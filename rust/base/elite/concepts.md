# Rust Comprehensive Guide — Master Topic List

---

## Category 1 — Ownership & Memory (11 topics)

1. Ownership model — values have exactly one owner
2. Move semantics — assignment moves, not copies
3. Borrow checker — compile-time aliasing rules
4. Shared vs mutable borrows — many `&T` or one `&mut T`
5. Lifetimes — named regions of borrow validity
6. Non-lexical lifetimes — borrows end at last use
7. Copy vs Move types — why `i32` copies but `String` moves
8. Drop trait & drop order — RAII, destructor mechanics
9. Two-phase borrows — re-borrow inside method call
10. Self-referential structs — why they require `Pin`
11. Stack vs heap allocation — `Box<T>` and when to heap-allocate

---

## Category 2 — Type System (21 topics)

12. Trait system basics — interfaces as capability grants
13. Operators are traits — `+`, `-`, `==`, `<` all desugar to trait calls
14. Associated types — `type Output` vs generic parameter
15. `impl Trait` vs `dyn Trait` — static vs dynamic dispatch
16. Object safety rules — why some traits can't be `dyn`
17. Orphan rule / coherence — can't impl foreign trait on foreign type
18. Newtype pattern — wrapping for type safety
19. Zero-sized types (ZST) — types that occupy no memory
20. `PhantomData` — marking ownership without storing data
21. Never type (`!`) — the type of diverging expressions
22. `Sized` and `?Sized` — compile-time size knowability
23. Variance — covariance, contravariance, invariance
24. Higher-ranked trait bounds — `for<'a> Fn(&'a T)`
25. Blanket implementations — `impl<T: X> Y for T`
26. `From` / `Into` / `TryFrom` — the conversion trait hierarchy
27. Deref coercions — auto-deref chains in method calls
28. Supertrait constraints — `trait A: B` requiring another trait
29. Const generics — array length as a generic parameter
30. Generic associated types (GATs) — associated types with their own generics
31. `Default` trait — `Default::default()` pattern
32. `PartialEq` vs `Eq` — why NaN breaks reflexivity
33. `PartialOrd` vs `Ord` — total vs partial ordering

---

## Category 3 — Closures & Fn Traits (6 topics)

34. `Fn` / `FnMut` / `FnOnce` — closure capability hierarchy
35. Closure capture modes — by-reference or by-value capture
36. `move` closures — forcing ownership capture
37. Function pointers vs closures — `fn()` is not the same as `Fn()`
38. Returning closures — why you need `Box<dyn Fn>`
39. `impl Fn` in signatures — return position `impl Trait`

---

## Category 4 — Error Handling (7 topics)

40. `Result<T, E>` model — no exceptions, explicit errors
41. `Option<T>` — no null; absence is encoded in the type
42. `?` operator desugaring — early return + `From` conversion
43. `panic!` vs `Result` — when each is the right choice
44. Custom error types — `impl std::error::Error`
45. Error trait hierarchy — `Display` + `Debug` + `source()`
46. `anyhow` vs `thiserror` — application vs library error style

---

## Category 5 — Generics (7 topics)

47. Monomorphization — generics generate specialized code per type
48. Trait bounds and `where` clauses — constraining generic type parameters
49. Turbofish syntax `::<>` — explicit type parameters at call site
50. Generic lifetime parameters — `<'a>` in struct and function signatures
51. Lifetime elision rules — when annotations can be omitted
52. Lifetimes in structs — `struct Foo<'a> { x: &'a str }`
53. `'static` lifetime — lives for the entire program duration

---

## Category 6 — Smart Pointers (9 topics)

54. `Box<T>` — owned heap allocation
55. `Rc<T>` — shared ownership, single thread
56. `Arc<T>` — shared ownership, multi-thread
57. `Cell<T>` — interior mutability for `Copy` types
58. `RefCell<T>` — runtime borrow checking
59. `Mutex<T>` and `RwLock<T>` — thread-safe interior mutability
60. `Weak<T>` — breaking reference cycles
61. `Pin<T>` and `Unpin` — preventing moves in memory
62. Interior mutability pattern — shared reference + mutation via `Cell`

---

## Category 7 — Concurrency (5 topics)

63. `Send` and `Sync` auto-traits — type-level thread safety proofs
64. Data race prevention — guaranteed by the type system
65. `Arc<Mutex<T>>` pattern — shared mutable state across threads
66. Channel types (`mpsc`) — message-passing concurrency
67. Rayon data parallelism — `par_iter()` for parallel work

---

## Category 8 — Async / Await (7 topics)

68. `Future` trait — lazy async computation unit
69. `async fn` desugaring — returns `impl Future`, not a value
70. `await` and polling — how executors drive futures
71. Async runtimes (Tokio) — executor + reactor model
72. `Pin` in async context — why async state machines need `Pin`
73. `Send` bounds in async — futures must be `Send` for `spawn()`
74. `select!` and `join!` — concurrent future combinators

---

## Category 9 — Strings & Collections (7 topics)

75. `str` vs `String` vs `&str` — three string types with distinct roles
76. `OsStr` / `OsString` — OS-native string types for paths
77. `Path` and `PathBuf` — cross-platform path manipulation
78. `Vec<T>` vs `[T; N]` vs `[T]` — owned, fixed-size, and slice forms
79. Fat pointers (wide pointers) — `&[T]` and `&dyn T` carry metadata
80. `HashMap` vs `BTreeMap` — hash vs ordered key semantics
81. Byte strings `b"hello"` — raw byte literals and `u8` slices

---

## Category 10 — Iterators (7 topics)

