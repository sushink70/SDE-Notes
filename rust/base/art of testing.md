# The Complete Art of Testing in Rust: From Fundamentals to Mastery

## Philosophy: Why Testing Matters for Top 1% Engineers

Before diving into mechanics, understand this: **testing is not bureaucracy—it's a mental discipline**. Elite engineers write tests because:
- Tests force **precise thinking** about edge cases before code exists
- They create a **safety net** for fearless refactoring (essential for DSA optimization)
- They document **behavioral contracts** better than comments ever could

Think of tests as **mathematical proofs** for your code's correctness.

---

## Part I: The Foundation - Writing Tests in Rust

### 1.1 Anatomy of a Test Function

**What is a test?** A test is a function that verifies a specific behavior or property of your code. In Rust, tests are regular functions marked with the `#[test]` attribute.

```rust
// Basic structure of a test
#[test]
fn test_name() {
    // Arrange: Set up test data
    let input = 5;
    
    // Act: Execute the code under test
    let result = my_function(input);
    
    // Assert: Verify the result
    assert_eq!(result, expected_value);
}
```

**Mental Model:** Think of tests following the **AAA pattern** (Arrange-Act-Assert):
- **Arrange**: Prepare your battlefield (test data)
- **Act**: Execute the operation (call the function)
- **Assert**: Verify victory conditions (check correctness)

### 1.2 The Three Core Assertion Macros

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn demonstrate_assertions() {
        // 1. assert! - Tests boolean conditions
        // Use when: You need custom logic
        let x = 10;
        assert!(x > 5, "x should be greater than 5, got {}", x);
        
        // 2. assert_eq! - Tests equality
        // Use when: Comparing values (most common)
        let result = add(2, 3);
        assert_eq!(result, 5);
        
        // 3. assert_ne! - Tests inequality
        // Use when: Ensuring values are different
        let a = vec![1, 2];
        let b = vec![1, 2, 3];
        assert_ne!(a, b);
    }
    
    fn add(a: i32, b: i32) -> i32 {
        a + b
    }
}
```

**Hidden Knowledge:** 
- `assert_eq!` and `assert_ne!` require types to implement `PartialEq` and `Debug` traits
- The order matters: `assert_eq!(actual, expected)` — this is **convention** for better error messages
- Custom messages use `format!` syntax under the hood

### 1.3 Testing Panics: The `#[should_panic]` Attribute

**Concept: Panic** = Rust's way of saying "unrecoverable error occurred, abort execution"

When testing error conditions, you often want to verify your code **correctly panics**:

```rust
#[cfg(test)]
mod panic_tests {
    use super::*;

    // Basic panic test
    #[test]
    #[should_panic]
    fn test_division_by_zero_panics() {
        divide(10, 0); // Should panic
    }
    
    // Advanced: Verify specific panic message
    #[test]
    #[should_panic(expected = "Cannot divide by zero")]
    fn test_panic_message() {
        divide_with_message(10, 0);
    }
    
    fn divide(a: i32, b: i32) -> i32 {
        if b == 0 {
            panic!("Cannot divide by zero");
        }
        a / b
    }
    
    fn divide_with_message(a: i32, b: i32) -> i32 {
        assert!(b != 0, "Cannot divide by zero");
        a / b
    }
}
```

**Expert Insight:** `should_panic(expected = "...")` uses **substring matching**, not exact equality. This is both powerful and dangerous:

```rust
#[test]
#[should_panic(expected = "zero")] // Passes if panic message contains "zero"
fn flexible_panic_check() {
    panic!("Cannot divide by zero!");
}
```

### 1.4 Using `Result<T, E>` in Tests (Modern Approach)

**Paradigm Shift:** Instead of panicking, return `Result` for more granular control:

```rust
#[cfg(test)]
mod result_tests {
    use super::*;

    #[test]
    fn test_with_result() -> Result<(), String> {
        let result = parse_number("42")?;
        
        if result != 42 {
            return Err(String::from("Parsed value incorrect"));
        }
        
        Ok(())
    }
    
    #[test]
    fn test_error_propagation() -> Result<(), Box<dyn std::error::Error>> {
        let data = std::fs::read_to_string("test_file.txt")?;
        assert!(data.len() > 0);
        Ok(())
    }
    
    fn parse_number(s: &str) -> Result<i32, String> {
        s.parse::<i32>().map_err(|e| e.to_string())
    }
}
```

**Why This Matters:**
- `?` operator provides **early return** on error
- More **composable** than panics
- Better for integration tests where setup might fail
- Test fails if function returns `Err`

---

## Part II: Test Organization - The `#[cfg(test)]` Module Pattern

### 2.1 The Standard Unit Test Structure

**Concept: Conditional Compilation** - `#[cfg(test)]` tells Rust to compile this code **only** when running tests.

```rust
// src/lib.rs or src/module.rs

pub fn fibonacci(n: u32) -> u64 {
    match n {
        0 => 0,
        1 => 1,
        _ => fibonacci(n - 1) + fibonacci(n - 2),
    }
}

// Tests module - only compiled during testing
#[cfg(test)]
mod tests {
    // Import everything from parent module
    use super::*;
    
    #[test]
    fn test_fibonacci_base_cases() {
        assert_eq!(fibonacci(0), 0);
        assert_eq!(fibonacci(1), 1);
    }
    
    #[test]
    fn test_fibonacci_recursive_cases() {
        assert_eq!(fibonacci(2), 1);
        assert_eq!(fibonacci(10), 55);
    }
}
```

**Why `use super::*;`?** 
- `super` refers to the **parent module**
- `*` imports all public items
- Alternative: `use super::fibonacci;` for explicit imports

### 2.2 Integration Tests vs Unit Tests

**Mental Model:**

```
Project Structure (Mental Map):

my_crate/
├── src/
│   ├── lib.rs          ← Unit tests here (#[cfg(test)] mod tests)
│   └── utils.rs        ← Unit tests here
├── tests/              ← Integration tests (separate files)
│   ├── integration_test.rs
│   └── common/
│       └── mod.rs      ← Shared test utilities
└── Cargo.toml
```

#### Unit Tests (White-box testing)
- **Location:** Same file as code (`#[cfg(test)] mod tests`)
- **Purpose:** Test individual functions/modules in isolation
- **Access:** Can test private functions
- **Compilation:** Only when running tests

```rust
// src/stack.rs
pub struct Stack<T> {
    items: Vec<T>, // Private field
}

impl<T> Stack<T> {
    pub fn new() -> Self {
        Stack { items: Vec::new() }
    }
    
    pub fn push(&mut self, item: T) {
        self.items.push(item);
    }
    
    // Private helper function
    fn internal_size(&self) -> usize {
        self.items.len()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_private_function() {
        let stack = Stack::<i32>::new();
        // Can test private methods!
        assert_eq!(stack.internal_size(), 0);
    }
    
    #[test]
    fn test_private_field_access() {
        let mut stack = Stack::new();
        stack.push(5);
        // Can access private fields!
        assert_eq!(stack.items.len(), 1);
    }
}
```

#### Integration Tests (Black-box testing)
- **Location:** `tests/` directory at project root
- **Purpose:** Test public API as external users would
- **Access:** Only public items (like external crate)
- **Each file:** Separate crate (compiled independently)

```rust
// tests/integration_test.rs
use my_crate::Stack; // Must use crate name

#[test]
fn test_public_api() {
    let mut stack = Stack::new();
    stack.push(10);
    // Cannot access private fields or methods
    // stack.items; // ERROR: field `items` is private
}
```

### 2.3 Shared Test Utilities (Common Module Pattern)

**Problem:** You want helper functions shared across integration tests.

**Solution:** Use `tests/common/mod.rs` pattern:

```rust
// tests/common/mod.rs
pub fn setup_test_environment() -> TestFixture {
    TestFixture {
        data: vec![1, 2, 3, 4, 5],
    }
}

pub struct TestFixture {
    pub data: Vec<i32>,
}

impl TestFixture {
    pub fn get_sorted_data(&self) -> Vec<i32> {
        let mut sorted = self.data.clone();
        sorted.sort();
        sorted
    }
}
```

```rust
// tests/integration_test.rs
mod common; // Import common module

#[test]
fn test_with_fixture() {
    let fixture = common::setup_test_environment();
    assert_eq!(fixture.data.len(), 5);
}
```

**Critical Detail:** Rust treats `tests/common/mod.rs` as a **module**, not a test file, so it won't try to run it as tests.

---

## Part III: Controlling Test Execution

### 3.1 Running Tests - The Mental Model

**Concept:** By default, Rust runs tests in **parallel** across multiple threads for speed.

```bash
# Basic test execution
cargo test

# Flow:
# 1. Cargo compiles code in test mode
# 2. Runs all tests in parallel
# 3. Captures stdout/stderr (hidden by default)
# 4. Reports pass/fail
```

### 3.2 Sequential Test Execution

**When to use:** Tests that share state or resources (files, databases, global variables)

```rust
// tests/sequential_tests.rs

use std::fs::File;
use std::io::Write;

#[test]
fn test_write_file() {
    let mut file = File::create("shared.txt").unwrap();
    file.write_all(b"test data").unwrap();
}

#[test]
fn test_read_file() {
    let content = std::fs::read_to_string("shared.txt").unwrap();
    assert!(content.len() > 0);
}
```

**Problem:** These tests might interfere if run in parallel!

**Solution:**
```bash
# Run tests sequentially (one at a time)
cargo test -- --test-threads=1
```

**Performance Trade-off:**
- Parallel (default): Fast but requires isolation
- Sequential: Slower but allows shared state

### 3.3 Showing Test Output

**Default Behavior:** Rust **captures** stdout/stderr for passing tests.

```rust
#[test]
fn test_with_output() {
    println!("Debug value: {}", 42);
    assert_eq!(2 + 2, 4);
    // You won't see the println! output unless test fails
}
```

**Show output for ALL tests:**
```bash
cargo test -- --show-output
```

**Real-World Use Case:** Debugging flaky tests or understanding test execution flow.

### 3.4 Running Specific Tests by Name

```bash
# Run all tests with "add" in the name
cargo test add

# Run exact test
cargo test test_add_positive_numbers

# Run all tests in a module
cargo test tests::math_tests
```

**Pattern Matching Flow:**
```
cargo test fibonacci
         ↓
Searches for test functions containing "fibonacci"
         ↓
Runs: test_fibonacci_base
      test_fibonacci_recursive
      fibonacci_performance_test
```

### 3.5 Ignoring Tests

**Use Case:** Expensive tests (benchmarks, integration tests that hit external services)

```rust
#[test]
#[ignore]
fn expensive_test() {
    // Simulate expensive operation
    std::thread::sleep(std::time::Duration::from_secs(10));
    assert_eq!(2 + 2, 4);
}

#[test]
fn quick_test() {
    assert_eq!(1 + 1, 2);
}
```

```bash
# Run normal tests (skips ignored)
cargo test

# Run ONLY ignored tests
cargo test -- --ignored

# Run ALL tests (including ignored)
cargo test -- --include-ignored
```

---

## Part IV: Real-World DSA Testing Examples

### 4.1 Testing a Binary Search Implementation

