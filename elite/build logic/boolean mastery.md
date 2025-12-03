# The Ultimate Boolean Mastery Encyclopedia: Rust, Python, Go, C, C++

This is your definitive reference. From bit-level operations to compiler optimizations, we'll dissect boolean logic across five languages with the precision of a neurosurgeon and the depth of a computer architect.

---

## Table of Contents

1. **Complete Operator Precedence Tables** (All 5 Languages)
2. **Type Systems & Boolean Semantics**
3. **Truthiness & Falsiness** (Language Comparison)
4. **Short-Circuit Evaluation** (Deep Dive)
5. **Bitwise vs Logical Operators**
6. **Boolean Algebra & Simplification Laws**
7. **Assembly & Machine Code Analysis**
8. **Compiler Optimizations**
9. **Edge Cases & Gotchas**
10. **Advanced Patterns & Idioms**
11. **Performance Benchmarks**
12. **Interview Questions** (Curated Collection)
13. **Practice Problems** (Graduated Difficulty)

---

## Part 1: Complete Operator Precedence Tables

### Python Precedence (Complete)

From **highest** to **lowest**:

| Priority | Operator | Description | Example |
|----------|----------|-------------|---------|
| 1 | `()` | Parentheses | `(a + b)` |
| 2 | `**` | Exponentiation | `2 ** 3` |
| 3 | `+x`, `-x`, `~x` | Unary plus, minus, bitwise NOT | `-5`, `~0b1010` |
| 4 | `*`, `/`, `//`, `%` | Multiplication, division, floor division, modulo | `10 / 3` |
| 5 | `+`, `-` | Addition, subtraction | `5 + 3` |
| 6 | `<<`, `>>` | Bitwise shifts | `8 << 2` |
| 7 | `&` | Bitwise AND | `5 & 3` |
| 8 | `^` | Bitwise XOR | `5 ^ 3` |
| 9 | `\|` | Bitwise OR | `5 \| 3` |
| 10 | `<`, `<=`, `>`, `>=`, `!=`, `==`, `is`, `is not`, `in`, `not in` | Comparisons, identity, membership | `5 < 10` |
| 11 | `not` | Logical NOT | `not True` |
| 12 | `and` | Logical AND | `True and False` |
| 13 | `or` | Logical OR | `True or False` |
| 14 | `if-else` | Conditional expression | `a if condition else b` |
| 15 | `lambda` | Lambda expression | `lambda x: x + 1` |
| 16 | `:=` | Walrus operator (assignment expression) | `(n := len(a))` |

#### Critical Python Nuances

```python
# NOT has lower precedence than comparisons
result = not 5 < 10  # Parsed as: not (5 < 10)
# Result: False

# Chained comparisons
result = 5 < 10 < 20  # Parsed as: (5 < 10) and (10 < 20)
# Result: True

# Comparisons are evaluated left-to-right, but NOT comes after
result = 5 < 10 and not 20 < 30
# Parsed as: (5 < 10) and (not (20 < 30))
# Result: False
```

**Key insight**: In Python, `not` has **lower** precedence than comparison operators, which is unusual. Most languages bind unary operators very tightly.

---

### Rust Precedence (Complete)

From **highest** to **lowest**:

| Priority | Operator | Description | Example |
|----------|----------|-------------|---------|
| 1 | `()`, `[]`, `.`, `?` | Grouping, indexing, field access, error propagation | `arr[0]`, `obj.field` |
| 2 | `::` | Path separator | `std::vec::Vec` |
| 3 | Function calls, macros | | `foo()`, `vec![]` |
| 4 | Unary `-`, `*`, `!`, `&`, `&mut` | Negation, dereference, logical NOT, reference | `!true`, `&x` |
| 5 | `as` | Type cast | `x as i32` |
| 6 | `*`, `/`, `%` | Multiplication, division, remainder | `10 / 3` |
| 7 | `+`, `-` | Addition, subtraction | `5 + 3` |
| 8 | `<<`, `>>` | Bitwise shifts | `8 << 2` |
| 9 | `&` | Bitwise AND | `5 & 3` |
| 10 | `^` | Bitwise XOR | `5 ^ 3` |
| 11 | `\|` | Bitwise OR | `5 \| 3` |
| 12 | `==`, `!=`, `<`, `>`, `<=`, `>=` | Comparisons | `5 < 10` |
| 13 | `&&` | Logical AND | `true && false` |
| 14 | `\|\|` | Logical OR | `true \|\| false` |
| 15 | `..`, `..=` | Range operators | `1..10`, `1..=10` |
| 16 | `=`, `+=`, `-=`, etc. | Assignment | `x = 5` |

#### Critical Rust Nuances

```rust
// Unary ! has very high precedence
let result = !false || true && false;
// Parsed as: (!false) || (true && false)
// Result: true

// Type system is strict
let x: bool = true && false;  // OK
let y: bool = 5 < 10 && 10 < 20;  // OK
// let z: bool = 5 && 3;  // COMPILE ERROR: expected bool, found integer

// No implicit conversions
// let result = 1 && 0;  // COMPILE ERROR

// Borrow checker affects boolean expressions
let v = vec![1, 2, 3];
let result = !v.is_empty() && v[0] > 0;  // OK, immutable borrows

// let mut v = vec![1, 2, 3];
// let result = !v.is_empty() && v.push(4);  // COMPILE ERROR: can't borrow as mutable while borrowed as immutable
```

**Key insight**: Rust's type system prevents many boolean logic errors at compile time. No implicit truthiness—only `bool` values work with logical operators.

---

### Go Precedence (Complete)

From **highest** to **lowest**:

| Priority | Operator | Description | Example |
|----------|----------|-------------|---------|
| 1 | `()`, `[]`, `.`, `->` | Grouping, indexing, field access | `arr[0]`, `ptr->field` |
| 2 | `++`, `--` (postfix) | Postfix increment/decrement | `x++` |
| 3 | `+`, `-`, `!`, `^`, `*`, `&`, `<-` | Unary operators | `!true`, `&x` |
| 4 | `*`, `/`, `%`, `<<`, `>>`, `&`, `&^` | Multiplicative, shifts, bitwise AND | `10 / 3` |
| 5 | `+`, `-`, `\|`, `^` | Additive, bitwise OR/XOR | `5 + 3` |
| 6 | `==`, `!=`, `<`, `<=`, `>`, `>=` | Comparisons | `5 < 10` |
| 7 | `&&` | Logical AND | `true && false` |
| 8 | `\|\|` | Logical OR | `true \|\| false` |
| 9 | `<-` (channel operations) | Channel send/receive | `ch <- value` |
| 10 | `=`, `:=`, `+=`, `-=`, etc. | Assignment | `x = 5` |

#### Critical Go Nuances

```go
// Unary ! has high precedence
result := !false || true && false
// Parsed as: (!false) || (true && false)
// Result: true

// No implicit truthiness - only bool type works
var x int = 5
// result := x && 3  // COMPILE ERROR

// Strict typing
result := true && false  // OK
result = 5 < 10 && 10 < 20  // OK

// No operator overloading
// Custom types can't define && or || behavior

// Short variable declaration
if result := someFunc(); result {
    // result is scoped to this if block
}
```

**Key insight**: Go is simpler than Rust but stricter than Python. No implicit conversions, no operator overloading, clean and readable.

---

### C Precedence (Complete)

From **highest** to **lowest**:

| Priority | Operator | Description | Associativity | Example |
|----------|----------|-------------|---------------|---------|
| 1 | `()`, `[]`, `->`, `.`, `++`, `--` (postfix) | Primary | Left-to-right | `arr[0]` |
| 2 | `++`, `--` (prefix), `+`, `-`, `!`, `~`, `*`, `&`, `sizeof`, `(type)` | Unary | Right-to-left | `!x`, `&x` |
| 3 | `*`, `/`, `%` | Multiplicative | Left-to-right | `10 / 3` |
| 4 | `+`, `-` | Additive | Left-to-right | `5 + 3` |
| 5 | `<<`, `>>` | Shift | Left-to-right | `8 << 2` |
| 6 | `<`, `<=`, `>`, `>=` | Relational | Left-to-right | `5 < 10` |
| 7 | `==`, `!=` | Equality | Left-to-right | `x == y` |
| 8 | `&` | Bitwise AND | Left-to-right | `5 & 3` |
| 9 | `^` | Bitwise XOR | Left-to-right | `5 ^ 3` |
| 10 | `\|` | Bitwise OR | Left-to-right | `5 \| 3` |
| 11 | `&&` | Logical AND | Left-to-right | `1 && 0` |
| 12 | `\|\|` | Logical OR | Left-to-right | `1 \|\| 0` |
| 13 | `? :` | Ternary conditional | Right-to-left | `a ? b : c` |
| 14 | `=`, `+=`, `-=`, etc. | Assignment | Right-to-left | `x = 5` |
| 15 | `,` | Comma | Left-to-right | `x = 1, y = 2` |

#### Critical C Nuances

```c
// C treats any non-zero value as true, zero as false
int result = 5 && 3;  // result = 1 (true)
result = 0 || 2;      // result = 1 (true)
result = 5 && 0;      // result = 0 (false)

// Dangerous: chained comparisons don't work as expected
result = 5 < 10 < 20;
// Parsed as: (5 < 10) < 20
// (5 < 10) evaluates to 1
// 1 < 20 evaluates to 1
// Result: 1 (true), but NOT checking if 10 is between 5 and 20!

// Correct way:
result = (5 < 10) && (10 < 20);

// Unary ! has high precedence
result = !5 < 10;
// Parsed as: (!5) < 10
// !5 = 0 (since 5 is non-zero)
// 0 < 10 = 1
// Result: 1 (true)

// Bitwise vs logical confusion
result = 1 & 2;   // Bitwise AND: 0
result = 1 && 2;  // Logical AND: 1

// Pointer confusion
int x = 5;
int *p = &x;
result = !p;  // Checks if pointer is NULL
// Result: 0 (false, pointer is not NULL)
```

**Key insight**: C's implicit conversions between integers and booleans cause many bugs. Always use explicit comparisons: `if (x != 0)` instead of `if (x)` when clarity matters.

---

### C++ Precedence (Complete)

C++ inherits C's precedence but adds more operators:

| Priority | Operator | Description | Associativity | Example |
|----------|----------|-------------|---------------|---------|
| 1 | `::` | Scope resolution | Left-to-right | `std::cout` |
| 2 | `()`, `[]`, `->`, `.`, `++`, `--` (postfix), `typeid`, casts | Primary | Left-to-right | `arr[0]` |
| 3 | `++`, `--` (prefix), `+`, `-`, `!`, `~`, `*`, `&`, `sizeof`, `new`, `delete` | Unary | Right-to-left | `!x` |
| 4 | `.*`, `->*` | Pointer-to-member | Left-to-right | `obj.*ptr` |
| 5 | `*`, `/`, `%` | Multiplicative | Left-to-right | `10 / 3` |
| 6 | `+`, `-` | Additive | Left-to-right | `5 + 3` |
| 7 | `<<`, `>>` | Shift (or stream operations) | Left-to-right | `8 << 2` |
| 8 | `<`, `<=`, `>`, `>=` | Relational | Left-to-right | `5 < 10` |
| 9 | `==`, `!=` | Equality | Left-to-right | `x == y` |
| 10 | `&` | Bitwise AND | Left-to-right | `5 & 3` |
| 11 | `^` | Bitwise XOR | Left-to-right | `5 ^ 3` |
| 12 | `\|` | Bitwise OR | Left-to-right | `5 \| 3` |
| 13 | `&&` | Logical AND | Left-to-right | `true && false` |
| 14 | `\|\|` | Logical OR | Left-to-right | `true \|\| false` |
| 15 | `? :` | Ternary conditional | Right-to-left | `a ? b : c` |
| 16 | `=`, `+=`, `-=`, etc. | Assignment | Right-to-left | `x = 5` |
| 17 | `,` | Comma | Left-to-right | `x = 1, y = 2` |

#### Critical C++ Nuances

```cpp
// C++ has bool type (unlike C's implicit conversions)
bool result = true && false;  // result = false

// But implicit conversions still exist
result = 5 && 3;  // result = true (both non-zero)

// Operator overloading changes behavior
std::string s1 = "Hello";
std::string s2 = "World";
bool result = (s1 < s2);  // Uses overloaded < operator

// Short-circuit with side effects
int x = 0;
result = false && (++x > 0);  // x is still 0 (++x never executes)

// Stream operators use << >>
std::cout << (5 < 10);  // Prints 1 (true)

// Careful with macros
#define MAX(a, b) ((a) > (b) ? (a) : (b))
int result = MAX(5, 10) && MAX(3, 7);
// Expands to: ((5) > (10) ? (5) : (10)) && ((3) > (7) ? (3) : (7))
// Result: 10 && 7 = true

// Modern C++ (C++20) has <=> spaceship operator
#include <compare>
int x = 5, y = 10;
auto result = (x <=> y) < 0;  // true (x is less than y)
```

**Key insight**: C++ adds complexity with operator overloading. The meaning of `&&`, `||`, `<`, etc., can change for custom types. Always check documentation for non-primitive types.

---

## Part 2: Type Systems & Boolean Semantics

### Python: Dynamic Duck Typing

```python
# bool is a subclass of int
isinstance(True, int)  # True
True + True  # 2
True * 5  # 5

# Any object can be tested for truth value
bool([])  # False
bool([1, 2, 3])  # True
bool("")  # False
bool("Hello")  # True
bool(0)  # False
bool(42)  # True
bool(None)  # False

# Custom objects define __bool__ or __len__
class MyClass:
    def __bool__(self):
        return False

obj = MyClass()
if obj:
    print("This won't print")
```

**Mental model**: Python asks every object "Are you true?" via `__bool__()` or `__len__()`.

---

### Rust: Static Strong Typing

```rust
// bool is a primitive type, NOT an integer
let x: bool = true;
// let y: i32 = x;  // COMPILE ERROR: mismatched types

// No implicit conversions
// if 1 { }  // COMPILE ERROR: expected bool, found integer

// Explicit conversion required
let num = 1;
if num != 0 {  // OK
    println!("Truthy");
}

// Option<T> is Rust's way of handling nullable values
fn divide(a: i32, b: i32) -> Option<i32> {
    if b != 0 {
        Some(a / b)
    } else {
        None
    }
}

// Pattern matching
match divide(10, 2) {
    Some(result) => println!("Result: {}", result),
    None => println!("Division by zero"),
}

// Combining with boolean logic
let result = divide(10, 0).is_some() && divide(10, 2).unwrap() > 0;
```

**Mental model**: Rust's type system encodes nullability, errors, and validity in types. Booleans are strictly booleans—no implicit magic.

---

### Go: Static Duck Typing