82. `Iterator` trait — lazy evaluation; nothing runs until consumed
83. `IntoIterator` trait — `for` loop desugaring
84. `iter()` vs `into_iter()` vs `drain()` — borrow, own, or drain a collection
85. Iterator adapters — `map`, `filter`, `flat_map`, `take`, `chain`, ...
86. `collect()` type inference — turbofish or annotation required
87. Chaining and iterator fusion — compiler fuses adapters into one pass
88. Custom `Iterator` implementation — implementing `Iterator` for your own type

---

## Category 11 — Pattern Matching (8 topics)

89. Exhaustive matching — all arms must be covered
90. `if let` / `while let` — single-arm match desugaring
91. `ref` patterns — bind by reference inside `match`
92. Match ergonomics — auto-ref in pattern position
93. Guard clauses — `if condition` inside a match arm
94. Destructuring — structs, tuples, enums in patterns
95. `@` bindings — bind and test in one pattern
96. Slice patterns — `[first, .., last]` matching

---

## Category 12 — Macros (5 topics)

97. `macro_rules!` (declarative) — pattern-matched token tree rewriting
98. Procedural macros — derive, attribute, and function-like macros
99. `#[derive]` mechanics — what code `derive` actually generates
100. Format string mechanics — `println!("{:?}")` and the format traits
101. Hygiene in macros — variable capture rules inside macros

---

## Category 13 — Memory Layout & Unsafe (9 topics)

102. `#[repr(C)]` layout — FFI-compatible struct layout
103. `#[repr(transparent)]` — newtype with same layout as inner type
104. `unsafe` blocks — the four unsafe superpowers
105. Raw pointers `*const` / `*mut` — bypass the borrow checker entirely
106. `unsafe` traits — implementer must uphold invariants manually
107. FFI (C interop) — `extern "C"` functions and types
108. `transmute` — type reinterpretation; extremely dangerous
109. Undefined behavior in Rust — what `unsafe` can trigger
110. `MaybeUninit<T>` — safely working with uninitialized memory

---

## Category 14 — Syntax & Expressions (10 topics)

111. Everything is an expression — blocks, `if`, `match` all return values
112. Semicolon vs no-semicolon — last expression without `;` is the return value
113. Shadowing — `let x = x + 1` creates a new binding, not mutation
114. `const` vs `static` vs `let` — compile-time vs runtime bindings
115. `loop` with break value — `break expr` returns a value from a loop
116. Method resolution order — deref chain during `.` dispatch
117. `as` casting rules — truncating, not converting like `From`
118. Type aliases vs newtypes — `type Km = f64` vs `struct Km(f64)`
119. Struct update syntax `..` — `{ field, ..other }` pattern
120. Range types — `0..5` vs `0..=5` vs `..` are distinct types

---

## Category 15 — Modules & Visibility (6 topics)

121. Module tree and file system — `mod` maps to files and folders
122. `pub` / `pub(crate)` / `pub(super)` — granular visibility levels
123. `use` paths and re-exports — `pub use` for API surface control
124. The prelude — what is auto-imported into every scope
125. Cargo features — conditional compilation flags
126. `cfg!` and `#[cfg(...)]` — conditional code inclusion

---

## Study Roadmap Summary

```
PHASE 1 — Foundation (topics 1–33, 40–42, 47–53, 75–88, 111–120)
  Ownership, basic traits, generics, iterators, syntax

PHASE 2 — Intermediate (topics 34–39, 43–46, 54–67, 89–101, 121–126)
  Closures, error handling, smart pointers, concurrency, macros

PHASE 3 — Advanced (topics 68–74, 102–110)
  Async/await, unsafe, memory layout, FFI

The three walls every Rust learner must break through:
  Wall 1 → Topic 5 (Lifetimes)
  Wall 2 → Topics 34–36 (Fn/FnMut/FnOnce)
  Wall 3 → Topics 61, 71–73 (Pin + async)
```

Tell me which topic number you want to begin with and we go deep.

This is a great initiative — building a comprehensive map before diving deep is a master-level learning strategy (this is the "chunking" principle from cognitive science: knowing the landscape prevents you from getting lost in any individual forest). Here is the complete map of every Rust concept that trips people coming from other languages:Every card is clickable — it will send a deep-dive request directly into our conversation.

---

Here is the complete picture of the guide you are building. There are **15 major categories** spanning roughly **120+ distinct concepts**. A few notes to guide your study plan:

**The critical path** (concepts that unlock everything else) runs in this order:

```
Ownership → Move/Copy → Borrowing → Lifetimes
    ↓
Trait system → Generics → Closures (Fn/FnMut/FnOnce)
    ↓
Smart pointers → Interior mutability → Send/Sync
    ↓
Iterators → Error handling → Async/Await
```

**Why this is not like other languages — the meta-insight:** In Python, C++, Go, and Java, most of these concepts either don't exist, are handled at runtime, or are handled by the garbage collector. Rust moves all of this decision-making to *compile time*, which is why the concepts feel unfamiliar — you are doing work that other languages quietly do for you at a cost you never see.

**Recommended study order for your level:**

Starting from zero → work through the categories exactly as listed in the map. The dot colors (green = fundamental, yellow = intermediate, red = advanced) tell you not to touch the red dots until the yellow ones feel instinctive.

**The three "wall" topics** where most Rust learners stall — and where we will spend the most time:

```
Wall 1: Lifetimes           ← feels like syntax noise until it clicks
Wall 2: Fn/FnMut/FnOnce    ← confusing because closures have invisible types
Wall 3: Pin + async         ← requires ownership + lifetimes + traits all at once
```

Filter by any category in the widget and click any card to begin a deep-dive session on that exact topic. Which category do you want to start with?