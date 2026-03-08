# The `pub` Keyword in Rust — A Complete Master Guide

> *"Encapsulation is not about hiding implementation details for the sake of hiding them.  
> It is about defining invariants that the compiler will enforce forever."*

---

## Table of Contents

1. [The Philosophy: Why Rust's Privacy Model Exists](#1-the-philosophy)
2. [The Privacy Hierarchy — All Five Visibility Levels](#2-visibility-levels)
3. [Module System Fundamentals — The Stage for `pub`](#3-module-system)
4. [Applying `pub` to Every Rust Construct](#4-applying-pub)
5. [`pub use` — Re-exports and the Public API Surface](#5-pub-use)
6. [Struct Field Visibility — Invariant Enforcement](#6-struct-fields)
7. [Enum Visibility](#7-enum-visibility)
8. [Traits and `pub`](#8-traits)
9. [`pub` in `impl` Blocks](#9-impl-blocks)
10. [Constants, Statics, and Type Aliases](#10-constants-statics)
11. [Visibility in `use` Declarations](#11-use-declarations)
12. [Real-World Architectural Patterns](#12-real-world-patterns)
13. [The Orphan Rule and Visibility Interaction](#13-orphan-rule)
14. [Common Pitfalls and Subtle Behaviors](#14-pitfalls)
15. [Mental Models for Reasoning About Visibility](#15-mental-models)

---

## 1. The Philosophy

### Why Rust Has a Privacy System

Most languages use privacy as a *convention* (`_private` in Python) or
as *soft enforcement* (Java's package-private). Rust uses privacy as a
**compile-time invariant guarantee**.

The core insight: **if a field or function is private, no code outside
its module can violate the invariants that field is supposed to maintain.**

This is not aesthetic — it's correctness engineering. Consider a
`NonZeroU32` type. If the inner value were public, anyone could write
`n.value = 0`, breaking the invariant. Because it is private, the
compiler *structurally prevents* the invariant from being broken —
forever, for any downstream crate.

```rust
// The standard library's NonZeroU32 — simplified
pub struct NonZeroU32(u32); // inner u32 is PRIVATE

impl NonZeroU32 {
    // Only constructor: enforces the invariant at the boundary
    pub fn new(n: u32) -> Option<Self> {
        if n != 0 { Some(Self(n)) } else { None }
    }

    pub fn get(self) -> u32 {
        self.0 // safe: we KNOW it's nonzero
    }
}
```

**Mental Model:** Think of `pub` as defining **trust boundaries**.
Everything inside a module trusts everything else in that module.
`pub` decides which pieces of trust you extend outward.

---

## 2. Visibility Levels

Rust has **five distinct visibility levels**, not just public/private.

### The Complete Hierarchy (most restrictive → least restrictive)

```
private (default)
    │
pub(self)          ← identical to private, explicit form
    │
pub(super)         ← visible to parent module
    │
pub(in some::path) ← visible within a specific ancestor module
    │
pub(crate)         ← visible within the entire crate
    │
pub                ← visible everywhere (across crates)
```

### 2.1 Private (Default)

If you write nothing, the item is private to its **defining module**.

```rust
mod engine {
    fn combustion_cycle() { // private: only accessible within `engine`
        println!("BOOM");
    }

    pub fn start() {
        combustion_cycle(); // ✅ same module: allowed
    }
}

fn main() {
    engine::start();           // ✅ pub: allowed
    // engine::combustion_cycle(); // ❌ compile error: private
}
```

**Key subtlety:** Private items are visible to *descendant* modules
(child modules can see private items of ancestors), but not to
*sibling* or *ancestor* modules.

```rust
mod outer {
    fn secret() -> u32 { 42 }

    mod inner {
        fn use_secret() {
            super::secret(); // ✅ child accessing parent private: ALLOWED
        }
    }
}
```

This is Rust's unique rule — children can see parent privates.
This enables "implementation modules" that have access to internal
state without exposing it outward.

### 2.2 `pub(self)` — Explicit Private

Semantically identical to the default private. Used when you want
to be *explicit* in a `pub(...)` context for clarity or macros.

```rust
pub(self) fn internal_helper() { } // identical to just `fn internal_helper()`
```

### 2.3 `pub(super)` — Parent Module Visibility

Visible within the parent module and any of its descendants.

```rust
mod graphics {
    mod shader {
        pub(super) fn compile_glsl(src: &str) -> Vec<u8> {
            // Only `graphics` module can call this
            vec![]
        }
    }

    mod pipeline {
        fn build() {
            // ❌ sibling module: cannot access pub(super) from shader
            // shader::compile_glsl("...");
        }
    }

    fn init_graphics() {
        // ✅ `graphics` is `shader`'s parent: can access pub(super)
        let bytecode = shader::compile_glsl("void main() {}");
    }
}
```

**When to use:** When you have implementation submodules that need
to expose helpers to their parent for assembly, but not to the world.

### 2.4 `pub(crate)` — Crate-Wide Visibility

The workhorse of library internals. Visible anywhere within the
same crate, but invisible to downstream users of your library.

```rust
// src/lib.rs
pub(crate) struct InternalBuffer {
    data: Vec<u8>,
    capacity: usize,
}

// src/io.rs — same crate
use crate::InternalBuffer; // ✅ crate-visible

// downstream user's code
use my_lib::InternalBuffer; // ❌ not pub: cannot see it
```

**When to use:** Shared internal infrastructure — error types,
helper structs, internal traits — that multiple modules within your
crate need but should not be part of your public API.

### 2.5 `pub(in path)` — Path-Scoped Visibility

The most precise visibility specifier. Limits visibility to a
specific ancestor module by path.

```rust
mod a {
    mod b {
        mod c {
            pub(in crate::a) fn only_a_can_see_me() {
                // visible to module `a` and all its descendants
            }

            pub(in crate::a::b) fn only_b_can_see_me() {
                // visible to module `b` and all its descendants
            }
        }

        fn test_b() {
            c::only_a_can_see_me(); // ✅ b is a descendant of a
            c::only_b_can_see_me(); // ✅ b is the exact scope
        }
    }

    fn test_a() {
        b::c::only_a_can_see_me(); // ✅ a is the specified scope
        // b::c::only_b_can_see_me(); // ❌ a is NOT a descendant of b
    }
}
```

**Constraint:** The path must be an *ancestor* of the defining module.
You cannot grant visibility to a sibling or unrelated module.

### 2.6 `pub` — Fully Public

Visible everywhere — within the crate, to any downstream crate that
imports you, and potentially to binaries using your library.

```rust
pub fn add(a: i32, b: i32) -> i32 { a + b } // visible to the universe
```

---

## 3. Module System Fundamentals

The `pub` keyword is meaningless without understanding Rust's module system.
They are inseparable.

### 3.1 Module Declaration Forms

```rust
// FORM 1: Inline module
mod math {
    pub fn square(x: i64) -> i64 { x * x }
}

// FORM 2: File module (compiler looks for src/math.rs or src/math/mod.rs)
mod math; // in src/lib.rs or src/main.rs

// FORM 3: Nested file module
// In src/graphics/mod.rs:
pub mod shader; // compiler looks for src/graphics/shader.rs
```

### 3.2 The Module Tree

Every crate has a root module (`crate::`) and all modules form a tree.
Privacy is always relative to a *position in this tree*.

```
crate (src/lib.rs)
 ├── pub mod api          → src/api.rs
 │    ├── pub mod routes  → src/api/routes.rs
 │    └── mod middleware  → src/api/middleware.rs  (private)
 ├── pub(crate) mod db    → src/db.rs
 └── mod internal         → src/internal.rs        (private)
```

### 3.3 The Critical Rule: Reachability

**An item is accessible only if BOTH conditions are true:**
1. The item itself is visible at the use site.
2. The *path* to reach the item (every module in the chain) is also visible.

```rust
mod outer {        // private: only accessible within crate root
    pub mod inner {
        pub fn hello() {} // pub: but can you reach it?
    }
}

fn main() {
    // outer::inner::hello() is UNREACHABLE because `outer` is private.
    // Even though `inner` and `hello` are pub, the path is blocked.
}
```

This is why library authors often need to re-export: to make the path
accessible without exposing the entire module structure.

---

## 4. Applying `pub` to Every Rust Construct

### 4.1 Functions

```rust
mod net {
    // Private: implementation detail
    fn tcp_handshake(addr: &str) -> bool { true }

    // pub(crate): used by other modules internally
    pub(crate) fn raw_connect(addr: &str) -> std::io::Result<()> {
        if tcp_handshake(addr) { Ok(()) } else {
            Err(std::io::Error::from(std::io::ErrorKind::ConnectionRefused))
        }
    }

    // pub: user-facing API
    pub fn connect(addr: &str) -> std::io::Result<()> {
        raw_connect(addr)
    }
}
```

### 4.2 Modules

```rust
// Modules themselves carry visibility
pub mod api;          // fully public module
pub(crate) mod db;    // crate-internal module
mod internals;        // private module (still usable by submodules)
```

### 4.3 Closures and `pub`

Closures are values, not declarations — they don't directly take `pub`.
But the *binding* they're stored in does:

```rust
pub static VALIDATOR: fn(&str) -> bool = |s| !s.is_empty();
pub(crate) const TRANSFORM: fn(u8) -> u8 = |b| b.wrapping_add(1);
```

---

## 5. `pub use` — Re-exports and the Public API Surface

This is one of Rust's most powerful API design tools.

### 5.1 Basic Re-export

```rust
// src/lib.rs
mod parsing;  // private module

// Expose only what users need — not the entire module
pub use parsing::Parser;
pub use parsing::ParseError;
// `parsing::InternalState` remains hidden
```

### 5.2 The Facade Pattern — Flattening Nested Modules

This is the canonical way to build ergonomic library APIs in Rust.

```
Project structure:
src/
  lib.rs
  collections/
    mod.rs
    vec_deque.rs
    linked_list.rs
    btree/
      map.rs
      set.rs
```

```rust
// src/lib.rs — the public facade
pub use collections::VecDeque;
pub use collections::LinkedList;
pub use collections::btree::BTreeMap;
pub use collections::btree::BTreeSet;

mod collections; // private: users don't need to know the structure
```

Users write `use mylib::BTreeMap` instead of
`use mylib::collections::btree::BTreeMap`. The internal module
structure is irrelevant to them.

### 5.3 Re-exporting from Other Crates

```rust
// Publicly re-export a dependency's type as part of YOUR API
pub use serde::{Serialize, Deserialize};
// Now users can: `use mylib::Serialize;`
// They don't need serde as a direct dependency for YOUR types
```

**Expert insight:** This is a versioning strategy. If you re-export
`serde::Serialize` as your own, you control which version of serde
you expose. If you change it, you do so in one place.

### 5.4 `pub use self::` — Idiomatic Module Re-export

```rust
mod error {
    pub struct Error { /* ... */ }
    pub type Result<T> = std::result::Result<T, Error>;
}

// In parent module:
pub use self::error::{Error, Result};
```

### 5.5 Glob Re-exports — The Prelude Pattern

```rust
// src/prelude.rs
pub use crate::core::Config;
pub use crate::core::Runtime;
pub use crate::traits::{Handler, Middleware};
pub use crate::error::{Error, Result};

// src/lib.rs
pub mod prelude; // users: `use mylib::prelude::*;`
```

This is exactly how `std::prelude::*` works in Rust. You get
`Vec`, `Option`, `Result`, etc. without explicit imports.

---

## 6. Struct Field Visibility — Invariant Enforcement

This is where Rust's privacy model becomes genuinely powerful.

### 6.1 Default: All Fields Private

```rust
pub struct Config {
    host: String,      // private
    port: u16,         // private
    max_retries: u8,   // private
}
```

Even though `Config` is `pub`, none of its fields are accessible
from outside the module. This forces construction through defined
constructors.

### 6.2 Selective Field Exposure

```rust
pub struct Measurement {
    pub value: f64,       // pub: users can read AND write
    pub unit: &'static str, // pub
    precision: u8,        // private: internal formatting detail
}
```

### 6.3 The Constructor Pattern — Enforcing Invariants

```rust
pub struct EmailAddress {
    // PRIVATE: must be a valid email. We enforce this at construction.
    address: String,
}

impl EmailAddress {
    pub fn new(raw: &str) -> Result<Self, &'static str> {
        if raw.contains('@') && raw.contains('.') {
            Ok(Self { address: raw.to_string() })
        } else {
            Err("Invalid email address")
        }
    }

    pub fn as_str(&self) -> &str {
        &self.address
    }

    pub fn domain(&self) -> &str {
        // Safe: we know `@` exists because of the constructor invariant
        self.address.split('@').nth(1).unwrap()
    }
}
```

**The invariant guarantee:** Because `address` is private, the
compiler guarantees that `domain()` will *never panic* — the `unwrap()`
is unconditionally safe because no external code could have bypassed
the `new()` constructor to create an invalid state.

### 6.4 The Builder Pattern with Visibility

```rust
pub struct ServerConfig {
    host: String,
    port: u16,
    workers: usize,
    tls_enabled: bool,
}

pub struct ServerConfigBuilder {
    host: String,
    port: u16,
    workers: usize,
    tls_enabled: bool,
}

impl ServerConfigBuilder {
    pub fn new() -> Self {
        Self {
            host: "127.0.0.1".to_string(),
            port: 8080,
            workers: num_cpus(),
            tls_enabled: false,
        }
    }

    pub fn host(mut self, h: &str) -> Self { self.host = h.to_string(); self }
    pub fn port(mut self, p: u16) -> Self { self.port = p; self }
    pub fn workers(mut self, w: usize) -> Self { self.workers = w; self }
    pub fn tls(mut self) -> Self { self.tls_enabled = true; self }

    pub fn build(self) -> Result<ServerConfig, &'static str> {
        if self.port == 0 {
            return Err("Port cannot be zero");
        }
        Ok(ServerConfig {
            host: self.host,
            port: self.port,
            workers: self.workers,
            tls_enabled: self.tls_enabled,
        })
    }
}

fn num_cpus() -> usize { 4 } // stub

// Usage:
// let cfg = ServerConfigBuilder::new()
//     .host("0.0.0.0")
//     .port(443)
//     .tls()
//     .build()?;
```

### 6.5 `#[non_exhaustive]` — Forward Compatibility with `pub` Structs

When all fields must be `pub` but you want freedom to add fields later:

```rust
#[non_exhaustive]
pub struct Event {
    pub kind: EventKind,
    pub timestamp: u64,
    pub payload: Vec<u8>,
}

// Downstream code CANNOT destructure this exhaustively:
// let Event { kind, timestamp, payload } = e; // ❌ compile error
// Must use: let kind = e.kind; // ✅
```

---

## 7. Enum Visibility

Enums have a simpler visibility model than structs: variants always
inherit the enum's visibility.

### 7.1 Basic Enum Visibility

```rust
pub enum Status {
    Active,    // automatically pub (enum is pub)
    Inactive,  // automatically pub
    Pending,   // automatically pub
}
```

You cannot make individual variants private — if the enum is `pub`,
all variants are `pub`. This is by design: enums represent a *complete*
set of cases, and hiding variants would break exhaustive matching.

### 7.2 Hiding an Enum Entirely

```rust
pub(crate) enum InternalState {
    Idle,
    Processing { batch_size: usize },
    Flushing,
}
```

### 7.3 Enum Variant Fields — Selective Exposure

Struct-like variant fields *can* have individual visibility:

```rust
pub enum Message {
    Ping,
    Data {
        pub payload: Vec<u8>,     // pub field in variant
        checksum: u32,            // private field in variant
    },
}
```

**Note:** In practice, variant fields with mixed visibility are rare.
Prefer keeping variant fields public or encapsulating the variant
behind a method.

### 7.4 `#[non_exhaustive]` on Enums

```rust
#[non_exhaustive]
pub enum Error {
    NotFound,
    PermissionDenied,
    TimedOut,
    // Future variants can be added without breaking downstream code
}

// Downstream must handle the wildcard:
match err {
    Error::NotFound => {},
    Error::PermissionDenied => {},
    Error::TimedOut => {},
    _ => {} // REQUIRED because of #[non_exhaustive]
}
```

---

## 8. Traits and `pub`

### 8.1 Trait Visibility

```rust
pub trait Serialize {        // visible everywhere
    fn serialize(&self) -> Vec<u8>;
}

pub(crate) trait InternalCodec { // crate-internal
    fn encode(&self) -> u64;
}

trait PrivateStrategy {      // private: implementation detail
    fn execute(&self);
}
```

### 8.2 Trait Method Visibility

All methods in a trait definition inherit the trait's visibility.
You cannot make individual trait methods more or less visible than
the trait itself.

```rust
pub trait Handler {
    fn handle(&self, req: Request) -> Response; // pub (inherited)
    fn validate(&self, req: &Request) -> bool { true } // pub with default
}
```

### 8.3 The Sealed Trait Pattern — Controlled Extensibility

This is an advanced pattern using `pub` and private traits together
to create traits that are public (usable) but not implementable
by downstream users.

```rust
// src/lib.rs

mod private {
    // This trait is NOT public — downstream cannot name it
    pub trait Sealed {}
}

// Public trait, but requires Sealed which no one outside can implement
pub trait Primitive: private::Sealed {
    fn type_name() -> &'static str;
}

// We implement Sealed for specific types only
impl private::Sealed for u8 {}
impl private::Sealed for u16 {}
impl private::Sealed for u32 {}
impl private::Sealed for u64 {}

impl Primitive for u8  { fn type_name() -> &'static str { "u8" } }
impl Primitive for u16 { fn type_name() -> &'static str { "u16" } }
impl Primitive for u32 { fn type_name() -> &'static str { "u32" } }
impl Primitive for u64 { fn type_name() -> &'static str { "u64" } }

// Downstream users can USE `Primitive`, write generic functions over it,
// but CANNOT implement it for their own types.
```

**Why this matters:** You maintain the invariant that only your types
can satisfy `Primitive`. This is how `std::ops::Add` restricts numeric
operations in some contexts.

### 8.4 Trait Objects and Visibility

```rust
pub trait Plugin: Send + Sync {
    fn name(&self) -> &str;
    fn execute(&self, ctx: &mut Context);
}

// Internal registry — crate-only
pub(crate) struct PluginRegistry {
    plugins: Vec<Box<dyn Plugin>>,
}

impl PluginRegistry {
    pub(crate) fn register(&mut self, plugin: Box<dyn Plugin>) {
        self.plugins.push(plugin);
    }

    pub(crate) fn run_all(&self, ctx: &mut Context) {
        for p in &self.plugins {
            p.execute(ctx);
        }
    }
}

pub struct Context {
    pub state: std::collections::HashMap<String, String>,
}
```

---

## 9. `pub` in `impl` Blocks

`impl` blocks themselves don't take a visibility modifier — visibility
is specified on individual methods within them.

### 9.1 Mixing Visibility in `impl`

```rust
pub struct Cache<K, V> {
    store: std::collections::HashMap<K, V>,
    hits: u64,
    misses: u64,
}

impl<K: std::hash::Hash + Eq, V: Clone> Cache<K, V> {
    // Public API
    pub fn new() -> Self {
        Self {
            store: std::collections::HashMap::new(),
            hits: 0,
            misses: 0,
        }
    }

    pub fn get(&mut self, key: &K) -> Option<V> {
        match self.store.get(key) {
            Some(v) => { self.hits += 1; Some(v.clone()) }
            None    => { self.misses += 1; None }
        }
    }

    pub fn insert(&mut self, key: K, value: V) {
        self.invalidate_related(&key); // calls private method
        self.store.insert(key, value);
    }

    pub fn stats(&self) -> CacheStats {
        CacheStats { hits: self.hits, misses: self.misses }
    }

    // Private: implementation detail, not API surface
    fn invalidate_related(&mut self, _key: &K) {
        // Complex invalidation logic
    }

    // pub(crate): used by cache manager in same crate
    pub(crate) fn raw_store(&self) -> &std::collections::HashMap<K, V> {
        &self.store
    }
}

pub struct CacheStats {
    pub hits: u64,
    pub misses: u64,
}
```

### 9.2 `impl` for Trait — Visibility Rules

When implementing a trait, the method visibility is dictated by
the trait definition, not by what you write in the `impl` block.

```rust
pub trait Area {
    fn area(&self) -> f64; // pub in trait
}

struct Circle { radius: f64 }

impl Area for Circle {
    fn area(&self) -> f64 { // inherits pub from trait — don't add `pub` here
        std::f64::consts::PI * self.radius * self.radius
    }
}
```

---

## 10. Constants, Statics, and Type Aliases

All of these fully support the visibility spectrum:

```rust
mod config {
    // pub constant: part of the library's API
    pub const MAX_CONNECTIONS: usize = 1024;

    // pub(crate) constant: used across modules internally
    pub(crate) const BUFFER_SIZE: usize = 4096;

    // Private constant: local magic number
    const TIMEOUT_MS: u64 = 5000;

    // pub static: global mutable state (requires unsafe to mutate)
    pub static VERSION: &str = "1.0.0";

    // pub(crate) type alias
    pub(crate) type Result<T> = std::result::Result<T, crate::Error>;

    // pub type alias: part of public API
    pub type Callback = fn(u64) -> bool;
}
```

---

## 11. Visibility in `use` Declarations

`use` declarations can themselves be public or private:

```rust
mod inner {
    // Private use: only inner can use this name
    use std::collections::HashMap;

    // Public use (re-export): anyone who can see `inner` can use Map
    pub use std::collections::BTreeMap as Map;

    pub fn make_map() -> Map<String, i32> {
        Map::new()
    }
}

fn main() {
    // inner::HashMap — ❌ private use, not re-exported
    // inner::Map — ✅ pub use re-exports it
    let m: inner::Map<String, i32> = inner::Map::new();
}
```

---

## 12. Real-World Architectural Patterns

### 12.1 The Library API Layer Pattern

This is how large Rust libraries (like `tokio`, `serde`, `axum`) are structured:

```rust
// src/lib.rs — the public face
pub mod prelude;     // convenience re-exports for users
pub use error::{Error, Result};
pub use server::Server;
pub use config::Config;

// Private implementation modules
mod error;
mod server;
mod config;
mod transport;   // not pub: internal only
mod codec;       // not pub: internal only
```

```rust
// src/error.rs
#[derive(Debug)]
pub enum Error {
    Io(std::io::Error),
    Parse(String),
    Timeout,
}

pub type Result<T> = std::result::Result<T, Error>;
```

```rust
// src/transport.rs — internal
pub(crate) struct TcpTransport {
    socket: std::net::TcpStream,
}

impl TcpTransport {
    pub(crate) fn new(addr: &str) -> crate::Result<Self> {
        let socket = std::net::TcpStream::connect(addr)
            .map_err(crate::Error::Io)?;
        Ok(Self { socket })
    }

    pub(crate) fn send(&mut self, data: &[u8]) -> crate::Result<()> {
        use std::io::Write;
        self.socket.write_all(data).map_err(crate::Error::Io)
    }
}
```

### 12.2 The State Machine with Typestate Pattern

Using `pub` strategically with type-state to make illegal states
*unrepresentable*:

```rust
mod connection {
    // States — pub so users can name them in type signatures
    pub struct Disconnected;
    pub struct Connected { pub(super) stream: std::net::TcpStream }
    pub struct Authenticated { pub(super) stream: std::net::TcpStream, pub user: String }

    pub struct Client<State> {
        state: State,
    }

    // Only valid on Disconnected
    impl Client<Disconnected> {
        pub fn new() -> Self {
            Self { state: Disconnected }
        }

        pub fn connect(self, addr: &str) -> Result<Client<Connected>, std::io::Error> {
            let stream = std::net::TcpStream::connect(addr)?;
            Ok(Client { state: Connected { stream } })
        }
    }

    // Only valid on Connected
    impl Client<Connected> {
        pub fn authenticate(self, user: &str, _pass: &str) -> Client<Authenticated> {
            Client {
                state: Authenticated {
                    stream: self.state.stream,
                    user: user.to_string(),
                }
            }
        }
    }

    // Only valid on Authenticated
    impl Client<Authenticated> {
        pub fn send_command(&mut self, cmd: &str) {
            use std::io::Write;
            let _ = self.state.stream.write_all(cmd.as_bytes());
        }

        pub fn whoami(&self) -> &str {
            &self.state.user
        }
    }
}

// At compile time, this is IMPOSSIBLE:
// let client = Client::new();
// client.send_command("ls"); // ❌ send_command doesn't exist on Disconnected
//
// You MUST go through connect() → authenticate() before any commands.
```

### 12.3 Internal Plugin System

```rust
// src/plugin.rs
pub trait Plugin: Send + Sync + 'static {
    fn name(&self) -> &'static str;
    fn on_start(&self);
    fn on_stop(&self);
}

// src/registry.rs
use std::sync::{Arc, RwLock};
use crate::plugin::Plugin;

pub(crate) struct Registry {
    plugins: RwLock<Vec<Arc<dyn Plugin>>>,
}

impl Registry {
    pub(crate) fn new() -> Self {
        Self { plugins: RwLock::new(Vec::new()) }
    }

    pub(crate) fn register(&self, plugin: Arc<dyn Plugin>) {
        self.plugins.write().unwrap().push(plugin);
    }

    pub(crate) fn start_all(&self) {
        for p in self.plugins.read().unwrap().iter() {
            p.on_start();
        }
    }
}

// src/lib.rs
static REGISTRY: std::sync::OnceLock<registry::Registry> = std::sync::OnceLock::new();

pub fn register_plugin(plugin: Arc<dyn plugin::Plugin>) {
    REGISTRY
        .get_or_init(|| registry::Registry::new())
        .register(plugin);
}

pub fn start() {
    if let Some(r) = REGISTRY.get() {
        r.start_all();
    }
}

mod registry;
pub mod plugin;

use std::sync::Arc;
```

### 12.4 The Repository Pattern with Visibility

```rust
// src/db/mod.rs
pub(crate) use repository::UserRepository;
mod repository;
mod connection;

// src/db/connection.rs
pub(super) struct DbConnection {
    // internal: only db module uses this
}

impl DbConnection {
    pub(super) fn query(&self, sql: &str) -> Vec<Vec<String>> {
        vec![] // stub
    }
}

// src/db/repository.rs
use super::connection::DbConnection;

pub(crate) struct UserRepository {
    conn: DbConnection,
}

pub struct User {
    pub id: u64,
    pub name: String,
    pub email: String,
}

impl UserRepository {
    pub(crate) fn find_by_id(&self, id: u64) -> Option<User> {
        let rows = self.conn.query(&format!("SELECT * FROM users WHERE id={}", id));
        rows.into_iter().next().map(|row| User {
            id,
            name: row.get(1).cloned().unwrap_or_default(),
            email: row.get(2).cloned().unwrap_or_default(),
        })
    }
}
```

---

## 13. The Orphan Rule and Visibility Interaction

The orphan rule states: you can implement a trait for a type only if
the trait or the type is defined in your crate. Visibility interacts
with this because you can only *use* traits and types you can *see*.

```rust
// In your crate: you can implement std::fmt::Display for your type
pub struct Point { pub x: f64, pub y: f64 }

impl std::fmt::Display for Point {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(f, "({}, {})", self.x, self.y)
    }
}

// You CANNOT implement Display for Vec<i32> — neither is yours.
// This is the orphan rule, enforced independently of visibility.
```

**The connection to `pub`:** If a type is `pub(crate)`, downstream
crates cannot implement traits for it (they can't even *name* it).
This gives you safety that nobody outside can attach behavior to
your internal types.

---

## 14. Common Pitfalls and Subtle Behaviors

### 14.1 The "pub but Unreachable" Trap

```rust
mod a {
    mod b {          // PRIVATE module
        pub fn hi() {}  // pub function — but b is private
    }

    pub fn expose() {
        b::hi(); // ✅ works from inside `a`
    }
}

fn main() {
    a::expose();    // ✅
    a::b::hi();     // ❌ `b` is private — cannot reach `hi` this way
}
```

**Rule:** Visibility is not just about the item — it's about the entire path.

### 14.2 `pub use` Does Not Change Ownership

```rust
mod inner {
    pub struct Foo;
}

pub use inner::Foo; // re-exports Foo at the current module level

// Foo is still defined in `inner`. Re-export just adds an alias.
// inner::Foo and the_current_module::Foo refer to the same type.
```

### 14.3 Struct Update Syntax Requires Field Access

```rust
pub struct Config {
    pub debug: bool,
    timeout: u32,   // private
}

// From outside the module:
let new_cfg = Config {
    debug: true,
    // ..old_cfg  // ❌ cannot use struct update syntax if ANY private
                  //    field differs — but actually, you can use it:
    ..old_cfg      // ✅ this works IF you don't override private fields
                   // because the private fields are copied from old_cfg
};
```

### 14.4 `pub` on `use` in `mod.rs` — A Common Pattern Mistake

```rust
// src/lib.rs
mod utils; // private module

pub fn process(data: &[u8]) -> Vec<u8> {
    utils::transform(data) // ✅ can use private module internally
}

// But if you forget to re-export what users need:
// pub use utils::TransformConfig; // ← missing this means users can't configure it
```

### 14.5 `impl Trait` in Return Position and Visibility

```rust
mod inner {
    struct Hidden; // private

    impl Hidden {
        fn value(&self) -> u32 { 42 }
    }

    // You CAN return a private type through `impl Trait`
    pub fn make_it() -> impl Fn() -> u32 {
        let h = Hidden;
        move || h.value()
    }
}

fn main() {
    let f = inner::make_it();
    println!("{}", f()); // ✅ user can call it, but cannot name `Hidden`
}
```

---

## 15. Mental Models for Reasoning About Visibility

### 15.1 The Trust Boundary Model

Think of each module as a **team** working on a component:
- `private` = internal team notes
- `pub(super)` = info shared with the parent team lead
- `pub(crate)` = company-internal documentation
- `pub` = what you publish externally

Never expose implementation details beyond the boundary that needs them.

### 15.2 The Invariant Ownership Model

For every invariant your type must maintain, ask:
*"What is the smallest set of code that needs to be trusted to uphold this?"*

Make that the visibility boundary. Everything else should be locked
behind private fields and controlled constructors.

### 15.3 The API Surface Minimization Principle

Every `pub` item is a *promise* you must keep across versions.
Adding `pub` to something is easy. Removing it is a **breaking change**.

**Expert habit:** Start everything `private`. Only add `pub`,
`pub(crate)`, etc., when something genuinely needs to be accessible.
This is called **visibility discipline**.

### 15.4 The Coherence Triangle

```
Visibility
    ↑
    │      For any item, all three must be consistent:
    │      1. The item's own visibility
    │      2. The visibility of its module path
    │      3. The visibility of types it references
    └──────────────────────────────────────
Item Visibility ←——→ Type Visibility
```

A `pub` function that returns a `pub(crate)` type is problematic:
Rust will warn you (`pub` function returning `pub(crate)` type means
external callers cannot use the return value properly).

```rust
pub(crate) struct Internal;

// Rust warns: unreachable pub — the return type isn't pub
pub fn create_internal() -> Internal { Internal }
```

---

## Quick Reference Summary

| Specifier | Visible To |
|-----------|-----------|
| *(none)* | Current module and its descendants |
| `pub(self)` | Same as private — current module |
| `pub(super)` | Parent module and its descendants |
| `pub(in path)` | Specified ancestor module and its descendants |
| `pub(crate)` | Entire current crate |
| `pub` | Everywhere — all crates |

| Pattern | Visibility Tool Used |
|---------|---------------------|
| Enforce type invariants | Private fields + `pub` constructors |
| Library API surface | `pub` on selected items + `pub use` for re-exports |
| Shared crate internals | `pub(crate)` |
| Submodule helpers | `pub(super)` |
| Ergonomic user API | `pub use` (flattening) |
| Sealed traits | `pub trait + private::Sealed` |
| Typestate machines | `pub` states, private fields |
| Prelude pattern | `pub mod prelude` with glob `pub use` |
| Forward compatibility | `#[non_exhaustive]` + `pub` |

---

*"The best API is one where correct usage is the path of least resistance,  
and incorrect usage does not compile."*

— The philosophy of Rust's visibility system, applied expertly.

Here's the complete guide — let me walk you through the key intellectual pillars:

---

**The core insight that separates experts from beginners:** `pub` is not just syntax — it's a *compiler-enforced invariant system*. When you make a field private, you're not hiding it for aesthetics. You're making it *structurally impossible* for the invariant over that field to be violated, forever, by any code anywhere.

**The five levels you must internalize:**
- Default private → children can see parent privates (unique Rust rule)
- `pub(super)` → parent-team visibility, for submodule helpers
- `pub(crate)` → the workhorse for shared internal infrastructure
- `pub(in path)` → surgical precision, rarely needed but powerful
- `pub` → a *promise* you're making to every downstream user

**The two most powerful patterns:**
1. **`pub use` for API facades** — your internal module tree is an implementation detail. Users shouldn't care that `BTreeMap` lives three levels deep. Re-export it at the top.
2. **Sealed traits** — `pub` trait + `private::Sealed` supertrait = a trait everyone can *use* but no one can *implement*. This is how the standard library controls extensibility.

**The discipline to develop:** Start everything private. Only lift visibility when something genuinely needs to cross a boundary. Every `pub` item is a *promise you cannot break* without a semver major bump.