```rust
// src/search.rs

/// Performs binary search on a sorted slice.
/// Returns Some(index) if found, None otherwise.
/// 
/// Time Complexity: O(log n)
/// Space Complexity: O(1)
pub fn binary_search<T: Ord>(arr: &[T], target: &T) -> Option<usize> {
    let mut left = 0;
    let mut right = arr.len();
    
    while left < right {
        let mid = left + (right - left) / 2; // Avoid overflow
        
        match arr[mid].cmp(target) {
            std::cmp::Ordering::Equal => return Some(mid),
            std::cmp::Ordering::Less => left = mid + 1,
            std::cmp::Ordering::Greater => right = mid,
        }
    }
    
    None
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_empty_array() {
        let arr: Vec<i32> = vec![];
        assert_eq!(binary_search(&arr, &5), None);
    }
    
    #[test]
    fn test_single_element_found() {
        let arr = vec![5];
        assert_eq!(binary_search(&arr, &5), Some(0));
    }
    
    #[test]
    fn test_single_element_not_found() {
        let arr = vec![5];
        assert_eq!(binary_search(&arr, &3), None);
    }
    
    #[test]
    fn test_found_at_beginning() {
        let arr = vec![1, 2, 3, 4, 5];
        assert_eq!(binary_search(&arr, &1), Some(0));
    }
    
    #[test]
    fn test_found_at_end() {
        let arr = vec![1, 2, 3, 4, 5];
        assert_eq!(binary_search(&arr, &5), Some(4));
    }
    
    #[test]
    fn test_found_in_middle() {
        let arr = vec![1, 2, 3, 4, 5];
        assert_eq!(binary_search(&arr, &3), Some(2));
    }
    
    #[test]
    fn test_not_found_too_small() {
        let arr = vec![10, 20, 30];
        assert_eq!(binary_search(&arr, &5), None);
    }
    
    #[test]
    fn test_not_found_too_large() {
        let arr = vec![10, 20, 30];
        assert_eq!(binary_search(&arr, &40), None);
    }
    
    #[test]
    fn test_not_found_between_elements() {
        let arr = vec![10, 20, 30];
        assert_eq!(binary_search(&arr, &25), None);
    }
    
    #[test]
    fn test_duplicate_elements() {
        let arr = vec![1, 2, 2, 2, 3];
        // Should find ANY occurrence
        let result = binary_search(&arr, &2);
        assert!(result.is_some());
        assert!((1..=3).contains(&result.unwrap()));
    }
    
    #[test]
    fn test_large_array() {
        let arr: Vec<i32> = (0..10000).collect();
        assert_eq!(binary_search(&arr, &5000), Some(5000));
        assert_eq!(binary_search(&arr, &10001), None);
    }
}
```

**Test Design Principles Demonstrated:**
1. **Edge Cases First:** Empty, single element
2. **Boundary Testing:** First, last, middle positions
3. **Negative Cases:** Not found (too small, too large, between elements)
4. **Special Cases:** Duplicates
5. **Scale Testing:** Large inputs

### 4.2 Testing a Stack with Custom Error Types

