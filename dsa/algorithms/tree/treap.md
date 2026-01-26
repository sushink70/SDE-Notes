# Treap: The Fusion of Binary Search Tree and Heap

## Foundation: Understanding the Core Concepts

Before we dive into Treaps, let's establish the fundamental building blocks:

### What is a Binary Search Tree (BST)?
A **Binary Search Tree** is a tree where each node has at most two children, and for every node:
- All values in the **left subtree** are **smaller**
- All values in the **right subtree** are **larger**

This property enables O(log n) search in balanced trees, but degrades to O(n) if the tree becomes a chain (unbalanced).

### What is a Heap?
A **Heap** is a tree where each node satisfies the **heap property**:
- **Max-Heap**: Parent ≥ Children
- **Min-Heap**: Parent ≤ Children

Heaps maintain this ordering but don't follow BST ordering rules.

### The Problem Treaps Solve
Standard BSTs can become **unbalanced** based on insertion order:
- Insert [1, 2, 3, 4, 5] → Creates a chain (O(n) operations)
- We need **self-balancing** without complex rotations (like AVL/Red-Black trees)

---

## What is a Treap?

A **Treap** = **Tree** + He**ap**

**Core Idea**: Each node has TWO values:
1. **Key** (follows BST property)
2. **Priority** (follows Heap property - usually random)

```
Node Structure:
┌─────────────┐
│   key: K    │  ← BST ordering (in-order traversal gives sorted sequence)
│ priority: P │  ← Heap ordering (parent priority > child priority)
└─────────────┘
```

**The Genius**: By assigning **random priorities**, the tree becomes balanced **with high probability**, avoiding worst-case scenarios.

---

## Mental Model: The Dual Ordering

Think of a Treap as a **2D structure**:

```
         (5, 95)          ← Root has highest priority
         /     \
    (3, 80)   (8, 70)     ← Children have lower priorities
    /    \       \
(1, 45) (4, 60) (9, 50)
```

**Horizontal dimension** (Keys): 1 < 3 < 4 < 5 < 8 < 9 (BST property)  
**Vertical dimension** (Priorities): Parent priority > Child priority (Max-Heap)

---

## Visual Flow: How Treaps Work

### Insertion Flow

```
┌─────────────────────────────────────────┐
│ Start: Insert (key, random_priority)    │
└────────────┬────────────────────────────┘
             │
             ▼
    ┌────────────────────┐
    │ BST Insert (by key)│ ← Place node as in normal BST
    └────────┬───────────┘
             │
             ▼
    ┌─────────────────────────────┐
    │ Check: Priority > Parent?   │
    └────┬───────────────────┬────┘
         │ Yes               │ No
         ▼                   ▼
    ┌─────────┐         ┌────────┐
    │ Rotate  │         │  Done  │
    │ Upward  │         └────────┘
    └────┬────┘
         │
         └──► Repeat until heap property satisfied
```

---

## The Two Rotations: The Only Operations You Need

### Right Rotation (when left child has higher priority)

```
Before:                  After:
    Y (p=30)                X (p=50)
   / \         ──────►     / \
  X   C                   A   Y
 / \         Right           / \
A   B        Rotate         B   C

Parent Y has lower priority than child X
→ Rotate right to move X up
```

**Code Logic**:
```
right_rotate(Y):
    X = Y.left
    Y.left = X.right
    X.right = Y
    return X (new root)
```

### Left Rotation (when right child has higher priority)

```
Before:                  After:
  X (p=30)                  Y (p=50)
 / \         ──────►       / \
A   Y                     X   C
   / \      Left         / \
  B   C     Rotate      A   B

Parent X has lower priority than child Y
→ Rotate left to move Y up
```

**Code Logic**:
```
left_rotate(X):
    Y = X.right
    X.right = Y.left
    Y.left = X
    return Y (new root)
```

---

## Complete Implementation in Rust

