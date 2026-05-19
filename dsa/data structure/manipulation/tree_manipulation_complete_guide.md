# Complete & Comprehensive Guide to Tree Manipulation
> Deep internals, mental models, common mistakes, and production implementations in C, Go, and Rust.

---

## Table of Contents

1. [Foundational Mental Model](#1-foundational-mental-model)
2. [Tree Anatomy & Terminology](#2-tree-anatomy--terminology)
3. [Memory Layout & Internal Representations](#3-memory-layout--internal-representations)
4. [Tree Traversals — Every Variant](#4-tree-traversals--every-variant)
5. [Binary Search Trees (BST)](#5-binary-search-trees-bst)
6. [AVL Trees — Self-Balancing with Rotations](#6-avl-trees--self-balancing-with-rotations)
7. [Red-Black Trees](#7-red-black-trees)
8. [Heaps & Priority Queues](#8-heaps--priority-queues)
9. [Segment Trees](#9-segment-trees)
10. [Fenwick Trees (Binary Indexed Trees)](#10-fenwick-trees-binary-indexed-trees)
11. [Tries (Prefix Trees)](#11-tries-prefix-trees)
12. [B-Trees & B+ Trees](#12-b-trees--b-trees)
13. [Treaps & Randomized BSTs](#13-treaps--randomized-bsts)
14. [Splay Trees](#14-splay-trees)
15. [N-ary Trees & General Trees](#15-n-ary-trees--general-trees)
16. [Critical Tree Operations Deep Dive](#16-critical-tree-operations-deep-dive)
    - [Insertion](#insertion)
    - [Deletion (the hardest operation)](#deletion-the-hardest-operation)
    - [Rotations — Every Type](#rotations--every-type)
    - [Merging Trees](#merging-trees)
    - [Splitting Trees](#splitting-trees)
    - [Flattening / Serialization](#flattening--serialization)
    - [Lowest Common Ancestor (LCA)](#lowest-common-ancestor-lca)
    - [Tree Diameter & Path Problems](#tree-diameter--path-problems)
    - [Mirroring & Symmetry](#mirroring--symmetry)
17. [What You CAN Do vs What You CANNOT Do](#17-what-you-can-do-vs-what-you-cannot-do)
18. [Common Mistakes — Exhaustive List](#18-common-mistakes--exhaustive-list)
19. [Complexity Cheat Sheet](#19-complexity-cheat-sheet)
20. [Implementations: C, Go, Rust](#20-implementations-c-go-rust)

---

## 1. Foundational Mental Model

A **tree** is a connected, acyclic, undirected graph. In computer science, we root it: pick one node as the **root**, then every other node has exactly one parent.

**The one mental model to internalize:**

> A tree is a **recursive data structure**. Every node IS itself the root of a subtree. Every algorithm on trees is either: (a) do something at current node, (b) recurse left, (c) recurse right, in some order.

This is not a metaphor — it is the literal structural reality. When you internalize this, you stop writing iterative tree code that fights itself, and you start writing recursive code that matches the structure of the data.

**Why trees matter for bug bounty / systems work:**
- XML/HTML parsing is tree traversal (XXE, HTML injection contexts)
- File systems are trees (path traversal maps to tree traversal)
- Abstract Syntax Trees (ASTs) underpin all parsers, compilers, template engines (SSTI)
- JSON is a tree (deeply nested input = deep recursion = stack overflow DoS)
- OAuth/JWT structures are tree-validated claims
- DNS is a tree
- LDAP directory is a tree
- Process hierarchies are trees (privilege escalation chains)

---

## 2. Tree Anatomy & Terminology

```
                        [A]          <-- Root (depth=0, level=1)
                       /   \
                    [B]     [C]      <-- Internal nodes (depth=1)
                   /   \      \
                [D]    [E]    [F]    <-- D,E,F: leaves (depth=2)
                      /   \
                   [G]    [H]        <-- G,H: leaves (depth=3)
```

| Term | Definition |
|------|-----------|
| **Root** | The single node with no parent |
| **Leaf** | A node with no children |
| **Internal node** | A node with at least one child |
| **Edge** | A link between parent and child |
| **Height of a node** | Longest path from node DOWN to a leaf |
| **Depth of a node** | Distance from root DOWN to the node |
| **Height of tree** | Height of root node |
| **Degree of a node** | Number of children |
| **Level** | Depth + 1 (root is level 1) |
| **Subtree** | A node and all its descendants |
| **Ancestor** | Any node on the path from root to a node |
| **Descendant** | Any node in the subtree rooted at a node |
| **Sibling** | Nodes sharing the same parent |
| **Path** | Sequence of nodes connected by edges |
| **Forest** | Set of disjoint trees |

### Height vs Depth — The Most Confused Pair

```
Tree:       A           Height(A) = 3   Depth(A) = 0
           / \          Height(B) = 2   Depth(B) = 1
          B   C         Height(C) = 0   Depth(C) = 1
         / \            Height(D) = 1   Depth(D) = 2
        D   E           Height(D) = 0   Depth(D) = 2
           / \          Height(E) = 1   Depth(E) = 2
          F   G         Height(F) = 0   Depth(F) = 3
                        Height(G) = 0   Depth(G) = 3

Rule: Height flows UP (from leaves). Depth flows DOWN (from root).
```

### Tree Properties

- A tree with N nodes has exactly **N-1 edges** (no exceptions)
- A full binary tree: every node has 0 or 2 children
- A complete binary tree: all levels full except possibly last, filled left to right
- A perfect binary tree: all internal nodes have 2 children, all leaves at same level
- A degenerate (pathological) tree: every internal node has 1 child → essentially a linked list

```
Full:         Perfect:      Complete:     Degenerate:
    A             A             A              A
   / \          /   \          / \              \
  B   C        B     C        B   C              B
 / \          / \   / \      / \                  \
D   E        D   E F   G    D   E                  C
                                                    \
                                                     D
```

---

## 3. Memory Layout & Internal Representations

### 3.1 Linked Node Representation

The classic: each node is a heap-allocated struct with pointers.

```
Struct Layout in Memory (64-bit system):

Binary Tree Node:
+--------+--------+--------+
| left*  | right* |  data  |
| 8 bytes| 8 bytes| varies |
+--------+--------+--------+
  0x00     0x08    0x10

Example for int data (4 bytes + 4 bytes padding):
+--------+--------+------+----+
| left*  | right* | data | pad|
| 8 bytes| 8 bytes|4bytes|4 b |
+--------+--------+------+----+
Total: 24 bytes per node
```

Heap Layout for tree A->B, A->C:

```
Heap Memory:
Address    Content
0x1000:   [left=0x1018][right=0x1030][data=A]     <- Node A (root)
0x1018:   [left=NULL  ][right=NULL  ][data=B]     <- Node B
0x1030:   [left=NULL  ][right=NULL  ][data=C]     <- Node C

root pointer: 0x1000

Cache implication: Nodes scattered across heap → cache MISS on every pointer
follow. This is why array-based layouts exist.
```

### 3.2 Array-Based (Implicit) Representation

Used for complete binary trees (heaps, segment trees). Index math replaces pointers.

```
Tree:         1
             / \
            2   3
           / \ / \
          4  5 6  7

Array: [_, 1, 2, 3, 4, 5, 6, 7]  (1-indexed)
Index:  0  1  2  3  4  5  6  7

For node at index i:
  Parent      = i / 2   (integer division)
  Left child  = 2 * i
  Right child = 2 * i + 1
  Is root     = i == 1
  Is leaf     = 2*i > n (where n = number of nodes)

For 0-indexed:
  Parent      = (i - 1) / 2
  Left child  = 2 * i + 1
  Right child = 2 * i + 2
```

Memory layout — contiguous, cache-friendly:

```
           +-+-+-+-+-+-+-+-+
Array:     |_|1|2|3|4|5|6|7|
           +-+-+-+-+-+-+-+-+
           0 1 2 3 4 5 6 7

vs Linked:
[1]-->[2]  [3]  (non-contiguous, pointer chasing)
      |
     [4] [5]

Cache line = 64 bytes. Array fits ~16 ints per cache line.
Linked: every node access = potential cache miss.
```

### 3.3 Parent Array Representation

For union-find / disjoint set / general trees:

```
Nodes:    A   B   C   D   E
Index:    0   1   2   3   4
parent:  [-1,  0,  0,  1,  1]

parent[i] = -1 means root
parent[B] = 0 = A  → B's parent is A
parent[C] = 0 = A  → C's parent is A
parent[D] = 1 = B  → D's parent is B
parent[E] = 1 = B  → E's parent is B

Tree:        A
            / \
           B   C
          / \
         D   E
```

### 3.4 Adjacency List (General Graph-as-Tree)

```c
// Each node stores list of children
node[0] = {children: [1, 2]}   // A -> B, C
node[1] = {children: [3, 4]}   // B -> D, E
node[2] = {children: []}        // C (leaf)
node[3] = {children: []}        // D (leaf)
node[4] = {children: []}        // E (leaf)
```

### 3.5 Left-Child Right-Sibling (LCRS) Representation

Converts any N-ary tree into a binary tree:

```
Original N-ary tree:        LCRS representation:
        A                         A
      / | \                      /
     B  C  D                    B
    /\      \                  / \
   E  F      G                E   C
                              \    \
                               F    D
                                   /
                                  G

Each node: left = first child, right = next sibling
Powerful: converts complex structures to binary operations.
```

---

## 4. Tree Traversals — Every Variant

Traversal is the foundation of everything. Master ALL variants.

### 4.1 Depth-First Traversals

#### Inorder (Left → Root → Right)
- For BST: produces SORTED output (this is the key invariant)
- Use: BST validation, sorted iteration

```
Tree:         4
             / \
            2   6
           / \ / \
          1  3 5  7

Inorder:  1 → 2 → 3 → 4 → 5 → 6 → 7  (sorted!)

Algorithm:
1. Recurse left
2. Visit current
3. Recurse right
```

#### Preorder (Root → Left → Right)
- Root always first
- Use: tree copying, serialization, expression trees (prefix notation)

```
Same tree:
Preorder: 4 → 2 → 1 → 3 → 6 → 5 → 7

Algorithm:
1. Visit current
2. Recurse left
3. Recurse right
```

#### Postorder (Left → Right → Root)
- Root always last
- Use: tree deletion (delete children before parent), expression trees (postfix notation), calculating subtree sizes

```
Same tree:
Postorder: 1 → 3 → 2 → 5 → 7 → 6 → 4

Algorithm:
1. Recurse left
2. Recurse right
3. Visit current
```

### 4.2 Breadth-First (Level Order) Traversal

```
Tree:         4
             / \
            2   6
           / \ / \
          1  3 5  7

Level order: 4 → 2 → 6 → 1 → 3 → 5 → 7

Algorithm: Use a queue (FIFO)
1. Enqueue root
2. While queue not empty:
   a. Dequeue node, visit it
   b. Enqueue left child (if exists)
   c. Enqueue right child (if exists)
```

Queue state visualization:

```
Step 1: Queue=[4]          Visit: (empty)
Step 2: Queue=[2,6]        Visit: 4
Step 3: Queue=[6,1,3]      Visit: 4,2
Step 4: Queue=[1,3,5,7]    Visit: 4,2,6
Step 5: Queue=[3,5,7]      Visit: 4,2,6,1
...
```

### 4.3 Iterative Traversal with Explicit Stack

Recursive traversal risks **stack overflow on deep/degenerate trees** — critical for production systems. The iterative version is essential.

**Iterative Inorder:**
```
State machine using stack:
- Push nodes LEFT-ward until null
- Pop, visit, push RIGHT child, repeat

Trace for tree above:
Stack=[], curr=4
  Push 4, go left → Stack=[4], curr=2
  Push 2, go left → Stack=[4,2], curr=1
  Push 1, go left → Stack=[4,2,1], curr=NULL
  Pop 1, visit(1), go right → Stack=[4,2], curr=NULL
  Pop 2, visit(2), go right → Stack=[4], curr=3
  Push 3, go left → Stack=[4,3], curr=NULL
  Pop 3, visit(3), go right → Stack=[4], curr=NULL
  Pop 4, visit(4), go right → Stack=[], curr=6
  ...continues...
Output: 1,2,3,4,5,6,7 ✓
```

**Iterative Postorder (tricky — two approaches):**

Approach 1: Reverse of modified preorder (Root→Right→Left reversed = Left→Right→Root)
```
1. Do modified preorder: Root→Right→Left, push to output stack
2. Pop output stack (this gives Left→Right→Root = postorder)
```

Approach 2: Track "last visited" to avoid double-processing:
```
While stack not empty OR curr not null:
  if curr not null:
    push curr
    curr = curr.left
  else:
    peek = stack.top()
    if peek.right != null AND last_visited != peek.right:
      curr = peek.right  // process right subtree first
    else:
      visit(peek)
      last_visited = stack.pop()
```

### 4.4 Morris Traversal — O(1) Space Traversal

No stack, no recursion. Temporarily threads the tree (modifies right pointers, then restores).

```
Morris Inorder Algorithm:
1. curr = root
2. While curr != null:
   a. If curr.left == null:
      - Visit curr
      - curr = curr.right
   b. Else:
      - Find inorder predecessor (rightmost node in left subtree)
      - If predecessor.right == null:
        * predecessor.right = curr  (create thread)
        * curr = curr.left
      - Else (thread exists):
        * predecessor.right = null  (remove thread)
        * Visit curr
        * curr = curr.right

State change visualization:
Before threading:        After threading curr=4:
      4                        4
     / \                      / \
    2   6          →         2   6
   / \                      / \
  1   3                    1   3
                                \
                                 4* (thread, not real child)
```

Morris traversal is O(N) time, O(1) space — critical when stack space is limited.

### 4.5 Zigzag / Spiral Level Order

```
Tree:        1
            / \
           2   3
          / \ / \
         4  5 6  7

Zigzag: Level 0 (L→R): 1
        Level 1 (R→L): 3, 2
        Level 2 (L→R): 4, 5, 6, 7

Implementation: Use two stacks (or deque with direction flag)
- Stack1: current level
- Stack2: next level
- Alternate L→R and R→L push order
```

---

## 5. Binary Search Trees (BST)

### BST Invariant

```
For EVERY node N:
  ALL nodes in left subtree  < N.value
  ALL nodes in right subtree > N.value

Valid BST:           Invalid BST:
      5                   5
     / \                 / \
    3   7               3   7
   / \ / \             / \ / \
  2  4 6  8           2  6 4  8
                           ^
                    6 is in left subtree of 7
                    but 6 < 7 → wait, that's fine
                    Actually: 4 is in right subtree of 3
                    but 4 < 5 → VALID
                    6 is in left subtree of 7 → VALID
                    Wait: 6 is in left subtree of 7 and 6 > 5 → check
                    VALID BST: left < root AND right > root at EVERY level

Common mistake: checking only parent-child, not entire subtree!
Invalid BST (looks valid locally):
      5
     / \
    1   4    ← 4 < 5, so right child 4 violates BST property!
       / \
      3   6
```

**Critical validation insight:** When validating a BST, you must pass down bounds:

```
validate(node, min=-∞, max=+∞):
  if node == null: return true
  if node.val <= min OR node.val >= max: return false
  return validate(node.left, min, node.val) AND
         validate(node.right, node.val, max)

For node 3 in right subtree of 5:
  It must satisfy: 5 < 3 < +∞ → FALSE! 3 < 5 so invalid.
```

### BST Search

```
Search(root, target):
  if root == null: return NOT_FOUND
  if root.val == target: return FOUND
  if target < root.val: return Search(root.left, target)
  else: return Search(root.right, target)

Trace: Search(root=5, target=4)
  5 != 4, 4 < 5 → go left → node=3
  3 != 4, 4 > 3 → go right → node=4
  4 == 4 → FOUND ✓

Best case: O(log n) — balanced tree
Worst case: O(n) — degenerate tree (linked list)
```

### BST Insert

```
Insert(root, val):
  if root == null: return new Node(val)
  if val < root.val: root.left = Insert(root.left, val)
  else if val > root.val: root.right = Insert(root.right, val)
  return root  // val == root.val: handle duplicates as needed

Inserting 3.5 into BST:
Before:           After:
    5                 5
   / \               / \
  3   7             3   7
 / \               / \
2   4             2   4
                     /
                    3.5
```

### BST Deletion — The Hard One

Three cases, and case 3 is where bugs live:

```
CASE 1: Node has NO children (leaf)
  Just remove it.
  Delete 2:
      5              5
     / \    →       / \
    3   7           3   7
   / \               \
  2   4               4

CASE 2: Node has ONE child
  Replace node with its child.
  Delete 3 (has only right child 4):
      5              5
     / \    →       / \
    3   7           4   7
     \
      4

CASE 3: Node has TWO children (the tricky case)
  Find INORDER SUCCESSOR (smallest node in right subtree)
  OR INORDER PREDECESSOR (largest node in left subtree)
  Copy that value into current node
  Delete that successor/predecessor node (now guaranteed to have ≤1 child)

  Delete 5 (root, has two children):
      5                7 (successor)        6
     / \    find    → min of right =   →   / \
    3   7   succ      6 in {7,6,8}        3   7
   / \ / \                               / \   \
  2  4 6  8                             2   4   8

  Wait, let me redo: successor of 5 is 6 (smallest in right subtree {7,6,8})
  Copy 6 to root, delete 6 from right subtree:
      6
     / \
    3   7
   / \   \
  2   4   8
```

**The successor-deletion subtlety:**

```
The inorder successor of a node N is:
  IF N.right exists: leftmost node in N.right subtree
  ELSE: first ancestor where N is in the left subtree

Finding leftmost (min) of a subtree:
  min(node):
    while node.left != null: node = node.left
    return node

The successor has NO left child (it's the leftmost!)
So deleting it is always CASE 1 or CASE 2 — never CASE 3.
This breaks the recursion. Key insight for implementation.
```

---

## 6. AVL Trees — Self-Balancing with Rotations

### Balance Factor

```
Balance Factor (BF) = Height(left subtree) - Height(right subtree)
Valid BF: {-1, 0, +1}
BF = +2 or higher: LEFT-HEAVY (need right rotation)
BF = -2 or lower: RIGHT-HEAVY (need left rotation)

Computing height at each node:
height(null) = -1 (or 0, depending on convention — be consistent!)
height(node) = 1 + max(height(left), height(right))
```

### The Four Rotation Cases

Every imbalance in an AVL tree is exactly one of these four cases. Learn to identify them by the BF of the node AND its heavy child.

#### Case 1: Left-Left (LL) — Single Right Rotation

```
Trigger: BF(z) = +2, BF(y) = +1 or 0

BEFORE:         AFTER:
    z(+2)           y(0)
   /                / \
  y(+1)    →      x    z
 /
x

Rotation: Right rotate at z
  z.left = y.right
  y.right = z
  update heights: z first, then y

Concrete example:
    30(+2)          20(0)
   /        →      /    \
  20(+1)          10     30
 /
10
```

#### Case 2: Right-Right (RR) — Single Left Rotation

```
Trigger: BF(z) = -2, BF(y) = -1 or 0

BEFORE:         AFTER:
  z(-2)              y(0)
    \                / \
     y(-1)  →       z   x
       \
        x

Rotation: Left rotate at z
  z.right = y.left
  y.left = z

Concrete example:
  10(-2)           20(0)
    \      →      /    \
    20(-1)        10    30
      \
      30
```

#### Case 3: Left-Right (LR) — Double Rotation

```
Trigger: BF(z) = +2, BF(y) = -1

BEFORE:           STEP 1 (left rotate y):    STEP 2 (right rotate z):
    z(+2)                z(+2)                      x(0)
   /                    /                           / \
  y(-1)      →         x               →           y   z
    \                 /
     x               y

Concrete example:
    30(+2)          30(+2)          20(0)
   /         →     /        →     /    \
  10(-1)          20              10    30
    \            /
    20          10

Step 1: Left rotate at y=10 → 20 becomes new left child of 30
Step 2: Right rotate at z=30
```

#### Case 4: Right-Left (RL) — Double Rotation

```
Trigger: BF(z) = -2, BF(y) = +1

BEFORE:         STEP 1 (right rotate y):  STEP 2 (left rotate z):
  z(-2)               z(-2)                      x(0)
    \                   \                        / \
     y(+1)  →            x            →        z   y
    /                     \
   x                       y

Concrete example:
  10(-2)           10(-2)          20(0)
    \      →          \    →      /    \
    30(+1)            20         10    30
   /                   \
  20                   30
```

### AVL Insert Algorithm

```
avl_insert(root, val):
  1. Perform standard BST insert
  2. Update height of current node
  3. Compute balance factor
  4. If BF == +2:
     - If BF(left child) >= 0: LL → right rotate
     - If BF(left child) < 0:  LR → left rotate left child, then right rotate
  5. If BF == -2:
     - If BF(right child) <= 0: RR → left rotate
     - If BF(right child) > 0:  RL → right rotate right child, then left rotate
  6. Return (possibly new) root of this subtree

After every insert: at MOST O(log n) rotations (usually just 1 or 2).
```

### AVL Height Guarantee

```
For an AVL tree with n nodes:
  height ≤ 1.44 * log₂(n+2) - 0.328

Minimum nodes for height h (Fibonacci relationship):
  N(0) = 1, N(1) = 2, N(h) = N(h-1) + N(h-2) + 1

This is Fibonacci-like → height grows as O(log n) — GUARANTEED.
```

---

## 7. Red-Black Trees

### Properties (All Must Hold Simultaneously)

```
1. Every node is RED or BLACK.
2. The root is BLACK.
3. Every NULL (leaf sentinel) is BLACK.
4. If a node is RED, both children are BLACK. (No two reds in a row)
5. For each node, all paths from that node to descendant NULLs
   contain the same number of BLACK nodes. (Black-height property)

Valid Red-Black Tree:
         7(B)
        /    \
      3(R)   18(R)
      / \    /  \
    2(B)4(B)11(B)19(B)
    /         \
  1(R)        14(R)

NULL sentinels (all black, not shown) hang off every leaf.

Black height from root to any null = 3 (counting 7, then one more B on each path)
Path 7→3→2→1→NULL: 7(B),3(R),2(B),1(R),NULL(B) → 3 black nodes ✓
Path 7→18→19→NULL: 7(B),18(R),19(B),NULL(B) → 3 black nodes ✓
```

### Why 5 Properties → O(log n) Height

```
Black-height h_b ≥ 1 → at least 2^(h_b) - 1 internal nodes
Total height h ≤ 2*h_b (because you can at most double by inserting reds)
Therefore: n ≥ 2^(h/2) - 1 → h ≤ 2*log₂(n+1)
```

### RB Tree Insertion Cases

Insert as RED (to not violate black-height property immediately).

```
Let: Z = inserted node (RED), P = parent, U = uncle, G = grandparent

CASE 1: Z is root → color BLACK. Done.

CASE 2: P is BLACK → no violation (red under black is fine). Done.

CASE 3: P is RED, U is RED (uncle is red):
  Recolor: P→BLACK, U→BLACK, G→RED
  Then treat G as newly inserted node (recurse up)

  Before:      G(B)          After:       G(R)  ← now check G
              /    \                     /    \
           P(R)   U(R)              P(B)   U(B)
           /                        /
          Z(R)                     Z(R)

CASE 4: P is RED, U is BLACK, Z is inner grandchild
  (P is left child of G, Z is right child of P)
  → Rotate Z to P's position (left rotate at P)
  Now Z is in P's old position, P is Z's left child
  → Fall into Case 5

CASE 5: P is RED, U is BLACK, Z is outer grandchild
  (P is left child of G, Z is left child of P)
  → Rotate at G (right rotate)
  → Recolor: P→BLACK, G→RED

  Before Case 5:              After Case 5:
       G(B)                      P(B)
      /    \                    /    \
   P(R)   U(B)    →          Z(R)   G(R)
   /                                   \
  Z(R)                                U(B)
```

### RB vs AVL: When to Use Which

```
Metric              AVL Tree              Red-Black Tree
────────────────────────────────────────────────────────
Height guarantee    ≤ 1.44 log n          ≤ 2 log n
Lookup speed        Faster (shorter)      Slightly slower
Insert/Delete       More rotations        Fewer rotations (≤3)
Best for            Read-heavy            Write-heavy
Used in             Database indexes      std::map (C++), TreeMap (Java),
                                          Linux kernel (CFS scheduler)
Rebalancing ops     O(log n)              O(1) amortized
```

---

## 8. Heaps & Priority Queues

### Heap Property

```
MAX HEAP: parent.value >= children.values (root = maximum)
MIN HEAP: parent.value <= children.values (root = minimum)

Max Heap:              Min Heap:
      100                   1
     /    \               /   \
    90     80            5     3
   /  \   /  \         /  \  /  \
  70  60 50  40       10   7 8   4

CRITICAL: A heap is NOT a BST.
Left child vs right child ordering: UNDEFINED in a heap.
Heap only guarantees parent > children (or parent < children).
```

### Heap as Array

```
Max Heap:        Array (1-indexed):
      100         [_, 100, 90, 80, 70, 60, 50, 40]
     /    \            1   2   3   4   5   6   7
    90     80
   /  \   /  \
  70  60 50  40

node[i].left  = node[2i]
node[i].right = node[2i+1]
node[i].parent = node[i/2]

This is perfectly cache-friendly and requires ZERO pointer storage.
For n elements: O(n) space (no overhead).
```

### Heapify-Up (Sift-Up) — After Insert

```
Insert 95 into max heap:
Step 1: Append to array end (place at rightmost leaf)
Array: [_, 100, 90, 80, 70, 60, 50, 40, 95]
Tree:
      100
     /    \
    90     80
   /  \   /  \
  70  60 50  40
  /
 95

Step 2: Sift Up — compare with parent, swap if larger
  95 > 70? YES → swap
      100
     /    \
    90     80
   /  \   /  \
  95  60 50  40
  /
 70

  95 > 90? YES → swap
      100
     /    \
    95     80
   /  \   /  \
  90  60 50  40
  /
 70

  95 > 100? NO → stop

Final:
      100
     /    \
    95     80
   /  \   /  \
  90  60 50  40
  /
 70
```

### Heapify-Down (Sift-Down) — After Extract Max

```
Extract Max (remove 100):
Step 1: Remove root, put last element (40) at root
Array: [_, 40, 95, 80, 90, 60, 50]
Tree:
      40
     /    \
    95     80
   /  \   /
  90  60 50

Step 2: Sift Down — swap with LARGER child
  40 vs children 95 and 80 → larger child = 95 → swap
      95
     /    \
    40     80
   /  \   /
  90  60 50

  40 vs children 90 and 60 → larger child = 90 → swap
      95
     /    \
    90     80
   /  \   /
  40  60 50

  40 vs children (none, it's a leaf) → stop

Final max heap:
      95
     /    \
    90     80
   /  \   /
  40  60 50
```

### Build Heap — O(n) not O(n log n)

```
Naive: insert n elements one by one = O(n log n)
Floyd's algorithm: start from last internal node, sift down each

Last internal node = n/2 (1-indexed)
for i from n/2 down to 1: sift_down(i)

Why O(n)? Most nodes are near leaves (need little sifting).
Height h: 2^h nodes, each needs O(h) sifts
Total = Σ (h * n/2^h) = O(n) [geometric series convergence]

Example: array [3, 1, 6, 5, 2, 4]
Treated as tree:
        3
       / \
      1   6
     / \ /
    5  2 4

Last internal: index 3 (value=6). Start there.
heapify(3): 6 > 4 → no swap (6 is leaf's parent... wait 4 is child of 6)
             6 > 4 → no, 6 > 4, fine. Actually:
             children of idx 3 (val=6): idx 6 (val=4). 6 > 4, no swap.

heapify(2): val=1. Children: idx 4 (val=5), idx 5 (val=2). Max child=5. 1<5 → swap.
        3
       / \
      5   6
     / \ /
    1  2 4

heapify(1): val=3. Children: idx 2 (val=5), idx 3 (val=6). Max child=6. 3<6 → swap.
        6
       / \
      5   3
     / \ /
    1  2 4

Then sift down 3 at idx 3: child is 4. 3<4 → swap.
        6
       / \
      5   4
     / \ /
    1  2 3

Result: Valid max heap in O(n) time.
```

---

## 9. Segment Trees

A segment tree answers range queries (sum, min, max, GCD, etc.) and supports point/range updates efficiently.

### Structure

```
Array: [2, 4, 3, 1, 6, 7, 2, 5]  (indices 1..8)

Segment Tree for RANGE SUM:
                  [30]
              (range 1-8)
             /            \
          [10]            [20]
        (1-4)            (5-8)
        /    \           /    \
      [6]    [4]       [13]   [7]
     (1-2)  (3-4)     (5-6)  (7-8)
     / \    / \       / \    / \
   [2] [4][3] [1]  [6] [7][2] [5]
   (1) (2)(3) (4)  (5) (6)(7) (8)

Array representation (1-indexed, size = 4*n):
[_, 30, 10, 20, 6, 4, 13, 7, 2, 4, 3, 1, 6, 7, 2, 5]
 0   1   2   3  4  5   6  7  8  9 10 11 12 13 14 15

Node i covers range [l, r]:
  Left child = 2i  covers [l, mid]
  Right child= 2i+1 covers [mid+1, r]
  where mid = (l+r)/2
```

### Range Query

```
Query(node, node_l, node_r, query_l, query_r):
  if query range completely OUTSIDE node range: return IDENTITY (0 for sum)
  if query range completely COVERS node range: return node.value
  mid = (node_l + node_r) / 2
  return Query(left_child, node_l, mid, query_l, query_r) +
         Query(right_child, mid+1, node_r, query_l, query_r)

Cases:
  [nnnn] = node range
  [qqqq] = query range

  No overlap:  [nnnn]  [qqqq]  → return 0
  Full cover:  [nnnn] fully inside [qqqq] → return node.val
  Partial:     [nn[qq]nn] → recurse to children
               [qq[nn]qq]

At most O(4 * log n) nodes visited per query → O(log n)
```

### Lazy Propagation — Range Updates

Without lazy: updating range [l,r] requires O(n) updates.
With lazy: defer updates, propagate only when needed.

```
Lazy tree stores pending updates at each node.
When we need a node's children: PUSH DOWN the lazy update first.

pushdown(node):
  if lazy[node] != 0:
    lazy[2*node] += lazy[node]     // propagate to left child
    lazy[2*node+1] += lazy[node]   // propagate to right child
    tree[2*node] += lazy[node] * (size of left child's range)
    tree[2*node+1] += lazy[node] * (size of right child's range)
    lazy[node] = 0                 // clear current node's lazy

Range update "add v to all elements in [l,r]":
  update(node, node_l, node_r, l, r, v):
    if no overlap: return
    if full cover:
      tree[node] += v * (node_r - node_l + 1)
      lazy[node] += v
      return
    pushdown(node)
    mid = (node_l + node_r) / 2
    update(left, node_l, mid, l, r, v)
    update(right, mid+1, node_r, l, r, v)
    tree[node] = tree[2*node] + tree[2*node+1]  // pull up
```

---

## 10. Fenwick Trees (Binary Indexed Trees)

Simpler than segment trees for prefix sum queries. Exploits binary representation.

### The Key Insight

```
lowbit(i) = i & (-i)  (extracts lowest set bit)

i=6: binary 110 → lowbit = 010 = 2
i=4: binary 100 → lowbit = 100 = 4
i=12: binary 1100 → lowbit = 100 = 4

BIT[i] stores sum of elements from index (i - lowbit(i) + 1) to i

For array [3,2,1,4,5,2,7,3]:
Index:  1  2  3  4  5  6  7  8
BIT[1] = A[1]                       = 3       covers [1,1]
BIT[2] = A[1]+A[2]                  = 5       covers [1,2]
BIT[3] = A[3]                       = 1       covers [3,3]
BIT[4] = A[1]+A[2]+A[3]+A[4]       = 10      covers [1,4]
BIT[5] = A[5]                       = 5       covers [5,5]
BIT[6] = A[5]+A[6]                  = 7       covers [5,6]
BIT[7] = A[7]                       = 7       covers [7,7]
BIT[8] = A[1]+..+A[8]              = 27      covers [1,8]

Visual:
Idx:  1   2   3   4   5   6   7   8
      |   |   |   |   |   |   |   |
1:   [3]
2:   [3   2   ]
3:           [1]
4:   [3   2   1   4   ]
5:                   [5]
6:                   [5   2   ]
7:                           [7]
8:   [3   2   1   4   5   2   7   3   ]
```

### Prefix Sum Query

```
prefix_sum(i):
  sum = 0
  while i > 0:
    sum += BIT[i]
    i -= lowbit(i)  // move to parent
  return sum

prefix_sum(7):
  i=7 (111): sum += BIT[7]=7, i = 7-1 = 6
  i=6 (110): sum += BIT[6]=7, i = 6-2 = 4
  i=4 (100): sum += BIT[4]=10, i = 4-4 = 0
  return 7+7+10 = 24 ✓ (3+2+1+4+5+2+7=24)

O(log n) per query
```

### Point Update

```
update(i, delta):
  while i <= n:
    BIT[i] += delta
    i += lowbit(i)  // move to next responsible index

update(3, +5) [add 5 to index 3]:
  i=3 (011): BIT[3] += 5, i = 3+1 = 4
  i=4 (100): BIT[4] += 5, i = 4+4 = 8
  i=8 (1000): BIT[8] += 5, i = 8+8 = 16 > n → stop

O(log n) per update
```

---

## 11. Tries (Prefix Trees)

### Structure

```
Insert: "cat", "car", "card", "care", "bat"

          root
         /    \
        c      b
        |      |
        a      a
       / \     |
      t   r    t
          |
         [d,e]  ← both 'd' and 'e' are children

Full trie:
root
├── c
│   └── a
│       ├── t (end)
│       └── r
│           ├── d (end)
│           └── e (end)
└── b
    └── a
        └── t (end)

Each node: array of 26 children (for lowercase English)
           OR hashmap for arbitrary characters
           + isEndOfWord flag

Memory per node (array approach):
+----------------------------------+-------+
| children[26] (26 pointers)       | isEnd |
| 26 * 8 bytes = 208 bytes         | 1 byte|
+----------------------------------+-------+
Total: ~209 bytes per node
Optimization: use hashmap or compressed trie (patricia trie)
```

### Trie Operations

```
Search "car": root→c→a→r (found, and isEnd=true) → FOUND
Search "ca":  root→c→a (found, but isEnd=false) → NOT A WORD (but prefix exists)
Search "cat": root→c→a→t (found, isEnd=true) → FOUND
Search "cap": root→c→a→p (p doesn't exist) → NOT FOUND

Insert: O(L) where L = length of word
Search: O(L)
Space: O(ALPHABET_SIZE * L * N) worst case

Prefix search advantage: find all words with prefix "car" in O(L + results)
vs BST which is O(n) for prefix matching
```

### Compressed Trie (Patricia Trie / Radix Tree)

```
Regular trie for "romane","romanus","romulus","rubens","ruber","rubicon","rubicundus":

r
├── o
│   ├── m
│   │   ├── a
│   │   │   ├── n
│   │   │   │   ├── e (end)
│   │   │   │   └── u
│   │   │   │       └── s (end)
│   └── u
│       └── l
│           └── u
│               └── s (end)
└── u
    └── b
        ├── e
        │   ├── n
        │   │   └── s (end)
        │   └── r (end)
        └── i
            └── c
                ├── o
                │   └── n (end)
                └── u
                    └── n
                        └── d
                            └── u
                                └── s (end)

Patricia Trie (compress single-child chains):
r
├── oman → e (end) / us (end) / ulus (end)
└── ub
    ├── e → ns (end) / r (end)
    └── ic → on (end) / undus (end)

Nodes reduced from ~40 to ~10. Used in: IP routing tables, autocomplete,
spell checkers, Linux VFS, HTTP routing in web frameworks.
```

---

## 12. B-Trees & B+ Trees

### Why B-Trees Exist

Disk I/O is ~1000x slower than RAM access. The goal: minimize the number of disk reads/writes. A B-tree of order M stores M-1 keys per node, so each disk read (one node = one page = 4KB-16KB) fetches many keys.

```
Disk page: 4096 bytes
Key+value: 8 bytes each
Children pointers: 8 bytes each
B-tree order M: (M-1)*8 + M*8 ≤ 4096 → M ≈ 256

With M=256: height ≈ log₂₅₆(n)
For n=1 million: height ≈ 2-3 disk reads!
BST for same: height ≈ 20 disk reads.
```

### B-Tree Properties (Order M / Degree T)

```
1. Every node has at most M-1 keys and M children.
2. Every non-root node has at least ⌈M/2⌉-1 keys.
3. The root has at least 1 key (unless tree is empty).
4. All leaves are at the SAME LEVEL.
5. A non-leaf node with k keys has exactly k+1 children.
6. Keys in a node are sorted.
7. Keys in node[i] are: children[i-1].keys < node[i].key < children[i].keys

B-Tree of order 5 (min 2, max 4 keys per node):

         [30, 60]
        /    |    \
  [10,20] [40,50] [70,80,90]

Leaf nodes contain actual data (or pointers to data records).
```

### B-Tree vs B+ Tree

```
B-Tree:              B+ Tree:
- Data at ALL nodes  - Data ONLY at LEAF nodes
- No duplicate keys  - Internal nodes duplicate leaf keys (just for routing)
- No linked leaves   - Leaves linked as doubly-linked list

B+ Tree structure:
            [30, 70]           ← internal (routing) nodes
           /    |    \
       [10,20] [40,60] [70,80,90]   ← leaves (all data here)
          ↔       ↔        ↔        ← linked list!

B+ Tree advantages:
1. Range queries: follow leaf linked list (no tree traversal)
2. All queries same cost (always reach leaf level)
3. Better cache utilization (internal nodes are pure index)

Used in: PostgreSQL, MySQL InnoDB, SQLite, Oracle, NTFS, ext4
```

### B-Tree Insertion (Split on Overflow)

```
Order 3 B-tree (max 2 keys, min 1 key per node):
Insert: 1, 2, 3, 4, 5, 6, 7

After inserting 1,2:
[1, 2]

Insert 3: overflow! Split:
       [2]
      /   \
    [1]   [3]

Insert 4:
       [2]
      /   \
    [1]   [3, 4]

Insert 5: right leaf overflows, split:
       [2, 4]
      /  |   \
    [1] [3]  [5]

Insert 6:
       [2, 4]
      /  |   \
    [1] [3]  [5, 6]

Insert 7: right leaf overflows, split and push up:
Root overflows too! Split root:
         [4]
        /   \
      [2]   [6]
     / \   /   \
   [1] [3][5]  [7]
```

---

## 13. Treaps & Randomized BSTs

A treap combines a BST (by key) and a heap (by priority). Priorities are assigned randomly.

```
Nodes: (key, priority)

Insert (A,9), (C,3), (E,7), (D,5), (B,6):

BST by key, heap by priority (max-heap):

         (A,9)     ← highest priority = root
             \
            (C,3)
           /    \
         (B,6)  (E,7)
                /
              (D,5)

After rotations to satisfy heap property:
         (A,9)
             \
            (E,7)
            /   \
          (B,6) ...
          
Wait, let me build it properly:
Keys sorted: A<B<C<D<E
Priorities:  A=9, B=6, C=3, D=5, E=7

By heap: root must be A (priority 9)
A's right subtree contains B,C,D,E (all keys > A)
Root of right subtree: E (priority 7, highest among B,C,D,E)
E's left: B,C,D. Root: B (priority 6)
B's right: C,D. Root: D (priority 5)
D's left: C

         A(9)
              \
               E(7)
              /
            B(6)
               \
                D(5)
               /
              C(3)

This is BOTH a valid BST (inorder: A,B,C,D,E) AND max-heap by priority.
Random priorities → tree is balanced with high probability → O(log n) expected height.
```

### Treap Split and Merge

Treaps support O(log n) split and merge — making them extremely flexible.

```
Split(treap, key) → (left_treap, right_treap):
  left: all nodes with key ≤ split_key
  right: all nodes with key > split_key

Merge(left, right) → treap:
  All keys in left < all keys in right (precondition)
  Algorithm: pick root as whichever root has higher priority,
             recursively merge the relevant child with the other treap.

Applications:
- Insert: split at key, create new node, merge left + new + right
- Delete: split into left, mid (single node), right → merge left and right
- Interval operations, order statistics
```

---

## 14. Splay Trees

### Splay Operation

Every accessed node is moved to the root via rotations. Recent nodes stay near root — exploits temporal locality.

```
Three splay cases:

ZIG (root's child):
  x is child of root r, one rotation:
       r               x
      /       →       / \
     x               A   r
    / \                  / \
   A   B                B   C
     \
      C (r's right child)

ZIG-ZIG (same direction):
  x and p (parent) are both left children:
       g               x
      /               / \
     p      →        A   p
    /                   / \
   x                   B   g
  / \                      / \
 A   B                    C   D
         (g.right child D not shown above, moving...)

ZIG-ZAG (opposite direction):
  x is left child of p which is right child of g:
     g               x
      \             / \
       p    →      g   p
      /           / \ / \
     x           A  B C  D
    / \
   B   C

By always splaying accessed node to root, amortized O(log n) per operation.
Worst case per operation: O(n). But amortized over m ops: O(m log n).
Used in: caches, network routers, Linux memory allocator (for VMA tree)
```

---

## 15. N-ary Trees & General Trees

### Representations

```
N-ary tree: each node can have any number of children

Representation 1: Array of children
struct Node {
  int val;
  Node* children[MAX_CHILDREN];
  int num_children;
};

Representation 2: Dynamic list of children
struct Node {
  int val;
  vector<Node*> children;
};

Representation 3: Left-Child Right-Sibling (LCRS)
struct Node {
  int val;
  Node* first_child;   // leftmost child
  Node* next_sibling;  // next sibling
};

Tree:        A
           / | \
          B  C  D
         / \
        E   F

LCRS:        A
            /
           B → C → D
          /
         E → F

Key: LCRS lets you treat any N-ary tree as a binary tree.
     Any binary tree algorithm works on LCRS-encoded N-ary tree.
```

---

## 16. Critical Tree Operations Deep Dive

### Insertion

**General principles:**
```
1. Find insertion position (BST: comparison-guided; heap: next array slot)
2. Place new node
3. Restore structural property (BST: none; AVL: rotations; RB: recolor+rotate; heap: sift-up)

Position finding: O(log n) for balanced trees, O(n) worst case for BST
Restoration: O(log n) for AVL/RB, O(log n) for heap
Total: O(log n) for balanced trees
```

### Deletion (The Hardest Operation)

**Step-by-step decision tree:**
```
DELETE node N:

Step 1: Find N (O(log n))

Step 2: How many children does N have?
  0 children → simply remove, update parent.child = null
  1 child → replace N with its child, update parent and child pointers
  2 children → find inorder successor S (leftmost node in right subtree)
               copy S.value into N.value
               delete S (which has at most 1 child → case 0 or 1)

Step 3: Rebalance
  AVL: walk back up tree, check BF, rotate if needed
  RB: fix double-black violations (complex, 6 cases)
  Heap: sift-down from deletion point

RB Tree Deletion Cases (fixing double-black):
  After removing a black node, the path is short one black → "double black"
  
  Case 1: Double-black's sibling is RED
    → Rotate toward double-black, recolor
    → Falls into case 2,3,4
    
  Case 2: Sibling is BLACK, sibling's children both BLACK
    → Recolor sibling to RED, propagate double-black to parent
    → If parent was RED: make it BLACK and done
    → If parent was BLACK: parent becomes double-black, recurse
    
  Case 3: Sibling BLACK, sibling's far child BLACK, near child RED
    → Rotate sibling away from double-black
    → Falls into Case 4
    
  Case 4: Sibling BLACK, sibling's far child RED
    → Rotate parent toward double-black
    → Recolor: sibling takes parent's color, parent→BLACK, far child→BLACK
    → Done! Double-black resolved.
```

### Rotations — Every Type

```
LEFT ROTATION at node x:
(x's right child y becomes new root of subtree)

Before:           After:
  x                 y
 / \               / \
A   y     →       x   C
   / \           / \
  B   C         A   B

Code:
  left_rotate(x):
    y = x.right
    x.right = y.left      // B becomes x's right
    if y.left: y.left.parent = x
    y.parent = x.parent   // y takes x's position
    if !x.parent: root = y
    elif x == x.parent.left: x.parent.left = y
    else: x.parent.right = y
    y.left = x            // x becomes y's left
    x.parent = y
    // update heights (for AVL)

RIGHT ROTATION at node y:
(symmetric)

Before:           After:
    y                 x
   / \               / \
  x   C     →       A   y
 / \                   / \
A   B                 B   C

Code:
  right_rotate(y):
    x = y.left
    y.left = x.right
    if x.right: x.right.parent = y
    x.parent = y.parent
    if !y.parent: root = x
    elif y == y.parent.right: y.parent.right = x
    else: y.parent.left = x
    x.right = y
    y.parent = x
```

**Critical rotation mistakes:**
```
1. Forgetting to update parent pointers (in nodes with parent field)
2. Wrong order of assignments (overwriting pointers before saving them)
3. Not updating heights AFTER rotation (AVL trees)
4. Rotating the wrong node (rotate at imbalanced node, not its child)
5. Not handling the case where rotated node was root
```

### Merging Trees

```
MERGE TWO BSTs (all keys of tree1 < all keys of tree2):
Method 1: Flatten both to sorted arrays, merge arrays, rebuild tree
  → O(m+n) time, O(m+n) space

Method 2 (for treaps): merge by priority
  O(log(m+n)) expected for treaps

Method 3: Append smallest tree's rightmost path to largest tree
  Complex, but O(h1 + h2) time

MERGE TWO HEAPS:
  Binary heap: merge by concatenating arrays, then build heap
  → O(n) time (Floyd's algorithm on combined array)
  
  Binomial heap: O(log n) merge
  Fibonacci heap: O(1) amortized merge (just link root lists!)
  
  Fibonacci Heap root list merge:
  H1 root list: A ↔ B ↔ C (circular doubly-linked)
  H2 root list: D ↔ E (circular doubly-linked)
  
  Merge: just splice the two circular lists together
  Before: ...→A→B→C→A...  and  ...→D→E→D...
  After:  ...→A→B→C→D→E→A...
  O(1) operation!
```

### Splitting Trees

```
SPLIT BST at key k:
  left_tree: all nodes with key ≤ k
  right_tree: all nodes with key > k

Algorithm (recursive):
  split(node, k) → (left, right):
    if node == null: return (null, null)
    if node.key ≤ k:
      (rl, right) = split(node.right, k)
      node.right = rl
      return (node, right)
    else:
      (left, lr) = split(node.left, k)
      node.left = lr
      return (left, node)

Trace: Split BST [1,2,3,4,5] at k=3:
       4
      / \
     2   5
    / \
   1   3

split(4, k=3):
  4.key=4 > 3 → split left subtree (rooted at 2) at k=3
  split(2, k=3):
    2.key=2 ≤ 3 → split right subtree (rooted at 3) at k=3
    split(3, k=3):
      3.key=3 ≤ 3 → split right subtree (null) at k=3
      return (3, null)
    2.right = 3 (left part)
    return (2, null)  ← left=subtree{1,2,3}, right=null
  4.left = null
  return (null, 4)   ← left=null, right=subtree{4,5}

Wait, let me re-trace carefully:
split(2, k=3) returns (2→right=3, null)
  So (rl=null from split(3 right=null), right=null)
  Wait: split(3,3):
    3≤3 → split(3.right=null, 3) → (null, null)
    3.right = null (rl)
    return (3, null)  so left={3}, right={}

Back to split(2,3):
  2≤3 → (rl, right) = split(2.right=3, 3) = ({3}, {})
  2.right = {3} → node 2's right = 3 → subtree {1,2,3}
  return ({1,2,3}, {})

Back to split(4,3):
  4>3 → (left, lr) = split(4.left=2, 3) = ({1,2,3}, {})
  4.left = {} (lr = null)
  return ({1,2,3}, {4,5}) ✓
```

### Flattening / Serialization

```
FLATTEN BST TO LINKED LIST (in-place, inorder):

Method 1: Reverse inorder + rewiring
  Do reverse inorder (right → root → left)
  Keep a "prev" pointer, set prev.left = null, prev.right = current
  Result: doubly linked list using left/right pointers

Method 2: Morris-based (O(1) space)

SERIALIZE TREE TO STRING:
  Method: Preorder with null markers
  Tree:        1
              / \
             2   3
            / \
           4   5

  Preorder serialization: "1,2,4,#,#,5,#,#,3,#,#"
  (#= null)

  Deserialize:
  Read 1 → root=1
  Read 2 → 1.left=2
  Read 4 → 2.left=4
  Read # → 4.left=null
  Read # → 4.right=null
  Read 5 → 2.right=5
  Read # → 5.left=null
  Read # → 5.right=null
  Read 3 → 1.right=3
  Read # → 3.left=null
  Read # → 3.right=null ✓

Level-order serialization: "1,2,3,4,5,#,#"
  Used by LeetCode. Compact for wide trees, verbose for deep trees.
```

### Lowest Common Ancestor (LCA)

```
LCA of nodes p and q = the deepest node that has both p and q as descendants.

Tree:            1
                / \
               2   3
              / \   \
             4   5   6

LCA(4, 5) = 2   (2 is deepest node with 4 and 5 as descendants)
LCA(4, 6) = 1   (1 is deepest node with 4 and 6 as descendants)
LCA(3, 6) = 3   (a node is its own ancestor/descendant)

ALGORITHM 1: Recursive O(n) time, O(h) space
lca(root, p, q):
  if root == null: return null
  if root == p OR root == q: return root
  left  = lca(root.left, p, q)
  right = lca(root.right, p, q)
  if left && right: return root  // p and q in different subtrees → root is LCA
  return left if left else right // both in same subtree

ALGORITHM 2: Binary Lifting O(n log n) preprocess, O(log n) per query
  - Precompute ancestor[node][j] = 2^j-th ancestor of node
  - ancestor[node][0] = parent
  - ancestor[node][j] = ancestor[ancestor[node][j-1]][j-1]
  
  LCA query:
  1. Bring both nodes to same depth (use binary lifting)
  2. Binary lift both together until they meet

  ancestor table for depth 4 tree (nodes 1-7):
  ancestor[node][0]=parent  [1]=grandparent  [2]=great-grandparent
  ancestor[4][0]=2, ancestor[4][1]=1, ancestor[4][2]=null(overflow to root)

ALGORITHM 3: Euler Tour + RMQ (Range Minimum Query)
  Fastest for many LCA queries: O(n) preprocess, O(1) per query
  1. Do Euler tour of tree: record each node as you enter/leave
  2. LCA(u,v) = node with minimum depth between first occurrence of u and first occurrence of v
  3. Preprocess array with sparse table for O(1) RMQ
```

### Tree Diameter & Path Problems

```
DIAMETER = longest path between any two nodes (may not pass through root)

Key insight: the diameter is the maximum over all nodes N of:
  height(N.left) + height(N.right) + 2

Algorithm:
diameter(root):
  max_dia = 0
  height(node):
    if node == null: return -1
    lh = height(node.left)
    rh = height(node.right)
    max_dia = max(max_dia, lh + rh + 2)
    return 1 + max(lh, rh)
  height(root)
  return max_dia

Example:
         1
        / \
       2   3
      / \
     4   5
          \
           6

diameter candidates:
  Node 1: left_h=3 (1→2→5→6), right_h=0 → path=5
  Node 2: left_h=0 (4), right_h=1 (5→6) → path=4-2-5-6=3
  Node 5: left_h=-1, right_h=0 (6) → path=1
  Max = 5 (path: 4-2-5-6-... wait)
  
  Actually path through 1: 4→2→1→3 = length 3
  Path through 2: 4→2→5→6 = length 3
  Diameter = 3? Let me recount: 4-2-5-6 has edges: 3 edges = diameter 3.
  Actually diameter counts edges. 
```

### Mirroring & Symmetry

```
MIRROR a tree (swap left and right children recursively):

Original:      Mirror:
    1              1
   / \            / \
  2   3          3   2
 / \              \  /
4   5              5 4

mirror(node):
  if node == null: return
  swap(node.left, node.right)
  mirror(node.left)
  mirror(node.right)

SYMMETRIC CHECK:
Tree is symmetric if its mirror equals itself.

Symmetric:     Not Symmetric:
    1              1
   / \            / \
  2   2          2   2
 / \ / \        /     \
3  4 4  3      3       3

isMirror(left, right):
  if both null: return true
  if one null: return false
  return left.val == right.val
    AND isMirror(left.left, right.right)
    AND isMirror(left.right, right.left)
```

---

## 17. What You CAN Do vs What You CANNOT Do

### ✅ What You CAN Do

```
TRAVERSAL:
✓ Any traversal on any tree: O(n) time, O(h) space (recursive) or O(1) (Morris)
✓ Level-order traversal always O(n) time, O(w) space (w = max width)
✓ Convert any traversal to iterative using explicit stack

MODIFICATION:
✓ Insert/delete in BST: O(h) time [O(log n) if balanced]
✓ Insert in heap: O(log n) always (array-based)
✓ Delete max/min from heap: O(log n) always
✓ Build heap from array: O(n) (Floyd's algorithm)
✓ Rotate in AVL/RB: O(1) per rotation
✓ Rebalance AVL after insert: O(log n) rotations
✓ Rebalance RB after insert: O(log n) recolors, O(1) rotations
✓ Serialize/deserialize any binary tree: O(n)
✓ Convert between representations: O(n)

QUERIES:
✓ Find min/max in BST: O(h) → leftmost/rightmost node
✓ Find successor/predecessor in BST: O(h)
✓ Find k-th smallest in BST (with size augmentation): O(log n)
✓ Range query in BST [a,b]: O(log n + k) where k = results
✓ Range sum/min/max in segment tree: O(log n)
✓ Range update + query with lazy propagation: O(log n) each
✓ LCA queries: O(n) naive, O(log n) binary lifting, O(1) with RMQ
✓ Trie prefix search: O(L) per query, L = string length

MERGING/SPLITTING:
✓ Merge two treaps: O(log(m+n)) expected
✓ Split treap: O(log n) expected
✓ Merge two heaps (Fibonacci): O(1)
✓ Merge two sorted arrays from BST traversal: O(m+n)

STRUCTURE CHANGES:
✓ Convert BST to doubly linked list: O(n), in-place
✓ Flatten binary tree to linked list: O(n), in-place
✓ Mirror/invert a tree: O(n)
✓ Construct tree from traversal pairs: O(n) with hashmap
```

### ❌ What You CANNOT Do (and Why)

```
TRAVERSAL LIMITATIONS:
✗ Find exact path between two arbitrary nodes faster than O(n) without preprocessing
✗ Do inorder traversal faster than O(n) — you must visit all nodes
✗ Do true O(1)-space tree traversal without modifying tree (Morris requires temp mods)

BST LIMITATIONS:
✗ O(log n) insert/delete without balancing (worst case O(n) with unbalanced BST)
✗ Reconstruct unique BST from ONLY inorder traversal
   → Infinite BSTs can have same inorder sequence (add any node, delete it differently)
   → Need BOTH preorder+inorder, or postorder+inorder, or preorder+postorder (all unique)
✗ Find median in standard BST faster than O(n) without augmentation
   With augmentation (order statistics): O(log n)

AVL/RB TREE LIMITATIONS:
✗ O(1) merge of two arbitrary AVL trees (need O(log n) minimum)
✗ Guarantee worst-case O(1) delete (always O(log n))
✗ Guarantee tree height = ⌊log₂ n⌋ (AVL allows up to 1.44 log n)

HEAP LIMITATIONS:
✗ Find arbitrary element faster than O(n) — heap has no "search" path structure
✗ Delete arbitrary element without knowing its position faster than O(n) search + O(log n) delete
✗ O(1) decrease-key without special heap structure (Fibonacci heap gives O(1) amortized)
✗ Merge two binary heaps faster than O(n) (need binomial/Fibonacci heap)
✗ Get sorted order from heap without O(n log n) (must extract one by one)

SEGMENT TREE LIMITATIONS:
✗ Dynamic insertions (standard segment tree is static; use balanced BST instead)
✗ Range updates without lazy propagation in O(log n) (naive is O(n))
✗ 2D range queries in O(log n) — need O(log² n) or fractional cascading

TRIE LIMITATIONS:
✗ Space-efficient trie without compression (naive = O(ALPHABET * n * L))
✗ Fuzzy/approximate matching in O(L) (need Aho-Corasick or edit distance DP)

GENERAL IMPOSSIBILITIES:
✗ Compare two arbitrary trees for isomorphism faster than O(n)
   (Can do O(n) but not better)
✗ Find diameter of tree without visiting every node: must be O(n)
✗ Construct balanced BST from unsorted array faster than O(n log n)
   (Sorting lower bound is Ω(n log n) with comparisons)
✗ Find LCA of two nodes in O(1) without O(n log n) preprocessing
   (Preprocessing: O(n log n); then O(1) queries possible)
✗ Persistent tree (version history) without O(log n) overhead per operation
   Persistent segment tree: O(log n) per update (path copying)
✗ Perfectly balance an arbitrary BST without O(n) time
   (Must read all nodes = Ω(n))
✗ Guarantee O(log n) for all operations with a splay tree
   (Amortized O(log n) but individual ops can be O(n))
```

---

## 18. Common Mistakes — Exhaustive List

### Category 1: Pointer / Reference Mistakes

```
MISTAKE 1: Not returning the (possibly new) root after rotation/rebalancing
// WRONG:
void insert(Node* root, int val) {
    // root might change after rotation, but we return void!
    // caller still points to old root
}

// CORRECT:
Node* insert(Node* root, int val) {
    // ... insert ...
    // ... rotate if needed ...
    return root;  // root might be different now
}

MISTAKE 2: Off-by-one in parent pointer update during rotation
left_rotate(x):
  y = x.right
  x.right = y.left
  // FORGOT: if (y.left) y.left.parent = x  ← parent not updated!
  y.parent = x.parent
  ...

MISTAKE 3: Modifying tree structure during traversal
// WRONG: deleting nodes while iterating
for each node in inorder:
    if node.val < 0: delete node  // corrupts traversal state!

// CORRECT: collect nodes to delete first, then delete
```

### Category 2: BST Invariant Violations

```
MISTAKE 4: Checking only immediate parent-child, not full subtree
isBST(node):
    if node.left and node.left.val > node.val: return false
    if node.right and node.right.val < node.val: return false
    // WRONG! Only checks immediate children.
    
// Counter-example that passes wrong check but is invalid BST:
//       5
//      / \
//     1   4    ← 4 < 5, but 4 is right child. 
//        / \     Also 4 in right subtree of 5 but 4 < 5: INVALID!
//       3   6

// CORRECT: pass min/max bounds
isBST(node, min=-inf, max=+inf):
    if !node: return true
    if node.val <= min or node.val >= max: return false
    return isBST(node.left, min, node.val)
       and isBST(node.right, node.val, max)

MISTAKE 5: Incorrect successor finding during deletion
// Wrong: treating any right child as successor
successor = node.right  // WRONG if node.right has left subtree

// Correct: leftmost node in right subtree
successor = node.right
while successor.left: successor = successor.left

MISTAKE 6: Handling duplicates inconsistently
// BST doesn't define behavior for duplicates. 
// Decide: left, right, or ignore. Be consistent!
// Classic bug: inserting to left for <, right for >=
// but searching for = only goes right → can miss nodes on left
```

### Category 3: Height / Balance Factor Calculation

```
MISTAKE 7: Computing height recursively every time (O(n) per node, O(n²) total)
// WRONG in AVL:
height(node):
    if !node: return 0
    return 1 + max(height(node.left), height(node.right))  // called at every node!
    
// CORRECT: cache height in each node, update after each operation
node.height = 1 + max(node.left.height, node.right.height)

MISTAKE 8: Wrong base case for height
// Inconsistent conventions cause BF calculation errors
height(null) = -1  // convention 1: height of empty = -1
height(null) = 0   // convention 2: height of empty = 0

// With convention 1: height(leaf) = 0
// With convention 2: height(leaf) = 1
// PICK ONE AND STICK TO IT. Mixing = wrong BF.

MISTAKE 9: Forgetting to update heights after rotation
left_rotate(x):
    y = x.right
    x.right = y.left
    y.left = x
    // FORGOT: update x.height, then y.height (x first, since x is now lower)
    x.height = 1 + max(height(x.left), height(x.right))
    y.height = 1 + max(height(y.left), height(y.right))
    return y
```

### Category 4: Heap Mistakes

```
MISTAKE 10: 0-indexed vs 1-indexed confusion
// 1-indexed: parent = i/2, children = 2i, 2i+1
// 0-indexed: parent = (i-1)/2, children = 2i+1, 2i+2
// Mixing these: catastrophic wrong sifting

MISTAKE 11: Sifting wrong direction after arbitrary deletion
// After deleting arbitrary element from heap:
// The replacement (last element) might need to go UP or DOWN
// You must try BOTH sift-up and sift-down
heap_delete(i):
    heap[i] = heap[n]  // replace with last
    n--
    sift_up(i)         // try going up
    sift_down(i)       // try going down
    // Only one will actually move the element; both are safe to call

MISTAKE 12: Not handling empty heap
extract_min():
    // WRONG: accessing heap[1] when heap is empty
    // Always check n > 0 first!

MISTAKE 13: Building heap wrong way
// Naive O(n log n):
for each element: heap_insert(element)

// But Floyd's O(n) starts from MIDDLE, not end:
for i from n/2 DOWN TO 1: sift_down(i)
// NOT: for i from 1 TO n/2: sift_down(i)  ← wrong direction!
```

### Category 5: Traversal Mistakes

```
MISTAKE 14: Stack overflow on degenerate trees
// Recursive traversal stack depth = tree height
// Degenerate BST (sorted input): height = n
// n = 100,000 → stack overflow with default stack size (~1MB)
// Solution: iterative traversal or explicit stack allocation

MISTAKE 15: Modifying return value after recursion
// In postorder deletion:
// WRONG: deleting node BEFORE recursing
delete_tree(node):
    delete node  // frees memory!
    delete_tree(node.left)   // accessing freed memory → UB/crash
    
// CORRECT: postorder = delete children BEFORE current
delete_tree(node):
    if !node: return
    delete_tree(node.left)
    delete_tree(node.right)
    delete node  // NOW safe

MISTAKE 16: Incorrect level-order without tracking level boundaries
// If you need to process each level separately:
// WRONG: using single counter
// CORRECT: either (a) use queue size at start of each level
//               (b) use two queues (current level, next level)
//               (c) use NULL sentinel in queue

level_order_by_level(root):
    queue = [root]
    while queue:
        level_size = len(queue)  // capture size BEFORE processing
        for i in range(level_size):
            node = queue.dequeue()
            process(node)
            if node.left: queue.enqueue(node.left)
            if node.right: queue.enqueue(node.right)
        // One complete level processed above

MISTAKE 17: Morris traversal left in corrupted state
// If you break out of Morris traversal early (e.g., found target):
// MUST restore all threads before returning!
// Otherwise tree is structurally corrupted for future operations.
```

### Category 6: Segment Tree Mistakes

```
MISTAKE 18: Wrong array size for segment tree
// Segment tree needs 4*n space (not 2*n)
// n=5: tree might need indices up to 16 (next power of 2 * 2)
// Safe: allocate 4*n always
int tree[4 * MAXN];  // not 2*MAXN

MISTAKE 19: Lazy propagation pushdown before accessing children
// WRONG: accessing children before pushing down lazy
query(node, ...):
    // immediately accessing children without pushing lazy
    return query(2*node, ...) + query(2*node+1, ...)  // stale values!
    
// CORRECT: push down first
query(node, node_l, node_r, l, r):
    if complete overlap: return tree[node]
    pushdown(node)  // MUST come before accessing children
    mid = (node_l + node_r) / 2
    return query(2*node, ...) + query(2*node+1, ...)

MISTAKE 20: Wrong identity element for different operations
// Sum: identity = 0
// Min: identity = +infinity
// Max: identity = -infinity
// Product: identity = 1
// GCD: identity = 0 (gcd(0,x)=x)
// Bitwise AND: identity = all-1s (0xFFFFFFFF)
// Bitwise OR: identity = 0
// Using wrong identity corrupts out-of-range returns!
```

### Category 7: Recursion & Logic Mistakes

```
MISTAKE 21: Wrong termination condition
// WRONG: checking children from parent (double-processes nodes)
if node.left == null and node.right == null:
    return  // only handles leaf, misses nodes with one child

// More common wrong pattern:
find_path(node, target):
    if node == null: return []  // forgot to check if node == target!
    if node.left == target or node.right == target: ...  // only checks immediate

// CORRECT: check current node first
find_path(node, target):
    if node == null: return null
    if node == target: return [node]
    ...

MISTAKE 22: Off-by-one in diameter calculation
// Diameter = number of EDGES on longest path
// vs.       number of NODES on longest path
// These differ by 1. Be clear which one you need.
// height(leaf) = 0 if counting edges from leaf
// Diameter through node = height(left) + height(right) + 2 (for edge convention)
//                       = height(left) + height(right)     if height(null)=0

MISTAKE 23: Forgetting null checks in doubly-linked pointer structures
// When converting BST to doubly linked list using left/right pointers:
prev.right = curr    // prev's right = curr ✓
curr.left = prev     // curr's left = prev ✓
// BUT: did you null out the original children pointers?
// Forgetting creates cycles!

MISTAKE 24: Misidentifying LR vs LL case
// Node is left-heavy (BF=+2)
// Check child's BF:
// child.BF >= 0 → LL case → single right rotation
// child.BF < 0  → LR case → left rotate child, then right rotate node
// Confusing these: broken AVL tree

MISTAKE 25: Integer overflow in array indexing for segment trees
// Midpoint calculation overflow:
mid = (l + r) / 2   // WRONG if l+r overflows int!
mid = l + (r - l) / 2  // CORRECT
```

---

## 19. Complexity Cheat Sheet

```
Operation          BST(avg) BST(worst) AVL      RB       Heap     Seg Tree  BIT
───────────────────────────────────────────────────────────────────────────────
Search             O(log n) O(n)       O(log n) O(log n) O(n)     O(log n)  O(log n)
Insert             O(log n) O(n)       O(log n) O(log n) O(log n) O(log n)  O(log n)
Delete             O(log n) O(n)       O(log n) O(log n) O(log n) O(log n)  O(log n)
Min/Max            O(log n) O(n)       O(log n) O(log n) O(1)     O(log n)  O(log n)
Predecessor        O(log n) O(n)       O(log n) O(log n) O(n)     -         -
Range query        O(log n) O(n)       O(log n) O(log n) O(n)     O(log n)  O(log n)
Range update       O(n)     O(n)       O(n)     O(n)     -        O(log n)* O(log n)**
Build from array   O(n log n)          O(n log n)        O(n)     O(n)      O(n)
Space              O(n)     O(n)       O(n)     O(n)     O(n)     O(n)      O(n)
Rotations/rebal    -        -          O(log n) O(1)***  -        -         -

* With lazy propagation
** BIT range update with difference array technique
*** O(1) rotations but O(log n) recolors for RB insert

Traversal complexity (all trees, n nodes):
  Any DFS traversal: O(n) time, O(h) space (recursive) / O(h) space (iterative)
  Morris traversal: O(n) time, O(1) space
  BFS: O(n) time, O(w) space (w = max width, up to n/2)

Trie:
  Insert/Search: O(L) where L = string length
  Prefix search: O(L + results)
  Space: O(ALPHABET * L * N) worst, O(total chars) with compression
```

---

## 20. Implementations: C, Go, Rust

### C Implementation

```c
// ============================================================
// COMPLETE TREE IMPLEMENTATION IN C
// Covers: BST, AVL, Heap, Segment Tree, Trie
// ============================================================

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>

// ─────────────────────────────────────────────
// SECTION 1: BST
// ─────────────────────────────────────────────

typedef struct BSTNode {
    int val;
    struct BSTNode *left, *right;
} BSTNode;

BSTNode* bst_new(int val) {
    BSTNode* n = malloc(sizeof(BSTNode));
    n->val = val;
    n->left = n->right = NULL;
    return n;
}

// Returns new root (may change after balancing in AVL/RB)
BSTNode* bst_insert(BSTNode* root, int val) {
    if (!root) return bst_new(val);
    if (val < root->val)
        root->left = bst_insert(root->left, val);
    else if (val > root->val)
        root->right = bst_insert(root->right, val);
    // val == root->val: ignore duplicate
    return root;
}

BSTNode* bst_find_min(BSTNode* root) {
    while (root && root->left)
        root = root->left;
    return root;
}

BSTNode* bst_delete(BSTNode* root, int val) {
    if (!root) return NULL;
    if (val < root->val) {
        root->left = bst_delete(root->left, val);
    } else if (val > root->val) {
        root->right = bst_delete(root->right, val);
    } else {
        // Found the node to delete
        if (!root->left) {
            BSTNode* right = root->right;
            free(root);
            return right;
        }
        if (!root->right) {
            BSTNode* left = root->left;
            free(root);
            return left;
        }
        // Two children: find inorder successor (min of right subtree)
        BSTNode* succ = bst_find_min(root->right);
        root->val = succ->val;               // copy successor value
        root->right = bst_delete(root->right, succ->val); // delete successor
    }
    return root;
}

BSTNode* bst_search(BSTNode* root, int val) {
    if (!root || root->val == val) return root;
    if (val < root->val) return bst_search(root->left, val);
    return bst_search(root->right, val);
}

// Inorder traversal (sorted output for BST)
void bst_inorder(BSTNode* root) {
    if (!root) return;
    bst_inorder(root->left);
    printf("%d ", root->val);
    bst_inorder(root->right);
}

// BST validation with bounds
int bst_validate(BSTNode* node, long long min, long long max) {
    if (!node) return 1;
    if (node->val <= min || node->val >= max) return 0;
    return bst_validate(node->left, min, node->val)
        && bst_validate(node->right, node->val, max);
}

// ─────────────────────────────────────────────
// SECTION 2: AVL Tree
// ─────────────────────────────────────────────

typedef struct AVLNode {
    int val, height;
    struct AVLNode *left, *right;
} AVLNode;

int avl_height(AVLNode* n) {
    return n ? n->height : -1;  // height of null = -1
}

void avl_update_height(AVLNode* n) {
    if (!n) return;
    int lh = avl_height(n->left);
    int rh = avl_height(n->right);
    n->height = 1 + (lh > rh ? lh : rh);
}

int avl_bf(AVLNode* n) {
    if (!n) return 0;
    return avl_height(n->left) - avl_height(n->right);
}

// Right rotation (fixes LL imbalance)
AVLNode* avl_right_rotate(AVLNode* y) {
    AVLNode* x = y->left;
    AVLNode* T2 = x->right;

    x->right = y;
    y->left = T2;

    avl_update_height(y);  // y is now lower; update first
    avl_update_height(x);

    return x;  // x is new root of this subtree
}

// Left rotation (fixes RR imbalance)
AVLNode* avl_left_rotate(AVLNode* x) {
    AVLNode* y = x->right;
    AVLNode* T2 = y->left;

    y->left = x;
    x->right = T2;

    avl_update_height(x);
    avl_update_height(y);

    return y;
}

AVLNode* avl_balance(AVLNode* node) {
    avl_update_height(node);
    int bf = avl_bf(node);

    // LL case
    if (bf > 1 && avl_bf(node->left) >= 0)
        return avl_right_rotate(node);

    // LR case
    if (bf > 1 && avl_bf(node->left) < 0) {
        node->left = avl_left_rotate(node->left);
        return avl_right_rotate(node);
    }

    // RR case
    if (bf < -1 && avl_bf(node->right) <= 0)
        return avl_left_rotate(node);

    // RL case
    if (bf < -1 && avl_bf(node->right) > 0) {
        node->right = avl_right_rotate(node->right);
        return avl_left_rotate(node);
    }

    return node;  // already balanced
}

AVLNode* avl_new(int val) {
    AVLNode* n = malloc(sizeof(AVLNode));
    n->val = val;
    n->height = 0;
    n->left = n->right = NULL;
    return n;
}

AVLNode* avl_insert(AVLNode* root, int val) {
    if (!root) return avl_new(val);
    if (val < root->val)
        root->left = avl_insert(root->left, val);
    else if (val > root->val)
        root->right = avl_insert(root->right, val);
    else
        return root;  // duplicate

    return avl_balance(root);
}

AVLNode* avl_find_min(AVLNode* root) {
    while (root->left) root = root->left;
    return root;
}

AVLNode* avl_delete(AVLNode* root, int val) {
    if (!root) return NULL;
    if (val < root->val)
        root->left = avl_delete(root->left, val);
    else if (val > root->val)
        root->right = avl_delete(root->right, val);
    else {
        if (!root->left || !root->right) {
            AVLNode* child = root->left ? root->left : root->right;
            free(root);
            return child;
        }
        AVLNode* succ = avl_find_min(root->right);
        root->val = succ->val;
        root->right = avl_delete(root->right, succ->val);
    }
    return avl_balance(root);
}

// ─────────────────────────────────────────────
// SECTION 3: Binary Max Heap (array-based)
// ─────────────────────────────────────────────

#define HEAP_MAX 10000

typedef struct MaxHeap {
    int data[HEAP_MAX];
    int size;
} MaxHeap;

void heap_swap(MaxHeap* h, int i, int j) {
    int tmp = h->data[i];
    h->data[i] = h->data[j];
    h->data[j] = tmp;
}

void heap_sift_up(MaxHeap* h, int i) {
    while (i > 1 && h->data[i/2] < h->data[i]) {
        heap_swap(h, i/2, i);
        i /= 2;
    }
}

void heap_sift_down(MaxHeap* h, int i) {
    while (1) {
        int largest = i;
        int l = 2*i, r = 2*i+1;
        if (l <= h->size && h->data[l] > h->data[largest]) largest = l;
        if (r <= h->size && h->data[r] > h->data[largest]) largest = r;
        if (largest == i) break;
        heap_swap(h, i, largest);
        i = largest;
    }
}

void heap_insert(MaxHeap* h, int val) {
    h->data[++h->size] = val;  // 1-indexed
    heap_sift_up(h, h->size);
}

int heap_extract_max(MaxHeap* h) {
    if (h->size == 0) return INT_MIN;  // error: empty
    int max = h->data[1];
    h->data[1] = h->data[h->size--];
    heap_sift_down(h, 1);
    return max;
}

// Build heap from array: O(n) using Floyd's algorithm
void heap_build(MaxHeap* h, int* arr, int n) {
    h->size = n;
    for (int i = 0; i < n; i++) h->data[i+1] = arr[i];
    for (int i = n/2; i >= 1; i--) heap_sift_down(h, i);
}

// ─────────────────────────────────────────────
// SECTION 4: Segment Tree with Lazy Propagation
// ─────────────────────────────────────────────

#define MAXN 100005

long long seg[4*MAXN], lazy[4*MAXN];

void seg_build(int* arr, int node, int l, int r) {
    lazy[node] = 0;
    if (l == r) { seg[node] = arr[l]; return; }
    int mid = l + (r-l)/2;
    seg_build(arr, 2*node, l, mid);
    seg_build(arr, 2*node+1, mid+1, r);
    seg[node] = seg[2*node] + seg[2*node+1];
}

void seg_pushdown(int node, int l, int r) {
    if (!lazy[node]) return;
    int mid = l + (r-l)/2;
    seg[2*node]   += lazy[node] * (mid - l + 1);
    seg[2*node+1] += lazy[node] * (r - mid);
    lazy[2*node]  += lazy[node];
    lazy[2*node+1]+= lazy[node];
    lazy[node] = 0;
}

// Range add: add val to all elements in [ql, qr]
void seg_range_add(int node, int l, int r, int ql, int qr, long long val) {
    if (qr < l || r < ql) return;
    if (ql <= l && r <= qr) {
        seg[node] += val * (r - l + 1);
        lazy[node] += val;
        return;
    }
    seg_pushdown(node, l, r);
    int mid = l + (r-l)/2;
    seg_range_add(2*node, l, mid, ql, qr, val);
    seg_range_add(2*node+1, mid+1, r, ql, qr, val);
    seg[node] = seg[2*node] + seg[2*node+1];
}

// Range sum query: sum of elements in [ql, qr]
long long seg_query(int node, int l, int r, int ql, int qr) {
    if (qr < l || r < ql) return 0;
    if (ql <= l && r <= qr) return seg[node];
    seg_pushdown(node, l, r);
    int mid = l + (r-l)/2;
    return seg_query(2*node, l, mid, ql, qr)
         + seg_query(2*node+1, mid+1, r, ql, qr);
}

// ─────────────────────────────────────────────
// SECTION 5: Fenwick Tree (BIT)
// ─────────────────────────────────────────────

long long bit[MAXN];
int bit_n;

void bit_update(int i, long long delta) {
    for (; i <= bit_n; i += i & (-i))
        bit[i] += delta;
}

long long bit_query(int i) {  // prefix sum [1..i]
    long long s = 0;
    for (; i > 0; i -= i & (-i))
        s += bit[i];
    return s;
}

long long bit_range_query(int l, int r) {
    return bit_query(r) - bit_query(l-1);
}

// ─────────────────────────────────────────────
// SECTION 6: Trie
// ─────────────────────────────────────────────

#define ALPHA 26

typedef struct TrieNode {
    struct TrieNode* children[ALPHA];
    int is_end;
    int count;  // number of strings passing through this node
} TrieNode;

TrieNode* trie_new() {
    TrieNode* n = calloc(1, sizeof(TrieNode));
    return n;
}

void trie_insert(TrieNode* root, const char* word) {
    TrieNode* cur = root;
    for (int i = 0; word[i]; i++) {
        int idx = word[i] - 'a';
        if (!cur->children[idx])
            cur->children[idx] = trie_new();
        cur = cur->children[idx];
        cur->count++;
    }
    cur->is_end = 1;
}

int trie_search(TrieNode* root, const char* word) {
    TrieNode* cur = root;
    for (int i = 0; word[i]; i++) {
        int idx = word[i] - 'a';
        if (!cur->children[idx]) return 0;
        cur = cur->children[idx];
    }
    return cur->is_end;
}

int trie_starts_with(TrieNode* root, const char* prefix) {
    TrieNode* cur = root;
    for (int i = 0; prefix[i]; i++) {
        int idx = prefix[i] - 'a';
        if (!cur->children[idx]) return 0;
        cur = cur->children[idx];
    }
    return 1;
}

// ─────────────────────────────────────────────
// SECTION 7: LCA with Binary Lifting
// ─────────────────────────────────────────────

#define MAXLOG 20

int depth[MAXN], up[MAXN][MAXLOG];
// adjacency list
int head[MAXN], nxt[2*MAXN], to[2*MAXN], edge_cnt;

void add_edge(int u, int v) {
    to[++edge_cnt] = v; nxt[edge_cnt] = head[u]; head[u] = edge_cnt;
    to[++edge_cnt] = u; nxt[edge_cnt] = head[v]; head[v] = edge_cnt;
}

void dfs_lca(int u, int par, int d) {
    depth[u] = d;
    up[u][0] = par;
    for (int j = 1; j < MAXLOG; j++)
        up[u][j] = up[up[u][j-1]][j-1];
    for (int e = head[u]; e; e = nxt[e]) {
        if (to[e] != par)
            dfs_lca(to[e], u, d+1);
    }
}

int lca(int u, int v) {
    if (depth[u] < depth[v]) { int t = u; u = v; v = t; }
    int diff = depth[u] - depth[v];
    for (int j = 0; j < MAXLOG; j++)
        if ((diff >> j) & 1) u = up[u][j];
    if (u == v) return u;
    for (int j = MAXLOG-1; j >= 0; j--)
        if (up[u][j] != up[v][j]) { u = up[u][j]; v = up[v][j]; }
    return up[u][0];
}

// ─────────────────────────────────────────────
// SECTION 8: Iterative Inorder Traversal
// ─────────────────────────────────────────────

void iterative_inorder(BSTNode* root) {
    BSTNode* stack[10000];
    int top = -1;
    BSTNode* curr = root;
    while (curr || top >= 0) {
        while (curr) {
            stack[++top] = curr;
            curr = curr->left;
        }
        curr = stack[top--];
        printf("%d ", curr->val);
        curr = curr->right;
    }
}

// ─────────────────────────────────────────────
// SECTION 9: Tree Diameter
// ─────────────────────────────────────────────

int diameter;

int tree_height_for_diameter(BSTNode* node) {
    if (!node) return -1;
    int lh = tree_height_for_diameter(node->left);
    int rh = tree_height_for_diameter(node->right);
    int d = lh + rh + 2;  // edges in path through this node
    if (d > diameter) diameter = d;
    return 1 + (lh > rh ? lh : rh);
}

int get_diameter(BSTNode* root) {
    diameter = 0;
    tree_height_for_diameter(root);
    return diameter;
}

// ─────────────────────────────────────────────
// DEMO MAIN
// ─────────────────────────────────────────────

int main() {
    // BST demo
    printf("=== BST ===\n");
    BSTNode* bst = NULL;
    int vals[] = {5, 3, 7, 1, 4, 6, 8};
    for (int i = 0; i < 7; i++) bst = bst_insert(bst, vals[i]);
    printf("Inorder: "); bst_inorder(bst); printf("\n");
    printf("Valid BST: %s\n", bst_validate(bst, LLONG_MIN, LLONG_MAX) ? "YES" : "NO");
    bst = bst_delete(bst, 5);
    printf("After deleting 5: "); bst_inorder(bst); printf("\n");

    // AVL demo
    printf("\n=== AVL ===\n");
    AVLNode* avl = NULL;
    for (int i = 1; i <= 7; i++) avl = avl_insert(avl, i);
    // Inserting 1,2,3,4,5,6,7 in order into BST = degenerate chain
    // AVL auto-balances it
    printf("AVL root after inserting 1-7 in order: %d (balanced!)\n", avl->val);
    printf("AVL height: %d (should be ~2)\n", avl->height);

    // Heap demo
    printf("\n=== MAX HEAP ===\n");
    MaxHeap h = {.size = 0};
    int arr[] = {3, 1, 6, 5, 2, 4};
    heap_build(&h, arr, 6);
    printf("Extract in order: ");
    while (h.size > 0) printf("%d ", heap_extract_max(&h));
    printf("\n");

    // BIT demo
    printf("\n=== FENWICK TREE ===\n");
    bit_n = 8;
    int bit_arr[] = {0, 3, 2, 1, 4, 5, 2, 7, 3};  // 1-indexed
    for (int i = 1; i <= 8; i++) bit_update(i, bit_arr[i]);
    printf("Sum [1..7] = %lld (expected 24)\n", bit_query(7));
    printf("Sum [3..6] = %lld (expected 12)\n", bit_range_query(3, 6));

    // Trie demo
    printf("\n=== TRIE ===\n");
    TrieNode* trie = trie_new();
    trie_insert(trie, "cat");
    trie_insert(trie, "car");
    trie_insert(trie, "card");
    printf("Search 'car': %s\n", trie_search(trie, "car") ? "FOUND" : "NOT FOUND");
    printf("Search 'ca': %s\n", trie_search(trie, "ca") ? "FOUND" : "NOT FOUND");
    printf("Prefix 'ca': %s\n", trie_starts_with(trie, "ca") ? "EXISTS" : "NOT EXISTS");

    return 0;
}
```

---

### Go Implementation

```go
// ============================================================
// COMPLETE TREE IMPLEMENTATION IN GO
// Covers: Generic BST, AVL, Heap, Segment Tree, Trie
// ============================================================

package main

import (
	"fmt"
	"math"
)

// ─────────────────────────────────────────────
// SECTION 1: BST (Generic with comparable constraint)
// ─────────────────────────────────────────────

type BSTNode[T interface{ ~int | ~float64 | ~string }] struct {
	Val         T
	Left, Right *BSTNode[T]
}

func bstInsert[T interface{ ~int | ~float64 | ~string }](
	root *BSTNode[T], val T,
) *BSTNode[T] {
	if root == nil {
		return &BSTNode[T]{Val: val}
	}
	if val < root.Val {
		root.Left = bstInsert(root.Left, val)
	} else if val > root.Val {
		root.Right = bstInsert(root.Right, val)
	}
	return root
}

func bstFindMin[T interface{ ~int | ~float64 | ~string }](
	root *BSTNode[T],
) *BSTNode[T] {
	for root.Left != nil {
		root = root.Left
	}
	return root
}

func bstDelete[T interface{ ~int | ~float64 | ~string }](
	root *BSTNode[T], val T,
) *BSTNode[T] {
	if root == nil {
		return nil
	}
	switch {
	case val < root.Val:
		root.Left = bstDelete(root.Left, val)
	case val > root.Val:
		root.Right = bstDelete(root.Right, val)
	default: // found
		if root.Left == nil {
			return root.Right
		}
		if root.Right == nil {
			return root.Left
		}
		succ := bstFindMin(root.Right)
		root.Val = succ.Val
		root.Right = bstDelete(root.Right, succ.Val)
	}
	return root
}

func bstInorder[T interface{ ~int | ~float64 | ~string }](
	root *BSTNode[T], result *[]T,
) {
	if root == nil {
		return
	}
	bstInorder(root.Left, result)
	*result = append(*result, root.Val)
	bstInorder(root.Right, result)
}

// Iterative inorder using explicit stack
func bstIterativeInorder[T interface{ ~int | ~float64 | ~string }](
	root *BSTNode[T],
) []T {
	var result []T
	var stack []*BSTNode[T]
	curr := root
	for curr != nil || len(stack) > 0 {
		for curr != nil {
			stack = append(stack, curr)
			curr = curr.Left
		}
		curr = stack[len(stack)-1]
		stack = stack[:len(stack)-1]
		result = append(result, curr.Val)
		curr = curr.Right
	}
	return result
}

// BST validation
func bstValidate[T interface{ ~int | ~float64 | ~string }](
	node *BSTNode[T], hasMin, hasMax bool, min, max T,
) bool {
	if node == nil {
		return true
	}
	if hasMin && node.Val <= min {
		return false
	}
	if hasMax && node.Val >= max {
		return false
	}
	return bstValidate(node.Left, hasMin, true, min, node.Val) &&
		bstValidate(node.Right, true, hasMax, node.Val, max)
}

// ─────────────────────────────────────────────
// SECTION 2: AVL Tree
// ─────────────────────────────────────────────

type AVLNode struct {
	Val         int
	Height      int
	Left, Right *AVLNode
}

func avlHeight(n *AVLNode) int {
	if n == nil {
		return -1
	}
	return n.Height
}

func avlUpdateHeight(n *AVLNode) {
	if n == nil {
		return
	}
	lh, rh := avlHeight(n.Left), avlHeight(n.Right)
	if lh > rh {
		n.Height = 1 + lh
	} else {
		n.Height = 1 + rh
	}
}

func avlBF(n *AVLNode) int {
	if n == nil {
		return 0
	}
	return avlHeight(n.Left) - avlHeight(n.Right)
}

func avlRotateRight(y *AVLNode) *AVLNode {
	x := y.Left
	t2 := x.Right
	x.Right = y
	y.Left = t2
	avlUpdateHeight(y)
	avlUpdateHeight(x)
	return x
}

func avlRotateLeft(x *AVLNode) *AVLNode {
	y := x.Right
	t2 := y.Left
	y.Left = x
	x.Right = t2
	avlUpdateHeight(x)
	avlUpdateHeight(y)
	return y
}

func avlBalance(node *AVLNode) *AVLNode {
	avlUpdateHeight(node)
	bf := avlBF(node)

	if bf > 1 { // left heavy
		if avlBF(node.Left) < 0 { // LR case
			node.Left = avlRotateLeft(node.Left)
		}
		return avlRotateRight(node) // LL or after LR fix
	}
	if bf < -1 { // right heavy
		if avlBF(node.Right) > 0 { // RL case
			node.Right = avlRotateRight(node.Right)
		}
		return avlRotateLeft(node) // RR or after RL fix
	}
	return node
}

func avlInsert(root *AVLNode, val int) *AVLNode {
	if root == nil {
		return &AVLNode{Val: val, Height: 0}
	}
	if val < root.Val {
		root.Left = avlInsert(root.Left, val)
	} else if val > root.Val {
		root.Right = avlInsert(root.Right, val)
	} else {
		return root // duplicate
	}
	return avlBalance(root)
}

func avlFindMin(root *AVLNode) *AVLNode {
	for root.Left != nil {
		root = root.Left
	}
	return root
}

func avlDelete(root *AVLNode, val int) *AVLNode {
	if root == nil {
		return nil
	}
	if val < root.Val {
		root.Left = avlDelete(root.Left, val)
	} else if val > root.Val {
		root.Right = avlDelete(root.Right, val)
	} else {
		if root.Left == nil {
			return root.Right
		}
		if root.Right == nil {
			return root.Left
		}
		succ := avlFindMin(root.Right)
		root.Val = succ.Val
		root.Right = avlDelete(root.Right, succ.Val)
	}
	return avlBalance(root)
}

// ─────────────────────────────────────────────
// SECTION 3: Binary Max Heap
// ─────────────────────────────────────────────

type MaxHeap struct {
	data []int // 1-indexed: data[0] unused
}

func NewMaxHeap() *MaxHeap {
	return &MaxHeap{data: []int{0}} // sentinel at index 0
}

func (h *MaxHeap) Len() int { return len(h.data) - 1 }

func (h *MaxHeap) swap(i, j int) {
	h.data[i], h.data[j] = h.data[j], h.data[i]
}

func (h *MaxHeap) siftUp(i int) {
	for i > 1 && h.data[i/2] < h.data[i] {
		h.swap(i/2, i)
		i /= 2
	}
}

func (h *MaxHeap) siftDown(i int) {
	n := h.Len()
	for {
		largest := i
		l, r := 2*i, 2*i+1
		if l <= n && h.data[l] > h.data[largest] {
			largest = l
		}
		if r <= n && h.data[r] > h.data[largest] {
			largest = r
		}
		if largest == i {
			break
		}
		h.swap(i, largest)
		i = largest
	}
}

func (h *MaxHeap) Push(val int) {
	h.data = append(h.data, val)
	h.siftUp(h.Len())
}

func (h *MaxHeap) Pop() (int, bool) {
	if h.Len() == 0 {
		return 0, false
	}
	max := h.data[1]
	n := h.Len()
	h.data[1] = h.data[n]
	h.data = h.data[:n]
	if h.Len() > 0 {
		h.siftDown(1)
	}
	return max, true
}

// Build heap from slice in O(n) using Floyd's algorithm
func BuildMaxHeap(arr []int) *MaxHeap {
	h := &MaxHeap{data: append([]int{0}, arr...)} // prepend sentinel
	for i := h.Len() / 2; i >= 1; i-- {
		h.siftDown(i)
	}
	return h
}

// ─────────────────────────────────────────────
// SECTION 4: Segment Tree (Range Sum + Lazy Range Add)
// ─────────────────────────────────────────────

type SegTree struct {
	n    int
	tree []int64
	lazy []int64
}

func NewSegTree(arr []int) *SegTree {
	n := len(arr)
	st := &SegTree{
		n:    n,
		tree: make([]int64, 4*n),
		lazy: make([]int64, 4*n),
	}
	st.build(arr, 1, 0, n-1)
	return st
}

func (st *SegTree) build(arr []int, node, l, r int) {
	if l == r {
		st.tree[node] = int64(arr[l])
		return
	}
	mid := l + (r-l)/2
	st.build(arr, 2*node, l, mid)
	st.build(arr, 2*node+1, mid+1, r)
	st.tree[node] = st.tree[2*node] + st.tree[2*node+1]
}

func (st *SegTree) pushDown(node, l, r int) {
	if st.lazy[node] == 0 {
		return
	}
	mid := l + (r-l)/2
	// Apply lazy to children
	st.tree[2*node] += st.lazy[node] * int64(mid-l+1)
	st.lazy[2*node] += st.lazy[node]
	st.tree[2*node+1] += st.lazy[node] * int64(r-mid)
	st.lazy[2*node+1] += st.lazy[node]
	st.lazy[node] = 0
}

func (st *SegTree) update(node, l, r, ql, qr int, val int64) {
	if qr < l || r < ql {
		return
	}
	if ql <= l && r <= qr {
		st.tree[node] += val * int64(r-l+1)
		st.lazy[node] += val
		return
	}
	st.pushDown(node, l, r)
	mid := l + (r-l)/2
	st.update(2*node, l, mid, ql, qr, val)
	st.update(2*node+1, mid+1, r, ql, qr, val)
	st.tree[node] = st.tree[2*node] + st.tree[2*node+1]
}

func (st *SegTree) query(node, l, r, ql, qr int) int64 {
	if qr < l || r < ql {
		return 0
	}
	if ql <= l && r <= qr {
		return st.tree[node]
	}
	st.pushDown(node, l, r)
	mid := l + (r-l)/2
	return st.query(2*node, l, mid, ql, qr) +
		st.query(2*node+1, mid+1, r, ql, qr)
}

func (st *SegTree) Update(l, r int, val int64) {
	st.update(1, 0, st.n-1, l, r, val)
}

func (st *SegTree) Query(l, r int) int64 {
	return st.query(1, 0, st.n-1, l, r)
}

// ─────────────────────────────────────────────
// SECTION 5: Fenwick Tree (BIT)
// ─────────────────────────────────────────────

type BIT struct {
	data []int64
	n    int
}

func NewBIT(n int) *BIT {
	return &BIT{data: make([]int64, n+1), n: n}
}

func (b *BIT) Update(i int, delta int64) {
	for ; i <= b.n; i += i & (-i) {
		b.data[i] += delta
	}
}

func (b *BIT) Query(i int) int64 { // prefix sum [1..i]
	var s int64
	for ; i > 0; i -= i & (-i) {
		s += b.data[i]
	}
	return s
}

func (b *BIT) RangeQuery(l, r int) int64 {
	return b.Query(r) - b.Query(l-1)
}

// ─────────────────────────────────────────────
// SECTION 6: Trie
// ─────────────────────────────────────────────

type TrieNode struct {
	children [26]*TrieNode
	isEnd    bool
	count    int
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
		cur.count++
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

func (t *Trie) CountWithPrefix(prefix string) int {
	cur := t.root
	for _, ch := range prefix {
		idx := ch - 'a'
		if cur.children[idx] == nil {
			return 0
		}
		cur = cur.children[idx]
	}
	return cur.count
}

// ─────────────────────────────────────────────
// SECTION 7: LCA (Binary Lifting)
// ─────────────────────────────────────────────

const MAXLOG = 20

type LCATree struct {
	n     int
	depth []int
	up    [][]int
	adj   [][]int
}

func NewLCATree(n int) *LCATree {
	up := make([][]int, n+1)
	for i := range up {
		up[i] = make([]int, MAXLOG)
	}
	return &LCATree{
		n:     n,
		depth: make([]int, n+1),
		up:    up,
		adj:   make([][]int, n+1),
	}
}

func (lt *LCATree) AddEdge(u, v int) {
	lt.adj[u] = append(lt.adj[u], v)
	lt.adj[v] = append(lt.adj[v], u)
}

func (lt *LCATree) DFS(u, parent, d int) {
	lt.depth[u] = d
	lt.up[u][0] = parent
	for j := 1; j < MAXLOG; j++ {
		lt.up[u][j] = lt.up[lt.up[u][j-1]][j-1]
	}
	for _, v := range lt.adj[u] {
		if v != parent {
			lt.DFS(v, u, d+1)
		}
	}
}

func (lt *LCATree) LCA(u, v int) int {
	if lt.depth[u] < lt.depth[v] {
		u, v = v, u
	}
	diff := lt.depth[u] - lt.depth[v]
	for j := 0; j < MAXLOG; j++ {
		if (diff>>j)&1 == 1 {
			u = lt.up[u][j]
		}
	}
	if u == v {
		return u
	}
	for j := MAXLOG - 1; j >= 0; j-- {
		if lt.up[u][j] != lt.up[v][j] {
			u = lt.up[u][j]
			v = lt.up[v][j]
		}
	}
	return lt.up[u][0]
}

// ─────────────────────────────────────────────
// SECTION 8: Tree Diameter (any general tree)
// ─────────────────────────────────────────────

func treeDiameter(adj [][]int, n int) int {
	// Two BFS approach: find farthest from any node, then farthest from that
	bfs := func(start int) (farthest, dist int) {
		visited := make([]bool, n)
		queue := []int{start}
		d := make([]int, n)
		visited[start] = true
		farthest, dist = start, 0
		for len(queue) > 0 {
			u := queue[0]
			queue = queue[1:]
			if d[u] > dist {
				dist = d[u]
				farthest = u
			}
			for _, v := range adj[u] {
				if !visited[v] {
					visited[v] = true
					d[v] = d[u] + 1
					queue = append(queue, v)
				}
			}
		}
		return
	}
	// BFS from node 0 to find one endpoint of diameter
	far1, _ := bfs(0)
	// BFS from far1 to find other endpoint and diameter length
	_, diameter := bfs(far1)
	return diameter
}

// ─────────────────────────────────────────────
// SECTION 9: Serialize / Deserialize Binary Tree
// ─────────────────────────────────────────────

type TreeNode struct {
	Val   int
	Left  *TreeNode
	Right *TreeNode
}

func serialize(root *TreeNode) string {
	if root == nil {
		return "#"
	}
	return fmt.Sprintf("%d,%s,%s",
		root.Val,
		serialize(root.Left),
		serialize(root.Right))
}

func deserialize(data string) *TreeNode {
	idx := 0
	var build func() *TreeNode
	build = func() *TreeNode {
		start := idx
		for idx < len(data) && data[idx] != ',' {
			idx++
		}
		token := data[start:idx]
		idx++ // skip comma
		if token == "#" {
			return nil
		}
		var val int
		fmt.Sscanf(token, "%d", &val)
		node := &TreeNode{Val: val}
		node.Left = build()
		node.Right = build()
		return node
	}
	return build()
}

// ─────────────────────────────────────────────
// SECTION 10: Mirror Tree
// ─────────────────────────────────────────────

func mirrorTree(root *TreeNode) *TreeNode {
	if root == nil {
		return nil
	}
	root.Left, root.Right = mirrorTree(root.Right), mirrorTree(root.Left)
	return root
}

func isSymmetric(root *TreeNode) bool {
	var isMirror func(l, r *TreeNode) bool
	isMirror = func(l, r *TreeNode) bool {
		if l == nil && r == nil {
			return true
		}
		if l == nil || r == nil {
			return false
		}
		return l.Val == r.Val &&
			isMirror(l.Left, r.Right) &&
			isMirror(l.Right, r.Left)
	}
	if root == nil {
		return true
	}
	return isMirror(root.Left, root.Right)
}

// ─────────────────────────────────────────────
// DEMO
// ─────────────────────────────────────────────

func main() {
	// BST demo
	fmt.Println("=== BST ===")
	var bst *BSTNode[int]
	for _, v := range []int{5, 3, 7, 1, 4, 6, 8} {
		bst = bstInsert(bst, v)
	}
	var inorder []int
	bstInorder(bst, &inorder)
	fmt.Println("Inorder:", inorder)
	fmt.Println("Iterative inorder:", bstIterativeInorder(bst))

	// AVL demo
	fmt.Println("\n=== AVL ===")
	var avl *AVLNode
	for i := 1; i <= 7; i++ {
		avl = avlInsert(avl, i)
	}
	fmt.Printf("AVL root: %d, height: %d (balanced despite sorted insert)\n",
		avl.Val, avl.Height)

	// Heap demo
	fmt.Println("\n=== MAX HEAP ===")
	h := BuildMaxHeap([]int{3, 1, 6, 5, 2, 4})
	fmt.Print("Extract order: ")
	for h.Len() > 0 {
		v, _ := h.Pop()
		fmt.Print(v, " ")
	}
	fmt.Println()

	// Segment tree demo
	fmt.Println("\n=== SEGMENT TREE ===")
	st := NewSegTree([]int{1, 2, 3, 4, 5})
	fmt.Println("Sum [0..4]:", st.Query(0, 4)) // 15
	st.Update(1, 3, 10)                         // add 10 to indices 1-3
	fmt.Println("After +10 to [1,3], Sum [0..4]:", st.Query(0, 4)) // 15+30=45

	// BIT demo
	fmt.Println("\n=== FENWICK TREE ===")
	bit := NewBIT(8)
	for i, v := range []int{3, 2, 1, 4, 5, 2, 7, 3} {
		bit.Update(i+1, int64(v))
	}
	fmt.Println("Prefix sum [1..7]:", bit.Query(7))      // 24
	fmt.Println("Range sum [3..6]:", bit.RangeQuery(3, 6)) // 12

	// Trie demo
	fmt.Println("\n=== TRIE ===")
	trie := NewTrie()
	for _, w := range []string{"cat", "car", "card", "care", "bat"} {
		trie.Insert(w)
	}
	fmt.Println("Search 'car':", trie.Search("car"))
	fmt.Println("Search 'ca':", trie.Search("ca"))
	fmt.Println("StartsWith 'car':", trie.StartsWith("car"))
	fmt.Println("Count with prefix 'car':", trie.CountWithPrefix("car"))

	// Diameter demo
	fmt.Println("\n=== TREE DIAMETER ===")
	adj := make([][]int, 7)
	edges := [][2]int{{0, 1}, {0, 2}, {1, 3}, {1, 4}, {4, 5}, {4, 6}}
	for _, e := range edges {
		adj[e[0]] = append(adj[e[0]], e[1])
		adj[e[1]] = append(adj[e[1]], e[0])
	}
	fmt.Println("Diameter:", treeDiameter(adj, 7))

	// Serialize demo
	fmt.Println("\n=== SERIALIZE/DESERIALIZE ===")
	root := &TreeNode{
		Val:  1,
		Left: &TreeNode{Val: 2, Left: &TreeNode{Val: 4}, Right: &TreeNode{Val: 5}},
		Right: &TreeNode{Val: 3},
	}
	s := serialize(root)
	fmt.Println("Serialized:", s)
	root2 := deserialize(s)
	fmt.Println("Deserialized root val:", root2.Val)

	_ = math.MaxInt64 // just to ensure math import used
}
```

---

### Rust Implementation

```rust
// ============================================================
// COMPLETE TREE IMPLEMENTATION IN RUST
// Covers: BST, AVL, Heap, Segment Tree, Trie
// Safe Rust with ownership-correct patterns
// ============================================================

use std::cmp::{max, Ordering};
use std::collections::VecDeque;

// ─────────────────────────────────────────────
// SECTION 1: BST (Box-based, safe ownership)
// ─────────────────────────────────────────────

#[derive(Debug)]
pub struct BSTNode {
    pub val: i32,
    pub left: Option<Box<BSTNode>>,
    pub right: Option<Box<BSTNode>>,
}

impl BSTNode {
    pub fn new(val: i32) -> Box<Self> {
        Box::new(BSTNode { val, left: None, right: None })
    }
}

pub fn bst_insert(root: Option<Box<BSTNode>>, val: i32) -> Box<BSTNode> {
    match root {
        None => BSTNode::new(val),
        Some(mut node) => {
            match val.cmp(&node.val) {
                Ordering::Less    => node.left  = Some(bst_insert(node.left.take(), val)),
                Ordering::Greater => node.right = Some(bst_insert(node.right.take(), val)),
                Ordering::Equal   => {} // ignore duplicate
            }
            node
        }
    }
}

fn bst_find_min(root: &Box<BSTNode>) -> i32 {
    let mut cur = root;
    while let Some(ref left) = cur.left {
        cur = left;
    }
    cur.val
}

pub fn bst_delete(root: Option<Box<BSTNode>>, val: i32) -> Option<Box<BSTNode>> {
    root.map(|mut node| {
        match val.cmp(&node.val) {
            Ordering::Less => {
                node.left = bst_delete(node.left.take(), val);
                node
            }
            Ordering::Greater => {
                node.right = bst_delete(node.right.take(), val);
                node
            }
            Ordering::Equal => {
                // Found: handle 3 cases
                match (node.left.take(), node.right.take()) {
                    (None, right) => return right,    // no left child
                    (left, None)  => return left,     // no right child
                    (left, right) => {
                        // Two children: find inorder successor
                        let succ_val = bst_find_min(right.as_ref().unwrap());
                        node.val = succ_val;
                        node.left = left;
                        node.right = bst_delete(right, succ_val);
                        node
                    }
                }
            }
        }
    })
}

pub fn bst_inorder(root: &Option<Box<BSTNode>>, result: &mut Vec<i32>) {
    if let Some(node) = root {
        bst_inorder(&node.left, result);
        result.push(node.val);
        bst_inorder(&node.right, result);
    }
}

pub fn bst_validate(node: &Option<Box<BSTNode>>, min: Option<i32>, max: Option<i32>) -> bool {
    match node {
        None => true,
        Some(n) => {
            if let Some(mn) = min { if n.val <= mn { return false; } }
            if let Some(mx) = max { if n.val >= mx { return false; } }
            bst_validate(&n.left, min, Some(n.val)) &&
            bst_validate(&n.right, Some(n.val), max)
        }
    }
}

// Iterative inorder (avoids recursion stack overflow)
pub fn bst_iterative_inorder(root: &Option<Box<BSTNode>>) -> Vec<i32> {
    let mut result = Vec::new();
    let mut stack: Vec<*const BSTNode> = Vec::new();
    let mut curr: *const BSTNode = root
        .as_ref()
        .map(|n| n.as_ref() as *const BSTNode)
        .unwrap_or(std::ptr::null());

    // SAFETY: We only dereference valid pointers from our tree
    unsafe {
        loop {
            while !curr.is_null() {
                stack.push(curr);
                curr = (*curr).left
                    .as_ref()
                    .map(|n| n.as_ref() as *const BSTNode)
                    .unwrap_or(std::ptr::null());
            }
            match stack.pop() {
                None => break,
                Some(ptr) => {
                    result.push((*ptr).val);
                    curr = (*ptr).right
                        .as_ref()
                        .map(|n| n.as_ref() as *const BSTNode)
                        .unwrap_or(std::ptr::null());
                }
            }
        }
    }
    result
}

// ─────────────────────────────────────────────
// SECTION 2: AVL Tree (arena-allocated for efficiency)
// ─────────────────────────────────────────────

#[derive(Debug, Default)]
pub struct AVLNode {
    pub val: i32,
    pub height: i32,
    pub left: Option<Box<AVLNode>>,
    pub right: Option<Box<AVLNode>>,
}

impl AVLNode {
    fn new(val: i32) -> Box<Self> {
        Box::new(AVLNode { val, height: 0, ..Default::default() })
    }
}

fn avl_height(n: &Option<Box<AVLNode>>) -> i32 {
    n.as_ref().map_or(-1, |node| node.height)
}

fn avl_update_height(n: &mut Box<AVLNode>) {
    let lh = avl_height(&n.left);
    let rh = avl_height(&n.right);
    n.height = 1 + max(lh, rh);
}

fn avl_bf(n: &Box<AVLNode>) -> i32 {
    avl_height(&n.left) - avl_height(&n.right)
}

fn avl_rotate_right(mut y: Box<AVLNode>) -> Box<AVLNode> {
    let mut x = y.left.take().expect("rotate_right requires left child");
    y.left = x.right.take();
    avl_update_height(&mut y);
    x.right = Some(y);
    avl_update_height(&mut x);
    x
}

fn avl_rotate_left(mut x: Box<AVLNode>) -> Box<AVLNode> {
    let mut y = x.right.take().expect("rotate_left requires right child");
    x.right = y.left.take();
    avl_update_height(&mut x);
    y.left = Some(x);
    avl_update_height(&mut y);
    y
}

fn avl_balance(mut node: Box<AVLNode>) -> Box<AVLNode> {
    avl_update_height(&mut node);
    let bf = avl_bf(&node);

    if bf > 1 {
        // Left heavy
        if avl_bf(node.left.as_ref().unwrap()) < 0 {
            // LR case: left rotate left child first
            let left = node.left.take().unwrap();
            node.left = Some(avl_rotate_left(left));
        }
        // LL case (or after LR fix)
        avl_rotate_right(node)
    } else if bf < -1 {
        // Right heavy
        if avl_bf(node.right.as_ref().unwrap()) > 0 {
            // RL case: right rotate right child first
            let right = node.right.take().unwrap();
            node.right = Some(avl_rotate_right(right));
        }
        // RR case (or after RL fix)
        avl_rotate_left(node)
    } else {
        node
    }
}

pub fn avl_insert(root: Option<Box<AVLNode>>, val: i32) -> Box<AVLNode> {
    match root {
        None => AVLNode::new(val),
        Some(mut node) => {
            match val.cmp(&node.val) {
                Ordering::Less    => node.left  = Some(avl_insert(node.left.take(), val)),
                Ordering::Greater => node.right = Some(avl_insert(node.right.take(), val)),
                Ordering::Equal   => return node,
            }
            avl_balance(node)
        }
    }
}

fn avl_find_min(root: &Box<AVLNode>) -> i32 {
    let mut cur = root;
    while let Some(ref left) = cur.left { cur = left; }
    cur.val
}

pub fn avl_delete(root: Option<Box<AVLNode>>, val: i32) -> Option<Box<AVLNode>> {
    root.map(|mut node| {
        match val.cmp(&node.val) {
            Ordering::Less => {
                node.left = avl_delete(node.left.take(), val);
                avl_balance(node)
            }
            Ordering::Greater => {
                node.right = avl_delete(node.right.take(), val);
                avl_balance(node)
            }
            Ordering::Equal => {
                match (node.left.take(), node.right.take()) {
                    (None, right) => return right,
                    (left, None)  => return left,
                    (left, right) => {
                        let succ_val = avl_find_min(right.as_ref().unwrap());
                        node.val = succ_val;
                        node.left = left;
                        node.right = avl_delete(right, succ_val);
                        avl_balance(node)
                    }
                }
            }
        }
    })
}

// ─────────────────────────────────────────────
// SECTION 3: Binary Max Heap (1-indexed Vec)
// ─────────────────────────────────────────────

pub struct MaxHeap {
    data: Vec<i32>, // data[0] is sentinel/unused; 1-indexed
}

impl MaxHeap {
    pub fn new() -> Self {
        MaxHeap { data: vec![0] } // sentinel
    }

    pub fn len(&self) -> usize {
        self.data.len() - 1
    }

    pub fn is_empty(&self) -> bool {
        self.len() == 0
    }

    fn sift_up(&mut self, mut i: usize) {
        while i > 1 && self.data[i / 2] < self.data[i] {
            self.data.swap(i / 2, i);
            i /= 2;
        }
    }

    fn sift_down(&mut self, mut i: usize) {
        let n = self.len();
        loop {
            let mut largest = i;
            let l = 2 * i;
            let r = 2 * i + 1;
            if l <= n && self.data[l] > self.data[largest] { largest = l; }
            if r <= n && self.data[r] > self.data[largest] { largest = r; }
            if largest == i { break; }
            self.data.swap(i, largest);
            i = largest;
        }
    }

    pub fn push(&mut self, val: i32) {
        self.data.push(val);
        let i = self.len();
        self.sift_up(i);
    }

    pub fn pop(&mut self) -> Option<i32> {
        if self.is_empty() { return None; }
        let max = self.data[1];
        let last = self.data.len() - 1;
        self.data.swap(1, last);
        self.data.pop();
        if !self.is_empty() { self.sift_down(1); }
        Some(max)
    }

    pub fn peek(&self) -> Option<i32> {
        if self.is_empty() { None } else { Some(self.data[1]) }
    }

    // Floyd's O(n) build
    pub fn from_vec(arr: Vec<i32>) -> Self {
        let mut heap = MaxHeap { data: std::iter::once(0).chain(arr).collect() };
        let n = heap.len();
        for i in (1..=n / 2).rev() {
            heap.sift_down(i);
        }
        heap
    }
}

// ─────────────────────────────────────────────
// SECTION 4: Segment Tree (Range Sum + Lazy Add)
// ─────────────────────────────────────────────

pub struct SegTree {
    n: usize,
    tree: Vec<i64>,
    lazy: Vec<i64>,
}

impl SegTree {
    pub fn new(arr: &[i64]) -> Self {
        let n = arr.len();
        let mut st = SegTree {
            n,
            tree: vec![0; 4 * n],
            lazy: vec![0; 4 * n],
        };
        if n > 0 { st.build(arr, 1, 0, n - 1); }
        st
    }

    fn build(&mut self, arr: &[i64], node: usize, l: usize, r: usize) {
        if l == r {
            self.tree[node] = arr[l];
            return;
        }
        let mid = l + (r - l) / 2;
        self.build(arr, 2 * node, l, mid);
        self.build(arr, 2 * node + 1, mid + 1, r);
        self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1];
    }

    fn push_down(&mut self, node: usize, l: usize, r: usize) {
        if self.lazy[node] == 0 { return; }
        let mid = l + (r - l) / 2;
        let lv = self.lazy[node];
        self.tree[2 * node]     += lv * (mid - l + 1) as i64;
        self.lazy[2 * node]     += lv;
        self.tree[2 * node + 1] += lv * (r - mid) as i64;
        self.lazy[2 * node + 1] += lv;
        self.lazy[node] = 0;
    }

    fn update_inner(&mut self, node: usize, l: usize, r: usize,
                    ql: usize, qr: usize, val: i64) {
        if qr < l || r < ql { return; }
        if ql <= l && r <= qr {
            self.tree[node] += val * (r - l + 1) as i64;
            self.lazy[node] += val;
            return;
        }
        self.push_down(node, l, r);
        let mid = l + (r - l) / 2;
        self.update_inner(2 * node, l, mid, ql, qr, val);
        self.update_inner(2 * node + 1, mid + 1, r, ql, qr, val);
        self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1];
    }

    fn query_inner(&mut self, node: usize, l: usize, r: usize,
                   ql: usize, qr: usize) -> i64 {
        if qr < l || r < ql { return 0; }
        if ql <= l && r <= qr { return self.tree[node]; }
        self.push_down(node, l, r);
        let mid = l + (r - l) / 2;
        self.query_inner(2 * node, l, mid, ql, qr) +
        self.query_inner(2 * node + 1, mid + 1, r, ql, qr)
    }

    pub fn update(&mut self, l: usize, r: usize, val: i64) {
        let n = self.n;
        self.update_inner(1, 0, n - 1, l, r, val);
    }

    pub fn query(&mut self, l: usize, r: usize) -> i64 {
        let n = self.n;
        self.query_inner(1, 0, n - 1, l, r)
    }
}

// ─────────────────────────────────────────────
// SECTION 5: Fenwick Tree (BIT)
// ─────────────────────────────────────────────

pub struct BIT {
    data: Vec<i64>,
}

impl BIT {
    pub fn new(n: usize) -> Self {
        BIT { data: vec![0; n + 1] }
    }

    pub fn update(&mut self, mut i: usize, delta: i64) {
        while i < self.data.len() {
            self.data[i] += delta;
            i += i & i.wrapping_neg(); // i += lowbit(i)
        }
    }

    pub fn query(&self, mut i: usize) -> i64 {
        let mut s = 0i64;
        while i > 0 {
            s += self.data[i];
            i -= i & i.wrapping_neg(); // i -= lowbit(i)
        }
        s
    }

    pub fn range_query(&self, l: usize, r: usize) -> i64 {
        self.query(r) - if l > 0 { self.query(l - 1) } else { 0 }
    }
}

// ─────────────────────────────────────────────
// SECTION 6: Trie
// ─────────────────────────────────────────────

const ALPHA: usize = 26;

#[derive(Default)]
pub struct TrieNode {
    children: [Option<Box<TrieNode>>; ALPHA],
    is_end: bool,
    count: usize,
}

pub struct Trie {
    root: Box<TrieNode>,
}

impl Trie {
    pub fn new() -> Self {
        Trie { root: Box::new(TrieNode::default()) }
    }

    pub fn insert(&mut self, word: &str) {
        let mut cur = &mut *self.root;
        for ch in word.chars() {
            let idx = (ch as u8 - b'a') as usize;
            if cur.children[idx].is_none() {
                cur.children[idx] = Some(Box::new(TrieNode::default()));
            }
            cur = cur.children[idx].as_mut().unwrap();
            cur.count += 1;
        }
        cur.is_end = true;
    }

    pub fn search(&self, word: &str) -> bool {
        let mut cur = &*self.root;
        for ch in word.chars() {
            let idx = (ch as u8 - b'a') as usize;
            match &cur.children[idx] {
                None => return false,
                Some(node) => cur = node,
            }
        }
        cur.is_end
    }

    pub fn starts_with(&self, prefix: &str) -> bool {
        let mut cur = &*self.root;
        for ch in prefix.chars() {
            let idx = (ch as u8 - b'a') as usize;
            match &cur.children[idx] {
                None => return false,
                Some(node) => cur = node,
            }
        }
        true
    }

    pub fn count_with_prefix(&self, prefix: &str) -> usize {
        let mut cur = &*self.root;
        for ch in prefix.chars() {
            let idx = (ch as u8 - b'a') as usize;
            match &cur.children[idx] {
                None => return 0,
                Some(node) => cur = node,
            }
        }
        cur.count
    }
}

// ─────────────────────────────────────────────
// SECTION 7: Level Order Traversal (BFS)
// ─────────────────────────────────────────────

pub fn level_order(root: &Option<Box<BSTNode>>) -> Vec<Vec<i32>> {
    let mut result = Vec::new();
    if root.is_none() { return result; }

    let mut queue: VecDeque<*const BSTNode> = VecDeque::new();
    // SAFETY: root is valid for the duration of this function
    unsafe {
        queue.push_back(root.as_ref().unwrap().as_ref() as *const BSTNode);
        while !queue.is_empty() {
            let level_size = queue.len();
            let mut level = Vec::with_capacity(level_size);
            for _ in 0..level_size {
                let ptr = queue.pop_front().unwrap();
                level.push((*ptr).val);
                if let Some(ref left) = (*ptr).left {
                    queue.push_back(left.as_ref() as *const BSTNode);
                }
                if let Some(ref right) = (*ptr).right {
                    queue.push_back(right.as_ref() as *const BSTNode);
                }
            }
            result.push(level);
        }
    }
    result
}

// ─────────────────────────────────────────────
// SECTION 8: LCA (Binary Lifting on Vec-based tree)
// ─────────────────────────────────────────────

pub struct LCATree {
    depth: Vec<usize>,
    up: Vec<Vec<usize>>, // up[v][j] = 2^j-th ancestor of v
    adj: Vec<Vec<usize>>,
    log: usize,
}

impl LCATree {
    pub fn new(n: usize) -> Self {
        let log = (usize::BITS - n.leading_zeros()) as usize + 1;
        LCATree {
            depth: vec![0; n],
            up: vec![vec![0; log]; n],
            adj: vec![Vec::new(); n],
            log,
        }
    }

    pub fn add_edge(&mut self, u: usize, v: usize) {
        self.adj[u].push(v);
        self.adj[v].push(u);
    }

    pub fn build(&mut self, root: usize) {
        self.dfs(root, root, 0);
    }

    fn dfs(&mut self, u: usize, parent: usize, d: usize) {
        self.depth[u] = d;
        self.up[u][0] = parent;
        for j in 1..self.log {
            let anc = self.up[u][j-1];
            self.up[u][j] = self.up[anc][j-1];
        }
        let neighbors: Vec<usize> = self.adj[u].clone();
        for v in neighbors {
            if v != parent {
                self.dfs(v, u, d + 1);
            }
        }
    }

    pub fn lca(&self, mut u: usize, mut v: usize) -> usize {
        if self.depth[u] < self.depth[v] { std::mem::swap(&mut u, &mut v); }
        let mut diff = self.depth[u] - self.depth[v];
        for j in 0..self.log {
            if (diff >> j) & 1 == 1 { u = self.up[u][j]; }
        }
        if u == v { return u; }
        for j in (0..self.log).rev() {
            if self.up[u][j] != self.up[v][j] {
                u = self.up[u][j];
                v = self.up[v][j];
            }
        }
        self.up[u][0]
    }
}

// ─────────────────────────────────────────────
// MAIN DEMO
// ─────────────────────────────────────────────

fn main() {
    // BST
    println!("=== BST ===");
    let mut bst: Option<Box<BSTNode>> = None;
    for &v in &[5, 3, 7, 1, 4, 6, 8] {
        bst = Some(bst_insert(bst.take(), v));
    }
    let mut inorder = Vec::new();
    bst_inorder(&bst, &mut inorder);
    println!("Inorder: {:?}", inorder);
    println!("Iterative: {:?}", bst_iterative_inorder(&bst));
    println!("Valid BST: {}", bst_validate(&bst, None, None));

    // AVL
    println!("\n=== AVL ===");
    let mut avl: Option<Box<AVLNode>> = None;
    for i in 1..=7 {
        avl = Some(avl_insert(avl.take(), i));
    }
    let avl_root = avl.as_ref().unwrap();
    println!("Root: {}, height: {} (balanced despite sorted insert!)", avl_root.val, avl_root.height);

    // Heap
    println!("\n=== MAX HEAP ===");
    let mut heap = MaxHeap::from_vec(vec![3, 1, 6, 5, 2, 4]);
    print!("Extract order: ");
    while let Some(v) = heap.pop() { print!("{} ", v); }
    println!();

    // Segment Tree
    println!("\n=== SEGMENT TREE ===");
    let mut st = SegTree::new(&[1, 2, 3, 4, 5]);
    println!("Sum [0..4]: {}", st.query(0, 4)); // 15
    st.update(1, 3, 10);
    println!("After +10 to [1,3], Sum [0..4]: {}", st.query(0, 4)); // 45

    // BIT
    println!("\n=== FENWICK TREE ===");
    let mut bit = BIT::new(8);
    for (i, &v) in [3i64, 2, 1, 4, 5, 2, 7, 3].iter().enumerate() {
        bit.update(i + 1, v);
    }
    println!("Prefix sum [1..7]: {}", bit.query(7));       // 24
    println!("Range sum [3..6]: {}", bit.range_query(3, 6)); // 12

    // Trie
    println!("\n=== TRIE ===");
    let mut trie = Trie::new();
    for w in &["cat", "car", "card", "care", "bat"] {
        trie.insert(w);
    }
    println!("Search 'car': {}", trie.search("car"));
    println!("Search 'ca': {}", trie.search("ca"));
    println!("StartsWith 'car': {}", trie.starts_with("car"));
    println!("Count with prefix 'car': {}", trie.count_with_prefix("car"));

    // LCA
    println!("\n=== LCA ===");
    let mut lca_tree = LCATree::new(7);
    for &(u, v) in &[(0usize,1usize),(0,2),(1,3),(1,4),(4,5),(4,6)] {
        lca_tree.add_edge(u, v);
    }
    lca_tree.build(0);
    println!("LCA(3, 4) = {} (expected 1)", lca_tree.lca(3, 4));
    println!("LCA(5, 6) = {} (expected 4)", lca_tree.lca(5, 6));
    println!("LCA(3, 6) = {} (expected 1)", lca_tree.lca(3, 6));
}
```

---

## Summary: Mental Model for Tree Problems

```
When you see a tree problem, ask:

1. WHAT TYPE OF TREE?
   Ordered? → BST family
   Balanced? → AVL or RB
   Priority? → Heap
   Range? → Segment or BIT
   String? → Trie
   General? → N-ary or adjacency list

2. WHAT OPERATION?
   Point query? → BST search O(log n)
   Range query? → Segment tree O(log n)
   Range update? → Lazy segment tree O(log n)
   Prefix query? → BIT O(log n)
   Path query? → LCA + binary lifting
   Ancestry? → DFS timestamps (in-time, out-time)

3. WHAT TRAVERSAL?
   Sorted output? → Inorder
   Top-down processing? → Preorder
   Bottom-up (children before parent)? → Postorder
   Level processing? → BFS

4. RECURSIVE OR ITERATIVE?
   Deep trees? → Iterative (avoid stack overflow)
   Simple logic? → Recursive (cleaner)
   O(1) space? → Morris traversal

5. WHAT INVARIANT MUST HOLD?
   BST: left < node < right (with BOUNDS, not just parent check!)
   AVL: |BF| ≤ 1 at every node
   RB: 5 properties simultaneously
   Heap: parent dominates children
   Segment tree: node = f(children)

When stuck: Draw the tree. Trace one example by hand.
The bug is almost always: wrong null check, wrong height update,
wrong bounds in validation, or wrong rotation case.
```

---

*This guide covers: BST, AVL, Red-Black, Heap, Segment Tree (with lazy propagation), Fenwick Tree, Trie, B-Tree, B+ Tree, Treap, Splay Tree, N-ary Tree, Morris Traversal, LCA Binary Lifting, Tree Diameter, Serialization, and all major common mistakes.*