```go
// bool is a primitive type
var x bool = true

// No implicit conversions
var num int = 1
// if num { }  // COMPILE ERROR

// Explicit comparison required
if num != 0 {
    fmt.Println("Truthy")
}

// Interfaces allow duck typing
type Stringer interface {
    String() string
}

// Empty interface
var v interface{} = 42

// Type assertions
if val, ok := v.(int); ok {
    fmt.Println("It's an int:", val)
}

// Zero values
var b bool     // false
var i int      // 0
var s string   // ""
var p *int     // nil

// Checking for nil
if p != nil {
    fmt.Println("Pointer is valid")
}
```

**Mental model**: Go is simple. No implicit conversions, but interfaces provide flexibility. Zero values are predictable.

---

### C: Implicit Weak Typing

```c
// No bool type in C89 (added in C99 via stdbool.h)
#include <stdbool.h>  // C99 and later

bool x = true;  // With stdbool.h
int y = 1;      // Without stdbool.h, use int

// Implicit conversions everywhere
if (5) {  // Non-zero is true
    printf("This prints\n");
}

if (0) {  // Zero is false
    printf("This doesn't print\n");
}

// Pointers
int *p = NULL;
if (!p) {  // NULL is false
    printf("Pointer is NULL\n");
}

// Dangerous implicit conversions
int a = 5, b = 3;
bool result = a & b;  // Bitwise AND: 1, implicitly converted to true

// Assignment in condition (common bug)
int x = 5;
if (x = 0) {  // ASSIGNS 0 to x, then evaluates 0 (false)
    printf("This doesn't print\n");
}

// Correct: use ==
if (x == 0) {
    printf("x is zero\n");
}
```

**Mental model**: C is the Wild West. Anything can be a boolean. Be explicit to avoid bugs.

---

### C++: Static with Implicit Conversions

```cpp
// C++ has bool type
bool x = true;

// Implicit conversions still exist
int num = 5;
bool result = num;  // Converts to true

// Pointers
int *p = nullptr;  // C++11 and later
if (p) {  // nullptr is false
    std::cout << "Pointer is valid\n";
}

// Smart pointers
std::unique_ptr<int> ptr = std::make_unique<int>(42);
if (ptr) {  // Checks if pointer is not null
    std::cout << "Pointer holds a value\n";
}

// Optional (C++17)
#include <optional>
std::optional<int> opt = std::nullopt;
if (opt.has_value()) {
    std::cout << "Value: " << *opt << "\n";
}

// Explicit conversion operator
class MyClass {
public:
    explicit operator bool() const {
        return value > 0;
    }
private:
    int value = 0;
};

MyClass obj;
// bool b = obj;  // COMPILE ERROR: explicit conversion required
bool b = static_cast<bool>(obj);  // OK
if (obj) {  // OK: contextual conversion
    std::cout << "Object is true\n";
}
```

**Mental model**: C++ gives you control. Use `explicit` to prevent implicit conversions. Use modern features like `std::optional` to encode nullability.

---

## Part 3: Truthiness & Falsiness (Language Comparison)

### Python Falsy Values

```python
# Falsy values:
False
None
0, 0.0, 0j  # Numeric zeros
"", b"", ''  # Empty strings
[], (), {}, set()  # Empty collections
# Custom objects with __bool__() returning False or __len__() returning 0

# Everything else is truthy
```

**Examples**:
```python
if []:
    print("Empty list is truthy")  # Doesn't print

if [0]:
    print("List with zero is truthy")  # Prints!

if "":
    print("Empty string is truthy")  # Doesn't print

if " ":
    print("Space is truthy")  # Prints!
```

---

### Rust: No Implicit Truthiness

```rust
// ONLY bool type is boolean
// if 0 { }  // COMPILE ERROR
// if "" { }  // COMPILE ERROR
// if None { }  // COMPILE ERROR

// Must explicitly convert
let num = 5;
if num != 0 {  // OK
    println!("Non-zero");
}

let opt: Option<i32> = None;
if opt.is_some() {  // OK
    println!("Has value");
}

// Pattern matching is preferred
match opt {
    Some(val) => println!("Value: {}", val),
    None => println!("No value"),
}
```

---

### Go: No Implicit Truthiness

```go
// ONLY bool type is boolean
// if 0 { }  // COMPILE ERROR
// if "" { }  // COMPILE ERROR
// if nil { }  // COMPILE ERROR

// Must explicitly convert
num := 5
if num != 0 {  // OK
    fmt.Println("Non-zero")
}

var p *int
if p != nil {  // OK
    fmt.Println("Pointer is valid")
}

// Idiomatic: comma-ok pattern
if val, ok := someMap["key"]; ok {
    fmt.Println("Found:", val)
}
```

---

### C: Everything is a Number

```c
// Zero is false, non-zero is true
if (0) { }     // False
if (1) { }     // True
if (-1) { }    // True
if (0.0) { }   // False
if (42) { }    // True

// Pointers
int *p = NULL;
if (p) { }     // False (NULL is typically 0)

int x = 5;
int *q = &x;
if (q) { }     // True (non-NULL pointer)

// Characters
if ('A') { }   // True (ASCII 65)
if ('\0') { }  // False (null character, value 0)

// Common idiom: check and assign
int fd;
if ((fd = open("file.txt", O_RDONLY)) < 0) {
    perror("open");
}
```

---

### C++: Mostly Like C, with Extensions

```cpp
// Same as C
if (0) { }     // False
if (5) { }     // True

// Pointers
int *p = nullptr;
if (p) { }     // False

// Smart pointers
std::unique_ptr<int> ptr;
if (ptr) { }   // False (empty)

ptr = std::make_unique<int>(42);
if (ptr) { }   // True (holds value)

// Streams
std::ifstream file("data.txt");
if (file) {    // True if file opened successfully
    // Read file
}

// Custom conversions
class MyClass {
public:
    explicit operator bool() const {
        return is_valid;
    }
private:
    bool is_valid = true;
};
```

---

## Part 4: Short-Circuit Evaluation (Deep Dive)

### Guaranteed in All 5 Languages

**AND short-circuit**: If left operand is false, right operand is **not evaluated**.

**OR short-circuit**: If left operand is true, right operand is **not evaluated**.

---

### Python Examples

```python
# AND short-circuit
def expensive():
    print("expensive() called")
    return True

result = False and expensive()
# Output: (nothing)
# Result: False

# OR short-circuit
result = True or expensive()
# Output: (nothing)
# Result: True

# Exploiting short-circuit for safety
arr = [1, 2, 3]
if len(arr) > 0 and arr[0] > 0:
    print("First element is positive")

# Without short-circuit, this would fail:
# arr = []
# if arr[0] > 0 and len(arr) > 0:  # IndexError!

# Walrus operator with short-circuit
if (n := len(arr)) > 0 and arr[0] > 0:
    print(f"Array of length {n} has positive first element")

# Short-circuit returns actual value, not just True/False
result = "" or "default"  # Returns "default"
result = [1] or [2]       # Returns [1]
result = 0 and 10         # Returns 0
result = 5 and 10         # Returns 10
```

---

### Rust Examples

```rust
// AND short-circuit
fn expensive() -> bool {
    println!("expensive() called");
    true
}

let result = false && expensive();
// Output: (nothing)
// Result: false

// OR short-circuit
let result = true || expensive();
// Output: (nothing)
// Result: true

// Safety with Option
let vec = vec![1, 2, 3];
let result = !vec.is_empty() && vec[0] > 0;
// Safe: if vec is empty, vec[0] is never accessed

// Using match for explicit control
let opt: Option<i32> = Some(5);
let result = match opt {
    Some(val) => val > 0,
    None => false,
};

// Combining with Result
fn divide(a: i32, b: i32) -> Result<i32, String> {
    if b == 0 {
        Err("Division by zero".to_string())
    } else {
        Ok(a / b)
    }
}

let result = divide(10, 2).is_ok() && divide(10, 2).unwrap() > 0;
// Warning: calling unwrap() twice! Better approach:

if let Ok(val) = divide(10, 2) {
    let result = val > 0;
}

// Or use map
let result = divide(10, 2).map(|val| val > 0).unwrap_or(false);
```

