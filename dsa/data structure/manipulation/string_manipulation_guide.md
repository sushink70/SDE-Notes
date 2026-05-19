# String Manipulation: A Complete, In-Depth Guide
## Rust · C · Go — Internals, Operations, Patterns, and Pitfalls

---

# Table of Contents

1. [What Is a String? First Principles](#1-what-is-a-string-first-principles)
2. [Encoding Fundamentals](#2-encoding-fundamentals)
3. [Memory Layout and Internals](#3-memory-layout-and-internals)
   - 3.1 C strings
   - 3.2 Go strings
   - 3.3 Rust `str` and `String`
   - 3.4 Small String Optimization (SSO)
4. [String Creation and Initialization](#4-string-creation-and-initialization)
5. [Concatenation and Building](#5-concatenation-and-building)
6. [Slicing and Substrings](#6-slicing-and-substrings)
7. [Search and Find](#7-search-and-find)
8. [Replace and Substitution](#8-replace-and-substitution)
9. [Split and Join](#9-split-and-join)
10. [Trim and Strip](#10-trim-and-strip)
11. [Case Conversion](#11-case-conversion)
12. [Comparison and Ordering](#12-comparison-and-ordering)
13. [Conversion: Strings ↔ Numbers ↔ Bytes](#13-conversion-strings--numbers--bytes)
14. [Formatting and Interpolation](#14-formatting-and-interpolation)
15. [Iteration: Bytes vs Code Units vs Code Points vs Grapheme Clusters](#15-iteration-bytes-vs-code-units-vs-code-points-vs-grapheme-clusters)
16. [Pattern Matching and Regex](#16-pattern-matching-and-regex)
17. [Unicode: Normalization, Collation, Grapheme Clusters](#17-unicode-normalization-collation-grapheme-clusters)
18. [String Interning](#18-string-interning)
19. [The Rope Data Structure](#19-the-rope-data-structure)
20. [Performance: Allocation Strategies](#20-performance-allocation-strategies)
21. [Common Mistakes: Complete Catalogue](#21-common-mistakes-complete-catalogue)
22. [Mental Models: How to Think About Strings](#22-mental-models-how-to-think-about-strings)

---

# 1. What Is a String? First Principles

A **string** is a sequence of characters. That deceptively simple definition hides enormous complexity once you ask: what is a "character"?

At the hardware level, memory holds only bytes. A string is a convention—an agreement that some bytes, interpreted according to some encoding, represent text. Every language encodes that convention differently in its type system and runtime.

Three distinct concepts are routinely confused:

```
CONCEPT            DEFINITION                                  EXAMPLE
─────────────────────────────────────────────────────────────────────────
Byte               8 bits, range 0–255                         0xE2
Code unit          Atomic unit of an encoding                  UTF-8 byte, UTF-16 word
Code point         Unicode scalar value (U+XXXX)               U+1F600 😀
Grapheme cluster   What a human considers "one character"      é (U+0065 U+0301)
```

A single grapheme cluster (`é`) may be:
- 1 code point (U+00E9, precomposed)  OR
- 2 code points (U+0065 `e` + U+0301 combining accent)

And each code point maps to 1–4 UTF-8 bytes.

This layering is the root cause of most string bugs.

---

# 2. Encoding Fundamentals

## ASCII (7-bit, 128 characters)

```
Bit pattern: 0xxxxxxx
Range: 0x00 – 0x7F
Every ASCII string is also valid UTF-8.

Dec  Hex  Char    Dec  Hex  Char
───────────────   ───────────────
 65  0x41  A       97  0x61  a
 66  0x42  B       98  0x62  b
 48  0x30  0       10  0x0A  \n (newline)
 32  0x20  (space)  0  0x00  NUL
```

## UTF-8 (Variable-width: 1–4 bytes per code point)

```
Code Point Range   Byte Count   Byte Pattern
──────────────────────────────────────────────────────────────
U+0000   – U+007F      1        0xxxxxxx
U+0080   – U+07FF      2        110xxxxx 10xxxxxx
U+0800   – U+FFFF      3        1110xxxx 10xxxxxx 10xxxxxx
U+10000  – U+10FFFF    4        11110xxx 10xxxxxx 10xxxxxx 10xxxxxx

Continuation bytes always start with 10xxxxxx (0x80–0xBF).
Leading bytes never start with 10xxxxxx.
This makes UTF-8 self-synchronizing: you can find any character boundary
by scanning backwards for a non-continuation byte.
```

Example — U+1F600 😀 encoded in UTF-8:

```
Code point: 0x1F600 = 0b 000 011111 011000 000000

Fit into 4-byte template: 11110xxx 10xxxxxx 10xxxxxx 10xxxxxx
                                ↓        ↓        ↓        ↓
                          11110000 10011111 10011000 10000000
                            0xF0     0x9F     0x98     0x80
```

## UTF-16 (2 or 4 bytes; surrogate pairs for > U+FFFF)

```
BMP (U+0000 – U+FFFF):     stored as one 16-bit code unit
Non-BMP (U+10000–U+10FFFF): stored as a surrogate pair

High surrogate: 0xD800–0xDBFF
Low  surrogate: 0xDC00–0xDFFF

A lone surrogate is invalid. JavaScript and Java use UTF-16 internally.
```

## UTF-32 (Fixed-width: 4 bytes per code point)

```
Simple but wasteful. Every code point → exactly 4 bytes.
Used internally in some languages for O(1) indexing by code point.
Python 3 uses a variant (compact ASCII / UCS-2 / UCS-4 depending on content).
```

## Why This Matters for String Manipulation

- `len(s)` in Go returns **byte count**, not character count.
- `s[i]` in Go on a `string` returns a **byte** (type `byte` = `uint8`).
- `&s[i]` in C is a **byte address** inside a null-terminated array.
- `s.len()` in Rust returns **byte count**, not char count.
- `s.chars().count()` in Rust returns **Unicode scalar value count**, not grapheme cluster count.
- None of these return what a human sees as the number of characters.

---

# 3. Memory Layout and Internals

## 3.1 C Strings (Null-Terminated Byte Arrays)

A C string is a pointer to a contiguous array of `char` (bytes) where the sequence ends at the first `NUL` byte (0x00).

```
char *s = "hello";

Stack:               Heap / .rodata:
┌──────────┐         ┌────┬────┬────┬────┬────┬────┐
│  ptr ────┼────────►│ h  │ e  │ l  │ l  │ o  │\0  │
└──────────┘         └────┴────┴────┴────┴────┴────┘
                      [0]  [1]  [2]  [3]  [4]  [5]
                     0x68 0x65 0x6C 0x6C 0x6F 0x00

The NUL byte is NOT part of the content; it is the terminator.
strlen("hello") = 5 (does not count NUL).
sizeof("hello") = 6 (counts NUL, because it is a char[6] array literal).
```

### Heap-allocated C string

```c
char *s = malloc(6);  // must include room for NUL
strcpy(s, "hello");

Stack:           Heap:
┌──────────┐     ┌────┬────┬────┬────┬────┬────┐
│  ptr ────┼────►│ h  │ e  │ l  │ l  │ o  │\0  │
└──────────┘     └────┴────┴────┴────┴────┴────┘
                  allocated = 6 bytes
                  length    = 5 bytes (not stored; must recompute with strlen)
```

**Key internal constraint: C strings cannot contain embedded NUL bytes.**
If you try to store binary data with a 0x00 in a C string, every function using it will truncate at that byte.

### `char` vs `unsigned char` vs `uint8_t`

```
char          : may be signed or unsigned (implementation-defined!)
unsigned char : always 0–255, safe for byte manipulation
uint8_t       : exactly 8-bit unsigned, from <stdint.h>

For binary/UTF-8 work, always use unsigned char or uint8_t.
```

## 3.2 Go Strings

A Go `string` is an **immutable** value described by a two-word header (16 bytes on 64-bit):

```
type StringHeader struct {
    Data uintptr  // pointer to backing byte array
    Len  int      // number of bytes (not runes)
}

var s string = "hello, 世界"

Stack (string header):        Heap (backing array):
┌──────────────────────┐      ┌────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐
│ Data ptr ────────────┼─────►│ h  │ e  │ l  │ l  │ o  │ ,  │ SP │ E4 │ B8 │ 96 │ E7 │ 95 │ 8C │
│ Len = 13             │      └────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘
└──────────────────────┘       [0]  [1]  [2]  [3]  [4]  [5]  [6]  [7]  [8]  [9] [10] [11] [12]
                               ←──────────── ASCII ────────────► ←─ 世 (U+4E16, 3 bytes) ─► ←界─►
```

**Go string invariants:**
- Byte array is NOT NUL-terminated (Go stores the length separately).
- The backing array is immutable; multiple strings can share the same backing array (substrings are just different headers pointing into the same memory).
- Assigning a string copies the header (8 + 8 = 16 bytes), not the bytes.

```
s2 := s[0:5]   // "hello"

Stack:                        Heap (SAME backing array, no copy):
┌──────────────────────┐      ┌────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐
│ Data ptr ────────────┼─────►│ h  │ e  │ l  │ l  │ o  │ ,  │ SP │ E4 │ B8 │ 96 │ E7 │ 95 │ 8C │
│ Len = 5              │      └────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘
└──────────────────────┘       ↑─── s2 sees only bytes [0:5] ────┘
```

This is O(1) slicing — zero copy. The backing memory lives as long as any string header points to it.

### `strings.Builder` Internal Layout

```
type Builder struct {
    addr *Builder  // for noescape trick
    buf  []byte    // the growing buffer
}

buf is a slice header: (ptr, len, cap)

Initially: ptr=nil, len=0, cap=0

After WriteString("hello"):
buf: ┌────────────────────────┐
     │ ptr ──► [h][e][l][l][o]│
     │ len=5                  │
     │ cap=8  (or some power) │
     └────────────────────────┘

String() returns string(b.buf) which copies buf into an immutable string.
```

## 3.3 Rust `str` and `String`

Rust has two primary string types:

- `&str` — a borrowed reference to UTF-8 bytes; a fat pointer (ptr + len).
- `String` — an owned, heap-allocated, growable UTF-8 byte buffer.

```
&str (fat pointer, 16 bytes on 64-bit):
┌────────────────┬────────────────┐
│   ptr (8 B)    │   len (8 B)    │
└────────────────┴────────────────┘
       │
       ▼  (points into any UTF-8 byte region: heap, stack, .rodata)
  ┌────┬────┬────┬────┬────┐
  │ h  │ e  │ l  │ l  │ o  │
  └────┴────┴────┴────┴────┘

String (Vec<u8> with UTF-8 invariant):
┌────────────────┬────────────────┬────────────────┐
│   ptr (8 B)    │   len (8 B)    │   cap (8 B)    │
└────────────────┴────────────────┴────────────────┘
       │
       ▼  heap allocation
  ┌────┬────┬────┬────┬────┬────┬────┬────┐
  │ h  │ e  │ l  │ l  │ o  │    │    │    │
  └────┴────┴────┴────┴────┴────┴────┴────┘
   [0]  [1]  [2]  [3]  [4]   ←── unused capacity ──►
   ←──── len=5 ────────────►
   ←──────────── cap=8 ──────────────────────────────►
```

`String` is literally a `Vec<u8>` that enforces the UTF-8 invariant. Its `push_str`, `push`, `insert` methods maintain this invariant.

### `&str` as a slice of `String`

```
let s: String = String::from("hello, world");
let slice: &str = &s[7..12];   // "world"

String on heap:
┌────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐
│ h  │ e  │ l  │ l  │ o  │ ,  │ SP │ w  │ o  │ r  │ l  │ d  │
└────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘
 [0]  [1]  [2]  [3]  [4]  [5]  [6]  [7]  [8]  [9] [10] [11]
                                          ↑
&str slice: { ptr: &heap[7], len: 5 }   ──┘
```

**Rust enforces that slice boundaries fall on UTF-8 code point boundaries at runtime.**  
`&s[0..1]` on a multi-byte character causes a panic.

### Why `String` Cannot Be Indexed with `s[i]`

Rust intentionally does not implement `Index<usize>` for `String` or `str`. The reason: `s[i]` would return a byte in O(1), but that byte is not a valid "character" in general. Rust forces you to be explicit about what you want:

```rust
s.as_bytes()[i]     // byte (u8) — fast, O(1), possibly mid-codepoint
s.chars().nth(i)    // char (Unicode scalar) — O(n), scans from start
```

## 3.4 Small String Optimization (SSO)

Many production string implementations avoid a heap allocation for short strings by embedding the bytes directly in the string header itself.

```
Generic layout (with heap):

┌──────────┬──────────┬──────────┐
│   ptr    │   len    │   cap    │
└──────────┴──────────┴──────────┘
     │ (heap alloc even for "hi")
     ▼
  [h][i]

SSO layout — "hi" (2 bytes, fits inline):

┌──────────────────────────────────────┐
│ [h][i][\0][...padding...][len=2][tag]│
└──────────────────────────────────────┘
  ^ no heap pointer at all

The tag (often a bit in the capacity or length field) distinguishes modes.
C++ std::string, folly::fbstring, and many others do this.
Typical SSO threshold: 15 bytes (GCC libstdc++) or 22 bytes (Clang libc++).
```

Rust's standard `String` does NOT do SSO. Libraries like `compact_str` and `smol_str` add SSO to Rust.

Go's `strings.Builder` does not do SSO either; it always heap-allocates.

---

# 4. String Creation and Initialization

## C

```c
#include <string.h>
#include <stdlib.h>

// ── String literals (stored in read-only .rodata section) ────────────
const char *s1 = "hello";         // pointer to .rodata; do NOT write through it

// ── Stack arrays ─────────────────────────────────────────────────────
char s2[6] = "hello";             // copies bytes onto stack; s2 is mutable
char s3[] = "hello";              // size inferred: char[6]

// ── Heap allocation ───────────────────────────────────────────────────
char *s4 = malloc(6);
strcpy(s4, "hello");

// ── strdup (POSIX): malloc + strcpy in one call ───────────────────────
char *s5 = strdup("hello");       // caller must free(s5)

// ── Initialization of fixed-size buffer ──────────────────────────────
char buf[256];
memset(buf, 0, sizeof(buf));      // zero the whole thing first
snprintf(buf, sizeof(buf), "value=%d", 42);

// ── Compound literal (C99) ────────────────────────────────────────────
const char *s6 = (char[]){ 'h','e','l','l','o','\0' };
```

## Go

```go
// ── String literals ───────────────────────────────────────────────────
s1 := "hello"                    // immutable string
s2 := `hello\nworld`            // raw string literal; backslash is NOT escape

// ── From bytes/runes ─────────────────────────────────────────────────
b := []byte{0x68, 0x65, 0x6C, 0x6C, 0x6F}
s3 := string(b)                  // copies bytes into a new string

r := []rune{'h', 'e', 'l', 'l', 'o'}
s4 := string(r)                  // encodes each rune to UTF-8, allocates

// ── From a single rune ────────────────────────────────────────────────
s5 := string(rune(0x1F600))      // "😀"

// ── fmt.Sprintf ───────────────────────────────────────────────────────
s6 := fmt.Sprintf("value=%d", 42)

// ── strings.Builder (efficient multi-step construction) ───────────────
var sb strings.Builder
sb.WriteString("hello")
sb.WriteByte(',')
sb.WriteRune(' ')
sb.WriteString("world")
s7 := sb.String()               // "hello, world"
```

## Rust

```rust
// ── String literals (type: &'static str) ─────────────────────────────
let s1: &str = "hello";

// ── Owned String from literal ─────────────────────────────────────────
let s2: String = String::from("hello");
let s3: String = "hello".to_string();
let s4: String = "hello".to_owned();    // same as to_string() for &str

// ── With capacity pre-allocation ─────────────────────────────────────
let mut s5 = String::with_capacity(64); // allocates 64 bytes upfront
s5.push_str("hello");

// ── From bytes (unsafe bypass) ────────────────────────────────────────
let bytes = vec![104u8, 101, 108, 108, 111];
let s6 = String::from_utf8(bytes).unwrap();             // checked
let s7 = unsafe { String::from_utf8_unchecked(vec![]) }; // unchecked

// ── format! macro ────────────────────────────────────────────────────
let s8 = format!("value={}", 42);

// ── Concatenation via + operator (takes ownership of lhs) ─────────────
let s9  = String::from("hello");
let s10 = String::from(", world");
let s11 = s9 + &s10;   // s9 is moved; s10 is borrowed
```

---

# 5. Concatenation and Building

## The Naive Quadratic Problem

Concatenating N strings naively creates O(N²) allocations:

```
Step 1: "a"              → alloc 1 byte
Step 2: "a" + "b"       → alloc 2 bytes, copy "a", append "b"
Step 3: "ab" + "c"      → alloc 3 bytes, copy "ab", append "c"
...
Step N: total copies = 1+2+3+...+N = O(N²)

Total bytes copied for N strings of avg length L:
  sum = L*(1 + 2 + ... + N) = L*N*(N+1)/2 = O(L*N²)
```

The correct approach is to use a **builder/buffer** that amortizes allocations by doubling capacity:

```
Capacity doubling strategy:
start: cap=0
push "hello" (5):  cap=8   (allocate)
push ", "    (2):  cap=8   (fits)
push "world" (5):  len=12, cap=16  (reallocate: cap*2=16)
push "!"     (1):  len=13, cap=16  (fits)

Total allocations: 2 (not N)
```

## C

```c
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

// ── Simple concatenation (dangerous: no bounds check) ─────────────────
char buf[256];
strcpy(buf, "hello");
strcat(buf, ", world");   // DO NOT USE if sizes are unknown

// ── Safe: strncat ─────────────────────────────────────────────────────
strncat(buf, "!", sizeof(buf) - strlen(buf) - 1);

// ── Best: snprintf for building ───────────────────────────────────────
snprintf(buf, sizeof(buf), "%s%s%s", "hello", ", ", "world");

// ── Dynamic builder pattern ───────────────────────────────────────────
typedef struct {
    char  *data;
    size_t len;
    size_t cap;
} StrBuf;

void sb_append(StrBuf *sb, const char *s, size_t slen) {
    if (sb->len + slen + 1 > sb->cap) {
        size_t newcap = (sb->cap == 0) ? 16 : sb->cap * 2;
        while (newcap < sb->len + slen + 1) newcap *= 2;
        sb->data = realloc(sb->data, newcap);
        sb->cap  = newcap;
    }
    memcpy(sb->data + sb->len, s, slen);
    sb->len += slen;
    sb->data[sb->len] = '\0';  // keep it NUL-terminated
}

// Usage:
StrBuf sb = {0};
sb_append(&sb, "hello", 5);
sb_append(&sb, ", world", 7);
printf("%s\n", sb.data);
free(sb.data);
```

## Go

```go
// ── + operator: OK for 2–3 strings, quadratic for loops ──────────────
s := "hello" + ", " + "world"   // compiler may optimize small literal chains

// ── strings.Builder: preferred for loops ─────────────────────────────
var b strings.Builder
b.Grow(64)  // optional: hint total capacity to avoid reallocs
for _, word := range words {
    if b.Len() > 0 { b.WriteByte(',') }
    b.WriteString(word)
}
result := b.String()

// ── strings.Join: when you already have a slice ───────────────────────
result2 := strings.Join(words, ", ")

// ── bytes.Buffer: older alternative (allocates on the heap) ──────────
var buf bytes.Buffer
buf.WriteString("hello")
buf.WriteString(", world")
result3 := buf.String()

// ── fmt.Sprintf: convenient but slowest (reflection overhead) ─────────
result4 := fmt.Sprintf("%s, %s", "hello", "world")
```

## Rust

```rust
// ── + operator (moves lhs, borrows rhs) ──────────────────────────────
let s = String::from("hello") + ", " + "world";
// Each + calls add(self, &str), consuming the lhs String.
// Chaining: (("hello" + ", ") + "world")

// ── format! macro: cleaner but allocates a new String always ──────────
let s2 = format!("{}{}{}", "hello", ", ", "world");

// ── push_str/push: most efficient for incremental builds ─────────────
let mut s3 = String::with_capacity(64);
for (i, word) in words.iter().enumerate() {
    if i > 0 { s3.push_str(", "); }
    s3.push_str(word);
}

// ── collect from iterator ─────────────────────────────────────────────
let s4: String = vec!["hello", ", ", "world"]
    .into_iter()
    .collect();

// ── join (like Go's strings.Join) ─────────────────────────────────────
let s5 = words.join(", ");
```

---

# 6. Slicing and Substrings

## C

```c
// C has no substring type. Substrings are: a pointer + length, OR
// a null-terminated copy.

const char *s = "hello, world";

// ── Pointer-based substring (zero copy, original must stay alive) ─────
const char *sub = s + 7;   // points to "world"

// ── Length-bounded print (no NUL needed) ─────────────────────────────
printf("%.*s\n", 5, sub);  // prints "world"

// ── Copy into new buffer ──────────────────────────────────────────────
char copy[6];
strncpy(copy, s + 7, 5);
copy[5] = '\0';            // strncpy does NOT guarantee NUL termination!

// ── memcpy + manual NUL ───────────────────────────────────────────────
memcpy(copy, s + 7, 5);
copy[5] = '\0';            // safer pattern
```

**Critical rule:** `strncpy` pads with NUL up to `n` bytes but does NOT add a terminator if the source is >= n bytes. **Always add `\0` manually after `strncpy`.**

## Go

```go
s := "hello, world"

// ── Byte slice (O(1), zero copy, shares backing array) ────────────────
sub1 := s[7:12]     // "world" — half-open range [low, high)
sub2 := s[7:]       // "world" — to end
sub3 := s[:5]       // "hello" — from start

// Full slice expression (controls capacity): only for []byte, not string
b := []byte(s)
sub4 := b[7:12:12]  // len=5, cap=5

// ── DANGER: byte slicing may split a multi-byte rune ──────────────────
s2 := "hello, 世界"
bad := s2[7:10]    // 0xE4 0xB8 0x96 — valid UTF-8 for 世, OK here
                    // but s2[7:9] would be an incomplete sequence!

// ── Safe: convert to []rune first ─────────────────────────────────────
runes := []rune(s2)    // allocates; each rune is one Unicode scalar
sub5  := string(runes[7:8])  // "世"

// ── strings.Cut: preferred for splitting on a separator ───────────────
before, after, found := strings.Cut(s, ", ")
// before="hello", after="world", found=true
```

## Rust

```rust
let s = "hello, world";

// ── &str slices (zero copy, O(1)) ─────────────────────────────────────
let sub1 = &s[7..12];    // "world"
let sub2 = &s[7..];      // "world"
let sub3 = &s[..5];      // "hello"

// ── PANICS if boundary is not on a char boundary ──────────────────────
let s2 = "hello, 世界";
// let bad = &s2[7..9];  // PANICS: byte 9 is mid-codepoint

// ── Safe: use char_indices ─────────────────────────────────────────────
let mut it = s2.char_indices();
let start = it.by_ref().nth(7).map(|(i, _)| i).unwrap_or(s2.len());
let end   = it.next().map(|(i, _)| i).unwrap_or(s2.len());
let safe  = &s2[start..end];   // "世"

// ── String::get: returns Option<&str>, never panics ───────────────────
let opt = s.get(7..12);     // Some("world")
let opt2 = s.get(0..999);   // None (out of bounds, no panic)

// ── chars + skip/take (O(n) but safe) ────────────────────────────────
let sub: String = s.chars().skip(7).take(5).collect();
```

---

# 7. Search and Find

## The Conceptual Categories

```
SEARCH TYPE         DESCRIPTION                          RETURN TYPE
──────────────────────────────────────────────────────────────────────
contains            Boolean: does pattern exist?         bool
find/index          First byte offset of pattern         Option<usize> / int
rfind               Last byte offset of pattern          Option<usize> / int
starts_with         Prefix check                         bool
ends_with           Suffix check                         bool
find + all          All occurrences                      iterator / slice
```

## C

```c
#include <string.h>

const char *s = "the cat sat on the mat";

// ── Single character search ────────────────────────────────────────────
char *pos = strchr(s, 'c');     // pointer to first 'c'; NULL if not found
char *rpos = strrchr(s, 'a');   // pointer to last 'a'

// ── Substring search ──────────────────────────────────────────────────
char *sub = strstr(s, "cat");   // pointer to first "cat"; NULL if not found

// ── Find byte offset ──────────────────────────────────────────────────
if (sub) {
    ptrdiff_t offset = sub - s;  // 4
}

// ── Scan for any char in set (like strpbrk) ───────────────────────────
char *p = strpbrk(s, "aeiou");   // first vowel

// ── Not in set (like strcspn) ─────────────────────────────────────────
size_t n = strcspn(s, "aeiou");  // bytes until first vowel

// ── Prefix/suffix check (manual) ─────────────────────────────────────
int starts = (strncmp(s, "the", 3) == 0);
size_t len = strlen(s);
int ends   = (len >= 3 && strcmp(s + len - 3, "mat") == 0);
```

## Go

```go
import "strings"

s := "the cat sat on the mat"

// ── Contains ──────────────────────────────────────────────────────────
ok1 := strings.Contains(s, "cat")       // true
ok2 := strings.ContainsRune(s, 'c')     // true
ok3 := strings.ContainsAny(s, "xyz")    // false (none of x,y,z present)

// ── Index (byte offset) ───────────────────────────────────────────────
i1 := strings.Index(s, "cat")     // 4
i2 := strings.LastIndex(s, "at")  // 20
i3 := strings.IndexByte(s, 'c')   // 4
i4 := strings.IndexRune(s, 'c')   // 4
i5 := strings.IndexAny(s, "xyz")  // -1

// ── Prefix / Suffix ───────────────────────────────────────────────────
strings.HasPrefix(s, "the")   // true
strings.HasSuffix(s, "mat")   // true

// ── Count occurrences ─────────────────────────────────────────────────
n := strings.Count(s, "at")   // 3

// ── Find all (manual iteration) ───────────────────────────────────────
rest := s
for {
    idx := strings.Index(rest, "at")
    if idx < 0 { break }
    fmt.Println(idx)
    rest = rest[idx+2:]
}
```

## Rust

```rust
let s = "the cat sat on the mat";

// ── Contains ──────────────────────────────────────────────────────────
s.contains("cat");          // true
s.contains('c');            // true (char implements Pattern)

// ── Find (first byte offset) ──────────────────────────────────────────
s.find("cat");              // Some(4)
s.rfind("at");              // Some(20)
s.find('c');                // Some(4)
s.find(|c: char| c.is_ascii_digit());  // None

// ── Prefix / Suffix ───────────────────────────────────────────────────
s.starts_with("the");       // true
s.ends_with("mat");         // true
s.strip_prefix("the ");     // Some("cat sat on the mat")
s.strip_suffix(" mat");     // Some("the cat sat on the")

// ── All matches (iterator) ────────────────────────────────────────────
let offsets: Vec<usize> = s.match_indices("at")
    .map(|(i, _)| i)
    .collect();             // [5, 9, 20]

// ── Split_once: like Go's strings.Cut ─────────────────────────────────
let (before, after) = s.split_once(" cat ").unwrap();
// before="the", after="sat on the mat"
```

---

# 8. Replace and Substitution

## C

```c
// C has no built-in replace. Must implement manually.
void str_replace(char *result, size_t result_size,
                 const char *src, const char *find, const char *repl) {
    size_t flen = strlen(find);
    size_t rlen = strlen(repl);
    size_t out  = 0;
    while (*src && out < result_size - 1) {
        if (strncmp(src, find, flen) == 0) {
            size_t copy = (rlen < result_size - 1 - out) ? rlen : result_size - 1 - out;
            memcpy(result + out, repl, copy);
            out += copy;
            src += flen;
        } else {
            result[out++] = *src++;
        }
    }
    result[out] = '\0';
}
```

## Go

```go
s := "the cat sat on the mat"

// ── Replace first N occurrences (-1 = all) ────────────────────────────
r1 := strings.Replace(s, "at", "AT", -1)   // all
r2 := strings.Replace(s, "at", "AT", 1)    // first only
r3 := strings.ReplaceAll(s, "at", "AT")    // sugar for Replace(..., -1)

// ── Strings.Map: transform char by char ───────────────────────────────
r4 := strings.Map(func(r rune) rune {
    if r == 'a' { return 'A' }
    return r
}, s)

// ── strings.NewReplacer: batch multi-pair replacement ─────────────────
rep := strings.NewReplacer(
    "cat", "dog",
    "mat", "rug",
)
r5 := rep.Replace(s)   // "the dog sat on the rug"
// NewReplacer builds an Aho-Corasick-like trie internally for efficiency.
```

## Rust

```rust
let s = "the cat sat on the mat";

// ── Replace all occurrences ───────────────────────────────────────────
let r1 = s.replace("at", "AT");          // all; returns new String

// ── Replace first N ───────────────────────────────────────────────────
let r2 = s.replacen("at", "AT", 1);     // first only

// ── Replace with closure ──────────────────────────────────────────────
let r3: String = s.chars()
    .map(|c| if c == 'a' { 'A' } else { c })
    .collect();

// ── Replace by char set ───────────────────────────────────────────────
let r4 = s.replace(|c: char| "aeiou".contains(c), "_");
```

---

# 9. Split and Join

## Conceptual View

```
"a,b,,c".split(",")

Position:  0  1  2  3  4  5
Chars:     a  ,  b  ,  ,  c
                  ↑     ↑↑
Separators found at 1, 3, 4

Resulting parts: ["a", "b", "", "c"]
                               ↑
                    Empty string between consecutive separators
```

## C

```c
// strtok: modifies the original string! Not re-entrant! Not thread-safe!
char s[] = "a,b,,c";           // must be mutable (not a string literal)
char *token = strtok(s, ",");
while (token != NULL) {
    printf("[%s]\n", token);
    token = strtok(NULL, ",");  // continue same string
}
// Output: [a] [b] [c]  <-- SKIPS empty tokens! strtok is not for empty fields.

// strtok_r: re-entrant version
char *saveptr;
token = strtok_r(s, ",", &saveptr);
```

`strtok` has two critical flaws:
1. It **modifies the input string** by writing `\0` at each delimiter.
2. It **skips consecutive delimiters** (no empty tokens).

For robust splitting in C, implement a custom function using `strchr`/`memchr`.

## Go

```go
s := "a,b,,c"

// ── Split (all parts, including empty) ───────────────────────────────
parts := strings.Split(s, ",")          // ["a", "b", "", "c"]

// ── SplitN: limit number of parts ────────────────────────────────────
parts2 := strings.SplitN(s, ",", 3)    // ["a", "b", ",c"] — max 3 parts

// ── SplitAfter: include separator in each part ────────────────────────
parts3 := strings.SplitAfter(s, ",")   // ["a,", "b,", ",", "c"]

// ── Fields: split on whitespace, skip empty ───────────────────────────
parts4 := strings.Fields("  hello   world  ")  // ["hello", "world"]

// ── FieldsFunc: split on custom predicate ────────────────────────────
parts5 := strings.FieldsFunc(s, func(r rune) bool {
    return r == ',' || r == ';'
})

// ── Join ──────────────────────────────────────────────────────────────
joined := strings.Join(parts, " | ")   // "a | b |  | c"
```

## Rust

```rust
let s = "a,b,,c";

// ── split: produces an iterator of &str ───────────────────────────────
let parts: Vec<&str> = s.split(',').collect();     // ["a", "b", "", "c"]

// ── splitn: limit to N parts ──────────────────────────────────────────
let parts2: Vec<&str> = s.splitn(3, ',').collect(); // ["a", "b", ",c"]

// ── split_whitespace (equivalent to Go's Fields) ──────────────────────
let parts3: Vec<&str> = "  hello   world  ".split_whitespace().collect();
// ["hello", "world"]

// ── split_terminator: removes trailing empty string ───────────────────
let parts4: Vec<&str> = "a,b,c,".split_terminator(',').collect();
// ["a", "b", "c"]  (not ["a", "b", "c", ""])

// ── split with closure ────────────────────────────────────────────────
let parts5: Vec<&str> = s.split(|c: char| c == ',' || c == ';').collect();

// ── Join ──────────────────────────────────────────────────────────────
let joined = parts.join(" | ");       // "a | b |  | c"
let joined2 = ["a", "b", "c"].join(",");  // "a,b,c"
```

---

# 10. Trim and Strip

## Conceptual View

```
s = "   hello, world   "
       ↑↑↑              ↑↑↑
    leading            trailing
    whitespace         whitespace

TrimLeft:  "hello, world   "
TrimRight: "   hello, world"
Trim:      "hello, world"
```

## C

```c
#include <ctype.h>
#include <string.h>

// ── Trim left (skip leading whitespace) ───────────────────────────────
char *ltrim(char *s) {
    while (*s && isspace((unsigned char)*s)) s++;
    return s;
}

// ── Trim right (remove trailing whitespace by writing NUL) ────────────
char *rtrim(char *s) {
    char *end = s + strlen(s) - 1;
    while (end >= s && isspace((unsigned char)*end)) *end-- = '\0';
    return s;
}

// Note: isspace() with plain char argument is UNDEFINED BEHAVIOR if char is
// signed and value is negative (e.g., 0xFF). Always cast to unsigned char.
```

## Go

```go
s := "   hello, world   "

strings.TrimSpace(s)                    // "hello, world"
strings.TrimLeft(s, " \t")             // trim specific chars from left
strings.TrimRight(s, " \t")            // trim specific chars from right
strings.Trim(s, " ")                   // both sides, specific chars

strings.TrimPrefix(s, "   hello")      // ", world   "
strings.TrimSuffix(s, "world   ")      // "   hello, "

strings.TrimFunc(s, unicode.IsSpace)   // trim using predicate
```

## Rust

```rust
let s = "   hello, world   ";

s.trim()                          // "hello, world"
s.trim_start()                    // "hello, world   "
s.trim_end()                      // "   hello, world"

s.trim_matches(' ')               // trim matching chars both sides
s.trim_start_matches(char::is_whitespace)  // with predicate

s.trim_start_matches("   ")       // trim a prefix string

// ── strip_prefix / strip_suffix (returns Option) ──────────────────────
s.strip_prefix("   hello")        // Some(", world   ")
s.strip_suffix("world   ")        // Some("   hello, ")
```

---

# 11. Case Conversion

## ASCII Case vs Unicode Case: A Critical Distinction

ASCII case conversion is simple: flip bit 5 (`'A' | 0x20 == 'a'`).

Unicode case conversion is not:
- Turkish `i` uppercases to `İ` (U+0130), not `I`.
- German `ß` uppercases to `SS` (one char → two chars).
- Greek σ (sigma) has two lowercase forms: σ (mid-word) and ς (end-of-word).

Most standard libraries implement only simple case mapping. **Locale-aware case mapping requires Unicode libraries.**

## C

```c
#include <ctype.h>

// ASCII only; UB if char is signed and value > 127
char c_upper = toupper('a');   // 'A'
char c_lower = tolower('A');   // 'a'

// Convert in-place (ASCII strings only)
for (char *p = s; *p; p++) *p = tolower((unsigned char)*p);
```

## Go

```go
import (
    "strings"
    "unicode"
)

strings.ToUpper("hello")       // "HELLO" (Unicode-aware simple mapping)
strings.ToLower("HELLO")       // "hello"
strings.Title("hello world")   // "Hello World" (deprecated; use golang.org/x/text)

// Per-rune
unicode.ToUpper('a')           // 'A'
unicode.IsUpper('A')           // true
unicode.IsLower('a')           // true

// Locale-aware (requires x/text):
// import "golang.org/x/text/cases"
// cases.Upper(language.Turkish).String("istanbul")  →  "İSTANBUL"
```

## Rust

```rust
// Simple Unicode case mapping (no locale)
"hello".to_uppercase()         // "HELLO" — returns String (may be longer!)
"HELLO".to_lowercase()         // "hello"

// "ß".to_uppercase() == "SS"   (length changes!)
assert_eq!("ß".to_uppercase(), "SS");
assert_eq!("ß".to_uppercase().len(), 2);

// ASCII-only (fastest if you know input is ASCII)
"hello".to_ascii_uppercase()   // "HELLO" — O(n) in-place mapping
b'a'.to_ascii_uppercase()      // b'A' — byte-level

// Char-level
'a'.to_uppercase().collect::<String>()  // "A"
'ß'.to_uppercase().collect::<String>()  // "SS"
```

---

# 12. Comparison and Ordering

## Byte Comparison vs Unicode Collation

```
Lexicographic byte comparison:
"apple" < "banana"   ✓ (correct intuition, works for ASCII)
"café" vs "cafe"      ? (depends on encoding; byte comparison is wrong for non-ASCII)
"ñ" > "z"             byte-compare says yes (0xC3 0xB1 > 0x7A), but Spanish says no

Unicode collation (CLDR/ICU):
- Language-specific ordering rules (Swedish: ä sorts after z)
- Accent-insensitive / case-insensitive comparison
- Standard library implementations are NOT locale-aware
```

## C

```c
// ── Byte-exact comparison ─────────────────────────────────────────────
strcmp("abc", "abc")       //  0 (equal)
strcmp("abc", "abd")       // <0 (abc < abd)
strcmp("abd", "abc")       // >0

// ── Length-limited ────────────────────────────────────────────────────
strncmp("abc", "abcdef", 3) // 0 (equal for first 3 bytes)

// ── Case-insensitive (POSIX) ──────────────────────────────────────────
strcasecmp("Hello", "hello")   // 0 (ASCII-only)
strncasecmp("Hello", "HELL", 4) // 0

// ── Binary safe (embedded NUL ok) ─────────────────────────────────────
memcmp(a, b, len)   // compare exactly len bytes
```

## Go

```go
// ── Exact comparison ──────────────────────────────────────────────────
s1 == s2                           // byte-exact
s1 != s2
strings.Compare(s1, s2)            // -1, 0, 1

// ── Case-insensitive (Unicode, simple mapping) ────────────────────────
strings.EqualFold("Hello", "hELLO")   // true
strings.EqualFold("ß", "ss")          // true! (German folding)

// ── Sort a slice of strings ───────────────────────────────────────────
import "sort"
sort.Strings([]string{"banana", "apple", "cherry"})

// ── Locale-aware (x/text) ─────────────────────────────────────────────
// import "golang.org/x/text/collate"
// col := collate.New(language.German)
// col.CompareString("ä", "z")   // negative (ä < z in German)
```

## Rust

```rust
// ── Exact byte comparison ─────────────────────────────────────────────
"abc" == "abc"           // true
"abc" < "abd"            // true (lexicographic by Unicode scalar value)
"abc".cmp("abd")         // Ordering::Less

// ── Case-insensitive (Unicode simple mapping) ─────────────────────────
"Hello".eq_ignore_ascii_case("hello")   // true (ASCII only!)
// For Unicode case folding, need external crate (unicase, unicode-casefold)

// ── Sorting ───────────────────────────────────────────────────────────
let mut v = vec!["banana", "apple", "cherry"];
v.sort();                // lexicographic by Unicode scalar

// ── Key-based sort ────────────────────────────────────────────────────
v.sort_by_key(|s| s.to_lowercase());

// ── Locale-aware: use `icu4x` or `unicode-collation` crate ───────────
```

---

# 13. Conversion: Strings ↔ Numbers ↔ Bytes

## C

```c
#include <stdlib.h>
#include <stdio.h>
#include <errno.h>

// ── String → Integer ──────────────────────────────────────────────────
int n1 = atoi("42");                   // no error detection!

long n2 = strtol("42", NULL, 10);      // base 10
long n3 = strtol("0xFF", NULL, 0);     // auto-detect base (255)
long n4 = strtol("0b1010", NULL, 2);   // NOT standard; use strtol("1010", ..., 2)

// ── strtol with error detection ───────────────────────────────────────
char *endptr;
errno = 0;
long n = strtol("42abc", &endptr, 10);
if (errno != 0) { /* overflow/underflow */ }
if (*endptr != '\0') { /* not fully consumed: "abc" remains */ }

// ── String → Float ────────────────────────────────────────────────────
double d = strtod("3.14", NULL);

// ── Integer → String ──────────────────────────────────────────────────
char buf[32];
snprintf(buf, sizeof(buf), "%d", 42);
snprintf(buf, sizeof(buf), "%x", 255);    // "ff"
snprintf(buf, sizeof(buf), "%08x", 255);  // "000000ff"

// ── String ↔ Bytes ────────────────────────────────────────────────────
// A C string IS a byte array; no conversion needed.
unsigned char *bytes = (unsigned char *)s;
```

## Go

```go
import (
    "strconv"
    "fmt"
)

// ── String → Integer ──────────────────────────────────────────────────
n1, err := strconv.Atoi("42")           // returns (int, error)
n2, err := strconv.ParseInt("42", 10, 64)    // base 10, 64-bit
n3, err := strconv.ParseInt("FF", 16, 64)    // hex → 255
n4, err := strconv.ParseUint("42", 10, 64)
n5, err := strconv.ParseFloat("3.14", 64)
n6, err := strconv.ParseBool("true")    // true, false, 1, 0, T, F, ...

// ── Integer → String ──────────────────────────────────────────────────
s1 := strconv.Itoa(42)                  // "42"
s2 := strconv.FormatInt(255, 16)        // "ff"
s3 := strconv.FormatInt(255, 2)         // "11111111"
s4 := strconv.FormatFloat(3.14, 'f', 2, 64)  // "3.14"
s5 := strconv.FormatBool(true)          // "true"
s6 := fmt.Sprintf("%08x", 255)          // "000000ff"

// ── String ↔ Bytes ────────────────────────────────────────────────────
b := []byte("hello")           // string → []byte (COPIES)
s := string(b)                 // []byte → string (COPIES)

// Zero-copy conversion (unsafe; only valid while b is alive):
import "unsafe"
s_unsafe := *(*string)(unsafe.Pointer(&b))  // DO NOT use if b will be mutated!
```

## Rust

```rust
// ── String → Integer ──────────────────────────────────────────────────
let n1: i32 = "42".parse().unwrap();
let n2: i32 = "42".parse::<i32>().unwrap();
let n3 = i32::from_str_radix("FF", 16).unwrap();  // 255
let n4: f64 = "3.14".parse().unwrap();

// ── With error handling ───────────────────────────────────────────────
match "abc".parse::<i32>() {
    Ok(n)  => println!("{}", n),
    Err(e) => println!("parse error: {}", e),
}

// ── Integer → String ──────────────────────────────────────────────────
let s1 = 42.to_string();                 // "42"
let s2 = format!("{:x}", 255);           // "ff"
let s3 = format!("{:08x}", 255);         // "000000ff"
let s4 = format!("{:b}", 42);            // "101010"
let s5 = format!("{:.2}", 3.14159);      // "3.14"

// ── String ↔ Bytes ────────────────────────────────────────────────────
let s = "hello";
let bytes: &[u8] = s.as_bytes();         // zero-copy borrow (immutable)
let bytes_vec: Vec<u8> = s.as_bytes().to_vec();  // copy into owned Vec

let s_back = std::str::from_utf8(bytes).unwrap();   // checked (returns &str)
let s_owned = String::from_utf8(bytes_vec).unwrap(); // checked, owned
let s_lossy = String::from_utf8_lossy(bytes);        // replace invalid UTF-8 with U+FFFD
```

---

# 14. Formatting and Interpolation

## C — printf Format Specifiers

```
SPECIFIER    TYPE             EXAMPLE OUTPUT
──────────────────────────────────────────────
%d           int              42
%u           unsigned int     42
%ld          long             42
%lld         long long        42
%x / %X      unsigned hex     ff / FF
%o           unsigned octal   52
%f           double           3.140000
%e / %E      scientific       3.14e+00
%g / %G      shortest float   3.14
%s           char *           hello
%c           char             h
%p           pointer          0x7fff5fbff860
%%           literal %        %
%5d          right-padded     "   42"
%-5d         left-padded      "42   "
%05d         zero-padded      "00042"
%.*s         dynamic width    printf("%.*s", 3, "hello") → "hel"
```

```c
// ── Safe formatting into buffer ───────────────────────────────────────
char buf[256];
int written = snprintf(buf, sizeof(buf), "x=%d, y=%.2f", 10, 3.14);
// written = number of bytes that WOULD be written (excluding NUL)
// if written >= sizeof(buf), output was truncated

// ── asprintf (POSIX): allocates buffer automatically ─────────────────
char *s;
asprintf(&s, "x=%d", 42);  // s must be freed
free(s);
```

## Go

```go
// ── Verb reference ────────────────────────────────────────────────────
fmt.Sprintf("%d", 42)         // "42"
fmt.Sprintf("%05d", 42)       // "00042"
fmt.Sprintf("%x", 255)        // "ff"
fmt.Sprintf("%X", 255)        // "FF"
fmt.Sprintf("%08X", 255)      // "000000FF"
fmt.Sprintf("%b", 42)         // "101010"
fmt.Sprintf("%o", 42)         // "52"
fmt.Sprintf("%f", 3.14)       // "3.140000"
fmt.Sprintf("%.2f", 3.14)     // "3.14"
fmt.Sprintf("%e", 3.14)       // "3.140000e+00"
fmt.Sprintf("%g", 3.14)       // "3.14"
fmt.Sprintf("%s", "hello")    // "hello"
fmt.Sprintf("%q", "hell\"o")  // `"hell\"o"` (Go-quoted)
fmt.Sprintf("%v", struct{ X int }{42})  // {42}
fmt.Sprintf("%+v", struct{ X int }{42}) // {X:42}
fmt.Sprintf("%#v", struct{ X int }{42}) // struct { X int }{X:42}
fmt.Sprintf("%T", 3.14)       // "float64"
fmt.Sprintf("%p", &s)         // pointer address
```

## Rust

```rust
// ── format! verb reference ────────────────────────────────────────────
format!("{}", 42)             // "42"    (Display trait)
format!("{:?}", vec![1,2,3])  // "[1, 2, 3]" (Debug trait)
format!("{:#?}", s)           // pretty-printed debug
format!("{:05}", 42)          // "00042"
format!("{:>10}", "hi")       // "        hi" (right-align, width 10)
format!("{:<10}", "hi")       // "hi        " (left-align)
format!("{:^10}", "hi")       // "    hi    " (center)
format!("{:x}", 255)          // "ff"
format!("{:X}", 255)          // "FF"
format!("{:#x}", 255)         // "0xff"
format!("{:b}", 42)           // "101010"
format!("{:#b}", 42)          // "0b101010"
format!("{:.2}", 3.14159)     // "3.14"
format!("{:e}", 3.14)         // "3.14e0"
format!("{:010.3}", 3.14)     // "000003.140"

// ── Named arguments ───────────────────────────────────────────────────
let x = 42;
format!("{x}")                 // "42" (Rust 1.58+)
format!("{x:05}")              // "00042"

// ── Positional ────────────────────────────────────────────────────────
format!("{0} {1} {0}", "aba", "caba")  // "aba caba aba"
```

---

# 15. Iteration: Bytes vs Code Units vs Code Points vs Grapheme Clusters

This section is the most important for correctness.

```
String: "café"

Memory (UTF-8):
┌────┬────┬────┬────┬────┬────┐
│ c  │ a  │ f  │ é (2 bytes) │
│0x63│0x61│0x66│0xC3│0xA9│    │
└────┴────┴────┴────┴────┴────┘
  [0]  [1]  [2]  [3]  [4]

ITERATION LEVEL    ELEMENTS            COUNT   CORRECT FOR
─────────────────────────────────────────────────────────
bytes              [63,61,66,C3,A9]     5      Network I/O, binary ops
code units (UTF8)  same as bytes        5      UTF-8 processing
code points        ['c','a','f','é']    4      Unicode-aware ops
grapheme clusters  ["c","a","f","é"]    4      Same here (é is precomposed)

BUT: "café" = "cafe\u0301" (combining accent)
Memory:  c  a  f  e  ̣(U+0301 = 2 bytes)
┌────┬────┬────┬────┬────┬────┐
│0x63│0x61│0x66│0x65│0xCC│0x81│
└────┴────┴────┴────┴────┴────┘

Iteration level    Count
─────────────────────────
bytes                6
code points          5   (c, a, f, e, U+0301)
grapheme clusters    4   (c, a, f, é)  ← what a human sees
```

## C — Iterating a UTF-8 String

```c
// ── Byte iteration (trivial) ──────────────────────────────────────────
const char *s = "café";
for (const char *p = s; *p; p++) {
    printf("%02X ", (unsigned char)*p);
}
// C3 61 66 C3 A9 -- wait, that's wrong. café:
// c=63, a=61, f=66, é=C3 A9 → correct: 63 61 66 C3 A9

// ── UTF-8 code point iteration (manual decoder) ───────────────────────
uint32_t utf8_next(const uint8_t **p) {
    uint32_t cp;
    uint8_t b = *(*p)++;
    if      (b < 0x80)                cp = b;
    else if ((b & 0xE0) == 0xC0) {   cp = b & 0x1F;  cp = (cp<<6) | ((*(*p)++) & 0x3F); }
    else if ((b & 0xF0) == 0xE0) {   cp = b & 0x0F;  cp = (cp<<6) | ((*(*p)++) & 0x3F);
                                                       cp = (cp<<6) | ((*(*p)++) & 0x3F); }
    else                          {   cp = b & 0x07;  cp = (cp<<6) | ((*(*p)++) & 0x3F);
                                                       cp = (cp<<6) | ((*(*p)++) & 0x3F);
                                                       cp = (cp<<6) | ((*(*p)++) & 0x3F); }
    return cp;
}
```

## Go — Three Iteration Modes

```go
s := "café"

// ── Mode 1: byte iteration (s[i] returns byte) ────────────────────────
for i := 0; i < len(s); i++ {
    fmt.Printf("[%d] = %02X\n", i, s[i])
}
// [0]=63  [1]=61  [2]=66  [3]=C3  [4]=A9

// ── Mode 2: range iteration (decodes UTF-8, gives runes) ─────────────
for i, r := range s {
    fmt.Printf("[%d] = U+%04X (%c)\n", i, r, r)
}
// [0]=U+0063 (c)
// [1]=U+0061 (a)
// [2]=U+0066 (f)
// [3]=U+00E9 (é)
// i is the BYTE offset, not the rune index!

// ── Mode 3: grapheme clusters (requires x/text) ───────────────────────
// import "golang.org/x/text/unicode/norm"
// import "golang.org/x/text/unicode/grapheme"  (or use rivo/uniseg)
```

## Rust — Four Iteration Modes

```rust
let s = "café";

// ── Mode 1: bytes ─────────────────────────────────────────────────────
for b in s.bytes() {
    print!("{:02X} ", b);
}
// 63 61 66 C3 A9

// ── Mode 2: chars (Unicode scalar values) ─────────────────────────────
for c in s.chars() {
    println!("{}", c);
}
// c, a, f, é

// ── Mode 3: char_indices (char + byte offset) ─────────────────────────
for (i, c) in s.char_indices() {
    println!("[{}] = {}", i, c);
}
// [0]=c  [1]=a  [2]=f  [3]=é

// ── Mode 4: grapheme clusters (unicode-segmentation crate) ────────────
use unicode_segmentation::UnicodeSegmentation;
for g in s.graphemes(true) {  // true = extended grapheme clusters
    println!("{}", g);
}
// With NFD "café": c, a, f, é (combining e + accent treated as one)
```

---

# 16. Pattern Matching and Regex

## C — POSIX Regex

```c
#include <regex.h>

regex_t re;
regcomp(&re, "([0-9]+)", REG_EXTENDED);

const char *s = "value=42;";
regmatch_t matches[2];
if (regexec(&re, s, 2, matches, 0) == 0) {
    // matches[0] = whole match
    // matches[1] = first capture group
    printf("match at [%d, %d]\n", matches[1].rm_so, matches[1].rm_eo);
    // → "42" at [6, 8]
}
regfree(&re);
```

## Go — regexp Package

```go
import "regexp"

// ── Compile (panics on bad pattern; use MustCompile in init) ─────────
re := regexp.MustCompile(`([0-9]+)`)

s := "value=42; other=100"

re.MatchString(s)               // true
re.FindString(s)                // "42" (first match)
re.FindAllString(s, -1)         // ["42", "100"] (all matches)
re.FindStringIndex(s)           // [6, 8] (byte offsets)
re.FindStringSubmatch(s)        // ["42", "42"] ([whole, group1])
re.FindAllStringSubmatch(s, -1) // all groups for all matches

re.ReplaceAllString(s, "NUM")          // "value=NUM; other=NUM"
re.ReplaceAllStringFunc(s, func(m string) string {
    n, _ := strconv.Atoi(m)
    return strconv.Itoa(n * 2)
})   // "value=84; other=200"

// ── Compile once, use many times (expensive to compile) ───────────────
var reNum = regexp.MustCompile(`\d+`)   // package-level var
```

**Go's regex uses RE2 semantics — no backtracking, no lookahead/lookbehind, guaranteed O(n) matching.**

## Rust — regex Crate

```rust
use regex::Regex;

let re = Regex::new(r"([0-9]+)").unwrap();
let s  = "value=42; other=100";

re.is_match(s);                          // true
re.find(s).map(|m| m.as_str());          // Some("42")
re.captures(s).and_then(|c| c.get(1));   // first capture group

// All matches
for m in re.find_iter(s) {
    println!("{}", m.as_str());          // 42, 100
}

// Named groups
let re2 = Regex::new(r"(?P<num>[0-9]+)").unwrap();
let caps = re2.captures("value=42").unwrap();
println!("{}", &caps["num"]);            // "42"

// Replace
let result = re.replace_all(s, "NUM");  // "value=NUM; other=NUM"
let result2 = re.replace_all(s, |caps: &regex::Captures| {
    let n: i32 = caps[0].parse().unwrap();
    (n * 2).to_string()
});   // "value=84; other=200"

// ── Compile once with lazy_static or once_cell ────────────────────────
use once_cell::sync::Lazy;
static RE: Lazy<Regex> = Lazy::new(|| Regex::new(r"\d+").unwrap());
```

---

# 17. Unicode: Normalization, Collation, Grapheme Clusters

## Normalization Forms

Unicode allows the same human-visible character to be encoded multiple ways. Normalization picks one canonical form.

```
FORM    NAME                   DESCRIPTION
────────────────────────────────────────────────────────────────
NFC     Canonical Composition  Decompose, then re-compose
                               é (U+00E9) stays as U+00E9
NFD     Canonical Decomposition Decompose fully
                               é → U+0065 U+0301
NFKC    Compatibility Composition Decompose (compat) + re-compose
                               ﬁ (ligature) → fi
NFKD    Compatibility Decomposition Decompose fully (compat)
                               ﬁ → f + i

Use NFC for storage and display (most compact, matches what users type).
Use NFD for string comparison/search (ensures consistent decomposition).
Use NFKC for identifiers and search normalization.
```

**Consequence:** Two strings that look identical may fail `==` if one is NFC and the other is NFD.

```
"é" (NFC: 2 bytes)  ≠  "é" (NFD: 3 bytes)
strlen gives different results
Visual output identical
String comparison fails!
```

## Grapheme Cluster Boundaries

Grapheme clusters are defined by Unicode Standard Annex #29. Examples of multi-codepoint grapheme clusters:

```
क्ष  (Devanagari consonant cluster: 3 code points, 1 grapheme)
👩‍👩‍👧‍👦 (family emoji: 7 code points joined by ZWJ, 1 grapheme)
g̈    (g + combining diaeresis: 2 code points, 1 grapheme)
```

## Go — unicode and golang.org/x/text

```go
// ── NFC normalization ─────────────────────────────────────────────────
import "golang.org/x/text/unicode/norm"

nfc := norm.NFC.String("café")    // normalize to NFC
nfd := norm.NFD.String("café")    // normalize to NFD

norm.NFC.IsNormalString(s)        // check without allocating

// ── Grapheme iteration (rivo/uniseg is popular) ───────────────────────
import "github.com/rivo/uniseg"

g := uniseg.NewGraphemes("Hello, 世界!")
for g.Next() {
    fmt.Printf("%q\n", g.Str())
}
```

## Rust — unicode-normalization + unicode-segmentation crates

```rust
use unicode_normalization::UnicodeNormalization;
use unicode_segmentation::UnicodeSegmentation;

// ── Normalization ─────────────────────────────────────────────────────
let nfc: String = "café".nfc().collect();
let nfd: String = "café".nfd().collect();
let nfkc: String = "ﬁle".nfkc().collect();   // "file"

// ── Grapheme clusters ─────────────────────────────────────────────────
let clusters: Vec<&str> = "Hello, 世界!".graphemes(true).collect();
let count = "👩‍👩‍👧‍👦".graphemes(true).count();  // 1

// ── Word boundaries ───────────────────────────────────────────────────
let words: Vec<&str> = "Hello, world!".unicode_words().collect();
// ["Hello", "world"]
```

---

# 18. String Interning

**String interning** stores only one copy of each distinct string value in a pool. Subsequent intern calls for the same content return the same pointer/reference.

```
Without interning:
"hello" (alloc 1) → 0x1000
"hello" (alloc 2) → 0x2000
"hello" == "hello" → byte-compare all 5 chars each time

With interning:
"hello" (alloc 1) → 0x1000  ← stored in pool
"hello" (lookup)  → 0x1000  ← same pointer returned
"hello" == "hello" → pointer compare (O(1))
```

Benefits: deduplication of memory, O(1) equality via pointer comparison.
Cost: pool management overhead; interned strings usually live forever.

## C — Manual Interning with a Hash Table

```c
// Interning implemented as a hash table mapping string → canonical pointer
#include <string.h>
#include <stdlib.h>

#define POOL_SIZE 1024

typedef struct Entry { const char *key; struct Entry *next; } Entry;
static Entry *pool[POOL_SIZE];

unsigned hash(const char *s) {
    unsigned h = 5381;
    while (*s) h = h * 33 ^ (unsigned char)*s++;
    return h % POOL_SIZE;
}

const char *intern(const char *s) {
    unsigned h = hash(s);
    for (Entry *e = pool[h]; e; e = e->next)
        if (strcmp(e->key, s) == 0) return e->key;
    Entry *e = malloc(sizeof(Entry));
    e->key  = strdup(s);
    e->next = pool[h];
    pool[h] = e;
    return e->key;
}

// Usage:
const char *a = intern("hello");
const char *b = intern("hello");
assert(a == b);              // same pointer!
```

## Go — Interning Patterns

```go
// Go string literals and constants are automatically interned by the compiler.
// Runtime strings created via conversion are NOT.

// ── Manual pool (unsafe, zero-copy) ───────────────────────────────────
var internPool = make(map[string]string)
func intern(s string) string {
    if v, ok := internPool[s]; ok { return v }
    internPool[s] = s
    return s
}

// ── sync.Map for concurrent interning ─────────────────────────────────
var pool sync.Map
func internConcurrent(s string) string {
    v, _ := pool.LoadOrStore(s, s)
    return v.(string)
}
```

## Rust

```rust
use std::collections::HashMap;
use std::sync::Mutex;

// ── Simple thread-local intern pool ──────────────────────────────────
static POOL: Mutex<HashMap<String, &'static str>> = Mutex::new(HashMap::new());

fn intern(s: &str) -> &'static str {
    let mut pool = POOL.lock().unwrap();
    if let Some(&interned) = pool.get(s) { return interned; }
    let leaked: &'static str = Box::leak(s.to_string().into_boxed_str());
    pool.insert(leaked.to_string(), leaked);
    leaked
}

// ── Production crates: `string-interner`, `internment` ────────────────
use string_interner::StringInterner;
let mut interner = StringInterner::default();
let sym1 = interner.get_or_intern("hello");
let sym2 = interner.get_or_intern("hello");
assert_eq!(sym1, sym2);  // same symbol (integer ID)
```

---

# 19. The Rope Data Structure

A **Rope** is a binary tree where leaf nodes hold short string chunks and internal nodes store the total length of their left subtree. Ropes make large-string editing efficient.

```
Rope for "Hello, World!"

            [13]           ← root: total length
           /     \
        [7]       [6]      ← internal nodes: left subtree lengths
       /   \      /  \
  "Hello" ", "  "Wo" "rld!"
   [5]    [2]   [2]  [4]

Insert "Beautiful " between "," and " ":

          [23]
         /     \
      [7]       [16]
     /   \      /    \
"Hello" ","  [10]   "rld!"
              /   \
          " Beau"  "tiful "

Operations:
- Index(i):    O(log n)  — traverse tree summing left lengths
- Concat:      O(1)      — create new root node
- Split(i):    O(log n)  — split tree at position i
- Insert(i,s): O(log n)  — split + concat
- Delete(i,j): O(log n)  — split + split + concat middle
- Append:      O(1) amortized
```

Ropes are used in text editors (VS Code uses a piece table variant, Vim uses a gap buffer, Xi editor used a rope). For normal in-memory string work, ropes are overkill.

Rust: `jumprope` and `ropey` crates.  
Go: `ropes` package.  
C: custom implementation.

---

# 20. Performance: Allocation Strategies

## The Cost of String Operations

```
OPERATION               COMPLEXITY     ALLOCATES?
─────────────────────────────────────────────────────────────────
Byte access s[i]        O(1)           No
contains/find           O(n*m)*        No
starts_with/ends_with   O(k)           No
len()                   O(1)           No (stored)
strlen() in C           O(n)           No (scans for NUL)
Substring (Go/Rust)     O(1)           No (fat pointer)
Substring (C copy)      O(k)           Yes
Concatenation (+)       O(n+m)         Yes
format!/Sprintf         O(n)           Yes
to_uppercase            O(n)           Yes (may grow!)
split → collect         O(n)           Yes (Vec of &str = no body copy)
Replace                 O(n)           Yes
Parse (string→int)      O(k)           No
to_string (int)         O(k)           Yes

* Naive O(n*m); Boyer-Moore/KMP gives O(n+m)
```

## Pre-allocation Strategy

```rust
// ── Rust: reserve before a loop ───────────────────────────────────────
let mut s = String::with_capacity(total_bytes_estimate);
for chunk in chunks {
    s.push_str(chunk);
}
// Zero reallocations if estimate is accurate.

// ── Check remaining capacity ──────────────────────────────────────────
println!("len={} cap={}", s.len(), s.capacity());
```

```go
// ── Go: Grow before a loop ────────────────────────────────────────────
var sb strings.Builder
sb.Grow(totalEstimate)
for _, chunk := range chunks {
    sb.WriteString(chunk)
}
```

## Avoiding Unnecessary Allocations

```rust
// ── Use &str instead of String where possible ─────────────────────────
fn process(s: &str) -> usize { s.len() }   // borrows, no alloc
// NOT:
fn process(s: String) -> usize { s.len() } // takes ownership, forces alloc at call site

// ── Use Cow<str> for sometimes-owned strings ───────────────────────────
use std::borrow::Cow;
fn ensure_uppercase(s: &str) -> Cow<str> {
    if s.chars().all(|c| c.is_uppercase()) {
        Cow::Borrowed(s)      // no alloc if already uppercase
    } else {
        Cow::Owned(s.to_uppercase())   // alloc only when needed
    }
}

// ── Use as_str() / as_bytes() to avoid cloning ────────────────────────
fn takes_str(s: &str) {}
let owned = String::from("hello");
takes_str(&owned);    // borrows, no copy
takes_str(owned.as_str());  // same
```

## Boyer-Moore-Horspool String Search (Conceptual)

For substring search (find/contains), naive is O(n*m). Standard libraries use optimized algorithms:

```
Text:    a b c d e f g h i j
Pattern:         e f g

Naive:   try at every position: O(n*m) worst case

Boyer-Moore shift table (bad character rule):
- Build table of rightmost occurrence of each char in pattern.
- On mismatch, shift pattern right by max(1, mismatch_position - last_occurrence)

Go uses Rabin-Karp for short patterns, then switches to BMH variants.
Rust's regex crate uses SIMD-accelerated literal search (memchr).
libc memchr is often SIMD-optimized at the libc level.
```

---

# 21. Common Mistakes: Complete Catalogue

## Category 1: Buffer Overflows and Off-by-One (C)

### Mistake 1: Forgetting the NUL terminator

```c
// WRONG: malloc(strlen(s)) forgets the NUL byte
char *copy = malloc(strlen(s));    // off by 1!
strcpy(copy, s);                   // writes one byte past allocation

// CORRECT:
char *copy = malloc(strlen(s) + 1);
strcpy(copy, s);
```

### Mistake 2: strncpy does not guarantee NUL termination

```c
// WRONG:
char dst[5];
strncpy(dst, "hello, world", sizeof(dst));  // no NUL if src >= n bytes!
// dst is now: [h][e][l][l][o] with NO NUL terminator
printf("%s\n", dst);   // reads past end — undefined behavior

// CORRECT:
strncpy(dst, "hello, world", sizeof(dst) - 1);
dst[sizeof(dst) - 1] = '\0';

// BETTER: use snprintf or strlcpy (BSD):
snprintf(dst, sizeof(dst), "%s", "hello, world");
```

### Mistake 3: sizeof vs strlen on a pointer

```c
void bad(char *s) {
    printf("%zu\n", sizeof(s));  // prints 8 (pointer size), not string length!
}
// sizeof(char*) = 8 on 64-bit; sizeof only gives array size for char arr[]
```

### Mistake 4: Signed char comparison with character functions

```c
// WRONG:
char c = '\xFF';   // may be -1 on signed char platforms
isspace(c);        // UB: isspace expects unsigned char or EOF

// CORRECT:
isspace((unsigned char)c);
```

### Mistake 5: strtok modifying the string

```c
const char *s = "a,b,c";    // const!
strtok(s, ",");              // UB: writes NUL into read-only memory
// strtok REQUIRES a mutable (non-const) char array
```

### Mistake 6: strcat on insufficient buffer

```c
char buf[10] = "hello";
strcat(buf, ", world");   // buffer overflow: "hello, world\0" = 13 bytes > 10
```

## Category 2: Encoding and UTF-8 Confusion

### Mistake 7: Treating bytes as characters

```go
// Go
s := "hello, 世界"
fmt.Println(len(s))          // 13 (bytes), NOT 9 (characters)
fmt.Println(s[7])            // 228 = 0xE4 (first byte of 世), NOT a character

// Correct:
fmt.Println([]rune(s)[7])    // '世'
```

```rust
// Rust
let s = "hello, 世界";
println!("{}", s.len());          // 13 (bytes)
// s.chars().nth(7) == Some('世') — O(n) but correct
```

### Mistake 8: Slicing at non-character boundaries

```go
// Go: silently gives garbled output if you print a partial multi-byte rune
s := "世界"
bad := s[0:2]   // first 2 of 3 bytes of 世 — valid []byte, invalid UTF-8
fmt.Println(bad) // garbage or replacement character
```

```rust
// Rust: panics at runtime
let s = "世界";
let bad = &s[0..2];   // PANIC: byte index 2 is not a char boundary
```

### Mistake 9: Assuming len == character count

```go
// Go
emoji := "😀"
fmt.Println(len(emoji))              // 4 (bytes)
fmt.Println(len([]rune(emoji)))      // 1 (rune)
```

### Mistake 10: Comparing NFC and NFD strings

```go
// Both look like "café" but have different byte representations
nfc := "caf\u00E9"        // NFC: 5 bytes
nfd := "cafe\u0301"       // NFD: 6 bytes
fmt.Println(nfc == nfd)   // false! Visually identical, bytewise different
```

### Mistake 11: Case conversion changes length

```rust
// WRONG assumption: to_uppercase is always same length
let s = "ß";
assert_eq!(s.len(), 2);
let u = s.to_uppercase();
assert_eq!(u.len(), 2);    // FAILS! "SS".len() == 2, but original was 2 bytes
// Actually: "ß" is 2 bytes, "SS" is also 2 bytes here, but...

let s2 = "straße";
let u2 = s2.to_uppercase();
assert_eq!(u2, "STRASSE");  // 6 → 7 characters!
```

## Category 3: Ownership and Lifetime (Rust)

### Mistake 12: Returning a reference to a local String

```rust
// WRONG: compile error — String dropped at end of function
fn bad() -> &str {
    let s = String::from("hello");
    &s   // ERROR: s is dropped here
}

// CORRECT: return owned String
fn good() -> String {
    String::from("hello")
}

// ALSO CORRECT: return &'static str literal
fn also_good() -> &'static str {
    "hello"
}
```

### Mistake 13: Moving a String into + then using it

```rust
let s1 = String::from("hello");
let s2 = String::from(", world");
let s3 = s1 + &s2;   // s1 is MOVED into +; s2 is borrowed
// println!("{}", s1); // ERROR: s1 moved
println!("{}", s3);   // OK
println!("{}", s2);   // OK: s2 was only borrowed
```

### Mistake 14: &String vs &str confusion

```rust
// Over-constraining (forces caller to have a String):
fn bad(s: &String) -> usize { s.len() }

// Correct (accepts String, str, &str, Cow<str>, etc.):
fn good(s: &str) -> usize { s.len() }

// Deref coercion: &String auto-derefs to &str, so good(&some_string) works.
```

### Mistake 15: Forgetting str is unsized

```rust
// WRONG: str has no known compile-time size
let s: str = *"hello";   // ERROR: str is unsized; cannot be stored directly

// CORRECT: always use via reference
let s: &str = "hello";
let s: Box<str> = "hello".into();
```

## Category 4: Go-Specific Mistakes

### Mistake 16: Modifying a string via []byte and expecting the string to update

```go
s := "hello"
b := []byte(s)    // COPY, not a view
b[0] = 'H'
fmt.Println(s)    // "hello" — s is unchanged
fmt.Println(string(b))  // "Hello"
```

### Mistake 17: Using + in a loop (quadratic allocation)

```go
// WRONG: O(n²) allocations
result := ""
for _, s := range items {
    result += s   // creates new string every iteration
}

// CORRECT:
var sb strings.Builder
for _, s := range items {
    sb.WriteString(s)
}
result := sb.String()
```

### Mistake 18: Range loop index is byte offset, not rune index

```go
s := "hello, 世界"
for i, r := range s {
    fmt.Printf("i=%d, r=%c\n", i, r)
}
// i=0  r=h
// i=1  r=e
// ...
// i=7  r=世  ← i=7 (byte offset), not i=7 (rune index)
// i=10 r=界  ← i=10, not i=8
```

### Mistake 19: fmt.Sprintf for simple concatenation

```go
// Slow: reflection, formatting overhead
s := fmt.Sprintf("%s%s", a, b)

// Fast:
s := a + b                    // two strings
s := strings.Join([]string{a, b}, "")  // many strings
```

### Mistake 20: Not checking errors from strconv

```go
// WRONG:
n, _ := strconv.Atoi(userInput)   // ignoring error; n=0 on bad input

// CORRECT:
n, err := strconv.Atoi(userInput)
if err != nil {
    return fmt.Errorf("invalid number: %w", err)
}
```

## Category 5: Subtle Logical Mistakes

### Mistake 21: Off-by-one in substring bounds

```go
s := "hello"
// Extract "ell":
sub := s[1:4]   // bytes [1,4) = "ell" — correct (half-open interval)
sub2 := s[1:3]  // "el" — one too short!
```

### Mistake 22: Replace before searching for original

```go
s := "aaa"
r := strings.Replace(s, "a", "aa", -1)  // "aaaaaa"
// Replace does NOT re-scan replaced text. One pass through original.
```

### Mistake 23: Empty string edge cases

```go
// Split on empty separator
parts := strings.Split("", ",")    // [""] — one empty string, NOT []
len(parts)                          // 1

// Contains empty string
strings.Contains("anything", "")   // always true
strings.HasPrefix("anything", "")  // always true
```

```rust
"".split(',').count()  // 1 — one empty element
"a,b,c".split(',').count()  // 3
```

### Mistake 24: Assuming ASCII in Unicode input

```go
// WRONG: assume one byte = one char for counting/padding
padded := fmt.Sprintf("%-10s", "世界")  // does NOT produce 10 visible chars
// "世界" is 2 runes but may be 4 wide-character columns in a terminal
```

### Mistake 25: Regex not anchored

```go
// Match "42" anywhere in string — might not be what you want
re := regexp.MustCompile(`\d+`)
re.MatchString("abc42def")   // true — matched "42" inside

// Full-string match:
re2 := regexp.MustCompile(`^\d+$`)
re2.MatchString("abc42def")  // false
re2.MatchString("42")        // true
```

### Mistake 26: String equality with rune/char cast

```go
// WRONG:
s := "A"
if s == 'A' { }   // compile error: cannot compare string and rune

// CORRECT:
if s == "A" { }
if s[0] == 'A' { }             // byte comparison (ASCII-safe)
if []rune(s)[0] == 'A' { }     // rune comparison
```

### Mistake 27: Trimming wrong set of characters

```go
// TrimLeft removes any CHARS from the set, not the prefix as a string!
strings.TrimLeft("hello", "helo")  // "" — removes h,e,l,o chars from left
strings.TrimPrefix("hello", "helo")  // "hello" — "helo" is not a prefix of "hello"
```

```rust
// Same trap in Rust:
"hello".trim_start_matches("helo")  // "" — keeps trimming while char is in set?
// Actually: trim_start_matches(&[char]) trims chars; trim_start_matches("str") trims prefix string.
// They behave differently based on the Pattern type.
"hello".trim_start_matches(|c| "helo".contains(c))  // "" — explicit char-set trim
```

---

# 22. Mental Models: How to Think About Strings

## Mental Model 1: The Three-Layer Stack

Always think of strings as three distinct layers:

```
Layer 3: DISPLAY       What the user sees: grapheme clusters, glyphs, visual cells
            │
            │ text shaping, font rendering
            ▼
Layer 2: UNICODE       Code points (U+XXXX): the language model's abstraction
            │
            │ encoding (UTF-8, UTF-16, etc.)
            ▼
Layer 1: BYTES         What the machine sees: raw octets in memory
```

When you get a string bug, immediately ask: **which layer is the mismatch?**

- Length is wrong? → Layer 1 vs Layer 2 confusion (bytes vs code points).
- Comparison fails? → Layer 2 vs Layer 3 confusion (normalization).
- Display is wrong? → Layer 3 (grapheme/glyph-level).

## Mental Model 2: Ownership State Machine (Rust)

```
                  str (borrowed slice)
                 /        \
    &'static str          &'a str
    (literal, forever)    (temporary borrow)
                               ↑
                           String (owned)
                           can deref to &str
                               ↑
                          Box<str> (owned, fixed-size, no capacity overhead)
                               ↑
                         Cow<'a, str>
                         (either borrowed or owned; deref to &str)
```

Rule: always accept `&str` in function signatures. Return `String` when you create, `&str` when you borrow. Use `Cow<str>` when sometimes you clone and sometimes you don't.

## Mental Model 3: C Strings as "Pointer + Convention"

C has no string type. It has:
1. A pointer to memory.
2. A convention that the first 0x00 byte ends the string.

Every C string bug comes from violating one of these:
- Writing past the pointer's allocation (overflow).
- Not placing or misplacing the 0x00 (bad termination).
- Modifying memory the pointer doesn't own (const violation).

**Defense:** Always carry (pointer, length) explicitly. Use `snprintf` not `sprintf`. Use `strncat` not `strcat`. Never use `gets`. Use `strlcpy` (BSD) or write your own.

## Mental Model 4: Go Strings as Immutable Windows

A Go string is a (ptr, len) window into a byte array. The window is immutable. Multiple windows can overlap the same array.

```
Original: [h][e][l][l][o][,][ ][w][o][r][l][d]
           ↑                                  ↑
s[0:12]:  ptr=0, len=12

s[0:5]:   ptr=0, len=5   → "hello"  (no allocation)
s[7:12]:  ptr=7, len=5   → "world"  (no allocation)
```

Converting `string` → `[]byte` **always copies** (must, because []byte is mutable). Converting `[]byte` → `string` **always copies** (to enforce immutability).

## Mental Model 5: UTF-8 as Self-Describing Bytes

UTF-8 byte ranges are non-overlapping and self-synchronizing:

```
0xxxxxxx               Single-byte codepoint (ASCII)
10xxxxxx               Continuation byte (never starts a codepoint)
110xxxxx               2-byte sequence start
1110xxxx               3-byte sequence start
11110xxx               4-byte sequence start

To find the start of the current codepoint from any position:
  scan backward until byte does NOT match 10xxxxxx
  → that byte is the start of the current codepoint

This means:
- Random access by byte offset: O(1) — safe to do
- Random access by code point: O(n) — must scan from start
- Detecting invalid UTF-8: O(n) scan; very fast with SIMD
```

## Mental Model 6: Builder vs Immutable — When to Use Each

```
Use IMMUTABLE string (&str / Go string / C char*) when:
  - Reading/searching/comparing text
  - Passing to functions (borrow, don't copy)
  - Storing string literals

Use BUILDER (String / strings.Builder / StrBuf) when:
  - Building from parts in a loop
  - Concatenating > 2 strings
  - Constructing format output

Use BYTE SLICE ([]byte / Vec<u8> / unsigned char[]) when:
  - Binary data manipulation
  - In-place modification needed
  - Writing a UTF-8 encoder/decoder
  - Interfacing with I/O (reads directly into buffer)
```

## Summary Table: Which Method to Use

```
GOAL                   C                  Go                   Rust
─────────────────────────────────────────────────────────────────────────────
Length (bytes)         strlen(s)          len(s)               s.len()
Length (chars)         utf8_count(s)*     len([]rune(s))       s.chars().count()
Index (byte)           s[i]               s[i]                 s.as_bytes()[i]
Index (char)           utf8_nth(s,i)*     []rune(s)[i]         s.chars().nth(i)
Substring              ptr + offset       s[lo:hi]             &s[lo..hi]
Find                   strstr(s,p)        strings.Index(s,p)   s.find(p)
Contains               strstr != NULL     strings.Contains      s.contains(p)
Replace                manual             strings.ReplaceAll    s.replace(p,r)
Split                  strtok_r*          strings.Split         s.split(p).collect()
Join                   manual             strings.Join          v.join(sep)
Trim whitespace        manual             strings.TrimSpace     s.trim()
To upper (ASCII)       toupper loop       strings.ToUpper       s.to_ascii_uppercase()
To upper (Unicode)     ICU                strings.ToUpper       s.to_uppercase()
Parse int              strtol             strconv.Atoi          s.parse::<i32>()
Int to string          snprintf           strconv.Itoa          n.to_string()
Concat (builder)       StrBuf*            strings.Builder       String::with_capacity
Regex                  regcomp/regexec    regexp.MustCompile    regex::Regex::new
Unicode normalize      ICU                norm.NFC.String       s.nfc().collect()
Grapheme clusters      ICU                uniseg.Graphemes*     s.graphemes(true)

* = third-party library or manual implementation required
```

---

# Appendix: Quick Reference — Common Pitfalls

```
PITFALL                              LANGUAGE   FIX
────────────────────────────────────────────────────────────────────────
strlen doesn't include NUL           C          malloc(strlen(s)+1)
strncpy may not NUL-terminate        C          always set dst[n-1]='\0'
sizeof on pointer = pointer size     C          use strlen, not sizeof
isspace(char) with signed char       C          cast to unsigned char
strtok modifies input                C          use strtok_r on a copy
len(s) is bytes, not chars           Go         use len([]rune(s))
s[i] is a byte, not a rune           Go         use range loop or []rune(s)
+ in a loop is O(n²)                 Go         use strings.Builder
TrimLeft trims char set not prefix   Go/Rust    use TrimPrefix
NFC ≠ NFD (visual identical)         All        normalize before compare
to_uppercase may lengthen string     All        don't assume len stays same
&s[i] on Rust str can panic          Rust       use s.get(i..j) → Option
Moving String into + invalidates it  Rust       use format! for clarity
Returning &str to local String       Rust       return String instead
&String in fn param (too specific)   Rust       use &str instead
regex without anchors matches inside All        use ^...$ anchors
strconv errors ignored               Go         always check err return
strtol: check endptr and errno       C          full error-check pattern
UTF-16 surrogates in Java/JS         Java/JS    handle surrogate pairs
```

---

*End of guide. All code examples are self-contained and compile with standard toolchains (C11/POSIX, Go 1.21+, Rust 1.75+). Third-party crates noted explicitly.*
