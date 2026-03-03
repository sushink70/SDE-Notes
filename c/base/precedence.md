# Operator Precedence: A Comprehensive Guide Across C, C++, Rust, and Go

Precedence is not just a syntactic rule — it is the **grammar of computation**. Misunderstanding it causes subtle bugs that survive code review. Mastering it sharpens your ability to read code like a compiler.

---

## Mental Model First: How Precedence Works

Before any table, internalize this:

> **Precedence determines grouping. Associativity determines direction. Neither determines evaluation order.**

These three concepts are distinct and frequently conflated even by experienced engineers.

- **Precedence**: Which operator binds more tightly to its operands (`*` before `+`)
- **Associativity**: When operators have equal precedence, which side groups first (left or right)
- **Evaluation order**: Which subexpression is *computed* first — largely unspecified in C/C++, defined in Rust/Go

```
a + b * c        →  a + (b * c)          [precedence]
a - b - c        →  (a - b) - c          [left associativity]
a = b = c        →  a = (b = c)          [right associativity]
f() + g()        →  undefined order      [evaluation order, C/C++]
```

---

## C — Operator Precedence Table

C has **15 precedence levels**. Higher number = lower precedence.

| Level | Operators | Description | Associativity |
|-------|-----------|-------------|---------------|
| 1 | `()` `[]` `->` `.` `++` `--` (postfix) | Postfix / call / member | Left → Right |
| 2 | `++` `--` (prefix) `+` `-` (unary) `!` `~` `*` (deref) `&` (addr) `sizeof` `_Alignof` `(type)` | Prefix unary / cast | Right → Left |
| 3 | `*` `/` `%` | Multiplicative | Left → Right |
| 4 | `+` `-` | Additive | Left → Right |
| 5 | `<<` `>>` | Bitwise shift | Left → Right |
| 6 | `<` `<=` `>` `>=` | Relational | Left → Right |
| 7 | `==` `!=` | Equality | Left → Right |
| 8 | `&` | Bitwise AND | Left → Right |
| 9 | `^` | Bitwise XOR | Left → Right |
| 10 | `\|` | Bitwise OR | Left → Right |
| 11 | `&&` | Logical AND | Left → Right |
| 12 | `\|\|` | Logical OR | Left → Right |
| 13 | `?:` | Ternary | Right → Left |
| 14 | `=` `+=` `-=` `*=` `/=` `%=` `<<=` `>>=` `&=` `^=` `\|=` | Assignment | Right → Left |
| 15 | `,` | Comma | Left → Right |

### Critical C Traps

**Trap 1: Bitwise operators have lower precedence than comparison**
```c
// Intent: (x & MASK) == VALUE
// Written: x & MASK == VALUE
// Parsed:  x & (MASK == VALUE)   ← BUG

if (x & 0xFF == 0x1A) { }   // WRONG
if ((x & 0xFF) == 0x1A) { } // CORRECT
```

**Trap 2: `->` vs `*` dereference**
```c
struct Node *p;
*p.data    // parsed as *(p.data)  — WRONG if p is a pointer
(*p).data  // correct manual dereference
p->data    // idiomatic and correct
```

**Trap 3: Shift and arithmetic mixing**
```c
int x = 1 + 2 << 3;   // parsed as (1 + 2) << 3 = 24
// shift has lower precedence than +
```

**Trap 4: Comma operator (the silent killer)**
```c
int a = (1, 2, 3);  // a = 3; evaluates all, returns last
// In function args, comma is a SEPARATOR, not the comma operator
f(a, b)   // two args
f((a, b)) // one arg: value of b
```

**Trap 5: Undefined behavior with evaluation order**
```c
int i = 0;
int a = i++ + i++;   // UNDEFINED BEHAVIOR in C
// The compiler may evaluate either i++ first
```

---

## C++ — Precedence Table (Superset of C)

C++ inherits all C operators and adds several critical new ones.

