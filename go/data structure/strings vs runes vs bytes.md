# Strings vs Runes vs Bytes in Go — The Complete Mental Model

Understanding this trinity is foundational to writing correct, performant Go. Most bugs in text processing stem from conflating these three distinct concepts. Let's build a precise mental model from the ground up.

---

## 1. The Memory Reality — What Go Actually Stores

Before touching syntax, internalize the physical layout:

```
string "Hello, 世界"

Memory layout (bytes):
H    e    l    l    o    ,         世          界
0x48 0x65 0x6C 0x6C 0x6F 0x2C 0x20 0xE4 0xB8 0x96 0xE7 0x95 0x8C
[0]  [1]  [2]  [3]  [4]  [5]  [6]  [7]  [8]  [9]  [10] [11] [12]

len("Hello, 世界") = 13   ← bytes, NOT characters
```

The moment you see this, the entire model crystallizes: **a Go string is a read-only slice of bytes.** It has no inherent encoding awareness — it just stores bytes. The *convention* (enforced by Go tooling and string literals) is UTF-8, but the type itself doesn't enforce it.

---

## 2. The Three Types — Precise Definitions

### `byte` — alias for `uint8`

```go
var b byte = 'A'   // 65
var b2 byte = 0x41 // same thing
```

A single octet. No encoding knowledge. It's the atomic unit of storage.

### `rune` — alias for `int32`

```go
var r rune = '世'   // 19990 (Unicode code point U+4E16)
var r2 rune = '\u4E16' // identical
```

A Unicode code point. This is the atomic unit of *meaning* in text. Critically, a single rune can occupy **1 to 4 bytes** when encoded as UTF-8.

### `string` — immutable byte sequence

```go
// Internal struct (from runtime):
type StringHeader struct {
    Data uintptr // pointer to backing array
    Len  int     // number of BYTES
}
```

This internal representation is everything. A string is not a character array. It's a (pointer, length) pair pointing at bytes.

---

## 3. UTF-8 Encoding — The Bridge Between Runes and Bytes

Go source code is UTF-8. String literals are UTF-8. Understanding the encoding scheme eliminates all confusion:

```
Code point range       | Byte pattern
U+0000   – U+007F      | 0xxxxxxx                          (1 byte)
U+0080   – U+07FF      | 110xxxxx 10xxxxxx                 (2 bytes)
U+0800   – U+FFFF      | 1110xxxx 10xxxxxx 10xxxxxx        (3 bytes)
U+10000  – U+10FFFF    | 11110xxx 10xxxxxx 10xxxxxx 10xxxxxx (4 bytes)
```

This means:
- ASCII characters (A-Z, 0-9, common symbols) → 1 byte → `byte == rune` value
- Most European/Cyrillic characters → 2 bytes
- CJK characters (Chinese, Japanese, Korean) → 3 bytes
- Emoji, ancient scripts → 4 bytes

```go
package main

import (
    "fmt"
    "unicode/utf8"
)

func main() {
    s := "Hello, 世界"

    fmt.Println(len(s))                    // 13  (bytes)
    fmt.Println(utf8.RuneCountInString(s)) // 9   (runes/characters)
}
```

---

## 4. Indexing — The Most Common Source of Bugs

```go
s := "Hello, 世界"

// Byte indexing — always valid
fmt.Printf("%x\n", s[7])  // e4 (first byte of '世', NOT the character)

// Rune iteration — correct
for i, r := range s {
    fmt.Printf("index=%d rune=%c bytes=%d\n", i, r, utf8.RuneLen(r))
}
```

Output of range loop:
```
index=0  rune=H  bytes=1
index=1  rune=e  bytes=1
...
index=7  rune=世  bytes=3
index=10 rune=界  bytes=3
```

**Critical insight**: `i` in `range` is the **byte offset** of where the rune starts, not its ordinal position. The indices jump from 7 to 10 because '世' occupies 3 bytes.

---

## 5. Conversions — The Full Conversion Matrix

