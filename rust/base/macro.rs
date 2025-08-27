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