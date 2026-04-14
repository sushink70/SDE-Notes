# 🌳 The Complete Guide to Building Trees in DSA
### From Foundations to Advanced Constructions — C, Go & Rust

---

> *"A tree is not just a data structure. It is a recursion made visible — a hierarchy encoded in memory. Every problem involving hierarchy, ordering, or recursive decomposition collapses into a tree."*

---

## TABLE OF CONTENTS

1. [What Is a Tree? — The Mental Model](#1-what-is-a-tree--the-mental-model)
2. [Core Terminology — Every Word Defined](#2-core-terminology--every-word-defined)
3. [Tree Properties — Mathematical Foundations](#3-tree-properties--mathematical-foundations)
4. [The 5 Ways to REPRESENT a Tree in Memory](#4-the-5-ways-to-represent-a-tree-in-memory)
   - 4.1 Linked Node (Pointer-Based)
   - 4.2 Array-Based (Index Arithmetic)
   - 4.3 Parent Array
   - 4.4 Adjacency List
   - 4.5 Left-Child Right-Sibling (LCRS)
5. [Types of Trees — Taxonomy and Construction](#5-types-of-trees--taxonomy-and-construction)
   - 5.1 General / N-ary Tree
   - 5.2 Binary Tree (Free-Form)
   - 5.3 Binary Search Tree (BST)
   - 5.4 AVL Tree (Height-Balanced BST)
   - 5.5 Red-Black Tree
   - 5.6 Min-Heap & Max-Heap
   - 5.7 Trie (Prefix Tree)
   - 5.8 Segment Tree
   - 5.9 Fenwick Tree (Binary Indexed Tree)
   - 5.10 B-Tree
   - 5.11 Expression Tree
   - 5.12 Huffman Tree
   - 5.13 Cartesian Tree
   - 5.14 Treap
   - 5.15 Splay Tree (Concept)
   - 5.16 Suffix Tree / Suffix Array
6. [Tree Construction Algorithms](#6-tree-construction-algorithms)
   - 6.1 From Level-Order (BFS Array)
   - 6.2 From Inorder + Preorder Traversals
   - 6.3 From Inorder + Postorder Traversals
   - 6.4 From Sorted Array → Balanced BST
   - 6.5 From Parent Array
   - 6.6 From Expression (Shunting-Yard)
7. [Traversal Methods — Reading the Tree](#7-traversal-methods)
8. [Cognitive Mastery Map — Mental Models](#8-cognitive-mastery-map)

---

## 1. What Is a Tree? — The Mental Model

### The Intuition

A **tree** is a connected, acyclic undirected graph. In computer science, we root it — we pick one node as the **root** and all edges flow downward from it.

Think of it this way:

```
REAL WORLD → TREE MAPPING
─────────────────────────────────────────────────────────
File system          → Directories are nodes, files are leaves
Company hierarchy    → CEO is root, employees are nodes
HTML DOM             → <html> is root, tags are nodes
Arithmetic expr      → Operators are internal, operands are leaves
Decision making      → Questions are internal nodes, answers are leaves
DNA phylogeny        → Common ancestor is root
```

### The Recursive Definition (Most Powerful Mental Model)

> **A tree is either:**
> 1. **Empty** (null/nil), OR
> 2. **A root node** connected to zero or more **subtrees** (each of which is itself a tree)

This recursive definition is the master key. Every tree algorithm you will ever write exploits this structure.

```
T = ∅   OR   T = (root, T₁, T₂, ..., Tₖ)
              where each Tᵢ is itself a tree
```

---

## 2. Core Terminology — Every Word Defined

Every term you encounter, defined precisely.

```
         A              ← ROOT (topmost node, has no parent)
        / \
       B   C            ← B and C are CHILDREN of A
      / \   \           ← A is PARENT of B and C
     D   E   F          ← D, E, F are LEAF NODES (no children)
```

| Term | Definition | Example Above |
|------|-----------|---------------|
| **Node** | A single element holding data | A, B, C, D, E, F |
| **Root** | The topmost node; has no parent | A |
| **Leaf / External Node** | A node with NO children | D, E, F |
| **Internal Node** | A node WITH at least one child | A, B, C |
| **Parent** | Direct ancestor of a node | A is parent of B |
| **Child** | Direct descendant of a node | B, C are children of A |
| **Sibling** | Nodes sharing the same parent | B and C are siblings |
| **Ancestor** | Any node on path from root to a node | A, B are ancestors of D |
| **Descendant** | Any node in the subtree below a node | B, D, E are descendants of A |
| **Subtree** | A node + all its descendants | B's subtree = {B, D, E} |
| **Edge** | Connection between parent and child | A-B, A-C, B-D, etc. |
| **Path** | Sequence of nodes from X to Y | A → B → D |
| **Depth of node** | Number of edges from root to that node | depth(D) = 2 |
| **Height of node** | Longest path from that node to a leaf | height(A) = 2 |
| **Height of tree** | Height of the root node | 2 |
| **Level** | All nodes at same depth | Level 0={A}, Level 1={B,C} |
| **Degree** | Number of children a node has | degree(B) = 2, degree(C) = 1 |
| **Forest** | Collection of disjoint trees | Remove A → forest {B-tree, C-tree} |

### Additional Terms for BST and Advanced Trees

| Term | Definition |
|------|-----------|
| **Key** | The value used for comparisons/ordering |
| **Predecessor** | The node with the largest key less than X (in BST, inorder predecessor) |
| **Successor** | The node with the smallest key greater than X (in BST, inorder successor) |
| **Balance Factor** | height(left subtree) - height(right subtree) |
| **Pivot** | The node around which rotation occurs in AVL/RB trees |
| **Sentinel** | A dummy nil node used in RB trees to simplify edge cases |
| **Prefix** | A string formed by the first k characters of another string (used in Tries) |
| **Suffix** | A string formed by the last k characters (used in Suffix Trees) |
| **Infix / Inorder** | Visit left, root, right |
| **Prefix / Preorder** | Visit root, left, right |
| **Postfix / Postorder** | Visit left, right, root |

---

## 3. Tree Properties — Mathematical Foundations

Understanding these mathematically will make you faster at estimating complexity.

### For any tree with N nodes:
- **Edges = N - 1** (trees are minimally connected)
- **Exactly one path** between any two nodes

### For a Binary Tree:
- Maximum nodes at level L = **2^L**
- Maximum nodes in tree of height H = **2^(H+1) - 1**
- Minimum height for N nodes = **⌊log₂(N)⌋**

```
HEIGHT vs NODES (Binary Tree):
Height 0: max 1 node     (just root)
Height 1: max 3 nodes    (root + 2 children)
Height 2: max 7 nodes
Height 3: max 15 nodes
Height H: max 2^(H+1)-1 nodes

CONVERSELY:
N=1 million nodes → minimum height = log₂(1,000,000) ≈ 20

This is WHY balanced trees are so powerful!
```

### Structural Varieties:

```
FULL Binary Tree:        Every node has 0 or 2 children
       A
      / \
     B   C
    / \
   D   E

COMPLETE Binary Tree:    All levels filled except possibly last;
                         last level filled left-to-right
       A
      / \
     B   C
    / \  /
   D   E F

PERFECT Binary Tree:     All internal nodes have 2 children;
                         all leaves at same level
       A
      / \
     B   C
    / \ / \
   D  E F  G

DEGENERATE/Skewed Tree:  Every node has 1 child (basically a linked list)
   A
    \
     B
      \
       C
```

---

## 4. The 5 Ways to REPRESENT a Tree in Memory

This is the most fundamental question: **how do you store a tree?** There are 5 main strategies, each with different trade-offs.

---

### 4.1 Linked Node (Pointer-Based)

The most natural representation. Each node is a struct/record containing data and pointers to children.

**Mental Model:** Like a physical tree — each branch points to its sub-branches.

```
STRUCTURE:
┌──────────┐      ┌──────────┐
│  data: 1 │─────>│  data: 2 │
│  left ───┘      │  left: ∅ │
│  right ──┐      │  right:∅ │
└──────────┘      └──────────┘
           │      ┌──────────┐
           └─────>│  data: 3 │
                  │  left: ∅ │
                  │  right:∅ │
                  └──────────┘
```

**Trade-offs:**
- ✅ Natural for recursive algorithms
- ✅ Dynamic size — grow/shrink freely
- ✅ Works for any tree shape
- ❌ Memory overhead per node (pointer storage)
- ❌ Cache-unfriendly (nodes scattered in heap)

#### Implementation — Binary Tree Node

**C:**
```c
#include <stdio.h>
#include <stdlib.h>

typedef struct BinaryNode {
    int data;
    struct BinaryNode *left;
    struct BinaryNode *right;
} BinaryNode;

// Allocate a new node
BinaryNode *new_node(int data) {
    BinaryNode *node = (BinaryNode *)malloc(sizeof(BinaryNode));
    if (!node) {
        fprintf(stderr, "Memory allocation failed\n");
        exit(EXIT_FAILURE);
    }
    node->data  = data;
    node->left  = NULL;
    node->right = NULL;
    return node;
}

// Build a small tree manually:
//       1
//      / \
//     2   3
//    / \
//   4   5
BinaryNode *build_sample_tree(void) {
    BinaryNode *root  = new_node(1);
    root->left        = new_node(2);
    root->right       = new_node(3);
    root->left->left  = new_node(4);
    root->left->right = new_node(5);
    return root;
}

// Inorder traversal: Left → Root → Right
// For a BST this prints sorted order
void inorder(BinaryNode *node) {
    if (node == NULL) return;
    inorder(node->left);
    printf("%d ", node->data);
    inorder(node->right);
}

// Free all nodes (post-order deletion)
void free_tree(BinaryNode *node) {
    if (node == NULL) return;
    free_tree(node->left);
    free_tree(node->right);
    free(node);
}

int main(void) {
    BinaryNode *root = build_sample_tree();
    printf("Inorder: ");
    inorder(root);   // Output: 4 2 5 1 3
    printf("\n");
    free_tree(root);
    return 0;
}
```

**Go:**
```go
package main

import "fmt"

// TreeNode is the fundamental building block
type TreeNode struct {
    Data  int
    Left  *TreeNode
    Right *TreeNode
}

// NewNode creates a leaf node
func NewNode(data int) *TreeNode {
    return &TreeNode{Data: data}
}

// BuildSampleTree constructs:
//       1
//      / \
//     2   3
//    / \
//   4   5
func BuildSampleTree() *TreeNode {
    root := NewNode(1)
    root.Left = NewNode(2)
    root.Right = NewNode(3)
    root.Left.Left = NewNode(4)
    root.Left.Right = NewNode(5)
    return root
}

// Inorder: Left → Root → Right
func Inorder(node *TreeNode) {
    if node == nil {
        return
    }
    Inorder(node.Left)
    fmt.Printf("%d ", node.Data)
    Inorder(node.Right)
}

func main() {
    root := BuildSampleTree()
    fmt.Print("Inorder: ")
    Inorder(root) // Output: 4 2 5 1 3
    fmt.Println()
}
```

**Rust:**
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

> **Why `Box<T>` in Rust?**
> Rust needs to know the size of every type at compile time. A `TreeNode` containing a `TreeNode` directly would be infinitely sized. `Box<T>` is a fixed-size pointer to heap memory, breaking the recursion.

---

### 4.2 Array-Based (Index Arithmetic)

For a **complete binary tree**, we can store nodes in a flat array using the following index mapping:

```
ARRAY INDEX → TREE POSITION
─────────────────────────────
Index:    0   1   2   3   4   5   6
Array: [  A   B   C   D   E   F   G ]

Tree:
            A (0)
           / \
         B(1) C(2)
        / \ / \
      D(3)E(4)F(5)G(6)

FORMULA (0-indexed):
  Parent of node i   = (i - 1) / 2
  Left child of i    = 2*i + 1
  Right child of i   = 2*i + 2

FORMULA (1-indexed, used in heaps):
  Parent of node i   = i / 2
  Left child of i    = 2*i
  Right child of i   = 2*i + 1
```

**Trade-offs:**
- ✅ Cache-friendly (contiguous memory)
- ✅ O(1) parent/child lookup via arithmetic
- ✅ No pointer overhead
- ❌ Only efficient for complete/near-complete trees
- ❌ Sparse trees waste enormous space

**C:**
```c
#include <stdio.h>
#include <stdlib.h>

#define MAX_SIZE 128

typedef struct {
    int data[MAX_SIZE];
    int size;  // number of nodes
} ArrayTree;

void array_tree_init(ArrayTree *t) {
    t->size = 0;
}

// Insert into next available position (like a heap push — no ordering here)
void array_tree_insert(ArrayTree *t, int val) {
    if (t->size >= MAX_SIZE) return;
    t->data[t->size++] = val;
}

int parent(int i)      { return (i - 1) / 2; }
int left_child(int i)  { return 2 * i + 1;   }
int right_child(int i) { return 2 * i + 2;   }

// BFS-order print (just printing the array)
void print_level_order(ArrayTree *t) {
    for (int i = 0; i < t->size; i++) {
        printf("%d ", t->data[i]);
    }
    printf("\n");
}

// Inorder traversal using index arithmetic (recursive)
void inorder_array(int *arr, int i, int size) {
    if (i >= size) return;
    inorder_array(arr, left_child(i), size);
    printf("%d ", arr[i]);
    inorder_array(arr, right_child(i), size);
}

int main(void) {
    ArrayTree t;
    array_tree_init(&t);

    // Build:      1
    //            / \
    //           2   3
    //          / \
    //         4   5
    int vals[] = {1, 2, 3, 4, 5};
    for (int i = 0; i < 5; i++) array_tree_insert(&t, vals[i]);

    printf("Level-order: ");
    print_level_order(&t);  // 1 2 3 4 5

    printf("Inorder: ");
    inorder_array(t.data, 0, t.size);  // 4 2 5 1 3
    printf("\n");

    printf("Parent of index 3: %d\n", t.data[parent(3)]);  // 2
    printf("Left child of index 1: %d\n", t.data[left_child(1)]);  // 4

    return 0;
}
```

**Go:**
```go
package main

import "fmt"

type ArrayTree struct {
    Data []int
}

func NewArrayTree(vals []int) *ArrayTree {
    t := &ArrayTree{Data: make([]int, len(vals))}
    copy(t.Data, vals)
    return t
}

func parent(i int) int     { return (i - 1) / 2 }
func leftChild(i int) int  { return 2*i + 1 }
func rightChild(i int) int { return 2*i + 2 }

func (t *ArrayTree) Inorder(i int) {
    if i >= len(t.Data) {
        return
    }
    t.Inorder(leftChild(i))
    fmt.Printf("%d ", t.Data[i])
    t.Inorder(rightChild(i))
}

func main() {
    // Array stores level-order (BFS) sequence:
    //      1
    //     / \
    //    2   3
    //   / \
    //  4   5
    t := NewArrayTree([]int{1, 2, 3, 4, 5})

    fmt.Print("Inorder: ")
    t.Inorder(0)   // 4 2 5 1 3
    fmt.Println()

    fmt.Printf("Parent of index 3 (val %d): %d\n",
        t.Data[3], t.Data[parent(3)]) // val=4, parent=2
}
```

**Rust:**
```rust
struct ArrayTree {
    data: Vec<i32>,
}

impl ArrayTree {
    fn new(vals: Vec<i32>) -> Self {
        ArrayTree { data: vals }
    }

    fn parent(i: usize) -> usize     { (i.saturating_sub(1)) / 2 }
    fn left_child(i: usize) -> usize { 2 * i + 1 }
    fn right_child(i: usize) -> usize{ 2 * i + 2 }

    fn inorder(&self, i: usize) {
        if i >= self.data.len() {
            return;
        }
        self.inorder(Self::left_child(i));
        print!("{} ", self.data[i]);
        self.inorder(Self::right_child(i));
    }
}

fn main() {
    //      1
    //     / \
    //    2   3
    //   / \
    //  4   5
    let t = ArrayTree::new(vec![1, 2, 3, 4, 5]);

    print!("Inorder: ");
    t.inorder(0); // 4 2 5 1 3
    println!();

    let i = 3usize; // node with value 4
    println!(
        "Parent of index {} (val {}): {}",
        i, t.data[i], t.data[ArrayTree::parent(i)]
    );
}
```

---

### 4.3 Parent Array

Store only the parent index for each node. The root has parent = -1 (or itself).

```
EXAMPLE:
Nodes:    0  1  2  3  4  5  6
Parent:  -1  0  0  1  1  2  2
          ↑  ↑  ↑
        root  1,2 are children of 0
                 3,4 are children of 1
                    5,6 are children of 2

This represents:
        0
       / \
      1   2
     / \ / \
    3  4 5  6
```

**When to use:** Edge lists, union-find, tree problems given as flat arrays.

**C:**
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAXN 100

// Build an adjacency-list tree from a parent array
// Then do a DFS to find children
void build_from_parent(int *parent, int n) {
    // children[i] stores list of children of node i
    int children[MAXN][MAXN];
    int child_count[MAXN];
    memset(child_count, 0, sizeof(child_count));

    int root = -1;
    for (int i = 0; i < n; i++) {
        if (parent[i] == -1) {
            root = i;
        } else {
            children[parent[i]][child_count[parent[i]]++] = i;
        }
    }

    // BFS to print level-order
    int queue[MAXN], front = 0, back = 0;
    queue[back++] = root;
    printf("Level-order from parent array: ");
    while (front < back) {
        int node = queue[front++];
        printf("%d ", node);
        for (int i = 0; i < child_count[node]; i++) {
            queue[back++] = children[node][i];
        }
    }
    printf("\n");
}

int main(void) {
    int parent[] = {-1, 0, 0, 1, 1, 2, 2};
    int n = 7;
    build_from_parent(parent, n);
    // Output: 0 1 2 3 4 5 6
    return 0;
}
```

**Go:**
```go
package main

import "fmt"

func buildFromParentArray(parent []int) {
    n := len(parent)
    children := make([][]int, n)
    root := -1

    for i, p := range parent {
        if p == -1 {
            root = i
        } else {
            children[p] = append(children[p], i)
        }
    }

    // BFS
    queue := []int{root}
    fmt.Print("Level-order: ")
    for len(queue) > 0 {
        node := queue[0]
        queue = queue[1:]
        fmt.Printf("%d ", node)
        queue = append(queue, children[node]...)
    }
    fmt.Println()
}

func main() {
    //      0
    //     / \
    //    1   2
    //   / \ / \
    //  3  4 5  6
    parent := []int{-1, 0, 0, 1, 1, 2, 2}
    buildFromParentArray(parent) // 0 1 2 3 4 5 6
}
```

**Rust:**
```rust
use std::collections::VecDeque;

fn build_from_parent_array(parent: &[i32]) {
    let n = parent.len();
    let mut children: Vec<Vec<usize>> = vec![vec![]; n];
    let mut root = 0usize;

    for (i, &p) in parent.iter().enumerate() {
        if p == -1 {
            root = i;
        } else {
            children[p as usize].push(i);
        }
    }

    // BFS
    let mut queue = VecDeque::new();
    queue.push_back(root);
    print!("Level-order: ");
    while let Some(node) = queue.pop_front() {
        print!("{} ", node);
        for &child in &children[node] {
            queue.push_back(child);
        }
    }
    println!();
}

fn main() {
    //       0
    //      / \
    //     1   2
    //    / \ / \
    //   3  4 5  6
    let parent: Vec<i32> = vec![-1, 0, 0, 1, 1, 2, 2];
    build_from_parent_array(&parent); // 0 1 2 3 4 5 6
}
```

---

### 4.4 Adjacency List

Represent the tree as a graph: each node has a list of its neighbors. For a rooted tree, we either store parent separately or avoid traversing back to parent.

```
Node 0: [1, 2]
Node 1: [0, 3, 4]   ← 0 is parent, 3,4 are children
Node 2: [0, 5, 6]
Node 3: [1]
Node 4: [1]
Node 5: [2]
Node 6: [2]
```

**When to use:** When tree is given as edge list (e.g., Leetcode "N-ary Tree" problems, graph-based tree problems).

**C:**
```c
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

#define MAXN 100

int adj[MAXN][MAXN];  // adjacency list (simplified with 2D array)
int adj_size[MAXN];
bool visited[MAXN];

void add_edge(int u, int v) {
    adj[u][adj_size[u]++] = v;
    adj[v][adj_size[v]++] = u;
}

// DFS from root, skipping visited (= parent)
void dfs(int node, int depth) {
    visited[node] = true;
    // Print with indentation to show depth
    for (int i = 0; i < depth; i++) printf("  ");
    printf("%d\n", node);
    for (int i = 0; i < adj_size[node]; i++) {
        int neighbor = adj[node][i];
        if (!visited[neighbor]) {
            dfs(neighbor, depth + 1);
        }
    }
}

int main(void) {
    // Build tree:
    //   0
    //  / \
    // 1   2
    // |   |
    // 3   4
    add_edge(0, 1);
    add_edge(0, 2);
    add_edge(1, 3);
    add_edge(2, 4);

    printf("DFS tree structure (root=0):\n");
    dfs(0, 0);
    return 0;
}
```

**Go:**
```go
package main

import "fmt"

type AdjTree struct {
    adj     [][]int
    visited []bool
}

func NewAdjTree(n int) *AdjTree {
    return &AdjTree{
        adj:     make([][]int, n),
        visited: make([]bool, n),
    }
}

func (t *AdjTree) AddEdge(u, v int) {
    t.adj[u] = append(t.adj[u], v)
    t.adj[v] = append(t.adj[v], u)
}

func (t *AdjTree) DFS(node, depth int) {
    t.visited[node] = true
    for i := 0; i < depth; i++ {
        fmt.Print("  ")
    }
    fmt.Println(node)
    for _, neighbor := range t.adj[node] {
        if !t.visited[neighbor] {
            t.DFS(neighbor, depth+1)
        }
    }
}

func main() {
    tree := NewAdjTree(5)
    tree.AddEdge(0, 1)
    tree.AddEdge(0, 2)
    tree.AddEdge(1, 3)
    tree.AddEdge(2, 4)

    fmt.Println("Tree structure:")
    tree.DFS(0, 0)
}
```

**Rust:**
```rust
fn dfs(adj: &[Vec<usize>], node: usize, parent: Option<usize>, depth: usize) {
    let indent = "  ".repeat(depth);
    println!("{}{}", indent, node);
    for &neighbor in &adj[node] {
        if Some(neighbor) != parent {
            dfs(adj, neighbor, Some(node), depth + 1);
        }
    }
}

fn main() {
    let n = 5;
    let mut adj: Vec<Vec<usize>> = vec![vec![]; n];

    let edges = [(0, 1), (0, 2), (1, 3), (2, 4)];
    for &(u, v) in &edges {
        adj[u].push(v);
        adj[v].push(u);
    }

    println!("Tree structure:");
    dfs(&adj, 0, None, 0);
}
```

---

### 4.5 Left-Child Right-Sibling (LCRS)

An elegant way to represent any N-ary tree using only binary node structs. Each node stores:
- A pointer to its **first (leftmost) child**
- A pointer to its **next sibling**

```
ORIGINAL N-ARY TREE:        LCRS REPRESENTATION:
      A                           A
    / | \                        /
   B  C  D                      B → C → D
   |                            |
   E                            E

Node A: left_child = B,  right_sibling = null
Node B: left_child = E,  right_sibling = C
Node C: left_child = null, right_sibling = D
Node D: left_child = null, right_sibling = null
Node E: left_child = null, right_sibling = null
```

**Why is this brilliant?** Any N-ary tree becomes a binary tree, enabling all binary tree algorithms to apply!

**C:**
```c
#include <stdio.h>
#include <stdlib.h>

typedef struct LCRSNode {
    int data;
    struct LCRSNode *first_child;   // leftmost child
    struct LCRSNode *next_sibling;  // next sibling
} LCRSNode;

LCRSNode *lcrs_new(int data) {
    LCRSNode *n = (LCRSNode *)malloc(sizeof(LCRSNode));
    n->data         = data;
    n->first_child  = NULL;
    n->next_sibling = NULL;
    return n;
}

// Add child to parent (appends to sibling list)
void lcrs_add_child(LCRSNode *parent, LCRSNode *child) {
    if (parent->first_child == NULL) {
        parent->first_child = child;
        return;
    }
    // Walk sibling list to end
    LCRSNode *sibling = parent->first_child;
    while (sibling->next_sibling != NULL) {
        sibling = sibling->next_sibling;
    }
    sibling->next_sibling = child;
}

// Preorder DFS
void lcrs_preorder(LCRSNode *node, int depth) {
    if (node == NULL) return;
    for (int i = 0; i < depth; i++) printf("  ");
    printf("%d\n", node->data);
    lcrs_preorder(node->first_child, depth + 1);
    lcrs_preorder(node->next_sibling, depth);  // sibling stays at same depth
}

int main(void) {
    //     A
    //   / | \
    //  B  C  D
    //  |
    //  E
    LCRSNode *A = lcrs_new(1); // A=1
    LCRSNode *B = lcrs_new(2); // B=2
    LCRSNode *C = lcrs_new(3); // C=3
    LCRSNode *D = lcrs_new(4); // D=4
    LCRSNode *E = lcrs_new(5); // E=5

    lcrs_add_child(A, B);
    lcrs_add_child(A, C);
    lcrs_add_child(A, D);
    lcrs_add_child(B, E);

    printf("LCRS Preorder:\n");
    lcrs_preorder(A, 0);
    return 0;
}
```

---

## 5. Types of Trees — Taxonomy and Construction

```
TREE TAXONOMY:
══════════════════════════════════════════════════════
                      TREE
                        │
          ┌─────────────┼─────────────┐
       General        Binary          N-ary
       Tree           Tree            Tree
                        │
          ┌─────────────┼─────────────┐
         BST         Heap           Complete
          │                         Binary Tree
     ┌────┴────┐
    AVL      Red-Black
   Tree        Tree

  SPECIALIZED:
  Trie, Segment Tree, Fenwick Tree, B-Tree,
  Cartesian Tree, Treap, Splay Tree,
  Suffix Tree, Expression Tree, Huffman Tree
══════════════════════════════════════════════════════
```

---

### 5.1 General / N-ary Tree

A tree where each node can have **any number of children**.

```
        CEO
       / | \
     VP1  VP2  VP3
    / \    |
  Mgr1 Mgr2 Mgr3
```

**C:**
```c
#include <stdio.h>
#include <stdlib.h>

#define MAX_CHILDREN 10

typedef struct NAryNode {
    int data;
    struct NAryNode *children[MAX_CHILDREN];
    int child_count;
} NAryNode;

NAryNode *nary_new(int data) {
    NAryNode *node = (NAryNode *)calloc(1, sizeof(NAryNode));
    node->data = data;
    return node;
}

void nary_add_child(NAryNode *parent, NAryNode *child) {
    if (parent->child_count < MAX_CHILDREN) {
        parent->children[parent->child_count++] = child;
    }
}

// DFS preorder
void nary_print(NAryNode *node, int depth) {
    if (!node) return;
    for (int i = 0; i < depth; i++) printf("  ");
    printf("%d\n", node->data);
    for (int i = 0; i < node->child_count; i++) {
        nary_print(node->children[i], depth + 1);
    }
}

int main(void) {
    NAryNode *root = nary_new(1);
    NAryNode *c1   = nary_new(2);
    NAryNode *c2   = nary_new(3);
    NAryNode *c3   = nary_new(4);
    NAryNode *gc1  = nary_new(5);
    NAryNode *gc2  = nary_new(6);

    nary_add_child(root, c1);
    nary_add_child(root, c2);
    nary_add_child(root, c3);
    nary_add_child(c1, gc1);
    nary_add_child(c1, gc2);

    nary_print(root, 0);
    return 0;
}
```

**Go:**
```go
package main

import "fmt"

type NAryNode struct {
    Data     int
    Children []*NAryNode
}

func NewNAry(data int) *NAryNode {
    return &NAryNode{Data: data}
}

func (n *NAryNode) AddChild(child *NAryNode) {
    n.Children = append(n.Children, child)
}

func (n *NAryNode) Print(depth int) {
    fmt.Printf("%s%d\n", indent(depth), n.Data)
    for _, child := range n.Children {
        child.Print(depth + 1)
    }
}

func indent(depth int) string {
    s := ""
    for i := 0; i < depth; i++ {
        s += "  "
    }
    return s
}

func main() {
    root := NewNAry(1)
    c1 := NewNAry(2)
    c2 := NewNAry(3)
    root.AddChild(c1)
    root.AddChild(c2)
    c1.AddChild(NewNAry(4))
    c1.AddChild(NewNAry(5))
    root.Print(0)
}
```

**Rust:**
```rust
#[derive(Debug)]
struct NAryNode {
    data: i32,
    children: Vec<Box<NAryNode>>,
}

impl NAryNode {
    fn new(data: i32) -> Self {
        NAryNode { data, children: vec![] }
    }

    fn add_child(&mut self, child: NAryNode) {
        self.children.push(Box::new(child));
    }

    fn print(&self, depth: usize) {
        println!("{}{}", "  ".repeat(depth), self.data);
        for child in &self.children {
            child.print(depth + 1);
        }
    }
}

fn main() {
    let mut root = NAryNode::new(1);
    let mut c1 = NAryNode::new(2);
    c1.add_child(NAryNode::new(4));
    c1.add_child(NAryNode::new(5));
    root.add_child(c1);
    root.add_child(NAryNode::new(3));
    root.print(0);
}
```

---

### 5.2 Binary Tree (Free-Form)

A binary tree where each node has **at most 2 children**. No ordering constraint. Used as a base for BST, heaps, expression trees, Huffman trees, etc.

Already implemented in Section 4.1. The key insight is:

```
BINARY TREE SHAPES:
─────────────────────────────────────────────────────
Full:     every node has 0 or 2 children
Complete: filled level by level, left to right
Perfect:  all levels fully filled
Balanced: height difference ≤ 1 (AVL property)
Skewed:   degenerate case (linked list behavior)
```

---

### 5.3 Binary Search Tree (BST)

**The ordering invariant (BST Property):**
> For every node X:
> - ALL values in X's **left subtree** are **LESS THAN** X.data
> - ALL values in X's **right subtree** are **GREATER THAN** X.data

```
       8
      / \
     3   10
    / \    \
   1   6    14
      / \   /
     4   7 13

Verify: 3 < 8 ✓   10 > 8 ✓
        1 < 3 ✓   6 is in [3,8) ✓
```

**BST Operations:**
```
INSERT:   Compare and go left/right until null → insert
SEARCH:   Compare and go left/right until found or null
DELETE:   3 cases:
          1. Leaf node → just remove
          2. One child → replace with child
          3. Two children → replace with inorder successor (smallest in right subtree)
```

**ALGORITHM FLOW — BST Insert:**
```
        START: insert(root, key)
                    │
              Is root null?
             YES ──────── NO
              │                │
         Create new         key < root.data?
          node, return      YES ──── NO
                             │           │
                      root.left =    root.right =
                   insert(left,key) insert(right,key)
                             │           │
                         return root  return root
```

**C:**
```c
#include <stdio.h>
#include <stdlib.h>

typedef struct BSTNode {
    int key;
    struct BSTNode *left, *right;
} BSTNode;

BSTNode *bst_new_node(int key) {
    BSTNode *n = (BSTNode *)malloc(sizeof(BSTNode));
    n->key = key; n->left = n->right = NULL;
    return n;
}

// Recursive insert — returns new root
BSTNode *bst_insert(BSTNode *root, int key) {
    if (root == NULL) return bst_new_node(key);
    if (key < root->key)
        root->left  = bst_insert(root->left,  key);
    else if (key > root->key)
        root->right = bst_insert(root->right, key);
    // key == root->key: duplicate, do nothing (or handle as needed)
    return root;
}

// Search: returns node or NULL
BSTNode *bst_search(BSTNode *root, int key) {
    if (root == NULL || root->key == key) return root;
    if (key < root->key) return bst_search(root->left,  key);
    else                 return bst_search(root->right, key);
}

// Find minimum (inorder successor helper)
BSTNode *bst_min(BSTNode *node) {
    while (node->left != NULL) node = node->left;
    return node;
}

// Delete — returns new root
BSTNode *bst_delete(BSTNode *root, int key) {
    if (root == NULL) return NULL;
    if (key < root->key) {
        root->left  = bst_delete(root->left,  key);
    } else if (key > root->key) {
        root->right = bst_delete(root->right, key);
    } else {
        // Found the node to delete
        if (root->left == NULL) {   // Case 1 & 2: no left child
            BSTNode *temp = root->right;
            free(root);
            return temp;
        } else if (root->right == NULL) {  // Case 2: no right child
            BSTNode *temp = root->left;
            free(root);
            return temp;
        }
        // Case 3: two children → find inorder successor
        BSTNode *successor = bst_min(root->right);
        root->key = successor->key;  // copy successor's key
        root->right = bst_delete(root->right, successor->key);
    }
    return root;
}

void inorder(BSTNode *root) {
    if (!root) return;
    inorder(root->left);
    printf("%d ", root->key);
    inorder(root->right);
}

int main(void) {
    BSTNode *root = NULL;
    int keys[] = {8, 3, 10, 1, 6, 14, 4, 7, 13};
    int n = sizeof(keys) / sizeof(keys[0]);

    for (int i = 0; i < n; i++)
        root = bst_insert(root, keys[i]);

    printf("Inorder (sorted): ");
    inorder(root);  // 1 3 4 6 7 8 10 13 14
    printf("\n");

    root = bst_delete(root, 3);
    printf("After deleting 3: ");
    inorder(root);  // 1 4 6 7 8 10 13 14
    printf("\n");

    return 0;
}
```

**Go:**
```go
package main

import "fmt"

type BSTNode struct {
    Key        int
    Left, Right *BSTNode
}

func bstInsert(root *BSTNode, key int) *BSTNode {
    if root == nil {
        return &BSTNode{Key: key}
    }
    if key < root.Key {
        root.Left = bstInsert(root.Left, key)
    } else if key > root.Key {
        root.Right = bstInsert(root.Right, key)
    }
    return root
}

func bstMin(node *BSTNode) *BSTNode {
    for node.Left != nil {
        node = node.Left
    }
    return node
}

func bstDelete(root *BSTNode, key int) *BSTNode {
    if root == nil {
        return nil
    }
    switch {
    case key < root.Key:
        root.Left = bstDelete(root.Left, key)
    case key > root.Key:
        root.Right = bstDelete(root.Right, key)
    default:
        if root.Left == nil {
            return root.Right
        }
        if root.Right == nil {
            return root.Left
        }
        // Two children: replace with inorder successor
        successor := bstMin(root.Right)
        root.Key = successor.Key
        root.Right = bstDelete(root.Right, successor.Key)
    }
    return root
}

func inorder(root *BSTNode) {
    if root == nil {
        return
    }
    inorder(root.Left)
    fmt.Printf("%d ", root.Key)
    inorder(root.Right)
}

func main() {
    var root *BSTNode
    for _, k := range []int{8, 3, 10, 1, 6, 14, 4, 7, 13} {
        root = bstInsert(root, k)
    }
    fmt.Print("Inorder: ")
    inorder(root)
    fmt.Println()
    root = bstDelete(root, 3)
    fmt.Print("After delete 3: ")
    inorder(root)
    fmt.Println()
}
```

**Rust:**
```rust
#[derive(Debug)]
struct BSTNode {
    key: i32,
    left: Option<Box<BSTNode>>,
    right: Option<Box<BSTNode>>,
}

impl BSTNode {
    fn new(key: i32) -> Box<Self> {
        Box::new(BSTNode { key, left: None, right: None })
    }
}

fn bst_insert(root: Option<Box<BSTNode>>, key: i32) -> Box<BSTNode> {
    match root {
        None => BSTNode::new(key),
        Some(mut node) => {
            if key < node.key {
                node.left = Some(bst_insert(node.left, key));
            } else if key > node.key {
                node.right = Some(bst_insert(node.right, key));
            }
            node
        }
    }
}

fn bst_min_key(node: &BSTNode) -> i32 {
    match &node.left {
        None => node.key,
        Some(left) => bst_min_key(left),
    }
}

fn bst_delete(root: Option<Box<BSTNode>>, key: i32) -> Option<Box<BSTNode>> {
    match root {
        None => None,
        Some(mut node) => {
            if key < node.key {
                node.left = bst_delete(node.left, key);
                Some(node)
            } else if key > node.key {
                node.right = bst_delete(node.right, key);
                Some(node)
            } else {
                match (node.left.take(), node.right.take()) {
                    (None, right) => right,
                    (left, None) => left,
                    (left, right) => {
                        // Two children: find inorder successor
                        let successor_key = bst_min_key(right.as_ref().unwrap());
                        node.key = successor_key;
                        node.left = left;
                        node.right = bst_delete(right, successor_key);
                        Some(node)
                    }
                }
            }
        }
    }
}

fn inorder(root: &Option<Box<BSTNode>>) {
    if let Some(node) = root {
        inorder(&node.left);
        print!("{} ", node.key);
        inorder(&node.right);
    }
}

fn main() {
    let mut root: Option<Box<BSTNode>> = None;
    for &k in &[8, 3, 10, 1, 6, 14, 4, 7, 13] {
        root = Some(bst_insert(root, k));
    }
    print!("Inorder: ");
    inorder(&root); // 1 3 4 6 7 8 10 13 14
    println!();

    root = bst_delete(root, 3);
    print!("After delete 3: ");
    inorder(&root); // 1 4 6 7 8 10 13 14
    println!();
}
```

---

### 5.4 AVL Tree (Height-Balanced BST)

**The Problem with Plain BST:**
Insert sorted data → BST degenerates into a linked list → O(N) operations instead of O(log N).

```
Inserting 1,2,3,4,5 into BST:
  1
   \
    2
     \
      3           ← Degenerate! Like a linked list.
       \
        4
         \
          5
```

**AVL Solution:**
After every insert/delete, **rebalance** using **rotations** to maintain:
> Balance Factor (BF) = height(left) - height(right) ∈ {-1, 0, 1}

**The 4 Rotation Cases:**

```
CASE 1: LEFT-LEFT (LL)  → Right Rotation
    z                   y
   / \                 / \
  y   T4    →         x   z
 / \                 / \ / \
x   T3              T1 T2 T3 T4
/ \
T1 T2

CASE 2: RIGHT-RIGHT (RR) → Left Rotation
  z                       y
 / \                     / \
T1  y          →        z   x
   / \                 / \ / \
  T2  x               T1 T2 T3 T4
     / \
    T3  T4

CASE 3: LEFT-RIGHT (LR)  → Left rotate y, then Right rotate z
    z                z                 x
   / \              / \               / \
  y   T4   →       x  T4    →        y   z
 / \              / \               / \ / \
T1  x            y  T3             T1 T2 T3 T4
   / \          / \
  T2  T3       T1  T2

CASE 4: RIGHT-LEFT (RL)  → Right rotate y, then Left rotate z
  z                 z                    x
 / \               / \                  / \
T1   y    →       T1  x      →         z   y
    / \               / \             / \ / \
   x  T4             T2  y           T1 T2 T3 T4
  / \                   / \
 T2  T3                T3  T4
```

**DECISION TREE — Which Rotation to Apply:**
```
After insert, calculate BF at current node:

         BF > 1 (Left Heavy)?
        YES                 NO
         │                   │
  BF of left child?    BF < -1 (Right Heavy)?
  ≥ 0 → LL → Right Rot   YES         NO
  < 0 → LR → Left-Right   │          │
              Double Rot  BF of right child?
                          ≤ 0 → RR → Left Rot
                          > 0 → RL → Right-Left
                                     Double Rot
```

**C:**
```c
#include <stdio.h>
#include <stdlib.h>

typedef struct AVLNode {
    int key, height;
    struct AVLNode *left, *right;
} AVLNode;

int avl_height(AVLNode *n) { return n ? n->height : 0; }

int avl_max(int a, int b) { return a > b ? a : b; }

void avl_update_height(AVLNode *n) {
    n->height = 1 + avl_max(avl_height(n->left), avl_height(n->right));
}

int avl_bf(AVLNode *n) {
    return n ? avl_height(n->left) - avl_height(n->right) : 0;
}

AVLNode *avl_new(int key) {
    AVLNode *n = (AVLNode *)malloc(sizeof(AVLNode));
    n->key = key; n->height = 1; n->left = n->right = NULL;
    return n;
}

// Right rotation around z
AVLNode *avl_right_rotate(AVLNode *z) {
    AVLNode *y = z->left;
    AVLNode *T3 = y->right;
    y->right = z;       // y becomes new root
    z->left  = T3;      // T3 moves to z's left
    avl_update_height(z);
    avl_update_height(y);
    return y;
}

// Left rotation around z
AVLNode *avl_left_rotate(AVLNode *z) {
    AVLNode *y = z->right;
    AVLNode *T2 = y->left;
    y->left  = z;       // y becomes new root
    z->right = T2;      // T2 moves to z's right
    avl_update_height(z);
    avl_update_height(y);
    return y;
}

AVLNode *avl_insert(AVLNode *root, int key) {
    // Step 1: Standard BST insert
    if (!root) return avl_new(key);
    if (key < root->key)
        root->left  = avl_insert(root->left,  key);
    else if (key > root->key)
        root->right = avl_insert(root->right, key);
    else
        return root;  // Duplicate

    // Step 2: Update height
    avl_update_height(root);

    // Step 3: Get balance factor and rebalance
    int bf = avl_bf(root);

    // LL Case
    if (bf > 1 && key < root->left->key)
        return avl_right_rotate(root);

    // RR Case
    if (bf < -1 && key > root->right->key)
        return avl_left_rotate(root);

    // LR Case
    if (bf > 1 && key > root->left->key) {
        root->left = avl_left_rotate(root->left);
        return avl_right_rotate(root);
    }

    // RL Case
    if (bf < -1 && key < root->right->key) {
        root->right = avl_right_rotate(root->right);
        return avl_left_rotate(root);
    }

    return root;  // Already balanced
}

void inorder_avl(AVLNode *root) {
    if (!root) return;
    inorder_avl(root->left);
    printf("%d(h=%d) ", root->key, root->height);
    inorder_avl(root->right);
}

int main(void) {
    AVLNode *root = NULL;
    // Inserting in sorted order — without AVL this would be a linked list!
    for (int i = 1; i <= 7; i++)
        root = avl_insert(root, i);

    printf("AVL Inorder: ");
    inorder_avl(root);
    printf("\n");
    printf("Root: %d (height: %d)\n", root->key, root->height);
    // Root should be 4, height 3 — balanced!
    return 0;
}
```

**Go:**
```go
package main

import "fmt"

type AVLNode struct {
    Key         int
    Height      int
    Left, Right *AVLNode
}

func avlHeight(n *AVLNode) int {
    if n == nil {
        return 0
    }
    return n.Height
}

func avlMax(a, b int) int {
    if a > b {
        return a
    }
    return b
}

func avlUpdateHeight(n *AVLNode) {
    n.Height = 1 + avlMax(avlHeight(n.Left), avlHeight(n.Right))
}

func avlBF(n *AVLNode) int {
    if n == nil {
        return 0
    }
    return avlHeight(n.Left) - avlHeight(n.Right)
}

func avlRightRotate(z *AVLNode) *AVLNode {
    y := z.Left
    t3 := y.Right
    y.Right = z
    z.Left = t3
    avlUpdateHeight(z)
    avlUpdateHeight(y)
    return y
}

func avlLeftRotate(z *AVLNode) *AVLNode {
    y := z.Right
    t2 := y.Left
    y.Left = z
    z.Right = t2
    avlUpdateHeight(z)
    avlUpdateHeight(y)
    return y
}

func avlInsert(root *AVLNode, key int) *AVLNode {
    if root == nil {
        return &AVLNode{Key: key, Height: 1}
    }
    if key < root.Key {
        root.Left = avlInsert(root.Left, key)
    } else if key > root.Key {
        root.Right = avlInsert(root.Right, key)
    } else {
        return root
    }

    avlUpdateHeight(root)
    bf := avlBF(root)

    if bf > 1 && key < root.Left.Key {
        return avlRightRotate(root)
    }
    if bf < -1 && key > root.Right.Key {
        return avlLeftRotate(root)
    }
    if bf > 1 && key > root.Left.Key {
        root.Left = avlLeftRotate(root.Left)
        return avlRightRotate(root)
    }
    if bf < -1 && key < root.Right.Key {
        root.Right = avlRightRotate(root.Right)
        return avlLeftRotate(root)
    }
    return root
}

func inorderAVL(root *AVLNode) {
    if root == nil {
        return
    }
    inorderAVL(root.Left)
    fmt.Printf("%d(h=%d) ", root.Key, root.Height)
    inorderAVL(root.Right)
}

func main() {
    var root *AVLNode
    for i := 1; i <= 7; i++ {
        root = avlInsert(root, i)
    }
    fmt.Print("AVL Inorder: ")
    inorderAVL(root)
    fmt.Printf("\nRoot: %d (height: %d)\n", root.Key, root.Height)
}
```

---

### 5.5 Red-Black Tree (Concept + Structure)

A Red-Black Tree is a BST where every node is colored **RED** or **BLACK** with these invariants:

```
RED-BLACK PROPERTIES:
─────────────────────────────────────────────────────
1. Every node is RED or BLACK
2. The ROOT is BLACK
3. Every LEAF (NIL sentinel) is BLACK
4. If a node is RED, both its children are BLACK
   (no two consecutive red nodes)
5. For each node, all paths to descendant NIL leaves
   have the SAME number of black nodes
   (black-height is uniform)
─────────────────────────────────────────────────────

EXAMPLE:
        7(B)
       /    \
     3(R)   18(R)
    / \     / \
  2(B) 4(B) 11(B) 19(B)
```

**Why Red-Black over AVL?**
| Property | AVL | Red-Black |
|---------|-----|-----------|
| Balance | Stricter (BF ≤ 1) | Looser (factor of 2) |
| Lookup | Faster (lower height) | Slightly slower |
| Insert/Delete | More rotations | Fewer rotations |
| Use case | Read-heavy | Write-heavy, general |
| Used in | Databases | OS schedulers, Java TreeMap, C++ std::map |

> Full Red-Black implementation is complex (~300 lines). In practice, use library implementations (`std::collections::BTreeMap` in Rust, `map` in C++). The critical insight is *understanding when to use it*.

---

### 5.6 Min-Heap & Max-Heap

A **heap** is a complete binary tree satisfying the **heap property**:
- **Min-Heap:** Every parent ≤ its children → root is minimum
- **Max-Heap:** Every parent ≥ its children → root is maximum

```
MIN-HEAP:           MAX-HEAP:
      1                  9
     / \                / \
    3   2              7   8
   / \ / \            / \ / \
  5  4 6  7          2  5 3  6
```

**Key Operations:**
```
INSERT:   Add at end, then "bubble up" (sift up)
DELETE MIN/MAX: Remove root, move last element to root, "bubble down" (sift down)
BUILD HEAP from array: O(N) — start from last non-leaf, sift down

INSERT ALGORITHM (Min-Heap):
  1. Add element at index size
  2. i = size, size++
  3. While i > 0 and heap[parent(i)] > heap[i]:
       swap(heap[i], heap[parent(i)])
       i = parent(i)
```

**C — Min-Heap:**
```c
#include <stdio.h>
#include <stdlib.h>

#define MAX_HEAP 1024

typedef struct MinHeap {
    int data[MAX_HEAP];
    int size;
} MinHeap;

static inline int heap_parent(int i) { return (i - 1) / 2; }
static inline int heap_left(int i)   { return 2 * i + 1; }
static inline int heap_right(int i)  { return 2 * i + 2; }

void heap_swap(MinHeap *h, int i, int j) {
    int t = h->data[i]; h->data[i] = h->data[j]; h->data[j] = t;
}

// Sift element at index i upward
void sift_up(MinHeap *h, int i) {
    while (i > 0 && h->data[heap_parent(i)] > h->data[i]) {
        heap_swap(h, i, heap_parent(i));
        i = heap_parent(i);
    }
}

// Sift element at index i downward
void sift_down(MinHeap *h, int i) {
    int smallest = i;
    int l = heap_left(i), r = heap_right(i);
    if (l < h->size && h->data[l] < h->data[smallest]) smallest = l;
    if (r < h->size && h->data[r] < h->data[smallest]) smallest = r;
    if (smallest != i) {
        heap_swap(h, i, smallest);
        sift_down(h, smallest);
    }
}

void heap_push(MinHeap *h, int val) {
    if (h->size >= MAX_HEAP) return;
    h->data[h->size++] = val;
    sift_up(h, h->size - 1);
}

int heap_pop(MinHeap *h) {
    int min_val = h->data[0];
    h->data[0] = h->data[--h->size];  // Move last to root
    sift_down(h, 0);
    return min_val;
}

// Build heap from arbitrary array in O(N)
// Key insight: leaf nodes already satisfy heap property.
// Start from last non-leaf node (size/2 - 1) and sift down.
void build_heap(MinHeap *h, int *arr, int n) {
    for (int i = 0; i < n; i++) h->data[i] = arr[i];
    h->size = n;
    for (int i = n/2 - 1; i >= 0; i--) {
        sift_down(h, i);
    }
}

int main(void) {
    MinHeap h = {.size = 0};

    int arr[] = {5, 3, 8, 1, 9, 2, 7, 4, 6};
    int n = sizeof(arr)/sizeof(arr[0]);

    build_heap(&h, arr, n);

    printf("Heap sort (ascending): ");
    while (h.size > 0) printf("%d ", heap_pop(&h));
    printf("\n");
    // Output: 1 2 3 4 5 6 7 8 9
    return 0;
}
```

**Go:**
```go
package main

import (
    "container/heap"
    "fmt"
)

// Implement heap.Interface for a min-heap of ints
type IntHeap []int

func (h IntHeap) Len() int           { return len(h) }
func (h IntHeap) Less(i, j int) bool { return h[i] < h[j] }
func (h IntHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }
func (h *IntHeap) Push(x interface{}) { *h = append(*h, x.(int)) }
func (h *IntHeap) Pop() interface{} {
    old := *h
    n := len(old)
    x := old[n-1]
    *h = old[:n-1]
    return x
}

func main() {
    h := &IntHeap{5, 3, 8, 1, 9, 2, 7, 4, 6}
    heap.Init(h) // Build heap in O(N)

    fmt.Print("Heap sort: ")
    for h.Len() > 0 {
        fmt.Printf("%d ", heap.Pop(h))
    }
    fmt.Println()
    // Output: 1 2 3 4 5 6 7 8 9
}
```

**Rust:**
```rust
use std::collections::BinaryHeap;
use std::cmp::Reverse;

fn main() {
    // BinaryHeap is a MAX-heap by default.
    // Use Reverse<T> for min-heap.
    let nums = vec![5, 3, 8, 1, 9, 2, 7, 4, 6];

    // MAX-HEAP
    let mut max_heap: BinaryHeap<i32> = nums.iter().cloned().collect();
    print!("Max heap sort (descending): ");
    while let Some(val) = max_heap.pop() {
        print!("{} ", val);
    }
    println!();

    // MIN-HEAP using Reverse
    let mut min_heap: BinaryHeap<Reverse<i32>> =
        nums.iter().map(|&x| Reverse(x)).collect();
    print!("Min heap sort (ascending): ");
    while let Some(Reverse(val)) = min_heap.pop() {
        print!("{} ", val);
    }
    println!();
}
```

---

### 5.7 Trie (Prefix Tree)

A trie is a tree used for **string key retrieval**. Each path from root to a node spells out a prefix.

```
INSERT: "cat", "car", "bat", "bad"

          root
         /    \
        c      b
        |      |
        a      a
       / \    / \
      t*  r* t*  d*
     
     * = end of word marker

OPERATIONS:
  Insert "car" : root → c → a → r (mark end)
  Search "cat" : root → c → a → t → found end-mark ✓
  Prefix "ca"  : root → c → a → both words found
```

**C:**
```c
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>

#define ALPHA 26  // lowercase a-z

typedef struct TrieNode {
    struct TrieNode *children[ALPHA];
    bool is_end;
} TrieNode;

TrieNode *trie_new_node(void) {
    return (TrieNode *)calloc(1, sizeof(TrieNode));
}

void trie_insert(TrieNode *root, const char *word) {
    TrieNode *cur = root;
    for (int i = 0; word[i]; i++) {
        int idx = word[i] - 'a';
        if (!cur->children[idx])
            cur->children[idx] = trie_new_node();
        cur = cur->children[idx];
    }
    cur->is_end = true;
}

bool trie_search(TrieNode *root, const char *word) {
    TrieNode *cur = root;
    for (int i = 0; word[i]; i++) {
        int idx = word[i] - 'a';
        if (!cur->children[idx]) return false;
        cur = cur->children[idx];
    }
    return cur->is_end;
}

bool trie_starts_with(TrieNode *root, const char *prefix) {
    TrieNode *cur = root;
    for (int i = 0; prefix[i]; i++) {
        int idx = prefix[i] - 'a';
        if (!cur->children[idx]) return false;
        cur = cur->children[idx];
    }
    return true;
}

int main(void) {
    TrieNode *root = trie_new_node();

    char *words[] = {"apple", "app", "application", "bat", "bad", "cat"};
    int n = sizeof(words) / sizeof(words[0]);

    for (int i = 0; i < n; i++) trie_insert(root, words[i]);

    printf("Search 'app': %s\n",     trie_search(root, "app")     ? "YES" : "NO");
    printf("Search 'ap': %s\n",      trie_search(root, "ap")      ? "YES" : "NO");
    printf("Prefix 'app': %s\n",     trie_starts_with(root, "app")? "YES" : "NO");
    printf("Prefix 'ba': %s\n",      trie_starts_with(root, "ba") ? "YES" : "NO");
    printf("Search 'batman': %s\n",  trie_search(root, "batman")  ? "YES" : "NO");

    return 0;
}
```

**Go:**
```go
package main

import "fmt"

const alpha = 26

type TrieNode struct {
    children [alpha]*TrieNode
    isEnd    bool
}

type Trie struct {
    root *TrieNode
}

func NewTrie() *Trie {
    return &Trie{root: &TrieNode{}}
}

func (t *Trie) Insert(word string) {
    cur := t.root
    for _, ch := range word {
        idx := ch - 'a'
        if cur.children[idx] == nil {
            cur.children[idx] = &TrieNode{}
        }
        cur = cur.children[idx]
    }
    cur.isEnd = true
}

func (t *Trie) Search(word string) bool {
    cur := t.root
    for _, ch := range word {
        idx := ch - 'a'
        if cur.children[idx] == nil {
            return false
        }
        cur = cur.children[idx]
    }
    return cur.isEnd
}

func (t *Trie) StartsWith(prefix string) bool {
    cur := t.root
    for _, ch := range prefix {
        idx := ch - 'a'
        if cur.children[idx] == nil {
            return false
        }
        cur = cur.children[idx]
    }
    return true
}

func main() {
    t := NewTrie()
    for _, w := range []string{"apple", "app", "application", "bat"} {
        t.Insert(w)
    }
    fmt.Println(t.Search("app"))       // true
    fmt.Println(t.Search("ap"))        // false
    fmt.Println(t.StartsWith("appl"))  // true
}
```

**Rust:**
```rust
use std::collections::HashMap;

#[derive(Default, Debug)]
struct TrieNode {
    children: HashMap<char, TrieNode>,
    is_end: bool,
}

struct Trie {
    root: TrieNode,
}

impl Trie {
    fn new() -> Self {
        Trie { root: TrieNode::default() }
    }

    fn insert(&mut self, word: &str) {
        let mut cur = &mut self.root;
        for ch in word.chars() {
            cur = cur.children.entry(ch).or_default();
        }
        cur.is_end = true;
    }

    fn search(&self, word: &str) -> bool {
        let mut cur = &self.root;
        for ch in word.chars() {
            match cur.children.get(&ch) {
                None => return false,
                Some(next) => cur = next,
            }
        }
        cur.is_end
    }

    fn starts_with(&self, prefix: &str) -> bool {
        let mut cur = &self.root;
        for ch in prefix.chars() {
            match cur.children.get(&ch) {
                None => return false,
                Some(next) => cur = next,
            }
        }
        true
    }
}

fn main() {
    let mut t = Trie::new();
    for word in &["apple", "app", "application", "bat"] {
        t.insert(word);
    }
    println!("search 'app': {}", t.search("app"));       // true
    println!("search 'ap': {}", t.search("ap"));         // false
    println!("prefix 'appl': {}", t.starts_with("appl"));// true
}
```

---

### 5.8 Segment Tree

A segment tree is built over an **array** to answer **range queries** (sum, min, max) and **point/range updates** in O(log N).

```
ARRAY: [2, 1, 5, 3, 4]
INDEX:  0  1  2  3  4

SEGMENT TREE (range sum):

          [0,4]=15
         /         \
     [0,2]=8      [3,4]=7
     /     \      /    \
  [0,1]=3 [2,2]=5 [3,3]=3 [4,4]=4
  /    \
[0,0]=2 [1,1]=1

QUERY sum(1,3) = 1+5+3 = 9  → traverse relevant nodes
UPDATE arr[2] = 10           → update path from root to leaf
```

**Storage:** Use 4*N sized array (safe upper bound).

**C:**
```c
#include <stdio.h>
#include <stdlib.h>

#define MAXN 100005

int seg[4 * MAXN];

// Build: O(N)
void seg_build(int *arr, int node, int start, int end) {
    if (start == end) {
        seg[node] = arr[start];
        return;
    }
    int mid = (start + end) / 2;
    seg_build(arr, 2*node,   start,   mid);
    seg_build(arr, 2*node+1, mid+1,   end);
    seg[node] = seg[2*node] + seg[2*node+1];
}

// Point update: O(log N)
void seg_update(int node, int start, int end, int idx, int val) {
    if (start == end) {
        seg[node] = val;
        return;
    }
    int mid = (start + end) / 2;
    if (idx <= mid) seg_update(2*node,   start,   mid, idx, val);
    else            seg_update(2*node+1, mid+1,   end, idx, val);
    seg[node] = seg[2*node] + seg[2*node+1];
}

// Range query: O(log N)
// Returns sum of arr[l..r]
int seg_query(int node, int start, int end, int l, int r) {
    if (r < start || end < l) return 0;  // Out of range
    if (l <= start && end <= r) return seg[node];  // Fully in range
    int mid = (start + end) / 2;
    return seg_query(2*node,   start, mid, l, r)
         + seg_query(2*node+1, mid+1, end, l, r);
}

int main(void) {
    int arr[] = {2, 1, 5, 3, 4};
    int n = 5;

    seg_build(arr, 1, 0, n-1);  // Node 1 is root

    printf("Sum [1,3]: %d\n", seg_query(1, 0, n-1, 1, 3));  // 9

    seg_update(1, 0, n-1, 2, 10);  // arr[2] = 10

    printf("Sum [1,3] after update: %d\n",
           seg_query(1, 0, n-1, 1, 3));  // 14
    return 0;
}
```

**Go:**
```go
package main

import "fmt"

type SegTree struct {
    tree []int
    n    int
}

func NewSegTree(arr []int) *SegTree {
    n := len(arr)
    st := &SegTree{tree: make([]int, 4*n), n: n}
    st.build(arr, 1, 0, n-1)
    return st
}

func (st *SegTree) build(arr []int, node, start, end int) {
    if start == end {
        st.tree[node] = arr[start]
        return
    }
    mid := (start + end) / 2
    st.build(arr, 2*node, start, mid)
    st.build(arr, 2*node+1, mid+1, end)
    st.tree[node] = st.tree[2*node] + st.tree[2*node+1]
}

func (st *SegTree) Update(node, start, end, idx, val int) {
    if start == end {
        st.tree[node] = val
        return
    }
    mid := (start + end) / 2
    if idx <= mid {
        st.Update(2*node, start, mid, idx, val)
    } else {
        st.Update(2*node+1, mid+1, end, idx, val)
    }
    st.tree[node] = st.tree[2*node] + st.tree[2*node+1]
}

func (st *SegTree) Query(node, start, end, l, r int) int {
    if r < start || end < l {
        return 0
    }
    if l <= start && end <= r {
        return st.tree[node]
    }
    mid := (start + end) / 2
    return st.Query(2*node, start, mid, l, r) +
        st.Query(2*node+1, mid+1, end, l, r)
}

func main() {
    arr := []int{2, 1, 5, 3, 4}
    st := NewSegTree(arr)

    fmt.Println("Sum [1,3]:", st.Query(1, 0, 4, 1, 3)) // 9
    st.Update(1, 0, 4, 2, 10)
    fmt.Println("Sum [1,3] after update:", st.Query(1, 0, 4, 1, 3)) // 14
}
```

**Rust:**
```rust
struct SegTree {
    tree: Vec<i64>,
    n: usize,
}

impl SegTree {
    fn new(arr: &[i64]) -> Self {
        let n = arr.len();
        let mut st = SegTree {
            tree: vec![0; 4 * n],
            n,
        };
        st.build(arr, 1, 0, n - 1);
        st
    }

    fn build(&mut self, arr: &[i64], node: usize, start: usize, end: usize) {
        if start == end {
            self.tree[node] = arr[start];
            return;
        }
        let mid = (start + end) / 2;
        self.build(arr, 2 * node, start, mid);
        self.build(arr, 2 * node + 1, mid + 1, end);
        self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1];
    }

    fn update(&mut self, node: usize, start: usize, end: usize, idx: usize, val: i64) {
        if start == end {
            self.tree[node] = val;
            return;
        }
        let mid = (start + end) / 2;
        if idx <= mid {
            self.update(2 * node, start, mid, idx, val);
        } else {
            self.update(2 * node + 1, mid + 1, end, idx, val);
        }
        self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1];
    }

    fn query(&self, node: usize, start: usize, end: usize, l: usize, r: usize) -> i64 {
        if r < start || end < l {
            return 0;
        }
        if l <= start && end <= r {
            return self.tree[node];
        }
        let mid = (start + end) / 2;
        self.query(2 * node, start, mid, l, r)
            + self.query(2 * node + 1, mid + 1, end, l, r)
    }
}

fn main() {
    let arr = vec![2i64, 1, 5, 3, 4];
    let n = arr.len();
    let mut st = SegTree::new(&arr);

    println!("Sum [1,3]: {}", st.query(1, 0, n - 1, 1, 3)); // 9
    st.update(1, 0, n - 1, 2, 10);
    println!("Sum [1,3] after update: {}", st.query(1, 0, n - 1, 1, 3)); // 14
}
```

---

### 5.9 Fenwick Tree (Binary Indexed Tree / BIT)

A Fenwick tree is a flat array that implicitly represents a binary tree. It answers **prefix sum queries** and **point updates** in O(log N) with extremely low constant factor and code simplicity.

```
ARRAY:    [1, 2, 3, 4, 5, 6, 7, 8]
INDEX:     1  2  3  4  5  6  7  8   (1-indexed!)

BIT TREE (each index i stores sum of a range):
bit[i] covers: arr[i - lowbit(i) + 1 .. i]
where lowbit(i) = i & (-i) = least significant bit

bit[1] = arr[1]               (covers 1 element)
bit[2] = arr[1]+arr[2]        (covers 2 elements)
bit[3] = arr[3]               (covers 1 element)
bit[4] = arr[1]+...+arr[4]    (covers 4 elements)
bit[6] = arr[5]+arr[6]        (covers 2 elements)
bit[8] = arr[1]+...+arr[8]    (covers 8 elements)

QUERY prefix_sum(i):
  sum = 0
  while i > 0:
    sum += bit[i]
    i -= lowbit(i)    // remove lowest set bit

UPDATE point(i, delta):
  while i <= n:
    bit[i] += delta
    i += lowbit(i)    // add lowest set bit
```

**C:**
```c
#include <stdio.h>

#define MAXN 1024

int bit[MAXN];  // 1-indexed
int n;

static inline int lowbit(int x) { return x & (-x); }

void bit_update(int i, int delta) {
    for (; i <= n; i += lowbit(i))
        bit[i] += delta;
}

int bit_query(int i) {  // prefix sum [1..i]
    int sum = 0;
    for (; i > 0; i -= lowbit(i))
        sum += bit[i];
    return sum;
}

int bit_range_query(int l, int r) {  // sum [l..r]
    return bit_query(r) - bit_query(l - 1);
}

// Build BIT from array in O(N log N)
void bit_build(int *arr, int size) {
    n = size;
    for (int i = 1; i <= n; i++)
        bit_update(i, arr[i]);
}

int main(void) {
    int arr[] = {0, 1, 2, 3, 4, 5, 6, 7, 8};  // 1-indexed (arr[0] unused)
    bit_build(arr, 8);

    printf("Prefix sum [1..4]: %d\n", bit_query(4));       // 10
    printf("Range sum  [3..6]: %d\n", bit_range_query(3,6)); // 18

    bit_update(3, 5);  // arr[3] += 5 (now = 8)

    printf("Range sum  [3..6] after update: %d\n",
           bit_range_query(3, 6));  // 23
    return 0;
}
```

**Go:**
```go
package main

import "fmt"

type BIT struct {
    tree []int
    n    int
}

func NewBIT(n int) *BIT {
    return &BIT{tree: make([]int, n+1), n: n}
}

func (b *BIT) Update(i, delta int) {
    for ; i <= b.n; i += i & (-i) {
        b.tree[i] += delta
    }
}

func (b *BIT) Query(i int) int {
    sum := 0
    for ; i > 0; i -= i & (-i) {
        sum += b.tree[i]
    }
    return sum
}

func (b *BIT) RangeQuery(l, r int) int {
    return b.Query(r) - b.Query(l-1)
}

func main() {
    arr := []int{0, 1, 2, 3, 4, 5, 6, 7, 8} // 1-indexed
    b := NewBIT(8)
    for i := 1; i <= 8; i++ {
        b.Update(i, arr[i])
    }
    fmt.Println("Prefix sum [1..4]:", b.Query(4))         // 10
    fmt.Println("Range sum [3..6]:", b.RangeQuery(3, 6))  // 18
    b.Update(3, 5)
    fmt.Println("After update:", b.RangeQuery(3, 6))      // 23
}
```

**Rust:**
```rust
struct BIT {
    tree: Vec<i64>,
    n: usize,
}

impl BIT {
    fn new(n: usize) -> Self {
        BIT { tree: vec![0; n + 1], n }
    }

    fn update(&mut self, mut i: usize, delta: i64) {
        while i <= self.n {
            self.tree[i] += delta;
            i += i & i.wrapping_neg();
        }
    }

    fn query(&self, mut i: usize) -> i64 {
        let mut sum = 0i64;
        while i > 0 {
            sum += self.tree[i];
            i -= i & i.wrapping_neg();
        }
        sum
    }

    fn range_query(&self, l: usize, r: usize) -> i64 {
        self.query(r) - self.query(l - 1)
    }
}

fn main() {
    let arr: Vec<i64> = vec![0, 1, 2, 3, 4, 5, 6, 7, 8]; // 1-indexed
    let mut bit = BIT::new(8);
    for i in 1..=8 {
        bit.update(i, arr[i]);
    }
    println!("Prefix sum [1..4]: {}", bit.query(4));         // 10
    println!("Range sum [3..6]: {}", bit.range_query(3, 6)); // 18
    bit.update(3, 5);
    println!("After update: {}", bit.range_query(3, 6));     // 23
}
```

---

### 5.10 B-Tree (Concept)

B-Trees are self-balancing trees where each node can hold **multiple keys** and have **multiple children** (degree M). Used in databases and file systems.

```
B-TREE of order 3 (max 2 keys, max 3 children per node):

        [10 | 20]
       /    |    \
   [5|7]  [12|15]  [25|30]

PROPERTIES:
- Every node has at most M-1 keys
- Every non-leaf node has between ⌈M/2⌉ and M children
- All leaves are at the same level
- Keys within each node are sorted

WHY? Minimizes disk I/O — one node = one disk page read.
MySQL InnoDB uses B+ Tree variant (all data in leaves).
```

> B-Tree full implementation spans 400+ lines. The key insight: **when a node overflows, split and push middle key to parent**. This guarantees O(log N) operations where N = total keys.

---

### 5.11 Expression Tree

An expression tree encodes an arithmetic or logical expression. **Internal nodes are operators**, **leaves are operands**.

```
Expression: (3 + 4) * (2 - 1)

        *
       / \
      +   -
     / \ / \
    3  4 2  1

Evaluation: postorder traversal
Infix print: inorder traversal with parentheses
Prefix print: preorder traversal
```

**C:**
```c
#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <string.h>

typedef struct ExprNode {
    char val;  // operator or digit
    struct ExprNode *left, *right;
} ExprNode;

ExprNode *expr_new(char val) {
    ExprNode *n = (ExprNode *)malloc(sizeof(ExprNode));
    n->val = val; n->left = n->right = NULL;
    return n;
}

// Build from postfix expression string
// e.g., "34+21-*" → (3+4)*(2-1)
ExprNode *build_from_postfix(const char *expr) {
    ExprNode *stack[64];
    int top = 0;

    for (int i = 0; expr[i]; i++) {
        char c = expr[i];
        if (isdigit(c)) {
            stack[top++] = expr_new(c);  // Leaf node
        } else {
            // Operator: pop two operands
            ExprNode *node = expr_new(c);
            node->right = stack[--top];  // Right operand popped first
            node->left  = stack[--top];
            stack[top++] = node;
        }
    }
    return stack[0];
}

int evaluate(ExprNode *node) {
    if (!node) return 0;
    if (isdigit(node->val)) return node->val - '0';
    int l = evaluate(node->left);
    int r = evaluate(node->right);
    switch (node->val) {
        case '+': return l + r;
        case '-': return l - r;
        case '*': return l * r;
        case '/': return l / r;
    }
    return 0;
}

void infix_print(ExprNode *node) {
    if (!node) return;
    if (node->left || node->right) printf("(");
    infix_print(node->left);
    printf("%c", node->val);
    infix_print(node->right);
    if (node->left || node->right) printf(")");
}

int main(void) {
    // Postfix: 3 4 + 2 1 - *  means  (3+4)*(2-1)
    ExprNode *root = build_from_postfix("34+21-*");
    printf("Infix: ");
    infix_print(root);       // ((3+4)*(2-1))
    printf("\nResult: %d\n", evaluate(root));  // 7
    return 0;
}
```

---

### 5.12 Huffman Tree

A Huffman tree is a greedy-built tree for **optimal prefix-free encoding** (data compression). Characters with higher frequency get shorter codes.

```
FREQUENCIES: a=5, b=9, c=12, d=13, e=16, f=45

ALGORITHM:
1. Put all chars in a min-heap by frequency
2. Extract two min-freq nodes
3. Create a parent with freq = sum of two
4. Insert parent back
5. Repeat until one node remains (root)

FINAL TREE:
          100
         /   \
        f(45)  55
              /  \
            25    30
           /  \   / \
         12   13 14  16
         (c) (d) /\  (e)
                a  b
               (5)(9)

HUFFMAN CODES:
f = 0   (1 bit!)
c = 100
d = 101
e = 111
a = 1100
b = 1101
```

**Go:**
```go
package main

import (
    "container/heap"
    "fmt"
)

type HuffNode struct {
    Char  rune
    Freq  int
    Left  *HuffNode
    Right *HuffNode
}

// min-heap of HuffNode pointers
type HuffHeap []*HuffNode

func (h HuffHeap) Len() int            { return len(h) }
func (h HuffHeap) Less(i, j int) bool  { return h[i].Freq < h[j].Freq }
func (h HuffHeap) Swap(i, j int)       { h[i], h[j] = h[j], h[i] }
func (h *HuffHeap) Push(x interface{}) { *h = append(*h, x.(*HuffNode)) }
func (h *HuffHeap) Pop() interface{} {
    old := *h
    n := len(old)
    x := old[n-1]
    *h = old[:n-1]
    return x
}

func BuildHuffman(freqs map[rune]int) *HuffNode {
    h := &HuffHeap{}
    for ch, freq := range freqs {
        heap.Push(h, &HuffNode{Char: ch, Freq: freq})
    }
    heap.Init(h)

    for h.Len() > 1 {
        left  := heap.Pop(h).(*HuffNode)
        right := heap.Pop(h).(*HuffNode)
        parent := &HuffNode{
            Freq:  left.Freq + right.Freq,
            Left:  left,
            Right: right,
        }
        heap.Push(h, parent)
    }
    return heap.Pop(h).(*HuffNode)
}

func PrintCodes(node *HuffNode, code string) {
    if node == nil {
        return
    }
    if node.Left == nil && node.Right == nil {
        fmt.Printf("'%c': %s (freq=%d)\n", node.Char, code, node.Freq)
        return
    }
    PrintCodes(node.Left, code+"0")
    PrintCodes(node.Right, code+"1")
}

func main() {
    freqs := map[rune]int{
        'a': 5, 'b': 9, 'c': 12, 'd': 13, 'e': 16, 'f': 45,
    }
    root := BuildHuffman(freqs)
    fmt.Println("Huffman Codes:")
    PrintCodes(root, "")
}
```

---

### 5.13 Cartesian Tree

A Cartesian tree is a binary tree derived from a sequence where:
- **BST property** on indices (inorder traversal = original sequence)
- **Min-heap property** on values (root = minimum element)

```
Array: [3, 2, 6, 1, 9]
Index:  0  1  2  3  4

         1 (index 3, value 1 = minimum)
        / \
       2   9
      / \
     3   6
    (0) (2)

Build: O(N) using a monotonic stack
```

---

### 5.14 Treap (Tree + Heap)

A Treap assigns a **random priority** to each key. It maintains:
- BST property on keys
- Max-heap property on priorities

This gives O(log N) expected performance without complex rotations.

```
Key:      5   (key=5, priority=9)
         / \
        3   7  (priorities randomly assigned)
       / \
      1   4

SPLIT and MERGE operations make Treap very flexible:
- Split(T, k): Divide into T1 (keys ≤ k) and T2 (keys > k)
- Merge(T1, T2): Combine maintaining heap property
```

---

### 5.15 Splay Tree (Concept)

A splay tree **moves the last accessed node to the root** via rotations (the "splay" operation). This gives O(log N) amortized for all operations. Excellent for cache-friendly access patterns (temporal locality).

**Key insight:** Recently accessed elements are cheap to access again — useful for LRU-like workloads.

---

### 5.16 Suffix Tree / Suffix Array (Concept)

```
SUFFIX ARRAY of "banana":
Suffixes:  banana, anana, nana, ana, na, a
Sorted:    a, ana, anana, banana, na, nana
SA:        [5, 3, 1, 0, 4, 2]

Used for:
- Pattern matching in O(M log N) after O(N) build
- Longest common substring
- Count distinct substrings
```

Suffix trees (compressed trie of all suffixes) solve string problems that are otherwise O(N²). Ukkonen's algorithm builds them in O(N).

---

## 6. Tree Construction Algorithms

These algorithms answer: **"Given different forms of tree data, how do I reconstruct the tree?"**

---

### 6.1 From Level-Order Array (BFS Array)

Common in LeetCode: array `[1, 2, 3, null, null, 4, 5]` means:

```
         1
        / \
       2   3
          / \
         4   5
```

**C:**
```c
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

typedef struct BTNode { int val; struct BTNode *left, *right; } BTNode;

#define NONE -9999  // represents null

BTNode *build_from_level_order(int *arr, int n) {
    if (n == 0 || arr[0] == NONE) return NULL;

    BTNode **queue = (BTNode **)malloc(n * sizeof(BTNode *));
    int front = 0, back = 0;

    BTNode *root = (BTNode *)malloc(sizeof(BTNode));
    root->val = arr[0]; root->left = root->right = NULL;
    queue[back++] = root;

    int i = 1;
    while (front < back && i < n) {
        BTNode *node = queue[front++];

        if (i < n && arr[i] != NONE) {
            node->left = (BTNode *)malloc(sizeof(BTNode));
            node->left->val = arr[i]; node->left->left = node->left->right = NULL;
            queue[back++] = node->left;
        }
        i++;

        if (i < n && arr[i] != NONE) {
            node->right = (BTNode *)malloc(sizeof(BTNode));
            node->right->val = arr[i]; node->right->left = node->right->right = NULL;
            queue[back++] = node->right;
        }
        i++;
    }
    free(queue);
    return root;
}

void inorder_bt(BTNode *n) {
    if (!n) return;
    inorder_bt(n->left);
    printf("%d ", n->val);
    inorder_bt(n->right);
}

int main(void) {
    int arr[] = {1, 2, 3, NONE, NONE, 4, 5};
    BTNode *root = build_from_level_order(arr, 7);
    printf("Inorder: ");
    inorder_bt(root);  // 2 1 4 3 5
    printf("\n");
    return 0;
}
```

---

### 6.2 From Inorder + Preorder Traversals

**Key Insight:**
- **Preorder[0]** is always the **root**
- Find root's position in inorder array → everything left is left subtree, right is right subtree
- Recurse!

```
Preorder: [3, 9, 20, 15, 7]
Inorder:  [9, 3, 15, 20, 7]

Step 1: root = Preorder[0] = 3
Step 2: Find 3 in Inorder → index 1
        Left subtree inorder:  [9]          (indices 0..0)
        Right subtree inorder: [15, 20, 7]  (indices 2..4)
Step 3: Left subtree preorder:  [9]          (next 1 elements)
        Right subtree preorder: [20, 15, 7]  (remaining)
Step 4: Recurse on each half

RESULT:
        3
       / \
      9   20
         /  \
        15   7
```

**C:**
```c
#include <stdio.h>
#include <stdlib.h>

typedef struct Node { int val; struct Node *left, *right; } Node;

Node *new_node(int v) {
    Node *n = malloc(sizeof(Node));
    n->val = v; n->left = n->right = NULL;
    return n;
}

// inorder[in_start..in_end], preorder[pre_start..pre_end]
Node *build_pre_in(int *pre, int *in, int pre_start, int in_start, int in_end) {
    if (in_start > in_end) return NULL;

    int root_val = pre[pre_start];
    Node *root = new_node(root_val);

    // Find root in inorder
    int idx = in_start;
    while (in[idx] != root_val) idx++;

    int left_size = idx - in_start;

    root->left  = build_pre_in(pre, in,
                               pre_start + 1,
                               in_start, idx - 1);
    root->right = build_pre_in(pre, in,
                               pre_start + 1 + left_size,
                               idx + 1, in_end);
    return root;
}

void inorder_p(Node *n) {
    if (!n) return;
    inorder_p(n->left);
    printf("%d ", n->val);
    inorder_p(n->right);
}

int main(void) {
    int pre[] = {3, 9, 20, 15, 7};
    int in[]  = {9, 3, 15, 20, 7};
    int n = 5;

    Node *root = build_pre_in(pre, in, 0, 0, n-1);
    printf("Inorder (verify): ");
    inorder_p(root);  // Should match: 9 3 15 20 7
    printf("\n");
    return 0;
}
```

**Optimization:** Use a hash map for O(1) root-lookup in inorder array → reduces from O(N²) to O(N).

**Go:**
```go
package main

import "fmt"

type Node struct {
    Val   int
    Left  *Node
    Right *Node
}

func buildPreIn(pre, in []int, preStart, inStart, inEnd int, inMap map[int]int) *Node {
    if inStart > inEnd {
        return nil
    }
    rootVal := pre[preStart]
    root := &Node{Val: rootVal}
    idx := inMap[rootVal]
    leftSize := idx - inStart

    root.Left = buildPreIn(pre, in, preStart+1, inStart, idx-1, inMap)
    root.Right = buildPreIn(pre, in, preStart+1+leftSize, idx+1, inEnd, inMap)
    return root
}

func inorderPrint(n *Node) {
    if n == nil {
        return
    }
    inorderPrint(n.Left)
    fmt.Printf("%d ", n.Val)
    inorderPrint(n.Right)
}

func main() {
    pre := []int{3, 9, 20, 15, 7}
    in  := []int{9, 3, 15, 20, 7}
    n := len(in)

    // Build position map for O(1) lookup
    inMap := make(map[int]int)
    for i, v := range in {
        inMap[v] = i
    }

    root := buildPreIn(pre, in, 0, 0, n-1, inMap)
    fmt.Print("Inorder: ")
    inorderPrint(root) // 9 3 15 20 7
    fmt.Println()
}
```

---

### 6.3 From Inorder + Postorder

Same logic, but **Postorder's LAST element** is the root.

```
Postorder: [9, 15, 7, 20, 3]
Inorder:   [9, 3, 15, 20, 7]

root = Postorder[last] = 3
Find in Inorder → split left/right
```

**Go:**
```go
func buildPostIn(post, in []int, postEnd, inStart, inEnd int, inMap map[int]int) *Node {
    if inStart > inEnd {
        return nil
    }
    rootVal := post[postEnd]
    root := &Node{Val: rootVal}
    idx := inMap[rootVal]
    leftSize := idx - inStart

    root.Left  = buildPostIn(post, in, postEnd-1-(inEnd-idx), inStart, idx-1, inMap)
    root.Right = buildPostIn(post, in, postEnd-1, idx+1, inEnd, inMap)
    return root
}
```

---

### 6.4 From Sorted Array → Balanced BST

Convert sorted array into a height-balanced BST by always choosing the **middle element** as root.

```
SORTED: [1, 2, 3, 4, 5, 6, 7]
         ↑     ↑           ↑
        lo    mid          hi

Step 1: mid = 4, root = 4
Step 2: Left  → build([1,2,3]) → root=2, left=1, right=3
        Right → build([5,6,7]) → root=6, left=5, right=7

RESULT:
        4
       / \
      2   6
     / \ / \
    1  3 5  7
```

**C:**
```c
#include <stdio.h>
#include <stdlib.h>

typedef struct N { int v; struct N *l, *r; } N;
N *nn(int v) { N *n=malloc(sizeof(N)); n->v=v; n->l=n->r=NULL; return n; }

N *sorted_to_bst(int *arr, int lo, int hi) {
    if (lo > hi) return NULL;
    int mid = lo + (hi - lo) / 2;  // Avoids integer overflow
    N *root = nn(arr[mid]);
    root->l = sorted_to_bst(arr, lo,    mid - 1);
    root->r = sorted_to_bst(arr, mid+1, hi);
    return root;
}

void inorder_n(N *n) {
    if (!n) return;
    inorder_n(n->l);
    printf("%d ", n->v);
    inorder_n(n->r);
}

int main(void) {
    int arr[] = {1, 2, 3, 4, 5, 6, 7};
    N *root = sorted_to_bst(arr, 0, 6);
    printf("Inorder (should be sorted): ");
    inorder_n(root);  // 1 2 3 4 5 6 7
    printf("\n");
    printf("Root (should be 4): %d\n", root->v);
    return 0;
}
```

**Rust:**
```rust
fn sorted_to_bst(arr: &[i32]) -> Option<Box<TreeNode>> {
    if arr.is_empty() {
        return None;
    }
    let mid = arr.len() / 2;
    let mut node = Box::new(TreeNode::new(arr[mid]));
    node.left = sorted_to_bst(&arr[..mid]);
    node.right = sorted_to_bst(&arr[mid + 1..]);
    Some(node)
}

// Uses the TreeNode defined earlier in section 4.1
```

---

### 6.5 From Parent Array

Already covered in Section 4.3. Key steps:
1. Iterate array, build children lists
2. Find root (parent[i] == -1)
3. BFS/DFS from root

---

### 6.6 From Expression (Postfix to Expression Tree)

Already covered in Section 5.11.

---

## 7. Traversal Methods

**Every tree algorithm is one of these traversals in disguise.**

```
TREE:
      1
     / \
    2   3
   / \
  4   5

TRAVERSAL       ORDER           RESULT    USE CASE
─────────────────────────────────────────────────────────
Inorder         L → Root → R    4,2,5,1,3 BST sorted output
Preorder        Root → L → R    1,2,4,5,3 Copy tree, serialize
Postorder       L → R → Root    4,5,2,3,1 Delete tree, evaluate expr
Level-order     BFS by levels   1,2,3,4,5 Shortest path, serialization
Reverse inorder R → Root → L    3,1,5,2,4 BST descending sort
```

**Iterative Inorder (using stack — important for interviews):**

```c
// C: Iterative Inorder
void iterative_inorder(BSTNode *root) {
    // Stack to simulate recursion
    BSTNode *stack[1000];
    int top = 0;
    BSTNode *cur = root;

    while (cur != NULL || top > 0) {
        // Go as far left as possible
        while (cur != NULL) {
            stack[top++] = cur;
            cur = cur->left;
        }
        // Pop and visit
        cur = stack[--top];
        printf("%d ", cur->key);
        // Move to right subtree
        cur = cur->right;
    }
}
```

**Morris Traversal — O(1) Space Inorder:**

```
KEY IDEA: Temporarily modify the tree.
For each node with a left subtree:
  1. Find inorder predecessor (rightmost node of left subtree)
  2. Make predecessor's right point to current node (threaded link)
  3. Move to left child
  4. When we return via the threaded link, restore tree and visit

This achieves O(N) time, O(1) space inorder traversal!
```

---

## 8. Cognitive Mastery Map

### The Mental Model Hierarchy for Trees

```
LEVEL 1 — RECOGNITION
  Can you identify: what TYPE of tree does this problem need?
  
  SIGNAL → TREE TYPE
  ─────────────────────────────────────────────────────
  "Range query / update"        → Segment Tree or BIT
  "String prefix matching"      → Trie
  "Dynamic sorted order"        → BST / AVL / RB Tree
  "Priority queue / scheduling" → Heap
  "Hierarchical data"           → N-ary / General Tree
  "Optimal encoding"            → Huffman Tree
  "Expression parsing"          → Expression Tree
  "Graph, is it a tree?"        → Adjacency List DFS
  "K-th smallest / largest"     → Order Statistic Tree
  "Interval overlap"            → Segment Tree / Interval Tree

LEVEL 2 — REPRESENTATION
  Which storage fits the constraint?
  
  Dynamic, unknown size         → Linked Nodes
  Complete tree, cache perf     → Array (index arithmetic)
  Given as edges                → Adjacency List
  N-ary tree with binary ops    → LCRS (Left-Child Right-Sibling)
  Large integers/union-find     → Parent Array

LEVEL 3 — CONSTRUCTION STRATEGY
  Where does the data come from?
  
  Sorted array                  → Recursion on midpoint
  Traversal pair (in+pre/post)  → Divide & conquer
  Level-order (BFS) array       → Queue-based build
  Parent array                  → Group by parent
  Online (streaming)            → BST Insert / Heap Push

LEVEL 4 — ANALYSIS
  Time Complexity Master Table:
  ─────────────────────────────────────────────────────
  Structure       Insert    Search    Delete    Space
  ─────────────────────────────────────────────────────
  BST (worst)     O(N)      O(N)      O(N)      O(N)
  BST (avg)       O(logN)   O(logN)   O(logN)   O(N)
  AVL Tree        O(logN)   O(logN)   O(logN)   O(N)
  RB Tree         O(logN)   O(logN)   O(logN)   O(N)
  Min/Max Heap    O(logN)   O(N)      O(logN)   O(N)
  Trie            O(L)      O(L)      O(L)      O(N*L)
  Segment Tree    O(logN)   O(logN)   O(logN)   O(N)
  Fenwick Tree    O(logN)   O(logN)   O(logN)   O(N)
  B-Tree(order M) O(logN)   O(logN)   O(logN)   O(N)
  ─────────────────────────────────────────────────────
  L = length of string key
```

### Deliberate Practice — The Path to Top 1%

1. **Chunking:** Don't memorize code. Memorize the INVARIANT of each tree.
   - BST: left < root < right
   - Heap: parent ≤ children (min) or parent ≥ children (max)
   - AVL: |bf| ≤ 1 at every node
   - Trie: path spells key, edge = character

2. **Pattern Transfer:** Once you know Segment Tree for range sum, you can extend it to range min, range max, range GCD — same skeleton, different `combine()` function.

3. **The Recursive Lens:** Every tree problem can be stated as:
   - *"Solve for subtree rooted at X, given solutions for X.left and X.right"*
   - This is the **post-order thinking pattern** that separates top-tier problem solvers.

4. **Space-Time Tradeoffs:** Memoize positions (e.g., inorder index map) to trade O(N) space for O(N) time reduction. Always ask: *"Can I precompute something in O(N) that makes queries O(1) or O(log N)?"*

5. **The Monk Principle:** Practice one tree type per day. Implement from scratch — no references. Then implement a hard problem using it. Sleep on it. Review tomorrow. This is **spaced repetition + active recall** — the scientifically proven fastest path to mastery.

---

## QUICK REFERENCE — Decision Flowchart

```
                  DO YOU NEED A TREE?
                         │
         ┌───────────────┼───────────────┐
     Hierarchy?      Range Query?    Key-Value?
         │               │               │
    N-ary Tree    ┌───────┴──────┐    ┌──┴──┐
                 Sum/Min/Max?  Prefix?  Freq?  BST
                    │             │      │
              Segment Tree      BIT    (both work)
              (lazy=range upd)

     KEY-VALUE ORDERED? → BST family
       Need guaranteed O(log N)? → AVL (read) or RB (write)
       Need persistence? → Functional trees
       Need disk storage? → B-Tree

     STRING KEYS?
       Prefix operations? → Trie
       Pattern matching?  → Suffix Tree/Array
       Exact match only?  → Hash Map (not tree)

     PRIORITY?
       Always need min/max? → Heap
       Need ordered + priority? → Treap

     COMPRESSION?
       Huffman Tree

     ARITHMETIC EXPRESSION?
       Expression Tree (postfix build)
```

---

*"Mastery is not knowing every tree. It is knowing which tree the problem is asking for — before you write a single line of code."*

I'll craft a truly comprehensive `.md` guide. This will be a large, deeply structured document — let me build it properly.**3,443 lines. Every concept, every tree type, every construction method — in one document.**

Here's exactly what's inside and how to use it:

---

### What the Guide Covers

**Section 1–3 — The Foundations**
Every term defined precisely (root, leaf, depth, height, balance factor, successor, pivot, prefix, suffix, sentinel). Mathematical properties of trees with complexity derivations. You will never be confused by terminology again.

**Section 4 — The 5 Representation Methods**
This is the most overlooked topic. All 5 ways to store a tree in memory — Linked Nodes, Array Index Arithmetic, Parent Array, Adjacency List, and Left-Child Right-Sibling — each with C, Go, and Rust implementations. Knowing *which representation to choose* is a top-1% skill.

**Section 5 — 16 Tree Types**
Every major tree type: General N-ary, Binary Tree, BST, AVL (with all 4 rotation cases explained), Red-Black, Min/Max Heap, Trie, Segment Tree, Fenwick Tree (BIT), B-Tree, Expression Tree, Huffman Tree, Cartesian Tree, Treap, Splay Tree, Suffix Tree. Full code for the most important ones.

**Section 6 — Construction Algorithms**
How to build a tree from: BFS array, Inorder+Preorder, Inorder+Postorder, Sorted Array, Parent Array, Postfix Expression. These are the exact patterns that appear in interviews.

**Section 7 — Traversals**
Including the iterative inorder (stack-based) and the O(1) space Morris Traversal — a technique most candidates don't know.

**Section 8 — Cognitive Mastery Map**
A signal-to-tree-type decision table, time/space complexity master table, and the recursive lens mental model that separates expert problem solvers from average ones.

---

### Your Training Path

Start with Section 4 (representations) — implement each from scratch in all 3 languages. Then pick one tree type per day from Section 5, implement it blind (no reference), then solve one hard problem with it. The guide's decision flowchart at the end is your compass for every future problem.

Great question — this forces you to think about **what "visit" truly means**. It means *"execute any arbitrary operation using this node's context."* Here's every meaningful category:

---

### 📊 Data Operations
- **Accumulate** — add to a running sum, product, min, max (`sum += node.val`)
- **Collect** — append to a list/array (serialization, level-order output)
- **Count** — increment a counter (count nodes, count leaves, count nodes at depth K)
- **Hash** — feed value into a hash function (tree fingerprinting, duplicate detection)
- **Serialize** — encode into a string/byte stream (persistence, network transfer)

### ✏️ Mutation Operations
- **Update** — modify the node's value (`node.val = new_val`)
- **Augment** — store extra computed data into the node itself (`node.size = left.size + right.size + 1`)
- **Tag / Mark** — set a flag (`node.visited = true`, `node.color = BLACK`)
- **Lazy push-down** — in segment trees, propagate a pending operation from parent to children before going deeper
- **Assign rank/index** — number nodes in traversal order (useful for Euler tour, HLD)

### 🔗 Structural Operations
- **Rotate** — restructure around this node (AVL/RB tree rebalancing)
- **Swap children** — mirror/flip the subtree (`left ↔ right`)
- **Thread** — make a null pointer point somewhere else (Morris traversal: predecessor's right → current)
- **Splice / Detach** — cut this node out of the tree and reattach elsewhere
- **Clone / Copy** — allocate a new node with the same value (deep copy of tree)
- **Build parent pointer** — `node.parent = current_parent` (add upward links)

### 📐 Computation (Store Result Back or Return It)
- **Compute height** — `node.height = 1 + max(left.height, right.height)`
- **Compute balance factor** — `bf = height(left) - height(right)`
- **Compute subtree size** — `node.size = 1 + left.size + right.size`
- **Compute subtree sum / min / max** — used in segment tree build
- **Evaluate** — in expression trees, compute the arithmetic result at this operator node
- **Compute path cost** — accumulate edge weights from root to here

### ✅ Validation Operations
- **Assert BST property** — check `left.val < node.val < right.val`
- **Assert heap property** — check `node.val ≤ children`
- **Assert balance** — check `|bf| ≤ 1` (AVL)
- **Detect cycle** — in graph-trees, check if this node was already visited
- **Validate schema** — e.g., in a JSON/XML tree, check node type or attribute rules

### 🔍 Search & Decision Operations
- **Record path** — push node onto a path stack (backtracking, root-to-leaf paths)
- **Prune** — decide to stop recursing into a subtree entirely (branch and bound, alpha-beta)
- **Emit event** — trigger a callback/observer (event-driven tree walk)
- **Lookup external resource** — use node's key to query a hash map or database

### 🧠 Algorithm-Specific
- **Update Fenwick / Segment node** — during range update, modify the stored aggregate
- **Splay** — move this node to the root via a sequence of rotations (Splay Tree)
- **Merge two subtrees** at this node (Treap merge)
- **Split at this node** (Treap split)
- **Assign DFS in-time / out-time** — for LCA, subtree queries using Euler tour
- **Assign heavy/light label** — Heavy-Light Decomposition for path queries

---

### The Unified Mental Model

```
"Visiting a node" = executing a FUNCTION f(node, context)

f can:
  READ   → node.val, node.left, node.right, node.height ...
  WRITE  → node.val = x, node.color = RED, node.size = ...
  DECIDE → recurse left? recurse right? prune? rotate?
  EMIT   → push to stack, append to list, fire callback
  LINK   → change pointers (rotate, thread, splice)
```

The key insight is: **traversal order determines WHEN you visit, not WHAT you do.** Pre/In/Post/Level-order are just *scheduling policies* for when `f(node)` gets called. The operation itself is completely open.

This is why **higher-order tree traversal** is so powerful — you write one generic `traverse(root, f)` function and pass different `f`'s to count, collect, validate, serialize, evaluate, or transform — without rewriting the traversal logic.

