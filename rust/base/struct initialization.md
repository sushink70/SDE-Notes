# Struct Initialization Syntax in Rust

```rust
// In Rust, we use Box<T> for heap-allocated recursive structures.
// Option<Box<T>> represents "either a node or nothing (null)".

#[derive(Debug)]
struct TreeNode {
    data: i32,
    left: Option<Box<TreeNode>>,
    right: Option<Box<TreeNode>>,
}

impl TreeNode {
    fn new(data: i32) -> Self {
        TreeNode {
            data,
            left: None,
            right: None,
        }
    }

    fn with_children(
        data: i32,
        left: Option<Box<TreeNode>>,
        right: Option<Box<TreeNode>>,
    ) -> Self {
        TreeNode { data, left, right }
    }
}

// Build:    1
//          / \
//         2   3
//        / \
//       4   5
fn build_sample_tree() -> Box<TreeNode> {
    Box::new(TreeNode::with_children(
        1,
        Some(Box::new(TreeNode::with_children(
            2,
            Some(Box::new(TreeNode::new(4))),
            Some(Box::new(TreeNode::new(5))),
        ))),
        Some(Box::new(TreeNode::new(3))),
    ))
}

fn inorder(node: &Option<Box<TreeNode>>) {
    if let Some(n) = node {
        inorder(&n.left);
        print!("{} ", n.data);
        inorder(&n.right);
    }
}

fn main() {
    let root = build_sample_tree();
    print!("Inorder: ");
    inorder(&Some(root)); // Output: 4 2 5 1 3
    println!();
}
```

## The `TreeNode { data, left, right }` Syntax Explained

This is called **Struct Initialization** in Rust. Let me build it up from scratch.

---

## The Long Form First (Most Explicit)

When you create a struct, the full explicit syntax is:

```rust
TreeNode {
    field_name: value,
    field_name: value,
    field_name: value,
}
```

So for your `TreeNode`:

```rust
fn new(data: i32) -> Self {
    TreeNode {
        data: data,      // field "data"  gets the value of variable "data"
        left: None,      // field "left"  gets None
        right: None,     // field "right" gets None
    }
}
```

This is perfectly valid. But notice `data: data` — the **field name and variable name are identical**. Rust has a shorthand for this.

---

## The Shorthand (Field Init Shorthand)

When a **variable name matches the field name exactly**, Rust lets you write just the name once:

```
data: data   →   data      (shorthand, means the same thing)
```

So this:
```rust
TreeNode {
    data: data,   // redundant — name appears twice
    left: None,
    right: None,
}
```

Becomes this:
```rust
TreeNode {
    data,         // shorthand — variable "data" goes into field "data"
    left: None,
    right: None,
}
```

**Identical behavior. Just less repetition.**

---

## Side by Side Comparison

```rust
// LONG FORM — explicit
fn new(data: i32) -> Self {
    TreeNode {
        data: data,    // field : variable
        left: None,
        right: None,
    }
}

// SHORT FORM — field init shorthand
fn new(data: i32) -> Self {
    TreeNode {
        data,          // field name == variable name, write once
        left: None,
        right: None,
    }
}
```

Both produce **exactly the same memory layout**. No difference in behavior.

---

## Why `left` and `right` Don't Use Shorthand Here

In `new()`, you write:

```rust
TreeNode {
    data,          // shorthand works: parameter is also called "data"
    left: None,    // no shorthand: there's no variable called "left" in scope
    right: None,   // no shorthand: there's no variable called "right" in scope
}
```

There is no local variable named `left` or `right` inside `new()`. So you must write `left: None` explicitly — you're assigning the **value `None`** to the **field `left`**.

---

## But in `with_children` — All Three Use Shorthand

Look at your other constructor:

```rust
fn with_children(
    data: i32,
    left: Option<Box<TreeNode>>,    // parameter named "left"
    right: Option<Box<TreeNode>>,   // parameter named "right"
) -> Self {
    TreeNode { data, left, right }  // ALL three are shorthand
}
```

Here, the **parameters are named** `data`, `left`, `right` — which match the **field names** exactly. So all three can use shorthand.

```
Parameter name     Field name     Match?     Shorthand?
──────────────     ──────────     ──────     ──────────
data               data           YES        data
left               left           YES        left
right              right          YES        right
```

---

## ASCII Flow: How Rust Resolves the Shorthand

```
You write:   TreeNode { data, left, right }
                           │      │      │
Rust reads:                │      │      │
                           ▼      ▼      ▼
              "Find a variable in scope with this name"
                           │      │      │
                           ▼      ▼      ▼
              data=data  left=left  right=right
                           │      │      │
                           ▼      ▼      ▼
              Assign each to the matching struct field
```

