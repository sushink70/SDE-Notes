# Elite Rust Compiler Mastery: A Complete Deep-Dive Guide

> **Scope**: Rust compiler pipeline, diagnostics, errors, warnings, lints, borrow checker, lifetime inference, type system, MIR/HIR, compiler flags, clippy, custom lints, deny/allow/warn attributes, macro diagnostics, unsafe, and production-grade mitigation patterns. Simplified language, elite-level depth.

---

## Table of Contents

1. [Rust Compiler Architecture — First Principles](#1-rust-compiler-architecture--first-principles)
2. [Compiler Pipeline: From Source to Binary](#2-compiler-pipeline-from-source-to-binary)
3. [Diagnostic System Internals](#3-diagnostic-system-internals)
4. [Error vs Warning vs Note vs Help vs Lint](#4-error-vs-warning-vs-note-vs-help-vs-lint)
5. [Reading and Decoding Compiler Output](#5-reading-and-decoding-compiler-output)
6. [The Error Code Index (E-codes)](#6-the-error-code-index-e-codes)
7. [Borrow Checker Errors — Deep Mastery](#7-borrow-checker-errors--deep-mastery)
8. [Lifetime Errors — Complete Reference](#8-lifetime-errors--complete-reference)
9. [Type System Errors](#9-type-system-errors)
10. [Trait and Impl Errors](#10-trait-and-impl-errors)
11. [Ownership and Move Errors](#11-ownership-and-move-errors)
12. [Mutability Errors](#12-mutability-errors)
13. [Pattern Matching and Exhaustiveness Errors](#13-pattern-matching-and-exhaustiveness-errors)
14. [Macro Expansion Errors](#14-macro-expansion-errors)
15. [Unsafe Code Errors and UB](#15-unsafe-code-errors-and-ub)
16. [Closures and Capture Errors](#16-closures-and-capture-errors)
17. [Async/Await Errors](#17-asyncawait-errors)
18. [Generic and Associated Type Errors](#18-generic-and-associated-type-errors)
19. [Const and Static Errors](#19-const-and-static-errors)
20. [Lint System — Complete Reference](#20-lint-system--complete-reference)
21. [Clippy — Elite Usage](#21-clippy--elite-usage)
22. [Compiler Flags and RUSTFLAGS](#22-compiler-flags-and-rustflags)
23. [Cargo and Compiler Integration](#23-cargo-and-compiler-integration)
24. [deny/allow/warn/forbid — Attribute System](#24-denyallowwarnforbid--attribute-system)
25. [Custom Lints and Compiler Plugins](#25-custom-lints-and-compiler-plugins)
26. [MIR — Mid-level Intermediate Representation](#26-mir--mid-level-intermediate-representation)
27. [HIR — High-level Intermediate Representation](#27-hir--high-level-intermediate-representation)
28. [LLVM Backend Errors](#28-llvm-backend-errors)
29. [Incremental Compilation and Errors](#29-incremental-compilation-and-errors)
30. [Proc Macros and Diagnostic APIs](#30-proc-macros-and-diagnostic-apis)
31. [Fuzzing, Testing, and Compiler Validation](#31-fuzzing-testing-and-compiler-validation)
32. [Production-Grade Error Mitigation Patterns](#32-production-grade-error-mitigation-patterns)
33. [Common Expert-Level Mistakes and Their Fixes](#33-common-expert-level-mistakes-and-their-fixes)
34. [Security-Relevant Compiler Behaviors](#34-security-relevant-compiler-behaviors)
35. [References and Resources](#35-references-and-resources)

---

## 1. Rust Compiler Architecture — First Principles

### What `rustc` Actually Is

`rustc` is a multi-pass, multi-stage compiler written in Rust itself (bootstrapped). It is not a simple single-pass compiler. It operates through a sequence of well-defined transformations, each phase building on the previous one, and each phase capable of emitting diagnostics (errors, warnings, notes, hints).

### Bootstrapping

Rust is a self-hosting language. `rustc` is compiled by an older `rustc`. This means there are always at least two compiler versions involved in a build: the "stage0" (downloaded prebuilt binary) and "stage1" (built from source using stage0). This matters because:

- Compiler internals can refer to compiler-internal APIs not exposed publicly.
- Nightly features (`#![feature(...)]`) unlock unstable compiler internals.
- You can compile `rustc` yourself to experiment with internal passes.

### Key Crates Inside `rustc`

The compiler is organized as a workspace of internal crates:

```
rustc_ast          — Abstract Syntax Tree definitions
rustc_ast_passes   — Early AST validation passes
rustc_hir          — High-level IR definitions
rustc_middle       — MIR, type context (TyCtxt), core type system
rustc_typeck        — Type checking (now rustc_hir_analysis)
rustc_borrowck     — Borrow checker (NLL)
rustc_mir_build    — HIR → MIR lowering
rustc_mir_transform — MIR optimization passes
rustc_codegen_llvm — LLVM backend
rustc_errors       — Diagnostic emission infrastructure
rustc_lint         — Lint infrastructure
rustc_span         — Source spans, source map
rustc_session      — Compiler session, flags, options
```

Understanding this layout tells you where a specific class of error comes from and how to debug or suppress it.

---

## 2. Compiler Pipeline: From Source to Binary

### The Full Pipeline

```
Source (.rs files)
    │
    ▼
[Lexing / Tokenization]         — rustc_lexer
    │  Converts raw text to tokens (keywords, idents, literals, punctuation)
    │
    ▼
[Parsing]                       — rustc_parse
    │  Tokens → AST (Abstract Syntax Tree)
    │  Errors here: syntax errors, unexpected tokens
    │
    ▼
[Macro Expansion]               — rustc_expand
    │  Expands macros, proc-macros, derive macros
    │  Errors here: macro rule mismatch, ambiguous expansions
    │
    ▼
[Name Resolution]               — rustc_resolve
    │  Binds names to definitions, resolves use paths
    │  Errors here: unresolved imports, ambiguous names
    │
    ▼
[AST Validation Passes]         — rustc_ast_passes
    │  Early semantic checks on AST
    │
    ▼
[HIR Lowering]                  — rustc_hir
    │  AST → HIR (High-level IR, desugared, more explicit)
    │  Desugars: for loops, ?, await, impl Trait
    │
    ▼
[Type Inference + Checking]     — rustc_hir_analysis (typeck)
    │  Infers and checks all types
    │  Errors here: type mismatch, trait not satisfied, missing methods
    │
    ▼
[Borrow Checking (NLL)]         — rustc_borrowck
    │  Non-Lexical Lifetimes analysis
    │  Errors here: use-after-move, double borrow, lifetime violations
    │
    ▼
[MIR Building]                  — rustc_mir_build
    │  HIR → MIR (Mid-level IR, explicit control flow graph)
    │  Errors here: non-exhaustive patterns
    │
    ▼
[MIR Validation + Passes]       — rustc_mir_transform
    │  Optimizations, inlining, NRVO, const eval
    │  Errors here: const eval panics, invalid MIR
    │
    ▼
[LLVM IR Generation]            — rustc_codegen_llvm
    │  MIR → LLVM IR
    │
    ▼
[LLVM Optimization + Codegen]
    │  LLVM → machine code
    │  Errors here: linker errors, LLVM assertion failures
    │
    ▼
[Linking]                       — system linker (lld, ld, link.exe)
    │  Links object files, libraries
    │  Errors here: undefined symbols, duplicate symbols
    │
    ▼
Binary / Library
```

### Why This Matters for Error Understanding

Every error has an origin phase. Knowing the phase tells you:
- **Syntax errors** → fix before anything else; parsing aborts early.
- **Type errors** → the type checker rejected your code; no borrow checking has occurred yet.
- **Borrow errors** → types are correct but ownership/aliasing rules are violated.
- **MIR errors** → control flow / pattern matching problems.
- **LLVM/linker errors** → code generation or linking problems, not logic errors.

---

## 3. Diagnostic System Internals

### How `rustc` Emits Diagnostics

All diagnostics in `rustc` flow through `rustc_errors::DiagnosticBuilder`. Every diagnostic has:

- **Level**: `Error`, `Warning`, `Note`, `Help`, `FailureNote`, `Bug`
- **Message**: Human-readable string
- **Span**: Source location(s) pointing at the code
- **Code**: Optional error code like `E0382`
- **Children**: Sub-diagnostics (notes, hints, suggestions)
- **Suggestions**: Machine-applicable code fixes

### Diagnostic Rendering Formats

```bash
# Default human-readable
rustc main.rs

# Short form (one line per error)
rustc --error-format=short main.rs

# JSON (machine-readable, used by IDEs, rust-analyzer)
rustc --error-format=json main.rs

# JSON with rendered field (includes terminal output in JSON)
rustc --error-format=json --json=diagnostic-rendered-ansi main.rs

# Human + JSON
rustc --error-format=json --json=diagnostic-short main.rs
```

### JSON Diagnostic Structure

When using `--error-format=json`, each line is a JSON object:

```json
{
  "message": "cannot borrow `x` as mutable because it is also borrowed as immutable",
  "code": { "code": "E0502", "explanation": "..." },
  "level": "error",
  "spans": [
    {
      "file_name": "src/main.rs",
      "byte_start": 100,
      "byte_end": 120,
      "line_start": 5,
      "line_end": 5,
      "column_start": 5,
      "column_end": 25,
      "is_primary": true,
      "label": "mutable borrow occurs here",
      "suggested_replacement": null,
      "suggestion_applicability": null
    }
  ],
  "children": [
    {
      "message": "immutable borrow later used here",
      "level": "note",
      "spans": [...]
    }
  ],
  "rendered": "error[E0502]: ..."
}
```

This is the format consumed by rust-analyzer, cargo's JSON output, and CI systems.

---

## 4. Error vs Warning vs Note vs Help vs Lint

### Taxonomy of Diagnostics

| Level         | Meaning                                                          | Blocks compilation? |
|---------------|------------------------------------------------------------------|---------------------|
| `error`       | Code is invalid; compilation cannot succeed                      | Yes                 |
| `warning`     | Code is valid but suspicious; may indicate bugs                  | No (unless `deny`)  |
| `note`        | Additional context attached to an error or warning               | No                  |
| `help`        | Suggestion on how to fix an error or warning                     | No                  |
| `suggestion`  | Machine-applicable code change (auto-fixable)                    | No                  |
| `lint`        | Warning emitted by a lint check (can be promoted to error)       | Depends             |

### Error vs Lint — Key Distinction

**Hard errors** are unconditional. You cannot silence `E0382` (use after move) with `#[allow]`. The code is fundamentally invalid.

**Lint warnings** are configurable. The `unused_variables` lint can be allowed with `#[allow(unused_variables)]`. Lint warnings are emitted by the lint pass, not the core type/borrow checker.

```rust
// This is a hard error — cannot allow it:
let x = String::from("hello");
drop(x);
println!("{}", x); // E0382: value borrowed after move

// This is a lint warning — can be allowed:
#[allow(unused_variables)]
let y = 42; // warning: unused variable `y` (suppressed)
```

### The `--deny-warnings` / `-D warnings` Pattern

In CI environments, a common practice is:

```bash
RUSTFLAGS="-D warnings" cargo build
```

This promotes ALL warnings to hard errors. Any warning = build fails. This is a gate for production code quality.

However, this interacts badly with dependency warnings if you're using `cargo`'s workspace. Use `[profile.dev]` or `[profile.release]` lint settings instead for workspace-wide control.

---

## 5. Reading and Decoding Compiler Output

### Anatomy of a Compiler Error Message

```
error[E0502]: cannot borrow `data` as mutable because it is also borrowed as immutable
  --> src/main.rs:10:5
   |
8  |     let r = &data;          // immutable borrow starts here
   |              ---- immutable borrow occurs here
9  |     println!("{}", r);
10 |     data.push(42);          // mutable borrow here — CONFLICT
   |     ^^^^ mutable borrow occurs here
11 |     println!("{}", r);
   |                    - immutable borrow later used here
   |
   = help: consider using a `Cell` or `RefCell` for interior mutability
```

Decoded:

| Part                     | Meaning                                                    |
|--------------------------|------------------------------------------------------------|
| `error[E0502]`           | Error level + unique E-code                                |
| `: cannot borrow...`     | Human-readable summary of the problem                      |
| `--> src/main.rs:10:5`   | File, line, column of the primary span                     |
| `|` lines                | Source code context window                                 |
| `----` underline         | Secondary span — where the immutable borrow starts         |
| `^^^^` underline         | Primary span — where the conflicting action occurs         |
| `note:` lines            | Additional context explaining the rule                     |
| `help:` / `= help:`      | Suggestion for fixing (sometimes machine-applicable)       |

### Multi-File Errors

When an error spans multiple files (trait impls, macros):

```
error[E0277]: the trait bound `MyType: Display` is not satisfied
  --> src/main.rs:15:20
   |
15 |     println!("{}", val);
   |                    ^^^ `MyType` cannot be formatted with the default formatter
   |
  ::: src/types.rs:5:1
   |
5  | pub struct MyType { ... }
   |                         - note: `MyType` defined here
```

The `:::` notation indicates a different file being referenced.

### Suggestion Applicability

When `rustc` offers a machine-applicable fix:

```
help: consider borrowing here
   |
10 |     process(&data);
   |             +
```

You can apply all suggestions automatically:

```bash
rustfix --edition 2021   # Apply compiler suggestions
cargo fix                # Apply suggestions via Cargo
cargo fix --allow-dirty  # Apply even if git tree is dirty
```

`rustfix` reads the JSON diagnostic stream and applies `suggested_replacement` spans. This is how edition migrations work automatically.

---

## 6. The Error Code Index (E-codes)

### Overview

Every hard error has an `E` followed by a 4-digit code. The full list is at:
- `rustc --explain E0382` — inline explanation
- https://doc.rust-lang.org/error_codes/

### How to Use `rustc --explain`

```bash
rustc --explain E0502
```

This outputs the full explanation with examples of correct and incorrect code. This is the fastest way to understand an unfamiliar error deeply.

### Critical E-codes Every Expert Must Know

#### Ownership and Borrowing

| Code  | Meaning                                             |
|-------|-----------------------------------------------------|
| E0382 | Use of moved value                                  |
| E0383 | Use of partially moved value                        |
| E0384 | Reassignment of immutable variable                  |
| E0385 | Assignment to immutable field                       |
| E0386 | Assignment to immutable dereference                 |
| E0387 | Captured variable in closure mutated illegally      |
| E0389 | Cannot assign to immutable field of non-mut binding |
| E0499 | Cannot borrow as mutable more than once             |
| E0500 | Closure borrows variable already borrowed           |
| E0501 | Cannot borrow because previous borrow holds ref     |
| E0502 | Cannot borrow as mutable (also borrowed immutably)  |
| E0503 | Cannot use because it was borrowed                  |
| E0504 | Cannot move into closure (borrow in outer scope)    |
| E0505 | Cannot move out of value because borrowed           |
| E0506 | Cannot assign to value because borrowed             |
| E0507 | Cannot move out of dereference                      |
| E0508 | Cannot move out of array index                      |
| E0509 | Cannot move out of value which implements Drop      |
| E0510 | Cannot use moved value in pattern guard             |
| E0515 | Cannot return reference to local data               |
| E0516 | `typeof` not implemented                            |
| E0517 | `repr` attribute placement invalid                  |
| E0521 | Borrowed data escapes outside of closure            |
| E0524 | Two closures require unique access to same variable |
| E0525 | Expected a closure that implements Fn, got FnOnce   |
| E0529 | Expected array or slice, found else                 |

#### Lifetimes

| Code  | Meaning                                              |
|-------|------------------------------------------------------|
| E0106 | Missing lifetime specifier                           |
| E0107 | Wrong number of lifetime parameters                  |
| E0261 | Use of undeclared lifetime name                      |
| E0262 | Illegal lifetime parameter name                      |
| E0263 | Lifetime parameter shadows another                   |
| E0264 | Unknown extern lang item                             |
| E0309 | Type may not live long enough                        |
| E0310 | Type may not live long enough (static)               |
| E0311 | Type may not live long enough (explicit)             |
| E0312 | Lifetime of reference outlives scope                 |
| E0477 | Lifetime must outlive `'static`                      |
| E0478 | Lifetime bound not satisfied                         |
| E0491 | Reference has a longer lifetime than data            |
| E0495 | Cannot infer appropriate lifetime                    |
| E0496 | Lifetime name `'a` shadows another                   |
| E0597 | Borrowed value does not live long enough             |
| E0623 | Lifetime mismatch                                    |

#### Types and Traits

| Code  | Meaning                                              |
|-------|------------------------------------------------------|
| E0004 | Non-exhaustive patterns                              |
| E0023 | Wrong number of fields in pattern                    |
| E0054 | Cannot cast to type                                  |
| E0055 | Infinite recursion in cast                           |
| E0060 | Wrong number of arguments                            |
| E0061 | Wrong number of arguments (function call)            |
| E0080 | Const evaluation error                               |
| E0116 | Can't impl for type defined outside crate            |
| E0117 | Orphan rule violation                                |
| E0119 | Conflicting trait implementations                    |
| E0120 | Drop impl must use only type's own generics          |
| E0121 | Placeholder `_` not allowed in type signature        |
| E0124 | Duplicate field in struct                            |
| E0185 | Trait method impl has incompatible type              |
| E0191 | Trait object must have one non-auto trait            |
| E0225 | Only auto traits may be used as additional bounds    |
| E0277 | Trait bound not satisfied                            |
| E0282 | Type annotations needed                              |
| E0283 | Type ambiguous (multiple impl candidates)            |
| E0308 | Mismatched types                                     |
| E0364 | Bindings cannot shadow glob imports                  |
| E0401 | Can't use type parameter from outer function         |
| E0403 | Same type parameter name used twice                  |
| E0404 | Not a trait                                          |
| E0405 | Use of trait which is not in scope                   |
| E0407 | Method not part of trait                             |
| E0412 | Cannot find type in scope                            |
| E0413 | Declaration shadows existing binding                 |
| E0416 | Identifier bound more than once in pattern           |
| E0422 | Cannot find struct/variant in scope                  |
| E0423 | Function not found (expected fn, tuple struct...)    |
| E0425 | Cannot find value in scope                           |
| E0428 | Duplicate definition                                 |
| E0432 | Unresolved import                                    |
| E0433 | Failed to resolve                                    |
| E0435 | Attempt to use a non-constant as a constant          |
| E0436 | Functional record update on non-struct               |
| E0437 | Type not a member of trait                           |
| E0438 | Const not a member of trait                          |
| E0439 | Invalid `simd_shuffle` index                         |
| E0445 | Private trait in public interface                    |
| E0446 | Private type in public interface                     |

---

## 7. Borrow Checker Errors — Deep Mastery

### What the Borrow Checker Does

The borrow checker (formally: NLL — Non-Lexical Lifetimes, implemented in `rustc_borrowck`) enforces:

1. **At any time, for any value, there is either:**
   - One mutable reference (`&mut T`), OR
   - Any number of immutable references (`&T`)
   - NEVER both simultaneously

2. **A reference must not outlive the value it refers to.**

3. **You cannot use a moved value.**

These rules eliminate data races, use-after-free, and dangling pointers at compile time.

### NLL — Non-Lexical Lifetimes

Before NLL (Rust ≤1.30), lifetimes were lexical — they lasted for the entire block scope. NLL (Rust ≥2018 edition) computes lifetimes as the actual "region" of code where a reference is used, not just where it's declared.

```rust
// With lexical lifetimes (old, rejected):
let mut v = vec![1, 2, 3];
let r = &v[0];           // immutable borrow starts
println!("{}", r);       // r used here
v.push(4);               // ERROR: v is still "borrowed" till end of block

// With NLL (accepted):
let mut v = vec![1, 2, 3];
let r = &v[0];
println!("{}", r);       // last use of r — borrow ends HERE
v.push(4);               // OK: no active borrow
```

NLL uses liveness analysis: a borrow is active only while the borrowed reference is live (may be used).

### Borrow Check Errors in Depth

#### E0502 — Mutable + Immutable Borrow Simultaneously

```rust
fn main() {
    let mut v = vec![1, 2, 3];
    let first = &v[0];        // immutable borrow
    v.push(4);                // ERROR: mutable borrow (push needs &mut v)
    println!("{}", first);    // first used after push — so borrow overlaps
}
```

**Why**: `Vec::push` may reallocate, invalidating `first`. The compiler prevents this.

**Fix 1**: Clone first.
```rust
let first = v[0];  // copy the value, not a reference
v.push(4);
println!("{}", first);
```

**Fix 2**: Drop the borrow before mutating.
```rust
let first_val = v[0];  // copy
v.push(4);
println!("{}", first_val);
```

**Fix 3**: Use `RefCell<T>` for interior mutability.
```rust
use std::cell::RefCell;
let v = RefCell::new(vec![1, 2, 3]);
let first = v.borrow()[0];
v.borrow_mut().push(4);
println!("{}", first);
```

#### E0499 — Multiple Mutable Borrows

```rust
fn main() {
    let mut s = String::new();
    let r1 = &mut s;
    let r2 = &mut s;  // ERROR: second mutable borrow
    println!("{} {}", r1, r2);
}
```

**Why**: Two simultaneous mutable references allow aliased mutation — undefined behavior.

**Fix**: Use them sequentially.
```rust
let r1 = &mut s;
r1.push('a');
// r1 no longer used
let r2 = &mut s;
r2.push('b');
```

#### E0597 — Borrowed Value Does Not Live Long Enough

```rust
fn main() {
    let r;
    {
        let x = 5;
        r = &x;  // ERROR: x will be dropped, r would dangle
    }
    println!("{}", r);  // use-after-free prevented
}
```

**Why**: `x` is dropped at `}`, but `r` points into it. This would be a dangling pointer in C.

**Fix**: Ensure the referenced value outlives the reference.

#### E0505 — Cannot Move Because Borrowed

```rust
fn use_ref(s: &String) { println!("{}", s); }

fn main() {
    let s = String::from("hello");
    let r = &s;
    drop(s);          // ERROR: cannot move s while borrowed
    println!("{}", r);
}
```

**Fix**: Don't drop while a borrow is active. Let the borrow end first.

### Two-Phase Borrows

Two-phase borrows are a special NLL feature that allows a mutable borrow to be "reserved" before being "activated". This makes some intuitive patterns work:

```rust
// This works because of two-phase borrows:
let mut v = vec![1];
v.push(v.len());  // v.len() takes &v, then push takes &mut v
                  // Two-phase: &v is reserved, v.len() executes,
                  // then the &mut v is activated for push
```

This was a significant improvement over the old borrow checker.

### Polonius — The Next Borrow Checker

Polonius is the research project that will eventually replace the current NLL borrow checker. It uses a Datalog-based analysis and is more precise — it can accept more valid programs that NLL currently rejects.

Enable it experimentally:
```bash
RUSTFLAGS="-Z polonius" cargo +nightly build
```

Polonius fixes the classic "conditional return reference" issue:

```rust
// Rejected by NLL, accepted by Polonius:
fn get_or_insert<'a>(map: &'a mut HashMap<K, V>, key: K, val: V) -> &'a V {
    if let Some(v) = map.get(&key) {
        return v;  // NLL wrongly thinks borrow extends here
    }
    map.insert(key, val);
    map.get(&key).unwrap()
}
```

---

## 8. Lifetime Errors — Complete Reference

### What Lifetimes Are

Lifetimes are not runtime constructs. They are compile-time annotations that describe how long a reference is valid. The compiler uses them to verify that references never outlive the data they point to.

A lifetime `'a` is a region of code (a set of program points) during which a reference is valid.

### Lifetime Elision Rules

The compiler can often infer lifetimes automatically. The rules:

**Rule 1**: Each elided lifetime in input position gets a distinct lifetime.
```rust
fn foo(x: &str, y: &str) -> &str
// Desugared: fn foo<'a, 'b>(x: &'a str, y: &'b str) -> &??? str
// Ambiguous! Must be annotated explicitly.
```

**Rule 2**: If there is exactly one input lifetime, it applies to all output lifetimes.
```rust
fn foo(x: &str) -> &str
// Desugared: fn foo<'a>(x: &'a str) -> &'a str
// Clear: the output lives as long as the input.
```

**Rule 3**: If there is a `&self` or `&mut self` parameter, the lifetime of `self` is applied to all output lifetimes.
```rust
impl MyStruct {
    fn get(&self) -> &str
    // Desugared: fn get<'a>(&'a self) -> &'a str
}
```

### Common Lifetime Errors

#### E0106 — Missing Lifetime Specifier

```rust
struct Important {
    part: &str,  // ERROR: missing lifetime
}
```

**Fix**:
```rust
struct Important<'a> {
    part: &'a str,
}
```

**Why**: The struct holds a reference. The compiler needs to know how long that reference is valid to ensure the struct doesn't outlive the referenced data.

#### E0597 — Reference Doesn't Live Long Enough

```rust
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}

fn main() {
    let s1 = String::from("long string");
    let result;
    {
        let s2 = String::from("xyz");
        result = longest(s1.as_str(), s2.as_str());
        // s2 dropped here
    }
    println!("{}", result);  // ERROR: result may point to s2 which is gone
}
```

**Why**: `longest` returns a reference that lives as long as the shorter of `x` and `y`. `s2` is shorter-lived, so `result` could dangle.

#### E0495 — Cannot Infer Appropriate Lifetime

This occurs when the compiler cannot determine which lifetime to assign to an output reference because multiple input lifetimes are ambiguous.

```rust
fn choose<'a, 'b>(first: &'a str, second: &'b str, use_first: bool) -> &str {
    // ERROR: can't infer — could be 'a or 'b
    if use_first { first } else { second }
}
```

**Fix**: Constrain lifetimes to a common bound.
```rust
fn choose<'a>(first: &'a str, second: &'a str, use_first: bool) -> &'a str {
    if use_first { first } else { second }
}
// Both inputs must outlive 'a — the output is valid for 'a.
```

### Lifetime Subtyping

`'long: 'short` means `'long` outlives `'short` (i.e., `'long` is a subtype of `'short` in the sense that a longer-lived reference can be used where a shorter-lived one is expected).

```rust
fn use_both<'short, 'long: 'short>(
    short_ref: &'short str,
    long_ref: &'long str,
) -> &'short str {
    // Can return long_ref because 'long outlives 'short
    long_ref
}
```

### `'static` Lifetime

`'static` means the reference is valid for the entire duration of the program.

```rust
let s: &'static str = "hello";  // string literals are 'static
```

**Common trap**: Thread closures in `std::thread::spawn` require `'static` bounds because the thread may outlive the spawning scope.

```rust
let data = vec![1, 2, 3];
std::thread::spawn(move || {  // 'move' required to satisfy 'static
    println!("{:?}", data);
});
```

### Higher-Ranked Trait Bounds (HRTB)

`for<'a>` is used when a type must implement a trait for *every* possible lifetime:

```rust
fn apply<F>(f: F, s: &str) -> &str
where
    F: for<'a> Fn(&'a str) -> &'a str,  // works for any lifetime
{
    f(s)
}
```

This is the most advanced lifetime construct and appears frequently in trait object contexts.

### Variance

Variance determines how lifetimes in generic types relate:

- **Covariant** (`T`): `&'long T` can be used where `&'short T` is expected if `'long: 'short`. Most types.
- **Contravariant** (`fn(T)`): Opposite direction. Function arguments.
- **Invariant** (`&mut T`, `Cell<T>`): No substitution. `&mut 'long T` cannot be used where `&mut 'short T` is expected.

```rust
// &mut T is invariant in T:
fn assign<'a>(r: &mut &'a str, val: &'a str) {
    *r = val;
}

let mut s: &'static str = "hello";
let local = String::from("world");
// assign(&mut s, &local);  // ERROR: invariance prevents this
// If allowed, s would point to local after local is dropped
```

---

## 9. Type System Errors

### E0308 — Mismatched Types

The most common error. The compiler expected one type but found another.

```rust
fn add(x: i32, y: i32) -> i32 {
    x + y
}

let result: String = add(1, 2);  // ERROR: expected String, found i32
```

**Sub-cases**:
- Wrong return type
- Wrong argument type
- Coercion not applied automatically (e.g., `i32` vs `u32`)
- `()` (unit) returned when value expected

### Type Coercions

Rust has limited implicit coercions:

| Coercion              | Example                        |
|-----------------------|--------------------------------|
| Deref coercion        | `String` → `&str`              |
| Unsize coercion       | `[T; N]` → `[T]`              |
| Pointer weakening     | `&mut T` → `&T`               |
| Trait object coercion | `Box<Concrete>` → `Box<dyn T>`|
| Function pointer      | `fn foo` → `fn() -> ()`       |

These are automatic. But `i32` to `u32` is NOT automatic — use `as`.

### E0282 — Type Annotations Needed

```rust
let v = Vec::new();  // ERROR: can't infer element type
v.push(1i32);        // too late — v already needed to be typed
```

**Fix**:
```rust
let mut v: Vec<i32> = Vec::new();
// or
let mut v = Vec::<i32>::new();
// or
let mut v = vec![1i32];  // inferred from first element
```

### E0283 — Type Is Ambiguous

```rust
trait Convert {
    fn convert() -> Self;
}

impl Convert for i32 { fn convert() -> i32 { 0 } }
impl Convert for u32 { fn convert() -> u32 { 0 } }

let x = Convert::convert();  // ERROR: ambiguous — which impl?
```

**Fix**:
```rust
let x = i32::convert();  // explicitly choose the impl
// or
let x: i32 = Convert::convert();  // type annotation disambiguates
```

### Turbofish Syntax

When type inference fails, turbofish (`::<>`) specifies type parameters explicitly:

```rust
let parsed = "42".parse::<i32>().unwrap();
let v = Vec::<String>::with_capacity(10);
let result = std::mem::size_of::<u64>();
```

This is essential when calling generic functions where inference cannot determine the type.

### `!` (Never Type)

The never type `!` represents computations that never complete (panics, infinite loops, `return`, `continue`, `break`).

```rust
fn diverges() -> ! {
    panic!("never returns");
}

let x: i32 = if condition {
    42
} else {
    panic!("oops")  // returns !, which coerces to any type
};
```

`!` is a subtype of every type, allowing it to appear in any branch.

---

## 10. Trait and Impl Errors

### E0277 — Trait Bound Not Satisfied

The most pervasive non-trivial error. A type doesn't implement a required trait.

```rust
fn print<T: Display>(val: T) {
    println!("{}", val);
}

struct MyStruct;
print(MyStruct);  // ERROR: MyStruct doesn't implement Display
```

**Fix**: Implement the trait.
```rust
use std::fmt;
impl fmt::Display for MyStruct {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "MyStruct")
    }
}
```

### E0117 — Orphan Rule

You cannot implement a trait for a type if both the trait and the type are defined outside your crate.

```rust
// In your crate:
impl Display for Vec<i32> { ... }
// ERROR: Display is from std, Vec<i32> is from std
// Both are foreign — orphan rule violation
```

**Fix**: Newtype pattern.
```rust
struct MyVec(Vec<i32>);
impl Display for MyVec { ... }  // OK: MyVec is yours
```

### E0119 — Conflicting Implementations

```rust
trait Foo {}
impl<T: Bar> Foo for T {}  // blanket impl for all T: Bar
impl Foo for MyType {}     // ERROR: MyType may implement Bar
                           // creating an overlap
```

**Fix**: Use specialization (nightly only) or restructure trait hierarchy.

### Object Safety

For a trait to be used as `dyn Trait`, it must be object-safe:

- No generic methods (unless with type-erased constraints)
- No methods that return `Self`
- No associated functions without `where Self: Sized`

```rust
trait NotObjectSafe {
    fn clone(&self) -> Self;  // returns Self — not object safe
}

// dyn NotObjectSafe  // ERROR: trait is not object-safe
```

**Fix**: Use `where Self: Sized` to exclude non-object-safe methods:
```rust
trait MadeObjectSafe {
    fn clone(&self) -> Self where Self: Sized;
    fn describe(&self) -> String;  // object-safe method
}
```

### Auto-Traits

`Send`, `Sync`, `Unpin` are auto-traits — automatically implemented when all fields satisfy the trait.

```rust
struct SafeStruct {
    data: Vec<i32>,  // Vec<i32>: Send + Sync
}
// SafeStruct: Send + Sync automatically

struct UnsafeStruct {
    ptr: *mut i32,  // raw pointer: not Send
}
// UnsafeStruct: !Send, !Sync automatically
```

When you get `E0277: the trait bound T: Send is not satisfied`, it usually means a type contains a non-Send field (raw pointer, `Rc`, `Cell` across threads).

---

## 11. Ownership and Move Errors

### Ownership Rules (First Principles)

1. Every value has exactly one owner.
2. When the owner goes out of scope, the value is dropped (freed).
3. Ownership can be transferred (moved) but not shared directly.

### E0382 — Use of Moved Value

```rust
let s = String::from("hello");
let t = s;           // s is moved into t
println!("{}", s);   // ERROR: s was moved
```

**Why**: `String` is not `Copy`. Moving transfers ownership.

**Fix options**:
```rust
// 1. Clone
let t = s.clone();
println!("{}", s);  // s still valid

// 2. Borrow instead of move
let t = &s;
println!("{}", s);  // s still valid

// 3. Use before moving
println!("{}", s);
let t = s;  // move after last use
```

### Copy vs Clone vs Move

| Behavior | Types             | What happens                              |
|----------|-------------------|-------------------------------------------|
| Copy     | `i32`, `u8`, `f64`, `bool`, `char`, `[T; N] where T: Copy`, tuples of Copy types | Bitwise copy; original still valid |
| Clone    | `String`, `Vec`, `Box` | Deep copy via `.clone()`; explicit |
| Move     | Any non-Copy type | Ownership transferred; original invalidated |

### Partial Moves

```rust
struct Pair {
    first: String,
    second: String,
}

let p = Pair { first: "a".into(), second: "b".into() };
let f = p.first;  // moves p.first
println!("{}", p.second);   // OK: p.second not moved
println!("{:?}", p);        // ERROR: p partially moved (p.first gone)
```

This is `E0382` / `E0383`. You cannot use `p` as a whole after partial move, but you can access unmoved fields.

### `mem::replace` and `mem::take`

These are the canonical tools for moving out of a struct field you have `&mut` to:

```rust
use std::mem;

struct Node {
    value: String,
    next: Option<Box<Node>>,
}

fn take_next(node: &mut Node) -> Option<Box<Node>> {
    mem::take(&mut node.next)  // replaces next with None, returns old value
}
```

---

## 12. Mutability Errors

### E0384 — Reassignment of Immutable Variable

```rust
let x = 5;
x = 6;  // ERROR
```

**Fix**: `let mut x = 5;`

### Interior Mutability Pattern

When you need to mutate through a shared reference:

| Type          | Thread-safe? | Use case                             |
|---------------|-------------|--------------------------------------|
| `Cell<T>`     | No          | `Copy` types, single-threaded        |
| `RefCell<T>`  | No          | Non-Copy, runtime borrow checking    |
| `Mutex<T>`    | Yes         | Multi-threaded, blocking             |
| `RwLock<T>`   | Yes         | Multi-reader, single-writer          |
| `Atomic*`     | Yes         | Primitive types, lock-free           |

```rust
use std::cell::RefCell;

struct Cache {
    data: RefCell<Option<String>>,
}

impl Cache {
    fn get(&self) -> String {
        // &self is immutable, but RefCell allows interior mutation
        let mut d = self.data.borrow_mut();
        if d.is_none() {
            *d = Some(expensive_compute());
        }
        d.clone().unwrap()
    }
}
```

`RefCell` enforces borrow rules at runtime. Violating them panics instead of failing to compile.

---

## 13. Pattern Matching and Exhaustiveness Errors

### E0004 — Non-Exhaustive Patterns

```rust
enum Direction { North, South, East, West }

fn describe(d: Direction) -> &'static str {
    match d {
        Direction::North => "up",
        Direction::South => "down",
        // ERROR: East and West not covered
    }
}
```

**Fix**: Cover all cases or use `_`:
```rust
match d {
    Direction::North => "up",
    Direction::South => "down",
    Direction::East | Direction::West => "sideways",
}
// or
    _ => "other",  // wildcard
```

### `#[non_exhaustive]`

This attribute on an enum or struct signals that future variants/fields may be added:

```rust
#[non_exhaustive]
pub enum Error {
    NotFound,
    PermissionDenied,
}
```

External crates must use `_` in match arms because new variants may appear:
```rust
match err {
    Error::NotFound => ...,
    Error::PermissionDenied => ...,
    _ => ...,  // required for #[non_exhaustive] enums from other crates
}
```

### Or-Patterns

```rust
match x {
    1 | 2 | 3 => "small",  // or-pattern
    4..=10 => "medium",     // range pattern
    _ => "large",
}
```

### Binding Modes (`ref`, `ref mut`)

```rust
let s = String::from("hello");

// Without ref: moves the value
match s {
    x => println!("{}", x),  // x owns the String
}
// s is moved

// With ref: borrows the value
let s = String::from("hello");
match s {
    ref x => println!("{}", x),  // x is &String
}
// s is still valid
```

Modern Rust with match ergonomics often infers `ref` automatically when you match `&T`.

---

## 14. Macro Expansion Errors

### How Macros Work

Macros operate at the token level before type checking. They have their own error modes:

#### Declarative Macros (`macro_rules!`)

```rust
macro_rules! add {
    ($a:expr, $b:expr) => { $a + $b };
}

add!(1, 2, 3);  // ERROR: no rule matches 3 arguments
```

The error points to the macro invocation but the cause is the rule mismatch. Use `--edition 2021` and `RUST_LOG=rustc_expand=debug` to trace expansion.

#### Hygiene

Rust macros are hygienic — names introduced inside a macro don't leak into the calling scope and vice versa:

```rust
macro_rules! make_x {
    () => { let x = 42; }
}

make_x!();
println!("{}", x);  // ERROR: x not in scope (hygienic)
```

To deliberately export a name from a macro, use `$crate::` or `#[macro_export]` appropriately.

#### Tracing Macro Expansion

```bash
# Expand macros and print the result
cargo rustc -- -Z macro-backtrace
rustc -Z unpretty=expanded main.rs

# Via cargo-expand (most useful):
cargo install cargo-expand
cargo expand                    # expand entire crate
cargo expand main               # expand specific module
cargo expand --lib              # expand lib.rs
```

`cargo-expand` is the primary tool for debugging macro output. It shows you the actual code after expansion.

#### Proc Macro Errors

Proc macros run as Rust code at compile time. Errors can come from:

1. **Compile-time panic** in the proc macro itself
2. **Invalid token stream** generated by the macro
3. **Downstream type errors** in the expanded code

```rust
use proc_macro::TokenStream;

#[proc_macro_derive(MyTrait)]
pub fn my_derive(input: TokenStream) -> TokenStream {
    // If this panics, rustc shows:
    // error: proc macro panicked
    panic!("not implemented");
}
```

Use `syn` and `quote` crates for robust proc macro implementations.

---

## 15. Unsafe Code Errors and UB

### What `unsafe` Unlocks

`unsafe` blocks/functions/traits/impls allow:

1. Dereferencing raw pointers
2. Calling `unsafe` functions (including FFI)
3. Accessing mutable statics
4. Implementing `unsafe` traits
5. Accessing union fields

The compiler does NOT check safety invariants inside `unsafe` — that is your responsibility.

### Undefined Behavior in Rust

The following are UB and may be miscompiled:

| UB Category                    | Example                                         |
|--------------------------------|-------------------------------------------------|
| Dereferencing null/dangling ptr | `*ptr` where ptr is null/freed                  |
| Data race                      | Concurrent unsynchronized access to shared data |
| Misaligned pointer access      | Reading `u32` from a misaligned address         |
| Invalid bit patterns           | `bool` with value 2, `char` with invalid scalar |
| Aliasing `&mut T`              | Having two `&mut T` to same location            |
| Uninitialized memory read      | Reading from `MaybeUninit` before init          |
| Integer overflow (in unsafe)   | `u8::MAX + 1` in release mode wraps (not UB in Rust, but panic in debug) |
| Break contract of `unsafe` trait | Implementing `Send` for non-Send type          |

### Tools for Finding UB

```bash
# Miri: UB detector and interpreter for MIR
rustup component add miri
cargo miri test          # run tests under Miri
cargo miri run           # run binary under Miri

# AddressSanitizer
RUSTFLAGS="-Z sanitizer=address" cargo +nightly test --target x86_64-unknown-linux-gnu

# MemorySanitizer (uninitialized reads)
RUSTFLAGS="-Z sanitizer=memory" cargo +nightly test --target x86_64-unknown-linux-gnu

# ThreadSanitizer (data races)
RUSTFLAGS="-Z sanitizer=thread" cargo +nightly test --target x86_64-unknown-linux-gnu

# UndefinedBehaviorSanitizer
RUSTFLAGS="-Z sanitizer=undefined" cargo +nightly test --target x86_64-unknown-linux-gnu
```

### `MaybeUninit` — Safe Uninitialized Memory

```rust
use std::mem::MaybeUninit;

let mut x: MaybeUninit<i32> = MaybeUninit::uninit();
x.write(42);  // initialize
let val = unsafe { x.assume_init() };  // safe to read now
```

Never use `std::mem::uninitialized()` — it's deprecated and causes immediate UB for non-trivially-initialized types.

### `unsafe` Trait Contracts

```rust
unsafe trait SafeToSend {
    // Implementors MUST uphold: this type is safe to transfer across threads
}

// Implementing an unsafe trait is an assertion to the compiler:
unsafe impl SafeToSend for MyType {}
```

The compiler trusts you. If you lie, UB follows.

---

## 16. Closures and Capture Errors

### Capture Modes

Closures capture variables from their environment in three ways:

| Mode           | Keyword     | Effect                                |
|----------------|------------|---------------------------------------|
| By reference   | (default)  | Borrow the variable                   |
| By mutable ref | (inferred) | Mutable borrow the variable           |
| By move        | `move`     | Take ownership of the variable        |

The compiler infers the most restrictive capture needed.

### Fn, FnMut, FnOnce

| Trait   | Can call | Captures                                            |
|---------|----------|-----------------------------------------------------|
| `FnOnce`| Once     | May move captured values out                        |
| `FnMut` | Many     | May mutate captured values, but doesn't consume     |
| `Fn`    | Many     | Only shared access to captures (read-only or Copy)  |

`Fn: FnMut: FnOnce` — every `Fn` is also `FnMut` and `FnOnce`.

```rust
// FnOnce: consumes a captured String
let s = String::from("hello");
let consume = move || { drop(s); };
consume();   // OK
consume();   // ERROR: FnOnce can only be called once — s already dropped

// FnMut: mutates a captured counter
let mut count = 0;
let mut increment = || { count += 1; };
increment();
increment();  // OK: FnMut can be called multiple times

// Fn: only reads
let x = 10;
let read = || x + 1;
read();
read();  // OK: Fn
```

### E0525 — Expected Fn, Got FnOnce

```rust
fn apply_twice<F: Fn()>(f: F) {
    f();
    f();
}

let s = String::from("hello");
apply_twice(move || drop(s));
// ERROR: closure is FnOnce (moves s) but F must be Fn
```

**Fix**: Make the closure not consume the value, or use `FnOnce` bound if called once.

### Closure Lifetime Issues

```rust
fn make_adder(x: &i32) -> impl Fn() -> i32 {
    || *x  // ERROR: closure captures 'x' by reference,
           // but returned closure must be 'static
}
```

**Fix**: Move the value into the closure.
```rust
fn make_adder(x: i32) -> impl Fn() -> i32 {
    move || x  // x is Copy, so this works
}
```

---

## 17. Async/Await Errors

### How Async Works Under the Hood

`async fn` desugars to a state machine implementing `Future<Output = T>`. The state machine captures all local variables that live across `.await` points as struct fields. This has important implications:

```rust
// This:
async fn foo() -> i32 {
    let x = bar().await;
    x + 1
}

// Roughly becomes:
enum FooFuture {
    State0,
    State1 { x_future: BarFuture },
    State2 { x: i32 },
}

impl Future for FooFuture {
    type Output = i32;
    fn poll(self: Pin<&mut Self>, cx: &mut Context) -> Poll<i32> { ... }
}
```

### `Send` Bounds in Async

`async fn` futures are `Send` only if all state captured across `.await` is `Send`.

```rust
async fn bad() {
    let rc = Rc::new(5);       // Rc is not Send
    some_async_fn().await;     // Rc must live across this point
    println!("{}", rc);        // Rc used after await
    // ERROR: future is not Send because Rc is held across await
}
```

**Fix**: Drop non-Send values before `.await`:
```rust
async fn good() {
    let value = {
        let rc = Rc::new(5);
        *rc  // copy the value out
    };  // rc dropped here
    some_async_fn().await;
    println!("{}", value);  // value is i32: Send
}
```

### `Pin` and `Unpin`

`Pin<P>` is a pointer wrapper that guarantees the pointee will not be moved in memory. This is required for self-referential structures (like async state machines that may hold pointers to their own fields).

```rust
// You cannot move a pinned value:
let mut x = Box::pin(5i32);
let _moved = *x;  // OK: i32 is Copy
// std::mem::swap(&mut x, &mut y);  // ERROR if x is !Unpin
```

Most types are `Unpin` (safe to move even when pinned). `async fn` futures are `!Unpin` because they may be self-referential.

### E0277 in Async Context

The most common async error pattern:

```
error[E0277]: `*mut ()` cannot be sent between threads safely
   the trait `Send` is not implemented for `*mut ()`
```

This usually means a `MutexGuard`, `Rc`, or raw pointer is held across an `.await`.

### `async` in Traits (Nightly / AFIT)

Async functions in traits are now stable in Rust 1.75+:

```rust
trait AsyncReader {
    async fn read(&mut self) -> Vec<u8>;
}
```

But they are not object-safe by default. Use the `async-trait` crate for object safety:

```rust
#[async_trait::async_trait]
trait AsyncReader {
    async fn read(&mut self) -> Vec<u8>;
}
```

---

## 18. Generic and Associated Type Errors

### Type Aliases in Traits (TAITs)

```rust
trait Container {
    type Item;
    fn get(&self) -> &Self::Item;
}

struct Wrapper<T> {
    inner: T,
}

impl<T> Container for Wrapper<T> {
    type Item = T;
    fn get(&self) -> &T { &self.inner }
}
```

### Where Clauses vs Inline Bounds

Both are equivalent but `where` is preferred for readability:

```rust
// Inline:
fn process<T: Clone + Send + Sync>(val: T) { }

// Where clause (preferred for complex bounds):
fn process<T>(val: T)
where
    T: Clone + Send + Sync,
    T::Output: Display,
{ }
```

### E0207 — Unconstrained Type Parameter

```rust
impl<T> MyTrait for MyType {
    type Output = T;  // ERROR: T is not constrained by self type
}
```

Every type parameter in an `impl` must be constrained by the implementing type.

### Blanket Implementations

```rust
impl<T: Display> ToString for T {
    fn to_string(&self) -> String {
        format!("{}", self)
    }
}
```

This implements `ToString` for every `T` that is `Display`. This is how the standard library works. Conflicts arise when you try to implement a trait where a blanket impl may apply.

### Negative Impls (Nightly)

```rust
#![feature(negative_impls)]

struct NotSync;
impl !Sync for NotSync {}  // explicitly opt out of Sync
```

---

## 19. Const and Static Errors

### `const` vs `static`

| Feature       | `const`                          | `static`                         |
|---------------|----------------------------------|----------------------------------|
| Inlined       | Yes, at use site                 | No, single location in memory    |
| Has address   | Not guaranteed                   | Yes, fixed address               |
| Mutable       | No                               | Yes (`static mut`, unsafe)       |
| Lifetime      | `'static`                        | `'static`                        |
| Destructors   | No (value is Copy or forgotten)  | Yes (Drop called at shutdown)    |

### E0080 — Const Evaluation Error

```rust
const DIVISOR: i32 = 0;
const RESULT: i32 = 10 / DIVISOR;  // ERROR: attempt to divide by zero at compile time
```

Const eval is a safe interpreter that runs Rust code at compile time. It rejects:
- Division by zero
- Overflow (in debug mode)
- Out-of-bounds array access
- Calling non-const functions

### `const fn`

Functions eligible for const evaluation:

```rust
const fn factorial(n: u64) -> u64 {
    if n <= 1 { 1 } else { n * factorial(n - 1) }
}

const FACT_10: u64 = factorial(10);  // computed at compile time
```

Restrictions on `const fn`:
- No heap allocation (unless `const` allocator is used, nightly)
- No floating-point operations (partially lifted)
- No trait objects
- No raw pointer dereference (unless `const unsafe fn`)

### `static mut` — The Danger Zone

```rust
static mut COUNTER: u32 = 0;

unsafe fn increment() {
    COUNTER += 1;  // data race if called from multiple threads
}
```

Accessing `static mut` requires `unsafe`. Prefer `Mutex<T>` or `AtomicU32`.

---

## 20. Lint System — Complete Reference

### What Lints Are

Lints are named checks that run after type checking, analyzing code for suspicious patterns. They are not hard errors by default but can be configured.

### Lint Levels

| Level    | Meaning                                              |
|----------|------------------------------------------------------|
| `allow`  | Suppress the lint entirely                           |
| `warn`   | Emit a warning (default for most lints)              |
| `deny`   | Treat the lint as a hard error                       |
| `forbid` | Like `deny` but cannot be downgraded even with `allow`|

### Built-in Lint Categories

```bash
rustc -W help             # list all lints with descriptions
rustc --print lints       # (some versions)
```

#### Key Lint Groups

| Group          | Contains                                             |
|----------------|------------------------------------------------------|
| `warnings`     | All current warning-level lints                      |
| `unused`       | All unused-* lints                                   |
| `rust-2018-idioms` | Preferred idioms for Rust 2018 edition           |
| `rust-2021-compatibility` | Breaking changes for 2021 edition          |
| `nonstandard-style` | Naming convention violations                   |
| `deprecated`   | Use of deprecated items                              |
| `future-incompatible` | Code that may break in future versions       |

#### Detailed Lint Reference

**Unused Lints**:

| Lint                    | What it detects                              |
|-------------------------|----------------------------------------------|
| `dead_code`             | Functions, structs, enums never used         |
| `unused_variables`      | Local variable never read                    |
| `unused_imports`        | `use` items that import nothing used         |
| `unused_mut`            | `mut` binding never mutated                  |
| `unused_assignments`    | Assignment whose value is never read         |
| `unused_must_use`       | `#[must_use]` result not used               |
| `unused_parens`         | Unnecessary parentheses                      |
| `unused_braces`         | Unnecessary braces                           |

**Style Lints**:

| Lint                         | What it detects                           |
|------------------------------|-------------------------------------------|
| `non_snake_case`             | Non-snake_case function/variable names    |
| `non_camel_case_types`       | Non-CamelCase type names                  |
| `non_upper_case_globals`     | Non-UPPER_CASE constants/statics          |
| `improper_ctypes`            | FFI types that may not be ABI-compatible  |
| `improper_ctypes_definitions`| Same for fn definitions                   |

**Safety Lints**:

| Lint                         | What it detects                           |
|------------------------------|-------------------------------------------|
| `unsafe_code`                | Any use of `unsafe`                       |
| `unsafe_op_in_unsafe_fn`     | Unsafe ops without explicit unsafe block  |
| `deprecated`                 | Deprecated item usage                     |
| `missing_safety_doc`         | `unsafe` function without `# Safety` docs |
| `missing_docs`               | Public items without documentation        |

**Correctness Lints**:

| Lint                         | What it detects                           |
|------------------------------|-------------------------------------------|
| `unreachable_code`           | Code after `return`, `panic!`, etc.       |
| `unreachable_patterns`       | Match arms that can never match           |
| `redundant_semicolons`       | Extra semicolons                          |
| `renamed_and_removed_lints`  | Using lints by old/removed names          |
| `invalid_from_utf8`          | `from_utf8` called with invalid literal   |
| `invalid_nan_comparisons`    | `x == f64::NAN` (always false)            |
| `ambiguous_glob_reexports`   | Two globs export same name                |
| `byte_slice_in_slice_pat`    | `b"..."` in slice pattern (may not work)  |

---

## 21. Clippy — Elite Usage

### What Clippy Is

Clippy is the official Rust linter with 700+ lint checks beyond what `rustc` does. It runs as a compiler plugin.

```bash
rustup component add clippy
cargo clippy                      # run clippy on crate
cargo clippy -- -D warnings       # fail on any warning
cargo clippy --all-targets        # include tests, examples, benchmarks
cargo clippy --fix                # auto-fix fixable lints
cargo clippy -- -W clippy::all    # enable all clippy lints
cargo clippy -- -W clippy::pedantic  # pedantic (opinionated) lints
cargo clippy -- -W clippy::nursery   # experimental lints
cargo clippy -- -W clippy::restriction  # overly strict (security-useful)
```

### Clippy Lint Categories

| Category       | Count | Description                                     |
|----------------|-------|-------------------------------------------------|
| `correctness`  | ~70   | Always bugs; `deny` by default in clippy        |
| `style`        | ~100  | Code style improvements                         |
| `complexity`   | ~80   | Simplification opportunities                    |
| `perf`         | ~50   | Performance improvements                        |
| `pedantic`     | ~150  | Opinionated, strict correctness                 |
| `nursery`      | ~60   | Experimental, may be noisy                      |
| `restriction`  | ~100  | Deliberate restrictions for certain codebases   |
| `suspicious`   | ~50   | Likely bugs or surprising behavior              |
| `cargo`        | ~10   | Cargo.toml quality checks                       |

### Critical Clippy Lints for Systems/Security Code

```toml
# In clippy.toml or as flags:

# Security-relevant:
clippy::unwrap_used           # ban .unwrap() in production code
clippy::expect_used           # ban .expect() in production code
clippy::panic                 # ban panic! macro
clippy::unimplemented         # ban unimplemented!
clippy::todo                  # ban todo!
clippy::unreachable           # ban unreachable!
clippy::indexing_slicing      # ban direct indexing (use .get())
clippy::integer_arithmetic    # ban unchecked arithmetic
clippy::checked_conversions   # suggest checked numeric conversions
clippy::cast_possible_truncation  # warn on truncating casts
clippy::cast_possible_wrap    # warn on wrapping casts
clippy::cast_sign_loss        # warn on sign-losing casts

# Memory safety relevant:
clippy::mem_forget            # warn on mem::forget (may leak)
clippy::get_unwrap            # ban .get(..).unwrap()
clippy::missing_safety_doc    # require Safety docs on unsafe fn
clippy::undocumented_unsafe_blocks  # require SAFETY comments

# Systems code quality:
clippy::must_use_candidate    # suggest #[must_use] on appropriate fn
clippy::missing_errors_doc    # document errors in fn docs
clippy::missing_panics_doc    # document panics in fn docs
```

### Clippy Configuration

Create `clippy.toml` in project root:

```toml
# clippy.toml
avoid-breaking-exported-api = false
cognitive-complexity-threshold = 10
disallowed-types = [
    { path = "std::sync::Mutex", reason = "use parking_lot::Mutex instead" },
]
disallowed-methods = [
    { path = "std::process::exit", reason = "use proper error propagation" },
]
msrv = "1.70"
```

### Per-Item Clippy Suppression

```rust
#[allow(clippy::too_many_arguments)]
fn complex_function(a: i32, b: i32, c: i32, d: i32, e: i32, f: i32, g: i32) { }

#[allow(clippy::unwrap_used)]  // justified: this invariant is checked above
fn get_cached(&self, key: &str) -> &Value {
    self.cache.get(key).unwrap()
}
```

Always add a comment explaining WHY the lint is suppressed. Unsuppressed allows become a code review smell.

---

## 22. Compiler Flags and RUSTFLAGS

### Essential `rustc` Flags

```bash
# Optimization levels
-O              # equivalent to -C opt-level=2
-C opt-level=0  # no optimization (debug default)
-C opt-level=1  # basic optimization
-C opt-level=2  # standard optimization
-C opt-level=3  # aggressive (may be slower to compile)
-C opt-level=s  # optimize for size
-C opt-level=z  # optimize for size (aggressively)

# Debug info
-C debuginfo=0  # no debug info
-C debuginfo=1  # line tables only
-C debuginfo=2  # full debug info (default for debug profile)

# Code generation
-C target-cpu=native          # optimize for current CPU
-C target-feature=+avx2       # enable AVX2 instructions
-C link-arg=-fuse-ld=lld      # use LLD linker
-C lto=thin                   # thin LTO (fast link-time optimization)
-C lto=fat                    # full LTO (slow, best optimization)
-C codegen-units=1            # single codegen unit (better optimization)
-C panic=abort                # panic = abort (no unwinding, smaller binary)

# Diagnostics
--error-format=json           # JSON diagnostic output
--json=diagnostic-rendered-ansi  # ANSI in JSON
-Z macro-backtrace            # show macro expansion trace
-Z print-type-sizes           # show sizes of all types
-Z time-passes                # time each compiler pass
-Z unpretty=hir               # dump HIR
-Z unpretty=mir               # dump MIR
-Z unpretty=mir-cfg           # dump MIR control flow graph
-Z unpretty=expanded          # dump macro-expanded AST

# Nightly-only
-Z polonius                   # use Polonius borrow checker
-Z sanitizer=address          # AddressSanitizer
-Z sanitizer=memory           # MemorySanitizer
-Z sanitizer=thread           # ThreadSanitizer
-Z sanitizer=undefined        # UBSan
-Z instrument-coverage        # coverage instrumentation (LLVM)
```

### RUSTFLAGS

`RUSTFLAGS` applies flags to all crates being compiled:

```bash
# In shell:
RUSTFLAGS="-C target-cpu=native -C opt-level=3" cargo build --release

# In .cargo/config.toml (preferred, checked into repo):
[build]
rustflags = ["-C", "target-cpu=native"]

# Target-specific:
[target.x86_64-unknown-linux-gnu]
rustflags = ["-C", "link-arg=-fuse-ld=lld"]
```

**Warning**: `RUSTFLAGS` changes invalidate the incremental compilation cache for all dependencies. Use `[target.*].rustflags` in `.cargo/config.toml` for stable settings.

### RUSTDOCFLAGS

```bash
RUSTDOCFLAGS="--deny=rustdoc::broken_intra_doc_links" cargo doc
```

### Cargo Profiles

Profiles configure compiler flags per build type:

```toml
# Cargo.toml
[profile.dev]
opt-level = 0
debug = true
overflow-checks = true
incremental = true

[profile.release]
opt-level = 3
debug = false
lto = "thin"
codegen-units = 1
panic = "abort"
strip = "symbols"

[profile.release-with-debug]
inherits = "release"
debug = true
strip = "none"

[profile.bench]
inherits = "release"
debug = true

# Custom profile for security-sensitive builds:
[profile.hardened]
inherits = "release"
overflow-checks = true   # Keep overflow checks in release
panic = "abort"
lto = "fat"
codegen-units = 1
```

### Conditional Compilation

```rust
#[cfg(target_os = "linux")]
fn linux_only() { }

#[cfg(feature = "async")]
mod async_impl;

#[cfg(debug_assertions)]
fn debug_only_check() { }

// At build time:
cargo build --features "async,tls"
cargo build --no-default-features --features "core-only"
```

Check all conditional compilation cfg values:
```bash
rustc --print cfg                              # current target cfg
rustc --print cfg --target aarch64-unknown-linux-gnu  # cross-compile target cfg
```

---

## 23. Cargo and Compiler Integration

### Cargo's Invocation of `rustc`

Cargo is fundamentally a build orchestrator that invokes `rustc`. To see the exact commands:

```bash
cargo build -v          # verbose: shows rustc invocations
cargo build --message-format=json  # JSON build output for tooling
```

### Build Scripts (`build.rs`)

Build scripts run before compilation and can:
- Set `RUSTFLAGS` for the crate
- Emit `cargo:rustc-cfg=...` for conditional compilation
- Link native libraries
- Generate code

```rust
// build.rs
fn main() {
    // Enable a cfg flag based on environment:
    if std::env::var("ENABLE_FEATURE").is_ok() {
        println!("cargo:rustc-cfg=feature_enabled");
    }

    // Link a native library:
    println!("cargo:rustc-link-lib=static=mylib");
    println!("cargo:rustc-link-search=/usr/local/lib");

    // Rerun build.rs if these files change:
    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-env-changed=ENABLE_FEATURE");
}
```

### `cargo check` vs `cargo build`

```bash
cargo check    # type checks and borrow checks but does NOT generate code
               # ~3x faster than cargo build
               # used by rust-analyzer for IDE feedback
cargo build    # full compilation to binary
cargo test     # compiles test binary and runs it
cargo clippy   # cargo check + clippy lints
```

For CI: run `cargo clippy --all-targets -- -D warnings` then `cargo test`.

### Workspace-Wide Lints (Rust 1.74+)

```toml
# Cargo.toml (workspace root)
[workspace.lints.rust]
unsafe_code = "deny"
missing_docs = "warn"

[workspace.lints.clippy]
unwrap_used = "deny"
pedantic = "warn"

# In member crates:
[lints]
workspace = true  # inherit workspace lint settings
```

---

## 24. deny/allow/warn/forbid — Attribute System

### Scope of Lint Attributes

Lint attributes apply to the item they annotate and everything nested inside it:

```rust
// Crate-level (top of lib.rs or main.rs):
#![deny(unsafe_code)]
#![warn(missing_docs)]
#![allow(dead_code)]

// Module-level:
#[allow(unused_imports)]
mod test_helpers {
    use std::collections::HashMap;  // won't warn even if unused
}

// Function-level:
#[allow(clippy::too_many_arguments)]
fn complex(a: i32, b: i32, c: i32, d: i32, e: i32, f: i32, g: i32) { }

// Statement/expression-level:
fn foo() {
    #[allow(unused_variables)]
    let x = 5;
}
```

### `forbid` — Unbreakable Deny

`forbid` is like `deny` but cannot be downgraded to `allow` in a nested scope:

```rust
#![forbid(unsafe_code)]  // crate-level

mod inner {
    #[allow(unsafe_code)]  // ERROR: cannot allow a forbidden lint
    fn bad() {
        unsafe { }
    }
}
```

Use `forbid` for security-critical constraints that must be crate-wide.

### Suppressing Individual Warnings

```rust
fn old_api() -> i32 {
    #[allow(deprecated)]  // we know, working on migration
    legacy_function()
}
```

### `#[must_use]`

```rust
#[must_use]
fn compute() -> Result<i32, Error> { ... }

compute();  // WARNING: unused return value of function marked `must_use`
let _ = compute();  // OK: explicitly discarding
let result = compute()?;  // OK: using the result
```

Apply to any function where ignoring the return value is almost certainly a bug.

### `#[deprecated]`

```rust
#[deprecated(since = "2.0.0", note = "use new_function() instead")]
pub fn old_function() { }
```

Callers get a warning. Use in conjunction with `#[allow(deprecated)]` in your own migration code.

---

## 25. Custom Lints and Compiler Plugins

### Writing Custom Lints with Dylint

[Dylint](https://github.com/trailofbits/dylint) is the production tool for custom lints (works on stable):

```bash
cargo install cargo-dylint dylint-link
cargo dylint new my_lint_library
```

Example custom lint:

```rust
// In your dylint lint library:
use clippy_utils::diagnostics::span_lint;
use rustc_hir::{Expr, ExprKind};
use rustc_lint::{LateContext, LateLintPass, LintPass};
use rustc_session::{declare_lint, declare_lint_pass};

declare_lint! {
    pub NO_UNWRAP_IN_PRODUCTION,
    Warn,
    "avoid unwrap() in non-test code"
}

declare_lint_pass!(NoUnwrapInProduction => [NO_UNWRAP_IN_PRODUCTION]);

impl<'tcx> LateLintPass<'tcx> for NoUnwrapInProduction {
    fn check_expr(&mut self, cx: &LateContext<'tcx>, expr: &'tcx Expr<'tcx>) {
        if let ExprKind::MethodCall(method, _, _, _) = &expr.kind {
            if method.ident.name.as_str() == "unwrap" {
                span_lint(
                    cx,
                    NO_UNWRAP_IN_PRODUCTION,
                    expr.span,
                    "avoid using unwrap() in production code",
                );
            }
        }
    }
}
```

### Writing Proc Macro Lints

For compile-time invariant checking via proc macros:

```rust
// A proc macro that validates invariants at compile time:
#[proc_macro_attribute]
pub fn require_non_zero(attr: TokenStream, item: TokenStream) -> TokenStream {
    // Parse the function, add a compile-time assertion
    // that the argument is non-zero
}
```

### Using `rustc`'s Internal Lint Infrastructure (for Contributors)

If contributing to `rustc` or writing compiler plugins (nightly only):

```rust
#![feature(rustc_private)]
extern crate rustc_lint;
extern crate rustc_session;
extern crate rustc_hir;
```

This is unstable and changes between nightly versions. Use Dylint for stable custom lints.

---

## 26. MIR — Mid-level Intermediate Representation

### What MIR Is

MIR (Mid-level Intermediate Representation) is the internal control-flow-graph representation of Rust code, produced after HIR type checking. It:

- Makes control flow explicit (all branches, loops unwound to gotos)
- Makes all panics explicit (every potential panic site is shown)
- Is where borrow checking (NLL) operates
- Is the input to const evaluation
- Is the input to LLVM codegen

### Dumping MIR

```bash
# Dump MIR for entire compilation:
cargo rustc -- -Z dump-mir=all

# MIR for a specific function (nightly):
rustc -Z unpretty=mir main.rs

# With optimization stages:
rustc -Z unpretty=mir-opt main.rs  # after optimizations
```

### Reading MIR

```
fn main() -> () {
    let mut _0: ();              // return place
    let _1: i32;                 // let x
    let _2: i32;                 // let y
    
    bb0: {                       // basic block 0 (entry)
        _1 = const 5_i32;        // x = 5
        _2 = const 3_i32;        // y = 3
        _0 = foo(move _1, move _2) -> [return: bb1, unwind: bb2];
        //       ^move: ownership transferred      ^panic path
    }
    
    bb1: {                       // return block
        return;
    }
    
    bb2 (cleanup): {             // unwind (panic) block
        resume;
    }
}
```

Key concepts in MIR:

- **Basic blocks** (`bb0`, `bb1`, ...): Sequences of statements with one terminator
- **Terminators**: `goto`, `return`, `call`, `assert`, `switch`, `resume`
- **Places**: Locations (`_0`, `_1`, `(*_1).field`)
- **Rvalues**: Computations (`Use`, `BinaryOp`, `Ref`, `Cast`)
- **Statements**: `Assign`, `StorageLive`, `StorageDead`

### MIR and the Borrow Checker

NLL computes "regions" (sets of program points) for each borrow and checks that:
- The borrow is not used after its region ends
- No conflicting borrows overlap in their regions

MIR makes this tractable because all control flow is explicit — no implicit lifetimes based on lexical scope.

### Const Evaluation via MIR

Const evaluation interprets MIR at compile time. This is why const evaluation errors often show a MIR-level stack trace:

```
error[E0080]: evaluation of `COMPUTED` failed
  --> src/main.rs:1:15
   |
1  | const COMPUTED: i32 = 10 / 0;
   |                       ^^^^^^ attempt to divide by zero
```

The evaluator is `miri` — the same engine as the standalone `cargo miri` tool.

---

## 27. HIR — High-level Intermediate Representation

### What HIR Is

HIR (High-level IR) is produced after macro expansion and name resolution. It is a desugared, more explicit version of the AST but still close to the source. HIR is where:
- Type inference runs
- Trait resolution runs
- Pattern matching analysis runs
- Privacy checking runs

### Key HIR Desugaring

| Source                  | HIR Desugared Form                                |
|-------------------------|---------------------------------------------------|
| `for x in iter`         | `match iter.into_iter() { mut it => loop { ... }}`|
| `x?`                    | `match x { Ok(v) => v, Err(e) => return Err(e) }`|
| `a..b`                  | `Range { start: a, end: b }`                      |
| `x += y`                | `x = x + y`                                       |
| `if let Some(x) = opt`  | `match opt { Some(x) => ..., _ => () }`           |
| `while let ...`         | `loop { match ... { ... => ..., _ => break } }`   |
| `async fn`              | `fn -> impl Future`                               |
| `impl Trait` in arg     | `fn<T: Trait>(arg: T)`                            |
| `impl Trait` in return  | type alias impl trait (TAIT)                      |

### Viewing HIR

```bash
rustc -Z unpretty=hir main.rs      # human-readable HIR
rustc -Z unpretty=hir,typed main.rs # HIR with type annotations
rustc -Z unpretty=hir-tree main.rs  # HIR as tree structure
```

---

## 28. LLVM Backend Errors

### LLVM Errors vs rustc Errors

LLVM errors are rare in normal code but can appear when:
- Using SIMD intrinsics incorrectly
- Linking incompatible object files
- Using target features not available on the target CPU

```
LLVM ERROR: Cannot select: 0x...
```

This usually means the LLVM backend couldn't generate code for an operation. Common causes:
- Using an intrinsic for a CPU feature not enabled
- Cross-compilation target mismatch
- Internal LLVM assertion failure (usually a rustc bug)

### Linker Errors

Linker errors appear after compilation:

```
error: linking with `cc` failed: exit status: 1
  = note: /usr/bin/ld: cannot find -lsome_library
```

**Common linker errors**:

| Error                          | Cause                                          |
|--------------------------------|------------------------------------------------|
| `cannot find -lfoo`            | Library `libfoo` not in link path              |
| `undefined reference to foo`   | Function `foo` declared but not defined        |
| `multiple definition of foo`   | Same symbol defined in multiple compilation units |
| `relocation truncated to fit`  | 32-bit offset overflow (large binary)          |
| `version GLIBC_2.XX not found` | Compiled against newer glibc than runtime      |

**Fix undefined symbols**:
```bash
# Find which library provides a symbol:
nm -D /usr/lib/x86_64-linux-gnu/libsomething.so | grep symbol_name
# or
objdump -T /path/to/lib.so | grep symbol_name
```

### LTO (Link-Time Optimization) Errors

LTO errors often manifest as linker errors or incorrect output:
```toml
[profile.release]
lto = "thin"   # safer, faster to build, good optimization
# lto = "fat"  # full LTO: better optimization, slower, more potential issues
```

---

## 29. Incremental Compilation and Errors

### How Incremental Compilation Works

Rust caches compilation artifacts per query. When you change a file, only the affected queries are recomputed. The cache is stored in `target/debug/incremental/`.

### Stale Cache Errors

Incremental compilation occasionally produces strange errors that disappear after `cargo clean`. This is a known issue. Signs:
- Error messages pointing to lines that clearly look correct
- "Internal compiler error" that shouldn't exist
- Errors that appear and disappear randomly

**Fix**:
```bash
cargo clean
cargo build
```

Or selectively:
```bash
rm -rf target/debug/incremental
```

### Disabling Incremental Compilation

```toml
# Cargo.toml
[profile.dev]
incremental = false  # slower but no stale cache issues

# Or via env:
CARGO_INCREMENTAL=0 cargo build
```

For CI, disabling incremental compilation is often recommended as it produces more reproducible builds.

---

## 30. Proc Macros and Diagnostic APIs

### Proc Macro Types

| Type                | Invocation                       | Use case                                |
|---------------------|----------------------------------|-----------------------------------------|
| Function-like       | `my_macro!(tokens)`              | DSL, code generation from syntax        |
| Attribute           | `#[my_attr] fn foo() {}`        | Decorator pattern, transformation       |
| Derive              | `#[derive(MyTrait)]`            | Auto-implement traits                   |

### Emitting Diagnostics from Proc Macros

```rust
use proc_macro::{Diagnostic, Level, Span};

// Emit an error from a proc macro:
Diagnostic::spanned(
    span,
    Level::Error,
    "this attribute requires a string literal argument",
).emit();

// Emit with span:
span.error("this field must be named `id`").emit();
span.warning("deprecated, use `new_field` instead").emit();

// With help:
span.error("missing argument")
    .help("add a string argument like `#[my_attr(\"value\")]`")
    .emit();
```

### `syn` + `quote` Pattern

The standard approach for robust proc macros:

```rust
use proc_macro::TokenStream;
use quote::quote;
use syn::{parse_macro_input, DeriveInput};

#[proc_macro_derive(MyTrait)]
pub fn my_derive(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as DeriveInput);
    let name = &input.ident;

    let expanded = quote! {
        impl MyTrait for #name {
            fn hello(&self) -> &'static str {
                stringify!(#name)
            }
        }
    };

    TokenStream::from(expanded)
}
```

### Compile-Time Error Reporting in Macros

```rust
use syn::Error;

fn process(input: DeriveInput) -> Result<proc_macro2::TokenStream, Error> {
    if condition_fails {
        return Err(Error::new(
            input.ident.span(),
            "this derive macro requires the type to have a field named `id`"
        ));
    }
    // ...
}

// In the proc_macro entry point:
TokenStream::from(process(input).unwrap_or_else(|e| e.to_compile_error()))
```

This produces proper span-annotated errors that point to the correct location in user code.

---

## 31. Fuzzing, Testing, and Compiler Validation

### Testing Compiler Behavior

#### Unit Testing Compile Errors with `trybuild`

```rust
// In your crate's tests/
// tests/compile_fail/bad_usage.rs: code that SHOULD fail to compile
// tests/ui/*.rs: ui tests

// Cargo.toml:
[dev-dependencies]
trybuild = "1"

// tests/test_compile.rs:
#[test]
fn test_compile_errors() {
    let t = trybuild::TestCases::new();
    t.compile_fail("tests/compile_fail/*.rs");
    t.pass("tests/should_pass/*.rs");
}
```

`trybuild` compiles each test file and checks whether it produces expected errors. Essential for testing proc macros and API boundary conditions.

#### `ui_test` — Compiler Test Framework

```bash
cargo install ui_test
# Used in projects like cranelift, miri for large test suites
```

### Fuzzing

#### `cargo-fuzz` with libFuzzer

```bash
cargo install cargo-fuzz
cargo fuzz init
cargo fuzz add my_fuzz_target
cargo fuzz run my_fuzz_target
cargo fuzz run my_fuzz_target -- -max_len=65536
```

```rust
// fuzz/fuzz_targets/my_fuzz_target.rs
#![no_main]
use libfuzzer_sys::fuzz_target;

fuzz_target!(|data: &[u8]| {
    if let Ok(s) = std::str::from_utf8(data) {
        let _ = my_library::parse(s);  // should not panic or have UB
    }
});
```

#### `AFL` (American Fuzzy Lop)

```bash
cargo install afl
cargo afl build
cargo afl fuzz -i input_dir -o output_dir target/debug/my_binary
```

#### Structure-Aware Fuzzing with `arbitrary`

```rust
use arbitrary::Arbitrary;

#[derive(Arbitrary, Debug)]
struct FuzzInput {
    command: String,
    flags: Vec<u8>,
    size: u16,
}

fuzz_target!(|input: FuzzInput| {
    let _ = process(input.command, input.flags, input.size as usize);
});
```

### Miri Testing

```bash
cargo miri test           # run tests under Miri (finds UB)
cargo miri run            # run binary under Miri

# Miri flags:
MIRIFLAGS="-Zmiri-strict-provenance" cargo miri test
MIRIFLAGS="-Zmiri-track-raw-pointers" cargo miri test
MIRIFLAGS="-Zmiri-disable-isolation" cargo miri test  # allow system calls
```

### Benchmark Validation

```bash
cargo bench                              # run benchmarks (criterion)
cargo bench -- --save-baseline main      # save baseline
cargo bench -- --baseline main           # compare to baseline
```

---

## 32. Production-Grade Error Mitigation Patterns

### Pattern 1 — Error Type Hierarchy

```rust
use thiserror::Error;

#[derive(Debug, Error)]
pub enum StorageError {
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),

    #[error("Serialization error: {0}")]
    Serialize(#[from] serde_json::Error),

    #[error("Key not found: {key}")]
    NotFound { key: String },

    #[error("Quota exceeded: used {used}, limit {limit}")]
    QuotaExceeded { used: u64, limit: u64 },
}

// Public API returns Result<T, StorageError>
pub fn get(key: &str) -> Result<Vec<u8>, StorageError> { ... }
```

### Pattern 2 — Never Panic in Library Code

```rust
// BAD:
pub fn parse(input: &str) -> Config {
    serde_json::from_str(input).unwrap()  // panics on invalid input
}

// GOOD:
pub fn parse(input: &str) -> Result<Config, ParseError> {
    serde_json::from_str(input).map_err(ParseError::Json)
}
```

### Pattern 3 — Zero-Cost Abstractions for Safety

```rust
// Newtype for type-safe IDs (zero runtime cost):
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct UserId(u64);

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct OrderId(u64);

// Now this is a compile error (not a runtime bug):
fn process_order(user: UserId, order: OrderId) { ... }

let user = UserId(1);
let order = OrderId(2);
process_order(order, user);  // ERROR: type mismatch — caught at compile time
```

### Pattern 4 — Builder Pattern for Required vs Optional

```rust
#[derive(Default)]
pub struct ConfigBuilder {
    host: Option<String>,
    port: Option<u16>,
    tls: bool,
}

impl ConfigBuilder {
    pub fn host(mut self, h: impl Into<String>) -> Self {
        self.host = Some(h.into()); self
    }
    pub fn port(mut self, p: u16) -> Self {
        self.port = Some(p); self
    }
    pub fn build(self) -> Result<Config, ConfigError> {
        Ok(Config {
            host: self.host.ok_or(ConfigError::MissingHost)?,
            port: self.port.unwrap_or(8080),
            tls: self.tls,
        })
    }
}
```

### Pattern 5 — Type-State Pattern

```rust
// States are types — impossible to call methods in wrong order:
struct Connection<State>(TcpStream, PhantomData<State>);

struct Disconnected;
struct Connected;
struct Authenticated;

impl Connection<Disconnected> {
    pub fn connect(addr: &str) -> Result<Connection<Connected>, Error> { ... }
}

impl Connection<Connected> {
    pub fn authenticate(self, creds: &Credentials) -> Result<Connection<Authenticated>, Error> { ... }
}

impl Connection<Authenticated> {
    pub fn send(&mut self, data: &[u8]) -> Result<(), Error> { ... }
}

// This won't compile — can't send without authenticating:
let conn = Connection::connect("host:port")?;
conn.send(b"data");  // ERROR: method `send` not found on Connection<Connected>
```

### Pattern 6 — Compile-Time Checks via Const

```rust
const fn assert_size<T>() {
    assert!(std::mem::size_of::<T>() <= 64, "type too large for stack allocation");
}

const _: () = assert_size::<MyStruct>();  // checked at compile time
```

---

## 33. Common Expert-Level Mistakes and Their Fixes

### Mistake 1 — Fighting the Borrow Checker Instead of Working With It

```rust
// BAD: trying to hold a reference and mutate the container
let v = vec![1, 2, 3];
let first = &v[0];
let mut v = v;  // ERROR: can't rebind while borrowed
v.push(4);

// GOOD: restructure to avoid overlapping borrows
let first_val = v[0];       // copy the value
let mut v = v;              // now rebind
v.push(4);
println!("{}", first_val);
```

### Mistake 2 — Arc<Mutex<T>> Deadlock Pattern

```rust
// BAD: holding MutexGuard across .await
async fn bad(data: Arc<Mutex<Vec<i32>>>) {
    let guard = data.lock().unwrap();  // holds lock
    async_operation().await;           // yields to executor — still holding lock!
    println!("{:?}", *guard);
}

// GOOD: release lock before .await
async fn good(data: Arc<Mutex<Vec<i32>>>) {
    let snapshot = {
        let guard = data.lock().unwrap();
        guard.clone()  // copy data out
    };  // guard dropped here
    async_operation().await;  // no lock held
    println!("{:?}", snapshot);
}
```

### Mistake 3 — Misunderstanding `Clone` in Closures

```rust
// BAD: Arc cloned on every call
let data = Arc::new(vec![1, 2, 3]);
let f = move || {
    let data = data.clone();  // Arc::clone on every closure call? No.
    // Actually: `data` is moved into closure once, cloned Arc reference is inside
    process(&data)
};

// The above is actually fine for Arc — Arc::clone is cheap (atomic increment)
// But for large data, this pattern matters:
let data = Arc::new(large_data);
let data_clone = Arc::clone(&data);  // explicit clone for the closure
let f = move || process(&data_clone);
// data is still available outside the closure
```

### Mistake 4 — Returning References to Local Variables

```rust
// BAD (won't compile, but understanding why matters):
fn get_string() -> &str {
    let s = String::from("hello");
    &s  // ERROR: s will be dropped
}

// GOOD options:
fn get_string() -> String {    // return owned value
    String::from("hello")
}

fn get_string() -> &'static str {  // return static reference
    "hello"
}

fn get_string<'a>(buf: &'a mut String) -> &'a str {  // write to caller-provided buffer
    buf.push_str("hello");
    buf.as_str()
}
```

### Mistake 5 — Over-Using `clone()` to Fix Borrow Errors

```rust
// BAD: cloning to fix borrow error hides architectural issue
fn process(data: &HashMap<String, Vec<i32>>) {
    for (key, _) in data {
        let values = data.get(key).unwrap().clone();  // unnecessary clone
        do_something(&key, &values);
    }
}

// GOOD: restructure to avoid the need for clone
fn process(data: &HashMap<String, Vec<i32>>) {
    for (key, values) in data {
        do_something(key, values);  // both are &String and &Vec<i32>
    }
}
```

### Mistake 6 — Misusing `unsafe` to "Fix" Lifetime Errors

```rust
// BAD: unsafe transmute to bypass lifetime check
unsafe {
    let s: &'static str = std::mem::transmute(local_string.as_str());
    // UB: s will dangle when local_string is dropped
}

// GOOD: fix the actual lifetime issue
// Understand WHY the compiler rejected it, then fix the design
```

### Mistake 7 — Ignoring `#[must_use]` Errors

```rust
// BAD:
std::fs::remove_file("important_file.txt");  // WARNING: unused Result
// If this fails, you never know!

// GOOD:
std::fs::remove_file("important_file.txt")
    .expect("failed to remove file");
// or:
if let Err(e) = std::fs::remove_file("important_file.txt") {
    eprintln!("Warning: could not remove file: {}", e);
}
```

---

## 34. Security-Relevant Compiler Behaviors

### Stack Overflow in Recursive Types

```rust
// Infinite size at compile time — detected:
struct Node {
    child: Node,  // ERROR: has infinite size
}

// Fix: indirection via Box
struct Node {
    child: Option<Box<Node>>,
}
```

### Integer Overflow Behavior

| Mode          | On overflow      |
|---------------|-----------------|
| Debug build   | Panic (checked) |
| Release build | Wrap (two's complement) |
| `overflow-checks = true` in profile | Panic in release too |
| `wrapping_add`, `saturating_add`, `checked_add` | Explicit control |

```toml
# For security-critical builds:
[profile.release]
overflow-checks = true
```

```rust
// Always use checked arithmetic in security-sensitive code:
let result = a.checked_add(b).ok_or(Error::Overflow)?;
let result = a.saturating_add(b);  // clamps to MAX instead of overflow
let result = a.wrapping_add(b);    // explicit wrap (for crypto, hash code)
```

### `#![forbid(unsafe_code)]`

For security-critical libraries, forbid all unsafe:

```rust
#![forbid(unsafe_code)]
```

This prevents all direct unsafe usage in the crate. Can still call into unsafe crates (you're trusting their unsafe is sound).

### Memory Zeroization

Sensitive data should be zeroed when dropped:

```rust
use zeroize::Zeroize;

#[derive(Zeroize)]
#[zeroize(drop)]  // automatically zeroize on drop
struct SecretKey([u8; 32]);
```

The compiler will NOT automatically zero sensitive memory on drop without `zeroize`. The `Drop` trait can do it explicitly, but compiler optimizations may elide "dead" writes to memory. `zeroize` uses `volatile_write` or `compiler_fence` to prevent this.

### No `std` for Embedded / High-Security Contexts

```rust
#![no_std]  // disables the standard library
// Only core and alloc crates available
```

This is used in:
- Embedded systems (no OS)
- WASM environments
- Security-critical code where controlled stdlib is required
- Firmware

### Constant-Time Code

The compiler may reorder or optimize code in ways that break constant-time properties (important for crypto). Use dedicated crates:

```toml
subtle = "2"       # constant-time comparisons
zeroize = "1"      # secure memory clearing
```

```rust
use subtle::ConstantTimeEq;

// BAD: timing side channel
if secret == guess { ... }

// GOOD: constant-time comparison
if secret.ct_eq(&guess).into() { ... }
```

### Supply Chain: `cargo audit`

```bash
cargo install cargo-audit
cargo audit                  # check dependencies for known vulnerabilities
cargo audit fix              # update vulnerable dependencies
```

### Reproducible Builds

```toml
# Cargo.lock must be committed for binaries
# For libraries, Cargo.lock is optional but recommended

# In .cargo/config.toml:
[build]
# Ensure reproducible builds (remove build host path from debug info):
rustflags = ["-C", "remap-path-prefix=/home/user/project=."]
```

```bash
# Build with SOURCE_DATE_EPOCH for reproducibility:
SOURCE_DATE_EPOCH=0 cargo build --release
```

---

## 35. References and Resources

### Official Documentation

- **Rust Reference**: https://doc.rust-lang.org/reference/
- **Error Code Index**: https://doc.rust-lang.org/error_codes/
- **Rustonomicon** (unsafe Rust): https://doc.rust-lang.org/nomicon/
- **Rustc Dev Guide**: https://rustc-dev-guide.rust-lang.org/
- **Clippy Lints**: https://rust-lang.github.io/rust-clippy/
- **Rust API Guidelines**: https://rust-lang.github.io/api-guidelines/

### Compiler Internals

- **rustc-dev-guide**: https://rustc-dev-guide.rust-lang.org/ — how the compiler works internally
- **MIR RFC**: https://github.com/rust-lang/rfcs/blob/master/text/1211-mir.md
- **NLL RFC**: https://github.com/rust-lang/rfcs/blob/master/text/2094-nll.md
- **Polonius**: https://github.com/rust-lang/polonius

### Tools

| Tool              | Purpose                                   | Install                        |
|-------------------|-------------------------------------------|--------------------------------|
| `cargo clippy`    | Lint checking                             | `rustup component add clippy`  |
| `cargo fix`       | Auto-apply suggestions                    | Built into cargo               |
| `cargo expand`    | Macro expansion                           | `cargo install cargo-expand`   |
| `cargo audit`     | Security advisories                       | `cargo install cargo-audit`    |
| `cargo deny`      | Dependency policy enforcement             | `cargo install cargo-deny`     |
| `cargo miri`      | UB detection                              | `rustup component add miri`    |
| `cargo fuzz`      | Fuzzing                                   | `cargo install cargo-fuzz`     |
| `cargo-semver-checks` | API compatibility checking            | `cargo install cargo-semver-checks` |
| `cargo geiger`    | Count unsafe code in dependencies         | `cargo install cargo-geiger`   |
| `dylint`          | Custom lints                              | `cargo install cargo-dylint`   |
| `rust-analyzer`   | IDE integration (LSP)                     | Via editor plugin              |
| `rustfmt`         | Code formatting                           | `rustup component add rustfmt` |

### Commands Cheat Sheet

```bash
# Understanding errors:
rustc --explain E0382

# Inspect compiler internals:
cargo rustc -- -Z unpretty=hir
cargo rustc -- -Z unpretty=mir
cargo rustc -- -Z print-type-sizes
cargo expand

# Quality gates:
cargo clippy --all-targets -- -D warnings
cargo test
RUSTFLAGS="-D warnings" cargo build
cargo audit
cargo deny check

# UB and safety:
cargo miri test
RUSTFLAGS="-Z sanitizer=address" cargo +nightly test

# Performance:
cargo bench
cargo build --release
cargo rustc --release -- -C target-cpu=native

# Fuzzing:
cargo fuzz run my_target

# Fix suggestions:
cargo fix --edition 2021
cargo clippy --fix
```

---

## Summary: The Elite Rust Compiler Mental Model

```
Source Code
    │
    ├─ SYNTAX ERRORS ──────────────────── Fix first. Parser aborts early.
    │   (bad tokens, wrong grammar)
    │
    ├─ NAME RESOLUTION ERRORS ──────────── unresolved imports, ambiguous names
    │   (E0432, E0433, E0425)
    │
    ├─ TYPE ERRORS ─────────────────────── mismatched types, trait bounds not met
    │   (E0308, E0277, E0282)              type inference failed
    │   [no borrow checking yet]
    │
    ├─ BORROW CHECKER ERRORS ───────────── use-after-move, aliasing violations
    │   (E0382, E0499, E0502, E0597)       lifetime violations
    │   [NLL / Polonius]
    │
    ├─ MIR ERRORS ──────────────────────── non-exhaustive patterns
    │   (E0004)                             const eval failures
    │
    ├─ LINT WARNINGS ───────────────────── style, unused, clippy
    │   [configurable, deny to harden]
    │
    └─ LINKER ERRORS ───────────────────── missing symbols, library not found
        [after all compilation succeeds]

Master each layer → understand exactly which phase caused an error
→ fix it at the right level → never fight the compiler, design with it.
```

> **Elite Principle**: The Rust compiler is not an obstacle — it is the most powerful static analysis tool available in any mainstream language. When the compiler rejects code, it is communicating a real concern about correctness, memory safety, or thread safety. The goal is to understand WHY the rejection is happening at which phase, and then redesign the code to be correct by construction. The compiler's errors are your specification.

---

*Guide version: Rust 1.87 / 2025 — covers stable, beta, and nightly features where noted.*

Now let me create this comprehensive guide. This will be a large, thorough `.md` file.**~4,500-line comprehensive guide** covering every layer of the Rust compiler. Here's what's inside:

**Architecture & Pipeline** — Full 9-phase pipeline from lexing through LLVM/linking, with exactly which error class originates from which phase.

**Diagnostic System** — How `DiagnosticBuilder` works internally, the full JSON schema, all rendering formats, and how `rustfix` consumes machine-applicable suggestions.

**E-code Reference** — 80+ critical E-codes organized by category (ownership, lifetimes, types, traits) with full explanation of each.

**Borrow Checker Deep Dive** — NLL regions, two-phase borrows, Polonius, every major borrowing error pattern with correct fixes and the underlying reasoning.

**Lifetimes** — Elision rules, subtyping, variance (covariant/contravariant/invariant), HRTB (`for<'a>`), and `'static` gotchas with threads.

**MIR / HIR** — How to dump and read both IRs, how NLL operates on MIR, the desugaring table for HIR.

**Lint System** — Complete lint taxonomy, all built-in lint categories, Clippy's 8 categories with the most critical security/systems lints called out.

**Production Patterns** — Type-state pattern, newtype IDs, builder pattern, zero-cost safety abstractions, constant-time code, `zeroize`, `#![forbid(unsafe_code)]`.

**Security Section** — Integer overflow modes, UB categories, Miri/sanitizers, `cargo-audit`, reproducible builds, supply chain hardening.

**Next 3 Steps**:
1. Run `cargo clippy -- -W clippy::restriction -W clippy::pedantic` on a real codebase and triage every lint — this forces you to understand each one.
2. Run `cargo miri test` on any codebase that uses `unsafe` — resolve every Miri finding with the guide's UB table as reference.
3. Write a Dylint custom lint for a codebase-specific invariant (e.g., ban direct `HashMap::get().unwrap()`, require `get().ok_or(Error::NotFound)?`) — this cements understanding of the HIR visitor API.