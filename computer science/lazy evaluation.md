# Comprehensive Guide to Short-Circuit Evaluation (Lazy Evaluation)

## What is Short-Circuit Evaluation?

Short-circuit evaluation is a programming concept where the second argument of a logical operation is **only evaluated if necessary**. It's called "short-circuit" because the evaluation stops early—like an electrical short circuit that takes a shortcut.

Think of it like this: If you're checking "Is it raining AND do I need an umbrella?", and you look outside to see bright sunshine, you don't even need to think about the umbrella question. The answer is already "no."

## Core Concepts

### Boolean Operators

**AND (`&&` or `and`)**
- Returns `true` only if **both** operands are true
- Short-circuits when the first operand is `false` (no need to check the second)
- Pattern: `false && anything` → always `false`

**OR (`||` or `or`)**
- Returns `true` if **at least one** operand is true
- Short-circuits when the first operand is `true` (no need to check the second)
- Pattern: `true || anything` → always `true`

### Why Does This Matter?

1. **Performance**: Avoid expensive computations when they're unnecessary
2. **Safety**: Prevent errors (like null pointer dereferences or division by zero)
3. **Side Effects**: Control when certain code executes
4. **Clean Code**: Write more concise conditional logic

## Detailed Examples in Three Languages

### Python Implementation

```python
# Basic Short-Circuit with AND
def expensive_check():
    print("Expensive check called!")
    return True

x = None
# Safe null check - second part never executes if x is None
if x is not None and x.expensive_check():
    print("Both conditions met")

# Output: Nothing! expensive_check() is never called because x is None

# Short-Circuit with OR
def process_data():
    print("Processing data...")
    return [1, 2, 3]

cache = [4, 5, 6]
# Use cached data if available, otherwise process
result = cache or process_data()
print(result)  # Output: [4, 5, 6] - process_data() never called

# Practical Example: Division by Zero Protection
def safe_divide(a, b):
    # b != 0 is checked first, preventing division by zero
    if b != 0 and a / b > 10:
        return "Large quotient"
    return "Safe"

print(safe_divide(100, 0))  # Output: "Safe" - no error!

# Using Short-Circuit for Default Values
user_input = ""
name = user_input or "Anonymous"  # If user_input is empty, use default
print(name)  # Output: "Anonymous"

# Chain of Fallbacks
primary_data = None
backup_data = None
default_data = "Default"

data = primary_data or backup_data or default_data
print(data)  # Output: "Default"

# Short-Circuit with Function Calls
def validate_email(email):
    print(f"Validating {email}")
    return "@" in email

def send_email(email):
    print(f"Sending to {email}")
    return True

email = "invalid-email"
# Second function only called if first returns True
if validate_email(email) and send_email(email):
    print("Email sent successfully")
# Output: "Validating invalid-email" only - send_email never called
```

### Rust Implementation

```rust
// Basic Short-Circuit Evaluation
fn expensive_operation() -> bool {
    println!("Expensive operation called!");
    true
}

fn main() {
    // AND short-circuit
    let x = false;
    if x && expensive_operation() {
        println!("Both true");
    }
    // Output: Nothing! expensive_operation() never called
    
    // OR short-circuit
    let y = true;
    if y || expensive_operation() {
        println!("At least one true");
    }
    // Output: "At least one true" - expensive_operation() never called
    
    // Practical: Option Safety
    let maybe_value: Option<i32> = None;
    
    // Safe access - second part only runs if Some
    if maybe_value.is_some() && maybe_value.unwrap() > 10 {
        println!("Value is greater than 10");
    }
    // No panic! unwrap() never called because is_some() is false
    
    // Better Rust idiom using pattern matching
    if let Some(value) = maybe_value {
        if value > 10 {
            println!("Value is greater than 10");
        }
    }
    
    // Division Safety
    let numerator = 100;
    let denominator = 0;
    
    if denominator != 0 && numerator / denominator > 5 {
        println!("Large quotient");
    }
    // Safe! Division never happens
    
    // Using Short-Circuit for Default Values with unwrap_or
    let user_input: Option<String> = None;
    let name = user_input.unwrap_or_else(|| {
        println!("Using default");
        "Anonymous".to_string()
    });
    println!("Name: {}", name);
    
    // Lazy Evaluation with Iterators
    let numbers = vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
    
    // find() uses short-circuit - stops at first match
    let first_even = numbers.iter()
        .find(|&&x| {
            println!("Checking {}", x);
            x % 2 == 0
        });
    // Output: "Checking 1", "Checking 2" - stops immediately!
    
    // any() short-circuits on first true
    let has_large = numbers.iter()
        .any(|&x| {
            println!("Checking {}", x);
            x > 7
        });
    // Checks until it finds a number > 7
    
    // all() short-circuits on first false
    let all_positive = numbers.iter()
        .all(|&x| {
            println!("Checking {}", x);
            x > 0
        });
}

// Function Call Chaining with Short-Circuit
fn validate_user(username: &str) -> bool {
    println!("Validating user: {}", username);
    !username.is_empty()
}

fn check_permissions(username: &str) -> bool {
    println!("Checking permissions for: {}", username);
    username == "admin"
}

fn grant_access(username: &str) -> bool {
    println!("Granting access to: {}", username);
    true
}

fn access_control(username: &str) {
    if validate_user(username) && check_permissions(username) && grant_access(username) {
        println!("Access granted!");
    } else {
        println!("Access denied!");
    }
}

// Example usage:
// access_control(""); // Only validates, stops there
// access_control("user"); // Validates and checks permissions, stops there
// access_control("admin"); // All three functions execute
```

