# Call by Value vs Call by Reference: Complete Implementations in Python and Rust

I'll create a comprehensive guide covering call by value and call by reference with complete implementations in both Python and Rust.I've created a comprehensive guide covering call by value and call by reference with complete implementations in both Python and Rust. The guide includes:

## Key Features:

1. **Fundamental Concepts** - Clear explanations of both paradigms
2. **Complete Python Implementation**:
   - Call by value with immutable objects (int, string, tuple)
   - Call by reference with mutable objects (list, dict, set)
   - Advanced examples with nested structures
   - Performance comparisons

3. **Complete Rust Implementation**:
   - Call by value with Copy trait and move semantics
   - Call by reference with borrowing (immutable and mutable)
   - Advanced ownership and borrowing examples
   - Performance comparisons

4. **Comparative Analysis** - Side-by-side comparison of both languages
5. **Performance Considerations** - When to use each approach
6. **Best Practices** - Practical guidelines for both languages

## Key Insights:

- **Python** uses "call by object reference" - behavior depends on mutability
- **Rust** provides explicit control through ownership and borrowing
- **Performance** varies significantly based on data size and usage patterns
- **Safety** vs **Performance** trade-offs differ between languages

The implementations include working code examples you can run to see the concepts in action, complete with detailed explanations and output demonstrations. This should give you a solid foundation for understanding and applying these concepts in both languages.

## Complete Guide: Call by Value vs Call by Reference in Python and Rust

## Table of Contents

