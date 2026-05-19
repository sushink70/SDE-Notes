# Bitwise Operators: A Complete and Comprehensive Guide

> *Mastering bitwise operations gives you the mental model to think in terms of raw machine state — enabling you to write faster code, design compact data structures, and reason directly about hardware behavior.*

---

## Table of Contents

1. [Binary Fundamentals](#1-binary-fundamentals)
2. [Number Representation in Memory](#2-number-representation-in-memory)
3. [Two's Complement — The Foundation](#3-twos-complement--the-foundation)
4. [Endianness](#4-endianness)
5. [All Bitwise Operators — Complete Reference](#5-all-bitwise-operators--complete-reference)
   - [AND (`&`)](#51-and-)
   - [OR (`|`)](#52-or-)
   - [XOR (`^`)](#53-xor-)
   - [NOT (`~`)](#54-not-)
   - [Left Shift (`<<`)](#55-left-shift-)
   - [Right Shift (`>>`)](#56-right-shift-)
6. [Bit Masks — The Core Abstraction](#6-bit-masks--the-core-abstraction)
7. [Bit Flags and Permission Systems](#7-bit-flags-and-permission-systems)
8. [Bit Fields and Packed Structures](#8-bit-fields-and-packed-structures)
9. [Essential Bit Manipulation Techniques](#9-essential-bit-manipulation-techniques)
10. [Bit Tricks and Hacks](#10-bit-tricks-and-hacks)
11. [Arithmetic via Bitwise Operations](#11-arithmetic-via-bitwise-operations)
12. [Bitsets and Bitmaps](#12-bitsets-and-bitmaps)
13. [Floating-Point Bit Representation](#13-floating-point-bit-representation)
14. [Signed vs Unsigned: Pitfalls](#14-signed-vs-unsigned-pitfalls)
15. [Platform and Language Differences](#15-platform-and-language-differences)
16. [Performance and Compiler Behavior](#16-performance-and-compiler-behavior)
17. [Real-World Applications](#17-real-world-applications)
18. [Complete Implementation Reference (C, Go, Rust)](#18-complete-implementation-reference-c-go-rust)
19. [Mental Models Summary](#19-mental-models-summary)

---

## 1. Binary Fundamentals

### What is Binary?

Every value stored in a computer is ultimately a sequence of **bits** (binary digits). A bit is the most fundamental unit of information — it can be either `0` or `1`, representing two electrical states: low voltage (off) and high voltage (on).

```
Decimal:   0   1   2   3   4   5   6   7   8   9  10  11  12  13  14  15
Binary:  000 001 010 011 100 101 110 111 1000...

         +---+---+---+---+---+---+---+---+
8-bit:   | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |   <- bit positions (index)
         +---+---+---+---+---+---+---+---+
           ^                           ^
         MSB                          LSB
    (Most Significant Bit)     (Least Significant Bit)
```

### Positional Notation

In base-10 (decimal), each position is a power of 10:
```
  1  3  7
  |  |  +-- 7 * 10^0 =   7
  |  +----- 3 * 10^1 =  30
  +-------- 1 * 10^2 = 100
                         ---
                         137
```

In base-2 (binary), each position is a power of 2:
```
  1  0  0  0  1  0  0  1
  |  |  |  |  |  |  |  +-- 1 * 2^0 =   1
  |  |  |  |  |  |  +----- 0 * 2^1 =   0
  |  |  |  |  |  +-------- 0 * 2^2 =   0
  |  |  |  |  +----------- 1 * 2^3 =   8
  |  |  |  +-------------- 0 * 2^4 =   0
  |  |  +----------------- 0 * 2^5 =   0
  |  +-------------------- 0 * 2^6 =   0
  +----------------------- 1 * 2^7 = 128
                                      ---
                                      137  (decimal)
```

### Powers of 2 — The Cheat Sheet

```
Bit Position    Power       Value
     0          2^0           1
     1          2^1           2
     2          2^2           4
     3          2^3           8
     4          2^4          16
     5          2^5          32
     6          2^6          64
     7          2^7         128
     8          2^8         256
     9          2^9         512
    10          2^10       1,024    (1 KiB)
    16          2^16      65,536
    20          2^20   1,048,576   (1 MiB)
    30          2^30   1,073,741,824 (~1 GiB)
    31          2^31   2,147,483,648 (max signed 32-bit)
    32          2^32   4,294,967,296 (max unsigned 32-bit + 1)
    63          2^63   9,223,372,036,854,775,808 (max signed 64-bit)
```

### Hexadecimal — The Programmer's Shorthand

Binary is verbose. Hexadecimal (base 16) is used as a compact notation because one hex digit maps exactly to 4 bits (a **nibble**).

```
Hex: 0  1  2  3  4  5  6  7  8  9   A   B   C   D   E   F
Dec: 0  1  2  3  4  5  6  7  8  9  10  11  12  13  14  15
Bin: 0000 0001 0010 0011 0100 0101 0110 0111 1000 1001 1010 1011 1100 1101 1110 1111

Example: 0xAB = 1010 1011
                ^^^^ ^^^^
                 A    B

         0xDEADBEEF = 1101 1110 1010 1101 1011 1110 1110 1111
                       D    E    A    D    B    E    E    F
```

---

## 2. Number Representation in Memory

### Integer Sizes

```
Type            Bits    Bytes    Unsigned Range             Signed Range
---------------------------------------------------------------------------
u8  / uint8      8        1       0 to 255                  -128 to 127
u16 / uint16    16        2       0 to 65,535            -32,768 to 32,767
u32 / uint32    32        4       0 to 4,294,967,295     -2,147,483,648 to 2,147,483,647
u64 / uint64    64        8       0 to 18,446,744,073... -9,223,372,036,854,775,808 to ...
u128 / uint128 128       16       0 to 3.4 * 10^38       -1.7 * 10^38 to ...
```

### Memory Layout of an Integer

```
u32 value = 0xDEADBEEF

Memory (big-endian order shown):
+--------+--------+--------+--------+
|  0xDE  |  0xAD  |  0xBE  |  0xEF  |
+--------+--------+--------+--------+
  Byte 0   Byte 1   Byte 2   Byte 3

Bit layout (32 bits, position 31 down to 0):
+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
| 31 | 30 | 29 | 28 | 27 | 26 | 25 | 24 | 23 | 22 | 21 | 20 | 19 | 18 | 17 | 16 |
+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
|  1 |  1 |  0 |  1 |  1 |  1 |  1 |  0 |  1 |  0 |  1 |  0 |  1 |  1 |  0 |  1 |
+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+

+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
| 15 | 14 | 13 | 12 | 11 | 10 |  9 |  8 |  7 |  6 |  5 |  4 |  3 |  2 |  1 |  0 |
+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
|  1 |  0 |  1 |  1 |  1 |  1 |  1 |  0 |  1 |  1 |  1 |  0 |  1 |  1 |  1 |  1 |
+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
     D    E    A    D         B    E         E    F
     (0xDE = 1101 1110) (0xAD = 1010 1101) (0xBE = 1011 1110) (0xEF = 1110 1111)
```

---

## 3. Two's Complement — The Foundation

### Why Two's Complement?

Computers need a way to represent negative numbers. Two's complement is universally used on modern hardware because:
1. There is only **one representation of zero**
2. Addition and subtraction use the **same circuit** for signed and unsigned numbers
3. The sign bit naturally encodes the sign without special treatment

### Sign-Magnitude (NOT used) vs Two's Complement

```
Sign-Magnitude (naive, problematic):
  +0 = 0000 0000
  -0 = 1000 0000   <- Two zeros! Ambiguous.
  -1 = 1000 0001
  -127 = 1111 1111

Two's Complement (actual standard):
  +0  = 0000 0000   <- Only one zero
  -1  = 1111 1111
  -2  = 1111 1110
  -127= 1000 0001
  -128= 1000 0000   <- Extra negative number
  +127= 0111 1111
```

### How to Compute Two's Complement

**Rule:** Invert all bits, then add 1.

```
Convert +5 to -5 (in 8-bit):

Step 1: +5 in binary
  +5  = 0000 0101

Step 2: Invert all bits (bitwise NOT)
  NOT = 1111 1010

Step 3: Add 1
        1111 1010
      +         1
      -----------
        1111 1011  <- this is -5 in two's complement

Verify: 0000 0101  (+5)
      + 1111 1011  (-5)
      -----------
      1 0000 0000  <- overflow discarded, result = 0 ✓
```

### Two's Complement Number Circle

```
          0000 0000  (0)
       /               \
  1111 1111 (-1)    0000 0001 (+1)
  1111 1110 (-2)    0000 0010 (+2)
  1111 1101 (-3)    0000 0011 (+3)
        ...                ...
  1000 0001 (-127)  0111 1111 (+127)
       \               /
        1000 0000 (-128)

The MSB (bit 7) is the SIGN BIT:
  0 = positive
  1 = negative
```

### 8-bit Two's Complement Full Table

```
Binary      Unsigned    Signed
0000 0000      0           0
0000 0001      1           1
0000 0010      2           2
...
0111 1110    126         126
0111 1111    127         127   <- max positive signed
1000 0000    128        -128   <- min negative signed (flip: sign bit)
1000 0001    129        -127
1000 0010    130        -126
...
1111 1110    254          -2
1111 1111    255          -1
```

### Sign Extension

When you promote a smaller signed integer to a larger type, the sign bit is replicated:

```
-1 as i8:
  1111 1111

-1 as i16 (sign-extended):
  1111 1111 1111 1111
  ^^^^^^^^^ <- copied sign bit fills new bytes

-1 as i32:
  1111 1111 1111 1111 1111 1111 1111 1111

+5 as i8:
  0000 0101

+5 as i16 (sign-extended):
  0000 0000 0000 0101  <- zero-filled (MSB was 0)
```

---

## 4. Endianness

Endianness determines the **byte order** in which a multi-byte value is stored in memory. It does NOT affect bit order within a byte.

```
Value: 0x12345678 stored at address 0x1000

BIG-ENDIAN (most significant byte first — "network order"):
  Address: 0x1000  0x1001  0x1002  0x1003
  Value:    0x12    0x34    0x56    0x78
                                    ^--- least significant byte at highest address

LITTLE-ENDIAN (least significant byte first — x86/ARM default):
  Address: 0x1000  0x1001  0x1002  0x1003
  Value:    0x78    0x56    0x34    0x12
            ^--- least significant byte at lowest address

Memory diagram (little-endian, x86):

  Low address                          High address
  +--------+--------+--------+--------+
  |  0x78  |  0x56  |  0x34  |  0x12  |
  +--------+--------+--------+--------+
  0x1000   0x1001   0x1002   0x1003
```

Bitwise operations work on the **logical value**, not the memory layout, so endianness is transparent when doing arithmetic/bitwise operations in code. It only matters when reading raw bytes from files, networks, or casting pointers.

---

## 5. All Bitwise Operators — Complete Reference

### 5.1 AND (`&`)

**Truth table:**

```
A   B   A & B
-----------
0   0     0
0   1     0
1   0     0
1   1     1

Rule: Output is 1 ONLY IF BOTH inputs are 1.
```

**Bitwise AND on bytes:**

```
    0b10110110   (0xB6 = 182)
  & 0b11001101   (0xCD = 205)
  ------------
    0b10000100   (0x84 = 132)

Bit-by-bit:
  Pos: 7  6  5  4  3  2  1  0
    A: 1  0  1  1  0  1  1  0
    B: 1  1  0  0  1  1  0  1
  A&B: 1  0  0  0  0  1  0  0
```

**Mental model:** AND is a **mask** — it keeps only the bits where the mask has a `1`, clearing everything else.

**Common uses:**
- Check if a specific bit is set
- Clear specific bits
- Extract a field from a packed integer
- Modulo by power-of-2 (`n & (p - 1)` instead of `n % p`)

### 5.2 OR (`|`)

**Truth table:**

```
A   B   A | B
-----------
0   0     0
0   1     1
1   0     1
1   1     1

Rule: Output is 1 IF AT LEAST ONE input is 1.
```

**Bitwise OR on bytes:**

```
    0b10110110   (0xB6 = 182)
  | 0b11001101   (0xCD = 205)
  ------------
    0b11111111   (0xFF = 255)

Bit-by-bit:
  Pos: 7  6  5  4  3  2  1  0
    A: 1  0  1  1  0  1  1  0
    B: 1  1  0  0  1  1  0  1
  A|B: 1  1  1  1  1  1  1  1
```

**Mental model:** OR **sets** bits — it forces specific bit positions to `1` without disturbing others.

**Common uses:**
- Set a specific bit
- Combine (merge) flags
- Build up a value by OR-ing fields together

### 5.3 XOR (`^`)

**Truth table:**

```
A   B   A ^ B
-----------
0   0     0
0   1     1
1   0     1
1   1     0

Rule: Output is 1 IF EXACTLY ONE input is 1 (they differ).
     Output is 0 IF BOTH inputs are the same.
```

**Bitwise XOR on bytes:**

```
    0b10110110   (0xB6 = 182)
  ^ 0b11001101   (0xCD = 205)
  ------------
    0b01111011   (0x7B = 123)

Bit-by-bit:
  Pos: 7  6  5  4  3  2  1  0
    A: 1  0  1  1  0  1  1  0
    B: 1  1  0  0  1  1  0  1
  A^B: 0  1  1  1  1  0  1  1
```

**Key XOR identities:**

```
a ^ 0 = a        (XOR with 0 is identity)
a ^ a = 0        (XOR with itself = 0)
a ^ ~0 = ~a      (XOR with all-ones flips all bits = NOT)
a ^ b ^ b = a    (XOR is its own inverse)
```

**Mental model:** XOR **toggles** bits — flip specific positions while leaving others untouched.

**Common uses:**
- Toggle a bit
- Swap two values without a temp variable
- Simple encryption (XOR cipher)
- Find a unique value in an array where everything else is duplicated
- Detect bit differences between two values
- Parity calculation
- CRC/checksum computation

### 5.4 NOT (`~`)

**Truth table:**

```
A   ~A
------
0    1
1    0

Rule: Flip every bit.
```

**Bitwise NOT on a byte:**

```
  ~ 0b10110110   (0xB6 = 182)
  ------------
    0b01001001   (0x49 = 73)

Bit-by-bit:
  Pos: 7  6  5  4  3  2  1  0
    A: 1  0  1  1  0  1  1  0
   ~A: 0  1  0  0  1  0  0  1
```

**Critical: NOT and Two's Complement Relationship**

```
~n = -(n + 1)     for all signed integers

~0  = -1
~1  = -2
~-1 =  0
~127 = -128
~(-128) = 127

Why? Because: ~n + 1 = -n (two's complement negation)
So:          ~n = -n - 1 = -(n+1)
```

**Mental model:** NOT produces the **bitwise inverse** — the complement. It's the first step of two's complement negation.

**Common uses:**
- Invert a mask (turn a "keep" mask into a "clear" mask)
- Clear all bits in a masked region: `value & ~mask`
- Two's complement negation step 1

### 5.5 Left Shift (`<<`)

**Behavior:** Shift all bits to the left by N positions. Vacated positions on the right are filled with `0`. Bits shifted off the left end are **discarded**.

```
value = 0b00001011   (11 decimal)
value << 1:

  Before: 0  0  0  0  1  0  1  1
          |  |  |  |  |  |  |  |
          v  v  v  v  v  v  v  v
  Shift:  0  0  0  1  0  1  1  [0]  <- zero inserted on right
                                      bit 7 falls off (discarded)
  After:  0  0  0  1  0  1  1  0    = 22 decimal

value << 2:
  Before: 0  0  0  0  1  0  1  1
  After:  0  0  1  0  1  1  0  0    = 44 decimal

value << 3:
  Before: 0  0  0  0  1  0  1  1
  After:  0  1  0  1  1  0  0  0    = 88 decimal
```

**Visualization:**

```
  [7][6][5][4][3][2][1][0]       original
        |  |  |  |  |  |  |
        v  v  v  v  v  v  v
  [7][6][5][4][3][2][1][0]  << 1
   dropped             ^--- zero
```

**Left shift = multiplication by powers of 2:**

```
x << 1  =  x * 2
x << 2  =  x * 4
x << 3  =  x * 8
x << n  =  x * 2^n
```

**Overflow:** If significant bits are shifted off the left end, the value wraps or produces undefined behavior (in C for signed integers — see section 14).

### 5.6 Right Shift (`>>`)

**Two types exist, depending on whether the type is signed or unsigned:**

#### Logical Right Shift (unsigned / `>>>` in Java)

Vacated positions on the LEFT are filled with **0**.

```
value = 0b10110000   (176 decimal, treated as unsigned)
value >> 1:

  Before: 1  0  1  1  0  0  0  0
  After:  0  1  0  1  1  0  0  0    = 88 decimal
          ^--- zero inserted

value >> 3:
  Before: 1  0  1  1  0  0  0  0
  After:  0  0  0  1  0  1  1  0    = 22 decimal
```

#### Arithmetic Right Shift (signed integers)

Vacated positions on the LEFT are filled with the **sign bit** (0 for positive, 1 for negative). This preserves the sign and implements division by powers of 2 for negative numbers.

```
value = 0b10110000   (-80 in signed 8-bit two's complement)
value >> 1 (arithmetic):

  Before: 1  0  1  1  0  0  0  0
  After:  1  1  0  1  1  0  0  0    = -40 (sign bit replicated!)
          ^--- sign bit copied

value >> 3 (arithmetic):
  Before: 1  0  1  1  0  0  0  0
  After:  1  1  1  1  0  1  1  0    = -10

Positive value (sign bit = 0):
value = 0b01011000   (+88 decimal)
value >> 2 (arithmetic):
  Before: 0  1  0  1  1  0  0  0
  After:  0  0  0  1  0  1  1  0    = +22 (zeros fill in, same as logical)
```

**Arithmetic right shift diagram:**

```
  Sign bit copies itself across
  |
  v
  [S][7][6][5][4][3][2][1][0]  >> 2
      |  |  |  |  |  |
      v  v  v  v  v  v
  [S][S][S][7][6][5][4][3]       (bits 1,0 discarded)
```

**Right shift = integer division by powers of 2:**

```
x >> 1  =  x / 2   (integer division, rounds toward -infinity for signed)
x >> 2  =  x / 4
x >> n  =  x / 2^n

Note: For negative numbers, arithmetic right shift rounds DOWN (toward -inf),
      whereas C division rounds toward zero.

  -7 >> 1 = -4   (rounds down)
  -7 / 2  = -3   (rounds toward zero)
```

---

## 6. Bit Masks — The Core Abstraction

A **bitmask** is a value used with bitwise operators to selectively read, set, clear, or toggle specific bits.

### Mask Construction

```
Goal: Create a mask for bit N

mask = 1 << N

Examples:
  bit 0 mask: 1 << 0 = 0b00000001 = 0x01
  bit 3 mask: 1 << 3 = 0b00001000 = 0x08
  bit 7 mask: 1 << 7 = 0b10000000 = 0x80

Goal: Create a mask covering bits N to M (inclusive)

Method: ((1 << (M - N + 1)) - 1) << N

Bits 2..5 mask (4 bits starting at position 2):
  width = 5 - 2 + 1 = 4
  ((1 << 4) - 1) << 2
  = (16 - 1) << 2
  = 15 << 2
  = 0b00001111 << 2
  = 0b00111100

Visual:
  Bit position: 7  6  5  4  3  2  1  0
  Mask value:   0  0  1  1  1  1  0  0
                      ^-----------^
                      Bits 5 to 2 covered
```

### The Four Fundamental Mask Operations

```
Let: value = 0b10110101
     mask  = 0b00001111   (lower nibble)

1. TEST (check if any masked bit is set):
   result = value & mask
   0b10110101
 & 0b00001111
 ------------
   0b00000101   != 0, so YES, some bits in mask are set

2. SET (force bits in mask to 1):
   result = value | mask
   0b10110101
 | 0b00001111
 ------------
   0b10111111   <- lower nibble all set to 1

3. CLEAR (force bits in mask to 0):
   result = value & ~mask
   ~mask  = 0b11110000
   0b10110101
 & 0b11110000
 ------------
   0b10110000   <- lower nibble cleared to 0

4. TOGGLE (flip bits in mask):
   result = value ^ mask
   0b10110101
 ^ 0b00001111
 ------------
   0b10111010   <- lower nibble toggled
```

---

## 7. Bit Flags and Permission Systems

Bit flags are a classic use of bitwise operators. Each bit in an integer represents an independent boolean flag.

### Designing a Flag System

```
// Example: Unix-style file permissions (9 flags in lower 9 bits)

Flag Layout (bit positions):
  Bit 8: owner read
  Bit 7: owner write
  Bit 6: owner execute
  Bit 5: group read
  Bit 4: group write
  Bit 3: group execute
  Bit 2: others read
  Bit 1: others write
  Bit 0: others execute

Octal 755 = 111 101 101 in binary:
  Pos: 8  7  6 | 5  4  3 | 2  1  0
       1  1  1 | 1  0  1 | 1  0  1
       rwx       r-x       r-x
```

### Flag Operations

```c
// In C (also applies to Go and Rust)

#define FLAG_READABLE   (1 << 0)   // 0001
#define FLAG_WRITABLE   (1 << 1)   // 0010
#define FLAG_EXECUTABLE (1 << 2)   // 0100
#define FLAG_HIDDEN     (1 << 3)   // 1000

uint8_t permissions = 0;

// Set flags
permissions |= FLAG_READABLE;               // Set read
permissions |= FLAG_READABLE | FLAG_WRITABLE; // Set multiple

// Clear a flag
permissions &= ~FLAG_WRITABLE;             // Clear write

// Toggle a flag
permissions ^= FLAG_HIDDEN;                // Toggle hidden

// Test a flag
if (permissions & FLAG_READABLE) { ... }   // Is readable?

// Test multiple flags (ALL must be set)
if ((permissions & (FLAG_READABLE | FLAG_WRITABLE)) == (FLAG_READABLE | FLAG_WRITABLE)) { ... }

// Test multiple flags (ANY set)
if (permissions & (FLAG_READABLE | FLAG_WRITABLE)) { ... }

// Replace all flags
permissions = FLAG_READABLE | FLAG_EXECUTABLE;

// Clear all flags
permissions = 0;

// Set all flags
permissions = ~0u;    // 0xFF for uint8
```

### Flag State Machine Diagram

```
                    SET flag:   val |= flag
                   CLEAR flag:  val &= ~flag
                  TOGGLE flag:  val ^= flag

  Initial state
  permissions = 0b00000000

  Set READ (bit 0):
  permissions |= 0b00000001
  = 0b00000001

  Set WRITE (bit 1):
  permissions |= 0b00000010
  = 0b00000011

  Clear READ (bit 0):
  permissions &= ~0b00000001
  = permissions & 0b11111110
  = 0b00000010

  Toggle EXECUTE (bit 2):
  permissions ^= 0b00000100
  = 0b00000110   (WRITE + EXECUTE)
```

---

## 8. Bit Fields and Packed Structures

### Manual Bit Fields (Portable, Explicit)

When you need to pack multiple small values into one integer (e.g., network packets, hardware registers, protocol headers), you manually define field positions and masks.

```
Example: Pack a date into a 32-bit integer
  Year:  bits 16..31  (16 bits, values 0–65535)
  Month: bits 8..15   (8 bits,  values 0–255)
  Day:   bits 0..7    (8 bits,  values 0–255)

  32-bit integer layout:
  +------------------+--------+--------+
  |  YEAR (16 bits)  | MONTH  |  DAY   |
  |  bits 31..16     | 15..8  |  7..0  |
  +------------------+--------+--------+
   31              16 15     8 7      0

Constants:
  YEAR_SHIFT  = 16
  MONTH_SHIFT = 8
  DAY_SHIFT   = 0

  YEAR_MASK   = 0xFFFF0000
  MONTH_MASK  = 0x0000FF00
  DAY_MASK    = 0x000000FF

Pack date (2024, 12, 25):
  packed  = (2024 << 16) | (12 << 8) | 25
  packed  = 0x07E80C19

Unpack year:
  year    = (packed >> 16) & 0xFFFF   = 2024

Unpack month:
  month   = (packed >> 8)  & 0xFF     = 12

Unpack day:
  day     = (packed >> 0)  & 0xFF     = 25
```

### IPv4 Header Bit Fields

```
IPv4 Header (first 32 bits):
  +-------+-------+------------------+--------------------------------+
  | 4 bits| 4 bits|     8 bits       |           16 bits              |
  |  VER  |  IHL  |      DSCP/ECN    |         Total Length           |
  +-------+-------+------------------+--------------------------------+
   31  28  27  24   23            16   15                            0

Extract VER (bits 28..31):
  version = (header >> 28) & 0x0F

Extract IHL (bits 24..27):
  ihl = (header >> 24) & 0x0F

Extract Total Length (bits 0..15):
  length = header & 0xFFFF
```

### C Compiler Bit Fields (NOT portable)

```c
// Language feature, but NOT portable (layout is implementation-defined)
struct Date {
    uint32_t day   : 5;   // 5 bits (0..31)
    uint32_t month : 4;   // 4 bits (0..15)
    uint32_t year  : 23;  // 23 bits
};

// WARNING: bit ordering, padding, and alignment are
// compiler and platform specific. Use manual packing for
// portable code (network protocols, file formats, etc.)
```

---

## 9. Essential Bit Manipulation Techniques

This section catalogs the most important and widely used bit manipulation operations.

### 9.1 Set, Clear, Toggle, Test a Single Bit

```
// For bit position n in value x:

SET bit n:       x |= (1 << n)
CLEAR bit n:     x &= ~(1 << n)
TOGGLE bit n:    x ^= (1 << n)
TEST bit n:      (x >> n) & 1    or    x & (1 << n)

Visual example for bit 3 of 0b10100001:

  x = 0b10100001

  SET bit 3:
    1 << 3      = 0b00001000
    x |= mask   = 0b10101001

  CLEAR bit 3 (wasn't set, but anyway):
    ~(1<<3)     = 0b11110111
    x &= mask   = 0b10100001

  TOGGLE bit 3:
    x ^= 0b00001000 = 0b10101001

  TEST bit 3:
    (x >> 3) & 1 = (0b00010100) & 1 = 0   (not set)
```

### 9.2 Isolate the Lowest Set Bit

```
result = x & (-x)       also written as    x & (~x + 1)

Why it works (two's complement):
  -x flips all bits and adds 1.
  The lowest set bit in x and -x share only the lowest set bit.

Example:
  x       = 0b10110100   (lowest set bit is bit 2)
  -x      = 0b01001100   (two's complement of x)
  x & -x  = 0b00000100   <- isolated lowest bit!

         x: 1 0 1 1 0 1 0 0
        -x: 0 1 0 0 1 1 0 0
    x & -x: 0 0 0 0 0 1 0 0   = 4 = 2^2 ✓
```

### 9.3 Clear the Lowest Set Bit

```
result = x & (x - 1)

Example:
  x       = 0b10110100
  x - 1   = 0b10110011   (borrow propagates through the trailing zeros)
  x & x-1 = 0b10110000   <- lowest set bit cleared!

  Before: 1 0 1 1 0 1 0 0
  After:  1 0 1 1 0 0 0 0

Use case: Count set bits by repeatedly clearing the lowest:
  while (x != 0) { x &= (x-1); count++; }
```

### 9.4 Check if Value is a Power of 2

```
A power of 2 has exactly one bit set:
  1   = 0b00000001
  2   = 0b00000010
  4   = 0b00000100
  8   = 0b00001000
  16  = 0b00010000

Using trick 9.3:
  is_power_of_two = (x != 0) && ((x & (x - 1)) == 0)

Why: If x is a power of 2, clearing its only set bit gives 0.

  x = 8:    0b00001000
  x-1 = 7:  0b00000111
  x & x-1:  0b00000000   == 0, so yes!

  x = 6:    0b00000110
  x-1 = 5:  0b00000101
  x & x-1:  0b00000100   != 0, so no!
```

### 9.5 Count Set Bits (Popcount / Hamming Weight)

```
Naive approach:
  count = 0
  while x != 0:
    count += x & 1
    x >>= 1

Better: Brian Kernighan's algorithm
  count = 0
  while x != 0:
    x &= x - 1   // clear lowest set bit
    count++

Best: Parallel bit counting (SWAR algorithm for 32-bit):

  x = x - ((x >> 1) & 0x55555555)     // pairs
  x = (x & 0x33333333) + ((x >> 2) & 0x33333333)  // nibbles
  x = (x + (x >> 4)) & 0x0F0F0F0F     // bytes
  x = (x * 0x01010101) >> 24           // sum bytes

Pattern of masks:
  0x55555555 = 0101 0101 0101 0101 0101 0101 0101 0101 (alternating bits)
  0x33333333 = 0011 0011 0011 0011 0011 0011 0011 0011 (alternating pairs)
  0x0F0F0F0F = 0000 1111 0000 1111 0000 1111 0000 1111 (alternating nibbles)

Hardware instruction: most CPUs have a POPCNT instruction (one cycle).
  C:    __builtin_popcount(x)
  Rust: x.count_ones()
  Go:   bits.OnesCount(x)
```

### 9.6 Find the Position of the Lowest Set Bit (Count Trailing Zeros)

```
Naive:
  pos = 0
  while (x & 1) == 0:
    x >>= 1
    pos++

Bit trick (for 32-bit):
  pos = popcount((x & -x) - 1)

Hardware (preferred):
  C:    __builtin_ctz(x)    // count trailing zeros
  Rust: x.trailing_zeros()
  Go:   bits.TrailingZeros(x)

Example:
  x = 0b10110100
  trailing zeros = 2   (bits 0 and 1 are 0)
  lowest set bit is at position 2
```

### 9.7 Find the Position of the Highest Set Bit (Count Leading Zeros / Log2)

```
Hardware:
  C:    __builtin_clz(x)    // count leading zeros
  Rust: x.leading_zeros()
  Go:   bits.LeadingZeros(x)

Floor of log base 2:
  floor_log2(x) = (bit_width - 1) - leading_zeros(x)
               = 31 - __builtin_clz(x)   (for 32-bit)

Example:
  x = 0b00010110 = 22
  Leading zeros = 3
  Highest set bit = bit 4 (position 4, zero-indexed)
  floor_log2(22) = 4  (since 2^4=16 <= 22 < 32=2^5)
```

### 9.8 Round Up to Next Power of 2

```
Algorithm (for 32-bit):
  x--
  x |= x >> 1
  x |= x >> 2
  x |= x >> 4
  x |= x >> 8
  x |= x >> 16
  x++

This works by setting all bits below the highest set bit to 1,
then adding 1 causes a carry that produces the next power of 2.

Example: round up 10 (0b00001010):
  x = 9         = 0b00001001   (after x--)
  x |= x>>1     = 0b00001001 | 0b00000100 = 0b00001101
  x |= x>>2     = 0b00001101 | 0b00000011 = 0b00001111
  x |= x>>4     = 0b00001111 | 0b00000000 = 0b00001111
  ...
  x++           = 0b00010000  = 16 ✓

Simpler with CLZ:
  next_pow2(x) = 1 << (32 - __builtin_clz(x - 1))
```

### 9.9 Swap Two Values Without a Temporary

```
XOR swap:
  a ^= b
  b ^= a
  a ^= b

Proof:
  Initial:  a = A, b = B
  Step 1:   a = A^B,    b = B
  Step 2:   b = B^(A^B) = A,  a = A^B
  Step 3:   a = (A^B)^A = B
  Result:   a = B, b = A ✓

WARNING: If a and b are the same variable/alias, XOR swap produces 0!
  a ^= a -> a = 0 (broken)
  Always use a temp variable in real code unless you're certain they're distinct.
```

### 9.10 Reverse All Bits

```
Reverse bits of a 32-bit value:

Algorithm:
  x = ((x & 0xAAAAAAAA) >> 1) | ((x & 0x55555555) << 1)   // swap adjacent bits
  x = ((x & 0xCCCCCCCC) >> 2) | ((x & 0x33333333) << 2)   // swap nibble halves
  x = ((x & 0xF0F0F0F0) >> 4) | ((x & 0x0F0F0F0F) << 4)   // swap nibbles
  x = ((x & 0xFF00FF00) >> 8) | ((x & 0x00FF00FF) << 8)   // swap bytes
  x = (x >> 16) | (x << 16)                                 // swap 16-bit halves

Visualization (8-bit):
  Before: b7 b6 b5 b4 b3 b2 b1 b0
  After:  b0 b1 b2 b3 b4 b5 b6 b7

Example:
  x = 0b10110001
  Rev = 0b10001101
```

### 9.11 Extract a Bitfield (Range of Bits)

```
Extract bits [high:low] from value:

  mask = ((1 << (high - low + 1)) - 1) << low
  field = (value & mask) >> low

  Or more simply:
  field = (value >> low) & ((1 << (high - low + 1)) - 1)

Example: Extract bits 4..7 from 0b11001010:
  value = 0b11001010
  low = 4, high = 7
  width = 4
  (value >> 4) = 0b00001100
  mask = (1<<4)-1 = 0b00001111
  field = 0b00001100 & 0b00001111 = 0b00001100 = 12
```

### 9.12 Set a Bitfield Value

```
Set bits [high:low] to a new value:

  width = high - low + 1
  mask = ((1 << width) - 1) << low
  result = (original & ~mask) | ((new_val << low) & mask)

Example: Set bits 4..7 to value 5 (0b0101) in 0b11001010:
  original = 0b11001010
  mask     = 0b11110000
  ~mask    = 0b00001111
  original & ~mask  = 0b00001010   (cleared field)
  5 << 4            = 0b01010000   (new value shifted into position)
  result            = 0b01011010
```

### 9.13 Rotate Left and Rotate Right

**Rotation** (or circular shift) wraps bits around instead of discarding them.

```
Rotate left by 1 (8-bit):
  Before: b7 b6 b5 b4 b3 b2 b1 b0
  After:  b6 b5 b4 b3 b2 b1 b0 b7   <- b7 wraps to position 0

Implementation (n-bit rotate left by k):
  result = (x << k) | (x >> (n - k))

Example (8-bit, rotate left by 2):
  x = 0b10110101
  x << 2  = 0b11010100   (top 2 bits lost)
  x >> 6  = 0b00000010   (top 2 bits moved to bottom)
  result  = 0b11010110   ✓

Rotate right by k:
  result = (x >> k) | (x << (n - k))

Hardware: x86 has ROL and ROR instructions.
  C:    No standard; use intrinsics or trust compiler
  Rust: x.rotate_left(k), x.rotate_right(k)
  Go:   bits.RotateLeft(x, k)
```

---

## 10. Bit Tricks and Hacks

### 10.1 Fast Modulo for Powers of 2

```
For n = power of 2:
  x % n  ==  x & (n - 1)    (for unsigned x)

Example: x % 8 == x & 7
  x = 25 = 0b00011001
  x & 7  = 0b00000001 = 1
  25 % 8 = 1 ✓

Why: n = 2^k means n in binary is 1 followed by k zeros.
  n - 1 = k ones in a row.
  x & (n-1) keeps only the k lower bits = x mod n.

  n = 8:   0b00001000
  n-1 = 7: 0b00000111   <- mask for lower 3 bits (= mod 8)
```

### 10.2 Fast Absolute Value (Branchless)

```
For signed 32-bit integer x:

  mask = x >> 31    // arithmetic right shift: 0 if positive, -1 (0xFFFFFFFF) if negative
  abs  = (x + mask) ^ mask

If x >= 0: mask = 0,  abs = (x + 0) ^ 0 = x
If x < 0:  mask = -1, abs = (x + (-1)) ^ (-1) = (x-1) ^ -1 = ~(x-1) = -x  ✓

Alternative:
  abs = (x ^ mask) - mask
```

### 10.3 Branchless Minimum and Maximum

```
// For 32-bit signed integers a, b:

min(a, b):
  diff = a - b
  mask = diff >> 31   // 0 if a>=b, -1 if a<b
  min  = b + (diff & mask)   // = b if a>=b, = b+(a-b)=a if a<b

max(a, b):
  diff = a - b
  mask = diff >> 31
  max  = a - (diff & mask)
```

### 10.4 Conditional Set Without Branch

```
// Set y = (condition) ? a : b without if statement

// Using arithmetic:
  y = b ^ ((a ^ b) & -(condition != 0))
  // -(cond != 0) is 0 if false, -1 (all bits set) if true

// If condition is already 0 or 1:
  mask = -condition  // 0 -> 0, 1 -> 0xFFFFFFFF
  y = (a & mask) | (b & ~mask)
```

### 10.5 Sign Detection

```
// Sign of x (returns -1, 0, or 1):
  sign = (x >> 31) | ((-x) >> 31 & 1)

// Simple: is x negative?
  is_negative = (x >> 31) & 1   // for signed 32-bit

// Check if two numbers have opposite signs:
  opposite_signs = ((a ^ b) < 0)   // MSBs differ = different signs
```

### 10.6 Interleave (Morton Code / Z-Order Curve)

```
Interleave bits of two 16-bit numbers x, y to form one 32-bit Morton code.
Used in spatial indexing, Z-order curves, quadtrees.

Result layout:
  Bit: 31 30 29 28 27 26 25 24 23 22 21 20 19 18 17 16 15 14...
  Src:  y  x  y  x  y  x  y  x  y  x  y  x  y  x  y  x ...

Function (spreading bits):
  uint32_t spread(uint16_t n) {
      uint32_t x = n;
      x = (x | (x << 8)) & 0x00FF00FF;
      x = (x | (x << 4)) & 0x0F0F0F0F;
      x = (x | (x << 2)) & 0x33333333;
      x = (x | (x << 1)) & 0x55555555;
      return x;
  }
  morton = spread(x) | (spread(y) << 1);
```

### 10.7 Parity Calculation

```
// Parity = XOR of all bits (1 if odd number of set bits, 0 if even)

// 32-bit:
  x ^= x >> 16;
  x ^= x >> 8;
  x ^= x >> 4;
  x ^= x >> 2;
  x ^= x >> 1;
  parity = x & 1;

// Example for 0b10110101 (5 set bits = odd parity):
  x =  1011 0101
  x ^= x>>4: 1011 0101 ^ 0000 1011 = 1011 1110
  x ^= x>>2: 1011 1110 ^ 0010 1111 = 1001 0001
  x ^= x>>1: 1001 0001 ^ 0100 1000 = 1101 1001
  x & 1 = 1 (odd parity) ✓
```

---

## 11. Arithmetic via Bitwise Operations

Understanding how arithmetic maps to bits deepens your mental model of how CPUs work.

### 11.1 Addition (Half Adder / Full Adder)

```
Half adder (no carry-in):
  A B | Sum  Carry
  0 0 |  0     0
  0 1 |  1     0
  1 0 |  1     0
  1 1 |  0     1

  sum   = A ^ B       (XOR)
  carry = A & B       (AND)

Full adder (with carry-in Cin):
  sum   = A ^ B ^ Cin
  carry = (A & B) | (B & Cin) | (A & Cin)

Ripple-carry adder for multi-bit:
  Bit 0: half adder     -> sum[0], carry[0]
  Bit 1: full adder     -> sum[1], carry[1]
  Bit 2: full adder     -> sum[2], carry[2]
  ...
  Bit n: full adder     -> sum[n], carry_out (overflow)

Adding 6 + 5 = 11 in 4-bit binary:
    0110  (6)
  + 0101  (5)
  ------
    1011  (11)

Carry chain:
  Bit 0: 0+1+0 = 1, carry=0
  Bit 1: 1+0+0 = 1, carry=0
  Bit 2: 1+1+0 = 0, carry=1
  Bit 3: 0+0+1 = 1, carry=0
```

### 11.2 Subtraction via Two's Complement

```
a - b = a + (-b) = a + (~b + 1)

So: a - b can be implemented with:
  1. Bitwise NOT of b
  2. Add 1 (increment)
  3. Add to a

6 - 4:
  4  =  0100
  ~4 =  1011
  -4 =  1100  (add 1)
  6  =  0110
  6+(-4) = 0110 + 1100 = 10010 -> (discard carry) -> 0010 = 2 ✓
```

### 11.3 Multiplication (Shift and Add)

```
Shift-and-add multiplication:
  a * b = sum of (a << i) for each bit i in b that is set

Example: 5 * 6:
  5 = 0b0101
  6 = 0b0110  (bits 1 and 2 are set)

  5 << 1 = 10   (bit 1 of 6 is set)
  5 << 2 = 20   (bit 2 of 6 is set)
  sum = 10 + 20 = 30 ✓

Pseudocode:
  result = 0
  while b > 0:
    if b & 1:
      result += a
    a <<= 1
    b >>= 1
```

### 11.4 Division (Shift and Subtract / Bit-by-Bit)

```
Integer division (unsigned):
  For divisor that is a power of 2: x / 2^n = x >> n

For general division (restoring division):
  quotient = 0
  for i from (n-1) downto 0:
    if dividend >= (divisor << i):
      quotient |= (1 << i)
      dividend -= (divisor << i)
  remainder = dividend
```

---

## 12. Bitsets and Bitmaps

A **bitset** (or bitmap) stores a large collection of bits efficiently — one bit per element — instead of one byte or word per element.

### Memory Layout

```
bitset of 64 elements, stored as two 32-bit words:

  Element index: 63 62 ... 33 32 | 31 30 ... 1 0
  Word index:         [1]        |       [0]

  To find element i:
    word  = i / 32     (or i >> 5)
    bit   = i % 32     (or i & 31)

  bits[word] |= (1u << bit)   // set element i
  bits[word] &= ~(1u << bit)  // clear element i
  (bits[word] >> bit) & 1     // test element i
```

### Bitset Operations (whole-set)

```
Two bitsets A and B of same size (n words each):

  Union (A | B):       for each i: result[i] = A[i] | B[i]
  Intersection (A & B):for each i: result[i] = A[i] & B[i]
  Difference (A - B):  for each i: result[i] = A[i] & ~B[i]
  Complement (~A):     for each i: result[i] = ~A[i]
  Count set bits:      sum of popcount(A[i]) for each i
```

### Bitset Example: Sieve of Eratosthenes

```
Find all primes up to N using a bitset:

  bits array = 1 bit per number (0=composite, 1=prime)

  Memory:
    N=1000000 primes:   ~125 KB using bitset
                        ~1 MB using byte array
                        ~4 MB using int array

  Algorithm:
    Set all bits = 1 (all "prime")
    Clear bit 0, bit 1 (not prime)
    For p = 2 to sqrt(N):
      if bit[p] is set (p is prime):
        for j = p*p, p*p+p, p*p+2p ...:
          clear bit[j]
```

---

## 13. Floating-Point Bit Representation

Understanding IEEE 754 float layout lets you apply bitwise operations on floats directly.

### IEEE 754 Single Precision (float, 32-bit)

```
 31  30        23 22                    0
+---+----------+------------------------+
| S |  Exponent|       Mantissa         |
| 1 |  8 bits  |       23 bits          |
+---+----------+------------------------+

S = sign bit (0 = positive, 1 = negative)
Exponent = biased by 127 (stored = actual + 127)
Mantissa = fractional part (implicit leading 1)

Value = (-1)^S * 1.Mantissa * 2^(Exponent - 127)

Examples:
  1.0:
    S=0, Exp=127 (0111 1111), Mantissa=0
    = 0 01111111 00000000000000000000000
    = 0x3F800000

  -2.0:
    S=1, Exp=128 (1000 0000), Mantissa=0
    = 1 10000000 00000000000000000000000
    = 0xC0000000

  0.5:
    S=0, Exp=126 (0111 1110), Mantissa=0
    = 0 01111110 00000000000000000000000
    = 0x3F000000
```

### Fast Inverse Square Root (Quake III Hack)

```
The famous Q_rsqrt:
  float rsqrt(float x) {
      long i = *(long*)&x;           // reinterpret float bits as int
      i = 0x5F3759DF - (i >> 1);    // magic initial approximation
      float y = *(float*)&i;         // reinterpret int bits as float
      y = y * (1.5f - 0.5f*x*y*y); // Newton-Raphson refinement
      return y;
  }

Why it works:
  log2(rsqrt(x)) = -0.5 * log2(x)
  The float bit pattern of x encodes approximately log2(x) (scaled and biased).
  So (i >> 1) halves the log2, and the magic constant adjusts the bias.
```

### IEEE 754 Double Precision (double, 64-bit)

```
 63  62          52 51                                          0
+---+-------------+----------------------------------------------+
| S |   Exponent  |                 Mantissa                     |
| 1 |   11 bits   |                 52 bits                      |
+---+-------------+----------------------------------------------+

Bias = 1023
Range: ~5e-324 to ~1.8e308
Precision: ~15-17 significant decimal digits
```

### Special Float Values

```
Value           Sign    Exponent    Mantissa
+Infinity        0    1111 1111    00...0
-Infinity        1    1111 1111    00...0
+NaN             0    1111 1111    nonzero
-NaN             1    1111 1111    nonzero
+Zero            0    0000 0000    00...0
-Zero            1    0000 0000    00...0
Subnormal      any    0000 0000    nonzero

Check for infinity: (bits & 0x7FFFFFFF) == 0x7F800000
Check for NaN:      (bits & 0x7FFFFFFF) > 0x7F800000
```

---

## 14. Signed vs Unsigned: Pitfalls

### Undefined Behavior in C (Critical!)

```c
// In C, signed integer overflow is UNDEFINED BEHAVIOR
// The compiler can assume it never happens and optimize accordingly.

// DANGEROUS (signed left shift overflow = UB):
int x = 1 << 31;    // UB! shifting into sign bit

// SAFE (use unsigned):
unsigned int x = 1u << 31;   // OK

// DANGEROUS (signed arithmetic overflow = UB):
int a = INT_MAX;
int b = a + 1;     // UB!

// SAFE:
unsigned int a = UINT_MAX;
unsigned int b = a + 1;   // wraps to 0, well-defined
```

### Arithmetic vs Logical Right Shift in C

```c
// In C, right shift of signed integers is IMPLEMENTATION-DEFINED
// (usually arithmetic on all major platforms/compilers, but not guaranteed)

int a = -8;          // 0b11111000 in 8-bit
int b = a >> 2;      // implementation-defined (-2 on most platforms)

// SAFE: use unsigned for logical (guaranteed zero-fill):
unsigned int u = (unsigned int)a;
unsigned int v = u >> 2;   // always logical right shift

// In Rust: signed >> is arithmetic, unsigned >> is logical (defined)
// In Go:   signed >> is arithmetic, unsigned >> is logical (defined)
```

### Integer Promotion Rules (C)

```c
// In C expressions, integers narrower than int are promoted to int first!

uint8_t a = 200;
uint8_t b = 200;
uint8_t c = a + b;   // a and b promoted to int! 400 mod 256 = 144
                     // This is fine (wraps on assignment back)

// But this can be surprising with bitwise NOT:
uint8_t x = 0xFF;
uint8_t y = ~x;      // ~x is computed as ~(int)0xFF = 0xFFFFFF00
                     // then truncated to uint8_t = 0x00... OK
// But:
if (~x == 0) { ... }  // FALSE! ~x as int = 0xFFFFFF00 != 0
```

### Mixing Signed and Unsigned (Silent Bug)

```c
int a = -1;
unsigned int b = 1;

if (a < b) { ... }   // WRONG! a is converted to unsigned: (unsigned)-1 = 4294967295 > 1!
                     // The branch is NOT taken.

// Always cast explicitly when mixing:
if ((unsigned int)a < b) { ... }   // explicit intent
```

---

## 15. Platform and Language Differences

### Integer Width Gotchas

```
Type     C/C++       Go          Rust
int      platform!   (no int)    (no int)
long     platform!   (no long)   (no long)
size_t   platform    (no)        usize
int32_t  32-bit       int32       i32
uint64_t 64-bit       uint64      u64
uintptr  uintptr_t   uintptr     usize

C `int` on 64-bit platform = 32 bits (NOT 64!)
C `long` on Linux 64-bit = 64 bits, on Windows 64-bit = 32 bits!

Always use fixed-width types for bitwise work:
  C:    #include <stdint.h>  -> int32_t, uint64_t, ...
  Go:   int32, uint64, ...   (explicit)
  Rust: i32, u64, ...        (always explicit)
```

### Operator Differences

```
Operation        C          Go         Rust
Bitwise AND      &          &          &
Bitwise OR       |          |          |
Bitwise XOR      ^          ^          ^
Bitwise NOT      ~          ^          !     <- Rust uses !
Left shift       <<         <<         <<
Right shift      >>         >>         >>
Unsigned rshift  >> (cast)  >> (uint)  >> (u-type)

NOTE: In Go, ^ is also the unary NOT operator (no separate ~ symbol).
NOTE: In Rust, ! is the bitwise NOT for integers.
```

### Overflow Behavior

```
Language    Default signed overflow    Wrapping behavior
C           UNDEFINED BEHAVIOR         Use unsigned types
Go          Wraps (defined)            Always wraps
Rust        Panic in debug mode        Use .wrapping_*() methods in release

Rust safe wrapping:
  a.wrapping_add(b)      // add with defined wrap
  a.wrapping_shl(n)      // shift with wrap
  a.checked_add(b)       // returns Option<T>
  a.saturating_add(b)    // clamps to MAX/MIN
  a.overflowing_add(b)   // returns (result, did_overflow)
```

---

## 16. Performance and Compiler Behavior

### Bit Operations vs Arithmetic

```
CPU instruction cost (modern x86, approximate cycles):

Operation       Cycles
AND/OR/XOR      1       (same as add)
NOT             1
Shift           1
Multiply        3-5
Divide          20-90   <- very slow!
Branch          0 (predicted) / 15+ (mispredicted)

Key optimizations:
  x * 2    ->  x << 1           (compiler often does this automatically)
  x / 4    ->  x >> 2           (for unsigned; compiler does this)
  x % 16   ->  x & 15           (compiler does this for unsigned)
  x * 9    ->  (x << 3) + x     (multiply by non-power-of-2)
```

### Branchless Code and CPUs

```
Modern CPUs use branch prediction. A mispredicted branch costs ~15 cycles.
Branchless bitwise alternatives avoid this:

Branchless:  mask = -(x < 0);      // 0 or all-ones based on condition
             result = (a & mask) | (b & ~mask);

vs:          if (x < 0) result = a; else result = b;

The branchless version is often faster when the condition is unpredictable.
When the condition is predictable, the branch version may be faster.
```

### Compiler Auto-Vectorization

```
Bitwise operations on arrays are ideal for SIMD (Single Instruction, Multiple Data):

  // Processing 4 x 32-bit values at once with SSE2 (128-bit registers):
  __m128i a = _mm_load_si128(...);
  __m128i b = _mm_load_si128(...);
  __m128i r = _mm_and_si128(a, b);   // 4 ANDs in one instruction

  // With AVX2 (256-bit registers): 8 x 32-bit at once
  // With AVX-512 (512-bit): 16 x 32-bit at once

Modern compilers auto-vectorize simple loops:
  for (int i = 0; i < n; i++) c[i] = a[i] & b[i];
  // -> compiler generates SIMD instructions automatically
```

### Compiler Output Examples

```
// C source:
int mod8(int x) { return x & 7; }
// Compiler output (x86-64):
//   and eax, 7
//   ret

int isPow2(unsigned x) { return x && !(x & (x-1)); }
// Compiler output:
//   test edi, edi
//   je .L2
//   lea eax, [rdi-1]
//   test edi, eax
//   sete al
//   movzx eax, al
//   ret

// Rust's count_ones() compiles to POPCNT instruction:
let n: u32 = x.count_ones();
// -> popcnt eax, edi
```

---

## 17. Real-World Applications

### 17.1 Network Protocol Parsing

```
TCP/IP Header parsing uses bitwise operations extensively:

IPv4 Flags field (in IP header, 3 bits):
  bit 0 (reserved, must be 0)
  bit 1 (DF = Don't Fragment)
  bit 2 (MF = More Fragments)

  uint16_t flags_fragment = ntohs(ip->frag_off);
  int df = (flags_fragment >> 14) & 1;
  int mf = (flags_fragment >> 13) & 1;
  uint16_t frag_offset = flags_fragment & 0x1FFF;

TCP flags (8 bits in TCP header):
  #define TCP_FIN  0x01
  #define TCP_SYN  0x02
  #define TCP_RST  0x04
  #define TCP_PSH  0x08
  #define TCP_ACK  0x10
  #define TCP_URG  0x20
  #define TCP_ECE  0x40
  #define TCP_CWR  0x80

  uint8_t flags = tcp_header->flags;
  bool is_syn_ack = (flags & (TCP_SYN | TCP_ACK)) == (TCP_SYN | TCP_ACK);
```

### 17.2 Bloom Filter

```
A Bloom filter tests set membership with NO false negatives and
a tunable false-positive rate, using O(m) bits for m-bit filter.

Structure:
  - m-bit array (= m/8 bytes)
  - k hash functions

  +---+---+---+---+---+---+---+---+---+---+...
  | 0 | 1 | 0 | 1 | 0 | 0 | 1 | 0 | 1 | 0 |...   <- bit array
  +---+---+---+---+---+---+---+---+---+---+...
    0   1   2   3   4   5   6   7   8   9

Insert "hello":
  hash1("hello") = 3  -> set bit 3
  hash2("hello") = 6  -> set bit 6
  hash3("hello") = 8  -> set bit 8

Query "world":
  hash1("world") = 3  -> bit 3 set? YES
  hash2("world") = 2  -> bit 2 set? NO -> DEFINITELY NOT IN SET

Operations:
  Set bit i:   bits[i/8] |= (1 << (i%8))
  Test bit i:  (bits[i/8] >> (i%8)) & 1
```

### 17.3 Chess Engine Bitboards

```
In chess engines, each piece type and color has a 64-bit integer
where each bit represents a board square.

Board layout (LSB = a1, MSB = h8):
  8  56 57 58 59 60 61 62 63
  7  48 49 50 51 52 53 54 55
  6  40 41 42 43 44 45 46 47
  5  32 33 34 35 36 37 38 39
  4  24 25 26 27 28 29 30 31
  3  16 17 18 19 20 21 22 23
  2   8  9 10 11 12 13 14 15
  1   0  1  2  3  4  5  6  7
      a  b  c  d  e  f  g  h

Pawns (White):
  uint64_t white_pawns = 0x000000000000FF00; // rank 2

Pawn attacks:
  east_attacks = (white_pawns << 9) & NOT_A_FILE;
  west_attacks = (white_pawns << 7) & NOT_H_FILE;
  all_attacks  = east_attacks | west_attacks;

Find occupied squares (any piece):
  occupied = white_all | black_all;

Move generation = pure bitwise ops — extremely fast.
```

### 17.4 Hash Functions

```
Bit manipulation in FNV-1a hash:
  hash = FNV_OFFSET_BASIS (2166136261 for 32-bit)
  for each byte b:
      hash ^= b           // XOR with byte
      hash *= FNV_PRIME   // multiply (16777619 for 32-bit)

MurmurHash3 finalizer (avalanche mixing):
  h ^= h >> 16;
  h *= 0x85ebca6b;
  h ^= h >> 13;
  h *= 0xc2b2ae35;
  h ^= h >> 16;

These XOR+shift patterns ensure every input bit affects every output bit.
```

### 17.5 Graphics and Color Manipulation

```
Packed RGBA color: 0xRRGGBBAA

Extract channels:
  r = (color >> 24) & 0xFF;
  g = (color >> 16) & 0xFF;
  b = (color >>  8) & 0xFF;
  a = (color >>  0) & 0xFF;

Pack channels:
  color = (r << 24) | (g << 16) | (b << 8) | a;

Alpha blend (source over):
  // out = src * alpha + dst * (1 - alpha)
  // With integer approximation (alpha: 0-255):
  out_r = (src_r * alpha + dst_r * (255 - alpha)) >> 8;
```

### 17.6 Memory Alignment

```
Check alignment (alignment must be power of 2):
  is_aligned = (address & (alignment - 1)) == 0;

Round down to alignment:
  aligned = address & ~(alignment - 1);

Round up to alignment:
  aligned = (address + alignment - 1) & ~(alignment - 1);

Example: align 37 to 16-byte boundary:
  ~(16-1) = ~15 = 0xFFFFFFF0
  (37 + 15) & ~15 = 52 & 0xFFFFFFF0 = 48
  48 / 16 = 3 (the next multiple of 16 >= 37)
```

### 17.7 CRC (Cyclic Redundancy Check)

```
CRC uses XOR-based polynomial division over GF(2) (Galois Field of 2).

CRC-32 table-based implementation concept:
  For each byte b of input:
    crc = (crc >> 8) ^ table[(crc ^ b) & 0xFF];

The lookup table precomputes XOR with the CRC polynomial.
The polynomial 0xEDB88320 (reflected CRC-32) is used in Ethernet, ZIP, PNG.

Why bitwise: modulo-2 arithmetic (no carry) = XOR.
  Every "subtraction" in the polynomial division is an XOR.
```

---

## 18. Complete Implementation Reference (C, Go, Rust)

### C Implementation

```c
#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <limits.h>

// ─────────────────────────────────────────────────────────────────────────────
// Section 1: Basic Bit Operations
// ─────────────────────────────────────────────────────────────────────────────

// Set bit at position n
static inline uint32_t set_bit(uint32_t x, int n) {
    return x | (1u << n);
}

// Clear bit at position n
static inline uint32_t clear_bit(uint32_t x, int n) {
    return x & ~(1u << n);
}

// Toggle bit at position n
static inline uint32_t toggle_bit(uint32_t x, int n) {
    return x ^ (1u << n);
}

// Test bit at position n (returns 0 or 1)
static inline int test_bit(uint32_t x, int n) {
    return (x >> n) & 1;
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 2: Bit Counting and Finding
// ─────────────────────────────────────────────────────────────────────────────

// Count set bits (popcount) — Brian Kernighan's algorithm
int popcount_kernighan(uint32_t x) {
    int count = 0;
    while (x) {
        x &= x - 1;  // clear lowest set bit
        count++;
    }
    return count;
}

// Count set bits — SWAR parallel algorithm
int popcount_parallel(uint32_t x) {
    x = x - ((x >> 1) & 0x55555555u);
    x = (x & 0x33333333u) + ((x >> 2) & 0x33333333u);
    x = (x + (x >> 4)) & 0x0F0F0F0Fu;
    return (int)((x * 0x01010101u) >> 24);
}

// Count set bits — hardware instruction
int popcount_hw(uint32_t x) {
    return __builtin_popcount(x);
}

// Count trailing zeros
int trailing_zeros(uint32_t x) {
    return (x == 0) ? 32 : __builtin_ctz(x);
}

// Count leading zeros
int leading_zeros(uint32_t x) {
    return (x == 0) ? 32 : __builtin_clz(x);
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 3: Bit Tricks
// ─────────────────────────────────────────────────────────────────────────────

// Isolate the lowest set bit
static inline uint32_t lowest_set_bit(uint32_t x) {
    return x & (uint32_t)(-(int32_t)x);
}

// Clear the lowest set bit
static inline uint32_t clear_lowest_set_bit(uint32_t x) {
    return x & (x - 1);
}

// Check if x is a power of 2
static inline bool is_power_of_two(uint32_t x) {
    return x != 0 && (x & (x - 1)) == 0;
}

// Round up to next power of 2
uint32_t next_power_of_two(uint32_t x) {
    if (x == 0) return 1;
    x--;
    x |= x >> 1;
    x |= x >> 2;
    x |= x >> 4;
    x |= x >> 8;
    x |= x >> 16;
    return x + 1;
}

// Fast modulo for power-of-2 divisors
static inline uint32_t fast_mod(uint32_t x, uint32_t n) {
    // n must be a power of 2
    return x & (n - 1);
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 4: Bit Field Extraction and Insertion
// ─────────────────────────────────────────────────────────────────────────────

// Extract bits [low..high] from value (inclusive, 0-indexed)
uint32_t extract_bits(uint32_t value, int low, int high) {
    int width = high - low + 1;
    uint32_t mask = (width == 32) ? 0xFFFFFFFFu : ((1u << width) - 1);
    return (value >> low) & mask;
}

// Insert value into bits [low..high]
uint32_t insert_bits(uint32_t original, uint32_t field, int low, int high) {
    int width = high - low + 1;
    uint32_t mask = ((1u << width) - 1) << low;
    return (original & ~mask) | ((field << low) & mask);
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 5: Rotate
// ─────────────────────────────────────────────────────────────────────────────

uint32_t rotate_left(uint32_t x, int n) {
    n &= 31;  // safe mod 32
    return (x << n) | (x >> (32 - n));
}

uint32_t rotate_right(uint32_t x, int n) {
    n &= 31;
    return (x >> n) | (x << (32 - n));
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 6: Reverse Bits
// ─────────────────────────────────────────────────────────────────────────────

uint32_t reverse_bits(uint32_t x) {
    x = ((x & 0xAAAAAAAAu) >> 1)  | ((x & 0x55555555u) << 1);
    x = ((x & 0xCCCCCCCCu) >> 2)  | ((x & 0x33333333u) << 2);
    x = ((x & 0xF0F0F0F0u) >> 4)  | ((x & 0x0F0F0F0Fu) << 4);
    x = ((x & 0xFF00FF00u) >> 8)  | ((x & 0x00FF00FFu) << 8);
    return (x >> 16) | (x << 16);
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 7: Parity
// ─────────────────────────────────────────────────────────────────────────────

int parity(uint32_t x) {
    x ^= x >> 16;
    x ^= x >> 8;
    x ^= x >> 4;
    x ^= x >> 2;
    x ^= x >> 1;
    return x & 1;
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 8: Branchless Operations
// ─────────────────────────────────────────────────────────────────────────────

// Branchless absolute value (signed)
int32_t abs_branchless(int32_t x) {
    int32_t mask = x >> 31;
    return (x ^ mask) - mask;
}

// Branchless min (signed)
int32_t min_branchless(int32_t a, int32_t b) {
    return b + ((a - b) & ((a - b) >> 31));
}

// Branchless max (signed)
int32_t max_branchless(int32_t a, int32_t b) {
    return a - ((a - b) & ((a - b) >> 31));
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 9: XOR Swap
// ─────────────────────────────────────────────────────────────────────────────

void xor_swap(uint32_t *a, uint32_t *b) {
    if (a != b) {  // guard: must not be same memory location
        *a ^= *b;
        *b ^= *a;
        *a ^= *b;
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 10: Bitset (Dynamic, 64-element example)
// ─────────────────────────────────────────────────────────────────────────────

#define BITSET_WORDS 2   // 64 bits total
typedef struct {
    uint32_t words[BITSET_WORDS];
} Bitset64;

void bitset_set(Bitset64 *bs, int i) {
    bs->words[i / 32] |= (1u << (i % 32));
}

void bitset_clear(Bitset64 *bs, int i) {
    bs->words[i / 32] &= ~(1u << (i % 32));
}

bool bitset_test(const Bitset64 *bs, int i) {
    return (bs->words[i / 32] >> (i % 32)) & 1;
}

int bitset_popcount(const Bitset64 *bs) {
    return __builtin_popcount(bs->words[0]) +
           __builtin_popcount(bs->words[1]);
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 11: Packed Date Example
// ─────────────────────────────────────────────────────────────────────────────

typedef uint32_t PackedDate;

PackedDate date_pack(int year, int month, int day) {
    return ((uint32_t)year << 16) | ((uint32_t)month << 8) | (uint32_t)day;
}

int date_year(PackedDate d)  { return (int)((d >> 16) & 0xFFFF); }
int date_month(PackedDate d) { return (int)((d >> 8)  & 0xFF); }
int date_day(PackedDate d)   { return (int)((d >> 0)  & 0xFF); }

// ─────────────────────────────────────────────────────────────────────────────
// Section 12: Flags Example
// ─────────────────────────────────────────────────────────────────────────────

typedef enum {
    PERM_READ    = 1 << 0,
    PERM_WRITE   = 1 << 1,
    PERM_EXECUTE = 1 << 2,
    PERM_HIDDEN  = 1 << 3,
} Permission;

typedef uint8_t PermFlags;

PermFlags perm_set(PermFlags f, Permission p)    { return f | p; }
PermFlags perm_clear(PermFlags f, Permission p)  { return f & ~p; }
PermFlags perm_toggle(PermFlags f, Permission p) { return f ^ p; }
bool      perm_has(PermFlags f, Permission p)    { return (f & p) != 0; }

// ─────────────────────────────────────────────────────────────────────────────
// Section 13: CRC32 (table-less, bit-by-bit)
// ─────────────────────────────────────────────────────────────────────────────

uint32_t crc32_slow(const uint8_t *data, size_t len) {
    uint32_t crc = 0xFFFFFFFFu;
    for (size_t i = 0; i < len; i++) {
        crc ^= data[i];
        for (int j = 0; j < 8; j++) {
            if (crc & 1)
                crc = (crc >> 1) ^ 0xEDB88320u;  // reflected CRC-32 polynomial
            else
                crc >>= 1;
        }
    }
    return ~crc;
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 14: Demo Main
// ─────────────────────────────────────────────────────────────────────────────

int main(void) {
    uint32_t x = 0b10110100;
    printf("Value:            0x%08X (%u)\n", x, x);
    printf("Set bit 0:        0x%08X\n", set_bit(x, 0));
    printf("Clear bit 2:      0x%08X\n", clear_bit(x, 2));
    printf("Toggle bit 7:     0x%08X\n", toggle_bit(x, 7));
    printf("Test bit 4:       %d\n",     test_bit(x, 4));
    printf("Popcount:         %d\n",     popcount_hw(x));
    printf("Trailing zeros:   %d\n",     trailing_zeros(x));
    printf("Leading zeros:    %d\n",     leading_zeros(x));
    printf("Lowest set bit:   0x%08X\n", lowest_set_bit(x));
    printf("Is power of 2:    %s\n",     is_power_of_two(x) ? "yes" : "no");
    printf("Next pow2:        %u\n",     next_power_of_two(x));
    printf("Rotate left 3:    0x%08X\n", rotate_left(x, 3));
    printf("Reverse bits:     0x%08X\n", reverse_bits(x));
    printf("Parity:           %d\n",     parity(x));

    PackedDate d = date_pack(2024, 12, 25);
    printf("Packed date:      0x%08X -> %d/%d/%d\n",
           d, date_year(d), date_month(d), date_day(d));

    PermFlags p = 0;
    p = perm_set(p, PERM_READ | PERM_WRITE);
    p = perm_clear(p, PERM_WRITE);
    printf("Permissions:      0x%02X (read=%d, write=%d)\n",
           p, perm_has(p, PERM_READ), perm_has(p, PERM_WRITE));

    return 0;
}
```

---

### Go Implementation

```go
package main

import (
    "fmt"
    "math/bits"
)

// ─────────────────────────────────────────────────────────────────────────────
// Section 1: Basic Bit Operations
// ─────────────────────────────────────────────────────────────────────────────

func SetBit(x uint32, n int) uint32    { return x | (1 << n) }
func ClearBit(x uint32, n int) uint32  { return x &^ (1 << n) }  // &^ is bit-clear (AND NOT)
func ToggleBit(x uint32, n int) uint32 { return x ^ (1 << n) }
func TestBit(x uint32, n int) uint32   { return (x >> n) & 1 }

// ─────────────────────────────────────────────────────────────────────────────
// Section 2: Bit Counting and Finding
// ─────────────────────────────────────────────────────────────────────────────

// Popcount — hardware (via math/bits)
func Popcount(x uint32) int {
    return bits.OnesCount32(x)
}

// Count trailing zeros
func TrailingZeros(x uint32) int {
    return bits.TrailingZeros32(x)
}

// Count leading zeros
func LeadingZeros(x uint32) int {
    return bits.LeadingZeros32(x)
}

// Floor log2 (position of highest set bit)
func FloorLog2(x uint32) int {
    if x == 0 {
        return -1
    }
    return 31 - bits.LeadingZeros32(x)
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 3: Bit Tricks
// ─────────────────────────────────────────────────────────────────────────────

// Isolate the lowest set bit
func LowestSetBit(x uint32) uint32 {
    return x & uint32(-int32(x))
}

// Clear the lowest set bit
func ClearLowestSetBit(x uint32) uint32 {
    return x & (x - 1)
}

// Check if x is power of 2
func IsPowerOfTwo(x uint32) bool {
    return x != 0 && (x&(x-1)) == 0
}

// Next power of 2 (rounds up)
func NextPowerOfTwo(x uint32) uint32 {
    if x == 0 {
        return 1
    }
    x--
    x |= x >> 1
    x |= x >> 2
    x |= x >> 4
    x |= x >> 8
    x |= x >> 16
    return x + 1
}

// Fast modulo (n must be power of 2)
func FastMod(x, n uint32) uint32 {
    return x & (n - 1)
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 4: Bit Field Extraction and Insertion
// ─────────────────────────────────────────────────────────────────────────────

// Extract bits [low..high] inclusive
func ExtractBits(value uint32, low, high int) uint32 {
    width := high - low + 1
    var mask uint32
    if width == 32 {
        mask = 0xFFFFFFFF
    } else {
        mask = (1 << width) - 1
    }
    return (value >> low) & mask
}

// Insert field into bits [low..high]
func InsertBits(original, field uint32, low, high int) uint32 {
    width := high - low + 1
    mask := uint32((1<<width)-1) << low
    return (original &^ mask) | ((field << low) & mask)
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 5: Rotate (via math/bits)
// ─────────────────────────────────────────────────────────────────────────────

func RotateLeft(x uint32, n int) uint32  { return bits.RotateLeft32(x, n) }
func RotateRight(x uint32, n int) uint32 { return bits.RotateLeft32(x, -n) }

// ─────────────────────────────────────────────────────────────────────────────
// Section 6: Reverse Bits
// ─────────────────────────────────────────────────────────────────────────────

func ReverseBits(x uint32) uint32 {
    return bits.Reverse32(x)
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 7: Parity
// ─────────────────────────────────────────────────────────────────────────────

func Parity(x uint32) int {
    x ^= x >> 16
    x ^= x >> 8
    x ^= x >> 4
    x ^= x >> 2
    x ^= x >> 1
    return int(x & 1)
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 8: Branchless Operations
// ─────────────────────────────────────────────────────────────────────────────

// Branchless absolute value
func AbsBranchless(x int32) int32 {
    mask := x >> 31
    return (x ^ mask) - mask
}

// Branchless min
func MinBranchless(a, b int32) int32 {
    diff := a - b
    return b + (diff & (diff >> 31))
}

// Branchless max
func MaxBranchless(a, b int32) int32 {
    diff := a - b
    return a - (diff & (diff >> 31))
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 9: XOR Swap (pointer-based)
// ─────────────────────────────────────────────────────────────────────────────

func XorSwap(a, b *uint32) {
    if a != b {
        *a ^= *b
        *b ^= *a
        *a ^= *b
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 10: Bitset (64-element)
// ─────────────────────────────────────────────────────────────────────────────

type Bitset64 [2]uint32

func (b *Bitset64) Set(i int)          { b[i/32] |= 1 << (i % 32) }
func (b *Bitset64) Clear(i int)        { b[i/32] &^= 1 << (i % 32) }
func (b *Bitset64) Test(i int) bool    { return (b[i/32]>>(i%32))&1 == 1 }
func (b *Bitset64) Popcount() int      { return bits.OnesCount32(b[0]) + bits.OnesCount32(b[1]) }
func (b *Bitset64) Union(o Bitset64)   { b[0] |= o[0]; b[1] |= o[1] }
func (b *Bitset64) Intersect(o Bitset64) { b[0] &= o[0]; b[1] &= o[1] }

// ─────────────────────────────────────────────────────────────────────────────
// Section 11: Packed Date
// ─────────────────────────────────────────────────────────────────────────────

type PackedDate uint32

func PackDate(year, month, day int) PackedDate {
    return PackedDate(uint32(year)<<16 | uint32(month)<<8 | uint32(day))
}

func (d PackedDate) Year() int  { return int((d >> 16) & 0xFFFF) }
func (d PackedDate) Month() int { return int((d >> 8) & 0xFF) }
func (d PackedDate) Day() int   { return int(d & 0xFF) }

// ─────────────────────────────────────────────────────────────────────────────
// Section 12: Permission Flags
// ─────────────────────────────────────────────────────────────────────────────

type Permission uint8

const (
    PermRead    Permission = 1 << 0
    PermWrite   Permission = 1 << 1
    PermExecute Permission = 1 << 2
    PermHidden  Permission = 1 << 3
)

type PermFlags uint8

func (f PermFlags) Set(p Permission) PermFlags    { return f | PermFlags(p) }
func (f PermFlags) Clear(p Permission) PermFlags  { return f &^ PermFlags(p) }
func (f PermFlags) Toggle(p Permission) PermFlags { return f ^ PermFlags(p) }
func (f PermFlags) Has(p Permission) bool         { return (f & PermFlags(p)) != 0 }

// ─────────────────────────────────────────────────────────────────────────────
// Section 13: CRC32 (slow, no table)
// ─────────────────────────────────────────────────────────────────────────────

func CRC32Slow(data []byte) uint32 {
    crc := uint32(0xFFFFFFFF)
    for _, b := range data {
        crc ^= uint32(b)
        for j := 0; j < 8; j++ {
            if crc&1 != 0 {
                crc = (crc >> 1) ^ 0xEDB88320
            } else {
                crc >>= 1
            }
        }
    }
    return ^crc
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 14: Find single non-duplicate in array (XOR trick)
// ─────────────────────────────────────────────────────────────────────────────

// All elements appear twice except one. Find the single element.
func FindUnique(nums []int) int {
    result := 0
    for _, n := range nums {
        result ^= n
    }
    return result
    // XOR of a^a = 0, so all duplicates cancel, leaving the unique value.
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Demo
// ─────────────────────────────────────────────────────────────────────────────

func main() {
    x := uint32(0b10110100)
    fmt.Printf("Value:            0x%08X (%d)\n", x, x)
    fmt.Printf("Set bit 0:        0x%08X\n", SetBit(x, 0))
    fmt.Printf("Clear bit 2:      0x%08X\n", ClearBit(x, 2))
    fmt.Printf("Toggle bit 7:     0x%08X\n", ToggleBit(x, 7))
    fmt.Printf("Test bit 4:       %d\n", TestBit(x, 4))
    fmt.Printf("Popcount:         %d\n", Popcount(x))
    fmt.Printf("Trailing zeros:   %d\n", TrailingZeros(x))
    fmt.Printf("Leading zeros:    %d\n", LeadingZeros(x))
    fmt.Printf("Lowest set bit:   0x%08X\n", LowestSetBit(x))
    fmt.Printf("Is power of 2:    %v\n", IsPowerOfTwo(x))
    fmt.Printf("Next pow2:        %d\n", NextPowerOfTwo(x))
    fmt.Printf("Rotate left 3:    0x%08X\n", RotateLeft(x, 3))
    fmt.Printf("Reverse bits:     0x%08X\n", ReverseBits(x))
    fmt.Printf("Parity:           %d\n", Parity(x))
    fmt.Printf("Floor log2:       %d\n", FloorLog2(x))

    d := PackDate(2024, 12, 25)
    fmt.Printf("Packed date:      0x%08X -> %d/%d/%d\n", uint32(d), d.Year(), d.Month(), d.Day())

    var perms PermFlags
    perms = perms.Set(PermRead | PermWrite)
    perms = perms.Clear(PermWrite)
    fmt.Printf("Permissions:      0x%02X (read=%v, write=%v)\n",
        perms, perms.Has(PermRead), perms.Has(PermWrite))

    nums := []int{4, 1, 2, 1, 2}
    fmt.Printf("Unique in array:  %d\n", FindUnique(nums))  // 4

    fmt.Printf("CRC32('hello'):   0x%08X\n", CRC32Slow([]byte("hello")))
}
```

---

### Rust Implementation

```rust
use std::fmt;

// ─────────────────────────────────────────────────────────────────────────────
// Section 1: Basic Bit Operations
// ─────────────────────────────────────────────────────────────────────────────

pub fn set_bit(x: u32, n: u32) -> u32    { x | (1 << n) }
pub fn clear_bit(x: u32, n: u32) -> u32  { x & !(1 << n) }  // ! is bitwise NOT in Rust
pub fn toggle_bit(x: u32, n: u32) -> u32 { x ^ (1 << n) }
pub fn test_bit(x: u32, n: u32) -> u32   { (x >> n) & 1 }

// ─────────────────────────────────────────────────────────────────────────────
// Section 2: Bit Counting and Finding (using Rust's built-in methods)
// ─────────────────────────────────────────────────────────────────────────────

pub fn popcount(x: u32) -> u32 {
    x.count_ones()                // maps to POPCNT instruction
}

pub fn trailing_zeros(x: u32) -> u32 {
    x.trailing_zeros()            // maps to TZCNT/BSF instruction
}

pub fn leading_zeros(x: u32) -> u32 {
    x.leading_zeros()             // maps to LZCNT/BSR instruction
}

pub fn floor_log2(x: u32) -> Option<u32> {
    if x == 0 { return None; }
    Some(31 - x.leading_zeros())
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 3: Bit Tricks
// ─────────────────────────────────────────────────────────────────────────────

pub fn lowest_set_bit(x: u32) -> u32 {
    x & x.wrapping_neg()          // x & -x using wrapping negation
}

pub fn clear_lowest_set_bit(x: u32) -> u32 {
    x & x.wrapping_sub(1)
}

pub fn is_power_of_two(x: u32) -> bool {
    x.is_power_of_two()           // built-in: x != 0 && (x & (x-1)) == 0
}

pub fn next_power_of_two(x: u32) -> u32 {
    x.next_power_of_two()         // built-in with overflow checking
}

pub fn fast_mod(x: u32, n: u32) -> u32 {
    // n must be a power of 2
    x & (n - 1)
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 4: Bit Field Extraction and Insertion
// ─────────────────────────────────────────────────────────────────────────────

pub fn extract_bits(value: u32, low: u32, high: u32) -> u32 {
    let width = high - low + 1;
    let mask = if width == 32 { u32::MAX } else { (1u32 << width) - 1 };
    (value >> low) & mask
}

pub fn insert_bits(original: u32, field: u32, low: u32, high: u32) -> u32 {
    let width = high - low + 1;
    let mask = ((1u32 << width) - 1) << low;
    (original & !mask) | ((field << low) & mask)
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 5: Rotate (built-in methods)
// ─────────────────────────────────────────────────────────────────────────────

pub fn rotate_left(x: u32, n: u32) -> u32  { x.rotate_left(n) }
pub fn rotate_right(x: u32, n: u32) -> u32 { x.rotate_right(n) }

// ─────────────────────────────────────────────────────────────────────────────
// Section 6: Reverse Bits (built-in)
// ─────────────────────────────────────────────────────────────────────────────

pub fn reverse_bits(x: u32) -> u32 {
    x.reverse_bits()
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 7: Parity
// ─────────────────────────────────────────────────────────────────────────────

pub fn parity(x: u32) -> u32 {
    x.count_ones() & 1   // parity = popcount mod 2
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 8: Branchless Operations
// ─────────────────────────────────────────────────────────────────────────────

pub fn abs_branchless(x: i32) -> i32 {
    let mask = x >> 31;
    (x ^ mask).wrapping_sub(mask)
}

pub fn min_branchless(a: i32, b: i32) -> i32 {
    let diff = a.wrapping_sub(b);
    b.wrapping_add(diff & (diff >> 31))
}

pub fn max_branchless(a: i32, b: i32) -> i32 {
    let diff = a.wrapping_sub(b);
    a.wrapping_sub(diff & (diff >> 31))
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 9: XOR Swap
// ─────────────────────────────────────────────────────────────────────────────

pub fn xor_swap(a: &mut u32, b: &mut u32) {
    *a ^= *b;
    *b ^= *a;
    *a ^= *b;
    // Note: Rust's borrow checker ensures a != b at the type level.
    // You cannot pass the same &mut twice, so no aliasing risk.
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 10: Bitset (64-element)
// ─────────────────────────────────────────────────────────────────────────────

#[derive(Default, Clone, Copy)]
pub struct Bitset64([u32; 2]);

impl Bitset64 {
    pub fn new() -> Self { Bitset64([0; 2]) }

    pub fn set(&mut self, i: usize) {
        self.0[i / 32] |= 1 << (i % 32);
    }

    pub fn clear(&mut self, i: usize) {
        self.0[i / 32] &= !(1 << (i % 32));
    }

    pub fn test(&self, i: usize) -> bool {
        (self.0[i / 32] >> (i % 32)) & 1 == 1
    }

    pub fn count(&self) -> u32 {
        self.0[0].count_ones() + self.0[1].count_ones()
    }

    pub fn union(&self, other: &Bitset64) -> Bitset64 {
        Bitset64([self.0[0] | other.0[0], self.0[1] | other.0[1]])
    }

    pub fn intersect(&self, other: &Bitset64) -> Bitset64 {
        Bitset64([self.0[0] & other.0[0], self.0[1] & other.0[1]])
    }

    pub fn complement(&self) -> Bitset64 {
        Bitset64([!self.0[0], !self.0[1]])
    }
}

impl fmt::Display for Bitset64 {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{:032b}{:032b}", self.0[1], self.0[0])
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 11: Packed Date
// ─────────────────────────────────────────────────────────────────────────────

#[derive(Clone, Copy)]
pub struct PackedDate(u32);

impl PackedDate {
    pub fn new(year: u32, month: u32, day: u32) -> Self {
        PackedDate((year << 16) | (month << 8) | day)
    }
    pub fn year(&self)  -> u32 { (self.0 >> 16) & 0xFFFF }
    pub fn month(&self) -> u32 { (self.0 >> 8) & 0xFF }
    pub fn day(&self)   -> u32 { self.0 & 0xFF }
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 12: Permission Flags
// ─────────────────────────────────────────────────────────────────────────────

bitflags::bitflags! {   // using the bitflags crate
    // Without bitflags crate, manual implementation below
}

// Manual flags implementation (no external crate):
#[derive(Clone, Copy, Default)]
pub struct PermFlags(u8);

impl PermFlags {
    pub const READ:    u8 = 1 << 0;
    pub const WRITE:   u8 = 1 << 1;
    pub const EXECUTE: u8 = 1 << 2;
    pub const HIDDEN:  u8 = 1 << 3;

    pub fn set(self, flag: u8) -> Self    { PermFlags(self.0 | flag) }
    pub fn clear(self, flag: u8) -> Self  { PermFlags(self.0 & !flag) }
    pub fn toggle(self, flag: u8) -> Self { PermFlags(self.0 ^ flag) }
    pub fn has(self, flag: u8) -> bool    { (self.0 & flag) != 0 }
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 13: CRC32 (slow, no table)
// ─────────────────────────────────────────────────────────────────────────────

pub fn crc32_slow(data: &[u8]) -> u32 {
    let mut crc: u32 = 0xFFFF_FFFF;
    for &byte in data {
        crc ^= byte as u32;
        for _ in 0..8 {
            if crc & 1 != 0 {
                crc = (crc >> 1) ^ 0xEDB88320;
            } else {
                crc >>= 1;
            }
        }
    }
    !crc
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 14: Find unique element (XOR trick)
// ─────────────────────────────────────────────────────────────────────────────

pub fn find_unique(nums: &[i32]) -> i32 {
    nums.iter().fold(0, |acc, &x| acc ^ x)
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 15: Overflow-safe arithmetic (Rust's type system enforces this)
// ─────────────────────────────────────────────────────────────────────────────

pub fn safe_shift_demo() {
    let x: u32 = 0xFF;

    // Panic in debug, wrap in release:
    // let _ = x << 33;  // PANICS: shift amount too large

    // Always safe:
    let wrapped = x.wrapping_shl(33);  // wraps shift amount: 33 % 32 = 1
    let checked = x.checked_shl(33);   // returns None
    let _sat    = x.saturating_shl(33); // saturates to 0

    println!("wrapping_shl(33): {wrapped}");
    println!("checked_shl(33):  {:?}", checked);
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 16: Byte Swap / Endianness Conversion
// ─────────────────────────────────────────────────────────────────────────────

pub fn endianness_demo() {
    let x: u32 = 0xDEADBEEF;

    let be = x.to_be();              // convert to big-endian
    let le = x.to_le();              // convert to little-endian
    let swapped = x.swap_bytes();    // reverse byte order

    let from_be = u32::from_be(be);  // convert from big-endian
    let from_le = u32::from_le(le);  // convert from little-endian

    println!("Original:       0x{x:08X}");
    println!("Swap bytes:     0x{swapped:08X}");
    println!("To BE, back:    0x{from_be:08X}");
    println!("To LE, back:    0x{from_le:08X}");
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Demo
// ─────────────────────────────────────────────────────────────────────────────

fn main() {
    let x: u32 = 0b10110100;

    println!("Value:            0x{x:08X} ({x})");
    println!("Set bit 0:        0x{:08X}", set_bit(x, 0));
    println!("Clear bit 2:      0x{:08X}", clear_bit(x, 2));
    println!("Toggle bit 7:     0x{:08X}", toggle_bit(x, 7));
    println!("Test bit 4:       {}", test_bit(x, 4));
    println!("Popcount:         {}", popcount(x));
    println!("Trailing zeros:   {}", trailing_zeros(x));
    println!("Leading zeros:    {}", leading_zeros(x));
    println!("Lowest set bit:   0x{:08X}", lowest_set_bit(x));
    println!("Is power of 2:    {}", is_power_of_two(x));
    println!("Next pow2:        {}", next_power_of_two(x));
    println!("Rotate left 3:    0x{:08X}", rotate_left(x, 3));
    println!("Reverse bits:     0x{:08X}", reverse_bits(x));
    println!("Parity:           {}", parity(x));
    println!("Floor log2:       {:?}", floor_log2(x));

    let d = PackedDate::new(2024, 12, 25);
    println!("Packed date:      0x{:08X} -> {}/{}/{}", d.0, d.year(), d.month(), d.day());

    let mut perms = PermFlags::default();
    perms = perms.set(PermFlags::READ | PermFlags::WRITE);
    perms = perms.clear(PermFlags::WRITE);
    println!("Permissions:      0x{:02X} (read={}, write={})",
             perms.0, perms.has(PermFlags::READ), perms.has(PermFlags::WRITE));

    let nums = vec![4, 1, 2, 1, 2];
    println!("Unique in array:  {}", find_unique(&nums));

    println!("CRC32('hello'):   0x{:08X}", crc32_slow(b"hello"));

    safe_shift_demo();
    endianness_demo();

    // Demonstrate Rust's safe overflow operations
    let a: u32 = u32::MAX;
    println!("MAX + 1 (wrapping): {}", a.wrapping_add(1));  // 0
    println!("MAX + 1 (checked):  {:?}", a.checked_add(1)); // None
    println!("MAX + 1 (saturate): {}", a.saturating_add(1)); // 4294967295

    // Bitset demo
    let mut bs = Bitset64::new();
    bs.set(0);
    bs.set(7);
    bs.set(63);
    println!("Bitset:    {bs}");
    println!("Count:     {}", bs.count());
    println!("Test[7]:   {}", bs.test(7));
}
```

---

## 19. Mental Models Summary

### The 6-Operator Mental Model

```
  AND  (&)   -> MASK / FILTER   (keep only what you want)
  OR   (|)   -> MERGE / SET     (turn bits on, combine)
  XOR  (^)   -> TOGGLE / DIFF   (flip what differs, find differences)
  NOT  (~,!) -> INVERT          (complement, flip everything)
  SHL  (<<)  -> MULTIPLY by 2^n (shift left = scale up)
  SHR  (>>)  -> DIVIDE by 2^n   (shift right = scale down)
```

### The Bit Manipulation Cheat Sheet

```
Operation                  Expression           Notes
─────────────────────────────────────────────────────────────────────
Set bit n                  x |= (1 << n)
Clear bit n                x &= ~(1 << n)
Toggle bit n               x ^= (1 << n)
Test bit n                 (x >> n) & 1
Isolate lowest set bit     x & -x              (x & (~x+1))
Clear lowest set bit       x & (x-1)
Check power of 2           x && !(x & (x-1))
Mod by power of 2          x & (n-1)            n must be pow2
Multiply by 2              x << 1
Divide by 2 (unsigned)     x >> 1
Sign of x (signed)         x >> (bits-1)        all 1s or all 0s
Absolute value             (x^mask) - mask      mask = x>>(bits-1)
Min(a,b) branchless        b + ((a-b) & (a-b)>>(bits-1))
Swap a,b (no temp)         a^=b; b^=a; a^=b    NOT for same addr
Pack two 16-bit values     (hi << 16) | lo
Unpack high 16 bits        (x >> 16) & 0xFFFF
Unpack low 16 bits         x & 0xFFFF
Next power of 2            use clz or loop
Reverse bits               SWAR 5-step algo
Popcount                   SWAR or hardware
Count trailing zeros       hardware ctz
Count leading zeros        hardware clz
Rotate left (n-bit by k)   (x<<k) | (x>>(n-k))
Parity                     fold XOR, test LSB
```

### Key Insights for Deep Understanding

```
1. EVERYTHING is bits. All values — integers, floats, pointers,
   structs — are stored as sequences of bits in memory.

2. Two's complement enables a single adder to handle signed
   and unsigned numbers. Addition, subtraction, and sign
   handling unify under the same hardware.

3. AND clears bits; OR sets bits; XOR flips bits.
   These three are the "write" operations on specific positions.

4. x & -x isolates the single lowest set bit — a gateway
   to most efficient bit manipulation algorithms.

5. x & (x-1) removes the lowest set bit — the foundation
   of O(k) popcount where k = number of set bits.

6. Left shift is fast multiplication; right shift is fast
   division. The CPU does this in one cycle vs 20-90 for divide.

7. XOR's self-inverse property (a^b^b = a) makes it useful
   for encryption, checksums, and finding unique elements.

8. Masks are the abstraction layer between bit positions
   and logical meaning. Always name your masks.

9. Use unsigned types for bitwise operations in C. Signed
   overflow is undefined behavior; unsigned overflow wraps.

10. Hardware intrinsics (popcount, lzcnt, tzcnt, rotate) are
    single instructions — always prefer the language's built-in
    methods over manual implementations.
```

### Bit Reasoning Framework

```
When you see a bitwise expression, ask:

  Which bits are being SELECTED?   -> look at the AND mask
  Which bits are being FORCED ON?  -> look at the OR mask
  Which bits are being FLIPPED?    -> look at the XOR mask
  How is data being SCALED?        -> look at the shifts
  What is the SIGN doing?          -> check type and MSB

When you design a bit structure, decide:

  What is the bit width needed for each field?
  Which field occupies which bit range?
  What mask and shift is needed to extract/insert each field?
  Is this field signed or unsigned?
  Will this be read on multiple platforms? -> be explicit about endianness
```

---

*This guide covers every fundamental concept in bitwise operations. Internalize the mental models in Section 19, practice the cheat sheet until it's second nature, and you will be able to think efficiently at the machine level for any problem involving raw bits: protocols, compression, hashing, graphics, cryptography, embedded systems, and high-performance computing.*
