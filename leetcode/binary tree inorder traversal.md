## Before Writing Code — Build the Mental Model

### What is a Binary Tree?

```
A Binary Tree is a structure where each node has:
  - A value (Val)
  - At most ONE left child
  - At most ONE right child

          [4]          ← ROOT node (no parent)
         /   \
       [2]   [6]       ← INTERNAL nodes
       / \   / \
     [1] [3][5] [7]    ← LEAF nodes (no children)

TreeNode struct:
┌─────────────────────┐
│  Val   int          │  ← stores the number
│  Left  *TreeNode    │  ← pointer to left child (or nil)
│  Right *TreeNode    │  ← pointer to right child (or nil)
└─────────────────────┘
```

---

### What is "Traversal"?

> **Traversal** = visiting every node in the tree **exactly once**, in a specific order.

There are 3 classic depth-first orders:

```
Tree:        [4]
            /   \
          [2]   [6]
          / \
        [1] [3]

─────────────────────────────────────────────────────
Traversal     Order           Result
─────────────────────────────────────────────────────
INORDER      Left→Root→Right  [1, 2, 3, 4, 6]  ← SORTED for BST!
PREORDER     Root→Left→Right  [4, 2, 1, 3, 6]
POSTORDER    Left→Right→Root  [1, 3, 2, 6, 4]
─────────────────────────────────────────────────────
```

### Why Inorder? Critical Insight:
> For a **Binary Search Tree (BST)**, Inorder traversal always produces a **sorted ascending sequence**. This is the fundamental property that makes BST powerful.

---

## Inorder Rule: Left → Root → Right

```
For EVERY node you visit:
  1. First, go all the way LEFT (recurse)
  2. Then, process THIS node (append Val)
  3. Then, go RIGHT (recurse)
```

### Tracing Through an Example

```
Tree:
        [1]
           \
           [2]
          /
        [3]

Inorder should give: [1, 3, 2]

TRACE:
Visit(1)
  → go LEFT of 1 → nil  (nothing)
  → process 1    → result = [1]
  → go RIGHT of 1 → Visit(2)
       → go LEFT of 2 → Visit(3)
            → go LEFT of 3  → nil
            → process 3     → result = [1, 3]
            → go RIGHT of 3 → nil
       → process 2     → result = [1, 3, 2]
       → go RIGHT of 2 → nil

Final: [1, 3, 2] ✓
```

---

## Approach 1 — Recursive (Most Natural)

```
THINK LIKE AN EXPERT:
─────────────────────────────────────────────────────────
The recursive definition of inorder IS the algorithm.
"Inorder of a tree = Inorder(left) + [root] + Inorder(right)"
Base case: nil node → return nothing.
─────────────────────────────────────────────────────────
```

```go
func inorderTraversal(root *TreeNode) []int {
    result := []int{}
    
    var inorder func(node *TreeNode)
    inorder = func(node *TreeNode) {
        if node == nil {
            return             // base case: empty subtree, do nothing
        }
        inorder(node.Left)     // 1. recurse LEFT
        result = append(result, node.Val)  // 2. process ROOT
        inorder(node.Right)    // 3. recurse RIGHT
    }
    
    inorder(root)
    return result
}
```

### Call Stack Visualization

```
Tree:      [4]
          /   \
        [2]   [5]
        / \
      [1] [3]

Call Stack grows DOWNWARD (most recent call on top):

inorder(4)
  inorder(2)
    inorder(1)
      inorder(nil) ← LEFT of 1  → return
      append(1)    → result=[1]
      inorder(nil) ← RIGHT of 1 → return
    ← returns
    append(2)      → result=[1,2]
    inorder(3)
      inorder(nil) ← LEFT of 3  → return
      append(3)    → result=[1,2,3]
      inorder(nil) ← RIGHT of 3 → return
    ← returns
  ← returns
  append(4)        → result=[1,2,3,4]
  inorder(5)
    inorder(nil)   → return
    append(5)      → result=[1,2,3,4,5]
    inorder(nil)   → return
  ← returns
← returns

Final: [1, 2, 3, 4, 5] ✓
```

