# Comprehensive Guide to Rust Macros

Rust macros are metaprogramming tools that generate code at compile time. They're more powerful than traditional preprocessor macros and type-safe, making them essential for reducing boilerplate and creating domain-specific languages.

## 1. Macro Fundamentals

### Why Macros Exist

Macros solve problems that functions cannot:
- **Variable argument count**: `println!`, `vec!`
- **Compile-time code generation**: Reduce runtime overhead
- **Pattern matching on syntax**: Match against Rust's AST
- **Trait implementations**: Derive macros for automatic trait impl

### Macro Types Overview

1. **Declarative Macros** (`macro_rules!`) - Pattern matching on syntax
2. **Procedural Macros** - Custom derive, attribute, function-like
3. **Built-in Macros** - `println!`, `vec!`, `panic!`, etc.

---

## 2. Declarative Macros (`macro_rules!`)

### Basic Syntax

```rust
macro_rules! macro_name {
    (pattern) => {
        expansion
    };
}
```

### Simple Example

```rust
macro_rules! say_hello {
    () => {
        println!("Hello, world!");
    };
}

fn main() {
    say_hello!(); // Expands to println!("Hello, world!");
}
```

### Pattern Matching

Macros use **fragment specifiers** to match different syntax elements:

| Specifier | Matches | Example |
|-----------|---------|---------|
| `expr` | Expression | `1 + 2`, `foo()` |
| `stmt` | Statement | `let x = 5;` |
| `ty` | Type | `i32`, `Vec<T>` |
| `ident` | Identifier | `foo`, `bar` |
| `path` | Path | `std::io::Read` |
| `pat` | Pattern | `Some(x)` |
| `block` | Block | `{ ... }` |
| `item` | Item | `fn`, `struct`, `mod` |
| `meta` | Attribute content | `cfg(test)` |
| `tt` | Token tree | Any single token |
| `literal` | Literal | `42`, `"string"` |

### Practical Examples

#### Creating a HashMap

```rust
macro_rules! hashmap {
    ($($key:expr => $val:expr),* $(,)?) => {{
        let mut map = ::std::collections::HashMap::new();
        $(
            map.insert($key, $val);
        )*
        map
    }};
}

fn main() {
    let map = hashmap! {
        "name" => "Alice",
        "age" => "30",
    };
}
```

**Key concepts:**
- `$($key:expr => $val:expr),*` - Repetition pattern
- `$(,)?` - Optional trailing comma
- `$(...)*` - Zero or more repetitions
- `::std::` - Absolute path to avoid name conflicts

#### Multiple Patterns

```rust
macro_rules! calculate {
    // Addition
    (add $a:expr, $b:expr) => {
        $a + $b
    };
    
    // Multiplication
    (mul $a:expr, $b:expr) => {
        $a * $b
    };
    
    // Power (recursive)
    (pow $base:expr, $exp:expr) => {{
        let mut result = 1;
        for _ in 0..$exp {
            result *= $base;
        }
        result
    }};
}

fn main() {
    let sum = calculate!(add 5, 3);      // 8
    let product = calculate!(mul 4, 7);  // 28
    let power = calculate!(pow 2, 8);    // 256
}
```

### Repetition Patterns

```rust
macro_rules! create_function {
    // Match function name and parameter list
    ($func_name:ident, $($param:ident: $type:ty),*) => {
        fn $func_name($($param: $type),*) {
            println!("Function {} called", stringify!($func_name));
        }
    };
}

create_function!(my_func, x: i32, y: i32);
// Expands to:
// fn my_func(x: i32, y: i32) {
//     println!("Function my_func called");
// }
```

### Recursive Macros

```rust
macro_rules! count_exprs {
    () => (0);
    ($head:expr) => (1);
    ($head:expr, $($tail:expr),*) => (1 + count_exprs!($($tail),*));
}

fn main() {
    const COUNT: usize = count_exprs!(1, 2, 3, 4, 5); // 5
}
```

### Internal Rules (TT Munching)

