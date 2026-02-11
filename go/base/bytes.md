# The Complete Guide to Bytes in Go: From Fundamentals to Mastery

## Table of Contents
1. Foundation: What Are Bytes?
2. The `byte` Type in Go
3. Byte Slices (`[]byte`)
4. The `bytes` Package
5. Memory & Performance Characteristics
6. Advanced Patterns & Techniques
7. Real-World Applications

---

## 1. Foundation: What Are Bytes?

### What is a Byte?
A **byte** is the fundamental unit of digital information, consisting of **8 bits**. Each bit can be either 0 or 1, giving a byte 2^8 = 256 possible values (0-255).

```
Byte representation:
┌─────────────────────────────────────────┐
│  Bit positions: 7  6  5  4  3  2  1  0  │
│  Example byte:  1  0  1  1  0  0  1  1  │
│  Decimal value: 128+32+16+2+1 = 179     │
└─────────────────────────────────────────┘
```

### Why Bytes Matter in Programming

Bytes are the **atomic unit** for:
- **File I/O**: Reading/writing files
- **Network communication**: Sending/receiving data
- **Memory representation**: How data lives in RAM
- **Encoding**: UTF-8, ASCII, binary protocols
- **Low-level operations**: Bit manipulation, cryptography

**Mental Model**: Think of bytes as the "raw material" of computing. Everything—text, images, videos, network packets—eventually becomes bytes.

---

## 2. The `byte` Type in Go

### Type Definition

```go
// In Go, byte is an alias for uint8
type byte = uint8
```

This means:
- Range: 0 to 255
- Size: 8 bits (1 byte)
- Unsigned: No negative values

### Basic Operations

```go
package main

import "fmt"

func main() {
    // Declaration
    var b byte = 65        // Decimal
    var b2 byte = 0x41     // Hexadecimal (same as 65)
    var b3 byte = 'A'      // Character literal (ASCII 65)
    
    fmt.Printf("Decimal: %d\n", b)      // 65
    fmt.Printf("Hex: %x\n", b)          // 41
    fmt.Printf("Binary: %b\n", b)       // 1000001
    fmt.Printf("Character: %c\n", b)    // A
    
    // Arithmetic
    b4 := byte(100)
    b5 := byte(50)
    sum := b4 + b5         // 150
    
    // Overflow behavior
    var overflow byte = 255
    overflow += 1          // Wraps to 0 (not an error!)
    fmt.Println(overflow)  // 0
}
```

**Critical Insight**: Go's byte arithmetic **wraps around** on overflow. This is intentional for performance (no bounds checking on every operation).

---

## 3. Byte Slices (`[]byte`)

### What is a Slice?

A **slice** is Go's dynamic array. It's a descriptor containing:
1. **Pointer** to the underlying array
2. **Length** (current number of elements)
3. **Capacity** (maximum size before reallocation)

```
Slice structure visualization:
┌─────────────────────────────────────────────┐
│  Slice Header (24 bytes on 64-bit systems)  │
├─────────────────────────────────────────────┤
│  ptr  ────────────────┐                     │
│  len  = 5             │                     │
│  cap  = 8             │                     │
└───────────────────────┼─────────────────────┘
                        │
                        ▼
        ┌───┬───┬───┬───┬───┬───┬───┬───┐
        │ H │ e │ l │ l │ o │   │   │   │
        └───┴───┴───┴───┴───┴───┴───┴───┘
         0   1   2   3   4   5   6   7
        (capacity = 8, length = 5)
```

### Creating Byte Slices

```go
package main

import "fmt"

func main() {
    // Method 1: Literal
    b1 := []byte{72, 101, 108, 108, 111}
    fmt.Println(string(b1))  // "Hello"
    
    // Method 2: From string
    b2 := []byte("Hello")
    // This creates a NEW copy of the string's bytes
    
    // Method 3: Make with length
    b3 := make([]byte, 5)     // [0 0 0 0 0]
    
    // Method 4: Make with length and capacity
    b4 := make([]byte, 5, 10) // len=5, cap=10
    
    // Method 5: Empty slice
    var b5 []byte             // nil slice
    b6 := []byte{}            // empty but non-nil
    
    fmt.Printf("b3: len=%d, cap=%d\n", len(b3), cap(b3))
    fmt.Printf("b4: len=%d, cap=%d\n", len(b4), cap(b4))
}
```

**Expert Pattern**: Pre-allocate capacity when you know the approximate size to avoid multiple reallocations.

```go
// Bad: Multiple reallocations
func inefficient() []byte {
    var result []byte
    for i := 0; i < 10000; i++ {
        result = append(result, byte(i%256))  // May reallocate many times
    }
    return result
}

// Good: Single allocation
func efficient() []byte {
    result := make([]byte, 0, 10000)  // Pre-allocate capacity
    for i := 0; i < 10000; i++ {
        result = append(result, byte(i%256))
    }
    return result
}
```

### Slice Operations

```go
package main

import "fmt"

func main() {
    data := []byte("Hello, World!")
    
    // Indexing
    fmt.Println(data[0])        // 72 (ASCII 'H')
    
    // Slicing (creates a view, not a copy)
    hello := data[0:5]          // "Hello"
    world := data[7:12]         // "World"
    
    // Modifying through slice affects original
    hello[0] = 'h'
    fmt.Println(string(data))   // "hello, World!"
    
    // Append
    data = append(data, '?')
    
    // Copy (creates independent copy)
    copied := make([]byte, len(data))
    copy(copied, data)
    copied[0] = 'H'
    fmt.Println(string(data))   // "hello, World!?"
    fmt.Println(string(copied)) // "Hello, World!?"
}
```

**Critical Concept - Slicing Creates Views**:

```
Original array:
┌───┬───┬───┬───┬───┬───┬───┐
│ H │ e │ l │ l │ o │ ! │ ! │
└───┴───┴───┴───┴───┴───┴───┘
  0   1   2   3   4   5   6

slice1 := data[0:5]
┌─────────┐
│ ptr ────┼──┐
│ len = 5 │  │
│ cap = 7 │  │
└─────────┘  │
             ▼
┌───┬───┬───┬───┬───┬───┬───┐
│ H │ e │ l │ l │ o │ ! │ ! │
└───┴───┴───┴───┴───┴───┴───┘

slice2 := data[2:5]
┌─────────┐
│ ptr ────┼──────────┐
│ len = 3 │          │
│ cap = 5 │          │
└─────────┘          │
                     ▼
┌───┬───┬───┬───┬───┬───┬───┐
│ H │ e │ l │ l │ o │ ! │ ! │
└───┴───┴───┴───┴───┴───┴───┘

Both slices point to the SAME underlying array!
```

---

## 4. The `bytes` Package

The `bytes` package provides functions for manipulating byte slices. It mirrors the `strings` package but works with `[]byte` instead of `string`.

### Core Functions

#### 4.1 Comparison

```go
package main

import (
    "bytes"
    "fmt"
)

func main() {
    a := []byte("Hello")
    b := []byte("Hello")
    c := []byte("World")
    
    // Equal: Check if slices are identical
    fmt.Println(bytes.Equal(a, b))    // true
    fmt.Println(bytes.Equal(a, c))    // false
    
    // Compare: Lexicographical comparison
    // Returns: -1 if a < b, 0 if a == b, 1 if a > b
    fmt.Println(bytes.Compare(a, c))  // -1 ('H' < 'W')
    fmt.Println(bytes.Compare(c, a))  // 1
    fmt.Println(bytes.Compare(a, b))  // 0
}
```

**Algorithm Insight**: `bytes.Equal` is optimized with assembly for common architectures, using SIMD instructions when possible.

#### 4.2 Searching

```go
package main

import (
    "bytes"
    "fmt"
)

func main() {
    data := []byte("Hello, World! Hello!")
    
    // Contains
    fmt.Println(bytes.Contains(data, []byte("World")))  // true
    
    // Index (first occurrence)
    fmt.Println(bytes.Index(data, []byte("Hello")))     // 0
    
    // LastIndex (last occurrence)
    fmt.Println(bytes.LastIndex(data, []byte("Hello"))) // 14
    
    // IndexByte (optimized for single byte)
    fmt.Println(bytes.IndexByte(data, 'W'))             // 7
    
    // Count
    fmt.Println(bytes.Count(data, []byte("Hello")))     // 2
    
    // HasPrefix / HasSuffix
    fmt.Println(bytes.HasPrefix(data, []byte("Hello"))) // true
    fmt.Println(bytes.HasSuffix(data, []byte("!")))     // true
}
```