**Complexity:**
```
Time:  O(n)  — every node visited exactly once
Space: O(h)  — call stack depth = height of tree
               Best (balanced): O(log n)
               Worst (skewed):  O(n)
```

---

## Approach 2 — Iterative with Explicit Stack

```
THINK LIKE AN EXPERT:
─────────────────────────────────────────────────────────
Recursion uses the PROGRAM'S call stack implicitly.
We can simulate this with an EXPLICIT stack data structure.
Why? Avoids stack overflow for very deep trees, and
interviewers love seeing you can think iteratively.

KEY INSIGHT: "Go as far LEFT as possible, pushing nodes.
             When stuck (nil), pop and process, then go RIGHT."
─────────────────────────────────────────────────────────
```

### What is a Stack?
```
A Stack is LIFO — Last In, First Out.
Like a stack of plates: you add/remove from the TOP only.

Push(A) → [A]
Push(B) → [A, B]
Push(C) → [A, B, C]
Pop()   → returns C, stack=[A, B]
Pop()   → returns B, stack=[A]
```

### Iterative Algorithm Flow

```
          ┌──────────────────────────────────┐
          │  current = root, stack = []      │
          └────────────────┬─────────────────┘
                           │
                           ▼
          ┌──────────────────────────────────┐
          │ current != nil OR stack not empty?│
          └────────────┬─────────────────────┘
                       │
              ┌────────┴────────┐
             YES               NO
              │                 │
              ▼              RETURN result
    ┌──────────────────┐
    │ current != nil ? │
    └────────┬─────────┘
             │
    ┌────────┴────────┐
   YES               NO
    │                 │
    ▼                 ▼
push(current)    pop from stack → node
current =        append(node.Val) to result
current.Left     current = node.Right
    │                 │
    └────────┬────────┘
             ▼
        (loop again)
```

```go
func inorderTraversal(root *TreeNode) []int {
    result := []int{}
    stack := []*TreeNode{}   // our explicit stack
    current := root

    for current != nil || len(stack) > 0 {
        
        // Phase 1: go as far LEFT as possible, pushing each node
        for current != nil {
            stack = append(stack, current)   // push
            current = current.Left
        }
        
        // Phase 2: we hit nil — backtrack via pop
        // stack[-1] is the last unprocessed node
        current = stack[len(stack)-1]        // peek top
        stack = stack[:len(stack)-1]         // pop
        
        result = append(result, current.Val) // process node
        
        // Phase 3: now explore the RIGHT subtree
        current = current.Right
    }
    
    return result
}
```

### Iterative Trace

```
Tree:      [4]
          /   \
        [2]   [5]
        / \
      [1] [3]

──────────────────────────────────────────────────────
Step  current  stack            action
──────────────────────────────────────────────────────
init    4       []
 1      4       []     → push 4,  go left
 2      2       [4]    → push 2,  go left
 3      1       [4,2]  → push 1,  go left
 4     nil      [4,2,1]→ nil: POP 1, append 1, go right
 5     nil      [4,2]  → nil: POP 2, append 2, go right
 6      3       [4]    → push 3, go left
 7     nil      [4,3]  → nil: POP 3, append 3, go right
 8     nil      [4]    → nil: POP 4, append 4, go right
 9      5       []     → push 5, go left
10     nil      [5]    → nil: POP 5, append 5, go right
11     nil      []     → nil, stack empty → DONE
──────────────────────────────────────────────────────
result: [1, 2, 3, 4, 5] ✓
```

**Complexity:**
```
Time:  O(n)  — every node pushed and popped exactly once
Space: O(h)  — stack holds at most h nodes (h = tree height)
```

---

## Approach 3 — Morris Traversal (O(1) Space — Expert Level)