```rust
macro_rules! parse_values {
    // Base case
    (@internal $name:ident; ) => {
        println!("{}", stringify!($name));
    };
    
    // Recursive case
    (@internal $name:ident; $val:expr, $($rest:expr,)*) => {
        println!("{}: {}", stringify!($name), $val);
        parse_values!(@internal $name; $($rest,)*);
    };
    
    // Entry point
    ($name:ident = $($vals:expr),* $(,)?) => {
        parse_values!(@internal $name; $($vals,)*);
    };
}
```

**Pattern**: Use `@internal` as a hidden rule for recursion.

---

## 3. Procedural Macros

Procedural macros operate on the token stream and are more powerful than declarative macros. They're defined in separate crates with `proc-macro = true`.

### Setup

**Cargo.toml**:
```toml
[lib]
proc-macro = true

[dependencies]
syn = { version = "2.0", features = ["full"] }
quote = "1.0"
proc-macro2 = "1.0"
```

### Types of Procedural Macros

#### 1. Custom Derive Macros

```rust
// my_macro/src/lib.rs
use proc_macro::TokenStream;
use quote::quote;
use syn::{parse_macro_input, DeriveInput};

#[proc_macro_derive(Builder)]
pub fn derive_builder(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as DeriveInput);
    let name = &input.ident;
    let builder_name = format!("{}Builder", name);
    let builder_ident = syn::Ident::new(&builder_name, name.span());
    
    // Extract fields
    let fields = if let syn::Data::Struct(data) = &input.data {
        if let syn::Fields::Named(fields) = &data.fields {
            &fields.named
        } else {
            panic!("Builder only works with named fields");
        }
    } else {
        panic!("Builder only works with structs");
    };
    
    // Generate builder fields (all Option<T>)
    let builder_fields = fields.iter().map(|f| {
        let name = &f.ident;
        let ty = &f.ty;
        quote! { #name: Option<#ty> }
    });
    
    // Generate setter methods
    let setters = fields.iter().map(|f| {
        let name = &f.ident;
        let ty = &f.ty;
        quote! {
            pub fn #name(mut self, value: #ty) -> Self {
                self.#name = Some(value);
                self
            }
        }
    });
    
    // Generate build method
    let build_fields = fields.iter().map(|f| {
        let name = &f.ident;
        quote! {
            #name: self.#name.ok_or(concat!("Field ", stringify!(#name), " is required"))?
        }
    });
    
    let expanded = quote! {
        impl #name {
            pub fn builder() -> #builder_ident {
                #builder_ident {
                    #(#builder_fields: None,)*
                }
            }
        }
        
        pub struct #builder_ident {
            #(#builder_fields,)*
        }
        
        impl #builder_ident {
            #(#setters)*
            
            pub fn build(self) -> Result<#name, Box<dyn std::error::Error>> {
                Ok(#name {
                    #(#build_fields,)*
                })
            }
        }
    };
    
    TokenStream::from(expanded)
}
```

**Usage**:
```rust
#[derive(Builder)]
struct User {
    name: String,
    age: u32,
    email: String,
}

fn main() {
    let user = User::builder()
        .name("Alice".to_string())
        .age(30)
        .email("alice@example.com".to_string())
        .build()
        .unwrap();
}
```

#### 2. Attribute Macros

```rust
use proc_macro::TokenStream;
use quote::quote;
use syn::{parse_macro_input, ItemFn};

#[proc_macro_attribute]
pub fn timing(_attr: TokenStream, item: TokenStream) -> TokenStream {
    let input = parse_macro_input!(item as ItemFn);
    let fn_name = &input.sig.ident;
    let fn_block = &input.block;
    let fn_sig = &input.sig;
    let fn_vis = &input.vis;
    
    let expanded = quote! {
        #fn_vis #fn_sig {
            let start = std::time::Instant::now();
            let result = (|| #fn_block)();
            let elapsed = start.elapsed();
            println!("[{}] took {:?}", stringify!(#fn_name), elapsed);
            result
        }
    };
    
    TokenStream::from(expanded)
}
```

**Usage**:
```rust
#[timing]
fn expensive_operation() -> u32 {
    std::thread::sleep(std::time::Duration::from_millis(100));
    42
}
```

