# String Manipulation in Go: A Deep Mental Model

## Why Go "Struggles" With Strings — The Root Cause

Most languages lie to you about strings. Go doesn't.

In Python, Java, or JavaScript, a string is a sequence of *characters*. That feels natural. But it's an abstraction that hides a painful truth: **computers don't store characters, they store bytes**. The moment you hit non-ASCII text (Chinese, Arabic, emoji, Malayalam — your own language), that abstraction breaks.

Go forces you to confront this truth directly. A Go string is, by definition:

> **An immutable, read-only slice of bytes (`[]byte`). Nothing more.**

```go
s := "hello"
fmt.Println(len(s)) // 5 — this is BYTES, not characters
```

```go
s := "നമസ്കാരം" // Malayalam: "Namaskaram"
fmt.Println(len(s)) // 24 — bytes, not 8 characters
```

This is not a bug. This is Go refusing to paper over the complexity of Unicode.

---

## The Unicode Problem — Why Bytes ≠ Characters

### ASCII Era (Simple World)
Every character fit in 1 byte (0–127). `len(s)` == number of characters. Life was easy.

### Unicode Era (Real World)
Unicode defines **1,114,112 code points** (U+0000 to U+10FFFF). A *code point* is the abstract identity of a character — `A` is U+0041, `😀` is U+1F600, `ക` is U+0D15.

**UTF-8** is the *encoding* — how you store code points as bytes:

| Code Point Range | Bytes Used |
|---|---|
| U+0000 – U+007F | 1 byte (ASCII compatible) |
| U+0080 – U+07FF | 2 bytes |
| U+0800 – U+FFFF | 3 bytes |
| U+10000 – U+10FFFF | 4 bytes |

Go source files are UTF-8. Go strings are UTF-8 byte sequences. This is the design.

---

## The Rune — Go's Answer to "What Is a Character?"

A `rune` is simply an alias for `int32`. It represents a **Unicode code point**.

```go
type rune = int32
```

That's it. No magic. It's a 32-bit integer large enough to hold any Unicode code point (max value ~1.1 million, fits easily in int32).

```go
var r rune = 'ക'
fmt.Println(r)        // 3349 — the Unicode code point number
fmt.Printf("%c\n", r) // ക — the character
fmt.Printf("%U\n", r) // U+0D15 — Unicode notation
```

### The Mental Model

```
String  →  []byte  →  raw memory (what the OS/network sees)
String  →  []rune  →  sequence of Unicode code points (what humans see)
```

A single `rune` can occupy 1 to 4 bytes in a string. When you iterate with index, you get bytes. When you iterate with `range`, Go automatically decodes UTF-8 and gives you runes.

---

## String Internals — Memory Layout

```go
// A string header in Go is just two words:
type StringHeader struct {
    Data uintptr // pointer to byte array
    Len  int     // number of bytes
}
```

Strings are **immutable**. You cannot do `s[0] = 'X'`. This is a deliberate choice enabling safe sharing without copying — two strings can point to the same underlying memory.

```go
s := "hello world"
sub := s[6:11] // "world" — NO copy, shares memory with s
```

---

## Iteration: The Critical Distinction

### Byte Iteration (index loop) — Dangerous for Unicode
```go
s := "café"
for i := 0; i < len(s); i++ {
    fmt.Printf("byte[%d] = %x\n", i, s[i])
}
// byte[0] = 63  (c)
// byte[1] = 61  (a)
// byte[2] = 66  (f)
// byte[3] = c3  ← first byte of 'é' (2-byte UTF-8)
// byte[4] = a9  ← second byte of 'é'
```

You get 5 iterations for a 4-character word. Indexing mid-rune gives you garbage.

### Rune Iteration (range loop) — Correct for Unicode
```go
s := "café"
for i, r := range s {
    fmt.Printf("index=%d rune=%c codepoint=%U\n", i, r, r)
}
// index=0 rune=c codepoint=U+0063
// index=1 rune=a codepoint=U+0061
// index=2 rune=f codepoint=U+0066
// index=3 rune=é codepoint=U+00E9  ← index 3, but occupies bytes 3-4
```

`range` on a string yields `(byte_index, rune)`. The byte index jumps by the rune's width. This is the idiomatic Go way to walk characters.

---

## String Conversion Triad

