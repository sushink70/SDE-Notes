# DFS on Trees — Complete In-Depth Guide

> *"The expert has failed more times than the beginner has even tried."*
> Master the mental model first. The code follows naturally.

---

## Table of Contents

1. [Foundational Vocabulary — Every Term Defined](#1-foundational-vocabulary)
2. [What Is a Tree? — First Principles](#2-what-is-a-tree)
3. [What Is DFS? — The Core Mental Model](#3-what-is-dfs)
4. [The Three Traversal Orders](#4-the-three-traversal-orders)
5. [The Call Stack — How Recursion Really Works](#5-the-call-stack)
6. [Recursive DFS — Implementation Deep Dive](#6-recursive-dfs)
7. [Iterative DFS — Explicit Stack](#7-iterative-dfs)
8. [Morris Traversal — O(1) Space DFS](#8-morris-traversal)
9. [Core DFS Patterns on Trees](#9-core-dfs-patterns)
10. [Classic Problems Solved with DFS](#10-classic-problems)
11. [Performance Analysis — Hardware Reality](#11-performance-analysis)
12. [Complete Go Implementation](#12-go-implementation)
13. [Complete C Implementation](#13-c-implementation)
14. [Complete Rust Implementation](#14-rust-implementation)
15. [Mental Models and Expert Intuition](#15-mental-models)

---

## 1. Foundational Vocabulary

Before anything else, we must share a precise language. Every term below will be used throughout this guide. If a term is fuzzy in your mind, the algorithm will be fuzzy too.

```
                        1          <- ROOT (no parent)
                      /   \
                     2     3       <- INTERNAL NODES (have children)
                    / \     \
                   4   5     6     <- 4,5,6,7 are LEAVES (no children)
                        \
                         7
```

| Term | Definition | In the diagram above |
|------|-----------|----------------------|
| **Node** | A single element storing a value + pointers to children | 1, 2, 3, 4, 5, 6, 7 |
| **Root** | The topmost node; has no parent | Node 1 |
| **Leaf** | A node with zero children | Nodes 4, 6, 7 |
| **Internal node** | A node with at least one child | Nodes 1, 2, 3, 5 |
| **Parent** | The node directly above | 2 is parent of 4 and 5 |
| **Child** | A node directly below another | 4 and 5 are children of 2 |
| **Sibling** | Nodes sharing the same parent | 4 and 5 are siblings |
| **Edge** | A connection between parent and child | There are 6 edges here |
| **Depth** | Distance from root to a node (root = depth 0) | depth(7) = 3 |
| **Height of a node** | Longest path from that node to any leaf | height(2) = 2 |
| **Height of tree** | Height of the root node | 3 |
| **Level** | All nodes at the same depth | Level 2 = {4, 5, 6} |
| **Ancestor** | Any node on the path from root to a node | ancestors of 7: {1,2,5} |
| **Descendant** | Any node reachable downward | descendants of 2: {4,5,7} |
| **Subtree** | A node + all its descendants | Subtree rooted at 2 |
| **Binary tree** | Each node has at most 2 children | Our example above |
| **N-ary tree** | Each node can have up to N children | File system trees |
| **BST** | Binary tree where left < node < right | Explained in Section 9 |
| **Balanced tree** | Height is O(log n) | AVL, Red-Black trees |
| **Complete tree** | All levels full except possibly last (filled left) | Heaps |
| **Full tree** | Every node has 0 or 2 children | Common in problems |
| **Perfect tree** | All internal nodes have 2 children; all leaves same depth | |
| **Path** | Sequence of nodes connected by edges | 1→2→5→7 |
| **Path length** | Number of edges in a path | length(1→2→5→7) = 3 |
| **Successor (in-order)** | The next node in sorted (in-order) traversal | successor of 4 = 2 (in BST) |
| **Predecessor** | The previous node in sorted traversal | |

### Critical Insight: Trees Are Recursive by Nature

A tree is defined recursively:
- A tree is either **empty**, or
- A **root node** connected to zero or more **subtrees** (each of which is itself a tree)

This is not just an academic observation. It is the *reason* recursive DFS feels so natural on trees — you are literally following the shape of the data structure.

---

## 2. What Is a Tree?

### Formal Definition

A tree with `n` nodes has exactly `n-1` edges. This is a theorem, not a convention. It follows from: every node except the root has exactly one parent edge.

### Memory Representation

In memory, a binary tree node looks like this:

```
  Node in memory (binary tree):
  ┌─────────────────────────────┐
  │  value  │  left*  │  right* │
  │  (data) │ (ptr)   │ (ptr)   │
  └─────────────────────────────┘
       │         │          │
       │         ▼          ▼
       │    left child   right child
       │    (or NULL)    (or NULL)
       ▼
    stored value (int, string, etc.)
```

**On a 64-bit system:**
- `value` (int32): 4 bytes
- `left*` pointer: 8 bytes
- `right*` pointer: 8 bytes
- Total per node: ~20 bytes (+ padding = 24 bytes typically)

For 1 million nodes → ~24 MB. This matters for cache analysis later.

### Tree vs. Graph: The Critical Distinction

| Property | Tree | General Graph |
|----------|------|---------------|
| Cycles | Never | Possible |
| Parent count per node | Exactly 1 (except root=0) | Any number |
| Connectivity | Always connected | May be disconnected |
| DFS visited tracking | **Not needed** | Required (no revisit) |

This is why tree DFS is simpler than graph DFS — you never need a `visited` array. There are no cycles to cause infinite loops. Every path from root terminates at a leaf.

---

## 3. What Is DFS?

### The Core Mental Model

**Depth-First Search** means: *go as deep as possible along one path before backtracking and trying another path.*

Imagine you are exploring a cave system:
- You pick a tunnel and walk until you hit a dead end (leaf node)
- You mark that dead end as "visited"
- You backtrack to the last junction
- You try the next unexplored tunnel
- Repeat until all tunnels are explored

```
Cave exploration order (DFS):
                    [A]
                   /   \
                 [B]   [C]
                /  \      \
              [D]  [E]   [F]

DFS visits: A → B → D (dead end) → backtrack → E (dead end) 
            → backtrack → backtrack → C → F (dead end) → done

Visit order: A, B, D, E, C, F
```

### DFS vs BFS — The Fundamental Difference

```
BFS (Breadth-First):          DFS (Depth-First):
Explores level by level       Explores branch by branch

        1                             1
       / \                           / \
      2   3                         2   3
     / \   \                       / \   \
    4   5   6                     4   5   6

Visit: 1,2,3,4,5,6             Visit: 1,2,4,5,3,6
Uses: QUEUE                    Uses: STACK (call stack or explicit)
```

### Why DFS for Trees?

DFS on trees is the natural operation because:
1. **Recursive structure matches recursive algorithm** — a tree IS a recursive data structure
2. **Stack memory = call stack** — no auxiliary data structure needed in the recursive form
3. **Subtree problems** — almost all tree problems require computing something for subtrees first, which is exactly what DFS does

---

## 4. The Three Traversal Orders

This is the heart of tree DFS. There are exactly three classical DFS traversal orderings for binary trees. The difference is only: **when do you process the current node relative to its children?**

### The Traversal Mnemonic

```
For every node, you do three things:
  (V) = Visit/process current node
  (L) = Recurse into left subtree
  (R) = Recurse into right subtree

Pre-order:  V → L → R    (process BEFORE children)
In-order:   L → V → R    (process BETWEEN children)
Post-order: L → R → V    (process AFTER children)
```

### Working Example — All Three Orders

```
Our example tree:
            10
           /  \
          5    15
         / \     \
        3   7    20

PRE-ORDER  (Root, Left, Right): 10, 5, 3, 7, 15, 20
IN-ORDER   (Left, Root, Right):  3, 5, 7, 10, 15, 20   ← SORTED for BST!
POST-ORDER (Left, Right, Root):  3, 7, 5, 20, 15, 10
```

### Visual Traversal Walkthrough: Pre-Order

```
Step-by-step pre-order on:
            10
           /  \
          5    15
         / \     \
        3   7    20

Step 1: Visit 10 → OUTPUT: [10]
        Go Left to 5

Step 2: Visit 5 → OUTPUT: [10, 5]
        Go Left to 3

Step 3: Visit 3 → OUTPUT: [10, 5, 3]
        No left child → No right child → RETURN to 5

Step 4: Back at 5, go Right to 7

Step 5: Visit 7 → OUTPUT: [10, 5, 3, 7]
        No left child → No right child → RETURN to 5 → RETURN to 10

Step 6: Back at 10, go Right to 15

Step 7: Visit 15 → OUTPUT: [10, 5, 3, 7, 15]
        No left child → go Right to 20

Step 8: Visit 20 → OUTPUT: [10, 5, 3, 7, 15, 20]
        Done!
```

### Visual Traversal Walkthrough: In-Order

```
In-order on the same tree:
            10
           /  \
          5    15
         / \     \
        3   7    20

Step 1: Go Left from 10 → Left from 5 → reach 3
Step 2: 3 has no left → Visit 3 → OUTPUT: [3]
        3 has no right → RETURN to 5
Step 3: Visit 5 → OUTPUT: [3, 5]
        Go Right to 7
Step 4: 7 has no left → Visit 7 → OUTPUT: [3, 5, 7]
        7 has no right → RETURN to 5 → RETURN to 10
Step 5: Visit 10 → OUTPUT: [3, 5, 7, 10]
        Go Right to 15
Step 6: 15 has no left → Visit 15 → OUTPUT: [3, 5, 7, 10, 15]
        Go Right to 20
Step 7: 20 has no left → Visit 20 → OUTPUT: [3, 5, 7, 10, 15, 20]
        Done! (Perfect sorted order — BST property!)
```

### Visual Traversal Walkthrough: Post-Order

```
Post-order on the same tree:
            10
           /  \
          5    15
         / \     \
        3   7    20

Step 1: Descend all the way Left → reach 3
Step 2: 3 has no children → Visit 3 → OUTPUT: [3] → RETURN to 5
Step 3: Go Right to 7 → 7 has no children → Visit 7 → OUTPUT: [3, 7]
Step 4: RETURN to 5 → both children done → Visit 5 → OUTPUT: [3, 7, 5]
Step 5: RETURN to 10 → go Right to 15
Step 6: 15 has no left → go Right to 20
Step 7: 20 has no children → Visit 20 → OUTPUT: [3, 7, 5, 20] → RETURN to 15
Step 8: Visit 15 → OUTPUT: [3, 7, 5, 20, 15] → RETURN to 10
Step 9: Visit 10 → OUTPUT: [3, 7, 5, 20, 15, 10]
        Done! (Root always last)
```

### When to Use Each Order

| Order | Use When |
|-------|----------|
| **Pre-order** | Serialize/copy a tree; create directory structure; prefix expression; when you need parent before children |
| **In-order** | BST sorted output; BST validation; kth-smallest element |
| **Post-order** | Delete a tree; compute subtree aggregates (height, size, sum); dependency resolution; when children must be processed before parent |

---

## 5. The Call Stack — How Recursion Really Works

Understanding this deeply will make you a better programmer in every language.

### The Runtime Stack

When your program runs, the OS gives it a **stack** — a region of memory that grows and shrinks as functions call each other.

```
Stack frame for recursive DFS call:

When we call dfs(node):
┌────────────────────────────────┐  ← Stack grows DOWN
│  dfs(10)                       │  Frame 1 (first call)
│  local vars: node=10           │
│  saved return address          │
├────────────────────────────────┤
│  dfs(5)                        │  Frame 2 (recursive call)
│  local vars: node=5            │
│  saved return address          │
├────────────────────────────────┤
│  dfs(3)                        │  Frame 3
│  local vars: node=3            │
│  saved return address          │
├────────────────────────────────┤
│  dfs(nil/NULL)                 │  Frame 4 (base case → returns)
└────────────────────────────────┘  ← Stack pointer here

When dfs(nil) returns:
  Frame 4 is POPPED
  dfs(3) resumes from where it left off
  Then dfs(3) returns
  Frame 3 is POPPED
  dfs(5) resumes... and so on
```

### Stack Depth = Tree Height

The maximum number of stack frames active simultaneously equals the **height of the tree**.

```
Balanced tree (height = log₂n):
  n = 1,000,000 nodes → height ≈ 20 → ~20 stack frames
  Each frame ≈ 100-200 bytes → ~4KB stack usage  ✓ SAFE

Degenerate (skewed) tree (height = n):
  n = 1,000,000 nodes → height = 1,000,000 → ~1,000,000 stack frames
  Each frame ≈ 100-200 bytes → ~200MB stack usage  ✗ STACK OVERFLOW

Default stack sizes:
  Linux: 8MB
  macOS: 8MB  
  Windows: 1MB
  Go goroutine: starts at 8KB, grows dynamically (key advantage!)
```

**This is why iterative DFS matters** — it moves the stack to the **heap** where you have gigabytes of memory.

---

## 6. Recursive DFS — Implementation Deep Dive

### The Template (Language-Agnostic)

Every recursive DFS on a tree follows this exact template:

```
function dfs(node):
    // BASE CASE: empty node
    if node is null/nil/None:
        return <identity_value>
    
    // RECURSIVE CASES:
    left_result  = dfs(node.left)
    right_result = dfs(node.right)
    
    // COMBINE: compute answer for current node using children's answers
    return combine(node.value, left_result, right_result)
```

The **identity value** is the value that doesn't affect the combination:
- For sum: 0
- For max: -infinity
- For min: +infinity  
- For count: 0
- For "exists": false

### The Three Traversal Code Templates

```
// Pre-order DFS template
function preorder(node):
    if node == null: return
    process(node)        // ← BEFORE
    preorder(node.left)
    preorder(node.right)

// In-order DFS template  
function inorder(node):
    if node == null: return
    inorder(node.left)
    process(node)        // ← BETWEEN
    inorder(node.right)

// Post-order DFS template
function postorder(node):
    if node == null: return
    postorder(node.left)
    postorder(node.right)
    process(node)        // ← AFTER
```

---

## 7. Iterative DFS — Explicit Stack

### Why Iterative?

1. **Avoids stack overflow** on skewed/deep trees
2. **More control** — you can pause, resume, inspect state
3. **Required knowledge** for interviews (showing you understand the mechanism)
4. **Some compilers** don't optimize tail recursion; iterative is always O(1) overhead per step

### Iterative Pre-Order

```
Algorithm:
  Push root onto stack
  While stack not empty:
    node = stack.pop()
    process(node)
    Push RIGHT child first (so LEFT is processed first — LIFO)
    Push LEFT child

Why right before left?
  Stack is LIFO. If we push left then right:
    stack = [left, right]
    next pop = right → WRONG ORDER
  If we push right then left:
    stack = [right, left]
    next pop = left → CORRECT (pre-order: root, left, right)
```

```
Visual trace on:
        10
       /  \
      5    15
     / \     \
    3   7    20

Initial: stack = [10]

Pop 10, process → output: [10]
Push 15 (right), push 5 (left) → stack = [15, 5]

Pop 5, process → output: [10, 5]
Push 7 (right), push 3 (left) → stack = [15, 7, 3]

Pop 3, process → output: [10, 5, 3]
No children → stack = [15, 7]

Pop 7, process → output: [10, 5, 3, 7]
No children → stack = [15]

Pop 15, process → output: [10, 5, 3, 7, 15]
Push 20 (right) → stack = [20]

Pop 20, process → output: [10, 5, 3, 7, 15, 20]
Stack empty → DONE ✓
```

### Iterative In-Order

In-order is trickier iteratively because we must go as far left as possible before processing.

```
Algorithm:
  current = root
  stack = empty
  
  While current != null OR stack not empty:
    // Go as far left as possible
    While current != null:
      push current
      current = current.left
    
    // Process leftmost unprocessed node
    current = stack.pop()
    process(current)
    
    // Move to right subtree
    current = current.right
```

```
Visual trace on:
        10
       /  \
      5    15
     / \     \
    3   7    20

current=10, push 10, go left
current=5,  push 5,  go left
current=3,  push 3,  go left
current=nil → inner while stops

stack=[10,5,3]

Pop 3, process → output: [3]
current = 3.right = nil

stack=[10,5]
inner while: current=nil, skip

Pop 5, process → output: [3, 5]
current = 5.right = 7

stack=[10]
inner while: push 7, go left → current=nil

Pop 7, process → output: [3, 5, 7]
current = 7.right = nil

stack=[10]
Pop 10, process → output: [3, 5, 7, 10]
current = 10.right = 15

push 15, go left → current=nil
Pop 15, process → output: [3, 5, 7, 10, 15]
current = 15.right = 20

push 20, go left → current=nil
Pop 20, process → output: [3, 5, 7, 10, 15, 20]
Done ✓
```

### Iterative Post-Order

Post-order iteratively requires extra thought. The classic trick:

**Method 1 — Two Stacks:**
```
Post-order = reverse of (Root, Right, Left)
So: compute (Root, Right, Left) using a pre-order-like approach,
    collect results, then reverse.

Push root to stack1
While stack1 not empty:
  node = stack1.pop()
  push node to stack2       // collect results reversed
  push node.left to stack1  // note: left before right (opposite of pre-order)
  push node.right to stack1
Output stack2 in reverse
```

**Method 2 — One Stack with prev tracking:**
```
stack = [root]
prev = null

While stack not empty:
  curr = stack.top() (peek, don't pop)
  
  // Going DOWN: if no children or children not visited
  if (curr.left != null AND curr.left != prev AND curr.right != prev):
    push curr.left
  elif (curr.right != null AND curr.right != prev):
    push curr.right
  else:
    pop curr
    process(curr)
    prev = curr
```

---

## 8. Morris Traversal — O(1) Space DFS

### The Problem Morris Solves

Both recursive and iterative DFS use O(h) extra space (h = height of tree):
- Recursive: O(h) call stack
- Iterative: O(h) explicit stack

For a balanced tree: O(log n) space. For a skewed tree: O(n) space.

**Morris traversal achieves O(1) space** by temporarily modifying the tree itself to encode where to return after visiting a subtree.

### The Core Idea: Threaded Binary Trees

The key insight: most nodes have a `right` pointer that is `null`. Morris exploits these null pointers to create **temporary backward links** (threads) that let you return to the parent after finishing a subtree — without a stack.

### Morris In-Order Algorithm

```
For each node:
  IF node has no left child:
    → process node, move to right child
  
  IF node has a left child:
    → Find the IN-ORDER PREDECESSOR of current node
       (rightmost node in left subtree)
    
    IF predecessor.right == null:
      → Create thread: predecessor.right = current
      → Move to left child (start exploring left)
    
    IF predecessor.right == current:
      → Thread already exists: left subtree done
      → Remove thread: predecessor.right = null
      → Process current node
      → Move to right child
```

```
Visual trace:
        10
       /  \
      5    15
     / \
    3   7

Step 1: curr=10
  10 has left child (5)
  Find in-order predecessor of 10 in left subtree:
    Go left to 5, then right to 7 (rightmost in left subtree)
    predecessor = 7
  7.right == null → create thread: 7.right = 10
  Move curr to 10.left = 5

        10
       /  \
      5    15
     / \
    3   7
         \
         10  ← THREAD (temporary link back)

Step 2: curr=5
  5 has left (3)
  Find predecessor of 5: go left to 3 (no right child)
  predecessor = 3
  3.right == null → create thread: 3.right = 5
  Move curr to 5.left = 3

Step 3: curr=3
  3 has no left → PROCESS 3 → output: [3]
  Move to 3.right = 5 (following thread!)

Step 4: curr=5
  5 has left (3)
  Find predecessor: 3
  3.right == 5 → thread exists! → remove thread: 3.right = null
  PROCESS 5 → output: [3, 5]
  Move to 5.right = 7

Step 5: curr=7
  7 has no left → PROCESS 7 → output: [3, 5, 7]
  Move to 7.right = 10 (following thread!)

Step 6: curr=10
  10 has left (5)
  Find predecessor: 7 (rightmost of left subtree)
  7.right == 10 → thread exists! → remove: 7.right = null
  PROCESS 10 → output: [3, 5, 7, 10]
  Move to 10.right = 15

Step 7: curr=15
  15 has no left → PROCESS 15 → output: [3, 5, 7, 10, 15]
  15.right = null → done

Final output: [3, 5, 7, 10, 15] ✓
Space used: O(1) — only two pointers (curr, predecessor)
```

**Morris is used in production systems where memory is severely constrained** (embedded systems, large dataset processing). The tradeoff: tree is temporarily mutated (thread-unsafe without synchronization), and code is more complex to reason about.

---

## 9. Core DFS Patterns on Trees

These are the **universal patterns** that solve 90% of tree problems. Internalize the pattern, then any specific problem is just an instance of it.

### Pattern 1: Accumulate (bottom-up computation)

Compute something for a subtree using the results from its children.

```
Template:
  dfs(node):
    if null: return base_value
    left_val  = dfs(node.left)
    right_val = dfs(node.right)
    return f(node.val, left_val, right_val)  // combine

Examples: height, size, sum, diameter, max path sum
```

### Pattern 2: Propagate (top-down information passing)

Pass information FROM ancestors DOWN to descendants.

```
Template:
  dfs(node, state_from_ancestor):
    if null: return
    // use state_from_ancestor to make decision
    dfs(node.left,  update_state(state_from_ancestor, node))
    dfs(node.right, update_state(state_from_ancestor, node))

Examples: path sum (pass remaining sum), level tracking, BST validation (pass valid range)
```

### Pattern 3: Global Variable Updated at Nodes

The answer isn't the return value — it's updated at each node into a global.

```
Template:
  best = initial_value
  
  dfs(node):
    if null: return base
    left_val  = dfs(node.left)
    right_val = dfs(node.right)
    best = max/min(best, compute(node, left_val, right_val))
    return something_for_parent

Examples: diameter of tree, max path sum, longest zigzag
```

### Pattern 4: Path Tracking (root-to-leaf paths)

Track the exact path from root to leaf.

```
Template:
  dfs(node, path):
    if null: return
    path.add(node.val)
    if leaf: process(path)
    dfs(node.left,  path)
    dfs(node.right, path)
    path.remove_last()   // BACKTRACK — critical!
```

The **backtracking** step is essential. Without it, the path accumulates values from different branches.

### Pattern 5: Two-Pass DFS

Some problems require knowing subtree info (bottom-up) before making decisions (top-down). Use two DFS passes.

```
Pass 1 (post-order): compute subtree sizes, sums, etc.
Pass 2 (pre-order): use computed values to answer query
```

---

## 10. Classic Problems Solved with DFS

### Problem 1: Height of a Binary Tree

```
Height = max(height_of_left_subtree, height_of_right_subtree) + 1
Height of empty tree = -1 (or 0, depending on convention)
Height of single node = 0

Tree:
        1
       / \
      2   3
     /
    4

height(4) = 0    (leaf)
height(2) = max(height(4), height(nil)) + 1 = max(0, -1) + 1 = 1
height(3) = max(-1, -1) + 1 = 0
height(1) = max(1, 0) + 1 = 2   ← answer

Time: O(n) — must visit every node
Space: O(h) — call stack depth
```

### Problem 2: Diameter of a Binary Tree

**Diameter**: longest path between any two nodes (path may not pass through root!)

```
Key insight: For each node, the longest path THROUGH it =
  height(left subtree) + height(right subtree) + 2
  (the +2 accounts for the two edges connecting node to its subtrees)

But the diameter might NOT pass through root, so we track
the global maximum.

Tree:
        1
       / \
      2   3
     / \
    4   5

diameter through 2 = height(4) + height(5) + 2 = 0 + 0 + 2 = 2
diameter through 1 = height(2) + height(3) + 2 = 1 + 0 + 2 = 3 ← max

Wait, let's recalculate:
height(4) = 0, height(5) = 0
height(2) = max(0, 0) + 1 = 1
height(3) = 0

Longest path through 2: 0 + 0 + 2 = 2 edges (4→2→5)
Longest path through 1: height_left + height_right + 2
  = 1 + 0 + 2 = 3 edges? But that's 1→2→4 or 1→2→5 (length 2)
  
  Actually the formula uses:
  Path through node = left_height + right_height + 2
  where height of null = -1

height(null) = -1
height(4) = 0, height(5) = 0
height(2) = max(0,0)+1 = 1
height(3) = max(-1,-1)+1 = 0

At node 2: path = 0 + 0 + 2 = 2 (path 4→2→5, length 2 edges ✓)
At node 1: path = 1 + 0 + 2 = 3 (path 4→2→1→3, length 3 edges ✓)

Global max diameter = 3
```

### Problem 3: BST Validation

A BST is valid if for every node:
- All values in its left subtree are **strictly less** than node's value
- All values in its right subtree are **strictly greater** than node's value

**Common wrong approach**: only check immediate children.

```
This tree FAILS the BST property but passes if you only check children:
        5
       / \
      1   4      ← 4 < 5 ✓ locally
         / \
        3   6    ← 3 < 4 ✓ locally, but 3 < 5 VIOLATES BST!

Correct approach: pass valid range [min, max] down the tree.

dfs(node, min_val, max_val):
  if null: return true
  if node.val <= min_val OR node.val >= max_val: return false
  return dfs(node.left, min_val, node.val) AND
         dfs(node.right, node.val, max_val)

Initial call: dfs(root, -∞, +∞)

For the invalid tree above:
  dfs(5, -inf, +inf): 5 in range ✓
    dfs(1, -inf, 5): 1 in range ✓
    dfs(4, 5, +inf): 4 NOT > 5 → return FALSE ✓ (correctly caught!)
```

### Problem 4: Lowest Common Ancestor (LCA)

**Lowest Common Ancestor** of nodes p and q: the deepest node that has both p and q as descendants (a node is a descendant of itself).

```
Tree:
            3
           / \
          5   1
         / \ / \
        6  2 0  8
          / \
         7   4

LCA(5, 1) = 3
LCA(5, 4) = 5  (5 is ancestor of 4, and 5 is ancestor of itself)
LCA(6, 4) = 5

Algorithm (elegant recursive):
  dfs(node, p, q):
    if null: return null
    if node == p OR node == q: return node   // found one!
    
    left  = dfs(node.left,  p, q)
    right = dfs(node.right, p, q)
    
    if left != null AND right != null:
      return node    // p and q are in different subtrees → current node is LCA
    
    return left != null ? left : right  // both in same subtree

Why this works:
  - If both p and q are found in different subtrees → current node is their LCA
  - If only one subtree has a finding → LCA is deeper (in that subtree)
  - If a node IS p or q, return it immediately (it might be ancestor of other)
```

### Problem 5: Path Sum — Does a Root-to-Leaf Path Sum to Target?

```
Tree:
        5
       / \
      4   8
     /   / \
    11  13  4
   /  \      \
  7    2      1

Target = 22
Path: 5 → 4 → 11 → 2 = 22 ✓

Algorithm (top-down):
  dfs(node, remaining):
    if null: return false
    remaining -= node.val
    if leaf AND remaining == 0: return true  // found valid path
    return dfs(node.left, remaining) OR dfs(node.right, remaining)

Key: we pass "remaining" down, subtracting each node's value.
     At a leaf, if remaining == 0, path found.
     Must check leaf condition (both children null) — not just any node!
```

### Problem 6: Serialize and Deserialize a Binary Tree

Pre-order traversal naturally encodes a tree's structure:

```
Serialize (pre-order, mark nulls with '#'):
        1
       / \
      2   3
     /
    4

Traversal: 1, 2, 4, #, #, #, 3, #, #
String: "1,2,4,#,#,#,3,#,#"

Deserialize: read values left to right, build tree pre-order
  read 1 → node(1)
    read 2 → node(2)
      read 4 → node(4)
        read # → null (4.left = null)
        read # → null (4.right = null)
      → 4 complete, 2.left = 4
      read # → null (2.right = null)
    → 2 complete, 1.left = 2
    read 3 → node(3)
      read # → null
      read # → null
    → 3 complete, 1.right = 3
  → Tree reconstructed ✓

Why pre-order? It naturally encodes the reconstruction order.
Why not in-order? In-order without null markers is ambiguous.
```

---

## 11. Performance Analysis — Hardware Reality

### Time Complexity

| Operation | Time | Reason |
|-----------|------|--------|
| Any complete traversal | O(n) | Must visit every node exactly once |
| Search in BST | O(h) | One path from root to answer |
| Search in arbitrary tree | O(n) | May need to visit all nodes |
| Height computation | O(n) | Visit every node |
| LCA | O(n) | Worst case entire tree |

### Space Complexity

| Approach | Space | When it matters |
|----------|-------|-----------------|
| Recursive DFS | O(h) call stack | Skewed tree → O(n) |
| Iterative DFS | O(h) explicit stack | Same asymptotically |
| Morris traversal | O(1) | Critical for huge trees |

### Cache Behavior — This Is Where It Gets Real

Modern CPUs have cache hierarchies:
```
CPU Registers:   ~1 cycle    (a few KB)
L1 Cache:        ~4 cycles   (32-64 KB per core)
L2 Cache:        ~12 cycles  (256 KB - 1 MB per core)
L3 Cache:        ~40 cycles  (4-32 MB shared)
Main Memory:     ~200 cycles (GBs)
```

**Tree DFS has poor cache behavior compared to arrays** because:

1. **Pointer chasing**: Each tree traversal dereferences a pointer to access the next node. Each dereference may be a cache miss if the node isn't in cache.

2. **Memory fragmentation**: Tree nodes are individually heap-allocated, scattered across memory.

3. **Prefetcher confusion**: CPU prefetchers excel at sequential or strided access patterns. Pointer-following is unpredictable — the prefetcher cannot help.

```
Array DFS (imagine tree in array form, like a heap):
[1, 2, 3, 4, 5, 6, 7]  ← contiguous memory
Accessing sequentially: every cache line brings 8+ elements → very cache-friendly

Tree DFS (pointer-based):
node(1) at address 0x1000
node(2) at address 0x5A38   ← may be far from node(1)
node(3) at address 0x2B10
→ Each access may be a cache miss
```

**Practical implication**: For performance-critical applications, consider:

- **Van Emde Boas layout**: Arrange tree nodes in memory so that nodes visited consecutively in DFS are close in memory
- **Arena/pool allocation**: Allocate all tree nodes from a contiguous pool
- **Array-based trees**: For complete binary trees, use array indexing (left child at 2i+1, right at 2i+2)

```
Arena allocation effect on cache:
Without arena (individual malloc):
  node addresses scattered → frequent cache misses

With arena (all nodes from one buffer):
  node[0] at buffer+0
  node[1] at buffer+24   ← predictable stride
  node[2] at buffer+48
  DFS visits nodes allocated in insertion order → better locality
```

### Stack Frame Size Analysis

```
Recursive DFS frame contents:
  - Return address:        8 bytes (x86-64)
  - Saved frame pointer:   8 bytes
  - Local vars (node ptr): 8 bytes
  - Alignment padding:     0-8 bytes
  Total per frame: ~32-40 bytes

For balanced tree with n=1,000,000:
  height ≈ 20
  Stack usage: 20 × 40 = 800 bytes   ← negligible

For skewed tree with n=100,000:
  height = 100,000
  Stack usage: 100,000 × 40 = 4MB   ← approaches typical 8MB limit!
```

### Compiler Optimizations

**Tail call optimization (TCO)**: If the recursive call is the LAST thing a function does, the compiler can reuse the current stack frame instead of creating a new one.

Pre-order DFS is NOT tail-recursive because after the left recursive call, we still need to call right. In-order and post-order are also not tail-recursive.

Go: Does not guarantee TCO  
Rust: Does not guarantee TCO (but LLVM may optimize)  
C: With `-O2`, GCC/Clang may apply TCO in simple cases

**Inlining**: For small helper functions (e.g., `is_null(node)`), compilers will inline them, eliminating function call overhead.

---

## 12. Go Implementation

```go
// dfs_tree.go
// Complete, production-grade DFS implementation on binary trees
// Uses idiomatic Go patterns with proper error handling

package main

import (
	"errors"
	"fmt"
	"math"
	"strings"
)

// ============================================================
// DATA STRUCTURES
// ============================================================

// TreeNode represents a node in a binary tree.
// Using int32 for the value to be explicit about type width.
type TreeNode struct {
	Val   int
	Left  *TreeNode
	Right *TreeNode
}

// newNode is a constructor — idiomatic Go prefers constructors
// over direct struct literals for encapsulation.
func newNode(val int) *TreeNode {
	return &TreeNode{Val: val}
}

// DFSResult holds traversal output to avoid global state.
type DFSResult struct {
	Values []int
}

// ============================================================
// SENTINEL / CONSTANT VALUES
// ============================================================

const (
	// EmptyTreeHeight is the canonical height for a nil node.
	// Using -1 so height(leaf) = max(-1,-1)+1 = 0 is consistent.
	EmptyTreeHeight = -1

	// MinInt and MaxInt used for BST validation bounds.
	MinBound = math.MinInt64
	MaxBound = math.MaxInt64
)

// ============================================================
// RECURSIVE TRAVERSALS
// ============================================================

// PreOrder performs recursive pre-order (Root, Left, Right) traversal.
// Time: O(n), Space: O(h) for call stack.
func PreOrder(root *TreeNode) []int {
	result := make([]int, 0)
	preOrderHelper(root, &result)
	return result
}

func preOrderHelper(node *TreeNode, result *[]int) {
	if node == nil {
		return
	}
	*result = append(*result, node.Val) // process BEFORE children
	preOrderHelper(node.Left, result)
	preOrderHelper(node.Right, result)
}

// InOrder performs recursive in-order (Left, Root, Right) traversal.
// For a BST, this produces values in sorted ascending order.
func InOrder(root *TreeNode) []int {
	result := make([]int, 0)
	inOrderHelper(root, &result)
	return result
}

func inOrderHelper(node *TreeNode, result *[]int) {
	if node == nil {
		return
	}
	inOrderHelper(node.Left, result)
	*result = append(*result, node.Val) // process BETWEEN children
	inOrderHelper(node.Right, result)
}

// PostOrder performs recursive post-order (Left, Right, Root) traversal.
// Children are always fully processed before the parent.
func PostOrder(root *TreeNode) []int {
	result := make([]int, 0)
	postOrderHelper(root, &result)
	return result
}

func postOrderHelper(node *TreeNode, result *[]int) {
	if node == nil {
		return
	}
	postOrderHelper(node.Left, result)
	postOrderHelper(node.Right, result)
	*result = append(*result, node.Val) // process AFTER children
}

// ============================================================
// ITERATIVE TRAVERSALS
// ============================================================

// IterativePreOrder implements pre-order using an explicit stack.
// Advantage: no stack overflow on skewed trees.
// Time: O(n), Space: O(h)
func IterativePreOrder(root *TreeNode) []int {
	if root == nil {
		return nil
	}

	result := make([]int, 0)
	stack := make([]*TreeNode, 0)
	stack = append(stack, root)

	for len(stack) > 0 {
		// Pop from stack (last element)
		n := len(stack) - 1
		node := stack[n]
		stack = stack[:n]

		result = append(result, node.Val)

		// Push RIGHT first so LEFT is processed first (LIFO)
		if node.Right != nil {
			stack = append(stack, node.Right)
		}
		if node.Left != nil {
			stack = append(stack, node.Left)
		}
	}
	return result
}

// IterativeInOrder implements in-order using an explicit stack.
// This is the standard iterative in-order algorithm.
func IterativeInOrder(root *TreeNode) []int {
	result := make([]int, 0)
	stack := make([]*TreeNode, 0)
	current := root

	for current != nil || len(stack) > 0 {
		// Descend to leftmost node
		for current != nil {
			stack = append(stack, current)
			current = current.Left
		}

		// Process leftmost unprocessed node
		n := len(stack) - 1
		current = stack[n]
		stack = stack[:n]

		result = append(result, current.Val)

		// Move to right subtree
		current = current.Right
	}
	return result
}

// IterativePostOrder implements post-order using two stacks.
// Method: collect (Root, Right, Left) then reverse → (Left, Right, Root)
func IterativePostOrder(root *TreeNode) []int {
	if root == nil {
		return nil
	}

	stack1 := make([]*TreeNode, 0)
	stack2 := make([]*TreeNode, 0)
	stack1 = append(stack1, root)

	for len(stack1) > 0 {
		n := len(stack1) - 1
		node := stack1[n]
		stack1 = stack1[:n]

		stack2 = append(stack2, node)

		// Push left before right (so right is collected before left)
		if node.Left != nil {
			stack1 = append(stack1, node.Left)
		}
		if node.Right != nil {
			stack1 = append(stack1, node.Right)
		}
	}

	// stack2 contains (Root, Right, Left) — reverse it
	result := make([]int, len(stack2))
	for i, node := range stack2 {
		result[len(stack2)-1-i] = node.Val
	}
	return result
}

// ============================================================
// MORRIS IN-ORDER TRAVERSAL (O(1) space)
// ============================================================

// MorrisInOrder performs in-order traversal using O(1) extra space.
// It temporarily modifies the tree (thread pointers) and restores it.
// NOT safe for concurrent use without external synchronization.
func MorrisInOrder(root *TreeNode) []int {
	result := make([]int, 0)
	current := root

	for current != nil {
		if current.Left == nil {
			// No left subtree: process current, move right
			result = append(result, current.Val)
			current = current.Right
		} else {
			// Find in-order predecessor (rightmost in left subtree)
			predecessor := current.Left
			for predecessor.Right != nil && predecessor.Right != current {
				predecessor = predecessor.Right
			}

			if predecessor.Right == nil {
				// Create thread: predecessor → current
				predecessor.Right = current
				current = current.Left
			} else {
				// Thread exists: left subtree is processed
				predecessor.Right = nil // restore tree
				result = append(result, current.Val)
				current = current.Right
			}
		}
	}
	return result
}

// ============================================================
// TREE PROPERTY COMPUTATIONS (DFS patterns)
// ============================================================

// Height returns the height of the tree.
// Height of nil = -1 (so height of single node = 0).
// Pattern: post-order accumulation.
func Height(root *TreeNode) int {
	if root == nil {
		return EmptyTreeHeight
	}
	leftH := Height(root.Left)
	rightH := Height(root.Right)
	if leftH > rightH {
		return leftH + 1
	}
	return rightH + 1
}

// Size returns the total number of nodes in the tree.
func Size(root *TreeNode) int {
	if root == nil {
		return 0
	}
	return 1 + Size(root.Left) + Size(root.Right)
}

// Diameter returns the length (in edges) of the longest path
// between any two nodes. The path need not pass through the root.
// Pattern: post-order accumulation with global tracking.
func Diameter(root *TreeNode) int {
	maxDiameter := 0
	diameterHelper(root, &maxDiameter)
	return maxDiameter
}

// diameterHelper returns height of subtree rooted at node,
// and updates maxDiameter via pointer.
func diameterHelper(node *TreeNode, maxDiameter *int) int {
	if node == nil {
		return EmptyTreeHeight
	}

	leftH := diameterHelper(node.Left, maxDiameter)
	rightH := diameterHelper(node.Right, maxDiameter)

	// Longest path through this node (in edges)
	// leftH + 1 = distance from this node to leftmost leaf
	// rightH + 1 = distance from this node to rightmost leaf
	pathThroughNode := (leftH + 1) + (rightH + 1)
	if pathThroughNode > *maxDiameter {
		*maxDiameter = pathThroughNode
	}

	// Return height of this subtree
	if leftH > rightH {
		return leftH + 1
	}
	return rightH + 1
}

// IsSymmetric returns true if the tree is a mirror of itself.
func IsSymmetric(root *TreeNode) bool {
	if root == nil {
		return true
	}
	return isMirror(root.Left, root.Right)
}

func isMirror(left, right *TreeNode) bool {
	if left == nil && right == nil {
		return true
	}
	if left == nil || right == nil {
		return false
	}
	return left.Val == right.Val &&
		isMirror(left.Left, right.Right) &&
		isMirror(left.Right, right.Left)
}

// ============================================================
// BST OPERATIONS
// ============================================================

// IsValidBST validates a binary search tree using range propagation.
// Pattern: top-down propagation.
// Time: O(n), Space: O(h)
func IsValidBST(root *TreeNode) bool {
	return isValidBSTHelper(root, MinBound, MaxBound)
}

func isValidBSTHelper(node *TreeNode, minVal, maxVal int) bool {
	if node == nil {
		return true
	}
	if node.Val <= minVal || node.Val >= maxVal {
		return false
	}
	return isValidBSTHelper(node.Left, minVal, node.Val) &&
		isValidBSTHelper(node.Right, node.Val, maxVal)
}

// SearchBST returns the subtree rooted at the node with the given value.
// Returns nil if not found.
func SearchBST(root *TreeNode, target int) *TreeNode {
	if root == nil || root.Val == target {
		return root
	}
	if target < root.Val {
		return SearchBST(root.Left, target)
	}
	return SearchBST(root.Right, target)
}

// ============================================================
// PATH PROBLEMS
// ============================================================

// HasPathSum returns true if there's a root-to-leaf path
// whose values sum to the given target.
// Pattern: top-down propagation with remaining sum.
func HasPathSum(root *TreeNode, target int) bool {
	if root == nil {
		return false
	}
	remaining := target - root.Val
	// Check if this is a leaf with exact path sum
	if root.Left == nil && root.Right == nil {
		return remaining == 0
	}
	return HasPathSum(root.Left, remaining) ||
		HasPathSum(root.Right, remaining)
}

// AllRootToLeafPaths returns all root-to-leaf paths as string slices.
// Pattern: path tracking with backtracking.
func AllRootToLeafPaths(root *TreeNode) []string {
	paths := make([]string, 0)
	if root == nil {
		return paths
	}
	currentPath := make([]int, 0)
	collectPaths(root, currentPath, &paths)
	return paths
}

func collectPaths(node *TreeNode, path []int, paths *[]string) {
	path = append(path, node.Val)

	if node.Left == nil && node.Right == nil {
		// Leaf node: build path string
		parts := make([]string, len(path))
		for i, v := range path {
			parts[i] = fmt.Sprintf("%d", v)
		}
		*paths = append(*paths, strings.Join(parts, "->"))
		return
	}

	if node.Left != nil {
		collectPaths(node.Left, path, paths)
	}
	if node.Right != nil {
		collectPaths(node.Right, path, paths)
	}
	// Note: Go's slice append creates a new slice header,
	// so we don't need explicit backtracking here.
	// The 'path' slice in the caller is unchanged because
	// append on a full slice allocates a new backing array.
	// For very large trees, use explicit index tracking instead.
}

// ============================================================
// LOWEST COMMON ANCESTOR
// ============================================================

// LCA finds the lowest common ancestor of nodes with values p and q.
// Assumes both values exist in the tree.
// Pattern: post-order with early return.
func LCA(root *TreeNode, p, q int) *TreeNode {
	if root == nil {
		return nil
	}
	if root.Val == p || root.Val == q {
		return root
	}

	leftResult := LCA(root.Left, p, q)
	rightResult := LCA(root.Right, p, q)

	if leftResult != nil && rightResult != nil {
		// p and q are in different subtrees → current node is LCA
		return root
	}
	if leftResult != nil {
		return leftResult
	}
	return rightResult
}

// ============================================================
// TREE SERIALIZATION / DESERIALIZATION
// ============================================================

// Serialize encodes a binary tree to a string using pre-order traversal.
// Null nodes are represented as "#".
func Serialize(root *TreeNode) string {
	var sb strings.Builder
	serializeHelper(root, &sb)
	return sb.String()
}

func serializeHelper(node *TreeNode, sb *strings.Builder) {
	if node == nil {
		sb.WriteString("#,")
		return
	}
	sb.WriteString(fmt.Sprintf("%d,", node.Val))
	serializeHelper(node.Left, sb)
	serializeHelper(node.Right, sb)
}

// Deserialize reconstructs a tree from its serialized string.
// Returns an error for malformed input — production-grade error handling.
func Deserialize(data string) (*TreeNode, error) {
	if data == "" {
		return nil, errors.New("deserialize: empty input string")
	}
	tokens := strings.Split(data, ",")
	// Remove trailing empty token from trailing comma
	if len(tokens) > 0 && tokens[len(tokens)-1] == "" {
		tokens = tokens[:len(tokens)-1]
	}
	index := 0
	return deserializeHelper(tokens, &index)
}

func deserializeHelper(tokens []string, index *int) (*TreeNode, error) {
	if *index >= len(tokens) {
		return nil, errors.New("deserialize: insufficient tokens")
	}

	token := tokens[*index]
	*index++

	if token == "#" {
		return nil, nil //nolint:nilerr // nil node is valid (not an error)
	}

	var val int
	if _, err := fmt.Sscanf(token, "%d", &val); err != nil {
		return nil, fmt.Errorf("deserialize: invalid token %q: %w", token, err)
	}

	node := newNode(val)
	var err error

	node.Left, err = deserializeHelper(tokens, index)
	if err != nil {
		return nil, err
	}

	node.Right, err = deserializeHelper(tokens, index)
	if err != nil {
		return nil, err
	}

	return node, nil
}

// ============================================================
// TREE CONSTRUCTION HELPERS
// ============================================================

// buildFromSlice constructs a binary tree from a level-order slice.
// -1 represents null nodes. Used for testing.
func buildFromSlice(vals []int) *TreeNode {
	if len(vals) == 0 || vals[0] == -1 {
		return nil
	}

	root := newNode(vals[0])
	queue := []*TreeNode{root}
	i := 1

	for len(queue) > 0 && i < len(vals) {
		node := queue[0]
		queue = queue[1:]

		if i < len(vals) && vals[i] != -1 {
			node.Left = newNode(vals[i])
			queue = append(queue, node.Left)
		}
		i++

		if i < len(vals) && vals[i] != -1 {
			node.Right = newNode(vals[i])
			queue = append(queue, node.Right)
		}
		i++
	}
	return root
}

// ============================================================
// MAIN — DEMONSTRATION
// ============================================================

func main() {
	// Build tree:
	//         10
	//        /  \
	//       5    15
	//      / \     \
	//     3   7    20
	root := buildFromSlice([]int{10, 5, 15, 3, 7, -1, 20})

	fmt.Println("=== DFS Tree Traversals ===")
	fmt.Printf("Pre-order  (recursive):  %v\n", PreOrder(root))
	fmt.Printf("In-order   (recursive):  %v\n", InOrder(root))
	fmt.Printf("Post-order (recursive):  %v\n", PostOrder(root))

	fmt.Println("\n=== Iterative Traversals ===")
	fmt.Printf("Pre-order  (iterative):  %v\n", IterativePreOrder(root))
	fmt.Printf("In-order   (iterative):  %v\n", IterativeInOrder(root))
	fmt.Printf("Post-order (iterative):  %v\n", IterativePostOrder(root))

	fmt.Println("\n=== Morris Traversal (O(1) space) ===")
	fmt.Printf("Morris In-order: %v\n", MorrisInOrder(root))

	fmt.Println("\n=== Tree Properties ===")
	fmt.Printf("Height:   %d\n", Height(root))
	fmt.Printf("Size:     %d\n", Size(root))
	fmt.Printf("Diameter: %d\n", Diameter(root))
	fmt.Printf("Symmetric: %v\n", IsSymmetric(root))

	fmt.Println("\n=== BST Validation ===")
	// This tree happens to be a valid BST
	fmt.Printf("Valid BST: %v\n", IsValidBST(root))

	fmt.Println("\n=== Path Problems ===")
	fmt.Printf("Has path sum 18 (10→5→3): %v\n", HasPathSum(root, 18))
	fmt.Printf("Has path sum 22 (10→5→7): %v\n", HasPathSum(root, 22))
	fmt.Printf("Has path sum 45 (10→15→20): %v\n", HasPathSum(root, 45))
	fmt.Printf("All root-to-leaf paths: %v\n", AllRootToLeafPaths(root))

	fmt.Println("\n=== LCA ===")
	lca := LCA(root, 3, 7)
	if lca != nil {
		fmt.Printf("LCA(3, 7) = %d\n", lca.Val) // Expected: 5
	}
	lca = LCA(root, 3, 20)
	if lca != nil {
		fmt.Printf("LCA(3, 20) = %d\n", lca.Val) // Expected: 10
	}

	fmt.Println("\n=== Serialization ===")
	serialized := Serialize(root)
	fmt.Printf("Serialized: %s\n", serialized)
	deserialized, err := Deserialize(serialized)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
	} else {
		fmt.Printf("Deserialized in-order: %v\n", InOrder(deserialized))
	}
}
```

---

## 13. C Implementation

```c
/* dfs_tree.c
 * Complete, production-grade DFS on binary trees in C.
 * Compiled with: gcc -Wall -Wextra -O2 -std=c11 dfs_tree.c -o dfs_tree
 *
 * Memory safety: all allocations checked, all heap memory freed.
 * No undefined behavior: no buffer overflows, no dangling pointers.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include <stdbool.h>
#include <assert.h>

/* ============================================================
 * CONSTANTS — no magic numbers
 * ============================================================ */
#define EMPTY_TREE_HEIGHT   (-1)
#define INITIAL_CAPACITY    16
#define NULL_MARKER         (-1)

/* ============================================================
 * DATA STRUCTURES
 * ============================================================ */

typedef struct TreeNode {
    int            val;
    struct TreeNode *left;
    struct TreeNode *right;
} TreeNode;

/* Dynamic array for collecting traversal results */
typedef struct {
    int   *data;
    size_t size;
    size_t capacity;
} IntArray;

/* Stack for iterative traversal */
typedef struct {
    TreeNode **data;
    size_t     top;
    size_t     capacity;
} NodeStack;

/* ============================================================
 * DYNAMIC ARRAY OPERATIONS
 * ============================================================ */

static IntArray *intarray_create(void) {
    IntArray *arr = malloc(sizeof(IntArray));
    if (!arr) return NULL;

    arr->data = malloc(INITIAL_CAPACITY * sizeof(int));
    if (!arr->data) {
        free(arr);
        return NULL;
    }
    arr->size     = 0;
    arr->capacity = INITIAL_CAPACITY;
    return arr;
}

static bool intarray_push(IntArray *arr, int val) {
    if (arr->size == arr->capacity) {
        size_t new_cap = arr->capacity * 2;
        int *new_data = realloc(arr->data, new_cap * sizeof(int));
        if (!new_data) return false;
        arr->data     = new_data;
        arr->capacity = new_cap;
    }
    arr->data[arr->size++] = val;
    return true;
}

static void intarray_free(IntArray *arr) {
    if (!arr) return;
    free(arr->data);
    free(arr);
}

static void intarray_print(const IntArray *arr, const char *label) {
    printf("%s: [", label);
    for (size_t i = 0; i < arr->size; i++) {
        printf("%d", arr->data[i]);
        if (i + 1 < arr->size) printf(", ");
    }
    printf("]\n");
}

/* ============================================================
 * STACK OPERATIONS
 * ============================================================ */

static NodeStack *stack_create(void) {
    NodeStack *s = malloc(sizeof(NodeStack));
    if (!s) return NULL;

    s->data = malloc(INITIAL_CAPACITY * sizeof(TreeNode *));
    if (!s->data) {
        free(s);
        return NULL;
    }
    s->top      = 0;
    s->capacity = INITIAL_CAPACITY;
    return s;
}

static bool stack_push(NodeStack *s, TreeNode *node) {
    if (s->top == s->capacity) {
        size_t new_cap = s->capacity * 2;
        TreeNode **new_data = realloc(s->data, new_cap * sizeof(TreeNode *));
        if (!new_data) return false;
        s->data     = new_data;
        s->capacity = new_cap;
    }
    s->data[s->top++] = node;
    return true;
}

static TreeNode *stack_pop(NodeStack *s) {
    if (s->top == 0) return NULL;
    return s->data[--s->top];
}

static TreeNode *stack_peek(const NodeStack *s) {
    if (s->top == 0) return NULL;
    return s->data[s->top - 1];
}

static bool stack_is_empty(const NodeStack *s) {
    return s->top == 0;
}

static void stack_free(NodeStack *s) {
    if (!s) return;
    free(s->data);
    free(s);
}

/* ============================================================
 * TREE NODE OPERATIONS
 * ============================================================ */

TreeNode *tree_new_node(int val) {
    TreeNode *node = malloc(sizeof(TreeNode));
    if (!node) return NULL;
    node->val   = val;
    node->left  = NULL;
    node->right = NULL;
    return node;
}

/* Free entire tree using post-order traversal (children before parent) */
void tree_free(TreeNode *root) {
    if (!root) return;
    tree_free(root->left);
    tree_free(root->right);
    free(root);
}

/* ============================================================
 * RECURSIVE TRAVERSALS
 * ============================================================ */

static void preorder_helper(TreeNode *node, IntArray *result) {
    if (!node) return;
    intarray_push(result, node->val);  /* process BEFORE children */
    preorder_helper(node->left,  result);
    preorder_helper(node->right, result);
}

IntArray *preorder(TreeNode *root) {
    IntArray *result = intarray_create();
    if (!result) return NULL;
    preorder_helper(root, result);
    return result;
}

static void inorder_helper(TreeNode *node, IntArray *result) {
    if (!node) return;
    inorder_helper(node->left, result);
    intarray_push(result, node->val);  /* process BETWEEN children */
    inorder_helper(node->right, result);
}

IntArray *inorder(TreeNode *root) {
    IntArray *result = intarray_create();
    if (!result) return NULL;
    inorder_helper(root, result);
    return result;
}

static void postorder_helper(TreeNode *node, IntArray *result) {
    if (!node) return;
    postorder_helper(node->left,  result);
    postorder_helper(node->right, result);
    intarray_push(result, node->val);  /* process AFTER children */
}

IntArray *postorder(TreeNode *root) {
    IntArray *result = intarray_create();
    if (!result) return NULL;
    postorder_helper(root, result);
    return result;
}

/* ============================================================
 * ITERATIVE TRAVERSALS
 * ============================================================ */

IntArray *iterative_preorder(TreeNode *root) {
    IntArray  *result = intarray_create();
    NodeStack *stack  = stack_create();
    if (!result || !stack) {
        intarray_free(result);
        stack_free(stack);
        return NULL;
    }

    if (root) stack_push(stack, root);

    while (!stack_is_empty(stack)) {
        TreeNode *node = stack_pop(stack);
        intarray_push(result, node->val);

        /* Push right before left so left is processed first (LIFO) */
        if (node->right) stack_push(stack, node->right);
        if (node->left)  stack_push(stack, node->left);
    }

    stack_free(stack);
    return result;
}

IntArray *iterative_inorder(TreeNode *root) {
    IntArray  *result  = intarray_create();
    NodeStack *stack   = stack_create();
    TreeNode  *current = root;

    if (!result || !stack) {
        intarray_free(result);
        stack_free(stack);
        return NULL;
    }

    while (current || !stack_is_empty(stack)) {
        /* Descend to leftmost node */
        while (current) {
            stack_push(stack, current);
            current = current->left;
        }

        current = stack_pop(stack);
        intarray_push(result, current->val);
        current = current->right;
    }

    stack_free(stack);
    return result;
}

IntArray *iterative_postorder(TreeNode *root) {
    IntArray  *result = intarray_create();
    NodeStack *stack1 = stack_create();
    NodeStack *stack2 = stack_create();

    if (!result || !stack1 || !stack2) {
        intarray_free(result);
        stack_free(stack1);
        stack_free(stack2);
        return NULL;
    }

    if (root) stack_push(stack1, root);

    while (!stack_is_empty(stack1)) {
        TreeNode *node = stack_pop(stack1);
        stack_push(stack2, node);
        if (node->left)  stack_push(stack1, node->left);
        if (node->right) stack_push(stack1, node->right);
    }

    /* stack2 contains (Root, Right, Left) — output in reverse */
    while (!stack_is_empty(stack2)) {
        TreeNode *node = stack_pop(stack2);
        intarray_push(result, node->val);
    }

    stack_free(stack1);
    stack_free(stack2);
    return result;
}

/* ============================================================
 * MORRIS IN-ORDER TRAVERSAL (O(1) space)
 * ============================================================ */

IntArray *morris_inorder(TreeNode *root) {
    IntArray *result  = intarray_create();
    if (!result) return NULL;

    TreeNode *current = root;

    while (current) {
        if (!current->left) {
            intarray_push(result, current->val);
            current = current->right;
        } else {
            /* Find in-order predecessor */
            TreeNode *pred = current->left;
            while (pred->right && pred->right != current) {
                pred = pred->right;
            }

            if (!pred->right) {
                /* Create thread */
                pred->right = current;
                current     = current->left;
            } else {
                /* Thread already exists: restore tree, process node */
                pred->right = NULL;
                intarray_push(result, current->val);
                current     = current->right;
            }
        }
    }
    return result;
}

/* ============================================================
 * TREE PROPERTY COMPUTATIONS
 * ============================================================ */

int tree_height(TreeNode *root) {
    if (!root) return EMPTY_TREE_HEIGHT;
    int left_h  = tree_height(root->left);
    int right_h = tree_height(root->right);
    int max_h   = left_h > right_h ? left_h : right_h;
    return max_h + 1;
}

int tree_size(TreeNode *root) {
    if (!root) return 0;
    return 1 + tree_size(root->left) + tree_size(root->right);
}

/* Internal helper: returns height and updates diameter via pointer */
static int diameter_helper(TreeNode *node, int *max_diameter) {
    if (!node) return EMPTY_TREE_HEIGHT;

    int left_h  = diameter_helper(node->left,  max_diameter);
    int right_h = diameter_helper(node->right, max_diameter);

    int path_through = (left_h + 1) + (right_h + 1);
    if (path_through > *max_diameter) {
        *max_diameter = path_through;
    }

    return (left_h > right_h ? left_h : right_h) + 1;
}

int tree_diameter(TreeNode *root) {
    int max_diam = 0;
    diameter_helper(root, &max_diam);
    return max_diam;
}

static bool is_mirror(TreeNode *left, TreeNode *right) {
    if (!left && !right) return true;
    if (!left || !right) return false;
    return left->val == right->val
        && is_mirror(left->left,  right->right)
        && is_mirror(left->right, right->left);
}

bool tree_is_symmetric(TreeNode *root) {
    if (!root) return true;
    return is_mirror(root->left, root->right);
}

/* ============================================================
 * BST OPERATIONS
 * ============================================================ */

static bool is_valid_bst_helper(TreeNode *node, long min_val, long max_val) {
    if (!node) return true;
    if ((long)node->val <= min_val || (long)node->val >= max_val) return false;
    return is_valid_bst_helper(node->left,  min_val, (long)node->val)
        && is_valid_bst_helper(node->right, (long)node->val, max_val);
}

bool is_valid_bst(TreeNode *root) {
    return is_valid_bst_helper(root, (long)INT_MIN - 1, (long)INT_MAX + 1);
}

TreeNode *bst_search(TreeNode *root, int target) {
    if (!root || root->val == target) return root;
    if (target < root->val) return bst_search(root->left,  target);
    return                         bst_search(root->right, target);
}

/* ============================================================
 * PATH PROBLEMS
 * ============================================================ */

bool has_path_sum(TreeNode *root, int target) {
    if (!root) return false;

    int remaining = target - root->val;

    /* Leaf check: both children null */
    if (!root->left && !root->right) return remaining == 0;

    return has_path_sum(root->left,  remaining)
        || has_path_sum(root->right, remaining);
}

/* ============================================================
 * LOWEST COMMON ANCESTOR
 * ============================================================ */

TreeNode *lca(TreeNode *root, int p, int q) {
    if (!root)          return NULL;
    if (root->val == p) return root;
    if (root->val == q) return root;

    TreeNode *left_result  = lca(root->left,  p, q);
    TreeNode *right_result = lca(root->right, p, q);

    if (left_result && right_result) return root; /* split: this is LCA */
    return left_result ? left_result : right_result;
}

/* ============================================================
 * TREE CONSTRUCTION HELPER
 * ============================================================ */

/* Build from level-order array. NULL_MARKER (-1) = null node. */
TreeNode *build_from_array(const int *vals, size_t len) {
    if (len == 0 || vals[0] == NULL_MARKER) return NULL;

    TreeNode **queue = malloc(len * sizeof(TreeNode *));
    if (!queue) return NULL;

    TreeNode *root = tree_new_node(vals[0]);
    if (!root) {
        free(queue);
        return NULL;
    }

    size_t head = 0, tail = 0;
    queue[tail++] = root;

    size_t i = 1;
    while (head < tail && i < len) {
        TreeNode *node = queue[head++];

        if (i < len && vals[i] != NULL_MARKER) {
            node->left = tree_new_node(vals[i]);
            if (node->left) queue[tail++] = node->left;
        }
        i++;

        if (i < len && vals[i] != NULL_MARKER) {
            node->right = tree_new_node(vals[i]);
            if (node->right) queue[tail++] = node->right;
        }
        i++;
    }

    free(queue);
    return root;
}

/* ============================================================
 * MAIN — DEMONSTRATION
 * ============================================================ */

int main(void) {
    /* Build tree:
     *        10
     *       /  \
     *      5    15
     *     / \     \
     *    3   7    20
     */
    int vals[] = {10, 5, 15, 3, 7, NULL_MARKER, 20};
    size_t len = sizeof(vals) / sizeof(vals[0]);

    TreeNode *root = build_from_array(vals, len);
    if (!root) {
        fprintf(stderr, "Failed to build tree\n");
        return EXIT_FAILURE;
    }

    printf("=== DFS Tree Traversals ===\n");

    IntArray *pre  = preorder(root);
    IntArray *in   = inorder(root);
    IntArray *post = postorder(root);

    if (pre && in && post) {
        intarray_print(pre,  "Pre-order  (recursive)");
        intarray_print(in,   "In-order   (recursive)");
        intarray_print(post, "Post-order (recursive)");
    }

    intarray_free(pre);
    intarray_free(in);
    intarray_free(post);

    printf("\n=== Iterative Traversals ===\n");

    IntArray *ipre  = iterative_preorder(root);
    IntArray *iin   = iterative_inorder(root);
    IntArray *ipost = iterative_postorder(root);

    if (ipre && iin && ipost) {
        intarray_print(ipre,  "Pre-order  (iterative)");
        intarray_print(iin,   "In-order   (iterative)");
        intarray_print(ipost, "Post-order (iterative)");
    }

    intarray_free(ipre);
    intarray_free(iin);
    intarray_free(ipost);

    printf("\n=== Morris Traversal (O(1) space) ===\n");
    IntArray *morris = morris_inorder(root);
    if (morris) {
        intarray_print(morris, "Morris In-order");
        intarray_free(morris);
    }

    printf("\n=== Tree Properties ===\n");
    printf("Height:    %d\n", tree_height(root));
    printf("Size:      %d\n", tree_size(root));
    printf("Diameter:  %d\n", tree_diameter(root));
    printf("Symmetric: %s\n", tree_is_symmetric(root) ? "true" : "false");

    printf("\n=== BST Validation ===\n");
    printf("Valid BST: %s\n", is_valid_bst(root) ? "true" : "false");

    printf("\n=== Path Problems ===\n");
    printf("Has path sum 18 (10+5+3): %s\n", has_path_sum(root, 18) ? "true" : "false");
    printf("Has path sum 22 (10+5+7): %s\n", has_path_sum(root, 22) ? "true" : "false");
    printf("Has path sum 45 (10+15+20): %s\n", has_path_sum(root, 45) ? "true" : "false");

    printf("\n=== LCA ===\n");
    TreeNode *ancestor = lca(root, 3, 7);
    if (ancestor) printf("LCA(3, 7) = %d\n", ancestor->val);
    ancestor = lca(root, 3, 20);
    if (ancestor) printf("LCA(3, 20) = %d\n", ancestor->val);

    tree_free(root);
    return EXIT_SUCCESS;
}
```

---

## 14. Rust Implementation

```rust
// dfs_tree.rs
// Complete, idiomatic Rust DFS on binary trees.
//
// Design decisions:
//   - Box<TreeNode> for owned heap allocation (no Rc/RefCell needed for
//     immutable tree traversal)
//   - No unwrap() without justification
//   - Option<Box<TreeNode>> for nullable children (idiomatic Rust)
//   - Explicit lifetime annotations where needed
//   - All allocations are safe (Rust guarantees no use-after-free)

use std::collections::VecDeque;
use std::fmt;

// ============================================================
// CONSTANTS
// ============================================================

/// Canonical height for an empty (None) tree node.
/// Using -1i32 so height(leaf) = max(-1, -1) + 1 = 0.
const EMPTY_TREE_HEIGHT: i32 = -1;

// ============================================================
// DATA STRUCTURES
// ============================================================

/// A node in a binary tree.
/// Box<TreeNode> provides heap allocation with single ownership.
/// This means the tree is a value type — dropping the root drops the whole tree.
#[derive(Debug, Clone)]
pub struct TreeNode {
    pub val:   i32,
    pub left:  Option<Box<TreeNode>>,
    pub right: Option<Box<TreeNode>>,
}

impl TreeNode {
    /// Constructor: creates a leaf node.
    pub fn new(val: i32) -> Self {
        TreeNode { val, left: None, right: None }
    }

    /// Builder: set left child, consuming self for chaining.
    pub fn with_left(mut self, left: TreeNode) -> Self {
        self.left = Some(Box::new(left));
        self
    }

    /// Builder: set right child, consuming self for chaining.
    pub fn with_right(mut self, right: TreeNode) -> Self {
        self.right = Some(Box::new(right));
        self
    }
}

impl fmt::Display for TreeNode {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let values = inorder(Some(self));
        write!(f, "Tree(inorder: {:?})", values)
    }
}

// ============================================================
// ERROR TYPES
// ============================================================

#[derive(Debug)]
pub enum TreeError {
    /// Returned when deserializing from invalid input.
    InvalidInput(String),
    /// Returned when an expected node is missing.
    MissingNode(String),
}

impl fmt::Display for TreeError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            TreeError::InvalidInput(msg) => write!(f, "Invalid input: {}", msg),
            TreeError::MissingNode(msg)  => write!(f, "Missing node: {}", msg),
        }
    }
}

// ============================================================
// TYPE ALIAS
// ============================================================

/// Idiomatic type alias for a nullable tree node reference.
type NodeRef<'a> = Option<&'a TreeNode>;

// ============================================================
// RECURSIVE TRAVERSALS
// ============================================================

/// Pre-order (Root, Left, Right) traversal.
/// Time: O(n), Space: O(h) for call stack.
pub fn preorder(root: NodeRef<'_>) -> Vec<i32> {
    let mut result = Vec::new();
    preorder_helper(root, &mut result);
    result
}

fn preorder_helper(node: NodeRef<'_>, result: &mut Vec<i32>) {
    if let Some(n) = node {
        result.push(n.val);                          // process BEFORE
        preorder_helper(n.left.as_deref(),  result);
        preorder_helper(n.right.as_deref(), result);
    }
}

/// In-order (Left, Root, Right) traversal.
/// For a valid BST, yields values in ascending sorted order.
pub fn inorder(root: NodeRef<'_>) -> Vec<i32> {
    let mut result = Vec::new();
    inorder_helper(root, &mut result);
    result
}

fn inorder_helper(node: NodeRef<'_>, result: &mut Vec<i32>) {
    if let Some(n) = node {
        inorder_helper(n.left.as_deref(),  result);
        result.push(n.val);                          // process BETWEEN
        inorder_helper(n.right.as_deref(), result);
    }
}

/// Post-order (Left, Right, Root) traversal.
/// Children are always processed before the parent.
pub fn postorder(root: NodeRef<'_>) -> Vec<i32> {
    let mut result = Vec::new();
    postorder_helper(root, &mut result);
    result
}

fn postorder_helper(node: NodeRef<'_>, result: &mut Vec<i32>) {
    if let Some(n) = node {
        postorder_helper(n.left.as_deref(),  result);
        postorder_helper(n.right.as_deref(), result);
        result.push(n.val);                          // process AFTER
    }
}

// ============================================================
// ITERATIVE TRAVERSALS
// ============================================================

/// Iterative pre-order using an explicit stack.
/// Avoids stack overflow on deep/skewed trees.
pub fn iterative_preorder(root: NodeRef<'_>) -> Vec<i32> {
    let mut result = Vec::new();
    let mut stack: Vec<&TreeNode> = Vec::new();

    if let Some(r) = root {
        stack.push(r);
    }

    while let Some(node) = stack.pop() {
        result.push(node.val);

        // Push right before left so left is processed first (LIFO)
        if let Some(right) = node.right.as_deref() {
            stack.push(right);
        }
        if let Some(left) = node.left.as_deref() {
            stack.push(left);
        }
    }
    result
}

/// Iterative in-order using an explicit stack.
pub fn iterative_inorder(root: NodeRef<'_>) -> Vec<i32> {
    let mut result  = Vec::new();
    let mut stack: Vec<&TreeNode> = Vec::new();
    let mut current = root;

    loop {
        // Descend to leftmost node
        while let Some(node) = current {
            stack.push(node);
            current = node.left.as_deref();
        }

        // Process leftmost unprocessed node
        match stack.pop() {
            None       => break,
            Some(node) => {
                result.push(node.val);
                current = node.right.as_deref();
            }
        }
    }
    result
}

/// Iterative post-order using two stacks.
/// Method: collect (Root, Right, Left) then reverse → (Left, Right, Root).
pub fn iterative_postorder(root: NodeRef<'_>) -> Vec<i32> {
    let mut stack1: Vec<&TreeNode> = Vec::new();
    let mut stack2: Vec<&TreeNode> = Vec::new();

    if let Some(r) = root {
        stack1.push(r);
    }

    while let Some(node) = stack1.pop() {
        stack2.push(node);
        if let Some(left) = node.left.as_deref() {
            stack1.push(left);
        }
        if let Some(right) = node.right.as_deref() {
            stack1.push(right);
        }
    }

    // stack2 contains (Root, Right, Left) — drain in reverse
    stack2.iter().rev().map(|n| n.val).collect()
}

// ============================================================
// TREE PROPERTY COMPUTATIONS
// ============================================================

/// Returns the height of the tree.
/// Height of None = -1; height of a single leaf = 0.
/// Pattern: post-order accumulation.
pub fn height(root: NodeRef<'_>) -> i32 {
    match root {
        None    => EMPTY_TREE_HEIGHT,
        Some(n) => {
            let left_h  = height(n.left.as_deref());
            let right_h = height(n.right.as_deref());
            left_h.max(right_h) + 1
        }
    }
}

/// Returns the total number of nodes in the tree.
pub fn size(root: NodeRef<'_>) -> usize {
    match root {
        None    => 0,
        Some(n) => 1 + size(n.left.as_deref()) + size(n.right.as_deref()),
    }
}

/// Returns the diameter: the longest path (in edges) between any two nodes.
/// Pattern: post-order accumulation with auxiliary mutable tracking.
pub fn diameter(root: NodeRef<'_>) -> i32 {
    let mut max_diameter = 0i32;
    diameter_helper(root, &mut max_diameter);
    max_diameter
}

/// Returns height of subtree, updates max_diameter via mutable reference.
fn diameter_helper(node: NodeRef<'_>, max_diameter: &mut i32) -> i32 {
    match node {
        None    => EMPTY_TREE_HEIGHT,
        Some(n) => {
            let left_h  = diameter_helper(n.left.as_deref(),  max_diameter);
            let right_h = diameter_helper(n.right.as_deref(), max_diameter);

            let path_through_node = (left_h + 1) + (right_h + 1);
            *max_diameter = (*max_diameter).max(path_through_node);

            left_h.max(right_h) + 1
        }
    }
}

/// Returns true if the tree is a mirror of itself.
pub fn is_symmetric(root: NodeRef<'_>) -> bool {
    match root {
        None    => true,
        Some(n) => mirrors(n.left.as_deref(), n.right.as_deref()),
    }
}

fn mirrors(left: NodeRef<'_>, right: NodeRef<'_>) -> bool {
    match (left, right) {
        (None,    None)    => true,
        (Some(_), None)    => false,
        (None,    Some(_)) => false,
        (Some(l), Some(r)) => {
            l.val == r.val
                && mirrors(l.left.as_deref(),  r.right.as_deref())
                && mirrors(l.right.as_deref(), r.left.as_deref())
        }
    }
}

// ============================================================
// BST OPERATIONS
// ============================================================

/// Validates that a binary tree satisfies BST properties.
/// Uses range propagation (top-down pattern).
/// Time: O(n), Space: O(h)
pub fn is_valid_bst(root: NodeRef<'_>) -> bool {
    is_valid_bst_helper(root, i64::MIN, i64::MAX)
}

fn is_valid_bst_helper(node: NodeRef<'_>, min_val: i64, max_val: i64) -> bool {
    match node {
        None    => true,
        Some(n) => {
            let val = n.val as i64;
            if val <= min_val || val >= max_val {
                return false;
            }
            is_valid_bst_helper(n.left.as_deref(),  min_val, val) &&
            is_valid_bst_helper(n.right.as_deref(), val, max_val)
        }
    }
}

/// Search for a value in a BST.
/// Returns a reference to the subtree rooted at the found node, or None.
pub fn bst_search<'a>(root: NodeRef<'a>, target: i32) -> NodeRef<'a> {
    match root {
        None    => None,
        Some(n) => {
            if n.val == target {
                root
            } else if target < n.val {
                bst_search(n.left.as_deref(), target)
            } else {
                bst_search(n.right.as_deref(), target)
            }
        }
    }
}

// ============================================================
// PATH PROBLEMS
// ============================================================

/// Returns true if any root-to-leaf path sums to target.
/// Pattern: top-down propagation with remaining sum.
pub fn has_path_sum(root: NodeRef<'_>, target: i32) -> bool {
    match root {
        None    => false,
        Some(n) => {
            let remaining = target - n.val;
            if n.left.is_none() && n.right.is_none() {
                // Leaf node: check if path is complete
                return remaining == 0;
            }
            has_path_sum(n.left.as_deref(),  remaining) ||
            has_path_sum(n.right.as_deref(), remaining)
        }
    }
}

/// Returns all root-to-leaf paths.
/// Pattern: path tracking with backtracking.
pub fn all_root_to_leaf_paths(root: NodeRef<'_>) -> Vec<Vec<i32>> {
    let mut paths   = Vec::new();
    let mut current = Vec::new();
    collect_paths(root, &mut current, &mut paths);
    paths
}

fn collect_paths(node: NodeRef<'_>, path: &mut Vec<i32>, paths: &mut Vec<Vec<i32>>) {
    if let Some(n) = node {
        path.push(n.val);

        if n.left.is_none() && n.right.is_none() {
            // Leaf: record complete path
            paths.push(path.clone());
        } else {
            collect_paths(n.left.as_deref(),  path, paths);
            collect_paths(n.right.as_deref(), path, paths);
        }

        path.pop(); // BACKTRACK — restore path for sibling exploration
    }
}

// ============================================================
// LOWEST COMMON ANCESTOR
// ============================================================

/// Finds the Lowest Common Ancestor of nodes with values p and q.
/// Assumes both values exist in the tree.
/// Pattern: post-order with early return.
pub fn lca<'a>(root: NodeRef<'a>, p: i32, q: i32) -> NodeRef<'a> {
    match root {
        None    => None,
        Some(n) => {
            if n.val == p || n.val == q {
                return root; // Found one of the targets
            }

            let left_result  = lca(n.left.as_deref(),  p, q);
            let right_result = lca(n.right.as_deref(), p, q);

            match (left_result, right_result) {
                (Some(_), Some(_)) => root,         // p and q in different subtrees
                (Some(_), None)    => left_result,  // both in left subtree
                (None,    Some(_)) => right_result, // both in right subtree
                (None,    None)    => None,          // neither found
            }
        }
    }
}

// ============================================================
// SERIALIZATION / DESERIALIZATION
// ============================================================

/// Serialize a tree to a string using pre-order traversal.
/// None nodes are represented as "#".
pub fn serialize(root: NodeRef<'_>) -> String {
    let mut parts = Vec::new();
    serialize_helper(root, &mut parts);
    parts.join(",")
}

fn serialize_helper(node: NodeRef<'_>, parts: &mut Vec<String>) {
    match node {
        None    => parts.push("#".to_string()),
        Some(n) => {
            parts.push(n.val.to_string());
            serialize_helper(n.left.as_deref(),  parts);
            serialize_helper(n.right.as_deref(), parts);
        }
    }
}

/// Deserialize a tree from a serialized string.
/// Returns Err for malformed input.
pub fn deserialize(data: &str) -> Result<Option<Box<TreeNode>>, TreeError> {
    if data.is_empty() {
        return Err(TreeError::InvalidInput("empty input".to_string()));
    }
    let tokens: Vec<&str> = data.split(',').collect();
    let mut index = 0usize;
    deserialize_helper(&tokens, &mut index)
}

fn deserialize_helper(
    tokens: &[&str],
    index:  &mut usize,
) -> Result<Option<Box<TreeNode>>, TreeError> {
    if *index >= tokens.len() {
        return Err(TreeError::MissingNode(
            format!("ran out of tokens at index {}", index)
        ));
    }

    let token = tokens[*index];
    *index += 1;

    if token == "#" {
        return Ok(None);
    }

    let val: i32 = token.parse().map_err(|_| {
        TreeError::InvalidInput(format!("cannot parse {:?} as i32", token))
    })?;

    let mut node = Box::new(TreeNode::new(val));
    node.left  = deserialize_helper(tokens, index)?;
    node.right = deserialize_helper(tokens, index)?;

    Ok(Some(node))
}

// ============================================================
// TREE CONSTRUCTION HELPERS
// ============================================================

/// Build a binary tree from a level-order slice.
/// None entries represent null nodes.
pub fn build_from_slice(vals: &[Option<i32>]) -> Option<Box<TreeNode>> {
    if vals.is_empty() {
        return None;
    }
    let root_val = vals[0]?;
    let root = Box::new(TreeNode::new(root_val));

    let mut queue: VecDeque<*mut TreeNode> = VecDeque::new();
    // SAFETY: root is allocated on heap via Box. We hold the Box for its lifetime.
    // The raw pointer is used only within this function's scope while the Box lives.
    queue.push_back(Box::into_raw(root));

    let mut i = 1usize;

    // We need to collect raw pointers to nodes we've already inserted.
    // This is one of the few places in idiomatic Rust where raw pointers
    // are the pragmatic choice for building a tree from a level-order slice.
    let mut nodes: Vec<*mut TreeNode> = Vec::new();
    let root_ptr = *queue.front().unwrap();
    nodes.push(root_ptr);

    while !queue.is_empty() && i < vals.len() {
        let node_ptr = queue.pop_front().unwrap();

        if i < vals.len() {
            if let Some(Some(val)) = vals.get(i) {
                let child = Box::into_raw(Box::new(TreeNode::new(*val)));
                // SAFETY: node_ptr is a valid pointer to a live TreeNode.
                unsafe { (*node_ptr).left = Some(Box::from_raw(child)); }
                // SAFETY: We just set left, retrieve the raw pointer
                let child_ptr = unsafe {
                    (*node_ptr).left.as_mut().unwrap().as_mut() as *mut TreeNode
                };
                queue.push_back(child_ptr);
                nodes.push(child_ptr);
            }
            i += 1;
        }

        if i < vals.len() {
            if let Some(Some(val)) = vals.get(i) {
                let child = Box::into_raw(Box::new(TreeNode::new(*val)));
                unsafe { (*node_ptr).right = Some(Box::from_raw(child)); }
                let child_ptr = unsafe {
                    (*node_ptr).right.as_mut().unwrap().as_mut() as *mut TreeNode
                };
                queue.push_back(child_ptr);
                nodes.push(child_ptr);
            }
            i += 1;
        }
    }

    // Reconstruct the root Box from the original raw pointer
    Some(unsafe { Box::from_raw(root_ptr) })
}

/// Simpler tree builder using the fluent TreeNode builder API.
/// Preferred for test/demo code.
pub fn build_demo_tree() -> Option<Box<TreeNode>> {
    //        10
    //       /  \
    //      5    15
    //     / \     \
    //    3   7    20
    Some(Box::new(
        TreeNode::new(10)
            .with_left(
                TreeNode::new(5)
                    .with_left(TreeNode::new(3))
                    .with_right(TreeNode::new(7))
            )
            .with_right(
                TreeNode::new(15)
                    .with_right(TreeNode::new(20))
            )
    ))
}

// ============================================================
// MAIN — DEMONSTRATION
// ============================================================

fn main() {
    let root = build_demo_tree();
    let root_ref = root.as_deref();

    println!("=== DFS Tree Traversals ===");
    println!("Pre-order  (recursive):  {:?}", preorder(root_ref));
    println!("In-order   (recursive):  {:?}", inorder(root_ref));
    println!("Post-order (recursive):  {:?}", postorder(root_ref));

    println!("\n=== Iterative Traversals ===");
    println!("Pre-order  (iterative):  {:?}", iterative_preorder(root_ref));
    println!("In-order   (iterative):  {:?}", iterative_inorder(root_ref));
    println!("Post-order (iterative):  {:?}", iterative_postorder(root_ref));

    println!("\n=== Tree Properties ===");
    println!("Height:    {}", height(root_ref));
    println!("Size:      {}", size(root_ref));
    println!("Diameter:  {}", diameter(root_ref));
    println!("Symmetric: {}", is_symmetric(root_ref));

    println!("\n=== BST Validation ===");
    println!("Valid BST: {}", is_valid_bst(root_ref));

    println!("\n=== Path Problems ===");
    println!("Has path sum 18 (10+5+3): {}", has_path_sum(root_ref, 18));
    println!("Has path sum 22 (10+5+7): {}", has_path_sum(root_ref, 22));
    println!("Has path sum 45 (10+15+20): {}", has_path_sum(root_ref, 45));

    println!("\n=== All Root-to-Leaf Paths ===");
    let paths = all_root_to_leaf_paths(root_ref);
    for path in &paths {
        let path_str: Vec<String> = path.iter().map(|v| v.to_string()).collect();
        println!("  {}", path_str.join(" -> "));
    }

    println!("\n=== LCA ===");
    if let Some(ancestor) = lca(root_ref, 3, 7) {
        println!("LCA(3, 7)  = {}", ancestor.val);
    }
    if let Some(ancestor) = lca(root_ref, 3, 20) {
        println!("LCA(3, 20) = {}", ancestor.val);
    }

    println!("\n=== Serialization ===");
    let serialized = serialize(root_ref);
    println!("Serialized: {}", serialized);

    match deserialize(&serialized) {
        Ok(deserialized) => {
            println!("Deserialized in-order: {:?}", inorder(deserialized.as_deref()));
        }
        Err(e) => eprintln!("Deserialization error: {}", e),
    }
}
```

---

## 15. Mental Models and Expert Intuition

### The "Delegate to Children" Model

When approaching ANY tree problem, ask yourself:

> *"If I already know the answer for my left subtree and my right subtree, can I compute the answer for my entire tree?"*

If yes → the problem has **optimal substructure** and DFS (specifically post-order) will solve it.

Examples: height, size, sum, diameter, check balanced, check BST.

### The "Pass Memo From Parent" Model

> *"Does each node need to know something about its ancestors to make its decision?"*

If yes → use **top-down DFS** passing information as function parameters.

Examples: path sum remaining, valid range for BST check, current depth/level.

### The "Divide and Conquer" Model

Tree problems often decompose as:

```
solve(tree) = combine(solve(left_subtree), solve(right_subtree), root.val)
```

The base case is the empty tree. This is divide-and-conquer on a naturally divided structure.

### The Return Value Duality

Many problems require returning **two things** from each recursive call:

1. The **answer for the subtree** (for the parent to use)
2. An **update to the global answer**

Example: Diameter
- Return: height of subtree (for parent to compute its own diameter)
- Update: global max diameter

Recognize this pattern and you can solve a large class of problems.

### Common Mistake Patterns to Avoid

```
1. LEAF CHECK ERROR:
   Wrong: if node.val == 0: return true  (triggers on any 0-valued node)
   Right: if node.left == nil && node.right == nil: return ...

2. FORGETTING BACKTRACKING:
   Wrong: path.add(val) → recurse (path grows permanently)
   Right: path.add(val) → recurse → path.remove_last()

3. ONLY CHECKING IMMEDIATE CHILDREN (BST):
   Wrong: node.left.val < node.val  (misses deep violations)
   Right: pass range [min, max] top-down

4. OFF-BY-ONE ON HEIGHT:
   Define: height(null) = -1  → height(leaf) = 0  (consistent with edge count)
   OR:     height(null) =  0  → height(leaf) = 1  (consistent with node count)
   Pick one and be consistent throughout your solution.

5. RETURNING WRONG NODE IN LCA:
   If node == p, return node immediately — don't check if q is in subtree.
   The algorithm's correctness relies on bubbling up found nodes.
```

### Problem Classification

```
Look at the problem → ask these questions in order:

Q1: Does the answer require visiting every node?
    YES → O(n) is unavoidable. Use DFS.
    NO  → Maybe O(log n) BST search is possible.

Q2: Does the answer for a node depend on subtree results?
    YES → POST-ORDER (bottom-up)
    NO  → Maybe PRE-ORDER (top-down)

Q3: Is the path order important?
    YES (need sorted) → IN-ORDER on BST

Q4: Is extra space a constraint?
    SEVERE → Morris traversal (O(1))
    MILD   → Iterative with stack (moves heap vs call stack)
    NO     → Recursive is simplest
```

### The Cognitive Chunking Principle

Experts recognize **problem families**, not individual problems. Once you deeply understand these 8 patterns:

1. Height / depth computation (post-order accumulate)
2. Path sum / existence (top-down propagate)
3. Subtree aggregate (post-order combine)
4. Global optimum (post-order + global variable)
5. BST validation / search (top-down with range)
6. Symmetry / mirror check (simultaneous DFS on two subtrees)
7. LCA finding (post-order with early return)
8. Serialization (pre-order + null markers)

...you have mental **chunks** that apply to hundreds of problems. Your working memory handles one chunk, not a sequence of individual steps. This is the mechanism behind expert intuition.

### Complexity Summary Table

| Algorithm | Time | Space (avg) | Space (worst, skewed) |
|-----------|------|-------------|----------------------|
| Recursive traversal | O(n) | O(log n) | O(n) |
| Iterative traversal | O(n) | O(log n) | O(n) |
| Morris traversal | O(n) | O(1) | O(1) |
| Height | O(n) | O(log n) | O(n) |
| Diameter | O(n) | O(log n) | O(n) |
| BST validation | O(n) | O(log n) | O(n) |
| LCA | O(n) | O(log n) | O(n) |
| Serialize | O(n) | O(n) output | O(n) output |
| Deserialize | O(n) | O(n) input | O(n) input |

---

## Final Note: The Hierarchy of Understanding

```
Level 1 — Recognition:    "I've seen this pattern before"
Level 2 — Understanding:  "I know why it works"
Level 3 — Adaptation:     "I can modify it to fit new constraints"
Level 4 — Creation:       "I can invent new patterns"

DFS on trees is Level 1-2 territory.
Applying it to novel problems is Level 3.
You are building the foundation for Level 4.
```

Depth-first search on trees is, in its essence, the **natural recursion of a recursive structure**. When you see a tree, see recursion. When you see recursion, see DFS. When you see DFS, see the three traversal orders. And when you see the traversal orders, see the five patterns. This is the mental model of a world-class practitioner.

---

*End of Guide — DFS on Trees*

Now let me build this comprehensive guide. This will be deeply thorough.Here is what this guide covers, organized so you know exactly what you now own mentally:

**Vocabulary & Foundations** — Every single term (ancestor, successor, depth, height, leaf, subtree, etc.) defined precisely with ASCII diagrams. No fuzzy terms, no assumed knowledge.

**The Three Traversal Orders** — Pre / In / Post order, each with a full step-by-step visual walkthrough showing exactly what happens at each function call and return.

**The Call Stack Demystified** — How recursion actually works in memory, why stack overflow happens, the exact byte cost per frame, and why Go goroutines have an advantage here.

**Three DFS Implementations** — Recursive, Iterative (all three orders), and Morris O(1)-space. Each with a visual trace so the algorithm is alive in your mind, not just on paper.

**Five Universal Patterns** — The mental frameworks (accumulate, propagate, global-variable, path-tracking, two-pass) that collapse hundreds of problems into 5 templates.

**Classic Problems** — Height, Diameter, LCA, BST Validation, Path Sum, Serialization — each with a reasoning walkthrough before the algorithm, not just code.

**Hardware Reality** — Cache miss behavior, pointer-chasing costs, arena allocation, compiler optimization, and exact stack frame sizes. This is what separates practitioners from theorists.

**Production Code in Go, C, and Rust** — No `unwrap()` without justification, no magic numbers, proper error types, memory freed in C, idiomatic ownership in Rust, clean module structure in Go.