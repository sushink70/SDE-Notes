# Comprehensive Guide to Go Data Types and Usage

Go is a statically typed language with a rich set of built-in data types. Let me cover all of them comprehensively.

## Basic Data Types

### Boolean Type
**`bool`** - represents true or false values

```go
var isActive bool = true
var isComplete bool = false
```

### Numeric Types

#### Integers (Signed)
- **`int8`** - 8-bit signed integer (-128 to 127)
- **`int16`** - 16-bit signed integer (-32,768 to 32,767)
- **`int32`** - 32-bit signed integer (-2,147,483,648 to 2,147,483,647)
- **`int64`** - 64-bit signed integer (-9,223,372,036,854,775,808 to 9,223,372,036,854,775,807)
- **`int`** - platform-dependent (32 or 64 bits)

#### Integers (Unsigned)
- **`uint8`** - 8-bit unsigned integer (0 to 255)
- **`uint16`** - 16-bit unsigned integer (0 to 65,535)
- **`uint32`** - 32-bit unsigned integer (0 to 4,294,967,295)
- **`uint64`** - 64-bit unsigned integer (0 to 18,446,744,073,709,551,615)
- **`uint`** - platform-dependent (32 or 64 bits)
- **`uintptr`** - unsigned integer large enough to store pointer values

#### Special Integer Types
- **`byte`** - alias for uint8
- **`rune`** - alias for int32, represents a Unicode code point

#### Floating-Point Numbers
- **`float32`** - IEEE-754 32-bit floating-point
- **`float64`** - IEEE-754 64-bit floating-point (default for float literals)

#### Complex Numbers
- **`complex64`** - complex numbers with float32 real and imaginary parts
- **`complex128`** - complex numbers with float64 real and imaginary parts

```go
var a int = 42
var b uint = 100
var c float64 = 3.14159
var d complex128 = 1 + 2i
var e rune = '世'
var f byte = 255
```

### String Type
**`string`** - immutable sequence of bytes (typically UTF-8 encoded text)

```go
var name string = "Hello, 世界"
var empty string = ""
var multiline string = `This is a
multiline string
using backticks`
```

## Composite Data Types

### Arrays
Fixed-size sequence of elements of the same type. Size is part of the type.

```go
var arr1 [5]int                    // [0 0 0 0 0]
var arr2 [3]string = [3]string{"a", "b", "c"}
arr3 := [...]int{1, 2, 3, 4}       // compiler counts elements
arr4 := [5]int{1: 10, 3: 30}       // sparse initialization
```

### Slices
Dynamic-size, flexible view into arrays. Most commonly used sequence type.

```go
var s1 []int                       // nil slice
s2 := []int{1, 2, 3}              // slice literal
s3 := make([]int, 5)              // length 5, capacity 5
s4 := make([]int, 5, 10)          // length 5, capacity 10
s5 := arr3[1:3]                    // slice from array

// Common slice operations
s2 = append(s2, 4, 5)             // append elements
s2 = append(s2, s3...)            // append another slice
len(s2)                            // length
cap(s2)                            // capacity
copy(s3, s2)                       // copy slice
```

### Maps
Key-value pairs (hash table/dictionary).

```go
var m1 map[string]int              // nil map
m2 := make(map[string]int)        // empty map
m3 := map[string]int{
    "one": 1,
    "two": 2,
}

// Map operations
m3["three"] = 3                    // set value
value := m3["one"]                 // get value
value, ok := m3["four"]            // check existence
delete(m3, "two")                  // delete key
len(m3)                            // number of keys

// Iterate over map
for key, value := range m3 {
    // use key and value
}
```

### Structs
Collection of fields with different types.

```go
type Person struct {
    Name    string
    Age     int
    Email   string
}

// Creating structs
p1 := Person{Name: "Alice", Age: 30, Email: "alice@example.com"}
p2 := Person{"Bob", 25, "bob@example.com"}  // positional
var p3 Person                                // zero values

// Anonymous structs
employee := struct {
    ID   int
    Name string
}{
    ID:   100,
    Name: "John",
}

// Embedded structs
type Address struct {
    Street string
    City   string
}

type Employee struct {
    Person            // embedded
    Address           // embedded
    EmployeeID int
}
```

## Pointer Types
Hold memory addresses of values.

```go
var p *int                         // nil pointer
x := 42
p = &x                             // address of x
*p = 21                            // dereference and modify
y := *p                            // dereference and read

// Pointer to struct
person := &Person{Name: "Alice", Age: 30}
person.Name = "Bob"                // automatic dereferencing
```

## Function Types
Functions are first-class citizens in Go.

