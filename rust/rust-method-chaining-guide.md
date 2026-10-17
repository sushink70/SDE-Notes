# Rust Method Chaining: The Complete Mental-Model Guide

> **Goal:** after this guide you should be able to look at *any* Rust chain such as
> `a.b().c(|x| ...).d()?.e()` and say, without running it: what each dot receives, what each dot returns,
> **who owns what**, **when each closure actually runs**, **what the compiler turns it into**, and **how much it costs**.

**How this guide was verified.** The complete functions and programs in this guide were compiled and run with `rustc 1.75.0` (edition 2021), and the outputs and compiler errors shown are the real ones. Short fragments that mention elided variables (such as `it`, `v`, or `a`) are excerpts of those verified programs, and blocks that list several expressions with `// result` comments are lists of independent expressions (each was run on its own). Sections 15 and 16 (async/streams/rayon and Go) were **not compiled** and are marked as such, and the "costly mistakes" list in 13.3 shows patterns rather than full programs. Struct sizes are measured on a 64-bit machine and are *implementation details* that can differ between compiler versions. All diagrams are plain ASCII.

---

## Table of Contents

1. [What method chaining really is](#1-what-method-chaining-really-is)
2. [Ownership inside a chain: `self`, `&self`, `&mut self`](#2-ownership-inside-a-chain-self-self-mut-self)
3. [Iterator chains: the machinery](#3-iterator-chains-the-machinery)
4. [Closures inside chains](#4-closures-inside-chains)
5. [Adapter and consumer catalogue (with verified outputs)](#5-adapter-and-consumer-catalogue-with-verified-outputs)
6. [Order matters: the same adapters, different results](#6-order-matters-the-same-adapters-different-results)
7. [`collect`, `FromIterator`, and the turbofish](#7-collect-fromiterator-and-the-turbofish)
8. [Custom iterators and functions that return chains](#8-custom-iterators-and-functions-that-return-chains)
9. [`Option` and `Result` chains](#9-option-and-result-chains)
10. [The builder pattern](#10-the-builder-pattern)
11. [Text, slices, maps, and ordering chains](#11-text-slices-maps-and-ordering-chains)
12. [Real-world programs](#12-real-world-programs)
13. [Performance and complexity](#13-performance-and-complexity)
14. [Debugging chains and reading compiler errors](#14-debugging-chains-and-reading-compiler-errors)
15. [Async, streams, and parallel chains (not compiled)](#15-async-streams-and-parallel-chains-not-compiled)
16. [Go comparison](#16-go-comparison)
17. [Chain or loop? Style rules](#17-chain-or-loop-style-rules)
18. [The 5-pass method for reading any chain, and a cheat sheet](#18-the-5-pass-method-for-reading-any-chain-and-a-cheat-sheet)
19. [Active recall and practice](#19-active-recall-and-practice)

---

# 1. What method chaining really is

## 1.1 Concept

**Method chaining** means calling a method on the *result* of the previous method call, in one expression:

```rust
let result: Vec<i32> = nums
    .iter()                      // receiver: nums      -> returns Iter
    .filter(|&&x| x % 2 == 0)    // receiver: Iter      -> returns Filter<Iter, _>
    .map(|&x| x * x)             // receiver: Filter    -> returns Map<Filter<..>, _>
    .collect();                  // receiver: Map       -> returns Vec<i32>
```

Three ingredients make a chain possible. If you understand these three, you understand all chains:

| # | Ingredient | Meaning |
|---|---|---|
| 1 | **Every call is an expression with a value** | `a.b()` evaluates to something, and that something can be the receiver of the next `.c()`. |
| 2 | **Every call has a return type** | The type *after* each dot decides which methods are available at the *next* dot. |
| 3 | **Every call has a receiver kind** | The method takes `self` (consumes), `&self` (borrows), or `&mut self` (mutably borrows). This decides what happens to ownership. |

> **The single most useful habit:** after every `.`, write down the type that comes out. Most "I can't trace this" confusion is really "I don't know what type is flowing here."

## 1.2 The five families of chains

Rust chains look the same on the page but behave very differently. Classify first, then trace.

| Family | Example | Does each dot do work now? | What flows between dots |
|---|---|---|---|
| **Iterator chain** | `v.iter().map(f).filter(g).collect()` | **No.** Adapters only *build* a pipeline. Work happens when a *consumer* pulls. | A new iterator *struct* wrapping the previous one |
| **Option/Result chain** | `opt.map(f).and_then(g).unwrap_or(0)` | **Yes**, immediately, one step at a time | An `Option<T>` / `Result<T,E>` value |
| **Builder chain** | `Req::new(u).header(a,b).build()` | **Yes**, each call mutates/rebuilds config | The builder (by value, or `&mut` to it) |
| **Text/collection chain** | `s.trim().split(',').map(str::trim)` | Mixed: `trim` is immediate, `split` is lazy | `&str`, iterators, `String`s |
| **Async/stream chain** | `client.get(u).send().await?.json().await?` | Futures are lazy until `.await` | Futures, then values |

## 1.3 Why Rust is unusually good at chaining

```text
 +--------------------------+     +---------------------------+     +----------------------------+
 | Expression-oriented      |     | Traits + generics         |     | Monomorphization + inlining|
 | everything has a value   | --> | each adapter is its own   | --> | compiler generates a custom|
 | `x.f().g()` is just      |     | type: Map<I,F>,Filter<I,P>|     | loop for YOUR exact chain, |
 | nested expressions       |     | so no dynamic dispatch    |     | often as fast as a hand    |
 +--------------------------+     +---------------------------+     | written loop               |
                                                                    +----------------------------+
```

## 1.4 Method syntax is sugar for a plain function call

`a.method(b)` is shorthand for a *function call whose first argument is the receiver*. Verified:

```rust
let nums = vec![1, 2, 3, 4, 5, 6];
let a: Vec<i32> = nums.iter().map(|x| x * 2).collect();
let b: Vec<i32> = Iterator::map(nums.iter(), |x| x * 2).collect(); // same thing, spelled out
assert_eq!(a, b);
```

So this chain:

```text
nums.iter().map(f).collect()
```

is exactly this nesting (read inside-out):

```text
collect( map( iter(&nums), f ) )
```

> **Why chains exist:** the nested form reads *inside-out*; the chained form reads *left-to-right in the order things happen*. That is the entire point of method chaining. It is a readability feature on top of ordinary function composition.

## 1.5 How the compiler finds the method (auto-ref and auto-deref)

When you write `v.iter()` where `v: Vec<i32>`, the compiler does **not** find `iter` on `Vec`. It searches like this:

```text
Candidate receiver types, tried in order, for expression `v.iter()` with v: Vec<i32>

 Round 1: type = Vec<i32>
          try  Vec<i32>        (by value)    -> no method `iter` taking self
          try  &Vec<i32>       (auto-ref)    -> no
          try  &mut Vec<i32>   (auto-ref)    -> no
 Round 2: deref Vec<i32> -> [i32]    (Vec implements Deref<Target=[T]>)
          try  [i32]           (by value)    -> no
          try  &[i32]          (auto-ref)    -> YES: <[i32]>::iter(&self)   <-- chosen
```

Spelled out (verified):

```rust
let w = vec![1, 2, 3];
let a: Vec<&i32> = <[i32]>::iter(&w[..]).collect();
let b: Vec<&i32> = w.iter().collect();
assert_eq!(a, b);
println!("{} {}", w.len(), Vec::len(&w)); // 3 3
```

This is why you can write `v.iter()` without writing `(&v).iter()`: **auto-ref** inserted the `&` for you, and **auto-deref** walked from `Vec<T>` to `[T]`.

---

# 2. Ownership inside a chain: `self`, `&self`, `&mut self`

Every method in a chain has a **receiver kind**. It controls whether the previous value is *consumed*, *borrowed*, or *mutably borrowed*.

| Receiver | Meaning | After the call, can you still use the previous value? | Typical chain examples |
|---|---|---|---|
| `self` | **Consumes** the receiver (moves it in) | **No** (moved), unless the type is `Copy` | `Iterator::map`, `filter`, `collect`, `sum`; `Option::map`, `and_then`, `unwrap`; owned-builder methods |
| `&self` | Shared borrow | Yes | `Vec::len`, `str::trim`, `Option::is_some`, `Option::as_ref`, `slice::iter` |
| `&mut self` | Exclusive borrow | Yes, after the borrow ends | `Iterator::next`, `by_ref`, `Peekable::peek`, `Option::take`, `Vec::push`, `Command::arg` |

## 2.1 Why `into_iter()` then reusing the Vec fails

```rust
let v = vec![1, 2, 3];
let doubled: Vec<i32> = v.into_iter().map(|x| x * 2).collect();
println!("{:?}", v);   // error[E0382]: borrow of moved value: `v`
```

`into_iter(self)` takes `v` **by value**. `v` is gone after that dot.

```text
 v (owns heap buffer) --into_iter(self)--> IntoIter (now owns the buffer) --map--> Map --collect--> Vec (new buffer)
 ^
 v is dead here. Using it is a compile error.
```

The fix is to borrow instead: `v.iter()` (takes `&self`) leaves `v` alive.

## 2.2 Adapters consume the iterator before them

`Iterator::map(self, f)` **consumes** the iterator it is called on. That is why you can't use `it` again after `it.map(...)`. If you want to take some items and keep using the iterator, borrow it with `by_ref()` (which takes `&mut self` and returns `&mut Self`, and `&mut I` is itself an iterator). Verified:

```rust
let mut it = (1..=6).into_iter();
let first_two: Vec<i32> = it.by_ref().take(2).collect();
let rest: Vec<i32> = it.collect();
println!("{first_two:?} {rest:?}");   // [1, 2] [3, 4, 5, 6]
```

## 2.3 Temporaries live until the end of the statement

Every intermediate value in a chain is a **temporary**. A temporary is dropped at the end of the full statement (the `;`). This is harmless when each dot *returns a new owned value*, but it bites when a method returns a **reference into the temporary**:

```rust
struct CommandBuilder { args: Vec<String> }
impl CommandBuilder {
    fn new() -> Self { CommandBuilder { args: vec![] } }
    fn arg(&mut self, a: &str) -> &mut Self { self.args.push(a.into()); self }
    fn run(&self) {}
}
fn main() {
    let cmd = CommandBuilder::new().arg("-l");   // error[E0716]: temporary value dropped while borrowed
    cmd.run();
}
```

```text
 CommandBuilder::new()  -> creates a TEMPORARY builder          lives until the `;`
        .arg("-l")      -> returns &mut (pointer INTO that temporary)
 `;`                    -> temporary dropped
 cmd                    -> dangling pointer: compiler refuses
```

Two fixes (both verified later in [Chapter 10](#10-the-builder-pattern)):

```rust
// Fix 1: keep the builder in a variable, then chain on it
let mut cmd = CommandBuilder::new();
cmd.arg("-l").arg("-a");
cmd.run();

// Fix 2: finish the chain in ONE statement, ending with a method that returns an owned value
let out = CommandBuilder::new().arg("-l").arg("-a").run();
```

## 2.4 Quick decision rule

```text
Does the method take `self`?     -> the thing on its left is MOVED INTO the call (gone after).
Does it take `&self`/`&mut self`?-> the thing on its left is only BORROWED (still yours after, but
                                    the returned value may borrow from it, so watch lifetimes).
```

---

# 3. Iterator chains: the machinery

This is the chapter that makes the rest of the guide easy. Take your time with it.

## 3.1 The `Iterator` trait (the entire foundation)

```rust
trait Iterator {
    type Item;                                  // what this iterator yields
    fn next(&mut self) -> Option<Self::Item>;   // THE one required method

    // dozens of PROVIDED methods, all written in terms of next():
    // map, filter, fold, collect, sum, count, zip, chain, take, skip, ...
}
```

- `next()` returns `Some(item)` while items remain and `None` when exhausted.
- `next` takes `&mut self` because producing the next item **changes the iterator's internal position**.
- Every adapter and consumer you will ever call is just code that calls `next()` (directly or indirectly).

```text
        +-------------------+  next()   +--------------+
        |   Iterator state  | --------> | Option<Item> |
        | (a position, etc.)|           +--------------+
        +-------------------+      Some(x) = here is the next value (state advanced)
                                   None    = finished
```

## 3.2 `IntoIterator` and the three ways to iterate a collection

A `for` loop does not call `next()` on a collection. It first calls `into_iter()` to get an iterator:

```rust
for x in expr { body }
// is roughly:
let mut it = IntoIterator::into_iter(expr);
while let Some(x) = it.next() { body }
```

For a `Vec<T>` there are **three** flavours, and they differ in *ownership of the items*:

| You write | Calls | `Item` type | Effect on the Vec |
|---|---|---|---|
| `for x in &v` / `v.iter()` | `IntoIterator for &Vec<T>` | `&T` | borrows, Vec stays usable |
| `for x in &mut v` / `v.iter_mut()` | `IntoIterator for &mut Vec<T>` | `&mut T` | mutable borrow, can modify in place |
| `for x in v` / `v.into_iter()` | `IntoIterator for Vec<T>` | `T` | **moves** the Vec; items are moved out |

Verified:

```rust
let mut v = vec![1, 2, 3];
for x in &v { print!("{} ", x); }            // x: &i32      prints 1 2 3
for x in &mut v { *x += 10; }                // x: &mut i32
println!("{v:?}");                           // [11, 12, 13]
let owned: Vec<i32> = v.into_iter().collect(); // x: i32, v is moved
println!("{owned:?}");                       // [11, 12, 13]
```

```text
 v.iter()        -> yields &1, &2, &3      (pointers INTO the vec)       Item = &i32
 v.iter_mut()    -> yields &mut 1, ...     (exclusive pointers)          Item = &mut i32
 v.into_iter()   -> yields 1, 2, 3         (values moved OUT of the vec) Item = i32
```

> **Why this matters for chains:** the `Item` type decides whether your closures see `i32`, `&i32`, or `&&i32` (see [4.3](#43-what-each-adapter-hands-to-your-closure-and-the--patterns)). Most "weird `&&x` syntax" is simply the `Item` type of `.iter()`.

## 3.3 Adapters are just structs that wrap an iterator

An **adapter** is a struct holding (1) the previous iterator and (2) maybe a closure, and it implements `Iterator` by calling `next()` on the iterator it wraps.

Here are real, working re-implementations of `map` and `filter`. These are simplified versions of what the standard library does (verified):

```rust
struct MyMap<I, F> { iter: I, f: F }

impl<I: Iterator, B, F: FnMut(I::Item) -> B> Iterator for MyMap<I, F> {
    type Item = B;
    fn next(&mut self) -> Option<B> {
        let x = self.iter.next()?;   // 1) ask the stage BELOW for an item (None => we are done too)
        Some((self.f)(x))            // 2) transform it with my closure
    }
}

struct MyFilter<I, P> { iter: I, pred: P }

impl<I: Iterator, P: FnMut(&I::Item) -> bool> Iterator for MyFilter<I, P> {
    type Item = I::Item;
    fn next(&mut self) -> Option<I::Item> {
        loop {
            let x = self.iter.next()?;           // ask below
            if (self.pred)(&x) { return Some(x); } // keep it
            // rejected: loop and ask below again (we do NOT return to the caller)
        }
    }
}

// An "extension trait" is how `.my_map(...)` becomes available on every iterator:
trait MyIterExt: Iterator + Sized {
    fn my_map<B, F: FnMut(Self::Item) -> B>(self, f: F) -> MyMap<Self, F> { MyMap { iter: self, f } }
    fn my_filter<P: FnMut(&Self::Item) -> bool>(self, pred: P) -> MyFilter<Self, P> { MyFilter { iter: self, pred } }
}
impl<I: Iterator> MyIterExt for I {}

fn main() {
    let mine: Vec<i32> = (1..=6).my_filter(|x| x % 2 == 0).my_map(|x| x * x).collect();
    println!("{mine:?}");   // [4, 16, 36]
}
```

This is the **whole trick** behind `std`'s `Map` and `Filter`. Adding `.map(f)` to a chain just *wraps one more struct around the previous one*. The same extension-trait idea is how crates like `itertools` add methods to every iterator.

## 3.4 The type of a chain is a nested struct ("onion")

Let `chain = v.into_iter().map(f).filter(g);`. The compiler's real type for it (printed with `std::any::type_name`, shortened):

```text
Filter< Map< IntoIter<i32>, {closure f} >, {closure g} >
```

As nested values:

```text
Filter {
    pred: g                    // closure, 0 bytes (captures nothing)
    iter: Map {
        f:    f                // closure, 0 bytes (captures nothing)
        iter: IntoIter {       // the SOURCE, the only part with real data
            buf: 0x5000        // start of the heap allocation
            cap: 3
            ptr: 0x5000        // next element to yield
            end: 0x500C        // one past the last element
        }
    }
}
```

**Reading a chain left to right builds this onion from the inside out.** The first receiver is the core; every later method adds a layer.

## 3.5 Real memory layout (64-bit, measured)

```text
Vec<i32> `v = vec![1,2,3]` BEFORE into_iter()
 STACK (24 bytes)                         HEAP (3 x i32 = 12 bytes used)
 +------------------+
 | ptr  : 0x5000    |-------------------> 0x5000     0x5004     0x5008
 | cap  : 3         |                     +----------+----------+----------+
 | len  : 3         |                     |    1     |    2     |    3     |
 +------------------+                     +----------+----------+----------+
```

`v.into_iter()` **moves** the buffer ownership into `IntoIter` (32 bytes). Nothing in the heap is copied:

```text
 STACK: chain  (size_of_val = 32 bytes, measured)       HEAP buffer (unchanged)
 +----------------------+
 | buf : 0x5000         |--+
 | cap : 3              |  |      0x5000      0x5004      0x5008      0x500C
 | ptr : 0x5000         |--+----> +-----------+-----------+-----------+
 | end : 0x500C         |-----+   |     1     |     2     |     3     |
 +----------------------+     |   +-----------+-----------+-----------+
 closures f and g add 0 bytes |                                       ^
 (they capture nothing)       +---------------------------------------+
                                       `end` is one PAST the last element

 After IntoIter::next() returns Some(1):  `ptr` advanced by 4 bytes (size_of::<i32>())
   0x5000      0x5004      0x5008      0x500C
   +-----------+-----------+-----------+
   | (moved)   |     2     |     3     |
   +-----------+-----------+-----------+
               ^                       ^
              ptr                     end          exhausted when ptr == end
```

`v.iter()` is cheaper still: it **borrows** and holds only two pointers (16 bytes):

```text
 slice::Iter<'_, i32>  (16 bytes)
 +----------------+
 | ptr : 0x5000   |--> first element
 | end : 0x500C   |--> one past last
 +----------------+      Item = &i32 : a pointer INTO the vec's buffer
```

**Measured sizes** (rustc 1.75, 64-bit; implementation details, may change between versions):

| Type | `size_of` | Why |
|---|---|---|
| `Vec<i32>` | 24 | ptr + cap + len |
| `&[i32]` | 16 | ptr + len (a "fat pointer") |
| `slice::Iter<i32>` | 16 | start ptr + end ptr |
| `vec::IntoIter<i32>` | 32 | buf + cap + ptr + end |
| `Map<Iter, non-capturing closure>` | 16 | closure is zero-sized: `Map` adds **nothing** |
| `Map<Iter, move \|x\| x + offset>` | 24 | closure stores one `i32` (4 bytes, padded to 8) |
| `Filter<Map<IntoIter<i32>, f>, g>` | 32 | same as the source alone |
| `Iter.map.filter.take(5).enumerate()` | 32 | 16 (iter) + 8 (`take` counter) + 8 (`enumerate` counter) |
| `Option<&i32>` | 8 | null-pointer niche: `None` is the null pointer |
| `Option<Box<i32>>` | 8 | same niche |
| `Option<i32>` | 8 | 4-byte tag + 4-byte value |

Key takeaways: **a chain is a small stack value** (no heap allocation for adapters), and a long chain costs only the *state* each layer needs (a counter for `take`, a captured value for a `move` closure).

## 3.6 The pull model: who calls whom

Nothing happens while you build the chain. The **consumer at the end** (`collect`, `sum`, `for`, ...) *pulls* items by calling `next()` on the outermost layer, and each layer calls `next()` on the layer inside it.

Verified code (the prints let us watch the real order):

```rust
let v: Vec<i32> = vec![1, 2, 3]
    .into_iter()
    .map(|x| { println!("map {x}"); x * 2 })
    .filter(|&x| { println!("filter {x}"); x > 2 })
    .collect();
println!("{v:?}");
```

Real output:

```text
map 1
filter 2
map 2
filter 4
map 3
filter 6
[4, 6]
```

Now the **exact call stack**, indentation = who called whom:

```text
 1. collect() calls Filter::next()                    [outer call A]
 2.     Filter::next() calls Map::next()
 3.         Map::next() calls IntoIter::next()   -> returns Some(1)
 4.         Map::next() calls f(1)               -> prints "map 1",   returns 2
 5.     Map::next() returns Some(2)
 6.     Filter::next() calls g(&2)               -> prints "filter 2", false
 7.     (rejected, so Filter loops and asks again)
 8.     Filter::next() calls Map::next()
 9.         Map::next() calls IntoIter::next()   -> returns Some(2)
10.         Map::next() calls f(2)               -> prints "map 2",   returns 4
11.     Map::next() returns Some(4)
12.     Filter::next() calls g(&4)               -> prints "filter 4", true
13. Filter::next() returns Some(4)
14. collect() pushes 4          Vec = [4]

15. collect() calls Filter::next()                    [outer call B]
16.     Filter::next() calls Map::next()
17.         Map::next() calls IntoIter::next()   -> returns Some(3)
18.         Map::next() calls f(3)               -> prints "map 3",   returns 6
19.     Map::next() returns Some(6)
20.     Filter::next() calls g(&6)               -> prints "filter 6", true
21. Filter::next() returns Some(6)
22. collect() pushes 6          Vec = [4, 6]

23. collect() calls Filter::next()                    [outer call C]
24.     Filter::next() calls Map::next()
25.         Map::next() calls IntoIter::next()   -> returns None
26.     Map::next() returns None   (f is NOT called)
27. Filter::next() returns None  (g is NOT called)
28. collect() sees None, stops
```

Two directions, never confuse them:

```text
 CALL direction  (who asks):   collect  -->  Filter  -->  Map  -->  IntoIter      (outer to inner)
 VALUE direction (who gives):  IntoIter -->  Map  -->  Filter -->  collect        (inner to outer)
```

As a stack picture for one pull:

```text
 depth   frame                       state at its deepest point
   0     collect()
   1       Filter::next()
   2         Map::next()
   3           IntoIter::next()      returns Some(1)   <- frame popped, value flows UP
   2         Map::next()             f(1) = 2          prints "map 1"
   1       Filter::next()            g(&2) = false     prints "filter 2"  -> loop, go DOWN again
```

### Dry run table

| Pull # | Source yields | `map` f(x)=x*2 | `filter` g: >2 | `collect` Vec | closure calls so far |
|---|---|---|---|---|---|
| A (1st) | 1 | 2 | 2 > 2 = false, **drop**, loop | `[]` | f:1 g:1 |
| A (cont.) | 2 | 4 | 4 > 2 = true | `[4]` | f:2 g:2 |
| B | 3 | 6 | 6 > 2 = true | `[4, 6]` | f:3 g:3 |
| C | `None` | not called | not called | `[4, 6]` (done) | f:3 g:3 |

**Operation counts** for n = 3 inputs: `f` runs 3 times, `g` runs 3 times, 2 values are pushed. In general for n inputs: n calls to each per-element stage and at most n pushes. That is **O(n) time, one pass**.

## 3.7 Laziness: nothing runs until something pulls

```rust
let it = vec![1, 2, 3].into_iter().map(|x| { println!("never printed {x}"); x });
println!("built, nothing ran yet");
drop(it);
```

Output: `built, nothing ran yet`. The closure **never** ran. The compiler even warns you when you forget the consumer:

```rust
v.iter().map(|x| println!("{x}"));
// warning: unused `Map` that must be used
//   = note: iterators are lazy and do nothing unless consumed
// help: you might have meant to use `Iterator::for_each`
```

(`for_each` is a *consumer*; `map` is an *adapter*. For side effects, use `for_each` or a `for` loop.)

## 3.8 Short-circuiting: pulling stops as soon as the consumer is satisfied

Because the consumer pulls one at a time, it can stop early, and the **source is never asked for more**. Verified, even with an infinite source:

```rust
let found = (1..)                                  // infinite!
    .inspect(|x| println!("  source {x}"))
    .map(|x| x * x)
    .find(|&sq| sq > 10);
println!("{found:?}");
```

```text
  source 1
  source 2
  source 3
  source 4
Some(16)
```

`find` stopped at 4 (16 > 10). Items 5, 6, 7, ... were **never produced**. This is how `(1..)`, `cycle()`, and `repeat()` are safe to use.

Another verified example of lazy infinite sources:

```rust
let first: Vec<u64> = (1u64..).map(|x| x * x).filter(|x| x % 3 == 1).take(4).collect();
println!("{first:?}");   // [1, 4, 16, 25]
```

## 3.9 What the compiler does with a chain

Each adapter is a generic struct, and each closure has its own unique type. So for *your* chain the compiler **monomorphizes**: it generates specialized `next()` code for exactly `Filter<Map<IntoIter<i32>, closure1>, closure2>`. There is no dynamic dispatch and no boxing. Then the optimizer typically **inlines** all those tiny `next()` calls, and the whole chain commonly collapses to roughly this loop:

```rust
let mut out = Vec::new();
for x in v {                 // IntoIter::next
    let y = x * 2;           // Map
    if y > 2 { out.push(y); } // Filter + collect
}
```

> This fusion is what people mean by *zero-cost abstraction*. It is typical rather than guaranteed: it depends on the optimizer and on build mode. In an unoptimized **debug build** the individual `next()` frames from section 3.6 really exist on the stack and the chain can be noticeably slower than a loop. Always benchmark in `--release`.

---

# 4. Closures inside chains

## 4.1 The three closure traits

Every closure you pass is one of three kinds, chosen by what the closure *does* with the variables it captures:

| Trait | The closure body... | Can be called | Typical chain use |
|---|---|---|---|
| `Fn` | only **reads** captured variables | many times, shared | `map`, `filter` (read-only), `Option::map_or` |
| `FnMut` | **mutates** captured variables | many times, needs `&mut` | `for_each`, `scan`, counters, `fold` accumulation |
| `FnOnce` | **moves out** a captured variable | at most **once** | `Option::map` / `unwrap_or_else` take `FnOnce` |

Hierarchy: every `Fn` is also `FnMut`, and every `FnMut` is also `FnOnce`.

Verified examples:

```rust
fn apply_twice<F: Fn(i32) -> i32>(f: F, x: i32) -> i32 { f(f(x)) }
fn make_adder(n: i32) -> impl Fn(i32) -> i32 { move |x| x + n }
fn make_counter() -> impl FnMut() -> u32 { let mut c = 0; move || { c += 1; c } }
fn consume<F: FnOnce() -> String>(f: F) -> String { f() }

println!("{}", apply_twice(|x| x * 3, 2));          // 18
let add5 = make_adder(5);          println!("{}", add5(1));            // 6
let mut next = make_counter();     println!("{} {} {}", next(), next(), next()); // 1 2 3
let name = String::from("ann");    println!("{}", consume(move || name + "!"));   // ann!
```

An `FnMut` closure inside a chain (verified):

```rust
let mut cnt = 0;
[1, 2, 3].iter().for_each(|_| cnt += 1);
println!("{cnt}");   // 3
```

## 4.2 Capturing and `move`

A closure captures variables from its environment **by the weakest access it needs** (shared borrow, mutable borrow, or move). The `move` keyword forces capture **by value**.

```text
 let offset = 10;
 let it = v.iter().map(move |x| x + offset);     // the Map struct now STORES a copy of `offset`
                                                  //   Map { iter: Iter(16 B), f: { offset: i32 } }  -> 24 bytes (measured)
 let it = v.iter().map(|x| x + 1);                // captures nothing -> closure is 0 bytes -> Map is 16 bytes
```

You need `move` when the chain **outlives** the scope that owns the captured variable (returning an iterator, spawning a thread).

### A borrow-checker trap: mutating the collection you are iterating

```rust
let mut v = vec![1, 2, 3];
v.iter().for_each(|x| v.push(*x));   // error[E0502]: cannot borrow `v` as mutable because it is also borrowed as immutable
```

`v.iter()` holds a shared borrow of `v` for the *whole* chain; the closure needs a mutable borrow of the same `v`. Rust rejects it (it would invalidate the iterator mid-flight). Fix by collecting first, or restructure with indices.

### Edition 2021 helps with struct fields (disjoint capture)

```rust
struct Inventory { items: Vec<u32>, factor: u32 }
impl Inventory {
    fn scale(&mut self) { self.items.iter_mut().for_each(|i| *i *= self.factor); }
}
// verified: Inventory { items: [1,2,3], factor: 10 }.scale()  =>  [10, 20, 30]
```

The closure captures only `self.factor`, not all of `self`, so it doesn't conflict with the mutable borrow of `self.items`.

## 4.3 What each adapter hands to your closure, and the `&` patterns

This is the #1 source of `|&&x|` confusion. The rule is simple:

> **Closures that only need to *look* at an item get `&Item`. Closures that *consume* an item get `Item` by value.**

For `v.iter()`, `Item = &i32`. So (all of these were proven by compiling with explicit type annotations):

| Method | Closure receives | Type for `v.iter()` | Pattern to get a plain `i32` |
|---|---|---|---|
| `map`, `for_each`, `filter_map`, `flat_map`, `map_while`, `find_map` | `Item` | `&i32` | `\|&x\|` |
| `any`, `all`, `position` | `Item` | `&i32` | `\|&x\|` |
| `fold(init, \|acc, x\|)` | `Item` | `x: &i32` | `\|acc, &x\|` |
| `filter`, `find`, `take_while`, `skip_while`, `inspect` | **`&Item`** | **`&&i32`** | `\|&&x\|` |
| `max_by_key`, `min_by_key`, `max_by`, `min_by`, `partition` | **`&Item`** | **`&&i32`** | `\|&&x\|` or `\|x\| **x` |

Visual:

```text
 v.iter()  yields  &i32
                     |
   map(|x| ..)       x : &i32           -> pattern |&x|    gives i32
                     |
   filter(|x| ..)    x : &&i32  (a reference to the item, and the item is itself &i32)
                                       -> pattern |&&x|  gives i32
                                          or write  |x| **x > 1   (explicit derefs)
```

With `.copied()` (or `.cloned()`) you turn `Item = &i32` into `Item = i32`, so closures see simpler types:

```rust
let v = vec![1, 2, 3, 4];
let a: Vec<&i32> = v.iter().filter(|&&x| x > 1).collect();          // x: i32 via &&x
let b: Vec<&i32> = v.iter().filter(|x| **x > 1).collect();          // explicit double deref
let c: Vec<i32>  = v.iter().map(|&x| x * 2).collect();
let d: Vec<i32>  = v.iter().map(|x| x * 2).collect();               // &i32 * i32 works: Mul is implemented for &i32
let e: Vec<i32>  = v.iter().copied().filter(|x| *x > 1).collect();  // Item is i32; filter still gets &i32
let f: Vec<i32>  = v.iter().copied().filter(|&x| x > 1).collect();
// all of a..f print [2,3,4] / [2,4,6,8] as expected
```

The comparison trap (real compiler output):

```rust
let big: Vec<&i32> = v.iter().filter(|x| x > 1).collect();
// error[E0308]: mismatched types
//   expected `&&_`, found integer       <- x is &&i32, you compared it to the integer 1
```

## 4.4 Passing functions instead of closures

Any path to a function whose signature fits can replace a closure. It is shorter and often clearer (all verified):

```rust
let lens:   Vec<usize>      = ["a", "bb", "ccc"].into_iter().map(str::len).collect();       // [1, 2, 3]
let owned:  Vec<String>     = ["a", "b"].into_iter().map(String::from).collect();           // ["a", "b"]
let somes:  Vec<Option<i32>> = [1, 2].into_iter().map(Some).collect();                      // [Some(1), Some(2)]
let oks:    Vec<i32>        = ["1", "x", "3"].iter().map(|s| s.parse::<i32>()).filter_map(Result::ok).collect(); // [1, 3]
let trimmed: Vec<&str>      = [" a ", "b "].into_iter().map(str::trim).collect();           // ["a", "b"]
let upper:  Vec<String>     = ["ab"].into_iter().map(str::to_uppercase).collect();          // ["AB"]
```

`Some` (an enum variant constructor) and `Result::ok` (a method) are ordinary functions here. Use `str::trim` (not `String::trim`) because `trim` is defined on `str`.

**Rule:** if the closure is `|x| f(x)` with nothing else, replace it with `f`. If the types don't line up (extra `&`, different ownership), keep the closure.

---

# 5. Adapter and consumer catalogue (with verified outputs)

Three kinds of methods appear in an iterator chain. Learn to **label every dot** with one of them:

```text
   SOURCE            ADAPTERS (lazy, return an iterator)                  CONSUMER (eager, ends the chain)
 +-----------+     +-------+   +--------+   +------+   +-------+        +---------+
 | v.iter()  | --> | map   |-->| filter |-->| take |-->| rev   | -----> | collect |  -> Vec / String / Map / Result
 | 0..n      |     +-------+   +--------+   +------+   +-------+        | sum     |  -> number
 | s.chars() |     build a bigger struct, run NO code                   | count   |  -> usize
 | s.lines() |                                                          | find    |  -> Option<Item>
 +-----------+                                                          | for_each|  -> ()
                                                                        +---------+
                                                       the consumer DRIVES the whole chain by pulling
```

## 5.1 Sources

| Source | Yields (`Item`) | Notes |
|---|---|---|
| `v.iter()` / `iter_mut()` / `into_iter()` | `&T` / `&mut T` / `T` | [Section 3.2](#32-intoiterator-and-the-three-ways-to-iterate-a-collection) |
| `a..b`, `a..=b`, `a..` | integers | `a..` is **infinite**; combine with `take`, `find`, `take_while` |
| `s.chars()` | `char` | Unicode scalar values; **not** indexable, **not** `ExactSizeIterator` |
| `s.bytes()` | `u8` | raw UTF-8 bytes |
| `s.lines()` | `&str` | splits on `\n`, strips a trailing `\r` |
| `s.split(p)`, `s.split_whitespace()` | `&str` | `split` is lazy; `split_whitespace` skips runs of whitespace |
| `slice.windows(k)` | `&[T]` | **overlapping** windows of length `k` |
| `slice.chunks(k)` | `&[T]` | **non-overlapping** pieces, last may be shorter |
| `map.iter()`, `map.keys()`, `map.values()` | `(&K,&V)`, `&K`, `&V` | `HashMap` order is unspecified; sort if you need determinism |
| `std::iter::from_fn(f)` | whatever `f` returns | `f` returns `Option<T>`; `None` ends it |
| `std::iter::successors(first, f)` | `T` | each item computed from the previous one |
| `std::iter::repeat(x)` / `once(x)` / `empty()` | `T` | infinite repeat / single / none |

Verified generators:

```rust
let mut n = 0;
let evens: Vec<i32> = std::iter::from_fn(|| { n += 2; if n <= 10 { Some(n) } else { None } }).collect();
let pows: Vec<u32> = std::iter::successors(Some(1u32), |&x| x.checked_mul(10)).collect();
let rep: String = std::iter::repeat("ab").take(3).collect();
let once: Vec<i32> = std::iter::once(0).chain(1..3).collect();
// evens = [2, 4, 6, 8, 10]
// pows  = [1, 10, 100, ..., 1_000_000_000]   (stops when checked_mul overflows u32)
// rep   = "ababab"      once = [0, 1, 2]
```

## 5.2 Adapters (lazy)

Each of these *only builds a new struct*. Results below are real output.

| Adapter | What it does | Verified example | Result |
|---|---|---|---|
| `map(f)` | transform each item | `iter().filter(even).map(sq)` over 1..6 | `[4, 16, 36]` |
| `filter(p)` | keep items where `p` is true | (same chain) | |
| `filter_map(f)` | `map` + drop the `None`s (`f` returns `Option`) | `["1","x","3","","5"].iter().filter_map(\|s\| s.parse().ok())` | `[1, 3, 5]` |
| `flat_map(f)` | `map` then flatten one level | `words.iter().flat_map(\|w\| w.chars().take(2))` | `['a','p','b','a','c','h']` |
| `flatten()` | flatten one level (`Vec<Vec>`, `Option`s, ...) | `vec![vec![1,2],vec![3],vec![]]` / `vec![Some(1),None,Some(3)]` | `[1, 2, 3]` / `[1, 3]` |
| `enumerate()` | pair each item with its index | `["apple","banana","cherry"]` | `(0,apple) (1,banana) (2,cherry)` |
| `zip(other)` | pair items from two iterators; **stops at the shorter** | `[1,2,3].zip("ab".chars())` | `[(1,'a'),(2,'b')]` |
| `chain(other)` | all of the first, then all of the second | `(1..3).chain(7..9)` | `[1, 2, 7, 8]` |
| `take(n)` | first `n` items | `(1..=10).skip(2).take(3)` | `[3, 4, 5]` |
| `skip(n)` | drop the first `n` | (same) | |
| `take_while(p)` | take until `p` first fails, then **stop** | `[1,2,3,10,4]`, `x < 5` | `[1, 2, 3]` |
| `skip_while(p)` | drop until `p` first fails, then take **everything** | (same input) | `[10, 4]` |
| `map_while(f)` | like `take_while` + `map` in one (`f` returns `Option`) | `["1","2","x","4"]` parse | `[1, 2]` |
| `step_by(n)` | every `n`-th item, starting with the first | `(0..10).step_by(3)` | `[0, 3, 6, 9]` |
| `rev()` | reverse (needs a double-ended iterator) | `(1..4).rev()` | `[3, 2, 1]` |
| `scan(init, f)` | running state; `f(&mut state, item)` returns `Option` | running sum of `[1,2,3,4]` | `[1, 3, 6, 10]` |
| `cycle()` | repeat forever (clones the iterator) | `[1,2,3].iter().cycle().take(7)` | `[1,2,3,1,2,3,1]` |
| `peekable()` | adds `peek()` / `next_if()` to look ahead one item | run-length of `[1,1,2,2,2,3]` | `[(1,2),(2,3),(3,1)]` |
| `copied()` / `cloned()` | turn `&T` items into `T` (copy / clone) | `iter().copied()` | |
| `inspect(f)` | run `f(&item)` for side effects (debugging); passes item along | see [Chapter 14](#14-debugging-chains-and-reading-compiler-errors) | |
| `fuse()` | after the first `None`, guarantee `None` forever | | |
| `by_ref()` | borrow the iterator (`&mut I`) so you can resume it | [Section 2.2](#22-adapters-consume-the-iterator-before-them) | |

Slice methods that *produce* iterators and are handy mid-chain:

```rust
[1, 3, 6, 10].windows(2).map(|w| w[1] - w[0])               // [2, 3, 4]   differences of neighbours
[1, 2, 3, 4, 5].chunks(2).map(|c| c.iter().sum::<i32>())    // [3, 7, 5]   sum of each pair, last chunk is short
xs.iter().zip(xs.iter().skip(1)).map(|(a, b)| b - a)        // same idea as windows(2) with zip + skip(1)
xs.windows(2).all(|w| w[0] < w[1])                          // is strictly increasing?  (xs = [1,4,9,16] -> true)
```

`peekable` in full (verified), grouping equal neighbours:

```rust
let mut it = [1, 1, 2, 2, 2, 3].iter().peekable();
let mut groups = vec![];
while let Some(&x) = it.next() {
    let mut count = 1;
    while it.next_if(|&&y| y == x).is_some() { count += 1; }   // consume only while the NEXT item equals x
    groups.push((x, count));
}
println!("{groups:?}");   // [(1, 2), (2, 3), (3, 1)]
```

## 5.3 Consumers (eager, they pull)

| Consumer | Returns | Short-circuits? | Verified example | Result |
|---|---|---|---|---|
| `collect()` | any `FromIterator` type | no | see [Chapter 7](#7-collect-fromiterator-and-the-turbofish) | |
| `sum()`, `product()` | number | no | `(1..=4).sum::<i32>()`, `.product::<i32>()` | `10`, `24` |
| `count()` | `usize` | no | `(1..=4).count()` | `4` |
| `last()`, `nth(n)` | `Option<Item>` | `nth` stops at `n` | `(1..=4).last()`, `.nth(1)` | `Some(4)`, `Some(2)` |
| `fold(init, f)` | accumulator type | no | `(1..=5).fold(0, \|acc, x\| acc + x)` | `15` |
| `reduce(f)` | `Option<Item>` (no initial value) | no | `(1..=5).reduce(\|a, b\| a.max(b))` | `Some(5)` |
| `any(p)` / `all(p)` | `bool` | **yes** | `[1,2,3]`: `x>2` | `true` / `false` |
| `find(p)` | `Option<Item>` | **yes** | `[5,6,7].find(>5)` | `Some(6)` |
| `position(p)` | `Option<usize>` | **yes** | `[5,6,7]` pos of 7 | `Some(2)` |
| `find_map(f)` | `Option<B>` | **yes** | `["a","12","b"]` first that parses | `Some(12)` |
| `max_by_key(k)` / `min_by_key(k)` | `Option<Item>` | no | longest / shortest of `apple, banana, cherry` | `Some("cherry")` / `Some("apple")` |
| `max_by(cmp)` / `min_by(cmp)` | `Option<Item>` | no | floats `[2.5, 9.1, 3.3]` with `partial_cmp` | `Some(9.1)` |
| `try_fold(init, f)` | `Option`/`Result` of accumulator | **yes** (on `None`/`Err`) | checked add of `[1,2,3]` / `[100i8,100]` | `Some(6)` / `None` |
| `partition(p)` | `(B, B)` | no | split `1..=6` by even | `([2,4,6],[1,3,5])` |
| `unzip()` | `(A, B)` | no | `[(1,'a'),(2,'b')]` | `([1,2], ['a','b'])` |
| `for_each(f)` | `()` | no | `[1,2,3].for_each(\|_\| cnt += 1)` | `cnt == 3` |

**Ties matter:** `max_by_key` returns the **last** maximal element, `min_by_key` the **first** minimal one. With `["apple","banana","cherry"]` and `len`, `banana` and `cherry` both have length 6, and the result was `"cherry"`.

**Floats are not `Ord`**, so `.max()` / `.min()` don't compile on `f64`. Use `max_by(|a, b| a.partial_cmp(b).unwrap())`, or `total_cmp` (verified: `fl.sort_by(|a, b| b.total_cmp(a))` sorted `[2.5, -1.0, 9.0]` into `[9.0, 2.5, -1.0]`; note the vector needed a concrete type `Vec<f64>` for `total_cmp` to resolve).

**`try_fold` verified:**

```rust
let tf:  Option<i32> = [1, 2, 3].iter().try_fold(0i32, |acc, &x| acc.checked_add(x));   // Some(6)
let tf2: Option<i8>  = [100i8, 100].iter().try_fold(0i8, |acc, &x| acc.checked_add(x)); // None  (200 overflows i8)
```

## 5.4 Comparing whole iterators

```rust
[1, 2, 3].iter().eq([1, 2, 3].iter())   // true
[1, 2].iter().cmp([1, 3].iter())        // Less     (lexicographic)
```

---

# 6. Order matters: the same adapters, different results

Adapters are **not commutative**. Swapping two dots changes the meaning, and sometimes the performance.

## 6.1 Verified examples

```rust
(1..=10).skip(1).step_by(3)   // [2, 5, 8]      skip 1 first -> 2..=10, then every 3rd
(1..=10).step_by(3).skip(1)   // [4, 7, 10]     every 3rd -> 1,4,7,10, then skip the first

(1..=10).filter(|x| x % 2 == 0).take(2)   // [2, 4]   find 2 evens
(1..=10).take(2).filter(|x| x % 2 == 0)   // [2]      take 2 items (1,2) THEN keep evens
```

```text
 skip(1).step_by(3):   1  [2] 3  4  [5] 6  7  [8] 9  10        picks 2, 5, 8
 step_by(3).skip(1):  [1] 2  3 [4] 5  6 [7] 8  9 [10]          step gives 1,4,7,10 -> skip 1 -> 4,7,10
```

## 6.2 `rev()` and `enumerate()`: the index changes meaning

```rust
"abc".chars().rev().enumerate()           // [(0,'c'), (1,'b'), (2,'a')]   indices count the REVERSED order
[7, 8, 9].iter().enumerate().rev()        // [(2,9), (1,8), (0,7)]          indices keep the ORIGINAL positions
```

## 6.3 Some orders are rejected by the type system

`rev()` needs `DoubleEndedIterator`; `enumerate().rev()` needs the inner iterator to also be `ExactSizeIterator` (it must know how long it is to number from the back). `Chars` is not exact-size, because UTF-8 characters have 1 to 4 bytes:

```rust
"abc".chars().enumerate().rev()
// error[E0277]: the trait bound `Chars<'_>: ExactSizeIterator` is not satisfied
```

Verified capability facts:

```rust
let mut de = [1, 2, 3, 4].iter();
println!("{:?} {:?} {:?} len={}", de.next(), de.next_back(), de.next(), de.len());
// Some(1) Some(4) Some(2) len=1       <- iterating from both ends; len() works because slice::Iter is ExactSize

(0..10).size_hint()                          // (10, Some(10))   exact
(0..10).filter(|x| x % 2 == 0).size_hint()   // (0, Some(10))    filter can't know how many survive
```

```text
 Capabilities flow THROUGH adapters:
   slice::Iter  = DoubleEnded + ExactSize
   .map(f)      keeps both                  .rev()  ok     .len() ok
   .filter(p)   keeps DoubleEnded only      .rev()  ok     .len() NOT available (count unknown)
   .enumerate() is ExactSize if inner is; DoubleEnded only if inner is BOTH ExactSize and DoubleEnded
                (so enumerate().rev() works on slices but not on chars())
   .chars()     DoubleEnded only            .rev() ok      enumerate().rev() NOT allowed
```

## 6.4 Performance rule of thumb for ordering

```text
 Cheap-and-selective FIRST            Expensive LAST
   .filter(cheap_check)               .map(expensive_transform)
   .take(n)                           .collect()
 -> fewer items reach the expensive stages
 -> take() before expensive work means the expensive closure runs at most n times
```

---

# 7. `collect`, `FromIterator`, and the turbofish

## 7.1 Why `collect` needs a type annotation

```rust
trait FromIterator<A>: Sized {
    fn from_iter<I: IntoIterator<Item = A>>(iter: I) -> Self;
}
// Iterator::collect is roughly:
fn collect<B: FromIterator<Self::Item>>(self) -> B { B::from_iter(self) }
```

`collect` is **generic over its return type `B`**. Many types implement `FromIterator<i32>` (`Vec<i32>`, `HashSet<i32>`, `VecDeque<i32>`, `BinaryHeap<i32>`, ...), so Rust cannot guess; **you must say which**.

```rust
let doubled = v.iter().map(|x| x * 2).collect();
// error[E0283]: type annotations needed
//   = note: cannot satisfy `_: FromIterator<i32>`
// help: consider giving `doubled` an explicit type
```

Four ways to tell it:

```rust
let a: Vec<i32>   = it.collect();               // annotate the variable
let b = it.collect::<Vec<i32>>();               // turbofish: ::<...> after the method name
let c = it.collect::<Vec<_>>();                 // let the compiler infer the element type with `_`
fn f() -> Vec<i32> { it.collect() }             // the return type decides
```

`sum` and `product` have the same issue (`error[E0283]: cannot satisfy _: Sum<i32>`): write `let total: i32 = ...sum();` or `.sum::<i32>()`.

## 7.2 What you can collect into (verified)

```rust
let words = ["a", "bb", "a", "ccc"];
let set: HashSet<&str>             = words.iter().copied().collect();                  // 3 distinct
let lens: BTreeMap<&str, usize>    = words.iter().map(|w| (*w, w.len())).collect();    // {"a":1,"bb":2,"ccc":3}
let s: String                      = words.iter().copied().collect();                  // "abbaccc"  (concatenates &str)
let rev: String                    = "hello".chars().rev().collect();                  // "olleh"
let v = (1..=3).collect::<Vec<_>>();                                                   // [1, 2, 3]
```

Note the `BTreeMap`: `"a"` appears twice; when keys repeat, **the later pair overwrites the earlier one**.

## 7.3 Collecting `Result` and `Option`: "all or nothing"

```rust
let r:  Result<Vec<i32>, _> = ["1","2","3"].iter().map(|s| s.parse::<i32>()).collect(); // Ok([1, 2, 3])
let r2: Result<Vec<i32>, _> = ["1","x","3"].iter().map(|s| s.parse::<i32>()).collect(); // Err(ParseIntError { kind: InvalidDigit })
let o:  Option<Vec<i32>>    = [Some(1), Some(2)].into_iter().collect();                 // Some([1, 2])
let o2: Option<Vec<i32>>    = [Some(1), None].into_iter().collect();                    // None
```

```text
 items:   Ok(1)    Ok(2)    Err(e)    Ok(4)  ...
 collect::<Result<Vec<_>,_>>():
           push 1   push 2   SEES Err  --> stop pulling, return Err(e)       (Ok(4) is never pulled)
 If it reaches the end with no Err:  returns Ok(vec_of_all_values)
```

This is the idiomatic way to turn `Vec<Result<T,E>>` into `Result<Vec<T>,E>`. The same works for `sum`/`product` (verified):

```rust
let total: Result<i32, _> = ["1", "2"].iter().map(|s| s.parse::<i32>()).sum();   // Ok(3)
```

## 7.4 Splitting results: `partition` and `unzip`

When you want **both** the successes and the failures instead of stopping at the first error (verified in [Chapter 11](#11-text-slices-maps-and-ordering-chains)):

```rust
let (ok, bad): (Vec<_>, Vec<_>) = lines.map(parse_line).partition(|r| r.is_ok());
let good:   Vec<Person> = ok.into_iter().map(Result::unwrap).collect();   // safe: all are Ok
let errors: Vec<String> = bad.into_iter().filter_map(Result::err).collect();
```

`unzip` is the inverse of `zip`: `let (nums, chars): (Vec<i32>, Vec<char>) = pairs.into_iter().unzip();`

## 7.5 Other terminal ways to materialize

`Vec::extend(iter)` appends an iterator into an existing collection without creating an intermediate `Vec`; `String::from_iter`, `HashMap::from_iter`, etc. are the same trait called directly.

---

# 8. Custom iterators and functions that return chains

## 8.1 Write `next()` once, get every adapter for free

```rust
struct Fib { a: u64, b: u64 }
impl Fib { fn new() -> Self { Fib { a: 0, b: 1 } } }

impl Iterator for Fib {
    type Item = u64;
    fn next(&mut self) -> Option<u64> {
        let r = self.a;
        let next = self.a.checked_add(self.b)?;   // stop (None) instead of overflowing
        self.a = self.b;
        self.b = next;
        Some(r)
    }
}

let v: Vec<u64> = Fib::new().take_while(|&n| n < 100).filter(|n| n % 2 == 0).collect();
println!("{v:?}");   // [0, 2, 8, 34]
```

Dry run (the sequence is `0 1 1 2 3 5 8 13 21 34 55 89 144 ...`):

| Pull | `Fib::next` yields | `take_while(<100)` | `filter(even)` | collected |
|---|---|---|---|---|
| 1 | 0 | pass | keep | `[0]` |
| 2, 3 | 1, 1 | pass | drop, drop | `[0]` |
| 4 | 2 | pass | keep | `[0, 2]` |
| 5, 6 | 3, 5 | pass | drop, drop | `[0, 2]` |
| 7 | 8 | pass | keep | `[0, 2, 8]` |
| 8..9 | 13, 21 | pass | drop | |
| 10 | 34 | pass | keep | `[0, 2, 8, 34]` |
| 11, 12 | 55, 89 | pass | drop | |
| 13 | 144 | **fails** -> `take_while` ends | | done |

`Fib` is infinite in spirit; `take_while` is what ends it. **Lazy pull** is what makes that safe.

## 8.2 Making your own collection work with `for` and chains

```rust
struct Stack<T> { items: Vec<T> }

impl<T> Stack<T> {
    // top of the stack first. `impl Iterator` hides the long concrete type.
    fn iter(&self) -> impl Iterator<Item = &T> + '_ { self.items.iter().rev() }
}

impl<'a, T> IntoIterator for &'a Stack<T> {
    type Item = &'a T;
    type IntoIter = std::iter::Rev<std::slice::Iter<'a, T>>;
    fn into_iter(self) -> Self::IntoIter { self.items.iter().rev() }
}

let s = Stack { items: vec![1, 2, 3] };
println!("{:?}", s.iter().collect::<Vec<_>>());   // [3, 2, 1]
for x in &s { print!("{x} "); }                   // 3 2 1
```

```text
 Stack { items: [1, 2, 3] }          bottom -> top
                                       1  2  3
 .iter() = items.iter().rev()          3  2  1     (top first)
```

## 8.3 Returning a chain: `impl Iterator` vs `Box<dyn Iterator>`

You cannot write the real type of a chain (it contains closure types, which have no names). Two solutions:

```rust
// (A) impl Iterator: ONE concrete type, hidden. Static dispatch, no heap, fastest.
fn evens_squared(v: &[i32]) -> impl Iterator<Item = i32> + '_ {
    v.iter().filter(|&&x| x % 2 == 0).map(|&x| x * x)
}

// (B) Box<dyn Iterator>: type-erased, can return DIFFERENT concrete types from different branches.
fn pick<'a>(flag: bool, v: &'a [i32]) -> Box<dyn Iterator<Item = &'a i32> + 'a> {
    if flag { Box::new(v.iter()) } else { Box::new(v.iter().rev()) }
}

println!("{:?}", evens_squared(&[1, 2, 3, 4]).collect::<Vec<_>>());                  // [4, 16]
println!("{:?} {:?}", pick(true, &[1,2,3]).collect::<Vec<_>>(), pick(false, &[1,2,3]).collect::<Vec<_>>()); // [1, 2, 3] [3, 2, 1]
```

| | `impl Iterator` | `Box<dyn Iterator>` |
|---|---|---|
| Concrete type | exactly one | can differ per branch |
| Dispatch | static (inlined) | dynamic (vtable call per `next`) |
| Allocation | none | one heap `Box` |
| Use when | one shape of chain | `if/else` branches return different iterator types (`Iter` vs `Rev<Iter>`) |

**The `+ '_` is required here.** The returned iterator *borrows* `v`, and the compiler must be told. Without it (edition 2021, rustc 1.75):

```rust
fn evens(v: &Vec<i32>) -> impl Iterator<Item = i32> {
    v.iter().filter(|&&x| x % 2 == 0).map(|&x| x)
}
// error[E0700]: hidden type for `impl Iterator<Item = i32>` captures lifetime that does not appear in bounds
// help: ... you can add an explicit `'_` lifetime bound
```

(Newer editions relax this rule so that return-position `impl Trait` captures in-scope lifetimes automatically; on 2021 you still write `+ '_`.)

---

# 9. `Option` and `Result` chains

Unlike iterator chains, **these run immediately**, one step at a time. There is no laziness. The mental model is a **railway with two tracks**.

## 9.1 The railway model

```text
 Result<T, E> chain:     parse(s).and_then(check).map(double)

                       +--------+      +--------+      +--------+
  Ok track   --------->| parse  |--Ok->| check  |--Ok->| double |-----> Ok(final)
                       +--------+      +--------+      +--------+
                            |               |
                            | Err(e)        | Err(e)
                            v               v
  Err track  --------------------------------------------------------> Err(e)
              Once on the Err track you STAY there: later closures are skipped, `e` rides along.

 Option<T> is the same railway with "Some track" and "None track" (None carries no payload).
```

## 9.2 `map` vs `and_then`: the rule that removes most confusion

> **If your closure returns a plain value `U`, use `map`. If your closure returns an `Option<U>` / `Result<U,E>` itself, use `and_then`.**

```text
 Some(4).map(|x| Some(x + 1))       -> Some(Some(5))   Option<Option<i32>>   <- nested! usually a bug
 Some(4).and_then(|x| Some(x + 1))  -> Some(5)         Option<i32>            <- flattened

 map(f)      : Some(x) -> Some( f(x) )          f: T -> U
 and_then(f) : Some(x) ->       f(x)            f: T -> Option<U>
 (both)      : None    -> None                   f is not called
```

(`and_then` is also called *flat-map* or *bind*; it is `map` followed by `flatten`, and `Some(Some(3)).flatten()` gives `Some(3)`, verified.)

## 9.3 Combinator catalogue (verified outputs)

| Method | Meaning | Example | Result |
|---|---|---|---|
| `map(f)` | transform the `Some`/`Ok` value | `Some(2).map(\|x\| x*10)` | `Some(20)` |
| `and_then(f)` | chain a step that can itself fail | `s.split('@').nth(1)` inside a chain | see below |
| `filter(p)` | `Some(x)` only if `p(&x)` | `Some(4).filter(\|x\| x%2==0)` / `Some(3)...` | `Some(4)` / `None` |
| `ok_or(e)` / `ok_or_else(f)` | `Option` -> `Result` | `opt.ok_or_else(\|\| "missing")` | |
| `ok()` / `err()` | `Result` -> `Option` | `"7".parse::<i32>().ok()` | `Some(7)` |
| `map_err(f)` | transform the **error** only | `.map_err(\|e\| format!("bad: {e}"))` | |
| `unwrap_or(d)` | value or a default (**eager**) | | |
| `unwrap_or_else(f)` | value or compute default (**lazy**) | | |
| `unwrap_or_default()` | value or `Default::default()` | `None::<String>.unwrap_or_default().len()` | `0` |
| `map_or(d, f)` | `f(value)` or default `d` | `Some(2).map_or(0, \|x\| x*10)` / `None` | `20` / `0` |
| `or(o)` / `or_else(f)` | fallback `Option`/`Result` | `None.or_else(\|\| Some(9))` | `Some(9)` |
| `and(o)` / `xor(o)` | combine two options | `Some(1).and(Some(2))`, `Some(1).xor(None)` | `Some(2)`, `Some(1)` |
| `zip(o)` | both present -> tuple | `Some(1).zip(Some('a'))` | `Some((1,'a'))` |
| `is_some_and(p)` | present **and** predicate holds | `Some(5).is_some_and(\|x\| x>3)` | `true` |
| `take()` | **move the value out**, leave `None` | `let t = slot.take()` | `t = Some(3)`, `slot = None` |
| `flatten()` | `Option<Option<T>>` -> `Option<T>` | | `Some(3)` |
| `copied()` / `cloned()` | `Option<&T>` -> `Option<T>` | `v.first().copied()` | `Some(10)` |
| `as_ref()` / `as_mut()` | `&Option<T>` -> `Option<&T>` (borrow instead of move) | | |
| `as_deref()` | `Option<String>` -> `Option<&str>` | | |
| `transpose()` | `Option<Result<T,E>>` <-> `Result<Option<T>,E>` | `Some("5").map(parse).transpose()` | `Ok(Some(5))` |

The `transpose` and `as_ref` examples, verified:

```rust
let o: Option<&str> = Some("5");
let t: Result<Option<i32>, _> = o.map(|s| s.parse::<i32>()).transpose();   // Ok(Some(5))

let name = Some(String::from("hi"));
let len = name.as_ref().map(|s| s.len());         // Some(2); `as_ref` borrows so `name` is NOT consumed
println!("{len:?} still usable {name:?}");        // Some(2) still usable Some("hi")
```

**Why `as_ref` matters:** `Option::map(self, f)` takes `self` by value. On `Option<String>` it would **move the `String` out** and leave `name` unusable. `as_ref()` makes an `Option<&String>` view first.

## 9.4 Eager vs lazy variants (`_else`)

```rust
fn expensive(tag: &str) -> i32 { println!("  expensive({tag}) ran"); 0 }

println!("eager:");
let _ = Some(1).unwrap_or(expensive("unwrap_or"));              // argument is evaluated BEFORE the call
println!("lazy:");
let _ = Some(1).unwrap_or_else(|| expensive("unwrap_or_else")); // closure only runs on None
```

Real output:

```text
eager:
  expensive(unwrap_or) ran        <- ran even though the value was Some(1)!
lazy:                             <- closure never ran
```

**Rule:** if the default is a constant or a cheap value, `unwrap_or` is fine. If it allocates, calls a function, or has side effects, use the `_else` form. Same for `ok_or` / `ok_or_else`, `or` / `or_else`.

## 9.5 Real world: reading a port from a config map (railway in action)

```rust
fn get_port(cfg: &HashMap<String, String>) -> Result<u16, String> {
    cfg.get("port")                                                  // Option<&String>
        .ok_or_else(|| "missing 'port'".to_string())                 // Result<&String, String>
        .and_then(|s| s.trim().parse::<u16>()                        // Result<u16, ParseIntError>
            .map_err(|e| format!("invalid port {s:?}: {e}")))        //   ...converted to Result<u16, String>
        .and_then(|p| if p >= 1024 { Ok(p) } else { Err(format!("port {p} is privileged")) })
}
```

Type after each dot:

```text
cfg                                   : &HashMap<String,String>
.get("port")                          : Option<&String>
.ok_or_else(|| ...)                   : Result<&String, String>
.and_then(|s| ...parse...map_err)     : Result<u16, String>        (closure returns a Result, so and_then)
.and_then(|p| if ... {Ok} else {Err}) : Result<u16, String>
```

Verified outputs:

```text
config empty            -> Err("missing 'port'")
port = " 80 "           -> Err("port 80 is privileged")
port = "abc"            -> Err("invalid port \"abc\": invalid digit found in string")
port = "8080"           -> Ok(8080)
```

The **same logic written with `?`** (verified identical results):

```rust
fn get_port_q(cfg: &HashMap<String, String>) -> Result<u16, String> {
    let raw = cfg.get("port").ok_or("missing 'port'")?;
    let port: u16 = raw.trim().parse().map_err(|e| format!("invalid port {raw:?}: {e}"))?;
    if port < 1024 { return Err(format!("port {port} is privileged")); }
    Ok(port)
}
```

`?` means "on `Err(e)` / `None`, **return early** (converting the error with `From`); otherwise unwrap". It is the railway's *exit ramp*.

**Which style?** Combinator chains read well for short pure transformations. Use `?` when you have several steps, need early returns, or would otherwise nest closures. Both compile to similar code.

## 9.6 More real-world `Option` chains

```rust
// Optional nested data: customer.address?.zip  (verified: Some("500001"), None, None)
fn zip_of(c: &Customer) -> Option<&str> {
    c.address.as_ref().and_then(|a| a.zip.as_deref())
}

// Environment variable with a default (verified: prints 8080 when the variable is not set)
let port: u16 = std::env::var("MY_APP_PORT").ok().and_then(|s| s.parse().ok()).unwrap_or(8080);

// Email domain (verified: Some("example.com") and None)
fn domain(user: &User) -> Option<&str> {
    user.email.as_deref().and_then(|e| e.split('@').nth(1))
}
```

Reading the `std::env::var` chain:

```text
std::env::var("MY_APP_PORT")  : Result<String, VarError>
.ok()                         : Option<String>        (error details discarded: we only care "set or not")
.and_then(|s| s.parse().ok()) : Option<u16>           (parse failure also becomes None; u16 inferred from the let type)
.unwrap_or(8080)              : u16                   (any failure along the way -> default)
```

### The `?` mismatch (real compiler error)

```rust
fn parse(s: &str) -> Option<i32> {
    let n = s.parse::<i32>()?;      // error[E0277]: the `?` operator can only be used on `Option`s, not `Result`s,
    Some(n)                         //               in a function that returns `Option`
}
```

`?` cannot silently mix families. Convert explicitly: `s.parse::<i32>().ok()?` (Result -> Option) or `.ok_or(...)?` (Option -> Result).

---

# 10. The builder pattern

A builder collects configuration step by step and produces the final value at the end. There are **two styles**, and the difference is purely about receiver kinds from [Chapter 2](#2-ownership-inside-a-chain-self-self-mut-self).

## 10.1 Style A: owned builder (`self -> Self`)

Each method **consumes** the builder and **returns it back**. The builder *moves* down the chain.

```text
 RequestBuilder::new(url) --move--> .method("POST") --move--> .header(..) --move--> .body(..) --move--> .build()
       [builder]                      [same builder]            [same builder]       [same builder]       [Request]
 Each arrow passes OWNERSHIP forward. No borrow lasts beyond a single call, so no lifetime issues.
```

```rust
#[derive(Debug)]
struct Request { method: String, url: String, headers: Vec<(String, String)>, body: Option<String>, timeout_ms: u64 }

struct RequestBuilder { method: String, url: String, headers: Vec<(String, String)>, body: Option<String>, timeout_ms: u64 }

impl RequestBuilder {
    fn new(url: impl Into<String>) -> Self {
        RequestBuilder { method: "GET".into(), url: url.into(), headers: vec![], body: None, timeout_ms: 30_000 }
    }
    fn method(mut self, m: &str) -> Self { self.method = m.to_string(); self }
    fn header(mut self, k: &str, v: &str) -> Self { self.headers.push((k.into(), v.into())); self }
    fn body(mut self, b: impl Into<String>) -> Self { self.body = Some(b.into()); self }
    fn timeout_ms(mut self, ms: u64) -> Self { self.timeout_ms = ms; self }

    fn build(self) -> Result<Request, String> {            // consumes: can MOVE the fields out, no cloning
        if self.url.is_empty() { return Err("url is empty".into()); }
        if self.method == "GET" && self.body.is_some() { return Err("GET cannot have a body".into()); }
        Ok(Request { method: self.method, url: self.url, headers: self.headers, body: self.body, timeout_ms: self.timeout_ms })
    }
}

let req = RequestBuilder::new("https://api.example.com/users")
    .method("POST")
    .header("Content-Type", "application/json")
    .header("Authorization", "Bearer abc123")
    .body(r#"{"name":"ann"}"#)
    .timeout_ms(5_000)
    .build();
println!("{req:#?}");
println!("{:?}", RequestBuilder::new("x").body("oops").build().map(|_| ()));   // Err("GET cannot have a body")
```

Notes:

- `mut self` means "I take ownership **and** may mutate my own copy". It is not a mutable borrow.
- `impl Into<String>` lets callers pass `&str` or `String`.
- Validation lives in `build()`, so invalid combinations are caught in **one place** and returned as a `Result`.
- Conditional configuration with an owned builder must **reassign**: `if verbose { b = b.header("X-Debug", "1"); }`.

## 10.2 Style B: `&mut` builder (`&mut self -> &mut Self`)

Each method **mutably borrows** the builder and returns the **same borrow**, so the builder stays in one stack slot. This is how `std::process::Command` works.

```text
 let mut cmd = CommandBuilder::new("git");        cmd lives in ONE stack slot for the whole time
 cmd.arg("log")        returns &mut cmd  (a pointer back to that slot)
    .arg("--oneline")  returns &mut cmd
    .env("K", "V")     returns &mut cmd
 cmd.run()             uses &cmd
```

```rust
struct CommandBuilder { program: String, args: Vec<String>, env: Vec<(String, String)> }

impl CommandBuilder {
    fn new(p: &str) -> Self { CommandBuilder { program: p.into(), args: vec![], env: vec![] } }
    fn arg(&mut self, a: &str) -> &mut Self { self.args.push(a.into()); self }
    fn env(&mut self, k: &str, v: &str) -> &mut Self { self.env.push((k.into(), v.into())); self }
    fn run(&self) -> String {
        let envs: Vec<String> = self.env.iter().map(|(k, v)| format!("{k}={v}")).collect();
        format!("{} {} {}", envs.join(" "), self.program, self.args.join(" ")).trim().to_string()
    }
}

let mut cmd = CommandBuilder::new("git");
cmd.arg("log").arg("--oneline").env("GIT_PAGER", "cat");
println!("{}", cmd.run());                                            // GIT_PAGER=cat git log --oneline
println!("{}", CommandBuilder::new("ls").arg("-l").arg("-a").run());   // ls -l -a
```

The second form is a **single statement**: the temporary builder lives until the `;`, and `run()` returns an owned `String`, so nothing dangles. The real standard library does exactly this (verified):

```rust
let out = std::process::Command::new("echo").arg("hello").arg("world").output().unwrap();
println!("{}", String::from_utf8_lossy(&out.stdout).trim());   // hello world
```

**The gotcha** (real compiler error, shown in [Section 2.3](#23-temporaries-live-until-the-end-of-the-statement)): binding the middle of a `&mut` chain to a variable, `let cmd = Builder::new().arg("-l");`, fails with `E0716: temporary value dropped while borrowed`.

## 10.3 Which style should you use?

| | Owned (`self -> Self`) | `&mut` (`&mut self -> &mut Self`) |
|---|---|---|
| One-expression chain ending in `build()` | yes | yes (if the last call returns an owned value) |
| Configure conditionally in `if`/loops | must reassign `b = b.x()` | natural: `b.x();` |
| `let b = Builder::new().x();` | fine | **E0716** (temporary dropped) |
| Final step can move fields out (no clone) | yes (`build(self)`) | no: only `&self`, so clone or take |
| Real-world example | many crates' builders | `std::process::Command` |

## 10.4 Typestate builder: make invalid states unrepresentable

The compiler can enforce "you must set the URL and port before `connect()`" by encoding progress **in the type**. (Verified.)

```rust
use std::marker::PhantomData;
struct Missing; struct Present;

struct Conn<U, P> { url: Option<String>, port: Option<u16>, _m: PhantomData<(U, P)> }

impl Conn<Missing, Missing> {
    fn new() -> Self { Conn { url: None, port: None, _m: PhantomData } }
}
impl<P> Conn<Missing, P> {                                   // only available while URL is Missing
    fn url(self, u: &str) -> Conn<Present, P> { Conn { url: Some(u.into()), port: self.port, _m: PhantomData } }
}
impl<U> Conn<U, Missing> {                                   // only available while port is Missing
    fn port(self, p: u16) -> Conn<U, Present> { Conn { url: self.url, port: Some(p), _m: PhantomData } }
}
impl Conn<Present, Present> {                                // only available when BOTH are set
    fn connect(self) -> String { format!("{}:{}", self.url.unwrap(), self.port.unwrap()) }
}

let c = Conn::new().port(5432).url("db.local").connect();    // order of port/url doesn't matter
println!("{c}");                                              // db.local:5432
```

```text
 Conn<Missing,Missing> --url()--> Conn<Present,Missing> --port()--> Conn<Present,Present> --connect()--> String
          |                                                                  ^
          +--port()--> Conn<Missing,Present> --url()-------------------------+
 `connect()` exists ONLY on Conn<Present,Present>.  Forgetting a step is a COMPILE error, not a runtime error.
```

`Conn::new().url("x").connect()` does not compile: there is no method `connect` on `Conn<Present, Missing>`. The chain's **type after each dot** is carrying real information.

---

# 11. Text, slices, maps, and ordering chains

## 11.1 Parsing CSV-like text (verified)

```rust
#[derive(Debug)]
struct Person { name: String, age: u32, city: String }

fn parse_line(line: &str) -> Result<Person, String> {
    let mut parts = line.split(',').map(str::trim);                       // lazy iterator of trimmed &str
    let name = parts.next().filter(|s| !s.is_empty()).ok_or("missing name")?;
    let age  = parts.next().ok_or("missing age")?.parse::<u32>().map_err(|e| format!("bad age: {e}"))?;
    let city = parts.next().ok_or("missing city")?;
    Ok(Person { name: name.to_string(), age, city: city.to_string() })
}

let csv = "  Alice , 30 ,NYC\nBob,25,  LA \n\nCarol, x ,SF\nDave,41";
let (ok, bad): (Vec<_>, Vec<_>) = csv
    .lines()
    .filter(|l| !l.trim().is_empty())      // skip blank lines
    .map(parse_line)                       // each line -> Result<Person, String>
    .partition(|r| r.is_ok());             // split into two Vecs
let people: Vec<Person> = ok.into_iter().map(Result::unwrap).collect();
let errors: Vec<String> = bad.into_iter().filter_map(Result::err).collect();
println!("{people:?}\n{errors:?}");
```

Real output:

```text
[Person { name: "Alice", age: 30, city: "NYC" }, Person { name: "Bob", age: 25, city: "LA" }]
["bad age: invalid digit found in string", "missing city"]
```

Type flow of the main chain:

```text
csv                          : &str
.lines()                     : Lines<'_>              Item = &str
.filter(|l| ...)             : Filter<Lines, _>       Item = &str    (closure got &&str)
.map(parse_line)             : Map<Filter<..>, fn>    Item = Result<Person, String>
.partition(|r| r.is_ok())    : (Vec<Result<..>>, Vec<Result<..>>)    consumer
```

Inside `parse_line`, `parts.next()` is called **three times on the same iterator**, each call advancing it: this is why `parts` is `let mut` and why a *named* iterator is handy when you consume pieces in sequence.

## 11.2 String pipelines (verified)

```rust
// Title Case
let title: String = "hello wide world"
    .split(' ')
    .map(|w| {
        let mut cs = w.chars();
        match cs.next() {
            Some(f) => f.to_uppercase().collect::<String>() + cs.as_str(),   // first char uppercased + the rest
            None => String::new(),
        }
    })
    .collect::<Vec<_>>()
    .join(" ");
// "Hello Wide World"

// Clean a tag list
let tags = " rust , , go,  zig ,";
let clean: Vec<&str> = tags.split(',').map(str::trim).filter(|s| !s.is_empty()).collect();
// ["rust", "go", "zig"]

// Reverse a string
let rev: String = "hello".chars().rev().collect();   // "olleh"
```

`cs.as_str()` returns what is *left* in the `Chars` iterator after `next()` consumed the first char. This is a neat example of an iterator being an inspectable *state*.

## 11.3 Sorting does not chain (it returns `()`)

`sort`, `sort_by`, `dedup`, `retain`, `push`, `reverse` **mutate in place and return `()`**, so you can't put another dot after them:

```rust
let v = vec![3, 1, 2];
let sorted = v.sort().iter().map(|x| x * 2).count();
// error[E0599]: no method named `iter` found for unit type `()` in the current scope
```

Fix by sorting in a block expression, which is the standard idiom (verified):

```rust
let sorted = { let mut t = vec![9, 8, 7]; t.sort(); t };    // [7, 8, 9]
```

Sort by several keys (verified): `std::cmp::Reverse` flips one key's direction, and tuples compare lexicographically:

```rust
let mut people = vec![("bob", 25), ("ann", 30), ("cat", 25)];
people.sort_by_key(|&(n, a)| (std::cmp::Reverse(a), n));
// [("ann", 30), ("bob", 25), ("cat", 25)]      age descending, then name ascending
```

## 11.4 `Ordering` is chainable too

```rust
top.sort_by(|a, b| b.1.cmp(&a.1).then(a.0.cmp(b.0)));          // count desc, then word asc
1.cmp(&1).then_with(|| 2.cmp(&3))                              // Less
```

`a.cmp(b)` returns `Equal`/`Less`/`Greater`; `.then(next)` keeps the first result unless it was `Equal`, and `.then_with(|| ...)` does the same lazily.

## 11.5 The `HashMap` entry API

`entry(key)` returns an `Entry` (vacant or occupied), and you chain on it. This avoids the double lookup of "check, then insert".

```rust
// word frequency
let text = "the quick brown fox jumps over the lazy dog the end";
let mut freq: HashMap<&str, usize> = HashMap::new();
for w in text.split_whitespace() { *freq.entry(w).or_insert(0) += 1; }
let mut top: Vec<(&str, usize)> = freq.into_iter().collect();
top.sort_by(|a, b| b.1.cmp(&a.1).then(a.0.cmp(b.0)));
println!("{:?}", &top[..3]);       // [("the", 3), ("brown", 1), ("dog", 1)]

// group words by length: or_default() creates an empty Vec the first time
let mut groups: HashMap<usize, Vec<&str>> = HashMap::new();
for w in text.split_whitespace() { groups.entry(w.len()).or_default().push(w); }
let by_len: BTreeMap<_, _> = groups.into_iter().collect();   // BTreeMap = sorted, deterministic print
// {3: ["the","fox","the","dog","the","end"], 4: ["over","lazy"], 5: ["quick","brown","jumps"]}

// add, or insert if absent
let mut stock: HashMap<&str, i32> = HashMap::new();
stock.entry("apple").and_modify(|n| *n += 5).or_insert(5);   // absent -> inserts 5
stock.entry("apple").and_modify(|n| *n += 5).or_insert(5);   // present -> 5 + 5
// {"apple": 10}
```

```text
 map.entry(k)                      -> Entry
     .and_modify(|v| ..)           -> Entry    (runs ONLY if occupied)
     .or_insert(d)                 -> &mut V   (inserts d ONLY if vacant; returns the slot either way)
     .or_default()                 -> &mut V   (inserts Default::default())
 `*map.entry(k).or_insert(0) += 1`  : the returned &mut V is dereferenced and incremented in place
```

## 11.6 Group-by with `fold` (verified)

`fold` threads an accumulator through the chain; here the accumulator is a map:

```rust
let g: HashMap<bool, Vec<i32>> = (1..=6).fold(HashMap::new(), |mut m, x| {
    m.entry(x % 2 == 0).or_default().push(x);
    m
});
// g[&true] = [2, 4, 6]     g[&false] = [1, 3, 5]
```

Reading a `HashMap` as a chain (verified):

```rust
let m: HashMap<&str, i32> = [("a", 1), ("b", 2), ("c", 3)].into_iter().collect();
let total: i32 = m.values().sum();                                                  // 6
let mut keys: Vec<&&str> = m.keys().collect(); keys.sort();                          // ["a", "b", "c"]
let big: Vec<(&&str, &i32)> = { let mut t: Vec<_> = m.iter().filter(|(_, &v)| v >= 2).collect(); t.sort(); t }; // [("b",2),("c",3)]
```

---

# 12. Real-world programs

Each program below was compiled and run. Read the chain **with the 5-pass method** from [Chapter 18](#18-the-5-pass-method-for-reading-any-chain-and-a-cheat-sheet).

## 12.1 Expression tokenizer with `Peekable`

The classic use of **look-ahead**: you must *look* at the next char to decide what to do, without consuming it yet.

```rust
#[derive(Debug, PartialEq)]
enum Token { Num(f64), Plus, Minus, Star, Slash, LParen, RParen }

fn tokenize(src: &str) -> Result<Vec<Token>, String> {
    let mut out = Vec::new();
    let mut it = src.chars().peekable();
    while let Some(&c) = it.peek() {                       // LOOK at next char; don't consume yet
        match c {
            ' ' => { it.next(); }                          // consume and ignore
            '0'..='9' | '.' => {
                let mut s = String::new();
                while let Some(d) = it.next_if(|ch| ch.is_ascii_digit() || *ch == '.') { s.push(d); }
                out.push(Token::Num(s.parse().map_err(|e| format!("bad number {s:?}: {e}"))?));
            }
            '+' => { out.push(Token::Plus);   it.next(); }
            '-' => { out.push(Token::Minus);  it.next(); }
            '*' => { out.push(Token::Star);   it.next(); }
            '/' => { out.push(Token::Slash);  it.next(); }
            '(' => { out.push(Token::LParen); it.next(); }
            ')' => { out.push(Token::RParen); it.next(); }
            other => return Err(format!("unexpected {other:?}")),
        }
    }
    Ok(out)
}
```

Verified outputs:

```text
tokenize("3.5 * (2 + 10) / 4") -> Ok([Num(3.5), Star, LParen, Num(2.0), Plus, Num(10.0), RParen, Slash, Num(4.0)])
tokenize("2 $ 3")              -> Err("unexpected '$'")
tokenize("1.2.3")              -> Err("bad number \"1.2.3\": invalid float literal")
```

Dry run on `"3.5 *"`:

| Step | `peek()` | Action | `out` |
|---|---|---|---|
| 1 | `'3'` | digit branch: `next_if` consumes `'3'`, `'.'`, `'5'` | `[]` |
| 2 | (inside) `' '` | `next_if` predicate false -> **leaves the space unconsumed**, stops | |
| 3 | | parse `"3.5"` -> `Num(3.5)` pushed | `[Num(3.5)]` |
| 4 | `' '` | consume and ignore | |
| 5 | `'*'` | push `Star`, consume | `[Num(3.5), Star]` |
| 6 | `None` | loop ends | done |

`peek()` returns `Option<&char>` (a borrow of the buffered item), so the pattern is `Some(&c)` to copy the `char` out. `next_if` is `peek` + conditional `next` in one call.

## 12.2 Log analyzer

Input (7 lines, one is garbage):

```rust
const LOG: &str = "\
2024-05-01T10:00:01 INFO  auth    login ok user=alice latency=12ms
2024-05-01T10:00:02 ERROR db      timeout user=bob latency=3000ms
2024-05-01T10:00:03 INFO  auth    login ok user=carol latency=20ms
2024-05-01T10:00:04 WARN  db      slow query user=alice latency=900ms
garbage line
2024-05-01T10:00:05 ERROR auth    bad password user=bob latency=15ms
2024-05-01T10:00:06 INFO  db      query ok user=carol latency=40ms";
```

Parsing one line into an `Option<Entry>`. Note how many `?` early-exits there are:

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Level { Info, Warn, Error }
struct Entry<'a> { level: Level, service: &'a str, latency_ms: u32 }

fn parse_entry(line: &str) -> Option<Entry<'_>> {
    let mut f = line.split_whitespace();
    let _ts = f.next()?;                                    // timestamp (ignored); None if the line is empty
    let level = match f.next()? { "INFO" => Level::Info, "WARN" => Level::Warn, "ERROR" => Level::Error, _ => return None };
    let service = f.next()?;
    let latency_ms = line
        .split_whitespace()
        .find_map(|t| t.strip_prefix("latency=")?.strip_suffix("ms")?.parse::<u32>().ok())?;
    Some(Entry { level, service, latency_ms })
}
```

**Two different `?` operators live inside `find_map`'s line.** This is subtle and worth understanding:

```text
 .find_map( |t|  t.strip_prefix("latency=")?  .strip_suffix("ms")?  .parse::<u32>().ok()  )?
                                          ^                      ^                          ^
                           these two `?` return from the CLOSURE                    this `?` returns from
                           (closure returns Option<u32>)                            the FUNCTION parse_entry
```

For a token like `user=alice`, `strip_prefix("latency=")` is `None`, the inner `?` makes the **closure** return `None` for that token, and `find_map` moves to the next token. For `latency=12ms` the closure returns `Some(12)`, so `find_map` stops and the outer `?` unwraps it.

The analysis chain:

```rust
let entries: Vec<Entry> = LOG.lines().filter_map(parse_entry).collect();   // garbage line -> None -> dropped
println!("parsed {} of {}", entries.len(), LOG.lines().count());          // parsed 6 of 7

let mut stats: HashMap<&str, (u32, u32, u32)> = HashMap::new();           // service -> (count, errors, total_latency)
entries.iter().for_each(|e| {
    let s = stats.entry(e.service).or_default();
    s.0 += 1;
    s.1 += (e.level == Level::Error) as u32;
    s.2 += e.latency_ms;
});

let mut report: Vec<_> = stats
    .iter()
    .map(|(svc, &(n, errs, lat))| (*svc, n, errs, lat as f64 / n as f64))
    .collect();
report.sort_by(|a, b| b.2.cmp(&a.2).then_with(|| a.0.cmp(b.0)));          // most errors first, tie -> name
report.iter().for_each(|(svc, n, errs, avg)| println!("{svc:<5} n={n} errors={errs} avg={avg:.1}ms"));

let slowest = entries.iter().max_by_key(|e| e.latency_ms).map(|e| (e.service, e.latency_ms));
let worst_non_error = entries.iter().filter(|e| e.level != Level::Error).map(|e| e.latency_ms).max();
println!("{slowest:?}");
println!("{worst_non_error:?}");
```

Real output:

```text
parsed 6 of 7
auth  n=3 errors=1 avg=15.7ms
db    n=3 errors=1 avg=1313.3ms
Some(("db", 3000))
Some(900)
```

Check by hand: `auth` latencies are 12, 20, 15 so the average is 47/3 = 15.7; `db` latencies are 3000, 900, 40 so the average is 3940/3 = 1313.3. Both have exactly one `ERROR`, so the tie is broken by name.

## 12.3 Order analytics

```rust
#[derive(Debug)]
enum Status { Paid, Pending, Cancelled }
struct Item { sku: &'static str, qty: u32, unit_cents: u64 }
struct Order { id: u32, customer: &'static str, items: Vec<Item>, status: Status }

let orders = vec![
    Order { id: 1, customer: "ann", status: Status::Paid,      items: vec![Item { sku: "pen", qty: 10,  unit_cents: 150 }, Item { sku: "ink", qty: 2, unit_cents: 900 }] },
    Order { id: 2, customer: "bob", status: Status::Pending,   items: vec![Item { sku: "pad", qty: 5,   unit_cents: 400 }] },
    Order { id: 3, customer: "ann", status: Status::Paid,      items: vec![Item { sku: "pad", qty: 1,   unit_cents: 400 }] },
    Order { id: 4, customer: "cat", status: Status::Paid,      items: vec![Item { sku: "pen", qty: 100, unit_cents: 120 }] },
    Order { id: 5, customer: "bob", status: Status::Cancelled, items: vec![Item { sku: "ink", qty: 9,   unit_cents: 900 }] },
];

// 1) Revenue per customer, paid orders only
let mut revenue: HashMap<&str, u64> = HashMap::new();
orders
    .iter()
    .filter(|o| matches!(o.status, Status::Paid))
    .for_each(|o| {
        let total: u64 = o.items.iter().map(|i| i.qty as u64 * i.unit_cents).sum();   // nested chain
        *revenue.entry(o.customer).or_default() += total;
    });

// 2) Top 2 customers
let mut ranked: Vec<(&&str, &u64)> = revenue.iter().collect();
ranked.sort_by(|a, b| b.1.cmp(a.1).then_with(|| a.0.cmp(b.0)));
for (c, cents) in ranked.iter().take(2) { println!("{c}: ${}.{:02}", **cents / 100, **cents % 100); }
// cat: $120.00
// ann: $37.00

// 3) Distinct SKUs, sorted
let skus: Vec<&str> = {
    let mut s: Vec<&str> = orders.iter().flat_map(|o| o.items.iter().map(|i| i.sku)).collect();
    s.sort_unstable();
    s.dedup();
    s
};
// ["ink", "pad", "pen"]

// 4) Units sold in non-cancelled orders:  &o.items is &Vec<Item>, which IS IntoIterator (yields &Item)
let units: u32 = orders.iter().filter(|o| !matches!(o.status, Status::Cancelled)).flat_map(|o| &o.items).map(|i| i.qty).sum();
// 118

// 5) First order containing a bulk line (qty >= 100)
let first_big = orders.iter().find(|o| o.items.iter().any(|i| i.qty >= 100)).map(|o| o.id);
// Some(4)
```

Hand-check: `ann` = 10x150 + 2x900 + 1x400 = 1500 + 1800 + 400 = 3700 cents = $37.00; `cat` = 100x120 = 12000 cents = $120.00. Units = 12 + 5 + 1 + 100 = 118 (order 5 is cancelled).

Notice the **chain inside a chain** (step 1): the outer chain walks orders; the inner `o.items.iter().map(..).sum()` is a self-contained pipeline evaluated *per order*. Read the inner one first, as a single value.

## 12.4 Streaming a big file with O(1) memory

```rust
use std::fs::File;
use std::io::{BufRead, BufReader};

fn count_errors(path: &str) -> std::io::Result<usize> {
    let file = File::open(path)?;
    Ok(BufReader::new(file)
        .lines()                           // Iterator<Item = io::Result<String>>, ONE line at a time
        .map_while(Result::ok)             // stop at the first I/O error instead of panicking
        .filter(|l| l.contains("ERROR"))
        .count())
}
// verified on the 7-line LOG written to a temp file: 2.   And count_errors("/nope").is_err() == true.
```

**Why this scales:** because the chain is lazy and pulls one line at a time, memory use is **one line**, whether the file is 1 KB or 100 GB. The eager alternative `fs::read_to_string(p)?.lines()...` loads the *whole file* first. A verified small version of that:

```rust
fn line_count(path: &str) -> std::io::Result<usize> {
    Ok(fs::read_to_string(path)?.lines().filter(|l| !l.trim().is_empty()).count())
}
// file "a\n\nb\n  \nc\n"  ->  3
```

---

# 13. Performance and complexity

## 13.1 Cost model of one chain

For `v.iter().map(f).filter(g).collect::<Vec<_>>()` with **n** input items:

| Quantity | Cost | Why |
|---|---|---|
| Building the chain | O(1) time, **no heap allocation** | each adapter just wraps the previous struct (a few words on the stack) |
| Calls to `f` | exactly n | every source item goes through `map` |
| Calls to `g` | exactly n | every mapped item goes through `filter` |
| `push` into the result | at most n (k = survivors) | |
| Total time | **O(n)**, single pass | stages are interleaved per element, not run as separate passes |
| Auxiliary space | **O(1)** besides the output | no intermediate collections |
| Output space | O(k) | the final `Vec`; growth is amortized O(1) per push |

For the traced chain in [Section 3.6](#36-the-pull-model-who-calls-whom) (n = 3): `f` ran 3 times, `g` ran 3 times, 2 values were pushed, 1 extra `None` pull ended it.

**Compare with the "stage by stage" mental model** (what it is *not*): that would need two intermediate `Vec`s of size n and k, i.e. extra O(n) space and extra passes. The pull model avoids this entirely.

## 13.2 Cost of individual operations

| Operation | Time | Notes |
|---|---|---|
| `iter()`, `map`, `filter`, `take`, `enumerate`, `zip`, `chain`, `peekable`, ... (constructing) | O(1) | no work, no allocation |
| each `next()` through an adapter | O(1) amortized | `filter` may loop several times inside one `next()` |
| `collect::<Vec<_>>()` | O(n) | allocates (may grow a few times) |
| `count()` | O(n) in general | some iterators (e.g. slice iterators) shortcut to O(1) |
| `len()` | O(1) | only on `ExactSizeIterator` |
| `last()`, `nth(k)` | O(n) / O(k) in general | slice iterators and ranges can jump |
| `rev()` | O(1) to set up | needs `DoubleEndedIterator` |
| `skip(n)` | O(n) on first pull in general | |
| `s.len()` (bytes) | O(1) | |
| `s.chars().count()`, `s.chars().nth(k)` | O(n), O(k) | UTF-8 is variable width, no random access |
| `max`, `min`, `max_by_key`, `sum`, `fold` | O(n) | |
| `any`, `all`, `find`, `position` | O(n) worst, **short-circuit** | may stop after 1 item |
| `sort()` / `sort_unstable()` | O(n log n) | in place; stable sort may use a temporary buffer |
| `dedup()` | O(n) | removes **consecutive** duplicates, so sort first |
| `HashMap::entry(..).or_insert(..)` | O(1) expected | |
| `partition`, `unzip` | O(n) | allocate **two** collections |
| `windows(k)` yielding | O(1) per window | each window is just a slice view |
| `windows(k).map(\|w\| w.iter().sum())` | **O(n x k)** | summing each window again does k work per window |
| `cycle()` | O(1) per item | **clones** the iterator, so it needs `Clone` |
| `flat_map` / `flatten` | O(total inner items) | |

## 13.3 Costly mistakes and their fixes

```rust
// 1. Collecting just to count
let n1 = nums.iter().filter(|&&x| x > 2).collect::<Vec<_>>().len();   // allocates a Vec only to read its length
let n2 = nums.iter().filter(|&&x| x > 2).count();                      // no allocation   (both give 4, verified)

// 2. Collecting in the middle of a pipeline, then iterating again
let tmp: Vec<_> = a.iter().map(f).collect();       // allocation #1
let out: Vec<_> = tmp.iter().filter(g).collect();  // pass #2
// better: one chain, one collect:  a.iter().map(f).filter(g).collect()

// 3. Cloning when borrowing is enough
let names: Vec<String> = people.iter().map(|p| p.name.clone()).collect();   // allocates a String per person
let names: Vec<&str>   = people.iter().map(|p| p.name.as_str()).collect();  // no per-item allocation

// 4. Indexing characters in a loop (O(n^2))
for i in 0..s.chars().count() { let c = s.chars().nth(i); /* each nth is O(i) */ }
// better: for c in s.chars() { ... }   or   for (i, c) in s.char_indices() { ... }

// 5. Linear search inside a filter (O(n x m))
let common: Vec<_> = a.iter().filter(|x| b.contains(x)).collect();   // b is a Vec: O(m) per check
// better: let set: HashSet<_> = b.iter().collect();  a.iter().filter(|x| set.contains(x))   // O(n + m)

// 6. Expensive work before cheap rejection
v.iter().map(expensive).filter(cheap_check)     // expensive runs for every item
v.iter().filter(cheap_check).map(expensive)     // expensive runs only for survivors
```

## 13.4 Zero-cost, honestly

- **Typical behaviour:** in `--release` builds, chains over slices and ranges are commonly optimized to loops comparable to hand-written ones, because every adapter is a generic struct whose `next()` the compiler can inline.
- **Not guaranteed:** it depends on the optimizer, closure size, and the chain's shape. In **debug** builds the nested `next()` calls are real calls, and a chain can be markedly slower than a loop.
- **I have not benchmarked anything in this guide.** If performance matters, measure in `--release` (for example with `cargo bench` or the `criterion` crate) on your real data.
- **Memory:** a lazy chain's extra state is tiny and on the stack ([Section 3.5](#35-real-memory-layout-64-bit-measured)). The big costs are always *allocations you ask for* (`collect`, `clone`, `to_string`, `partition`).

---

# 14. Debugging chains and reading compiler errors

## 14.1 The toolbox

**Tool 1: ask the compiler for the type.** Assign the chain to the wrong type on purpose. The error names the real type:

```rust
let x: () = v.iter().map(|x| x + 1).filter(|x| x % 2 == 0);
```

```text
error[E0308]: mismatched types
  expected `()`, found `Filter<Map<..., ...>, ...>`
  = note: expected unit type `()`
                found struct `Filter<Map<std::slice::Iter<'_, {integer}>, {closure@...}>, {closure@...}>`
```

You can read the layers (`Filter` over `Map` over `slice::Iter`) straight off the message.

**Tool 2: print the type at runtime.**

```rust
fn type_of<T>(_: &T) -> &'static str { std::any::type_name::<T>() }
let chain = nums.iter().map(|x| x + 1).filter(|x| x % 2 == 0);
println!("{}", type_of(&chain));
// core::iter::adapters::filter::Filter<core::iter::adapters::map::Map<core::slice::iter::Iter<i32>, f::main::{{closure}}>, f::main::{{closure}}>
```

**Tool 3: `inspect`: watch the items flow through a stage** (verified):

```rust
let result: Vec<i32> = nums
    .iter()
    .inspect(|x| println!("iter   -> {x}"))
    .filter(|&&x| x % 2 == 0)
    .inspect(|x| println!("passed -> {x}"))
    .map(|&x| x * x)
    .collect();
```

```text
iter   -> 1
iter   -> 2
passed -> 2
iter   -> 3
iter   -> 4
passed -> 4
iter   -> 5
iter   -> 6
passed -> 6
[4, 16, 36]
```

Output interleaves **per element**, which proves the one-at-a-time pull model. `inspect` is the right tool for "which items reach this point?".

**Tool 4: break the chain into named, annotated steps.** Each `let` makes the intermediate type explicit (and nothing runs until the consumer):

```rust
let it1: std::slice::Iter<i32> = nums.iter();
let it2 = it1.filter(|&&x| x % 2 == 0);
let it3 = it2.map(|&x| x * x);
let result: Vec<i32> = it3.collect();      // only now does work happen
```

**Tool 5:** turbofish (`collect::<Vec<_>>()`, `parse::<i32>()`, `sum::<i32>()`) to pin a type mid-chain; rust-analyzer **inlay hints** in your editor to see the type after every dot; `dbg!(expr)` to print a value and its location (it returns the value, so it can sit inside a chain: `.map(|x| dbg!(x * 2))`).

## 14.2 Error catalogue (all triggered and captured with rustc 1.75)

| Real message (shortened) | Code | What it means | Fix |
|---|---|---|---|
| `borrow of moved value: v` after `v.into_iter()` | E0382 | `into_iter(self)` consumed the Vec | use `v.iter()`, or `v.clone().into_iter()` |
| `use of moved value: it` after `it.map(..)` | E0382 | adapters take `self` | `it.by_ref().map(..)`, or create a fresh iterator |
| `borrow of moved value: name` after `name.map(..)` on `Option<String>` | E0382 | `Option::map(self)` moved the `String` out | `name.as_ref().map(..)` |
| `type annotations needed` / `cannot satisfy _: FromIterator<i32>` | E0283 | `collect` is generic over the result | `let x: Vec<_> = ..` or `collect::<Vec<_>>()` |
| `cannot satisfy _: Sum<i32>` | E0283 | same, for `sum` | `let t: i32 = ..sum()` or `sum::<i32>()` |
| `expected &&_, found integer` | E0308 | `filter` gives `&Item`; with `iter()` that is `&&i32` | `\|&&x\| x > 1`, `\|x\| **x > 1`, or `.copied()` first |
| `Vec<String> cannot be built from an iterator over &String` | E0277 | `iter()` yields references | `.cloned()` (verified) or `.map(String::clone)` |
| `temporary value dropped while borrowed` | E0716 | binding the middle of a `&mut` builder chain | bind the builder first, or end the chain with an owned value |
| `cannot borrow v as mutable because it is also borrowed as immutable` | E0502 | closure mutates the collection being iterated | collect first, or use indices |
| `no method named iter found for unit type ()` | E0599 | `sort()` etc. return `()` | block expression `{ v.sort(); v }` |
| `? ... only be used on Options, not Results, in a function that returns Option` | E0277 | `?` can't cross families | `.ok()?` (verified) or `.ok_or(..)?` |
| `hidden type for impl Iterator captures lifetime...` | E0700 | returned chain borrows an argument | add `+ '_` (edition 2021) |
| `if and else have incompatible types` (`Iter` vs `Rev<Iter>`) | E0308 | two branches, two chain types | `Box<dyn Iterator<..>>` |
| `Chars<'_>: ExactSizeIterator is not satisfied` | E0277 | `enumerate().rev()` on `chars()` | `char_indices().rev()` (verified: `[(3,'y'),(1,'é'),(0,'h')]`, byte indices) |
| `no method named connect found for Conn<Present, Missing>` | E0599 | **intended**: typestate stops you | set the missing field first |
| warning: `unused Map that must be used` / `iterators are lazy` | warning | chain has no consumer | add `.count()` / `.collect()` / use `for_each` / a `for` loop |

## 14.3 A debugging procedure that always works

```text
 1. Read the FIRST error only (later ones are often consequences).
 2. Find the line and the column of the caret: which DOT is it pointing at?
 3. Write the type that flows INTO that dot and the type that flows OUT.
 4. Ask: does this method take self / &self / &mut self?   (moved? borrowed?)
 5. Ask: does the closure get Item or &Item?   (the &&x question)
 6. If still stuck: split the chain with `let` and explicit types, or use the `let x: () = ...` trick.
```

---

# 15. Async, streams, and parallel chains (not compiled)

> **Not compiled here.** These need external crates (`tokio`, `reqwest`, `futures`, `rayon`) that were not available in the verification environment. They are included so you can recognize the shapes; the mental model is the same as above.

**Async chains.** Futures are *lazy* like iterators: nothing runs until `.await` (or a runtime polls it). Each `.await` is another suspension point, and `?` still short-circuits:

```rust
// requires: reqwest (json feature), serde, tokio. NOT compiled.
let user: User = client
    .get(url)               // RequestBuilder: a builder chain (owned style)
    .header("Accept", "application/json")
    .send().await?          // -> Response     (the request actually happens here)
    .error_for_status()?    // -> Response     (turn 4xx/5xx into Err)
    .json().await?;         // -> User         (parse the body)
```

```text
 builder methods (sync, cheap) --> .send() returns a Future --> .await runs it --> `?` unwraps/propagates Err
```

**Streams** (`futures::StreamExt`) are the async cousin of `Iterator`, with similar adapters:

```rust
// requires: futures, tokio. NOT compiled.
let bodies: Vec<String> = futures::stream::iter(urls)
    .map(|u| fetch(u))             // each item becomes a Future
    .buffer_unordered(8)           // run up to 8 at once, yield results as they finish
    .collect().await;
```

**Data parallelism** with `rayon` keeps the chain shape and swaps the entry point:

```rust
// requires: rayon. NOT compiled.
let total: u64 = data.par_iter().map(|x| expensive(*x)).sum();   // iter() -> par_iter()
```

---

# 16. Go comparison

> The Go snippets below are **illustrative and not compiled here** (no Go toolchain was used for verification). They use generics (Go 1.18+) and, for the last one, the `iter` package (Go 1.23+).

## 16.1 The same pipeline in Go

Go's standard library has no `map`/`filter` chain for slices, so the idiomatic version is a loop; a generic-helper version looks like this:

```go
func Filter[T any](xs []T, keep func(T) bool) []T {
	out := make([]T, 0, len(xs))
	for _, x := range xs {
		if keep(x) {
			out = append(out, x)
		}
	}
	return out
}

func Map[T, U any](xs []T, f func(T) U) []U {
	out := make([]U, 0, len(xs))
	for _, x := range xs {
		out = append(out, f(x))
	}
	return out
}

nums := []int{1, 2, 3, 4, 5, 6}
result := Map(
	Filter(nums, func(x int) bool { return x%2 == 0 }),
	func(x int) int { return x * x },
) // [4 16 36]
```

The idiomatic loop (what most Go code actually does):

```go
result := make([]int, 0, len(nums))
for _, x := range nums {
	if x%2 != 0 { continue }          // filter
	result = append(result, x*x)       // map + collect
}
```

## 16.2 A lazy, pull-vs-push contrast (Go 1.23+)

Go 1.23 added range-over-func and `iter.Seq`. It is **push-based**: the *producer* calls `yield` for each item. Rust is **pull-based**: the *consumer* calls `next()`.

```go
func FilterSeq[T any](seq iter.Seq[T], keep func(T) bool) iter.Seq[T] {
	return func(yield func(T) bool) {
		for x := range seq {
			if keep(x) && !yield(x) { // stop early if the consumer said "no more"
				return
			}
		}
	}
}
```

```text
 Rust (pull):  collect --next()--> Filter --next()--> Map --next()--> source      consumer drives
 Go   (push):  source --yield(x)--> filter func --yield(x)--> map func --> loop body   producer drives
```

## 16.3 Side-by-side

| Aspect | Rust | Go |
|---|---|---|
| Chain syntax | `a.iter().filter(..).map(..).collect()` (method chain) | nested calls `Map(Filter(a, ..), ..)` or loops (methods can't have their own type parameters) |
| Laziness | adapters are lazy structs; one pass | helper functions above are **eager**: one new slice per stage |
| Intermediate allocation | none until `collect` | one slice per stage (garbage-collected later) |
| Who drives iteration | consumer pulls (`next`) | producer pushes (`yield`) in `iter.Seq` |
| Item ownership | `iter()` / `iter_mut()` / `into_iter()` choose borrow / mut borrow / move | slices share a backing array; values are copied or you take pointers; GC frees |
| Closure capture rules | `Fn` / `FnMut` / `FnOnce`, checked by the borrow checker | closures capture variables by reference and may mutate them freely |
| Absence / failure | `Option<T>`, `Result<T,E>` with `?` and combinators | multiple returns `(T, error)`, `nil`, explicit `if err != nil` |
| Mutating while iterating | compile error (E0502) | allowed; behavior is your responsibility |
| Cost model | adapters usually optimize to a loop in release builds | loops are the baseline; helper calls may or may not inline |

---

# 17. Chain or loop? Style rules

**Prefer a chain when** the code is a *pipeline of transformations* on one data stream: filter, map, group, aggregate, search. The chain states *what*, the loop states *how*.

**Prefer a plain `for` loop when**:

- you need **several mutable accumulators** at once;
- there are **multiple early exits** with different return values;
- the body has **side effects** (I/O, logging): use `for`, not `map`/`for_each`;
- the closure body would exceed ~5 lines: extract a named function, then `.map(parse_line)`.

**Rules of thumb:**

1. One method per line, rustfmt-style, so you can comment, `inspect`, or delete a stage.
2. Put cheap, selective stages first ([6.4](#64-performance-rule-of-thumb-for-ordering)).
3. Pass function paths when you can (`.map(str::trim)`), closures when you must.
4. Don't `unwrap()` in the middle: use `?`, `filter_map`, `ok_or`, or `collect::<Result<_,_>>()`.
5. Don't `collect` and then immediately iterate again; keep it lazy.
6. When a closure's `&` gymnastics get unreadable, add `.copied()` or `.cloned()` so items become plain values.
7. Let intermediate **names** document meaning: `let active = users.iter().filter(..);` then use `active` twice (by cloning the iterator if needed).
8. Annotate with a `let x: Type =` at the *consumer* so readers (and the compiler) see the result type.

**Clippy** (`cargo clippy`) knows many of these patterns. Lints such as `needless_collect`, `manual_map`, `manual_filter_map`, `map_flatten`, `redundant_closure`, `needless_range_loop` and `manual_flatten` suggest chain-friendly rewrites.

---

# 18. The 5-pass method for reading any chain, and a cheat sheet

## 18.1 The five passes

```text
 PASS 1  SOURCE      What is the first receiver, and is it owned, &, or &mut?  (iter / into_iter / Option / builder)
 PASS 2  TYPES       Write the type that comes OUT of every dot.
 PASS 3  LABEL       Mark each call: adapter (lazy) | consumer (eager) | combinator (immediate) | mutator (returns ()).
 PASS 4  DRIVER      Find what triggers the work: the consumer, `.await`, `?`, or the builder's final call.
 PASS 5  SIMULATE    Push ONE element through all stages. Repeat for a filtered-out element and for the end (None).
```

## 18.2 Worked example (verified)

```rust
let text = "  alpha \n\n beta\n gamma  ";
let top: Vec<String> = text
    .lines()
    .map(str::trim)
    .filter(|l| !l.is_empty())
    .map(str::to_uppercase)
    .take(2)
    .collect();
println!("{top:?}");       // ["ALPHA", "BETA"]
```

**Pass 1:** source is `text: &str`, a borrowed string slice.

**Passes 2 and 3** together:

| Dot | Output type | Label | Closure receives |
|---|---|---|---|
| `.lines()` | `Lines<'_>`, Item `&str` | source (lazy) | |
| `.map(str::trim)` | `Map<Lines, fn>`, Item `&str` | adapter | `&str` |
| `.filter(\|l\| !l.is_empty())` | `Filter<..>`, Item `&str` | adapter | **`&&str`** (auto-deref makes `.is_empty()` work) |
| `.map(str::to_uppercase)` | `Map<..>`, Item `String` | adapter (allocates a `String` per item) | `&str` |
| `.take(2)` | `Take<..>`, Item `String` | adapter (holds a counter) | |
| `.collect()` | `Vec<String>` | **consumer** | |

**Pass 4:** driver = `collect()`.

**Pass 5**, simulating:

| Pull | `lines()` | `trim` | `filter` non-empty | `to_uppercase` | `take(2)` | `Vec` |
|---|---|---|---|---|---|---|
| 1 | `"  alpha "` | `"alpha"` | keep | `"ALPHA"` | 1st of 2 | `["ALPHA"]` |
| 2 | `""` | `""` | **drop**, ask again | (not called) | | |
| 2 (cont.) | `" beta"` | `"beta"` | keep | `"BETA"` | 2nd of 2 | `["ALPHA","BETA"]` |
| 3 | **not requested**: `take(2)` is satisfied, returns `None` without asking `" gamma  "` | | | | | done |

The last row is the payoff: `" gamma  "` is **never even read** because `take` short-circuits the pull.

## 18.3 Cheat sheet

| I want to... | Chain |
|---|---|
| transform every item | `.map(f)` |
| keep some items | `.filter(p)` |
| transform and drop failures | `.filter_map(f)` where `f` returns `Option` |
| flatten nested collections | `.flatten()` / `.flat_map(f)` |
| number the items | `.enumerate()` |
| walk two things together | `.zip(other)` |
| first N / skip N | `.take(n)` / `.skip(n)` |
| stop at a condition | `.take_while(p)` |
| compare neighbours | `.windows(2)` |
| group into fixed-size pieces | `.chunks(k)` |
| look ahead one item | `.peekable()` then `.peek()` / `.next_if(..)` |
| running total / state | `.scan(init, f)` or `.fold(init, f)` |
| to a Vec / String / Map / Set | `.collect::<Vec<_>>()` etc. |
| all-or-nothing on `Result` | `.collect::<Result<Vec<_>,_>>()` |
| keep both successes and failures | `.partition(\|r\| r.is_ok())` |
| number of matches | `.filter(p).count()` |
| is there any / are all | `.any(p)` / `.all(p)` |
| first match | `.find(p)` / `.position(p)` / `.find_map(f)` |
| biggest / smallest by a key | `.max_by_key(k)` / `.min_by_key(k)` |
| sum / product | `.sum::<T>()` / `.product::<T>()` |
| default for a missing value | `.unwrap_or(d)` / `.unwrap_or_else(\|\| ..)` / `.unwrap_or_default()` |
| `Option` -> `Result` | `.ok_or(e)` / `.ok_or_else(\|\| e)` |
| count / group in a map | `*m.entry(k).or_insert(0) += 1` / `m.entry(k).or_default().push(x)` |
| build a request/command | `Builder::new().a().b().build()` |

## 18.4 Glossary

| Term | Meaning |
|---|---|
| **Receiver** | The value a method is called on (left of the dot). |
| **Adapter** | A lazy iterator method that returns a new iterator wrapping the old one (`map`, `filter`, `take`...). |
| **Consumer** | A method that pulls items and ends the chain (`collect`, `sum`, `count`, `find`...). |
| **Combinator** | A method on `Option`/`Result` that transforms or sequences values (`map`, `and_then`, `ok_or`...). |
| **Lazy** | Does no work until something requests a value. |
| **Pull model** | The consumer asks (`next()`); the sources answer. |
| **Short-circuit** | Stopping early without visiting the rest (`find`, `any`, `take`, `?`). |
| **Turbofish** | The `::<Type>` syntax used to specify a generic argument on a method call. |
| **Monomorphization** | The compiler generating specialized code for each concrete generic type (here, your exact chain). |
| **Niche optimization** | Using impossible bit patterns (like a null pointer) to store `None` without extra space. |
| **Extension trait** | A trait implemented for all types that satisfy a bound, adding methods to them (how `.my_map` works). |
| **Typestate** | Encoding an object's state in its type so illegal sequences don't compile. |

---

# 19. Active recall and practice

Answers are deliberately **not** included. Try each on paper first, then compile and check. Ask for answers or a code review for any attempt.

## 19.1 Active recall (predict, trace, explain)

1. **Trace.** In what exact order are the prints produced? What does the whole expression evaluate to?
   ```rust
   let n = (1..=3)
       .map(|x| { print!("m{x} "); x })
       .filter(|x| { print!("f{x} "); x % 2 == 1 })
       .count();
   ```
2. **Types.** For `let v: Vec<String> = ...;`, what is the closure parameter type in each of `v.iter().filter(|a| ..)`, `v.iter().map(|a| ..)`, and `v.into_iter().filter(|a| ..)`?
3. **Ownership.** Why does `let c = Builder::new().arg("x");` fail for a `&mut self -> &mut Self` builder but succeed for a `self -> Self` builder?
4. **Complexity.** What is the extra space cost of `.filter(p).collect::<Vec<_>>().len()` compared with `.filter(p).count()`? Which would you choose and why?
5. **Short-circuit.** In `["1","x","3"].iter().map(|s| s.parse::<i32>()).collect::<Result<Vec<_>,_>>()`, how many times is `parse` called? Why?
6. **Compile error.** Why does `"abc".chars().enumerate().rev()` not compile, and what is the smallest change that makes a reversed, indexed walk work? What do the indices mean after the change?
7. **`map` vs `and_then`.** What is the type of `Some(5).map(|x| Some(x + 1))`? Which method gives `Option<i32>` instead?
8. **Laziness.** What does this print, and what does `_it` hold when it is dropped?
   ```rust
   let _it = vec![1, 2, 3].into_iter().map(|x| { println!("saw {x}"); x });
   ```
9. **Order.** Predict `(1..=10).step_by(4).skip(1)` and `(1..=10).skip(1).step_by(4)` before running them.
10. **Memory model.** `Map<slice::Iter<i32>, F>` is 16 bytes when `F` captures nothing. Explain why, and why a `move` closure capturing an `i64` would change the size.

## 19.2 Independent practice

**Beginner.** Given `words: Vec<&str>`, produce the lengths of all words longer than 3 characters, in order. Then write the same logic as a `for` loop. Predict the output for `["rust", "go", "zig", "swift"]` before running.

**Intermediate.** Given `"a=1;b=2;c=x;d=4"`, build a `HashMap<String, i32>` containing only the valid pairs, using **one chain**. Hint: think `split`, `split_once`, `filter_map`, `parse().ok()`, `collect`.

**Variation (change one constraint).** Same input, but now return `Result<HashMap<String, i32>, String>` that fails with a message naming the **first** bad pair. Which `collect` target and which `map_err` placement do you need? How many pairs are examined when the third is bad?

**Stretch.**

1. Write your own `my_take_while` adapter (a struct + an extension-trait method), following the `MyMap`/`MyFilter` pattern in [Section 3.3](#33-adapters-are-just-structs-that-wrap-an-iterator), and test it on an infinite range.
2. Write a `Windowed<I>` iterator that yields `[T; 3]` windows from any iterator of `Copy` items. Decide what state it needs to store.
3. Add a typestate builder for `Request` where `.build()` only exists after `url()` **and** `method()` were called.
4. Take any loop-based function you wrote recently, rewrite it as a chain, and decide (using Chapter 17) which version you would ship.

## 19.3 Key takeaways

1. A chain is **function composition written left to right**; `a.f().g()` is `g(f(a))` ([1.4](#14-method-syntax-is-sugar-for-a-plain-function-call)).
2. After every dot, ask **"what type comes out?"** and **"does this method take `self`, `&self`, or `&mut self`?"**
3. Iterator adapters **build a nested struct** and run **no code**; the consumer **pulls one element at a time** through every stage ([3.4](#34-the-type-of-a-chain-is-a-nested-struct-onion), [3.6](#36-the-pull-model-who-calls-whom)).
4. Closures get `Item` when they consume and `&Item` when they only look; that is the entire explanation of `|&&x|` ([4.3](#43-what-each-adapter-hands-to-your-closure-and-the--patterns)).
5. **Order matters** for both results and cost ([Chapter 6](#6-order-matters-the-same-adapters-different-results)).
6. `Option`/`Result` chains are a **two-track railway**: `map` for plain values, `and_then` when the closure itself returns `Option`/`Result`, `?` as the exit ramp ([Chapter 9](#9-option-and-result-chains)).
7. Builders come in two shapes (`self -> Self` and `&mut self -> &mut Self`) and the difference is *only* ownership; the `&mut` form has the temporary-lifetime trap ([Chapter 10](#10-the-builder-pattern)).
8. Laziness gives **O(1) auxiliary space and single-pass O(n) time**; the costs you pay are the allocations you explicitly request ([Chapter 13](#13-performance-and-complexity)).
9. When stuck: split the chain with `let`, use the `let x: () =` trick, or `inspect` ([Chapter 14](#14-debugging-chains-and-reading-compiler-errors)).

## 19.4 Portable progress tracker (paste into a new conversation)

```text
RUST METHOD CHAINING: PROGRESS
Mastery scale: 0 Unfamiliar | 1 Recognition | 2 Guided | 3 Independent | 4 Transfer

Topic                                   Level   Notes / recurring mistakes
--------------------------------------  -----   ---------------------------------------
Lazy vs eager, pull model                 _
Per-element flow vs stage-by-stage        _
Receiver kinds (self / &self / &mut)      _
Item vs &Item vs &&Item in closures       _
Adapter order and its effects             _
collect / turbofish / Result collect      _
Option/Result railway, map vs and_then    _
Builder styles + E0716                    _
Entry API, Ordering::then                 _
Custom iterator / impl Iterator           _
Reading compiler errors                   _

Problems attempted: _     solved independently: _
Next exercise: _
```
