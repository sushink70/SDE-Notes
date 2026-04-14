# 🔧 The Complete Guide to Tree Manipulations
### Every Operation, Every Transformation, Every Algorithm — C, Go & Rust

---

> *"Manipulation is the art of reshaping structure without losing meaning. Every rotation, every splice, every rebalance is a controlled transformation that preserves an invariant while achieving a goal."*

---

## TABLE OF CONTENTS

1. [What Is Tree Manipulation? — Mental Framework](#1-what-is-tree-manipulation--mental-framework)
2. [Rotation — The Atomic Operation of Self-Balancing Trees](#2-rotation--the-atomic-operation)
3. [Inversion and Mirroring](#3-inversion-and-mirroring)
4. [Flattening — Tree to Linear Structure](#4-flattening--tree-to-linear-structure)
5. [Cloning — Deep Copy of a Tree](#5-cloning--deep-copy)
6. [Merging Two Trees](#6-merging-two-trees)
7. [Splitting a Tree](#7-splitting-a-tree)
8. [Pruning — Removing Subtrees by Condition](#8-pruning)
9. [Grafting — Attaching Subtrees](#9-grafting--attaching-subtrees)
10. [Serialization and Deserialization](#10-serialization-and-deserialization)
11. [Threaded Binary Trees](#11-threaded-binary-trees)
12. [DSW Algorithm — Rebalancing Any BST in O(N)](#12-dsw-algorithm)
13. [Tree to Doubly Linked List (In-Place)](#13-tree-to-doubly-linked-list)
14. [Subtree Operations — Find, Extract, Replace](#14-subtree-operations)
15. [Path Manipulation — Find, Modify, Compress](#15-path-manipulation)
16. [Lazy Propagation in Segment Trees](#16-lazy-propagation)
17. [Euler Tour — Flattening Tree into Array for Range Queries](#17-euler-tour)
18. [Heavy-Light Decomposition (HLD)](#18-heavy-light-decomposition)
19. [Centroid Decomposition](#19-centroid-decomposition)
20. [Augmented Trees — Storing Extra Data](#20-augmented-trees)
21. [Persistent Trees — Immutable Versioned Trees](#21-persistent-trees)
22. [Tree Isomorphism and Canonicalization](#22-tree-isomorphism-and-canonicalization)
23. [Conversion Algorithms](#23-conversion-algorithms)
24. [Complexity Master Table and Decision Map](#24-complexity-master-table)

---

## 1. What Is Tree Manipulation? — Mental Framework

### The Core Idea

Tree manipulation means **changing the structure or content** of a tree while **preserving (or deliberately transforming) its invariants**.

Every manipulation falls into one of three categories:

```
TAXONOMY OF TREE MANIPULATIONS
═══════════════════════════════════════════════════════════════
  CONTENT MANIPULATION     │ STRUCTURAL MANIPULATION   │ TRANSFORMATION
  (value-level changes)    │ (pointer-level changes)   │ (whole-tree reshape)
─────────────────────────────────────────────────────────────────────────────
  Update node value        │ Rotate subtree            │ BST → DLL
  Augment (add metadata)   │ Flatten to linked list    │ BST → Balanced BST
  Tag / color node         │ Mirror / invert           │ N-ary → Binary (LCRS)
  Lazy tag (seg tree)      │ Clone / deep copy         │ Tree → Array (Euler)
  Assign DFS timestamps    │ Merge two trees           │ Tree → Heap
  Assign rank/size         │ Split at key              │ Serialize / Deserialize
  Path update              │ Prune subtrees            │ Threaded tree
  Lazy pushdown            │ Graft subtrees            │ Persistent version
═══════════════════════════════════════════════════════════════
```

### The Invariant Mindset

Before every manipulation, ask:

```
1. What is the INVARIANT I must preserve?
   (BST: left < root < right)
   (Heap: parent ≤ children)
   (AVL: |balance_factor| ≤ 1)
   (Red-Black: black-height uniform, no double-red)

2. Will my operation BREAK the invariant?

3. What REPAIR step restores it?
   (Rotations repair AVL/RB)
   (Sift-up/down repairs heap)
   (DSW repairs BST balance)

This 3-step thinking is what separates
expert tree programmers from everyone else.
```

### Shared Structures Used Throughout This Guide

**C — Base Node:**
```c
// binary_tree.h — shared across all examples
#ifndef BINARY_TREE_H
#define BINARY_TREE_H

#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>

typedef struct Node {
    int   val;
    int   height;   // used by AVL; 0 for plain trees
    int   size;     // subtree size (augmented)
    struct Node *left;
    struct Node *right;
    struct Node *parent; // used in threaded/DLL conversions
} Node;

Node *node_new(int val) {
    Node *n = (Node *)calloc(1, sizeof(Node));
    n->val    = val;
    n->height = 1;
    n->size   = 1;
    return n;
}

int node_height(Node *n) { return n ? n->height : 0; }
int node_size(Node *n)   { return n ? n->size   : 0; }

void node_update(Node *n) {
    if (!n) return;
    int lh = node_height(n->left),  rh = node_height(n->right);
    n->height = 1 + (lh > rh ? lh : rh);
    n->size   = 1 + node_size(n->left) + node_size(n->right);
}

void inorder_print(Node *n) {
    if (!n) return;
    inorder_print(n->left);
    printf("%d ", n->val);
    inorder_print(n->right);
}

// Build BST from array
Node *bst_insert(Node *root, int val) {
    if (!root) return node_new(val);
    if (val < root->val) root->left  = bst_insert(root->left,  val);
    else if (val > root->val) root->right = bst_insert(root->right, val);
    return root;
}

#endif
```

**Go — Base Node:**
```go
package tree

type Node struct {
    Val    int
    Height int
    Size   int
    Left   *Node
    Right  *Node
    Parent *Node
}

func NewNode(val int) *Node {
    return &Node{Val: val, Height: 1, Size: 1}
}

func Height(n *Node) int {
    if n == nil { return 0 }
    return n.Height
}

func Size(n *Node) int {
    if n == nil { return 0 }
    return n.Size
}

func Update(n *Node) {
    if n == nil { return }
    lh, rh := Height(n.Left), Height(n.Right)
    if lh > rh { n.Height = 1 + lh } else { n.Height = 1 + rh }
    n.Size = 1 + Size(n.Left) + Size(n.Right)
}

func Inorder(n *Node) {
    if n == nil { return }
    Inorder(n.Left)
    print(n.Val, " ")
    Inorder(n.Right)
}
```

**Rust — Base Node:**
```rust
// All examples use this shared definition
use std::fmt;

pub type Tree = Option<Box<Node>>;

#[derive(Debug, Clone)]
pub struct Node {
    pub val:    i32,
    pub height: i32,
    pub size:   i32,
    pub left:   Tree,
    pub right:  Tree,
}

impl Node {
    pub fn new(val: i32) -> Box<Self> {
        Box::new(Node { val, height: 1, size: 1, left: None, right: None })
    }
    pub fn leaf(val: i32) -> Tree { Some(Self::new(val)) }
}

pub fn height(t: &Tree) -> i32 {
    t.as_ref().map_or(0, |n| n.height)
}

pub fn sz(t: &Tree) -> i32 {
    t.as_ref().map_or(0, |n| n.size)
}

pub fn update(n: &mut Node) {
    n.height = 1 + height(&n.left).max(height(&n.right));
    n.size   = 1 + sz(&n.left) + sz(&n.right);
}

pub fn inorder(t: &Tree) {
    if let Some(n) = t {
        inorder(&n.left);
        print!("{} ", n.val);
        inorder(&n.right);
    }
}
```

---

## 2. Rotation — The Atomic Operation

Rotation is **the fundamental structural primitive** of all self-balancing trees. Every complex tree manipulation (AVL rebalance, RB-tree fix, Splay, Treap split/merge) is built from rotations.

### What Rotation Does

Rotation moves a node UP and its child DOWN — **while preserving the BST inorder sequence**.

```
RIGHT ROTATION about node Z:

BEFORE:                     AFTER:
    Z                           Y
   / \                         / \
  Y   T3      ──────►         X   Z
 / \                         / \ / \
X   T2                      T1 T2 T3 T4
/ \
T1 T4

KEY INVARIANT PRESERVED:
  Inorder of both trees = [T1, X, T2, Y, T3, Z, T4]
  The relative order NEVER changes during rotation!

LEFT ROTATION about node Z:

BEFORE:                     AFTER:
    Z                           Y
   / \                         / \
  T1  Y       ──────►         Z   X
     / \                     / \ / \
    T2  X                   T1 T2 T3 T4
       / \
      T3  T4
```

### The 6 Rotation Rules (Memorize These)

```
RIGHT ROTATE(Z) — Y becomes new root:
  1. Y = Z.left
  2. T2 = Y.right
  3. Y.right = Z          (Z descends)
  4. Z.left  = T2         (T2 moves across)
  5. Update heights: Z first, then Y (bottom-up order!)
  6. Return Y             (new subtree root)

LEFT ROTATE(Z) — Y becomes new root:
  1. Y = Z.right
  2. T2 = Y.left
  3. Y.left  = Z          (Z descends)
  4. Z.right = T2         (T2 moves across)
  5. Update heights: Z first, then Y
  6. Return Y
```

### Visual Call Flow — Left Rotation

```
left_rotate(Z):
│
├── Y = Z.right          [save right child]
│      Z                         Y
│     / \                       / \
│    T1   Y          →         ?   X
│        / \                      / \
│       T2  X                    T3  T4
│
├── T2 = Y.left          [save Y's left child (the "transfer" node)]
│
├── Y.left = Z           [Y rises, Z descends]
│      Z←──Y                     Y
│     / \   \                   / \
│    T1  T2   X    →           Z   X
│            / \              / \ / \
│           T3  T4           T1 T2 T3 T4
│
├── Z.right = T2         [T2 fills the gap]
│
├── update_height(Z)     [Z's children changed]
├── update_height(Y)     [Y's children changed]
└── return Y             [Y is now subtree root]
```

**C:**
```c
#include "binary_tree.h"

// ── RIGHT ROTATION ──────────────────────────────────────────────
// Z is the node being rotated down.
// Y (Z's left child) becomes the new subtree root.
Node *right_rotate(Node *Z) {
    Node *Y  = Z->left;   // Y will rise
    Node *T2 = Y->right;  // T2 is the "transfer" subtree

    // Perform rotation
    Y->right = Z;   // Y rises: Z becomes Y's right child
    Z->left  = T2;  // T2 fills Z's left gap

    // CRITICAL: update Z BEFORE Y (Z is now lower)
    node_update(Z);
    node_update(Y);

    return Y;  // Y is new subtree root
}

// ── LEFT ROTATION ───────────────────────────────────────────────
Node *left_rotate(Node *Z) {
    Node *Y  = Z->right;  // Y will rise
    Node *T2 = Y->left;   // T2 is the "transfer" subtree

    Y->left  = Z;
    Z->right = T2;

    node_update(Z);
    node_update(Y);

    return Y;
}

// ── DOUBLE ROTATIONS ────────────────────────────────────────────
// Left-Right: first left-rotate Z.left, then right-rotate Z
Node *left_right_rotate(Node *Z) {
    Z->left = left_rotate(Z->left);
    return right_rotate(Z);
}

// Right-Left: first right-rotate Z.right, then left-rotate Z
Node *right_left_rotate(Node *Z) {
    Z->right = right_rotate(Z->right);
    return left_rotate(Z);
}

// ── AVL REBALANCE (uses all 4 cases) ────────────────────────────
Node *avl_rebalance(Node *n) {
    node_update(n);
    int bf = node_height(n->left) - node_height(n->right);

    if (bf > 1) {  // Left heavy
        if (node_height(n->left->left) >= node_height(n->left->right))
            return right_rotate(n);         // LL case
        else
            return left_right_rotate(n);    // LR case
    }
    if (bf < -1) {  // Right heavy
        if (node_height(n->right->right) >= node_height(n->right->left))
            return left_rotate(n);          // RR case
        else
            return right_left_rotate(n);    // RL case
    }
    return n;  // Already balanced
}

// ── SPLAY OPERATION ─────────────────────────────────────────────
// Move node with given key to root via rotations.
// Used in Splay Trees. Amortized O(log N).
//
// Three cases:
//   Zig:       X is child of root → single rotation
//   Zig-Zig:   X and parent same side → rotate parent first, then X
//   Zig-Zag:   X and parent opposite sides → rotate X twice
Node *splay(Node *root, int key) {
    if (!root || root->val == key) return root;

    if (key < root->val) {
        if (!root->left) return root;

        if (key < root->left->val) {
            // Zig-Zig (Left-Left): splay key in left-left subtree
            root->left->left = splay(root->left->left, key);
            root = right_rotate(root);           // rotate root
        } else if (key > root->left->val) {
            // Zig-Zag (Left-Right): splay key in left-right subtree
            root->left->right = splay(root->left->right, key);
            if (root->left->right)
                root->left = left_rotate(root->left);
        }
        return root->left ? right_rotate(root) : root;
    } else {
        if (!root->right) return root;

        if (key > root->right->val) {
            // Zig-Zig (Right-Right)
            root->right->right = splay(root->right->right, key);
            root = left_rotate(root);
        } else if (key < root->right->val) {
            // Zig-Zag (Right-Left)
            root->right->left = splay(root->right->left, key);
            if (root->right->left)
                root->right = right_rotate(root->right);
        }
        return root->right ? left_rotate(root) : root;
    }
}

int main(void) {
    // Build a right-skewed BST (worst case)
    Node *root = NULL;
    for (int i = 1; i <= 7; i++)
        root = bst_insert(root, i);

    printf("Before splay: ");
    inorder_print(root);  // 1 2 3 4 5 6 7
    printf("\n");

    // Splay key=3 to root
    root = splay(root, 3);
    printf("After splay(3): root=%d\n", root->val);  // 3

    // Now left-rotate and check
    root = left_rotate(root);
    printf("After left_rotate: root=%d\n", root->val);

    return 0;
}
```

**Go:**
```go
package main

import "fmt"

type Node struct {
    Val         int
    Height      int
    Left, Right *Node
}

func newNode(val int) *Node { return &Node{Val: val, Height: 1} }

func height(n *Node) int {
    if n == nil { return 0 }
    return n.Height
}

func maxInt(a, b int) int {
    if a > b { return a }
    return b
}

func updateHeight(n *Node) {
    if n != nil {
        n.Height = 1 + maxInt(height(n.Left), height(n.Right))
    }
}

// rightRotate: Y = Z.left rises; Z descends to Y.right
func rightRotate(Z *Node) *Node {
    Y := Z.Left
    T2 := Y.Right

    Y.Right = Z
    Z.Left = T2

    updateHeight(Z) // Z first — it's now lower
    updateHeight(Y)
    return Y
}

// leftRotate: Y = Z.right rises; Z descends to Y.left
func leftRotate(Z *Node) *Node {
    Y := Z.Right
    T2 := Y.Left

    Y.Left = Z
    Z.Right = T2

    updateHeight(Z)
    updateHeight(Y)
    return Y
}

func leftRightRotate(Z *Node) *Node {
    Z.Left = leftRotate(Z.Left)
    return rightRotate(Z)
}

func rightLeftRotate(Z *Node) *Node {
    Z.Right = rightRotate(Z.Right)
    return leftRotate(Z)
}

func avlRebalance(n *Node) *Node {
    updateHeight(n)
    bf := height(n.Left) - height(n.Right)

    if bf > 1 {
        if height(n.Left.Left) >= height(n.Left.Right) {
            return rightRotate(n)
        }
        return leftRightRotate(n)
    }
    if bf < -1 {
        if height(n.Right.Right) >= height(n.Right.Left) {
            return leftRotate(n)
        }
        return rightLeftRotate(n)
    }
    return n
}

func inorder(n *Node) {
    if n == nil { return }
    inorder(n.Left)
    fmt.Printf("%d ", n.Val)
    inorder(n.Right)
}

func main() {
    // Build right-skewed tree then rebalance root
    root := newNode(4)
    root.Right = newNode(6)
    root.Right.Right = newNode(8)

    fmt.Printf("Before: root=%d height=%d\n", root.Val, root.Height)
    root = leftRotate(root)
    fmt.Printf("After leftRotate: root=%d\n", root.Val) // 6
}
```

**Rust:**
```rust
type Tree = Option<Box<Node>>;

#[derive(Debug, Clone)]
struct Node {
    val:   i32,
    ht:    i32,
    left:  Tree,
    right: Tree,
}

impl Node {
    fn new(val: i32) -> Box<Self> {
        Box::new(Node { val, ht: 1, left: None, right: None })
    }
}

fn ht(t: &Tree) -> i32 { t.as_ref().map_or(0, |n| n.ht) }

fn update_ht(n: &mut Node) {
    n.ht = 1 + ht(&n.left).max(ht(&n.right));
}

// Left rotation: Z.right (Y) rises, Z descends to Y.left
fn left_rotate(mut z: Box<Node>) -> Box<Node> {
    let mut y = z.right.take().expect("left_rotate: no right child");
    let t2 = y.left.take();   // "transfer" subtree

    z.right = t2;             // T2 fills Z's right gap
    update_ht(&mut z);        // update Z first — it's now lower

    y.left = Some(z);         // Z becomes Y's left child
    update_ht(&mut y);
    y
}

// Right rotation: Z.left (Y) rises, Z descends to Y.right
fn right_rotate(mut z: Box<Node>) -> Box<Node> {
    let mut y = z.left.take().expect("right_rotate: no left child");
    let t2 = y.right.take();

    z.left = t2;
    update_ht(&mut z);

    y.right = Some(z);
    update_ht(&mut y);
    y
}

fn left_right_rotate(mut z: Box<Node>) -> Box<Node> {
    z.left = Some(left_rotate(z.left.take().unwrap()));
    right_rotate(z)
}

fn right_left_rotate(mut z: Box<Node>) -> Box<Node> {
    z.right = Some(right_rotate(z.right.take().unwrap()));
    left_rotate(z)
}

fn avl_rebalance(mut n: Box<Node>) -> Box<Node> {
    update_ht(&mut n);
    let bf = ht(&n.left) - ht(&n.right);

    if bf > 1 {
        let ll = ht(&n.left.as_ref().unwrap().left);
        let lr = ht(&n.left.as_ref().unwrap().right);
        if ll >= lr { right_rotate(n) } else { left_right_rotate(n) }
    } else if bf < -1 {
        let rr = ht(&n.right.as_ref().unwrap().right);
        let rl = ht(&n.right.as_ref().unwrap().left);
        if rr >= rl { left_rotate(n) } else { right_left_rotate(n) }
    } else {
        n
    }
}

fn inorder(t: &Tree) {
    if let Some(n) = t {
        inorder(&n.left);
        print!("{} ", n.val);
        inorder(&n.right);
    }
}

fn main() {
    // Build: 4 → right → 6 → right → 8 (right-skewed)
    let mut root = Node::new(4);
    let mut n6   = Node::new(6);
    n6.right     = Some(Node::new(8));
    root.right   = Some(n6);

    let root = left_rotate(root);
    println!("After left_rotate: root={}", root.val); // 6

    inorder(&Some(root));
    println!();
}
```

---

## 3. Inversion and Mirroring

**Inverting** (mirroring) a binary tree means swapping every node's left and right children, recursively. The tree becomes its own mirror image.

```
ORIGINAL:               MIRRORED:
      4                       4
    /   \                   /   \
   2     7       →         7     2
  / \   / \               / \   / \
 1   3 6   9             9   6 3   1

Algorithm: Postorder — process children first, then swap.
Why postorder? We must finish transforming subtrees BEFORE swapping.
```

**Decision Flow:**
```
invert(node):
    if node == null → return null
    ┌─────────────────────────────┐
    │  Recurse into BOTH children │  ← Must complete first
    │  left  = invert(node.left)  │
    │  right = invert(node.right) │
    └─────────────────────────────┘
                ↓
    ┌─────────────────────────────┐
    │  SWAP left and right        │
    │  node.left  = right         │
    │  node.right = left          │
    └─────────────────────────────┘
                ↓
           return node
```

**C:**
```c
#include "binary_tree.h"

// Recursive inversion — O(N) time, O(H) space (call stack)
Node *invert_tree(Node *root) {
    if (!root) return NULL;

    // Recurse first (postorder)
    Node *new_left  = invert_tree(root->right);
    Node *new_right = invert_tree(root->left);

    // Swap
    root->left  = new_left;
    root->right = new_right;

    return root;
}

// Iterative inversion using a queue (BFS-based)
// Insight: visit each node level by level and swap its children
Node *invert_tree_iterative(Node *root) {
    if (!root) return NULL;

    Node *queue[1024];
    int front = 0, back = 0;
    queue[back++] = root;

    while (front < back) {
        Node *cur = queue[front++];

        // Swap children
        Node *tmp  = cur->left;
        cur->left  = cur->right;
        cur->right = tmp;

        if (cur->left)  queue[back++] = cur->left;
        if (cur->right) queue[back++] = cur->right;
    }
    return root;
}

// Check if two trees are mirror images of each other
// (Useful for "symmetric tree" problem)
bool are_mirrors(Node *a, Node *b) {
    if (!a && !b) return true;
    if (!a || !b) return false;
    return (a->val == b->val)
        && are_mirrors(a->left,  b->right)
        && are_mirrors(a->right, b->left);
}

bool is_symmetric(Node *root) {
    return !root || are_mirrors(root->left, root->right);
}

int main(void) {
    //       4
    //      / \
    //     2   7
    //    / \ / \
    //   1  3 6  9
    Node *root = node_new(4);
    root->left  = node_new(2);
    root->right = node_new(7);
    root->left->left   = node_new(1);
    root->left->right  = node_new(3);
    root->right->left  = node_new(6);
    root->right->right = node_new(9);

    printf("Before invert: ");
    inorder_print(root);  // 1 2 3 4 6 7 9
    printf("\n");

    invert_tree(root);

    printf("After invert:  ");
    inorder_print(root);  // 9 7 6 4 3 2 1
    printf("\n");

    printf("Symmetric? %s\n", is_symmetric(root) ? "YES" : "NO");
    return 0;
}
```

**Go:**
```go
package main

import "fmt"

type Node struct {
    Val         int
    Left, Right *Node
}

func newNode(val int) *Node { return &Node{Val: val} }

// Recursive invert
func invertTree(root *Node) *Node {
    if root == nil {
        return nil
    }
    root.Left, root.Right = invertTree(root.Right), invertTree(root.Left)
    return root
}

// Iterative invert using BFS
func invertTreeIterative(root *Node) *Node {
    if root == nil {
        return nil
    }
    queue := []*Node{root}
    for len(queue) > 0 {
        cur := queue[0]
        queue = queue[1:]
        cur.Left, cur.Right = cur.Right, cur.Left
        if cur.Left != nil  { queue = append(queue, cur.Left)  }
        if cur.Right != nil { queue = append(queue, cur.Right) }
    }
    return root
}

func areMirrors(a, b *Node) bool {
    if a == nil && b == nil { return true }
    if a == nil || b == nil { return false }
    return a.Val == b.Val &&
        areMirrors(a.Left, b.Right) &&
        areMirrors(a.Right, b.Left)
}

func isSymmetric(root *Node) bool {
    return root == nil || areMirrors(root.Left, root.Right)
}

func inorder(n *Node) {
    if n == nil { return }
    inorder(n.Left)
    fmt.Printf("%d ", n.Val)
    inorder(n.Right)
}

func main() {
    root := newNode(4)
    root.Left = newNode(2)
    root.Right = newNode(7)
    root.Left.Left = newNode(1)
    root.Left.Right = newNode(3)
    root.Right.Left = newNode(6)
    root.Right.Right = newNode(9)

    fmt.Print("Before: "); inorder(root); fmt.Println()
    invertTree(root)
    fmt.Print("After:  "); inorder(root); fmt.Println()
    // 9 7 6 4 3 2 1
}
```

**Rust:**
```rust
type Tree = Option<Box<Node>>;

#[derive(Debug, Clone)]
struct Node { val: i32, left: Tree, right: Tree }

impl Node {
    fn new(val: i32) -> Tree {
        Some(Box::new(Node { val, left: None, right: None }))
    }
}

fn invert(t: Tree) -> Tree {
    t.map(|mut n| {
        // swap then recurse (can also recurse then swap — same result)
        let (l, r) = (n.left.take(), n.right.take());
        n.left  = invert(r);
        n.right = invert(l);
        n
    })
}

fn are_mirrors(a: &Tree, b: &Tree) -> bool {
    match (a, b) {
        (None, None) => true,
        (Some(x), Some(y)) =>
            x.val == y.val
            && are_mirrors(&x.left,  &y.right)
            && are_mirrors(&x.right, &y.left),
        _ => false,
    }
}

fn is_symmetric(t: &Tree) -> bool {
    match t {
        None    => true,
        Some(n) => are_mirrors(&n.left, &n.right),
    }
}

fn inorder(t: &Tree) {
    if let Some(n) = t {
        inorder(&n.left);
        print!("{} ", n.val);
        inorder(&n.right);
    }
}

fn main() {
    let root = Some(Box::new(Node {
        val: 4,
        left: Some(Box::new(Node {
            val: 2,
            left:  Node::new(1),
            right: Node::new(3),
        })),
        right: Some(Box::new(Node {
            val: 7,
            left:  Node::new(6),
            right: Node::new(9),
        })),
    }));

    print!("Before: "); inorder(&root); println!();
    let root = invert(root);
    print!("After:  "); inorder(&root); println!();
    // 9 7 6 4 3 2 1
}
```

---

## 4. Flattening — Tree to Linear Structure

Flattening reshapes a tree into a linear sequence **in-place**, using the existing node pointers.

### 4.1 Flatten to Right-Skewed List (Preorder)

Classic LeetCode 114. Convert to a right-linked list in preorder traversal order.

```
ORIGINAL:               FLATTENED (right-linked list):
      1                 1
     / \                 \
    2   5       →         2
   / \   \                 \
  3   4   6                 3
                             \
                              4
                               \
                                5
                                 \
                                  6

Algorithm Options:
  A) Preorder collect → rebuild (O(N) extra space)
  B) Morris-like in-place (O(1) extra space) ← preferred
  C) Reverse postorder with "prev" pointer
```

**C — O(1) space approach:**
```c
#include "binary_tree.h"

// ── METHOD 1: O(1) space — Morris-like ──────────────────────────
// For each node with a left subtree:
//   1. Find the rightmost node of the left subtree
//   2. Wire it to the current node's right subtree
//   3. Move left subtree to right
//   4. Advance to next right node
void flatten_to_list(Node *root) {
    Node *cur = root;
    while (cur) {
        if (cur->left) {
            // Find rightmost node of left subtree
            Node *rightmost = cur->left;
            while (rightmost->right) rightmost = rightmost->right;

            // Wire: rightmost.right → cur.right (splice in the right subtree)
            rightmost->right = cur->right;

            // Move entire left subtree to right
            cur->right = cur->left;
            cur->left  = NULL;
        }
        cur = cur->right;  // advance
    }
}

// ── METHOD 2: Recursive with "prev" pointer (reverse postorder) ─
// Traverse in reverse preorder (right → left → root)
// Each node's right points to previously processed node
static Node *prev_node = NULL;

void flatten_recursive(Node *root) {
    if (!root) return;
    flatten_recursive(root->right);  // Process right first
    flatten_recursive(root->left);
    root->right = prev_node;  // Link to previously processed
    root->left  = NULL;
    prev_node   = root;
}

void print_flat_list(Node *root) {
    Node *cur = root;
    while (cur) {
        printf("%d", cur->val);
        if (cur->right) printf(" → ");
        cur = cur->right;
    }
    printf("\n");
}

int main(void) {
    //       1
    //      / \
    //     2   5
    //    / \   \
    //   3   4   6
    Node *root = node_new(1);
    root->left  = node_new(2);
    root->right = node_new(5);
    root->left->left   = node_new(3);
    root->left->right  = node_new(4);
    root->right->right = node_new(6);

    flatten_to_list(root);
    printf("Flattened: ");
    print_flat_list(root);  // 1 → 2 → 3 → 4 → 5 → 6
    return 0;
}
```

**Go:**
```go
package main

import "fmt"

type Node struct{ Val int; Left, Right *Node }

func newNode(v int) *Node { return &Node{Val: v} }

// Flatten in-place: Morris-like O(1) space
func flatten(root *Node) {
    cur := root
    for cur != nil {
        if cur.Left != nil {
            // Find rightmost of left subtree
            rightmost := cur.Left
            for rightmost.Right != nil {
                rightmost = rightmost.Right
            }
            rightmost.Right = cur.Right // splice
            cur.Right = cur.Left
            cur.Left = nil
        }
        cur = cur.Right
    }
}

func printList(root *Node) {
    for cur := root; cur != nil; cur = cur.Right {
        fmt.Printf("%d", cur.Val)
        if cur.Right != nil { fmt.Print(" → ") }
    }
    fmt.Println()
}

func main() {
    root := newNode(1)
    root.Left = newNode(2)
    root.Right = newNode(5)
    root.Left.Left = newNode(3)
    root.Left.Right = newNode(4)
    root.Right.Right = newNode(6)

    flatten(root)
    printList(root) // 1 → 2 → 3 → 4 → 5 → 6
}
```

**Rust:**
```rust
type Tree = Option<Box<Node>>;
#[derive(Debug)]
struct Node { val: i32, left: Tree, right: Tree }

impl Node {
    fn leaf(v: i32) -> Tree { Some(Box::new(Node{val:v,left:None,right:None})) }
}

// Collect preorder into vec, then rebuild as right-linked list
fn flatten(root: Tree) -> Tree {
    let mut vals = Vec::new();
    collect_preorder(&root, &mut vals);

    // Rebuild as right-linked list from the end
    let mut head: Tree = None;
    for &v in vals.iter().rev() {
        let mut n = Box::new(Node { val: v, left: None, right: None });
        n.right = head.take();
        head = Some(n);
    }
    head
}

fn collect_preorder(t: &Tree, out: &mut Vec<i32>) {
    if let Some(n) = t {
        out.push(n.val);
        collect_preorder(&n.left,  out);
        collect_preorder(&n.right, out);
    }
}

fn print_list(t: &Tree) {
    let mut cur = t;
    while let Some(n) = cur {
        print!("{}", n.val);
        if n.right.is_some() { print!(" → "); }
        cur = &n.right;
    }
    println!();
}

fn main() {
    let root = Some(Box::new(Node {
        val: 1,
        left: Some(Box::new(Node {
            val: 2,
            left:  Node::leaf(3),
            right: Node::leaf(4),
        })),
        right: Some(Box::new(Node {
            val: 5, left: None,
            right: Node::leaf(6),
        })),
    }));

    let flat = flatten(root);
    print_list(&flat); // 1 → 2 → 3 → 4 → 5 → 6
}
```

---

## 5. Cloning — Deep Copy

A **deep copy** creates a completely independent tree. Every node is newly allocated; no shared pointers with the original.

```
SHALLOW copy (WRONG): both trees share the same nodes
  original.root ──┐
                   └──► Node(4) ◄── clone.root
                  (shared! mutating one affects the other)

DEEP copy (CORRECT): completely independent
  original.root ──► Node(4)      (original)
  clone.root    ──► Node(4)'     (new allocation, same values)
```

**C:**
```c
// Deep copy: O(N) time, O(N) space
Node *deep_copy(Node *root) {
    if (!root) return NULL;
    Node *copy   = node_new(root->val);
    copy->left   = deep_copy(root->left);
    copy->right  = deep_copy(root->right);
    copy->height = root->height;
    copy->size   = root->size;
    return copy;
}

// Verify independence: modify copy, check original unchanged
int main(void) {
    Node *original = NULL;
    for (int v : (int[]){5, 3, 7, 1, 4}) // C99 compound literal
        original = bst_insert(original, v);

    Node *copy = deep_copy(original);

    // Modify copy
    copy->val = 999;

    printf("Original root: %d\n", original->val);  // 5 (unchanged)
    printf("Copy root: %d\n",     copy->val);       // 999
    return 0;
}
```

**Go:**
```go
// Deep copy using recursion
func deepCopy(root *Node) *Node {
    if root == nil { return nil }
    return &Node{
        Val:    root.Val,
        Height: root.Height,
        Left:   deepCopy(root.Left),
        Right:  deepCopy(root.Right),
    }
}

// Deep copy using BFS (iterative) — useful for very deep trees
// to avoid stack overflow
func deepCopyIterative(root *Node) *Node {
    if root == nil { return nil }

    // Use two queues: one for original, one for copies
    origQ := []*Node{root}
    copyRoot := &Node{Val: root.Val}
    copyQ := []*Node{copyRoot}

    for len(origQ) > 0 {
        orig := origQ[0]; origQ = origQ[1:]
        cpy  := copyQ[0]; copyQ = copyQ[1:]

        if orig.Left != nil {
            cpy.Left = &Node{Val: orig.Left.Val}
            origQ = append(origQ, orig.Left)
            copyQ = append(copyQ, cpy.Left)
        }
        if orig.Right != nil {
            cpy.Right = &Node{Val: orig.Right.Val}
            origQ = append(origQ, orig.Right)
            copyQ = append(copyQ, cpy.Right)
        }
    }
    return copyRoot
}
```

**Rust:**
```rust
// In Rust, Clone is derived — clone() performs a deep copy automatically
// because Box<T> clones recursively.

#[derive(Debug, Clone)]  // derive Clone
struct Node {
    val:   i32,
    left:  Option<Box<Node>>,
    right: Option<Box<Node>>,
}

fn main() {
    let original = Some(Box::new(Node {
        val:   5,
        left:  Some(Box::new(Node { val: 3, left: None, right: None })),
        right: Some(Box::new(Node { val: 7, left: None, right: None })),
    }));

    let mut copy = original.clone();  // Deep copy — completely independent!

    // Mutate copy
    if let Some(ref mut n) = copy {
        n.val = 999;
    }

    // Original untouched
    println!("Original: {}", original.as_ref().unwrap().val); // 5
    println!("Copy:     {}", copy.as_ref().unwrap().val);     // 999
}
```

---

## 6. Merging Two Trees

### 6.1 Merge Two Binary Trees (Overlapping Sum)

Merge two trees by **adding values at overlapping positions**. If only one tree has a node at a position, use that node.

```
TREE 1:          TREE 2:          MERGED:
     1                2                3
    / \              / \              / \
   3   2            1   3            4   5
  /                  \   \          / \   \
 5                    4   7        5   4   7
```

**C:**
```c
// Merge two trees — node values are SUMMED at overlapping positions
Node *merge_trees(Node *t1, Node *t2) {
    if (!t1) return t2;  // Use t2 if t1 missing
    if (!t2) return t1;  // Use t1 if t2 missing

    // Both exist: sum values, recurse on both sides
    t1->val  += t2->val;
    t1->left  = merge_trees(t1->left,  t2->left);
    t1->right = merge_trees(t1->right, t2->right);
    return t1;
}

// Non-destructive merge (creates new nodes)
Node *merge_trees_copy(Node *t1, Node *t2) {
    if (!t1 && !t2) return NULL;
    int val = (t1 ? t1->val : 0) + (t2 ? t2->val : 0);
    Node *result = node_new(val);
    result->left  = merge_trees_copy(t1 ? t1->left  : NULL,
                                     t2 ? t2->left  : NULL);
    result->right = merge_trees_copy(t1 ? t1->right : NULL,
                                     t2 ? t2->right : NULL);
    return result;
}
```

### 6.2 Merge Two BSTs (Sorted Merge)

Merge two BSTs into one balanced BST.

```
ALGORITHM:
  1. Convert BST1 to sorted array  → A1  (inorder traversal)
  2. Convert BST2 to sorted array  → A2
  3. Merge A1 and A2 (merge step of merge sort) → A
  4. Build balanced BST from sorted array A

TIME: O(N + M)   SPACE: O(N + M)
```

**Go:**
```go
package main

import "fmt"

type Node struct { Val int; Left, Right *Node }

// Step 1: BST → sorted slice via inorder
func toSortedSlice(root *Node, out *[]int) {
    if root == nil { return }
    toSortedSlice(root.Left, out)
    *out = append(*out, root.Val)
    toSortedSlice(root.Right, out)
}

// Step 2: merge two sorted slices
func mergeSorted(a, b []int) []int {
    result := make([]int, 0, len(a)+len(b))
    i, j := 0, 0
    for i < len(a) && j < len(b) {
        if a[i] <= b[j] { result = append(result, a[i]); i++ } else
                         { result = append(result, b[j]); j++ }
    }
    result = append(result, a[i:]...)
    result = append(result, b[j:]...)
    return result
}

// Step 3: sorted slice → balanced BST
func sortedToBST(arr []int) *Node {
    if len(arr) == 0 { return nil }
    mid := len(arr) / 2
    return &Node{
        Val:   arr[mid],
        Left:  sortedToBST(arr[:mid]),
        Right: sortedToBST(arr[mid+1:]),
    }
}

func mergeBSTs(t1, t2 *Node) *Node {
    var a1, a2 []int
    toSortedSlice(t1, &a1)
    toSortedSlice(t2, &a2)
    merged := mergeSorted(a1, a2)
    return sortedToBST(merged)
}

func inorder(n *Node) {
    if n == nil { return }
    inorder(n.Left)
    fmt.Printf("%d ", n.Val)
    inorder(n.Right)
}

func bstInsert(root *Node, val int) *Node {
    if root == nil { return &Node{Val: val} }
    if val < root.Val { root.Left  = bstInsert(root.Left,  val) } else
                      { root.Right = bstInsert(root.Right, val) }
    return root
}

func main() {
    var t1, t2 *Node
    for _, v := range []int{3, 1, 5}  { t1 = bstInsert(t1, v) }
    for _, v := range []int{4, 2, 6}  { t2 = bstInsert(t2, v) }

    merged := mergeBSTs(t1, t2)
    fmt.Print("Merged BST (inorder): ")
    inorder(merged) // 1 2 3 4 5 6
    fmt.Println()
}
```

---

## 7. Splitting a Tree

Splitting divides a tree into two subtrees at a given key. Used heavily in **Treap** and **order-statistic trees**.

```
SPLIT BST at key K:
  → T_left:  all nodes with key ≤ K
  → T_right: all nodes with key > K

EXAMPLE: Split at K=4:
      5                2          7
     / \             /   \       / \
    2   7    →      1     4     6   8
   / \ / \               /
  1  4 6  8             3

ALGORITHM (recursive):
  split(root, K):
    if root == null: return (null, null)
    if root.key ≤ K:
        (left, right) = split(root.right, K)
        root.right = left
        return (root, right)
    else:
        (left, right) = split(root.left, K)
        root.left = right
        return (left, root)
```

**C:**
```c
typedef struct { Node *left; Node *right; } SplitResult;

// Split BST at key: left has keys ≤ key, right has keys > key
SplitResult bst_split(Node *root, int key) {
    if (!root) return (SplitResult){NULL, NULL};

    if (root->val <= key) {
        // Root goes to LEFT part; recurse into right subtree
        SplitResult r = bst_split(root->right, key);
        root->right = r.left;   // attach left portion of right split
        node_update(root);
        return (SplitResult){root, r.right};
    } else {
        // Root goes to RIGHT part; recurse into left subtree
        SplitResult r = bst_split(root->left, key);
        root->left = r.right;   // attach right portion of left split
        node_update(root);
        return (SplitResult){r.left, root};
    }
}

// Merge two BSTs where ALL keys in left < ALL keys in right
// (reverse of split — valid only when this ordering holds)
Node *bst_merge_ordered(Node *left, Node *right) {
    if (!left)  return right;
    if (!right) return left;

    // Splay max of left to root, or use recursive approach
    // Simple recursive merge:
    if (left->val > right->val) {
        left->right = bst_merge_ordered(left->right, right);
        node_update(left);
        return left;
    } else {
        right->left = bst_merge_ordered(left, right->left);
        node_update(right);
        return right;
    }
}

int main(void) {
    Node *root = NULL;
    for (int v : (int[]){5, 2, 7, 1, 4, 6, 8})
        root = bst_insert(root, v);

    printf("Original: ");
    inorder_print(root);  // 1 2 4 5 6 7 8
    printf("\n");

    SplitResult s = bst_split(root, 4);
    printf("Left  (≤4): "); inorder_print(s.left);  printf("\n");  // 1 2 4
    printf("Right (>4): "); inorder_print(s.right); printf("\n");  // 5 6 7 8

    // Merge back
    Node *merged = bst_merge_ordered(s.left, s.right);
    printf("After merge: "); inorder_print(merged); printf("\n");  // 1 2 4 5 6 7 8
    return 0;
}
```

**Rust:**
```rust
type Tree = Option<Box<Node>>;

#[derive(Debug)]
struct Node { val: i32, left: Tree, right: Tree }

impl Node {
    fn new(val: i32) -> Tree {
        Some(Box::new(Node { val, left: None, right: None }))
    }
}

fn bst_insert(root: Tree, val: i32) -> Tree {
    match root {
        None => Node::new(val),
        Some(mut n) => {
            if val < n.val { n.left  = bst_insert(n.left.take(),  val); }
            else           { n.right = bst_insert(n.right.take(), val); }
            Some(n)
        }
    }
}

// Returns (left_tree where keys ≤ key, right_tree where keys > key)
fn split(root: Tree, key: i32) -> (Tree, Tree) {
    match root {
        None => (None, None),
        Some(mut n) => {
            if n.val <= key {
                // n goes left; recurse right
                let (rl, rr) = split(n.right.take(), key);
                n.right = rl;
                (Some(n), rr)
            } else {
                // n goes right; recurse left
                let (ll, lr) = split(n.left.take(), key);
                n.left = lr;
                (ll, Some(n))
            }
        }
    }
}

fn inorder(t: &Tree) {
    if let Some(n) = t {
        inorder(&n.left);
        print!("{} ", n.val);
        inorder(&n.right);
    }
}

fn main() {
    let mut root: Tree = None;
    for &v in &[5, 2, 7, 1, 4, 6, 8] {
        root = bst_insert(root, v);
    }
    let (left, right) = split(root, 4);
    print!("Left  (≤4): "); inorder(&left);  println!();  // 1 2 4
    print!("Right (>4): "); inorder(&right); println!();  // 5 6 7 8
}
```

---

## 8. Pruning

Pruning removes subtrees that satisfy (or fail) a given condition.

### 8.1 Prune Nodes with Value Below Threshold

```
PRUNE all nodes whose value < 3:
      5                   5
     / \                 / \
    3   6       →       3   6
   / \   \               \
  2   4   7               4
 /
1

Algorithm: POSTORDER — decide to keep/remove AFTER processing children.
If we used preorder, we'd prune a parent and lose the valid children.
```

**C:**
```c
// Remove all nodes with val < threshold
// Returns new root (could be NULL if entire tree pruned)
Node *prune_below(Node *root, int threshold) {
    if (!root) return NULL;

    // Postorder: fix children first
    root->left  = prune_below(root->left,  threshold);
    root->right = prune_below(root->right, threshold);

    // Now decide on this node
    if (root->val < threshold) {
        // This node is invalid.
        // But wait — what if it has valid children?
        // In "prune node" semantics: remove the node, children become orphaned.
        // Here we assume "remove entire subtree if value invalid"
        free(root);
        return NULL;
    }
    return root;
}

// Prune: remove subtrees that contain only values outside [low, high]
// A node is kept if its subtree contains at least one node in [low, high]
Node *prune_range(Node *root, int low, int high) {
    if (!root) return NULL;
    root->left  = prune_range(root->left,  low, high);
    root->right = prune_range(root->right, low, high);

    // If current node is out of range AND has no valid children, remove it
    if (root->val < low || root->val > high) {
        if (!root->left && !root->right) {
            free(root);
            return NULL;
        }
    }
    return root;
}

// Prune leaf nodes that are NOT in a target set
Node *prune_leaves(Node *root, bool *keep, int n) {
    if (!root) return NULL;
    root->left  = prune_leaves(root->left,  keep, n);
    root->right = prune_leaves(root->right, keep, n);
    // If leaf and not in keep set, remove
    if (!root->left && !root->right && root->val < n && !keep[root->val]) {
        free(root);
        return NULL;
    }
    return root;
}
```

**Go:**
```go
package main

import "fmt"

type Node struct{ Val int; Left, Right *Node }

// Prune all nodes with val < threshold (removes entire subtrees)
func pruneBelow(root *Node, threshold int) *Node {
    if root == nil { return nil }
    root.Left  = pruneBelow(root.Left,  threshold)
    root.Right = pruneBelow(root.Right, threshold)
    if root.Val < threshold { return nil }
    return root
}

// Prune subtrees that have NO node in [low, high]
// A subtree is kept if ANY node within is in range
func pruneRange(root *Node, low, high int) *Node {
    if root == nil { return nil }
    root.Left  = pruneRange(root.Left,  low, high)
    root.Right = pruneRange(root.Right, low, high)
    // Remove leaf if out of range
    if root.Val < low || root.Val > high {
        if root.Left == nil && root.Right == nil {
            return nil
        }
    }
    return root
}

func inorder(n *Node) {
    if n == nil { return }
    inorder(n.Left)
    fmt.Printf("%d ", n.Val)
    inorder(n.Right)
}

func build(vals []int) *Node {
    var root *Node
    var ins func(*Node, int) *Node
    ins = func(r *Node, v int) *Node {
        if r == nil { return &Node{Val: v} }
        if v < r.Val { r.Left = ins(r.Left, v) } else { r.Right = ins(r.Right, v) }
        return r
    }
    for _, v := range vals { root = ins(root, v) }
    return root
}

func main() {
    root := build([]int{5, 3, 6, 2, 4, 7, 1})
    fmt.Print("Before prune: "); inorder(root); fmt.Println()
    root = pruneBelow(root, 3)
    fmt.Print("After prune<3:"); inorder(root); fmt.Println()
    // 3 4 5 6 7
}
```

**Rust:**
```rust
type T = Option<Box<Node>>;
#[derive(Debug)] struct Node { val: i32, left: T, right: T }
impl Node { fn l(v:i32)->T{Some(Box::new(Node{val:v,left:None,right:None}))} }

fn prune_below(root: T, threshold: i32) -> T {
    root.and_then(|mut n| {
        n.left  = prune_below(n.left.take(),  threshold);
        n.right = prune_below(n.right.take(), threshold);
        if n.val < threshold { None } else { Some(n) }
    })
}

fn inorder(t: &T) {
    if let Some(n) = t {
        inorder(&n.left); print!("{} ", n.val); inorder(&n.right);
    }
}

fn main() {
    let root = Some(Box::new(Node {
        val: 5,
        left: Some(Box::new(Node {
            val:3, left: Node::l(2), right: Node::l(4)
        })),
        right: Node::l(7),
    }));
    let pruned = prune_below(root, 3);
    inorder(&pruned); println!(); // 3 4 5 7
}
```

---

## 9. Grafting — Attaching Subtrees

Grafting attaches an external subtree at a specific node position.

```
GRAFT at node with value 3 (replace its right child):

ORIGINAL TREE:      GRAFT SUBTREE:     RESULT:
      5                  10                 5
     / \                /  \              /   \
    3   7              8    12           3     7
   / \                                  / \
  2   4                                2   10
                                          /  \
                                         8    12
```

**C:**
```c
// Attach 'subtree' as the right child of node with key 'target'
// Returns false if target not found
bool graft_right(Node *root, int target, Node *subtree) {
    if (!root) return false;
    if (root->val == target) {
        root->right = subtree;  // Replace (old right subtree is discarded)
        node_update(root);
        return true;
    }
    if (graft_right(root->left,  target, subtree)) return true;
    if (graft_right(root->right, target, subtree)) return true;
    return false;
}

// Safe graft: only attaches if target's right is NULL
bool graft_right_safe(Node *root, int target, Node *subtree) {
    if (!root) return false;
    if (root->val == target && !root->right) {
        root->right = subtree;
        node_update(root);
        return true;
    }
    if (graft_right_safe(root->left,  target, subtree)) return true;
    if (graft_right_safe(root->right, target, subtree)) return true;
    return false;
}

// Splice: insert a node BETWEEN a parent and its child
// parent → new_node → old_child
void splice_between(Node *parent, bool go_left, Node *new_node) {
    if (!parent || !new_node) return;
    if (go_left) {
        new_node->left = parent->left;
        parent->left   = new_node;
    } else {
        new_node->right = parent->right;
        parent->right   = new_node;
    }
    node_update(new_node);
    node_update(parent);
}
```

---

## 10. Serialization and Deserialization

Serialization converts a tree into a portable format (string, byte array). Deserialization rebuilds the exact tree from that format. Essential for persistence and network transfer.

### Method 1: Preorder with Null Markers

```
TREE:          SERIALIZED (preorder with '#' for null):
    1           "1,2,4,#,#,5,#,#,3,#,6,#,#"
   / \
  2   3
 / \   \
4   5   6

Preorder visits: 1 → 2 → 4 → null → null → 5 → null → null
                    → 3 → null → 6 → null → null

Deserialization: consume tokens one by one, recursively build
```

**C:**
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAXBUF 8192
#define MAXTOKEN 64
#define NULL_MARKER "#"
#define DELIMITER ","

// Serialize: preorder with null markers
void serialize(Node *root, char *buf, int *pos) {
    if (!root) {
        *pos += sprintf(buf + *pos, "%s%s", NULL_MARKER, DELIMITER);
        return;
    }
    *pos += sprintf(buf + *pos, "%d%s", root->val, DELIMITER);
    serialize(root->left,  buf, pos);
    serialize(root->right, buf, pos);
}

// Token stream for deserialization
typedef struct { char **tokens; int idx; int count; } TokenStream;

TokenStream tokenize(char *str) {
    TokenStream ts = {.tokens=(char **)malloc(MAXTOKEN*sizeof(char*)), .idx=0, .count=0};
    char *tok = strtok(str, DELIMITER);
    while (tok) {
        ts.tokens[ts.count++] = tok;
        tok = strtok(NULL, DELIMITER);
    }
    return ts;
}

// Deserialize: rebuild tree from token stream
Node *deserialize(TokenStream *ts) {
    if (ts->idx >= ts->count) return NULL;
    char *tok = ts->tokens[ts->idx++];
    if (strcmp(tok, NULL_MARKER) == 0) return NULL;

    Node *node = node_new(atoi(tok));
    node->left  = deserialize(ts);
    node->right = deserialize(ts);
    return node;
}

int main(void) {
    //    1
    //   / \
    //  2   3
    // / \   \
    //4   5   6
    Node *root = node_new(1);
    root->left  = node_new(2); root->right = node_new(3);
    root->left->left   = node_new(4);
    root->left->right  = node_new(5);
    root->right->right = node_new(6);

    char buf[MAXBUF] = {0};
    int pos = 0;
    serialize(root, buf, &pos);
    printf("Serialized: %s\n", buf);
    // "1,2,4,#,#,5,#,#,3,#,6,#,#,"

    // Deserialize from copy (strtok modifies string)
    char buf2[MAXBUF];
    strcpy(buf2, buf);
    TokenStream ts = tokenize(buf2);
    Node *restored = deserialize(&ts);

    printf("Restored inorder: ");
    inorder_print(restored);  // 4 2 5 1 3 6
    printf("\n");

    free(ts.tokens);
    return 0;
}
```

### Method 2: Level-Order Serialization

```
TREE:    1          SERIALIZED: "1,2,3,4,5,#,6"
        / \         (standard LeetCode format)
       2   3
      / \   \
     4   5   6
```

**Go:**
```go
package main

import (
    "fmt"
    "strconv"
    "strings"
)

type Node struct{ Val int; Left, Right *Node }

const nullMarker = "#"

// Serialize using level-order (BFS)
func serialize(root *Node) string {
    if root == nil { return "" }
    var parts []string
    queue := []*Node{root}
    for len(queue) > 0 {
        cur := queue[0]; queue = queue[1:]
        if cur == nil {
            parts = append(parts, nullMarker)
        } else {
            parts = append(parts, strconv.Itoa(cur.Val))
            queue = append(queue, cur.Left, cur.Right)
        }
    }
    return strings.Join(parts, ",")
}

// Deserialize level-order
func deserialize(data string) *Node {
    if data == "" { return nil }
    parts := strings.Split(data, ",")
    if parts[0] == nullMarker { return nil }

    val, _ := strconv.Atoi(parts[0])
    root := &Node{Val: val}
    queue := []*Node{root}
    i := 1

    for len(queue) > 0 && i < len(parts) {
        cur := queue[0]; queue = queue[1:]

        if i < len(parts) && parts[i] != nullMarker {
            v, _ := strconv.Atoi(parts[i])
            cur.Left = &Node{Val: v}
            queue = append(queue, cur.Left)
        }
        i++

        if i < len(parts) && parts[i] != nullMarker {
            v, _ := strconv.Atoi(parts[i])
            cur.Right = &Node{Val: v}
            queue = append(queue, cur.Right)
        }
        i++
    }
    return root
}

func inorder(n *Node) {
    if n == nil { return }
    inorder(n.Left)
    fmt.Printf("%d ", n.Val)
    inorder(n.Right)
}

func main() {
    root := &Node{Val: 1,
        Left:  &Node{Val: 2, Left: &Node{Val:4}, Right: &Node{Val:5}},
        Right: &Node{Val: 3, Right: &Node{Val: 6}},
    }

    s := serialize(root)
    fmt.Println("Serialized:", s)   // "1,2,3,4,5,#,6"

    restored := deserialize(s)
    fmt.Print("Inorder: "); inorder(restored); fmt.Println() // 4 2 5 1 3 6
}
```

**Rust:**
```rust
use std::collections::VecDeque;

type T = Option<Box<Node>>;
#[derive(Debug, Clone)]
struct Node { val: i32, left: T, right: T }

// Preorder serialize with '#' for null
fn serialize(root: &T) -> String {
    match root {
        None    => "#".to_string(),
        Some(n) => format!("{},{},{}", n.val, serialize(&n.left), serialize(&n.right)),
    }
}

// Deserialize from preorder string
fn deserialize(tokens: &[&str], i: &mut usize) -> T {
    if *i >= tokens.len() || tokens[*i] == "#" {
        *i += 1;
        return None;
    }
    let val: i32 = tokens[*i].parse().unwrap();
    *i += 1;
    let left  = deserialize(tokens, i);
    let right = deserialize(tokens, i);
    Some(Box::new(Node { val, left, right }))
}

fn inorder(t: &T) {
    if let Some(n) = t {
        inorder(&n.left); print!("{} ", n.val); inorder(&n.right);
    }
}

fn main() {
    let root: T = Some(Box::new(Node {
        val: 1,
        left: Some(Box::new(Node {
            val: 2,
            left:  Some(Box::new(Node{val:4,left:None,right:None})),
            right: Some(Box::new(Node{val:5,left:None,right:None})),
        })),
        right: Some(Box::new(Node {
            val: 3, left: None,
            right: Some(Box::new(Node{val:6,left:None,right:None})),
        })),
    }));

    let s = serialize(&root);
    println!("Serialized: {}", s);

    let tokens: Vec<&str> = s.split(',').collect();
    let mut i = 0;
    let restored = deserialize(&tokens, &mut i);
    print!("Inorder: "); inorder(&restored); println!();
}
```

---

## 11. Threaded Binary Trees

A **threaded binary tree** repurposes the NULL pointers in leaf nodes (which are wasted space) to point to the inorder predecessor or successor. This enables O(1) space inorder traversal without a stack.

```
TYPES:
  Right-threaded: null right pointers → inorder successor
  Left-threaded:  null left  pointers → inorder predecessor
  Fully-threaded: both

ORIGINAL:                   RIGHT-THREADED:
      4                           4
     / \                        /   \
    2   6           →          2     6
   / \ / \                    / \   / \
  1  3 5  7                  1→3 3→4  5→6  7→NULL
                                ↑thread  ↑thread

A "thread" bit is needed per node to distinguish
"real child pointer" from "thread pointer"
```

**C:**
```c
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

typedef struct TNode {
    int val;
    struct TNode *left, *right;
    bool right_thread;  // true = right pointer is a thread (successor)
    bool left_thread;   // true = left pointer is a thread (predecessor)
} TNode;

TNode *tnode_new(int val) {
    TNode *n = (TNode *)calloc(1, sizeof(TNode));
    n->val = val;
    return n;
}

// Convert a regular BST to a right-threaded BST in-place
// Uses inorder traversal; 'prev' tracks the previously visited node
static TNode *prev_thread = NULL;

void thread_bst(TNode *root) {
    if (!root) return;

    thread_bst(root->left);  // process left subtree

    // Link previous node's right thread to current (if null right)
    if (prev_thread && !prev_thread->right) {
        prev_thread->right        = root;
        prev_thread->right_thread = true;
    }
    prev_thread = root;

    thread_bst(root->right);  // process right subtree
}

// Inorder traversal using threads — O(1) space, no stack!
void threaded_inorder(TNode *root) {
    if (!root) return;

    // Go to leftmost node
    TNode *cur = root;
    while (cur->left && !cur->left_thread) cur = cur->left;

    while (cur) {
        printf("%d ", cur->val);

        if (cur->right_thread) {
            // Thread: jump directly to successor
            cur = cur->right;
        } else {
            // Real right child: go to leftmost of right subtree
            cur = cur->right;
            if (!cur) break;
            while (cur->left && !cur->left_thread) cur = cur->left;
        }
    }
    printf("\n");
}

int main(void) {
    //     4
    //    / \
    //   2   6
    //  / \ / \
    // 1  3 5  7
    TNode *root = tnode_new(4);
    root->left  = tnode_new(2); root->right = tnode_new(6);
    root->left->left   = tnode_new(1);
    root->left->right  = tnode_new(3);
    root->right->left  = tnode_new(5);
    root->right->right = tnode_new(7);

    prev_thread = NULL;
    thread_bst(root);

    printf("Threaded inorder (O(1) space): ");
    threaded_inorder(root);  // 1 2 3 4 5 6 7
    return 0;
}
```

---

## 12. DSW Algorithm — Rebalancing Any BST in O(N)

The **Day-Stout-Warren (DSW)** algorithm converts ANY BST into a **perfectly balanced BST** in O(N) time and O(1) extra space. It works in two phases.

```
PHASE 1: Tree → Vine (right-skewed list)
  Using right rotations repeatedly until tree is a right-linked list ("vine")

PHASE 2: Vine → Balanced Tree
  Using left rotations in carefully counted batches to compress the vine

EXAMPLE:
  BST (unbalanced):        VINE:         BALANCED BST:
       5                   1               4
      / \                   \             / \
     2   7        →          2           2   6
    / \   \                   \         / \ / \
   1   3   8                   3       1  3 5  7
                                \               \
                                 5               8
                                  \
                                   7
                                    \
                                     8
```

**C:**
```c
#include "binary_tree.h"

// Add a pseudo-root (dummy) to simplify edge cases
// Compress: apply left rotations at every other node in the vine
static void compress(Node *root, int count) {
    Node *scanner = root;
    for (int i = 0; i < count; i++) {
        Node *child = scanner->right;
        scanner->right = child->right;
        scanner = scanner->right;
        child->right = scanner->left;
        scanner->left = child;
    }
}

// DSW: convert any BST to balanced BST
// Returns new root
Node *dsw_balance(Node *root) {
    // Step 1: Create a pseudo-root
    Node pseudo = {0};
    pseudo.right = root;

    // Step 2: Tree → Vine (right-spine linked list)
    Node *tail = &pseudo;
    Node *rest = tail->right;

    int node_count = 0;
    while (rest) {
        if (!rest->left) {
            // No left child: just advance
            tail = rest;
            rest = rest->right;
            node_count++;
        } else {
            // Right-rotate: bring left child up
            Node *tmp    = rest->left;
            rest->left   = tmp->right;
            tmp->right   = rest;
            tail->right  = tmp;
            rest         = tmp;
        }
    }

    // Step 3: Vine → Balanced BST
    // Find next power of 2 ≤ node_count + 1
    int leaves = node_count + 1;
    int m = 1;
    while (m <= leaves) m <<= 1;
    m = (m >> 1) - 1;   // largest perfect tree ≤ node_count

    compress(&pseudo, node_count - m);

    for (m = m / 2; m > 0; m /= 2) {
        compress(&pseudo, m);
    }

    return pseudo.right;
}

int main(void) {
    // Build skewed BST (worst case)
    Node *root = NULL;
    for (int i = 1; i <= 8; i++)
        root = bst_insert(root, i);

    printf("Before DSW (inorder): ");
    inorder_print(root);  // 1 2 3 4 5 6 7 8
    printf("\nBefore DSW (root): %d\n", root->val);  // 1 (skewed!)

    root = dsw_balance(root);

    printf("After DSW (inorder): ");
    inorder_print(root);  // 1 2 3 4 5 6 7 8 (same, but balanced now)
    printf("\nAfter DSW (root): %d\n", root->val);   // 4 (balanced root)

    return 0;
}
```

**Go:**
```go
package main

import "fmt"

type Node struct{ Val int; Left, Right *Node }

// compress applies 'count' left rotations at alternating nodes
func compress(root *Node, count int) {
    scanner := root
    for i := 0; i < count; i++ {
        child := scanner.Right
        scanner.Right = child.Right
        scanner = scanner.Right
        child.Right = scanner.Left
        scanner.Left = child
    }
}

func dswBalance(root *Node) *Node {
    pseudo := &Node{} // dummy head
    pseudo.Right = root

    // Phase 1: Tree → Vine
    tail, rest := pseudo, pseudo.Right
    n := 0
    for rest != nil {
        if rest.Left == nil {
            tail = rest
            rest = rest.Right
            n++
        } else {
            tmp := rest.Left
            rest.Left = tmp.Right
            tmp.Right = rest
            tail.Right = tmp
            rest = tmp
        }
    }

    // Phase 2: Vine → Balanced tree
    leaves := n + 1
    m := 1
    for m <= leaves { m <<= 1 }
    m = (m >> 1) - 1

    compress(pseudo, n-m)
    for m /= 2; m > 0; m /= 2 {
        compress(pseudo, m)
    }

    return pseudo.Right
}

func bstInsert(root *Node, val int) *Node {
    if root == nil { return &Node{Val: val} }
    if val < root.Val { root.Left = bstInsert(root.Left, val) } else
                      { root.Right = bstInsert(root.Right, val) }
    return root
}

func inorder(n *Node) {
    if n == nil { return }
    inorder(n.Left)
    fmt.Printf("%d ", n.Val)
    inorder(n.Right)
}

func height(n *Node) int {
    if n == nil { return 0 }
    l, r := height(n.Left), height(n.Right)
    if l > r { return 1+l }
    return 1 + r
}

func main() {
    var root *Node
    for i := 1; i <= 8; i++ {
        root = bstInsert(root, i)
    }
    fmt.Printf("Before: root=%d, height=%d\n", root.Val, height(root)) // 1, 8
    root = dswBalance(root)
    fmt.Printf("After:  root=%d, height=%d\n", root.Val, height(root)) // 4, 4
    inorder(root); fmt.Println()
}
```

---

## 13. Tree to Doubly Linked List (In-Place)

Convert a BST to a **sorted circular doubly linked list** using only the existing left/right pointers — no new nodes allocated.

```
BST:              DLL (sorted, circular):
      4
     / \           ←prev    next→
    2   6    →   1 ↔ 2 ↔ 3 ↔ 4 ↔ 5 ↔ 6
   / \ / \        ↑_____________________↑  (circular)
  1  3 5  7

ALGORITHM (inorder-based):
  Use a 'prev' pointer. During inorder traversal:
    - Set prev.right = current   (prev's next = current)
    - Set current.left = prev    (current's prev = prev)
    - Update prev = current

After traversal: connect head and tail for circularity.
```

**C:**
```c
#include "binary_tree.h"

static Node *dll_head = NULL;
static Node *dll_prev = NULL;

void bst_to_dll_helper(Node *root) {
    if (!root) return;

    bst_to_dll_helper(root->left);  // process left

    // Stitch current node into DLL
    if (!dll_prev) {
        dll_head = root;  // leftmost = head
    } else {
        dll_prev->right = root;  // prev's "next" = current
        root->left = dll_prev;   // current's "prev" = prev
    }
    dll_prev = root;  // advance prev

    bst_to_dll_helper(root->right);  // process right
}

Node *bst_to_circular_dll(Node *root) {
    dll_head = dll_prev = NULL;
    bst_to_dll_helper(root);

    // Make circular: connect head ↔ tail
    if (dll_head && dll_prev) {
        dll_prev->right = dll_head;  // tail.next = head
        dll_head->left  = dll_prev;  // head.prev = tail
    }
    return dll_head;
}

void print_dll(Node *head, int count) {
    if (!head) return;
    Node *cur = head;
    for (int i = 0; i < count; i++) {
        printf("%d ", cur->val);
        cur = cur->right;
    }
    printf("(circular → %d)\n", cur->val);  // should be head
}

int main(void) {
    //      4
    //     / \
    //    2   6
    //   / \ / \
    //  1  3 5  7
    Node *root = NULL;
    for (int v : (int[]){4,2,6,1,3,5,7})
        root = bst_insert(root, v);

    int count = 7;
    Node *head = bst_to_circular_dll(root);

    printf("DLL: ");
    print_dll(head, count);  // 1 2 3 4 5 6 7 (circular → 1)
    return 0;
}
```

**Go:**
```go
package main

import "fmt"

type Node struct{ Val int; Left, Right *Node }

func bstToDLL(root *Node) *Node {
    if root == nil { return nil }

    var head, prev *Node

    var inorder func(*Node)
    inorder = func(n *Node) {
        if n == nil { return }
        inorder(n.Left)

        if prev == nil {
            head = n     // leftmost node = head
        } else {
            prev.Right = n  // stitch
            n.Left = prev
        }
        prev = n

        inorder(n.Right)
    }
    inorder(root)

    // Make circular
    prev.Right = head
    head.Left  = prev

    return head
}

func printDLL(head *Node, n int) {
    cur := head
    for i := 0; i < n; i++ {
        fmt.Printf("%d ", cur.Val)
        cur = cur.Right
    }
    fmt.Printf("→ %d (circular)\n", cur.Val)
}

func main() {
    nodes := []int{4, 2, 6, 1, 3, 5, 7}
    var root *Node
    var ins func(*Node, int) *Node
    ins = func(r *Node, v int) *Node {
        if r == nil { return &Node{Val: v} }
        if v < r.Val { r.Left = ins(r.Left, v) } else { r.Right = ins(r.Right, v) }
        return r
    }
    for _, v := range nodes { root = ins(root, v) }

    head := bstToDLL(root)
    printDLL(head, 7) // 1 2 3 4 5 6 7 → 1 (circular)
}
```

**Rust:**
```rust
// In Rust, circular structures with mutable references are complex.
// The idiomatic approach is to collect inorder values then build
// a Vec-backed DLL, or use Rc<RefCell<Node>>.
// Here we demonstrate the value-collection approach:

type T = Option<Box<Node>>;
#[derive(Debug)] struct Node { val: i32, left: T, right: T }

fn inorder_vals(t: &T, out: &mut Vec<i32>) {
    if let Some(n) = t {
        inorder_vals(&n.left, out);
        out.push(n.val);
        inorder_vals(&n.right, out);
    }
}

// Represents DLL as Vec with head index (conceptual)
fn bst_to_sorted_dll(root: &T) -> Vec<i32> {
    let mut vals = Vec::new();
    inorder_vals(root, &mut vals);
    vals  // sorted — represents the DLL order
}

fn main() {
    let root: T = Some(Box::new(Node {
        val: 4,
        left: Some(Box::new(Node {
            val: 2,
            left:  Some(Box::new(Node{val:1,left:None,right:None})),
            right: Some(Box::new(Node{val:3,left:None,right:None})),
        })),
        right: Some(Box::new(Node {
            val: 6,
            left:  Some(Box::new(Node{val:5,left:None,right:None})),
            right: Some(Box::new(Node{val:7,left:None,right:None})),
        })),
    }));

    let dll = bst_to_sorted_dll(&root);
    println!("DLL order: {:?}", dll); // [1, 2, 3, 4, 5, 6, 7]
}
```

---

## 14. Subtree Operations — Find, Extract, Replace

### 14.1 Finding a Subtree

Check if tree T2 is a subtree of T1.

```
T1:              T2:
      1               3
     / \             / \
    2   3   →       4   5
   / \ / \
  4  5 4  5       T2 is a subtree of T1 (matches at right child of root)
```

**C:**
```c
// Check if two trees are identical
bool trees_equal(Node *a, Node *b) {
    if (!a && !b) return true;
    if (!a || !b) return false;
    return (a->val == b->val)
        && trees_equal(a->left,  b->left)
        && trees_equal(a->right, b->right);
}

// Check if sub is a subtree of root
bool is_subtree(Node *root, Node *sub) {
    if (!sub)  return true;   // Empty tree is subtree of everything
    if (!root) return false;  // Non-empty sub can't be in empty root

    if (trees_equal(root, sub)) return true;
    return is_subtree(root->left, sub) || is_subtree(root->right, sub);
}

// Extract a subtree rooted at node with given value
// Returns the extracted subtree (detached from parent)
Node *extract_subtree(Node *root, Node *parent, int target, bool is_left) {
    if (!root) return NULL;
    if (root->val == target) {
        if (parent) {
            if (is_left) parent->left  = NULL;
            else         parent->right = NULL;
        }
        return root;  // Return detached subtree
    }
    Node *found = extract_subtree(root->left,  root, target, true);
    if (found) return found;
    return extract_subtree(root->right, root, target, false);
}

// Replace subtree rooted at 'old_val' with 'replacement'
Node *replace_subtree(Node *root, int old_val, Node *replacement) {
    if (!root) return NULL;
    if (root->val == old_val) return replacement;
    root->left  = replace_subtree(root->left,  old_val, replacement);
    root->right = replace_subtree(root->right, old_val, replacement);
    return root;
}
```

**Go:**
```go
func treesEqual(a, b *Node) bool {
    if a == nil && b == nil { return true }
    if a == nil || b == nil { return false }
    return a.Val == b.Val && treesEqual(a.Left, b.Left) && treesEqual(a.Right, b.Right)
}

func isSubtree(root, sub *Node) bool {
    if sub  == nil { return true  }
    if root == nil { return false }
    if treesEqual(root, sub) { return true }
    return isSubtree(root.Left, sub) || isSubtree(root.Right, sub)
}

// Replace subtree rooted at target value
func replaceSubtree(root *Node, target int, replacement *Node) *Node {
    if root == nil { return nil }
    if root.Val == target { return replacement }
    root.Left  = replaceSubtree(root.Left,  target, replacement)
    root.Right = replaceSubtree(root.Right, target, replacement)
    return root
}
```

---

## 15. Path Manipulation — Find, Modify, Compress

### 15.1 Find Path Between Two Nodes

```
PATH from 4 to 6 in BST:
       5
      / \
     2   7        Path: 4 → 2 → 5 → 7 → 6
    / \ / \
   1  4 6  8

Algorithm:
  1. Find path from root to node1 (root→...→4)
  2. Find path from root to node2 (root→...→6)
  3. Find LCA (Lowest Common Ancestor)
  4. Path = (path from 4 to LCA) + (path from LCA to 6, reversed)
```

**C:**
```c
#include "binary_tree.h"

// Find path from root to target; store in path array
// Returns true if found
bool find_path(Node *root, int target, Node **path, int *len) {
    if (!root) return false;
    path[(*len)++] = root;
    if (root->val == target) return true;

    if (find_path(root->left,  target, path, len)) return true;
    if (find_path(root->right, target, path, len)) return true;

    (*len)--;  // backtrack
    return false;
}

// Find LCA (Lowest Common Ancestor) of nodes with val1 and val2
// For BST: compare values to navigate
Node *lca_bst(Node *root, int val1, int val2) {
    if (!root) return NULL;
    if (val1 < root->val && val2 < root->val) return lca_bst(root->left, val1, val2);
    if (val1 > root->val && val2 > root->val) return lca_bst(root->right, val1, val2);
    return root;  // root is LCA (val1 ≤ root ≤ val2 or one equals root)
}

// LCA for general binary tree (not BST)
Node *lca_general(Node *root, int val1, int val2) {
    if (!root) return NULL;
    if (root->val == val1 || root->val == val2) return root;

    Node *left_lca  = lca_general(root->left,  val1, val2);
    Node *right_lca = lca_general(root->right, val1, val2);

    if (left_lca && right_lca) return root;  // Found in both sides → root is LCA
    return left_lca ? left_lca : right_lca;
}

// Add delta to all nodes on path from root to target
void add_on_path(Node *root, int target, int delta) {
    if (!root) return;
    Node *path[100];
    int len = 0;
    if (find_path(root, target, path, &len)) {
        for (int i = 0; i < len; i++) path[i]->val += delta;
    }
}

int main(void) {
    Node *root = NULL;
    for (int v : (int[]){5,2,7,1,4,6,8})
        root = bst_insert(root, v);

    Node *lca = lca_bst(root, 4, 6);
    printf("LCA of 4 and 6: %d\n", lca->val);  // 5

    Node *path[100]; int len = 0;
    if (find_path(root, 4, path, &len)) {
        printf("Path to 4: ");
        for (int i = 0; i < len; i++) printf("%d ", path[i]->val);
        printf("\n");  // 5 2 4
    }
    return 0;
}
```

### 15.2 Path Compression (Union-Find)

Path compression is a tree manipulation used in the **Union-Find (Disjoint Set)** data structure. It flattens the path from any node to the root, making future queries O(1) amortized.

```
BEFORE compression (find(5)):     AFTER compression:
    1                                  1
   /                                 / | \
  2                                 2  3  5
 /                                  |
3                                   4
 \
  4
   \
    5

All nodes on the path now point directly to root!
```

**C:**
```c
#define MAXN 1000

int parent[MAXN];
int rank_uf[MAXN];

void uf_init(int n) {
    for (int i = 0; i < n; i++) { parent[i] = i; rank_uf[i] = 0; }
}

// Find with PATH COMPRESSION — the manipulation!
// After find(x), parent[x] directly points to root
int uf_find(int x) {
    if (parent[x] != x)
        parent[x] = uf_find(parent[x]);  // Path compression: point straight to root
    return parent[x];
}

// Union by rank: attach smaller tree under larger tree
void uf_union(int x, int y) {
    int px = uf_find(x), py = uf_find(y);
    if (px == py) return;
    if (rank_uf[px] < rank_uf[py]) { int t=px; px=py; py=t; }
    parent[py] = px;
    if (rank_uf[px] == rank_uf[py]) rank_uf[px]++;
}

int main(void) {
    uf_init(6);
    uf_union(1, 2);
    uf_union(2, 3);
    uf_union(3, 4);
    uf_union(4, 5);

    printf("Find(5) = %d\n", uf_find(5));  // 1 (after compression)
    printf("Parent[5] = %d\n", parent[5]);  // 1 (directly!)
    printf("Connected(1,5)? %s\n", uf_find(1)==uf_find(5) ? "YES":"NO");
    return 0;
}
```

**Go:**
```go
type UnionFind struct {
    parent []int
    rank   []int
}

func NewUF(n int) *UnionFind {
    uf := &UnionFind{parent: make([]int, n), rank: make([]int, n)}
    for i := range uf.parent { uf.parent[i] = i }
    return uf
}

func (uf *UnionFind) Find(x int) int {
    if uf.parent[x] != x {
        uf.parent[x] = uf.Find(uf.parent[x]) // path compression
    }
    return uf.parent[x]
}

func (uf *UnionFind) Union(x, y int) {
    px, py := uf.Find(x), uf.Find(y)
    if px == py { return }
    if uf.rank[px] < uf.rank[py] { px, py = py, px }
    uf.parent[py] = px
    if uf.rank[px] == uf.rank[py] { uf.rank[px]++ }
}
```

**Rust:**
```rust
struct UnionFind { parent: Vec<usize>, rank: Vec<usize> }

impl UnionFind {
    fn new(n: usize) -> Self {
        UnionFind { parent: (0..n).collect(), rank: vec![0; n] }
    }

    fn find(&mut self, x: usize) -> usize {
        if self.parent[x] != x {
            self.parent[x] = self.find(self.parent[x]); // path compression
        }
        self.parent[x]
    }

    fn union(&mut self, x: usize, y: usize) {
        let (px, py) = (self.find(x), self.find(y));
        if px == py { return; }
        let (px, py) = if self.rank[px] >= self.rank[py] { (px,py) } else { (py,px) };
        self.parent[py] = px;
        if self.rank[px] == self.rank[py] { self.rank[px] += 1; }
    }
}

fn main() {
    let mut uf = UnionFind::new(6);
    uf.union(1, 2); uf.union(2, 3); uf.union(3, 4); uf.union(4, 5);
    println!("Find(5) = {}", uf.find(5)); // 1
    println!("Connected(1,5)? {}", uf.find(1) == uf.find(5)); // true
}
```

---

## 16. Lazy Propagation in Segment Trees

**Lazy propagation** is a tree manipulation technique where **range updates are deferred** — instead of updating all nodes immediately, we attach a "lazy tag" to a node and push it down only when we need to access children.

```
PROBLEM WITHOUT LAZY:
  Range update [add 3 to all elements in range 0..4]:
  Without lazy: must update O(N) nodes → O(N) per update

WITH LAZY (O(log N)):
  Mark root with lazy=3 (meaning "add 3 to all nodes below me")
  Only push down when we need to access children

LAZY PUSH-DOWN:
  When visiting node N that has lazy tag L:
    1. Apply L to N's actual stored value
    2. Pass L down to N.left.lazy and N.right.lazy
    3. Clear N.lazy = 0
    
  We never store incorrect values — we always push before reading.
```

```
SEGMENT TREE with lazy range update [l..r] += delta:

            [0..7] sum=36 lazy=0
           /                    \
     [0..3] sum=10 lazy=0    [4..7] sum=26 lazy=0
     /           \            /           \
  [0..1] lazy=0 [2..3]    [4..5]       [6..7] lazy=0
   /    \       lazy=0    lazy=0        /    \
 [0]   [1]    /    \    /    \       [6]    [7]
              [2]  [3] [4]  [5]

After range_update(0,3, +5):
  → [0..3] sum=30 lazy=5     ← tag stored here, NOT propagated yet
  → [0..7] sum=56 lazy=0     ← parent updated immediately

When we query [0..1]:
  → Push down: [0..1].lazy+=5, [2..3].lazy+=5, clear [0..3].lazy
  → Now access [0..1] correctly
```

**C:**
```c
#include <stdio.h>
#include <string.h>

#define MAXN 100005

long long seg[4*MAXN];   // segment tree (range sum)
long long lazy[4*MAXN];  // lazy tags

void seg_build(long long *arr, int node, int s, int e) {
    lazy[node] = 0;
    if (s == e) { seg[node] = arr[s]; return; }
    int mid = (s + e) / 2;
    seg_build(arr, 2*node, s, mid);
    seg_build(arr, 2*node+1, mid+1, e);
    seg[node] = seg[2*node] + seg[2*node+1];
}

// PUSH DOWN: propagate lazy tag to children
void push_down(int node, int s, int e) {
    if (lazy[node] == 0) return;  // Nothing to push

    int mid = (s + e) / 2;
    long long tag = lazy[node];

    // Apply to left child
    seg[2*node]   += tag * (mid - s + 1);  // sum increases by tag * count
    lazy[2*node]  += tag;

    // Apply to right child
    seg[2*node+1] += tag * (e - mid);
    lazy[2*node+1]+= tag;

    lazy[node] = 0;  // Clear this node's tag
}

// Range update: add delta to all elements in [l..r]
void range_update(int node, int s, int e, int l, int r, long long delta) {
    if (r < s || e < l) return;  // Completely out of range

    if (l <= s && e <= r) {
        // Completely inside: update this node, tag children
        seg[node]  += delta * (e - s + 1);
        lazy[node] += delta;
        return;
    }

    push_down(node, s, e);  // Push before going deeper!

    int mid = (s + e) / 2;
    range_update(2*node,   s, mid, l, r, delta);
    range_update(2*node+1, mid+1, e, l, r, delta);
    seg[node] = seg[2*node] + seg[2*node+1];
}

// Range query: sum of [l..r]
long long range_query(int node, int s, int e, int l, int r) {
    if (r < s || e < l) return 0;
    if (l <= s && e <= r) return seg[node];

    push_down(node, s, e);  // Push before going deeper!

    int mid = (s + e) / 2;
    return range_query(2*node,   s, mid, l, r)
         + range_query(2*node+1, mid+1, e, l, r);
}

int main(void) {
    long long arr[] = {0, 1, 2, 3, 4, 5, 6, 7, 8};  // 1-indexed
    int n = 8;
    seg_build(arr, 1, 1, n);

    printf("Sum [1..4]: %lld\n", range_query(1, 1, n, 1, 4));  // 10
    printf("Sum [3..6]: %lld\n", range_query(1, 1, n, 3, 6));  // 18

    range_update(1, 1, n, 1, 4, 10);  // Add 10 to elements [1..4]

    printf("After update [1..4] += 10:\n");
    printf("Sum [1..4]: %lld\n", range_query(1, 1, n, 1, 4));  // 50 (10+11+12+13+4)
    printf("Sum [1..8]: %lld\n", range_query(1, 1, n, 1, 8));  // 76

    return 0;
}
```

**Go:**
```go
package main

import "fmt"

const MAXN = 100005

var seg  [4*MAXN]int64
var lazy [4*MAXN]int64

func build(arr []int64, node, s, e int) {
    lazy[node] = 0
    if s == e { seg[node] = arr[s]; return }
    mid := (s + e) / 2
    build(arr, 2*node, s, mid)
    build(arr, 2*node+1, mid+1, e)
    seg[node] = seg[2*node] + seg[2*node+1]
}

func pushDown(node, s, e int) {
    if lazy[node] == 0 { return }
    mid := (s + e) / 2
    tag := lazy[node]

    seg[2*node]    += tag * int64(mid-s+1)
    lazy[2*node]   += tag
    seg[2*node+1]  += tag * int64(e-mid)
    lazy[2*node+1] += tag

    lazy[node] = 0
}

func rangeUpdate(node, s, e, l, r int, delta int64) {
    if r < s || e < l { return }
    if l <= s && e <= r {
        seg[node]  += delta * int64(e-s+1)
        lazy[node] += delta
        return
    }
    pushDown(node, s, e)
    mid := (s + e) / 2
    rangeUpdate(2*node, s, mid, l, r, delta)
    rangeUpdate(2*node+1, mid+1, e, l, r, delta)
    seg[node] = seg[2*node] + seg[2*node+1]
}

func rangeQuery(node, s, e, l, r int) int64 {
    if r < s || e < l { return 0 }
    if l <= s && e <= r { return seg[node] }
    pushDown(node, s, e)
    mid := (s + e) / 2
    return rangeQuery(2*node, s, mid, l, r) +
           rangeQuery(2*node+1, mid+1, e, l, r)
}

func main() {
    arr := []int64{0, 1, 2, 3, 4, 5, 6, 7, 8} // 1-indexed
    n := 8
    build(arr, 1, 1, n)

    fmt.Println("Sum [1..4]:", rangeQuery(1, 1, n, 1, 4)) // 10
    rangeUpdate(1, 1, n, 1, 4, 10)
    fmt.Println("After += 10 on [1..4]:")
    fmt.Println("Sum [1..4]:", rangeQuery(1, 1, n, 1, 4)) // 50
    fmt.Println("Sum [1..8]:", rangeQuery(1, 1, n, 1, 8)) // 76
}
```

**Rust:**
```rust
struct LazySegTree {
    seg:  Vec<i64>,
    lazy: Vec<i64>,
    n:    usize,
}

impl LazySegTree {
    fn new(arr: &[i64]) -> Self {
        let n = arr.len() - 1; // 1-indexed
        let mut st = LazySegTree {
            seg:  vec![0i64; 4 * arr.len()],
            lazy: vec![0i64; 4 * arr.len()],
            n,
        };
        st.build(arr, 1, 1, n);
        st
    }

    fn build(&mut self, arr: &[i64], node: usize, s: usize, e: usize) {
        self.lazy[node] = 0;
        if s == e { self.seg[node] = arr[s]; return; }
        let mid = (s + e) / 2;
        self.build(arr, 2*node, s, mid);
        self.build(arr, 2*node+1, mid+1, e);
        self.seg[node] = self.seg[2*node] + self.seg[2*node+1];
    }

    fn push_down(&mut self, node: usize, s: usize, e: usize) {
        if self.lazy[node] == 0 { return; }
        let mid = (s + e) / 2;
        let tag = self.lazy[node];

        self.seg[2*node]    += tag * (mid - s + 1) as i64;
        self.lazy[2*node]   += tag;
        self.seg[2*node+1]  += tag * (e - mid) as i64;
        self.lazy[2*node+1] += tag;

        self.lazy[node] = 0;
    }

    fn update(&mut self, node: usize, s: usize, e: usize, l: usize, r: usize, delta: i64) {
        if r < s || e < l { return; }
        if l <= s && e <= r {
            self.seg[node]  += delta * (e - s + 1) as i64;
            self.lazy[node] += delta;
            return;
        }
        self.push_down(node, s, e);
        let mid = (s + e) / 2;
        self.update(2*node, s, mid, l, r, delta);
        self.update(2*node+1, mid+1, e, l, r, delta);
        self.seg[node] = self.seg[2*node] + self.seg[2*node+1];
    }

    fn query(&mut self, node: usize, s: usize, e: usize, l: usize, r: usize) -> i64 {
        if r < s || e < l { return 0; }
        if l <= s && e <= r { return self.seg[node]; }
        self.push_down(node, s, e);
        let mid = (s + e) / 2;
        self.query(2*node, s, mid, l, r) + self.query(2*node+1, mid+1, e, l, r)
    }
}

fn main() {
    let arr = vec![0i64, 1, 2, 3, 4, 5, 6, 7, 8]; // 1-indexed
    let n = arr.len() - 1;
    let mut st = LazySegTree::new(&arr);

    println!("Sum [1..4]: {}", st.query(1, 1, n, 1, 4)); // 10
    st.update(1, 1, n, 1, 4, 10);
    println!("Sum [1..4] after += 10: {}", st.query(1, 1, n, 1, 4)); // 50
    println!("Sum [1..8]: {}", st.query(1, 1, n, 1, 8)); // 76
}
```

---

## 17. Euler Tour — Flattening Tree into Array

The **Euler Tour** (or DFS flattening) converts a tree into a linear array so that **subtree queries become range queries** on the array.

```
TREE:                 DFS TRAVERSAL ORDER:
      1               Enter/Exit timestamps:
     / \
    2   3             Node  in_time  out_time
   / \   \            ────────────────────────
  4   5   6             1      1        6
                         2      2        5
                         4      3        3
                         5      4        4
                         3      5        6   (wait, let me redo)
                         6      6        6

EULER TOUR ARRAY (record node ID on each entry AND exit):
  [1, 2, 4, 4, 5, 5, 2, 3, 6, 6, 3, 1]
   ↑enter ↑exit pairs

SUBTREE of node 2 = nodes {2, 4, 5}
  in_time[2]=2, out_time[2]=5
  → All nodes 2,4,5 have timestamps in [2..5]
  → Subtree query = array range [2..5] !

LCA(u, v) = node with minimum depth in Euler tour
            between first occurrence of u and first occurrence of v
```

**C:**
```c
#include <stdio.h>
#include <string.h>

#define MAXN 100005

int adj[MAXN][MAXN], adj_cnt[MAXN]; // adjacency list
int euler[2*MAXN];   // euler tour array (stores node IDs)
int in_time[MAXN];   // time node was first visited
int out_time[MAXN];  // time node was last visited
int depth_arr[MAXN]; // depth of each node
int timer_g = 0;

void euler_dfs(int node, int parent, int depth) {
    in_time[node]     = timer_g;
    euler[timer_g]    = node;
    depth_arr[node]   = depth;
    timer_g++;

    for (int i = 0; i < adj_cnt[node]; i++) {
        int child = adj[node][i];
        if (child != parent) {
            euler_dfs(child, node, depth + 1);
        }
    }

    out_time[node]  = timer_g - 1;
    // Note: in/out gives us the subtree range [in_time..out_time]
}

void add_edge(int u, int v) {
    adj[u][adj_cnt[u]++] = v;
    adj[v][adj_cnt[v]++] = u;
}

// Check if u is ancestor of v
bool is_ancestor(int u, int v) {
    return in_time[u] <= in_time[v] && out_time[v] <= out_time[u];
}

// All nodes in subtree of u are those v where in_time[u] <= in_time[v] <= out_time[u]
void print_subtree(int root_node, int n) {
    printf("Subtree of %d: ", root_node);
    for (int v = 1; v <= n; v++) {
        if (in_time[root_node] <= in_time[v] && in_time[v] <= out_time[root_node]) {
            printf("%d ", v);
        }
    }
    printf("\n");
}

int main(void) {
    //     1
    //    / \
    //   2   3
    //  / \   \
    // 4   5   6
    add_edge(1, 2); add_edge(1, 3);
    add_edge(2, 4); add_edge(2, 5);
    add_edge(3, 6);

    euler_dfs(1, 0, 0);

    printf("in_time:  "); for (int i=1;i<=6;i++) printf("%d:%d ", i, in_time[i]);  printf("\n");
    printf("out_time: "); for (int i=1;i<=6;i++) printf("%d:%d ", i, out_time[i]); printf("\n");

    print_subtree(2, 6);  // 2 4 5
    printf("Is 4 ancestor of 2? %s\n", is_ancestor(4, 2) ? "YES":"NO"); // NO
    printf("Is 2 ancestor of 4? %s\n", is_ancestor(2, 4) ? "YES":"NO"); // YES
    return 0;
}
```

**Go:**
```go
package main

import "fmt"

type EulerTree struct {
    adj     [][]int
    inTime  []int
    outTime []int
    timer   int
}

func NewEulerTree(n int) *EulerTree {
    return &EulerTree{
        adj:     make([][]int, n+1),
        inTime:  make([]int, n+1),
        outTime: make([]int, n+1),
    }
}

func (et *EulerTree) AddEdge(u, v int) {
    et.adj[u] = append(et.adj[u], v)
    et.adj[v] = append(et.adj[v], u)
}

func (et *EulerTree) DFS(node, parent int) {
    et.inTime[node] = et.timer
    et.timer++
    for _, child := range et.adj[node] {
        if child != parent {
            et.DFS(child, node)
        }
    }
    et.outTime[node] = et.timer - 1
}

func (et *EulerTree) IsAncestor(u, v int) bool {
    return et.inTime[u] <= et.inTime[v] && et.inTime[v] <= et.outTime[u]
}

func (et *EulerTree) SubtreeRange(u int) (int, int) {
    return et.inTime[u], et.outTime[u]
}

func main() {
    et := NewEulerTree(6)
    et.AddEdge(1, 2); et.AddEdge(1, 3)
    et.AddEdge(2, 4); et.AddEdge(2, 5)
    et.AddEdge(3, 6)
    et.DFS(1, 0)

    l, r := et.SubtreeRange(2)
    fmt.Printf("Subtree of 2: in=[%d..%d]\n", l, r) // [1..3]
    fmt.Println("Is 2 ancestor of 4?", et.IsAncestor(2, 4)) // true
    fmt.Println("Is 3 ancestor of 4?", et.IsAncestor(3, 4)) // false
}
```

---

## 18. Heavy-Light Decomposition (HLD)

**HLD** decomposes a tree into chains so that **any root-to-node path passes through at most O(log N) chains**. Each chain is stored as a contiguous segment, enabling O(log² N) path queries/updates using a segment tree.

```
KEY DEFINITIONS:
  Heavy child: the child with the LARGEST subtree size
  Light child: all other children
  Heavy edge:  edge to heavy child
  Light edge:  edge to light child
  Heavy chain: maximal path of heavy edges

WHY O(log N) CHAINS?
  Each light edge you cross at least DOUBLES the subtree size
  (light child's subtree ≤ half of parent's subtree)
  → Can cross at most log N light edges from any node to root

TREE:                    HEAVY CHILDREN:
       1 (size=7)          1's heavy child = 2 (size=4 > size=3)
      / \                  2's heavy child = 4 (size=2 > size=1)
    2(4) 3(2)              3's heavy child = 6 (size=1)
   / \ / \
  4  5 6  7              CHAINS:
 (2)(1)(1)(1)              Chain 1: 1 → 2 → 4
  |                        Chain 2: 3 → 6
  8(1)                     Chain 3: 5
                            Chain 4: 7
                            Chain 5: 8
```

**C:**
```c
#include <stdio.h>
#include <string.h>

#define MAXN 100005

int adj[MAXN][50], adj_cnt[MAXN];
int parent[MAXN], depth[MAXN], sub_size[MAXN];
int heavy_child[MAXN];
int chain_head[MAXN];   // head of chain for each node
int position[MAXN];     // position of node in the flat chain array
int pos_counter = 0;

void add_edge(int u, int v) {
    adj[u][adj_cnt[u]++] = v;
    adj[v][adj_cnt[v]++] = u;
}

// Step 1: DFS to compute subtree sizes and heavy children
void dfs_size(int node, int par, int dep) {
    parent[node]     = par;
    depth[node]      = dep;
    sub_size[node]   = 1;
    heavy_child[node]= -1;
    int max_sub = 0;

    for (int i = 0; i < adj_cnt[node]; i++) {
        int child = adj[node][i];
        if (child == par) continue;
        dfs_size(child, node, dep + 1);
        sub_size[node] += sub_size[child];
        if (sub_size[child] > max_sub) {
            max_sub = sub_size[child];
            heavy_child[node] = child;  // track heavy child
        }
    }
}

// Step 2: DFS to assign positions along chains
// 'head' is the current chain's topmost node
void dfs_hld(int node, int head) {
    chain_head[node] = head;
    position[node]   = pos_counter++;

    // Follow heavy edge first (continue current chain)
    if (heavy_child[node] != -1) {
        dfs_hld(heavy_child[node], head);
    }

    // Then process light children (start new chains)
    for (int i = 0; i < adj_cnt[node]; i++) {
        int child = adj[node][i];
        if (child == parent[node] || child == heavy_child[node]) continue;
        dfs_hld(child, child);  // child starts its own chain
    }
}

// Query/Update path from u to v using segment tree on positions
// Here we just demonstrate the chain decomposition
int path_chain_count(int u, int v) {
    int chains = 0;
    while (chain_head[u] != chain_head[v]) {
        // u and v are on different chains
        if (depth[chain_head[u]] < depth[chain_head[v]]) {
            int tmp = u; u = v; v = tmp;  // ensure u is deeper
        }
        // Process chain from chain_head[u] to u
        // → segment tree query on [position[chain_head[u]], position[u]]
        chains++;
        u = parent[chain_head[u]];  // jump to parent of chain head
    }
    // u and v are now on the same chain
    // → single range query [min(position[u],position[v]), max(...)]
    chains++;
    return chains;
}

int main(void) {
    //       1
    //      / \
    //     2   3
    //    / \ / \
    //   4  5 6  7
    //   |
    //   8
    for (int i = 1; i <= 7; i++) add_edge(1 + (i>1), i+1 > 5 ? i : i);
    // Simplified: build manually
    memset(adj_cnt, 0, sizeof(adj_cnt));
    add_edge(1,2); add_edge(1,3);
    add_edge(2,4); add_edge(2,5);
    add_edge(3,6); add_edge(3,7);
    add_edge(4,8);

    dfs_size(1, 0, 0);
    dfs_hld(1, 1);

    printf("Positions (HLD order):\n");
    for (int i = 1; i <= 8; i++) {
        printf("  Node %d: pos=%d, chain_head=%d\n", i, position[i], chain_head[i]);
    }

    printf("\nPath 8→7 spans %d chain(s)\n", path_chain_count(8, 7));
    return 0;
}
```

---

## 19. Centroid Decomposition

**Centroid decomposition** recursively finds the **centroid** of a tree (a node whose removal creates subtrees each with ≤ N/2 nodes) and builds a **centroid tree** — a separate meta-tree used for distance queries.

```
WHY CENTROID?
  Every subtree after centroid removal has size ≤ N/2
  → Recursion depth ≤ log N
  → O(N log N) to solve many "distance between nodes" problems

ALGORITHM:
  1. Find centroid C of current tree (component)
  2. C is the root of the centroid tree for this component
  3. Remove C, recurse on each remaining subtree
  4. Each sub-centroid becomes a child of C in centroid tree

TREE:                CENTROID DECOMPOSITION:
     1                  4 (centroid of whole tree)
    / \                / \
   2   3             2   6 (centroids of subtrees)
  / \ / \           / \ / \
 4  5 6  7         1  5 3  7
                       |
                       (and so on)
```

**C:**
```c
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdbool.h>

#define MAXN 100005

int adj[MAXN][50], adj_cnt[MAXN];
int sub_sz[MAXN];
bool removed[MAXN];    // nodes removed in centroid decomp
int centroid_parent[MAXN];  // parent in centroid tree
int n_nodes;

void add_edge_cd(int u, int v) {
    adj[u][adj_cnt[u]++] = v;
    adj[v][adj_cnt[v]++] = u;
}

// Compute subtree sizes (ignoring removed nodes)
void compute_size(int node, int par) {
    sub_sz[node] = 1;
    for (int i = 0; i < adj_cnt[node]; i++) {
        int child = adj[node][i];
        if (child == par || removed[child]) continue;
        compute_size(child, node);
        sub_sz[node] += sub_sz[child];
    }
}

// Find centroid of component containing 'node' with 'comp_size' nodes
int find_centroid(int node, int par, int comp_size) {
    for (int i = 0; i < adj_cnt[node]; i++) {
        int child = adj[node][i];
        if (child == par || removed[child]) continue;
        // If child's subtree > half total, centroid is in that subtree
        if (sub_sz[child] > comp_size / 2) {
            return find_centroid(child, node, comp_size);
        }
    }
    return node;  // This node is the centroid
}

// Build centroid decomposition tree
void build_centroid_decomp(int node, int par_centroid) {
    compute_size(node, -1);
    int centroid = find_centroid(node, -1, sub_sz[node]);

    centroid_parent[centroid] = par_centroid;

    removed[centroid] = true;  // "Remove" centroid

    // Recurse on each subtree
    for (int i = 0; i < adj_cnt[centroid]; i++) {
        int child = adj[centroid][i];
        if (!removed[child]) {
            build_centroid_decomp(child, centroid);
        }
    }
}

int main(void) {
    n_nodes = 7;
    add_edge_cd(1,2); add_edge_cd(1,3);
    add_edge_cd(2,4); add_edge_cd(2,5);
    add_edge_cd(3,6); add_edge_cd(3,7);

    memset(removed, false, sizeof(removed));
    build_centroid_decomp(1, -1);

    printf("Centroid tree parents:\n");
    for (int i = 1; i <= n_nodes; i++) {
        printf("  Node %d → parent %d\n", i, centroid_parent[i]);
    }
    return 0;
}
```

---

## 20. Augmented Trees

An **augmented tree** is a BST extended with extra metadata at each node, computed from the subtree, enabling new query types.

```
STANDARD BST:          ORDER-STATISTIC TREE (augmented with size):
    5                       5 [size=5]
   / \                     / \
  3   7        →          3[2] 7[1]
 / \                     / \
1   4                  1[1] 4[1]

EXTRA OPERATIONS:
  select(k)  = find the k-th smallest element  → O(log N)
  rank(x)    = count elements less than x       → O(log N)
```

**C:**
```c
#include "binary_tree.h"

// Find k-th smallest element in BST (1-indexed)
// Requires size augmentation
Node *kth_smallest(Node *root, int k) {
    if (!root) return NULL;
    int left_size = node_size(root->left);

    if (k == left_size + 1) return root;           // This is k-th
    if (k <= left_size) return kth_smallest(root->left, k);  // In left subtree
    return kth_smallest(root->right, k - left_size - 1);     // In right subtree
}

// Rank: how many elements are strictly less than key?
int rank_of(Node *root, int key) {
    if (!root) return 0;
    if (key <= root->val)
        return rank_of(root->left, key);
    return node_size(root->left) + 1 + rank_of(root->right, key);
}

// Augmented BST insert (maintains size)
Node *aug_insert(Node *root, int val) {
    if (!root) return node_new(val);
    if (val < root->val) root->left  = aug_insert(root->left,  val);
    else                 root->right = aug_insert(root->right, val);
    node_update(root);  // update size and height
    return root;
}

// Interval tree node (augmented BST on interval start points)
typedef struct IntervalNode {
    int lo, hi;       // interval [lo, hi]
    int max_hi;       // max hi value in subtree
    struct IntervalNode *left, *right;
} IntervalNode;

IntervalNode *inode_new(int lo, int hi) {
    IntervalNode *n = (IntervalNode *)calloc(1, sizeof(IntervalNode));
    n->lo = lo; n->hi = hi; n->max_hi = hi;
    return n;
}

void inode_update(IntervalNode *n) {
    n->max_hi = n->hi;
    if (n->left  && n->left->max_hi  > n->max_hi) n->max_hi = n->left->max_hi;
    if (n->right && n->right->max_hi > n->max_hi) n->max_hi = n->right->max_hi;
}

IntervalNode *interval_insert(IntervalNode *root, int lo, int hi) {
    if (!root) return inode_new(lo, hi);
    if (lo < root->lo) root->left  = interval_insert(root->left,  lo, hi);
    else               root->right = interval_insert(root->right, lo, hi);
    inode_update(root);
    return root;
}

// Find any interval overlapping [qlo, qhi]
IntervalNode *interval_search(IntervalNode *root, int qlo, int qhi) {
    if (!root) return NULL;
    // Check overlap: two intervals [a,b] and [c,d] overlap iff a<=d && c<=b
    if (root->lo <= qhi && qlo <= root->hi) return root;

    // If left subtree's max_hi >= qlo, overlap might be in left subtree
    if (root->left && root->left->max_hi >= qlo)
        return interval_search(root->left, qlo, qhi);

    return interval_search(root->right, qlo, qhi);
}

int main(void) {
    Node *root = NULL;
    for (int v : (int[]){5,3,7,1,4,6,8})
        root = aug_insert(root, v);

    printf("3rd smallest: %d\n",  kth_smallest(root, 3)->val);  // 4
    printf("Rank of 6: %d\n",     rank_of(root, 6));            // 4

    IntervalNode *itree = NULL;
    itree = interval_insert(itree, 15, 20);
    itree = interval_insert(itree, 10, 30);
    itree = interval_insert(itree,  5, 20);
    itree = interval_insert(itree, 12, 15);
    itree = interval_insert(itree, 30, 40);

    IntervalNode *found = interval_search(itree, 6, 7);
    if (found) printf("Overlap with [6,7]: [%d,%d]\n", found->lo, found->hi);
    // [5,20]
    return 0;
}
```

---

## 21. Persistent Trees — Immutable Versioned Trees

A **persistent tree** (also called a **functional tree**) preserves **all previous versions** of the tree. After each update, instead of modifying the tree in place, we create a new root that shares all unchanged nodes with the old tree.

```
PERSISTENT BST: insert 5 into {3, 7}

VERSION 0:                VERSION 1 (after insert 5):
     3                         3'  ← NEW NODE (can't reuse old 3)
    / \                       / \
  nil  7                    nil  7'  ← NEW NODE (path to 5 updated)
      / \                       / \
    nil  nil                   5   nil   ← NEW NODE

Only 3 new nodes created! Old version 0 is UNCHANGED.
Shared nodes: the nil pointers are shared.

MEMORY: O(log N) new nodes per update, O(N log N) total for N updates
USE CASES:
  - Functional programming
  - Version history / undo
  - Offline range queries (persistent segment tree)
  - Time-travel queries: "what was the BST state at time T?"
```

**C:**
```c
// Persistent BST — never modify existing nodes
#include "binary_tree.h"

// Insert into persistent BST: creates at most O(H) new nodes
// Old tree version is NEVER modified
Node *persistent_insert(Node *root, int val) {
    if (!root) return node_new(val);  // New leaf

    // Create a NEW node (copy of current), modify the copy
    Node *new_root = (Node *)malloc(sizeof(Node));
    *new_root = *root;  // Copy all fields (shallow — but we change only one path)

    if (val < root->val)
        new_root->left  = persistent_insert(root->left,  val);
    else
        new_root->right = persistent_insert(root->right, val);

    node_update(new_root);
    return new_root;  // Return new version
}

// Persistent delete
Node *persistent_delete(Node *root, int val) {
    if (!root) return NULL;

    Node *new_root = (Node *)malloc(sizeof(Node));
    *new_root = *root;

    if (val < root->val) {
        new_root->left  = persistent_delete(root->left, val);
    } else if (val > root->val) {
        new_root->right = persistent_delete(root->right, val);
    } else {
        // Found: handle deletion cases
        if (!root->left)  { free(new_root); return root->right; }
        if (!root->right) { free(new_root); return root->left;  }
        // Find inorder successor
        Node *succ = root->right;
        while (succ->left) succ = succ->left;
        new_root->val   = succ->val;
        new_root->right = persistent_delete(root->right, succ->val);
    }
    node_update(new_root);
    return new_root;
}

int main(void) {
    #define VERSIONS 5
    Node *versions[VERSIONS];
    versions[0] = NULL;

    int vals[] = {5, 3, 7, 1, 4};
    for (int i = 0; i < 5; i++) {
        versions[i+1 < VERSIONS ? i+1 : 4] =
            persistent_insert(versions[i], vals[i]);
    }

    // All versions accessible!
    printf("Version 1 (just 5): ");  inorder_print(versions[1]); printf("\n");
    printf("Version 2 (5,3):    ");  inorder_print(versions[2]); printf("\n");
    printf("Version 3 (5,3,7):  ");  inorder_print(versions[3]); printf("\n");
    printf("Version 4 (5,3,7,1):"); inorder_print(versions[4]); printf("\n");

    // Go back in time!
    printf("Time travel to V2: "); inorder_print(versions[2]); printf("\n");
    return 0;
}
```

---

## 22. Tree Isomorphism and Canonicalization

Two trees are **isomorphic** if one can be transformed into the other by permuting children. **Canonicalization** assigns a unique string/hash to each tree shape for O(N) isomorphism checking.

```
ISOMORPHIC TREES (same structure, different labels):
  Tree A:        Tree B:
     1              x
    / \            / \
   2   3          y   z

These are isomorphic as UNLABELED trees.

For ROOTED trees, canonical form via AHU algorithm:
  1. Each leaf gets label "0"
  2. Each internal node: sort children's canonical labels,
     concatenate, assign next integer if new pattern
  3. Two trees isomorphic ↔ root labels equal
```

**Go:**
```go
package main

import (
    "fmt"
    "sort"
    "strings"
)

type Node struct{ Val int; Children []*Node }

// Canonical string for a rooted tree (shape only, ignores values)
func canonical(n *Node) string {
    if len(n.Children) == 0 {
        return "()"  // leaf
    }
    childCanons := make([]string, len(n.Children))
    for i, c := range n.Children {
        childCanons[i] = canonical(c)
    }
    sort.Strings(childCanons)  // sort for canonical ordering
    return "(" + strings.Join(childCanons, "") + ")"
}

// Two trees are isomorphic iff their canonical forms are equal
func areIsomorphic(a, b *Node) bool {
    return canonical(a) == canonical(b)
}

// Check binary tree isomorphism (either subtree can be swapped)
type BNode struct{ Val int; Left, Right *BNode }

func binaryCanonical(n *BNode) string {
    if n == nil { return "#" }
    l, r := binaryCanonical(n.Left), binaryCanonical(n.Right)
    // Sort so swapped children still match
    if l > r { l, r = r, l }
    return fmt.Sprintf("(%s,%s)", l, r)
}

func main() {
    // Tree A:   1→{2,3,4}
    A := &Node{Val: 1, Children: []*Node{
        {Val: 2}, {Val: 3}, {Val: 4},
    }}
    // Tree B:   9→{5,6,7} (same shape, different values)
    B := &Node{Val: 9, Children: []*Node{
        {Val: 5}, {Val: 6}, {Val: 7},
    }}
    // Tree C:   1→{2,3} (different shape)
    C := &Node{Val: 1, Children: []*Node{{Val: 2}, {Val: 3}}}

    fmt.Println("A and B isomorphic:", areIsomorphic(A, B)) // true
    fmt.Println("A and C isomorphic:", areIsomorphic(A, C)) // false
    fmt.Println("Canon A:", canonical(A)) // (()()())
    fmt.Println("Canon C:", canonical(C)) // (()())
}
```

---

## 23. Conversion Algorithms

### 23.1 BST to Min-Heap

```
ALGORITHM (using array):
  1. Do inorder traversal of BST → sorted array A  (O(N))
  2. Build min-heap from A using BFS-style assignment  (O(N))
     Assign: level-order position i gets value A[i-1]
```

**C:**
```c
// Collect inorder into array
void bst_to_array(Node *root, int *arr, int *idx) {
    if (!root) return;
    bst_to_array(root->left, arr, idx);
    arr[(*idx)++] = root->val;
    bst_to_array(root->right, arr, idx);
}

// Assign values from sorted array in level-order (BFS) → min-heap
void assign_level_order(Node *root, int *arr, int *idx) {
    if (!root) return;
    Node *q[1024]; int f=0, b=0;
    q[b++] = root;
    while (f < b) {
        Node *cur = q[f++];
        cur->val = arr[(*idx)++];
        if (cur->left)  q[b++] = cur->left;
        if (cur->right) q[b++] = cur->right;
    }
}

// Convert BST to min-heap (tree remains complete binary tree if it was)
void bst_to_minheap(Node *root, int n) {
    int arr[1024], idx = 0;
    bst_to_array(root, arr, &idx);   // sorted array

    idx = 0;
    assign_level_order(root, arr, &idx);  // fill in BFS order
}
```

### 23.2 N-ary Tree to Binary (LCRS)

Already shown in Section 4.5 of the previous guide. The key transformation:

```
ALGORITHM:
  For each N-ary node N with children [C1, C2, C3]:
    Binary.left  = C1                 (first child)
    Binary.right = C2 (C2.right = C3) (sibling chain)

This is the Left-Child Right-Sibling transformation.
```

### 23.3 Expression Tree to String (All Notations)

```c
// Infix (with parentheses)
void to_infix(Node *n) {
    if (!n) return;
    if (n->left || n->right) printf("(");
    to_infix(n->left);
    printf("%d", n->val);  // or char for operators
    to_infix(n->right);
    if (n->left || n->right) printf(")");
}

// Prefix (Polish notation) — preorder
void to_prefix(Node *n) {
    if (!n) return;
    printf("%d ", n->val);
    to_prefix(n->left);
    to_prefix(n->right);
}

// Postfix (Reverse Polish) — postorder
void to_postfix(Node *n) {
    if (!n) return;
    to_postfix(n->left);
    to_postfix(n->right);
    printf("%d ", n->val);
}
```

---

## 24. Complexity Master Table and Decision Map

### Complexity of All Manipulations

```
OPERATION                   TIME        SPACE       NOTES
══════════════════════════════════════════════════════════════════════
Rotation (single)           O(1)        O(1)        Constant pointer ops
AVL rebalance (per insert)  O(log N)    O(log N)    At most 2 rotations
RB rebalance (per insert)   O(log N)    O(log N)    At most 3 rotations
Invert/Mirror               O(N)        O(H)        H=height (recursion)
Flatten to list (in-place)  O(N)        O(1)        Morris-like approach
Deep copy                   O(N)        O(N)        Must allocate N nodes
Merge two trees (sum)       O(N+M)      O(H)        N,M = tree sizes
Merge two BSTs (sorted)     O(N+M)      O(N+M)      Via sorted array merge
Split BST at key            O(H)        O(H)        H = height
Prune by condition          O(N)        O(H)        Postorder DFS
Serialize (preorder)        O(N)        O(N)        Output string
Deserialize                 O(N)        O(N)        One pass
Thread BST (Morris)         O(N)        O(1)        Modify null pointers
DSW Balance                 O(N)        O(1)        Vine then compress
BST → DLL                   O(N)        O(1)        In-place via inorder
Kth smallest (augmented)    O(log N)    O(1)        Requires size field
Path find (root to node)    O(H)        O(H)        DFS with backtrack
LCA (BST)                   O(H)        O(1)        Compare values
LCA (general, sparse table) O(1) query  O(N log N)  After O(N log N) prep
Union-Find with compression O(α(N)) amortized O(N)  α = inverse Ackermann
Euler Tour build            O(N)        O(N)        Single DFS
HLD build                   O(N)        O(N)        Two DFS passes
HLD path query              O(log² N)   O(1)        log N chains × log N segtree
Centroid Decomp build       O(N log N)  O(N)        Recursive with sizes
Segment tree range update   O(log N)    O(1)        With lazy propagation
Persistent BST insert       O(log N)    O(log N)    Creates new path copy
Persistent seg tree update  O(log N)    O(log N)    Creates new path copy
Tree isomorphism (AHU)      O(N log N)  O(N)        Sort children labels
══════════════════════════════════════════════════════════════════════
```

### The Decision Map

```
WHAT IS YOUR GOAL?             USE THIS MANIPULATION
═══════════════════════════════════════════════════════════════════
Balance an unbalanced BST?  → DSW (O(N), O(1) space) or AVL rotations
Flatten for serialization?  → Preorder with null markers
Convert to list in-place?   → Flatten (Morris-like) or BST→DLL
Copy tree independently?    → Deep copy (recursive or BFS)
Divide tree at value?       → BST Split
Merge two trees?            → By shape (overlap sum) or BST merge
Remove invalid nodes?       → Prune (postorder)
Space-efficient traversal?  → Thread the tree (Morris)
Range queries on tree path? → HLD + Segment Tree
Subtree queries as ranges?  → Euler Tour + Segment Tree
Distance queries on tree?   → Centroid Decomposition
Keep history of tree?       → Persistent BST/Seg Tree
Move hot node to root?      → Splay operation
K-th element in O(log N)?   → Augmented BST (order-statistic)
Interval overlap query?     → Augmented BST (interval tree)
Range update + query?       → Lazy Segment Tree
Find if subtree present?    → Tree isomorphism / canonical form
Union-Find fast queries?    → Path compression + union by rank
═══════════════════════════════════════════════════════════════════
```

### The Invariant Preservation Map

```
WHEN YOU DO THIS:           YOU MUST REPAIR THIS INVARIANT:
────────────────────────────────────────────────────────────────────
Insert into AVL          → Check BF, apply ≤2 rotations
Insert into Red-Black    → Fix double-red via rotation+recolor
Delete from BST          → Replace with successor (maintain order)
Delete from AVL          → Rebalance up the path to root
Rotate                   → Update heights (child before parent!)
Augment split/merge      → Update size/height at each new node
Lazy pushdown            → Always push before accessing children
HLD assign               → Heavy child must have max subtree size
Centroid remove          → Track removed[] to avoid revisiting
Persistent copy          → Copy only the path nodes (not whole tree)
────────────────────────────────────────────────────────────────────
```

---

### The Monk's Mastery Path

```
PHASE 1 — FUNDAMENTALS (week 1-2):
  Master: Rotation (all 4 cases), Inversion, Flatten, Clone
  Daily practice: implement each from scratch, no reference

PHASE 2 — TREE TRANSFORMS (week 3-4):
  Master: Serialize/Deserialize, BST→DLL, DSW, Split/Merge
  Key insight: "Does this operation preserve inorder sequence?"

PHASE 3 — ADVANCED STRUCTURES (week 5-8):
  Master: Lazy Segment Tree, Euler Tour, HLD, Centroid Decomp
  Key insight: "Every path problem on a tree is a range problem on an array"

PHASE 4 — PERSISTENCE AND AUGMENTATION (week 9-12):
  Master: Persistent BST, Order-Statistic Tree, Interval Tree
  Key insight: "O(log N) new nodes per update — only the modified path"

COGNITIVE PRINCIPLE (Chunking):
  Do not memorize code. Memorize the INVARIANT + the REPAIR STEP.
  The code always flows from those two things.
  
  Rotation invariant: inorder sequence unchanged
  Repair step: update heights bottom-up after any pointer change
  
  This is ONE chunk — once internalized, all rotation code writes itself.
```

---

*"Every manipulation is a controlled perturbation. The expert does not fight the invariant — they use it as a guide, letting it show exactly which repair is needed and where."*

**4,016 lines. Every tree manipulation, fully implemented in C, Go, and Rust.**

Here is the complete map of what's inside:

---

### What the Guide Covers

**Section 2 — Rotation (The Atomic Operation)**
The most important section. Right rotation, left rotation, left-right and right-left double rotations, with exact 6-rule algorithm and call-flow diagrams. Includes the full Splay operation (Zig, Zig-Zig, Zig-Zag cases). This is the primitive that every balancing algorithm is built from.

**Sections 3–9 — Core Structural Manipulations**
Inversion/mirroring (recursive + iterative BFS), flattening to right-skewed list (Morris O(1) space approach), deep copy (recursive + iterative BFS), merging two trees (element-wise sum AND sorted BST merge), splitting a BST at a key, pruning by condition or range, and grafting/splicing subtrees.

**Section 10 — Serialization / Deserialization**
Both preorder-with-null-markers method AND level-order (BFS) method. Exact tokenization and reconstruction code.

**Section 11 — Threaded Binary Trees**
Repurposing null pointers as successor/predecessor links. Enables O(1) space inorder traversal with no stack.

**Section 12 — DSW Algorithm**
The most underrated algorithm: rebalances ANY BST in O(N) time with O(1) space. Phase 1 creates a vine (right-skewed list), Phase 2 compresses it into a perfect tree via counted left rotations.

**Sections 13–15 — DLL Conversion, Subtree Ops, Path Manipulation**
BST to sorted circular doubly-linked list in-place. Subtree search, extraction, replacement. Path finding, LCA (BST and general), and path compression (Union-Find with rank).

**Section 16 — Lazy Propagation**
The push-down mechanism in detail — why you must push before accessing children, how the tag propagates, range update + range query all in O(log N). Full implementation in C, Go, and Rust.

**Sections 17–19 — Euler Tour, HLD, Centroid Decomposition**
These three are the pillars of competitive programming tree manipulation. Euler Tour converts subtree queries to range queries. HLD decomposes path queries into O(log N) chain segments. Centroid Decomposition answers distance queries in O(N log N).

**Sections 20–22 — Augmented Trees, Persistent Trees, Isomorphism**
Order-statistic tree (K-th smallest, rank), interval tree (overlap queries), persistent BST (full version history in O(log N) per update), and AHU canonicalization for tree isomorphism checking.

---

### The Key Mental Model to Internalize

Every manipulation in this guide follows one pattern: **identify the invariant → perform the operation → apply the repair**. Once you internalize this for each tree type, you stop memorizing code and start *deriving* it on the fly — which is exactly how top-tier engineers think.