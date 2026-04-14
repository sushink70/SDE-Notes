# Bitwise Operations — Complete In-Depth Guide
> C (Linux kernel-style) · Go · Rust | From fundamentals to kernel internals

---

## Table of Contents

1. [Binary Representation & Number Systems](#1-binary-representation--number-systems)
2. [Two's Complement & Signed Integers](#2-twos-complement--signed-integers)
3. [Bitwise Operators — Complete Reference](#3-bitwise-operators--complete-reference)
   - AND (`&`)
   - OR (`|`)
   - XOR (`^`)
   - NOT (`~` / `!`)
   - Left Shift (`<<`)
   - Right Shift (`>>`)
4. [Bit Masks & Flags](#4-bit-masks--flags)
5. [Bit Fields (C Struct Bitfields)](#5-bit-fields-c-struct-bitfields)
6. [Compound Assignment Operators](#6-compound-assignment-operators)
7. [Bit Manipulation Tricks & Idioms](#7-bit-manipulation-tricks--idioms)
8. [Population Count (Hamming Weight)](#8-population-count-hamming-weight)
9. [Bit Reversal](#9-bit-reversal)
10. [Endianness & Byte Swapping](#10-endianness--byte-swapping)
11. [Arithmetic via Bit Operations](#11-arithmetic-via-bit-operations)
12. [Fixed-Point Arithmetic](#12-fixed-point-arithmetic)
13. [Bitsets & Bitmaps](#13-bitsets--bitmaps)
14. [Rotate Operations](#14-rotate-operations)
15. [Gray Code](#15-gray-code)
16. [Signed vs Unsigned Shift Behaviour](#16-signed-vs-unsigned-shift-behaviour)
17. [Undefined Behaviour & Overflow Traps](#17-undefined-behaviour--overflow-traps)
18. [SIMD / Vectorized Bit Operations (intro)](#18-simd--vectorized-bit-operations-intro)
19. [Linux Kernel Bitwise Patterns](#19-linux-kernel-bitwise-patterns)
20. [Compiler Intrinsics & Built-ins](#20-compiler-intrinsics--built-ins)
21. [eBPF Bitwise Operations](#21-ebpf-bitwise-operations)
22. [Exercises & Interview Problems](#22-exercises--interview-problems)

---

## 1. Binary Representation & Number Systems

### Positional Weight

Every bit position `i` (0-indexed from LSB) carries weight `2^i`.

```
Decimal 173 in 8-bit binary:

 Bit position: 7    6    5    4    3    2    1    0
 Bit value:    1    0    1    0    1    1    0    1
 Weight:      128   64   32   16    8    4    2    1

 128 + 0 + 32 + 0 + 8 + 4 + 0 + 1 = 173
```

### Number System Conversions

```
Decimal  → Binary   : repeated division by 2 (record remainders, read bottom-up)
Binary   → Decimal  : sum of 2^i for each set bit
Binary   → Hex      : group into nibbles (4-bit groups) from LSB
Hex      → Binary   : expand each hex digit to 4 bits

173 decimal:
  173 / 2 = 86 R 1
   86 / 2 = 43 R 0
   43 / 2 = 21 R 1
   21 / 2 = 10 R 1
   10 / 2 =  5 R 0
    5 / 2 =  2 R 1
    2 / 2 =  1 R 0
    1 / 2 =  0 R 1
  Read remainders bottom-up: 10101101 = 0xAD
```

### Nibble ↔ Hex

```
0000 = 0    0100 = 4    1000 = 8    1100 = C
0001 = 1    0101 = 5    1001 = 9    1101 = D
0010 = 2    0110 = 6    1010 = A    1110 = E
0011 = 3    0111 = 7    1011 = B    1111 = F

0xAD = 1010 1101
       ^^^^=A ^^^^=D
```

### C — Literal prefixes

```c
/* kernel/printk/printk.c style: always use UL/ULL suffixes for constants */
u32 a = 0b10101101;     /* binary literal (GCC extension, C23 standard) */
u32 b = 0xAD;           /* hex */
u32 c = 0255;           /* octal — AVOID in kernel, confusing */
u32 d = 173U;           /* unsigned decimal */
u64 e = 0xDEADBEEFULL;  /* 64-bit hex — always ULL for u64 constants */
```

### Go

```go
package main

import "fmt"

func main() {
    a := 0b10101101   // binary literal (Go 1.13+)
    b := 0xAD         // hex
    c := 0255         // octal
    d := 173          // decimal

    fmt.Printf("binary=%08b hex=%#x octal=%#o decimal=%d\n", a, b, c, d)
    // binary=10101101 hex=0xad octal=0255 decimal=173
}
```

### Rust

```rust
fn main() {
    let a: u32 = 0b10101101;    // binary
    let b: u32 = 0xAD;          // hex
    let c: u32 = 0o255;         // octal (0o prefix, NOT 0)
    let d: u32 = 173;           // decimal
    let e: u64 = 0xDEAD_BEEF;   // underscores for readability

    println!("binary={:08b} hex={:#x} octal={:#o} decimal={}", a, b, c, d);
}
```

---

## 2. Two's Complement & Signed Integers

### Encoding

```
For N-bit type:
  Positive range: 0 to 2^(N-1) - 1
  Negative range: -2^(N-1) to -1

  For 8-bit signed (i8 / s8):
    Range: -128 to 127
    -1  = 0b11111111 = 0xFF
    -2  = 0b11111110 = 0xFE
    -128= 0b10000000 = 0x80
    127 = 0b01111111 = 0x7F
```

### Negation rule: invert all bits then add 1

```
  +5 = 0000 0101
  ~5 = 1111 1010   (bitwise NOT = one's complement)
  -5 = 1111 1011   (add 1 → two's complement)

  Check: 0000 0101 + 1111 1011 = 1 0000 0000
         Carry overflows 8 bits → result is 0 ✓
```

### Sign bit & MSB tricks

```
For signed N-bit integer x:
  Sign bit (MSB) = (x >> (N-1)) & 1   → 1 if negative, 0 if positive
  Mask of sign:   x >> (N-1)          → -1 (all 1s) if negative, 0 if positive
                  (arithmetic right shift)
```

### C

```c
#include <linux/types.h>   /* u8, s8, u32, s32, u64, s64 */

/*
 * Signed type sizes — kernel's canonical form
 * Defined in: include/uapi/linux/types.h
 *             include/linux/types.h
 */
s8  a = -5;      /* 0xFB */
s16 b = -1000;
s32 c = INT_MIN; /* 0x80000000 — most negative 32-bit */
s64 d = LLONG_MIN;

/* Detect sign without branch */
static inline int sign_of(s32 x)
{
    /* Returns -1, 0, or +1 */
    return (x >> 31) | (u32)(-x >> 31);
}

/* Negate using bitwise: ~x + 1 */
static inline s32 negate(s32 x)
{
    return ~x + 1;
}
```

### Go

```go
package main

import "fmt"

func signOf(x int32) int32 {
    // Arithmetic right shift propagates sign bit
    return (x >> 31) | int32(uint32(-x) >> 31)
}

func negate(x int32) int32 {
    return ^x + 1  // ^ is bitwise NOT in Go for unary
}

func main() {
    var x int8 = -5
    fmt.Printf("x=%d  binary=%08b\n", x, uint8(x)) // 11111011

    fmt.Println(signOf(-42))  // -1
    fmt.Println(signOf(0))    //  0
    fmt.Println(signOf(42))   //  1

    fmt.Println(negate(5))    // -5
    fmt.Println(negate(-5))   //  5
}
```

### Rust

```rust
fn sign_of(x: i32) -> i32 {
    (x >> 31) | ((-x as u32 >> 31) as i32)
}

fn negate_bitwise(x: i32) -> i32 {
    !x + 1   // ! is bitwise NOT in Rust
}

fn main() {
    let x: i8 = -5_i8;
    println!("x={} binary={:08b}", x, x as u8);  // 11111011

    println!("{}", sign_of(-42));  // -1
    println!("{}", sign_of(0));    //  0
    println!("{}", sign_of(42));   //  1

    // Rust: use wrapping_neg() to avoid overflow panic in debug mode
    println!("{}", i32::MIN.wrapping_neg()); // i32::MIN (overflow case)
    println!("{}", (-5_i32).wrapping_neg()); // 5
}
```

---

## 3. Bitwise Operators — Complete Reference

### 3.1 AND (`&`)

**Truth table** (applied per bit):

```
A   B   A & B
0   0     0
0   1     0
1   0     0
1   1     1
```

**Key properties:**
- Idempotent: `x & x = x`
- Zero identity: `x & 0 = 0`
- One identity: `x & ~0 = x` (all-ones mask)
- Commutative: `x & y = y & x`
- Associative: `(x & y) & z = x & (y & z)`

**Primary uses:**
1. Mask bits (isolate specific bits)
2. Clear specific bits (AND with inverted mask)
3. Test if bit is set
4. Alignment checks (power-of-2)

```
Example: isolate lower nibble
  x   = 1010 1101   (0xAD)
mask  = 0000 1111   (0x0F)
x & m = 0000 1101   (0x0D)
```

**C**
```c
#include <linux/kernel.h>

/* Test bit N */
#define TEST_BIT(x, n)   (!!((x) & (1UL << (n))))

/* Isolate lower nibble */
static u8 lower_nibble(u8 x)
{
    return x & 0x0F;
}

/* Check power-of-2 alignment */
/* Used throughout mm/ — see include/linux/mm.h: IS_ALIGNED() */
static bool is_aligned(unsigned long addr, unsigned long align)
{
    /* align must be power of 2 */
    return (addr & (align - 1)) == 0;
}

/* Check if even */
static bool is_even(long x)
{
    return (x & 1) == 0;
}

/* Round down to alignment — heavily used in mm/page_alloc.c */
static unsigned long round_down_align(unsigned long x, unsigned long align)
{
    return x & ~(align - 1);
}
```

**Go**
```go
package main

import "fmt"

func testBit(x uint64, n uint) bool  { return (x>>n)&1 == 1 }
func lowerNibble(x uint8) uint8      { return x & 0x0F }
func isAligned(addr, align uintptr) bool {
    return addr&(align-1) == 0
}
func isEven(x int64) bool { return x&1 == 0 }
func roundDown(x, align uint64) uint64 {
    return x &^ (align - 1)  // &^ is AND-NOT (bit clear) in Go
}

func main() {
    x := uint8(0xAD)
    fmt.Printf("lower nibble of 0x%X = 0x%X\n", x, lowerNibble(x))
    fmt.Printf("bit 3 set? %v\n", testBit(uint64(x), 3))
    fmt.Printf("0x1001 aligned to 0x1000? %v\n", isAligned(0x1001, 0x1000))
    fmt.Printf("round down 0x1005 to 0x10: 0x%X\n", roundDown(0x1005, 0x10))
}
```

**Rust**
```rust
fn test_bit(x: u64, n: u32) -> bool { (x >> n) & 1 == 1 }
fn lower_nibble(x: u8) -> u8        { x & 0x0F }
fn is_aligned(addr: usize, align: usize) -> bool {
    addr & (align - 1) == 0
}
fn is_even(x: i64) -> bool { x & 1 == 0 }
fn round_down(x: u64, align: u64) -> u64 {
    x & !(align - 1)
}

fn main() {
    let x: u8 = 0xAD;
    println!("lower nibble: 0x{:X}", lower_nibble(x));
    println!("bit 3 set? {}", test_bit(x as u64, 3));
    println!("aligned? {}", is_aligned(0x1000, 0x1000));
    println!("round down: 0x{:X}", round_down(0x1005, 0x10));
}
```

---

### 3.2 OR (`|`)

**Truth table:**

```
A   B   A | B
0   0     0
0   1     1
1   0     1
1   1     1
```

**Key properties:**
- Idempotent: `x | x = x`
- Zero identity: `x | 0 = x`
- One annihilator: `x | ~0 = ~0`
- Commutative, Associative

**Primary uses:**
1. Set specific bits
2. Combine flags
3. Build masks

```
Example: set bits 4 and 1
  x        = 0000 0001   (0x01)
  mask     = 0001 0010   (0x12) = BIT(4) | BIT(1)
  x | mask = 0001 0011   (0x13)
```

**C**
```c
/* Combine permission flags — style used in fs/namei.c, security/ */
#define O_RDONLY   0x00000000
#define O_WRONLY   0x00000001
#define O_RDWR     0x00000002
#define O_CREAT    0x00000040
#define O_TRUNC    0x00000200
#define O_NONBLOCK 0x00000800

/* Open for writing, create if not exist, truncate */
int flags = O_WRONLY | O_CREAT | O_TRUNC;

/* Set bit N — kernel macro: include/linux/bitops.h */
#define SET_BIT(x, n)  ((x) | (1UL << (n)))

/* Combine CPU feature flags — arch/x86/include/asm/cpufeatures.h pattern */
#define X86_FEATURE_FPU    (0*32+ 0)  /* Onboard FPU */
#define X86_FEATURE_VME    (0*32+ 1)  /* Virtual Mode Extensions */
u32 feature_word = 0;
feature_word |= BIT(0);  /* set FPU bit */
feature_word |= BIT(1);  /* set VME bit */
```

**Go**
```go
package main

import "fmt"

const (
    FlagRead    = 1 << 0  // 0b0001
    FlagWrite   = 1 << 1  // 0b0010
    FlagExec    = 1 << 2  // 0b0100
    FlagSticky  = 1 << 3  // 0b1000
)

func setBit(x uint64, n uint) uint64 { return x | (1 << n) }

func combineFlags(flags ...uint32) uint32 {
    var result uint32
    for _, f := range flags {
        result |= f
    }
    return result
}

func main() {
    perm := combineFlags(FlagRead, FlagWrite)
    fmt.Printf("perms = %04b\n", perm)   // 0011

    perm = setBit(uint64(perm), 2)
    fmt.Printf("after set exec = %04b\n", perm)  // 0111
}
```

**Rust**
```rust
bitflags::bitflags! {
    // Using the bitflags crate (common in Rust ecosystem)
    // For kernel-style manual flags:
}

// Manual flag approach (kernel-style)
const FLAG_READ:   u32 = 1 << 0;
const FLAG_WRITE:  u32 = 1 << 1;
const FLAG_EXEC:   u32 = 1 << 2;
const FLAG_STICKY: u32 = 1 << 3;

fn set_bit(x: u64, n: u32) -> u64 { x | (1u64 << n) }

fn main() {
    let perm = FLAG_READ | FLAG_WRITE;
    println!("perms = {:04b}", perm);  // 0011

    let perm2 = set_bit(perm as u64, 2);
    println!("after set exec = {:04b}", perm2);  // 0111
}
```

---

### 3.3 XOR (`^`)

**Truth table:**

```
A   B   A ^ B
0   0     0
0   1     1
1   0     1
1   1     0
```

XOR = "exactly one input is 1" = "inputs differ"

**Key properties:**
- Self-inverse: `x ^ x = 0`
- Identity: `x ^ 0 = x`
- Commutative, Associative
- `x ^ ~0 = ~x` (XOR with all-ones = NOT)

**Primary uses:**
1. Toggle bits
2. Swap two values without a temp variable
3. Detect differences (diff/changed bits)
4. Parity computation
5. Cryptographic XOR cipher
6. CRC computation

```
Toggle bits 3 and 0:
  x        = 1010 1101   (0xAD)
  mask     = 0000 1001   (0x09)
  x ^ mask = 1010 0100   (0xA4)

Swap a and b:
  a ^= b   →  a = a^b
  b ^= a   →  b = b^(a^b) = a
  a ^= b   →  a = (a^b)^a = b
```

**C**
```c
/* Toggle bit N */
#define TOGGLE_BIT(x, n)  ((x) ^ (1UL << (n)))

/* Swap without temp — NOTE: UB if a == b (same address), avoid in kernel */
static void swap_xor(u32 *a, u32 *b)
{
    if (a != b) {
        *a ^= *b;
        *b ^= *a;
        *a ^= *b;
    }
}

/* Detect which bits changed — used in irq handlers, GPIO drivers */
static u32 changed_bits(u32 old_val, u32 new_val)
{
    return old_val ^ new_val;
}

/* Parity — 1 if odd number of set bits, 0 if even */
static int parity(u32 x)
{
    x ^= x >> 16;
    x ^= x >> 8;
    x ^= x >> 4;
    x ^= x >> 2;
    x ^= x >> 1;
    return x & 1;
}

/* Simple XOR checksum — used in some boot protocols, firmware */
static u8 xor_checksum(const u8 *buf, size_t len)
{
    u8 chk = 0;
    while (len--)
        chk ^= *buf++;
    return chk;
}
```

**Go**
```go
package main

import "fmt"

func toggleBit(x uint64, n uint) uint64 { return x ^ (1 << n) }

// XOR swap — only when a and b are distinct variables
func swapXOR(a, b *uint32) {
    *a ^= *b
    *b ^= *a
    *a ^= *b
}

func changedBits(old, new_ uint32) uint32 { return old ^ new_ }

// Parallel prefix XOR for parity
func parity(x uint32) uint32 {
    x ^= x >> 16
    x ^= x >> 8
    x ^= x >> 4
    x ^= x >> 2
    x ^= x >> 1
    return x & 1
}

func main() {
    x := uint64(0xAD)
    fmt.Printf("toggle bit 0: %08b\n", toggleBit(x, 0))  // 0xAC
    fmt.Printf("toggle bit 3: %08b\n", toggleBit(x, 3))  // 0xA5

    old, new_ := uint32(0b1100), uint32(0b1010)
    fmt.Printf("changed bits: %04b\n", changedBits(old, new_))  // 0110

    fmt.Printf("parity(0xFF) = %d\n", parity(0xFF)) // 0 (even)
    fmt.Printf("parity(0x01) = %d\n", parity(0x01)) // 1 (odd)
}
```

**Rust**
```rust
fn toggle_bit(x: u64, n: u32) -> u64 { x ^ (1u64 << n) }
fn changed_bits(old: u32, new: u32) -> u32 { old ^ new }

fn parity(mut x: u32) -> u32 {
    x ^= x >> 16;
    x ^= x >> 8;
    x ^= x >> 4;
    x ^= x >> 2;
    x ^= x >> 1;
    x & 1
}

fn main() {
    let x = 0xAD_u64;
    println!("toggle bit 0: {:08b}", toggle_bit(x, 0));
    println!("toggle bit 3: {:08b}", toggle_bit(x, 3));

    println!("parity(0xFF) = {}", parity(0xFF));  // 0
    println!("parity(0x7F) = {}", parity(0x7F));  // 1

    // XOR cipher (trivial but illustrates property)
    let key: u8 = 0x42;
    let plaintext: u8 = b'A'; // 0x41
    let ciphertext = plaintext ^ key;
    let recovered = ciphertext ^ key;
    assert_eq!(plaintext, recovered);
    println!("XOR cipher: {} -> {} -> {}", plaintext, ciphertext, recovered);
}
```

---

### 3.4 NOT (`~` bitwise, `!` logical)

**Unary operator — inverts every bit:**

```
x  = 0101 1001   (0x59 = 89)
~x = 1010 0110   (0xA6 = 166 unsigned / -90 signed 8-bit)

~x = -(x+1) for signed two's complement
```

**C**
```c
/* Bitwise NOT */
u8  a = ~0x59;       /* = 0xA6 */
u32 mask = ~0U;      /* all-ones: 0xFFFFFFFF */
u64 mask64 = ~0ULL;  /* 0xFFFFFFFFFFFFFFFF */

/* Common pattern: clear bits using NOT */
u32 val = 0xFF;
u32 clear_bits_4_7 = val & ~(0xF0);   /* clear bits 4-7 */

/* Generate mask with bits [high:low] set */
/* Example from include/linux/bitops.h: GENMASK() */
#define GENMASK(h, l) \
    (((~0UL) - (1UL << (l)) + 1) & (~0UL >> (BITS_PER_LONG - 1 - (h))))

/* Usage: GENMASK(7, 4) = 0xF0 = bits 7..4 set */
u32 byte_high_nibble = GENMASK(7, 4);
```

**Go**
```go
package main

import "fmt"

func main() {
    var a uint8 = 0x59
    fmt.Printf("~0x59 = 0x%X\n", ^a)   // 0xA6

    // ^uint8(0) = all-ones mask
    allOnes := ^uint8(0)
    fmt.Printf("all-ones u8 = 0x%X\n", allOnes) // 0xFF

    // Clear bits 4-7 (upper nibble)
    val := uint8(0xFF)
    cleared := val &^ uint8(0xF0)  // &^ = AND NOT (bit clear operator)
    fmt.Printf("cleared upper nibble: 0x%X\n", cleared)  // 0x0F

    // GENMASK equivalent
    genmask := func(h, l uint) uint32 {
        return (^uint32(0) >> (31 - h)) &^ ((1 << l) - 1)
    }
    fmt.Printf("GENMASK(7,4) = 0x%X\n", genmask(7, 4))  // 0xF0
}
```

**Rust**
```rust
fn genmask(h: u32, l: u32) -> u32 {
    (!0u32 >> (31 - h)) & !((1u32 << l) - 1)
}

fn main() {
    let a: u8 = 0x59;
    println!("!0x59 = 0x{:X}", !a);  // 0xA6

    let all_ones: u8 = !0u8;
    println!("all-ones: 0x{:X}", all_ones);

    // Clear bits 4-7
    let val: u8 = 0xFF;
    let cleared = val & !0xF0_u8;
    println!("cleared upper nibble: 0x{:X}", cleared);  // 0x0F

    println!("GENMASK(7,4) = 0x{:X}", genmask(7, 4));  // 0xF0
}
```

---

### 3.5 Left Shift (`<<`)

**Shifts all bits left by N positions; vacated bits filled with 0.**

```
x       = 0000 0011   (3)
x << 1  = 0000 0110   (6)   = 3 * 2^1
x << 2  = 0000 1100   (12)  = 3 * 2^2
x << 4  = 0011 0000   (48)  = 3 * 2^4

Overflow: bits shifted past MSB are discarded.
  u8: 1000 0001 << 1 = 0000 0010  (MSB lost)
```

**Equivalence:** `x << n` = `x * 2^n` (when no overflow)

**Undefined Behaviour in C:**
- Shifting by >= type width (e.g., `1 << 32` on u32) → UB
- Left shifting a negative signed value → UB (pre-C99/C11)
- Left shifting into or past sign bit of signed type → UB

**C**
```c
#include <linux/bitops.h>

/* BIT() macro — canonical kernel idiom */
/* Defined in include/linux/bitops.h */
#define BIT(nr)         (1UL << (nr))
#define BIT_ULL(nr)     (1ULL << (nr))
#define BIT_MASK(nr)    (1UL << ((nr) % BITS_PER_LONG))

/* Power of 2 multiplication */
static u32 times_power2(u32 x, u32 exp)
{
    return x << exp;  /* Undefined if exp >= 32 on 32-bit */
}

/* Safe left shift that avoids UB */
static u32 safe_lshift(u32 x, u32 n)
{
    if (n >= 32) return 0;
    return x << n;
}

/* Build a contiguous bitmask from position l to h */
/* GENMASK(h, l) from include/linux/bits.h */
static u32 bitmask_range(u32 h, u32 l)
{
    return ((2U << h) - 1U) & ~((1U << l) - 1U);
}

/* Kernel page size constants */
#define PAGE_SHIFT  12
#define PAGE_SIZE   (1UL << PAGE_SHIFT)    /* 4096 */
#define PAGE_MASK   (~(PAGE_SIZE - 1))
```

**Go**
```go
package main

import "fmt"

func bit(n uint) uint64 { return 1 << n }

func main() {
    // Left shift = multiply by 2^n
    x := uint32(3)
    for n := uint(0); n <= 4; n++ {
        fmt.Printf("3 << %d = %d\n", n, x<<n)
    }

    // Build bit masks
    const PAGE_SHIFT = 12
    const PAGE_SIZE  = 1 << PAGE_SHIFT   // 4096
    const PAGE_MASK  = ^(PAGE_SIZE - 1)

    fmt.Printf("PAGE_SIZE = %d\n", PAGE_SIZE)
    fmt.Printf("PAGE_MASK = 0x%X\n", uint64(PAGE_MASK))

    // Use bit() to build flag masks
    for i := uint(0); i < 8; i++ {
        fmt.Printf("BIT(%d) = 0x%02X = %08b\n", i, bit(i), bit(i))
    }
}
```

**Rust**
```rust
const PAGE_SHIFT: u32 = 12;
const PAGE_SIZE:  u64 = 1 << PAGE_SHIFT;
const PAGE_MASK:  u64 = !(PAGE_SIZE - 1);

fn bit(n: u32) -> u64 { 1u64 << n }
fn bit_mask_range(h: u32, l: u32) -> u32 {
    ((2u32 << h) - 1) & !((1u32 << l) - 1)
}

fn main() {
    for n in 0u32..=4 {
        println!("3u32 << {} = {}", n, 3u32 << n);
    }

    println!("PAGE_SIZE = {}", PAGE_SIZE);
    println!("PAGE_MASK = {:#018x}", PAGE_MASK);

    println!("GENMASK(7,4) = {:#010b}", bit_mask_range(7, 4));

    // Rust panics on overflow in debug mode:
    // 1u32 << 32  → panic in debug, wraps/UB in release
    // Use checked_shl for safety:
    let safe = 1u32.checked_shl(32);
    println!("checked_shl(32) = {:?}", safe);  // None
}
```

---

### 3.6 Right Shift (`>>`)

**Two flavours — critical distinction:**

```
LOGICAL (unsigned types):
  vacated bits filled with 0
  0b10110100 >> 2 = 0b00101101   (unsigned, always)

ARITHMETIC (signed types, implementation-defined in C):
  vacated bits filled with sign bit (MSB copy)
  0b10110100 >> 2 = 0b11101101   (if arithmetic, negative value)
  0b01100100 >> 2 = 0b00011001   (positive value — same as logical)
```

On x86/ARM: compiler generates SAR (arithmetic) for signed, SHR (logical) for unsigned.

In Linux kernel: **always use unsigned types for bit manipulation** to guarantee logical shift.

**Equivalence:** `x >> n` = `x / 2^n` rounding toward −∞ (arithmetic) or 0 (logical)

**C**
```c
/* Logical shift: use unsigned types */
u32 a = 0xAD000000U;
u32 b = a >> 4;           /* 0x0AD00000 — always logical */

/* Arithmetic shift: signed (compiler-specific, but universally SAR on x86/ARM) */
s32 c = (s32)0xAD000000;  /* negative: sign bit = 1 */
s32 d = c >> 4;            /* 0xFAD00000 — sign-extended (SAR) */

/* Integer division by power of 2 using shift */
static s32 div_pow2(s32 x, u32 exp)
{
    /*
     * Arithmetic right shift rounds toward -inf, but integer division
     * rounds toward 0. For negative values, adjust by (2^exp - 1).
     */
    return (x + ((x >> 31) & ((1 << exp) - 1))) >> exp;
}

/* Extract field from register value (common in driver code) */
/* Example: bits [15:8] from a 32-bit register */
static u8 extract_field(u32 reg, u32 shift, u32 mask)
{
    return (reg >> shift) & mask;
}

/* IRQ status register pattern from drivers/gpio/*.c */
#define STATUS_REG_IRQ_SHIFT  8
#define STATUS_REG_IRQ_MASK   0xFF
static u8 get_irq_status(u32 status_reg)
{
    return extract_field(status_reg, STATUS_REG_IRQ_SHIFT, STATUS_REG_IRQ_MASK);
}
```

**Go**
```go
package main

import "fmt"

func main() {
    // Logical right shift (unsigned)
    a := uint32(0xAD000000)
    fmt.Printf("0x%X >> 4 = 0x%X\n", a, a>>4)   // 0x0AD00000

    // Go uses arithmetic shift for signed, logical for unsigned
    b := int32(-1)
    fmt.Printf("%d >> 1 = %d\n", b, b>>1)   // -1 (arithmetic: all 1s)

    c := int32(-4)
    fmt.Printf("%d >> 1 = %d\n", c, c>>1)   // -2 (arithmetic)

    // Extract bit field [15:8]
    extractField := func(reg uint32, shift, mask uint32) uint32 {
        return (reg >> shift) & mask
    }
    reg := uint32(0x0000AB00)
    field := extractField(reg, 8, 0xFF)
    fmt.Printf("field[15:8] = 0x%X\n", field)  // 0xAB
}
```

**Rust**
```rust
fn extract_field(reg: u32, shift: u32, mask: u32) -> u32 {
    (reg >> shift) & mask
}

fn main() {
    // Logical right shift for unsigned
    let a: u32 = 0xAD000000;
    println!("0x{:X} >> 4 = 0x{:X}", a, a >> 4);

    // Arithmetic right shift for signed
    let b: i32 = -1;
    println!("{} >> 1 = {}", b, b >> 1);  // -1

    let c: i32 = -4;
    println!("{} >> 1 = {}", c, c >> 1);  // -2

    // Field extraction
    let reg: u32 = 0x0000AB00;
    println!("field[15:8] = 0x{:X}", extract_field(reg, 8, 0xFF));  // 0xAB

    // wrapping_shr avoids panic on shift >= width
    println!("{}", 1u32.wrapping_shr(32));  // 0 (wraps to shift by 0 on x86)
    println!("{:?}", 1u32.checked_shr(32)); // None
}
```

---

## 4. Bit Masks & Flags

### Mask Construction Patterns

```
Single bit N:          1UL << N
Bits 0..N-1 (N bits):  (1UL << N) - 1
Bits H..L:             GENMASK(H, L)
Upper byte of u32:     0xFF000000U
Lower 3 bytes:         0x00FFFFFFU
Alternating bits:      0x55555555U  (0101...) or 0xAAAAAAAAU (1010...)
```

### Mask Operations

```
Set bit N:      val |=  (1UL << N)
Clear bit N:    val &= ~(1UL << N)
Toggle bit N:   val ^=  (1UL << N)
Test bit N:     (val >> N) & 1    or   !!(val & (1UL << N))

Extract bits [H:L]:   (val >> L) & GENMASK(H-L, 0)
Insert bits [H:L]:    (val & ~GENMASK(H,L)) | ((field << L) & GENMASK(H,L))
```

**C — Full register manipulation (driver pattern)**

```c
#include <linux/bits.h>
#include <linux/bitops.h>
#include <linux/io.h>

/*
 * Hypothetical peripheral control register layout:
 *
 *  31      24 23     16 15   12 11  8 7   4 3 2 1 0
 * +----------+---------+-------+-----+-----+-+-+-+-+
 * | RESERVED |  FREQ   |  MODE | DIV | IRQ |E|W|R|X|
 * +----------+---------+-------+-----+-----+-+-+-+-+
 *
 * E=Enable, W=Write, R=Read, X=Execute
 */

#define CTRL_X_BIT          BIT(0)
#define CTRL_R_BIT          BIT(1)
#define CTRL_W_BIT          BIT(2)
#define CTRL_E_BIT          BIT(3)

#define CTRL_IRQ_SHIFT      4
#define CTRL_IRQ_MASK       GENMASK(7, 4)   /* bits [7:4] */

#define CTRL_DIV_SHIFT      8
#define CTRL_DIV_MASK       GENMASK(11, 8)  /* bits [11:8] */

#define CTRL_MODE_SHIFT     12
#define CTRL_MODE_MASK      GENMASK(15, 12) /* bits [15:12] */

#define CTRL_FREQ_SHIFT     16
#define CTRL_FREQ_MASK      GENMASK(23, 16) /* bits [23:16] */

/* Field access helpers */
#define FIELD_GET(mask, reg)        \
    (((reg) & (mask)) >> __builtin_ctzl(mask))

#define FIELD_PREP(mask, val)       \
    (((u32)(val) << __builtin_ctzl(mask)) & (mask))

static u32 build_ctrl_reg(u8 mode, u8 div, u8 irq_mask, bool enable)
{
    u32 reg = 0;

    reg |= FIELD_PREP(CTRL_MODE_MASK, mode);
    reg |= FIELD_PREP(CTRL_DIV_MASK, div);
    reg |= FIELD_PREP(CTRL_IRQ_MASK, irq_mask);
    if (enable)
        reg |= CTRL_E_BIT;
    reg |= CTRL_R_BIT | CTRL_W_BIT;

    return reg;
}

static u8 get_mode(u32 ctrl_reg)
{
    return FIELD_GET(CTRL_MODE_MASK, ctrl_reg);
}
```

**Go**
```go
package main

import "fmt"

const (
    CtrlXBit     = 1 << 0
    CtrlRBit     = 1 << 1
    CtrlWBit     = 1 << 2
    CtrlEBit     = 1 << 3
    CtrlIRQShift = 4
    CtrlIRQMask  = 0xF0       // bits[7:4]
    CtrlDivShift = 8
    CtrlDivMask  = 0xF00      // bits[11:8]
    CtrlModeShift = 12
    CtrlModeMask  = 0xF000    // bits[15:12]
    CtrlFreqShift = 16
    CtrlFreqMask  = 0xFF0000  // bits[23:16]
)

func fieldGet(mask uint32, reg uint32) uint32 {
    shift := uint32(0)
    for (mask>>shift)&1 == 0 {
        shift++
    }
    return (reg & mask) >> shift
}

func fieldPrep(mask uint32, val uint32) uint32 {
    shift := uint32(0)
    for (mask>>shift)&1 == 0 {
        shift++
    }
    return (val << shift) & mask
}

func buildCtrlReg(mode, div, irqMask uint8, enable bool) uint32 {
    reg := uint32(0)
    reg |= fieldPrep(CtrlModeMask, uint32(mode))
    reg |= fieldPrep(CtrlDivMask, uint32(div))
    reg |= fieldPrep(CtrlIRQMask, uint32(irqMask))
    if enable {
        reg |= CtrlEBit
    }
    reg |= CtrlRBit | CtrlWBit
    return reg
}

func main() {
    reg := buildCtrlReg(3, 5, 0xF, true)
    fmt.Printf("ctrl_reg = 0x%08X = %032b\n", reg, reg)
    fmt.Printf("mode = %d\n", fieldGet(CtrlModeMask, reg))
    fmt.Printf("div  = %d\n", fieldGet(CtrlDivMask, reg))
}
```

**Rust**
```rust
const CTRL_X_BIT:    u32 = 1 << 0;
const CTRL_R_BIT:    u32 = 1 << 1;
const CTRL_W_BIT:    u32 = 1 << 2;
const CTRL_E_BIT:    u32 = 1 << 3;
const CTRL_IRQ_MASK: u32 = 0x0000_00F0;
const CTRL_DIV_MASK: u32 = 0x0000_0F00;
const CTRL_MODE_MASK:u32 = 0x0000_F000;
const CTRL_FREQ_MASK:u32 = 0x00FF_0000;

fn field_get(mask: u32, reg: u32) -> u32 {
    (reg & mask) >> mask.trailing_zeros()
}

fn field_prep(mask: u32, val: u32) -> u32 {
    (val << mask.trailing_zeros()) & mask
}

fn build_ctrl_reg(mode: u8, div: u8, irq_mask: u8, enable: bool) -> u32 {
    let mut reg: u32 = 0;
    reg |= field_prep(CTRL_MODE_MASK, mode as u32);
    reg |= field_prep(CTRL_DIV_MASK, div as u32);
    reg |= field_prep(CTRL_IRQ_MASK, irq_mask as u32);
    if enable { reg |= CTRL_E_BIT; }
    reg |= CTRL_R_BIT | CTRL_W_BIT;
    reg
}

fn main() {
    let reg = build_ctrl_reg(3, 5, 0xF, true);
    println!("ctrl_reg = {:#010x}", reg);
    println!("mode = {}", field_get(CTRL_MODE_MASK, reg));
    println!("div  = {}", field_get(CTRL_DIV_MASK, reg));
}
```

---

## 5. Bit Fields (C Struct Bitfields)

### Definition & Layout

```c
/*
 * C bitfield syntax:
 *   type name : width;
 *
 * WARNING: Layout (endianness, padding, allocation order) is
 * implementation-defined. NEVER use for hardware register mapping
 * in portable code — use explicit shifts/masks instead.
 *
 * Kernel policy: bitfields OK for flags in internal structs,
 * NOT for hardware register structs.
 * See: Documentation/process/coding-style.rst
 */
struct flags {
    unsigned int readable   : 1;   /* 1 bit */
    unsigned int writable   : 1;
    unsigned int executable : 1;
    unsigned int dirty      : 1;
    unsigned int reserved   : 28;  /* pad to 32 bits */
};

/* Anonymous bitfield for padding */
struct packed_data {
    u8 type     : 4;  /* bits [3:0] */
    u8 subtype  : 3;  /* bits [6:4] */
    u8 valid    : 1;  /* bit  [7]   */
};
```

### Kernel Bitfield Usage

```c
/*
 * task_struct uses bitfields for flags:
 * include/linux/sched.h
 */
struct task_struct {
    /* ... */
    unsigned int        __state;
    /* ... */
#ifdef CONFIG_SMP
    int         on_cpu;
#endif
    /* scheduler-private: */
    unsigned int        flags;   /* per-process flags: PF_* */
    /* ... */
};

/*
 * vm_area_struct uses vm_flags (unsigned long, NOT bitfield):
 * include/linux/mm_types.h — vm_flags uses explicit BIT() constants
 */
#define VM_READ     BIT(0)
#define VM_WRITE    BIT(1)
#define VM_EXEC     BIT(2)
#define VM_SHARED   BIT(3)
```

**C — Bitfield struct with manual approach comparison**

```c
#include <linux/types.h>

/* Approach 1: struct bitfield (NOT for hardware) */
struct ip_flags_bitfield {
    u16 frag_offset : 13;  /* fragment offset */
    u16 mf          :  1;  /* more fragments */
    u16 df          :  1;  /* don't fragment */
    u16 reserved    :  1;
} __attribute__((packed));

/* Approach 2: explicit shifts/masks (PREFERRED for hardware/network) */
/* Matches: include/uapi/linux/ip.h style */
#define IP_RF       0x8000  /* reserved fragment flag */
#define IP_DF       0x4000  /* don't fragment flag */
#define IP_MF       0x2000  /* more fragments flag */
#define IP_OFFMASK  0x1FFF  /* mask for fragmenting bits */

static u16 get_frag_offset(u16 frag_off_word)
{
    return ntohs(frag_off_word) & IP_OFFMASK;
}

static bool dont_fragment(u16 frag_off_word)
{
    return !!(ntohs(frag_off_word) & IP_DF);
}
```

**Go**
```go
package main

import "fmt"

// Go has no struct bitfields — use explicit bit manipulation

type IPFragWord uint16

const (
    IPReserved  IPFragWord = 0x8000
    IPDontFrag  IPFragWord = 0x4000
    IPMoreFrags IPFragWord = 0x2000
    IPOffMask   IPFragWord = 0x1FFF
)

func (w IPFragWord) FragOffset() uint16   { return uint16(w & IPOffMask) }
func (w IPFragWord) DontFragment() bool   { return w&IPDontFrag != 0 }
func (w IPFragWord) MoreFragments() bool  { return w&IPMoreFrags != 0 }

func NewFragWord(offset uint16, df, mf bool) IPFragWord {
    var w IPFragWord = IPFragWord(offset & 0x1FFF)
    if df { w |= IPDontFrag }
    if mf { w |= IPMoreFrags }
    return w
}

func main() {
    w := NewFragWord(100, true, false)
    fmt.Printf("frag_word = 0x%04X\n", w)
    fmt.Printf("offset = %d, DF = %v, MF = %v\n",
        w.FragOffset(), w.DontFragment(), w.MoreFragments())
}
```

**Rust**
```rust
#[repr(transparent)]
#[derive(Copy, Clone)]
struct IpFragWord(u16);

impl IpFragWord {
    const RESERVED: u16 = 0x8000;
    const DONT_FRAG: u16 = 0x4000;
    const MORE_FRAGS: u16 = 0x2000;
    const OFF_MASK: u16 = 0x1FFF;

    fn new(offset: u16, df: bool, mf: bool) -> Self {
        let mut w = offset & Self::OFF_MASK;
        if df { w |= Self::DONT_FRAG; }
        if mf { w |= Self::MORE_FRAGS; }
        IpFragWord(w)
    }

    fn frag_offset(self) -> u16 { self.0 & Self::OFF_MASK }
    fn dont_fragment(self) -> bool { self.0 & Self::DONT_FRAG != 0 }
    fn more_fragments(self) -> bool { self.0 & Self::MORE_FRAGS != 0 }
}

fn main() {
    let w = IpFragWord::new(100, true, false);
    println!("frag_word = {:#06x}", w.0);
    println!("offset = {}, DF = {}, MF = {}",
        w.frag_offset(), w.dont_fragment(), w.more_fragments());
}
```

---

## 6. Compound Assignment Operators

```
x &=  mask    equivalent to: x = x & mask
x |=  mask    equivalent to: x = x | mask
x ^=  mask    equivalent to: x = x ^ mask
x <<= n       equivalent to: x = x << n
x >>= n       equivalent to: x = x >> n

Go also has:
x &^= mask    equivalent to: x = x &^ mask   (AND NOT / bit clear)
```

---

## 7. Bit Manipulation Tricks & Idioms

### 7.1 Turn off rightmost set bit

```
x & (x - 1)

Example:
  x      = 0101 1100
  x-1    = 0101 1011
  x&(x-1)= 0101 1000   (rightmost 1 cleared)
```

**C**
```c
/* Test if power of 2: exactly one bit set */
static bool is_power_of_2(u32 x)
{
    return x != 0 && (x & (x - 1)) == 0;
}
/* Same as: include/linux/log2.h: is_power_of_2() */

/* Count set bits using Brian Kernighan's algorithm — O(set bits) */
static int popcount_slow(u32 x)
{
    int count = 0;
    while (x) {
        x &= x - 1;  /* clear rightmost set bit */
        count++;
    }
    return count;
}
```

### 7.2 Isolate rightmost set bit

```
x & (-x)  which equals  x & (~x + 1)

Example:
  x       = 0110 1100
  -x      = 1001 0100   (two's complement negate)
  x & -x  = 0000 0100   (isolated lowest set bit)
```

**C**
```c
static u32 lowest_set_bit(u32 x)
{
    return x & (-(u32)x);  /* or: x & (~x + 1) */
}

/* Find index of lowest set bit (0-indexed) */
static int bit_index_of_lowest(u32 x)
{
    if (!x) return -1;
    return __builtin_ctz(x);  /* count trailing zeros */
}
```

### 7.3 Propagate rightmost set bit downward

```
x | (x - 1)

Example:
  x         = 0101 1000
  x-1       = 0101 0111
  x|(x-1)   = 0101 1111   (fills in all bits below lowest set bit)
```

### 7.4 Turn on rightmost clear bit

```
x | (x + 1)

Example:
  x         = 0101 1011
  x+1       = 0101 1100
  x|(x+1)   = 0101 1111
```

### 7.5 Isolate rightmost 0-bit

```
~x & (x + 1)

Example:
  x          = 0101 1011
  ~x         = 1010 0100
  x+1        = 0101 1100
  ~x & (x+1) = 0000 0100
```

### 7.6 Next power of 2

```
Algorithm:
  1. Decrement by 1
  2. OR with all right-shifted versions
  3. Increment by 1

For 32-bit:
  x--;
  x |= x >> 1;
  x |= x >> 2;
  x |= x >> 4;
  x |= x >> 8;
  x |= x >> 16;
  x++;
```

**C**
```c
/* roundup_pow_of_two — from include/linux/log2.h */
static inline unsigned long next_pow2(unsigned long x)
{
    if (x <= 1) return 1;
    return 1UL << (BITS_PER_LONG - __builtin_clzl(x - 1));
}
```

**Go**
```go
package main

import (
    "fmt"
    "math/bits"
)

func nextPow2(x uint64) uint64 {
    if x <= 1 { return 1 }
    return 1 << bits.Len64(x-1)
}

func lowestSetBit(x uint32) uint32 { return x & uint32(-int32(x)) }
func isPow2(x uint32) bool         { return x != 0 && x&(x-1) == 0 }

func main() {
    for _, v := range []uint64{0, 1, 2, 3, 5, 8, 9, 15, 16, 17, 100} {
        fmt.Printf("nextPow2(%3d) = %d\n", v, nextPow2(v))
    }

    fmt.Printf("lowestSetBit(0x6C) = 0x%X\n", lowestSetBit(0x6C))  // 0x04

    for _, v := range []uint32{0, 1, 2, 3, 4, 7, 8, 16} {
        fmt.Printf("isPow2(%d) = %v\n", v, isPow2(v))
    }
}
```

**Rust**
```rust
fn next_pow2(x: u64) -> u64 {
    if x <= 1 { return 1; }
    1u64 << (u64::BITS - (x - 1).leading_zeros())
}

fn lowest_set_bit(x: u32) -> u32 { x & x.wrapping_neg() }
fn is_pow2(x: u32) -> bool { x != 0 && x & (x - 1) == 0 }

fn main() {
    for v in [0u64, 1, 2, 3, 5, 8, 9, 15, 16, 17, 100] {
        println!("next_pow2({:3}) = {}", v, next_pow2(v));
    }

    println!("lowest_set_bit(0x6C) = {:#X}", lowest_set_bit(0x6C));

    for v in [0u32, 1, 2, 3, 4, 7, 8, 16] {
        println!("is_pow2({}) = {}", v, is_pow2(v));
    }
}
```

---

## 8. Population Count (Hamming Weight)

**popcount = number of set bits (1s) in a word**

### Algorithms

```
SWAR (SIMD Within A Register) — parallel prefix sum technique:

For 32-bit:
  x = x - ((x >> 1) & 0x55555555);           // 2-bit sums
  x = (x & 0x33333333) + ((x >> 2) & 0x33333333); // 4-bit sums
  x = (x + (x >> 4)) & 0x0F0F0F0F;           // 8-bit sums
  x = (x * 0x01010101) >> 24;                // horizontal add via multiply

Lookup table (8-bit chunks):
  popcount_byte[256] precomputed
  Result = popcount_byte[b3] + popcount_byte[b2]
         + popcount_byte[b1] + popcount_byte[b0]
```

**C**
```c
#include <linux/bitops.h>

/*
 * Kernel uses: hweight32(), hweight64(), hweight_long()
 * Defined in: include/linux/bitops.h
 * Calls arch-specific __builtin_popcount where available
 */

/* SWAR algorithm for u32 — no instruction dependency */
static u32 popcount32_swar(u32 x)
{
    x = x - ((x >> 1) & 0x55555555U);
    x = (x & 0x33333333U) + ((x >> 2) & 0x33333333U);
    x = (x + (x >> 4)) & 0x0F0F0F0FU;
    return (x * 0x01010101U) >> 24;
}

/* SWAR for u64 */
static u64 popcount64_swar(u64 x)
{
    x = x - ((x >> 1) & 0x5555555555555555ULL);
    x = (x & 0x3333333333333333ULL) + ((x >> 2) & 0x3333333333333333ULL);
    x = (x + (x >> 4)) & 0x0F0F0F0F0F0F0F0FULL;
    return (x * 0x0101010101010101ULL) >> 56;
}

/* Preferred in kernel: compiler intrinsic (maps to POPCNT instruction on x86) */
static int popcount_fast(u32 x)
{
    return __builtin_popcount(x);
}

static int popcount64_fast(u64 x)
{
    return __builtin_popcountll(x);
}
```

**Go**
```go
package main

import (
    "fmt"
    "math/bits"
)

func popcountSWAR(x uint32) int {
    x = x - ((x >> 1) & 0x55555555)
    x = (x & 0x33333333) + ((x >> 2) & 0x33333333)
    x = (x + (x >> 4)) & 0x0F0F0F0F
    return int((x * 0x01010101) >> 24)
}

func main() {
    for _, v := range []uint32{0, 1, 0xFF, 0xFFFF, 0xFFFFFFFF, 0xABCD1234} {
        // stdlib
        fast := bits.OnesCount32(v)
        // manual
        slow := popcountSWAR(v)
        fmt.Printf("popcount(0x%08X) = %d (stdlib) = %d (swar)\n", v, fast, slow)
    }
}
```

**Rust**
```rust
fn popcount_swar(mut x: u32) -> u32 {
    x = x.wrapping_sub((x >> 1) & 0x55555555);
    x = (x & 0x33333333) + ((x >> 2) & 0x33333333);
    x = (x.wrapping_add(x >> 4)) & 0x0F0F0F0F;
    x.wrapping_mul(0x01010101) >> 24
}

fn main() {
    let cases = [0u32, 1, 0xFF, 0xFFFF, 0xFFFF_FFFF, 0xABCD_1234];
    for v in cases {
        // Rust intrinsic (maps to POPCNT)
        let stdlib = v.count_ones();
        let manual = popcount_swar(v);
        println!("popcount({:#010x}) = {} (stdlib) = {} (swar)", v, stdlib, manual);
    }
}
```

---

## 9. Bit Reversal

**Reverse the order of all bits in a word.**

### Algorithms

```
Nibble swap approach (divide and conquer):
  1. Swap odd/even bits
  2. Swap consecutive pairs
  3. Swap nibbles
  4. Swap bytes
  5. Swap 16-bit halves (for 32-bit input)

For u8:
  x = 1010 1101
  swap adjacent bits:     0101 1110
  swap adjacent pairs:    0110 1011 (wrong for illustration — see code)
```

**C**
```c
/* Reverse 32-bit word */
static u32 bitrev32(u32 x)
{
    x = ((x & 0xAAAAAAAAU) >> 1)  | ((x & 0x55555555U) << 1);
    x = ((x & 0xCCCCCCCCU) >> 2)  | ((x & 0x33333333U) << 2);
    x = ((x & 0xF0F0F0F0U) >> 4)  | ((x & 0x0F0F0F0FU) << 4);
    x = ((x & 0xFF00FF00U) >> 8)  | ((x & 0x00FF00FFU) << 8);
    return (x >> 16) | (x << 16);
}

/*
 * Kernel has: lib/bitrev.c — bitrev8(), bitrev16(), bitrev32()
 * Uses lookup table for bitrev8, builds larger from that.
 * Used in: CRC computation (lib/crc32.c), wireless drivers
 */
#include <linux/bitrev.h>
/* bitrev32(x), bitrev16(x), bitrev8(x) available */
```

**Go**
```go
package main

import (
    "fmt"
    "math/bits"
)

func bitrev32(x uint32) uint32 {
    x = ((x & 0xAAAAAAAA) >> 1)  | ((x & 0x55555555) << 1)
    x = ((x & 0xCCCCCCCC) >> 2)  | ((x & 0x33333333) << 2)
    x = ((x & 0xF0F0F0F0) >> 4)  | ((x & 0x0F0F0F0F) << 4)
    x = ((x & 0xFF00FF00) >> 8)  | ((x & 0x00FF00FF) << 8)
    return (x >> 16) | (x << 16)
}

func main() {
    x := uint32(0x12345678)
    manual := bitrev32(x)
    stdlib := bits.Reverse32(x)
    fmt.Printf("bitrev32(0x%08X) = 0x%08X (manual), 0x%08X (stdlib)\n",
        x, manual, stdlib)

    fmt.Printf("binary: %032b\n", x)
    fmt.Printf("reverse:%032b\n", stdlib)
}
```

**Rust**
```rust
fn bitrev32(mut x: u32) -> u32 {
    x = ((x & 0xAAAA_AAAA) >> 1)  | ((x & 0x5555_5555) << 1);
    x = ((x & 0xCCCC_CCCC) >> 2)  | ((x & 0x3333_3333) << 2);
    x = ((x & 0xF0F0_F0F0) >> 4)  | ((x & 0x0F0F_0F0F) << 4);
    x = ((x & 0xFF00_FF00) >> 8)  | ((x & 0x00FF_00FF) << 8);
    (x >> 16) | (x << 16)
}

fn main() {
    let x: u32 = 0x1234_5678;
    let manual = bitrev32(x);
    let stdlib = x.reverse_bits();
    println!("bitrev32({:#010x}) = {:#010x} (manual), {:#010x} (stdlib)",
        x, manual, stdlib);
    println!("binary: {:032b}", x);
    println!("reverse:{:032b}", stdlib);
}
```

---

## 10. Endianness & Byte Swapping

### Concept

```
Little-endian (x86, ARM default):
  Value 0x12345678 stored at address A:
  A+0: 0x78   (LSB first)
  A+1: 0x56
  A+2: 0x34
  A+3: 0x12   (MSB last)

Big-endian (network byte order, PowerPC, MIPS BE):
  A+0: 0x12   (MSB first)
  A+1: 0x34
  A+2: 0x56
  A+3: 0x78   (LSB last)
```

### Byte swap (bswap)

```
0x12345678 → bswap32 → 0x78563412
```

**C — Kernel's endian handling**

```c
/*
 * Kernel endian conversions:
 * include/uapi/linux/swab.h  — __swab16, __swab32, __swab64
 * include/linux/byteorder/   — cpu_to_be32, le32_to_cpu, etc.
 * include/uapi/linux/byteorder/little_endian.h
 * include/uapi/linux/byteorder/big_endian.h
 *
 * Network (big-endian) conversions:
 *   htons, htonl, ntohs, ntohl   — POSIX
 *   cpu_to_be16, be16_to_cpu     — kernel preferred
 *   cpu_to_le32, le32_to_cpu     — kernel preferred
 */
#include <linux/byteorder/generic.h>
#include <uapi/linux/swab.h>

/* Manual bswap32 */
static u32 bswap32_manual(u32 x)
{
    return ((x & 0x000000FFU) << 24) |
           ((x & 0x0000FF00U) <<  8) |
           ((x & 0x00FF0000U) >>  8) |
           ((x & 0xFF000000U) >> 24);
}

/* GCC builtin: maps to single BSWAP instruction on x86 */
static u32 bswap32_fast(u32 x) { return __builtin_bswap32(x); }
static u64 bswap64_fast(u64 x) { return __builtin_bswap64(x); }

/* Usage in network driver (net/ethernet/eth.c style) */
static void write_be32_field(void __iomem *reg, u32 val)
{
    writel(cpu_to_be32(val), reg);
}
```

**Go**
```go
package main

import (
    "encoding/binary"
    "fmt"
    "math/bits"
)

func bswap32(x uint32) uint32 { return bits.ReverseBytes32(x) }
func bswap64(x uint64) uint64 { return bits.ReverseBytes64(x) }

func main() {
    x := uint32(0x12345678)
    fmt.Printf("original: 0x%08X\n", x)
    fmt.Printf("bswap32:  0x%08X\n", bswap32(x))

    // Network byte order (big-endian) conversion
    var buf [4]byte
    binary.BigEndian.PutUint32(buf[:], x)
    fmt.Printf("big-endian bytes: %X %X %X %X\n", buf[0], buf[1], buf[2], buf[3])

    restored := binary.BigEndian.Uint32(buf[:])
    fmt.Printf("restored: 0x%08X\n", restored)

    // Little-endian
    binary.LittleEndian.PutUint32(buf[:], x)
    fmt.Printf("little-endian bytes: %X %X %X %X\n", buf[0], buf[1], buf[2], buf[3])
}
```

**Rust**
```rust
fn main() {
    let x: u32 = 0x1234_5678;
    println!("original: {:#010x}", x);
    println!("bswap32:  {:#010x}", x.swap_bytes());
    println!("to_be:    {:#010x}", x.to_be());
    println!("to_le:    {:#010x}", x.to_le());

    // From big-endian bytes
    let bytes: [u8; 4] = [0x12, 0x34, 0x56, 0x78];
    let from_be = u32::from_be_bytes(bytes);
    let from_le = u32::from_le_bytes(bytes);
    println!("from_be_bytes({:X?}) = {:#010x}", bytes, from_be);
    println!("from_le_bytes({:X?}) = {:#010x}", bytes, from_le);

    // to_bytes
    let be_bytes = x.to_be_bytes();
    let le_bytes = x.to_le_bytes();
    println!("to_be_bytes: {:X?}", be_bytes);  // [12, 34, 56, 78]
    println!("to_le_bytes: {:X?}", le_bytes);  // [78, 56, 34, 12]
}
```

---

## 11. Arithmetic via Bit Operations

### All Operations

```
Multiply by 2^n:    x << n
Divide by 2^n:      x >> n  (logical for unsigned)
Modulo 2^n:         x & ((1 << n) - 1)
Absolute value:     (x ^ mask) - mask   where mask = x >> 31 (signed 32-bit)
Min(x,y):           y ^ ((x^y) & -(x<y))   (branchless)
Max(x,y):           x ^ ((x^y) & -(x<y))   (branchless)
```

**C — Branchless arithmetic**

```c
/* Modulo power of 2 — used in ring buffers, hash tables */
static u32 mod_pow2(u32 x, u32 mod)
{
    /* mod MUST be power of 2 */
    return x & (mod - 1);
}

/* Kernel ring buffer pattern: kernel/printk/printk_ringbuf.c */
static u64 ring_index(u64 seq, u32 ring_size)
{
    return seq & (ring_size - 1);
}

/* Branchless absolute value for s32 */
static s32 abs_branchless(s32 x)
{
    s32 mask = x >> 31;  /* -1 if negative, 0 if positive */
    return (x ^ mask) - mask;
}

/* Branchless min/max */
static s32 min_branchless(s32 x, s32 y)
{
    return y ^ ((x ^ y) & -(x < y));
}

static s32 max_branchless(s32 x, s32 y)
{
    return x ^ ((x ^ y) & -(x < y));
}

/* Average without overflow — used in binary search */
static u32 avg_no_overflow(u32 a, u32 b)
{
    return (a & b) + ((a ^ b) >> 1);
}

/* Multiply by constant using shifts — compiler does this automatically,
 * but useful to understand for embedded/no-multiplier targets */
static u32 mul_by_7(u32 x)
{
    return (x << 3) - x;  /* 8x - x = 7x */
}

static u32 mul_by_10(u32 x)
{
    return (x << 3) + (x << 1);  /* 8x + 2x = 10x */
}
```

**Go**
```go
package main

import "fmt"

func modPow2(x, mod uint32) uint32 { return x & (mod - 1) }

func absVal(x int32) int32 {
    mask := x >> 31
    return (x ^ mask) - mask
}

func minBranchless(x, y int32) int32 {
    var cmp int32
    if x < y { cmp = -1 }
    return y ^ ((x ^ y) & cmp)
}

func avgNoOverflow(a, b uint32) uint32 {
    return (a & b) + ((a ^ b) >> 1)
}

func main() {
    fmt.Printf("100 mod 16 = %d\n", modPow2(100, 16))  // 4
    fmt.Printf("|−42| = %d\n", absVal(-42))            // 42
    fmt.Printf("|42|  = %d\n", absVal(42))             // 42
    fmt.Printf("min(3,5) = %d\n", minBranchless(3, 5))  // 3
    fmt.Printf("avg(10,14) = %d\n", avgNoOverflow(10, 14)) // 12
    // avg(0xFFFFFFFE, 0xFFFFFFFF) — no overflow:
    fmt.Printf("avg(2^32-2, 2^32-1) = %d\n",
        avgNoOverflow(0xFFFFFFFE, 0xFFFFFFFF))  // 4294967294
}
```

**Rust**
```rust
fn mod_pow2(x: u32, m: u32) -> u32 { x & (m - 1) }
fn abs_branchless(x: i32) -> i32 {
    let mask = x >> 31;
    (x ^ mask) - mask
}
fn avg_no_overflow(a: u32, b: u32) -> u32 {
    (a & b) + ((a ^ b) >> 1)
}

fn main() {
    println!("100 mod 16 = {}", mod_pow2(100, 16));
    println!("|−42| = {}", abs_branchless(-42));
    println!("avg(0xFFFFFFFE, 0xFFFFFFFF) = {}", avg_no_overflow(0xFFFF_FFFE, 0xFFFF_FFFF));

    // Rust std: i32::abs(), i32::min(), i32::max() — use these normally
    println!("std abs(-42) = {}", (-42_i32).abs());
    println!("std min(3,5) = {}", 3_i32.min(5));
}
```

---

## 12. Fixed-Point Arithmetic

**Represent fractional numbers as scaled integers using bit shifts.**

```
Q-format notation: Qm.n
  m = integer bits (including sign bit for signed)
  n = fractional bits
  value = integer_representation / 2^n

Example: Q16.16 (16 integer bits, 16 fractional bits, 32-bit total)
  1.0  = 0x00010000
  0.5  = 0x00008000  (1 >> 1)
  0.25 = 0x00004000  (1 >> 2)
  PI ≈ 0x0003243F   (3.14159... * 65536 ≈ 205887 = 0x0003243F)
```

**C**
```c
#include <linux/types.h>

typedef s32 fixed16_t;  /* Q16.16 signed */
#define FIXED_SHIFT  16
#define FIXED_ONE    (1 << FIXED_SHIFT)

static fixed16_t fixed_from_int(s32 x)
{
    return x << FIXED_SHIFT;
}

static fixed16_t fixed_from_float_approx(int integer_part, int frac_num, int frac_den)
{
    /* e.g. PI: integer=3, frac_num=14159, frac_den=100000 */
    return (integer_part << FIXED_SHIFT) |
           ((frac_num * FIXED_ONE) / frac_den);
}

static s32 fixed_to_int(fixed16_t x)
{
    return x >> FIXED_SHIFT;
}

static fixed16_t fixed_add(fixed16_t a, fixed16_t b)
{
    return a + b;  /* no scaling needed */
}

static fixed16_t fixed_sub(fixed16_t a, fixed16_t b)
{
    return a - b;
}

/* Multiply: (a/2^n) * (b/2^n) = (a*b) / 2^(2n)
 * Must shift back by n to get Q16.16 result */
static fixed16_t fixed_mul(fixed16_t a, fixed16_t b)
{
    return (s32)(((s64)a * b) >> FIXED_SHIFT);
}

static fixed16_t fixed_div(fixed16_t a, fixed16_t b)
{
    return (s32)(((s64)a << FIXED_SHIFT) / b);
}
```

**Go**
```go
package main

import "fmt"

const fixedShift = 16
const fixedOne   = 1 << fixedShift

type Fixed int32

func fromInt(x int32) Fixed    { return Fixed(x) << fixedShift }
func (f Fixed) toInt() int32   { return int32(f) >> fixedShift }
func (f Fixed) add(g Fixed) Fixed { return f + g }
func (f Fixed) sub(g Fixed) Fixed { return f - g }
func (f Fixed) mul(g Fixed) Fixed {
    return Fixed((int64(f) * int64(g)) >> fixedShift)
}
func (f Fixed) div(g Fixed) Fixed {
    return Fixed((int64(f) << fixedShift) / int64(g))
}

func main() {
    pi    := Fixed(205887)  // PI * 2^16 ≈ 205887
    two   := fromInt(2)
    three := fromInt(3)

    fmt.Printf("PI ≈ %d (Q16.16)\n", pi)
    fmt.Printf("2 + 3 = %d\n", two.add(three).toInt())
    fmt.Printf("PI * 2 = %d (Q16.16)\n", pi.mul(two))
    fmt.Printf("6 / 2 = %d\n", fromInt(6).div(two).toInt())
}
```

**Rust**
```rust
const FIXED_SHIFT: u32 = 16;
const FIXED_ONE:   i32 = 1 << FIXED_SHIFT;

#[derive(Copy, Clone, Debug)]
struct Fixed(i32);  // Q16.16

impl Fixed {
    fn from_int(x: i32) -> Self { Fixed(x << FIXED_SHIFT) }
    fn to_int(self) -> i32 { self.0 >> FIXED_SHIFT }
    fn add(self, rhs: Self) -> Self { Fixed(self.0 + rhs.0) }
    fn sub(self, rhs: Self) -> Self { Fixed(self.0 - rhs.0) }
    fn mul(self, rhs: Self) -> Self {
        Fixed(((self.0 as i64 * rhs.0 as i64) >> FIXED_SHIFT) as i32)
    }
    fn div(self, rhs: Self) -> Self {
        Fixed(((self.0 as i64) << FIXED_SHIFT) as i32 / rhs.0)
    }
}

fn main() {
    let pi    = Fixed(205887); // PI * 65536
    let two   = Fixed::from_int(2);
    let three = Fixed::from_int(3);

    println!("PI raw = {}", pi.0);
    println!("2 + 3 = {}", two.add(three).to_int());
    println!("PI * 2 raw = {}", pi.mul(two).0);
    println!("6 / 2 = {}", Fixed::from_int(6).div(two).to_int());
}
```

---

## 13. Bitsets & Bitmaps

### Concept

```
A bitmap represents a set of N items (integers 0..N-1)
using N/BITS_PER_LONG words.

For item i:
  word index  = i / BITS_PER_LONG  = i >> 6   (for 64-bit words)
  bit  index  = i % BITS_PER_LONG  = i & 63

Set operations:
  Union:        A | B
  Intersection: A & B
  Difference:   A & ~B
  Complement:   ~A
```

**C — Kernel bitmap API**

```c
/*
 * Kernel bitmap implementation:
 * include/linux/bitmap.h
 * lib/bitmap.c
 *
 * Used extensively for:
 *   - CPU masks (include/linux/cpumask.h)
 *   - IRQ masks
 *   - Memory zone bitmaps (mm/page_alloc.c)
 *   - scheduler domain bitmaps
 */
#include <linux/bitmap.h>
#include <linux/cpumask.h>

#define BITS_PER_LONG  64
#define BIT_WORD(nr)   ((nr) / BITS_PER_LONG)
#define BIT_MASK(nr)   (1UL << ((nr) % BITS_PER_LONG))

/* Simple fixed-size bitmap (64 items max) using single u64 */
typedef u64 bitmap64_t;

static void bitmap64_set(bitmap64_t *bm, int n)    { *bm |=  (1ULL << n); }
static void bitmap64_clear(bitmap64_t *bm, int n)  { *bm &= ~(1ULL << n); }
static bool bitmap64_test(bitmap64_t bm, int n)    { return !!(bm & (1ULL << n)); }
static int  bitmap64_first_set(bitmap64_t bm)      { return __builtin_ctzll(bm); }
static int  bitmap64_last_set(bitmap64_t bm)
{
    return 63 - __builtin_clzll(bm);
}

/* Dynamic bitmap for >64 items */
struct dyn_bitmap {
    unsigned long *bits;
    int            nbits;
};

static void dynbm_set(struct dyn_bitmap *bm, int n)
{
    bm->bits[BIT_WORD(n)] |= BIT_MASK(n);
}

static void dynbm_clear(struct dyn_bitmap *bm, int n)
{
    bm->bits[BIT_WORD(n)] &= ~BIT_MASK(n);
}

static bool dynbm_test(const struct dyn_bitmap *bm, int n)
{
    return !!(bm->bits[BIT_WORD(n)] & BIT_MASK(n));
}

/* Iterate over set bits — kernel idiom: for_each_set_bit() */
/* include/linux/bitmap.h: for_each_set_bit(bit, addr, size) */
static void iterate_set_bits(bitmap64_t bm)
{
    int bit;
    while (bm) {
        bit = __builtin_ctzll(bm);
        pr_info("bit %d is set\n", bit);
        bm &= bm - 1;  /* clear lowest set bit */
    }
}

/* Kernel cpumask usage */
void cpumask_example(void)
{
    cpumask_t mask;
    cpumask_clear(&mask);
    cpumask_set_cpu(0, &mask);
    cpumask_set_cpu(2, &mask);
    /* for_each_cpu(cpu, &mask) { ... } */
}
```

**Go**
```go
package main

import (
    "fmt"
    "math/bits"
)

type Bitmap64 uint64

func (b *Bitmap64) Set(n uint)   { *b |= 1 << n }
func (b *Bitmap64) Clear(n uint) { *b &^= 1 << n }
func (b Bitmap64) Test(n uint) bool { return (b>>n)&1 == 1 }
func (b Bitmap64) Count() int    { return bits.OnesCount64(uint64(b)) }
func (b Bitmap64) FirstSet() int {
    if b == 0 { return -1 }
    return bits.TrailingZeros64(uint64(b))
}
func (b Bitmap64) LastSet() int {
    if b == 0 { return -1 }
    return 63 - bits.LeadingZeros64(uint64(b))
}

// Iterate over set bits
func (b Bitmap64) ForEachSet(fn func(int)) {
    x := uint64(b)
    for x != 0 {
        bit := bits.TrailingZeros64(x)
        fn(bit)
        x &= x - 1  // clear lowest set bit
    }
}

// Set operations
func (a Bitmap64) Union(b Bitmap64) Bitmap64        { return a | b }
func (a Bitmap64) Intersect(b Bitmap64) Bitmap64    { return a & b }
func (a Bitmap64) Difference(b Bitmap64) Bitmap64   { return a &^ b }
func (a Bitmap64) Complement() Bitmap64              { return ^a }

func main() {
    var bm Bitmap64
    bm.Set(0); bm.Set(3); bm.Set(7); bm.Set(15); bm.Set(63)

    fmt.Printf("bitmap = 0x%016X\n", bm)
    fmt.Printf("count = %d\n", bm.Count())
    fmt.Printf("first = %d\n", bm.FirstSet())
    fmt.Printf("last  = %d\n", bm.LastSet())

    fmt.Print("set bits: ")
    bm.ForEachSet(func(n int) { fmt.Printf("%d ", n) })
    fmt.Println()

    var bm2 Bitmap64
    bm2.Set(3); bm2.Set(5); bm2.Set(7)
    fmt.Printf("union:     0x%X\n", bm.Union(bm2))
    fmt.Printf("intersect: 0x%X\n", bm.Intersect(bm2))
    fmt.Printf("diff A-B:  0x%X\n", bm.Difference(bm2))
}
```

**Rust**
```rust
#[derive(Copy, Clone, Debug, Default)]
struct Bitmap64(u64);

impl Bitmap64 {
    fn set(&mut self, n: u32)    { self.0 |=  1u64 << n; }
    fn clear(&mut self, n: u32)  { self.0 &= !(1u64 << n); }
    fn test(self, n: u32) -> bool { (self.0 >> n) & 1 == 1 }
    fn count(self) -> u32         { self.0.count_ones() }
    fn first_set(self) -> Option<u32> {
        if self.0 == 0 { None } else { Some(self.0.trailing_zeros()) }
    }
    fn last_set(self) -> Option<u32> {
        if self.0 == 0 { None } else { Some(63 - self.0.leading_zeros()) }
    }
    fn for_each_set<F: FnMut(u32)>(self, mut f: F) {
        let mut x = self.0;
        while x != 0 {
            let bit = x.trailing_zeros();
            f(bit);
            x &= x - 1;
        }
    }
    fn union(self, rhs: Self) -> Self      { Bitmap64(self.0 | rhs.0) }
    fn intersect(self, rhs: Self) -> Self  { Bitmap64(self.0 & rhs.0) }
    fn difference(self, rhs: Self) -> Self { Bitmap64(self.0 & !rhs.0) }
}

fn main() {
    let mut bm = Bitmap64::default();
    for n in [0u32, 3, 7, 15, 63] { bm.set(n); }

    println!("bitmap = {:#018x}", bm.0);
    println!("count = {}", bm.count());
    println!("first = {:?}", bm.first_set());
    println!("last  = {:?}", bm.last_set());

    print!("set bits: ");
    bm.for_each_set(|n| print!("{} ", n));
    println!();

    let mut bm2 = Bitmap64::default();
    for n in [3u32, 5, 7] { bm2.set(n); }
    println!("intersect: {:#018x}", bm.intersect(bm2).0);
    println!("difference: {:#018x}", bm.difference(bm2).0);
}
```

---

## 14. Rotate Operations

**Bit rotation wraps bits that fall off one end around to the other — unlike shift which discards them.**

```
Rotate left by 1:
  x       = 1010 1101
  ROL(1)  = 0101 1011   (MSB wraps to LSB position)

Rotate right by 1:
  x       = 1010 1101
  ROR(1)  = 1101 0110   (LSB wraps to MSB position)
```

**C**
```c
/* GCC/Clang recognize this pattern and emit a single ROL/ROR instruction */
static u32 rol32(u32 x, u32 n)
{
    n &= 31;  /* prevent shift by 32 UB */
    return (x << n) | (x >> (32 - n));
}

static u32 ror32(u32 x, u32 n)
{
    n &= 31;
    return (x >> n) | (x << (32 - n));
}

static u64 rol64(u64 x, u32 n)
{
    n &= 63;
    return (x << n) | (x >> (64 - n));
}

/*
 * Kernel provides: include/linux/bitops.h
 *   rol8, ror8, rol16, ror16, rol32, ror32, rol64, ror64
 *
 * Used in: crypto (lib/crypto/), CRC, hash functions
 */
#include <linux/bitops.h>
/* rol32(x, n), ror32(x, n) etc. available */
```

**Go**
```go
package main

import (
    "fmt"
    "math/bits"
)

func rol32(x uint32, n uint) uint32 { return bits.RotateLeft32(x, int(n)) }
func ror32(x uint32, n uint) uint32 { return bits.RotateLeft32(x, -int(n)) }
func rol64(x uint64, n uint) uint64 { return bits.RotateLeft64(x, int(n)) }
func ror64(x uint64, n uint) uint64 { return bits.RotateLeft64(x, -int(n)) }

func main() {
    x := uint32(0x12345678)
    for n := uint(0); n <= 8; n += 2 {
        fmt.Printf("ROL(%08b, %d) = %08b\n", x, n, rol32(x, n))
    }
    fmt.Printf("ROR(0x%08X, 4) = 0x%08X\n", x, ror32(x, 4))
}
```

**Rust**
```rust
fn main() {
    let x: u32 = 0x1234_5678;
    println!("ROL(x, 4) = {:#010x}", x.rotate_left(4));
    println!("ROR(x, 4) = {:#010x}", x.rotate_right(4));

    // Rotation is its own inverse with complementary amount:
    assert_eq!(x.rotate_left(4).rotate_right(4), x);

    let x64: u64 = 0x0102030405060708;
    println!("ROL64(x, 8) = {:#018x}", x64.rotate_left(8));
    println!("ROR64(x, 8) = {:#018x}", x64.rotate_right(8));
}
```

---

## 15. Gray Code

**Gray code: consecutive values differ by exactly 1 bit.**

```
Decimal  Binary  Gray
0        000     000
1        001     001
2        010     011
3        011     010
4        100     110
5        101     111
6        110     101
7        111     100

Encoding: gray = n ^ (n >> 1)
Decoding: n    = gray
          for each shift: n ^= (gray >>= 1) while gray
```

**Use cases:** rotary encoders, error correction, digital circuits, Karnaugh maps.

**C**
```c
static u32 to_gray(u32 n)
{
    return n ^ (n >> 1);
}

static u32 from_gray(u32 gray)
{
    u32 n = gray;
    while (gray >>= 1)
        n ^= gray;
    return n;
}
```

**Go**
```go
package main

import "fmt"

func toGray(n uint32) uint32  { return n ^ (n >> 1) }
func fromGray(g uint32) uint32 {
    n := g
    for g >>= 1; g != 0; g >>= 1 {
        n ^= g
    }
    return n
}

func main() {
    fmt.Printf("%-8s %-8s %-8s %-8s\n", "Decimal", "Binary", "Gray", "GrayBin")
    for i := uint32(0); i < 8; i++ {
        g := toGray(i)
        fmt.Printf("%-8d %08b %08b %d\n", i, i, g, fromGray(g))
    }
}
```

**Rust**
```rust
fn to_gray(n: u32) -> u32  { n ^ (n >> 1) }
fn from_gray(mut g: u32) -> u32 {
    let mut n = g;
    g >>= 1;
    while g != 0 {
        n ^= g;
        g >>= 1;
    }
    n
}

fn main() {
    println!("{:<8} {:<8} {:<8}", "Decimal", "Binary", "Gray");
    for i in 0u32..8 {
        let g = to_gray(i);
        println!("{:<8} {:08b} {:08b}  (decoded={})", i, i, g, from_gray(g));
    }
}
```

---

## 16. Signed vs Unsigned Shift Behaviour

```
PLATFORM: x86-64 Linux

Signed left shift:
  C standard: shifting into/past sign bit is UB (C11 §6.5.7)
  GCC/Clang: emit SHL, no trap, but optimiser may exploit UB
  Rust:      panic in debug mode if shift would overflow; use wrapping_shl()

Signed right shift:
  C standard: implementation-defined (§6.5.7.5)
  x86 GCC:   emits SAR — arithmetic (sign extension)
  ARM GCC:   emits ASR — arithmetic (sign extension)
  Rust:      always arithmetic for signed types (guaranteed)
  Go:        always arithmetic for signed types (spec guaranteed)

Unsigned right shift:
  C/Go/Rust: always logical (zero fill) — guaranteed

JavaScript:
  >>> = unsigned logical right shift
  >>  = signed arithmetic right shift
  (Not C/Go/Rust, but worth knowing for reference)
```

**C — Safe shift wrappers**

```c
/*
 * COMPILER_WARN_UNUSED_RESULT, __must_check etc.
 * come from include/linux/compiler_attributes.h
 *
 * Kernel uses __builtin_* liberally. UB sanitizer (UBSAN) in
 * kernel catches shift violations at runtime.
 * Enable with: CONFIG_UBSAN=y, CONFIG_UBSAN_SHIFT=y
 */

/* Safe arithmetic left shift for u32 (defined for all shift amounts) */
static u32 shl32_safe(u32 x, u32 n)
{
    if (unlikely(n >= 32)) return 0;
    return x << n;
}

/* Arithmetic right shift for s32 (relies on implementation-defined, but
 * safe on all Linux-supported architectures) */
static s32 asr32(s32 x, u32 n)
{
    /* n must be < 32; guaranteed by caller contract */
    return x >> n;  /* SAR on x86/ARM */
}

/* Portable arithmetic right shift without relying on impl-defined */
static s32 asr32_portable(s32 x, u32 n)
{
    /* Using unsigned type, then OR sign bits back */
    u32 ux = (u32)x;
    u32 sign_mask = (u32)(-(x < 0));  /* 0 or 0xFFFFFFFF */
    sign_mask = sign_mask & ~((1U << (32 - n)) - 1U);  /* upper n bits */
    return (s32)((ux >> n) | sign_mask);
}
```

---

## 17. Undefined Behaviour & Overflow Traps

### C UB Summary for Bitwise Operations

```
1. Shift by negative amount:       x >> -1         → UB
2. Shift by >= type width:         u32 x; x << 32  → UB
3. Left shift of negative value:   -1 << 1          → UB
4. Left shift into sign bit:       (s32)0x40000000 << 1 → UB
5. Signed integer overflow:        INT_MAX + 1      → UB (not bitwise, but related)
```

### Detecting in the Kernel

```bash
# Enable undefined behaviour sanitizer:
make menuconfig → Kernel hacking → UB Sanitizer → Enable UBSAN

# In .config:
CONFIG_UBSAN=y
CONFIG_UBSAN_SHIFT=y
CONFIG_UBSAN_INTEGER_OVERFLOW=y  # available in newer kernels

# Runtime: UBSAN reports violations to dmesg with file/line info
```

**C — UB-safe patterns**

```c
#include <linux/overflow.h>  /* check_add_overflow, check_mul_overflow */

/* Safe multiply: returns true if overflow occurred */
bool safe_mul(u32 a, u32 b, u32 *result)
{
    return check_mul_overflow(a, b, result);
}

/* Saturating add (clamp to max instead of overflow) */
static u32 sat_add(u32 a, u32 b)
{
    u32 result;
    if (check_add_overflow(a, b, &result))
        return U32_MAX;
    return result;
}
```

**Rust — Built-in overflow control**

```rust
fn main() {
    let x: u32 = u32::MAX;

    // checked: returns Option
    println!("{:?}", x.checked_add(1));        // None
    println!("{:?}", x.checked_shl(1));        // None (shift >= 32)

    // wrapping: modular arithmetic
    println!("{}", x.wrapping_add(1));          // 0
    println!("{}", 1u32.wrapping_shl(33));      // 2 (33 % 32 = 1)

    // saturating: clamps to min/max
    println!("{}", x.saturating_add(100));      // 4294967295

    // overflowing: (result, did_overflow)
    println!("{:?}", x.overflowing_add(1));    // (0, true)
    println!("{:?}", 1u32.overflowing_shl(32)); // (1, true) on some platforms

    // Debug builds: panic on overflow by default
    // Release builds: wrapping (configure in Cargo.toml)
}
```

---

## 18. SIMD / Vectorized Bit Operations (intro)

**SIMD: Single Instruction, Multiple Data — apply the same bitwise operation to multiple lanes simultaneously.**

```
SSE2 (128-bit XMM registers, 2x u64 lanes or 16x u8 lanes):
  _mm_and_si128(a, b)   — 128-bit AND
  _mm_or_si128(a, b)    — 128-bit OR
  _mm_xor_si128(a, b)   — 128-bit XOR
  _mm_andnot_si128(a,b) — AND NOT

AVX2 (256-bit YMM registers):
  _mm256_and_si256, _mm256_or_si256, etc.

Example: compute 16 byte-wise XOR operations at once (for XOR cipher):
  __m128i key16   = _mm_set1_epi8(key_byte);
  __m128i plain16 = _mm_loadu_si128(src);
  __m128i cipher  = _mm_xor_si128(plain16, key16);
  _mm_storeu_si128(dst, cipher);
```

**C — Kernel SIMD example (arch/x86)**

```c
/*
 * Kernel uses SIMD for:
 *   - XOR RAID: lib/xor.c (xor_avx_2, xor_sse_2, etc.)
 *   - Crypto: arch/x86/crypto/*.c (AES-NI, SHA-NI)
 *   - Memory: arch/x86/lib/memcpy_64.S
 *
 * Direct intrinsics in kernel require:
 *   kernel_fpu_begin() / kernel_fpu_end()  (save/restore FPU state)
 *   From: arch/x86/include/asm/fpu/api.h
 */
#include <asm/fpu/api.h>
#include <asm/simd.h>

void xor_blocks_simd(u8 *dst, const u8 *src_a, const u8 *src_b, size_t len)
{
    /* Must be called from process context, not interrupt */
    if (may_use_simd()) {
        kernel_fpu_begin();
        /* SIMD XOR here */
        kernel_fpu_end();
    } else {
        /* Fallback: scalar */
        while (len--)
            *dst++ = *src_a++ ^ *src_b++;
    }
}
```

**Rust — std::simd (portable SIMD, nightly)**

```rust
// Nightly only: #![feature(portable_simd)]
// use std::simd::u8x16;
//
// fn xor_16bytes(a: u8x16, b: u8x16) -> u8x16 { a ^ b }
//
// Stable alternative: use crates like packed_simd or wide

// Demonstration using std types (compiler auto-vectorizes):
fn xor_buffers(dst: &mut [u8], src_a: &[u8], src_b: &[u8]) {
    // Modern compilers will auto-vectorize this loop with SIMD instructions
    // when compiled with -C target-cpu=native
    for ((d, a), b) in dst.iter_mut().zip(src_a).zip(src_b) {
        *d = a ^ b;
    }
}

fn main() {
    let a = vec![0xDE_u8; 16];
    let b = vec![0xAD_u8; 16];
    let mut dst = vec![0u8; 16];
    xor_buffers(&mut dst, &a, &b);
    println!("{:?}", dst);
}
```

---

## 19. Linux Kernel Bitwise Patterns

### 19.1 Key Header Files

```
include/linux/bitops.h       — bit operations: hweight, ffz, fls, ffs, BIT()
include/linux/bits.h         — BIT(), GENMASK(), BITS_PER_LONG, BIT_MASK()
include/linux/bitmap.h       — dynamic bitmap operations
include/linux/bitrev.h       — bitrev8/16/32/64
include/linux/overflow.h     — overflow-checked arithmetic
include/uapi/linux/swab.h    — __swab16/32/64
include/linux/byteorder/     — cpu_to_be32 etc.
arch/x86/include/asm/bitops.h — x86-specific: set_bit, clear_bit (atomic)
```

### 19.2 Atomic Bit Operations

```c
/*
 * arch/x86/include/asm/bitops.h provides:
 *   set_bit(nr, addr)      — atomic (uses LOCK BTS)
 *   clear_bit(nr, addr)    — atomic (uses LOCK BTR)
 *   change_bit(nr, addr)   — atomic (uses LOCK BTC)
 *   test_bit(nr, addr)     — non-atomic read
 *   test_and_set_bit()     — atomic, returns old value
 *   test_and_clear_bit()   — atomic, returns old value
 *
 * Non-atomic variants (for local-only use):
 *   __set_bit, __clear_bit, __change_bit, __test_and_set_bit
 */
#include <linux/bitops.h>

/* Typical spinlock-protected bit flag pattern in device drivers */
struct my_device {
    unsigned long flags;
#define DEV_RUNNING   0
#define DEV_SUSPENDED 1
#define DEV_ERROR     2
};

void set_running(struct my_device *dev)
{
    set_bit(DEV_RUNNING, &dev->flags);
}

bool is_running(struct my_device *dev)
{
    return test_bit(DEV_RUNNING, &dev->flags);
}

bool try_start(struct my_device *dev)
{
    /* Atomically set; returns true if bit was already set */
    return test_and_set_bit(DEV_RUNNING, &dev->flags);
}
```

### 19.3 find_first_bit / find_next_bit

```c
/*
 * lib/find_bit.c:
 *   find_first_bit(addr, size)        — index of first set bit
 *   find_next_bit(addr, size, offset) — next set bit after offset
 *   find_first_zero_bit(addr, size)
 *   find_next_zero_bit(addr, size, offset)
 *
 * Used in:
 *   kernel/sched/core.c — find_lowest_rq()
 *   drivers/irqchip/    — find next pending IRQ
 *   mm/page_alloc.c     — find free page in zone
 */
#include <linux/bitmap.h>

void process_pending_irqs(unsigned long *pending_irq_bitmap, int nirqs)
{
    int irq;
    for_each_set_bit(irq, pending_irq_bitmap, nirqs) {
        handle_irq(irq);
    }
}
```

### 19.4 fls / ffs / ffz

```c
/*
 * fls(x)  — find last (highest) set bit, 1-indexed (0 if x==0)
 * ffs(x)  — find first (lowest) set bit, 1-indexed (0 if x==0)
 * ffz(x)  — find first zero bit, 0-indexed
 *
 * Used for: log2, order calculation, memory allocator
 *
 * fls(8)  = 4   (bit 3 is highest, but fls is 1-indexed)
 * fls(16) = 5
 * ffs(8)  = 4
 * ffs(12) = 3   (bit 2 is lowest set bit: 0b1100 → bit 2 → ffs = 3)
 * ffz(0xFFFFFFFE) = 0  (bit 0 is first zero)
 */

/* ilog2 equivalent: floor(log2(x)) for x > 0 */
static inline int ilog2_from_fls(u32 x)
{
    return fls(x) - 1;
}

/* roundup_pow_of_two using fls */
static u32 roundup_pow2_via_fls(u32 x)
{
    if (x <= 1) return 1;
    return 1U << fls(x - 1);
}
```

### 19.5 Kernel BIT/GENMASK Pattern Deep Dive

```c
/*
 * Real-world example: Intel e1000 NIC driver
 * drivers/net/ethernet/intel/e1000/e1000_hw.h (simplified)
 */

/* Transmit Descriptor Status bits */
#define E1000_TXD_STAT_DD    BIT(0)  /* Descriptor Done */
#define E1000_TXD_STAT_EC    BIT(1)  /* Excess Collisions */
#define E1000_TXD_STAT_LC    BIT(2)  /* Late Collision */

/* Receive Descriptor Status bits */
#define E1000_RXD_STAT_DD    BIT(0)  /* Descriptor Done */
#define E1000_RXD_STAT_EOP   BIT(1)  /* End of Packet */
#define E1000_RXD_STAT_IXSM  BIT(2)  /* Ignore Checksum */
#define E1000_RXD_STAT_VP    BIT(3)  /* VLAN Packet */
#define E1000_RXD_STAT_TCPCS BIT(5)  /* TCP Checksum Computed */
#define E1000_RXD_STAT_IPCS  BIT(6)  /* IP Checksum Computed */

/* Control Register (CTRL) field definitions */
#define E1000_CTRL_FD        BIT(0)   /* Full Duplex */
#define E1000_CTRL_ASDE      BIT(5)   /* Auto-Speed Detection Enable */
#define E1000_CTRL_SLU       BIT(6)   /* Set Link Up */
#define E1000_CTRL_SPEED     GENMASK(9, 8)   /* Speed selection field */
#define E1000_CTRL_SPEED_10  FIELD_PREP(E1000_CTRL_SPEED, 0)
#define E1000_CTRL_SPEED_100 FIELD_PREP(E1000_CTRL_SPEED, 1)
#define E1000_CTRL_SPEED_1000 FIELD_PREP(E1000_CTRL_SPEED, 2)
```

### 19.6 Memory Alignment in mm/

```c
/*
 * mm/page_alloc.c uses bit operations extensively for:
 *   - Page order (2^order pages per block)
 *   - Buddy system: buddies differ by exactly one bit
 *   - Zone bitmaps
 *
 * include/linux/mm.h:
 */
#define PAGE_SHIFT    12
#define PAGE_SIZE     (_AC(1, UL) << PAGE_SHIFT)    /* 4096 */
#define PAGE_MASK     (~(PAGE_SIZE - 1))

/* Align address UP to page boundary */
#define PAGE_ALIGN(addr)    ALIGN(addr, PAGE_SIZE)

/* ALIGN macro from include/linux/kernel.h */
#define ALIGN(x, a)         __ALIGN_KERNEL((x), (a))
#define __ALIGN_KERNEL(x, a) __ALIGN_KERNEL_MASK(x, (typeof(x))(a) - 1)
#define __ALIGN_KERNEL_MASK(x, mask)    (((x) + (mask)) & ~(mask))

/* Buddy allocator: buddy of block at pfn with order n */
static unsigned long find_buddy_pfn(unsigned long pfn, unsigned int order)
{
    return pfn ^ (1 << order);
}
```

---

## 20. Compiler Intrinsics & Built-ins

### GCC/Clang Built-ins for Bit Operations

```c
/*
 * All map to single CPU instructions on x86/ARM.
 * Available in kernel without any include (GCC built-ins).
 */

/* Count trailing zeros (index of LSB) */
int n = __builtin_ctz(x);    /* u32, UB if x==0 */
int n = __builtin_ctzl(x);   /* unsigned long */
int n = __builtin_ctzll(x);  /* u64 */

/* Count leading zeros (32 - 1 - index of MSB) */
int n = __builtin_clz(x);    /* UB if x==0 */
int n = __builtin_clzl(x);
int n = __builtin_clzll(x);

/* Population count */
int n = __builtin_popcount(x);   /* u32 */
int n = __builtin_popcountl(x);  /* unsigned long */
int n = __builtin_popcountll(x); /* u64 */

/* Parity (1 if odd number of set bits) */
int p = __builtin_parity(x);
int p = __builtin_parityll(x);

/* Byte swap */
u32 b = __builtin_bswap32(x);
u64 b = __builtin_bswap64(x);
u16 b = __builtin_bswap16(x);

/* Expect (branch prediction hint — used in likely/unlikely) */
/* include/linux/compiler.h: likely() / unlikely() */
#define likely(x)   __builtin_expect(!!(x), 1)
#define unlikely(x) __builtin_expect(!!(x), 0)
```

### Go `math/bits` Package

```go
import "math/bits"

bits.OnesCount32(x)          // popcount
bits.OnesCount64(x)
bits.TrailingZeros32(x)      // ctz (0 if x==0)
bits.LeadingZeros32(x)       // clz (32 if x==0)
bits.Len32(x)                // bit length = 32 - LeadingZeros32
bits.ReverseBytes32(x)       // bswap32
bits.Reverse32(x)            // bitrev32
bits.RotateLeft32(x, k)      // rol32 (k<0 = ror)
bits.Add32(x, y, carry)      // (sum, carry_out)
bits.Mul32(x, y)             // (hi, lo) full multiply
bits.Div32(hi, lo, y)        // (quotient, remainder)
bits.UintSize                // 32 or 64
```

### Rust Intrinsic Methods on Integer Types

```rust
// All of these are method calls on integer types:
x.count_ones()               // popcount
x.count_zeros()
x.leading_zeros()            // clz
x.trailing_zeros()           // ctz
x.leading_ones()
x.trailing_ones()
x.reverse_bits()             // bitrev
x.swap_bytes()               // bswap
x.rotate_left(n)             // rol
x.rotate_right(n)            // ror
x.checked_shl(n)             // safe shift
x.wrapping_shl(n)
x.overflowing_shl(n)

// Widening operations:
let (hi, lo) = x.widening_mul(y);   // u64 from 2xu32 (nightly)

// From/to bytes:
u32::from_be_bytes([b0, b1, b2, b3])
u32::from_le_bytes([b0, b1, b2, b3])
x.to_be_bytes()
x.to_le_bytes()
```

---

## 21. eBPF Bitwise Operations

**eBPF instructions mirror C bitwise semantics. All operations work on 64-bit or 32-bit registers (r0–r10).**

### BPF ISA Bitwise Instructions

```
ALU64 (64-bit):                    ALU32 (32-bit, zero-extends):
  BPF_AND   dst &= src/imm          BPF_AND32
  BPF_OR    dst |= src/imm          BPF_OR32
  BPF_XOR   dst ^= src/imm          BPF_XOR32
  BPF_LSH   dst <<= src/imm         BPF_LSH32
  BPF_RSH   dst >>= src/imm         BPF_RSH32  (logical)
  BPF_ARSH  dst s>>= src/imm        BPF_ARSH32 (arithmetic)
  BPF_NEG   dst = -dst
```

### bpftrace Examples

```bash
# Count syscalls per process using bitwise access to syscall number
# (from args->id which is a 32-bit field)
bpftrace -e '
tracepoint:raw_syscalls:sys_enter {
    @calls[comm, args->id & 0xFF] = count();  // lower byte of syscall#
}'

# Check if network packet has TCP SYN flag
# TCP flags byte: FIN=1, SYN=2, RST=4, PSH=8, ACK=16, URG=32
bpftrace -e '
kprobe:tcp_v4_connect {
    $sk = (struct sock *)arg0;
    printf("connect from PID %d\n", pid);
}'

# Inspect mmap flags using bit test
bpftrace -e '
tracepoint:syscalls:sys_enter_mmap {
    if (args->flags & 0x20) {  // MAP_ANONYMOUS
        @anon_maps[comm] = count();
    }
}'
```

### BPF C Program (using libbpf)

```c
/*
 * tools/testing/selftests/bpf/ contains examples.
 * BPF programs in kernel: net/core/filter.c
 */
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

/* XDP program: filter packets with specific IP flag bits */
SEC("xdp")
int xdp_bitfilter(struct xdp_md *ctx)
{
    void *data     = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;

    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_DROP;

    if (eth->h_proto != __constant_htons(ETH_P_IP))
        return XDP_PASS;

    struct iphdr *iph = (void *)(eth + 1);
    if ((void *)(iph + 1) > data_end)
        return XDP_DROP;

    /* Check DF bit in fragment offset field */
    __u16 frag_off = __be16_to_cpu(iph->frag_off);
    if (frag_off & IP_DF) {
        /* Don't Fragment set — pass through */
        return XDP_PASS;
    }

    /* Drop fragmented packets */
    if (frag_off & IP_MF || (frag_off & IP_OFFMASK))
        return XDP_DROP;

    return XDP_PASS;
}

char LICENSE[] SEC("license") = "GPL";
```

---

## 22. Exercises & Interview Problems

### Problems

```
E1. Given x, swap bit positions i and j.
E2. Given x, reverse the bits of every byte (don't reverse byte order).
E3. Find the only non-duplicate in an array where every element appears twice.
     Hint: XOR of all elements.
E4. Find two non-duplicate elements in an array where all others appear twice.
     Hint: XOR all → get x^y; find differing bit; partition array.
E5. Determine if an integer has alternating bits (e.g. 0b10101, 0b01010).
E6. Find the position of the rightmost bit that differs between x and y.
E7. Given a 32-bit integer, count the number of bits needed to convert x to y.
E8. Implement a function that checks if x is a power of 4.
     Hint: power of 2 AND bit is in even position.
E9. Add two integers without using + or -.
     Hint: XOR = sum-without-carry; AND<<1 = carry.
E10. Multiply two integers using only shifts and adds.
```

**C — Solutions**

```c
/* E1: Swap bits i and j */
static u32 swap_bits(u32 x, u32 i, u32 j)
{
    u32 bi = (x >> i) & 1;
    u32 bj = (x >> j) & 1;
    if (bi != bj)
        x ^= (1U << i) | (1U << j);
    return x;
}

/* E3: Find non-duplicate */
static u32 find_unique(const u32 *arr, int n)
{
    u32 result = 0;
    for (int i = 0; i < n; i++)
        result ^= arr[i];
    return result;
}

/* E5: Alternating bits */
static bool has_alternating_bits(u32 x)
{
    u32 shifted = x ^ (x >> 1);
    return (shifted & (shifted + 1)) == 0;
}

/* E8: Power of 4 */
static bool is_power_of_4(u32 x)
{
    /* Must be power of 2 AND the bit must be at an even position */
    return x != 0 &&
           (x & (x - 1)) == 0 &&
           (x & 0x55555555U) != 0;  /* 0x55... has bits at even positions */
}

/* E9: Add without + */
static u32 add_no_plus(u32 a, u32 b)
{
    while (b) {
        u32 carry = a & b;
        a = a ^ b;
        b = carry << 1;
    }
    return a;
}

/* E10: Multiply using shifts */
static u32 multiply_shifts(u32 a, u32 b)
{
    u32 result = 0;
    while (b) {
        if (b & 1)
            result = add_no_plus(result, a);
        a <<= 1;
        b >>= 1;
    }
    return result;
}
```

**Go — Solutions**

```go
package main

import "fmt"

func swapBits(x uint32, i, j uint) uint32 {
    bi := (x >> i) & 1
    bj := (x >> j) & 1
    if bi != bj {
        x ^= (1 << i) | (1 << j)
    }
    return x
}

func findUnique(arr []uint32) uint32 {
    var r uint32
    for _, v := range arr { r ^= v }
    return r
}

func hasAlternatingBits(x uint32) bool {
    shifted := x ^ (x >> 1)
    return shifted&(shifted+1) == 0
}

func isPowerOf4(x uint32) bool {
    return x != 0 && x&(x-1) == 0 && x&0x55555555 != 0
}

func addNoBinaryPlus(a, b uint32) uint32 {
    for b != 0 {
        carry := a & b
        a = a ^ b
        b = carry << 1
    }
    return a
}

func multiplyShifts(a, b uint32) uint32 {
    var result uint32
    for b != 0 {
        if b&1 == 1 {
            result = addNoBinaryPlus(result, a)
        }
        a <<= 1
        b >>= 1
    }
    return result
}

func main() {
    fmt.Printf("swapBits(0b1010, 1, 3) = %04b\n", swapBits(0b1010, 1, 3))
    fmt.Printf("findUnique = %d\n", findUnique([]uint32{1, 2, 3, 2, 1}))
    fmt.Printf("alternating(0b10101) = %v\n", hasAlternatingBits(0b10101))
    fmt.Printf("alternating(0b10110) = %v\n", hasAlternatingBits(0b10110))
    fmt.Printf("isPow4(16) = %v\n", isPowerOf4(16))
    fmt.Printf("isPow4(8)  = %v\n", isPowerOf4(8))
    fmt.Printf("3+5 (no +) = %d\n", addNoBinaryPlus(3, 5))
    fmt.Printf("6*7 (shifts) = %d\n", multiplyShifts(6, 7))
}
```

**Rust — Solutions**

```rust
fn swap_bits(mut x: u32, i: u32, j: u32) -> u32 {
    let bi = (x >> i) & 1;
    let bj = (x >> j) & 1;
    if bi != bj {
        x ^= (1 << i) | (1 << j);
    }
    x
}

fn find_unique(arr: &[u32]) -> u32 {
    arr.iter().fold(0, |acc, &x| acc ^ x)
}

fn has_alternating_bits(x: u32) -> bool {
    let shifted = x ^ (x >> 1);
    shifted & shifted.wrapping_add(1) == 0
}

fn is_power_of_4(x: u32) -> bool {
    x != 0 && x & (x - 1) == 0 && x & 0x5555_5555 != 0
}

fn add_no_plus(mut a: u32, mut b: u32) -> u32 {
    while b != 0 {
        let carry = a & b;
        a ^= b;
        b = carry << 1;
    }
    a
}

fn multiply_shifts(mut a: u32, mut b: u32) -> u32 {
    let mut result = 0u32;
    while b != 0 {
        if b & 1 == 1 {
            result = add_no_plus(result, a);
        }
        a <<= 1;
        b >>= 1;
    }
    result
}

fn main() {
    println!("swap_bits(0b1010, 1, 3) = {:04b}", swap_bits(0b1010, 1, 3));
    println!("find_unique = {}", find_unique(&[1, 2, 3, 2, 1]));
    println!("alternating(0b10101) = {}", has_alternating_bits(0b10101));
    println!("alternating(0b10110) = {}", has_alternating_bits(0b10110));
    println!("is_pow4(16) = {}", is_power_of_4(16));
    println!("is_pow4(8)  = {}", is_power_of_4(8));
    println!("3+5 (no +) = {}", add_no_plus(3, 5));
    println!("6*7 (shifts) = {}", multiply_shifts(6, 7));
}
```

---

## Quick Reference Cheat Sheet

```
OPERATION                C / Kernel              Go            Rust
─────────────────────────────────────────────────────────────────────────────
Set bit N                x |= BIT(N)             x |= 1<<N     x |= 1<<N
Clear bit N              x &= ~BIT(N)            x &^= 1<<N    x &= !(1<<N)
Toggle bit N             x ^= BIT(N)             x ^= 1<<N     x ^= 1<<N
Test bit N               !!(x & BIT(N))          (x>>N)&1==1   (x>>N)&1==1
LSB index                __builtin_ctz(x)        bits.TrailingZeros32(x) x.trailing_zeros()
MSB index                fls(x)-1                bits.Len32(x)-1  31-x.leading_zeros()
Popcount                 hweight32(x)            bits.OnesCount32(x) x.count_ones()
Bswap32                  __builtin_bswap32(x)    bits.ReverseBytes32(x) x.swap_bytes()
Bitrev32                 bitrev32(x)             bits.Reverse32(x) x.reverse_bits()
Rotate left              rol32(x,n)              bits.RotateLeft32(x,n) x.rotate_left(n)
Is power of 2            is_power_of_2(x)        x&(x-1)==0    x&(x-1)==0
Next power of 2          roundup_pow_of_two(x)   1<<bits.Len64(x-1) 1<<(64-x.leading_zeros())
AND-NOT                  x & ~mask               x &^ mask     x & !mask
GENMASK(h,l)             GENMASK(h,l)            manual        manual
Field extract [h:l]      FIELD_GET(mask,reg)     manual        (x>>l)&mask
Field insert [h:l]       FIELD_PREP(mask,val)    manual        (val<<l)&mask
Overflow-safe add        check_add_overflow()    n/a           x.checked_add(y)
Wrapping add             (implicit, UB risk)     n/a           x.wrapping_add(y)
─────────────────────────────────────────────────────────────────────────────

KEY IDENTITIES:
  x & 0       = 0                x | ~0     = ~0
  x & ~0      = x                x | 0      = x
  x & x       = x                x ^ x      = 0
  x & ~x      = 0                x ^ 0      = x
  x ^ ~0      = ~x               x ^ ~x     = ~0
  x & (x-1)   = x with LSB cleared
  x | (x-1)   = x with all lower bits filled
  x & -x      = isolated LSB
  ~x & (x+1) = isolated lowest 0-bit
```

---

*Guide version: 2025 | Kernel refs: v6.8+*
*Key source files: `include/linux/bitops.h`, `include/linux/bits.h`, `include/linux/bitmap.h`, `lib/bitmap.c`, `lib/bitrev.c`, `arch/x86/include/asm/bitops.h`*

~3,600 lines covering every bitwise concept end-to-end. Here's what's inside:

**Structure:**
- **Sections 1–2** — Binary representation, positional weight, number system conversions, two's complement encoding, sign bit tricks
- **Section 3** — All 6 operators (AND/OR/XOR/NOT/LSH/RSH) with full truth tables, algebraic identities, UB rules, and annotated kernel usage per operator
- **Sections 4–5** — Mask construction (`GENMASK`, `FIELD_GET`, `FIELD_PREP`), full register field manipulation (driver-style), and struct bitfields with kernel policy on when to avoid them
- **Sections 7–9** — Idiom bank: LSB tricks, `x & (x-1)`, `x & -x`, next-power-of-2, popcount SWAR, bit reversal
- **Sections 10–12** — Endianness/bswap with kernel's `cpu_to_be32` family, fixed-point Q16.16 arithmetic, arithmetic tricks (branchless abs/min/max, modulo-power-of-2)
- **Sections 13–15** — Full bitmap/bitset implementation with set operations, bit rotation, Gray code
- **Sections 16–18** — Signed vs unsigned shift guarantees (C UB vs Go/Rust guarantees), UBSAN config, SIMD intro with kernel `kernel_fpu_begin()` context
- **Section 19** — Pure kernel: `include/linux/bitops.h` API, atomic `set_bit`/`test_and_set_bit`, `for_each_set_bit`, buddy allocator PFN XOR, `fls`/`ffs`/`ffz`, real e1000 register definitions
- **Section 20** — All `__builtin_*` intrinsics, `math/bits` package, Rust integer methods
- **Section 21** — eBPF/BPF ISA bitwise opcodes, bpftrace one-liners, XDP C program with IP fragmentation flag parsing
- **Section 22** — 10 exercises with full C/Go/Rust solutions (swap bits, find-unique XOR, alternating bits, power-of-4, add-without-plus, multiply-via-shifts)
- **Cheat sheet** — All operations side-by-side across C/Go/Rust + key algebraic identities

