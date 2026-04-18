# The Complete Cargo Guide — Elite Level Reference

> Cargo is Rust's build system, package manager, test runner, documentation generator, and project orchestrator — all in one.

---

## Table of Contents

1. [What Is Cargo?](#1-what-is-cargo)
2. [Installation & Setup](#2-installation--setup)
3. [Project Structure](#3-project-structure)
4. [Cargo.toml Deep Dive](#4-cargotoml-deep-dive)
5. [Cargo.lock](#5-cargolock)
6. [Creating Projects](#6-creating-projects)
7. [Building Projects](#7-building-projects)
8. [Running Projects](#8-running-projects)
9. [Testing](#9-testing)
10. [Benchmarking](#10-benchmarking)
11. [Documentation](#11-documentation)
12. [Dependencies & Crates.io](#12-dependencies--cratesio)
13. [Workspaces](#13-workspaces)
14. [Features & Conditional Compilation](#14-features--conditional-compilation)
15. [Build Scripts (build.rs)](#15-build-scripts-buildrs)
16. [Cargo Profiles](#16-cargo-profiles)
17. [Environment Variables](#17-environment-variables)
18. [Cross Compilation](#18-cross-compilation)
19. [Cargo Extensions & Third-Party Subcommands](#19-cargo-extensions--third-party-subcommands)
20. [Live Debugging with Cargo](#20-live-debugging-with-cargo)
21. [Cargo with GDB and LLDB](#21-cargo-with-gdb-and-lldb)
22. [Publishing to Crates.io](#22-publishing-to-cratesio)
23. [Security & Auditing](#23-security--auditing)
24. [Cargo Cache & Offline Mode](#24-cargo-cache--offline-mode)
25. [Advanced Cargo Configuration](#25-advanced-cargo-configuration)
26. [CI/CD Integration](#26-cicd-integration)
27. [Performance Tips & Expert Tricks](#27-performance-tips--expert-tricks)

---

## 1. What Is Cargo?

Cargo is the **official Rust package manager and build tool**. It handles:

```
+----------------------------------------------------------+
|                        CARGO                             |
|                                                          |
|  +-----------+  +----------+  +----------+  +--------+  |
|  |  Dependency|  |  Build   |  |   Test   |  |  Doc   |  |
|  |  Manager  |  |  System  |  |  Runner  |  |  Gen   |  |
|  +-----------+  +----------+  +----------+  +--------+  |
|                                                          |
|  +-----------+  +----------+  +----------+  +--------+  |
|  | Workspace |  | Profile  |  | Feature  |  |Publish |  |
|  | Manager   |  | Manager  |  | Flags    |  |  Tool  |  |
|  +-----------+  +----------+  +----------+  +--------+  |
+----------------------------------------------------------+
```

Cargo reads `Cargo.toml` (your project manifest), resolves dependency graphs, fetches crates, compiles your code, links binaries, and produces artifacts — all reproducibly.

---

## 2. Installation & Setup

Cargo is bundled with `rustup`. You do not install it separately.

```bash
# Install rustup (includes cargo + rustc + std)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Check versions
cargo --version       # cargo 1.x.x
rustc --version       # rustc 1.x.x

# Update everything
rustup update

# Show active toolchain
rustup show

# Install a specific toolchain
rustup install stable
rustup install nightly
rustup install 1.75.0

# Set default toolchain
rustup default stable

# Override per directory
rustup override set nightly
```

### Toolchain File

Create a `rust-toolchain.toml` in your project root to pin a toolchain:

```toml
[toolchain]
channel = "stable"         # or "nightly", "1.78.0"
components = ["rustfmt", "clippy", "rust-src"]
targets = ["x86_64-unknown-linux-gnu"]
```

Now anyone cloning your project automatically uses the right Rust version.

---

## 3. Project Structure

### Binary (Application) Layout

```
my_project/
├── Cargo.toml              <-- Project manifest
├── Cargo.lock              <-- Dependency lockfile
├── rust-toolchain.toml     <-- Optional: pin toolchain
├── .cargo/
│   └── config.toml         <-- Cargo local config
├── src/
│   ├── main.rs             <-- Binary entry point
│   ├── lib.rs              <-- Optional library root
│   └── bin/
│       ├── tool1.rs        <-- Extra binary: `cargo run --bin tool1`
│       └── tool2.rs        <-- Extra binary: `cargo run --bin tool2`
├── tests/
│   └── integration_test.rs <-- Integration tests
├── benches/
│   └── my_bench.rs         <-- Benchmarks (criterion)
├── examples/
│   └── demo.rs             <-- `cargo run --example demo`
└── build.rs                <-- Optional build script
```

### Library Layout

```
my_lib/
├── Cargo.toml
├── src/
│   ├── lib.rs              <-- Library root (exposed API)
│   └── internal/
│       └── helper.rs       <-- Internal module
└── tests/
    └── integration.rs
```

### Key Rule

```
src/main.rs  -->  cargo knows it's a binary automatically
src/lib.rs   -->  cargo knows it's a library automatically
src/bin/*.rs -->  each file becomes a separate binary
```

---

## 4. Cargo.toml Deep Dive

`Cargo.toml` uses **TOML** (Tom's Obvious Minimal Language) syntax.

### Full Annotated Example

```toml
# ===========================================================
# [package] — metadata about your crate
# ===========================================================
[package]
name        = "my_project"       # crate name (must be unique on crates.io)
version     = "0.1.0"            # semver: MAJOR.MINOR.PATCH
edition     = "2021"             # Rust edition: 2015, 2018, 2021
authors     = ["Your Name <you@example.com>"]
description = "A short description"
license     = "MIT OR Apache-2.0"
repository  = "https://github.com/you/my_project"
homepage    = "https://my_project.rs"
documentation = "https://docs.rs/my_project"
readme      = "README.md"
keywords    = ["cli", "tool"]    # max 5
categories  = ["command-line-utilities"]
exclude     = ["tests/", "benches/"]
include     = ["src/**/*", "Cargo.toml"]
build       = "build.rs"         # path to build script
publish     = true               # set false to prevent `cargo publish`

# Minimum Rust version required
rust-version = "1.70"

# ===========================================================
# [dependencies] — runtime dependencies
# ===========================================================
[dependencies]
serde       = "1.0"              # any 1.x.x compatible version
serde_json  = "1.0.100"         # exactly 1.0.100+
tokio       = { version = "1", features = ["full"] }
rand        = { version = "0.8", optional = true }  # optional dep
log         = { version = "0.4", default-features = false }
my_lib      = { path = "../my_lib" }    # local path
my_git_dep  = { git = "https://github.com/user/repo", branch = "main" }
my_git_rev  = { git = "https://github.com/user/repo", rev = "abc1234" }
my_git_tag  = { git = "https://github.com/user/repo", tag = "v1.2.3" }

# Platform-specific dependency
[target.'cfg(windows)'.dependencies]
winapi = "0.3"

[target.'cfg(unix)'.dependencies]
nix = "0.26"

# ===========================================================
# [dev-dependencies] — only for tests and examples
# ===========================================================
[dev-dependencies]
criterion   = { version = "0.5", features = ["html_reports"] }
proptest    = "1.0"
mockall     = "0.11"
pretty_assertions = "1.4"

# ===========================================================
# [build-dependencies] — only for build.rs
# ===========================================================
[build-dependencies]
cc          = "1.0"    # for compiling C code
pkg-config  = "0.3"

# ===========================================================
# [[bin]] — define multiple binaries
# ===========================================================
[[bin]]
name = "tool1"
path = "src/bin/tool1.rs"
required-features = ["feature_x"]   # only built when feature is on

[[bin]]
name = "tool2"
path = "src/bin/tool2.rs"

# ===========================================================
# [lib] — configure the library target
# ===========================================================
[lib]
name        = "my_lib"
path        = "src/lib.rs"
crate-type  = ["cdylib", "rlib"]   # types: lib, rlib, dylib, cdylib, staticlib, proc-macro

# ===========================================================
# [[example]] — runnable examples
# ===========================================================
[[example]]
name = "demo"
path = "examples/demo.rs"
required-features = ["rand"]

# ===========================================================
# [[test]] — custom test targets
# ===========================================================
[[test]]
name = "integration"
path = "tests/integration.rs"

# ===========================================================
# [[bench]] — benchmark targets
# ===========================================================
[[bench]]
name    = "my_bench"
harness = false    # false = use criterion, not built-in libtest

# ===========================================================
# [features] — feature flags
# ===========================================================
[features]
default  = ["logging"]       # features enabled by default
logging  = ["log"]
async    = ["tokio"]
full     = ["logging", "async", "rand"]

# ===========================================================
# [profile.*] — build profiles
# ===========================================================
[profile.dev]
opt-level       = 0      # no optimisation
debug           = true   # include debug symbols
overflow-checks = true

[profile.release]
opt-level       = 3      # max optimisation
lto             = true   # link time optimisation
codegen-units   = 1      # single codegen unit (slower build, faster binary)
strip           = true   # strip symbols from binary
panic           = "abort" # abort on panic (smaller binary)

[profile.bench]
opt-level = 3
debug     = true         # keep debug for profiling

# Custom profile inheriting from release
[profile.staging]
inherits  = "release"
opt-level = 2

# ===========================================================
# [workspace] — if this is a workspace root
# ===========================================================
[workspace]
members  = ["crate_a", "crate_b", "crate_c"]
exclude  = ["experiments"]
resolver = "2"   # dependency resolver version (always use 2)

[workspace.package]      # shared package metadata
edition = "2021"
authors = ["You"]

[workspace.dependencies] # shared dependency versions
serde = { version = "1.0", features = ["derive"] }
tokio = { version = "1", features = ["full"] }

# ===========================================================
# [patch] — override a dependency globally
# ===========================================================
[patch.crates-io]
serde = { path = "../my-serde-fork" }
# or
serde = { git = "https://github.com/you/serde", branch = "fix-bug" }

# ===========================================================
# [replace] — (deprecated, use [patch] instead)
# ===========================================================

# ===========================================================
# [badges] — display on crates.io
# ===========================================================
[badges]
maintenance = { status = "actively-developed" }
```

---

## 5. Cargo.lock

`Cargo.lock` is an **exact snapshot** of every dependency version resolved at build time.

```
+--------------------+      resolves      +--------------------+
|   Cargo.toml       | -----------------> |   Cargo.lock       |
| (version ranges)   |                   | (exact versions)   |
+--------------------+                   +--------------------+
```

### Rules

| Project Type | Commit Cargo.lock? |
|---|---|
| Binary / Application | YES — ensures reproducible builds |
| Library (crate) | NO — let downstream pick compatible versions |

### Lock File Structure

```toml
# This file is automatically @generated by Cargo.
# It is not intended for manual editing.
version = 3

[[package]]
name     = "my_project"
version  = "0.1.0"
dependencies = [
  "serde 1.0.193 (registry+https://github.com/rust-lang/crates.io-index)",
]

[[package]]
name     = "serde"
version  = "1.0.193"
source   = "registry+https://github.com/rust-lang/crates.io-index"
checksum = "25dd0975d2646abe23884..."
```

### Updating Locks

```bash
cargo update              # update all deps to latest compatible versions
cargo update -p serde     # update only serde
cargo update -p serde --precise 1.0.195  # pin to exact version
```

---

## 6. Creating Projects

```bash
# Create a new binary project
cargo new my_app

# Create a new library
cargo new my_lib --lib

# Create in current directory (must be empty or uninitialized)
cargo init
cargo init --lib

# Create with specific edition
cargo new my_app --edition 2021

# Create with a VCS
cargo new my_app --vcs git     # default
cargo new my_app --vcs none    # no VCS
```

What `cargo new` creates:

```
my_app/
├── .git/              (git init)
├── .gitignore         (contains /target)
├── Cargo.toml
└── src/
    └── main.rs        (fn main() { println!("Hello, world!"); })
```

---

## 7. Building Projects

### Build Command Reference

```bash
# Development build (fast compile, slow binary)
cargo build

# Release build (slow compile, fast binary)
cargo build --release

# Build specific binary
cargo build --bin tool1

# Build specific library
cargo build --lib

# Build all targets (bin, lib, tests, examples, benches)
cargo build --all-targets

# Build for a specific target triple
cargo build --target x86_64-unknown-linux-musl

# Build with features
cargo build --features "async logging"
cargo build --all-features
cargo build --no-default-features
cargo build --no-default-features --features "logging"

# Check compilation without producing output (much faster!)
cargo check
cargo check --all-targets

# Build and show assembly output
RUSTFLAGS="--emit=asm" cargo build --release

# Clean build artifacts
cargo clean
cargo clean --release         # clean only release artifacts
cargo clean -p my_crate       # clean only one crate's artifacts
```

### Where Artifacts Go

```
target/
├── debug/             <-- cargo build (default)
│   ├── my_app         <-- the binary
│   ├── libmy_lib.rlib <-- library
│   ├── deps/          <-- compiled dependencies
│   ├── build/         <-- build script outputs
│   └── incremental/   <-- incremental build cache
└── release/           <-- cargo build --release
    ├── my_app
    └── deps/
```

### Build Pipeline

```
Cargo.toml
    |
    v
Dependency Resolution
    |
    v
Download & Compile Dependencies (in parallel)
    |
    v
Run build.rs (if exists)
    |
    v
Compile your code (rustc)
    |
    v
Link binary / produce .rlib
    |
    v
Artifact in target/
```

### Verbose Build (see what rustc is doing)

```bash
cargo build -v          # verbose
cargo build -vv         # very verbose (shows full rustc commands)
```

### Controlling Parallelism

```bash
cargo build -j 4        # use 4 parallel jobs
cargo build -j 1        # single threaded (good for debugging order issues)
```

---

## 8. Running Projects

```bash
# Compile + run (debug mode)
cargo run

# Compile + run (release mode)
cargo run --release

# Run a specific binary
cargo run --bin tool1

# Run an example
cargo run --example demo

# Pass arguments to your program
cargo run -- arg1 arg2 --flag value
#              ^^ everything after -- goes to your program

# Run with features
cargo run --features "async"

# Run with environment variables
MY_VAR=hello cargo run
```

---

## 9. Testing

### Test Types in Rust

```
+------------------------------------------------+
|              Rust Test Types                   |
|                                                |
|  1. Unit Tests       (inside src/             |
|     #[test] inside same file as code)          |
|                                                |
|  2. Integration Tests (in tests/ directory)   |
|     Test your public API like an external user |
|                                                |
|  3. Doc Tests         (in doc comments ///)   |
|     Code examples in documentation             |
|                                                |
|  4. Benchmarks        (in benches/)           |
|     Performance tests                          |
+------------------------------------------------+
```

### Unit Test Example

```rust
// src/lib.rs
pub fn add(a: i32, b: i32) -> i32 {
    a + b
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_add() {
        assert_eq!(add(2, 3), 5);
    }

    #[test]
    #[should_panic(expected = "divide by zero")]
    fn test_panic() {
        let _ = 1 / 0;
    }

    #[test]
    #[ignore]
    fn expensive_test() {
        // skipped by default
    }
}
```

### Integration Test Example

```rust
// tests/integration.rs
use my_lib::add;   // uses public API only

#[test]
fn test_add_integration() {
    assert_eq!(add(10, 20), 30);
}
```

### Doc Test Example

```rust
/// Adds two numbers.
///
/// # Examples
///
/// ```
/// let result = my_lib::add(2, 3);
/// assert_eq!(result, 5);
/// ```
pub fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

### Running Tests

```bash
# Run all tests
cargo test

# Run in release mode
cargo test --release

# Run specific test by name (substring match)
cargo test test_add

# Run tests in a specific file
cargo test --test integration

# Run doc tests only
cargo test --doc

# Run unit tests only (exclude integration and doc tests)
cargo test --lib

# Run benchmarks as tests
cargo test --benches

# Run ignored tests
cargo test -- --ignored
cargo test -- --include-ignored

# Show output even for passing tests
cargo test -- --nocapture

# Run tests with a single thread (avoid parallel races)
cargo test -- --test-threads=1

# List all test names without running
cargo test -- --list

# Run tests and show timing
cargo test -- --report-time

# Run tests for a specific binary
cargo test --bin tool1

# Run tests with features
cargo test --features "async"
cargo test --all-features
```

### Custom Test Output (with `nextest`)

`cargo-nextest` is a faster, better test runner:

```bash
cargo install cargo-nextest

cargo nextest run            # faster parallel test runner
cargo nextest run --no-fail-fast
cargo nextest list           # list all tests
```

---

## 10. Benchmarking

### Built-in Benchmarks (nightly only)

```rust
// benches/my_bench.rs
#![feature(test)]
extern crate test;

#[bench]
fn bench_add(b: &mut test::Bencher) {
    b.iter(|| {
        test::black_box(1 + 2)
    });
}
```

```bash
rustup run nightly cargo bench
```

### Criterion (stable, preferred)

```toml
# Cargo.toml
[dev-dependencies]
criterion = { version = "0.5", features = ["html_reports"] }

[[bench]]
name    = "my_bench"
harness = false
```

```rust
// benches/my_bench.rs
use criterion::{black_box, criterion_group, criterion_main, Criterion};

fn fibonacci(n: u64) -> u64 {
    match n {
        0 => 0,
        1 => 1,
        n => fibonacci(n - 1) + fibonacci(n - 2),
    }
}

fn bench_fib(c: &mut Criterion) {
    c.bench_function("fib 20", |b| {
        b.iter(|| fibonacci(black_box(20)))
    });
}

criterion_group!(benches, bench_fib);
criterion_main!(benches);
```

```bash
cargo bench                        # run all benchmarks
cargo bench bench_fib              # run specific benchmark
cargo bench -- --save-baseline old # save baseline
cargo bench -- --baseline old      # compare against baseline
```

Results go to `target/criterion/`. Open `target/criterion/report/index.html`.

---

## 11. Documentation

```bash
# Generate docs for your crate
cargo doc

# Generate + open in browser
cargo doc --open

# Include docs for private items
cargo doc --document-private-items

# Generate docs for all dependencies too
cargo doc --no-deps   # only your crate (faster)

# Generate docs for a specific package in workspace
cargo doc -p my_lib
```

### Writing Great Docs

```rust
//! Module-level documentation (inner doc comment)
//! This describes the module itself.

/// Function-level documentation (outer doc comment)
///
/// # Arguments
/// * `x` - the input value
///
/// # Returns
/// The doubled value
///
/// # Examples
/// ```
/// assert_eq!(my_crate::double(3), 6);
/// ```
///
/// # Panics
/// Panics if x > i32::MAX / 2
///
/// # Errors
/// Returns Err if input is negative
///
/// # Safety
/// This function is safe for all inputs
pub fn double(x: i32) -> i32 {
    x * 2
}
```

---

## 12. Dependencies & Crates.io

### Dependency Version Syntax

```toml
[dependencies]
# Exact version
foo = "=1.2.3"

# Caret requirement (default) — compatible with 1.2.3
# allows: >=1.2.3, <2.0.0
foo = "1.2.3"
foo = "^1.2.3"  # same as above

# Tilde requirement — only patch updates
# allows: >=1.2.3, <1.3.0
foo = "~1.2.3"

# Wildcard
foo = "1.*"     # any 1.x.x
foo = "*"       # any version (avoid this)

# Ranges
foo = ">=1.2, <1.5"
```

### Semver Rules Summary

```
MAJOR.MINOR.PATCH

^1.2.3  = >=1.2.3, <2.0.0   (most common)
^0.2.3  = >=0.2.3, <0.3.0   (0.x is special — minor is breaking)
^0.0.3  = >=0.0.3, <0.0.4   (0.0.x — patch is breaking)
```

### Searching for Crates

```bash
cargo search serde           # search crates.io from terminal
cargo search tokio --limit 5
```

### Adding Dependencies

```bash
# Using cargo-add (built into cargo since 1.62)
cargo add serde
cargo add serde --features derive
cargo add tokio --features full
cargo add rand --dev         # dev dependency
cargo add cc --build         # build dependency
cargo add my_lib --path ../my_lib
cargo add serde --git https://github.com/serde-rs/serde

# Remove a dependency
cargo rm serde
```

### Viewing Dependency Tree

```bash
cargo tree                           # full dependency tree
cargo tree -p my_lib                 # tree for specific package
cargo tree --duplicates              # show duplicate versions
cargo tree -i serde                  # who depends on serde?
cargo tree --depth 2                 # limit depth
cargo tree -e features               # show feature edges
cargo tree --target x86_64-pc-windows-msvc  # for a target
```

Example output:
```
my_project v0.1.0
├── serde v1.0.193
│   └── serde_derive v1.0.193 (proc-macro)
└── tokio v1.35.1
    ├── bytes v1.5.0
    ├── mio v0.8.10
    └── ...
```

---

## 13. Workspaces

A workspace is a collection of crates that share `Cargo.lock` and `target/` directory.

### Workspace Layout

```
my_workspace/
├── Cargo.toml          <-- workspace root
├── Cargo.lock          <-- shared lock file
├── target/             <-- shared build output
├── crate_a/
│   ├── Cargo.toml
│   └── src/lib.rs
├── crate_b/
│   ├── Cargo.toml
│   └── src/lib.rs
└── cli/
    ├── Cargo.toml
    └── src/main.rs
```

### Workspace Root Cargo.toml

```toml
[workspace]
resolver = "2"
members  = [
    "crate_a",
    "crate_b",
    "cli",
]

# Shared dependency versions (workspace inheritance)
[workspace.dependencies]
serde   = { version = "1.0", features = ["derive"] }
tokio   = { version = "1", features = ["full"] }
log     = "0.4"

[workspace.package]
edition = "2021"
authors = ["You <you@example.com>"]
license = "MIT"
```

### Member Crate Cargo.toml (inheriting workspace)

```toml
[package]
name     = "crate_a"
version  = "0.1.0"
edition.workspace = true    # inherit from workspace
authors.workspace = true

[dependencies]
serde = { workspace = true }        # use workspace version
tokio = { workspace = true, optional = true }  # workspace + optional
```

### Workspace Commands

```bash
# Build all members
cargo build --workspace

# Test all members
cargo test --workspace

# Run a specific package
cargo run -p cli

# Build a specific package
cargo build -p crate_a

# Check all
cargo check --workspace

# Clippy on all
cargo clippy --workspace

# Format all
cargo fmt --all
```

---

## 14. Features & Conditional Compilation

### Defining Features

```toml
[features]
default = ["logging"]        # enabled by default
logging = ["dep:log"]        # enables `log` crate
async   = ["dep:tokio"]
serde   = ["dep:serde", "dep:serde_json"]
full    = ["logging", "async", "serde"]

[dependencies]
log       = { version = "0.4", optional = true }
tokio     = { version = "1",   optional = true }
serde     = { version = "1.0", optional = true, features = ["derive"] }
serde_json = { version = "1.0", optional = true }
```

### Using Features in Code

```rust
// Conditionally compile based on feature
#[cfg(feature = "logging")]
fn log_message(msg: &str) {
    log::info!("{}", msg);
}

#[cfg(not(feature = "async"))]
fn run_sync() { /* ... */ }

// cfg in use statements
#[cfg(feature = "serde")]
use serde::{Serialize, Deserialize};

// cfg on struct fields
#[derive(Debug)]
pub struct Config {
    pub name: String,
    #[cfg(feature = "logging")]
    pub log_level: String,
}
```

### Build-time Feature Detection

```rust
// In build.rs
fn main() {
    // Tell cargo to re-run this script if features change
    println!("cargo:rerun-if-changed=build.rs");

    // Set a config flag for use in code
    if cfg!(feature = "logging") {
        println!("cargo:rustc-cfg=has_logging");
    }
}

// In src/lib.rs — use the custom cfg
#[cfg(has_logging)]
fn log_msg() { /* ... */ }
```

### Enabling Features from CLI

```bash
cargo build --features "logging async"
cargo build --all-features
cargo build --no-default-features
cargo build --no-default-features --features "logging"
```

---

## 15. Build Scripts (build.rs)

`build.rs` runs **before** your crate compiles. Use it to:
- Compile C/C++ code
- Generate Rust code
- Link native libraries
- Set environment variables for your code

```
Cargo detects build.rs
        |
        v
Compiles build.rs with rustc
        |
        v
Runs the build.rs binary
        |
        v
build.rs prints `cargo:` instructions
        |
        v
Cargo acts on those instructions
        |
        v
Your crate compiles
```

### Build Script Communication

`build.rs` communicates with Cargo by printing to stdout:

```rust
// build.rs
fn main() {
    // Tell cargo to rerun this script if file changes
    println!("cargo:rerun-if-changed=src/native.c");
    println!("cargo:rerun-if-env-changed=MY_ENV_VAR");

    // Link a native library
    println!("cargo:rustc-link-lib=ssl");              // dynamic: libssl.so
    println!("cargo:rustc-link-lib=static=mylib");     // static: libmylib.a
    println!("cargo:rustc-link-search=native=/usr/local/lib");

    // Set a cfg flag usable in your code
    println!("cargo:rustc-cfg=has_sse4");

    // Set an environment variable your code can read with env!()
    println!("cargo:rustc-env=MY_BUILD_TIME=2024-01-01");

    // Emit metadata (readable by dependent crates)
    println!("cargo:my_key=my_value");

    // Warnings shown to user
    println!("cargo:warning=This build requires libssl");
}
```

### Compiling C Code in build.rs

```toml
[build-dependencies]
cc = "1.0"
```

```rust
// build.rs
fn main() {
    cc::Build::new()
        .file("src/native.c")
        .flag("-O2")
        .compile("mynative");
}
```

### Reading build.rs output in code

```rust
// src/lib.rs
const BUILD_TIME: &str = env!("MY_BUILD_TIME");   // set by cargo:rustc-env

#[cfg(has_sse4)]   // set by cargo:rustc-cfg
fn fast_path() { /* ... */ }
```

### OUT_DIR — Generating Code

```rust
// build.rs
use std::{env, fs, path::Path};

fn main() {
    let out_dir = env::var("OUT_DIR").unwrap();
    let dest    = Path::new(&out_dir).join("generated.rs");

    fs::write(&dest, r#"
        pub fn generated_fn() -> &'static str {
            "I was generated at build time!"
        }
    "#).unwrap();
}
```

```rust
// src/lib.rs
include!(concat!(env!("OUT_DIR"), "/generated.rs"));

pub fn use_generated() {
    println!("{}", generated_fn());
}
```

---

## 16. Cargo Profiles

Profiles control **how** your code is compiled.

```
+------------------+----------+-----------+---------------+
| Profile          | Trigger  | Opt Level | Debug Symbols |
+------------------+----------+-----------+---------------+
| dev              | build    | 0         | Yes           |
| release          | --release| 3         | No            |
| test             | test     | 0         | Yes           |
| bench            | bench    | 3         | No            |
+------------------+----------+-----------+---------------+
```

### All Profile Options

```toml
[profile.release]
# Optimization level: 0, 1, 2, 3, "s" (size), "z" (min size)
opt-level = 3

# Debug info: false, 0, "line-tables-only", "limited", true, 2
debug = false

# Strip symbols: false, "debuginfo", "symbols"
strip = "symbols"

# Enable Link Time Optimization
# false, true (thin), "thin", "fat"
lto = "thin"

# Parallel code generation units (1 = max optimization but slow build)
codegen-units = 1

# Panic strategy: "unwind" (default) or "abort" (smaller, no stack unwinding)
panic = "abort"

# Enable overflow checks (default: true in dev, false in release)
overflow-checks = false

# Incremental compilation (default: true in dev, false in release)
incremental = false

# Rpath linking (Linux)
rpath = false

# Per-dependency optimization overrides
[profile.dev.package."*"]
opt-level = 2   # optimize all deps even in dev mode (speeds up heavy deps like regex)

[profile.dev.package.serde]
opt-level = 3   # always optimize serde
```

### Practical Release Profile

```toml
[profile.release]
opt-level       = 3
lto             = true
codegen-units   = 1
panic           = "abort"
strip           = true
overflow-checks = false
```

### Profile for Fast Dev Builds with Optimized Deps

```toml
[profile.dev.package."*"]
opt-level = 2

[profile.dev]
opt-level = 0
debug     = true
```

---

## 17. Environment Variables

### Variables Cargo Sets for You

```bash
CARGO_MANIFEST_DIR    # directory containing Cargo.toml
CARGO_PKG_NAME        # package name
CARGO_PKG_VERSION     # package version (e.g., "0.1.0")
CARGO_PKG_VERSION_MAJOR
CARGO_PKG_VERSION_MINOR
CARGO_PKG_VERSION_PATCH
CARGO_PKG_AUTHORS
CARGO_PKG_DESCRIPTION
CARGO_PKG_HOMEPAGE
CARGO_PKG_REPOSITORY
OUT_DIR               # output dir for build scripts
CARGO_FEATURE_<NAME>  # set when feature is enabled (CARGO_FEATURE_ASYNC)
CARGO_CFG_<KEY>       # cfg values (CARGO_CFG_TARGET_OS, CARGO_CFG_TARGET_ARCH)
```

### Accessing in Code

```rust
fn main() {
    let version = env!("CARGO_PKG_VERSION");
    let name    = env!("CARGO_PKG_NAME");
    println!("{} v{}", name, version);

    // Optional: doesn't fail if not set
    let home = option_env!("HOME").unwrap_or("unknown");
    println!("Home: {}", home);
}
```

### Variables That Control Cargo

```bash
CARGO_HOME            # where cargo stores registry, binaries (~/.cargo)
CARGO_TARGET_DIR      # override target/ directory location
RUSTFLAGS             # extra flags passed to rustc
RUSTDOCFLAGS          # extra flags passed to rustdoc
CARGO_LOG             # cargo's internal logging (cargo=debug, cargo=trace)
CARGO_INCREMENTAL     # 0 or 1
RUST_BACKTRACE        # 0, 1, or "full" — show backtraces in panics
RUST_LOG              # for env_logger crate
HTTP_PROXY / HTTPS_PROXY  # proxy settings
```

---

## 18. Cross Compilation

### Concept

```
+---------------------+       compile for      +---------------------+
|  Host Machine       | --------------------> |  Target Platform    |
|  (x86_64 Linux)     |                        |  (ARM, Windows, etc)|
+---------------------+                        +---------------------+
```

### Adding Targets

```bash
# List installed targets
rustup target list --installed

# List all available targets
rustup target list

# Install a target
rustup target add x86_64-unknown-linux-musl   # static Linux binary
rustup target add aarch64-unknown-linux-gnu   # ARM Linux (Raspberry Pi)
rustup target add x86_64-pc-windows-gnu       # Windows
rustup target add wasm32-unknown-unknown      # WebAssembly
rustup target add aarch64-apple-darwin        # Apple Silicon
```

### Common Target Triples

```
<arch>-<vendor>-<os>-<abi>

x86_64-unknown-linux-gnu        Linux 64-bit (glibc)
x86_64-unknown-linux-musl       Linux 64-bit (musl, fully static)
aarch64-unknown-linux-gnu       ARM 64-bit Linux
aarch64-apple-darwin            macOS Apple Silicon
x86_64-apple-darwin             macOS Intel
x86_64-pc-windows-msvc          Windows 64-bit (MSVC)
x86_64-pc-windows-gnu           Windows 64-bit (MinGW)
wasm32-unknown-unknown          WebAssembly
wasm32-wasi                     WebAssembly with WASI
thumbv7em-none-eabihf           ARM Cortex-M4/M7 (embedded)
riscv32imc-unknown-none-elf     RISC-V 32-bit embedded
```

### Cross Compiling

```bash
# Build for musl (fully static binary)
cargo build --target x86_64-unknown-linux-musl --release

# Build for Windows (from Linux)
cargo build --target x86_64-pc-windows-gnu --release

# Build for ARM
cargo build --target aarch64-unknown-linux-gnu --release
```

### Linker Configuration (in .cargo/config.toml)

```toml
[target.x86_64-unknown-linux-musl]
linker = "x86_64-linux-musl-gcc"

[target.aarch64-unknown-linux-gnu]
linker = "aarch64-linux-gnu-gcc"

[target.x86_64-pc-windows-gnu]
linker = "x86_64-w64-mingw32-gcc"
```

### Using `cross` (Docker-based cross compilation)

```bash
cargo install cross

cross build --target aarch64-unknown-linux-gnu --release
cross test  --target aarch64-unknown-linux-gnu
```

`cross` automatically handles linkers and system libraries via Docker.

---

## 19. Cargo Extensions & Third-Party Subcommands

Cargo's power multiplies with extensions. Any binary named `cargo-*` becomes a `cargo *` subcommand.

```bash
# Install an extension
cargo install cargo-watch
# Use it
cargo watch -x build
```

### Essential Extensions

| Tool | Install | Use |
|---|---|---|
| `cargo-watch` | `cargo install cargo-watch` | Recompile on file change |
| `cargo-edit` | `cargo install cargo-edit` | `cargo add/rm/upgrade` |
| `cargo-nextest` | `cargo install cargo-nextest` | Better test runner |
| `cargo-expand` | `cargo install cargo-expand` | Expand macros |
| `cargo-flamegraph` | `cargo install flamegraph` | Flame graph profiling |
| `cargo-audit` | `cargo install cargo-audit` | Security audit |
| `cargo-outdated` | `cargo install cargo-outdated` | Check outdated deps |
| `cargo-udeps` | `cargo install cargo-udeps` | Find unused deps |
| `cargo-deny` | `cargo install cargo-deny` | Dependency policy |
| `cargo-bloat` | `cargo install cargo-bloat` | Find what's bloating binary |
| `cargo-binstall` | `cargo install cargo-binstall` | Install binary from release |
| `cargo-make` | `cargo install cargo-make` | Task runner |
| `cargo-tarpaulin` | `cargo install cargo-tarpaulin` | Code coverage |
| `cargo-hack` | `cargo install cargo-hack` | Test feature combos |
| `cargo-criterion` | built into criterion | Benchmark helper |
| `cargo-asm` | `cargo install cargo-show-asm` | View assembly |

### Usage Examples

```bash
# cargo-watch: rebuild on any change
cargo watch -x build
cargo watch -x test
cargo watch -x "run -- --flag"
cargo watch -x check -x test -x run   # chain commands

# cargo-expand: see what macros expand to
cargo expand                     # expand entire crate
cargo expand main                # expand a specific module
cargo expand --test tests        # expand test module

# cargo-outdated: find outdated deps
cargo outdated
cargo outdated --root-deps-only

# cargo-udeps: find unused deps (requires nightly)
cargo +nightly udeps
cargo +nightly udeps --all-targets

# cargo-audit: security audit
cargo audit
cargo audit fix               # auto-fix where possible

# cargo-bloat: see binary size breakdown
cargo bloat --release
cargo bloat --release --crates   # by crate
cargo bloat --release -n 20      # top 20 functions

# cargo-show-asm: view generated assembly
cargo asm my_crate::my_function
cargo asm --release my_crate::add

# cargo-tarpaulin: code coverage
cargo tarpaulin
cargo tarpaulin --out Html

# cargo-hack: test all feature combinations
cargo hack check --feature-powerset
cargo hack test --each-feature
```

---

## 20. Live Debugging with Cargo

### Enabling Debug Symbols

Debug builds already have debug symbols. For release debugging:

```toml
[profile.release]
debug = true   # keep debug symbols in release
```

Or use a custom profile:

```toml
[profile.debug-release]
inherits = "release"
opt-level = 2
debug     = true
```

```bash
cargo build --profile debug-release
```

### RUST_BACKTRACE

```bash
# Show backtrace on panic
RUST_BACKTRACE=1 cargo run
RUST_BACKTRACE=full cargo run    # full, verbose backtrace
```

### Using eprintln! for Quick Debugging

```rust
fn process(data: &[u8]) -> Result<(), Box<dyn std::error::Error>> {
    eprintln!("[DEBUG] data len: {}", data.len());
    eprintln!("[DEBUG] data: {:?}", data);
    Ok(())
}
```

### Using the `log` + `env_logger` crate

```toml
[dependencies]
log        = "0.4"
env_logger = "0.10"
```

```rust
use log::{debug, info, warn, error};

fn main() {
    env_logger::init();
    debug!("Starting up");
    info!("Processing {} items", 42);
}
```

```bash
RUST_LOG=debug cargo run
RUST_LOG=my_crate=trace cargo run
RUST_LOG=info,my_crate::module=debug cargo run
```

### Using `tracing` (modern, structured logging)

```toml
[dependencies]
tracing         = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }
```

```rust
use tracing::{info, debug, instrument};

#[instrument]
fn process(input: &str) -> usize {
    debug!("processing input");
    info!(len = input.len(), "done");
    input.len()
}

fn main() {
    tracing_subscriber::fmt::init();
    process("hello");
}
```

```bash
RUST_LOG=debug cargo run
```

---

## 21. Cargo with GDB and LLDB

### Setup

```bash
# Install rust-gdb and rust-lldb (come with rustup)
rustup component add rust-src

# Build with debug symbols (default in dev mode)
cargo build

# Or explicitly:
cargo build --profile dev
```

### GDB

```bash
# Start debugging your binary
rust-gdb target/debug/my_app

# With arguments
rust-gdb --args target/debug/my_app arg1 arg2

# GDB commands inside the debugger:
# r / run        — run the program
# b main         — set breakpoint at main
# b src/main.rs:42   — set breakpoint at line 42
# n / next       — next line (step over)
# s / step       — step into function
# c / continue   — continue to next breakpoint
# p var          — print variable
# p *ptr         — dereference pointer
# bt             — backtrace (call stack)
# info locals    — show all locals
# info registers — show CPU registers
# watch var      — watch variable for changes
# q / quit       — quit gdb
```

### LLDB

```bash
# Start debugging
rust-lldb target/debug/my_app

# LLDB commands:
# run / r            — run
# breakpoint set --name main          — break at main
# breakpoint set --file main.rs --line 42
# thread step-over   — next line
# thread step-in     — step into
# continue / c       — continue
# frame variable     — show all variables in frame
# p var              — print variable
# bt                 — backtrace
# quit / q           — quit
```

### VS Code Debugging

Install the `CodeLLDB` extension. Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "lldb",
      "request": "launch",
      "name": "Debug my_app",
      "cargo": {
        "args": ["build", "--bin=my_app", "--package=my_app"],
        "filter": {
          "name": "my_app",
          "kind": "bin"
        }
      },
      "args": [],
      "cwd": "${workspaceFolder}",
      "env": {
        "RUST_LOG": "debug",
        "RUST_BACKTRACE": "1"
      }
    },
    {
      "type": "lldb",
      "request": "launch",
      "name": "Debug Tests",
      "cargo": {
        "args": ["test", "--no-run", "--bin=my_app"],
        "filter": {
          "name": "my_app",
          "kind": "bin"
        }
      },
      "args": []
    }
  ]
}
```

### RustRover (JetBrains) Debugging

RustRover has built-in Rust debugging with LLDB. Just:
1. Set breakpoints by clicking the gutter
2. Click the Debug button (or Shift+F9)
3. Use the Debug panel to step through, inspect variables, evaluate expressions

### Flamegraph Profiling

```bash
# Linux (perf-based)
cargo install flamegraph
cargo flamegraph --bin my_app

# macOS (dtrace-based, needs sudo)
sudo cargo flamegraph --bin my_app
```

Output: `flamegraph.svg` — open in browser.

### Heaptrack / Valgrind Memory Profiling

```bash
# Build with debug symbols
cargo build --release  # with debug=true in profile

# Valgrind memory check
valgrind --tool=memcheck target/release/my_app

# Heaptrack
heaptrack target/release/my_app
heaptrack_gui heaptrack.my_app.*.gz
```

---

## 22. Publishing to Crates.io

### One-time Setup

```bash
# Create account at crates.io
# Get API token from: https://crates.io/me

# Login
cargo login <your-api-token>
# Token stored in ~/.cargo/credentials.toml
```

### Pre-publish Checklist

```bash
# Check what files will be published
cargo package --list

# Check everything is OK (dry run)
cargo publish --dry-run

# Check your crate compiles cleanly
cargo check
cargo test
cargo clippy -- -D warnings
cargo fmt --check

# Verify docs
cargo doc --no-deps
```

### Publish

```bash
cargo publish

# Publish specific package in workspace
cargo publish -p my_lib
```

### Yanking Versions

```bash
# Yank a bad version (doesn't delete, just stops new projects using it)
cargo yank --version 0.1.0
cargo yank --version 0.1.0 --undo   # un-yank
```

### Ownership

```bash
# Add a co-owner
cargo owner --add github:username:team_name
cargo owner --add username

# List owners
cargo owner --list

# Remove owner
cargo owner --remove username
```

---

## 23. Security & Auditing

### cargo-audit

Checks your dependencies against the [RustSec Advisory Database](https://rustsec.org/).

```bash
cargo install cargo-audit

# Audit Cargo.lock
cargo audit

# Fix automatically
cargo audit fix

# Show full details
cargo audit --json | jq .

# Ignore specific advisory
cargo audit --ignore RUSTSEC-2020-0001
```

### cargo-deny

More comprehensive: checks licenses, duplicate crates, and security advisories.

```bash
cargo install cargo-deny
cargo deny init        # create deny.toml
cargo deny check       # check all
cargo deny check bans
cargo deny check licenses
cargo deny check advisories
```

Example `deny.toml`:

```toml
[advisories]
vulnerability = "deny"
unmaintained  = "warn"

[licenses]
allow = ["MIT", "Apache-2.0", "BSD-3-Clause"]
deny  = ["GPL-3.0"]

[bans]
multiple-versions = "warn"
deny = [
    { name = "openssl" }   # force rustls
]
```

---

## 24. Cargo Cache & Offline Mode

### Cache Location

```
~/.cargo/
├── bin/             <-- installed binaries (cargo install)
├── registry/
│   ├── index/       <-- crates.io index (git repo)
│   └── src/         <-- downloaded crate source
├── git/
│   └── db/          <-- git dependency cache
└── credentials.toml
```

### Offline Mode

```bash
# Use only cached crates — no network access
cargo build --offline
cargo test --offline
cargo run --offline
```

### Clearing Cache

```bash
cargo install cargo-cache
cargo cache               # show cache size
cargo cache --autoclean   # remove old versions
cargo cache --remove-dir all   # clear everything
```

### Vendoring Dependencies

```bash
# Download all deps into ./vendor/
cargo vendor

# Use vendored deps (put in .cargo/config.toml)
[source.crates-io]
replace-with = "vendored-sources"

[source.vendored-sources]
directory = "vendor"
```

Now builds work with zero network access — great for:
- Air-gapped environments
- Docker builds without cache mount
- Reproducible CI

---

## 25. Advanced Cargo Configuration

### `.cargo/config.toml`

This file lives at either:
- `<project>/.cargo/config.toml` — project-level
- `~/.cargo/config.toml` — user-level (applies everywhere)

```toml
# ===========================================================
# Build settings
# ===========================================================
[build]
jobs          = 8                      # parallel jobs
target        = "x86_64-unknown-linux-musl"  # default target
rustc         = "/usr/local/bin/rustc"
rustflags     = ["-C", "target-cpu=native"]  # extra rustc flags
rustdocflags  = ["--cfg", "docsrs"]
incremental   = true
target-dir    = "/tmp/cargo-target"    # custom target dir

# ===========================================================
# Target-specific settings
# ===========================================================
[target.x86_64-unknown-linux-musl]
linker  = "x86_64-linux-musl-gcc"
rustflags = ["-C", "link-arg=-static"]

[target.aarch64-unknown-linux-gnu]
linker = "aarch64-linux-gnu-gcc"

[target.'cfg(target_os = "linux")']
rustflags = ["-C", "link-arg=-Wl,--as-needed"]

# ===========================================================
# Aliases — custom cargo commands
# ===========================================================
[alias]
b      = "build"
t      = "test"
r      = "run"
rr     = "run --release"
br     = "build --release"
c      = "check"
cl     = "clippy"
fmt    = "fmt --all"
ta     = "test --all-features"
tw     = "watch -x test"

# Multi-command alias
ci     = "hack check --feature-powerset"

# ===========================================================
# Registry settings
# ===========================================================
[registry]
default = "crates-io"
token   = "your-api-token"   # better: use `cargo login`

# Private registry
[registries]
my-registry = { index = "https://my-registry.example.com/index" }

# ===========================================================
# Source replacement (mirrors)
# ===========================================================
[source.crates-io]
replace-with = "tuna"       # use mirror

[source.tuna]
registry = "https://mirrors.tuna.tsinghua.edu.cn/git/crates.io-index.git"

# ===========================================================
# Network
# ===========================================================
[net]
retry          = 3       # retry on network failure
offline        = false
git-fetch-with-cli = true  # use system git instead of built-in

# ===========================================================
# HTTP settings
# ===========================================================
[http]
debug          = false
proxy          = "http://proxy.example.com:8080"
timeout        = 30
low-speed-limit = 5
check-revoke   = true
cainfo         = "/path/to/cert.pem"

# ===========================================================
# Future incompatible report
# ===========================================================
[future-incompat-report]
frequency = "always"
```

### RUSTFLAGS Common Values

```bash
# In env or config.toml rustflags

# Use native CPU features (better performance, not portable)
RUSTFLAGS="-C target-cpu=native" cargo build --release

# Enable specific CPU feature
RUSTFLAGS="-C target-feature=+avx2,+fma" cargo build --release

# Show link args
RUSTFLAGS="-Z print-link-args" cargo build

# Use mold linker (much faster linking)
RUSTFLAGS="-C link-arg=-fuse-ld=mold" cargo build

# Use lld linker
RUSTFLAGS="-C link-arg=-fuse-ld=lld" cargo build

# Abort on panic (like profile setting)
RUSTFLAGS="-C panic=abort" cargo build

# Deny all warnings
RUSTFLAGS="-D warnings" cargo build
```

---

## 26. CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:

env:
  CARGO_TERM_COLOR: always
  RUST_BACKTRACE: 1

jobs:
  test:
    name: Test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Rust
        uses: dtolnay/rust-toolchain@stable
        with:
          components: rustfmt, clippy

      - name: Cache cargo
        uses: Swatinem/rust-cache@v2

      - name: Check format
        run: cargo fmt --check

      - name: Clippy
        run: cargo clippy --all-targets --all-features -- -D warnings

      - name: Test
        run: cargo test --all-features

      - name: Build release
        run: cargo build --release

  audit:
    name: Security Audit
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: rustsec/audit-check@v1
        with:
          token: ${{ secrets.GITHUB_TOKEN }}

  coverage:
    name: Coverage
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - name: Install tarpaulin
        run: cargo install cargo-tarpaulin
      - name: Coverage
        run: cargo tarpaulin --out Xml
      - uses: codecov/codecov-action@v3
```

### Makefile Integration

```makefile
.PHONY: build test release check fmt lint clean audit

build:
	cargo build

test:
	cargo test --all-features

release:
	cargo build --release

check:
	cargo check --all-targets

fmt:
	cargo fmt --all

lint:
	cargo clippy --all-targets --all-features -- -D warnings

clean:
	cargo clean

audit:
	cargo audit

doc:
	cargo doc --open --no-deps

ci: fmt lint test audit
```

---

## 27. Performance Tips & Expert Tricks

### Faster Builds

```bash
# 1. Use mold linker (10x faster linking on Linux)
cargo install mold  # or: apt install mold
# Then in .cargo/config.toml:
# [build]
# rustflags = ["-C", "link-arg=-fuse-ld=mold"]

# 2. Use sccache (compiler cache)
cargo install sccache
# Then in .cargo/config.toml:
# [build]
# rustc-wrapper = "sccache"

# 3. Optimize dev deps
# In Cargo.toml — heavy deps like serde get compiled once with optimization:
# [profile.dev.package."*"]
# opt-level = 2

# 4. Split into a workspace — cargo compiles only changed crates

# 5. Use cargo check instead of cargo build during development

# 6. Cranelift backend (experimental, much faster compile)
rustup component add rustc-codegen-cranelift-preview --toolchain nightly
CARGO_PROFILE_DEV_CODEGEN_BACKEND=cranelift cargo +nightly build
```

### Binary Size Reduction

```toml
[profile.release]
opt-level       = "z"    # optimize for size (not speed)
lto             = true
codegen-units   = 1
panic           = "abort"
strip           = true
```

```bash
# Check binary size breakdown
cargo bloat --release --crates

# UPX compression (post-build)
upx --best target/release/my_app
```

### Checking What Gets Compiled

```bash
# Why is a crate included?
cargo tree -i serde

# Check what features are active
cargo tree -e features

# Show duplicate crate versions
cargo tree --duplicates
```

### `cargo fix` — Auto-fix Warnings

```bash
cargo fix              # fix compiler warnings
cargo fix --edition    # migrate to next edition
cargo fix --allow-dirty  # allow with uncommitted changes
```

### Dependency Inspection

```bash
# See metadata as JSON
cargo metadata
cargo metadata --format-version 1 | jq .packages[].name

# See package information
cargo pkgid serde     # get package ID

# Locate source of a crate
cargo locate-project  # prints Cargo.toml location
```

### Workspace Dependency Graph

```bash
cargo tree --workspace --depth 1
```

### Inspecting Compile Times

```bash
# Show per-crate compile times
cargo build --timings
# Opens target/cargo-timings/cargo-timing.html in browser
```

### Pro-Level Command Cheatsheet

```bash
# Fast feedback loop
cargo check                          # just check, no binary

# Find code quality issues
cargo clippy --all -- -D warnings

# Format code
cargo fmt

# Full lint pass before commit
cargo fmt --check && cargo clippy -- -D warnings && cargo test

# See all warnings
RUSTFLAGS="-W clippy::all" cargo clippy

# Expand a macro to see what it generates
cargo expand src::my_module

# Disassemble a function
cargo asm --release my_crate::sort::quicksort

# Profile with perf
cargo build --release
perf record target/release/my_app
perf report

# Run with sanitizers (nightly)
RUSTFLAGS="-Z sanitizer=address" cargo +nightly test
RUSTFLAGS="-Z sanitizer=thread"  cargo +nightly test  # ThreadSanitizer
RUSTFLAGS="-Z sanitizer=memory"  cargo +nightly test  # MemorySanitizer

# Print all cfg values for current target
rustc --print cfg

# Print list of supported targets
rustc --print target-list

# Emit IR for inspection
RUSTFLAGS="--emit=llvm-ir" cargo build --release
```

---

## Quick Reference: Command Summary

```
+-----------------------------+------------------------------------------+
| Command                     | Description                              |
+-----------------------------+------------------------------------------+
| cargo new <name>            | Create new binary project                |
| cargo new <name> --lib      | Create new library project               |
| cargo init                  | Init project in current dir              |
| cargo build                 | Build (debug mode)                       |
| cargo build --release       | Build (release mode)                     |
| cargo run                   | Build + run                              |
| cargo run -- <args>         | Build + run with args                    |
| cargo check                 | Type-check, no binary                    |
| cargo test                  | Run all tests                            |
| cargo test <name>           | Run tests matching name                  |
| cargo bench                 | Run benchmarks                           |
| cargo doc --open            | Generate + open docs                     |
| cargo clean                 | Delete target/ directory                 |
| cargo update                | Update Cargo.lock                        |
| cargo add <dep>             | Add dependency                           |
| cargo rm <dep>              | Remove dependency                        |
| cargo search <query>        | Search crates.io                         |
| cargo publish               | Publish to crates.io                     |
| cargo login <token>         | Authenticate with crates.io              |
| cargo tree                  | Show dependency tree                     |
| cargo audit                 | Security audit                           |
| cargo fmt                   | Format code                              |
| cargo clippy                | Lint code                                |
| cargo fix                   | Auto-fix warnings                        |
| cargo expand                | Expand macros                            |
| cargo vendor                | Vendor dependencies                      |
| cargo metadata              | Print project metadata as JSON           |
| cargo package               | Create .crate archive                    |
| cargo install <crate>       | Install binary from crates.io            |
| cargo uninstall <crate>     | Uninstall binary                         |
+-----------------------------+------------------------------------------+
```

---

*This document covers Cargo at an elite professional level. Master each section incrementally — start from project structure and work toward cross-compilation and live debugging. The deeper your understanding of Cargo, the more Rust's guarantees work in your favor.*

Here's your complete, elite-level Cargo reference — 27 chapters, zero fluff.

**What's covered end-to-end:**

- **Project anatomy** — binary vs library layout, multi-binary crates, workspace structure
- **Cargo.toml mastery** — every field explained with real examples including `[patch]`, feature inheritance, platform-specific deps
- **Cargo.lock** — when to commit, how it works, precise update control
- **Build system internals** — pipeline, artifact locations, codegen-units, LTO, panic strategies
- **Features & conditional compilation** — `cfg!`, `#[cfg(feature)]`, `dep:`, build-time cfg flags
- **Build scripts (`build.rs`)** — full communication protocol with Cargo, code generation, C FFI compilation
- **Cross compilation** — target triples, linker config, `cross` tool, musl static binaries
- **Live debugging** — `rust-gdb`, `rust-lldb`, VS Code CodeLLDB config, RustRover, flamegraph profiling, Valgrind
- **Testing** — unit, integration, doc tests, `cargo-nextest`, sanitizers (ASAN, TSAN, MSAN)
- **Benchmarking** — Criterion setup, baseline comparison, HTML reports
- **Security** — `cargo-audit`, `cargo-deny`, license enforcement
- **Publishing workflow** — dry-run, yanking, ownership management
- **Performance tricks** — `mold` linker, `sccache`, compile-time profiling (`--timings`), binary bloat analysis
- **`.cargo/config.toml`** — full local/global config with aliases, RUSTFLAGS, mirrors, offline vendoring
- **CI/CD** — GitHub Actions template with caching, coverage, audit

The mental model to build: **Cargo is a programmable build graph** — your `Cargo.toml` declares nodes, `build.rs` lets you inject custom nodes, and profiles control how each node is compiled. Once you internalize that, every Cargo behavior becomes predictable.

# The Complete Cargo Guide — Elite Pro Level
> Rust's build system, package manager, and workflow engine — end-to-end, first principles.

---

## SUMMARY (8 lines)

Cargo is the official Rust build system, package manager, test runner, documentation
generator, and workspace orchestrator rolled into one binary. It resolves dependency
graphs deterministically via `Cargo.lock`, compiles crates in parallel, runs unit/
integration/doc tests, generates docs via rustdoc, manages multiple crates in a
workspace, and supports pluggable subcommands via `cargo install`. Understanding Cargo
deeply means understanding how Rust source transforms into a binary: manifest parsing →
dependency resolution → build graph → compilation units → linking. For security-critical
production work, understanding feature flags, audit tooling, supply-chain controls,
reproducible builds, and cross-compilation are non-negotiable. This guide covers every
concept from first principles to live debugging at production depth.

---

## TABLE OF CONTENTS

1. [Mental Model — What Cargo Actually Is](#1-mental-model)
2. [Installation and Toolchain Management](#2-installation-and-toolchain-management)
3. [Cargo.toml — The Manifest In Depth](#3-cargotoml-the-manifest-in-depth)
4. [Cargo.lock — Determinism and Security](#4-cargolock)
5. [Project Layouts and Conventions](#5-project-layouts-and-conventions)
6. [Dependency Management](#6-dependency-management)
7. [Features and Conditional Compilation](#7-features-and-conditional-compilation)
8. [Workspaces](#8-workspaces)
9. [Build Scripts (build.rs)](#9-build-scripts-buildrs)
10. [Profiles — Debug, Release, Custom](#10-profiles)
11. [Testing — Unit, Integration, Doc, Fuzz](#11-testing)
12. [Benchmarking](#12-benchmarking)
13. [Documentation (rustdoc)](#13-documentation)
14. [Publishing to crates.io](#14-publishing-to-cratesio)
15. [Cross-Compilation](#15-cross-compilation)
16. [cargo check, clippy, fmt](#16-cargo-check-clippy-fmt)
17. [Cargo Subcommands — Built-in and Third-Party](#17-cargo-subcommands)
18. [Live Debugging with cargo](#18-live-debugging)
19. [Environment Variables Cargo Reads and Sets](#19-environment-variables)
20. [Caching, Incremental Compilation, and Sccache](#20-caching-and-incremental-compilation)
21. [Supply Chain Security — Audit, Vet, SBOM](#21-supply-chain-security)
22. [Reproducible Builds](#22-reproducible-builds)
23. [CI/CD Integration](#23-cicd-integration)
24. [Config Files (.cargo/config.toml)](#24-config-files)
25. [Internals — How Cargo Builds a Crate](#25-cargo-internals)
26. [Threat Model and Mitigations](#26-threat-model)
27. [Next 3 Steps](#27-next-3-steps)

---

## 1. Mental Model

```
SOURCE CODE
    |
    v
+------------------+
|   Cargo.toml     |  <- manifest: metadata, deps, features, profiles
|   Cargo.lock     |  <- exact versions pinned (determinism)
+------------------+
    |
    v
+------------------+
|  Dependency      |  <- resolves semver constraints from registry
|  Resolver        |     (crates.io, git, path, registry mirrors)
+------------------+
    |
    v
+------------------+
|  Build Graph     |  <- DAG of compilation units (crates)
|  (units)         |     each unit = (crate, profile, features, target)
+------------------+
    |  parallel edges
    v
+------------------+
|  rustc           |  <- Rust compiler (one invocation per unit)
|  invocations     |     produces .rlib / .rmeta / .so / binary
+------------------+
    |
    v
+------------------+
|  Linker          |  <- ld / lld / mold links final binary
+------------------+
    |
    v
  BINARY / LIB
```

Cargo does NOT compile Rust. `rustc` compiles Rust. Cargo orchestrates `rustc`
invocations, manages the build graph, downloads crates, and handles everything else.

### Crate vs Package vs Module

```
Package
  |-- Cargo.toml   (one package manifest)
  |-- src/
  |     |-- lib.rs         <- library crate root  (optional)
  |     |-- main.rs        <- binary crate root   (optional)
  |     |-- bin/
  |           |-- tool.rs  <- another binary crate
  |-- tests/               <- integration test crates
  |-- benches/             <- benchmark crates
  |-- examples/            <- example crates

Crate = single compilation unit fed to rustc
Module = namespace inside a crate (mod keyword)
```

---

## 2. Installation and Toolchain Management

### Install rustup (manages Rust + Cargo)

```bash
curl --proto '=https' --tlsv1.3 -sSf https://sh.rustup.rs | sh
```

`rustup` installs:
- `rustc`  — the compiler
- `cargo`  — the build tool
- `rustup` — the toolchain manager

### Toolchain Commands

```bash
rustup show                        # active toolchain and targets
rustup toolchain list              # all installed toolchains
rustup toolchain install stable    # install stable
rustup toolchain install nightly   # install nightly (needed for some features)
rustup toolchain install 1.77.0    # pin specific version

rustup default stable              # set global default
rustup override set nightly        # override for current directory only
rustup override unset              # remove override

rustup update                      # update all installed toolchains
rustup component add rustfmt       # add a component
rustup component add clippy
rustup component add rust-src      # needed for some IDE features and cross-compile
rustup component add llvm-tools-preview  # llvm-profdata, llvm-cov
```

### Check versions

```bash
cargo --version
rustc --version
rustup --version
```

### toolchain file (pin per project)

Create `rust-toolchain.toml` in project root:

```toml
[toolchain]
channel = "1.78.0"
components = ["rustfmt", "clippy"]
targets = ["x86_64-unknown-linux-musl"]
```

Cargo reads this automatically. Guarantees everyone on the team uses the same compiler.

---

## 3. Cargo.toml — The Manifest In Depth

```toml
# ── Package metadata ─────────────────────────────────────────────────────────
[package]
name        = "my-crate"         # crate name on crates.io (must be unique)
version     = "0.1.0"            # semver: MAJOR.MINOR.PATCH
edition     = "2021"             # Rust edition (2015, 2018, 2021)
rust-version = "1.70"            # minimum supported Rust version (MSRV)
authors     = ["You <you@example.com>"]
description = "One-line description"
license     = "MIT OR Apache-2.0"
repository  = "https://github.com/you/my-crate"
readme      = "README.md"
keywords    = ["security", "systems"]  # max 5 for crates.io
categories  = ["network-programming"]  # must be from crates.io list
exclude     = [".github/", "tests/fixtures/big-file"]
include     = ["src/**", "Cargo.toml", "README.md"]  # overrides exclude
publish     = true               # set false to prevent accidental publish

# ── Dependencies ─────────────────────────────────────────────────────────────
[dependencies]
serde       = { version = "1", features = ["derive"] }
tokio       = { version = "1", features = ["full"] }
anyhow      = "1"
clap        = { version = "4", features = ["derive", "env"] }

# git dependency (use for unreleased / forked crates)
my-fork = { git = "https://github.com/you/my-fork", branch = "main" }

# path dependency (local development / workspace member)
my-lib = { path = "../my-lib" }

# optional dependency (activated by feature flag)
openssl = { version = "0.10", optional = true }

# rename a dep to avoid name conflict
sqlx_ = { package = "sqlx", version = "0.7" }

# ── Dev dependencies (only compiled for tests/benches/examples) ───────────────
[dev-dependencies]
criterion = { version = "0.5", features = ["html_reports"] }
proptest   = "1"
tokio-test = "0.4"

# ── Build dependencies (only for build.rs) ────────────────────────────────────
[build-dependencies]
cc      = "1"
bindgen = "0.69"

# ── Features ─────────────────────────────────────────────────────────────────
[features]
default  = ["std"]               # features enabled by default
std      = []
tls      = ["openssl"]           # enables optional dep
full     = ["std", "tls"]

# ── Library target ────────────────────────────────────────────────────────────
[lib]
name      = "my_crate"           # crate name (underscores, not hyphens)
path      = "src/lib.rs"
crate-type = ["cdylib", "rlib"]  # cdylib for FFI .so/.dll, rlib for Rust linking

# ── Binary targets ────────────────────────────────────────────────────────────
[[bin]]
name    = "my-tool"
path    = "src/bin/tool.rs"
required-features = ["tls"]      # only build this bin if feature is on

# ── Example targets ───────────────────────────────────────────────────────────
[[example]]
name = "basic"
path = "examples/basic.rs"

# ── Bench targets ─────────────────────────────────────────────────────────────
[[bench]]
name    = "throughput"
harness = false                  # use custom harness (criterion)

# ── Integration test targets ──────────────────────────────────────────────────
[[test]]
name = "integration"
path = "tests/integration.rs"

# ── Profiles ─────────────────────────────────────────────────────────────────
[profile.dev]
opt-level = 0
debug     = true

[profile.release]
opt-level = 3
debug     = false
lto       = "thin"
strip     = "symbols"
panic     = "abort"              # smaller binary, no unwinding cost

[profile.release-with-debug]    # custom profile (inherits from release)
inherits  = "release"
debug     = true

# ── Workspace (if this is the workspace root) ─────────────────────────────────
[workspace]
members    = ["crates/*", "tools/cli"]
exclude    = ["crates/experimental"]
resolver   = "2"                 # use resolver v2 (required for edition 2021)

# ── Workspace-level dependency versions (shared across workspace) ─────────────
[workspace.dependencies]
tokio     = { version = "1", features = ["rt-multi-thread", "net"] }
serde     = { version = "1", features = ["derive"] }

# ── Patches (override a dependency anywhere in the graph) ─────────────────────
[patch.crates-io]
my-crate = { path = "../my-crate-dev" }
```

### Edition Notes

| Edition | Key Changes |
|---------|-------------|
| 2015    | Original edition |
| 2018    | `async/await`, module path clarity, `dyn Trait` required |
| 2021    | Resolver v2 default, `IntoIterator` for arrays, closure captures |

All editions are compatible at the crate boundary. A 2015 crate can depend on a 2021 crate.

---

## 4. Cargo.lock

### What it is

`Cargo.lock` is a snapshot of the exact dependency tree: every transitive dependency,
exact version, and checksum. It guarantees reproducible builds.

```
# Example Cargo.lock entry
[[package]]
name     = "serde"
version  = "1.0.197"
source   = "registry+https://github.com/rust-lang/crates.io-index"
checksum = "3fb1c873e1b9b056a4dc4c0c198b24c3ffa059243875552b2bd0933b1aee4ce2"
dependencies = [
 "serde_derive",
]
```

### When to commit it

| Project Type | Commit Cargo.lock? |
|---|---|
| Binary / application | YES — ensures reproducible builds |
| Library crate | Convention says NO (let consumers pick version) |
| Workspace with binaries | YES |

For security-critical systems: **always commit Cargo.lock**, even for libraries.
Without it, `cargo build` on a fresh clone may pull newer (potentially vulnerable) deps.

### Lock file operations

```bash
cargo update                  # update all deps within semver constraints
cargo update -p serde         # update only serde
cargo update -p serde --precise 1.0.195   # pin to exact version
cargo generate-lockfile       # create Cargo.lock without building
```

### How the resolver works

Cargo uses a SAT-like dependency resolver (resolver v2 since edition 2021):

```
Given:
  my-app depends on: libA >=1.0, libB >=2.0
  libA 1.2 depends on: libC >=3.0
  libB 2.1 depends on: libC >=3.1

Resolver finds:
  libC 3.1+ satisfies both >=3.0 and >=3.1
  picks: libC 3.2 (latest compatible)
```

Resolver v2 key difference: features are unified per package, not per dep edge.
This prevents accidental feature activation from transitive dependencies.

---

## 5. Project Layouts and Conventions

### Single-crate package (standard)

```
my-project/
├── Cargo.toml
├── Cargo.lock
├── src/
│   ├── lib.rs          <- library root
│   ├── main.rs         <- binary root (or bin/name.rs)
│   ├── bin/
│   │   ├── tool-a.rs   <- cargo run --bin tool-a
│   │   └── tool-b.rs
│   └── modules/
│       └── mod.rs
├── tests/
│   ├── integration_a.rs
│   └── common/
│       └── mod.rs      <- shared test helpers
├── benches/
│   └── bench_main.rs
├── examples/
│   └── basic_usage.rs  <- cargo run --example basic_usage
└── build.rs            <- build script (optional)
```

### Workspace (mono-repo)

```
workspace-root/
├── Cargo.toml          <- [workspace] manifest (no [package])
├── Cargo.lock          <- one lockfile for entire workspace
├── crates/
│   ├── core/
│   │   ├── Cargo.toml
│   │   └── src/lib.rs
│   ├── api/
│   │   ├── Cargo.toml
│   │   └── src/main.rs
│   └── cli/
│       ├── Cargo.toml
│       └── src/main.rs
└── tools/
    └── codegen/
        ├── Cargo.toml
        └── src/main.rs
```

---

## 6. Dependency Management

### Version specifiers (semver)

```toml
dep = "1"           # >= 1.0.0, < 2.0.0  (caret, default)
dep = "^1.2.3"      # >= 1.2.3, < 2.0.0  (explicit caret)
dep = "~1.2.3"      # >= 1.2.3, < 1.3.0  (tilde, patch updates only)
dep = "=1.2.3"      # exactly 1.2.3
dep = ">=1.0, <1.5" # range
dep = "*"           # any version (avoid in production)
```

### Dependency sources

```toml
# Registry (crates.io default)
serde = "1"

# Registry with alternate registry
my-private = { version = "1", registry = "my-registry" }

# Git
dep = { git = "https://github.com/user/repo" }
dep = { git = "https://github.com/user/repo", branch = "dev" }
dep = { git = "https://github.com/user/repo", tag = "v1.2.3" }
dep = { git = "https://github.com/user/repo", rev = "abc1234" }  # exact commit

# Path (local)
dep = { path = "../other-crate" }

# Renamed package
rand_ = { package = "rand", version = "0.8" }
```

### Inspect dependencies

```bash
cargo tree                           # full dependency tree
cargo tree -d                        # duplicate dependencies
cargo tree -p serde                  # tree for specific package
cargo tree -e features               # show features per dep
cargo tree --depth 2                 # limit depth
cargo tree -i serde                  # reverse tree (who depends on serde)

cargo metadata                       # full JSON graph (used by tools)
cargo metadata --format-version 1 | jq '.packages[].name'
```

### Dependency duplication

If two deps require incompatible versions of a third dep, Cargo compiles BOTH versions.
This is safe but inflates binary size. Use `cargo tree -d` to find duplicates and
resolve with `[patch]` or version bumps.

---

## 7. Features and Conditional Compilation

### Defining features

```toml
[features]
default  = ["std"]
std      = []
alloc    = []
serde    = ["dep:serde"]        # namespaced dep (cleaner than "serde/default")
tls-rustls = ["dep:rustls"]
tls-native = ["dep:openssl"]
full     = ["std", "serde", "tls-rustls"]

[dependencies]
serde    = { version = "1", optional = true }
rustls   = { version = "0.22", optional = true }
openssl  = { version = "0.10", optional = true }
```

### Enabling features from command line

```bash
cargo build --features tls-rustls            # add feature
cargo build --features "tls-rustls,serde"    # multiple
cargo build --all-features                   # enable everything
cargo build --no-default-features            # disable defaults
cargo build --no-default-features --features alloc  # minimal alloc build
```

### Conditional code

```rust
// Conditional compilation based on feature
#[cfg(feature = "tls-rustls")]
mod tls {
    // ...
}

// Conditional imports
#[cfg(feature = "serde")]
use serde::{Serialize, Deserialize};

// Available in ALL Rust code (set by Cargo or rustc)
#[cfg(target_os = "linux")]
#[cfg(target_arch = "x86_64")]
#[cfg(target_env = "musl")]
#[cfg(debug_assertions)]
#[cfg(test)]
```

### cfg in Cargo.toml

```toml
# Target-specific dependency (only on Linux)
[target.'cfg(target_os = "linux")'.dependencies]
nix = "0.27"

[target.'cfg(target_os = "windows")'.dependencies]
winapi = { version = "0.3", features = ["winsock2"] }

[target.'cfg(unix)'.dependencies]
libc = "0.2"
```

### Feature best practices (security angle)

- Prefer opt-in features over opt-out. Reduces attack surface by default.
- `default = []` for security libraries (user must explicitly enable extras).
- Use `dep:serde` syntax (namespaced deps) to avoid implicitly enabling serde's features.
- Avoid `--all-features` in production builds.

---

## 8. Workspaces

### Workspace Cargo.toml

```toml
[workspace]
resolver = "2"
members  = [
    "crates/core",
    "crates/api",
    "crates/cli",
    "tools/*",          # glob supported
]
exclude = ["tools/experimental"]

# Shared dependency versions — members inherit with workspace = true
[workspace.dependencies]
tokio   = { version = "1.36", features = ["rt-multi-thread", "net", "io-util"] }
serde   = { version = "1", features = ["derive"] }
anyhow  = "1"
tracing = "0.1"

[workspace.metadata]          # arbitrary metadata for tools
docs-rs.all-features = true
```

### Member inheriting workspace deps

```toml
# crates/api/Cargo.toml
[package]
name    = "api"
version = "0.1.0"
edition.workspace = true      # inherit edition from workspace

[dependencies]
tokio   = { workspace = true }       # uses version + features from workspace
serde   = { workspace = true, features = ["derive"] }  # can add extra features
core    = { path = "../core" }       # path to sibling crate
```

### Workspace commands

```bash
cargo build                    # build all workspace members
cargo build -p api             # build specific member
cargo build -p api -p cli      # build multiple specific members
cargo test --workspace         # test all members
cargo test -p core             # test specific member
cargo run -p cli               # run specific binary
cargo check --workspace        # check all without linking

# Building all at once (parallel, shared target/ dir)
cargo build --workspace --release
```

### Workspace target/ layout

```
workspace-root/
└── target/
    ├── debug/
    │   ├── core.rlib          <- library artifacts
    │   ├── api                <- binary
    │   └── .fingerprint/      <- incremental build state
    └── release/
        ├── api
        └── cli
```

All members share one `target/` dir. Cargo reuses compiled artifacts across members
automatically (this is a major build speed advantage of workspaces).

---

## 9. Build Scripts (build.rs)

### What is build.rs

A Rust program that runs BEFORE the crate is compiled. Used for:
- Compiling C/C++ code (via `cc` crate)
- Generating Rust bindings from C headers (via `bindgen`)
- Code generation (protocol buffers, etc.)
- Detecting system libraries (`pkg-config`)
- Setting environment variables for the main crate
- Embedding version/git info at compile time

### Example: embed git revision

```rust
// build.rs
fn main() {
    // Tell Cargo to re-run if git HEAD changes
    println!("cargo:rerun-if-changed=.git/HEAD");
    println!("cargo:rerun-if-changed=.git/refs/heads/");

    let output = std::process::Command::new("git")
        .args(["rev-parse", "--short", "HEAD"])
        .output()
        .unwrap();

    let git_hash = String::from_utf8(output.stdout).unwrap();
    let git_hash = git_hash.trim();

    // Set env var readable in main crate via env!("GIT_HASH")
    println!("cargo:rustc-env=GIT_HASH={git_hash}");
}
```

```rust
// src/main.rs
const VERSION: &str = env!("CARGO_PKG_VERSION");
const GIT_HASH: &str = env!("GIT_HASH");

fn main() {
    println!("Version: {VERSION}-{GIT_HASH}");
}
```

### Example: compile C code

```toml
# Cargo.toml
[build-dependencies]
cc = "1"
```

```rust
// build.rs
fn main() {
    cc::Build::new()
        .file("src/native/fast_hash.c")
        .flag("-O3")
        .compile("fast_hash");         // produces libfast_hash.a

    println!("cargo:rerun-if-changed=src/native/fast_hash.c");
}
```

### Example: generate bindings from C header (bindgen)

```toml
[build-dependencies]
bindgen = "0.69"
```

```rust
// build.rs
use std::path::PathBuf;

fn main() {
    println!("cargo:rerun-if-changed=wrapper.h");

    let bindings = bindgen::Builder::default()
        .header("wrapper.h")
        .parse_callbacks(Box::new(bindgen::CargoCallbacks::new()))
        .generate()
        .expect("Unable to generate bindings");

    let out_path = PathBuf::from(std::env::var("OUT_DIR").unwrap());
    bindings.write_to_file(out_path.join("bindings.rs")).unwrap();
}
```

```rust
// src/lib.rs
include!(concat!(env!("OUT_DIR"), "/bindings.rs"));
```

### build.rs output directives (println!)

```
cargo:rerun-if-changed=PATH     <- re-run build.rs if file changes
cargo:rerun-if-env-changed=VAR  <- re-run if env var changes
cargo:rustc-link-lib=foo        <- link libfoo.a or libfoo.so
cargo:rustc-link-lib=static=foo <- force static linking
cargo:rustc-link-search=PATH    <- add to linker search path
cargo:rustc-env=KEY=VALUE       <- set env var readable via env!()
cargo:rustc-cfg=feature="name"  <- enable a cfg flag
cargo:rustc-cdylib-link-arg=-s  <- pass arg to linker (cdylib only)
cargo:warning=message           <- print a warning
cargo:metadata=KEY=VALUE        <- metadata for other build scripts
```

---

## 10. Profiles

Profiles control how `rustc` compiles your code. Four built-in profiles:

| Profile | Command | opt-level | debug | What it's for |
|---------|---------|-----------|-------|---------------|
| dev | `cargo build` | 0 | true | Fast compile, slow run |
| release | `cargo build --release` | 3 | false | Fast run, slow compile |
| test | `cargo test` | 0 | true | Testing (uses dev settings) |
| bench | `cargo bench` | 3 | false | Benchmarking |

### Profile settings explained

```toml
[profile.release]
opt-level     = 3         # 0=none, 1=basic, 2=some, 3=all, "s"=size, "z"=min size
debug         = false     # true=full, 1=line tables only, 2=full (same as true), false
debug-assertions = false  # enable debug_assert! macros
overflow-checks  = false  # panic on integer overflow
lto           = "thin"    # link-time optimization: false, "thin", "fat", true
codegen-units = 1         # 1=best optimization, 16=fastest compile
rpath         = false
incremental   = false
panic         = "unwind"  # "unwind" or "abort" (abort=smaller, no stack unwinding)
strip         = "none"    # "none", "debuginfo", "symbols"

# Per-dependency overrides inside a profile
[profile.release.package.serde]
opt-level = 3             # always optimize serde even in dev builds
codegen-units = 1

[profile.dev.package."*"]
opt-level = 2             # optimize all deps in dev (faster tests)
```

### Custom profiles

```toml
# Inherits from release but keeps debug symbols
[profile.production]
inherits  = "release"
debug     = 1             # line tables for profiling
lto       = "fat"
strip     = "debuginfo"   # strip debug info but keep symbols

# Usage
# cargo build --profile production
```

### profile impact on security

- `debug = true` + published binary = stack traces expose internal names to attackers.
- `panic = "abort"` removes unwinding support → prevents panic-based exploits, smaller binary.
- `overflow-checks = true` in release can catch integer overflow bugs (performance cost).
- `lto = "fat"` enables cross-crate inlining which can eliminate more code (smaller attack surface).

---

## 11. Testing

### Test types in Rust

```
+-----------------------------------------------------------+
| Unit Tests         | Inside src/         | same crate     |
|                    | #[cfg(test)] mod    | private access |
+--------------------+---------------------+----------------+
| Integration Tests  | tests/              | separate crate |
|                    | each file = crate   | only pub API   |
+--------------------+---------------------+----------------+
| Doc Tests          | /// ```rust         | in docs        |
|                    | code blocks         | public API     |
+--------------------+---------------------+----------------+
| Benchmark Tests    | benches/            | separate crate |
|                    | #[bench] (unstable) | or criterion   |
+--------------------+---------------------+----------------+
```

### Unit tests

```rust
// src/lib.rs
pub fn add(a: u32, b: u32) -> u32 {
    a + b
}

#[cfg(test)]                         // only compiled when testing
mod tests {
    use super::*;                    // access private items

    #[test]
    fn test_add() {
        assert_eq!(add(2, 3), 5);
    }

    #[test]
    #[should_panic(expected = "overflow")]
    fn test_overflow() {
        add(u32::MAX, 1);
    }

    #[test]
    fn test_result() -> Result<(), String> {
        let n = "42".parse::<u32>().map_err(|e| e.to_string())?;
        assert_eq!(n, 42);
        Ok(())
    }

    #[test]
    #[ignore = "slow test, run explicitly"]
    fn slow_test() {
        // only runs with: cargo test -- --ignored
    }
}
```

### Integration tests

```rust
// tests/integration.rs
use my_crate::add;      // only public API available

#[test]
fn test_add_integration() {
    assert_eq!(add(1, 2), 3);
}
```

```rust
// tests/common/mod.rs  (shared helpers, NOT a test itself)
pub fn setup() -> SomeState {
    SomeState::new()
}
```

### Running tests

```bash
cargo test                            # run all tests
cargo test test_add                   # run tests matching name pattern
cargo test --lib                      # unit tests only
cargo test --test integration         # specific integration test file
cargo test --doc                      # doc tests only
cargo test --examples                 # test examples
cargo test -p core                    # workspace member

# Flags after -- go to the test binary
cargo test -- --nocapture             # print stdout (default: captured)
cargo test -- --test-threads=1        # single-threaded (for global state tests)
cargo test -- --ignored               # run ignored tests
cargo test -- --list                  # list test names without running
cargo test -- --format json           # JSON output (for CI parsing)
```

### Async tests (tokio)

```rust
#[cfg(test)]
mod tests {
    #[tokio::test]
    async fn test_async() {
        let result = some_async_fn().await;
        assert!(result.is_ok());
    }

    #[tokio::test(flavor = "multi_thread", worker_threads = 2)]
    async fn test_multi_thread() { ... }
}
```

### Property-based testing (proptest)

```toml
[dev-dependencies]
proptest = "1"
```

```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn parse_doesnt_crash(s in ".*") {
        // panics = test failures in proptest
        let _ = my_parser(&s);
    }

    #[test]
    fn add_is_commutative(a in 0u32..1000, b in 0u32..1000) {
        prop_assert_eq!(add(a, b), add(b, a));
    }
}
```

### Fuzzing (cargo-fuzz, AFL)

```bash
cargo install cargo-fuzz

# Initialize fuzzing targets (uses libFuzzer under the hood)
cargo fuzz init
cargo fuzz add my_target

# Edit fuzz/fuzz_targets/my_target.rs:
# #![no_main]
# use libfuzzer_sys::fuzz_target;
# fuzz_target!(|data: &[u8]| {
#     let _ = my_crate::parse(data);
# });

cargo fuzz run my_target                         # start fuzzing
cargo fuzz run my_target -- -jobs=4              # parallel
cargo fuzz run my_target -- -max_total_time=60   # 60 seconds
cargo fuzz corpus my_target                       # manage corpus
cargo fuzz coverage my_target                     # coverage report
```

### Code coverage

```bash
# Install llvm tools
rustup component add llvm-tools-preview
cargo install cargo-llvm-cov

cargo llvm-cov                        # print summary
cargo llvm-cov --html                 # HTML report in target/llvm-cov/html/
cargo llvm-cov --lcov --output-path lcov.info   # for CI

# Alternative: tarpaulin (Linux only, simpler)
cargo install cargo-tarpaulin
cargo tarpaulin --out Html
```

---

## 12. Benchmarking

### Using Criterion (recommended, stable Rust)

```toml
[dev-dependencies]
criterion = { version = "0.5", features = ["html_reports"] }

[[bench]]
name    = "my_bench"
harness = false           # REQUIRED: disables default libtest harness
```

```rust
// benches/my_bench.rs
use criterion::{criterion_group, criterion_main, Criterion, BenchmarkId};

fn bench_add(c: &mut Criterion) {
    c.bench_function("add 2+3", |b| b.iter(|| add(2, 3)));
}

fn bench_with_input(c: &mut Criterion) {
    let mut group = c.benchmark_group("parse");
    for size in [100, 1000, 10_000].iter() {
        group.bench_with_input(
            BenchmarkId::new("my_parser", size),
            size,
            |b, &size| b.iter(|| my_parser(&vec![0u8; size]))
        );
    }
    group.finish();
}

criterion_group!(benches, bench_add, bench_with_input);
criterion_main!(benches);
```

```bash
cargo bench                          # run all benchmarks
cargo bench bench_add                # filter by name
cargo bench -- --save-baseline main  # save baseline
cargo bench -- --baseline main       # compare against baseline
```

### Microbenchmarking with #[bench] (nightly only)

```rust
// Only on nightly: #![feature(test)]
extern crate test;
use test::Bencher;

#[bench]
fn bench_add(b: &mut Bencher) {
    b.iter(|| add(test::black_box(2), test::black_box(3)));
}
```

Use `test::black_box()` to prevent the compiler from optimizing away the benchmark.

---

## 13. Documentation

### Writing doc comments

```rust
/// Short one-line description.
///
/// Longer description. Supports **markdown**.
///
/// # Examples
///
/// ```
/// use my_crate::add;
/// assert_eq!(add(1, 2), 3);
/// ```
///
/// # Errors
///
/// Returns `Err` if the input overflows.
///
/// # Panics
///
/// Panics if `a` is zero.
///
/// # Safety
///
/// This function is safe to call from multiple threads.
pub fn add(a: u32, b: u32) -> u32 { a + b }

//! Module-level doc (inner doc comment, at top of file)
//! This documents the module itself.
```

### Cargo doc commands

```bash
cargo doc                        # generate docs for this crate + deps
cargo doc --no-deps              # only this crate (faster)
cargo doc --open                 # open in browser when done
cargo doc --document-private-items  # include private items

# Test all doc examples
cargo test --doc

# Check for broken links (nightly)
RUSTDOCFLAGS="-D rustdoc::broken-intra-doc-links" cargo doc
```

### Docs.rs features

docs.rs builds your crate automatically when published. Control it with:

```toml
[package.metadata.docs.rs]
features         = ["full"]           # features to enable for docs.rs build
all-features     = false
rustdoc-args     = ["--cfg", "docsrs"]  # enable #[doc(cfg(...))] annotations
targets          = ["x86_64-unknown-linux-gnu"]
```

---

## 14. Publishing to crates.io

### Pre-publish checklist

```bash
# 1. Check what will be published
cargo package --list

# 2. Dry run (build, check, no upload)
cargo publish --dry-run

# 3. Actually publish
cargo publish

# 4. Yank a bad version (does NOT delete, just warns users)
cargo yank --version 0.1.0
cargo yank --version 0.1.0 --undo   # un-yank

# 5. Update owner
cargo owner --add github:org:team
cargo owner --remove username
```

### API token setup

```bash
# Login (opens browser)
cargo login

# Or set token directly
cargo login <token>

# Token stored in ~/.cargo/credentials.toml
# For CI, use CARGO_REGISTRY_TOKEN env var
```

### Publishing workflow security

- Never commit `credentials.toml` to git.
- In CI, use `CARGO_REGISTRY_TOKEN` secret.
- Consider using `cargo release` (third-party) for automated versioning.

---

## 15. Cross-Compilation

### Add targets

```bash
rustup target add x86_64-unknown-linux-musl    # static Linux binary
rustup target add aarch64-unknown-linux-gnu    # Linux ARM64
rustup target add x86_64-apple-darwin          # macOS x86
rustup target add aarch64-apple-darwin         # macOS ARM (M1/M2)
rustup target add x86_64-pc-windows-gnu        # Windows (GNU toolchain)
rustup target add wasm32-unknown-unknown        # WebAssembly
rustup target add wasm32-wasi                  # WASI WebAssembly
rustup target add thumbv7em-none-eabihf        # bare metal ARM (embedded)

rustup target list --installed
rustup target list                             # all available targets
```

### Build for a target

```bash
cargo build --target x86_64-unknown-linux-musl
cargo build --target aarch64-unknown-linux-gnu
```

### Cross-compilation toolchain setup (Linux → musl static)

```bash
# Install musl cross-compile tools
sudo apt-get install musl-tools

# Configure linker in .cargo/config.toml
# (see Section 24)
```

### .cargo/config.toml for cross-compile

```toml
[target.x86_64-unknown-linux-musl]
linker = "x86_64-linux-musl-gcc"
rustflags = ["-C", "link-self-contained=yes", "-C", "target-feature=+crt-static"]

[target.aarch64-unknown-linux-gnu]
linker = "aarch64-linux-gnu-gcc"

[target.x86_64-pc-windows-gnu]
linker = "x86_64-w64-mingw32-gcc"
```

### Using `cross` (Docker-based, simplest approach)

```bash
cargo install cross

cross build --target aarch64-unknown-linux-gnu
cross test  --target aarch64-unknown-linux-gnu
cross build --target x86_64-unknown-linux-musl --release
```

`cross` uses a Docker container with the correct cross-toolchain pre-installed.
No manual linker setup needed. Best choice for CI.

### Musl static binary (zero runtime deps)

```bash
cargo build --target x86_64-unknown-linux-musl --release

# Verify: should output "statically linked"
file target/x86_64-unknown-linux-musl/release/my-binary
ldd  target/x86_64-unknown-linux-musl/release/my-binary
```

This is the gold standard for distributing Rust binaries: single file, no glibc
dependency, runs on any Linux kernel ≥ 3.x.

---

## 16. cargo check, clippy, fmt

### cargo check

```bash
cargo check                     # type-check without linking (10x faster than build)
cargo check --workspace
cargo check --target x86_64-unknown-linux-musl  # check for a target
```

`cargo check` is the fastest feedback loop. Use it in your editor via rust-analyzer.
It performs all type-checking but skips code generation and linking.

### cargo clippy — Linter

Clippy has 700+ lints organized into lint groups.

```bash
cargo clippy                                    # run lints
cargo clippy --workspace
cargo clippy -- -D warnings                    # treat warnings as errors (CI)
cargo clippy -- -D clippy::all                 # enable all lints
cargo clippy -- -A clippy::needless_return     # allow a specific lint
cargo clippy --fix                             # auto-fix fixable lints
cargo clippy --fix --allow-dirty              # fix with uncommitted changes
```

#### Lint groups

```
clippy::all        - all lints
clippy::correctness - likely bugs (enabled by default, errors)
clippy::suspicious  - suspicious code (enabled by default, warnings)
clippy::style       - style suggestions
clippy::complexity  - unnecessary complexity
clippy::perf        - performance improvements
clippy::pedantic    - strict, opinionated lints
clippy::nursery     - experimental lints
clippy::cargo       - Cargo.toml lints
```

#### In-code lint attributes

```rust
#[allow(clippy::too_many_arguments)]
fn complex_fn(a: u8, b: u8, c: u8, d: u8, e: u8, f: u8, g: u8) {}

#[deny(clippy::unwrap_used)]    // make unwrap a compile error in this scope
fn safe_fn() { ... }

#![deny(clippy::all)]           // deny all lints for entire file
#![allow(dead_code)]            // allow dead code for entire file
```

### cargo fmt — Code Formatter

```bash
cargo fmt                       # format all files in place
cargo fmt --check               # check only (exit 1 if changes needed, for CI)
cargo fmt -- --edition 2021     # specify edition
cargo fmt -p core               # format specific workspace member
```

Configure via `rustfmt.toml` or `.rustfmt.toml` in project root:

```toml
edition         = "2021"
max_width       = 100
tab_spaces      = 4
use_small_heuristics = "Default"
imports_granularity = "Module"
group_imports   = "StdExternalCrate"
```

---

## 17. Cargo Subcommands — Built-in and Third-Party

### Built-in commands

```bash
cargo new NAME              # create new package
cargo new NAME --lib        # create library
cargo new NAME --bin        # create binary (default)
cargo init                  # init in current directory
cargo init --lib

cargo add serde             # add dependency (modifies Cargo.toml)
cargo add serde --features derive
cargo add tokio@1.36
cargo add --dev proptest    # add to dev-dependencies
cargo add --build cc        # add to build-dependencies
cargo remove serde          # remove dependency

cargo build                 # compile
cargo run                   # compile and run
cargo run --bin tool-a      # run specific binary
cargo run -- arg1 arg2      # pass args to the program
cargo test
cargo bench
cargo check
cargo clean                 # delete target/
cargo doc
cargo publish
cargo package
cargo install NAME          # install binary from crates.io
cargo uninstall NAME
cargo update
cargo search NAME           # search crates.io
cargo info NAME             # crate info (version, deps)
cargo fetch                 # download deps without building
cargo vendor                # vendor all deps locally (for airgap/reproducibility)
cargo fix                   # automatically apply rustc suggestions
cargo report future-incompatibilities  # report future compat issues
```

### Third-party subcommands (install via cargo install)

```bash
# Security
cargo install cargo-audit       # audit deps for vulnerabilities (RustSec)
cargo install cargo-deny        # policy enforcement (licenses, bans, advisories)
cargo install cargo-vet         # supply chain verification (Mozilla)

# Development productivity
cargo install cargo-watch       # re-run on file change
cargo install cargo-expand      # expand macros
cargo install cargo-flamegraph  # profiling flamegraph
cargo install cargo-bloat       # what's taking space in my binary?
cargo install cargo-machete     # find unused dependencies
cargo install cargo-udeps       # find unused dependencies (nightly)
cargo install cargo-outdated    # find outdated dependencies
cargo install cargo-upgrades    # check for upgradeable deps

# Build helpers
cargo install cargo-binstall    # install binaries from releases (fast)
cargo install cross             # cross-compilation via Docker
cargo install cargo-release     # automated release workflow
cargo install cargo-nextest     # better test runner (faster, better output)

# WASM
cargo install wasm-pack         # build for WebAssembly

# Analysis
cargo install cargo-geiger      # count unsafe code
cargo install cargo-count       # count lines of code
```

### cargo-watch (live recompile)

```bash
cargo watch -x check                  # re-run check on change
cargo watch -x "test -- --nocapture"  # re-run tests
cargo watch -x run                    # re-run binary
cargo watch -x "clippy -- -D warnings" -x test   # chain commands
cargo watch -w src -x check           # watch specific directory
```

### cargo-nextest (better test runner)

```bash
cargo install cargo-nextest

cargo nextest run                      # run tests
cargo nextest run -p core              # specific workspace member
cargo nextest run --retries 2          # retry flaky tests
cargo nextest run --test-threads 16    # parallel test execution
cargo nextest show-config              # show config
```

Nextest runs each test in its own process (better isolation, better output, faster on
multi-core).

---

## 18. Live Debugging

### Using rust-gdb / rust-lldb

Cargo builds with debug symbols in dev profile. Use:

```bash
# Build with debug symbols
cargo build

# Launch GDB with Rust pretty-printers
rust-gdb target/debug/my-binary

# Or LLDB
rust-lldb target/debug/my-binary

# Pass arguments
rust-gdb --args target/debug/my-binary arg1 arg2
```

Inside GDB:

```gdb
(gdb) break main                     # breakpoint at main
(gdb) break my_crate::my_fn          # break at Rust function
(gdb) run
(gdb) next  / n                      # step over
(gdb) step  / s                      # step into
(gdb) continue / c                   # continue
(gdb) print my_var                   # print variable
(gdb) info locals                    # all local variables
(gdb) backtrace / bt                 # stack trace
(gdb) frame 2                        # switch to frame
(gdb) watch my_var                   # watchpoint
(gdb) list                           # show source
(gdb) quit
```

### VS Code / RustRover Debugging

You use RustRover (per your history). RustRover supports native LLDB/GDB debugging.

In RustRover:
1. Click the gutter icon next to a line → breakpoint
2. Run → Debug (Shift+F9) or click the bug icon
3. Evaluate expressions in the Debug panel
4. Hot-swap supported in some cases

Launch config for VS Code (`.vscode/launch.json`):

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "lldb",
      "request": "launch",
      "name": "Debug",
      "cargo": {
        "args": ["build", "--bin=my-binary", "--package=my-crate"],
        "filter": { "name": "my-binary", "kind": "bin" }
      },
      "args": ["--my-flag"],
      "cwd": "${workspaceFolder}",
      "env": { "RUST_LOG": "debug" }
    },
    {
      "type": "lldb",
      "request": "launch",
      "name": "Debug Tests",
      "cargo": {
        "args": ["test", "--no-run", "--lib"],
        "filter": { "name": "my-crate", "kind": "lib" }
      },
      "args": ["test_name_filter"]
    }
  ]
}
```

### Debug async (Tokio console)

```toml
# Cargo.toml
[dependencies]
tokio = { version = "1", features = ["full", "tracing"] }
console-subscriber = "0.3"
```

```rust
// main.rs
fn main() {
    console_subscriber::init();     // must be first
    // ... tokio runtime ...
}
```

```bash
cargo install tokio-console
cargo run                          # start your app with TOKIO_CONSOLE=1
tokio-console                      # in another terminal, see live task view
```

### Debugging build scripts

```bash
cargo build -vv                    # very verbose: shows all rustc invocations
cargo build -v                     # verbose: shows commands
```

### RUST_LOG (tracing / env_logger)

```bash
RUST_LOG=debug cargo run
RUST_LOG=my_crate=trace,other_crate=warn cargo run
RUST_LOG=trace cargo test -- --nocapture
```

### RUST_BACKTRACE

```bash
RUST_BACKTRACE=1 cargo run         # short backtrace on panic
RUST_BACKTRACE=full cargo run      # full backtrace with all frames
```

### Print cargo's internal execution plan

```bash
cargo build --message-format=json 2>&1 | jq '.reason'  # build events as JSON
cargo rustc -- --print cfg          # print all cfg values
cargo rustc -- -Z print-link-args   # print linker arguments (nightly)
```

### Address Sanitizer / Memory Sanitizer (nightly)

```bash
# AddressSanitizer (detect memory bugs)
RUSTFLAGS="-Z sanitizer=address" \
    cargo +nightly test --target x86_64-unknown-linux-gnu

# ThreadSanitizer (detect data races)
RUSTFLAGS="-Z sanitizer=thread" \
    cargo +nightly test --target x86_64-unknown-linux-gnu

# LeakSanitizer
RUSTFLAGS="-Z sanitizer=leak" \
    cargo +nightly run --target x86_64-unknown-linux-gnu

# MemorySanitizer (uninitialized reads, requires libc sources)
RUSTFLAGS="-Z sanitizer=memory" \
    cargo +nightly test --target x86_64-unknown-linux-gnu
```

### Flamegraph profiling

```bash
cargo install cargo-flamegraph
sudo cargo flamegraph --bin my-binary
# Opens flamegraph.svg in browser
```

### Inspecting the binary

```bash
cargo bloat --release                    # which functions are largest
cargo bloat --release --crates           # which crates use most space
nm -C target/release/my-binary          # symbol table
objdump -d target/release/my-binary     # disassembly
readelf -d target/release/my-binary     # dynamic section (deps)
```

---

## 19. Environment Variables

### Variables Cargo reads

```bash
CARGO_HOME              # where cargo stores its data (~/.cargo by default)
CARGO_TARGET_DIR        # override target/ directory location
CARGO_BUILD_JOBS        # number of parallel jobs (default: num CPUs)
CARGO_INCREMENTAL       # 0=disable incremental, 1=enable
CARGO_REGISTRIES_CRATES_IO_PROTOCOL=sparse   # use sparse protocol (faster)
CARGO_NET_OFFLINE=true  # build offline (no network)
CARGO_UNSTABLE_*        # enable unstable features

RUSTFLAGS               # flags passed to rustc for all crates
RUSTDOCFLAGS            # flags passed to rustdoc
RUSTC                   # path to rustc (override)
RUSTC_WRAPPER           # wrap rustc invocations (e.g., sccache)
CARGO_REGISTRY_TOKEN    # crates.io auth token (for CI publish)

HTTP_PROXY / HTTPS_PROXY / NO_PROXY  # proxy settings
```

### Variables Cargo sets for build.rs and proc macros

```bash
CARGO_MANIFEST_DIR      # absolute path to directory containing Cargo.toml
CARGO_PKG_NAME          # crate name
CARGO_PKG_VERSION       # crate version (e.g., "0.1.0")
CARGO_PKG_VERSION_MAJOR # "0"
CARGO_PKG_VERSION_MINOR # "1"
CARGO_PKG_VERSION_PATCH # "0"
CARGO_PKG_AUTHORS
CARGO_PKG_DESCRIPTION
CARGO_PKG_REPOSITORY
CARGO_PKG_LICENSE
CARGO_PKG_HOMEPAGE
CARGO_PKG_README
OUT_DIR                 # directory for build script output
PROFILE                 # "debug" or "release"
OPT_LEVEL               # "0", "1", "2", "3", "s", or "z"
DEBUG                   # "true" or "false"
HOST                    # host triple (e.g., x86_64-unknown-linux-gnu)
TARGET                  # target triple (e.g., x86_64-unknown-linux-musl)
NUM_JOBS                # number of parallel jobs
RUSTC_LINKER            # linker path
CARGO_CFG_*             # all cfg values (e.g., CARGO_CFG_TARGET_OS="linux")
CARGO_FEATURE_*         # one var per active feature (e.g., CARGO_FEATURE_STD=1)
```

### Read in code with env!()

```rust
// Compile-time (panics if not set at compile time)
const VERSION: &str = env!("CARGO_PKG_VERSION");
const PROFILE:  &str = env!("PROFILE");

// Option version (returns Option<&str>)
const OPT: Option<&str> = option_env!("CUSTOM_VAR");

// Runtime
let val = std::env::var("RUNTIME_VAR").unwrap_or_default();
```

---

## 20. Caching and Incremental Compilation

### How incremental compilation works

```
First build:
  rustc compiles every file → saves .d (dep info) + incremental state

Second build (one file changed):
  Cargo reads .d files → sees only foo.rs changed
  → recompiles only foo.rs and crates that depend on it
  → links new binary

Incremental state stored in:
  target/debug/.fingerprint/
  target/debug/incremental/
```

### Incremental compilation settings

```toml
[profile.dev]
incremental = true      # default for dev
[profile.release]
incremental = false     # default for release (full optimization needs full context)
```

Disable incremental if you see stale build bugs:
```bash
cargo clean && cargo build
CARGO_INCREMENTAL=0 cargo build
```

### Sccache — Shared compilation cache

Sccache intercepts `rustc` calls and caches outputs in local disk, S3, GCS, Redis, etc.
Critical for CI build speed.

```bash
cargo install sccache

# Set wrapper
export RUSTC_WRAPPER=sccache

# Now build normally
cargo build --release

# Stats
sccache --show-stats
sccache --zero-stats

# Configuration (~/.config/sccache/config)
# Or via SCCACHE_* env vars
```

```toml
# .cargo/config.toml
[build]
rustc-wrapper = "sccache"
```

For S3-backed cache (CI):

```bash
export SCCACHE_BUCKET=my-sccache-bucket
export SCCACHE_REGION=us-east-1
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export RUSTC_WRAPPER=sccache
```

### cargo-cache — manage the registry cache

```bash
cargo install cargo-cache

cargo cache              # show disk usage of ~/.cargo
cargo cache --autoclean  # remove old versions of cached crates
cargo cache -e           # show each component size
```

### Target directory on tmpfs (fast builds)

```bash
# Linux: put target/ on tmpfs for dramatically faster incremental builds
# WARNING: lost on reboot
sudo mount -t tmpfs -o size=8G tmpfs /tmp/cargo-target
export CARGO_TARGET_DIR=/tmp/cargo-target
```

---

## 21. Supply Chain Security — Audit, Vet, SBOM

### cargo-audit — check for known vulnerabilities

```bash
cargo install cargo-audit

cargo audit                        # check against RustSec Advisory Database
cargo audit --deny warnings        # fail on warnings too
cargo audit fix                    # attempt to auto-fix (upgrades deps)
cargo audit fix --dry-run

# Output formats
cargo audit --json                 # machine-readable output
```

Cargo audit checks `Cargo.lock` against https://rustsec.org advisories.

### cargo-deny — policy enforcement

```bash
cargo install cargo-deny

cargo deny init                    # create deny.toml
cargo deny check                   # run all checks
cargo deny check advisories        # only security advisories
cargo deny check licenses          # only license compliance
cargo deny check bans              # only banned crates
cargo deny check sources           # only source checks
```

Example `deny.toml`:

```toml
[advisories]
db-path     = "~/.cargo/advisory-db"
db-urls     = ["https://github.com/rustsec/advisory-db"]
vulnerability = "deny"             # deny crates with known vulns
unmaintained  = "warn"
yanked        = "deny"
notice        = "warn"

[licenses]
allow = [
    "MIT",
    "Apache-2.0",
    "Apache-2.0 WITH LLVM-exception",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "ISC",
    "Unicode-DFS-2016",
]
deny  = ["GPL-3.0"]
copyleft = "warn"

[bans]
multiple-versions = "warn"         # warn on duplicate dep versions
wildcards         = "deny"         # deny wildcard version specs
deny = [
    { name = "openssl", wrappers = ["native-tls"] },  # use rustls instead
]

[sources]
unknown-registry  = "deny"
unknown-git       = "deny"
allow-registry    = ["https://github.com/rust-lang/crates.io-index"]
```

### cargo-vet — Mozilla's supply chain verification

```bash
cargo install cargo-vet

cargo vet init                     # initialize vet store
cargo vet                          # check all deps are audited
cargo vet certify serde 1.0.197    # certify a specific crate version
cargo vet suggest                  # suggest what to audit next
cargo vet import                   # import someone else's audit set
```

Stores audit results in `supply-chain/audits.toml`. Commits to your repo.
Used by Firefox, curl, and other high-security projects.

### cargo-geiger — count unsafe code

```bash
cargo install cargo-geiger

cargo geiger                       # report unsafe code in all deps
cargo geiger --include-tests       # include test code
```

Output shows which crates use `unsafe` and how much. Use to make informed decisions
about dependencies in security-critical code.

### SBOM generation

```bash
# cyclonedx (industry standard SBOM format)
cargo install cargo-cyclonedx
cargo cyclonedx --format json      # JSON SBOM
cargo cyclonedx --format xml       # XML SBOM

# SPDX format
cargo install cargo-spdx
cargo spdx
```

---

## 22. Reproducible Builds

A reproducible build produces bit-for-bit identical output given the same source + tools.

### Requirements

1. Pin exact dependency versions → `Cargo.lock` committed
2. Pin toolchain → `rust-toolchain.toml` with exact version
3. Consistent linker flags
4. No timestamps in output (use `SOURCE_DATE_EPOCH`)
5. Consistent `RUSTFLAGS`

```bash
# Reproducible release build
export SOURCE_DATE_EPOCH=$(git log -1 --pretty=%ct)
export RUSTFLAGS="-C metadata=deadbeef"
cargo build --release --locked      # --locked: fail if Cargo.lock is out of date
```

### --locked flag (critical for CI)

```bash
cargo build --locked    # error if Cargo.lock doesn't match Cargo.toml
cargo test  --locked
```

Always use `--locked` in CI. Without it, CI might fetch newer (broken) patch versions.

### cargo vendor — air-gapped / offline builds

```bash
cargo vendor                        # download all deps to vendor/
cargo vendor vendor/                # specify directory

# Then add to .cargo/config.toml:
# [source.crates-io]
# replace-with = "vendored-sources"
# [source."vendored-sources"]
# directory = "vendor"

cargo build --offline               # build using only vendored sources
```

Commit `vendor/` to your repo for fully offline, auditable builds.

---

## 23. CI/CD Integration

### GitHub Actions example

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:

env:
  CARGO_TERM_COLOR: always
  CARGO_INCREMENTAL: 0        # disable incremental in CI
  CARGO_REGISTRIES_CRATES_IO_PROTOCOL: sparse
  RUSTFLAGS: "-D warnings"    # treat warnings as errors

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Rust
        uses: dtolnay/rust-toolchain@stable
        with:
          components: rustfmt, clippy

      - name: Cache
        uses: Swatinem/rust-cache@v2
        with:
          shared-key: "ci"

      - run: cargo fmt --check
      - run: cargo clippy --workspace -- -D warnings
      - run: cargo test --workspace --locked
      - run: cargo audit

  build-release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
        with:
          targets: x86_64-unknown-linux-musl
      - run: cargo build --release --target x86_64-unknown-linux-musl --locked
      - uses: actions/upload-artifact@v4
        with:
          name: my-binary-linux-musl
          path: target/x86_64-unknown-linux-musl/release/my-binary
```

### Dockerfile with cargo-chef (layer caching)

```dockerfile
# Multi-stage build with dependency layer caching
FROM rust:1.78-slim as chef
RUN cargo install cargo-chef
WORKDIR /app

# Plan stage: compute dep recipe
FROM chef as planner
COPY . .
RUN cargo chef prepare --recipe-path recipe.json

# Build stage: build deps first (cached layer)
FROM chef as builder
COPY --from=planner /app/recipe.json recipe.json
RUN cargo chef cook --release --recipe-path recipe.json

# Build application (only app code, deps already cached)
COPY . .
RUN cargo build --release --locked

# Final minimal image
FROM debian:bookworm-slim
COPY --from=builder /app/target/release/my-binary /usr/local/bin/
ENTRYPOINT ["/usr/local/bin/my-binary"]
```

For fully static binary (no runtime deps):

```dockerfile
FROM rust:1.78-alpine as builder
RUN apk add --no-cache musl-dev
WORKDIR /app
COPY . .
RUN cargo build --release --target x86_64-unknown-linux-musl --locked

FROM scratch                           # absolute minimal image
COPY --from=builder /app/target/x86_64-unknown-linux-musl/release/my-binary /
ENTRYPOINT ["/my-binary"]
```

---

## 24. Config Files (.cargo/config.toml)

Config files live in:
1. `.cargo/config.toml` — project-level (committed to repo)
2. `~/.cargo/config.toml` — user-level (global defaults)
3. Each parent directory up to root is also checked

Lower (more specific) directories override higher ones.

```toml
# .cargo/config.toml

[build]
rustc-wrapper   = "sccache"          # wrap rustc (caching)
jobs            = 8                  # parallel jobs
target-dir      = "/tmp/cargo-target" # shared target dir
rustflags       = ["-C", "link-arg=-fuse-ld=mold"]  # use mold linker

[net]
retry           = 3
offline         = false
git-fetch-with-cli = true            # use system git (for SSH keys)

[http]
multiplexing    = true
debug           = false

[profile.dev.package."*"]
opt-level       = 2                  # optimize all deps in dev (faster tests)

# Target-specific linker
[target.x86_64-unknown-linux-gnu]
linker          = "clang"
rustflags       = ["-C", "link-arg=-fuse-ld=lld"]

[target.x86_64-unknown-linux-musl]
linker          = "x86_64-linux-musl-gcc"

[target.aarch64-unknown-linux-gnu]
linker          = "aarch64-linux-gnu-gcc"

# Registry config
[registries.my-internal]
index           = "https://registry.internal.company.com/index"

[registry]
default         = "crates-io"

# Source replacement (for mirroring crates.io)
[source.crates-io]
replace-with    = "company-mirror"

[source.company-mirror]
registry        = "https://mirror.internal.company.com/crates.io-index"

# Aliases
[alias]
b   = "build"
t   = "test"
r   = "run"
rr  = "run --release"
c   = "check"
br  = "build --release"
sec = "audit"
```

### Faster linker setup (mold)

```bash
# Install mold (fastest linker for Linux)
sudo apt-get install mold   # or: cargo install mold

# .cargo/config.toml
[target.x86_64-unknown-linux-gnu]
rustflags = ["-C", "link-arg=-fuse-ld=mold"]

# or globally:
[build]
rustflags = ["-C", "link-arg=-fuse-ld=mold"]
```

mold is 5-10x faster than GNU ld for incremental links. Critical for dev loop speed.

---

## 25. Cargo Internals — How Cargo Builds a Crate

### Full build pipeline (step by step)

```
Step 1: Parse Manifest
  Read Cargo.toml, resolve workspace, parse features

Step 2: Resolve Dependencies
  Read Cargo.lock (or solve if missing)
  For each dep: check local cache (~/.cargo/registry)
  Download missing crates from registry (checksums verified)
  Verify checksums against Cargo.lock

Step 3: Build Graph
  Create a DAG of compilation units
  Each node = (package, profile, features, target, mode)
  Edges = dependency relationships

Step 4: Topological Order
  Process units bottom-up (leaves first)
  Parallel execution of independent units

Step 5: Fingerprint Check
  Each unit has a fingerprint (hash of: source, deps, flags, env)
  If fingerprint unchanged → skip recompilation

Step 6: Run build.rs (if present)
  Compile build script crate
  Execute build script
  Collect output directives

Step 7: rustc Invocation
  For each unit:
    cargo invokes: rustc [flags] --edition=2021 --crate-type=... src/lib.rs
  Output: .rlib (Rust lib), .rmeta (metadata for dependent crates)

Step 8: Link
  For final binary: invoke linker with all .rlib + .o files
  Produces executable
```

### How cargo invokes rustc

To see the exact rustc commands Cargo runs:

```bash
cargo build -v             # verbose: prints each rustc command
cargo build -vv            # very verbose: also prints build script output

# Example output:
#   Running `rustc --edition=2021 --crate-name my_crate src/lib.rs
#     --crate-type lib
#     --emit=dep-info,metadata,link
#     -C opt-level=0
#     -C embed-bitcode=no
#     -C debuginfo=2
#     --out-dir target/debug/deps
#     -L dependency=target/debug/deps
#     --extern serde=target/debug/deps/libserde-abc123.rlib`
```

### Crate types explained

| crate-type | Output | Use case |
|---|---|---|
| `bin` | executable | main.rs binaries |
| `lib` / `rlib` | `.rlib` | Rust-only library |
| `cdylib` | `.so` / `.dll` | FFI shared library (Python, C, etc.) |
| `staticlib` | `.a` | FFI static library |
| `dylib` | `.so` | Rust dylib (avoid, ABI unstable) |
| `proc-macro` | `.so` | Procedural macros |

### .fingerprint directory

```
target/debug/.fingerprint/
  serde-abc123/
    dep-lib-serde         <- dep-info file (input file list)
    invoked.timestamp     <- when this unit was built
    lib-serde             <- fingerprint hash
    lib-serde.json        <- metadata
```

Cargo reads `.fingerprint` to decide what to rebuild. If you see "correct" behavior
not happening (stale builds), inspect this directory or run `cargo clean`.

---

## 26. Threat Model and Mitigations

```
THREAT SURFACE MAP
==================

External (supply chain)
  ┌─────────────────────────────────────────────────┐
  │  crates.io registry    ← typosquatting attacks  │
  │  Git dependencies      ← compromised repos      │
  │  Build scripts         ← arbitrary code exec    │
  │  Proc macros           ← arbitrary code exec    │
  └─────────────────────────────────────────────────┘

Build-time
  ┌─────────────────────────────────────────────────┐
  │  build.rs              ← runs on your machine   │
  │  Env vars              ← secret leakage         │
  │  Network access        ← data exfiltration      │
  └─────────────────────────────────────────────────┘

Runtime (binary)
  ┌─────────────────────────────────────────────────┐
  │  Debug symbols         ← information leak       │
  │  Unsafe code           ← memory vulnerabilities │
  │  Panics                ← DoS via unwind          │
  └─────────────────────────────────────────────────┘
```

### Mitigations

| Threat | Mitigation |
|---|---|
| Vulnerable dep | `cargo audit` + `cargo deny` in CI |
| Typosquatting | Review dep names carefully; use `cargo deny` bans |
| Compromised dep | `cargo vet`, pin exact git commits |
| Malicious build.rs | `cargo geiger`, review build scripts before first build |
| Compromised registry | Use `cargo vendor` + verify checksums |
| Secret in env during build | Audit what build.rs reads via `env::var()` |
| Debug info in release | `strip = "symbols"` in release profile |
| Integer overflow | `overflow-checks = true` in release profile |
| Panics (DoS) | `panic = "abort"` in release profile |
| Excessive unsafe | `cargo geiger`, `#![deny(unsafe_code)]` at crate root |
| License violations | `cargo deny check licenses` |
| Stale Cargo.lock | `--locked` in CI, commit Cargo.lock |
| MITM of registry | crates.io uses TLS + checksums in Cargo.lock |

### Enforce no unsafe at crate level

```rust
// src/lib.rs
#![deny(unsafe_code)]    // compile error if any unsafe{} block used
```

Allow specific exceptions:

```rust
// Only allow unsafe in one controlled module
#![deny(unsafe_code)]

mod ffi {
    #![allow(unsafe_code)]   // override for this module only
    // ... FFI bindings ...
}
```

---

## 27. Next 3 Steps

**Step 1 — Harden your current project:**
```bash
cargo install cargo-audit cargo-deny cargo-geiger
cargo audit
cargo deny init && cargo deny check
cargo geiger 2>&1 | head -50
```
Add `cargo audit` and `cargo deny check` to your CI pipeline before anything merges.

**Step 2 — Set up a reproducible, fast build environment:**
```bash
# 1. Add rust-toolchain.toml with exact version
cat > rust-toolchain.toml << 'EOF'
[toolchain]
channel = "1.78.0"
components = ["rustfmt", "clippy", "rust-src"]
EOF

# 2. Install mold for fast linking
sudo apt-get install mold
echo '[build]
rustflags = ["-C", "link-arg=-fuse-ld=mold"]' >> .cargo/config.toml

# 3. Install sccache
cargo install sccache
echo 'rustc-wrapper = "sccache"' >> .cargo/config.toml
```

**Step 3 — Integrate cargo-nextest + coverage into your workflow:**
```bash
cargo install cargo-nextest cargo-llvm-cov
cargo nextest run --workspace
cargo llvm-cov --workspace --html
# View: open target/llvm-cov/html/index.html
```

---

## REFERENCES

- Cargo Book (official): https://doc.rust-lang.org/cargo/
- Cargo API docs: https://docs.rs/cargo/latest/cargo/
- RustSec Advisory DB: https://rustsec.org/
- cargo-deny docs: https://embarkstudios.github.io/cargo-deny/
- cargo-vet docs: https://mozilla.github.io/cargo-vet/
- The Rust Reference (cfg): https://doc.rust-lang.org/reference/conditional-compilation.html
- rustc Book: https://doc.rust-lang.org/rustc/
- Criterion.rs: https://bheisler.github.io/criterion.rs/book/
- cargo-nextest: https://nexte.st/
- Cross-compilation: https://rust-lang.github.io/rustup/cross-compilation.html
- Reproducible Builds: https://reproducible-builds.org/
- CNCF + Rust: https://landscape.cncf.io/

---
*Guide generated for: cargo / Rust ecosystem — all versions as of Rust 1.78 / Cargo 1.78*

Now I'll build the complete guide as a `.md` file.27 sections, zero fluff. Here's what's packed in:

**Architecture** — the mental model of `cargo → rustc → linker`, the difference between crate/package/module, and how the build graph is a DAG of compilation units.

**Manifest deep-dive** — every `Cargo.toml` field explained: editions, MSRV, crate-types, `optional` deps, `dep:` namespacing, workspace inheritance, `[patch]`.

**Cargo.lock** — why you always commit it for binaries, how the resolver v2 SAT-solving works, and what semver specifiers actually mean.

**Build scripts** — `build.rs` from scratch: embed git hash, compile C, generate `bindgen` bindings, all output directives documented.

**Live debugging** — `rust-gdb`/`rust-lldb`, RustRover/VS Code launch configs, `tokio-console` for async, `RUST_BACKTRACE`, sanitizers (ASan/TSan/MSan), flamegraphs, `cargo bloat`.

**Supply-chain security** — `cargo-audit`, `cargo-deny` with full `deny.toml`, `cargo-vet`, `cargo-geiger` unsafe counts, SBOM generation. This section is production-grade for your threat model.

**Reproducible builds** — `--locked`, `SOURCE_DATE_EPOCH`, `cargo vendor` for airgap builds.

**CI/CD** — GitHub Actions with `Swatinem/rust-cache`, `cargo-chef` Dockerfile pattern, `FROM scratch` musl image.

**Next 3 steps** are immediately runnable commands, not theory.