### Go Implementation

```go
package main

import (
    "fmt"
)

func expensiveCheck() bool {
    fmt.Println("Expensive check called!")
    return true
}

func main() {
    // Basic AND Short-Circuit
    x := false
    if x && expensiveCheck() {
        fmt.Println("Both true")
    }
    // Output: Nothing! expensiveCheck() never called
    
    // Basic OR Short-Circuit
    y := true
    if y || expensiveCheck() {
        fmt.Println("At least one true")
    }
    // Output: "At least one true" - expensiveCheck() never called
    
    // Nil Pointer Safety
    type User struct {
        Name string
        Age  int
    }
    
    var user *User = nil
    
    // Safe check - second part never executes if user is nil
    if user != nil && user.Age > 18 {
        fmt.Println("Adult user")
    }
    // No panic! user.Age never accessed
    
    // Division by Zero Protection
    numerator := 100
    denominator := 0
    
    if denominator != 0 && numerator/denominator > 5 {
        fmt.Println("Large quotient")
    }
    // Safe! Division never happens
    
    // Default Value Pattern
    userInput := ""
    name := userInput
    if name == "" {
        name = "Anonymous"
    }
    fmt.Println("Name:", name)
    
    // Or using short-circuit with custom function
    name = getOrDefault(userInput, "Anonymous")
    fmt.Println("Name:", name)
    
    // Function Call Chain
    username := "guest"
    if validateUser(username) && checkPermissions(username) && grantAccess(username) {
        fmt.Println("Full access granted")
    } else {
        fmt.Println("Access restricted")
    }
    
    // Slice/Array Bounds Checking
    numbers := []int{1, 2, 3, 4, 5}
    index := 10
    
    // Safe access - second part only runs if index is valid
    if index >= 0 && index < len(numbers) && numbers[index] > 3 {
        fmt.Println("Number is greater than 3")
    }
    // No panic! numbers[index] never accessed with invalid index
    
    // Early Return Pattern (implicit short-circuit)
    result := processWithValidation("test@example.com")
    fmt.Println("Result:", result)
}

func getOrDefault(value, defaultValue string) string {
    if value != "" {
        return value
    }
    return defaultValue
}

func validateUser(username string) bool {
    fmt.Println("Validating user:", username)
    return username != ""
}

func checkPermissions(username string) bool {
    fmt.Println("Checking permissions for:", username)
    return username == "admin"
}

func grantAccess(username string) bool {
    fmt.Println("Granting access to:", username)
    return true
}

// Early Return Pattern (Alternative to Short-Circuit)
func processWithValidation(email string) string {
    if email == "" {
        return "Error: empty email"
    }
    
    if !contains(email, "@") {
        return "Error: invalid email"
    }
    
    if !sendEmail(email) {
        return "Error: failed to send"
    }
    
    return "Success"
}

func contains(s, substr string) bool {
    fmt.Println("Checking if", s, "contains", substr)
    return true // Simplified
}

func sendEmail(email string) bool {
    fmt.Println("Sending email to:", email)
    return true
}

// Lazy Evaluation Pattern for Expensive Operations
type LazyValue struct {
    computed bool
    value    int
    compute  func() int
}

func (l *LazyValue) Get() int {
    if !l.computed {
        fmt.Println("Computing value...")
        l.value = l.compute()
        l.computed = true
    }
    return l.value
}

func exampleLazyValue() {
    lazy := &LazyValue{
        compute: func() int {
            fmt.Println("Expensive computation!")
            return 42
        },
    }
    
    // Value not computed until needed
    if false && lazy.Get() > 10 {
        fmt.Println("This won't print")
    }
    // Output: Nothing! Get() never called
    
    if true || lazy.Get() > 10 {
        fmt.Println("This will print")
    }
    // Output: "This will print" - Get() never called
}
```

## Common Patterns and Use Cases

### 1. Null/Nil Safety Pattern
```
// Pattern: Check existence before access
if object != null AND object.property > value:
    use(object.property)
```

### 2. Default Value Pattern
```
result = primary_value OR backup_value OR default_value
```

### 3. Validation Chain Pattern
```
if validate() AND authorize() AND execute():
    success()
```