```rust
// src/stack.rs

use std::fmt;

#[derive(Debug, PartialEq)]
pub enum StackError {
    Overflow,
    Underflow,
}

impl fmt::Display for StackError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            StackError::Overflow => write!(f, "Stack overflow"),
            StackError::Underflow => write!(f, "Stack underflow"),
        }
    }
}

impl std::error::Error for StackError {}

pub struct BoundedStack<T> {
    items: Vec<T>,
    capacity: usize,
}

impl<T> BoundedStack<T> {
    pub fn new(capacity: usize) -> Self {
        BoundedStack {
            items: Vec::with_capacity(capacity),
            capacity,
        }
    }
    
    pub fn push(&mut self, item: T) -> Result<(), StackError> {
        if self.items.len() >= self.capacity {
            return Err(StackError::Overflow);
        }
        self.items.push(item);
        Ok(())
    }
    
    pub fn pop(&mut self) -> Result<T, StackError> {
        self.items.pop().ok_or(StackError::Underflow)
    }
    
    pub fn peek(&self) -> Result<&T, StackError> {
        self.items.last().ok_or(StackError::Underflow)
    }
    
    pub fn is_empty(&self) -> bool {
        self.items.is_empty()
    }
    
    pub fn len(&self) -> usize {
        self.items.len()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_new_stack_is_empty() {
        let stack: BoundedStack<i32> = BoundedStack::new(10);
        assert!(stack.is_empty());
        assert_eq!(stack.len(), 0);
    }
    
    #[test]
    fn test_push_success() {
        let mut stack = BoundedStack::new(3);
        assert!(stack.push(1).is_ok());
        assert_eq!(stack.len(), 1);
        assert!(!stack.is_empty());
    }
    
    #[test]
    fn test_push_overflow() {
        let mut stack = BoundedStack::new(2);
        stack.push(1).unwrap();
        stack.push(2).unwrap();
        
        let result = stack.push(3);
        assert_eq!(result, Err(StackError::Overflow));
    }
    
    #[test]
    fn test_pop_success() -> Result<(), StackError> {
        let mut stack = BoundedStack::new(5);
        stack.push(42)?;
        
        let value = stack.pop()?;
        assert_eq!(value, 42);
        assert!(stack.is_empty());
        Ok(())
    }
    
    #[test]
    fn test_pop_underflow() {
        let mut stack: BoundedStack<i32> = BoundedStack::new(5);
        let result = stack.pop();
        assert_eq!(result, Err(StackError::Underflow));
    }
    
    #[test]
    fn test_peek_success() -> Result<(), StackError> {
        let mut stack = BoundedStack::new(5);
        stack.push(10)?;
        stack.push(20)?;
        
        assert_eq!(*stack.peek()?, 20);
        assert_eq!(stack.len(), 2); // Peek doesn't remove
        Ok(())
    }
    
    #[test]
    fn test_peek_underflow() {
        let stack: BoundedStack<i32> = BoundedStack::new(5);
        assert_eq!(stack.peek(), Err(StackError::Underflow));
    }
    
    #[test]
    fn test_lifo_order() -> Result<(), StackError> {
        let mut stack = BoundedStack::new(5);
        stack.push(1)?;
        stack.push(2)?;
        stack.push(3)?;
        
        assert_eq!(stack.pop()?, 3);
        assert_eq!(stack.pop()?, 2);
        assert_eq!(stack.pop()?, 1);
        Ok(())
    }
    
    #[test]
    fn test_alternating_operations() -> Result<(), StackError> {
        let mut stack = BoundedStack::new(3);
        stack.push(1)?;
        assert_eq!(stack.pop()?, 1);
        stack.push(2)?;
        stack.push(3)?;
        assert_eq!(*stack.peek()?, 3);
        Ok(())
    }
}
```

**Advanced Testing Patterns:**
1. **Result-based tests** using `?` operator for clean error propagation
2. **Equivalence testing** (`assert_eq!` with custom error types)
3. **State verification** (checking len, is_empty after operations)
4. **Behavioral testing** (LIFO order verification)

---

## Part V: Advanced Testing Techniques

### 5.1 Property-Based Testing Mindset

**Concept:** Instead of testing specific inputs, test **properties** that should hold for ALL inputs.

```rust
#[cfg(test)]
mod property_tests {
    use super::*;
    
    #[test]
    fn test_reverse_twice_equals_original() {
        // Property: reverse(reverse(x)) == x
        let original = vec![1, 2, 3, 4, 5];
        let mut reversed = original.clone();
        reversed.reverse();
        reversed.reverse();
        assert_eq!(reversed, original);
    }
    
    #[test]
    fn test_sort_idempotent() {
        // Property: sort(sort(x)) == sort(x)
        let mut arr1 = vec![3, 1, 4, 1, 5];
        let mut arr2 = arr1.clone();
        
        arr1.sort();
        arr2.sort();
        arr2.sort(); // Sort again
        
        assert_eq!(arr1, arr2);
    }
}
```

### 5.2 Testing with Custom Comparators

