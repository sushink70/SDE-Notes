# 🧭 The Complete Guide to Tracking Backtracking

---

## 📌 First: What IS Backtracking? (The Mental Model)

Before tracking, you must understand **what backtracking physically does**.

> **Backtracking = Explore a choice → Go deep → If it fails (or finishes) → UNDO the choice → Try the next choice**

Think of it like navigating a maze:

```
You walk forward → hit a dead end → STEP BACK to last junction → try another path
```

The key insight: **Backtracking is recursion + an explicit UNDO step.**

```
┌─────────────────────────────────────────────────────┐
│              THE BACKTRACKING LOOP                  │
│                                                     │
│   for each choice in available_choices:             │
│       1. MAKE the choice    (add to state)          │
│       2. RECURSE            (go deeper)             │
│       3. UNMAKE the choice  (remove from state)     │
│                                                     │
│   ← This "UNMAKE" step is the BACKTRACK             │
└─────────────────────────────────────────────────────┘
```

---

## 🌳 The Universal Tracking Tool: The Recursion Tree

Every backtracking problem can be **drawn as a tree**. This is your simulation table equivalent.

```
Each NODE  = a state (what you've built so far)
Each EDGE  = a choice you made
Each LEAF  = a complete result OR a dead end
```

---

## 📐 The 4-Column Tracking Table (Your New Simulation Table)

For every backtracking call, track these 4 things:

```
┌──────────┬──────────────┬───────────────┬──────────────────────────────┐
│  DEPTH   │  CURRENT     │  CHOICES      │  ACTION                      │
│ (level)  │  STATE       │  REMAINING    │  (CHOOSE / RECURSE / UNDO)   │
├──────────┼──────────────┼───────────────┼──────────────────────────────┤
│   0      │  []          │  [1,2,3]      │  Choose 1 → recurse          │
│   1      │  [1]         │  [2,3]        │  Choose 2 → recurse          │
│   2      │  [1,2]       │  [3]          │  Choose 3 → recurse          │
│   3      │  [1,2,3]     │  []           │  BASE CASE → record [1,2,3]  │
│   2      │  [1,2]       │  []           │  UNDO 3 → back to depth 2    │
│   1      │  [1]         │  [3]          │  UNDO 2 → Choose 3 → recurse │
│   2      │  [1,3]       │  []           │  BASE CASE → record [1,3]    │
│   ...    │  ...         │  ...          │  ...                         │
└──────────┴──────────────┴───────────────┴──────────────────────────────┘
```

---

## 🔬 Deep Example: Subsets of `[1, 2, 3]`

**Problem:** Find all subsets (power set) of `[1, 2, 3]`.

**Expected output:** `[], [1], [1,2], [1,2,3], [1,3], [2], [2,3], [3]`

### Step 1 — The Recursion Tree (Draw BEFORE coding)

```
                        START: []
                       /    |    \
               pick 1       pick 2    pick 3
              /              |           \
           [1]              [2]          [3]
          /   \            /   \           \
      pick 2  pick 3   pick 3  (none)    (none)
       /         \       |
    [1,2]       [1,3]  [2,3]
      |
  pick 3
    |
 [1,2,3]
```

> **Key insight:** At each node, you decide: include the next element or skip to next. The `start` index prevents re-using previous elements.

---

### Step 2 — The Full Tracking Table