```go
s := "Hello, 世界"

// string → []byte
b := []byte(s)          // allocates, copies bytes
// b[7] = 0xE4 (first byte of '世')

// string → []rune  
r := []rune(s)          // allocates, decodes UTF-8
// r[7] = '世' (rune 19990)
// len(r) = 9

// []byte → string
s2 := string(b)         // allocates, copies

// []rune → string
s3 := string(r)         // allocates, encodes UTF-8

// rune → string (encodes single rune as UTF-8)
s4 := string('世')       // "世" (3 bytes)
s5 := string(65)        // "A"  NOT "65"!  ← common trap

// int → string TRAP:
n := 65
_ = string(n)   // "A", not "65" — use strconv.Itoa(n) for that
```

### Conversion Cost Model

Every conversion between `string` and `[]byte` or `[]rune` **allocates and copies** unless the compiler can prove the slice isn't modified (it sometimes can optimize this away). For performance-critical paths:

```go
// Avoid in hot loops:
for _, r := range []rune(s) { ... }  // allocation each iteration if not optimized

// Prefer:
for _, r := range s { ... }  // range on string directly — no allocation
```

---

## 6. The `strings`, `unicode`, `utf8` Packages — Know the Boundaries

```go
import (
    "strings"
    "unicode"
    "unicode/utf8"
)

s := "Hello, 世界!"

// strings package — operates at byte level for ASCII, rune-aware for others
strings.ToUpper(s)           // correct, rune-aware
strings.Contains(s, "世")    // correct
strings.Index(s, "世")       // returns BYTE index (7), not rune index

// unicode package — predicates on runes
unicode.IsLetter('世')        // true
unicode.IsUpper('A')          // true
unicode.ToLower('Ñ')          // 'ñ'

// utf8 package — low-level encoding operations
utf8.RuneCountInString(s)     // 9
utf8.ValidString(s)           // true
utf8.RuneLen('世')             // 3

// Decode a single rune manually:
r, size := utf8.DecodeRuneInString(s[7:])
// r = '世', size = 3
```

---

## 7. String Immutability and Builder Pattern

Strings are immutable. Every concatenation with `+` creates a new allocation:

```go
// Naive — O(n²) allocations
result := ""
for i := 0; i < 1000; i++ {
    result += "x"  // allocates new string each iteration
}

// Correct — strings.Builder uses a []byte internally
var sb strings.Builder
for i := 0; i < 1000; i++ {
    sb.WriteByte('x')
}
result := sb.String()  // single allocation at the end
```

`strings.Builder.String()` is special — it converts its internal `[]byte` to a `string` **without copying** by using an unsafe pointer cast. This is the one place in the standard library where that conversion is zero-cost.

---

## 8. Byte Slices vs Strings — When to Use Which

| Concern | Use `string` | Use `[]byte` |
|---|---|---|
| Immutability needed | ✓ | |
| Map key | ✓ | |
| Comparison with `==` | ✓ | |
| Mutation needed | | ✓ |
| I/O (Reader/Writer) | | ✓ |
| Cryptography/hashing | | ✓ |
| Building incrementally | | ✓ (then convert) |

The compiler can sometimes eliminate the allocation when converting `[]byte` to `string` for map lookup:

```go
m := map[string]int{"hello": 1}
b := []byte("hello")
v := m[string(b)]  // compiler may optimize away the allocation here
```

---

## 9. Common Traps — Ranked by Frequency

**Trap 1: Byte-indexing multibyte strings**
```go
s := "世界"
fmt.Println(s[0])        // 228 (byte), NOT '世'
fmt.Println(string(s[0])) // "ä" — garbage character!

// Correct:
r, _ := utf8.DecodeRuneInString(s)
fmt.Println(string(r))   // "世"
```

**Trap 2: Slicing by byte index mid-rune**
```go
s := "世界"
fmt.Println(s[:2])  // invalid UTF-8 — sliced mid-character
// Go won't panic, but the bytes are meaningless as text

// Safe slicing by rune position:
runes := []rune(s)
fmt.Println(string(runes[:1]))  // "世"
```

