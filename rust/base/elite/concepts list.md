# Rust & CS Deep Curriculum Map

> 120+ hidden topics across 14 categories — from foundational to expert.
> Each topic is a full study unit. Work through dependency chains, not randomly.

---

## How to Use This Map

| Difficulty | Meaning |
|---|---|
| `foundational` | Prerequisites most tutorials cover superficially |
| `intermediate` | Topics experienced Rust devs encounter but rarely master |
| `advanced` | Topics that separate good engineers from great ones |
| `expert` | Requires many prerequisite chunks; deep systems/theory knowledge |

**The 7 invisible layers (bottom = foundation):**
```
Layer 7: Patterns & Idioms          (what you write)
Layer 6: Traits & Generics          (how APIs compose)
Layer 5: Ownership & Borrowing      (what the compiler enforces)
Layer 4: Type System                (what the compiler knows)
Layer 3: Memory Layout              (what actually exists in RAM)
Layer 2: Hardware Model             (what CPUs actually do)
Layer 1: Formal Theory              (why the rules are the way they are)
```

---

## Recommended Dependency Chains

**Chain 1 — Ownership to Variance:**
`Move semantics` → `NLL borrow checker` → `Lifetime elision` → `Lifetime subtyping` → `Variance` → `HRTB`

**Chain 2 — Traits to Dispatch:**
`Traits as contracts` → `Blanket impls` → `Orphan rule` → `Trait object safety` → `impl Trait vs dyn Trait` → `Fat pointers` → `Monomorphization`

**Chain 3 — Safe to Lock-Free:**
`UnsafeCell` → `Interior mutability` → `Atomic types` → `Memory ordering` → `Compare-and-swap` → `Lock-free structures` → `Epoch-based reclamation`

---

## Category Index