#### 3. Function-like Macros

```rust
use proc_macro::TokenStream;
use quote::quote;
use syn::{parse_macro_input, LitStr};

#[proc_macro]
pub fn sql(input: TokenStream) -> TokenStream {
    let query = parse_macro_input!(input as LitStr);
    let query_str = query.value();
    
    // Validate SQL at compile time
    if !query_str.to_uppercase().starts_with("SELECT") {
        panic!("Only SELECT queries are allowed");
    }
    
    let expanded = quote! {
        {
            let query: &'static str = #query_str;
            // Return prepared query struct
            Query::new(query)
        }
    };
    
    TokenStream::from(expanded)
}
```

**Usage**:
```rust
let query = sql!("SELECT * FROM users WHERE age > 18");
```

---

## 4. Advanced Macro Techniques

### Hygiene and Variable Capture

Rust macros are **hygienic** - variables in the expansion don't clash with surrounding code:

```rust
macro_rules! using_a {
    ($e:expr) => {{
        let a = 42;
        $e
    }};
}

fn main() {
    let a = 100;
    let result = using_a!(a + 1); // Uses outer 'a', result = 101
}
```

### Breaking Hygiene (When Needed)

```rust
macro_rules! declare_var {
    ($name:ident) => {
        let $name = 42;
    };
}

fn main() {
    declare_var!(x);
    println!("{}", x); // Works! Intentional variable injection
}
```

### Macro Expansion Recursion Limits

```rust
// Default limit is 128 recursions
#![recursion_limit = "256"]

macro_rules! recursive {
    (0) => { 1 };
    ($n:tt) => { 1 + recursive!(0) }; // Simplified
}
```

### Debugging Macros

```rust
// View macro expansion with cargo expand
// cargo install cargo-expand
// cargo expand --bin my_binary

macro_rules! debug_macro {
    ($($t:tt)*) => {
        println!("Tokens: {}", stringify!($($t)*));
    };
}
```

### Macro Visibility and Exports

```rust
// Export macro from crate
#[macro_export]
macro_rules! my_macro {
    () => { /* ... */ };
}

// Import macro
use my_crate::my_macro;

// Or import all macros
#[macro_use]
extern crate my_crate;
```

### Macro Modules

```rust
// Define macro in module
mod macros {
    #[macro_export]
    macro_rules! internal_macro {
        () => { /* ... */ };
    }
}

// Re-export at crate root
pub use macros::*;
```

---

## 5. Real-World Patterns

### DSL Creation

```rust
macro_rules! html {
    // Self-closing tags
    (<$tag:ident />) => {
        format!("<{} />", stringify!($tag))
    };
    
    // Tags with content
    (<$tag:ident>$($content:tt)*</$close:ident>) => {{
        let content = html!($($content)*);
        format!("<{}>{}</{}>", stringify!($tag), content, stringify!($close))
    }};
    
    // Text content
    ($text:expr) => {
        $text.to_string()
    };
}

fn main() {
    let markup = html! {
        <div>
            <h1>"Hello"</h1>
            <p>"World"</p>
        </div>
    };
}
```

### Test Generation

```rust
macro_rules! test_cases {
    ($fn_name:ident: $($name:ident => $input:expr, $expected:expr);* $(;)?) => {
        $(
            #[test]
            fn $name() {
                assert_eq!($fn_name($input), $expected);
            }
        )*
    };
}

fn add_one(x: i32) -> i32 {
    x + 1
}

test_cases! {
    add_one:
    test_zero => 0, 1;
    test_positive => 5, 6;
    test_negative => -3, -2;
}
```

### Lazy Static Initialization

```rust
macro_rules! lazy_static {
    ($name:ident: $ty:ty = $init:expr) => {
        static $name: std::sync::OnceLock<$ty> = std::sync::OnceLock::new();
        
        impl $name {
            pub fn get() -> &'static $ty {
                $name.get_or_init(|| $init)
            }
        }
    };
}
```

### Compile-Time Assertions

