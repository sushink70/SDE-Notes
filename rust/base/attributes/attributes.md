# Attributes: The Complete Deep Dive

Attributes are Rust's metaprogramming system. They're how the compiler communicates with you and how you communicate with the compiler. This is the knowledge that separates experts from users.

---

## **I. The Fundamental Architecture**

### **What Attributes Actually Are**

Attributes are **metadata** attached to items. They exist in three forms:

```rust
#![crate_attribute]  // Inner attribute (applies to enclosing item)
#[item_attribute]    // Outer attribute (applies to following item)
```

**At the AST level**, attributes are just structured data:

```rust
pub struct Attribute {
    pub kind: AttrKind,
    pub id: AttrId,
    pub style: AttrStyle,  // Inner vs Outer
    pub span: Span,
}

pub enum AttrKind {
    Normal(AttrItem),      // #[attr]
    DocComment(CommentKind, Symbol),  // /// doc
}
```

**Processing Order**:
1. Parser creates AST with attributes attached
2. Attribute macros run (transform AST)
3. Derive macros run (generate new code)
4. Built-in attributes processed by compiler
5. Lints check for unknown/malformed attributes

---

## **II. Built-In Attributes: The Complete Catalog**

### **Conditional Compilation**

#### **cfg: The Power Tool**

```rust
// Basic platform detection
#[cfg(target_os = "linux")]
fn linux_only() {}

#[cfg(target_os = "windows")]
fn windows_only() {}

#[cfg(target_os = "macos")]
fn macos_only() {}
```

**All cfg Predicates**:

```rust
// Operating System
#[cfg(target_os = "linux")]      // linux, windows, macos, ios, android, freebsd, etc.

// Architecture
#[cfg(target_arch = "x86_64")]   // x86, x86_64, arm, aarch64, wasm32, etc.

// Pointer width
#[cfg(target_pointer_width = "64")]  // "32" or "64"

// Endianness
#[cfg(target_endian = "little")]     // "little" or "big"

// Environment
#[cfg(target_env = "gnu")]       // gnu, msvc, musl, etc.

// Vendor
#[cfg(target_vendor = "apple")]  // apple, pc, unknown, etc.

// Features
#[cfg(feature = "serde")]        // Cargo features

// Debug vs Release
#[cfg(debug_assertions)]         // Present in debug builds
#[cfg(not(debug_assertions))]    // Present in release builds

// Test mode
#[cfg(test)]                     // Only when running tests

// Target family
#[cfg(target_family = "unix")]   // unix or windows
```

**Complex Conditions**:

```rust
// Boolean logic
#[cfg(all(unix, target_arch = "x86_64"))]
fn unix_x64_only() {}

#[cfg(any(target_os = "linux", target_os = "macos"))]
fn unix_like() {}

#[cfg(not(windows))]
fn non_windows() {}

// Nested conditions
#[cfg(all(
    feature = "advanced",
    any(target_arch = "x86_64", target_arch = "aarch64"),
    not(debug_assertions)
))]
fn optimized_advanced() {}
```

**Elite Pattern: Feature Flags for API Evolution**

```rust
// lib.rs
#[cfg(feature = "v2")]
pub mod v2;

#[cfg(not(feature = "v2"))]
pub mod v1;

// Export appropriate version
#[cfg(feature = "v2")]
pub use v2::*;

#[cfg(not(feature = "v2"))]
pub use v1::*;
```

#### **cfg_attr: Conditional Attributes**

```rust
// Apply attribute only on certain platforms
#[cfg_attr(target_os = "linux", link(name = "ssl"))]
#[cfg_attr(target_os = "windows", link(name = "ssleay32"))]
extern "C" {}

// Conditional derives
#[cfg_attr(feature = "serde", derive(Serialize, Deserialize))]
struct Data {
    value: i32,
}

// Performance: inline only in release
#[cfg_attr(not(debug_assertions), inline(always))]
fn hot_function() {}
```

**Hidden Power**: Chain multiple attributes:

```rust
#[cfg_attr(
    all(target_arch = "x86_64", not(debug_assertions)),
    inline(always),
    target_feature(enable = "avx2")
)]
fn simd_optimized() {}
```