| Level | Operators | Description | Associativity |
|-------|-----------|-------------|---------------|
| 1 | `::` | Scope resolution | Left → Right |
| 2 | `()` `[]` `->` `.` `++` `--` (postfix) `typeid` `const_cast` `dynamic_cast` `reinterpret_cast` `static_cast` | Postfix | Left → Right |
| 3 | `++` `--` (prefix) `+` `-` (unary) `!` `~` `*` `&` `sizeof` `co_await` `new` `new[]` `delete` `delete[]` `(type)` | Prefix unary | Right → Left |
| 4 | `.*` `->*` | Pointer-to-member | Left → Right |
| 5 | `*` `/` `%` | Multiplicative | Left → Right |
| 6 | `+` `-` | Additive | Left → Right |
| 7 | `<<` `>>` | Shift | Left → Right |
| 8 | `<=>` | Three-way comparison (C++20) | Left → Right |
| 9 | `<` `<=` `>` `>=` | Relational | Left → Right |
| 10 | `==` `!=` | Equality | Left → Right |
| 11 | `&` | Bitwise AND | Left → Right |
| 12 | `^` | Bitwise XOR | Left → Right |
| 13 | `\|` | Bitwise OR | Left → Right |
| 14 | `&&` | Logical AND | Left → Right |
| 15 | `\|\|` | Logical OR | Left → Right |
| 16 | `?:` `throw` `co_yield` `=` `+=` `-=` `*=` `/=` `%=` `<<=` `>>=` `&=` `^=` `\|=` | Ternary / throw / assign | Right → Left |
| 17 | `,` | Comma | Left → Right |

### C++-Specific Critical Notes

**`::` is the highest precedence operator** — scope resolution binds tighter than everything.
```cpp
// Class::member access always resolves before any other operation
std::cout << Foo::value + 1;  // (Foo::value) + 1
```

**Pointer-to-member operators `.*` and `->*`**
```cpp
struct Foo { int x; };
int Foo::*mp = &Foo::x;

Foo obj;
obj.*mp;    // access member via pointer-to-member
// Precedence: LOWER than postfix, HIGHER than multiplicative

Foo *ptr = &obj;
ptr->*mp;  // pointer-to-member through pointer
```

**`<=>` spaceship operator (C++20)** sits between shift and relational:
```cpp
auto result = a <=> b;
// Returns std::strong_ordering / std::weak_ordering / std::partial_ordering
```

**Overloaded operators and precedence:**
Operator overloading **does not change precedence**. If you overload `+` for a custom type, it still has the same precedence as built-in `+`. This is a powerful guarantee.

**The `new` / `delete` precedence trap:**
```cpp
delete p + 1;   // parsed as delete (p + 1) — likely a bug
// new[] and delete[] have the same precedence level as other prefix unary
```

**Template disambiguation and `>`:**
```cpp
// Classic issue pre-C++11:
vector<vector<int>>  // C++11+: OK
vector<vector<int> > // C++03 required space: >> was shift operator
```

---

## Rust — Operator Precedence

Rust has a cleaner, more deliberate precedence system. The compiler is stricter and will **refuse to compile ambiguous chains** in some contexts (e.g., mixing `&&` and `||` without explicit parentheses is allowed but strongly discouraged by `clippy`).

| Level | Operators | Description | Associativity |
|-------|-----------|-------------|---------------|
| 1 | Method calls `.method()`, field access `.field`, index `[]`, `?` | Postfix | Left → Right |
| 2 | Unary `-` `!` `*` (deref) `&` `&mut` | Prefix unary | Right → Left |
| 3 | `as` | Type cast | Left → Right |
| 4 | `*` `/` `%` | Multiplicative | Left → Right |
| 5 | `+` `-` | Additive | Left → Right |
| 6 | `<<` `>>` | Shift | Left → Right |
| 7 | `&` | Bitwise AND | Left → Right |
| 8 | `^` | Bitwise XOR | Left → Right |
| 9 | `\|` | Bitwise OR | Left → Right |
| 10 | `==` `!=` `<` `>` `<=` `>=` | Comparison | Require parens (non-associative) |
| 11 | `&&` | Logical AND | Left → Right |
| 12 | `\|\|` | Logical OR | Left → Right |
| 13 | `..` `..=` | Range | Non-associative |
| 14 | `=` `+=` `-=` `*=` `/=` `%=` `<<=` `>>=` `&=` `^=` `\|=` | Assignment | Right → Left |
| 15 | `return` `break` `continue` `\|...\|` (closure) | Control flow expressions | — |

