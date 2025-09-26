# Understanding Macros: A Comprehensive Guide

A **macro** is a code generation tool that writes code for you at compile time. Think of it as a "code template" that expands into actual code before your program is compiled.

## Key Concepts:

**What macros do:**

- Take some input (code, tokens, or patterns)
- Generate new code based on that input
- This happens during compilation, not at runtime
- The generated code is then compiled normally

**Why use macros:**

- Reduce code duplication
- Generate repetitive code automatically
- Create domain-specific languages (DSLs)
- Perform compile-time computations
- Generate code that would be impossible or tedious to write by hand

## Types of Macros (using Rust examples):

**1. Declarative Macros (macro_rules!):**

```rust
// Define a macro
macro_rules! say_hello {
    () => {
        println!("Hello, World!");
    };
    ($name:expr) => {
        println!("Hello, {}!", $name);
    };
}

// Use the macro
say_hello!();           // Expands to: println!("Hello, World!"); see macro.rs file
say_hello!("Alice");    // Expands to: println!("Hello, Alice!");
```

**2. Built-in Macros:**

```rust
println!("Debug: {:?}", value);  // Generates formatted print code
vec![1, 2, 3];                  // Generates vector creation code
format!("Value: {}", x);        // Generates string formatting code
```

## Real-World Example:

Instead of writing:

```rust
let mut v = Vec::new();
v.push(1);
v.push(2);
v.push(3);
```

The `vec!` macro lets you write:

```rust
let v = vec![1, 2, 3];
```

The macro expands this into the longer form automatically.

## In Other Languages:

- **C/C++**: `#define` preprocessor macros
- **Lisp**: Powerful macro systems for code transformation
- **JavaScript**: Template literals and build-time transforms
- **Python**: Decorators (similar concept)
- **Java**: Annotation processors (compile-time code generation)

## Macro vs Function:

| Aspect | Macro | Function |
|--------|-------|----------|
| **When executed** | Compile time | Runtime |
| **Input** | Code/tokens | Values |
| **Output** | Generated code | Return value |
| **Type checking** | After expansion | Before call |
| **Performance** | Zero runtime cost | Function call overhead |

**Simple analogy:** A macro is like a "find and replace" operation in your text editor, but much more sophisticated - it can analyze the code you give it and generate completely different code based on patterns and rules you define.

Macros are particularly powerful in systems programming languages like Rust and C, where you want the flexibility of code generation without runtime overhead.

## Comprehensive Guide to Rust Macros

## Table of Contents

