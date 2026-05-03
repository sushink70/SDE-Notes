# BFS on Trees — A Complete, In-Depth Guide
### From First Principles to Expert Mastery

---

## Table of Contents

1. [Mental Foundation — Before Any Code](#1-mental-foundation)
2. [What is a Tree? (Precise Definition)](#2-what-is-a-tree)
3. [What is BFS? (Breadth-First Search)](#3-what-is-bfs)
4. [The Queue — BFS's Heartbeat](#4-the-queue)
5. [Level-Order Traversal — The Core of Tree BFS](#5-level-order-traversal)
6. [Step-by-Step BFS Mechanics (Traced by Hand)](#6-step-by-step-bfs-mechanics)
7. [ASCII Architecture & Diagrams](#7-ascii-architecture--diagrams)
8. [BFS Algorithm Flowchart (Text-Based)](#8-bfs-algorithm-flowchart)
9. [Variants of Tree BFS](#9-variants-of-tree-bfs)
10. [Classic Problems Solved with Tree BFS](#10-classic-problems-solved-with-tree-bfs)
11. [Time & Space Complexity Analysis](#11-time--space-complexity-analysis)
12. [Implementation in C](#12-implementation-in-c)
13. [Implementation in Go](#13-implementation-in-go)
14. [Implementation in Rust](#14-implementation-in-rust)
15. [Common Mistakes & Pitfalls](#15-common-mistakes--pitfalls)
16. [Pattern Recognition — Mental Models](#16-pattern-recognition--mental-models)
17. [Deliberate Practice Problems](#17-deliberate-practice-problems)

---

## 1. Mental Foundation

> *"Before you code, understand. Before you understand, visualize. Before you visualize, define."*

**Cognitive Principle: Chunking**
Your brain learns faster when concepts are chunked into units. BFS on trees has exactly 3 chunks:
- **What** you are traversing (a Tree)
- **How** you traverse it (a Queue)
- **Why** the order matters (level-by-level = shortest path first)

Internalize these three chunks separately. Then merge them. This is how experts build intuition — not by memorizing code, but by owning the mental model.

---

## 2. What is a Tree?

A **Tree** is a hierarchical, connected, acyclic data structure. Let us define each word precisely:

- **Hierarchical**: There is a top node (called the **root**). All other nodes descend from it.
- **Connected**: Every node can be reached from the root.
- **Acyclic**: There are no loops. You can never start at a node and return to it by following edges.

### Key Vocabulary (Every Term Defined)

| Term | Definition |
|------|-----------|
| **Root** | The topmost node. Has no parent. The starting point of the tree. |
| **Node** | A single element in the tree. Holds data + references to children. |
| **Edge** | The connection between a parent and a child node. |
| **Parent** | A node that has one or more children. |
| **Child** | A node that descends directly from another node (its parent). |
| **Leaf** | A node with no children. The "end" of a branch. |
| **Level** | The distance (in edges) from the root. Root is Level 0. |
| **Height** | The number of edges on the longest path from root to any leaf. |
| **Depth** | The number of edges from the root to a specific node. |
| **Sibling** | Nodes that share the same parent. |
| **Subtree** | A node and all its descendants, treated as its own tree. |
| **Ancestor** | Any node on the path from a given node up to the root. |
| **Descendant** | Any node reachable from a given node going downward. |
| **Binary Tree** | A tree where each node has at most 2 children (left, right). |
| **N-ary Tree** | A tree where each node can have up to N children. |
| **Complete Binary Tree** | All levels filled except possibly the last; last level filled left to right. |
| **Perfect Binary Tree** | All levels completely filled. |
| **Balanced Tree** | Height is O(log n). No branch is excessively deeper than another. |

### ASCII Tree Anatomy

```
Level 0:              [A]              <-- Root
                     /   \
Level 1:          [B]     [C]          <-- Children of A, siblings to each other
                 / \       \
Level 2:       [D] [E]     [F]         <-- D,E are children of B; F is child of C
              /
Level 3:   [G]                         <-- Leaf node (no children)

Nodes:  A, B, C, D, E, F, G
Edges:  A-B, A-C, B-D, B-E, C-F, D-G
Leaves: E, F, G  (no children)
Height of tree: 3 (root to G has 3 edges)
Depth of G: 3
Depth of C: 1
```

---

## 3. What is BFS?

**Breadth-First Search (BFS)** is a traversal strategy that explores a tree **level by level**, visiting all nodes at depth `d` before visiting any node at depth `d+1`.

### BFS vs DFS — The Core Distinction

Think of it this way:

```
DFS (Depth-First Search):
  "Go as deep as possible on one path, then backtrack."
  Like drilling a single borehole straight down, then trying another spot.

BFS (Breadth-First Search):
  "Explore all neighbors at current depth before going deeper."
  Like flood-filling water — it spreads evenly outward in all directions.
```

Visually, on this tree:

```
         [1]
        /   \
      [2]   [3]
      / \     \
    [4] [5]   [6]
```

**DFS Pre-order** visits: 1 → 2 → 4 → 5 → 3 → 6  (goes deep first)
**BFS Level-order** visits: 1 → 2 → 3 → 4 → 5 → 6  (level by level)

### Why Does BFS Matter for Trees?

BFS answers a specific class of questions elegantly:
- What is the **minimum number of levels** to reach a leaf? (Min depth)
- What nodes are at the **same level**?
- What is the **rightmost/leftmost** node at each level?
- What is the **level-order** representation of a tree?
- What is the **shortest path** (in terms of edges) from root to a target?

---

## 4. The Queue — BFS's Heartbeat

### What is a Queue?

A **Queue** is a linear data structure that follows **FIFO** — First In, First Out.

```
FIFO Analogy: A line of people at a ticket counter.
The first person to join the line is the first to be served.

  ENQUEUE (add to back)       DEQUEUE (remove from front)
         |                           |
         v                           v
  BACK [E]-[D]-[C]-[B]-[A] FRONT
         ^                           ^
     New arrivals               Served first
```

### Queue Operations

| Operation | Action | Time Complexity |
|-----------|--------|----------------|
| `enqueue(x)` | Add `x` to the back | O(1) |
| `dequeue()` | Remove from front, return it | O(1) |
| `peek()` | Look at front without removing | O(1) |
| `isEmpty()` | Check if queue has elements | O(1) |

### Why Queue for BFS?

This is the key insight. Let's think through it:

When you visit a node, you need to remember its children to visit them **later** (after finishing the current level). A queue does exactly this: children are enqueued, and because the queue is FIFO, all nodes enqueued at level `d` will be dequeued (processed) before any node at level `d+1`.

```
Property being enforced by Queue:
  "Nodes closer to the root are always processed before nodes farther away."

This is exactly level-order traversal.
```

---

## 5. Level-Order Traversal — The Core of Tree BFS

**Level-Order Traversal** means visiting every node level by level, left to right.

It is the most direct expression of BFS on a tree.

```
Tree:
         [10]              Level 0
        /    \
      [20]  [30]           Level 1
      / \      \
   [40][50]   [60]         Level 2

Level-order output: 10, 20, 30, 40, 50, 60
```

### The Universal BFS Template (Conceptual)

```
1. Create an empty Queue Q
2. Enqueue the root node into Q
3. While Q is not empty:
   a. Dequeue a node N from the front of Q
   b. Process (visit) node N
   c. If N has a left child, enqueue it
   d. If N has a right child, enqueue it
4. Done
```

This 4-step template is the skeleton. Every tree BFS problem is a variation of this.

---

## 6. Step-by-Step BFS Mechanics (Traced by Hand)

Let's trace BFS on this tree, step by step:

```
         [A]
        /   \
      [B]   [C]
      / \
    [D] [E]
```

### Execution Trace

```
STEP 0: Initialize
  Queue: [A]
  Visited: []

-------------------------------
STEP 1: Dequeue A
  Process: A
  A has left child B -> Enqueue B
  A has right child C -> Enqueue C
  Queue: [B, C]
  Visited: [A]

-------------------------------
STEP 2: Dequeue B
  Process: B
  B has left child D -> Enqueue D
  B has right child E -> Enqueue E
  Queue: [C, D, E]
  Visited: [A, B]

-------------------------------
STEP 3: Dequeue C
  Process: C
  C has no children
  Queue: [D, E]
  Visited: [A, B, C]

-------------------------------
STEP 4: Dequeue D
  Process: D
  D has no children
  Queue: [E]
  Visited: [A, B, C, D]

-------------------------------
STEP 5: Dequeue E
  Process: E
  E has no children
  Queue: []
  Visited: [A, B, C, D, E]

-------------------------------
STEP 6: Queue is empty. BFS complete.
  Final order: A -> B -> C -> D -> E
```

### Queue State Visualization (Over Time)

```
Time  | Queue State (Front -> Back) | Action
------|-----------------------------|--------------------------------
  0   | [A]                         | Start: enqueue root
  1   | [B, C]                      | Dequeue A, enqueue B, C
  2   | [C, D, E]                   | Dequeue B, enqueue D, E
  3   | [D, E]                      | Dequeue C (no children)
  4   | [E]                         | Dequeue D (no children)
  5   | []                          | Dequeue E (no children) -> DONE
```

---

## 7. ASCII Architecture & Diagrams

### Memory Layout of a Binary Tree Node

```
+------------------+
|   Binary Node    |
+------------------+
|   data : int     |  <-- The value stored
|   left : *Node   |  <-- Pointer to left child (NULL if none)
|   right: *Node   |  <-- Pointer to right child (NULL if none)
+------------------+

For N-ary Node:
+----------------------------+
|      N-ary Node            |
+----------------------------+
|   data    : int            |
|   children: []*Node        |  <-- Slice/array of child pointers
+----------------------------+
```

### How a Tree Lives in Memory (Heap-Allocated)

```
HEAP MEMORY:

  Addr 0x100         Addr 0x200         Addr 0x300
  +-----------+      +-----------+      +-----------+
  | data = 1  |      | data = 2  |      | data = 3  |
  | left=0x200|----> | left=0x400|      | left=NULL |
  | right=0x30|      | right=0x50|      | right=NULL|
  +-----------+      +-----------+      +-----------+
        |                  |   \
        '-> 0x300          |    '--------------.
                           v                    v
                     Addr 0x400           Addr 0x500
                     +-----------+        +-----------+
                     | data = 4  |        | data = 5  |
                     | left=NULL |        | left=NULL |
                     | right=NULL|        | right=NULL|
                     +-----------+        +-----------+

Tree structure (logical):
        [1]
       /   \
     [2]   [3]
     / \
   [4] [5]
```

### BFS Queue Architecture (During Execution)

```
Queue is a circular buffer or a linked list.
Let's show it as a dynamic array-like structure:

Initial:          FRONT                 BACK
                    |                    |
                  [ 1 | _ | _ | _ | _ ]
                    ^root

After processing 1, enqueue 2,3:
                  FRONT       BACK
                    |           |
                  [ _ | 2 | 3 | _ | _ ]
                          ^level 1

After processing 2, enqueue 4,5:
                  FRONT           BACK
                    |               |
                  [ _ | _ | 3 | 4 | 5 ]
                              ^level 2 mixed with 3

After processing 3 (no children):
                  FRONT     BACK
                    |         |
                  [ _ | _ | _ | 4 | 5 ]
                                 ^still level 2

After processing 4,5 (no children): Queue is empty -> DONE
```

### Level-Separator BFS Architecture

To track which nodes belong to which level, we use the **queue size snapshot**:

```
Snapshot Pattern:
  At the START of each level iteration,
  take queue.size() as the count of nodes AT THAT LEVEL.
  Process exactly that many nodes, then move to next level.

LEVEL 0:
  Queue snapshot size = 1
  Process: [1]
  Enqueue children of 1: [2, 3]
  Queue after level 0: [2, 3]

LEVEL 1:
  Queue snapshot size = 2
  Process: [2, 3]
  Enqueue children: [4, 5] (from 2), nothing (from 3)
  Queue after level 1: [4, 5]

LEVEL 2:
  Queue snapshot size = 2
  Process: [4, 5]
  No children enqueued
  Queue after level 2: []

Done. 3 levels processed.
```

---

## 8. BFS Algorithm Flowchart

### Text-Based Flowchart

```
+---------------------------------------+
|            BFS TREE START             |
+---------------------------------------+
                    |
                    v
+---------------------------------------+
| Is root NULL?                         |
+---------------------------------------+
    |               |
   YES              NO
    |               |
    v               v
 RETURN        Create Queue Q
               Enqueue root -> Q
                    |
                    v
+---------------------------------------+
|         Is Q empty?                   |
+---------------------------------------+
         |           |
        YES          NO
         |           |
         v           v
       END      Dequeue front node N
                    |
                    v
+---------------------------------------+
|         PROCESS node N                |
|   (print, compute, compare, etc.)     |
+---------------------------------------+
                    |
                    v
+---------------------------------------+
| Does N have a LEFT child?             |
+---------------------------------------+
    |               |
   YES              NO
    |               |
    v               |
Enqueue N.left      |
    |               |
    +<--------------+
    |
    v
+---------------------------------------+
| Does N have a RIGHT child?            |
+---------------------------------------+
    |               |
   YES              NO
    |               |
    v               |
Enqueue N.right     |
    |               |
    +<--------------+
    |
    v
+---------------------------------------+
|   Go back to "Is Q empty?" check      |
+---------------------------------------+
```

### Level-Aware BFS Flowchart

```
+---------------------------------------+
|     LEVEL-AWARE BFS START             |
+---------------------------------------+
                    |
                    v
        Enqueue root; level = 0
                    |
                    v
+---------------------------------------+
|         Is Q empty?                   |
+---------------------------------------+
    |               |
   YES              NO
    |               |
    v               v
  END       levelSize = Q.size()
            i = 0
                    |
                    v
+---------------------------------------+
|         i < levelSize?                |
+---------------------------------------+
    |               |
   YES              NO
    |               |
    v               v
Dequeue N    level++ -> back to Q empty check
Process N
Enqueue N's children
i++
    |
    v
Back to "i < levelSize?" check
```

---

## 9. Variants of Tree BFS

### 9.1 Standard Level-Order Traversal

Visit every node level by level, left to right.

**Output**: A flat list of all values in BFS order.

```
Tree:      [1]
          /   \
        [2]   [3]
        / \
      [4] [5]

Output: [1, 2, 3, 4, 5]
```

---

### 9.2 Level-by-Level Grouping (2D Output)

Group nodes by their level. Output is a list of lists.

```
Tree: same as above

Output: [[1], [2, 3], [4, 5]]
```

**When to use**: When you need per-level statistics (max, min, average at each level).

---

### 9.3 Zigzag (Spiral) Level-Order

Even levels go left-to-right. Odd levels go right-to-left.

```
Tree:
         [1]
        /   \
      [2]   [3]
      / \   / \
    [4][5][6] [7]

Level 0 (L->R): [1]
Level 1 (R->L): [3, 2]
Level 2 (L->R): [4, 5, 6, 7]

Output: [[1], [3, 2], [4, 5, 6, 7]]
```

**Technique**: Use a flag `leftToRight`. On each level, if `leftToRight=false`, reverse the collected level array before appending.

---

### 9.4 Right-Side View (Rightmost Node at Each Level)

Return only the **last** node visible when the tree is viewed from the right.

```
Tree:
         [1]
        /   \
      [2]   [3]
        \
        [5]

Right-side view: [1, 3, 5]

Explanation:
  Level 0: see [1] -> 1
  Level 1: see [2, 3] -> rightmost is 3
  Level 2: see [5] -> 5
```

**Technique**: In level-aware BFS, after processing each level, record the **last** dequeued node.

---

### 9.5 Left-Side View

Same as right-side view, but record the **first** dequeued node at each level.

---

### 9.6 Average of Levels

Compute the arithmetic mean of node values at each level.

```
Tree:
         [1]
        /   \
      [2]   [3]

Level 0: avg = 1.0
Level 1: avg = (2+3)/2 = 2.5

Output: [1.0, 2.5]
```

---

### 9.7 Maximum Width of Tree

Find the level with the most nodes. Return that count.

```
Tree:
         [1]
        /   \
      [2]   [3]
      / \     \
    [4] [5]   [6]

Level 0: width = 1
Level 1: width = 2
Level 2: width = 3  <-- maximum

Answer: 3
```

---

### 9.8 Minimum Depth (Shortest Root-to-Leaf Path)

BFS naturally finds this because it reaches the first leaf at the shallowest level.

```
Tree:
         [1]
        /   \
      [2]   [3]
              \
              [4]

BFS reaches [2] at level 1 (it's a leaf!) -> min depth = 2
(depth is counted as number of nodes, not edges: root [1] + leaf [2] = 2)
```

> **Key Insight**: DFS finds minimum depth too, but has to explore ALL paths. BFS finds the first leaf and stops immediately — it's optimal here.

---

### 9.9 Connect Nodes at Same Level (Next Right Pointer)

In some tree problems, you need to connect all nodes at the same level using a `next` pointer.

```
Before:
         [1]       -> NULL
        /   \
      [2]   [3]    -> NULL
      / \     \
    [4] [5]   [6]  -> NULL

After BFS connection:
         [1]       -> NULL
        /   \
      [2] -> [3]  -> NULL
      / \      \
    [4]->[5] -> [6] -> NULL
```

**Technique**: During level-aware BFS, link `prev.next = current` as you process each level.

---

### 9.10 Serialize / Deserialize a Tree Using BFS

Convert a tree to a string representation (for storage/transmission) and back.

```
Tree:
     [1]
    /   \
  [2]   [3]
  / \
[4] [5]

BFS Serialization: "1,2,3,4,5,#,#,#,#"
   # = NULL placeholder

This is the exact format LeetCode uses internally for tree problems.
```

---

## 10. Classic Problems Solved with Tree BFS

### Problem Category Map

```
+--------------------------------------------------+
|           TREE BFS PROBLEM CATEGORIES            |
+--------------------------------------------------+
|                                                  |
|  LEVEL INFO          STRUCTURE          PATH     |
|  -----------         ---------          ----     |
|  Level averages      Max width          Min depth|
|  Level max/min       Connect nodes      Cousins  |
|  Level grouping      Serialize/Deser.   Level of |
|  Zigzag order        Complete tree?     a node   |
|                      Count levels                |
|                                                  |
|  VIEW PROBLEMS       COMPARISON                  |
|  -------------       ----------                  |
|  Right side view     Same tree?                  |
|  Left side view      Symmetric tree?             |
|  Bottom view         Mirror?                     |
|  Top view                                        |
+--------------------------------------------------+
```

---

### Problem 10.1: Binary Tree Level Order Traversal (Grouped)

**Input**: Root of tree  
**Output**: List of lists, each inner list = one level

**Algorithm**:
```
1. Enqueue root
2. While queue not empty:
   a. levelSize = queue.size()
   b. Create currentLevel = []
   c. For i in 0..levelSize:
      - node = dequeue
      - currentLevel.append(node.val)
      - Enqueue node's children
   d. result.append(currentLevel)
3. Return result
```

---

### Problem 10.2: Check if Tree is Symmetric (Mirror)

A tree is symmetric if its left and right subtrees are mirror images.

```
Symmetric:              Not Symmetric:
       [1]                    [1]
      /   \                  /   \
    [2]   [2]              [2]   [2]
    / \   / \              / \     \
  [3][4][4][3]           [3][4]   [3]
```

**BFS Approach**: At each level, check if the array of values reads the same forwards and backwards (is a palindrome).

---

### Problem 10.3: Find Minimum Depth

**Key Distinction**:
- Minimum depth = shortest path from root to a **leaf node**
- A node with only one child is NOT a leaf!

```
Tree:
       [1]
      /
    [2]

Min depth = 2 (path: 1->2, and 2 is a leaf)
NOT 1! Because [1] has a child, it's not a leaf.
```

**BFS stops the moment it finds a node with NO children** — that's the min depth.

---

### Problem 10.4: Cousins in Binary Tree

Two nodes are **cousins** if they are at the same level but have different parents.

```
       [1]
      /   \
    [2]   [3]
    / \     \
  [4] [5]   [6]

Nodes 4 and 6: same level (level 2), different parents (2 and 3) -> COUSINS
Nodes 4 and 5: same level (level 2), same parent (2) -> NOT cousins (siblings)
```

**BFS Approach**: Track `(node, parent, level)` as you traverse. For the target nodes, compare their levels and parents.

---

### Problem 10.5: Binary Tree Right Side View

**BFS Approach**: Level-aware BFS. At the end of processing each level, the last dequeued node is the rightmost — add it to result.

---

### Problem 10.6: Maximum Level Sum

Find the level whose sum of node values is maximum.

**BFS Approach**: Level-aware BFS. For each level, sum the values. Track max sum and corresponding level.

---

## 11. Time & Space Complexity Analysis

### Time Complexity

```
Every node is:
  - Enqueued exactly once: O(1)
  - Dequeued exactly once: O(1)
  - Processed exactly once: O(1)

For a tree with N nodes:
  Total time = O(N)
```

**T(n) = O(N)** — Linear in the number of nodes. This is optimal. You cannot traverse a tree in less than O(N) since you must visit all nodes.

---

### Space Complexity

The space used by BFS is determined by the **maximum size the queue ever reaches**.

```
For a BALANCED binary tree:
  The widest level has the most nodes.
  In a perfect binary tree with N nodes,
  the last level has ceil(N/2) nodes.
  
  So max queue size = O(N/2) = O(N)

For a SKEWED (linear) tree:
           [1]
             \
             [2]
               \
               [3]
  
  The queue never holds more than 1 node at a time.
  Space = O(1) in terms of queue, O(H) for recursion (if used).

General Space: O(W) where W is the maximum width of the tree.
Worst case W = O(N/2) = O(N) for a complete/perfect binary tree.
```

### Complexity Summary Table

```
+--------------------+------------------+------------------+
| Scenario           | Time Complexity  | Space Complexity |
+--------------------+------------------+------------------+
| BFS on any tree    | O(N)             | O(W) = O(N) worst|
| Balanced binary    | O(N)             | O(N/2) = O(N)    |
| Skewed tree        | O(N)             | O(1) queue size  |
| Level grouping     | O(N)             | O(N) for output  |
+--------------------+------------------+------------------+
W = max width of tree
N = number of nodes
```

---

## 12. Implementation in C

### Node Structure and BFS Core

```c
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

/* ============================================================
   SECTION 1: Binary Tree Node Definition
   ============================================================ */

/*
 * TreeNode: A single node in a binary tree.
 *
 * Fields:
 *   val   - the integer value stored in this node
 *   left  - pointer to the left child (NULL if none)
 *   right - pointer to the right child (NULL if none)
 */
typedef struct TreeNode {
    int val;
    struct TreeNode *left;
    struct TreeNode *right;
} TreeNode;

/*
 * newNode: Allocate and initialize a new TreeNode.
 *
 * Parameters:
 *   val - integer value for the node
 *
 * Returns:
 *   Pointer to the newly created node.
 */
TreeNode *newNode(int val) {
    TreeNode *node = (TreeNode *)malloc(sizeof(TreeNode));
    if (!node) {
        fprintf(stderr, "Memory allocation failed\n");
        exit(EXIT_FAILURE);
    }
    node->val = val;
    node->left = NULL;
    node->right = NULL;
    return node;
}


/* ============================================================
   SECTION 2: Queue for BFS
   
   We implement a simple queue using a dynamic array.
   
   Why not use a linked-list queue here?
   Arrays give better cache locality (data is contiguous in memory),
   which is faster for BFS in practice.
   
   We use a circular buffer-style queue with head and tail indices.
   ============================================================ */

#define MAX_QUEUE_SIZE 10000

typedef struct Queue {
    TreeNode *data[MAX_QUEUE_SIZE]; /* Array of node pointers */
    int front;                      /* Index of the front element */
    int back;                       /* Index where next element is inserted */
    int size;                       /* Current number of elements */
} Queue;

/* Initialize a queue to empty state */
void initQueue(Queue *q) {
    q->front = 0;
    q->back  = 0;
    q->size  = 0;
}

/* Check if queue is empty */
bool isEmpty(Queue *q) {
    return q->size == 0;
}

/* Enqueue: add a node pointer to the back of the queue */
void enqueue(Queue *q, TreeNode *node) {
    if (q->size == MAX_QUEUE_SIZE) {
        fprintf(stderr, "Queue overflow\n");
        exit(EXIT_FAILURE);
    }
    q->data[q->back] = node;
    q->back = (q->back + 1) % MAX_QUEUE_SIZE;
    q->size++;
}

/* Dequeue: remove and return the front node pointer */
TreeNode *dequeue(Queue *q) {
    if (isEmpty(q)) {
        fprintf(stderr, "Queue underflow\n");
        exit(EXIT_FAILURE);
    }
    TreeNode *node = q->data[q->front];
    q->front = (q->front + 1) % MAX_QUEUE_SIZE;
    q->size--;
    return node;
}


/* ============================================================
   SECTION 3: Basic BFS — Level Order Traversal (Flat Output)
   
   Visits every node level by level, prints values.
   ============================================================ */

/*
 * bfsLevelOrder:
 *   Performs BFS on the tree rooted at `root`.
 *   Prints all node values in level-order (BFS order).
 *
 * Algorithm:
 *   1. Enqueue root.
 *   2. While queue is not empty:
 *      a. Dequeue node N.
 *      b. Print N->val.
 *      c. Enqueue N->left if not NULL.
 *      d. Enqueue N->right if not NULL.
 */
void bfsLevelOrder(TreeNode *root) {
    if (root == NULL) return;

    Queue q;
    initQueue(&q);
    enqueue(&q, root);

    printf("BFS Level Order: ");
    while (!isEmpty(&q)) {
        TreeNode *node = dequeue(&q);
        printf("%d ", node->val);

        if (node->left)  enqueue(&q, node->left);
        if (node->right) enqueue(&q, node->right);
    }
    printf("\n");
}


/* ============================================================
   SECTION 4: Level-Aware BFS — Grouped by Level
   
   Tracks which level each node belongs to.
   Uses the "snapshot size" technique:
     - At the start of each level, record queue size.
     - Process exactly that many nodes (they all belong to same level).
   ============================================================ */

/*
 * bfsGroupedByLevel:
 *   Performs level-aware BFS.
 *   Prints nodes grouped by their level.
 *
 *   Example output:
 *     Level 0: 1
 *     Level 1: 2 3
 *     Level 2: 4 5 6
 */
void bfsGroupedByLevel(TreeNode *root) {
    if (root == NULL) return;

    Queue q;
    initQueue(&q);
    enqueue(&q, root);

    int level = 0;
    while (!isEmpty(&q)) {
        /*
         * SNAPSHOT: How many nodes are in the queue RIGHT NOW?
         * All of them are at the current level.
         * We will process exactly this many, then increment level.
         */
        int levelSize = q.size;

        printf("Level %d: ", level);
        for (int i = 0; i < levelSize; i++) {
            TreeNode *node = dequeue(&q);
            printf("%d ", node->val);

            if (node->left)  enqueue(&q, node->left);
            if (node->right) enqueue(&q, node->right);
        }
        printf("\n");
        level++;
    }
}


/* ============================================================
   SECTION 5: Right Side View
   
   At each level, print only the LAST node processed.
   This is the node visible when tree is viewed from the right.
   ============================================================ */

void bfsRightSideView(TreeNode *root) {
    if (root == NULL) return;

    Queue q;
    initQueue(&q);
    enqueue(&q, root);

    printf("Right Side View: ");
    while (!isEmpty(&q)) {
        int levelSize = q.size;
        TreeNode *lastNode = NULL;

        for (int i = 0; i < levelSize; i++) {
            TreeNode *node = dequeue(&q);
            lastNode = node; /* Keep updating; last value = rightmost */

            if (node->left)  enqueue(&q, node->left);
            if (node->right) enqueue(&q, node->right);
        }

        if (lastNode) printf("%d ", lastNode->val);
    }
    printf("\n");
}


/* ============================================================
   SECTION 6: Minimum Depth
   
   The minimum depth = number of nodes on the shortest root-to-leaf path.
   BFS is PERFECT for this: first leaf we encounter IS the minimum.
   We stop immediately — no need to traverse the entire tree.
   ============================================================ */

int bfsMinDepth(TreeNode *root) {
    if (root == NULL) return 0;

    Queue q;
    initQueue(&q);
    enqueue(&q, root);

    int depth = 1; /* Root is at depth 1 */

    while (!isEmpty(&q)) {
        int levelSize = q.size;

        for (int i = 0; i < levelSize; i++) {
            TreeNode *node = dequeue(&q);

            /*
             * A LEAF node has no children.
             * In BFS, the first leaf we encounter is at the minimum depth.
             * Return immediately!
             */
            if (node->left == NULL && node->right == NULL) {
                return depth;
            }

            if (node->left)  enqueue(&q, node->left);
            if (node->right) enqueue(&q, node->right);
        }
        depth++;
    }
    return depth;
}


/* ============================================================
   SECTION 7: Maximum Width of Tree
   
   Width of a level = number of nodes at that level.
   Return the maximum width across all levels.
   ============================================================ */

int bfsMaxWidth(TreeNode *root) {
    if (root == NULL) return 0;

    Queue q;
    initQueue(&q);
    enqueue(&q, root);

    int maxWidth = 0;

    while (!isEmpty(&q)) {
        int levelSize = q.size;

        /* Update max if this level has more nodes */
        if (levelSize > maxWidth) maxWidth = levelSize;

        for (int i = 0; i < levelSize; i++) {
            TreeNode *node = dequeue(&q);
            if (node->left)  enqueue(&q, node->left);
            if (node->right) enqueue(&q, node->right);
        }
    }
    return maxWidth;
}


/* ============================================================
   SECTION 8: Level Sum & Average
   ============================================================ */

void bfsLevelAverages(TreeNode *root) {
    if (root == NULL) return;

    Queue q;
    initQueue(&q);
    enqueue(&q, root);

    int level = 0;

    while (!isEmpty(&q)) {
        int levelSize = q.size;
        long long sum = 0;

        for (int i = 0; i < levelSize; i++) {
            TreeNode *node = dequeue(&q);
            sum += node->val;

            if (node->left)  enqueue(&q, node->left);
            if (node->right) enqueue(&q, node->right);
        }

        printf("Level %d average: %.2f\n", level, (double)sum / levelSize);
        level++;
    }
}


/* ============================================================
   SECTION 9: BFS Zigzag (Spiral) Level Order
   
   Even levels: left to right
   Odd levels:  right to left (reverse the collected level array)
   ============================================================ */

void bfsZigzag(TreeNode *root) {
    if (root == NULL) return;

    Queue q;
    initQueue(&q);
    enqueue(&q, root);

    int level = 0;

    while (!isEmpty(&q)) {
        int levelSize = q.size;
        int vals[MAX_QUEUE_SIZE];

        for (int i = 0; i < levelSize; i++) {
            TreeNode *node = dequeue(&q);
            vals[i] = node->val;

            if (node->left)  enqueue(&q, node->left);
            if (node->right) enqueue(&q, node->right);
        }

        printf("Level %d (zigzag): ", level);
        if (level % 2 == 0) {
            /* Even level: left to right */
            for (int i = 0; i < levelSize; i++) printf("%d ", vals[i]);
        } else {
            /* Odd level: right to left (reverse) */
            for (int i = levelSize - 1; i >= 0; i--) printf("%d ", vals[i]);
        }
        printf("\n");
        level++;
    }
}


/* ============================================================
   SECTION 10: Free Tree Memory
   ============================================================ */

void freeTree(TreeNode *root) {
    if (root == NULL) return;
    freeTree(root->left);
    freeTree(root->right);
    free(root);
}


/* ============================================================
   SECTION 11: Main — Test All BFS Variants
   ============================================================ */

int main(void) {
    /*
     * Build this tree:
     *
     *          [1]
     *         /   \
     *       [2]   [3]
     *       / \     \
     *     [4] [5]   [6]
     *         /
     *        [7]
     */
    TreeNode *root = newNode(1);
    root->left         = newNode(2);
    root->right        = newNode(3);
    root->left->left   = newNode(4);
    root->left->right  = newNode(5);
    root->right->right = newNode(6);
    root->left->right->left = newNode(7);

    printf("=== BFS Tree Traversal Demonstrations ===\n\n");

    bfsLevelOrder(root);
    printf("\n");

    bfsGroupedByLevel(root);
    printf("\n");

    bfsRightSideView(root);
    printf("\n");

    printf("Minimum Depth: %d\n", bfsMinDepth(root));
    printf("Maximum Width: %d\n", bfsMaxWidth(root));
    printf("\n");

    bfsLevelAverages(root);
    printf("\n");

    bfsZigzag(root);

    freeTree(root);
    return 0;
}
```

---

## 13. Implementation in Go

```go
package main

import "fmt"

// ============================================================
// SECTION 1: Binary Tree Node Definition
// ============================================================

// TreeNode represents a single node in a binary tree.
//
// In Go, we use pointers to build linked structures.
// nil represents the absence of a child (equivalent to NULL in C).
type TreeNode struct {
	Val   int
	Left  *TreeNode
	Right *TreeNode
}

// newNode creates and returns a pointer to a new TreeNode.
func newNode(val int) *TreeNode {
	return &TreeNode{Val: val}
}

// ============================================================
// SECTION 2: Queue Using a Slice
//
// Go slices work perfectly as queues using:
//   - append(slice, element) to enqueue (add to back)
//   - slice[1:]              to dequeue (remove from front)
//   - slice[0]               to peek at front
//
// NOTE: For production use, consider a deque or ring buffer.
// Slicing from front does NOT free the memory of the removed element
// (the underlying array still holds it). For simplicity in problem
// solving, the slice approach is idiomatic and fine.
// ============================================================

// ============================================================
// SECTION 3: Basic BFS — Flat Level Order
// ============================================================

// BFSLevelOrder performs BFS and returns all node values
// in level-order (breadth-first) as a single slice.
func BFSLevelOrder(root *TreeNode) []int {
	if root == nil {
		return nil
	}

	result := []int{}
	queue := []*TreeNode{root} // Initialize queue with root

	for len(queue) > 0 {
		// Dequeue the front node
		node := queue[0]
		queue = queue[1:]

		// Process the node
		result = append(result, node.Val)

		// Enqueue children (left first, then right)
		if node.Left != nil {
			queue = append(queue, node.Left)
		}
		if node.Right != nil {
			queue = append(queue, node.Right)
		}
	}

	return result
}

// ============================================================
// SECTION 4: Level-Aware BFS — Grouped by Level
//
// Returns [][]int where result[i] = values at level i.
//
// The KEY technique: snapshot the queue length at the start
// of each level iteration. Process exactly that many nodes.
// ============================================================

// BFSGroupedByLevel returns nodes grouped by level.
func BFSGroupedByLevel(root *TreeNode) [][]int {
	if root == nil {
		return nil
	}

	result := [][]int{}
	queue := []*TreeNode{root}

	for len(queue) > 0 {
		levelSize := len(queue)       // SNAPSHOT: all nodes at this level
		currentLevel := []int{}

		for i := 0; i < levelSize; i++ {
			node := queue[0]
			queue = queue[1:]

			currentLevel = append(currentLevel, node.Val)

			if node.Left != nil {
				queue = append(queue, node.Left)
			}
			if node.Right != nil {
				queue = append(queue, node.Right)
			}
		}

		result = append(result, currentLevel)
	}

	return result
}

// ============================================================
// SECTION 5: Right Side View
// ============================================================

// BFSRightSideView returns the value of the rightmost node
// at each level — what you'd see from the right.
func BFSRightSideView(root *TreeNode) []int {
	if root == nil {
		return nil
	}

	result := []int{}
	queue := []*TreeNode{root}

	for len(queue) > 0 {
		levelSize := len(queue)
		var lastVal int

		for i := 0; i < levelSize; i++ {
			node := queue[0]
			queue = queue[1:]

			// Keep overwriting lastVal; final value is rightmost
			lastVal = node.Val

			if node.Left != nil {
				queue = append(queue, node.Left)
			}
			if node.Right != nil {
				queue = append(queue, node.Right)
			}
		}

		result = append(result, lastVal)
	}

	return result
}

// ============================================================
// SECTION 6: Minimum Depth
//
// Minimum depth = # nodes on shortest root-to-leaf path.
// BFS finds this optimally: first leaf encountered = answer.
// ============================================================

// BFSMinDepth returns the minimum depth of the tree.
func BFSMinDepth(root *TreeNode) int {
	if root == nil {
		return 0
	}

	queue := []*TreeNode{root}
	depth := 1

	for len(queue) > 0 {
		levelSize := len(queue)

		for i := 0; i < levelSize; i++ {
			node := queue[0]
			queue = queue[1:]

			// Found a leaf — this is the minimum depth
			if node.Left == nil && node.Right == nil {
				return depth
			}

			if node.Left != nil {
				queue = append(queue, node.Left)
			}
			if node.Right != nil {
				queue = append(queue, node.Right)
			}
		}
		depth++
	}

	return depth
}

// ============================================================
// SECTION 7: Maximum Depth (Height)
//
// Count how many levels the tree has.
// Each full iteration of the outer loop = one level.
// ============================================================

// BFSMaxDepth returns the maximum depth (height) of the tree.
func BFSMaxDepth(root *TreeNode) int {
	if root == nil {
		return 0
	}

	queue := []*TreeNode{root}
	depth := 0

	for len(queue) > 0 {
		levelSize := len(queue)
		depth++ // Each outer iteration = one level = one depth unit

		for i := 0; i < levelSize; i++ {
			node := queue[0]
			queue = queue[1:]

			if node.Left != nil {
				queue = append(queue, node.Left)
			}
			if node.Right != nil {
				queue = append(queue, node.Right)
			}
		}
	}

	return depth
}

// ============================================================
// SECTION 8: Maximum Width
// ============================================================

// BFSMaxWidth returns the maximum number of nodes at any level.
func BFSMaxWidth(root *TreeNode) int {
	if root == nil {
		return 0
	}

	queue := []*TreeNode{root}
	maxWidth := 0

	for len(queue) > 0 {
		levelSize := len(queue)

		if levelSize > maxWidth {
			maxWidth = levelSize
		}

		for i := 0; i < levelSize; i++ {
			node := queue[0]
			queue = queue[1:]

			if node.Left != nil {
				queue = append(queue, node.Left)
			}
			if node.Right != nil {
				queue = append(queue, node.Right)
			}
		}
	}

	return maxWidth
}

// ============================================================
// SECTION 9: Zigzag Level Order
//
// Even levels: collect left to right (natural order).
// Odd levels:  reverse the collected level before appending.
// ============================================================

// BFSZigzag returns zigzag level-order traversal.
func BFSZigzag(root *TreeNode) [][]int {
	if root == nil {
		return nil
	}

	result := [][]int{}
	queue := []*TreeNode{root}
	level := 0

	for len(queue) > 0 {
		levelSize := len(queue)
		currentLevel := make([]int, levelSize)

		for i := 0; i < levelSize; i++ {
			node := queue[0]
			queue = queue[1:]
			currentLevel[i] = node.Val

			if node.Left != nil {
				queue = append(queue, node.Left)
			}
			if node.Right != nil {
				queue = append(queue, node.Right)
			}
		}

		// Reverse odd levels
		if level%2 != 0 {
			for l, r := 0, len(currentLevel)-1; l < r; l, r = l+1, r-1 {
				currentLevel[l], currentLevel[r] = currentLevel[r], currentLevel[l]
			}
		}

		result = append(result, currentLevel)
		level++
	}

	return result
}

// ============================================================
// SECTION 10: Level Averages
// ============================================================

// BFSLevelAverages returns the average value at each level.
func BFSLevelAverages(root *TreeNode) []float64 {
	if root == nil {
		return nil
	}

	averages := []float64{}
	queue := []*TreeNode{root}

	for len(queue) > 0 {
		levelSize := len(queue)
		sum := 0

		for i := 0; i < levelSize; i++ {
			node := queue[0]
			queue = queue[1:]
			sum += node.Val

			if node.Left != nil {
				queue = append(queue, node.Left)
			}
			if node.Right != nil {
				queue = append(queue, node.Right)
			}
		}

		averages = append(averages, float64(sum)/float64(levelSize))
	}

	return averages
}

// ============================================================
// SECTION 11: Connect Nodes at Same Level (Next Pointer)
//
// Add a 'Next' pointer to each node, connecting it to the
// next node at the same level (or nil if it's the last).
// ============================================================

// TreeNodeWithNext is an extended node with a Next pointer.
type TreeNodeWithNext struct {
	Val   int
	Left  *TreeNodeWithNext
	Right *TreeNodeWithNext
	Next  *TreeNodeWithNext // Points to right neighbor at same level
}

// BFSConnectNextPointers connects all nodes at the same level.
func BFSConnectNextPointers(root *TreeNodeWithNext) *TreeNodeWithNext {
	if root == nil {
		return nil
	}

	queue := []*TreeNodeWithNext{root}

	for len(queue) > 0 {
		levelSize := len(queue)

		for i := 0; i < levelSize; i++ {
			node := queue[0]
			queue = queue[1:]

			// Connect to the next node in THIS level
			// If it's the last node (i == levelSize-1), queue[0]
			// is the first node of the NEXT level, not this level.
			if i < levelSize-1 {
				node.Next = queue[0] // queue[0] is the next sibling
			}
			// If i == levelSize-1, node.Next stays nil (default)

			if node.Left != nil {
				queue = append(queue, node.Left)
			}
			if node.Right != nil {
				queue = append(queue, node.Right)
			}
		}
	}

	return root
}

// ============================================================
// SECTION 12: Check if Tree is Symmetric
//
// BFS approach: at each level, check if the value array
// is a palindrome (reads the same forwards and backwards).
// ============================================================

// BFSIsSymmetric returns true if the tree is symmetric (mirror image).
func BFSIsSymmetric(root *TreeNode) bool {
	if root == nil {
		return true
	}

	queue := []*TreeNode{root}

	for len(queue) > 0 {
		levelSize := len(queue)
		vals := make([]int, levelSize)

		for i := 0; i < levelSize; i++ {
			node := queue[0]
			queue = queue[1:]
			vals[i] = node.Val

			if node.Left != nil {
				queue = append(queue, node.Left)
			}
			if node.Right != nil {
				queue = append(queue, node.Right)
			}
		}

		// Check if level values form a palindrome
		for l, r := 0, len(vals)-1; l < r; l, r = l+1, r-1 {
			if vals[l] != vals[r] {
				return false
			}
		}
	}

	return true
}

// ============================================================
// SECTION 13: Main — Test Driver
// ============================================================

func main() {
	/*
	 * Build this tree:
	 *
	 *          [1]
	 *         /   \
	 *       [2]   [3]
	 *       / \     \
	 *     [4] [5]   [6]
	 *         /
	 *        [7]
	 */
	root := newNode(1)
	root.Left = newNode(2)
	root.Right = newNode(3)
	root.Left.Left = newNode(4)
	root.Left.Right = newNode(5)
	root.Right.Right = newNode(6)
	root.Left.Right.Left = newNode(7)

	fmt.Println("=== BFS Tree Traversal Demonstrations (Go) ===")
	fmt.Println()

	fmt.Println("Flat Level Order:", BFSLevelOrder(root))
	fmt.Println("Grouped by Level:", BFSGroupedByLevel(root))
	fmt.Println("Right Side View: ", BFSRightSideView(root))
	fmt.Println("Min Depth:       ", BFSMinDepth(root))
	fmt.Println("Max Depth:       ", BFSMaxDepth(root))
	fmt.Println("Max Width:       ", BFSMaxWidth(root))
	fmt.Println("Level Averages:  ", BFSLevelAverages(root))
	fmt.Println("Zigzag Order:    ", BFSZigzag(root))

	// Symmetric tree test
	symRoot := newNode(1)
	symRoot.Left = newNode(2)
	symRoot.Right = newNode(2)
	symRoot.Left.Left = newNode(3)
	symRoot.Right.Right = newNode(3)
	fmt.Println("Is Symmetric:    ", BFSIsSymmetric(symRoot)) // true

	fmt.Println("Is Original Symmetric:", BFSIsSymmetric(root)) // false
}
```

---

## 14. Implementation in Rust

```rust
// ============================================================
// BFS on Binary Trees — Complete Rust Implementation
//
// Rust specifics to understand:
//
// 1. Ownership: Each value has exactly one owner.
// 2. Box<T>: A heap allocation. We use Box<TreeNode> to
//    create heap-allocated child nodes. This is necessary
//    because a struct cannot contain itself directly
//    (that would be infinite size), but Box has a fixed size
//    (just a pointer).
// 3. Option<Box<TreeNode>>: The child can either be
//    Some(node) or None. This replaces NULL pointers safely.
// 4. VecDeque: Rust's standard double-ended queue.
//    Use push_back to enqueue, pop_front to dequeue.
//    This is O(1) amortized for both operations.
// ============================================================

use std::collections::VecDeque;

// ============================================================
// SECTION 1: Binary Tree Node
// ============================================================

/// A single node in a binary tree.
///
/// `Option<Box<TreeNode>>` means:
///   - `None`         -> no child (NULL equivalent)
///   - `Some(boxed)`  -> there is a child node, heap-allocated
#[derive(Debug)]
struct TreeNode {
    val: i32,
    left: Option<Box<TreeNode>>,
    right: Option<Box<TreeNode>>,
}

impl TreeNode {
    /// Create a new leaf node with the given value.
    fn new(val: i32) -> Self {
        TreeNode {
            val,
            left: None,
            right: None,
        }
    }

    /// Convenience: wrap a TreeNode in Box and Option for use as child.
    fn boxed(val: i32) -> Option<Box<TreeNode>> {
        Some(Box::new(TreeNode::new(val)))
    }
}


// ============================================================
// SECTION 2: Basic BFS — Flat Level Order
//
// Using VecDeque<&TreeNode>:
//   We store references (&TreeNode) to avoid moving ownership.
//   Rust's borrow checker ensures these references are valid
//   for the entire duration of the BFS (the tree lives in main).
// ============================================================

/// Performs BFS and returns all values in level order.
fn bfs_level_order(root: &Option<Box<TreeNode>>) -> Vec<i32> {
    let mut result = Vec::new();

    let root_node = match root {
        None => return result,
        Some(node) => node,
    };

    // VecDeque is Rust's efficient double-ended queue.
    // push_back = enqueue, pop_front = dequeue
    let mut queue: VecDeque<&TreeNode> = VecDeque::new();
    queue.push_back(root_node);

    while let Some(node) = queue.pop_front() {
        result.push(node.val);

        // Enqueue left child if it exists
        if let Some(left) = &node.left {
            queue.push_back(left);
        }
        // Enqueue right child if it exists
        if let Some(right) = &node.right {
            queue.push_back(right);
        }
    }

    result
}


// ============================================================
// SECTION 3: Level-Aware BFS — Grouped by Level
// ============================================================

/// Returns node values grouped by their level.
/// result[i] = all values at level i.
fn bfs_grouped_by_level(root: &Option<Box<TreeNode>>) -> Vec<Vec<i32>> {
    let mut result: Vec<Vec<i32>> = Vec::new();

    let root_node = match root {
        None => return result,
        Some(node) => node.as_ref(),
    };

    let mut queue: VecDeque<&TreeNode> = VecDeque::new();
    queue.push_back(root_node);

    while !queue.is_empty() {
        // SNAPSHOT: number of nodes at the current level
        let level_size = queue.len();
        let mut current_level = Vec::with_capacity(level_size);

        for _ in 0..level_size {
            let node = queue.pop_front().unwrap();
            current_level.push(node.val);

            if let Some(left) = &node.left {
                queue.push_back(left);
            }
            if let Some(right) = &node.right {
                queue.push_back(right);
            }
        }

        result.push(current_level);
    }

    result
}


// ============================================================
// SECTION 4: Right Side View
// ============================================================

/// Returns the rightmost node value at each level.
fn bfs_right_side_view(root: &Option<Box<TreeNode>>) -> Vec<i32> {
    let mut result = Vec::new();

    let root_node = match root {
        None => return result,
        Some(node) => node.as_ref(),
    };

    let mut queue: VecDeque<&TreeNode> = VecDeque::new();
    queue.push_back(root_node);

    while !queue.is_empty() {
        let level_size = queue.len();
        let mut last_val = 0;

        for _ in 0..level_size {
            let node = queue.pop_front().unwrap();
            last_val = node.val; // Keep overwriting -> last is rightmost

            if let Some(left) = &node.left {
                queue.push_back(left);
            }
            if let Some(right) = &node.right {
                queue.push_back(right);
            }
        }

        result.push(last_val);
    }

    result
}


// ============================================================
// SECTION 5: Minimum Depth
// ============================================================

/// Returns the minimum depth (root-to-nearest-leaf path length).
/// BFS finds this optimally: stop at the first leaf encountered.
fn bfs_min_depth(root: &Option<Box<TreeNode>>) -> usize {
    let root_node = match root {
        None => return 0,
        Some(node) => node.as_ref(),
    };

    let mut queue: VecDeque<&TreeNode> = VecDeque::new();
    queue.push_back(root_node);
    let mut depth = 1;

    while !queue.is_empty() {
        let level_size = queue.len();

        for _ in 0..level_size {
            let node = queue.pop_front().unwrap();

            // A leaf: no children. First leaf found = min depth.
            if node.left.is_none() && node.right.is_none() {
                return depth;
            }

            if let Some(left) = &node.left {
                queue.push_back(left);
            }
            if let Some(right) = &node.right {
                queue.push_back(right);
            }
        }

        depth += 1;
    }

    depth
}


// ============================================================
// SECTION 6: Maximum Depth
// ============================================================

/// Returns the maximum depth (height) of the tree.
fn bfs_max_depth(root: &Option<Box<TreeNode>>) -> usize {
    let root_node = match root {
        None => return 0,
        Some(node) => node.as_ref(),
    };

    let mut queue: VecDeque<&TreeNode> = VecDeque::new();
    queue.push_back(root_node);
    let mut depth = 0;

    while !queue.is_empty() {
        let level_size = queue.len();
        depth += 1; // Each outer iteration = one level

        for _ in 0..level_size {
            let node = queue.pop_front().unwrap();

            if let Some(left) = &node.left {
                queue.push_back(left);
            }
            if let Some(right) = &node.right {
                queue.push_back(right);
            }
        }
    }

    depth
}


// ============================================================
// SECTION 7: Maximum Width
// ============================================================

/// Returns the maximum number of nodes at any single level.
fn bfs_max_width(root: &Option<Box<TreeNode>>) -> usize {
    let root_node = match root {
        None => return 0,
        Some(node) => node.as_ref(),
    };

    let mut queue: VecDeque<&TreeNode> = VecDeque::new();
    queue.push_back(root_node);
    let mut max_width = 0;

    while !queue.is_empty() {
        let level_size = queue.len();
        if level_size > max_width {
            max_width = level_size;
        }

        for _ in 0..level_size {
            let node = queue.pop_front().unwrap();

            if let Some(left) = &node.left {
                queue.push_back(left);
            }
            if let Some(right) = &node.right {
                queue.push_back(right);
            }
        }
    }

    max_width
}


// ============================================================
// SECTION 8: Zigzag Level Order
// ============================================================

/// Returns zigzag (spiral) level-order traversal.
/// Even levels: left to right. Odd levels: right to left.
fn bfs_zigzag(root: &Option<Box<TreeNode>>) -> Vec<Vec<i32>> {
    let mut result: Vec<Vec<i32>> = Vec::new();

    let root_node = match root {
        None => return result,
        Some(node) => node.as_ref(),
    };

    let mut queue: VecDeque<&TreeNode> = VecDeque::new();
    queue.push_back(root_node);
    let mut level = 0usize;

    while !queue.is_empty() {
        let level_size = queue.len();
        let mut current_level: Vec<i32> = Vec::with_capacity(level_size);

        for _ in 0..level_size {
            let node = queue.pop_front().unwrap();
            current_level.push(node.val);

            if let Some(left) = &node.left {
                queue.push_back(left);
            }
            if let Some(right) = &node.right {
                queue.push_back(right);
            }
        }

        // Reverse odd levels for right-to-left ordering
        if level % 2 != 0 {
            current_level.reverse();
        }

        result.push(current_level);
        level += 1;
    }

    result
}


// ============================================================
// SECTION 9: Level Averages
// ============================================================

/// Returns the average value of nodes at each level.
fn bfs_level_averages(root: &Option<Box<TreeNode>>) -> Vec<f64> {
    let mut averages = Vec::new();

    let root_node = match root {
        None => return averages,
        Some(node) => node.as_ref(),
    };

    let mut queue: VecDeque<&TreeNode> = VecDeque::new();
    queue.push_back(root_node);

    while !queue.is_empty() {
        let level_size = queue.len();
        let mut sum: i64 = 0;

        for _ in 0..level_size {
            let node = queue.pop_front().unwrap();
            sum += node.val as i64;

            if let Some(left) = &node.left {
                queue.push_back(left);
            }
            if let Some(right) = &node.right {
                queue.push_back(right);
            }
        }

        averages.push(sum as f64 / level_size as f64);
    }

    averages
}


// ============================================================
// SECTION 10: Check Symmetric Tree
// ============================================================

/// Returns true if the tree is symmetric (mirror image of itself).
/// BFS approach: each level's values must form a palindrome.
fn bfs_is_symmetric(root: &Option<Box<TreeNode>>) -> bool {
    let root_node = match root {
        None => return true,
        Some(node) => node.as_ref(),
    };

    let mut queue: VecDeque<&TreeNode> = VecDeque::new();
    queue.push_back(root_node);

    while !queue.is_empty() {
        let level_size = queue.len();
        let mut vals: Vec<i32> = Vec::with_capacity(level_size);

        for _ in 0..level_size {
            let node = queue.pop_front().unwrap();
            vals.push(node.val);

            if let Some(left) = &node.left {
                queue.push_back(left);
            }
            if let Some(right) = &node.right {
                queue.push_back(right);
            }
        }

        // Check palindrome
        let n = vals.len();
        for i in 0..n / 2 {
            if vals[i] != vals[n - 1 - i] {
                return false;
            }
        }
    }

    true
}


// ============================================================
// SECTION 11: Main — Test Driver
// ============================================================

fn main() {
    /*
     * Build this tree:
     *
     *          [1]
     *         /   \
     *       [2]   [3]
     *       / \     \
     *     [4] [5]   [6]
     *         /
     *        [7]
     */
    let mut root = TreeNode::new(1);
    let mut left = TreeNode::new(2);
    let right_node = TreeNode::new(3);
    let node4 = TreeNode::new(4);
    let mut node5 = TreeNode::new(5);
    let node6 = TreeNode::new(6);
    let node7 = TreeNode::new(7);

    // Assemble the tree bottom-up (Rust ownership requires this)
    node5.left = Some(Box::new(node7));
    left.left = Some(Box::new(node4));
    left.right = Some(Box::new(node5));

    let mut right = right_node;
    right.right = Some(Box::new(node6));

    root.left = Some(Box::new(left));
    root.right = Some(Box::new(right));

    let root_opt = Some(Box::new(root));

    println!("=== BFS Tree Traversal Demonstrations (Rust) ===\n");

    println!("Flat Level Order:  {:?}", bfs_level_order(&root_opt));
    println!("Grouped by Level:  {:?}", bfs_grouped_by_level(&root_opt));
    println!("Right Side View:   {:?}", bfs_right_side_view(&root_opt));
    println!("Min Depth:         {}",   bfs_min_depth(&root_opt));
    println!("Max Depth:         {}",   bfs_max_depth(&root_opt));
    println!("Max Width:         {}",   bfs_max_width(&root_opt));
    println!("Level Averages:    {:?}", bfs_level_averages(&root_opt));
    println!("Zigzag Order:      {:?}", bfs_zigzag(&root_opt));

    // Symmetric test
    let mut sym_root = TreeNode::new(1);
    let mut sym_left = TreeNode::new(2);
    let mut sym_right = TreeNode::new(2);
    sym_left.left = Some(Box::new(TreeNode::new(3)));
    sym_right.right = Some(Box::new(TreeNode::new(3)));
    sym_root.left = Some(Box::new(sym_left));
    sym_root.right = Some(Box::new(sym_right));

    let sym_root_opt = Some(Box::new(sym_root));
    println!("Is Symmetric (sym): {}", bfs_is_symmetric(&sym_root_opt)); // true
    println!("Is Symmetric (orig): {}", bfs_is_symmetric(&root_opt));    // false
}
```

---

## 15. Common Mistakes & Pitfalls

### Mistake 1: Confusing BFS with DFS

```
BFS uses a QUEUE (FIFO).
DFS uses a STACK (LIFO) — either explicit or via recursion's call stack.

If you accidentally use a stack for BFS, you get DFS order.
The data structure determines the traversal order — this is not incidental.
```

### Mistake 2: Forgetting the NULL / nil Check for Root

```
Always check: if root is NULL, return early.
Otherwise, you'll try to enqueue NULL, leading to crashes or incorrect results.
```

### Mistake 3: Not Taking a Snapshot of Queue Size

```
WRONG (for level-grouping):
  while queue not empty:
    for node in queue:  // This iterates the GROWING queue!
      process node
      enqueue children  // Children added mid-loop = wrong level

RIGHT:
  while queue not empty:
    levelSize = queue.size()  // SNAPSHOT before the inner loop
    for i in 0..levelSize:    // Process only THIS level's nodes
      ...
```

### Mistake 4: Treating Nodes with One Child as Leaves (Min Depth)

```
A LEAF has BOTH children as NULL.
A node with only a left child (and no right) is NOT a leaf.

Wrong:
  if node.left == NULL || node.right == NULL: return depth

Right:
  if node.left == NULL && node.right == NULL: return depth
```

### Mistake 5: Queue Memory in C (Fixed-Size Arrays)

```
In C, if you use a fixed-size array for the queue,
make sure it's large enough for the widest level.
For a perfect binary tree with 2^h nodes at the last level,
your MAX_QUEUE_SIZE must be at least 2^h.

Safe default: MAX_QUEUE_SIZE = N (total number of nodes).
```

### Mistake 6: Modifying the Tree During BFS

```
BFS is a READ-ONLY operation in most problems.
If you modify node pointers (children) while enqueueing,
you will corrupt the traversal.
```

---

## 16. Pattern Recognition — Mental Models

### The 3-Question Framework (Before Coding)

When you see a tree problem, ask:

```
1. Do I need to go DEEP or WIDE?
   - Deep (path, root-to-leaf, subtree structure) -> Consider DFS
   - Wide (levels, same-level nodes, layer info)  -> BFS

2. Do I need level information?
   - Per-level stats (max, min, avg, count)       -> Level-aware BFS
   - Just BFS order (no level grouping)           -> Simple BFS

3. Can I terminate early?
   - Minimum depth, first occurrence              -> BFS stops at first find
   - Maximum depth, all paths                     -> Need full traversal
```

### The Queue-as-Frontier Mental Model

Think of the queue as the **current frontier** of exploration:

```
Start: Frontier = {root}

After level 0: Frontier = {all level-1 nodes}
After level 1: Frontier = {all level-2 nodes}
...

The frontier advances one level at a time.
BFS = "Systematically advance the frontier level by level."
```

### BFS as Water Flooding

```
Imagine your tree is a landscape.
Root is at the top. Children hang below.
You pour water onto the root.

Water spreads EVENLY downward — it reaches all nodes
at level 1 before any node at level 2.
This is exactly BFS order.
```

### When NOT to Use BFS

```
Use DFS instead when:
- You need to explore root-to-leaf paths (path sum, path existence)
- The problem involves subtree structure (height, balance)
- You're doing in-order, pre-order, or post-order traversal
- The tree is very wide (BFS space = O(N) for last level)
  but very tall (DFS space = O(H) = O(log N) for balanced trees)
```

### Cognitive Principle: Problem-to-Pattern Mapping

The skill of top 1% programmers isn't memorizing solutions — it's **mapping a new problem to a known pattern** instantly.

Train this with:
1. Read the problem.
2. Ask: "What kind of question is this asking about the tree?"
3. Map to one of these BFS variants:
   - Level info -> Level-aware BFS
   - Shortest path -> Basic BFS (stop at first answer)
   - Per-level view -> Level-aware BFS + record first/last
   - Connection -> Level-aware BFS + link nodes
   - Structure check -> BFS + per-level symmetry check

---

## 17. Deliberate Practice Problems

Work through these problems in order. Each builds on the last.

### Tier 1 — Foundation (Master these first)

```
1. Binary Tree Level Order Traversal
   -> Return [[level0], [level1], ...]

2. Maximum Depth of Binary Tree
   -> Count number of levels via BFS

3. Minimum Depth of Binary Tree
   -> Stop BFS at first leaf

4. Binary Tree Right Side View
   -> Record last node at each level
```

### Tier 2 — Intermediate

```
5. Average of Levels in Binary Tree
   -> Sum / count per level

6. Binary Tree Zigzag Level Order Traversal
   -> Alternate direction per level

7. Maximum Width of Binary Tree
   -> Track max queue size per level

8. Find Largest Value in Each Tree Row
   -> Track max value per level
```

### Tier 3 — Advanced

```
9.  Populating Next Right Pointers in Each Node
    -> Connect same-level nodes with 'next' pointer

10. Cousins in Binary Tree
    -> Track (node, parent, level), compare for target nodes

11. Check Completeness of a Binary Tree
    -> In BFS, after first None child, all remaining must be None

12. Serialize and Deserialize Binary Tree
    -> BFS order + NULL markers

13. Vertical Order Traversal of a Binary Tree
    -> BFS + column tracking

14. Find Bottom Left Tree Value
    -> Level-aware BFS; track first node at each level; return last level's first
```

### Tier 4 — Expert

```
15. Binary Tree Level Order Traversal with obstacles
    -> Add constraints (skip nodes, accumulate conditionally)

16. Maximum Level Sum of a Binary Tree
    -> Track which level has maximum sum

17. N-ary Tree Level Order Traversal
    -> Generalize: enqueue ALL children (not just left, right)

18. Step-By-Step Directions From a Binary Tree Node to Another
    -> BFS to find LCA, then reconstruct path
```

---

## Summary — The Complete Mental Model

```
+----------------------------------------------------------+
|                   BFS ON TREES                           |
+----------------------------------------------------------+
|                                                          |
|  WHEN TO USE        HOW IT WORKS       KEY TOOL          |
|  -----------        ------------       --------          |
|  Level info         Enqueue root       QUEUE (FIFO)      |
|  Shortest path      While not empty:   VecDeque / slice  |
|  Min depth          - Dequeue N        Level snapshot    |
|  Level statistics   - Process N                          |
|  Width / view       - Enqueue children                   |
|                                                          |
|  VARIANTS           COMPLEXITY         STOP EARLY?       |
|  --------           ----------         -----------       |
|  Flat order         O(N) time          Min depth: YES    |
|  Grouped            O(N) space         Target found: YES |
|  Zigzag             (queue = O(W))     Otherwise: NO     |
|  Right/Left view    W = max width                        |
|  Connect nodes                                           |
|  Symmetric check                                         |
|                                                          |
+----------------------------------------------------------+

GOLDEN RULE:
  "If a problem asks about LEVELS or LAYER-BY-LAYER structure,
   reach for BFS first."
```

---

*This guide is your complete foundation for mastering BFS on trees. Work through each section methodically, trace every example by hand before running code, and practice each problem tier with full deliberate attention. The code reveals the algorithm; the trace reveals the understanding.*

Here's your complete BFS Tree guide — every concept built from first principles, nothing skipped.

---

**What's inside (17 sections):**

The guide opens by defining every single term you'll encounter — root, leaf, level, depth, height, ancestor, sibling — before touching any algorithm. Then BFS is introduced through the **water flooding mental model** (the most intuitive way to understand level-by-level spread), followed by a precise analysis of why a Queue (FIFO) is the *only* correct data structure for this — not incidental, but mathematically forced.

The **hand-traced execution table** walks you through every queue state change, step by step, so you can internalize what's happening in memory, not just in code.

**9 BFS variants** are covered with their own ASCII diagrams and when-to-use reasoning:
- Flat level order, grouped by level, zigzag, right/left side view, min/max depth, max width, level averages, next-pointer connection, symmetric check

The **3 implementations (C, Go, Rust)** are heavily commented, explaining *why* each line exists — including Rust-specific explanations of `Option<Box<TreeNode>>`, `VecDeque`, and borrow mechanics that trip up beginners.

---

**The single most important mental model from this guide:**

> *"The data structure you choose determines the traversal order. Queue = BFS. Stack = DFS. This is not convention — it is mathematics."*

Start your practice at Tier 1 problems. Trace every execution by hand before you run it. That is where understanding lives.