```go
s := "hello, 世界"

// String → []byte (for byte-level manipulation, I/O)
b := []byte(s)      // COPIES the data
b[0] = 'H'
s2 := string(b)     // COPIES back

// String → []rune (for character-level manipulation)
r := []rune(s)      // COPIES, decodes UTF-8
fmt.Println(len(r)) // 9 — actual character count
r[7] = '地'
s3 := string(r)     // COPIES, re-encodes to UTF-8

// Single byte index → rune (unsafe if multi-byte at that position)
// Correct way: use utf8.DecodeRuneInString
```

**Performance note:** Every conversion allocates. In hot paths, avoid converting back and forth. The compiler sometimes optimizes away allocations in simple cases (like `[]byte(s)` used in a function call), but don't rely on it.

---

## The `strings` Package — Your Primary Tool

```go
import "strings"
```

### Searching
```go
s := "the quick brown fox"

strings.Contains(s, "quick")        // true
strings.HasPrefix(s, "the")         // true
strings.HasSuffix(s, "fox")         // true
strings.Index(s, "brown")           // 10 (byte index)
strings.LastIndex(s, "o")           // 17
strings.Count(s, "o")               // 2
strings.ContainsRune(s, 'q')        // true
strings.ContainsAny(s, "aeiou")     // true (any vowel)
```

### Transformation
```go
strings.ToUpper(s)                  // Unicode-aware
strings.ToLower(s)
strings.Title(s)                    // deprecated, use golang.org/x/text
strings.TrimSpace("  hello  ")      // "hello"
strings.Trim("--hello--", "-")      // "hello"
strings.TrimLeft("--hello--", "-")  // "hello--"
strings.TrimRight("--hello--", "-") // "--hello"
strings.TrimPrefix(s, "the ")       // "quick brown fox"
strings.TrimSuffix(s, " fox")       // "the quick brown"
strings.Replace(s, "o", "0", -1)    // all occurrences (-1 = all)
strings.Replace(s, "o", "0", 1)     // only first
strings.ReplaceAll(s, "o", "0")     // cleaner alias for Replace(...,-1)
```

### Splitting and Joining
```go
parts := strings.Split("a,b,c", ",")     // ["a","b","c"]
parts  = strings.SplitN("a,b,c", ",", 2) // ["a","b,c"] — max 2 parts
parts  = strings.Fields("  a  b  c  ")   // ["a","b","c"] — splits on any whitespace

strings.Join([]string{"a","b","c"}, "-") // "a-b-c"
```

### The `strings.Builder` — Efficient Concatenation
Never use `+` in a loop. Each `+` creates a new string (new allocation, copy). `strings.Builder` amortizes allocations like `ArrayList`:

```go
var sb strings.Builder
sb.Grow(64) // pre-allocate if you know approximate size

for i := 0; i < 5; i++ {
    sb.WriteString("hello")
    sb.WriteByte(' ')
    sb.WriteRune('世')
    sb.WriteByte('\n')
}

result := sb.String() // single allocation at the end
sb.Reset()            // reuse the builder (keeps underlying array)
```

**Complexity:** `+` in loop = O(n²) time. `strings.Builder` = O(n) amortized.

### `strings.Reader` — String as io.Reader
```go
r := strings.NewReader("hello world")
// Implements io.Reader, io.Seeker, io.WriterTo
// Useful for APIs that expect io.Reader without []byte conversion
```

---

## The `unicode` and `unicode/utf8` Packages

### `unicode` — Rune Classification
```go
import "unicode"

unicode.IsLetter('A')    // true
unicode.IsDigit('5')     // true
unicode.IsSpace(' ')     // true
unicode.IsUpper('A')     // true
unicode.IsLower('a')     // true
unicode.IsPunct('.')     // true
unicode.ToUpper('a')     // 'A'
unicode.ToLower('A')     // 'a'
```

These work correctly for ALL Unicode, not just ASCII. `unicode.IsLetter('ക')` returns true.

### `unicode/utf8` — Low-Level UTF-8 Operations
```go
import "unicode/utf8"

s := "café"
utf8.RuneCountInString(s)            // 4 — character count
utf8.ValidString(s)                  // true — valid UTF-8?

r, size := utf8.DecodeRuneInString(s)     // first rune + byte width
r, size  = utf8.DecodeLastRuneInString(s) // last rune + byte width

utf8.RuneLen('é')  // 2 — how many bytes this rune needs
utf8.RuneLen('A')  // 1
utf8.RuneLen('世')  // 3

// Encode a rune into bytes
buf := make([]byte, utf8.UTFMax) // UTFMax = 4
n := utf8.EncodeRune(buf, '世')   // n = 3
```

