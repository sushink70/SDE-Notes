**`impl` in Rust means “implement”.**

It is the keyword you use to **attach behavior (methods and associated functions) to a type**, or to make a type satisfy a trait.

### 1. Implementing methods for a type (inherent impl)

Rust has no classes. You define data with `struct` or `enum`, then add methods in an `impl` block:

```rust
struct Rectangle {
    width: u32,
    height: u32,
}

impl Rectangle {
    // Associated function (like a static method / constructor)
    fn new(width: u32, height: u32) -> Self {
        Self { width, height }
    }

    // Method (takes &self, &mut self, or self)
    fn area(&self) -> u32 {
        self.width * self.height
    }

    fn can_hold(&self, other: &Rectangle) -> bool {
        self.width > other.width && self.height > other.height
    }
}
```

You call them like this:

```rust
let rect = Rectangle::new(30, 50);
println!("Area: {}", rect.area());
```

Without the `impl` block the type would just be a bag of data with no behavior.

### 2. Implementing a trait for a type

Traits are like interfaces / protocols. When you want a type to satisfy a trait, you write:

```rust
impl TraitName for TypeName {
    // required methods go here
}
```

Example:

```rust
trait Summary {
    fn summarize(&self) -> String;
}

struct Article {
    title: String,
    content: String,
}

impl Summary for Article {
    fn summarize(&self) -> String {
        format!("{}: {}", self.title, &self.content[..50])
    }
}
```

Now any function that accepts `impl Summary` (or `&dyn Summary`) can work with `Article`.

### Why do we need `impl` at all?

| Reason                        | Explanation |
|-------------------------------|-----------|
| **Separation of data and behavior** | Data lives in the `struct`/`enum`. Behavior lives in `impl` blocks. This is the Rust way instead of classes. |
| **Multiple impl blocks**      | You can have several `impl Type { ... }` blocks (even in different modules/files). |
| **Trait implementation**      | The only way to make a type implement a trait is with `impl Trait for Type`. |
| **Orphan rule / coherence**   | Rust’s rules about who can implement what are enforced through `impl`. |
| **Clarity**                   | Seeing `impl` immediately tells you “this is where the methods live”. |

### Quick mental model

- `struct` / `enum` → **what the data looks like**
- `impl Type` → **what the type can do by itself**
- `impl Trait for Type` → **what capabilities the type gains by promising to follow a contract**

That’s why almost every non-trivial Rust type has one or more `impl` blocks.