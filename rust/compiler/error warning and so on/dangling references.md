# Dangling References

```rust
fn main() {
    let reference_to_nothing = dangle();
}

fn dangle() -> &String {
    let s = String::from("hello");

    &s
}
```

```rust
$ cargo run
   Compiling ownership v0.1.0 (file:///projects/ownership)
error[E0106]: missing lifetime specifier
 --> src/main.rs:5:16
  |
5 | fn dangle() -> &String {
  |                ^ expected named lifetime parameter
  |
  = help: this function's return type contains a borrowed value, but there is no value for it to be borrowed from
help: consider using the `'static` lifetime, but this is uncommon unless you're returning a borrowed value from a `const` or a `static`
  |
5 | fn dangle() -> &'static String {
  |                 +++++++
help: instead, you are more likely to want to return an owned value
  |
5 - fn dangle() -> &String {
5 + fn dangle() -> String {
  |

For more information about this error, try `rustc --explain E0106`.
error: could not compile `ownership` (bin "ownership") due to 1 previous error

error[E0106]: missing lifetime specifier
  --> src/main.rs:43:18
   |
43 | fn dangling() -> &String {
   |                  ^ expected named lifetime parameter
   |
   = help: this function's return type contains a borrowed value, but there is no value for it to be borrowed from
help: consider using the `'static` lifetime, but this is uncommon unless you're returning a borrowed value from a `const` or a `static`
   |
43 | fn dangling() -> &'static String {
   |                   +++++++
help: instead, you are more likely to want to return an owned value
   |
43 - fn dangling() -> &String {
43 + fn dangling() -> String {
   |
```

## What's Actually Happening

Forget the compiler jargon for a second. Think of it like this:

**The function creates a variable `s`, then tries to return a pointer to it. But the moment the function ends, `s` is destroyed. So you'd be pointing to memory that no longer exists.** That's a "dangling reference" — a pointer to a ghost.

```rust
fn dangling() -> &String {
    let s = String::from("Hello");  // s is born here
    &s                              // you return a pointer to s...
}                                   // ...but s DIES here. Pointer now points to nothing.
```

In C/C++, this compiles and causes mysterious crashes. **Rust refuses to let this happen at compile time.** That's the whole point of the error.

---

## Reading the Error, Line by Line

```
error[E0106]: missing lifetime specifier
```
> "You're returning a reference (`&String`), but I don't know *how long* that reference is valid for."

```
= help: this function's return type contains a borrowed value,
  but there is no value for it to be borrowed from
```
> "A reference must point to *something*. But the thing it would point to (`s`) dies when the function ends. So there's nothing left to borrow from."

---

## The Fix

The compiler itself tells you: **just return an owned value, not a reference.**

```rust
// ❌ Wrong — trying to return a reference to a local variable
fn dangling() -> &String {
    let s = String::from("Hello");
    &s
}

// ✅ Correct — transfer ownership out of the function
fn dangling() -> String {
    let s = String::from("Hello");
    s  // move s out, don't borrow it
}
```

When you return `s` directly (not `&s`), you're **transferring ownership** to the caller. Nothing gets destroyed prematurely.

---

## The Mental Model

| Concept | Think of it as |
|---|---|
| `String` | You own a house |
| `&String` | You lend someone your house key |
| The bug | You demolish the house, but the key still exists |
| Rust's fix | Either keep the house alive, or don't give out keys |

**The `'static` suggestion** the compiler makes is a red herring for your case — ignore it. It's for very specific scenarios (like string literals hardcoded in the binary). Your fix is simply `-> String`.

```rust
fn main() {
    let d_pointer = dangling();
}

fn dangling() -> &'static String {
    let s = String::from("Helloe");
    &s
}
```

```
error[E0515]: cannot return reference to local variable `s`
  --> src/main.rs:45:5
   |
45 |     &s
   |     ^^ returns a reference to data owned by the current function
```
## You Followed the Wrong Suggestion

The compiler gave you two options last time. You picked the **wrong one** — the one it literally said was "uncommon."

---

## What `'static` Actually Means

`'static` means **"this reference lives for the entire duration of the program."**

For that to work, the data must exist *forever* — like a value baked into the binary at compile time.

```rust
// ✅ This is 'static — hardcoded into the binary, lives forever
let s: &'static str = "Hello";

// ❌ This is NOT 'static — created at runtime, dies when function ends
let s = String::from("Hello");
```

`String::from(...)` is **runtime-allocated** (lives on the heap). It has an owner. It gets dropped. It can **never** be `'static`.

So you told Rust *"trust me, this lives forever"* — and Rust checked, saw it definitely doesn't, and errored again.

---

## The Only Real Fix

The compiler told you this the first time too — it's the second suggestion:

```rust
// ✅ Just return the owned String
fn dangling() -> String {
    let s = String::from("Hello");
    s
}
```

That's it. No `&`, no lifetime annotation needed.

---

## One-Line Rule to Remember

> **If you created it inside the function → return it owned, never as a reference.**

References are for borrowing things that **already exist somewhere else** and will **outlive the borrow.** A local variable qualifies as neither.