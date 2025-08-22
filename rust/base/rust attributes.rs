Alright — here’s your **Rust Attributes Cheat Sheet** 📜.
I’ll organize it so you can quickly scan, learn, and use them without digging through docs every time.

---

# **Rust Attributes Cheat Sheet**

## **1. Crate-Level Attributes (Inner Attributes)**

Applied at the **top of the file** with `#![...]` and affect the entire crate.

| Attribute                     | Purpose                                        | Example                          |
| ----------------------------- | ---------------------------------------------- | -------------------------------- |
| `#![crate_type = "lib"]`      | Sets crate type (`bin`, `lib`, `cdylib`, etc.) | `#![crate_type = "bin"]`         |
| `#![crate_name = "my_crate"]` | Sets the name of the crate                     | `#![crate_name = "hello_world"]` |
| `#![no_std]`                  | Compile without Rust standard library          | `#![no_std]`                     |
| `#![feature(...)]`            | Enable unstable nightly features               | `#![feature(async_closure)]`     |
| `#![deny(...)]`               | Turn warnings into errors                      | `#![deny(warnings)]`             |
| `#![allow(...)]`              | Silence certain warnings globally              | `#![allow(dead_code)]`           |

---

## **2. Conditional Compilation**

Control which code gets compiled.

| Attribute                      | Purpose                                      | Example                                                    |
| ------------------------------ | -------------------------------------------- | ---------------------------------------------------------- |
| `#[cfg(...)]`                  | Compile code if condition matches            | `#[cfg(unix)] fn run_on_unix() {}`                         |
| `#[cfg_attr(condition, attr)]` | Apply an attribute only if condition matches | `#[cfg_attr(debug_assertions, derive(Debug))]`             |
| `#[cfg(any(...))]`             | Logical OR for conditions                    | `#[cfg(any(windows, unix))]`                               |
| `#[cfg(all(...))]`             | Logical AND for conditions                   | `#[cfg(all(target_os = "linux", target_arch = "x86_64"))]` |
| `#[cfg(not(...))]`             | Negation                                     | `#[cfg(not(debug_assertions))]`                            |

---

## **3. Lint Control**

Manage compiler warnings/errors.

| Attribute        | Purpose                                  | Example                     |
| ---------------- | ---------------------------------------- | --------------------------- |
| `#[allow(...)]`  | Allow something without warning          | `#[allow(dead_code)]`       |
| `#[warn(...)]`   | Show as warning                          | `#[warn(missing_docs)]`     |
| `#[deny(...)]`   | Show as error                            | `#[deny(unused_variables)]` |
| `#[forbid(...)]` | Forbid completely (cannot be overridden) | `#[forbid(unsafe_code)]`    |

**Common lint names:**

* `dead_code`
* `unused_variables`
* `unused_imports`
* `missing_docs`
* `unsafe_code`

---

## **4. Derive Traits Automatically**

Saves you from manually implementing traits.

| Attribute        | Purpose               | Example                                                              |
| ---------------- | --------------------- | -------------------------------------------------------------------- |
| `#[derive(...)]` | Auto-implement traits | `#[derive(Debug, Clone, PartialEq)] struct Point { x: i32, y: i32 }` |

**Common derive traits:**

* `Debug`
* `Clone`
* `Copy`
* `PartialEq`, `Eq`
* `PartialOrd`, `Ord`
* `Hash`
* `Default`

---

## **5. Function and Performance Attributes**

Control inlining, optimization, etc.

| Attribute                           | Purpose                   | Example                              |
| ----------------------------------- | ------------------------- | ------------------------------------ |
| `#[inline]`                         | Hint compiler to inline   | `#[inline] fn fast() {}`             |
| `#[inline(always)]`                 | Force inline              | `#[inline(always)]`                  |
| `#[inline(never)]`                  | Prevent inlining          | `#[inline(never)]`                   |
| `#[cold]`                           | Function rarely called    | `#[cold] fn error_handler() {}`      |
| `#[target_feature(enable = "...")]` | Use CPU-specific features | `#[target_feature(enable = "sse2")]` |

---

## **6. Representation & Memory Layout**

Affects how structs/enums are stored in memory.

| Attribute                     | Purpose                     | Example                                                  |
| ----------------------------- | --------------------------- | -------------------------------------------------------- |
| `#[repr(C)]`                  | C-compatible memory layout  | `#[repr(C)] struct MyCStruct { x: i32, y: i32 }`         |
| `#[repr(packed)]`             | Remove padding              | `#[repr(packed)] struct Packed { a: u8, b: u32 }`        |
| `#[repr(align(N))]`           | Force alignment             | `#[repr(align(8))] struct Aligned(u8);`                  |
| `#[repr(u8)]`, `#[repr(i32)]` | Set enum integer type       | `#[repr(u8)] enum Color { Red, Green }`                  |
| `#[non_exhaustive]`           | Prevent exhaustive matching | `#[non_exhaustive] pub struct Config { pub field: i32 }` |

---

## **7. Testing & Benchmarking**

Mark functions as tests or benchmarks.

| Attribute         | Purpose                         | Example                                           |
| ----------------- | ------------------------------- | ------------------------------------------------- |
| `#[test]`         | Marks test function             | `#[test] fn it_works() { assert_eq!(2+2, 4); }`   |
| `#[ignore]`       | Skip test unless explicitly run | `#[ignore]`                                       |
| `#[should_panic]` | Test must panic                 | `#[should_panic(expected = "fail")]`              |
| `#[bench]`        | Benchmark function (nightly)    | `#[bench] fn bench_something(b: &mut Bencher) {}` |

---