### 4. Bounds Checking Pattern
```
if index >= 0 AND index < length AND array[index] == target:
    found()
```

### 5. Resource Cleanup Pattern
```
if resource_exists() AND resource.is_open() AND resource.read():
    process()
```

## Advanced Concepts

### Non-Short-Circuit Operators

Some languages have **non-short-circuit** (eager) operators that always evaluate both operands:

- **Python**: `&` and `|` for bitwise operations (always evaluate both sides)
- **Rust**: `&` and `|` for bitwise operations
- **Go**: `&` and `|` for bitwise operations

```python
# Python: Short-circuit vs Non-short-circuit
x = False
y = True

# Short-circuit: second function not called
result = x and expensive_function()

# Bitwise (always evaluates both - DON'T use for logic!)
# result = x & expensive_function()  # This would call the function
```

### Side Effects and Order of Evaluation

Short-circuit evaluation affects **when** side effects occur:

```python
counter = 0

def increment_and_return_false():
    global counter
    counter += 1
    return False

def increment_and_return_true():
    global counter
    counter += 1
    return True

# Only first function executes
if increment_and_return_false() and increment_and_return_true():
    pass
print(counter)  # Output: 1 (not 2!)

# Both functions execute
if increment_and_return_true() or increment_and_return_false():
    pass
print(counter)  # Output: 2 (first function was enough, but we already called it)
```

### Ternary Operators and Conditional Expressions

These also use lazy evaluation:

**Python:**
```python
value = expensive_computation() if condition else default_value
# expensive_computation() only called if condition is True
```

**Rust:**
```rust
let value = if condition {
    expensive_computation()
} else {
    default_value
};
```

**Go:**
```go
var value int
if condition {
    value = expensiveComputation()
} else {
    value = defaultValue
}
```

## Performance Implications

### When Short-Circuit Helps

1. **Expensive Computations**: Place cheap checks first
```python
if cheap_check() and expensive_database_query():
    process()
```

2. **Avoiding Errors**: Prevent crashes with guard clauses
```python
if data is not None and len(data) > 0 and data[0].is_valid():
    use(data[0])
```

3. **Network Calls**: Skip unnecessary API calls
```python
if cache.has(key) or fetch_from_api(key):
    process()
```

### Order Matters!

Always put the **most likely to fail** or **cheapest to evaluate** conditions first:

❌ **Bad:**
```python
if user.has_permission() and user is not None:  # Crashes if user is None!
    grant_access()
```

✅ **Good:**
```python
if user is not None and user.has_permission():  # Safe and efficient
    grant_access()
```

## Common Pitfalls

### 1. Assuming Both Sides Execute
```python
# Wrong assumption: both increments happen
x = 0
if (x := x + 1) > 5 or (x := x + 1) > 0:
    print(x)  # Might print 1, not 2!
```

### 2. Relying on Side Effects
```python
# Dangerous: side effect might not occur
if condition or update_database():  # Database might not update!
    pass
```

### 3. Using Bitwise Operators for Logic
```python
# Wrong: Always evaluates both (and does bitwise operation)
if x > 0 & y > 0:  # Should be 'and'
    process()
```

## Best Practices

1. **Order Conditions by Likelihood**: Put conditions most likely to be false first in AND chains
2. **Order by Cost**: Put cheaper operations before expensive ones
3. **Null Checks First**: Always check for null/None/nil before accessing properties
4. **Avoid Side Effects**: Don't rely on side effects in short-circuit expressions
5. **Be Explicit**: Use parentheses for complex conditions to make intent clear
6. **Document Unusual Cases**: Comment when order matters for correctness

## Summary

Short-circuit evaluation is a fundamental programming concept that:
- **Stops evaluation early** when the result is already determined
- **Improves performance** by avoiding unnecessary computations
- **Prevents errors** through guard conditions
- **Enables cleaner code** with chained fallbacks

The key is understanding **when** and **why** evaluation stops, and using that knowledge to write safer, faster, and more elegant code.

# Complete Guide to Conditional Expressions

## 1. If-Else Statements (Basic Conditionals)

The fundamental building block of conditional logic.

### Python
```python
# Basic if
if temperature > 30:
    print("It's hot!")

# If-else
if temperature > 30:
    print("It's hot!")
else:
    print("It's not hot")

# If-elif-else (multiple conditions)
if temperature > 30:
    print("Hot")
elif temperature > 20:
    print("Warm")
elif temperature > 10:
    print("Cool")
else:
    print("Cold")

# Nested if
if is_weekend:
    if weather == "sunny":
        print("Go to the beach!")
    else:
        print("Stay home and relax")
```