```
┌───────┬──────────┬──────────────┬────────┬────────────────────────────────────┐
│ CALL# │  DEPTH   │  STATE(path) │  start │  ACTION                            │
├───────┼──────────┼──────────────┼────────┼────────────────────────────────────┤
│  1    │    0     │  []          │   0    │  Record [] → try i=0 (pick 1)      │
│  2    │    1     │  [1]         │   1    │  Record [1] → try i=1 (pick 2)     │
│  3    │    2     │  [1,2]       │   2    │  Record [1,2] → try i=2 (pick 3)   │
│  4    │    3     │  [1,2,3]     │   3    │  Record [1,2,3] → no more choices  │
│       │          │              │        │  ← BACKTRACK: undo 3               │
│  5    │    2     │  [1,2]       │   3    │  No more choices at i=3            │
│       │          │              │        │  ← BACKTRACK: undo 2               │
│  6    │    1     │  [1]         │   2    │  try i=2 (pick 3)                  │
│  7    │    2     │  [1,3]       │   3    │  Record [1,3] → no more choices    │
│       │          │              │        │  ← BACKTRACK: undo 3               │
│  8    │    1     │  [1]         │   3    │  No more choices                   │
│       │          │              │        │  ← BACKTRACK: undo 1               │
│  9    │    0     │  []          │   1    │  try i=1 (pick 2)                  │
│  10   │    1     │  [2]         │   2    │  Record [2] → try i=2 (pick 3)     │
│  11   │    2     │  [2,3]       │   3    │  Record [2,3] → no more choices    │
│       │          │              │        │  ← BACKTRACK: undo 3               │
│  12   │    1     │  [2]         │   3    │  No more choices                   │
│       │          │              │        │  ← BACKTRACK: undo 2               │
│  13   │    0     │  []          │   2    │  try i=2 (pick 3)                  │
│  14   │    1     │  [3]         │   3    │  Record [3] → no more choices      │
│       │          │              │        │  ← BACKTRACK: undo 3               │
│  15   │    0     │  []          │   3    │  No more choices → DONE            │
└───────┴──────────┴──────────────┴────────┴────────────────────────────────────┘
```

---

### Step 3 — The Visual Stack Trace (Call Stack)

This shows you what's alive in memory at each point:

```
CALL STACK at deepest point (call #4):

┌─────────────────────────┐  ← TOP (currently executing)
│  bt(start=3, path=[1,2,3]) │
├─────────────────────────┤
│  bt(start=2, path=[1,2])   │
├─────────────────────────┤
│  bt(start=1, path=[1])     │
├─────────────────────────┤
│  bt(start=0, path=[])      │
└─────────────────────────┘  ← BOTTOM (original call)

After recording [1,2,3]:
→ bt(start=3) RETURNS
→ UNDO: path becomes [1,2]  (pop 3)
→ bt(start=2) checks next i → none → RETURNS
→ UNDO: path becomes [1]    (pop 2)
→ bt(start=1) tries i=2 (pick 3)...
```

---

### Step 4 — The Code (Rust) with Inline Annotations

```rust
fn backtrack(
    nums: &[i32],
    start: usize,        // which index to start picking from
    path: &mut Vec<i32>, // current subset being built
    result: &mut Vec<Vec<i32>>,
) {
    // ✅ RECORD current state (every node is a valid subset)
    result.push(path.clone());

    // 🔁 TRY each choice from 'start' to end
    for i in start..nums.len() {
        // 1. MAKE choice
        path.push(nums[i]);          // ← ADD to state

        // 2. RECURSE (go deeper)
        backtrack(nums, i + 1, path, result);

        // 3. UNMAKE choice  ← THIS IS THE BACKTRACK
        path.pop();                  // ← REMOVE from state (undo)
    }
}

fn subsets(nums: Vec<i32>) -> Vec<Vec<i32>> {
    let mut result = Vec::new();
    let mut path = Vec::new();
    backtrack(&nums, 0, &mut path, &mut result);
    result
}
```

---

## 🧠 The Universal Backtracking Template

Every backtracking problem fits this skeleton:

```
┌────────────────────────────────────────────────────────────┐
│  fn backtrack(state, choices, ...):                        │
│                                                            │
│      if BASE_CASE:          ← when to stop / record       │
│          save/return result                                │
│          return                                            │
│                                                            │
│      for each choice in choices:                           │
│          if NOT_VALID(choice): continue  ← pruning        │
│                                                            │
│          MAKE(choice)        ← modify state               │
│          backtrack(new_state, remaining_choices)           │
│          UNMAKE(choice)      ← restore state (UNDO)        │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 🌿 What Changes Between Problems? (Pattern Map)

```
┌─────────────────────┬───────────────────┬──────────────────┬───────────────┐
│  PROBLEM TYPE       │  STATE            │  CHOICE          │  BASE CASE    │
├─────────────────────┼───────────────────┼──────────────────┼───────────────┤
│  Subsets            │  current subset   │  include/skip    │  start==len   │
│  Permutations       │  current order    │  unused elements │  len==target  │
│  Combinations       │  current combo    │  next elements   │  k chosen     │
│  N-Queens           │  board positions  │  valid columns   │  row==N       │
│  Word Search        │  current path     │  adjacent cells  │  word matched │
│  Sudoku             │  filled cells     │  digits 1-9      │  board full   │
└─────────────────────┴───────────────────┴──────────────────┴───────────────┘
```

---

## ✂️ Pruning — The Backtracking Superpower

**Pruning** = cutting off branches you KNOW will fail, before exploring them.

```
WITHOUT PRUNING:          WITH PRUNING:
     ROOT                      ROOT
    / | \                      / \
   A  B  C                    A   C     ← B pruned early
  /|  |  |\                  / \   \
 D E  F  G H                D   E   G
           |                        ← H pruned
           I (fail)