**Performance Tip**: Use `bytes.IndexByte()` instead of `bytes.Index()` for single-byte searches—it's significantly faster.

#### 4.3 Transformation

```go
package main

import (
    "bytes"
    "fmt"
)

func main() {
    data := []byte("  Hello, World!  ")
    
    // Trim
    trimmed := bytes.Trim(data, " ")
    fmt.Printf("|%s|\n", trimmed)  // |Hello, World!|
    
    // TrimSpace (removes all whitespace)
    spaced := bytes.TrimSpace(data)
    
    // ToUpper / ToLower
    upper := bytes.ToUpper([]byte("hello"))
    lower := bytes.ToLower([]byte("WORLD"))
    fmt.Println(string(upper), string(lower))  // HELLO world
    
    // Replace
    text := []byte("foo foo foo")
    replaced := bytes.Replace(text, []byte("foo"), []byte("bar"), 2)
    fmt.Println(string(replaced))  // bar bar foo
    
    // ReplaceAll (replace all occurrences)
    allReplaced := bytes.ReplaceAll(text, []byte("foo"), []byte("bar"))
    fmt.Println(string(allReplaced))  // bar bar bar
}
```

#### 4.4 Splitting and Joining

```go
package main

import (
    "bytes"
    "fmt"
)

func main() {
    // Split
    csv := []byte("apple,banana,cherry")
    parts := bytes.Split(csv, []byte(","))
    for _, part := range parts {
        fmt.Println(string(part))
    }
    // Output:
    // apple
    // banana
    // cherry
    
    // Join
    joined := bytes.Join(parts, []byte(" | "))
    fmt.Println(string(joined))  // apple | banana | cherry
    
    // Fields (split on whitespace)
    text := []byte("  one  two   three  ")
    fields := bytes.Fields(text)
    fmt.Printf("%d fields: %q\n", len(fields), fields)
    // 3 fields: ["one" "two" "three"]
}
```

**Concept - Delimiter**: A delimiter is a character or sequence that marks boundaries. In CSV files, commas are delimiters separating values.

### 4.5 The Buffer Type

`bytes.Buffer` is a **growable byte buffer** optimized for sequential writes and reads.

```
Buffer internal structure:
┌──────────────────────────────┐
│  bytes.Buffer                │
├──────────────────────────────┤
│  buf []byte ────┐            │
│  off int = 3    │  (read offset)
└─────────────────┼────────────┘
                  │
                  ▼
        ┌───┬───┬───┬───┬───┬───┐
        │ a │ b │ c │ d │ e │ f │
        └───┴───┴───┴───┴───┴───┘
              ▲
              │
         read position
```

```go
package main

import (
    "bytes"
    "fmt"
)

func main() {
    var buf bytes.Buffer
    
    // Write methods
    buf.WriteString("Hello")
    buf.WriteByte(' ')
    buf.Write([]byte("World"))
    buf.WriteRune('!')  // Writes UTF-8 encoded rune
    
    fmt.Println(buf.String())  // Hello World!
    
    // Read methods
    data := make([]byte, 5)
    n, _ := buf.Read(data)
    fmt.Printf("Read %d bytes: %s\n", n, data)  // Read 5 bytes: Hello
    
    // Peek at remaining without consuming
    fmt.Println(buf.String())  //  World!
    
    // Reset
    buf.Reset()
    fmt.Println(buf.Len())  // 0
}
```

**Use Case Pattern**:

```go
// Building strings/bytes efficiently
func buildMessage(items []string) []byte {
    var buf bytes.Buffer
    
    buf.WriteString("Items:\n")
    for i, item := range items {
        buf.WriteString(fmt.Sprintf("%d. %s\n", i+1, item))
    }
    
    return buf.Bytes()  // Returns copy of buffer contents
}

// This is MORE efficient than repeated string concatenation:
// Bad:
// result := "Items:\n"
// for i, item := range items {
//     result += fmt.Sprintf("%d. %s\n", i+1, item)  // Creates new string each time
// }
```

**Why Buffer is Fast**:
- Amortized growth: Doubles capacity when full
- No intermediate allocations
- Single final copy with `Bytes()`

---

## 5. Memory & Performance Characteristics

### String vs []byte Conversion

```go
s := "Hello"
b := []byte(s)  // COPIES the string's bytes to new allocation
s2 := string(b) // COPIES the byte slice to new string
```

**Memory Diagram**:

```
String "Hello" in memory:
┌────────────────┐
│ String header  │
│ ptr ─────┐     │
│ len = 5  │     │
└──────────┼─────┘
           │
           ▼
     ┌───┬───┬───┬───┬───┐
     │ H │ e │ l │ l │ o │  (Immutable, often in read-only memory)
     └───┴───┴───┴───┴───┘

After b := []byte(s):
┌────────────────┐
│ Slice header   │
│ ptr ─────┐     │
│ len = 5  │     │
│ cap = 5  │     │
└──────────┼─────┘
           │
           ▼
     ┌───┬───┬───┬───┬───┐
     │ H │ e │ l │ l │ o │  (NEW allocation, mutable)
     └───┴───┴───┴───┴───┘
```

**Zero-Copy Conversion (Unsafe)**:

```go
import "unsafe"

// String to []byte WITHOUT copying (DANGEROUS)
func stringToBytes(s string) []byte {
    return unsafe.Slice(unsafe.StringData(s), len(s))
}

// []byte to string WITHOUT copying (DANGEROUS)
func bytesToString(b []byte) string {
    return unsafe.String(&b[0], len(b))
}

// ⚠️ WARNING: These break Go's safety guarantees!
// Only use when:
// 1. You're certain the data won't be modified
// 2. Performance profiling proves it's necessary
// 3. You document WHY it's safe in your specific case
```

### Performance Benchmarking

Let me create a benchmark file:**To run these benchmarks**:

```bash
go test -bench=. -benchmem bytes_benchmark_test.go
```

**Expected Results Analysis**:

```
BenchmarkStringConcat         : ~100,000 ns/op (SLOW - many allocations)
BenchmarkBytesBuffer          : ~10,000 ns/op  (10x faster)

BenchmarkAppendNoPrealloc     : ~500,000 ns/op (many reallocations)
BenchmarkAppendWithPrealloc   : ~50,000 ns/op  (10x faster)

BenchmarkIndex                : ~100 ns/op
BenchmarkIndexByte            : ~20 ns/op      (5x faster for single byte)

BenchmarkBytesEqual           : ~10 ns/op      (optimized assembly)
BenchmarkManualEqual          : ~80 ns/op      (8x slower)
```

### Memory Allocation Patterns

```go
package main

import "fmt"

func demonstrateAllocation() {
    // Small allocation (< 32KB): Uses fast path, allocated on stack if possible
    small := make([]byte, 1024)
    
    // Large allocation (> 32KB): Goes directly to heap
    large := make([]byte, 64*1024)
    
    // Growth pattern: Capacity doubles until 1024, then grows by 25%
    var growth []byte
    for i := 0; i < 20; i++ {
        growth = append(growth, 'x')
        fmt.Printf("len=%d, cap=%d\n", len(growth), cap(growth))
    }
}
```

**Growth Visualization**:

```
Append growth pattern:
Step  Length  Capacity  Growth Strategy
────────────────────────────────────────
0     1       1         Initial
1     2       2         Double (1 → 2)
2     3       4         Double (2 → 4)
3     4       4         No growth
4     5       8         Double (4 → 8)
5     8       8         No growth
...
10    ...     1024      Double (512 → 1024)
11    ...     1280      +25% (1024 → 1280)
12    ...     1600      +25% (1280 → 1600)
```

---

## 6. Advanced Patterns & Techniques

### 6.1 Efficient String Building