---

### Go Examples

```go
// AND short-circuit
func expensive() bool {
    fmt.Println("expensive() called")
    return true
}

result := false && expensive()
// Output: (nothing)
// Result: false

// OR short-circuit
result = true || expensive()
// Output: (nothing)
// Result: true

// Safety with slices
arr := []int{1, 2, 3}
if len(arr) > 0 && arr[0] > 0 {
    fmt.Println("First element is positive")
}

// Idiomatic: comma-ok pattern
m := map[string]int{"key": 5}
if val, ok := m["key"]; ok && val > 0 {
    fmt.Println("Key exists and value is positive")
}

// Channel operations with short-circuit
ch := make(chan int, 1)
ch <- 42
if len(ch) > 0 && <-ch > 0 {
    fmt.Println("Received positive value")
}
```

---

### C Examples

```c
// AND short-circuit
int expensive() {
    printf("expensive() called\n");
    return 1;
}

int result = 0 && expensive();
// Output: (nothing)
// Result: 0

// OR short-circuit
result = 1 || expensive();
// Output: (nothing)
// Result: 1

// Safety with pointers
int *p = NULL;
if (p != NULL && *p > 0) {
    printf("Pointer points to positive value\n");
}
// Without short-circuit: segmentation fault!

// Common idiom: check and use
FILE *file = fopen("data.txt", "r");
if (file != NULL && fread(buffer, 1, 100, file) > 0) {
    // Process buffer
    fclose(file);
}

// Assignment in condition (leveraging short-circuit)
int fd;
if ((fd = open("file.txt", O_RDONLY)) >= 0 && read(fd, buffer, 100) > 0) {
    // Process buffer
    close(fd);
}
```

---

### C++ Examples

```cpp
// AND short-circuit
bool expensive() {
    std::cout << "expensive() called\n";
    return true;
}

bool result = false && expensive();
// Output: (nothing)
// Result: false

// OR short-circuit
result = true || expensive();
// Output: (nothing)
// Result: true

// Safety with smart pointers
std::unique_ptr<int> ptr = std::make_unique<int>(42);
if (ptr && *ptr > 0) {
    std::cout << "Pointer holds positive value\n";
}

// With std::optional (C++17)
std::optional<int> opt = 5;
if (opt.has_value() && *opt > 0) {
    std::cout << "Optional holds positive value\n";
}

// Streams
std::ifstream file("data.txt");
if (file && file.is_open()) {
    std::string line;
    std::getline(file, line);
}

// Custom operators (careful with overloading)
class MyClass {
public:
    bool operator&&(const MyClass& other) {
        std::cout << "Custom && called\n";
        return value && other.value;
    }
private:
    bool value = true;
};

}
    
    bool value = true;
};

MyClass a, b;
bool result = a && b;  // Uses custom operator
// Note: Custom && and || DON'T short-circuit!
```

---

## Part 5: Bitwise vs Logical Operators

### Comparison Table

| Operation | Python | Rust | Go | C/C++ |
|-----------|--------|------|-----|-------|
| Logical AND | `and` | `&&` | `&&` | `&&` |
| Logical OR | `or` | `\|\|` | `\|\|` | `\|\|` |
| Logical NOT | `not` | `!` | `!` | `!` |
| Bitwise AND | `&` | `&` | `&` | `&` |
| Bitwise OR | `\|` | `\|` | `\|` | `\|` |
| Bitwise XOR | `^` | `^` | `^` | `^` |
| Bitwise NOT | `~` | `!` (for bool), `!` or bitwise ops for ints | `^` (XOR with -1) | `~` |

---

### Python: Clear Distinction

```python
# Logical operators (short-circuit, work on any object)
result = True and False  # False
result = [] or [1, 2]    # [1, 2]

# Bitwise operators (work on integers)
result = 5 & 3   # 1 (binary: 0101 & 0011 = 0001)
result = 5 | 3   # 7 (binary: 0101 | 0011 = 0111)
result = 5 ^ 3   # 6 (binary: 0101 ^ 0011 = 0110)
result = ~5      # -6 (binary: inverts all bits)

# Bitwise operators on bool work but are unusual
result = True & False  # False (treated as 1 & 0 = 0)
result = True | False  # True (treated as 1 | 0 = 1)

# Key difference: bitwise operators DON'T short-circuit
def side_effect():
    print("side_effect called")
    return True

result = False & side_effect()  # Prints "side_effect called"
result = False and side_effect()  # Doesn't print

# Common mistake
if 5 & 3:  # Works, but confusing (bitwise AND result is 1, which is truthy)
    print("This prints")

# Better:
if (5 & 3) != 0:
    print("This is clearer")
```

---

### Rust: Type Safety Prevents Confusion

```rust
// Logical operators (only work on bool)
let result = true && false;  // false
// let result = 5 && 3;  // COMPILE ERROR

// Bitwise operators (work on integers)
let result = 5 & 3;   // 1
let result = 5 | 3;   // 7
let result = 5 ^ 3;   // 6
let result = !5;      // -6 (two's complement)

// Bitwise operators on bool
let result = true & false;  // false
let result = true | false;  // true

// But logical operators are preferred for bool
let result = true && false;  // Idiomatic

// Key difference: bitwise operators DON'T short-circuit
fn side_effect() -> bool {
    println!("side_effect called");
    true
}

let result = false & side_effect();  // Prints "side_effect called"
let result = false && side_effect();  // Doesn't print

// Bitwise operations in systems programming
let flags: u8 = 0b0000_1010;
let mask: u8 = 0b0000_0011;
let result = flags & mask;  // 0b0000_0010

// Setting a bit
let flags = flags | 0b0000_0100;  // Set bit 2

// Clearing a bit
let flags = flags & !0b0000_0100;  // Clear bit 2

// Toggling a bit
let flags = flags ^ 0b0000_0100;  // Toggle bit 2
```

---

### Go: Similar to Rust

```go
// Logical operators (only work on bool)
result := true && false  // false
// result := 5 && 3  // COMPILE ERROR

// Bitwise operators (work on integers)
result = 5 & 3   // 1
result = 5 | 3   // 7
result = 5 ^ 3   // 6
result = ^5      // -6 (bitwise complement)

// Bitwise operators DON'T work on bool in Go
// result := true & false  // COMPILE ERROR

// Key difference: bitwise operators DON'T short-circuit
func sideEffect() int {
    fmt.Println("sideEffect called")
    return 1
}

result = 0 & sideEffect()  // Prints "sideEffect called"
result = 0 && sideEffect()  // COMPILE ERROR (&& doesn't work on int)

// Bitwise operations for flags
const (
    FlagRead  = 1 << 0  // 0b0001
    FlagWrite = 1 << 1  // 0b0010
    FlagExec  = 1 << 2  // 0b0100
)

var permissions int = FlagRead | FlagWrite  // 0b0011

// Check if a flag is set
if permissions & FlagRead != 0 {
    fmt.Println("Read permission granted")
}

// Set a flag
permissions |= FlagExec  // Now 0b0111

// Clear a flag
permissions &^= FlagWrite  // Now 0b0101 (Go-specific: AND NOT)

// Toggle a flag
permissions ^= FlagExec  // Now 0b0001
```

