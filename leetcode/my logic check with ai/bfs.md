Exactly! With BFS you just count **levels** — increment the counter each time you start a new level.

```python
from collections import deque

def maxDepth(root):
    if not root:
        return 0
    
    queue = deque([root])
    depth = 0

    while queue:
        depth += 1  # each iteration = one level
        for _ in range(len(queue)):  # process all nodes at current level
            node = queue.popleft()
            if node.left:  queue.append(node.left)
            if node.right: queue.append(node.right)

    return depth
```

The key insight is `range(len(queue))` — snapshot the queue size *before* the inner loop so you process exactly the nodes at the current level, then `depth += 1` ticks once per level, not once per node.

For your tree example: processes `[A]` → `[B,C]` → `[D,E]` = depth 3.

DFS recursive is even shorter if you want it:

```python
def maxDepth(root):
    if not root: return 0
    return 1 + max(maxDepth(root.left), maxDepth(root.right))
```

Both are O(n) time, O(n) space. BFS space is O(w) where w = max width, DFS is O(h) where h = height — so for very wide trees DFS wins on space.

# 🔍 Diagnosing Your Bug: BFS Maximum Depth

## The Core Problem — Mental Model First

Before touching the code, let's understand what **BFS (Breadth-First Search)** means conceptually, because the bug is a misunderstanding of BFS mechanics.

---

## 📚 Concept: What is BFS?

**BFS = Level-by-Level traversal.** Imagine dropping a stone in water — ripples spread outward in rings. Each ring = one level of the tree.

```
Tree: [3, 9, 20, null, null, 15, 7]

Level 0:        3          ← depth = 1
               / \
Level 1:      9   20       ← depth = 2
                 /  \
Level 2:        15   7     ← depth = 3
```

**The answer should be 3** (3 levels). But your code outputs **5** (total node count). That's the bug.

---

## 🐛 The Bug — Exact Location

```go
for len(queue) > 0 {
    treenode := queue[0]
    queue = queue[1:]

    depth++  // ❌ BUG HERE — incrementing per NODE, not per LEVEL

    if treenode.Left != nil {
        queue = append(queue, treenode.Left)
    }
    if treenode.Right != nil {
        queue = append(queue, treenode.Right)
    }
}
```

### What your code actually does:

```
Iteration 1: process node 3  → depth = 1, enqueue [9, 20]
Iteration 2: process node 9  → depth = 2, enqueue []
Iteration 3: process node 20 → depth = 3, enqueue [15, 7]
Iteration 4: process node 15 → depth = 4, enqueue []
Iteration 5: process node 7  → depth = 5, enqueue []

Final depth = 5  ← WRONG (counted nodes, not levels!)
```

---

## 🧠 The Mental Model You Were Missing

**Key Insight:** To count LEVELS in BFS, you must know where one level ends and the next begins.

The trick: **Before processing each level, snapshot how many nodes are currently in the queue.** That count = all nodes at the current level.

```
Queue state over time:

Start:         [3]           → levelSize = 1  → process 1 node → depth = 1
After level 0: [9, 20]       → levelSize = 2  → process 2 nodes → depth = 2
After level 1: [15, 7]       → levelSize = 2  → process 2 nodes → depth = 3
After level 2: []            → STOP
```

---

## ✅ The Fix — Level-Aware BFS

```go
func maxDepth(root *TreeNode) int {
    if root == nil {
        return 0
    }

    depth := 0
    queue := []*TreeNode{root}

    for len(queue) > 0 {
        levelSize := len(queue) // ✅ snapshot how many nodes are at THIS level

        depth++ // ✅ increment ONCE per level, not per node

        for i := 0; i < levelSize; i++ { // ✅ process ALL nodes at this level
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
```

---

## 📊 Trace of Fixed Code

```
LEVEL 0:
  levelSize = 1  (queue: [3])
  depth → 1
  Process node 3 → enqueue 9, 20
  queue after: [9, 20]

LEVEL 1:
  levelSize = 2  (queue: [9, 20])
  depth → 2
  Process node 9 → no children
  Process node 20 → enqueue 15, 7
  queue after: [15, 7]

LEVEL 2:
  levelSize = 2  (queue: [15, 7])
  depth → 3
  Process node 15 → no children
  Process node 7  → no children
  queue after: []

Loop ends → return 3 ✅
```

---

## 🔄 Algorithm Flow (Fixed)

```
maxDepth(root)
     │
     ▼
root == nil? ──YES──► return 0
     │NO
     ▼
depth = 0
queue = [root]
     │
     ▼
┌─────────────────────────────────────┐
│  OUTER LOOP: while queue not empty  │
│                                     │
│   levelSize = len(queue)  ◄── KEY  │
│   depth++                           │
│                                     │
│   ┌──────────────────────────────┐  │
│   │ INNER LOOP: i < levelSize    │  │
│   │                              │  │
│   │  node = dequeue()            │  │
│   │  if node.Left  → enqueue it  │  │
│   │  if node.Right → enqueue it  │  │
│   └──────────────────────────────┘  │
└─────────────────────────────────────┘
     │
     ▼
return depth
```

---

## ⚡ Alternative: Recursive DFS (Elegant & Simpler)

The BFS approach is valid, but for max depth, **DFS recursion** is the most elegant:

```go
// Concept: depth of tree = 1 + max(depth of left, depth of right)
func maxDepth(root *TreeNode) int {
    if root == nil {
        return 0
    }
    leftDepth  := maxDepth(root.Left)
    rightDepth := maxDepth(root.Right)
    if leftDepth > rightDepth {
        return leftDepth + 1
    }
    return rightDepth + 1
}
```

### Why this works — The Recurrence:

```
maxDepth(3)
├── maxDepth(9)
│   ├── maxDepth(nil) = 0
│   └── maxDepth(nil) = 0
│   → return max(0,0)+1 = 1
│
└── maxDepth(20)
    ├── maxDepth(15)
    │   → return 1
    └── maxDepth(7)
        → return 1
    → return max(1,1)+1 = 2

→ return max(1,2)+1 = 3 ✅
```

---

## 🐛 Bonus Bug in Your `buildTree`

There's a **variable shadowing bug** here:

```go
current := queue[0]
queue := queue[1:]  // ❌ := creates a NEW local variable, not updating outer queue!
```

Should be:
```go
current := queue[0]
queue = queue[1:]   // ✅ = updates the outer queue
```

This is a classic Go gotcha — `:=` inside a block creates a new scope-local variable.

---

## 📊 Complexity Analysis

| Approach | Time | Space | Notes |
|---|---|---|---|
| Your BFS (buggy) | O(n) | O(n) | Counts nodes, not levels |
| Fixed BFS | O(n) | O(n) | O(w) space where w = max width |
| DFS Recursive | O(n) | O(h) | h = height, best for balanced trees |

---

## 🧘 Mental Model to Remember

> **"BFS depth counting = outer loop counts levels, inner loop counts nodes at that level."**

The pattern `levelSize := len(queue)` before the inner loop is a **template** you'll use in many BFS problems: level-order traversal, zigzag traversal, right-side view, etc. Internalize it.

This is an example of **chunking** — once you recognize "I need level-aware BFS," you reach for this exact pattern automatically. That's expert pattern recognition.