---

### **Derive Macros: The Magic**

```rust
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
struct Point {
    x: i32,
    y: i32,
}
```

**What derive Actually Does**:

```rust
// #[derive(Debug)] expands to:
impl std::fmt::Debug for Point {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("Point")
            .field("x", &self.x)
            .field("y", &self.y)
            .finish()
    }
}
```

**All Standard Derivable Traits**:

```rust
// Comparison
#[derive(PartialEq)]  // a == b
#[derive(Eq)]         // Requires PartialEq, adds reflexivity guarantee
#[derive(PartialOrd)] // a < b, a > b
#[derive(Ord)]        // Requires Eq + PartialOrd, total ordering

// Copying
#[derive(Clone)]      // Explicit .clone()
#[derive(Copy)]       // Requires Clone, implicit bitwise copy

// Hashing
#[derive(Hash)]       // For HashMap keys

// Debug
#[derive(Debug)]      // {:?} formatting

// Default
#[derive(Default)]    // Default::default()
```

**Derive Dependencies**:

```
Ord requires: Eq + PartialOrd
Eq requires: PartialEq
Copy requires: Clone
```

**Elite Insight: Derive Behavior Control**

```rust
use std::hash::{Hash, Hasher};

#[derive(Hash)]
struct Optimized {
    #[hash(ignore)]  // NOT STANDARD - example of what you'd want
    cached: String,
    
    id: u64,
}

// Manual implementation for fine control
impl Hash for Optimized {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.id.hash(state);
        // cached is intentionally not hashed
    }
}
```

---

### **Testing Attributes**

```rust
// Basic test
#[test]
fn test_addition() {
    assert_eq!(2 + 2, 4);
}

// Ignore test (don't run by default)
#[test]
#[ignore]
fn expensive_test() {
    // Run with: cargo test -- --ignored
}

// Ignore with reason (Rust 1.68+)
#[test]
#[ignore = "waiting for upstream fix"]
fn broken_test() {}

// Should panic
#[test]
#[should_panic]
fn test_panic() {
    panic!("Expected");
}

// Should panic with specific message
#[test]
#[should_panic(expected = "division by zero")]
fn test_div_zero() {
    let _ = 1 / 0;
}
```

**Advanced Test Organization**:

```rust
// Test module
#[cfg(test)]
mod tests {
    use super::*;
    
    // Setup for all tests
    fn setup() -> Context {
        Context::new()
    }
    
    #[test]
    fn test_with_setup() {
        let ctx = setup();
        assert!(ctx.is_valid());
    }
}

// Integration tests (in tests/ directory)
#[test]
#[ignore]
fn integration_test() {}
```

**Benchmark Tests** (unstable):

```rust
#![feature(test)]
extern crate test;

#[bench]
fn bench_function(b: &mut test::Bencher) {
    b.iter(|| {
        // Code to benchmark
        expensive_operation()
    });
}
```

---

### **Inline Attributes: Performance Control**

```rust
// Suggest inlining
#[inline]
fn small_function() -> i32 {
    42
}

// Force inlining (almost always)
#[inline(always)]
fn must_inline() -> i32 {
    1 + 1
}

// Prevent inlining
#[inline(never)]
fn large_function() {
    // Complex logic
}
```

**When Each Matters**:

| Attribute | Use Case | Effect |
|-----------|----------|--------|
| `#[inline]` | Small hot functions | Suggests to optimizer |
| `#[inline(always)]` | Tiny functions (<10 instructions) | Forces inlining |
| `#[inline(never)]` | Large cold functions | Prevents code bloat |

**Elite Pattern: Inline Based on Build Mode**:

```rust
#[cfg_attr(not(debug_assertions), inline(always))]
#[cfg_attr(debug_assertions, inline(never))]
fn conditional_inline() {
    // Inlined in release, not in debug (better stack traces)
}
```

**The Hidden Cost**:

```rust
// This prevents inlining across crates by default
pub fn public_function() {}

// This allows cross-crate inlining
#[inline]
pub fn inlinable_function() {}
```

