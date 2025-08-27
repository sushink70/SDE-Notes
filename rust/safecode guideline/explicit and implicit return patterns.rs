I'll show you comprehensive examples of `return` keyword usage in Rust, covering both explicit and implicit return patterns across different contexts.This comprehensive example covers all the major use cases for explicit and implicit `return` statements in Rust:

## Key Patterns:

### **Implicit Returns (Rust Idiom - Preferred)**
- No `return` keyword, no semicolon
- Expression at end of block/function
- Cleaner, more idiomatic Rust code

### **Explicit Returns (Required in some cases)**
- Use `return` keyword with semicolon
- **Required** for early returns (guard clauses)
- **Required** when returning from middle of function
- **Required** in some control flow situations

## When to Use Each:

### **Use Implicit Returns:**
- Final expression in functions
- Match arms
- If/else expressions
- Block expressions
- When following Rust idioms

### **Use Explicit Returns:**
- Early returns (guard clauses)
- Multiple return points
- Returning from loops early
- Error handling patterns
- When breaking out of nested control flow

## Important Notes:

1. **Semicolons matter**: Adding `;` turns an expression into a statement
2. **Early returns require explicit `return`**
3. **Match arms can use either style**
4. **Closures follow the same rules**
5. **Unit type `()` can be returned implicitly or explicitly**
6. **Const functions support both styles**
7. **Never type `!` functions don't need returns**

The examples show real-world patterns you'll encounter in Rust codebases, from simple functions to complex async operations, generics, traits, and macros.

// =============================================================================
// RUST RETURN KEYWORD - EXPLICIT vs IMPLICIT USAGE EXAMPLES
// =============================================================================

// -----------------------------------------------------------------------------
// 1. BASIC FUNCTION RETURNS
// -----------------------------------------------------------------------------

// Implicit return (Rust idiom - preferred)
fn add_implicit(a: i32, b: i32) -> i32 {
    a + b  // No semicolon = expression = return value
}

// Explicit return
fn add_explicit(a: i32, b: i32) -> i32 {
    return a + b;  // Explicit return with semicolon
}

// Mixed style (not recommended)
fn add_mixed(a: i32, b: i32) -> i32 {
    let result = a + b;
    result  // Implicit return of variable
}

// Explicit return of variable
fn add_explicit_var(a: i32, b: i32) -> i32 {
    let result = a + b;
    return result;
}

// -----------------------------------------------------------------------------
// 2. EARLY RETURNS AND GUARDS
// -----------------------------------------------------------------------------

// Early return with guards (explicit return required)
fn divide_safe(a: f64, b: f64) -> Option<f64> {
    if b == 0.0 {
        return None;  // Early return - explicit required
    }
    Some(a / b)  // Implicit return at end
}

// Multiple early returns
fn categorize_number(n: i32) -> &'static str {
    if n < 0 {
        return "negative";  // Explicit early return
    }
    if n == 0 {
        return "zero";      // Explicit early return
    }
    if n > 100 {
        return "large";     // Explicit early return
    }
    "positive"  // Implicit final return
}

// Guard clauses with explicit returns
fn process_user(name: Option<&str>, age: Option<u8>) -> Result<String, &'static str> {
    let name = match name {
        Some(n) if !n.is_empty() => n,
        _ => return Err("Invalid name"),  // Explicit return in match arm
    };
    
    let age = match age {
        Some(a) if a >= 18 => a,
        _ => return Err("Must be adult"),  // Explicit return in match arm
    };
    
    Ok(format!("User: {}, Age: {}", name, age))  // Implicit return
}

// -----------------------------------------------------------------------------
// 3. CLOSURES AND LAMBDA EXPRESSIONS
// -----------------------------------------------------------------------------

fn closure_examples() {
    // Implicit return in closure (single expression)
    let add = |x, y| x + y;
    
    // Explicit return in closure
    let add_explicit = |x, y| {
        return x + y;
    };
    
    // Mixed in closure body
    let add_mixed = |x, y| {
        let result = x + y;
        result  // Implicit return
    };
    
    // Early return in closure
    let divide = |x: f64, y: f64| {
        if y == 0.0 {
            return 0.0;  // Explicit early return
        }
        x / y  // Implicit return
    };
    
    // Closure with complex logic
    let process = |numbers: Vec<i32>| {
        if numbers.is_empty() {
            return Vec::new();  // Early explicit return
        }
        
        numbers.into_iter()
               .filter(|&x| x > 0)
               .collect()  // Implicit return
    };
}