1. [Rust: Type System](#1-rust-type-system)
2. [Rust: Memory & Ownership](#2-rust-memory--ownership)
3. [Rust: Interior Mutability](#3-rust-interior-mutability)
4. [Rust: Traits & Generics Deep](#4-rust-traits--generics-deep)
5. [Rust: Closures Internals](#5-rust-closures-internals)
6. [Rust: Async & Concurrency](#6-rust-async--concurrency)
7. [Rust: Unsafe & Internals](#7-rust-unsafe--internals)
8. [Rust: Patterns & Idioms](#8-rust-patterns--idioms)
9. [Rust: Macros](#9-rust-macros)
10. [CS: Data Structures (Hidden)](#10-cs-data-structures-hidden)
11. [CS: Algorithms (Hidden)](#11-cs-algorithms-hidden)
12. [CS: Memory & Architecture](#12-cs-memory--architecture)
13. [CS: Concurrency Internals](#13-cs-concurrency-internals)
14. [CS: Type Theory](#14-cs-type-theory)
15. [CS: Compiler Internals](#15-cs-compiler-internals)
16. [CS: OS & Systems](#16-cs-os--systems)

---

## 1. Rust: Type System

### Variance (covariant / contravariant / invariant)
- **Difficulty:** advanced
- **What it is:** Why `&'long T` can coerce to `&'short T` but not vice versa. The hidden rule behind lifetime errors.
- **Why it matters:** Explains a class of lifetime errors that seem impossible to fix without understanding variance. Essential for writing correct generic library code.
- **Study prompt:** "Teach me Rust variance — covariant, contravariant, invariant — with concrete examples showing how each affects lifetime coercions and why PhantomData changes variance."

---

### Higher-Rank Trait Bounds (HRTB) — `for<'a>`
- **Difficulty:** expert
- **What it is:** Expressing "this closure works for any lifetime", not just a specific one.
- **Why it matters:** Required when writing functions that accept callbacks operating on borrowed data of unknown lifetime. Appears in `Fn` trait bounds.
- **Study prompt:** "Teach me Higher-Rank Trait Bounds in Rust. What does `for<'a>` mean, why is it needed, and how does it differ from a normal lifetime parameter?"

---

### Lifetime Elision Rules
- **Difficulty:** intermediate
- **What it is:** The 3 compiler rules that let you omit lifetime annotations in most cases.
- **Why it matters:** Understanding elision means you can predict when annotations are required and why the compiler rejects certain signatures.
- **Study prompt:** "Teach me Rust's lifetime elision rules — all three of them — with examples showing what the compiler infers and cases where elision fails."

---

### Lifetime Subtyping
- **Difficulty:** advanced
- **What it is:** `'a: 'b` means `'a` lives at least as long as `'b`. How this interacts with coercion.
- **Why it matters:** Needed when writing structs or functions that hold multiple borrows with ordering constraints between their lifetimes.
- **Study prompt:** "Teach me lifetime subtyping in Rust. What does `'a: 'b` mean, how does it affect what you can assign, and show me a real case where it's required."

---

### Trait Object Safety Rules
- **Difficulty:** advanced
- **What it is:** Why some traits cannot become `dyn Trait` — the rules around `Self`, `Sized`, and generic methods.
- **Why it matters:** You hit this wall when trying to use a trait dynamically. Understanding the rules lets you design object-safe traits from the start.
- **Study prompt:** "Teach me Rust's object safety rules. Why can't every trait become dyn Trait? Cover all the rules and show workarounds for common violations."

---

### Orphan Rule & Coherence
- **Difficulty:** advanced
- **What it is:** Why you cannot implement external traits on external types. Prevents conflicting impls.
- **Why it matters:** Causes "upstream crates" compiler errors. Understanding it tells you when to use the newtype pattern.
- **Study prompt:** "Teach me Rust's orphan rule and coherence. Why does it exist, what exactly does it forbid, and how does the newtype pattern work around it?"

---

### Blanket Implementations
- **Difficulty:** intermediate
- **What it is:** `impl<T: Display> Foo for T` — implementing a trait for every type satisfying a bound.
- **Why it matters:** How the standard library implements `Into` from `From`, `ToString` from `Display`, etc. Understanding this prevents "conflicting implementations" errors.
- **Study prompt:** "Teach me blanket implementations in Rust with real examples from std. Explain how they interact with the orphan rule and when they cause coherence conflicts."

---

### Negative Implementations (`!Send`, `!Sync`)
- **Difficulty:** expert
- **What it is:** Opting out of auto-trait implementations and what that means for the type system.
- **Why it matters:** `*mut T` is `!Send` and `!Sync`. Understanding this is essential for writing wrapper types that encapsulate raw pointers safely.
- **Study prompt:** "Teach me negative implementations in Rust — !Send, !Sync, and how you explicitly opt out of auto-traits. Why is *mut T not Send?"

---

### `impl Trait` vs `dyn Trait`
- **Difficulty:** intermediate
- **What it is:** Static dispatch (monomorphized) vs dynamic dispatch (vtable). When to use each.
- **Why it matters:** Directly impacts binary size, compile time, and runtime performance. A core API design decision.
- **Study prompt:** "Teach me impl Trait vs dyn Trait in depth. Cover monomorphization, vtables, code size, performance, and when each is appropriate in API design."

---

### Associated Types vs Type Parameters
- **Difficulty:** intermediate
- **What it is:** Why `Iterator` uses `type Item` instead of `Iterator<Item>`. The semantic difference.
- **Why it matters:** Associated types enforce a single implementation per type. Type parameters allow multiple. Getting this wrong leads to unusable APIs.
- **Study prompt:** "Teach me the difference between associated types and type parameters in Rust traits. Why does Iterator use an associated type? When should I use each?"

---

### Generic Associated Types (GATs)
- **Difficulty:** expert
- **What it is:** Associated types that themselves have lifetime or type parameters. Unlocks streaming iterators.
- **Why it matters:** Needed for lending iterators (where items borrow from the iterator itself), generic containers, and async traits.
- **Study prompt:** "Teach me Generic Associated Types (GATs) in Rust. What problem do they solve, why weren't regular associated types enough, and show a real use case."

---

### Const Generics
- **Difficulty:** advanced
- **What it is:** Parameterizing types and functions over constant values, e.g. `[T; N]` where N is a generic const.
- **Why it matters:** Enables zero-cost type-level encoding of array sizes, matrix dimensions, and compile-time checked bounds.
- **Study prompt:** "Teach me const generics in Rust. Show how to write functions and types parameterized by const values, and what the current limitations are."

---

### Never Type (`!`)
- **Difficulty:** advanced
- **What it is:** The bottom type. A function returning `!` can coerce to any type. Used in diverging functions.
- **Why it matters:** Makes `panic!()`, `loop {}`, and `process::exit()` type-check in any position. Understanding this removes confusion about `match` arms.
- **Study prompt:** "Teach me the never type ! in Rust. What is a bottom type, why can ! coerce to any type, and where does this appear in real code?"

---

### Zero-Sized Types (ZSTs)
- **Difficulty:** advanced
- **What it is:** Types that occupy no memory: `PhantomData`, `()`, marker structs. Used for type-level logic.
- **Why it matters:** Vectors of ZSTs are used in sets. ZSTs enable the type-state pattern. Understanding them prevents memory layout surprises.
- **Study prompt:** "Teach me zero-sized types in Rust. What are they, what guarantees does the compiler make about them, and how are they used in real library design?"

---

### Unsized Types & `?Sized` Bound
- **Difficulty:** advanced
- **What it is:** Types whose size is not known at compile time: `str`, `[T]`, `dyn Trait`. How fat pointers handle them.
- **Why it matters:** Explains why `str` cannot live on the stack directly, why `Box<dyn Trait>` is two words, and what `?Sized` unlocks in generic bounds.
- **Study prompt:** "Teach me unsized types and the ?Sized bound in Rust. Why can't str be used directly, what are fat pointers, and when do I need ?Sized in generic bounds?"

---

### Fat Pointers / Wide Pointers
- **Difficulty:** advanced
- **What it is:** Two-word pointers: `(ptr, len)` for slices, `(ptr, vtable)` for `dyn Trait`. The memory layout.
- **Why it matters:** Explains the runtime cost of `dyn Trait`, why `Box<dyn Trait>` is 16 bytes, and how method dispatch works at the machine level.
- **Study prompt:** "Teach me fat pointers in Rust. Show the memory layout for slice fat pointers and trait object fat pointers. How does the vtable work?"

---

### `PhantomData<T>`
- **Difficulty:** expert
- **What it is:** Tells the compiler a type logically owns or uses `T` without storing it. Controls variance and drop check.
- **Why it matters:** Every unsafe generic type that holds raw pointers needs `PhantomData` to communicate ownership semantics to the borrow checker.
- **Study prompt:** "Teach me PhantomData<T> in Rust. Why is it needed, how does it affect variance and drop check, and show examples from real unsafe code."

---

### Specialization (nightly)
- **Difficulty:** expert
- **What it is:** Providing more specific impls that override blanket impls. RFC 1210 and its subtleties.
- **Why it matters:** Enables performance optimizations where a generic algorithm can be replaced by a faster type-specific one. Still unstable due to soundness issues.
- **Study prompt:** "Teach me specialization in Rust — what it is, why RFC 1210 exists, what the min_specialization subset allows, and what soundness problems block stabilization."

---

## 2. Rust: Memory & Ownership

### Non-Lexical Lifetimes (NLL)
- **Difficulty:** intermediate
- **What it is:** The borrow checker algorithm that tracks borrows by actual use, not lexical scope.
- **Why it matters:** NLL eliminated a whole class of false-positive borrow errors from pre-2018 Rust. Understanding it helps you read borrow checker error messages correctly.
- **Study prompt:** "Teach me Non-Lexical Lifetimes in Rust. How does NLL differ from the old lexical borrow checker? Show examples of code NLL accepts that the old checker rejected."

---

### Stacked Borrows Memory Model
- **Difficulty:** expert
- **What it is:** The formal model defining valid pointer aliasing in unsafe Rust. Ralf Jung's research.
- **Why it matters:** The mental model for writing correct unsafe code. Violations are undefined behavior even if they seem to work in practice.
- **Study prompt:** "Teach me the Stacked Borrows memory model. What invariants must unsafe Rust code maintain, and how does Miri use this model to detect UB?"

---

### `repr(C)`, `repr(Rust)`, `repr(packed)`, `repr(align)`
- **Difficulty:** advanced
- **What it is:** How to control the memory layout of structs. Critical for FFI and performance.
- **Why it matters:** Without `repr(C)`, you cannot safely pass structs across FFI boundaries. `repr(packed)` and `repr(align)` are tools for SIMD and zero-copy protocols.
- **Study prompt:** "Teach me all repr attributes in Rust — repr(C), repr(Rust), repr(packed), repr(align), repr(transparent), repr(u8). Show how each changes the memory layout."

---

### Alignment & Padding Rules
- **Difficulty:** advanced
- **What it is:** Why structs have gaps between fields. How the compiler inserts padding to satisfy alignment requirements.
- **Why it matters:** Affects struct size, cache efficiency, and FFI compatibility. Reordering fields can reduce struct size significantly.
- **Study prompt:** "Teach me struct alignment and padding in Rust. How does the compiler decide field order and padding? How can I minimize struct size by reordering fields?"

---

### Drop Order Rules
- **Difficulty:** advanced
- **What it is:** The exact order in which fields, variables, and temporaries are dropped. Subtle and critical.
- **Why it matters:** Wrong drop order can cause use-after-free in unsafe code. Understanding it is essential when fields hold references to each other.
- **Study prompt:** "Teach me Rust's drop order rules in depth. What is the order for struct fields, local variables, tuple elements, and temporaries in expressions?"

---

### `ManuallyDrop<T>`
- **Difficulty:** expert
- **What it is:** Wraps `T` and prevents its `Drop` from running. Essential in unsafe code building custom allocators.
- **Why it matters:** Used when you need to transfer ownership of a value to external code (FFI) or manage memory manually without the compiler's destructor running.
- **Study prompt:** "Teach me ManuallyDrop<T> in Rust. When is it needed, how does it prevent Drop from running, and show a real unsafe use case."

---

### `MaybeUninit<T>`
- **Difficulty:** expert
- **What it is:** A union that holds either initialized or uninitialized `T`. The safe way to handle uninit memory.
- **Why it matters:** Replaces the old `mem::uninitialized()` which is UB. Required for writing custom collections and working with uninitialized buffers.
- **Study prompt:** "Teach me MaybeUninit<T> in Rust. Why did mem::uninitialized() become UB? Show how to correctly initialize a buffer using MaybeUninit."

---

### Move Semantics vs Copy Semantics
- **Difficulty:** foundational
- **What it is:** Why `String` moves but `i32` copies. What makes a type `Copy`. The ownership transfer model.
- **Why it matters:** The most fundamental concept in Rust. Everything about ownership flows from this distinction.
- **Study prompt:** "Teach me move semantics vs copy semantics in Rust from first principles. What is the Copy trait, what types implement it, and what happens at the machine level?"

---

### Place Expressions (lvalues) vs Value Expressions
- **Difficulty:** advanced
- **What it is:** The semantic distinction between memory locations and values. Matters for assignment and borrows.
- **Why it matters:** Understanding place expressions explains why some things can be assigned to and some cannot. Relevant to partial moves and `ref` patterns.
- **Study prompt:** "Teach me the distinction between place expressions and value expressions in Rust. How does this affect borrowing, assignment, and match binding modes?"

---

### Stack Allocation vs Heap Allocation
- **Difficulty:** foundational
- **What it is:** What goes on the stack (fixed-size locals) vs heap (`Box`, `Vec`, `String`). The cost difference.
- **Why it matters:** Allocation strategy is the first performance consideration in any Rust program. Every `Box::new()` is a system call path.
- **Study prompt:** "Teach me stack vs heap allocation in Rust with concrete examples. What are the actual costs, and how does Rust's ownership model interact with allocation?"

---

### `mem::forget` and Memory Leaks
- **Difficulty:** advanced
- **What it is:** Leaking memory is safe in Rust. `mem::forget` skips `Drop`. Why this is intentional by design.
- **Why it matters:** Rust guarantees memory safety, not absence of leaks. Understanding this is crucial for designing APIs with `ManuallyDrop` and FFI.
- **Study prompt:** "Teach me mem::forget in Rust. Why is intentional memory leaking considered safe? How does this interact with the Leak amplification problem in safe APIs?"

---

### The Drop Glue Mechanism
- **Difficulty:** advanced
- **What it is:** How the compiler auto-generates `Drop` code for composite types that contain droppable fields.
- **Why it matters:** Even types without an explicit `impl Drop` generate drop code. Understanding drop glue is essential for performance-sensitive code and unsafe wrappers.
- **Study prompt:** "Teach me Rust's drop glue mechanism. How does the compiler generate drop code for structs and enums? How does explicit impl Drop interact with drop glue?"

---

## 3. Rust: Interior Mutability

### `UnsafeCell<T>`
- **Difficulty:** expert
- **What it is:** The root of all interior mutability. The only way to legally alias `&T` as `&mut T`. How `Cell` and `RefCell` are built on it.
- **Why it matters:** Every interior mutability type in Rust is ultimately `UnsafeCell`. Without it, even correct aliasing is undefined behavior per the Rust memory model.
- **Study prompt:** "Teach me UnsafeCell<T> — why it's the only legal way to have interior mutability, how Cell and RefCell are built on it, and what undefined behavior it prevents."

---

### `Cell<T>`
- **Difficulty:** intermediate
- **What it is:** Single-threaded interior mutability via copy. `get()` and `set()` with no borrow checker involvement.
- **Why it matters:** Zero-overhead interior mutability for `Copy` types. Used in `Rc`'s reference count and anywhere you need mutation through a shared reference.
- **Study prompt:** "Teach me Cell<T> in Rust. How does it achieve interior mutability without runtime checks? When should I use Cell vs RefCell?"

---

### `RefCell<T>`
- **Difficulty:** intermediate
- **What it is:** Runtime borrow checking. `borrow()` and `borrow_mut()` panic if the borrow rules are violated at runtime.
- **Why it matters:** The standard tool for interior mutability when you need references (not copies). The runtime cost is a reference count increment.
- **Study prompt:** "Teach me RefCell<T> in Rust. How does runtime borrow checking work internally, what triggers a panic, and what are the performance implications?"

---

### The `Rc<RefCell<T>>` Pattern
- **Difficulty:** intermediate
- **What it is:** The canonical single-threaded shared mutable state pattern. Why it exists and its costs.
- **Why it matters:** The Rust answer to "how do I have multiple owners of mutable data?" in single-threaded code. Common in GUI code and graph structures.
- **Study prompt:** "Teach me the Rc<RefCell<T>> pattern deeply. What problem does it solve, what are all its costs, and when should I use it vs alternatives?"

---

### Atomic Types & Memory Ordering
- **Difficulty:** expert
- **What it is:** `AtomicUsize`, `AtomicBool`. `Relaxed`, `Acquire`, `Release`, `AcqRel`, `SeqCst` — what each means for CPUs.
- **Why it matters:** The foundation of all lock-free concurrent programming. Using the wrong ordering causes data races that only manifest on certain CPU architectures.
- **Study prompt:** "Teach me Rust's atomic types and memory ordering from first principles. What does each ordering (Relaxed, Acquire, Release, SeqCst) actually guarantee at the CPU level?"

---

### `Mutex<T>` Internals & Poisoning
- **Difficulty:** advanced
- **What it is:** How `Mutex` wraps data, not code. What poison means and when to handle it.
- **Why it matters:** Rust's `Mutex` is unique — it owns the data it protects. Poisoning is a correctness mechanism most languages lack. Understanding it prevents subtle bugs.
- **Study prompt:** "Teach me Mutex<T> in Rust. Why does it wrap data instead of just being a lock? What is mutex poisoning, when does it trigger, and how should I handle it?"

---

### `RwLock<T>`
- **Difficulty:** advanced
- **What it is:** Multiple readers OR one writer. When it outperforms `Mutex` and when it doesn't (writer starvation).
- **Why it matters:** Often slower than `Mutex` in practice due to write starvation and implementation overhead. Understanding when the tradeoff is worth it is a system design skill.
- **Study prompt:** "Teach me RwLock<T> in Rust. When does it outperform Mutex, what is writer starvation, and what does the OS implementation look like under the hood?"

---

### `OnceLock` / `OnceCell`
- **Difficulty:** intermediate
- **What it is:** Lazy initialization patterns. Initialize exactly once, then read-only forever.
- **Why it matters:** The standard pattern for global configuration, singletons, and lazily-computed constants. Thread-safe with `OnceLock`.
- **Study prompt:** "Teach me OnceLock and OnceCell in Rust. How do they guarantee single initialization, what is the difference between them, and show real use cases."

---

## 4. Rust: Traits & Generics Deep

### `Fn`, `FnMut`, `FnOnce` Hierarchy
- **Difficulty:** intermediate
- **What it is:** Why there are three closure traits. Which one to use in bounds. The `call_once`/`call_mut`/`call` dispatch.
- **Why it matters:** Choosing the wrong trait bound either over-restricts callers or under-constrains the closure, causing runtime errors or inflexible APIs.
- **Study prompt:** "Teach me the Fn, FnMut, FnOnce trait hierarchy in Rust. What is the relationship between them, how does the compiler choose which a closure implements, and when do I use each in bounds?"

---

### Iterator Trait & Lazy Evaluation
- **Difficulty:** intermediate
- **What it is:** How `Iterator` is a pull-based protocol. Why `map`/`filter`/`chain` produce zero work until consumed.
- **Why it matters:** Understanding laziness lets you chain complex transformations with zero intermediate allocations. The foundation of idiomatic Rust data processing.
- **Study prompt:** "Teach me the Iterator trait's design in depth. How does lazy evaluation work, what is the state machine each adapter maintains, and how does the compiler optimize iterator chains?"

---

### `IntoIterator` & `FromIterator`
- **Difficulty:** intermediate
- **What it is:** How `for` loops desugar. How `collect()` knows what type to build.
- **Why it matters:** Writing `for x in collection` only works because of `IntoIterator`. Implementing these traits for custom types makes them first-class in Rust idioms.
- **Study prompt:** "Teach me IntoIterator and FromIterator. How does a for loop desugar, how does collect() know what to build, and how do I implement them for a custom collection?"

---

### `Index` & `IndexMut` Traits
- **Difficulty:** intermediate
- **What it is:** How `v[i]` desugars to `*v.index(i)`. How to make your type indexable.
- **Why it matters:** Understanding the desugar reveals why `v[i]` returns a place (can be assigned to) and why range indexing returns a slice.
- **Study prompt:** "Teach me the Index and IndexMut traits in Rust. How does v[i] desugar, why is the return type a reference, and how do I implement custom indexing?"

---

### `From`, `Into`, `TryFrom`, `TryInto`
- **Difficulty:** foundational
- **What it is:** The canonical conversion traits. How `Into` is auto-implemented from `From`. The `Try` variants for fallible conversions.
- **Why it matters:** Used everywhere. The blanket `impl<T, U: From<T>> Into<U> for T` means implementing `From` gives `Into` for free.
- **Study prompt:** "Teach me From, Into, TryFrom, TryInto in Rust. How does the blanket Into impl work, when do I implement From vs Into, and how do TryFrom/TryInto integrate with ?"

---

### `AsRef` & `AsMut`
- **Difficulty:** intermediate
- **What it is:** Cheap reference conversions. How `Path` accepts `&str`, `&String`, and `&OsStr` via a single bound.
- **Why it matters:** The idiomatic way to write functions that accept multiple string-like or path-like types without forcing allocation.
- **Study prompt:** "Teach me AsRef and AsMut in Rust. How do they differ from Deref and From? Show how std uses AsRef<Path> to accept multiple types in file I/O functions."

---

### `Borrow` & `BorrowMut`
- **Difficulty:** advanced
- **What it is:** Like `AsRef` but stronger: borrowed form must have same `Hash`/`Eq` as owned. Used in `HashMap`.
- **Why it matters:** Explains why `HashMap<String, V>` can be indexed with `&str` — because `String: Borrow<str>` and `str` has the same hash as `String`.
- **Study prompt:** "Teach me the Borrow trait in Rust. Why does it exist separately from AsRef, what contract does it impose, and how does HashMap use it to accept &str keys?"

---

### `ToOwned` Trait
- **Difficulty:** intermediate
- **What it is:** The owned counterpart to `Borrow`. How `str::to_owned()` produces `String`.
- **Why it matters:** Completes the owned/borrowed symmetry. Used in `Cow<'a, B>` to clone the borrowed form into the owned form when needed.
- **Study prompt:** "Teach me the ToOwned trait. How does it relate to Borrow, how is it used in Cow, and what is the relationship between str/String and [T]/Vec<T>?"

---

### The `?` Operator Desugaring
- **Difficulty:** intermediate
- **What it is:** How `?` expands to `From::from` + early return. Why your error types need `From` impls.
- **Why it matters:** Understanding the desugaring explains every "`?` cannot be used" error message and informs how to design error types.
- **Study prompt:** "Teach me the exact desugaring of the ? operator in Rust. What does it expand to, how does From::from participate, and how does this work with the Try trait?"

---

### Sealed Traits Pattern
- **Difficulty:** advanced
- **What it is:** Making a trait un-implementable outside your crate. Private supertrait technique.
- **Why it matters:** Allows you to add methods to a sealed trait without a breaking change. Used in `std` and major libraries.
- **Study prompt:** "Teach me the sealed traits pattern in Rust. How does the private supertrait technique prevent external implementations, and when should I use it?"

---

### Extension Traits Pattern
- **Difficulty:** advanced
- **What it is:** Adding methods to external types via a local trait. The ergonomic API design pattern.
- **Why it matters:** The standard way to add methods to foreign types (working around the orphan rule). Used pervasively in async Rust (e.g., `StreamExt`, `SinkExt`).
- **Study prompt:** "Teach me the extension traits pattern in Rust. How do I add methods to a foreign type using a local trait, and what are the design conventions?"

---

### Operator Overloading (`Add`, `Sub`, `Mul`, etc.)
- **Difficulty:** intermediate
- **What it is:** How `+`, `-`, `*` desugar to trait calls. How to implement them for custom types.
- **Why it matters:** Enables mathematical types (vectors, matrices, custom numerics) to use natural syntax without sacrificing Rust's type safety.
- **Study prompt:** "Teach me operator overloading in Rust. Show how +, -, *, /, %, ==, <, +=, etc. map to traits, and how to implement them for a custom numeric type."

---

### `Display`, `Debug`, and the Formatting Machinery
- **Difficulty:** intermediate
- **What it is:** How `format!()` dispatches. The `Write` trait. The `{:?}` vs `{}` distinction. Custom formatters.
- **Why it matters:** Understanding the machinery lets you write efficient custom formatters and use format specifiers correctly.
- **Study prompt:** "Teach me Rust's formatting machinery in depth. How does format! dispatch, what is the Write trait, how do I write a custom formatter, and what do all the format specifiers do?"

---

## 5. Rust: Closures Internals

### Closure Capture Desugaring
- **Difficulty:** advanced
- **What it is:** Every closure is an anonymous struct. Captures become fields. How the compiler decides capture mode.
- **Why it matters:** Understanding the desugaring explains closure sizes, why closures can't be cloned by default, and how to reason about capture semantics.
- **Study prompt:** "Teach me how Rust closures desugar to anonymous structs. Show the exact struct the compiler generates for different capture scenarios."

---

### Capture Modes: by ref, by mut ref, by value
- **Difficulty:** intermediate
- **What it is:** How the compiler chooses the minimal capture. When `move` forces by-value capture.
- **Why it matters:** Determines whether a closure is `Send`, whether it can outlive its environment, and what trait (`Fn`/`FnMut`/`FnOnce`) it implements.
- **Study prompt:** "Teach me Rust's closure capture modes. How does the compiler choose between capturing by reference, mutable reference, or value? What are all the rules?"

---

### Move Closures
- **Difficulty:** intermediate
- **What it is:** `move ||` forces all captures to be by value. Why this is needed for threads and async.
- **Why it matters:** The essential technique for sending closures across thread boundaries or into async tasks where the captured data must have `'static` lifetime.
- **Study prompt:** "Teach me move closures in Rust. Why does `move` force by-value captures, how does this interact with Send, and show real examples with threads and async."

---

### Function Pointers vs Closures
- **Difficulty:** intermediate
- **What it is:** `fn(i32)->i32` is zero-sized; a closure is a struct. Why function pointers can't capture environment.
- **Why it matters:** Explains why you can't always substitute `fn` pointers for closures and why closure types are unnameable.
- **Study prompt:** "Teach me the difference between function pointers and closures in Rust at the type level. When can a closure coerce to a function pointer, and when can't it?"

---

## 6. Rust: Async & Concurrency

### `Future` Trait Internals
- **Difficulty:** advanced
- **What it is:** `Poll::Pending` vs `Poll::Ready`. `Context` and `Waker`. How an executor drives a `Future` to completion.
- **Why it matters:** Everything in async Rust is ultimately a `Future`. Understanding polling is what separates someone who uses async from someone who can debug and optimize it.
- **Study prompt:** "Teach me the Future trait from first principles. What is Poll, how does Context work, what is a Waker, and how does an executor drive a future to completion?"

---

### `async`/`await` State Machine Desugaring
- **Difficulty:** expert
- **What it is:** How the compiler transforms `async fn` into an enum of states. Why async function sizes are surprising.
- **Why it matters:** Explains async function performance characteristics, why futures can be large, and how to reason about memory usage in async code.
- **Study prompt:** "Teach me how async/await desugars to a state machine in Rust. Show the enum the compiler generates, how .await becomes a yield point, and why async fn sizes are hard to predict."

---

### `Pin<P>` and `Unpin`
- **Difficulty:** expert
- **What it is:** Why self-referential structs need pinning. What `Pin` guarantees. How it prevents moves after pinning.
- **Why it matters:** The most confusing concept in async Rust. Required for understanding why `async fn` state machines require `Pin`, and for writing custom `Future` implementations.
- **Study prompt:** "Teach me Pin<P> and Unpin in Rust from first principles. Why do self-referential structs break when moved, how does Pin prevent this, and what does impl Unpin mean?"

---

### Waker and Executor Model
- **Difficulty:** expert
- **What it is:** How a `Waker` notifies the executor to re-poll. The relationship between tasks and futures.
- **Why it matters:** Required for writing custom executors, integrating Rust async with foreign event loops, and debugging spurious wake-ups.
- **Study prompt:** "Teach me how Wakers work in Rust async. How does a Waker get created and passed to futures, how does it notify the executor, and how is this implemented in Tokio?"

---

### `Send` + `Sync` in Async Code
- **Difficulty:** advanced
- **What it is:** Why async blocks crossing `.await` must be `Send` if run on a multi-thread runtime.
- **Why it matters:** The most common class of async compile errors. Understanding the rule makes them instantly diagnosable.
- **Study prompt:** "Teach me why Send matters across .await points in async Rust. What exactly makes an async block non-Send, and how do I fix it?"

---

### Atomic Memory Ordering (CPU Model)
- **Difficulty:** expert
- **What it is:** How CPUs reorder instructions. What `Acquire`/`Release` barriers mean at the hardware level.
- **Why it matters:** Without understanding CPU reordering, you cannot correctly reason about lock-free code. Correct code on x86 may fail on ARM.
- **Study prompt:** "Teach me CPU memory ordering from the hardware up. What instruction reorderings do CPUs perform, what do memory barriers prevent, and how does this map to Rust's atomic orderings?"

---

### Compare-and-Swap (CAS) Operations
- **Difficulty:** expert
- **What it is:** The atomic primitive behind all lock-free algorithms. ABA problem. `fetch_update`.
- **Why it matters:** CAS is the building block for lock-free queues, stacks, and counters. Understanding the ABA problem is essential for correctness.
- **Study prompt:** "Teach me compare-and-swap in Rust atomics. How does compare_exchange work, what is the ABA problem, and how does fetch_update help? Show a lock-free algorithm built on CAS."

---

### Fearless Concurrency Model
- **Difficulty:** intermediate
- **What it is:** How ownership and `Send`/`Sync` make data races a compile error. The theoretical foundation.
- **Why it matters:** Understanding why Rust's model prevents data races (not just races, but specifically data races) is the conceptual foundation for all concurrent Rust code.
- **Study prompt:** "Teach me Rust's fearless concurrency model. What is the precise definition of a data race, how do Send and Sync prevent them, and why are these marker traits auto-implemented?"

---

### `Arc<Mutex<T>>` vs `Rc<RefCell<T>>`
- **Difficulty:** intermediate
- **What it is:** The two shared-mutable-state patterns. Thread-safe vs single-threaded. When to use each.
- **Why it matters:** The first thing anyone needs when building stateful Rust programs. Understanding the tradeoffs prevents both over-engineering and unsound code.
- **Study prompt:** "Teach me Arc<Mutex<T>> vs Rc<RefCell<T>>. What are all the runtime costs of each, when is each appropriate, and what are the alternatives?"

---

## 7. Rust: Unsafe & Internals

### The 5 Unsafe Superpowers
- **Difficulty:** advanced
- **What it is:** Dereference raw pointer, call unsafe fn, implement unsafe trait, access `static mut`, access union fields.
- **Why it matters:** Knowing exactly what `unsafe` enables (and does not enable) is the first step to writing sound unsafe code.
- **Study prompt:** "Teach me the 5 things unsafe blocks unlock in Rust. For each, explain exactly what invariants the programmer must uphold, and give a concrete example."

---

### Raw Pointers (`*const T`, `*mut T`)
- **Difficulty:** advanced
- **What it is:** Pointers with no borrow checker guarantees. How to create, cast, and use them safely.
- **Why it matters:** Required for FFI, implementing data structures that the borrow checker cannot verify, and interfacing with memory-mapped hardware.
- **Study prompt:** "Teach me raw pointers in Rust. How do *const T and *mut T differ from references, how do I create and use them safely, and what are the rules for when they can be dereferenced?"

---

### `unsafe fn` vs `unsafe {}`
- **Difficulty:** advanced
- **What it is:** `fn foo()` is a safe fn with an unsafe block inside. `unsafe fn foo()` requires the caller to uphold invariants.
- **Why it matters:** The distinction defines who is responsible for safety invariants. Misusing it creates unsound safe APIs.
- **Study prompt:** "Teach me the distinction between unsafe fn and unsafe {} blocks in Rust. What does marking a function unsafe communicate to callers, and how should I document the invariants?"

---

### Safety Invariants & Contracts
- **Difficulty:** advanced
- **What it is:** The mental model of documenting what the caller must guarantee for unsafe code to be sound.
- **Why it matters:** Sound unsafe code is not just "it works on my machine" — it must be sound for all possible inputs. Safety contracts make this formal.
- **Study prompt:** "Teach me how to write and reason about safety invariants in Rust unsafe code. What should # Safety docs contain, and how do I check if my unsafe code is sound?"

---

### `transmute` and Its Dangers
- **Difficulty:** expert
- **What it is:** Reinterpreting raw bytes as a different type. Why it's the most dangerous fn in std.
- **Why it matters:** The nuclear option — misuse causes immediate UB. Understanding it is necessary for low-level serialization, type punning, and FFI.
- **Study prompt:** "Teach me mem::transmute in Rust. What does it actually do, what are all the ways it can cause UB, and what are the safer alternatives for common use cases?"

---

### Extern Functions & FFI
- **Difficulty:** advanced
- **What it is:** Calling C from Rust and vice versa. ABI, calling conventions, `extern "C"` blocks, bindgen.
- **Why it matters:** The bridge between Rust and the entire existing ecosystem of C libraries. Incorrect FFI is one of the main sources of unsoundness.
- **Study prompt:** "Teach me Rust FFI in depth. How do extern C blocks work, what is ABI, what are calling conventions, how do I safely wrap a C library, and what does bindgen do?"

---

### Union Types in Rust
- **Difficulty:** advanced
- **What it is:** C-style unions. All fields share memory. Reading any field is unsafe. Use cases.
- **Why it matters:** Used for type-punning, `MaybeUninit`, and interfacing with C APIs that use unions. The only Rust type where reading a field is always unsafe.
- **Study prompt:** "Teach me union types in Rust. How does memory layout work, why is reading a field always unsafe, and what are the legitimate use cases?"

---

### Global Allocator Interface
- **Difficulty:** expert
- **What it is:** How to replace jemalloc or the system allocator. The `GlobalAlloc` trait.
- **Why it matters:** Critical for embedded systems (where there may be no allocator), custom memory management, and instrumenting allocations for profiling.
- **Study prompt:** "Teach me Rust's global allocator interface. How does the GlobalAlloc trait work, how do I implement a custom allocator, and how does the #[global_allocator] attribute work?"

---

### Intrinsics (`core::intrinsics`)
- **Difficulty:** expert
- **What it is:** LLVM intrinsics exposed to Rust. `unreachable_unchecked`, `assume`, `black_box` for benchmarks.
- **Why it matters:** Enables fine-grained control over optimization hints. `black_box` is essential for micro-benchmarks. `unreachable_unchecked` enables performance-critical elimination of bounds checks.
- **Study prompt:** "Teach me Rust's compiler intrinsics. What is unreachable_unchecked, what does assume do, how does black_box prevent optimization in benchmarks, and which are stable?"

---

## 8. Rust: Patterns & Idioms

### Newtype Pattern
- **Difficulty:** foundational
- **What it is:** Wrapping a type in a tuple struct to add type safety or implement foreign traits.
- **Why it matters:** The primary workaround for the orphan rule. Also adds type safety (you can't pass a `UserId` where `PostId` is expected even though both are `u64`).
- **Study prompt:** "Teach me the newtype pattern in Rust. Show its uses for type safety, trait implementation, and unit types, with real examples from production code."

---

### Type State Pattern
- **Difficulty:** advanced
- **What it is:** Encoding state in the type system so invalid state transitions are compile errors.
- **Why it matters:** One of Rust's most powerful patterns. Turns runtime errors (calling `send()` before `connect()`) into compile errors.
- **Study prompt:** "Teach me the type state pattern in Rust with a detailed example (like a network connection or a builder). Show how state transitions consume and produce different types."

---

### Builder Pattern
- **Difficulty:** intermediate
- **What it is:** Constructing complex objects step by step. Method chaining. The owned vs `&mut self` tradeoff.
- **Why it matters:** The standard Rust API design for constructing complex structs with many optional parameters.
- **Study prompt:** "Teach me the builder pattern in Rust in depth. Compare the owned builder (consuming self) vs the mutable reference builder, show how to handle required vs optional fields."

---

### Typestate Finite State Machines
- **Difficulty:** advanced
- **What it is:** FSMs where each state is a distinct Rust type. Transitions consume the old state.
- **Why it matters:** The strongest form of the type state pattern. Protocols (TCP handshake, HTTP request lifecycle) encoded as type-level FSMs are impossible to misuse.
- **Study prompt:** "Teach me how to encode a finite state machine in Rust's type system. Show a protocol (like a TCP-like connection) where invalid transitions don't compile."

---

### The `FromStr` Trait Pattern
- **Difficulty:** foundational
- **What it is:** Implementing `FromStr` for your types to get ergonomic string parsing.
- **Why it matters:** Enables `"127.0.0.1".parse::<IpAddr>()` style ergonomics for custom types. Integrates with argument parsing libraries.
- **Study prompt:** "Teach me the FromStr trait in Rust. How do I implement it for a custom type, how does the parse() method use it, and what error type conventions should I follow?"

---

### Error Handling with `thiserror` & `anyhow`
- **Difficulty:** intermediate
- **What it is:** Idiomatic library vs application error handling. The `From` impl generation approach.
- **Why it matters:** The two canonical error handling crates represent two philosophies. Knowing when to use each separates good Rust error handling from cargo-culted boilerplate.
- **Study prompt:** "Teach me thiserror vs anyhow for error handling in Rust. What is the philosophy behind each, when should I use each, and how does thiserror generate From impls?"

---

### `Cow<'a, B>` (Clone on Write)
- **Difficulty:** advanced
- **What it is:** Avoiding allocation when a borrowed value suffices, cloning only when mutation is needed.
- **Why it matters:** The performance-critical pattern for functions that might need to modify input or might return it unchanged. Zero-allocation in the common case.
- **Study prompt:** "Teach me Cow<'a, B> in Rust. How does it work, what is the Borrow bound, when does it allocate, and show a real use case where it eliminates unnecessary allocation."

---

### Iterators as Lazy Pipelines
- **Difficulty:** intermediate
- **What it is:** Building computation chains that only execute on `collect()`/for-loop. Zero-cost abstractions.
- **Why it matters:** The foundation of idiomatic Rust data processing. LLVM optimizes iterator chains into tight loops, often matching hand-written imperative code.
- **Study prompt:** "Teach me how Rust's iterator pipelines are optimized. Show how map/filter/chain/flat_map compose, what the compiler generates, and how to write custom iterator adapters."

---

### Index-Based vs Pointer-Based Data Structures
- **Difficulty:** advanced
- **What it is:** Why Rust code often uses `Vec` + indices instead of pointers. Avoids borrow checker conflicts.
- **Why it matters:** The main technique for implementing graphs, trees with parent pointers, and other self-referential structures that the borrow checker would reject.
- **Study prompt:** "Teach me the index-based data structure pattern in Rust. Why do we use Vec+indices instead of pointers, how does it interact with the borrow checker, and what are the tradeoffs?"

---

### The Arena Allocation Pattern
- **Difficulty:** advanced
- **What it is:** Allocating many objects in a pool, freeing all at once. Solves lifetime complexity.
- **Why it matters:** The standard technique for compiler and interpreter data structures. Eliminates lifetime annotation complexity while maintaining performance.
- **Study prompt:** "Teach me arena allocation in Rust. How does it work, what lifetime does it assign to allocated objects, and show an example using bumpalo or a custom arena."

---

## 9. Rust: Macros

### `macro_rules!` Pattern Syntax
- **Difficulty:** intermediate
- **What it is:** The token tree matching language. `:expr`, `:ty`, `:ident`, `:tt`, `:block` matchers. Repetition.
- **Why it matters:** The first level of metaprogramming in Rust. Understanding the matcher syntax is required to read or write any non-trivial declarative macro.
- **Study prompt:** "Teach me macro_rules! in depth. Cover all fragment specifiers (:expr, :ty, :ident, :tt, :pat, :stmt, :block, :literal), repetition syntax, and show progressively complex examples."

---

### Procedural Macros (derive)
- **Difficulty:** advanced
- **What it is:** Generating code from a struct definition. `TokenStream` manipulation with `syn` + `quote`.
- **Why it matters:** Powers `#[derive(Serialize, Deserialize)]`, `#[derive(Debug)]` and nearly every major Rust framework. Understanding this unlocks the ability to write your own.
- **Study prompt:** "Teach me how to write a procedural derive macro in Rust. Show how to use syn to parse the input, manipulate the AST, and use quote to generate output code."

---

### Attribute Macros
- **Difficulty:** advanced
- **What it is:** `#[my_macro]` that transforms or wraps the annotated item. Used in web frameworks.
- **Why it matters:** Powers `#[tokio::main]`, `#[actix_web::get("/")]`, and similar ergonomic annotations. A fundamentally different kind of code generation than derive.
- **Study prompt:** "Teach me attribute macros in Rust. How do they differ from derive macros, what is their input and output, and show how to write one that transforms a function."

---

### Function-Like Procedural Macros
- **Difficulty:** advanced
- **What it is:** `sql!("SELECT ...")` — macros that look like function calls but work at compile time.
- **Why it matters:** Used for compile-time SQL validation, regex compilation, HTML template parsing, and any DSL that benefits from compile-time checking.
- **Study prompt:** "Teach me function-like procedural macros in Rust. Show how to write one that parses a custom DSL at compile time and generates Rust code."

---

### Hygiene in Macros
- **Difficulty:** advanced
- **What it is:** Why variables in macros don't accidentally capture names from the caller's scope.
- **Why it matters:** The property that makes declarative macros composable and safe. Understanding when hygiene is broken (intentionally or not) is required for advanced macro authoring.
- **Study prompt:** "Teach me macro hygiene in Rust. What does hygienic mean, how does Rust implement it for macro_rules!, when is it intentionally broken with $crate, and what are the rules for proc macros?"

---

### The `tt`-Muncher Pattern
- **Difficulty:** expert
- **What it is:** Consuming a token tree recursively in `macro_rules!`. Enables complex DSLs.
- **Why it matters:** The most powerful declarative macro technique. Enables macros that parse arbitrary syntax, implement loop-like constructs, and accumulate results recursively.
- **Study prompt:** "Teach me the tt-muncher pattern in Rust macros. How does recursive token consumption work, what is the push-down accumulator pattern, and show a real example."

---

## 10. CS: Data Structures (Hidden)

### Amortized Complexity Analysis
- **Difficulty:** intermediate
- **What it is:** Why `Vec::push` is O(1) amortized despite occasional O(n) resizing. The potential method.
- **Why it matters:** The correct way to analyze data structures with occasionally expensive operations. Essential for evaluating dynamic arrays, hash tables, and splay trees.
- **Study prompt:** "Teach me amortized complexity analysis. Explain the accounting method and potential method, then apply both to Vec's push operation to prove O(1) amortized."

---

### B-Trees & B+ Trees
- **Difficulty:** advanced
- **What it is:** The data structure behind every database index and filesystem. Why not binary trees.
- **Why it matters:** Understanding B-trees explains the performance characteristics of every relational database, key-value store, and filesystem you will ever use.
- **Study prompt:** "Teach me B-trees and B+ trees from scratch. Why do databases use them instead of binary trees, how do splits and merges work, and what is the difference between B and B+?"

---

### Skip Lists
- **Difficulty:** advanced
- **What it is:** Probabilistic layered linked lists achieving O(log n) ops. Used in Redis sorted sets.
- **Why it matters:** A concurrent-friendly alternative to balanced BSTs. Understanding them shows how randomization can replace complex balancing logic.
- **Study prompt:** "Teach me skip lists. How does the probabilistic layer structure work, prove the expected O(log n) complexity, and explain why they're used in Redis."

---

### Bloom Filters
- **Difficulty:** intermediate
- **What it is:** Probabilistic membership test. Zero false negatives, tunable false positives. No deletions.
- **Why it matters:** Used in databases (avoid disk lookups for missing keys), CDNs, spell checkers, and anywhere a small false positive rate is acceptable to save memory.
- **Study prompt:** "Teach me bloom filters. How do multiple hash functions reduce false positives, what is the math for optimal filter size, and what are Counting Bloom Filters?"

---

### Rope Data Structure
- **Difficulty:** advanced
- **What it is:** B-tree of string chunks. Used in text editors (VSCode). O(log n) insert/delete anywhere.
- **Why it matters:** Understanding ropes explains why text editors can handle gigabyte files with instant edits. The classic solution to the mutable string performance problem.
- **Study prompt:** "Teach me the Rope data structure. How does splitting and concatenating work, what is the complexity for common text editor operations, and how does it compare to a gap buffer?"

---

### Persistent Data Structures
- **Difficulty:** expert
- **What it is:** Immutable structures that share structure between versions. O(log n) path copying.
- **Why it matters:** The foundation of functional languages (Clojure, Haskell) and undo/redo systems. Understanding structural sharing is essential for efficient immutable code.
- **Study prompt:** "Teach me persistent data structures. How does path copying work for a persistent BST, what is structural sharing, and how does Clojure's persistent hash map work?"

---

### Van Emde Boas Tree
- **Difficulty:** expert
- **What it is:** O(log log U) operations on integers in range [0, U). Beats comparison-based trees.
- **Why it matters:** Demonstrates that for integer keys, information theory permits faster-than-O(log n) operations. Foundation for understanding word RAM models.
- **Study prompt:** "Teach me the Van Emde Boas tree. How does the recursive structure achieve O(log log U), and what are the practical tradeoffs vs a simpler structure like a binary trie?"

---

### Sparse Table (RMQ)
- **Difficulty:** advanced
- **What it is:** Range Minimum Query in O(1) after O(n log n) preprocessing. Uses binary lifting.
- **Why it matters:** The classic application of sparse tables. Understanding binary lifting here transfers directly to LCA on trees and many other range query problems.
- **Study prompt:** "Teach me sparse tables for Range Minimum Query. How does binary lifting work, why does the overlap property allow O(1) queries, and implement it in Rust."

---

### Suffix Array + LCP Array
- **Difficulty:** expert
- **What it is:** All suffixes of a string, sorted. Combined with LCP enables string algorithms in O(n log n).
- **Why it matters:** The practical alternative to suffix trees. Used in bioinformatics, data compression, and competitive programming for string matching problems.
- **Study prompt:** "Teach me suffix arrays and LCP arrays. How is a suffix array built efficiently, what problems does the LCP array solve, and how do they compare to suffix trees?"

---

### Suffix Automaton (SAM)
- **Difficulty:** expert
- **What it is:** The smallest automaton recognizing all substrings. O(n) build. Used in competitive programming.
- **Why it matters:** The most powerful string data structure. Solves in O(n) what suffix trees solve in O(n log n) in practice. Essential for top competitive programmers.
- **Study prompt:** "Teach me the Suffix Automaton (SAM). What does it represent, how is the online O(n) construction algorithm derived, and what problems can it solve efficiently?"

---

### Treap (Tree + Heap)
- **Difficulty:** advanced
- **What it is:** BST with random priorities maintaining heap property. Expected O(log n). Simple to implement.
- **Why it matters:** One of the most practical balanced BST implementations. Easy to implement correctly, supports split/merge operations, and naturally handles implicit keys.
- **Study prompt:** "Teach me treaps. How do random priorities maintain balance, how do split and merge work, and how is an implicit treap used to implement a sequence data structure?"

---

### Segment Tree with Lazy Propagation
- **Difficulty:** advanced
- **What it is:** Range updates + range queries in O(log n). Lazy tag defers updates until needed.
- **Why it matters:** The workhorse of competitive programming. Handles any associative operation over ranges with range updates. Understanding lazy propagation is the key insight.
- **Study prompt:** "Teach me segment trees with lazy propagation from scratch. How does the lazy tag mechanism work, implement range add + range sum query in Rust, and show how to generalize it."

---

### Fenwick Tree (BIT)
- **Difficulty:** intermediate
- **What it is:** Prefix sum updates/queries in O(log n) with minimal code. The elegant bitwise trick.
- **Why it matters:** The simplest data structure for prefix sums with updates. The bitwise `x & (-x)` trick is one of the most elegant ideas in competitive programming.
- **Study prompt:** "Teach me the Fenwick tree (Binary Indexed Tree). Derive the bitwise lowbit trick from first principles, implement prefix sum queries and point updates, and explain 2D Fenwick trees."

---

### Disjoint Set Union (DSU / Union-Find)
- **Difficulty:** intermediate
- **What it is:** Path compression + union by rank gives near-O(1) per op. Used in Kruskal's MST.
- **Why it matters:** One of the most elegant data structures. The inverse Ackermann function complexity is one of CS's most surprising results.
- **Study prompt:** "Teach me DSU with path compression and union by rank. Prove the amortized complexity, implement it in Rust, and show its application in Kruskal's MST algorithm."

---

### Lock-Free Queues (Michael-Scott)
- **Difficulty:** expert
- **What it is:** CAS-based concurrent queue. The canonical lock-free data structure in systems research.
- **Why it matters:** The foundation for understanding concurrent data structure design. Used in the crossbeam crate and other high-performance Rust concurrency libraries.
- **Study prompt:** "Teach me the Michael-Scott lock-free queue. How does it use CAS for enqueue and dequeue, what is the ABA problem in this context, and how does Rust's crossbeam implement this safely?"

---

### Fibonacci Heap
- **Difficulty:** expert
- **What it is:** O(1) amortized `decrease-key`. Used in Dijkstra for theoretical O(E + V log V) bound.
- **Why it matters:** Understanding why Fibonacci heaps are rarely used in practice (despite theoretical superiority) is a lesson in the gap between asymptotic complexity and real performance.
- **Study prompt:** "Teach me Fibonacci heaps. How do lazy merging and the cascading cut operation achieve O(1) amortized decrease-key, and why are they rarely used in practice?"

---

## 11. CS: Algorithms (Hidden)

### Manacher's Algorithm
- **Difficulty:** advanced
- **What it is:** All palindromic substrings of a string in O(n). The mirror observation trick.
- **Why it matters:** The classic example of using previous computation to avoid redundant work. The mirror trick is a beautiful insight transferable to other problems.
- **Study prompt:** "Teach me Manacher's algorithm. Derive the O(n) algorithm step by step from the naive O(n²) approach, explain the mirror property, and implement it in Rust."

---

### Z-Algorithm
- **Difficulty:** advanced
- **What it is:** Z-array: at each position, the length of the longest substring matching a prefix. O(n).
- **Why it matters:** A simpler alternative to KMP for many pattern matching problems. The Z-array is directly useful for string period finding and pattern matching.
- **Study prompt:** "Teach me the Z-algorithm. Derive the Z-array construction, prove O(n) complexity, and show how to use it for pattern matching by concatenating pattern + $ + text."

---

### KMP Failure Function
- **Difficulty:** intermediate
- **What it is:** Pattern matching in O(n+m) using the prefix-suffix overlap table.
- **Why it matters:** The first string matching algorithm most competitive programmers learn deeply. The failure function is a profound idea about string structure.
- **Study prompt:** "Teach me KMP. Derive the failure function from first principles (why is it the proper prefix that is also a suffix?), prove O(n+m), and implement it in Rust."

---

### Aho-Corasick Automaton
- **Difficulty:** advanced
- **What it is:** Multi-pattern string matching in O(n + total_pattern_length). KMP generalized to a trie.
- **Why it matters:** The industrial-strength multi-pattern matching algorithm used in intrusion detection systems, firewalls, and search engines.
- **Study prompt:** "Teach me the Aho-Corasick automaton. How does it extend KMP to multiple patterns using failure links on a trie, prove the complexity, and implement it."

---

### Rolling Hash / Rabin-Karp
- **Difficulty:** intermediate
- **What it is:** Polynomial hashing enabling O(1) substring hash comparison. Randomized string matching.
- **Why it matters:** The gateway to hashing-based string algorithms. Rolling hash appears in longest duplicate substring, plagiarism detection, and many other problems.
- **Study prompt:** "Teach me rolling hash and Rabin-Karp. How does the polynomial rolling hash work, how do you handle collisions, and what is the probability of a false match?"

---

### Bitmask DP
- **Difficulty:** advanced
- **What it is:** DP over subsets encoded as bitmasks. O(2^n × n) algorithms on sets. TSP and set cover.
- **Why it matters:** The standard approach to exact exponential algorithms for NP-hard problems on small inputs. TSP with n≤20 is a classic bitmask DP problem.
- **Study prompt:** "Teach me bitmask DP. How do we enumerate subsets, how is the Traveling Salesman Problem solved with bitmask DP, and what are the key implementation techniques in Rust?"

---

### Convex Hull Trick (DP Optimization)
- **Difficulty:** expert
- **What it is:** Optimizes DP transitions of the form `dp[i] = min(dp[j] + cost(j,i))` to O(n).
- **Why it matters:** Transforms O(n²) DP problems into O(n) when the cost function satisfies certain convexity conditions. Appears in many hard competitive programming problems.
- **Study prompt:** "Teach me the convex hull trick for DP optimization. Derive why it works geometrically (lines on a convex hull), implement the monotone version and the Li Chao tree version."

---

### Divide and Conquer DP Optimization
- **Difficulty:** expert
- **What it is:** When cost satisfies the quadrangle inequality, O(n²) DP becomes O(n log n).
- **Why it matters:** One of the most powerful DP optimizations. The quadrangle inequality is a deep property that appears in many interval DP problems.
- **Study prompt:** "Teach me divide-and-conquer DP optimization. What is the quadrangle inequality, how does it imply the optimal split point is monotone, and how does this give O(n log n)?"

---

### Matrix Exponentiation
- **Difficulty:** advanced
- **What it is:** Computing recurrence relations (like Fibonacci) in O(k³ log n) via fast matrix power.
- **Why it matters:** Transforms linear recurrences computable in O(n) into O(log n). Essential for DP problems that need the nth element of a recurrence for huge n.
- **Study prompt:** "Teach me matrix exponentiation. How does fast matrix power work, how do I encode a linear recurrence as matrix multiplication, and show examples beyond Fibonacci."

---

### Mo's Algorithm
- **Difficulty:** advanced
- **What it is:** Offline range queries answered in O((n+q)√n) by sorting queries by a block structure.
- **Why it matters:** The elegant square root decomposition trick. Applicable to any problem where you can add/remove elements and maintain an answer incrementally.
- **Study prompt:** "Teach me Mo's algorithm. How does block-based query sorting achieve O((n+q)√n), implement it for range frequency queries in Rust, and explain Mo's algorithm with updates."

---

### Heavy-Light Decomposition (HLD)
- **Difficulty:** expert
- **What it is:** Decomposes tree paths into O(log n) segments enabling range queries on trees.
- **Why it matters:** The standard technique for path queries on trees. Reduces tree path problems to array range problems solvable with segment trees.
- **Study prompt:** "Teach me Heavy-Light Decomposition from scratch. Prove O(log n) chains, show how to map tree paths to array ranges, and implement path sum queries with a segment tree."

---

### Centroid Decomposition
- **Difficulty:** expert
- **What it is:** Splits tree at centroid recursively. Solves path problems in O(n log² n).
- **Why it matters:** The technique for problems involving paths between all pairs of nodes in a tree. The centroid gives a guaranteed O(log n) depth decomposition.
- **Study prompt:** "Teach me centroid decomposition. How is the centroid found efficiently, why does recursion on components give O(log n) depth, and show a path problem solved with it."

---

### Euler Tour / Tree Linearization
- **Difficulty:** advanced
- **What it is:** Maps a tree to an array so subtree queries become range queries. DFS in/out time.
- **Why it matters:** Reduces a large class of tree problems to array problems. The DFS in/out time encodes subtree structure in a way that segment trees can exploit.
- **Study prompt:** "Teach me tree Euler tour and DFS in/out times. How does this linearize the tree, why does the subtree of node v correspond to range [in_v, out_v], and show subtree sum queries."

---

### Tarjan's SCC Algorithm
- **Difficulty:** advanced
- **What it is:** Strongly Connected Components in O(V+E) using low-link values on the DFS stack.
- **Why it matters:** SCCs reduce many graph problems. Understanding Tarjan's algorithm deeply (vs Kosaraju's) demonstrates the power of DFS ordering properties.
- **Study prompt:** "Teach me Tarjan's SCC algorithm. What are low-link values, why does the DFS stack identify SCCs, prove correctness, and implement it in Rust."

---

### Articulation Points & Bridges
- **Difficulty:** advanced
- **What it is:** Cut vertices and cut edges in O(V+E). Foundation for biconnected components.
- **Why it matters:** Essential in network reliability analysis. Understanding bridge-finding applies to many connectivity problems in competitive programming.
- **Study prompt:** "Teach me articulation points and bridges in graphs. How does DFS low-link analysis find them, what are biconnected components, and implement both algorithms in Rust."

---

### Dinic's Max Flow
- **Difficulty:** expert
- **What it is:** O(V² E) max flow using level graphs and blocking flows. Fastest general max-flow.
- **Why it matters:** The standard max-flow algorithm for competitive programming and network optimization. Understanding blocking flows is the conceptual leap over Ford-Fulkerson.
- **Study prompt:** "Teach me Dinic's algorithm for maximum flow. How do level graphs and blocking flows give the O(V²E) bound, and why is it O(E√V) for unit-capacity graphs?"

---

### 2-SAT
- **Difficulty:** advanced
- **What it is:** Boolean satisfiability with only 2-literal clauses, solved in O(V+E) via SCC.
- **Why it matters:** A surprisingly powerful algorithm — many seemingly hard combinatorial problems reduce to 2-SAT. Understanding the SCC-based solution is illuminating.
- **Study prompt:** "Teach me 2-SAT. How does the implication graph encode 2-SAT, why does an SCC containing both x and ¬x imply UNSAT, and how do we extract a satisfying assignment?"

---

### Chinese Remainder Theorem
- **Difficulty:** advanced
- **What it is:** Solving systems of modular congruences. Used in competitive math and cryptography.
- **Why it matters:** Fundamental in number theory, RSA implementation, and many number-theoretic DP optimizations. Understanding it requires understanding modular inverses.
- **Study prompt:** "Teach me the Chinese Remainder Theorem from first principles. Prove it constructively, implement the general algorithm for non-coprime moduli, and show a competitive programming application."

---

### Binary Exponentiation
- **Difficulty:** foundational
- **What it is:** Computing `a^n mod m` in O(log n) using repeated squaring. The fundamental number theory tool.
- **Why it matters:** Used in virtually every number-theoretic algorithm. The technique of repeated squaring appears in matrix exponentiation, modular inverses, and cryptography.
- **Study prompt:** "Teach me binary exponentiation. Derive the algorithm from the binary representation of the exponent, implement it in Rust with overflow-safe modular arithmetic."

---

### Euler's Totient & Multiplicative Functions
- **Difficulty:** advanced
- **What it is:** φ(n) counts integers coprime to n. Foundation of RSA and number theoretic algorithms.
- **Why it matters:** The theoretical foundation of RSA encryption. The totient function and its properties appear throughout number theory and competitive programming.
- **Study prompt:** "Teach me Euler's totient function and multiplicative functions. How do you compute φ(n) efficiently, what is the multiplicative property, and how does this connect to RSA?"

---

### Bitset Optimization
- **Difficulty:** advanced
- **What it is:** Using 64-bit integers as bool arrays. Reduces O(n²) to O(n²/64) in many DP problems.
- **Why it matters:** A constant factor optimization that often makes the difference between passing and failing a time limit. Bitset DP for subset problems is a common competitive programming technique.
- **Study prompt:** "Teach me bitset optimization for DP. Show how to accelerate 0/1 knapsack and other DP transitions using bitset operations, and implement it efficiently in Rust."

---

## 12. CS: Memory & Architecture

### CPU Cache Hierarchy (L1/L2/L3)
- **Difficulty:** intermediate
- **What it is:** Why cache misses cost 100+ cycles vs 4 for L1 hits. How data layout dominates runtime.
- **Why it matters:** Cache efficiency is the single largest factor in real-world program performance. Big-O analysis cannot capture it.
- **Study prompt:** "Teach me the CPU cache hierarchy. What are the sizes and latencies of L1/L2/L3 caches, how does this explain why array traversal beats linked list traversal, and how do I write cache-friendly Rust?"

---

### Cache Lines & Spatial Locality
- **Difficulty:** intermediate
- **What it is:** 64-byte cache lines. Why iterating arrays beats linked lists regardless of O complexity.
- **Why it matters:** The single most important hardware fact for writing high-performance code. Struct layout decisions flow directly from this.
- **Study prompt:** "Teach me cache lines and spatial locality. How does a 64-byte cache line work, what is prefetching, and show how struct layout affects cache efficiency with benchmarks."

---

### False Sharing in Concurrent Code
- **Difficulty:** advanced
- **What it is:** Two threads on different variables in the same cache line cause cache coherence thrashing.
- **Why it matters:** A performance bug that cannot be detected by correctness testing. A 10x slowdown from threads competing for the same cache line.
- **Study prompt:** "Teach me false sharing. How does cache coherence cause performance degradation when threads share a cache line, and how do I use padding (or cache_padded) to fix it in Rust?"

---

### NUMA (Non-Uniform Memory Access)
- **Difficulty:** expert
- **What it is:** Memory access latency depends on which socket allocated the memory. Critical for HPC.
- **Why it matters:** On multi-socket servers, incorrect memory placement causes 3-4x slowdowns. Essential for writing high-performance server-side Rust.
- **Study prompt:** "Teach me NUMA architecture. How does it differ from UMA, what is the performance impact of cross-NUMA memory access, and how does one write NUMA-aware code in Rust?"

---

### Virtual Memory & Page Tables
- **Difficulty:** advanced
- **What it is:** How the OS maps process virtual addresses to physical RAM. 4-level page tables on x86-64.
- **Why it matters:** Explains memory isolation, how `mmap` works, why allocation is expensive, and the cost of page faults. Essential for understanding OS-level performance.
- **Study prompt:** "Teach me virtual memory and x86-64 page tables. How does 4-level paging work, what is a page fault, and how does the OS use this mechanism for copy-on-write and demand paging?"

---

### TLB (Translation Lookaside Buffer)
- **Difficulty:** advanced
- **What it is:** Cache for page table entries. TLB misses are expensive. Huge pages reduce TLB pressure.
- **Why it matters:** High TLB miss rates cause significant overhead in workloads with large working sets. Understanding this motivates huge pages and memory-efficient data structure design.
- **Study prompt:** "Teach me the TLB. Why is page table lookup expensive without it, what is a TLB miss, how do huge pages reduce TLB pressure, and how do I observe TLB effects in benchmarks?"

---

### Branch Prediction & Misprediction Cost
- **Difficulty:** advanced
- **What it is:** Modern CPUs predict branches speculatively. Mispredicts flush the pipeline (~15 cycles).
- **Why it matters:** Unpredictable branches cause measurable performance loss. Understanding this motivates branchless code and `likely`/`unlikely` hints.
- **Study prompt:** "Teach me CPU branch prediction. How does a branch predictor work, what is the cost of misprediction, and how do I write branchless alternatives in Rust?"

---

### Out-of-Order Execution
- **Difficulty:** expert
- **What it is:** CPUs execute instructions in a different order than written. Memory ordering barriers prevent reordering.
- **Why it matters:** The reason memory ordering in concurrent code matters. Without barriers, operations visible to one CPU may appear in a different order to another.
- **Study prompt:** "Teach me out-of-order execution. What reorderings can CPUs perform, how do memory barriers prevent them, and how does this connect to Rust's atomic memory ordering model?"

---

### SIMD / Vectorization
- **Difficulty:** advanced
- **What it is:** Single instruction operating on multiple data (SSE, AVX). 4x–16x throughput for numeric code.
- **Why it matters:** The primary source of computational throughput in numeric, multimedia, and ML workloads. Rust's `std::simd` and auto-vectorization make this accessible.
- **Study prompt:** "Teach me SIMD and vectorization. What are SSE/AVX registers, how does auto-vectorization work in LLVM, and how do I use std::simd in Rust to write explicit SIMD code?"

---

### Memory Allocator Internals (jemalloc, tcmalloc)
- **Difficulty:** expert
- **What it is:** Thread-local caches, size classes, slab allocation. Why allocation is expensive.
- **Why it matters:** Understanding allocator internals explains allocation performance, fragmentation, and how to avoid allocation in hot paths.
- **Study prompt:** "Teach me memory allocator internals. How does jemalloc use size classes and thread-local caches, what is slab allocation, and what makes a heap allocation expensive?"

---

### `mmap` and Memory-Mapped Files
- **Difficulty:** advanced
- **What it is:** Mapping files directly into the address space. Zero-copy I/O. How databases use it.
- **Why it matters:** The fastest way to read large files. Used by SQLite, LMDB, and many other databases as their primary I/O mechanism.
- **Study prompt:** "Teach me mmap and memory-mapped files. How does mmap work at the OS level, what are the performance benefits, what are the pitfalls, and how do I use it in Rust?"

---

## 13. CS: Concurrency Internals

### Memory Ordering Model (C++11/Rust)
- **Difficulty:** expert
- **What it is:** The formal model of what reorderings are allowed. Sequential consistency vs relaxed.
- **Why it matters:** The foundation for all correct concurrent programming with atomics. Without this model, "it works on my machine" means nothing for concurrent code.
- **Study prompt:** "Teach me the C++11/Rust memory ordering model formally. What are the happens-before and synchronizes-with relations, and how do they define the behavior of atomic operations?"

---

### ABA Problem in Lock-Free Structures
- **Difficulty:** expert
- **What it is:** CAS succeeds incorrectly because A→B→A looks like no change. Hazard pointers solve it.
- **Why it matters:** The fundamental correctness problem in lock-free algorithms. Understanding it is required to write any correct lock-free data structure.
- **Study prompt:** "Teach me the ABA problem. Show a concrete example of how it causes incorrect behavior in a lock-free stack, and explain hazard pointers and tagged pointers as solutions."

---

### Epoch-Based Reclamation
- **Difficulty:** expert
- **What it is:** Safe memory reclamation for lock-free structures without garbage collection (crossbeam).
- **Why it matters:** The technique used in crossbeam (Rust's concurrency library) for safely freeing memory in lock-free data structures.
- **Study prompt:** "Teach me epoch-based reclamation. How do epochs track which threads are accessing data, why is it safe to free retired objects from old epochs, and how does crossbeam implement this?"

---

### Work-Stealing Schedulers
- **Difficulty:** expert
- **What it is:** How async runtimes (Tokio) distribute tasks. Deques per thread, steal from tail.
- **Why it matters:** The scheduling algorithm behind Tokio, Rayon, and most modern parallel runtimes. Understanding it explains why async Rust scales well across cores.
- **Study prompt:** "Teach me work-stealing schedulers. How does the Chase-Lev deque enable efficient work stealing, why steal from the opposite end, and how does Tokio implement this?"

---

### Spinlocks vs Mutexes
- **Difficulty:** intermediate
- **What it is:** Spinlocks burn CPU waiting; mutexes park the thread. When each is better.
- **Why it matters:** Choosing the wrong synchronization primitive is a common performance mistake. Spinlocks are faster for microsecond contention; mutexes for millisecond.
- **Study prompt:** "Teach me spinlocks vs OS mutexes. When does spinning outperform parking, how do adaptive mutexes (like parking_lot) combine both strategies, and how do I choose in Rust?"

---

### Read-Copy-Update (RCU)
- **Difficulty:** expert
- **What it is:** Linux kernel synchronization: readers proceed without locks, writers update via atomic pointer swap.
- **Why it matters:** The most scalable read-mostly synchronization mechanism. Used throughout the Linux kernel. Understanding it gives insight into the limits of lock-based synchronization.
- **Study prompt:** "Teach me Read-Copy-Update (RCU). How do readers proceed without any synchronization, how do writers ensure readers finish before freeing old data, and are there Rust equivalents?"

---

## 14. CS: Type Theory

### Parametric Polymorphism
- **Difficulty:** intermediate
- **What it is:** Generics: a function that works identically for all types (Rust generics, Haskell's `forall`).
- **Why it matters:** The foundation of Rust's generic system. Understanding parametricity gives you theorems about what a function can and cannot do based solely on its type signature.
- **Study prompt:** "Teach me parametric polymorphism. What does it mean for a function to work identically for all types, what are free theorems, and how does Rust's monomorphization relate to Haskell's System F?"

---

### Ad-Hoc Polymorphism
- **Difficulty:** intermediate
- **What it is:** Traits/typeclasses: different behavior per type. Rust traits, Haskell typeclasses.
- **Why it matters:** Understanding the distinction between parametric and ad-hoc polymorphism clarifies when to use generics vs traits and when to use `impl Trait` vs `dyn Trait`.
- **Study prompt:** "Teach me ad-hoc polymorphism vs parametric polymorphism. How do Rust traits implement ad-hoc polymorphism, and what is the relationship to Haskell's typeclasses?"

---

### Algebraic Data Types (ADT)
- **Difficulty:** intermediate
- **What it is:** Product types (structs) and sum types (enums). The algebra of types. Isomorphisms.
- **Why it matters:** The theoretical foundation that explains why Rust's `Option<T>` is better than null, and why enums model state machines so well.
- **Study prompt:** "Teach me algebraic data types from first principles. What is the cardinality of a product type vs sum type, what are type isomorphisms, and how does this algebra explain Option and Result?"

---

### Variance in Type Systems
- **Difficulty:** advanced
- **What it is:** Covariant, contravariant, invariant. Why `fn(T)->U` is contravariant in T, covariant in U.
- **Why it matters:** The theoretical underpinning of Rust's lifetime variance. Understanding this in general (not just Rust) gives you the mental model to reason about any generic type system.
- **Study prompt:** "Teach me variance in type systems from theory. Why is function types contravariant in their argument type, what is the Liskov Substitution Principle, and how does this manifest in Rust?"

---

### Linear Types & Affine Types
- **Difficulty:** advanced
- **What it is:** The theoretical foundation of Rust's ownership. Each value used exactly once (linear) or at most once (affine).
- **Why it matters:** Rust's ownership system is an affine type system. Understanding this places Rust in a broader context of programming language theory and explains the design choices.
- **Study prompt:** "Teach me linear and affine type systems. What is substructural logic, how does it give rise to linear and affine types, and how does Rust's ownership system implement affine types?"

---

### Type Inference — Hindley-Milner
- **Difficulty:** advanced
- **What it is:** The algorithm behind Rust's and Haskell's type inference. Unification of type variables.
- **Why it matters:** Understanding type inference helps you predict when the compiler needs annotations and why some annotations are in surprising places.
- **Study prompt:** "Teach me Hindley-Milner type inference. How does Algorithm W work, what is unification, and how does Rust's type inference extend HM to handle traits and lifetimes?"

---

### Substructural Type Systems
- **Difficulty:** expert
- **What it is:** Type systems that restrict how variables can be used: linear, affine, relevant, ordered.
- **Why it matters:** The formal classification system that places Rust alongside linear Haskell and session types. Understanding this gives deep insight into resource management in type systems.
- **Study prompt:** "Teach me the substructural type system hierarchy: linear, affine, relevant, and ordered types. Show where Rust sits in this hierarchy and what each restriction enables."

---

### Effect Systems
- **Difficulty:** expert
- **What it is:** Tracking side effects in the type system. `async`/`await` as an effect. Algebraic effects.
- **Why it matters:** The theoretical framework for understanding async/await, checked exceptions, and capability-based security. The next frontier in type system design.
- **Study prompt:** "Teach me effect systems. How do they track side effects in types, how is async/await an instance of an effect system, and what are algebraic effects and handlers?"

---

### Dependent Types
- **Difficulty:** expert
- **What it is:** Types that depend on values. Coq, Idris. Proofs as programs. Curry-Howard correspondence.
- **Why it matters:** The theoretical endpoint of type system expressiveness. Const generics in Rust are a limited form of dependent types. Understanding this shows where type systems are headed.
- **Study prompt:** "Teach me dependent types and the Curry-Howard correspondence. How do types-as-propositions work, what is a proof term, and how do Rust's const generics relate to dependent types?"

---

## 15. CS: Compiler Internals

### Recursive Descent & Pratt Parsers
- **Difficulty:** advanced
- **What it is:** Top-down parsing. Pratt's elegant operator-precedence technique used in Rust's parser.
- **Why it matters:** The parsing techniques behind most production compilers. Writing a parser for a language is both a practical skill and a deep exercise in recursion and grammar theory.
- **Study prompt:** "Teach me Pratt parsing. How does it handle operator precedence elegantly, implement a Pratt parser for arithmetic expressions in Rust, and how does it compare to recursive descent?"

---

### AST vs CST
- **Difficulty:** intermediate
- **What it is:** Concrete Syntax Tree preserves all tokens. Abstract Syntax Tree discards noise.
- **Why it matters:** The design decision between AST and CST affects everything from error recovery to IDE tooling. Rust-analyzer uses a lossless CST for full-fidelity error recovery.
- **Study prompt:** "Teach me the difference between AST and CST. Why did rust-analyzer choose a lossless CST (rowan), what are the tradeoffs for error recovery and IDE features?"

---

### SSA Form (Static Single Assignment)
- **Difficulty:** advanced
- **What it is:** Each variable assigned exactly once. Enables most compiler optimizations. LLVM IR is SSA.
- **Why it matters:** Understanding SSA explains why LLVM can perform such aggressive optimizations. MIR is also SSA-like. Essential for anyone writing compiler passes.
- **Study prompt:** "Teach me Static Single Assignment form. How does renaming variables into SSA form work, what is a phi node, and what optimizations become trivially easy in SSA form?"

---

### Monomorphization vs Vtable Dispatch
- **Difficulty:** intermediate
- **What it is:** Rust's generics are monomorphized (code duplication, fast). `dyn Trait` uses vtables (one copy, slower).
- **Why it matters:** The core tradeoff in Rust API design. Monomorphization causes binary bloat; vtables cause indirection. Understanding both helps you make the right choice.
- **Study prompt:** "Teach me monomorphization vs vtable dispatch in Rust. What code does the compiler generate for each, what are the binary size and runtime performance tradeoffs, and show profiling evidence."

---

### Register Allocation
- **Difficulty:** expert
- **What it is:** Mapping variables to CPU registers. Graph coloring. Spilling to stack. Critical for performance.
- **Why it matters:** The quality of register allocation determines the efficiency of generated machine code. Understanding it explains why some code patterns are faster than others.
- **Study prompt:** "Teach me register allocation via graph coloring. How does the interference graph work, what is register spilling, and how does LLVM's RA differ from the classic graph-coloring approach?"

---

### Inlining Heuristics
- **Difficulty:** advanced
- **What it is:** When the compiler copies function bodies to call sites. Code size vs speed tradeoff.
- **Why it matters:** Inlining enables all other optimizations by giving the optimizer a larger view. Understanding inlining heuristics explains `#[inline]`, `#[inline(always)]`, and LTO.
- **Study prompt:** "Teach me compiler inlining heuristics. What factors determine whether a function is inlined, what do #[inline], #[inline(always)], and #[inline(never)] do, and how does LTO change inlining?"

---

### Link-Time Optimization (LTO)
- **Difficulty:** advanced
- **What it is:** Optimizations across compilation unit boundaries. Enables inlining across crates.
- **Why it matters:** Without LTO, calls across crate boundaries cannot be inlined. Enabling LTO can significantly improve performance of Rust programs with many small crates.
- **Study prompt:** "Teach me LTO in Rust. How does LLVM LTO work, what is the difference between thin LTO and full LTO, and when does it give measurable performance improvements?"

---

### MIR (Mid-level Intermediate Representation)
- **Difficulty:** advanced
- **What it is:** Rust's CFG-based IR between HIR and LLVM IR. Where borrow checking happens.
- **Why it matters:** Understanding MIR makes borrow checker errors more interpretable. MIR is also where const evaluation, coverage instrumentation, and many optimizations occur.
- **Study prompt:** "Teach me Rust's MIR. What does it look like, why is it a CFG instead of an AST, what is a basic block, and why does borrow checking happen on MIR rather than the AST?"

---

### Panic Unwinding vs Abort
- **Difficulty:** intermediate
- **What it is:** Two panic strategies. Unwinding runs `Drop` impls and is catchable. Abort terminates immediately.
- **Why it matters:** Choosing `panic = "abort"` in release builds eliminates unwinding code, reducing binary size and improving performance. Essential for embedded targets.
- **Study prompt:** "Teach me Rust's panic strategies. How does stack unwinding work, what is the runtime cost, when should I use panic=abort, and how does this interact with FFI?"

---

## 16. CS: OS & Systems

### System Calls and the Syscall Interface
- **Difficulty:** advanced
- **What it is:** How user-space code enters the kernel. `int 0x80`, `syscall` instruction, vDSO optimization.
- **Why it matters:** Every I/O operation, thread creation, and memory allocation ultimately invokes the kernel. Understanding the overhead helps you decide when to batch operations.
- **Study prompt:** "Teach me the syscall interface on Linux x86-64. How does the syscall instruction work, what is the overhead of a syscall, and how does vDSO eliminate that overhead for common calls?"

---

### Page Faults & Demand Paging
- **Difficulty:** advanced
- **What it is:** Pages allocated lazily. Major vs minor faults. How `malloc` doesn't immediately use RAM.
- **Why it matters:** Explains why allocating a large Vec doesn't immediately consume memory, why first access is slow, and how to pre-fault memory for latency-sensitive code.
- **Study prompt:** "Teach me demand paging and page faults. What is the difference between a major and minor page fault, how does Linux implement lazy allocation, and how do I pre-fault pages in Rust?"

---

### epoll / kqueue (Event-Driven I/O)
- **Difficulty:** advanced
- **What it is:** The OS mechanism behind async I/O runtimes. Level-triggered vs edge-triggered.
- **Why it matters:** The foundation of every async runtime including Tokio. Understanding `epoll` explains what happens when you `.await` a network read.
- **Study prompt:** "Teach me epoll on Linux. How does it differ from select and poll, what is the difference between level-triggered and edge-triggered modes, and how does Tokio use epoll under the hood?"

---

### `io_uring`
- **Difficulty:** expert
- **What it is:** Linux's newest async I/O interface. Submission/completion ring buffers. Near-zero syscall overhead.
- **Why it matters:** The future of high-performance I/O on Linux. `io_uring` can achieve orders-of-magnitude more I/O operations per second than epoll for certain workloads.
- **Study prompt:** "Teach me io_uring. How do the submission and completion ring buffers work, how does it minimize syscall overhead, and what Rust crates (tokio-uring, glommio) use it?"

---

### Zero-Copy I/O (`sendfile`, `splice`)
- **Difficulty:** advanced
- **What it is:** Moving data between file descriptors without copying to user space. Network performance.
- **Why it matters:** Eliminating the kernel→userspace→kernel copy loop can double throughput for file serving workloads. The mechanism behind high-performance web servers.
- **Study prompt:** "Teach me zero-copy I/O. How does sendfile work, what copies does it eliminate, what is splice, and how do I use these techniques from Rust?"

---

### Signal Handling in Rust
- **Difficulty:** advanced
- **What it is:** How Unix signals interact with Rust's runtime. Why signals and threads are dangerous together.
- **Why it matters:** Incorrect signal handling is one of the most subtle sources of bugs in systems programs. Very few functions are safe to call from a signal handler.
- **Study prompt:** "Teach me Unix signal handling in Rust. What is async-signal-safety, why is signal handling with threads dangerous, and how does the signal-hook crate make this safe?"

---

### File System Internals (inodes, extents)
- **Difficulty:** advanced
- **What it is:** How filesystems represent file metadata and data. B-trees in modern filesystems.
- **Why it matters:** Understanding filesystem internals explains why rename is atomic, why `fsync` is expensive, and why large directories are slow in some filesystems.
- **Study prompt:** "Teach me filesystem internals. What is an inode, how do extents improve on block lists, how does ext4 use a B-tree for large directories, and what are the durability guarantees of common operations?"

---

## Study Progress Tracker

Use this table to track your progress through the curriculum.

| Category | Total | Foundational | Intermediate | Advanced | Expert |
|---|---|---|---|---|---|
| Rust: Type System | 18 | 0 | 4 | 9 | 5 |
| Rust: Memory & Ownership | 12 | 2 | 1 | 7 | 2 |
| Rust: Interior Mutability | 8 | 0 | 4 | 3 | 1 |
| Rust: Traits & Generics | 14 | 3 | 7 | 3 | 1 |
| Rust: Closures | 4 | 0 | 3 | 1 | 0 |
| Rust: Async & Concurrency | 9 | 0 | 2 | 3 | 4 |
| Rust: Unsafe | 9 | 0 | 0 | 6 | 3 |
| Rust: Patterns & Idioms | 10 | 2 | 3 | 5 | 0 |
| Rust: Macros | 6 | 0 | 1 | 4 | 1 |
| CS: Data Structures | 16 | 0 | 3 | 7 | 6 |
| CS: Algorithms | 20 | 1 | 3 | 9 | 7 |
| CS: Memory & Architecture | 11 | 0 | 2 | 7 | 2 |
| CS: Concurrency Internals | 6 | 0 | 1 | 1 | 4 |
| CS: Type Theory | 9 | 0 | 2 | 3 | 4 |
| CS: Compiler Internals | 9 | 0 | 2 | 5 | 2 |
| CS: OS & Systems | 7 | 0 | 0 | 6 | 1 |
| **Total** | **168** | **8** | **38** | **79** | **43** |

---

*Generated for systematic deep mastery of Rust and CS fundamentals.*
*Each "Study prompt" field is a ready-to-use message for a full in-depth lesson.*