1. [Introduction to Macros](#introduction-to-macros)
2. [Types of Macros in Rust](#types-of-macros-in-rust)
3. [Declarative Macros (macro_rules!)](#declarative-macros-macro_rules)
4. [Procedural Macros](#procedural-macros)
5. [Common Macro Patterns](#common-macro-patterns)
6. [Advanced Techniques](#advanced-techniques)
7. [Best Practices](#best-practices)
8. [Debugging Macros](#debugging-macros)
9. [Real-World Examples](#real-world-examples)

## Introduction to Macros

Macros in Rust are a powerful metaprogramming feature that allows you to write code that writes other code. Unlike functions, macros operate at compile time and can generate code based on the input they receive. This makes them extremely powerful for reducing boilerplate, creating domain-specific languages, and implementing functionality that would be impossible with regular functions.

### Why Use Macros?

- **Code Generation**: Automatically generate repetitive code
- **Compile-time Computation**: Perform computations at compile time
- **Variadic Arguments**: Accept variable numbers of arguments
- **Pattern Matching on Code Structure**: Match against the structure of code itself
- **Zero-cost Abstractions**: Generate efficient code without runtime overhead

## Types of Macros in Rust

Rust has two main types of macros:

1. **Declarative Macros** (`macro_rules!`) - Pattern-based macros
2. **Procedural Macros** - Function-like macros that manipulate token streams

### Declarative vs Procedural Macros

| Feature | Declarative | Procedural |
|---------|-------------|------------|
| Definition | `macro_rules!` | Functions with special attributes |
| Input | Token patterns | Token streams |
| Complexity | Simple to moderate | Can be very complex |
| Compile-time | Fast | Slower |
| Power | Limited | Very powerful |

## Declarative Macros (macro_rules!)

Declarative macros are the most common type of macro in Rust. They work by pattern matching against the structure of code.

### Basic Syntax

```rust
macro_rules! macro_name {
    (pattern) => {
        // expansion
    };
}
```

### Simple Example

```rust
macro_rules! say_hello {
    () => {
        println!("Hello, World!");
    };
}

fn main() {
    say_hello!(); // Expands to: println!("Hello, World!");
}
```

### Pattern Matching

Macros can match different patterns and expand differently based on the input:

```rust
macro_rules! calculate {
    // Match addition
    ($a:expr + $b:expr) => {
        $a + $b
    };
    
    // Match multiplication
    ($a:expr * $b:expr) => {
        $a * $b
    };
    
    // Match a single expression
    ($a:expr) => {
        $a
    };
}

fn main() {
    let result1 = calculate!(5 + 3);  // 8
    let result2 = calculate!(4 * 2);  // 8
    let result3 = calculate!(42);     // 42
}
```

### Designators

Designators specify what kind of syntax element can be matched:

| Designator | Matches |
|------------|---------|
| `expr` | Expressions |
| `stmt` | Statements |
| `ident` | Identifiers |
| `path` | Paths |
| `ty` | Types |
| `pat` | Patterns |
| `item` | Items (functions, structs, etc.) |
| `block` | Block expressions |
| `meta` | Attribute contents |
| `tt` | Token trees |

### Repetition

Macros can handle repeated patterns using `*` (zero or more) or `+` (one or more):

```rust
macro_rules! vec_of {
    ($($x:expr),*) => {
        {
            let mut temp_vec = Vec::new();
            $(
                temp_vec.push($x);
            )*
            temp_vec
        }
    };
}

fn main() {
    let v = vec_of![1, 2, 3, 4, 5];
    println!("{:?}", v); // [1, 2, 3, 4, 5]
}
```

### Advanced Pattern Matching

```rust
macro_rules! hashmap {
    // Handle empty case
    () => {
        std::collections::HashMap::new()
    };
    
    // Handle key-value pairs
    ($($key:expr => $value:expr),+ $(,)?) => {
        {
            let mut map = std::collections::HashMap::new();
            $(
                map.insert($key, $value);
            )+
            map
        }
    };
}

use std::collections::HashMap;

fn main() {
    let map1: HashMap<&str, i32> = hashmap!();
    let map2 = hashmap!{
        "one" => 1,
        "two" => 2,
        "three" => 3,
    };
}
```

## Procedural Macros

Procedural macros are more powerful than declarative macros and come in three types:

1. **Function-like macros** (`proc_macro`)
2. **Derive macros** (`proc_macro_derive`)
3. **Attribute macros** (`proc_macro_attribute`)

### Setting Up Procedural Macros

First, you need a separate crate with the `proc-macro` crate type:

```toml
# Cargo.toml
[lib]
proc-macro = true

[dependencies]
proc-macro2 = "1.0"
quote = "1.0"
syn = { version = "2.0", features = ["full"] }
```

### Function-like Macros

```rust
use proc_macro::TokenStream;
use quote::quote;
use syn::{parse_macro_input, Expr};

#[proc_macro]
pub fn double(input: TokenStream) -> TokenStream {
    let expr = parse_macro_input!(input as Expr);
    
    let expanded = quote! {
        2 * (#expr)
    };
    
    expanded.into()
}
```

Usage:
```rust
use my_macros::double;

fn main() {
    let result = double!(5 + 3); // Expands to: 2 * (5 + 3)
    println!("{}", result); // 16
}
```

### Derive Macros

Derive macros automatically implement traits for structs and enums:

```rust
use proc_macro::TokenStream;
use quote::quote;
use syn::{parse_macro_input, DeriveInput};

#[proc_macro_derive(HelloWorld)]
pub fn hello_world_derive(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as DeriveInput);
    let name = &input.ident;
    
    let expanded = quote! {
        impl #name {
            fn hello_world(&self) {
                println!("Hello, World! My name is {}", stringify!(#name));
            }
        }
    };
    
    expanded.into()
}
```

Usage:
```rust
use my_macros::HelloWorld;

#[derive(HelloWorld)]
struct Person;

fn main() {
    let person = Person;
    person.hello_world(); // Hello, World! My name is Person
}
```

### Attribute Macros

Attribute macros can modify items they're attached to:

```rust
use proc_macro::TokenStream;
use quote::quote;
use syn::{parse_macro_input, ItemFn};

#[proc_macro_attribute]
pub fn timing(_args: TokenStream, input: TokenStream) -> TokenStream {
    let input_fn = parse_macro_input!(input as ItemFn);
    let fn_name = &input_fn.sig.ident;
    let fn_block = &input_fn.block;
    let fn_vis = &input_fn.vis;
    let fn_sig = &input_fn.sig;
    
    let expanded = quote! {
        #fn_vis #fn_sig {
            let start = std::time::Instant::now();
            let result = #fn_block;
            let duration = start.elapsed();
            println!("{} took: {:?}", stringify!(#fn_name), duration);
            result
        }
    };
    
    expanded.into()
}
```

Usage:
```rust
use my_macros::timing;

#[timing]
fn slow_function() {
    std::thread::sleep(std::time::Duration::from_millis(100));
    println!("Function completed");
}
```

## Common Macro Patterns

### Creating DSLs (Domain-Specific Languages)

```rust
macro_rules! html {
    ($tag:ident { $($content:tt)* }) => {
        format!("<{}>{}</{}>", stringify!($tag), html!($($content)*), stringify!($tag))
    };
    
    ($tag:ident) => {
        format!("<{} />", stringify!($tag))
    };
    
    ($text:literal) => {
        $text.to_string()
    };
    
    ($($tokens:tt)*) => {
        {
            let mut result = String::new();
            $(
                result.push_str(&html!($tokens));
            )*
            result
        }
    };
}

fn main() {
    let html_content = html! {
        div {
            h1 { "Welcome" }
            p { "This is generated HTML" }
        }
    };
    println!("{}", html_content);
}
```

### Configuration Macros

```rust
macro_rules! config {
    (
        $(
            $key:ident: $value:expr
        ),* $(,)?
    ) => {
        {
            let mut config = std::collections::HashMap::new();
            $(
                config.insert(stringify!($key), $value.to_string());
            )*
            config
        }
    };
}

fn main() {
    let app_config = config! {
        host: "localhost",
        port: 8080,
        debug: true,
    };
}
```

### Builder Pattern Macro

```rust
macro_rules! builder {
    (
        struct $name:ident {
            $(
                $field:ident: $type:ty
            ),* $(,)?
        }
    ) => {
        pub struct $name {
            $(
                $field: Option<$type>,
            )*
        }
        
        impl $name {
            pub fn new() -> Self {
                Self {
                    $(
                        $field: None,
                    )*
                }
            }
            
            $(
                pub fn $field(mut self, value: $type) -> Self {
                    self.$field = Some(value);
                    self
                }
            )*
            
            pub fn build(self) -> Result<Built$name, String> {
                Ok(Built$name {
                    $(
                        $field: self.$field.ok_or(format!("Field '{}' is required", stringify!($field)))?,
                    )*
                })
            }
        }
        
        pub struct Built$name {
            $(
                pub $field: $type,
            )*
        }
    };
}

builder! {
    struct User {
        name: String,
        age: u32,
        email: String,
    }
}

fn main() -> Result<(), String> {
    let user = User::new()
        .name("Alice".to_string())
        .age(30)
        .email("alice@example.com".to_string())
        .build()?;
    
    println!("User: {} ({})", user.name, user.age);
    Ok(())
}
```

## Advanced Techniques

### Macro Hygiene

Rust macros are hygienic, meaning they don't accidentally capture variables from the calling scope:

```rust
macro_rules! declare_and_use {
    ($var_name:ident) => {
        let x = 42; // This 'x' won't interfere with outer 'x'
        let $var_name = x + 1;
    };
}

fn main() {
    let x = 10;
    declare_and_use!(y);
    println!("x: {}, y: {}", x, y); // x: 10, y: 43
}
```

### Recursive Macros

```rust
macro_rules! count {
    () => (0);
    ($x:tt $($xs:tt)*) => (1 + count!($($xs)*));
}

fn main() {
    let count = count!(a b c d e);
    println!("Count: {}", count); // Count: 5
}
```

### Internal Rules

Use internal rules to break down complex macros:

```rust
macro_rules! complex_macro {
    // Public interface
    ($($input:tt)*) => {
        complex_macro!(@internal $($input)*)
    };
    
    // Internal rule
    (@internal $first:expr, $($rest:expr),*) => {
        {
            let mut result = $first;
            $(
                result += $rest;
            )*
            result
        }
    };
}

fn main() {
    let sum = complex_macro!(1, 2, 3, 4, 5);
    println!("Sum: {}", sum); // Sum: 15
}
```

### Generating Tests

```rust
macro_rules! test_cases {
    (
        $test_name:ident: $func:ident {
            $(
                $case_name:ident: $input:expr => $expected:expr
            ),* $(,)?
        }
    ) => {
        #[cfg(test)]
        mod $test_name {
            use super::*;
            
            $(
                #[test]
                fn $case_name() {
                    assert_eq!($func($input), $expected);
                }
            )*
        }
    };
}

fn double(x: i32) -> i32 {
    x * 2
}

test_cases! {
    double_tests: double {
        positive: 5 => 10,
        negative: -3 => -6,
        zero: 0 => 0,
    }
}
```

## Best Practices

### 1. Start Simple

Begin with simple declarative macros before moving to procedural macros.

### 2. Use Descriptive Names

```rust
// Good
macro_rules! create_getter_setter {
    // ...
}

// Less clear
macro_rules! cgs {
    // ...
}
```

### 3. Document Your Macros

```rust
/// Creates a HashMap with the given key-value pairs.
/// 
/// # Example
/// 
/// ```
/// let map = hashmap!{
///     "key1" => "value1",
///     "key2" => "value2",
/// };
/// ```
macro_rules! hashmap {
    // implementation
}
```

### 4. Handle Edge Cases

Always consider empty inputs and error cases:

```rust
macro_rules! safe_macro {
    () => {
        compile_error!("Macro requires at least one argument");
    };
    ($($args:tt)*) => {
        // actual implementation
    };
}
```

### 5. Use `tt` for Maximum Flexibility

When you need to accept arbitrary tokens:

```rust
macro_rules! flexible_macro {
    ($($tokens:tt)*) => {
        // Process tokens as needed
    };
}
```

### 6. Prefer Functions When Possible

Only use macros when you need compile-time code generation or when functions can't express what you need.

## Debugging Macros

### 1. Use `cargo expand`

Install and use `cargo expand` to see macro expansions:

```bash
cargo install cargo-expand
cargo expand
```

### 2. Compile-time Debugging

```rust
macro_rules! debug_macro {
    ($($args:tt)*) => {
        {
            compile_error!(concat!("Debug: ", stringify!($($args)*)));
        }
    };
}
```

### 3. Runtime Debugging

```rust
macro_rules! debug_print {
    ($($args:tt)*) => {
        {
            println!("Macro generated: {}", stringify!($($args)*));
            $($args)*
        }
    };
}
```

### 4. Step-by-step Development

Build macros incrementally, testing each part:

```rust
macro_rules! step_by_step {
    // Step 1: Basic structure
    ($name:ident) => {
        struct $name;
    };
    
    // Step 2: Add fields (develop incrementally)
    // ...
}
```

## Real-World Examples

### 1. JSON-like Macro (Simplified)

```rust
macro_rules! json {
    (null) => {
        serde_json::Value::Null
    };
    
    (true) => {
        serde_json::Value::Bool(true)
    };
    
    (false) => {
        serde_json::Value::Bool(false)
    };
    
    ($n:expr) => {
        serde_json::json!($n)
    };
    
    ({ $($key:expr => $value:tt),* $(,)? }) => {
        serde_json::json!({
            $(
                $key: json!($value)
            ),*
        })
    };
    
    ([ $($item:tt),* $(,)? ]) => {
        serde_json::json!([
            $(
                json!($item)
            ),*
        ])
    };
}
```

### 2. State Machine Macro

```rust
macro_rules! state_machine {
    (
        enum $name:ident {
            $(
                $state:ident
            ),* $(,)?
        }
        
        transitions {
            $(
                $from:ident -> $to:ident on $event:ident
            ),* $(,)?
        }
    ) => {
        #[derive(Debug, Clone, PartialEq)]
        pub enum $name {
            $(
                $state,
            )*
        }
        
        impl $name {
            pub fn transition(&self, event: &str) -> Option<Self> {
                match (self, event) {
                    $(
                        (Self::$from, stringify!($event)) => Some(Self::$to),
                    )*
                    _ => None,
                }
            }
        }
    };
}

state_machine! {
    enum TrafficLight {
        Red,
        Yellow,
        Green,
    }
    
    transitions {
        Red -> Green on go,
        Green -> Yellow on slow,
        Yellow -> Red on stop,
    }
}
```

### 3. Enum Iteration Macro

```rust
macro_rules! iterable_enum {
    (
        $(#[$meta:meta])*
        pub enum $name:ident {
            $(
                $variant:ident
            ),* $(,)?
        }
    ) => {
        $(#[$meta])*
        #[derive(Debug, Clone, Copy, PartialEq, Eq)]
        pub enum $name {
            $(
                $variant,
            )*
        }
        
        impl $name {
            pub fn all() -> &'static [Self] {
                &[
                    $(
                        Self::$variant,
                    )*
                ]
            }
            
            pub fn iter() -> std::slice::Iter<'static, Self> {
                Self::all().iter()
            }
        }
    };
}

iterable_enum! {
    pub enum Color {
        Red,
        Green,
        Blue,
    }
}

fn main() {
    for color in Color::iter() {
        println!("{:?}", color);
    }
}
```

## Conclusion

Macros are a powerful feature of Rust that enable metaprogramming and code generation at compile time. They can significantly reduce boilerplate code and enable the creation of elegant APIs and domain-specific languages. However, they should be used judiciously—prefer functions when possible, and reach for macros when you need their unique capabilities.

Key takeaways:
- Start with declarative macros (`macro_rules!`) for simpler use cases
- Move to procedural macros when you need more power and flexibility
- Always consider macro hygiene and edge cases
- Document your macros thoroughly
- Use debugging tools like `cargo expand` to understand macro expansions
- Test your macros extensively

With practice, macros can become an invaluable tool in your Rust programming toolkit, enabling you to write more expressive and maintainable code.

RUST MACROS: STEP-BY-STEP PROCESS
=====================================

STEP 1: MACRO DEFINITION
========================
Source Code (.rs file):
┌─────────────────────────────────────────────────────────────┐
│ macro_rules! say_hello {                                    │
│     ($name:expr) => {                                       │
│         println!("Hello, {}!", $name);                     │
│     };                                                      │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
                    [Macro Registry]
                    Stored for later use

STEP 2: MACRO INVOCATION
========================
Source Code:
┌─────────────────────────────────────────────────────────────┐
│ fn main() {                                                 │
│     say_hello!("World");    ◄── Macro invocation           │
│     say_hello!("Rust");                                    │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
                    [Tokenization]
                    
Token Stream:
┌─────────────────────────────────────────────────────────────┐
│ say_hello ! ( "World" ) ;                                   │
│    │      │ │    │    │ │                                   │
│   Ident  Bang Delim Literal Delim Semi                     │
└─────────────────────────────────────────────────────────────┘

STEP 3: PATTERN MATCHING
=========================
Macro Engine compares invocation with patterns:

Pattern:    ($name:expr)
           ┌─────────────┐
           │   $name     │ ◄── Variable capture
           │   :expr     │ ◄── Expression type
           └─────────────┘
                 │
                 ▼
Input:     ("World")
           ┌─────────────┐
           │  "World"    │ ◄── Matches expr pattern
           └─────────────┘

Match Result: $name = "World"

STEP 4: MACRO EXPANSION
=======================
Template:   println!("Hello, {}!", $name);
                                    │
                                    ▼
Substitution: $name → "World"
                                    │
                                    ▼
Expanded:   println!("Hello, {}!", "World");

STEP 5: RECURSIVE EXPANSION (if needed)
=======================================
println! is also a macro, so it gets expanded too:

println!("Hello, {}!", "World")
                │
                ▼
        [Further expansion]
                │
                ▼
std::io::_print(format_args!("Hello, {}!\n", "World"))

STEP 6: COMPLETE EXPANSION TREE
===============================
Original Code:
┌─────────────────────────────────────────────────────────────┐
│ fn main() {                                                 │
│     say_hello!("World");                                   │
│     say_hello!("Rust");                                    │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼ [Macro Expansion Phase]
Expanded Code:
┌─────────────────────────────────────────────────────────────┐
│ fn main() {                                                 │
│     {                                                       │
│         std::io::_print(                                   │
│             format_args!("Hello, {}!\n", "World")         │
│         );                                                  │
│     };                                                      │
│     {                                                       │
│         std::io::_print(                                   │
│             format_args!("Hello, {}!\n", "Rust")          │
│         );                                                  │
│     };                                                      │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘

STEP 7: COMPILATION PHASES
==========================

Phase 1: Lexing & Parsing
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Source Code   │───▶│   Token Stream  │───▶│   Parse Tree    │
└─────────────────┘    └─────────────────┘    └─────────────────┘

Phase 2: Macro Expansion
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Parse Tree    │───▶│ Macro Processor │───▶│ Expanded Tree   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ Pattern Matcher │
                       │ Template Engine │
                       │ Hygiene Checker │
                       └─────────────────┘

Phase 3: Further Compilation
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Expanded Tree   │───▶│  Type Checker   │───▶│   Assembly/     │
└─────────────────┘    └─────────────────┘    │   Machine Code  │
                                              └─────────────────┘

STEP 8: MACRO HYGIENE SYSTEM
============================
Rust ensures macro hygiene to prevent variable capture:

Original scope:           Macro scope:
┌─────────────────┐      ┌─────────────────┐
│ let x = 5;      │      │ let x = 10;     │ ◄── Different 'x'
│ my_macro!();    │──────┤ println!("{}", x);│
│ println!("{}", x)│      └─────────────────┘
└─────────────────┘              │
        │                        │
        ▼                        ▼
   Prints: 5              Prints: 10
   (Original x)           (Macro's x)

STEP 9: COMPLEX MACRO EXAMPLE
=============================
Input Pattern Matching:

macro_rules! vec {
    ( $( $x:expr ),* ) => {    ◄── Repetition pattern
        {
            let mut temp_vec = Vec::new();
            $(                 ◄── Repeat this block
                temp_vec.push($x);
            )*
            temp_vec
        }
    };
}

Invocation: vec![1, 2, 3, 4]

Expansion Process:
┌─────────────────────────────────────────────────────────────┐
│ Pattern: ( $( $x:expr ),* )                                 │
│          └─┬─┘ └─┬─┘  └┬┘                                   │
│            │    │     └── Zero or more, comma-separated     │
│            │    └──────── Expression                        │
│            └──────────── Repetition group                   │
├─────────────────────────────────────────────────────────────┤
│ Input: [1, 2, 3, 4]                                         │
│        │  │  │  └── $x = 4                                  │
│        │  │  └───── $x = 3                                  │
│        │  └────── $x = 2                                    │
│        └─────── $x = 1                                      │
├─────────────────────────────────────────────────────────────┤
│ Expansion:                                                  │
│ {                                                           │
│     let mut temp_vec = Vec::new();                          │
│     temp_vec.push(1);      ◄── Repeated 4 times            │
│     temp_vec.push(2);                                       │
│     temp_vec.push(3);                                       │
│     temp_vec.push(4);                                       │
│     temp_vec                                                │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘

TIMELINE SUMMARY
================
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Write      │  │   Compile    │  │   Expand     │  │   Generate   │
│   Macro      │─▶│   Time       │─▶│   Macros     │─▶│   Final      │
│   Definition │  │   Analysis   │  │              │  │   Machine    │
│              │  │              │  │              │  │   Code       │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
      │                   │                   │                   │
      ▼                   ▼                   ▼                   ▼
Parse & Store      Pattern Match      Code Generation      Optimization
in Registry        & Validate         & Substitution       & Assembly

Key Points:
• Macros are expanded at COMPILE TIME, not runtime
• Pattern matching happens on token streams
• Hygiene system prevents variable capture
• Recursive expansion for nested macros
• Zero-cost abstraction - no runtime overhead