Now let me build this comprehensive guide. This is a deep compiler-level topic — we'll go from zero to expert.

---

# 📖 The Complete Guide to Function Inlining
### *From Call Stack Mechanics → Compiler Internals → Rust-Specific Mastery*

---

## 🧠 Mental Model Before Everything

> **Inlining is the compiler's way of saying: "I trust this function enough to copy-paste its body directly into every place it's called — and throw away the call itself."**

To understand *why* this matters, you must first understand what a function call *actually costs*.

---

## PART 1 — What Is a Function Call, Really?

### 1.1 The Problem: Every Function Call Has a Tax

When you write:

```rust
fn add(a: i32, b: i32) -> i32 {
    a + b
}

fn main() {
    let result = add(3, 5);
}
```

You assume `add(3, 5)` just runs `a + b`. But at the **machine code level**, a function call is a carefully orchestrated sequence of CPU instructions. There's a hidden tax.

Let's look at what the CPU actually does:

---

### 1.2 The Call Stack — A Visual Foundation

Before understanding inlining, you must understand the **call stack**.

```
┌─────────────────────────────────────────────────────────────────┐
│                     MEMORY LAYOUT                               │
│                                                                 │
│   HIGH ADDRESS                                                  │
│   ┌─────────────────────────────┐                               │
│   │  STACK (grows downward ↓)   │                               │
│   │                             │                               │
│   │  ┌─────────────────────┐    │                               │
│   │  │   main() frame      │    │                               │
│   │  │   result: ???       │    │                               │
│   │  │   return address    │    │  ← "come back here after add" │
│   │  ├─────────────────────┤    │                               │
│   │  │   add() frame       │    │  ← pushed when add() called   │
│   │  │   a: 3              │    │                               │
│   │  │   b: 5              │    │                               │
│   │  │   (local vars)      │    │                               │
│   │  └─────────────────────┘    │                               │
│   │         ↑ SP (stack ptr)    │                               │
│   │                             │                               │
│   │         (free stack space)  │                               │
│   │                             │                               │
│   └─────────────────────────────┘                               │
│                                                                 │
│   LOW ADDRESS                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

### 1.3 The Exact CPU Cost of a Function Call

Let's trace `add(3, 5)` at the assembly level (x86-64):

```
CALLER (main):
─────────────────────────────────────────────────
  mov  edi, 3          ; put first argument (a=3) into register
  mov  esi, 5          ; put second argument (b=5) into register
  call add             ; PUSH return address onto stack
                       ; JUMP to add's address

   ↓ CPU jumps to add()

CALLEE (add):
─────────────────────────────────────────────────
  push rbp             ; save caller's base pointer
  mov  rbp, rsp        ; set up our own stack frame
  mov  DWORD [rbp-4], edi  ; store a onto stack
  mov  DWORD [rbp-8], esi  ; store b onto stack
  mov  eax, [rbp-4]    ; load a into return register
  add  eax, [rbp-8]    ; add b to it
  pop  rbp             ; restore caller's base pointer
  ret                  ; POP return address, JUMP back to caller

   ↑ CPU jumps back to main

CALLER (main) resumes:
─────────────────────────────────────────────────
  mov  [result], eax   ; store return value
```

Count the overhead instructions just to call `add`:
- `call` = push return address + jump (2 ops)
- `push rbp` / `pop rbp` = save/restore frame pointer (2 ops)
- `mov` for each argument (2 ops)
- `ret` = pop + jump (2 ops)
- Stack memory reads/writes for locals (2+ ops)

**For a function that does ONE ADD instruction, we're paying 10+ overhead instructions.** That's a 10x tax on a trivial operation.

---

### 1.4 The Hidden Costs Beyond Instruction Count

The overhead isn't just instruction count. Modern CPUs have hardware mechanisms that suffer from function calls:

```
┌───────────────────────────────────────────────────────────────┐
│              HIDDEN HARDWARE COSTS                            │
├──────────────────────────────────┬────────────────────────────┤
│ Cost                             │ Why it hurts               │
├──────────────────────────────────┼────────────────────────────┤
│ Branch predictor pollution       │ CPU tries to predict the   │
│                                  │ call target; every new     │
│                                  │ call confuses it           │
├──────────────────────────────────┼────────────────────────────┤
│ Instruction cache (I-cache) miss │ CPU must fetch the         │
│                                  │ function's code from a     │
│                                  │ different memory location  │
├──────────────────────────────────┼────────────────────────────┤
│ Register spilling                │ Caller must save registers │
│                                  │ it was using; callee might │
│                                  │ clobber them               │
├──────────────────────────────────┼────────────────────────────┤
│ Stack frame allocation           │ rsp adjustment, memory     │
│                                  │ writes for saved state     │
├──────────────────────────────────┼────────────────────────────┤
│ Optimizer blindness              │ The compiler can't         │
│                                  │ optimize ACROSS a call     │
│                                  │ boundary it can't see into │
└──────────────────────────────────┴────────────────────────────┘
```

The last one — **optimizer blindness** — is often the biggest cost. When the compiler can't see inside a function, it can't:
- Eliminate redundant computations
- Simplify constant expressions
- Vectorize loops
- Remove dead code

---

## PART 2 — What Inlining Actually Does

### 2.1 The Core Transformation

Inlining replaces a function call with the function's body, substituting arguments for parameters.

**Before inlining:**
```rust
fn add(a: i32, b: i32) -> i32 {
    a + b
}