### Rust's Unique Design Decisions

**Comparisons are non-associative** — Rust refuses to compile chained comparisons without parens:
```rust
// This DOES NOT COMPILE in Rust:
let ok = 1 < 2 < 3;   // error: comparison operators cannot be chained

// You must write:
let ok = 1 < 2 && 2 < 3;

// Contrast with Python which handles chaining mathematically
// Rust prioritizes explicitness over cleverness
```

**`as` has higher precedence than arithmetic** — this is a frequent source of bugs:
```rust
let x: i32 = -1;
let y = x as u32 + 1;     // (x as u32) + 1 = 4294967296 (wraps!)
// NOT: x as (u32 + 1) — that's nonsensical but the point is `as` binds tight

// The danger: cast happens BEFORE addition
let bits = value & 0xFF as u64;   // parsed as value & (0xFF as u64) — OK here
let bits = value & mask as u64;   // parsed as value & (mask as u64)
```

**`?` operator (question mark) has postfix precedence — the highest:**
```rust
fn read() -> Result<i32, Error> {
    let val = parse_number()?.abs();  // ? applies to parse_number(), then .abs()
    // Equivalent to: (parse_number()?).abs()
}
```

**`*` deref in Rust vs C:**
In Rust, dereferencing interacts with the borrow checker, not just raw memory. The precedence is the same (prefix unary), but the semantic weight is heavier:
```rust
let mut v = vec![1, 2, 3];
let r = &mut v[0];
*r += 1;   // deref then add-assign; r has type &mut i32
```

**Range operators `..` and `..=` are non-associative:**
```rust
// Cannot chain ranges:
let r = 1..5..10;  // COMPILE ERROR

// But ranges are expressions with their own type:
let r: std::ops::Range<i32> = 1..10;
for i in 0..n { }         // exclusive
for i in 0..=n { }        // inclusive
```

**Closures have the lowest precedence** (after assignment):
```rust
let add = |x, y| x + y;
// The entire `x + y` is the body — `+` binds tighter than `|...|`

let f = |x| x * 2 + 1;   // body is: x * 2 + 1, not x * (2 + 1)
```

**Rust enforces overflow behavior by precedence rules of semantics:**
```rust
let x: u8 = 200u8 + 100u8;   // panics in debug, wraps in release
// No precedence issue, but worth noting Rust's stance on arithmetic safety
```

---

## Go — Operator Precedence

Go has the **simplest and most minimal** precedence system of the four languages. This is a deliberate design choice by the Go team for readability and predictability.

| Level | Operators | Description | Associativity |
|-------|-----------|-------------|---------------|
| 5 (highest) | `*` `/` `%` `<<` `>>` `&` `&^` | Multiplicative + bitwise | Left → Right |
| 4 | `+` `-` `\|` `^` | Additive + bitwise OR/XOR | Left → Right |
| 3 | `==` `!=` `<` `<=` `>` `>=` | Comparison | Left → Right |
| 2 | `&&` | Logical AND | Left → Right |
| 1 (lowest) | `\|\|` | Logical OR | Left → Right |

Unary operators (`+` `-` `!` `^` `*` `&` `<-`) have higher precedence than all binary operators.

### Go's Radical Simplicity

Go uses **5 binary precedence levels** — far fewer than C/C++/Rust. This is intentional.

**`&^` is Go's unique bit-clear (AND NOT) operator:**
```go
x &^ y   // clears bits in x where y has 1s
// Equivalent to x & (^y) in C
// Precedence: same level as * / % << >> &

mask := 0xFF
x &^ mask   // clear lower 8 bits of x
```

**Shifts are at level 5 (highest binary)** — same level as `*`:
```go
x + y << 2   // parsed as x + (y << 2)  — same as C/C++/Rust
1 << n - 1   // parsed as 1 << (n - 1)  — CAREFUL: shift binds tight in Go
             // In C this would be (1 << n) - 1
```

