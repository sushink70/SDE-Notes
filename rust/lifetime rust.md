**The core idea:** a lifetime is how long a variable is alive, from when it's created to when it's destroyed. The borrow checker uses lifetimes to make sure a reference never outlives the thing it points to.

**Lifetime vs scope**

They're related but not identical:
- **Lifetime** of a borrow is tied to where the borrowed variable (the "lender") lives. The borrow is valid only as long as the lender is still alive.
- **Scope** of a borrow is where the reference is actually used.

**Walking through the page's example**

```rust
fn main() {
    let i = 3;                      // i's lifetime starts

    {
        let borrow1 = &i;           // borrow1 starts
        println!("borrow1: {}", borrow1);
    }                               // borrow1 ends

    {
        let borrow2 = &i;           // borrow2 starts
        println!("borrow2: {}", borrow2);
    }                               // borrow2 ends
}                                   // i ends
```

- `i` lives the longest because both inner blocks sit entirely inside its lifetime.
- `borrow1` and `borrow2` never overlap, so their relative order doesn't matter.
- Both borrows end before `i` is destroyed, so the compiler accepts this.

**What would break it**

If a reference could outlive `i`, it would point to freed memory (a dangling reference), and Rust rejects that at compile time:

```rust
fn main() {
    let r;
    {
        let x = 5;
        r = &x;      // x dies at the end of this block
    }
    println!("{}", r); // error: `x` does not live long enough
}
```

**One last note from the page:** in this basic example, lifetimes have no names or labels. The compiler just tracks them silently. The next chapter (explicit annotations) introduces named lifetimes like `'a`, which you need when the compiler can't figure out relationships on its own, such as in functions that take and return references.

Want me to continue with the explicit `'a` annotations next, with Rust examples?

## What "outlive" means

**A outlives B** means A is still alive after B has been destroyed.

```rust
let a = 10;        // a is created first
{
    let b = 20;    // b is created later
}                  // b destroyed here
                   // a is still alive -> a outlives b
```

A reference is only an address that points to some data. The rule is:

> **The data must outlive every reference pointing to it.**

If the data dies first, the reference points to freed memory. That is a **dangling reference**.

## Why we need to check lifetimes

In C or C++ nothing stops you from writing this:

```c
int* get() {
    int x = 5;
    return &x;   // x is destroyed when the function returns
}                // the caller gets a pointer to dead memory
```

Using that pointer causes use-after-free bugs, crashes, security holes and random garbage values. These are some of the most common serious bugs in systems code.

Rust checks lifetimes at **compile time**, so:
- dangling references are impossible in safe Rust,
- there is no garbage collector and no runtime cost,
- the bug is caught before the program runs.

For bare-metal and systems work this matters a lot, because you get memory safety without a runtime.

## Explicit lifetime annotations `'a`

Most of the time the compiler works out lifetimes on its own. It needs your help when a function takes **multiple references** and returns one, because it can't tell which input the output is tied to.

### Syntax

```rust
fn foo<'a>(x: &'a i32) { }
```

- `<'a>` declares a lifetime named `a`. The name is arbitrary: `'a`, `'b`, `'long` all work.
- `&'a i32` means "a reference to an `i32` that lives for lifetime `'a`".

An annotation **does not change how long anything lives**. It only **describes the relationship** so the compiler can check it.

### Example 1: the problem

```rust
fn longest(x: &str, y: &str) -> &str {   // error: missing lifetime specifier
    if x.len() > y.len() { x } else { y }
}
```

The function may return `x` or `y`. The compiler doesn't know which one the result borrows from, so it can't verify the result stays valid.

### Example 2: the fix

```rust
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}
```

This says: "the returned reference is valid for as long as **both** inputs are valid." In practice `'a` becomes the **shorter** of the two input lifetimes.

### Example 3: the check in action

```rust
fn main() {
    let s1 = String::from("long string");
    let result;
    {
        let s2 = String::from("short");
        result = longest(s1.as_str(), s2.as_str());
    }                                // s2 dies here
    println!("{}", result);          // error: `s2` does not live long enough
}
```

`result` might point to `s2`, and `s2` is already dead at the `println!`. Rust rejects this.

Move the `println!` inside the inner block and it compiles:

```rust
fn main() {
    let s1 = String::from("long string");
    {
        let s2 = String::from("short");
        let result = longest(s1.as_str(), s2.as_str());
        println!("{}", result);      // s2 still alive, so this is fine
    }
}
```

