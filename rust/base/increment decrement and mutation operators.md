# Increment, Decrement & Mutation Operators — Complete Guide
### C · Go · Rust — In-Depth, First-Principles Reference

---

## Table of Contents

1. [Taxonomy of Operators](#1-taxonomy-of-operators)
2. [Mental Model: How the CPU Sees These](#2-mental-model-how-the-cpu-sees-these)
3. [Pre-Increment vs Post-Increment (`++i` vs `i++`)](#3-pre-increment-vs-post-increment)
4. [Pre-Decrement vs Post-Decrement (`--i` vs `i--`)](#4-pre-decrement-vs-post-decrement)
5. [Compound Assignment Operators](#5-compound-assignment-operators)
6. [Bitwise Compound Assignment Operators](#6-bitwise-compound-assignment-operators)
7. [Sequence Points, Evaluation Order & Undefined Behavior (C)](#7-sequence-points-evaluation-order--undefined-behavior-c)
8. [Language-by-Language Deep Dive](#8-language-by-language-deep-dive)
   - 8.1 [C](#81-c)
   - 8.2 [Go](#82-go)
   - 8.3 [Rust](#83-rust)
9. [Assembly-Level Analysis](#9-assembly-level-analysis)
10. [Operator Overloading & Custom Types](#10-operator-overloading--custom-types)
11. [Iterators, Cursors & Pointer Arithmetic](#11-iterators-cursors--pointer-arithmetic)
12. [Atomics & Concurrent Mutation](#12-atomics--concurrent-mutation)
13. [Overflow Semantics](#13-overflow-semantics)
14. [Common Pitfalls & Anti-Patterns](#14-common-pitfalls--anti-patterns)
15. [Performance & Optimization](#15-performance--optimization)
16. [Full Code Implementations](#16-full-code-implementations)
17. [Test, Fuzz & Benchmark Steps](#17-test-fuzz--benchmark-steps)
18. [References](#18-references)

---

## 1. Taxonomy of Operators

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     MUTATION OPERATOR TAXONOMY                              │
├──────────────────────┬─────────────────────────────────────────────────────┤
│ CATEGORY             │ OPERATORS                                            │
├──────────────────────┼─────────────────────────────────────────────────────┤
│ Prefix Increment     │ ++i                                                  │
│ Postfix Increment    │ i++                                                  │
│ Prefix Decrement     │ --i                                                  │
│ Postfix Decrement    │ i--                                                  │
├──────────────────────┼─────────────────────────────────────────────────────┤
│ Arithmetic Compound  │ +=  -=  *=  /=  %=                                  │
│ Bitwise Compound     │ &=  |=  ^=  <<=  >>=                                 │
│ (Rust extra)         │ >>>=  (logical shift, not in stable)                 │
├──────────────────────┼─────────────────────────────────────────────────────┤
│ Assignment           │ = (plain, not mutation per se, but root op)         │
│ Walrus (Python only) │ :=  (not covered — Go := is declaration)            │
└──────────────────────┴─────────────────────────────────────────────────────┘
```

**Language availability matrix:**

| Operator | C   | Go  | Rust |
|----------|-----|-----|------|
| `++i`    | ✅  | ❌  | ❌   |
| `i++`    | ✅  | ✅* | ❌   |
| `--i`    | ✅  | ❌  | ❌   |
| `i--`    | ✅  | ✅* | ❌   |
| `+=`     | ✅  | ✅  | ✅   |
| `-=`     | ✅  | ✅  | ✅   |
| `*=`     | ✅  | ✅  | ✅   |
| `/=`     | ✅  | ✅  | ✅   |
| `%=`     | ✅  | ✅  | ✅   |
| `&=`     | ✅  | ✅  | ✅   |
| `\|=`   | ✅  | ✅  | ✅   |
| `^=`     | ✅  | ✅  | ✅   |
| `<<=`    | ✅  | ✅  | ✅   |
| `>>=`    | ✅  | ✅  | ✅   |

> *Go's `i++` and `i--` are **statements**, not expressions. They cannot produce a value.

---

## 2. Mental Model: How the CPU Sees These

At the machine level, **all of these collapse to `LOAD → MODIFY → STORE`**:

```
i++   →   tmp = LOAD(addr(i))
           STORE(addr(i), tmp + 1)
           use(tmp)              ← returns OLD value

++i   →   tmp = LOAD(addr(i)) + 1
           STORE(addr(i), tmp)
           use(tmp)              ← returns NEW value
```

On modern x86-64, `++i` and `i++` on a standalone statement compile to the **same** instruction (`INC` or `ADD`). The difference is only observable **when the expression's value is consumed**.

```asm
; Standalone: no observable difference
inc DWORD PTR [rbp-4]    ; both ++i and i++ when result unused

; When result IS used:
; i++ → MOV eax, [rbp-4] ; read old
;        ADD [rbp-4], 1  ; increment in place
;        use eax         ; return old

; ++i → ADD [rbp-4], 1  ; increment
;        MOV eax, [rbp-4] ; read new
;        use eax          ; return new
```

---

## 3. Pre-Increment vs Post-Increment

### Conceptual definition

```
Pre-increment (++i):
  1. Increment i by 1
  2. Return the NEW value of i

Post-increment (i++):
  1. Save the CURRENT value of i as temp
  2. Increment i by 1
  3. Return temp (the OLD value)
```

### Value semantics illustrated

```c
int i = 5;

int a = ++i;   // i becomes 6, a = 6  (prefix: increment THEN read)
int b = i++;   // b = 6 (old i), i becomes 7  (postfix: read THEN increment)
int c = --i;   // i becomes 6, c = 6
int d = i--;   // d = 6 (old i), i becomes 5
```

### State trace table

| Step       | Expression | i before | i after | Returned |
|------------|------------|----------|---------|----------|
| `a = ++i`  | `++i`      | 5        | 6       | 6        |
| `b = i++`  | `i++`      | 6        | 7       | 6        |
| `c = --i`  | `--i`      | 7        | 6       | 6        |
| `d = i--`  | `i--`      | 6        | 5       | 6        |

### Chaining (C only — dangerous territory)

```c
int i = 3;
int x = (++i) + (++i);   // UNDEFINED BEHAVIOR in C — modifying i twice
                           // between sequence points
```

---

## 4. Pre-Decrement vs Post-Decrement

Mirror of increment, same rules apply.

```c
int i = 10;

int a = --i;   // i = 9,  a = 9   (prefix decrement)
int b = i--;   // b = 9,  i = 8   (postfix decrement)
```

### Practical difference: loop idioms

```c
// Prefix: check AFTER decrement — more natural for "count down to zero"
int n = 5;
while (--n > 0) {       // iterates n=4,3,2,1 → 4 iterations
    printf("%d\n", n);
}

// Postfix: check BEFORE decrement — iterate 5,4,3,2,1 → 5 iterations
int m = 5;
while (m-- > 0) {       // reads m=5,4,3,2,1, then decrements
    printf("%d\n", m);  // prints 4,3,2,1,0 ← tricky!
}
```

> **Trap**: `while (m-- > 0)` decrements *then* the body sees the already-decremented `m`. Many bugs live here.

---

## 5. Compound Assignment Operators

### Full operator table with exact semantics

| Operator | Meaning       | Equivalent to    | Notes                              |
|----------|---------------|------------------|------------------------------------|
| `x += n` | Add-assign    | `x = x + n`     | Arithmetic addition                |
| `x -= n` | Sub-assign    | `x = x - n`     | Arithmetic subtraction             |
| `x *= n` | Mul-assign    | `x = x * n`     | Multiplication                     |
| `x /= n` | Div-assign    | `x = x / n`     | Integer truncation if both int     |
| `x %= n` | Mod-assign    | `x = x % n`     | Remainder; sign follows dividend C |

### Critical: `x op= expr` evaluates `x` ONCE

```c
int arr[5] = {1,2,3,4,5};
int i = 1;

arr[i++] += 10;
// Evaluates arr[1] += 10 → arr[1] = 12, and i becomes 2
// "arr[i++]" is evaluated ONCE — the side effect of i++ is NOT repeated
```

This is guaranteed since C11 via sequence-point rules and in all three languages.

### Integer division truncation semantics

```c
int x = 7;
x /= 2;    // x = 3, NOT 3.5 (truncation toward zero in C99+)

int y = -7;
y /= 2;    // y = -3 (toward zero), NOT -4 (toward negative infinity)
```

### Modulo sign behavior (language differences)

| Expression | C (C99+) | Go    | Rust  |
|------------|----------|-------|-------|
| `7 % 3`    | `1`      | `1`   | `1`   |
| `-7 % 3`   | `-1`     | `-1`  | `-1`  |
| `7 % -3`   | `1`      | `1`   | `1`   |
| `-7 % -3`  | `-1`     | `-1`  | `-1`  |

> All three follow **truncated division** (sign follows dividend). Python follows **floored division** (sign follows divisor) — completely different behavior.

---

## 6. Bitwise Compound Assignment Operators

### Operator semantics

| Operator | Meaning                    | Use Case                                |
|----------|----------------------------|-----------------------------------------|
| `x &= m` | AND-assign (mask/clear)    | Clear specific bits: `flags &= ~FLAG_A` |
| `x \|= m`| OR-assign (set bits)       | Set specific bits: `flags \|= FLAG_B`  |
| `x ^= m` | XOR-assign (toggle/flip)   | Toggle bits: `flags ^= FLAG_C`          |
| `x <<= n`| Left-shift-assign          | Multiply by 2^n (if no overflow)        |
| `x >>= n`| Right-shift-assign         | Arithmetic or logical divide by 2^n    |

### Bit manipulation idioms using compound assign

```c
typedef uint32_t flags_t;

#define FLAG_READ    (1U << 0)   // 0x00000001
#define FLAG_WRITE   (1U << 1)   // 0x00000002
#define FLAG_EXEC    (1U << 2)   // 0x00000004
#define FLAG_SUID    (1U << 3)   // 0x00000008

flags_t perms = 0;

// SET bits
perms |= FLAG_READ | FLAG_WRITE;    // perms = 0x03

// CLEAR bits
perms &= ~FLAG_WRITE;               // perms = 0x01

// TOGGLE bits
perms ^= FLAG_EXEC;                 // perms = 0x05

// CHECK bit (no mutation)
if (perms & FLAG_READ) { ... }

// Shift-assign for log2 indexing
uint32_t bucket = 0;
bucket <<= 3;     // bucket *= 8
bucket >>= 1;     // bucket /= 2
```

### Arithmetic vs Logical Right Shift

```
Value: -8 in int8_t = 0b11111000 (two's complement)

Arithmetic right shift (>>): sign-extends
  -8 >> 1 = 0b11111100 = -4   ← preserves sign (signed types)

Logical right shift: zero-extends
  -8 >> 1 = 0b01111100 = 124  ← treats as unsigned (unsigned types)
```

**In C**: `>>` on signed integers is **implementation-defined** for negative values.  
**In Go**: `>>` is arithmetic for signed, logical for unsigned — defined behavior.  
**In Rust**: `>>` is arithmetic for signed (`i32`), logical for unsigned (`u32`) — defined behavior.

```rust
// Rust: explicit control
let x: i32 = -8;
let y = x >> 1;          // -4  (arithmetic, defined)

let x: u32 = 0b11111000;
let y = x >> 1;          // 0b01111100 = 124 (logical, defined)
```

---

## 7. Sequence Points, Evaluation Order & Undefined Behavior (C)

This is the most dangerous section for C programmers.

### What is a sequence point?

A **sequence point** is a point in program execution where all side effects of preceding evaluations are complete, and no side effects of subsequent evaluations have started. In C11+, this was reformalized as **sequenced-before** relationships.

### Classic undefined behavior patterns

```c
// ❌ UB: i modified twice between sequence points
int i = 5;
i = i++;              // UB — both modify i

// ❌ UB: i modified and read (for non-determining-the-new-value purpose)
int arr[10];
arr[i] = i++;         // UB — i read and modified

// ❌ UB: order of evaluation of function arguments is unspecified
printf("%d %d", i++, i++);   // UB

// ❌ UB: chained modification
int x = (i++) + (i++);       // UB

// ✅ OK: i modified once per statement
i++;
i += 2;
int x = i;

// ✅ OK: i++ in separate sub-expressions with intervening sequence point
// C uses comma operator as sequence point
int a = (i++, i++);    // OK: first i++, THEN i++ — a = second result
```

### What the compiler can do with UB

The compiler **may legally**:
- Use the old OR new value of `i`
- Evaluate both increments simultaneously
- Optimize away the entire expression
- Emit nasal demons (joke, but the point is: ANY behavior is conforming)

### C11 sequenced-before rules (simplified)

```
Full expression boundary (`;`)     → sequence point
`&&` and `||` (short-circuit)      → left sequenced-before right
`,` operator                       → left sequenced-before right
`?:` condition                     → sequenced before selected branch
Function call: all args            → sequenced before function body
```

### Compiler warnings to enable

```bash
gcc -Wall -Wextra -Wsequence-point -fsanitize=undefined -o prog prog.c
clang -Wall -Wextra -fsanitize=undefined -o prog prog.c
```

UBSan will catch many (not all) of these at runtime.

---

## 8. Language-by-Language Deep Dive

### 8.1 C

#### `++i` and `i++` as lvalues (pre-increment is, post-increment is NOT)

```c
int i = 5;

++(++i);    // OK in C: ++i returns an lvalue, can be incremented again
            // Result: i = 7

// (i++)++;  // ERROR: i++ returns an rvalue (prvalue), cannot increment
```

#### Pointer arithmetic with `++`

```c
int arr[] = {10, 20, 30, 40, 50};
int *p = arr;

printf("%d\n", *p++);   // prints 10, p now points to arr[1]
                         // postfix ++ has higher precedence than *
                         // equivalent to *(p++)

printf("%d\n", *++p);   // p advances to arr[2], prints 30
                         // prefix ++ has SAME precedence as *, right-to-left
                         // equivalent to *(++p)

printf("%d\n", ++*p);   // increments the VALUE at p (arr[2] → 31), prints 31
                         // equivalent to ++(*p)

printf("%d\n", (*p)++); // prints 31 (current arr[2]), then arr[2] becomes 32
```

#### Volatile and `++`

```c
volatile int counter = 0;

counter++;    // Generates a LOAD and STORE even with optimization
              // Without volatile, standalone ++ might be cached in register
              // With volatile: compiler must access memory every time

// In device drivers / MMIO — volatile is critical for correctness
volatile uint32_t *reg = (volatile uint32_t *)0xDEADBEEF;
(*reg)++;    // Guaranteed to read from and write to exact memory address
```

#### `_Atomic` and `++` (C11)

```c
#include <stdatomic.h>

_Atomic int shared = 0;

// These are atomic read-modify-write operations
shared++;    // atomic_fetch_add(&shared, 1) — returns old value
++shared;    // atomic_fetch_add(&shared, 1) + 1 — but full expression atomic
shared += 5; // atomic_fetch_add(&shared, 5)
```

---

### 8.2 Go

#### Go's deliberate design choice

Go **deliberately removed** `++` and `--` as expressions (they are statements only) and **removed prefix forms entirely** to eliminate a whole class of bugs.

```go
i := 5

i++    // STATEMENT: valid, i = 6
i--    // STATEMENT: valid, i = 5

// ❌ These do NOT compile in Go:
// j := i++      → syntax error
// ++i           → syntax error
// --i           → syntax error
// arr[i++] = 0  → syntax error (i++ not an expression)
```

#### Why Go made this choice

From the Go FAQ:
> "Without pointer arithmetic [and with] the +/- operators as statements (not expressions), the source of confusion and bugs... is eliminated."

Go treats `i++` as syntactic sugar for `i += 1`, nothing more. It cannot be nested or chained.

#### Go compound assignment operators

```go
x := 10

x += 3    // x = 13
x -= 2    // x = 11
x *= 4    // x = 44
x /= 11   // x = 4
x %= 3    // x = 1

x = 0b10101010
x &= 0x0F    // x = 0x0A (clear upper nibble)
x |= 0x50    // x = 0x5A (set bits)
x ^= 0xFF    // x = 0xA5 (flip all bits)
x <<= 2      // x = 0x294 (shift left 2)
x >>= 1      // x = 0x14A (shift right 1, arithmetic for int)
```

#### Go's evaluation order for compound assignments

```go
// Go defines left-to-right evaluation of indices and operands
a := []int{1, 2, 3}
i := 0
a[i] = i + 1   // i is evaluated, then a[i] assigned; i = 0, a[0] = 1
                 // well-defined in Go
```

---

### 8.3 Rust

#### Rust has no `++` or `--` at all

Rust made the same choice as Go but went further — **no `++` or `--` in any form**.

```rust
let mut i = 5;

// ❌ Does NOT compile:
// i++     → error[E0067]: invalid left-hand side of assignment
// ++i     → error[E0600]: cannot apply unary operator `+` twice
// i--     → same errors

// ✅ Correct idiomatic Rust:
i += 1;   // increment
i -= 1;   // decrement
```

#### Rust compound assignment operators

```rust
let mut x: i32 = 100;

x += 10;    // x = 110
x -= 20;    // x = 90
x *= 3;     // x = 270
x /= 9;     // x = 30
x %= 7;     // x = 2

let mut flags: u8 = 0b00000000;
flags |= 0b00001111;   // set lower nibble
flags &= 0b11110101;   // clear bits 1 and 3 in lower nibble
flags ^= 0b00001010;   // toggle bits
flags <<= 2;            // shift left
flags >>= 1;            // shift right (logical for u8)
```

#### Rust wrapping/checked/saturating variants

Rust exposes the overflow behavior explicitly through method chaining, even for compound ops:

```rust
let mut x: u8 = 250;

// Standard += panics in debug mode on overflow
// x += 10;   // panic: 'attempt to add with overflow' (debug)
              // wraps in release mode (unsafe to rely on!)

// Safe alternatives:
x = x.wrapping_add(10);    // x = 4 (wraps 260 → 4)
x = x.saturating_add(10);  // x = 255 (saturates at max)
x = x.checked_add(10).unwrap_or(0);  // checked, returns Option<u8>

// For i32, arithmetic shift right:
let y: i32 = -8;
let z = y >> 1;   // z = -4 (arithmetic, sign-extended, defined)

// Explicit wrapping shift (to avoid panic on shift >= bit_width):
let a: u32 = 1;
let b = a.wrapping_shl(32);  // wraps: result = 1 (since 32 % 32 = 0)
```

#### Rust's `AddAssign`, `SubAssign` traits

```rust
use std::ops::{AddAssign, SubAssign};

#[derive(Debug, Clone, Copy)]
struct Counter {
    value: i64,
    step: i64,
}

impl AddAssign<i64> for Counter {
    fn add_assign(&mut self, rhs: i64) {
        self.value += rhs * self.step;
    }
}

impl SubAssign<i64> for Counter {
    fn sub_assign(&mut self, rhs: i64) {
        self.value -= rhs * self.step;
    }
}

fn main() {
    let mut c = Counter { value: 0, step: 5 };
    c += 3;    // value += 3 * 5 = 15
    c -= 1;    // value -= 1 * 5 = 10
    println!("{:?}", c);  // Counter { value: 10, step: 5 }
}
```

---

## 9. Assembly-Level Analysis

### Setup for analysis

```bash
# C → ASM
gcc -O0 -S -fverbose-asm -o out.s prog.c   # no optimization
gcc -O2 -S -fverbose-asm -o out.s prog.c   # with optimization

# Go → ASM
go tool compile -S main.go > out.s

# Rust → ASM
rustc --emit=asm -C opt-level=0 -o /dev/null main.rs > out.s
cargo rustc -- --emit=asm                  # places in target/debug/deps/
```

### C: `i++` vs `++i` at `-O0`

```c
// Source
int a = i++;
int b = ++i;
```

```asm
; int a = i++
mov    eax, DWORD PTR [rbp-4]   ; load i
lea    edx, [rax+1]             ; compute i+1
mov    DWORD PTR [rbp-4], edx   ; store i+1 → i
mov    DWORD PTR [rbp-8], eax   ; store OLD value → a

; int b = ++i
add    DWORD PTR [rbp-4], 1     ; increment i in place
mov    eax, DWORD PTR [rbp-4]   ; load NEW i
mov    DWORD PTR [rbp-12], eax  ; store → b
```

At `-O2`, both often reduce to a single `inc` or `add` with the stored result differing.

### Go: `i++` (statement only)

```go
i++
```

```asm
MOVQ    "".i+8(SP), AX
INCQ    AX
MOVQ    AX, "".i+8(SP)
```

Go's `i++` is always a clean `INC` — never entangled in expression evaluation.

### Rust: `i += 1`

```rust
let mut i: i32 = 5;
i += 1;
```

```asm
; debug mode (no opt)
movl    -4(%rbp), %eax          ; load i
addl    $1, %eax                ; add 1
movl    %eax, -4(%rbp)          ; store back

; release mode (opt=3) — often becomes:
incl    %edi                    ; single INC instruction if register-allocated
```

---

## 10. Operator Overloading & Custom Types

### C: No overloading — simulate with macros or functions

```c
// For user-defined types, you must write explicit functions
typedef struct { double real, imag; } Complex;

static inline Complex complex_add(Complex a, Complex b) {
    return (Complex){ a.real + b.real, a.imag + b.imag };
}

// "Increment" a complex number by (1,0)
static inline Complex complex_inc(Complex *c) {
    Complex old = *c;
    c->real += 1.0;
    return old;  // simulates postfix behavior
}
```

### Go: No operator overloading at all

```go
// Must use explicit methods
type Vector2 struct{ X, Y float64 }

func (v *Vector2) Add(other Vector2) {
    v.X += other.X
    v.Y += other.Y
}

// Usage
v := Vector2{1, 2}
v.Add(Vector2{3, 4})   // v = {4, 6}
```

### Rust: Operator overloading via traits

```rust
use std::ops::{Add, AddAssign, Sub, SubAssign, Neg};

#[derive(Debug, Clone, Copy, PartialEq)]
struct Vec2 {
    x: f64,
    y: f64,
}

impl AddAssign for Vec2 {
    fn add_assign(&mut self, rhs: Vec2) {
        self.x += rhs.x;
        self.y += rhs.y;
    }
}

impl SubAssign for Vec2 {
    fn sub_assign(&mut self, rhs: Vec2) {
        self.x -= rhs.x;
        self.y -= rhs.y;
    }
}

impl Add for Vec2 {
    type Output = Vec2;
    fn add(self, rhs: Vec2) -> Vec2 {
        Vec2 { x: self.x + rhs.x, y: self.y + rhs.y }
    }
}

impl Neg for Vec2 {
    type Output = Vec2;
    fn neg(self) -> Vec2 {
        Vec2 { x: -self.x, y: -self.y }
    }
}

fn main() {
    let mut a = Vec2 { x: 1.0, y: 2.0 };
    let b = Vec2 { x: 3.0, y: 4.0 };
    a += b;    // calls add_assign
    a -= b;    // calls sub_assign
    println!("{:?}", a);  // Vec2 { x: 1.0, y: 2.0 }
}
```

---

## 11. Iterators, Cursors & Pointer Arithmetic

### C: Pointer increment as iterator

```c
// Classic C pattern: pointer-as-iterator
const char *haystack = "hello world";
const char *needle = "world";

// Advance pointer to find substring
const char *p = haystack;
while (*p) {
    if (strncmp(p, needle, strlen(needle)) == 0) {
        printf("Found at offset %ld\n", p - haystack);
        break;
    }
    p++;    // advance one element (sizeof char = 1 byte)
}

// Generic typed pointer arithmetic
int arr[] = {5, 3, 1, 4, 2};
int *start = arr;
int *end   = arr + 5;    // one past last element — sentinel

for (int *cur = start; cur != end; cur++) {  // cur++ → cur += sizeof(int)
    printf("%d ", *cur);
}
```

**Key rule**: `p++` on `T*` advances by `sizeof(T)` bytes, not 1 byte.

```c
int   *pi = ...; pi++;   // advances 4 bytes
double *pd = ...; pd++;  // advances 8 bytes
char  *pc = ...; pc++;   // advances 1 byte
```

### Go: Explicit index — no pointer arithmetic

```go
// Go does not allow pointer arithmetic directly
// Use slices as iterators
data := []int{5, 3, 1, 4, 2}

for i := 0; i < len(data); i++ {
    fmt.Println(data[i])
}

// Or range (idiomatic Go)
for i, v := range data {
    fmt.Printf("data[%d] = %d\n", i, v)
}
```

### Rust: Iterator adapters — `++` replaced by `.next()`, `.advance_by()`

```rust
fn main() {
    let data = vec![5, 3, 1, 4, 2];

    // iter() returns an iterator, next() advances it
    let mut iter = data.iter();
    while let Some(val) = iter.next() {
        println!("{}", val);
    }

    // Indexed style (like C for-loop)
    for i in 0..data.len() {
        println!("data[{}] = {}", i, data[i]);
    }

    // Iterator chaining — no explicit ++ anywhere
    let sum: i32 = data.iter()
        .filter(|&&x| x > 2)
        .map(|&x| x * 2)
        .sum();
    println!("sum = {}", sum);  // (5+3+4)*2 = 24
}

// Raw pointer arithmetic in Rust (unsafe)
fn raw_ptr_walk() {
    let arr = [1i32, 2, 3, 4, 5];
    let mut ptr = arr.as_ptr();
    let end = unsafe { ptr.add(arr.len()) };

    unsafe {
        while ptr != end {
            println!("{}", *ptr);
            ptr = ptr.add(1);    // equivalent to ptr++ in C
            // ptr.offset(1) is the older API, prefer .add() for non-negative
        }
    }
}
```

---

## 12. Atomics & Concurrent Mutation

### C11 Atomics

```c
#include <stdatomic.h>
#include <pthread.h>

atomic_int shared_counter = 0;

void *worker(void *arg) {
    for (int i = 0; i < 100000; i++) {
        // All of these are atomic operations:
        atomic_fetch_add(&shared_counter, 1);   // atomic ++
        atomic_fetch_sub(&shared_counter, 1);   // atomic --
        atomic_fetch_add_explicit(&shared_counter, 5, memory_order_relaxed);  // fast
    }
    return NULL;
}
```

**`++` on `_Atomic` types** in C11 is defined to be an atomic RMW (read-modify-write) operation with `memory_order_seq_cst` (sequentially consistent — the strongest ordering). This is EXPENSIVE.

```c
_Atomic int x = 0;
x++;    // Equivalent to atomic_fetch_add_explicit(&x, 1, memory_order_seq_cst)
        // This generates LOCK XADD or LOCK INC on x86-64

// For performance-sensitive code, use explicit relaxed ordering:
atomic_fetch_add_explicit(&x, 1, memory_order_relaxed);
```

### Go: `sync/atomic`

```go
import "sync/atomic"

var counter int64 = 0

// Atomic increment (no ++ on atomic types)
atomic.AddInt64(&counter, 1)     // counter += 1 atomically
atomic.AddInt64(&counter, -1)    // counter -= 1 atomically
atomic.AddInt64(&counter, 5)     // counter += 5 atomically

// Newer API (Go 1.19+): typed atomics
var c atomic.Int64
c.Add(1)
c.Add(-1)
val := c.Load()
```

### Rust: `std::sync::atomic`

```rust
use std::sync::atomic::{AtomicI32, Ordering};
use std::sync::Arc;
use std::thread;

fn main() {
    let counter = Arc::new(AtomicI32::new(0));
    let mut handles = vec![];

    for _ in 0..4 {
        let c = Arc::clone(&counter);
        handles.push(thread::spawn(move || {
            for _ in 0..100_000 {
                // Equivalent to ++; uses fetch_add
                c.fetch_add(1, Ordering::Relaxed);

                // Equivalent to +=
                c.fetch_add(5, Ordering::SeqCst);  // sequential consistency

                // Equivalent to &=
                c.fetch_and(0xFF, Ordering::AcqRel);

                // Equivalent to |=
                c.fetch_or(0x01, Ordering::Release);

                // Equivalent to ^=
                c.fetch_xor(0b10101010, Ordering::Acquire);
            }
        }));
    }

    for h in handles { h.join().unwrap(); }
    println!("final: {}", counter.load(Ordering::SeqCst));
}
```

### Memory ordering quick reference

| Ordering         | C11 Equivalent           | Meaning                                    |
|------------------|--------------------------|--------------------------------------------|
| `Relaxed`        | `memory_order_relaxed`   | Only atomicity, no ordering guarantees     |
| `Acquire`        | `memory_order_acquire`   | Load: see all writes before paired Release |
| `Release`        | `memory_order_release`   | Store: previous writes visible to Acquire  |
| `AcqRel`         | `memory_order_acq_rel`   | Both Acquire and Release (for RMW ops)     |
| `SeqCst`         | `memory_order_seq_cst`   | Total global order (expensive, safe)       |

---

## 13. Overflow Semantics

### C: Signed overflow is Undefined Behavior

```c
int x = INT_MAX;   // 2147483647
x++;               // UNDEFINED BEHAVIOR — signed overflow

// Compiler may assume signed overflow never happens and optimize aggressively
// GCC with -O2 will convert:
//   for (int i = 0; i < i+1; i++) { ... }
// into an infinite loop, because "i < i+1" is always true under no-UB assumption

// Safe alternatives:
if (x < INT_MAX) x++;  // guard before increment
x = (x == INT_MAX) ? INT_MAX : x + 1;  // saturating

// Or use unsigned (wrapping is defined for unsigned in C):
unsigned int u = UINT_MAX;
u++;    // u = 0 (wraps, DEFINED behavior for unsigned)
```

### C: Detecting overflow before it happens

```c
#include <limits.h>

// Check before incrementing
bool safe_increment(int *x) {
    if (*x == INT_MAX) return false;
    (*x)++;
    return true;
}

// Using __builtin_add_overflow (GCC/Clang extension)
int result;
if (__builtin_add_overflow(*x, 1, &result)) {
    // overflow would occur
} else {
    *x = result;
}
```

### Go: Wraps silently (no panic, no UB)

```go
var x int8 = 127
x++          // x = -128 (wraps — defined behavior in Go)
// No panic, no UB — Go integer overflow always wraps in two's complement
```

### Rust: Overflow depends on build mode

```rust
fn main() {
    let mut x: i8 = 127;

    // debug build: panics with "attempt to add with overflow"
    // release build: wraps silently (same as Go)
    x += 1;

    // Explicit wrapping (always wraps, regardless of build mode):
    x = x.wrapping_add(1);     // x = -128

    // Explicit checked (returns None on overflow):
    let result = x.checked_add(1);  // Some(-127) or None

    // Explicit saturating:
    x = x.saturating_add(200);     // x = 127 (saturates at i8::MAX)

    // Explicit overflowing (returns value AND bool):
    let (val, overflowed) = x.overflowing_add(1);
    // val = -128, overflowed = true
}
```

**Overflow summary:**

| Scenario                    | C (signed)  | C (unsigned) | Go    | Rust (debug) | Rust (release) |
|-----------------------------|-------------|--------------|-------|--------------|----------------|
| `MAX + 1`                   | UB          | Wraps        | Wraps | Panic        | Wraps          |
| `MIN - 1`                   | UB          | Wraps        | Wraps | Panic        | Wraps          |
| Compile-time detectable?    | Warning     | No           | No    | Yes          | No             |
| Safe checked variant?       | Extension   | N/A          | No*   | `checked_*`  | `checked_*`    |

*Go has `math/big` for arbitrary precision, but no checked arithmetic on basic types.

---

## 14. Common Pitfalls & Anti-Patterns

### Pitfall 1: Off-by-one in loops (pre vs post confusion)

```c
// Intention: process elements 0..n-1
int n = 10;

// ❌ Wrong: loop body runs with i=1..10 (starts at 1, ends at 10)
for (int i = 0; ++i < n; ) {   // ++i evaluated BEFORE check
    printf("%d ", i);            // prints 1 2 3 4 5 6 7 8 9
}

// ✅ Correct:
for (int i = 0; i < n; i++) {   // i++ happens AFTER body and check
    printf("%d ", i);            // prints 0 1 2 3 4 5 6 7 8 9
}

// ✅ Also correct (slightly less common):
for (int i = 0; i < n; ++i) {   // ++i same effect when result discarded
    printf("%d ", i);
}
```

### Pitfall 2: Forgetting `i--` in while loop (infinite loop)

```c
int i = 10;
while (i > 0) {
    printf("%d\n", i);
    // ❌ forgot: i--
}   // infinite loop!
```

### Pitfall 3: Double-decrement in complex conditions

```c
// ❌ UB: i decremented twice
if (--i > 0 && --i > 0) { ... }    // well, this is OK (short-circuit is a sequence point)
                                      // BUT: the value of i after differs from intent

// The && does create a sequence point, so it's NOT UB.
// But it IS confusing and error-prone — avoid modifying variables in conditions.
```

### Pitfall 4: Post-increment in function args

```c
int i = 0;
// ❌ UB: argument evaluation order is unspecified
func(i++, i++);    // Could be func(0,1) or func(1,0) or anything

// ✅ Safe: evaluate before calling
int a = i++;
int b = i++;
func(a, b);
```

### Pitfall 5: Rust `+=` moves vs copies

```rust
// For types that implement Copy, += works fine:
let mut x: i32 = 5;
x += 3;    // fine, i32 is Copy

// For non-Copy types with custom AddAssign, mutation in place:
let mut s = String::from("hello");
s += " world";    // calls add_assign, appends in-place

// But note: String += &str (not String)
// s += String::from(" world");  // ERROR: expected &str, found String
// s += &String::from(" world"); // OK: coerces to &str via Deref
```

### Pitfall 6: Go's `i++` in goroutines (data race)

```go
var i int
// ❌ Data race: concurrent i++ without synchronization
go func() { i++ }()
go func() { i++ }()
// i is NOT atomic — use sync/atomic or a mutex

// ✅ Safe:
var atomicI atomic.Int64
go func() { atomicI.Add(1) }()
go func() { atomicI.Add(1) }()
```

### Pitfall 7: Signed shift undefined behavior (C)

```c
int x = -1;
x >>= 1;    // Implementation-defined in C (NOT undefined, but non-portable)
             // On x86 with GCC: arithmetic shift (x = -1) — but don't rely on it!

int y = 1;
y <<= 31;   // OK for int32_t if bit 31 of signed int — borderline UB in C89/C99
             // In C11: UB if result not representable in the type
```

### Pitfall 8: `x /= 0` — always undefined / panic / crash

```c
int x = 10;
x /= 0;    // C: UNDEFINED BEHAVIOR (hardware exception SIGFPE on x86)

// Go:
x /= 0    // runtime panic: integer divide by zero

// Rust:
x /= 0;   // thread panic: 'attempt to divide by zero'
```

Always guard divisions:

```c
if (divisor != 0) x /= divisor;
```

---

## 15. Performance & Optimization

### Pre vs Post: Performance perspective

For **primitive types**: no performance difference when result is unused (same assembly).

For **C++ iterator types** (not covered here but worth noting): `++it` (prefix) is generally preferred because `it++` must copy the old value. This applies to STL iterators, not plain integers.

```cpp
// C++ only (not C, Go, or Rust):
std::vector<int>::iterator it = v.begin();
it++;    // creates a copy of it, increments original, returns copy
++it;    // increments in place, returns reference — FASTER for complex types
```

For Go and Rust: `i += 1` is the only option — no such dilemma.

### Loop counter: which is fastest?

```c
// Forward counting (cache-friendly, branch-predictor friendly)
for (int i = 0; i < n; i++) { process(arr[i]); }

// Reverse counting (sometimes allows comparison against 0 instead of n)
// On some older CPUs, comparing against 0 was 1 cycle faster
for (int i = n - 1; i >= 0; i--) { process(arr[i]); }

// Zero-comparison form (used in tight embedded loops)
int i = n;
do {
    --i;
    process(arr[i]);
} while (i);

// Modern CPUs: negligible difference. Prefer forward for readability.
```

### SIMD and `+=` with vectors

```c
#include <immintrin.h>

// x86 AVX2: add 8 int32 values simultaneously
__m256i va = _mm256_load_si256((__m256i*)a);
__m256i vb = _mm256_load_si256((__m256i*)b);
va = _mm256_add_epi32(va, vb);   // "va += vb" for 8 elements at once
_mm256_store_si256((__m256i*)a, va);
```

### Branch-free increment / decrement

```c
// Branchless conditional increment: increment only if condition is true
// Avoids branch misprediction penalty
int flag = (x > threshold);   // 0 or 1
counter += flag;               // counter++ if true, nop if false
```

---

## 16. Full Code Implementations

### File structure

```
increment_guide/
├── c/
│   ├── main.c
│   └── Makefile
├── go/
│   ├── main.go
│   └── go.mod
└── rust/
    ├── src/main.rs
    └── Cargo.toml
```

---

### C Implementation (`c/main.c`)

```c
#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdatomic.h>
#include <limits.h>
#include <string.h>
#include <assert.h>

/* ─── 1. Basic pre/post increment/decrement ─── */

void demo_basic(void) {
    puts("\n=== Basic Increment/Decrement ===");

    int i = 5;

    printf("Initial i = %d\n", i);
    printf("i++ returns %d, i is now %d\n", i++, i);   // prints 5, 6
    printf("++i returns %d, i is now %d\n", ++i, i);   // prints 7, 7
    printf("i-- returns %d, i is now %d\n", i--, i);   // prints 7, 6
    printf("--i returns %d, i is now %d\n", --i, i);   // prints 5, 5

    // Reset
    i = 5;

    // Chaining safe forms
    int a = ++i;   // i=6, a=6
    int b = i++;   // b=6, i=7
    int c = --i;   // i=6, c=6
    int d = i--;   // d=6, i=5

    printf("After chain: a=%d b=%d c=%d d=%d i=%d\n", a, b, c, d, i);
    assert(a == 6 && b == 6 && c == 6 && d == 6 && i == 5);
}

/* ─── 2. Compound arithmetic assignment ─── */

void demo_compound_arithmetic(void) {
    puts("\n=== Compound Arithmetic Assignment ===");

    int x = 100;

    x += 25;   printf("+= 25 → %d\n", x);   // 125
    x -= 75;   printf("-= 75 → %d\n", x);   // 50
    x *= 3;    printf("*= 3  → %d\n", x);   // 150
    x /= 5;    printf("/= 5  → %d\n", x);   // 30
    x %= 7;    printf("%%= 7  → %d\n", x);  // 2

    // Division truncation
    int y = -7;
    y /= 2;
    printf("-7 /= 2 → %d (truncates toward zero)\n", y);  // -3

    // Modulo sign
    int m1 = -7 % 3;
    int m2 = 7 % -3;
    printf("-7 %% 3 = %d, 7 %% -3 = %d\n", m1, m2);  // -1, 1
}

/* ─── 3. Compound bitwise assignment ─── */

void demo_compound_bitwise(void) {
    puts("\n=== Compound Bitwise Assignment ===");

    uint32_t flags = 0x00000000;

    // Set bits
    flags |= (1U << 0);   // set bit 0 (READ)
    flags |= (1U << 2);   // set bit 2 (EXEC)
    printf("After set:    0x%08X\n", flags);   // 0x00000005

    // Clear bits
    flags &= ~(1U << 2);  // clear bit 2
    printf("After clear:  0x%08X\n", flags);   // 0x00000001

    // Toggle bits
    flags ^= (1U << 1);   // toggle bit 1 (WRITE)
    printf("After toggle: 0x%08X\n", flags);   // 0x00000003

    // Shift operations
    uint32_t val = 0x00000001;
    val <<= 4;    printf("<<= 4 → 0x%08X\n", val);   // 0x00000010
    val >>= 2;    printf(">>= 2 → 0x%08X\n", val);   // 0x00000004

    // Arithmetic right shift on signed
    int32_t sv = -128;
    sv >>= 2;
    printf("-128 >>= 2 → %d (impl-defined, typically -32)\n", sv);
}

/* ─── 4. Pointer arithmetic with ++ ─── */

void demo_pointer_increment(void) {
    puts("\n=== Pointer Arithmetic ===");

    int arr[] = {10, 20, 30, 40, 50};
    int *p = arr;

    printf("*p++  = %d (p now points to arr[1])\n", *p++);   // 10
    printf("*p    = %d\n", *p);                                // 20
    printf("*++p  = %d (p now points to arr[2])\n", *++p);   // 30
    printf("(*p)++: arr[2] was %d", *p);
    (*p)++;
    printf(", arr[2] is now %d\n", arr[2]);   // 31

    // Iterator pattern over array
    printf("All elements: ");
    for (int *cur = arr, *end = arr + 5; cur != end; cur++) {
        printf("%d ", *cur);
    }
    printf("\n");
}

/* ─── 5. Overflow demo ─── */

void demo_overflow(void) {
    puts("\n=== Overflow Behavior ===");

    // Unsigned wraps (defined)
    uint8_t u = 255;
    u++;
    printf("uint8 255++ = %u (wraps to 0)\n", u);   // 0

    uint8_t v = 0;
    v--;
    printf("uint8 0-- = %u (wraps to 255)\n", v);   // 255

    // Signed: use __builtin_add_overflow (GCC/Clang)
    int32_t big = INT32_MAX;
    int32_t result;
    if (__builtin_add_overflow(big, 1, &result)) {
        printf("int32 MAX+1 would overflow! Not incrementing.\n");
    }
}

/* ─── 6. Atomic increment ─── */

void demo_atomic(void) {
    puts("\n=== Atomic Operations ===");

    _Atomic int counter = 0;

    // These are atomic RMW operations
    counter++;                          // seq_cst
    int old = atomic_fetch_add(&counter, 1);         // returns old value
    atomic_fetch_add_explicit(&counter, 5, memory_order_relaxed);

    printf("counter = %d, old value during fetch_add = %d\n",
           atomic_load(&counter), old);
}

/* ─── 7. Loop idioms ─── */

void demo_loop_idioms(void) {
    puts("\n=== Loop Idioms ===");

    // Classic for-loop
    for (int i = 0; i < 5; i++) printf("%d ", i);
    puts("← i++ in for");

    // Reverse
    for (int i = 4; i >= 0; i--) printf("%d ", i);
    puts("← i-- reverse");

    // While with pre-decrement
    int n = 5;
    while (--n >= 0) printf("%d ", n);  // 4 3 2 1 0
    puts("← --n while");

    // While with post-decrement (careful!)
    n = 5;
    while (n-- > 0) printf("%d ", n);   // 4 3 2 1 0 (body sees decremented n)
    puts("← n-- while (body sees n-1)");

    // Do-while (always executes at least once)
    int m = 3;
    do {
        printf("%d ", m--);   // prints 3 2 1
    } while (m > 0);
    puts("← m-- do-while");
}

/* ─── 8. Bit manipulation patterns ─── */

void demo_bit_manipulation(void) {
    puts("\n=== Bit Manipulation Patterns ===");

    uint32_t x = 0b10101010101010101010101010101010U;

    // Pack/unpack using shift-assign
    uint8_t r = 0xDE, g = 0xAD, b = 0xBE;
    uint32_t rgb = 0;
    rgb |= (uint32_t)r << 16;
    rgb |= (uint32_t)g << 8;
    rgb |= (uint32_t)b;
    printf("RGB packed: 0x%06X\n", rgb);

    // Extract components
    uint8_t r2 = (rgb >> 16) & 0xFF;
    uint8_t g2 = (rgb >> 8)  & 0xFF;
    uint8_t b2 =  rgb        & 0xFF;
    assert(r2 == r && g2 == g && b2 == b);

    // Power-of-2 multiply/divide via shift
    int32_t v = 7;
    v <<= 3;   // v *= 8 = 56
    v >>= 1;   // v /= 2 = 28
    printf("7 <<= 3 then >>= 1 → %d\n", v);

    // XOR swap (no temp variable)
    int a = 42, bv = 99;
    a ^= bv;
    bv ^= a;
    a ^= bv;
    printf("XOR swap: a=%d b=%d (were 42, 99)\n", a, bv);
}

int main(void) {
    demo_basic();
    demo_compound_arithmetic();
    demo_compound_bitwise();
    demo_pointer_increment();
    demo_overflow();
    demo_atomic();
    demo_loop_idioms();
    demo_bit_manipulation();
    puts("\nAll demos completed.");
    return 0;
}
```

---

### C Makefile

```makefile
CC      = gcc
CFLAGS  = -std=c11 -Wall -Wextra -Wpedantic -Wsequence-point \
           -fsanitize=address,undefined -g
RELEASE = -O2 -DNDEBUG -march=native

.PHONY: all debug release asm clean

all: debug

debug:
	$(CC) $(CFLAGS) -o prog main.c

release:
	$(CC) $(RELEASE) -o prog_rel main.c

asm:
	$(CC) -O0 -S -fverbose-asm -o main_O0.s main.c
	$(CC) -O2 -S -fverbose-asm -o main_O2.s main.c

clean:
	rm -f prog prog_rel *.s
```

---

### Go Implementation (`go/main.go`)

```go
package main

import (
	"fmt"
	"math"
	"math/bits"
	"sync/atomic"
)

// ─── 1. Basic increment/decrement (statements only) ───

func demoBasic() {
	fmt.Println("\n=== Basic Increment/Decrement ===")

	i := 5
	fmt.Printf("Initial i = %d\n", i)

	i++ // i = 6 — statement, no return value
	fmt.Printf("After i++: %d\n", i)

	i-- // i = 5
	fmt.Printf("After i--: %d\n", i)

	// Cannot do j := i++ in Go — compile error
	// Cannot do ++i or --i in Go — compile error

	// Must use += / -= for all expression contexts
	j := i
	j += 1
	fmt.Printf("j (via j += 1): %d\n", j)
}

// ─── 2. Compound arithmetic assignment ───

func demoCompoundArithmetic() {
	fmt.Println("\n=== Compound Arithmetic Assignment ===")

	x := 100
	x += 25
	fmt.Printf("+= 25 → %d\n", x)  // 125
	x -= 75
	fmt.Printf("-= 75 → %d\n", x)  // 50
	x *= 3
	fmt.Printf("*= 3  → %d\n", x)  // 150
	x /= 5
	fmt.Printf("/= 5  → %d\n", x)  // 30
	x %= 7
	fmt.Printf("%%= 7  → %d\n", x) // 2

	// Go integer division: truncation toward zero
	y := -7
	y /= 2
	fmt.Printf("-7 /= 2 → %d\n", y) // -3

	// Modulo: sign follows dividend
	fmt.Printf("-7 %% 3 = %d\n", -7%3)  // -1
	fmt.Printf("7 %% -3 = %d\n", 7%-3)  // 1

	// Float division
	f := 7.0
	f /= 2.0
	fmt.Printf("7.0 /= 2.0 = %f\n", f) // 3.5
}

// ─── 3. Compound bitwise assignment ───

func demoCompoundBitwise() {
	fmt.Println("\n=== Compound Bitwise Assignment ===")

	var flags uint32 = 0

	const (
		FlagRead  uint32 = 1 << 0
		FlagWrite uint32 = 1 << 1
		FlagExec  uint32 = 1 << 2
	)

	flags |= FlagRead | FlagWrite
	fmt.Printf("After set:    0x%08X\n", flags) // 0x00000003

	flags &^= FlagWrite // Go's bit-clear operator: AND NOT
	fmt.Printf("After clear:  0x%08X\n", flags) // 0x00000001

	flags ^= FlagExec
	fmt.Printf("After toggle: 0x%08X\n", flags) // 0x00000005

	// Note: Go has &^ (AND NOT) which is unique — no equivalent in C/Rust directly
	var mask uint8 = 0xFF
	mask &^= 0x0F // clear lower nibble
	fmt.Printf("0xFF &^= 0x0F → 0x%02X\n", mask) // 0xF0

	// Shifts
	var val uint32 = 1
	val <<= 4
	fmt.Printf("<<= 4 → %d\n", val) // 16
	val >>= 2
	fmt.Printf(">>= 2 → %d\n", val) // 4

	// Arithmetic right shift on signed
	sv := int32(-128)
	sv >>= 2
	fmt.Printf("int32(-128) >>= 2 → %d\n", sv) // -32

	// bits package for bit operations
	n := uint32(0b10101010)
	fmt.Printf("Ones count: %d\n", bits.OnesCount32(n))   // 4
	fmt.Printf("Leading zeros: %d\n", bits.LeadingZeros32(n)) // 24
}

// ─── 4. Overflow behavior ───

func demoOverflow() {
	fmt.Println("\n=== Overflow Behavior ===")

	// Go wraps silently — no UB, no panic
	var u uint8 = 255
	u++
	fmt.Printf("uint8(255)++ = %d (wraps to 0)\n", u) // 0

	var s int8 = 127
	s++
	fmt.Printf("int8(127)++ = %d (wraps to -128)\n", s) // -128

	// For overflow detection, check manually
	var i int8 = 127
	if i == math.MaxInt8 {
		fmt.Println("int8 at max — cannot increment safely")
	}
}

// ─── 5. Atomic increment ───

func demoAtomic() {
	fmt.Println("\n=== Atomic Operations ===")

	var counter int64

	old := atomic.AddInt64(&counter, 1)   // returns new value (not old!)
	fmt.Printf("After atomic +1: counter=%d, returned=%d\n", counter, old)

	atomic.AddInt64(&counter, -1) // decrement atomically

	// Go 1.19+ typed atomics
	var c atomic.Int64
	c.Store(10)
	c.Add(5)
	c.Add(-3)
	fmt.Printf("Typed atomic counter: %d\n", c.Load()) // 12

	// Swap (no += equivalent for swap)
	old2 := c.Swap(100)
	fmt.Printf("Swapped: old=%d, new=%d\n", old2, c.Load())

	// Compare-and-Swap (foundation of lock-free algorithms)
	swapped := c.CompareAndSwap(100, 200)
	fmt.Printf("CAS(100→200): swapped=%v, val=%d\n", swapped, c.Load())
}

// ─── 6. Loop idioms ───

func demoLoopIdioms() {
	fmt.Println("\n=== Loop Idioms ===")

	// Classic forward loop
	fmt.Print("Forward: ")
	for i := 0; i < 5; i++ {
		fmt.Printf("%d ", i)
	}
	fmt.Println()

	// Reverse loop — Go doesn't have i-- in condition, use i -= 1 pattern
	fmt.Print("Reverse: ")
	for i := 4; i >= 0; i-- {
		fmt.Printf("%d ", i)
	}
	fmt.Println()

	// Index-based slice iteration
	data := []int{10, 20, 30, 40, 50}
	for i := 0; i < len(data); i++ {
		data[i] += i * 2 // compound assign on slice element
	}
	fmt.Printf("Modified slice: %v\n", data) // [10 22 34 46 58]

	// Range is idiomatic Go
	sum := 0
	for _, v := range data {
		sum += v
	}
	fmt.Printf("Sum: %d\n", sum)

	// Infinite loop with break (no do-while in Go)
	n := 3
	for {
		fmt.Printf("n=%d ", n)
		n--
		if n <= 0 {
			break
		}
	}
	fmt.Println()
}

// ─── 7. Custom type with method-based increment ───

type ByteAddr struct {
	offset uint64
	base   uint64
}

func (a *ByteAddr) Inc(n uint64) { a.offset += n }
func (a *ByteAddr) Dec(n uint64) { a.offset -= n }
func (a *ByteAddr) Abs() uint64  { return a.base + a.offset }

func demoCustomType() {
	fmt.Println("\n=== Custom Type (no operator overloading in Go) ===")

	addr := ByteAddr{base: 0x1000, offset: 0}
	addr.Inc(4)
	addr.Inc(8)
	addr.Dec(2)
	fmt.Printf("Effective address: 0x%X\n", addr.Abs()) // 0x100A
}

// ─── 8. Bit packing / unpacking ───

func demoBitPack() {
	fmt.Println("\n=== Bit Packing / Unpacking ===")

	// Pack RGB into uint32
	r, g, b := uint32(0xDE), uint32(0xAD), uint32(0xBE)
	rgb := uint32(0)
	rgb |= r << 16
	rgb |= g << 8
	rgb |= b
	fmt.Printf("Packed RGB: 0x%06X\n", rgb) // 0xDEADBE

	// Extract
	r2 := (rgb >> 16) & 0xFF
	g2 := (rgb >> 8) & 0xFF
	b2 := rgb & 0xFF
	if r2 != r || g2 != g || b2 != b {
		panic("pack/unpack mismatch")
	}
	fmt.Printf("Extracted: R=0x%02X G=0x%02X B=0x%02X\n", r2, g2, b2)

	// XOR swap
	a, bv := 42, 99
	a ^= bv
	bv ^= a
	a ^= bv
	fmt.Printf("XOR swap: a=%d b=%d\n", a, bv) // 99, 42
}

func main() {
	demoBasic()
	demoCompoundArithmetic()
	demoCompoundBitwise()
	demoOverflow()
	demoAtomic()
	demoLoopIdioms()
	demoCustomType()
	demoBitPack()
	fmt.Println("\nAll demos completed.")
}
```

---

### Go module file (`go/go.mod`)

```
module increment_guide

go 1.21
```

---

### Rust Implementation (`rust/src/main.rs`)

```rust
use std::sync::atomic::{AtomicI32, AtomicU64, Ordering};
use std::sync::Arc;
use std::ops::{AddAssign, SubAssign, MulAssign, DivAssign, RemAssign,
               BitAndAssign, BitOrAssign, BitXorAssign, ShlAssign, ShrAssign};

// ─── 1. Basic mutation — Rust has no ++ or -- ───

fn demo_basic() {
    println!("\n=== Basic Mutation (no ++ in Rust) ===");

    let mut i: i32 = 5;
    println!("Initial i = {i}");

    i += 1;
    println!("After i += 1: {i}");  // 6

    i -= 1;
    println!("After i -= 1: {i}");  // 5

    // Idiomatic: use += 1 everywhere
    // No pre/post distinction — it's just i += 1, result not captured
}

// ─── 2. Compound arithmetic assignment ───

fn demo_compound_arithmetic() {
    println!("\n=== Compound Arithmetic Assignment ===");

    let mut x: i32 = 100;
    x += 25;  println!("+= 25 → {x}");   // 125
    x -= 75;  println!("-= 75 → {x}");   // 50
    x *= 3;   println!("*= 3  → {x}");   // 150
    x /= 5;   println!("/= 5  → {x}");   // 30
    x %= 7;   println!("%= 7  → {x}");   // 2

    // Truncation toward zero
    let mut y: i32 = -7;
    y /= 2;
    println!("-7 /= 2 → {y}");  // -3

    // Modulo: sign follows dividend (same as C and Go)
    println!("-7 % 3 = {}", -7i32 % 3);   // -1
    println!("7 % -3 = {}", 7i32 % -3);   // 1

    // Float
    let mut f: f64 = 7.0;
    f /= 2.0;
    println!("7.0 /= 2.0 = {f}");  // 3.5
}

// ─── 3. Compound bitwise assignment ───

fn demo_compound_bitwise() {
    println!("\n=== Compound Bitwise Assignment ===");

    const FLAG_READ:  u32 = 1 << 0;
    const FLAG_WRITE: u32 = 1 << 1;
    const FLAG_EXEC:  u32 = 1 << 2;

    let mut flags: u32 = 0;

    flags |= FLAG_READ | FLAG_WRITE;
    println!("After set:    0x{flags:08X}");  // 0x00000003

    flags &= !FLAG_WRITE;   // Rust: ! is bitwise NOT for integers
    println!("After clear:  0x{flags:08X}");  // 0x00000001

    flags ^= FLAG_EXEC;
    println!("After toggle: 0x{flags:08X}");  // 0x00000005

    // Shift assign
    let mut val: u32 = 1;
    val <<= 4;  println!("<<= 4 → {val}");   // 16
    val >>= 2;  println!(">>= 2 → {val}");   // 4

    // Signed arithmetic right shift
    let mut sv: i32 = -128;
    sv >>= 2;
    println!("i32(-128) >>= 2 → {sv}");  // -32 (arithmetic, defined)

    // Unsigned logical right shift
    let mut uv: u32 = 0xFFFFFFFF;
    uv >>= 4;
    println!("u32(0xFFFFFFFF) >>= 4 → 0x{uv:08X}");  // 0x0FFFFFFF (logical)
}

// ─── 4. Overflow semantics ───

fn demo_overflow() {
    println!("\n=== Overflow Semantics ===");

    let mut x: u8 = 255;
    // x += 1;  // panics in debug, wraps in release

    // Explicit wrapping
    x = x.wrapping_add(1);
    println!("u8(255).wrapping_add(1) = {x}");   // 0

    // Saturating
    let mut s: i8 = 120;
    s = s.saturating_add(100);
    println!("i8(120).saturating_add(100) = {s}");  // 127 (i8::MAX)

    // Checked
    let checked = 127i8.checked_add(1);
    println!("i8(127).checked_add(1) = {:?}", checked);  // None

    // Overflowing (returns (value, did_overflow))
    let (val, overflowed) = 127i8.overflowing_add(1);
    println!("i8(127).overflowing_add(1) = ({val}, {overflowed})");  // (-128, true)

    // Wrapping shift (prevents panic on shift >= bit_width)
    let shift_val: u32 = 1;
    let result = shift_val.wrapping_shl(32);
    println!("u32(1).wrapping_shl(32) = {result}");  // 1 (32 % 32 = 0)
}

// ─── 5. Operator overloading via traits ───

#[derive(Debug, Clone, Copy, PartialEq)]
struct Vec2 {
    x: f64,
    y: f64,
}

impl AddAssign for Vec2 {
    fn add_assign(&mut self, rhs: Self) {
        self.x += rhs.x;
        self.y += rhs.y;
    }
}

impl SubAssign for Vec2 {
    fn sub_assign(&mut self, rhs: Self) {
        self.x -= rhs.x;
        self.y -= rhs.y;
    }
}

impl MulAssign<f64> for Vec2 {
    fn mul_assign(&mut self, scalar: f64) {
        self.x *= scalar;
        self.y *= scalar;
    }
}

impl DivAssign<f64> for Vec2 {
    fn div_assign(&mut self, scalar: f64) {
        assert!(scalar != 0.0, "division by zero");
        self.x /= scalar;
        self.y /= scalar;
    }
}

fn demo_operator_overload() {
    println!("\n=== Operator Overloading (AddAssign etc.) ===");

    let mut a = Vec2 { x: 1.0, y: 2.0 };
    let b = Vec2 { x: 3.0, y: 4.0 };

    a += b;
    println!("After +=: {:?}", a);   // Vec2 { x: 4.0, y: 6.0 }

    a -= b;
    println!("After -=: {:?}", a);   // Vec2 { x: 1.0, y: 2.0 }

    a *= 2.0;
    println!("After *= 2.0: {:?}", a);  // Vec2 { x: 2.0, y: 4.0 }

    a /= 2.0;
    println!("After /= 2.0: {:?}", a);  // Vec2 { x: 1.0, y: 2.0 }
}

// ─── 6. All compound-assign traits implemented ───

#[derive(Debug, Clone, Copy)]
struct Bits(u32);

impl AddAssign     for Bits { fn add_assign(&mut self, r: Self) { self.0 += r.0; } }
impl SubAssign     for Bits { fn sub_assign(&mut self, r: Self) { self.0 -= r.0; } }
impl MulAssign     for Bits { fn mul_assign(&mut self, r: Self) { self.0 *= r.0; } }
impl DivAssign     for Bits { fn div_assign(&mut self, r: Self) { self.0 /= r.0; } }
impl RemAssign     for Bits { fn rem_assign(&mut self, r: Self) { self.0 %= r.0; } }
impl BitAndAssign  for Bits { fn bitand_assign(&mut self, r: Self) { self.0 &= r.0; } }
impl BitOrAssign   for Bits { fn bitor_assign(&mut self, r: Self) { self.0 |= r.0; } }
impl BitXorAssign  for Bits { fn bitxor_assign(&mut self, r: Self) { self.0 ^= r.0; } }
impl ShlAssign<u32> for Bits { fn shl_assign(&mut self, r: u32) { self.0 <<= r; } }
impl ShrAssign<u32> for Bits { fn shr_assign(&mut self, r: u32) { self.0 >>= r; } }

fn demo_all_assign_traits() {
    println!("\n=== All Compound-Assign Traits on Custom Type ===");

    let mut b = Bits(0b1010_1010);
    println!("Initial: {:08b}", b.0);

    b &= Bits(0b1111_0000); println!("&=: {:08b}", b.0);    // 10100000
    b |= Bits(0b0000_1111); println!("|=: {:08b}", b.0);    // 10101111
    b ^= Bits(0b1100_1100); println!("^=: {:08b}", b.0);    // 00100011
    b <<= 2;                 println!("<<=2: {:08b}", b.0);  // 10001100
    b >>= 1;                 println!(">>=1: {:08b}", b.0);  // 01000110
}

// ─── 7. Atomic mutation ───

fn demo_atomic() {
    println!("\n=== Atomic Mutation ===");

    let counter = Arc::new(AtomicI32::new(0));
    let mut handles = vec![];

    for _ in 0..4 {
        let c = Arc::clone(&counter);
        handles.push(std::thread::spawn(move || {
            for _ in 0..10_000 {
                c.fetch_add(1, Ordering::Relaxed);    // atomic +=1
            }
        }));
    }

    for h in handles { h.join().unwrap(); }
    println!("Atomic counter: {}", counter.load(Ordering::SeqCst));  // 40000

    // All atomic compound-equivalent operations
    let x = AtomicU64::new(0xFF);
    x.fetch_and(0x0F, Ordering::SeqCst);   // &=
    x.fetch_or(0xF0, Ordering::SeqCst);    // |=
    x.fetch_xor(0xAA, Ordering::SeqCst);   // ^=
    x.fetch_add(1, Ordering::SeqCst);      // +=
    x.fetch_sub(1, Ordering::SeqCst);      // -=
    println!("Atomic bitwise result: 0x{:02X}", x.load(Ordering::SeqCst));
}

// ─── 8. Raw pointer arithmetic (unsafe) ───

fn demo_raw_pointer() {
    println!("\n=== Raw Pointer Arithmetic (unsafe) ===");

    let arr = [10i32, 20, 30, 40, 50];
    let mut ptr = arr.as_ptr();
    let end = unsafe { ptr.add(arr.len()) };

    print!("Elements: ");
    unsafe {
        while ptr != end {
            print!("{} ", *ptr);
            ptr = ptr.add(1);  // ptr++ equivalent
        }
    }
    println!();

    // Pointer difference (like ptr subtraction in C)
    let base = arr.as_ptr();
    let mid  = unsafe { base.add(2) };
    let diff = unsafe { mid.offset_from(base) };
    println!("Offset of mid from base: {diff}");  // 2
}

// ─── 9. Loop idioms ───

fn demo_loop_idioms() {
    println!("\n=== Loop Idioms ===");

    // Forward loop
    print!("Forward: ");
    for i in 0..5 { print!("{i} "); }
    println!();

    // Reverse loop
    print!("Reverse: ");
    for i in (0..5).rev() { print!("{i} "); }
    println!();

    // Inclusive range
    print!("Inclusive 0..=4: ");
    for i in 0..=4 { print!("{i} "); }
    println!();

    // While-let with counter
    let mut n = 5;
    while n > 0 {
        print!("{n} ");
        n -= 1;
    }
    println!();

    // Step_by
    print!("Step by 2: ");
    for i in (0..10).step_by(2) { print!("{i} "); }
    println!();

    // Sum with accumulator
    let mut sum = 0i64;
    for x in 1..=100 { sum += x; }
    println!("Sum 1..=100 = {sum}");  // 5050

    // Enumerate (index + value)
    let mut data = vec![10, 20, 30, 40, 50];
    for (i, v) in data.iter_mut().enumerate() {
        *v += (i as i32) * 5;   // compound assign through mutable reference
    }
    println!("Modified: {:?}", data);   // [10, 25, 40, 55, 70]
}

// ─── 10. Bit packing ───

fn demo_bit_pack() {
    println!("\n=== Bit Packing / Unpacking ===");

    let (r, g, b) = (0xDEu32, 0xADu32, 0xBEu32);
    let mut rgb: u32 = 0;
    rgb |= r << 16;
    rgb |= g << 8;
    rgb |= b;
    println!("Packed: 0x{rgb:06X}");  // 0xDEADBE

    let r2 = (rgb >> 16) & 0xFF;
    let g2 = (rgb >> 8) & 0xFF;
    let b2 = rgb & 0xFF;
    assert_eq!((r, g, b), (r2, g2, b2));
    println!("Extracted: R=0x{r2:02X} G=0x{g2:02X} B=0x{b2:02X}");

    // XOR swap
    let (mut a, mut bv) = (42u32, 99u32);
    a ^= bv;
    bv ^= a;
    a ^= bv;
    println!("XOR swap: a={a} b={bv}");  // 99, 42

    // Count bits using leading/trailing zeros
    let n: u32 = 0b00101100;
    println!("Leading zeros: {}", n.leading_zeros());   // 26
    println!("Trailing zeros: {}", n.trailing_zeros()); // 2
    println!("Set bits: {}", n.count_ones());           // 3
}

fn main() {
    demo_basic();
    demo_compound_arithmetic();
    demo_compound_bitwise();
    demo_overflow();
    demo_operator_overload();
    demo_all_assign_traits();
    demo_atomic();
    demo_raw_pointer();
    demo_loop_idioms();
    demo_bit_pack();
    println!("\nAll demos completed.");
}
```

---

### Rust `Cargo.toml`

```toml
[package]
name = "increment_guide"
version = "0.1.0"
edition = "2021"

[[bin]]
name = "increment_guide"
path = "src/main.rs"
```

---

## 17. Test, Fuzz & Benchmark Steps

### Build and run

```bash
# C
cd c/
make debug
./prog
make asm          # generates main_O0.s and main_O2.s

# Go
cd go/
go mod tidy
go run main.go
go build -o prog .
go vet ./...

# Rust
cd rust/
cargo run
cargo build --release
cargo run --release
```

### Sanitizers

```bash
# C: UBSan + ASan
gcc -std=c11 -Wall -Wsequence-point \
    -fsanitize=address,undefined,integer \
    -fno-omit-frame-pointer -g \
    -o prog main.c
./prog

# Clang with full suite
clang -std=c11 -Wall \
    -fsanitize=address,undefined,integer,bounds \
    -o prog main.c

# Go race detector
go run -race main.go
go test -race ./...

# Rust address sanitizer (nightly)
RUSTFLAGS="-Z sanitizer=address" \
    cargo +nightly run --target x86_64-unknown-linux-gnu
```

### Testing

```bash
# C: use a simple test harness
gcc -std=c11 -DTEST -fsanitize=address,undefined -o test_prog main.c
./test_prog

# Go: table-driven tests
# Create main_test.go with TestXxx functions
go test -v -count=1 ./...
go test -cover ./...

# Rust: built-in test framework
cargo test -- --nocapture
cargo test --release
```

### Fuzzing

```bash
# Go fuzzing (1.18+)
# Create FuzzXxx functions in *_test.go
go test -fuzz=FuzzCompoundOps -fuzztime=30s

# Rust fuzzing with cargo-fuzz
cargo install cargo-fuzz
cargo fuzz init
cargo fuzz add fuzz_ops
cargo fuzz run fuzz_ops -- -max_total_time=60
```

### Benchmarking

```bash
# C: use clock_gettime or perf
perf stat ./prog
perf record -g ./prog
perf report

# Go benchmarks
# Create BenchmarkXxx in *_test.go
go test -bench=. -benchmem -benchtime=5s ./...
go test -bench=BenchmarkCompound -cpuprofile cpu.prof ./...
go tool pprof cpu.prof

# Rust
cargo bench   # requires [[bench]] section + criterion
cargo install hyperfine
hyperfine './target/release/increment_guide' --warmup 3
```

### Assembly inspection

```bash
# C
objdump -d -M intel ./prog | grep -A 10 "demo_basic"
gobjdump -d -M intel prog | grep -A 20 "<demo_basic>"

# Go
go tool objdump -s "main\.demoBasic" ./prog

# Rust
objdump -d -M intel ./target/release/increment_guide | grep -A 20 "demo_basic"
cargo rustc -- --emit=asm && cat target/debug/deps/*.s | grep -A 20 "demo_basic"
```

---

## 18. References

### Standards

- **C11 Standard**: ISO/IEC 9899:2011 — §6.5.2.4 (Postfix inc/dec), §6.5.3.1 (Prefix inc/dec), §6.5.16 (Assignment operators), §6.5 (Sequence points / evaluation order)
- **C11 Atomics**: §7.17 — `_Atomic`, `memory_order`, `atomic_fetch_add`
- **Go Specification**: https://go.dev/ref/spec#IncDec_statements — `IncDecStmt = Expression ( "++" | "--" )`
- **Go Specification**: https://go.dev/ref/spec#Assign_op — Compound assignment operators
- **Rust Reference**: https://doc.rust-lang.org/reference/expressions/operator-expr.html#compound-assignment-expressions
- **Rust `std::ops`**: https://doc.rust-lang.org/std/ops/index.html — `AddAssign`, `SubAssign`, etc.

### Deep reading

- **GCC UBSan documentation**: https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html
- **Clang UBSan**: https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html
- **LLVM Language Reference**: https://llvm.org/docs/LangRef.html#integer-operations
- **Intel® 64 and IA-32 Architectures Software Developer's Manual** Vol 2: `INC`, `DEC`, `ADD`, `XADD`, `LOCK` prefix
- **Rust Atomics and Locks** (Mara Bos): https://marabos.nl/atomics/ — definitive Rust atomics reference
- **"What Every C Programmer Should Know About Undefined Behavior"** — LLVM Blog (3-part series)
- **Go memory model**: https://go.dev/ref/mem — guarantees for concurrent access
- **Rust memory model** (ongoing): https://github.com/rust-lang/unsafe-code-guidelines

### Security implications

- **CWE-190**: Integer Overflow or Wraparound — https://cwe.mitre.org/data/definitions/190.html
- **CWE-191**: Integer Underflow — https://cwe.mitre.org/data/definitions/191.html
- **CWE-362**: Race Condition (concurrent mutation without synchronization) — https://cwe.mitre.org/data/definitions/362.html

---

## Next 3 Steps

1. **Compile all three implementations with all sanitizers enabled** (`-fsanitize=address,undefined,integer` for C; `-race` for Go; `RUSTFLAGS=-Zsanitizer=address` for Rust) and confirm clean output — internalize the tooling muscle memory for catching these bugs in CI.

2. **Inspect the assembly output** at `-O0` and `-O2` for the `++i` vs `i++` demo in C, then compare the Go and Rust output at optimization level 3 — confirm the compiler collapses them to identical `INC`/`ADD` instructions when the result is unused; understand exactly when and why they diverge.

3. **Write a concurrent counter** using all three languages' atomic primitives with `Relaxed` vs `SeqCst` ordering, run under TSan (C/Rust) and `-race` (Go), and benchmark the throughput difference between the two orderings under 8-thread contention — this will give you a production-grade understanding of the cost of strong memory ordering vs. correctness trade-offs.
```