---

### **Cold and Hot Paths**

```rust
// Mark rarely executed code
#[cold]
fn error_path() {
    eprintln!("Error occurred");
}

// Compiler moves this out of hot path
fn main_loop() {
    if unlikely_condition {
        error_path();  // Marked cold, moved away
    }
}
```

**Branch Prediction Hints**:

```rust
// Manual likely/unlikely (unstable)
#![feature(core_intrinsics)]

if std::intrinsics::likely(condition) {
    // Hot path
} else {
    // Cold path
}
```

**Elite Technique: Profile-Guided Optimization**:

```bash
# Build with instrumentation
RUSTFLAGS="-Cprofile-generate=/tmp/pgo-data" cargo build --release

# Run workload
./target/release/myapp

# Build with profile data
RUSTFLAGS="-Cprofile-use=/tmp/pgo-data" cargo build --release
```

---

### **Link and Linkage Attributes**

```rust
// Link to native library
#[link(name = "ssl")]
extern "C" {
    fn SSL_new() -> *mut std::ffi::c_void;
}

// Specify link kind
#[link(name = "mylib", kind = "static")]
extern "C" {}

// Link framework (macOS/iOS)
#[link(name = "Foundation", kind = "framework")]
extern "C" {}
```

**Link Name Override**:

```rust
#[link(name = "ssl")]
extern "C" {
    // Function is actually named "OpenSSL_version" in library
    #[link_name = "OpenSSL_version"]
    fn ssl_version(t: i32) -> *const i8;
}
```

**Export Symbols**:

```rust
// Make symbol visible in library
#[no_mangle]
pub extern "C" fn my_function() {}

// Control symbol visibility
#[no_mangle]
#[export_name = "custom_name"]
pub extern "C" fn exposed_function() {}
```

---

### **Representation Attributes**

```rust
// C-compatible layout
#[repr(C)]
struct CStruct {
    x: i32,
    y: i32,
}

// Packed (no padding)
#[repr(packed)]
struct Packed {
    a: u8,
    b: u32,  // Normally padded, not here
}

// Aligned
#[repr(align(64))]  // Cache line aligned
struct Aligned {
    data: [u8; 64],
}

// Transparent (single-field wrapper)
#[repr(transparent)]
struct Wrapper(u32);
```

**Advanced Representations**:

```rust
// Integer discriminant for enum
#[repr(u8)]
enum SmallEnum {
    A,     // 0
    B,     // 1
    C = 5, // 5
}

// C-style enum
#[repr(C)]
enum CFfiEnum {
    Variant1,
    Variant2,
}

// Explicit discriminants
#[repr(i32)]
enum Flags {
    Read = 0b0001,
    Write = 0b0010,
    Execute = 0b0100,
}
```

**The repr(Rust) Secret**:

```rust
// Default representation - UNDEFINED
struct Optimized {
    a: u8,
    b: u64,
    c: u8,
}

// Compiler may reorder to:
// struct Optimized {
//     b: u64,  // 8 bytes
//     a: u8,   // 1 byte
//     c: u8,   // 1 byte
//     // 6 bytes padding
// }
// Total: 16 bytes instead of 24 bytes with C layout
```

---

### **Allow, Warn, Deny, Forbid**

```rust
// Allow specific lint
#[allow(dead_code)]
fn unused_function() {}

// Warn on specific pattern
#[warn(missing_docs)]
pub fn public_api() {}

// Deny (error on)
#[deny(unsafe_code)]
mod safe_module {}

// Forbid (cannot be overridden)
#[forbid(unsafe_code)]
mod ultra_safe {}
```

**Crate-level Lints**:

```rust
// At crate root
#![warn(missing_docs)]
#![deny(unsafe_code)]
#![forbid(unsafe_op_in_unsafe_fn)]

// Clippy lints
#![warn(clippy::all)]
#![warn(clippy::pedantic)]
#![warn(clippy::cargo)]
```

**The Lint Hierarchy**:

```
forbid > deny > warn > allow
```

**Elite Pattern: Lint Groups**:

```rust
#![deny(
    missing_docs,
    missing_debug_implementations,
    missing_copy_implementations,
    trivial_casts,
    trivial_numeric_casts,
    unsafe_code,
    unstable_features,
    unused_import_braces,
    unused_qualifications
)]
```

---

### **Deprecation**

```rust
// Deprecated item
#[deprecated]
fn old_function() {}

// With message
#[deprecated(since = "1.2.0", note = "Use new_function instead")]
fn old_api() {}

// Deprecate conditionally
#[cfg_attr(feature = "v2", deprecated)]
fn legacy_function() {}
```

**Deprecation for Types**:

```rust
#[deprecated(
    since = "2.0.0",
    note = "Use NewStruct instead. This will be removed in 3.0.0"
)]
pub struct OldStruct {
    pub field: i32,
}
```

---

### **Documentation Attributes**

```rust
/// This is a doc comment (sugar for #[doc = "..."])
/// 
/// # Examples
/// 
/// ```
/// let x = example();
/// assert_eq!(x, 42);
/// ```
pub fn example() -> i32 { 42 }

// Equivalent to:
#[doc = "This is a doc comment"]
pub fn example2() -> i32 { 42 }
```

**Advanced Doc Attributes**:

```rust
// Include file contents as docs
#[doc = include_str!("../README.md")]
pub struct Documented;

// Hide from documentation
#[doc(hidden)]
pub fn internal_api() {}

// Documentation alias (searchable alternative name)
#[doc(alias = "remove")]
pub fn delete() {}

// Inline documentation from another item
#[doc(inline)]
pub use other_module::Type;

// Cfg for documentation
#[cfg_attr(docsrs, doc(cfg(feature = "advanced")))]
#[cfg(feature = "advanced")]
pub fn advanced_feature() {}
```

**Doc Tests**:

```rust
/// ```
/// # use mylib::*;
/// # fn main() -> Result<(), Box<dyn std::error::Error>> {
/// let result = fallible_operation()?;
/// assert_eq!(result, 42);
/// # Ok(())
/// # }
/// ```
pub fn fallible_operation() -> Result<i32, Error> {
    Ok(42)
}

/// ```no_run
/// // This compiles but doesn't run
/// loop {
///     expensive_operation();
/// }
/// ```
pub fn expensive_operation() {}

/// ```compile_fail
/// // This is expected to fail compilation
/// let x: i32 = "not a number";
/// ```
pub fn type_safety() {}

/// ```ignore
/// // Completely ignored (useful for pseudocode)
/// let magic = do_impossible_thing();
/// ```
pub fn conceptual() {}
```

---

## **III. Procedural Macros: The Deep Architecture**

### **The Three Types**

```rust
// 1. Function-like macros
my_macro!(input);

// 2. Derive macros
#[derive(MyDerive)]
struct S;

// 3. Attribute macros
#[my_attribute]
fn f() {}
```

### **How Derive Macros Work**

**The Trait**:

```rust
// In your library
pub trait MyTrait {
    fn my_method(&self);
}
```

**The Derive Implementation**:

```rust
// In separate proc-macro crate
use proc_macro::TokenStream;
use quote::quote;
use syn::{parse_macro_input, DeriveInput};

#[proc_macro_derive(MyTrait)]
pub fn derive_my_trait(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as DeriveInput);
    let name = &input.ident;
    
    let expanded = quote! {
        impl MyTrait for #name {
            fn my_method(&self) {
                println!("Called on {}", stringify!(#name));
            }
        }
    };
    
    TokenStream::from(expanded)
}
```

**Usage**:

```rust
#[derive(MyTrait)]
struct MyStruct;

fn main() {
    MyStruct.my_method();  // "Called on MyStruct"
}
```

### **Derive Macro Helpers**

```rust
#[proc_macro_derive(MyTrait, attributes(my_helper))]
pub fn derive_my_trait(input: TokenStream) -> TokenStream {
    // Can now use #[my_helper] on fields
}

// Usage:
#[derive(MyTrait)]
struct S {
    #[my_helper(skip)]
    field: i32,
}
```

**Parsing Helper Attributes**:

```rust
use syn::{Attribute, Meta, NestedMeta};