### Example 4: different lifetimes when the output depends on only one input

```rust
fn first<'a, 'b>(x: &'a str, _y: &'b str) -> &'a str {
    x
}
```

The result only depends on `x`, so it is tied to `'a` alone. `y` can die earlier without causing problems.

### Example 5: lifetimes in structs

A struct holding a reference must say how long that reference lasts:

```rust
struct Parser<'a> {
    input: &'a str,
}

impl<'a> Parser<'a> {
    fn first_word(&self) -> &'a str {
        self.input.split(' ').next().unwrap_or("")
    }
}

fn main() {
    let text = String::from("hello world");
    let p = Parser { input: &text };
    println!("{}", p.first_word());
}
```

This means a `Parser` cannot outlive the string it borrows from. This pattern is very common in tokenizers and parsers, which is useful for competitive programming and systems code.

## Quick summary

| Concept | Meaning |
|---|---|
| Lifetime | How long data is alive |
| Outlive | Stay alive longer than something else |
| `'a` | A name for a lifetime, used to link references together |
| `<'a>` | Declares that name on a function, struct or impl |
| Annotation | A label for the compiler, with no effect on runtime behavior |

**Rule of thumb:** if a function returns a reference, ask "which input does this come from?" and give the output the same `'a` as that input.

The next topics in the book are **lifetime elision** (when you can skip writing `'a`), `'static`, and **lifetime bounds** like `T: 'a`. Want me to cover those next?

## 1. Lifetime elision (when you can skip writing `'a`)

Writing `'a` everywhere would be tedious, so the compiler applies **3 fixed rules** to fill them in for you. If the rules can fully determine every lifetime, you write nothing. If not, it gives an error and asks you to annotate.

### The 3 rules

**Rule 1: each reference parameter gets its own lifetime.**

```rust
fn foo(x: &str, y: &str)
// becomes
fn foo<'a, 'b>(x: &'a str, y: &'b str)
```

**Rule 2: if there is exactly one input lifetime, it is given to all output references.**

```rust
fn first_word(s: &str) -> &str
// becomes
fn first_word<'a>(s: &'a str) -> &'a str
```

**Rule 3: if one of the inputs is `&self` or `&mut self`, its lifetime is given to all output references.**

```rust
impl Parser<'_> {
    fn name(&self, other: &str) -> &str { ... }
    // output gets the lifetime of &self, not of `other`
}
```

### Why `longest` failed but `first_word` works

```rust
fn first_word(s: &str) -> &str { ... }        // OK: Rule 2 applies, one input
fn longest(x: &str, y: &str) -> &str { ... }  // error: two inputs, no &self, no rule fits
```

With two inputs, Rule 1 creates `'a` and `'b`. Rule 2 doesn't apply (not exactly one input). Rule 3 doesn't apply (no `self`). The output lifetime stays unknown, so you must write it.

**Under the hood:** elision is only a syntax shortcut. After the compiler fills in the names, the code is identical to the version you would have written by hand.

## 2. `'static`

`'static` is the longest possible lifetime: the data lives for the **entire run of the program**.

### Where `'static` data comes from

```rust
let s: &'static str = "hello";   // string literal
```

**Under the hood:** the bytes `"hello"` are stored directly in the compiled binary, in the read-only data section (`.rodata`). They're loaded into memory when the program starts and are never freed. The reference `s` points into that section, so it can never dangle. That is why it is `'static`.

```
Binary layout (simplified)
┌──────────────────┐
│ .text   (code)   │
│ .rodata ("hello")│  <- 'static data lives here
│ .data / .bss     │  <- static / global variables
└──────────────────┘
   Stack: local variables (short lifetimes)
   Heap:  Box/Vec/String data (lifetime tied to its owner)
```

### Other ways to get `'static`

```rust
static MAX: i32 = 100;           // global variable, lives forever
const NAME: &str = "rust";       // constant

let leaked: &'static mut i32 = Box::leak(Box::new(5));
// Box::leak intentionally never frees the memory, so it becomes 'static
```

`Box::leak` is common in bare-metal and embedded code, where you allocate something once at startup and keep it forever.

### Two meanings of `'static`

This confuses many people:

```rust
&'static str      // a reference that is valid for the whole program
T: 'static        // a type that contains no non-static references
```

The second form is a **bound** (section 3). An owned `String` satisfies `T: 'static`, even though it can be dropped early, because it holds **no borrowed references** that could expire.