### Rust
```rust
let temperature = 25;

// Basic if
if temperature > 30 {
    println!("It's hot!");
}

// If-else
if temperature > 30 {
    println!("It's hot!");
} else {
    println!("It's not hot");
}

// If-else if-else
if temperature > 30 {
    println!("Hot");
} else if temperature > 20 {
    println!("Warm");
} else if temperature > 10 {
    println!("Cool");
} else {
    println!("Cold");
}

// If as expression (returns a value!)
let status = if temperature > 30 {
    "hot"
} else {
    "comfortable"
};
```

### Go
```go
temperature := 25

// Basic if
if temperature > 30 {
    fmt.Println("It's hot!")
}

// If-else
if temperature > 30 {
    fmt.Println("It's hot!")
} else {
    fmt.Println("It's not hot")
}

// If with initialization statement
if temp := getTemperature(); temp > 30 {
    fmt.Println("Hot:", temp)
} else {
    fmt.Println("Comfortable:", temp)
}
// Note: temp is scoped to the if block

// Multiple else if
if temperature > 30 {
    fmt.Println("Hot")
} else if temperature > 20 {
    fmt.Println("Warm")
} else if temperature > 10 {
    fmt.Println("Cool")
} else {
    fmt.Println("Cold")
}
```

---

## 2. Ternary Operator / Conditional Expression

A compact way to write simple if-else in a single line.

### Python
```python
# Python uses: value_if_true if condition else value_if_false
age = 20
status = "adult" if age >= 18 else "minor"
print(status)  # "adult"

# Nested ternary (use sparingly!)
score = 85
grade = "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 70 else "F"

# With function calls
result = expensive_operation() if should_compute else cached_value

# Common patterns
max_value = a if a > b else b  # Get maximum
absolute = x if x >= 0 else -x  # Absolute value
greeting = f"Hello, {name}" if name else "Hello, Guest"  # Default value
```

### Rust
```rust
// Rust uses if-else as an expression
let age = 20;
let status = if age >= 18 { "adult" } else { "minor" };
println!("{}", status);  // "adult"

// More complex
let score = 85;
let grade = if score >= 90 {
    "A"
} else if score >= 80 {
    "B"
} else if score >= 70 {
    "C"
} else {
    "F"
};

// In function returns
fn get_max(a: i32, b: i32) -> i32 {
    if a > b { a } else { b }
}

// With blocks
let result = if complex_condition {
    let temp = expensive_computation();
    temp * 2
} else {
    default_value
};
```

### Go
```go
// Go doesn't have a ternary operator!
// Must use full if-else

age := 20
var status string
if age >= 18 {
    status = "adult"
} else {
    status = "minor"
}

// Common workaround: helper functions
func ternary(condition bool, trueVal, falseVal interface{}) interface{} {
    if condition {
        return trueVal
    }
    return falseVal
}

// Using generics (Go 1.18+)
func Ternary[T any](condition bool, trueVal, falseVal T) T {
    if condition {
        return trueVal
    }
    return falseVal
}

status = Ternary(age >= 18, "adult", "minor")
```

---

## 3. Switch/Match Statements

Multi-way branching based on value comparison.

### Python
```python
# Python 3.10+ has match-case (structural pattern matching)
status_code = 404

match status_code:
    case 200:
        print("OK")
    case 404:
        print("Not Found")
    case 500:
        print("Server Error")
    case _:  # Default case
        print("Unknown status")

# Pattern matching with structures
point = (0, 5)
match point:
    case (0, 0):
        print("Origin")
    case (0, y):
        print(f"On Y axis at {y}")
    case (x, 0):
        print(f"On X axis at {x}")
    case (x, y):
        print(f"Point at ({x}, {y})")

# Matching with conditions (guards)
match number:
    case x if x < 0:
        print("Negative")
    case 0:
        print("Zero")
    case x if x > 0:
        print("Positive")

# Before Python 3.10, use dictionary dispatch
def handle_200():
    return "OK"

def handle_404():
    return "Not Found"

def handle_default():
    return "Unknown"

handlers = {
    200: handle_200,
    404: handle_404,
}

result = handlers.get(status_code, handle_default)()
```

### Rust
```rust
let status_code = 404;

// Basic match (exhaustive - must cover all cases!)
match status_code {
    200 => println!("OK"),
    404 => println!("Not Found"),
    500 => println!("Server Error"),
    _ => println!("Unknown status"),  // Catch-all
}

// Match as expression
let message = match status_code {
    200 => "OK",
    404 => "Not Found",
    500 => "Server Error",
    _ => "Unknown",
};

// Multiple patterns
match number {
    1 | 2 | 3 => println!("One, two, or three"),
    4..=10 => println!("Four through ten"),  // Range
    _ => println!("Something else"),
}

// Matching with destructuring
struct Point { x: i32, y: i32 }
let point = Point { x: 0, y: 5 };

match point {
    Point { x: 0, y: 0 } => println!("Origin"),
    Point { x: 0, y } => println!("On Y axis at {}", y),
    Point { x, y: 0 } => println!("On X axis at {}", x),
    Point { x, y } => println!("Point at ({}, {})", x, y),
}

// Match with guards
match number {
    n if n < 0 => println!("Negative: {}", n),
    0 => println!("Zero"),
    n if n > 0 => println!("Positive: {}", n),
    _ => unreachable!(),
}

// Matching Option and Result
let maybe_value: Option<i32> = Some(5);
match maybe_value {
    Some(x) if x > 10 => println!("Large: {}", x),
    Some(x) => println!("Small: {}", x),
    None => println!("No value"),
}

// Match with binding
enum Message {
    Quit,
    Move { x: i32, y: i32 },
    Write(String),
}

let msg = Message::Write("Hello".to_string());
match msg {
    Message::Quit => println!("Quit"),
    Message::Move { x, y } => println!("Move to ({}, {})", x, y),
    Message::Write(text) => println!("Text: {}", text),
}
```