```go
package main

import (
    "bytes"
    "fmt"
    "strings"
)

// Pattern 1: Using bytes.Buffer for dynamic content
func buildHTML(title string, items []string) string {
    var buf bytes.Buffer
    
    buf.WriteString("<html><head><title>")
    buf.WriteString(title)
    buf.WriteString("</title></head><body><ul>")
    
    for _, item := range items {
        buf.WriteString("<li>")
        buf.WriteString(item)
        buf.WriteString("</li>")
    }
    
    buf.WriteString("</ul></body></html>")
    return buf.String()
}

// Pattern 2: Using strings.Builder (Go 1.10+)
// Similar to bytes.Buffer but optimized for string building
func buildHTMLOptimized(title string, items []string) string {
    var builder strings.Builder
    
    // Pre-calculate approximate size
    builder.Grow(len(title) + 100 + len(items)*20)
    
    builder.WriteString("<html><head><title>")
    builder.WriteString(title)
    builder.WriteString("</title></head><body><ul>")
    
    for _, item := range items {
        builder.WriteString("<li>")
        builder.WriteString(item)
        builder.WriteString("</li>")
    }
    
    builder.WriteString("</ul></body></html>")
    return builder.String()
}

func main() {
    items := []string{"Apple", "Banana", "Cherry"}
    html := buildHTMLOptimized("Fruits", items)
    fmt.Println(html)
}
```

**Cognitive Principle - Chunking**: Pre-calculating sizes and pre-allocating reduces cognitive load on the garbage collector, similar to how organizing information into chunks improves human memory.

### 6.2 Zero-Allocation Parsing

```go
package main

import (
    "bytes"
    "fmt"
)

// Parse CSV without allocating new slices for each field
func parseCSVZeroAlloc(data []byte, callback func(field []byte)) {
    start := 0
    for i := 0; i < len(data); i++ {
        if data[i] == ',' || i == len(data)-1 {
            end := i
            if i == len(data)-1 {
                end = i + 1
            }
            callback(data[start:end])
            start = i + 1
        }
    }
}

func main() {
    csv := []byte("apple,banana,cherry,date")
    
    parseCSVZeroAlloc(csv, func(field []byte) {
        fmt.Printf("Field: %s\n", field)
    })
}
```

**Performance Insight**: By passing slices (views) instead of copying data, we achieve O(n) time with O(1) extra space instead of O(n) space.

### 6.3 Byte Pool Pattern

```go
package main

import (
    "bytes"
    "sync"
)

// Object pooling reduces GC pressure for frequently allocated objects
var bufferPool = sync.Pool{
    New: func() interface{} {
        return new(bytes.Buffer)
    },
}

func processData(data []byte) []byte {
    // Get buffer from pool
    buf := bufferPool.Get().(*bytes.Buffer)
    defer func() {
        buf.Reset()           // Clear for reuse
        bufferPool.Put(buf)   // Return to pool
    }()
    
    // Use the buffer
    buf.WriteString("Processed: ")
    buf.Write(data)
    
    // Must copy since buffer will be reused
    result := make([]byte, buf.Len())
    copy(result, buf.Bytes())
    return result
}

func main() {
    data := []byte("Hello")
    result := processData(data)
    println(string(result))
}
```

**Mental Model - Object Pooling**: Like renting equipment instead of buying new each time. Reduces allocation overhead in high-throughput scenarios.

### 6.4 Custom Reader/Writer

```go
package main

import (
    "fmt"
    "io"
)

// Custom reader that reads from a byte slice
type ByteReader struct {
    data []byte
    pos  int
}

func NewByteReader(data []byte) *ByteReader {
    return &ByteReader{data: data, pos: 0}
}

func (r *ByteReader) Read(p []byte) (n int, err error) {
    if r.pos >= len(r.data) {
        return 0, io.EOF
    }
    
    n = copy(p, r.data[r.pos:])
    r.pos += n
    return n, nil
}

// Custom writer that accumulates bytes
type ByteWriter struct {
    data []byte
}

func (w *ByteWriter) Write(p []byte) (n int, err error) {
    w.data = append(w.data, p...)
    return len(p), nil
}

func main() {
    // Using custom reader
    reader := NewByteReader([]byte("Hello, World!"))
    buf := make([]byte, 5)
    
    for {
        n, err := reader.Read(buf)
        if err == io.EOF {
            break
        }
        fmt.Printf("Read %d bytes: %s\n", n, buf[:n])
    }
    
    // Using custom writer
    writer := &ByteWriter{}
    writer.Write([]byte("First "))
    writer.Write([]byte("Second"))
    fmt.Println(string(writer.data))
}
```

**Interface Concept - io.Reader/Writer**: These are Go's fundamental I/O interfaces. Any type implementing `Read([]byte) (int, error)` is a Reader. This enables **composition** and **abstraction**.

---

## 7. Real-World Applications

### 7.1 HTTP Request/Response Handling

```go
package main

import (
    "bytes"
    "fmt"
    "io"
    "net/http"
)

// Read and modify HTTP response body
func modifyResponse(resp *http.Response) ([]byte, error) {
    // Read body (consumed once)
    body, err := io.ReadAll(resp.Body)
    if err != nil {
        return nil, err
    }
    resp.Body.Close()
    
    // Modify
    modified := bytes.ReplaceAll(body, []byte("old"), []byte("new"))
    
    // Restore body for further reading
    resp.Body = io.NopCloser(bytes.NewReader(modified))
    
    return modified, nil
}

// Build HTTP request with JSON body
func buildJSONRequest(url string, jsonData []byte) (*http.Request, error) {
    req, err := http.NewRequest("POST", url, bytes.NewReader(jsonData))
    if err != nil {
        return nil, err
    }
    
    req.Header.Set("Content-Type", "application/json")
    req.ContentLength = int64(len(jsonData))
    
    return req, nil
}

func main() {
    json := []byte(`{"name":"Alice","age":30}`)
    req, _ := buildJSONRequest("https://api.example.com", json)
    fmt.Printf("Request: %+v\n", req)
}
```

### 7.2 Binary Protocol Parsing

```go
package main

import (
    "encoding/binary"
    "fmt"
)

// Example: Parse simple binary protocol
// Format: [4-byte length][payload]

func encodeMessage(message []byte) []byte {
    buf := make([]byte, 4+len(message))
    
    // Write length (big-endian uint32)
    binary.BigEndian.PutUint32(buf[0:4], uint32(len(message)))
    
    // Write payload
    copy(buf[4:], message)
    
    return buf
}

func decodeMessage(data []byte) ([]byte, error) {
    if len(data) < 4 {
        return nil, fmt.Errorf("insufficient data")
    }
    
    // Read length
    length := binary.BigEndian.Uint32(data[0:4])
    
    if len(data) < int(4+length) {
        return nil, fmt.Errorf("incomplete message")
    }
    
    // Extract payload
    return data[4 : 4+length], nil
}

func main() {
    original := []byte("Hello, Binary!")
    
    encoded := encodeMessage(original)
    fmt.Printf("Encoded (%d bytes): %v\n", len(encoded), encoded)
    
    decoded, _ := decodeMessage(encoded)
    fmt.Printf("Decoded: %s\n", decoded)
}
```

**Binary Protocol Visualization**:

```
Encoded message structure:
┌────────────┬──────────────────────────────┐
│   Length   │          Payload             │
│  (4 bytes) │      (variable length)       │
├────────────┼──────────────────────────────┤
│ 0x00000005 │  H  e  l  l  o              │
│ (uint32)   │ (5 bytes)                   │
└────────────┴──────────────────────────────┘
  Byte 0-3      Byte 4-8
```

### 7.3 File Processing

```go
package main

import (
    "bytes"
    "fmt"
    "os"
)

// Read file and process line by line
func processFileLines(filename string, processor func(line []byte)) error {
    data, err := os.ReadFile(filename)
    if err != nil {
        return err
    }
    
    // Split on newlines without allocating for each line
    start := 0
    for i := 0; i < len(data); i++ {
        if data[i] == '\n' {
            processor(bytes.TrimSpace(data[start:i]))
            start = i + 1
        }
    }
    
    // Process last line if file doesn't end with newline
    if start < len(data) {
        processor(bytes.TrimSpace(data[start:]))
    }
    
    return nil
}

// Find and replace in file
func replaceInFile(filename string, old, new []byte) error {
    data, err := os.ReadFile(filename)
    if err != nil {
        return err
    }
    
    modified := bytes.ReplaceAll(data, old, new)
    
    return os.WriteFile(filename, modified, 0644)
}

func main() {
    // Example: Count lines starting with '#'
    count := 0
    processFileLines("example.txt", func(line []byte) {
        if len(line) > 0 && line[0] == '#' {
            count++
        }
    })
    fmt.Printf("Found %d comment lines\n", count)
}
```