fn parse_helper_attr(attr: &Attribute) -> Option<String> {
    if attr.path.is_ident("my_helper") {
        match attr.parse_meta() {
            Ok(Meta::List(meta_list)) => {
                for nested in meta_list.nested {
                    if let NestedMeta::Meta(Meta::Path(path)) = nested {
                        if path.is_ident("skip") {
                            return Some("skip".to_string());
                        }
                    }
                }
            }
            _ => {}
        }
    }
    None
}
```

### **Attribute Macros**

```rust
#[proc_macro_attribute]
pub fn my_attribute(
    attr: TokenStream,  // Arguments to attribute
    item: TokenStream,  // Item the attribute is on
) -> TokenStream {
    let input = parse_macro_input!(item as ItemFn);
    let name = &input.sig.ident;
    
    let expanded = quote! {
        fn #name() {
            println!("Before");
            #input
            println!("After");
        }
    };
    
    TokenStream::from(expanded)
}
```

**Elite Pattern: Wrapping Functions**:

```rust
#[proc_macro_attribute]
pub fn measure_time(_attr: TokenStream, item: TokenStream) -> TokenStream {
    let input = parse_macro_input!(item as ItemFn);
    let name = &input.sig.ident;
    let body = &input.block;
    let vis = &input.vis;
    let sig = &input.sig;
    
    let expanded = quote! {
        #vis #sig {
            let start = std::time::Instant::now();
            let result = (|| #body)();
            let elapsed = start.elapsed();
            println!("{} took {:?}", stringify!(#name), elapsed);
            result
        }
    };
    
    TokenStream::from(expanded)
}

// Usage:
#[measure_time]
fn expensive_operation() -> i32 {
    // ...
    42
}
```

### **Function-Like Macros**

```rust
#[proc_macro]
pub fn sql(input: TokenStream) -> TokenStream {
    let sql = input.to_string();
    
    // Parse SQL at compile time
    let parsed = parse_sql(&sql);
    
    // Generate type-safe Rust code
    generate_query_code(parsed)
}

// Usage:
let query = sql!("SELECT * FROM users WHERE id = ?");
```

---

## **IV. Advanced Attribute Patterns**

### **Conditional Compilation Matrix**

```rust
// Complex feature matrix
#[cfg(all(
    any(target_os = "linux", target_os = "macos"),
    target_arch = "x86_64",
    feature = "ssl",
    not(feature = "native-tls")
))]
mod openssl_x64_unix;

#[cfg(all(
    target_os = "windows",
    any(target_arch = "x86_64", target_arch = "aarch64"),
    feature = "ssl"
))]
mod schannel_windows;
```

**Elite Pattern: Feature Flag Validation**:

```rust
// Ensure mutually exclusive features
#[cfg(all(feature = "backend-a", feature = "backend-b"))]
compile_error!("Cannot enable both backend-a and backend-b");

// Ensure at least one feature
#[cfg(not(any(feature = "backend-a", feature = "backend-b")))]
compile_error!("Must enable at least one backend");
```

### **Custom Section Data**

```rust
// Place data in custom ELF section
#[link_section = ".mystuff"]
static MY_DATA: [u8; 1024] = [0; 1024];

// Used for embedded systems, kernel modules
#[link_section = ".init"]
fn init_function() {}
```

### **Must Use**

```rust
// Result of function must be used
#[must_use]
fn important_operation() -> Result<(), Error> {
    Ok(())
}

// With custom message
#[must_use = "The lock guard must be held"]
fn acquire_lock() -> LockGuard {
    LockGuard::new()
}

// On types
#[must_use = "Iterators are lazy and do nothing unless consumed"]
struct MyIterator;
```

### **Track Caller**

```rust
// Get caller's location
#[track_caller]
fn assert_positive(x: i32) {
    if x <= 0 {
        panic!(
            "Expected positive number at {}",
            std::panic::Location::caller()
        );
    }
}