### Manual UTF-8 Walking (Zero Allocation)
This is the expert technique — walk a string character by character without converting to `[]rune`:

```go
func countVowels(s string) int {
    count := 0
    for i := 0; i < len(s); {
        r, size := utf8.DecodeRuneInString(s[i:])
        if r == utf8.RuneError && size == 1 {
            // invalid UTF-8 byte
            i++
            continue
        }
        switch unicode.ToLower(r) {
        case 'a', 'e', 'i', 'o', 'u':
            count++
        }
        i += size
    }
    return count
}
```

This is O(n) time, zero heap allocations — superior to converting to `[]rune` first.

---

## `strconv` Package — String ↔ Primitive Conversion

```go
import "strconv"

// Int → String
s := strconv.Itoa(42)              // "42" (fast path)
s  = strconv.FormatInt(42, 10)     // "42" (base 10)
s  = strconv.FormatInt(255, 16)    // "ff" (hex)
s  = strconv.FormatInt(8, 2)       // "1000" (binary)
s  = strconv.FormatFloat(3.14, 'f', 2, 64) // "3.14"
s  = strconv.FormatBool(true)      // "true"

// String → Int
n, err := strconv.Atoi("42")       // fast path
n64, err := strconv.ParseInt("ff", 16, 64)  // hex → int64
f, err  := strconv.ParseFloat("3.14", 64)
b, err  := strconv.ParseBool("true")

// Quote / Unquote (useful for escaping)
strconv.Quote("hello\nworld")      // `"hello\nworld"`
strconv.Unquote(`"hello\nworld"`)  // "hello\nworld", nil
```

**Prefer `strconv` over `fmt.Sprintf` for performance.** `fmt.Sprintf("%d", n)` uses reflection and is significantly slower than `strconv.Itoa(n)`.

---

## `fmt` Package — Formatted String Building

```go
s := fmt.Sprintf("Hello, %s! You are %d years old.", name, age)

// Verb reference for DSA work:
fmt.Sprintf("%d", 42)       // decimal
fmt.Sprintf("%b", 42)       // binary: 101010
fmt.Sprintf("%x", 255)      // hex: ff
fmt.Sprintf("%o", 8)        // octal: 10
fmt.Sprintf("%f", 3.14)     // float
fmt.Sprintf("%.2f", 3.14159) // 3.14
fmt.Sprintf("%v", anyStruct) // default format
fmt.Sprintf("%T", anyVar)    // type name
fmt.Sprintf("%q", "hello")  // "hello" (quoted)
fmt.Sprintf("%p", &v)        // pointer address
```

---

## Byte-Level Manipulation — When You Need Speed

For ASCII-only or binary data, work at byte level directly:

```go
func reverseASCIIString(s string) string {
    b := []byte(s)
    for i, j := 0, len(b)-1; i < j; i, j = i+1, j-1 {
        b[i], b[j] = b[j], b[i]
    }
    return string(b)
}

// Reverse Unicode-correct version:
func reverseString(s string) string {
    runes := []rune(s)
    for i, j := 0, len(runes)-1; i < j; i, j = i+1, j-1 {
        runes[i], runes[j] = runes[j], runes[i]
    }
    return string(runes)
}
```

---

## String Comparison and Ordering

```go
// Equality
s1 == s2            // byte-for-byte comparison, O(n)
s1 != s2

// Lexicographic ordering
s1 < s2             // works correctly for UTF-8 (byte order)
strings.Compare(s1, s2) // -1, 0, 1

// Case-insensitive comparison (idiomatic)
strings.EqualFold(s1, s2) // Unicode-aware case folding, NOT just ToLower == ToLower
// EqualFold handles things like: "ß" == "SS" in German
```

---

## `strings.Map` — Functional Transformation

```go
// Apply a function to every rune
rot13 := strings.Map(func(r rune) rune {
    switch {
    case r >= 'A' && r <= 'Z':
        return 'A' + (r-'A'+13)%26
    case r >= 'a' && r <= 'z':
        return 'a' + (r-'a'+13)%26
    }
    return r
}, "Hello, World!")
// "Uryyb, Jbeyq!"

// Remove all digits
clean := strings.Map(func(r rune) rune {
    if unicode.IsDigit(r) {
        return -1 // returning -1 drops the rune
    }
    return r
}, "h3ll0 w0rld")
// "hll wrld"
```