```rust
macro_rules! static_assert {
    ($condition:expr) => {
        const _: () = assert!($condition);
    };
}

static_assert!(std::mem::size_of::<usize>() == 8); // On 64-bit
```

---

## 6. Performance Considerations

### Zero-Cost Abstractions

Macros expand at compile time - no runtime overhead:

```rust
macro_rules! fast_loop {
    ($n:expr, $body:expr) => {{
        for _ in 0..$n {
            $body
        }
    }};
}

// Identical performance to hand-written loop
fast_loop!(1000, println!("Hello"));
```

### Compile-Time Computation

```rust
macro_rules! const_eval {
    ($expr:expr) => {{
        const VALUE: usize = $expr;
        VALUE
    }};
}

// Computed at compile time
const SIZE: usize = const_eval!(100 * 100);
```

### Avoiding Code Bloat

```rust
// BAD: Creates separate function for each type
macro_rules! bad_generic {
    ($t:ty) => {
        fn process_bad(val: $t) {
            // Large function body duplicated per type
        }
    };
}

// GOOD: Use actual generics
fn process_good<T>(val: T) {
    // Single monomorphized instance per type
}
```

---

## 7. Common Pitfalls

### 1. Macro Hygiene Confusion

```rust
macro_rules! swap {
    ($a:expr, $b:expr) => {{
        let temp = $a; // 'temp' is hygienic
        $a = $b;
        $b = temp;
    }};
}
```

### 2. Fragment Specifier Limitations

```rust
// DOESN'T WORK: Can't match 'ty' then use as 'expr'
macro_rules! bad_macro {
    ($t:ty) => {
        let x: $t = $t::default(); // Can't call methods on 'ty'
    };
}

// WORKS: Use 'path' for type with associated functions
macro_rules! good_macro {
    ($t:path) => {
        let x = $t::default();
    };
}
```

### 3. Repetition Edge Cases

```rust
// Handle zero, one, or many
macro_rules! count {
    () => (0);
    ($single:expr) => (1);
    ($first:expr, $($rest:expr),+) => (1 + count!($($rest),+));
}
```

### 4. Order of Expansion

```rust
// Macros expand outside-in
macro_rules! outer {
    ($e:expr) => { inner!($e) };
}

macro_rules! inner {
    ($e:expr) => { $e + 1 };
}

// outer!(5) -> inner!(5) -> 5 + 1
```

---

## 8. Ecosystem Tools

### `syn` - Parsing Rust Syntax

```rust
use syn::{parse_quote, Expr};

let expr: Expr = parse_quote! {
    x + y * z
};
```

### `quote` - Generating Code

```rust
use quote::quote;

let tokens = quote! {
    fn hello() {
        println!("Hello, world!");
    }
};
```

### `proc-macro2` - Stable Token Manipulation

```rust
use proc_macro2::TokenStream;

// Works in tests and outside proc-macro crates
```

### `cargo-expand` - View Expansions

```bash
cargo install cargo-expand
cargo expand --lib
cargo expand my_function
```

---

## 9. Best Practices

1. **Prefer functions over macros** - Use macros only when necessary
2. **Keep macros simple** - Complex logic belongs in functions
3. **Document thoroughly** - Show examples of expansion
4. **Test extensively** - Include compile-fail tests
5. **Use fragment specifiers correctly** - `expr`, `ty`, `ident`, etc.
6. **Handle edge cases** - Empty input, trailing commas
7. **Be hygienic** - Avoid unintended variable capture
8. **Version carefully** - Proc macros affect compile time
9. **Use `cargo expand`** - Always verify expansion
10. **Consider alternatives** - Const generics, traits, builders

---

## 10. When to Use Macros

### Good Use Cases
- Reducing repetitive boilerplate (derive macros)
- Domain-specific languages
- Variadic functions (`println!`, `vec!`)
- Compile-time code generation
- Test generation

### Avoid Macros For
- Simple functions
- Type conversions (use `From`/`Into`)
- Logic that can use generics
- Code that benefits from IDE support
- Simple builders (use structs)

---

This guide covers macro fundamentals through advanced techniques. Macros are powerful but complex - use them judiciously and always prefer simpler alternatives when available.