fn main() {
    assert_positive(-1);  // Panic shows THIS line, not inside function
}
```

---

## **V. Unstable and Nightly Attributes**

### **Feature Gates**

```rust
#![feature(test)]           // Enable unstable features
#![feature(asm)]            // Inline assembly
#![feature(box_syntax)]     // box syntax
#![feature(specialization)] // Trait specialization
```

### **Const Fn**

```rust
// Const function
#[const_fn]
const fn compile_time_computation(x: i32) -> i32 {
    x * 2
}

const RESULT: i32 = compile_time_computation(21);  // Computed at compile time
```

### **Intrinsics**

```rust
#![feature(core_intrinsics)]

use std::intrinsics;

#[inline(always)]
unsafe fn fast_copy<T>(src: *const T, dst: *mut T, count: usize) {
    intrinsics::copy_nonoverlapping(src, dst, count);
}
```

### **SIMD**

```rust
#![feature(portable_simd)]

use std::simd::f32x8;

#[target_feature(enable = "avx2")]
unsafe fn vectorized_add(a: &[f32], b: &[f32], c: &mut [f32]) {
    let a_vec = f32x8::from_slice(a);
    let b_vec = f32x8::from_slice(b);
    let c_vec = a_vec + b_vec;
    c_vec.copy_to_slice(c);
}
```

---

## **VI. Hidden Compiler Attributes**

These are **undocumented** but used in std library:

```rust
// Compiler built-in (no implementation needed)
#[rustc_builtin_macro]
macro_rules! builtin_macro {}

// Mark as language item
#[lang = "box"]
pub struct Box<T: ?Sized>;

// Unsafe but omit checks
#[rustc_unsafe_skip_check]
unsafe fn unchecked_operation() {}

// Don't generate drop glue
#[rustc_no_drop_glue]
struct NoDrop;
```

**Diagnostic Attributes**:

```rust
// Custom error message
#[rustc_on_unimplemented(
    message = "the trait `MyTrait` is not implemented for `{Self}`",
    label = "implement `MyTrait` for this type"
)]
trait MyTrait {}

// Compiler hint
#[rustc_variance]  // Show variance information
struct Foo<'a, T> {
    data: &'a T,
}
```

---

## **VII. Attribute Macros for Testing Frameworks**

### **Custom Test Framework**

```rust
// Define custom test harness
#![feature(custom_test_frameworks)]
#![test_runner(my_runner)]

fn my_runner(tests: &[&dyn Fn()]) {
    println!("Running {} tests", tests.len());
    for test in tests {
        test();
    }
}

#[test_case]
fn test1() {
    assert_eq!(2 + 2, 4);
}
```

### **Async Test Attribute**

```rust
#[proc_macro_attribute]
pub fn async_test(_attr: TokenStream, item: TokenStream) -> TokenStream {
    let input = parse_macro_input!(item as ItemFn);
    let name = &input.sig.ident;
    let body = &input.block;
    
    let expanded = quote! {
        #[test]
        fn #name() {
            tokio::runtime::Runtime::new()
                .unwrap()
                .block_on(async #body)
        }
    };
    
    TokenStream::from(expanded)
}

// Usage:
#[async_test]
async fn test_async() {
    let result = some_async_fn().await;
    assert_eq!(result, 42);
}
```

---

## **VIII. Performance-Critical Attribute Patterns**

### **Target Features**

```rust
// Enable CPU features for this function
#[target_feature(enable = "avx2")]
unsafe fn avx2_function() {
    // Can use AVX2 instructions
}

#[target_feature(enable = "sse4.2,popcnt")]
unsafe fn multiple_features() {}

// Detect at runtime
#[cfg(any(target_arch = "x86", target_arch = "x86_64"))]
fn runtime_dispatch() {
    if is_x86_feature_detected!("avx2") {
        unsafe { avx2_function() }
    } else {
        fallback_function()
    }
}
```

**All x86_64 Features**:
- `sse`, `sse2`, `sse3`, `ssse3`, `sse4.1`, `sse4.2`
- `avx`, `avx2`, `avx512f`
- `fma`, `bmi1`, `bmi2`
- `aes`, `sha`
- `popcnt`, `lzcnt`

### **Optimization Levels Per Function**

```rust
// Force specific optimization (unstable)
#![feature(optimize_attribute)]

