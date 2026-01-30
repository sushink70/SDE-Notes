# Comprehensive Guide to Derivable Traits in Rust

Derivable traits are Rust's mechanism for automatic trait implementation via the `#[derive]` attribute. This is a powerful metaprogramming feature that generates boilerplate code at compile time.

## Core Derivable Traits

### 1. **Debug**

Enables formatted output for debugging via `{:?}` and `{:#?}`.

```rust
#[derive(Debug)]
struct User {
    id: u64,
    name: String,
    email: String,
}

fn main() {
    let user = User {
        id: 1,
        name: "Alice".to_string(),
        email: "alice@example.com".to_string(),
    };
    
    println!("{:?}", user);        // Single-line
    println!("{:#?}", user);       // Pretty-printed
}
```

**Requirements**: All fields must implement `Debug`.

---

### 2. **Clone**

Creates deep copies of values.

```rust
#[derive(Clone, Debug)]
struct Point {
    x: f64,
    y: f64,
}

#[derive(Clone, Debug)]
struct Shape {
    center: Point,
    vertices: Vec<Point>,
}

fn main() {
    let shape1 = Shape {
        center: Point { x: 0.0, y: 0.0 },
        vertices: vec![Point { x: 1.0, y: 1.0 }],
    };
    
    let shape2 = shape1.clone(); // Deep clone
}
```

**Key Points**:
- All fields must implement `Clone`
- Heap-allocated data (Vec, String, Box) is cloned recursively
- Can be expensive for large structures

---

### 3. **Copy**

Enables bitwise copying for simple types (stack-only).

```rust
#[derive(Copy, Clone, Debug)]
struct Point {
    x: i32,
    y: i32,
}

fn main() {
    let p1 = Point { x: 1, y: 2 };
    let p2 = p1; // Bitwise copy, p1 still valid
    
    println!("{:?} {:?}", p1, p2);
}
```

**Requirements**:
- Must also derive `Clone`
- All fields must be `Copy`
- Cannot contain heap-allocated data (no `String`, `Vec`, `Box`)
- Types: primitives, fixed-size arrays, tuples of `Copy` types

**Copy vs Clone Decision Tree**:
```rust
// Copy: Small, stack-only types
#[derive(Copy, Clone)]
struct Color(u8, u8, u8);

// Clone only: Contains heap data
#[derive(Clone)]
struct User {
    name: String,  // Heap-allocated
}
```

---

### 4. **PartialEq & Eq**

Enable equality comparisons.

```rust
#[derive(PartialEq, Eq, Debug)]
struct User {
    id: u64,
    name: String,
}

fn main() {
    let u1 = User { id: 1, name: "Alice".to_string() };
    let u2 = User { id: 1, name: "Alice".to_string() };
    
    assert_eq!(u1, u2); // Structural equality
}
```

**Differences**:
- **PartialEq**: Allows partial equality (e.g., `f64` with `NaN`)
- **Eq**: Requires total equality (reflexive, symmetric, transitive)

```rust
// PartialEq only (contains f64)
#[derive(PartialEq, Debug)]
struct Point {
    x: f64,
    y: f64,
}

// Can derive Eq (no floats)
#[derive(PartialEq, Eq, Debug)]
struct Id {
    value: u64,
}
```

**Custom field-level comparison**:
```rust
#[derive(PartialEq)]
struct User {
    #[allow(dead_code)]
    id: u64,
    name: String,
}
// Compares ALL fields by default
```

---

### 5. **PartialOrd & Ord**

Enable ordering comparisons.

```rust
#[derive(PartialOrd, Ord, PartialEq, Eq, Debug)]
struct Priority {
    level: u8,
    timestamp: u64,
}

fn main() {
    let p1 = Priority { level: 1, timestamp: 100 };
    let p2 = Priority { level: 2, timestamp: 50 };
    
    assert!(p1 < p2); // Compares fields in order
}
```

**Requirements**:
- `Ord` requires `Eq` and `PartialOrd`
- `PartialOrd` requires `PartialEq`

**Field Ordering**: Compares fields in declaration order (lexicographic).

```rust
#[derive(PartialOrd, Ord, PartialEq, Eq)]
struct Task {
    priority: u8,    // Compared first
    created_at: u64, // Compared second (tiebreaker)
}
```

---

### 6. **Hash**

Enables use in hash-based collections (`HashMap`, `HashSet`).

```rust
use std::collections::HashSet;

#[derive(Hash, PartialEq, Eq, Debug)]
struct UserId(u64);

fn main() {
    let mut users = HashSet::new();
    users.insert(UserId(1));
    users.insert(UserId(2));
    
    assert!(users.contains(&UserId(1)));
}
```

**Requirements**:
- Must also implement `Eq`
- Hash consistency: `k1 == k2` implies `hash(k1) == hash(k2)`

---

### 7. **Default**

Provides sensible default values.

```rust
#[derive(Default, Debug)]
struct Config {
    host: String,       // ""
    port: u16,          // 0
    timeout: Option<u64>, // None
}

fn main() {
    let config = Config::default();
    println!("{:?}", config);
}
```

**Field Requirements**:
- All fields must implement `Default`
- Common defaults: `""`, `0`, `false`, `None`, `vec![]`

**Custom defaults with builder pattern**:
```rust
#[derive(Default)]
struct Server {
    #[default]
    host: String,
}

// Or manually implement for custom logic
impl Default for Server {
    fn default() -> Self {
        Self {
            host: "localhost".to_string(),
        }
    }
}
```

---

## Advanced Derivable Traits