---

## Regular Expressions — `regexp` Package

```go
import "regexp"

// Compile once, reuse many times (compile is expensive)
re := regexp.MustCompile(`\b\w+@\w+\.\w+\b`)

re.MatchString("send to user@example.com please") // true
re.FindString("email: user@example.com here")     // "user@example.com"
re.FindAllString("a@b.com and c@d.org", -1)       // ["a@b.com","c@d.org"]
re.ReplaceAllString(s, "[REDACTED]")
re.Split("a,b,,c", -1)                            // ["a","b","","c"]

// Capture groups
re2 := regexp.MustCompile(`(\w+)@(\w+)\.(\w+)`)
matches := re2.FindStringSubmatch("user@example.com")
// matches[0]="user@example.com", [1]="user", [2]="example", [3]="com"
```

**Performance:** Regex in Go uses RE2 algorithm — O(n) time guaranteed, no backtracking catastrophe. But it's still slower than `strings` package functions for simple cases.

---

## Performance Hierarchy (Fastest → Slowest)

For string operations, here's the mental model you should internalize:

```
[]byte direct operations          ← fastest (no Unicode overhead)
    ↓
strings.Builder accumulation      ← fast (amortized O(1) append)
    ↓
range loop with utf8 package      ← fast (zero alloc Unicode walk)
    ↓
range loop (built-in)             ← slightly slower (same, more readable)
    ↓
[]rune conversion + operation     ← allocates O(n) runes
    ↓
strings package functions         ← convenient, well optimized
    ↓
fmt.Sprintf for conversions       ← uses reflection, avoid in hot paths
    ↓
"+" concatenation in loop         ← O(n²), never do this
    ↓
regexp for simple patterns        ← powerful but expensive to compile
```

---

## Common DSA Patterns in Go Strings

### Frequency Map (rune-safe)
```go
func charFrequency(s string) map[rune]int {
    freq := make(map[rune]int)
    for _, r := range s {
        freq[r]++
    }
    return freq
}
```

### Two-Pointer on String (ASCII)
```go
func isPalindrome(s string) bool {
    b := []byte(strings.ToLower(s))
    i, j := 0, len(b)-1
    for i < j {
        for i < j && !isAlnum(b[i]) { i++ }
        for i < j && !isAlnum(b[j]) { j-- }
        if b[i] != b[j] { return false }
        i++; j--
    }
    return true
}

func isAlnum(b byte) bool {
    return (b >= 'a' && b <= 'z') || (b >= '0' && b <= '9')
}
```

### Sliding Window on String
```go
func longestUniqueSubstring(s string) int {
    seen := make(map[byte]int) // byte is fine for ASCII
    best, left := 0, 0
    for right := 0; right < len(s); right++ {
        if idx, ok := seen[s[right]]; ok && idx >= left {
            left = idx + 1
        }
        seen[s[right]] = right
        if right-left+1 > best {
            best = right - left + 1
        }
    }
    return best
}
```

---

## The Hidden Insight — String Interning

Go does **not** automatically intern strings. But the compiler interns string *literals*. Two identical string literals in code may share the same pointer. Use `==` always for equality, never pointer comparison.

```go
// These might share memory internally:
a := "hello"
b := "hello"
// a == b is true, but you cannot rely on &a[0] == &b[0]
```

---

## Mental Model Summary

Engrave this in memory:

```
String
├── is []byte under the hood (immutable)
├── len() → byte count, NOT character count
├── s[i] → byte, NOT character
├── range s → (byte_index, rune) ← only safe character iteration
│
Rune
├── is int32, represents a Unicode code point
├── 'A' is a rune literal (single quotes)
├── can be 1-4 bytes when encoded as UTF-8
│
For manipulation:
├── ASCII / bytes only → work with []byte directly
├── Characters / Unicode → work with []rune or range + utf8 pkg
├── Building strings → strings.Builder (never + in loop)
├── Searching/Replacing → strings package
├── Numbers ↔ strings → strconv (not fmt.Sprintf)
└── Patterns → regexp (compile once)
```

The design philosophy Go follows here is the same one that makes it excellent for systems work: **no hidden costs, no magic, explicit over implicit**. Once you internalize the byte/rune duality, you become capable of writing string code that is both correct across all human languages and fast enough for production systems — something most developers in other languages simply cannot do.