### Go
```go
statusCode := 404

// Basic switch
switch statusCode {
case 200:
    fmt.Println("OK")
case 404:
    fmt.Println("Not Found")
case 500:
    fmt.Println("Server Error")
default:
    fmt.Println("Unknown status")
}

// Multiple values per case
switch statusCode {
case 200, 201, 204:
    fmt.Println("Success")
case 400, 404:
    fmt.Println("Client Error")
case 500, 502, 503:
    fmt.Println("Server Error")
default:
    fmt.Println("Unknown")
}

// Switch with conditions (no expression after switch)
number := 15
switch {
case number < 0:
    fmt.Println("Negative")
case number == 0:
    fmt.Println("Zero")
case number > 0:
    fmt.Println("Positive")
}

// Switch with initialization
switch result := compute(); result {
case 0:
    fmt.Println("Zero")
default:
    fmt.Println("Non-zero:", result)
}

// Type switch (for interfaces)
var i interface{} = "hello"
switch v := i.(type) {
case int:
    fmt.Printf("Integer: %d\n", v)
case string:
    fmt.Printf("String: %s\n", v)
case bool:
    fmt.Printf("Boolean: %t\n", v)
default:
    fmt.Printf("Unknown type: %T\n", v)
}

// Fallthrough (explicit fall-through to next case)
switch num := 2; num {
case 1:
    fmt.Println("One")
    fallthrough
case 2:
    fmt.Println("Two")
    fallthrough  // Will also execute case 3
case 3:
    fmt.Println("Three")
default:
    fmt.Println("Other")
}
// Output: "Two" then "Three"
```

---

## 4. Guard Clauses / Early Returns

Exit early from functions when conditions aren't met.

### Python
```python
def process_user(user):
    # Guard clauses at the top
    if user is None:
        return "Error: No user provided"
    
    if not user.get("email"):
        return "Error: Missing email"
    
    if not user.get("age") or user["age"] < 18:
        return "Error: User must be 18 or older"
    
    # Main logic here (no deep nesting!)
    print(f"Processing {user['email']}")
    return "Success"

# Alternative with exceptions
def validate_user(user):
    if user is None:
        raise ValueError("No user provided")
    
    if not user.get("email"):
        raise ValueError("Missing email")
    
    # Continue with valid user...
```

### Rust
```rust
fn process_user(user: Option<&User>) -> Result<String, String> {
    // Guard clauses
    let user = match user {
        Some(u) => u,
        None => return Err("No user provided".to_string()),
    };
    
    if user.email.is_empty() {
        return Err("Missing email".to_string());
    }
    
    if user.age < 18 {
        return Err("User must be 18 or older".to_string());
    }
    
    // Main logic
    println!("Processing {}", user.email);
    Ok("Success".to_string())
}

// Using early return with ? operator
fn process_user_result(user: Option<&User>) -> Result<(), &'static str> {
    let user = user.ok_or("No user provided")?;
    
    if user.email.is_empty() {
        return Err("Missing email");
    }
    
    if user.age < 18 {
        return Err("User must be 18 or older");
    }
    
    println!("Processing {}", user.email);
    Ok(())
}
```

### Go
```go
func processUser(user *User) error {
    // Guard clauses
    if user == nil {
        return errors.New("no user provided")
    }
    
    if user.Email == "" {
        return errors.New("missing email")
    }
    
    if user.Age < 18 {
        return errors.New("user must be 18 or older")
    }
    
    // Main logic
    fmt.Printf("Processing %s\n", user.Email)
    return nil
}

// Multiple return values
func validateAndProcess(user *User) (string, error) {
    if user == nil {
        return "", errors.New("no user provided")
    }
    
    if user.Email == "" {
        return "", errors.New("missing email")
    }
    
    result := fmt.Sprintf("Processed: %s", user.Email)
    return result, nil
}
```

---

## 5. Option/Maybe Monad Pattern

Handling optional values without null checks.