---

## The Key Rule to Remember

```
field: variable    →   works always
field              →   works ONLY when a variable with
                       the same name exists in scope
```

This is purely a **syntax convenience**. Rust just saves you from writing the same name twice when they match.

## How `build_sample_tree()` Works — Inside Out

The key insight is: **Rust evaluates nested expressions from the innermost call outward**. Like peeling an onion — deepest layer first.

---

## The Tree We Are Building

```
        1
       / \
      2   3
     / \
    4   5
```

---

## Step 1: Understand `with_children` Signature First

```rust
fn with_children(
    data: i32,
    left: Option<Box<TreeNode>>,
    right: Option<Box<TreeNode>>,
) -> Self
```

So every call needs **3 arguments**:
```
Position 1 → data  (i32)
Position 2 → left  (Option<Box<TreeNode>>)
Position 3 → right (Option<Box<TreeNode>>)
```

---

## Step 2: Execution Order — Innermost First

Rust **cannot** pass something that doesn't exist yet. So it builds from the **leaf nodes upward**.

```
EVALUATION ORDER:

Level 3 (leaves):    TreeNode::new(4)     TreeNode::new(5)     TreeNode::new(3)
                          ↓                    ↓                    ↓
Level 2 (wrap box):  Box::new(...)        Box::new(...)        Box::new(...)
                          ↓                    ↓                    ↓
Level 2 (wrap Some): Some(...)            Some(...)            Some(...)
                          ↓                    ↓
Level 1 (node 2):    TreeNode::with_children(2, Some(Box(4)), Some(Box(5)))
                          ↓
                     Box::new(...)
                          ↓
                     Some(...)
                          ↓
Level 0 (root 1):    TreeNode::with_children(1, Some(Box(node2)), Some(Box(3)))
                          ↓
                     Box::new(root)
```

---

## Step 3: Walk Through Each Layer

### Layer 1 — Build Leaf Node 4
```rust
TreeNode::new(4)
```
```
Creates in memory:
┌──────┬──────┬───────┐
│ data │ left │ right │
│  4   │ None │ None  │
└──────┴──────┴───────┘
```

### Layer 2 — Wrap Node 4 in Box, then Some
```rust
Box::new(TreeNode::new(4))
```
```
Stack              Heap
┌─────────┐        ┌──────┬──────┬───────┐
│  ptr ───┼──────► │  4   │ None │ None  │
└─────────┘        └──────┴──────┴───────┘

Box = pointer living on stack, data living on heap
```

```rust
Some(Box::new(TreeNode::new(4)))
```
```
Some just WRAPS the Box — it means "this value exists, it is not null"

Some( ptr → [4, None, None] )
```

### Same happens for Node 5 and Node 3
```
Some( ptr → [5, None, None] )
Some( ptr → [3, None, None] )
```

---

### Layer 3 — Build Node 2 Using Nodes 4 and 5

Now node 4 and node 5 are **ready** as `Option<Box<TreeNode>>`. So node 2 can be built:

```rust
TreeNode::with_children(
    2,                                      // data
    Some(Box::new(TreeNode::new(4))),       // left
    Some(Box::new(TreeNode::new(5))),       // right
)
```

```
Argument matching:
┌──────────────────────────────────────────────────────────┐
│  Parameter       │  Value passed                         │
├──────────────────┼───────────────────────────────────────┤
│  data: i32       │  2                                    │
│  left: Option<.> │  Some(Box → [4, None, None])          │
│  right: Option<.>│  Some(Box → [5, None, None])          │
└──────────────────┴───────────────────────────────────────┘

Result in memory (Node 2):
┌──────┬───────────────────┬───────────────────┐
│ data │      left         │      right        │
│  2   │ Some(ptr→ node4)  │ Some(ptr→ node5)  │
└──────┴───────────────────┴───────────────────┘
                │                    │
                ▼                    ▼
        [4, None, None]      [5, None, None]
```

### Layer 4 — Wrap Node 2 in Box, then Some
```rust
Some(Box::new( node2 ))
```
```
Some( ptr → [2, Some(ptr→4), Some(ptr→5)] )
```

---

### Layer 5 — Build Root Node 1

Now **all children are ready**. Build the root:

```rust
TreeNode::with_children(
    1,                                      // data
    Some(Box::new(TreeNode::with_children(  // left = node2 subtree
        2, ...
    ))),
    Some(Box::new(TreeNode::new(3))),       // right = node3
)
```

```
Argument matching:
┌──────────────────────────────────────────────────────────┐
│  Parameter       │  Value passed                         │
├──────────────────┼───────────────────────────────────────┤
│  data: i32       │  1                                    │
│  left: Option<.> │  Some(Box → node2)                    │
│  right: Option<.>│  Some(Box → node3)                    │
└──────────────────┴───────────────────────────────────────┘
```