// -----------------------------------------------------------------------------
// 4. MATCH EXPRESSIONS
// -----------------------------------------------------------------------------

// Implicit returns in match arms
fn match_implicit(option: Option<i32>) -> i32 {
    match option {
        Some(value) => value * 2,      // Implicit return in arm
        None => 0,                     // Implicit return in arm
    }  // Implicit return of entire match
}

// Explicit returns in match arms
fn match_explicit(option: Option<i32>) -> i32 {
    match option {
        Some(value) => return value * 2,  // Explicit return in arm
        None => return 0,                 // Explicit return in arm
    }
}

// Mixed match arms
fn match_mixed(result: Result<i32, &str>) -> i32 {
    match result {
        Ok(value) => {
            println!("Success: {}", value);
            value  // Implicit return in block
        },
        Err(_) => {
            println!("Error occurred");
            return -1;  // Explicit return in block
        }
    }
}

// Complex match with early returns
fn match_complex(data: Option<Vec<i32>>) -> i32 {
    let vec = match data {
        Some(v) if !v.is_empty() => v,
        Some(_) => return 0,     // Explicit return for empty vec
        None => return -1,       // Explicit return for None
    };
    
    vec.iter().sum()  // Implicit return
}

// -----------------------------------------------------------------------------
// 5. IF-ELSE EXPRESSIONS
// -----------------------------------------------------------------------------

// Implicit returns in if-else
fn if_implicit(x: i32) -> &'static str {
    if x > 0 {
        "positive"     // Implicit return
    } else if x < 0 {
        "negative"     // Implicit return
    } else {
        "zero"         // Implicit return
    }  // Implicit return of entire if-else
}

// Explicit returns in if-else
fn if_explicit(x: i32) -> &'static str {
    if x > 0 {
        return "positive";     // Explicit return
    } else if x < 0 {
        return "negative";     // Explicit return
    } else {
        return "zero";         // Explicit return
    }
}

// Mixed if-else
fn if_mixed(x: i32) -> i32 {
    if x < 0 {
        return 0;  // Early explicit return
    }
    
    if x > 100 {
        100        // Implicit return
    } else {
        x          // Implicit return
    }
}

// -----------------------------------------------------------------------------
// 6. LOOP RETURNS
// -----------------------------------------------------------------------------

// Return from loop with explicit return
fn find_first_even(numbers: &[i32]) -> Option<i32> {
    for &num in numbers {
        if num % 2 == 0 {
            return Some(num);  // Explicit return from function
        }
    }
    None  // Implicit return
}

// Loop with break and implicit return
fn sum_until_negative(numbers: &[i32]) -> i32 {
    let mut sum = 0;
    for &num in numbers {
        if num < 0 {
            break;  // Break from loop, not return
        }
        sum += num;
    }
    sum  // Implicit return
}

// While loop with explicit return
fn find_power_of_two(target: u32) -> Option<u32> {
    let mut power = 1;
    while power <= target {
        if power == target {
            return Some(power);  // Explicit return
        }
        power *= 2;
    }
    None  // Implicit return
}

// Loop with labeled break (not return)
fn nested_loop_example(matrix: &[Vec<i32>]) -> Option<(usize, usize)> {
    'outer: for (i, row) in matrix.iter().enumerate() {
        for (j, &value) in row.iter().enumerate() {
            if value == 0 {
                break 'outer;  // Labeled break, not return
            }
            if value < 0 {
                return Some((i, j));  // Explicit return
            }
        }
    }
    None  // Implicit return
}

// -----------------------------------------------------------------------------
// 7. BLOCK EXPRESSIONS
// -----------------------------------------------------------------------------

