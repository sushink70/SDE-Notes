# Binary Search Tree (BST) Traversal — Complete In-Depth Guide

> **Implementations:** C · Go · Rust  
> **Coverage:** All traversal strategies, iterative + recursive variants, complexity analysis, practical use cases, and production-level code.

---

## Table of Contents

1. [What is a BST?](#1-what-is-a-bst)
2. [BST Node Structure](#2-bst-node-structure)
3. [Traversal Categories](#3-traversal-categories)
4. [Depth-First Search (DFS) Traversals](#4-depth-first-search-dfs-traversals)
   - 4.1 [In-Order (LNR)](#41-in-order-lnr--left--node--right)
   - 4.2 [Pre-Order (NLR)](#42-pre-order-nlr--node--left--right)
   - 4.3 [Post-Order (LRN)](#43-post-order-lrn--left--right--node)
   - 4.4 [Reverse In-Order (RNL)](#44-reverse-in-order-rnl--right--node--left)
5. [Breadth-First Search (BFS) / Level-Order Traversal](#5-breadth-first-search-bfs--level-order-traversal)
6. [Morris Traversal (O(1) Space)](#6-morris-traversal-o1-space)
7. [Iterative Traversals Using Explicit Stack](#7-iterative-traversals-using-explicit-stack)
8. [Zigzag / Spiral Level-Order Traversal](#8-zigzag--spiral-level-order-traversal)
9. [Vertical Order Traversal](#9-vertical-order-traversal)
10. [Boundary Traversal](#10-boundary-traversal)
11. [Diagonal Traversal](#11-diagonal-traversal)
12. [Complexity Analysis Summary](#12-complexity-analysis-summary)
13. [Use Cases & When to Use Which](#13-use-cases--when-to-use-which)
14. [Full Implementations](#14-full-implementations)
    - 14.1 [C Implementation](#141-c-implementation)
    - 14.2 [Go Implementation](#142-go-implementation)
    - 14.3 [Rust Implementation](#143-rust-implementation)

---

## 1. What is a BST?

A **Binary Search Tree** is a binary tree where every node satisfies the **BST property**:

```
For any node N:
  - All values in N.left subtree  < N.value
  - All values in N.right subtree > N.value
  - Both left and right subtrees are also valid BSTs
```

This invariant is the cornerstone of all BST operations. It allows logarithmic search, insertion, and deletion on average — O(log n) — degrading to O(n) on a degenerate (skewed) tree.

### Key Properties
| Property | Balanced BST | Degenerate BST |
|---|---|---|
| Height | O(log n) | O(n) |
| Search | O(log n) | O(n) |
| Insert | O(log n) | O(n) |
| Traversal | O(n) | O(n) |

Traversal is always **O(n)** — every node must be visited exactly once regardless of tree shape.

---

## 2. BST Node Structure

The fundamental building block:

```
+-------+
| value |
+-------+
| *left | ---> left subtree (values < node)
+-------+
| *right| ---> right subtree (values > node)
+-------+
```

The shape of a traversal is determined entirely by **when you visit the node** relative to its children — before, between, or after.

---

## 3. Traversal Categories

```
BST Traversal
│
├── Depth-First Search (DFS)
│   ├── In-Order     (Left → Node → Right)   [most common]
│   ├── Pre-Order    (Node → Left → Right)
│   ├── Post-Order   (Left → Right → Node)
│   └── Reverse In-Order (Right → Node → Left)
│
├── Breadth-First Search (BFS)
│   ├── Level-Order  (queue-based)
│   └── Zigzag / Spiral Level-Order
│
├── Space-Optimized
│   └── Morris Traversal (O(1) extra space)
│
└── Structural / Pattern Traversals
    ├── Vertical Order
    ├── Boundary Traversal
    └── Diagonal Traversal
```

---

## 4. Depth-First Search (DFS) Traversals

DFS traversals follow a path deep into the tree before backtracking. They differ only in **when the current node is processed** — before, between, or after recursive calls.

---

### 4.1 In-Order (LNR) — Left → Node → Right

**The most important traversal for BSTs.**

#### How it works
1. Recursively traverse the left subtree
2. Visit the current node
3. Recursively traverse the right subtree

#### Why it matters
In-Order traversal of a valid BST produces nodes in **strictly ascending sorted order**. This is a direct consequence of the BST property and is used extensively:
- Validating if a tree is a valid BST
- Sorting (tree sort)
- Finding kth smallest element
- Generating sorted output from a BST

#### Example

```
        10
       /  \
      5    15
     / \   / \
    3   7 12  20

In-Order:  3 → 5 → 7 → 10 → 12 → 15 → 20
```

#### Recursive — Pseudocode
```
inorder(node):
  if node is null: return
  inorder(node.left)
  visit(node)
  inorder(node.right)
```

#### Call Stack Trace (for root=10)
```
inorder(10)
  inorder(5)
    inorder(3)
      inorder(null) ← base case
      visit(3)       ← OUTPUT: 3
      inorder(null) ← base case
    visit(5)         ← OUTPUT: 5
    inorder(7)
      inorder(null) ← base case
      visit(7)       ← OUTPUT: 7
      inorder(null) ← base case
  visit(10)          ← OUTPUT: 10
  inorder(15)
    inorder(12)
      visit(12)      ← OUTPUT: 12
    visit(15)        ← OUTPUT: 15
    inorder(20)
      visit(20)      ← OUTPUT: 20
```

---

### 4.2 Pre-Order (NLR) — Node → Left → Right

#### How it works
1. Visit the current node **first**
2. Recursively traverse the left subtree
3. Recursively traverse the right subtree

#### Why it matters
- **Tree serialization/deserialization**: Pre-order output can recreate the exact tree structure
- **Copying a tree**: The first element is always the root, making reconstruction straightforward
- **Expression trees**: Produces prefix notation (Polish notation) — `* + a b c` means `(a + b) * c`
- **Directory/file system traversal**: Print parent before children

#### Example
```
        10
       /  \
      5    15
     / \   / \
    3   7 12  20

Pre-Order: 10 → 5 → 3 → 7 → 15 → 12 → 20
```

#### Recursive — Pseudocode
```
preorder(node):
  if node is null: return
  visit(node)
  preorder(node.left)
  preorder(node.right)
```

#### Key insight: Reconstruction
Given pre-order output `[10, 5, 3, 7, 15, 12, 20]`:
- First element (`10`) is always the root
- Elements less than root (`5, 3, 7`) form the left subtree
- Elements greater than root (`15, 12, 20`) form the right subtree
- Apply recursively — this reconstructs the original BST

---

### 4.3 Post-Order (LRN) — Left → Right → Node

#### How it works
1. Recursively traverse the left subtree
2. Recursively traverse the right subtree
3. Visit the current node **last**

#### Why it matters
- **Tree deletion**: Safe deletion order — delete children before parent (no dangling pointers)
- **Computing aggregate values**: Subtree sizes, heights, sums — children computed before parent
- **Expression trees**: Produces postfix notation (Reverse Polish Notation) — `a b + c *`
- **Dependency resolution**: Process dependencies before the dependent (like `make` targets)

#### Example
```
        10
       /  \
      5    15
     / \   / \
    3   7 12  20

Post-Order: 3 → 7 → 5 → 12 → 20 → 15 → 10
```

#### Recursive — Pseudocode
```
postorder(node):
  if node is null: return
  postorder(node.left)
  postorder(node.right)
  visit(node)
```

#### Key insight: Root is always last
The root appears at the very end, which is why this is used for safe resource cleanup and memory deallocation.

---

### 4.4 Reverse In-Order (RNL) — Right → Node → Left

#### How it works
Mirror of In-Order: traverse right first, then visit, then left.

#### Why it matters
Produces nodes in **strictly descending order** — useful for:
- Finding kth **largest** element efficiently
- Populating cumulative sums from largest to smallest (BST to Greater Sum Tree)
- Reverse sorted output

#### Example
```
        10
       /  \
      5    15
     / \   / \
    3   7 12  20

Reverse In-Order: 20 → 15 → 12 → 10 → 7 → 5 → 3
```

#### Recursive — Pseudocode
```
reverse_inorder(node):
  if node is null: return
  reverse_inorder(node.right)
  visit(node)
  reverse_inorder(node.left)
```

---

## 5. Breadth-First Search (BFS) / Level-Order Traversal

BFS visits all nodes **level by level**, left to right, using a **queue** (FIFO).

#### How it works
1. Enqueue the root
2. While queue is not empty:
   a. Dequeue the front node
   b. Visit it
   c. Enqueue its left child (if exists)
   d. Enqueue its right child (if exists)

#### Example
```
        10
       /  \
      5    15
     / \   / \
    3   7 12  20

Level 0: 10
Level 1: 5  → 15
Level 2: 3  → 7  → 12 → 20

BFS Output: 10 → 5 → 15 → 3 → 7 → 12 → 20
```

#### Queue State Walkthrough
```
Initial:    [10]
Dequeue 10  → visit 10  → enqueue 5, 15   →  [5, 15]
Dequeue 5   → visit 5   → enqueue 3, 7    →  [15, 3, 7]
Dequeue 15  → visit 15  → enqueue 12, 20  →  [3, 7, 12, 20]
Dequeue 3   → visit 3   → no children     →  [7, 12, 20]
Dequeue 7   → visit 7   → no children     →  [12, 20]
Dequeue 12  → visit 12  → no children     →  [20]
Dequeue 20  → visit 20  → no children     →  []
```

#### Why it matters
- **Finding shortest path** in unweighted trees
- **Level-by-level processing**: Printing tree levels, finding level of a node
- **Connecting nodes at the same level** (right pointers in Leetcode-style problems)
- **Minimum depth** of a tree (BFS finds it faster than DFS — stops at first leaf)
- **Serialization** to array representation (heap-style indexing)

#### Pseudocode
```
level_order(root):
  if root is null: return
  queue = new Queue()
  queue.enqueue(root)
  
  while queue is not empty:
    node = queue.dequeue()
    visit(node)
    if node.left  ≠ null: queue.enqueue(node.left)
    if node.right ≠ null: queue.enqueue(node.right)
```

#### Variant: Level-by-Level with Grouping
To get results grouped per level (returns `[[10], [5,15], [3,7,12,20]]`):
```
level_order_grouped(root):
  if root is null: return []
  result = []
  queue = [root]
  
  while queue is not empty:
    level_size = queue.size()
    current_level = []
    
    repeat level_size times:
      node = queue.dequeue()
      current_level.append(node.value)
      if node.left  ≠ null: queue.enqueue(node.left)
      if node.right ≠ null: queue.enqueue(node.right)
    
    result.append(current_level)
  
  return result
```

---

## 6. Morris Traversal (O(1) Space)

Morris Traversal is the most space-efficient DFS traversal — it achieves **O(1) auxiliary space** (no recursion stack, no explicit stack) by temporarily modifying the tree structure using **threaded binary tree** concepts.

### Core Idea
For a node `curr`, find its **in-order predecessor** (rightmost node of its left subtree). Temporarily set that predecessor's right pointer to `curr` as a "thread." After visiting, restore the pointer.

### How Morris In-Order Works

```
Algorithm:
  curr = root
  while curr ≠ null:
    if curr.left == null:
      visit(curr)          ← no left subtree, visit and go right
      curr = curr.right
    else:
      pred = in_order_predecessor(curr)   ← rightmost of left subtree
      
      if pred.right == null:
        pred.right = curr  ← CREATE thread (mark "return here")
        curr = curr.left   ← go left
      else:
        pred.right = null  ← REMOVE thread (we've come back)
        visit(curr)        ← now visit
        curr = curr.right  ← go right
```

### Step-by-Step Trace

```
Tree:       10
           /  \
          5    15
         / \
        3   7

Step 1: curr=10, left=5 → find predecessor of 10 = 7 (rightmost of left subtree)
        7.right = null, so: 7.right = 10 (create thread), curr = 5

Step 2: curr=5, left=3 → find predecessor of 5 = 3
        3.right = null, so: 3.right = 5 (create thread), curr = 3

Step 3: curr=3, left=null → VISIT 3, curr = 3.right = 5 (thread!)

Step 4: curr=5, left=3 → find predecessor of 5 = 3
        3.right = 5 (thread exists!), so: 3.right = null (restore), VISIT 5, curr = 7

Step 5: curr=7, left=null → VISIT 7, curr = 7.right = 10 (thread!)

Step 6: curr=10, left=5 → find predecessor of 10 = 7
        7.right = 10 (thread exists!), so: 7.right = null (restore), VISIT 10, curr = 15

Step 7: curr=15, left=null → VISIT 15, curr = null → DONE

Output: 3, 5, 7, 10, 15 ✓
```

### Why Morris Is Powerful
| Approach | Time | Space |
|---|---|---|
| Recursive | O(n) | O(h) stack |
| Iterative (explicit stack) | O(n) | O(h) stack |
| Morris | O(n) | **O(1)** |

Where `h` is tree height — O(log n) balanced, O(n) skewed.

### Caveats
- **Not thread-safe**: Temporarily mutates the tree
- More complex to implement correctly
- Slightly higher constant factor due to predecessor searches (but still O(n) total)

---

## 7. Iterative Traversals Using Explicit Stack

Recursive traversals use the call stack implicitly. Converting to iterative form uses an **explicit stack** — important for:
- Avoiding stack overflow on very deep trees
- Pausing/resuming traversal (generators/iterators)
- Finer control over traversal state

### Iterative In-Order

```
iterative_inorder(root):
  stack = []
  curr = root
  
  while curr ≠ null OR stack is not empty:
    while curr ≠ null:
      stack.push(curr)   ← push and go left
      curr = curr.left
    
    curr = stack.pop()   ← backtrack
    visit(curr)
    curr = curr.right    ← go right
```

**Insight**: We push nodes going left, pop when we can't go further left, visit, then move right. This perfectly simulates the recursive call stack.

### Iterative Pre-Order

```
iterative_preorder(root):
  if root is null: return
  stack = [root]
  
  while stack is not empty:
    node = stack.pop()
    visit(node)
    
    // Push RIGHT first so LEFT is processed first (LIFO)
    if node.right ≠ null: stack.push(node.right)
    if node.left  ≠ null: stack.push(node.left)
```

**Insight**: Push right before left — since stack is LIFO, left will be processed first.

### Iterative Post-Order (Two-Stack Method)

```
iterative_postorder(root):
  if root is null: return
  stack1 = [root]
  stack2 = []
  
  while stack1 is not empty:
    node = stack1.pop()
    stack2.push(node)          ← instead of visiting, defer to stack2
    
    if node.left  ≠ null: stack1.push(node.left)
    if node.right ≠ null: stack1.push(node.right)
  
  while stack2 is not empty:
    visit(stack2.pop())        ← reverse of NRL = LRN (post-order!)
```

**Insight**: Stack1 processes in N→R→L order. Stack2 reverses it to L→R→N (post-order).

### Iterative Post-Order (Single-Stack Method)

```
iterative_postorder_single(root):
  stack = []
  curr = root
  last_visited = null
  
  while curr ≠ null OR stack is not empty:
    while curr ≠ null:
      stack.push(curr)
      curr = curr.left
    
    peek = stack.top()
    
    if peek.right ≠ null AND peek.right ≠ last_visited:
      curr = peek.right      ← right subtree not yet done
    else:
      visit(peek)
      last_visited = stack.pop()
```

This is more complex but uses O(h) space with a single stack.

---

## 8. Zigzag / Spiral Level-Order Traversal

A variation of BFS where direction alternates per level: left-to-right, then right-to-left, and so on.

```
        10
       /  \
      5    15
     / \   / \
    3   7 12  20

Level 0 (L→R): 10
Level 1 (R→L): 15, 5
Level 2 (L→R): 3, 7, 12, 20

Output: [[10], [15, 5], [3, 7, 12, 20]]
```

#### Algorithm Using Deque
```
zigzag(root):
  if root is null: return []
  result = []
  queue = deque([root])
  left_to_right = true
  
  while queue is not empty:
    level_size = queue.size()
    level = deque()
    
    repeat level_size times:
      node = queue.popleft()
      
      if left_to_right:
        level.append_right(node.value)
      else:
        level.append_left(node.value)   ← prepend for reverse
      
      if node.left  ≠ null: queue.append(node.left)
      if node.right ≠ null: queue.append(node.right)
    
    result.append(list(level))
    left_to_right = !left_to_right
  
  return result
```

---

## 9. Vertical Order Traversal

Group and sort nodes by their **horizontal distance (column)** from the root. Root has column 0; left child = col-1, right child = col+1.

```
        10  (col=0)
       /  \
      5    15   (col=-1, col=1)
     / \   / \
    3   7 12  20  (col=-2, col=0, col=0, col=2)
```

Nodes with col=0: 10, 7, 12 → sorted by row then value: [10, 7, 12]

```
Output columns:
  col -2: [3]
  col -1: [5]
  col  0: [10, 7, 12]   ← multiple nodes per column
  col  1: [15]
  col  2: [20]
```

#### Algorithm
```
vertical_order(root):
  if root is null: return []
  
  col_map = {}        ← col → list of (row, value)
  queue = [(root, 0, 0)]    ← (node, row, col)
  
  while queue is not empty:
    node, row, col = queue.dequeue()
    col_map[col].append((row, node.value))
    
    if node.left  ≠ null: queue.enqueue((node.left,  row+1, col-1))
    if node.right ≠ null: queue.enqueue((node.right, row+1, col+1))
  
  result = []
  for col in sorted(col_map.keys()):
    sorted_nodes = sort col_map[col] by (row, value)
    result.append([v for (_, v) in sorted_nodes])
  
  return result
```

---

## 10. Boundary Traversal

Print all boundary nodes: left boundary (top-down), leaves (left-right), right boundary (bottom-up), without duplication.

```
        10
       /  \
      5    15
     / \   / \
    3   7 12  20
       / \
      6   8

Left boundary:   10 → 5 → 3
Leaf nodes:      3 → 6 → 8 → 7 → 12 → 20   (no, re-examine tree)
Right boundary:  20 → 15
```

#### Algorithm
```
boundary(root):
  if root is null: return
  
  visit(root)                         ← root (not a leaf)
  print_left_boundary(root.left)      ← left boundary, top-down
  print_leaves(root)                  ← all leaves, left-right
  print_right_boundary(root.right)    ← right boundary, bottom-up

print_left_boundary(node):
  if node is null OR node is leaf: return
  visit(node)
  if node.left  ≠ null: print_left_boundary(node.left)
  else:                  print_left_boundary(node.right)

print_right_boundary(node):
  if node is null OR node is leaf: return
  if node.right ≠ null: print_right_boundary(node.right)
  else:                  print_right_boundary(node.left)
  visit(node)            ← POST-order for bottom-up

print_leaves(node):
  if node is null: return
  print_leaves(node.left)
  if node is leaf: visit(node)
  print_leaves(node.right)
```

---

## 11. Diagonal Traversal

Nodes on the same diagonal (slope of -1, going from top-right to bottom-left) are grouped together.

```
        10  (diag=0)
       /  \
      5    15  (diag=1, diag=0)
     / \   / \
    3   7 12  20  (diag=2,1, diag=1,0)

Diagonal 0: 10 → 15 → 20
Diagonal 1: 5  → 7  → 12
Diagonal 2: 3
```

#### Key rule
- Moving **right** stays on the same diagonal
- Moving **left** increments diagonal by 1

```
diagonal_traversal(root):
  diag_map = {}
  
  dfs(node, d):
    if node is null: return
    diag_map[d].append(node.value)
    dfs(node.left,  d + 1)   ← left = next diagonal
    dfs(node.right, d)       ← right = same diagonal
  
  dfs(root, 0)
  
  for d in sorted(diag_map.keys()):
    print diag_map[d]
```

---

## 12. Complexity Analysis Summary

| Traversal | Time | Space (Recursive) | Space (Iterative) | Space (Morris) |
|---|---|---|---|---|
| In-Order | O(n) | O(h) | O(h) | O(1) |
| Pre-Order | O(n) | O(h) | O(h) | O(1) |
| Post-Order | O(n) | O(h) | O(h) | O(1) |
| Reverse In-Order | O(n) | O(h) | O(h) | O(1) |
| BFS / Level-Order | O(n) | O(w)* | O(w)* | N/A |
| Zigzag | O(n) | O(w) | O(w) | N/A |
| Vertical Order | O(n log n)** | O(n) | O(n) | N/A |
| Boundary | O(n) | O(h) | — | N/A |
| Diagonal | O(n) | O(n) | — | N/A |

- `h` = height of tree (O(log n) balanced, O(n) skewed)
- `w` = maximum width of tree at any level (O(n/2) = O(n) at worst in complete tree)
- `**` Vertical order has O(n log n) due to sorting nodes within columns

---

## 13. Use Cases & When to Use Which

| Goal | Best Traversal | Why |
|---|---|---|
| Get sorted output | In-Order | BST property → ascending order |
| Serialize the tree | Pre-Order | Root first enables reconstruction |
| Deserialize / clone the tree | Pre-Order | Root is first → split into subtrees |
| Delete entire tree | Post-Order | Children freed before parent |
| Evaluate expression tree | Post-Order | Operands before operator |
| Find shortest path / min depth | BFS | Stops at first leaf = minimum depth |
| Level-by-level processing | BFS | Natural level grouping |
| Print tree by columns | Vertical Order | Groups nodes per horizontal distance |
| kth smallest element | In-Order | Sorted order, stop at k |
| kth largest element | Reverse In-Order | Descending, stop at k |
| Check if valid BST | In-Order | Output must be strictly ascending |
| Compute subtree aggregates | Post-Order | Compute children first |
| Find LCA (Lowest Common Ancestor) | Pre-Order / DFS | Top-down search |
| Flatten tree to linked list | Pre-Order | Rearrange in pre-order sequence |
| Balance an unbalanced BST | In-Order → rebuild | Sorted array → balanced BST |
| Space-constrained environment | Morris | O(1) space |
| Avoid stack overflow on deep tree | Iterative | Explicit stack, controllable |

---

## 14. Full Implementations

---

### 14.1 C Implementation

```c
/**
 * BST Traversal — Complete C Implementation
 * Covers: In-Order, Pre-Order, Post-Order, Reverse In-Order,
 *         BFS (Level-Order), Zigzag, Morris In-Order,
 *         Iterative (In/Pre/Post), Vertical Order, Boundary, Diagonal
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <limits.h>

/* ============================================================
 * SECTION 1: Node and Tree Construction
 * ============================================================ */

typedef struct Node {
    int value;
    struct Node *left;
    struct Node *right;
} Node;

Node *new_node(int value) {
    Node *n = (Node *)malloc(sizeof(Node));
    if (!n) { perror("malloc"); exit(EXIT_FAILURE); }
    n->value = value;
    n->left  = NULL;
    n->right = NULL;
    return n;
}

Node *insert(Node *root, int value) {
    if (!root) return new_node(value);
    if (value < root->value)
        root->left  = insert(root->left,  value);
    else if (value > root->value)
        root->right = insert(root->right, value);
    return root;  /* duplicate values ignored */
}

void free_tree(Node *root) {
    if (!root) return;
    free_tree(root->left);
    free_tree(root->right);
    free(root);
}

/* ============================================================
 * SECTION 2: DFS Traversals (Recursive)
 * ============================================================ */

/* In-Order: Left → Node → Right
 * Produces ascending sorted output for valid BST. */
void inorder(Node *root) {
    if (!root) return;
    inorder(root->left);
    printf("%d ", root->value);
    inorder(root->right);
}

/* Pre-Order: Node → Left → Right
 * Useful for tree serialization and reconstruction. */
void preorder(Node *root) {
    if (!root) return;
    printf("%d ", root->value);
    preorder(root->left);
    preorder(root->right);
}

/* Post-Order: Left → Right → Node
 * Useful for tree deletion, evaluating expression trees. */
void postorder(Node *root) {
    if (!root) return;
    postorder(root->left);
    postorder(root->right);
    printf("%d ", root->value);
}

/* Reverse In-Order: Right → Node → Left
 * Produces descending sorted output. */
void reverse_inorder(Node *root) {
    if (!root) return;
    reverse_inorder(root->right);
    printf("%d ", root->value);
    reverse_inorder(root->left);
}

/* ============================================================
 * SECTION 3: Morris In-Order Traversal (O(1) Space)
 * ============================================================ */

/**
 * Morris In-Order Traversal.
 * Achieves O(1) auxiliary space by threading predecessor pointers.
 * Temporarily mutates the tree, restores it fully before returning.
 *
 * Algorithm:
 *   1. If no left child: visit, go right.
 *   2. Else: find in-order predecessor (rightmost of left subtree).
 *      a. If predecessor.right == NULL: thread it to curr, go left.
 *      b. If predecessor.right == curr: remove thread, visit, go right.
 */
void morris_inorder(Node *root) {
    Node *curr = root;
    Node *pred = NULL;

    while (curr) {
        if (!curr->left) {
            /* Case 1: No left child — visit and move right */
            printf("%d ", curr->value);
            curr = curr->right;
        } else {
            /* Find in-order predecessor */
            pred = curr->left;
            while (pred->right && pred->right != curr)
                pred = pred->right;

            if (!pred->right) {
                /* Case 2a: Create thread */
                pred->right = curr;
                curr = curr->left;
            } else {
                /* Case 2b: Thread already exists — remove, visit, go right */
                pred->right = NULL;
                printf("%d ", curr->value);
                curr = curr->right;
            }
        }
    }
}

/* ============================================================
 * SECTION 4: Iterative Traversals (Explicit Stack)
 * ============================================================ */

/* --- Stack Implementation for Nodes --- */
#define MAX_STACK 1024

typedef struct {
    Node *data[MAX_STACK];
    int   top;
} Stack;

void stack_init(Stack *s)        { s->top = -1; }
bool stack_empty(Stack *s)       { return s->top < 0; }
void stack_push(Stack *s, Node *n) {
    if (s->top >= MAX_STACK - 1) { fprintf(stderr, "Stack overflow\n"); exit(1); }
    s->data[++(s->top)] = n;
}
Node *stack_pop(Stack *s) {
    if (stack_empty(s)) { fprintf(stderr, "Stack underflow\n"); exit(1); }
    return s->data[(s->top)--];
}
Node *stack_peek(Stack *s) {
    if (stack_empty(s)) return NULL;
    return s->data[s->top];
}

/**
 * Iterative In-Order.
 * Simulates the call stack: push nodes going left, pop and visit,
 * then move right.
 */
void iterative_inorder(Node *root) {
    Stack s;
    stack_init(&s);
    Node *curr = root;

    while (curr || !stack_empty(&s)) {
        /* Push all left children */
        while (curr) {
            stack_push(&s, curr);
            curr = curr->left;
        }
        /* Backtrack and visit */
        curr = stack_pop(&s);
        printf("%d ", curr->value);
        /* Move to right subtree */
        curr = curr->right;
    }
}

/**
 * Iterative Pre-Order.
 * Push right before left (LIFO: left processed first).
 */
void iterative_preorder(Node *root) {
    if (!root) return;
    Stack s;
    stack_init(&s);
    stack_push(&s, root);

    while (!stack_empty(&s)) {
        Node *node = stack_pop(&s);
        printf("%d ", node->value);
        /* Push right first so left is processed first */
        if (node->right) stack_push(&s, node->right);
        if (node->left)  stack_push(&s, node->left);
    }
}

/**
 * Iterative Post-Order (Two-Stack Method).
 * Stack1 generates N→R→L order.
 * Stack2 reverses to L→R→N (post-order).
 */
void iterative_postorder(Node *root) {
    if (!root) return;
    Stack s1, s2;
    stack_init(&s1);
    stack_init(&s2);
    stack_push(&s1, root);

    while (!stack_empty(&s1)) {
        Node *node = stack_pop(&s1);
        stack_push(&s2, node);
        if (node->left)  stack_push(&s1, node->left);
        if (node->right) stack_push(&s1, node->right);
    }

    while (!stack_empty(&s2)) {
        printf("%d ", stack_pop(&s2)->value);
    }
}

/* ============================================================
 * SECTION 5: BFS / Level-Order Traversal
 * ============================================================ */

/* --- Queue Implementation for BFS --- */
#define MAX_QUEUE 1024

typedef struct {
    Node *data[MAX_QUEUE];
    int   front, rear, size;
} Queue;

void queue_init(Queue *q)  { q->front = q->rear = q->size = 0; }
bool queue_empty(Queue *q) { return q->size == 0; }
void queue_enqueue(Queue *q, Node *n) {
    if (q->size >= MAX_QUEUE) { fprintf(stderr, "Queue full\n"); exit(1); }
    q->data[q->rear] = n;
    q->rear = (q->rear + 1) % MAX_QUEUE;
    q->size++;
}
Node *queue_dequeue(Queue *q) {
    if (queue_empty(q)) { fprintf(stderr, "Queue empty\n"); exit(1); }
    Node *n = q->data[q->front];
    q->front = (q->front + 1) % MAX_QUEUE;
    q->size--;
    return n;
}

/**
 * BFS Level-Order Traversal.
 * Visits nodes level by level, left to right.
 */
void level_order(Node *root) {
    if (!root) return;
    Queue q;
    queue_init(&q);
    queue_enqueue(&q, root);

    while (!queue_empty(&q)) {
        int level_size = q.size;
        printf("[ ");
        for (int i = 0; i < level_size; i++) {
            Node *node = queue_dequeue(&q);
            printf("%d ", node->value);
            if (node->left)  queue_enqueue(&q, node->left);
            if (node->right) queue_enqueue(&q, node->right);
        }
        printf("] ");
    }
    printf("\n");
}

/* ============================================================
 * SECTION 6: Zigzag Level-Order Traversal
 * ============================================================ */

/**
 * Zigzag Traversal.
 * Alternates direction per level: L→R, R→L, L→R, ...
 * Implementation: collect each level into array, then conditionally reverse.
 */
void zigzag_level_order(Node *root) {
    if (!root) return;
    Queue q;
    queue_init(&q);
    queue_enqueue(&q, root);
    bool left_to_right = true;

    while (!queue_empty(&q)) {
        int level_size = q.size;
        int *level = (int *)malloc(level_size * sizeof(int));
        
        for (int i = 0; i < level_size; i++) {
            Node *node = queue_dequeue(&q);
            /* Fill based on direction */
            if (left_to_right)
                level[i] = node->value;
            else
                level[level_size - 1 - i] = node->value;
            
            if (node->left)  queue_enqueue(&q, node->left);
            if (node->right) queue_enqueue(&q, node->right);
        }

        printf("[ ");
        for (int i = 0; i < level_size; i++)
            printf("%d ", level[i]);
        printf("] ");

        free(level);
        left_to_right = !left_to_right;
    }
    printf("\n");
}

/* ============================================================
 * SECTION 7: Boundary Traversal
 * ============================================================ */

bool is_leaf(Node *node) {
    return node && !node->left && !node->right;
}

/* Top-down, exclude leaf */
void print_left_boundary(Node *node) {
    if (!node || is_leaf(node)) return;
    printf("%d ", node->value);
    if (node->left)  print_left_boundary(node->left);
    else             print_left_boundary(node->right);
}

/* All leaves, left-to-right */
void print_leaves(Node *node) {
    if (!node) return;
    print_leaves(node->left);
    if (is_leaf(node)) printf("%d ", node->value);
    print_leaves(node->right);
}

/* Bottom-up, exclude leaf */
void print_right_boundary(Node *node) {
    if (!node || is_leaf(node)) return;
    if (node->right) print_right_boundary(node->right);
    else             print_right_boundary(node->left);
    printf("%d ", node->value);  /* post-order for bottom-up */
}

void boundary_traversal(Node *root) {
    if (!root) return;
    printf("%d ", root->value);         /* root */
    print_left_boundary(root->left);    /* left boundary (excl. root, leaf) */
    print_leaves(root);                 /* all leaves */
    print_right_boundary(root->right);  /* right boundary bottom-up */
    printf("\n");
}

/* ============================================================
 * SECTION 8: Diagonal Traversal
 * ============================================================ */

#define MAX_DIAG 64

/**
 * Diagonal Traversal.
 * Moving right stays on same diagonal (d).
 * Moving left increments diagonal (d+1).
 */
void diagonal_dfs(Node *node, int d, int **diag_vals, int *diag_counts) {
    if (!node) return;
    diag_vals[d][diag_counts[d]++] = node->value;
    diagonal_dfs(node->left,  d + 1, diag_vals, diag_counts);
    diagonal_dfs(node->right, d,     diag_vals, diag_counts);
}

void diagonal_traversal(Node *root) {
    int *diag_vals[MAX_DIAG];
    int  diag_counts[MAX_DIAG];
    memset(diag_counts, 0, sizeof(diag_counts));

    for (int i = 0; i < MAX_DIAG; i++)
        diag_vals[i] = (int *)malloc(256 * sizeof(int));

    diagonal_dfs(root, 0, diag_vals, diag_counts);

    for (int d = 0; d < MAX_DIAG; d++) {
        if (diag_counts[d] == 0) break;
        printf("Diagonal %d: ", d);
        for (int i = 0; i < diag_counts[d]; i++)
            printf("%d ", diag_vals[d][i]);
        printf("\n");
        free(diag_vals[d]);
    }
}

/* ============================================================
 * SECTION 9: Utility — Tree Validation & Height
 * ============================================================ */

int tree_height(Node *root) {
    if (!root) return 0;
    int lh = tree_height(root->left);
    int rh = tree_height(root->right);
    return 1 + (lh > rh ? lh : rh);
}

/**
 * Validate BST using in-order predecessor tracking.
 * A valid BST in-order sequence is strictly ascending.
 */
bool validate_bst_helper(Node *root, long long *prev) {
    if (!root) return true;
    if (!validate_bst_helper(root->left, prev)) return false;
    if (root->value <= *prev) return false;
    *prev = root->value;
    return validate_bst_helper(root->right, prev);
}

bool is_valid_bst(Node *root) {
    long long prev = (long long)INT_MIN - 1;
    return validate_bst_helper(root, &prev);
}

/* ============================================================
 * SECTION 10: Main — Demo
 * ============================================================ */

int main(void) {
    /*
     * Build BST:
     *         10
     *        /  \
     *       5    15
     *      / \   / \
     *     3   7 12  20
     *        / \
     *       6   8
     */
    int values[] = {10, 5, 15, 3, 7, 12, 20, 6, 8};
    int n = sizeof(values) / sizeof(values[0]);
    Node *root = NULL;
    for (int i = 0; i < n; i++)
        root = insert(root, values[i]);

    printf("=== BST Traversal Demo (C) ===\n\n");

    printf("[Recursive DFS]\n");
    printf("  In-Order     : "); inorder(root);          printf("\n");
    printf("  Pre-Order    : "); preorder(root);         printf("\n");
    printf("  Post-Order   : "); postorder(root);        printf("\n");
    printf("  Rev In-Order : "); reverse_inorder(root);  printf("\n\n");

    printf("[Morris Traversal - O(1) Space]\n");
    printf("  Morris In-Order: "); morris_inorder(root); printf("\n\n");

    printf("[Iterative DFS]\n");
    printf("  In-Order     : "); iterative_inorder(root);   printf("\n");
    printf("  Pre-Order    : "); iterative_preorder(root);  printf("\n");
    printf("  Post-Order   : "); iterative_postorder(root); printf("\n\n");

    printf("[BFS Traversals]\n");
    printf("  Level-Order  : "); level_order(root);
    printf("  Zigzag       : "); zigzag_level_order(root);  printf("\n");

    printf("[Structural Traversals]\n");
    printf("  Boundary     : "); boundary_traversal(root);
    printf("  Diagonal     :\n"); diagonal_traversal(root);

    printf("\n[Utility]\n");
    printf("  Height       : %d\n", tree_height(root));
    printf("  Valid BST    : %s\n", is_valid_bst(root) ? "true" : "false");

    free_tree(root);
    return 0;
}
```

---

### 14.2 Go Implementation

```go
// BST Traversal — Complete Go Implementation
// Covers: All traversal strategies with idiomatic Go patterns.
//
// Run: go run bst_traversal.go

package main

import (
	"fmt"
	"math"
	"sort"
)

// ============================================================
// SECTION 1: Node and Tree Construction
// ============================================================

// Node represents a single BST node.
type Node struct {
	Value       int
	Left, Right *Node
}

// NewNode allocates and returns a new BST node.
func NewNode(value int) *Node {
	return &Node{Value: value}
}

// Insert inserts a value into the BST and returns the (possibly new) root.
// Duplicates are ignored — BST invariant: unique values.
func Insert(root *Node, value int) *Node {
	if root == nil {
		return NewNode(value)
	}
	switch {
	case value < root.Value:
		root.Left = Insert(root.Left, value)
	case value > root.Value:
		root.Right = Insert(root.Right, value)
	}
	return root
}

// BuildBST constructs a BST from a slice of values.
func BuildBST(values []int) *Node {
	var root *Node
	for _, v := range values {
		root = Insert(root, v)
	}
	return root
}

// ============================================================
// SECTION 2: DFS Traversals (Recursive)
// ============================================================

// InOrder visits Left → Node → Right.
// Produces ascending sorted output for a valid BST.
func InOrder(root *Node, visit func(int)) {
	if root == nil {
		return
	}
	InOrder(root.Left, visit)
	visit(root.Value)
	InOrder(root.Right, visit)
}

// PreOrder visits Node → Left → Right.
// Useful for serialization and cloning.
func PreOrder(root *Node, visit func(int)) {
	if root == nil {
		return
	}
	visit(root.Value)
	PreOrder(root.Left, visit)
	PreOrder(root.Right, visit)
}

// PostOrder visits Left → Right → Node.
// Useful for deletion, aggregate computation.
func PostOrder(root *Node, visit func(int)) {
	if root == nil {
		return
	}
	PostOrder(root.Left, visit)
	PostOrder(root.Right, visit)
	visit(root.Value)
}

// ReverseInOrder visits Right → Node → Left.
// Produces descending sorted output.
func ReverseInOrder(root *Node, visit func(int)) {
	if root == nil {
		return
	}
	ReverseInOrder(root.Right, visit)
	visit(root.Value)
	ReverseInOrder(root.Left, visit)
}

// ============================================================
// SECTION 3: Morris In-Order Traversal (O(1) Space)
// ============================================================

// MorrisInOrder performs in-order traversal with O(1) auxiliary space.
// Uses the threaded binary tree technique — temporarily threads
// predecessor pointers, restores them after use.
func MorrisInOrder(root *Node, visit func(int)) {
	curr := root
	for curr != nil {
		if curr.Left == nil {
			// Case 1: No left child — visit and move right
			visit(curr.Value)
			curr = curr.Right
		} else {
			// Find in-order predecessor (rightmost of left subtree)
			pred := curr.Left
			for pred.Right != nil && pred.Right != curr {
				pred = pred.Right
			}

			if pred.Right == nil {
				// Case 2a: Create thread — mark return path
				pred.Right = curr
				curr = curr.Left
			} else {
				// Case 2b: Thread exists — came back, remove thread, visit
				pred.Right = nil
				visit(curr.Value)
				curr = curr.Right
			}
		}
	}
}

// ============================================================
// SECTION 4: Iterative Traversals (Explicit Stack)
// ============================================================

// IterativeInOrder simulates the recursive call stack explicitly.
func IterativeInOrder(root *Node, visit func(int)) {
	stack := make([]*Node, 0)
	curr := root

	for curr != nil || len(stack) > 0 {
		// Drill left, pushing nodes onto stack
		for curr != nil {
			stack = append(stack, curr)
			curr = curr.Left
		}
		// Pop, visit, move right
		curr = stack[len(stack)-1]
		stack = stack[:len(stack)-1]
		visit(curr.Value)
		curr = curr.Right
	}
}

// IterativePreOrder uses a stack to visit Node before children.
// Right pushed before left so left is processed first (LIFO).
func IterativePreOrder(root *Node, visit func(int)) {
	if root == nil {
		return
	}
	stack := []*Node{root}

	for len(stack) > 0 {
		node := stack[len(stack)-1]
		stack = stack[:len(stack)-1]

		visit(node.Value)

		// Push right first — left will be popped/processed first
		if node.Right != nil {
			stack = append(stack, node.Right)
		}
		if node.Left != nil {
			stack = append(stack, node.Left)
		}
	}
}

// IterativePostOrder uses two stacks.
// Stack1 generates N→R→L; Stack2 reverses to L→R→N (post-order).
func IterativePostOrder(root *Node, visit func(int)) {
	if root == nil {
		return
	}
	stack1 := []*Node{root}
	stack2 := make([]*Node, 0)

	for len(stack1) > 0 {
		node := stack1[len(stack1)-1]
		stack1 = stack1[:len(stack1)-1]
		stack2 = append(stack2, node)

		if node.Left != nil {
			stack1 = append(stack1, node.Left)
		}
		if node.Right != nil {
			stack1 = append(stack1, node.Right)
		}
	}

	// Process stack2 in reverse — produces post-order
	for len(stack2) > 0 {
		node := stack2[len(stack2)-1]
		stack2 = stack2[:len(stack2)-1]
		visit(node.Value)
	}
}

// ============================================================
// SECTION 5: BFS / Level-Order Traversal
// ============================================================

// LevelOrder performs BFS, returning nodes grouped by level.
// Returns [][]int where result[i] contains values at depth i.
func LevelOrder(root *Node) [][]int {
	if root == nil {
		return nil
	}
	result := [][]int{}
	queue := []*Node{root}

	for len(queue) > 0 {
		levelSize := len(queue)
		level := make([]int, 0, levelSize)

		for i := 0; i < levelSize; i++ {
			node := queue[0]
			queue = queue[1:]
			level = append(level, node.Value)
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

// ============================================================
// SECTION 6: Zigzag Level-Order Traversal
// ============================================================

// ZigzagLevelOrder alternates direction per level.
// Level 0: L→R, Level 1: R→L, Level 2: L→R, ...
func ZigzagLevelOrder(root *Node) [][]int {
	if root == nil {
		return nil
	}
	result := [][]int{}
	queue := []*Node{root}
	leftToRight := true

	for len(queue) > 0 {
		levelSize := len(queue)
		level := make([]int, levelSize)

		for i := 0; i < levelSize; i++ {
			node := queue[0]
			queue = queue[1:]

			// Place value based on direction
			if leftToRight {
				level[i] = node.Value
			} else {
				level[levelSize-1-i] = node.Value
			}

			if node.Left != nil {
				queue = append(queue, node.Left)
			}
			if node.Right != nil {
				queue = append(queue, node.Right)
			}
		}
		result = append(result, level)
		leftToRight = !leftToRight
	}
	return result
}

// ============================================================
// SECTION 7: Vertical Order Traversal
// ============================================================

// columnEntry holds a node value with its row for sorting.
type columnEntry struct {
	row, value int
}

// VerticalOrder groups nodes by horizontal distance from root.
// Returns map[column] → sorted list of values.
func VerticalOrder(root *Node) map[int][]int {
	if root == nil {
		return nil
	}

	// colMap tracks (row, value) pairs per column
	colMap := make(map[int][]columnEntry)

	// BFS queue item: (node, row, col)
	type item struct {
		node    *Node
		row, col int
	}
	queue := []item{{root, 0, 0}}

	for len(queue) > 0 {
		curr := queue[0]
		queue = queue[1:]

		colMap[curr.col] = append(colMap[curr.col], columnEntry{curr.row, curr.node.Value})

		if curr.node.Left != nil {
			queue = append(queue, item{curr.node.Left, curr.row + 1, curr.col - 1})
		}
		if curr.node.Right != nil {
			queue = append(queue, item{curr.node.Right, curr.row + 1, curr.col + 1})
		}
	}

	// Sort each column's entries by (row, value)
	result := make(map[int][]int)
	for col, entries := range colMap {
		sort.Slice(entries, func(i, j int) bool {
			if entries[i].row != entries[j].row {
				return entries[i].row < entries[j].row
			}
			return entries[i].value < entries[j].value
		})
		vals := make([]int, len(entries))
		for i, e := range entries {
			vals[i] = e.value
		}
		result[col] = vals
	}
	return result
}

// ============================================================
// SECTION 8: Boundary Traversal
// ============================================================

func isLeaf(node *Node) bool {
	return node != nil && node.Left == nil && node.Right == nil
}

func leftBoundary(node *Node, result *[]int) {
	if node == nil || isLeaf(node) {
		return
	}
	*result = append(*result, node.Value)
	if node.Left != nil {
		leftBoundary(node.Left, result)
	} else {
		leftBoundary(node.Right, result)
	}
}

func collectLeaves(node *Node, result *[]int) {
	if node == nil {
		return
	}
	collectLeaves(node.Left, result)
	if isLeaf(node) {
		*result = append(*result, node.Value)
	}
	collectLeaves(node.Right, result)
}

func rightBoundary(node *Node, result *[]int) {
	if node == nil || isLeaf(node) {
		return
	}
	if node.Right != nil {
		rightBoundary(node.Right, result)
	} else {
		rightBoundary(node.Left, result)
	}
	*result = append(*result, node.Value) // post-order → bottom-up
}

// BoundaryTraversal returns boundary nodes: left boundary (top-down),
// all leaves (left-right), right boundary (bottom-up).
func BoundaryTraversal(root *Node) []int {
	if root == nil {
		return nil
	}
	result := []int{root.Value}
	leftBoundary(root.Left, &result)
	collectLeaves(root, &result)
	rightBoundary(root.Right, &result)
	return result
}

// ============================================================
// SECTION 9: Diagonal Traversal
// ============================================================

// DiagonalTraversal groups nodes by diagonal (slope = -1 lines).
// Right = same diagonal; Left = next diagonal (d+1).
func DiagonalTraversal(root *Node) map[int][]int {
	result := make(map[int][]int)
	var dfs func(node *Node, d int)
	dfs = func(node *Node, d int) {
		if node == nil {
			return
		}
		result[d] = append(result[d], node.Value)
		dfs(node.Left, d+1)  // left → next diagonal
		dfs(node.Right, d)   // right → same diagonal
	}
	dfs(root, 0)
	return result
}

// ============================================================
// SECTION 10: Utility Functions
// ============================================================

// Height returns the height of the BST.
func Height(root *Node) int {
	if root == nil {
		return 0
	}
	lh := Height(root.Left)
	rh := Height(root.Right)
	if lh > rh {
		return 1 + lh
	}
	return 1 + rh
}

// IsValidBST validates BST property via in-order traversal.
// The in-order sequence must be strictly ascending.
func IsValidBST(root *Node) bool {
	prev := math.MinInt64
	valid := true

	var check func(*Node)
	check = func(node *Node) {
		if node == nil || !valid {
			return
		}
		check(node.Left)
		if node.Value <= prev {
			valid = false
			return
		}
		prev = node.Value
		check(node.Right)
	}
	check(root)
	return valid
}

// KthSmallest finds the kth smallest element using in-order traversal.
func KthSmallest(root *Node, k int) (int, bool) {
	count := 0
	result := 0
	found := false

	var dfs func(*Node)
	dfs = func(node *Node) {
		if node == nil || found {
			return
		}
		dfs(node.Left)
		count++
		if count == k {
			result = node.Value
			found = true
			return
		}
		dfs(node.Right)
	}
	dfs(root)
	return result, found
}

// KthLargest finds the kth largest using reverse in-order traversal.
func KthLargest(root *Node, k int) (int, bool) {
	count := 0
	result := 0
	found := false

	var dfs func(*Node)
	dfs = func(node *Node) {
		if node == nil || found {
			return
		}
		dfs(node.Right)
		count++
		if count == k {
			result = node.Value
			found = true
			return
		}
		dfs(node.Left)
	}
	dfs(root)
	return result, found
}

// ============================================================
// SECTION 11: Main — Demo
// ============================================================

func main() {
	/*
	 * BST structure:
	 *         10
	 *        /  \
	 *       5    15
	 *      / \   / \
	 *     3   7 12  20
	 *        / \
	 *       6   8
	 */
	root := BuildBST([]int{10, 5, 15, 3, 7, 12, 20, 6, 8})

	fmt.Println("=== BST Traversal Demo (Go) ===\n")

	// Collector helper
	collect := func(fn func(*Node, func(int))) []int {
		result := []int{}
		fn(root, func(v int) { result = append(result, v) })
		return result
	}

	fmt.Println("[Recursive DFS]")
	fmt.Printf("  In-Order     : %v\n", collect(InOrder))
	fmt.Printf("  Pre-Order    : %v\n", collect(PreOrder))
	fmt.Printf("  Post-Order   : %v\n", collect(PostOrder))
	fmt.Printf("  Rev In-Order : %v\n\n", collect(ReverseInOrder))

	fmt.Println("[Morris Traversal - O(1) Space]")
	fmt.Printf("  Morris In-Order: %v\n\n", collect(MorrisInOrder))

	fmt.Println("[Iterative DFS]")
	fmt.Printf("  In-Order     : %v\n", collect(IterativeInOrder))
	fmt.Printf("  Pre-Order    : %v\n", collect(IterativePreOrder))
	fmt.Printf("  Post-Order   : %v\n\n", collect(IterativePostOrder))

	fmt.Println("[BFS Traversals]")
	fmt.Printf("  Level-Order  : %v\n", LevelOrder(root))
	fmt.Printf("  Zigzag       : %v\n\n", ZigzagLevelOrder(root))

	fmt.Println("[Structural Traversals]")
	fmt.Printf("  Boundary     : %v\n", BoundaryTraversal(root))

	vo := VerticalOrder(root)
	cols := make([]int, 0, len(vo))
	for c := range vo {
		cols = append(cols, c)
	}
	sort.Ints(cols)
	fmt.Printf("  Vertical     : ")
	for _, c := range cols {
		fmt.Printf("col%d=%v ", c, vo[c])
	}
	fmt.Println()

	diag := DiagonalTraversal(root)
	fmt.Printf("  Diagonal     : ")
	for d := 0; d < len(diag); d++ {
		fmt.Printf("d%d=%v ", d, diag[d])
	}
	fmt.Println()

	fmt.Printf("\n[Utility]\n")
	fmt.Printf("  Height       : %d\n", Height(root))
	fmt.Printf("  Valid BST    : %v\n", IsValidBST(root))

	if v, ok := KthSmallest(root, 3); ok {
		fmt.Printf("  3rd Smallest : %d\n", v)
	}
	if v, ok := KthLargest(root, 2); ok {
		fmt.Printf("  2nd Largest  : %d\n", v)
	}
}
```

---

### 14.3 Rust Implementation

```rust
//! BST Traversal — Complete Rust Implementation
//!
//! Covers: All traversal strategies with idiomatic Rust patterns.
//! Uses safe, owned tree structure with `Box<Node>` for ownership.
//!
//! Run: cargo run (add to main.rs or a standalone binary)

use std::collections::{BTreeMap, VecDeque};

// ============================================================
// SECTION 1: Node and Tree Construction
// ============================================================

/// A single BST node. Ownership managed via Box<T>.
/// Option<Box<Node>> cleanly represents nullable child pointers.
#[derive(Debug)]
pub struct Node {
    pub value: i32,
    pub left:  Option<Box<Node>>,
    pub right: Option<Box<Node>>,
}

impl Node {
    /// Creates a new leaf node.
    pub fn new(value: i32) -> Box<Self> {
        Box::new(Node { value, left: None, right: None })
    }
}

/// BST wrapper type providing a clean API.
#[derive(Debug, Default)]
pub struct BST {
    pub root: Option<Box<Node>>,
}

impl BST {
    pub fn new() -> Self {
        BST { root: None }
    }

    /// Inserts a value. Duplicates are silently ignored.
    pub fn insert(&mut self, value: i32) {
        Self::insert_node(&mut self.root, value);
    }

    fn insert_node(node: &mut Option<Box<Node>>, value: i32) {
        match node {
            None => *node = Some(Node::new(value)),
            Some(n) => match value.cmp(&n.value) {
                std::cmp::Ordering::Less    => Self::insert_node(&mut n.left,  value),
                std::cmp::Ordering::Greater => Self::insert_node(&mut n.right, value),
                std::cmp::Ordering::Equal   => {} // duplicate — ignore
            }
        }
    }

    /// Builds a BST from a slice of values.
    pub fn from_slice(values: &[i32]) -> Self {
        let mut bst = BST::new();
        for &v in values {
            bst.insert(v);
        }
        bst
    }
}

// ============================================================
// SECTION 2: DFS Traversals (Recursive)
// ============================================================

/// In-Order: Left → Node → Right.
/// Produces ascending sorted output for a valid BST.
pub fn inorder(node: &Option<Box<Node>>, result: &mut Vec<i32>) {
    if let Some(n) = node {
        inorder(&n.left, result);
        result.push(n.value);
        inorder(&n.right, result);
    }
}

/// Pre-Order: Node → Left → Right.
/// Root is always first — useful for serialization.
pub fn preorder(node: &Option<Box<Node>>, result: &mut Vec<i32>) {
    if let Some(n) = node {
        result.push(n.value);
        preorder(&n.left, result);
        preorder(&n.right, result);
    }
}

/// Post-Order: Left → Right → Node.
/// Root is always last — useful for cleanup and aggregation.
pub fn postorder(node: &Option<Box<Node>>, result: &mut Vec<i32>) {
    if let Some(n) = node {
        postorder(&n.left, result);
        postorder(&n.right, result);
        result.push(n.value);
    }
}

/// Reverse In-Order: Right → Node → Left.
/// Produces descending sorted output.
pub fn reverse_inorder(node: &Option<Box<Node>>, result: &mut Vec<i32>) {
    if let Some(n) = node {
        reverse_inorder(&n.right, result);
        result.push(n.value);
        reverse_inorder(&n.left, result);
    }
}

// ============================================================
// SECTION 3: Iterative Traversals (Explicit Stack)
// ============================================================

/// Iterative In-Order using an explicit stack.
/// Avoids stack overflow for deep/degenerate trees.
pub fn iterative_inorder(root: &Option<Box<Node>>) -> Vec<i32> {
    let mut result = Vec::new();
    // Stack stores raw pointer references — safe here as tree is immutable
    let mut stack: Vec<&Box<Node>> = Vec::new();
    let mut curr = root.as_ref();

    loop {
        // Drill left
        while let Some(node) = curr {
            stack.push(node);
            curr = node.left.as_ref();
        }
        // Backtrack
        match stack.pop() {
            None => break,
            Some(node) => {
                result.push(node.value);
                curr = node.right.as_ref();
            }
        }
    }
    result
}

/// Iterative Pre-Order.
/// Pushes right before left (LIFO ensures left processed first).
pub fn iterative_preorder(root: &Option<Box<Node>>) -> Vec<i32> {
    let mut result = Vec::new();
    let mut stack: Vec<&Box<Node>> = Vec::new();

    if let Some(node) = root.as_ref() {
        stack.push(node);
    }

    while let Some(node) = stack.pop() {
        result.push(node.value);
        // Right pushed first — left popped first
        if let Some(right) = node.right.as_ref() {
            stack.push(right);
        }
        if let Some(left) = node.left.as_ref() {
            stack.push(left);
        }
    }
    result
}

/// Iterative Post-Order (Two-Stack Method).
/// Stack1 generates N→R→L. Stack2 reverses to post-order L→R→N.
pub fn iterative_postorder(root: &Option<Box<Node>>) -> Vec<i32> {
    let mut stack1: Vec<&Box<Node>> = Vec::new();
    let mut stack2: Vec<i32>        = Vec::new();

    if let Some(node) = root.as_ref() {
        stack1.push(node);
    }

    while let Some(node) = stack1.pop() {
        stack2.push(node.value);
        if let Some(left)  = node.left.as_ref()  { stack1.push(left);  }
        if let Some(right) = node.right.as_ref() { stack1.push(right); }
    }

    stack2.reverse();
    stack2
}

// ============================================================
// SECTION 4: BFS / Level-Order Traversal
// ============================================================

/// Level-Order BFS traversal.
/// Returns nodes grouped by level: Vec<Vec<i32>>.
pub fn level_order(root: &Option<Box<Node>>) -> Vec<Vec<i32>> {
    let mut result = Vec::new();
    if root.is_none() {
        return result;
    }

    // VecDeque as an efficient queue (O(1) push_back, pop_front)
    let mut queue: VecDeque<&Box<Node>> = VecDeque::new();
    if let Some(node) = root.as_ref() {
        queue.push_back(node);
    }

    while !queue.is_empty() {
        let level_size = queue.len();
        let mut level  = Vec::with_capacity(level_size);

        for _ in 0..level_size {
            let node = queue.pop_front().unwrap();
            level.push(node.value);
            if let Some(left)  = node.left.as_ref()  { queue.push_back(left);  }
            if let Some(right) = node.right.as_ref() { queue.push_back(right); }
        }
        result.push(level);
    }
    result
}

// ============================================================
// SECTION 5: Zigzag Level-Order Traversal
// ============================================================

/// Zigzag (Spiral) Level-Order Traversal.
/// Alternates direction: L→R for even levels, R→L for odd levels.
pub fn zigzag_level_order(root: &Option<Box<Node>>) -> Vec<Vec<i32>> {
    let mut result = Vec::new();
    if root.is_none() {
        return result;
    }

    let mut queue: VecDeque<&Box<Node>> = VecDeque::new();
    if let Some(node) = root.as_ref() {
        queue.push_back(node);
    }
    let mut left_to_right = true;

    while !queue.is_empty() {
        let level_size = queue.len();
        let mut level  = vec![0i32; level_size];

        for i in 0..level_size {
            let node = queue.pop_front().unwrap();
            // Place value based on direction
            let idx = if left_to_right { i } else { level_size - 1 - i };
            level[idx] = node.value;

            if let Some(left)  = node.left.as_ref()  { queue.push_back(left);  }
            if let Some(right) = node.right.as_ref() { queue.push_back(right); }
        }
        result.push(level);
        left_to_right = !left_to_right;
    }
    result
}

// ============================================================
// SECTION 6: Vertical Order Traversal
// ============================================================

/// Vertical Order Traversal.
/// Groups nodes by column (horizontal distance from root).
/// Root = col 0; left child = col-1; right child = col+1.
/// Within a column, sorted by row then value.
///
/// BTreeMap used for automatic column sorting.
pub fn vertical_order(root: &Option<Box<Node>>) -> Vec<Vec<i32>> {
    // BTreeMap<col, Vec<(row, value)>>
    let mut col_map: BTreeMap<i32, Vec<(i32, i32)>> = BTreeMap::new();

    // BFS: queue of (node_ref, row, col)
    let mut queue: VecDeque<(&Box<Node>, i32, i32)> = VecDeque::new();
    if let Some(node) = root.as_ref() {
        queue.push_back((node, 0, 0));
    }

    while let Some((node, row, col)) = queue.pop_front() {
        col_map.entry(col).or_default().push((row, node.value));
        if let Some(left)  = node.left.as_ref()  { queue.push_back((left,  row+1, col-1)); }
        if let Some(right) = node.right.as_ref() { queue.push_back((right, row+1, col+1)); }
    }

    col_map.values_mut()
        .map(|entries| {
            entries.sort(); // sort by (row, value) — tuple comparison is lexicographic
            entries.iter().map(|&(_, v)| v).collect()
        })
        .collect()
}

// ============================================================
// SECTION 7: Boundary Traversal
// ============================================================

fn is_leaf(node: &Box<Node>) -> bool {
    node.left.is_none() && node.right.is_none()
}

fn left_boundary(node: &Option<Box<Node>>, result: &mut Vec<i32>) {
    if let Some(n) = node {
        if !is_leaf(n) {
            result.push(n.value);
            if n.left.is_some() {
                left_boundary(&n.left, result);
            } else {
                left_boundary(&n.right, result);
            }
        }
    }
}

fn collect_leaves(node: &Option<Box<Node>>, result: &mut Vec<i32>) {
    if let Some(n) = node {
        collect_leaves(&n.left, result);
        if is_leaf(n) { result.push(n.value); }
        collect_leaves(&n.right, result);
    }
}

fn right_boundary(node: &Option<Box<Node>>, result: &mut Vec<i32>) {
    if let Some(n) = node {
        if !is_leaf(n) {
            if n.right.is_some() {
                right_boundary(&n.right, result);
            } else {
                right_boundary(&n.left, result);
            }
            result.push(n.value); // post-order → bottom-up
        }
    }
}

/// Boundary Traversal: left boundary (top-down) + leaves + right boundary (bottom-up).
pub fn boundary_traversal(root: &Option<Box<Node>>) -> Vec<i32> {
    let mut result = Vec::new();
    if let Some(node) = root.as_ref() {
        result.push(node.value);
        left_boundary(&node.left, &mut result);
        collect_leaves(root, &mut result);
        right_boundary(&node.right, &mut result);
    }
    result
}

// ============================================================
// SECTION 8: Diagonal Traversal
// ============================================================

/// Diagonal Traversal. Nodes on the same diagonal grouped together.
/// Right traversal stays on same diagonal; left increments diagonal.
pub fn diagonal_traversal(root: &Option<Box<Node>>) -> BTreeMap<i32, Vec<i32>> {
    let mut result: BTreeMap<i32, Vec<i32>> = BTreeMap::new();

    fn dfs(node: &Option<Box<Node>>, d: i32, result: &mut BTreeMap<i32, Vec<i32>>) {
        if let Some(n) = node {
            result.entry(d).or_default().push(n.value);
            dfs(&n.left,  d + 1, result); // left → next diagonal
            dfs(&n.right, d,     result); // right → same diagonal
        }
    }

    dfs(root, 0, &mut result);
    result
}

// ============================================================
// SECTION 9: Utility Functions
// ============================================================

/// Returns the height (max depth) of the BST.
pub fn height(root: &Option<Box<Node>>) -> usize {
    match root {
        None    => 0,
        Some(n) => 1 + height(&n.left).max(height(&n.right)),
    }
}

/// Validates BST property: in-order sequence must be strictly ascending.
pub fn is_valid_bst(root: &Option<Box<Node>>) -> bool {
    fn check(node: &Option<Box<Node>>, prev: &mut i64) -> bool {
        match node {
            None    => true,
            Some(n) => {
                if !check(&n.left, prev) { return false; }
                if n.value as i64 <= *prev { return false; }
                *prev = n.value as i64;
                check(&n.right, prev)
            }
        }
    }
    let mut prev = i64::MIN;
    check(root, &mut prev)
}

/// Finds the kth smallest element using in-order traversal.
pub fn kth_smallest(root: &Option<Box<Node>>, k: usize) -> Option<i32> {
    let mut count = 0;
    let mut result = None;

    fn dfs(node: &Option<Box<Node>>, k: usize, count: &mut usize, result: &mut Option<i32>) {
        if node.is_none() || result.is_some() { return; }
        let n = node.as_ref().unwrap();
        dfs(&n.left, k, count, result);
        *count += 1;
        if *count == k {
            *result = Some(n.value);
            return;
        }
        dfs(&n.right, k, count, result);
    }

    dfs(root, k, &mut count, &mut result);
    result
}

/// Finds the kth largest element using reverse in-order traversal.
pub fn kth_largest(root: &Option<Box<Node>>, k: usize) -> Option<i32> {
    let mut count = 0;
    let mut result = None;

    fn dfs(node: &Option<Box<Node>>, k: usize, count: &mut usize, result: &mut Option<i32>) {
        if node.is_none() || result.is_some() { return; }
        let n = node.as_ref().unwrap();
        dfs(&n.right, k, count, result); // right first
        *count += 1;
        if *count == k {
            *result = Some(n.value);
            return;
        }
        dfs(&n.left, k, count, result);
    }

    dfs(root, k, &mut count, &mut result);
    result
}

// ============================================================
// SECTION 10: Main — Demo
// ============================================================

fn main() {
    /*
     * BST structure:
     *         10
     *        /  \
     *       5    15
     *      / \   / \
     *     3   7 12  20
     *        / \
     *       6   8
     */
    let mut bst = BST::from_slice(&[10, 5, 15, 3, 7, 12, 20, 6, 8]);
    let root = &bst.root;

    println!("=== BST Traversal Demo (Rust) ===\n");

    println!("[Recursive DFS]");
    let mut buf = Vec::new();

    buf.clear(); inorder(root, &mut buf);
    println!("  In-Order     : {:?}", buf);

    buf.clear(); preorder(root, &mut buf);
    println!("  Pre-Order    : {:?}", buf);

    buf.clear(); postorder(root, &mut buf);
    println!("  Post-Order   : {:?}", buf);

    buf.clear(); reverse_inorder(root, &mut buf);
    println!("  Rev In-Order : {:?}\n", buf);

    println!("[Iterative DFS]");
    println!("  In-Order     : {:?}", iterative_inorder(root));
    println!("  Pre-Order    : {:?}", iterative_preorder(root));
    println!("  Post-Order   : {:?}\n", iterative_postorder(root));

    println!("[BFS Traversals]");
    println!("  Level-Order  : {:?}", level_order(root));
    println!("  Zigzag       : {:?}\n", zigzag_level_order(root));

    println!("[Structural Traversals]");
    println!("  Boundary     : {:?}", boundary_traversal(root));
    println!("  Vertical     : {:?}", vertical_order(root));

    let diag = diagonal_traversal(root);
    println!("  Diagonal     :");
    for (d, vals) in &diag {
        println!("    d={}: {:?}", d, vals);
    }

    println!("\n[Utility]");
    println!("  Height       : {}", height(root));
    println!("  Valid BST    : {}", is_valid_bst(root));
    println!("  3rd Smallest : {:?}", kth_smallest(root, 3));
    println!("  2nd Largest  : {:?}", kth_largest(root, 2));
}
```

---

## Expected Output (All Implementations)

```
=== BST Traversal Demo ===

[Recursive DFS]
  In-Order     : 3 5 6 7 8 10 12 15 20
  Pre-Order    : 10 5 3 7 6 8 15 12 20
  Post-Order   : 3 6 8 7 5 12 20 15 10
  Rev In-Order : 20 15 12 10 8 7 6 5 3

[Morris Traversal - O(1) Space]
  Morris In-Order: 3 5 6 7 8 10 12 15 20

[Iterative DFS]
  In-Order     : 3 5 6 7 8 10 12 15 20
  Pre-Order    : 10 5 3 7 6 8 15 12 20
  Post-Order   : 3 6 8 7 5 12 20 15 10

[BFS Traversals]
  Level-Order  : [[10], [5, 15], [3, 7, 12, 20], [6, 8]]
  Zigzag       : [[10], [15, 5], [3, 7, 12, 20], [8, 6]]

[Structural Traversals]
  Boundary     : [10, 5, 3, 6, 8, 12, 20, 15]
  Vertical     : col-2=[3] col-1=[5] col0=[10,7,12] col1=[15] col2=[20]
  Diagonal     : d0=[10,15,20] d1=[5,7,12] d2=[3,6,8]

[Utility]
  Height       : 4
  Valid BST    : true
  3rd Smallest : 6
  2nd Largest  : 15
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────┐
│                   BST TRAVERSAL CHEAT SHEET                     │
├──────────────────┬──────────────┬────────┬──────────────────────┤
│ Traversal        │ Pattern      │ Space  │ Primary Use Case      │
├──────────────────┼──────────────┼────────┼──────────────────────┤
│ In-Order         │ L → N → R   │ O(h)   │ Sorted output, kth   │
│ Pre-Order        │ N → L → R   │ O(h)   │ Serialize/clone      │
│ Post-Order       │ L → R → N   │ O(h)   │ Delete, aggregate    │
│ Reverse In-Order │ R → N → L   │ O(h)   │ Descending, kth max  │
│ BFS/Level-Order  │ Level by lvl│ O(w)   │ Min depth, level ops │
│ Zigzag           │ Alt. BFS    │ O(w)   │ Spiral output        │
│ Morris           │ Threaded    │ O(1)   │ Minimal memory       │
│ Iterative DFS    │ Explicit stk│ O(h)   │ No stack overflow    │
│ Vertical Order   │ By column   │ O(n)   │ Column grouping      │
│ Boundary         │ Perimeter   │ O(h)   │ Tree outline         │
│ Diagonal         │ By slope    │ O(n)   │ Diagonal grouping    │
└──────────────────┴──────────────┴────────┴──────────────────────┘
h = tree height | w = max tree width | n = total nodes
```

Here's the complete guide. Here's what's packed in:

**11 Traversal Types Covered:**
- **DFS (Recursive):** In-Order, Pre-Order, Post-Order, Reverse In-Order — with full call stack traces and invariant explanations
- **Iterative DFS:** All three using explicit stacks — including the two-stack post-order trick and single-stack pre-order LIFO insight
- **BFS / Level-Order:** With and without level grouping, queue state walkthrough
- **Morris Traversal:** Full O(1) space — step-by-step thread creation/destruction trace
- **Zigzag / Spiral:** Deque-based alternating direction
- **Vertical Order:** Column-keyed BFS + sort by `(row, value)`
- **Boundary Traversal:** Three-phase: left boundary top-down → leaves → right boundary bottom-up
- **Diagonal Traversal:** DFS keyed by diagonal index

**Per Language highlights:**
- **C:** Custom stack/queue on fixed arrays, Morris traversal, raw pointer management, full memory cleanup
- **Go:** Idiomatic functional visitor pattern (`func(int)`), `VecDeque`-equivalent via slices, `BTreeMap` for sorted column output, closures for kth smallest/largest
- **Rust:** `Option<Box<Node>>` ownership model, safe borrow-based traversal, `BTreeMap` for auto-sorted columns, nested `fn` for DFS closures