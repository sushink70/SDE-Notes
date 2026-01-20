# Comprehensive Guide to Go's Built-in Functions

Before we dive deep, let me explain what **built-in functions** are: these are functions that come pre-packaged with the Go language itself—you don't need to import any package to use them. They're fundamental operations that the language designers deemed essential enough to make universally available.

Think of them as the "atomic operations" of Go—the irreducible building blocks from which all other functionality is constructed.

---

## Mental Model: Categorization by Purpose

To master these functions, we'll organize them by **cognitive purpose**—how they relate to memory, data manipulation, and program flow. This mirrors how expert programmers chunk knowledge for rapid recall.

---

## 1. Memory Allocation & Management

### `make(T, args)` - Allocate and Initialize Reference Types
```go
// Syntax: make(type, size, capacity)
// Returns: initialized (non-zero) reference type

// Slices
s := make([]int, 5)      // length=5, capacity=5, all zeros
s := make([]int, 3, 10)  // length=3, capacity=10

// Maps
m := make(map[string]int)           // empty map, ready to use
m := make(map[string]int, 100)      // pre-allocated for ~100 entries

// Channels
ch := make(chan int)       // unbuffered channel
ch := make(chan int, 10)   // buffered channel with capacity 10
```

**Key Insight**: `make` is ONLY for slices, maps, and channels. Why? These are **reference types** that need internal data structure initialization. Arrays and structs don't need it.

**Performance Note**: Pre-allocating capacity reduces reallocations. For a slice that will grow to 1000 elements, `make([]int, 0, 1000)` is far superior to `make([]int, 0)`.

---

### `new(T)` - Allocate Zero-Valued Memory
```go
// Syntax: new(Type)
// Returns: *Type (pointer to zero value)

p := new(int)        // p is *int, *p == 0
s := new(string)     // s is *string, *s == ""
arr := new([10]int)  // arr is *[10]int, all elements zero
```

**Conceptual Difference from `make`**:
- `new(T)` returns `*T` (pointer) with zero value
- `make(T)` returns `T` itself, initialized and ready

```go
// Compare:
s1 := new([]int)     // s1 is *[]int, points to nil slice (unusable!)
s2 := make([]int, 0) // s2 is []int, empty but initialized (usable!)
```

**When to use**: Rarely needed in idiomatic Go. Prefer composite literals: `&MyStruct{}` over `new(MyStruct)`.

---

## 2. Collection Operations

### `len(v)` - Length of Collections
```go
// Works on: string, array, slice, map, channel

s := "hello"
len(s)  // 5 (bytes, not runes! "你好" is 6 bytes, 2 runes)

arr := [3]int{1, 2, 3}
len(arr)  // 3 (compile-time constant for arrays)

slice := []int{1, 2, 3, 4}
len(slice)  // 4 (runtime value)

m := map[string]int{"a": 1, "b": 2}
len(m)  // 2

ch := make(chan int, 5)
len(ch)  // 0 (number of queued elements)
```

**Complexity**: O(1) for all types—length is stored in metadata.

---

### `cap(v)` - Capacity of Slices/Channels
```go
// Works on: array, slice, channel

s := make([]int, 3, 10)
len(s)  // 3 (current elements)
cap(s)  // 10 (allocated space before reallocation)

ch := make(chan int, 5)
cap(ch)  // 5 (buffer size)
```

**Critical Distinction**: Length vs Capacity
- **Length**: how many elements currently exist
- **Capacity**: how many elements CAN exist before reallocation

```go
s := make([]int, 3, 10)
// s[0], s[1], s[2] are valid
// s[3] will panic! Use append() instead
```

---

### `append(slice, elements...)` - Grow Slices
```go
// Syntax: append(slice, elem1, elem2, ...)
// Returns: new slice (may be same underlying array or new one)

s := []int{1, 2, 3}
s = append(s, 4)           // [1, 2, 3, 4]
s = append(s, 5, 6, 7)     // [1, 2, 3, 4, 5, 6, 7]

// Append another slice (use ... to unpack)
s2 := []int{8, 9}
s = append(s, s2...)       // [1, 2, 3, 4, 5, 6, 7, 8, 9]
```

**Performance Deep Dive**:
```go
// Growing strategy (approximately):
// When cap is exceeded, new cap ≈ 2 * old cap (for small slices)
// This is amortized O(1) per append

s := make([]int, 0)
for i := 0; i < 1000; i++ {
    s = append(s, i)  // Reallocates ~10 times (log₂(1000))
}

// Pre-allocate for O(1) every time:
s := make([]int, 0, 1000)
for i := 0; i < 1000; i++ {
    s = append(s, i)  // Zero reallocations
}
```

**CRITICAL**: Always assign result back: `s = append(s, x)`, never just `append(s, x)`.

---

### `copy(dst, src)` - Copy Slice Elements
```go
// Syntax: copy(destination, source)
// Returns: number of elements copied (min(len(dst), len(src)))

src := []int{1, 2, 3, 4, 5}
dst := make([]int, 3)
n := copy(dst, src)  // n=3, dst=[1,2,3]

// Copy works even if slices overlap:
s := []int{1, 2, 3, 4, 5}
copy(s[2:], s[1:])  // s=[1,2,2,3,4] - shifts right
```

**Complexity**: O(n) where n = min(len(dst), len(src))

**Idiomatic Pattern**: Growing and copying
```go
// Wrong (inefficient):
var result []int
for _, v := range data {
    result = append(result, transform(v))  // Reallocates multiple times
}

// Right (pre-allocate):
result := make([]int, len(data))
for i, v := range data {
    result[i] = transform(v)  // No reallocation
}
```