### 7.4 Text Processing & Tokenization

```go
package main

import (
    "bytes"
    "fmt"
    "unicode"
)

// Tokenize text into words (zero-allocation)
func tokenizeWords(text []byte, callback func(word []byte)) {
    start := -1
    
    for i, b := range text {
        if unicode.IsLetter(rune(b)) || unicode.IsDigit(rune(b)) {
            if start == -1 {
                start = i
            }
        } else {
            if start != -1 {
                callback(text[start:i])
                start = -1
            }
        }
    }
    
    // Handle last word
    if start != -1 {
        callback(text[start:])
    }
}

// Word frequency counter
func wordFrequency(text []byte) map[string]int {
    freq := make(map[string]int)
    
    tokenizeWords(text, func(word []byte) {
        // Normalize to lowercase
        lower := bytes.ToLower(word)
        freq[string(lower)]++
    })
    
    return freq
}

func main() {
    text := []byte("Hello world! Hello Go. Go is awesome.")
    
    fmt.Println("Words:")
    tokenizeWords(text, func(word []byte) {
        fmt.Printf("  %s\n", word)
    })
    
    fmt.Println("\nFrequency:")
    for word, count := range wordFrequency(text) {
        fmt.Printf("  %s: %d\n", word, count)
    }
}
```

---

## 8. Complete Reference Examples

Let me create comprehensive example files:Now let me create practice problems:Now let me create one final advanced example showing performance optimization:Perfect! Now let me move all files to the outputs directory:---

## Mental Models for Mastery

### 1. **The Pointer-View Model**
Think of slices as **windows** into arrays. Multiple windows can look at the same data.

```
Mental image: Looking at a street through different windows
- All windows show the SAME street
- Moving in one window affects what others see
- Only copying creates a new, independent street
```

### 2. **The Water Container Analogy**
- **Capacity**: Size of the container
- **Length**: Current water level
- **Append**: Pouring more water
  - If container is full → get bigger container (reallocation)
  - Otherwise → just raise water level

### 3. **The Assembly Line Pattern**
For efficient byte processing:
1. **Pre-allocate** → Set up stations
2. **Process** → Items flow through
3. **Pool reuse** → Recycle containers

---

## Performance Decision Tree

```
Need to process bytes?
│
├─ Small, one-time operation?
│  └─ Use simple []byte operations
│
├─ Building strings incrementally?
│  ├─ Know final size?
│  │  └─ Pre-allocate bytes.Buffer with Grow()
│  └─ Don't know size?
│     └─ Use bytes.Buffer or strings.Builder
│
├─ Searching patterns frequently?
│  ├─ Single byte?
│  │  └─ Use bytes.IndexByte() (5x faster)
│  └─ Multi-byte pattern?
│     └─ Use Boyer-Moore or bytes.Index()
│
├─ High-frequency allocations?
│  └─ Use sync.Pool for buffer reuse
│
└─ Processing large files?
   └─ Use chunked/streaming approach
```

---

## Key Takeaways for Top 1% Performance