fn block_examples() -> i32 {
    // Implicit return from block
    let result = {
        let x = 10;
        let y = 20;
        x + y  // Implicit return from block
    };
    
    // Explicit return from block
    let result2 = {
        let x = 10;
        let y = 20;
        return x + y;  // This returns from function, not block!
    };
    
    // Correct explicit return within block scope
    let result3 = {
        let x = 10;
        let y = 20;
        if x > 5 {
            x + y  // Implicit return from block
        } else {
            0      // Implicit return from block
        }
    };
    
    result + result3  // Implicit return from function
}

// -----------------------------------------------------------------------------
// 8. ASYNC FUNCTIONS
// -----------------------------------------------------------------------------

// Implicit return in async function
async fn fetch_data_implicit(id: u32) -> Result<String, &'static str> {
    if id == 0 {
        return Err("Invalid ID");  // Explicit early return
    }
    
    // Simulate async operation
    Ok(format!("Data for ID: {}", id))  // Implicit return
}

// Explicit return in async function
async fn fetch_data_explicit(id: u32) -> Result<String, &'static str> {
    if id == 0 {
        return Err("Invalid ID");  // Explicit early return
    }
    
    // Simulate async operation
    return Ok(format!("Data for ID: {}", id));  // Explicit return
}

// -----------------------------------------------------------------------------
// 9. GENERIC FUNCTIONS
// -----------------------------------------------------------------------------

// Implicit return with generics
fn get_first_implicit<T: Clone>(items: &[T]) -> Option<T> {
    items.first().cloned()  // Implicit return
}

// Explicit return with generics
fn get_first_explicit<T: Clone>(items: &[T]) -> Option<T> {
    return items.first().cloned();  // Explicit return
}

// Mixed with generics and constraints
fn find_max<T: PartialOrd + Copy>(items: &[T]) -> Option<T> {
    if items.is_empty() {
        return None;  // Explicit early return
    }
    
    let mut max = items[0];
    for &item in items.iter().skip(1) {
        if item > max {
            max = item;
        }
    }
    Some(max)  // Implicit return
}

// -----------------------------------------------------------------------------
// 10. METHODS AND IMPL BLOCKS
// -----------------------------------------------------------------------------

struct Calculator {
    value: f64,
}

impl Calculator {
    // Constructor with implicit return
    fn new(initial: f64) -> Self {
        Calculator { value: initial }  // Implicit return
    }
    
    // Constructor with explicit return
    fn new_explicit(initial: f64) -> Self {
        return Calculator { value: initial };  // Explicit return
    }
    
    // Method with implicit return
    fn add(&mut self, other: f64) -> f64 {
        self.value += other;
        self.value  // Implicit return
    }
    
    // Method with explicit return
    fn subtract_explicit(&mut self, other: f64) -> f64 {
        self.value -= other;
        return self.value;  // Explicit return
    }
    
    // Method with early return
    fn divide(&mut self, other: f64) -> Result<f64, &'static str> {
        if other == 0.0 {
            return Err("Division by zero");  // Explicit early return
        }
        self.value /= other;
        Ok(self.value)  // Implicit return
    }
    
    // Getter with implicit return
    fn get_value(&self) -> f64 {
        self.value  // Implicit return
    }
}

// -----------------------------------------------------------------------------
// 11. TRAIT IMPLEMENTATIONS
// -----------------------------------------------------------------------------

use std::fmt::Display;

impl Display for Calculator {
    // Trait method with implicit return
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "Calculator({})", self.value)  // Implicit return
    }
}

// Custom trait
trait Processable {
    fn process(&self) -> String;
    fn validate(&self) -> bool;
}

impl Processable for Calculator {
    // Trait method with explicit return
    fn process(&self) -> String {
        if self.value < 0.0 {
            return String::from("Negative");  // Explicit early return
        }
        format!("Value: {:.2}", self.value)  // Implicit return
    }
    
    // Trait method with implicit return only
    fn validate(&self) -> bool {
        self.value.is_finite()  // Implicit return
    }
}

// -----------------------------------------------------------------------------
// 12. MACRO RULES (PROCEDURAL)
// -----------------------------------------------------------------------------

macro_rules! create_function {
    ($name:ident, $return_type:ty, $value:expr) => {
        fn $name() -> $return_type {
            $value  // Implicit return in macro expansion
        }
    };
}

