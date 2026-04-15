# BST Validity Conditions

Before diving into conditions, let me ground you in the concept.

## What is a BST (Binary Search Tree)?

A **Binary Search Tree** is a binary tree (each node has at most 2 children — left and right) where data is organized with a specific ordering rule so that searching is fast (like binary search on a sorted array).

---

## The 3 Formal Conditions for a Valid BST

**Condition 1 — Left Subtree Rule:**
Every node in the left subtree must have a value **strictly less than** the current node's value.

**Condition 2 — Right Subtree Rule:**
Every node in the right subtree must have a value **strictly greater than** the current node's value.

**Condition 3 — Recursive Rule:**
Both the left subtree and right subtree must themselves be valid BSTs.

> The word "subtree" is crucial — it means not just the direct child, but ALL descendants below it.

---

## The Most Common Mistake (The Hidden Trap)

Most beginners think: *"Just compare each node with its immediate parent."* That is WRONG.

```
        10
       /  \
      5    15
     / \
    3   12   ← 12 > 10 but sits in left subtree of 10!
```
This tree looks locally correct (12 > 5 ✓) but 12 > 10, violating the global BST rule. This is **INVALID**.

The fix: every node carries an **invisible range constraint** — `(min_allowed, max_allowed)` — passed down from ancestors.

---

## Range Constraint Propagation

```
How constraints flow down the tree:
                  
    Start: root has range (-∞, +∞)
    
                [10]   range: (-∞, +∞)
               /    \
    (-∞, 10) [5]    [15] (10, +∞)
            /   \
  (-∞, 5) [3]  [7] (5, 10)   ← must be BOTH > 5 AND < 10
```

Each time you go **left**, the current node's value becomes the new **upper bound**.
Each time you go **right**, the current node's value becomes the new **lower bound**.

---

## Decision Tree: Is This BST Valid?

```
For each node, ask:
                  
┌─────────────────────────────┐
│  Is node.value > min_bound? │
└──────────────┬──────────────┘
               │
        Yes ───┤─── No → INVALID BST
               │
┌──────────────▼──────────────┐
│  Is node.value < max_bound? │
└──────────────┬──────────────┘
               │
        Yes ───┤─── No → INVALID BST
               │
┌──────────────▼────────────────────┐
│  Recurse LEFT with range          │
│  (min_bound, node.value)          │
│  AND RIGHT with range             │
│  (node.value, max_bound)          │
└──────────────┬────────────────────┘
               │
    Both VALID ─┤─── Any INVALID → INVALID BST
               │
           VALID BST ✓
```

---

## Visual: Valid vs Invalid BSTs---

## Algorithm Flow: Validate BST

```
validate(node, min=-∞, max=+∞):

    ┌─────────────────────────────┐
    │  node == NULL?              │
    └────────────┬────────────────┘
                 │
           YES ──┴── return TRUE   ← empty tree / leaf's child = valid
                 │
                 NO
                 ↓
    ┌────────────────────────────────────────┐
    │  node.value <= min  OR                 │
    │  node.value >= max  ?                  │
    └────────────┬───────────────────────────┘
                 │
           YES ──┴── return FALSE   ← constraint violated
                 │
                 NO
                 ↓
    ┌────────────────────────────────────────────────────┐
    │  return validate(node.left,  min, node.value)      │
    │     AND validate(node.right, node.value, max)      │
    └────────────────────────────────────────────────────┘
```

---

## Implementations

**Rust** (idiomatic with `Option<Box<Node>>`)

```rust
#[derive(Debug)]
struct Node {
    val: i64,
    left: Option<Box<Node>>,
    right: Option<Box<Node>>,
}

fn is_valid_bst(node: &Option<Box<Node>>, min: i64, max: i64) -> bool {
    match node {
        None => true, // base case: null node is valid
        Some(n) => {
            if n.val <= min || n.val >= max {
                return false; // violates range constraint
            }
            // pass tightened bounds down each branch
            is_valid_bst(&n.left,  min,   n.val) &&
            is_valid_bst(&n.right, n.val, max)
        }
    }
}

// Entry point: full integer range
fn validate(root: &Option<Box<Node>>) -> bool {
    is_valid_bst(root, i64::MIN, i64::MAX)
}
```