```
THINK LIKE AN EXPERT:
─────────────────────────────────────────────────────────
Can we traverse without ANY extra space? No stack, no recursion?
Morris traversal uses the tree's OWN nil pointers as
temporary "threads" back to the parent. This is called
a THREADED BINARY TREE technique.
─────────────────────────────────────────────────────────
```

### Core Concept: Predecessor
```
INORDER PREDECESSOR of a node X:
= the node that comes JUST BEFORE X in inorder sequence
= the RIGHTMOST node of X's LEFT subtree

Example:
        [4]
       /   \
     [2]   [5]
     / \
   [1] [3]

Inorder: [1, 2, 3, 4, 5]
Predecessor of 4 = 3  (rightmost of left subtree [2,1,3])
Predecessor of 2 = 1  (rightmost of left subtree [1])
```

### Morris Algorithm Idea
```
For each node with a LEFT child:
  1. Find its inorder predecessor (rightmost of left subtree)
  2. If predecessor.Right == nil:
       → Set predecessor.Right = current  (create thread)
       → Move current to current.Left
  3. If predecessor.Right == current:  (thread already exists)
       → Remove the thread (restore tree)
       → PROCESS current (append Val)
       → Move current to current.Right
```

```go
func inorderTraversal(root *TreeNode) []int {
    result := []int{}
    current := root

    for current != nil {
        if current.Left == nil {
            // No left child: process and go right
            result = append(result, current.Val)
            current = current.Right
        } else {
            // Find inorder predecessor
            predecessor := current.Left
            for predecessor.Right != nil && predecessor.Right != current {
                predecessor = predecessor.Right
            }

            if predecessor.Right == nil {
                // First visit: create thread, go left
                predecessor.Right = current   // temporary thread
                current = current.Left
            } else {
                // Second visit: remove thread, process, go right
                predecessor.Right = nil       // restore tree
                result = append(result, current.Val)
                current = current.Right
            }
        }
    }

    return result
}
```

**Complexity:**
```
Time:  O(n)  — each node visited at most twice
Space: O(1)  — no stack, no recursion. Pure pointer manipulation.
```

---

## All Three Approaches — Side by Side

```
─────────────────────────────────────────────────────────────
Approach      Time   Space   Simplicity   Interview Signal
─────────────────────────────────────────────────────────────
Recursive     O(n)   O(h)    ★★★★★       Good starting point
Iterative     O(n)   O(h)    ★★★★        Shows stack mastery
Morris        O(n)   O(1)    ★★           Top 1% thinking
─────────────────────────────────────────────────────────────
```

---

## What to Submit on LeetCode

For LeetCode problem **94. Binary Tree Inorder Traversal**, submit the iterative or recursive version. Start clean:

```go
func inorderTraversal(root *TreeNode) []int {
    result := []int{}
    stack := []*TreeNode{}
    current := root

    for current != nil || len(stack) > 0 {
        for current != nil {
            stack = append(stack, current)
            current = current.Left
        }
        current = stack[len(stack)-1]
        stack = stack[:len(stack)-1]
        result = append(result, current.Val)
        current = current.Right
    }

    return result
}
```

---

## Cognitive Principle: Chunking

> Your brain cannot hold all recursive calls simultaneously. **Chunking** means internalizing `Left → Root → Right` as a single unit, then trusting it recursively without mentally simulating every frame. Expert programmers don't trace — they *trust the invariant*. Practice stating: *"This function correctly processes a subtree — I define it to be true, now I use it."* That is the mindset of inductive reasoning, and it is how all tree problems are solved at high speed.

## Test Cases — LC 99: Recover Binary Search Tree

Before diving in, internalize the **core invariant**: in a valid BST, its **inorder traversal produces a strictly increasing sequence**. Every test case below is a violation of that invariant in some specific shape.

---

### 🧱 Basic / Edge Cases

**Test 1 — Swap adjacent nodes in inorder sequence**
```
Input:  [1, 3, null, null, 2]
Output: [3, 1, null, null, 2]
```
*Why it matters:* The swapped nodes are **adjacent** in inorder. This is the harder sub-case — only **one inversion** appears in the sequence instead of two.

