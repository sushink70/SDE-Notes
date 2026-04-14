# Binary Search Tree (BST) — Complete Mastery Guide

> *"The tree that bends in the wind survives the storm. The tree that understands its own structure dominates it."*
> — A world-class DSA mentor

---

## Table of Contents

1. [Mental Model Before Anything Else](#1-mental-model-before-anything-else)
2. [Foundational Vocabulary — Every Term Defined](#2-foundational-vocabulary)
3. [What Is a Binary Search Tree?](#3-what-is-a-binary-search-tree)
4. [The BST Property — The Core Law](#4-the-bst-property)
5. [Visual Anatomy of a BST](#5-visual-anatomy-of-a-bst)
6. [Node Structure — Implementation Foundation](#6-node-structure)
7. [BST Operations — Deep Dive](#7-bst-operations)
   - 7.1 [Search](#71-search)
   - 7.2 [Insert](#72-insert)
   - 7.3 [Delete — The Hardest Operation](#73-delete)
   - 7.4 [Find Minimum and Maximum](#74-find-minimum-and-maximum)
   - 7.5 [Successor and Predecessor](#75-successor-and-predecessor)
   - 7.6 [Height and Depth](#76-height-and-depth)
   - 7.7 [Count Nodes](#77-count-nodes)
8. [Tree Traversals — All Four Patterns](#8-tree-traversals)
   - 8.1 [Inorder (LNR)](#81-inorder-lnr)
   - 8.2 [Preorder (NLR)](#82-preorder-nlr)
   - 8.3 [Postorder (LRN)](#83-postorder-lrn)
   - 8.4 [Level-Order (BFS)](#84-level-order-bfs)
9. [BST Validation](#9-bst-validation)
10. [Balanced vs Unbalanced BST](#10-balanced-vs-unbalanced-bst)
11. [Time and Space Complexity Analysis](#11-time-and-space-complexity-analysis)
12. [Complete Implementations](#12-complete-implementations)
    - [Go Implementation](#go-implementation)
    - [C Implementation](#c-implementation)
    - [Rust Implementation](#rust-implementation)
13. [Common BST Patterns and Problem Templates](#13-common-bst-patterns-and-problem-templates)
14. [Expert Mental Models and Intuition Building](#14-expert-mental-models-and-intuition-building)
15. [Edge Cases — What Breaks Average Programmers](#15-edge-cases)

---

## 1. Mental Model Before Anything Else

Before writing a single line of code, an expert builds a **mental simulation** of the data structure. This is called **Schema Formation** in cognitive science — building an internal model you can run in your head.

Think of a BST as a **decision tree for a sorted dictionary**:

```
You have 1 million names sorted alphabetically.
You open the book to the MIDDLE page.
- Is the name you want BEFORE the middle? → Go left half.
- Is it AFTER the middle? → Go right half.
- Is it the SAME? → Found it.
Repeat on the half you chose.
```

This is **binary search made spatial**. Instead of an array, you store this structure as linked nodes in memory — and that's a BST.

**The key insight**: Every node IS a decision point. Left means "smaller", right means "larger". The structure of the tree encodes the sorting order.

---

## 2. Foundational Vocabulary

Every term you will encounter, defined precisely:

```
                        ┌─────────────────────────────────────┐
                        │           TREE VOCABULARY            │
                        └─────────────────────────────────────┘

┌─────────┬──────────────────────────────────────────────────────────────┐
│  Term   │  Definition                                                   │
├─────────┼──────────────────────────────────────────────────────────────┤
│  Node   │  A single element in the tree. Contains a VALUE (key) and    │
│         │  POINTERS to its children.                                    │
├─────────┼──────────────────────────────────────────────────────────────┤
│  Root   │  The topmost node. Has NO parent. Every tree has exactly one. │
├─────────┼──────────────────────────────────────────────────────────────┤
│  Leaf   │  A node with NO children (both left and right are NULL/nil).  │
├─────────┼──────────────────────────────────────────────────────────────┤
│  Parent │  A node that has one or more children below it.              │
├─────────┼──────────────────────────────────────────────────────────────┤
│  Child  │  A node directly connected BELOW another node.               │
├─────────┼──────────────────────────────────────────────────────────────┤
│Subtree  │  A node AND all of its descendants. Every node is the root   │
│         │  of its own subtree.                                          │
├─────────┼──────────────────────────────────────────────────────────────┤
│ Depth   │  Distance from the ROOT to a given node. Root has depth 0.   │
├─────────┼──────────────────────────────────────────────────────────────┤
│ Height  │  Distance from a node DOWN to the FARTHEST LEAF below it.    │
│         │  A leaf node has height 0. An empty tree has height -1.      │
├─────────┼──────────────────────────────────────────────────────────────┤
│  Level  │  All nodes at the same depth. Level 0 = root level.          │
├─────────┼──────────────────────────────────────────────────────────────┤
│Ancestor │  Any node on the path from root to a given node (inclusive). │
├─────────┼──────────────────────────────────────────────────────────────┤
│Descend. │  Any node in the subtree below a given node.                 │
├─────────┼──────────────────────────────────────────────────────────────┤
│Successor│  The node with the NEXT LARGER value. In inorder traversal,  │
│         │  the node that comes AFTER the current node.                  │
├─────────┼──────────────────────────────────────────────────────────────┤
│Predecess│  The node with the NEXT SMALLER value. Comes BEFORE in       │
│         │  inorder traversal.                                           │
├─────────┼──────────────────────────────────────────────────────────────┤
│  Edge   │  The connection (pointer/link) between a parent and child.   │
├─────────┼──────────────────────────────────────────────────────────────┤
│  Path   │  Sequence of nodes connected by edges from one node to       │
│         │  another.                                                     │
├─────────┼──────────────────────────────────────────────────────────────┤
│ Pivot   │  In tree rotations (balancing), the node around which        │
│         │  restructuring happens. Used in AVL/Red-Black trees.         │
├─────────┼──────────────────────────────────────────────────────────────┤
│ Skewed  │  A BST where all nodes lean one direction — becomes a        │
│         │  linked list. Worst case for performance.                     │
└─────────┴──────────────────────────────────────────────────────────────┘
```

---

## 3. What Is a Binary Search Tree?

A BST is a **binary tree** (each node has at most 2 children) with a **special ordering constraint** on every node.

### From General Tree → Binary Tree → BST

```
GENERAL TREE                  BINARY TREE              BINARY SEARCH TREE
(Any # of children)           (≤2 children)            (+ ordering rule)

        A                         A                           8
      / | \                      / \                         / \
     B  C  D                    B   C                       3   10
    /|      \                  / \   \                     / \    \
   E  F      G                D   E   F                  1   6    14
                                                             / \   /
                                                            4   7 13

No ordering rule         No ordering rule          LEFT < NODE < RIGHT
                                                   (at every single node)
```

---

## 4. The BST Property — The Core Law

This is the **invariant** — the rule that must ALWAYS be true:

```
┌──────────────────────────────────────────────────────────────┐
│                    THE BST INVARIANT                          │
│                                                              │
│   For EVERY node N in the tree:                              │
│                                                              │
│   • ALL values in N's LEFT subtree  < N's value             │
│   • ALL values in N's RIGHT subtree > N's value             │
│                                                              │
│   This must hold for EVERY node, not just the root!         │
└──────────────────────────────────────────────────────────────┘
```

### Common Mistake — The Subtree Trap

Many beginners check only IMMEDIATE children. This is WRONG:

```
         10
        /  \
       5    15
      / \
     2   12   ← VIOLATION! 12 is in the LEFT subtree of 10
                but 12 > 10. This is NOT a valid BST!
```

You must verify against ALL ANCESTORS, not just the immediate parent.

---

## 5. Visual Anatomy of a BST

```
                         ┌──────────────────────────────────────────┐
                         │         ANATOMY OF A BST                  │
                         └──────────────────────────────────────────┘

                              [8]          ← ROOT (depth=0, height=3)
                             /   \
                           [3]   [10]      ← depth=1
                           / \      \
                         [1] [6]   [14]   ← depth=2
                             / \   /
                           [4] [7][13]    ← LEAVES (depth=3, height=0)

  ┌─────────────────────────────────────────────────────────────────┐
  │  Node  │ Depth │ Height │ Parent │  Left  │  Right │  Type     │
  ├─────────┼───────┼────────┼────────┼────────┼────────┼───────────┤
  │   8    │   0   │   3    │  none  │   3    │   10   │  Root     │
  │   3    │   1   │   2    │   8    │   1    │   6    │  Internal │
  │  10    │   1   │   2    │   8    │  none  │   14   │  Internal │
  │   1    │   2   │   0    │   3    │  none  │  none  │  Leaf     │
  │   6    │   2   │   1    │   3    │   4    │   7    │  Internal │
  │  14    │   2   │   1    │  10    │   13   │  none  │  Internal │
  │   4    │   3   │   0    │   6    │  none  │  none  │  Leaf     │
  │   7    │   3   │   0    │   6    │  none  │  none  │  Leaf     │
  │  13    │   3   │   0    │  14    │  none  │  none  │  Leaf     │
  └─────────┴───────┴────────┴────────┴────────┴────────┴───────────┘

  BST Property Verification:
  • Node 8:  Left subtree {3,1,6,4,7} all < 8 ✓   Right subtree {10,14,13} all > 8 ✓
  • Node 3:  Left subtree {1} < 3 ✓               Right subtree {6,4,7} all > 3 ✓
  • Node 6:  Left subtree {4} < 6 ✓               Right subtree {7} > 6 ✓
  • Node 10: Left subtree {} empty ✓               Right subtree {14,13} all > 10 ✓
  • Node 14: Left subtree {13} < 14 ✓              Right subtree {} empty ✓
```

---

## 6. Node Structure — Implementation Foundation

Every node needs three components:

```
┌─────────────────────────────────────────┐
│              NODE STRUCTURE              │
│                                         │
│   ┌──────┬──────────┬──────────┐        │
│   │ LEFT │  VALUE   │  RIGHT   │        │
│   │ ptr  │  (key)   │  ptr     │        │
│   └──────┴──────────┴──────────┘        │
│      │                    │             │
│      ▼                    ▼             │
│   (child node          (child node      │
│    or NULL)             or NULL)        │
└─────────────────────────────────────────┘
```

---

## 7. BST Operations — Deep Dive

### 7.1 Search

**Concept**: Exploit the BST property to eliminate half the tree at each step.

**Expert Thinking Process**:
```
1. Start at root
2. Is target == current node's value? → FOUND
3. Is target < current node's value?  → Go LEFT (target is in left subtree)
4. Is target > current node's value?  → Go RIGHT (target is in right subtree)
5. Reached NULL? → NOT FOUND
```

**Decision Tree for Search**:
```
                    START at ROOT
                         │
                         ▼
              ┌──────────────────┐
              │  current = NULL? │
              └────────┬─────────┘
                 YES   │   NO
                  │    │
                  ▼    ▼
              NOT    ┌─────────────────────┐
              FOUND  │ target == current?  │
                     └──────┬──────────────┘
                       YES  │  NO
                        │   │
                        ▼   ▼
                      FOUND ┌──────────────────────┐
                            │  target < current?   │
                            └──────┬───────────────┘
                              YES  │  NO
                               │   │
                               ▼   ▼
                             Go   Go
                            LEFT RIGHT
                            (recurse/iterate)
```

**Trace on example tree (searching for 6)**:
```
Tree:           8
               / \
              3   10
             / \
            1   6   ← target
               / \
              4   7

Step 1: current=8,  target=6,  6 < 8  → Go LEFT
Step 2: current=3,  target=6,  6 > 3  → Go RIGHT
Step 3: current=6,  target=6,  6 == 6 → FOUND ✓

Steps taken: 3  (log₂(9) ≈ 3.17 — nearly optimal)
```

**Time Complexity**:
- Best/Average: O(log n) — balanced tree
- Worst: O(n) — completely skewed tree (like a linked list)

---

### 7.2 Insert

**Concept**: Search for WHERE the value WOULD BE, then place it there.

**Key insight**: In a BST, every new node is ALWAYS inserted as a LEAF. You never insert in the middle.

**Algorithm Flow**:
```
                    START: insert value V
                           │
                           ▼
              ┌────────────────────────┐
              │   Tree is EMPTY?       │
              └────────────┬───────────┘
                  YES      │     NO
                   │       │
                   ▼       ▼
              V becomes  ┌──────────────────────┐
               new ROOT  │   V == current.val?  │
                         └──────┬───────────────┘
                          YES   │    NO
                           │    │
                           ▼    ▼
                        DUPLICATE ┌─────────────────────┐
                        (ignore   │   V < current.val?  │
                         or error)└──────┬──────────────┘
                                   YES  │  NO
                                    │   │
                                    ▼   ▼
                               Go LEFT  Go RIGHT
                                    │       │
                                    ▼       ▼
                           ┌──────────────────────┐
                           │  child is NULL/nil?  │
                           └────────┬─────────────┘
                              YES   │   NO
                               │    │
                               ▼    ▼
                           INSERT  Continue
                          new node  searching
                           here
```

**Trace — Inserting 5 into the tree**:
```
Before Insert:
         8
        / \
       3   10
      / \    \
     1   6   14
        / \  /
       4   7 13

Step 1: current=8,  5 < 8  → Go LEFT
Step 2: current=3,  5 > 3  → Go RIGHT
Step 3: current=6,  5 < 6  → Go LEFT
Step 4: current=4,  5 > 4  → Go RIGHT
Step 5: current=NULL → INSERT 5 as right child of 4

After Insert:
         8
        / \
       3   10
      / \    \
     1   6   14
        / \  /
       4   7 13
        \
         5   ← new node
```

---

### 7.3 Delete — The Hardest Operation

Deletion requires careful handling of three distinct cases. This is where most programmers make mistakes.

**The Three Cases**:

```
┌─────────────────────────────────────────────────────────────────────┐
│                   DELETE — THREE CASES                               │
├─────────────────────────────────────────────────────────────────────┤
│ CASE 1: Node is a LEAF (no children)                                │
│   → Simply remove it. Set parent's pointer to NULL.                 │
│                                                                     │
│ CASE 2: Node has ONE child                                          │
│   → Replace the node with its only child.                           │
│   → Parent now points directly to the grandchild.                   │
│                                                                     │
│ CASE 3: Node has TWO children  ← THE COMPLEX CASE                  │
│   → Find the INORDER SUCCESSOR (smallest in right subtree)          │
│   → Copy successor's VALUE into the node being deleted              │
│   → Delete the SUCCESSOR (which has at most 1 child — Case 1 or 2) │
└─────────────────────────────────────────────────────────────────────┘
```

**Why inorder successor for Case 3?**

The inorder successor is the smallest value in the right subtree. If we put it where the deleted node was:
- It's larger than everything in the LEFT subtree ✓ (because it came from right)
- It's smaller than everything else in the RIGHT subtree ✓ (it was the minimum there)
- BST property is maintained ✓

You can alternatively use the **inorder predecessor** (largest in left subtree) — same logic applies.

**Visual for all three cases**:

```
CASE 1 — Delete LEAF node (delete 7):
─────────────────────────────────────
    8                    8
   / \                  / \
  3   10      →        3   10
 / \    \             / \    \
1   6   14           1   6   14
   / \  /               /   /
  4  [7] 13             4   13
         ↑ DELETE

CASE 2 — Delete node with ONE child (delete 10):
──────────────────────────────────────────────────
    8                    8
   / \                  / \
  3   10      →        3   14
 / \    \             / \  /
1   6   14           1   6 13
   / \  /               / \
  4   7 13             4   7
        ↑ 10 has only right child (14), so 14 replaces 10

CASE 3 — Delete node with TWO children (delete 3):
────────────────────────────────────────────────────
    8                    8
   / \                  / \
  3   10      →       [4]  10
 / \    \             / \    \
1   6   14           1   6   14
   / \  /               / \  /
  4   7 13              ✗  7 13
  ↑
  Inorder successor of 3 = 4 (smallest in right subtree of 3)
  1. Copy 4's value into node 3's position
  2. Delete node 4 (it's a leaf → Case 1)
```

**Delete Algorithm Full Decision Tree**:
```
                    DELETE(value V)
                          │
                          ▼
                  ┌──────────────┐
                  │ node = NULL? │ → return NULL (not found)
                  └──────┬───────┘
                     NO  │
                         ▼
              ┌────────────────────┐
              │   V < node.val?    │ → recurse LEFT
              └────────┬───────────┘
                   NO  │
                        ▼
              ┌────────────────────┐
              │   V > node.val?    │ → recurse RIGHT
              └────────┬───────────┘
                   NO  │ (V == node.val → FOUND, delete this node)
                        ▼
              ┌─────────────────────────────┐
              │  node has TWO children?     │
              └────────────┬────────────────┘
                    YES    │    NO
                     │     │
                     ▼     ▼
              Find INORDER  ┌──────────────────────┐
              SUCCESSOR     │  node has ONE child?  │
              (min of right │  or ZERO children?    │
               subtree)     └──────┬────────────────┘
                     │        ONE  │  ZERO
                     │         │   │
                     ▼         ▼   ▼
              Copy successor  Return  Return
              val into node   the     NULL
              Delete successor child
```

---

### 7.4 Find Minimum and Maximum

**Concept**: In a BST, the minimum is always the LEFTMOST node, and the maximum is always the RIGHTMOST node.

**Why?** By the BST property, every left child is smaller. Keep going left until you can't — that's the minimum. Mirror logic for maximum.

```
Find MIN:                       Find MAX:
─────────                       ─────────
Start at ROOT                   Start at ROOT
   │                               │
   ▼                               ▼
While LEFT exists:             While RIGHT exists:
   go LEFT                        go RIGHT
   │                               │
   ▼                               ▼
Return current node            Return current node
(leftmost = minimum)           (rightmost = maximum)

Visual trace on our tree:
         8
        / \
       3   10
      / \    \
     1   6   14   ← MIN=1 (go left: 8→3→1, no more left)
        / \  /      MAX=14 (go right: 8→10→14, no more right)
       4   7 13
```

---

### 7.5 Successor and Predecessor

**SUCCESSOR** = The node with the NEXT LARGER value (immediately after in sorted order).
**PREDECESSOR** = The node with the NEXT SMALLER value (immediately before in sorted order).

**Why do we need these?** Critical for delete (Case 3), range queries, sorted iteration.

**Finding Successor — Two Scenarios**:

```
SCENARIO A: Node has a RIGHT subtree
────────────────────────────────────
Successor = MINIMUM of the right subtree
(The smallest node to the right is the next larger value)

Example: Successor of 3 in this tree:
         8
        / \
      [3]  10
      / \
     1   6
        / \
       4   7

3 has right subtree {6,4,7}.
Min of right subtree = 4.
Successor of 3 = 4 ✓  (sequence: ...3, 4, 6, 7, 8, 10...)

SCENARIO B: Node has NO right subtree
──────────────────────────────────────
Successor = The lowest ANCESTOR for which the node is in the LEFT subtree
(We need to find the first ancestor we came from by going left)

Example: Successor of 7:
         8
        / \
       3   10
      / \
     1   6
        / \
       4  [7]

7 has no right child.
Walk up: 7→6 (7 is RIGHT child of 6, keep going)
         6→3 (6 is RIGHT child of 3, keep going)
         3→8 (3 is LEFT child of 8 ← STOP)
Successor of 7 = 8 ✓  (sequence: ...4, 6, 7, 8, 10...)
```

**Finding Predecessor — Mirror Logic**:

```
SCENARIO A: Node has a LEFT subtree
→ Predecessor = MAXIMUM of the left subtree

SCENARIO B: Node has NO left subtree
→ Predecessor = The lowest ancestor for which the node is in the RIGHT subtree
```

---

### 7.6 Height and Depth

**Height of a node** = longest path from that node DOWN to a leaf.
**Depth of a node** = path from ROOT down to that node.

```
Height Calculation (recursive):
─────────────────────────────────
height(NULL) = -1   (empty tree convention)
height(node) = 1 + max(height(node.left), height(node.right))

Trace on tree:
         8                h(8) = 1 + max(h(3), h(10))
        / \                    = 1 + max(2, 2)
       3   10                  = 3
      / \    \
     1   6   14     h(3)  = 1 + max(h(1), h(6))  = 1 + max(0,1) = 2
        / \  /      h(10) = 1 + max(h(nil), h(14)) = 1 + max(-1,1) = 2
       4   7 13     h(6)  = 1 + max(h(4), h(7)) = 1 + max(0,0) = 1
                    h(1)  = 1 + max(-1,-1) = 0  (leaf)
                    h(14) = 1 + max(h(13), -1) = 1 + max(0,-1) = 1
                    h(4)  = 0  (leaf)
                    h(7)  = 0  (leaf)
                    h(13) = 0  (leaf)
```

---

### 7.7 Count Nodes

```
count(NULL) = 0
count(node) = 1 + count(node.left) + count(node.right)

This is a simple postorder traversal where you accumulate counts.
```

---

## 8. Tree Traversals — All Four Patterns

**Traversal** = visiting every node in a specific ORDER. The order matters enormously for what you can compute.

```
┌──────────────────────────────────────────────────────────────────┐
│           TRAVERSAL TYPES — OVERVIEW                              │
├──────────────────┬────────────────────────────────────────────────┤
│  Traversal       │  Visit Order                                   │
├──────────────────┼────────────────────────────────────────────────┤
│  Inorder (LNR)   │  Left → Node → Right                          │
│                  │  Gives SORTED output for BST                   │
├──────────────────┼────────────────────────────────────────────────┤
│  Preorder (NLR)  │  Node → Left → Right                          │
│                  │  Used to COPY/SERIALIZE a tree                 │
├──────────────────┼────────────────────────────────────────────────┤
│  Postorder (LRN) │  Left → Right → Node                          │
│                  │  Used to DELETE a tree, evaluate expressions   │
├──────────────────┼────────────────────────────────────────────────┤
│  Level Order     │  Level by level (BFS)                         │
│  (BFS)           │  Used for shortest path, tree structure        │
└──────────────────┴────────────────────────────────────────────────┘
```

### 8.1 Inorder (LNR)

**Output order for our tree**: 1, 3, 4, 6, 7, 8, 10, 13, 14 (SORTED! ← Critical property of BST)

```
Call Stack Visualization (Inorder of small tree: 4, 2, 5, 1, 3):

Tree:       4
           / \
          2   5
         / \
        1   3

Call: inorder(4)
  Call: inorder(2)
    Call: inorder(1)
      Call: inorder(nil) → return
      PRINT 1
      Call: inorder(nil) → return
    PRINT 2
    Call: inorder(3)
      Call: inorder(nil) → return
      PRINT 3
      Call: inorder(nil) → return
  PRINT 4
  Call: inorder(5)
    Call: inorder(nil) → return
    PRINT 5
    Call: inorder(nil) → return

Output: 1 2 3 4 5 ← SORTED
```

### 8.2 Preorder (NLR)

**Output**: 8, 3, 1, 6, 4, 7, 10, 14, 13

```
Used for: Serializing a tree (if you insert these values in this order
          into an empty BST, you reconstruct the SAME tree structure)

Call Stack (same tree as above):
Call: preorder(4)
  PRINT 4
  Call: preorder(2)
    PRINT 2
    Call: preorder(1) → PRINT 1
    Call: preorder(3) → PRINT 3
  Call: preorder(5) → PRINT 5

Output: 4 2 1 3 5
```

### 8.3 Postorder (LRN)

**Output**: 1, 4, 7, 6, 3, 13, 14, 10, 8

```
Used for: Deleting a tree safely (children before parents),
          expression tree evaluation (operators after operands)

Pattern: Process children FIRST, then the current node.
This is why it's used for deletion — you never delete a parent
before you've handled its children.
```

### 8.4 Level-Order (BFS)

**Output**: 8, 3, 10, 1, 6, 14, 4, 7, 13

Uses a **Queue** (FIFO data structure):

```
Level-Order Algorithm:
─────────────────────
1. Enqueue root
2. While queue is not empty:
   a. Dequeue front node
   b. VISIT (print) it
   c. Enqueue left child (if exists)
   d. Enqueue right child (if exists)

Trace:
Queue: [8]
Dequeue 8, print 8, enqueue 3 and 10.   Queue: [3, 10]
Dequeue 3, print 3, enqueue 1 and 6.    Queue: [10, 1, 6]
Dequeue 10, print 10, enqueue 14.       Queue: [1, 6, 14]
Dequeue 1, print 1, no children.        Queue: [6, 14]
Dequeue 6, print 6, enqueue 4 and 7.   Queue: [14, 4, 7]
Dequeue 14, print 14, enqueue 13.      Queue: [4, 7, 13]
Dequeue 4, print 4, no children.       Queue: [7, 13]
Dequeue 7, print 7, no children.       Queue: [13]
Dequeue 13, print 13, no children.     Queue: []

Output: 8 3 10 1 6 14 4 7 13  ← Level by level!
```

---

## 9. BST Validation

**Problem**: Given a tree, determine if it satisfies the BST property.

**The Wrong Approach** (common beginner mistake):
```
// WRONG: Only checking immediate children
func isValid(node) bool {
    if node.left != nil && node.left.val >= node.val { return false }
    if node.right != nil && node.right.val <= node.val { return false }
    return isValid(node.left) && isValid(node.right)
}

// FAILS for this invalid BST:
//      10
//     /  \
//    5    15
//        /
//       6   ← 6 < 10, but it's in right subtree!
//           Immediate parent check passes (6 < 15 ✓)
//           but global property violated (6 < 10 ✗)
```

**The Correct Approach — Range Propagation**:
```
Every node has a valid RANGE [min, max].
Pass down the allowed range through recursion.

         8            range for 8: (-∞, +∞)
        / \
       3   10         range for 3:  (-∞, 8)
      / \    \        range for 10: (8, +∞)
     1   6   14       range for 1:  (-∞, 3)
        / \  /        range for 6:  (3, 8)
       4   7 13       range for 14: (10, +∞)
                      range for 4:  (3, 6)
                      range for 7:  (6, 8)
                      range for 13: (10, 14)

Algorithm:
isValid(node, min=-∞, max=+∞):
  if node == NULL: return true
  if node.val <= min OR node.val >= max: return false
  return isValid(node.left, min, node.val)   ← left must be < current
      && isValid(node.right, node.val, max)  ← right must be > current
```

---

## 10. Balanced vs Unbalanced BST

**Balance Factor** of a node = height(left subtree) - height(right subtree)

```
BALANCED BST:                     UNBALANCED (Skewed) BST:
─────────────                     ────────────────────────
        8                         1
       / \                         \
      3   10                        2
     / \    \                        \
    1   6   14                        3
       / \  /                          \
      4   7 13                          4
                                         \
                                          5
Height = 3, n = 9                 Height = 4, n = 5
Search: O(log 9) ≈ O(3)          Search: O(5) = O(n)

Inserting 1,2,3,4,5 in ORDER creates the worst case!
Inserting the MEDIAN first creates the best case.

WHY THIS MATTERS:
If data comes sorted (very common in real world!), a plain BST
degrades to O(n) for all operations — no better than a linked list!
This is why Self-Balancing BSTs (AVL, Red-Black) exist.
```

**Balance Analysis**:
```
┌────────────────────────────────────────────────────────────┐
│           Height vs Number of Nodes                         │
├────────────────┬────────────────────────────────────────────┤
│  Tree Type     │  Height                                    │
├────────────────┼────────────────────────────────────────────┤
│  Best (full)   │  ⌊log₂(n)⌋                               │
│  Average       │  O(log n) (random insertions)             │
│  Worst         │  O(n) (sorted insertion)                  │
└────────────────┴────────────────────────────────────────────┘
```

---

## 11. Time and Space Complexity Analysis

```
┌───────────────────────────────────────────────────────────────┐
│              BST COMPLEXITY TABLE                              │
├─────────────────┬────────────────┬────────────────────────────┤
│   Operation     │   Average Case │   Worst Case               │
│                 │   (balanced)   │   (skewed/degenerate)      │
├─────────────────┼────────────────┼────────────────────────────┤
│   Search        │   O(log n)     │   O(n)                     │
│   Insert        │   O(log n)     │   O(n)                     │
│   Delete        │   O(log n)     │   O(n)                     │
│   Find Min/Max  │   O(log n)     │   O(n)                     │
│   Successor     │   O(log n)     │   O(n)                     │
│   Inorder       │   O(n)         │   O(n)                     │
│   Height        │   O(n)         │   O(n)                     │
│   Validate      │   O(n)         │   O(n)                     │
├─────────────────┼────────────────┼────────────────────────────┤
│   SPACE (tree)  │   O(n)         │   O(n)                     │
│   SPACE (stack) │   O(log n)     │   O(n)  ← recursion depth │
│   for recursion │                │                            │
└─────────────────┴────────────────┴────────────────────────────┘

KEY INSIGHT:
The SPACE complexity of recursive algorithms depends on the
CALL STACK DEPTH, which equals the tree HEIGHT.
- Balanced BST: O(log n) stack frames
- Skewed BST:   O(n) stack frames → potential stack overflow!

This is why iterative implementations matter for production code.
```

---

## 12. Complete Implementations

---

### Go Implementation

```go
// bst.go — Complete Binary Search Tree in Go
// Idiomatic Go: methods on structs, error handling, no exceptions

package bst

import (
    "fmt"
    "math"
)

// ─────────────────────────────────────────────
// NODE STRUCTURE
// ─────────────────────────────────────────────

// Node represents a single BST node.
// Go uses pointer types for nullable references.
type Node struct {
    Val   int
    Left  *Node
    Right *Node
}

// BST is the wrapper holding the root reference.
type BST struct {
    Root *Node
    size int
}

// newNode creates and returns a heap-allocated node.
func newNode(val int) *Node {
    return &Node{Val: val}
}

// ─────────────────────────────────────────────
// SEARCH
// ─────────────────────────────────────────────

// Search returns the node with the given value, or nil if not found.
// Iterative — avoids call stack overflow on deep trees.
func (b *BST) Search(val int) *Node {
    current := b.Root
    for current != nil {
        if val == current.Val {
            return current
        } else if val < current.Val {
            current = current.Left
        } else {
            current = current.Right
        }
    }
    return nil
}

// SearchRecursive demonstrates the recursive approach for clarity.
func searchRecursive(node *Node, val int) *Node {
    if node == nil || node.Val == val {
        return node
    }
    if val < node.Val {
        return searchRecursive(node.Left, val)
    }
    return searchRecursive(node.Right, val)
}

// ─────────────────────────────────────────────
// INSERT
// ─────────────────────────────────────────────

// Insert adds a value to the BST. Ignores duplicates.
// Uses the recursive helper pattern common in Go BST code.
func (b *BST) Insert(val int) {
    b.Root = insertNode(b.Root, val)
    b.size++
}

// insertNode is the recursive helper.
// Returning *Node lets us wire parent pointers cleanly.
func insertNode(node *Node, val int) *Node {
    // Base case: found the spot, create and return new node
    if node == nil {
        return newNode(val)
    }
    if val < node.Val {
        node.Left = insertNode(node.Left, val)
    } else if val > node.Val {
        node.Right = insertNode(node.Right, val)
    }
    // val == node.Val: duplicate, do nothing
    return node
}

// ─────────────────────────────────────────────
// DELETE
// ─────────────────────────────────────────────

// Delete removes a value from the BST if it exists.
func (b *BST) Delete(val int) {
    b.Root = deleteNode(b.Root, val)
}

// deleteNode handles all three deletion cases.
func deleteNode(node *Node, val int) *Node {
    if node == nil {
        return nil // Value not found
    }

    if val < node.Val {
        // Target is in the left subtree
        node.Left = deleteNode(node.Left, val)
    } else if val > node.Val {
        // Target is in the right subtree
        node.Right = deleteNode(node.Right, val)
    } else {
        // FOUND the node to delete

        // Case 1: No children (leaf) — return nil to parent
        // Case 2: One child — return the existing child to parent
        if node.Left == nil {
            return node.Right // covers both Case 1 and right-only Case 2
        }
        if node.Right == nil {
            return node.Left // left-only Case 2
        }

        // Case 3: Two children
        // Find inorder successor (minimum of right subtree)
        successor := findMin(node.Right)
        // Copy successor's value into current node
        node.Val = successor.Val
        // Delete the successor from right subtree
        // Successor has at most ONE child (no left child, since it's minimum)
        node.Right = deleteNode(node.Right, successor.Val)
    }
    return node
}

// ─────────────────────────────────────────────
// MIN / MAX
// ─────────────────────────────────────────────

// FindMin returns the minimum value in the BST.
func (b *BST) FindMin() (int, bool) {
    if b.Root == nil {
        return 0, false
    }
    return findMin(b.Root).Val, true
}

// findMin is the internal helper — goes leftmost.
func findMin(node *Node) *Node {
    current := node
    for current.Left != nil {
        current = current.Left
    }
    return current
}

// FindMax returns the maximum value in the BST.
func (b *BST) FindMax() (int, bool) {
    if b.Root == nil {
        return 0, false
    }
    current := b.Root
    for current.Right != nil {
        current = current.Right
    }
    return current.Val, true
}

// ─────────────────────────────────────────────
// SUCCESSOR & PREDECESSOR
// ─────────────────────────────────────────────

// Successor returns the inorder successor of the given value.
// Returns (successor_value, found bool).
func (b *BST) Successor(val int) (int, bool) {
    var successor *Node
    current := b.Root

    for current != nil {
        if val < current.Val {
            // current could be the successor; record it and go left
            successor = current
            current = current.Left
        } else if val > current.Val {
            current = current.Right
        } else {
            // Found the node
            if current.Right != nil {
                // Case A: has right subtree → min of right subtree
                return findMin(current.Right).Val, true
            }
            // Case B: no right subtree → last recorded ancestor when going left
            break
        }
    }

    if successor != nil {
        return successor.Val, true
    }
    return 0, false
}

// Predecessor returns the inorder predecessor of the given value.
func (b *BST) Predecessor(val int) (int, bool) {
    var predecessor *Node
    current := b.Root

    for current != nil {
        if val > current.Val {
            // current could be the predecessor; record it and go right
            predecessor = current
            current = current.Right
        } else if val < current.Val {
            current = current.Left
        } else {
            // Found the node
            if current.Left != nil {
                // Has left subtree → max of left subtree
                node := current.Left
                for node.Right != nil {
                    node = node.Right
                }
                return node.Val, true
            }
            break
        }
    }

    if predecessor != nil {
        return predecessor.Val, true
    }
    return 0, false
}

// ─────────────────────────────────────────────
// HEIGHT & COUNT
// ─────────────────────────────────────────────

// Height returns the height of the BST (-1 for empty tree).
func (b *BST) Height() int {
    return height(b.Root)
}

func height(node *Node) int {
    if node == nil {
        return -1
    }
    leftH := height(node.Left)
    rightH := height(node.Right)
    if leftH > rightH {
        return 1 + leftH
    }
    return 1 + rightH
}

// Count returns the number of nodes in the BST.
func (b *BST) Count() int {
    return countNodes(b.Root)
}

func countNodes(node *Node) int {
    if node == nil {
        return 0
    }
    return 1 + countNodes(node.Left) + countNodes(node.Right)
}

// ─────────────────────────────────────────────
// TRAVERSALS
// ─────────────────────────────────────────────

// InOrder visits nodes in sorted order (Left → Node → Right).
// Uses a function callback — idiomatic Go for traversals.
func (b *BST) InOrder(visit func(int)) {
    inOrder(b.Root, visit)
}

func inOrder(node *Node, visit func(int)) {
    if node == nil {
        return
    }
    inOrder(node.Left, visit)
    visit(node.Val)
    inOrder(node.Right, visit)
}

// PreOrder visits Node → Left → Right.
func (b *BST) PreOrder(visit func(int)) {
    preOrder(b.Root, visit)
}

func preOrder(node *Node, visit func(int)) {
    if node == nil {
        return
    }
    visit(node.Val)
    preOrder(node.Left, visit)
    preOrder(node.Right, visit)
}

// PostOrder visits Left → Right → Node.
func (b *BST) PostOrder(visit func(int)) {
    postOrder(b.Root, visit)
}

func postOrder(node *Node, visit func(int)) {
    if node == nil {
        return
    }
    postOrder(node.Left, visit)
    postOrder(node.Right, visit)
    visit(node.Val)
}

// LevelOrder performs BFS traversal using a queue (slice as queue in Go).
func (b *BST) LevelOrder(visit func(int)) {
    if b.Root == nil {
        return
    }
    queue := []*Node{b.Root}
    for len(queue) > 0 {
        node := queue[0]
        queue = queue[1:] // dequeue front
        visit(node.Val)
        if node.Left != nil {
            queue = append(queue, node.Left)
        }
        if node.Right != nil {
            queue = append(queue, node.Right)
        }
    }
}

// ─────────────────────────────────────────────
// VALIDATION
// ─────────────────────────────────────────────

// IsValid checks whether the tree satisfies the BST property.
func (b *BST) IsValid() bool {
    return isValidBST(b.Root, math.MinInt64, math.MaxInt64)
}

// isValidBST propagates valid [min, max] ranges down the tree.
func isValidBST(node *Node, min, max int) bool {
    if node == nil {
        return true
    }
    if node.Val <= min || node.Val >= max {
        return false
    }
    return isValidBST(node.Left, min, node.Val) &&
        isValidBST(node.Right, node.Val, max)
}

// ─────────────────────────────────────────────
// DISPLAY UTILITY
// ─────────────────────────────────────────────

// PrintSorted prints all values in sorted order.
func (b *BST) PrintSorted() {
    b.InOrder(func(val int) {
        fmt.Printf("%d ", val)
    })
    fmt.Println()
}

// ─────────────────────────────────────────────
// MAIN DEMO
// ─────────────────────────────────────────────

func main() {
    tree := &BST{}

    // Insert values
    for _, v := range []int{8, 3, 10, 1, 6, 14, 4, 7, 13} {
        tree.Insert(v)
    }

    fmt.Print("InOrder (sorted):  ") // Expected: 1 3 4 6 7 8 10 13 14
    tree.PrintSorted()

    fmt.Print("PreOrder:          ")
    tree.PreOrder(func(v int) { fmt.Printf("%d ", v) })
    fmt.Println()

    fmt.Print("PostOrder:         ")
    tree.PostOrder(func(v int) { fmt.Printf("%d ", v) })
    fmt.Println()

    fmt.Print("LevelOrder:        ")
    tree.LevelOrder(func(v int) { fmt.Printf("%d ", v) })
    fmt.Println()

    fmt.Printf("Height:            %d\n", tree.Height())
    fmt.Printf("Count:             %d\n", tree.Count())
    fmt.Printf("Is Valid BST:      %v\n", tree.IsValid())

    if min, ok := tree.FindMin(); ok {
        fmt.Printf("Min:               %d\n", min)
    }
    if max, ok := tree.FindMax(); ok {
        fmt.Printf("Max:               %d\n", max)
    }

    if succ, ok := tree.Successor(6); ok {
        fmt.Printf("Successor of 6:    %d\n", succ) // Expected: 7
    }
    if pred, ok := tree.Predecessor(6); ok {
        fmt.Printf("Predecessor of 6:  %d\n", pred) // Expected: 4
    }

    // Delete demonstrations
    fmt.Println("\n--- Deletions ---")
    tree.Delete(7)  // Case 1: leaf
    fmt.Print("After deleting 7:  ") ; tree.PrintSorted()

    tree.Delete(10) // Case 2: one child
    fmt.Print("After deleting 10: ") ; tree.PrintSorted()

    tree.Delete(3)  // Case 3: two children
    fmt.Print("After deleting 3:  ") ; tree.PrintSorted()

    fmt.Printf("Search 6: %v\n", tree.Search(6) != nil) // true
    fmt.Printf("Search 3: %v\n", tree.Search(3) != nil) // false (deleted)
}
```

---

### C Implementation

```c
/* bst.c — Complete Binary Search Tree in C
 * Memory-safe patterns, explicit malloc/free,
 * NULL-pointer discipline throughout.
 */

#include <stdio.h>
#include <stdlib.h>
#include <limits.h>
#include <stdbool.h>

/* ─────────────────────────────────────────────
 * NODE STRUCTURE
 * ───────────────────────────────────────────── */

typedef struct Node {
    int val;
    struct Node *left;
    struct Node *right;
} Node;

/* ─────────────────────────────────────────────
 * NODE CREATION
 * ───────────────────────────────────────────── */

Node *new_node(int val) {
    Node *node = (Node *)malloc(sizeof(Node));
    if (!node) {
        fprintf(stderr, "Fatal: malloc failed\n");
        exit(EXIT_FAILURE);
    }
    node->val   = val;
    node->left  = NULL;
    node->right = NULL;
    return node;
}

/* ─────────────────────────────────────────────
 * SEARCH — Iterative O(h)
 * ───────────────────────────────────────────── */

Node *search(Node *root, int val) {
    Node *current = root;
    while (current != NULL) {
        if (val == current->val) return current;
        else if (val < current->val) current = current->left;
        else                          current = current->right;
    }
    return NULL; /* not found */
}

/* ─────────────────────────────────────────────
 * INSERT — Recursive, returns new root
 * ───────────────────────────────────────────── */

Node *insert(Node *node, int val) {
    if (node == NULL) return new_node(val); /* base case */

    if (val < node->val)
        node->left  = insert(node->left,  val);
    else if (val > node->val)
        node->right = insert(node->right, val);
    /* duplicate: do nothing */

    return node;
}

/* ─────────────────────────────────────────────
 * FIND MINIMUM — leftmost node
 * ───────────────────────────────────────────── */

Node *find_min(Node *node) {
    if (node == NULL) return NULL;
    while (node->left != NULL)
        node = node->left;
    return node;
}

/* ─────────────────────────────────────────────
 * FIND MAXIMUM — rightmost node
 * ───────────────────────────────────────────── */

Node *find_max(Node *node) {
    if (node == NULL) return NULL;
    while (node->right != NULL)
        node = node->right;
    return node;
}

/* ─────────────────────────────────────────────
 * DELETE — handles all 3 cases
 * ───────────────────────────────────────────── */

Node *delete_node(Node *node, int val) {
    if (node == NULL) return NULL; /* value not in tree */

    if (val < node->val) {
        node->left  = delete_node(node->left,  val);
    } else if (val > node->val) {
        node->right = delete_node(node->right, val);
    } else {
        /* Found node to delete */

        /* Case 1 & 2: zero or one child */
        if (node->left == NULL) {
            Node *temp = node->right;
            free(node);          /* C requires manual deallocation! */
            return temp;
        }
        if (node->right == NULL) {
            Node *temp = node->left;
            free(node);
            return temp;
        }

        /* Case 3: two children
         * Find inorder successor (min of right subtree) */
        Node *successor = find_min(node->right);

        /* Copy successor's value */
        node->val = successor->val;

        /* Delete the successor from right subtree
         * Successor has no left child (it was the min),
         * so this will hit Case 1 or 2 above */
        node->right = delete_node(node->right, successor->val);
    }
    return node;
}

/* ─────────────────────────────────────────────
 * TRAVERSALS
 * ───────────────────────────────────────────── */

void inorder(Node *node) {
    if (node == NULL) return;
    inorder(node->left);
    printf("%d ", node->val);
    inorder(node->right);
}

void preorder(Node *node) {
    if (node == NULL) return;
    printf("%d ", node->val);
    preorder(node->left);
    preorder(node->right);
}

void postorder(Node *node) {
    if (node == NULL) return;
    postorder(node->left);
    postorder(node->right);
    printf("%d ", node->val);
}

/* Level-order (BFS) — requires a queue.
 * We use a simple array-based circular queue here. */
#define MAX_QUEUE 1024

void level_order(Node *root) {
    if (root == NULL) return;

    Node *queue[MAX_QUEUE];
    int  head = 0, tail = 0;

    queue[tail++] = root;

    while (head != tail) {
        Node *current = queue[head++];
        printf("%d ", current->val);

        if (current->left  != NULL) queue[tail++] = current->left;
        if (current->right != NULL) queue[tail++] = current->right;
    }
    printf("\n");
}

/* ─────────────────────────────────────────────
 * HEIGHT
 * ───────────────────────────────────────────── */

int height(Node *node) {
    if (node == NULL) return -1;
    int lh = height(node->left);
    int rh = height(node->right);
    return 1 + (lh > rh ? lh : rh);
}

/* ─────────────────────────────────────────────
 * COUNT
 * ───────────────────────────────────────────── */

int count_nodes(Node *node) {
    if (node == NULL) return 0;
    return 1 + count_nodes(node->left) + count_nodes(node->right);
}

/* ─────────────────────────────────────────────
 * VALIDATION — range propagation
 * ───────────────────────────────────────────── */

bool is_valid_bst_helper(Node *node, long min, long max) {
    if (node == NULL) return true;
    if ((long)node->val <= min || (long)node->val >= max) return false;
    return is_valid_bst_helper(node->left,  min,           (long)node->val) &&
           is_valid_bst_helper(node->right, (long)node->val, max);
}

bool is_valid_bst(Node *root) {
    return is_valid_bst_helper(root, (long)INT_MIN - 1, (long)INT_MAX + 1);
}

/* ─────────────────────────────────────────────
 * SUCCESSOR
 * ───────────────────────────────────────────── */

Node *successor(Node *root, int val) {
    Node *succ    = NULL;
    Node *current = root;

    while (current != NULL) {
        if (val < current->val) {
            succ    = current;     /* record potential successor */
            current = current->left;
        } else if (val > current->val) {
            current = current->right;
        } else {
            /* Found the node */
            if (current->right != NULL) {
                return find_min(current->right); /* Case A */
            }
            break; /* Case B: use recorded ancestor */
        }
    }
    return succ; /* NULL if no successor */
}

/* ─────────────────────────────────────────────
 * PREDECESSOR
 * ───────────────────────────────────────────── */

Node *predecessor(Node *root, int val) {
    Node *pred    = NULL;
    Node *current = root;

    while (current != NULL) {
        if (val > current->val) {
            pred    = current;
            current = current->right;
        } else if (val < current->val) {
            current = current->left;
        } else {
            if (current->left != NULL) {
                return find_max(current->left);
            }
            break;
        }
    }
    return pred;
}

/* ─────────────────────────────────────────────
 * FREE ENTIRE TREE — postorder to avoid use-after-free
 * ───────────────────────────────────────────── */

void free_tree(Node *node) {
    if (node == NULL) return;
    free_tree(node->left);
    free_tree(node->right);
    free(node); /* free children before parent */
}

/* ─────────────────────────────────────────────
 * MAIN DEMO
 * ───────────────────────────────────────────── */

int main(void) {
    Node *root = NULL;

    int values[] = {8, 3, 10, 1, 6, 14, 4, 7, 13};
    int n = sizeof(values) / sizeof(values[0]);

    for (int i = 0; i < n; i++) {
        root = insert(root, values[i]);
    }

    printf("InOrder (sorted):  "); inorder(root);   printf("\n");
    printf("PreOrder:          "); preorder(root);  printf("\n");
    printf("PostOrder:         "); postorder(root); printf("\n");
    printf("LevelOrder:        "); level_order(root);

    printf("Height:            %d\n",    height(root));
    printf("Count:             %d\n",    count_nodes(root));
    printf("Is Valid BST:      %s\n",    is_valid_bst(root) ? "true" : "false");

    Node *min_node = find_min(root);
    Node *max_node = find_max(root);
    if (min_node) printf("Min:               %d\n", min_node->val);
    if (max_node) printf("Max:               %d\n", max_node->val);

    Node *succ6 = successor(root, 6);
    Node *pred6 = predecessor(root, 6);
    if (succ6) printf("Successor of 6:    %d\n", succ6->val);
    if (pred6) printf("Predecessor of 6:  %d\n", pred6->val);

    /* Deletions */
    printf("\n--- Deletions ---\n");
    root = delete_node(root, 7);  /* leaf */
    printf("After deleting 7:  "); inorder(root); printf("\n");

    root = delete_node(root, 10); /* one child */
    printf("After deleting 10: "); inorder(root); printf("\n");

    root = delete_node(root, 3);  /* two children */
    printf("After deleting 3:  "); inorder(root); printf("\n");

    printf("Search 6: %s\n", search(root, 6) ? "found" : "not found");
    printf("Search 3: %s\n", search(root, 3) ? "found" : "not found");

    /* CRITICAL in C: always free your memory */
    free_tree(root);
    return 0;
}
```

---

### Rust Implementation

```rust
// bst.rs — Complete Binary Search Tree in Rust
//
// Rust's ownership model transforms BST implementation:
// • Box<T>        = heap-allocated, owned pointer (replaces raw pointer)
// • Option<Box<T>>= nullable node (None = null, Some(box) = valid node)
// • No garbage collector — ownership rules ensure memory safety at compile time
//
// Key Rust philosophy demonstrated here:
// • Ownership and borrowing prevent use-after-free, double-free
// • Pattern matching on Option is exhaustive (compiler enforces null checks)
// • No manual malloc/free — Drop trait handles deallocation automatically

use std::cmp::Ordering;
use std::collections::VecDeque; // for level-order BFS

// ─────────────────────────────────────────────
// NODE STRUCTURE
// ─────────────────────────────────────────────

/// A BST node owning its value and optionally its children.
/// Box<Node> = heap allocation; Option = nullable.
#[derive(Debug)]
pub struct Node {
    pub val:   i64,
    pub left:  Option<Box<Node>>,
    pub right: Option<Box<Node>>,
}

impl Node {
    /// Creates a new leaf node on the heap.
    pub fn new(val: i64) -> Box<Node> {
        Box::new(Node { val, left: None, right: None })
    }
}

// ─────────────────────────────────────────────
// BST WRAPPER
// ─────────────────────────────────────────────

#[derive(Debug, Default)]
pub struct BST {
    root: Option<Box<Node>>,
}

impl BST {
    pub fn new() -> Self {
        BST { root: None }
    }

    // ─────────────────────────────────────────────
    // SEARCH — iterative
    // ─────────────────────────────────────────────

    /// Returns true if val exists in the BST.
    /// We borrow the tree (& self) — no ownership transfer.
    pub fn search(&self, val: i64) -> bool {
        let mut current = self.root.as_deref(); // Option<&Node>
        while let Some(node) = current {
            match val.cmp(&node.val) {
                Ordering::Equal   => return true,
                Ordering::Less    => current = node.left.as_deref(),
                Ordering::Greater => current = node.right.as_deref(),
            }
        }
        false
    }

    // ─────────────────────────────────────────────
    // INSERT
    // ─────────────────────────────────────────────

    /// Inserts val into the BST. Duplicates are ignored.
    pub fn insert(&mut self, val: i64) {
        // We use a helper that takes Option<Box<Node>> by value,
        // allowing recursive reconstruction of the tree.
        self.root = Self::insert_node(self.root.take(), val);
    }

    fn insert_node(node: Option<Box<Node>>, val: i64) -> Option<Box<Node>> {
        match node {
            // Base case: empty spot — create new node here
            None => Some(Node::new(val)),

            Some(mut n) => {
                match val.cmp(&n.val) {
                    Ordering::Less    => n.left  = Self::insert_node(n.left.take(),  val),
                    Ordering::Greater => n.right = Self::insert_node(n.right.take(), val),
                    Ordering::Equal   => {} // duplicate, no-op
                }
                Some(n) // return the node back up the chain
            }
        }
    }

    // ─────────────────────────────────────────────
    // DELETE
    // ─────────────────────────────────────────────

    /// Deletes val from the BST if it exists.
    pub fn delete(&mut self, val: i64) {
        self.root = Self::delete_node(self.root.take(), val);
    }

    fn delete_node(node: Option<Box<Node>>, val: i64) -> Option<Box<Node>> {
        match node {
            None => None, // value not found

            Some(mut n) => match val.cmp(&n.val) {
                Ordering::Less => {
                    n.left = Self::delete_node(n.left.take(), val);
                    Some(n)
                }
                Ordering::Greater => {
                    n.right = Self::delete_node(n.right.take(), val);
                    Some(n)
                }
                Ordering::Equal => {
                    // Found the node to delete
                    match (n.left.take(), n.right.take()) {
                        // Case 1: No children → return None (remove node)
                        (None, None) => None,

                        // Case 2a: Only right child → replace with right child
                        (None, right) => right,

                        // Case 2b: Only left child → replace with left child
                        (left, None) => left,

                        // Case 3: Two children
                        // Find inorder successor (min of right subtree)
                        // Copy successor val, delete successor from right
                        (left, right) => {
                            let successor_val = Self::find_min_val(right.as_deref().unwrap());
                            n.val   = successor_val;
                            n.left  = left;
                            n.right = Self::delete_node(right, successor_val);
                            Some(n)
                        }
                    }
                }
            }
        }
    }

    // ─────────────────────────────────────────────
    // MIN / MAX
    // ─────────────────────────────────────────────

    /// Returns the minimum value in the BST.
    pub fn find_min(&self) -> Option<i64> {
        self.root.as_deref().map(Self::find_min_val)
    }

    fn find_min_val(mut node: &Node) -> i64 {
        while let Some(left) = node.left.as_deref() {
            node = left;
        }
        node.val
    }

    /// Returns the maximum value in the BST.
    pub fn find_max(&self) -> Option<i64> {
        let mut current = self.root.as_deref()?;
        while let Some(right) = current.right.as_deref() {
            current = right;
        }
        Some(current.val)
    }

    // ─────────────────────────────────────────────
    // SUCCESSOR & PREDECESSOR
    // ─────────────────────────────────────────────

    pub fn successor(&self, val: i64) -> Option<i64> {
        let mut succ: Option<i64> = None;
        let mut current = self.root.as_deref();

        while let Some(node) = current {
            match val.cmp(&node.val) {
                Ordering::Less => {
                    succ = Some(node.val); // record candidate
                    current = node.left.as_deref();
                }
                Ordering::Greater => {
                    current = node.right.as_deref();
                }
                Ordering::Equal => {
                    if let Some(right) = node.right.as_deref() {
                        return Some(Self::find_min_val(right));
                    }
                    break;
                }
            }
        }
        succ
    }

    pub fn predecessor(&self, val: i64) -> Option<i64> {
        let mut pred: Option<i64> = None;
        let mut current = self.root.as_deref();

        while let Some(node) = current {
            match val.cmp(&node.val) {
                Ordering::Greater => {
                    pred = Some(node.val);
                    current = node.right.as_deref();
                }
                Ordering::Less => {
                    current = node.left.as_deref();
                }
                Ordering::Equal => {
                    if node.left.is_some() {
                        let mut n = node.left.as_deref().unwrap();
                        while let Some(r) = n.right.as_deref() { n = r; }
                        return Some(n.val);
                    }
                    break;
                }
            }
        }
        pred
    }

    // ─────────────────────────────────────────────
    // HEIGHT & COUNT
    // ─────────────────────────────────────────────

    pub fn height(&self) -> i32 {
        Self::node_height(self.root.as_deref())
    }

    fn node_height(node: Option<&Node>) -> i32 {
        match node {
            None => -1,
            Some(n) => {
                let lh = Self::node_height(n.left.as_deref());
                let rh = Self::node_height(n.right.as_deref());
                1 + lh.max(rh)
            }
        }
    }

    pub fn count(&self) -> usize {
        Self::count_nodes(self.root.as_deref())
    }

    fn count_nodes(node: Option<&Node>) -> usize {
        match node {
            None    => 0,
            Some(n) => 1 + Self::count_nodes(n.left.as_deref())
                         + Self::count_nodes(n.right.as_deref()),
        }
    }

    // ─────────────────────────────────────────────
    // TRAVERSALS
    // ─────────────────────────────────────────────

    /// Inorder traversal — returns sorted vec.
    pub fn inorder(&self) -> Vec<i64> {
        let mut result = Vec::new();
        Self::inorder_helper(self.root.as_deref(), &mut result);
        result
    }

    fn inorder_helper(node: Option<&Node>, result: &mut Vec<i64>) {
        if let Some(n) = node {
            Self::inorder_helper(n.left.as_deref(),  result);
            result.push(n.val);
            Self::inorder_helper(n.right.as_deref(), result);
        }
    }

    /// Preorder traversal.
    pub fn preorder(&self) -> Vec<i64> {
        let mut result = Vec::new();
        Self::preorder_helper(self.root.as_deref(), &mut result);
        result
    }

    fn preorder_helper(node: Option<&Node>, result: &mut Vec<i64>) {
        if let Some(n) = node {
            result.push(n.val);
            Self::preorder_helper(n.left.as_deref(),  result);
            Self::preorder_helper(n.right.as_deref(), result);
        }
    }

    /// Postorder traversal.
    pub fn postorder(&self) -> Vec<i64> {
        let mut result = Vec::new();
        Self::postorder_helper(self.root.as_deref(), &mut result);
        result
    }

    fn postorder_helper(node: Option<&Node>, result: &mut Vec<i64>) {
        if let Some(n) = node {
            Self::postorder_helper(n.left.as_deref(),  result);
            Self::postorder_helper(n.right.as_deref(), result);
            result.push(n.val);
        }
    }

    /// Level-order (BFS) traversal using VecDeque.
    pub fn level_order(&self) -> Vec<i64> {
        let mut result = Vec::new();
        if self.root.is_none() { return result; }

        let mut queue: VecDeque<&Node> = VecDeque::new();
        queue.push_back(self.root.as_deref().unwrap());

        while let Some(node) = queue.pop_front() {
            result.push(node.val);
            if let Some(left)  = node.left.as_deref()  { queue.push_back(left);  }
            if let Some(right) = node.right.as_deref() { queue.push_back(right); }
        }
        result
    }

    // ─────────────────────────────────────────────
    // VALIDATION
    // ─────────────────────────────────────────────

    pub fn is_valid(&self) -> bool {
        Self::is_valid_helper(self.root.as_deref(), i64::MIN, i64::MAX)
    }

    fn is_valid_helper(node: Option<&Node>, min: i64, max: i64) -> bool {
        match node {
            None    => true,
            Some(n) => {
                if n.val <= min || n.val >= max { return false; }
                Self::is_valid_helper(n.left.as_deref(),  min,    n.val) &&
                Self::is_valid_helper(n.right.as_deref(), n.val,  max)
            }
        }
    }
}

// ─────────────────────────────────────────────
// MAIN DEMO
// ─────────────────────────────────────────────

fn main() {
    let mut tree = BST::new();

    for &v in &[8i64, 3, 10, 1, 6, 14, 4, 7, 13] {
        tree.insert(v);
    }

    println!("InOrder (sorted):  {:?}", tree.inorder());
    println!("PreOrder:          {:?}", tree.preorder());
    println!("PostOrder:         {:?}", tree.postorder());
    println!("LevelOrder:        {:?}", tree.level_order());
    println!("Height:            {}", tree.height());
    println!("Count:             {}", tree.count());
    println!("Is Valid BST:      {}", tree.is_valid());
    println!("Min:               {:?}", tree.find_min());
    println!("Max:               {:?}", tree.find_max());
    println!("Successor of 6:    {:?}", tree.successor(6));   // Some(7)
    println!("Predecessor of 6:  {:?}", tree.predecessor(6)); // Some(4)

    println!("\n--- Deletions ---");
    tree.delete(7);  // leaf
    println!("After deleting 7:  {:?}", tree.inorder());

    tree.delete(10); // one child
    println!("After deleting 10: {:?}", tree.inorder());

    tree.delete(3);  // two children
    println!("After deleting 3:  {:?}", tree.inorder());

    println!("Search 6: {}", tree.search(6)); // true
    println!("Search 3: {}", tree.search(3)); // false (deleted)

    // Memory automatically freed when `tree` drops — no free_tree() needed!
}

// ─────────────────────────────────────────────
// TESTS — Rust's built-in test framework
// ─────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    fn build_test_tree() -> BST {
        let mut t = BST::new();
        for &v in &[8i64, 3, 10, 1, 6, 14, 4, 7, 13] {
            t.insert(v);
        }
        t
    }

    #[test]
    fn test_inorder_sorted() {
        let t = build_test_tree();
        assert_eq!(t.inorder(), vec![1, 3, 4, 6, 7, 8, 10, 13, 14]);
    }

    #[test]
    fn test_search() {
        let t = build_test_tree();
        assert!(t.search(6));
        assert!(!t.search(99));
    }

    #[test]
    fn test_min_max() {
        let t = build_test_tree();
        assert_eq!(t.find_min(), Some(1));
        assert_eq!(t.find_max(), Some(14));
    }

    #[test]
    fn test_height() {
        let t = build_test_tree();
        assert_eq!(t.height(), 3);
    }

    #[test]
    fn test_successor_predecessor() {
        let t = build_test_tree();
        assert_eq!(t.successor(6),   Some(7));
        assert_eq!(t.predecessor(6), Some(4));
        assert_eq!(t.successor(14),  None); // no successor for max
        assert_eq!(t.predecessor(1), None); // no predecessor for min
    }

    #[test]
    fn test_delete_leaf() {
        let mut t = build_test_tree();
        t.delete(7);
        assert!(!t.search(7));
        assert_eq!(t.inorder(), vec![1, 3, 4, 6, 8, 10, 13, 14]);
    }

    #[test]
    fn test_delete_one_child() {
        let mut t = build_test_tree();
        t.delete(10);
        assert!(!t.search(10));
        assert!(t.search(14)); // child should still exist
    }

    #[test]
    fn test_delete_two_children() {
        let mut t = build_test_tree();
        t.delete(3);
        assert!(!t.search(3));
        assert!(t.is_valid()); // BST property must still hold
    }

    #[test]
    fn test_validation() {
        let t = build_test_tree();
        assert!(t.is_valid());

        // Manually build invalid BST
        let invalid = Some(Box::new(Node {
            val: 10,
            left: Some(Box::new(Node {
                val: 5,
                left: None,
                right: Some(Box::new(Node { val: 12, left: None, right: None })),
                //              ↑ INVALID: 12 > 10, can't be in left subtree of 10
            })),
            right: None,
        }));
        let invalid_tree = BST { root: invalid };
        assert!(!invalid_tree.is_valid());
    }
}
```

---

## 13. Common BST Patterns and Problem Templates

```
┌──────────────────────────────────────────────────────────────────────┐
│              EXPERT PATTERN RECOGNITION GUIDE                         │
├────────────────────────────┬─────────────────────────────────────────┤
│  Pattern                   │  Tell-tale Signs in Problem              │
├────────────────────────────┼─────────────────────────────────────────┤
│  Range Propagation         │  "Valid BST", "within bounds",           │
│  (pass min/max down)       │  "kth element in BST"                   │
├────────────────────────────┼─────────────────────────────────────────┤
│  Inorder = Sorted          │  "kth smallest", "sorted output",       │
│                            │  "convert BST to sorted array"          │
├────────────────────────────┼─────────────────────────────────────────┤
│  Postorder for cleanup     │  "delete tree", "bottom-up calculation",│
│                            │  "tree diameter", "max path sum"        │
├────────────────────────────┼─────────────────────────────────────────┤
│  LCA (Lowest Common        │  "lowest common ancestor",              │
│  Ancestor)                 │  "path between two nodes"               │
│  → In BST: first node      │                                         │
│    where paths diverge     │                                         │
├────────────────────────────┼─────────────────────────────────────────┤
│  Level order / BFS         │  "level by level", "zigzag",            │
│                            │  "right side view", "widest level"      │
├────────────────────────────┼─────────────────────────────────────────┤
│  Successor/Predecessor     │  "next larger", "in-place sort",        │
│                            │  "floor/ceiling of value"               │
├────────────────────────────┼─────────────────────────────────────────┤
│  Two-pointer on Inorder    │  "two sum in BST", "find pair"          │
│                            │  (use inorder iterator as pointer)      │
└────────────────────────────┴─────────────────────────────────────────┘
```

### LCA in BST — Elegant Pattern

```
Lowest Common Ancestor (LCA) of nodes p and q:

In a BST, the LCA is the FIRST node where p and q are in DIFFERENT subtrees,
OR one of them IS the node.

Algorithm:
  current = root
  while true:
    if p < current AND q < current: go LEFT (both in left subtree)
    if p > current AND q > current: go RIGHT (both in right subtree)
    else: current IS the LCA (paths diverge here, or one matches)

Example: LCA of 1 and 7 in our tree:
  current=8:  1 < 8 AND 7 < 8 → go LEFT
  current=3:  1 < 3 AND 7 > 3 → DIVERGE → LCA = 3 ✓

Example: LCA of 4 and 13:
  current=8:  4 < 8 AND 13 > 8 → DIVERGE → LCA = 8 ✓
```

### Kth Smallest — Inorder Counter Pattern

```
Problem: Find the kth smallest element in BST.

Key insight: Inorder traversal produces sorted order.
The kth element visited during inorder IS the kth smallest.

Pattern (use a counter that decrements):
  inorder_kth(node, k, counter):
    if node == nil: return
    inorder_kth(node.left, k, counter)
    counter--
    if counter == 0: RETURN node.val (← this is kth smallest)
    inorder_kth(node.right, k, counter)

No sorting needed — the BST structure IS the sorted order!
```

### Floor and Ceiling

```
FLOOR(val)   = largest value in BST that is ≤ val
CEILING(val) = smallest value in BST that is ≥ val

Floor Algorithm:
  result = None
  current = root
  while current:
    if current.val == val: return val (exact match)
    if current.val < val:
      result = current.val  ← candidate floor
      go RIGHT (look for closer floor)
    else:
      go LEFT (current too big)
  return result

Ceiling: Mirror of floor logic.
```

---

## 14. Expert Mental Models and Intuition Building

### Mental Model 1 — The "Ruling Out" Model

```
Every BST operation works by RULING OUT regions of the tree:

At each node, you eliminate HALF the remaining search space.
This is why BSTs give O(log n) — not because trees are special,
but because the CONSTRAINT (left < node < right) lets you make
a CERTAIN decision at every step.

If you can't make a certain decision → the structure is broken (not a valid BST).
```

### Mental Model 2 — Recursion as "Trust the Subtree"

```
When writing recursive BST functions:

1. Write the BASE CASE first (null node → return something simple)
2. ASSUME the recursive call works correctly for subtrees
3. Combine results to solve the current node

For example, height():
  - "If null, height is -1"           ← base case
  - "Assume height(left) works"       ← trust the subtree
  - "Assume height(right) works"      ← trust the subtree
  - "My height = 1 + max(both)"       ← combine

This is the INDUCTIVE HYPOTHESIS mental model from mathematics.
```

### Mental Model 3 — The "Sorted Array in Disguise"

```
A BST is a SORTED ARRAY restructured as a tree for O(log n) access.

Sorted Array:  [1, 3, 4, 6, 7, 8, 10, 13, 14]
BST Inorder:   [1, 3, 4, 6, 7, 8, 10, 13, 14]

Any operation you'd do on a sorted array, you can do on a BST:
• Binary search             → BST search
• Insert maintaining order  → BST insert
• Finding successor         → BST successor
• Range queries             → BST range traversal

The tree structure just makes INSERT/DELETE O(log n) instead of O(n).
```

### Cognitive Principle — Chunking

```
Expert BST programmers have CHUNKED these operations:
• "find min" → instantly know: go leftmost
• "delete with two children" → instantly reach for: find successor
• "inorder = sorted" → immediately available without derivation

Build these chunks deliberately:
  1. Understand WHY each operation works (deep understanding)
  2. Practice until you can PRODUCE it from memory (retrieval practice)
  3. Recognize the PATTERN in novel problems (transfer learning)

The goal is not memorization — it's pattern abstraction so fast
it feels like intuition. That IS what intuition is.
```

---

## 15. Edge Cases — What Breaks Average Programmers

```
┌─────────────────────────────────────────────────────────────────┐
│               CRITICAL EDGE CASES TO ALWAYS CONSIDER            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. EMPTY TREE (root = null)                                    │
│     → Search, delete, min/max must handle this gracefully       │
│                                                                 │
│  2. SINGLE NODE TREE                                            │
│     → Delete the only node → tree becomes empty                │
│     → Height = 0, Count = 1                                    │
│                                                                 │
│  3. DELETING THE ROOT                                           │
│     → Must correctly update root reference                     │
│     → All 3 delete cases must work for root                    │
│                                                                 │
│  4. DUPLICATE VALUES                                            │
│     → Decide: ignore, error, or allow (usually ignore)         │
│     → Must be consistent in search and insert                  │
│                                                                 │
│  5. SKEWED TREE (sorted input)                                  │
│     → Recursive operations may stack overflow (O(n) depth)     │
│     → Iterative implementations are safer                      │
│                                                                 │
│  6. BST VALIDATION WITH INT_MIN / INT_MAX VALUES               │
│     → If node.val == INT_MAX, comparison (val >= max) fails    │
│     → Use LONG or unbounded integers for bounds in validation  │
│                                                                 │
│  7. SUCCESSOR/PREDECESSOR OF MIN/MAX                            │
│     → Successor of maximum = None (no successor)               │
│     → Predecessor of minimum = None (no predecessor)           │
│                                                                 │
│  8. DELETING A VALUE NOT IN THE TREE                            │
│     → Must silently do nothing, not crash                      │
│                                                                 │
│  9. AFTER DELETION, BST PROPERTY MUST STILL HOLD               │
│     → Always test with is_valid() after delete operations      │
│                                                                 │
│ 10. RUST SPECIFIC: Ownership in recursive delete               │
│     → .take() extracts Option<Box<Node>> for reconstruction    │
│     → Pattern matching on (left, right) after take() is clean  │
│                                                                 │
│ 11. C SPECIFIC: Memory leaks in delete                         │
│     → Every malloc must have a corresponding free             │
│     → free_tree must use POSTORDER (children before parent)    │
│                                                                 │
│ 12. GO SPECIFIC: Slice-as-queue in level_order                 │
│     → Slicing from front (queue[1:]) causes memory leak       │
│     → Use container/list or channel for production code        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Summary — The Master View

```
┌─────────────────────────────────────────────────────────────────────┐
│                    BST COMPLETE OVERVIEW                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PROPERTY:    left subtree < node < right subtree (all nodes)      │
│                                                                     │
│  OPERATIONS:                                                        │
│    Search     → Follow BST property left/right until found/null    │
│    Insert     → Search for position, place as leaf                 │
│    Delete     → 3 cases: leaf / 1-child / 2-children (successor)   │
│    Min/Max    → Leftmost / Rightmost node                          │
│    Successor  → Min(right subtree) OR first left-ancestor          │
│    Height     → 1 + max(left height, right height) recursively     │
│    Validate   → Range propagation [min, max] top-down              │
│                                                                     │
│  TRAVERSALS:                                                        │
│    Inorder    → LNR → SORTED output (most important for BST)       │
│    Preorder   → NLR → Serialization / copy                         │
│    Postorder  → LRN → Deletion / bottom-up computation             │
│    LevelOrder → BFS → Level-by-level structure                     │
│                                                                     │
│  COMPLEXITY:                                                        │
│    Balanced:  O(log n) for search/insert/delete                    │
│    Skewed:    O(n) for all operations (worst case)                 │
│    Traversal: Always O(n)                                          │
│                                                                     │
│  NEXT STEPS (Self-Balancing Trees):                                │
│    AVL Tree        → Strict balance |bf| ≤ 1, rotations           │
│    Red-Black Tree  → Relaxed balance, faster insert/delete         │
│    B-Tree          → Disk-optimized, used in databases             │
│    Treap           → Random priorities, expected O(log n)          │
└─────────────────────────────────────────────────────────────────────┘
```

---

*End of BST Complete Mastery Guide*
*Next topics to master: AVL Trees → Red-Black Trees → B-Trees → Segment Trees*

Now let me build this comprehensive BST guide. This will be a thorough, deeply structured markdown file.**2,381 lines. Every concept, zero fluff.** Here's what's inside:

---

**Structure of the Guide:**

| Section | What You Master |
|---|---|
| §1 Mental Model | Schema formation before code — binary search made spatial |
| §2 Vocabulary | Every term (node, leaf, pivot, successor, predecessor, etc.) with a lookup table |
| §3–4 BST Fundamentals | The invariant, the subtree trap (common mistake), why the property must hold globally |
| §5 Visual Anatomy | Full node-by-node depth/height/type breakdown |
| §6–7 All Operations | Search, Insert, Delete (all 3 cases with visual traces), Min/Max, Successor/Predecessor, Height, Count — each with decision trees and step-by-step traces |
| §8 Traversals | Inorder/Preorder/Postorder/Level-Order — with call stack visualizations and BFS queue traces |
| §9 Validation | The "range propagation" technique and why the naive approach fails |
| §10 Balance | Balanced vs skewed, why sorted insertion is the BST's enemy |
| §11 Complexity | Full table: average/worst case for every operation with call-stack depth insight |
| §12 Implementations | Complete, idiomatic, production-quality code in **Go**, **C**, and **Rust** with tests |
| §13 Patterns | Expert pattern recognition table + LCA, Kth smallest, Floor/Ceiling templates |
| §14 Mental Models | 3 expert models + the chunking cognitive principle |
| §15 Edge Cases | 12 critical edge cases including language-specific pitfalls (Go slice leak, C free order, Rust `.take()` pattern) |

---

**Three things to internalize before moving to AVL Trees:**

1. **The delete case 3 logic** — copy successor value, then delete successor. This is the non-obvious insight that trips everyone.
2. **Validation uses range propagation, not child comparison** — the subtree trap is a guaranteed interview question.
3. **Inorder = sorted** is not a coincidence — it's the BST property expressed through time rather than space.