**Trap 3: `len` on string**
```go
s := "世界"
fmt.Println(len(s))        // 6  (bytes)
fmt.Println(len([]rune(s))) // 2  (characters) — allocation!
fmt.Println(utf8.RuneCountInString(s)) // 2 — no allocation
```

**Trap 4: `string(integer)` doesn't stringify**
```go
fmt.Println(string(97))   // "a"  (rune U+0061)
fmt.Println(string(1000)) // "Ϩ"  (rune U+03E8)
// Use fmt.Sprintf("%d", n) or strconv.Itoa(n)
```

**Trap 5: Modifying a string via `[]byte` and assuming references update**
```go
s := "hello"
b := []byte(s)   // COPY — s and b are independent
b[0] = 'H'
fmt.Println(s)   // "hello" — unchanged
fmt.Println(string(b)) // "Hello"
```

---

## 10. Performance Mental Model

Build this hierarchy in your mind for string operations:

```
Fastest → Slowest

Direct byte access  s[i]                         O(1), no allocation
range s             for i, r := range s           O(n), no allocation
utf8.DecodeRune     manual decode                 O(1), no allocation
[]byte(s)           conversion                    O(n), allocates
[]rune(s)           conversion + decode           O(n), allocates
strings.Builder     incremental build             O(n) amortized
"+" concatenation   repeated                      O(n²), many allocations
```

---

## 11. Practical Pattern — Correct Rune Manipulation

Here's a complete, idiomatic example covering all edge cases:

```go
package main

import (
    "fmt"
    "strings"
    "unicode"
    "unicode/utf8"
)

// Reverse a string correctly (by rune, not by byte)
func reverseString(s string) string {
    runes := []rune(s)
    for i, j := 0, len(runes)-1; i < j; i, j = i+1, j-1 {
        runes[i], runes[j] = runes[j], runes[i]
    }
    return string(runes)
}

// Count words handling Unicode letters
func wordCount(s string) int {
    count := 0
    inWord := false
    for _, r := range s {
        if unicode.IsLetter(r) || unicode.IsDigit(r) {
            if !inWord {
                count++
                inWord = true
            }
        } else {
            inWord = false
        }
    }
    return count
}

// Safe rune at position (O(n) — unavoidable without indexing structure)
func runeAt(s string, pos int) (rune, bool) {
    i := 0
    for _, r := range s {
        if i == pos {
            return r, true
        }
        i++
    }
    return 0, false
}

// Build string efficiently from rune transformations
func processString(s string) string {
    var sb strings.Builder
    sb.Grow(len(s)) // pre-allocate — len(s) bytes is a safe lower bound
    for _, r := range s {
        if unicode.IsUpper(r) {
            sb.WriteRune(unicode.ToLower(r))
        } else {
            sb.WriteRune(r)
        }
    }
    return sb.String()
}

func main() {
    s := "Hello, 世界! 🌍"
    
    fmt.Println("Bytes:", len(s))
    fmt.Println("Runes:", utf8.RuneCountInString(s))
    fmt.Println("Reversed:", reverseString(s))
    fmt.Println("Words:", wordCount(s))
    fmt.Println("Processed:", processString(s))
    
    r, _ := runeAt(s, 7)
    fmt.Printf("Rune at position 7: %c (U+%04X)\n", r, r)
}
```

---

## 12. The Expert's Mental Checklist

When writing any string-handling code, run through this:

1. **Am I using `len(s)` to mean characters?** → Use `utf8.RuneCountInString(s)`
2. **Am I indexing `s[i]` and expecting a character?** → Use `range` or `utf8.DecodeRuneInString`
3. **Am I slicing `s[a:b]` at computed positions?** → Verify positions are on rune boundaries
4. **Am I building a string in a loop?** → Use `strings.Builder` with `Grow`
5. **Am I converting `string(integer)`?** → Use `strconv.Itoa` or `fmt.Sprintf`
6. **Do I need mutation?** → Work with `[]byte`, convert to `string` at the end

---

The master insight is this: **Go separates storage (bytes), encoding unit (rune), and container (string) as distinct concerns.** Most languages blur these. Go forces you to be explicit, which is why Go string code is more correct — and why developers who don't internalize this model write subtly broken code for years.