1. [Fundamental Concepts](#fundamental-concepts)
2. [Python Implementation](#python-implementation)
3. [Rust Implementation](#rust-implementation)
4. [Comparative Analysis](#comparative-analysis)
5. [Performance Considerations](#performance-considerations)
6. [Best Practices](#best-practices)

---

## Fundamental Concepts

### Call by Value

In call by value, a **copy** of the actual parameter's value is passed to the function. Changes made to the parameter inside the function do not affect the original variable.

**Characteristics:**

- Function receives a copy of the data
- Original data remains unchanged
- Safe from unintended modifications
- Higher memory usage for large data structures
- Generally slower for large objects due to copying overhead

### Call by Reference

In call by reference, the **memory address** of the actual parameter is passed to the function. Changes made to the parameter inside the function directly affect the original variable.

**Characteristics:**

- Function receives a reference/pointer to the original data
- Original data can be modified
- More memory efficient
- Faster for large data structures
- Risk of unintended side effects

---

## Python Implementation

Python uses a unique approach called "call by object reference" or "call by sharing". The behavior depends on whether the object is mutable or immutable.

### Call by Value Behavior (Immutable Objects)

```python
def call_by_value_demo():
    """Demonstrates call by value with immutable objects"""
    
    def modify_integer(x):
        print(f"Inside function - before modification: x = {x}, id = {id(x)}")
        x = x + 10  # Creates a new integer object
        print(f"Inside function - after modification: x = {x}, id = {id(x)}")
        return x
    
    def modify_string(s):
        print(f"Inside function - before modification: s = '{s}', id = {id(s)}")
        s = s + " World"  # Creates a new string object
        print(f"Inside function - after modification: s = '{s}', id = {id(s)}")
        return s
    
    def modify_tuple(t):
        print(f"Inside function - before modification: t = {t}, id = {id(t)}")
        t = t + (4, 5)  # Creates a new tuple object
        print(f"Inside function - after modification: t = {t}, id = {id(t)}")
        return t
    
    # Integer example
    print("=== INTEGER EXAMPLE ===")
    original_int = 5
    print(f"Original: {original_int}, id = {id(original_int)}")
    
    result_int = modify_integer(original_int)
    print(f"After function call: original = {original_int}, result = {result_int}")
    print(f"Original unchanged: {original_int == 5}")
    print()
    
    # String example
    print("=== STRING EXAMPLE ===")
    original_string = "Hello"
    print(f"Original: '{original_string}', id = {id(original_string)}")
    
    result_string = modify_string(original_string)
    print(f"After function call: original = '{original_string}', result = '{result_string}'")
    print(f"Original unchanged: {original_string == 'Hello'}")
    print()
    
    # Tuple example
    print("=== TUPLE EXAMPLE ===")
    original_tuple = (1, 2, 3)
    print(f"Original: {original_tuple}, id = {id(original_tuple)}")
    
    result_tuple = modify_tuple(original_tuple)
    print(f"After function call: original = {original_tuple}, result = {result_tuple}")
    print(f"Original unchanged: {original_tuple == (1, 2, 3)}")

### Call by Reference Behavior (Mutable Objects)

def call_by_reference_demo():
    """Demonstrates call by reference with mutable objects"""
    
    def modify_list(lst):
        print(f"Inside function - before modification: lst = {lst}, id = {id(lst)}")
        lst.append(4)  # Modifies the original list object
        lst[0] = 99    # Modifies the original list object
        print(f"Inside function - after modification: lst = {lst}, id = {id(lst)}")
        return lst
    
    def modify_dict(d):
        print(f"Inside function - before modification: d = {d}, id = {id(d)}")
        d['new_key'] = 'new_value'  # Modifies the original dict object
        d['a'] = 100               # Modifies the original dict object
        print(f"Inside function - after modification: d = {d}, id = {id(d)}")
        return d
    
    def modify_set(s):
        print(f"Inside function - before modification: s = {s}, id = {id(s)}")
        s.add(4)      # Modifies the original set object
        s.discard(1)  # Modifies the original set object
        print(f"Inside function - after modification: s = {s}, id = {id(s)}")
        return s
    
    # List example
    print("=== LIST EXAMPLE ===")
    original_list = [1, 2, 3]
    print(f"Original: {original_list}, id = {id(original_list)}")
    
    result_list = modify_list(original_list)
    print(f"After function call: original = {original_list}, result = {result_list}")
    print(f"Original modified: {original_list != [1, 2, 3]}")
    print(f"Same object: {original_list is result_list}")
    print()
    
    # Dictionary example
    print("=== DICTIONARY EXAMPLE ===")
    original_dict = {'a': 1, 'b': 2}
    print(f"Original: {original_dict}, id = {id(original_dict)}")
    
    result_dict = modify_dict(original_dict)
    print(f"After function call: original = {original_dict}, result = {result_dict}")
    print(f"Original modified: {original_dict != {'a': 1, 'b': 2}}")
    print(f"Same object: {original_dict is result_dict}")
    print()
    
    # Set example
    print("=== SET EXAMPLE ===")
    original_set = {1, 2, 3}
    print(f"Original: {original_set}, id = {id(original_set)}")
    
    result_set = modify_set(original_set)
    print(f"After function call: original = {original_set}, result = {result_set}")
    print(f"Original modified: {original_set != {1, 2, 3}}")
    print(f"Same object: {original_set is result_set}")

### Advanced Python Examples

def advanced_python_examples():
    """Advanced examples showing edge cases and practical applications"""
    
    def swap_values_attempt(a, b):
        """Attempt to swap values - doesn't work with immutables"""
        print(f"Inside swap: before - a={a}, b={b}")
        a, b = b, a
        print(f"Inside swap: after - a={a}, b={b}")
    
    def swap_list_elements(lst, i, j):
        """Swap elements in a list - works because list is mutable"""
        print(f"Before swap: {lst}")
        lst[i], lst[j] = lst[j], lst[i]
        print(f"After swap: {lst}")
    
    def modify_nested_structure(data):
        """Modifying nested mutable structures"""
        print(f"Before: {data}")
        data['list'].append('new_item')
        data['nested']['count'] += 1
        print(f"After: {data}")
    
    # Swap attempt with immutables
    print("=== SWAP ATTEMPT WITH IMMUTABLES ===")
    x, y = 10, 20
    print(f"Before function: x={x}, y={y}")
    swap_values_attempt(x, y)
    print(f"After function: x={x}, y={y}")  # Unchanged
    print()
    
    # Swap with mutable list
    print("=== SWAP WITH MUTABLE LIST ===")
    numbers = [1, 2, 3, 4, 5]
    swap_list_elements(numbers, 0, 4)
    print(f"Final list: {numbers}")
    print()
    
    # Nested structure modification
    print("=== NESTED STRUCTURE MODIFICATION ===")
    complex_data = {
        'list': [1, 2, 3],
        'nested': {'count': 0, 'name': 'test'}
    }
    print(f"Original: {complex_data}")
    modify_nested_structure(complex_data)
    print(f"Final: {complex_data}")

### Performance Comparison

def performance_comparison():
    """Compare performance of call by value vs reference"""
    import time
    import copy
    
    def process_large_list_by_reference(lst):
        """Process list by reference (direct modification)"""
        for i in range(len(lst)):
            lst[i] = lst[i] * 2
    
    def process_large_list_by_value(lst):
        """Simulate call by value by making a copy"""
        lst_copy = copy.deepcopy(lst)
        for i in range(len(lst_copy)):
            lst_copy[i] = lst_copy[i] * 2
        return lst_copy
    
    # Create a large list
    large_list = list(range(100000))
    
    # Test reference-style (in-place modification)
    start_time = time.time()
    process_large_list_by_reference(large_list.copy())
    ref_time = time.time() - start_time
    
    # Test value-style (with copying)
    start_time = time.time()
    process_large_list_by_value(large_list)
    val_time = time.time() - start_time
    
    print(f"Reference-style processing: {ref_time:.4f} seconds")
    print(f"Value-style processing: {val_time:.4f} seconds")
    print(f"Reference is {val_time/ref_time:.1f}x faster")

# Run all Python examples
if __name__ == "__main__":
    print("PYTHON CALL BY VALUE AND REFERENCE EXAMPLES")
    print("=" * 50)
    
    call_by_value_demo()
    print("\n" + "=" * 50 + "\n")
    
    call_by_reference_demo()
    print("\n" + "=" * 50 + "\n")
    
    advanced_python_examples()
    print("\n" + "=" * 50 + "\n")
    
    performance_comparison()
```

---

## Rust Implementation

Rust provides explicit control over ownership, borrowing, and references, making the distinction between call by value and call by reference very clear.

### Call by Value in Rust

```rust
#[derive(Debug, Clone)]
struct Person {
    name: String,
    age: u32,
}

fn call_by_value_examples() {
    println!("RUST CALL BY VALUE EXAMPLES");
    println!("{}", "=".repeat(40));
    
    // Primitive types (Copy trait)
    fn modify_integer(mut x: i32) -> i32 {
        println!("Inside function - before: x = {}", x);
        x += 10;
        println!("Inside function - after: x = {}", x);
        x
    }
    
    fn modify_float(mut x: f64) -> f64 {
        println!("Inside function - before: x = {}", x);
        x *= 2.0;
        println!("Inside function - after: x = {}", x);
        x
    }
    
    // String and Vec (Move semantics - ownership transferred)
    fn modify_string(mut s: String) -> String {
        println!("Inside function - before: s = '{}'", s);
        s.push_str(" World");
        println!("Inside function - after: s = '{}'", s);
        s
    }
    
    fn modify_vector(mut v: Vec<i32>) -> Vec<i32> {
        println!("Inside function - before: v = {:?}", v);
        v.push(4);
        v[0] = 99;
        println!("Inside function - after: v = {:?}", v);
        v
    }
    
    // Struct with Clone
    fn modify_person(mut p: Person) -> Person {
        println!("Inside function - before: p = {:?}", p);
        p.age += 1;
        p.name.push_str(" Jr.");
        println!("Inside function - after: p = {:?}", p);
        p
    }
    
    // Integer example (Copy trait)
    println!("=== INTEGER EXAMPLE (Copy) ===");
    let original_int = 5;
    println!("Original: {}", original_int);
    
    let result_int = modify_integer(original_int);
    println!("After function: original = {}, result = {}", original_int, result_int);
    println!("Original unchanged: {}", original_int == 5);
    println!();
    
    // Float example (Copy trait)
    println!("=== FLOAT EXAMPLE (Copy) ===");
    let original_float = 3.14;
    println!("Original: {}", original_float);
    
    let result_float = modify_float(original_float);
    println!("After function: original = {}, result = {}", original_float, result_float);
    println!();
    
    // String example (Move semantics)
    println!("=== STRING EXAMPLE (Move) ===");
    let original_string = String::from("Hello");
    println!("Original: '{}'", original_string);
    
    // Note: original_string is moved here, can't use it afterwards
    let result_string = modify_string(original_string);
    // println!("Original: {}", original_string); // This would cause a compile error!
    println!("Result: '{}'", result_string);
    println!();
    
    // Vector example (Move semantics)
    println!("=== VECTOR EXAMPLE (Move) ===");
    let original_vec = vec![1, 2, 3];
    println!("Original: {:?}", original_vec);
    
    let result_vec = modify_vector(original_vec);
    println!("Result: {:?}", result_vec);
    println!();
    
    // Struct example with Clone
    println!("=== STRUCT EXAMPLE (Clone) ===");
    let original_person = Person {
        name: String::from("Alice"),
        age: 30,
    };
    println!("Original: {:?}", original_person);
    
    // Clone to keep original
    let result_person = modify_person(original_person.clone());
    println!("After function: original = {:?}, result = {:?}", original_person, result_person);
}

### Call by Reference in Rust

fn call_by_reference_examples() {
    println!("RUST CALL BY REFERENCE EXAMPLES");
    println!("{}", "=".repeat(40));
    
    // Immutable references
    fn read_string(s: &String) {
        println!("Inside function - reading string: '{}'", s);
        println!("String length: {}", s.len());
        // s.push_str(" World"); // This would cause a compile error!
    }
    
    fn read_vector(v: &Vec<i32>) -> i32 {
        println!("Inside function - reading vector: {:?}", v);
        v.iter().sum()
    }
    
    // Mutable references
    fn modify_string_ref(s: &mut String) {
        println!("Inside function - before: '{}'", s);
        s.push_str(" World");
        println!("Inside function - after: '{}'", s);
    }
    
    fn modify_vector_ref(v: &mut Vec<i32>) {
        println!("Inside function - before: {:?}", v);
        v.push(4);
        if !v.is_empty() {
            v[0] = 99;
        }
        println!("Inside function - after: {:?}", v);
    }
    
    fn modify_person_ref(p: &mut Person) {
        println!("Inside function - before: {:?}", p);
        p.age += 1;
        p.name.push_str(" Jr.");
        println!("Inside function - after: {:?}", p);
    }
    
    // Multiple references
    fn compare_strings(s1: &String, s2: &String) -> bool {
        println!("Comparing '{}' and '{}'", s1, s2);
        s1 == s2
    }
    
    // Immutable reference examples
    println!("=== IMMUTABLE REFERENCE EXAMPLES ===");
    let my_string = String::from("Hello Rust");
    println!("Before function: '{}'", my_string);
    
    read_string(&my_string);
    println!("After function: '{}'", my_string); // Unchanged and still accessible
    println!();
    
    let my_vector = vec![1, 2, 3, 4, 5];
    println!("Before function: {:?}", my_vector);
    
    let sum = read_vector(&my_vector);
    println!("After function: {:?}, sum: {}", my_vector, sum);
    println!();
    
    // Mutable reference examples
    println!("=== MUTABLE REFERENCE EXAMPLES ===");
    let mut mutable_string = String::from("Hello");
    println!("Before function: '{}'", mutable_string);
    
    modify_string_ref(&mut mutable_string);
    println!("After function: '{}'", mutable_string); // Modified!
    println!();
    
    let mut mutable_vector = vec![1, 2, 3];
    println!("Before function: {:?}", mutable_vector);
    
    modify_vector_ref(&mut mutable_vector);
    println!("After function: {:?}", mutable_vector); // Modified!
    println!();
    
    let mut mutable_person = Person {
        name: String::from("Bob"),
        age: 25,
    };
    println!("Before function: {:?}", mutable_person);
    
    modify_person_ref(&mut mutable_person);
    println!("After function: {:?}", mutable_person); // Modified!
    println!();
    
    // Multiple references
    println!("=== MULTIPLE REFERENCES ===");
    let str1 = String::from("Hello");
    let str2 = String::from("World");
    
    let are_equal = compare_strings(&str1, &str2);
    println!("Strings equal: {}", are_equal);
    println!("Both strings still accessible: '{}' and '{}'", str1, str2);
}

### Advanced Rust Examples

fn advanced_rust_examples() {
    println!("ADVANCED RUST EXAMPLES");
    println!("{}", "=".repeat(40));
    
    // Function that takes ownership and returns it
    fn process_and_return(mut data: Vec<i32>) -> Vec<i32> {
        data.iter_mut().for_each(|x| *x *= 2);
        data
    }
    
    // Function that borrows and modifies
    fn process_in_place(data: &mut Vec<i32>) {
        data.iter_mut().for_each(|x| *x *= 2);
    }
    
    // Function demonstrating borrowing rules
    fn borrowing_rules_demo() {
        let mut data = vec![1, 2, 3, 4, 5];
        println!("Original data: {:?}", data);
        
        // Multiple immutable borrows are allowed
        let ref1 = &data;
        let ref2 = &data;
        println!("ref1: {:?}, ref2: {:?}", ref1, ref2);
        
        // Mutable borrow (exclusive)
        {
            let mut_ref = &mut data;
            mut_ref.push(6);
            println!("After mutable borrow: {:?}", mut_ref);
        } // mut_ref goes out of scope here
        
        // Can create immutable borrows again
        println!("Final data: {:?}", data);
    }
    
    // Slice parameters (flexible borrowing)
    fn process_slice(slice: &[i32]) -> i32 {
        slice.iter().sum()
    }
    
    fn modify_slice(slice: &mut [i32]) {
        for item in slice.iter_mut() {
            *item *= 2;
        }
    }
    
    // Ownership transfer vs borrowing
    println!("=== OWNERSHIP TRANSFER VS BORROWING ===");
    let mut original = vec![1, 2, 3, 4, 5];
    println!("Original: {:?}", original);
    
    // Method 1: Transfer ownership and get it back
    let processed = process_and_return(original);
    // original is no longer valid here
    println!("After process_and_return: {:?}", processed);
    
    // Method 2: Borrow mutably
    let mut original2 = vec![1, 2, 3, 4, 5];
    println!("Original2 before: {:?}", original2);
    
    process_in_place(&mut original2);
    println!("Original2 after process_in_place: {:?}", original2);
    println!();
    
    // Borrowing rules demonstration
    println!("=== BORROWING RULES ===");
    borrowing_rules_demo();
    println!();
    
    // Slice examples
    println!("=== SLICE EXAMPLES ===");
    let mut array = [1, 2, 3, 4, 5];
    let vector = vec![6, 7, 8, 9, 10];
    
    // Works with both arrays and vectors
    println!("Array sum: {}", process_slice(&array));
    println!("Vector sum: {}", process_slice(&vector));
    
    modify_slice(&mut array);
    println!("Array after modification: {:?}", array);
}

### Performance Comparison

fn performance_comparison() {
    use std::time::Instant;
    
    #[derive(Debug, Clone)]
    struct LargeStruct {
        data: Vec<i32>,
        name: String,
        id: u64,
    }
    
    impl LargeStruct {
        fn new(size: usize) -> Self {
            LargeStruct {
                data: (0..size).collect(),
                name: "Large Struct".repeat(100),
                id: 12345,
            }
        }
    }
    
    fn process_by_value(mut s: LargeStruct) -> LargeStruct {
        s.data.iter_mut().for_each(|x| *x *= 2);
        s.id += 1;
        s
    }
    
    fn process_by_reference(s: &mut LargeStruct) {
        s.data.iter_mut().for_each(|x| *x *= 2);
        s.id += 1;
    }
    
    println!("PERFORMANCE COMPARISON");
    println!("{}", "=".repeat(40));
    
    const SIZE: usize = 100_000;
    let large_struct = LargeStruct::new(SIZE);
    
    // Test by value (with move)
    let start = Instant::now();
    let _result = process_by_value(large_struct.clone());
    let by_value_time = start.elapsed();
    
    // Test by reference
    let mut large_struct_copy = large_struct.clone();
    let start = Instant::now();
    process_by_reference(&mut large_struct_copy);
    let by_reference_time = start.elapsed();
    
    println!("By value (with clone): {:?}", by_value_time);
    println!("By reference: {:?}", by_reference_time);
    println!("Reference is {:.1}x faster", 
             by_value_time.as_nanos() as f64 / by_reference_time.as_nanos() as f64);
}

// Main function to run all examples
fn main() {
    call_by_value_examples();
    println!("\n{}\n", "=".repeat(50));
    
    call_by_reference_examples();
    println!("\n{}\n", "=".repeat(50));
    
    advanced_rust_examples();
    println!("\n{}\n", "=".repeat(50));
    
    performance_comparison();
}
```

---

## Comparative Analysis

### Key Differences

| Aspect | Python | Rust |
|--------|--------|------|
| **Default Behavior** | Call by object reference | Explicit ownership/borrowing |
| **Mutability** | Object-dependent | Explicitly controlled |
| **Memory Safety** | Garbage collected | Compile-time guaranteed |
| **Performance** | Runtime overhead | Zero-cost abstractions |
| **Flexibility** | Dynamic, runtime checks | Static, compile-time checks |

### Python Characteristics

- **Implicit behavior**: Depends on object mutability
- **Runtime flexibility**: Can modify behavior dynamically
- **Memory managed**: Garbage collector handles cleanup
- **Potential pitfalls**: Unexpected mutations with mutable objects

### Rust Characteristics

- **Explicit control**: Clear ownership and borrowing rules
- **Compile-time safety**: Prevents data races and memory issues
- **Performance optimized**: Zero-cost abstractions
- **Learning curve**: More complex syntax but safer code

---

## Performance Considerations

### When to Use Call by Value

1. **Small data structures** (primitives, small structs)
2. **Immutable operations** where original data shouldn't change
3. **Thread safety** requirements
4. **Functional programming** paradigms

### When to Use Call by Reference

1. **Large data structures** to avoid copying overhead
2. **In-place modifications** for efficiency
3. **Shared data** across multiple functions
4. **Resource constraints** (memory or performance)

### Memory Usage Comparison

```
Call by Value:
- Memory usage: O(size of data)
- Time complexity: O(size of data) for copying
- Safety: High (no side effects)

Call by Reference:
- Memory usage: O(1) - only reference/pointer
- Time complexity: O(1) for parameter passing
- Safety: Lower (potential side effects)
```

---

## Best Practices

### Python Best Practices

1. **Understand mutability**: Know which objects are mutable/immutable
2. **Use copying when needed**: `copy.copy()` or `copy.deepcopy()`
3. **Document side effects**: Clear function documentation about mutations
4. **Prefer immutable**: Use immutable objects when possible
5. **Defensive programming**: Make copies to prevent accidental mutations

```python
# Good: Clear about mutations
def modify_list_safely(lst: List[int]) -> List[int]:
    """Returns a modified copy, leaving original unchanged."""
    return lst.copy() + [42]

# Good: Clear about in-place modification
def modify_list_inplace(lst: List[int]) -> None:
    """Modifies the list in-place."""
    lst.append(42)
```

### Rust Best Practices

1. **Prefer borrowing**: Use references when ownership transfer isn't needed
2. **Use slices**: More flexible than concrete types (`&[T]` vs `&Vec<T>`)
3. **Minimize cloning**: Only clone when necessary
4. **Understand lifetimes**: Ensure references remain valid
5. **Leverage the type system**: Let the compiler catch errors

```rust
// Good: Flexible with slices
fn process_numbers(nums: &[i32]) -> i32 {
    nums.iter().sum()
}

// Good: Clear ownership semantics
fn take_ownership(data: Vec<i32>) -> Vec<i32> {
    // Process and return
    data
}

// Good: Borrow when possible
fn read_data(data: &Vec<i32>) -> usize {
    data.len()
}
```

### General Guidelines

1. **Choose based on use case**: Value for safety, reference for performance
2. **Consider data size**: Large objects benefit from references
3. **Think about ownership**: Who should own the data?
4. **Document behavior**: Make calling conventions clear
5. **Profile when needed**: Measure performance impact of different approaches

This guide provides a comprehensive foundation for understanding and implementing call by value and call by reference patterns in both Python and Rust, helping you make informed decisions based on your specific requirements.

I'll create a detailed ASCII diagram showing how Call by Value and Call by Reference work step by step.I've created a comprehensive ASCII diagram that shows exactly how Call by Value and Call by Reference work step by step. The diagram illustrates:

**Call by Value:**

- Shows how copies of the original values are made
- Demonstrates that modifications inside the function don't affect the original variables
- Shows the memory layout with separate storage for the copies

**Call by Reference:**

- Shows how memory addresses (pointers) are passed instead of values
- Demonstrates direct access to the original memory locations
- Shows how changes inside the function directly modify the original variables

The key insight is that Call by Value creates a "firewall" between the function and the original data by working with copies, while Call by Reference creates a direct connection by sharing memory addresses. This is why swapping fails with Call by Value but succeeds with Call by Reference.

The diagram also includes memory addresses (like 0x1000, 0x1004) to make it clear how pointers reference specific memory locations, and uses arrows to show the flow of data and access patterns.

## Call by Value vs Call by Reference - Step by Step Diagram

### Call by Value

```
STEP 1: Initial Setup
┌─────────────────────┐    ┌─────────────────────┐
│     Main Function   │    │   Function swap()   │
│                     │    │                     │
│  int a = 10;        │    │  void swap(int x,   │
│  int b = 20;        │    │            int y) { │
│                     │    │    int temp = x;    │
│  Memory:            │    │    x = y;           │
│  ┌─────┬─────┐     │    │    y = temp;        │
│  │  a  │ 10  │     │    │  }                  │
│  ├─────┼─────┤     │    │                     │
│  │  b  │ 20  │     │    │                     │
│  └─────┴─────┘     │    │                     │
└─────────────────────┘    └─────────────────────┘

STEP 2: Function Call - swap(a, b)
┌─────────────────────┐    ┌─────────────────────┐
│     Main Function   │    │   Function swap()   │
│                     │    │                     │
│  int a = 10;        │    │  Parameters:        │
│  int b = 20;        │    │  ┌─────┬─────┐     │
│                     │    │  │  x  │ 10  │◄────┼──── COPY of 'a'
│  swap(a, b);        │    │  ├─────┼─────┤     │
│                     │    │  │  y  │ 20  │◄────┼──── COPY of 'b'
│  Memory:            │    │  └─────┴─────┘     │
│  ┌─────┬─────┐     │    │                     │
│  │  a  │ 10  │     │    │  Local variable:    │
│  ├─────┼─────┤     │    │  ┌──────┬─────┐    │
│  │  b  │ 20  │     │    │  │ temp │  ?  │    │
│  └─────┴─────┘     │    │  └──────┴─────┘    │
└─────────────────────┘    └─────────────────────┘

STEP 3: Execute swap() - temp = x
┌─────────────────────┐    ┌─────────────────────┐
│     Main Function   │    │   Function swap()   │
│                     │    │                     │
│  int a = 10;        │    │  Parameters:        │
│  int b = 20;        │    │  ┌─────┬─────┐     │
│                     │    │  │  x  │ 10  │     │
│  swap(a, b);        │    │  ├─────┼─────┤     │
│                     │    │  │  y  │ 20  │     │
│  Memory:            │    │  └─────┴─────┘     │
│  ┌─────┬─────┐     │    │                     │
│  │  a  │ 10  │     │    │  Local variable:    │
│  ├─────┼─────┤     │    │  ┌──────┬─────┐    │
│  │  b  │ 20  │     │    │  │ temp │ 10  │    │
│  └─────┴─────┘     │    │  └──────┴─────┘    │
└─────────────────────┘    └─────────────────────┘

STEP 4: Execute swap() - x = y
┌─────────────────────┐    ┌─────────────────────┐
│     Main Function   │    │   Function swap()   │
│                     │    │                     │
│  int a = 10;        │    │  Parameters:        │
│  int b = 20;        │    │  ┌─────┬─────┐     │
│                     │    │  │  x  │ 20  │     │
│  swap(a, b);        │    │  ├─────┼─────┤     │
│                     │    │  │  y  │ 20  │     │
│  Memory:            │    │  └─────┴─────┘     │
│  ┌─────┬─────┐     │    │                     │
│  │  a  │ 10  │     │    │  Local variable:    │
│  ├─────┼─────┤     │    │  ┌──────┬─────┐    │
│  │  b  │ 20  │     │    │  │ temp │ 10  │    │
│  └─────┴─────┘     │    │  └──────┴─────┘    │
└─────────────────────┘    └─────────────────────┘

STEP 5: Execute swap() - y = temp
┌─────────────────────┐    ┌─────────────────────┐
│     Main Function   │    │   Function swap()   │
│                     │    │                     │
│  int a = 10;        │    │  Parameters:        │
│  int b = 20;        │    │  ┌─────┬─────┐     │
│                     │    │  │  x  │ 20  │     │
│  swap(a, b);        │    │  ├─────┼─────┤     │
│                     │    │  │  y  │ 10  │     │
│  Memory:            │    │  └─────┴─────┘     │
│  ┌─────┬─────┐     │    │                     │
│  │  a  │ 10  │     │    │  Local variable:    │
│  ├─────┼─────┤     │    │  ┌──────┬─────┐    │
│  │  b  │ 20  │     │    │  │ temp │ 10  │    │
│  └─────┴─────┘     │    │  └──────┴─────┘    │
└─────────────────────┘    └─────────────────────┘

STEP 6: Function Returns - Original values UNCHANGED
┌─────────────────────┐    
│     Main Function   │    
│                     │    
│  int a = 10;        │ ◄── Still 10!
│  int b = 20;        │ ◄── Still 20!
│                     │    
│  After swap(a, b);  │    
│                     │    
│  Memory:            │    
│  ┌─────┬─────┐     │    
│  │  a  │ 10  │     │    
│  ├─────┼─────┤     │    
│  │  b  │ 20  │     │    
│  └─────┴─────┘     │    
└─────────────────────┘    
```

---

## Call by Reference

```
STEP 1: Initial Setup
┌─────────────────────┐    ┌─────────────────────┐
│     Main Function   │    │   Function swap()   │
│                     │    │                     │
│  int a = 10;        │    │  void swap(int* x,  │
│  int b = 20;        │    │            int* y) {│
│                     │    │    int temp = *x;   │
│  Memory:            │    │    *x = *y;         │
│  Address: 0x1000    │    │    *y = temp;       │
│  ┌─────┬─────┐     │    │  }                  │
│  │  a  │ 10  │     │    │                     │
│  ├─────┼─────┤     │    │                     │
│  │  b  │ 20  │     │    │                     │
│  └─────┴─────┘     │    │                     │
│  Address: 0x1004    │    │                     │
└─────────────────────┘    └─────────────────────┘

STEP 2: Function Call - swap(&a, &b)
┌─────────────────────┐    ┌─────────────────────┐
│     Main Function   │    │   Function swap()   │
│                     │    │                     │
│  int a = 10;        │    │  Parameters:        │
│  int b = 20;        │    │  ┌─────┬────────┐  │
│                     │    │  │  x  │ 0x1000 │──┼─┐
│  swap(&a, &b);      │    │  ├─────┼────────┤  │ │
│                     │    │  │  y  │ 0x1004 │──┼─┼─┐
│  Memory:            │    │  └─────┴────────┘  │ │ │
│  Address: 0x1000    │    │                     │ │ │
│  ┌─────┬─────┐     │ ◄──┼─────────────────────┘ │ │
│  │  a  │ 10  │     │    │                       │ │
│  ├─────┼─────┤     │ ◄──┼───────────────────────┘ │
│  │  b  │ 20  │     │    │                         │
│  └─────┴─────┘     │    │  Local variable:        │
│  Address: 0x1004    │    │  ┌──────┬─────┐        │
└─────────────────────┘    │  │ temp │  ?  │        │
                           │  └──────┴─────┘        │
                           └─────────────────────────┘

STEP 3: Execute swap() - temp = *x
┌─────────────────────┐    ┌─────────────────────┐
│     Main Function   │    │   Function swap()   │
│                     │    │                     │
│  int a = 10;        │    │  Parameters:        │
│  int b = 20;        │    │  ┌─────┬────────┐  │
│                     │    │  │  x  │ 0x1000 │──┼─┐
│  swap(&a, &b);      │    │  ├─────┼────────┤  │ │
│                     │    │  │  y  │ 0x1004 │──┼─┼─┐
│  Memory:            │    │  └─────┴────────┘  │ │ │
│  Address: 0x1000    │    │                     │ │ │
│  ┌─────┬─────┐     │ ◄──┼─────────────────────┘ │ │
│  │  a  │ 10  │ ────┼────┼───READ VALUE (10)     │ │
│  ├─────┼─────┤     │ ◄──┼───────────────────────┘ │
│  │  b  │ 20  │     │    │                         │
│  └─────┴─────┘     │    │  Local variable:        │
│  Address: 0x1004    │    │  ┌──────┬─────┐        │
└─────────────────────┘    │  │ temp │ 10  │        │
                           │  └──────┴─────┘        │
                           └─────────────────────────┘

STEP 4: Execute swap() - *x = *y
┌─────────────────────┐    ┌─────────────────────┐
│     Main Function   │    │   Function swap()   │
│                     │    │                     │
│  int a = 20; ◄──────┼────┼── CHANGED!         │
│  int b = 20;        │    │                     │
│                     │    │  Parameters:        │
│  swap(&a, &b);      │    │  ┌─────┬────────┐  │
│                     │    │  │  x  │ 0x1000 │──┼─┐
│  Memory:            │    │  ├─────┼────────┤  │ │
│  Address: 0x1000    │    │  │  y  │ 0x1004 │──┼─┼─┐
│  ┌─────┬─────┐     │ ◄──┼─ └─────┴────────┘  │ │ │
│  │  a  │ 20  │ ◄───┼────┼──WRITE VALUE (20)   │ │ │
│  ├─────┼─────┤     │ ◄──┼─────────────────────┘ │ │
│  │  b  │ 20  │ ────┼────┼───READ VALUE (20) ────┘ │
│  └─────┴─────┘     │    │                         │
│  Address: 0x1004    │    │  Local variable:        │
└─────────────────────┘    │  ┌──────┬─────┐        │
                           │  │ temp │ 10  │        │
                           │  └──────┴─────┘        │
                           └─────────────────────────┘

STEP 5: Execute swap() - *y = temp
┌─────────────────────┐    ┌─────────────────────┐
│     Main Function   │    │   Function swap()   │
│                     │    │                     │
│  int a = 20;        │    │                     │
│  int b = 10; ◄──────┼────┼── CHANGED!         │
│                     │    │                     │
│  swap(&a, &b);      │    │  Parameters:        │
│                     │    │  ┌─────┬────────┐  │
│  Memory:            │    │  │  x  │ 0x1000 │──┼─┐
│  Address: 0x1000    │    │  ├─────┼────────┤  │ │
│  ┌─────┬─────┐     │ ◄──┼─ │  y  │ 0x1004 │──┼─┼─┐
│  │  a  │ 20  │     │    │  └─────┴────────┘  │ │ │
│  ├─────┼─────┤     │ ◄──┼─────────────────────┘ │ │
│  │  b  │ 10  │ ◄───┼────┼──WRITE VALUE (10) ────┘ │
│  └─────┴─────┘     │    │                         │
│  Address: 0x1004    │    │  Local variable:        │
└─────────────────────┘    │  ┌──────┬─────┐        │
                           │  │ temp │ 10  │ ───READ │
                           │  └──────┴─────┘        │
                           └─────────────────────────┘

STEP 6: Function Returns - Original values SWAPPED!
┌─────────────────────┐    
│     Main Function   │    
│                     │    
│  int a = 20; ◄──────┼── SUCCESSFULLY SWAPPED!
│  int b = 10; ◄──────┼── SUCCESSFULLY SWAPPED!
│                     │    
│  After swap(&a,&b); │    
│                     │    
│  Memory:            │    
│  Address: 0x1000    │    
│  ┌─────┬─────┐     │    
│  │  a  │ 20  │     │    
│  ├─────┼─────┤     │    
│  │  b  │ 10  │     │    
│  └─────┴─────┘     │    
│  Address: 0x1004    │    
└─────────────────────┘    
```

---

## Key Differences Summary

```
┌──────────────────────┬──────────────────────────────────────────────┐
│    CALL BY VALUE     │              CALL BY REFERENCE               │
├──────────────────────┼──────────────────────────────────────────────┤
│ • Copies VALUES      │ • Passes ADDRESSES (pointers)               │
│ • Original unchanged │ • Original variables can be modified        │
│ • More memory usage  │ • Less memory usage (just addresses)        │
│ • Safer (no side     │ • More powerful but requires care           │
│   effects)           │                                              │
│ • Used for: int,     │ • Used for: arrays, large structures,       │
│   char, float, etc.  │   when modification is needed                │
└──────────────────────┴──────────────────────────────────────────────┘

Memory Flow:
Call by Value:    main_var → [COPY] → function_param
Call by Reference: main_var ← [DIRECT ACCESS] ← function_param
```

This diagram shows how in Call by Value, the function works with copies and cannot affect the original variables, while in Call by Reference, the function works directly with the memory addresses of the original variables, allowing it to modify them.