# The `mod` Keyword in Rust — A Complete Deep-Dive Guide

> *"Modules are not just organization tools — they are the architecture of trust, visibility, and reasoning at scale."*

---

## Table of Contents

1. [What Is `mod`? — The Mental Model](#1-what-is-mod)
2. [Module Basics — Inline Modules](#2-inline-modules)
3. [File-Based Modules — The Module Tree & File System](#3-file-based-modules)
4. [Nested Modules — Hierarchical Namespacing](#4-nested-modules)
5. [Visibility & `pub` — The Privacy System](#5-visibility--pub)
6. [`pub(crate)`, `pub(super)`, `pub(in path)` — Scoped Visibility](#6-scoped-visibility)
7. [`use` Declarations — Bringing Names Into Scope](#7-use-declarations)
8. [`self`, `super`, `crate` — Path Qualifiers](#8-path-qualifiers)
9. [Re-exporting with `pub use`](#9-re-exporting-with-pub-use)
10. [The `mod.rs` Pattern vs. the Modern Pattern](#10-modrs-vs-modern-pattern)
11. [Module Splitting Across Files — Real-World Structure](#11-module-splitting-across-files)
12. [Modules and the Orphan Rule](#12-modules-and-the-orphan-rule)
13. [`#[cfg]` — Conditional Compilation with Modules](#13-cfg--conditional-compilation)
14. [Testing Modules — `#[cfg(test)]`](#14-testing-modules)
15. [Real-World Project Architectures](#15-real-world-project-architectures)
16. [Expert Patterns & Idioms](#16-expert-patterns--idioms)
17. [Common Pitfalls & How to Think Past Them](#17-common-pitfalls)
18. [Mental Model Summary](#18-mental-model-summary)

---

## 1. What Is `mod`?

`mod` declares a **module** — a named namespace that groups related items (functions, types, constants, traits, other modules) and controls their **visibility**.

Think of the Rust module system as a **tree of namespaces** rooted at the **crate root** (`main.rs` or `lib.rs`). Every item in your program lives at a specific path in this tree.

```
crate
 └── network
      ├── http
      │    ├── request()
      │    └── response()
      └── tcp
           └── connect()
```

The key insight experts hold: **modules are not about files — they are about the logical namespace tree.** Files are just one way to express that tree. This distinction is critical.

### Why Modules Matter Beyond Organization

1. **Encapsulation**: Items are private by default. Modules let you expose a clean, minimal API while hiding implementation details.
2. **Namespace collision prevention**: Two modules can each have a `parse()` function without conflict.
3. **Compiler reasoning**: The module boundary is where the borrow checker, type checker, and visibility rules operate. Understanding modules = understanding the compiler's trust model.
4. **Conditional compilation**: Modules can be included/excluded based on target platform or features.

---

## 2. Inline Modules

The simplest form — a module declared directly inside another file:

```rust
// src/main.rs or src/lib.rs

mod math {
    // Everything inside is private by default
    fn add(a: i32, b: i32) -> i32 {
        a + b
    }

    pub fn multiply(a: i32, b: i32) -> i32 {
        a * b
    }
}

fn main() {
    // math::add(1, 2);       // ERROR: `add` is private
    let result = math::multiply(3, 4); // OK: `multiply` is pub
    println!("{}", result);
}
```

### Key Properties of Inline Modules

- They share the **same file** as their parent.
- Items inside are **private to the module** by default — even the parent cannot access them without `pub`.
- They can be arbitrarily nested.

---

## 3. File-Based Modules

When a module grows large, move it to its own file. There are **two ways** to do this:

### Method A: `mod foo;` pointing to `foo.rs`

```
src/
├── main.rs
└── math.rs
```

```rust
// src/main.rs
mod math;   // ← Tells the compiler: "find `math` module in math.rs or math/mod.rs"

fn main() {
    println!("{}", math::multiply(3, 4));
}
```

```rust
// src/math.rs
pub fn multiply(a: i32, b: i32) -> i32 {
    a * b
}

fn internal_helper() -> i32 {
    42  // private — not accessible outside this module
}
```

### Method B: `mod foo;` pointing to `foo/mod.rs` (older pattern)

```
src/
├── main.rs
└── math/
    └── mod.rs
```

```rust
// src/math/mod.rs — same content as math.rs above
```

> **Rule**: `mod math;` at crate root causes the compiler to look for:
> 1. `src/math.rs`
> 2. `src/math/mod.rs`
>
> If both exist → **compile error**. Pick one.

### Critical Understanding

`mod math;` is a **declaration**, not an `include`. It tells the compiler:
- "A module named `math` exists."
- "Its content is defined in the file I point to."
- "That file becomes part of the module tree under the current module."

Without `mod math;` in any parent, `math.rs` is **completely ignored** by the compiler — even if the file exists.

---

## 4. Nested Modules

```rust
// src/lib.rs
mod network {
    pub mod http {
        pub fn get(url: &str) -> String {
            format!("GET {}", url)
        }

        pub mod headers {
            pub fn content_type() -> &'static str {
                "application/json"
            }
        }
    }

    pub mod tcp {
        pub fn connect(addr: &str) {
            println!("Connecting to {}", addr);
        }
    }
}

fn main() {
    let resp = network::http::get("https://example.com");
    let ct   = network::http::headers::content_type();
    network::tcp::connect("127.0.0.1:8080");
}
```

### Absolute vs. Relative Paths

```rust
mod outer {
    pub mod inner {
        pub fn hello() {}
    }

    pub fn call_absolute() {
        crate::outer::inner::hello();   // absolute path from crate root
    }

    pub fn call_relative() {
        self::inner::hello();           // relative to current module (outer)
        inner::hello();                 // same — implicit self
    }
}
```

---

## 5. Visibility & `pub`

Rust's privacy model: **everything is private by default** and visibility flows **outward**, never inward.

A parent module **can access** the private items of its children (with some nuance). Children **cannot** access private items of parents or siblings.

```rust
mod outer {
    fn private_outer() {}

    mod inner {
        fn private_inner() {}

        fn demo() {
            private_inner();        // OK — same module
            super::private_outer(); // OK — parent's private item is accessible via super
        }
    }

    fn demo() {
        private_outer();            // OK
        // inner::private_inner();  // ERROR: private to `inner`
    }
}
```

### Wait — can parents access children's privates?

**No.** The example above uses `super::` to access `private_outer` from within `inner`. The parent (`outer`) calling `inner::private_inner()` would fail because `private_inner` is private to `inner`.

```rust
mod outer {
    mod inner {
        fn secret() -> i32 { 42 }
    }
    fn try_access() {
        // inner::secret(); // ERROR: `secret` is private
    }
}
```

### Structs and Privacy — A Subtle Case

```rust
mod shapes {
    pub struct Circle {
        pub radius: f64,     // publicly accessible
        area_cache: f64,     // private field — even though struct is pub
    }

    impl Circle {
        pub fn new(radius: f64) -> Self {
            Circle {
                radius,
                area_cache: std::f64::consts::PI * radius * radius,
            }
        }

        pub fn area(&self) -> f64 {
            self.area_cache
        }
    }
}

fn main() {
    let c = shapes::Circle::new(5.0);
    println!("radius: {}", c.radius);   // OK — pub field
    // println!("{}", c.area_cache);    // ERROR — private field
}
```

### Enums Are Different

If an `enum` is `pub`, **all its variants are automatically `pub`**:

```rust
mod status {
    pub enum Status {
        Active,    // automatically pub
        Inactive,  // automatically pub
        Pending,   // automatically pub
    }
}
```

---

## 6. Scoped Visibility

Rust provides fine-grained visibility specifiers beyond just `pub`:

| Specifier | Accessible from |
|-----------|----------------|
| `pub` | Everywhere the item is reachable |
| `pub(crate)` | Anywhere within the current crate |
| `pub(super)` | Only the parent module |
| `pub(in path)` | Only the specified module path |
| *(nothing)* | Only the current module |

```rust
mod engine {
    pub(crate) struct EngineConfig {
        pub(crate) max_threads: usize,
        pub(super) debug_mode: bool,     // visible to parent of `engine`
        internal_id: u64,                // private to this module only
    }

    pub(in crate::engine) fn internal_reset() {
        // Only callable from within the `engine` module subtree
    }

    pub mod scheduler {
        pub fn schedule() {
            // Can access engine-level pub(crate) items
            super::internal_reset(); // OK — scheduler is within crate::engine
        }
    }
}
```

### Real-World Use Case: Internal Crate API

```rust
// In a library crate:
// lib.rs exposes only clean public API
// but internal subsystems need to communicate

pub mod parser {
    pub(crate) fn tokenize(input: &str) -> Vec<String> {
        // used by other modules in this crate, not by external users
        input.split_whitespace().map(String::from).collect()
    }
}

pub mod evaluator {
    pub fn eval(input: &str) -> i64 {
        let tokens = crate::parser::tokenize(input); // OK — pub(crate)
        tokens.len() as i64
    }
}
```

---

## 7. `use` Declarations

`use` brings a path into scope as a shorter name. It does **not** make items public — it's purely a local alias.

```rust
use std::collections::HashMap;
use std::fmt::{self, Display, Formatter};

// Bring in multiple items from same path
use std::io::{self, Read, Write, BufReader};

// Rename on import
use std::collections::HashMap as Map;

fn main() {
    let mut m: Map<&str, i32> = Map::new();
    m.insert("key", 42);
}
```

### `use` Inside Functions

`use` can appear anywhere — inside functions for local scope:

```rust
fn process() {
    use std::collections::HashSet;
    let mut seen = HashSet::new();
    seen.insert(1);
    // `HashSet` is only in scope for this function
}
```

### `use` With Modules

```rust
mod geometry {
    pub mod shapes {
        pub struct Circle { pub radius: f64 }
        pub struct Square { pub side: f64 }
    }
}

use geometry::shapes::{Circle, Square};
// Now you write `Circle` instead of `geometry::shapes::Circle`
```

### Glob Imports — Use Sparingly

```rust
use std::prelude::v1::*;  // Rust does this automatically
use geometry::shapes::*;   // imports all pub items from shapes
```

Expert note: glob imports (`*`) are useful in test modules and preludes, but in application code they obscure where names come from. Prefer explicit imports.

---

## 8. Path Qualifiers

Three special keywords navigate the module tree:

### `self` — Current Module

```rust
mod audio {
    fn compress() {}
    fn encode() {
        self::compress();  // same as just `compress()`
    }
}
```

`self` is also used in `use` to bring the module itself into scope:

```rust
use std::io::{self, Write};
// `self` here refers to `std::io` itself
// so you can write both `io::Error` and `Write`
```

### `super` — Parent Module

```rust
mod config {
    pub fn load() -> &'static str { "config_data" }

    mod validator {
        pub fn validate() {
            let data = super::load();  // go up to `config`, call `load`
            println!("Validating: {}", data);
        }
    }
}
```

### `crate` — Crate Root (Absolute Path)

```rust
// src/lib.rs
pub mod constants {
    pub const VERSION: &str = "1.0.0";
}

pub mod logger {
    pub fn log_version() {
        // crate:: always means "from the root of this crate"
        println!("{}", crate::constants::VERSION);
    }
}
```

### Path Chaining Example

```rust
mod a {
    pub mod b {
        pub mod c {
            pub fn deep_fn() {}
        }
        pub fn b_fn() {
            self::c::deep_fn();     // relative
            crate::a::b::c::deep_fn();  // absolute
        }
    }
    pub fn a_fn() {
        self::b::c::deep_fn();      // relative from a
        b::b_fn();                  // shorthand relative
    }
}
```

---

## 9. Re-exporting with `pub use`

`pub use` re-exports an item — makes it accessible as if it lived in the current module.

This is one of the most powerful patterns in Rust API design.

```rust
// src/lib.rs
mod internal {
    pub struct Engine {
        pub capacity: u32,
    }
    impl Engine {
        pub fn new(capacity: u32) -> Self { Engine { capacity } }
        pub fn start(&self) { println!("Engine started"); }
    }
}

// Re-export: users write `mylib::Engine`, not `mylib::internal::Engine`
pub use internal::Engine;
```

### Facade Pattern — Flattening Deep Hierarchies

```rust
// Deep structure (internal)
mod core {
    pub mod types {
        pub struct Token(pub String);
        pub struct Span { pub start: usize, pub end: usize }
    }
    pub mod errors {
        pub struct ParseError(pub String);
    }
}

// Clean public API (facade)
pub use core::types::{Token, Span};
pub use core::errors::ParseError;

// Users: `use mylib::{Token, Span, ParseError};`
// Not:   `use mylib::core::types::Token;`
```

### Re-exporting External Crates

```rust
// In your library, re-export a dependency so users don't need to add it
pub use serde::{Serialize, Deserialize};
pub use tokio::runtime::Runtime;
```

This is standard practice in Rust ecosystems — e.g., `tokio` re-exports `bytes::Bytes` as `tokio::Bytes`.

---

## 10. `mod.rs` vs. the Modern Pattern

### Old Pattern (`mod.rs`)

```
src/
├── main.rs
└── network/
    ├── mod.rs        ← defines the `network` module
    ├── http.rs
    └── tcp.rs
```

```rust
// src/network/mod.rs
pub mod http;
pub mod tcp;
```

### Modern Pattern (Rust 2018+)

```
src/
├── main.rs
├── network.rs        ← defines the `network` module
└── network/
    ├── http.rs
    └── tcp.rs
```

```rust
// src/network.rs
pub mod http;
pub mod tcp;
```

```rust
// src/main.rs
mod network;
```

### Why the Modern Pattern Is Preferred

1. **Clarity**: `network.rs` and `network/` are clearly paired. `mod.rs` files look identical in editors/terminal listings.
2. **Navigation**: In your editor's file tree, `network.rs` is easier to identify than hunting for `mod.rs` in a folder.
3. **No ambiguity**: Can't accidentally have both `network.rs` and `network/mod.rs`.

> **Rule**: In Rust 2018 and later, use `network.rs` + `network/` directory. Reserve `mod.rs` only when working on legacy codebases.

---

## 11. Module Splitting Across Files — Real-World Structure

### A production-grade library structure

```
src/
├── lib.rs              ← crate root, public API surface
├── error.rs            ← unified error types
├── config.rs           ← configuration
├── parser.rs           ← module declaration file
├── parser/
│   ├── lexer.rs
│   ├── ast.rs
│   └── visitor.rs
├── engine.rs
├── engine/
│   ├── scheduler.rs
│   └── worker.rs
└── prelude.rs          ← re-exports for ergonomic imports
```

```rust
// src/lib.rs
pub mod error;
pub mod config;
pub mod parser;
pub mod engine;
pub mod prelude;

// Convenience re-exports at crate root
pub use error::Error;
pub use config::Config;
```

```rust
// src/parser.rs
pub mod lexer;
pub mod ast;
mod visitor;  // internal — not exposed

pub use ast::Node; // flatten into parser namespace

pub fn parse(input: &str) -> ast::Node {
    let tokens = lexer::tokenize(input);
    ast::build(tokens)
}
```

```rust
// src/prelude.rs
pub use crate::error::Error;
pub use crate::config::Config;
pub use crate::parser::{parse, Node};
pub use crate::engine::Engine;

// Users can write: use mylib::prelude::*;
```

### Connecting It All

```rust
// src/engine/scheduler.rs
use crate::config::Config;      // absolute path
use crate::error::Error;        // absolute path
use super::worker::Worker;      // sibling module

pub struct Scheduler {
    config: Config,
    workers: Vec<Worker>,
}

impl Scheduler {
    pub fn new(config: Config) -> Self {
        Scheduler { config, workers: Vec::new() }
    }
    pub fn run(&mut self) -> Result<(), Error> {
        // implementation
        Ok(())
    }
}
```

---

## 12. Modules and the Orphan Rule

The **orphan rule**: you can only implement a trait for a type if either the trait or the type is defined in your crate.

Modules do **not** relax this rule — it's crate-level, not module-level.

```rust
// In your crate:
mod display {
    use std::fmt;

    struct MyType(i32);

    // OK: MyType is defined in this crate
    impl fmt::Display for MyType {
        fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
            write!(f, "MyType({})", self.0)
        }
    }

    // OK: MyTrait is defined in this crate (even if in another module)
    trait MyTrait {}
    impl MyTrait for Vec<i32> {}   // Vec is foreign, but MyTrait is local — OK
}
```

The orphan rule means module boundaries don't matter — only crate boundaries do.

---

## 13. `#[cfg]` — Conditional Compilation

Entire modules can be conditionally compiled:

```rust
// src/lib.rs

#[cfg(target_os = "linux")]
mod linux_backend;

#[cfg(target_os = "macos")]
mod macos_backend;

#[cfg(target_os = "windows")]
mod windows_backend;

#[cfg(feature = "async")]
pub mod async_runtime;

#[cfg(feature = "serde")]
mod serde_impl;
```

### Platform Abstraction Pattern

```rust
// src/platform.rs
#[cfg(unix)]
mod unix;
#[cfg(windows)]
mod windows;

#[cfg(unix)]
pub use unix::get_process_id;
#[cfg(windows)]
pub use windows::get_process_id;
```

```rust
// src/platform/unix.rs
pub fn get_process_id() -> u32 {
    unsafe { libc::getpid() as u32 }
}
```

```rust
// src/platform/windows.rs
pub fn get_process_id() -> u32 {
    unsafe { winapi::um::processthreadsapi::GetCurrentProcessId() }
}
```

Users call `platform::get_process_id()` without caring about the OS.

---

## 14. Testing Modules — `#[cfg(test)]`

The idiomatic Rust pattern: embed tests in the same file as the code, inside a `mod tests` block gated by `#[cfg(test)]`.

```rust
// src/math.rs
pub fn gcd(mut a: u64, mut b: u64) -> u64 {
    while b != 0 {
        let temp = b;
        b = a % b;
        a = temp;
    }
    a
}

pub fn lcm(a: u64, b: u64) -> u64 {
    a / gcd(a, b) * b
}

#[cfg(test)]
mod tests {
    use super::*;  // bring parent module's items into scope

    #[test]
    fn test_gcd_basic() {
        assert_eq!(gcd(12, 8), 4);
        assert_eq!(gcd(100, 75), 25);
        assert_eq!(gcd(7, 13), 1);  // coprime
    }

    #[test]
    fn test_gcd_zero() {
        assert_eq!(gcd(0, 5), 5);
        assert_eq!(gcd(5, 0), 5);
    }

    #[test]
    fn test_lcm() {
        assert_eq!(lcm(4, 6), 12);
        assert_eq!(lcm(7, 13), 91);  // coprime
    }

    // Test private functions — only possible because tests are in the same file
    #[test]
    fn test_internal() {
        // If there were a private helper in this module, we could test it here
        // This is a major advantage of the embedded test pattern
    }
}
```

### Why `use super::*`?

`mod tests` is a **child** of the module being tested. `super` refers to the parent — the module under test. This allows tests to access both public and private items of the parent module.

### Integration Tests — Separate from Unit Tests

Integration tests go in `tests/` directory and are entirely separate crates:

```
src/
├── lib.rs
└── ...
tests/
├── integration_test.rs
└── another_test.rs
```

```rust
// tests/integration_test.rs
use my_crate::Engine;   // only public API accessible here

#[test]
fn test_engine_end_to_end() {
    let engine = Engine::new();
    assert!(engine.start().is_ok());
}
```

---

## 15. Real-World Project Architectures

### Architecture 1: CLI Tool

```
src/
├── main.rs         ← entry point, arg parsing
├── cli.rs          ← CLI argument definitions (clap)
├── commands/
│   ├── mod.rs      ← or commands.rs
│   ├── build.rs
│   ├── test.rs
│   └── deploy.rs
├── config.rs
└── error.rs
```

```rust
// src/main.rs
mod cli;
mod commands;
mod config;
mod error;

use error::Error;

fn main() -> Result<(), Error> {
    let args = cli::parse();
    commands::dispatch(args)
}
```

### Architecture 2: Web Server (tokio + axum style)

```
src/
├── main.rs
├── lib.rs          ← shared library code
├── routes/
│   ├── mod.rs
│   ├── users.rs
│   └── products.rs
├── handlers/
│   ├── mod.rs
│   ├── auth.rs
│   └── data.rs
├── models/
│   ├── mod.rs
│   ├── user.rs
│   └── product.rs
├── db/
│   ├── mod.rs
│   └── postgres.rs
└── error.rs
```

```rust
// src/routes/mod.rs
pub mod users;
pub mod products;

use axum::Router;

pub fn app_router() -> Router {
    Router::new()
        .nest("/users",    users::router())
        .nest("/products", products::router())
}
```

### Architecture 3: Data Processing Library

```rust
// src/lib.rs
pub mod io {
    pub mod csv;
    pub mod json;
    pub mod parquet;
}

pub mod transform {
    pub mod filter;
    pub mod aggregate;
    pub mod join;
}

pub mod compute {
    pub mod stats;
    pub mod ml;
}

// Clean public API
pub use io::csv::read_csv;
pub use transform::aggregate::group_by;
pub use compute::stats::describe;
```

---

## 16. Expert Patterns & Idioms

### Pattern 1: The Prelude Module

```rust
// src/prelude.rs — users write: use my_crate::prelude::*;
pub use crate::{
    Engine,
    Config,
    Error,
    Result,  // type alias: pub type Result<T> = std::result::Result<T, Error>;
};
pub use crate::traits::{Processable, Serializable};
```

### Pattern 2: Sealed Traits via Module Privacy

Prevent external crates from implementing your trait:

```rust
pub mod sealed {
    // This trait is pub but the module path is known
    // External users cannot name `Sealed` to implement it
    pub trait Sealed {}
}

pub trait MyTrait: sealed::Sealed {
    fn do_thing(&self);
}

// Internal implementations — only your types can impl MyTrait
pub struct TypeA;
impl sealed::Sealed for TypeA {}
impl MyTrait for TypeA {
    fn do_thing(&self) { println!("TypeA"); }
}
```

### Pattern 3: Builder Pattern With Private Construction

```rust
mod request {
    pub struct Request {
        url: String,
        headers: Vec<(String, String)>,
        body: Option<String>,
    }

    pub struct RequestBuilder {
        url: String,
        headers: Vec<(String, String)>,
        body: Option<String>,
    }

    impl Request {
        pub fn builder(url: &str) -> RequestBuilder {
            RequestBuilder {
                url: url.to_string(),
                headers: Vec::new(),
                body: None,
            }
        }
    }

    impl RequestBuilder {
        pub fn header(mut self, key: &str, value: &str) -> Self {
            self.headers.push((key.to_string(), value.to_string()));
            self
        }
        pub fn body(mut self, body: &str) -> Self {
            self.body = Some(body.to_string());
            self
        }
        pub fn build(self) -> Request {
            Request { url: self.url, headers: self.headers, body: self.body }
        }
    }
}
```

### Pattern 4: Type-State Pattern With Modules

```rust
mod connection {
    pub struct Disconnected;
    pub struct Connected { pub(super) socket_fd: i32 }
    pub struct Authenticated { pub(super) socket_fd: i32, pub(super) user_id: u64 }

    pub struct Connection<State> {
        state: State,
    }

    impl Connection<Disconnected> {
        pub fn new() -> Self {
            Connection { state: Disconnected }
        }
        pub fn connect(self, _addr: &str) -> Connection<Connected> {
            Connection { state: Connected { socket_fd: 42 } }
        }
    }

    impl Connection<Connected> {
        pub fn authenticate(self, _token: &str) -> Connection<Authenticated> {
            Connection { state: Authenticated { socket_fd: self.state.socket_fd, user_id: 1 } }
        }
    }

    impl Connection<Authenticated> {
        pub fn query(&self, sql: &str) -> String {
            format!("Result of `{}` for user {}", sql, self.state.user_id)
        }
    }
}

fn main() {
    use connection::Connection;
    let result = Connection::new()
        .connect("127.0.0.1:5432")
        .authenticate("secret_token")
        .query("SELECT * FROM users");
    println!("{}", result);
}
```

### Pattern 5: Feature-Gated Module Extensions

```rust
// src/lib.rs
pub struct DataFrame { /* ... */ }

impl DataFrame {
    pub fn new() -> Self { DataFrame {} }
}

#[cfg(feature = "serde")]
mod serde_support {
    use super::DataFrame;
    use serde::{Serialize, Deserialize};

    impl Serialize for DataFrame {
        fn serialize<S: serde::Serializer>(&self, s: S) -> Result<S::Ok, S::Error> {
            s.serialize_str("DataFrame")
        }
    }
}

#[cfg(feature = "arrow")]
pub mod arrow_compat;
```

---

## 17. Common Pitfalls

### Pitfall 1: Forgetting to Declare `mod`

```
src/
├── main.rs
└── utils.rs       ← IGNORED if not declared
```

```rust
// main.rs — this is WRONG if you didn't add `mod utils;`
use utils::helper;   // ERROR: unresolved import `utils`
```

Fix: Add `mod utils;` to `main.rs`.

### Pitfall 2: Privacy Confusion With Struct Fields

```rust
pub struct Config {
    pub host: String,
    port: u16,          // private!
}

// In another module:
let c = Config { host: "localhost".into(), port: 8080 };
// ERROR: field `port` is private
```

Fix: Either make `port` pub, or provide a constructor.

### Pitfall 3: Both `foo.rs` and `foo/mod.rs` Exist

```
src/
├── main.rs
├── config.rs         ← ambiguous!
└── config/
    └── mod.rs        ← ambiguous!
```

Compiler error: `file for module `config` found at both...`

Fix: Delete one. Prefer the modern pattern (`config.rs`).

### Pitfall 4: `use` in Module But Forgetting `pub use` for Re-export

```rust
mod internal {
    use std::collections::HashMap;
    pub type Config = HashMap<String, String>;
}

// In another crate using your library:
// ERROR: cannot use `Config` because it's not re-exported
```

Fix: `pub use internal::Config;` at an appropriate public level.

### Pitfall 5: Circular Module Dependencies

Rust **prevents** circular crate dependencies but modules within a crate **can** reference each other freely (since they share a single compilation unit). However, circular *logical dependencies* make code harder to reason about.

Solution: Introduce a common types/traits module that both modules depend on.

```rust
// Instead of: parser uses evaluator uses parser
// Do:
mod types { pub struct Ast {} }   // no dependencies
mod parser { use super::types::Ast; }
mod evaluator { use super::types::Ast; }
```

### Pitfall 6: Confusion Between `mod foo;` and `use foo;`

```rust
mod math;   // DECLARES the module — tells compiler it exists
use math::add;  // IMPORTS an item — creates a local alias
```

These are fundamentally different operations. `mod` defines the tree. `use` navigates it.

---

## 18. Mental Model Summary

### The Module System as a Decision Engine

Ask yourself these questions when designing module structure:

1. **What is my public API?** → Everything else is an implementation detail. Hide it.
2. **What changes together?** → Put it in the same module.
3. **What is the trust boundary?** → `pub(crate)` for intra-crate trust, `pub` for external trust.
4. **Who needs to know about what?** → Design dependency directions to avoid cycles.
5. **What should users never need to qualify?** → Re-export with `pub use`.

### The Visibility Hierarchy (From Least to Most Visible)

```
private                (default)
    ↓
pub(self)              (explicit private — rare, same as default)
    ↓
pub(super)             (parent only)
    ↓
pub(in some::path)     (specific ancestor)
    ↓
pub(crate)             (whole crate)
    ↓
pub                    (the world)
```

### The Module Tree is a Promise

When you write `pub fn api_function()`, you are making a **contract**. The module system is the mechanism by which you control who you're making that contract with. Private means you reserve the right to change it at will. `pub(crate)` means you trust your own codebase. `pub` means you're making a public commitment.

This is not just organization — it is **communication about intent and stability**.

---

## Quick Reference

```rust
mod foo;                        // declare module (file-backed)
mod foo { }                     // declare inline module
pub mod foo;                    // public module
pub(crate) mod foo;             // crate-internal module

use crate::foo::Bar;            // absolute import
use super::foo::Bar;            // relative import (parent)
use self::foo::Bar;             // relative import (sibling)
use foo::{Bar, Baz};            // multi-import
use foo::*;                     // glob import
pub use foo::Bar;               // re-export
use foo::Bar as B;              // aliased import

pub fn f() {}                   // public function
pub(crate) fn f() {}            // crate-visible
pub(super) fn f() {}            // parent-visible
fn f() {}                       // private

#[cfg(test)]
mod tests { use super::*; }     // test module pattern
#[cfg(feature = "x")]
mod feature_module;             // feature-gated module
#[cfg(target_os = "linux")]
mod platform_module;            // platform-gated module
```

---

*Master the module system and you master Rust's trust model. Every `pub` is a decision. Every hidden implementation is a gift to your future self. Think in modules before you think in code.*

Here's your complete guide. Let me give you the expert distillation of what's inside:

---

### What this guide covers (18 deep chapters):

**Foundations** — The mental model that separates beginners from experts: modules are a *namespace tree*, not a file system. The file system is just one way to *express* that tree.

**The 3 declaration forms** — Inline `mod {}`, file-backed `mod foo;` → `foo.rs`, and the legacy `mod.rs` pattern vs. the modern Rust 2018 style. Why both exist and which to use.

**The entire visibility system** — `pub`, `pub(crate)`, `pub(super)`, `pub(in path)`, and the nuanced rule that structs and enums behave *differently* (struct fields stay private; enum variants go public automatically).

**Path navigation** — `self`, `super`, `crate` as a precise navigation system through the module tree. Relative vs. absolute paths and when each is appropriate.

**`pub use` — the most underused power tool** — Re-exporting for facade patterns, flattening deep hierarchies, and creating prelude modules. This is how crates like `tokio` and `serde` deliver ergonomic APIs.

**5 Expert design patterns** — Sealed traits, type-state machines, builder patterns with private construction, feature-gated extensions, and the prelude idiom.

**Real-world architectures** — CLI tools, web servers, and data processing libraries laid out with actual file trees and module declarations.

**6 critical pitfalls** — The exact errors that trip up intermediate Rust programmers, with root causes and fixes.

---

### The one mental model to internalize:

> Every `pub` is a **contract**. Private means you can change it freely. `pub(crate)` means you trust your codebase. `pub` means you're making a public promise. The module system is the mechanism of *trust*, not just organization.

Exactly 👍 — in Rust, **`mod`** is used to **define a module** (a unit of code organization and namespace).
It tells the compiler:

> “This block/file is part of my crate, treat it as a module.”

---

## 1. Inline Modules

You can define a module **inside a file** using a `mod {}` block:

```rust
mod greetings {
    pub fn hello() {
        println!("Hello from greetings module!");
    }
}

fn main() {
    greetings::hello();
}
```

Here:

* `mod greetings { ... }` defines a module inline.
* Functions inside need `pub` to be accessible outside.

---

## 2. File Modules

Instead of inline, you can put modules in separate files.

**📂 Project Structure**

```
src/
 ├── main.rs
 └── greetings.rs
```

**main.rs**

```rust
mod greetings; // declare the module

fn main() {
    greetings::hello();
}
```

**greetings.rs**

```rust
pub fn hello() {
    println!("Hello from greetings.rs!");
}
```

Here `mod greetings;` tells Rust: *look for `greetings.rs` or `greetings/mod.rs` and load it as a module*.

---

## 3. Nested Modules (Folders)

Modules can be hierarchical (like packages).

**📂 Project Structure**

```
src/
 ├── main.rs
 └── greetings/
      ├── mod.rs
      └── english.rs
```

**main.rs**

```rust
mod greetings;

fn main() {
    greetings::english::hello();
}
```

**greetings/mod.rs**

```rust
pub mod english;
```

**greetings/english.rs**

```rust
pub fn hello() {
    println!("Hello from greetings::english!");
}
```

---

## 4. Module Visibility

* By default, everything is **private** inside a module.
* Use `pub` to expose.
* You can even expose submodules:

```rust
mod greetings {
    pub mod english {
        pub fn hello() {
            println!("Hello!");
        }
    }
}

fn main() {
    greetings::english::hello(); // ✅ works
}
```

---

## 5. `mod` vs `use`

* `mod` = *declare the module exists*.
* `use` = *bring an item into scope (shortcut)*.

Example:

```rust
mod greetings {
    pub fn hello() {
        println!("Hello!");
    }
}

use greetings::hello;

fn main() {
    hello(); // shortcut via `use`
}
```

---

## 🌳 Summary

* **`mod` = define a module** (inline, file, or folder).
* Modules help organize code into namespaces.
* Use `pub` to expose things.
* Combine with `use` for easier paths.

---

👉 Mental model:

* **`mod`** = *put code into a drawer*.
* **`pub`** = *make the drawer handle visible to others*.
* **`use`** = *pull the drawer’s contents onto your desk*.

---

Do you want me to also show how **modules interact with crates** (e.g., `crate::`, `super::`, `self::` inside a `mod`)?

I looked at the directory tree you gave and walked through how Rust's module system makes those three files work together. Below I explain step‑by‑step what usually happens with this layout, show small example contents, call out common pitfalls, and finish with what I can do next.

What the tree means
- src/main.rs is the crate root (the binary entry point).
- src/greetings/mod.rs is the greetings module file (the parent module for the greetings directory).
- src/greetings/english.rs is a submodule file of greetings (the english module).

Step‑by‑step explanation

1) main.rs must declare the greetings module so the compiler loads the files
- In main.rs you typically write:
  - mod greetings;
  This tells the compiler: "look for a module named greetings" and Rust will load src/greetings/mod.rs (because greetings is a directory with mod.rs).
- After declaring mod greetings, you can refer to greetings and its public children.

Example main.rs (minimal)
```rust
fn main() {
    // Call a function defined in greetings::english
    greetings::english::hello();
}
```
But this example assumes main.rs also has `mod greetings;` at the top:
```rust
mod greetings;

fn main() {
    greetings::english::hello();
}
```

2) greetings/mod.rs defines the greetings module and declares submodules (like english)
- In src/greetings/mod.rs you normally declare the english submodule and possibly re-export or provide wrapper functions.

Example greetings/mod.rs
```rust
pub mod english; // loads src/greetings/english.rs

// Optionally add a convenience re-export or shared functions:
pub fn say_hello_in_english() {
    english::hello();
}
```
Notes:
- `pub mod english;` makes the english module public so code outside greetings can access greetings::english.
- If `pub` is omitted, english is private to the greetings module and main.rs (or other modules) can't call greetings::english::hello().

3) greetings/english.rs provides the implementation (functions, types)
- In src/greetings/english.rs you implement functions, types, etc.

Example greetings/english.rs
```rust
pub fn hello() {
    println!("Hello!");
}

// or returning a value:
pub fn greeting() -> &'static str {
    "Hello"
}
```
- `pub fn hello()` is public so callers like main.rs can call greetings::english::hello().

How the compiler wires it up
- When you compile, rustc starts at the crate root (main.rs). The `mod greetings;` line makes it load src/greetings/mod.rs.
- Inside mod.rs the `pub mod english;` line makes the compiler load src/greetings/english.rs and attach it as greetings::english.
- Visibility rules apply: `pub` exposes modules/items to parent/other modules; no `pub` means private (module-local).

Execution flow at runtime
- Cargo builds the crate, producing a binary.
- Running the binary executes main(), which calls into the functions defined in the module tree (e.g., greetings::english::hello()).
- The function prints or returns its value accordingly.

Common variations and gotchas
- You must declare `mod greetings;` in main.rs (or lib.rs) — having the folder alone does not auto‑include it.
- Using `pub mod english;` vs `mod english;` in greetings/mod.rs controls whether english is reachable from other modules.
- You can re-export items to shorten paths:
  ```rust
  // in greetings/mod.rs
  pub use english::hello as english_hello;
  // then main can call greetings::english_hello()
  ```
- Alternative layout: instead of greetings/mod.rs you can sometimes have src/greetings.rs with `mod english;` and then src/greetings/english.rs. Both styles are supported; mod.rs is the directory module pattern.
- Lifetime/ownership/visibility issues still follow ordinary Rust rules.

A concrete minimal complete example
- src/main.rs
```rust
mod greetings;

fn main() {
    greetings::english::hello();
}
```
- src/greetings/mod.rs
```rust
pub mod english;
```
- src/greetings/english.rs
```rust
pub fn hello() {
    println!("Hello from english.rs!");
}
```
Running `cargo run` prints:
Hello from english.rs!

What I did and what's next
- I inspected your tree and explained how Rust resolves modules from main.rs -> greetings/mod.rs -> greetings/english.rs, described visibility and execution, and showed small example contents.
- Next, if you want, I can:
  - Inspect the exact contents of your three files if you paste them, and explain line‑by‑line.
  - Show how to add another language module (e.g., french.rs) and a higher‑level API that chooses a language.
  - Point out any specific compilation errors you’re getting and help fix them — paste the error output and the files.

Which of those would you like me to do?

Short answer first
- Nested mod creates a module tree (namespaces) at compile time. In your example the crate root (main.rs) has a child module greetings which itself has a child module english. The fully qualified path to the function is greetings::english::hello().
- Purpose: organization (namespacing), encapsulation (privacy), and clearer public API boundaries (pub, pub(crate), pub(super)).
- Alternative: keep everything in one file (no modules) or use file-based modules (mod greetings; with src/greetings/mod.rs and src/greetings/english.rs). Both are equivalent in meaning — inline vs file-based is mostly about source layout.
- If you don't use modules at all your program can still be a single-file program; modules are optional but recommended as code grows.

Step-by-step explanation of how your snippet works
1) Declaration and compile-time inclusion
   - You wrote mod greetings { ... } directly in main.rs. That declares an inline module named greetings and the compiler attaches the contents as a child module of the crate root.
   - Inside that inline greetings you declared pub mod english { ... } which creates another nested module named english (a child of greetings).

2) Namespacing and access
   - The function hello is defined at path greetings::english::hello.
   - In main(), you refer to greetings::english::hello(); that resolves the path starting from the crate root.
   - The english module was declared pub, so its public items (pub fn hello) are accessible from outside the greetings module. If you omitted pub on english, main() could still call it because greetings and english are in the same crate root? Correction: within the same parent module, non-pub children are accessible to siblings inside the parent only when visibility rules allow — generally mark public when you intend cross-module access (pub, pub(crate), etc.). For clarity: use pub when you want other modules to access the item.

3) Privacy rules in brief
   - pub makes an item visible outside its parent module.
   - pub(crate) visible to the entire crate.
   - pub(super) visible to the parent module.
   - Items without any pub are private to their parent module (and its descendants only).

4) Runtime/compile flow
   - The compiler builds a module tree from mod declarations. Inline modules are compiled from the block you wrote; file modules are compiled from files rustc loads when it sees mod name; the rest of the build (type checking, monomorphization, linking) is the same.

Inline (nested) module vs file-based module (equivalent)
- Inline nested example (what you have):
```rust name=src/main.rs
mod greetings {
    pub mod english {
        pub fn hello() {
            println!("Hello!");
        }
    }
}

fn main() {
    greetings::english::hello();
}
```

- Exact same structure using files (more common for larger projects):
```rust name=src/main.rs
mod greetings; // rustc will load src/greetings/mod.rs

fn main() {
    greetings::english::hello();
}
```

```rust name=src/greetings/mod.rs
pub mod english; // rustc will load src/greetings/english.rs
```

```rust name=src/greetings/english.rs
pub fn hello() {
    println!("Hello!");
}
```

When to use each style
- Inline nested modules (mod name { ... }):
  - Good for small examples, tiny helper modules, or when you want tests and implementation colocated.
  - Quick for playground code or when the module is one short block.
- File-based modules (mod name; + files):
  - Prefer this for larger codebases, multi-file organization, or when a module grows significant content.
  - Matches file-system layout and is easier to navigate.

Alternatives and useful patterns
- Flatten everything into main.rs: perfectly valid for tiny programs. As code grows, organizing into modules is recommended.
- Re-export publicly to simplify API:
  - In greetings/mod.rs: pub use english::hello; then callers do greetings::hello() instead of greetings::english::hello().
- pub(crate) when you want items visible across the crate but not to external crates (libraries).
- pub(super) to expose to the parent but keep hidden from others.
- #[path = "some/other.rs"] mod foo; — advanced: load a module from a custom path.

Common pitfalls
- Forgetting to declare mod greetings; when using file-based module layout — the compiler won't auto-include directories.
- Assuming pub on a child makes parent public — it doesn't. For external crates you must expose the module from the crate root (pub mod on lib.rs or re-export).
- Deep nesting can make paths long; re-export sensible APIs at higher level to keep user-facing paths small.

Concrete small variants
- Re-export to shorten path:
```rust name=src/greetings/mod.rs
pub mod english;
pub use english::hello; // now callers use greetings::hello()
```
- Use use in main to shorten call:
```rust
use greetings::english::hello;

fn main() {
    hello();
}
```

Summary (what I did)
I explained how nested modules are created and compiled, why you would use them, what alternatives exist (single-file, file-based modules, re-exports), showed equivalent file-based layout and small code patterns, and listed common pitfalls and visibility rules.

If you want, I can now:
- convert your inline example into a multi-file layout in a sample repo tree and show exact files (I already included those examples above), or
- explain visibility examples with pub(crate)/pub(super) in more detail, or
- help refactor a specific real codebase you have — paste the files and I’ll walk through them line-by-line.

```rust name=src/main.rs
mod greetings; // rustc will load src/greetings/mod.rs

fn main() {
    greetings::english::hello();
}

pub mod english;
pub use english::hello; // now callers use greetings::hello()

pub fn hello() {
    println!("Hello!");
}
```

# The `mod` Keyword in Rust — A Complete Deep-Dive Guide

> *"A codebase without discipline in its module structure is a codebase that will collapse under its own weight."*

---

## Table of Contents

1. [The Mental Model: What Is a Module?](#1-the-mental-model-what-is-a-module)
2. [Inline Modules — The Atom of Structure](#2-inline-modules)
3. [File-Based Modules — Scaling Outward](#3-file-based-modules)
4. [Directory Modules — The Two Styles](#4-directory-modules)
5. [Visibility: The Access Control System](#5-visibility-access-control)
6. [Paths: Navigating the Module Tree](#6-paths-navigating-the-module-tree)
7. [The `use` Keyword and `mod`](#7-the-use-keyword-and-mod)
8. [Re-exports with `pub use`](#8-re-exports-with-pub-use)
9. [Glob Imports](#9-glob-imports)
10. [The Prelude Pattern](#10-the-prelude-pattern)
11. [The Facade Pattern](#11-the-facade-pattern)
12. [Test Modules — `#[cfg(test)]`](#12-test-modules)
13. [Conditional Compilation with `cfg`](#13-conditional-compilation-with-cfg)
14. [Real-World: Library Crate Architecture](#14-real-world-library-crate-architecture)
15. [Real-World: CLI Application Structure](#15-real-world-cli-application-structure)
16. [Real-World: Systems Programming Pattern](#16-real-world-systems-programming-pattern)
17. [Advanced: `pub(in path)` for Fine-Grained Control](#17-advanced-pub-in-path)
18. [Common Mistakes and Pitfalls](#18-common-mistakes-and-pitfalls)
19. [Mental Models for Mastery](#19-mental-models-for-mastery)

---

## 1. The Mental Model: What Is a Module?

Before writing a single line, internalize this: **Rust's module system is a tree**. Every Rust program has a single root — the *crate root* — from which all modules branch outward.

```
crate (root)
├── mod network
│   ├── mod tcp
│   └── mod udp
├── mod storage
│   ├── mod disk
│   └── mod memory
└── mod utils
```

This tree has three responsibilities:

| Responsibility   | What It Controls                             |
|------------------|----------------------------------------------|
| **Namespacing**  | Prevents name collisions between items       |
| **Encapsulation**| Controls what is visible to the outside world|
| **Organization** | Maps logical domains to physical file layout |

The `mod` keyword **declares** a module into existence. It does one of two things:
- Defines the module **inline** (body follows immediately with `{}`)
- Tells the compiler to **look for the module in a separate file**

**Critical insight**: `mod` is a *declaration*, not an *import*. This distinguishes Rust from languages like Go or C, where files implicitly belong to packages or translation units. In Rust, **a file does not exist to the compiler unless some `mod` declaration references it**.

---

## 2. Inline Modules

The simplest form — the entire module lives inside the current file.

```rust
// src/main.rs  (or any .rs file)

mod math {
    // Everything here is private to `math` by default
    fn add_internal(a: i32, b: i32) -> i32 {
        a + b
    }

    // Public to whoever can see the `math` module
    pub fn add(a: i32, b: i32) -> i32 {
        add_internal(a, b)
    }

    pub fn multiply(a: i32, b: i32) -> i32 {
        a * b
    }

    // Nested inline module
    pub mod advanced {
        pub fn power(base: i64, exp: u32) -> i64 {
            base.pow(exp)
        }

        // `super` refers to the parent module (`math`)
        pub fn double_add(a: i32, b: i32) -> i32 {
            super::add(a, b) * 2
        }
    }
}

fn main() {
    println!("{}", math::add(3, 4));           // 7
    println!("{}", math::advanced::power(2, 10)); // 1024
    println!("{}", math::advanced::double_add(3, 4)); // 14

    // This would NOT compile — add_internal is private:
    // math::add_internal(1, 2);
}
```

### Key Rules for Inline Modules

- Items inside a module are **private by default** — invisible to the outside.
- A child module **can** access private items of its *ancestor* modules.
- A parent module **cannot** access private items of its *child* modules.

```rust
mod outer {
    fn secret() -> &'static str { "outer secret" }

    mod inner {
        pub fn reveal() -> &'static str {
            // Child CAN access parent's private items
            super::secret()
        }
    }

    pub fn expose() -> &'static str {
        // Parent can call inner's public function
        inner::reveal()
        // But NOT: inner's private functions
    }
}
```

This asymmetry is intentional and powerful: **children know about their parents, but parents only know what children choose to expose**. Think of it like a company — employees know company strategy (parent), but management only sees what teams surface to them (children's public API).

---

## 3. File-Based Modules

When a module grows beyond a few functions, it belongs in its own file. The `mod` declaration in the parent file tells the compiler where to look.

### Project Structure:
```
src/
├── main.rs
├── network.rs      ← content of `mod network`
└── storage.rs      ← content of `mod storage`
```

```rust
// src/main.rs
mod network;   // Compiler loads src/network.rs
mod storage;   // Compiler loads src/storage.rs

fn main() {
    network::connect("127.0.0.1:8080");
    storage::write("key", "value");
}
```

```rust
// src/network.rs
// No `mod` declaration needed here — this file IS the module body

pub fn connect(addr: &str) {
    println!("Connecting to {addr}");
}

fn internal_handshake() {
    // Private, not visible outside this module
}
```

```rust
// src/storage.rs
pub fn write(key: &str, value: &str) {
    println!("Writing {key} = {value}");
}
```

**The rule**: When you write `mod network;` (with a semicolon instead of braces), Rust looks for **either**:
- `src/network.rs` — single file module
- `src/network/mod.rs` — directory module (covered next)

---

## 4. Directory Modules — The Two Styles

When a module itself has submodules, you need a directory. Rust supports **two styles**:

### Style A: The `mod.rs` pattern (older, still valid)

```
src/
├── main.rs
└── network/
    ├── mod.rs      ← the `network` module's body
    ├── tcp.rs
    └── udp.rs
```

```rust
// src/network/mod.rs
pub mod tcp;   // loads src/network/tcp.rs
pub mod udp;   // loads src/network/udp.rs

pub fn connect(addr: &str) {
    tcp::establish(addr);
}
```

### Style B: Named file pattern (modern, preferred since Rust 2018)

```
src/
├── main.rs
├── network.rs      ← the `network` module's body
└── network/
    ├── tcp.rs
    └── udp.rs
```

```rust
// src/network.rs  (same role as mod.rs, but named after the module)
pub mod tcp;
pub mod udp;

pub fn connect(addr: &str) {
    tcp::establish(addr);
}
```

**Why prefer Style B?**
- Avoid `mod.rs` file proliferation — dozens of `mod.rs` files in an editor are indistinguishable by filename.
- `network.rs` is immediately readable; you know it's the entry point for `network`.
- The Rust team recommends this style for new code.

**Do not mix** both styles for the same module. Rust will error if both `network.rs` and `network/mod.rs` exist.

---

## 5. Visibility: The Access Control System

Rust's visibility system is one of its most expressive. The `pub` modifier has multiple forms:

| Syntax            | Visible To                                        |
|-------------------|---------------------------------------------------|
| (nothing)         | Only the current module and its descendants       |
| `pub`             | Everyone who can name the item's parent module    |
| `pub(crate)`      | Any code within the same crate                    |
| `pub(super)`      | The parent module only                            |
| `pub(in path)`    | Any module within the specified ancestor path     |
| `pub(self)`       | Equivalent to private (the current module)        |

```rust
mod outer {
    // Completely private — only `outer` and its children can see
    fn private_fn() {}

    // Visible to the parent of `outer` (and up)
    pub(super) fn super_visible() {}

    // Visible to anyone in the same crate
    pub(crate) fn crate_visible() {}

    // Fully public — visible to anyone using this crate
    pub fn public_fn() {}

    mod inner {
        pub fn call_parent_private() {
            // Children CAN access parent's private items
            super::private_fn();

            // Children can also access super-visible and crate-visible
            super::super_visible();
            super::crate_visible();
        }
    }
}

// In same crate, different module:
mod consumer {
    fn test() {
        // outer::private_fn();      // ERROR: private
        // outer::super_visible();   // ERROR: only visible to outer's parent
        outer::crate_visible();      // OK: pub(crate)
        outer::public_fn();          // OK: pub
    }
}
```

### Struct Field Visibility

Visibility applies to struct fields individually — this is critical for API design:

```rust
pub mod config {
    pub struct Config {
        pub host: String,       // readable and writable from outside
        pub port: u16,          // readable and writable from outside
        timeout_ms: u64,        // PRIVATE — external code cannot touch this
    }

    impl Config {
        // Since `timeout_ms` is private, we provide a constructor
        pub fn new(host: impl Into<String>, port: u16) -> Self {
            Config {
                host: host.into(),
                port,
                timeout_ms: 5000,  // internal default
            }
        }

        pub fn with_timeout(mut self, ms: u64) -> Self {
            self.timeout_ms = ms;
            self
        }

        pub fn timeout(&self) -> u64 {
            self.timeout_ms
        }
    }
}

fn main() {
    let cfg = config::Config::new("localhost", 8080)
        .with_timeout(3000);

    println!("{}:{}", cfg.host, cfg.port);
    println!("Timeout: {}ms", cfg.timeout());

    // cfg.timeout_ms = 1000;  // ERROR: field is private
}
```

---

## 6. Paths: Navigating the Module Tree

Every item in Rust has a *path* — like a filesystem path, but for the module tree. There are two kinds:

### Absolute Paths

Start from the crate root with the `crate` keyword:

```rust
crate::network::tcp::connect("localhost");
// or, for external crates:
std::collections::HashMap::new();
```

### Relative Paths

Start from the current module:

```rust
// From within `network`:
tcp::connect("localhost");          // child module
super::logger::log("connecting");  // parent's sibling
self::udp::send("data");           // explicit self (same as just `udp::`)
```

### `self` and `super` in depth

```rust
mod a {
    pub fn hello() { println!("hello from a"); }

    pub mod b {
        pub fn hello() { println!("hello from b"); }

        pub mod c {
            pub fn call_all() {
                self::greet();          // calls c::greet
                super::hello();         // calls b::hello
                super::super::hello();  // calls a::hello
                crate::a::hello();      // absolute path to a::hello
            }

            fn greet() { println!("hello from c"); }
        }
    }
}
```

**Mental model for paths**: Think of `crate::` as `/` (root in filesystem), `super::` as `../`, and `self::` as `./`. This mapping is exact and will never mislead you.

---

## 7. The `use` Keyword and `mod`

`use` brings a path into local scope — it's purely a convenience alias. It does **not** load modules (that's `mod`'s job).

```rust
mod geometry {
    pub mod shapes {
        pub struct Circle {
            pub radius: f64,
        }

        pub struct Rectangle {
            pub width: f64,
            pub height: f64,
        }

        impl Circle {
            pub fn area(&self) -> f64 {
                std::f64::consts::PI * self.radius * self.radius
            }
        }

        impl Rectangle {
            pub fn area(&self) -> f64 {
                self.width * self.height
            }
        }
    }
}

// Without use — verbose but explicit:
fn without_use() {
    let c = geometry::shapes::Circle { radius: 5.0 };
    println!("{}", c.area());
}

// With use — ergonomic:
use geometry::shapes::{Circle, Rectangle};

fn with_use() {
    let c = Circle { radius: 5.0 };
    let r = Rectangle { width: 4.0, height: 3.0 };
    println!("{} {}", c.area(), r.area());
}

// Aliasing with `as`:
use geometry::shapes::Circle as Circ;
use std::collections::HashMap as Map;

fn with_alias() {
    let c = Circ { radius: 1.0 };
    let mut m: Map<String, i32> = Map::new();
    m.insert("pi".to_string(), 3);
}
```

### Where `use` Lives — Scope Rules

`use` follows normal scoping. It can live inside functions, impl blocks, or modules:

```rust
mod processor {
    pub fn run() {
        // `use` scoped to this function only
        use std::collections::BTreeMap;
        let mut map: BTreeMap<i32, i32> = BTreeMap::new();
        map.insert(1, 100);
    }

    pub fn other() {
        // BTreeMap is NOT in scope here — only inside `run`
    }
}
```

---

## 8. Re-exports with `pub use`

`pub use` is one of Rust's most powerful API design tools. It lets you **expose items from one location under a different module path**.

```rust
// src/lib.rs

mod internal {
    mod parsing {
        pub struct Parser {
            pub source: String,
        }

        impl Parser {
            pub fn new(src: impl Into<String>) -> Self {
                Parser { source: src.into() }
            }

            pub fn parse(&self) -> Vec<String> {
                self.source.split_whitespace()
                    .map(String::from)
                    .collect()
            }
        }
    }

    mod validation {
        pub fn validate(tokens: &[String]) -> bool {
            !tokens.is_empty()
        }
    }

    // Re-export from `internal` to make accessible
    pub use parsing::Parser;
    pub use validation::validate;
}

// Re-export at the crate root — users see a flat, clean API
pub use internal::Parser;
pub use internal::validate;
```

Now users of this crate write:
```rust
use my_crate::Parser;     // Not: my_crate::internal::parsing::Parser
use my_crate::validate;   // Not: my_crate::internal::validation::validate
```

**The insight**: `pub use` lets you design your *internal organization* freely (deep nesting for clarity) while presenting a *clean public API* (flat, discoverable). The two are decoupled.

This is exactly how the Rust standard library works — `std::string::String` is the internal path, but `String` is available everywhere because the prelude re-exports it.

---

## 9. Glob Imports

Import everything public from a module:

```rust
use std::collections::*;   // brings HashMap, BTreeMap, HashSet, etc.

fn main() {
    let mut map = HashMap::new();   // no prefix needed
    map.insert("key", 42);
}
```

**When to use globs**:
- In test modules (`use super::*;` is idiomatic)
- When implementing the *prelude pattern* (intentional bulk re-export)
- When using a module specifically designed for glob-import (e.g., `use glam::*;` for math libraries)

**When to avoid globs**:
- In library code — it obscures where items come from
- When two modules export identically-named items — causes conflicts

---

## 10. The Prelude Pattern

A *prelude* is a module specifically designed to be glob-imported, containing the most commonly needed items. The standard library's `std::prelude::v1` is injected into every Rust program automatically.

You can create your own:

```rust
// src/lib.rs

pub mod prelude {
    // Re-export the things users almost always need
    pub use crate::error::{Error, Result};
    pub use crate::config::Config;
    pub use crate::client::Client;
    pub use crate::traits::{Serialize, Deserialize};

    // Re-export common external types your users will always need
    pub use std::collections::HashMap;
}
```

Users of your library:
```rust
use my_library::prelude::*;

// Now they have Error, Result, Config, Client, etc. without verbose imports
fn main() -> Result<()> {
    let cfg = Config::new("localhost", 8080);
    let client = Client::connect(cfg)?;
    Ok(())
}
```

---

## 11. The Facade Pattern

A *facade* module re-exports a simplified interface over a complex internal system. This is a structural design pattern implemented purely through `pub use`.

```rust
// Internal complexity:
// src/
//   database/
//     connection_pool.rs
//     query_builder.rs
//     transaction.rs
//     migrations/
//       runner.rs
//       schema.rs

// src/lib.rs — the facade:
mod database;

// Expose only what users need — hide the internals
pub use database::connection_pool::ConnectionPool;
pub use database::query_builder::QueryBuilder;
pub use database::transaction::Transaction;

// Internal migration details are NOT re-exported
// Users cannot accidentally depend on internal types
```

**Why this matters for performance**: There is **zero runtime cost** to `pub use`. It's purely a compile-time name aliasing mechanism. No indirection, no overhead.

---

## 12. Test Modules

The `#[cfg(test)]` attribute creates a module compiled only during `cargo test`. This is Rust's idiomatic unit testing pattern:

```rust
// src/math.rs

pub fn add(a: i32, b: i32) -> i32 {
    a + b
}

pub fn divide(a: f64, b: f64) -> Option<f64> {
    if b == 0.0 { None } else { Some(a / b) }
}

fn internal_helper(x: i32) -> i32 {
    x * x + 1
}

// This entire module is excluded from release builds
#[cfg(test)]
mod tests {
    // Import everything from the parent module —
    // including PRIVATE functions. Tests are siblings, not outsiders.
    use super::*;

    #[test]
    fn test_add() {
        assert_eq!(add(2, 3), 5);
        assert_eq!(add(-1, 1), 0);
        assert_eq!(add(i32::MAX, 0), i32::MAX);
    }

    #[test]
    fn test_divide_normal() {
        assert_eq!(divide(10.0, 2.0), Some(5.0));
    }

    #[test]
    fn test_divide_by_zero() {
        assert_eq!(divide(5.0, 0.0), None);
    }

    #[test]
    fn test_internal_helper() {
        // Tests can access private functions via `super::*`
        assert_eq!(internal_helper(3), 10);  // 3*3 + 1 = 10
        assert_eq!(internal_helper(0), 1);
    }

    // Nested test organization
    mod edge_cases {
        use super::super::*;  // Go up two levels to reach the actual module

        #[test]
        fn test_add_overflow() {
            // In debug mode, this would panic. This tests the behavior.
            assert_eq!(add(0, i32::MIN), i32::MIN);
        }
    }
}
```

For **integration tests** (testing the public API as an external user would), place them in `tests/`:

```
src/
  lib.rs
  math.rs
tests/
  integration_test.rs   ← a separate crate that imports your library
```

```rust
// tests/integration_test.rs
use my_crate::add;  // Only public items — integration tests are external

#[test]
fn integration_add() {
    assert_eq!(add(100, 200), 300);
}
```

---

## 13. Conditional Compilation with `cfg`

`mod` can be conditioned on compile-time flags:

```rust
// Platform-specific modules
#[cfg(target_os = "linux")]
mod linux_impl;

#[cfg(target_os = "macos")]
mod macos_impl;

#[cfg(target_os = "windows")]
mod windows_impl;

// Compile only with a specific feature flag
// (defined in Cargo.toml's [features] section)
#[cfg(feature = "async")]
mod async_runtime;

#[cfg(feature = "serde")]
mod serialization;

// Combining conditions
#[cfg(all(target_arch = "x86_64", feature = "simd"))]
mod simd_optimized;

// Negation
#[cfg(not(feature = "no_std"))]
mod std_extensions;
```

```toml
# Cargo.toml
[features]
default = ["async"]
async = []
simd = []
serde = ["dep:serde"]
```

### Real-World Platform Abstraction

```rust
// src/platform/mod.rs
#[cfg(unix)]
mod unix;
#[cfg(unix)]
pub use unix::*;

#[cfg(windows)]
mod windows;
#[cfg(windows)]
pub use windows::*;

// Now callers use `platform::get_cpu_count()` regardless of OS
```

```rust
// src/platform/unix.rs
use std::os::unix::process::CommandExt;

pub fn get_cpu_count() -> usize {
    // POSIX implementation
    num_cpus::get()
}

pub fn set_process_priority(nice: i32) {
    unsafe { libc::setpriority(libc::PRIO_PROCESS, 0, nice); }
}
```

---

## 14. Real-World: Library Crate Architecture

Let's build a realistic HTTP client library structure:

```
http_client/
├── Cargo.toml
└── src/
    ├── lib.rs                ← crate root, public API surface
    ├── client.rs             ← Client struct
    ├── request.rs            ← Request builder
    ├── response.rs           ← Response parsing
    ├── error.rs              ← Error types
    ├── middleware/
    │   ├── mod.rs (or middleware.rs)
    │   ├── retry.rs
    │   ├── timeout.rs
    │   └── auth.rs
    └── internal/
        ├── mod.rs
        ├── connection.rs     ← private: raw TCP
        └── codec.rs          ← private: HTTP encoding/decoding
```

```rust
// src/lib.rs
//! # HTTP Client
//!
//! A high-performance HTTP client for Rust.

// Private internals — never re-exported
mod internal;

// Implementation modules — partially exposed
mod client;
mod request;
mod response;
mod error;
pub mod middleware;   // pub: users can write their own middleware

// Curated public API via re-exports
pub use client::Client;
pub use request::{Request, RequestBuilder, Method};
pub use response::Response;
pub use error::{Error, Result};

// Prelude for ergonomic usage
pub mod prelude {
    pub use super::{Client, Request, Response, Result, Method};
    pub use super::middleware::{RetryPolicy, Timeout};
}
```

```rust
// src/error.rs
use std::fmt;

#[derive(Debug)]
pub enum Error {
    ConnectionFailed(String),
    Timeout { elapsed_ms: u64 },
    InvalidResponse(String),
    Io(std::io::Error),
}

// Type alias — users write `Result<T>` not `Result<T, http_client::Error>`
pub type Result<T> = std::result::Result<T, Error>;

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Error::ConnectionFailed(addr) => write!(f, "Failed to connect to {addr}"),
            Error::Timeout { elapsed_ms } => write!(f, "Timed out after {elapsed_ms}ms"),
            Error::InvalidResponse(msg) => write!(f, "Invalid response: {msg}"),
            Error::Io(e) => write!(f, "I/O error: {e}"),
        }
    }
}

impl From<std::io::Error> for Error {
    fn from(e: std::io::Error) -> Self {
        Error::Io(e)
    }
}
```

```rust
// src/client.rs
use crate::error::Result;
use crate::request::{Request, RequestBuilder};
use crate::response::Response;
use crate::internal::connection::Connection;

pub struct Client {
    base_url: String,
    timeout_ms: u64,
    // internal connection pool — private!
    pool: crate::internal::connection::Pool,
}

impl Client {
    pub fn new(base_url: impl Into<String>) -> Self {
        Client {
            base_url: base_url.into(),
            timeout_ms: 30_000,
            pool: crate::internal::connection::Pool::new(10),
        }
    }

    pub fn get(&self, path: &str) -> RequestBuilder {
        RequestBuilder::new(
            crate::request::Method::GET,
            format!("{}{}", self.base_url, path),
        )
    }

    pub fn post(&self, path: &str) -> RequestBuilder {
        RequestBuilder::new(
            crate::request::Method::POST,
            format!("{}{}", self.base_url, path),
        )
    }

    pub(crate) fn execute(&self, request: Request) -> Result<Response> {
        // pub(crate): middleware can call this, external users cannot
        let conn = self.pool.get()?;
        conn.send(request)
    }
}
```

```rust
// src/middleware/mod.rs
mod retry;
mod timeout;
mod auth;

pub use retry::RetryPolicy;
pub use timeout::Timeout;
pub use auth::BearerAuth;

// The trait all middleware must implement
pub trait Middleware: Send + Sync {
    fn handle(
        &self,
        request: crate::request::Request,
        next: &dyn Fn(crate::request::Request) -> crate::error::Result<crate::response::Response>,
    ) -> crate::error::Result<crate::response::Response>;
}
```

---

## 15. Real-World: CLI Application Structure

```
myapp/
├── Cargo.toml
└── src/
    ├── main.rs
    ├── cli.rs           ← argument parsing
    ├── commands/
    │   ├── mod.rs
    │   ├── init.rs
    │   ├── build.rs
    │   └── deploy.rs
    ├── config.rs
    └── output.rs        ← formatting, colors
```

```rust
// src/main.rs
mod cli;
mod commands;
mod config;
mod output;

fn main() -> anyhow::Result<()> {
    let args = cli::parse();

    match args.command {
        cli::Command::Init(opts) => commands::init::run(opts),
        cli::Command::Build(opts) => commands::build::run(opts),
        cli::Command::Deploy(opts) => commands::deploy::run(opts),
    }
}
```

```rust
// src/commands/mod.rs
pub mod init;
pub mod build;
pub mod deploy;

// Shared utilities for all commands — visible within this module subtree
pub(crate) fn print_success(msg: &str) {
    crate::output::success(msg);
}

pub(crate) fn print_error(msg: &str) {
    crate::output::error(msg);
}
```

```rust
// src/commands/build.rs
use crate::cli::BuildOptions;
use super::print_success;   // from commands/mod.rs via super

pub fn run(opts: BuildOptions) -> anyhow::Result<()> {
    println!("Building with {} threads...", opts.jobs);
    // ... build logic ...
    print_success("Build complete!");
    Ok(())
}
```

---

## 16. Real-World: Systems Programming Pattern

Low-level systems code benefits enormously from careful module architecture:

```rust
// A memory allocator library

// src/lib.rs
#![no_std]  // No standard library — bare metal

mod allocator;
mod block;
mod free_list;
mod bitmap;

// Only expose the allocator interface
pub use allocator::Allocator;
pub use allocator::AllocError;

// Safety: internal details must never leak
// The `block` and `free_list` modules are purely internal
```

```rust
// src/allocator.rs
use crate::free_list::FreeList;
use crate::block::Block;
use core::alloc::Layout;

pub struct Allocator {
    free_list: FreeList,
    // All fields private — callers cannot corrupt internal state
}

#[derive(Debug)]
pub enum AllocError {
    OutOfMemory,
    InvalidLayout,
}

impl Allocator {
    pub unsafe fn new(heap_start: *mut u8, heap_size: usize) -> Self {
        Allocator {
            free_list: FreeList::new(heap_start, heap_size),
        }
    }

    pub fn allocate(&mut self, layout: Layout) -> Result<*mut u8, AllocError> {
        if layout.size() == 0 {
            return Err(AllocError::InvalidLayout);
        }
        self.free_list
            .find_free_block(layout.size(), layout.align())
            .ok_or(AllocError::OutOfMemory)
    }

    pub unsafe fn deallocate(&mut self, ptr: *mut u8, layout: Layout) {
        self.free_list.return_block(ptr, layout.size());
    }
}
```

```rust
// src/free_list.rs
// This entire module is private — implementation detail

use crate::block::Block;

pub(crate) struct FreeList {
    head: Option<*mut Block>,
    total_size: usize,
}

// Note: pub(crate) — visible within our crate but NOT to library users
impl FreeList {
    pub(crate) unsafe fn new(start: *mut u8, size: usize) -> Self {
        // ... initialize the free list ...
        FreeList { head: None, total_size: size }
    }

    pub(crate) fn find_free_block(
        &mut self,
        size: usize,
        align: usize,
    ) -> Option<*mut u8> {
        // ... first-fit / best-fit search ...
        None  // placeholder
    }

    pub(crate) fn return_block(&mut self, ptr: *mut u8, size: usize) {
        // ... coalesce adjacent free blocks ...
    }
}
```

---

## 17. Advanced: `pub(in path)`

The most surgical visibility specifier — exposes an item to a specific ancestor module and its descendants, but nobody else.

```rust
mod company {
    mod hr {
        pub(in crate::company) struct SalaryData {
            pub employee_id: u64,
            pub salary: f64,
        }
        // Only visible within `company` module subtree
        // Invisible to `crate::reporting`, `crate::sales`, etc.
    }

    mod payroll {
        use super::hr::SalaryData;  // OK — payroll is within `company`

        pub(in crate::company) fn process_payroll(data: &SalaryData) {
            println!("Processing salary: {}", data.salary);
        }
    }

    pub fn run_payroll() {
        let data = hr::SalaryData {
            employee_id: 42,
            salary: 95_000.0,
        };
        payroll::process_payroll(&data);
    }
}

mod reporting {
    fn generate_report() {
        // ERROR: SalaryData is not visible here
        // let data = crate::company::hr::SalaryData { ... };
    }
}
```

This is invaluable for **large codebase design**: you can grant specific sibling modules access to internals without opening them to the entire crate.

---

## 18. Common Mistakes and Pitfalls

### Mistake 1: Confusing `mod` and `use`

```rust
// WRONG — `use` does not load a module:
use my_module;  // This is a path lookup, not a module declaration

// CORRECT — you must first declare the module:
mod my_module;  // loads the file
use my_module::SomeType;  // then bring a name into scope
```

### Mistake 2: Forgetting that files don't auto-register

```
src/
├── main.rs
└── utils.rs   ← this file is INVISIBLE to the compiler
```

```rust
// src/main.rs — you must explicitly declare it:
mod utils;  // Without this, utils.rs might as well not exist
```

### Mistake 3: Missing `pub` on module declaration

```rust
// src/lib.rs
mod network;          // network module exists but is private
                      // External crates cannot use network::anything

pub mod network;      // Now external crates can access network's public items
```

### Mistake 4: `pub use` vs `pub mod`

```rust
// pub mod: exposes the entire module (users traverse into it)
pub mod shapes;       // Users write: my_crate::shapes::Circle

// pub use: re-exports specific items at current level
pub use shapes::Circle;  // Users write: my_crate::Circle
```

### Mistake 5: Circular module references

Rust modules are a tree — circular dependencies within a crate don't exist at the module level. However, you can have two types that reference each other within the same module:

```rust
// Both in the same module — no circularity issue:
struct Node {
    next: Option<Box<Node>>,
    data: i32,
}
```

If you find yourself wanting `mod a` to use items from `mod b` and vice versa, consider moving shared items to a third module `mod common` that both depend on.

### Mistake 6: Wrong path with `super` in nested tests

```rust
mod math {
    pub fn add(a: i32, b: i32) -> i32 { a + b }

    #[cfg(test)]
    mod tests {
        use super::*;  // correct: brings `math`'s items into scope

        mod edge_cases {
            use super::super::*;  // correct: goes up through tests, then math
            // NOT: use super::*; (that would only bring `tests` into scope)

            #[test]
            fn test() {
                assert_eq!(add(1, 1), 2);
            }
        }
    }
}
```

---

## 19. Mental Models for Mastery

### The Tree Navigation Model

Every path question reduces to tree traversal:
- `crate::` — go to root, then descend
- `super::` — go up one level, then navigate
- `self::` — stay here, then navigate (rarely needed but explicit)

Draw the tree on paper for any complex structure. The answer becomes obvious.

### The "Who Needs to Know?" Visibility Model

Before assigning visibility, ask: *"Who legitimately needs to use this?"*

- Only this function? → private
- Sibling modules in the same logical domain? → `pub(in crate::domain)`
- All modules in this crate? → `pub(crate)`
- The direct parent? → `pub(super)`
- External library users? → `pub`

Default to the **most restrictive** visibility that works. Expanding visibility later is non-breaking; restricting it is a breaking change.

### The "API vs. Implementation" Separation Model

Every module has two faces:
1. **Public API** — what you promise to the world (stable, documented, minimal)
2. **Private implementation** — how you do it (can change freely)

The `pub use` re-export mechanism is how you keep these faces independent. Your internal file structure can be as deeply nested as needed for clarity; your public API can be as flat as needed for usability.

### The Cognitive Chunking Insight

Expert Rust programmers "chunk" module trees into logical domains automatically — they don't think about individual files. When reading a crate, they look at `lib.rs`, see the `pub use` re-exports, and immediately know the API surface. The file structure is secondary.

Build this intuition deliberately: when designing a crate, **write `lib.rs` first** (the API you want to expose), then create the modules needed to implement it. This is top-down design — and it produces cleaner architectures than bottom-up.

### Visibility as Communication

`pub(crate)` is not just a technical restriction — it's documentation. It tells every reader: *"This is an internal implementation detail that I've chosen to share across this crate's internals, but it's not part of our external contract."* Use visibility modifiers to communicate intent, not just to pass the compiler.

---

## Quick Reference

```rust
mod inline {}               // Inline module definition
mod external;               // Load from file (external.rs or external/mod.rs)
pub mod visible;            // Module itself is publicly accessible

pub use item;               // Re-export item at current level
pub use module::Type;       // Re-export a specific type
pub use module::*;          // Re-export everything (glob)

use crate::a::b::C;         // Absolute path import
use super::D;               // Parent-relative import
use self::e::F;             // Self-relative import (rare)
use a::{B, C, D};          // Group import
use a::B as AliasB;         // Aliased import

pub fn visible() {}         // Fully public
pub(crate) fn internal() {} // Crate-wide internal
pub(super) fn to_parent() {}// Parent module only
pub(in crate::x) fn y() {} // Specific ancestor scope
fn private() {}             // Default: module-private only

#[cfg(test)]
mod tests { use super::*; } // Test module with access to private items
#[cfg(feature = "async")]
mod async_impl;             // Feature-gated module
#[cfg(target_os = "linux")]
mod linux;                  // Platform-specific module
```

---

*The module system is Rust's answer to the question: "How do we build systems that scale?" — in code size, team size, and time. Master it, and you gain the power to architect software that remains comprehensible as it grows.*