**Python** (clean and readable)

```python
class Node:
    def __init__(self, val, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def is_valid_bst(node, min_val=float('-inf'), max_val=float('inf')):
    if node is None:
        return True                          # base case

    if not (min_val < node.val < max_val):   # range violation
        return False

    return (is_valid_bst(node.left,  min_val, node.val) and
            is_valid_bst(node.right, node.val, max_val))
```

**C** (explicit and low-level)

```c
#include <limits.h>
#include <stdbool.h>

typedef struct Node {
    int val;
    struct Node *left, *right;
} Node;

bool validate_helper(Node *node, long min, long max) {
    if (node == NULL) return true;          /* base case */

    if (node->val <= min || node->val >= max)
        return false;                       /* range violated */

    return validate_helper(node->left,  min,       node->val) &&
           validate_helper(node->right, node->val, max);
}

bool is_valid_bst(Node *root) {
    return validate_helper(root, LONG_MIN, LONG_MAX);
}
```

**Go** (idiomatic)

```go
type Node struct {
    Val   int
    Left  *Node
    Right *Node
}

func isValidBST(root *Node) bool {
    return validate(root, -1<<63, 1<<63-1) // int64 min/max
}

func validate(node *Node, min, max int) bool {
    if node == nil {
        return true
    }
    if node.Val <= min || node.Val >= max {
        return false
    }
    return validate(node.Left,  min,      node.Val) &&
           validate(node.Right, node.Val, max)
}
```

---

## Complexity Analysis

| Metric | Value | Why |
|---|---|---|
| Time | O(n) | visit every node exactly once |
| Space | O(h) | recursion stack depth = tree height `h` |
| Best case (balanced) | O(log n) space | `h = log n` for balanced tree |
| Worst case (skewed) | O(n) space | `h = n` for a linear chain tree |

---

## The "In-order Trick" (Alternative Method)

A valid BST, when traversed **in-order** (left → root → right), always produces a **strictly increasing** sequence. You can validate a BST by doing an in-order traversal and checking that each value is greater than the previous.

```
Tree:      Valid in-order output:
   8
  / \           3 → 8 → 12    ← strictly increasing = VALID BST
 3   12

Tree:      Invalid in-order output:
   10
  /  \
 5    15
/ \
3 12           3 → 5 → 12 → 10 → 15  ← 12 > 10 breaks it = INVALID
```

```python
def is_valid_bst_inorder(root):
    prev = float('-inf')

    def inorder(node):
        nonlocal prev
        if node is None:
            return True
        if not inorder(node.left):
            return False
        if node.val <= prev:   # must be strictly greater
            return False
        prev = node.val
        return inorder(node.right)

    return inorder(root)
```

Both approaches are O(n) time — use whichever feels more natural. The range-bounds method is more *explicit* and interview-preferred. The in-order method is more *elegant* and reveals a deeper insight.

---

## Mental Model to Internalize

Think of every node as a **customs checkpoint**. When a value descends left, it receives a new ceiling ("you and everything below you must be less than me"). When it descends right, it receives a new floor. By the time a value reaches a leaf position, it carries a tightly bounded valid range — the accumulated constraints of every ancestor above it. A BST is valid if and only if every node peacefully respects the passport range handed to it by its ancestors.

> **Cognitive principle — "chunking":** Rather than memorizing "left < root < right" as a flat rule, internalize it as a *dynamic constraint propagation* system. Once you see it as a range narrowing as you descend, you'll never confuse it with the naive single-node check again. That reframing is worth 100 problems of practice.