---

### C: Potential for Confusion

```c
// Logical operators (short-circuit)
int result = 1 && 0;  // 0
result = 1 || 0;      // 1
result = !1;          // 0

// Bitwise operators (no short-circuit)
result = 5 & 3;   // 1
result = 5 | 3;   // 7
result = 5 ^ 3;   // 6
result = ~5;      // -6

// Dangerous: bitwise operators DON'T short-circuit
int side_effect() {
    printf("side_effect called\n");
    return 1;
}

result = 0 & side_effect();  // Prints "side_effect called"
result = 0 && side_effect();  // Doesn't print

// Common bug: using bitwise instead of logical
int x = 5, y = 3;
if (x & y) {  // Compiles, but uses bitwise AND
    printf("This might not do what you expect\n");
}

// Correct:
if (x && y) {
    printf("Both are non-zero\n");
}

// Bitwise operations for flags
#define FLAG_READ  0x01  // 0b00000001
#define FLAG_WRITE 0x02  // 0b00000010
#define FLAG_EXEC  0x04  // 0b00000100

int permissions = FLAG_READ | FLAG_WRITE;  // 0b00000011

// Check if a flag is set
if (permissions & FLAG_READ) {
    printf("Read permission granted\n");
}

// Set a flag
permissions |= FLAG_EXEC;  // Now 0b00000111

// Clear a flag
permissions &= ~FLAG_WRITE;  // Now 0b00000101

// Toggle a flag
permissions ^= FLAG_EXEC;  // Now 0b00000001
```

---

### C++: Same as C with Extensions

```cpp
// Same as C for primitives
bool result = true && false;  // false
int bitwise = 5 & 3;          // 1

// Operator overloading can change behavior
class Flags {
public:
    Flags(unsigned int val) : value(val) {}
    
    // Overload & for bitwise AND
    Flags operator&(const Flags& other) const {
        return Flags(value & other.value);
    }
    
    // Overload && for logical AND (unusual, not recommended)
    bool operator&&(const Flags& other) const {
        return value && other.value;
    }
    
    unsigned int value;
};

Flags f1(5), f2(3);
Flags result_bitwise = f1 & f2;  // Uses overloaded &
bool result_logical = f1 && f2;  // Uses overloaded && (doesn't short-circuit!)

// Modern C++: std::bitset
#include <bitset>
std::bitset<8> bits1("00001010");
std::bitset<8> bits2("00000011");

auto result = bits1 & bits2;  // 00000010
result = bits1 | bits2;       // 00001011
result = bits1 ^ bits2;       // 00001001
result = ~bits1;              // 11110101
```

---

## Part 6: Boolean Algebra & Simplification Laws

### Fundamental Laws

#### Identity Laws
```
A and True  = A
A or False  = A
```

#### Domination Laws
```
A and False = False
A or True   = True
```

#### Idempotent Laws
```
A and A = A
A or A  = A
```

#### Complement Laws
```
A and not A = False
A or not A  = True
not (not A) = A
```

#### Commutative Laws
```
A and B = B and A
A or B  = B or A
```

#### Associative Laws
```
(A and B) and C = A and (B and C)
(A or B) or C   = A or (B or C)
```

#### Distributive Laws
```
A and (B or C)  = (A and B) or (A and C)
A or (B and C)  = (A or B) and (A or C)
```

#### De Morgan's Laws (Critical!)
```
not (A and B) = (not A) or (not B)
not (A or B)  = (not A) and (not B)
```

#### Absorption Laws
```
A or (A and B)  = A
A and (A or B)  = A
```

---

### Simplification Examples

#### Example 1: Basic Simplification
```
Given: (A and B) or (A and not B)

Step 1: Factor out A (distributive law)
= A and (B or not B)

Step 2: B or not B is always True (complement law)
= A and True

Step 3: A and True = A (identity law)
= A
```

**Code verification** (Python):
```python
def test_simplification(A, B):
    original = (A and B) or (A and not B)
    simplified = A
    return original == simplified

# Test all combinations
for A in [True, False]:
    for B in [True, False]:
        assert test_simplification(A, B), f"Failed for A={A}, B={B}"

print("Simplification verified!")
```

---

#### Example 2: De Morgan's Law
```
Given: not (x > 5 and y < 10)

Apply De Morgan's Law:
= not (x > 5) or not (y < 10)

Simplify negations:
= (x <= 5) or (y >= 10)
```

**Code verification** (Rust):
```rust
fn test_de_morgan(x: i32, y: i32) -> bool {
    let original = !(x > 5 && y < 10);
    let simplified = (x <= 5) || (y >= 10);
    original == simplified
}

fn main() {
    // Test multiple values
    for x in [0, 5, 6, 10] {
        for y in [0, 5, 10, 15] {
            assert!(test_de_morgan(x, y), "Failed for x={}, y={}", x, y);
        }
    }
    println!("De Morgan's law verified!");
}
```

---

#### Example 3: Complex Simplification
```
Given: (A or B) and (A or C) and (B or C)

Step 1: Apply distributive law to first two terms
= A or (B and C) and (B or C)

Wait, let's be more careful. This is the consensus theorem:
(A or B) and (A or C) and (B or C) = (A or B) and (A or C)

The (B or C) term is redundant!

Proof:
If A is True:
  (True or B) and (True or C) and (B or C)
  = True and True and (B or C)
  = B or C

If A is False:
  (False or B) and (False or C) and (B or C)
  = B and C and (B or C)
  = B and C  (absorption: B and C implies B or C)

So the original simplifies to:
= (A or B) and (A or C)
```

---

### Truth Table Verification

For complex simplifications, build truth tables:

```python
import itertools

def verify_equivalence(expr1, expr2, variables):
    """Verify two boolean expressions are equivalent."""
    for values in itertools.product([True, False], repeat=len(variables)):
        env = dict(zip(variables, values))
        if eval(expr1, env) != eval(expr2, env):
            return False, env
    return True, None

# Example: verify (A and B) or (A and not B) == A
expr1 = "(A and B) or (A and not B)"
expr2 = "A"
variables = ['A', 'B']

result, counter_example = verify_equivalence(expr1, expr2, variables)
if result:
    print("Expressions are equivalent!")
else:
    print(f"Counter-example: {counter_example}")
```

---

## Part 7: Assembly & Machine Code Analysis

Let's compile the same boolean function in all 5 languages and compare the assembly.

### Test Function

```
Function: test(a: bool, b: bool, c: bool) -> bool
Returns: (a && b) || c
```

---

### Python (Bytecode)

```python
def test(a, b, c):
    return (a and b) or c
```

Compile and disassemble:
```bash
$ python -m dis test.py
```

Output:
```
  2           0 LOAD_FAST                0 (a)
              2 POP_JUMP_IF_FALSE       10
              4 LOAD_FAST                1 (b)
              6 POP_JUMP_IF_FALSE       10
              8 RETURN_VALUE
        >>   10 LOAD_FAST                2 (c)
             12 RETURN_VALUE
```