---

**Test 2 — Swap non-adjacent nodes**
```
Input:  [3, 1, 4, null, null, 2]
Output: [2, 1, 4, null, null, 3]
```
*Why it matters:* Non-adjacent swap produces **two separate inversions** in the inorder sequence. Your algorithm must handle both sub-cases.

---

**Test 3 — Single node tree**
```
Input:  [1]
Output: [1]
```
*Why it matters:* No swap is possible. Tests null-safety and base case handling.

---

**Test 4 — Two node tree (left child)**
```
Input:  [2, 1]
Output: [2, 1]  ← already valid
```

**Test 4b — Two node tree, swapped**
```
Input:  [1, 2]  ← left child greater than root
Output: [2, 1]
```

---

### 🔩 Structural Variations

**Test 5 — Swap root with a deep right descendant**
```
Input:  [5, 3, 7, 2, 4, 6, 1]
          (root=5 and rightmost=1 are swapped)
Correct tree should be: [1, 3, 7, 2, 4, 6, 5]
```
*Why it matters:* Tests whether you correctly identify the **first** and **last** violation pointers.

---

**Test 6 — Swap two leaf nodes**
```
Input:  [6, 3, 8, 1, 4, 7, 9]  
         where 4 and 7 are swapped → [6, 3, 8, 1, 7, 4, 9]
Output: [6, 3, 8, 1, 4, 7, 9]
```

---

**Test 7 — Perfectly balanced BST, root swapped with a leaf**
```
Input:  [4, 2, 6, 1, 3, 5, 7]  (valid BST)
         Swap root (4) with node (1) → [1, 2, 6, 4, 3, 5, 7]
Output: [4, 2, 6, 1, 3, 5, 7]
```

---

**Test 8 — Left-skewed tree (all left children)**
```
Input:  [4, 3, null, 1, null, null, null]
         (3 and 1 swapped → should be [4, 1, null, 3, ...])
```
*Why it matters:* Tests purely left-spine traversal, no right subtree interference.

---

**Test 9 — Right-skewed tree (all right children)**
```
Input:  [1, null, 5, null, null, null, 3]
         (5 and 3 swapped)
Output: [1, null, 3, null, null, null, 5]
```

---

### 🧠 What to Look For in Your Solution

| Scenario | Inorder inversions | Difficulty |
|---|---|---|
| Adjacent swap | 1 pair | Higher — easy to miss `second` pointer |
| Non-adjacent swap | 2 pairs | Standard |
| Root ↔ deepest node | 2 pairs, far apart | Tests pointer tracking |
| Skewed trees | 1 pair, linear | Tests null handling |

---

**Mental Model to apply before coding:**

> *"A BST is just a sorted array wearing a tree costume."*
> Flatten it mentally via inorder, find the anomaly in the sorted sequence, then recover.

Good luck — the adjacent-swap edge case is where most solutions silently break. 🎯

## ASCII Diagrams — All Test Cases

---

### Test 1 — Adjacent swap (left child > root)

```
INPUT (invalid BST)        OUTPUT (valid BST)

    1                          3
   /                          /
  3          ──────►         1
   \                          \
    2                          2

Inorder: [3, 1, 2]            Inorder: [1, 2, 3] ✓
          ↑  ↑
       one inversion (adjacent swap)
```

---

### Test 2 — Non-adjacent swap

```
INPUT (invalid BST)        OUTPUT (valid BST)

    3                          2
   / \                        / \
  1   4      ──────►         1   4
     /                          /
    2                          3

Inorder: [1, 3, 2, 4]         Inorder: [1, 2, 3, 4] ✓
              ↑  ↑
          two inversions (3>2 and 2<4... track first and last)
```

---

### Test 3 — Single node

```
INPUT / OUTPUT

    1

Inorder: [1] ✓    No swap needed.
```

---

### Test 4 — Two node, already valid

```
INPUT / OUTPUT

  2
 /
1

Inorder: [1, 2] ✓    No swap needed.
```