### ✅ **Always Do**:
1. **Pre-allocate** when you know approximate sizes
2. **Reuse buffers** with `sync.Pool` in hot paths
3. **Use bytes.Buffer** for string building
4. **Profile before optimizing** (don't guess)

### ❌ **Never Do**:
1. String concatenation in loops (`s += x`)
2. Converting between string/[]byte unnecessarily
3. Allocating in hot loops
4. Ignoring slice capacity

### 🎯 **Complexity Analysis**:
- **bytes.Equal**: O(n) with SIMD optimizations
- **bytes.Index**: O(n*m) worst case, optimized in Go
- **append**: Amortized O(1), worst case O(n) with reallocation
- **copy**: O(n) with assembly optimizations

---

## Next Steps for Deliberate Practice

1. **Run the benchmarks**: See actual performance differences
2. **Solve all practice problems**: Build muscle memory
3. **Profile your code**: Learn to use `pprof`
4. **Read Go source**: Study `bytes` package implementation
5. **Build a project**: Create a CSV parser, HTTP server, or text processor

**Monk's Reminder**: "Understanding is not enough. Practice until the patterns become instinct. The top 1% write code that flows like water—effortless because fundamentals are deeply internalized."

You now have a comprehensive foundation. The files contain:
- **Complete reference** (comprehensive)
- **10 practice problems** (practice)
- **Advanced patterns** (advanced)
- **Performance benchmarks** (benchmark_test)

Run them, study them, modify them. The path to mastery is through deliberate, focused iteration. 🎯

```go
package main

import (
	"bytes"
	"encoding/hex"
	"fmt"
	"io"
	"strings"
)

// ============================================================================
// SECTION 1: Basic Byte Operations
// ============================================================================

func demonstrateBasicOps() {
	fmt.Println("=== BASIC BYTE OPERATIONS ===\n")

	// Creating bytes
	b1 := byte(65)           // Decimal
	b2 := byte(0x41)         // Hex
	b3 := byte('A')          // Character
	fmt.Printf("All represent: %c (%d, 0x%02X, 0b%08b)\n\n", b1, b1, b1, b1)

	// Byte slice creation methods
	literal := []byte{72, 101, 108, 108, 111}
	fromString := []byte("Hello")
	withMake := make([]byte, 5)
	withMakeCap := make([]byte, 5, 10)

	fmt.Printf("Literal:     %s (len=%d, cap=%d)\n", literal, len(literal), cap(literal))
	fmt.Printf("FromString:  %s (len=%d, cap=%d)\n", fromString, len(fromString), cap(fromString))
	fmt.Printf("WithMake:    %v (len=%d, cap=%d)\n", withMake, len(withMake), cap(withMake))
	fmt.Printf("WithMakeCap: %v (len=%d, cap=%d)\n\n", withMakeCap, len(withMakeCap), cap(withMakeCap))
}

// ============================================================================
// SECTION 2: Slice Mechanics
// ============================================================================

func demonstrateSliceMechanics() {
	fmt.Println("=== SLICE MECHANICS ===\n")

	data := []byte("Hello, World!")
	fmt.Printf("Original: %s\n", data)

	// Slicing creates views
	view1 := data[0:5]  // "Hello"
	view2 := data[7:12] // "World"

	fmt.Printf("View1: %s (len=%d, cap=%d)\n", view1, len(view1), cap(view1))
	fmt.Printf("View2: %s (len=%d, cap=%d)\n", view2, len(view2), cap(view2))

	// Modification through view affects original
	view1[0] = 'h'
	fmt.Printf("After modifying view1[0]: %s\n", data)

	// Copying creates independent slice
	copied := make([]byte, len(data))
	copy(copied, data)
	copied[0] = 'H'
	fmt.Printf("Original after copy modification: %s\n", data)
	fmt.Printf("Copied: %s\n\n", copied)

	// Demonstrate append behavior
	fmt.Println("Append growth pattern:")
	var growth []byte
	for i := 0; i < 10; i++ {
		growth = append(growth, byte('x'))
		fmt.Printf("  len=%2d, cap=%2d\n", len(growth), cap(growth))
	}
	fmt.Println()
}

// ============================================================================
// SECTION 3: bytes Package Functions
// ============================================================================

func demonstrateBytesPackage() {
	fmt.Println("=== BYTES PACKAGE FUNCTIONS ===\n")

	// Comparison
	a := []byte("apple")
	b := []byte("banana")
	c := []byte("apple")

	fmt.Println("Comparison:")
	fmt.Printf("  Equal(a, c): %v\n", bytes.Equal(a, c))
	fmt.Printf("  Compare(a, b): %d (a < b)\n", bytes.Compare(a, b))
	fmt.Printf("  Compare(b, a): %d (b > a)\n\n", bytes.Compare(b, a))

	// Searching
	text := []byte("The quick brown fox jumps over the lazy dog")
	fmt.Println("Searching:")
	fmt.Printf("  Contains 'fox': %v\n", bytes.Contains(text, []byte("fox")))
	fmt.Printf("  Index of 'quick': %d\n", bytes.Index(text, []byte("quick")))
	fmt.Printf("  Count 'the': %d\n", bytes.Count(bytes.ToLower(text), []byte("the")))
	fmt.Printf("  IndexByte 'f': %d\n\n", bytes.IndexByte(text, 'f'))

	// Transformation
	fmt.Println("Transformation:")
	messy := []byte("  Hello,  World!  ")
	fmt.Printf("  Original: |%s|\n", messy)
	fmt.Printf("  TrimSpace: |%s|\n", bytes.TrimSpace(messy))
	fmt.Printf("  ToUpper: |%s|\n", bytes.ToUpper(messy))
	fmt.Printf("  ToLower: |%s|\n\n", bytes.ToLower(messy))

	// Splitting and Joining
	csv := []byte("apple,banana,cherry,date")
	parts := bytes.Split(csv, []byte(","))
	fmt.Println("Split and Join:")
	fmt.Printf("  Original: %s\n", csv)
	fmt.Printf("  Split parts: %d\n", len(parts))
	for i, part := range parts {
		fmt.Printf("    %d: %s\n", i, part)
	}
	joined := bytes.Join(parts, []byte(" | "))
	fmt.Printf("  Joined: %s\n\n", joined)
}

// ============================================================================
// SECTION 4: Buffer Usage
// ============================================================================

func demonstrateBuffer() {
	fmt.Println("=== BYTES.BUFFER ===\n")

	var buf bytes.Buffer

	// Writing
	buf.WriteString("Line 1\n")
	buf.WriteByte('>')
	buf.Write([]byte(" Line 2\n"))
	buf.WriteRune('→') // UTF-8 encoded rune

	fmt.Printf("Buffer contents:\n%s\n", buf.String())
	fmt.Printf("Length: %d bytes\n", buf.Len())

	// Reading
	data := make([]byte, 6)
	n, _ := buf.Read(data)
	fmt.Printf("Read %d bytes: %q\n", n, data)
	fmt.Printf("Remaining: %q\n\n", buf.String())

	// Buffer for building
	var builder bytes.Buffer
	builder.WriteString("<html>\n")
	builder.WriteString("  <body>\n")
	builder.WriteString("    <h1>Hello</h1>\n")
	builder.WriteString("  </body>\n")
	builder.WriteString("</html>")

	fmt.Printf("Built HTML:\n%s\n\n", builder.String())
}

// ============================================================================
// SECTION 5: Efficient Patterns
// ============================================================================

// Pattern: Zero-allocation parsing
func parseCSV(data []byte) [][]byte {
	var result [][]byte
	start := 0

	for i := 0; i < len(data); i++ {
		if data[i] == ',' {
			result = append(result, data[start:i])
			start = i + 1
		}
	}
	// Last field
	result = append(result, data[start:])

	return result
}

// Pattern: Streaming processing
func processStream(r io.Reader, processor func([]byte)) error {
	buf := make([]byte, 4096) // 4KB buffer

	for {
		n, err := r.Read(buf)
		if n > 0 {
			processor(buf[:n])
		}
		if err == io.EOF {
			break
		}
		if err != nil {
			return err
		}
	}

	return nil
}

// Pattern: Builder with capacity hint
func buildLargeString(items []string) string {
	var buf bytes.Buffer

	// Estimate size
	totalSize := 0
	for _, item := range items {
		totalSize += len(item) + 1 // +1 for newline
	}
	buf.Grow(totalSize)

	for _, item := range items {
		buf.WriteString(item)
		buf.WriteByte('\n')
	}

	return buf.String()
}

func demonstratePatterns() {
	fmt.Println("=== EFFICIENT PATTERNS ===\n")

	// CSV parsing
	csv := []byte("name,age,city")
	fields := parseCSV(csv)
	fmt.Println("CSV fields:")
	for i, field := range fields {
		fmt.Printf("  %d: %s\n", i, field)
	}
	fmt.Println()

	// Streaming
	fmt.Println("Stream processing:")
	reader := strings.NewReader("This is streaming data that will be processed in chunks")
	processStream(reader, func(chunk []byte) {
		fmt.Printf("  Processed chunk: %q\n", chunk)
	})
	fmt.Println()

	// Building with hint
	items := []string{"First", "Second", "Third"}
	result := buildLargeString(items)
	fmt.Printf("Built string:\n%s\n", result)
}

// ============================================================================
// SECTION 6: Real-World Example - HTTP-like Protocol
// ============================================================================

type Request struct {
	Method  string
	Path    string
	Headers map[string]string
	Body    []byte
}

func parseHTTPRequest(data []byte) (*Request, error) {
	req := &Request{Headers: make(map[string]string)}

	// Find double newline separating headers from body
	headerEnd := bytes.Index(data, []byte("\r\n\r\n"))
	if headerEnd == -1 {
		headerEnd = bytes.Index(data, []byte("\n\n"))
		if headerEnd == -1 {
			return nil, fmt.Errorf("invalid request")
		}
	}

	headerSection := data[:headerEnd]
	req.Body = data[headerEnd+4:]

	// Parse headers
	lines := bytes.Split(headerSection, []byte("\n"))
	if len(lines) < 1 {
		return nil, fmt.Errorf("no request line")
	}

	// Parse request line
	parts := bytes.Fields(lines[0])
	if len(parts) >= 2 {
		req.Method = string(parts[0])
		req.Path = string(parts[1])
	}

	// Parse header fields
	for _, line := range lines[1:] {
		if idx := bytes.IndexByte(line, ':'); idx != -1 {
			key := string(bytes.TrimSpace(line[:idx]))
			value := string(bytes.TrimSpace(line[idx+1:]))
			req.Headers[key] = value
		}
	}

	return req, nil
}

func demonstrateProtocol() {
	fmt.Println("=== HTTP-LIKE PROTOCOL PARSING ===\n")

	rawRequest := []byte("GET /api/users HTTP/1.1\n" +
		"Host: example.com\n" +
		"Content-Type: application/json\n" +
		"\n" +
		"{\"name\":\"Alice\"}")

	req, err := parseHTTPRequest(rawRequest)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}

	fmt.Printf("Method: %s\n", req.Method)
	fmt.Printf("Path: %s\n", req.Path)
	fmt.Println("Headers:")
	for k, v := range req.Headers {
		fmt.Printf("  %s: %s\n", k, v)
	}
	fmt.Printf("Body: %s\n\n", req.Body)
}

// ============================================================================
// SECTION 7: Hex Dump Utility
// ============================================================================

func hexDump(data []byte) string {
	var buf bytes.Buffer
	const bytesPerLine = 16

	for i := 0; i < len(data); i += bytesPerLine {
		// Offset
		buf.WriteString(fmt.Sprintf("%08x  ", i))

		// Hex bytes
		lineEnd := i + bytesPerLine
		if lineEnd > len(data) {
			lineEnd = len(data)
		}

		for j := i; j < lineEnd; j++ {
			buf.WriteString(fmt.Sprintf("%02x ", data[j]))
		}

		// Padding
		for j := lineEnd; j < i+bytesPerLine; j++ {
			buf.WriteString("   ")
		}

		buf.WriteString(" |")

		// ASCII representation
		for j := i; j < lineEnd; j++ {
			if data[j] >= 32 && data[j] <= 126 {
				buf.WriteByte(data[j])
			} else {
				buf.WriteByte('.')
			}
		}

		buf.WriteString("|\n")
	}

	return buf.String()
}

func demonstrateHexDump() {
	fmt.Println("=== HEX DUMP ===\n")

	data := []byte("Hello, World! This is a hex dump example.\x00\x01\x02\xff")
	fmt.Println(hexDump(data))
}

// ============================================================================
// SECTION 8: Binary Data Encoding
// ============================================================================

func demonstrateBinaryEncoding() {
	fmt.Println("=== BINARY ENCODING ===\n")

	data := []byte{0xDE, 0xAD, 0xBE, 0xEF, 0xCA, 0xFE, 0xBA, 0xBE}

	// Hex encoding
	hexStr := hex.EncodeToString(data)
	fmt.Printf("Hex: %s\n", hexStr)

	// Decode back
	decoded, _ := hex.DecodeString(hexStr)
	fmt.Printf("Decoded: %v\n", decoded)
	fmt.Printf("Match: %v\n\n", bytes.Equal(data, decoded))
}

// ============================================================================
// MAIN
// ============================================================================

func main() {
	demonstrateBasicOps()
	demonstrateSliceMechanics()
	demonstrateBytesPackage()
	demonstrateBuffer()
	demonstratePatterns()
	demonstrateProtocol()
	demonstrateHexDump()
	demonstrateBinaryEncoding()
}
```

```go
package main

import (
	"bytes"
	"fmt"
)

// ============================================================================
// PRACTICE PROBLEMS - BYTES MASTERY
// ============================================================================

// Problem 1: Reverse Bytes In-Place
// Difficulty: Easy
// Time Complexity: O(n)
// Space Complexity: O(1)
//
// Task: Reverse a byte slice in-place without allocating new memory
func reverseBytes(data []byte) {
	left, right := 0, len(data)-1
	for left < right {
		data[left], data[right] = data[right], data[left]
		left++
		right--
	}
}

// Problem 2: Find Pattern Occurrences
// Difficulty: Medium
// Time Complexity: O(n*m) naive, O(n+m) with KMP
// Space Complexity: O(1) for naive
//
// Task: Find all starting indices where pattern occurs in text
func findAllOccurrences(text, pattern []byte) []int {
	var indices []int

	if len(pattern) == 0 || len(pattern) > len(text) {
		return indices
	}

	// Naive approach (simple to understand)
	for i := 0; i <= len(text)-len(pattern); i++ {
		match := true
		for j := 0; j < len(pattern); j++ {
			if text[i+j] != pattern[j] {
				match = false
				break
			}
		}
		if match {
			indices = append(indices, i)
		}
	}

	return indices
}

// Problem 3: Run-Length Encoding
// Difficulty: Medium
// Time Complexity: O(n)
// Space Complexity: O(n)
//
// Task: Compress data using run-length encoding
// Example: "aaabbbcc" -> "a3b3c2"
func runLengthEncode(data []byte) []byte {
	if len(data) == 0 {
		return []byte{}
	}

	var result bytes.Buffer

	i := 0
	for i < len(data) {
		current := data[i]
		count := 1

		// Count consecutive occurrences
		for i+count < len(data) && data[i+count] == current {
			count++
		}

		result.WriteByte(current)
		result.WriteString(fmt.Sprintf("%d", count))

		i += count
	}

	return result.Bytes()
}

// Problem 4: Run-Length Decoding
// Difficulty: Medium
// Time Complexity: O(n)
// Space Complexity: O(output_size)
//
// Task: Decompress run-length encoded data
func runLengthDecode(data []byte) []byte {
	var result bytes.Buffer

	i := 0
	for i < len(data) {
		if i+1 >= len(data) {
			break
		}

		char := data[i]
		count := 0

		// Parse count (simple single digit for this example)
		i++
		for i < len(data) && data[i] >= '0' && data[i] <= '9' {
			count = count*10 + int(data[i]-'0')
			i++
		}

		// Write character count times
		for j := 0; j < count; j++ {
			result.WriteByte(char)
		}
	}

	return result.Bytes()
}

// Problem 5: Remove Duplicates (Preserve Order)
// Difficulty: Medium
// Time Complexity: O(n)
// Space Complexity: O(256) = O(1) for bytes
//
// Task: Remove duplicate bytes while preserving first occurrence order
func removeDuplicates(data []byte) []byte {
	seen := make(map[byte]bool)
	result := make([]byte, 0, len(data))

	for _, b := range data {
		if !seen[b] {
			seen[b] = true
			result = append(result, b)
		}
	}

	return result
}

// Problem 6: Rotate Left
// Difficulty: Medium
// Time Complexity: O(n)
// Space Complexity: O(1)
//
// Task: Rotate byte slice left by k positions
// Example: [1,2,3,4,5] rotated by 2 -> [3,4,5,1,2]
func rotateLeft(data []byte, k int) {
	if len(data) == 0 {
		return
	}

	k = k % len(data) // Handle k > len
	if k == 0 {
		return
	}

	// Reverse entire array
	reverse(data, 0, len(data)-1)
	// Reverse second part
	reverse(data, 0, len(data)-k-1)
	// Reverse first part
	reverse(data, len(data)-k, len(data)-1)
}

func reverse(data []byte, left, right int) {
	for left < right {
		data[left], data[right] = data[right], data[left]
		left++
		right--
	}
}

// Problem 7: Longest Common Prefix
// Difficulty: Medium
// Time Complexity: O(n*m) where n=number of strings, m=min length
// Space Complexity: O(1)
//
// Task: Find longest common prefix among byte slices
func longestCommonPrefix(slices [][]byte) []byte {
	if len(slices) == 0 {
		return []byte{}
	}

	prefix := slices[0]

	for i := 1; i < len(slices); i++ {
		// Shorten prefix until it matches
		for !bytes.HasPrefix(slices[i], prefix) {
			prefix = prefix[:len(prefix)-1]
			if len(prefix) == 0 {
				return []byte{}
			}
		}
	}

	return prefix
}

// Problem 8: XOR Encryption/Decryption
// Difficulty: Easy
// Time Complexity: O(n)
// Space Complexity: O(n)
//
// Task: Implement simple XOR cipher with repeating key
func xorCipher(data, key []byte) []byte {
	if len(key) == 0 {
		return data
	}

	result := make([]byte, len(data))
	for i := 0; i < len(data); i++ {
		result[i] = data[i] ^ key[i%len(key)]
	}

	return result
}

// Problem 9: Check if Palindrome
// Difficulty: Easy
// Time Complexity: O(n)
// Space Complexity: O(1)
//
// Task: Check if byte slice is a palindrome (ignoring case and non-alphanumeric)
func isPalindrome(data []byte) bool {
	left, right := 0, len(data)-1

	for left < right {
		// Skip non-alphanumeric
		for left < right && !isAlphaNum(data[left]) {
			left++
		}
		for left < right && !isAlphaNum(data[right]) {
			right--
		}

		// Compare (case-insensitive)
		if toLower(data[left]) != toLower(data[right]) {
			return false
		}

		left++
		right--
	}

	return true
}

func isAlphaNum(b byte) bool {
	return (b >= 'a' && b <= 'z') || (b >= 'A' && b <= 'Z') || (b >= '0' && b <= '9')
}

func toLower(b byte) byte {
	if b >= 'A' && b <= 'Z' {
		return b + ('a' - 'A')
	}
	return b
}

// Problem 10: Word Wrap
// Difficulty: Hard
// Time Complexity: O(n)
// Space Complexity: O(n)
//
// Task: Wrap text to fit within maxWidth characters per line
func wordWrap(text []byte, maxWidth int) [][]byte {
	var lines [][]byte
	words := bytes.Fields(text)

	if len(words) == 0 {
		return lines
	}

	var currentLine bytes.Buffer
	currentLen := 0

	for i, word := range words {
		wordLen := len(word)

		if currentLen == 0 {
			// First word on line
			currentLine.Write(word)
			currentLen = wordLen
		} else if currentLen+1+wordLen <= maxWidth {
			// Word fits on current line
			currentLine.WriteByte(' ')
			currentLine.Write(word)
			currentLen += 1 + wordLen
		} else {
			// Start new line
			lines = append(lines, currentLine.Bytes())
			currentLine.Reset()
			currentLine.Write(word)
			currentLen = wordLen
		}

		// Last word - add the line
		if i == len(words)-1 {
			lines = append(lines, currentLine.Bytes())
		}
	}

	return lines
}

// ============================================================================
// TEST CASES
// ============================================================================

func main() {
	fmt.Println("=== BYTES PRACTICE PROBLEMS ===\n")

	// Problem 1: Reverse
	fmt.Println("1. Reverse Bytes:")
	data1 := []byte("Hello")
	reverseBytes(data1)
	fmt.Printf("   Reversed: %s\n\n", data1)

	// Problem 2: Find Pattern
	fmt.Println("2. Find Pattern Occurrences:")
	text := []byte("ababcababa")
	pattern := []byte("aba")
	indices := findAllOccurrences(text, pattern)
	fmt.Printf("   Pattern '%s' in '%s': %v\n\n", pattern, text, indices)

	// Problem 3: Run-Length Encode
	fmt.Println("3. Run-Length Encoding:")
	original := []byte("aaabbbcc")
	encoded := runLengthEncode(original)
	fmt.Printf("   '%s' -> '%s'\n\n", original, encoded)

	// Problem 4: Run-Length Decode
	fmt.Println("4. Run-Length Decoding:")
	decoded := runLengthDecode(encoded)
	fmt.Printf("   '%s' -> '%s'\n\n", encoded, decoded)

	// Problem 5: Remove Duplicates
	fmt.Println("5. Remove Duplicates:")
	dupes := []byte("aabbccddaa")
	unique := removeDuplicates(dupes)
	fmt.Printf("   '%s' -> '%s'\n\n", dupes, unique)

	// Problem 6: Rotate Left
	fmt.Println("6. Rotate Left:")
	rotate := []byte{1, 2, 3, 4, 5}
	fmt.Printf("   Before: %v\n", rotate)
	rotateLeft(rotate, 2)
	fmt.Printf("   After rotating by 2: %v\n\n", rotate)

	// Problem 7: Longest Common Prefix
	fmt.Println("7. Longest Common Prefix:")
	slices := [][]byte{
		[]byte("flower"),
		[]byte("flow"),
		[]byte("flight"),
	}
	prefix := longestCommonPrefix(slices)
	fmt.Printf("   Prefix of %v: '%s'\n\n", slices, prefix)

	// Problem 8: XOR Cipher
	fmt.Println("8. XOR Cipher:")
	message := []byte("Secret Message")
	key := []byte("KEY")
	encrypted := xorCipher(message, key)
	decrypted := xorCipher(encrypted, key)
	fmt.Printf("   Original:  %s\n", message)
	fmt.Printf("   Encrypted: %v\n", encrypted)
	fmt.Printf("   Decrypted: %s\n\n", decrypted)

	// Problem 9: Palindrome
	fmt.Println("9. Palindrome Check:")
	pal1 := []byte("A man, a plan, a canal: Panama")
	pal2 := []byte("race a car")
	fmt.Printf("   '%s': %v\n", pal1, isPalindrome(pal1))
	fmt.Printf("   '%s': %v\n\n", pal2, isPalindrome(pal2))

	// Problem 10: Word Wrap
	fmt.Println("10. Word Wrap:")
	longText := []byte("The quick brown fox jumps over the lazy dog")
	wrapped := wordWrap(longText, 20)
	fmt.Println("   Wrapped to 20 chars:")
	for i, line := range wrapped {
		fmt.Printf("   Line %d: '%s'\n", i+1, line)
	}
}
```

```go
package main

import (
	"bytes"
	"fmt"
	"sync"
)

// ============================================================================
// ADVANCED PERFORMANCE PATTERNS
// ============================================================================

// Pattern 1: Object Pooling for Buffers
// Use Case: High-frequency buffer allocation (HTTP handlers, parsers)
var bufferPool = sync.Pool{
	New: func() interface{} {
		// Pre-allocate 4KB buffers
		return bytes.NewBuffer(make([]byte, 0, 4096))
	},
}

func processWithPooledBuffer(data []byte) []byte {
	// Get buffer from pool
	buf := bufferPool.Get().(*bytes.Buffer)

	// Ensure buffer is returned to pool
	defer func() {
		buf.Reset()          // Clear contents
		bufferPool.Put(buf)  // Return to pool
	}()

	// Use buffer
	buf.WriteString("Processed: ")
	buf.Write(data)

	// IMPORTANT: Must copy since buffer will be reused
	result := make([]byte, buf.Len())
	copy(result, buf.Bytes())
	return result
}

// Pattern 2: Zero-Copy String to Bytes (UNSAFE but fast)
// WARNING: Only use when you're CERTAIN data won't be modified

// THIS IS FOR EDUCATIONAL PURPOSES ONLY
// In production, always prefer safe conversions unless profiling proves necessity

// Pattern 3: Efficient CSV Parser with Minimal Allocations
type CSVParser struct {
	buf       []byte
	lineStart int
	fieldBuf  []byte
}

func NewCSVParser(capacity int) *CSVParser {
	return &CSVParser{
		buf:      make([]byte, 0, capacity),
		fieldBuf: make([]byte, 0, 256),
	}
}

// ParseLine returns slices into the original buffer (zero-copy)
func (p *CSVParser) ParseLine(line []byte) [][]byte {
	fields := make([][]byte, 0, 8) // Estimate 8 fields
	start := 0

	for i := 0; i < len(line); i++ {
		if line[i] == ',' {
			fields = append(fields, line[start:i])
			start = i + 1
		}
	}

	// Last field
	if start <= len(line) {
		fields = append(fields, line[start:])
	}

	return fields
}

// Pattern 4: Streaming Line Reader (Memory Efficient)
type LineReader struct {
	data []byte
	pos  int
}

func NewLineReader(data []byte) *LineReader {
	return &LineReader{data: data, pos: 0}
}

func (lr *LineReader) ReadLine() ([]byte, bool) {
	if lr.pos >= len(lr.data) {
		return nil, false
	}

	start := lr.pos
	for lr.pos < len(lr.data) && lr.data[lr.pos] != '\n' {
		lr.pos++
	}

	line := lr.data[start:lr.pos]

	// Skip newline
	if lr.pos < len(lr.data) {
		lr.pos++
	}

	return line, true
}

// Pattern 5: Byte Slice Builder (Alternative to bytes.Buffer)
type ByteSliceBuilder struct {
	buf []byte
}

func NewByteSliceBuilder(initialCap int) *ByteSliceBuilder {
	return &ByteSliceBuilder{
		buf: make([]byte, 0, initialCap),
	}
}

func (b *ByteSliceBuilder) Append(data []byte) {
	b.buf = append(b.buf, data...)
}

func (b *ByteSliceBuilder) AppendByte(byte byte) {
	b.buf = append(b.buf, byte)
}

func (b *ByteSliceBuilder) AppendString(s string) {
	b.buf = append(b.buf, s...)
}

func (b *ByteSliceBuilder) Bytes() []byte {
	return b.buf
}

func (b *ByteSliceBuilder) Len() int {
	return len(b.buf)
}

func (b *ByteSliceBuilder) Reset() {
	b.buf = b.buf[:0] // Keep capacity
}

// Pattern 6: Trie for Fast Prefix Matching
// Use Case: URL routing, autocomplete, dictionary lookups
type TrieNode struct {
	children map[byte]*TrieNode
	isEnd    bool
	value    interface{}
}

type ByteTrie struct {
	root *TrieNode
}

func NewByteTrie() *ByteTrie {
	return &ByteTrie{
		root: &TrieNode{children: make(map[byte]*TrieNode)},
	}
}

func (t *ByteTrie) Insert(key []byte, value interface{}) {
	node := t.root
	for _, b := range key {
		if node.children[b] == nil {
			node.children[b] = &TrieNode{children: make(map[byte]*TrieNode)}
		}
		node = node.children[b]
	}
	node.isEnd = true
	node.value = value
}

func (t *ByteTrie) Search(key []byte) (interface{}, bool) {
	node := t.root
	for _, b := range key {
		if node.children[b] == nil {
			return nil, false
		}
		node = node.children[b]
	}
	return node.value, node.isEnd
}

func (t *ByteTrie) HasPrefix(prefix []byte) bool {
	node := t.root
	for _, b := range prefix {
		if node.children[b] == nil {
			return false
		}
		node = node.children[b]
	}
	return true
}

// Pattern 7: Boyer-Moore String Search (Fast Pattern Matching)
// Time Complexity: O(n/m) average case, O(n*m) worst case
func boyerMooreSearch(text, pattern []byte) int {
	if len(pattern) == 0 || len(pattern) > len(text) {
		return -1
	}

	// Build bad character table
	badChar := make(map[byte]int)
	for i := 0; i < len(pattern)-1; i++ {
		badChar[pattern[i]] = len(pattern) - 1 - i
	}

	// Search
	i := len(pattern) - 1
	for i < len(text) {
		j := len(pattern) - 1
		for j >= 0 && text[i] == pattern[j] {
			i--
			j--
		}

		if j < 0 {
			return i + 1 // Found
		}

		// Shift based on bad character
		shift, exists := badChar[text[i]]
		if !exists {
			shift = len(pattern)
		}
		i += max(shift, 1)
	}

	return -1 // Not found
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}

// Pattern 8: Memory-Mapped File Processing Simulation
// (Actual mmap requires syscalls, this demonstrates the concept)
type ChunkedProcessor struct {
	data      []byte
	chunkSize int
}

func NewChunkedProcessor(data []byte, chunkSize int) *ChunkedProcessor {
	return &ChunkedProcessor{
		data:      data,
		chunkSize: chunkSize,
	}
}

func (cp *ChunkedProcessor) Process(handler func(chunk []byte) error) error {
	for offset := 0; offset < len(cp.data); offset += cp.chunkSize {
		end := offset + cp.chunkSize
		if end > len(cp.data) {
			end = len(cp.data)
		}

		chunk := cp.data[offset:end]
		if err := handler(chunk); err != nil {
			return err
		}
	}
	return nil
}

// Pattern 9: Circular Buffer for Streaming
type CircularBuffer struct {
	buf   []byte
	read  int
	write int
	size  int
}

func NewCircularBuffer(size int) *CircularBuffer {
	return &CircularBuffer{
		buf:  make([]byte, size),
		size: size,
	}
}

func (cb *CircularBuffer) Write(data []byte) int {
	written := 0
	for _, b := range data {
		if (cb.write+1)%cb.size == cb.read {
			break // Buffer full
		}
		cb.buf[cb.write] = b
		cb.write = (cb.write + 1) % cb.size
		written++
	}
	return written
}

func (cb *CircularBuffer) Read(p []byte) int {
	read := 0
	for i := 0; i < len(p) && cb.read != cb.write; i++ {
		p[i] = cb.buf[cb.read]
		cb.read = (cb.read + 1) % cb.size
		read++
	}
	return read
}

func (cb *CircularBuffer) Available() int {
	if cb.write >= cb.read {
		return cb.write - cb.read
	}
	return cb.size - cb.read + cb.write
}

// ============================================================================
// DEMONSTRATION
// ============================================================================

func main() {
	fmt.Println("=== ADVANCED BYTES PERFORMANCE PATTERNS ===\n")

	// Pattern 1: Buffer Pooling
	fmt.Println("1. Buffer Pooling:")
	data := []byte("test data")
	result := processWithPooledBuffer(data)
	fmt.Printf("   Result: %s\n\n", result)

	// Pattern 3: CSV Parser
	fmt.Println("3. Zero-Copy CSV Parser:")
	parser := NewCSVParser(1024)
	line := []byte("name,age,city,country")
	fields := parser.ParseLine(line)
	for i, field := range fields {
		fmt.Printf("   Field %d: %s\n", i, field)
	}
	fmt.Println()

	// Pattern 4: Line Reader
	fmt.Println("4. Streaming Line Reader:")
	text := []byte("Line 1\nLine 2\nLine 3")
	reader := NewLineReader(text)
	for {
		line, ok := reader.ReadLine()
		if !ok {
			break
		}
		fmt.Printf("   Read: %s\n", line)
	}
	fmt.Println()

	// Pattern 5: Byte Slice Builder
	fmt.Println("5. Byte Slice Builder:")
	builder := NewByteSliceBuilder(100)
	builder.AppendString("Hello, ")
	builder.AppendString("World!")
	builder.AppendByte('\n')
	fmt.Printf("   Built: %s", builder.Bytes())
	fmt.Println()

	// Pattern 6: Trie
	fmt.Println("6. Byte Trie (Fast Prefix Matching):")
	trie := NewByteTrie()
	trie.Insert([]byte("apple"), "🍎")
	trie.Insert([]byte("application"), "📱")
	trie.Insert([]byte("apply"), "✅")

	if val, found := trie.Search([]byte("apple")); found {
		fmt.Printf("   Found 'apple': %v\n", val)
	}
	fmt.Printf("   Has prefix 'app': %v\n", trie.HasPrefix([]byte("app")))
	fmt.Println()

	// Pattern 7: Boyer-Moore Search
	fmt.Println("7. Boyer-Moore String Search:")
	haystack := []byte("The quick brown fox jumps over the lazy dog")
	needle := []byte("fox")
	idx := boyerMooreSearch(haystack, needle)
	fmt.Printf("   Pattern '%s' found at index: %d\n", needle, idx)
	fmt.Println()

	// Pattern 8: Chunked Processing
	fmt.Println("8. Chunked Processing:")
	bigData := make([]byte, 1000)
	for i := range bigData {
		bigData[i] = byte(i % 256)
	}
	processor := NewChunkedProcessor(bigData, 100)
	chunkCount := 0
	processor.Process(func(chunk []byte) error {
		chunkCount++
		return nil
	})
	fmt.Printf("   Processed %d chunks of 100 bytes\n", chunkCount)
	fmt.Println()

	// Pattern 9: Circular Buffer
	fmt.Println("9. Circular Buffer:")
	cbuf := NewCircularBuffer(10)
	written := cbuf.Write([]byte("Hello"))
	fmt.Printf("   Written: %d bytes\n", written)
	fmt.Printf("   Available: %d bytes\n", cbuf.Available())

	readBuf := make([]byte, 5)
	readCount := cbuf.Read(readBuf)
	fmt.Printf("   Read: %d bytes: %s\n", readCount, readBuf[:readCount])
	fmt.Printf("   Available after read: %d bytes\n", cbuf.Available())
}
```

```go
package main

import (
	"bytes"
	"testing"
)

// Benchmark: String concatenation vs Buffer
func BenchmarkStringConcat(b *testing.B) {
	for i := 0; i < b.N; i++ {
		var s string
		for j := 0; j < 1000; j++ {
			s += "x"
		}
	}
}

func BenchmarkBytesBuffer(b *testing.B) {
	for i := 0; i < b.N; i++ {
		var buf bytes.Buffer
		for j := 0; j < 1000; j++ {
			buf.WriteByte('x')
		}
		_ = buf.String()
	}
}

// Benchmark: Slice append with/without preallocation
func BenchmarkAppendNoPrealloc(b *testing.B) {
	for i := 0; i < b.N; i++ {
		var slice []byte
		for j := 0; j < 10000; j++ {
			slice = append(slice, byte(j%256))
		}
	}
}

func BenchmarkAppendWithPrealloc(b *testing.B) {
	for i := 0; i < b.N; i++ {
		slice := make([]byte, 0, 10000)
		for j := 0; j < 10000; j++ {
			slice = append(slice, byte(j%256))
		}
	}
}

// Benchmark: Index vs IndexByte
func BenchmarkIndex(b *testing.B) {
	data := []byte("Hello, World! This is a longer string to search through.")
	needle := []byte("o")
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = bytes.Index(data, needle)
	}
}

func BenchmarkIndexByte(b *testing.B) {
	data := []byte("Hello, World! This is a longer string to search through.")
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = bytes.IndexByte(data, 'o')
	}
}

// Benchmark: Equal vs manual comparison
func BenchmarkBytesEqual(b *testing.B) {
	a := []byte("This is a test string for comparison benchmarks")
	b2 := []byte("This is a test string for comparison benchmarks")
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = bytes.Equal(a, b2)
	}
}

func BenchmarkManualEqual(b *testing.B) {
	a := []byte("This is a test string for comparison benchmarks")
	b2 := []byte("This is a test string for comparison benchmarks")
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		equal := true
		if len(a) != len(b2) {
			equal = false
		} else {
			for j := 0; j < len(a); j++ {
				if a[j] != b2[j] {
					equal = false
					break
				}
			}
		}
		_ = equal
	}
}

// Benchmark: Copy operations
func BenchmarkCopyBuiltin(b *testing.B) {
	src := make([]byte, 10000)
	dst := make([]byte, 10000)
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		copy(dst, src)
	}
}

func BenchmarkCopyManual(b *testing.B) {
	src := make([]byte, 10000)
	dst := make([]byte, 10000)
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		for j := 0; j < len(src); j++ {
			dst[j] = src[j]
		}
	}
}
```