### Python
```python
from typing import Optional

# Using None
def find_user(user_id: int) -> Optional[dict]:
    users = {1: {"name": "Alice"}, 2: {"name": "Bob"}}
    return users.get(user_id)  # Returns None if not found

# Safe access with get and chaining
user = find_user(1)
name = user.get("name") if user else "Unknown"

# Using walrus operator with guard
if (user := find_user(3)) and user.get("active"):
    print(f"Active user: {user['name']}")

# Optional chaining (Python 3.9+ dict method)
class User:
    def __init__(self, name, address=None):
        self.name = name
        self.address = address

user = User("Alice")
# Safe navigation
city = user.address.city if user.address else None
```

### Rust
```rust
// Option<T> is built into Rust
fn find_user(user_id: i32) -> Option<User> {
    // Returns Some(user) or None
    if user_id == 1 {
        Some(User { name: "Alice".to_string() })
    } else {
        None
    }
}

// Pattern matching
match find_user(1) {
    Some(user) => println!("Found: {}", user.name),
    None => println!("User not found"),
}

// if let (convenience syntax)
if let Some(user) = find_user(1) {
    println!("Found: {}", user.name);
}

// Chaining with map
let user_name = find_user(1)
    .map(|u| u.name)
    .unwrap_or_else(|| "Unknown".to_string());

// Chaining with and_then (flatMap)
fn get_user_email(user_id: i32) -> Option<String> {
    find_user(user_id)
        .and_then(|user| user.email)
}

// Using ? operator for early return
fn process_user(user_id: i32) -> Option<String> {
    let user = find_user(user_id)?;  // Returns None if None
    let email = user.email?;          // Returns None if None
    Some(format!("Email: {}", email))
}

// Combining Options
let result = find_user(1)
    .filter(|u| u.age >= 18)
    .map(|u| u.name)
    .unwrap_or("No adult user found".to_string());
```

### Go
```go
// Go doesn't have built-in Option, but we can simulate it

// Using pointers (nil = None)
func findUser(userID int) *User {
    if userID == 1 {
        return &User{Name: "Alice"}
    }
    return nil
}

// Safe access
user := findUser(1)
if user != nil {
    fmt.Println("Found:", user.Name)
} else {
    fmt.Println("User not found")
}

// Multiple return values pattern (idiomatic Go)
func findUserWithError(userID int) (*User, error) {
    if userID == 1 {
        return &User{Name: "Alice"}, nil
    }
    return nil, errors.New("user not found")
}

// Usage
if user, err := findUserWithError(1); err == nil {
    fmt.Println("Found:", user.Name)
} else {
    fmt.Println("Error:", err)
}

// Custom Option type
type Option[T any] struct {
    value *T
}

func Some[T any](val T) Option[T] {
    return Option[T]{value: &val}
}

func None[T any]() Option[T] {
    return Option[T]{value: nil}
}

func (o Option[T]) IsSome() bool {
    return o.value != nil
}

func (o Option[T]) Unwrap() T {
    if o.value == nil {
        panic("unwrap on None")
    }
    return *o.value
}

func (o Option[T]) UnwrapOr(defaultVal T) T {
    if o.value == nil {
        return defaultVal
    }
    return *o.value
}
```

---

## 6. Result/Either Pattern

Handling operations that can succeed or fail.

### Python
```python
from typing import Union, Generic, TypeVar
from dataclasses import dataclass

T = TypeVar('T')
E = TypeVar('E')

@dataclass
class Ok(Generic[T]):
    value: T

@dataclass
class Err(Generic[E]):
    error: E

Result = Union[Ok[T], Err[E]]

def divide(a: int, b: int) -> Result[float, str]:
    if b == 0:
        return Err("Division by zero")
    return Ok(a / b)

# Pattern matching (Python 3.10+)
result = divide(10, 2)
match result:
    case Ok(value):
        print(f"Result: {value}")
    case Err(error):
        print(f"Error: {error}")

# Traditional approach
if isinstance(result, Ok):
    print(f"Result: {result.value}")
else:
    print(f"Error: {result.error}")

# Exception-based (traditional Python)
def divide_with_exception(a: int, b: int) -> float:
    if b == 0:
        raise ValueError("Division by zero")
    return a / b

try:
    result = divide_with_exception(10, 0)
    print(f"Result: {result}")
except ValueError as e:
    print(f"Error: {e}")
```