---

### Test 4b — Two node, swapped

```
INPUT (invalid)            OUTPUT (valid)

  1                            2
 /           ──────►          /
2                            1

Inorder: [2, 1]               Inorder: [1, 2] ✓
          ↑  ↑
       one inversion
```

---

### Test 5 — Root swapped with leftmost leaf

```
INPUT (invalid BST)            OUTPUT (valid BST)

          1                              4
        /   \                          /   \
       2     6        ──────►         2     6
      / \   / \                      / \   / \
     4   3 5   7                    1   3 5   7

Inorder: [4, 2, 3, 1, 5, 6, 7]     Inorder: [1, 2, 3, 4, 5, 6, 7] ✓
          ↑        ↑
     first          second
    violation      violation
    (4 > 2)        (3 > 1)
```

---

### Test 6 — Two leaf nodes swapped

```
INPUT (invalid BST)            OUTPUT (valid BST)

          6                              6
        /   \                          /   \
       3     8        ──────►         3     8
      / \   / \                      / \   / \
     1   7 4   9                    1   4 7   9

Inorder: [1, 3, 7, 6, 4, 8, 9]     Inorder: [1, 3, 4, 6, 7, 8, 9] ✓
                  ↑     ↑
             first      second
            violation  violation
            (7 > 6)    (4 < 8... but 6 > 4)
```

---

### Test 7 — Balanced BST, root ↔ leaf

```
INPUT (invalid BST)            OUTPUT (valid BST)

          1                              4
        /   \                          /   \
       2     6        ──────►         2     6
      / \   / \                      / \   / \
     4   3 5   7                    1   3 5   7

Inorder: [4, 2, 3, 1, 5, 6, 7]     Inorder: [1, 2, 3, 4, 5, 6, 7] ✓
          ↑        ↑
       first      second
      violation  violation
```
> ⚠️ Same shape as Test 5 — intentional. Root-to-leaf swap always yields **two well-separated inversions**. Verify your `first` and `second` pointers are tracking the right nodes.

---

### Test 8 — Left-skewed tree

```
INPUT (invalid BST)        OUTPUT (valid BST)

    4                          4
   /                          /
  1          ──────►         3
 /                          /
3                          1

Inorder: [3, 1, 4]            Inorder: [1, 3, 4] ✓
          ↑  ↑
       one inversion (adjacent)
```

---

### Test 9 — Right-skewed tree

```
INPUT (invalid BST)        OUTPUT (valid BST)

1                          1
 \                          \
  5          ──────►         3
   \                          \
    3                          5

Inorder: [1, 5, 3]            Inorder: [1, 3, 5] ✓
             ↑  ↑
          one inversion (adjacent)
```

---

### 🧠 Inorder Inversion Summary

```
Test | Swapped Nodes        | # Inversions | Swap Type
-----|----------------------|--------------|-------------
  1  | root ↔ left child    |      1       | Adjacent
  2  | root ↔ deep left     |      2       | Non-adjacent
  3  | none                 |      0       | No-op
  4  | none                 |      0       | No-op
  4b | root ↔ left child    |      1       | Adjacent
  5  | root ↔ leftmost leaf |      2       | Non-adjacent
  6  | two internal leaves  |      2       | Non-adjacent
  7  | root ↔ leaf          |      2       | Non-adjacent
  8  | left-skew adjacent   |      1       | Adjacent
  9  | right-skew adjacent  |      1       | Adjacent
```

The **adjacent swap → single inversion** edge case is the crux of this problem. Make sure your algorithm finds `second` correctly even when there's only **one** inversion in the inorder sequence.

## Step-by-Step Inorder Traversal — Test 6

### The Tree (keep this as reference)

```
              6
            /   \
           3     8
          / \   / \
         1   7 4   9

Inorder visits: Left → Root → Right
```

---

### Pointers We Track

```
prev   = the last visited node
first  = first violating node  (initially null)
second = second violating node (initially null)

Violation condition: prev.val > current.val
```

---

