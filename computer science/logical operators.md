# Comprehensive Guide to Logical Operators

## Table of Contents
1. [Introduction](#introduction)
2. [Core Concepts](#core-concepts)
3. [The Three Main Operators](#the-three-main-operators)
4. [Truth Tables](#truth-tables)
5. [Basic Operations](#basic-operations)
6. [Logical Operators with Comparisons](#logical-operators-with-comparisons)
7. [Short-Circuit Evaluation](#short-circuit-evaluation)
8. [Bitwise vs Logical Operators](#bitwise-vs-logical-operators)
9. [Advanced Topics](#advanced-topics)
10. [Operator Precedence](#operator-precedence)
11. [Common Patterns](#common-patterns)
12. [Best Practices](#best-practices)

---

## Introduction

Logical operators are fundamental tools in programming that allow you to combine or modify boolean values (true/false) to make decisions in your code. Think of them as the building blocks for creating conditions and controlling program flow.

## Core Concepts

### What are Boolean Values?

Boolean values are the simplest data type in programming, representing only two possible states:
- **True** (1, yes, on)
- **False** (0, no, off)

These represent the foundation of binary logic and decision-making in code.

---

## The Three Main Operators

### 1. AND Operator
- **Symbol**: `&&` (Rust, Go) or `and` (Python)
- **Behavior**: Returns true only if BOTH conditions are true
- **Real-world analogy**: "I need my keys AND my wallet to leave the house"

### 2. OR Operator
- **Symbol**: `||` (Rust, Go) or `or` (Python)
- **Behavior**: Returns true if AT LEAST ONE condition is true
- **Real-world analogy**: "I can pay with cash OR credit card"

### 3. NOT Operator
- **Symbol**: `!` (Rust, Go) or `not` (Python)
- **Behavior**: Inverts/flips the boolean value
- **Real-world analogy**: "The opposite of true is false"

---

## Truth Tables

### AND Truth Table
```
A     | B     | A AND B
------|-------|--------
true  | true  | true
true  | false | false
false | true  | false
false | false | false
```
**Key insight**: Only true when ALL operands are true.

### OR Truth Table
```
A     | B     | A OR B
------|-------|--------
true  | true  | true
true  | false | true
false | true  | true
false | false | false
```
**Key insight**: True when AT LEAST ONE operand is true.

### NOT Truth Table
```
A     | NOT A
------|-------
true  | false
false | true
```
**Key insight**: Simply flips the value.

---

## Basic Operations

### Python Implementation

```python
# AND operator - both must be true
result1 = True and True    # True
result2 = True and False   # False
result3 = False and False  # False

# OR operator - at least one must be true
result4 = True or False    # True
result5 = False or False   # False
result6 = True or True     # True

# NOT operator - inverts the value
result7 = not True         # False
result8 = not False        # True

# Combining operators
age = 25
has_license = True
can_drive = age >= 18 and has_license  # True

# Using parentheses for precedence
is_weekend = True
is_holiday = False
has_work = False
can_sleep_in = (is_weekend or is_holiday) and not has_work
print(can_sleep_in)  # True
```

### Rust Implementation

```rust
fn main() {
    // AND operator - both must be true
    let result1 = true && true;    // true
    let result2 = true && false;   // false
    let result3 = false && false;  // false

    // OR operator - at least one must be true
    let result4 = true || false;   // true
    let result5 = false || false;  // false
    let result6 = true || true;    // true

    // NOT operator - inverts the value
    let result7 = !true;           // false
    let result8 = !false;          // true

    // Combining operators
    let age = 25;
    let has_license = true;
    let can_drive = age >= 18 && has_license;  // true

    // Using parentheses for precedence
    let is_weekend = true;
    let is_holiday = false;
    let has_work = false;
    let can_sleep_in = (is_weekend || is_holiday) && !has_work;
    println!("Can sleep in: {}", can_sleep_in);  // true
}
```

### Go Implementation

```go
package main

import "fmt"

func main() {
    // AND operator - both must be true
    result1 := true && true    // true
    result2 := true && false   // false
    result3 := false && false  // false

    // OR operator - at least one must be true
    result4 := true || false   // true
    result5 := false || false  // false
    result6 := true || true    // true

    // NOT operator - inverts the value
    result7 := !true           // false
    result8 := !false          // true

    // Combining operators
    age := 25
    hasLicense := true
    canDrive := age >= 18 && hasLicense  // true

    // Using parentheses for precedence
    isWeekend := true
    isHoliday := false
    hasWork := false
    canSleepIn := (isWeekend || isHoliday) && !hasWork
    fmt.Printf("Can sleep in: %v\n", canSleepIn)  // true
}
```

---

## Logical Operators with Comparisons

Logical operators become powerful when combined with comparison operators (`<`, `>`, `==`, `!=`, `<=`, `>=`).

### Python Examples

```python
x = 10
y = 20
z = 10

# AND with comparisons
print(x < y and z == x)     # True and True = True
print(x > y and z == x)     # False and True = False

# OR with comparisons
print(x == z or x > y)      # True or False = True
print(x > y or y < x)       # False or False = False

# NOT with comparisons
print(not x == y)           # not False = True
print(not (x < y))          # not True = False

# Complex real-world conditions
temperature = 75
is_sunny = True
has_umbrella = False

# Check if weather is good for outdoor activity
good_weather = temperature > 70 and temperature < 85 and is_sunny
print(f"Good weather: {good_weather}")  # True

# Check if you need an umbrella
need_umbrella = not is_sunny and not has_umbrella
print(f"Need umbrella: {need_umbrella}")  # False

# Python's elegant chained comparisons
age = 25
is_adult = 18 <= age <= 65  # Equivalent to: age >= 18 and age <= 65
print(is_adult)  # True
```

### Rust Examples

```rust
fn main() {
    let x = 10;
    let y = 20;
    let z = 10;

    // AND with comparisons
    println!("{}", x < y && z == x);     // true && true = true
    println!("{}", x > y && z == x);     // false && true = false

    // OR with comparisons
    println!("{}", x == z || x > y);     // true || false = true
    println!("{}", x > y || y < x);      // false || false = false

    // NOT with comparisons
    println!("{}", !(x == y));           // !false = true
    println!("{}", !(x < y));            // !true = false

    // Complex real-world conditions
    let temperature = 75;
    let is_sunny = true;
    let has_umbrella = false;

    let good_weather = temperature > 70 && temperature < 85 && is_sunny;
    println!("Good weather: {}", good_weather);  // true

    let need_umbrella = !is_sunny && !has_umbrella;
    println!("Need umbrella: {}", need_umbrella);  // false
    
    // Pattern matching with boolean logic
    match (is_sunny, has_umbrella) {
        (true, _) => println!("Enjoy the sunshine!"),
        (false, true) => println!("Good thing you have an umbrella"),
        (false, false) => println!("You might get wet!"),
    }
}
```

### Go Examples

```go
package main

import "fmt"

func main() {
    x := 10
    y := 20
    z := 10

    // AND with comparisons
    fmt.Println(x < y && z == x)     // true && true = true
    fmt.Println(x > y && z == x)     // false && true = false

    // OR with comparisons
    fmt.Println(x == z || x > y)     // true || false = true
    fmt.Println(x > y || y < x)      // false || false = false

    // NOT with comparisons
    fmt.Println(!(x == y))           // !false = true
    fmt.Println(!(x < y))            // !true = false

    // Complex real-world conditions
    temperature := 75
    isSunny := true
    hasUmbrella := false

    goodWeather := temperature > 70 && temperature < 85 && isSunny
    fmt.Printf("Good weather: %v\n", goodWeather)  // true

    needUmbrella := !isSunny && !hasUmbrella
    fmt.Printf("Need umbrella: %v\n", needUmbrella)  // false
    
    // Switch with boolean conditions
    switch {
    case isSunny && temperature > 70:
        fmt.Println("Perfect beach weather!")
    case !isSunny && hasUmbrella:
        fmt.Println("Good thing you have an umbrella")
    default:
        fmt.Println("Maybe stay inside")
    }
}
```

---

## Short-Circuit Evaluation

**Short-circuit evaluation** is a crucial optimization where the second operand isn't evaluated if the result is already determined by the first operand.

### How It Works

**AND (`&&`)**:
- If the first operand is `false`, the result MUST be `false`
- The second operand is never evaluated
- Example: `false && expensiveFunction()` → `expensiveFunction()` never runs

**OR (`||`)**:
- If the first operand is `true`, the result MUST be `true`
- The second operand is never evaluated
- Example: `true || expensiveFunction()` → `expensiveFunction()` never runs

### Why It Matters

1. **Performance optimization**: Avoid expensive operations
2. **Error prevention**: Check conditions before operations that might fail
3. **Conditional execution**: Use as a compact if-statement alternative

### Python Examples

```python
def expensive_function():
    print("Expensive function called!")
    return True

def another_function():
    print("Another function called!")
    return False

# AND short-circuit demonstration
print("\nAND short-circuit:")
result1 = False and expensive_function()  # expensive_function NOT called
print(f"Result: {result1}")  # False

result2 = True and expensive_function()   # expensive_function IS called
print(f"Result: {result2}")  # True

# OR short-circuit demonstration
print("\nOR short-circuit:")
result3 = True or another_function()      # another_function NOT called
print(f"Result: {result3}")  # True

result4 = False or another_function()     # another_function IS called
print(f"Result: {result4}")  # False

# Practical use case: avoiding AttributeError
user_data = None

# This would crash with AttributeError:
# if user_data.age > 18:

# This is safe thanks to short-circuit:
if user_data is not None and user_data.age > 18:
    print("User is adult")
else:
    print("User is None or not adult")

# Another practical example: list bounds checking
my_list = [1, 2, 3]
index = 5

# Safe access using short-circuit
if index < len(my_list) and my_list[index] > 0:
    print("Valid and positive")
else:
    print("Invalid index or not positive")
```

### Rust Examples

```rust
fn expensive_function() -> bool {
    println!("Expensive function called!");
    true
}

fn another_function() -> bool {
    println!("Another function called!");
    false
}

fn main() {
    // AND short-circuit demonstration
    println!("\nAND short-circuit:");
    let result1 = false && expensive_function();  // expensive_function NOT called
    println!("Result: {}", result1);  // false

    let result2 = true && expensive_function();   // expensive_function IS called
    println!("Result: {}", result2);  // true

    // OR short-circuit demonstration
    println!("\nOR short-circuit:");
    let result3 = true || another_function();     // another_function NOT called
    println!("Result: {}", result3);  // true

    let result4 = false || another_function();    // another_function IS called
    println!("Result: {}", result4);  // false

    // Practical use with Option type
    let user_age: Option<i32> = Some(25);
    
    // Safe check using short-circuit
    if user_age.is_some() && user_age.unwrap() > 18 {
        println!("User is adult");
    }
    
    // Better Rust idiom: using if let
    if let Some(age) = user_age {
        if age > 18 {
            println!("User is adult");
        }
    }
    
    // Vector bounds checking
    let vec = vec![1, 2, 3];
    let index = 5;
    
    // Safe access
    if index < vec.len() && vec[index] > 0 {
        println!("Valid and positive");
    }
}
```

### Go Examples

```go
package main

import "fmt"

func expensiveFunction() bool {
    fmt.Println("Expensive function called!")
    return true
}

func anotherFunction() bool {
    fmt.Println("Another function called!")
    return false
}

func main() {
    // AND short-circuit demonstration
    fmt.Println("\nAND short-circuit:")
    result1 := false && expensiveFunction()  // expensiveFunction NOT called
    fmt.Printf("Result: %v\n", result1)      // false

    result2 := true && expensiveFunction()   // expensiveFunction IS called
    fmt.Printf("Result: %v\n", result2)      // true

    // OR short-circuit demonstration
    fmt.Println("\nOR short-circuit:")
    result3 := true || anotherFunction()     // anotherFunction NOT called
    fmt.Printf("Result: %v\n", result3)      // true

    result4 := false || anotherFunction()    // anotherFunction IS called
    fmt.Printf("Result: %v\n", result4)      // false

    // Practical use: avoiding nil pointer dereference
    type User struct {
        Age int
    }
    
    var user *User = nil
    
    // This would crash with nil pointer dereference:
    // if user.Age > 18 {
    
    // This is safe using short-circuit:
    if user != nil && user.Age > 18 {
        fmt.Println("User is adult")
    } else {
        fmt.Println("User is nil or not adult")
    }
    
    // Slice bounds checking
    mySlice := []int{1, 2, 3}
    index := 5
    
    // Safe access
    if index < len(mySlice) && mySlice[index] > 0 {
        fmt.Println("Valid and positive")
    } else {
        fmt.Println("Invalid index or not positive")
    }
}
```

---

## Bitwise vs Logical Operators

**Important**: Don't confuse bitwise operators with logical operators! They serve different purposes.

### Comparison Table

| Purpose | Logical | Bitwise |
|---------|---------|---------|
| **Operators** | `&&`, `\|\|`, `!` (or `and`, `or`, `not`) | `&`, `\|`, `^`, `~` |
| **Works on** | Boolean values | Individual bits in integers |
| **Returns** | Boolean result | Integer result |
| **Use for** | Control flow, conditions | Bit manipulation, flags |

### Python Examples

```python
# Logical operators - for boolean logic
print("Logical Operators:")
print(True and False)   # False
print(True or False)    # True
print(not True)         # False

# Bitwise operators - for binary manipulation
print("\nBitwise Operators:")
a = 5   # Binary: 0101
b = 3   # Binary: 0011

print(f"{a} & {b} = {a & b}")   # 1 (0001) - AND
print(f"{a} | {b} = {a | b}")   # 7 (0111) - OR
print(f"~{a} = {~a}")           # -6 (inverts all bits) - NOT

# XOR (exclusive or) - true if values differ
print(f"\n{a} ^ {b} = {a ^ b}")   # 6 (0110)

# Bitwise shift operators
print(f"\n{a} << 1 = {a << 1}")   # 10 (multiply by 2)
print(f"{a} >> 1 = {a >> 1}")      # 2 (divide by 2)

# Practical example: checking if number is even
num = 42
is_even = (num & 1) == 0  # Check if last bit is 0
print(f"\n{num} is even: {is_even}")

# Using bitwise for flags
READ = 1 << 0    # 0001
WRITE = 1 << 1   # 0010
EXECUTE = 1 << 2 # 0100

permissions = READ | WRITE  # Combine permissions: 0011
can_read = (permissions & READ) != 0     # True
can_execute = (permissions & EXECUTE) != 0  # False

print(f"\nPermissions: {bin(permissions)}")
print(f"Can read: {can_read}")
print(f"Can execute: {can_execute}")
```

### Rust Examples

```rust
fn main() {
    // Logical operators - for boolean logic
    println!("Logical Operators:");
    println!("{}", true && false);   // false
    println!("{}", true || false);   // true
    println!("{}", !true);           // false

    // Bitwise operators - for binary manipulation
    println!("\nBitwise Operators:");
    let a: i32 = 5;   // Binary: 0101
    let b: i32 = 3;   // Binary: 0011

    println!("{} & {} = {}", a, b, a & b);   // 1 (0001)
    println!("{} | {} = {}", a, b, a | b);   // 7 (0111)
    println!("!{} = {}", a, !a);             // -6 (inverts all bits)

    // XOR (exclusive or) - true if values differ
    println!("\n{} ^ {} = {}", a, b, a ^ b);   // 6 (0110)

    // Bitwise shift operators
    println!("\n{} << 1 = {}", a, a << 1);   // 10
    println!("{} >> 1 = {}", a, a >> 1);      // 2

    // Practical: checking if number is even
    let num = 42;
    let is_even = (num & 1) == 0;
    println!("\n{} is even: {}", num, is_even);
    
    // Bit flags (common pattern in Rust)
    const READ: u8 = 0b0001;
    const WRITE: u8 = 0b0010;
    const EXECUTE: u8 = 0b0100;
    
    let permissions = READ | WRITE;  // Combine permissions
    let can_read = (permissions & READ) != 0;
    let can_execute = (permissions & EXECUTE) != 0;
    
    println!("\nCan read: {}", can_read);
    println!("Can execute: {}", can_execute);
}
```

### Go Examples

```go
package main

import "fmt"

func main() {
    // Logical operators - for boolean logic
    fmt.Println("Logical Operators:")
    fmt.Println(true && false)   // false
    fmt.Println(true || false)   // true
    fmt.Println(!true)           // false

    // Bitwise operators - for binary manipulation
    fmt.Println("\nBitwise Operators:")
    a := 5   // Binary: 0101
    b := 3   // Binary: 0011

    fmt.Printf("%d & %d = %d\n", a, b, a&b)   // 1 (0001)
    fmt.Printf("%d | %d = %d\n", a, b, a|b)   // 7 (0111)
    fmt.Printf("^%d = %d\n", a, ^a)           // -6 (inverts all bits)

    // XOR (exclusive or) - true if values differ
    fmt.Printf("\n%d ^ %d = %d\n", a, b, a^b)   // 6 (0110)

    // Bit clear (AND NOT) - unique to Go
    fmt.Printf("%d &^ %d = %d\n", a, b, a&^b)  // 4 (0100)

    // Bitwise shift operators
    fmt.Printf("\n%d << 1 = %d\n", a, a<<1)   // 10
    fmt.Printf("%d >> 1 = %d\n", a, a>>1)      // 2

    // Practical: checking if number is even
    num := 42
    isEven := (num & 1) == 0
    fmt.Printf("\n%d is even: %v\n", num, isEven)
    
    // Bit flags pattern (idiomatic Go)
    const (
        FlagRead    = 1 << iota  // 1 (0001)
        FlagWrite                // 2 (0010)
        FlagExecute              // 4 (0100)
    )
    
    permissions := FlagRead | FlagWrite  // Combine permissions
    canRead := (permissions & FlagRead) != 0
    canExecute := (permissions & FlagExecute) != 0
    
    fmt.Printf("\nCan read: %v\n", canRead)
    fmt.Printf("Can execute: %v\n", canExecute)
}
```

### When to Use Each

**Use Logical Operators (`&&`, `||`, `!`) when:**
- Making decisions in if statements
- Combining boolean conditions
- Controlling program flow
- Working with true/false values

**Use Bitwise Operators (`&`, `|`, `^`, `~`) when:**
- Setting/checking individual bits
- Working with flags or permissions
- Low-level optimization
- Network protocols or file formats
- Cryptography or compression

---

## Advanced Topics

### De Morgan's Laws

De Morgan's Laws are mathematical principles that help simplify complex logical expressions:

**Law 1**: `NOT (A AND B) = (NOT A) OR (NOT B)`
**Law 2**: `NOT (A OR B) = (NOT A) AND (NOT B)`

#### Python Examples

```python
# De Morgan's Laws demonstration
x = True
y = False

# Law 1: NOT (A AND B) = NOT A OR NOT B
law1_left = not (x and y)
law1_right = (not x) or (not y)
print(f"Law 1: {law1_left} == {law1_right}")  # True == True

# Law 2: NOT (A OR B) = NOT A AND NOT B
law2_left = not (x or y)
law2_right = (not x) and (not y)
print(f"Law 2: {law2_left} == {law2_right}")  # False == False

# Practical application
is_weekend = False
is_sunny = False

# Original condition
not_good_day = not (is_weekend and is_sunny)

# Simplified using De Morgan's Law
not_good_day_simplified = (not is_weekend) or (not is_sunny)

print(f"Results match: {not_good_day == not_good_day_simplified}")
```

### Truthiness and Falsiness

**Python** has flexible truthy/falsy evaluation:

```python
# Falsy values in Python
falsy_values = [False, None, 0, 0.0, "", [], {}, (), set()]

for val in falsy_values:
    if not val:
        print(f"{repr(val):12} is falsy")

# Truthy values (everything else)
truthy_values = [True, 1, "hello", [1], {"a": 1}, (1,), {1}]

for val in truthy_values:
    if val:
        print(f"{repr(val):12} is truthy")

# Practical use
name = input("Enter name: ")
if name:  # Empty string is falsy
    print(f"Hello, {name}!")
else:
    print("No name provided")

# Default values using 'or'
username = "" or "Anonymous"  # "Anonymous"
port = 0 or 8080              # 8080
items = [] or ["default"]     # ["default"]
```

**Rust** requires explicit boolean values:

```rust
fn main() {
    // Rust does NOT have implicit truthiness
    let name = String::from("");
    
    // This won't compile:
    // if name { }
    
    // Must be explicit:
    if !name.is_empty() {
        println!("Name: {}", name);
    }
    
    // Option handling
    let maybe_value: Option<i32> = None;
    
    if maybe_value.is_some() {
        println!("Has value");
    }
    
    // Better: using if let
    if let Some(value) = maybe_value {
        println!("Value: {}", value);
    }
}
```

**Go** also requires explicit boolean values:

```go
package main

import "fmt"

func main() {
    // Go does NOT have implicit truthiness
    name := ""
    
    // This won't compile:
    // if name { }
    
    // Must be explicit:
    if len(name) > 0 {
        fmt.Printf("Name: %s\n", name)
    }
    
    // Checking for nil
    var ptr *int = nil
    
    if ptr != nil {
        fmt.Println("Has value")
    }
    
    // Checking empty slices
    items := []int{}
    if len(items) == 0 {
        fmt.Println("Empty slice")
    }
}
```

### All and Any Operations

#### Python Built-in Functions

```python
# all() - returns True if ALL elements are truthy
grades = [85, 90, 78, 92]
all_passed = all(grade >= 70 for grade in grades)
print(f"All passed: {all_passed}")  # True

empty_list = []
print(f"all([]) = {all(empty_list)}")  # True (vacuous truth)

# any() - returns True if ANY element is truthy
any_excellent = any(grade >= 90 for grade in grades)
print(f"Any excellent: {any_excellent}")  # True

print(f"any([]) = {any([])}")  # False

# Practical examples
# Check if all items in cart are in stock
cart = [
    {"name": "Book", "in_stock": True},
    {"name": "Pen", "in_stock": True},
    {"name": "Notebook", "in_stock": True}
]
can_checkout = all(item["in_stock"] for item in cart)
print(f"Can checkout: {can_checkout}")

# Check if any payment method is available
payment_methods = {
    "credit_card": False,
    "paypal": True,
    "bitcoin": False
}
can_pay = any(payment_methods.values())
print(f"Can pay: {can_pay}")
```

#### Rust Iterators

```rust
fn main() {
    // all() - check if all elements satisfy condition
    let grades = vec![85, 90, 78, 92];
    let all_passed = grades.iter().all(|&grade| grade >= 70);
    println!("All passed: {}", all_passed);  // true

    // any() - check if any element satisfies condition
    let any_excellent = grades.iter().any(|&grade| grade >= 90);
    println!("Any excellent: {}", any_excellent);  // true

    // Practical example with structs
    struct Item {
        name: String,
        in_stock: bool,
    }

    let cart = vec![
        Item { name: "Book".to_string(), in_stock: true },
        Item { name: "Pen".to_string(), in_stock: true },
        Item { name: "Notebook".to_string(), in_stock: false },
    ];

    let can_checkout = cart.iter().all(|item| item.in_stock);
    println!("Can checkout: {}", can_checkout);  // false

    let has_available_items = cart.iter().any(|item| item.in_stock);
    println!("Has available items: {}", has_available_items);  // true
}
```

#### Go Manual Implementation

```go
package main

import "fmt"

func main() {
    // Go doesn't have built-in all/any, implement manually
    grades := []int{85, 90, 78, 92}
    
    // Check if all passed
    allPassed := true
    for _, grade := range grades {
        if grade < 70 {
            allPassed = false
            break
        }
    }
    fmt.Printf("All passed: %v\n", allPassed)
    
    // Check if any excellent
    anyExcellent := false
    for _, grade := range grades {
        if grade >= 90 {
            anyExcellent = true
            break
        }
    }
    fmt.Printf("Any excellent: %v\n", anyExcellent)
    
    // Generic helper functions (Go 1.18+)
    type Item struct {
        Name    string
        InStock bool
    }
    
    cart := []Item{
        {"Book", true},
        {"Pen", true},
        {"Notebook", false},
    }
    
    canCheckout := All(cart, func(item Item) bool {
        return item.InStock
    })
    fmt.Printf("Can checkout: %v\n", canCheckout)
}

// Generic All function
func All[T any](slice []T, predicate func(T) bool) bool {
    for _, item := range slice {
        if !predicate(item) {
            return false
        }
    }
    return true
}

// Generic Any function
func Any[T any](slice []T, predicate func(T) bool) bool {
    for _, item := range slice {
        if predicate(item) {
            return true
        }
    }
    return false
}
```

### Complex Condition Handling

#### Python

```python
# Break complex conditions into named variables
score = 85
attendance = 90
participation = 75
extra_credit = 10

# Bad: hard to read
if score >= 70 and attendance >= 80 and (participation >= 70 or score >= 90 or extra_credit >= 10):
    print("Passed")

# Good: readable and maintainable
has_passing_score = score >= 70
has_good_attendance = attendance >= 80
has_participation = participation >= 70
has_excellent_score = score >= 90
has_extra_credit = extra_credit >= 10

```python
meets_basic_requirements = has_passing_score and has_good_attendance
has_bonus_criteria = has_participation or has_excellent_score or has_extra_credit

passed = meets_basic_requirements and has_bonus_criteria
print(f"Passed: {passed}")

# Multiple condition patterns
def can_access_resource(user, resource):
    """Check if user can access a resource"""
    # Break down complex logic
    is_owner = user.id == resource.owner_id
    is_admin = user.role == "admin"
    is_public = resource.visibility == "public"
    has_permission = resource.id in user.permissions
    
    # Combine logically
    return is_owner or is_admin or (is_public and has_permission)

# Using helper functions for clarity
def is_business_hours(hour):
    return 9 <= hour <= 17

def is_weekday(day):
    return day not in ["Saturday", "Sunday"]

def can_make_call(hour, day, is_urgent):
    during_hours = is_business_hours(hour) and is_weekday(day)
    return during_hours or is_urgent
```

#### Rust

```rust
fn main() {
    // Break complex conditions into named variables
    let score = 85;
    let attendance = 90;
    let participation = 75;
    let extra_credit = 10;

    // Good: readable and maintainable
    let has_passing_score = score >= 70;
    let has_good_attendance = attendance >= 80;
    let has_participation = participation >= 70;
    let has_excellent_score = score >= 90;
    let has_extra_credit = extra_credit >= 10;

    let meets_basic_requirements = has_passing_score && has_good_attendance;
    let has_bonus_criteria = has_participation || has_excellent_score || has_extra_credit;

    let passed = meets_basic_requirements && has_bonus_criteria;
    println!("Passed: {}", passed);

    // Pattern matching with guards (Rust-specific)
    let status = match score {
        s if s >= 90 && attendance >= 90 => "Excellent",
        s if s >= 80 && attendance >= 80 => "Good",
        s if s >= 70 && attendance >= 70 => "Pass",
        _ => "Fail",
    };
    println!("Status: {}", status);
}

// Struct-based approach for complex conditions
struct User {
    id: u32,
    role: String,
    permissions: Vec<u32>,
}

struct Resource {
    id: u32,
    owner_id: u32,
    visibility: String,
}

fn can_access_resource(user: &User, resource: &Resource) -> bool {
    let is_owner = user.id == resource.owner_id;
    let is_admin = user.role == "admin";
    let is_public = resource.visibility == "public";
    let has_permission = user.permissions.contains(&resource.id);
    
    is_owner || is_admin || (is_public && has_permission)
}

// Using helper functions
fn is_business_hours(hour: u8) -> bool {
    (9..=17).contains(&hour)
}

fn is_weekday(day: &str) -> bool {
    !matches!(day, "Saturday" | "Sunday")
}

fn can_make_call(hour: u8, day: &str, is_urgent: bool) -> bool {
    let during_hours = is_business_hours(hour) && is_weekday(day);
    during_hours || is_urgent
}
```

#### Go

```go
package main

import "fmt"

func main() {
    // Break complex conditions into named variables
    score := 85
    attendance := 90
    participation := 75
    extraCredit := 10

    // Good: readable and maintainable
    hasPassingScore := score >= 70
    hasGoodAttendance := attendance >= 80
    hasParticipation := participation >= 70
    hasExcellentScore := score >= 90
    hasExtraCredit := extraCredit >= 10

    meetsBasicRequirements := hasPassingScore && hasGoodAttendance
    hasBonusCriteria := hasParticipation || hasExcellentScore || hasExtraCredit

    passed := meetsBasicRequirements && hasBonusCriteria
    fmt.Printf("Passed: %v\n", passed)

    // Switch with complex conditions
    var status string
    switch {
    case score >= 90 && attendance >= 90:
        status = "Excellent"
    case score >= 80 && attendance >= 80:
        status = "Good"
    case score >= 70 && attendance >= 70:
        status = "Pass"
    default:
        status = "Fail"
    }
    fmt.Printf("Status: %s\n", status)
}

// Struct-based approach
type User struct {
    ID          uint32
    Role        string
    Permissions []uint32
}

type Resource struct {
    ID         uint32
    OwnerID    uint32
    Visibility string
}

func canAccessResource(user *User, resource *Resource) bool {
    isOwner := user.ID == resource.OwnerID
    isAdmin := user.Role == "admin"
    isPublic := resource.Visibility == "public"
    hasPermission := contains(user.Permissions, resource.ID)
    
    return isOwner || isAdmin || (isPublic && hasPermission)
}

func contains(slice []uint32, item uint32) bool {
    for _, v := range slice {
        if v == item {
            return true
        }
    }
    return false
}

// Helper functions
func isBusinessHours(hour int) bool {
    return hour >= 9 && hour <= 17
}

func isWeekday(day string) bool {
    return day != "Saturday" && day != "Sunday"
}

func canMakeCall(hour int, day string, isUrgent bool) bool {
    duringHours := isBusinessHours(hour) && isWeekday(day)
    return duringHours || isUrgent
}
```

---

## Operator Precedence

Understanding operator precedence is crucial for writing correct logical expressions.

### Precedence Order (highest to lowest)

1. **Parentheses** `()`
2. **NOT** `!` / `not`
3. **Comparison operators** `<`, `>`, `==`, `!=`, `<=`, `>=`
4. **AND** `&&` / `and`
5. **OR** `||` / `or`

### Examples

```python
# Python examples
x = 5
y = 10
z = 15

# Without parentheses - following precedence
result1 = not x > y or z < y
# Evaluated as: ((not (x > y)) or (z < y))
# Step 1: x > y = False
# Step 2: not False = True
# Step 3: z < y = True
# Step 4: True or True = True
print(result1)  # True

# With parentheses - explicit control
result2 = not (x > y or z < y)
# Step 1: x > y = False
# Step 2: z < y = True
# Step 3: False or True = True
# Step 4: not True = False
print(result2)  # False

# Complex example
a = True
b = False
c = True

result3 = a or b and c  # a or (b and c)
print(result3)  # True

result4 = (a or b) and c  # Different grouping
print(result4)  # True

# Another example
result5 = not a or b and c  # (not a) or (b and c)
print(result5)  # False

result6 = not (a or b) and c  # Different meaning
print(result6)  # False
```

### Best Practice: Use Parentheses

```python
# Bad: relies on precedence knowledge
if user.is_active and user.age >= 18 or user.is_admin:
    grant_access()

# Good: explicit intent
if (user.is_active and user.age >= 18) or user.is_admin:
    grant_access()

# Also good: break into variables
is_adult_user = user.is_active and user.age >= 18
can_access = is_adult_user or user.is_admin
if can_access:
    grant_access()
```

---

## Common Patterns

### 1. Input Validation

#### Python
```python
def validate_user_input(username, password, email):
    """Validate user registration input"""
    # Check username
    username_valid = (
        username is not None and
        len(username) >= 3 and
        len(username) <= 20 and
        username.isalnum()
    )
    
    # Check password
    password_valid = (
        password is not None and
        len(password) >= 8 and
        any(c.isupper() for c in password) and
        any(c.islower() for c in password) and
        any(c.isdigit() for c in password)
    )
    
    # Check email
    email_valid = (
        email is not None and
        "@" in email and
        "." in email.split("@")[1]
    )
    
    return username_valid and password_valid and email_valid

# Usage
if validate_user_input("john_doe", "SecurePass123", "john@example.com"):
    print("Valid registration")
else:
    print("Invalid input")
```

#### Rust
```rust
fn validate_user_input(username: &str, password: &str, email: &str) -> bool {
    // Check username
    let username_valid = username.len() >= 3 
        && username.len() <= 20
        && username.chars().all(|c| c.is_alphanumeric());
    
    // Check password
    let password_valid = password.len() >= 8
        && password.chars().any(|c| c.is_uppercase())
        && password.chars().any(|c| c.is_lowercase())
        && password.chars().any(|c| c.is_numeric());
    
    // Check email
    let email_valid = email.contains('@') 
        && email.split('@').nth(1).map_or(false, |domain| domain.contains('.'));
    
    username_valid && password_valid && email_valid
}

fn main() {
    if validate_user_input("john_doe", "SecurePass123", "john@example.com") {
        println!("Valid registration");
    } else {
        println!("Invalid input");
    }
}
```

#### Go
```go
package main

import (
    "fmt"
    "strings"
    "unicode"
)

func validateUserInput(username, password, email string) bool {
    // Check username
    usernameValid := len(username) >= 3 &&
        len(username) <= 20 &&
        isAlphanumeric(username)
    
    // Check password
    passwordValid := len(password) >= 8 &&
        hasUppercase(password) &&
        hasLowercase(password) &&
        hasDigit(password)
    
    // Check email
    emailValid := strings.Contains(email, "@") &&
        strings.Contains(strings.Split(email, "@")[1], ".")
    
    return usernameValid && passwordValid && emailValid
}

func isAlphanumeric(s string) bool {
    for _, r := range s {
        if !unicode.IsLetter(r) && !unicode.IsDigit(r) {
            return false
        }
    }
    return true
}

func hasUppercase(s string) bool {
    for _, r := range s {
        if unicode.IsUpper(r) {
            return true
        }
    }
    return false
}

func hasLowercase(s string) bool {
    for _, r := range s {
        if unicode.IsLower(r) {
            return true
        }
    }
    return false
}

func hasDigit(s string) bool {
    for _, r := range s {
        if unicode.IsDigit(r) {
            return true
        }
    }
    return false
}

func main() {
    if validateUserInput("john_doe", "SecurePass123", "john@example.com") {
        fmt.Println("Valid registration")
    } else {
        fmt.Println("Invalid input")
    }
}
```

### 2. Default Values

#### Python
```python
# Using 'or' for default values (leverages truthiness)
name = user_input or "Anonymous"
port = config_port or 8080
items = user_items or []

# More examples
def greet(name=None):
    display_name = name or "Guest"
    print(f"Hello, {display_name}!")

# Multiple fallbacks
primary = None
secondary = ""
tertiary = "default"
value = primary or secondary or tertiary  # "default"

# With functions
def get_user_setting(key):
    return user_settings.get(key) or default_settings.get(key) or "N/A"
```

#### Rust
```rust
fn main() {
    // Using Option and unwrap_or
    let name = Some("John");
    let display_name = name.unwrap_or("Anonymous");
    println!("Hello, {}!", display_name);
    
    // Using unwrap_or_else for lazy evaluation
    let port = None;
    let actual_port = port.unwrap_or_else(|| {
        println!("Computing default port");
        8080
    });
    
    // Pattern matching approach
    let items: Option<Vec<i32>> = None;
    let actual_items = match items {
        Some(i) => i,
        None => vec![],
    };
    
    // Multiple fallbacks using or
    let primary: Option<String> = None;
    let secondary: Option<String> = Some("fallback".to_string());
    let value = primary.or(secondary).unwrap_or("default".to_string());
    println!("{}", value);
}
```

#### Go
```go
package main

import "fmt"

func main() {
    // Go requires explicit checks
    var name string
    if name == "" {
        name = "Anonymous"
    }
    
    var port int
    if port == 0 {
        port = 8080
    }
    
    // Helper function for default values
    displayName := defaultString(name, "Guest")
    fmt.Printf("Hello, %s!\n", displayName)
    
    // Multiple fallbacks
    primary := ""
    secondary := ""
    tertiary := "default"
    
    value := primary
    if value == "" {
        value = secondary
    }
    if value == "" {
        value = tertiary
    }
    fmt.Println(value)  // "default"
}

func defaultString(value, defaultValue string) string {
    if value == "" {
        return defaultValue
    }
    return value
}

func defaultInt(value, defaultValue int) int {
    if value == 0 {
        return defaultValue
    }
    return value
}
```

### 3. Range Checking

#### Python
```python
# Elegant chained comparisons (Python-specific)
age = 25
if 18 <= age <= 65:
    print("Working age")

temperature = 72
if 60 <= temperature <= 80:
    print("Comfortable temperature")

# With AND operator (works in all languages)
score = 85
if score >= 70 and score <= 100:
    print("Valid score")

# Multiple range checks
def categorize_temperature(temp):
    if temp < 32:
        return "Freezing"
    elif 32 <= temp < 50:
        return "Cold"
    elif 50 <= temp < 70:
        return "Cool"
    elif 70 <= temp < 85:
        return "Comfortable"
    else:
        return "Hot"
```

#### Rust
```rust
fn main() {
    // Using comparison operators
    let age = 25;
    if age >= 18 && age <= 65 {
        println!("Working age");
    }
    
    // Using ranges (Rust-specific)
    let temperature = 72;
    if (60..=80).contains(&temperature) {
        println!("Comfortable temperature");
    }
    
    // Pattern matching with ranges
    let score = 85;
    match score {
        0..=59 => println!("Fail"),
        60..=69 => println!("D"),
        70..=79 => println!("C"),
        80..=89 => println!("B"),
        90..=100 => println!("A"),
        _ => println!("Invalid score"),
    }
}

fn categorize_temperature(temp: i32) -> &'static str {
    match temp {
        i32::MIN..=31 => "Freezing",
        32..=49 => "Cold",
        50..=69 => "Cool",
        70..=84 => "Comfortable",
        85..=i32::MAX => "Hot",
    }
}
```

#### Go
```go
package main

import "fmt"

func main() {
    // Using comparison operators
    age := 25
    if age >= 18 && age <= 65 {
        fmt.Println("Working age")
    }
    
    temperature := 72
    if temperature >= 60 && temperature <= 80 {
        fmt.Println("Comfortable temperature")
    }
    
    // Switch with range checks
    score := 85
    switch {
    case score >= 90 && score <= 100:
        fmt.Println("A")
    case score >= 80 && score < 90:
        fmt.Println("B")
    case score >= 70 && score < 80:
        fmt.Println("C")
    case score >= 60 && score < 70:
        fmt.Println("D")
    default:
        fmt.Println("F")
    }
}

func categorizeTemperature(temp int) string {
    switch {
    case temp < 32:
        return "Freezing"
    case temp >= 32 && temp < 50:
        return "Cold"
    case temp >= 50 && temp < 70:
        return "Cool"
    case temp >= 70 && temp < 85:
        return "Comfortable"
    default:
        return "Hot"
    }
}
```

### 4. Permission/Authorization Checks

#### Python
```python
def can_edit_post(user, post):
    """Check if user can edit a post"""
    is_author = user.id == post.author_id
    is_admin = user.role == "admin"
    is_moderator = user.role == "moderator"
    post_is_locked = post.locked
    
    # Author can always edit their own post
    # Admin can edit any post
    # Moderator can edit if post isn't locked
    return (is_author or is_admin or (is_moderator and not post_is_locked))

def can_delete_comment(user, comment):
    """Check if user can delete a comment"""
    is_commenter = user.id == comment.user_id
    is_admin = user.role == "admin"
    is_post_author = user.id == comment.post.author_id
    
    # Can delete if: own comment, admin, or post author
    return is_commenter or is_admin or is_post_author

# Usage
class User:
    def __init__(self, id, role):
        self.id = id
        self.role = role

class Post:
    def __init__(self, author_id, locked=False):
        self.author_id = author_id
        self.locked = locked

user = User(1, "moderator")
post = Post(2, locked=False)

if can_edit_post(user, post):
    print("User can edit post")
```

#### Rust
```rust
struct User {
    id: u32,
    role: String,
}

struct Post {
    author_id: u32,
    locked: bool,
}

struct Comment {
    user_id: u32,
    post_author_id: u32,
}

fn can_edit_post(user: &User, post: &Post) -> bool {
    let is_author = user.id == post.author_id;
    let is_admin = user.role == "admin";
    let is_moderator = user.role == "moderator";
    
    is_author || is_admin || (is_moderator && !post.locked)
}

fn can_delete_comment(user: &User, comment: &Comment) -> bool {
    let is_commenter = user.id == comment.user_id;
    let is_admin = user.role == "admin";
    let is_post_author = user.id == comment.post_author_id;
    
    is_commenter || is_admin || is_post_author
}

fn main() {
    let user = User {
        id: 1,
        role: "moderator".to_string(),
    };
    
    let post = Post {
        author_id: 2,
        locked: false,
    };
    
    if can_edit_post(&user, &post) {
        println!("User can edit post");
    }
}
```

#### Go
```go
package main

import "fmt"

type User struct {
    ID   uint32
    Role string
}

type Post struct {
    AuthorID uint32
    Locked   bool
}

type Comment struct {
    UserID       uint32
    PostAuthorID uint32
}

func canEditPost(user *User, post *Post) bool {
    isAuthor := user.ID == post.AuthorID
    isAdmin := user.Role == "admin"
    isModerator := user.Role == "moderator"
    
    return isAuthor || isAdmin || (isModerator && !post.Locked)
}

func canDeleteComment(user *User, comment *Comment) bool {
    isCommenter := user.ID == comment.UserID
    isAdmin := user.Role == "admin"
    isPostAuthor := user.ID == comment.PostAuthorID
    
    return isCommenter || isAdmin || isPostAuthor
}

func main() {
    user := &User{
        ID:   1,
        Role: "moderator",
    }
    
    post := &Post{
        AuthorID: 2,
        Locked:   false,
    }
    
    if canEditPost(user, post) {
        fmt.Println("User can edit post")
    }
}
```

---

## Best Practices

### 1. Keep Conditions Simple

```python
# Bad: complex nested conditions
if user:
    if user.is_active:
        if user.has_permission("read"):
            if not user.is_banned:
                if resource.is_available:
                    grant_access()

# Good: combine with AND
if (user and 
    user.is_active and 
    user.has_permission("read") and 
    not user.is_banned and 
    resource.is_available):
    grant_access()

# Better: early returns
if not user:
    return deny_access()
if not user.is_active:
    return deny_access()
if not user.has_permission("read"):
    return deny_access()
if user.is_banned:
    return deny_access()
if not resource.is_available:
    return deny_access()
    
grant_access()
```

### 2. Use Named Variables

```python
# Bad: unclear intent
if (x > 0 and x < 100) and (y > 0 and y < 100) and (x + y < 150):
    process()

# Good: named variables explain intent
is_x_valid = 0 < x < 100
is_y_valid = 0 < y < 100
is_sum_valid = x + y < 150

if is_x_valid and is_y_valid and is_sum_valid:
    process()
```

### 3. Avoid Double Negatives

```python
# Bad: hard to understand
if not user.is_not_banned:
    grant_access()

# Good: positive logic
if user.is_active:
    grant_access()

# Bad: confusing
if not (not is_valid or is_expired):
    proceed()

# Good: apply De Morgan's Law
if is_valid and not is_expired:
    proceed()
```

### 4. Use Short-Circuit to Your Advantage

```python
# Check cheapest condition first
if is_cache_valid() and expensive_database_query():
    process_data()

# Prevent errors
if user is not None and user.age > 18:
    grant_adult_access()

# Avoid unnecessary work
if quick_check() or detailed_verification():
    proceed()
```

### 5. Be Consistent with Style

```python
# Choose one style and stick with it

# Style 1: Compact
if user and user.is_active and user.has_permission:
    grant_access()

# Style 2: Multiline for readability
if (user and 
    user.is_active and 
    user.has_permission):
    grant_access()

# Style 3: Parenthesized groups
if (user and user.is_active) and user.has_permission:
    grant_access()
```

### 6. Comment Complex Logic

```python
# Good: comment explains WHY
# Allow access if user is owner OR (is member AND resource is shared)
if user.id == resource.owner_id or (user.is_member and resource.is_shared):
    grant_access()

# Better: self-documenting code
is_owner = user.id == resource.owner_id
can_access_shared = user.is_member and resource.is_shared

if is_owner or can_access_shared:
    grant_access()
```

---

## Common Mistakes to Avoid

### 1. Confusing `=` with `==`

```python
# WRONG: Assignment instead of comparison
x = 5
if x = 10:  # SyntaxError in Python
    print("Equal")

# CORRECT
if x == 10:
    print("Equal")
```

```rust
// Rust prevents this at compile time
let x = 5;
// if x = 10 {  // Compile error: expected `bool`, found `()`
if x == 10 {
    println!("Equal");
}
```

```go
// Go also prevents this at compile time
x := 5
// if x = 10 {  // Compile error: non-boolean condition
if x == 10 {
    fmt.Println("Equal")
}
```

### 2. Confusing Bitwise and Logical Operators

```python
# WRONG: Using bitwise operator for boolean logic
if True & False:  # 0 (falsy), but not idiomatic
    print("Won't print")

# CORRECT
if True and False:
    print("Won't print")
```

### 3. Not Handling None/Nil/Null

```python
# WRONG: Will crash with AttributeError
user = None
if user.age > 18:
    print("Adult")

# CORRECT: Check existence first
if user and user.age > 18:
    print("Adult")

# ALSO CORRECT: Using try-except
try:
    if user.age > 18:
        print("Adult")
except AttributeError:
    print("User is None")
```

### 4. Overly Complex Conditions

```python
# BAD: Too complex to understand
if ((a and b) or (c and d)) and not (e or (f and not g)) or (h and i and not j):
    process()

# GOOD: Break it down
condition1 = (a and b) or (c and d)
condition2 = not (e or (f and not g))
condition3 = h and i and not j

if (condition1 and condition2) or condition3:
    process()

# BETTER: Use helper functions
if should_process(a, b, c, d, e, f, g, h, i, j):
    process()
```

### 5. Forgetting Operator Precedence

```python
# UNCLEAR: Relies on precedence knowledge
if not user.is_active and user.age > 18:
    # Is it: (not user.is_active) and (user.age > 18)
    # Or: not (user.is_active and user.age > 18)?
    block_user()

# CLEAR: Use parentheses
if (not user.is_active) and (user.age > 18):
    block_user()
```

---

## Summary

### Quick Reference Table

| Feature | Python | Rust | Go |
|---------|--------|------|-----|
| **AND** | `and` or `&` | `&&` | `&&` |
| **OR** | `or` or `\|` | `\|\|` | `\|\|` |
| **NOT** | `not` | `!` | `!` |
| **Truthiness** | Yes | No | No |
| **Short-circuit** | Yes | Yes | Yes |
| **Chained comparisons** | Yes | No | No |

### Key Takeaways

1. **AND** returns true only when ALL conditions are true
2. **OR** returns true when AT LEAST ONE condition is true
3. **NOT** inverts the boolean value
4. **Short-circuit evaluation** can prevent errors and improve performance
5. **Use parentheses** to make complex conditions clear
6. **Break complex logic** into named variables or helper functions
7. **Bitwise operators** are different from logical operators
8. **Test edge cases** like None/nil/null values
9. **Apply De Morgan's Laws** to simplify complex negations
10. **Be consistent** with your coding style

### Practice Exercises

Try implementing these on your own:

1. Write a function to check if a year is a leap year
2. Create a password strength validator
3. Implement a permission system with roles
4. Build a validator for form inputs
5. Write a function to determine if three sides can form a triangle

Remember: The best way to master logical operators is through practice. Start with simple conditions and gradually build up to more complex scenarios!