---

### `delete(map, key)` - Remove Map Entry
```go
m := map[string]int{"a": 1, "b": 2, "c": 3}
delete(m, "b")  // m = {"a": 1, "c": 3}
delete(m, "x")  // No-op if key doesn't exist (no panic)
```

**Complexity**: Average O(1), worst O(n) (hash collision)

---

### `clear(collection)` - Empty Collection (Go 1.21+)
```go
// Works on: slice, map

s := []int{1, 2, 3, 4, 5}
clear(s)  // s = [0, 0, 0, 0, 0] (length unchanged, values zeroed)

m := map[string]int{"a": 1, "b": 2}
clear(m)  // m = {} (empty map, but allocated)
```

**Use Case**: Reusing allocated memory without creating new collections.

---

## 3. Channel Operations

### `close(ch)` - Close Channel
```go
ch := make(chan int, 3)
ch <- 1
ch <- 2
close(ch)

// Reading from closed channel:
v, ok := <-ch  // v=1, ok=true
v, ok = <-ch   // v=2, ok=true
v, ok = <-ch   // v=0 (zero value), ok=false

// Range automatically stops on close:
for v := range ch {
    // Processes all values until close
}
```

**Critical Rules**:
- Closing a nil channel: **panic**
- Closing a closed channel: **panic**
- Sending to closed channel: **panic**
- Receiving from closed channel: returns zero value + false

**Idiom**: Only the sender should close channels.

---

## 4. Error Handling & Control Flow

### `panic(v)` - Abort Execution
```go
func divide(a, b int) int {
    if b == 0 {
        panic("division by zero")
    }
    return a / b
}
```

**Mental Model**: `panic` is for **programmer errors** (bugs), not expected runtime errors. Use errors for the latter.

---

### `recover()` - Catch Panic
```go
func safeFunction() {
    defer func() {
        if r := recover(); r != nil {
            fmt.Println("Recovered from:", r)
        }
    }()
    
    panic("something went wrong")
    // This line never executes
}
```

**CRITICAL**: `recover()` only works inside `defer`. Calling it elsewhere returns `nil`.

---

## 5. Complex Number Operations

```go
// Complex number creation
c1 := complex(3, 4)        // 3+4i
c2 := complex(1.5, 2.5)    // 1.5+2.5i

// Extract components
r := real(c1)   // r = 3.0
i := imag(c1)   // i = 4.0
```

**Use Case**: Rare in typical programming; used in scientific computing, signal processing, FFT algorithms.

---

## 6. Type Assertions & Printing

### `print()` & `println()` - Debug Printing
```go
println("Debug:", x)  // Writes to stderr, minimal formatting
```

**WARNING**: Not for production! Use `fmt.Println()` instead. These are for debugging/bootstrapping the language itself.

---

## Complete Reference Table

| Function | Purpose | Works On | Returns | Complexity |
|----------|---------|----------|---------|------------|
| `make(T, ...)` | Allocate & init | slice, map, chan | `T` | O(n) for size |
| `new(T)` | Allocate zero | any type | `*T` | O(1) |
| `len(v)` | Length | string, array, slice, map, chan | `int` | O(1) |
| `cap(v)` | Capacity | array, slice, chan | `int` | O(1) |
| `append(s, x...)` | Grow slice | slice | slice | Amortized O(1) |
| `copy(dst, src)` | Copy elements | slice | `int` | O(min(len(dst), len(src))) |
| `delete(m, k)` | Remove key | map | - | O(1) avg |
| `clear(v)` | Zero/empty | slice, map | - | O(n) |
| `close(ch)` | Close channel | chan | - | O(1) |
| `panic(v)` | Abort | any | - | - |
| `recover()` | Catch panic | - | `any` | O(1) |
| `complex(r, i)` | Create complex | float | complex | O(1) |
| `real(c)` | Real part | complex | float | O(1) |
| `imag(c)` | Imag part | complex | float | O(1) |
| `print(...)` | Debug print | any | - | - |
| `println(...)` | Debug print+newline | any | - | - |

---

## Deep Understanding: Why So Few?

**Philosophical Insight**: Go's minimalism is intentional. Compare to Python's 70+ built-ins or C's rich standard library. Go forces you to:

1. **Use packages explicitly**: Want to sort? Import `sort`. Math? Import `math`.
2. **Understand composition**: Build complexity from simple parts
3. **Avoid magic**: If it's not built-in, you can read its source

This is a **deliberate cognitive load reduction**—fewer primitives to memorize, more focus on problem-solving patterns.

---

## Expert Practice Pattern

**Chunking Exercise**: Categorize each function by:
1. **Memory category** (allocation, measurement, modification)
2. **Time complexity**
3. **When it can panic**

Example:
- `append`: Modification, Amortized O(1), Never panics
- `close`: Modification, O(1), Panics on nil/closed channel
- `len`: Measurement, O(1), Never panics

This creates **neural pathways** for instant recall during problem-solving.

---

## Next Steps in Your Mastery Journey

Now that you understand the primitives, you're ready to:
1. **Compose them** into data structures (stacks, queues, heaps)
2. **Analyze patterns** in how they're used in algorithms
3. **Recognize idioms** that combine multiple built-ins efficiently

Every algorithm you encounter will use these as building blocks. Your fluency with them determines your coding velocity.

Would you like me to demonstrate advanced patterns combining these built-ins for specific algorithmic techniques (sliding window, two pointers, etc.)?