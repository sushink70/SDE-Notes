# 🌳 Complete Guide to Tree Traversal
## From Zero to World-Class Mastery

> *"To traverse a tree is to understand the shape of thought itself — every path reveals a different truth about the same structure."*

---

## 📑 Table of Contents

1. [What is a Tree? — Ground Zero](#1-what-is-a-tree--ground-zero)
2. [Core Terminology — The Language of Trees](#2-core-terminology--the-language-of-trees)
3. [Binary Tree — The Foundation](#3-binary-tree--the-foundation)
4. [What is Tree Traversal?](#4-what-is-tree-traversal)
5. [The Big Picture — Traversal Taxonomy](#5-the-big-picture--traversal-taxonomy)
6. [DFS Traversals — Going Deep](#6-dfs-traversals--going-deep)
   - 6.1 Inorder (LNR)
   - 6.2 Preorder (NLR)
   - 6.3 Postorder (LRN)
7. [BFS Traversal — Level Order](#7-bfs-traversal--level-order)
8. [Advanced Traversals](#8-advanced-traversals)
   - 8.1 Reverse Level Order
   - 8.2 Zigzag / Spiral Traversal
   - 8.3 Boundary Traversal
   - 8.4 Vertical Order Traversal
   - 8.5 Diagonal Traversal
9. [Morris Traversal — O(1) Space Magic](#9-morris-traversal--o1-space-magic)
10. [Iterative DFS — Explicit Stack](#10-iterative-dfs--explicit-stack)
11. [N-ary Tree Traversal](#11-n-ary-tree-traversal)
12. [Complexity Master Table](#12-complexity-master-table)
13. [Expert Mental Models](#13-expert-mental-models)

---

## 1. What is a Tree? — Ground Zero

A **tree** is a hierarchical (parent-child) data structure made of **nodes** connected by **edges**. Unlike arrays or linked lists (which are linear — one after another), a tree branches out — one node can connect to many children.

**Real-world analogy:**
- A **family tree**: you have grandparents → parents → children.
- A **file system**: `/home` → `/home/user` → `/home/user/docs`.
- A **company hierarchy**: CEO → VPs → Managers → Employees.

### Visual Anatomy of a Tree

```
              [A]          ← ROOT (top-most node, no parent)
             /   \
           [B]   [C]       ← INTERNAL NODES (have children)
           / \     \
         [D] [E]   [F]     ← LEAF NODES (no children)
```

> **Key rule:** A tree with N nodes always has exactly **N-1 edges**. There are **no cycles** (no loops).

---

## 2. Core Terminology — The Language of Trees

Before we traverse, you must master the vocabulary. These terms appear in every problem.

```
              [A]          ← Root
             /   \
           [B]   [C]       ← Children of A
           / \
         [D] [E]           ← D and E are siblings (same parent B)
              |
             [F]           ← Leaf node (no children)
```

| Term | Definition |
|---|---|
| **Node** | A single unit storing data + pointers to children |
| **Root** | The topmost node; has no parent |
| **Leaf** | A node with no children (end node) |
| **Edge** | The connection (link) between a parent and child |
| **Parent** | A node that has children |
| **Child** | A node directly connected below its parent |
| **Sibling** | Nodes sharing the same parent |
| **Ancestor** | Any node on the path from root to a given node |
| **Descendant** | Any node in the subtree rooted at a given node |
| **Depth of node** | Distance (edges) from root to that node |
| **Height of node** | Longest path (edges) from that node to a leaf |
| **Height of tree** | Height of the root node |
| **Level** | All nodes at same depth = same level (root = level 0) |
| **Subtree** | A node + all its descendants (a tree within a tree) |
| **Degree** | Number of children a node has |
| **Path** | Sequence of nodes connected by edges |
| **Internal Node** | A node with at least one child |
| **Successor** | In BST: the next larger node (smallest in right subtree) |
| **Predecessor** | In BST: the previous smaller node (largest in left subtree) |

### Height vs Depth Visualized

```
Level 0:          [A]          ← depth=0, height=3
                 /   \
Level 1:       [B]   [C]       ← depth=1, height=2 (B), height=1 (C)
               / \     \
Level 2:     [D] [E]   [F]     ← depth=2, height=0 (leaves)
             /
Level 3:   [G]                 ← depth=3, height=0 (leaf)
```

> **Memory trick:** Depth = distance FROM root (how deep you dug). Height = distance TO furthest leaf (how tall your subtree stands).

---

## 3. Binary Tree — The Foundation

A **Binary Tree** is a tree where every node has **at most 2 children**: a **left child** and a **right child**.

```
         [10]
        /    \
      [5]    [15]
      / \    /  \
    [3] [7] [12] [20]
```

### Types of Binary Trees

```
FULL Binary Tree:            COMPLETE Binary Tree:        PERFECT Binary Tree:
Every node has 0 or 2        All levels filled except     All levels completely
children (never 1)           last; last filled L→R        filled

      [1]                          [1]                        [1]
     /   \                        /   \                      /   \
   [2]   [3]                    [2]   [3]                  [2]   [3]
   / \                          / \   /                    / \ / \
 [4] [5]                      [4][5][6]                  [4][5][6][7]


BALANCED Binary Tree:        DEGENERATE Tree:
Height = O(log N)            Essentially a linked list
                             (each node has 1 child)
      [1]
     /   \                         [1]
   [2]   [3]                         \
   / \                               [2]
 [4] [5]                               \
                                       [3]
```

### Node Structure — Defined in All 3 Languages

**C:**
```c
#include <stdio.h>
#include <stdlib.h>

typedef struct TreeNode {
    int val;
    struct TreeNode *left;
    struct TreeNode *right;
} TreeNode;

// Helper: create a new node
TreeNode* new_node(int val) {
    TreeNode *node = (TreeNode*)malloc(sizeof(TreeNode));
    node->val   = val;
    node->left  = NULL;
    node->right = NULL;
    return node;
}
```

**Go:**
```go
package main

import "fmt"

type TreeNode struct {
    Val   int
    Left  *TreeNode
    Right *TreeNode
}

// Helper: create a new node
func newNode(val int) *TreeNode {
    return &TreeNode{Val: val}
}
```

**Rust:**
```rust
// Rust uses Box<T> for heap-allocated owned pointers
// Option<Box<TreeNode>> = either None (null) or Some(pointer)
#[derive(Debug)]
struct TreeNode {
    val: i32,
    left: Option<Box<TreeNode>>,
    right: Option<Box<TreeNode>>,
}

impl TreeNode {
    fn new(val: i32) -> Self {
        TreeNode { val, left: None, right: None }
    }
}
```

> **Rust concept — `Box<T>`:** Heap-allocated smart pointer. Needed because recursive structs can't be sized on the stack (infinite size). `Option<Box<TreeNode>>` means "either nothing (null) or a pointer to a node."

---

## 4. What is Tree Traversal?

**Traversal** = visiting every node in the tree **exactly once**, in a specific order.

**Why does order matter?**
- Different orders solve different problems.
- **Inorder** of a BST gives sorted output.
- **Postorder** is used to delete a tree (children before parents).
- **Preorder** is used to copy/serialize a tree.
- **Level order** is used in shortest path problems.

**Two fundamental strategies:**

```
+---------------------------+-------------------------------+
|  DFS (Depth-First Search) |  BFS (Breadth-First Search)   |
|  Goes DEEP before wide    |  Goes WIDE before deep        |
|  Uses: STACK (or recursion)|  Uses: QUEUE                  |
|  Variants: Pre/In/Post    |  Variant: Level Order         |
+---------------------------+-------------------------------+
```

---

## 5. The Big Picture — Traversal Taxonomy

```
                        TREE TRAVERSAL
                       /              \
               DFS                    BFS
          (Depth First)          (Breadth First)
         /      |      \               |
     Preorder Inorder Postorder   Level Order
     (NLR)    (LNR)   (LRN)
     
     ADVANCED:
     - Reverse Level Order
     - Zigzag / Spiral
     - Boundary Traversal
     - Vertical Order
     - Diagonal Traversal
     - Morris Traversal (O(1) space)
```

### Working Tree for All Examples

We'll use this single tree throughout the entire guide:

```
              [1]
            /     \
          [2]     [3]
         /   \   /   \
       [4]  [5] [6]  [7]
       /
     [8]
```

| Traversal | Output |
|---|---|
| Inorder (LNR) | 8, 4, 2, 5, 1, 6, 3, 7 |
| Preorder (NLR) | 1, 2, 4, 8, 5, 3, 6, 7 |
| Postorder (LRN) | 8, 4, 5, 2, 6, 7, 3, 1 |
| Level Order | 1 / 2,3 / 4,5,6,7 / 8 |

---

## 6. DFS Traversals — Going Deep

DFS explores as far as possible along a branch before backtracking. Think of it like exploring a maze — always go forward until you hit a wall, then come back.

**The three DFS traversals differ only in WHEN you process the current node (N) relative to its Left (L) and Right (R) subtrees.**

```
PREORDER:  N → L → R    (Process node FIRST, then children)
INORDER:   L → N → R    (Process LEFT, then node, then RIGHT)
POSTORDER: L → R → N    (Process children FIRST, then node)
```

---

### 6.1 Inorder Traversal (Left → Node → Right)

**Pattern:** Go all the way LEFT, process node, then go RIGHT.

**The golden rule:** Inorder traversal of a **BST** gives nodes in **sorted (ascending) order**.

#### Step-by-Step Trace

```
Tree:
              [1]
            /     \
          [2]     [3]
         /   \   /   \
       [4]  [5] [6]  [7]
       /
     [8]

Step 1: Go left from 1 → reach 2
Step 2: Go left from 2 → reach 4
Step 3: Go left from 4 → reach 8
Step 4: Go left from 8 → NULL → STOP
Step 5: PRINT 8 ✓ (no right child)
Step 6: Back to 4: PRINT 4 ✓
Step 7: Go right from 4 → NULL
Step 8: Back to 2: PRINT 2 ✓
Step 9: Go right from 2 → reach 5
Step 10: Go left from 5 → NULL → PRINT 5 ✓
Step 11: Back to 1: PRINT 1 ✓
Step 12: Go right from 1 → reach 3
Step 13: Go left from 3 → reach 6
Step 14: PRINT 6 ✓
Step 15: Back to 3: PRINT 3 ✓
Step 16: Go right from 3 → reach 7
Step 17: PRINT 7 ✓

OUTPUT: 8 → 4 → 2 → 5 → 1 → 6 → 3 → 7
```

#### Call Stack Visualization (Recursive)

```
inorder(1)
  inorder(2)
    inorder(4)
      inorder(8)
        inorder(NULL) → return
        PRINT 8
        inorder(NULL) → return
      PRINT 4
      inorder(NULL) → return
    PRINT 2
    inorder(5)
      inorder(NULL) → return
      PRINT 5
      inorder(NULL) → return
  PRINT 1
  inorder(3)
    inorder(6)
      inorder(NULL) → return
      PRINT 6
      inorder(NULL) → return
    PRINT 3
    inorder(7)
      inorder(NULL) → return
      PRINT 7
      inorder(NULL) → return
```

#### C Implementation — Inorder

```c
#include <stdio.h>
#include <stdlib.h>

typedef struct TreeNode {
    int val;
    struct TreeNode *left;
    struct TreeNode *right;
} TreeNode;

TreeNode* new_node(int val) {
    TreeNode *node = (TreeNode*)malloc(sizeof(TreeNode));
    node->val = val;
    node->left = node->right = NULL;
    return node;
}

// RECURSIVE: O(N) time, O(H) space (H = height, call stack)
void inorder_recursive(TreeNode *root) {
    if (root == NULL) return;   // Base case: empty subtree
    inorder_recursive(root->left);   // L
    printf("%d ", root->val);        // N
    inorder_recursive(root->right);  // R
}

int main() {
    //        [1]
    //       /   \
    //     [2]   [3]
    //    /  \  /  \
    //  [4] [5][6] [7]
    //  /
    // [8]
    TreeNode *root = new_node(1);
    root->left = new_node(2);
    root->right = new_node(3);
    root->left->left = new_node(4);
    root->left->right = new_node(5);
    root->right->left = new_node(6);
    root->right->right = new_node(7);
    root->left->left->left = new_node(8);

    printf("Inorder: ");
    inorder_recursive(root);  // 8 4 2 5 1 6 3 7
    printf("\n");
    return 0;
}
```

#### Go Implementation — Inorder

```go
package main

import "fmt"

type TreeNode struct {
    Val   int
    Left  *TreeNode
    Right *TreeNode
}

func newNode(val int) *TreeNode {
    return &TreeNode{Val: val}
}

// RECURSIVE inorder
func inorderRecursive(root *TreeNode, result *[]int) {
    if root == nil {
        return
    }
    inorderRecursive(root.Left, result)   // L
    *result = append(*result, root.Val)   // N
    inorderRecursive(root.Right, result)  // R
}

func main() {
    root := newNode(1)
    root.Left = newNode(2)
    root.Right = newNode(3)
    root.Left.Left = newNode(4)
    root.Left.Right = newNode(5)
    root.Right.Left = newNode(6)
    root.Right.Right = newNode(7)
    root.Left.Left.Left = newNode(8)

    var result []int
    inorderRecursive(root, &result)
    fmt.Println("Inorder:", result) // [8 4 2 5 1 6 3 7]
}
```

#### Rust Implementation — Inorder

```rust
#[derive(Debug)]
struct TreeNode {
    val: i32,
    left: Option<Box<TreeNode>>,
    right: Option<Box<TreeNode>>,
}

impl TreeNode {
    fn new(val: i32) -> Box<Self> {
        Box::new(TreeNode { val, left: None, right: None })
    }
}

// RECURSIVE inorder — borrows the node immutably
fn inorder_recursive(root: &Option<Box<TreeNode>>, result: &mut Vec<i32>) {
    if let Some(node) = root {        // Pattern match: if not None
        inorder_recursive(&node.left, result);   // L
        result.push(node.val);                   // N
        inorder_recursive(&node.right, result);  // R
    }
}

fn main() {
    let mut root = TreeNode::new(1);
    root.left = Some(TreeNode::new(2));
    root.right = Some(TreeNode::new(3));
    root.left.as_mut().unwrap().left = Some(TreeNode::new(4));
    root.left.as_mut().unwrap().right = Some(TreeNode::new(5));
    root.right.as_mut().unwrap().left = Some(TreeNode::new(6));
    root.right.as_mut().unwrap().right = Some(TreeNode::new(7));
    root.left.as_mut().unwrap().left.as_mut().unwrap().left = Some(TreeNode::new(8));

    let mut result = Vec::new();
    inorder_recursive(&Some(root), &mut result);
    println!("Inorder: {:?}", result); // [8, 4, 2, 5, 1, 6, 3, 7]
}
```

---

### 6.2 Preorder Traversal (Node → Left → Right)

**Pattern:** Process node FIRST, then explore left, then right. You see the node BEFORE its subtrees.

**Key use cases:**
- Copying / cloning a tree (you need to create parent before children)
- Serialization (convert tree to string for storage)
- Prefix expression evaluation (e.g., `+ 3 4` → 3 + 4)

#### Step-by-Step Trace

```
Tree:
              [1]
            /     \
          [2]     [3]
         /   \   /   \
       [4]  [5] [6]  [7]
       /
     [8]

PRINT 1 ✓  → go left
  PRINT 2 ✓ → go left
    PRINT 4 ✓ → go left
      PRINT 8 ✓ → no children
    → go right from 4 → NULL
  → go right from 2
    PRINT 5 ✓ → no children
→ go right from 1
  PRINT 3 ✓ → go left
    PRINT 6 ✓ → no children
  → go right from 3
    PRINT 7 ✓ → no children

OUTPUT: 1 → 2 → 4 → 8 → 5 → 3 → 6 → 7
```

#### C Implementation — Preorder

```c
// RECURSIVE preorder: O(N) time, O(H) space
void preorder_recursive(TreeNode *root) {
    if (root == NULL) return;
    printf("%d ", root->val);        // N — FIRST
    preorder_recursive(root->left);  // L
    preorder_recursive(root->right); // R
}
```

#### Go Implementation — Preorder

```go
func preorderRecursive(root *TreeNode, result *[]int) {
    if root == nil {
        return
    }
    *result = append(*result, root.Val)    // N — FIRST
    preorderRecursive(root.Left, result)   // L
    preorderRecursive(root.Right, result)  // R
}
```

#### Rust Implementation — Preorder

```rust
fn preorder_recursive(root: &Option<Box<TreeNode>>, result: &mut Vec<i32>) {
    if let Some(node) = root {
        result.push(node.val);                    // N — FIRST
        preorder_recursive(&node.left, result);   // L
        preorder_recursive(&node.right, result);  // R
    }
}
```

---

### 6.3 Postorder Traversal (Left → Right → Node)

**Pattern:** Process children FIRST, then the node. You see the node AFTER its subtrees.

**Key use cases:**
- Deleting a tree (must delete children before parent, else memory leak)
- Evaluating expression trees (evaluate sub-expressions before combining)
- Computing size/height (need subtree info before processing root)
- Postfix expression evaluation (e.g., `3 4 +` → 3 + 4)

#### Step-by-Step Trace

```
Tree:
              [1]
            /     \
          [2]     [3]
         /   \   /   \
       [4]  [5] [6]  [7]
       /
     [8]

Go left all the way:
  1 → 2 → 4 → 8 → NULL
  LEFT of 8 = NULL, RIGHT of 8 = NULL → PRINT 8 ✓
  Back to 4: left done. Go right → NULL → PRINT 4 ✓
  Back to 2: left done. Go right → 5
    LEFT of 5 = NULL, RIGHT of 5 = NULL → PRINT 5 ✓
  Back to 2: both done → PRINT 2 ✓
Back to 1: left done. Go right → 3
  Go left → 6: both NULL → PRINT 6 ✓
  Back to 3: go right → 7: both NULL → PRINT 7 ✓
  Back to 3: both done → PRINT 3 ✓
Back to 1: both done → PRINT 1 ✓

OUTPUT: 8 → 4 → 5 → 2 → 6 → 7 → 3 → 1
```

#### C Implementation — Postorder

```c
// RECURSIVE postorder: O(N) time, O(H) space
void postorder_recursive(TreeNode *root) {
    if (root == NULL) return;
    postorder_recursive(root->left);  // L
    postorder_recursive(root->right); // R
    printf("%d ", root->val);         // N — LAST
}
```

#### Go Implementation — Postorder

```go
func postorderRecursive(root *TreeNode, result *[]int) {
    if root == nil {
        return
    }
    postorderRecursive(root.Left, result)   // L
    postorderRecursive(root.Right, result)  // R
    *result = append(*result, root.Val)     // N — LAST
}
```

#### Rust Implementation — Postorder

```rust
fn postorder_recursive(root: &Option<Box<TreeNode>>, result: &mut Vec<i32>) {
    if let Some(node) = root {
        postorder_recursive(&node.left, result);   // L
        postorder_recursive(&node.right, result);  // R
        result.push(node.val);                     // N — LAST
    }
}
```

---

### DFS Comparison Decision Tree

```
You need to solve a tree problem...
              |
     What information do you need?
    /              |               \
"Visit each     "Process          "Process
 node, parent    children before   left subtree
 before child"   parent"           before root"
    |                |                  |
 PREORDER         POSTORDER           INORDER
 (copy, serial,   (delete, eval,      (sorted BST,
  prefix expr)     height, size,       search, range
                   postfix expr)       queries)
```

---

## 7. BFS Traversal — Level Order

**BFS (Breadth-First Search)** visits nodes level by level, left to right. Think of it like ripples in a pond — wave by wave outward.

**Key insight:** BFS uses a **QUEUE** (FIFO — First In, First Out). This is the fundamental difference from DFS (which uses a stack/recursion).

### Why a Queue works for BFS

```
QUEUE behavior: [front] ← dequeue    enqueue → [back]

Process nodes of level N:
  → Enqueue their children (level N+1)
  → By the time we finish level N, all level N+1 nodes are queued
  → Perfect level-by-level processing!
```

### Step-by-Step BFS Trace

```
Tree:
              [1]
            /     \
          [2]     [3]
         /   \   /   \
       [4]  [5] [6]  [7]
       /
     [8]

Initial: Queue = [1]

STEP 1: Dequeue 1, PRINT 1 ✓
        Enqueue left(2), right(3)
        Queue = [2, 3]

STEP 2: Dequeue 2, PRINT 2 ✓
        Enqueue left(4), right(5)
        Queue = [3, 4, 5]

STEP 3: Dequeue 3, PRINT 3 ✓
        Enqueue left(6), right(7)
        Queue = [4, 5, 6, 7]

STEP 4: Dequeue 4, PRINT 4 ✓
        Enqueue left(8), right(NULL)
        Queue = [5, 6, 7, 8]

STEP 5: Dequeue 5, PRINT 5 ✓ (no children)
        Queue = [6, 7, 8]

STEP 6: Dequeue 6, PRINT 6 ✓ (no children)
        Queue = [7, 8]

STEP 7: Dequeue 7, PRINT 7 ✓ (no children)
        Queue = [8]

STEP 8: Dequeue 8, PRINT 8 ✓ (no children)
        Queue = []  → DONE

OUTPUT: 1, 2, 3, 4, 5, 6, 7, 8
        ─────────────────────────
Level:   0  1  1  2  2  2  2  3
```

### Level-by-Level BFS (Grouped Output)

A common interview variant: return a **list of lists**, where each inner list is one level.

**Trick:** Before processing each level, snapshot the current queue size. That size = exactly how many nodes are at this level.

```
Level 0: [1]
Level 1: [2, 3]
Level 2: [4, 5, 6, 7]
Level 3: [8]
```

### BFS Flowchart

```
START
  |
  ▼
Enqueue root
  |
  ▼
Queue empty? ──YES──► END
  |
  NO
  |
  ▼
Dequeue front node
  |
  ▼
Visit / Process node
  |
  ▼
Has left child? ──YES──► Enqueue left child
  |
  ▼
Has right child? ──YES──► Enqueue right child
  |
  └───────────────────────► (back to: Queue empty?)
```

#### C Implementation — BFS / Level Order

```c
#include <stdio.h>
#include <stdlib.h>

typedef struct TreeNode {
    int val;
    struct TreeNode *left;
    struct TreeNode *right;
} TreeNode;

// Simple queue using array (for clarity)
// In production: use a proper circular queue
#define MAX_QUEUE 1000

TreeNode* queue[MAX_QUEUE];
int front_idx = 0, back_idx = 0;

void enqueue(TreeNode *node) { queue[back_idx++] = node; }
TreeNode* dequeue()          { return queue[front_idx++]; }
int is_empty()               { return front_idx == back_idx; }

// BASIC level order
void level_order(TreeNode *root) {
    if (!root) return;

    front_idx = back_idx = 0;  // reset queue
    enqueue(root);

    while (!is_empty()) {
        TreeNode *node = dequeue();
        printf("%d ", node->val);

        if (node->left)  enqueue(node->left);
        if (node->right) enqueue(node->right);
    }
    printf("\n");
}

// GROUPED level order — returns level-by-level (prints grouped)
void level_order_grouped(TreeNode *root) {
    if (!root) return;

    front_idx = back_idx = 0;
    enqueue(root);

    while (!is_empty()) {
        // Snapshot: how many nodes are at this level?
        int level_size = back_idx - front_idx;

        printf("[ ");
        for (int i = 0; i < level_size; i++) {
            TreeNode *node = dequeue();
            printf("%d ", node->val);
            if (node->left)  enqueue(node->left);
            if (node->right) enqueue(node->right);
        }
        printf("]\n");
    }
}
```

#### Go Implementation — BFS / Level Order

```go
package main

import "fmt"

type TreeNode struct {
    Val   int
    Left  *TreeNode
    Right *TreeNode
}

// Basic level order
func levelOrder(root *TreeNode) []int {
    if root == nil {
        return nil
    }
    result := []int{}
    queue := []*TreeNode{root}  // slice as queue

    for len(queue) > 0 {
        node := queue[0]
        queue = queue[1:]         // dequeue (pop from front)

        result = append(result, node.Val)

        if node.Left != nil {
            queue = append(queue, node.Left)
        }
        if node.Right != nil {
            queue = append(queue, node.Right)
        }
    }
    return result
}

// Grouped level order — returns [][]int
func levelOrderGrouped(root *TreeNode) [][]int {
    if root == nil {
        return nil
    }
    result := [][]int{}
    queue := []*TreeNode{root}

    for len(queue) > 0 {
        levelSize := len(queue)   // snapshot current level size
        level := []int{}

        for i := 0; i < levelSize; i++ {
            node := queue[0]
            queue = queue[1:]

            level = append(level, node.Val)
            if node.Left != nil {
                queue = append(queue, node.Left)
            }
            if node.Right != nil {
                queue = append(queue, node.Right)
            }
        }
        result = append(result, level)
    }
    return result
}

func main() {
    root := &TreeNode{Val: 1,
        Left:  &TreeNode{Val: 2, Left: &TreeNode{Val: 4,
            Left: &TreeNode{Val: 8}}, Right: &TreeNode{Val: 5}},
        Right: &TreeNode{Val: 3, Left: &TreeNode{Val: 6}, Right: &TreeNode{Val: 7}},
    }

    fmt.Println("Level Order:", levelOrder(root))
    fmt.Println("Grouped:", levelOrderGrouped(root))
}
```

#### Rust Implementation — BFS / Level Order

```rust
use std::collections::VecDeque;

// VecDeque = Double-ended queue — O(1) push/pop from both ends
// Perfect for BFS queue

fn level_order(root: &Option<Box<TreeNode>>) -> Vec<i32> {
    let mut result = Vec::new();
    let mut queue: VecDeque<&TreeNode> = VecDeque::new();

    if let Some(node) = root {
        queue.push_back(node);
    }

    while let Some(node) = queue.pop_front() {  // dequeue from front
        result.push(node.val);

        if let Some(left) = &node.left {
            queue.push_back(left);
        }
        if let Some(right) = &node.right {
            queue.push_back(right);
        }
    }
    result
}

// Grouped level order
fn level_order_grouped(root: &Option<Box<TreeNode>>) -> Vec<Vec<i32>> {
    let mut result = Vec::new();
    let mut queue: VecDeque<&TreeNode> = VecDeque::new();

    if let Some(node) = root {
        queue.push_back(node.as_ref());
    }

    while !queue.is_empty() {
        let level_size = queue.len();  // snapshot
        let mut level = Vec::new();

        for _ in 0..level_size {
            if let Some(node) = queue.pop_front() {
                level.push(node.val);
                if let Some(left) = &node.left {
                    queue.push_back(left);
                }
                if let Some(right) = &node.right {
                    queue.push_back(right);
                }
            }
        }
        result.push(level);
    }
    result
}
```

---

## 8. Advanced Traversals

### 8.1 Reverse Level Order

Visit nodes level by level, but output from **bottom to top** (last level first).

**Trick:** Do normal BFS but push results to a **stack** (or just reverse the result array at the end).

```
Normal Level Order:  [1], [2,3], [4,5,6,7], [8]
Reverse Level Order: [8], [4,5,6,7], [2,3], [1]
```

**C:**
```c
// Simple approach: run BFS, store result, then reverse print
void reverse_level_order(TreeNode *root) {
    if (!root) return;

    int vals[1000], count = 0;
    TreeNode *q[1000];
    int f = 0, b = 0;

    q[b++] = root;
    while (f != b) {
        TreeNode *node = q[f++];
        vals[count++] = node->val;
        // NOTE: enqueue RIGHT first, then LEFT
        // So when reversed, left comes before right
        if (node->right) q[b++] = node->right;
        if (node->left)  q[b++] = node->left;
    }
    // Print in reverse
    for (int i = count - 1; i >= 0; i--)
        printf("%d ", vals[i]);
    printf("\n");
}
```

**Go:**
```go
func reverseLevelOrder(root *TreeNode) [][]int {
    grouped := levelOrderGrouped(root)
    // Reverse the slice of slices
    for i, j := 0, len(grouped)-1; i < j; i, j = i+1, j-1 {
        grouped[i], grouped[j] = grouped[j], grouped[i]
    }
    return grouped
}
```

**Rust:**
```rust
fn reverse_level_order(root: &Option<Box<TreeNode>>) -> Vec<Vec<i32>> {
    let mut result = level_order_grouped(root);
    result.reverse();
    result
}
```

---

### 8.2 Zigzag / Spiral Traversal

Visit level by level, but alternate direction: left-to-right on even levels, right-to-left on odd levels.

```
Tree:
              [1]            Level 0 → Left to Right:  [1]
            /     \
          [2]     [3]        Level 1 → Right to Left:  [3, 2]
         /   \   /   \
       [4]  [5] [6]  [7]    Level 2 → Left to Right:  [4, 5, 6, 7]
       /
     [8]                    Level 3 → Right to Left:  [8]

Zigzag output: [1], [3,2], [4,5,6,7], [8]
```

**Algorithm:** Run BFS with level grouping. For odd-indexed levels, reverse the collected level array.

**C:**
```c
// Uses same grouped BFS structure; reverse every odd level
// (Uses same queue helpers from above)
void zigzag(TreeNode *root) {
    if (!root) return;

    front_idx = back_idx = 0;
    enqueue(root);
    int level = 0;

    while (!is_empty()) {
        int sz = back_idx - front_idx;
        int vals[100], cnt = 0;

        for (int i = 0; i < sz; i++) {
            TreeNode *node = dequeue();
            vals[cnt++] = node->val;
            if (node->left)  enqueue(node->left);
            if (node->right) enqueue(node->right);
        }

        if (level % 2 == 1) {
            // Reverse for odd levels (right-to-left)
            for (int i = cnt-1; i >= 0; i--) printf("%d ", vals[i]);
        } else {
            for (int i = 0; i < cnt; i++) printf("%d ", vals[i]);
        }
        printf("\n");
        level++;
    }
}
```

**Go:**
```go
func zigzag(root *TreeNode) [][]int {
    if root == nil {
        return nil
    }
    result := [][]int{}
    queue := []*TreeNode{root}
    leftToRight := true   // toggle direction

    for len(queue) > 0 {
        sz := len(queue)
        level := make([]int, sz)

        for i := 0; i < sz; i++ {
            node := queue[0]
            queue = queue[1:]
            // Place at correct position based on direction
            if leftToRight {
                level[i] = node.Val
            } else {
                level[sz-1-i] = node.Val  // fill from end
            }
            if node.Left != nil  { queue = append(queue, node.Left) }
            if node.Right != nil { queue = append(queue, node.Right) }
        }
        result = append(result, level)
        leftToRight = !leftToRight   // flip direction
    }
    return result
}
```

**Rust:**
```rust
fn zigzag(root: &Option<Box<TreeNode>>) -> Vec<Vec<i32>> {
    let mut result = Vec::new();
    let mut queue: VecDeque<&TreeNode> = VecDeque::new();
    let mut left_to_right = true;

    if let Some(node) = root {
        queue.push_back(node.as_ref());
    }

    while !queue.is_empty() {
        let sz = queue.len();
        let mut level = vec![0i32; sz];  // pre-allocate with size

        for i in 0..sz {
            if let Some(node) = queue.pop_front() {
                let idx = if left_to_right { i } else { sz - 1 - i };
                level[idx] = node.val;
                if let Some(l) = &node.left  { queue.push_back(l); }
                if let Some(r) = &node.right { queue.push_back(r); }
            }
        }
        result.push(level);
        left_to_right = !left_to_right;
    }
    result
}
```

---

### 8.3 Boundary Traversal

Visit all boundary (edge) nodes of the tree: left boundary + all leaves + right boundary (in order).

```
Tree:
              [1]        ← root (always included)
            /     \
          [2]     [3]    ← left boundary includes 2
         /   \   /   \
       [4]  [5] [6]  [7] ← right boundary includes 7
       /
     [8]                  ← leaf

Boundary = Left boundary (top→bottom, excluding leaves): 1, 2, 4
         + All leaves (left→right):                          8, 5, 6
         + Right boundary (bottom→top, excluding leaves):       7, 3
                                         (note: 3 and 7 order reversed)

OUTPUT: 1 → 2 → 4 → 8 → 5 → 6 → 7 → 3
```

**Three separate passes:**
1. **Left boundary:** Go left (prefer left child, else right). Stop at leaves.
2. **Leaves:** Standard inorder/DFS to collect all leaves.
3. **Right boundary:** Go right (prefer right child, else left). Stop at leaves. Then **reverse**.

**Go:**
```go
func isLeaf(node *TreeNode) bool {
    return node.Left == nil && node.Right == nil
}

// Collect left boundary (excluding leaf)
func leftBoundary(root *TreeNode, result *[]int) {
    curr := root.Left
    for curr != nil {
        if !isLeaf(curr) {
            *result = append(*result, curr.Val)
        }
        if curr.Left != nil {
            curr = curr.Left
        } else {
            curr = curr.Right
        }
    }
}

// Collect all leaves
func collectLeaves(root *TreeNode, result *[]int) {
    if root == nil { return }
    if isLeaf(root) {
        *result = append(*result, root.Val)
        return
    }
    collectLeaves(root.Left, result)
    collectLeaves(root.Right, result)
}

// Collect right boundary (excluding leaf) then reverse
func rightBoundary(root *TreeNode, result *[]int) {
    curr := root.Right
    temp := []int{}
    for curr != nil {
        if !isLeaf(curr) {
            temp = append(temp, curr.Val)
        }
        if curr.Right != nil {
            curr = curr.Right
        } else {
            curr = curr.Left
        }
    }
    // Reverse temp and append
    for i := len(temp) - 1; i >= 0; i-- {
        *result = append(*result, temp[i])
    }
}

func boundaryTraversal(root *TreeNode) []int {
    if root == nil { return nil }
    result := []int{root.Val}
    leftBoundary(root, &result)
    collectLeaves(root, &result)
    rightBoundary(root, &result)
    return result
}
```

---

### 8.4 Vertical Order Traversal

Group nodes by their **horizontal distance (HD)** from root.

**Concept — Horizontal Distance:**
- Root has HD = 0
- Going LEFT decreases HD by 1 (HD - 1)
- Going RIGHT increases HD by 1 (HD + 1)

```
Tree with HD values:
              [1]     HD=0
            /     \
          [2]     [3]  HD=-1     HD=1
         /   \   /   \
       [4]  [5] [6]  [7]  HD=-2  HD=0  HD=0  HD=2
       /
     [8]   HD=-3

Vertical Groups:
HD=-3: [8]
HD=-2: [4]
HD=-1: [2]
HD= 0: [1, 5, 6]  ← all nodes at center column
HD= 1: [3]
HD= 2: [7]
```

**Algorithm:** DFS/BFS while tracking HD. Use a map from HD → list of node values.

**Go:**
```go
import "sort"

func verticalOrder(root *TreeNode) [][]int {
    if root == nil { return nil }

    hdMap := map[int][]int{}  // horizontal distance → node values
    minHD, maxHD := 0, 0

    // DFS with (node, hd) pairs
    var dfs func(node *TreeNode, hd int)
    dfs = func(node *TreeNode, hd int) {
        if node == nil { return }
        hdMap[hd] = append(hdMap[hd], node.Val)
        if hd < minHD { minHD = hd }
        if hd > maxHD { maxHD = hd }
        dfs(node.Left, hd-1)
        dfs(node.Right, hd+1)
    }
    dfs(root, 0)

    result := [][]int{}
    for hd := minHD; hd <= maxHD; hd++ {
        result = append(result, hdMap[hd])
    }
    return result
}
```

**Rust:**
```rust
use std::collections::HashMap;

fn vertical_order(root: &Option<Box<TreeNode>>) -> Vec<Vec<i32>> {
    let mut hd_map: HashMap<i32, Vec<i32>> = HashMap::new();
    let mut min_hd = 0i32;
    let mut max_hd = 0i32;

    fn dfs(node: &Option<Box<TreeNode>>, hd: i32,
           map: &mut HashMap<i32, Vec<i32>>,
           min_hd: &mut i32, max_hd: &mut i32) {
        if let Some(n) = node {
            map.entry(hd).or_default().push(n.val);
            if hd < *min_hd { *min_hd = hd; }
            if hd > *max_hd { *max_hd = hd; }
            dfs(&n.left, hd - 1, map, min_hd, max_hd);
            dfs(&n.right, hd + 1, map, min_hd, max_hd);
        }
    }

    dfs(root, 0, &mut hd_map, &mut min_hd, &mut max_hd);

    (min_hd..=max_hd)
        .map(|hd| hd_map.get(&hd).cloned().unwrap_or_default())
        .collect()
}
```

---

### 8.5 Diagonal Traversal

Nodes on the same **diagonal** (same `row - col` value) are grouped together. Going right keeps you on the same diagonal; going left moves to the next diagonal.

```
Tree with diagonal values (0=topmost):
              [1]     d=0
            /     \
          [2]     [3]  d=1   d=0
         /   \   /   \
       [4]  [5] [6]  [7]  d=2  d=1  d=1  d=0
       /
     [8]   d=3

Diagonal groups:
d=0: [1, 3, 7]
d=1: [2, 5, 6]
d=2: [4]
d=3: [8]
```

**Go:**
```go
func diagonalTraversal(root *TreeNode) [][]int {
    diagMap := map[int][]int{}
    maxDiag := 0

    var dfs func(node *TreeNode, d int)
    dfs = func(node *TreeNode, d int) {
        if node == nil { return }
        diagMap[d] = append(diagMap[d], node.Val)
        if d > maxDiag { maxDiag = d }
        dfs(node.Left, d+1)   // left child → next diagonal
        dfs(node.Right, d)    // right child → SAME diagonal
    }
    dfs(root, 0)

    result := [][]int{}
    for d := 0; d <= maxDiag; d++ {
        result = append(result, diagMap[d])
    }
    return result
}
```

---

## 9. Morris Traversal — O(1) Space Magic

All traversals above use O(H) space for the call stack (or O(N) for BFS queue). **Morris Traversal** achieves O(1) extra space using a clever trick: **temporarily modifying the tree itself** using "threaded binary tree" pointers.

### Core Idea — Threading

**Concept — Predecessor in Inorder:**
For a node `curr`, its **inorder predecessor** is the **rightmost node of its left subtree** (the last node visited before `curr` in inorder).

The trick:
1. If `curr` has no left child → visit it, go right.
2. If `curr` has a left child → find its inorder predecessor `pred`.
   - If `pred.right == NULL` → set `pred.right = curr` (create a "thread" back to curr), go left.
   - If `pred.right == curr` → we've been here before (thread exists). Remove thread, visit `curr`, go right.

```
Morris Inorder — Thread Creation and Removal:

Step 1: curr=1, find predecessor of 1 in left subtree
        Leftmost chain: 1→2→4→8
        Predecessor of 1 = 5 (rightmost of left subtree rooted at 2)
        pred(5).right = NULL → CREATE THREAD: 5.right = 1
        Move curr = curr.left = 2

Step 2: curr=2, predecessor = 4 (rightmost of 2's left subtree)
        pred(4).right = NULL → CREATE THREAD: 4.right = 2
        Move curr = 2.left = 4

Step 3: curr=4, predecessor = 8
        pred(8).right = NULL → CREATE THREAD: 8.right = 4
        Move curr = 4.left = 8

Step 4: curr=8, no left child → VISIT 8, move curr = 8.right = 4 (thread!)

Step 5: curr=4, predecessor = 8
        pred(8).right = 4 (thread exists!) → REMOVE THREAD: 8.right = NULL
        VISIT 4, move curr = 4.right = NULL → move to 2

... and so on
```

**C — Morris Inorder:**
```c
// Morris Inorder: O(N) time, O(1) space (no stack/recursion)
void morris_inorder(TreeNode *root) {
    TreeNode *curr = root;

    while (curr != NULL) {
        if (curr->left == NULL) {
            // No left child: visit node, go right
            printf("%d ", curr->val);
            curr = curr->right;
        } else {
            // Find inorder predecessor
            TreeNode *pred = curr->left;
            while (pred->right != NULL && pred->right != curr) {
                pred = pred->right;
            }

            if (pred->right == NULL) {
                // Thread does NOT exist: create it, go left
                pred->right = curr;
                curr = curr->left;
            } else {
                // Thread EXISTS: remove it, visit node, go right
                pred->right = NULL;
                printf("%d ", curr->val);
                curr = curr->right;
            }
        }
    }
    printf("\n");
}
```

**Go — Morris Inorder:**
```go
func morrisInorder(root *TreeNode) []int {
    result := []int{}
    curr := root

    for curr != nil {
        if curr.Left == nil {
            result = append(result, curr.Val)
            curr = curr.Right
        } else {
            // Find predecessor
            pred := curr.Left
            for pred.Right != nil && pred.Right != curr {
                pred = pred.Right
            }

            if pred.Right == nil {
                pred.Right = curr   // create thread
                curr = curr.Left
            } else {
                pred.Right = nil    // remove thread
                result = append(result, curr.Val)
                curr = curr.Right
            }
        }
    }
    return result
}
```

**Rust — Morris Inorder (unsafe raw pointers for mutation):**
```rust
// Rust's ownership system makes in-place tree modification complex.
// Morris traversal requires temporarily creating cycles (back-pointers),
// which violates Rust's borrow checker. The idiomatic Rust solution
// uses raw pointers with unsafe, or uses RefCell<T> for interior mutability.
// Below is the raw pointer approach for educational completeness:

fn morris_inorder_raw(root: *mut TreeNode) -> Vec<i32> {
    let mut result = Vec::new();
    let mut curr = root;

    unsafe {
        while !curr.is_null() {
            if (*curr).left.is_none() {
                result.push((*curr).val);
                curr = match &(*curr).right {
                    Some(r) => r.as_ref() as *const _ as *mut TreeNode,
                    None => std::ptr::null_mut(),
                };
            } else {
                // Finding predecessor requires raw traversal
                // This is simplified pseudocode for the concept
                // In practice, use RefCell or restructure ownership
                result.push((*curr).val);
                break; // placeholder
            }
        }
    }
    result
}
// NOTE: For production Rust code with Morris traversal, prefer
// using an explicit stack (iterative DFS) which is idiomatic and safe.
// Morris traversal's O(1) space benefit is less critical in Rust
// where stack-based approaches compile to very efficient code.
```

> **Expert Insight:** Morris traversal trades **time constants** (two passes per node to create/destroy threads) for **space**. Total time is still O(N) but with a higher constant. Use it only when space is critically constrained (embedded systems, very deep trees).

---

## 10. Iterative DFS — Explicit Stack

The recursive DFS implicitly uses the **call stack**. We can make this explicit with our own stack. This is crucial for:
- Very deep trees (avoid stack overflow)
- Languages/platforms with limited stack size
- When you need fine-grained control over traversal

### Why Stack works for DFS

```
Stack = LIFO (Last In, First Out)
When we push right then left, left is popped first → left explored first
This mirrors recursive DFS exactly.
```

### Iterative Inorder

```
INSIGHT: Inorder (L→N→R) iteratively is trickier than pre/postorder.
Strategy: Push nodes going left until NULL, then process, then go right.

Trace on: [1]→[2]→[4]→[8] (left chain)
Push all left nodes to stack.
Pop 8 (no right), pop 4 (go right → NULL), pop 2 (go right → 5), etc.
```

**C — Iterative Inorder:**
```c
#define STACK_MAX 1000
typedef struct {
    TreeNode *data[STACK_MAX];
    int top;
} Stack;

void push(Stack *s, TreeNode *n) { s->data[s->top++] = n; }
TreeNode* pop(Stack *s) { return s->data[--s->top]; }
int stack_empty(Stack *s) { return s->top == 0; }

void iterative_inorder(TreeNode *root) {
    Stack s = {.top = 0};
    TreeNode *curr = root;

    while (curr != NULL || !stack_empty(&s)) {
        // Go as far left as possible
        while (curr != NULL) {
            push(&s, curr);
            curr = curr->left;
        }
        // Process node
        curr = pop(&s);
        printf("%d ", curr->val);
        // Move to right subtree
        curr = curr->right;
    }
    printf("\n");
}
```

**Go — Iterative Inorder:**
```go
func iterativeInorder(root *TreeNode) []int {
    result := []int{}
    stack := []*TreeNode{}
    curr := root

    for curr != nil || len(stack) > 0 {
        // Go left as far as possible
        for curr != nil {
            stack = append(stack, curr)
            curr = curr.Left
        }
        // Process
        curr = stack[len(stack)-1]
        stack = stack[:len(stack)-1]   // pop
        result = append(result, curr.Val)
        // Move right
        curr = curr.Right
    }
    return result
}
```

**Rust — Iterative Inorder:**
```rust
fn iterative_inorder(root: &Option<Box<TreeNode>>) -> Vec<i32> {
    let mut result = Vec::new();
    let mut stack: Vec<&TreeNode> = Vec::new();
    let mut curr: Option<&TreeNode> = root.as_deref();

    loop {
        // Go left as far as possible
        while let Some(node) = curr {
            stack.push(node);
            curr = node.left.as_deref();
        }
        // Nothing left: done
        match stack.pop() {
            None => break,
            Some(node) => {
                result.push(node.val);
                curr = node.right.as_deref();  // move right
            }
        }
    }
    result
}
```

### Iterative Preorder

Preorder is simpler iteratively. Push root, then right child before left (so left is processed first).

**Go:**
```go
func iterativePreorder(root *TreeNode) []int {
    if root == nil { return nil }
    result := []int{}
    stack := []*TreeNode{root}

    for len(stack) > 0 {
        node := stack[len(stack)-1]
        stack = stack[:len(stack)-1]   // pop

        result = append(result, node.Val)  // VISIT

        // Push RIGHT first (so LEFT is popped/visited first)
        if node.Right != nil { stack = append(stack, node.Right) }
        if node.Left  != nil { stack = append(stack, node.Left)  }
    }
    return result
}
```

### Iterative Postorder (Two-Stack Trick)

**Insight:** Postorder (L→R→N) is the reverse of a modified preorder (N→R→L).
- Run "reverse preorder" (push LEFT before RIGHT) → get N,R,L order
- Reverse the result → get L,R,N = Postorder ✓

**Go:**
```go
func iterativePostorder(root *TreeNode) []int {
    if root == nil { return nil }
    result := []int{}
    stack := []*TreeNode{root}

    for len(stack) > 0 {
        node := stack[len(stack)-1]
        stack = stack[:len(stack)-1]

        result = append(result, node.Val)

        // Opposite of preorder: push LEFT first
        if node.Left  != nil { stack = append(stack, node.Left)  }
        if node.Right != nil { stack = append(stack, node.Right) }
    }
    // Reverse gives postorder
    for i, j := 0, len(result)-1; i < j; i, j = i+1, j-1 {
        result[i], result[j] = result[j], result[i]
    }
    return result
}
```

**Rust:**
```rust
fn iterative_postorder(root: &Option<Box<TreeNode>>) -> Vec<i32> {
    let mut result = Vec::new();
    let mut stack = Vec::new();

    if let Some(node) = root {
        stack.push(node.as_ref());
    }

    while let Some(node) = stack.pop() {
        result.push(node.val);
        if let Some(l) = &node.left  { stack.push(l); }
        if let Some(r) = &node.right { stack.push(r); }
    }
    result.reverse();
    result
}
```

---

## 11. N-ary Tree Traversal

An **N-ary tree** is a tree where each node can have **any number of children** (not just 2). Used in file systems, DOM trees, organization charts.

```
           [1]
         / | \
       [2][3][4]
       /|   \
     [5][6]  [7]
```

### Node Structure

**C:**
```c
#define MAX_CHILDREN 10

typedef struct NaryNode {
    int val;
    struct NaryNode *children[MAX_CHILDREN];
    int num_children;
} NaryNode;
```

**Go:**
```go
type NaryNode struct {
    Val      int
    Children []*NaryNode
}
```

**Rust:**
```rust
struct NaryNode {
    val: i32,
    children: Vec<Box<NaryNode>>,
}
```

### Preorder N-ary

```go
func naryPreorder(root *NaryNode, result *[]int) {
    if root == nil { return }
    *result = append(*result, root.Val)  // VISIT first
    for _, child := range root.Children {
        naryPreorder(child, result)       // then each child
    }
}
```

### Postorder N-ary

```go
func naryPostorder(root *NaryNode, result *[]int) {
    if root == nil { return }
    for _, child := range root.Children {
        naryPostorder(child, result)      // children first
    }
    *result = append(*result, root.Val)  // VISIT last
}
```

### Level Order N-ary

```go
func naryLevelOrder(root *NaryNode) [][]int {
    if root == nil { return nil }
    result := [][]int{}
    queue := []*NaryNode{root}

    for len(queue) > 0 {
        sz := len(queue)
        level := []int{}
        for i := 0; i < sz; i++ {
            node := queue[0]; queue = queue[1:]
            level = append(level, node.Val)
            queue = append(queue, node.Children...)  // append all children
        }
        result = append(result, level)
    }
    return result
}
```

---

## 12. Complexity Master Table

```
+----------------------+-------------+-------------+------------------+
| Traversal            | Time        | Space       | Notes            |
+----------------------+-------------+-------------+------------------+
| Inorder (recursive)  | O(N)        | O(H)        | H=height         |
| Preorder (recursive) | O(N)        | O(H)        | Best case O(logN)|
| Postorder (recursve) | O(N)        | O(H)        | Worst: O(N)      |
| Inorder (iterative)  | O(N)        | O(H)        | Same as recursive|
| Preorder (iteratve)  | O(N)        | O(H)        | Explicit stack   |
| Postorder (iteratve) | O(N)        | O(H)        | 2-stack trick    |
| Morris Inorder       | O(N)        | O(1) !!     | Modifies tree    |
| Level Order (BFS)    | O(N)        | O(W)        | W=max width      |
| Zigzag               | O(N)        | O(W)        | BFS variant      |
| Reverse Level Order  | O(N)        | O(W)        | BFS + reverse    |
| Vertical Order       | O(N log N)  | O(N)        | Sorting by HD    |
| Diagonal Traversal   | O(N)        | O(N)        | Map by diag      |
| Boundary Traversal   | O(N)        | O(H)        | 3 separate DFS   |
| N-ary Level Order    | O(N)        | O(W)        | W=max width      |
+----------------------+-------------+-------------+------------------+

Space: H = tree height
  - Balanced tree: H = O(log N) 
  - Skewed tree:   H = O(N) (worst case)
  - Perfect tree:  H = O(log N)

Space: W = maximum width (number of nodes at widest level)
  - Perfect tree: W = O(N/2) = O(N) at bottom level
  - Skewed tree:  W = O(1) at each level
```

---

## 13. Expert Mental Models

### 13.1 The "3 Questions" Framework

Before writing any traversal code, ask:

```
Q1: Do I need parent info BEFORE processing children?
    → YES → PREORDER

Q2: Do I need children info BEFORE processing parent?
    → YES → POSTORDER

Q3: Do I need sorted order (BST) or process in left-root-right order?
    → YES → INORDER

Q4: Do I need layer-by-layer, shortest paths, or min-depth?
    → YES → BFS / LEVEL ORDER
```

### 13.2 Stack vs Queue Mental Model

```
RECURSIVE DFS       ITERATIVE DFS         BFS
(implicit stack)    (explicit stack)      (explicit queue)
     ↓                    ↓                    ↓
Goes DEEP           Goes DEEP            Goes WIDE
Backtracks on       Backtracks on        Never backtracks
return              pop                  within level
```

### 13.3 Traversal-to-Problem Mapping

```
PROBLEM                              → TRAVERSAL
─────────────────────────────────────────────────
BST sorted output                    → Inorder
Clone/serialize a tree               → Preorder
Delete a tree / compute height       → Postorder
Level-by-level output                → BFS
Minimum depth of tree                → BFS (finds it faster)
Check if tree is symmetric           → BFS or Inorder
Right side view of tree              → BFS (last of each level)
Left side view of tree               → BFS (first of each level)
Lowest Common Ancestor               → Postorder
Path from root to node               → Preorder + backtrack
Sum of all paths                     → Postorder
Validate BST                         → Inorder (check sorted)
Serialize / Deserialize              → Preorder + BFS
```

### 13.4 The Recursion Pattern Template

Every recursive tree solution follows this skeleton — internalize it:

```
function solve(node):
    // BASE CASE
    if node is null:
        return base_value  // 0, null, true, etc.

    // RECURSE on subtrees
    left_result  = solve(node.left)
    right_result = solve(node.right)

    // COMBINE results + current node
    return combine(left_result, right_result, node.val)
```

### 13.5 Cognitive Chunking for Traversals

> **Chunking** is a cognitive principle where you group individual items into a single meaningful unit, reducing cognitive load.

Instead of memorizing Pre/In/Post as separate algorithms, chunk them as:
- **One algorithm:** `DFS(node, L, R)` where you choose *when to process node*.
- The only variable is the **position of the `print` statement**.

```c
void dfs(TreeNode *node) {
    if (!node) return;
    // printf here → PREORDER
    dfs(node->left);
    // printf here → INORDER
    dfs(node->right);
    // printf here → POSTORDER
}
```

This single mental model gives you all three traversals. That's chunking in action.

---

## Summary — The Complete Traversal Map

```
                    TREE TRAVERSAL COMPLETE MAP
                    ════════════════════════════

    ┌──────────────────────────────────────────────────────────────┐
    │                     DFS (Stack / Recursion)                  │
    │                                                              │
    │  PREORDER (N→L→R)    INORDER (L→N→R)    POSTORDER (L→R→N)  │
    │  • Clone trees        • BST sorted        • Delete trees     │
    │  • Serialize          • Validate BST      • Eval expressions │
    │  • Prefix expr        • Range queries     • Height/size      │
    │                                                              │
    │  Morris Traversal: O(1) space inorder (threaded trees)      │
    │  Iterative DFS:    Explicit stack, avoids stack overflow     │
    └──────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────┐
    │                     BFS (Queue)                              │
    │                                                              │
    │  LEVEL ORDER         ZIGZAG           REVERSE LEVEL ORDER   │
    │  • Shortest path     • Spiral view    • Bottom-up output    │
    │  • Min depth         • Alternating    • Reverse tree levels │
    │  • Right/Left view                                          │
    └──────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────┐
    │                  GEOMETRIC TRAVERSALS (DFS + Map)            │
    │                                                              │
    │  VERTICAL ORDER      DIAGONAL         BOUNDARY              │
    │  • Column view       • Diagonal view  • Perimeter nodes     │
    │  • HD-based groups   • slope-based    • Left+Leaves+Right   │
    └──────────────────────────────────────────────────────────────┘

    Time:  All = O(N)  (visit each node once)
    Space: DFS = O(H)  |  BFS = O(W)  |  Morris = O(1)
           H = height, W = width, N = total nodes
```

---

*"An expert is not someone who has all the answers — they are someone who has internalized the patterns so deeply that the solution emerges before the problem is fully stated."*

*Master these traversals not by memorizing code, but by understanding the **shape of the algorithm** — when to go deep, when to go wide, when to go left, and when to look back.*

---
**End of Guide — Tree Traversal: Complete Reference**

Now let me build this comprehensive guide. This will be a large, rich `.md` file.Here's your complete tree traversal guide. Here's what's covered and why each section matters:

**Structure of the Guide:**

The guide builds from absolute zero — node anatomy, terminology (depth vs height, successor vs predecessor), and tree types — before touching a single traversal. This is intentional: every traversal bug in competitive programming traces back to a misunderstood concept.

**What's inside:**

1. **Core DFS trilogy (Pre/In/Post)** — explained as a *single algorithm* with one moving line. This is the chunking insight: you don't learn 3 algorithms, you learn 1 with 3 positions for the print statement.

2. **BFS with the level-snapshot trick** — `levelSize := len(queue)` before the inner loop is the key pattern for all grouped-level problems. Internalize this once, it unlocks 20+ problems.

3. **Advanced traversals** (Zigzag, Vertical, Diagonal, Boundary) — each reduces to a known primitive (BFS + toggle, DFS + hashmap). The mental model: *new traversal = old traversal + one extra tracking variable.*

4. **Morris Traversal** — the O(1) space variant. Rust section honestly explains why idiomatic Rust resists in-place mutation, which is a deeper insight about ownership than any syntax example.

5. **Iterative DFS** — the `while (curr != null || stack not empty)` loop for inorder is a pattern that appears in BST iterator problems, which are common in top-tier interviews.

6. **Complexity table + problem-to-traversal mapping** — use this as your lookup when you see a new problem.

**Next depth to go:** When you're ready, the natural next step is applying these traversals to solve BST problems (validation, LCA, kth smallest), then expression trees, then serialization/deserialization — which combines preorder + BFS.

## Trace Analysis: Inserting 65 into BST

Assuming the tree structure:
```
        50
       /  \
      ...   70
           /
          60
```

Your comments are **correct**. :

---

### Step 1 ✅
```python
else:  # execute 65 > 50  ✓
    root.right = insert(root.right, val)  # passes node(70) → 70 will be reassigned ✓
return root
```

### Step 2 ✅
```python
# step 2: root.right (node 70) and val=65 passed here ✓
if val < root.val:  # execute 65 < 70 ✓
    root.left = insert(root.left, val)  # passes node(60) → 60 will be reassigned ✓
```

### Step 3 ✅
```python
# step 3: root.left (node 60) and val=65 passed here ✓
else:  # execute 65 > 60 ✓
    root.right = insert(root.right, val)  # passes None → TreeNode(65) assigned here ✓
return root  # returns node(60) ✓
```

### Step 4 ✅ 
```python
# step 4: root.right (None) and val=65 passed here ✓
if root is None:  # executes ✓
    return TreeNode(val)  # 65 node created ✓

```

---

### The Fix

`return root` at the bottom of Step 4 **is never executed** — the function exits early at `return TreeNode(val)`. The correct comment:

```python
return TreeNode(val)  # exits here, returns new node(65)
return root           # unreachable in this execution path
```

### Unwind Summary
```
Step 4: return TreeNode(65)
Step 3: node60.right = TreeNode(65), return node(60)
Step 2: node70.left  = node(60),     return node(70)
Step 1: node50.right = node(70),     return node(50)
```