---

## Final Memory Picture

```
Stack
┌─────────────┐
│  root ptr ──┼──────────────────────────────────────────┐
└─────────────┘                                          │
                                                         ▼
Heap                                           ┌──────┬──────┬───────┐
                                               │  1   │ left │ right │
                                               └──────┴──┬───┴───┬───┘
                                                         │       │
                              ┌──────────────────────────┘       │
                              ▼                                   ▼
                    ┌──────┬──────┬───────┐           ┌──────┬──────┬───────┐
                    │  2   │ left │ right │           │  3   │ None │ None  │
                    └──────┴──┬───┴───┬───┘           └──────┴──────┴───────┘
                              │       │
                   ┌──────────┘       └──────────┐
                   ▼                             ▼
        ┌──────┬──────┬───────┐      ┌──────┬──────┬───────┐
        │  4   │ None │ None  │      │  5   │ None │ None  │
        └──────┴──────┴───────┘      └──────┴──────┴───────┘
```

---

## The Pattern: Every Node Follows This Exact Wrapping

```
raw node value
    → Box::new(raw node)        wrap in heap pointer
        → Some(Box::new(...))   wrap in "exists" signal
```

Why this triple-layer?

```
TreeNode          =   the actual data
Box<TreeNode>     =   data lives on heap (needed for recursion — 
                      compiler must know struct size at compile time,
                      a raw recursive struct has infinite size)
Option<Box<...>>  =   either Some(node exists) or None (null/empty)
```

---

## Cognitive Model: Think of it as Nesting Boxes

```
You are packing a shipping box (root node 1):
  └── Left compartment contains another box (node 2)
        └── Left sub-compartment: small item (node 4)
        └── Right sub-compartment: small item (node 5)
  └── Right compartment: small item (node 3)

You can only SEAL a box after its contents are ready.
So you pack innermost items first, seal, then pack outward.
```

This is exactly what Rust does — **innermost expressions evaluated first, result passed outward**.

## No — This is Universal, Not Rust-Specific

This is a **common misconception** worth clearing up immediately.

**Every language evaluates nested expressions from innermost to outermost.** This is not Rust's choice — it is fundamental mathematics and computer science.

---

## Same Tree in Python

```python
class TreeNode:
    def __init__(self, data, left=None, right=None):
        self.data = data
        self.left = left
        self.right = right

root = TreeNode(
    1,
    TreeNode(                        # left of 1
        2,
        TreeNode(4),                 # left of 2  ← built FIRST
        TreeNode(5),                 # right of 2 ← built SECOND
    ),
    TreeNode(3),                     # right of 1 ← built THIRD
)
```

Python evaluates **exactly the same order** — innermost first, outward last.

---

## Same Tree in C

```c
TreeNode* build_tree() {
    return new_node(1,
        new_node(2,
            new_node(4, NULL, NULL),   // ← evaluated first
            new_node(5, NULL, NULL)    // ← evaluated second
        ),
        new_node(3, NULL, NULL)        // ← evaluated third
    );
}
```

Same order. C has no choice either.

---

## Why? — Mathematical Reason

This comes from how **function calls work in all languages**:

```
Rule: Before calling a function, ALL arguments must be
      fully computed first.
```

```
new_node(2,   arg1,   arg2)
              │       │
              │       └── must be a complete value before call
              └────────── must be a complete value before call

So arg1 and arg2 are evaluated BEFORE new_node(2,...) runs.
This is true in every language. Always.
```

---

## What Actually Differs Between Languages

The confusion probably comes from **what you must write explicitly**. Rust makes you write more wrapping (`Box::new`, `Some`) which *looks* more complex — but the evaluation order is identical.

```
                  Python          C              Rust
──────────────────────────────────────────────────────────
Evaluation order  inner→outer     inner→outer    inner→outer
Heap allocation   automatic       manual malloc  explicit Box::new
Null safety       None (runtime)  NULL (runtime) Option (compile time)
Verbosity         low             medium         higher (explicit)
```

---

## The Real Takeaway

```
What you thought:   Rust is different — builds opposite direction
What is true:       ALL languages build inner → outer
What IS different:  Rust makes memory management VISIBLE in code
                    Other languages HIDE it from you
```

Rust's explicitness (writing `Box::new`, `Some`) can **feel** like something different is happening. But underneath, every language runtime is doing the same stack-based inside-out evaluation.

The monk principle here: **never mistake unfamiliar syntax for different behavior**. Always ask — *what is the machine actually doing?*

