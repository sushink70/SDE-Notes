# Bits & Bytes: A Complete Foundational Guide

---

## 1. The Atom of Information: The Bit

A **bit** (binary digit) is the smallest unit of information. It exists in one of two states: `0` or `1`. This maps directly to physical reality — voltage high/low, magnetic polarity, light/dark.

Everything your computer does — arithmetic, memory access, networking, rendering — reduces to manipulating sequences of bits. Understanding this layer gives you mental X-ray vision into how machines actually think.

**Why binary?** Not because it's natural to humans, but because it's *noise-resistant*. Distinguishing two states (0/1) is far more reliable than distinguishing ten (0–9). This is Shannon's insight from information theory.

---

## 2. Groupings: Nibble, Byte, Word

| Unit | Bits | Values |
|------|------|--------|
| Bit | 1 | 0–1 |
| Nibble | 4 | 0–15 |
| Byte | 8 | 0–255 |
| Word | 16/32/64* | depends on architecture |

*"Word" is architecture-dependent — on modern 64-bit systems, a word is 64 bits.*

A **byte** (8 bits) became the standard atomic unit of addressable memory. Every memory address points to one byte. This is why `sizeof(char) == 1` in C always — not because chars are small, but because byte is the unit.

---

## 3. Number Systems

### Binary (Base-2)
Each position is a power of 2:

```
1 0 1 1 0 1
│ │ │ │ │ └── 2⁰ = 1
│ │ │ │ └──── 2¹ = 2
│ │ │ └────── 2² = 4
│ │ └──────── 2³ = 8  ← 0, so contributes 0
│ └────────── 2⁴ = 16 ← 0, so contributes 0
└──────────── 2⁵ = 32

101101₂ = 32 + 8 + 4 + 1 = 45₁₀
```

### Hexadecimal (Base-16)
Each hex digit = 4 bits (one nibble). This is why hex is so useful — it compresses binary into readable form.

```
Binary:  1010 1111 0011 1100
Hex:        A    F    3    C   → 0xAF3C
```

| Hex | Binary | Decimal |
|-----|--------|---------|
| 0 | 0000 | 0 |
| 1 | 0001 | 1 |
| ... | ... | ... |
| A | 1010 | 10 |
| B | 1011 | 11 |
| C | 1100 | 12 |
| D | 1101 | 13 |
| E | 1110 | 14 |
| F | 1111 | 15 |

**Mental model:** When you see `0xFF`, immediately think `1111_1111` = 255. When you see `0x0F`, think `0000_1111` = lower nibble mask.

---

## 4. Integer Representations

### Unsigned Integers
Straightforward binary. An `n`-bit unsigned integer represents `[0, 2ⁿ - 1]`.

```
u8:  0 to 255
u16: 0 to 65,535
u32: 0 to 4,294,967,295
u64: 0 to 18,446,744,073,709,551,615
```

### Sign-Magnitude (historical, rarely used)
MSB = sign bit (0 = positive, 1 = negative). Problem: two representations of zero (`+0` and `-0`). Arithmetic is complicated.

