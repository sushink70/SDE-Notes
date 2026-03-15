# The Complete Integer Types Guide
## Why We Have u8, i32, u64... and Why One Type Is Never Enough

> *"To a man with only a hammer, every problem looks like a nail."*  
> The same applies to types — constraining your vocabulary constrains your thinking.

---

## Table of Contents

1. [The Core Question: Why Not Just One Type?](#1-the-core-question)
2. [Binary Fundamentals — What the CPU Actually Sees](#2-binary-fundamentals)
3. [Signed vs Unsigned — Two's Complement Deep Dive](#3-signed-vs-unsigned)
4. [The Width Taxonomy: 8, 16, 32, 64, 128 bits](#4-the-width-taxonomy)
5. [Platform-Dependent Types](#5-platform-dependent-types)
6. [Overflow, Underflow, and Wrapping Behavior](#6-overflow-and-underflow)
7. [Type Casting and Promotion Rules](#7-type-casting-and-promotion)
8. [Bit Manipulation Mastery](#8-bit-manipulation)
9. [Real-World Use Cases](#9-real-world-use-cases)
10. [Performance and Memory Implications](#10-performance-and-memory)
11. [Common Pitfalls and War Stories](#11-common-pitfalls)
12. [Language Implementations: Go, Rust, C](#12-language-implementations)

---

## 1. The Core Question

**"What if we just use one type that fits everything?"**

At first glance, this seems reasonable. Python essentially does this — integers grow arbitrarily. Java uses `long` (64-bit) for everything. But this breaks down the moment you care about:

| Concern | Why One Type Fails |
|---|---|
| **Memory layout** | A pixel's color channel is 0-255. Storing it as 64 bits wastes 7/8 of your RAM for no gain |
| **Hardware fidelity** | CPUs speak in 8/16/32/64-bit words. Misalignment causes penalty cycles |
| **Protocol compliance** | TCP ports are exactly 16 bits (0-65535). The spec doesn't care about your "universal" type |
| **Overflow semantics** | A cyclic counter, a hash, and a bank balance all overflow differently — intentionally |
| **Type safety as documentation** | `u8` says "this is a byte, values 0-255, and I mean it" — that's information |
| **SIMD/Vectorization** | CPUs can process 32× u8 values simultaneously in a 256-bit register |

The expert mental model: **types are constraints, and constraints are power**. A `u8` doesn't just limit — it *communicates intent, enables optimizations, and catches bugs at compile time*.

---

## 2. Binary Fundamentals — What the CPU Actually Sees

### Positional Notation

At the hardware level, everything is bits. The number `42` in different widths:

```
8-bit:   0010 1010
16-bit:  0000 0000 0010 1010
32-bit:  0000 0000 0000 0000 0000 0000 0010 1010
```

**Bit position weight** (unsigned interpretation):
```
Position: 7  6  5  4  3  2  1  0
Weight:   128 64 32 16  8  4  2  1

0010 1010 = 0 + 0 + 32 + 0 + 8 + 0 + 2 + 0 = 42 ✓
```

### Why This Matters in Code

```c
// C — raw memory inspection
#include <stdio.h>
#include <stdint.h>
#include <string.h>

void print_bits(uint64_t val, int width) {
    for (int i = width - 1; i >= 0; i--) {
        printf("%llu", (val >> i) & 1);
        if (i % 4 == 0 && i > 0) printf(" ");
    }
    printf("\n");
}

int main() {
    uint8_t  a = 42;
    uint16_t b = 42;
    uint32_t c = 42;
    
    printf("u8:  "); print_bits(a, 8);
    printf("u16: "); print_bits(b, 16);
    printf("u32: "); print_bits(c, 32);
    
    // Same bit pattern, different semantics based on type
    uint8_t  raw = 0xFF;
    int8_t   signed_raw;
    memcpy(&signed_raw, &raw, 1);
    
    printf("0xFF as u8:  %u\n", raw);        // 255
    printf("0xFF as i8:  %d\n", signed_raw); // -1
    return 0;
}
```

```go
// Go — same concept
package main

import (
    "fmt"
    "math/bits"
)

func printBits(val uint64, width int) {
    for i := width - 1; i >= 0; i-- {
        fmt.Printf("%d", (val>>i)&1)
        if i%4 == 0 && i > 0 {
            fmt.Print(" ")
        }
    }
    fmt.Println()
}

func main() {
    var raw uint8 = 0xFF
    // Reinterpret the same bits as signed
    signed := int8(raw)
    
    fmt.Printf("0xFF as uint8: %d\n", raw)    // 255
    fmt.Printf("0xFF as int8:  %d\n", signed) // -1
    
    fmt.Printf("Leading zeros in 42 (uint64): %d\n", bits.LeadingZeros64(42))
    fmt.Printf("Population count of 42:       %d\n", bits.OnesCount64(42))
}
```

```rust
// Rust — with explicit transmute for unsafe reinterpretation
fn print_bits(val: u64, width: usize) {
    for i in (0..width).rev() {
        print!("{}", (val >> i) & 1);
        if i % 4 == 0 && i > 0 { print!(" "); }
    }
    println!();
}

fn main() {
    let raw: u8 = 0xFF;
    let signed = raw as i8;  // safe cast — Rust reinterprets
    
    println!("0xFF as u8:  {}", raw);     // 255
    println!("0xFF as i8:  {}", signed);  // -1
    
    print_bits(42, 8);  // 0010 1010
    
    // Rust's rich integer methods
    println!("Leading zeros: {}", 42u64.leading_zeros());
    println!("Count ones:    {}", 42u64.count_ones());
    println!("Next power of 2: {}", 42u64.next_power_of_two());
}
```

---

## 3. Signed vs Unsigned — Two's Complement Deep Dive

### The Key Question: How Do We Represent Negative Numbers?

Three historical approaches exist. Only one won.

#### Approach 1: Sign-Magnitude (Intuitive but broken)
```
+5 = 0000 0101
-5 = 1000 0101  (flip the sign bit)

Problem: +0 = 0000 0000 and -0 = 1000 0000  — two zeros!
Addition hardware needs special cases.
```

#### Approach 2: One's Complement (Better but still broken)
```
+5 = 0000 0101
-5 = 1111 1010  (flip all bits)

Still has two zeros. Addition wraps awkwardly.
```

#### Approach 3: Two's Complement (The Winner) ✓
```
+5 = 0000 0101
-5 = 1111 1011  (flip all bits, then add 1)

Only one zero. Addition/subtraction use the SAME hardware circuit.
```

### Two's Complement: The Mathematical Insight

For an N-bit signed integer, the MSB (most significant bit) has weight **−2^(N-1)** instead of **+2^(N-1)**.

```
8-bit two's complement:
Position: 7    6  5  4  3  2  1  0
Weight:  -128  64 32 16  8  4  2  1

1111 1011 = -128 + 64 + 32 + 16 + 8 + 0 + 2 + 1 = -128 + 123 = -5 ✓
```

### Range Formulas

| Type | Min | Max |
|---|---|---|
| Unsigned N-bit | 0 | 2^N − 1 |
| Signed N-bit | −2^(N-1) | 2^(N-1) − 1 |

Notice the asymmetry: **signed ranges are not symmetric**. `i8` goes from -128 to +127. There is no +128. This trips up beginners constantly.

```rust
fn main() {
    println!("i8  range: {} to {}", i8::MIN, i8::MAX);     // -128 to 127
    println!("u8  range: {} to {}", u8::MIN, u8::MAX);     // 0 to 255
    println!("i16 range: {} to {}", i16::MIN, i16::MAX);   // -32768 to 32767
    println!("u16 range: {} to {}", u16::MIN, u16::MAX);   // 0 to 65535
    println!("i32 range: {} to {}", i32::MIN, i32::MAX);   // -2147483648 to 2147483647
    println!("i64 range: {} to {}", i64::MIN, i64::MAX);   // ±9.2 × 10^18
    
    // The asymmetry trap
    let x: i8 = i8::MIN;  // -128
    // let y = x.abs();   // PANICS in debug! abs(-128) = 128, which overflows i8
    let y = x.checked_abs().unwrap_or(i8::MAX);  // Safe handling
    println!("Safe abs of i8::MIN: {}", y);
}
```

```c
#include <stdio.h>
#include <stdint.h>
#include <limits.h>

int main() {
    printf("INT8_MIN  = %d\n",   INT8_MIN);    // -128
    printf("INT8_MAX  = %d\n",   INT8_MAX);    // 127
    printf("UINT8_MAX = %u\n",   UINT8_MAX);   // 255
    printf("INT32_MIN = %d\n",   INT32_MIN);   // -2147483648
    printf("INT64_MAX = %lld\n", INT64_MAX);   // 9223372036854775807
    
    // The asymmetry trap in C — undefined behavior!
    int8_t x = INT8_MIN; // -128
    // int8_t y = -x;    // UB! -(-128) = 128, overflows
    return 0;
}
```

### Why Unsigned for Bit Operations?

When you're treating data as raw bits (not as a number), use unsigned types. Right-shifting a signed integer performs **arithmetic shift** (fills with sign bit), while unsigned performs **logical shift** (fills with 0).

```c
int8_t  signed_val   = -4;   // 1111 1100
uint8_t unsigned_val = 252;  // 1111 1100  (same bits!)

// Arithmetic right shift (signed):
signed_val >> 1;    // 1111 1110 = -2  (sign bit preserved)

// Logical right shift (unsigned):
unsigned_val >> 1;  // 0111 1110 = 126 (zero filled)
```

```rust
fn main() {
    let a: i8 = -4;    // 1111 1100
    let b: u8 = 252;   // 1111 1100

    println!("i8  -4   >> 1 = {}", a >> 1);  // -2 (arithmetic shift)
    println!("u8  252  >> 1 = {}", b >> 1);  // 126 (logical shift)
    
    // Rust gives you both explicitly
    println!("Unsigned >> on i8: {}", (-4i8 as u8) >> 1);  // 126
}
```

---

## 4. The Width Taxonomy: 8, 16, 32, 64, 128 bits

### u8 / i8 — The Byte

The fundamental atom of data. Every network packet, file, pixel, and encryption algorithm lives in bytes.

**Range:** u8 → [0, 255], i8 → [-128, 127]

```rust
// Canonical u8 use cases
let pixel_red: u8 = 255;
let ascii_char: u8 = b'A';         // 65
let utf8_byte: u8 = 0xE2;          // Part of multi-byte UTF-8 sequence
let checksum: u8 = data.iter().fold(0u8, |acc, &x| acc.wrapping_add(x));
```

```go
// Go — u8 is 'byte', which is alias for uint8
var b byte = 0xFF
var signed int8 = int8(b)  // -1
packet := []byte{0x48, 0x65, 0x6C, 0x6C, 0x6F}  // "Hello"
```

```c
uint8_t pixel[4] = {255, 128, 0, 255}; // RGBA
char    ascii    = 'A';                // 65 — note: 'char' signedness is implementation-defined!
unsigned char safe_byte = 200;         // Always use unsigned char for bytes
```

**Critical C Pitfall:** `char` is **implementation-defined** as signed or unsigned. Always use `unsigned char` or `uint8_t` for raw bytes.

---

### u16 / i16 — The Short

Common in legacy systems, audio, and network protocols. 

**Range:** u16 → [0, 65535], i16 → [-32768, 32767]

```rust
// Network ports — defined by TCP/UDP spec as 16-bit
let http_port: u16 = 80;
let https_port: u16 = 443;
let max_port: u16 = 65535;

// Audio — PCM samples at 16-bit depth (CD quality)
let audio_sample: i16 = 32767;  // Max amplitude

// Unicode code point subset (BMP plane)
let utf16_char: u16 = 0x4E2D;   // Chinese character 中
```

```go
// Go: uint16, int16
var port uint16 = 8080
var sample int16 = -32768  // Min audio amplitude

// IPv4 header uses 16-bit fields
type IPv4Header struct {
    TotalLength    uint16
    Identification uint16
    Checksum       uint16
}
```

```c
// Audio processing — aligned with hardware DAC/ADC precision
int16_t  audio_buffer[1024];
uint16_t tcp_port = 443;

// ELF file format uses 16-bit fields
typedef struct {
    uint16_t e_type;      // Object file type
    uint16_t e_machine;   // Architecture
    uint16_t e_version;   // Version
} Elf32_Ehdr_partial;
```

---

### u32 / i32 — The Workhorse

The most common general-purpose integer. On most 32-bit and 64-bit CPUs, 32-bit operations are native and fast.

**Range:** u32 → [0, ~4.3 billion], i32 → [~-2.1B, ~2.1B]

```rust
// Hash values — most hash algorithms produce 32-bit outputs
let hash: u32 = 0xDEADBEEF;

// IPv4 addresses — exactly 32 bits
let localhost: u32 = 0x7F000001;  // 127.0.0.1

// Unix timestamps (until 2038!)
let epoch: u32 = 1700000000;

// Color in 0xRRGGBBAA format
let red: u32 = 0xFF0000FF;

// Array indices (common in 32-bit systems)
let index: u32 = 42;
```

```go
var color uint32 = 0xFF6600FF  // Orange, full opacity
var crc32_val uint32

// rune is alias for int32 — Unicode code points
var r rune = '中'  // U+4E2D = 20013 as int32
fmt.Printf("%c = U+%04X = %d\n", r, r, r)
```

```c
// Most hash functions return uint32_t
uint32_t fnv1a_hash(const char *str) {
    uint32_t hash = 2166136261u;
    while (*str) {
        hash ^= (uint8_t)*str++;
        hash *= 16777619u;
    }
    return hash;
}

// IPv4
struct in_addr {
    uint32_t s_addr;  // Network byte order
};
```

---

### u64 / i64 — The 64-bit Giant

The natural integer size on 64-bit systems. Required for anything that can exceed ~4 billion.

**Range:** u64 → [0, ~1.8 × 10^19], i64 → [~±9.2 × 10^18]

```rust
// File sizes, memory sizes on modern systems
let file_size: u64 = 8_589_934_592; // 8 GB

// Nanosecond timestamps
let timestamp_ns: u64 = 1_700_000_000_000_000_000;

// Database primary keys
let user_id: u64 = 9_223_372_036_854_775_807;

// Pointer-sized operations (often u64 on 64-bit systems)
let addr: u64 = 0x7FFF_5FBF_F580;

// Bitcoin satoshis (max 21M BTC × 10^8 = 2.1 × 10^15, fits in i64)
let satoshis: i64 = 2_100_000_000_000_000;

// Bitset / flags — 64 independent boolean flags in one word
let permissions: u64 = 0b0000_0000_0000_0000_0000_0000_0000_0111;
```

```go
// Go: int is 64-bit on 64-bit platforms (but not guaranteed!)
var fileSize int64 = 8 * 1024 * 1024 * 1024  // 8 GB

// time.Duration is int64 (nanoseconds)
import "time"
duration := 2*time.Hour + 30*time.Minute  // int64 nanoseconds internally

// sync/atomic operations require 64-bit types
var counter uint64
atomic.AddUint64(&counter, 1)
```

```c
// POSIX file operations
#include <sys/stat.h>
struct stat st;
stat("large_file.bin", &st);
off_t size = st.st_size;  // off_t is typically int64_t on modern systems

// Atomic operations
#include <stdatomic.h>
atomic_uint_fast64_t counter = ATOMIC_VAR_INIT(0);
atomic_fetch_add(&counter, 1);
```

---

### u128 / i128 — The Heavyweight

Not a native CPU type on most architectures — emulated with two 64-bit operations. Use sparingly.

**Range:** u128 → [0, ~3.4 × 10^38]

```rust
// Cryptographic nonces, UUIDs
let uuid: u128 = 0x6ba7b810_9dad_11d1_80b4_00c04fd430c8;

// Very large counters (nanoseconds since Big Bang would fit)
let ns_since_big_bang: u128 = 4_320_000_000 * 1_000_000_000; // still fits!

// 128-bit hash outputs (MD5, etc.)
let md5_hash: u128 = 0xd41d8cd98f00b204e9800998ecf8427e;

// IPv6 addresses — exactly 128 bits
let ipv6_loopback: u128 = 1; // ::1
```

```go
// Go has no native int128; use math/big or two uint64s
import "math/big"
big128 := new(big.Int).SetUint64(^uint64(0))  // 2^64 - 1

// For UUID, use [16]byte
type UUID [16]byte
```

```c
// GCC/Clang extension — not C standard
__uint128_t big = (__uint128_t)1 << 100;

// For portable code, use two uint64_t
typedef struct { uint64_t hi, lo; } uint128_t;
```

---

## 5. Platform-Dependent Types

### The Subtlety That Breaks Portability

Some types change size depending on the target architecture. This is intentional — they represent the CPU's "natural" word size.

```
Architecture | usize/isize (Rust) | size_t (C) | int (C)
-------------|-------------------|------------|--------
x86 (32-bit) | 4 bytes           | 4 bytes    | 4 bytes
x86_64       | 8 bytes           | 8 bytes    | 4 bytes  ← int stays 32-bit!
ARM64        | 8 bytes           | 8 bytes    | 4 bytes
ARM32        | 4 bytes           | 4 bytes    | 4 bytes
```

**Notice:** In C, `int` is always 32-bit on modern platforms, even on 64-bit systems. This is the "LP64" model (Long and Pointer are 64-bit, int stays 32-bit).

### Rust: usize/isize

```rust
// Array/slice indexing — MUST use usize
let arr = [1, 2, 3, 4, 5];
let i: usize = 2;
println!("{}", arr[i]);  // Only usize can index

// Memory addresses
let ptr = arr.as_ptr() as usize;
println!("Pointer value: {:#x}", ptr);

// Collection lengths always return usize
let len: usize = arr.len();

// usize for loop counters over collections
for i in 0..arr.len() {  // 0..len is Range<usize>
    println!("{}", arr[i]);
}

// Caution: usize subtraction can wrap/panic
let a: usize = 3;
let b: usize = 5;
// let diff = a - b;  // PANICS in debug, wraps in release
let diff = a.saturating_sub(b);  // Safe: gives 0
```

### Go: int/uint

```go
// Go's 'int' is platform-sized — do NOT assume 32 or 64 bits
var n int = 42  // 64-bit on 64-bit systems, 32-bit on 32-bit systems

// For portability across architectures:
var portable int64 = 42  // Always 64 bits

// Slice/map lengths return int (not uint!)
s := []int{1, 2, 3}
n = len(s)     // int
n = cap(s)     // int

// Pointer arithmetic via uintptr (unsafe)
import "unsafe"
ptr := uintptr(unsafe.Pointer(&s[0]))
nextPtr := ptr + unsafe.Sizeof(s[0])
```

### C: size_t and ptrdiff_t

```c
#include <stddef.h>  // For size_t, ptrdiff_t

// size_t for sizes and counts — ALWAYS unsigned
size_t len = strlen("hello");  // 5
void* buf = malloc(len);       // malloc takes size_t

// ptrdiff_t for pointer differences — ALWAYS signed
int arr[] = {1, 2, 3, 4, 5};
int *a = &arr[1];
int *b = &arr[4];
ptrdiff_t diff = b - a;  // 3 — can be negative if a > b

// intptr_t / uintptr_t for storing pointer values
uintptr_t addr = (uintptr_t)buf;

// The classic mistake: using int for array index
int n = 2000000000;
for (int i = 0; i < n; i++) {  // OK on 32-bit, but n*4 = 8GB array would require size_t
    // ...
}
```

---

## 6. Overflow and Underflow

### The Three Models

| Language | Default | What happens at overflow |
|---|---|---|
| **C** | Signed: UB, Unsigned: wraps | Signed overflow = undefined behavior (demons!) |
| **Go** | Wraps silently | No panic, wraps modulo 2^N |
| **Rust Debug** | Panics | Runtime panic on overflow |
| **Rust Release** | Wraps | Silently wraps (like Go) |

### C: The Minefield

```c
#include <stdio.h>
#include <stdint.h>

int main() {
    // UNSIGNED overflow — DEFINED: wraps modulo 2^N
    uint8_t a = 255;
    a++;  // Wraps to 0 — guaranteed by C standard
    printf("uint8 256 wraps to: %u\n", a);  // 0

    // SIGNED overflow — UNDEFINED BEHAVIOR
    int8_t b = 127;
    b++;  // ← UNDEFINED BEHAVIOR — compiler can do ANYTHING
    printf("int8 128: %d\n", b);  // Might print -128, might crash, might do neither
    
    // Compiler WILL optimize assuming this never happens:
    // "if (x + 1 > x)" — compiler may remove this check entirely!
    
    // Safe alternatives:
    // 1. Check before operation
    if (b < INT8_MAX) b++;
    
    // 2. Use unsigned and cast
    uint8_t c = (uint8_t)b;
    c++;  // Defined wrapping
    b = (int8_t)c;
    
    // 3. GCC built-in overflow check
    int8_t result;
    if (__builtin_add_overflow(b, (int8_t)1, &result)) {
        printf("Overflow detected!\n");
    }
    return 0;
}
```

### Go: Silent Wrapping

```go
package main

import (
    "fmt"
    "math"
)

func main() {
    // Go wraps silently — no panic, no UB
    var a uint8 = 255
    a++
    fmt.Println("uint8 overflow:", a)  // 0

    var b int8 = 127
    b++
    fmt.Println("int8 overflow:", b)   // -128

    // Go has no built-in overflow detection
    // Manual check pattern:
    x := math.MaxInt64
    if x == math.MaxInt64 {
        fmt.Println("Would overflow, handle it")
    }
    
    // Or use math/bits for detected arithmetic
    import "math/bits"
    sum, carry := bits.Add64(uint64(math.MaxUint64), 1, 0)
    fmt.Printf("sum=%d carry=%d\n", sum, carry)  // sum=0 carry=1
}
```

### Rust: The Safest Model

```rust
fn main() {
    // Debug mode: panics on overflow
    // Release mode: wraps (same as C unsigned)
    
    // Always-safe checked arithmetic
    let a: u8 = 255;
    let result = a.checked_add(1);
    match result {
        Some(v) => println!("Result: {}", v),
        None    => println!("Overflow detected!"),  // ← This prints
    }
    
    // Wrapping arithmetic (explicit intent)
    let b: u8 = 255;
    let wrapped = b.wrapping_add(1);  // 0 — intentional wraparound
    println!("Wrapped: {}", wrapped);
    
    // Saturating arithmetic (clamp at boundary)
    let c: u8 = 255;
    let saturated = c.saturating_add(1);  // 255 — stays at max
    println!("Saturated: {}", saturated);
    
    // Overflowing arithmetic (returns value + overflow flag)
    let d: u8 = 255;
    let (val, overflowed) = d.overflowing_add(1);
    println!("Value: {}, Overflowed: {}", val, overflowed);  // 0, true
}
```

**The Rust Mental Model:** Never accidentally overflow. Choose your overflow semantics explicitly:
- `.checked_*()` → Option — for when overflow is an error
- `.wrapping_*()` → value — for hash/crypto/cyclic counters
- `.saturating_*()` → value — for signal processing, clamping
- `.overflowing_*()` → (value, bool) — for multi-word arithmetic

---

## 7. Type Casting and Promotion

### C: Implicit Promotion (The Source of Many Bugs)

C's integer promotion rules silently convert types before operations:

```c
#include <stdio.h>
#include <stdint.h>

int main() {
    // Rule: operands smaller than int are promoted to int first
    uint8_t  a = 200;
    uint8_t  b = 100;
    uint16_t c = a + b;  // a and b promoted to int, sum = 300, fits in u16
    printf("%u\n", c);   // 300 ✓ — works here
    
    // The trap: comparison between signed and unsigned
    int32_t  signed_val   = -1;
    uint32_t unsigned_val = 1;
    
    if (signed_val < unsigned_val) {
        printf("signed < unsigned\n");  // You'd expect this
    } else {
        printf("signed >= unsigned\n"); // THIS PRINTS — -1 promoted to uint32_t = 4294967295!
    }
    
    // Usual arithmetic conversions hierarchy:
    // long double > double > float > unsigned long long > long long >
    // unsigned long > long > unsigned int > int
    
    // Explicit cast to prevent promotion surprises
    int32_t result = (int32_t)((uint8_t)200 + (uint8_t)100);
    printf("Explicit: %d\n", result);  // 300
    
    return 0;
}
```

### Go: Explicit Casts Only

```go
package main

import "fmt"

func main() {
    // Go requires ALL conversions to be explicit — no implicit promotions
    var a int32 = 100
    var b int64 = 200
    
    // c := a + b  // ← Compile error: mismatched types
    c := int64(a) + b   // ✓ Explicit conversion required
    fmt.Println(c)
    
    // Byte to int
    var ch byte = 'A'   // 65
    var n int  = int(ch)
    fmt.Println(n)      // 65
    
    // Float to int truncates (no rounding)
    var f float64 = 3.99
    var i int     = int(f)
    fmt.Println(i)  // 3 (truncated, not 4)
    
    // Narrowing conversion — no error, wraps silently
    var big int32 = 300
    var small uint8 = uint8(big)
    fmt.Println(small)  // 44 (300 mod 256)
}
```

### Rust: Safe and Explicit

```rust
fn main() {
    // 'as' cast: safe widening, truncating/wrapping narrowing
    let a: u8  = 255;
    let b: u32 = a as u32;    // Widening: 255
    let c: u8  = 300u32 as u8; // Narrowing: truncates to 44 (300 & 0xFF)
    
    println!("Widened: {}", b);    // 255
    println!("Truncated: {}", c);  // 44
    
    // 'as' for signed ↔ unsigned reinterpretation
    let neg: i8 = -1;
    let pos: u8 = neg as u8;  // Reinterprets bits: 0xFF = 255
    println!("i8 -1 as u8: {}", pos);  // 255
    
    // For checked conversion: From/Into traits (infallible widening)
    let small: u8  = 100;
    let big: u64   = u64::from(small);  // Always safe
    println!("From: {}", big);
    
    // TryFrom for fallible conversions (narrowing that might fail)
    use std::convert::TryFrom;
    let large: u32 = 300;
    match u8::try_from(large) {
        Ok(v)  => println!("Fits: {}", v),
        Err(e) => println!("Doesn't fit: {}", e),  // ← This prints
    }
    
    // i32 → u32 when value is non-negative
    let x: i32 = 42;
    let y: u32 = u32::try_from(x).expect("Value was negative");
    println!("Safe conversion: {}", y);
}
```

---

## 8. Bit Manipulation Mastery

This is where integer types reveal their full power. Every expert-level programmer needs fluency here.

### Core Operations Reference

```
Operation        | C/Go          | Rust
-----------------|---------------|------------------
AND              | a & b         | a & b
OR               | a | b         | a | b
XOR              | a ^ b         | a ^ b
NOT              | ~a            | !a
Left shift       | a << n        | a << n
Right shift      | a >> n        | a >> n
```

### Essential Idioms

```rust
fn bit_tricks() {
    let n: u32 = 0b1010_1100;
    
    // Test bit k
    let k = 3;
    let is_set = (n >> k) & 1 == 1;
    println!("Bit {} set: {}", k, is_set);  // true
    
    // Set bit k
    let set = n | (1u32 << k);
    
    // Clear bit k
    let cleared = n & !(1u32 << k);
    
    // Toggle bit k
    let toggled = n ^ (1u32 << k);
    
    // Extract lowest set bit (isolate)
    let lowest = n & n.wrapping_neg();  // n & (-n) in signed
    println!("Lowest set bit: {:08b}", lowest);  // 0000_0100
    
    // Clear lowest set bit
    let cleared_lowest = n & (n - 1);
    println!("Cleared lowest: {:08b}", cleared_lowest);  // 1010_1000
    
    // Check if power of 2
    let is_pow2 = n != 0 && (n & (n - 1)) == 0;
    println!("Is power of 2: {}", is_pow2);  // false
    
    // Round up to next power of 2
    let next_p2 = n.next_power_of_two();
    
    // Count set bits (popcount / Hamming weight)
    let popcount = n.count_ones();
    println!("Popcount: {}", popcount);  // 4
    
    // Reverse bits
    let reversed = n.reverse_bits();
    
    // Byte swap (endianness conversion)
    let swapped = n.swap_bytes();
    
    // Rotate bits
    let rotated_left  = n.rotate_left(3);
    let rotated_right = n.rotate_right(3);
}
```

```c
#include <stdint.h>
#include <stdio.h>

// GCC/Clang have built-ins for hardware-accelerated bit ops
void bit_tricks(uint32_t n) {
    // Count leading zeros
    int clz = __builtin_clz(n);
    
    // Count trailing zeros
    int ctz = __builtin_ctz(n);
    
    // Population count
    int pop = __builtin_popcount(n);
    
    // For 64-bit:
    long long m = n;
    int clz64 = __builtin_clzll(m);
    int pop64 = __builtin_popcountll(m);
    
    // Byte swap for endianness
    uint32_t swapped = __builtin_bswap32(n);
    uint64_t swapped64 = __builtin_bswap64((uint64_t)n);
    
    printf("CLZ=%d, CTZ=%d, Pop=%d\n", clz, ctz, pop);
}
```

```go
package main

import (
    "fmt"
    "math/bits"
)

func bitTricks(n uint32) {
    // Go's math/bits package — maps directly to hardware instructions
    fmt.Println("Leading zeros:", bits.LeadingZeros32(n))
    fmt.Println("Trailing zeros:", bits.TrailingZeros32(n))
    fmt.Println("Population count:", bits.OnesCount32(n))
    fmt.Println("Rotate left 3:", bits.RotateLeft32(n, 3))
    fmt.Println("Byte swap:", bits.ReverseBytes32(n))
    fmt.Println("Reverse bits:", bits.Reverse32(n))
    
    // Length (floor(log2(n)) + 1)
    fmt.Println("Bit length:", bits.Len32(n))
}
```

### Practical Bit Packing Example

```rust
// Packing multiple fields into a single u32
// Layout: [flags: 8 bits][priority: 4 bits][id: 20 bits]

const ID_BITS:       u32 = 20;
const PRIORITY_BITS: u32 = 4;
const FLAGS_BITS:    u32 = 8;

const ID_MASK:       u32 = (1 << ID_BITS) - 1;        // 0x000FFFFF
const PRIORITY_MASK: u32 = (1 << PRIORITY_BITS) - 1;  // 0x0000000F
const FLAGS_MASK:    u32 = (1 << FLAGS_BITS) - 1;      // 0x000000FF

const PRIORITY_SHIFT: u32 = ID_BITS;                  // 20
const FLAGS_SHIFT:    u32 = ID_BITS + PRIORITY_BITS;  // 24

fn pack(id: u32, priority: u32, flags: u32) -> u32 {
    (flags    & FLAGS_MASK)    << FLAGS_SHIFT |
    (priority & PRIORITY_MASK) << PRIORITY_SHIFT |
    (id       & ID_MASK)
}

fn unpack(val: u32) -> (u32, u32, u32) {
    let id       = val & ID_MASK;
    let priority = (val >> PRIORITY_SHIFT) & PRIORITY_MASK;
    let flags    = (val >> FLAGS_SHIFT) & FLAGS_MASK;
    (id, priority, flags)
}

fn main() {
    let packed = pack(123456, 7, 0b10110011);
    let (id, pri, flags) = unpack(packed);
    println!("id={} priority={} flags={:08b}", id, pri, flags);
}
```

---

## 9. Real-World Use Cases

### 9.1 Networking / Protocols

```rust
// TCP/IP header parsing — every field has a precise bit width
use std::net::Ipv4Addr;

#[repr(C, packed)]
struct IPv4Header {
    version_ihl:  u8,   // 4 bits version + 4 bits IHL
    dscp_ecn:     u8,   // 6 bits DSCP + 2 bits ECN
    total_length: u16,  // Total packet length (network byte order)
    id:           u16,
    flags_frag:   u16,  // 3 bits flags + 13 bits fragment offset
    ttl:          u8,
    protocol:     u8,   // 6=TCP, 17=UDP, 1=ICMP
    checksum:     u16,
    src:          u32,
    dst:          u32,
}

impl IPv4Header {
    fn version(&self) -> u8 { self.version_ihl >> 4 }
    fn ihl(&self) -> u8 { self.version_ihl & 0x0F }
    fn src_addr(&self) -> Ipv4Addr {
        Ipv4Addr::from(u32::from_be(self.src))
    }
}
```

```go
// DNS message parsing
type DNSHeader struct {
    ID      uint16 // Transaction ID
    Flags   uint16 // QR|Opcode|AA|TC|RD|RA|Z|RCODE
    QDCount uint16 // Questions
    ANCount uint16 // Answer RRs
    NSCount uint16 // Authority RRs
    ARCount uint16 // Additional RRs
}

func (h *DNSHeader) IsResponse() bool  { return h.Flags>>15 == 1 }
func (h *DNSHeader) Opcode() uint16    { return (h.Flags >> 11) & 0xF }
func (h *DNSHeader) RCode() uint16     { return h.Flags & 0xF }
```

### 9.2 Image Processing

```c
// Efficient pixel manipulation — u8 per channel, SIMD-friendly layout
typedef struct { uint8_t r, g, b, a; } Pixel;

// Convert RGB to grayscale (luminance formula)
uint8_t to_grayscale(Pixel p) {
    // Weighted sum — integer arithmetic avoids floats
    // 0.299*R + 0.587*G + 0.114*B
    // Scaled by 256 to avoid float: (77*R + 150*G + 29*B) / 256
    uint32_t luma = 77u * p.r + 150u * p.g + 29u * p.b;
    return (uint8_t)(luma >> 8);  // Divide by 256
}

// Alpha blending: dst = src * alpha + dst * (1 - alpha)
Pixel alpha_blend(Pixel src, Pixel dst) {
    uint16_t alpha = src.a;
    uint16_t inv_alpha = 255 - alpha;
    return (Pixel){
        .r = (uint8_t)((src.r * alpha + dst.r * inv_alpha) / 255),
        .g = (uint8_t)((src.g * alpha + dst.g * inv_alpha) / 255),
        .b = (uint8_t)((src.b * alpha + dst.b * inv_alpha) / 255),
        .a = 255,
    };
}
```

### 9.3 Cryptography and Hashing

```rust
// FNV-1a hash — 32-bit and 64-bit variants
fn fnv1a_32(data: &[u8]) -> u32 {
    const BASIS: u32 = 2166136261;
    const PRIME: u32 = 16777619;
    data.iter().fold(BASIS, |hash, &byte| {
        (hash ^ byte as u32).wrapping_mul(PRIME)
    })
}

fn fnv1a_64(data: &[u8]) -> u64 {
    const BASIS: u64 = 14695981039346656037;
    const PRIME: u64 = 1099511628211;
    data.iter().fold(BASIS, |hash, &byte| {
        (hash ^ byte as u64).wrapping_mul(PRIME)
    })
}

// XOR shift RNG — fits in u64
struct XorShift64 { state: u64 }

impl XorShift64 {
    fn next(&mut self) -> u64 {
        self.state ^= self.state << 13;
        self.state ^= self.state >> 7;
        self.state ^= self.state << 17;
        self.state
    }
}
```

### 9.4 Embedded Systems

```c
// Register-mapped I/O — exact bit positions matter
// ARM Cortex-M GPIO example

#define GPIOA_BASE  0x40020000UL
#define GPIO_MODER  (*(volatile uint32_t*)(GPIOA_BASE + 0x00))
#define GPIO_ODR    (*(volatile uint32_t*)(GPIOA_BASE + 0x14))

// Configure pin 5 as output (MODER[11:10] = 01)
void gpio_set_output(int pin) {
    GPIO_MODER &= ~(0x3u << (pin * 2));  // Clear 2 bits
    GPIO_MODER |=  (0x1u << (pin * 2));  // Set output mode
}

// Toggle pin
void gpio_toggle(int pin) {
    GPIO_ODR ^= (1u << pin);
}

// Read pin state
int gpio_read(int pin) {
    return (GPIO_ODR >> pin) & 1;
}
```

```rust
// Rust embedded with no_std — same precision, more safety
#[repr(C)]
struct GpioRegisters {
    moder:   u32,
    otyper:  u16,
    _pad0:   u16,
    ospeedr: u32,
    pupdr:   u32,
    idr:     u16,
    _pad1:   u16,
    odr:     u16,
    _pad2:   u16,
}

unsafe fn configure_gpio(gpio: *mut GpioRegisters, pin: u32) {
    let reg = &mut *gpio;
    reg.moder &= !(0x3 << (pin * 2));
    reg.moder |= 0x1 << (pin * 2);
}
```

### 9.5 Database Internals

```go
// B-tree node — compact representation matters for cache efficiency
type BTreeNode struct {
    // Pack metadata into a single uint32 for atomic operations
    meta     uint32  // [is_leaf:1][key_count:15][level:8][flags:8]
    keys     [255]int64
    children [256]uint32  // Page IDs — uint32 allows 4B pages
}

func (n *BTreeNode) IsLeaf() bool     { return n.meta>>31 == 1 }
func (n *BTreeNode) KeyCount() int    { return int((n.meta >> 16) & 0x7FFF) }
func (n *BTreeNode) Level() uint8     { return uint8((n.meta >> 8) & 0xFF) }

// Varint encoding (Protocol Buffers style) — store small ints in 1 byte
func encodeVarint(buf []byte, v uint64) int {
    i := 0
    for v >= 0x80 {
        buf[i] = byte(v) | 0x80
        v >>= 7
        i++
    }
    buf[i] = byte(v)
    return i + 1
}
```

### 9.6 Permissions and Bit Flags

```rust
// Unix-style permission flags
bitflags::bitflags! {
    pub struct Permissions: u16 {
        const OWNER_READ    = 0o400;
        const OWNER_WRITE   = 0o200;
        const OWNER_EXEC    = 0o100;
        const GROUP_READ    = 0o040;
        const GROUP_WRITE   = 0o020;
        const GROUP_EXEC    = 0o010;
        const OTHER_READ    = 0o004;
        const OTHER_WRITE   = 0o002;
        const OTHER_EXEC    = 0o001;
        const SETUID        = 0o4000;
        const SETGID        = 0o2000;
        const STICKY        = 0o1000;
    }
}

// Without the crate, manual bit flags
const READ:    u8 = 1 << 2;  // 4
const WRITE:   u8 = 1 << 1;  // 2
const EXECUTE: u8 = 1 << 0;  // 1

fn can_read(perms: u8) -> bool  { perms & READ != 0 }
fn can_write(perms: u8) -> bool { perms & WRITE != 0 }
```

---

## 10. Performance and Memory Implications

### Cache Lines and Data Layout

Modern CPUs load data in **64-byte cache lines**. Integer width directly impacts how many elements fit per cache line:

| Type | Elements per cache line | Practical impact |
|---|---|---|
| u8  | 64 | Maximum throughput for byte arrays |
| u16 | 32 | Half throughput |
| u32 | 16 | Quarter |
| u64 | 8  | Eighth |
| u128 | 4 | Not native — requires 2 u64 ops |

```rust
// This matters enormously in tight loops
fn sum_u8(data: &[u8]) -> u32 {
    // CPU can load 64 u8 per cache line, vectorize with SIMD (32 per AVX2 register)
    data.iter().map(|&x| x as u32).sum()
}

fn sum_u64(data: &[u64]) -> u64 {
    // CPU loads 8 u64 per cache line — same bytes, 8x fewer elements
    data.iter().sum()
}
```

### SIMD Vectorization

Using smaller types enables the CPU to process more data per instruction:

```c
// AVX2 can process:
// 32 × uint8_t in one instruction
// 16 × uint16_t
//  8 × uint32_t
//  4 × uint64_t

#include <immintrin.h>

// Process 32 bytes simultaneously — auto-vectorized by modern compilers
void add_arrays_u8(const uint8_t* a, const uint8_t* b, uint8_t* c, size_t n) {
    for (size_t i = 0; i < n; i++) {
        c[i] = a[i] + b[i];  // Compiler vectorizes this with PMOVZXBW + PADDW
    }
}
```

### Memory Alignment

```c
// Misaligned access can cause performance penalties or hardware exceptions
struct BadLayout {
    uint8_t  a;    // offset 0
    // 3 bytes padding inserted by compiler
    uint32_t b;    // offset 4 (aligned to 4 bytes)
    uint8_t  c;    // offset 8
    // 7 bytes padding
    uint64_t d;    // offset 16 (aligned to 8 bytes)
};  // Total: 24 bytes

struct GoodLayout {
    uint64_t d;    // offset 0  — largest first
    uint32_t b;    // offset 8
    uint8_t  a;    // offset 12
    uint8_t  c;    // offset 13
    // 2 bytes padding
};  // Total: 16 bytes — 33% smaller!
```

```rust
// Rust respects alignment automatically
// Use repr(packed) to eliminate padding (may cause misaligned access)
#[repr(C)]
struct Aligned {
    d: u64,  // 8 bytes
    b: u32,  // 4 bytes
    a: u8,   // 1 byte
    c: u8,   // 1 byte
             // 2 bytes padding for alignment
}

println!("Size: {}", std::mem::size_of::<Aligned>());  // 16
```

---

## 11. Common Pitfalls

### The Year 2038 Problem (i32 Overflow)

```c
// Unix timestamp stored as int32_t overflows on Jan 19, 2038 03:14:07 UTC
time_t now = time(NULL);  // time_t should be int64_t on modern systems

// Check: on YOUR system, what is time_t?
printf("time_t size: %zu bytes\n", sizeof(time_t));  // Should print 8

// Embedded systems still using 32-bit timestamps will break!
uint32_t old_timestamp = 2147483647;  // 2038 edge — next second wraps!
```

### Signed/Unsigned Comparison in C

```c
// This is a notorious bug source
void process(int8_t* data, uint32_t len) {
    for (int i = 0; i < len; i++) {  // DANGER: int vs uint32_t
        // When len > INT_MAX, this comparison is UB
        // When len = 0 (zero-length array), i < len:
        // i = 0 (int), len = 0 (uint32_t)
        // 0 < 0 is false — loop doesn't execute ✓ (works by accident)
    }
    
    // But:
    uint32_t len2 = 0;
    if (len2 - 1 > 0) {  // uint32_t underflow: 0 - 1 = 4294967295 > 0 = TRUE!
        printf("This should never print... but it does\n");
    }
}
```

### Integer Compression Trap in Go

```go
// Go's int is 64-bit on 64-bit platforms — but int32 is not int!
var a int32 = 100
var b int   = 200

// These don't mix:
// c := a + b  // Compile error

// Safe in Go, surprising to C programmers:
var x uint32 = 4294967295  // MaxUint32
x++  // Wraps silently to 0 — no panic, no warning
```

### Rust's "as" Cast Truncates, Not Clamps

```rust
fn main() {
    let big: u32 = 1000;
    let small: u8 = big as u8;  // Truncates: 1000 % 256 = 232
    // Most bugs come from thinking "as" will clamp or error
    
    // If you want clamping:
    let clamped: u8 = big.min(u8::MAX as u32) as u8;  // 255
    
    // If you want error on overflow:
    let checked = u8::try_from(big);  // Err(TryFromIntError)
}
```

---

## 12. Language Implementations: Full Reference

### Rust Integer Type System

```rust
// Complete Rust integer taxonomy
fn rust_integers() {
    // Fixed-width signed
    let _a: i8   = -128;
    let _b: i16  = -32768;
    let _c: i32  = -2_147_483_648;
    let _d: i64  = -9_223_372_036_854_775_808;
    let _e: i128 = i128::MIN;
    
    // Fixed-width unsigned
    let _f: u8   = 255;
    let _g: u16  = 65535;
    let _h: u32  = 4_294_967_295;
    let _i: u64  = 18_446_744_073_709_551_615;
    let _j: u128 = u128::MAX;
    
    // Platform-dependent
    let _k: isize = -1;  // i32 on 32-bit, i64 on 64-bit
    let _l: usize = 0;   // u32 on 32-bit, u64 on 64-bit
    
    // Default inference: integer literals default to i32
    let x = 42;   // i32
    let y = 42u8; // u8 — suffix forces type
    let z: u64 = 42; // type annotation forces u64
    
    // Numeric methods — Rust has the richest stdlib for integers
    println!("{}", 255u8.leading_zeros()); // 0
    println!("{}", 1u8.leading_zeros());   // 7
    println!("{}", 42u32.pow(3));          // 74088
    println!("{}", 2u64.checked_pow(63)); // Some(9223372036854775808)
    println!("{}", i64::MAX.checked_add(1)); // None
    
    // Endianness
    let be = 0xDEADBEEFu32.to_be_bytes(); // [0xDE, 0xAD, 0xBE, 0xEF]
    let le = 0xDEADBEEFu32.to_le_bytes(); // [0xEF, 0xBE, 0xAD, 0xDE]
    let reconstructed = u32::from_be_bytes(be);
    
    // Bit counting intrinsics
    println!("{}", 0b1010_1100u8.count_ones());   // 4
    println!("{}", 0b1010_1100u8.count_zeros());  // 4
    println!("{}", 0b1010_1100u8.reverse_bits()); // 0b0011_0101
}
```

### Go Integer Type System

```go
package main

import (
    "fmt"
    "math"
    "math/bits"
    "unsafe"
)

func goIntegers() {
    // Explicit-width types (via math constants)
    fmt.Println(math.MaxInt8, math.MinInt8)
    fmt.Println(math.MaxUint8)
    fmt.Println(math.MaxInt16, math.MinInt16)
    fmt.Println(math.MaxInt32, math.MinInt32)
    fmt.Println(math.MaxInt64, math.MinInt64)

    // Platform-size types
    var i   int    = 42   // Platform-sized signed
    var u   uint   = 42   // Platform-sized unsigned
    var ptr uintptr = uintptr(unsafe.Pointer(&i))
    
    // byte = uint8, rune = int32
    var b byte = 0xFF
    var r rune = '界'  // Unicode codepoint as int32

    // Integer literals: Go does NOT default-infer to specific widths
    // Untyped constants have "ideal" type, assigned based on context
    const Big = 1 << 62  // Untyped constant — fits anywhere it can

    // Bit operations via math/bits
    fmt.Println(bits.Len(42))          // 6 (ceil(log2(42)) + 1)
    fmt.Println(bits.OnesCount(42))    // 3
    fmt.Println(bits.RotateLeft(1, 3)) // 8

    // Endianness
    import "encoding/binary"
    buf := make([]byte, 8)
    binary.BigEndian.PutUint64(buf, 0xDEADBEEFCAFEBABE)
    val := binary.LittleEndian.Uint64(buf)
    
    _ = i; _ = u; _ = ptr; _ = b; _ = r; _ = val
}
```

### C Integer Type System

```c
#include <stdint.h>   // Fixed-width types
#include <stddef.h>   // size_t, ptrdiff_t
#include <inttypes.h> // printf format macros
#include <limits.h>   // Min/max constants

void c_integers() {
    // Fixed-width (always use these for portable code)
    int8_t   a = INT8_MIN;    // -128
    uint8_t  b = UINT8_MAX;   // 255
    int16_t  c = INT16_MAX;   // 32767
    uint16_t d = UINT16_MAX;  // 65535
    int32_t  e = INT32_MAX;   // 2147483647
    uint32_t f = UINT32_MAX;  // 4294967295
    int64_t  g = INT64_MAX;   // 9223372036854775807
    uint64_t h = UINT64_MAX;  // 18446744073709551615
    
    // Platform types (avoid using int/long for portable code)
    size_t    sz  = sizeof(int);  // Always unsigned
    ptrdiff_t pd  = 0;            // Pointer difference — signed
    intptr_t  ip  = (intptr_t)&a; // Pointer as integer
    
    // Portable printf format macros from <inttypes.h>
    printf("int64: %" PRId64 "\n", g);
    printf("uint64: %" PRIu64 "\n", h);
    printf("hex32: %" PRIx32 "\n", f);
    
    // Fast types (hint for CPU's preferred size, at least N bits)
    uint_fast8_t  fast8  = 42;  // Might actually be 32 or 64 bits!
    uint_fast16_t fast16 = 42;
    
    // Least types (guaranteed smallest size that can hold N bits)
    uint_least8_t  least8  = 42;  // Exactly 8 bits minimum
    uint_least16_t least16 = 42;
}
```

---

## Summary: Decision Framework

```
What integer type should I use?

1. Is it a memory address or array index?
   → usize (Rust) / size_t (C) / int (Go, with care)

2. Is it a known protocol/spec field?
   → Match the spec exactly: u16 for ports, u8 for bytes, etc.

3. Can the value be negative?
   → Yes: iN    No: uN

4. Do I need overflow to wrap (hash/crypto/counter)?
   → Use unsigned + wrapping_* in Rust, or unsigned in Go/C

5. What's the value range?
   → 0-255: u8    0-65535: u16    0-4B: u32    0-18E: u64

6. Performance-critical inner loop?
   → Smallest type that fits (cache efficiency, SIMD)
   → Avoid u128 (no native hardware support)

7. General purpose count/sum?
   → i32 in C/C++ (historical default, native on modern CPUs)
   → int in Go (idiomatic for loop vars)
   → i32/u32 in Rust unless bounds demand more
```

---

*The master programmer doesn't pick the biggest type for safety — they pick the smallest type that expresses the constraint. That precision is what separates experts from beginners.*

Here's the complete guide. Let me walk you through the intellectual architecture of this topic:

---

**The Central Insight — Types Are Constraints, and Constraints Are Power**

The question "why not one type?" dissolves once you internalize that types are not just containers — they are *documentation, optimization hints, and bug prevention rolled into one*. A `u8` tells the compiler, the reader, and the hardware: "this is a byte, nothing else." That constraint enables SIMD (processing 32 bytes per CPU instruction vs 4 u64s), prevents semantic errors, and communicates protocol specs directly in the type.

**The Three Mental Models You Must Own**

1. **Two's Complement** — Understand *why* `-1` as `u8` becomes `255`. It's not a cast, it's a reinterpretation of the same bits under a different weight function. The MSB carries weight `-2^(N-1)` instead of `+2^(N-1)`. This explains the asymmetry (`i8` has -128 but no +128), overflow wrapping, and why unsigned types are safer for bitwise ops.

2. **Overflow Semantics** — Rust's four-way split (checked/wrapping/saturating/overflowing) is the cleanest expression of what *you actually mean*. C's silent signed UB is the source of real CVEs. Go's silent wrapping is safe but invisible. Always know which model you're in.

3. **Width = Cache Efficiency** — 64 bytes per cache line. A `u8` array lets you load 64 elements at once; a `u64` array loads 8. In hot loops, this is a 8x difference. Smaller types also unlock SIMD vectorization automatically.

**Cognitive Principle at Work:** This is *chunking* in action — instead of memorizing 20 types individually, you now have 3 axes (width, signed/unsigned, overflow model) that generate the entire space. That's how experts compress knowledge.