# Rust Primitive Types: A World-Class Comprehensive Guide

> *"To understand a language deeply, first master its atoms — the primitive types are the DNA of every program you will ever write."*

---

## Table of Contents

1. [The Mental Model: How Rust Thinks About Types](#mental-model)
2. [Memory Layout Primer](#memory-layout)
3. [bool — The Logic Gate](#bool)
4. [char — The Unicode Scalar](#char)
5. [str — The String Slice](#str)
6. [Unsigned Integers: u8 → u128, usize](#unsigned)
7. [Signed Integers: i8 → i128, isize](#signed)
8. [Floating Point: f32 & f64](#floats)
9. [Type Casting & Conversions](#casting)
10. [Hardware Reality & Cache Behavior](#hardware)
11. [Real-World Implementations](#realworld)

---

## 1. The Mental Model: How Rust Thinks About Types {#mental-model}

### What Is a Type?

A **type** is a contract between you and the compiler. It answers three questions:

```
┌─────────────────────────────────────────────────────────────┐
│  WHAT A TYPE DEFINES                                         │
│                                                              │
│  1. SIZE     → How many bytes does this occupy in memory?    │
│  2. VALIDITY → Which bit patterns are legal values?          │
│  3. OPS      → What operations can be performed on it?       │
└─────────────────────────────────────────────────────────────┘
```

### The Type Hierarchy

```
Rust Types
├── Scalar (single value)
│   ├── Integer    → i8, i16, i32, i64, i128, isize
│   │               u8, u16, u32, u64, u128, usize
│   ├── Float      → f32, f64
│   ├── Boolean    → bool
│   └── Character  → char
│
└── Compound (multiple values)
    ├── Tuple      → (i32, bool, char)
    ├── Array      → [u8; 256]
    ├── Slice      → &[u8]
    └── str        → &str  (special slice)
```

### Why Static Typing Matters at Hardware Level

When the compiler knows your type at compile time, it can:
- Emit **exact** machine instructions (no runtime dispatch)
- Lay out memory **precisely** (no boxing overhead)
- Enable **SIMD vectorization** (process 8×i32 in one CPU cycle)
- Catch **entire classes of bugs** before runtime

---

## 2. Memory Layout Primer {#memory-layout}

Before touching any type, you must understand how memory works.

### The Stack vs Heap

```
┌──────────────────────────────────────────────────────────┐
│  PROCESS MEMORY MAP                                       │
│                                                          │
│  High Addresses ↑                                        │
│  ┌────────────┐                                          │
│  │   STACK    │  ← Fast. Fixed size. LIFO. Primitives    │
│  │            │    bool, char, integers, floats live here│
│  │  grows ↓   │                                          │
│  ├────────────┤                                          │
│  │   (gap)    │                                          │
│  ├────────────┤                                          │
│  │   HEAP     │  ← Slower. Dynamic. String, Vec live here│
│  │  grows ↑   │                                          │
│  ├────────────┤                                          │
│  │    BSS     │  ← Uninitialized statics                 │
│  ├────────────┤                                          │
│  │   DATA     │  ← Initialized statics, string literals  │
│  ├────────────┤                                          │
│  │   TEXT     │  ← Your compiled machine code            │
│  └────────────┘                                          │
│  Low Addresses ↓                                         │
└──────────────────────────────────────────────────────────┘
```

### Alignment: The Rule the Hardware Enforces

**Alignment** means: a value of size N must start at a memory address divisible by N.

```
Why? Because CPUs read memory in aligned "words" (4 or 8 bytes).
Misaligned reads require TWO memory fetches → slower.

u32 (4 bytes) must live at address: 0, 4, 8, 12, 16 ...
u64 (8 bytes) must live at address: 0, 8, 16, 24 ...

    Address:  0x00  0x01  0x02  0x03  0x04  0x05  0x06  0x07
              ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
    Memory:   │  A  │  A  │  A  │  A  │  B  │  B  │  B  │  B  │
              └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘
              ↑─── u32 A at 0x00 ────↑─── u32 B at 0x04 ───↑
              ✓ ALIGNED                ✓ ALIGNED
```

### Size Reference Table

```
┌──────────┬──────────┬───────────┬────────────────────────────┐
│  TYPE    │  SIZE    │ ALIGNMENT │  VALUE RANGE               │
├──────────┼──────────┼───────────┼────────────────────────────┤
│  bool    │  1 byte  │  1 byte   │  true / false              │
│  char    │  4 bytes │  4 bytes  │  U+0000 to U+10FFFF        │
│  u8      │  1 byte  │  1 byte   │  0 to 255                  │
│  u16     │  2 bytes │  2 bytes  │  0 to 65,535               │
│  u32     │  4 bytes │  4 bytes  │  0 to 4,294,967,295        │
│  u64     │  8 bytes │  8 bytes  │  0 to 18.4 quintillion     │
│  u128    │ 16 bytes │  16 bytes │  0 to 3.4 × 10^38          │
│  usize   │  8 bytes │  8 bytes  │  0 to 2^64-1 (on 64-bit)  │
│  i8      │  1 byte  │  1 byte   │  -128 to 127               │
│  i16     │  2 bytes │  2 bytes  │  -32,768 to 32,767         │
│  i32     │  4 bytes │  4 bytes  │  -2.1B to 2.1B             │
│  i64     │  8 bytes │  8 bytes  │  -9.2 × 10^18 to same      │
│  i128    │ 16 bytes │  16 bytes │  ±1.7 × 10^38              │
│  isize   │  8 bytes │  8 bytes  │  ±2^63 (on 64-bit)        │
│  f32     │  4 bytes │  4 bytes  │  ~±3.4 × 10^38             │
│  f64     │  8 bytes │  8 bytes  │  ~±1.8 × 10^308            │
└──────────┴──────────┴───────────┴────────────────────────────┘
```

---

## 3. bool — The Logic Gate {#bool}

### What Is bool?

`bool` represents a single binary truth value. At the machine level, it is stored as a **single byte** (not a single bit), where:
- `false` = byte value `0x00`
- `true`  = byte value `0x01`

```
Why 1 byte and not 1 bit?
→ Modern CPUs cannot address individual bits.
→ The smallest addressable unit is 1 byte.
→ So even a single bool wastes 7 bits of space.
→ For packed booleans: use bitsets (covered in advanced topics).
```

### Memory Representation

```
bool false:   0000 0000  (0x00)
bool true:    0000 0001  (0x01)

IMPORTANT: In Rust, ONLY 0x00 and 0x01 are valid bool bit patterns.
Any other byte value is UNDEFINED BEHAVIOR if transmuted to bool.
This allows the compiler to optimize: if(b) → TEST byte, JNZ
```

### Operations on bool

```
LOGICAL OPERATORS (short-circuit):
  &&  → AND  — if left is false, right is NOT evaluated
  ||  → OR   — if left is true,  right is NOT evaluated

BITWISE OPERATORS (no short-circuit, both sides always evaluated):
  &   → bitwise AND
  |   → bitwise OR
  ^   → bitwise XOR
  !   → NOT (logical negation)
```

### Production-Grade bool Code

```rust
// ─────────────────────────────────────────────────────────────
// FILE: bool_guide.rs
// PURPOSE: Demonstrates bool usage patterns in production Rust
// ─────────────────────────────────────────────────────────────

/// Memory size verification — always verify your assumptions
#[test]
fn verify_bool_layout() {
    use std::mem;
    assert_eq!(mem::size_of::<bool>(), 1);   // 1 byte
    assert_eq!(mem::align_of::<bool>(), 1);  // 1-byte aligned
}

// ── PATTERN 1: State Flags in a System ────────────────────────

/// Represents the operational state of a network connection.
/// Each field is a bool — simple, self-documenting, zero-cost.
#[derive(Debug, Clone, Copy)]
pub struct ConnectionState {
    pub is_connected:    bool,
    pub is_authenticated: bool,
    pub is_encrypted:    bool,
    pub is_rate_limited: bool,
}

impl ConnectionState {
    /// Returns true only if the connection is fully operational.
    ///
    /// COGNITIVE NOTE: Chain && for "all must be true" logic.
    /// Short-circuit means: if is_connected is false, the rest
    /// are never evaluated — matches real-world logic perfectly.
    #[inline]
    pub fn is_fully_operational(&self) -> bool {
        self.is_connected
            && self.is_authenticated
            && self.is_encrypted
            && !self.is_rate_limited
    }

    /// Returns true if connection needs any attention.
    #[inline]
    pub fn needs_attention(&self) -> bool {
        !self.is_connected
            || !self.is_authenticated
            || self.is_rate_limited
    }
}

// ── PATTERN 2: bool as Function Return (Predicate Pattern) ────

/// Validates that a username meets security requirements.
///
/// EXPERT PATTERN: Predicates return bool. They answer YES/NO
/// questions about data. Name them: is_X, has_X, can_X, should_X.
pub fn is_valid_username(name: &str) -> bool {
    const MIN_LEN: usize = 3;
    const MAX_LEN: usize = 32;

    if name.len() < MIN_LEN || name.len() > MAX_LEN {
        return false;
    }

    // All characters must be alphanumeric or underscore
    name.chars().all(|c| c.is_alphanumeric() || c == '_')
}

// ── PATTERN 3: bool Optimization — Branchless Code ────────────

/// Counts how many values in a slice satisfy a predicate.
///
/// PERFORMANCE INSIGHT: Converting bool to u8 (0 or 1) lets
/// the CPU accumulate counts WITHOUT branch instructions.
/// Branches are expensive due to CPU pipeline flushing.
/// This is called "branchless programming" — used in hot paths.
pub fn count_matching<T, F>(slice: &[T], predicate: F) -> usize
where
    F: Fn(&T) -> bool,
{
    slice.iter()
        .map(|item| predicate(item) as usize)  // bool → 0 or 1
        .sum()
    // The compiler can auto-vectorize this into SIMD instructions:
    // Process 32 bools at once using AVX2 registers!
}

// ── PATTERN 4: Packed Booleans with Bitflags ──────────────────
// When you have many booleans, pack them into an integer.
// A u8 holds 8 booleans in 1 byte vs 8 bytes individually.

/// Permission flags packed into a single byte.
/// Bit 0 = read, Bit 1 = write, Bit 2 = execute, etc.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Permissions(u8);

impl Permissions {
    const READ:    u8 = 0b0000_0001;  // bit 0
    const WRITE:   u8 = 0b0000_0010;  // bit 1
    const EXECUTE: u8 = 0b0000_0100;  // bit 2

    pub fn new() -> Self { Self(0) }

    pub fn with_read(self) -> Self {
        Self(self.0 | Self::READ)
    }

    pub fn with_write(self) -> Self {
        Self(self.0 | Self::WRITE)
    }

    pub fn with_execute(self) -> Self {
        Self(self.0 | Self::EXECUTE)
    }

    pub fn can_read(&self) -> bool {
        self.0 & Self::READ != 0
    }

    pub fn can_write(&self) -> bool {
        self.0 & Self::WRITE != 0
    }

    pub fn can_execute(&self) -> bool {
        self.0 & Self::EXECUTE != 0
    }
}

// ── PATTERN 5: bool in match expressions ──────────────────────

pub fn describe_access(perms: &Permissions) -> &'static str {
    // IDIOMATIC: match on tuple of bools for multi-condition logic
    match (perms.can_read(), perms.can_write(), perms.can_execute()) {
        (true,  true,  true)  => "full access",
        (true,  true,  false) => "read-write",
        (true,  false, false) => "read-only",
        (false, false, false) => "no access",
        _                     => "partial access",
    }
}

fn main() {
    // Verify layout
    use std::mem;
    println!("bool size:      {} byte", mem::size_of::<bool>());
    println!("bool alignment: {} byte", mem::align_of::<bool>());

    // Test connection state
    let conn = ConnectionState {
        is_connected:     true,
        is_authenticated: true,
        is_encrypted:     true,
        is_rate_limited:  false,
    };
    println!("Operational: {}", conn.is_fully_operational()); // true

    // Test packed permissions
    let perms = Permissions::new()
        .with_read()
        .with_write();
    println!("Access: {}", describe_access(&perms)); // read-write
    println!("Perms byte: {:08b}", perms.0);         // 00000011

    // Test predicate counting
    let numbers = vec![1i32, -2, 3, -4, 5, -6, 7, -8];
    let positive_count = count_matching(&numbers, |&x| x > 0);
    println!("Positive numbers: {}", positive_count); // 4
}
```

### bool: Common Mistakes to Avoid

```
❌ MISTAKE: Redundant boolean comparison
   if is_valid == true { ... }

✓ CORRECT:
   if is_valid { ... }

❌ MISTAKE: Returning bool expression as if-else
   if condition { return true; } else { return false; }

✓ CORRECT:
   return condition;

❌ MISTAKE: Using & when && is intended (side-effect bug)
   if authenticate() & authorize() { ... }
   // Both functions ALWAYS run even if authenticate() is false!

✓ CORRECT:
   if authenticate() && authorize() { ... }
   // authorize() only runs if authenticate() returns true
```

---

## 4. char — The Unicode Scalar {#char}

### What Is char?

A Rust `char` is **not** an ASCII character. It is a **Unicode Scalar Value (USV)** — a 32-bit (4-byte) value representing any valid Unicode character from the entire human writing system.

```
Unicode Scalar Value:
→ Any Unicode code point EXCEPT surrogate pairs (U+D800–U+DFFF)
→ Range: U+0000 to U+D7FF, then U+E000 to U+10FFFF
→ That's 1,114,112 possible values — every human script

Examples:
  'A'      → U+0041  (Latin capital A)
  'é'      → U+00E9  (Latin e with acute)
  '中'      → U+4E2D  (Chinese character for "middle")
  '🦀'     → U+1F980 (Crab — Rust's mascot emoji)
  '\n'     → U+000A  (Newline control character)
  '\u{1F980}' → Same as 🦀 via Unicode escape
```

### Memory Representation

```
char is ALWAYS 4 bytes (u32 internally), regardless of the character.

'A' (U+0041):
  Memory:  41 00 00 00  (little-endian on x86-64)
  
'🦀' (U+1F980):
  Memory:  80 F9 01 00  (little-endian)

This differs from UTF-8 strings where characters use 1–4 bytes.
A char has FIXED 4-byte size. A UTF-8 encoded char is VARIABLE.
```

### char vs String Encoding

```
┌─────────────────────────────────────────────────────────────┐
│  char  vs  str/String                                        │
│                                                              │
│  char:    Fixed 4 bytes. A single Unicode scalar value.      │
│           Guaranteed valid. Never an invalid code point.     │
│                                                              │
│  str:     UTF-8 encoded. Variable width (1–4 bytes/char).    │
│           A sequence of bytes that form valid UTF-8.         │
│                                                              │
│  ASCII 'A':   char = [0x41, 0x00, 0x00, 0x00] (4 bytes)    │
│               UTF-8 = [0x41]                   (1 byte)     │
│                                                              │
│  '中' U+4E2D: char = [0x2D, 0x4E, 0x00, 0x00] (4 bytes)   │
│               UTF-8 = [0xE4, 0xB8, 0xAD]       (3 bytes)   │
└─────────────────────────────────────────────────────────────┘
```

### Production-Grade char Code

```rust
// ─────────────────────────────────────────────────────────────
// FILE: char_guide.rs
// PURPOSE: Demonstrates char usage patterns in production Rust
// ─────────────────────────────────────────────────────────────

use std::mem;

// ── LAYOUT VERIFICATION ───────────────────────────────────────
#[test]
fn verify_char_layout() {
    assert_eq!(mem::size_of::<char>(), 4);
    assert_eq!(mem::align_of::<char>(), 4);
}

// ── CHAR CLASSIFICATION METHODS ───────────────────────────────

/// Demonstrates the rich classification API on char.
/// These are Unicode-aware — they handle all scripts, not just ASCII.
pub fn demonstrate_char_classification() {
    let samples: &[char] = &[
        'A', 'a', '5', ' ', '\n', '!', '中', 'é', '🦀',
    ];

    for &c in samples {
        println!(
            "'{}'  | alpha:{:5} | digit:{:5} | upper:{:5} | \
             lower:{:5} | space:{:5} | ascii:{:5} | U+{:04X}",
            c,
            c.is_alphabetic(),    // true for letters in ANY script
            c.is_numeric(),       // true for digits (incl. Arabic-Indic)
            c.is_uppercase(),
            c.is_lowercase(),
            c.is_whitespace(),    // true for any Unicode whitespace
            c.is_ascii(),         // true only for U+0000..U+007F
            c as u32              // cast char to its Unicode code point
        );
    }
}

// ── PATTERN 1: Lexer / Tokenizer (Real-World Use) ─────────────

/// Represents a token type in a simple expression language.
#[derive(Debug, PartialEq)]
pub enum TokenKind {
    Number(f64),
    Identifier(String),
    Plus,
    Minus,
    Star,
    Slash,
    LeftParen,
    RightParen,
    Whitespace,
    Unknown(char),
}

/// Classifies a single character into its token kind.
/// This is how real lexers work — char-by-char classification.
///
/// EXPERT PATTERN: match on char is EXTREMELY efficient.
/// The compiler generates a jump table for contiguous ranges.
pub fn classify_char(c: char) -> TokenKind {
    match c {
        '+' => TokenKind::Plus,
        '-' => TokenKind::Minus,
        '*' => TokenKind::Star,
        '/' => TokenKind::Slash,
        '(' => TokenKind::LeftParen,
        ')' => TokenKind::RightParen,

        // RANGE PATTERN: matches '0', '1', ..., '9'
        '0'..='9' => {
            // Convert ASCII digit to its numeric value
            // This works because ASCII digits are contiguous: '0'=48, '9'=57
            let digit = (c as u8 - b'0') as f64;
            TokenKind::Number(digit)
        }

        // Match any Unicode alphabetic character (all scripts!)
        c if c.is_alphabetic() || c == '_' => {
            TokenKind::Identifier(c.to_string())
        }

        c if c.is_whitespace() => TokenKind::Whitespace,

        other => TokenKind::Unknown(other),
    }
}

// ── PATTERN 2: char ↔ u32 Conversion ─────────────────────────

/// Demonstrates char to integer conversion and back.
///
/// INSIGHT: char IS a u32 internally.
/// 'A' as u32 → 65
/// char::from_u32(65) → Some('A')
pub fn char_integer_conversion() {
    // char → u32: always safe (every valid char has a code point)
    let c: char = '🦀';
    let code_point: u32 = c as u32;
    println!("'{}' = U+{:04X} = {}", c, code_point, code_point);

    // u32 → char: might fail (not all u32 values are valid chars)
    // Use char::from_u32 which returns Option<char>
    let valid   = char::from_u32(0x41);       // Some('A')
    let invalid = char::from_u32(0xD800);     // None (surrogate)
    let emoji   = char::from_u32(0x1F980);   // Some('🦀')

    println!("U+0041 → {:?}", valid);
    println!("U+D800 → {:?}", invalid);
    println!("U+1F980 → {:?}", emoji);

    // char → u8: ONLY safe for ASCII (use with care)
    let ascii_char: char = 'A';
    if ascii_char.is_ascii() {
        let byte: u8 = ascii_char as u8;  // Safe: 'A' = 65
        println!("'A' as u8 = {}", byte);
    }
}

// ── PATTERN 3: char Case Conversion ───────────────────────────

/// Case conversion is Unicode-aware in Rust.
/// 'ß'.to_uppercase() → "SS" (two characters!)
/// This is why to_uppercase returns an iterator, not a char.
pub fn demonstrate_case_conversion() {
    let chars = ['a', 'A', 'é', 'ß', '中'];

    for c in chars {
        // to_uppercase/lowercase return iterators because
        // some Unicode chars expand to multiple chars when cased.
        let upper: String = c.to_uppercase().collect();
        let lower: String = c.to_lowercase().collect();
        println!("'{}' upper='{}' lower='{}'", c, upper, lower);
    }
    // Output:
    // 'a' upper='A' lower='a'
    // 'A' upper='A' lower='a'
    // 'é' upper='É' lower='é'
    // 'ß' upper='SS' lower='ß'   ← Two chars from one!
    // '中' upper='中' lower='中'
}

// ── PATTERN 4: UTF-8 Encoding of a char ───────────────────────

/// Encode a char to its UTF-8 byte representation.
///
/// INSIGHT: This is what happens inside String when you push a char.
/// Understanding this bridges char ↔ str.
pub fn encode_char_to_utf8(c: char) -> Vec<u8> {
    let mut buf = [0u8; 4];  // max 4 bytes for any UTF-8 char
    let s = c.encode_utf8(&mut buf);
    s.as_bytes().to_vec()
}

pub fn demonstrate_utf8_encoding() {
    let examples = [
        ('A',  "U+0041 (1 byte ASCII)"),
        ('é',  "U+00E9 (2 byte Latin)"),
        ('中', "U+4E2D (3 byte CJK)"),
        ('🦀', "U+1F980 (4 byte emoji)"),
    ];

    for (c, desc) in examples {
        let bytes = encode_char_to_utf8(c);
        let hex: Vec<String> = bytes.iter()
            .map(|b| format!("{:02X}", b))
            .collect();
        println!("{}: '{}' → [{}]", desc, c, hex.join(", "));
    }
    // A:   [41]
    // é:   [C3, A9]
    // 中:  [E4, B8, AD]
    // 🦀: [F0, 9F, A6, 80]
}

fn main() {
    println!("=== char Layout ===");
    println!("size:      {} bytes", mem::size_of::<char>());
    println!("alignment: {} bytes", mem::align_of::<char>());

    println!("\n=== Classification ===");
    demonstrate_char_classification();

    println!("\n=== Integer Conversion ===");
    char_integer_conversion();

    println!("\n=== Case Conversion ===");
    demonstrate_case_conversion();

    println!("\n=== UTF-8 Encoding ===");
    demonstrate_utf8_encoding();
}
```

---

## 5. str — The String Slice {#str}

### What Is str?

`str` is the **most fundamental string type** in Rust. It is a **dynamically-sized slice of UTF-8 bytes**. Because its size is unknown at compile time, you almost always use it behind a reference: `&str`.

```
CONCEPTUAL MODEL of &str:

    &str is a FAT POINTER — two machine words:

    ┌──────────────┬──────────────┐
    │   pointer    │    length    │
    │  (8 bytes)   │  (8 bytes)  │
    └──────────────┴──────────────┘
         │                │
         │                └─→ number of BYTES (not chars!)
         │
         └─→ points to UTF-8 encoded bytes in memory
             (could be stack, heap, or data segment)

Total size of &str on 64-bit: 16 bytes (two usize values)
```

### str vs String vs &str

```
┌───────────────────────────────────────────────────────────────┐
│  THE THREE STRING TYPES                                        │
│                                                                │
│  str      → A slice type. Unsized. Never used alone.          │
│             Lives in code as a concept, not a variable.        │
│                                                                │
│  &str     → A reference to str. Fat pointer (ptr + len).      │
│             Immutable view into UTF-8 bytes.                   │
│             Can point to: string literals, String heap data,   │
│             or any valid UTF-8 byte slice.                     │
│                                                                │
│  String   → An owned, heap-allocated, growable UTF-8 string.  │
│             Three words: (ptr, len, capacity)                  │
│             Like Vec<u8> but guaranteed valid UTF-8.           │
│                                                                │
│  &str  → reading/borrowing a string (zero-copy view)          │
│  String → owning/building a string (heap allocation)          │
└───────────────────────────────────────────────────────────────┘
```

### String Literal Internals

```rust
let s: &str = "hello";

// Where does "hello" live?
// → In the binary's DATA SEGMENT (read-only memory)
// → The &str is a pointer into the compiled binary
// → This is why string literals have 'static lifetime

// Memory layout:
//
// Binary DATA segment:
//   [0x68, 0x65, 0x6C, 0x6C, 0x6F]  ← "hello" bytes
//    h      e      l      l      o
//
// &str on stack:
//   [ptr: 0x400123] [len: 5]
//         ↓
//   points into binary data
```

### Production-Grade str Code

```rust
// ─────────────────────────────────────────────────────────────
// FILE: str_guide.rs
// PURPOSE: Demonstrates str/String patterns in production Rust
// ─────────────────────────────────────────────────────────────

use std::mem;

// ── LAYOUT VERIFICATION ───────────────────────────────────────
#[test]
fn verify_str_layout() {
    // &str is a fat pointer: (ptr, len) — two usize values
    assert_eq!(mem::size_of::<&str>(), 2 * mem::size_of::<usize>());
    // On 64-bit: 16 bytes
}

// ── PATTERN 1: &str as Function Parameters ────────────────────

/// EXPERT RULE: Accept &str in function parameters, not &String.
///
/// Why? &String auto-derefs to &str, so &str accepts BOTH:
///   - string literals:  &str
///   - owned Strings:    &String (via Deref coercion)
///
/// This is the "Deref Coercion" principle — a zero-cost abstraction.
pub fn count_words(text: &str) -> usize {
    // split_whitespace handles: spaces, tabs, newlines, \r\n
    // It is Unicode-aware and handles multiple consecutive spaces
    text.split_whitespace().count()
}

// ── PATTERN 2: String Slicing — The Byte Index Trap ───────────

/// CRITICAL INSIGHT: str indices are BYTE positions, not char positions!
/// Slicing at a non-char-boundary will PANIC at runtime.
///
/// This is Rust's protection against invalid UTF-8.
pub fn demonstrate_slicing() {
    let s = "hello, world";

    // ASCII: byte index == char index (safe)
    let hello: &str = &s[0..5];   // bytes 0..5
    println!("{}", hello);         // "hello"

    // DANGEROUS with multi-byte chars:
    let mixed = "héllo";  // 'é' is 2 bytes at position 1-2

    // &mixed[1..2] would PANIC: cuts 'é' in the middle!
    // SAFE alternative: use char_indices()
    let safe_slice: String = mixed
        .char_indices()             // yields (byte_pos, char)
        .skip(1)                    // skip 'h'
        .take(3)                    // take 'é', 'l', 'l'
        .map(|(_, c)| c)
        .collect();
    println!("Safe slice: {}", safe_slice);  // "éll"
}

// ── PATTERN 3: str Methods Reference ──────────────────────────

pub fn demonstrate_str_methods() {
    let text = "  Hello, World! Hello, Rust!  ";

    // ── Searching ──────────────────────────────────────────────
    println!("{}", text.contains("Rust"));        // true
    println!("{}", text.starts_with("  Hello"));  // true
    println!("{}", text.ends_with("!  "));        // true

    // find returns byte index of first match
    if let Some(pos) = text.find("World") {
        println!("'World' at byte {}", pos);   // 9
    }

    // ── Trimming ───────────────────────────────────────────────
    let trimmed = text.trim();           // remove leading/trailing whitespace
    let left    = text.trim_start();     // remove only leading
    let right   = text.trim_end();       // remove only trailing
    println!("Trimmed: '{}'", trimmed);

    // ── Splitting ──────────────────────────────────────────────
    // split returns an iterator (lazy — no allocation until collected)
    let words: Vec<&str> = "one,two,three".split(',').collect();
    println!("{:?}", words);  // ["one", "two", "three"]

    // splitn limits to N parts
    let parts: Vec<&str> = "a:b:c:d".splitn(3, ':').collect();
    println!("{:?}", parts);  // ["a", "b", "c:d"]

    // ── Replacing ──────────────────────────────────────────────
    let replaced = text.replace("Hello", "Hi");  // returns new String
    let replaced_n = text.replacen("Hello", "Hi", 1); // first N only

    // ── Case ───────────────────────────────────────────────────
    let upper = text.to_uppercase();  // Unicode-aware
    let lower = text.to_lowercase();  // Unicode-aware

    // ── Char Operations ────────────────────────────────────────
    println!("byte len: {}", text.len());       // byte count
    println!("char count: {}", text.chars().count()); // Unicode char count
    // Note: .len() is O(1), .chars().count() is O(n)!

    // Iterate characters (correct Unicode iteration)
    for c in "héllo".chars() {
        print!("[{}]", c);
    }
    println!();  // [h][é][l][l][o]

    // Iterate bytes (raw UTF-8 bytes)
    for b in "héllo".bytes() {
        print!("{:02X} ", b);
    }
    println!();  // 68 C3 A9 6C 6C 6F
}

// ── PATTERN 4: Building Strings Efficiently ───────────────────

/// PERFORMANCE INSIGHT: String concatenation with + creates
/// many allocations. Use a String with push_str or format!
/// for clarity, or write! for zero-allocation building.
pub fn build_string_efficiently(parts: &[&str]) -> String {
    // BAD: each + creates a new allocation
    // let s = "hello" + " " + "world";  // doesn't even compile!

    // GOOD: pre-allocate capacity, then push
    let total_len: usize = parts.iter().map(|s| s.len()).sum();
    let mut result = String::with_capacity(total_len + parts.len());

    for (i, part) in parts.iter().enumerate() {
        if i > 0 {
            result.push(' ');          // push a char
        }
        result.push_str(part);         // push a &str (no allocation)
    }
    result
    // COMPLEXITY: O(n) time, O(n) space, exactly ONE heap allocation
}

// ── PATTERN 5: String Parsing ─────────────────────────────────

/// Parse a key=value configuration line.
///
/// EXPERT PATTERN: Return Option/Result, never panic on bad input.
/// splitn(2, '=') splits into AT MOST 2 parts — handles values
/// that contain '=' (e.g., "token=abc=def" → key="token", val="abc=def")
pub fn parse_config_line(line: &str) -> Option<(&str, &str)> {
    let line = line.trim();

    // Skip empty lines and comments
    if line.is_empty() || line.starts_with('#') {
        return None;
    }

    // splitn ensures values can contain '='
    let mut parts = line.splitn(2, '=');
    let key   = parts.next()?.trim();
    let value = parts.next()?.trim();

    if key.is_empty() {
        return None;
    }

    Some((key, value))
}

fn main() {
    println!("=== &str Layout ===");
    println!("size of &str: {} bytes", mem::size_of::<&str>());

    println!("\n=== Slicing ===");
    demonstrate_slicing();

    println!("\n=== Methods ===");
    demonstrate_str_methods();

    println!("\n=== Building Strings ===");
    let parts = ["The", "quick", "brown", "fox"];
    println!("{}", build_string_efficiently(&parts));

    println!("\n=== Parsing ===");
    let lines = ["host = localhost", "# comment", "port=8080", "=bad"];
    for line in &lines {
        println!("{:?} → {:?}", line, parse_config_line(line));
    }
}
```

---

## 6. Unsigned Integers: u8 → u128, usize {#unsigned}

### The Mental Model: Bit Counting

An unsigned N-bit integer stores exactly **2^N** different values: 0 through 2^N - 1.

```
NUMBER OF BITS → NUMBER OF VALUES → RANGE

u8:   2^8  = 256          values  →  0 to 255
u16:  2^16 = 65,536        values  →  0 to 65,535
u32:  2^32 = 4,294,967,296 values  →  0 to 4,294,967,295
u64:  2^64 ≈ 1.8 × 10^19  values  →  0 to ~18.4 quintillion
u128: 2^128 ≈ 3.4 × 10^38 values  →  astronomically large

FORMULA: max value = 2^N - 1
```

### Binary Representation

```
u8 value 42:
  Bit 7 6 5 4 3 2 1 0
       0 0 1 0 1 0 1 0
       │   │   │   │ │
       │   │   │   │ └── 2^0 = 1  (0×1 = 0)
       │   │   │   └──── 2^1 = 2  (1×2 = 2)
       │   │   └──────── 2^2 = 4  (0×4 = 0)
       │   └──────────── 2^3 = 8  (1×8 = 8)
       └──────────────── 2^5 = 32 (1×32 = 32)
                                    Total: 32+8+2 = 42 ✓
```

### usize: The Platform-Native Integer

```
usize is special:
  → On 32-bit systems: 4 bytes (u32)
  → On 64-bit systems: 8 bytes (u64)
  → It matches the pointer size of the platform

Use usize for:
  ✓ Array/slice indices:  arr[i]  where i: usize
  ✓ Lengths:              vec.len() returns usize
  ✓ Memory sizes:         mem::size_of::<T>() returns usize
  ✓ Pointer arithmetic

DO NOT use usize for:
  ✗ Business data (ages, counts that should be u32)
  ✗ Serialized data (format would change across platforms)
```

### Production-Grade Unsigned Integer Code

```rust
// ─────────────────────────────────────────────────────────────
// FILE: unsigned_integers.rs
// PURPOSE: Production patterns for unsigned integer types
// ─────────────────────────────────────────────────────────────

use std::mem;

// ── TYPE CONSTANTS AND RANGES ─────────────────────────────────
fn print_unsigned_ranges() {
    println!("Type  | Size | Min | Max");
    println!("u8    | {}B   | {}   | {}", mem::size_of::<u8>(),   u8::MIN,   u8::MAX);
    println!("u16   | {}B   | {}   | {}", mem::size_of::<u16>(),  u16::MIN,  u16::MAX);
    println!("u32   | {}B   | {}   | {}", mem::size_of::<u32>(),  u32::MIN,  u32::MAX);
    println!("u64   | {}B   | {}   | {}", mem::size_of::<u64>(),  u64::MIN,  u64::MAX);
    println!("u128  | {}B  | {}   | {}", mem::size_of::<u128>(), u128::MIN, u128::MAX);
    println!("usize | {}B   | {}   | {}", mem::size_of::<usize>(),usize::MIN,usize::MAX);
}

// ── PATTERN 1: u8 — The Byte Type ─────────────────────────────

/// u8 IS a byte. It's the atomic unit of memory.
/// Use it for: raw bytes, pixel values, network packets, hashing.

/// RGB color — three bytes, natural fit for u8 (0–255 per channel)
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Color {
    pub r: u8,
    pub g: u8,
    pub b: u8,
}

impl Color {
    pub const BLACK: Color = Color { r: 0,   g: 0,   b: 0   };
    pub const WHITE: Color = Color { r: 255, g: 255, b: 255 };
    pub const RED:   Color = Color { r: 255, g: 0,   b: 0   };

    /// Blend two colors 50/50.
    /// INSIGHT: Use u16 intermediate to avoid u8 overflow during addition.
    pub fn blend(self, other: Color) -> Color {
        Color {
            r: ((self.r as u16 + other.r as u16) / 2) as u8,
            g: ((self.g as u16 + other.g as u16) / 2) as u8,
            b: ((self.b as u16 + other.b as u16) / 2) as u8,
        }
    }

    /// Convert to hex string #RRGGBB
    pub fn to_hex(&self) -> String {
        format!("#{:02X}{:02X}{:02X}", self.r, self.g, self.b)
    }

    /// Compute perceived luminance (brightness).
    /// Uses BT.709 coefficients as f64, returns 0.0–1.0.
    pub fn luminance(&self) -> f64 {
        const R_WEIGHT: f64 = 0.2126;
        const G_WEIGHT: f64 = 0.7152;
        const B_WEIGHT: f64 = 0.0722;
        const MAX_VAL:  f64 = 255.0;

        (self.r as f64 / MAX_VAL) * R_WEIGHT
            + (self.g as f64 / MAX_VAL) * G_WEIGHT
            + (self.b as f64 / MAX_VAL) * B_WEIGHT
    }
}

// ── PATTERN 2: u16 — Port Numbers, Small Counts ───────────────

/// TCP/UDP port: 0–65535, perfectly fits u16.
/// This is not just style — it DOCUMENTS the domain constraint.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub struct Port(u16);

impl Port {
    pub const HTTP:  Port = Port(80);
    pub const HTTPS: Port = Port(443);
    pub const SSH:   Port = Port(22);

    const WELL_KNOWN_MAX:  u16 = 1023;
    const REGISTERED_MAX: u16 = 49151;

    pub fn new(value: u16) -> Self { Self(value) }
    pub fn value(&self) -> u16 { self.0 }

    pub fn is_well_known(&self)  -> bool { self.0 <= Self::WELL_KNOWN_MAX }
    pub fn is_registered(&self)  -> bool {
        self.0 > Self::WELL_KNOWN_MAX && self.0 <= Self::REGISTERED_MAX
    }
    pub fn is_ephemeral(&self)   -> bool { self.0 > Self::REGISTERED_MAX }
}

// ── PATTERN 3: u32 — IDs, Counts, IPv4 Addresses ─────────────

/// An IPv4 address stored as a single u32.
/// 4 bytes = 4 octets. This is the actual binary format.
/// Network byte order (big-endian): 192.168.1.1 = 0xC0A80101
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Ipv4Addr(u32);

impl Ipv4Addr {
    pub fn new(a: u8, b: u8, c: u8, d: u8) -> Self {
        // Pack four octets into one u32 (big-endian)
        Self(
            (a as u32) << 24
            | (b as u32) << 16
            | (c as u32) << 8
            | (d as u32)
        )
    }

    pub fn octets(&self) -> [u8; 4] {
        [
            (self.0 >> 24) as u8,  // extract highest byte
            (self.0 >> 16) as u8,
            (self.0 >> 8)  as u8,
            (self.0)       as u8,  // extract lowest byte
        ]
    }

    pub fn is_loopback(&self) -> bool {
        // 127.0.0.0/8: any address starting with 127
        (self.0 >> 24) == 127
    }

    pub fn is_private(&self) -> bool {
        // 10.0.0.0/8
        (self.0 >> 24) == 10
        // 172.16.0.0/12
        || (self.0 >> 20) == 0b1010_1100_0001  // 172.16–172.31
        // 192.168.0.0/16
        || (self.0 >> 16) == 0xC0A8
    }
}

impl std::fmt::Display for Ipv4Addr {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let [a, b, c, d] = self.octets();
        write!(f, "{}.{}.{}.{}", a, b, c, d)
    }
}

// ── PATTERN 4: u64 — Timestamps, File Sizes ───────────────────

/// Unix timestamp in nanoseconds since epoch.
///
/// WHY u64?
/// - Year 2024 in nanoseconds: ~1.7 × 10^18
/// - u64 max: ~1.8 × 10^19
/// - Safe for next ~580 years
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub struct Timestamp(u64);

impl Timestamp {
    const NANOS_PER_SECOND: u64 = 1_000_000_000;
    const NANOS_PER_MILLI:  u64 = 1_000_000;
    const NANOS_PER_MICRO:  u64 = 1_000;

    pub fn from_nanos(nanos: u64)   -> Self { Self(nanos) }
    pub fn from_millis(ms: u64)     -> Self { Self(ms * Self::NANOS_PER_MILLI) }
    pub fn from_secs(secs: u64)     -> Self { Self(secs * Self::NANOS_PER_SECOND) }

    pub fn as_nanos(&self)  -> u64 { self.0 }
    pub fn as_millis(&self) -> u64 { self.0 / Self::NANOS_PER_MILLI }
    pub fn as_secs(&self)   -> u64 { self.0 / Self::NANOS_PER_SECOND }

    /// Duration between two timestamps.
    /// Returns None if other is earlier than self (prevents underflow).
    pub fn duration_since(&self, earlier: Timestamp) -> Option<u64> {
        self.0.checked_sub(earlier.0)
    }
}

// ── PATTERN 5: u128 — Cryptographic Hashes, UUIDs ─────────────

/// A UUID (Universally Unique Identifier) — 128 bits.
/// RFC 4122 standard. Stored as u128.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Uuid(u128);

impl Uuid {
    pub const NIL: Uuid = Uuid(0);

    pub fn from_u128(v: u128) -> Self { Self(v) }

    /// Convert to the standard hyphenated string format.
    /// xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    pub fn to_hyphenated(&self) -> String {
        format!(
            "{:08x}-{:04x}-{:04x}-{:04x}-{:012x}",
            (self.0 >> 96)         as u32,  // time_low
            (self.0 >> 80) as u16,           // time_mid
            (self.0 >> 64) as u16,           // time_hi_and_version
            (self.0 >> 48) as u16,           // clock_seq
            self.0          as u64 & 0xFFFF_FFFF_FFFF, // node
        )
    }
}

// ── PATTERN 6: Overflow-Safe Arithmetic ───────────────────────

/// CRITICAL: Integer overflow in Rust:
/// - DEBUG builds:   panics at runtime  (catches bugs early)
/// - RELEASE builds: wraps around (silent! use checked/saturating)
///
/// EXPERT RULE: Use checked_, saturating_, or wrapping_ variants
/// whenever overflow is possible.
pub fn demonstrate_overflow_safety() {
    let max: u8 = u8::MAX;  // 255

    // checked_add: returns None on overflow
    println!("{:?}", max.checked_add(1));       // None
    println!("{:?}", max.checked_add(0));       // Some(255)

    // saturating_add: clamps to max/min value
    println!("{}", max.saturating_add(1));      // 255 (clamps)
    println!("{}", max.saturating_add(100));    // 255 (clamps)

    // wrapping_add: wraps around (explicit modular arithmetic)
    println!("{}", max.wrapping_add(1));        // 0 (255 + 1 wraps)
    println!("{}", max.wrapping_add(2));        // 1

    // overflowing_add: returns (result, did_overflow)
    println!("{:?}", max.overflowing_add(1));   // (0, true)
    println!("{:?}", max.overflowing_add(0));   // (255, false)
}

// ── PATTERN 7: Bitwise Operations ─────────────────────────────

/// Bit manipulation is fundamental to systems programming.
/// Used in: protocols, compression, graphics, cryptography.
pub fn demonstrate_bit_operations() {
    let flags: u8 = 0b0000_0000;

    // SET bit N:    value | (1 << N)
    let with_bit2: u8 = flags | (1 << 2);   // 0000_0100
    println!("Set bit 2:   {:08b}", with_bit2);

    // CLEAR bit N:  value & !(1 << N)
    let cleared: u8 = with_bit2 & !(1 << 2); // 0000_0000
    println!("Clear bit 2: {:08b}", cleared);

    // TOGGLE bit N: value ^ (1 << N)
    let toggled: u8 = with_bit2 ^ (1 << 2);  // 0000_0000
    println!("Toggle bit 2: {:08b}", toggled);

    // CHECK bit N:  (value >> N) & 1  or  value & (1 << N) != 0
    let val: u8 = 0b1010_0110;
    for bit in 0..8u8 {
        let is_set = (val >> bit) & 1 == 1;
        if is_set { println!("Bit {} is set", bit); }
    }

    // COUNT SET BITS (popcount) — hardware instruction on modern CPUs
    println!("Popcount of {:08b}: {}", val, val.count_ones());
    println!("Leading zeros:  {}", val.leading_zeros());
    println!("Trailing zeros: {}", val.trailing_zeros());

    // ROTATE (not shift): bits wrap around
    println!("Rotate left 3:  {:08b}", val.rotate_left(3));
}

fn main() {
    println!("=== Unsigned Integer Ranges ===");
    print_unsigned_ranges();

    println!("\n=== Color Type (u8) ===");
    let red  = Color::RED;
    let blue = Color { r: 0, g: 0, b: 255 };
    let mixed = red.blend(blue);
    println!("Red: {}   Blue: {}   Mixed: {}", red.to_hex(), blue.to_hex(), mixed.to_hex());
    println!("Red luminance: {:.4}", red.luminance());

    println!("\n=== IPv4 (u32) ===");
    let ip = Ipv4Addr::new(192, 168, 1, 100);
    println!("{} | private: {}", ip, ip.is_private());

    println!("\n=== Timestamps (u64) ===");
    let t1 = Timestamp::from_secs(1_000_000);
    let t2 = Timestamp::from_secs(1_000_005);
    println!("Duration: {:?} ns", t2.duration_since(t1));

    println!("\n=== UUID (u128) ===");
    let uuid = Uuid::from_u128(0x550e8400_e29b_41d4_a716_446655440000);
    println!("{}", uuid.to_hyphenated());

    println!("\n=== Overflow Safety ===");
    demonstrate_overflow_safety();

    println!("\n=== Bit Operations ===");
    demonstrate_bit_operations();
}
```

---

## 7. Signed Integers: i8 → i128, isize {#signed}

### Two's Complement: How Negative Numbers Are Stored

This is **the single most important concept** for signed integers. Every CPU in existence uses **Two's Complement** to represent negative numbers.

```
WHY TWO'S COMPLEMENT?
→ Addition works identically for positive and negative numbers.
→ The CPU uses ONE adder circuit for both cases.
→ No special handling needed for negative numbers.

TWO'S COMPLEMENT RULE:
  To negate a number:
  1. Flip all bits (bitwise NOT)
  2. Add 1

Example: Convert +5 to -5 in i8:
  +5: 0000 0101
  NOT: 1111 1010
  +1:  1111 1011  ← This is -5 in two's complement

VERIFICATION: -5 + 5 should = 0
  1111 1011  (-5)
+ 0000 0101  (+5)
= 0000 0000  (0) ← The overflow carry bit is discarded ✓
```

### Signed Range Formula

```
For iN (N-bit signed integer):
  MSB (bit N-1) = sign bit: 0 = positive, 1 = negative
  
  Range: -2^(N-1)  to  2^(N-1) - 1
  
  i8:   -128 to 127
  i16:  -32,768 to 32,767
  i32:  -2,147,483,648 to 2,147,483,647 (~2.1 billion)
  i64:  -9,223,372,036,854,775,808 to 9,223,372,036,854,775,807
```

### Visual: i8 Number Circle

```
        0
      /   \
   127     -128
    |         |
    64     -64
      \   /
       -1 ← Just below 0

Adding 1 to 127 (i8::MAX) WRAPS to -128.
This is the integer overflow trap!
```

### Production-Grade Signed Integer Code

```rust
// ─────────────────────────────────────────────────────────────
// FILE: signed_integers.rs
// PURPOSE: Production patterns for signed integer types
// ─────────────────────────────────────────────────────────────

// ── PATTERN 1: i8 — Temperature, Offsets ─────────────────────

/// Temperature in Celsius as i8.
/// Covers -128°C to 127°C — enough for real-world temps.
/// INSIGHT: Using i8 not i32 saves memory in temperature arrays.
///          For a 1000×1000 grid: i8 = 1MB, i32 = 4MB.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub struct TempCelsius(i8);

impl TempCelsius {
    pub const FREEZING:   TempCelsius = TempCelsius(0);
    pub const BOILING:    TempCelsius = TempCelsius(100);
    pub const BODY_TEMP:  TempCelsius = TempCelsius(37);
    pub const ABSOLUTE_ZERO_APPROX: TempCelsius = TempCelsius(-128);

    pub fn new(val: i8) -> Self { Self(val) }

    pub fn is_freezing(&self)    -> bool { self.0 <= 0 }
    pub fn is_comfortable(&self) -> bool { self.0 >= 18 && self.0 <= 24 }

    pub fn to_fahrenheit(&self) -> f32 {
        (self.0 as f32) * 9.0 / 5.0 + 32.0
    }
}

// ── PATTERN 2: i32 — The Workhorse Signed Integer ─────────────

/// Game entity position in a 2D world.
///
/// WHY i32? Worlds have negative coordinates (e.g., left/below origin).
/// i32 gives ±2.1 billion — enough for any game grid.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Position {
    pub x: i32,
    pub y: i32,
}

impl Position {
    pub const ORIGIN: Position = Position { x: 0, y: 0 };

    pub fn new(x: i32, y: i32) -> Self { Self { x, y } }

    /// Manhattan distance (no floats needed).
    /// abs() is the key operation for signed integers.
    pub fn manhattan_distance(&self, other: &Position) -> u32 {
        // abs() returns i32, cast to u32 — safe because abs >= 0
        let dx = (self.x - other.x).abs() as u32;
        let dy = (self.y - other.y).abs() as u32;
        dx + dy
    }

    /// Euclidean distance (requires float).
    pub fn euclidean_distance(&self, other: &Position) -> f64 {
        let dx = (self.x - other.x) as f64;
        let dy = (self.y - other.y) as f64;
        (dx * dx + dy * dy).sqrt()
    }

    /// Move by delta, saturating at i32 bounds (no panic).
    pub fn translate_saturating(&self, dx: i32, dy: i32) -> Position {
        Position {
            x: self.x.saturating_add(dx),
            y: self.y.saturating_add(dy),
        }
    }
}

// ── PATTERN 3: i64 — Financial Amounts in Cents ───────────────

/// Money represented as cents (i64).
///
/// EXPERT RULE: NEVER use floats for money.
/// 0.1 + 0.2 ≠ 0.3 in floating point!
///
/// Store as integer cents: $10.99 = 1099 cents
/// i64 max = 9.2 × 10^18 cents = 9.2 × 10^16 dollars
/// More than enough for any financial application.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub struct Money {
    cents: i64,        // negative = debt
    currency_code: u8, // simplified; normally a proper enum
}

impl Money {
    const CENTS_PER_DOLLAR: i64 = 100;

    pub fn from_cents(cents: i64) -> Self {
        Self { cents, currency_code: 0 }
    }

    pub fn from_dollars_and_cents(dollars: i64, cents: i64) -> Self {
        // Handle negative dollars correctly
        let sign = if dollars < 0 { -1i64 } else { 1i64 };
        Self::from_cents(dollars * Self::CENTS_PER_DOLLAR + sign * cents)
    }

    pub fn dollars(&self) -> i64 { self.cents / Self::CENTS_PER_DOLLAR }
    pub fn cents_remainder(&self) -> i64 {
        (self.cents % Self::CENTS_PER_DOLLAR).abs()
    }

    pub fn is_debt(&self)     -> bool { self.cents < 0 }
    pub fn is_positive(&self) -> bool { self.cents > 0 }

    /// Add two amounts. Returns None on overflow.
    pub fn checked_add(self, other: Money) -> Option<Money> {
        self.cents.checked_add(other.cents)
            .map(|c| Money::from_cents(c))
    }
}

impl std::fmt::Display for Money {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let sign = if self.cents < 0 { "-" } else { "" };
        write!(f, "{}${}.{:02}", sign, self.dollars().abs(), self.cents_remainder())
    }
}

// ── PATTERN 4: Signed vs Unsigned — The Subtraction Trap ──────

/// CRITICAL BUG: Unsigned subtraction can silently underflow.
/// This is a source of real-world security vulnerabilities.
pub fn demonstrate_subtraction_trap() {
    // DANGEROUS: usize subtraction
    let a: usize = 5;
    let b: usize = 10;
    // a - b would underflow in release mode! a - b = usize::MAX - 4
    // In debug mode: panic.

    // SAFE: use checked_sub
    match a.checked_sub(b) {
        Some(result) => println!("Result: {}", result),
        None         => println!("Would underflow — handle it!"),
    }

    // SAFE alternative: convert to signed before subtracting
    let diff: isize = (a as isize) - (b as isize);
    println!("Signed diff: {}", diff); // -5, correct

    // REAL-WORLD EXAMPLE: Array index calculation
    // If you have: index = current - offset
    // And offset could be > current, use isize then bounds check.
    let current: usize = 3;
    let offset:  usize = 5;
    let index = (current as isize) - (offset as isize); // -2
    if index >= 0 {
        println!("Valid index: {}", index as usize);
    } else {
        println!("Before start of array, clamping to 0");
    }
}

// ── PATTERN 5: Absolute Value and Sign Operations ─────────────

pub fn demonstrate_signed_operations() {
    let x: i32 = -42;

    println!("abs:       {}", x.abs());       // 42
    println!("signum:    {}", x.signum());     // -1 (neg) | 0 | 1 (pos)
    println!("pow(2):    {}", x.pow(2));       // 1764

    // pow can overflow! use checked version:
    println!("checked pow: {:?}", x.checked_pow(10));  // None (overflows)

    // Integer division: rounds toward zero (truncation)
    println!("7 / 2 = {}", 7i32 / 2);      // 3  (not 3.5)
    println!("-7 / 2 = {}", -7i32 / 2);    // -3 (not -4, floors to -3)

    // Remainder: same sign as DIVIDEND (unlike mathematical modulo)
    println!("7 % 3 = {}", 7i32 % 3);      //  1
    println!("-7 % 3 = {}", -7i32 % 3);    // -1 (sign of dividend!)
    println!("7 % -3 = {}", 7i32 % -3);    //  1

    // For true mathematical modulo (always non-negative):
    fn modulo(a: i32, b: i32) -> i32 {
        ((a % b) + b) % b
    }
    println!("mod(-7, 3) = {}", modulo(-7, 3)); // 2 (mathematical)
}

fn main() {
    println!("=== Signed Integer Ranges ===");
    println!("i8:  {} to {}", i8::MIN, i8::MAX);
    println!("i16: {} to {}", i16::MIN, i16::MAX);
    println!("i32: {} to {}", i32::MIN, i32::MAX);
    println!("i64: {} to {}", i64::MIN, i64::MAX);

    println!("\n=== Temperature (i8) ===");
    let t = TempCelsius::new(37);
    println!("{}°C = {:.1}°F", t.0, t.to_fahrenheit());

    println!("\n=== Position (i32) ===");
    let p1 = Position::new(-10, 20);
    let p2 = Position::new(30, -15);
    println!("Manhattan: {}", p1.manhattan_distance(&p2));
    println!("Euclidean: {:.2}", p1.euclidean_distance(&p2));

    println!("\n=== Money (i64) ===");
    let price  = Money::from_dollars_and_cents(10, 99);
    let tax    = Money::from_cents(88);
    let total  = price.checked_add(tax).expect("no overflow");
    println!("Price: {}  Tax: {}  Total: {}", price, tax, total);

    println!("\n=== Subtraction Trap ===");
    demonstrate_subtraction_trap();

    println!("\n=== Signed Operations ===");
    demonstrate_signed_operations();
}
```

---

## 8. Floating Point: f32 & f64 {#floats}

### IEEE 754: The Standard

Both `f32` and `f64` follow the **IEEE 754** floating-point standard. This is NOT approximation — it is a precise specification of how real numbers are encoded in binary.

```
IEEE 754 SINGLE PRECISION (f32 — 32 bits):
┌────┬──────────┬────────────────────────┐
│ S  │ Exponent │       Mantissa          │
│ 1  │   8 bits │       23 bits           │
└────┴──────────┴────────────────────────┘

IEEE 754 DOUBLE PRECISION (f64 — 64 bits):
┌────┬──────────┬─────────────────────────────────────────────┐
│ S  │ Exponent │                  Mantissa                    │
│ 1  │  11 bits │                  52 bits                     │
└────┴──────────┴─────────────────────────────────────────────┘

S = Sign bit (0 = positive, 1 = negative)

VALUE = (-1)^S × 1.Mantissa × 2^(Exponent - Bias)
                 └────────┘   └──────────────────┘
                 implied 1     the actual exponent
```

### Special Values

```
Floating point has FOUR special values:

  +Infinity:  Sign=0, Exp=all 1s, Mantissa=0
  -Infinity:  Sign=1, Exp=all 1s, Mantissa=0
  NaN:        Exp=all 1s, Mantissa≠0  (not-a-number)
  ±0:         Two zeros! +0.0 and -0.0

In Rust:
  f64::INFINITY     =  ∞
  f64::NEG_INFINITY = -∞
  f64::NAN          = NaN
  
  1.0 / 0.0  = Infinity  (no panic!)
  0.0 / 0.0  = NaN       (no panic!)
  
  NaN ≠ NaN  ← CRITICAL: NaN is not equal to itself!
  f64::is_nan(x)  is the correct way to check.
```

### The Precision Problem

```
WHY 0.1 + 0.2 ≠ 0.3:

0.1 in binary: 0.0001100110011001100... (infinite repeating)
Cannot be represented exactly in finite bits.
So 0.1 is stored as the NEAREST representable value.

0.1 actual stored: 0.1000000000000000055511151231257827021181583404541015625
0.2 actual stored: 0.200000000000000011102230246251565404236316680908203125
Sum:               0.300000000000000044408920985006261616945266723632812500
0.3 actual stored: 0.29999999999999998889776975374843459576368331909179687500
These differ at the 17th decimal place → 0.1 + 0.2 ≠ 0.3 exactly
```

### Production-Grade Float Code

```rust
// ─────────────────────────────────────────────────────────────
// FILE: floats_guide.rs
// PURPOSE: Production-grade floating point patterns
// ─────────────────────────────────────────────────────────────

use std::mem;

// ── LAYOUT VERIFICATION ───────────────────────────────────────
#[test]
fn verify_float_layout() {
    assert_eq!(mem::size_of::<f32>(), 4);
    assert_eq!(mem::size_of::<f64>(), 8);
    assert_eq!(mem::align_of::<f32>(), 4);
    assert_eq!(mem::align_of::<f64>(), 8);
}

// ── FLOAT CLASSIFICATION ──────────────────────────────────────

pub fn classify_float(x: f64) {
    use std::num::FpCategory;
    match x.classify() {
        FpCategory::Normal    => println!("{} → Normal",    x),
        FpCategory::Subnormal => println!("{} → Subnormal", x), // tiny
        FpCategory::Zero      => println!("{} → Zero",      x),
        FpCategory::Infinite  => println!("{} → Infinite",  x),
        FpCategory::Nan       => println!("{} → NaN",       x),
    }
}

// ── FLOAT COMPARISON — The Critical Rule ──────────────────────

/// NEVER compare floats with ==.
/// ALWAYS use epsilon-based comparison.
///
/// EXPERT PATTERN: The epsilon tolerance depends on your domain.
/// Machine epsilon for f64: ~2.2 × 10^-16
pub fn float_nearly_equal(a: f64, b: f64) -> bool {
    const EPSILON: f64 = 1e-9;
    (a - b).abs() < EPSILON
}

/// Relative epsilon comparison — better for large numbers.
/// Absolute epsilon fails for large values:
///   1_000_000.0 vs 1_000_000.001 differ by 0.001 (> 1e-9)
///   But relatively they're very close.
pub fn float_relative_equal(a: f64, b: f64) -> bool {
    const REL_EPSILON: f64 = 1e-9;
    const ABS_EPSILON: f64 = f64::EPSILON;  // ~2.22e-16

    // Handle the case where both are zero or near-zero
    let diff = (a - b).abs();
    if diff <= ABS_EPSILON {
        return true;
    }

    let max_magnitude = a.abs().max(b.abs());
    diff <= REL_EPSILON * max_magnitude
}

// ── PATTERN 1: Physics Simulation (f32 vs f64 choice) ─────────

/// Physics vector using f64 for precision.
///
/// WHEN TO USE f32 vs f64:
///   f32: Graphics, game positions, ML weights, when saving memory
///        (half the bytes → twice the cache efficiency for arrays)
///   f64: Scientific computing, financial calculations, physics sims
///        where precision matters over long simulations
#[derive(Debug, Clone, Copy)]
pub struct Vec3 {
    pub x: f64,
    pub y: f64,
    pub z: f64,
}

impl Vec3 {
    pub const ZERO: Vec3 = Vec3 { x: 0.0, y: 0.0, z: 0.0 };

    pub fn new(x: f64, y: f64, z: f64) -> Self { Self { x, y, z } }

    pub fn dot(&self, other: &Vec3) -> f64 {
        self.x * other.x + self.y * other.y + self.z * other.z
    }

    pub fn cross(&self, other: &Vec3) -> Vec3 {
        Vec3 {
            x: self.y * other.z - self.z * other.y,
            y: self.z * other.x - self.x * other.z,
            z: self.x * other.y - self.y * other.x,
        }
    }

    pub fn length_squared(&self) -> f64 {
        self.dot(self)  // avoids sqrt for comparison purposes
    }

    pub fn length(&self) -> f64 {
        self.length_squared().sqrt()
    }

    /// Normalize to unit vector (length = 1).
    /// Returns None if the vector is zero-length (avoid division by zero).
    pub fn normalize(&self) -> Option<Vec3> {
        let len = self.length();
        if len < f64::EPSILON {
            return None;
        }
        Some(Vec3 {
            x: self.x / len,
            y: self.y / len,
            z: self.z / len,
        })
    }

    pub fn scale(&self, factor: f64) -> Vec3 {
        Vec3 { x: self.x * factor, y: self.y * factor, z: self.z * factor }
    }
}

// ── PATTERN 2: Statistics (f64 for numerical stability) ────────

/// Compute mean and variance using Welford's online algorithm.
///
/// EXPERT INSIGHT: Welford's algorithm is numerically stable.
/// Naive: sum all then divide — accumulates floating point error.
/// Welford: update incrementally — far more stable.
pub struct RunningStats {
    count: u64,
    mean:  f64,
    m2:    f64,  // sum of squared deviations
}

impl RunningStats {
    pub fn new() -> Self {
        Self { count: 0, mean: 0.0, m2: 0.0 }
    }

    /// Update with a new value (online/streaming).
    pub fn update(&mut self, x: f64) {
        self.count += 1;
        let delta  = x - self.mean;
        self.mean += delta / self.count as f64;
        let delta2 = x - self.mean;
        self.m2   += delta * delta2;
    }

    pub fn mean(&self) -> Option<f64> {
        if self.count == 0 { None } else { Some(self.mean) }
    }

    /// Population variance
    pub fn variance(&self) -> Option<f64> {
        if self.count < 2 { None }
        else { Some(self.m2 / self.count as f64) }
    }

    /// Sample standard deviation
    pub fn std_dev(&self) -> Option<f64> {
        if self.count < 2 { None }
        else { Some((self.m2 / (self.count - 1) as f64).sqrt()) }
    }
}

// ── PATTERN 3: f32 Bit Tricks ─────────────────────────────────

/// Inspect the raw bits of a float.
///
/// EXPERT KNOWLEDGE: The fast inverse square root trick
/// (famous from Quake III) exploits float bit layout.
pub fn inspect_float_bits(x: f32) {
    let bits: u32 = x.to_bits(); // f32 → u32, same bit pattern
    let sign     = bits >> 31;
    let exponent = (bits >> 23) & 0xFF;
    let mantissa = bits & 0x7FFFFF;

    println!("f32 value:  {}", x);
    println!("Bits:       {:032b}", bits);
    println!("Sign:       {}", sign);
    println!("Exponent:   {} (biased), {} (actual)",
             exponent, exponent as i32 - 127);
    println!("Mantissa:   {:023b}", mantissa);
}

/// Fast approximation of 1/sqrt(x) using bit manipulation.
/// Historical: Used in Quake III Arena for lighting calculations.
/// Pedagogical value: Shows how float structure can be exploited.
pub fn fast_inv_sqrt(x: f32) -> f32 {
    let i = x.to_bits();
    let i = 0x5f3759df_u32.wrapping_sub(i >> 1);  // magic number
    let y = f32::from_bits(i);
    // One Newton-Raphson iteration for refinement
    y * (1.5 - (x * 0.5 * y * y))
}

fn main() {
    println!("=== Float Ranges ===");
    println!("f32: {} to {}", f32::MIN, f32::MAX);
    println!("f32 epsilon: {}", f32::EPSILON);
    println!("f64: {} to {}", f64::MIN, f64::MAX);
    println!("f64 epsilon: {}", f64::EPSILON);

    println!("\n=== Special Values ===");
    classify_float(1.0);
    classify_float(f64::INFINITY);
    classify_float(f64::NAN);
    classify_float(0.0);

    println!("\n=== The 0.1 + 0.2 Problem ===");
    let a = 0.1_f64;
    let b = 0.2_f64;
    let c = 0.3_f64;
    println!("0.1 + 0.2 == 0.3 : {}", a + b == c);          // false!
    println!("nearly equal:      {}", float_nearly_equal(a + b, c)); // true

    println!("\n=== Physics Vec3 ===");
    let v1 = Vec3::new(1.0, 0.0, 0.0);
    let v2 = Vec3::new(0.0, 1.0, 0.0);
    let cross = v1.cross(&v2);
    println!("i × j = {:?}", cross);  // (0, 0, 1)

    println!("\n=== Running Statistics ===");
    let mut stats = RunningStats::new();
    for &val in &[2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0] {
        stats.update(val);
    }
    println!("Mean: {:?}", stats.mean());
    println!("StdDev: {:?}", stats.std_dev());

    println!("\n=== Float Bit Inspection ===");
    inspect_float_bits(1.0);
    inspect_float_bits(-0.5);

    println!("\n=== Fast Inverse Square Root ===");
    let x = 100.0_f32;
    println!("1/sqrt(100) exact: {}", 1.0_f32 / x.sqrt());
    println!("fast approx:       {}", fast_inv_sqrt(x));
}
```

---

## 9. Type Casting & Conversions {#casting}

### The Conversion Hierarchy

```
RUST CONVERSION METHODS (from safest to most dangerous):

1. From/Into traits  → Infallible, zero-cost when possible
2. TryFrom/TryInto  → Fallible, returns Result<T, E>
3. as casting       → C-style, silently truncates — use with care
4. transmute        → Raw bit reinterpretation — unsafe, dangerous

as CASTING RULES:
  Integer → Integer:
    Narrowing (u32 → u8):   TRUNCATES (takes lowest N bits)
    Widening  (u8 → u32):   Zero-extends (unsigned) or sign-extends (signed)
  
  Float → Integer:          Rounds toward zero, saturates at bounds (since Rust 1.45)
  Integer → Float:          Nearest representable value
  bool → Integer:           false=0, true=1
  char → u32:               Unicode code point
  u8 → char:                Valid (u8 is always valid ASCII/Latin-1)
  u32 → char:               UNSAFE (not all u32 are valid Unicode)
```

### Production Conversion Code

```rust
// ─────────────────────────────────────────────────────────────
// FILE: conversions.rs
// PURPOSE: Correct and safe type conversions in Rust
// ─────────────────────────────────────────────────────────────

use std::convert::TryFrom;

// ── PATTERN 1: as Casting — What Actually Happens ─────────────

pub fn demonstrate_as_casting() {
    // WIDENING (safe): small → large
    let small: u8  = 200;
    let wide:  u32 = small as u32;     // 200 → 200, zero-extended
    let wide2: i32 = small as i32;     // 200 → 200 (no sign issue)
    println!("u8 200 as u32: {}", wide);
    println!("u8 200 as i32: {}", wide2);

    // NARROWING (truncates!): large → small
    let big:  u32 = 300;  // binary: 0000_0001_0010_1100
    let tiny: u8  = big as u8;  // keeps low 8 bits: 0010_1100 = 44
    println!("u32 300 as u8: {} (300 % 256 = {})", tiny, 300 % 256);

    // SIGNED ↔ UNSIGNED reinterpretation
    let signed:   i8 = -1;            // bits: 1111_1111
    let unsigned: u8 = signed as u8;  // same bits: 255
    println!("i8 -1 as u8: {}", unsigned);  // 255

    // FLOAT → INTEGER: rounds toward zero, saturates at bounds
    let f: f32 = 300.9;
    let i: u8  = f as u8;   // Since Rust 1.45: saturates to 255
    println!("f32 300.9 as u8: {}", i);  // 255 (not 44, not UB)

    let neg: f32 = -1.9;
    let u: u8    = neg as u8;  // saturates to 0
    println!("f32 -1.9 as u8: {}", u);  // 0

    let nan: f32 = f32::NAN;
    let n: u8    = nan as u8;  // 0 (defined behavior since 1.45)
    println!("f32 NAN as u8: {}", n);  // 0
}

// ── PATTERN 2: From/Into — Infallible Conversions ─────────────

/// From<T> means: "I can always be created from T with no failure."
/// These are implemented for widening integer conversions.
pub fn demonstrate_from_into() {
    // u8 → u32: always safe (u8 range ⊆ u32 range)
    let byte: u8   = 200;
    let word: u32  = u32::from(byte);   // explicit
    let word2: u32 = byte.into();       // implicit, same thing

    // u8 → f64: always representable
    let float: f64 = f64::from(byte);

    // String from various types
    let s: String = String::from("hello");  // &str → String

    println!("{} {} {}", word, word2, float);

    // NARROWING is NOT implemented via From:
    // u32::from(word) for u8 doesn't exist — it would be lossy!
    // You'd use u8::try_from(word) instead.
}

// ── PATTERN 3: TryFrom/TryInto — Fallible Conversions ─────────

#[derive(Debug)]
pub struct SmallIndex(u8);  // indices 0..=99

#[derive(Debug)]
pub struct IndexOutOfRange(u32);

impl TryFrom<u32> for SmallIndex {
    type Error = IndexOutOfRange;

    fn try_from(value: u32) -> Result<Self, Self::Error> {
        if value <= 99 {
            Ok(SmallIndex(value as u8))
        } else {
            Err(IndexOutOfRange(value))
        }
    }
}

pub fn demonstrate_try_from() {
    // Safe conversion with proper error handling
    let valid:   Result<SmallIndex, _> = SmallIndex::try_from(50_u32);
    let invalid: Result<SmallIndex, _> = SmallIndex::try_from(200_u32);

    println!("{:?}", valid);    // Ok(SmallIndex(50))
    println!("{:?}", invalid);  // Err(IndexOutOfRange(200))

    // Standard library: u8::try_from(u32)
    let big: u32 = 300;
    match u8::try_from(big) {
        Ok(small) => println!("Fits: {}", small),
        Err(e)    => println!("Out of range: {}", e),
    }
}

fn main() {
    println!("=== as Casting ===");
    demonstrate_as_casting();

    println!("\n=== From/Into ===");
    demonstrate_from_into();

    println!("\n=== TryFrom/TryInto ===");
    demonstrate_try_from();
}
```

---

## 10. Hardware Reality & Cache Behavior {#hardware}

### The Memory Hierarchy (Why Type Size Matters)

```
┌────────────────────────────────────────────────────────────────┐
│  CPU MEMORY HIERARCHY — Latency at Each Level                   │
│                                                                  │
│  ┌──────────────────┐                                           │
│  │  CPU Registers   │  ~0 cycles   64-bit, 16 general purpose  │
│  ├──────────────────┤                                           │
│  │  L1 Cache        │  ~4 cycles   32–64 KB per core           │
│  ├──────────────────┤  64-byte CACHE LINES                      │
│  │  L2 Cache        │  ~12 cycles  256 KB per core             │
│  ├──────────────────┤                                           │
│  │  L3 Cache        │  ~40 cycles  8–32 MB shared              │
│  ├──────────────────┤                                           │
│  │  Main RAM        │  ~100 cycles 8–64 GB                     │
│  ├──────────────────┤                                           │
│  │  SSD             │  ~10,000 cycles                           │
│  └──────────────────┘                                           │
│                                                                  │
│  KEY INSIGHT: A cache miss costs ~100× more than a hit.         │
│  Smaller types → more data fits in cache → fewer misses.        │
└────────────────────────────────────────────────────────────────┘
```

### Cache Lines: The 64-Byte Atomic Unit

```
Modern CPUs don't load individual bytes — they load 64-byte cache lines.

If you have an array of u8 (1 byte each):
  One cache line holds 64 values at once.
  Iterating is CACHE FRIENDLY — prefetcher works well.

If you have an array of u64 (8 bytes each):
  One cache line holds only 8 values at once.
  8× more cache pressure for the same count.

PRACTICAL EXAMPLE:
  Counting bytes (u8[]) vs counting longs (u64[]):
  For 1 million elements:
    u8[]:  1MB → fits in L2 cache
    u64[]: 8MB → doesn't fit → 10× slower due to cache misses
```

### Type Choice Impact on Performance

```rust
// ─────────────────────────────────────────────────────────────
// FILE: cache_behavior.rs
// PURPOSE: Demonstrates how type choice affects cache performance
// ─────────────────────────────────────────────────────────────

/// DEMONSTRATION: Sum 10 million elements.
/// u8 array: 10MB — fits in L3 cache.
/// u64 array: 80MB — exceeds L3 cache.
/// Result: u8 sum is 3–5× FASTER due to cache efficiency alone.
pub fn cache_size_demo() {
    use std::time::Instant;
    const COUNT: usize = 10_000_000;

    // u8 array: 10MB
    let u8_data:  Vec<u8>  = (0..COUNT).map(|i| (i % 256) as u8).collect();
    let u64_data: Vec<u64> = (0..COUNT).map(|i| i as u64).collect();

    let t0 = Instant::now();
    let sum_u8: u64 = u8_data.iter().map(|&x| x as u64).sum();
    let t1 = Instant::now();

    let t2 = Instant::now();
    let sum_u64: u64 = u64_data.iter().sum();
    let t3 = Instant::now();

    println!("u8  sum: {}  time: {:?}", sum_u8,  t1 - t0);
    println!("u64 sum: {}  time: {:?}", sum_u64, t3 - t2);
    // Typical: u8 is ~3-5x faster
}

/// Struct of Arrays (SoA) vs Array of Structs (AoS)
/// This is one of the most important cache optimization patterns.

// AoS: Array of Structs — common but cache-unfriendly for partial access
#[derive(Clone)]
struct ParticleAoS {
    x:      f32,   // position
    y:      f32,
    z:      f32,
    mass:   f32,   // physical properties
    charge: f32,
    active: bool,  // boolean flag
}

// SoA: Struct of Arrays — cache-friendly when processing one field at a time
struct ParticlesSoA {
    x:      Vec<f32>,
    y:      Vec<f32>,
    z:      Vec<f32>,
    mass:   Vec<f32>,
    charge: Vec<f32>,
    active: Vec<bool>,
}

impl ParticlesSoA {
    fn new(count: usize) -> Self {
        Self {
            x:      vec![0.0; count],
            y:      vec![0.0; count],
            z:      vec![0.0; count],
            mass:   vec![1.0; count],
            charge: vec![0.0; count],
            active: vec![true; count],
        }
    }

    /// Update only positions — reads only x, y, z arrays.
    /// Cache behavior: 3 contiguous arrays → excellent spatial locality.
    /// Compare with AoS: position reads skip over mass, charge, active.
    fn update_positions(&mut self, dt: f32) {
        for i in 0..self.x.len() {
            if self.active[i] {
                self.x[i] += self.mass[i] * dt;
                self.y[i] += self.mass[i] * dt;
                self.z[i] += self.mass[i] * dt;
            }
        }
    }
}
```

---

## 11. Real-World Implementations {#realworld}

### Complete System: A Binary Protocol Parser

```rust
// ─────────────────────────────────────────────────────────────
// FILE: protocol_parser.rs
// PURPOSE: Real-world use of ALL primitive types in a network
//          binary protocol parser (like HTTP/2 frame parsing)
// ─────────────────────────────────────────────────────────────

/// A simplified binary frame format:
///
/// ┌────────────────────────────────────────────────────────┐
/// │  Byte 0:     Frame type (u8)                           │
/// │  Byte 1:     Flags (u8, packed booleans)               │
/// │  Bytes 2-3:  Stream ID (u16, big-endian)               │
/// │  Bytes 4-7:  Payload length (u32, big-endian)          │
/// │  Bytes 8-15: Timestamp nanos (u64, big-endian)         │
/// │  Byte  16:   ASCII character marker (u8 → char)        │
/// │  Bytes 17+:  UTF-8 payload (&str)                      │
/// └────────────────────────────────────────────────────────┘

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]  // stored as u8 in the wire format
pub enum FrameType {
    Data        = 0x00,
    Headers     = 0x01,
    Priority    = 0x02,
    RstStream   = 0x03,
    Settings    = 0x04,
    Ping        = 0x08,
    GoAway      = 0x07,
}

impl FrameType {
    pub fn from_u8(byte: u8) -> Option<Self> {
        match byte {
            0x00 => Some(Self::Data),
            0x01 => Some(Self::Headers),
            0x02 => Some(Self::Priority),
            0x03 => Some(Self::RstStream),
            0x04 => Some(Self::Settings),
            0x08 => Some(Self::Ping),
            0x07 => Some(Self::GoAway),
            _    => None,
        }
    }
}

/// Frame flags — packed booleans in a u8.
#[derive(Debug, Clone, Copy)]
pub struct FrameFlags(u8);

impl FrameFlags {
    const END_STREAM:  u8 = 0x01;
    const END_HEADERS: u8 = 0x04;
    const PADDED:      u8 = 0x08;
    const PRIORITY:    u8 = 0x20;

    pub fn end_stream(&self)  -> bool { self.0 & Self::END_STREAM  != 0 }
    pub fn end_headers(&self) -> bool { self.0 & Self::END_HEADERS != 0 }
    pub fn padded(&self)      -> bool { self.0 & Self::PADDED      != 0 }
    pub fn has_priority(&self)-> bool { self.0 & Self::PRIORITY    != 0 }
}

/// A fully parsed frame header.
#[derive(Debug)]
pub struct FrameHeader {
    pub frame_type:     FrameType,
    pub flags:          FrameFlags,
    pub stream_id:      u16,
    pub payload_len:    u32,
    pub timestamp_ns:   u64,
    pub marker:         char,
}

/// Parse errors with full context.
#[derive(Debug)]
pub enum ParseError {
    TooShort     { needed: usize, got: usize },
    UnknownType  { byte: u8 },
    InvalidUtf8  { at_byte: usize },
    InvalidChar  { code_point: u32 },
}

impl std::fmt::Display for ParseError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ParseError::TooShort { needed, got } =>
                write!(f, "frame too short: needed {} bytes, got {}", needed, got),
            ParseError::UnknownType { byte } =>
                write!(f, "unknown frame type: 0x{:02X}", byte),
            ParseError::InvalidUtf8 { at_byte } =>
                write!(f, "invalid UTF-8 at byte {}", at_byte),
            ParseError::InvalidChar { code_point } =>
                write!(f, "invalid char code point: U+{:04X}", code_point),
        }
    }
}

/// Reader that tracks position and provides typed reads.
struct ByteReader<'a> {
    data: &'a [u8],
    pos:  usize,
}

impl<'a> ByteReader<'a> {
    fn new(data: &'a [u8]) -> Self { Self { data, pos: 0 } }

    fn remaining(&self) -> usize { self.data.len() - self.pos }

    fn read_u8(&mut self) -> Result<u8, ParseError> {
        if self.remaining() < 1 {
            return Err(ParseError::TooShort { needed: 1, got: self.remaining() });
        }
        let val = self.data[self.pos];
        self.pos += 1;
        Ok(val)
    }

    // u16 big-endian: first byte is high, second byte is low
    fn read_u16_be(&mut self) -> Result<u16, ParseError> {
        if self.remaining() < 2 {
            return Err(ParseError::TooShort { needed: 2, got: self.remaining() });
        }
        let val = u16::from_be_bytes([self.data[self.pos], self.data[self.pos + 1]]);
        self.pos += 2;
        Ok(val)
    }

    fn read_u32_be(&mut self) -> Result<u32, ParseError> {
        if self.remaining() < 4 {
            return Err(ParseError::TooShort { needed: 4, got: self.remaining() });
        }
        let bytes = [
            self.data[self.pos],     self.data[self.pos + 1],
            self.data[self.pos + 2], self.data[self.pos + 3],
        ];
        self.pos += 4;
        Ok(u32::from_be_bytes(bytes))
    }

    fn read_u64_be(&mut self) -> Result<u64, ParseError> {
        if self.remaining() < 8 {
            return Err(ParseError::TooShort { needed: 8, got: self.remaining() });
        }
        let mut bytes = [0u8; 8];
        bytes.copy_from_slice(&self.data[self.pos..self.pos + 8]);
        self.pos += 8;
        Ok(u64::from_be_bytes(bytes))
    }

    fn read_char(&mut self) -> Result<char, ParseError> {
        let byte = self.read_u8()?;
        // Treat as ASCII char (must be valid ASCII)
        if byte.is_ascii() {
            Ok(byte as char)
        } else {
            Err(ParseError::InvalidChar { code_point: byte as u32 })
        }
    }

    fn read_utf8_str(&mut self, len: usize) -> Result<&'a str, ParseError> {
        if self.remaining() < len {
            return Err(ParseError::TooShort { needed: len, got: self.remaining() });
        }
        let slice = &self.data[self.pos..self.pos + len];
        self.pos += len;
        std::str::from_utf8(slice).map_err(|e| {
            ParseError::InvalidUtf8 { at_byte: e.valid_up_to() }
        })
    }
}

/// Parse a complete frame from raw bytes.
///
/// This demonstrates ALL primitive types working together:
/// u8 for type/flags, u16 for stream ID, u32 for length,
/// u64 for timestamp, char for marker, &str for payload.
pub fn parse_frame(data: &[u8]) -> Result<(FrameHeader, &str), ParseError> {
    const HEADER_SIZE: usize = 17;

    if data.len() < HEADER_SIZE {
        return Err(ParseError::TooShort {
            needed: HEADER_SIZE,
            got:    data.len(),
        });
    }

    let mut reader = ByteReader::new(data);

    let type_byte = reader.read_u8()?;
    let frame_type = FrameType::from_u8(type_byte)
        .ok_or(ParseError::UnknownType { byte: type_byte })?;

    let flags_byte = reader.read_u8()?;
    let flags = FrameFlags(flags_byte);

    let stream_id   = reader.read_u16_be()?;
    let payload_len = reader.read_u32_be()?;
    let timestamp   = reader.read_u64_be()?;
    let marker      = reader.read_char()?;
    let payload     = reader.read_utf8_str(payload_len as usize)?;

    let header = FrameHeader {
        frame_type,
        flags,
        stream_id,
        payload_len,
        timestamp_ns: timestamp,
        marker,
    };

    Ok((header, payload))
}

fn main() {
    // Construct a test frame in memory
    // Type=0x01 (Headers), Flags=0x05 (END_STREAM|END_HEADERS),
    // StreamID=1, PayloadLen=5, Timestamp=1234567890, Marker='H', Payload="hello"
    let mut frame = Vec::<u8>::new();
    frame.push(0x01_u8);                                    // frame type
    frame.push(0x05_u8);                                    // flags
    frame.extend_from_slice(&1_u16.to_be_bytes());          // stream ID
    frame.extend_from_slice(&5_u32.to_be_bytes());          // payload len
    frame.extend_from_slice(&1_234_567_890_u64.to_be_bytes()); // timestamp
    frame.push(b'H');                                       // marker char
    frame.extend_from_slice(b"hello");                      // payload

    match parse_frame(&frame) {
        Ok((header, payload)) => {
            println!("Frame type:  {:?}", header.frame_type);
            println!("End-stream:  {}", header.flags.end_stream());
            println!("End-headers: {}", header.flags.end_headers());
            println!("Stream ID:   {}", header.stream_id);
            println!("Payload len: {}", header.payload_len);
            println!("Timestamp:   {} ns", header.timestamp_ns);
            println!("Marker:      '{}'", header.marker);
            println!("Payload:     \"{}\"", payload);
        }
        Err(e) => eprintln!("Parse error: {}", e),
    }
}
```

---

## Quick Reference: Choosing the Right Type

```
┌─────────────────────────────────────────────────────────────────────┐
│  TYPE SELECTION DECISION TREE                                        │
│                                                                      │
│  Is it true/false?           → bool                                 │
│  Is it a Unicode character?  → char                                 │
│  Is it text?                 → &str (read) or String (owned)        │
│                                                                      │
│  Is it a count/index/size?   → usize                                │
│  Is it a byte/pixel/octet?   → u8                                   │
│  Is it a port number?        → u16                                  │
│  Is it an ID, IPv4 addr?     → u32                                  │
│  Is it a timestamp/hash?     → u64                                  │
│  Is it a UUID/crypto hash?   → u128                                 │
│                                                                      │
│  Can it be negative?                                                 │
│    Small offset/delta?       → i8 or i16                            │
│    General number?           → i32                                  │
│    Money/large count?        → i64                                  │
│    Astronomical?             → i128                                 │
│    Memory offset?            → isize                                │
│                                                                      │
│  Is it a measurement?                                                │
│    GPU/ML/games (fast)?      → f32                                  │
│    Science/finance (precise)?→ f64                                  │
│                                                                      │
│  DEFAULT CHOICES when unsure:                                        │
│    Integer:  i32  (Rust's default, most CPU-natural)                │
│    Float:    f64  (Rust's default, more precision)                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Cognitive Synthesis: The Expert Mental Model

```
When you see a type, your expert brain should instantly ask:

1. HOW BIG?    → Size in bytes → cache line impact
2. HOW WIDE?   → Value range → what can overflow?
3. HOW VALID?  → bool: only 0/1. char: only USV. float: NaN/Inf exist
4. HOW ALIGNED?→ Determines struct packing and SIMD eligibility
5. HOW NATIVE? → u32/i32 = register-native. u8/u16 = needs extend
6. HOW SIGNED? → Unsigned: bitops. Signed: negative numbers.

Master these six questions for every type, and you will
develop the instinct of a systems programmer.
```

---

*"The expert knows not just what the types are, but what they cost — in bytes, in cycles, in cognitive load. Every type choice is a silent contract with the hardware."*

2,409 lines of deep, structured content — your complete primitives reference. Here's the architecture of what's inside:

**The Thread Running Through Everything**

Every type is explained through the same six-question expert lens: *How big? How wide? How valid? How aligned? How native? How signed?* — these questions become instinct with deliberate repetition.

**What Makes This Guide Different**

Rather than just listing types, each section reveals the *why behind the why*:

- `bool` — You'll see why `&&` and `&` are fundamentally different (pipeline flushing vs. side effects), and how `bool as usize` enables branchless counting — a technique the compiler can SIMD-vectorize to process 32 booleans per CPU cycle.

- `char` — The critical distinction that 'ß'.to_uppercase() → "SS" (two characters) is not a bug — it's correct Unicode. This will save you from a real class of production bugs.

- `str / &str` — The fat pointer model (ptr + len = 16 bytes) and *why* `&str[1..2]` can panic on `"héllo"` — because indices are **byte** positions, never char positions.

- `u8 → u128 / usize` — Each type justified by a real domain: IPv4 = u32 (bit-packed), port numbers = u16, UUIDs = u128, timestamps = u64. You learn the *constraint thinking*, not memorization.

- Signed integers — Two's complement internalized visually, plus the **subtraction underflow trap** (a real CVE source) and why `%` in Rust differs from mathematical modulo.

- Floats — IEEE 754 bit layout, *why* 0.1 + 0.2 ≠ 0.3 precisely, Welford's numerically-stable algorithm, and the legendary fast inverse square root as a bit-manipulation lesson.

**The Capstone** is a production binary protocol parser that weaves every single primitive type into one cohesive, production-grade system — the same pattern used in HTTP/2, MessagePack, and QUIC frame parsing.