fn main() {
    let result = add(3, 5);
    println!("{result}");
}
```

**After inlining (conceptual — what the compiler internally produces):**
```rust
fn main() {
    let result = 3 + 5;   // ← add()'s body, with a=3, b=5 substituted
    println!("{result}");
}
```

Now the compiler sees `3 + 5` directly. It immediately **constant-folds** this:
```rust
fn main() {
    let result = 8;        // ← constant folding: 3+5 = 8, computed at compile time
    println!("{result}");
}
```

The final assembly for `println!("{result}")` will likely have the literal `8` embedded — **zero arithmetic happens at runtime**.

---

### 2.2 The Full Chain of Optimizations Inlining Unlocks

Inlining is rarely just "remove the call overhead." It's a **gate** that unlocks a cascade of further optimizations:

```
INLINING OCCURS
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│  OPTIMIZATIONS NOW POSSIBLE (weren't before)                 │
│                                                              │
│  Constant Folding                                            │
│  ├── If arguments are constants, compute result at           │
│  │   compile time                                            │
│  │   add(3, 5) → 8                                          │
│  │                                                            │
│  Dead Code Elimination (DCE)                                  │
│  ├── After inlining, some branches may become                │
│  │   provably unreachable                                    │
│  │   if (x > 0) { ... } → x is always 5 → always true      │
│  │   → else branch deleted                                   │
│  │                                                            │
│  Loop Unrolling                                               │
│  ├── If inlined function contains a loop with now-known      │
│  │   bounds, compiler can unroll it                          │
│  │                                                            │
│  Auto-Vectorization (SIMD)                                    │
│  ├── Inlined loops over arrays can be converted to           │
│  │   SIMD instructions (process 4/8/16 elements at once)    │
│  │                                                            │
│  Register Allocation                                          │
│  ├── With no call boundary, all values stay in CPU           │
│  │   registers — no memory spills                            │
│  │                                                            │
│  Value Range Propagation                                      │
│  └── Compiler can track exact range of values, enabling      │
│      more aggressive optimizations throughout                │
└──────────────────────────────────────────────────────────────┘
```

This cascade is why inlining is called **the mother of all optimizations** in compiler literature.

---

## PART 3 — Inlining in Rust Specifically

### 3.1 Where Rust Does Inlining

Rust uses **LLVM** as its backend. The inlining decision happens at the LLVM IR level, after Rust's own compilation phases. But Rust gives you attributes to guide this decision.

```
RUST SOURCE CODE
       │
       ▼ rustc frontend
RUST MIR (Mid-level Intermediate Representation)
       │
       ▼ monomorphization
LLVM IR (LLVM Intermediate Representation)
       │
       ▼ LLVM optimization passes (THIS IS WHERE INLINING HAPPENS)
       │   ├── InlinerPass
       │   ├── AlwaysInlinerPass
       │   └── PartialInliningPass
       │
       ▼
MACHINE CODE
```

---

### 3.2 The Three Inlining Attributes

Rust gives you three attributes to control inlining:

#### `#[inline]` — Hint to inline

```rust
#[inline]
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

This is a **suggestion** to the compiler. It says: "Consider inlining this, it's probably a good idea." The compiler may still refuse if it calculates inlining would be harmful (e.g., the function is very large and called many times — binary bloat).

> **Crucially**: Without `#[inline]`, a function defined in a **different crate** (library) **cannot be inlined** into your crate, even if the compiler wants to. The `#[inline]` attribute is what makes the function's body available to other crates for inlining.

---

#### `#[inline(always)]` — Forceful inline

```rust
#[inline(always)]
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

This **forces** the compiler to always inline this function, regardless of its size or how many times it's called. This overrides LLVM's cost model.

Use with caution:
```
WARNING: #[inline(always)] can increase binary size dramatically
if the function is large and called in many places.

Example:
  Function body: 50 instructions
  Called in 100 places
  Without inline: 50 instructions + 100 call sequences (~800 inst) = ~850 instructions
  With #[inline(always)]: 50 × 100 = 5,000 instructions

  5000 vs 850 — that's almost 6× binary size increase for that code.
```

---

#### `#[inline(never)]` — Prevent inlining

```rust
#[inline(never)]
fn large_error_handler(msg: &str) -> ! {
    panic!("{msg}");
}
```

Prevents inlining even when LLVM wants to inline it. Use cases:
- **Error/panic paths**: You never care about the performance of `panic`, but inlining it into your hot path bloats its instruction cache footprint
- **Profiling**: Inlined functions disappear from profiler call stacks (they have no call frame). `#[inline(never)]` makes them visible again
- **Debugging**: Inlined functions are harder to set breakpoints on

---

### 3.3 Default Inlining Behavior (Without Attributes)

```
SAME CRATE:
  ┌─────────────────────────────────────────────────────┐
  │  Functions WITHIN the same crate                    │
  │  → LLVM freely inlines at -O2/-O3                   │
  │  → No attribute needed for same-crate functions     │
  │  → LLVM's cost model decides automatically          │
  └─────────────────────────────────────────────────────┘

DIFFERENT CRATE (library → binary):
  ┌─────────────────────────────────────────────────────┐
  │  Functions from EXTERNAL crates                     │
  │  → Cannot be inlined WITHOUT #[inline]              │
  │  → Reason: Rust compiles crates independently       │
  │    The binary crate gets compiled OBJECT files      │
  │    from library crates, not source code             │
  │  → #[inline] makes the body available in            │
  │    the .rlib (Rust library file)                    │
  └─────────────────────────────────────────────────────┘
```

This is why every `Iterator` adapter (`.map()`, `.filter()`, etc.) in the standard library has `#[inline]` on it — they need to be inline-able into your crate for the zero-cost abstraction promise to hold.

---

### 3.4 Verifying Inlining: Cargo-ASM

You can actually **see** whether a function was inlined using `cargo-asm`:

```bash
cargo install cargo-show-asm
cargo asm --lib --rust  # shows generated assembly annotated with source
```

Or use **Compiler Explorer** (godbolt.org) with Rust. Compile this:

```rust
#[inline]
pub fn add(a: i32, b: i32) -> i32 { a + b }

pub fn caller() -> i32 { add(3, 5) }
```

With `-C opt-level=3`, you'll see `caller()` compiled to literally:
```asm
caller:
    mov eax, 8      ; just the constant 8 — no call, no arithmetic!
    ret
```

`add` doesn't exist in the output at all. It was inlined and then constant-folded away.

---

## PART 4 — Inlining and Monomorphization (The Connection)

### 4.1 Why Monomorphization Makes Inlining Powerful

Recall from the previous guide: monomorphization creates **concrete copies** of generic functions. This is the prerequisite for aggressive inlining.

Consider:
```rust
fn transform<T, F: Fn(T) -> T>(x: T, f: F) -> T {
    f(x)
}

let result = transform(5i32, |x| x * 2);
```

**Without monomorphization** (hypothetical):
- `f` is a `dyn Fn(T) -> T` — called through a vtable
- The compiler sees `CALL [vtable + offset]`
- It has no idea what function is behind that pointer
- **Inlining is impossible**

**With monomorphization** (what Rust actually does):
- The compiler generates `transform_i32_Closure123` with `F = Closure123` (a concrete struct)
- It can see exactly what `f` is
- It can substitute the closure body directly
- The result after inlining + optimization:

```rust
// What the compiler reduces this to:
let result = 5i32 * 2;  // → 10 at compile time
```

```
MONOMORPHIZATION → STATIC DISPATCH → INLINING → CONSTANT FOLDING

This is the chain that makes Rust's "zero-cost abstraction" claim true.
Without any step in this chain, the claim falls apart.
```

---

### 4.2 Dynamic Dispatch Blocks Inlining

```rust
// Static dispatch — inlinable
fn process(f: impl Fn(i32) -> i32) -> i32 {
    f(42)  // compiler knows exactly what f is → can inline
}

// Dynamic dispatch — NOT inlinable
fn process_dyn(f: &dyn Fn(i32) -> i32) -> i32 {
    f(42)  // compiler has NO idea which function f points to → cannot inline
}
```

This is the fundamental tradeoff between `impl Trait` and `dyn Trait`:

```
impl Trait / T: Trait          dyn Trait
──────────────────────────     ──────────────────────────
Static dispatch                Dynamic dispatch
Monomorphized                  Single function, vtable
Inlinable                      Not inlinable
Larger binary                  Smaller binary
Faster                         Slightly slower (1 indirect call)
```

---

## PART 5 — The Iterator Pipeline and Inlining

### 5.1 How `.map().filter().collect()` Becomes a Single Loop

Recall this from the previous guide:
```rust
items.iter().cloned().map(|x| x * 2).filter(|x| x > 5).collect::<Vec<_>>()
```

The type stack is:
```
Filter<Map<Cloned<Iter<i32>>, Closure1>, Closure2>
```

After monomorphization, the compiler has:
- `Iter<i32>::next()` — concrete
- `Cloned<Iter<i32>>::next()` — concrete, calls `i32::clone()`
- `Map<..., Closure1>::next()` — concrete, calls `Closure1::call()`
- `Filter<..., Closure2>::next()` — concrete, calls `Closure2::call()`
- `Vec::from_iter(...)` — concrete

Every single one of these has `#[inline]` in std. LLVM inlines them all. After inlining:

```
BEFORE (logical structure):            AFTER (what LLVM actually executes):
─────────────────────────────          ─────────────────────────────────────

collect()                              let mut result = Vec::new();
  calls Filter::next()                 let mut i = 0;
    calls Map::next()                  while i < items.len() {
      calls Cloned::next()                 let x = items[i];    // iter+clone
        calls Iter::next()                 let y = x * 2;       // map
          returns &items[i]                if y > 5 {           // filter
        calls x.clone()                        result.push(y);  // collect
        returns items[i]                   }
      applies |x| x * 2                   i += 1;
      returns x * 2                   }
    applies |x| x > 5
    returns Some/None
  pushes to result
```

This is a **single tight loop** — exactly as if you'd written it by hand. No intermediate allocations. No virtual calls. No extra function call overhead.

This is **the definitive proof** of why Rust's iterator chain is zero-cost.

---

### 5.2 The Inlining Decision Process (LLVM's Cost Model)

LLVM doesn't inline blindly. It uses a **cost model** to decide:

```
FOR EACH FUNCTION CALL IN THE IR:

1. Calculate the "inline cost" of the callee
   ├── Each instruction has a cost (add=1, load=2, branch=4, etc.)
   ├── Function with 5 instructions: low cost → likely inlined
   └── Function with 200 instructions: high cost → likely NOT inlined

2. Calculate the "threshold" for inlining
   ├── Base threshold = 225 (LLVM default at -O2)
   ├── Boosted if: caller is hot (frequently executed)
   ├── Boosted if: there are constant arguments (more optimization potential)
   ├── Boosted if: function is only called once
   └── Reduced if: binary size limit is approaching

3. If cost < threshold → INLINE
   If cost ≥ threshold → LEAVE AS CALL

4. Special cases:
   ├── #[inline(always)] → bypass cost model, always inline
   ├── #[inline(never)] → bypass cost model, never inline
   └── Single-use function → almost always inlined regardless of size
```

---

## PART 6 — Inlining in Practice: Code Patterns

### 6.1 Small Helper Functions — Always Annotate

```rust
// Without #[inline]: works within same crate, but if this is in a library,
// users' code CANNOT benefit from inlining
fn square(x: f64) -> f64 { x * x }

// With #[inline]: works across crate boundaries
#[inline]
fn square(x: f64) -> f64 { x * x }

// With #[inline(always)]: forces inlining regardless of context
// Appropriate here because the function is TINY (1 instruction)
#[inline(always)]
fn square(x: f64) -> f64 { x * x }
```

---

### 6.2 The Getter Pattern (Very Common in Rust APIs)

```rust
pub struct Buffer {
    data: Vec<u8>,
    len: usize,
}

impl Buffer {
    // This MUST be #[inline] if in a library
    // Without it, the "zero overhead" promise of data encapsulation breaks
    #[inline]
    pub fn len(&self) -> usize {
        self.len
    }

    #[inline]
    pub fn is_empty(&self) -> bool {
        self.len == 0
    }
}
```

Without `#[inline]`, calling `buf.len()` from external code costs a full function call just to read a field. With `#[inline]`, it becomes a single memory load — identical to accessing `buf.len` directly (if it were `pub`).

---

### 6.3 Closures and Inlining

Closures are automatically candidates for inlining in their immediate context, but the mechanism is the same — the closure must be of a **known concrete type** (not `dyn Fn`):

```rust
// This closure is immediately inlined — its type is known
let doubled: Vec<_> = vec![1, 2, 3].iter().map(|x| x * 2).collect();

// This stores the closure as a trait object — NOT inlinable
let f: Box<dyn Fn(i32) -> i32> = Box::new(|x| x * 2);
let y = f(5);  // goes through vtable — no inlining
```

---

### 6.4 Recursive Functions Cannot Be Fully Inlined

```rust
fn factorial(n: u64) -> u64 {
    if n <= 1 { 1 } else { n * factorial(n - 1) }
}
```

You cannot inline `factorial` into itself infinitely. LLVM handles this by doing **partial inlining** — inlining one or two recursive levels — but deep recursion is never fully inlined.

This is one reason recursive algorithms are sometimes slower than iterative equivalents in performance-critical code.

---

## PART 7 — Link-Time Optimization (LTO)

### 7.1 The Cross-Crate Inlining Problem

```
NORMAL COMPILATION:

  crate A (library)          crate B (your binary)
  ┌─────────────────┐        ┌─────────────────┐
  │ fn foo() { ... }│        │ use A::foo;      │
  │   compiled to   │──────▶ │ foo();           │
  │   object file   │        │   ← compiled     │
  └─────────────────┘        │     separately   │
                             └─────────────────┘

Problem: When compiling crate B, the compiler already
compiled crate A separately. It can only inline A's
functions that have #[inline] (body available).
```

### 7.2 What LTO Solves

```
WITH LTO (Link-Time Optimization):

  crate A (LLVM IR)          crate B (LLVM IR)
  ┌─────────────────┐        ┌─────────────────┐
  │ fn foo() { ... }│        │ foo();           │
  │   kept as IR,   │        │                 │
  │   not compiled  │        │                 │
  └────────┬────────┘        └────────┬────────┘
           │                          │
           └──────────┬───────────────┘
                      ▼
             COMBINED LLVM IR
             ┌─────────────────────────────┐
             │ All functions visible       │
             │ LLVM can inline ANY         │
             │ function across crates      │
             │ Full optimization possible  │
             └─────────────────────────────┘
```

Enable in Cargo.toml:
```toml
[profile.release]
lto = true           # "fat" LTO — maximum inlining, slow compile
# OR
lto = "thin"         # thin LTO — most of the benefit, faster compile
```

LTO is the **most powerful form of inlining** in Rust. It removes the crate boundary as an optimization barrier entirely.

---

## PART 8 — Inlining's Tradeoffs (The Full Picture)

### 8.1 The Binary Size Problem

```
SCENARIO: A function `render_widget()` is 300 instructions.
          It's called from 50 different places.

WITHOUT inlining:
  Code size = 300 (function body) + 50 × ~10 (call overhead) = 800 instructions
  Every call: i-cache loads function from ONE location

WITH inlining:
  Code size = 50 × 300 = 15,000 instructions
  Every call: its own copy of the code

RATIO: 15,000 vs 800 = 18.75× larger!
```

A massively larger binary has its own performance cost:
- More of the instruction cache is consumed
- More cache misses on the first execution of each call site
- Longer program load time
- More pages to page-fault in

This is the **inlining paradox**: inlining can make individual functions faster while making the overall program slower due to cache pressure.

---

### 8.2 The Icache (Instruction Cache) Effect

```
CPU INSTRUCTION CACHE (L1I): typically 32KB

Without excessive inlining:
  ┌──────────────────────────────────────────────┐
  │  render_widget() = 300 inst ≈ 1.2KB          │
  │  Fits in L1I cache                            │
  │  All 50 call sites share ONE cached copy      │
  │  First miss: 1 cache load                     │
  │  Subsequent calls: cache HIT — free!          │
  └──────────────────────────────────────────────┘

With inlining at every call site:
  ┌──────────────────────────────────────────────┐
  │  50 copies × 300 inst × 4 bytes = 60KB       │
  │  Exceeds L1I cache entirely!                  │
  │  Each call site: its own cold cache miss      │
  │  50 separate cache loads — all cold           │
  └──────────────────────────────────────────────┘
```

Large, frequently-called functions should **never** be inlined. The cache miss cost eclipses the call overhead savings.

---

### 8.3 The "Right Size" Heuristic

```
FUNCTION SIZE    CALL FREQUENCY    RECOMMENDATION
─────────────────────────────────────────────────────────────
Tiny (1-5 inst)  Any               Always inline (#[inline(always)])
Small (5-20 inst) High              Inline (#[inline])
Small (5-20 inst) Low               Probably inline (#[inline])
Medium (20-100)  High              Inline if frequently constant-folded
Medium (20-100)  Low               Likely don't inline
Large (100+)     Any               Generally don't inline (let LLVM decide)
Error/panic paths Any              #[inline(never)] — never on hot path
```

---

## PART 9 — Inlining Across Languages

### 9.1 C/C++

```c
// C: inline keyword (just a hint)
inline int add(int a, int b) { return a + b; }

// C++: templates are always monomorphized (like Rust generics)
template<typename T>
T add(T a, T b) { return a + b; }

// C++20: [[likely]] / [[unlikely]] help inlining decisions for branches
if ([[likely]] x > 0) { ... }
```

In C/C++, the `inline` keyword originally meant "put this function in every translation unit" (header files), not strictly "inline the call." The optimizer still decides the actual inlining. Modern C++ uses `[[always_inline]]` for forced inlining (like Rust's `#[inline(always)]`).

---

### 9.2 Go

Go deliberately limits inlining. The Go compiler inlines only **"leaf functions"** (functions that don't call other functions) up to a certain instruction budget (~80 nodes in Go's AST).

```go
// Go: this is inlined (simple, leaf function)
func add(a, b int) int { return a + b }

// Go: this is NOT inlined (too complex, calls other functions)
func processItems(items []int) []int {
    result := make([]int, 0, len(items))
    for _, v := range items {
        result = append(result, transform(v))  // calls transform → not a leaf
    }
    return result
}
```

Go's conservative inlining is a deliberate tradeoff for faster compilation and more predictable binary sizes. Go's iterators (using closures) are therefore not zero-cost the way Rust's are.

---

### 9.3 Python

Python has no inlining in the traditional sense. Every function call goes through:
- `CALL_FUNCTION` bytecode instruction
- Python's call stack machinery
- Dynamic type dispatch on every argument
- Reference counting for every object passed

PyPy (Python JIT) does inline — it uses tracing JIT compilation to inline frequently-called functions at runtime, observed after execution profiling.

---

### 9.4 Java

Java's JIT (JVM HotSpot) inlines aggressively **at runtime**, after the JVM detects "hot" methods (called ≥10,000 times by default). This is **profile-guided inlining** — it inlines what's actually hot in your specific workload.

The JVM can even inline **virtual (polymorphic) calls** if it observes that only one concrete type is ever used at a call site (speculative inlining). If a second type appears later, it **de-optimizes** (re-compiles that section without inlining).

Rust does all this at compile time, statically. Java does it at runtime, dynamically. Both approaches work — Rust's is more predictable; Java's adapts to the actual workload.

---

## PART 10 — Profile-Guided Optimization (PGO)

### 10.1 The Problem With Static Inlining Decisions

LLVM's cost model makes decisions based on **static analysis** — it estimates which functions are "probably" called often. But it doesn't know your actual workload.

```
EXAMPLE:
  fn handle_request(req: Request) {
      match req.kind {
          RequestKind::Common => handle_common(req),   // called 99.9% of time
          RequestKind::Rare   => handle_rare(req),      // called 0.1% of time
      }
  }

Static analysis: both branches look equally likely
LLVM: treats both handle_common and handle_rare with equal inlining priority

Reality: should aggressively inline handle_common, not handle_rare
```

### 10.2 PGO: Train-Then-Compile

```
PGO WORKFLOW:

Step 1: INSTRUMENTATION BUILD
  cargo rustc -- -C profile-generate=/tmp/pgo-data

Step 2: RUN with representative workload
  ./my_program --real-workload
  (profiling data collected → /tmp/pgo-data/*.profraw)

Step 3: MERGE profile data
  llvm-profdata merge -output=/tmp/merged.profdata /tmp/pgo-data/*.profraw

Step 4: OPTIMIZED BUILD using profile data
  cargo rustc -- -C profile-use=/tmp/merged.profdata

RESULT:
  LLVM now knows EXACTLY which functions are hot.
  Inlining decisions are made based on REAL execution frequency.
  Typically 10-30% performance improvement for real workloads.
```

PGO is used by Firefox, Chrome, Rust's own compiler, and most performance-critical systems. It's the gold standard for production performance tuning.

---

## PART 11 — Practical Debugging: Seeing Inlining in Action

### 11.1 Using `cargo-show-asm`

```bash
cargo install cargo-show-asm

# See assembly for a specific function
cargo asm --release 'my_crate::my_function'

# See with source interleaved
cargo asm --release --rust 'my_crate::my_function'
```

If `my_function` calls `helper()` and `helper` was inlined, you'll see `helper`'s instructions appear directly in `my_function`'s assembly — `helper` won't appear as a separate function at all.

### 11.2 Using Compiler Explorer (godbolt.org)

1. Go to godbolt.org
2. Select "Rust"
3. Set compiler flags: `-C opt-level=3`
4. Paste:

```rust
#[inline]
pub fn square(x: i64) -> i64 { x * x }

pub fn sum_of_squares(a: i64, b: i64) -> i64 {
    square(a) + square(b)
}
```

Assembly output:
```asm
sum_of_squares:
    imul rdi, rdi       ; a * a  (square inlined — no call!)
    imul rsi, rsi       ; b * b  (square inlined — no call!)
    lea rax, [rdi+rsi]  ; add them
    ret
```

No `call square` anywhere. Both instances are inlined.

### 11.3 Using `perf` (Linux) to Verify Inlining

```bash
# Profile your binary
perf record -g ./my_program

# View call graph
perf report --stdio

# If function is inlined: it appears WITHIN its caller in the call graph
# If function is NOT inlined: it appears as a separate entry with its own % time
```

---

## PART 12 — Anti-Patterns and When NOT to Inline

### 12.1 Never Force-Inline Error/Panic Paths

```rust
// BAD: panic path inlined into hot code
#[inline(always)]
fn check_bounds(i: usize, len: usize) {
    if i >= len {
        panic!("index out of bounds: {} >= {}", i, len);
    }
}

// GOOD: the check is inlined, but the panic path is not
#[inline]
fn check_bounds(i: usize, len: usize) {
    if i >= len {
        panic_out_of_bounds(i, len);  // cold path called, not inlined
    }
}

#[inline(never)]  // panic handler is large and cold — never inline it
#[cold]           // additionally marks this as unlikely to execute
fn panic_out_of_bounds(i: usize, len: usize) -> ! {
    panic!("index out of bounds: {} >= {}", i, len);
}
```

The `#[cold]` attribute tells LLVM this function is rarely called, further discouraging branch prediction and inlining.

---

### 12.2 Recursive Functions (Never Use `#[inline(always)]`)

```rust
// CATASTROPHIC — will not compile or will loop forever trying to inline
#[inline(always)]  // ← NEVER do this on recursive functions
fn factorial(n: u64) -> u64 {
    if n <= 1 { 1 } else { n * factorial(n - 1) }
}
```

The compiler will detect this and either refuse, or produce a warning. LLVM handles recursive inlining by inlining a fixed number of levels, but `#[inline(always)]` creates an infinite expansion request.

---

### 12.3 Very Large Functions

```rust
// WRONG: force-inlining a 500-line parsing function
#[inline(always)]  // ← don't do this
fn parse_complex_json(input: &str) -> JsonValue {
    // 500 lines of complex parsing logic
    // ...
}
```

This would inline 500 lines into every call site, bloating the binary massively and destroying icache efficiency.

---

## PART 13 — The Compiler's Full View (Assembly-Level Walkthrough)

Let's trace the complete lifecycle of inlining our original function from the attached document:

```rust
fn complex_function<T, U, F>(items: &[T], transform: F) -> Vec<U>
where
    T: Clone,
    F: Fn(T) -> U,
{
    items.iter().cloned().map(transform).collect()
}

// Called as:
let v = vec![1i32, 2, 3];
let result = complex_function(&v, |x| x * 2);
```

**Step 1 — After Monomorphization:**
```rust
fn complex_function_i32_i32_Closure0(
    items: &[i32],
    transform: Closure0,  // |x| x * 2
) -> Vec<i32> {
    items.iter().cloned().map(transform).collect()
}
```

**Step 2 — After Inlining Iterator Adapters (LLVM level):**
```rust
// Logical equivalent after all iterator .next() methods are inlined:
fn complex_function_i32_i32_Closure0(items: &[i32]) -> Vec<i32> {
    let mut result = Vec::with_capacity(items.len());
    for &item in items {
        result.push(item * 2);  // clone (copy) + transform, both inlined
    }
    result
}
```

**Step 3 — After SIMD Vectorization (if loop body is simple enough):**
```asm
; Process 4 elements at once using SSE2 instructions
vmovdqu  xmm0, [rsi]       ; load 4 i32s from items
vpslld   xmm0, xmm0, 1     ; left shift by 1 = multiply by 2 (×4 elements)
vmovdqu  [rdi], xmm0        ; store 4 i32s to result
```

Four elements processed per cycle. Without inlining, the vectorizer couldn't see the loop body because it was hidden behind function call boundaries.

---

## Summary: The 12 Core Truths of Inlining

```
┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│  1. A function call is NOT free: return address, register saves,   │
│     stack frame setup, icache miss — all have CPU cost             │
│                                                                    │
│  2. Inlining copies a function's body into its call site,          │
│     eliminating the call overhead entirely                         │
│                                                                    │
│  3. Inlining's main value is unlocking further optimizations:      │
│     constant folding, DCE, vectorization, range propagation        │
│                                                                    │
│  4. Rust's #[inline] makes a function's body available across      │
│     crate boundaries — required for library functions to be        │
│     inlinable in user code                                         │
│                                                                    │
│  5. Monomorphization is the prerequisite for inlining generics:    │
│     static dispatch → known type → visible body → inlinable        │
│                                                                    │
│  6. dyn Trait (dynamic dispatch) permanently blocks inlining       │
│     at that call site                                              │
│                                                                    │
│  7. Iterator chains are zero-cost because EVERY adapter has        │
│     #[inline] and they all get inlined into a single loop          │
│                                                                    │
│  8. More inlining ≠ faster program: binary bloat and icache        │
│     pressure can make overall performance worse                    │
│                                                                    │
│  9. LLVM uses a cost model to decide; #[inline(always)] overrides  │
│     it; #[inline(never)] prevents it; #[cold] hints rarity         │
│                                                                    │
│ 10. LTO (Link-Time Optimization) extends inlining across ALL crate │
│     boundaries — the most powerful form in Rust                    │
│                                                                    │
│ 11. PGO (Profile-Guided Optimization) makes inlining decisions     │
│     based on real execution data — best for production tuning      │
│                                                                    │
│ 12. Error/panic paths, recursive functions, and large functions    │
│     are the three cases where inlining is actively harmful         │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## What to Study Next

```
WHERE YOU ARE NOW:
  ✓ Function call mechanics (stack, registers, return addresses)
  ✓ Inlining: what it is, when it happens, what it unlocks
  ✓ Rust's #[inline], #[inline(always)], #[inline(never)]
  ✓ Monomorphization → static dispatch → inlining chain
  ✓ LTO, PGO, icache effects
  ✓ Iterator pipeline inlining (why it's truly zero-cost)

NEXT STEPS (logical order):

  1. SIMD / Auto-vectorization
     → What inlining enables at the loop level
     → std::simd in Rust (nightly)
     → When LLVM auto-vectorizes vs when you must use intrinsics

  2. Branch Prediction & Likely/Unlikely
     → #[cold], likely!(), unlikely!()
     → How mispredict penalty interacts with inlined code

  3. Cache Architecture (L1/L2/L3)
     → Why cache-friendly data layouts matter as much as inlining
     → Struct-of-arrays vs array-of-structs

  4. Peephole Optimizations & Constant Propagation
     → What LLVM does AFTER inlining (the full optimization chain)

  5. Unsafe and Inlining
     → How inlining interacts with Rust's safety guarantees
     → When inline assembly (#[naked]) is needed
```

Inlining is the cornerstone of all performance optimization in compiled systems languages. Every benchmark you've ever seen comparing Rust to C, or showing "zero-cost abstractions" — those results exist because of the chain you now understand completely: **monomorphization → static dispatch → inlining → optimization cascade → machine code indistinguishable from handwritten C**.