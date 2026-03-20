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