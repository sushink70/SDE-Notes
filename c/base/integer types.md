# C Integer Types: A Complete, In-Depth Guide

> **Goal of this document:** Build a rock-solid mental model of every integer-related type in C — where each lives in memory, why it exists, when to use it, and the hidden traps that bite real programmers.

---

## Table of Contents

1. [The Fundamental Mental Model: What Is an Integer Type?](#1-the-fundamental-mental-model-what-is-an-integer-type)
2. [Memory Layout and the Number Line](#2-memory-layout-and-the-number-line)
3. [Standard Integer Types](#3-standard-integer-types)
   - 3.1 `char`
   - 3.2 `short`
   - 3.3 `int`
   - 3.4 `long`
   - 3.5 `long long`
4. [Sign Modifiers: `signed` and `unsigned`](#4-sign-modifiers-signed-and-unsigned)
5. [Fixed-Width Integer Types (`<stdint.h>`)](#5-fixed-width-integer-types-stdinth)
6. [Specialty Types](#6-specialty-types)
   - 6.1 `size_t`
   - 6.2 `ptrdiff_t`
   - 6.3 `intptr_t` / `uintptr_t`
   - 6.4 `intmax_t` / `uintmax_t`
   - 6.5 `_Bool` / `bool`
7. [Integer Representation: Two's Complement Deep Dive](#7-integer-representation-twos-complement-deep-dive)
8. [Integer Promotions and Arithmetic Conversions](#8-integer-promotions-and-arithmetic-conversions)
9. [Overflow, Underflow, and Undefined Behavior](#9-overflow-underflow-and-undefined-behavior)
10. [Literals, Suffixes, and Constants](#10-literals-suffixes-and-constants)
11. [Format Specifiers for printf/scanf](#11-format-specifiers-for-printfscanf)
12. [Choosing the Right Type: Decision Framework](#12-choosing-the-right-type-decision-framework)
13. [Platform Portability and the ABI](#13-platform-portability-and-the-abi)
14. [Common Pitfalls and Security Implications](#14-common-pitfalls-and-security-implications)
15. [Practical Code Patterns](#15-practical-code-patterns)
16. [Quick Reference Tables](#16-quick-reference-tables)

---

## 1. The Fundamental Mental Model: What Is an Integer Type?

At the machine level, a CPU does not understand "an integer." It understands **bits in registers**. The C type system is an abstraction that tells the compiler:

1. **How many bytes** to allocate for a variable.
2. **How to interpret** those bytes (signed or unsigned).
3. **What operations** are legal.
4. **What the range** of representable values is.

Think of a type as a **contract** between you and the compiler. When you declare:

```c
int x = 42;
```

You are saying: *"Allocate enough space for an `int`, store the bit pattern for 42 in it, and treat any arithmetic on it as signed integer arithmetic."*

The compiler fulfills that contract by generating machine code, and the CPU executes it without knowing or caring about types at all — types are a *compile-time concept*.

### The Three Axes of Every Integer Type

```
+-------------------+-------------------+------------------------+
|    WIDTH          |    SIGNEDNESS     |    ALIGNMENT           |
|  (how many bits)  |  (signed or not)  |  (where in memory)     |
+-------------------+-------------------+------------------------+
|  8, 16, 32, 64   |  signed:  has -   |  Usually = sizeof(type)|
|  (or more)        |  unsigned: 0..max |  Can be 1,2,4,8 bytes  |
+-------------------+-------------------+------------------------+
```

---

## 2. Memory Layout and the Number Line

### What a "Byte" Looks Like in Memory

Every integer type is stored in contiguous bytes. Here is how an `int` (4 bytes) with value `0x0A0B0C0D` looks in memory on a **little-endian** system (x86, ARM in LE mode):

```
Address:  0x1000   0x1001   0x1002   0x1003
          +------+ +------+ +------+ +------+
Value:    | 0x0D | | 0x0C | | 0x0B | | 0x0A |
          +------+ +------+ +------+ +------+
          LSB                              MSB
          (least significant byte at lowest address)
```

On a **big-endian** system (SPARC, some embedded):

```
Address:  0x1000   0x1001   0x1002   0x1003
          +------+ +------+ +------+ +------+
Value:    | 0x0A | | 0x0B | | 0x0C | | 0x0D |
          +------+ +------+ +------+ +------+
          MSB                              LSB
```

> **Why does this matter?** When you cast between integer types, read binary files, or work with network protocols (which are big-endian), endianness determines whether you get the right answer or garbage.

### The Number Line Mental Model

Every integer type occupies a segment of the integer number line. Signed types straddle zero; unsigned types start at zero:

```
unsigned 8-bit (uint8_t):
|---------|---------|---------|---------|---------|
0        64       128       192       255

signed 8-bit (int8_t):
|---------|---------|---------|---------|---------|
-128      -64        0        63       127

Wrapping behavior (modular arithmetic):
  255 + 1 = 0   (unsigned wraps around to start)
  127 + 1 = -128 (signed overflow — UNDEFINED BEHAVIOR in C!)
```

---

## 3. Standard Integer Types

The C standard defines these types in increasing minimum width. Each must be *at least* as wide as the one before it, but the compiler is free to make them wider.

```
char <= short <= int <= long <= long long
 8b     16b     16b    32b       64b
          (minimum sizes guaranteed by the standard)
```

---

### 3.1 `char`

#### What it is

`char` is the smallest addressable unit of the machine — exactly one byte, always. It is the building block of strings in C.

```c
char c = 'A';       // stores 65 (ASCII code for 'A')
char arr[5] = "Hi"; // {'H', 'i', '\0', ?, ?}
```

#### Memory

```
+--------+
|  0x41  |   <- 'A' in ASCII, 1 byte, 8 bits
+--------+
```

#### The Signedness Trap — The #1 `char` Gotcha

**The C standard does NOT define whether `char` is signed or unsigned. It is implementation-defined.**

```
On most x86 Linux systems:    char is SIGNED   (-128 to 127)
On ARM (e.g., iOS/Android):   char is UNSIGNED (0 to 255)
On some embedded compilers:   char is UNSIGNED by default
```

This creates a classic bug when processing byte values > 127:

```c
char c = 0xFF;       // On a signed-char system: c == -1
int x = c;           // sign extension! x == -1 (0xFFFFFFFF), NOT 255

unsigned char uc = 0xFF;  // Always 255, always safe
int y = uc;               // y == 255 — correct
```

#### The Three `char` Variants

```
+-----------------+----------------+------------------+
| char            | signed char    | unsigned char    |
+-----------------+----------------+------------------+
| sign is         | always signed  | always unsigned  |
| implementation- | -128 to 127    | 0 to 255         |
| defined         |                |                  |
| Used for text   | Used for small | Used for raw     |
| (strings)       | signed numbers | binary data/     |
|                 |                | byte arrays      |
+-----------------+----------------+------------------+
```

#### When to Use `char`

- **String handling:** Always use plain `char` for text/strings, because the C standard library expects `char*` for strings.
- **Raw binary data:** Use `unsigned char` (or `uint8_t`) for byte buffers, pixel data, network packets, file I/O.
- **Small signed integers:** Use `signed char` (or `int8_t`) when you explicitly need a signed tiny integer.
- **Never** use plain `char` for arithmetic if the value can exceed 127 — you will get portability bugs.

```c
// GOOD: string handling
char name[] = "Alice";
strlen(name);   // expects char*

// GOOD: binary data
unsigned char buffer[1024];
fread(buffer, 1, 1024, fp);

// BAD: arithmetic on plain char — implementation-defined sign
char val = 200;   // may store as -56 on signed-char systems!
```

---

### 3.2 `short`

`short` (full name: `short int`) is guaranteed to be **at least 16 bits**. On virtually every modern system it is exactly 16 bits.

#### Memory

```
+--------+--------+
|  byte0 |  byte1 |    2 bytes = 16 bits
+--------+--------+
```

#### Ranges

```
signed short:    -32,768  to  32,767
unsigned short:       0   to  65,535
```

#### When to Use `short`

- **Network protocol fields** where a 16-bit field is specified (e.g., TCP/UDP port numbers as `uint16_t`).
- **Hardware registers** that are 16 bits wide.
- **Memory-constrained arrays** — if you have a million-element array and each element fits in 16 bits, using `short` halves memory vs `int`.
- **Interoperability with file formats** or binary protocols specifying 16-bit values.

```c
// Port numbers: always 16-bit in TCP/IP
uint16_t port = 8080;

// Audio samples: CD quality is 16-bit signed
short pcm_samples[44100];  // 1 second at 44.1 kHz
```

#### When NOT to Use `short`

Avoid `short` for general arithmetic. The CPU promotes `short` to `int` for every arithmetic operation (integer promotion rules — see Section 8), so there is no performance advantage in arithmetic; you just get confusion:

```c
short a = 30000;
short b = 30000;
short c = a + b;   // WRONG: a+b = 60000, overflows short (-5536)
int   d = a + b;   // RIGHT: promotion happens anyway, capture in int
```

---

### 3.3 `int`

`int` is the "natural" integer type — the size that is most efficient for the CPU's native word. The C standard guarantees **at least 16 bits**, but on all 32-bit and 64-bit platforms today, `int` is **exactly 32 bits**.

#### Memory

```
+--------+--------+--------+--------+
|  byte0 |  byte1 |  byte2 |  byte3 |    4 bytes = 32 bits
+--------+--------+--------+--------+
```

#### Ranges

```
signed int:     -2,147,483,648   to   2,147,483,647   (approx ±2.1 billion)
unsigned int:            0       to   4,294,967,295   (approx 4.2 billion)
```

#### Why `int` Exists

The C standard was designed to let compilers choose the integer size most natural for the target CPU. On a 32-bit machine, 32-bit integers require no extra instructions to load or manipulate. On 64-bit machines, `int` is still 32 bits by convention (for ABI compatibility and because 32 bits is enough for most counts).

#### When to Use `int`

- **Loop counters** and **general-purpose integers** where you know the value fits in 32 bits.
- **Return values from functions** (e.g., `main` returns `int`).
- **Wherever you don't have a strong reason to use a more specific type** — `int` is the default workhorse.
- **Boolean flags** in old C code (before `_Bool`).

```c
// Canonical loop counter
for (int i = 0; i < 100; i++) { ... }

// General purpose
int result = compute_score();

// errno, function return codes
int fd = open("file.txt", O_RDONLY);
if (fd < 0) { perror("open"); }
```

---

### 3.4 `long`

`long` (full name: `long int`) is the most **platform-variable** of the standard types. The standard guarantees **at least 32 bits**, but:

```
Platform                     | sizeof(long)
-----------------------------|-------------
Windows (MSVC, MinGW)        | 4 bytes (32 bits)  ← always, even on 64-bit Windows
Linux/macOS 64-bit (GCC/Clang)| 8 bytes (64 bits) ← LP64 model
Linux/macOS 32-bit           | 4 bytes (32 bits)
Embedded (AVR, some ARM)     | 4 bytes (32 bits)
```

This is the **LP64 vs LLP64** distinction (see Section 13 for details).

#### Memory

```
On 32-bit or Windows:               On 64-bit Linux/macOS:
+--------+--------+--------+--------+    +--------+...8 bytes...+--------+
|  byte0 |  byte1 |  byte2 |  byte3 |    |  byte0 |             |  byte7 |
+--------+--------+--------+--------+    +--------+-------------+--------+
         4 bytes                                   8 bytes
```

#### Ranges

```
32-bit long (signed):   -2,147,483,648        to  2,147,483,647
64-bit long (signed):   -9,223,372,036,854,775,808  to  9,223,372,036,854,775,807
```

#### When to Use `long`

- **Avoid `long` for portable code** — its size is too platform-dependent.
- Use `long` when **interfacing with OS APIs** or POSIX functions that specify `long` (e.g., `lseek` returns `long`, `time_t` is often `long`).
- Use `int32_t` or `int64_t` instead for explicit sizes in portable code.

```c
// POSIX file offset — the API requires long
long offset = lseek(fd, 0, SEEK_END);

// Time since epoch — often typedef'd to long
time_t now = time(NULL);  // time_t is typically long on Linux

// DON'T do this for portable code expecting 64-bit:
long big_number = 9000000000L;  // Only works if long is 64-bit!
// DO this instead:
int64_t big_number = 9000000000LL;  // Explicitly 64-bit everywhere
```

---

### 3.5 `long long`

`long long` was added in **C99** and is guaranteed to be **at least 64 bits** on every platform. On all modern platforms it is exactly 64 bits.

#### Memory

```
+--------+--------+--------+--------+--------+--------+--------+--------+
|  byte0 |  byte1 |  byte2 |  byte3 |  byte4 |  byte5 |  byte6 |  byte7 |
+--------+--------+--------+--------+--------+--------+--------+--------+
                           8 bytes = 64 bits
```

#### Ranges

```
signed long long:    -9,223,372,036,854,775,808  to  9,223,372,036,854,775,807
                     (approximately ±9.2 quintillion)

unsigned long long:  0  to  18,446,744,073,709,551,615
                     (approximately 18.4 quintillion)
```

#### When to Use `long long`

- **File sizes, offsets** on large files (`off64_t`, size in bytes of a file > 4 GB).
- **Timestamps** in microseconds or nanoseconds.
- **64-bit IDs** (database row IDs, UUIDs as integer pairs).
- **Cryptographic intermediate values**.
- **When you explicitly need 64 bits and care about the exact range**.

```c
// File size that could be > 4 GB
long long file_size = 5368709120LL;   // 5 GB

// High-resolution timer
long long start = clock();   // or use struct timespec

// Large counter
unsigned long long packet_count = 0;
```

> **Prefer `int64_t`/`uint64_t` over `long long`** in new code. They express intent explicitly, guarantee the exact width, and avoid confusion with `long` on different platforms.

---

## 4. Sign Modifiers: `signed` and `unsigned`

Every integer type comes in two **signedness** flavors.

### How Signedness Changes Interpretation

The **bits in memory do not change** when you change signedness. What changes is how the compiler **interprets** those bits.

```
Bit pattern: 1111 1111 1111 1111 1111 1111 1111 1111  (32 bits, all ones)

Interpreted as signed int:      -1
Interpreted as unsigned int:    4,294,967,295

Same bits. Completely different meaning.
```

### Two's Complement Representation

C since C20 mandates two's complement (it was implementation-defined before, but universally used in practice).

```
For an N-bit signed integer:
  - The most significant bit (MSB) is the sign bit.
  - If MSB = 0: value = unsigned interpretation of bits.
  - If MSB = 1: value = unsigned interpretation - 2^N.

8-bit examples:
Bits        Unsigned    Signed
0000 0000      0           0
0000 0001      1           1
0111 1111     127         127
1000 0000     128        -128   ← MSB set, subtract 256
1111 1111     255          -1   ← 255 - 256 = -1
```

### The Key Differences Between `signed` and `unsigned`

```
+---------------------------+----------------------------+-----------------------------+
| Property                  | signed                     | unsigned                    |
+---------------------------+----------------------------+-----------------------------+
| Negative values           | YES                        | NO                          |
| Range (N bits)            | -(2^(N-1)) to 2^(N-1)-1   | 0 to 2^N - 1               |
| Overflow behavior         | UNDEFINED BEHAVIOR          | wraps modulo 2^N (defined)  |
| Right shift (>>)          | arithmetic (sign-extended) | logical (zero-filled)       |
| Comparison with negatives | works correctly            | negative cast to huge uint  |
| Bit operations            | implementation-defined     | well-defined                |
+---------------------------+----------------------------+-----------------------------+
```

### The Signed-Unsigned Comparison Bug

This is one of the most common C bugs:

```c
int length = -1;
unsigned int size = 10;

if (length < size) {        // You'd expect this to be true
    printf("length is smaller\n");
} else {
    printf("this runs instead!\n");  // <-- THIS RUNS
}
```

**Why?** When you compare `signed` and `unsigned`, the signed value is **implicitly converted to unsigned**. `-1` as `unsigned int` is `4,294,967,295` — larger than `10`.

```
Conversion rule:
-1 (signed int)  →  UINT_MAX (unsigned int)
                     (all bits set, two's complement wraps)
```

**Fix:** Either use all-signed comparisons, or cast explicitly:

```c
if (length < (int)size) {    // explicit cast to signed
    printf("length is smaller\n");  // now works correctly
}
```

---

## 5. Fixed-Width Integer Types (`<stdint.h>`)

Introduced in **C99**, `<stdint.h>` defines types with **guaranteed exact widths**. This is the correct solution to the portability problem created by platform-variable standard types.

### The Type Families

```
<stdint.h> provides three families:

1. EXACT-WIDTH:    intN_t / uintN_t     (exactly N bits, required if the platform supports it)
2. MINIMUM-WIDTH:  int_leastN_t / ...   (at least N bits, smallest such type)
3. FASTEST:        int_fastN_t  / ...   (at least N bits, fastest for arithmetic)
```

### Exact-Width Types

```
+-------------+--------------+----------------------------------------------+
| Type        | Width        | Signed Range / Unsigned Range                |
+-------------+--------------+----------------------------------------------+
| int8_t      | exactly 8b   | -128 to 127                                  |
| uint8_t     | exactly 8b   | 0 to 255                                     |
| int16_t     | exactly 16b  | -32,768 to 32,767                            |
| uint16_t    | exactly 16b  | 0 to 65,535                                  |
| int32_t     | exactly 32b  | -2,147,483,648 to 2,147,483,647              |
| uint32_t    | exactly 32b  | 0 to 4,294,967,295                           |
| int64_t     | exactly 64b  | -9,223,372,036,854,775,808 to +9,223,...     |
| uint64_t    | exactly 64b  | 0 to 18,446,744,073,709,551,615              |
+-------------+--------------+----------------------------------------------+
```

> **Note:** `intN_t` types are optional — a platform with no 16-bit type need not provide `int16_t`. In practice, all modern systems (x86, ARM, RISC-V, MIPS) provide all four widths.

### Minimum-Width Types (`int_leastN_t`)

Use these when you need *at least* N bits but want the smallest such type:

```c
// You need at least 16 bits. int_least16_t gives you the
// smallest type that is >= 16 bits on the current platform.
int_least16_t val;

// On most systems:     int_least16_t = int16_t (16 bits)
// On some DSPs:        int_least16_t = int32_t (if 16-bit not native)
```

### Fastest Types (`int_fastN_t`)

Use these when you need at least N bits but want **maximum performance**:

```c
// int_fast16_t is the fastest type that is >= 16 bits.
// On 32-bit/64-bit CPUs, this is often int32_t or int64_t
// because the CPU operates fastest on its native word size.
int_fast16_t counter;
```

```
Typical mappings on x86-64 Linux:
  int_fast8_t   = int64_t  (64-bit is native word)
  int_fast16_t  = int64_t
  int_fast32_t  = int64_t
  int_fast64_t  = int64_t
```

### Constants for stdint.h Ranges

`<stdint.h>` also defines macros for min/max values:

```c
INT8_MIN      // -128
INT8_MAX      // 127
UINT8_MAX     // 255
INT16_MIN     // -32768
INT16_MAX     // 32767
UINT16_MAX    // 65535
INT32_MIN     // -2147483648
INT32_MAX     // 2147483647
UINT32_MAX    // 4294967295
INT64_MIN     // -9223372036854775808
INT64_MAX     // 9223372036854775807
UINT64_MAX    // 18446744073709551615
```

Always use these constants instead of magic numbers:

```c
// BAD: magic number, wrong on platforms where int is 16-bit
if (x > 32767) { overflow(); }

// GOOD: portable, self-documenting
if (x > INT16_MAX) { overflow(); }
```

### Literals for stdint.h Types

Use the helper macros from `<stdint.h>` to create properly-typed literals:

```c
#include <stdint.h>
#include <inttypes.h>  // for PRId32, PRIu64, etc.

int32_t a = INT32_C(1000000);      // literal with int32_t type
uint64_t b = UINT64_C(18000000000); // literal with uint64_t type
```

---

## 6. Specialty Types

### 6.1 `size_t`

#### What it is

`size_t` is an **unsigned integer type** defined in `<stddef.h>` (also `<stdlib.h>`, `<string.h>`). It is the type returned by `sizeof` and used by memory/array functions. It is guaranteed to be large enough to represent the size of any object in memory.

#### Size

```
On 32-bit systems:   size_t = 4 bytes  (uint32_t equivalent)
On 64-bit systems:   size_t = 8 bytes  (uint64_t equivalent)
```

Conceptually:

```
size_t width matches the pointer width:

64-bit process:
  Pointer:  [64 bits] -> can address 2^64 bytes
  size_t:   [64 bits] -> can represent sizes up to 2^64 - 1 bytes

32-bit process:
  Pointer:  [32 bits] -> can address 2^32 bytes (4 GB)
  size_t:   [32 bits] -> can represent sizes up to 4 GB - 1
```

#### When to Use `size_t`

- **Array indices and loop counters** when iterating over arrays (ensures you can address any element).
- **`malloc`, `calloc`, `realloc` arguments** — they take `size_t`.
- **Return values from `strlen`, `fread`, `fwrite`** — they return `size_t`.
- **Any variable that holds "how big is this object"**.

```c
// Correct: malloc takes size_t
void *buf = malloc(sizeof(int) * 1000);

// Correct: strlen returns size_t
size_t len = strlen("hello");

// Correct loop — i can reach any valid index
for (size_t i = 0; i < len; i++) { ... }
```

#### The `size_t` Underflow Trap

Because `size_t` is **unsigned**, subtracting past zero wraps:

```c
size_t len = strlen(s);
for (size_t i = len - 1; i >= 0; i--) {  // BUG! When i==0, i-- wraps to SIZE_MAX
    process(s[i]);
    // infinite loop!
}

// Fix: use a different loop structure or cast to signed
for (size_t i = len; i-- > 0; ) {   // safe: checks before decrement
    process(s[i]);
}
```

### 6.2 `ptrdiff_t`

`ptrdiff_t` is a **signed** integer type defined in `<stddef.h>`. It is the type of the result when you subtract two pointers.

```c
int arr[10];
int *p = &arr[3];
int *q = &arr[7];
ptrdiff_t diff = q - p;   // diff == 4 (q is 4 elements ahead of p)
```

#### Size

Same as `size_t` in bit width, but signed:

```
64-bit: ptrdiff_t is 8 bytes signed (can hold -(2^63) to 2^63-1)
32-bit: ptrdiff_t is 4 bytes signed (can hold -(2^31) to 2^31-1)
```

#### When to Use `ptrdiff_t`

- **Result of pointer arithmetic** — this is its primary purpose.
- **Signed offset into an array** where you need to express "go backwards".

```c
ptrdiff_t offset = end_ptr - start_ptr;
if (offset < 0) {
    printf("end is before start!\n");
}
```

### 6.3 `intptr_t` / `uintptr_t`

These types are **integer types large enough to hold any pointer**. Defined in `<stdint.h>`.

```
intptr_t:  signed integer, same size as a pointer
uintptr_t: unsigned integer, same size as a pointer
```

#### When to Use

- **Storing a pointer as an integer** for hashing, tagging, or low-level manipulation.
- **Bit manipulation of pointer values** (e.g., tagged pointers — storing flags in the low bits of a pointer).
- **Interfacing with low-level hardware or OS** where addresses are treated as integers.

```c
// Pointer to integer (to examine the bits)
void *ptr = malloc(64);
uintptr_t addr = (uintptr_t)ptr;
printf("Pointer address: 0x%lx\n", (unsigned long)addr);
printf("Alignment (mod 8): %lu\n", (unsigned long)(addr % 8));

// Tagged pointer: use low bit as a flag (only if alignment guarantees bit is always 0)
uintptr_t tagged = addr | 1;   // set bit 0 as a "marked" flag
uintptr_t clean  = tagged & ~(uintptr_t)1;  // recover original pointer
void *recovered  = (void*)clean;
```

> **Warning:** Do NOT use `int`, `long`, or `unsigned long` to store pointers — they may be the wrong size. On Windows 64-bit, `long` is 32 bits but pointers are 64 bits. `uintptr_t` is always correct.

### 6.4 `intmax_t` / `uintmax_t`

The **widest integer types** supported by the implementation. Defined in `<stdint.h>`.

```
On most modern 64-bit systems:
  intmax_t  = int64_t   (64 bits signed)
  uintmax_t = uint64_t  (64 bits unsigned)

On systems with 128-bit integer support (__int128 on GCC/Clang):
  intmax_t  may be 128 bits
```

#### When to Use

- **Generic code** that must work with any integer value without knowing its type.
- **Printf/scanf with `%jd`/`%ju`** format specifiers.
- **Intermediate calculations** where you need to accumulate into the widest possible type.

```c
#include <stdint.h>
#include <inttypes.h>  // PRIdMAX, PRIuMAX

intmax_t big = INTMAX_MAX;
printf("Max integer: %" PRIdMAX "\n", big);

// Generic accumulator
intmax_t sum = 0;
for (int i = 0; i < n; i++) {
    sum += (intmax_t)values[i];  // no overflow in accumulator
}
```

### 6.5 `_Bool` / `bool`

Introduced in **C99**. `_Bool` is a built-in type; `bool` is a macro defined in `<stdbool.h>`.

#### What it is

`_Bool` can hold only two values: **0** (false) and **1** (true). Any non-zero value assigned to `_Bool` is stored as 1.

```c
_Bool flag = 5;   // stored as 1 (not 5!)
_Bool off  = 0;   // stored as 0
```

#### Size

```
sizeof(_Bool) == 1  (1 byte on virtually all implementations, though standard allows more)
```

#### `<stdbool.h>` Macros

```c
#include <stdbool.h>

bool   // alias for _Bool
true   // expands to 1
false  // expands to 0
```

#### When to Use

- **Flag variables**: `bool found = false;`
- **Function return type** indicating success/failure: `bool is_valid(...)`
- **Bit fields** of width 1: `unsigned int flag : 1;`
- **Any time you need a true/false variable** — prefer `bool` over `int` for semantic clarity.

```c
#include <stdbool.h>

bool is_prime(int n) {
    if (n < 2) return false;
    for (int i = 2; i * i <= n; i++) {
        if (n % i == 0) return false;
    }
    return true;
}

bool found = false;
for (size_t i = 0; i < count; i++) {
    if (arr[i] == target) {
        found = true;
        break;
    }
}
```

---

## 7. Integer Representation: Two's Complement Deep Dive

### Why Two's Complement?

C historically allowed three representations: sign-magnitude, one's complement, and two's complement. C20 mandates two's complement. Here's why it won:

```
Sign-Magnitude (historical):
  +5 = 0000 0101
  -5 = 1000 0101  (just flip the sign bit)
  Problem: Two representations of zero (+0 and -0)
  Problem: Addition requires special-case logic

One's Complement:
  +5 = 0000 0101
  -5 = 1111 1010  (flip all bits)
  Problem: Still two zeros (0000 0000 and 1111 1111)
  Problem: Addition "end-around carry" complication

Two's Complement:
  +5 = 0000 0101
  -5 = 1111 1011  (flip all bits, add 1)
  Advantage: Single zero
  Advantage: Addition is identical for signed and unsigned — CPU uses same hardware!
```

### Two's Complement Arithmetic

```
How to compute -N in two's complement:
  1. Write N in binary
  2. Flip all bits (one's complement)
  3. Add 1

Example: -5 in 8-bit two's complement
  +5  = 0000 0101
  flip= 1111 1010   (one's complement)
  +1  = 1111 1011   (two's complement = -5)

Verification: +5 + (-5) should = 0
  0000 0101
+ 1111 1011
-----------
 10000 0000  <- the carry-out is discarded in 8-bit
=  0000 0000  ✓ correct!
```

### The Asymmetry of Signed Ranges

Notice that `INT8_MIN = -128` but `INT8_MAX = 127`. There is one more negative than positive:

```
8-bit two's complement number line:
-128  -127  ...  -1   0   1   ...  127
 |<-- 128 negative values -->|<-- 128 non-negative values (including 0) -->|

This is because 0 takes one slot from the positive side.
Total: 256 values = 2^8, as expected.

The "extra" negative: -128 = 1000 0000
  -(-128) would need 0001 ... 1000 + 1 = 1000 0000 = -128 again!
  abs(INT8_MIN) cannot be represented as INT8_MAX + 1.
  This is why  -INT_MIN  is UNDEFINED BEHAVIOR in C.
```

### Bit Shifting and Signedness

```
Left shift (<<):
  Both signed and unsigned: multiply by 2 per shift (if no overflow)
  5 << 1 = 10,   5 << 2 = 20

Right shift (>>):
  Unsigned: LOGICAL shift — always fills with 0s from the left
    0b10110000 >> 2 = 0b00101100

  Signed: ARITHMETIC shift (implementation-defined, but universal in practice)
    — fills with the sign bit from the left (sign extension)
    0b10110000 (= -80 in signed 8-bit) >> 2 = 0b11101100 (= -20)
```

---

## 8. Integer Promotions and Arithmetic Conversions

This section explains one of the most counterintuitive parts of C — what happens to types during arithmetic.

### Integer Promotion

Before arithmetic, **small types are promoted to `int`** (or `unsigned int` if `int` can't hold the value):

```
char, signed char, unsigned char, short, unsigned short
  --> if all values fit in int:        promoted to int
  --> if some values don't fit in int: promoted to unsigned int

This happens automatically in expressions.
```

```c
char a = 100, b = 200;
// a + b:  both promoted to int first
// int(100) + int(200) = 300 (no overflow, even though 300 > CHAR_MAX)
int result = a + b;   // 300 — correct!

// But:
char c = a + b;   // 300 gets truncated back to char: 300 % 256 = 44 (on typical system)
```

### Usual Arithmetic Conversions

When two operands have **different types**, C applies these rules in order:

```
Conversion hierarchy (higher rank wins):

  long double
      |
  double
      |
  float
      |
  unsigned long long    <-- or: long long, depending on which can represent all values
      |
  long long
      |
  unsigned long
      |
  long
      |
  unsigned int
      |
  int    <-- all smaller types promoted here first
```

The operand with the **lower rank** is converted to the type of the **higher rank** before the operation.

```c
int i = -1;
unsigned int u = 1;
long long ll = i + u;  // i is converted to unsigned int: (unsigned int)(-1) = UINT_MAX
                        // UINT_MAX + 1 = 0 (wraps). ll = 0, NOT -1+1=0 for the wrong reason!

// This is the signed/unsigned mixing bug from Section 4, now with arithmetic.
```

Visual representation of the promotion flow:

```
Expression:   short a  +  int b
              ^             ^
              |             |
        promoted to int     already int
              |             |
              +------+------+
                     |
                   int + int  -->  result is int
```

```
Expression:   int a  +  unsigned int b
              ^                ^
              |                |
         converted to        stays
         unsigned int       unsigned int
              |                |
              +------+---------+
                     |
               unsigned int + unsigned int --> result is unsigned int
```

### Practical Implications

```c
// Trap 1: mixing int and unsigned in comparison
int x = -1;
unsigned y = 1;
if (x < y)   // FALSE! x promoted to unsigned: (unsigned)-1 = UINT_MAX > 1

// Trap 2: integer division
int a = 7, b = 2;
double r = a / b;  // r = 3.0 (NOT 3.5!) — division done in int, THEN converted to double

// Fix for trap 2:
double r2 = (double)a / b;   // cast before division: 7.0 / 2 = 3.5

// Trap 3: shift of small type
char c = 0xFF;
int shifted = c << 8;  // First c is promoted to int (-1 on signed-char systems)
                        // Then -1 << 8 = -256 (implementation-defined!)
unsigned char uc = 0xFF;
int shifted2 = uc << 8;  // uc promoted to int(255), then 255 << 8 = 65280 ✓
```

---

## 9. Overflow, Underflow, and Undefined Behavior

### Signed Overflow = Undefined Behavior

This is one of the most dangerous aspects of C. **Signed integer overflow is explicitly undefined behavior (UB)** in the C standard. The compiler is allowed to assume it never happens — and modern optimizers exploit this assumption aggressively.

```c
int x = INT_MAX;
x = x + 1;   // UNDEFINED BEHAVIOR — NOT necessarily -2147483648!
```

Real consequences of signed overflow UB:

```c
// Compiler sees: if (x + 1 > x) is always true (signed integers never overflow, by definition)
// So it REMOVES the overflow check entirely:

int foo(int x) {
    if (x + 1 > x) return 1;  // Compiler optimizes this away entirely!
    return 0;                  // Dead code after optimization
}

// With -O2, GCC compiles this to: return 1; — always.
```

This is not a bug in the compiler — it is a correct optimization given the C standard.

### Unsigned Overflow = Well-Defined Wrapping

**Unsigned overflow wraps modulo 2^N** — this is guaranteed:

```c
uint8_t x = 255;
x = x + 1;   // x = 0 — defined, wraps mod 256

uint32_t y = UINT32_MAX;
y = y + 1;   // y = 0 — defined, wraps mod 2^32
```

### Safe Overflow Checking

```c
// Check for signed addition overflow BEFORE it happens:
bool safe_add(int a, int b, int *result) {
    if (b > 0 && a > INT_MAX - b) return false;  // would overflow positive
    if (b < 0 && a < INT_MIN - b) return false;  // would underflow negative
    *result = a + b;
    return true;
}

// GCC/Clang built-in for overflow detection (efficient):
int result;
if (__builtin_add_overflow(a, b, &result)) {
    // overflow occurred
}
// Also: __builtin_sub_overflow, __builtin_mul_overflow

// C23 provides: <stdckdint.h>
// ckd_add(&result, a, b)  — returns true on overflow
```

### Integer Truncation

When assigning a larger integer to a smaller type, the high bits are silently discarded:

```c
int x = 300;
char c = x;    // 300 = 0x12C, truncated to 0x2C = 44
               // Information LOST silently — no warning by default in C!

uint16_t port = 70000;   // 70000 > 65535, truncated!
                          // 70000 % 65536 = 4464 — wrong port!
```

---

## 10. Literals, Suffixes, and Constants

### Integer Literal Bases

```c
int dec = 42;       // decimal (base 10)
int hex = 0x2A;     // hexadecimal (base 16) — same value as 42
int oct = 052;      // octal (base 8)         — same value as 42
int bin = 0b101010; // binary (GCC extension, standard in C23)
```

> **Octal trap:** A leading zero makes a literal **octal**. `010 == 8`, NOT 10!

### Type Suffixes for Literals

Without a suffix, the literal has the smallest type that can represent it:

```c
42          // int
42L         // long
42LL        // long long
42U         // unsigned int
42UL        // unsigned long
42ULL       // unsigned long long
```

```
Suffix combinations:
  (none)  -> int (if it fits), then long, then long long
  U/u     -> unsigned int, then unsigned long, then unsigned long long
  L/l     -> long (if it fits), then long long
  UL/ul   -> unsigned long, then unsigned long long
  LL/ll   -> long long
  ULL/ull -> unsigned long long
```

### Common Mistake: Unsuffixed Large Literals

```c
// On 32-bit int systems, 2147483648 doesn't fit in int:
long x = 2147483648;    // The literal is long long, then assigned to long — OK
int y  = 2147483648;    // Literal is long long (2^31), truncated to int: -2147483648 (UB!)

// Always suffix large literals:
int64_t z = 9000000000LL;   // correct
int64_t w = 9000000000;     // without LL: integer constant overflow if int is 32 bits!
```

---

## 11. Format Specifiers for printf/scanf

Using the **wrong format specifier** is undefined behavior and causes bugs:

```c
printf("%d", x);   // OK if x is int
printf("%d", x);   // UB if x is long long! (too few bytes popped from stack)
```

### Complete Format Specifier Reference

```
+---------------+----------+-----------------------------+--------------------+
| Type          | printf   | scanf                       | Notes              |
+---------------+----------+-----------------------------+--------------------+
| char          | %c       | %c                          | character          |
| signed char   | %hhd     | %hhd                        | h = short, hh=char |
| unsigned char | %hhu     | %hhu                        |                    |
| short         | %hd      | %hd                         |                    |
| unsigned short| %hu      | %hu                         |                    |
| int           | %d or %i | %d or %i                    | default            |
| unsigned int  | %u       | %u                          |                    |
| long          | %ld      | %ld                         |                    |
| unsigned long | %lu      | %lu                         |                    |
| long long     | %lld     | %lld                        |                    |
| unsigned ll   | %llu     | %llu                        |                    |
| size_t        | %zu      | %zu                         | z modifier         |
| ptrdiff_t     | %td      | %td                         | t modifier         |
| intmax_t      | %jd      | %jd                         | j modifier         |
| uintmax_t     | %ju      | %ju                         |                    |
| void*         | %p       | %p                          | pointer            |
+---------------+----------+-----------------------------+--------------------+
```

### Using `<inttypes.h>` for Fixed-Width Types

`<inttypes.h>` provides portable macros that expand to the correct format string:

```c
#include <stdint.h>
#include <inttypes.h>

int32_t  a = 1000;
uint64_t b = 18446744073709551615ULL;

printf("a = %" PRId32 "\n", a);    // PRId32 expands to "d" or "ld" as needed
printf("b = %" PRIu64 "\n", b);    // PRIu64 expands to "lu" or "llu" as needed

// scanf equivalents:
scanf("%" SCNd32, &a);
scanf("%" SCNu64, &b);
```

Macro naming pattern:

```
PRI  = printf
SCN  = scanf
d    = signed decimal
u    = unsigned decimal
x    = hexadecimal
o    = octal
i    = signed (alternative)
N    = bit width (8, 16, 32, 64)
LEAST= for int_leastN_t
FAST = for int_fastN_t
MAX  = for intmax_t

Examples:
  PRId32     -> printf signed 32-bit decimal
  PRIu64     -> printf unsigned 64-bit decimal
  PRIx16     -> printf 16-bit hexadecimal
  SCNd32     -> scanf signed 32-bit decimal
  PRIdLEAST8 -> printf signed least-8-bit decimal
  PRIdFAST32 -> printf signed fast-32-bit decimal
  PRIdMAX    -> printf intmax_t decimal
```

---

## 12. Choosing the Right Type: Decision Framework

Use this flowchart to choose the correct integer type for any situation:

```
START
  |
  v
Is this for a string / text?
  YES --> use char (or unsigned char for raw bytes)
  NO  --> continue
  |
  v
Do you need an exact bit width? (binary protocols, hardware, file formats)
  YES --> use int8_t / uint8_t / int16_t / uint16_t / int32_t / uint32_t / int64_t / uint64_t
  NO  --> continue
  |
  v
Is this for sizeof() result, array index, or memory size?
  YES --> use size_t
  NO  --> continue
  |
  v
Is this for pointer arithmetic (difference between two pointers)?
  YES --> use ptrdiff_t
  NO  --> continue
  |
  v
Do you need to store a pointer as an integer?
  YES --> use uintptr_t (unsigned) or intptr_t (signed)
  NO  --> continue
  |
  v
Is this a boolean / flag?
  YES --> use bool (from <stdbool.h>)
  NO  --> continue
  |
  v
Is this a general-purpose counter / index that fits in 32 bits?
  YES --> use int (signed) or unsigned int
  NO  --> continue
  |
  v
Do you need more than 32 bits?
  YES --> use int64_t / uint64_t  (preferred over long long for clarity)
  NO  --> use int
```

### Quick Cheat Sheet by Use Case

```
Use Case                          | Recommended Type
----------------------------------|------------------
Loop counter (small array)        | int or size_t
Loop counter (large array)        | size_t
Array index                       | size_t
malloc/sizeof argument            | size_t
String length (strlen result)     | size_t
Text character                    | char
Raw byte / binary buffer          | unsigned char or uint8_t
Network byte (1 byte field)       | uint8_t
Network word (2 byte field)       | uint16_t (+ htons/ntohs)
Network dword (4 byte field)      | uint32_t (+ htonl/ntohl)
File offset (large files)         | off_t or int64_t
Timestamp (seconds)               | time_t (usually int64_t)
Timestamp (microseconds)          | int64_t
Hash value                        | uint32_t or uint64_t
Boolean flag                      | bool
Enum values (small set)           | int or enum
Hardware register (8-bit)         | uint8_t
Hardware register (16-bit)        | uint16_t
Hardware register (32-bit)        | uint32_t
Pixel value (8-bit color)         | uint8_t
Audio sample (16-bit)             | int16_t
Atomic counter (overflow safe)    | uint32_t or uint64_t (depends on range)
Database row ID                   | int64_t
UUID component                    | uint64_t
Pointer-sized integer             | uintptr_t
Signed pointer-sized integer      | intptr_t
Maximum precision integer         | intmax_t / uintmax_t
```

---

## 13. Platform Portability and the ABI

### Data Models

Different platforms use different "data models" — conventions for how wide each standard type is:

```
+----------+------+-------+------+------+-----------+------------------+
| Model    | char | short | int  | long | long long | Pointer          |
+----------+------+-------+------+------+-----------+------------------+
| LP32     |  8   |  16   |  16  |  32  |    64     | 32-bit           |
| ILP32    |  8   |  16   |  32  |  32  |    64     | 32-bit (common 32)|
| LP64     |  8   |  16   |  32  |  64  |    64     | 64-bit (Linux/Mac)|
| LLP64    |  8   |  16   |  32  |  32  |    64     | 64-bit (Windows) |
| ILP64    |  8   |  16   |  64  |  64  |    64     | 64-bit (rare)    |
+----------+------+-------+------+------+-----------+------------------+
                                    ^
                                    |
                   This column is where LP64 vs LLP64 differ!
                   Linux/macOS: long = 64 bits
                   Windows:     long = 32 bits  <-- gotcha for cross-platform code!
```

### The Portability Problem This Creates

```c
// This code works on Linux 64-bit but NOT on Windows 64-bit:
long big = 5000000000L;    // Linux: long is 64-bit, OK
                            // Windows: long is 32-bit, overflow!

// Portable fix:
int64_t big = 5000000000LL;  // Always correct on both platforms
```

### Checking Type Sizes at Runtime

```c
#include <stdio.h>

int main(void) {
    printf("char:        %zu bytes\n", sizeof(char));
    printf("short:       %zu bytes\n", sizeof(short));
    printf("int:         %zu bytes\n", sizeof(int));
    printf("long:        %zu bytes\n", sizeof(long));
    printf("long long:   %zu bytes\n", sizeof(long long));
    printf("size_t:      %zu bytes\n", sizeof(size_t));
    printf("ptrdiff_t:   %zu bytes\n", sizeof(ptrdiff_t));
    printf("void*:       %zu bytes\n", sizeof(void*));
    printf("int64_t:     %zu bytes\n", sizeof(int64_t));
    return 0;
}
```

### Static Assertions for Portability

Use `_Static_assert` (C11) to catch size mismatches at compile time:

```c
#include <stdint.h>

_Static_assert(sizeof(int)      == 4, "int must be 4 bytes");
_Static_assert(sizeof(long)     == 8, "long must be 8 bytes (LP64 expected)");
_Static_assert(sizeof(size_t)   == 8, "size_t must be 8 bytes (64-bit expected)");
_Static_assert(sizeof(uint32_t) == 4, "uint32_t must be 4 bytes");

// In C11+:
#include <assert.h>
static_assert(sizeof(void*) == 8, "Need 64-bit pointers");
```

---

## 14. Common Pitfalls and Security Implications

### Pitfall 1: Integer Overflow in Security-Critical Code

```c
// Classic buffer overflow via integer overflow:
size_t count = user_input;
size_t total = count * sizeof(int);  // If count is large, this overflows!
int *buf = malloc(total);            // malloc gets a tiny number, allocates tiny buffer
memcpy(buf, src, count * sizeof(int));  // HEAP OVERFLOW

// Fix: check for overflow first
if (count > SIZE_MAX / sizeof(int)) {
    return ERROR_OVERFLOW;
}
size_t total = count * sizeof(int);  // safe
```

### Pitfall 2: Signed/Unsigned Length Checks

```c
// Classic C security bug:
int len = get_user_input();  // attacker provides -1

if (len < MAX_LEN) {         // -1 < MAX_LEN is TRUE
    char buf[MAX_LEN];
    read(fd, buf, len);      // read() takes size_t, len=-1 becomes SIZE_MAX!
                              // reads gigabytes into tiny buffer
}

// Fix: validate that len is non-negative BEFORE using it as a size
if (len < 0 || len >= MAX_LEN) { return ERROR; }
char buf[MAX_LEN];
read(fd, buf, (size_t)len);  // safe now
```

### Pitfall 3: `char` Signedness in Character Classification

```c
// Classic bug: char is signed, EOF is -1, but some chars > 127
int c = getchar();              // correct: use int to hold EOF
while (c != EOF) {
    if (isalpha(c)) { ... }    // correct: isalpha takes int
    c = getchar();
}

// WRONG version:
char c = getchar();             // if char is signed, 0x80-0xFF stored as negative
while (c != EOF) {
    if (isalpha((unsigned char)c)) { ... }  // must cast to avoid UB in ctype.h!
    c = getchar();
}
// isalpha((char)0xFF) on a signed-char system passes -1 to isalpha!
// isalpha only defined for values 0..UCHAR_MAX and EOF.
// Passing negative values is UB!
```

### Pitfall 4: The `strlen` Return Type Surprise

```c
// strlen returns size_t (unsigned!)
size_t len = strlen(s);

// This underflows:
if (strlen(s) - 1 >= 0) { ... }  // always TRUE! (size_t - 1 when len=0 = SIZE_MAX)

// Safe version:
if (strlen(s) > 0) { ... }       // correct
```

### Pitfall 5: Bitwise Operations on Signed Integers

```c
// Right shift of negative signed: implementation-defined before C20
int x = -1;
int y = x >> 1;   // Implementation-defined! (but arithmetic shift in practice)

// Bitwise NOT of signed integer:
int flags = ~0;   // All bits set: -1 (signed), not an unsigned mask!
unsigned int mask = ~0u;  // Correct: all bits set in unsigned

// Bit manipulation: always use unsigned types
uint32_t flags = 0;
flags |= (1u << 31);    // correct: 1u is unsigned, prevents UB
flags |= (1  << 31);    // UB! left-shifting into sign bit of signed int
```

### Pitfall 6: `printf` Format Mismatch

```c
int64_t x = 1000000000000LL;
printf("%d\n", x);    // UB! %d expects int (4 bytes), x is 8 bytes
                       // prints garbage or partial value

printf("%lld\n", x);  // correct on most systems
printf("%" PRId64 "\n", x);  // always correct, portable
```

---

## 15. Practical Code Patterns

### Pattern 1: Safe Integer Casting with Range Check

```c
#include <stdint.h>
#include <limits.h>
#include <stdbool.h>

// Safely cast int64_t to int32_t, returns false if out of range
bool safe_cast_i64_to_i32(int64_t in, int32_t *out) {
    if (in < INT32_MIN || in > INT32_MAX) return false;
    *out = (int32_t)in;
    return true;
}

// Safely convert signed to unsigned
bool safe_to_uint32(int64_t in, uint32_t *out) {
    if (in < 0 || in > UINT32_MAX) return false;
    *out = (uint32_t)in;
    return true;
}
```

### Pattern 2: Portable Byte Extraction

```c
#include <stdint.h>

// Extract nth byte from a uint32_t (0 = least significant)
uint8_t get_byte(uint32_t value, int n) {
    return (uint8_t)((value >> (n * 8)) & 0xFF);
}

// Build uint32_t from 4 bytes (little-endian)
uint32_t from_bytes_le(uint8_t b0, uint8_t b1, uint8_t b2, uint8_t b3) {
    return (uint32_t)b0
         | ((uint32_t)b1 << 8)
         | ((uint32_t)b2 << 16)
         | ((uint32_t)b3 << 24);
}

// Build uint32_t from 4 bytes (big-endian / network order)
uint32_t from_bytes_be(uint8_t b0, uint8_t b1, uint8_t b2, uint8_t b3) {
    return ((uint32_t)b0 << 24)
         | ((uint32_t)b1 << 16)
         | ((uint32_t)b2 << 8)
         |  (uint32_t)b3;
}
```

### Pattern 3: Bitmask Operations

```c
#include <stdint.h>

// Set bit N
#define BIT_SET(val, n)    ((val) |=  (1u << (n)))

// Clear bit N
#define BIT_CLEAR(val, n)  ((val) &= ~(1u << (n)))

// Toggle bit N
#define BIT_TOGGLE(val, n) ((val) ^=  (1u << (n)))

// Test bit N
#define BIT_TEST(val, n)   (!!((val) &  (1u << (n))))

// Create a mask of N bits starting at position P
#define MASK(n, p) (((1u << (n)) - 1u) << (p))

// Extract N bits starting at position P
#define EXTRACT(val, n, p) (((val) >> (p)) & ((1u << (n)) - 1u))

// Usage:
uint32_t flags = 0;
BIT_SET(flags, 3);             // Set bit 3:    0b00001000
BIT_SET(flags, 7);             // Set bit 7:    0b10001000
BIT_CLEAR(flags, 3);           // Clear bit 3:  0b10000000
bool is_set = BIT_TEST(flags, 7);  // true

uint32_t reg = 0xABCD1234;
uint8_t nibble = EXTRACT(reg, 4, 8);  // Extract bits [11:8] = 0x2
```

### Pattern 4: Integer to String and Back

```c
#include <stdint.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>

// Integer to decimal string
char buf[32];
int32_t val = -1234567;
snprintf(buf, sizeof(buf), "%" PRId32, val);

// String to integer (safe, with error checking)
char *end;
long long result = strtoll(input_str, &end, 10);
if (end == input_str) {
    // no digits found
}
if (*end != '\0') {
    // trailing non-numeric characters
}
if (result > INT32_MAX || result < INT32_MIN) {
    // out of range for int32_t
}
int32_t safe_val = (int32_t)result;
```

### Pattern 5: Saturating Arithmetic (No Overflow)

```c
#include <stdint.h>

// Add two uint32_t values, clamping at UINT32_MAX (saturating addition)
uint32_t sat_add_u32(uint32_t a, uint32_t b) {
    return (a > UINT32_MAX - b) ? UINT32_MAX : a + b;
}

// Signed saturating addition for int32_t
int32_t sat_add_i32(int32_t a, int32_t b) {
    int64_t result = (int64_t)a + b;
    if (result > INT32_MAX) return INT32_MAX;
    if (result < INT32_MIN) return INT32_MIN;
    return (int32_t)result;
}
```

### Pattern 6: Endianness Conversion

```c
#include <stdint.h>

// Swap bytes of a 16-bit value
uint16_t bswap16(uint16_t x) {
    return (uint16_t)((x << 8) | (x >> 8));
}

// Swap bytes of a 32-bit value
uint32_t bswap32(uint32_t x) {
    return ((x & 0xFF000000u) >> 24)
         | ((x & 0x00FF0000u) >> 8)
         | ((x & 0x0000FF00u) << 8)
         | ((x & 0x000000FFu) << 24);
}

// Portable network-to-host conversion (without relying on <arpa/inet.h>)
uint32_t ntoh32(uint32_t net) {
    uint8_t *b = (uint8_t*)&net;
    return ((uint32_t)b[0] << 24)
         | ((uint32_t)b[1] << 16)
         | ((uint32_t)b[2] << 8)
         |  (uint32_t)b[3];
}
```

---

## 16. Quick Reference Tables

### Standard Types Summary

```
+---------------+----------+------------+------------------------------+------------------------------+
| Type          | Min Bits | Typical    | Signed Range                 | Unsigned Range               |
+---------------+----------+------------+------------------------------+------------------------------+
| char          |    8     | 1 byte     | implementation-defined       | implementation-defined       |
| signed char   |    8     | 1 byte     | -128 to 127                  | N/A                          |
| unsigned char |    8     | 1 byte     | N/A                          | 0 to 255                     |
| short         |   16     | 2 bytes    | -32,768 to 32,767            | 0 to 65,535                  |
| int           |   16     | 4 bytes    | -2,147,483,648 to 2,147,483,647 | 0 to 4,294,967,295        |
| long          |   32     | 4 or 8 bytes| (depends on platform)       | (depends on platform)        |
| long long     |   64     | 8 bytes    | -9.22e18 to 9.22e18          | 0 to 18.44e18                |
+---------------+----------+------------+------------------------------+------------------------------+
```

### Fixed-Width Types Summary

```
+-----------+-------+------------------+------------------+
| Type      | Bits  | Min Value        | Max Value        |
+-----------+-------+------------------+------------------+
| int8_t    |   8   | -128             | 127              |
| uint8_t   |   8   | 0                | 255              |
| int16_t   |  16   | -32,768          | 32,767           |
| uint16_t  |  16   | 0                | 65,535           |
| int32_t   |  32   | -2,147,483,648   | 2,147,483,647    |
| uint32_t  |  32   | 0                | 4,294,967,295    |
| int64_t   |  64   | -9.22 * 10^18    | 9.22 * 10^18     |
| uint64_t  |  64   | 0                | 1.84 * 10^19     |
+-----------+-------+------------------+------------------+
```

### Specialty Types Summary

```
+-------------+----------+----------+----------------------------------------------------+
| Type        | Signed?  | Size     | Purpose                                            |
+-------------+----------+----------+----------------------------------------------------+
| size_t      | unsigned | ptr-size | sizeof result, array sizes, malloc arg             |
| ptrdiff_t   | signed   | ptr-size | result of pointer subtraction                      |
| intptr_t    | signed   | ptr-size | integer large enough to hold any pointer           |
| uintptr_t   | unsigned | ptr-size | unsigned integer large enough to hold any pointer  |
| intmax_t    | signed   | max-int  | widest integer the platform supports               |
| uintmax_t   | unsigned | max-int  | widest unsigned integer the platform supports      |
| bool/_Bool  | N/A      | 1 byte   | boolean (0 or 1)                                   |
+-------------+----------+----------+----------------------------------------------------+
```

### Format Specifier Quick Reference

```
+-------------------+----------+----------+
| Type              | printf   | scanf    |
+-------------------+----------+----------+
| int               | %d       | %d       |
| unsigned int      | %u       | %u       |
| long              | %ld      | %ld      |
| unsigned long     | %lu      | %lu      |
| long long         | %lld     | %lld     |
| unsigned long long| %llu     | %llu     |
| size_t            | %zu      | %zu      |
| ptrdiff_t         | %td      | %td      |
| intmax_t          | %jd      | %jd      |
| uintmax_t         | %ju      | %ju      |
| int8_t            | %"PRId8" |%"SCNd8"  |
| uint8_t           | %"PRIu8" |%"SCNu8"  |
| int32_t           |%"PRId32" |%"SCNd32" |
| uint64_t          |%"PRIu64" |%"SCNu64" |
| pointer (void*)   | %p       | %p       |
+-------------------+----------+----------+
```

### Header File Reference

```
+-------------------+-------------------------------------------------------------+
| Header            | Provides                                                    |
+-------------------+-------------------------------------------------------------+
| <stdint.h>        | intN_t, uintN_t, int_leastN_t, int_fastN_t, intptr_t,      |
|                   | uintptr_t, intmax_t, uintmax_t and their _MIN/_MAX macros   |
| <inttypes.h>      | PRId32, PRIu64, SCNd32 etc. format macros; includes stdint.h|
| <stddef.h>        | size_t, ptrdiff_t, NULL, offsetof                           |
| <stdbool.h>       | bool, true, false (C99+)                                    |
| <limits.h>        | CHAR_MIN, CHAR_MAX, SHRT_MIN, INT_MAX, LLONG_MAX, etc.     |
| <stdckdint.h>     | ckd_add, ckd_sub, ckd_mul (C23 — checked arithmetic)        |
+-------------------+-------------------------------------------------------------+
```

---

## Closing Mental Model: The Complete Picture

```
C INTEGER TYPE HIERARCHY
========================

Raw Bits
   |
   +-- 8 bits  --> char / signed char / unsigned char / int8_t / uint8_t
   |
   +-- 16 bits --> short / int_least16_t / int16_t / uint16_t
   |
   +-- 32 bits --> int / long(maybe) / int32_t / uint32_t
   |
   +-- 64 bits --> long long / long(maybe) / int64_t / uint64_t / intmax_t
   |
   +-- ptr-size -> size_t / ptrdiff_t / intptr_t / uintptr_t

RULE 1: For general arithmetic and loop counters             --> int
RULE 2: For sizes and indices                                --> size_t
RULE 3: For pointer differences                              --> ptrdiff_t
RULE 4: For pointers cast to integers                        --> uintptr_t
RULE 5: For portable exact-width (files, network, hardware)  --> intN_t/uintN_t
RULE 6: For boolean flags                                    --> bool
RULE 7: For byte buffers / raw data                          --> uint8_t or unsigned char
RULE 8: For the widest possible integer                      --> intmax_t/uintmax_t
RULE 9: NEVER use long for portable cross-platform code      --> too variable
RULE 10: NEVER mix signed and unsigned in comparisons        --> use explicit casts
```

---

*End of guide. This document covers the complete C integer type system as defined by C89, C99, C11, and C20 standards.*