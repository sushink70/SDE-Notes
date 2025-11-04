# Comprehensive Functions Guide: Go, Rust, and Python

## Table of Contents
1. [Basic Function Syntax](#basic-syntax)
2. [Functions Returning Nothing](#returning-nothing)
3. [Boolean Returns](#boolean-returns)
4. [Integer Status Codes](#integer-status-codes)
5. [Error Handling Patterns](#error-handling)
6. [Multiple Return Values](#multiple-returns)
7. [Optional/Nullable Returns](#optional-returns)
8. [Best Practices by Use Case](#best-practices)

---

## 1. Basic Function Syntax {#basic-syntax}

### Python
```python
def function_name(param1: int, param2: str) -> return_type:
    """Docstring explaining the function"""
    return result
```

### Go
```go
func functionName(param1 int, param2 string) returnType {
    // Function body
    return result
}
```

### Rust
```rust
fn function_name(param1: i32, param2: &str) -> ReturnType {
    // Function body
    result  // or return result;
}
```

---

## 2. Functions Returning Nothing {#returning-nothing}

### When to Use
- Performing side effects (printing, logging, file I/O)
- Modifying state (updating databases, changing global state)
- Event handlers
- Initialization/setup functions

### Python - No Return (implicit None)
```python
def print_greeting(name: str) -> None:
    """Prints a greeting message"""
    print(f"Hello, {name}!")

def update_counter(counter: list) -> None:
    """Mutates the counter list"""
    counter[0] += 1

# Usage
print_greeting("Alice")  # Prints: Hello, Alice!
result = print_greeting("Bob")  # result is None
```

### Go - No Return (void)
```go
func printGreeting(name string) {
    fmt.Printf("Hello, %s!\n", name)
}

func updateCounter(counter *int) {
    *counter++
}

// Usage
printGreeting("Alice")
count := 0
updateCounter(&count)
```

### Rust - No Return (unit type)
```rust
fn print_greeting(name: &str) {
    println!("Hello, {}!", name);
}

fn update_counter(counter: &mut i32) {
    *counter += 1;
}

// Usage
print_greeting("Alice");
let mut count = 0;
update_counter(&mut count);
```

**Note**: Rust functions without explicit return type return `()` (unit type), which is similar to void.

---

## 3. Boolean Returns {#boolean-returns}

### When to Use
- Validation functions (is_valid, can_execute)
- Predicate functions (is_empty, has_permission)
- Success/failure indicators (simple operations)
- Search operations (exists, contains)

### Python
```python
def is_even(n: int) -> bool:
    """Check if number is even"""
    return n % 2 == 0

def is_valid_email(email: str) -> bool:
    """Validate email format"""
    return '@' in email and '.' in email

def has_permission(user: str, resource: str) -> bool:
    """Check if user has access to resource"""
    permissions = {"admin": ["users", "settings"], "user": ["profile"]}
    return resource in permissions.get(user, [])

# Usage
if is_even(4):
    print("Number is even")

if is_valid_email("user@example.com"):
    print("Valid email")
```

### Go
```go
func isEven(n int) bool {
    return n%2 == 0
}

func isValidEmail(email string) bool {
    return strings.Contains(email, "@") && strings.Contains(email, ".")
}

func hasPermission(user, resource string) bool {
    permissions := map[string][]string{
        "admin": {"users", "settings"},
        "user":  {"profile"},
    }
    for _, perm := range permissions[user] {
        if perm == resource {
            return true
        }
    }
    return false
}

// Usage
if isEven(4) {
    fmt.Println("Number is even")
}
```

### Rust
```rust
fn is_even(n: i32) -> bool {
    n % 2 == 0
}

fn is_valid_email(email: &str) -> bool {
    email.contains('@') && email.contains('.')
}

fn has_permission(user: &str, resource: &str) -> bool {
    let permissions = std::collections::HashMap::from([
        ("admin", vec!["users", "settings"]),
        ("user", vec!["profile"]),
    ]);
    
    permissions.get(user)
        .map(|perms| perms.contains(&resource))
        .unwrap_or(false)
}

// Usage
if is_even(4) {
    println!("Number is even");
}
```

---

## 4. Integer Status Codes {#integer-status-codes}

### When to Use
- C-style APIs and system programming
- Exit codes for programs
- Legacy code compatibility
- Performance-critical code (avoiding allocations)

### Common Conventions
- `0`: Success
- `-1`: General error
- `1+`: Specific error codes
- Position/index returns: `-1` for "not found"

### Python
```python
def find_index(items: list, target) -> int:
    """Return index of target, or -1 if not found"""
    try:
        return items.index(target)
    except ValueError:
        return -1

def safe_divide(a: int, b: int) -> int:
    """Return 0 for success, -1 for error"""
    if b == 0:
        return -1
    result = a / b
    return 0

def execute_command(cmd: str) -> int:
    """Return exit code (0 for success)"""
    import os
    return os.system(cmd)

# Usage
index = find_index([1, 2, 3], 2)
if index != -1:
    print(f"Found at index {index}")

status = safe_divide(10, 2)
if status == 0:
    print("Division successful")
```

### Go
```go
func findIndex(items []int, target int) int {
    for i, item := range items {
        if item == target {
            return i
        }
    }
    return -1
}

func safeDivide(a, b int, result *float64) int {
    if b == 0 {
        return -1  // Error code
    }
    *result = float64(a) / float64(b)
    return 0  // Success
}

func executeCommand(cmd string) int {
    // Returns exit code
    // 0 = success, non-zero = error
    return 0
}

// Usage
index := findIndex([]int{1, 2, 3}, 2)
if index != -1 {
    fmt.Printf("Found at index %d\n", index)
}

var result float64
if safeDivide(10, 2, &result) == 0 {
    fmt.Printf("Result: %.2f\n", result)
}
```

### Rust
```rust
fn find_index(items: &[i32], target: i32) -> i32 {
    for (i, &item) in items.iter().enumerate() {
        if item == target {
            return i as i32;
        }
    }
    -1
}

fn safe_divide(a: i32, b: i32) -> (i32, f64) {
    if b == 0 {
        return (-1, 0.0);  // Error code with default value
    }
    (0, a as f64 / b as f64)  // Success code with result
}

// Usage
let items = [1, 2, 3];
let index = find_index(&items, 2);
if index != -1 {
    println!("Found at index {}", index);
}

let (status, result) = safe_divide(10, 2);
if status == 0 {
    println!("Result: {:.2}", result);
}
```

**Note**: In Rust, using `Option<T>` or `Result<T, E>` is more idiomatic than integer codes.

---

## 5. Error Handling Patterns {#error-handling}

### Python - Exceptions
```python
def divide(a: float, b: float) -> float:
    """Raise exception on error"""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

def read_file(path: str) -> str:
    """May raise IOError"""
    with open(path, 'r') as f:
        return f.read()

# Usage with try-except
try:
    result = divide(10, 0)
except ValueError as e:
    print(f"Error: {e}")
```

### Go - Error Returns
```go
func divide(a, b float64) (float64, error) {
    if b == 0 {
        return 0, errors.New("cannot divide by zero")
    }
    return a / b, nil
}

func readFile(path string) (string, error) {
    data, err := os.ReadFile(path)
    if err != nil {
        return "", err
    }
    return string(data), nil
}

// Usage
result, err := divide(10, 2)
if err != nil {
    log.Printf("Error: %v", err)
    return
}
fmt.Printf("Result: %.2f\n", result)
```

### Rust - Result Type
```rust
fn divide(a: f64, b: f64) -> Result<f64, String> {
    if b == 0.0 {
        return Err("Cannot divide by zero".to_string());
    }
    Ok(a / b)
}

fn read_file(path: &str) -> Result<String, std::io::Error> {
    std::fs::read_to_string(path)
}

// Usage
match divide(10.0, 2.0) {
    Ok(result) => println!("Result: {:.2}", result),
    Err(e) => println!("Error: {}", e),
}

// Or with ? operator
fn process() -> Result<(), String> {
    let result = divide(10.0, 2.0)?;
    println!("Result: {:.2}", result);
    Ok(())
}
```

---

## 6. Multiple Return Values {#multiple-returns}

### Python - Tuples
```python
def get_user_info(user_id: int) -> tuple[str, int, bool]:
    """Return (name, age, is_active)"""
    return ("Alice", 30, True)

def divide_with_remainder(a: int, b: int) -> tuple[int, int]:
    """Return (quotient, remainder)"""
    return divmod(a, b)

# Usage
name, age, active = get_user_info(1)
quotient, remainder = divide_with_remainder(17, 5)

# Can ignore values
name, _, _ = get_user_info(1)
```

### Go - Native Multiple Returns
```go
func getUserInfo(userID int) (string, int, bool) {
    return "Alice", 30, true
}

func divideWithRemainder(a, b int) (quotient int, remainder int) {
    quotient = a / b
    remainder = a % b
    return  // Naked return uses named return values
}

// Usage
name, age, active := getUserInfo(1)
quotient, remainder := divideWithRemainder(17, 5)

// Can ignore values
name, _, _ := getUserInfo(1)
```

### Rust - Tuples
```rust
fn get_user_info(user_id: i32) -> (String, i32, bool) {
    ("Alice".to_string(), 30, true)
}

fn divide_with_remainder(a: i32, b: i32) -> (i32, i32) {
    (a / b, a % b)
}

// Usage
let (name, age, active) = get_user_info(1);
let (quotient, remainder) = divide_with_remainder(17, 5);

// Can ignore values
let (name, _, _) = get_user_info(1);
```

---

## 7. Optional/Nullable Returns {#optional-returns}

### When to Use
- Value may not exist (search, lookup)
- Computation may fail (parsing, conversion)
- Distinguish between "no value" and "zero value"

### Python - Optional
```python
from typing import Optional

def find_user(user_id: int) -> Optional[dict]:
    """Return user or None if not found"""
    users = {1: {"name": "Alice"}, 2: {"name": "Bob"}}
    return users.get(user_id)

def parse_int(s: str) -> Optional[int]:
    """Parse string to int, return None on failure"""
    try:
        return int(s)
    except ValueError:
        return None

# Usage
user = find_user(1)
if user is not None:
    print(user["name"])

number = parse_int("123")
if number is not None:
    print(f"Parsed: {number}")
```

### Go - Pointer or Multiple Returns
```go
// Using pointer (nullable)
func findUser(userID int) *User {
    users := map[int]User{
        1: {Name: "Alice"},
        2: {Name: "Bob"},
    }
    if user, ok := users[userID]; ok {
        return &user
    }
    return nil
}

// Using multiple returns (preferred)
func parseInt(s string) (int, bool) {
    val, err := strconv.Atoi(s)
    if err != nil {
        return 0, false
    }
    return val, true
}

// Usage
if user := findUser(1); user != nil {
    fmt.Println(user.Name)
}

if number, ok := parseInt("123"); ok {
    fmt.Printf("Parsed: %d\n", number)
}
```

### Rust - Option Type
```rust
use std::collections::HashMap;

fn find_user(user_id: i32) -> Option<User> {
    let mut users = HashMap::new();
    users.insert(1, User { name: "Alice".to_string() });
    users.insert(2, User { name: "Bob".to_string() });
    
    users.get(&user_id).cloned()
}

fn parse_int(s: &str) -> Option<i32> {
    s.parse().ok()
}

// Usage
if let Some(user) = find_user(1) {
    println!("{}", user.name);
}

match parse_int("123") {
    Some(number) => println!("Parsed: {}", number),
    None => println!("Parse failed"),
}

// Or with unwrap_or
let number = parse_int("123").unwrap_or(0);
```

---

## 8. Best Practices by Use Case {#best-practices}

### Validation Functions
**Use**: Boolean returns

```python
# Python
def is_valid_password(password: str) -> bool:
    return len(password) >= 8 and any(c.isdigit() for c in password)
```

```go
// Go
func isValidPassword(password string) bool {
    return len(password) >= 8
}
```

```rust
// Rust
fn is_valid_password(password: &str) -> bool {
    password.len() >= 8
}
```

### Operations That Can Fail
**Use**: Error returns (Go/Rust), Exceptions (Python)

```python
# Python
def create_user(name: str) -> User:
    if not name:
        raise ValueError("Name cannot be empty")
    return User(name)
```

```go
// Go
func createUser(name string) (*User, error) {
    if name == "" {
        return nil, errors.New("name cannot be empty")
    }
    return &User{Name: name}, nil
}
```

```rust
// Rust
fn create_user(name: String) -> Result<User, String> {
    if name.is_empty() {
        return Err("Name cannot be empty".to_string());
    }
    Ok(User { name })
}
```

### Search/Lookup Operations
**Use**: Optional returns or -1 for indexes

```python
# Python
def find_user_by_email(email: str) -> Optional[User]:
    # Search database
    return user if found else None
```

```go
// Go
func findUserByEmail(email string) (*User, bool) {
    // Search database
    return user, found
}
```

```rust
// Rust
fn find_user_by_email(email: &str) -> Option<User> {
    // Search database
}
```

### Side Effects (Logging, I/O)
**Use**: No return value

```python
# Python
def log_event(event: str) -> None:
    print(f"[LOG] {event}")
```

```go
// Go
func logEvent(event string) {
    fmt.Printf("[LOG] %s\n", event)
}
```

```rust
// Rust
fn log_event(event: &str) {
    println!("[LOG] {}", event);
}
```

### Complex Operations
**Use**: Result objects or multiple returns

```python
# Python
from dataclasses import dataclass

@dataclass
class ProcessResult:
    success: bool
    data: Optional[str]
    error: Optional[str]

def process_data(input: str) -> ProcessResult:
    if not input:
        return ProcessResult(False, None, "Empty input")
    return ProcessResult(True, input.upper(), None)
```

```go
// Go
type ProcessResult struct {
    Success bool
    Data    string
    Error   error
}

func processData(input string) ProcessResult {
    if input == "" {
        return ProcessResult{false, "", errors.New("empty input")}
    }
    return ProcessResult{true, strings.ToUpper(input), nil}
}
```

```rust
// Rust
struct ProcessResult {
    success: bool,
    data: Option<String>,
    error: Option<String>,
}

fn process_data(input: &str) -> ProcessResult {
    if input.is_empty() {
        return ProcessResult {
            success: false,
            data: None,
            error: Some("Empty input".to_string()),
        };
    }
    ProcessResult {
        success: true,
        data: Some(input.to_uppercase()),
        error: None,
    }
}
```

---

## Summary Table

| Use Case | Python | Go | Rust |
|----------|--------|-----|------|
| No return needed | `-> None` | (no return) | (unit `()`) |
| Simple validation | `-> bool` | `-> bool` | `-> bool` |
| Can fail | Raise exception | `-> (T, error)` | `-> Result<T, E>` |
| May not exist | `-> Optional[T]` | `-> (*T, bool)` | `-> Option<T>` |
| Multiple values | `-> tuple` | Multiple returns | `-> tuple` |
| Status code | `-> int` (-1, 0, 1+) | `-> int` | `-> i32` (prefer Result) |

### Key Takeaways

1. **Python**: Use exceptions for errors, `None` for missing values, type hints for clarity
2. **Go**: Explicit error handling with multiple returns, use pointers for optional values
3. **Rust**: Strong type system with `Result` and `Option`, compiler-enforced error handling

Each language has idiomatic patterns—follow them for clearer, more maintainable code!

# Comprehensive Guide to Functions in Go, Rust, and Python

I'll create a detailed guide covering function implementations, return patterns, and best practices across these three languages.I've created a comprehensive guide covering all aspects of functions across Go, Rust, and Python! The guide includes:

## What's Covered:

1. **Basic Syntax** - How to declare functions in each language
2. **Functions Returning Nothing** - When and how to use void/None/unit returns
3. **Boolean Returns** - For validation and predicate functions
4. **Integer Status Codes** - Legacy patterns with 0/-1 return codes
5. **Error Handling** - Language-specific error patterns (exceptions, Result, error returns)
6. **Multiple Return Values** - Tuples and native multiple returns
7. **Optional/Nullable Returns** - Handling cases where values might not exist
8. **Best Practices** - Specific guidance for different use cases

## Key Highlights:

- **When to use each pattern** with clear examples
- **Side-by-side comparisons** showing idiomatic code in all three languages
- **Real-world scenarios** like validation, search operations, I/O, and complex processing
- **Summary table** for quick reference

Each section includes working code examples and explains the philosophy behind each language's approach. Python favors exceptions, Go uses explicit error returns, and Rust enforces safety through its type system with `Result` and `Option`.

Would you like me to expand on any particular pattern or add more specific use cases?