### 8. **serde::{Serialize, Deserialize}**

From `serde` crate - JSON/binary serialization.

```rust
use serde::{Serialize, Deserialize};

#[derive(Serialize, Deserialize, Debug)]
struct User {
    id: u64,
    name: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    email: Option<String>,
}

fn main() -> Result<(), serde_json::Error> {
    let user = User {
        id: 1,
        name: "Alice".to_string(),
        email: None,
    };
    
    let json = serde_json::to_string(&user)?;
    let deserialized: User = serde_json::from_str(&json)?;
    
    Ok(())
}
```

**Powerful attributes**:
```rust
#[derive(Serialize, Deserialize)]
struct ApiResponse {
    #[serde(rename = "user_id")]
    id: u64,
    
    #[serde(default)]
    status: String,
    
    #[serde(skip)]
    internal_cache: Vec<String>,
    
    #[serde(flatten)]
    metadata: Metadata,
}
```

---

## Custom Derive Macros

Create your own derivable traits using procedural macros.

```rust
// In a separate proc-macro crate
use proc_macro::TokenStream;
use quote::quote;
use syn::{parse_macro_input, DeriveInput};

#[proc_macro_derive(Builder)]
pub fn derive_builder(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as DeriveInput);
    let name = &input.ident;
    let builder_name = format!("{}Builder", name);
    let builder_ident = syn::Ident::new(&builder_name, name.span());
    
    // Generate builder implementation
    let expanded = quote! {
        impl #name {
            pub fn builder() -> #builder_ident {
                #builder_ident::default()
            }
        }
    };
    
    TokenStream::from(expanded)
}
```

---

## Trait Bounds & Derive Dependencies

Understanding which traits depend on others:

```rust
// Dependency chain
#[derive(Copy)]      // Requires: Clone
#[derive(Clone)]
struct Point(i32, i32);

#[derive(Ord)]       // Requires: Eq, PartialOrd
#[derive(PartialOrd)] // Requires: PartialEq
#[derive(Eq)]        // Requires: PartialEq
#[derive(PartialEq)]
struct Priority(u8);

#[derive(Hash)]      // Requires: Eq
#[derive(Eq, PartialEq)]
struct Id(u64);
```

---

## Performance Considerations

### Memory Layout
```rust
// Derive affects struct layout indirectly via trait bounds
#[derive(Copy, Clone)]
#[repr(C)] // Explicit layout control
struct Efficient {
    a: u64,  // 8 bytes
    b: u32,  // 4 bytes
    c: u16,  // 2 bytes
    d: u8,   // 1 byte
    // + 1 byte padding = 16 bytes total
}
```

### Clone Performance
```rust
#[derive(Clone)]
struct Expensive {
    data: Vec<u64>, // Heap allocation on clone
}

#[derive(Clone)]
struct Cheap {
    data: [u64; 4], // Stack copy
}
```

---

## Common Patterns & Best Practices

### 1. **Standard Derive Bundle**
```rust
#[derive(Debug, Clone, PartialEq, Eq)]
struct StandardEntity {
    id: u64,
    name: String,
}
```

### 2. **Value Types (Small, Immutable)**
```rust
#[derive(Debug, Copy, Clone, PartialEq, Eq, Hash)]
struct UserId(u64);
```

### 3. **API DTOs (Data Transfer Objects)**
```rust
use serde::{Serialize, Deserialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
struct ApiUser {
    id: u64,
    username: String,
}
```

### 4. **Configuration Structs**
```rust
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
struct AppConfig {
    #[serde(default = "default_port")]
    port: u16,
}

fn default_port() -> u16 { 8080 }
```

### 5. **Newtype Pattern**
```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
struct Meters(f64);

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
struct Seconds(f64);

// Type safety: can't mix meters and seconds
```

---

## Derive Limitations & Manual Implementations

Some traits CANNOT be derived:

```rust
// Cannot derive Display - must implement manually
struct User {
    name: String,
}

impl std::fmt::Display for User {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(f, "User: {}", self.name)
    }
}

// Cannot derive Drop - custom cleanup logic
impl Drop for User {
    fn drop(&mut self) {
        println!("Cleaning up user: {}", self.name);
    }
}
```

---

## Conditional Derives with Feature Flags

```rust
#[derive(Debug, Clone)]
#[cfg_attr(feature = "serde", derive(Serialize, Deserialize))]
struct Data {
    value: String,
}
```

---

## Summary Table

| Trait | Purpose | Requires | Use Case |
|-------|---------|----------|----------|
| `Debug` | Formatting | - | Development, logging |
| `Clone` | Deep copy | - | Duplicate ownership |
| `Copy` | Bitwise copy | `Clone` | Primitives, small types |
| `PartialEq` | Equality | - | Comparisons |
| `Eq` | Total equality | `PartialEq` | HashMap keys |
| `PartialOrd` | Ordering | `PartialEq` | Sorting |
| `Ord` | Total ordering | `Eq`, `PartialOrd` | BTreeMap keys |
| `Hash` | Hashing | `Eq` | HashMap/HashSet |
| `Default` | Default values | - | Builders, constructors |

---

## Key Takeaways

1. **Derive is compile-time code generation** - zero runtime cost
2. **Trait dependencies matter** - derive order affects what's possible
3. **Not everything can be derived** - some traits require manual implementation
4. **Performance varies** - `Copy` is cheap, `Clone` can be expensive
5. **Composition over inheritance** - traits are Rust's polymorphism mechanism

The derive macro is one of Rust's most powerful features, enabling clean, maintainable code without sacrificing performance or type safety.