In Rust, checking the **byte size** of a value or type is usually done with the `std::mem::size_of` and `std::mem::size_of_val` functions from the standard library.

Here’s the breakdown:

---

### 1. **Size of a type (compile-time)**

```rust
use std::mem;

fn main() {
    println!("Size of i32: {} bytes", mem::size_of::<i32>());
    println!("Size of u64: {} bytes", mem::size_of::<u64>());
    println!("Size of f64: {} bytes", mem::size_of::<f64>());
    println!("Size of char: {} bytes", mem::size_of::<char>());
}
```

✅ `mem::size_of::<T>()` gives the **size in bytes** for type `T`.

---

### 2. **Size of a value (runtime)**

```rust
use std::mem;

fn main() {
    let x: i32 = 42;
    let arr = [1u8, 2, 3, 4, 5];

    println!("Size of x: {} bytes", mem::size_of_val(&x));
    println!("Size of arr: {} bytes", mem::size_of_val(&arr));
}
```

✅ `mem::size_of_val(&val)` returns the **size of the value at runtime**.
This is especially useful for slices, arrays, or trait objects.

---

### 3. **Heap vs Stack consideration**

* `size_of` / `size_of_val` only tell you the size of the data **on the stack**, or the size of the pointer + metadata for heap allocations.
* Example with `String`:

```rust
use std::mem;

fn main() {
    let s = String::from("Hello");
    println!("Size of String struct: {} bytes", mem::size_of_val(&s));
    println!("Length of string data: {} bytes", s.len());
    println!("Capacity of string buffer: {} bytes", s.capacity());
}
```

Output (on 64-bit system, may vary):

```
Size of String struct: 24 bytes   // stack (ptr + len + capacity)
Length of string data: 5 bytes    // heap data
Capacity of string buffer: 5 bytes
```

So:

* **Stack**: `String` itself (just 3 machine words: pointer, length, capacity).
* **Heap**: The actual characters `"Hello"` are stored here.

---

### 4. **Dynamic trait objects (`dyn Trait`)**

Trait objects are *fat pointers* → they contain:

* A pointer to the data.
* A pointer to the vtable (method resolution table).

```rust
use std::mem;

fn main() {
    let s: &dyn ToString = &123;
    println!("Size of trait object reference: {} bytes", mem::size_of_val(&s));
}
```

On 64-bit: `16 bytes` (8 for data pointer, 8 for vtable pointer).

---

🔑 **Key Takeaway:**

* `size_of::<T>()` → size of type (known at compile time).
* `size_of_val(&val)` → size of a value at runtime.
* For heap-based types (like `String`, `Vec`), the reported size is just the stack struct, not the actual heap contents. Use `.len()` or `.capacity()` for heap byte sizes.

---

Do you want me to also show you how to **measure total heap memory usage** of something like a `Vec` or `HashMap` in practice?