## **8. Documentation**

Affect generated docs (`cargo doc`).

| Attribute        | Purpose        | Example                         |
| ---------------- | -------------- | ------------------------------- |
| `#[doc = "..."]` | Set doc text   | `#[doc = "Custom doc string"]`  |
| `#[doc(hidden)]` | Hide from docs | `#[doc(hidden)] fn secret() {}` |

---

## **9. Safety & Security**

Control unsafe code and behaviors.

| Attribute                                    | Purpose               | Example                                       |
| -------------------------------------------- | --------------------- | --------------------------------------------- |
| `#[no_mangle]`                               | Prevent name mangling | `#[no_mangle] pub extern "C" fn my_func() {}` |
| `#[unsafe(no_critical_section)]` *(nightly)* | Unsafe restrictions   | Experimental                                  |

---

## **🔟 Procedural Macros (Custom Attributes)**

From libraries (e.g., Rocket, Serde).

| Attribute                   | Purpose                   | Example                                                                    |
| --------------------------- | ------------------------- | -------------------------------------------------------------------------- |
| `#[tokio::main]`            | Async runtime entry point | `#[tokio::main] async fn main() {}`                                        |
| `#[serde(rename = "name")]` | Serialization rules       | `#[derive(Serialize)] struct User { #[serde(rename = "n")] name: String }` |
| `#[route(GET, "/")]`        | Web route in Rocket       | `#[route(GET, "/")] fn index() {}`                                         |

---

## **11. Rare / Special**

* `#[panic_handler]` – Define custom panic behavior in `no_std`
* `#[global_allocator]` – Set a custom memory allocator
* `#[link(name = "...")]` – Link to external libraries

---

💡 **Pro Tip:** You can list all built-in attributes via:

```bash
rustc -W help
```

This shows every lint and attribute your compiler supports.

---

If you want, I can make you an **interactive mind map of Rust attributes** so you can visually navigate them and remember better — it’s far easier to recall than a flat list.
Do you want me to prepare that next?

Alright — let’s break **Rust attributes** down into **plain, no-buzzword English** and also peek under the hood at how they really work.

---

## **1️⃣ What They Are**

Think of Rust **attributes** as **instructions to the compiler** — little sticky notes you attach to your code saying:

> "Hey compiler, treat this thing in a special way."

They **don’t** run at runtime (except for procedural macros),
they’re **read by the compiler before code is compiled**,
and they can **change the compilation process** — not the logic you wrote.

---

## **2️⃣ How They Work Internally**

Here’s what happens step-by-step when you use an attribute:

1. **Parsing Stage**
   When Rust reads your code, it also parses the attributes attached to items like structs, functions, modules, or the whole crate.

2. **Metadata Interpretation**
   Each attribute tells the compiler (or a procedural macro) something:

   * *Enable or disable warnings*
   * *Generate extra code*
   * *Change how memory is laid out*
   * *Include/exclude this code for certain platforms*

3. **Code Transformation (Optional)**

   * Built-in attributes (`#[inline]`, `#[cfg]`, `#[repr(C)]`) are handled directly by **the compiler’s own logic**.
   * Custom attributes (`#[derive(Serialize)]`, `#[tokio::main]`) are handled by **procedural macros**, which are little programs that **rewrite your code** before compilation.

4. **Final Compilation**
   After attributes are applied, the compiler continues normally — now with possibly **added, removed, or altered code** based on those attributes.

---

## **3️⃣ Example: Behind the Scenes**

### Example 1: Built-in Attribute

```rust
#[inline(always)]
fn fast_add(a: i32, b: i32) -> i32 {
    a + b
}
```

* During compilation, Rust marks this function with an **"always inline"** hint in the machine code generation stage.
* The function call might **disappear** entirely — replaced by its body wherever it’s called.

---

### Example 2: Conditional Compilation

```rust
#[cfg(target_os = "windows")]
fn os_specific() {
    println!("Windows code");
}
```

* When compiling for Linux, the compiler **skips** this function entirely — as if it never existed.
* This changes the code flow **before** compilation finishes.

---

### Example 3: Procedural Macro

```rust
#[derive(Debug)]
struct User {
    name: String,
}
```

* `#[derive(Debug)]` runs a macro **before compilation** that generates:

  ```rust
  impl std::fmt::Debug for User {
      fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
          write!(f, "User {{ name: {:?} }}", self.name)
      }
  }
  ```
* The compiler then sees **both** your original struct and the generated `impl`.

---

## **4️⃣ How They Affect Code Flow**

* **They don’t change runtime behavior directly** (unless they generate code).
* They **alter what code gets compiled** or **how it gets compiled**.
* This means they influence:

  * Whether a function even exists in the compiled program.
  * How structs are stored in memory.
  * What warnings or errors you get.
  * How fast code runs (via inlining, optimizations).
  * Whether extra helper code is generated for you.

---

## **5️⃣ Quick Analogy**

Imagine you’re giving a chef (the compiler) a recipe (your code).
Attributes are **sticky notes** on the recipe:

* "Cook this dish only if the customer is from Windows." → `#[cfg(windows)]`
* "Please slice ingredients in a C-compatible way." → `#[repr(C)]`
* "Always mix these two steps together." → `#[inline(always)]`
* "Add secret sauce using this macro." → `#[derive(Debug)]`

The chef **changes how they cook** before starting — they don’t change it in the middle of serving.

---

If you want, I can make you a **step-by-step visual diagram** showing exactly how attributes flow through the Rust compilation pipeline — from parsing to code generation — so you can see how they "hook" into the process.
That would make the internal flow much clearer.

Do you want me to create that?