```rust
fn needs_static<T: 'static>(_t: T) {}

fn main() {
    needs_static(String::from("owned"));   // OK: String owns its data
    needs_static(5i32);                    // OK

    let x = 10;
    // needs_static(&x);                   // error: &x borrows a local, not 'static
}
```

This is why `std::thread::spawn` requires `'static`. The new thread may outlive the function that spawned it, so it can't hold references to that function's locals.

```rust
use std::thread;

fn main() {
    let v = vec![1, 2, 3];
    // thread::spawn(|| println!("{:?}", v));   // error: closure borrows v
    thread::spawn(move || println!("{:?}", v))  // OK: v is moved into the thread
        .join()
        .unwrap();
}
```

## 3. Lifetime bounds

Bounds say "this lifetime must last at least as long as that one."

### Form 1: `T: 'a` (type outlives lifetime)

"Everything inside `T` must stay valid for at least `'a`."

```rust
struct Ref<'a, T: 'a> {
    r: &'a T,
}
```

If `T` itself contained a short-lived reference, then `&'a T` could end up pointing to something that dies before `'a`. The bound rules that out. (Since Rust 2018 the compiler infers this in structs, so `T: 'a` is usually implicit there, but you still see it in function and trait signatures.)

```rust
fn print_it<'a, T: std::fmt::Debug + 'a>(x: &'a T) {
    println!("{:?}", x);
}
```

### Form 2: `'b: 'a` (lifetime outlives lifetime)

Read it as "`'b` lives at least as long as `'a`."

```rust
fn pick<'a, 'b: 'a>(x: &'a str, y: &'b str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}
```

Here `y` has the longer lifetime `'b`. Because `'b: 'a`, the compiler knows a `&'b str` can safely be used wherever a `&'a str` is expected, so returning `y` as `&'a str` is allowed. This works because a longer-lived reference can always be treated as a shorter-lived one (this is called **subtyping** or **variance**).

### Form 3: `for<'a>` (higher-ranked bounds)

You will see this with closures:

```rust
fn call_with_ref<F>(f: F)
where
    F: for<'a> Fn(&'a str) -> &'a str,
{
    let s = String::from("hi");
    println!("{}", f(&s));
}
```

It means "`F` must work for **any** lifetime `'a` the caller picks," not just one specific lifetime. Rust writes `Fn(&str) -> &str` this way automatically through elision, so you rarely type `for<'a>` yourself.

## 4. What happens at runtime? Nothing.

This is the main under-the-hood point:

- Lifetimes exist **only at compile time**. They are checked and then **erased**.
- The generated machine code contains no lifetime information, no counters and no checks.
- A `&'a T` is just a pointer (8 bytes on a 64-bit target, 16 for `&str` or `&[T]` because they also store a length).

```rust
fn size() {
    println!("{}", std::mem::size_of::<&i32>());         // 8
    println!("{}", std::mem::size_of::<&'static i32>()); // 8, same
}
```

How the borrow checker works internally (modern Rust uses **NLL, Non-Lexical Lifetimes**):
1. The compiler builds a **control-flow graph** of your function.
2. Each reference gets a set of program points where it is **still used later**.
3. Each borrow must stay valid across those points.
4. If the owner is dropped or mutated while a borrow is still live, you get a compile error.

NLL is why this compiles even though `r` is in scope:

```rust
fn main() {
    let mut x = 5;
    let r = &x;
    println!("{}", r);   // last use of r
    x = 6;               // OK: the borrow ended at its last use, not at the end of scope
}
```

This also connects back to the first chapter's point: **scope** is where a name is visible, while the **lifetime** (as NLL computes it) is where the reference is actually still needed.

## Summary

| Topic | One-line meaning |
|---|---|
| Elision | The compiler fills in `'a` using 3 rules, so you skip writing it |
| `&'static T` | Reference valid for the whole program (e.g. data in `.rodata`) |
| `T: 'static` | `T` holds no short-lived borrows (owned types qualify) |
| `T: 'a` | Everything inside `T` lasts at least `'a` |
| `'b: 'a` | `'b` outlives `'a` |
| `for<'a>` | Works for every possible lifetime |
| Runtime cost | Zero, since lifetimes are erased after checking |

Common beginner trap: when the compiler complains about lifetimes, adding `'static` everywhere is usually the wrong fix. It tends to push the problem somewhere else. The better question is "who owns this data, and how long does the owner live?"

Want me to go on to **variance and subtyping** (why `&'long T` can be used as `&'short T`, and why `&mut T` is different), or try a few lifetime puzzles you can solve yourself?