#[optimize(speed)]
fn hot_path() {
    // Optimize for speed
}

#[optimize(size)]
fn cold_path() {
    // Optimize for size
}
```

### **No Panic**

```rust
// Guarantee function never panics (unstable)
#![feature(never_type)]

#[no_panic]
fn guaranteed_safe() -> i32 {
    // Compiler verifies no panic paths
    42
}
```

---

## **IX. Attribute Syntax Deep Dive**

### **Meta Items**

```rust
// Word
#[test]

// Name-value
#[doc = "documentation"]

// List
#[cfg(all(unix, target_arch = "x86_64"))]

// Nested
#[derive(Debug, Clone)]

// Complex nesting
#[cfg_attr(
    all(feature = "a", feature = "b"),
    derive(SerdeA),
    serde(rename_all = "camelCase")
)]
```

### **Multiple Attributes**

```rust
// Separate lines
#[inline]
#[cold]
fn function() {}

// Combined (equivalent)
#[inline, cold]
fn function2() {}
```

### **Attribute Paths**

```rust
// Simple
#[derive(Debug)]

// Path
#[serde::rename = "customName"]

// Fully qualified
#[::std::prelude::v1::derive(Debug)]
```

---

## **X. Writing Advanced Derive Macros**

### **Complete Example: Builder Pattern**

```rust
// Proc macro crate
use proc_macro::TokenStream;
use quote::quote;
use syn::{parse_macro_input, Data, DeriveInput, Fields};

#[proc_macro_derive(Builder)]
pub fn derive_builder(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as DeriveInput);
    let name = &input.ident;
    let builder_name = format!("{}Builder", name);
    let builder_ident = syn::Ident::new(&builder_name, name.span());
    
    let fields = match &input.data {
        Data::Struct(data) => match &data.fields {
            Fields::Named(fields) => &fields.named,
            _ => panic!("Builder only supports named fields"),
        },
        _ => panic!("Builder only supports structs"),
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
            #name: self.#name.ok_or(concat!(
                "Field '", stringify!(#name), "' not set"
            ))?
        }
    });
    
    let expanded = quote! {
        pub struct #builder_ident {
            #(#builder_fields,)*
        }
        
        impl #builder_ident {
            #(#setters)*
            
            pub fn build(self) -> Result<#name, &'static str> {
                Ok(#name {
                    #(#build_fields,)*
                })
            }
        }
        
        impl #name {
            pub fn builder() -> #builder_ident {
                #builder_ident {
                    #(#name: None,)*
                }
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

### **Advanced: Custom Derive with Helper Attributes**

```rust
#[proc_macro_derive(Validate, attributes(validate))]
pub fn derive_validate(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as DeriveInput);
    
    let fields = // ... extract fields ...
    
    let validations = fields.iter().map(|f| {
        let name = &f.ident;
        let validations: Vec<_> = f.attrs.iter()
            .filter(|attr| attr.path.is_ident("validate"))
            .filter_map(|attr| parse_validate_attr(attr))
            .collect();
        
        quote! {
            #(#validations)*
        }
    });
    
    // ... generate impl
}

// Usage:
#[derive(Validate)]
struct User {
    #[validate(length(min = 3, max = 20))]
    name: String,
    
    #[validate(range(min = 0, max = 150))]
    age: u32,
    
    #[validate(email)]
    email: String,
}
```

---

## **XI. Debugging Attributes and Macros**

### **Expand Macros**

```bash
# See macro expansion
cargo expand

# Specific item
cargo expand my_function

# With features
cargo expand --features advanced
```

### **Compiler Flags**

```bash
# Show all attributes
RUSTFLAGS="-Z unpretty=expanded" cargo build

# Show HIR (High-level IR)
rustc +nightly -Z unpretty=hir src/main.rs

# Show MIR
rustc +nightly --emit mir src/main.rs
```

### **Procedural Macro Debugging**

