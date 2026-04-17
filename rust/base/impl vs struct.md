## Why Both `struct` and `impl`?

This is a deep question about **Rust's core design philosophy**. Let me break it down from first principles.

---

## The Core Idea: Data vs Behavior are Separate in Rust

In Rust, these two things are **intentionally separated**:

```
struct  →  defines WHAT data exists (shape/fields)
impl    →  defines WHAT the data can DO (behavior/methods)
```

This is **not** the same in all languages. Compare:

```python
# Python: data + behavior fused together in one block
class TreeNode:
    def __init__(self, data):   # data definition
        self.data = data
        self.left = None
        self.right = None
    
    def new(self, data):        # behavior — all inside one class
        ...
```

```rust
// Rust: deliberately SPLIT
struct TreeNode {        // ← ONLY data lives here
    data: i32,
    left: Option<Box<TreeNode>>,
    right: Option<Box<TreeNode>>,
}

impl TreeNode {          // ← ONLY behavior lives here
    fn new(data: i32) -> Self { ... }
}
```

---

## Why Does Rust Force This Separation?

### Reason 1: A Struct is Just a Memory Layout Blueprint

When you write:

```rust
struct TreeNode {
    data: i32,
    left: Option<Box<TreeNode>>,
    right: Option<Box<TreeNode>>,
}
```

Rust sees this as a **pure memory layout description**. It answers only one question:

```
"How many bytes do I need, and what types go where?"
```

```
Memory layout of TreeNode:
┌────────────┬──────────────────────┬──────────────────────┐
│  data: i32 │ left: Option<Box<..>>│right: Option<Box<..>>│
│  (4 bytes) │     (8 bytes ptr)    │    (8 bytes ptr)     │
└────────────┴──────────────────────┴──────────────────────┘
```

**Zero behavior. Zero logic. Just shape.**

A struct has no inherent knowledge of how to construct itself or operate on itself. That's intentional.

---

### Reason 2: `impl` Attaches Behavior — And Can Be Anywhere

This is where it gets powerful. In Rust, you can write `impl TreeNode` **in a completely different file**, or even **multiple times**:

```rust
// file: tree_core.rs
impl TreeNode {
    fn new(data: i32) -> Self { ... }
}

// file: tree_display.rs
impl TreeNode {
    fn print(&self) { ... }   // separate impl block, same struct!
}

// file: tree_search.rs
impl TreeNode {
    fn find(&self, val: i32) -> bool { ... }
}
```

This is **impossible** in Python/Java-style class fusion. Rust lets you **grow behavior modularly** without touching the original struct definition.

---

### Reason 3: The Trait System Requires This Separation

This is the biggest architectural reason. In Rust, you attach **shared interfaces** (called Traits) to structs via `impl`:

```rust
trait Printable {
    fn print(&self);
}

impl Printable for TreeNode {   // ← "TreeNode now IS Printable"
    fn print(&self) {
        println!("{}", self.data);
    }
}
```

If data and behavior were fused, this flexible plugging-in of behaviors would be **structurally impossible**.

```
STRUCT (data shape)
    │
    │   impl Block 1: constructor methods (new, with_children)
    ├──────────────────────────────────────────────────────
    │   impl Block 2: your own methods (search, insert)
    ├──────────────────────────────────────────────────────
    │   impl TraitA for TreeNode  (e.g., Display)
    ├──────────────────────────────────────────────────────
    │   impl TraitB for TreeNode  (e.g., Clone)
    └──────────────────────────────────────────────────────
```

One struct, many independent behavior layers. **All opt-in, all separate.**

---

### Reason 4: `new()` is Not Magic — It's Just a Convention

Notice that in your code:

```rust
impl TreeNode {
    fn new(data: i32) -> Self {   // ← "Self" means TreeNode
        TreeNode {
            data,
            left: None,
            right: None,
        }
    }
}
```

`new()` is **not a constructor** like in C++ or Java. It is just a **regular static function** that returns `Self`. Rust has no language-level constructor. You named it `new` by convention, but you could call it `create` or `build` — Rust doesn't care.

This reinforces the point: the struct itself **cannot construct itself**. Someone has to write that logic separately in `impl`.

---

## The Mental Model to Internalize

Think of it like **engineering blueprints vs operating manuals**:

```
struct TreeNode   =   Blueprint (dimensions, materials, shape)
impl TreeNode     =   Operating Manual (how to build it, use it, maintain it)
```

A blueprint doesn't tell you how to assemble. The manual doesn't define shape. They are **separate concerns** and separating them gives you flexibility, composability, and clarity.

---

## Your Specific Question Answered Directly

> "struct itself providing meaning right?"

The struct provides **structural meaning** (what data exists). But:

- **Who creates a `TreeNode`?** → `impl` (via `new`)
- **Who traverses it?** → `impl` or standalone functions
- **Who formats it for printing?** → `impl Display for TreeNode`

The struct is **inert data**. It cannot act on itself. `impl` is the **actor**.

---

## Cognitive Principle: Separation of Concerns

This maps to a mental model called **Separation of Concerns** — one of the most powerful ideas in systems thinking. By keeping data and behavior separate:

1. You can **reason about memory** without thinking about logic
2. You can **add behavior later** without modifying data layout
3. You can **test data independently** from behavior

Rust enforces this discipline at the language level. Over time, your brain will start **naturally separating "what is this"** from **"what can this do"** — a hallmark of elite systems thinking.