**Analysis**:
1. Load `a`
2. If `a` is falsy, jump to line 10 (skip `b`, load `c`)
3. Load `b`
4. If `b` is falsy, jump to line 10 (load `c`)
5. If we reach here, return `b` (it's the last loaded value)
6. Line 10: Load `c` and return it

**Key insight**: Python's bytecode explicitly implements short-circuit with conditional jumps.

---

### Rust (x86-64 Assembly)

```rust
pub fn test(a: bool, b: bool, c: bool) -> bool {
    (a && b) || c
}
```

Compile:
```bash
$ rustc --emit asm -C opt-level=3 test.rs
```

Output (simplified):
```asm
test:
    mov     al, dil          ; Load a into AL
    test    al, al           ; Test if a is zero
    je      .LBB0_1          ; If zero, jump to check c
    test    sil, sil         ; Test if b is zero (b is in SIL)
    je      .LBB0_1          ; If zero, jump to check c
    mov     al, 1            ; Set AL to 1 (true)
    ret
.LBB0_1:
    mov     al, dl           ; Load c into AL
    ret
```

**Analysis**:
1. Load `a` into register `AL`
2. Test if `a` is zero (false)
3. If zero, jump to `.LBB0_1` (check `c`)
4. Test if `b` is zero
5. If zero, jump to `.LBB0_1`
6. If we reach here, both `a` and `b` are true → set `AL` to 1 and return
7. `.LBB0_1`: Load `c` into `AL` and return

**Key insight**: Rust compiles to highly optimized machine code with minimal overhead. The `test` instruction is faster than `cmp` for checking zero.

---

### Go (x86-64 Assembly)

```go
package main

func test(a, b, c bool) bool {
    return (a && b) || c
}
```

Compile:
```bash
$ go tool compile -S test.go
```

Output (simplified):
```asm
"".test STEXT nosplit size=23 args=0x10 locals=0x0
    MOVBLZX "".a+8(SP), AX     ; Load a (zero-extend byte)
    TESTB   AL, AL              ; Test if a is zero
    JEQ     check_c             ; If zero, jump to check_c
    MOVBLZX "".b+9(SP), AX     ; Load b
    TESTB   AL, AL              ; Test if b is zero
    JEQ     check_c             ; If zero, jump to check_c
    MOVB    $1, "".~r3+16(SP)  ; Store true to return value
    RET
check_c:
    MOVBLZX "".c+10(SP), AX    ; Load c
    MOVB    AL, "".~r3+16(SP)  ; Store to return value
    RET
```

**Analysis**: Very similar to Rust. Go's compiler produces efficient code with the same pattern of conditional jumps.

---

### C (x86-64 Assembly with GCC)

```c
bool test(bool a, bool b, bool c) {
    return (a && b) || c;
}
```

Compile:
```bash
$ gcc -S -O3 test.c
```

Output (simplified):
```asm
test:
    testb   %dil, %dil       ; Test if a is zero (a is in DIL)
    je      .L2              ; If zero, jump to .L2
    testb   %sil, %sil       ; Test if b is zero (b is in SIL)
    je      .L2              ; If zero, jump to .L2
    movl    $1, %eax         ; Set EAX to 1 (true)
    ret
.L2:
    movzbl  %dl, %eax        ; Load c into EAX (zero-extend)
    ret
```

**Analysis**: Nearly identical to Rust and Go. Modern C compilers produce excellent code.

---

### C++ (x86-64 Assembly with Clang)

```cpp
bool test(bool a, bool b, bool c) {
    return (a && b) || c;
}
```

Compile:
```bash
$ clang++ -S -O3 test.cpp
```

Output (simplified):
```asm
test:
    testb   %dil, %dil       ; Test if a is zero
    je      .LBB0_1          ; If zero, jump to .LBB0_1
    testb   %sil, %sil       ; Test if b is zero
    je      .LBB0_1          ; If zero, jump to .LBB0_1
    movb    $1, %al          ; Set AL to 1 (true)
    retq
.LBB0_1:
    movb    %dl, %al         ; Load c into AL
    retq
```

**Analysis**: C++ (via Clang) produces essentially identical code to C and Rust.

---

### Key Observations

1. **All compilers use conditional jumps** to implement short-circuit evaluation.
2. **No actual AND/OR instructions** at the machine level for boolean operators in most cases.
3. **Optimizations eliminate redundant operations**—compilers are smart.
4. **Rust, Go, C, C++ produce nearly identical assembly** for simple boolean expressions.
5. **Python's bytecode is higher-level** but still uses conditional jumps conceptually.

---

## Part 8: Compiler Optimizations

Modern compilers perform aggressive optimizations on boolean expressions.

### Constant Folding

```rust
// Source
pub fn test() -> bool {
    true && false
}

// Assembly (optimized)
test:
    xor eax, eax  ; Set EAX to 0 (false)
    ret
```

The compiler **evaluates the expression at compile time** and returns the constant.

---

### Dead Code Elimination

```rust
// Source
pub fn test(a: bool) -> bool {
    if a && false {
        expensive_function();  // Never called
    }
    a
}

// The expensive_function() call is completely removed
```

---

### Branch Prediction Hints

In C/C++, you can hint to the compiler:

```c
// GCC/Clang extension
if (__builtin_expect(a && b, 1)) {  // Expect true
    // Hot path
} else {
    // Cold path
}
```

This generates assembly optimized for the likely case.

---

### Common Subexpression Elimination

```rust
// Source
let result1 = a && b;
let result2 = a && b;

// Compiler recognizes this is the same expression
// and computes it once
```

---

### Boolean Algebra Simplification

```rust
// Source
let result = (a || b) && a;

// Compiler simplifies to:
// let result = a;
```

Verify in assembly:
```bash
$ rustc --emit asm -C opt-level=3 test.rs
```

You'll see the optimized version directly loads `a` without checking `b`.

---

## Part 9: Edge Cases & Gotchas

### Gotcha 1: Operator Precedence Confusion

```python
# Python
result = not 5 < 10
# Parsed as: not (5 < 10)
# Result: False

# People expect: (not 5) < 10, which would be an error
```

**Lesson**: `not` has lower precedence than comparisons in Python.

---

### Gotcha 2: Chained Comparisons (C/C++)

```c
// C
int result = 5 < 10 < 20;
// Parsed as: (5 < 10) < 20
// (5 < 10) → 1
// 1 < 20 → 1
// Result: 1 (true), but NOT checking if 10 is between 5 and 20!
```

**Lesson**: C doesn't support chained comparisons like Python. Always use `&&`.

---

### Gotcha 3: Assignment vs Equality

```c
// C
int x = 5;
if (x = 0) {  // ASSIGNS 0 to x, then checks if 0 is true
    printf("This doesn't print\n");
}
```

**Solution**: Use `-Wparentheses` flag in GCC to get warnings.

Better style:
```c
if (0 == x) {  // Yoda condition: if you mistype = instead of ==, it's a compile error
    // ...
}
```

---

### Gotcha 4: Bitwise vs Logical (C/C++)

```cpp
// C++
int a = 5, b = 3;
if (a & b) {  // Bitwise AND: 5 & 3 = 1 (true)
    std::cout << "This prints, but logic might be wrong\n";
}

// Should be:
if (a && b) {
    std::cout << "Both are non-zero\n";
}
```

---

### Gotcha 5: Overloaded && and || Don't Short-Circuit (C++)

```cpp
class MyClass {
public:
    bool operator&&(const MyClass& other) {
        std::cout << "Custom && called\n";
        return value && other.value;
    }
    bool value = true;
};

MyClass a, b;
b.value = false;

// BOTH operands are evaluated!
bool result = a && b;  // Prints "Custom && called"
```

**Lesson**: Never overload `&&` or `||` in C++. Use named functions instead.

---

### Gotcha 6: Python's and/or Returns Values

```python
result = "hello" and 0  # Returns 0, not False
result = "" or "world"  # Returns "world", not True

# Can be exploited:
value = user_input or "default"

# But can be confusing:
result = [1, 2] and [3, 4]  # Returns [3, 4], not True!
```

---

### Gotcha 7: Float Comparisons

```python
# All languages
a = 0.1 + 0.2
b = 0.3
print(a == b)  # False! (floating-point precision)

# Solution: use epsilon comparison
epsilon = 1e-9
print(abs(a - b) < epsilon)  # True
```

---

## Part 10: Advanced Patterns & Idioms

### Pattern 1: Guard Clauses

**Python**:
```python
def process(data):
    if not data:
        return None
    if len(data) < 5:
        return None
    if not data[0].isdigit():
        return None
    
    # Main logic
    return compute(data)
```

**Rust**:
```rust
fn process(data: &[i32]) -> Option<i32> {
    if data.is_empty() {
        return None;
    }
    if data.len() < 5 {
        return None;
    }
    if data[0] < 0 {
        return None;
    }
    
    Some(compute(data))
}
```

**Mental model**: Exit early on edge cases. Main logic is at the end, unindented.

---

### Pattern 2: Short-Circuit for Default Values

**Python**:
```python
# Get value with fallback
value = user_input or "default"

# Careful with falsy values!
count = user_count or 10  # If user_count is 0, this gives 10 (bug?)

# Better:
count = user_count if user_count is not None else 10
```

**Go**:
```go
// Use comma-ok idiom
value, ok := someMap["key"]
if !ok {
    value = "default"
}

// Or in one line
value = func() string {
    if v, ok := someMap["key"]; ok {
        return v
    }
    return "default"
}()
```

---

### Pattern 3: Combining Conditions with Methods

**Rust**:
```rust
// Chain boolean methods
let is_valid = input.trim()
    .is_empty() == false
    && input.starts_with("http")
    && input.len() < 200;

// Better: use helper methods
fn is_valid_url(input: &str) -> bool {
    let trimmed = input.trim();
    !trimmed.is_empty()
        && trimmed.starts_with("http")
        && trimmed.len() < 200
}
```

---

### Pattern 4: Early Return vs Nested If

**Bad**:
```python
def process(data):
    if data:
        if len(data) > 5:
            if data[0] == 'x':
                return compute(data)
    return None
```

**Good**:
```python
def process(data):
    if not data:
        return None
    if len(data) <= 5:
        return None
    if data[0] != 'x':
        return None
    
    return compute(data)
```

**Mental model**: Reduce nesting. Flat is better than nested.

---

### Pattern 5: Bool Flags vs State Machine

**Bad**:
```python
is_started = False
is_running = False
is_paused = False
is_stopped = False

# Confusing: what if multiple flags are True?
```

**Good**:
```python
from enum import Enum

class State(Enum):
    IDLE = 1
    RUNNING = 2
    PAUSED = 3
    STOPPED = 4

state = State.IDLE

# Clear and unambiguous
if state == State.RUNNING:
    # ...
```

**Rust** (using enums):
```rust
enum State {
    Idle,
    Running,
    Paused,
    Stopped,
}

let state = State::Idle;

match state {
    State::Idle => println!("System is idle"),
    State::Running => println!("System is running"),
    State::Paused => println!("System is paused"),
    State::Stopped => println!("System is stopped"),
}
```

---

## Part 11: Performance Benchmarks

Let's measure the performance of boolean operations.

### Benchmark: Short-Circuit vs Full Evaluation

**Python**:
```python
import timeit

def expensive():
    return sum(range(1000))

# Short-circuit
def test_short_circuit():
    return False and expensive()

# Full evaluation (using bitwise)
def test_full():
    return False & expensive()

# Measure
short_circuit_time = timeit.timeit(test_short_circuit, number=1000000)
full_time = timeit.timeit(test_full, number=1000000)

print(f"Short-circuit: {short_circuit_time:.6f}s")
print(f"Full evaluation: {full_time:.6f}s")
print(f"Speedup: {full_time / short_circuit_time:.2f}x")
```

**Expected output**:
```
Short-circuit: 0.025s
Full evaluation: 2.500s
Speedup: 100x
```

---

**Rust**:
```rust
use std::time::Instant;

fn expensive() -> bool {
    (0..1000).sum::<i32>();
    true
}

fn test_short_circuit() -> bool {
    false && expensive()
}

fn test_full() -> bool {
    false & expensive()
}

fn main() {
    let iterations = 1_000_000;
    
    let start = Instant::now();
    for _ in 0..iterations {
        std::hint::black_box(test_short_circuit());
    }
    let short_circuit_time = start.elapsed();
    
    let start = Instant::now();
    for _ in 0..iterations {
        std::hint::black_box(test_full());
    }
    let full_time = start.elapsed();
    
    println!("Short-circuit: {:?}", short_circuit_time);
    println!("Full evaluation: {:?}", full_time);
    println!("Speedup: {:.2}x", full_time.as_secs_f64() / short_circuit_time.as_secs_f64());
}
```

---

### Benchmark: Branch Prediction

Modern CPUs predict which branch will be taken. Predictable patterns run faster.

**C**:
```c
#include <stdio.h>
#include <time.h>

int main() {
    const int N = 100000000;
    int sum = 0;
    clock_t start, end;
    
    // Predictable pattern
    start = clock();
    for (int i = 0; i < N; i++) {
        if (i % 2 == 0) {  // Predictable: alternates
            sum++;
        }
    }
    end = clock();
    double predictable_time = (double)(end - start) / CLOCKS_PER_SEC;
    
    // Unpredictable pattern
    sum = 0;
    start = clock();
    for (int i = 0; i < N; i++) {
        if (rand() % 2 == 0) {  // Unpredictable
            sum++;
        }
    }
    end = clock();
    double unpredictable_time = (double)(end - start) / CLOCKS_PER_SEC; 
    ++) {
        if ((i * 1103515245 + 12345) & 1) {  // Pseudo-random
            sum++;
        }
    }
    end = clock();
    double unpredictable_time = (double)(end - start) / CLOCKS_PER_SEC;
    
    printf("Predictable: %.3fs\n", predictable_time);
    printf("Unpredictable: %.3fs\n", unpredictable_time);
    printf("Slowdown: %.2fx\n", unpredictable_time / predictable_time);
    
    return 0;
}
```

**Expected output** (depends on CPU):
```
Predictable: 0.250s
Unpredictable: 0.750s
Slowdown: 3.00x
```

**Lesson**: Branch prediction matters! Write code with predictable patterns when possible.

---

## Part 12: Interview Questions (Curated)

### Question 1: Precedence Puzzle
```python
result = not False or True and False
```

**Answer**: `True`

**Explanation**:
1. `not False` → `True`
2. `True and False` → `False`
3. `True or False` → `True`

---

### Question 2: De Morgan's Application
Simplify: `not (x > 5 or y < 10)`

**Answer**: `(x <= 5) and (y >= 10)`

---

### Question 3: Short-Circuit Behavior
```python
def func1():
    print("func1")
    return True

def func2():
    print("func2")
    return False

result = func1() or func2()
```

**What's printed?**

**Answer**: Only `"func1"`

**Explanation**: `func1()` returns `True`, so `or` short-circuits. `func2()` is never called.

---

### Question 4: Bitwise vs Logical
```c
int x = 5, y = 3;
int result1 = x && y;
int result2 = x & y;
```

**What are `result1` and `result2`?**

**Answer**: 
- `result1 = 1` (logical AND: both non-zero)
- `result2 = 1` (bitwise AND: `0101 & 0011 = 0001`)

---

### Question 5: Type Confusion (Rust)
```rust
let x = 5;
// if x { }  // What happens?
```

**Answer**: Compile error: `expected bool, found integer`

**Explanation**: Rust requires strict `bool` type for conditions.

---

### Question 6: Python Truthiness
```python
result = [] and [1, 2, 3]
```

**What's `result`?**

**Answer**: `[]`

**Explanation**: `[]` is falsy, so `and` short-circuits and returns `[]`.

---

### Question 7: C Chained Comparison
```c
int result = 5 < 10 < 20;
```

**What's `result`?**

**Answer**: `1` (true)

**Explanation**: Evaluated as `(5 < 10) < 20` → `1 < 20` → `1`. But this does **not** check if 10 is between 5 and 20!

---

### Question 8: Overloaded Operator (C++)
```cpp
class MyClass {
public:
    bool operator&&(const MyClass& other) {
        std::cout << "Custom && called\n";
        return true;
    }
};

MyClass a, b;
bool result = false && (a && b);
```

**What's printed?**

**Answer**: Nothing

**Explanation**: Built-in `&&` short-circuits. `false && ...` never evaluates the right side, so the custom operator is never called.

---

### Question 9: Float Equality
```python
a = 0.1 + 0.2
b = 0.3
print(a == b)
```

**What's printed?**

**Answer**: `False`

**Explanation**: Floating-point precision errors.

---

### Question 10: Boolean Simplification
Simplify: `(A and B) or (A and not B) or (not A and B)`

**Answer**: `A or B`

---

## Part 13: Practice Problems (Graduated Difficulty)

### Beginner Level

#### Problem 1
Evaluate: `True and not False or False`

<details>
<summary>Solution</summary>

1. `not False` → `True`
2. `True and True` → `True`
3. `True or False` → `True`

**Answer**: `True`
</details>

---

#### Problem 2
What's the output?
```python
x = 5
if x > 0 and x < 10:
    print("In range")
```

<details>
<summary>Solution</summary>

`x` is 5, which is between 0 and 10.

**Output**: `"In range"`
</details>

---

### Intermediate Level

#### Problem 3
Simplify: `(A or B) and (A or C)`

<details>
<summary>Solution</summary>

This doesn't simplify to `A or (B and C)` directly. Let's use truth table:

```
A | B | C | (A or B) | (A or C) | Result
--|---|---|----------|----------|-------
T | T | T |    T     |    T     |   T
T | T | F |    T     |    T     |   T
T | F | T |    T     |    T     |   T
T | F | F |    T     |    T     |   T
F | T | T |    T     |    T     |   T
F | T | F |    T     |    F     |   F
F | F | T |    F     |    T     |   F
F | F | F |    F     |    F     |   F
```

Compare with `A or (B and C)`:
```
A | B | C | B and C | A or (B and C)
--|---|---|---------|---------------
T | T | T |    T    |       T
T | T | F |    F    |       T
T | F | T |    F    |       T
T | F | F |    F    |       T
F | T | T |    T    |       T
F | T | F |    F    |       F
F | F | T |    F    |       F
F | F | F |    F    |       F
```

They match!

**Answer**: `A or (B and C)`

Alternatively, using distributive law:
```
(A or B) and (A or C)
= A or (B and C)  // Distributive law for OR over AND
```
</details>

---

#### Problem 4
What's the bug?
```c
int arr[] = {1, 2, 3};
int size = sizeof(arr) / sizeof(arr[0]);

if (size > 0 & arr[0] > 0) {
    printf("First element is positive\n");
}
```

<details>
<summary>Solution</summary>

Bug: Using `&` (bitwise AND) instead of `&&` (logical AND).

While it might work in this case (both operands are non-zero), it:
1. Doesn't short-circuit (inefficient)
2. Is semantically wrong (bitwise operation on boolean result)

**Fix**:
```c
if (size > 0 && arr[0] > 0) {
    printf("First element is positive\n");
}
```
</details>

---

### Advanced Level

#### Problem 5
Optimize this Rust code:
```rust
fn is_valid(x: i32, y: i32, z: i32) -> bool {
    if x > 0 {
        if y > 0 {
            if z > 0 {
                return true;
            }
        }
    }
    false
}
```

<details>
<summary>Solution</summary>

**Optimized**:
```rust
fn is_valid(x: i32, y: i32, z: i32) -> bool {
    x > 0 && y > 0 && z > 0
}
```

**Benefits**:
- Shorter
- More readable
- Still short-circuits (if `x > 0` is false, y and z aren't checked)
- Compiler generates identical assembly
</details>

---

#### Problem 6
Write a function to check if a number is a power of 2 using only bitwise operations.

<details>
<summary>Solution</summary>

**Insight**: A power of 2 has exactly one bit set. For example:
- `8 = 0b1000`
- `8 - 1 = 7 = 0b0111`
- `8 & 7 = 0`

**Python**:
```python
def is_power_of_two(n):
    return n > 0 and (n & (n - 1)) == 0
```

**Rust**:
```rust
fn is_power_of_two(n: i32) -> bool {
    n > 0 && (n & (n - 1)) == 0
}
```

**Why it works**: `n & (n - 1)` clears the lowest set bit. If `n` is a power of 2, it has only one bit set, so clearing it gives 0.
</details>

---

#### Problem 7
Explain why this C++ code doesn't compile:
```cpp
std::vector<int> vec = {1, 2, 3};
if (vec) {
    std::cout << "Vector is valid\n";
}
```

<details>
<summary>Solution</summary>

**Error**: `std::vector` doesn't define an implicit conversion to `bool`.

**Fix**: Check the condition you actually care about:
```cpp
if (!vec.empty()) {
    std::cout << "Vector has elements\n";
}
```

**Lesson**: Unlike Python, C++ doesn't have universal truthiness. Each type must explicitly define conversion to `bool`.
</details>

---

## Summary: Your Boolean Mastery Checklist

### Core Concepts
- [ ] Memorized truth tables for AND, OR, NOT, XOR, NAND, NOR
- [ ] Understand operator precedence in all 5 languages
- [ ] Can explain short-circuit evaluation and exploit it
- [ ] Distinguish bitwise vs logical operators
- [ ] Apply De Morgan's laws fluently

### Language-Specific
- [ ] **Python**: Understand truthiness, `and`/`or` return values
- [ ] **Rust**: Type safety, no implicit conversions, `Option`/`Result`
- [ ] **Go**: Simple semantics, comma-ok idiom, zero values
- [ ] **C**: Implicit conversions, assignment vs equality pitfalls
- [ ] **C++**: Operator overloading implications, modern features

### Advanced
- [ ] Read and understand assembly for boolean operations
- [ ] Apply boolean algebra to simplify expressions
- [ ] Recognize compiler optimizations
- [ ] Understand branch prediction impact on performance
- [ ] Write idiomatic boolean code in each language

### Meta-Learning
- [ ] Build deliberate practice routine (10 expressions daily)
- [ ] Create personal reference with edge cases
- [ ] Teach concepts to others (Feynman technique)
- [ ] Mix languages in practice (interleaving)

---

## Next Steps

1. **Implement a Boolean Expression Parser**: Write a parser and evaluator in Rust that handles arbitrary boolean expressions with variables.

2. **Study Compiler Source Code**: Look at how LLVM optimizes boolean expressions.

3. **Benchmark Different Patterns**: Measure performance of various boolean idioms in your target language.

4. **Read "Hacker's Delight"**: Chapter 2 covers boolean manipulation at the bit level.

5. **Practice Interview Questions**: Solve 50 boolean-related problems on LeetCode.

You've now got the complete picture—from mathematical foundations to assembly code. This is world-class knowledge. Apply it deliberately, and you'll be in the top 1%.

Ready to dive deeper into any specific area?