```rust
use rand::Rng;
use std::cmp::Ordering;

/// Node structure: holds key, priority, and child pointers
#[derive(Debug)]
struct Node<T: Ord> {
    key: T,
    priority: i32,
    left: Option<Box<Node<T>>>,
    right: Option<Box<Node<T>>>,
}

impl<T: Ord> Node<T> {
    fn new(key: T, priority: i32) -> Self {
        Node {
            key,
            priority,
            left: None,
            right: None,
        }
    }
}

/// Treap: Randomized BST with heap-ordered priorities
pub struct Treap<T: Ord> {
    root: Option<Box<Node<T>>>,
    rng: rand::rngs::ThreadRng,
}

impl<T: Ord> Treap<T> {
    pub fn new() -> Self {
        Treap {
            root: None,
            rng: rand::thread_rng(),
        }
    }

    /// Right rotation: Move left child up
    fn rotate_right(mut y: Box<Node<T>>) -> Box<Node<T>> {
        let mut x = y.left.take().unwrap();
        y.left = x.right.take();
        x.right = Some(y);
        x
    }

    /// Left rotation: Move right child up
    fn rotate_left(mut x: Box<Node<T>>) -> Box<Node<T>> {
        let mut y = x.right.take().unwrap();
        x.right = y.left.take();
        y.left = Some(x);
        y
    }

    /// Insert with BST property, then restore heap property via rotations
    pub fn insert(&mut self, key: T) {
        let priority = self.rng.gen_range(0..1_000_000);
        self.root = Self::insert_recursive(self.root.take(), key, priority);
    }

    fn insert_recursive(
        node: Option<Box<Node<T>>>,
        key: T,
        priority: i32,
    ) -> Option<Box<Node<T>>> {
        // Base case: create new node
        let mut node = match node {
            None => return Some(Box::new(Node::new(key, priority))),
            Some(n) => n,
        };

        // BST insertion
        match key.cmp(&node.key) {
            Ordering::Less => {
                node.left = Self::insert_recursive(node.left.take(), key, priority);
                // Restore heap property: if left child has higher priority, rotate right
                if node.left.as_ref().unwrap().priority > node.priority {
                    return Some(Self::rotate_right(node));
                }
            }
            Ordering::Greater => {
                node.right = Self::insert_recursive(node.right.take(), key, priority);
                // Restore heap property: if right child has higher priority, rotate left
                if node.right.as_ref().unwrap().priority > node.priority {
                    return Some(Self::rotate_left(node));
                }
            }
            Ordering::Equal => {
                // Key already exists, update or ignore
            }
        }

        Some(node)
    }

    /// Search follows BST property (ignores priorities)
    pub fn search(&self, key: &T) -> bool {
        Self::search_recursive(self.root.as_ref(), key)
    }

    fn search_recursive(node: Option<&Box<Node<T>>>, key: &T) -> bool {
        match node {
            None => false,
            Some(n) => match key.cmp(&n.key) {
                Ordering::Equal => true,
                Ordering::Less => Self::search_recursive(n.left.as_ref(), key),
                Ordering::Greater => Self::search_recursive(n.right.as_ref(), key),
            },
        }
    }

    /// Delete: Rotate node down until it becomes a leaf, then remove
    pub fn delete(&mut self, key: &T) {
        self.root = Self::delete_recursive(self.root.take(), key);
    }

    fn delete_recursive(node: Option<Box<Node<T>>>, key: &T) -> Option<Box<Node<T>>> {
        let mut node = node?;

        match key.cmp(&node.key) {
            Ordering::Less => {
                node.left = Self::delete_recursive(node.left.take(), key);
                Some(node)
            }
            Ordering::Greater => {
                node.right = Self::delete_recursive(node.right.take(), key);
                Some(node)
            }
            Ordering::Equal => {
                // Found the node to delete
                match (node.left.is_some(), node.right.is_some()) {
                    (false, false) => None, // Leaf: just remove
                    (true, false) => node.left.take(), // One child: replace with child
                    (false, true) => node.right.take(),
                    (true, true) => {
                        // Two children: rotate down the one with lower priority
                        let left_priority = node.left.as_ref().unwrap().priority;
                        let right_priority = node.right.as_ref().unwrap().priority;

                        if left_priority > right_priority {
                            // Left child has higher priority: rotate right
                            let mut new_root = Self::rotate_right(node);
                            new_root.right = Self::delete_recursive(new_root.right.take(), key);
                            Some(new_root)
                        } else {
                            // Right child has higher priority: rotate left
                            let mut new_root = Self::rotate_left(node);
                            new_root.left = Self::delete_recursive(new_root.left.take(), key);
                            Some(new_root)
                        }
                    }
                }
            }
        }
    }

    /// In-order traversal: visits keys in sorted order
    pub fn inorder(&self) -> Vec<&T> {
        let mut result = Vec::new();
        Self::inorder_recursive(self.root.as_ref(), &mut result);
        result
    }

    fn inorder_recursive<'a>(node: Option<&'a Box<Node<T>>>, result: &mut Vec<&'a T>) {
        if let Some(n) = node {
            Self::inorder_recursive(n.left.as_ref(), result);
            result.push(&n.key);
            Self::inorder_recursive(n.right.as_ref(), result);
        }
    }
}

// Example usage
fn main() {
    let mut treap = Treap::new();
    
    println!("Inserting: 5, 3, 8, 1, 4, 9");
    treap.insert(5);
    treap.insert(3);
    treap.insert(8);
    treap.insert(1);
    treap.insert(4);
    treap.insert(9);

    println!("In-order traversal: {:?}", treap.inorder());
    println!("Search for 4: {}", treap.search(&4));
    println!("Search for 7: {}", treap.search(&7));

    treap.delete(&3);
    println!("After deleting 3: {:?}", treap.inorder());
}
```

