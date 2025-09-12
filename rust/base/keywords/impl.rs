Exactly ✅ — in Rust, **`impl`** is used to **implement functionality** for a type.
It has two main uses:

---

# 1. **Inherent Implementation** (methods directly on a type)

This is when you define methods that **belong only to that type** (not tied to a trait).

```rust
struct Rectangle {
    width: u32,
    height: u32,
}

impl Rectangle {
    // Inherent method
    fn area(&self) -> u32 {
        self.width * self.height
    }

    // Associated function (like a "static method")
    fn new(width: u32, height: u32) -> Self {
        Self { width, height }
    }
}

fn main() {
    let rect = Rectangle::new(10, 20);
    println!("Area: {}", rect.area());
}
```

* `rect.area()` → method call
* `Rectangle::new()` → associated function (no `self`)

---

# 2. **Trait Implementation**

This is when you implement behavior defined by a **trait** for a type.
It’s how Rust does **polymorphism**.

```rust
trait Speak {
    fn speak(&self);
}

struct Dog;

impl Speak for Dog {
    fn speak(&self) {
        println!("Woof!");
    }
}

fn main() {
    let d = Dog;
    d.speak(); // Calls the trait method
}
```

Here:

* `Speak` defines the contract.
* `impl Speak for Dog` provides the actual behavior.

---

# 3. **Generic Implementations**

You can combine `impl` with generics and trait bounds:

```rust
struct Pair<T> {
    x: T,
    y: T,
}

impl<T: std::fmt::Debug> Pair<T> {
    fn print(&self) {
        println!("x = {:?}, y = {:?}", self.x, self.y);
    }
}
```

* Works for any `T` that implements `Debug`.

---

# 4. **Blanket Implementations**

Traits can be implemented for *all* types that satisfy a condition.

```rust
trait Hello {
    fn hello(&self);
}

// Blanket impl for all T that implements Display
impl<T: std::fmt::Display> Hello for T {
    fn hello(&self) {
        println!("Hello, {}", self);
    }
}

fn main() {
    123.hello();      // works!
    "world".hello();  // works!
}
```

---

# 🌳 Summary

* **`impl Type { ... }`** → inherent methods (like class methods in OOP).
* **`impl Trait for Type { ... }`** → implement a trait’s contract for a type.
* **`impl<T> Type<T> { ... }`** → generic implementations.
* **Blanket impl** → one impl for many types at once.

---

👉 Mental model:

* `impl` = “attach functionality”
* Inherent impl = only for this type.
* Trait impl = plug this type into a shared behavior contract.

---

Would you like me to also compare **`impl` vs `trait`** with an OOP analogy (like classes vs interfaces) — since many people coming from Java/Python/C++ get confused there?