Wait — this is actually **different from C**. In C, `<<` has lower precedence than `+`. In Go, `<<` has **higher** precedence than `+`. This is a critical cross-language trap:

```c
// C:
1 << n - 1   →  1 << (n - 1)   // NO — in C: (1 << n) - 1
             // Because in C: shift (level 5) < additive (level 4 from top)
```

Actually let me be precise here. In C, `+` is level 4 and `<<` is level 5 (lower), so `+` binds tighter:
```
C:    1 << n - 1   → 1 << (n - 1)   // n-1 computed first, then shift
Go:   1 << n - 1   → (1 << n) - 1   // shift computed first, then subtract
```

This is one of the most dangerous cross-language traps if you write both C and Go.

**No ternary operator in Go.** This is a deliberate omission:
```go
// C/C++: x = cond ? a : b
// Go: you must write:
var x int
if cond {
    x = a
} else {
    x = b
}

// Or as a function (common pattern):
// There is no inline ternary in Go by design
```

**Go's `<-` channel operator:**
```go
ch <- value   // send to channel (binary, low precedence via statement context)
<-ch          // receive from channel (unary, highest unary precedence)

// In expressions:
x = <-ch + 1   // receive from ch, then add 1
               // unary <- has highest precedence
```

**No comma operator in Go.** Go's `,` is only a separator (function args, multi-assignment), never an expression:
```go
// This is multi-assignment:
a, b = b, a   // simultaneous swap — not comma operator

// Go evaluates the right side fully before assigning left side
// This is DEFINED behavior, unlike C
```

---

## Cross-Language Comparison: The Most Dangerous Differences

### 1. Shift Operator Precedence

| Language | `1 + 2 << 3` parses as | Result |
|----------|------------------------|--------|
| C | `(1 + 2) << 3` | 24 |
| C++ | `(1 + 2) << 3` | 24 |
| Rust | `1 + (2 << 3)` | 17 |
| Go | `1 + (2 << 3)` | 17 |

Rust and Go give shift **higher** precedence than addition. C and C++ do the opposite.

### 2. Bitwise vs Comparison

| Language | `a & b == c` parses as |
|----------|------------------------|
| C | `a & (b == c)` — TRAP |
| C++ | `a & (b == c)` — TRAP |
| Rust | `(a & b) == c` — correct intent |
| Go | `(a & b) == c` — correct intent |

Rust and Go fixed this historical C mistake. In Rust and Go, bitwise AND has **higher** precedence than `==`. In C/C++, it's the opposite.

### 3. Chained Comparisons

| Language | `1 < x < 10` behavior |
|----------|----------------------|
| C | `(1 < x) < 10` — always true (0 or 1 < 10) |
| C++ | `(1 < x) < 10` — always true |
| Rust | **COMPILE ERROR** — non-associative |
| Go | `(1 < x) < 10` — compile error (bool < int invalid) |

### 4. Assignment as Expression

| Language | `if (x = f())` | Notes |
|----------|----------------|-------|
| C | Legal, common idiom | Compiler warning with `=` in condition |
| C++ | Legal, common idiom | Same |
| Rust | Assignment returns `()`, so `if (x = f())` won't compile cleanly | By design |
| Go | `=` is a statement, not expression | Cannot use in `if` condition |

### 5. The `!` Operator on Integers

| Language | `!x` where x is integer |
|----------|--------------------------|
| C | Logical NOT — returns 0 or 1 |
| C++ | Same, but overloadable |
| Rust | **Bitwise NOT** on integers — same as `~` in C |
| Go | `!` only works on bool; `^` is bitwise NOT for integers |

```rust
// Rust:
let x: u8 = 0b1010_1010;
let y = !x;   // 0b0101_0101 — BITWISE NOT, not logical not
let b: bool = true;
let nb = !b;  // false — logical not for bool
```

```go
// Go:
var x uint8 = 0b10101010
y := ^x    // bitwise NOT: 0b01010101
b := true
nb := !b   // logical NOT
```

---

## Deep Concepts: Beyond the Table

### Sequence Points and Evaluation Order (C/C++)

C/C++ have **undefined behavior** when you modify a variable twice between sequence points, or read and modify it without a sequence point between:

```c
// UNDEFINED BEHAVIOR — classic examples:
i = i++;            // modifying i twice
a[i] = i++;         // read and modify i
f(i++, i++)         // order of argument evaluation unspecified

// DEFINED (sequence points exist):
i = 0; j = i++;     // semicolons are sequence points
x = (y = 5, y + 1); // comma operator introduces sequence point
```

C++17 tightened some of these rules. Specifically, in `a = b`, `b` is now sequenced before `a`. And in `a.b`, `a` is sequenced before `b`. But function argument evaluation is still unsequenced.

### Rust's Guaranteed Evaluation Order

Rust specifies that expressions are evaluated **left-to-right**:
```rust
fn f() -> i32 { println!("f"); 1 }
fn g() -> i32 { println!("g"); 2 }

let x = f() + g();  // Always prints "f" then "g"
                    // This is GUARANTEED in Rust
```

### Go's Defined Order

Go specifies operands are evaluated left-to-right within a single expression. But function arguments are evaluated in the order they appear before the call is made:
```go
// In assignments with multiple values on both sides:
a[i], b[j] = c[k], d[l]
// Right side is evaluated left-to-right first, then assignment occurs
// This is why swap works: a, b = b, a
```

---

## Idiomatic Rules for Each Language

### C
- **Always parenthesize** bitwise operations mixed with comparisons: `(x & mask) == value`
- Never rely on comma operator except in `for` loops
- Use `-Wall -Wextra` — the compiler will catch many precedence surprises

### C++
- Same as C, plus: be explicit with `.*` and `->*`
- With `<=>`, always store result in `auto` and compare to `std::strong_ordering` values
- Be very intentional with overloaded operators — precedence is fixed, but semantics can mislead readers

### Rust
- Trust the compiler — it will reject genuinely ambiguous chains
- Watch `as` casts: they bind tighter than you expect
- Use `clippy` — it warns on mixed logical operators without parens: `a && b || c` → clippy suggests `(a && b) || c`
- Ranges in `match` arms are clear, but in expressions always consider parens

### Go
- **Remember: Go's shift has higher precedence than addition** — the opposite of C
- `&^` (bit clear) is Go-specific: use it instead of `& ^`
- Never try to use assignment as an expression — Go won't allow it
- For channel ops, `<-` in complex expressions always deserves explicit parens for clarity

---

## The Expert's Mental Checklist

When reading a complex expression without parentheses, an expert thinks in this order:

1. **Identify all operators** present in the expression
2. **Find the lowest-precedence operator** — it is the "root" of the expression tree
3. **Recurse into each side** of that operator
4. **Check associativity** only when operators at the same level appear adjacent
5. **Ask: does evaluation order matter here?** (any side effects? function calls?)

```
Expression: a | b & c == d && e || f

Step 1: operators: |  &  ==  &&  ||
Step 2: Lowest precedence is || — root splits: (a | b & c == d && e) || f
Step 3: Left side: lowest is && → (a | b & c == d) && e
Step 4: a | b & c == d  → lowest is == → (a | b & c) == d
Step 5: a | b & c → lowest is | → a | (b & c)

Final: (((a | (b & c)) == d) && e) || f
```

This mechanical tree-building is how a compiler reads your code. If your intent doesn't match this tree — **add parentheses**.

---

## Summary: The 5 Laws of Precedence Mastery

1. **Parentheses are free.** Use them whenever intent might be misread — by humans or compilers.
2. **Bitwise operators in C/C++ need explicit grouping** — their precedence is a historical mistake.
3. **C and Go/Rust have opposite shift precedence** — the single most dangerous cross-language trap.
4. **Evaluation order ≠ precedence** — C/C++ have undefined behavior; Rust/Go are defined left-to-right.
5. **`as` in Rust and `<-` in Go bind tighter than you expect** — know your language's unique operators.

The programmer who truly understands precedence doesn't memorize tables — they understand *why* each level exists, can reconstruct the parse tree mentally, and knows exactly where their language deviates from expectations. That gap between "knowing the table" and "understanding the tree" is where the top 1% lives.