### Rust
```rust
// Result<T, E> is built into Rust
fn divide(a: i32, b: i32) -> Result<f64, String> {
    if b == 0 {
        Err("Division by zero".to_string())
    } else {
        Ok(a as f64 / b as f64)
    }
}

// Pattern matching
match divide(10, 2) {
    Ok(result) => println!("Result: {}", result),
    Err(error) => println!("Error: {}", error),
}

// if let for Ok case only
if let Ok(result) = divide(10, 2) {
    println!("Result: {}", result);
}

// Using ? operator for error propagation
fn calculate() -> Result<f64, String> {
    let result1 = divide(10, 2)?;  // Returns Err if divide fails
    let result2 = divide(result1 as i32, 2)?;
    Ok(result2)
}

// Chaining with map and and_then
let result = divide(10, 2)
    .map(|x| x * 2.0)
    .and_then(|x| divide(x as i32, 2))
    .unwrap_or(0.0);

// Converting between Option and Result
let opt: Option<i32> = Some(5);
let res: Result<i32, &str> = opt.ok_or("No value");

// Multiple error types with custom enum
#[derive(Debug)]
enum MathError {
    DivisionByZero,
    NegativeSquareRoot,
}

fn safe_sqrt(x: f64) -> Result<f64, MathError> {
    if x < 0.0 {
        Err(MathError::NegativeSquareRoot)
    } else {
        Ok(x.sqrt())
    }
}
```

### Go
```go
// Idiomatic Go: multiple return values
func divide(a, b int) (float64, error) {
    if b == 0 {
        return 0, errors.New("division by zero")
    }
    return float64(a) / float64(b), nil
}

// Usage
result, err := divide(10, 2)
if err != nil {
    fmt.Println("Error:", err)
} else {
    fmt.Println("Result:", result)
}

// Error propagation
func calculate() (float64, error) {
    result1, err := divide(10, 2)
    if err != nil {
        return 0, err  // Early return on error
    }
    
    result2, err := divide(int(result1), 2)
    if err != nil {
        return 0, err
    }
    
    return result2, nil
}

// Custom error types
type MathError struct {
    Op  string
    Err string
}

func (e *MathError) Error() string {
    return fmt.Sprintf("%s: %s", e.Op, e.Err)
}

func safeDivide(a, b int) (float64, error) {
    if b == 0 {
        return 0, &MathError{
            Op:  "divide",
            Err: "division by zero",
        }
    }
    return float64(a) / float64(b), nil
}

// Type assertion for specific errors
result, err := safeDivide(10, 0)
if err != nil {
    if mathErr, ok := err.(*MathError); ok {
        fmt.Printf("Math error in %s: %s\n", mathErr.Op, mathErr.Err)
    } else {
        fmt.Println("Unknown error:", err)
    }
}

// Using errors.Is and errors.As (Go 1.13+)
var ErrDivisionByZero = errors.New("division by zero")

func divide2(a, b int) (float64, error) {
    if b == 0 {
        return 0, fmt.Errorf("divide %d by %d: %w", a, b, ErrDivisionByZero)
    }
    return float64(a) / float64(b), nil
}

result, err = divide2(10, 0)
if errors.Is(err, ErrDivisionByZero) {
    fmt.Println("Caught division by zero!")
}
```

---

## 7. Assert Statements

Runtime checks that throw errors if conditions aren't met.

### Python
```python
# Basic assert
age = 15
assert age >= 18, "Must be 18 or older"
# Raises: AssertionError: Must be 18 or older

# Assert for debugging
def calculate_average(numbers):
    assert len(numbers) > 0, "List cannot be empty"
    assert all(isinstance(n, (int, float)) for n in numbers), "All items must be numbers"
    return sum(numbers) / len(numbers)

# Assert in testing
def test_addition():
    result = add(2, 3)
    assert result == 5, f"Expected 5, got {result}"

# Multiple conditions
x = 10
assert x > 0 and x < 100, "x must be between 0 and 100"

# Note: assertions can be disabled with python -O
# So never use assert for data validation in production!
```

### Rust
```rust
// Compile-time assertions
fn process_data(data: &[i32]) {
    assert!(data.len() > 0, "Data cannot be empty");
    assert!(data.len() < 1000, "Data too large");
    
    // Process data...
}

// assert_eq! for equality
let result = add(2, 3);
assert_eq!(result, 5, "Addition failed: {} != 5", result);

// assert_ne! for inequality
assert_ne!(result, 0, "Result should not be zero");

// debug_assert! (removed in release builds)
debug_assert!(expensive_check(), "This only runs in debug mode");

// Panic with custom message
if data.is_empty() {
    panic!("Data cannot be empty!");
}

// unreachable! for code that should never execute
match value {
    Some(x) => process(x),
    None => unreachable!("Value should always be Some here"),
}
```

### Go
```go
// Go doesn't have built-in assert
// But you can create one

func assert(condition bool, message string) {
    if !condition {
        panic(message)
    }
}

func calculateAverage(numbers []int) float64 {
    assert(len(numbers) > 0, "List cannot be empty")
    
    sum := 0
    for _, n := range numbers {
        sum += n
    }
    return float64(sum) / float64(len(numbers))
}

// For testing, use testing package
import "testing"

func TestAddition(t *testing.T) {
    result := add(2, 3)
    if result != 5 {
        t.Errorf("Expected 5, got %d", result)
    }
}

// Or with testify library
import "github.com/stretchr/testify/assert"

func TestAddition(t *testing.T) {
    result := add(2, 3)
    assert.Equal(t, 5, result, "Addition should return 5")
}
```

