# Mastering Chaining in Rust — A Complete Guide

> **What "chaining" means here:** writing `a.b().c().d()` so that each step's output becomes the next step's input. In Rust this single syntax covers *five different mechanisms*. Most confusion disappears once you can tell which one you are looking at.

**How to use this guide:** read Part 1–2 first (the mental model), then work through Parts 3–8 with the compiler open. Parts 9–10 show production-style code. Part 11 teaches you to learn *anything new* by reading documentation. Part 12 is a practice plan.

> **Note on code provenance.** Snippets marked *"pattern from `<crate>`"* are written to match how that crate's public API is used in real projects. They are not copied verbatim from those repositories; check the crate version on docs.rs, because APIs evolve. Blocks that contain a `fn main` and use only the standard library are meant to compile as-is.

---

## Table of Contents

1. [The five kinds of chaining](#1-the-five-kinds-of-chaining)
2. [The mental model](#2-the-mental-model)
3. [Language foundations chains depend on](#3-language-foundations-chains-depend-on)
4. [Option and Result chaining (the "railway")](#4-option-and-result-chaining-the-railway)
5. [Iterator chaining (the "assembly line")](#5-iterator-chaining-the-assembly-line)
6. [Builder chaining](#6-builder-chaining)
7. [Error-context chaining](#7-error-context-chaining)
8. [Async, streams and middleware chaining](#8-async-streams-and-middleware-chaining)
9. [Production-style examples, explained](#9-production-style-examples-explained)
10. [Writing your own chainable APIs](#10-writing-your-own-chainable-apis)
11. [How to read the docs and source to learn any chain](#11-how-to-read-the-docs-and-source-to-learn-any-chain)
12. [Pitfalls, debugging, style, and a practice plan](#12-pitfalls-debugging-style-and-a-practice-plan)
13. [Cheat sheets](#13-cheat-sheets)

---

## 1. The five kinds of chaining

| # | Kind | Shape of each step | Typical example |
|---|------|--------------------|-----------------|
| 1 | **Railway** (Option/Result combinators) | `Option<T> -> Option<U>` | `.map()`, `.and_then()`, `?` |
| 2 | **Adapter pipeline** (iterators) | `Iterator -> new Iterator` (lazy) | `.filter().map().collect()` |
| 3 | **Builder** | `Builder -> Builder` (or `&mut Builder`) | `Client::builder().timeout(..).build()` |
| 4 | **Future/Stream pipeline** | `Future -> Future` | `.send().await?.json().await?` |
| 5 | **Layering** (middleware/decorators) | `Service -> wrapped Service` | `ServiceBuilder::new().layer(..).layer(..)` |

All five share one trick: **every method returns something that has more methods.** What differs is *what is returned* and *whether work happens now or later.* That is the whole subject.

---

## 2. The mental model

### 2.1 Think "pipe with typed pipe-ends"

```
 value ──► [step 1] ──► value' ──► [step 2] ──► value'' ──► [step 3] ──► result
          T → U               U → V              V → W
```

Rules that always hold:

1. **The output type of step *n* must be the input (`self`) type of step *n+1*.** If a chain fails to compile, one pipe-end doesn't match.
2. **Each `.method()` is a function whose first argument is the thing on the left.** `x.f(y)` is sugar for `Type::f(x, y)`.
3. **The kind of `self` tells you what the chain does to ownership:**

| Method signature starts with | Meaning in a chain |
|------------------------------|--------------------|
| `self` | **Consumes** the left value and hands you a new one. The old one is gone. |
| `&self` | Peeks. Returns something usually *borrowed from* the left value. |
| `&mut self` | Mutates in place. May return `&mut Self` so you can keep chaining on the same object. |

### 2.2 The three-question habit

Before and while writing any chain, ask:

1. **What type do I have right now?** (Write it in a comment if unsure.)
2. **What does the next method take, and what does it return?** (Read the signature.)
3. **Is anything lazy?** (Iterators and futures do nothing until driven.)

### 2.3 The railway picture (Option / Result)

```
          map / and_then / ?
Ok(v) ═══●════●════●════════════►  Ok(final)        happy track
          │    │    │
          ▼    ▼    ▼   (any step can switch tracks; it never switches back)
Err(e) ──────────────────────────► Err(e)           failure track
```

Once on the `Err`/`None` track, remaining steps are skipped and the error rides to the end. That is why long chains do not need `if` checks at every step.

### 2.4 The assembly-line picture (Iterators)

```
 source ──► filter ──► map ──► take(3) ──► collect()
 (lazy)     (lazy)    (lazy)    (lazy)      (CONSUMER: pulls items through)
```

Nothing moves until the consumer at the end *pulls*. Each item travels the entire line before the next one starts (no big intermediate collections). That is why `iter().map(..).filter(..)` compiles down to a tight loop.

### 2.5 The Russian-doll picture (Layers / adapters)

Each adapter *wraps* the previous one in a new struct:

```
Take<Map<Filter<Range<u32>>>>
```

Method chaining on iterators builds this nested type at compile time. The compiler inlines it, so abstraction cost is generally near zero. That is also why error messages show monstrous types: they are literally the chain written as a type.

### 2.6 See the machinery: what `map` actually is

Simplified from the standard library (real code has more attributes and traits):

```rust
// Option::map — a match, nothing more
impl<T> Option<T> {
    pub fn map<U, F: FnOnce(T) -> U>(self, f: F) -> Option<U> {
        match self {
            Some(x) => Some(f(x)),
            None => None,
        }
    }
}

// Iterator::map — returns a *wrapper struct*, does no work yet
pub struct Map<I, F> { iter: I, f: F }

impl<B, I: Iterator, F: FnMut(I::Item) -> B> Iterator for Map<I, F> {
    type Item = B;
    fn next(&mut self) -> Option<B> {
        self.iter.next().map(&mut self.f) // pull one from upstream, transform it
    }
}
```

Internalize this and you can predict behavior of every adapter: **"it wraps the previous thing and implements `next` by calling the previous `next`."**

---

## 3. Language foundations chains depend on

### 3.1 Method-call syntax, auto-ref and auto-deref

`value.method()` makes the compiler try, in order: `T`, `&T`, `&mut T`, then dereferences (`*T`) and repeats. That's why `String` can call `str` methods and why `vec.iter()` works on a `Vec<T>` (via `Deref<Target=[T]>`).

### 3.2 Closures: the "arguments" of most chain steps

| Trait | Can the closure… | Used by |
|-------|------------------|---------|
| `FnOnce` | consume captured values; called at most once | `Option::map`, `unwrap_or_else`, `thread::spawn` |
| `FnMut` | mutate captured values; called many times | `Iterator::map/filter/for_each` |
| `Fn` | only read captured values; called many times | `Iterator::filter` predicate style in some APIs, callbacks shared across threads |

Capture modes: the compiler picks the least powerful capture needed (by reference, by mutable reference, or by move). Use `move |x| ...` to force ownership (essential for threads and `async move`).

### 3.3 Passing functions instead of closures

`.map(|s| s.to_uppercase())` can be written `.map(str::to_uppercase)`. `.filter_map(Result::ok)`, `.map(String::from)`, `.map(Some)`, `.map(Value::as_array)` all pass an existing function. Use this when the closure only forwards its argument.

### 3.4 `impl Trait`, generics and `dyn Trait` in return position

```rust
// Static, zero-cost, one concrete (hidden) type:
fn evens_squared(limit: u32) -> impl Iterator<Item = u32> {
    (0..limit).filter(|n| n % 2 == 0).map(|n| n * n)
}

// Dynamic, allows returning different chains from different branches:
fn pick(flag: bool) -> Box<dyn Iterator<Item = u32>> {
    if flag { Box::new(0..5) } else { Box::new((0..5).rev()) }
}

fn main() {
    println!("{:?}", evens_squared(10).collect::<Vec<_>>()); // [0, 4, 16, 36, 64]
    println!("{:?}", pick(false).collect::<Vec<_>>());        // [4, 3, 2, 1, 0]
}
```

### 3.5 Temporaries and lifetimes inside one chain

A temporary created in a chain lives until the **end of the full statement** (the `;`). Problems appear when you *store* a reference derived from a temporary:

```rust
// ERROR-prone shape (conceptually):
// let r = String::from("a b").split(' ').next();   // temp String dropped at `;`
// println!("{:?}", r);                              // borrow outlives temp -> compile error

fn main() {
    let owned = String::from("a b");        // give the data a name (an owner)
    let first = owned.split(' ').next();    // now the borrow is valid
    println!("{first:?}");
}
```

Fix: bind the owner to a variable, or convert to an owned value (`.map(str::to_owned)`) before the statement ends.

---

## 4. Option and Result chaining (the "railway")

### 4.1 The combinator vocabulary

| Goal | `Option<T>` | `Result<T, E>` |
|------|-------------|-----------------|
| Transform the success value | `map(f)` | `map(f)` |
| Transform the error | — | `map_err(f)` |
| Chain a step that can itself fail | `and_then(f)` | `and_then(f)` |
| Provide a fallback value | `unwrap_or(v)`, `unwrap_or_else(f)`, `unwrap_or_default()` | same |
| Fallback that is another Option/Result | `or(o)`, `or_else(f)` | `or(r)`, `or_else(f)` |
| Keep only if predicate holds | `filter(p)` | — |
| Convert between the two | `ok_or(e)`, `ok_or_else(f)` | `ok()`, `err()` |
| Borrow instead of move | `as_ref()`, `as_mut()`, `as_deref()` | `as_ref()`, `as_deref()` |
| Combine two | `zip(o)`, `xor(o)` | — |
| Flip nesting | `transpose()` (`Option<Result>` ⇄ `Result<Option>`) | `transpose()` |
| Remove one nesting level | `flatten()` | `flatten()` (check your toolchain's stability status) |
| Test and use | `is_some_and(f)`, `map_or(d, f)` | `is_ok_and(f)`, `map_or(d, f)` |
| Run side effect without changing value | `inspect(f)` | `inspect(f)`, `inspect_err(f)` |

**`map` vs `and_then`** — the single most important distinction:

- `map(f)` where `f: T -> U` → result `Option<U>`.
- `and_then(f)` where `f: T -> Option<U>` → result `Option<U>` (avoids `Option<Option<U>>`).

### 4.2 Navigating nested optional data

```rust
#[derive(Debug)]
struct Address { city: Option<String> }
#[derive(Debug)]
struct User { name: String, address: Option<Address> }

fn city_upper(user: &User) -> Option<String> {
    user.address
        .as_ref()                       // Option<&Address>   (borrow, don't move)
        .and_then(|a| a.city.as_deref()) // Option<&str>       (String -> &str view)
        .map(str::to_uppercase)         // Option<String>
}

fn main() {
    let u = User {
        name: "Asha".into(),
        address: Some(Address { city: Some("Chennai".into()) }),
    };
    let nobody = User { name: "Ravi".into(), address: None };

    println!("{:?} / {:?}", city_upper(&u), city_upper(&nobody));
    // Some("CHENNAI") / None
    let _ = (&u.name, &nobody.name);
}
```

Why `as_ref()` first: without it, `user.address.and_then(..)` would try to *move* `address` out of a borrowed `user`. `as_ref` turns `&Option<T>` into `Option<&T>`.

### 4.3 Turning "missing" into an error, then bubbling with `?`

```rust
use std::{fmt, fs, io, num::ParseIntError};

#[derive(Debug)]
enum ConfigError {
    Io(io::Error),
    Parse(ParseIntError),
    Missing(&'static str),
}

impl fmt::Display for ConfigError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ConfigError::Io(e) => write!(f, "io error: {e}"),
            ConfigError::Parse(e) => write!(f, "parse error: {e}"),
            ConfigError::Missing(k) => write!(f, "missing key: {k}"),
        }
    }
}
impl std::error::Error for ConfigError {}

// `?` calls `From::from` on the error, so these impls make `?` work across types.
impl From<io::Error> for ConfigError { fn from(e: io::Error) -> Self { Self::Io(e) } }
impl From<ParseIntError> for ConfigError { fn from(e: ParseIntError) -> Self { Self::Parse(e) } }

fn read_port(path: &str) -> Result<u16, ConfigError> {
    let text = fs::read_to_string(path)?;              // io::Error  -> ConfigError
    let value = text
        .lines()
        .find_map(|l| l.strip_prefix("port="))          // Option<&str>
        .ok_or(ConfigError::Missing("port"))?;          // Option -> Result, then bubble
    Ok(value.trim().parse()?)                           // ParseIntError -> ConfigError
}

fn main() {
    match read_port("definitely-not-here.conf") {
        Ok(p) => println!("port {p}"),
        Err(e) => println!("failed: {e}"),
    }
}
```

**What `?` really does** (mental expansion):

```rust
// expr?   ≈
match expr {
    Ok(v)  => v,
    Err(e) => return Err(From::from(e)),   // early return on the failure track
}
```

For `Option`, `None => return None`. `?` is railway-switching built into the language. It only works in functions (or closures/blocks) whose return type is compatible.

### 4.4 Validation chains with `map_err` and `and_then`

```rust
fn parse_port(s: &str) -> Result<u16, String> {
    s.trim()
        .parse::<u16>()
        .map_err(|e| format!("bad port {s:?}: {e}"))
        .and_then(|p| {
            if p >= 1024 { Ok(p) } else { Err(format!("port {p} is privileged")) }
        })
}

fn main() {
    for input in ["8080", " 80 ", "abc", "70000"] {
        println!("{input:>7?} -> {:?}", parse_port(input));
    }
}
```

### 4.5 Collecting a whole list of fallible items

`Iterator<Item = Result<T,E>>` can be collected into `Result<Vec<T>,E>`: it stops at the first `Err`.

```rust
fn main() {
    let ok: Result<Vec<i32>, _> = "1,2,3".split(',').map(str::parse::<i32>).collect();
    let bad: Result<Vec<i32>, _> = "1,x,3".split(',').map(str::parse::<i32>).collect();
    println!("{ok:?}");   // Ok([1, 2, 3])
    println!("{bad:?}");  // Err(ParseIntError { kind: InvalidDigit })

    // Keep the good ones, ignore the bad ones:
    let lenient: Vec<i32> = "1,x,3".split(',').filter_map(|s| s.parse().ok()).collect();
    println!("{lenient:?}"); // [1, 3]
}
```

The same works for `Option` (`Option<Vec<T>>`) and for `sum`/`product`.

### 4.6 When *not* to chain

If a `match`/`if let`/`let else` reads more clearly, use it:

```rust
fn first_even(v: &[i32]) -> i32 {
    let Some(x) = v.iter().copied().find(|n| n % 2 == 0) else {
        return -1;
    };
    x
}
fn main() { println!("{} {}", first_even(&[1, 3, 4]), first_even(&[1, 3])); }
```

Rule of thumb: chain when each step is a **small, pure transformation**. Switch to `match` when you need **branching logic per case** or **early returns with different handling**.

---

## 5. Iterator chaining (the "assembly line")

### 5.1 The anatomy

```
 SOURCE            ADAPTERS (lazy, return new iterators)       CONSUMER (eager)
 iter()            map  filter  take  skip  zip  chain          collect  sum  fold
 into_iter()       enumerate  rev  peekable  flat_map           count  find  any  all
 iter_mut()        take_while  skip_while  scan  windows*       max  min  for_each
 (0..n)  chars()   filter_map  inspect  step_by  cloned         last  nth  position
 lines()           copied  fuse  cycle  flatten                 partition  unzip  reduce
                   (*windows/chunks are on slices)
```

The trait itself is tiny; everything else is a *provided method* built on `next`:

```rust
pub trait Iterator {
    type Item;
    fn next(&mut self) -> Option<Self::Item>;   // the ONLY required method
    // ~75 provided methods: map, filter, fold, ...
}
```

### 5.2 Three flavors of "iterate over a collection"

| Call | Yields | Collection afterwards |
|------|--------|-----------------------|
| `.iter()` | `&T` | still usable |
| `.iter_mut()` | `&mut T` | usable after the loop |
| `.into_iter()` | `T` (owned) | **moved/consumed** |

`for x in &v` ⇒ `iter()`, `for x in &mut v` ⇒ `iter_mut()`, `for x in v` ⇒ `into_iter()`.

Use `.copied()` / `.cloned()` to go from `&T` to `T` when `T: Copy` / `T: Clone`.

### 5.3 Laziness: prove it to yourself

```rust
fn main() {
    let r = (1..=10)
        .inspect(|n| println!("  produce {n}"))
        .map(|n| n * 10)
        .filter(|n| n % 20 == 0)
        .take(2);                 // nothing printed yet! no consumer.

    println!("chain built, nothing has run");
    let v: Vec<_> = r.collect();  // NOW items are pulled through, one at a time
    println!("{v:?}");            // [20, 40]; stopped after producing only 4 items
}
```

Observe: **short-circuiting** — `take(2)` stops pulling after two results, so items 5–10 are never produced. That is also how `find`, `any`, `all`, `take_while` save work. Forgetting the consumer is a classic bug; the compiler warns with `unused_must_use` for iterator adapters.

### 5.4 A guided tour of the most useful adapters

```rust
use std::collections::HashMap;

fn main() {
    let words = ["apple", "bob", "cat", "avocado", "dog"];

    // filter + map + collect
    let a_words: Vec<String> = words
        .iter()
        .filter(|w| w.starts_with('a'))
        .map(|w| w.to_uppercase())
        .collect();
    println!("{a_words:?}");

    // enumerate + zip
    for (i, (w, len)) in words.iter().zip(words.iter().map(|w| w.len())).enumerate() {
        if i < 2 { println!("{i}: {w} has {len} letters"); }
    }

    // flat_map: one-to-many, then flatten
    let chars: Vec<char> = ["ab", "cd"].iter().flat_map(|s| s.chars()).collect();
    println!("{chars:?}"); // ['a', 'b', 'c', 'd']

    // windows: sliding pairs over a slice (not an iterator method; a slice method)
    let temps = [20, 22, 21, 25, 24];
    let rises = temps.windows(2).filter(|w| w[1] > w[0]).count();
    println!("rises: {rises}"); // 2

    // scan: running state (running total)
    let running: Vec<i32> = temps.iter().scan(0, |acc, &x| { *acc += x; Some(*acc) }).collect();
    println!("{running:?}");

    // fold: general reduction
    let longest = words.iter().fold("", |best, w| if w.len() > best.len() { w } else { best });
    println!("longest: {longest}");

    // partition: split into two collections
    let (short, long): (Vec<&str>, Vec<&str>) = words.iter().partition(|w| w.len() <= 3);
    println!("{short:?} | {long:?}");

    // group counts via HashMap entry API inside a chain
    let mut counts: HashMap<char, usize> = HashMap::new();
    words.iter().filter_map(|w| w.chars().next()).for_each(|c| *counts.entry(c).or_default() += 1);
    let mut sorted: Vec<_> = counts.into_iter().collect();
    sorted.sort_by(|a, b| b.1.cmp(&a.1).then(a.0.cmp(&b.0))); // Ordering::then chains comparisons
    println!("{sorted:?}");

    // peekable: look ahead without consuming
    let mut it = [1, 1, 2, 2, 2, 3].iter().peekable();
    let mut runs = Vec::new();
    while let Some(&x) = it.next() {
        let mut n = 1;
        while it.peek() == Some(&&x) { it.next(); n += 1; }
        runs.push((x, n));
    }
    println!("{runs:?}"); // [(1, 2), (2, 3), (3, 1)]
}
```

Notes worth remembering:

- `sort_by_key`, `sort_unstable_by`, `max_by_key`, `min_by` take closures; `Ordering::then`/`then_with` chain multi-key comparisons.
- `chain(other)` concatenates two iterators; `rev()` needs `DoubleEndedIterator`; `step_by(n)` strides; `cycle()` repeats forever (pair with `take`).
- `by_ref()` lets you consume part of an iterator and keep using it afterwards.
- `size_hint()` / `ExactSizeIterator` let `collect` pre-allocate; `collect::<Vec<_>>()` already uses it.

### 5.5 What `collect()` can build

`collect` is generic over the target (`FromIterator`). You must tell the compiler the target:

```rust
use std::collections::{BTreeMap, HashMap, HashSet};

fn main() {
    let v: Vec<i32>           = (1..4).collect();
    let s: HashSet<i32>       = [1, 1, 2].into_iter().collect();
    let m: HashMap<&str, i32> = [("a", 1), ("b", 2)].into_iter().collect();
    let b: BTreeMap<i32, char> = ['x', 'y'].into_iter().enumerate().map(|(i, c)| (i as i32, c)).collect();
    let text: String          = ['h', 'i'].iter().collect();
    let joined: String        = ["a", "b", "c"].iter().map(|s| s.to_string()).collect::<Vec<_>>().join("-");
    let r: Result<Vec<u8>, _> = ["1", "2"].iter().map(|s| s.parse::<u8>()).collect();
    println!("{v:?} {s:?} {m:?} {b:?} {text} {joined} {r:?}");
}
```

Two ways to specify: type annotation on the `let`, or the turbofish `collect::<Vec<_>>()`.

### 5.6 Performance mental model

- Iterator chains are **zero-cost abstractions** in typical release builds: adapters are monomorphized and inlined into a loop comparable to hand-written code. Measure with `cargo bench`/criterion before assuming otherwise.
- Allocation is the real cost: avoid intermediate `collect()` calls between steps unless you need the data twice.
- Prefer `iter()` + `copied()` over `clone()` of whole collections.
- Prefer `for` loops when you need `break`/`continue`/early `return` with complex flow; both compile to similar code.

### 5.7 Writing your own adapter (and extending every iterator with a new method)

```rust
// 1. The wrapper struct that holds the upstream iterator
struct EveryNth<I> { inner: I, n: usize }

// 2. Implement Iterator by calling the upstream `next`
impl<I: Iterator> Iterator for EveryNth<I> {
    type Item = I::Item;
    fn next(&mut self) -> Option<I::Item> {
        let item = self.inner.next()?;          // `?` works on Option here
        for _ in 1..self.n { self.inner.next(); } // skip n-1 items
        Some(item)
    }
}

// 3. An *extension trait* adds `.every_nth()` to ALL iterators
trait IterExt: Iterator + Sized {
    fn every_nth(self, n: usize) -> EveryNth<Self> {
        assert!(n > 0);
        EveryNth { inner: self, n }
    }
}
impl<I: Iterator> IterExt for I {}   // blanket impl

fn main() {
    let v: Vec<_> = (0..20).every_nth(5).map(|x| x * 2).collect();
    println!("{v:?}"); // [0, 10, 20, 30]
}
```

This is exactly how the `itertools` crate adds dozens of chainable methods (`.sorted()`, `.unique()`, `.join(",")`, …). The pattern: **wrapper struct + `impl Iterator` + extension trait with blanket impl**.

---

## 6. Builder chaining

Builders exist because Rust has no named/optional arguments. Three variants — know them all.

### 6.1 Variant A — owned/consuming builder (`self -> Self`)

Best for configuring then producing a value once. Used by `reqwest::ClientBuilder`, `tokio::runtime::Builder` (which uses `&mut self` returning `&mut Self` in places — check the docs for each), many config types.

```rust
#[derive(Debug)]
struct Server { host: String, port: u16, workers: usize, tls: bool }

#[derive(Default)]
struct ServerBuilder {
    host: Option<String>,
    port: Option<u16>,
    workers: Option<usize>,
    tls: bool,
}

impl ServerBuilder {
    fn host(mut self, h: impl Into<String>) -> Self { self.host = Some(h.into()); self }
    fn port(mut self, p: u16) -> Self { self.port = Some(p); self }
    fn workers(mut self, n: usize) -> Self { self.workers = Some(n); self }
    fn tls(mut self, on: bool) -> Self { self.tls = on; self }

    // Validation lives in `build`, which returns Result
    fn build(self) -> Result<Server, String> {
        Ok(Server {
            host: self.host.ok_or("host is required")?, // &str -> String via From
            port: self.port.unwrap_or(8080),
            workers: self.workers.unwrap_or(4),
            tls: self.tls,
        })
    }
}

fn main() {
    let server = ServerBuilder::default()
        .host("0.0.0.0")
        .port(9000)
        .tls(true)
        .build();
    println!("{server:?}");
    println!("{:?}", ServerBuilder::default().build()); // Err("host is required")
}
```

Notes: `mut self` in a signature means "I take ownership and may mutate my own copy" — each step moves the builder forward. `impl Into<String>` lets callers pass `&str` or `String`.

### 6.2 Variant B — borrowing builder (`&mut self -> &mut Self`)

Best when the builder is reusable or you want to keep configuring in a loop/conditionally. `std::process::Command` is the canonical example.

```rust
struct Cmd { program: String, args: Vec<String> }

impl Cmd {
    fn new(p: &str) -> Self { Cmd { program: p.into(), args: vec![] } }
    fn arg(&mut self, a: &str) -> &mut Self { self.args.push(a.into()); self }
    fn args<I, S>(&mut self, it: I) -> &mut Self
    where I: IntoIterator<Item = S>, S: AsRef<str> {
        self.args.extend(it.into_iter().map(|s| s.as_ref().to_owned()));
        self
    }
    fn describe(&self) -> String { format!("{} {}", self.program, self.args.join(" ")) }
}

fn main() {
    let mut c = Cmd::new("git");
    c.arg("log").arg("--oneline").args(["-n", "5"]); // chain on a named variable
    println!("{}", c.describe());

    // The classic trap:
    // let c = Cmd::new("git").arg("log");   // ERROR: temporary dropped while borrowed
    // `arg` returns &mut Self borrowed from a temporary that dies at `;`.
    // Fix: bind first (as above) or finish the chain in one statement:
    println!("{}", Cmd::new("ls").arg("-la").describe());
}
```

Trade-off: `&mut` builders can't be finished with a consuming `build(self)` mid-chain easily; many libraries expose a `build(&self)` or `spawn(&mut self)` instead.

### 6.3 Variant C — typestate builder (compile-time enforcement)

Make *invalid usage impossible to compile*: the type of the builder changes as you supply required pieces.

```rust
use std::marker::PhantomData;

struct NoUrl;
struct HasUrl;

struct RequestBuilder<S> {
    url: Option<String>,
    headers: Vec<(String, String)>,
    _state: PhantomData<S>,
}

impl RequestBuilder<NoUrl> {
    fn new() -> Self { RequestBuilder { url: None, headers: vec![], _state: PhantomData } }
    // transitions NoUrl -> HasUrl
    fn url(self, u: &str) -> RequestBuilder<HasUrl> {
        RequestBuilder { url: Some(u.into()), headers: self.headers, _state: PhantomData }
    }
}

impl<S> RequestBuilder<S> {                      // available in every state
    fn header(mut self, k: &str, v: &str) -> Self {
        self.headers.push((k.into(), v.into()));
        self
    }
}

impl RequestBuilder<HasUrl> {                    // only after a URL is set
    fn send(self) -> String {
        format!("GET {} with {} headers", self.url.unwrap(), self.headers.len())
    }
}

fn main() {
    let out = RequestBuilder::new()
        .header("Accept", "text/plain")
        .url("https://example.com")
        .header("X-Trace", "1")
        .send();
    println!("{out}");
    // RequestBuilder::new().send();   // does not compile: `send` doesn't exist for NoUrl
}
```

When to pick which: **A** for most config objects, **B** for command-like objects that you reuse, **C** when a forgotten step would be a serious bug (protocol builders, hardware config). The Rust API Guidelines discuss these ("C-BUILDER").

### 6.4 Derive-based builders in production

Crates like `derive_builder` and `bon` generate Variant-A builders from a struct definition, reducing boilerplate. Reading generated code with `cargo expand` is a great way to see exactly what is produced (see Part 11).

---

## 7. Error-context chaining

Production code needs errors that say *what you were doing*, not just *what failed*.

Pattern from `anyhow` (application-level errors) and `thiserror` (library-level typed errors):

```rust
use anyhow::{Context, Result};
use std::fs;

#[derive(Debug, serde::Deserialize)]
struct Settings { database_url: String, workers: usize }

fn load(path: &str) -> Result<Settings> {
    let raw = fs::read_to_string(path)
        .with_context(|| format!("reading config file {path}"))?;     // adds a layer
    let settings: Settings = toml::from_str(&raw)
        .with_context(|| format!("parsing config file {path} as TOML"))?;
    anyhow::ensure!(settings.workers > 0, "workers must be positive");
    Ok(settings)
}

fn main() {
    if let Err(e) = load("app.toml") {
        // {:#} prints the whole chain on one line: "reading config file app.toml: No such file ..."
        eprintln!("error: {e:#}");
        // {:?} prints a multi-line "Caused by:" report; you can also walk it:
        for (i, cause) in e.chain().enumerate() {
            eprintln!("  {i}: {cause}");
        }
    }
}
```

The "chain" here is the `std::error::Error::source()` linked list: each layer holds the layer below. `thiserror` makes this ergonomic for libraries:

```rust
use thiserror::Error;

#[derive(Debug, Error)]
pub enum StoreError {
    #[error("could not open database at {path}")]
    Open { path: String, #[source] source: std::io::Error },
    #[error("record {0} not found")]
    NotFound(u64),
}
```

Guideline: **libraries expose typed errors (`thiserror`), applications use `anyhow` and add context at each boundary with `.context()`.**

---

## 8. Async, streams and middleware chaining

### 8.1 Futures: `.await` is chaining in disguise

A `Future` is a value describing work that hasn't happened. `.await` drives it. A chain like:

```rust
client.get(url).send().await?.error_for_status()?.json::<T>().await?
```

reads left→right: build a request (builder), await the response (future), check status (Result), await the body (future), parse (Result). Each `?` is a railway switch; each `.await` is a suspension point.

Pattern from `reqwest` + `tokio` + `serde` + `anyhow` (typical for service-to-service HTTP calls):

```rust
use anyhow::{Context, Result};
use serde::Deserialize;
use std::time::Duration;

#[derive(Debug, Deserialize)]
struct Repo { name: String, stargazers_count: u32 }

#[tokio::main]
async fn main() -> Result<()> {
    // 1. Builder chain: one Client, reused for all requests (connection pooling)
    let client = reqwest::Client::builder()
        .user_agent("chaining-demo/0.1")
        .timeout(Duration::from_secs(10))
        .build()?;

    // 2. Request builder + future chain
    let repos: Vec<Repo> = client
        .get("https://api.github.com/orgs/rust-lang/repos")
        .query(&[("per_page", "5")])
        .send()
        .await
        .context("sending request")?
        .error_for_status()
        .context("server returned an error status")?
        .json()
        .await
        .context("decoding JSON body")?;

    // 3. Iterator chain on the result
    let top = repos.iter().max_by_key(|r| r.stargazers_count);
    println!("{top:?}");
    Ok(())
}
```

### 8.2 Concurrency with stream chains

`futures::StreamExt` brings iterator-like adapters to async streams. The idiom below fetches many URLs with bounded parallelism:

```rust
use futures::{stream, StreamExt};

async fn fetch_all(client: &reqwest::Client, urls: Vec<String>) -> Vec<(String, Result<usize, reqwest::Error>)> {
    stream::iter(urls)
        .map(|url| {
            let client = client.clone();           // Client is cheap to clone (Arc inside)
            async move {                           // `move` so the future owns `url` & `client`
                let len = client.get(&url).send().await?.bytes().await.map(|b| b.len());
                (url, len)
            }
        })
        .buffer_unordered(8)                       // at most 8 requests in flight
        .collect()
        .await
}
```

Mental model: it's the same assembly line as §5, but each item is a *future* and `buffer_unordered(n)` is the stage that runs up to `n` of them at once. Related combinators: `try_join!`/`join!` (run futures concurrently), `select!` (first to finish), `.then()`, `.filter_map()`, `.try_collect()`.

> Gotcha: `.await` inside a `.map` closure isn't allowed (closures aren't async). Return an `async move { .. }` block from the closure instead, as above.

### 8.3 Layer chaining: middleware with `tower`

In HTTP servers, requests pass through *layers* (logging, timeouts, compression, auth). Each `.layer()` wraps the service so far in a new service — the Russian-doll model from §2.5.

Pattern from `axum` + `tower` + `tower-http` (versions change; check docs.rs for your versions):

```rust
use axum::{routing::get, Router};
use tower::ServiceBuilder;
use tower_http::{catch_panic::CatchPanicLayer, compression::CompressionLayer, trace::TraceLayer};

fn app() -> Router {
    Router::new()
        .route("/health", get(|| async { "ok" }))
        .layer(
            ServiceBuilder::new()
                .layer(TraceLayer::new_for_http())      // outermost: runs first on request
                .layer(CatchPanicLayer::new())          // turns handler panics into 500s
                .layer(CompressionLayer::new()),        // innermost
        )
}
```

Order matters: with `ServiceBuilder`, layers listed **first are outermost** (they see the request first and the response last). With plain `Router::layer`, calling `.layer(A).layer(B)` makes **B outer** — a frequent source of bugs. When in doubt, read the doc comment on `ServiceBuilder`; it shows a diagram of the order.

### 8.4 Registry/layer chaining in `tracing-subscriber`

Pattern from `tracing-subscriber`, used in most async Rust services for logging setup:

```rust
use tracing_subscriber::{fmt, prelude::*, EnvFilter};

fn init_logging() {
    tracing_subscriber::registry()
        .with(EnvFilter::try_from_default_env().unwrap_or_else(|_| "info".into()))
        .with(fmt::layer().with_target(false))
        .init();
}
```

Each `.with(layer)` returns a *new, differently typed* subscriber (`Layered<L, S>`). That's the type-nesting of §2.5 again; `.init()` is the consumer that installs it globally.

---

## 9. Production-style examples, explained

### 9.1 Log analytics pipeline (iterators + Result + fold) — std only

This mirrors what log-processing tools do: parse lines, skip garbage, aggregate, rank.

```rust
use std::collections::HashMap;

#[derive(Debug)]
struct Hit<'a> { path: &'a str, status: u16, ms: u32 }

fn parse(line: &str) -> Option<Hit<'_>> {
    // "GET /api/users 200 12ms"
    let mut parts = line.split_whitespace();
    let _method = parts.next()?;
    let path = parts.next()?;
    let status = parts.next()?.parse().ok()?;
    let ms = parts.next()?.strip_suffix("ms")?.parse().ok()?;
    Some(Hit { path, status, ms })
}

fn main() {
    let log = "\
GET /api/users 200 12ms
GET /api/users 500 80ms
garbage line
POST /api/orders 201 45ms
GET /api/users 200 20ms
GET /api/orders 404 3ms";

    // lines -> Option<Hit> -> flatten away Nones -> keep only errors-or-slow
    let hits: Vec<Hit> = log.lines().filter_map(parse).collect();

    // aggregate: path -> (count, total_ms)
    let stats = hits.iter().fold(HashMap::<&str, (u32, u32)>::new(), |mut acc, h| {
        let e = acc.entry(h.path).or_insert((0, 0));
        e.0 += 1;
        e.1 += h.ms;
        acc
    });

    // rank by average latency, descending
    let mut ranked: Vec<_> = stats
        .iter()
        .map(|(path, &(n, total))| (*path, total as f64 / n as f64))
        .collect();
    ranked.sort_by(|a, b| b.1.total_cmp(&a.1));

    for (path, avg) in &ranked {
        println!("{path:<12} avg {avg:>6.1} ms");
    }

    let error_rate = hits.iter().filter(|h| h.status >= 500).count() as f64 / hits.len() as f64;
    println!("5xx rate: {:.1}%", error_rate * 100.0);
}
```

**How it works, step by step**

1. `parse` is itself a chain of `?` on `Option`: any missing/invalid piece returns `None` immediately (railway).
2. `filter_map(parse)` runs `parse` on each line and silently drops the `None`s (the "garbage line").
3. `fold` is the general-purpose consumer: it threads an accumulator (`HashMap`) through each item. The closure takes ownership of `acc` and returns it, so no clones are needed.
4. A second chain maps the map entries into `(path, avg)` pairs, then `sort_by` with `total_cmp` handles `f64` ordering safely.

### 9.2 Fast recursive file search (pattern from `ripgrep`'s `ignore` crate)

`ripgrep` is built on the `ignore` crate, which respects `.gitignore`. Using its builder + iterator chain:

```rust
use ignore::WalkBuilder;

fn main() {
    let rust_files: Vec<String> = WalkBuilder::new(".")
        .hidden(false)           // include dotfiles
        .git_ignore(true)        // honor .gitignore
        .max_depth(Some(4))
        .build()                                           // Walk: an Iterator<Item = Result<DirEntry, Error>>
        .filter_map(Result::ok)                            // drop unreadable entries
        .filter(|e| e.file_type().is_some_and(|t| t.is_file()))
        .filter(|e| e.path().extension().is_some_and(|x| x == "rs"))
        .map(|e| e.path().display().to_string())
        .collect();

    println!("{} files", rust_files.len());
}
```

Why this is a good template: **builder → iterator → combinators → collect.** Many Rust libraries follow exactly this shape (config via builder, results via iterator).

### 9.3 Navigating dynamic JSON (pattern from `serde_json`)

```rust
use serde_json::{json, Value};

fn main() {
    let v: Value = json!({ "data": { "items": [ { "name": "a" }, { "name": "b" } ] } });

    // Chain of Option steps — no panics if any level is missing
    let count = v.get("data")
        .and_then(|d| d.get("items"))
        .and_then(Value::as_array)     // function path instead of closure
        .map(Vec::len)
        .unwrap_or(0);

    // Shortcut: JSON Pointer syntax
    let first = v.pointer("/data/items/0/name").and_then(Value::as_str);

    println!("{count} {first:?}"); // 2 Some("a")
}
```

Prefer deriving `Deserialize` into typed structs when the shape is known; use `Value` chains for partially known/dynamic payloads.

### 9.4 Concurrent HTTP with timeout and context (pattern: `reqwest` + `tokio`)

Combine §8.1 and §8.2: a shared `Client` built once via builder; `buffer_unordered` for bounded concurrency; `tokio::time::timeout` for an outer deadline:

```rust
use std::time::Duration;
use tokio::time::timeout;

async fn probe(client: &reqwest::Client, url: &str) -> Result<u16, String> {
    let fut = client.get(url).send();
    timeout(Duration::from_secs(3), fut)
        .await
        .map_err(|_| "timed out".to_string())?          // Elapsed -> String
        .map(|resp| resp.status().as_u16())             // Result<Response,_> -> Result<u16,_>
        .map_err(|e| e.to_string())                     // reqwest::Error -> String
}
```

Read it as a railway with two nested `Result`s (`timeout` returns `Result<Result<..>>`); the first `?` handles the outer timeout layer, the remaining combinators handle the inner one.

### 9.5 Service assembly (pattern: `axum` + `tower` + `tracing`)

A realistic `main` composes everything from this guide:

```rust
#[tokio::main]
async fn main() -> anyhow::Result<()> {
    init_logging();                                   // §8.4: layered subscriber
    let app = app();                                  // §8.3: router + middleware layers
    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await?;
    tracing::info!("listening on {}", listener.local_addr()?);
    axum::serve(listener, app).await?;
    Ok(())
}
```

Notice how little *explicit* error handling there is: `?` plus `anyhow::Result` carry failures to one place. Idiomatic Rust centralizes handling and keeps the happy path flat.

---

## 10. Writing your own chainable APIs

Checklist for designing chain-friendly code:

1. **Decide the mechanism** (railway, adapter, builder, layer) — don't mix accidentally.
2. **Pick `self` carefully** — `self` for one-shot transformation, `&mut self` for reusable mutation, `&self` for pure inspection.
3. **Return types should keep the chain alive**: `Self`, `&mut Self`, a wrapper adapter, or a `Result`/`Option` of something chainable.
4. **Accept flexible inputs**: `impl Into<String>`, `impl AsRef<str>`, `impl IntoIterator<Item = T>`, `impl FnOnce(..)`.
5. **Validate at the end** (`build() -> Result`), not in each setter.
6. **Mark builders `#[must_use]`** so a forgotten `.build()` or consumer warns.
7. **Document with examples** (doc tests are compiled and run by `cargo test`).
8. **Follow the Rust API Guidelines** (naming: `with_*`, `into_*`, `as_*`, `to_*`).

Naming conventions as chain signals:

| Prefix | Meaning | Cost |
|--------|---------|------|
| `as_` | cheap borrow→borrow view | free |
| `to_` | produce a new owned value from a borrow | may allocate |
| `into_` | consume `self` and convert | usually free |
| `with_` | builder-style setter | free |
| `try_` | fallible version returning `Result` | — |

---

## 11. How to read the docs and source to learn any chain

You will never memorize every method. The real skill is to **read signatures fluently** and **navigate documentation fast.**

### 11.1 Where to look (in order)

| Need | Resource |
|------|----------|
| Language concepts | **The Rust Programming Language** ("the Book"): `rustup doc --book` |
| Learn by example | **Rust By Example**: `rustup doc --rust-by-example` |
| Standard library API | **std docs**: `rustup doc --std` (works offline), search with `s` key |
| Third-party crate API | **docs.rs/<crate>** (matches the exact version you use) |
| Your own project + dependencies, offline | `cargo doc --open` |
| Design conventions | **Rust API Guidelines** (rust-lang.github.io/api-guidelines) |
| Deep dives on tricky semantics | **The Rustonomicon**, **The Rust Reference** |
| Asynchronous Rust | **Async Book**, **Tokio tutorial** (tokio.rs) |
| Iterator extras | docs.rs/itertools |
| Real usage | the crate's `examples/` folder and tests on GitHub |

### 11.2 Reading a method signature like a sentence

Take `Option::map`:

```rust
pub fn map<U, F>(self, f: F) -> Option<U>
where
    F: FnOnce(T) -> U,
```

Read it aloud:

- `self` → "consumes the Option" (the old `Option` is gone after this call).
- `<U, F>` → "two type parameters the *caller* effectively chooses via the closure".
- `f: F` where `F: FnOnce(T) -> U` → "give me a closure that takes the inner `T` and returns some `U`, and I'll call it at most once".
- `-> Option<U>` → "I return an Option of whatever your closure produced".

Now `Iterator::filter`:

```rust
fn filter<P>(self, predicate: P) -> Filter<Self, P>
where
    P: FnMut(&Self::Item) -> bool,
```

- Returns **`Filter<Self, P>`** — an adapter struct, so it's lazy.
- The predicate receives **`&Item`** (a reference!), which is why you often write `|&x|` or `|x| **x > 1` and why `filter` after `iter()` gives `&&T`.

Compare with `filter_map`, whose closure takes `Self::Item` by value and returns `Option<B>`.

### 11.3 A reading routine for any rustdoc page

1. **Read the top summary and examples first** — they show intended chaining.
2. **Look at the sidebar**: *Methods*, *Trait Implementations*, *Required/Provided Methods*, *Implementors*. For `Iterator`, the sidebar is the full adapter menu.
3. **Check the return type** of each candidate method (adapter? consumer? `Result`?).
4. **Click `[src]`** on a method to see the real implementation — often 5–10 lines.
5. **Look at "Trait Implementations"** to learn what the type can do via traits (e.g., `FromIterator`, `Extend`, `From<…>`, `Deref`).
6. **Use the search bar with type signatures**, e.g. `Option<T> -> Result<T, E>` or `Vec<T> -> Option<T>` (rustdoc supports searching by signature) to discover `ok_or`, `pop`, etc.
7. **Read "Panics", "Errors", and "Safety" sections** before use in production code.
8. On docs.rs, check **feature flags** (`Feature flags` page) — a method may exist only behind a flag you must enable in `Cargo.toml`.
9. Check the **crate version** (top-left). Docs for `latest` may not match your pinned version.

### 11.4 Tools that make chains legible

| Tool | How it helps |
|------|--------------|
| **rust-analyzer** inlay hints | Shows the inferred type after every step in a chain. Turn on "chaining hints". |
| `cargo doc --open` | Offline docs for *your exact dependency versions*. |
| `cargo expand` (`cargo install cargo-expand`) | Shows macro/derive output — see what a `#[derive(Builder)]` generated. |
| **Clippy** (`cargo clippy`) | Suggests simpler chains (e.g., `map(..).flatten()` → `flat_map`, `.iter().count()` patterns). |
| Compiler errors | Read the **first** error and the "expected X, found Y" lines; they pinpoint the mismatched pipe-end. |
| `dbg!(expr)` / `.inspect(\|x\| dbg!(x))` | Print values mid-chain without restructuring. |
| `let () = expr;` trick | Deliberately mismatch to make the compiler print the type of `expr`. |
| Rust Playground (play.rust-lang.org) | Run experiments; *Tools → Clippy / Expand macros*. |

### 11.5 How to learn a *brand-new* crate's chain in 15 minutes

1. Open `docs.rs/<crate>` → read the crate-level docs and the first example.
2. Find the entry type (often a `Builder`, `Client`, `Router`, or `Config`).
3. Follow the return types: entry type → builder methods → terminal method (`build`, `send`, `run`, `collect`).
4. Copy an example from the repo's `examples/` directory and make it compile.
5. Change one thing at a time; use inlay hints to watch the type evolve.
6. When stuck, read the source of the method you're calling (`[src]` link).
7. Search GitHub for `crate_name::` in other projects to see production usage.

---

## 12. Pitfalls, debugging, style, and a practice plan

### 12.1 Common pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Forgetting the consumer | Nothing happens; `unused_must_use` warning | End with `.collect()`, `.count()`, `for_each`, `for` loop |
| `collect()` without a target type | "type annotations needed" | `let v: Vec<_> = …` or `collect::<Vec<_>>()` |
| Moving instead of borrowing | "use of moved value" | `.iter()`, `.as_ref()`, `.as_deref()`, `.copied()` |
| `&&T` confusion in `filter` | Comparison type mismatch | Pattern `\|&&x\|`, use `.copied()` before `filter` |
| Temporary dropped while borrowed | "temporary value dropped while borrowed" | Bind to a variable; or `.to_owned()` |
| Mixed error types with `?` | "`?` couldn't convert the error" | `impl From`, `map_err`, or `anyhow::Result` |
| `unwrap()` in the middle of a chain | Panics in production | `ok_or`, `?`, `unwrap_or_else`; reserve `unwrap/expect` for provable invariants |
| Side effects inside `map` | Surprise laziness/double-run | Use `for_each`/`inspect`; keep `map` pure |
| Huge unreadable chains | Review friction | Split into named `let` steps or helper functions |
| Wrong layer order | Middleware misbehaving | Read the docs diagram; test with logs |
| `async` closure issues | "cannot use `.await` in closure" | Return an `async move {}` block |
| Over-cloning to appease the borrow checker | Slow code | Restructure ownership; use references/`Arc` intentionally |

### 12.2 A debugging recipe for a failing chain

1. **Break the chain** into `let` bindings, one per step, with explicit type annotations.
2. The first binding that fails to compile is the broken link.
3. Compare *what the step returns* with *what the next step's `self` expects*.
4. Check closure parameter types (`&T` vs `T`, `&&T`).
5. Re-join the chain once it compiles, then let rustfmt/Clippy tidy it.

```rust
// Debug-friendly version of a chain:
fn main() {
    let words = vec!["a", "bb", "ccc"];
    let it = words.iter();                           // Iter<&str>        Item = &&str
    let it = it.map(|w| w.len());                    // Map<..>           Item = usize
    let it = it.filter(|&n| n > 1);                  // Filter<..>        Item = usize
    let v: Vec<usize> = it.collect();                // Vec<usize>
    println!("{v:?}");
}
```

### 12.3 Style guidelines

- One adapter per line, aligned on the dot (rustfmt does this).
- Keep closures short; extract named functions for anything beyond ~3 lines.
- Prefer function paths (`.map(String::from)`) when they read cleanly.
- Put the terminal operation on its own line so it stands out.
- Use `?` over `.unwrap()` in anything that isn't a test or example.
- Prefer `ok_or_else` over `ok_or` when constructing the error is expensive.
- Prefer `unwrap_or_else`/`map_or_else` when the default is expensive to compute.
- Use `let … else` for early-exit extraction instead of nested combinators.

### 12.4 Practice plan (4 weeks)

**Week 1 — Option/Result.** Re-implement `map`, `and_then`, `ok_or`, `unwrap_or_else` for your own `MyOption<T>` enum. Then write a function parsing `"key=value;key2=value2"` into a `HashMap`, using `Result` and `?` throughout.

**Week 2 — Iterators.** Solve 20 problems from Advent of Code or Exercism using *only iterator chains* (no `for` loops). Then implement `every_nth`, `dedup_consecutive`, and `pairwise` as extension-trait adapters.

**Week 3 — Builders and error handling.** Build a CLI-config type with an owned builder, then a typestate variant. Add `thiserror` errors with `#[source]`, then wrap the top level in `anyhow` with `.context()`.

**Week 4 — Async and layers.** Write a tiny `axum` service with `TraceLayer`, a custom `tower::Layer` that measures latency, and a client using `reqwest` + `buffer_unordered`. Read the source of one adapter in `futures` and one layer in `tower-http`.

**Capstone.** Read the source of a small, popular crate (for example, `itertools`'s `Itertools::join`, or the `Option` impl in `core::option`) and write a one-page explanation of how its chain works. Teaching it back is the fastest way to cement the model.

### 12.5 Self-test questions

1. For `a.b().c()`, what must be true about the return type of `b`?
2. Why does `v.iter().map(|x| x * 2)` print nothing without a consumer?
3. What's the difference between `Option::map` and `Option::and_then`?
4. Why does `Command::new("x").arg("y")` stored in a `let` fail to compile, but `Client::builder().build()` stored in a `let` doesn't?
5. What does `?` do on `Option` vs `Result`, and what traits does it rely on?
6. Which layer sees the request first in `ServiceBuilder::new().layer(A).layer(B)`?
7. Why does `filter` give closures `&Item` but `map` gives `Item`?

*(Answers: 1. It must have the method `c` — i.e., `c` is defined on that type or a trait in scope. 2. Adapters are lazy; only a consumer pulls items. 3. `and_then`'s closure returns an Option, avoiding nesting. 4. `arg` returns `&mut Self` borrowed from a temporary that dies at `;`; `build` returns an owned value. 5. Early-returns `None` / converts the error with `From` and returns `Err`; relies on `FromResidual`/`From`. 6. `A`. 7. `filter` must not consume items it only inspects, so it lends a reference.)*

---

## 13. Cheat sheets

### 13.1 "I have X, I want Y"

| Have | Want | Use |
|------|------|-----|
| `Option<T>` | `Option<U>` | `.map(f)` |
| `Option<T>` | `Option<U>`, `f` returns Option | `.and_then(f)` |
| `Option<T>` | `Result<T,E>` | `.ok_or(e)` / `.ok_or_else(f)` |
| `Result<T,E>` | `Option<T>` | `.ok()` |
| `Result<T,E>` | `Result<T,F>` | `.map_err(f)` |
| `Option<String>` | `Option<&str>` | `.as_deref()` |
| `&Option<T>` | `Option<&T>` | `.as_ref()` |
| `Option<Result<T,E>>` | `Result<Option<T>,E>` | `.transpose()` |
| `Iterator<Item=Result<T,E>>` | `Result<Vec<T>,E>` | `.collect::<Result<Vec<_>,_>>()` |
| `Iterator<Item=Option<T>>` | only the `Some` values | `.flatten()` or `.filter_map(\|x\| x)` |
| `Iterator<Item=&T>` | `Iterator<Item=T>` | `.copied()` / `.cloned()` |
| `Iterator<Item=(K,V)>` | `HashMap<K,V>` | `.collect()` |
| `Iterator<Item=Vec<T>>` | flat `Iterator<Item=T>` | `.flatten()` / `.flat_map(f)` |
| `Iterator` | sum/count/min/max | `.sum()`, `.count()`, `.min()`, `.max_by_key(f)` |
| two `Iterator`s | pairs | `.zip(other)` |
| `Iterator` | position-annotated | `.enumerate()` |
| `&str` | owned `String` | `.to_owned()`, `.to_string()`, `String::from` |
| closure needed once | — | `FnOnce` context (`map`, `unwrap_or_else`) |

### 13.2 Eager vs lazy

| Lazy (adapters; do nothing alone) | Eager (consumers; run the pipeline) |
|-----------------------------------|--------------------------------------|
| `map`, `filter`, `filter_map`, `flat_map`, `take`, `skip`, `take_while`, `skip_while`, `zip`, `chain`, `enumerate`, `rev`, `peekable`, `scan`, `inspect`, `step_by`, `cloned`, `copied`, `flatten`, `windows`, `chunks` | `collect`, `sum`, `product`, `count`, `fold`, `reduce`, `for_each`, `last`, `nth`, `find`, `position`, `any`, `all`, `min`, `max`, `partition`, `unzip`, `try_fold` |

### 13.3 The one-paragraph summary

A chain is a pipeline where **each step's output type is the next step's input type.** Option/Result chains are *railways* that skip work after failure. Iterator chains are *lazy assembly lines* pulled by a consumer, implemented as nested wrapper structs the compiler inlines. Builders pass the configuration object along, by value (`self`) or by `&mut`, ending in `build()`. Async chains do the same with futures, and middleware chains wrap services in layers. To master it: **track the type at each step, read the `self` kind and return type in every signature, know whether you're lazy or eager, and use the docs (`[src]`, sidebar, signature search) and rust-analyzer hints to verify.**

---

*End of guide.*
