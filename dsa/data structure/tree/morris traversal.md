# Morris Traversal — The Complete, Comprehensive Guide

note: this guide having some mistaks, so check the corrected details at the end of the article.

> *"To traverse without a stack, you must leave breadcrumbs in the tree itself."*

---

## Table of Contents

1. [Prerequisites & Foundational Concepts](#1-prerequisites--foundational-concepts)
2. [What Is Morris Traversal?](#2-what-is-morris-traversal)
3. [The Core Idea — Threaded Binary Trees](#3-the-core-idea--threaded-binary-trees)
4. [The Predecessor Concept — Deep Dive](#4-the-predecessor-concept--deep-dive)
5. [Morris Inorder Traversal](#5-morris-inorder-traversal)
6. [Morris Preorder Traversal](#6-morris-preorder-traversal)
7. [Morris Postorder Traversal](#7-morris-postorder-traversal)
8. [Complexity Analysis](#8-complexity-analysis)
9. [Implementations in C, Go, and Rust](#9-implementations-in-c-go-and-rust)
10. [Dry Run Walkthroughs](#10-dry-run-walkthroughs)
11. [Edge Cases & Pitfalls](#11-edge-cases--pitfalls)
12. [Applications & Problem Patterns](#12-applications--problem-patterns)
13. [Comparison with Other Traversal Methods](#13-comparison-with-other-traversal-methods)
14. [Mental Models & Expert Intuition](#14-mental-models--expert-intuition)

---

## 1. Prerequisites & Foundational Concepts

Before diving into Morris Traversal, every term and concept used must be crystal clear. Let us build from absolute ground zero.

---

### 1.1 Binary Tree — What Is It?

A **binary tree** is a hierarchical data structure where:
- Each element is called a **node**.
- Every node has at most **two children**: a **left child** and a **right child**.
- There is one special node called the **root** — it has no parent.
- Nodes with no children are called **leaf nodes**.

```
        10          <-- Root
       /  \
      5    20       <-- Internal nodes
     / \     \
    3   7     25    <-- 3, 7, 25 are leaf nodes
```

A node in code looks like this conceptually:
```
Node {
    value:  some integer
    left:   pointer to left child (or null/nil/None)
    right:  pointer to right child (or null/nil/None)
}
```

---

### 1.2 Tree Traversal — What Does It Mean?

**Traversal** means visiting every node in the tree exactly once, in some specific order.

The three classic orders:

```
        A
       / \
      B   C
     / \
    D   E
```

| Order    | Pattern              | Result for tree above |
|----------|----------------------|-----------------------|
| Inorder  | Left → Root → Right  | D B E A C             |
| Preorder | Root → Left → Right  | A B D E C             |
| Postorder| Left → Right → Root  | D E B C A             |

---

### 1.3 Why Do Standard Traversals Need Extra Memory?

The classic recursive approach uses the **call stack** — the hidden stack maintained by the CPU/OS for function calls. Each recursive call pushes a frame onto this stack.

```
inorder(A)
    inorder(B)
        inorder(D)
            visit D          ← D has no children, just visit
        visit B              ← visit B AFTER left (D), BEFORE right (E)
        inorder(E)
            visit E          ← E has no children, just visit
    visit A                  ← visit A AFTER left subtree (B), BEFORE right (C)
    inorder(C)
        visit C              ← C has no children, just visit

```

```
START
  │
  ▼
inorder(A)
  │
  ├──► inorder(B)  [A's LEFT]
  │       │
  │       ├──► inorder(D)  [B's LEFT]
  │       │       │
  │       │       └──► D has no children → VISIT D  ✅
  │       │
  │       ├──► VISIT B  ✅   ← ROOT of B's subtree
  │       │
  │       └──► inorder(E)  [B's RIGHT]
  │               │
  │               └──► E has no children → VISIT E  ✅
  │
  ├──► VISIT A  ✅   ← ROOT of whole tree
  │
  └──► inorder(C)  [A's RIGHT]
          │
          └──► C has no children → VISIT C  ✅

FINAL VISIT ORDER:  D → B → E → A → C
```

At the deepest point, the stack holds **O(h)** frames where **h = height of the tree**.
- In a balanced tree: h = O(log n)
- In a skewed tree (like a linked list): h = O(n)

The iterative approach replaces the call stack with an **explicit stack** data structure, but still requires O(h) space.

**The question Morris Traversal answers:**
> Can we traverse a binary tree in O(1) additional space (excluding output)?

---

### 1.4 Pointers and NULL

A **pointer** (or reference) stores the memory address of another object. In trees:
- `node.left = NULL` means "no left child exists"
- `node.right = NULL` means "no right child exists"

Leaf nodes always have both pointers set to NULL.

**Key Observation:** In a binary tree with `n` nodes, there are exactly `n+1` NULL pointers. Morris Traversal **temporarily borrows** these NULL pointers to store navigation information.

```
Tree with 5 nodes:
        10
       /  \
      5    20
     / \
    3   7

Total pointers = 5 nodes × 2 pointers each = 10 pointers
Non-null pointers = edges = 5 - 1 = 4
NULL pointers = 10 - 4 = 6 = n + 1  ✓
```

---

### 1.5 What Is a "Predecessor"?

The **inorder predecessor** of a node `X` is the node that comes **immediately before X** in an inorder traversal.

In other words: the predecessor of X is the **rightmost node in X's left subtree**.

Why? Because in inorder (Left → Root → Right), we visit the entire left subtree before X. The last node visited in X's left subtree is its rightmost descendant.

```
        10
       /  \
      5    20
     / \
    3   7

Inorder sequence: 3 → 5 → 7 → 10 → 20

Predecessor of 10 = 7   (rightmost of left subtree {5, 3, 7})
Predecessor of 5  = 3   (rightmost of left subtree {3})
Predecessor of 20 = 10  (rightmost of left subtree — but 20 has no left subtree,
                          so it has no left-subtree predecessor)
```

**Algorithm to find inorder predecessor of node X:**
```
predecessor(X):
    go to X.left
    then keep going right (right → right → right...)
    until you cannot go right anymore
    that final node is the predecessor
```

---

### 1.6 What Is a "Thread" in a Tree?

A **thread** (in the context of threaded binary trees) is a **temporary pointer** placed into a normally-NULL pointer, so that after visiting a subtree, you can navigate back upward to a "parent" node — without using a stack.

Morris Traversal creates and destroys these threads dynamically as it traverses. This is the magic that makes it O(1) space.

---

### 1.7 What Is a "Successor"?

The **inorder successor** of a node X is the node that comes **immediately after X** in an inorder traversal.

- It is the **leftmost node in X's right subtree**.

```
Inorder: 3 → 5 → 7 → 10 → 20

Successor of 5  = 7
Successor of 7  = 10
Successor of 10 = 20
```

---

## 2. What Is Morris Traversal?

**Morris Traversal** is an algorithm for traversing a binary tree that:
- Uses **O(1) extra space** (no stack, no recursion)
- Runs in **O(n) time**
- Works by temporarily modifying the tree's NULL right pointers (creating threads)
- **Restores** the tree to its original structure before finishing

It was introduced by **J.H. Morris** in 1979 in the paper:
> *"Traversing Binary Trees Simply and Cheaply"*

The fundamental innovation: instead of "memorising where to go back" using a stack, Morris Traversal **writes the return path into the tree itself**.

---

### 2.1 The Big Picture

```
TRADITIONAL TRAVERSAL                    MORRIS TRAVERSAL
================================         ================================
Uses recursive call stack OR             Uses NULL pointers in the tree
explicit stack data structure            itself as temporary threads

Space: O(h) where h = tree height        Space: O(1) — constant

When at a node, we "know" where          When at a node, we look at the
to go back because the stack             tree structure to decide where
remembers our path                       to go — threads guide us back
```

---

## 3. The Core Idea — Threaded Binary Trees

### 3.1 Observation That Drives Everything

Consider this tree and its inorder traversal:

```
        4
       / \
      2   6
     / \ / \
    1  3 5  7
```

**Inorder:** 1 → 2 → 3 → 4 → 5 → 6 → 7

Now look at the **NULL right pointers** of leaf nodes and nodes whose right child is null:
- Node 1 has `right = NULL` — but in inorder, after visiting 1, we visit **2**
- Node 3 has `right = NULL` — but in inorder, after visiting 3, we visit **4**
- Node 5 has `right = NULL` — but in inorder, after visiting 5, we visit **6**
- Node 7 has `right = NULL` — terminal

**The Insight:** We can fill those NULL right pointers with **threads pointing to the inorder successor**. Then when we reach the end of the left subtree, we can follow the thread back up instead of using a stack.

### 3.2 Threading Visualized

```
BEFORE MORRIS (standard tree):          AFTER THREADING (temporary state):

        4                                       4
       / \                                     / \
      2   6                                   2   6
     / \ / \                                 / \ / \
    1  3 5  7                               1  3 5  7
                                             \  \  \
    1.right = NULL                           [2] [4] [6]   <-- threads
    3.right = NULL
    5.right = NULL
```

These threads are **temporary** — Morris creates them, uses them to navigate, and then removes them.

---

## 4. The Predecessor Concept — Deep Dive

### 4.1 Why We Use the Predecessor (Not Successor)

Morris Traversal threads the **predecessor's right pointer** to point to the current node.

**Reasoning:**

In inorder traversal, the predecessor of node X is visited just before X. After the predecessor is visited, the algorithm needs to "jump up" to X. If we make `predecessor.right = X`, then after visiting the predecessor, following `.right` takes us directly to X.

```
        10
       /
      5
     / \
    3   7      <-- 7 is the predecessor of 10 (rightmost of left subtree)
```

By setting `7.right = 10` (thread), after visiting 7, we follow the thread to reach 10.

### 4.2 How Morris Uses Predecessor — State Machine

Morris Traversal is essentially a **state machine** with two states for each node:

```
STATE 1: "First Visit"
    - Current node's left subtree has NOT been visited yet
    - We find the predecessor and create a thread
    - Move to the left child

STATE 2: "Return Visit" (via thread)
    - We arrived at current node via a predecessor thread
    - The predecessor's right pointer still points to us
    - We know: left subtree is fully processed
    - Remove the thread (restore tree)
    - Visit (print) current node
    - Move to the right child
```

---

### 4.3 Decision Logic — Finding Predecessor

```
FIND PREDECESSOR OF CURRENT NODE (for inorder):
================================================

Start at: current.left  (if it exists)

Then: keep going RIGHT until:
    predecessor.right == NULL    (natural end, first visit)
    OR
    predecessor.right == current (thread exists, return visit)

WHY these two stopping conditions?
    NULL  → no thread yet → this is a first visit
    current → thread exists → this is a return visit via the thread
```

---

## 5. Morris Inorder Traversal

### 5.1 Algorithm

```
Morris Inorder:
===============

SET current = root

WHILE current != NULL:

    IF current.left == NULL:
        [Case A] No left subtree
        VISIT current (print/record its value)
        current = current.right
        (move right — could be real right child OR a thread)

    ELSE:
        [Case B] Has a left subtree
        Find PREDECESSOR = rightmost node in current's left subtree
            (stopping when predecessor.right == NULL OR predecessor.right == current)

        IF predecessor.right == NULL:
            [Case B1] First visit — thread does not exist
            CREATE THREAD: predecessor.right = current
            current = current.left
            (dive into left subtree)

        ELSE: (predecessor.right == current)
            [Case B2] Return visit — thread already exists
            REMOVE THREAD: predecessor.right = NULL
            VISIT current (print/record its value)
            current = current.right
            (move to right subtree)
```

### 5.2 Algorithm Flowchart

```
                    ┌─────────────────────┐
                    │   current = root    │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
              ┌─────┤  current != NULL?   ├──── NO ──→ [ DONE ]
              │     └─────────────────────┘
              │YES
              │
              │     ┌─────────────────────┐
              │     │ current.left == NULL│
              │     └──────────┬──────────┘
              │                │
              │          YES   │   NO
              │     ┌──────────┼──────────────────────────────┐
              │     │          │                              │
              │     ▼          ▼                              │
              │  VISIT(current)  Find PREDECESSOR             │
              │  current =       of current                   │
              │  current.right   (go left, then rightmost)    │
              │     │                                         │
              │     │          ┌──────────────────────┐       │
              │     │          │ predecessor.right     │       │
              │     │          │    == NULL?           │       │
              │     │          └──────────┬────────────┘       │
              │     │                     │                    │
              │     │          YES        │    NO              │
              │     │    ┌────────────────┼────────────────┐  │
              │     │    │                │                 │  │
              │     │    ▼                ▼                 │  │
              │     │  CREATE THREAD    REMOVE THREAD       │  │
              │     │  pred.right=cur   pred.right=NULL     │  │
              │     │  current=         VISIT(current)      │  │
              │     │  current.left     current=            │  │
              │     │                   current.right       │  │
              │     │                                       │  │
              └─────┴───────────────────────────────────────┘
                               (loop back)
```

### 5.3 Step-by-Step Trace on Example Tree

```
Tree:
        4
       / \
      2   6
     / \ / \
    1  3 5  7

Expected Inorder: 1 2 3 4 5 6 7
```

```
TRACE:
======

Step 1: current = 4
        Has left child (2) → Find predecessor of 4
        Go to 2, then keep going right: 2 → 3 (3.right is NULL, STOP)
        predecessor = 3, predecessor.right == NULL
        → Case B1: Create thread: 3.right = 4
        → current = 4.left = 2

Step 2: current = 2
        Has left child (1) → Find predecessor of 2
        Go to 1, then keep going right: 1.right is NULL (STOP)
        predecessor = 1, predecessor.right == NULL
        → Case B1: Create thread: 1.right = 2
        → current = 2.left = 1

Step 3: current = 1
        No left child → Case A
        VISIT 1 ← OUTPUT: [1]
        current = 1.right = 2  (following the THREAD we created!)

Step 4: current = 2
        Has left child (1) → Find predecessor of 2
        Go to 1, 1.right == 2 (STOP — thread found!)
        predecessor = 1, predecessor.right == current (2)
        → Case B2: Remove thread: 1.right = NULL
        → VISIT 2 ← OUTPUT: [1, 2]
        → current = 2.right = 3

Step 5: current = 3
        No left child → Case A
        VISIT 3 ← OUTPUT: [1, 2, 3]
        current = 3.right = 4  (following the THREAD we created!)

Step 6: current = 4
        Has left child (2) → Find predecessor of 4
        Go to 2, then keep going right: 2 → 3, 3.right == 4 (STOP!)
        predecessor = 3, predecessor.right == current (4)
        → Case B2: Remove thread: 3.right = NULL
        → VISIT 4 ← OUTPUT: [1, 2, 3, 4]
        → current = 4.right = 6

Step 7: current = 6
        Has left child (5) → Find predecessor of 6
        Go to 5, 5.right is NULL (STOP)
        predecessor = 5, predecessor.right == NULL
        → Case B1: Create thread: 5.right = 6
        → current = 6.left = 5

Step 8: current = 5
        No left child → Case A
        VISIT 5 ← OUTPUT: [1, 2, 3, 4, 5]
        current = 5.right = 6  (following the THREAD!)

Step 9: current = 6
        Has left child (5) → Find predecessor of 6
        Go to 5, 5.right == 6 (STOP — thread found!)
        → Case B2: Remove thread: 5.right = NULL
        → VISIT 6 ← OUTPUT: [1, 2, 3, 4, 5, 6]
        → current = 6.right = 7

Step 10: current = 7
         No left child → Case A
         VISIT 7 ← OUTPUT: [1, 2, 3, 4, 5, 6, 7]
         current = 7.right = NULL

Step 11: current = NULL → DONE!
```

### 5.4 Thread State Visualization at Each Step

```
STEP 1-2: Creating threads
        4 ←─────────────── thread from 3
       / \
      2 ←─── thread from 1
     / \  \
    1   3   (thread 1→2)
     \
      (thread 1→2)
```

---

## 6. Morris Preorder Traversal

### 6.1 Key Difference from Inorder

In **preorder**, we visit the node **before** going into its left subtree.

The difference from inorder: **when to call VISIT**.

- **Inorder:** Visit on the **return visit** (when thread found / no left child)
- **Preorder:** Visit on the **first visit** (when creating thread / no left child)

### 6.2 Algorithm

```
Morris Preorder:
================

SET current = root

WHILE current != NULL:

    IF current.left == NULL:
        VISIT current          ← visit here (no left child)
        current = current.right

    ELSE:
        Find PREDECESSOR

        IF predecessor.right == NULL:
            VISIT current      ← visit here BEFORE going left (first visit)
            CREATE THREAD: predecessor.right = current
            current = current.left

        ELSE: (predecessor.right == current)
            REMOVE THREAD: predecessor.right = NULL
            current = current.right
            (DO NOT visit — we already visited on first visit)
```

### 6.3 Preorder Flowchart

```
                    ┌─────────────────────┐
                    │   current = root    │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
              ┌─────┤  current != NULL?   ├──── NO ──→ [ DONE ]
              │     └─────────────────────┘
              YES
              │
              │     ┌─────────────────────────┐
              │     │  current.left == NULL?  │
              └─────┤                         │
                    └────────┬────────────────┘
                             │
                    YES      │     NO
              ┌──────────────┴─────────────────────┐
              │                                     │
              ▼                                     ▼
          VISIT(current)                    Find PREDECESSOR
          current =                                │
          current.right                            │
                                    ┌──────────────▼──────────────┐
                                    │  predecessor.right == NULL? │
                                    └──────────────┬──────────────┘
                                                   │
                                         YES       │      NO
                                    ┌──────────────┴──────────────┐
                                    │                             │
                                    ▼                             ▼
                               VISIT(current)             REMOVE THREAD
                               CREATE THREAD              pred.right = NULL
                               pred.right = cur           current =
                               current = cur.left         current.right
```

---

## 7. Morris Postorder Traversal

### 7.1 Why Postorder Is Harder

Postorder (Left → Right → Root) is the trickiest. The root is visited **last**. Morris Traversal handles this by using a **reverse trick**.

### 7.2 The Reverse Path Trick

The key insight: When we detect a "return visit" (thread exists), instead of visiting just the current node, we **reverse-visit the right spine** of the predecessor's subtree.

This sounds complex, but let's break it down:

**Definition — Right Spine of a node X:**
Starting from X, follow right pointers until you reach NULL.

```
Right spine of node 2 (in tree below):
        2
         \
          3
           \
            (null)
Spine: 2 → 3
```

**The Algorithm:**
When on a "return visit" to node X (its left subtree is done):
1. Temporarily reverse the right spine from `X.left` to the predecessor
2. Visit nodes in reverse order along that spine
3. Re-reverse the spine to restore the tree

### 7.3 Algorithm (Conceptual)

```
Morris Postorder:
=================

Create a DUMMY node, set dummy.left = root
SET current = dummy

WHILE current != NULL:

    IF current.left == NULL:
        current = current.right

    ELSE:
        Find PREDECESSOR of current in its left subtree

        IF predecessor.right == NULL:
            CREATE THREAD: predecessor.right = current
            current = current.left

        ELSE: (predecessor.right == current)
            REMOVE THREAD: predecessor.right = NULL
            REVERSE_VISIT(current.left to predecessor)
            current = current.right

At the end, REVERSE_VISIT(root)

REVERSE_VISIT(from, to):
    Reverse the right pointers from 'from' up to 'to'
    Visit nodes in that reversed order
    Re-reverse to restore
```

### 7.4 Postorder Trace

```
Tree:
        4
       / \
      2   6
     / \
    1   3

Expected Postorder: 1 3 2 6 4
```

```
Dummy → 4 → 2 → 6 (dummy.left = root)

current = dummy
Step 1: dummy.left = 4 (not NULL)
        Find predecessor of dummy in left subtree
        Go to 4, go right: 4 → 6 (6.right is NULL, STOP)
        predecessor = 6, pred.right == NULL
        → Thread: 6.right = dummy
        → current = dummy.left = 4

Step 2: current = 4
        4.left = 2 (not NULL)
        predecessor of 4: go to 2, right to 3 (3.right=NULL, STOP)
        predecessor = 3
        → Thread: 3.right = 4
        → current = 2

Step 3: current = 2
        2.left = 1 (not NULL)
        predecessor of 2: go to 1 (1.right=NULL, STOP)
        predecessor = 1
        → Thread: 1.right = 2
        → current = 1

Step 4: current = 1
        1.left = NULL → current = 1.right = 2 (via thread)

Step 5: current = 2
        2.left = 1 (not NULL)
        predecessor of 2: go to 1, 1.right = 2 (STOP — thread!)
        → Remove thread: 1.right = NULL
        → REVERSE_VISIT from 1 to 1: visit 1
        OUTPUT: [1]
        → current = 2.right = 3

Step 6: current = 3
        3.left = NULL → current = 3.right = 4 (via thread)

Step 7: current = 4
        4.left = 2 (not NULL)
        predecessor of 4: go to 2, right to 3, 3.right = 4 (STOP — thread!)
        → Remove thread: 3.right = NULL
        → REVERSE_VISIT from 2 to 3: reverse right spine 2→3, visit 3 then 2
        OUTPUT: [1, 3, 2]
        → current = 4.right = 6

Step 8: current = 6
        6.left = NULL → current = 6.right = dummy (via thread)

Step 9: current = dummy
        dummy.left = 4 (not NULL)
        predecessor of dummy: go to 4, right to 6, 6.right = dummy (STOP!)
        → Remove thread: 6.right = NULL
        → REVERSE_VISIT from 4 to 6: reverse right spine 4→6, visit 6 then 4
        OUTPUT: [1, 3, 2, 6, 4]
        → current = dummy.right = NULL

DONE! Output: 1 3 2 6 4 ✓
```

---

## 8. Complexity Analysis

### 8.1 Time Complexity

**Claim: O(n) despite finding predecessor repeatedly.**

This surprises many. Let us reason carefully:

Each node is visited **at most twice**:
1. Once when `current` first points to it (creating the thread)
2. Once when `current` returns to it via the thread (removing the thread)

Finding the predecessor: each node can serve as predecessor for **at most one node** (its inorder successor). The predecessor-finding loop traverses a right spine. Each edge on a right spine is traversed:
- Once during the "going right" in finding predecessor (for the create-thread step)
- Once during the "going right" in finding predecessor (for the remove-thread step)

So each edge is traversed at most **2 times total** across all predecessor-finding operations.

Total work = O(2n) = **O(n)**

### 8.2 Space Complexity

```
Space used by Morris Traversal:
================================
Variables: current, predecessor  →  O(1)
No recursion stack               →  O(1)
No explicit stack/queue          →  O(1)
Threads stored IN the tree       →  O(1) (reusing existing NULL pointers)
─────────────────────────────────────────────────
Total extra space: O(1)
```

### 8.3 Comparison Table

```
┌──────────────────────┬────────────┬────────────┬─────────────────────┐
│ Method               │ Time       │ Space      │ Notes               │
├──────────────────────┼────────────┼────────────┼─────────────────────┤
│ Recursive            │ O(n)       │ O(h)       │ h=height, simplest  │
│ Iterative (Stack)    │ O(n)       │ O(h)       │ explicit stack      │
│ Morris               │ O(n)       │ O(1)       │ modifies tree temp  │
├──────────────────────┼────────────┼────────────┼─────────────────────┤
│ h (balanced tree)    │            │ O(log n)   │                     │
│ h (skewed tree)      │            │ O(n)       │                     │
└──────────────────────┴────────────┴────────────┴─────────────────────┘
```

### 8.4 The Cost of O(1) Space

Morris Traversal has a **hidden cost**: it temporarily modifies the tree. This means:
- It is **NOT thread-safe** (concurrent reads would see inconsistent state)
- Cannot be used when tree modification is forbidden
- Slightly more complex to implement

---

## 9. Implementations in C, Go, and Rust

### 9.1 C Implementation

```c
#include <stdio.h>
#include <stdlib.h>

/* ── Node structure ─────────────────────────────────────────────────── */
typedef struct Node {
    int data;
    struct Node *left;
    struct Node *right;
} Node;

/* ── Helper: allocate a new node ────────────────────────────────────── */
Node *new_node(int data) {
    Node *n = (Node *)malloc(sizeof(Node));
    if (!n) { perror("malloc"); exit(EXIT_FAILURE); }
    n->data  = data;
    n->left  = NULL;
    n->right = NULL;
    return n;
}

/* ── MORRIS INORDER ─────────────────────────────────────────────────── */
/*
 * Algorithm:
 *   While current is not NULL:
 *     If current has no left child:
 *       VISIT current, move right
 *     Else:
 *       Find inorder predecessor (rightmost in left subtree)
 *       If predecessor.right == NULL:
 *         Make thread: predecessor.right = current
 *         Move left
 *       Else (thread exists):
 *         Remove thread
 *         VISIT current, move right
 */
void morris_inorder(Node *root) {
    Node *current    = root;
    Node *predecessor = NULL;

    while (current != NULL) {
        if (current->left == NULL) {
            /* Case A: No left subtree — visit and move right */
            printf("%d ", current->data);
            current = current->right;
        } else {
            /* Case B: Has left subtree — find predecessor */
            predecessor = current->left;

            /*
             * Find the rightmost node in current's left subtree.
             * Stop when:
             *   (a) predecessor->right is NULL  (first visit — no thread yet)
             *   (b) predecessor->right is current (return visit — thread exists)
             */
            while (predecessor->right != NULL &&
                   predecessor->right != current) {
                predecessor = predecessor->right;
            }

            if (predecessor->right == NULL) {
                /* Case B1: First visit — create thread */
                predecessor->right = current;   /* CREATE THREAD */
                current = current->left;
            } else {
                /* Case B2: Return visit — remove thread and visit */
                predecessor->right = NULL;      /* REMOVE THREAD */
                printf("%d ", current->data);
                current = current->right;
            }
        }
    }
    printf("\n");
}

/* ── MORRIS PREORDER ────────────────────────────────────────────────── */
/*
 * Identical to inorder EXCEPT: visit node on FIRST visit (not return visit)
 */
void morris_preorder(Node *root) {
    Node *current    = root;
    Node *predecessor = NULL;

    while (current != NULL) {
        if (current->left == NULL) {
            /* No left child: visit immediately */
            printf("%d ", current->data);
            current = current->right;
        } else {
            predecessor = current->left;

            while (predecessor->right != NULL &&
                   predecessor->right != current) {
                predecessor = predecessor->right;
            }

            if (predecessor->right == NULL) {
                /* First visit: VISIT here, before going left */
                printf("%d ", current->data);   /* ← key difference */
                predecessor->right = current;
                current = current->left;
            } else {
                /* Return visit: no visit — just remove thread and go right */
                predecessor->right = NULL;
                current = current->right;
            }
        }
    }
    printf("\n");
}

/* ── POSTORDER HELPER: reverse right spine and visit ───────────────── */
/*
 * Reverses the right pointers from 'from' to 'to',
 * visits nodes in that reversed order, then re-reverses.
 */
static void reverse_right(Node *from, Node *to) {
    if (from == to) {
        printf("%d ", from->data);
        return;
    }
    /* Reverse: from → ... → to becomes to → ... → from */
    Node *x = from, *y = from->right, *z;
    while (x != to) {
        z = y->right;
        y->right = x;
        x = y;
        y = z;
    }
    /* Visit in reversed order */
    Node *p = to;
    while (p != from) {
        printf("%d ", p->data);
        p = p->right;
    }
    printf("%d ", from->data);
    /* Re-reverse back to original */
    x = to; y = to->right; z = NULL;
    while (x != from) {
        z = y->right;
        y->right = x;
        x = y;
        y = z;
    }
    from->right = NULL;
}

/* ── MORRIS POSTORDER ───────────────────────────────────────────────── */
void morris_postorder(Node *root) {
    /* Create a dummy node whose left child is root */
    Node dummy = {.data = 0, .left = root, .right = NULL};
    Node *current    = &dummy;
    Node *predecessor = NULL;

    while (current != NULL) {
        if (current->left == NULL) {
            current = current->right;
        } else {
            predecessor = current->left;

            while (predecessor->right != NULL &&
                   predecessor->right != current) {
                predecessor = predecessor->right;
            }

            if (predecessor->right == NULL) {
                predecessor->right = current;
                current = current->left;
            } else {
                /* Return visit: reverse-visit the right spine */
                reverse_right(current->left, predecessor);
                predecessor->right = NULL;
                current = current->right;
            }
        }
    }
    printf("\n");
}

/* ── Test ───────────────────────────────────────────────────────────── */
int main(void) {
    /*
     * Build tree:
     *         4
     *        / \
     *       2   6
     *      / \ / \
     *     1  3 5  7
     */
    Node *root   = new_node(4);
    root->left   = new_node(2);
    root->right  = new_node(6);
    root->left->left   = new_node(1);
    root->left->right  = new_node(3);
    root->right->left  = new_node(5);
    root->right->right = new_node(7);

    printf("Morris Inorder:   ");
    morris_inorder(root);   /* Expected: 1 2 3 4 5 6 7 */

    printf("Morris Preorder:  ");
    morris_preorder(root);  /* Expected: 4 2 1 3 6 5 7 */

    printf("Morris Postorder: ");
    morris_postorder(root); /* Expected: 1 3 2 5 7 6 4 */

    /* Free memory (omitted for brevity in competitive programming;
       include in production code) */
    return 0;
}
```

---

### 9.2 Go Implementation

```go
package main

import "fmt"

// ── Node structure ──────────────────────────────────────────────────────
type Node struct {
    Data  int
    Left  *Node
    Right *Node
}

// newNode creates a leaf node with the given value.
func newNode(data int) *Node {
    return &Node{Data: data}
}

// ── Morris Inorder ──────────────────────────────────────────────────────
//
// Visit order: Left → Root → Right
// Key rule:
//   - No left child  → visit and move right
//   - Has left child → find predecessor
//       - No thread → create thread, move left (first visit)
//       - Thread exists → remove thread, visit, move right (return visit)
func MorrisInorder(root *Node) []int {
    result := make([]int, 0)
    current := root

    for current != nil {
        if current.Left == nil {
            // Case A: No left subtree
            result = append(result, current.Data)
            current = current.Right
        } else {
            // Case B: Find inorder predecessor
            predecessor := current.Left
            for predecessor.Right != nil && predecessor.Right != current {
                predecessor = predecessor.Right
            }

            if predecessor.Right == nil {
                // Case B1: First visit — create thread
                predecessor.Right = current // THREAD CREATED
                current = current.Left
            } else {
                // Case B2: Return visit — destroy thread, visit
                predecessor.Right = nil // THREAD REMOVED
                result = append(result, current.Data)
                current = current.Right
            }
        }
    }
    return result
}

// ── Morris Preorder ─────────────────────────────────────────────────────
//
// Visit order: Root → Left → Right
// Key difference from inorder: visit the node on FIRST encounter
// (when creating the thread), not on return visit.
func MorrisPreorder(root *Node) []int {
    result := make([]int, 0)
    current := root

    for current != nil {
        if current.Left == nil {
            // No left child: visit immediately
            result = append(result, current.Data)
            current = current.Right
        } else {
            predecessor := current.Left
            for predecessor.Right != nil && predecessor.Right != current {
                predecessor = predecessor.Right
            }

            if predecessor.Right == nil {
                // First visit: VISIT BEFORE going left ← key difference
                result = append(result, current.Data)
                predecessor.Right = current
                current = current.Left
            } else {
                // Return visit: remove thread, go right (no visit here)
                predecessor.Right = nil
                current = current.Right
            }
        }
    }
    return result
}

// ── Morris Postorder ────────────────────────────────────────────────────
//
// Visit order: Left → Right → Root
// Uses reverse-spine trick:
//   On return visit, reverse right spine from current.Left to predecessor,
//   visit nodes in reverse, then restore the spine.

// reverseRight reverses right pointers from 'from' to 'to', visits in
// that reverse order, then restores original direction.
func reverseRight(from, to *Node, result *[]int) {
    // Step 1: Reverse right chain from 'from' to 'to'
    reverseChain(from, to)

    // Step 2: Visit from 'to' back to 'from'
    p := to
    for p != from {
        *result = append(*result, p.Data)
        p = p.Right
    }
    *result = append(*result, from.Data)

    // Step 3: Restore chain
    reverseChain(to, from)
}

// reverseChain reverses the right pointers from 'from' to 'to'.
func reverseChain(from, to *Node) {
    if from == to {
        return
    }
    x := from
    y := from.Right
    for x != to {
        z := y.Right
        y.Right = x
        x = y
        y = z
    }
}

func MorrisPostorder(root *Node) []int {
    result := make([]int, 0)

    // Dummy node: its left child is root
    dummy := &Node{Left: root}
    current := dummy

    for current != nil {
        if current.Left == nil {
            current = current.Right
        } else {
            predecessor := current.Left
            for predecessor.Right != nil && predecessor.Right != current {
                predecessor = predecessor.Right
            }

            if predecessor.Right == nil {
                predecessor.Right = current
                current = current.Left
            } else {
                // Return visit: reverse-visit right spine
                reverseRight(current.Left, predecessor, &result)
                predecessor.Right = nil
                current = current.Right
            }
        }
    }
    return result
}

// ── BST Utilities using Morris ──────────────────────────────────────────

// KthSmallestInBST finds the k-th smallest element using Morris inorder.
// In a BST, inorder traversal produces sorted order.
// Time: O(n), Space: O(1)
func KthSmallestInBST(root *Node, k int) int {
    current := root
    count := 0

    for current != nil {
        if current.Left == nil {
            count++
            if count == k {
                return current.Data
            }
            current = current.Right
        } else {
            predecessor := current.Left
            for predecessor.Right != nil && predecessor.Right != current {
                predecessor = predecessor.Right
            }

            if predecessor.Right == nil {
                predecessor.Right = current
                current = current.Left
            } else {
                predecessor.Right = nil
                count++
                if count == k {
                    return current.Data
                }
                current = current.Right
            }
        }
    }
    return -1 // k out of bounds
}

// ValidateBST checks if a tree is a valid BST using Morris inorder.
// A BST is valid if inorder gives a strictly increasing sequence.
// Time: O(n), Space: O(1)
func ValidateBST(root *Node) bool {
    current := root
    prev := -1 << 62 // smallest possible int64 approximation

    visit := func(val int) bool {
        if val <= prev {
            return false
        }
        prev = val
        return true
    }

    for current != nil {
        if current.Left == nil {
            if !visit(current.Data) {
                return false
            }
            current = current.Right
        } else {
            predecessor := current.Left
            for predecessor.Right != nil && predecessor.Right != current {
                predecessor = predecessor.Right
            }

            if predecessor.Right == nil {
                predecessor.Right = current
                current = current.Left
            } else {
                predecessor.Right = nil
                if !visit(current.Data) {
                    return false
                }
                current = current.Right
            }
        }
    }
    return true
}

// ── Main ─────────────────────────────────────────────────────────────
func main() {
    /*
     * Build tree:
     *         4
     *        / \
     *       2   6
     *      / \ / \
     *     1  3 5  7
     */
    root := newNode(4)
    root.Left = newNode(2)
    root.Right = newNode(6)
    root.Left.Left = newNode(1)
    root.Left.Right = newNode(3)
    root.Right.Left = newNode(5)
    root.Right.Right = newNode(7)

    fmt.Println("Morris Inorder:  ", MorrisInorder(root))   // [1 2 3 4 5 6 7]
    fmt.Println("Morris Preorder: ", MorrisPreorder(root))  // [4 2 1 3 6 5 7]
    fmt.Println("Morris Postorder:", MorrisPostorder(root)) // [1 3 2 5 7 6 4]

    fmt.Println("\nBST Utilities:")
    fmt.Printf("  3rd smallest: %d\n", KthSmallestInBST(root, 3)) // 3
    fmt.Printf("  Is valid BST: %v\n", ValidateBST(root))          // true

    // Test invalid BST
    bad := newNode(5)
    bad.Left = newNode(3)
    bad.Right = newNode(7)
    bad.Left.Right = newNode(6) // 6 > 5, violates BST property
    fmt.Printf("  Invalid BST check: %v\n", ValidateBST(bad)) // false
}
```

---

### 9.3 Rust Implementation

```rust
//! Morris Traversal — Complete Implementation in Rust
//!
//! # Design Choices
//! Rust's ownership model makes pointer-based tree algorithms challenging.
//! We use `*mut Node` (raw pointers) to match the imperative nature of Morris.
//! This is safe in practice because:
//!   - We fully own the tree before traversal
//!   - Threads are temporary and removed before returning
//!   - All allocations are cleaned up in `drop`
//!
//! For production code, consider using `Rc<RefCell<Node>>` for a safe
//! alternative, though it has performance overhead.

use std::ptr;

// ── Node structure ──────────────────────────────────────────────────────
struct Node {
    data:  i32,
    left:  *mut Node,
    right: *mut Node,
}

impl Node {
    fn new(data: i32) -> *mut Node {
        Box::into_raw(Box::new(Node {
            data,
            left:  ptr::null_mut(),
            right: ptr::null_mut(),
        }))
    }
}

// ── Safe wrappers for raw pointer access ────────────────────────────────
// These are the only unsafe operations — we isolate them here.
unsafe fn left_of(node: *mut Node) -> *mut Node {
    (*node).left
}

unsafe fn right_of(node: *mut Node) -> *mut Node {
    (*node).right
}

unsafe fn set_right(node: *mut Node, val: *mut Node) {
    (*node).right = val;
}

unsafe fn data_of(node: *mut Node) -> i32 {
    (*node).data
}

// ── Morris Inorder ──────────────────────────────────────────────────────
/// Traverses the tree in-order (Left → Root → Right).
/// 
/// # Safety
/// `root` must point to a valid, non-cyclic binary tree (or be null).
/// The tree's structure is temporarily modified but fully restored.
/// 
/// # Complexity
/// Time: O(n), Space: O(1)
pub unsafe fn morris_inorder(root: *mut Node) -> Vec<i32> {
    let mut result = Vec::new();
    let mut current = root;

    while !current.is_null() {
        let left = left_of(current);

        if left.is_null() {
            // Case A: No left subtree — visit and move right
            result.push(data_of(current));
            current = right_of(current);
        } else {
            // Case B: Find inorder predecessor
            let mut predecessor = left;
            while !right_of(predecessor).is_null()
                && right_of(predecessor) != current
            {
                predecessor = right_of(predecessor);
            }

            if right_of(predecessor).is_null() {
                // Case B1: First visit — create thread
                set_right(predecessor, current); // THREAD CREATED
                current = left;
            } else {
                // Case B2: Return visit — remove thread, visit
                set_right(predecessor, ptr::null_mut()); // THREAD REMOVED
                result.push(data_of(current));
                current = right_of(current);
            }
        }
    }
    result
}

// ── Morris Preorder ─────────────────────────────────────────────────────
/// Traverses the tree in pre-order (Root → Left → Right).
///
/// Difference from inorder: visit on FIRST encounter (not return visit).
/// 
/// # Complexity
/// Time: O(n), Space: O(1)
pub unsafe fn morris_preorder(root: *mut Node) -> Vec<i32> {
    let mut result = Vec::new();
    let mut current = root;

    while !current.is_null() {
        let left = left_of(current);

        if left.is_null() {
            result.push(data_of(current));
            current = right_of(current);
        } else {
            let mut predecessor = left;
            while !right_of(predecessor).is_null()
                && right_of(predecessor) != current
            {
                predecessor = right_of(predecessor);
            }

            if right_of(predecessor).is_null() {
                // First visit: visit BEFORE creating thread ← key difference
                result.push(data_of(current));
                set_right(predecessor, current);
                current = left;
            } else {
                // Return visit: remove thread, go right (no visit)
                set_right(predecessor, ptr::null_mut());
                current = right_of(current);
            }
        }
    }
    result
}

// ── Reverse Right Spine Helper ──────────────────────────────────────────
/// Reverses the right-pointer chain from `from` to `to`,
/// visits nodes in reverse order, then restores the chain.
unsafe fn reverse_right_and_visit(from: *mut Node, to: *mut Node, result: &mut Vec<i32>) {
    // Step 1: Reverse chain from → ... → to
    reverse_chain(from, to);

    // Step 2: Visit from 'to' back to 'from'
    let mut p = to;
    loop {
        result.push(data_of(p));
        if p == from { break; }
        p = right_of(p);
    }

    // Step 3: Restore chain
    reverse_chain(to, from);
}

/// Reverses right pointers from `from` to `to` (in-place).
unsafe fn reverse_chain(from: *mut Node, to: *mut Node) {
    if from == to { return; }

    let mut x = from;
    let mut y = right_of(from);
    while x != to {
        let z = right_of(y);
        set_right(y, x);
        x = y;
        y = z;
    }
}

// ── Morris Postorder ─────────────────────────────────────────────────────
/// Traverses the tree in post-order (Left → Right → Root).
///
/// Uses a dummy node and the reverse-spine trick for O(1) space.
/// 
/// # Complexity
/// Time: O(n), Space: O(1)
pub unsafe fn morris_postorder(root: *mut Node) -> Vec<i32> {
    let mut result = Vec::new();

    // Create a dummy node; its left child = root
    let dummy = Node::new(0);
    (*dummy).left = root;
    let mut current = dummy;

    while !current.is_null() {
        let left = left_of(current);

        if left.is_null() {
            current = right_of(current);
        } else {
            let mut predecessor = left;
            while !right_of(predecessor).is_null()
                && right_of(predecessor) != current
            {
                predecessor = right_of(predecessor);
            }

            if right_of(predecessor).is_null() {
                set_right(predecessor, current);
                current = left;
            } else {
                // Return visit: reverse-visit the right spine
                reverse_right_and_visit(left, predecessor, &mut result);
                set_right(predecessor, ptr::null_mut());
                current = right_of(current);
            }
        }
    }

    // Clean up dummy node
    drop(Box::from_raw(dummy));

    result
}

// ── Kth Smallest in BST ─────────────────────────────────────────────────
/// Returns the k-th smallest element in a BST (1-indexed).
/// Uses Morris inorder for O(1) space.
pub unsafe fn kth_smallest(root: *mut Node, k: usize) -> Option<i32> {
    let mut current = root;
    let mut count = 0usize;

    while !current.is_null() {
        let left = left_of(current);

        if left.is_null() {
            count += 1;
            if count == k {
                return Some(data_of(current));
            }
            current = right_of(current);
        } else {
            let mut predecessor = left;
            while !right_of(predecessor).is_null()
                && right_of(predecessor) != current
            {
                predecessor = right_of(predecessor);
            }

            if right_of(predecessor).is_null() {
                set_right(predecessor, current);
                current = left;
            } else {
                set_right(predecessor, ptr::null_mut());
                count += 1;
                if count == k {
                    return Some(data_of(current));
                }
                current = right_of(current);
            }
        }
    }
    None // k out of bounds
}

// ── Recover BST (two swapped nodes) ────────────────────────────────────
/// In a BST, exactly two nodes are swapped by mistake.
/// Recover the BST by finding and swapping back without extra space.
///
/// Uses Morris inorder: in a valid BST, inorder is strictly increasing.
/// We detect the two violations to identify the swapped nodes.
pub unsafe fn recover_bst(root: *mut Node) {
    let mut current = root;
    let mut first: *mut Node  = ptr::null_mut();  // first violation
    let mut second: *mut Node = ptr::null_mut();  // second violation
    let mut prev: *mut Node   = ptr::null_mut();  // previous node in inorder

    while !current.is_null() {
        let left = left_of(current);

        if left.is_null() {
            // Visit
            if !prev.is_null() && data_of(prev) > data_of(current) {
                if first.is_null() { first = prev; }
                second = current;
            }
            prev = current;
            current = right_of(current);
        } else {
            let mut predecessor = left;
            while !right_of(predecessor).is_null()
                && right_of(predecessor) != current
            {
                predecessor = right_of(predecessor);
            }

            if right_of(predecessor).is_null() {
                set_right(predecessor, current);
                current = left;
            } else {
                set_right(predecessor, ptr::null_mut());
                // Visit
                if !prev.is_null() && data_of(prev) > data_of(current) {
                    if first.is_null() { first = prev; }
                    second = current;
                }
                prev = current;
                current = right_of(current);
            }
        }
    }

    // Swap the values of the two mis-placed nodes
    if !first.is_null() && !second.is_null() {
        let tmp = (*first).data;
        (*first).data = (*second).data;
        (*second).data = tmp;
    }
}

// ── Tree cleanup ────────────────────────────────────────────────────────
unsafe fn free_tree(node: *mut Node) {
    if node.is_null() { return; }
    free_tree(left_of(node));
    free_tree(right_of(node));
    drop(Box::from_raw(node));
}

// ── Main ─────────────────────────────────────────────────────────────────
fn main() {
    unsafe {
        /*
         * Build tree:
         *         4
         *        / \
         *       2   6
         *      / \ / \
         *     1  3 5  7
         */
        let root = Node::new(4);
        (*root).left  = Node::new(2);
        (*root).right = Node::new(6);
        (*(*root).left).left   = Node::new(1);
        (*(*root).left).right  = Node::new(3);
        (*(*root).right).left  = Node::new(5);
        (*(*root).right).right = Node::new(7);

        println!("Morris Inorder:   {:?}", morris_inorder(root));
        // [1, 2, 3, 4, 5, 6, 7]

        println!("Morris Preorder:  {:?}", morris_preorder(root));
        // [4, 2, 1, 3, 6, 5, 7]

        println!("Morris Postorder: {:?}", morris_postorder(root));
        // [1, 3, 2, 5, 7, 6, 4]

        println!("\nBST Utilities:");
        println!("  3rd smallest: {:?}", kth_smallest(root, 3)); // Some(3)
        println!("  5th smallest: {:?}", kth_smallest(root, 5)); // Some(5)

        // Test recover BST
        // Swapped tree: [3, 2, 4, 1, X, 5, 6] → nodes 3 and 1 are swapped
        //        3           (should be 1 at root of left subtree chain)
        //       / \
        //      2   4
        //     /
        //    1          <-- actually should be 3, it's swapped with 3
        let bad = Node::new(3);
        (*bad).left  = Node::new(2);
        (*bad).right = Node::new(4);
        (*(*bad).left).left = Node::new(1); // this is wrong swap
        // Actual wrong BST: 1 and 3 swapped
        //        3  ← should be 1
        //       / \
        //      2   4
        //     /
        //    1           ← should be 3
        recover_bst(bad);
        println!("\n  After recover BST, inorder: {:?}", morris_inorder(bad));
        // Should be [1, 2, 3, 4]

        free_tree(root);
        free_tree(bad);
    }
}
```

---

## 10. Dry Run Walkthroughs

### 10.1 Skewed Tree (Worst Case Visualization)

```
Skewed (right-heavy) tree:
    1
     \
      2
       \
        3
         \
          4

Inorder traversal: 1 2 3 4
```

```
TRACE (Morris Inorder on right-skewed tree):

current = 1
  1.left = NULL → Case A
  VISIT 1  → [1]
  current = 1.right = 2

current = 2
  2.left = NULL → Case A
  VISIT 2  → [1, 2]
  current = 2.right = 3

current = 3
  3.left = NULL → Case A
  VISIT 3  → [1, 2, 3]
  current = 3.right = 4

current = 4
  4.left = NULL → Case A
  VISIT 4  → [1, 2, 3, 4]
  current = 4.right = NULL

DONE.

Note: No threads created at all! Purely linear traversal.
```

```
Left-skewed tree:
        4
       /
      3
     /
    2
   /
  1

Inorder traversal: 1 2 3 4
```

```
TRACE (Morris Inorder on left-skewed tree):

current = 4
  4.left = 3 (not NULL) → find predecessor of 4
  predecessor = 3, go right: 3.right=NULL (STOP)
  pred.right == NULL → Case B1
  Thread: 3.right = 4
  current = 3

current = 3
  3.left = 2 (not NULL) → find predecessor of 3
  predecessor = 2, go right: 2.right=NULL (STOP)
  Thread: 2.right = 3
  current = 2

current = 2
  2.left = 1 (not NULL) → find predecessor of 2
  predecessor = 1, go right: 1.right=NULL (STOP)
  Thread: 1.right = 2
  current = 1

current = 1
  1.left = NULL → Case A
  VISIT 1  → [1]
  current = 1.right = 2  ← (following thread!)

current = 2
  2.left = 1 (not NULL) → find predecessor of 2
  predecessor = 1, 1.right = 2 (STOP — thread!)
  → Remove thread: 1.right = NULL
  VISIT 2  → [1, 2]
  current = 2.right = 3  ← (following thread!)

current = 3
  3.left = 2 (not NULL) → find predecessor of 3
  predecessor = 2, 2.right = 3 (STOP — thread!)
  → Remove thread: 2.right = NULL
  VISIT 3  → [1, 2, 3]
  current = 3.right = 4  ← (following thread!)

current = 4
  4.left = 3 (not NULL) → find predecessor of 4
  predecessor = 3, 3.right = 4 (STOP — thread!)
  → Remove thread: 3.right = NULL
  VISIT 4  → [1, 2, 3, 4]
  current = 4.right = NULL

DONE.
```

### 10.2 Single Node Tree

```
Tree: just root = 5

Morris Inorder:
  current = 5
  5.left = NULL → Case A
  VISIT 5 → [5]
  current = 5.right = NULL
  DONE. Output: [5]  ✓
```

### 10.3 Two Nodes

```
    2
   /
  1

Morris Inorder:
Step 1: current = 2
  2.left = 1 → predecessor = 1, 1.right=NULL
  Thread: 1.right = 2
  current = 1

Step 2: current = 1
  1.left = NULL → VISIT 1 → [1]
  current = 1.right = 2 (via thread)

Step 3: current = 2
  2.left = 1 → predecessor = 1, 1.right = 2 (thread found!)
  Remove thread: 1.right = NULL
  VISIT 2 → [1, 2]
  current = 2.right = NULL

DONE. Output: [1, 2]  ✓
```

---

## 11. Edge Cases & Pitfalls

### 11.1 Common Pitfalls

```
PITFALL 1: Infinite Loop
========================
If you forget to check `predecessor.right != current` in the while
loop condition, the algorithm will loop forever looking for the end
of the right spine (because the thread points back to current).

WRONG:
    while (predecessor->right != NULL) {   // ← missing the escape condition
        predecessor = predecessor->right;
    }

RIGHT:
    while (predecessor->right != NULL &&
           predecessor->right != current) {
        predecessor = predecessor->right;
    }
```

```
PITFALL 2: Not Restoring the Tree
==================================
If you crash or return early, threads may remain. This corrupts the
tree structure permanently. Always ensure thread removal happens in
every code path.
```

```
PITFALL 3: Thread-Safety
=========================
Morris Traversal is NOT safe for concurrent access.
During traversal, the tree is temporarily in an inconsistent state
(threads exist). Another thread reading the same tree would get
incorrect results. Use read-write locks if parallelism is required.
```

```
PITFALL 4: Trees with Cycles
==============================
Morris Traversal assumes no pre-existing cycles.
If your tree already has a cycle (corrupt data), the predecessor-
finding loop will not terminate. Validate tree integrity beforehand.
```

### 11.2 Decision Tree for Edge Cases

```
                    ┌─────────────────┐
                    │ root == NULL?   │
                    └────────┬────────┘
                             │
                    YES      │     NO
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
         Return empty              Continue traversal
         list/slice

                    ┌──────────────────────┐
                    │ Single node?         │
                    │ (left=NULL,right=NULL)│
                    └──────────┬───────────┘
                               │
                      Case A applies:
                      Visit directly, move right to NULL
                      Terminates cleanly ✓

                    ┌──────────────────────┐
                    │ All nodes in line    │
                    │ (linked list shape)  │
                    └──────────┬───────────┘
                               │
              Left-skewed: O(n) threads created then removed
              Right-skewed: Case A always applies, no threads
              Both terminate correctly ✓
```

---

## 12. Applications & Problem Patterns

Morris Traversal shines in problems where:
1. O(1) space is required
2. BST operations need to be done efficiently
3. We need to process nodes in sorted order without extra memory

### 12.1 Application Map

```
MORRIS TRAVERSAL APPLICATIONS
══════════════════════════════

┌─────────────────────────────────────────────────────┐
│                    INORDER APPLICATIONS              │
├──────────────────────┬──────────────────────────────┤
│ BST Validation       │ Check strictly increasing    │
│ Kth Smallest in BST  │ Count to k during traversal  │
│ Recover BST          │ Find 2 swapped nodes         │
│ BST to sorted array  │ Collect values in order      │
│ Closest value in BST │ Track previous, find min diff│
│ Convert BST to       │ Build doubly linked list      │
│ doubly linked list   │ modifying left/right pointers│
└──────────────────────┴──────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                   PREORDER APPLICATIONS              │
├──────────────────────┬──────────────────────────────┤
│ BST serialization    │ Preorder gives insert order   │
│ Find leftmost node   │ First visited in preorder     │
│ Right side view      │ Track level + preorder        │
└──────────────────────┴──────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                  POSTORDER APPLICATIONS              │
├──────────────────────┬──────────────────────────────┤
│ Delete all nodes     │ Delete children before parent │
│ Tree height (O(1)sp) │ Postorder + counting          │
│ Expression eval      │ Post-fix evaluation order     │
└──────────────────────┴──────────────────────────────┘
```

### 12.2 LeetCode Problem Pattern Guide

```
Problem: "Find Kth Smallest Element in a BST" (LC 230)
═══════════════════════════════════════════════════════
Pattern: Morris Inorder + counter
Stop when counter == k
Time: O(n), Space: O(1)

Problem: "Validate Binary Search Tree" (LC 98)
═══════════════════════════════════════════════════════
Pattern: Morris Inorder + track previous value
If current <= previous → not valid BST
Time: O(n), Space: O(1)

Problem: "Recover Binary Search Tree" (LC 99)
═══════════════════════════════════════════════════════
Pattern: Morris Inorder + find two out-of-order values
First descend: first node of first violated pair
Second descend: second node of last violated pair
Swap their values
Time: O(n), Space: O(1)

Problem: "Binary Tree Inorder Traversal" (LC 94)
═══════════════════════════════════════════════════════
Pattern: Morris Inorder directly
Time: O(n), Space: O(1)

Problem: "Convert Sorted List to Binary Search Tree" (LC 109)
═══════════════════════════════════════════════════════════════
Adjacent concept — Morris helps validate the result

Problem: "Closest Binary Search Tree Value" (LC 270)
═══════════════════════════════════════════════════════
Pattern: Morris Inorder, track running minimum difference
Time: O(n), Space: O(1)
```

---

## 13. Comparison with Other Traversal Methods

### 13.1 Detailed Comparison

```
TRAVERSAL METHOD COMPARISON
════════════════════════════

Feature              | Recursive    | Iterative    | Morris
─────────────────────┼──────────────┼──────────────┼────────────────
Extra space          | O(h)         | O(h)         | O(1)  ← WINNER
Code complexity      | Low          | Medium       | High
Modifies tree?       | No           | No           | Temporarily YES
Thread-safe?         | Yes          | Yes          | NO
All 3 orders easy?   | Yes          | Inorder easy | Postorder hard
Early termination    | Yes (tricky) | Yes (easy)   | Yes (easy)
Concurrent reads?    | Safe         | Safe         | UNSAFE
Cache performance    | Poor (stack) | Medium       | Better (local)

When to use Morris:
  ✓ Memory-constrained environments (embedded systems)
  ✓ Very deep trees (avoid stack overflow)
  ✓ BST problems requiring O(1) space
  ✓ Interview problems asking for O(1) space traversal

When NOT to use Morris:
  ✗ Concurrent or multi-threaded environments
  ✗ Read-only trees (you can't modify structure)
  ✗ When code clarity > performance
  ✗ Postorder needed AND simplicity is required
```

### 13.2 Stack Depth Problem

```
Recursive traversal on a skewed tree with 100,000 nodes:

    Stack depth = 100,000 frames
    Each frame ≈ 64 bytes
    Total stack usage ≈ 6.4 MB

Typical default stack sizes:
    Linux:   8 MB
    macOS:   8 MB
    Windows: 1 MB

→ Risk of STACK OVERFLOW on deep skewed trees!

Morris Traversal:
    Stack depth = 0 (no recursion)
    Extra memory = 3 pointers ≈ 24 bytes
    → Zero overflow risk, works on any depth tree
```

---

## 14. Mental Models & Expert Intuition

### 14.1 The "Breadcrumb" Mental Model

Think of Morris Traversal like exploring a cave system:

```
STANDARD TRAVERSAL (with map/stack):
  → You carry a map (stack) that records where you've been
  → Map grows proportional to cave depth
  → Safe but heavy

MORRIS TRAVERSAL (breadcrumbs):
  → You leave breadcrumbs (threads) in the cave itself
  → Each breadcrumb points you back to the right path
  → You pick up breadcrumbs as you return (restore tree)
  → Your pockets stay empty (O(1) space) regardless of cave depth
```

### 14.2 The "Two-Phase" Mental Model

Every node in Morris Traversal is processed in two phases:

```
PHASE 1 (Preparation):
  - Arrive at node for the first time
  - Create a thread in predecessor
  - Descend into left subtree

PHASE 2 (Execution):
  - Arrive via thread (return visit)
  - Remove the thread
  - Visit the node
  - Proceed to right subtree
```

Nodes with **no left child** collapse to a single phase: visit and proceed right.

### 14.3 Invariant to Always Verify

When reading your own Morris code or debugging, verify this invariant holds:

> **At any point in time, at most one thread exists per ancestor path.**

If multiple threads exist to the same node, you have a bug.

### 14.4 The Amortized Argument (For Interviews)

A common interview follow-up: *"Finding the predecessor takes O(log n) for balanced trees — doesn't that make it O(n log n)?"*

**The expert answer:**

"The finding-predecessor operation is **amortized O(1)** across all nodes. Each edge in the tree is traversed at most twice in total: once forward (when creating a thread) and once backward (when the thread guides us back). The total work for all predecessor-finding is bounded by O(2n) = O(n). This is an amortized analysis — the expensive steps are paid for by the cheap steps."

### 14.5 Pattern Recognition Cues

When should your brain immediately think "Morris Traversal"?

```
CUE WORDS IN PROBLEM STATEMENT:
  "O(1) extra space"           → Morris
  "without using stack"        → Morris
  "constant memory"            → Morris
  "in-place traversal"         → Morris

PROBLEM TYPES:
  BST + O(1) space             → Morris Inorder
  Kth smallest in BST          → Morris Inorder + counter
  Two nodes swapped in BST     → Morris + two-pointer violation tracking
  Validate BST + O(1)          → Morris Inorder + prev tracking
```

### 14.6 Cognitive Framework — Building Intuition

```
CHUNKING THE ALGORITHM (Cognitive Science Principle):

Chunk 1: "How do I know if a node has been prepared?"
    → Check if its predecessor has a thread to it
    → Thread exists = left subtree already processed

Chunk 2: "How do I find my way back up without a stack?"
    → The thread in the predecessor points back to me

Chunk 3: "How do I restore the tree?"
    → When I detect a thread (return visit), I immediately remove it

These three chunks compose the entire algorithm.
Master each chunk independently, then combine.
```

### 14.7 The "Thread Lifecycle" Diagram

```
THREAD LIFECYCLE FOR A SINGLE NODE X:

Time 0:       X arrives as current
              X.left != NULL
              predecessor found (P)
              P.right == NULL
              ┌──────────────┐
              │ THREAD BORN  │  P.right = X
              └──────────────┘
              current = X.left (descend)

              ... time passes, left subtree traversed ...

Time 1:       current arrives at X again (via thread from P)
              predecessor found again (P)
              P.right == X  ← thread detected
              ┌──────────────┐
              │ THREAD DIES  │  P.right = NULL
              └──────────────┘
              X is visited
              current = X.right

LIFESPAN of thread P→X:
  Created when X is first visited
  Destroyed when X is revisited
  Duration: exactly as long as X's left subtree takes to traverse
```

---

## Appendix: Quick Reference Summary

```
MORRIS TRAVERSAL QUICK REFERENCE
══════════════════════════════════

Three rules for INORDER:
  1. current.left == NULL → VISIT, go right
  2. pred.right == NULL   → Create thread, go left
  3. pred.right == current→ Remove thread, VISIT, go right

PREORDER changes: move VISIT from rule 3 to rule 2
POSTORDER changes: on return visit, reverse-visit right spine

Complexity:
  Time:  O(n) always
  Space: O(1) always

Key Insight:
  n+1 NULL pointers exist in a tree of n nodes.
  Morris borrows these to store navigation information
  (threads) and returns them before finishing.

When to use:
  Memory constraints + tree traversal → Morris

When to avoid:
  Concurrent access, read-only trees, postorder simplicity needed
```

---

*End of Morris Traversal Complete Guide*

> **Expert Wisdom:** The beauty of Morris Traversal is its philosophy — when you lack external resources (a stack), you find resources within the problem itself (NULL pointers). This mindset — "what exists in the problem that I can temporarily repurpose?" — is a hallmark of top-tier algorithmic thinking. Carry this lens into every problem you face.

Now let me write the comprehensive Morris Traversal guide as a `.md` file:Here is your complete Morris Traversal guide. Here's what it covers end-to-end:

**Structure of the Guide:**

The guide is built in a deliberate learning sequence — no concept is used before it's defined. Every term (predecessor, thread, successor, NULL pointer count, right spine) is explained with diagrams before the algorithm uses it.

**What Makes This Guide Deep:**

- **The n+1 NULL pointers insight** — the mathematical reason Morris is even possible. A tree of n nodes always has exactly n+1 unused pointer slots, which Morris borrows.
- **The state machine view** — every node has exactly two states (first visit / return visit), and the thread is the mechanism that distinguishes them.
- **Amortized O(n) proof** — explained in plain language so you can defend it in an interview when challenged.
- **Postorder's reverse spine trick** — the hardest variant, fully traced step-by-step with the dummy node.

**Language-Specific Notes:**

- **C** — cleanest imperative style, `static` helper for reverse-visit isolation
- **Go** — idiomatic slices, bonus utilities `KthSmallestInBST` and `ValidateBST` with O(1) space
- **Rust** — raw pointers with safety rationale explained, includes `recover_bst` (LeetCode 99 pattern) and proper `Box::into_raw`/`Box::from_raw` memory management

**Expert Insight to Carry Forward:** The deepest lesson is the *repurposing mindset* — when you lack external resources (a stack), look for latent structure *within the problem itself* (the NULL pointers). This is what separates top-tier algorithmic thinkers from average ones.

Got it. I can access the raw content. I've read the entire document. Let me now do a **complete, surgical audit** of every error — diagrams, logic, and all three language implementations.

---

## Full Bug Report — Morris Traversal Guide

---

## 🔴 BUG 1 — Section 1.3: Wrong Recursive Inorder Call Stack

This is the exact error you already spotted in the previous conversation. It is present in the document.

```
DOCUMENT SHOWS (WRONG):
    inorder(A)
        inorder(B)
            inorder(D)
            visit D
            inorder(E)     ← E called BEFORE visit B
            visit E
        visit B            ← B visited AFTER both children
        inorder(C)
            visit C
    visit A                ← A visited at the very end
```

```
CORRECT:
    inorder(A)
        inorder(B)
            inorder(D)
                visit D
            visit B        ← visit B BETWEEN left(D) and right(E)
            inorder(E)
                visit E
        visit A            ← visit A BEFORE entering right subtree C
        inorder(C)
            visit C
```

---

## 🔴 BUG 2 — Section 5.4: Thread Visualization is Wrong

```
DOCUMENT SHOWS:
        4 ←─────────────── thread from 3
       / \
      2 ←─── thread from 1
     / \  \
    1   3   (thread 1→2)      ← shows node 2 with a THIRD child
     \
      (thread 1→2)            ← label appears TWICE, contradicts itself
```

**Problems:**
- Node 2 appears to have three children: `1`, `3`, and something unnamed with `\  \`
- The label `(thread 1→2)` appears in two places, which is contradictory
- At step 1, only thread `3→4` exists. At step 2, thread `1→2` is also created. Showing both simultaneously without timestamping is misleading

**Correct thread state after step 1 and step 2:**

```
After Step 1 (current was 4, thread 3→4 created):
        4
       / \
      2   6
     / \ / \
    1  3 5  7
        ↑
    3.right = 4  ← thread arrow goes FROM 3 TO 4

After Step 2 (current was 2, thread 1→2 created):
        4
       / \
      2   6
     / \ / \
    1  3 5  7
    ↑   ↑
1.right=2  3.right=4  ← both threads exist simultaneously at this moment
```

---

## 🔴 BUG 3 — C Code: `reverse_right` Corrupts the Tree

This is the most critical code bug. Inside `reverse_right`, the last line is:

```c
from->right = NULL;   ← THIS IS WRONG
```

**What it should be:** The last node's right pointer (`to->right`) needs to be nulled — NOT `from->right`.

**What actually happens — traced step by step:**

```
Call: reverse_right(node2, node3)
      (node2.right = node3 originally — node3 is node2's real right child)

After first reversal loop:
  node2.right = node3  ← UNCHANGED (reversal never touches it)
  node3.right = node2  ← set by loop

After re-reversal loop:
  node2.right = node3  ← still unchanged
  node3.right = node2  ← still has the back-pointer

Then: from->right = NULL
  → node2.right = NULL   ← DESTROYS node2's link to its real right child node3!

Then in morris_postorder: predecessor->right = NULL
  → node3.right = NULL
```

**Final state:**

```
BEFORE postorder:          AFTER C postorder:
      4                          4
     / \                        /
    2   6          →           2       ← 4.right destroyed
   / \ / \                    /         ← 2.right destroyed
  1  3 5  7                  1           ← nodes 3,5,6,7 are ORPHANED
```

> The C postorder produces **correct output** but **destroys the tree**. If you call `morris_inorder` or `free_tree` after postorder, the tree is already corrupted. Node 3, 5, 6, 7 become **memory leaks**.

**Go and Rust do NOT have this bug** — they do not set `from->right = NULL` inside the helper, and the outer code `predecessor.Right = nil` correctly repairs only the last pointer.

---

## 🔴 BUG 4 — Go/Rust/C: Early Return Without Thread Cleanup

**Affects:** `KthSmallestInBST` (Go), `ValidateBST` (Go), `kth_smallest` (Rust)

When these functions return early (after finding the k-th element or the first BST violation), they abandon the traversal mid-way — leaving **threads (dangling right pointers pointing to ancestors) still attached to the tree**.

```
Example: KthSmallestInBST(root, 2) on tree [1,2,3,4,5,6,7]

Step 1: thread created → 3.right = 4
Step 2: thread created → 1.right = 2
Step 3: visit 1 (count=1)
Step 4: return visit at 2, thread 1.right removed, visit 2 (count=2=k)

→ EARLY RETURN HERE

But thread 3.right = 4 is STILL in the tree!
If you now call morris_inorder on the same tree, it enters an
infinite loop: ...→ 3 → 4 → find pred of 4 → reaches 3 → 3.right=4
(thread already exists) → Case B2: removes thread → 4 visited →
goes right → ... → seems to work, BUT any future use is undefined.
```

**The correct fix** — use a boolean flag and complete the traversal:

```go
// Go — correct early stopping without tree corruption
func KthSmallestInBST(root *Node, k int) int {
    current := root
    count := 0
    result := -1

    for current != nil {
        if current.Left == nil {
            count++
            if count == k { result = current.Data }
            current = current.Right
        } else {
            predecessor := current.Left
            for predecessor.Right != nil && predecessor.Right != current {
                predecessor = predecessor.Right
            }
            if predecessor.Right == nil {
                predecessor.Right = current
                current = current.Left
            } else {
                predecessor.Right = nil
                count++
                if count == k { result = current.Data }
                current = current.Right
            }
        }
    }
    return result  // traversal ALWAYS completes — no dangling threads
}
```

---

## 🔴 BUG 5 — Go `ValidateBST`: Wrong Sentinel Value

```go
prev := -1 << 62   // ← WRONG
```

**Problems:**

1. `-1 << 62` equals `-4611686018427387904` — this is NOT `math.MinInt`. The true minimum int64 is `-1 << 63`. So the sentinel is half as negative as intended.

2. If a BST node has value exactly `-1 << 62`, the first check `val <= prev` becomes `-1<<62 <= -1<<62` → `true` → returns `false` (claims BST is invalid, even though it's the very first node).

3. `prev` has type `int` (platform-dependent). On 32-bit platforms, `-1 << 62` causes a shift overflow.

**Correct approaches:**

```go
// Option A: Use math package
import "math"
prev := math.MinInt

// Option B: Use pointer sentinel (most correct)
var prev *int = nil
// then: if prev != nil && val <= *prev { return false }
//       prev = &val
```

---

## 🔴 BUG 6 — Rust `main`: `recover_bst` Test Case is Already a Valid BST

```rust
let bad = Node::new(3);
(*bad).left  = Node::new(2);
(*bad).right = Node::new(4);
(*(*bad).left).left = Node::new(1);
```

This builds:
```
    3
   / \
  2   4
 /
1
```

Inorder: `1 → 2 → 3 → 4` — **this is already a valid BST**. No nodes are swapped. `recover_bst` finds zero violations and does nothing. The test output `[1, 2, 3, 4]` is correct but for the wrong reason — it proves nothing.

**What the test should look like** (nodes 1 and 3 genuinely swapped):

```rust
// Wrong BST: 1 and 3 swapped
//     1     ← should be 3
//    / \
//   2   4
//  /
// 3          ← should be 1
let bad = Node::new(1);         // ← value 1 where 3 should be
(*bad).left  = Node::new(2);
(*bad).right = Node::new(4);
(*(*bad).left).left = Node::new(3);  // ← value 3 where 1 should be

// Inorder of this bad tree: 3 → 2 → 1 → 4  (two violations detected)
// After recover_bst: 1 → 2 → 3 → 4  ✓
```

---

## 🟡 BUG 7 — Section 7.3 Postorder Algorithm Description Contradicts the Code

**Algorithm description says:**
```
ELSE: (predecessor.right == current)
    REMOVE THREAD: predecessor.right = NULL    ← thread removed FIRST
    REVERSE_VISIT(current.left to predecessor)
    current = current.right
```

**Actual code does (all 3 languages):**
```c
reverse_right(current->left, predecessor);  // REVERSE_VISIT first
predecessor->right = NULL;                  // REMOVE THREAD second
current = current->right;
```

**Why it matters:** The description implies thread removal before reverse-visiting. The code does reverse-visiting while the thread is still present. These are semantically different states. In the correct implementation (code), the thread is still live during the reverse visit, which is fine because `reverse_visit` only walks `current.left → predecessor`, never touching `predecessor.right`. But a student reading the description and writing code from it would do the wrong thing.

---

## Complete Bug Summary

```
┌─────┬──────────────────────────────────────┬────────────┬──────────────┐
│  #  │  Bug                                 │  Severity  │  Affects     │
├─────┼──────────────────────────────────────┼────────────┼──────────────┤
│  1  │  Inorder call stack diagram wrong    │  🔴 High   │  Section 1.3 │
│  2  │  Thread visualization wrong          │  🔴 High   │  Section 5.4 │
│  3  │  C: from->right=NULL corrupts tree   │  🔴 High   │  C postorder │
│  4  │  Early return leaves threads alive   │  🔴 High   │  Go, Rust    │
│  5  │  Go: wrong sentinel -1<<62           │  🔴 High   │  Go Validate │
│  6  │  Rust: recover_bst test is valid BST │  🔴 High   │  Rust main   │
│  7  │  Postorder description ≠ code order  │  🟡 Medium │  Section 7.3 │
└─────┴──────────────────────────────────────┴────────────┴──────────────┘
```

---

## Expert Insight on the Root Pattern

Almost all bugs share a common cognitive trap: **"it produces the correct OUTPUT so it must be correct."**

- The C `reverse_right` gives right output but destroys the tree.
- The early-return functions give right answers but corrupt the structure.
- The `recover_bst` test produces `[1,2,3,4]` but never tests the actual logic.

> This is what separates novice code from expert code: **an expert also asks "what is the state of the system after this operation?"**, not just "did it return the right value?" Always verify invariants both before AND after a function call, especially in algorithms that temporarily mutate shared state.