```go
// Function declaration
func add(a, b int) int {
    return a + b
}

// Function type
type operation func(int, int) int

// Function as variable
var op operation = add

// Anonymous function
multiply := func(a, b int) int {
    return a * b
}

// Function returning function
func makeAdder(x int) func(int) int {
    return func(y int) int {
        return x + y
    }
}

// Variadic functions
func sum(nums ...int) int {
    total := 0
    for _, n := range nums {
        total += n
    }
    return total
}
```

## Interface Types
Define behavior through method sets.

```go
// Interface declaration
type Reader interface {
    Read(p []byte) (n int, err error)
}

type Writer interface {
    Write(p []byte) (n int, err error)
}

// Empty interface (can hold any type)
var any interface{}
any = 42
any = "string"
any = []int{1, 2, 3}

// Type assertion
var i interface{} = "hello"
s := i.(string)                    // panic if wrong type
s, ok := i.(string)                // safe type assertion

// Type switch
switch v := i.(type) {
case int:
    // v is int
case string:
    // v is string
default:
    // unknown type
}
```

## Channel Types
Used for communication between goroutines.

```go
var ch1 chan int                   // nil channel
ch2 := make(chan int)              // unbuffered channel
ch3 := make(chan int, 10)          // buffered channel (capacity 10)

// Channel operations
ch2 <- 42                          // send
value := <-ch2                     // receive
value, ok := <-ch2                 // receive with check

// Directional channels
var sendOnly chan<- int            // send-only
var recvOnly <-chan int            // receive-only

// Close channel
close(ch2)

// Range over channel
for value := range ch3 {
    // received value
}

// Select statement
select {
case v := <-ch2:
    // received from ch2
case ch3 <- 42:
    // sent to ch3
case <-time.After(time.Second):
    // timeout
default:
    // non-blocking
}
```

## Special Types

### Type Aliases
```go
type MyInt = int                   // alias
type UserID int                    // new type (not alias)
```

### Nil
The zero value for pointers, interfaces, maps, slices, channels, and function types.

```go
var ptr *int                       // nil
var m map[string]int              // nil
var s []int                        // nil
var ch chan int                    // nil
var fn func()                      // nil
var i interface{}                  // nil
```

## Zero Values
Every type has a zero value (default value when not initialized):
- **Numeric types**: 0
- **Boolean**: false
- **String**: "" (empty string)
- **Pointers, slices, maps, channels, functions, interfaces**: nil
- **Structs**: all fields set to their zero values
- **Arrays**: all elements set to their zero value

```go
var i int                          // 0
var b bool                         // false
var s string                       // ""
var ptr *int                       // nil
```

## Type Conversions
Go requires explicit type conversions (no implicit conversions).

```go
var i int = 42
var f float64 = float64(i)
var u uint = uint(i)

// String conversions
s := string(65)                    // "A" (rune to string)
num := strconv.Atoi("123")        // string to int
str := strconv.Itoa(123)          // int to string
```

## Type Definitions and Methods

```go
type Celsius float64
type Fahrenheit float64

// Method on custom type
func (c Celsius) ToFahrenheit() Fahrenheit {
    return Fahrenheit(c*9/5 + 32)
}

// Value receiver
func (c Celsius) String() string {
    return fmt.Sprintf("%.2f°C", c)
}

// Pointer receiver (can modify)
func (c *Celsius) Add(delta Celsius) {
    *c += delta
}
```

## Constants
Untyped and typed constants.

```go
const Pi = 3.14159                 // untyped constant
const Size int = 100               // typed constant

// Constant block
const (
    StatusOK = 200
    StatusNotFound = 404
)

// iota for enumerations
const (
    Sunday = iota                  // 0
    Monday                         // 1
    Tuesday                        // 2
    Wednesday                      // 3
    Thursday                       // 4
    Friday                         // 5
    Saturday                       // 6
)

const (
    _ = 1 << (10 * iota)
    KB                             // 1024
    MB                             // 1048576
    GB                             // 1073741824
)
```

## Memory Layout and Sizes

```go
import "unsafe"

sizeof := unsafe.Sizeof(variable)
alignof := unsafe.Alignof(variable)
offsetof := unsafe.Offsetof(struct.field)
```

Common sizes (on 64-bit systems):
- bool: 1 byte
- int8/uint8/byte: 1 byte
- int16/uint16: 2 bytes
- int32/uint32/float32/rune: 4 bytes
- int64/uint64/float64/complex64: 8 bytes
- complex128: 16 bytes
- int/uint/uintptr: 8 bytes (platform-dependent)
- string: 16 bytes (header)
- slice: 24 bytes (header)
- map: 8 bytes (pointer)
- pointer: 8 bytes

This covers all the fundamental data types in Go and their usage patterns. Each type has its specific use cases, and Go's type system emphasizes simplicity and clarity.