# 🦀 The Complete Guide to `macro_rules!` in Rust
### From First Principles to World-Class Mastery

---

## Table of Contents

1. [The Philosophy of Macros — Why They Exist](#1-the-philosophy-of-macros)
2. [Macros vs Functions — The Core Distinction](#2-macros-vs-functions)
3. [The Two Families of Rust Macros](#3-the-two-families-of-rust-macros)
4. [Anatomy of `macro_rules!`](#4-anatomy-of-macro_rules)
5. [Fragment Specifiers — The Type System of Macros](#5-fragment-specifiers)
6. [Repetition Operators — `*`, `+`, `?`](#6-repetition-operators)
7. [Multiple Match Arms — Pattern Dispatching](#7-multiple-match-arms)
8. [Recursive Macros](#8-recursive-macros)
9. [Macro Hygiene — The Hidden Safety Net](#9-macro-hygiene)
10. [Scoping and Exporting Macros](#10-scoping-and-exporting-macros)
11. [Advanced Patterns](#11-advanced-patterns)
12. [Real-World Implementations](#12-real-world-implementations)
13. [Debugging Macros](#13-debugging-macros)
14. [Common Pitfalls](#14-common-pitfalls)
15. [Mental Models and Mastery Path](#15-mental-models-and-mastery-path)

---

## 1. The Philosophy of Macros

### What Problem Do Macros Solve?

Imagine you are a builder. Functions are your pre-built doors — you install the same door everywhere. 
But what if you need a door that is *customized at construction time* — different sizes, different materials,
depending on what the blueprint says? That is what macros do.

**Macros are code that writes code.**

In computer science terms, macros operate at **compile time** on the **Abstract Syntax Tree (AST)** — the 
tree-like representation of your source code before it becomes machine instructions.

```
Your Source Code
      │
      ▼
┌─────────────────────────────────────────────────────┐
│                  COMPILATION PIPELINE                │
│                                                      │
│  Source Text                                         │
│      │                                               │
│      ▼                                               │
│  Lexer (tokenization)                                │
│      │  "hello", "+", "world", ";" ...               │
│      ▼                                               │
│  Parser (builds AST)         ◄── macro_rules! runs   │
│      │  FunctionCall(        ◄── HERE on the AST     │
│      │    name: "println"    ◄── BEFORE type-checking│
│      │    args: [...]                                 │
│      │  )                                            │
│      ▼                                               │
│  Type Checker                                        │
│      │                                               │
│      ▼                                               │
│  Code Generator (LLVM IR)                            │
│      │                                               │
│      ▼                                               │
│  Machine Code / Binary                               │
└─────────────────────────────────────────────────────┘
```

### Key Mental Model

> **A macro is a transformation rule: it receives a token stream (raw syntax) and produces a new token stream.**

This is fundamentally different from a function, which receives *values* at *runtime*.

---

## 2. Macros vs Functions — The Core Distinction

Before learning syntax, burn this table into your mind:

```
┌─────────────────────┬──────────────────────────┬────────────────────────────┐
│ Property            │ Function                 │ Macro (macro_rules!)       │
├─────────────────────┼──────────────────────────┼────────────────────────────┤
│ When does it run?   │ Runtime                  │ Compile time               │
│ What does it take?  │ Values (typed)           │ Token streams (syntax)     │
│ Return type?        │ One fixed type           │ Any valid Rust code        │
│ Variadic arguments? │ No (without traits)      │ Yes! (native)              │
│ Can define items?   │ No                       │ Yes (structs, fns, impls)  │
│ Checked when?       │ After expansion          │ After expansion            │
│ Hygienic?           │ N/A                      │ Yes (variable isolation)   │
│ Debuggable?         │ Step through debugger    │ Use cargo expand           │
│ Performance cost?   │ Call overhead (may inline│ Zero — inlined at compile  │
│                     │ by compiler)             │ time                       │
│ Arity               │ Fixed at definition      │ Variable (0 to N args)     │
└─────────────────────┴──────────────────────────┴────────────────────────────┘
```

### Why Does This Matter for Performance?

```rust
// FUNCTION — called at runtime, stack frame created
fn add(a: i32, b: i32) -> i32 { a + b }

// After compilation, roughly becomes:
// push a onto stack
// push b onto stack  
// call add
// pop result

// MACRO — expanded at compile time, NO call overhead
macro_rules! add {
    ($a:expr, $b:expr) => { $a + $b };
}

// add!(3, 4) literally becomes: 3 + 4 in the final code
// Zero function call overhead
```

---

## 3. The Two Families of Rust Macros

```
                    RUST MACROS
                        │
          ┌─────────────┴──────────────┐
          │                            │
  Declarative Macros           Procedural Macros
  (macro_rules!)               (proc macros)
          │                            │
  Pattern matching on         Operate on TokenStream
  token streams               Full Rust code to
  Simple, fast to write       manipulate AST
  No external crates          Requires separate crate
          │                            │
  ┌───────┴───────┐        ┌───────────┼───────────┐
  │               │        │           │           │
  vec![]     println!    #[derive]  #[attribute]  function-like
  assert!    format!    Clone/Debug  #[async_trait]  proc_macro!()
  matches!   todo!
```

> **This guide focuses entirely on `macro_rules!` (Declarative Macros).**
> Procedural macros are a separate, more advanced topic.

---

## 4. Anatomy of `macro_rules!`

### The Skeleton

```
macro_rules! MACRO_NAME {
    ( PATTERN ) => { EXPANSION };
    ( PATTERN ) => { EXPANSION };
    // ... more arms
}
```

Every `macro_rules!` has:
- A **name** (the identifier you call it with, followed by `!`)
- One or more **match arms**, each containing:
  - A **pattern** (what token sequence to match against)
  - An **expansion** (what Rust code to produce)

### Your First Macro — The "Hello" Version

```rust
macro_rules! say_hello {
    () => {
        println!("Hello, world!");
    };
}

fn main() {
    say_hello!(); // expands to: println!("Hello, world!");
}
```

```
MACRO CALL:   say_hello!()
                   │
                   ▼
PATTERN CHECK: () → matches empty pattern
                   │
                   ▼
EXPANSION:    println!("Hello, world!")
                   │
                   ▼
FINAL CODE:   println!("Hello, world!")
```

### Macro Invocation Syntax

All three forms are valid — they are completely equivalent:

```rust
say_hello!()    // parens
say_hello![]    // brackets  
say_hello!{}    // braces
```

> Convention: use `!()` for expression macros, `![]` for collection-like macros (e.g., `vec![]`), `!{}` for block-like macros.

---

## 5. Fragment Specifiers

### What is a Fragment Specifier?

A **fragment specifier** is the "type annotation" for macro patterns. When you write `$x:expr`, you are saying:
*"Capture whatever token sequence forms a valid Rust expression, and bind it to the name `$x`."*

**Syntax:** `$name:kind`

```
        $   x   :  expr
        │   │   │    │
        │   │   │    └── kind (what category of syntax)
        │   │   └─────── separator
        │   └─────────── name (your binding variable)
        └─────────────── sigil (marks this as a metavariable)
```

### Complete Fragment Specifier Reference

```
┌────────────────┬──────────────────────────────────────────────┬─────────────────────────────┐
│ Specifier      │ Matches                                      │ Example                     │
├────────────────┼──────────────────────────────────────────────┼─────────────────────────────┤
│ expr           │ Any expression                               │ 1+2, foo(), {let x=3; x}    │
│ stmt           │ A single statement                           │ let x = 5;                  │
│ ty             │ A type                                       │ i32, Vec<String>, &mut T    │
│ ident          │ An identifier                                │ foo, my_var, SomeStruct     │
│ path           │ A path (qualified identifier)                │ std::io, foo::Bar, ::crate  │
│ pat            │ A pattern (used in match arms)               │ Some(x), (a, b), 1..=5      │
│ pat_param      │ A pattern (no top-level OR)                  │ Some(x), (a, b)             │
│ block          │ A block expression { ... }                   │ { let x=5; x+1 }            │
│ item           │ An item (fn, struct, impl, use, etc.)        │ fn foo() {}, struct Bar {}  │
│ meta           │ Attribute metadata (inside #[...])           │ derive(Debug), cfg(test)    │
│ tt             │ A single token tree (most flexible!)         │ ANY token or group          │
│ lifetime       │ A lifetime annotation                        │ 'a, 'static, 'lifetime      │
│ vis            │ A visibility modifier                        │ pub, pub(crate), (empty)    │
│ literal        │ A literal value                              │ 42, "hello", 3.14, true     │
└────────────────┴──────────────────────────────────────────────┴─────────────────────────────┘
```

### Deep Dive: Each Specifier with Examples

#### `expr` — Expressions

```rust
macro_rules! double {
    ($x:expr) => {
        $x * 2
    };
}

fn main() {
    let a = double!(5);          // 5 * 2 = 10
    let b = double!(3 + 4);      // (3 + 4) * 2 = 14
    let c = double!({            // block expression!
        let x = 10;
        x + 5
    });                          // 15 * 2 = 30
}
```

> ⚠️ **Critical Rule:** `expr` captures greedily. It captures the ENTIRE expression as a unit. 
> This is why `double!(3 + 4)` becomes `(3 + 4) * 2`, NOT `3 + 4 * 2`.
> The macro wraps captured expressions in their own parentheses during expansion.

#### `ident` — Identifiers

```rust
// Creates a getter/setter pair for a struct field
macro_rules! make_getter {
    ($field:ident, $type:ty) => {
        pub fn $field(&self) -> &$type {
            &self.$field
        }
    };
}

struct Person {
    name: String,
    age: u32,
}

impl Person {
    make_getter!(name, String);  // generates: pub fn name(&self) -> &String { &self.name }
    make_getter!(age, u32);      // generates: pub fn age(&self) -> &u32 { &self.age }
}
```

#### `ty` — Types

```rust
macro_rules! impl_zero {
    ($type:ty, $zero:expr) => {
        impl Zero for $type {
            fn zero() -> $type {
                $zero
            }
        }
    };
}

trait Zero {
    fn zero() -> Self;
}

impl_zero!(i32, 0);
impl_zero!(f64, 0.0);
impl_zero!(String, String::new());
```

#### `tt` — Token Trees (The Wildcard)

`tt` is the most powerful and flexible specifier. It matches:
- Any single token: `42`, `"hello"`, `+`, `;`, `foo`
- Any token group: `(...)`, `[...]`, `{...}` (and everything inside)

```rust
// A macro that accepts ANYTHING and does something with it
macro_rules! inspect {
    ($x:tt) => {
        println!("Got a token tree: {:?}", stringify!($x));
    };
}

inspect!(42);           // "Got a token tree: \"42\""
inspect!((1 + 2));      // "Got a token tree: \"(1 + 2)\""
inspect!(Vec<i32>);     // ERROR — Vec<i32> is multiple tokens!
                        // use: inspect!((Vec<i32>)) to wrap in parens
```

```
TOKEN TREE VISUALIZATION:

  (1 + 2 * foo(3))
       │
       ▼
  ┌────────────────┐
  │   GROUP ( )    │  ← one tt (the whole group)
  │  ┌─┐ ┌─┐ ┌──┐ │
  │  │1│ │+│ │2 │ │  ← individual tts inside
  │  └─┘ └─┘ └──┘ │
  │          ┌──────────┐
  │          │  * foo(3)│  ← foo(3) is itself a group
  │          └──────────┘
  └────────────────┘
```

#### `pat` — Patterns

```rust
macro_rules! match_result {
    ($value:expr, $ok_pat:pat => $ok_body:expr, Err($err_pat:pat) => $err_body:expr) => {
        match $value {
            Ok($ok_pat) => $ok_body,
            Err($err_pat) => $err_body,
        }
    };
}

let result: Result<i32, &str> = Ok(42);
let answer = match_result!(
    result,
    x => x * 2,
    Err(e) => { println!("Error: {}", e); 0 }
);
```

#### `meta` — Attribute Metadata

```rust
macro_rules! attach_attr {
    (#[$attr:meta] $item:item) => {
        #[$attr]
        $item
    };
}

attach_attr!(
    #[derive(Debug, Clone)]
    struct Point { x: f64, y: f64 }
);
```

---

## 6. Repetition Operators

### The Problem Repetition Solves

Without repetition, you cannot write a macro that handles a variable number of arguments.

```rust
// WITHOUT repetition — fixed arity only
macro_rules! sum_two { ($a:expr, $b:expr) => { $a + $b }; }
macro_rules! sum_three { ($a:expr, $b:expr, $c:expr) => { $a + $b + $c }; }
// This approach scales terribly!

// WITH repetition — any number of args!
macro_rules! sum {
    ($($x:expr),*) => {
        0 $(+ $x)*
    };
}
sum!(1, 2, 3, 4, 5)  // works!
```

### Repetition Syntax

```
$( PATTERN ) SEPARATOR QUANTIFIER

         $  ( $x:expr )  ,   *
         │       │        │   │
         │       │        │   └── quantifier: * = zero or more
         │       │        └────── separator token between repetitions
         │       └─────────────── the pattern to repeat
         └─────────────────────── opens a repetition block
```

### The Three Quantifiers

```
┌────────────┬──────────────────────┬─────────────────────────────┐
│ Quantifier │ Meaning              │ Matches                     │
├────────────┼──────────────────────┼─────────────────────────────┤
│    *        │ Zero or more        │ (), (a), (a,b), (a,b,c)...  │
│    +        │ One or more         │ (a), (a,b), (a,b,c)...      │
│    ?        │ Zero or one (opt.)  │ () or (a) only              │
└────────────┴──────────────────────┴─────────────────────────────┘
```

### Building `vec!` from Scratch

The standard library's `vec!` macro is the canonical example of repetition:

```rust
macro_rules! my_vec {
    // Pattern: zero or more expressions, separated by commas
    ( $($element:expr),* ) => {
        {
            // Use a block so we can have multiple statements
            let mut v = Vec::new();
            // Repeat the push for each captured element
            $(
                v.push($element);
            )*
            v  // return the vec
        }
    };
    
    // Handle trailing comma: my_vec![1, 2, 3,]
    ( $($element:expr),+ , ) => {
        my_vec![$($element),+]  // delegate to the arm above
    };
}

fn main() {
    let v = my_vec![1, 2, 3, 4, 5];
    println!("{:?}", v);  // [1, 2, 3, 4, 5]
    
    let empty: Vec<i32> = my_vec![];  // works! (zero or more)
}
```

```
EXPANSION of my_vec![1, 2, 3]:

Pattern:   $($element:expr),*
Captures:  $element = [1, 2, 3]  (as a sequence)

Expansion step:
    let mut v = Vec::new();
    ┌─ repeat block ─────────────────────────┐
    │  v.push(1);   ← $element = 1, iteration 1 │
    │  v.push(2);   ← $element = 2, iteration 2 │
    │  v.push(3);   ← $element = 3, iteration 3 │
    └────────────────────────────────────────┘
    v
```

### Repetition with Separators — Key Rules

```rust
// COMMA separator — most common
macro_rules! print_all {
    ($($x:expr),*) => {
        $(println!("{}", $x);)*
    };
}

// SEMICOLON separator
macro_rules! run_all {
    ($($stmt:stmt);*) => {
        $($stmt;)*
    };
}

// NO separator — token streams glued together
macro_rules! concat_idents {
    ($($id:ident)*) => {
        // NOT valid Rust (identifiers can't be concatenated this way in macro_rules!)
        // This shows the syntax, but concat_idents is a nightly feature
    };
}

// NESTED repetitions
macro_rules! matrix {
    ( $( [ $($x:expr),* ] ),* ) => {
        vec![ $( vec![$($x),*] ),* ]
    };
}

let m = matrix!([1, 2, 3], [4, 5, 6], [7, 8, 9]);
// Produces: vec![vec![1,2,3], vec![4,5,6], vec![7,8,9]]
```

### The `?` Quantifier — Optional Arguments

```rust
macro_rules! log {
    ($level:expr, $msg:expr $(, $arg:expr)*) => {
        println!("[{}] {}", $level, format!($msg $(, $arg)*));
    };
}

log!("INFO", "Server started");              // no extra args
log!("ERROR", "Failed at line {}", 42);      // one extra arg
log!("DEBUG", "{} + {} = {}", 1, 2, 3);      // multiple extra args


// Optional trailing context with ?
macro_rules! make_point {
    ($x:expr, $y:expr $(, $z:expr)?) => {
        {
            let _z: f64 = 0.0 $(+ $z as f64 - 0.0)?;  // tricky: use ? in expansion too
            ($x, $y)
        }
    };
}
```

---

## 7. Multiple Match Arms — Pattern Dispatching

### How Arms Work

`macro_rules!` tries each arm **in order from top to bottom**. The first arm whose pattern matches the input wins. This is like Rust's `match` statement but for syntax.

```
macro_rules! my_macro {         Input tokens
    (arm 1 pattern) => { ... }      │
    (arm 2 pattern) => { ... }      │
    (arm 3 pattern) => { ... }      ▼
}                           ┌───────────────┐
                            │ Try arm 1?    │──── No match ──┐
                            └───────────────┘                │
                                                             ▼
                                                    ┌───────────────┐
                                                    │ Try arm 2?    │──── No match ──┐
                                                    └───────────────┘                │
                                                                                     ▼
                                                                            ┌───────────────┐
                                                                            │ Try arm 3?    │
                                                                            └───────────────┘
                                                                                    │
                                                                              Match! Use this
                                                                              expansion.
```

### A Classic Multi-Arm Macro — `assert_eq!` Style

```rust
macro_rules! my_assert {
    // Arm 1: assert with custom message
    ($left:expr, $right:expr, $msg:literal) => {
        if $left != $right {
            panic!("Assertion failed: {} != {} — {}", $left, $right, $msg);
        }
    };
    
    // Arm 2: assert without message (must come AFTER the one with message)
    ($left:expr, $right:expr) => {
        my_assert!($left, $right, "values are not equal");
    };
}

my_assert!(1 + 1, 2);                          // uses arm 2, delegates to arm 1
my_assert!(2 * 3, 6, "multiplication broken"); // uses arm 1 directly
```

> **Order Matters!** Always put more specific patterns BEFORE more general ones.
> If you put `($a:expr)` before `($a:expr, $b:expr)`, the former will never match
> a two-argument call because... wait, actually arms require exact structural matches.
> But with repetitions, ordering is critical.

### Keyword-Based Dispatch

One powerful pattern is using literal keywords to differentiate behavior:

```rust
macro_rules! collection {
    // Dispatch on the keyword before the colon
    (stack: $($item:expr),*) => {
        {
            let mut s: Vec<_> = Vec::new();
            $(s.push($item);)*
            s  // acts as LIFO stack
        }
    };
    
    (queue: $($item:expr),*) => {
        {
            use std::collections::VecDeque;
            let mut q = VecDeque::new();
            $(q.push_back($item);)*
            q
        }
    };
    
    (set: $($item:expr),*) => {
        {
            use std::collections::HashSet;
            let mut s = HashSet::new();
            $(s.insert($item);)*
            s
        }
    };
}

let stack = collection!(stack: 1, 2, 3);
let queue = collection!(queue: "a", "b", "c");
let set   = collection!(set: 10, 20, 30, 10);  // dedup automatically
```

---

## 8. Recursive Macros

### What is Recursion in Macros?

A macro can call **itself** in its expansion. This allows processing lists of items one-by-one, which is impossible with simple repetition when each step needs context from previous steps.

### Mental Model: Macro Recursion as List Processing

```
Processing list [1, 2, 3] recursively:

Step 1: head=1, tail=[2, 3]
    → process 1, then recurse with [2, 3]

Step 2: head=2, tail=[3]
    → process 2, then recurse with [3]

Step 3: head=3, tail=[]
    → process 3, then hit BASE CASE

Step 4: BASE CASE (empty list)
    → return
```

### Recursive Sum Macro

```rust
macro_rules! recursive_sum {
    // Base case: no arguments → return 0
    () => { 0 };
    
    // Recursive case: take first element, add to sum of rest
    ($head:expr $(, $tail:expr)*) => {
        $head + recursive_sum!($($tail),*)
        //                    ^^^^^^^^^^
        //                    passes remaining args to self
    };
}

fn main() {
    let s = recursive_sum!(1, 2, 3, 4, 5);
    // Expands as:
    // 1 + recursive_sum!(2, 3, 4, 5)
    // 1 + (2 + recursive_sum!(3, 4, 5))
    // 1 + (2 + (3 + recursive_sum!(4, 5)))
    // 1 + (2 + (3 + (4 + recursive_sum!(5))))
    // 1 + (2 + (3 + (4 + (5 + recursive_sum!()))))
    // 1 + (2 + (3 + (4 + (5 + 0))))
    // = 15
}
```

### Recursion Limit

Rust has a default recursion limit of **128** for macros. You can increase it:

```rust
#![recursion_limit = "256"]  // place at crate root (main.rs or lib.rs)
```

### TT Muncher Pattern — Advanced Recursion

A **TT Muncher** is a recursive macro that consumes ("munches") tokens one at a time from the front. This is the most powerful pattern in `macro_rules!`.

```
TT MUNCHER VISUALIZATION:

Input tokens: [A B C D]
                │
         ┌──────┘ munch A
         │ recurse with [B C D]
         │      │
         │      └──────┘ munch B
         │        recurse with [C D]
         │              │
         │              └──────┘ munch C
         │                recurse with [D]
         │                      │
         │                      └──────┘ munch D
         │                        recurse with []
         │                              │
         │                              └──── BASE CASE: [] done!
         │                              ▲
         │                        ──────┘  each step processes one token
         │                                 then passes the rest recursively
```

```rust
// TT Muncher: builds a HashMap from key => value pairs
macro_rules! hashmap {
    // Base case: no more tokens, return the map
    (@collect $map:expr,) => { $map };
    
    // Recursive case: consume one "key => value," pair
    (@collect $map:expr, $key:expr => $value:expr, $($rest:tt)*) => {
        {
            $map.insert($key, $value);
            hashmap!(@collect $map, $($rest)*)
        }
    };
    
    // Entry point: create the map and start collecting
    ($($rest:tt)*) => {
        {
            let mut map = std::collections::HashMap::new();
            hashmap!(@collect map, $($rest)*)
            // the @collect is an internal rule (see section 11)
        }
    };
}

// But wait — can't mutate across recursive blocks like this.
// Let's use a cleaner version with vec-to-map:

macro_rules! map {
    ($($key:expr => $val:expr),* $(,)?) => {
        {
            let mut m = std::collections::HashMap::new();
            $(m.insert($key, $val);)*
            m
        }
    };
}

let scores = map!{
    "Alice" => 95,
    "Bob"   => 87,
    "Carol" => 92,
};
```

---

## 9. Macro Hygiene

### What is Hygiene?

**Hygiene** means that variables defined INSIDE a macro expansion cannot accidentally clash with variables in the code that calls the macro.

Without hygiene, macros would be dangerous — imagine a macro secretly creating a variable `x` that shadows your own `x`.

### The Problem Hygiene Solves (C preprocessor analogy)

In C, macros are simple text substitution — NO hygiene:

```c
// C macro (NOT Rust) — dangerous text substitution
#define DOUBLE(x) x * 2

// Caller code:
int result = DOUBLE(y + 1);
// Expands to: y + 1 * 2  ← WRONG! (operator precedence disaster)

// Even worse:
#define SWAP(a, b) { int tmp = a; a = b; b = tmp; }
int tmp = 5;
SWAP(tmp, other);  // tmp inside macro shadows outer tmp — BUG!
```

### How Rust's Hygiene Works

In Rust's `macro_rules!`, every identifier introduced in a macro expansion gets a unique **syntax context** — an invisible tag that distinguishes "macro-defined `x`" from "caller-defined `x`".

```rust
macro_rules! create_variable {
    () => {
        let x = 42;  // This 'x' is tagged with the macro's context
        println!("Inside macro: x = {}", x);
    };
}

fn main() {
    let x = 100;           // This 'x' has the caller's context
    create_variable!();    // Introduces a DIFFERENT 'x' — no conflict!
    println!("Outside: x = {}", x);  // Still 100!
}

// Output:
// Inside macro: x = 42
// Outside: x = 100
```

```
HYGIENE VISUALIZATION:

Caller scope:
    let x[caller_ctx] = 100;
    
    ┌── macro expansion ────────────────────┐
    │   let x[macro_ctx] = 42;              │ ← different context!
    │   println!("{}", x[macro_ctx]);        │
    └────────────────────────────────────────┘
    
    println!("{}", x[caller_ctx]);          ← still sees caller's x
```

### Breaking Hygiene Intentionally

Sometimes you WANT the macro to define a variable that the caller can use. You do this by accepting the identifier as a parameter:

```rust
macro_rules! make_counter {
    ($name:ident) => {
        // $name comes from the CALLER's context
        let mut $name = 0;
        // Now caller can use it after the macro
    };
}

fn main() {
    make_counter!(count);  // caller passes "count" as the name
    count += 1;
    count += 1;
    println!("Count: {}", count);  // 2 — works! No hygiene violation
}
```

### The `$crate` Special Metavariable

When your macro references items from its own crate (library), you need `$crate` to ensure they resolve correctly regardless of where the macro is called from:

```rust
// In your library crate (my_lib)
macro_rules! create_error {
    ($msg:expr) => {
        // WITHOUT $crate — might fail if user doesn't have MyError in scope
        MyError::new($msg)
        
        // WITH $crate — always finds MyError in your crate
        $crate::MyError::new($msg)
    };
}
```

---

## 10. Scoping and Exporting Macros

### Default Scope: Local to Module

By default, a macro defined in a module is only usable AFTER its definition, within the same scope:

```rust
mod my_mod {
    macro_rules! local_macro {
        () => { println!("local!"); }
    }
    
    fn use_it() {
        local_macro!();  // OK — after definition, same module
    }
}

fn main() {
    // my_mod::local_macro!();  // ERROR — not exported
}
```

### `#[macro_export]` — Make it Public

```rust
// In lib.rs or any module
#[macro_export]
macro_rules! public_macro {
    () => { println!("I'm public!"); }
}

// This macro is now available at the CRATE ROOT
// Users of your crate write:
use my_crate::public_macro;  // or just rely on the implicit import
```

```
WITHOUT #[macro_export]:          WITH #[macro_export]:

my_crate                          my_crate
  └── mod utils                     ├── public_macro!  ← hoisted to root
        └── macro not_exported!     └── mod utils
              (only usable in             └── macro public_macro! (original)
               utils module)
```

### `#[macro_use]` — Import All Macros from a Crate (old style)

```rust
// Old way (Rust 2015 edition)
#[macro_use]
extern crate serde;

// New way (Rust 2018+ edition) — preferred
use serde::{Serialize, Deserialize};
```

### `#[macro_use] mod` — Re-export Macros Within Your Crate

```rust
// src/lib.rs
#[macro_use]
mod macros;  // all macros from macros.rs are now available in lib.rs and submodules

mod server;  // can use macros from macros.rs here
mod client;  // and here
```

---

## 11. Advanced Patterns

### Pattern 1: Internal Rules with `@`

When a macro needs multiple "phases" of processing, use internal rules. The `@` prefix is a convention (not enforced by Rust) to mark rules as "internal" — they should only be called by the macro itself.

```rust
macro_rules! process_items {
    // PUBLIC entry point — what callers use
    ($($item:expr),*) => {
        process_items!(@init [] $($item),*)
    };
    
    // INTERNAL: accumulation phase
    (@init [$($acc:expr),*] $head:expr, $($rest:expr),*) => {
        process_items!(@init [$($acc,)* $head * 2] $($rest),*)
    };
    
    // INTERNAL: base case — no more items
    (@init [$($acc:expr),*]) => {
        vec![$($acc),*]
    };
    
    // INTERNAL: base case with one remaining item
    (@init [$($acc:expr),*] $last:expr) => {
        process_items!(@init [$($acc,)* $last * 2])
    };
}

let result = process_items!(1, 2, 3, 4);
// Result: [2, 4, 6, 8]
```

```
INTERNAL RULE FLOW:

process_items!(1, 2, 3)
       │
       ▼ entry point dispatches to @init
process_items!(@init [] 1, 2, 3)
       │
       ▼ munch 1
process_items!(@init [2] 2, 3)
       │
       ▼ munch 2
process_items!(@init [2, 4] 3)
       │
       ▼ last item
process_items!(@init [2, 4, 6])
       │
       ▼ base case
vec![2, 4, 6]
```

### Pattern 2: Push-Down Accumulation

Accumulate results by passing a growing buffer through recursive calls:

```rust
macro_rules! reverse {
    // Entry: start with empty accumulator
    ($($x:tt)*) => {
        reverse!(@acc [] $($x)*)
    };
    
    // Take first token, prepend to accumulator
    (@acc [$($acc:tt)*] $head:tt $($tail:tt)*) => {
        reverse!(@acc [$head $($acc)*] $($tail)*)
    };
    
    // Base case: nothing left, return accumulator
    (@acc [$($acc:tt)*]) => {
        stringify!($($acc)*)
    };
}

// reverse!(a b c d) → "d c b a"
```

### Pattern 3: The Callback Pattern

Pass a "continuation" macro as an argument for composition:

```rust
macro_rules! apply_to_each {
    ($callback:ident, $($x:expr),*) => {
        $($callback!($x);)*
    };
}

macro_rules! print_doubled {
    ($x:expr) => { println!("{}", $x * 2); }
}

apply_to_each!(print_doubled, 1, 2, 3, 4, 5);
// Prints: 2, 4, 6, 8, 10
```

### Pattern 4: Counting Macro Arguments

```rust
// Using a trick: replace each token with 1, then sum
macro_rules! count {
    () => { 0usize };
    ($head:tt $($tail:tt)*) => { 1usize + count!($($tail)*) };
}

// More efficient version — compile-time array length trick
macro_rules! count_efficient {
    ($($x:tt)*) => {
        <[()]>::len(&[$(count_efficient!(@replace $x ()),)*])
    };
    (@replace $_t:tt $sub:expr) => { $sub };
}

fn main() {
    println!("{}", count!(a b c d e));  // 5
}
```

### Pattern 5: Generating Repetitive Code (The `impl` Factory)

```rust
macro_rules! impl_display_for_wrapper {
    ($($type:ty),*) => {
        $(
            impl std::fmt::Display for $type {
                fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
                    write!(f, "{}", self.0)
                }
            }
        )*
    };
}

struct Meters(f64);
struct Kilograms(f64);
struct Seconds(f64);

impl_display_for_wrapper!(Meters, Kilograms, Seconds);

fn main() {
    println!("{}", Meters(5.0));      // "5"
    println!("{}", Kilograms(70.0));  // "70"
}
```

### Pattern 6: DSL (Domain-Specific Language) Creation

```rust
// A mini SQL-like DSL macro
macro_rules! query {
    (SELECT $($field:ident),+ FROM $table:ident WHERE $condition:expr) => {
        {
            println!("Fields: {:?}", stringify!($($field),+));
            println!("Table: {}", stringify!($table));
            println!("Condition: {}", stringify!($condition));
            // In real code: build a Query struct here
        }
    };
    
    (SELECT * FROM $table:ident) => {
        {
            println!("Select all from: {}", stringify!($table));
        }
    };
}

query!(SELECT name, age FROM users WHERE age > 18);
query!(SELECT * FROM products);
```

---

## 12. Real-World Implementations

### 1. Error Handling Macro (Production Pattern)

```rust
/// Propagates errors with context, like the ? operator but with logging
macro_rules! try_with_context {
    ($expr:expr, $context:literal) => {
        match $expr {
            Ok(val) => val,
            Err(e) => {
                eprintln!("[ERROR] {}: {}", $context, e);
                return Err(e.into());
            }
        }
    };
    
    ($expr:expr, $context:expr) => {
        match $expr {
            Ok(val) => val,
            Err(e) => {
                eprintln!("[ERROR] {}: {}", $context, e);
                return Err(e.into());
            }
        }
    };
}

fn read_config(path: &str) -> Result<String, Box<dyn std::error::Error>> {
    let content = try_with_context!(
        std::fs::read_to_string(path),
        "Failed to read config file"
    );
    let parsed = try_with_context!(
        serde_json::from_str::<serde_json::Value>(&content),
        "Config file is not valid JSON"
    );
    Ok(parsed.to_string())
}
```

### 2. Benchmark Timing Macro

```rust
macro_rules! time_it {
    ($label:expr, $block:block) => {
        {
            let start = std::time::Instant::now();
            let result = $block;
            let elapsed = start.elapsed();
            println!("[BENCH] {}: {:.3}ms", $label, elapsed.as_secs_f64() * 1000.0);
            result
        }
    };
}

fn main() {
    let sum = time_it!("compute sum", {
        (0..1_000_000u64).sum::<u64>()
    });
    println!("Sum: {}", sum);
    // Output:
    // [BENCH] compute sum: 1.234ms
    // Sum: 499999500000
}
```

### 3. Builder Pattern Generator

```rust
macro_rules! builder {
    (
        struct $name:ident {
            $( $field:ident : $type:ty ),* $(,)?
        }
    ) => {
        // The actual struct
        #[derive(Debug)]
        pub struct $name {
            $( pub $field: $type, )*
        }
        
        // The builder struct
        #[derive(Default, Debug)]
        pub struct paste::paste! { [<$name Builder>] } {
            $( $field: Option<$type>, )*
        }
        
        impl $name {
            pub fn builder() -> paste::paste! { [<$name Builder>] } {
                Default::default()
            }
        }
        
        impl paste::paste! { [<$name Builder>] } {
            $(
                pub fn $field(mut self, val: $type) -> Self {
                    self.$field = Some(val);
                    self
                }
            )*
            
            pub fn build(self) -> Result<$name, &'static str> {
                Ok($name {
                    $(
                        $field: self.$field.ok_or(concat!("missing field: ", stringify!($field)))?,
                    )*
                })
            }
        }
    };
}

// Usage (requires `paste` crate for identifier concatenation):
// builder! {
//     struct HttpRequest {
//         url: String,
//         method: String,
//         timeout_ms: u64,
//     }
// }
//
// let req = HttpRequest::builder()
//     .url("https://api.example.com".to_string())
//     .method("GET".to_string())
//     .timeout_ms(5000)
//     .build()
//     .unwrap();
```

### 4. Enum with String Conversion

```rust
macro_rules! string_enum {
    (
        $(#[$attr:meta])*
        $vis:vis enum $name:ident {
            $($variant:ident => $string:literal),* $(,)?
        }
    ) => {
        $(#[$attr])*
        $vis enum $name {
            $($variant,)*
        }
        
        impl $name {
            pub fn as_str(&self) -> &'static str {
                match self {
                    $(Self::$variant => $string,)*
                }
            }
        }
        
        impl std::fmt::Display for $name {
            fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
                f.write_str(self.as_str())
            }
        }
        
        impl std::str::FromStr for $name {
            type Err = String;
            fn from_str(s: &str) -> Result<Self, Self::Err> {
                match s {
                    $($string => Ok(Self::$variant),)*
                    other => Err(format!("Unknown {}: '{}'", stringify!($name), other)),
                }
            }
        }
    };
}

string_enum! {
    #[derive(Debug, Clone, PartialEq)]
    pub enum HttpMethod {
        Get    => "GET",
        Post   => "POST",
        Put    => "PUT",
        Delete => "DELETE",
        Patch  => "PATCH",
    }
}

fn main() {
    let method = HttpMethod::Post;
    println!("{}", method);               // "POST"
    
    let parsed: HttpMethod = "GET".parse().unwrap();
    assert_eq!(parsed, HttpMethod::Get);
}
```

### 5. Test Helper Macro

```rust
macro_rules! parametrized_test {
    (
        $test_fn:ident,
        $( ($test_name:ident: $($arg:expr),+) ),* $(,)?
    ) => {
        $(
            #[test]
            fn $test_name() {
                $test_fn($($arg),+);
            }
        )*
    };
}

fn check_palindrome(s: &str, expected: bool) {
    let is_palindrome = s == s.chars().rev().collect::<String>();
    assert_eq!(is_palindrome, expected, "Failed for input: {:?}", s);
}

parametrized_test!(
    check_palindrome,
    (test_racecar:    "racecar",    true),
    (test_hello:      "hello",      false),
    (test_level:      "level",      true),
    (test_world:      "world",      false),
    (test_empty:      "",           true),
    (test_single:     "a",          true),
);

// Generates:
// #[test] fn test_racecar() { check_palindrome("racecar", true); }
// #[test] fn test_hello()   { check_palindrome("hello",   false); }
// ... etc
```

### 6. State Machine Definition Macro

```rust
macro_rules! state_machine {
    (
        $name:ident {
            states: [$($state:ident),+],
            initial: $initial:ident,
            transitions: [
                $($from:ident --[$event:ident]--> $to:ident),+ $(,)?
            ]
        }
    ) => {
        #[derive(Debug, Clone, PartialEq)]
        pub enum $name {
            $($state,)+
        }
        
        impl $name {
            pub fn initial() -> Self {
                Self::$initial
            }
            
            pub fn transition(&self, event: &str) -> Option<Self> {
                match (self, event) {
                    $(
                        (Self::$from, stringify!($event)) => Some(Self::$to),
                    )+
                    _ => None,
                }
            }
        }
    };
}

state_machine! {
    TrafficLight {
        states: [Red, Yellow, Green],
        initial: Red,
        transitions: [
            Red    --[go]-->   Green,
            Green  --[slow]--> Yellow,
            Yellow --[stop]--> Red,
        ]
    }
}

fn main() {
    let mut light = TrafficLight::initial();
    println!("{:?}", light);  // Red
    
    light = light.transition("go").unwrap();
    println!("{:?}", light);  // Green
    
    light = light.transition("slow").unwrap();
    println!("{:?}", light);  // Yellow
}
```

### 7. Lazy Static Initialization (understanding `lazy_static!`)

```rust
// Simplified version of what lazy_static! does internally
macro_rules! my_lazy_static {
    (static ref $name:ident : $type:ty = $init:expr ;) => {
        static $name: once_cell::sync::Lazy<$type> = 
            once_cell::sync::Lazy::new(|| $init);
    };
}

// With std only (no external crates), using std::sync::OnceLock:
macro_rules! lazy_global {
    (static $name:ident : $type:ty = $init:expr ;) => {
        static $name: std::sync::OnceLock<$type> = std::sync::OnceLock::new();
        
        // Note: This is simplified; real version would use a wrapper type
    };
}
```

---

## 13. Debugging Macros

### Tool 1: `cargo expand`

The most important tool for macro debugging. It shows the fully expanded output.

```bash
# Install
cargo install cargo-expand

# Expand a specific file
cargo expand

# Expand with a filter
cargo expand my_module::my_function
```

**Before expand:**
```rust
let v = vec![1, 2, 3];
```

**After expand:**
```rust
let v = {
    let mut temp_vec = ::alloc::vec::Vec::new();
    temp_vec.push(1);
    temp_vec.push(2);
    temp_vec.push(3);
    temp_vec
};
```

### Tool 2: `stringify!` — Print What You Got

```rust
macro_rules! debug_input {
    ($($x:tt)*) => {
        // stringify! converts tokens back to a string at compile time
        compile_error!(concat!("Got: ", stringify!($($x)*)));
        
        // Or at runtime:
        println!("Received tokens: {}", stringify!($($x)*));
    };
}
```

### Tool 3: `trace_macros!` (Nightly)

```rust
#![feature(trace_macros)]

trace_macros!(true);    // turn on tracing
my_macro!(1, 2, 3);     // compiler prints each expansion step
trace_macros!(false);   // turn off
```

### Tool 4: Compile-Time Error Messages

```rust
macro_rules! must_be_positive {
    ($x:expr) => {
        {
            let val = $x;
            if val <= 0 {
                panic!("Expected positive value, got: {}", val);
            }
            val
        }
    };
}
```

### Common Error Messages and What They Mean

```
error: no rules expected the token `X`
→ None of your macro arms matched the input.
  Check: Is the input syntax correct? Did you forget a comma? Wrong token type?

error: `$x:expr` is followed by `$y:expr` which is not allowed
→ Two expression fragments back-to-back are ambiguous.
  Fix: Put a separator (comma, semicolon) between them.

error: local ambiguity: multiple parsing options
→ The parser can't decide which arm to use.
  Fix: Make arms more structurally distinct, or reorder them.

error: attempted to repeat an expression containing no syntax variables
→ You have $(...) in expansion that doesn't reference a variable from the pattern.
  Fix: Ensure the repetition variable is inside the $()*  block.
```

---

## 14. Common Pitfalls

### Pitfall 1: Expression Evaluation — Multiple Evaluation

```rust
// DANGEROUS macro — evaluates $x TWICE
macro_rules! bad_increment {
    ($x:expr) => {
        $x + 1
        // If $x has side effects (e.g., a function call), 
        // it will be called multiple times
    };
}

let mut counter = 0;
let next = bad_increment!({ counter += 1; counter });
// counter is now 1 (incremented during evaluation)
// but bad_increment evaluates the block ONCE here

// In more complex macros:
macro_rules! bad_max {
    ($a:expr, $b:expr) => {
        if $a > $b { $a } else { $b }
        //    ^^       ^^  both evaluate $a TWICE
    };
}

// FIX: Bind to local variables first
macro_rules! good_max {
    ($a:expr, $b:expr) => {
        {
            let a = $a;  // evaluate once
            let b = $b;  // evaluate once
            if a > b { a } else { b }
        }
    };
}
```

### Pitfall 2: Ambiguity with Separators

```rust
// This FAILS — Rust can't tell where one arm ends and another begins
// because expr can consume the comma
macro_rules! ambiguous {
    ($a:expr, $b:expr) => { ... };
    ($a:expr) => { ... };
}

// When called as: ambiguous!(foo, bar)
// Is this arm 1 with two exprs, or arm 2 where foo,bar is one expr?
// Rust handles this with Follow-set restrictions — expr cannot be followed
// by certain tokens (comma IS allowed after expr in most cases, so this 
// specific example works; but other combinations may not)
```

### Pitfall 3: Identifier Hygiene Breaking Unexpectedly

```rust
// This looks like it should work but hygiene prevents it
macro_rules! for_loop_macro {
    ($iter:expr, $body:block) => {
        for i in $iter {  // 'i' is hygienic — caller CANNOT see it!
            $body
        }
    };
}

for_loop_macro!(0..5, {
    println!("{}", i);  // ERROR! 'i' not in scope — it's hygienically isolated
});

// FIX: Pass the variable name as a parameter
macro_rules! for_loop_macro_fixed {
    ($var:ident in $iter:expr, $body:block) => {
        for $var in $iter {  // $var comes from caller's context
            $body
        }
    };
}

for_loop_macro_fixed!(i in 0..5, {
    println!("{}", i);  // Works!
});
```

### Pitfall 4: Trailing Comma Handling

Always support optional trailing commas — it's idiomatic Rust:

```rust
// Without trailing comma support:
macro_rules! strict_vec {
    ($($x:expr),*) => { vec![$($x),*] };
}
strict_vec![1, 2, 3,]  // ERROR — trailing comma not allowed

// With trailing comma support (best practice):
macro_rules! flexible_vec {
    ($($x:expr),* $(,)?) => { vec![$($x),*] };
    //            ^^^^^ optional trailing comma
}
flexible_vec![1, 2, 3,]   // OK
flexible_vec![1, 2, 3]    // Also OK
```

### Pitfall 5: Fragment Specifier Follow Sets

Certain fragment types can only be followed by certain tokens. This is a compile-time rule:

```
Fragment  │ Can be followed by
──────────┼────────────────────────────────────────
expr      │ => , ;
pat       │ => , = | if in
ty        │ => , ; = | { [ : > as where
ident     │ Anything
block     │ Anything
stmt      │ Anything
tt        │ Anything
```

```rust
// This FAILS:
macro_rules! broken {
    ($e:expr $f:expr) => { ... };  // expr cannot be followed by expr
}

// This WORKS:
macro_rules! fixed {
    ($e:expr, $f:expr) => { ... };  // comma separator is valid after expr
}
```

---

## 15. Mental Models and Mastery Path

### The Three Mental Models for Macro Mastery

#### Mental Model 1: "Macros are Syntax Functions"

Think of a macro as a function that takes syntax (not values) and returns syntax:

```
Input:  Token stream that matches a pattern
Output: New token stream (valid Rust code)

my_macro!(a, b, c)
    │
    │   [pattern matching on token structure]
    │
    ▼
println!("{}", a);
println!("{}", b);
println!("{}", c);
```

#### Mental Model 2: "Macro Arms are a Decision Tree"

```
Call: my_macro!(arg1, arg2)
              │
    ┌─────────▼────────────────┐
    │   Try Arm 1              │
    │   Pattern: ($x:expr)     │
    │   Matches? NO (2 args)   │
    └─────────┬────────────────┘
              │ try next
    ┌─────────▼────────────────────────────┐
    │   Try Arm 2                          │
    │   Pattern: ($x:expr, $y:expr)        │
    │   Matches? YES                       │
    │   $x = arg1, $y = arg2              │
    └─────────┬────────────────────────────┘
              │ expand
              ▼
         Expansion code with $x and $y substituted
```

#### Mental Model 3: "Repetitions are Zippers"

When you have multiple repetition variables, they are "zipped" together and must have the same count:

```rust
macro_rules! zip_map {
    ($($key:expr => $val:expr),*) => {
        // $key and $val are "zipped" — same length
        // In expansion, they iterate in lockstep:
        vec![ $( ($key, $val) ),* ]
        //         ^^^^  ^^^^
        //         iteration 1: (key1, val1)
        //         iteration 2: (key2, val2)
        //         ...
    };
}
```

```
key sequence:  [k1, k2, k3]
val sequence:  [v1, v2, v3]
                │    │    │
                ▼    ▼    ▼
Zipper:       (k1,v1) (k2,v2) (k3,v3)
```

### The Progression Path to Mastery

```
LEVEL 1 — Reader           LEVEL 2 — Writer          LEVEL 3 — Architect
───────────────────────    ──────────────────────     ─────────────────────────
Understand vec![]          Write simple macros        Design DSLs with macros
Understand println!{}      Use all fragment types      TT muncher pattern
Understand assert_eq!      Handle repetition          Internal rules (@)
                           Multiple arms              Push-down accumulation
                           Basic recursion            Macro composition
                                                      Debugging mastery
                           
LEVEL 4 — Expert
──────────────────────────────────────────────────
Know exactly when NOT to use macros (use traits/generics instead)
Combine macro_rules! with procedural macros
Understand macro hygiene edge cases
Write macros that generate optimal code
Contribute to open-source Rust crates with macros
```

### Deliberate Practice Exercises

```
Week 1 — Foundations:
  □ Implement your own println!-like macro with format string support
  □ Implement my_vec! with trailing comma support
  □ Write a map! macro for HashMap creation

Week 2 — Repetition:
  □ Write a macro that generates N struct fields from a list
  □ Implement a matches_any! macro: matches_any!(x, 1 | 2 | 3)
  □ Write a zip! macro for two lists

Week 3 — Recursion:
  □ Implement a compile-time max! for any number of args
  □ Write a flatten! macro that flattens nested expressions
  □ Build a TT muncher that parses custom syntax

Week 4 — Real World:
  □ Generate a full CRUD interface from a struct definition
  □ Build a state machine DSL
  □ Create a test harness with parametrized tests
```

### Cognitive Principles for Macro Mastery

1. **Chunking (George Miller, 1956):** Internalize each fragment specifier as a chunk. 
   Don't think "dollar sign, x, colon, expr" — think "expr-binding". 
   Once each piece is a chunk, you can reason at higher levels.

2. **Deliberate Practice (Anders Ericsson):** Don't just USE macros — 
   *study existing macros in the standard library*. Run `cargo expand` on `vec![]`, 
   `println!`, `assert_eq!`. Understand every token of the expansion.

3. **Desirable Difficulty:** Write macros for things you COULD do with functions. 
   Then ask: "Is this actually better?" This builds judgment about when macros ARE
   the right tool.

4. **Interleaving:** Mix macro writing with reading the Rust Reference on macros 
   (https://doc.rust-lang.org/reference/macros-by-example.html). 
   Don't block-practice one alone.

5. **Transfer:** Every pattern in `macro_rules!` has an analogy in functional programming.
   Pattern matching on syntax = pattern matching on data. Recursion = recursion.
   Repetition = map/fold. See the connections.

---

## Quick Reference Card

```
┌──────────────────────────────────────────────────────────────────┐
│                     macro_rules! CHEAT SHEET                     │
├──────────────────────────────────────────────────────────────────┤
│ DEFINE:    macro_rules! name { (pattern) => { expansion }; }     │
│ CALL:      name!(...) or name![...] or name!{...}                │
│                                                                  │
│ FRAGMENT SPECIFIERS:                                             │
│   expr     any expression       ident    identifier             │
│   ty        type                pat      pattern                 │
│   stmt     statement            block    { ... }                 │
│   path     a::b::C              meta     derive(Debug)           │
│   tt       any token tree       literal  42, "hi", true          │
│   vis      pub / pub(crate)     lifetime 'a, 'static             │
│                                                                  │
│ REPETITIONS:                                                     │
│   $( $x:expr ),*   zero or more, comma-separated                │
│   $( $x:expr ),+   one  or more, comma-separated                │
│   $( $x:expr )?    zero or one                                   │
│   no separator:    $( $x:tt )*  tokens glued together            │
│                                                                  │
│ SPECIAL VARIABLES:                                               │
│   $crate            crate root (for library macros)              │
│   stringify!($x)    converts tokens to &str at compile time      │
│   concat!(...)      concatenates string literals                 │
│                                                                  │
│ EXPORT:                                                          │
│   #[macro_export]   makes macro public from crate root           │
│                                                                  │
│ DEBUG:                                                           │
│   cargo expand      shows full macro expansion                   │
│   stringify!($x)    see what tokens you captured                 │
└──────────────────────────────────────────────────────────────────┘
```

---

*"A language that doesn't affect the way you think about programming is not worth knowing."*
*— Alan Perlis*

*`macro_rules!` is not just a feature of Rust. It is a window into a different way of thinking — where code itself is data, and transformation is computation. Master this, and you think like the compiler.*

Now let me create this comprehensive guide as a well-structured markdown document.Here is your complete `macro_rules!` guide. Let me walk you through what it covers and the mental architecture behind it.

---

## What's Inside — The Conceptual Map

```
macro_rules! MASTERY
        │
        ├── WHY MACROS EXIST
        │     └─ Code that writes code, runs at compile-time on the AST
        │        before type-checking. Zero runtime cost.
        │
        ├── THE ANATOMY
        │     └─ name + arms (pattern → expansion)
        │        Patterns match TOKEN STREAMS, not values
        │
        ├── FRAGMENT SPECIFIERS (12 total)
        │     ├─ expr   — any expression (captured as a unit)
        │     ├─ ident  — identifier (use to generate variable/fn names)
        │     ├─ ty     — types (generate impls for any type)
        │     ├─ tt     — wildcard token tree (most flexible)
        │     └─ 8 more (pat, stmt, block, path, meta, literal, vis, lifetime)
        │
        ├── REPETITION  $( ),*  $( ),+  $( )?
        │     └─ The superpower that makes variadic macros possible
        │
        ├── RECURSION + TT MUNCHER
        │     └─ Process token lists one-by-one, like a parser
        │
        ├── HYGIENE
        │     └─ Variables inside macros don't leak to callers
        │        Break it intentionally by accepting $name:ident
        │
        └── REAL-WORLD PATTERNS
              ├─ Error propagation with context
              ├─ Benchmarking
              ├─ Builder pattern generation
              ├─ Enum with string conversion
              ├─ Parametrized tests
              └─ State machine DSL
```

The single most important rule to internalize: **`expr` evaluates greedily and must never be used twice in expansion** — bind it to a local variable first. This alone prevents 80% of subtle macro bugs. The second most important rule: **always support trailing commas** with `$(,)?`.