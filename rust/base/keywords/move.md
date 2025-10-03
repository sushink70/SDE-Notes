Exactly 💡 — in Rust, the **`move` keyword** changes how a **closure** captures variables.

By default, closures **borrow** values from the environment (`&` or `&mut`).
With `move`, the closure instead **takes ownership** of the captured values.

---

## 1. Default Closure Capture (borrowing)

```rust
fn main() {
    let s = String::from("hello");

    let closure = || {
        println!("Borrowed: {}", s); // 👈 borrows `s` immutably
    };

    closure();
    println!("Still usable: {}", s); // ✅ still usable
}
```

Here, `s` is borrowed, not moved, so you can still use it after calling the closure.

---

## 2. `move` Closure Capture (ownership)

```rust
fn main() {
    let s = String::from("hello");

    let closure = move || {
        println!("Moved: {}", s); // 👈 takes ownership
    };

    closure();
    // println!("{}", s); // ❌ Error: `s` moved into closure
}
```

* The `move` keyword forces the closure to **take ownership** of `s`.
* After that, `s` is no longer accessible in the outer scope.

---

## 3. Why `move` is Useful

### a) In Threads

Closures used with `std::thread::spawn` **must be `'static`**, meaning they can’t borrow local variables. `move` fixes this by transferring ownership.

```rust
use std::thread;

fn main() {
    let s = String::from("hello");

    let handle = thread::spawn(move || {
        println!("From thread: {}", s);
    });

    handle.join().unwrap();
}
```

Without `move`, the closure would borrow `s`, which doesn’t live long enough for the thread.

---

### b) In `async` / Futures

Async tasks may outlive the scope they’re created in, so `move` ensures all captured variables are owned by the closure.

```rust
async fn example() {
    let data = String::from("async data");

    let fut = async move {
        println!("Inside future: {}", data);
    };

    fut.await;
}
```

---

## 4. Key Rules

* **Without `move`** → closure borrows environment (`&` or `&mut`).
* **With `move`** → closure takes ownership (`T`).
* `Copy` types (like integers) behave the same in both cases, because ownership copying is trivial.

---

## 🌳 Summary

* **`|| { ... }`** → captures by reference (borrow).
* **`move || { ... }`** → captures by ownership (move).
* Needed when closures may **outlive their scope** (threads, async tasks).

---

👉 Quick mental model:

* **Normal closure** = “I’ll borrow your stuff while I run.”
* **`move` closure** = “I’ll take your stuff with me, you can’t use it anymore.”

---

Would you like me to also illustrate this with an **ASCII diagram showing ownership flow (stack vs heap)** so you can see *where the values go* in `move` vs normal closures?