Explores 9 nodes           Explores 5 nodes
```

In code, pruning = the `if NOT_VALID: continue` or `if impossible: return` check BEFORE recursing.

---

## 🗺️ How to Track Any Backtracking Problem (Step-by-Step Process)

```
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: Identify the STATE                                 │
│          What are you building? (path, board, subset...)    │
├─────────────────────────────────────────────────────────────┤
│  STEP 2: Identify the CHOICES                               │
│          What can you pick at each step?                    │
├─────────────────────────────────────────────────────────────┤
│  STEP 3: Identify the BASE CASE                             │
│          When do you stop? When do you record?              │
├─────────────────────────────────────────────────────────────┤
│  STEP 4: Draw the RECURSION TREE (first 2-3 levels)         │
│          Don't code yet — draw the tree on paper            │
├─────────────────────────────────────────────────────────────┤
│  STEP 5: Fill the TRACKING TABLE                            │
│          Trace columns: depth | state | choices | action    │
├─────────────────────────────────────────────────────────────┤
│  STEP 6: Identify PRUNING conditions                        │
│          What branches are obviously invalid?               │
├─────────────────────────────────────────────────────────────┤
│  STEP 7: Code using the TEMPLATE                            │
│          make → recurse → unmake                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔑 The One Mental Model That Unlocks Everything

> **Backtracking = You are the tree. Each recursive call IS a node. Returning from a call IS moving back up the tree.**

When you feel lost in a backtracking trace, ask yourself:

```
1. "What is in `path` RIGHT NOW at this call?" → that's your node
2. "What loop iteration am I on?"              → that's your edge
3. "Did I just push or pop?"                   → MAKE or UNMAKE
4. "Am I going down or returning?"             → recurse or backtrack
```

---

## 📊 Complexity Tracking Table

```
┌─────────────────┬─────────────────┬──────────────────────────────┐
│  PROBLEM        │  TIME           │  WHY                         │
├─────────────────┼─────────────────┼──────────────────────────────┤
│  Subsets(n)     │  O(n · 2^n)     │  2^n subsets, copy costs n   │
│  Permutations   │  O(n · n!)      │  n! perms, copy costs n      │
│  Combinations   │  O(k · C(n,k))  │  C(n,k) combos, copy k      │
│  N-Queens       │  O(n!)          │  prune invalid placements    │
└─────────────────┴─────────────────┴──────────────────────────────┘
```

---

## ⚡ Go Implementation (Same Problem, Idiomatic Go)

```go
func subsets(nums []int) [][]int {
    result := [][]int{}
    path := []int{}

    var backtrack func(start int)
    backtrack = func(start int) {
        // Record current state (copy! slices share memory)
        tmp := make([]int, len(path))
        copy(tmp, path)
        result = append(result, tmp)

        for i := start; i < len(nums); i++ {
            path = append(path, nums[i])  // MAKE
            backtrack(i + 1)              // RECURSE
            path = path[:len(path)-1]     // UNMAKE ← backtrack
        }
    }

    backtrack(0)
    return result
}
```

> ⚠️ **Critical Go Gotcha:** Never `append(result, path)` directly — slices are references. Always `copy` before saving. This is one of the most common bugs in Go backtracking.

---

## 🧘 The Monk's Checklist Before Every Backtracking Problem

```
□  Can I name the STATE clearly in one sentence?
□  Can I list ALL possible CHOICES at one step?
□  Do I know the exact BASE CASE condition?
□  Did I draw at least 2 levels of the recursion tree?
□  Is my UNDO step the EXACT reverse of my MAKE step?
□  Did I identify any PRUNING condition?
□  Am I copying state correctly (no aliasing bugs)?
```

Master this tracking discipline, and backtracking becomes as readable as a loop. The tree IS the algorithm — once you see the tree, the code writes itself.