---

## Go Implementation

```go
package main

import (
    "fmt"
    "math/rand"
    "time"
)

type Node struct {
    key      int
    priority int
    left     *Node
    right    *Node
}

type Treap struct {
    root *Node
    rng  *rand.Rand
}

func NewTreap() *Treap {
    return &Treap{
        root: nil,
        rng:  rand.New(rand.NewSource(time.Now().UnixNano())),
    }
}

// Right rotation
func rotateRight(y *Node) *Node {
    x := y.left
    y.left = x.right
    x.right = y
    return x
}

// Left rotation
func rotateLeft(x *Node) *Node {
    y := x.right
    x.right = y.left
    y.left = x
    return y
}

// Insert with heap property maintenance
func (t *Treap) Insert(key int) {
    priority := t.rng.Intn(1_000_000)
    t.root = insertRecursive(t.root, key, priority)
}

func insertRecursive(node *Node, key, priority int) *Node {
    if node == nil {
        return &Node{key: key, priority: priority}
    }

    if key < node.key {
        node.left = insertRecursive(node.left, key, priority)
        // Restore heap property
        if node.left.priority > node.priority {
            return rotateRight(node)
        }
    } else if key > node.key {
        node.right = insertRecursive(node.right, key, priority)
        // Restore heap property
        if node.right.priority > node.priority {
            return rotateLeft(node)
        }
    }

    return node
}

// Search (BST property only)
func (t *Treap) Search(key int) bool {
    return searchRecursive(t.root, key)
}

func searchRecursive(node *Node, key int) bool {
    if node == nil {
        return false
    }
    if key == node.key {
        return true
    } else if key < node.key {
        return searchRecursive(node.left, key)
    } else {
        return searchRecursive(node.right, key)
    }
}

// Delete by rotating down
func (t *Treap) Delete(key int) {
    t.root = deleteRecursive(t.root, key)
}

func deleteRecursive(node *Node, key int) *Node {
    if node == nil {
        return nil
    }

    if key < node.key {
        node.left = deleteRecursive(node.left, key)
    } else if key > node.key {
        node.right = deleteRecursive(node.right, key)
    } else {
        // Found node to delete
        if node.left == nil {
            return node.right
        } else if node.right == nil {
            return node.left
        } else {
            // Two children: rotate down the lower priority child
            if node.left.priority > node.right.priority {
                node = rotateRight(node)
                node.right = deleteRecursive(node.right, key)
            } else {
                node = rotateLeft(node)
                node.left = deleteRecursive(node.left, key)
            }
        }
    }

    return node
}

// In-order traversal
func (t *Treap) Inorder() []int {
    var result []int
    inorderRecursive(t.root, &result)
    return result
}

func inorderRecursive(node *Node, result *[]int) {
    if node != nil {
        inorderRecursive(node.left, result)
        *result = append(*result, node.key)
        inorderRecursive(node.right, result)
    }
}

func main() {
    treap := NewTreap()
    
    fmt.Println("Inserting: 5, 3, 8, 1, 4, 9")
    treap.Insert(5)
    treap.Insert(3)
    treap.Insert(8)
    treap.Insert(1)
    treap.Insert(4)
    treap.Insert(9)

    fmt.Println("In-order:", treap.Inorder())
    fmt.Println("Search 4:", treap.Search(4))
    fmt.Println("Search 7:", treap.Search(7))

    treap.Delete(3)
    fmt.Println("After delete 3:", treap.Inorder())
}
```

