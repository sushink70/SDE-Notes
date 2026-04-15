# The Complete Guide to Tree Data Structures: ISDT, Algorithms & Implementations

> **Languages covered:** C · Go · Rust  
> **Scope:** Every major tree variant, all fundamental and advanced operations, real-world complexity analysis, and production-grade implementations.

---

## Table of Contents

1. [Tree Fundamentals & Taxonomy](#1-tree-fundamentals--taxonomy)
2. [Binary Tree — Full ISDT & Operations](#2-binary-tree)
3. [Binary Search Tree (BST)](#3-binary-search-tree-bst)
4. [AVL Tree (Self-Balancing BST)](#4-avl-tree)
5. [Red-Black Tree](#5-red-black-tree)
6. [B-Tree & B+ Tree](#6-b-tree--b-tree)
7. [Heap (Min/Max)](#7-heap-minmax)
8. [Trie (Prefix Tree)](#8-trie-prefix-tree)
9. [Segment Tree](#9-segment-tree)
10. [Fenwick Tree (Binary Indexed Tree)](#10-fenwick-tree-binary-indexed-tree)
11. [Suffix Tree & Suffix Array](#11-suffix-tree--suffix-array)
12. [N-ary Tree & Generic Trees](#12-n-ary-tree--generic-trees)
13. [Disjoint Set Union (DSU/Union-Find)](#13-disjoint-set-union-dsunion-find)
14. [Traversal Algorithms — Deep Dive](#14-traversal-algorithms--deep-dive)
15. [Tree Serialization & Deserialization](#15-tree-serialization--deserialization)
16. [LCA: Lowest Common Ancestor](#16-lca-lowest-common-ancestor)
17. [Tree DP & Advanced Algorithms](#17-tree-dp--advanced-algorithms)
18. [Complexity Cheat Sheet](#18-complexity-cheat-sheet)

---

## 1. Tree Fundamentals & Taxonomy

### What Is a Tree?

A **tree** is a connected, acyclic, undirected graph with `N` nodes and `N-1` edges. In computer science, trees are almost always **rooted** — one node is designated the root, and all edges have an implicit parent→child direction.

**Formal definition:** A rooted tree is a DAG where every node except the root has exactly one parent, and the root has no parent.

### Core Vocabulary

| Term | Definition |
|------|-----------|
| **Root** | The single node with no parent. Entry point of the tree. |
| **Leaf** | A node with no children. |
| **Internal node** | Any node with at least one child. |
| **Depth of node v** | Number of edges from root to v. Root has depth 0. |
| **Height of node v** | Number of edges on the longest path from v to any leaf descendant. |
| **Height of tree** | Height of the root node. |
| **Degree of node** | Number of children a node has. |
| **Subtree** | A node and all its descendants, treated as a tree itself. |
| **Path** | A sequence of nodes where each consecutive pair is parent-child. |
| **Ancestor** | Any node on the path from root to a given node (inclusive). |
| **Descendant** | Any node reachable by following child pointers (inclusive). |
| **Sibling** | Nodes sharing the same parent. |
| **Forest** | A collection of disjoint trees. |
| **Level** | All nodes at the same depth. Level 0 = root. |
| **Width** | Maximum number of nodes at any level. |
| **Balance factor** | `height(left) - height(right)` at any node. |

### Tree Taxonomy

```
Trees
├── General / N-ary
│   ├── Rooted Forest
│   └── Ordered vs Unordered
│
├── Binary Trees
│   ├── Full Binary Tree        (every node has 0 or 2 children)
│   ├── Complete Binary Tree    (all levels full except last, filled L→R)
│   ├── Perfect Binary Tree     (all leaves at same level, all internals have 2 children)
│   ├── Degenerate Tree         (every internal node has 1 child → linked list)
│   ├── Binary Search Tree (BST)
│   │   ├── AVL Tree            (|balance| ≤ 1)
│   │   ├── Red-Black Tree      (color invariants)
│   │   ├── Splay Tree          (self-adjusting)
│   │   ├── Treap               (BST + heap priorities)
│   │   └── Weight-Balanced Tree
│   └── Heap
│       ├── Binary Heap
│       ├── Fibonacci Heap
│       └── Binomial Heap
│
├── Multi-way Trees
│   ├── B-Tree
│   ├── B+ Tree
│   ├── B* Tree
│   └── 2-3-4 Tree
│
├── String / Text Trees
│   ├── Trie
│   ├── Compressed Trie (Patricia / Radix)
│   ├── Suffix Tree
│   └── Suffix Array (not a tree, but derived)
│
└── Range / Interval Trees
    ├── Segment Tree
    ├── Fenwick Tree (BIT)
    ├── Interval Tree
    └── k-d Tree
```

### Key Properties & Formulae

- A **perfect binary tree** of height `h` has `2^(h+1) - 1` nodes and `2^h` leaves.
- A **complete binary tree** with `n` nodes has height `floor(log₂n)`.
- In any binary tree, the number of leaves `L = I + 1` where `I` = number of internal nodes with 2 children (full binary tree property).
- For a BST, **in-order traversal** yields a sorted sequence.
- A **balanced BST** guarantees O(log n) height, thus O(log n) search/insert/delete.

---

## 2. Binary Tree

A binary tree has no ordering constraint — each node holds a value and references to at most two children (left and right). It is the foundation on which BST, AVL, heap, and many other structures are built.

### Node Structure

The most fundamental design decision: **pointer-based** vs **array-based**.

- **Pointer-based:** Each node stores left/right pointers. Flexible, handles unbalanced trees, easy insertion/deletion.
- **Array-based:** Node at index `i`, left child at `2i`, right child at `2i+1`, parent at `i/2`. Cache-friendly for complete trees (heaps). Wastes space for sparse trees.

### CRUD Operations on a Generic Binary Tree

Since a generic binary tree has no ordering constraint, "create" and "insert" require a strategy (e.g., level-order insertion to maintain completeness). "Read" typically means search by value. "Update" is in-place value mutation. "Delete" requires careful child re-linkage.

**Operations and their complexity:**

| Operation | Average | Worst |
|-----------|---------|-------|
| Insert (level-order) | O(n) | O(n) |
| Search | O(n) | O(n) |
| Delete | O(n) | O(n) |
| Traversal | O(n) | O(n) |

Without ordering, all operations are O(n) because we must potentially visit every node. This is why BST and its balanced variants are preferred for lookup-heavy workloads.

---

### C Implementation — Binary Tree

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

/* ─── Node ─────────────────────────────────────────────────────── */
typedef struct BTNode {
    int data;
    struct BTNode *left;
    struct BTNode *right;
} BTNode;

/* ─── Queue (for BFS / level-order) ────────────────────────────── */
typedef struct QNode {
    BTNode *treeNode;
    struct QNode *next;
} QNode;

typedef struct Queue {
    QNode *front, *rear;
    int size;
} Queue;

Queue *queue_create() {
    Queue *q = calloc(1, sizeof(Queue));
    return q;
}

void enqueue(Queue *q, BTNode *node) {
    QNode *qn = malloc(sizeof(QNode));
    qn->treeNode = node;
    qn->next = NULL;
    if (!q->rear) { q->front = q->rear = qn; }
    else          { q->rear->next = qn; q->rear = qn; }
    q->size++;
}

BTNode *dequeue(Queue *q) {
    if (!q->front) return NULL;
    QNode *tmp = q->front;
    BTNode *node = tmp->treeNode;
    q->front = q->front->next;
    if (!q->front) q->rear = NULL;
    q->size--;
    free(tmp);
    return node;
}

bool queue_empty(Queue *q) { return q->size == 0; }
void queue_free(Queue *q) {
    while (!queue_empty(q)) dequeue(q);
    free(q);
}

/* ─── CREATE ────────────────────────────────────────────────────── */
BTNode *bt_node_create(int data) {
    BTNode *n = malloc(sizeof(BTNode));
    n->data  = data;
    n->left  = NULL;
    n->right = NULL;
    return n;
}

/*
 * INSERT (level-order / BFS insertion)
 * Maintains a "complete" binary tree shape.
 * Strategy: BFS until we find a node with a missing child, attach there.
 * Time: O(n) — must BFS to find the first available slot.
 */
BTNode *bt_insert(BTNode *root, int data) {
    BTNode *newNode = bt_node_create(data);
    if (!root) return newNode;

    Queue *q = queue_create();
    enqueue(q, root);

    while (!queue_empty(q)) {
        BTNode *curr = dequeue(q);

        if (!curr->left) {
            curr->left = newNode;
            queue_free(q);
            return root;
        } else {
            enqueue(q, curr->left);
        }

        if (!curr->right) {
            curr->right = newNode;
            queue_free(q);
            return root;
        } else {
            enqueue(q, curr->right);
        }
    }
    queue_free(q);
    return root;
}

/* ─── READ (search) ─────────────────────────────────────────────── */
/*
 * Search for a value using BFS.
 * Returns the node or NULL.
 * Time: O(n)
 */
BTNode *bt_search(BTNode *root, int data) {
    if (!root) return NULL;

    Queue *q = queue_create();
    enqueue(q, root);

    while (!queue_empty(q)) {
        BTNode *curr = dequeue(q);
        if (curr->data == data) {
            queue_free(q);
            return curr;
        }
        if (curr->left)  enqueue(q, curr->left);
        if (curr->right) enqueue(q, curr->right);
    }
    queue_free(q);
    return NULL;
}

/* ─── UPDATE ────────────────────────────────────────────────────── */
/*
 * Find a node with `old_val` and replace with `new_val`.
 * Since no ordering exists, simple BFS.
 * Time: O(n)
 */
bool bt_update(BTNode *root, int old_val, int new_val) {
    BTNode *node = bt_search(root, old_val);
    if (!node) return false;
    node->data = new_val;
    return true;
}

/* ─── DELETE ────────────────────────────────────────────────────── */
/*
 * Delete a node with value `data` from a generic binary tree.
 *
 * Strategy (preserving completeness):
 * 1. Find the node to delete.
 * 2. Find the deepest-rightmost node.
 * 3. Replace the target node's data with deepest-rightmost's data.
 * 4. Delete the deepest-rightmost node.
 *
 * This avoids complex pointer surgery and maintains a complete tree shape.
 * Time: O(n)
 */
static void bt_delete_deepest(BTNode *root, BTNode *delNode) {
    Queue *q = queue_create();
    enqueue(q, root);

    QNode *last = NULL;
    BTNode *prev = NULL;

    while (!queue_empty(q)) {
        BTNode *curr = dequeue(q);

        if (curr == delNode) {
            /* Found: parent is `prev` and we know which child this is */
            /* We'll do removal below */
        }

        if (curr->left) {
            if (curr->left == delNode) {
                curr->left = NULL;
                queue_free(q);
                return;
            }
            enqueue(q, curr->left);
        }

        if (curr->right) {
            if (curr->right == delNode) {
                curr->right = NULL;
                queue_free(q);
                return;
            }
            enqueue(q, curr->right);
        }
    }
    queue_free(q);
}

BTNode *bt_delete(BTNode *root, int data) {
    if (!root) return NULL;

    /* Edge case: single node */
    if (!root->left && !root->right) {
        if (root->data == data) {
            free(root);
            return NULL;
        }
        return root;
    }

    BTNode *targetNode = NULL;
    BTNode *lastNode   = NULL;

    Queue *q = queue_create();
    enqueue(q, root);

    while (!queue_empty(q)) {
        BTNode *curr = dequeue(q);
        if (curr->data == data) targetNode = curr;
        lastNode = curr;   /* track deepest-rightmost */
        if (curr->left)  enqueue(q, curr->left);
        if (curr->right) enqueue(q, curr->right);
    }
    queue_free(q);

    if (targetNode) {
        /* Copy data from deepest node to target */
        targetNode->data = lastNode->data;
        /* Remove the deepest-rightmost node */
        bt_delete_deepest(root, lastNode);
        free(lastNode);
    }
    return root;
}

/* ─── TRAVERSALS ────────────────────────────────────────────────── */
void bt_inorder(BTNode *root) {
    if (!root) return;
    bt_inorder(root->left);
    printf("%d ", root->data);
    bt_inorder(root->right);
}

void bt_preorder(BTNode *root) {
    if (!root) return;
    printf("%d ", root->data);
    bt_preorder(root->left);
    bt_preorder(root->right);
}

void bt_postorder(BTNode *root) {
    if (!root) return;
    bt_postorder(root->left);
    bt_postorder(root->right);
    printf("%d ", root->data);
}

void bt_levelorder(BTNode *root) {
    if (!root) return;
    Queue *q = queue_create();
    enqueue(q, root);
    while (!queue_empty(q)) {
        BTNode *curr = dequeue(q);
        printf("%d ", curr->data);
        if (curr->left)  enqueue(q, curr->left);
        if (curr->right) enqueue(q, curr->right);
    }
    queue_free(q);
}

/* ─── HEIGHT & SIZE ─────────────────────────────────────────────── */
int bt_height(BTNode *root) {
    if (!root) return -1;  /* -1 for empty, 0 for leaf */
    int lh = bt_height(root->left);
    int rh = bt_height(root->right);
    return 1 + (lh > rh ? lh : rh);
}

int bt_size(BTNode *root) {
    if (!root) return 0;
    return 1 + bt_size(root->left) + bt_size(root->right);
}

/* ─── FREE ──────────────────────────────────────────────────────── */
void bt_free(BTNode *root) {
    if (!root) return;
    bt_free(root->left);
    bt_free(root->right);
    free(root);
}

/* ─── DEMO ──────────────────────────────────────────────────────── */
int main(void) {
    BTNode *root = NULL;

    /* Insert */
    int values[] = {1, 2, 3, 4, 5, 6, 7};
    for (int i = 0; i < 7; i++)
        root = bt_insert(root, values[i]);

    printf("In-order:    "); bt_inorder(root);   printf("\n");
    printf("Pre-order:   "); bt_preorder(root);  printf("\n");
    printf("Post-order:  "); bt_postorder(root); printf("\n");
    printf("Level-order: "); bt_levelorder(root); printf("\n");
    printf("Height: %d, Size: %d\n", bt_height(root), bt_size(root));

    /* Search */
    BTNode *found = bt_search(root, 5);
    printf("Search 5: %s\n", found ? "found" : "not found");

    /* Update */
    bt_update(root, 5, 99);
    printf("After update(5->99) level-order: ");
    bt_levelorder(root); printf("\n");

    /* Delete */
    root = bt_delete(root, 2);
    printf("After delete(2) level-order: ");
    bt_levelorder(root); printf("\n");

    bt_free(root);
    return 0;
}
```

---

### Go Implementation — Binary Tree

```go
package main

import "fmt"

// ─── Node ─────────────────────────────────────────────────────────
type BTNode struct {
    Data  int
    Left  *BTNode
    Right *BTNode
}

func newBTNode(data int) *BTNode {
    return &BTNode{Data: data}
}

// ─── INSERT (level-order) ─────────────────────────────────────────
// Uses a channel as an efficient queue for BFS.
func BTInsert(root *BTNode, data int) *BTNode {
    newNode := newBTNode(data)
    if root == nil {
        return newNode
    }

    queue := []*BTNode{root}
    for len(queue) > 0 {
        curr := queue[0]
        queue = queue[1:]

        if curr.Left == nil {
            curr.Left = newNode
            return root
        }
        queue = append(queue, curr.Left)

        if curr.Right == nil {
            curr.Right = newNode
            return root
        }
        queue = append(queue, curr.Right)
    }
    return root
}

// ─── SEARCH ───────────────────────────────────────────────────────
func BTSearch(root *BTNode, data int) *BTNode {
    if root == nil {
        return nil
    }
    queue := []*BTNode{root}
    for len(queue) > 0 {
        curr := queue[0]
        queue = queue[1:]
        if curr.Data == data {
            return curr
        }
        if curr.Left != nil {
            queue = append(queue, curr.Left)
        }
        if curr.Right != nil {
            queue = append(queue, curr.Right)
        }
    }
    return nil
}

// ─── UPDATE ───────────────────────────────────────────────────────
func BTUpdate(root *BTNode, oldVal, newVal int) bool {
    node := BTSearch(root, oldVal)
    if node == nil {
        return false
    }
    node.Data = newVal
    return true
}

// ─── DELETE ───────────────────────────────────────────────────────
// Find target node and deepest-rightmost node via BFS.
// Copy deepest's data to target, then remove the deepest.
func BTDelete(root *BTNode, data int) *BTNode {
    if root == nil {
        return nil
    }

    // Single node
    if root.Left == nil && root.Right == nil {
        if root.Data == data {
            return nil
        }
        return root
    }

    var targetNode, lastNode *BTNode
    var lastParent *BTNode
    var lastIsLeft bool

    queue := []*BTNode{root}
    // We need parent info to detach the deepest node
    type entry struct {
        node   *BTNode
        parent *BTNode
        isLeft bool
    }

    bfsQueue := []entry{{root, nil, false}}
    for len(bfsQueue) > 0 {
        curr := bfsQueue[0]
        bfsQueue = bfsQueue[1:]

        if curr.node.Data == data {
            targetNode = curr.node
        }

        lastNode = curr.node
        lastParent = curr.parent
        lastIsLeft = curr.isLeft

        if curr.node.Left != nil {
            bfsQueue = append(bfsQueue, entry{curr.node.Left, curr.node, true})
        }
        if curr.node.Right != nil {
            bfsQueue = append(bfsQueue, entry{curr.node.Right, curr.node, false})
        }
    }
    _ = queue

    if targetNode != nil {
        targetNode.Data = lastNode.Data
        // Detach lastNode
        if lastParent != nil {
            if lastIsLeft {
                lastParent.Left = nil
            } else {
                lastParent.Right = nil
            }
        }
    }
    return root
}

// ─── TRAVERSALS ───────────────────────────────────────────────────
func BTInorder(root *BTNode) {
    if root == nil {
        return
    }
    BTInorder(root.Left)
    fmt.Printf("%d ", root.Data)
    BTInorder(root.Right)
}

func BTPreorder(root *BTNode) {
    if root == nil {
        return
    }
    fmt.Printf("%d ", root.Data)
    BTPreorder(root.Left)
    BTPreorder(root.Right)
}

func BTPostorder(root *BTNode) {
    if root == nil {
        return
    }
    BTPostorder(root.Left)
    BTPostorder(root.Right)
    fmt.Printf("%d ", root.Data)
}

func BTLevelOrder(root *BTNode) {
    if root == nil {
        return
    }
    queue := []*BTNode{root}
    for len(queue) > 0 {
        curr := queue[0]
        queue = queue[1:]
        fmt.Printf("%d ", curr.Data)
        if curr.Left != nil {
            queue = append(queue, curr.Left)
        }
        if curr.Right != nil {
            queue = append(queue, curr.Right)
        }
    }
}

// ─── HEIGHT & SIZE ────────────────────────────────────────────────
func BTHeight(root *BTNode) int {
    if root == nil {
        return -1
    }
    lh := BTHeight(root.Left)
    rh := BTHeight(root.Right)
    if lh > rh {
        return lh + 1
    }
    return rh + 1
}

func BTSize(root *BTNode) int {
    if root == nil {
        return 0
    }
    return 1 + BTSize(root.Left) + BTSize(root.Right)
}

func main() {
    var root *BTNode
    for _, v := range []int{1, 2, 3, 4, 5, 6, 7} {
        root = BTInsert(root, v)
    }

    fmt.Print("In-order:    "); BTInorder(root); fmt.Println()
    fmt.Print("Pre-order:   "); BTPreorder(root); fmt.Println()
    fmt.Print("Post-order:  "); BTPostorder(root); fmt.Println()
    fmt.Print("Level-order: "); BTLevelOrder(root); fmt.Println()
    fmt.Printf("Height: %d, Size: %d\n", BTHeight(root), BTSize(root))

    found := BTSearch(root, 5)
    if found != nil {
        fmt.Printf("Search 5: found (%d)\n", found.Data)
    }

    BTUpdate(root, 5, 99)
    fmt.Print("After update(5->99): "); BTLevelOrder(root); fmt.Println()

    root = BTDelete(root, 2)
    fmt.Print("After delete(2): "); BTLevelOrder(root); fmt.Println()
}
```

---

### Rust Implementation — Binary Tree

```rust
use std::collections::VecDeque;

// ─── Node ─────────────────────────────────────────────────────────
// Rust trees are notoriously tricky due to ownership.
// We use Option<Box<T>> — the idiomatic, safe approach.
// Box gives heap allocation; Option models null.

#[derive(Debug)]
pub struct BTNode {
    pub data: i32,
    pub left: Option<Box<BTNode>>,
    pub right: Option<Box<BTNode>>,
}

impl BTNode {
    pub fn new(data: i32) -> Self {
        BTNode { data, left: None, right: None }
    }
}

// ─── INSERT (level-order using raw pointers for BFS mutation) ─────
// The challenge in Rust: BFS requires holding multiple &mut references,
// which the borrow checker disallows. We use an unsafe raw-pointer
// BFS queue — a deliberate, contained use of unsafe for performance.
// Alternative (safe): use Rc<RefCell<BTNode>> — see note below.
pub fn bt_insert(root: &mut Option<Box<BTNode>>, data: i32) {
    let new_node = Box::new(BTNode::new(data));

    if root.is_none() {
        *root = Some(new_node);
        return;
    }

    // Safety: We hold &mut root exclusively; raw pointers are used
    // only within this function scope and not stored beyond it.
    let mut queue: VecDeque<*mut BTNode> = VecDeque::new();
    if let Some(ref mut r) = root {
        queue.push_back(r.as_mut() as *mut BTNode);
    }

    while let Some(ptr) = queue.pop_front() {
        let curr = unsafe { &mut *ptr };

        if curr.left.is_none() {
            curr.left = Some(new_node);
            return;
        } else if let Some(ref mut l) = curr.left {
            queue.push_back(l.as_mut() as *mut BTNode);
        }

        if curr.right.is_none() {
            curr.right = Some(new_node);
            return;
        } else if let Some(ref mut r) = curr.right {
            queue.push_back(r.as_mut() as *mut BTNode);
        }
    }
}

// ─── SEARCH ───────────────────────────────────────────────────────
pub fn bt_search(root: &Option<Box<BTNode>>, data: i32) -> bool {
    let mut queue: VecDeque<&BTNode> = VecDeque::new();
    if let Some(ref r) = root {
        queue.push_back(r);
    }
    while let Some(curr) = queue.pop_front() {
        if curr.data == data {
            return true;
        }
        if let Some(ref l) = curr.left  { queue.push_back(l); }
        if let Some(ref r) = curr.right { queue.push_back(r); }
    }
    false
}

// ─── UPDATE ───────────────────────────────────────────────────────
pub fn bt_update(root: &mut Option<Box<BTNode>>, old_val: i32, new_val: i32) -> bool {
    let mut queue: VecDeque<*mut BTNode> = VecDeque::new();
    if let Some(ref mut r) = root {
        queue.push_back(r.as_mut() as *mut BTNode);
    }
    while let Some(ptr) = queue.pop_front() {
        let curr = unsafe { &mut *ptr };
        if curr.data == old_val {
            curr.data = new_val;
            return true;
        }
        if let Some(ref mut l) = curr.left  { queue.push_back(l.as_mut()); }
        if let Some(ref mut r) = curr.right { queue.push_back(r.as_mut()); }
    }
    false
}

// ─── TRAVERSALS ───────────────────────────────────────────────────
pub fn bt_inorder(root: &Option<Box<BTNode>>, out: &mut Vec<i32>) {
    if let Some(ref node) = root {
        bt_inorder(&node.left, out);
        out.push(node.data);
        bt_inorder(&node.right, out);
    }
}

pub fn bt_preorder(root: &Option<Box<BTNode>>, out: &mut Vec<i32>) {
    if let Some(ref node) = root {
        out.push(node.data);
        bt_preorder(&node.left, out);
        bt_preorder(&node.right, out);
    }
}

pub fn bt_levelorder(root: &Option<Box<BTNode>>, out: &mut Vec<i32>) {
    let mut queue: VecDeque<&BTNode> = VecDeque::new();
    if let Some(ref r) = root { queue.push_back(r); }
    while let Some(curr) = queue.pop_front() {
        out.push(curr.data);
        if let Some(ref l) = curr.left  { queue.push_back(l); }
        if let Some(ref r) = curr.right { queue.push_back(r); }
    }
}

// ─── HEIGHT ───────────────────────────────────────────────────────
pub fn bt_height(root: &Option<Box<BTNode>>) -> i32 {
    match root {
        None => -1,
        Some(node) => {
            let lh = bt_height(&node.left);
            let rh = bt_height(&node.right);
            1 + lh.max(rh)
        }
    }
}

fn main() {
    let mut root: Option<Box<BTNode>> = None;
    for v in [1, 2, 3, 4, 5, 6, 7] {
        bt_insert(&mut root, v);
    }

    let mut out = Vec::new();
    bt_inorder(&root, &mut out);
    println!("In-order: {:?}", out);

    out.clear();
    bt_levelorder(&root, &mut out);
    println!("Level-order: {:?}", out);

    println!("Search 5: {}", bt_search(&root, 5));
    println!("Height: {}", bt_height(&root));

    bt_update(&mut root, 5, 99);
    out.clear();
    bt_levelorder(&root, &mut out);
    println!("After update(5->99): {:?}", out);
}

/*
 * NOTE on Rc<RefCell<T>> approach:
 * For trees that need shared ownership or complex mutations without unsafe,
 * use: type Tree = Option<Rc<RefCell<BTNode>>>;
 * This enables interior mutability and multiple owners but has runtime
 * borrow-checking overhead. Preferred for graph-like trees or when
 * you need parent pointers.
 */
```

---

## 3. Binary Search Tree (BST)

A BST is a binary tree with a **total ordering invariant**: for every node `N`, all keys in `N.left < N.key < N.right`. This ordering enables O(log n) average-case search, insert, and delete.

### BST Invariant (Formally)

For every node `v`:
- All nodes in `left subtree(v)` have keys **strictly less** than `v.key`
- All nodes in `right subtree(v)` have keys **strictly greater** than `v.key`
- No duplicate keys (or duplicates go consistently left or right — your choice, but be consistent)

### BST Operations

| Operation | Average Case | Worst Case (degenerate/sorted input) |
|-----------|-------------|--------------------------------------|
| Search    | O(log n)    | O(n)                                 |
| Insert    | O(log n)    | O(n)                                 |
| Delete    | O(log n)    | O(n)                                 |
| Min/Max   | O(log n)    | O(n)                                 |
| Successor/Predecessor | O(log n) | O(n)                      |
| In-order traversal    | O(n) | O(n)                              |
| Height    | O(n)        | O(n)                                 |

### BST Delete — Three Cases

BST deletion is the most nuanced operation:

1. **Node has no children (leaf):** Simply remove it.
2. **Node has one child:** Replace node with its child.
3. **Node has two children:** Find the **in-order successor** (smallest in right subtree) OR the **in-order predecessor** (largest in left subtree). Copy its key to the target node. Delete the successor/predecessor (which has at most one child — by BST structure).

### Predecessor and Successor

- **Successor** of node `v`: The node with the smallest key **greater** than `v.key`.
  - If `v.right` exists: leftmost node in `v.right`.
  - If not: walk up the tree; find the first ancestor where `v` is in the left subtree.
- **Predecessor** of node `v`: The node with the largest key **less** than `v.key`.
  - If `v.left` exists: rightmost node in `v.left`.
  - If not: walk up; find first ancestor where `v` is in the right subtree.

---

### C Implementation — BST

```c
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

typedef struct BSTNode {
    int key;
    struct BSTNode *left;
    struct BSTNode *right;
    struct BSTNode *parent;  /* optional but enables O(log n) successor */
} BSTNode;

/* ─── Helpers ───────────────────────────────────────────────────── */
static BSTNode *bst_new(int key) {
    BSTNode *n = malloc(sizeof(BSTNode));
    n->key = key; n->left = n->right = n->parent = NULL;
    return n;
}

/* Leftmost node in a subtree → minimum */
static BSTNode *bst_min(BSTNode *root) {
    if (!root) return NULL;
    while (root->left) root = root->left;
    return root;
}

/* Rightmost node in a subtree → maximum */
static BSTNode *bst_max(BSTNode *root) {
    if (!root) return NULL;
    while (root->right) root = root->right;
    return root;
}

/* ─── INSERT ────────────────────────────────────────────────────── */
/*
 * Iterative insertion preserving parent pointers.
 * Returns the (possibly new) root.
 * Time: O(h) where h = tree height. O(log n) avg, O(n) worst.
 */
BSTNode *bst_insert(BSTNode *root, int key) {
    BSTNode *parent = NULL;
    BSTNode *curr   = root;

    /* Traverse to insertion point */
    while (curr) {
        parent = curr;
        if (key < curr->key)       curr = curr->left;
        else if (key > curr->key)  curr = curr->right;
        else return root;  /* duplicate: ignore */
    }

    BSTNode *newNode = bst_new(key);
    newNode->parent = parent;

    if (!parent) return newNode;  /* tree was empty */
    if (key < parent->key) parent->left  = newNode;
    else                   parent->right = newNode;

    return root;
}

/* ─── SEARCH ────────────────────────────────────────────────────── */
/*
 * Standard BST search. Leverages ordering invariant.
 * Time: O(h).
 */
BSTNode *bst_search(BSTNode *root, int key) {
    BSTNode *curr = root;
    while (curr) {
        if      (key < curr->key) curr = curr->left;
        else if (key > curr->key) curr = curr->right;
        else return curr;
    }
    return NULL;
}

/* ─── SUCCESSOR & PREDECESSOR ───────────────────────────────────── */
BSTNode *bst_successor(BSTNode *node) {
    if (!node) return NULL;
    /* Case 1: Right subtree exists → leftmost in right subtree */
    if (node->right) return bst_min(node->right);
    /* Case 2: Walk up until we come from a left link */
    BSTNode *anc = node->parent;
    while (anc && node == anc->right) {
        node = anc;
        anc  = anc->parent;
    }
    return anc;
}

BSTNode *bst_predecessor(BSTNode *node) {
    if (!node) return NULL;
    if (node->left) return bst_max(node->left);
    BSTNode *anc = node->parent;
    while (anc && node == anc->left) {
        node = anc;
        anc  = anc->parent;
    }
    return anc;
}

/* ─── DELETE ────────────────────────────────────────────────────── */
/*
 * Helper: replace subtree rooted at `u` with subtree rooted at `v`.
 * Updates parent pointers.
 */
static void transplant(BSTNode **root, BSTNode *u, BSTNode *v) {
    if (!u->parent) {
        *root = v;
    } else if (u == u->parent->left) {
        u->parent->left = v;
    } else {
        u->parent->right = v;
    }
    if (v) v->parent = u->parent;
}

BSTNode *bst_delete(BSTNode *root, int key) {
    BSTNode *z = bst_search(root, key);
    if (!z) return root;  /* key not found */

    if (!z->left) {
        /* Case 1 & 2a: no left child — replace z with right child */
        transplant(&root, z, z->right);
    } else if (!z->right) {
        /* Case 2b: no right child — replace z with left child */
        transplant(&root, z, z->left);
    } else {
        /* Case 3: two children */
        /* Find in-order successor (min of right subtree) */
        BSTNode *y = bst_min(z->right);

        if (y->parent != z) {
            /* Successor is not the direct right child */
            /* Detach successor, put its right child in its place */
            transplant(&root, y, y->right);
            y->right         = z->right;
            y->right->parent = y;
        }
        /* Replace z with successor */
        transplant(&root, z, y);
        y->left         = z->left;
        y->left->parent = y;
    }

    free(z);
    return root;
}

/* ─── RANGE QUERY ───────────────────────────────────────────────── */
/*
 * Print all keys in [lo, hi].
 * BST ordering lets us prune branches efficiently.
 * Time: O(k + log n) where k = number of results.
 */
void bst_range(BSTNode *root, int lo, int hi) {
    if (!root) return;
    if (root->key > lo) bst_range(root->left,  lo, hi);
    if (root->key >= lo && root->key <= hi) printf("%d ", root->key);
    if (root->key < hi) bst_range(root->right, lo, hi);
}

/* ─── FLOOR & CEILING ───────────────────────────────────────────── */
/*
 * Floor(key): largest key ≤ key in the BST.
 * Ceiling(key): smallest key ≥ key in the BST.
 */
BSTNode *bst_floor(BSTNode *root, int key) {
    if (!root) return NULL;
    if (root->key == key) return root;
    if (root->key > key)  return bst_floor(root->left, key);
    /* root->key < key: floor might be in right subtree */
    BSTNode *t = bst_floor(root->right, key);
    return t ? t : root;
}

BSTNode *bst_ceiling(BSTNode *root, int key) {
    if (!root) return NULL;
    if (root->key == key) return root;
    if (root->key < key)  return bst_ceiling(root->right, key);
    BSTNode *t = bst_ceiling(root->left, key);
    return t ? t : root;
}

/* ─── RANK & SELECT ─────────────────────────────────────────────── */
/*
 * rank(key): number of keys < key in the BST.
 * select(k): the k-th smallest key (0-indexed).
 * Note: These run in O(n) without augmented node sizes.
 * With size-augmented nodes they run in O(h).
 */
int bst_rank(BSTNode *root, int key) {
    if (!root) return 0;
    if (key < root->key)  return bst_rank(root->left, key);
    if (key > root->key)  return 1 + bst_rank(root->left, key) + bst_rank(root->right, key);
    return bst_rank(root->left, key);   /* key == root->key: count left */
}

/* ─── VALIDATION ────────────────────────────────────────────────── */
/*
 * Validate BST invariant using the min/max bound technique.
 * Pass INT_MIN and INT_MAX initially; tighten bounds at each step.
 */
#include <limits.h>
bool bst_is_valid(BSTNode *root, long min_val, long max_val) {
    if (!root) return true;
    if (root->key <= min_val || root->key >= max_val) return false;
    return bst_is_valid(root->left,  min_val, root->key) &&
           bst_is_valid(root->right, root->key, max_val);
}

/* ─── INORDER ───────────────────────────────────────────────────── */
void bst_inorder(BSTNode *root) {
    if (!root) return;
    bst_inorder(root->left);
    printf("%d ", root->key);
    bst_inorder(root->right);
}

void bst_free(BSTNode *root) {
    if (!root) return;
    bst_free(root->left);
    bst_free(root->right);
    free(root);
}

int main(void) {
    BSTNode *root = NULL;
    int keys[] = {5, 3, 7, 1, 4, 6, 8, 2};
    for (int i = 0; i < 8; i++)
        root = bst_insert(root, keys[i]);

    printf("In-order (sorted): "); bst_inorder(root); printf("\n");

    /* Successor/Predecessor */
    BSTNode *n4 = bst_search(root, 4);
    BSTNode *succ = bst_successor(n4);
    BSTNode *pred = bst_predecessor(n4);
    printf("Successor of 4: %d\n", succ ? succ->key : -1);
    printf("Predecessor of 4: %d\n", pred ? pred->key : -1);

    /* Floor / Ceiling */
    printf("Floor(4.5)=4:   %d\n", bst_floor(root, 4) ? bst_floor(root,4)->key : -1);
    printf("Ceiling(4.5)=5: %d\n", bst_ceiling(root,5) ? bst_ceiling(root,5)->key : -1);

    /* Range query */
    printf("Range [3,7]: "); bst_range(root, 3, 7); printf("\n");

    /* Delete */
    root = bst_delete(root, 5);  /* root deletion, two-child case */
    printf("After deleting root (5): "); bst_inorder(root); printf("\n");

    /* Validate */
    printf("BST valid: %s\n", bst_is_valid(root, LONG_MIN, LONG_MAX) ? "yes" : "no");

    bst_free(root);
    return 0;
}
```

---

### Go Implementation — BST

```go
package main

import (
    "fmt"
    "math"
)

// ─── Node ─────────────────────────────────────────────────────────
type BSTNode struct {
    Key    int
    Left   *BSTNode
    Right  *BSTNode
    Parent *BSTNode
}

func newBSTNode(key int) *BSTNode { return &BSTNode{Key: key} }

func bstMin(root *BSTNode) *BSTNode {
    for root != nil && root.Left != nil { root = root.Left }
    return root
}

func bstMax(root *BSTNode) *BSTNode {
    for root != nil && root.Right != nil { root = root.Right }
    return root
}

// ─── INSERT ───────────────────────────────────────────────────────
func BSTInsert(root *BSTNode, key int) *BSTNode {
    var parent *BSTNode
    curr := root

    for curr != nil {
        parent = curr
        if key < curr.Key {
            curr = curr.Left
        } else if key > curr.Key {
            curr = curr.Right
        } else {
            return root // duplicate
        }
    }

    node := newBSTNode(key)
    node.Parent = parent
    if parent == nil { return node }
    if key < parent.Key { parent.Left = node } else { parent.Right = node }
    return root
}

// ─── SEARCH ───────────────────────────────────────────────────────
func BSTSearch(root *BSTNode, key int) *BSTNode {
    for root != nil {
        if key < root.Key      { root = root.Left  }
        else if key > root.Key { root = root.Right }
        else                   { return root       }
    }
    return nil
}

// ─── SUCCESSOR / PREDECESSOR ──────────────────────────────────────
func BSTSuccessor(node *BSTNode) *BSTNode {
    if node == nil { return nil }
    if node.Right != nil { return bstMin(node.Right) }
    anc := node.Parent
    for anc != nil && node == anc.Right { node = anc; anc = anc.Parent }
    return anc
}

func BSTPredecessor(node *BSTNode) *BSTNode {
    if node == nil { return nil }
    if node.Left != nil { return bstMax(node.Left) }
    anc := node.Parent
    for anc != nil && node == anc.Left { node = anc; anc = anc.Parent }
    return anc
}

// ─── DELETE ───────────────────────────────────────────────────────
func transplant(rootPtr **BSTNode, u, v *BSTNode) {
    if u.Parent == nil {
        *rootPtr = v
    } else if u == u.Parent.Left {
        u.Parent.Left = v
    } else {
        u.Parent.Right = v
    }
    if v != nil { v.Parent = u.Parent }
}

func BSTDelete(root *BSTNode, key int) *BSTNode {
    z := BSTSearch(root, key)
    if z == nil { return root }

    if z.Left == nil {
        transplant(&root, z, z.Right)
    } else if z.Right == nil {
        transplant(&root, z, z.Left)
    } else {
        y := bstMin(z.Right)
        if y.Parent != z {
            transplant(&root, y, y.Right)
            y.Right = z.Right
            y.Right.Parent = y
        }
        transplant(&root, z, y)
        y.Left = z.Left
        y.Left.Parent = y
    }
    return root
}

// ─── FLOOR / CEILING ──────────────────────────────────────────────
func BSTFloor(root *BSTNode, key int) *BSTNode {
    if root == nil { return nil }
    if root.Key == key { return root }
    if root.Key > key  { return BSTFloor(root.Left, key) }
    t := BSTFloor(root.Right, key)
    if t != nil { return t }
    return root
}

func BSTCeiling(root *BSTNode, key int) *BSTNode {
    if root == nil { return nil }
    if root.Key == key { return root }
    if root.Key < key  { return BSTCeiling(root.Right, key) }
    t := BSTCeiling(root.Left, key)
    if t != nil { return t }
    return root
}

// ─── RANGE QUERY ──────────────────────────────────────────────────
func BSTRange(root *BSTNode, lo, hi int) []int {
    var result []int
    var dfs func(*BSTNode)
    dfs = func(n *BSTNode) {
        if n == nil { return }
        if n.Key > lo  { dfs(n.Left) }
        if n.Key >= lo && n.Key <= hi { result = append(result, n.Key) }
        if n.Key < hi  { dfs(n.Right) }
    }
    dfs(root)
    return result
}

// ─── VALIDATION ───────────────────────────────────────────────────
func BSTIsValid(root *BSTNode, min, max float64) bool {
    if root == nil { return true }
    if float64(root.Key) <= min || float64(root.Key) >= max { return false }
    return BSTIsValid(root.Left, min, float64(root.Key)) &&
           BSTIsValid(root.Right, float64(root.Key), max)
}

func BSTInorder(root *BSTNode, result *[]int) {
    if root == nil { return }
    BSTInorder(root.Left, result)
    *result = append(*result, root.Key)
    BSTInorder(root.Right, result)
}

func main() {
    var root *BSTNode
    for _, k := range []int{5, 3, 7, 1, 4, 6, 8, 2} {
        root = BSTInsert(root, k)
    }

    var sorted []int
    BSTInorder(root, &sorted)
    fmt.Println("Sorted:", sorted)

    n4 := BSTSearch(root, 4)
    fmt.Printf("Successor of 4:   %d\n", BSTSuccessor(n4).Key)
    fmt.Printf("Predecessor of 4: %d\n", BSTPredecessor(n4).Key)
    fmt.Printf("Floor(4):   %d\n", BSTFloor(root, 4).Key)
    fmt.Printf("Ceiling(5): %d\n", BSTCeiling(root, 5).Key)
    fmt.Printf("Range [3,7]: %v\n", BSTRange(root, 3, 7))

    root = BSTDelete(root, 5)
    sorted = sorted[:0]
    BSTInorder(root, &sorted)
    fmt.Println("After deleting 5:", sorted)
    fmt.Println("BST valid:", BSTIsValid(root, math.Inf(-1), math.Inf(1)))
}
```

---

### Rust Implementation — BST

```rust
// In Rust, BST with parent pointers requires Rc<RefCell<T>>.
// Here we implement a clean recursive BST without parent pointers
// (parent-pointer version adds significant complexity).

use std::cmp::Ordering;

#[derive(Debug)]
pub struct BST {
    root: Link,
}

type Link = Option<Box<BSTNode>>;

#[derive(Debug)]
struct BSTNode {
    key:   i32,
    left:  Link,
    right: Link,
}

impl BSTNode {
    fn new(key: i32) -> Box<Self> {
        Box::new(BSTNode { key, left: None, right: None })
    }
}

impl BST {
    pub fn new() -> Self { BST { root: None } }

    // ─── INSERT ───────────────────────────────────────────────────
    pub fn insert(&mut self, key: i32) {
        self.root = insert_rec(self.root.take(), key);
    }

    // ─── SEARCH ───────────────────────────────────────────────────
    pub fn search(&self, key: i32) -> bool {
        search_rec(&self.root, key)
    }

    // ─── DELETE ───────────────────────────────────────────────────
    pub fn delete(&mut self, key: i32) {
        self.root = delete_rec(self.root.take(), key);
    }

    // ─── MIN / MAX ────────────────────────────────────────────────
    pub fn min(&self) -> Option<i32> {
        self.root.as_ref().map(|r| find_min(r))
    }

    pub fn max(&self) -> Option<i32> {
        self.root.as_ref().map(|r| find_max(r))
    }

    // ─── FLOOR / CEILING ──────────────────────────────────────────
    pub fn floor(&self, key: i32) -> Option<i32> {
        floor_rec(&self.root, key)
    }

    pub fn ceiling(&self, key: i32) -> Option<i32> {
        ceiling_rec(&self.root, key)
    }

    // ─── IN-ORDER ─────────────────────────────────────────────────
    pub fn inorder(&self) -> Vec<i32> {
        let mut out = Vec::new();
        inorder_rec(&self.root, &mut out);
        out
    }

    // ─── VALIDATION ───────────────────────────────────────────────
    pub fn is_valid(&self) -> bool {
        is_valid_rec(&self.root, i32::MIN, i32::MAX)
    }
}

fn insert_rec(node: Link, key: i32) -> Link {
    match node {
        None => Some(BSTNode::new(key)),
        Some(mut n) => {
            match key.cmp(&n.key) {
                Ordering::Less    => n.left  = insert_rec(n.left.take(),  key),
                Ordering::Greater => n.right = insert_rec(n.right.take(), key),
                Ordering::Equal   => {} // duplicate: no-op
            }
            Some(n)
        }
    }
}

fn search_rec(node: &Link, key: i32) -> bool {
    match node {
        None => false,
        Some(n) => match key.cmp(&n.key) {
            Ordering::Less    => search_rec(&n.left,  key),
            Ordering::Greater => search_rec(&n.right, key),
            Ordering::Equal   => true,
        }
    }
}

fn find_min(node: &BSTNode) -> i32 {
    match node.left {
        None => node.key,
        Some(ref l) => find_min(l),
    }
}

fn find_max(node: &BSTNode) -> i32 {
    match node.right {
        None => node.key,
        Some(ref r) => find_max(r),
    }
}

// Delete: returns the updated subtree link
fn delete_rec(node: Link, key: i32) -> Link {
    match node {
        None => None,
        Some(mut n) => {
            match key.cmp(&n.key) {
                Ordering::Less => {
                    n.left = delete_rec(n.left.take(), key);
                    Some(n)
                }
                Ordering::Greater => {
                    n.right = delete_rec(n.right.take(), key);
                    Some(n)
                }
                Ordering::Equal => {
                    // Found the node
                    match (n.left.take(), n.right.take()) {
                        (None, right) => right,     // 0 or 1 child
                        (left, None)  => left,
                        (left, right) => {
                            // Two children: replace with in-order successor
                            let successor_key = find_min(right.as_ref().unwrap());
                            let new_right = delete_rec(right, successor_key);
                            Some(Box::new(BSTNode {
                                key:   successor_key,
                                left:  left,
                                right: new_right,
                            }))
                        }
                    }
                }
            }
        }
    }
}

fn floor_rec(node: &Link, key: i32) -> Option<i32> {
    match node {
        None => None,
        Some(n) => {
            if n.key == key { return Some(key); }
            if n.key > key  { return floor_rec(&n.left, key); }
            // n.key < key
            floor_rec(&n.right, key).or(Some(n.key))
        }
    }
}

fn ceiling_rec(node: &Link, key: i32) -> Option<i32> {
    match node {
        None => None,
        Some(n) => {
            if n.key == key { return Some(key); }
            if n.key < key  { return ceiling_rec(&n.right, key); }
            ceiling_rec(&n.left, key).or(Some(n.key))
        }
    }
}

fn inorder_rec(node: &Link, out: &mut Vec<i32>) {
    if let Some(ref n) = node {
        inorder_rec(&n.left, out);
        out.push(n.key);
        inorder_rec(&n.right, out);
    }
}

fn is_valid_rec(node: &Link, min: i32, max: i32) -> bool {
    match node {
        None => true,
        Some(n) => {
            n.key > min && n.key < max
                && is_valid_rec(&n.left,  min,    n.key)
                && is_valid_rec(&n.right, n.key, max)
        }
    }
}

fn main() {
    let mut bst = BST::new();
    for k in [5, 3, 7, 1, 4, 6, 8, 2] {
        bst.insert(k);
    }

    println!("Sorted:     {:?}", bst.inorder());
    println!("Search 4:   {}", bst.search(4));
    println!("Min: {:?}, Max: {:?}", bst.min(), bst.max());
    println!("Floor(4):   {:?}", bst.floor(4));
    println!("Ceiling(5): {:?}", bst.ceiling(5));
    println!("Valid:      {}", bst.is_valid());

    bst.delete(5); // root with two children
    println!("After delete(5): {:?}", bst.inorder());
    println!("Still valid: {}", bst.is_valid());
}
```

---

## 4. AVL Tree

An AVL tree (Adelson-Velsky and Landis, 1962) is a **self-balancing BST** that enforces: for every node, `|height(left) - height(right)| ≤ 1`. This guarantees **O(log n) height** always, solving the O(n) worst case of naive BST.

### Balance Factor & Height Guarantee

Define: `bf(v) = height(v.left) - height(v.right)`

AVL property: `bf(v) ∈ {-1, 0, 1}` for every node `v`.

Theorem: An AVL tree with `n` nodes has height at most `1.44 * log₂(n+2) - 0.328`. In practice, height ≈ 1.44 log₂ n.

### The Four Rotations

When an insertion or deletion violates the AVL property, we restore it using **rotations**. Rotations are O(1) pointer manipulations that preserve BST ordering.

**Right Rotation (LL imbalance — left-heavy, left child also left-heavy):**
```
    z                   y
   / \                 / \
  y   T4    →        x   z
 / \                / \ / \
x   T3             T1 T2 T3 T4
```

**Left Rotation (RR imbalance — right-heavy, right child also right-heavy):**
```
  z                     y
 / \                   / \
T1   y       →        z   x
    / \              / \ / \
   T2   x           T1 T2 T3 T4
```

**Left-Right Rotation (LR imbalance — left-heavy, left child right-heavy):**
First left-rotate the left child, then right-rotate the node.

**Right-Left Rotation (RL imbalance — right-heavy, right child left-heavy):**
First right-rotate the right child, then left-rotate the node.

### When to Rotate After Insert

After inserting, walk up the ancestor chain updating heights. At the first ancestor `z` with `|bf| = 2`:

| Case | Condition | Fix |
|------|-----------|-----|
| LL | `bf(z) = 2`, `bf(z.left) ≥ 0` | Right rotate z |
| LR | `bf(z) = 2`, `bf(z.left) < 0` | Left rotate z.left, then right rotate z |
| RR | `bf(z) = -2`, `bf(z.right) ≤ 0` | Left rotate z |
| RL | `bf(z) = -2`, `bf(z.right) > 0` | Right rotate z.right, then left rotate z |

**Key insight for deletion:** After deletion, you may need to fix more than one ancestor (unlike insertion which fixes at most one). Keep walking up and fixing.

### Complexity

| Operation | Worst Case |
|-----------|-----------|
| Search    | O(log n)  |
| Insert    | O(log n)  |
| Delete    | O(log n)  |
| Rotations on insert | O(1) amortized |
| Rotations on delete | O(log n) worst  |
| Space | O(n) |

---

### C Implementation — AVL Tree

```c
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

typedef struct AVLNode {
    int key;
    int height;
    struct AVLNode *left;
    struct AVLNode *right;
} AVLNode;

/* ─── Height utilities ──────────────────────────────────────────── */
static int avl_height(AVLNode *n) { return n ? n->height : -1; }
static int avl_max(int a, int b)  { return a > b ? a : b; }
static int avl_bf(AVLNode *n)     { return n ? avl_height(n->left) - avl_height(n->right) : 0; }

static void avl_update_height(AVLNode *n) {
    if (n) n->height = 1 + avl_max(avl_height(n->left), avl_height(n->right));
}

/* ─── Rotations ─────────────────────────────────────────────────── */
/*
 * Right rotation around node y.
 * Returns the new root of this subtree (x).
 *      y                 x
 *     / \               / \
 *    x   C     →       A   y
 *   / \                   / \
 *  A   B                 B   C
 */
static AVLNode *rotate_right(AVLNode *y) {
    AVLNode *x  = y->left;
    AVLNode *B  = x->right;

    x->right = y;
    y->left  = B;

    avl_update_height(y);
    avl_update_height(x);
    return x;
}

/*
 * Left rotation around node x.
 * Returns the new root of this subtree (y).
 *  x                   y
 *   \                 / \
 *    y       →       x   C
 *   / \               \
 *  B   C               B
 */
static AVLNode *rotate_left(AVLNode *x) {
    AVLNode *y  = x->right;
    AVLNode *B  = y->left;

    y->left  = x;
    x->right = B;

    avl_update_height(x);
    avl_update_height(y);
    return y;
}

/* ─── Rebalance ─────────────────────────────────────────────────── */
static AVLNode *avl_rebalance(AVLNode *n) {
    avl_update_height(n);
    int bf = avl_bf(n);

    /* Left heavy */
    if (bf > 1) {
        if (avl_bf(n->left) < 0)           /* LR case */
            n->left = rotate_left(n->left);
        return rotate_right(n);            /* LL case */
    }

    /* Right heavy */
    if (bf < -1) {
        if (avl_bf(n->right) > 0)          /* RL case */
            n->right = rotate_right(n->right);
        return rotate_left(n);             /* RR case */
    }

    return n;  /* already balanced */
}

/* ─── INSERT ────────────────────────────────────────────────────── */
static AVLNode *avl_new(int key) {
    AVLNode *n  = malloc(sizeof(AVLNode));
    n->key      = key;
    n->height   = 0;
    n->left = n->right = NULL;
    return n;
}

AVLNode *avl_insert(AVLNode *root, int key) {
    if (!root) return avl_new(key);

    if      (key < root->key) root->left  = avl_insert(root->left,  key);
    else if (key > root->key) root->right = avl_insert(root->right, key);
    else return root;  /* duplicate */

    return avl_rebalance(root);
}

/* ─── SEARCH ────────────────────────────────────────────────────── */
AVLNode *avl_search(AVLNode *root, int key) {
    if (!root || root->key == key) return root;
    if (key < root->key) return avl_search(root->left,  key);
    return                      avl_search(root->right, key);
}

/* ─── DELETE ────────────────────────────────────────────────────── */
static AVLNode *avl_min_node(AVLNode *n) {
    while (n->left) n = n->left;
    return n;
}

AVLNode *avl_delete(AVLNode *root, int key) {
    if (!root) return NULL;

    if      (key < root->key) root->left  = avl_delete(root->left,  key);
    else if (key > root->key) root->right = avl_delete(root->right, key);
    else {
        /* Node found */
        if (!root->left || !root->right) {
            AVLNode *child = root->left ? root->left : root->right;
            free(root);
            return child;
        }
        /* Two children: replace with in-order successor */
        AVLNode *succ   = avl_min_node(root->right);
        root->key       = succ->key;
        root->right     = avl_delete(root->right, succ->key);
    }

    return avl_rebalance(root);
}

/* ─── TRAVERSAL & UTILS ─────────────────────────────────────────── */
void avl_inorder(AVLNode *root) {
    if (!root) return;
    avl_inorder(root->left);
    printf("%d(h=%d) ", root->key, root->height);
    avl_inorder(root->right);
}

void avl_free(AVLNode *root) {
    if (!root) return;
    avl_free(root->left);
    avl_free(root->right);
    free(root);
}

/* Verify AVL property recursively */
bool avl_verify(AVLNode *root) {
    if (!root) return true;
    int bf = avl_bf(root);
    if (bf < -1 || bf > 1) return false;
    return avl_verify(root->left) && avl_verify(root->right);
}

int main(void) {
    AVLNode *root = NULL;

    /* Insert in sorted order — would degenerate BST into O(n) linked list,
     * but AVL stays balanced with O(log n) height */
    int keys[] = {10, 20, 30, 40, 50, 25};
    for (int i = 0; i < 6; i++) {
        root = avl_insert(root, keys[i]);
        printf("Inserted %2d → height=%d, balanced=%s\n",
               keys[i], avl_height(root), avl_verify(root) ? "yes" : "NO");
    }

    printf("\nIn-order: "); avl_inorder(root); printf("\n");
    printf("AVL valid: %s\n", avl_verify(root) ? "yes" : "no");

    root = avl_delete(root, 40);
    printf("After delete(40): "); avl_inorder(root); printf("\n");
    printf("AVL valid: %s\n", avl_verify(root) ? "yes" : "no");

    avl_free(root);
    return 0;
}
```

---

### Go Implementation — AVL Tree

```go
package main

import "fmt"

type AVLNode struct {
    Key    int
    Height int
    Left   *AVLNode
    Right  *AVLNode
}

func avlHeight(n *AVLNode) int {
    if n == nil { return -1 }
    return n.Height
}

func avlBF(n *AVLNode) int {
    if n == nil { return 0 }
    return avlHeight(n.Left) - avlHeight(n.Right)
}

func avlUpdateHeight(n *AVLNode) {
    if n == nil { return }
    lh, rh := avlHeight(n.Left), avlHeight(n.Right)
    if lh > rh { n.Height = lh + 1 } else { n.Height = rh + 1 }
}

// ─── Rotations ────────────────────────────────────────────────────
func rotateRight(y *AVLNode) *AVLNode {
    x, B := y.Left, y.Left.Right
    x.Right = y
    y.Left  = B
    avlUpdateHeight(y)
    avlUpdateHeight(x)
    return x
}

func rotateLeft(x *AVLNode) *AVLNode {
    y, B := x.Right, x.Right.Left
    y.Left  = x
    x.Right = B
    avlUpdateHeight(x)
    avlUpdateHeight(y)
    return y
}

func avlRebalance(n *AVLNode) *AVLNode {
    avlUpdateHeight(n)
    bf := avlBF(n)
    if bf > 1 {
        if avlBF(n.Left) < 0 { n.Left = rotateLeft(n.Left) }
        return rotateRight(n)
    }
    if bf < -1 {
        if avlBF(n.Right) > 0 { n.Right = rotateRight(n.Right) }
        return rotateLeft(n)
    }
    return n
}

// ─── INSERT ───────────────────────────────────────────────────────
func AVLInsert(root *AVLNode, key int) *AVLNode {
    if root == nil { return &AVLNode{Key: key} }
    if key < root.Key      { root.Left  = AVLInsert(root.Left,  key) }
    else if key > root.Key { root.Right = AVLInsert(root.Right, key) }
    else                   { return root } // duplicate
    return avlRebalance(root)
}

// ─── DELETE ───────────────────────────────────────────────────────
func avlMinNode(n *AVLNode) *AVLNode {
    for n.Left != nil { n = n.Left }
    return n
}

func AVLDelete(root *AVLNode, key int) *AVLNode {
    if root == nil { return nil }
    if key < root.Key {
        root.Left = AVLDelete(root.Left, key)
    } else if key > root.Key {
        root.Right = AVLDelete(root.Right, key)
    } else {
        if root.Left == nil  { return root.Right }
        if root.Right == nil { return root.Left  }
        succ := avlMinNode(root.Right)
        root.Key   = succ.Key
        root.Right = AVLDelete(root.Right, succ.Key)
    }
    return avlRebalance(root)
}

// ─── SEARCH ───────────────────────────────────────────────────────
func AVLSearch(root *AVLNode, key int) *AVLNode {
    if root == nil || root.Key == key { return root }
    if key < root.Key { return AVLSearch(root.Left, key) }
    return AVLSearch(root.Right, key)
}

func AVLInorder(root *AVLNode, out *[]int) {
    if root == nil { return }
    AVLInorder(root.Left, out)
    *out = append(*out, root.Key)
    AVLInorder(root.Right, out)
}

func AVLVerify(root *AVLNode) bool {
    if root == nil { return true }
    bf := avlBF(root)
    if bf < -1 || bf > 1 { return false }
    return AVLVerify(root.Left) && AVLVerify(root.Right)
}

func main() {
    var root *AVLNode
    // Insert sorted sequence (stress-tests balancing)
    for _, k := range []int{10, 20, 30, 40, 50, 25} {
        root = AVLInsert(root, k)
        fmt.Printf("Inserted %2d → height=%d balanced=%v\n", k, avlHeight(root), AVLVerify(root))
    }
    var sorted []int
    AVLInorder(root, &sorted)
    fmt.Println("In-order:", sorted)
    root = AVLDelete(root, 40)
    sorted = sorted[:0]
    AVLInorder(root, &sorted)
    fmt.Println("After delete(40):", sorted, "valid:", AVLVerify(root))
}
```

---

### Rust Implementation — AVL Tree

```rust
#[derive(Debug)]
struct AVLNode {
    key:    i32,
    height: i32,
    left:   AVLLink,
    right:  AVLLink,
}

type AVLLink = Option<Box<AVLNode>>;

fn height(link: &AVLLink) -> i32 {
    link.as_ref().map_or(-1, |n| n.height)
}

fn bf(link: &AVLLink) -> i32 {
    link.as_ref().map_or(0, |n| height(&n.left) - height(&n.right))
}

fn update_height(node: &mut AVLNode) {
    node.height = 1 + height(&node.left).max(height(&node.right));
}

fn new_node(key: i32) -> Box<AVLNode> {
    Box::new(AVLNode { key, height: 0, left: None, right: None })
}

// ─── Rotations ────────────────────────────────────────────────────
fn rotate_right(mut y: Box<AVLNode>) -> Box<AVLNode> {
    let mut x = y.left.take().expect("rotate_right: no left child");
    y.left = x.right.take();
    update_height(&mut y);
    x.right = Some(y);
    update_height(&mut x);
    x
}

fn rotate_left(mut x: Box<AVLNode>) -> Box<AVLNode> {
    let mut y = x.right.take().expect("rotate_left: no right child");
    x.right = y.left.take();
    update_height(&mut x);
    y.left = Some(x);
    update_height(&mut y);
    y
}

fn rebalance(mut node: Box<AVLNode>) -> Box<AVLNode> {
    update_height(&mut node);
    let b = height(&node.left) - height(&node.right);

    if b > 1 {
        // Left heavy
        if bf(&node.left) < 0 {
            // LR case: left-rotate the left child first
            node.left = Some(rotate_left(node.left.take().unwrap()));
        }
        return rotate_right(node);
    }
    if b < -1 {
        // Right heavy
        if bf(&node.right) > 0 {
            // RL case: right-rotate the right child first
            node.right = Some(rotate_right(node.right.take().unwrap()));
        }
        return rotate_left(node);
    }
    node
}

// ─── INSERT ───────────────────────────────────────────────────────
fn avl_insert(link: AVLLink, key: i32) -> Box<AVLNode> {
    match link {
        None => new_node(key),
        Some(mut node) => {
            use std::cmp::Ordering::*;
            match key.cmp(&node.key) {
                Less    => node.left  = Some(avl_insert(node.left.take(),  key)),
                Greater => node.right = Some(avl_insert(node.right.take(), key)),
                Equal   => return node,
            }
            rebalance(node)
        }
    }
}

// ─── DELETE ───────────────────────────────────────────────────────
fn avl_min_key(node: &AVLNode) -> i32 {
    match node.left {
        None => node.key,
        Some(ref l) => avl_min_key(l),
    }
}

fn avl_delete(link: AVLLink, key: i32) -> AVLLink {
    let mut node = link?;
    use std::cmp::Ordering::*;
    match key.cmp(&node.key) {
        Less    => { node.left  = avl_delete(node.left.take(),  key); }
        Greater => { node.right = avl_delete(node.right.take(), key); }
        Equal   => {
            match (node.left.take(), node.right.take()) {
                (None,  right) => return right,
                (left,  None)  => return left,
                (left, right)  => {
                    let succ_key = avl_min_key(right.as_ref().unwrap());
                    node.right = avl_delete(right, succ_key);
                    node.left  = left;
                    node.key   = succ_key;
                }
            }
        }
    }
    Some(rebalance(node))
}

fn avl_inorder(link: &AVLLink, out: &mut Vec<i32>) {
    if let Some(ref n) = link {
        avl_inorder(&n.left, out);
        out.push(n.key);
        avl_inorder(&n.right, out);
    }
}

fn avl_verify(link: &AVLLink) -> bool {
    if let Some(ref n) = link {
        let b = height(&n.left) - height(&n.right);
        if b.abs() > 1 { return false; }
        return avl_verify(&n.left) && avl_verify(&n.right);
    }
    true
}

fn main() {
    let mut root: AVLLink = None;
    for k in [10, 20, 30, 40, 50, 25] {
        root = Some(avl_insert(root.take(), k));
        println!("Inserted {:2} → height={} valid={}", k,
            height(&root), avl_verify(&root));
    }
    let mut sorted = Vec::new();
    avl_inorder(&root, &mut sorted);
    println!("Sorted: {:?}", sorted);

    root = avl_delete(root, 40);
    sorted.clear();
    avl_inorder(&root, &mut sorted);
    println!("After delete(40): {:?}", sorted);
}
```

---

## 5. Red-Black Tree

A Red-Black Tree is a **self-balancing BST** that maintains balance through color constraints. Every node is colored Red or Black, and the following invariants are preserved:

### The Five Red-Black Invariants

1. **Every node is Red or Black.**
2. **The root is Black.**
3. **Every leaf (NIL sentinel) is Black.**
4. **Red nodes have Black children** (no two consecutive reds).
5. **For every node, all paths to descendant leaves have the same number of Black nodes** (the "black height" is uniform).

### Why These Invariants Work

From invariants 4 & 5: the longest path (alternating R-B-R-B...) is at most twice the shortest path (all Black). This gives height ≤ 2 log₂(n+1), ensuring O(log n) operations.

### RB vs AVL: When to Choose

| Aspect | AVL | Red-Black |
|--------|-----|-----------|
| Height bound | ~1.44 log n | ~2 log n |
| Lookups | Faster (shorter tree) | Slightly slower |
| Inserts | More rotations | Fewer rotations (≤2) |
| Deletes | More rotations | Fewer rotations (≤3) |
| Implementation | Simpler | More complex |
| Used in | Databases, filesystem indexes | Linux kernel, `std::map` (C++), `TreeMap` (Java) |

**Rule of thumb:** If read-heavy → AVL. If write-heavy → Red-Black.

### Recoloring and Rotations

**After Insert:** The new node is Red. If its parent is also Red (violating invariant 4), we fix by:
- **Uncle is Red (Recolor case):** Recolor parent and uncle Black, grandparent Red. Move up.
- **Uncle is Black (Rotation cases):** One or two rotations + recoloring to restructure.

**After Delete:** More complex. We track a "double-black" node and propagate it upward using recoloring and rotations.

---

### C Implementation — Red-Black Tree (Simplified, Production-Quality)

```c
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

#define RED   0
#define BLACK 1

typedef struct RBNode {
    int key;
    int color;
    struct RBNode *left, *right, *parent;
} RBNode;

typedef struct RBTree {
    RBNode *root;
    RBNode *nil;   /* sentinel NIL node (shared black leaf) */
} RBTree;

/* ─── Create / Init ─────────────────────────────────────────────── */
RBTree *rb_create() {
    RBTree *t    = malloc(sizeof(RBTree));
    t->nil       = malloc(sizeof(RBNode));
    t->nil->color  = BLACK;
    t->nil->left   = t->nil->right = t->nil->parent = t->nil;
    t->nil->key    = 0;
    t->root        = t->nil;
    return t;
}

/* ─── Rotations ─────────────────────────────────────────────────── */
static void left_rotate(RBTree *t, RBNode *x) {
    RBNode *y   = x->right;
    x->right    = y->left;
    if (y->left != t->nil) y->left->parent = x;
    y->parent   = x->parent;
    if (x->parent == t->nil)     t->root     = y;
    else if (x == x->parent->left) x->parent->left  = y;
    else                           x->parent->right = y;
    y->left     = x;
    x->parent   = y;
}

static void right_rotate(RBTree *t, RBNode *y) {
    RBNode *x   = y->left;
    y->left     = x->right;
    if (x->right != t->nil) x->right->parent = y;
    x->parent   = y->parent;
    if (y->parent == t->nil)      t->root     = x;
    else if (y == y->parent->right) y->parent->right = x;
    else                            y->parent->left  = x;
    x->right    = y;
    y->parent   = x;
}

/* ─── Insert Fixup ──────────────────────────────────────────────── */
static void rb_insert_fixup(RBTree *t, RBNode *z) {
    while (z->parent->color == RED) {
        if (z->parent == z->parent->parent->left) {
            /* Parent is left child */
            RBNode *y = z->parent->parent->right;  /* uncle */
            if (y->color == RED) {
                /* Case 1: Uncle is Red — recolor */
                z->parent->color          = BLACK;
                y->color                  = BLACK;
                z->parent->parent->color  = RED;
                z = z->parent->parent;
            } else {
                if (z == z->parent->right) {
                    /* Case 2: z is right child — left rotate to normalize */
                    z = z->parent;
                    left_rotate(t, z);
                }
                /* Case 3: z is left child — right rotate grandparent */
                z->parent->color         = BLACK;
                z->parent->parent->color = RED;
                right_rotate(t, z->parent->parent);
            }
        } else {
            /* Mirror: parent is right child */
            RBNode *y = z->parent->parent->left;
            if (y->color == RED) {
                z->parent->color         = BLACK;
                y->color                 = BLACK;
                z->parent->parent->color = RED;
                z = z->parent->parent;
            } else {
                if (z == z->parent->left) {
                    z = z->parent;
                    right_rotate(t, z);
                }
                z->parent->color         = BLACK;
                z->parent->parent->color = RED;
                left_rotate(t, z->parent->parent);
            }
        }
    }
    t->root->color = BLACK;
}

/* ─── INSERT ────────────────────────────────────────────────────── */
void rb_insert(RBTree *t, int key) {
    RBNode *z = malloc(sizeof(RBNode));
    z->key    = key;
    z->color  = RED;
    z->left   = z->right = z->parent = t->nil;

    RBNode *y = t->nil, *x = t->root;
    while (x != t->nil) {
        y = x;
        if      (z->key < x->key) x = x->left;
        else if (z->key > x->key) x = x->right;
        else { free(z); return; } /* duplicate */
    }
    z->parent = y;
    if      (y == t->nil)      t->root   = z;
    else if (z->key < y->key)  y->left   = z;
    else                       y->right  = z;

    rb_insert_fixup(t, z);
}

/* ─── Transplant helper ─────────────────────────────────────────── */
static void rb_transplant(RBTree *t, RBNode *u, RBNode *v) {
    if      (u->parent == t->nil)      t->root      = v;
    else if (u == u->parent->left)     u->parent->left  = v;
    else                               u->parent->right = v;
    v->parent = u->parent;
}

/* ─── Delete Fixup ──────────────────────────────────────────────── */
static void rb_delete_fixup(RBTree *t, RBNode *x) {
    while (x != t->root && x->color == BLACK) {
        if (x == x->parent->left) {
            RBNode *w = x->parent->right;
            if (w->color == RED) {                       /* Case 1 */
                w->color           = BLACK;
                x->parent->color   = RED;
                left_rotate(t, x->parent);
                w = x->parent->right;
            }
            if (w->left->color == BLACK && w->right->color == BLACK) {
                w->color = RED;                          /* Case 2 */
                x = x->parent;
            } else {
                if (w->right->color == BLACK) {          /* Case 3 */
                    w->left->color = BLACK;
                    w->color       = RED;
                    right_rotate(t, w);
                    w = x->parent->right;
                }
                w->color           = x->parent->color;  /* Case 4 */
                x->parent->color   = BLACK;
                w->right->color    = BLACK;
                left_rotate(t, x->parent);
                x = t->root;
            }
        } else {
            /* Mirror */
            RBNode *w = x->parent->left;
            if (w->color == RED) {
                w->color         = BLACK;
                x->parent->color = RED;
                right_rotate(t, x->parent);
                w = x->parent->left;
            }
            if (w->right->color == BLACK && w->left->color == BLACK) {
                w->color = RED;
                x = x->parent;
            } else {
                if (w->left->color == BLACK) {
                    w->right->color = BLACK;
                    w->color        = RED;
                    left_rotate(t, w);
                    w = x->parent->left;
                }
                w->color         = x->parent->color;
                x->parent->color = BLACK;
                w->left->color   = BLACK;
                right_rotate(t, x->parent);
                x = t->root;
            }
        }
    }
    x->color = BLACK;
}

/* ─── DELETE ────────────────────────────────────────────────────── */
void rb_delete(RBTree *t, int key) {
    RBNode *z = t->root;
    while (z != t->nil) {
        if      (key < z->key) z = z->left;
        else if (key > z->key) z = z->right;
        else break;
    }
    if (z == t->nil) return;

    RBNode *y = z, *x;
    int y_orig_color = y->color;

    if (z->left == t->nil) {
        x = z->right;
        rb_transplant(t, z, z->right);
    } else if (z->right == t->nil) {
        x = z->left;
        rb_transplant(t, z, z->left);
    } else {
        /* Find successor (min of right subtree) */
        y = z->right;
        while (y->left != t->nil) y = y->left;
        y_orig_color = y->color;
        x = y->right;
        if (y->parent == z) {
            x->parent = y;
        } else {
            rb_transplant(t, y, y->right);
            y->right = z->right;
            y->right->parent = y;
        }
        rb_transplant(t, z, y);
        y->left = z->left;
        y->left->parent = y;
        y->color = z->color;
    }
    free(z);
    if (y_orig_color == BLACK) rb_delete_fixup(t, x);
}

/* ─── SEARCH ────────────────────────────────────────────────────── */
RBNode *rb_search(RBTree *t, int key) {
    RBNode *curr = t->root;
    while (curr != t->nil) {
        if      (key < curr->key) curr = curr->left;
        else if (key > curr->key) curr = curr->right;
        else return curr;
    }
    return NULL;
}

/* ─── In-order traversal ────────────────────────────────────────── */
void rb_inorder(RBTree *t, RBNode *x) {
    if (x == t->nil) return;
    rb_inorder(t, x->left);
    printf("%d(%s) ", x->key, x->color == RED ? "R" : "B");
    rb_inorder(t, x->right);
}

/* ─── Black-height verification ─────────────────────────────────── */
int rb_black_height(RBTree *t, RBNode *x) {
    if (x == t->nil) return 0;
    int left_bh  = rb_black_height(t, x->left);
    int right_bh = rb_black_height(t, x->right);
    if (left_bh == -1 || right_bh == -1 || left_bh != right_bh) return -1;
    return left_bh + (x->color == BLACK ? 1 : 0);
}

void rb_free_nodes(RBTree *t, RBNode *x) {
    if (x == t->nil) return;
    rb_free_nodes(t, x->left);
    rb_free_nodes(t, x->right);
    free(x);
}

void rb_free(RBTree *t) {
    rb_free_nodes(t, t->root);
    free(t->nil);
    free(t);
}

int main(void) {
    RBTree *t = rb_create();
    int keys[] = {7, 3, 18, 10, 22, 8, 11, 26, 2, 6, 13};
    for (int i = 0; i < 11; i++) rb_insert(t, keys[i]);

    printf("In-order: "); rb_inorder(t, t->root); printf("\n");
    printf("Black height from root: %d\n", rb_black_height(t, t->root));

    rb_delete(t, 18);
    printf("After delete(18): "); rb_inorder(t, t->root); printf("\n");
    printf("Black height: %d\n", rb_black_height(t, t->root));

    rb_free(t);
    return 0;
}
```

---

### Go Implementation — Red-Black Tree

```go
package main

import "fmt"

const (
    Red   = 0
    Black = 1
)

type RBNode struct {
    Key    int
    Color  int
    Left   *RBNode
    Right  *RBNode
    Parent *RBNode
}

type RBTree struct {
    Root *RBNode
    Nil  *RBNode // sentinel
}

func NewRBTree() *RBTree {
    sentinel := &RBNode{Color: Black}
    sentinel.Left = sentinel
    sentinel.Right = sentinel
    sentinel.Parent = sentinel
    return &RBTree{Root: sentinel, Nil: sentinel}
}

func (t *RBTree) leftRotate(x *RBNode) {
    y := x.Right
    x.Right = y.Left
    if y.Left != t.Nil { y.Left.Parent = x }
    y.Parent = x.Parent
    if x.Parent == t.Nil         { t.Root = y    }
    else if x == x.Parent.Left   { x.Parent.Left = y  }
    else                         { x.Parent.Right = y }
    y.Left = x
    x.Parent = y
}

func (t *RBTree) rightRotate(y *RBNode) {
    x := y.Left
    y.Left = x.Right
    if x.Right != t.Nil { x.Right.Parent = y }
    x.Parent = y.Parent
    if y.Parent == t.Nil         { t.Root = x    }
    else if y == y.Parent.Right  { y.Parent.Right = x }
    else                         { y.Parent.Left  = x }
    x.Right = y
    y.Parent = x
}

func (t *RBTree) insertFixup(z *RBNode) {
    for z.Parent.Color == Red {
        if z.Parent == z.Parent.Parent.Left {
            y := z.Parent.Parent.Right
            if y.Color == Red {
                z.Parent.Color = Black
                y.Color = Black
                z.Parent.Parent.Color = Red
                z = z.Parent.Parent
            } else {
                if z == z.Parent.Right {
                    z = z.Parent
                    t.leftRotate(z)
                }
                z.Parent.Color = Black
                z.Parent.Parent.Color = Red
                t.rightRotate(z.Parent.Parent)
            }
        } else {
            y := z.Parent.Parent.Left
            if y.Color == Red {
                z.Parent.Color = Black
                y.Color = Black
                z.Parent.Parent.Color = Red
                z = z.Parent.Parent
            } else {
                if z == z.Parent.Left {
                    z = z.Parent
                    t.rightRotate(z)
                }
                z.Parent.Color = Black
                z.Parent.Parent.Color = Red
                t.leftRotate(z.Parent.Parent)
            }
        }
    }
    t.Root.Color = Black
}

func (t *RBTree) Insert(key int) {
    z := &RBNode{Key: key, Color: Red,
        Left: t.Nil, Right: t.Nil, Parent: t.Nil}

    y, x := t.Nil, t.Root
    for x != t.Nil {
        y = x
        if z.Key < x.Key      { x = x.Left  }
        else if z.Key > x.Key { x = x.Right }
        else                  { return } // duplicate
    }
    z.Parent = y
    if y == t.Nil               { t.Root = z }
    else if z.Key < y.Key       { y.Left = z }
    else                        { y.Right = z }
    t.insertFixup(z)
}

func (t *RBTree) transplant(u, v *RBNode) {
    if u.Parent == t.Nil           { t.Root = v }
    else if u == u.Parent.Left     { u.Parent.Left = v }
    else                           { u.Parent.Right = v }
    v.Parent = u.Parent
}

func (t *RBTree) deleteFixup(x *RBNode) {
    for x != t.Root && x.Color == Black {
        if x == x.Parent.Left {
            w := x.Parent.Right
            if w.Color == Red {
                w.Color = Black; x.Parent.Color = Red
                t.leftRotate(x.Parent); w = x.Parent.Right
            }
            if w.Left.Color == Black && w.Right.Color == Black {
                w.Color = Red; x = x.Parent
            } else {
                if w.Right.Color == Black {
                    w.Left.Color = Black; w.Color = Red
                    t.rightRotate(w); w = x.Parent.Right
                }
                w.Color = x.Parent.Color; x.Parent.Color = Black
                w.Right.Color = Black; t.leftRotate(x.Parent); x = t.Root
            }
        } else {
            w := x.Parent.Left
            if w.Color == Red {
                w.Color = Black; x.Parent.Color = Red
                t.rightRotate(x.Parent); w = x.Parent.Left
            }
            if w.Right.Color == Black && w.Left.Color == Black {
                w.Color = Red; x = x.Parent
            } else {
                if w.Left.Color == Black {
                    w.Right.Color = Black; w.Color = Red
                    t.leftRotate(w); w = x.Parent.Left
                }
                w.Color = x.Parent.Color; x.Parent.Color = Black
                w.Left.Color = Black; t.rightRotate(x.Parent); x = t.Root
            }
        }
    }
    x.Color = Black
}

func (t *RBTree) Delete(key int) {
    z := t.Root
    for z != t.Nil {
        if key < z.Key      { z = z.Left  }
        else if key > z.Key { z = z.Right }
        else                { break       }
    }
    if z == t.Nil { return }

    y, x := z, t.Nil
    yOrigColor := y.Color

    if z.Left == t.Nil {
        x = z.Right; t.transplant(z, z.Right)
    } else if z.Right == t.Nil {
        x = z.Left; t.transplant(z, z.Left)
    } else {
        y = z.Right
        for y.Left != t.Nil { y = y.Left }
        yOrigColor = y.Color; x = y.Right
        if y.Parent == z {
            x.Parent = y
        } else {
            t.transplant(y, y.Right)
            y.Right = z.Right; y.Right.Parent = y
        }
        t.transplant(z, y)
        y.Left = z.Left; y.Left.Parent = y; y.Color = z.Color
    }
    if yOrigColor == Black { t.deleteFixup(x) }
}

func (t *RBTree) Search(key int) *RBNode {
    n := t.Root
    for n != t.Nil {
        if key < n.Key      { n = n.Left  }
        else if key > n.Key { n = n.Right }
        else                { return n    }
    }
    return nil
}

func (t *RBTree) Inorder(n *RBNode, out *[]int) {
    if n == t.Nil { return }
    t.Inorder(n.Left, out)
    *out = append(*out, n.Key)
    t.Inorder(n.Right, out)
}

func main() {
    t := NewRBTree()
    for _, k := range []int{7, 3, 18, 10, 22, 8, 11, 26, 2, 6, 13} {
        t.Insert(k)
    }
    var sorted []int
    t.Inorder(t.Root, &sorted)
    fmt.Println("In-order:", sorted)

    t.Delete(18)
    sorted = sorted[:0]
    t.Inorder(t.Root, &sorted)
    fmt.Println("After delete(18):", sorted)
}
```

---

## 6. B-Tree & B+ Tree

### What Is a B-Tree?

A B-tree of order `m` is a **self-balancing multi-way search tree** where:
- Every node has at most `m` children.
- Every internal node (except root) has at least ⌈m/2⌉ children.
- The root has at least 2 children (if non-leaf).
- All leaves are at the same depth.
- A node with `k` children contains exactly `k-1` keys.

B-trees are designed for **disk-based storage** where block I/O dominates. A B-tree of order 1000 can store millions of records with height ≤ 3, meaning at most 3 disk reads per lookup.

### B+ Tree vs B-Tree

| Feature | B-Tree | B+ Tree |
|---------|--------|---------|
| Data storage | In all nodes | Only in leaf nodes |
| Internal nodes | Store keys + data | Store keys only (routing) |
| Leaf links | Not linked | Leaves form linked list |
| Range queries | Slow (need traversal) | Fast (scan leaves) |
| Space | Less efficient | More efficient (more keys per internal node) |
| Used in | Older filesystems | Databases (MySQL InnoDB, PostgreSQL), modern filesystems |

In a **B+ tree**, internal nodes act purely as routing nodes. All actual data (or pointers to records) live in the leaves. Leaves are linked together, making range scans O(k) where k is the result count.

### Key Operations

**Search:** Start at root. Binary search within the node. Follow child pointer. O(log_m n) disk reads.

**Insert:**
1. Search for the leaf where key belongs.
2. Insert into leaf.
3. If leaf overflows (has m keys), **split**: push median key up to parent.
4. Split may propagate upward; if root splits, a new root is created (tree grows upward, height increases by 1).

**Delete:**
1. Find the key.
2. If in a leaf, remove it.
3. If underflow (< ⌈m/2⌉ - 1 keys): try to **borrow** from a sibling (rotate via parent). If sibling also minimal: **merge** node + sibling + parent separator key into one node.
4. Merging may propagate upward.

---

### C Implementation — B-Tree (Order t, minimum degree)

```c
/*
 * B-Tree using the CLRS (Cormen) minimum-degree convention.
 * t = minimum degree:
 *   - Every node has at least t-1 keys (except root)
 *   - Every node has at most 2t-1 keys
 *   - Non-root internal nodes have at least t children
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>

#define T 3   /* minimum degree — change to 500+ for production */
#define MAX_KEYS (2*T - 1)
#define MIN_KEYS (T - 1)

typedef struct BTreeNode {
    int keys[MAX_KEYS];
    struct BTreeNode *children[MAX_KEYS + 1];
    int n;        /* current number of keys */
    bool leaf;
} BTreeNode;

/* ─── Allocation ────────────────────────────────────────────────── */
BTreeNode *bt_alloc(bool leaf) {
    BTreeNode *n = calloc(1, sizeof(BTreeNode));
    n->leaf = leaf;
    return n;
}

/* ─── SEARCH ────────────────────────────────────────────────────── */
typedef struct { BTreeNode *node; int idx; } BSearchResult;

BSearchResult btree_search(BTreeNode *x, int k) {
    int i = 0;
    /* Linear scan — use binary search for large T */
    while (i < x->n && k > x->keys[i]) i++;
    if (i < x->n && k == x->keys[i]) return (BSearchResult){x, i};
    if (x->leaf) return (BSearchResult){NULL, -1};
    return btree_search(x->children[i], k);
}

/* ─── SPLIT CHILD ───────────────────────────────────────────────── */
/*
 * Split child x->children[i] (which must be full: 2t-1 keys)
 * Promote median to x. x must not be full.
 */
static void btree_split_child(BTreeNode *x, int i) {
    BTreeNode *y = x->children[i];          /* full child */
    BTreeNode *z = bt_alloc(y->leaf);        /* new node */
    z->n = T - 1;

    /* Copy right half of y's keys to z */
    for (int j = 0; j < T-1; j++)
        z->keys[j] = y->keys[j + T];

    /* Copy right half of y's children to z (if internal) */
    if (!y->leaf) {
        for (int j = 0; j < T; j++)
            z->children[j] = y->children[j + T];
    }

    y->n = T - 1;  /* y keeps left half */

    /* Shift x's children right to make room for z */
    for (int j = x->n; j >= i+1; j--)
        x->children[j+1] = x->children[j];
    x->children[i+1] = z;

    /* Shift x's keys right and insert median */
    for (int j = x->n - 1; j >= i; j--)
        x->keys[j+1] = x->keys[j];
    x->keys[i] = y->keys[T-1];  /* median */
    x->n++;
}

/* ─── INSERT NON-FULL ───────────────────────────────────────────── */
/*
 * Insert key k into subtree rooted at x, which is guaranteed non-full.
 */
static void btree_insert_nonfull(BTreeNode *x, int k) {
    int i = x->n - 1;

    if (x->leaf) {
        /* Shift keys right and insert */
        while (i >= 0 && k < x->keys[i]) {
            x->keys[i+1] = x->keys[i];
            i--;
        }
        x->keys[i+1] = k;
        x->n++;
    } else {
        /* Find child to descend into */
        while (i >= 0 && k < x->keys[i]) i--;
        i++;
        /* Split child if full (proactive: split before descent) */
        if (x->children[i]->n == MAX_KEYS) {
            btree_split_child(x, i);
            /* After split, x->keys[i] is the median.
             * Determine which half k belongs to. */
            if (k > x->keys[i]) i++;
        }
        btree_insert_nonfull(x->children[i], k);
    }
}

/* ─── INSERT ────────────────────────────────────────────────────── */
BTreeNode *btree_insert(BTreeNode *root, int k) {
    if (root->n == MAX_KEYS) {
        /* Root is full: grow tree upward */
        BTreeNode *s = bt_alloc(false);
        s->children[0] = root;
        s->n = 0;
        btree_split_child(s, 0);
        btree_insert_nonfull(s, k);
        return s;
    }
    btree_insert_nonfull(root, k);
    return root;
}

/* ─── DELETE (complete implementation) ─────────────────────────── */

/* Find predecessor key in subtree rooted at x */
static int btree_predecessor(BTreeNode *x) {
    while (!x->leaf) x = x->children[x->n];
    return x->keys[x->n - 1];
}

/* Find successor key */
static int btree_successor(BTreeNode *x) {
    while (!x->leaf) x = x->children[0];
    return x->keys[0];
}

/* Merge children[i] and children[i+1] around keys[i] */
static void btree_merge(BTreeNode *x, int i) {
    BTreeNode *y = x->children[i];
    BTreeNode *z = x->children[i+1];

    /* Put separator key into y */
    y->keys[T-1] = x->keys[i];

    /* Copy z's keys into y */
    for (int j = 0; j < z->n; j++)
        y->keys[T + j] = z->keys[j];

    /* Copy z's children into y (if internal) */
    if (!y->leaf) {
        for (int j = 0; j <= z->n; j++)
            y->children[T + j] = z->children[j];
    }

    y->n = 2*T - 1;

    /* Remove separator and z from x */
    for (int j = i+1; j < x->n; j++)
        x->keys[j-1] = x->keys[j];
    for (int j = i+2; j <= x->n; j++)
        x->children[j-1] = x->children[j];
    x->n--;

    free(z);
}

static void btree_delete_rec(BTreeNode *x, int k);

/* Ensure child[i] has at least T keys before descending */
static void btree_fill(BTreeNode *x, int i) {
    if (i > 0 && x->children[i-1]->n >= T) {
        /* Borrow from left sibling */
        BTreeNode *child = x->children[i];
        BTreeNode *sibling = x->children[i-1];

        /* Shift child's keys/children right */
        for (int j = child->n - 1; j >= 0; j--)
            child->keys[j+1] = child->keys[j];
        if (!child->leaf)
            for (int j = child->n; j >= 0; j--)
                child->children[j+1] = child->children[j];

        child->keys[0] = x->keys[i-1];
        if (!child->leaf)
            child->children[0] = sibling->children[sibling->n];
        x->keys[i-1] = sibling->keys[sibling->n - 1];
        child->n++;
        sibling->n--;

    } else if (i < x->n && x->children[i+1]->n >= T) {
        /* Borrow from right sibling */
        BTreeNode *child = x->children[i];
        BTreeNode *sibling = x->children[i+1];

        child->keys[child->n] = x->keys[i];
        if (!child->leaf)
            child->children[child->n + 1] = sibling->children[0];
        x->keys[i] = sibling->keys[0];

        for (int j = 1; j < sibling->n; j++)
            sibling->keys[j-1] = sibling->keys[j];
        if (!sibling->leaf)
            for (int j = 1; j <= sibling->n; j++)
                sibling->children[j-1] = sibling->children[j];
        child->n++;
        sibling->n--;

    } else {
        /* Merge */
        if (i < x->n)  btree_merge(x, i);
        else            btree_merge(x, i-1);
    }
}

static void btree_delete_rec(BTreeNode *x, int k) {
    int i = 0;
    while (i < x->n && k > x->keys[i]) i++;

    if (i < x->n && k == x->keys[i]) {
        /* Key found in this node */
        if (x->leaf) {
            /* Case 1: key in leaf — just remove */
            for (int j = i+1; j < x->n; j++)
                x->keys[j-1] = x->keys[j];
            x->n--;
        } else if (x->children[i]->n >= T) {
            /* Case 2a: left child has ≥ T keys → replace with predecessor */
            int pred = btree_predecessor(x->children[i]);
            x->keys[i] = pred;
            btree_delete_rec(x->children[i], pred);
        } else if (x->children[i+1]->n >= T) {
            /* Case 2b: right child has ≥ T keys → replace with successor */
            int succ = btree_successor(x->children[i+1]);
            x->keys[i] = succ;
            btree_delete_rec(x->children[i+1], succ);
        } else {
            /* Case 2c: both children have T-1 keys → merge */
            btree_merge(x, i);
            btree_delete_rec(x->children[i], k);
        }
    } else {
        /* Key not in this node */
        if (x->leaf) return;  /* not found */

        /* Case 3: key is in subtree rooted at children[i] */
        bool last = (i == x->n);
        if (x->children[i]->n == T-1)
            btree_fill(x, i);

        /* After fill, the child structure may have changed */
        if (last && i > x->n)
            btree_delete_rec(x->children[i-1], k);
        else
            btree_delete_rec(x->children[i], k);
    }
}

BTreeNode *btree_delete(BTreeNode *root, int k) {
    if (!root) return NULL;
    btree_delete_rec(root, k);
    /* If root has 0 keys and has a child, shrink tree */
    if (root->n == 0 && !root->leaf) {
        BTreeNode *tmp = root;
        root = root->children[0];
        free(tmp);
    }
    return root;
}

/* ─── TRAVERSAL ─────────────────────────────────────────────────── */
void btree_traverse(BTreeNode *root) {
    if (!root) return;
    for (int i = 0; i < root->n; i++) {
        if (!root->leaf) btree_traverse(root->children[i]);
        printf("%d ", root->keys[i]);
    }
    if (!root->leaf) btree_traverse(root->children[root->n]);
}

void btree_free(BTreeNode *root) {
    if (!root) return;
    if (!root->leaf)
        for (int i = 0; i <= root->n; i++)
            btree_free(root->children[i]);
    free(root);
}

int main(void) {
    BTreeNode *root = bt_alloc(true);

    int keys[] = {10, 20, 5, 6, 12, 30, 7, 17};
    for (int i = 0; i < 8; i++)
        root = btree_insert(root, keys[i]);

    printf("B-tree in-order: "); btree_traverse(root); printf("\n");

    BSearchResult r = btree_search(root, 12);
    printf("Search 12: %s\n", r.node ? "found" : "not found");

    root = btree_delete(root, 6);
    printf("After delete(6): "); btree_traverse(root); printf("\n");

    root = btree_delete(root, 13);
    printf("After delete(13=not found): "); btree_traverse(root); printf("\n");

    btree_free(root);
    return 0;
}
```

---

### Go Implementation — B-Tree

```go
package main

import "fmt"

const BT = 3 // minimum degree

type BTNode struct {
    Keys     [2*BT - 1]int
    Children [2*BT]*BTNode
    N        int
    Leaf     bool
}

func newBTNode(leaf bool) *BTNode { return &BTNode{Leaf: leaf} }

// ─── SEARCH ───────────────────────────────────────────────────────
func BTreeSearch(x *BTNode, k int) (*BTNode, int) {
    i := 0
    for i < x.N && k > x.Keys[i] { i++ }
    if i < x.N && k == x.Keys[i] { return x, i }
    if x.Leaf { return nil, -1 }
    return BTreeSearch(x.Children[i], k)
}

// ─── SPLIT CHILD ──────────────────────────────────────────────────
func splitChild(x *BTNode, i int) {
    y := x.Children[i]
    z := newBTNode(y.Leaf)
    z.N = BT - 1

    for j := 0; j < BT-1; j++ { z.Keys[j] = y.Keys[j+BT] }
    if !y.Leaf {
        for j := 0; j < BT; j++ { z.Children[j] = y.Children[j+BT] }
    }
    y.N = BT - 1

    for j := x.N; j >= i+1; j-- { x.Children[j+1] = x.Children[j] }
    x.Children[i+1] = z
    for j := x.N - 1; j >= i; j-- { x.Keys[j+1] = x.Keys[j] }
    x.Keys[i] = y.Keys[BT-1]
    x.N++
}

func insertNonFull(x *BTNode, k int) {
    i := x.N - 1
    if x.Leaf {
        for i >= 0 && k < x.Keys[i] {
            x.Keys[i+1] = x.Keys[i]
            i--
        }
        x.Keys[i+1] = k
        x.N++
    } else {
        for i >= 0 && k < x.Keys[i] { i-- }
        i++
        if x.Children[i].N == 2*BT-1 {
            splitChild(x, i)
            if k > x.Keys[i] { i++ }
        }
        insertNonFull(x.Children[i], k)
    }
}

// ─── INSERT ───────────────────────────────────────────────────────
func BTreeInsert(root *BTNode, k int) *BTNode {
    if root.N == 2*BT-1 {
        s := newBTNode(false)
        s.Children[0] = root
        splitChild(s, 0)
        insertNonFull(s, k)
        return s
    }
    insertNonFull(root, k)
    return root
}

// ─── TRAVERSE ─────────────────────────────────────────────────────
func BTreeTraverse(x *BTNode, out *[]int) {
    for i := 0; i < x.N; i++ {
        if !x.Leaf { BTreeTraverse(x.Children[i], out) }
        *out = append(*out, x.Keys[i])
    }
    if !x.Leaf { BTreeTraverse(x.Children[x.N], out) }
}

func main() {
    root := newBTNode(true)
    for _, k := range []int{10, 20, 5, 6, 12, 30, 7, 17} {
        root = BTreeInsert(root, k)
    }
    var sorted []int
    BTreeTraverse(root, &sorted)
    fmt.Println("B-tree in-order:", sorted)

    node, idx := BTreeSearch(root, 12)
    fmt.Printf("Search 12: node=%v, idx=%d\n", node != nil, idx)
}
```

---

### Rust Implementation — B-Tree

```rust
// Rust's standard library has a BTreeMap/BTreeSet — production-quality.
// Below is a didactic implementation for understanding internals.

const T: usize = 3; // minimum degree

#[derive(Debug)]
struct BTreeNode {
    keys:     Vec<i32>,
    children: Vec<Box<BTreeNode>>,
    leaf:     bool,
}

impl BTreeNode {
    fn new(leaf: bool) -> Self {
        BTreeNode { keys: Vec::new(), children: Vec::new(), leaf }
    }

    fn is_full(&self) -> bool { self.keys.len() == 2 * T - 1 }

    // Linear search — use binary_search for production
    fn find_key(&self, k: i32) -> usize {
        self.keys.partition_point(|&x| x < k)
    }

    // ─── INSERT NON-FULL ──────────────────────────────────────────
    fn insert_non_full(&mut self, k: i32) {
        let mut i = self.find_key(k);
        if self.leaf {
            self.keys.insert(i, k);
        } else {
            if self.children[i].is_full() {
                self.split_child(i);
                if k > self.keys[i] { i += 1; }
            }
            self.children[i].insert_non_full(k);
        }
    }

    // ─── SPLIT CHILD ──────────────────────────────────────────────
    fn split_child(&mut self, i: usize) {
        let median_key = self.children[i].keys[T - 1];
        
        // Extract right half from child[i] into new node z
        let right_keys = self.children[i].keys.split_off(T);
        self.children[i].keys.pop(); // remove median
        
        let right_children = if !self.children[i].leaf {
            self.children[i].children.split_off(T)
        } else {
            Vec::new()
        };

        let z = Box::new(BTreeNode {
            keys:     right_keys,
            children: right_children,
            leaf:     self.children[i].leaf,
        });

        self.keys.insert(i, median_key);
        self.children.insert(i + 1, z);
    }

    // ─── SEARCH ───────────────────────────────────────────────────
    fn search(&self, k: i32) -> bool {
        let i = self.find_key(k);
        if i < self.keys.len() && self.keys[i] == k { return true; }
        if self.leaf { return false; }
        self.children[i].search(k)
    }

    // ─── TRAVERSE ─────────────────────────────────────────────────
    fn traverse(&self, out: &mut Vec<i32>) {
        for i in 0..self.keys.len() {
            if !self.leaf { self.children[i].traverse(out); }
            out.push(self.keys[i]);
        }
        if !self.leaf { self.children[self.keys.len()].traverse(out); }
    }
}

pub struct BTree { root: BTreeNode }

impl BTree {
    pub fn new() -> Self { BTree { root: BTreeNode::new(true) } }

    pub fn insert(&mut self, k: i32) {
        if self.root.is_full() {
            let old_root = std::mem::replace(&mut self.root, BTreeNode::new(false));
            self.root.children.push(Box::new(old_root));
            self.root.split_child(0);
        }
        self.root.insert_non_full(k);
    }

    pub fn search(&self, k: i32) -> bool { self.root.search(k) }

    pub fn inorder(&self) -> Vec<i32> {
        let mut out = Vec::new();
        self.root.traverse(&mut out);
        out
    }
}

fn main() {
    let mut tree = BTree::new();
    for k in [10, 20, 5, 6, 12, 30, 7, 17] {
        tree.insert(k);
    }
    println!("B-tree in-order: {:?}", tree.inorder());
    println!("Search 12: {}", tree.search(12));
    println!("Search 99: {}", tree.search(99));

    // Production note: Use std::collections::BTreeMap<K, V>
    // for real applications — it's a well-optimized B-tree.
    use std::collections::BTreeMap;
    let mut map: BTreeMap<i32, &str> = BTreeMap::new();
    map.insert(1, "one");
    map.insert(2, "two");
    map.insert(3, "three");
    // range query — O(log n + k)
    for (k, v) in map.range(1..=2) {
        println!("{}: {}", k, v);
    }
}
```

---

## 7. Heap (Min/Max)

A **binary heap** is a complete binary tree stored as an array, satisfying the **heap property**:
- **Min-Heap:** Every node's value ≤ its children's values. Root = global minimum.
- **Max-Heap:** Every node's value ≥ its children's values. Root = global maximum.

### Array Representation

For 0-indexed array:
- Node at index `i`
- Left child: `2i + 1`
- Right child: `2i + 2`
- Parent: `(i - 1) / 2`

For 1-indexed:
- Left: `2i`, Right: `2i+1`, Parent: `i/2`

**Advantage:** No pointers needed; cache-friendly; O(1) parent/child access.

### Heap Operations

| Operation | Time Complexity |
|-----------|----------------|
| Build heap (heapify) | O(n) — not O(n log n)! |
| Insert | O(log n) — sift up |
| Extract min/max | O(log n) — sift down |
| Peek min/max | O(1) |
| Decrease key | O(log n) — sift up |
| Delete arbitrary | O(log n) |
| Merge two heaps | O(n) for binary heap |

**Why build heap is O(n):** Most nodes are near the bottom and barely sift down. The total work is ∑ h * (n/2^h) = O(n).

### Heapsort

Build max-heap from array (O(n)), then repeatedly extract max (O(log n) × n) = **O(n log n)** total, **O(1) extra space**, not stable.

---

### C Implementation — Binary Min-Heap

```c
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

#define HEAP_MAX 1024

typedef struct MinHeap {
    int data[HEAP_MAX];
    int size;
} MinHeap;

static void heap_swap(int *a, int *b) { int t = *a; *a = *b; *b = t; }

/* ─── SIFT UP ────────────────────────────────────────────────────── */
/* After inserting at the end, restore heap property upward */
static void sift_up(MinHeap *h, int i) {
    while (i > 0) {
        int parent = (i - 1) / 2;
        if (h->data[parent] > h->data[i]) {
            heap_swap(&h->data[parent], &h->data[i]);
            i = parent;
        } else break;
    }
}

/* ─── SIFT DOWN ──────────────────────────────────────────────────── */
/* After removing root (or arbitrary update), restore heap property downward */
static void sift_down(MinHeap *h, int i) {
    while (true) {
        int smallest = i;
        int left  = 2 * i + 1;
        int right = 2 * i + 2;

        if (left  < h->size && h->data[left]  < h->data[smallest]) smallest = left;
        if (right < h->size && h->data[right] < h->data[smallest]) smallest = right;

        if (smallest != i) {
            heap_swap(&h->data[i], &h->data[smallest]);
            i = smallest;
        } else break;
    }
}

/* ─── INSERT ─────────────────────────────────────────────────────── */
void heap_insert(MinHeap *h, int val) {
    if (h->size >= HEAP_MAX) { fprintf(stderr, "heap full\n"); return; }
    h->data[h->size++] = val;
    sift_up(h, h->size - 1);
}

/* ─── PEEK (get minimum) ─────────────────────────────────────────── */
int heap_peek(MinHeap *h) {
    if (h->size == 0) { fprintf(stderr, "heap empty\n"); return -1; }
    return h->data[0];
}

/* ─── EXTRACT MIN ────────────────────────────────────────────────── */
int heap_extract_min(MinHeap *h) {
    if (h->size == 0) { fprintf(stderr, "heap empty\n"); return -1; }
    int min = h->data[0];
    h->data[0] = h->data[--h->size];
    sift_down(h, 0);
    return min;
}

/* ─── DECREASE KEY ───────────────────────────────────────────────── */
/* For priority queues: update priority of element at index i */
void heap_decrease_key(MinHeap *h, int i, int new_val) {
    if (new_val > h->data[i]) { fprintf(stderr, "new value larger\n"); return; }
    h->data[i] = new_val;
    sift_up(h, i);
}

/* ─── DELETE at index i ──────────────────────────────────────────── */
void heap_delete(MinHeap *h, int i) {
    heap_decrease_key(h, i, -2147483648);  /* decrease to -INF */
    heap_extract_min(h);                   /* now it's at root; extract */
}

/* ─── BUILD HEAP (from unsorted array) — O(n) ───────────────────── */
void heap_build(MinHeap *h, int *arr, int n) {
    for (int i = 0; i < n; i++) h->data[i] = arr[i];
    h->size = n;
    /* Start from last internal node; sift each down */
    for (int i = n/2 - 1; i >= 0; i--)
        sift_down(h, i);
}

/* ─── HEAPSORT ───────────────────────────────────────────────────── */
void heapsort(int *arr, int n) {
    /* Build max-heap (for ascending sort) */
    /* Reuse sift_down logic adapted for max */
    /* Here we implement in-place using array indexing */
    
    /* Build max-heap */
    for (int i = n/2 - 1; i >= 0; i--) {
        /* Max-sift-down inline */
        int root = i, size = n;
        while (true) {
            int largest = root;
            int l = 2*root+1, r = 2*root+2;
            if (l < size && arr[l] > arr[largest]) largest = l;
            if (r < size && arr[r] > arr[largest]) largest = r;
            if (largest != root) {
                int t = arr[root]; arr[root] = arr[largest]; arr[largest] = t;
                root = largest;
            } else break;
        }
    }

    /* Extract elements one by one */
    for (int i = n-1; i > 0; i--) {
        int t = arr[0]; arr[0] = arr[i]; arr[i] = t;  /* swap root with last */
        /* Sift down on reduced heap */
        int root = 0, size = i;
        while (true) {
            int largest = root;
            int l = 2*root+1, r = 2*root+2;
            if (l < size && arr[l] > arr[largest]) largest = l;
            if (r < size && arr[r] > arr[largest]) largest = r;
            if (largest != root) {
                int t2 = arr[root]; arr[root] = arr[largest]; arr[largest] = t2;
                root = largest;
            } else break;
        }
    }
}

void heap_print(MinHeap *h) {
    for (int i = 0; i < h->size; i++) printf("%d ", h->data[i]);
    printf("\n");
}

int main(void) {
    MinHeap h = {.size = 0};
    int arr[] = {5, 3, 8, 1, 9, 2, 7, 4, 6};
    int n = 9;

    heap_build(&h, arr, n);
    printf("After build: "); heap_print(&h);
    printf("Min: %d\n", heap_peek(&h));

    heap_insert(&h, 0);
    printf("After insert(0) min: %d\n", heap_peek(&h));

    printf("Extract sequence: ");
    while (h.size > 0) printf("%d ", heap_extract_min(&h));
    printf("\n");

    /* Heapsort demo */
    int arr2[] = {64, 34, 25, 12, 22, 11, 90};
    heapsort(arr2, 7);
    printf("Heapsort: ");
    for (int i = 0; i < 7; i++) printf("%d ", arr2[i]);
    printf("\n");

    return 0;
}
```

---

### Go Implementation — Min-Heap

```go
package main

import (
    "container/heap"
    "fmt"
)

// ─── Manual Min-Heap ──────────────────────────────────────────────
type MinHeap struct {
    data []int
}

func (h *MinHeap) parent(i int) int { return (i - 1) / 2 }
func (h *MinHeap) left(i int) int   { return 2*i + 1 }
func (h *MinHeap) right(i int) int  { return 2*i + 2 }

func (h *MinHeap) siftUp(i int) {
    for i > 0 && h.data[h.parent(i)] > h.data[i] {
        p := h.parent(i)
        h.data[p], h.data[i] = h.data[i], h.data[p]
        i = p
    }
}

func (h *MinHeap) siftDown(i int) {
    n := len(h.data)
    for {
        smallest := i
        if l := h.left(i);  l < n && h.data[l] < h.data[smallest] { smallest = l }
        if r := h.right(i); r < n && h.data[r] < h.data[smallest] { smallest = r }
        if smallest == i { break }
        h.data[i], h.data[smallest] = h.data[smallest], h.data[i]
        i = smallest
    }
}

func (h *MinHeap) Insert(val int) {
    h.data = append(h.data, val)
    h.siftUp(len(h.data) - 1)
}

func (h *MinHeap) Peek() int { return h.data[0] }

func (h *MinHeap) ExtractMin() int {
    min := h.data[0]
    n := len(h.data) - 1
    h.data[0] = h.data[n]
    h.data = h.data[:n]
    if n > 0 { h.siftDown(0) }
    return min
}

func (h *MinHeap) Build(arr []int) {
    h.data = make([]int, len(arr))
    copy(h.data, arr)
    for i := len(arr)/2 - 1; i >= 0; i-- {
        h.siftDown(i)
    }
}

// ─── Go stdlib heap.Interface approach ───────────────────────────
// For production, implement heap.Interface:
type IntHeap []int
func (h IntHeap) Len() int            { return len(h) }
func (h IntHeap) Less(i, j int) bool  { return h[i] < h[j] }
func (h IntHeap) Swap(i, j int)       { h[i], h[j] = h[j], h[i] }
func (h *IntHeap) Push(x interface{}) { *h = append(*h, x.(int)) }
func (h *IntHeap) Pop() interface{} {
    old := *h; n := len(old); x := old[n-1]; *h = old[:n-1]; return x
}

func main() {
    h := &MinHeap{}
    h.Build([]int{5, 3, 8, 1, 9, 2, 7})
    fmt.Printf("Min: %d\n", h.Peek())

    h.Insert(0)
    fmt.Printf("After insert(0) min: %d\n", h.Peek())

    fmt.Print("Extract: ")
    for len(h.data) > 0 { fmt.Printf("%d ", h.ExtractMin()) }
    fmt.Println()

    // stdlib heap
    pq := &IntHeap{5, 3, 8, 1, 9}
    heap.Init(pq)
    heap.Push(pq, 0)
    fmt.Printf("stdlib heap min: %d\n", (*pq)[0])
}
```

---

### Rust Implementation — Min-Heap

```rust
// Rust std has BinaryHeap (max-heap by default).
// For min-heap, wrap values in Reverse<T>.

use std::collections::BinaryHeap;
use std::cmp::Reverse;

struct MinHeap {
    data: Vec<i32>,
}

impl MinHeap {
    fn new() -> Self { MinHeap { data: Vec::new() } }

    fn parent(i: usize) -> usize { (i - 1) / 2 }
    fn left(i: usize) -> usize   { 2 * i + 1 }
    fn right(i: usize) -> usize  { 2 * i + 2 }

    fn sift_up(&mut self, mut i: usize) {
        while i > 0 {
            let p = Self::parent(i);
            if self.data[p] > self.data[i] {
                self.data.swap(p, i);
                i = p;
            } else { break; }
        }
    }

    fn sift_down(&mut self, mut i: usize) {
        let n = self.data.len();
        loop {
            let mut smallest = i;
            let l = Self::left(i);
            let r = Self::right(i);
            if l < n && self.data[l] < self.data[smallest] { smallest = l; }
            if r < n && self.data[r] < self.data[smallest] { smallest = r; }
            if smallest == i { break; }
            self.data.swap(i, smallest);
            i = smallest;
        }
    }

    fn insert(&mut self, val: i32) {
        self.data.push(val);
        let i = self.data.len() - 1;
        self.sift_up(i);
    }

    fn peek(&self) -> Option<i32> { self.data.first().copied() }

    fn extract_min(&mut self) -> Option<i32> {
        if self.data.is_empty() { return None; }
        let min = self.data[0];
        let last = self.data.pop().unwrap();
        if !self.data.is_empty() {
            self.data[0] = last;
            self.sift_down(0);
        }
        Some(min)
    }

    fn build(arr: &[i32]) -> Self {
        let mut h = MinHeap { data: arr.to_vec() };
        let n = h.data.len();
        for i in (0..n / 2).rev() { h.sift_down(i); }
        h
    }
}

fn main() {
    // Manual min-heap
    let mut h = MinHeap::build(&[5, 3, 8, 1, 9, 2, 7]);
    println!("Min: {:?}", h.peek());
    h.insert(0);
    println!("After insert(0) min: {:?}", h.peek());
    let mut extracted = Vec::new();
    while let Some(v) = h.extract_min() { extracted.push(v); }
    println!("Extracted: {:?}", extracted);

    // Stdlib BinaryHeap (max-heap)
    let mut max_heap = BinaryHeap::from([5, 3, 8, 1, 9]);
    println!("Max: {:?}", max_heap.peek()); // 9

    // Min-heap via Reverse
    let mut min_heap: BinaryHeap<Reverse<i32>> = BinaryHeap::new();
    for v in [5, 3, 8, 1, 9] { min_heap.push(Reverse(v)); }
    println!("Min (Reverse): {:?}", min_heap.peek().map(|r| r.0)); // 1
}
```

---

## 8. Trie (Prefix Tree)

A **Trie** is an N-ary tree where each edge is labeled with a character (or bit, or digit). A path from root to a marked node spells a string stored in the trie.

### Key Properties

- Root node represents the empty string.
- Each node can have up to `ALPHABET_SIZE` children (26 for lowercase English).
- The position in the tree (not the node itself) defines the character.
- Common prefixes share the same path, making prefix queries highly efficient.

### Trie Operations

| Operation | Time | Space |
|-----------|------|-------|
| Insert | O(m) where m = key length | O(m * ALPHABET_SIZE) worst per key |
| Search | O(m) | — |
| Delete | O(m) | — |
| Prefix count | O(p) where p = prefix length | — |
| Autocomplete | O(p + k) where k = results | — |
| Lexicographic sort | O(n * m) | — |

### Trie Variants

- **Compressed Trie / Patricia Tree / Radix Tree:** Merges nodes with single children. Reduces space from O(n*m) to O(n).
- **Ternary Search Tree (TST):** Space-efficient; each node has three children (less than, equal, greater than). Balance between trie and BST.
- **Suffix Trie/Tree:** Contains all suffixes of a string. Enables O(m) substring search.
- **Bit Trie / Binary Trie:** For integers; traverse bits. Used in XOR-max problems.

---

### C Implementation — Trie

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

#define ALPHA 26

typedef struct TrieNode {
    struct TrieNode *children[ALPHA];
    bool is_end;
    int count;          /* number of words with this prefix */
    int word_count;     /* number of words ending exactly here */
} TrieNode;

/* ─── CREATE ─────────────────────────────────────────────────────── */
TrieNode *trie_new_node() {
    TrieNode *n = calloc(1, sizeof(TrieNode));
    return n;
}

/* ─── INSERT ─────────────────────────────────────────────────────── */
void trie_insert(TrieNode *root, const char *word) {
    TrieNode *curr = root;
    while (*word) {
        int idx = *word - 'a';
        if (!curr->children[idx])
            curr->children[idx] = trie_new_node();
        curr = curr->children[idx];
        curr->count++;   /* increment prefix count at every node */
        word++;
    }
    curr->is_end = true;
    curr->word_count++;
}

/* ─── SEARCH (exact) ─────────────────────────────────────────────── */
bool trie_search(TrieNode *root, const char *word) {
    TrieNode *curr = root;
    while (*word) {
        int idx = *word - 'a';
        if (!curr->children[idx]) return false;
        curr = curr->children[idx];
        word++;
    }
    return curr->is_end;
}

/* ─── STARTS WITH (prefix check) ─────────────────────────────────── */
bool trie_starts_with(TrieNode *root, const char *prefix) {
    TrieNode *curr = root;
    while (*prefix) {
        int idx = *prefix - 'a';
        if (!curr->children[idx]) return false;
        curr = curr->children[idx];
        prefix++;
    }
    return true;
}

/* ─── COUNT words with prefix ─────────────────────────────────────── */
int trie_count_prefix(TrieNode *root, const char *prefix) {
    TrieNode *curr = root;
    while (*prefix) {
        int idx = *prefix - 'a';
        if (!curr->children[idx]) return 0;
        curr = curr->children[idx];
        prefix++;
    }
    return curr->count;
}

/* ─── DELETE ─────────────────────────────────────────────────────── */
/*
 * Recursive delete. Returns true if the current node can be freed.
 * Decrements prefix counts. Removes nodes that are no longer needed.
 */
bool trie_delete_helper(TrieNode *curr, const char *word) {
    if (!curr) return false;

    if (*word == '\0') {
        /* Reached end of word */
        if (!curr->is_end) return false;  /* word doesn't exist */
        curr->is_end = false;
        curr->word_count--;
        /* If no children remain, signal parent to free this node */
        for (int i = 0; i < ALPHA; i++)
            if (curr->children[i]) return false;
        return true;  /* can be deleted */
    }

    int idx = *word - 'a';
    if (trie_delete_helper(curr->children[idx], word + 1)) {
        free(curr->children[idx]);
        curr->children[idx] = NULL;
        curr->count--;
        /* Can free current if not end-of-word and no children */
        if (!curr->is_end) {
            for (int i = 0; i < ALPHA; i++)
                if (curr->children[i]) return false;
            return true;
        }
    }
    return false;
}

void trie_delete(TrieNode *root, const char *word) {
    trie_delete_helper(root, word);
}

/* ─── AUTOCOMPLETE (DFS from prefix node) ──────────────────────── */
static char buf[256];

void trie_autocomplete(TrieNode *node, int depth) {
    if (!node) return;
    if (node->is_end) {
        buf[depth] = '\0';
        printf("  %s\n", buf);
    }
    for (int i = 0; i < ALPHA; i++) {
        if (node->children[i]) {
            buf[depth] = 'a' + i;
            trie_autocomplete(node->children[i], depth + 1);
        }
    }
}

void trie_suggest(TrieNode *root, const char *prefix) {
    TrieNode *curr = root;
    int len = strlen(prefix);
    strncpy(buf, prefix, len);

    while (*prefix) {
        int idx = *prefix - 'a';
        if (!curr->children[idx]) {
            printf("No suggestions for prefix '%s'\n", buf);
            return;
        }
        curr = curr->children[idx];
        prefix++;
    }

    printf("Suggestions for '%s':\n", buf);
    trie_autocomplete(curr, len);
}

/* ─── LEXICOGRAPHIC SORT of all words ──────────────────────────── */
void trie_sort(TrieNode *node, char *buf, int depth) {
    if (node->is_end) {
        buf[depth] = '\0';
        printf("%s\n", buf);
    }
    for (int i = 0; i < ALPHA; i++) {
        if (node->children[i]) {
            buf[depth] = 'a' + i;
            trie_sort(node->children[i], buf, depth + 1);
        }
    }
}

void trie_free(TrieNode *root) {
    if (!root) return;
    for (int i = 0; i < ALPHA; i++) trie_free(root->children[i]);
    free(root);
}

int main(void) {
    TrieNode *root = trie_new_node();
    const char *words[] = {"apple", "app", "application", "apply", "apt", "banana"};
    for (int i = 0; i < 6; i++) trie_insert(root, words[i]);

    printf("Search 'app':   %s\n", trie_search(root, "app")   ? "found" : "not found");
    printf("Search 'ap':    %s\n", trie_search(root, "ap")    ? "found" : "not found");
    printf("Prefix 'app':   %s\n", trie_starts_with(root, "app") ? "yes" : "no");
    printf("Count prefix 'app': %d\n", trie_count_prefix(root, "app"));

    trie_suggest(root, "app");

    char sortbuf[256];
    printf("Lexicographic order:\n");
    trie_sort(root, sortbuf, 0);

    trie_delete(root, "app");
    printf("After delete 'app', search: %s\n",
           trie_search(root, "app") ? "found" : "not found");
    printf("'apple' still: %s\n",
           trie_search(root, "apple") ? "found" : "not found");

    trie_free(root);
    return 0;
}
```

---

### Go Implementation — Trie

```go
package main

import "fmt"

const alpha = 26

type TrieNode struct {
    Children    [alpha]*TrieNode
    IsEnd       bool
    PrefixCount int
}

type Trie struct{ root *TrieNode }

func NewTrie() *Trie { return &Trie{root: &TrieNode{}} }

func (t *Trie) Insert(word string) {
    curr := t.root
    for _, ch := range word {
        idx := ch - 'a'
        if curr.Children[idx] == nil { curr.Children[idx] = &TrieNode{} }
        curr = curr.Children[idx]
        curr.PrefixCount++
    }
    curr.IsEnd = true
}

func (t *Trie) Search(word string) bool {
    curr := t.root
    for _, ch := range word {
        idx := ch - 'a'
        if curr.Children[idx] == nil { return false }
        curr = curr.Children[idx]
    }
    return curr.IsEnd
}

func (t *Trie) StartsWith(prefix string) bool {
    curr := t.root
    for _, ch := range prefix {
        idx := ch - 'a'
        if curr.Children[idx] == nil { return false }
        curr = curr.Children[idx]
    }
    return true
}

func (t *Trie) CountPrefix(prefix string) int {
    curr := t.root
    for _, ch := range prefix {
        idx := ch - 'a'
        if curr.Children[idx] == nil { return 0 }
        curr = curr.Children[idx]
    }
    return curr.PrefixCount
}

func (t *Trie) Delete(word string) bool {
    return t.deleteHelper(t.root, word, 0)
}

func (t *Trie) deleteHelper(node *TrieNode, word string, depth int) bool {
    if node == nil { return false }
    if depth == len(word) {
        if !node.IsEnd { return false }
        node.IsEnd = false
        for _, c := range node.Children { if c != nil { return false } }
        return true
    }
    idx := word[depth] - 'a'
    if t.deleteHelper(node.Children[idx], word, depth+1) {
        node.Children[idx] = nil
        node.PrefixCount--
        if !node.IsEnd {
            for _, c := range node.Children { if c != nil { return false } }
            return true
        }
    }
    return false
}

func (t *Trie) Autocomplete(prefix string) []string {
    curr := t.root
    for _, ch := range prefix {
        idx := ch - 'a'
        if curr.Children[idx] == nil { return nil }
        curr = curr.Children[idx]
    }
    var results []string
    var dfs func(*TrieNode, []byte)
    dfs = func(node *TrieNode, buf []byte) {
        if node.IsEnd { results = append(results, string(buf)) }
        for i, c := range node.Children {
            if c != nil { dfs(c, append(buf, byte('a'+i))) }
        }
    }
    dfs(curr, []byte(prefix))
    return results
}

func main() {
    t := NewTrie()
    for _, w := range []string{"apple", "app", "application", "apply", "apt", "banana"} {
        t.Insert(w)
    }
    fmt.Println("Search 'app':", t.Search("app"))
    fmt.Println("Search 'ap':", t.Search("ap"))
    fmt.Println("CountPrefix('app'):", t.CountPrefix("app"))
    fmt.Println("Autocomplete('app'):", t.Autocomplete("app"))

    t.Delete("app")
    fmt.Println("After delete 'app':", t.Search("app"), "apple:", t.Search("apple"))
}
```

---

### Rust Implementation — Trie

```rust
use std::collections::HashMap;

#[derive(Default, Debug)]
struct TrieNode {
    children:     HashMap<char, TrieNode>,
    is_end:       bool,
    prefix_count: usize,
}

pub struct Trie { root: TrieNode }

impl Trie {
    pub fn new() -> Self { Trie { root: TrieNode::default() } }

    pub fn insert(&mut self, word: &str) {
        let mut curr = &mut self.root;
        for ch in word.chars() {
            curr = curr.children.entry(ch).or_default();
            curr.prefix_count += 1;
        }
        curr.is_end = true;
    }

    pub fn search(&self, word: &str) -> bool {
        let mut curr = &self.root;
        for ch in word.chars() {
            match curr.children.get(&ch) {
                None => return false,
                Some(n) => curr = n,
            }
        }
        curr.is_end
    }

    pub fn starts_with(&self, prefix: &str) -> bool {
        let mut curr = &self.root;
        for ch in prefix.chars() {
            match curr.children.get(&ch) {
                None => return false,
                Some(n) => curr = n,
            }
        }
        true
    }

    pub fn count_prefix(&self, prefix: &str) -> usize {
        let mut curr = &self.root;
        for ch in prefix.chars() {
            match curr.children.get(&ch) {
                None => return 0,
                Some(n) => curr = n,
            }
        }
        curr.prefix_count
    }

    pub fn autocomplete(&self, prefix: &str) -> Vec<String> {
        let mut curr = &self.root;
        for ch in prefix.chars() {
            match curr.children.get(&ch) {
                None => return Vec::new(),
                Some(n) => curr = n,
            }
        }
        let mut results = Vec::new();
        Self::collect(curr, prefix.to_string(), &mut results);
        results
    }

    fn collect(node: &TrieNode, current: String, results: &mut Vec<String>) {
        if node.is_end { results.push(current.clone()); }
        let mut sorted_keys: Vec<char> = node.children.keys().cloned().collect();
        sorted_keys.sort();
        for ch in sorted_keys {
            let mut next = current.clone();
            next.push(ch);
            Self::collect(&node.children[&ch], next, results);
        }
    }
}

fn main() {
    let mut t = Trie::new();
    for w in ["apple", "app", "application", "apply", "apt", "banana"] {
        t.insert(w);
    }
    println!("Search 'app': {}", t.search("app"));
    println!("Starts with 'app': {}", t.starts_with("app"));
    println!("Count prefix 'app': {}", t.count_prefix("app"));
    println!("Autocomplete 'app': {:?}", t.autocomplete("app"));
}
```

---

## 9. Segment Tree

A **Segment Tree** is a binary tree designed for **range queries** and **point/range updates** over an array. Each node stores the aggregated result for a range [l, r].

### Core Concept

- Leaf node `i` corresponds to `arr[i]`.
- Internal node for range [l, r] stores `aggregate(arr[l..r])`.
- Aggregate function: sum, min, max, GCD, XOR, or any **associative** function.
- Built in O(n) and stored in an array of size ~4n.

### Lazy Propagation

Without lazy propagation, **range updates** cost O(n). With lazy propagation:
- Defer updates to children using a `lazy[]` array.
- When traversing, push down lazy values before accessing children.
- Both range updates and range queries become O(log n).

### When to Use

- **Point query, range update:** Array + difference array (O(1) update, O(n) query for prefix sums) or segment tree with lazy.
- **Range query, point update:** Segment tree or Fenwick tree.
- **Range query, range update:** Segment tree with lazy propagation.

---

### C Implementation — Segment Tree (Sum + Lazy Range Update)

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAXN 100005

long long tree[4*MAXN];   /* segment tree array */
long long lazy[4*MAXN];   /* lazy propagation array */
int n;                    /* size of original array */

/* ─── BUILD ───────────────────────────────────────────────────────── */
void seg_build(int *arr, int node, int start, int end) {
    if (start == end) {
        tree[node] = arr[start];
        return;
    }
    int mid = (start + end) / 2;
    seg_build(arr, 2*node,   start,   mid);
    seg_build(arr, 2*node+1, mid+1, end);
    tree[node] = tree[2*node] + tree[2*node+1];
}

/* ─── PUSH DOWN (propagate lazy) ───────────────────────────────────── */
static void push_down(int node, int start, int end) {
    if (lazy[node] != 0) {
        int mid = (start + end) / 2;
        /* Apply to left child */
        tree[2*node]   += lazy[node] * (mid - start + 1);
        lazy[2*node]   += lazy[node];
        /* Apply to right child */
        tree[2*node+1] += lazy[node] * (end - mid);
        lazy[2*node+1] += lazy[node];
        lazy[node] = 0;
    }
}

/* ─── RANGE UPDATE (add val to all elements in [l, r]) ─────────────── */
void seg_update(int node, int start, int end, int l, int r, long long val) {
    if (r < start || end < l) return;  /* out of range */

    if (l <= start && end <= r) {
        /* Completely inside update range: apply and mark lazy */
        tree[node] += val * (end - start + 1);
        lazy[node] += val;
        return;
    }

    push_down(node, start, end);  /* push before going deeper */

    int mid = (start + end) / 2;
    seg_update(2*node,   start, mid,   l, r, val);
    seg_update(2*node+1, mid+1, end,   l, r, val);
    tree[node] = tree[2*node] + tree[2*node+1];
}

/* ─── RANGE QUERY (sum of [l, r]) ─────────────────────────────────── */
long long seg_query(int node, int start, int end, int l, int r) {
    if (r < start || end < l) return 0;  /* out of range */
    if (l <= start && end <= r) return tree[node];  /* fully covered */

    push_down(node, start, end);

    int mid = (start + end) / 2;
    return seg_query(2*node,   start, mid, l, r) +
           seg_query(2*node+1, mid+1, end, l, r);
}

/* ─── POINT UPDATE ────────────────────────────────────────────────── */
void seg_point_update(int node, int start, int end, int idx, long long val) {
    if (start == end) { tree[node] = val; return; }
    push_down(node, start, end);
    int mid = (start + end) / 2;
    if (idx <= mid) seg_point_update(2*node,   start,   mid, idx, val);
    else            seg_point_update(2*node+1, mid+1, end, idx, val);
    tree[node] = tree[2*node] + tree[2*node+1];
}

/* ─── RANGE MIN QUERY (separate tree for illustration) ─────────────── */
long long mintree[4*MAXN];

void seg_build_min(int *arr, int node, int start, int end) {
    if (start == end) { mintree[node] = arr[start]; return; }
    int mid = (start + end) / 2;
    seg_build_min(arr, 2*node,   start,   mid);
    seg_build_min(arr, 2*node+1, mid+1, end);
    mintree[node] = mintree[2*node] < mintree[2*node+1]
                  ? mintree[2*node] : mintree[2*node+1];
}

long long seg_query_min(int node, int start, int end, int l, int r) {
    if (r < start || end < l) return (long long)2e18;
    if (l <= start && end <= r) return mintree[node];
    int mid = (start + end) / 2;
    long long lq = seg_query_min(2*node,   start, mid, l, r);
    long long rq = seg_query_min(2*node+1, mid+1, end, l, r);
    return lq < rq ? lq : rq;
}

int main(void) {
    int arr[] = {1, 3, 5, 7, 9, 11};
    n = 6;

    memset(lazy, 0, sizeof(lazy));
    seg_build(arr, 1, 0, n-1);

    printf("Sum [1,3]: %lld\n", seg_query(1, 0, n-1, 1, 3));  /* 3+5+7=15 */
    printf("Sum [0,5]: %lld\n", seg_query(1, 0, n-1, 0, n-1));/* 36 */

    /* Range add 10 to [1,3] */
    seg_update(1, 0, n-1, 1, 3, 10);
    printf("After +10 to [1,3], sum [1,3]: %lld\n",
           seg_query(1, 0, n-1, 1, 3));  /* 15+30=45 */

    /* Point update: set arr[2] = 0 */
    seg_point_update(1, 0, n-1, 2, 0);
    printf("After point_update(2,0), sum [0,5]: %lld\n",
           seg_query(1, 0, n-1, 0, n-1));

    /* Min segment tree */
    seg_build_min(arr, 1, 0, n-1);
    printf("Min [1,4]: %lld\n", seg_query_min(1, 0, n-1, 1, 4));  /* 3 */

    return 0;
}
```

---

### Go Implementation — Segment Tree

```go
package main

import "fmt"

type SegTree struct {
    tree []int64
    lazy []int64
    n    int
}

func NewSegTree(arr []int) *SegTree {
    n := len(arr)
    st := &SegTree{
        tree: make([]int64, 4*n),
        lazy: make([]int64, 4*n),
        n:    n,
    }
    st.build(arr, 1, 0, n-1)
    return st
}

func (st *SegTree) build(arr []int, node, start, end int) {
    if start == end {
        st.tree[node] = int64(arr[start])
        return
    }
    mid := (start + end) / 2
    st.build(arr, 2*node, start, mid)
    st.build(arr, 2*node+1, mid+1, end)
    st.tree[node] = st.tree[2*node] + st.tree[2*node+1]
}

func (st *SegTree) pushDown(node, start, end int) {
    if st.lazy[node] != 0 {
        mid := (start + end) / 2
        st.tree[2*node]   += st.lazy[node] * int64(mid-start+1)
        st.lazy[2*node]   += st.lazy[node]
        st.tree[2*node+1] += st.lazy[node] * int64(end-mid)
        st.lazy[2*node+1] += st.lazy[node]
        st.lazy[node] = 0
    }
}

func (st *SegTree) Update(l, r int, val int64) {
    st.update(1, 0, st.n-1, l, r, val)
}

func (st *SegTree) update(node, start, end, l, r int, val int64) {
    if r < start || end < l { return }
    if l <= start && end <= r {
        st.tree[node] += val * int64(end-start+1)
        st.lazy[node] += val
        return
    }
    st.pushDown(node, start, end)
    mid := (start + end) / 2
    st.update(2*node, start, mid, l, r, val)
    st.update(2*node+1, mid+1, end, l, r, val)
    st.tree[node] = st.tree[2*node] + st.tree[2*node+1]
}

func (st *SegTree) Query(l, r int) int64 {
    return st.query(1, 0, st.n-1, l, r)
}

func (st *SegTree) query(node, start, end, l, r int) int64 {
    if r < start || end < l { return 0 }
    if l <= start && end <= r { return st.tree[node] }
    st.pushDown(node, start, end)
    mid := (start + end) / 2
    return st.query(2*node, start, mid, l, r) +
           st.query(2*node+1, mid+1, end, l, r)
}

func main() {
    arr := []int{1, 3, 5, 7, 9, 11}
    st := NewSegTree(arr)
    fmt.Println("Sum [1,3]:", st.Query(1, 3)) // 15
    fmt.Println("Sum [0,5]:", st.Query(0, 5)) // 36
    st.Update(1, 3, 10)
    fmt.Println("After +10 to [1,3], sum [1,3]:", st.Query(1, 3)) // 45
}
```

---

### Rust Implementation — Segment Tree

```rust
pub struct SegTree {
    tree: Vec<i64>,
    lazy: Vec<i64>,
    n:    usize,
}

impl SegTree {
    pub fn build(arr: &[i32]) -> Self {
        let n = arr.len();
        let mut st = SegTree {
            tree: vec![0; 4 * n],
            lazy: vec![0; 4 * n],
            n,
        };
        st.build_rec(arr, 1, 0, n - 1);
        st
    }

    fn build_rec(&mut self, arr: &[i32], node: usize, start: usize, end: usize) {
        if start == end { self.tree[node] = arr[start] as i64; return; }
        let mid = (start + end) / 2;
        self.build_rec(arr, 2*node, start, mid);
        self.build_rec(arr, 2*node+1, mid+1, end);
        self.tree[node] = self.tree[2*node] + self.tree[2*node+1];
    }

    fn push_down(&mut self, node: usize, start: usize, end: usize) {
        if self.lazy[node] != 0 {
            let mid = (start + end) / 2;
            self.tree[2*node]   += self.lazy[node] * (mid - start + 1) as i64;
            self.lazy[2*node]   += self.lazy[node];
            self.tree[2*node+1] += self.lazy[node] * (end - mid) as i64;
            self.lazy[2*node+1] += self.lazy[node];
            self.lazy[node] = 0;
        }
    }

    pub fn update(&mut self, l: usize, r: usize, val: i64) {
        let n = self.n - 1;
        self.update_rec(1, 0, n, l, r, val);
    }

    fn update_rec(&mut self, node: usize, start: usize, end: usize, l: usize, r: usize, val: i64) {
        if r < start || end < l { return; }
        if l <= start && end <= r {
            self.tree[node] += val * (end - start + 1) as i64;
            self.lazy[node] += val;
            return;
        }
        self.push_down(node, start, end);
        let mid = (start + end) / 2;
        self.update_rec(2*node, start, mid, l, r, val);
        self.update_rec(2*node+1, mid+1, end, l, r, val);
        self.tree[node] = self.tree[2*node] + self.tree[2*node+1];
    }

    pub fn query(&mut self, l: usize, r: usize) -> i64 {
        let n = self.n - 1;
        self.query_rec(1, 0, n, l, r)
    }

    fn query_rec(&mut self, node: usize, start: usize, end: usize, l: usize, r: usize) -> i64 {
        if r < start || end < l { return 0; }
        if l <= start && end <= r { return self.tree[node]; }
        self.push_down(node, start, end);
        let mid = (start + end) / 2;
        self.query_rec(2*node, start, mid, l, r) +
        self.query_rec(2*node+1, mid+1, end, l, r)
    }
}

fn main() {
    let arr = [1, 3, 5, 7, 9, 11];
    let mut st = SegTree::build(&arr);
    println!("Sum [1,3]: {}", st.query(1, 3)); // 15
    println!("Sum [0,5]: {}", st.query(0, 5)); // 36
    st.update(1, 3, 10);
    println!("After +10 to [1,3], sum [1,3]: {}", st.query(1, 3)); // 45
}
```

---

## 10. Fenwick Tree (Binary Indexed Tree)

A **Fenwick Tree (BIT)** supports two operations in O(log n):
1. **Point update:** Add a value to a specific index.
2. **Prefix sum query:** Sum of elements from index 1 to i.

From these two, range sums [l, r] = prefix(r) - prefix(l-1).

### How It Works

The key insight is the binary representation of indices. Each position `i` in the BIT is responsible for the range of length `i & (-i)` (the lowest set bit).

- **Update at i:** Propagate upward by repeatedly adding `i & (-i)` to i.
- **Query prefix [1..i]:** Walk downward by repeatedly subtracting `i & (-i)` from i.

### BIT vs Segment Tree

| | Fenwick Tree | Segment Tree |
|--|---|---|
| Space | O(n) | O(4n) |
| Point update | O(log n) | O(log n) |
| Prefix/range query | O(log n) | O(log n) |
| Range update | Complex (2 BITs) | O(log n) with lazy |
| Arbitrary queries (min/max) | Not supported | Supported |
| Implementation | ~10 lines | ~50+ lines |
| Constant factor | Very small | Larger |

**Rule:** Prefer BIT for sum/count queries with point updates. Use segment tree for min/max or range updates.

---

### C Implementation — Fenwick Tree

```c
#include <stdio.h>
#include <string.h>

#define MAXN 100005

typedef long long ll;

ll bit[MAXN];
int n;

/* ─── UPDATE: add val at index i (1-indexed) ────────────────────── */
void bit_update(int i, ll val) {
    for (; i <= n; i += i & (-i))
        bit[i] += val;
}

/* ─── QUERY: prefix sum [1..i] ──────────────────────────────────── */
ll bit_query(int i) {
    ll sum = 0;
    for (; i > 0; i -= i & (-i))
        sum += bit[i];
    return sum;
}

/* ─── RANGE QUERY: sum [l..r] ───────────────────────────────────── */
ll bit_range(int l, int r) {
    return bit_query(r) - bit_query(l-1);
}

/* ─── BUILD from array ───────────────────────────────────────────── */
void bit_build(int *arr, int size) {
    n = size;
    memset(bit, 0, sizeof(ll) * (n+1));
    for (int i = 1; i <= n; i++)
        bit_update(i, arr[i-1]);  /* arr is 0-indexed, BIT is 1-indexed */
}

/* ─── POINT QUERY (value at index i) ────────────────────────────── */
ll bit_point_query(int i) {
    return bit_range(i, i);
}

/* ─── FIND K-TH SMALLEST (order statistics BIT) ─────────────────── */
/*
 * If BIT stores frequency (1 for present, 0 for absent),
 * find the position of the k-th 1.
 * This runs in O(log n) using binary lifting.
 */
int bit_kth(int k) {
    int pos = 0;
    /* Find highest bit of n */
    int log_n = 0;
    while ((1 << log_n) <= n) log_n++;

    for (int i = log_n; i >= 0; i--) {
        if (pos + (1 << i) <= n && bit[pos + (1 << i)] < k) {
            pos += (1 << i);
            k -= bit[pos];
        }
    }
    return pos + 1;
}

/* ─── 2D BIT (for 2D range sum queries) ─────────────────────────── */
#define M 1005
ll bit2d[M][M];
int rows, cols;

void bit2d_update(int r, int c, ll val) {
    for (int i = r; i <= rows; i += i & (-i))
        for (int j = c; j <= cols; j += j & (-j))
            bit2d[i][j] += val;
}

ll bit2d_query(int r, int c) {
    ll sum = 0;
    for (int i = r; i > 0; i -= i & (-i))
        for (int j = c; j > 0; j -= j & (-j))
            sum += bit2d[i][j];
    return sum;
}

ll bit2d_range(int r1, int c1, int r2, int c2) {
    return bit2d_query(r2, c2)
         - bit2d_query(r1-1, c2)
         - bit2d_query(r2, c1-1)
         + bit2d_query(r1-1, c1-1);
}

int main(void) {
    int arr[] = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};
    bit_build(arr, 10);

    printf("Prefix sum [1..5]:  %lld\n", bit_query(5));    /* 15 */
    printf("Range sum  [3..7]:  %lld\n", bit_range(3, 7)); /* 25 */

    bit_update(3, 5);  /* add 5 to index 3 */
    printf("After +5 at [3], range [3..7]: %lld\n", bit_range(3, 7)); /* 30 */

    /* Point query */
    printf("Value at index 3 (original 3 + 5 = 8 delta): %lld\n",
           bit_range(3, 3));

    return 0;
}
```

---

### Go Implementation — Fenwick Tree

```go
package main

import "fmt"

type BIT struct {
    tree []int64
    n    int
}

func NewBIT(n int) *BIT { return &BIT{tree: make([]int64, n+1), n: n} }

func (b *BIT) Update(i int, val int64) {
    for ; i <= b.n; i += i & (-i) { b.tree[i] += val }
}

func (b *BIT) Query(i int) int64 {
    var sum int64
    for ; i > 0; i -= i & (-i) { sum += b.tree[i] }
    return sum
}

func (b *BIT) Range(l, r int) int64 { return b.Query(r) - b.Query(l-1) }

func NewBITFromArray(arr []int) *BIT {
    b := NewBIT(len(arr))
    for i, v := range arr { b.Update(i+1, int64(v)) }
    return b
}

func main() {
    arr := []int{1, 2, 3, 4, 5, 6, 7, 8, 9, 10}
    b := NewBITFromArray(arr)
    fmt.Println("Prefix [1..5]:", b.Query(5))    // 15
    fmt.Println("Range [3..7]:",  b.Range(3, 7)) // 25
    b.Update(3, 5)
    fmt.Println("After +5 at [3], range [3..7]:", b.Range(3, 7)) // 30
}
```

---

### Rust Implementation — Fenwick Tree

```rust
pub struct BIT {
    tree: Vec<i64>,
    n:    usize,
}

impl BIT {
    pub fn new(n: usize) -> Self { BIT { tree: vec![0; n + 1], n } }

    pub fn from_slice(arr: &[i32]) -> Self {
        let mut b = BIT::new(arr.len());
        for (i, &v) in arr.iter().enumerate() { b.update(i + 1, v as i64); }
        b
    }

    pub fn update(&mut self, mut i: usize, val: i64) {
        while i <= self.n { self.tree[i] += val; i += i & i.wrapping_neg(); }
    }

    pub fn query(&self, mut i: usize) -> i64 {
        let mut sum = 0;
        while i > 0 { sum += self.tree[i]; i -= i & i.wrapping_neg(); }
        sum
    }

    pub fn range(&self, l: usize, r: usize) -> i64 {
        self.query(r) - if l > 1 { self.query(l - 1) } else { 0 }
    }
}

fn main() {
    let arr = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
    let mut b = BIT::from_slice(&arr);
    println!("Prefix [1..5]: {}", b.query(5));    // 15
    println!("Range [3..7]:  {}", b.range(3, 7)); // 25
    b.update(3, 5);
    println!("After +5 at [3], range [3..7]: {}", b.range(3, 7)); // 30
}
```

---

## 14. Traversal Algorithms — Deep Dive

All traversal algorithms visit every node exactly once: O(n) time, O(h) stack space.

### Iterative Implementations (Essential for Production)

Recursive implementations risk stack overflow for deep trees (n=100,000 → depth=100,000 → stack overflow). Iterative implementations use an explicit stack.

---

### C Implementation — All Iterative Traversals

```c
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

typedef struct Node { int val; struct Node *l, *r; } Node;

/* ─── STACK for iterative traversals ────────────────────────────── */
typedef struct Stack { Node **data; int top, cap; } Stack;
Stack *stack_new(int cap) {
    Stack *s = malloc(sizeof(Stack));
    s->data = malloc(cap * sizeof(Node*));
    s->top = 0; s->cap = cap; return s;
}
void push(Stack *s, Node *n) { s->data[s->top++] = n; }
Node *pop(Stack *s)  { return s->data[--s->top]; }
Node *peek_s(Stack *s) { return s->data[s->top-1]; }
bool empty(Stack *s) { return s->top == 0; }

/* ─── ITERATIVE IN-ORDER ─────────────────────────────────────────── */
/*
 * Invariant: curr = "node we need to visit next" or NULL.
 * If curr: push it and go left.
 * Else: pop, visit, go right.
 */
void inorder_iter(Node *root) {
    Stack *s = stack_new(1000);
    Node *curr = root;
    while (curr || !empty(s)) {
        while (curr) { push(s, curr); curr = curr->l; }
        curr = pop(s);
        printf("%d ", curr->val);
        curr = curr->r;
    }
    printf("\n");
    free(s->data); free(s);
}

/* ─── ITERATIVE PRE-ORDER ───────────────────────────────────────── */
void preorder_iter(Node *root) {
    if (!root) return;
    Stack *s = stack_new(1000);
    push(s, root);
    while (!empty(s)) {
        Node *n = pop(s);
        printf("%d ", n->val);
        if (n->r) push(s, n->r);  /* push right first: LIFO */
        if (n->l) push(s, n->l);
    }
    printf("\n");
    free(s->data); free(s);
}

/* ─── ITERATIVE POST-ORDER (two-stack method) ───────────────────── */
/*
 * Push root to s1. While s1 not empty:
 *   Pop from s1, push to s2.
 *   Push left and right children to s1.
 * Print s2 in reverse (which gives post-order).
 * Result: root is printed last.
 */
void postorder_iter(Node *root) {
    if (!root) return;
    Stack *s1 = stack_new(1000);
    Stack *s2 = stack_new(1000);
    push(s1, root);
    while (!empty(s1)) {
        Node *n = pop(s1);
        push(s2, n);
        if (n->l) push(s1, n->l);
        if (n->r) push(s1, n->r);
    }
    while (!empty(s2)) printf("%d ", pop(s2)->val);
    printf("\n");
    free(s1->data); free(s1);
    free(s2->data); free(s2);
}

/* ─── MORRIS TRAVERSAL (in-order, O(1) space!) ──────────────────── */
/*
 * Morris traversal achieves O(n) time, O(1) space (no stack, no recursion)
 * by temporarily modifying the tree's right pointers (threading).
 *
 * For each node:
 * - If no left child: visit, go right.
 * - If left child exists: find in-order predecessor (rightmost of left subtree).
 *   - If predecessor's right == NULL: thread it to current, go left.
 *   - If predecessor's right == current: un-thread, visit current, go right.
 */
void morris_inorder(Node *root) {
    Node *curr = root;
    while (curr) {
        if (!curr->l) {
            printf("%d ", curr->val);
            curr = curr->r;
        } else {
            /* Find in-order predecessor */
            Node *pred = curr->l;
            while (pred->r && pred->r != curr) pred = pred->r;

            if (!pred->r) {
                /* Thread right pointer to current */
                pred->r = curr;
                curr    = curr->l;
            } else {
                /* Already threaded: un-thread, visit, move right */
                pred->r = NULL;
                printf("%d ", curr->val);
                curr = curr->r;
            }
        }
    }
    printf("\n");
}

/* ─── LEVEL-ORDER with level separation ────────────────────────── */
void levelorder_levels(Node *root) {
    if (!root) return;
    /* Use two queues or count-based approach */
    Node **queue = malloc(10000 * sizeof(Node*));
    int front = 0, rear = 0;
    queue[rear++] = root;
    queue[rear++] = NULL;  /* NULL sentinel marks end of level */

    while (front < rear) {
        Node *n = queue[front++];
        if (!n) {
            printf("\n");
            if (front < rear) queue[rear++] = NULL;
        } else {
            printf("%d ", n->val);
            if (n->l) queue[rear++] = n->l;
            if (n->r) queue[rear++] = n->r;
        }
    }
    free(queue);
}

/* ─── ZIGZAG LEVEL ORDER ────────────────────────────────────────── */
/*
 * Level 0: L→R, Level 1: R→L, Level 2: L→R, ...
 * Use a deque or two stacks alternating direction.
 */
void zigzag_levelorder(Node *root) {
    if (!root) return;
    Node **curr_level = malloc(10000 * sizeof(Node*));
    Node **next_level = malloc(10000 * sizeof(Node*));
    int curr_top = 0, next_top = 0;
    bool left_to_right = true;

    curr_level[curr_top++] = root;
    while (curr_top > 0) {
        next_top = 0;
        for (int i = 0; i < curr_top; i++) {
            Node *n = curr_level[i];
            printf("%d ", n->val);
            if (left_to_right) {
                if (n->l) next_level[next_top++] = n->l;
                if (n->r) next_level[next_top++] = n->r;
            } else {
                if (n->r) next_level[next_top++] = n->r;
                if (n->l) next_level[next_top++] = n->l;
            }
        }
        printf("\n");
        Node **tmp = curr_level; curr_level = next_level; next_level = tmp;
        curr_top = next_top;
        left_to_right = !left_to_right;
    }
    free(curr_level); free(next_level);
}

/* Helper to build test tree */
Node *mk(int v, Node *l, Node *r) {
    Node *n = malloc(sizeof(Node)); n->val=v; n->l=l; n->r=r; return n;
}

int main(void) {
    /*      4
           / \
          2   6
         / \ / \
        1  3 5  7     */
    Node *root = mk(4,
        mk(2, mk(1,NULL,NULL), mk(3,NULL,NULL)),
        mk(6, mk(5,NULL,NULL), mk(7,NULL,NULL)));

    printf("Iterative in-order:   "); inorder_iter(root);
    printf("Iterative pre-order:  "); preorder_iter(root);
    printf("Iterative post-order: "); postorder_iter(root);
    printf("Morris in-order:      "); morris_inorder(root);
    printf("Level-order by level:\n"); levelorder_levels(root);
    printf("Zigzag:\n"); zigzag_levelorder(root);

    return 0;
}
```

---

## 15. Tree Serialization & Deserialization

Converting a tree to/from a string representation. Used in databases, network protocols, LeetCode problems, and distributed systems.

### Methods

1. **Pre-order with null markers:** `"4,2,1,#,#,3,#,#,6,5,#,#,7,#,#"` — unique, lossless.
2. **Level-order (BFS) with null markers:** Used by LeetCode.
3. **In-order alone:** Not unique (same in-order, different tree shapes).
4. **Pre-order + in-order:** Together uniquely determine the tree (O(n²) naive, O(n) with hashmap).

---

### C Implementation — Serialize/Deserialize (Pre-order)

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct TNode { int val; struct TNode *l, *r; } TNode;

TNode *tnode_new(int v) {
    TNode *n = malloc(sizeof(TNode)); n->val=v; n->l=n->r=NULL; return n;
}

/* ─── SERIALIZE to string ────────────────────────────────────────── */
/* Returns a heap-allocated string. Caller must free. */
char *serialize(TNode *root) {
    static char buf[100000];
    static int pos;
    pos = 0;

    void ser(TNode *node) {
        if (!node) { pos += sprintf(buf+pos, "#,"); return; }
        pos += sprintf(buf+pos, "%d,", node->val);
        ser(node->l);
        ser(node->r);
    }
    ser(root);
    if (pos > 0) buf[pos-1] = '\0';  /* remove trailing comma */
    char *result = strdup(buf);
    return result;
}

/* ─── DESERIALIZE from string ──────────────────────────────────────── */
TNode *deserialize(char *data) {
    char *saveptr;
    char *copy = strdup(data);
    char *token = strtok_r(copy, ",", &saveptr);

    TNode *des(void) {
        if (!token || strcmp(token, "#") == 0) {
            token = strtok_r(NULL, ",", &saveptr);
            return NULL;
        }
        TNode *node = tnode_new(atoi(token));
        token = strtok_r(NULL, ",", &saveptr);
        node->l = des();
        node->r = des();
        return node;
    }

    TNode *root = des();
    free(copy);
    return root;
}

void inorder_print(TNode *root) {
    if (!root) return;
    inorder_print(root->l);
    printf("%d ", root->val);
    inorder_print(root->r);
}

int main(void) {
    TNode *root = tnode_new(4);
    root->l = tnode_new(2); root->r = tnode_new(6);
    root->l->l = tnode_new(1); root->l->r = tnode_new(3);
    root->r->l = tnode_new(5); root->r->r = tnode_new(7);

    char *s = serialize(root);
    printf("Serialized: %s\n", s);

    TNode *rebuilt = deserialize(s);
    printf("Deserialized in-order: "); inorder_print(rebuilt); printf("\n");
    free(s);
    return 0;
}
```

---

## 16. LCA: Lowest Common Ancestor

The **LCA** of nodes u and v in a rooted tree is the deepest node that is an ancestor of both.

### LCA Algorithms

| Algorithm | Preprocessing | Query | Space |
|-----------|--------------|-------|-------|
| Naive (walk up) | O(1) | O(n) | O(1) |
| Binary Lifting | O(n log n) | O(log n) | O(n log n) |
| Euler Tour + Range Min | O(n log n) or O(n) | O(1) | O(n) |
| Farach-Colton-Bender | O(n) | O(1) | O(n) |

### Binary Lifting (Most Common in Practice)

Precompute: `anc[v][k]` = the 2^k-th ancestor of v.

Base case: `anc[v][0] = parent[v]`  
Recurrence: `anc[v][k] = anc[anc[v][k-1]][k-1]`

To find LCA(u, v):
1. Ensure `depth[u] ≥ depth[v]`. If not, swap.
2. Lift `u` up by `depth[u] - depth[v]` levels (binary lifting).
3. If `u == v`, return u (v was ancestor of u).
4. Lift both u and v simultaneously to the highest level where they differ.
5. Return `anc[u][0]` (their common parent).

---

### C Implementation — LCA with Binary Lifting

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define MAXN  100005
#define LOG   17   /* ceil(log2(MAXN)) */

int anc[MAXN][LOG];  /* anc[v][k] = 2^k-th ancestor of v */
int depth[MAXN];
int *adj[MAXN];      /* adjacency list */
int adj_size[MAXN];
int n;

void add_edge(int u, int v) {
    adj[u] = realloc(adj[u], (adj_size[u]+1) * sizeof(int));
    adj[u][adj_size[u]++] = v;
    adj[v] = realloc(adj[v], (adj_size[v]+1) * sizeof(int));
    adj[v][adj_size[v]++] = u;
}

/* ─── DFS to set up anc[v][0] and depth[v] ─────────────────────── */
void dfs(int v, int parent, int d) {
    anc[v][0] = parent;
    depth[v]  = d;
    for (int i = 0; i < adj_size[v]; i++) {
        if (adj[v][i] != parent)
            dfs(adj[v][i], v, d+1);
    }
}

/* ─── PRECOMPUTE binary lifting table ───────────────────────────── */
void precompute(int root) {
    dfs(root, root, 0);
    for (int k = 1; k < LOG; k++)
        for (int v = 1; v <= n; v++)
            anc[v][k] = anc[anc[v][k-1]][k-1];
}

/* ─── LCA QUERY ──────────────────────────────────────────────────── */
int lca(int u, int v) {
    /* Ensure u is deeper */
    if (depth[u] < depth[v]) { int t = u; u = v; v = t; }

    /* Lift u to same depth as v */
    int diff = depth[u] - depth[v];
    for (int k = 0; k < LOG; k++)
        if ((diff >> k) & 1) u = anc[u][k];

    if (u == v) return u;

    /* Lift both until one step below LCA */
    for (int k = LOG-1; k >= 0; k--)
        if (anc[u][k] != anc[v][k]) {
            u = anc[u][k];
            v = anc[v][k];
        }

    return anc[u][0];  /* parent of u (or v) is the LCA */
}

/* ─── DISTANCE between two nodes ────────────────────────────────── */
int dist(int u, int v) {
    return depth[u] + depth[v] - 2 * depth[lca(u, v)];
}

int main(void) {
    n = 8;
    /* Build tree:
     *        1
     *       / \
     *      2   3
     *     / \   \
     *    4   5   6
     *   / \
     *  7   8
     */
    add_edge(1,2); add_edge(1,3);
    add_edge(2,4); add_edge(2,5);
    add_edge(3,6);
    add_edge(4,7); add_edge(4,8);

    precompute(1);

    printf("LCA(7,8) = %d\n", lca(7,8)); /* 4 */
    printf("LCA(7,5) = %d\n", lca(7,5)); /* 2 */
    printf("LCA(7,6) = %d\n", lca(7,6)); /* 1 */
    printf("dist(7,6) = %d\n", dist(7,6)); /* 4 */

    /* Cleanup */
    for (int i = 1; i <= n; i++) free(adj[i]);
    return 0;
}
```

---

## 17. Tree DP & Advanced Algorithms

### Tree DP Fundamentals

Tree DP solves optimization problems on trees using DFS. Standard pattern:

```
dp[v] = combine(dp[child1], dp[child2], ..., dp[childk], v.value)
```

The key idea: compute DP values bottom-up during post-order DFS.

### Classic Tree DP Problems

**1. Maximum Path Sum:**
At each node, compute:
- `gain_from_v` = `v.val + max(0, max(gain_from_left, gain_from_right))`
- `max_path_through_v` = `v.val + max(0, gain_from_left) + max(0, gain_from_right)`

**2. Tree Diameter:**
The diameter is the longest path between any two leaves.
- At each node: `diam = max_depth(left) + max_depth(right) + 1`
- Track global maximum.

**3. Maximum Independent Set (MIS):**
- `dp[v][0]` = max sum of independent set in subtree(v) where v is NOT included
- `dp[v][1]` = max sum where v IS included
- `dp[v][0] = Σ max(dp[child][0], dp[child][1])` — children can be anything
- `dp[v][1] = v.val + Σ dp[child][0]` — children cannot be included

**4. Rerooting / All-Roots DP:**
Compute answer for every node as the root without re-running DFS n times.
- First DFS: compute subtree results downward.
- Second DFS: propagate "upper" results downward to complete each node's answer.

---

### C Implementation — Tree DP (Diameter, MIS, Max Path Sum)

```c
#include <stdio.h>
#include <stdlib.h>

#define MAXN 100005
#define NEGINF -1000000000

typedef struct { int to, next; } Edge;
Edge edges[2*MAXN];
int head[MAXN], edge_cnt;
int val[MAXN];
int dp0[MAXN], dp1[MAXN];  /* MIS dp */
int diameter;
int max_path_sum;

void add_edge_dp(int u, int v) {
    edges[edge_cnt] = (Edge){v, head[u]};
    head[u] = edge_cnt++;
    edges[edge_cnt] = (Edge){u, head[v]};
    head[v] = edge_cnt++;
}

/* ─── DIAMETER ───────────────────────────────────────────────────── */
int dfs_diameter(int v, int parent) {
    int max1 = 0, max2 = 0;  /* top two depths */
    for (int e = head[v]; e != -1; e = edges[e].next) {
        int u = edges[e].to;
        if (u == parent) continue;
        int d = 1 + dfs_diameter(u, v);
        if (d > max1)       { max2 = max1; max1 = d; }
        else if (d > max2)  { max2 = d; }
    }
    if (max1 + max2 > diameter) diameter = max1 + max2;
    return max1;
}

/* ─── MAX INDEPENDENT SET ────────────────────────────────────────── */
void dfs_mis(int v, int parent) {
    dp0[v] = 0;
    dp1[v] = val[v];
    for (int e = head[v]; e != -1; e = edges[e].next) {
        int u = edges[e].to;
        if (u == parent) continue;
        dfs_mis(u, v);
        dp0[v] += (dp0[u] > dp1[u] ? dp0[u] : dp1[u]);
        dp1[v] += dp0[u];
    }
}

/* ─── MAX PATH SUM ───────────────────────────────────────────────── */
int dfs_path(int v, int parent) {
    int max_gain = 0;  /* if all paths are negative, gain = 0 (skip subtree) */
    int top1 = 0, top2 = 0;

    for (int e = head[v]; e != -1; e = edges[e].next) {
        int u = edges[e].to;
        if (u == parent) continue;
        int gain = dfs_path(u, v);
        if (gain > max_gain) max_gain = gain;
        /* Track top 2 gains for path through this node */
        if (gain > top1)       { top2 = top1; top1 = gain; }
        else if (gain > top2)  { top2 = gain; }
    }

    int path_here = val[v] + top1 + top2;
    if (path_here > max_path_sum) max_path_sum = path_here;

    return val[v] + max_gain > 0 ? val[v] + max_gain : 0;
}

int main(void) {
    int n = 7;
    memset(head, -1, sizeof(head));
    edge_cnt = 0;

    /* Tree:  1-2, 1-3, 2-4, 2-5, 3-6, 3-7 */
    add_edge_dp(1,2); add_edge_dp(1,3);
    add_edge_dp(2,4); add_edge_dp(2,5);
    add_edge_dp(3,6); add_edge_dp(3,7);

    /* Diameter */
    diameter = 0;
    dfs_diameter(1, -1);
    printf("Diameter: %d\n", diameter);  /* 4 (e.g., 4-2-1-3-6) */

    /* MIS — node values */
    for (int i = 1; i <= n; i++) val[i] = i;
    dfs_mis(1, -1);
    int mis = dp0[1] > dp1[1] ? dp0[1] : dp1[1];
    printf("MIS value: %d\n", mis);

    /* Max path sum — assign weights */
    int weights[] = {0, -3, 2, 4, 5, -1, 3, 2};
    for (int i = 1; i <= n; i++) val[i] = weights[i];
    max_path_sum = NEGINF;
    dfs_path(1, -1);
    printf("Max path sum: %d\n", max_path_sum);

    return 0;
}
```

---

## 18. Complexity Cheat Sheet

### Per-Operation Complexity

| Tree Type | Search | Insert | Delete | Space | Notes |
|-----------|--------|--------|--------|-------|-------|
| Binary Tree (generic) | O(n) | O(n) | O(n) | O(n) | No ordering |
| BST (average) | O(log n) | O(log n) | O(log n) | O(n) | Degenerate O(n) |
| BST (worst) | O(n) | O(n) | O(n) | O(n) | Sorted input |
| AVL Tree | O(log n) | O(log n) | O(log n) | O(n) | Height ≤ 1.44 log n |
| Red-Black Tree | O(log n) | O(log n) | O(log n) | O(n) | Height ≤ 2 log n |
| B-Tree (order m) | O(log_m n) | O(log_m n) | O(log_m n) | O(n) | Disk-optimized |
| Min/Max Heap | O(n) search | O(log n) | O(log n) | O(n) | O(1) peek |
| Heap build | — | — | — | O(n) | From array |
| Trie | O(m) | O(m) | O(m) | O(ALPHA * n * m) | m = key length |
| Segment Tree | — | O(log n) update | — | O(4n) | O(log n) range query |
| Fenwick Tree | — | O(log n) | — | O(n) | O(log n) prefix query |

### Traversal Complexity

| Traversal | Time | Space (recursive) | Space (iterative) | Space (Morris) |
|-----------|------|-------------------|--------------------|----------------|
| In-order | O(n) | O(h) | O(h) | O(1) |
| Pre-order | O(n) | O(h) | O(h) | O(1) |
| Post-order | O(n) | O(h) | O(h) | O(1) |
| Level-order | O(n) | — | O(w) (width) | — |

h = tree height, w = tree width.

### When to Choose Which Tree

| Use Case | Recommended |
|----------|-------------|
| General sorted dictionary, in-memory | Red-Black Tree (`std::map`, `TreeMap`) |
| Read-heavy, tight height bound | AVL Tree |
| Priority queue | Binary Heap |
| Prefix search, autocomplete | Trie / Radix Tree |
| Disk storage, database index | B+ Tree |
| Range sum/min/max query | Segment Tree |
| Count inversions, range sum (no range update) | Fenwick Tree |
| Network routing (IP prefix match) | Radix Tree / Patricia Trie |
| k-dimensional nearest neighbor | k-d Tree |
| Union-Find, connected components | DSU / Union-Find |
| Interval overlap queries | Interval Tree / Segment Tree |

### Space-Time Tradeoffs

- **AVL vs RB:** AVL maintains stricter balance (shorter tree) at the cost of more rotations. For n=1M, AVL height ≤ 29, RB height ≤ 40. In practice, cache effects often matter more.
- **Segment Tree vs Fenwick:** Segment tree uses 4× more memory but supports arbitrary associative queries (including min/max). Fenwick's constant factor is ~5× smaller.
- **Trie vs Hash Table:** Trie supports prefix queries and lexicographic iteration; hash table is O(1) lookup but no ordering.
- **B-Tree order selection:** Order 100–1000 minimizes I/O for disk storage. In-memory, order 32–64 maximizes cache line utilization.

---

*End of The Complete Tree Data Structures Guide.*
*Languages: C · Go · Rust | Scope: BST, AVL, Red-Black, B-Tree, Heap, Trie, Segment Tree, Fenwick Tree, Traversals, LCA, Tree DP, Serialization.*