```rust
// In proc macro
#[proc_macro_derive(Debug)]
pub fn derive_debug(input: TokenStream) -> TokenStream {
    // Print input for debugging
    eprintln!("Input: {}", input);
    
    let output = // ... generate code ...
    
    // Print output
    eprintln!("Output: {}", output);
    
    output
}
```

---

## **XII. Attribute Anti-Patterns**

### **❌ Over-inlining**

```rust
// BAD: Force inlining everything
#[inline(always)]
pub fn large_function() {
    // 1000 lines of code
}
```

**Problem**: Code bloat, slower compilation, worse cache locality.

**Solution**: Let compiler decide, or use `#[inline]` for small functions only.

### **❌ Incorrect repr**

```rust
// BAD: Using repr(C) unnecessarily
#[repr(C)]
struct PureRust {
    data: Vec<i32>,
}
```

**Problem**: Prevents compiler optimizations (field reordering).

**Solution**: Only use `repr(C)` for FFI.

### **❌ Cfg Spaghetti**

```rust
// BAD: Nested cfg everywhere
#[cfg(unix)]
#[cfg(target_arch = "x86_64")]
#[cfg(feature = "advanced")]
fn function() {}
```

**Solution**: Combine conditions:

```rust
#[cfg(all(unix, target_arch = "x86_64", feature = "advanced"))]
fn function() {}
```

---

## **XIII. The Elite Mental Model**

### **Attributes as Compiler Directives**

Think of attributes as **instructions to the compiler**:

```
Source Code + Attributes → Compiler → Optimized Binary
                  ↓
            Type System
         Code Generation
          Optimization
           Validation
```

### **The Attribute Pipeline**

```
1. Parse → AST with attributes
2. Expand attribute macros
3. Expand derive macros
4. Process built-in attributes
5. Type check
6. Borrow check
7. MIR construction (attributes affect this)
8. Optimization (inline, target_feature, etc.)
9. Code generation
```

### **Performance Model**

```rust
// Attributes control optimization at every level:

#[inline(always)]          // LLVM level
#[target_feature]          // CPU instruction level
#[repr(C)]                 // Memory layout level
#[cold]                    // Branch prediction level
```

---

## **XIV. The Complete Attribute Checklist**

**For Libraries**:
- [ ] Use `#[inline]` for small public functions
- [ ] Add `#[must_use]` to important return values
- [ ] Provide `#[derive]` macros for common traits
- [ ] Use `#[doc(cfg(...))]` to show feature requirements
- [ ] Add `#[deprecated]` when evolving APIs
- [ ] Use `#![forbid(unsafe_code)]` if possible
- [ ] Configure lints with `#![warn(...)]`

**For Performance**:
- [ ] Profile before adding `#[inline(always)]`
- [ ] Use `#[cold]` for error paths
- [ ] Consider `#[repr(C)]` cost vs FFI needs
- [ ] Use `#[target_feature]` for SIMD hot paths
- [ ] Add `#[cfg(not(debug_assertions))]` for release-only optimizations

**For Safety**:
- [ ] Use `#[forbid(unsafe_code)]` where applicable
- [ ] Add `#[track_caller]` to assertion helpers
- [ ] Use `#[must_use]` for guards and important results
- [ ] Validate feature combinations with `compile_error!`

**For Maintainability**:
- [ ] Document with `///` (which becomes `#[doc]`)
- [ ] Use `#[cfg_attr]` instead of duplicating code
- [ ] Organize tests with `#[cfg(test)]` modules
- [ ] Use feature flags judiciously

---

## **The Ultimate Truth**

Attributes are **compiler plugins**. They let you:
1. **Control** code generation (inline, repr)
2. **Extend** the language (procedural macros)
3. **Validate** at compile time (lints, deprecation)
4. **Optimize** selectively (target_feature, cold)
5. **Document** effectively (doc attributes)

Elite Rust programmers **think in attributes**. They see code and immediately know:
- Where to add `#[inline]`
- When to use `#[cold]`
- How to structure feature flags
- Which derives to provide

Attributes are not decoration—they're **semantic instructions** that transform how your code compiles and runs.

Master attributes, and you master the compiler. 🦀⚡