### Step 1 — Visit Node `1`

```
              6
            /   \
           3     8
          / \   / \
        [1]  7 4   9          ← currently visiting

prev   = null
current = 1

null > 1?  NO → no violation

prev   = [1]
first  = null
second = null
```

---

### Step 2 — Visit Node `3`

```
              6
            /   \
          [3]    8
          / \   / \
         1   7 4   9          ← currently visiting

prev   = 1
current = 3

1 > 3?  NO → no violation

prev   = [3]
first  = null
second = null
```

---

### Step 3 — Visit Node `7`

```
              6
            /   \
           3     8
          / \   / \
         1  [7] 4   9         ← currently visiting

prev   = 3
current = 7

3 > 7?  NO → no violation

prev   = [7]
first  = null
second = null
```

---

### Step 4 — Visit Node `6` 🚨 FIRST VIOLATION

```
             [6]
            /   \
           3     8
          / \   / \
         1   7 4   9          ← currently visiting

prev   = 7
current = 6

7 > 6?  YES → 🚨 FIRST VIOLATION FOUND

        prev(7) > current(6)
        ┌─────────────────────────────────┐
        │  first  = prev    = node(7)     │
        │  second = current = node(6)     │  ← tentative, may update
        └─────────────────────────────────┘

prev   = [6]
first  = [7]
second = [6]   ← tentative
```

---

### Step 5 — Visit Node `4` 🚨 SECOND VIOLATION

```
              6
            /   \
           3     8
          / \   / \
         1   7 [4]  9         ← currently visiting

prev   = 6
current = 4

6 > 4?  YES → 🚨 SECOND VIOLATION FOUND

        prev(6) > current(4)
        ┌─────────────────────────────────┐
        │  first  stays  = node(7)        │  ← never changes
        │  second UPDATE = node(4)        │  ← overwrite tentative
        └─────────────────────────────────┘

prev   = [4]
first  = [7]
second = [4]   ← finalized
```

---

### Step 6 — Visit Node `8`

```
              6
            /   \
           3    [8]
          / \   / \
         1   7 4   9          ← currently visiting

prev   = 4
current = 8

4 > 8?  NO → no violation

prev   = [8]
first  = [7]
second = [4]
```

---

### Step 7 — Visit Node `9`

```
              6
            /   \
           3     8
          / \   / \
         1   7 4  [9]         ← currently visiting

prev   = 8
current = 9

8 > 9?  NO → no violation

prev   = [9]
first  = [7]   ← CONFIRMED
second = [4]   ← CONFIRMED
```

---

### Inorder Sequence — Visual Anomaly

```
Position:  1    2    3    4    5    6    7
Sequence: [1]  [3]  [7]  [6]  [4]  [8]  [9]
                      ↑    ↑    ↑
                      │    │    └── second violation: 6 > 4
                      │    └─────── 
                      └──────────── first violation: 7 > 6
                      
first  = node(7)   ← the bigger  value sitting too early
second = node(4)   ← the smaller value sitting too late
```

---

### The Swap

```
BEFORE swap:                   AFTER swap:

      6                               6
    /   \                           /   \
   3     8          ──────►        3     8
  / \   / \                       / \   / \
 1  [7][4]  9                    1  [4][7]  9

swap(first.val, second.val)
swap(7, 4)

Inorder BEFORE: [1, 3, 7, 6, 4, 8, 9]  ✗
Inorder AFTER:  [1, 3, 4, 6, 7, 8, 9]  ✓
```

---

### The Core Logic in One Mental Model

```
Two violations  →  non-adjacent swap
                   first  = prev    at violation #1
                   second = current at violation #2   (overwrite #1's guess)

One violation   →  adjacent swap
                   first  = prev    at violation #1
                   second = current at violation #1   (no overwrite happens)

In both cases:  swap(first, second)  →  BST restored ✓
```

> The elegance here: you don't need to know **where** in the tree the nodes live.
> You only need to track **two pointers** during a single inorder pass. The tree's structure does the rest.