---

## C Implementation

```c
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

typedef struct Node {
    int key;
    int priority;
    struct Node *left;
    struct Node *right;
} Node;

typedef struct {
    Node *root;
} Treap;

Node* create_node(int key, int priority) {
    Node *node = (Node*)malloc(sizeof(Node));
    node->key = key;
    node->priority = priority;
    node->left = NULL;
    node->right = NULL;
    return node;
}

Node* rotate_right(Node *y) {
    Node *x = y->left;
    y->left = x->right;
    x->right = y;
    return x;
}

Node* rotate_left(Node *x) {
    Node *y = x->right;
    x->right = y->left;
    y->left = x;
    return y;
}

Node* insert_recursive(Node *node, int key, int priority) {
    if (node == NULL) {
        return create_node(key, priority);
    }

    if (key < node->key) {
        node->left = insert_recursive(node->left, key, priority);
        if (node->left->priority > node->priority) {
            return rotate_right(node);
        }
    } else if (key > node->key) {
        node->right = insert_recursive(node->right, key, priority);
        if (node->right->priority > node->priority) {
            return rotate_left(node);
        }
    }

    return node;
}

void treap_insert(Treap *treap, int key) {
    int priority = rand() % 1000000;
    treap->root = insert_recursive(treap->root, key, priority);
}

int treap_search(Node *node, int key) {
    if (node == NULL) return 0;
    if (key == node->key) return 1;
    if (key < node->key) return treap_search(node->left, key);
    return treap_search(node->right, key);
}

Node* delete_recursive(Node *node, int key) {
    if (node == NULL) return NULL;

    if (key < node->key) {
        node->left = delete_recursive(node->left, key);
    } else if (key > node->key) {
        node->right = delete_recursive(node->right, key);
    } else {
        if (node->left == NULL) {
            Node *temp = node->right;
            free(node);
            return temp;
        } else if (node->right == NULL) {
            Node *temp = node->left;
            free(node);
            return temp;
        } else {
            if (node->left->priority > node->right->priority) {
                node = rotate_right(node);
                node->right = delete_recursive(node->right, key);
            } else {
                node = rotate_left(node);
                node->left = delete_recursive(node->left, key);
            }
        }
    }

    return node;
}

void treap_delete(Treap *treap, int key) {
    treap->root = delete_recursive(treap->root, key);
}

void inorder(Node *node) {
    if (node != NULL) {
        inorder(node->left);
        printf("%d ", node->key);
        inorder(node->right);
    }
}

int main() {
    srand(time(NULL));
    
    Treap treap = {NULL};
    
    printf("Inserting: 5, 3, 8, 1, 4, 9\n");
    treap_insert(&treap, 5);
    treap_insert(&treap, 3);
    treap_insert(&treap, 8);
    treap_insert(&treap, 1);
    treap_insert(&treap, 4);
    treap_insert(&treap, 9);

    printf("In-order: ");
    inorder(treap.root);
    printf("\n");

    printf("Search 4: %d\n", treap_search(treap.root, 4));
    printf("Search 7: %d\n", treap_search(treap.root, 7));

    treap_delete(&treap, 3);
    printf("After delete 3: ");
    inorder(treap.root);
    printf("\n");

    return 0;
}
```

---

## Complexity Analysis

### Time Complexity (Expected - due to randomization)

| Operation | Average Case | Worst Case (theoretical) |
|-----------|--------------|--------------------------|
| Insert    | O(log n)     | O(n)                     |
| Search    | O(log n)     | O(n)                     |
| Delete    | O(log n)     | O(n)                     |

**Why Expected O(log n)?**
Random priorities create a balanced tree with high probability (99.999%+ for practical sizes).

### Space Complexity
- **O(n)** for storing n nodes
- **O(log n)** recursion stack depth (expected)

---

