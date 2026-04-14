# One's Complement & Two's Complement — A Complete, In-Depth Guide

> *"Computers don't understand negative numbers by magic — they are tricked by brilliant mathematical design."*

---

## Table of Contents

1. [Prerequisites — Binary Number System Deep Dive](#1-prerequisites--binary-number-system-deep-dive)
2. [The Core Problem — Representing Negative Numbers](#2-the-core-problem--representing-negative-numbers)
3. [Sign-Magnitude Representation (Naive Approach)](#3-sign-magnitude-representation-naive-approach)
4. [One's Complement](#4-ones-complement)
5. [Two's Complement](#5-twos-complement)
6. [Arithmetic Operations](#6-arithmetic-operations)
7. [Overflow Detection](#7-overflow-detection)
8. [Bit Manipulation Tricks Powered by Two's Complement](#8-bit-manipulation-tricks-powered-by-twos-complement)
9. [Edge Cases and Gotchas](#9-edge-cases-and-gotchas)
10. [Implementations in C, Go, and Rust](#10-implementations-in-c-go-and-rust)
11. [Mental Models and Visual Summary](#11-mental-models-and-visual-summary)

---

## 1. Prerequisites — Binary Number System Deep Dive

Before we can understand negative binary numbers, you must have absolute clarity on *positive* binary numbers.

### What is a Bit?

A **bit** (binary digit) is the smallest unit of data. It can be either `0` or `1`.

### What is a Byte?

A **byte** is 8 bits grouped together.

```
Byte example:
  Bit position:  7   6   5   4   3   2   1   0
  Bit value:     1   0   1   1   0   0   1   1
```

### Positional Value (Unsigned)

Each bit has a **positional value** — a power of 2 based on its position from the right (starting at position 0).

```
Positional Weight Table (8-bit):
+----------+----+----+----+----+---+---+---+---+
| Position |  7 |  6 |  5 |  4 | 3 | 2 | 1 | 0 |
+----------+----+----+----+----+---+---+---+---+
| Weight   |128 | 64 | 32 | 16 | 8 | 4 | 2 | 1 |
+----------+----+----+----+----+---+---+---+---+
```

**Example**: Convert `10110011` to decimal:

```
Bit:     1    0    1    1    0    0    1    1
Weight: 128   64   32   16    8    4    2    1

Sum = 128 + 0 + 32 + 16 + 0 + 0 + 2 + 1 = 179
```

### Number Range for N Bits (Unsigned)

For **N** bits:
- Minimum value = **0**
- Maximum value = **2^N - 1**

```
N=4 bits:  0000 to 1111  =>  0 to 15   (2^4 - 1 = 15)
N=8 bits:  00000000 to 11111111  =>  0 to 255
N=16 bits: 0 to 65535
N=32 bits: 0 to 4,294,967,295
N=64 bits: 0 to 18,446,744,073,709,551,615
```

---

## 2. The Core Problem — Representing Negative Numbers

A computer fundamentally only stores `0`s and `1`s. There's no dedicated "minus sign" wire.

**The question is:** *How do we encode negative numbers using only bits?*

We have **three historical approaches**:

```
Approaches to Represent Signed Integers:
+---------------------------+
|   Sign-Magnitude          |  <-- Naive, simple but flawed
+---------------------------+
|   One's Complement        |  <-- Better, still has a flaw
+---------------------------+
|   Two's Complement        |  <-- Industry standard (used in all modern CPUs)
+---------------------------+
```

---

## 3. Sign-Magnitude Representation (Naive Approach)

### Concept

Dedicate the **most significant bit (MSB)** — the leftmost bit — as a **sign bit**.

```
Sign-Magnitude Layout (8-bit):
+-----+----------------------------------+
| MSB |     Remaining 7 bits             |
+-----+----------------------------------+
|  0  |     Magnitude (positive)         |
|  1  |     Magnitude (negative)         |
+-----+----------------------------------+
```

### Examples

```
+5  =>  0 0000101
-5  =>  1 0000101
        ^
        Sign bit (1 = negative)

+0  =>  0 0000000
-0  =>  1 0000000   <-- PROBLEM: Two representations of zero!
```

### Range (8-bit Sign-Magnitude)

```
Range: -127 to +127
       (Not -128, because -0 and +0 waste one slot)
```

### The Fatal Flaws

#### Flaw 1: Two Zeros (+0 and -0)

```
+0 = 00000000
-0 = 10000000

These are logically the SAME value, but have two different bit patterns.
This wastes a code point and forces hardware to handle two zeros.
```

#### Flaw 2: Addition Doesn't Work Naturally

```
Let's try: +5 + (-3) = +2

+5  =>  00000101
-3  =>  10000011
        --------
Sum =>  10001000  = -8  (WRONG! Expected +2)
```

The hardware would need **special logic** to detect mixed signs and handle subtraction manually. This makes the ALU (Arithmetic Logic Unit) complex and slow.

### Sign-Magnitude Decision Tree

```
Is the number negative?
        |
   YES  |  NO
        |
  +-----+------+
  |             |
Set MSB=1    Set MSB=0
Store abs    Store as-is
value in     in remaining
remaining    bits
bits
```

---

## 4. One's Complement

### Core Idea

**One's complement** of a binary number is obtained by **flipping all the bits** (every `0` becomes `1`, every `1` becomes `0`).

This operation is also called **bitwise NOT**.

```
Notation: ~N  (bitwise NOT of N)
```

### How to Compute One's Complement

```
Step-by-step:

Original number: +5  =>  0 0 0 0 0 1 0 1
Flip every bit:          1 1 1 1 1 0 1 0
                        = -5 in one's complement notation
```

```
Visual bit flip:
     0 → 1
     1 → 0

0 0 0 0 0 1 0 1   (+5)
| | | | | | | |
v v v v v v v v
1 1 1 1 1 0 1 0   (-5)
```

### Interpreting One's Complement Values

The **MSB** still acts as a sign bit:
- `0` in MSB → positive number → read value normally
- `1` in MSB → negative number → flip all bits to find magnitude

```
8-bit One's Complement Interpretation:

Bit Pattern | Interpretation
------------+----------------
0 0000000   |  +0
0 0000001   |  +1
0 0000010   |  +2
...
0 1111111   | +127
1 1111110   |  -1   (flip => 0000001 = 1, negative, so -1)
1 1111101   |  -2   (flip => 0000010 = 2, so -2)
...
1 0000001   | -126
1 0000000   |  -0   <-- STILL TWO ZEROS!
```

### Range (8-bit One's Complement)

```
Range: -127 to +127
       (Same problem as sign-magnitude: -0 exists)
```

### Addition in One's Complement — The End-Around Carry

One's complement arithmetic almost works, but with one quirk: **end-around carry**.

**Rule**: If the addition produces a carry out of the MSB, add that carry back to the result (wrap it around).

#### Example 1: Positive + Negative, no carry

```
+5 + (-2) = +3?

  +5  =>  0 0 0 0 0 1 0 1
  -2  =>  1 1 1 1 1 1 0 1   (one's complement of 2 = 00000010 => 11111101)
          -----------------
Sum   =>  1 0 0 0 0 0 1 0   (carry=1 out of MSB position)
                            + 1 (end-around carry)
          -----------------
Result=>  0 0 0 0 0 0 1 1   = +3  ✓
```

```
End-Around Carry Diagram:

  Carry out: 1 ─────────────────────────────────┐
                                                 │
  [ 1 0 0 0 0 0 1 0 ]  <──────── add this 1 ───┘
                ↓
  [ 0 0 0 0 0 0 1 1 ] = +3  ✓
```

#### Example 2: Negative + Negative

```
-2 + (-3) = -5?

  -2  =>  1 1 1 1 1 1 0 1
  -3  =>  1 1 1 1 1 1 0 0
          -----------------
Sum   =>  1 1 1 1 1 0 0 1  (carry=1 out)
                        + 1 (end-around carry)
          -----------------
Result=>  1 1 1 1 1 0 1 0  = -5  ✓
          (flip => 0 0 0 0 0 1 0 1 = 5, so -5)
```

#### Example 3: The Zero Problem

```
+5 + (-5) = 0?

  +5  =>  0 0 0 0 0 1 0 1
  -5  =>  1 1 1 1 1 0 1 0
          -----------------
Sum   =>  1 1 1 1 1 1 1 1  = -0  (No carry)

Result is -0, not +0!
Hardware must treat 11111111 and 00000000 as the SAME value.
```

### One's Complement Flowchart

```
ONE'S COMPLEMENT ENCODING FLOWCHART:

Start: Integer N
       |
       v
  Is N >= 0?
  /         \
YES           NO
  |             |
Write N in    Write |N| in 7 bits
7 bits with   Flip ALL 8 bits
MSB = 0       (including sign)
  |             |
  +------+------+
         |
         v
    Output 8-bit
    one's complement
    representation
```

### Flaws of One's Complement

```
FLAW 1: Two representations of zero (+0 and -0)
FLAW 2: End-around carry makes hardware more complex
FLAW 3: Range is -127 to +127 (not -128 to +127)
```

---

## 5. Two's Complement

### The Breakthrough Insight

Two's complement solves **all** the problems of one's complement with one elegant idea:

> **Two's complement of N = One's complement of N + 1**
> i.e., flip all bits, then add 1.

### How to Compute Two's Complement

#### Method 1: Flip + Add 1

```
Step 1: Write the number in binary
Step 2: Flip all bits (one's complement)
Step 3: Add 1 to the result
```

**Example: -5 in 8-bit two's complement**

```
Step 1: +5  =  0 0 0 0 0 1 0 1
Step 2: Flip   1 1 1 1 1 0 1 0   (one's complement)
Step 3: +1  =  1 1 1 1 1 0 1 1   (two's complement = -5)
```

```
Visual Walkthrough:

+5:    [ 0 0 0 0 0 1 0 1 ]
         ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓  (flip all bits)
       [ 1 1 1 1 1 0 1 0 ]
                       +1  (add 1)
                   -------
       [ 1 1 1 1 1 0 1 1 ]  = -5
```

#### Method 2: Copy from Right Until First `1` (Shortcut)

Scan from the rightmost bit. Copy bits as-is until you've copied the **first `1`**, then flip all remaining bits to the left.

```
+5:  0 0 0 0 0 1 0 1
                   ^
                   Copy rightmost 1 and everything to its right as-is
                   
     Start copying →    1    ← first 1 found, copy it
     Now flip left →  1 1 0  ← flip remaining
     
+5:  0  0  0  0  0  1  0  1
-5:  1  1  1  1  1  0  1  1
     ↑-flipped-↑  ↑ kept ↑
```

**Example: -12**

```
+12:  0 0 0 0 1 1 0 0
               copy → 0 0  (rightmost zeros, no 1 yet)
               first 1 → copy 1
               flip rest → 1 1 1 1 0
               
-12:  1 1 1 1 0 1 0 0
```

Let's verify with flip+add:
```
+12:   0 0 0 0 1 1 0 0
flip:  1 1 1 1 0 0 1 1
+1:    1 1 1 1 0 1 0 0   = -12 ✓
```

### Why Does This Work? (Mathematical Proof)

For an N-bit system, two's complement represents `-x` as `2^N - x`.

For 8-bit: `-x` is stored as `256 - x`.

**Example**: `-5` is stored as `256 - 5 = 251`

```
251 in binary = 1 1 1 1 1 0 1 1   (which is what we computed!)
```

**Why this is brilliant for addition**:

```
+5 + (-5)
= 5 + (256 - 5)
= 256
= 1 0 0 0 0 0 0 0 0   (9 bits, carry discarded in 8-bit system)
= 0 0 0 0 0 0 0 0     (8-bit result = 0)  ✓
```

The carry is simply discarded, and the result is naturally zero — **no special hardware needed!**

### Two's Complement Value Table (4-bit)

```
4-bit Two's Complement:

Bit Pattern | Unsigned Value | Signed (Two's Complement) Value
------------+----------------+--------------------------------
  0 0 0 0   |       0        |      0
  0 0 0 1   |       1        |     +1
  0 0 1 0   |       2        |     +2
  0 0 1 1   |       3        |     +3
  0 1 0 0   |       4        |     +4
  0 1 0 1   |       5        |     +5
  0 1 1 0   |       6        |     +6
  0 1 1 1   |       7        |     +7    ← max positive
  1 0 0 0   |       8        |     -8    ← min negative (asymmetric!)
  1 0 0 1   |       9        |     -7
  1 0 1 0   |      10        |     -6
  1 0 1 1   |      11        |     -5
  1 1 0 0   |      12        |     -4
  1 1 0 1   |      13        |     -3
  1 1 1 0   |      14        |     -2
  1 1 1 1   |      15        |     -1
```

### The Number Circle (Wraparound Visualization)

Think of N-bit two's complement as a **clock face** or a **circle**.

```
4-bit Two's Complement Number Circle:

                    0000 (+0)
              1111         0001
           (-1)               (+1)
          1110                  0010
        (-2)                      (+2)
       1101                         0011
      (-3)                           (+3)
      1100                           0100
      (-4)                           (+4)
       1011                         0101
        (-5)                      (+5)
          1010                  0110
           (-6)               (+6)
              1001         0111
               (-7)      (+7)
                    1000
                    (-8)
                   ↑↑↑
               MOST NEGATIVE
               (no positive counterpart!)
```

**Key insight**: Going clockwise adds 1, going counter-clockwise subtracts 1. Overflow wraps around the circle.

### Range (N-bit Two's Complement)

```
Range: -2^(N-1)  to  +2^(N-1) - 1

8-bit:   -128  to  +127
16-bit:  -32768  to  +32767
32-bit:  -2,147,483,648  to  +2,147,483,647
64-bit:  -9,223,372,036,854,775,808  to  +9,223,372,036,854,775,807
```

**Why is the negative range 1 larger?** Because there's only ONE zero (0...0), freeing up one code point for an extra negative number (`1000...0 = -2^(N-1)`).

### The Asymmetry: INT_MIN Has No Positive Counterpart

```
8-bit: -128 has no +128 (only goes to +127)

Trying to negate -128:
  10000000  (-128)
  Flip: 01111111
  +1:   10000000  (-128 again!)  ← OVERFLOW!
```

This is the most critical gotcha in two's complement. `-INT_MIN` overflows back to `INT_MIN`.

### Two's Complement Encoding Flowchart

```
ENCODING FLOWCHART:

        Input integer N (N-bit system)
               |
    +----------+----------+
    |                     |
   N >= 0?              N < 0
    |                     |
Write N in           Write |N| in N bits
N bits               Flip all bits
(MSB = 0)            Add 1
    |                     |
    +----------+----------+
               |
         Output bit pattern
               |
        MSB = 0? → Positive
        MSB = 1? → Negative
```

### Two's Complement Decoding Flowchart

```
DECODING FLOWCHART (given a bit pattern):

        Read bit pattern
               |
        Is MSB = 0?
       /              \
     YES               NO
      |                 |
  Read directly      Flip all bits
  as unsigned        Add 1
  positive           Read as positive P
  number N           Result = -P
      |                 |
      +---------+--------+
                |
           Final Value
```

---

## 6. Arithmetic Operations

### Addition in Two's Complement

**No special cases needed.** Simply add the binary patterns and discard any carry beyond N bits.

#### Case 1: Positive + Positive

```
+3 + +4 = +7

  0 0 0 0 0 0 1 1   (+3)
+ 0 0 0 0 0 1 0 0   (+4)
  ---------------
  0 0 0 0 0 1 1 1   (+7)  ✓
```

#### Case 2: Positive + Negative

```
+5 + (-3) = +2

  0 0 0 0 0 1 0 1   (+5)
+ 1 1 1 1 1 1 0 1   (-3)
  ---------------
1 0 0 0 0 0 0 1 0   carry=1 (discarded)
  0 0 0 0 0 0 1 0   (+2)  ✓
```

#### Case 3: Negative + Negative

```
-3 + (-4) = -7

  1 1 1 1 1 1 0 1   (-3)
+ 1 1 1 1 1 1 0 0   (-4)
  ---------------
1 1 1 1 1 1 0 0 1   carry=1 (discarded)
  1 1 1 1 1 0 0 1   (-7)  ✓
  (flip+1 = 00000111 = 7, so -7)
```

#### Case 4: Zero Result

```
+5 + (-5) = 0

  0 0 0 0 0 1 0 1   (+5)
+ 1 1 1 1 1 0 1 1   (-5)
  ---------------
1 0 0 0 0 0 0 0 0   carry=1 (discarded)
  0 0 0 0 0 0 0 0   (0)  ✓
```

### Subtraction in Two's Complement

Subtraction is just addition with the negated second operand:

```
A - B  =  A + (-B)  =  A + (~B + 1)
```

This means a CPU only needs **one adder circuit** to do both addition and subtraction! The hardware just:
1. Optionally flips the second operand's bits (controlled by a subtract signal)
2. Adds 1 (via the carry-in pin of the adder)

```
ALU Subtraction Circuit:

  A ─────────────────────────────┐
                                 ↓
  B ─── [Bit Inverter] ─── [Adder] ─── Result
              ↑
         Subtract=1
         (also adds carry-in=1 to complete ~B+1)
```

### Multiplication

Two's complement multiplication requires sign extension (extending the sign bit) when widening, and truncation when narrowing. The result of multiplying two N-bit numbers can be up to 2N bits wide.

```
+3 × -4 = -12 in 4-bit:

  +3  =  0011
  -4  =  1100

Standard binary multiply (grade-school method):
     0011  × 1100

  0011 × 0 = 00000000  (bit 0 of 1100)
  0011 × 0 = 00000000  (bit 1)
  0011 × 1 = 00001100  shifted 2 positions = 00110000 (wait, 8-bit)

Shortcut: just use hardware; conceptually the result is -12 = 11110100 (8-bit)
```

---

## 7. Overflow Detection

Overflow occurs when the result of an arithmetic operation cannot be represented in the available number of bits.

### When Does Overflow Happen?

```
OVERFLOW CONDITIONS:

1. Positive + Positive = Negative  (result too large)
2. Negative + Negative = Positive  (result too small / too negative)

Overflow CANNOT happen when adding numbers of OPPOSITE signs.
```

### Overflow Detection Methods

#### Method 1: Sign Bit Rules

```
For addition A + B = S:

Overflow iff:
  (A is positive AND B is positive AND S is negative)
OR
  (A is negative AND B is negative AND S is positive)

In terms of sign bits (MSBs):
  Overflow = (MSB_A == MSB_B) AND (MSB_S != MSB_A)
```

#### Method 2: Carry-Based Detection (Hardware)

```
Overflow = Carry into MSB  XOR  Carry out of MSB

If carry_in(MSB) ≠ carry_out(MSB)  →  OVERFLOW
```

```
Example: 0111 + 0001 (in 4-bit) = +7 + +1

  0 1 1 1   (+7)
+ 0 0 0 1   (+1)
-----------
  1 0 0 0   (-8)  ← OVERFLOW! +8 cannot fit in 4-bit signed

carry into bit 3  = 1 (from bit 2's sum)
carry out of bit 3 = 0
1 XOR 0 = 1  → OVERFLOW detected  ✓
```

### Overflow Decision Tree

```
Performing A + B = S

         A and B same sign?
         /               \
       YES                NO
        |                  |
    S same sign          NO overflow
    as A and B?          possible
    /         \
  YES           NO
   |             |
No overflow   OVERFLOW
```

---

## 8. Bit Manipulation Tricks Powered by Two's Complement

Two's complement is the foundation of many elegant bit tricks used in competitive programming and systems code.

### Trick 1: Check if N is Power of Two

```
N & (N - 1) == 0  (and N != 0)

Why it works:
  Powers of 2:  0001, 0010, 0100, 1000
  N-1:          0000, 0001, 0011, 0111
  AND:          0000, 0000, 0000, 0000  ← always zero

  Non-power: N = 6 = 0110
             N-1 = 5 = 0101
             AND = 0100  ≠ 0
```

### Trick 2: Isolate the Lowest Set Bit

```
N & (-N)

Why it works:
  N     =  0...01???0...0   (some bits, then rightmost 1, then zeros)
 -N     =  1...10001...0+1
         = 1...10001...0    (flip N, add 1)
  N&-N  =  0...00001...0    (only rightmost 1 remains)

Example: N = 52 = 00110100
  -N  = 11001100   (flip) = 11001100 + 1 = 11001100
  Wait: flip(00110100) = 11001011, +1 = 11001100
  N & (-N) = 00110100 & 11001100 = 00000100   (rightmost set bit = bit 2)
```

### Trick 3: Turn Off the Lowest Set Bit

```
N & (N - 1)

Example: N = 52 = 00110100
  N-1 = 00110011
  AND = 00110000   (lowest set bit cleared)
```

### Trick 4: Get the Sign of a Number (Branchless)

```
sign = (N >> (BITS - 1))  // arithmetic right shift

For N = -5 (8-bit): 11111011 >> 7 = 11111111 = -1
For N = +5 (8-bit): 00000101 >> 7 = 00000000 =  0
```

*Note: Arithmetic right shift fills with the sign bit (1 for negative, 0 for positive).*

### Trick 5: Absolute Value (Branchless)

```
mask = N >> (BITS - 1)     // all 1s if negative, all 0s if positive
abs  = (N + mask) XOR mask

For N = -5:
  mask = 11111111 (-1)
  N + mask = -5 + (-1) = -6 = 11111010
  XOR mask = 11111010 XOR 11111111 = 00000101 = +5  ✓

For N = +5:
  mask = 00000000
  N + mask = 5
  XOR mask = 5 XOR 0 = 5  ✓
```

---

## 9. Edge Cases and Gotchas

### Gotcha 1: `-INT_MIN` Overflows

```
INT8_MIN = -128 = 10000000
-(-128) = flip(10000000) + 1 = 01111111 + 1 = 10000000 = -128  OVERFLOW!
```

### Gotcha 2: Right Shift Behavior

```
ARITHMETIC right shift (signed): fills with sign bit
LOGICAL right shift (unsigned):  fills with 0

In C:  signed >> n   is implementation-defined (usually arithmetic)
       unsigned >> n is always logical

In Rust: i32 >> n  is arithmetic
         u32 >> n  is logical

In Go:  int >> n   is arithmetic
        uint >> n  is logical
```

### Gotcha 3: Signed Integer Overflow is UB in C

```c
// In C, signed integer overflow is UNDEFINED BEHAVIOR!
int x = INT_MAX;
x = x + 1;  // UB! Could be anything.

// Unsigned overflow is well-defined (wraps around):
unsigned int y = UINT_MAX;
y = y + 1;  // y == 0  (defined, wraps around)
```

### Gotcha 4: Type Casting Traps

```
Casting from signed to unsigned reinterprets bits:
  int8_t  x = -1;   // bits: 11111111
  uint8_t y = (uint8_t)x;  // y = 255 (same bits, different interpretation)
```

### Gotcha 5: Implicit Promotion in C

```c
int8_t a = -1;   // 11111111
int8_t b = a >> 1;  // In C, a is promoted to int before shift
                    // Result: -1 (arithmetic shift, stays -1)
```

---

## 10. Implementations in C, Go, and Rust

### C Implementation

```c
#include <stdio.h>
#include <stdint.h>
#include <limits.h>

/*
 * PREREQUISITE CONCEPTS:
 * int8_t  = 8-bit signed integer (range: -128 to 127)
 * uint8_t = 8-bit unsigned integer (range: 0 to 255)
 * ~x      = bitwise NOT (one's complement)
 * -x      = arithmetic negation (two's complement in modern CPUs)
 */

/* ==================== ONE'S COMPLEMENT ==================== */

// Compute one's complement of an 8-bit value
uint8_t ones_complement(uint8_t x) {
    return ~x;  // Flip all 8 bits
}

/* ==================== TWO'S COMPLEMENT ==================== */

// Method 1: flip bits then add 1
int8_t twos_complement_method1(int8_t x) {
    // Cast to uint8_t to avoid signed overflow UB during flip
    uint8_t ux = (uint8_t)x;
    uint8_t flipped = ~ux;
    uint8_t result = flipped + 1;
    return (int8_t)result;
}

// Method 2: use arithmetic negation (CPU does two's complement)
int8_t twos_complement_method2(int8_t x) {
    // This is equivalent — the CPU uses two's complement internally
    // CAUTION: -INT8_MIN is undefined behavior in C for signed types
    // Use with care and only for valid ranges
    return (int8_t)(-(int)x);
}

/* ==================== OVERFLOW DETECTION ==================== */

// Detect overflow in signed 8-bit addition
// Returns 1 if overflow, 0 if no overflow
int add_overflow_check(int8_t a, int8_t b, int8_t *result) {
    // Use wider type to detect overflow safely
    int16_t wide = (int16_t)a + (int16_t)b;
    if (wide > INT8_MAX || wide < INT8_MIN) {
        return 1;  // Overflow!
    }
    *result = (int8_t)wide;
    return 0;
}

/* ==================== BIT TRICKS ==================== */

// Check if N is a power of two
int is_power_of_two(uint32_t n) {
    return (n != 0) && ((n & (n - 1)) == 0);
}

// Isolate lowest set bit
uint32_t lowest_set_bit(uint32_t n) {
    return n & (-n);  // n & (~n + 1)
}

// Count trailing zeros (how many zero bits from the right)
int count_trailing_zeros(uint32_t n) {
    if (n == 0) return 32;
    int count = 0;
    while ((n & 1) == 0) {
        count++;
        n >>= 1;
    }
    return count;
}

// Branchless absolute value
int32_t branchless_abs(int32_t n) {
    int32_t mask = n >> 31;       // All 1s if negative, all 0s if positive
    return (n + mask) ^ mask;
}

// Branchless sign: returns -1, 0, or +1
int32_t sign_of(int32_t n) {
    return (n > 0) - (n < 0);
}

/* ==================== PRINT HELPERS ==================== */

void print_binary_8(uint8_t val) {
    for (int i = 7; i >= 0; i--) {
        printf("%d", (val >> i) & 1);
        if (i == 4) printf(" ");  // nibble separator
    }
}

void demo_ones_complement(void) {
    printf("\n========== ONE'S COMPLEMENT ==========\n");
    for (int8_t n = -5; n <= 5; n++) {
        uint8_t as_bits = (uint8_t)n;
        uint8_t complement = ones_complement(as_bits);
        printf("~%4d  =  ", n);
        print_binary_8(as_bits);
        printf("  =>  ");
        print_binary_8(complement);
        printf("  (%4d as signed)\n", (int8_t)complement);
    }
}

void demo_twos_complement(void) {
    printf("\n========== TWO'S COMPLEMENT ==========\n");
    int8_t values[] = {1, 2, 5, 10, 42, 127, -1, -128};
    int n = sizeof(values) / sizeof(values[0]);
    for (int i = 0; i < n; i++) {
        int8_t original = values[i];
        int8_t negated = twos_complement_method1(original);
        printf("  %5d  =>  ", original);
        print_binary_8((uint8_t)original);
        printf("  negate =>  ");
        print_binary_8((uint8_t)negated);
        printf("  (%5d)\n", negated);
    }
}

void demo_addition(void) {
    printf("\n========== TWO'S COMPLEMENT ADDITION ==========\n");
    int8_t pairs[][2] = {
        {5, -3}, {-5, 3}, {-5, -3}, {100, 50}, {-100, -50}
    };
    int n = sizeof(pairs) / sizeof(pairs[0]);
    for (int i = 0; i < n; i++) {
        int8_t a = pairs[i][0], b = pairs[i][1];
        int8_t result;
        int overflow = add_overflow_check(a, b, &result);
        printf("  %4d + %4d = ", a, b);
        if (overflow) {
            printf("OVERFLOW! (raw bits: %d)\n", (int8_t)((int8_t)a + b));
        } else {
            printf("%4d\n", result);
        }
    }
}

void demo_bit_tricks(void) {
    printf("\n========== BIT TRICKS ==========\n");
    uint32_t test_vals[] = {0, 1, 4, 6, 8, 16, 52, 255};
    int n = sizeof(test_vals) / sizeof(test_vals[0]);
    for (int i = 0; i < n; i++) {
        uint32_t v = test_vals[i];
        printf("  N=%3u  pow2?=%d  lowest_set_bit=%2u  ctz=%2d\n",
               v,
               is_power_of_two(v),
               lowest_set_bit(v),
               count_trailing_zeros(v));
    }

    printf("\nBranchless abs:\n");
    int32_t signed_vals[] = {-100, -1, 0, 1, 100, INT32_MIN + 1};
    int m = sizeof(signed_vals) / sizeof(signed_vals[0]);
    for (int i = 0; i < m; i++) {
        int32_t v = signed_vals[i];
        printf("  abs(%12d) = %d\n", v, branchless_abs(v));
    }
}

int main(void) {
    printf("=== C: One's and Two's Complement Deep Demo ===\n");
    demo_ones_complement();
    demo_twos_complement();
    demo_addition();
    demo_bit_tricks();
    return 0;
}
```

---

### Go Implementation

```go
package main

import (
	"fmt"
	"math"
	"math/bits"
	"strings"
)

/*
 * In Go:
 * int8  = 8-bit signed  (-128 to 127)
 * uint8 = 8-bit unsigned (0 to 255)
 * ^x    = bitwise NOT (one's complement)
 * -x    = two's complement negation
 *
 * Go handles signed overflow differently from C:
 * Signed overflow in Go wraps (defined behavior), unlike C's UB.
 * However, for clarity we use explicit uint types for bit operations.
 */

// ==================== ONE'S COMPLEMENT ====================

// OnesComplement returns the bitwise NOT of an 8-bit value
func OnesComplement(x uint8) uint8 {
	return ^x
}

// ==================== TWO'S COMPLEMENT ====================

// TwosComplementManual: flip bits and add 1
func TwosComplementManual(x uint8) uint8 {
	return ^x + 1
}

// TwosComplementNegate: using Go's arithmetic negation
func TwosComplementNegate(x int8) int8 {
	// Safe for all values except math.MinInt8
	if x == math.MinInt8 {
		return math.MinInt8 // Overflows back to itself
	}
	return -x
}

// ==================== OVERFLOW DETECTION ====================

// AddInt8Safe adds two int8 values with overflow detection.
// Returns (result, overflowed).
func AddInt8Safe(a, b int8) (int8, bool) {
	result := int16(a) + int16(b)
	if result > math.MaxInt8 || result < math.MinInt8 {
		return int8(result), true // return truncated and overflow=true
	}
	return int8(result), false
}

// ==================== BIT TRICKS ====================

// IsPowerOfTwo checks if n is a power of two
func IsPowerOfTwo(n uint32) bool {
	return n != 0 && (n&(n-1)) == 0
}

// LowestSetBit returns a value with only the lowest set bit of n
func LowestSetBit(n uint32) uint32 {
	// In Go, -n on uint32 wraps (it's two's complement)
	// But cleaner to write it explicitly:
	return n & (^n + 1)
}

// CountTrailingZeros returns the number of zero bits from the right
func CountTrailingZeros(n uint32) int {
	if n == 0 {
		return 32
	}
	return bits.TrailingZeros32(n) // Go stdlib
}

// BranchlessAbs returns the absolute value without branching
func BranchlessAbs(n int32) int32 {
	mask := n >> 31 // arithmetic right shift: all 1s if negative
	return (n + mask) ^ mask
}

// SignOf returns -1, 0, or +1
func SignOf(n int32) int32 {
	// Convert bool to int trick
	pos := int32(0)
	if n > 0 {
		pos = 1
	}
	neg := int32(0)
	if n < 0 {
		neg = 1
	}
	return pos - neg
}

// ==================== PRINT HELPERS ====================

// ToBinaryString returns an 8-bit binary string with a nibble space
func ToBinaryString8(val uint8) string {
	var sb strings.Builder
	for i := 7; i >= 0; i-- {
		if (val>>i)&1 == 1 {
			sb.WriteByte('1')
		} else {
			sb.WriteByte('0')
		}
		if i == 4 {
			sb.WriteByte(' ')
		}
	}
	return sb.String()
}

// ==================== DEMO FUNCTIONS ====================

func demoOnesComplement() {
	fmt.Println("\n========== ONE'S COMPLEMENT ==========")
	for n := int8(-5); n <= 5; n++ {
		bits := uint8(n)
		complement := OnesComplement(bits)
		fmt.Printf("  ~%4d  =  %s  =>  %s  (%4d as signed)\n",
			n,
			ToBinaryString8(bits),
			ToBinaryString8(complement),
			int8(complement),
		)
	}
}

func demoTwosComplement() {
	fmt.Println("\n========== TWO'S COMPLEMENT ==========")
	values := []int8{1, 2, 5, 10, 42, 127, -1, -128}
	for _, v := range values {
		original := uint8(v)
		negated := TwosComplementManual(original)
		fmt.Printf("  %5d  =>  %s  negate =>  %s  (%5d)\n",
			v,
			ToBinaryString8(original),
			ToBinaryString8(negated),
			int8(negated),
		)
	}
}

func demoAddition() {
	fmt.Println("\n========== TWO'S COMPLEMENT ADDITION ==========")
	pairs := [][2]int8{
		{5, -3}, {-5, 3}, {-5, -3}, {100, 50}, {-100, -50},
	}
	for _, pair := range pairs {
		a, b := pair[0], pair[1]
		result, overflow := AddInt8Safe(a, b)
		if overflow {
			fmt.Printf("  %4d + %4d = OVERFLOW! (raw: %d)\n", a, b, result)
		} else {
			fmt.Printf("  %4d + %4d = %4d\n", a, b, result)
		}
	}
}

func demoBitTricks() {
	fmt.Println("\n========== BIT TRICKS ==========")
	testVals := []uint32{0, 1, 4, 6, 8, 16, 52, 255}
	for _, v := range testVals {
		fmt.Printf("  N=%3d  pow2?=%v  lowest_set_bit=%2d  ctz=%2d\n",
			v,
			IsPowerOfTwo(v),
			LowestSetBit(v),
			CountTrailingZeros(v),
		)
	}

	fmt.Println("\nBranchless abs:")
	signedVals := []int32{-100, -1, 0, 1, 100, math.MinInt32 + 1}
	for _, v := range signedVals {
		fmt.Printf("  abs(%12d) = %d\n", v, BranchlessAbs(v))
	}

	fmt.Println("\nSign function:")
	for _, v := range []int32{-42, -1, 0, 1, 42} {
		fmt.Printf("  sign(%4d) = %2d\n", v, SignOf(v))
	}
}

func demoNumberLine() {
	fmt.Println("\n========== 4-BIT TWO'S COMPLEMENT TABLE ==========")
	fmt.Println("  Bits  | Unsigned | Signed(2C)")
	fmt.Println("  ------|----------|----------")
	for i := 0; i < 16; i++ {
		b := uint8(i)
		signed := int8(b)
		// Display as 4-bit
		bin := ""
		for j := 3; j >= 0; j-- {
			if (b>>j)&1 == 1 {
				bin += "1"
			} else {
				bin += "0"
			}
		}
		marker := ""
		if i == 8 {
			marker = "  ← min negative"
		}
		if i == 7 {
			marker = "  ← max positive"
		}
		fmt.Printf("  %s  |  %2d      |  %4d%s\n", bin, b, signed, marker)
	}
}

func main() {
	fmt.Println("=== Go: One's and Two's Complement Deep Demo ===")
	demoOnesComplement()
	demoTwosComplement()
	demoAddition()
	demoBitTricks()
	demoNumberLine()
}
```

---

### Rust Implementation

```rust
//! One's Complement and Two's Complement — Complete Rust Demo
//!
//! Rust's type system makes signed/unsigned distinctions explicit.
//! Key Rust operators:
//!   !x   = bitwise NOT (one's complement) — for integers
//!   -x   = arithmetic negation (two's complement)
//!   i8::MIN.wrapping_neg() = handles -INT_MIN correctly
//!   checked_add, saturating_add, wrapping_add = safe arithmetic

use std::fmt;

// ==================== ONE'S COMPLEMENT ====================

/// Returns the one's complement (bitwise NOT) of an 8-bit value.
/// In Rust, `!x` on unsigned integers performs bitwise NOT.
fn ones_complement(x: u8) -> u8 {
    !x
}

// ==================== TWO'S COMPLEMENT ====================

/// Computes two's complement by flipping bits and adding 1.
/// This is the manual way to show the concept.
fn twos_complement_manual(x: u8) -> u8 {
    (!x).wrapping_add(1)
    // wrapping_add is used because plain `+` would panic on overflow in debug mode
}

/// Returns the negation using Rust's checked arithmetic.
/// Rust panics on overflow in debug mode for signed types unless you use
/// wrapping/checked/saturating variants.
fn negate_safe(x: i8) -> Option<i8> {
    x.checked_neg()
    // Returns None if x == i8::MIN (which has no positive counterpart)
}

/// Wrapping negation — never panics, wraps for i8::MIN
fn negate_wrapping(x: i8) -> i8 {
    x.wrapping_neg()
}

// ==================== OVERFLOW DETECTION ====================

/// Adds two i8 values with explicit overflow detection.
/// Returns Ok(result) or Err("overflow").
fn add_i8_checked(a: i8, b: i8) -> Result<i8, &'static str> {
    a.checked_add(b).ok_or("overflow")
}

// ==================== BIT TRICKS ====================

/// Check if n is a power of two
fn is_power_of_two(n: u32) -> bool {
    n != 0 && (n & n.wrapping_sub(1)) == 0
    // Equivalent: n.is_power_of_two() [Rust stdlib]
}

/// Isolate the lowest set bit
fn lowest_set_bit(n: u32) -> u32 {
    n & n.wrapping_neg()
    // wrapping_neg() = wrapping two's complement negation = ~n + 1
}

/// Count trailing zeros
fn count_trailing_zeros(n: u32) -> u32 {
    n.trailing_zeros() // Rust stdlib, returns 32 for n=0
}

/// Branchless absolute value for i32
fn branchless_abs(n: i32) -> i32 {
    let mask = n >> 31; // arithmetic right shift
    (n.wrapping_add(mask)) ^ mask
}

/// Sign of a number: -1, 0, or +1
fn sign_of(n: i32) -> i32 {
    (n > 0) as i32 - (n < 0) as i32
    // Rust: bool as i32 converts true→1, false→0
}

/// Demonstrates bit tricks for isolation and manipulation
fn clear_lowest_set_bit(n: u32) -> u32 {
    n & n.wrapping_sub(1)
}

// ==================== DISPLAY HELPERS ====================

/// Formats a u8 as a spaced binary string: "1011 0110"
fn to_binary_8(val: u8) -> String {
    format!("{:04b} {:04b}", (val >> 4), val & 0xF)
}

// ==================== DEMO FUNCTIONS ====================

fn demo_ones_complement() {
    println!("\n========== ONE'S COMPLEMENT ==========");
    for n in -5i8..=5 {
        let bits = n as u8;
        let complement = ones_complement(bits);
        println!(
            "  ~{:4}  =  {}  =>  {}  ({:4} as i8)",
            n,
            to_binary_8(bits),
            to_binary_8(complement),
            complement as i8
        );
    }
}

fn demo_twos_complement() {
    println!("\n========== TWO'S COMPLEMENT ==========");
    let values: &[i8] = &[1, 2, 5, 10, 42, 127, -1, -128];
    for &v in values {
        let original = v as u8;
        let negated = twos_complement_manual(original);
        let safe_neg = negate_safe(v);
        println!(
            "  {:5}  =>  {}  negate =>  {}  ({:5})  checked_neg={:?}",
            v,
            to_binary_8(original),
            to_binary_8(negated),
            negated as i8,
            safe_neg
        );
    }
}

fn demo_addition() {
    println!("\n========== TWO'S COMPLEMENT ADDITION ==========");
    let pairs: &[(i8, i8)] = &[
        (5, -3),
        (-5, 3),
        (-5, -3),
        (100, 50),
        (-100, -50),
    ];
    for &(a, b) in pairs {
        match add_i8_checked(a, b) {
            Ok(result) => println!("  {:4} + {:4} = {:4}", a, b, result),
            Err(_) => {
                let wrapped = a.wrapping_add(b);
                println!("  {:4} + {:4} = OVERFLOW! (wrapping: {})", a, b, wrapped);
            }
        }
    }
}

fn demo_bit_tricks() {
    println!("\n========== BIT TRICKS ==========");
    let test_vals: &[u32] = &[0, 1, 4, 6, 8, 16, 52, 255];
    for &v in test_vals {
        println!(
            "  N={:3}  pow2?={:5}  lowest_set_bit={:2}  ctz={:2}  clear_low={}",
            v,
            is_power_of_two(v),
            lowest_set_bit(v),
            count_trailing_zeros(v),
            clear_lowest_set_bit(v),
        );
    }

    println!("\nBranchless abs:");
    let signed_vals: &[i32] = &[-100, -1, 0, 1, 100, i32::MIN + 1];
    for &v in signed_vals {
        println!("  abs({:12}) = {}", v, branchless_abs(v));
    }

    println!("\nSign function:");
    for &v in &[-42i32, -1, 0, 1, 42] {
        println!("  sign({:4}) = {:2}", v, sign_of(v));
    }
}

fn demo_rust_safe_arithmetic() {
    println!("\n========== RUST SAFE ARITHMETIC MODES ==========");
    let a: i8 = 120;
    let b: i8 = 20;

    println!("  a = {}, b = {}", a, b);
    println!("  checked_add:    {:?}", a.checked_add(b));    // None on overflow
    println!("  saturating_add: {}", a.saturating_add(b));   // Clamps to i8::MAX
    println!("  wrapping_add:   {}", a.wrapping_add(b));     // Wraps around
    // a + b in debug mode would PANIC here

    let min: i8 = i8::MIN;
    println!("\n  i8::MIN = {}", min);
    println!("  checked_neg(MIN):    {:?}", min.checked_neg()); // None!
    println!("  wrapping_neg(MIN):   {}", min.wrapping_neg()); // i8::MIN
    println!("  saturating_neg(MIN): {}", min.saturating_neg()); // i8::MAX
}

fn demo_number_table() {
    println!("\n========== 4-BIT TWO'S COMPLEMENT TABLE ==========");
    println!("  Bits | Unsigned | Signed(2C)");
    println!("  -----|----------|----------");
    for i in 0u8..16 {
        let signed = i as i8; // 4-bit pattern in i8 (upper bits 0)
        // Manually handle 4-bit interpretation
        let signed_4bit: i8 = if i >= 8 { i as i8 - 16 } else { i as i8 };
        let bin = format!("{:04b}", i);
        let marker = if i == 8 { "  ← min negative" }
                     else if i == 7 { "  ← max positive" }
                     else { "" };
        println!("  {}  |  {:2}      |  {:4}{}", bin, i, signed_4bit, marker);
        let _ = signed; // suppress unused warning
    }
}

fn main() {
    println!("=== Rust: One's and Two's Complement Deep Demo ===");
    demo_ones_complement();
    demo_twos_complement();
    demo_addition();
    demo_bit_tricks();
    demo_rust_safe_arithmetic();
    demo_number_table();
}
```

---

## 11. Mental Models and Visual Summary

### The Three Representations Side by Side (8-bit, value = -5)

```
VALUE: -5  (decimal)

+---------------------+----------+----------+
| Representation      | Bit      | Value of |
|                     | Pattern  | 11111011 |
+---------------------+----------+----------+
| Sign-Magnitude      | 10000101 | -5       |
| One's Complement    | 11111010 | -5       |
| Two's Complement    | 11111011 | -5       |
+---------------------+----------+----------+
```

### Comparison Table

```
+--------------------+---------------+---------------+------------------+
| Property           | Sign-Magnitude| One's Compl.  | Two's Complement |
+--------------------+---------------+---------------+------------------+
| Zero representations|    TWO (+/-0) |   TWO (+/-0)  |   ONE (unique)   |
| Range (8-bit)      | -127 to +127  | -127 to +127  | -128 to +127     |
| Addition hardware  | Complex       | End-around    | Simple discard   |
|                    |               | carry needed  | carry            |
| Subtraction        | Needs special | Needs special | A + (~B + 1)     |
|                    | logic         | logic         | (simple!)        |
| Negation method    | Flip MSB      | Flip all bits | Flip + Add 1     |
| Used in practice?  | Floating point| Old computers | ALL modern CPUs  |
|                    | sign bit only | (rarely)      |                  |
+--------------------+---------------+---------------+------------------+
```

### The "Why Two's Complement Won" Mental Model

```
PROBLEM HIERARCHY:

  Binary hardware only knows 0 and 1
           |
           ↓
  Need negative numbers
           |
           ↓
  Attempt 1: Sign-Magnitude
  → Failed: two zeros, complex adder
           |
           ↓
  Attempt 2: One's Complement
  → Better: addition almost works
  → Failed: still two zeros, end-around carry
           |
           ↓
  Attempt 3: Two's Complement
  → Perfect: one zero, no special carry,
    subtraction = negated addition,
    single unified adder circuit
  → ADOPTED BY ALL MODERN CPUs
```

### Complete Algorithm Flowchart: Encode Integer in Two's Complement

```
START: Given integer N, bit width W
          |
          v
    Is N >= 0?
   /            \
 YES              NO
  |                |
  |         Compute |N| in W bits
  |                |
Write N in         Flip all W bits  
W bits             (one's complement)
                   |
                   Add 1
                   (handle carry within W bits)
  |                |
  +-------+--------+
          |
    Output W-bit pattern
          |
  Verify: MSB=0 means positive
          MSB=1 means negative
          |
         END
```

### Complete Algorithm Flowchart: Decode Two's Complement to Integer

```
START: Given W-bit pattern P
          |
          v
    Is MSB of P = 0?
   /                 \
 YES                   NO
  |                     |
  |               Flip all bits
  |               Add 1
Read P as         Read result as M
unsigned value N  Output: -(M)
  |                     |
  +----------+----------+
             |
        Output integer
             |
           END
```

### Cognitive Chunk Summary

To master this topic, your brain should chunk these facts:

```
CHUNK 1: REPRESENTATION
  Negative number X  =>  flip bits of |X|, then add 1
  One zero, simpler hardware

CHUNK 2: RANGE ASYMMETRY
  N-bit:  -2^(N-1)  to  +2^(N-1) - 1
  Extra negative exists because only one zero!
  INT_MIN has no positive counterpart

CHUNK 3: ARITHMETIC IS JUST ADDITION
  A - B  =  A + (~B + 1)
  Overflow: same-sign inputs → different-sign output

CHUNK 4: BIT TRICKS FROM TWO'S COMPLEMENT
  -N   = ~N + 1
  N & -N  = lowest set bit
  N & (N-1)  = clear lowest set bit
  (N & (N-1)) == 0  ↔  N is power of two
```

---

## Key Takeaways

```
1. ONE'S COMPLEMENT = flip all bits
   - Two zeros exist (+0, -0)
   - Needs end-around carry for addition
   - Rarely used (only in legacy systems)

2. TWO'S COMPLEMENT = flip all bits, then add 1
   - One unique zero
   - Simple addition: discard the carry-out
   - Subtraction = addition of negated value
   - Used in ALL modern CPUs and programming languages
   - Rust enforces overflow safety explicitly
   - C has UB on signed overflow (use unsigned or checked math)
   - Go has wrapping behavior on overflow (defined, but wraps silently)

3. CRITICAL GOTCHAS:
   - -INT_MIN overflows back to INT_MIN
   - Arithmetic right shift fills with sign bit
   - Signed overflow is UB in C (not in Rust/Go)
   - Cast between signed/unsigned reinterprets bits (same pattern)
```

---

*"The brilliance of two's complement is not that it represents negatives — it's that it makes subtraction disappear into addition."*

Now let me build the complete, comprehensive guide:Here's your complete guide. Let me walk you through what's inside and what makes it special:

---

### What the Guide Covers

**Conceptual Foundation (Sections 1–3)**
The guide opens with a clean binary number system refresher — positional weights, bit ranges — so everything that follows is built on solid ground. Then it lays out *why* the problem exists: a CPU only knows 0 and 1, and we need negative numbers.

**One's Complement (Section 4)**
Full treatment: how to compute it, how to interpret values, the addition rule with *end-around carry* (explained with carry diagrams), and — critically — *why it fails*: the dual-zero problem that forced engineers to go further.

**Two's Complement (Section 5)**
This is the core. It covers:
- Two computation methods (flip+add1, and the rightmost-bit shortcut)
- The *mathematical proof* showing why `2^N - x` makes addition naturally correct
- The number circle (wraparound visualization)
- The asymmetry of `INT_MIN` having no positive counterpart — one of the most dangerous gotchas in systems programming

**Arithmetic & Overflow (Sections 6–7)**
Addition for all four sign combinations, why subtraction becomes addition, and two overflow detection methods (sign bit rules + carry XOR).

**Bit Tricks (Section 8)**
`N & (N-1)`, `N & (-N)`, branchless abs, sign extraction — all derived from first principles.

**Implementations (Section 10)**
- **C**: Uses `uint8_t`/`int8_t`, exposes UB dangers with signed overflow, uses `int16_t` widening for safe overflow detection
- **Go**: Demonstrates `wrapping_add` semantics, `math/bits` stdlib, clean idiomatic style
- **Rust**: Showcases `checked_add`, `wrapping_add`, `saturating_add`, `checked_neg` — Rust's explicit safety model makes the overflow contracts visible at the type level

---

### The Deepest Insight to Carry Forward

Two's complement didn't just solve the dual-zero problem. It made **subtraction architecturally disappear** — a CPU's ALU only needs *one adder circuit*. Flipping the subtrahend's bits + setting carry-in to 1 is all it takes. That is why every modern CPU uses it.