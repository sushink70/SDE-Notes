# 🌳 Comprehensive Guide to Binary Trees
> *"A tree that doesn't bend in the wind is brittle. A mind that doesn't understand structure will break under complexity."*

---

## Table of Contents

1. [Foundational Vocabulary — Before Anything Else](#1-foundational-vocabulary)
2. [What is a Tree?](#2-what-is-a-tree)
3. [What is a Binary Tree?](#3-what-is-a-binary-tree)
4. [Anatomy of a Binary Tree — Every Term Explained](#4-anatomy-of-a-binary-tree)
5. [Types of Binary Trees](#5-types-of-binary-trees)
6. [Memory Representation](#6-memory-representation)
7. [Node Implementation: C, Rust, Go](#7-node-implementation)
8. [Tree Construction](#8-tree-construction)
9. [Tree Traversals — The Heart of Tree Algorithms](#9-tree-traversals)
10. [Tree Properties — Height, Depth, Size, Level](#10-tree-properties)
11. [Binary Search Tree (BST)](#11-binary-search-tree)
12. [BST Operations: Insert, Search, Delete](#12-bst-operations)
13. [BST Traversal and Validation](#13-bst-traversal-and-validation)
14. [Balanced Trees — The AVL Tree](#14-avl-tree)
15. [Important Binary Tree Algorithms](#15-important-algorithms)
16. [Lowest Common Ancestor (LCA)](#16-lowest-common-ancestor)
17. [Tree Diameter](#17-tree-diameter)
18. [Level Order / BFS Traversal](#18-level-order-bfs)
19. [Serialization and Deserialization](#19-serialization-and-deserialization)
20. [Time & Space Complexity Reference](#20-complexity-reference)
21. [Mental Models & Problem-Solving Patterns](#21-mental-models)
22. [Deliberate Practice Roadmap](#22-practice-roadmap)

---

## 1. Foundational Vocabulary

Before writing a single line of code, you must master the language. Every domain has its dialect. Here is yours.

| Term | Plain English Meaning |
|------|----------------------|
| **Node** | A single box/unit that holds a value and pointers to other nodes |
| **Edge** | The connection/link between two nodes (a pointer) |
| **Root** | The topmost node — the entry point of the tree (has no parent) |
| **Leaf** | A node with NO children — the end of a branch |
| **Parent** | A node that has at least one child directly below it |
| **Child** | A node directly connected below another node |
| **Sibling** | Two nodes that share the same parent |
| **Ancestor** | Any node on the path from root to a given node (inclusive of root) |
| **Descendant** | Any node reachable downward from a given node |
| **Subtree** | A node and ALL of its descendants — itself forms a smaller tree |
| **Height of node** | Number of edges on the longest downward path from this node to a leaf |
| **Depth of node** | Number of edges from the root to this node |
| **Level** | Depth + 1 (root is at level 1, or sometimes 0 — context-dependent) |
| **Height of tree** | Height of the root node |
| **Degree of node** | Number of children a node has |
| **Internal node** | Any node that is NOT a leaf (has at least one child) |
| **Path** | A sequence of nodes connected by edges |
| **In-order** | Left → Root → Right traversal |
| **Pre-order** | Root → Left → Right traversal |
| **Post-order** | Left → Right → Root traversal |
| **Successor** | In a BST, the next larger node after a given node (in-order successor) |
| **Predecessor** | In a BST, the next smaller node before a given node |
| **Pivot** | (AVL/rotation context) The node around which a rotation is performed |
| **Balance Factor** | Height(left subtree) - Height(right subtree) for AVL trees |
| **Null pointer** | A pointer that points to nothing — represents absence of a child |

---

## 2. What is a Tree?

A **tree** is a **hierarchical, non-linear data structure** made of nodes connected by directed edges. Unlike arrays (linear) or graphs (cyclic possible), a tree has **strict rules**:

### Rules of a Tree
```
1. Exactly ONE root node
2. Every non-root node has EXACTLY one parent
3. No cycles (you cannot follow edges and return to the same node)
4. The tree is CONNECTED (every node is reachable from root)
```

### ASCII Visualization — Generic Tree

```
            [A]               <- Root (depth=0)
           / | \
         [B][C][D]            <- Children of A (depth=1)
        /|   |   \
      [E][F][G]  [H]          <- depth=2
               |
              [I]             <- Leaf (depth=3)

Tree height = 3 (longest path from root to a leaf)
```

A tree with `N` nodes always has exactly `N-1` edges. This is a fundamental property.

---

## 3. What is a Binary Tree?

A **Binary Tree** is a tree where every node has **at most 2 children**, specifically called:
- **Left child**
- **Right child**

The constraint is: `degree(node) ≤ 2` for all nodes.

### Why "Binary"?

Binary = two. Each node branches into at most two directions, like a forking path.

```
            [10]
           /    \
         [5]   [15]
        /   \     \
      [3]   [7]  [20]
                 /
               [18]
```

Notice:
- `[10]` has 2 children → OK
- `[5]` has 2 children → OK
- `[15]` has 1 child (right only) → OK
- `[3]`, `[7]` have 0 children → Leaves
- `[18]` is a leaf

---

## 4. Anatomy of a Binary Tree

Let's use this tree for all anatomy explanations:

```
                    [50]           <- Root
                   /    \
               [30]      [70]
              /    \    /    \
           [20]  [40][60]   [80]
           /
         [10]
```

### Identifying each concept:

```
Root          → [50]
Leaves        → [10], [40], [60], [80]
Internal nodes→ [50], [30], [70], [20]

Parent of [30]  → [50]
Children of [30]→ [20], [40]
Sibling of [30] → [70]

Ancestors of [10]  → [20], [30], [50]
Descendants of [30]→ [20], [40], [10]

Depth of [50] = 0
Depth of [30] = 1
Depth of [20] = 2
Depth of [10] = 3

Height of [20] = 1  (path: [20]->[10])
Height of [30] = 2  (path: [30]->[20]->[10])
Height of [50] = 3  (path: [50]->[30]->[20]->[10])

Subtree rooted at [30]:
         [30]
        /    \
     [20]   [40]
     /
   [10]

Level 0: [50]
Level 1: [30], [70]
Level 2: [20], [40], [60], [80]
Level 3: [10]
```

---

## 5. Types of Binary Trees

Understanding tree types is critical — many algorithms behave differently on each type.

### 5.1 Full Binary Tree (Proper Binary Tree)

**Definition**: Every node has either **0 or 2 children**. No node has exactly 1 child.

```
        [1]
       /   \
     [2]   [3]
    /   \
  [4]   [5]
```

```
Property: If it has L leaves → it has exactly (L-1) internal nodes → total nodes = 2L - 1
```

### 5.2 Complete Binary Tree

**Definition**: All levels are **completely filled except possibly the last**, which is filled from **left to right** with no gaps.

```
COMPLETE:               NOT COMPLETE (gap exists):
       [1]                       [1]
      /   \                     /   \
    [2]   [3]                 [2]   [3]
   /   \  /                  /       \
 [4]  [5][6]               [4]       [5]
                                  ^^^^^ gap on left!
```

**Why it matters**: Complete binary trees map perfectly to arrays! This is how **heaps** are stored.

```
Array index mapping (0-based):
  Parent of node i   → (i-1) / 2
  Left child of i    → 2*i + 1
  Right child of i   → 2*i + 2
```

### 5.3 Perfect Binary Tree

**Definition**: ALL internal nodes have exactly 2 children AND all leaves are at the **same level**.

```
         [1]
        /   \
      [2]   [3]
     / \   / \
   [4][5][6] [7]

Height h → Total nodes = 2^(h+1) - 1
         → Leaf nodes  = 2^h
```

### 5.4 Balanced Binary Tree

**Definition**: For every node, the height difference between left and right subtree is **at most 1**.

```
|height(left) - height(right)| <= 1   for ALL nodes
```

AVL trees, Red-Black trees enforce balance. An unbalanced BST can degrade to O(N) operations.

### 5.5 Degenerate (Pathological) Tree

**Definition**: Every parent node has only **one child**. Effectively a linked list.

```
[1]
  \
  [2]
    \
    [3]
      \
      [4]
        \
        [5]
```

This is the **worst case** for BST operations — O(N) instead of O(log N).

### Decision Tree: Which Type is My Tree?

```
START
  │
  ▼
Every node has 0 or 2 children?
  ├─ YES → Full Binary Tree
  └─ NO  → Not Full
              │
              ▼
         Last level filled left-to-right, no gaps?
           ├─ YES → Complete Binary Tree
           │         (also check: is last level also full?)
           │           ├─ YES → Perfect Binary Tree
           │           └─ NO  → Complete only
           └─ NO  → Neither Complete nor Perfect
                       │
                       ▼
                  Every node has only 1 child?
                    ├─ YES → Degenerate Tree
                    └─ NO  → General Binary Tree
```

---

## 6. Memory Representation

### 6.1 Linked Representation (Most Common)

Each node is a struct/object with:
- A **value** (data)
- A **pointer to left child**
- A **pointer to right child**

```
+-------+-------+-------+
|  left |  val  | right |
| ptr   |       | ptr   |
+-------+-------+-------+
    |               |
    ▼               ▼
  [left           [right
   child]          child]
```

### 6.2 Array Representation (For Complete/Perfect Trees)

Index-based, no pointers needed:

```
Tree:           Array (0-indexed):
    [A]         [A, B, C, D, E, F, G]
   /   \          0  1  2  3  4  5  6
 [B]   [C]
 / \   / \
[D][E][F][G]

For node at index i:
  Left child  = 2i + 1
  Right child = 2i + 2
  Parent      = (i - 1) / 2
```

This is exactly how binary heaps work.

---

## 7. Node Implementation

### 7.1 C Implementation

```c
#include <stdio.h>
#include <stdlib.h>

/* ─────────────────────────────────────────────
   NODE STRUCTURE
   Each node holds:
     - data   : the integer value
     - left   : pointer to left child
     - right  : pointer to right child
   ───────────────────────────────────────────── */
typedef struct Node {
    int data;
    struct Node* left;
    struct Node* right;
} Node;

/* Allocate a new node on the heap */
Node* new_node(int val) {
    Node* n = (Node*)malloc(sizeof(Node));
    if (!n) {
        fprintf(stderr, "Memory allocation failed\n");
        exit(EXIT_FAILURE);
    }
    n->data  = val;
    n->left  = NULL;
    n->right = NULL;
    return n;
}

/* Free entire tree (post-order: free children before parent) */
void free_tree(Node* root) {
    if (root == NULL) return;
    free_tree(root->left);
    free_tree(root->right);
    free(root);
}

/* Example usage */
int main(void) {
    /*
     *       [10]
     *      /    \
     *    [5]   [15]
     *   /   \
     * [3]   [7]
     */
    Node* root     = new_node(10);
    root->left     = new_node(5);
    root->right    = new_node(15);
    root->left->left  = new_node(3);
    root->left->right = new_node(7);

    printf("Root: %d\n", root->data);                    /* 10 */
    printf("Left child: %d\n", root->left->data);        /* 5  */
    printf("Right child: %d\n", root->right->data);      /* 15 */
    printf("LL grandchild: %d\n", root->left->left->data); /* 3 */

    free_tree(root);
    return 0;
}
```

**Memory Layout in C (conceptual):**

```
Heap:
  0x1000: [left=0x1020 | data=10 | right=0x1040]   <- root
  0x1020: [left=0x1060 | data=5  | right=0x1080]   <- left child
  0x1040: [left=NULL   | data=15 | right=NULL  ]   <- right child
  0x1060: [left=NULL   | data=3  | right=NULL  ]   <- leaf
  0x1080: [left=NULL   | data=7  | right=NULL  ]   <- leaf
```

---

### 7.2 Rust Implementation

Rust's ownership model makes trees genuinely interesting. A node owns its children via `Box<T>` (heap-allocated, owned pointer). We use `Option<Box<Node>>` to represent "a child exists or doesn't."

```rust
// ─────────────────────────────────────────────────────────
//  WHAT IS Box<T>?
//  Box<T> = a heap-allocated value with single owner.
//  When Box goes out of scope, it frees the memory.
//
//  WHAT IS Option<T>?
//  Option<T> = Some(value) | None
//  Used here to represent "child present" or "no child"
// ─────────────────────────────────────────────────────────

#[derive(Debug)]
pub struct Node {
    pub data:  i32,
    pub left:  Option<Box<Node>>,
    pub right: Option<Box<Node>>,
}

impl Node {
    /// Create a new leaf node (no children)
    pub fn new(val: i32) -> Self {
        Node {
            data:  val,
            left:  None,
            right: None,
        }
    }

    /// Convenience: wrap a Node in Box and Option
    pub fn boxed(val: i32) -> Option<Box<Node>> {
        Some(Box::new(Node::new(val)))
    }
}

fn main() {
    /*
     *       [10]
     *      /    \
     *    [5]   [15]
     *   /   \
     * [3]   [7]
     */
    let mut root = Node::new(10);

    let mut left_child = Node::new(5);
    left_child.left  = Node::boxed(3);
    left_child.right = Node::boxed(7);

    root.left  = Some(Box::new(left_child));
    root.right = Node::boxed(15);

    // Access nodes safely
    if let Some(ref left) = root.left {
        println!("Left child: {}", left.data);           // 5
        if let Some(ref ll) = left.left {
            println!("Left-Left grandchild: {}", ll.data); // 3
        }
    }

    // Rust automatically drops (frees) all memory when root goes out of scope
    // No manual free_tree needed — RAII handles it
    println!("Root: {:?}", root);
}
```

**Why `Option<Box<Node>>` and not `*mut Node`?**

```
Option<Box<Node>> guarantees:
  ✓ No null pointer dereferences (Option forces you to check)
  ✓ No memory leaks (Box auto-drops children recursively)
  ✓ No double-free (Box enforces single ownership)
  ✓ No use-after-free (borrow checker enforces lifetimes)

*mut Node (raw pointer) would lose all these guarantees.
Use raw pointers only in unsafe blocks when truly needed.
```

**Recursive Drop in Rust:**

When `root` goes out of scope → `Box<Node>` for root drops → which drops `Box<Node>` for left and right → which drops their children → entire tree freed recursively without a single `free()` call.

---

### 7.3 Go Implementation

Go uses garbage collection, so we use pointers freely. Structs with pointer fields to the same type.

```go
package main

import "fmt"

// ─────────────────────────────────────────────────────────
// Node holds an integer value and pointers to children.
// In Go, pointer to struct (*Node) is nil by default.
// nil in Go = NULL in C = None in Rust
// ─────────────────────────────────────────────────────────
type Node struct {
    Data  int
    Left  *Node
    Right *Node
}

// NewNode creates a new leaf node
func NewNode(val int) *Node {
    return &Node{
        Data:  val,
        Left:  nil,
        Right: nil,
    }
}

func main() {
    /*
     *       [10]
     *      /    \
     *    [5]   [15]
     *   /   \
     * [3]   [7]
     */
    root := NewNode(10)
    root.Left = NewNode(5)
    root.Right = NewNode(15)
    root.Left.Left = NewNode(3)
    root.Left.Right = NewNode(7)

    fmt.Println("Root:", root.Data)                          // 10
    fmt.Println("Left child:", root.Left.Data)               // 5
    fmt.Println("Right child:", root.Right.Data)             // 15
    fmt.Println("LL grandchild:", root.Left.Left.Data)       // 3

    // Go's GC will handle memory — no manual free needed
}
```

---

## 8. Tree Construction

### 8.1 Manual Construction (Hardcoded)

Already shown above. Good for tests and examples.

### 8.2 Building from Level-Order Input

**Level-order input** means values given level by level, left to right. `-1` or `null` means no node.

Input: `[1, 2, 3, 4, 5, -1, 7]`

```
Expected tree:
         [1]
        /   \
      [2]   [3]
     /   \     \
   [4]   [5]  [7]
```

**Algorithm Flow:**

```
ALGORITHM: Build tree from level-order array
─────────────────────────────────────────────
1. If array is empty or arr[0] == -1 → return NULL
2. Create root from arr[0]
3. Use a QUEUE (FIFO): enqueue root
4. i = 1 (index into array)
5. While queue not empty AND i < arr.length:
     a. Dequeue current node
     b. If arr[i] != -1 → create left child, enqueue it
     c. i++
     d. If i < length AND arr[i] != -1 → create right child, enqueue it
     e. i++
6. Return root
─────────────────────────────────────────────
```

**Queue concept**: FIFO — First In, First Out. Elements leave in the order they entered.

```
Queue state during build of [1,2,3,4,5,-1,7]:

Step 1: Enqueue root(1)
  Queue: [1]  |  i=1

Step 2: Dequeue 1. arr[1]=2 → left=2, enqueue. arr[2]=3 → right=3, enqueue.
  Queue: [2, 3]  |  i=3

Step 3: Dequeue 2. arr[3]=4 → left=4, enqueue. arr[4]=5 → right=5, enqueue.
  Queue: [3, 4, 5]  |  i=5

Step 4: Dequeue 3. arr[5]=-1 → no left. arr[6]=7 → right=7, enqueue.
  Queue: [4, 5, 7]  |  i=7

Step 5: Dequeue 4. i=7 ≥ length. Stop.
  Result: Tree built correctly.
```

**C Implementation: Build from Array**

```c
#include <stdio.h>
#include <stdlib.h>

typedef struct Node {
    int data;
    struct Node* left;
    struct Node* right;
} Node;

Node* new_node(int val) {
    Node* n = (Node*)malloc(sizeof(Node));
    n->data = val; n->left = n->right = NULL;
    return n;
}

/* Simple queue using a circular array for BFS */
#define MAXQ 1024
typedef struct Queue {
    Node* arr[MAXQ];
    int front, rear, size;
} Queue;

void enqueue(Queue* q, Node* n) { q->arr[q->rear] = n; q->rear = (q->rear+1)%MAXQ; q->size++; }
Node* dequeue(Queue* q) { Node* n = q->arr[q->front]; q->front = (q->front+1)%MAXQ; q->size--; return n; }
int is_empty(Queue* q) { return q->size == 0; }

Node* build_from_level_order(int* arr, int len) {
    if (len == 0 || arr[0] == -1) return NULL;

    Queue q = {.front=0, .rear=0, .size=0};
    Node* root = new_node(arr[0]);
    enqueue(&q, root);
    int i = 1;

    while (!is_empty(&q) && i < len) {
        Node* cur = dequeue(&q);

        /* Left child */
        if (i < len && arr[i] != -1) {
            cur->left = new_node(arr[i]);
            enqueue(&q, cur->left);
        }
        i++;

        /* Right child */
        if (i < len && arr[i] != -1) {
            cur->right = new_node(arr[i]);
            enqueue(&q, cur->right);
        }
        i++;
    }
    return root;
}

int main(void) {
    int arr[] = {1, 2, 3, 4, 5, -1, 7};
    int len = sizeof(arr) / sizeof(arr[0]);
    Node* root = build_from_level_order(arr, len);

    printf("Root: %d\n", root->data);                   /* 1 */
    printf("Left: %d\n", root->left->data);             /* 2 */
    printf("Right: %d\n", root->right->data);           /* 3 */
    printf("Right-Right: %d\n", root->right->right->data); /* 7 */
    return 0;
}
```

---

## 9. Tree Traversals — The Heart of Tree Algorithms

A **traversal** is a systematic way to visit every node in the tree exactly once. Different traversal orders reveal different properties of the tree.

There are **4 fundamental traversals**:

```
┌─────────────────────────────────────────────────────────────┐
│  TRAVERSAL TYPE    │  ORDER              │  KEY USE          │
├────────────────────┼─────────────────────┼───────────────────┤
│  In-order (LNR)    │  Left→Node→Right    │  BST sorted order │
│  Pre-order (NLR)   │  Node→Left→Right    │  Tree copy/prefix │
│  Post-order (LRN)  │  Left→Right→Node    │  Deletion, postfix│
│  Level-order (BFS) │  Level by level     │  Shortest path    │
└─────────────────────────────────────────────────────────────┘
```

### The Reference Tree

```
              [4]
             /   \
           [2]   [6]
          /   \  / \
        [1]  [3][5] [7]
```

### 9.1 In-Order Traversal (Left → Node → Right)

**Mnemonic**: You visit the left subtree completely, then the node itself, then the right subtree.

```
ALGORITHM InOrder(node):
  if node is NULL → return
  InOrder(node.left)      ← go left first
  VISIT(node)             ← process current node
  InOrder(node.right)     ← go right last

Result on our tree: 1, 2, 3, 4, 5, 6, 7  ← SORTED! (BST property)
```

**Recursion call stack visualization:**

```
InOrder(4)
  └─ InOrder(2)
       └─ InOrder(1)
            └─ InOrder(NULL) → return
            VISIT(1)          → print 1
            └─ InOrder(NULL) → return
       VISIT(2)               → print 2
       └─ InOrder(3)
            └─ InOrder(NULL) → return
            VISIT(3)          → print 3
            └─ InOrder(NULL) → return
  VISIT(4)                    → print 4
  └─ InOrder(6)
       └─ InOrder(5)
            VISIT(5)          → print 5
       VISIT(6)               → print 6
       └─ InOrder(7)
            VISIT(7)          → print 7

Output: 1 2 3 4 5 6 7
```

**C:**
```c
void inorder(Node* root) {
    if (root == NULL) return;
    inorder(root->left);
    printf("%d ", root->data);
    inorder(root->right);
}
```

**Rust:**
```rust
fn inorder(node: &Option<Box<Node>>) {
    if let Some(n) = node {
        inorder(&n.left);
        print!("{} ", n.data);
        inorder(&n.right);
    }
}
```

**Go:**
```go
func InOrder(node *Node) {
    if node == nil {
        return
    }
    InOrder(node.Left)
    fmt.Printf("%d ", node.Data)
    InOrder(node.Right)
}
```

---

### 9.2 Pre-Order Traversal (Node → Left → Right)

**Mnemonic**: You visit the node FIRST before its children. Think of it as "print when entering."

```
ALGORITHM PreOrder(node):
  if node is NULL → return
  VISIT(node)             ← process FIRST
  PreOrder(node.left)
  PreOrder(node.right)

Result: 4, 2, 1, 3, 6, 5, 7
```

**Use case**: Copying a tree (process parent before children), serializing a tree, prefix expression evaluation.

**C:**
```c
void preorder(Node* root) {
    if (root == NULL) return;
    printf("%d ", root->data);
    preorder(root->left);
    preorder(root->right);
}
```

**Rust:**
```rust
fn preorder(node: &Option<Box<Node>>) {
    if let Some(n) = node {
        print!("{} ", n.data);
        preorder(&n.left);
        preorder(&n.right);
    }
}
```

**Go:**
```go
func PreOrder(node *Node) {
    if node == nil {
        return
    }
    fmt.Printf("%d ", node.Data)
    PreOrder(node.Left)
    PreOrder(node.Right)
}
```

---

### 9.3 Post-Order Traversal (Left → Right → Node)

**Mnemonic**: Children are processed BEFORE the parent. Think "print when leaving."

```
ALGORITHM PostOrder(node):
  if node is NULL → return
  PostOrder(node.left)
  PostOrder(node.right)
  VISIT(node)             ← process LAST

Result: 1, 3, 2, 5, 7, 6, 4
```

**Use case**: Deleting a tree (free children before parent), evaluating postfix expressions, calculating directory sizes.

**C:**
```c
void postorder(Node* root) {
    if (root == NULL) return;
    postorder(root->left);
    postorder(root->right);
    printf("%d ", root->data);
}
```

**Rust:**
```rust
fn postorder(node: &Option<Box<Node>>) {
    if let Some(n) = node {
        postorder(&n.left);
        postorder(&n.right);
        print!("{} ", n.data);
    }
}
```

**Go:**
```go
func PostOrder(node *Node) {
    if node == nil {
        return
    }
    PostOrder(node.Left)
    PostOrder(node.Right)
    fmt.Printf("%d ", node.Data)
}
```

---

### 9.4 Iterative Traversals (Using an Explicit Stack)

Recursive traversals use the **call stack** implicitly. We can make the stack explicit to avoid stack overflow on very deep trees.

**Why learn iterative?** Interview questions often require it. Deep trees (N=10^5) can cause stack overflow in recursive versions.

**Iterative In-Order (C):**

```c
/* ─────────────────────────────────────────────
   ALGORITHM (Iterative In-Order):
   1. Push nodes on stack going as LEFT as possible
   2. Pop → visit → go RIGHT → repeat
   ───────────────────────────────────────────── */
#define MAX_STACK 1024

void inorder_iterative(Node* root) {
    Node* stack[MAX_STACK];
    int top = -1;
    Node* curr = root;

    while (curr != NULL || top >= 0) {
        /* Go left as far as possible */
        while (curr != NULL) {
            stack[++top] = curr;
            curr = curr->left;
        }
        /* Pop and visit */
        curr = stack[top--];
        printf("%d ", curr->data);
        /* Move to right subtree */
        curr = curr->right;
    }
}
```

**Stack trace visualization:**

```
Tree:     [4]->[2]->[6]
         /     / \   / \
       [2]   [1][3][5] [7]
       
Initial: curr=4, stack=[]

Loop 1: Push 4,2,1  →  stack=[4,2,1], curr=NULL
  Pop 1 → visit 1. curr=1.right=NULL
  Pop 2 → visit 2. curr=2.right=3
    Push 3        →  stack=[4,3], curr=NULL
  Pop 3 → visit 3. curr=3.right=NULL
  Pop 4 → visit 4. curr=4.right=6
    Push 6,5      →  stack=[6,5], curr=NULL
  Pop 5 → visit 5. curr=5.right=NULL
  Pop 6 → visit 6. curr=6.right=7
    Push 7        →  stack=[7], curr=NULL
  Pop 7 → visit 7. curr=NULL
  Stack empty → done.
  
Output: 1 2 3 4 5 6 7
```

**Iterative Pre-Order (C):**

```c
void preorder_iterative(Node* root) {
    if (!root) return;
    Node* stack[MAX_STACK];
    int top = -1;
    stack[++top] = root;

    while (top >= 0) {
        Node* curr = stack[top--];
        printf("%d ", curr->data);          /* Visit before children */
        /* Push RIGHT first (so LEFT is processed first) */
        if (curr->right) stack[++top] = curr->right;
        if (curr->left)  stack[++top] = curr->left;
    }
}
```

**Iterative Post-Order (C — Two Stack method):**

```c
/* Method: Use 2 stacks.
   Stack1 drives the traversal.
   Stack2 collects nodes in reverse post-order.
   At end, print Stack2 in reverse. */
void postorder_iterative(Node* root) {
    if (!root) return;
    Node* s1[MAX_STACK], *s2[MAX_STACK];
    int t1 = -1, t2 = -1;
    s1[++t1] = root;

    while (t1 >= 0) {
        Node* curr = s1[t1--];
        s2[++t2] = curr;                    /* Store instead of printing */
        if (curr->left)  s1[++t1] = curr->left;
        if (curr->right) s1[++t1] = curr->right;
    }
    /* Print stack2 in reverse = post-order */
    while (t2 >= 0) printf("%d ", s2[t2--]->data);
}
```

---

## 10. Tree Properties

### 10.1 Height of a Tree

**Height** of a node = length of the longest path from that node to a leaf (counting edges).

```
ALGORITHM height(node):
  if node is NULL → return -1   (or 0, depending on convention)
  left_h  = height(node.left)
  right_h = height(node.right)
  return 1 + max(left_h, right_h)
```

**Why -1 for NULL?** If we return -1 for null, then a leaf node returns `1 + max(-1,-1) = 0`. This means a single-node tree has height 0, which is the standard convention.

**Visualization of height calculation:**

```
Tree:
         [1]
        /   \
      [2]   [3]
     /
   [4]

height(4) = 1 + max(-1,-1) = 0
height(2) = 1 + max(0,-1) = 1
height(3) = 1 + max(-1,-1) = 0
height(1) = 1 + max(1, 0) = 2
```

**C:**
```c
int height(Node* root) {
    if (root == NULL) return -1;
    int lh = height(root->left);
    int rh = height(root->right);
    return 1 + (lh > rh ? lh : rh);
}
```

**Rust:**
```rust
fn height(node: &Option<Box<Node>>) -> i32 {
    match node {
        None => -1,
        Some(n) => {
            let lh = height(&n.left);
            let rh = height(&n.right);
            1 + lh.max(rh)
        }
    }
}
```

**Go:**
```go
func Height(node *Node) int {
    if node == nil {
        return -1
    }
    lh := Height(node.Left)
    rh := Height(node.Right)
    if lh > rh {
        return 1 + lh
    }
    return 1 + rh
}
```

---

### 10.2 Size (Count of Nodes)

```
ALGORITHM size(node):
  if node is NULL → return 0
  return 1 + size(node.left) + size(node.right)
```

**C:**
```c
int size(Node* root) {
    if (root == NULL) return 0;
    return 1 + size(root->left) + size(root->right);
}
```

**Rust:**
```rust
fn size(node: &Option<Box<Node>>) -> usize {
    match node {
        None => 0,
        Some(n) => 1 + size(&n.left) + size(&n.right),
    }
}
```

**Go:**
```go
func Size(node *Node) int {
    if node == nil {
        return 0
    }
    return 1 + Size(node.Left) + Size(node.Right)
}
```

---

### 10.3 Counting Leaf Nodes

```
ALGORITHM count_leaves(node):
  if node is NULL → return 0
  if node.left == NULL AND node.right == NULL → return 1  (it's a leaf!)
  return count_leaves(node.left) + count_leaves(node.right)
```

**C:**
```c
int count_leaves(Node* root) {
    if (root == NULL) return 0;
    if (root->left == NULL && root->right == NULL) return 1;
    return count_leaves(root->left) + count_leaves(root->right);
}
```

---

### 10.4 Checking if Two Trees are Identical

```
ALGORITHM identical(a, b):
  if a == NULL AND b == NULL → return true
  if a == NULL OR  b == NULL → return false  (one is null, other isn't)
  if a.data != b.data        → return false
  return identical(a.left, b.left) AND identical(a.right, b.right)
```

**C:**
```c
int identical(Node* a, Node* b) {
    if (!a && !b) return 1;
    if (!a || !b) return 0;
    return (a->data == b->data)
        && identical(a->left,  b->left)
        && identical(a->right, b->right);
}
```

---

### 10.5 Mirror / Invert a Binary Tree

**Problem**: Flip the tree so left becomes right and right becomes left.

```
Original:              Mirrored:
      [4]                   [4]
     /   \                 /   \
   [2]   [6]             [6]   [2]
  /   \  / \            /  \   /  \
[1]  [3][5][7]         [7] [5][3] [1]
```

```
ALGORITHM invert(node):
  if node is NULL → return NULL
  swap(node.left, node.right)
  invert(node.left)
  invert(node.right)
  return node
```

**C:**
```c
Node* invert(Node* root) {
    if (root == NULL) return NULL;
    /* Swap children */
    Node* tmp   = root->left;
    root->left  = root->right;
    root->right = tmp;
    /* Recurse */
    invert(root->left);
    invert(root->right);
    return root;
}
```

**Rust:**
```rust
fn invert(node: &mut Option<Box<Node>>) {
    if let Some(n) = node {
        // Swap left and right
        std::mem::swap(&mut n.left, &mut n.right);
        invert(&mut n.left);
        invert(&mut n.right);
    }
}
```

**Go:**
```go
func Invert(node *Node) *Node {
    if node == nil {
        return nil
    }
    node.Left, node.Right = node.Right, node.Left
    Invert(node.Left)
    Invert(node.Right)
    return node
}
```

---

## 11. Binary Search Tree (BST)

A **Binary Search Tree** is a binary tree with one critical extra property:

```
BST PROPERTY:
  For every node N:
    ALL nodes in N's LEFT  subtree have values LESS    THAN N.data
    ALL nodes in N's RIGHT subtree have values GREATER THAN N.data

This must hold for EVERY node, not just immediate children!
```

### Visual Proof of BST Property:

```
VALID BST:               INVALID BST (looks BST-like but isn't!):
      [8]                        [8]
     /   \                      /   \
   [3]  [10]                  [3]  [10]
  /   \    \                 /   \
[1]   [6]  [14]           [1]   [9]   ← 9 > 8! Violates BST property
     /   \                            (9 is in left subtree of 8)
   [4]   [7]
```

**Why the BST property is powerful:**

```
In a balanced BST with N nodes:
  Search   → O(log N)  — eliminate half the tree each step
  Insert   → O(log N)
  Delete   → O(log N)
  Min      → O(log N)  — always leftmost node
  Max      → O(log N)  — always rightmost node
  In-order → O(N)      — gives SORTED sequence!
```

---

## 12. BST Operations

### 12.1 Search

```
ALGORITHM search(node, target):
  if node is NULL → return NULL (not found)
  if target == node.data → return node (found!)
  if target < node.data  → return search(node.left, target)
  else                   → return search(node.right, target)
```

**Decision tree for search:**

```
Searching for 6 in the BST:

         [8]          6 < 8  → go LEFT
        /   \
      [3]  [10]       6 > 3  → go RIGHT
     /   \
   [1]   [6]          6 == 6 → FOUND!
```

**C:**
```c
Node* search(Node* root, int target) {
    if (root == NULL || root->data == target) return root;
    if (target < root->data) return search(root->left,  target);
    else                     return search(root->right, target);
}
```

**Rust:**
```rust
fn search(node: &Option<Box<Node>>, target: i32) -> Option<&Node> {
    match node {
        None => None,
        Some(n) => {
            if target == n.data      { Some(n) }
            else if target < n.data  { search(&n.left,  target) }
            else                     { search(&n.right, target) }
        }
    }
}
```

**Go:**
```go
func Search(node *Node, target int) *Node {
    if node == nil || node.Data == target {
        return node
    }
    if target < node.Data {
        return Search(node.Left, target)
    }
    return Search(node.Right, target)
}
```

---

### 12.2 Insert

**Key insight**: A new node is ALWAYS inserted as a **leaf**. Find the correct empty spot where a leaf would go.

```
ALGORITHM insert(node, val):
  if node is NULL → create and return new_node(val)   ← BASE CASE
  if val < node.data  → node.left  = insert(node.left,  val)
  if val > node.data  → node.right = insert(node.right, val)
  if val == node.data → do nothing (duplicates ignored in standard BST)
  return node
```

**Insertion trace — Insert 5 into BST:**

```
Initial BST:          Insert 5:
      [8]                   [8]
     /   \                 /   \
   [3]  [10]             [3]  [10]
  /   \                 /   \
[1]   [6]             [1]   [6]
                            /
                          [5]   ← 5 < 6, goes left of 6

Trace:
  insert(8, 5):  5 < 8 → insert(3, 5)
  insert(3, 5):  5 > 3 → insert(6, 5)
  insert(6, 5):  5 < 6 → insert(NULL, 5)
  insert(NULL,5):        → return new_node(5)
  Node 6's left = new_node(5). Return 6.
  ...propagate back up.
```

**C:**
```c
Node* insert(Node* root, int val) {
    if (root == NULL) return new_node(val);
    if (val < root->data)       root->left  = insert(root->left,  val);
    else if (val > root->data)  root->right = insert(root->right, val);
    /* val == root->data: ignore duplicate */
    return root;
}
```

**Rust:**
```rust
fn insert(node: &mut Option<Box<Node>>, val: i32) {
    match node {
        None => {
            *node = Some(Box::new(Node::new(val)));
        }
        Some(n) => {
            if val < n.data      { insert(&mut n.left,  val); }
            else if val > n.data { insert(&mut n.right, val); }
            // equal: ignore duplicate
        }
    }
}
```

**Go:**
```go
func Insert(root *Node, val int) *Node {
    if root == nil {
        return NewNode(val)
    }
    if val < root.Data {
        root.Left = Insert(root.Left, val)
    } else if val > root.Data {
        root.Right = Insert(root.Right, val)
    }
    return root
}
```

---

### 12.3 Finding Min and Max

```
MIN: Keep going LEFT until left child is NULL
MAX: Keep going RIGHT until right child is NULL
```

```c
Node* find_min(Node* root) {
    if (root == NULL) return NULL;
    while (root->left != NULL) root = root->left;
    return root;
}

Node* find_max(Node* root) {
    if (root == NULL) return NULL;
    while (root->right != NULL) root = root->right;
    return root;
}
```

---

### 12.4 Delete

**The hardest BST operation.** Three cases:

```
CASE 1: Node to delete is a LEAF (no children)
  → Simply remove it (set parent's pointer to NULL)

CASE 2: Node has ONE child
  → Replace node with its child (bypass it)

CASE 3: Node has TWO children
  → Find its IN-ORDER SUCCESSOR (smallest value in right subtree)
  → Copy successor's value into current node
  → Delete the successor from the right subtree
  (The successor always has at most 1 child — easier deletion)
```

**What is an In-Order Successor?**

```
In-order successor of node X = the node with the SMALLEST value
GREATER THAN X.data.

In a BST, it's the leftmost node in X's right subtree.

Example: successor of [6] in this tree:
      [8]
     /   \
   [3]  [10]
  /   \
[1]   [6]
     /   \
   [4]   [7]   ← successor of 6 is 7 (leftmost of right subtree of 6)
```

**Delete Algorithm Decision Tree:**

```
DELETE(node, val)
      │
      ▼
  node == NULL?  ──YES──→  return NULL (not found)
      │
      NO
      ▼
  val < node.data?  ──YES──→  node.left = DELETE(node.left, val)
      │
      NO
      ▼
  val > node.data?  ──YES──→  node.right = DELETE(node.right, val)
      │
      NO (val == node.data, found it!)
      ▼
  ┌─────────────────────────────────────────────────────────┐
  │ CASE 1: no left child?  → return node.right             │
  │ CASE 2: no right child? → return node.left              │
  │ CASE 3: both children?                                  │
  │   successor = find_min(node.right)                      │
  │   node.data = successor.data                            │
  │   node.right = DELETE(node.right, successor.data)       │
  └─────────────────────────────────────────────────────────┘
      │
      ▼
  return node
```

**C:**
```c
Node* delete_node(Node* root, int val) {
    if (root == NULL) return NULL;

    if (val < root->data) {
        root->left = delete_node(root->left, val);
    } else if (val > root->data) {
        root->right = delete_node(root->right, val);
    } else {
        /* Found the node to delete */

        /* Case 1 & 2: 0 or 1 child */
        if (root->left == NULL) {
            Node* tmp = root->right;
            free(root);
            return tmp;
        }
        if (root->right == NULL) {
            Node* tmp = root->left;
            free(root);
            return tmp;
        }

        /* Case 3: Two children */
        Node* successor = find_min(root->right);
        root->data  = successor->data;
        root->right = delete_node(root->right, successor->data);
    }
    return root;
}
```

**Rust:**
```rust
fn delete(node: Option<Box<Node>>, val: i32) -> Option<Box<Node>> {
    match node {
        None => None,
        Some(mut n) => {
            if val < n.data {
                n.left = delete(n.left, val);
                Some(n)
            } else if val > n.data {
                n.right = delete(n.right, val);
                Some(n)
            } else {
                // Found the node
                match (n.left.take(), n.right.take()) {
                    (None, right)      => right,         // Case 1
                    (left, None)       => left,           // Case 2
                    (left, Some(mut right)) => {          // Case 3
                        // Find in-order successor (min of right subtree)
                        let succ_val = find_min_val(&right);
                        n.data  = succ_val;
                        n.left  = left;
                        n.right = Some(delete_min(right));
                        Some(n)
                    }
                }
            }
        }
    }
}

fn find_min_val(node: &Box<Node>) -> i32 {
    match &node.left {
        None    => node.data,
        Some(l) => find_min_val(l),
    }
}

fn delete_min(mut node: Box<Node>) -> Box<Node> {
    match node.left.take() {
        None    => *node.right.take().unwrap_or_else(|| Box::new(Node::new(0))),
        Some(l) => { node.left = Some(delete_min(l)); node }
    }
}
```

**Go:**
```go
func Delete(root *Node, val int) *Node {
    if root == nil {
        return nil
    }
    if val < root.Data {
        root.Left = Delete(root.Left, val)
    } else if val > root.Data {
        root.Right = Delete(root.Right, val)
    } else {
        // Found node
        if root.Left == nil {
            return root.Right
        }
        if root.Right == nil {
            return root.Left
        }
        // Two children: replace with in-order successor
        successor := FindMin(root.Right)
        root.Data  = successor.Data
        root.Right = Delete(root.Right, successor.Data)
    }
    return root
}
```

---

## 13. BST Traversal and Validation

### 13.1 In-Order gives Sorted Output

Because of the BST property, an in-order traversal of a BST always produces values in **ascending sorted order**.

```
BST:
       [5]
      /   \
    [3]   [8]
   /   \  / \
 [1]  [4][7][9]

In-order: 1, 3, 4, 5, 7, 8, 9  ← perfectly sorted!
```

### 13.2 Validating a BST

A common interview trap: you can't just check `node.left.data < node.data < node.right.data`. You must enforce the property globally using a **range [min, max]**.

```
ALGORITHM is_valid_bst(node, min, max):
  if node is NULL → return true
  if node.data <= min OR node.data >= max → return false
  return is_valid_bst(node.left,  min,       node.data)
      && is_valid_bst(node.right, node.data, max)

Initial call: is_valid_bst(root, -∞, +∞)
```

**Why range-based?**

```
This WRONG tree would pass naive left/right check:
       [5]
      /   \
    [1]   [8]
         /
       [3]   ← 3 > 5 needed but 3 < 5! BST violated.
       
Naive check: 3 < 8 (OK locally). But globally 3 < 5 violates right subtree rule.
Range check: is_valid(3, min=5, max=8) → 3 <= 5 → FALSE. Caught!
```

**C:**
```c
#include <limits.h>

int is_valid_bst(Node* root, int min, int max) {
    if (root == NULL) return 1;
    if (root->data <= min || root->data >= max) return 0;
    return is_valid_bst(root->left,  min,       root->data)
        && is_valid_bst(root->right, root->data, max);
}

/* Usage: is_valid_bst(root, INT_MIN, INT_MAX) */
```

**Go:**
```go
import "math"

func IsValidBST(node *Node, min, max int) bool {
    if node == nil {
        return true
    }
    if node.Data <= min || node.Data >= max {
        return false
    }
    return IsValidBST(node.Left, min, node.Data) &&
           IsValidBST(node.Right, node.Data, max)
}

// Usage: IsValidBST(root, math.MinInt64, math.MaxInt64)
```

---

## 14. AVL Tree

### What Problem Does AVL Solve?

A BST can degenerate into a linked list if you insert elements in sorted order:

```
Insert: 1, 2, 3, 4, 5 into a naive BST:

[1]
  \
  [2]
    \
    [3]
      \
      [4]
        \
        [5]

Height = 4. Search = O(N) not O(log N). 
```

An **AVL Tree** is a **self-balancing BST** that maintains the **balance property** after every insert/delete.

### The Balance Factor

```
Balance Factor (BF) of a node = height(left subtree) - height(right subtree)

AVL requirement: BF ∈ {-1, 0, +1} for EVERY node.

BF = +1 → left-heavy (acceptable)
BF =  0 → perfectly balanced
BF = -1 → right-heavy (acceptable)
BF = +2 or -2 → UNBALANCED → rotation needed!
```

### AVL Node Structure

```c
typedef struct AVLNode {
    int data;
    struct AVLNode* left;
    struct AVLNode* right;
    int height;               /* store height for O(1) balance factor calculation */
} AVLNode;

int avl_height(AVLNode* n) {
    return n ? n->height : -1;
}

int balance_factor(AVLNode* n) {
    return n ? avl_height(n->left) - avl_height(n->right) : 0;
}

void update_height(AVLNode* n) {
    if (n) {
        int lh = avl_height(n->left);
        int rh = avl_height(n->right);
        n->height = 1 + (lh > rh ? lh : rh);
    }
}
```

### Rotations — The Core Mechanism

When a node's BF becomes ±2, we restore balance using **rotations**. A rotation is a local restructuring that preserves BST order.

#### Right Rotation (LL Case — Left-Left imbalance)

**Triggered when**: BF(node) = +2 AND BF(node.left) ≥ 0

```
BEFORE:              AFTER right rotation:
      [C](BF=+2)           [B]
     /                    /   \
   [B](BF=+1)           [A]   [C]
   /
 [A]

BST order preserved: A < B < C  ✓
```

```
ALGORITHM right_rotate(z):
  y = z.left
  T2 = y.right
  
  y.right = z         ← z becomes right child of y
  z.left  = T2        ← T2 (between y and z) becomes z's left child
  
  update height of z  ← z is now lower, update first
  update height of y  ← y is now higher
  
  return y            ← y is the new root of this subtree
```

**C:**
```c
AVLNode* right_rotate(AVLNode* z) {
    AVLNode* y  = z->left;
    AVLNode* T2 = y->right;

    y->right = z;
    z->left  = T2;

    update_height(z);   /* z updated first (it's now lower) */
    update_height(y);   /* y updated second */

    return y;           /* y is new subtree root */
}
```

#### Left Rotation (RR Case — Right-Right imbalance)

**Triggered when**: BF(node) = -2 AND BF(node.right) ≤ 0

```
BEFORE:              AFTER left rotation:
  [A](BF=-2)                [B]
      \                    /   \
      [B](BF=-1)          [A]  [C]
          \
          [C]
```

```c
AVLNode* left_rotate(AVLNode* z) {
    AVLNode* y  = z->right;
    AVLNode* T2 = y->left;

    y->left  = z;
    z->right = T2;

    update_height(z);
    update_height(y);

    return y;
}
```

#### Left-Right Rotation (LR Case)

**Triggered when**: BF(node) = +2 AND BF(node.left) = -1

```
BEFORE:                     AFTER:
     [C](BF=+2)                 [B]
    /                          /   \
  [A](BF=-1)                 [A]   [C]
      \
      [B]

Step 1: Left-rotate [A]  →  gets us to LL case
Step 2: Right-rotate [C]
```

```c
/* LR Case: left-rotate the left child, then right-rotate root */
/* In the insert function, handled as: */
if (balance_factor(node) == 2 && balance_factor(node->left) == -1) {
    node->left = left_rotate(node->left);
    return right_rotate(node);
}
```

#### Right-Left Rotation (RL Case)

**Triggered when**: BF(node) = -2 AND BF(node.right) = +1

```
BEFORE:                     AFTER:
  [A](BF=-2)                    [B]
      \                        /   \
      [C](BF=+1)              [A]  [C]
      /
    [B]

Step 1: Right-rotate [C] → gets us to RR case
Step 2: Left-rotate  [A]
```

### Four Rotation Cases Summary

```
┌──────────┬──────────────────────┬─────────────────────────────────────┐
│ Case     │ Condition            │ Fix                                 │
├──────────┼──────────────────────┼─────────────────────────────────────┤
│ LL       │ BF=+2, left BF ≥ 0  │ Right rotate at unbalanced node     │
│ RR       │ BF=-2, right BF ≤ 0 │ Left rotate at unbalanced node      │
│ LR       │ BF=+2, left BF = -1 │ Left rotate left child, then right  │
│ RL       │ BF=-2, right BF = +1│ Right rotate right child, then left │
└──────────┴──────────────────────┴─────────────────────────────────────┘
```

### Complete AVL Insert (C)

```c
AVLNode* new_avl_node(int val) {
    AVLNode* n = (AVLNode*)malloc(sizeof(AVLNode));
    n->data = val;
    n->left = n->right = NULL;
    n->height = 0;
    return n;
}

AVLNode* avl_insert(AVLNode* root, int val) {
    /* ── STEP 1: Normal BST insert ─────────────────── */
    if (root == NULL) return new_avl_node(val);

    if (val < root->data)
        root->left  = avl_insert(root->left,  val);
    else if (val > root->data)
        root->right = avl_insert(root->right, val);
    else
        return root; /* Duplicate: no insert */

    /* ── STEP 2: Update height ──────────────────────── */
    update_height(root);

    /* ── STEP 3: Get balance factor ─────────────────── */
    int bf = balance_factor(root);

    /* ── STEP 4: Rebalance if needed ────────────────── */

    /* LL Case */
    if (bf == 2 && balance_factor(root->left) >= 0)
        return right_rotate(root);

    /* RR Case */
    if (bf == -2 && balance_factor(root->right) <= 0)
        return left_rotate(root);

    /* LR Case */
    if (bf == 2 && balance_factor(root->left) == -1) {
        root->left = left_rotate(root->left);
        return right_rotate(root);
    }

    /* RL Case */
    if (bf == -2 && balance_factor(root->right) == 1) {
        root->right = right_rotate(root->right);
        return left_rotate(root);
    }

    return root; /* No rotation needed */
}
```

---

## 15. Important Binary Tree Algorithms

### 15.1 Maximum Path Sum

**Problem**: Find the path in the tree where the sum of node values is maximum. The path can start and end at any node.

```
Tree:
      [-10]
      /    \
    [9]    [20]
           /   \
         [15]  [7]

Max path: 15 → 20 → 7 = 42
```

```
ALGORITHM max_path_sum(node, &global_max):
  if node is NULL → return 0
  
  /* Get max contribution from left and right (ignore if negative) */
  left_gain  = max(0, max_path_sum(node.left,  &global_max))
  right_gain = max(0, max_path_sum(node.right, &global_max))
  
  /* Current path through this node */
  path_through_node = node.data + left_gain + right_gain
  
  /* Update global maximum */
  global_max = max(global_max, path_through_node)
  
  /* Return max single-branch contribution upward */
  return node.data + max(left_gain, right_gain)
```

**C:**
```c
#include <limits.h>

int max_gain(Node* root, int* global_max) {
    if (root == NULL) return 0;

    int lg = max_gain(root->left,  global_max);
    int rg = max_gain(root->right, global_max);

    int left_gain  = lg > 0 ? lg : 0;
    int right_gain = rg > 0 ? rg : 0;

    int path = root->data + left_gain + right_gain;
    if (path > *global_max) *global_max = path;

    int branch = left_gain > right_gain ? left_gain : right_gain;
    return root->data + branch;
}

int max_path_sum(Node* root) {
    int result = INT_MIN;
    max_gain(root, &result);
    return result;
}
```

---

### 15.2 Check if Balanced

**Problem**: Determine if the tree is height-balanced (every node's subtrees differ in height by at most 1).

**Naïve approach**: Call `height()` at every node → O(N²) — recomputes heights repeatedly.

**Optimal approach**: Compute height and check balance in a single post-order pass → O(N).

```
ALGORITHM check_balanced(node):
  if node is NULL → return height=0, balanced=true
  
  left_h,  left_ok  = check_balanced(node.left)
  right_h, right_ok = check_balanced(node.right)
  
  this_balanced = left_ok && right_ok && |left_h - right_h| <= 1
  this_height   = 1 + max(left_h, right_h)
  
  return this_height, this_balanced
```

**C:**
```c
/* Returns -1 if unbalanced, else returns height */
int check_balanced(Node* root) {
    if (root == NULL) return 0;

    int lh = check_balanced(root->left);
    if (lh == -1) return -1;   /* propagate failure up */

    int rh = check_balanced(root->right);
    if (rh == -1) return -1;

    int diff = lh - rh;
    if (diff < -1 || diff > 1) return -1;   /* unbalanced here */

    return 1 + (lh > rh ? lh : rh);
}

int is_balanced(Node* root) {
    return check_balanced(root) != -1;
}
```

---

### 15.3 Symmetric Tree (Mirror Check)

**Problem**: Is the tree a mirror of itself (symmetric around the center)?

```
Symmetric:       Not Symmetric:
      [1]               [1]
     /   \             /   \
   [2]   [2]         [2]   [2]
  /   \ /   \       /       \
[3]  [4][4] [3]   [3]       [3]
                 (left has left child, right has right child)
```

```
ALGORITHM is_mirror(left, right):
  if both NULL → true
  if one NULL, other not → false
  if left.data != right.data → false
  return is_mirror(left.left,  right.right)   ← outer pair
      && is_mirror(left.right, right.left)    ← inner pair
```

**C:**
```c
int is_mirror(Node* left, Node* right) {
    if (!left && !right) return 1;
    if (!left || !right) return 0;
    return (left->data == right->data)
        && is_mirror(left->left,  right->right)
        && is_mirror(left->right, right->left);
}

int is_symmetric(Node* root) {
    if (!root) return 1;
    return is_mirror(root->left, root->right);
}
```

---

## 16. Lowest Common Ancestor (LCA)

**Definition**: The LCA of two nodes `p` and `q` in a tree is the deepest node that is an ancestor of BOTH p and q.

```
Tree:
          [3]
         /   \
       [5]   [1]
      /   \  / \
    [6]  [2][0][8]
        /   \
      [7]   [4]

LCA(5, 1) = 3
LCA(5, 4) = 5   (5 is ancestor of 4 and ancestor of itself)
LCA(6, 4) = 5
```

### Algorithm for General Binary Tree

```
ALGORITHM lca(node, p, q):
  if node is NULL → return NULL
  if node == p OR node == q → return node    ← found one target!
  
  left_lca  = lca(node.left,  p, q)
  right_lca = lca(node.right, p, q)
  
  if left_lca != NULL AND right_lca != NULL → return node   ← p and q on different sides!
  if left_lca  != NULL → return left_lca
  else                 → return right_lca
```

**Decision tree:**

```
Processing node X:
  │
  ├─ X == p or X == q?  →  YES: return X (bubble up)
  │
  └─ NO: recurse left and right
       │
       ├─ Both sides returned non-NULL?  →  X is the LCA! return X
       ├─ Only left returned non-NULL?   →  LCA is in left subtree
       └─ Only right returned non-NULL?  →  LCA is in right subtree
```

**C:**
```c
Node* lca(Node* root, int p, int q) {
    if (root == NULL) return NULL;
    if (root->data == p || root->data == q) return root;

    Node* left_lca  = lca(root->left,  p, q);
    Node* right_lca = lca(root->right, p, q);

    if (left_lca && right_lca) return root;       /* p and q split */
    return left_lca ? left_lca : right_lca;
}
```

**Rust:**
```rust
fn lca<'a>(node: &'a Option<Box<Node>>, p: i32, q: i32) -> Option<&'a Node> {
    match node {
        None => None,
        Some(n) => {
            if n.data == p || n.data == q {
                return Some(n);
            }
            let left  = lca(&n.left,  p, q);
            let right = lca(&n.right, p, q);
            match (left, right) {
                (Some(_), Some(_)) => Some(n),   // Both sides found
                (l, r)             => l.or(r),
            }
        }
    }
}
```

**Go:**
```go
func LCA(root *Node, p, q int) *Node {
    if root == nil {
        return nil
    }
    if root.Data == p || root.Data == q {
        return root
    }
    left  := LCA(root.Left,  p, q)
    right := LCA(root.Right, p, q)
    if left != nil && right != nil {
        return root
    }
    if left != nil {
        return left
    }
    return right
}
```

---

## 17. Tree Diameter

**Definition**: The diameter (or width) of a binary tree is the length of the LONGEST path between any two nodes. The path may or may not pass through the root.

```
Tree:
          [1]
         /   \
       [2]   [3]
      /   \
    [4]   [5]

Diameter = 3 (path: 4 → 2 → 1 → 3 or 5 → 2 → 1 → 3)
```

```
ALGORITHM diameter(node, &max_diameter):
  if node is NULL → return 0
  
  left_h  = diameter(node.left,  &max_diameter)
  right_h = diameter(node.right, &max_diameter)
  
  /* Path through this node = left height + right height */
  path_length = left_h + right_h
  max_diameter = max(max_diameter, path_length)
  
  /* Return height for parent's use */
  return 1 + max(left_h, right_h)
```

**C:**
```c
int diameter_helper(Node* root, int* max_d) {
    if (root == NULL) return 0;

    int lh = diameter_helper(root->left,  max_d);
    int rh = diameter_helper(root->right, max_d);

    if (lh + rh > *max_d) *max_d = lh + rh;

    return 1 + (lh > rh ? lh : rh);
}

int diameter(Node* root) {
    int result = 0;
    diameter_helper(root, &result);
    return result;
}
```

**Rust:**
```rust
fn diameter_helper(node: &Option<Box<Node>>, max_d: &mut i32) -> i32 {
    match node {
        None => 0,
        Some(n) => {
            let lh = diameter_helper(&n.left,  max_d);
            let rh = diameter_helper(&n.right, max_d);
            *max_d = (*max_d).max(lh + rh);
            1 + lh.max(rh)
        }
    }
}

fn diameter(root: &Option<Box<Node>>) -> i32 {
    let mut result = 0;
    diameter_helper(root, &mut result);
    result
}
```

**Go:**
```go
func DiameterHelper(node *Node, maxD *int) int {
    if node == nil {
        return 0
    }
    lh := DiameterHelper(node.Left,  maxD)
    rh := DiameterHelper(node.Right, maxD)
    if lh+rh > *maxD {
        *maxD = lh + rh
    }
    if lh > rh {
        return 1 + lh
    }
    return 1 + rh
}

func Diameter(root *Node) int {
    result := 0
    DiameterHelper(root, &result)
    return result
}
```

---

## 18. Level Order / BFS Traversal

**Level-order traversal** visits nodes level by level, left to right. It uses a **Queue**.

```
Tree:
          [1]
         /   \
       [2]   [3]
      /   \     \
    [4]   [5]   [6]

Level-order: 1  2 3  4 5 6
             ^  ^^^  ^^^^^
             L0  L1    L2
```

**Algorithm:**

```
ALGORITHM level_order(root):
  if root is NULL → return
  
  queue = empty queue
  enqueue(root)
  
  while queue not empty:
    node = dequeue()
    VISIT(node)
    
    if node.left  → enqueue(node.left)
    if node.right → enqueue(node.right)
```

**C:**
```c
void level_order(Node* root) {
    if (!root) return;

    Node* queue[MAX_STACK];
    int front = 0, rear = 0;
    queue[rear++] = root;

    while (front < rear) {
        Node* curr = queue[front++];
        printf("%d ", curr->data);

        if (curr->left)  queue[rear++] = curr->left;
        if (curr->right) queue[rear++] = curr->right;
    }
}
```

**Collecting levels separately (returning 2D array of levels):**

```c
/* Returns each level as a separate row */
void level_order_by_level(Node* root) {
    if (!root) return;

    Node* queue[MAX_STACK];
    int front = 0, rear = 0;
    queue[rear++] = root;

    while (front < rear) {
        int level_size = rear - front;   /* nodes in current level */
        printf("[ ");
        for (int i = 0; i < level_size; i++) {
            Node* curr = queue[front++];
            printf("%d ", curr->data);
            if (curr->left)  queue[rear++] = curr->left;
            if (curr->right) queue[rear++] = curr->right;
        }
        printf("]\n");
    }
}
/* Output:
   [ 1 ]
   [ 2 3 ]
   [ 4 5 6 ]
*/
```

**Go:**
```go
func LevelOrder(root *Node) [][]int {
    if root == nil {
        return nil
    }
    var result [][]int
    queue := []*Node{root}

    for len(queue) > 0 {
        levelSize := len(queue)
        var level []int

        for i := 0; i < levelSize; i++ {
            node := queue[0]
            queue = queue[1:]
            level = append(level, node.Data)
            if node.Left  != nil { queue = append(queue, node.Left)  }
            if node.Right != nil { queue = append(queue, node.Right) }
        }
        result = append(result, level)
    }
    return result
}
```

**Rust:**
```rust
use std::collections::VecDeque;

fn level_order(root: &Option<Box<Node>>) -> Vec<Vec<i32>> {
    let mut result = Vec::new();
    if root.is_none() { return result; }

    let mut queue: VecDeque<&Box<Node>> = VecDeque::new();
    if let Some(r) = root { queue.push_back(r); }

    while !queue.is_empty() {
        let level_size = queue.len();
        let mut level  = Vec::new();

        for _ in 0..level_size {
            let node = queue.pop_front().unwrap();
            level.push(node.data);
            if let Some(l) = &node.left  { queue.push_back(l); }
            if let Some(r) = &node.right { queue.push_back(r); }
        }
        result.push(level);
    }
    result
}
```

---

## 19. Serialization and Deserialization

**Serialization**: Convert a tree to a string/array so it can be stored or transmitted.
**Deserialization**: Reconstruct the tree from that string/array.

This is a classic interview problem (LeetCode 297).

### Pre-order Serialization with NULL markers

```
Tree:              Pre-order with nulls:
    [1]            "1,2,4,#,#,5,#,#,3,#,6,#,#"
   /   \            where # = NULL
 [2]   [3]
 / \     \
[4] [5]  [6]
```

**C:**
```c
#include <string.h>
#define BUFSIZE 4096

/* Serialize tree to buffer */
void serialize(Node* root, char* buf, int* pos) {
    if (root == NULL) {
        *pos += sprintf(buf + *pos, "#,");
        return;
    }
    *pos += sprintf(buf + *pos, "%d,", root->data);
    serialize(root->left,  buf, pos);
    serialize(root->right, buf, pos);
}

/* Deserialize from token stream */
Node* deserialize_helper(char** tokens, int* idx, int count) {
    if (*idx >= count) return NULL;
    char* token = tokens[(*idx)++];
    if (strcmp(token, "#") == 0) return NULL;

    Node* node = new_node(atoi(token));
    node->left  = deserialize_helper(tokens, idx, count);
    node->right = deserialize_helper(tokens, idx, count);
    return node;
}
```

**Go:**
```go
import (
    "strconv"
    "strings"
)

func Serialize(root *Node) string {
    if root == nil {
        return "#"
    }
    left  := Serialize(root.Left)
    right := Serialize(root.Right)
    return strconv.Itoa(root.Data) + "," + left + "," + right
}

func Deserialize(data string) *Node {
    tokens := strings.Split(data, ",")
    idx    := 0
    return deserializeHelper(tokens, &idx)
}

func deserializeHelper(tokens []string, idx *int) *Node {
    if *idx >= len(tokens) || tokens[*idx] == "#" {
        *idx++
        return nil
    }
    val, _ := strconv.Atoi(tokens[*idx])
    *idx++
    node        := NewNode(val)
    node.Left   = deserializeHelper(tokens, idx)
    node.Right  = deserializeHelper(tokens, idx)
    return node
}
```

---

## 20. Complexity Reference

### BST Operations

```
┌────────────────────┬──────────────┬──────────────────────────────────────┐
│ Operation          │ Average Case │ Worst Case (Degenerate/Skewed tree)   │
├────────────────────┼──────────────┼──────────────────────────────────────┤
│ Search             │ O(log N)     │ O(N)                                 │
│ Insert             │ O(log N)     │ O(N)                                 │
│ Delete             │ O(log N)     │ O(N)                                 │
│ Find Min/Max       │ O(log N)     │ O(N)                                 │
│ In-order traversal │ O(N)         │ O(N)                                 │
│ Space (recursive)  │ O(log N)     │ O(N)  [call stack depth]             │
└────────────────────┴──────────────┴──────────────────────────────────────┘
```

### AVL Tree (Balanced BST)

```
┌────────────────────┬─────────────────────────────────────────────────────┐
│ Operation          │ Complexity (always guaranteed)                       │
├────────────────────┼─────────────────────────────────────────────────────┤
│ Search             │ O(log N)                                             │
│ Insert             │ O(log N)  — includes at most 2 rotations             │
│ Delete             │ O(log N)  — may need O(log N) rotations up the tree  │
│ Space              │ O(N)  for storing nodes                              │
└────────────────────┴─────────────────────────────────────────────────────┘
```

### Traversal Complexities

```
┌──────────────┬────────────┬────────────────────────────────────────────┐
│ Traversal    │ Time       │ Space                                       │
├──────────────┼────────────┼────────────────────────────────────────────┤
│ In-order     │ O(N)       │ O(H)  where H = tree height (call stack)   │
│ Pre-order    │ O(N)       │ O(H)                                        │
│ Post-order   │ O(N)       │ O(H)                                        │
│ Level-order  │ O(N)       │ O(W)  where W = max width of tree           │
│              │            │       For perfect tree: W = N/2             │
└──────────────┴────────────┴────────────────────────────────────────────┘

Balanced tree: H = O(log N) → space = O(log N)
Skewed tree:   H = O(N)     → space = O(N)
```

---

## 21. Mental Models & Problem-Solving Patterns

### The Three Recursion Questions

Before coding ANY tree problem, answer these three:

```
1. BASE CASE: What do I return for NULL? What do I return for a leaf?
2. INDUCTIVE STEP: If I have answers from left and right children,
                   how do I compute THIS node's answer?
3. RETURN VALUE: What do I pass UPWARD to my parent?
```

This is the **DFS post-order pattern** and it solves ~70% of tree problems.

### Pattern Recognition Chart

```
PROBLEM TYPE                        →  APPROACH
────────────────────────────────────────────────────────────────
Find height/depth/size              →  Post-order DFS, return value upward
Path sum / path existence           →  DFS with running sum, update global var
Level-by-level processing           →  BFS with level-size trick
Find k-th element in BST            →  In-order DFS with counter
Validate BST                        →  DFS with [min, max] range
LCA                                 →  Post-order: bubble up found nodes
Tree construction from traversals   →  Pre-order gives root; In-order splits L/R
Check symmetry/mirror               →  Pair-wise DFS (left.left vs right.right)
Serialize/Deserialize               →  Pre-order with NULL markers
Connect nodes at same level         →  BFS, or right-child pointer trick
```

### The Dual Traversal Insight

**Reconstruct a unique binary tree from two traversals** (classic problem):

```
Pre-order [root, left, right] tells you the ROOT.
In-order  [left, root, right] tells you what's LEFT and RIGHT of root.

Algorithm:
  1. pre[0] is the root.
  2. Find pre[0] in in-order → splits in-order into left and right subtrees.
  3. Sizes of splits tell you how many elements in each subtree.
  4. Recurse on left and right subarrays.

You CANNOT reconstruct uniquely from pre+post alone (ambiguous).
You NEED in-order + (pre OR post) to reconstruct.
```

### Cognitive Principles for Mastery

**1. Chunking**: Don't think of "rotate left" as 5 pointer operations — think of it as ONE atomic operation: "pivot goes down, its child comes up." Your brain should see the pattern, not the steps.

**2. Deliberate Practice**: After solving a tree problem, solve it again without looking at your solution. Then solve it in a different language. Then explain it to someone. Three reps, three modalities.

**3. The Feynman Technique**: If you cannot explain WHY the LCA algorithm works (why returning the node when `node == p` is correct), you don't understand it — you memorized it. Push until you can explain it.

**4. Spaced Repetition**: Revisit these concepts after 1 day, 3 days, 1 week, 2 weeks. Memory consolidates during sleep.

**5. Schema Building**: Every new algorithm should slot into your existing mental schema. Ask: "How is this similar to what I already know?" Diameter = height problem + global max. LCA = post-order search + bubble up pattern.

---

## 22. Deliberate Practice Roadmap

### Phase 1 — Foundation (Week 1-2)
```
□ Implement Node struct in C, Rust, Go from memory
□ Build tree manually and via level-order array
□ Implement all 4 traversals recursively
□ Implement height, size, count_leaves
□ Implement BST insert, search, delete
□ Validate BST with range-based approach
```

### Phase 2 — Patterns (Week 3-4)
```
□ Implement isBalanced (O(N) version)
□ Implement diameter
□ Implement symmetric check
□ Implement invert/mirror
□ Implement LCA (general tree)
□ Implement level-order with level separation
□ Implement max path sum
```

### Phase 3 — Advanced (Week 5-8)
```
□ Implement AVL insert with all 4 rotation cases
□ Implement serialize/deserialize
□ Reconstruct tree from pre-order + in-order
□ k-th smallest in BST
□ Right side view of tree
□ Zigzag level order traversal
□ Morris Traversal (O(1) space in-order)
□ Threaded Binary Tree concepts
```

### Problem Difficulty Ladder

```
EASY:
  □ Maximum depth of binary tree
  □ Same tree check
  □ Symmetric tree
  □ Invert binary tree
  □ Path sum (root to leaf)

MEDIUM:
  □ Binary tree level-order traversal
  □ Validate BST
  □ Construct BST from preorder traversal
  □ LCA of BST
  □ LCA of binary tree
  □ Diameter of binary tree
  □ Serialize and deserialize

HARD:
  □ Binary tree maximum path sum
  □ Recover BST (two nodes swapped by mistake)
  □ Count complete tree nodes in O(log²N)
  □ Vertical order traversal
  □ Binary tree cameras (greedy)
```

---

## Final Summary — The Big Picture

```
BINARY TREE MASTERY MAP
══════════════════════════════════════════════════════════════
 FOUNDATION                 OPERATIONS              ALGORITHMS
 ─────────────             ──────────────          ────────────
 Node struct               Traversals:             Height/Size
 Linked repr.               In-order               Diameter
 Array repr.                Pre-order              Max path sum
 Tree types:                Post-order             LCA
   Full                     Level-order(BFS)       Symmetric check
   Complete                                        Invert
   Perfect                 BST Ops:               Serialize
   Balanced                 Insert                 Validate BST
   Degenerate               Search                 Construct from traversals
                            Delete
                            Min/Max
                           AVL:
                            Balance factor
                            Rotations (LL,RR,LR,RL)
══════════════════════════════════════════════════════════════

RECURSION TEMPLATE (applies to ~70% of tree problems):
  solve(node):
    if node == NULL: return base_case
    left_ans  = solve(node.left)
    right_ans = solve(node.right)
    this_ans  = combine(left_ans, right_ans, node.data)
    update_global_if_needed(this_ans)
    return this_ans

The monk's path: understand one concept completely before moving to the next.
A tree grows strong from deep roots — so does your understanding.
══════════════════════════════════════════════════════════════
```

---

*Guide compiled for elite DSA mastery. Every concept here is a foundation stone — master each before moving forward. The difference between top 1% and the rest is not knowing more algorithms — it's understanding fewer concepts with extraordinary depth.*