---

## 8. Null Coalescing / Elvis Operator

Provide default values for null/nil/None.

### Python
```python
# Using 'or' operator (falsy coalescing)
name = user_input or "Anonymous"
count = get_count() or 0

# Problem: 0, "", [], False are all falsy
value = 0
result = value or 10  # Result is 10, not 0!

# Better: explicit None check
value = None
result = value if value is not None else 10

# Python 3.8+ walrus with or
if (result := expensive_call()) or default_value:
    use(result)

# Dictionary get with default
config = {"debug": False}
debug_mode = config.get("debug", True)  # Returns False, not True

# Chained fallbacks
data = primary_source or backup_source or default_source

# For numeric values where 0 is valid
def get_or_default(value, default):
    return value if value is not None else default

count = get_or_default(0, 10)  # Returns 0, not 10
```

### Rust
```rust
// Using unwrap_or
let value: Option<i32> = None;
let result = value.unwrap_or(10);  // Returns 10

// Using unwrap_or_else (lazy evaluation)
let result = value.unwrap_or_else(|| {
    println!("Computing default");
    expensive_default()
});

// Using unwrap_or_default
let result = value.unwrap_or_default();  // Uses Default trait

// Chaining with or
let primary: Option<i32> = None;
let backup: Option<i32> = Some(5);
let result = primary.or(backup).unwrap_or(0);

// For Result type
let result: Result<i32, String> = Err("error".to_string());
let value = result.unwrap_or(10);

// or_else for Result
let value = result.or_else(|_| Ok(10)).unwrap();

// Pattern matching alternative
let value = match optional {
    Some(v) => v,
    None => 10,
};
```

### Go
```go
// Using simple if
var name string
if userInput != "" {
    name = userInput
} else {
    name = "Anonymous"
}

// Helper function
func coalesce(value, defaultValue string) string {
    if value != "" {
        return value
    }
    return defaultValue
}

name = coalesce(userInput, "Anonymous")

// For pointers
func coalescePtr(value *int, defaultValue int) int {
    if value != nil {
        return *value
    }
    return defaultValue
}

// Generic version (Go 1.18+)
func Coalesce[T comparable](value *T, defaultValue T) T {
    if value != nil {
        return *value
    }
    return defaultValue
}

// Multiple fallbacks
func firstNonEmpty(values ...string) string {
    for _, v := range values {
        if v != "" {
            return v
        }
    }
    return ""
}

name = firstNonEmpty(primary, backup, "default")
```

---

## 9. Conditional Loops

Loops that execute based on conditions.

### Python
```python
# While loop
count = 0
while count < 5:
    print(count)
    count += 1

# While with else (executes if loop completes normally)
while count < 10:
    if should_break():
        break
    count += 1
else:
    print("Loop completed normally")

# Infinite loop with break
while True:
    user_input = input("Enter 'quit' to exit: ")
    if user_input == 'quit':
        break
    process(user_input)

# While with multiple conditions
while not done and count < max_attempts and time_remaining > 0:
    perform_operation()

# Do-while simulation
while True:
    execute_once()
    if not condition:
        break
```

### Rust
```rust
// While loop
let mut count = 0;
while count < 5 {
    println!("{}", count);
    count += 1;
}

// Loop with break (infinite loop)
let mut count = 0;
loop {
    if count >= 5 {
        break;
    }
    println!("{}", count);
    count += 1;
}

// Loop that returns a value
let result = loop {
    count += 1;
    if count == 10 {
        break count * 2;  // Returns 20
    }
};

// While let (loop until pattern doesn't match)
let mut stack = vec![1, 2, 3];
while let Some(top) = stack.pop() {
    println!("Popped: {}", top);
}

// Labeled loops for nested break/continue
'outer: loop {
    'inner: loop {
        if condition {
            break 'outer;  // Breaks out of outer loop
        }
        break 'inner;
    }
}
```

### Go
```go
// For as while
count := 0
for count < 5 {
    fmt.Println(count)
    count++
}

// Infinite loop
for {
    userInput := getUserInput()
    if userInput == "quit" {
        break
    }
    process(userInput)
}

// For with condition and increment
for i := 0; i < 10; i++ {
    fmt.Println(i)
}

// Multiple variables
for i, j := 0, 10; i < j; i, j = i+1, j-1 {
    fmt.Printf("%d %d\n", i, j)
}

// Range loop (for arrays, slices, maps)
numbers := []int{1, 2, 3, 4, 5}
for index, value := range numbers {
    fmt.Printf("%d: %d\n", index, value)
}

// Nested loops with labels
outer:
for i := 0; i < 5; i++ {
    for j := 0; j < 5; j++ {
        if someCondition(i, j) {
            break outer  // Breaks out of outer loop
        }
    }
}
```

