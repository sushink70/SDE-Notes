Good question 👍

If you **don’t use the `struct Celsius; struct Fahrenheit;` markers**, your code will still *work*, but you’ll lose the **type safety** that those zero-sized structs are giving you. Let’s break it down:

---

### 🔹 With `Celsius` and `Fahrenheit` structs

```rust
fn convert_to_celsius(temp: f64, _marker: Fahrenheit) -> (f64, Celsius) { ... }
fn convert_to_fahrenheit(temp: f64, _marker: Celsius) -> (f64, Fahrenheit) { ... }
```

* The compiler **forces you** to pass the right unit marker:

  ```rust
  convert_to_celsius(77.0, Fahrenheit);   // ✅ correct
  convert_to_celsius(77.0, Celsius);      // ❌ compile-time error
  ```
* You can’t accidentally swap units (say, passing Celsius where Fahrenheit is expected).
* This is known as a **zero-cost phantom type marker** → no runtime overhead, but strong **type-level guarantees**.

---

### 🔹 Without `Celsius` and `Fahrenheit`

```rust
fn convert_to_celsius(temp: f64) -> f64 {
    (temp - 32.0) * 5.0 / 9.0
}

fn convert_to_fahrenheit(temp: f64) -> f64 {
    temp * 9.0 / 5.0 + 32.0
}
```

* Much simpler code ✅.
* But **any `f64` can be passed**:

  ```rust
  let wrong = convert_to_celsius(25.0); // This compiles!
  // but 25 was Celsius, not Fahrenheit → gives wrong result
  ```
* You lose **compiler-enforced unit safety**, so it’s easy to make logic mistakes.

---

### ⚖️ Trade-off

* **Without structs** → simple, less boilerplate, but error-prone.
* **With structs** → slightly more verbose, but prevents mixing units at compile time.

---

👉 In fact, Rust has a pattern for this called **"newtype pattern"** or **"phantom types"**. You could even define:

```rust
struct Celsius(f64);
struct Fahrenheit(f64);

fn to_fahrenheit(c: Celsius) -> Fahrenheit {
    Fahrenheit(c.0 * 9.0 / 5.0 + 32.0)
}
```

Now you literally cannot pass a wrong number, since only the correct type fits.

---

Do you want me to show you a **phantom type generic version** (using `PhantomData<T>`) where you can scale this idea for many units (Kelvin, meters, seconds, etc.)?
