# Comprehensive Go Syntax Guide

## Table of Contents
1. [Basic Structure](#basic-structure)
2. [Variables and Constants](#variables-and-constants)
3. [Data Types](#data-types)
4. [Functions](#functions)
5. [Structs](#structs)
6. [Methods](#methods)
7. [Interfaces](#interfaces)
8. [Control Flow](#control-flow)
9. [Loops](#loops)
10. [Arrays, Slices, and Maps](#arrays-slices-and-maps)
11. [Pointers](#pointers)
12. [Error Handling](#error-handling)
13. [Goroutines and Channels](#goroutines-and-channels)
14. [Packages and Imports](#packages-and-imports)

---

## Basic Structure

Every Go program starts with a package declaration and a main function:

```go
package main

import "fmt"

func main() {
    fmt.Println("Hello, World!")
}
```

---

## Variables and Constants

### Variable Declaration

```go
// Method 1: var keyword with type
var name string = "John"

// Method 2: var keyword with type inference
var age = 25

// Method 3: Short declaration (inside functions only)
city := "New York"

// Multiple variables
var x, y int = 1, 2
a, b, c := 10, "hello", true
```

### Constants

```go
const Pi = 3.14159
const (
    StatusOK = 200
    StatusNotFound = 404
)
```

### Zero Values

Variables declared without explicit initialization have zero values:
- `0` for numeric types
- `false` for boolean
- `""` (empty string) for strings
- `nil` for pointers, slices, maps, channels, functions, interfaces

---

## Data Types

### Basic Types

```go
// Integers
var i int = 42          // Platform dependent (32 or 64 bit)
var i8 int8 = 127       // -128 to 127
var i16 int16           // -32768 to 32767
var i32 int32           // -2^31 to 2^31-1
var i64 int64           // -2^63 to 2^63-1
var u uint = 42         // Unsigned, platform dependent
var u8 uint8            // 0 to 255 (byte is alias)
var u16 uint16          // 0 to 65535
var u32 uint32          // 0 to 2^32-1
var u64 uint64          // 0 to 2^64-1

// Floating point
var f32 float32 = 3.14
var f64 float64 = 3.14159

// Complex numbers
var c64 complex64 = 1 + 2i
var c128 complex128 = 2 + 3i

// Boolean
var isTrue bool = true

// String
var text string = "Hello"

// Byte and Rune
var b byte = 'A'        // alias for uint8
var r rune = '世'        // alias for int32 (Unicode code point)
```

### Type Conversion

```go
var i int = 42
var f float64 = float64(i)
var u uint = uint(f)
```

---

## Functions

### Basic Function

```go
func add(x int, y int) int {
    return x + y
}

// Shortened when parameters share type
func subtract(x, y int) int {
    return x - y
}
```

### Multiple Return Values

```go
func divide(x, y float64) (float64, error) {
    if y == 0 {
        return 0, fmt.Errorf("division by zero")
    }
    return x / y, nil
}

// Usage
result, err := divide(10, 2)
if err != nil {
    fmt.Println("Error:", err)
}
```

### Named Return Values

```go
func split(sum int) (x, y int) {
    x = sum * 4 / 9
    y = sum - x
    return // naked return
}
```

### Variadic Functions

```go
func sum(numbers ...int) int {
    total := 0
    for _, num := range numbers {
        total += num
    }
    return total
}

// Usage
result := sum(1, 2, 3, 4, 5)
```

### Anonymous Functions and Closures

```go
// Anonymous function
func() {
    fmt.Println("Anonymous function")
}()

// Function as variable
add := func(x, y int) int {
    return x + y
}
result := add(3, 5)

// Closure
func counter() func() int {
    count := 0
    return func() int {
        count++
        return count
    }
}

c := counter()
fmt.Println(c()) // 1
fmt.Println(c()) // 2
```

### Defer

```go
func example() {
    defer fmt.Println("World") // Executes after function returns
    fmt.Println("Hello")
}
// Output: Hello World
```

---

## Structs

Go doesn't have classes, but structs provide similar functionality:

```go
// Define a struct
type Person struct {
    Name string
    Age  int
    Email string
}

// Create struct instances
p1 := Person{Name: "Alice", Age: 30, Email: "alice@example.com"}
p2 := Person{"Bob", 25, "bob@example.com"}
p3 := Person{Name: "Charlie"} // Age and Email get zero values

// Access fields
fmt.Println(p1.Name)
p1.Age = 31

// Anonymous structs
car := struct {
    Make  string
    Model string
}{
    Make:  "Toyota",
    Model: "Camry",
}
```

### Embedded Structs

```go
type Address struct {
    Street string
    City   string
}

type Employee struct {
    Person  // Embedded struct
    Address // Embedded struct
    Salary  int
}

emp := Employee{
    Person: Person{Name: "John", Age: 30},
    Address: Address{Street: "123 Main St", City: "NYC"},
    Salary: 50000,
}

// Access embedded fields directly
fmt.Println(emp.Name)   // From Person
fmt.Println(emp.City)   // From Address
```

---

## Methods

Methods are functions with a receiver:

```go
type Rectangle struct {
    Width  float64
    Height float64
}

// Value receiver
func (r Rectangle) Area() float64 {
    return r.Width * r.Height
}

// Pointer receiver (can modify the struct)
func (r *Rectangle) Scale(factor float64) {
    r.Width *= factor
    r.Height *= factor
}

// Usage
rect := Rectangle{Width: 10, Height: 5}
fmt.Println(rect.Area())  // 50
rect.Scale(2)
fmt.Println(rect.Area())  // 200
```

---

## Interfaces

Interfaces define behavior through method signatures:

```go
// Define interface
type Shape interface {
    Area() float64
    Perimeter() float64
}

// Implement interface (implicit)
type Circle struct {
    Radius float64
}

func (c Circle) Area() float64 {
    return 3.14159 * c.Radius * c.Radius
}

func (c Circle) Perimeter() float64 {
    return 2 * 3.14159 * c.Radius
}

// Use interface
func printShapeInfo(s Shape) {
    fmt.Printf("Area: %.2f, Perimeter: %.2f\n", s.Area(), s.Perimeter())
}

circle := Circle{Radius: 5}
printShapeInfo(circle)
```

### Empty Interface

```go
// interface{} or any (Go 1.18+) accepts any type
func describe(i interface{}) {
    fmt.Printf("Type: %T, Value: %v\n", i, i)
}

describe(42)
describe("hello")
describe(true)
```

### Type Assertions and Type Switches

```go
// Type assertion
var i interface{} = "hello"
s := i.(string)
fmt.Println(s)

// Type assertion with check
s, ok := i.(string)
if ok {
    fmt.Println("String:", s)
}

// Type switch
func doSomething(i interface{}) {
    switch v := i.(type) {
    case int:
        fmt.Printf("Integer: %d\n", v)
    case string:
        fmt.Printf("String: %s\n", v)
    case bool:
        fmt.Printf("Boolean: %t\n", v)
    default:
        fmt.Printf("Unknown type: %T\n", v)
    }
}
```

---

## Control Flow

### If Statements

```go
// Basic if
if x > 0 {
    fmt.Println("Positive")
}

// If-else
if x > 0 {
    fmt.Println("Positive")
} else {
    fmt.Println("Non-positive")
}

// If-else if-else
if x > 0 {
    fmt.Println("Positive")
} else if x < 0 {
    fmt.Println("Negative")
} else {
    fmt.Println("Zero")
}

// If with initialization
if err := doSomething(); err != nil {
    fmt.Println("Error:", err)
}
```

### Switch Statements

```go
// Basic switch
switch day {
case "Monday":
    fmt.Println("Start of week")
case "Friday":
    fmt.Println("End of week")
default:
    fmt.Println("Midweek")
}

// Switch with multiple values
switch day {
case "Saturday", "Sunday":
    fmt.Println("Weekend")
default:
    fmt.Println("Weekday")
}

// Switch without expression (like if-else chain)
switch {
case age < 13:
    fmt.Println("Child")
case age < 20:
    fmt.Println("Teenager")
default:
    fmt.Println("Adult")
}

// Switch with fallthrough
switch num {
case 1:
    fmt.Println("One")
    fallthrough
case 2:
    fmt.Println("Two or less")
}
```

---

## Loops

Go has only one loop keyword: `for`

### Basic For Loop

```go
for i := 0; i < 10; i++ {
    fmt.Println(i)
}
```

### While-style Loop

```go
i := 0
for i < 10 {
    fmt.Println(i)
    i++
}
```

### Infinite Loop

```go
for {
    // Loop forever
    if condition {
        break
    }
}
```

### Range Loop

```go
// Array/Slice
numbers := []int{1, 2, 3, 4, 5}
for index, value := range numbers {
    fmt.Printf("Index: %d, Value: %d\n", index, value)
}

// Just values
for _, value := range numbers {
    fmt.Println(value)
}

// Just indices
for index := range numbers {
    fmt.Println(index)
}

// Map
ages := map[string]int{"Alice": 30, "Bob": 25}
for name, age := range ages {
    fmt.Printf("%s is %d years old\n", name, age)
}

// String (iterates over runes)
for index, char := range "Hello" {
    fmt.Printf("Index: %d, Char: %c\n", index, char)
}
```

### Break and Continue

```go
for i := 0; i < 10; i++ {
    if i == 5 {
        break // Exit loop
    }
    if i%2 == 0 {
        continue // Skip to next iteration
    }
    fmt.Println(i)
}
```

---

## Arrays, Slices, and Maps

### Arrays

Fixed size, not commonly used:

```go
var arr [5]int              // Array of 5 integers
arr[0] = 100

arr2 := [3]string{"a", "b", "c"}
arr3 := [...]int{1, 2, 3, 4, 5}  // Compiler counts elements

// Length
length := len(arr)
```

### Slices

Dynamic size, most commonly used:

```go
// Create slice
var s []int                     // nil slice
s = []int{1, 2, 3, 4, 5}       // slice literal
s = make([]int, 5)             // length 5, all zeros
s = make([]int, 5, 10)         // length 5, capacity 10

// Append
s = append(s, 6)
s = append(s, 7, 8, 9)

// Slicing
slice := []int{0, 1, 2, 3, 4, 5}
sub := slice[1:4]              // [1, 2, 3]
sub2 := slice[:3]              // [0, 1, 2]
sub3 := slice[2:]              // [2, 3, 4, 5]
sub4 := slice[:]               // Copy of entire slice

// Length and capacity
len(s)  // Number of elements
cap(s)  // Capacity

// Copy
dest := make([]int, len(s))
copy(dest, s)

// 2D slices
matrix := [][]int{
    {1, 2, 3},
    {4, 5, 6},
}
```

### Maps

```go
// Create map
var m map[string]int               // nil map
m = make(map[string]int)           // initialized map
m = map[string]int{                // map literal
    "Alice": 30,
    "Bob":   25,
}

// Add/Update
m["Charlie"] = 35

// Get
age := m["Alice"]

// Get with existence check
age, exists := m["David"]
if exists {
    fmt.Println("Age:", age)
}

// Delete
delete(m, "Bob")

// Length
length := len(m)

// Iterate
for key, value := range m {
    fmt.Printf("%s: %d\n", key, value)
}
```

---

## Pointers

```go
// Declare pointer
var p *int

// Get address
x := 42
p = &x

// Dereference
fmt.Println(*p)  // 42
*p = 100
fmt.Println(x)   // 100

// New
p2 := new(int)   // Allocates memory, returns pointer
*p2 = 50

// Pointers with structs
type Person struct {
    Name string
    Age  int
}

person := Person{Name: "Alice", Age: 30}
ptr := &person
ptr.Age = 31            // Automatic dereferencing
(*ptr).Age = 32         // Explicit dereferencing
```

---

## Error Handling

Go uses explicit error handling:

```go
// Return error
func divide(a, b float64) (float64, error) {
    if b == 0 {
        return 0, errors.New("division by zero")
    }
    return a / b, nil
}

// Check error
result, err := divide(10, 0)
if err != nil {
    fmt.Println("Error:", err)
    return
}
fmt.Println("Result:", result)

// Custom error type
type MyError struct {
    Message string
    Code    int
}

func (e *MyError) Error() string {
    return fmt.Sprintf("Error %d: %s", e.Code, e.Message)
}

// Panic and Recover
func riskyOperation() {
    defer func() {
        if r := recover(); r != nil {
            fmt.Println("Recovered from:", r)
        }
    }()
    
    panic("something went wrong")
}
```

---

## Goroutines and Channels

### Goroutines

```go
// Start goroutine
go func() {
    fmt.Println("Running in goroutine")
}()

// With named function
func sayHello() {
    fmt.Println("Hello")
}

go sayHello()
```

### Channels

```go
// Create channel
ch := make(chan int)
ch2 := make(chan string, 5)  // Buffered channel

// Send to channel
go func() {
    ch <- 42
}()

// Receive from channel
value := <-ch

// Close channel
close(ch)

// Range over channel
go func() {
    for i := 0; i < 5; i++ {
        ch <- i
    }
    close(ch)
}()

for value := range ch {
    fmt.Println(value)
}

// Select statement
select {
case msg1 := <-ch1:
    fmt.Println("Received from ch1:", msg1)
case msg2 := <-ch2:
    fmt.Println("Received from ch2:", msg2)
case ch3 <- 42:
    fmt.Println("Sent to ch3")
default:
    fmt.Println("No communication")
}
```

### WaitGroups

```go
import "sync"

var wg sync.WaitGroup

for i := 0; i < 5; i++ {
    wg.Add(1)
    go func(id int) {
        defer wg.Done()
        fmt.Printf("Worker %d done\n", id)
    }(i)
}

wg.Wait()
```

### Mutexes

```go
import "sync"

var (
    mu      sync.Mutex
    counter int
)

func increment() {
    mu.Lock()
    counter++
    mu.Unlock()
}
```

---

## Packages and Imports

### Import Syntax

```go
// Single import
import "fmt"

// Multiple imports
import (
    "fmt"
    "math"
    "strings"
)

// Aliased import
import f "fmt"

// Blank import (for side effects)
import _ "github.com/lib/pq"

// Dot import (not recommended)
import . "math"
```

### Creating a Package

```go
// In file: mypackage/mypackage.go
package mypackage

// Exported (capital letter)
func PublicFunction() {
    fmt.Println("Public")
}

// Unexported (lowercase)
func privateFunction() {
    fmt.Println("Private")
}

// Exported constant
const MaxSize = 100

// Exported struct
type Person struct {
    Name string   // Exported field
    age  int      // Unexported field
}
```

### Using Packages

```go
// In file: main.go
package main

import "myproject/mypackage"

func main() {
    mypackage.PublicFunction()
    // mypackage.privateFunction() // Error: not exported
}
```

---

## Additional Features

### Init Function

```go
func init() {
    // Runs automatically before main
    fmt.Println("Initialization")
}
```

### Blank Identifier

```go
// Ignore values
_, err := divide(10, 2)

// Unused imports/variables
import _ "fmt"
```

### Type Definitions

```go
// New type
type Celsius float64
type Fahrenheit float64

// Type alias (Go 1.9+)
type MyInt = int
```

### Generics (Go 1.18+)

```go
// Generic function
func Print[T any](value T) {
    fmt.Println(value)
}

// Generic type
type Stack[T any] struct {
    items []T
}

func (s *Stack[T]) Push(item T) {
    s.items = append(s.items, item)
}

func (s *Stack[T]) Pop() T {
    if len(s.items) == 0 {
        var zero T
        return zero
    }
    item := s.items[len(s.items)-1]
    s.items = s.items[:len(s.items)-1]
    return item
}

// Usage
intStack := Stack[int]{}
intStack.Push(42)
```

---

This guide covers the essential syntax and features of Go. For more details, visit the official Go documentation at https://go.dev/doc/


I'll create a comprehensive guide to Go syntax covering all the major language features.I've created a comprehensive Go syntax guide covering all the major language features! Here's what's included:

**Core Topics:**
- Variables, constants, and data types
- Functions (including closures, variadic, multiple returns)
- Structs and embedded structs (Go's approach instead of classes)
- Methods and interfaces
- Control flow (if, switch)
- Loops (for, range)
- Arrays, slices, and maps
- Pointers
- Error handling
- Goroutines and channels (concurrency)
- Packages and imports

**Key Go Concepts:**
- Go doesn't have classes, but uses structs with methods
- Interface implementation is implicit
- Only one loop keyword (`for`) with multiple styles
- Explicit error handling (no exceptions)
- Built-in concurrency with goroutines
- Exported names start with capital letters

The guide includes practical examples for each concept and covers modern features like generics (Go 1.18+). You can use this as a quick reference or learning resource!