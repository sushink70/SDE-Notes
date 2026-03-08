# The `super` Keyword in Rust — A Complete Deep-Dive Guide

> *"To understand `super`, you must first understand where you are."*  
> — The Rust Module System

---

## Table of Contents

1. [Mental Model: The Filesystem Metaphor](#1-mental-model)
2. [Rust's Module System — Foundation You Must Know](#2-module-system)
3. [What is `super`?](#3-what-is-super)
4. [Path Resolution: `self`, `super`, `crate` — The Holy Trinity](#4-path-resolution)
5. [Basic `super` Usage](#5-basic-usage)
6. [Chaining `super::super::`](#6-chaining)
7. [`super` in Unit Tests (The Most Common Use Case)](#7-tests)
8. [`super` vs `crate` — When to Choose Which](#8-super-vs-crate)
9. [Visibility + `super`: `pub(super)`](#9-pub-super)
10. [Real-World Implementation: Library Architecture](#10-real-world-lib)
11. [Real-World Implementation: Game Engine Module](#11-real-world-game)
12. [Real-World Implementation: Web Server Router](#12-real-world-web)
13. [Common Mistakes & Pitfalls](#13-pitfalls)
14. [Decision Tree: When to Use `super`](#14-decision-tree)
15. [Mental Models & Cognitive Anchors](#15-mental-models)

---

## 1. Mental Model: The Filesystem Metaphor {#1-mental-model}

Before a single line of code, lock this metaphor into your mind:

```
YOUR FILESYSTEM            RUST MODULE SYSTEM
─────────────────          ─────────────────────────────
/home/user/               crate root (main.rs / lib.rs)
  ├── projects/           ├── mod projects
  │   ├── web/            │   ├── mod web
  │   │   └── router.rs   │   │   └── fn route()
  │   └── cli/            │   └── mod cli
  └── utils/              └── mod utils

cd ..         →  super::
cd ../..      →  super::super::
cd /home      →  crate::
cd .          →  self::
```

`super` is literally **"go up one directory level"** but for Rust modules.

---

## 2. Rust's Module System — Foundation You Must Know {#2-module-system}

### What is a Module?

A **module** is a named scope/namespace that groups related code (functions, structs, traits, constants, other modules).

```
┌─────────────────────────────────────────────────────────────┐
│                    CRATE (your project)                      │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  mod network                        │   │
│  │                                                     │   │
│  │   ┌─────────────────┐   ┌─────────────────────┐    │   │
│  │   │   mod tcp       │   │   mod udp           │    │   │
│  │   │   fn connect()  │   │   fn send()         │    │   │
│  │   │   fn send()     │   │   fn receive()      │    │   │
│  │   └─────────────────┘   └─────────────────────┘    │   │
│  │                                                     │   │
│  │   fn establish_connection()  ← parent fn            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### How to Declare Modules

```rust
// ─── Inline module ───────────────────────────────────────────
mod greet {
    pub fn hello() {
        println!("Hello!");
    }
}

// ─── File-based module ───────────────────────────────────────
// Rust looks for src/greet.rs OR src/greet/mod.rs
mod greet;

// ─── Nested inline ───────────────────────────────────────────
mod outer {
    mod inner {
        fn secret() {}
    }
}
```

### Visibility Rules (Critical Context)

```
┌─────────────────────────────────────────────────────────────┐
│  VISIBILITY KEYWORDS                                        │
│                                                             │
│  (no keyword)   → private, only this module                 │
│  pub            → fully public                              │
│  pub(self)      → same as private (explicit)                │
│  pub(super)     → visible to PARENT module only             │
│  pub(crate)     → visible anywhere in this crate            │
│  pub(in path)   → visible to specific ancestor module       │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. What is `super`? {#3-what-is-super}

`super` is a **path keyword** in Rust that refers to the **immediate parent module** of the current module.

```
HIERARCHY:
    crate root
        └── mod parent          ← super refers to THIS
                └── mod current ← YOU ARE HERE
                        └── super::some_fn()  → calls parent's some_fn
```

### Formal Definition

> `super` is a path segment that resolves to the parent of the current module in the module tree. It is used in `use` statements and inline path expressions.

```rust
mod parent {
    pub fn greet() {
        println!("I am the parent");
    }

    mod child {
        pub fn run() {
            // super:: = "go to parent module (parent)"
            super::greet();  // ✅ calls parent::greet()
        }
    }
}
```

### ASCII Visualization of `super` Resolution

```
crate
 │
 ├─── mod parent
 │       │
 │       ├── fn greet()          ← super::greet() lands HERE
 │       │
 │       └── mod child           ← YOU ARE IN HERE
 │               │
 │               └── super::     ← walks UP one level to `parent`
```

---

## 4. Path Resolution: `self`, `super`, `crate` — The Holy Trinity {#4-path-resolution}

Think of these as **navigation anchors**:

```
┌────────────┬──────────────────────────────┬──────────────────────────────┐
│  Keyword   │  Meaning                     │  Analogy                     │
├────────────┼──────────────────────────────┼──────────────────────────────┤
│  self      │  Current module              │  pwd (print working dir)     │
│  super     │  Parent module               │  cd ..                       │
│  crate     │  Root of the crate           │  cd /  (absolute root)       │
│  (bare)    │  Relative from current scope │  relative path ./            │
└────────────┴──────────────────────────────┴──────────────────────────────┘
```

### Side-by-Side Comparison

```rust
mod level_a {
    pub fn func_a() {}

    mod level_b {
        pub fn func_b() {}

        mod level_c {
            use super::func_b;          // ✅ parent (level_b)
            use super::super::func_a;   // ✅ grandparent (level_a)
            use crate::level_a::func_a; // ✅ absolute from root
            // use self::func_b;        // ❌ func_b is not in level_c

            pub fn run() {
                func_b();               // works after `use`
                func_a();               // works after `use`
            }
        }
    }
}
```

### Decision Flowchart: Which Path Keyword to Use?

```
          ┌─────────────────────────────────────┐
          │   Where is the item you need?       │
          └──────────────┬──────────────────────┘
                         │
          ┌──────────────▼──────────────────────┐
          │  Is it in the SAME module as you?   │
          └──────────────┬──────────────────────┘
                    Yes  │  No
                         │
            ┌────────────▼─────────────────┐
            │  Use `self::` or bare name   │
            └──────────────────────────────┘
                         │ No
          ┌──────────────▼──────────────────────┐
          │  Is it ONE level UP (parent)?        │
          └──────────────┬──────────────────────┘
                    Yes  │  No
                         │
              ┌──────────▼──────────┐
              │   Use `super::`     │
              └─────────────────────┘
                         │ No
          ┌──────────────▼──────────────────────┐
          │  Is it MULTIPLE levels up, or are   │
          │  you refactoring and want stability? │
          └──────────────┬──────────────────────┘
                    Yes  │
                         │
              ┌──────────▼──────────┐
              │   Use `crate::`     │
              │   (absolute path)   │
              └─────────────────────┘
```

---

## 5. Basic `super` Usage {#5-basic-usage}

### Example 1: Calling a Parent Function

```rust
mod kitchen {
    pub fn wash_dishes() {
        println!("Washing dishes...");
    }

    pub fn prepare_meal() {
        println!("Preparing meal...");
    }

    mod chef {
        // The chef (child module) needs to use kitchen (parent) utilities

        pub fn cook() {
            // Without super:
            //   Rust would look for `wash_dishes` in `chef` module → ❌ not found
            //
            // With super:
            //   Rust walks up to `kitchen` → finds `wash_dishes` → ✅

            super::wash_dishes();       // calls kitchen::wash_dishes()
            super::prepare_meal();      // calls kitchen::prepare_meal()
            println!("Chef is cooking!");
        }
    }

    pub fn serve() {
        chef::cook(); // kitchen can call into chef
    }
}

fn main() {
    kitchen::serve();
}
```

**Output:**
```
Washing dishes...
Preparing meal...
Chef is cooking!
```

---

### Example 2: `super` in `use` Statements

`super` works in both inline paths AND `use` declarations:

```rust
mod math {
    pub fn square(x: i32) -> i32 {
        x * x
    }

    pub fn cube(x: i32) -> i32 {
        x * x * x
    }

    mod geometry {
        // Import parent's functions into this module's namespace
        use super::square;   // now `square` is available directly
        use super::cube;

        pub fn area_of_square(side: i32) -> i32 {
            square(side)     // clean — no need for super:: every time
        }

        pub fn volume_of_cube(side: i32) -> i32 {
            cube(side)
        }
    }

    pub fn run() {
        println!("Area:   {}", geometry::area_of_square(5));   // 25
        println!("Volume: {}", geometry::volume_of_cube(3));   // 27
    }
}

fn main() {
    math::run();
}
```

---

### Example 3: Accessing Parent's Struct

```rust
mod animal {
    pub struct Animal {
        pub name: String,
        pub sound: String,
    }

    impl Animal {
        pub fn new(name: &str, sound: &str) -> Self {
            Animal {
                name: name.to_string(),
                sound: sound.to_string(),
            }
        }

        pub fn speak(&self) {
            println!("{} says: {}", self.name, self.sound);
        }
    }

    mod trainer {
        use super::Animal; // bring Animal from parent into scope

        pub fn train_animal(name: &str) {
            let a = Animal::new(name, "Woof");
            a.speak();
            println!("Training {} is complete!", a.name);
        }
    }

    pub fn demo() {
        trainer::train_animal("Rex");
    }
}

fn main() {
    animal::demo();
}
```

---

## 6. Chaining `super::super::` {#6-chaining}

You can chain `super` to climb multiple levels up the module tree.

```
MODULE TREE:
    crate
     └── mod level_1
              └── mod level_2
                       └── mod level_3   ← YOU ARE HERE
```

```rust
mod level_1 {
    pub fn from_level_1() -> &'static str {
        "I am level 1"
    }

    mod level_2 {
        pub fn from_level_2() -> &'static str {
            "I am level 2"
        }

        mod level_3 {
            pub fn reach_up() {
                // Go up ONE level: level_3 → level_2
                let msg2 = super::from_level_2();

                // Go up TWO levels: level_3 → level_2 → level_1
                let msg1 = super::super::from_level_1();

                println!("{}", msg1);
                println!("{}", msg2);
            }
        }

        pub fn run() {
            level_3::reach_up();
        }
    }

    pub fn start() {
        level_2::run();
    }
}

fn main() {
    level_1::start();
}
```

### Visual Trace of `super::super::`

```
level_3::reach_up() calls super::super::from_level_1()

Step 1:  super::         →  jumps from level_3 to level_2
                              ┌──────────────┐
                              │   level_2    │  ← we're here now
                              └──────────────┘

Step 2:  super::         →  jumps from level_2 to level_1
                              ┌──────────────┐
                              │   level_1    │  ← we're here now
                              └──────────────┘

Step 3:  from_level_1()  →  resolve item in level_1 → ✅ FOUND
```

### ⚠️ The Depth Limit

You **cannot** `super` past the crate root:

```rust
// At crate root, there is no parent:
// super::anything  ← COMPILE ERROR if used at crate root
```

```
crate (root)
 └── mod a
        └── super::  ✅ → reaches crate root
               └── super::  ❌ → ERROR: "there are too many leading `super` keywords"
```

---

## 7. `super` in Unit Tests — The Most Common Use Case {#7-tests}

This is where you will use `super` **every single day** in Rust.

### The Pattern

```rust
pub fn add(a: i32, b: i32) -> i32 {
    a + b
}

pub fn is_even(n: i32) -> bool {
    n % 2 == 0
}

//  ╔══════════════════════════════════════════════════╗
//  ║  The test module is a CHILD of the parent file   ║
//  ╚══════════════════════════════════════════════════╝
#[cfg(test)]
mod tests {
    use super::*;  // ← THE KEY LINE: import everything from parent module

    //       ↑
    //  super = the module that contains `add` and `is_even`
    //  *     = wildcard import (import ALL pub items)

    #[test]
    fn test_add() {
        assert_eq!(add(2, 3), 5);       // add is from super::*
        assert_eq!(add(-1, 1), 0);
    }

    #[test]
    fn test_is_even() {
        assert!(is_even(4));
        assert!(!is_even(7));
    }
}
```

### WHY `use super::*` in tests?

```
src/lib.rs (or any file)
    │
    ├── pub fn add(...)       ← defined at file level (= some module scope)
    ├── pub fn is_even(...)
    │
    └── mod tests {           ← tests is a CHILD module
            │
            │  The functions add() and is_even() are in the PARENT scope
            │  So tests must use super:: to access them
            │
            └── use super::*; ← bring ALL parent items into tests scope
```

### Full Real-World Test Module Example

```rust
// src/calculator.rs

#[derive(Debug, PartialEq)]
pub enum CalcError {
    DivisionByZero,
    Overflow,
}

pub fn divide(a: f64, b: f64) -> Result<f64, CalcError> {
    if b == 0.0 {
        return Err(CalcError::DivisionByZero);
    }
    Ok(a / b)
}

pub fn power(base: i64, exp: u32) -> Result<i64, CalcError> {
    base.checked_pow(exp).ok_or(CalcError::Overflow)
}

pub fn factorial(n: u64) -> u64 {
    if n <= 1 { 1 } else { n * factorial(n - 1) }
}

#[cfg(test)]
mod tests {
    use super::*;   // imports: divide, power, factorial, CalcError

    // Testing the happy path
    #[test]
    fn test_divide_normal() {
        assert_eq!(divide(10.0, 2.0), Ok(5.0));
    }

    // Testing error case — CalcError is accessible via super::*
    #[test]
    fn test_divide_by_zero() {
        assert_eq!(divide(5.0, 0.0), Err(CalcError::DivisionByZero));
    }

    #[test]
    fn test_power_overflow() {
        assert_eq!(power(i64::MAX, 2), Err(CalcError::Overflow));
    }

    #[test]
    fn test_factorial() {
        assert_eq!(factorial(0), 1);
        assert_eq!(factorial(5), 120);
        assert_eq!(factorial(10), 3628800);
    }

    // Nested test submodules
    mod edge_cases {
        use super::super::*; // super = tests, super::super = calculator module

        #[test]
        fn test_divide_negative() {
            assert_eq!(divide(-10.0, 2.0), Ok(-5.0));
        }
    }
}
```

### Why `super::super::*` in Nested Tests?

```
calculator module          ← super::super::  (2 hops)
    └── mod tests          ← super::          (1 hop)
            └── mod edge_cases  ← YOU ARE HERE
```

---

## 8. `super` vs `crate` — When to Choose Which {#8-super-vs-crate}

This is one of the most important design decisions in Rust module architecture.

```
┌─────────────────────────────────────────────────────────────────────┐
│                     super:: vs crate::                              │
├─────────────────────────────────────────────────────────────────────┤
│  super::                    │  crate::                              │
│  ─────────────────────────  │  ───────────────────────────────────  │
│  Relative path              │  Absolute path                        │
│  Depends on where you ARE   │  Always from root, never changes      │
│  Breaks if module is moved  │  Stable across reorganizations        │
│  Better for tight coupling  │  Better for large codebases           │
│  (parent ↔ child)           │  (cross-module references)            │
└─────────────────────────────────────────────────────────────────────┘
```

### Demonstration

```rust
// Project structure:
//
//  crate root (lib.rs)
//   ├── mod config
//   │       └── pub fn load() -> Config
//   └── mod server
//           └── mod handlers
//                   └── fn handle_request()

mod config {
    pub struct Config {
        pub port: u16,
    }
    pub fn load() -> Config {
        Config { port: 8080 }
    }
}

mod server {
    mod handlers {
        fn handle_request() {
            // Option A: super::super (relative — fragile)
            let cfg = super::super::config::load();

            // Option B: crate:: (absolute — stable and recommended)
            let cfg = crate::config::load();

            println!("Handling on port {}", cfg.port);
        }
    }
}
```

### Rule of Thumb

```
┌─────────────────────────────────────────────────────┐
│  USE super:: WHEN:                                  │
│    • You're in a direct parent-child relationship   │
│    • Writing #[cfg(test)] modules (ALWAYS super::*) │
│    • The relationship is tightly coupled by design  │
│                                                     │
│  USE crate:: WHEN:                                  │
│    • Referencing items more than 1-2 levels away    │
│    • You want refactoring safety                    │
│    • Working in large, complex module trees         │
│    • Referencing shared utilities from deep modules │
└─────────────────────────────────────────────────────┘
```

---

## 9. Visibility + `super`: `pub(super)` {#9-pub-super}

`pub(super)` is a **restricted visibility modifier** that says:

> "This item is public, but ONLY to my parent module."

### Visual Scope of `pub(super)`

```
crate
 ├── mod grandparent
 │       │
 │       ├── mod parent                 ← pub(super) items are visible HERE
 │       │       │
 │       │       └── mod child
 │       │               └── pub(super) fn secret()  ← defined HERE
 │       │                   ↑
 │       │          visible to `parent` ONLY
 │       │          NOT visible to `grandparent`
 │       │          NOT visible to crate root
 │       │
 │       └── fn try_access() {
 │               child::secret() ← ❌ COMPILE ERROR
 │           }
```

### Complete Example

```rust
mod company {
    // This function can only be seen by `company` (the parent of `hr`)
    mod hr {
        pub(super) fn view_salaries() -> Vec<u32> {
            vec![50_000, 75_000, 90_000]
        }

        pub fn hire_employee(name: &str) {
            println!("Hiring: {}", name);
            // hr can use view_salaries internally too
            let salaries = view_salaries();
            println!("Current team sizes match {} salaries", salaries.len());
        }
    }

    mod finance {
        pub fn audit() {
            // finance is a sibling of hr, NOT a parent
            // hr::view_salaries() ← ❌ COMPILE ERROR
            // pub(super) means ONLY parent (company) can see it

            println!("Running audit (no direct salary access)");
        }
    }

    // company IS the parent of hr, so it CAN call pub(super) fn
    pub fn executive_review() {
        let salaries = hr::view_salaries(); // ✅ company is parent of hr
        let total: u32 = salaries.iter().sum();
        println!("Total salary budget: ${}", total);
    }
}

fn main() {
    company::executive_review();

    // main() is at crate root — cannot reach hr::view_salaries()
    // company::hr::view_salaries() ← ❌ COMPILE ERROR
}
```

### `pub(super)` vs Other Visibilities

```
pub(super) fn f() {}

ACCESSIBLE FROM:
    ✅  The module itself (child module where f is defined)
    ✅  The direct parent module
    ❌  Grandparent module
    ❌  Sibling modules
    ❌  Crate root
    ❌  External crates


pub(crate) fn g() {}

ACCESSIBLE FROM:
    ✅  Anywhere inside this crate
    ❌  External crates


pub fn h() {}

ACCESSIBLE FROM:
    ✅  Anywhere (including external crates if re-exported)
```

---

## 10. Real-World Implementation: Library Architecture {#10-real-world-lib}

Let's model a real database library using `super` thoughtfully:

```rust
// ─── lib.rs ───────────────────────────────────────────────────

pub mod database {

    // ── Core types shared across submodules ───────────────────
    #[derive(Debug, Clone)]
    pub struct Connection {
        pub host: String,
        pub port: u16,
        pub max_pool: usize,
    }

    impl Connection {
        pub fn new(host: &str, port: u16) -> Self {
            Connection {
                host: host.to_string(),
                port,
                max_pool: 10,
            }
        }
    }

    #[derive(Debug)]
    pub enum DbError {
        ConnectionFailed,
        QueryFailed(String),
        Timeout,
    }

    // ── Query builder submodule ───────────────────────────────
    pub mod query {
        use super::Connection;    // needs parent's Connection type
        use super::DbError;       // needs parent's error type

        pub struct Query {
            conn: Connection,
            sql: String,
        }

        impl Query {
            pub fn new(conn: Connection, sql: &str) -> Self {
                Query { conn, sql: sql.to_string() }
            }

            pub fn execute(&self) -> Result<Vec<String>, DbError> {
                if self.sql.is_empty() {
                    return Err(DbError::QueryFailed("Empty SQL".into()));
                }
                println!(
                    "[{}:{}] Executing: {}",
                    self.conn.host, self.conn.port, self.sql
                );
                Ok(vec!["row1".into(), "row2".into()])
            }
        }

        // ── Transaction submodule ─────────────────────────────
        pub mod transaction {
            use super::super::Connection;  // query's parent = database
            use super::super::DbError;
            use super::Query;              // sibling in `query` module

            pub struct Transaction {
                queries: Vec<Query>,
            }

            impl Transaction {
                pub fn new() -> Self {
                    Transaction { queries: Vec::new() }
                }

                pub fn add(&mut self, conn: Connection, sql: &str) {
                    self.queries.push(Query::new(conn, sql));
                }

                pub fn commit(&self) -> Result<(), DbError> {
                    println!("Beginning transaction...");
                    for q in &self.queries {
                        q.execute()?;
                    }
                    println!("Transaction committed.");
                    Ok(())
                }

                pub fn rollback(&self) {
                    println!("Transaction rolled back.");
                }
            }
        }
    }

    // ── Migration submodule ───────────────────────────────────
    pub mod migration {
        use super::Connection;    // go up to database module
        use super::DbError;
        use super::query::Query;  // sibling of migration

        pub fn run_migration(conn: Connection, script: &str) -> Result<(), DbError> {
            println!("Running migration script...");
            let q = Query::new(conn, script);
            q.execute()?;
            println!("Migration complete.");
            Ok(())
        }
    }

    // ── Tests for the database module ─────────────────────────
    #[cfg(test)]
    mod tests {
        use super::*;              // brings Connection, DbError, query, migration
        use super::query::Query;
        use super::query::transaction::Transaction;

        #[test]
        fn test_connection_defaults() {
            let conn = Connection::new("localhost", 5432);
            assert_eq!(conn.max_pool, 10);
            assert_eq!(conn.port, 5432);
        }

        #[test]
        fn test_query_empty_sql() {
            let conn = Connection::new("localhost", 5432);
            let q = Query::new(conn, "");
            let result = q.execute();
            assert!(matches!(result, Err(DbError::QueryFailed(_))));
        }

        #[test]
        fn test_transaction_commit() {
            let mut tx = Transaction::new();
            tx.add(Connection::new("localhost", 5432), "INSERT INTO users VALUES (1)");
            tx.add(Connection::new("localhost", 5432), "INSERT INTO logs VALUES (1)");
            assert!(tx.commit().is_ok());
        }
    }
}
```

### Module Relationship Diagram

```
database (pub mod)
  │
  ├── Connection (struct)
  ├── DbError (enum)
  │
  ├── query (pub mod)
  │     │
  │     ├── Query (struct)       ← uses super::Connection, super::DbError
  │     │
  │     └── transaction (pub mod)
  │           │
  │           └── Transaction    ← uses super::Query
  │                              ← uses super::super::Connection  (= database)
  │                              ← uses super::super::DbError     (= database)
  │
  ├── migration (pub mod)
  │     └── run_migration()     ← uses super::Connection, super::query::Query
  │
  └── tests (#[cfg(test)])
        └── use super::*        ← gets Connection, DbError, query, migration
```

---

## 11. Real-World Implementation: Game Engine Module {#11-real-world-game}

```rust
mod engine {
    // ── Shared types ──────────────────────────────────────────
    #[derive(Debug, Clone, Copy)]
    pub struct Vec2 {
        pub x: f32,
        pub y: f32,
    }

    impl Vec2 {
        pub fn new(x: f32, y: f32) -> Self { Vec2 { x, y } }
        pub fn length(&self) -> f32 {
            (self.x * self.x + self.y * self.y).sqrt()
        }
    }

    pub trait Component: std::fmt::Debug {}

    // ── Physics submodule ─────────────────────────────────────
    pub mod physics {
        use super::Vec2;   // needs engine's Vec2
        use super::Component;

        #[derive(Debug)]
        pub struct RigidBody {
            pub position: Vec2,
            pub velocity: Vec2,
            pub mass: f32,
        }

        impl Component for RigidBody {}

        impl RigidBody {
            pub fn new(x: f32, y: f32, mass: f32) -> Self {
                RigidBody {
                    position: Vec2::new(x, y),
                    velocity: Vec2::new(0.0, 0.0),
                    mass,
                }
            }

            pub fn apply_force(&mut self, force: Vec2) {
                // F = ma → a = F/m → v += a * dt (dt=1 simplified)
                self.velocity.x += force.x / self.mass;
                self.velocity.y += force.y / self.mass;
            }

            pub fn update(&mut self) {
                self.position.x += self.velocity.x;
                self.position.y += self.velocity.y;
            }
        }

        // ── Collision detection sub-submodule ─────────────────
        pub mod collision {
            use super::RigidBody;        // parent = physics
            use super::super::Vec2;      // grandparent = engine

            pub fn check_aabb(a: &RigidBody, b: &RigidBody, size: f32) -> bool {
                let dx = (a.position.x - b.position.x).abs();
                let dy = (a.position.y - b.position.y).abs();
                dx < size && dy < size
            }

            pub fn resolve_collision(a: &mut RigidBody, b: &mut RigidBody) {
                // Simple elastic collision: swap velocities
                let temp = a.velocity;
                a.velocity = b.velocity;
                b.velocity = temp;
                println!(
                    "Collision resolved between bodies at {:?} and {:?}",
                    a.position, b.position
                );
            }
        }
    }

    // ── Render submodule ──────────────────────────────────────
    pub mod render {
        use super::Vec2;
        use super::physics::RigidBody;  // sibling module

        pub fn draw_body(body: &RigidBody) {
            println!(
                "◉ Drawing body at ({:.2}, {:.2}) vel=({:.2},{:.2})",
                body.position.x, body.position.y,
                body.velocity.x, body.velocity.y
            );
        }
    }

    // ── Main game loop ────────────────────────────────────────
    pub fn run_simulation() {
        use physics::RigidBody;
        use physics::collision::{check_aabb, resolve_collision};
        use render::draw_body;

        let mut player = RigidBody::new(0.0, 0.0, 1.0);
        let mut enemy  = RigidBody::new(3.0, 0.0, 2.0);

        // Apply forces
        player.apply_force(Vec2::new(1.5, 0.0));
        enemy.apply_force(Vec2::new(-0.5, 0.0));

        // Simulate 5 frames
        for frame in 0..5 {
            player.update();
            enemy.update();

            draw_body(&player);
            draw_body(&enemy);

            if check_aabb(&player, &enemy, 1.5) {
                println!("⚡ Frame {}: COLLISION!", frame);
                resolve_collision(&mut player, &mut enemy);
            }
        }
    }

    #[cfg(test)]
    mod tests {
        use super::*;
        use super::physics::RigidBody;
        use super::physics::collision::check_aabb;

        #[test]
        fn test_vec2_length() {
            let v = Vec2::new(3.0, 4.0);
            assert_eq!(v.length(), 5.0);
        }

        #[test]
        fn test_rigid_body_force() {
            let mut body = RigidBody::new(0.0, 0.0, 2.0);
            body.apply_force(Vec2::new(4.0, 0.0));
            assert_eq!(body.velocity.x, 2.0); // F/m = 4/2 = 2
        }

        #[test]
        fn test_collision_detection() {
            let a = RigidBody::new(0.0, 0.0, 1.0);
            let b = RigidBody::new(0.5, 0.5, 1.0);
            assert!(check_aabb(&a, &b, 1.0));  // close enough to collide
        }
    }
}

fn main() {
    engine::run_simulation();
}
```

---

## 12. Real-World Implementation: Web Server Router {#12-real-world-web}

```rust
mod server {
    use std::collections::HashMap;

    // ── Shared Request/Response types ─────────────────────────
    #[derive(Debug, Clone)]
    pub struct Request {
        pub method: String,
        pub path: String,
        pub headers: HashMap<String, String>,
        pub body: Option<String>,
    }

    impl Request {
        pub fn get(path: &str) -> Self {
            Request {
                method: "GET".into(),
                path: path.to_string(),
                headers: HashMap::new(),
                body: None,
            }
        }

        pub fn post(path: &str, body: &str) -> Self {
            Request {
                method: "POST".into(),
                path: path.to_string(),
                headers: HashMap::new(),
                body: Some(body.to_string()),
            }
        }
    }

    #[derive(Debug)]
    pub struct Response {
        pub status: u16,
        pub body: String,
    }

    impl Response {
        pub fn ok(body: &str) -> Self {
            Response { status: 200, body: body.to_string() }
        }
        pub fn not_found() -> Self {
            Response { status: 404, body: "Not Found".to_string() }
        }
        pub fn bad_request(msg: &str) -> Self {
            Response { status: 400, body: msg.to_string() }
        }
    }

    // ── Middleware submodule ───────────────────────────────────
    pub mod middleware {
        use super::Request;   // parent's Request type
        use super::Response;

        pub fn log(req: &Request) {
            println!("[LOG] {} {}", req.method, req.path);
        }

        pub fn auth_check(req: &Request) -> bool {
            req.headers.get("Authorization").map_or(false, |v| v == "Bearer secret123")
        }

        pub fn cors_headers(resp: &mut Response) {
            println!("[CORS] Adding Access-Control-Allow-Origin: *");
        }
    }

    // ── Route handlers submodule ──────────────────────────────
    pub mod handlers {
        use super::Request;
        use super::Response;
        use super::middleware; // sibling of handlers

        pub fn handle_users(req: &Request) -> Response {
            middleware::log(req);

            match req.method.as_str() {
                "GET" => Response::ok(r#"{"users": ["alice", "bob"]}"#),
                "POST" => {
                    if let Some(body) = &req.body {
                        Response::ok(&format!("Created user from: {}", body))
                    } else {
                        Response::bad_request("Body required for POST")
                    }
                }
                _ => Response::not_found(),
            }
        }

        pub fn handle_health(_req: &Request) -> Response {
            Response::ok(r#"{"status": "healthy"}"#)
        }

        // ── Protected route handlers ──────────────────────────
        pub mod protected {
            use super::super::Request;     // handlers → server → Request
            use super::super::Response;
            use super::super::middleware;  // handlers → server → middleware

            pub fn handle_admin(req: &Request) -> Response {
                middleware::log(req);

                if !middleware::auth_check(req) {
                    return Response { status: 401, body: "Unauthorized".into() };
                }

                Response::ok(r#"{"admin": true, "users": 42}"#)
            }
        }
    }

    // ── Router ────────────────────────────────────────────────
    pub fn route(req: Request) -> Response {
        let mut resp = match req.path.as_str() {
            "/users"  => handlers::handle_users(&req),
            "/health" => handlers::handle_health(&req),
            "/admin"  => handlers::protected::handle_admin(&req),
            _         => Response::not_found(),
        };
        middleware::cors_headers(&mut resp);
        resp
    }

    // ── Tests ─────────────────────────────────────────────────
    #[cfg(test)]
    mod tests {
        use super::*;
        use super::handlers::{handle_users, handle_health};
        use super::handlers::protected::handle_admin;

        #[test]
        fn test_get_users() {
            let req = Request::get("/users");
            let resp = handle_users(&req);
            assert_eq!(resp.status, 200);
            assert!(resp.body.contains("alice"));
        }

        #[test]
        fn test_post_user_no_body() {
            let req = Request { method: "POST".into(), path: "/users".into(),
                                headers: Default::default(), body: None };
            let resp = handle_users(&req);
            assert_eq!(resp.status, 400);
        }

        #[test]
        fn test_admin_unauthorized() {
            let req = Request::get("/admin");
            let resp = handle_admin(&req);
            assert_eq!(resp.status, 401);
        }

        #[test]
        fn test_admin_authorized() {
            let mut req = Request::get("/admin");
            req.headers.insert("Authorization".into(), "Bearer secret123".into());
            let resp = handle_admin(&req);
            assert_eq!(resp.status, 200);
        }

        #[test]
        fn test_router_not_found() {
            let req = Request::get("/nonexistent");
            let resp = route(req);
            assert_eq!(resp.status, 404);
        }
    }
}

fn main() {
    let req = server::Request::get("/users");
    let resp = server::route(req);
    println!("Status: {}", resp.status);
    println!("Body:   {}", resp.body);
}
```

---

## 13. Common Mistakes & Pitfalls {#13-pitfalls}

### Mistake 1: Using `super` Past the Crate Root

```rust
// At crate root level:
use super::something; // ❌ ERROR: no parent beyond the crate root

// Fix: use crate:: instead
use crate::something;
```

### Mistake 2: Forgetting Visibility on Parent Items

```rust
mod parent {
    fn private_fn() { } // NOT pub!

    mod child {
        fn run() {
            super::private_fn(); // ❌ ERROR: private_fn is private to parent
        }
    }
}

// Fix:
mod parent {
    pub fn private_fn() { } // or pub(super) if only child needs it

    mod child {
        fn run() {
            super::private_fn(); // ✅
        }
    }
}
```

### Mistake 3: Unnecessary `super` Chains

```rust
// Deep super chains are a code smell
use super::super::super::utils::format; // ❌ fragile and hard to read

// Fix: use crate:: for multi-level jumps
use crate::utils::format;               // ✅ stable and clear
```

### Mistake 4: Forgetting `super` in Tests

```rust
fn add(a: i32, b: i32) -> i32 { a + b }

#[cfg(test)]
mod tests {
    #[test]
    fn test_add() {
        assert_eq!(add(1, 2), 3); // ❌ ERROR: `add` is not in scope!
    }

    // Fix:
    use super::*; // Add THIS at the top of the test module
}
```

### Mistake 5: Confusing Module Path with File Path

```
FILE: src/utils/parser.rs
MODULE PATH: crate::utils::parser

If you're inside src/utils/parser.rs, `super` refers to `crate::utils`,
NOT to `src/`. The module tree ≠ the file system exactly.
```

---

## 14. Decision Tree: When to Use `super` {#14-decision-tree}

```
START: You need to reference something from another location
              │
              ▼
    ┌─────────────────────────┐
    │  Is it in the SAME      │
    │  module (same file      │──── YES ──→  Use bare name or `self::`
    │  scope)?                │
    └─────────────┬───────────┘
                  │ NO
                  ▼
    ┌─────────────────────────┐
    │  Is it in your DIRECT   │
    │  PARENT module?         │──── YES ──→  Use `super::`
    └─────────────┬───────────┘
                  │ NO
                  ▼
    ┌─────────────────────────┐
    │  Is it 2 levels up      │
    │  (grandparent)?         │──── YES ──→  Consider `super::super::`
    └─────────────┬───────────┘                OR prefer `crate::`
                  │ NO
                  ▼
    ┌─────────────────────────┐
    │  Is it 3+ levels up     │
    │  OR a sibling/cousin    │──── YES ──→  Use `crate::` (absolute path)
    │  module?                │
    └─────────────┬───────────┘
                  │ NO
                  ▼
    ┌─────────────────────────┐
    │  Is it in an external   │
    │  crate?                 │──── YES ──→  Use the crate name directly
    └─────────────────────────┘               e.g. `serde::Deserialize`


SPECIAL CASE — Tests:
    ┌─────────────────────────┐
    │  Are you in a           │
    │  #[cfg(test)] module?   │──── YES ──→  ALWAYS use `use super::*;`
    └─────────────────────────┘               at the top
```

---

## 15. Mental Models & Cognitive Anchors {#15-mental-models}

### Model 1: The Org Chart Metaphor

```
CEO (crate root)
 ├── VP Engineering (mod engineering)
 │       ├── Team Lead Backend (mod backend)
 │       │       └── Developer (mod you are here)
 │       │               super:: → Team Lead Backend
 │       │               super::super:: → VP Engineering
 │       │               crate:: → CEO level
 │       └── Team Lead Frontend
 └── VP Sales

Rule: `super` is like escalating to your direct manager.
      Don't skip levels (use crate:: for that).
```

### Model 2: Russian Dolls (Matryoshka)

```
┌─────────────────────────────┐
│  crate                      │
│  ┌───────────────────────┐  │
│  │  mod outer            │  │
│  │  ┌─────────────────┐  │  │
│  │  │  mod inner      │  │  │
│  │  │  ← YOU ARE HERE │  │  │
│  │  │  super:: opens  │  │  │
│  │  │  one doll out   │  │  │
│  │  └─────────────────┘  │  │
│  └───────────────────────┘  │
└─────────────────────────────┘

Opening one doll = super::
Opening two dolls = super::super::
```

### Cognitive Principle: **Chunking**

> When you see `use super::*;` in test modules, chunk it as a **single atomic concept**: "test module imports its parent." Stop parsing it as individual tokens — recognize the pattern instantly.

Build these chunks as you practice:
- `use super::*` → "I'm in a test, importing everything from parent"  
- `super::super::` → "I'm deep, climbing two levels"  
- `pub(super)` → "only my parent can touch this"

### Cognitive Principle: **Deliberate Practice with Module Design**

Don't just read code. Every day, **draw the module tree** of something you're writing:

```
1. Sketch your module tree on paper
2. For each module, identify: what does it need from its parent?
3. Write those as super:: dependencies explicitly
4. Then ask: could I make this more stable with crate::?
5. Refactor accordingly
```

This builds **spatial reasoning** about code structure — a key skill of senior engineers.

---

## Quick Reference Summary

```
┌──────────────────────────────────────────────────────────────────┐
│                    SUPER KEYWORD CHEATSHEET                      │
├──────────────────────────┬───────────────────────────────────────┤
│  SYNTAX                  │  MEANING                              │
├──────────────────────────┼───────────────────────────────────────┤
│  super::item             │  item in parent module                │
│  super::super::item      │  item in grandparent module           │
│  use super::item         │  import item from parent              │
│  use super::*            │  import all pub items from parent     │
│  pub(super) fn f(){}     │  f visible ONLY to parent module      │
│  super::ModName::item    │  item in sibling module via parent    │
├──────────────────────────┼───────────────────────────────────────┤
│  MOST COMMON USE         │  #[cfg(test)] mod tests {             │
│                          │      use super::*;   ← THIS           │
│                          │  }                                    │
├──────────────────────────┼───────────────────────────────────────┤
│  NEVER DO                │  super:: at crate root level          │
│                          │  super::super::super:: (use crate::)  │
│                          │  super:: a private item               │
└──────────────────────────┴───────────────────────────────────────┘
```

---

*Master the module tree, and you master Rust's entire code organization model.*  
*`super` is not just a keyword — it is your map through the architecture.*

Here's your complete `super` keyword guide. Let me walk you through what's inside and the **core mental model** to lock in:

---

## The One Sentence That Explains Everything

> `super` in Rust is `cd ..` for the module system — it walks **one level up** the module tree to the parent module.

---

## The 5 Pillars of `super`

**1. Path Navigation** — `super::fn_name()` calls a function in the parent module. Works in both inline paths and `use` statements.

**2. Chaining** — `super::super::` climbs two levels. But if you go more than 2, use `crate::` instead — it's an absolute path that never breaks during refactoring.

**3. Test Modules (Most Important in Practice)** — Every `#[cfg(test)] mod tests` is a *child* of the file it lives in. So `use super::*` is how you bring the file's functions/types into the test scope. You will write this hundreds of times.

**4. Restricted Visibility `pub(super)`** — Exposes an item *only* to the parent module. Tighter than `pub`, wider than private. Perfect for internal APIs you don't want leaking further up the tree.

**5. The Trinity** — `self::` (here), `super::` (parent), `crate::` (root). These three path anchors are the navigation system of all Rust code.

---

## The Decision You'll Make Every Day

```
Need something from...         Use...
─────────────────────────────────────────
Same module?              →    bare name or self::
Direct parent?            →    super::
Grandparent or further?   →    crate:: (prefer this)
In a #[cfg(test)] block?  →    ALWAYS use super::*
```

The guide contains 3 complete real-world implementations (database library, game engine physics, HTTP router) that show `super` operating in realistic, production-style module trees — study those for pattern recognition.