// Usage
create_function!(get_number, i32, 42);
create_function!(get_string, String, String::from("Hello"));

// Macro with explicit return
macro_rules! create_function_explicit {
    ($name:ident, $return_type:ty, $value:expr) => {
        fn $name() -> $return_type {
            return $value;  // Explicit return in macro
        }
    };
}

// -----------------------------------------------------------------------------
// 13. ITERATOR METHODS
// -----------------------------------------------------------------------------

fn iterator_examples() {
    let numbers = vec![1, 2, 3, 4, 5];
    
    // Implicit returns in closures
    let doubled: Vec<i32> = numbers.iter()
        .map(|x| x * 2)              // Implicit return in closure
        .filter(|&&x| x > 4)         // Implicit return in closure
        .cloned()
        .collect();
    
    // Explicit returns in closures
    let processed: Vec<String> = numbers.iter()
        .map(|x| {
            if *x % 2 == 0 {
                return format!("Even: {}", x);  // Explicit return
            }
            format!("Odd: {}", x)  // Implicit return
        })
        .collect();
    
    // find with early return
    let found = numbers.iter().find(|&&x| {
        if x > 10 {
            return false;  // Explicit return from closure
        }
        x % 2 == 0  // Implicit return from closure
    });
}

// -----------------------------------------------------------------------------
// 14. NEVER TYPE AND DIVERGING FUNCTIONS
// -----------------------------------------------------------------------------

// Function that never returns (diverging)
fn panic_function() -> ! {
    panic!("This function never returns normally!");
}

// Function with never type in match
fn handle_result(result: Result<i32, &str>) -> i32 {
    match result {
        Ok(value) => value,                    // Implicit return
        Err(_) => panic_function(),            // Never returns, so no return needed
    }
}

// -----------------------------------------------------------------------------
// 15. CONST FUNCTIONS
// -----------------------------------------------------------------------------

// Const function with implicit return
const fn const_add_implicit(a: i32, b: i32) -> i32 {
    a + b  // Implicit return
}

// Const function with explicit return
const fn const_add_explicit(a: i32, b: i32) -> i32 {
    return a + b;  // Explicit return
}

// Const function with conditional
const fn const_max(a: i32, b: i32) -> i32 {
    if a > b {
        a      // Implicit return
    } else {
        b      // Implicit return
    }
}

// -----------------------------------------------------------------------------
// 16. UNIT TYPE RETURNS
// -----------------------------------------------------------------------------

// Function returning unit type (()) - implicit
fn print_message_implicit(msg: &str) {
    println!("{}", msg);
    // Implicit return of ()
}

// Function returning unit type - explicit
fn print_message_explicit(msg: &str) -> () {
    println!("{}", msg);
    return ();  // Explicit return of unit
}

// Function with early return of unit
fn conditional_print(should_print: bool, msg: &str) {
    if !should_print {
        return;  // Early return of unit (no value needed)
    }
    println!("{}", msg);
    // Implicit return of ()
}

// -----------------------------------------------------------------------------
// MAIN FUNCTION EXAMPLES
// -----------------------------------------------------------------------------

fn main() {
    // Test basic functions
    println!("Implicit add: {}", add_implicit(2, 3));
    println!("Explicit add: {}", add_explicit(2, 3));
    
    // Test early returns
    println!("Division: {:?}", divide_safe(10.0, 2.0));
    println!("Division by zero: {:?}", divide_safe(10.0, 0.0));
    
    // Test categorization
    println!("Category: {}", categorize_number(-5));
    println!("Category: {}", categorize_number(0));
    println!("Category: {}", categorize_number(150));
    println!("Category: {}", categorize_number(42));
    
    // Test calculator
    let mut calc = Calculator::new(10.0);
    println!("Calculator: {}", calc);
    println!("After add: {}", calc.add(5.0));
    println!("After divide: {:?}", calc.divide(3.0));
    
    // Test const functions
    const RESULT1: i32 = const_add_implicit(5, 3);
    const RESULT2: i32 = const_add_explicit(5, 3);
    println!("Const results: {}, {}", RESULT1, RESULT2);
    
    // Implicit return of () from main
}