```rust
#[derive(Debug, Clone)]
struct Point {
    x: i32,
    y: i32,
}

impl Point {
    fn distance_from_origin(&self) -> f64 {
        ((self.x.pow(2) + self.y.pow(2)) as f64).sqrt()
    }
}

#[cfg(test)]
mod custom_tests {
    use super::*;
    
    #[test]
    fn test_points_approximately_equal() {
        let p1 = Point { x: 3, y: 4 };
        let p2 = Point { x: 3, y: 4 };
        
        // For exact comparison
        assert_eq!(p1.x, p2.x);
        assert_eq!(p1.y, p2.y);
        
        // For floating point distance
        let epsilon = 1e-10;
        assert!((p1.distance_from_origin() - 5.0).abs() < epsilon);
    }
}
```

### 5.3 Benchmark Tests (Nightly Rust)

**Concept:** Measure performance systematically.

```rust
#![feature(test)]
extern crate test;

pub fn fibonacci_recursive(n: u32) -> u64 {
    match n {
        0 => 0,
        1 => 1,
        _ => fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2),
    }
}

pub fn fibonacci_iterative(n: u32) -> u64 {
    if n == 0 { return 0; }
    let mut prev = 0;
    let mut curr = 1;
    for _ in 1..n {
        let next = prev + curr;
        prev = curr;
        curr = next;
    }
    curr
}

#[cfg(test)]
mod benches {
    use super::*;
    use test::Bencher;
    
    #[bench]
    fn bench_fibonacci_recursive(b: &mut Bencher) {
        b.iter(|| fibonacci_recursive(20));
    }
    
    #[bench]
    fn bench_fibonacci_iterative(b: &mut Bencher) {
        b.iter(|| fibonacci_iterative(20));
    }
}
```

```bash
# Run benchmarks (requires nightly Rust)
cargo +nightly bench
```

---

## Part VI: Test Organization Best Practices (Flow Diagram)

```
Testing Decision Tree:

Is it testing internal implementation?
├─ YES → Unit Test (#[cfg(test)] mod in same file)
│         Can access private items
│         Fast, isolated
│
└─ NO → Is it testing public API from external perspective?
         └─ YES → Integration Test (tests/ directory)
                   Only public items
                   Slower, realistic
```

### Complete Project Structure Example:

```
dsa_library/
├── Cargo.toml
├── src/
│   ├── lib.rs                    # Public API
│   ├── sorting/
│   │   ├── mod.rs               # Module declaration
│   │   ├── quicksort.rs         # Implementation + unit tests
│   │   └── mergesort.rs         # Implementation + unit tests
│   ├── searching/
│   │   ├── mod.rs
│   │   └── binary_search.rs     # Implementation + unit tests
│   └── data_structures/
│       ├── mod.rs
│       ├── stack.rs             # Implementation + unit tests
│       └── queue.rs             # Implementation + unit tests
│
└── tests/
    ├── integration_sorting.rs    # Test public sorting API
    ├── integration_searching.rs  # Test public searching API
    ├── benchmarks.rs             # Performance tests
    └── common/
        └── mod.rs                # Shared test utilities
```

---

## Part VII: Hidden Knowledge & Expert Tips

### 7.1 Test Compilation Insights

```rust
// This code is ONLY compiled when running tests
#[cfg(test)]
mod tests {
    // This is ONLY compiled during tests
    use super::*;
    
    // Helper function - not in production binary
    fn create_test_data() -> Vec<i32> {
        vec![1, 2, 3]
    }
}

// This function is ALWAYS compiled (bloats binary if unused)
fn bad_test_helper() -> Vec<i32> {
    vec![1, 2, 3]
}
```

**Binary Size Impact:**
- Unit tests with `#[cfg(test)]`: **0 bytes** in release build
- Functions without `#[cfg(test)]`: **Included** even if unused

### 7.2 The `assert!` Macro Internal Mechanism