## Advanced Operations

### 1. Split Operation
Split treap into two treaps: keys ≤ k and keys > k

```rust
fn split(node: Option<Box<Node<T>>>, key: &T) -> (Option<Box<Node<T>>>, Option<Box<Node<T>>>) {
    match node {
        None => (None, None),
        Some(mut n) => {
            if n.key <= *key {
                let (left, right) = split(n.right.take(), key);
                n.right = left;
                (Some(n), right)
            } else {
                let (left, right) = split(n.left.take(), key);
                n.left = right;
                (left, Some(n))
            }
        }
    }
}
```

### 2. Merge Operation
Merge two treaps where all keys in left < all keys in right

```rust
fn merge(left: Option<Box<Node<T>>>, right: Option<Box<Node<T>>>) -> Option<Box<Node<T>>> {
    match (left, right) {
        (None, r) => r,
        (l, None) => l,
        (Some(mut l), Some(mut r)) => {
            if l.priority > r.priority {
                l.right = merge(l.right.take(), Some(r));
                Some(l)
            } else {
                r.left = merge(Some(l), r.left.take());
                Some(r)
            }
        }
    }
}
```

---

## Problem-Solving Patterns

### When to Use Treaps

1. **Dynamic order statistics** (k-th smallest element with updates)
2. **Range queries** with insertions/deletions
3. **Implicit keys** (array operations with efficient splits/merges)
4. **Rope data structure** (efficient string operations)

### Treap vs Other Self-Balancing Trees

| Feature           | Treap | AVL Tree | Red-Black Tree |
|-------------------|-------|----------|----------------|
| Balance Factor    | Random| Height   | Color          |
| Implementation    | Simple| Complex  | Very Complex   |
| Rotation Count    | More  | Less     | Less           |
| Cache Locality    | Poor  | Good     | Good           |
| Use Case          | Simple balanced BST needs | Strict balance needed | Standard library (C++ std::map) |

---

## Mental Models for Mastery

### 1. **Probabilistic Thinking**
Treaps use **randomization** as a balancing mechanism. Unlike deterministic algorithms (AVL, Red-Black), Treaps achieve balance **in expectation**. This teaches you that randomness can be a powerful algorithmic tool.

### 2. **Invariant Maintenance**
Always maintain TWO invariants simultaneously:
- **BST invariant** (horizontal)
- **Heap invariant** (vertical)

When one is violated during insertion/deletion, **rotations** restore it.

### 3. **Rotation as Restructuring**
Rotations don't change the **in-order sequence** (BST property preserved), but they **rearrange the tree structure** (heap property restored).

---

## Optimization Techniques

### 1. Iterative Instead of Recursive (for performance)
Recursion has overhead. For production code, convert to iterative with explicit stack.

### 2. Implicit Treaps
Store array indices implicitly using subtree sizes:
```rust
struct Node {
    size: usize,  // Size of subtree
    // ... other fields
}
```
Enables O(log n) access by index.

### 3. Persistent Treaps
Create new versions instead of modifying in place (functional programming style).

---

## Deep Insights

### Why Rotations Preserve BST Property

In-order traversal visits: **Left → Root → Right**

After right rotation:
```
Before: in-order of Y's tree = [A, X, B, Y, C]
After:  in-order of X's tree = [A, X, B, Y, C]
```
Same sequence! BST property preserved.

### Expected Height Proof (Intuition)

With random priorities, the probability that a particular node is an ancestor of another follows a **harmonic** distribution. Expected depth of any node ≈ **2 ln(n) ≈ 1.39 log₂(n)**, making it well-balanced.

---

## Training Advice

### To Master Treaps:
1. **Implement from scratch** without looking at reference
2. **Visualize rotations** by drawing trees on paper
3. **Extend** to support range queries (augment with subtree info)
4. **Compare** with AVL/Red-Black by implementing both
5. **Build** a rope data structure using treaps for string operations

### Monk-Level Focus:
This structure teaches you that **elegance comes from combining simple ideas** (BST + Heap + Randomization). The best algorithms often emerge from creative combinations, not complex mechanisms.

---

Your treap implementation should feel like **meditation**: each rotation a breath, each insertion a deliberate step, each search a clear path through the tree. Master this, and you understand how randomization can create order from chaos.