### One's Complement (historical)
Negate by flipping all bits. Still has two zeros. Used in old checksums (TCP/IP checksum uses ones' complement addition).

### Two's Complement (universal modern standard)
Negate by: flip all bits, then add 1.

```
 5 in 8-bit: 0000_0101
-5 in 8-bit: 1111_1010 + 1 = 1111_1011
```

**Why two's complement is genius:**
- Only one representation of zero
- Addition works identically for signed and unsigned — the hardware doesn't need to know
- The MSB has weight `-2^(n-1)` instead of `+2^(n-1)`

```
i8 range breakdown:
MSB weight = -128
Remaining 7 bits = 0 to 127
Range = -128 to +127
```

**Overflow behavior in Rust vs Go:**

```rust
// Rust — panics in debug, wraps in release
let x: i8 = 127i8.wrapping_add(1); // -128, explicit wrapping

// Go — always wraps silently (be careful!)
var x int8 = 127
x++ // x is now -128, no panic
```

---

## 5. Bitwise Operators — The Core Toolkit

These operate bit-by-bit on integers. Mastering them is essential for DSA — they appear in everything from graph algorithms to DP optimizations.

### AND `&`
Both bits must be 1.
```
  0110 1010
& 0011 1100
-----------
  0010 1000
```
**Use:** Masking — extract specific bits.

### OR `|`
At least one bit must be 1.
```
  0110 1010
| 0011 1100
-----------
  0111 1110
```
**Use:** Setting specific bits.

### XOR `^`
Bits must differ.
```
  0110 1010
^ 0011 1100
-----------
  0101 0110
```
**Use:** Toggling bits, finding unique elements, swap without temp variable.

### NOT `~` (bitwise complement)
Flip every bit.
```
~ 0110 1010
-----------
  1001 0101
```

### Left Shift `<<`
Shift bits left, fill with zeros on right. Equivalent to multiplying by `2^n`.
```
0000_0011 << 2 = 0000_1100   (3 → 12)
```

### Right Shift `>>`
Two flavors:
- **Logical right shift:** Fill with 0s (for unsigned). Always `>>` in Rust for unsigned types.
- **Arithmetic right shift:** Fill with sign bit (for signed). Preserves sign — divides by `2^n`.

```rust
let x: i8 = -8i8;      // 1111_1000
let y = x >> 2;         // 1111_1110 = -2  (arithmetic, sign-extended)

let a: u8 = 200u8;     // 1100_1000
let b = a >> 2;         // 0011_0010 = 50  (logical, zero-filled)
```

In Go, the shift type is determined by the variable type — signed integers use arithmetic shift right, unsigned use logical.

---

## 6. Essential Bit Manipulation Patterns

These are the bread and butter of competitive programming and systems design. Internalize them as reflexes.

### Check if bit `i` is set
```rust
fn is_set(n: u32, i: u32) -> bool {
    (n >> i) & 1 == 1
    // OR: n & (1 << i) != 0
}
```

### Set bit `i`
```rust
fn set_bit(n: u32, i: u32) -> u32 {
    n | (1 << i)
}
```

### Clear bit `i`
```rust
fn clear_bit(n: u32, i: u32) -> u32 {
    n & !(1 << i)   // Rust uses ! for bitwise NOT
    // In C/Go: n & ~(1 << i)
}
```

### Toggle bit `i`
```rust
fn toggle_bit(n: u32, i: u32) -> u32 {
    n ^ (1 << i)
}
```

### Isolate the lowest set bit (LSB trick)
```rust
let lsb = n & n.wrapping_neg();  // same as n & (-n) in two's complement
// e.g., n = 0b10110100 → lsb = 0b00000100
```
This is the foundation of Fenwick Trees (Binary Indexed Trees).

### Clear the lowest set bit
```rust
let cleared = n & (n - 1);
// e.g., n = 0b10110100 → 0b10110000
```
**Why it works:** Subtracting 1 flips the lowest set bit and all bits below it. ANDing with original clears exactly those positions.

Count set bits (Brian Kernighan's algorithm — O(k) where k = set bits):
```rust
fn count_bits(mut n: u32) -> u32 {
    let mut count = 0;
    while n != 0 {
        n &= n - 1;  // clear lowest set bit
        count += 1;
    }
    count
}
```
In practice, use `n.count_ones()` in Rust or `bits.OnesCount(n)` in Go — these compile to a single `POPCNT` CPU instruction.

### Power of 2 check
```rust
fn is_power_of_two(n: u32) -> bool {
    n != 0 && (n & (n - 1)) == 0
}
```
**Insight:** Powers of 2 have exactly one bit set. `n-1` flips all bits below that bit. AND = 0.

### XOR swap (no temp variable)
```rust
a ^= b;
b ^= a;
a ^= b;
```
**Don't use this in practice** — it's slower than a register swap and breaks if `a` and `b` are the same variable. But understand *why* it works: XOR is self-inverse.

### Find the only non-repeated element
```rust
fn find_unique(arr: &[i32]) -> i32 {
    arr.iter().fold(0, |acc, &x| acc ^ x)
}
```
**Why:** XOR is commutative and associative. `a ^ a = 0`. `0 ^ a = a`. All pairs cancel, unique element survives.

---

## 7. Bit Masking & Bitmask DP

Bitmasks encode subsets. For `n` elements, there are `2ⁿ` subsets, each representable as an integer from `0` to `2ⁿ - 1`.

**Iterating all subsets of a set `mask`:**
```rust
let mut sub = mask;
while sub > 0 {
    // process sub as a subset of mask
    sub = (sub - 1) & mask;
}
// Don't forget to process sub = 0 separately
```

**Check if `sub` is a subset of `mask`:**
```rust
(sub & mask) == sub
```

This pattern powers Travelling Salesman Problem DP, Set Cover, and many combinatorial optimization problems — typically O(3ⁿ) over all subsets of all masks.

---

## 8. Endianness

**Byte order** — the order in which bytes of a multi-byte value are stored in memory.

- **Little-endian (x86, ARM default):** Least significant byte at lowest address.
- **Big-endian (network byte order, some RISC):** Most significant byte at lowest address.

```
Value: 0x12345678 (4 bytes)

Little-endian memory: [78] [56] [34] [12]
Big-endian memory:    [12] [34] [56] [78]
```

**Why it matters in DSA/systems:**
- File format parsing (PNG, BMP headers are big-endian)
- Network protocols (TCP/IP uses big-endian = "network byte order")
- Reading binary data from disk
- Comparing multi-byte keys as raw memory

```rust
// Rust handles endianness explicitly
let val: u32 = 0x12345678;
let be_bytes = val.to_be_bytes(); // [0x12, 0x34, 0x56, 0x78]
let le_bytes = val.to_le_bytes(); // [0x78, 0x56, 0x34, 0x12]
let reconstructed = u32::from_be_bytes(be_bytes);
```

```go
// Go — encoding/binary package
import "encoding/binary"
buf := make([]byte, 4)
binary.BigEndian.PutUint32(buf, 0x12345678)
val := binary.LittleEndian.Uint32(buf)
```

---

## 9. Bit Fields & Packing

Store multiple small values in a single integer — critical for memory-efficient algorithms, compact state representation, and embedded systems.

```rust
// Pack: color = 3 bits, size = 4 bits, visible = 1 bit
// Layout: [visible:1][size:4][color:3]

fn pack(color: u8, size: u8, visible: bool) -> u8 {
    (color & 0b111) | ((size & 0b1111) << 3) | ((visible as u8) << 7)
}

fn unpack_color(packed: u8) -> u8 { packed & 0b111 }
fn unpack_size(packed: u8) -> u8  { (packed >> 3) & 0b1111 }
fn unpack_visible(packed: u8) -> bool { (packed >> 7) & 1 == 1 }
```

In DSA, this technique appears in:
- Encoding graph state in BFS/DFS (multiple properties per node in one int)
- Compact DP states
- Bloom filters
- Bitboards in chess engines

---

## 10. Signed Integer Arithmetic Traps

### Overflow
```rust
// Rust: explicit, safe by default
i32::MAX.checked_add(1)  // None
i32::MAX.wrapping_add(1) // i32::MIN
i32::MAX.saturating_add(1) // i32::MAX (clamps)
```

### Integer Promotion (C gotcha, relevant for understanding)
In C, small types are promoted to `int` before operations. In Rust and Go, no implicit promotion — you must cast explicitly. This is *safer* and forces intentional thinking.

### Division and Right Shift Diverge for Negatives
```
-7 / 2  = -3  (truncates toward zero — C, Rust, Go)
-7 >> 1 = -4  (arithmetic shift — rounds toward -infinity)
```
These are NOT equivalent for negative numbers. Know which you want.

### Unsigned Underflow
```rust
let a: u32 = 3;
let b: u32 = 5;
// a - b wraps to 4294967294 in release mode, panics in debug
let diff = a.wrapping_sub(b); // explicit
```

---

## 11. Floating Point: IEEE 754

Floating point is bits too. Understanding the layout prevents subtle bugs.

```
64-bit double (f64):
[sign: 1 bit][exponent: 11 bits][mantissa: 52 bits]

Value = (-1)^sign × 1.mantissa × 2^(exponent - 1023)
```

**Key insights:**
- `0.1 + 0.2 ≠ 0.3` in binary — some decimals cannot be represented exactly
- `NaN ≠ NaN` — NaN is the only value not equal to itself (use this to detect NaN)
- Infinity propagates through arithmetic
- Two zeros: `+0.0` and `-0.0` (they compare equal but behave differently in some ops)

```rust
let nan = f64::NAN;
println!("{}", nan == nan);     // false
println!("{}", nan.is_nan());   // true

let a = 0.1f64 + 0.2f64;
let b = 0.3f64;
println!("{}", a == b);         // false
println!("{}", (a - b).abs() < f64::EPSILON); // true — correct comparison
```

---

## 12. Memory Layout & Alignment

Data must often be aligned to boundaries equal to its size. A 4-byte integer must be at an address divisible by 4.

```rust
use std::mem;

println!("{}", mem::size_of::<u8>());    // 1
println!("{}", mem::size_of::<u32>());   // 4
println!("{}", mem::size_of::<u64>());   // 8
println!("{}", mem::align_of::<u32>());  // 4
```

**Struct padding:**
```rust
struct Padded {
    a: u8,    // 1 byte
    // 3 bytes padding
    b: u32,   // 4 bytes
    c: u8,    // 1 byte
    // 3 bytes padding
}
// size = 12, not 6!

struct Packed {
    b: u32,   // 4 bytes
    a: u8,    // 1 byte
    c: u8,    // 1 byte
    // 2 bytes padding
}
// size = 8 — better! Sort fields by decreasing size.
```

This matters for cache performance and memory footprint in large data structures.

---

## 13. Bit Tricks in Algorithm Contexts

### Fast modulo by power of 2
```rust
let x = n & (m - 1);  // equivalent to n % m, when m is power of 2
// e.g., n % 8 → n & 7
```
Used heavily in hash tables with power-of-2 capacities.

### Determine sign of integer
```rust
let sign = (n >> 31) | ((-n) >> 31);
// -1 if negative, 1 if positive, 0 if zero
```

### Absolute value without branch
```rust
let mask = n >> 31;       // all 0s or all 1s (arithmetic shift)
let abs = (n ^ mask) - mask;
```

### Next power of 2 (ceiling)
```rust
fn next_power_of_two(mut n: u32) -> u32 {
    if n == 0 { return 1; }
    n -= 1;
    n |= n >> 1;
    n |= n >> 2;
    n |= n >> 4;
    n |= n >> 8;
    n |= n >> 16;
    n + 1
}
// Or simply: n.next_power_of_two() in Rust
```
**Logic:** Subtract 1, then smear all bits below the highest set bit, then add 1.

### Position of highest set bit (floor log₂)
```rust
let pos = 31 - n.leading_zeros(); // for u32
// Or: usize::BITS - n.leading_zeros() - 1
```

---

## 14. Bitset — O(1/64) Operations

A bitset stores N boolean values in N/64 integers. Operations on 64 elements happen in one CPU instruction.

```rust
struct Bitset {
    data: Vec<u64>,
    size: usize,
}

impl Bitset {
    fn new(size: usize) -> Self {
        Bitset { data: vec![0u64; (size + 63) / 64], size }
    }
    fn set(&mut self, i: usize) {
        self.data[i / 64] |= 1u64 << (i % 64);
    }
    fn get(&self, i: usize) -> bool {
        (self.data[i / 64] >> (i % 64)) & 1 == 1
    }
    fn count(&self) -> u32 {
        self.data.iter().map(|x| x.count_ones()).sum()
    }
    fn and(&self, other: &Bitset) -> Bitset {
        let data = self.data.iter().zip(&other.data).map(|(a,b)| a & b).collect();
        Bitset { data, size: self.size }
    }
}
```

Bitsets power: sieve of Eratosthenes, subset DP, graph reachability (transitive closure), string pattern matching.

---

## 15. Cognitive Framework: How Experts See Bits

When experts look at `n & (n-1)`, they don't compute — they *see* "clear lowest set bit." Build a vocabulary of bit patterns as first-class thoughts:

| Pattern | Meaning |
|---------|---------|
| `x & 1` | parity (odd/even) |
| `x & (x-1)` | clear lowest set bit |
| `x & -x` | isolate lowest set bit |
| `x \| (x-1)` | set all bits below lowest set bit |
| `x ^ (x-1)` | trailing ones mask |
| `~x & (x+1)` | lowest zero bit position |
| `(x >> k) & 1` | k-th bit value |

This is **chunking** — the cognitive process of compressing many facts into single retrievable units. Expert chess players don't see individual pieces; they see formations. Expert programmers don't see bit operations; they see semantic transformations.

Build this vocabulary by practicing until each pattern triggers an immediate semantic interpretation, not a computation.

---

## 16. Go Implementation Reference

```go
package main

import (
    "fmt"
    "math/bits"
)

func main() {
    n := uint32(0b10110100)

    // Standard library bit operations
    fmt.Println(bits.OnesCount32(n))      // popcount
    fmt.Println(bits.Len32(n))            // floor(log2(n)) + 1
    fmt.Println(bits.LeadingZeros32(n))   // leading zeros
    fmt.Println(bits.TrailingZeros32(n))  // trailing zeros = position of LSB
    fmt.Println(bits.Reverse32(n))        // bit reversal
    fmt.Println(bits.RotateLeft32(n, 3))  // rotate left
}
```

Go's `math/bits` package maps directly to CPU intrinsics — always prefer it over manual implementations.

---

## Summary: The Hierarchy of Understanding

```
Level 0: Can read/write binary and hex
Level 1: Understands all bitwise operators
Level 2: Applies bit tricks reflexively (set/clear/toggle/check)
Level 3: Sees bitmask patterns in problems before coding
Level 4: Designs algorithms that exploit bit-parallelism (bitsets, SIMD thinking)
Level 5: Reasons about bits at the hardware level (alignment, cache lines, POPCNT)
```

The goal is Level 4-5. You get there by solving problems until the patterns are *automatic* — not recalled, but recognized. This is what deliberate practice at the bit level looks like: not reading about tricks, but encountering a problem and *immediately* seeing the bit structure beneath it.

Every algorithm you study from here — from heaps to graphs to DP — has a bit-level perspective worth understanding. When you reach that layer, you are thinking like a systems programmer and an algorithm designer simultaneously.