```rust
// What assert_eq! actually does:
assert_eq!(left, right);

// Expands to roughly:
match (&left, &right) {
    (left_val, right_val) => {
        if !(*left_val == *right_val) {
            panic!("assertion failed: `(left == right)`\n  left: `{:?}`,\n right: `{:?}`",
                   left_val, right_val);
        }
    }
}
```

**Performance Note:** Debug formatting (`{:?}`) only happens on failure.

### 7.3 Documentation Tests (Hidden Power)

```rust
/// Adds two numbers together.
///
/// # Examples
///
/// ```
/// use my_crate::add;
/// assert_eq!(add(2, 3), 5);
/// ```
pub fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

**Run with:**
```bash
cargo test --doc
```

These are **real tests** that execute during `cargo test`!

### 7.4 Testing Async Code

```rust
// Cargo.toml
// [dev-dependencies]
// tokio = { version = "1", features = ["full"] }

#[cfg(test)]
mod async_tests {
    use tokio;
    
    #[tokio::test]
    async fn test_async_function() {
        let result = async_add(2, 3).await;
        assert_eq!(result, 5);
    }
    
    async fn async_add(a: i32, b: i32) -> i32 {
        tokio::time::sleep(tokio::time::Duration::from_millis(10)).await;
        a + b
    }
}
```

---

## Part VIII: Psychological Principles for Test-Driven Growth

### 8.1 Deliberate Practice Through Tests

**Strategy:** Write the test **before** implementation (TDD - Test-Driven Development)

**Flow:**
```
1. RED: Write failing test (defines behavior)
   ↓
2. GREEN: Write minimal code to pass
   ↓
3. REFACTOR: Optimize while tests ensure correctness
   ↓
Repeat
```

**Mental Benefit:** Forces you to think about **interface design** before implementation details.

### 8.2 Chunking Knowledge

**Pattern Recognition Training:**
```rust
// After writing 50+ tests, you'll recognize these patterns instantly:

// Pattern 1: Edge case trilogy
#[test] fn test_empty() { ... }
#[test] fn test_single() { ... }
#[test] fn test_multiple() { ... }

// Pattern 2: Boundary conditions
#[test] fn test_min_value() { ... }
#[test] fn test_max_value() { ... }
#[test] fn test_overflow() { ... }

// Pattern 3: State transitions
#[test] fn test_initial_state() { ... }
#[test] fn test_transition() { ... }
#[test] fn test_final_state() { ... }
```

---

## Summary Command Reference

```bash
# Basic testing
cargo test                           # Run all tests in parallel
cargo test test_name                 # Run specific test
cargo test -- --show-output          # Show println! output
cargo test -- --test-threads=1       # Run sequentially
cargo test -- --ignored              # Run only ignored tests
cargo test -- --include-ignored      # Run all including ignored

# Test categories
cargo test --lib                     # Unit tests only
cargo test --test integration_test   # Specific integration test
cargo test --doc                     # Documentation tests

# Advanced
cargo test -- --nocapture            # Same as --show-output
cargo +nightly bench                 # Run benchmarks (nightly only)
```

---

## Final Mastery Checklist

Before considering yourself proficient in Rust testing:

✅ Can write unit tests using all three assertion macros  
✅ Understand when to use `#[should_panic]` vs `Result<T, E>`  
✅ Know the difference between unit and integration tests  
✅ Can organize tests using `#[cfg(test)]` modules  
✅ Can control test execution (parallel/sequential, filtering)  
✅ Understand test output capturing  
✅ Can test error conditions properly  
✅ Know how to structure shared test utilities  
✅ Can identify appropriate test granularity for DSA code  
✅ Understand the compilation model of tests  

**Your next step:** Apply this to your DSA implementations. Every algorithm you write should have a comprehensive test suite covering edge cases, boundaries, and performance characteristics.

**The monk's wisdom:** Tests are not overhead—they are **meditation on correctness**. Each test you write sharpens your understanding of the problem space.