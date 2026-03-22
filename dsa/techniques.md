This is going to be an extensive, structured masterclass. Let me build it layer by layer — from foundational to advanced — with ASCII visualizations, decision trees, and deep mental models for each technique.

---

# The Complete DSA Techniques Encyclopedia

> **Mental Model First:** Before memorizing techniques, understand *why* they exist. Every technique is an answer to a specific *waste* — wasted computation, wasted space, or wasted structure. When you recognize the waste, the technique reveals itself.

---

## Technique Master Index

```
┌─────────────────────────────────────────────────────────────────┐
│                    DSA TECHNIQUES UNIVERSE                      │
├─────────────────────────────────────────────────────────────────┤
│  TIER 1 — Array/String Techniques                               │
│  ├── 01. Two Pointers                                           │
│  ├── 02. Sliding Window                                         │
│  ├── 03. Fast & Slow Pointers                                   │
│  ├── 04. Prefix Sum / Suffix Sum                                │
│  └── 05. Kadane's Technique (Max Subarray Pattern)              │
│                                                                 │
│  TIER 2 — Search & Reduction Techniques                         │
│  ├── 06. Binary Search (on Answer)                              │
│  ├── 07. Divide and Conquer                                     │
│  └── 08. Meet in the Middle                                     │
│                                                                 │
│  TIER 3 — Graph Traversal Techniques                            │
│  ├── 09. DFS (Depth-First Search)                               │
│  ├── 10. BFS (Breadth-First Search)                             │
│  └── 11. Topological Sort                                       │
│                                                                 │
│  TIER 4 — Optimization Techniques                               │
│  ├── 12. Dynamic Programming                                    │
│  ├── 13. Greedy                                                 │
│  └── 14. Backtracking                                           │
│                                                                 │
│  TIER 5 — Data Structure Techniques                             │
│  ├── 15. Hashing                                                │
│  ├── 16. Monotonic Stack                                        │
│  ├── 17. Monotonic Queue (Deque)                                │
│  └── 18. Union-Find (Disjoint Set)                              │
│                                                                 │
│  TIER 6 — Advanced Techniques                                   │
│  ├── 19. Bit Manipulation                                       │
│  ├── 20. Sweep Line                                             │
│  └── 21. Reservoir Sampling                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## MASTER DECISION TREE
### "Which Technique Do I Use?"

```
Start with the problem
         │
         ▼
Is the input LINEAR (array, string, linked list)?
         │
   ┌─────┴─────┐
  YES          NO (graph/tree)
   │            └──► Go to GRAPH section
   ▼
Do you need a SUBARRAY or SUBSTRING?
         │
   ┌─────┴─────┐
  YES          NO
   │            │
   ▼            ▼
Fixed size?   Looking for pairs / triplets?
   │               │
  YES   NO        YES      NO
   │    │          │       │
Sliding Two      Two    Are you
Window  Pointers Ptrs   counting?
        (sort    (sort    │
        first)   first)  YES
                          │
                       Hashing /
                       Prefix Sum

If NO subarray:
   │
   ▼
Is there a RECURSIVE structure? (subproblems)
         │
   ┌─────┴─────┐
  YES          NO
   │            │
   ▼            ▼
Overlapping   Is input
subproblems?  SORTED?
   │               │
  YES   NO        YES      NO
   │    │          │       │
  DP  Divide   Binary   Hashing /
      Conquer  Search   Greedy
               on Answer

Constraints help:
   n ≤ 20      → Bitmask DP or Backtracking
   n ≤ 1000    → O(n²) OK, DP likely
   n ≤ 10^5    → O(n log n), think Sorting / Binary Search
   n ≤ 10^6+   → O(n) only, think Hashing / Two Pointers
```

---

## TIER 1 — Array/String Techniques

---

### 01. TWO POINTERS

#### What is a Pointer?
A pointer here is just an **index** — a number that says "I'm looking at position i in this array." Two pointers means you use **two such indices simultaneously**.

#### Core Idea

Instead of checking every pair (O(n²)), you place one pointer at the **left** and one at the **right**, and move them intelligently based on a condition. This eliminates unnecessary work.

```
BRUTE FORCE — O(n²):
Check every pair:
[1, 2, 3, 4, 5, 6]
 ↑  ↑              pair (0,1)
 ↑     ↑           pair (0,2)
 ↑        ↑        pair (0,3)
... and so on. Wasteful!

TWO POINTERS — O(n):
[1, 2, 3, 4, 5, 6]   target = 7
 L              R
 sum = 1+6 = 7  ✓ FOUND!

[1, 2, 3, 4, 5, 6]   target = 9
 L              R
 sum = 1+6 = 7 < 9  → move L right

[1, 2, 3, 4, 5, 6]
    L           R
    sum = 2+6 = 8 < 9  → move L right

[1, 2, 3, 4, 5, 6]
       L        R
       sum = 3+6 = 9  ✓ FOUND!
```

#### Algorithm Flow

```
SORTED array required for "sum" problems.

         ┌─────────────────────────────┐
         │  Place L=0, R=n-1           │
         └──────────────┬──────────────┘
                        │
                        ▼
         ┌─────────────────────────────┐
         │  While L < R                │
         └──────────────┬──────────────┘
                        │
                        ▼
              Compute condition
              (e.g., arr[L]+arr[R])
                        │
          ┌─────────────┼─────────────┐
          │             │             │
     Too small      Just right    Too large
          │             │             │
       L = L+1     Record/Return   R = R-1
          │             │             │
          └─────────────┴─────────────┘
                        │
                   Loop again
```

#### Variants

```
VARIANT 1: Opposite ends (classic)
[L ──────────────────── R]

VARIANT 2: Same direction (slow & fast)
[L → → F → → → → → → →]
Used for: in-place removal, partitioning

VARIANT 3: Two separate arrays
arr1: [L1 →]
arr2: [L2 →]
Used for: merging sorted arrays
```

#### When to Use
- Array is **sorted** (or you can sort it)
- Problem involves **pairs** or **triplets** summing to a target
- **Palindrome** checking
- **Partitioning** or in-place removal

#### Mental Model
> Imagine two people walking toward each other from opposite ends of a rope. They stop when they meet. Every step eliminates an impossible region. That's Two Pointers.

---

### 02. SLIDING WINDOW

#### What is a Window?
A **window** is a contiguous subarray (or substring) defined by two indices: `left` and `right`. It "slides" across the array.

#### Core Idea

Instead of recalculating properties of every subarray from scratch, you **maintain state** as the window expands and contracts. Adding a new right element is O(1). Removing the old left element is O(1). The total work is O(n).

```
PROBLEM: Find max sum subarray of size k=3

BRUTE FORCE — O(n·k):
[1, 3, -1, -3, 5, 3]
 └──┘         sum=3
    └──┘       sum=-1
       └───┘   sum=1
          └───┘ sum=5  ← recalculate each time

SLIDING WINDOW — O(n):
Initial window:
[1, 3, -1, -3, 5, 3]
 └──────┘        sum = 3

Slide: subtract left (1), add right (-3):
[1, 3, -1, -3, 5, 3]
    └───────┘    sum = 3 - 1 + (-3) = -1

Slide: subtract left (3), add right (5):
[1, 3, -1, -3, 5, 3]
        └────────┘   sum = -1 - 3 + 5 = 1

...
```

#### Fixed vs. Variable Window

```
FIXED WINDOW (size k):
─────────────────────────────────────────────────
    while right < n:
        add arr[right] to window
        if window size > k:
            remove arr[left], left++
        if window size == k:
            update answer
        right++

VARIABLE WINDOW (shrink when condition violated):
─────────────────────────────────────────────────
    while right < n:
        add arr[right] to window
        while window is INVALID:    ← shrink
            remove arr[left], left++
        update answer (window is now valid)
        right++
```

#### Visual: Variable Window in Action

```
Problem: Longest substring with at most 2 distinct chars
"a a b b c c a"
 0 1 2 3 4 5 6

Step 1: add 'a'  → {a:1}      window="a"      len=1
Step 2: add 'a'  → {a:2}      window="aa"     len=2
Step 3: add 'b'  → {a:2,b:1}  window="aab"    len=3
Step 4: add 'b'  → {a:2,b:2}  window="aabb"   len=4
Step 5: add 'c'  → {a:2,b:2,c:1} ← INVALID (3 distinct)
        SHRINK: remove 'a' → {a:1,b:2,c:1} still 3 chars
        SHRINK: remove 'a' → {b:2,c:1}     now valid
        window="bbcc"   len=4  ← same best

Answer: 4
```

#### Mental Model
> A sliding window is like a camera lens panning across a film strip. You don't reprint the whole strip — you just track what enters and exits the frame.

---

### 03. FAST & SLOW POINTERS

#### Core Idea

Two pointers move at **different speeds** through a linked list or array. The fast pointer moves 2 steps per iteration; the slow pointer moves 1 step. If there is a cycle, they **must eventually meet** (like two runners on a circular track).

#### Floyd's Cycle Detection — Visual

```
Linked list with cycle:
1 → 2 → 3 → 4 → 5
                ↑   ↓
                8 ← 6
                ↑   ↓
                    7

Iteration 1:
slow: 1→2    fast: 1→3

Iteration 2:
slow: 2→3    fast: 3→5

Iteration 3:
slow: 3→4    fast: 5→7

Iteration 4:
slow: 4→5    fast: 7→4

Iteration 5:
slow: 5→6    fast: 4→6  ← MEET! Cycle confirmed.
```

#### Phase 2 — Finding Cycle Start

```
After detection:
Reset slow to HEAD, keep fast at meeting point.
Both move 1 step at a time.
They meet at the CYCLE ENTRANCE.

This is a mathematical property:
distance(head → cycle_start) = distance(meeting_point → cycle_start)
```

#### Other Uses

```
USE CASE 1: Find Middle of Linked List
slow moves 1, fast moves 2
When fast reaches end, slow is at middle

1 → 2 → 3 → 4 → 5
                 fast ends here
         slow ends here = MIDDLE ✓

USE CASE 2: kth Node from End
Move fast k steps ahead.
Then move both 1 step at a time.
When fast reaches end, slow is at kth from end.
```

---

### 04. PREFIX SUM

#### What is a Prefix?
A **prefix** is everything from the beginning up to (and including) some position. The prefix sum at index `i` is the sum of all elements from index 0 to i.

#### Building the Prefix Sum Array

```
Original:  [3,  1,  4,  1,  5,  9,  2,  6]
Indices:    0   1   2   3   4   5   6   7

Prefix:    [3,  4,  8,  9, 14, 23, 25, 31]
            │
            └── prefix[i] = prefix[i-1] + arr[i]
```

#### Why This Is Powerful

```
PROBLEM: Sum of subarray from index L to R

BRUTE FORCE: loop from L to R → O(n) per query

PREFIX SUM:
sum(L, R) = prefix[R] - prefix[L-1]

Example: sum from index 2 to 5
= prefix[5] - prefix[1]
= 23 - 4
= 19

[3,  1,  4,  1,  5,  9]
          └────────┘
          4+1+5+9 = 19 ✓

O(1) per query after O(n) preprocessing!
```

#### 2D Prefix Sum (Matrix)

```
Matrix:
┌─────────────┐
│ 1  2  3  4  │
│ 5  6  7  8  │
│ 9 10 11 12  │
└─────────────┘

Prefix[i][j] = sum of rectangle from (0,0) to (i,j)

Query: sum of sub-rectangle (r1,c1) to (r2,c2):
= P[r2][c2] - P[r1-1][c2] - P[r2][c1-1] + P[r1-1][c1-1]

(Inclusion-exclusion principle — add back what you subtracted twice)
```

#### Mental Model
> A prefix sum converts repeated range-sum queries from O(n) to O(1) by pre-computing cumulative totals. It's a trade: pay O(n) once, save O(n) every query.

---

### 05. KADANE'S TECHNIQUE (Maximum Subarray)

#### Core Idea

At each position, you make a binary decision:
- **Extend** the current subarray
- **Start fresh** from this element

```
arr = [-2, 1, -3, 4, -1, 2, 1, -5, 4]

Decision at each step:
pos 0: max(-2, -2) = -2    current=-2    global=-2
pos 1: max(1, -2+1) = 1    current=1     global=1
pos 2: max(-3, 1-3) = -2   current=-2    global=1
pos 3: max(4, -2+4) = 4    current=4     global=4
pos 4: max(-1, 4-1) = 3    current=3     global=4
pos 5: max(2, 3+2)  = 5    current=5     global=5
pos 6: max(1, 5+1)  = 6    current=6     global=6
pos 7: max(-5, 6-5) = 1    current=1     global=6
pos 8: max(4, 1+4)  = 5    current=5     global=6

Answer: 6
Subarray: [4, -1, 2, 1]
```

The formula: `current = max(arr[i], current + arr[i])`

This is a **DP technique** compressed into O(1) space because each state only depends on the previous state.

---

## TIER 2 — Search & Reduction Techniques

---

### 06. BINARY SEARCH (On Answer)

#### Beyond Sorted Arrays

Most people know binary search for searching in sorted arrays. The **expert use** is "binary search on the answer space."

**Key Insight:** When you want to find the **minimum or maximum value** that satisfies a condition, and that condition is **monotonic** (if value X works, all values > X also work, or all values < X also work), you can binary search over the answer directly.

```
MONOTONIC CONDITION — Visual:

Value:  1  2  3  4  5  6  7  8  9  10
Works?  N  N  N  Y  Y  Y  Y  Y  Y  Y
                ↑
           Answer is here (minimum valid)

Binary search on this sequence!
```

#### Flowchart: Binary Search on Answer

```
     ┌──────────────────────────────────┐
     │ Define lo = min_possible_answer  │
     │ Define hi = max_possible_answer  │
     └─────────────────┬────────────────┘
                       │
                       ▼
     ┌──────────────────────────────────┐
     │      While lo < hi               │
     └─────────────────┬────────────────┘
                       │
                       ▼
              mid = lo + (hi - lo) / 2
              (avoids integer overflow)
                       │
                       ▼
            Can we achieve 'mid'?
            (call check(mid) function)
                       │
              ┌────────┴────────┐
             YES               NO
              │                 │
         hi = mid           lo = mid + 1
              │                 │
              └────────┬────────┘
                       │
                  Loop again
                       │
              lo == hi → ANSWER
```

#### Classic Example: Allocate Minimum Pages

```
Books: [12, 34, 67, 90]   students: 2

Answer space: [max_single_book=90, sum_all=203]
Binary search between 90 and 203.

check(mid): Can we allocate with max_pages = mid?
  Greedily assign books until student's pages exceed mid.
  If students needed ≤ 2, then mid works.

mid=146: check → needs 2 students. Works! → hi=146
mid=118: check → needs 2 students. Works! → hi=118
mid=104: check → needs 2 students. Works! → hi=104
mid= 97: check → needs 3 students. FAILS! → lo=98
...
Answer: 113
```

---

### 07. DIVIDE AND CONQUER

#### Core Idea

Break a problem into **independent subproblems**, solve each recursively, then **combine** the results.

```
STRUCTURE:

           Problem(n)
          /          \
    Problem(n/2)  Problem(n/2)
    /      \         /     \
P(n/4)  P(n/4)  P(n/4)  P(n/4)
  ...

Depth = log(n) levels
Work per level = n (combining)
Total = O(n log n)
```

#### Recurrence Relation

```
T(n) = a·T(n/b) + f(n)

a = number of subproblems
b = factor by which problem shrinks
f(n) = cost of combining

Master Theorem tells you the complexity.

Merge Sort:  T(n) = 2T(n/2) + O(n) → O(n log n)
Binary Search: T(n) = T(n/2) + O(1) → O(log n)
```

#### Key Insight: vs. Dynamic Programming

```
DIVIDE AND CONQUER         DYNAMIC PROGRAMMING
──────────────────         ───────────────────
Subproblems are            Subproblems OVERLAP
INDEPENDENT                (same subproblem
                           computed multiple times)

Combine results            Store results
after recursion            (memoize/tabulate)

Top-down flow              Either direction

Example: Merge Sort        Example: Fibonacci
```

---

### 08. MEET IN THE MIDDLE

#### What is a Middle?
You split the problem in half. Solve each half independently, then combine the solutions. This takes O(2^(n/2)) instead of O(2^n) — a dramatic improvement.

```
Problem: Subset sum — does any subset of n=40 numbers sum to T?

Brute force: 2^40 ≈ 10^12 subsets. Too slow.

Meet in Middle:
Left half  (20 numbers): all 2^20 ≈ 10^6 possible sums → store in hashset
Right half (20 numbers): all 2^20 ≈ 10^6 possible sums

For each right sum R, check if (T - R) is in left hashset.

Total: ~2 × 10^6 operations. Feasible!
```

```
VISUAL:

FULL PROBLEM:
[a1 a2 a3 a4 a5 a6 a7 a8]
 └────────────────────────┘ 2^8 = 256

SPLIT:
[a1 a2 a3 a4] [a5 a6 a7 a8]
 └─────────┘   └─────────┘
  2^4=16         2^4=16

Cross-reference: 16 + 16 + match_check
```

---

## TIER 3 — Graph Traversal Techniques

#### Prerequisite Vocabulary
- **Vertex/Node:** A point in a graph
- **Edge:** A connection between two vertices
- **Neighbor:** A vertex directly connected to another
- **Visited:** A vertex we've already processed
- **Component:** A group of connected vertices

---

### 09. DFS (Depth-First Search)

#### Core Idea

Go as **deep as possible** along one path before backtracking. Like exploring a maze by always choosing the leftmost unexplored path.

```
GRAPH:
        1
       / \
      2   3
     / \   \
    4   5   6

DFS from 1:
Visit 1 → go to 2 → go to 4 → DEAD END → backtrack
        → go to 5 → DEAD END → backtrack
        → back to 1 → go to 3 → go to 6 → DEAD END

Order: 1, 2, 4, 5, 3, 6
```

#### Implementation Mental Model

```
RECURSIVE (uses call stack):
──────────────────────────
dfs(node):
    mark node as visited
    for each neighbor of node:
        if neighbor not visited:
            dfs(neighbor)

ITERATIVE (uses explicit stack):
────────────────────────────────
stack = [start]
while stack not empty:
    node = stack.pop()
    if node not visited:
        mark visited
        push all unvisited neighbors

KEY: pop() from stack = go DEEP
     (most recently added neighbor processed first)
```

#### DFS on Trees — The Three Orders

```
Tree:
       A
      / \
     B   C
    / \
   D   E

PREORDER  (root → left → right): A B D E C
INORDER   (left → root → right): D B E A C   ← gives sorted order for BST!
POSTORDER (left → right → root): D E B C A   ← children before parent

When to use:
Preorder  → Copy/serialize a tree
Inorder   → Get sorted elements from BST
Postorder → Delete tree, compute subtree properties
```

#### DFS Applications

```
┌─────────────────────────────────────────────────────┐
│ PROBLEM TYPE             │ HOW DFS HELPS             │
├─────────────────────────────────────────────────────┤
│ Connected components     │ DFS from each unvisited   │
│ Cycle detection          │ Track back-edges          │
│ Topological sort         │ Post-order DFS            │
│ Path finding             │ DFS + backtrack           │
│ Flood fill               │ DFS on 2D grid            │
│ Articulation points      │ Track discovery time      │
└─────────────────────────────────────────────────────┘
```

---

### 10. BFS (Breadth-First Search)

#### Core Idea

Explore all vertices at distance 1, then all at distance 2, then distance 3... Like ripples in a pond. Uses a **queue** (FIFO) instead of stack.

```
GRAPH:
        1
       / \
      2   3
     / \   \
    4   5   6

BFS from 1:
Level 0: [1]
Level 1: [2, 3]
Level 2: [4, 5, 6]

Order: 1, 2, 3, 4, 5, 6
```

#### Why BFS Finds Shortest Path

```
Every vertex is first discovered at its MINIMUM distance from source.
This is because BFS processes vertices in order of distance.

If vertex X is at distance d, all vertices at distance d
are discovered before any at distance d+1.

This property makes BFS the go-to for:
- Shortest path in UNWEIGHTED graphs
- Minimum number of steps
- Word ladder problems
- 0-1 BFS (for 0/1 weighted edges)
```

#### BFS vs DFS Decision

```
                  ┌─────────────────────────────┐
                  │  Does ORDER of exploration   │
                  │  matter?                     │
                  └──────────────┬──────────────┘
                                 │
                    ┌────────────┴────────────┐
                   YES                        NO
                    │                          │
     ┌──────────────┴──────────────┐    Either works.
     │                             │    DFS uses less
     ▼                             ▼    memory (O(h)
Need SHORTEST                 Need to       vs O(w))
path / min steps?          explore deep
     │                      structure?
    YES                          │
     │                          YES
     ▼                           │
   BFS                          DFS
```

---

### 11. TOPOLOGICAL SORT

#### What is Topological Order?
For a **Directed Acyclic Graph (DAG)**, it's an ordering of vertices such that for every directed edge u→v, vertex u comes before v.

**Real world:** Task scheduling. If task A must happen before task B, then A appears before B in the sorted order.

```
GRAPH:
Compile A → Run Tests → Deploy
     ↓                     ↑
  Build B ─────────────────┘

Valid topological orders:
[Compile A, Build B, Run Tests, Deploy]
[Compile A, Run Tests, Build B, Deploy]  ← also valid

Invalid:
[Deploy, Run Tests, Compile A, Build B]  ← Deploy before its deps!
```

#### Two Algorithms

```
ALGORITHM 1: DFS-based (Postorder)
─────────────────────────────────
Run DFS. When a node finishes (all neighbors visited),
push it to a STACK.
Pop the stack = topological order.

WHY: A node is "finished" only after all its successors
are finished. So it goes behind them in the result.

ALGORITHM 2: Kahn's Algorithm (BFS-based)
─────────────────────────────────────────
1. Compute in-degree of every vertex.
   (in-degree = number of incoming edges)
2. Add all vertices with in-degree 0 to queue.
3. Process queue:
   - Remove vertex u
   - Add u to result
   - For each neighbor v: in-degree[v]--
   - If in-degree[v] becomes 0, add v to queue
4. If result size < total vertices → CYCLE EXISTS

VISUAL:
A(0) → B(1) → D(2)
              ↑
C(0) → ─────┘

Initial queue: [A, C]  (in-degree 0)
Process A: B's in-degree → 0, add B
Process C: D's in-degree → 1
Process B: D's in-degree → 0, add D
Process D: done

Result: A, C, B, D  ✓
```

---

## TIER 4 — Optimization Techniques

---

### 12. DYNAMIC PROGRAMMING (DP)

#### The Core Insight

DP solves problems with **overlapping subproblems** by ensuring each subproblem is solved **exactly once**.

#### Key Vocabulary
- **State:** A compact description of a subproblem (e.g., dp[i] = answer considering first i elements)
- **Transition:** How you get from one state to another (the recurrence relation)
- **Base case:** The smallest subproblem you can answer directly
- **Memoization:** Top-down DP (cache recursive results)
- **Tabulation:** Bottom-up DP (fill a table iteratively)

#### The Five DP Steps (Expert Framework)

```
STEP 1: Define the STATE
   What does dp[i] (or dp[i][j]) represent?
   This is the hardest step. Get this right and the rest follows.

STEP 2: Define the TRANSITION
   How does dp[i] relate to previous states?
   dp[i] = f(dp[i-1], dp[i-2], ...)

STEP 3: Define BASE CASES
   What is dp[0]? dp[1]?

STEP 4: Define the ORDER of computation
   Which states need to be computed before which?

STEP 5: Extract the ANSWER
   Is it dp[n]? max(dp[i])? dp[n][m]?
```

#### DP Patterns

```
PATTERN 1: Linear DP
dp[i] depends only on previous elements.
Example: Fibonacci, Climbing Stairs, House Robber

PATTERN 2: Interval DP
dp[i][j] = answer for subarray/substring from i to j.
Example: Matrix Chain Multiplication, Palindrome Partitioning

PATTERN 3: Knapsack (Subset DP)
dp[i][w] = best value using first i items with weight limit w
Example: 0/1 Knapsack, Subset Sum

PATTERN 4: Grid DP
dp[i][j] = answer for grid position (i,j)
Example: Unique Paths, Minimum Path Sum

PATTERN 5: Sequence DP
dp[i] = answer for sequences ending at i
Example: LIS (Longest Increasing Subsequence), LCS

PATTERN 6: Bitmask DP
State encodes which elements have been used as a bit mask
Example: Travelling Salesman, Assignment Problems
```

#### Memoization vs Tabulation

```
MEMOIZATION (Top-Down):              TABULATION (Bottom-Up):
────────────────────────             ────────────────────────
Write recursive function             Build table from base case
Cache results in hashmap             up to final answer

fib(5)                               fib = [0, 1, _, _, _, _]
  fib(4)                             fib[2] = fib[1]+fib[0] = 1
    fib(3)                           fib[3] = fib[2]+fib[1] = 2
      fib(2) → cache                 fib[4] = 3
      fib(1) → cache                 fib[5] = 5
    fib(2) → LOOKUP ✓
  fib(3) → LOOKUP ✓

PRO: Only computes needed states     PRO: No recursion overhead
CON: Recursion stack overhead        CON: Computes all states
```

#### Visual: Fibonacci Overlapping Subproblems

```
Without memoization:
fib(5) calls fib(4) and fib(3)
fib(4) calls fib(3) and fib(2)
fib(3) called TWICE — WASTE!

          fib(5)
         /      \
     fib(4)    fib(3)  ← computed twice!
     /    \    /    \
  fib(3) fib(2) fib(2) fib(1)
  /   \
fib(2) fib(1)

With memoization: each node computed ONCE.
```

---

### 13. GREEDY

#### Core Idea

At every step, make the **locally optimal** choice, trusting that this leads to a **globally optimal** solution.

```
KEY QUESTION: Does greedy work here?
It works when the problem has the "Greedy Choice Property":
A globally optimal solution includes the locally optimal choice.

This is NOT always true. Counterexample:
[1, 3, 3] → max path sum? 
Greedy: pick max at each step.
Tree:
        1
       / \
      3   5
     / \ / \
   10  3 2  6

Greedy from root: 1 → 5 → 6 = 12
Optimal:          1 → 3 → 10 = 14
Greedy FAILS here → need DP!
```

#### When Greedy Is Provably Correct

```
1. INTERVAL SCHEDULING:
   Sort by END TIME. Always pick earliest-ending interval.
   Why? Picking the earliest-ending interval leaves the
   maximum room for future intervals.

2. HUFFMAN CODING:
   Always merge the two lowest-frequency nodes.

3. DIJKSTRA'S SHORTEST PATH:
   Always process the unvisited vertex with minimum distance.
   Works because edges are non-negative.

4. FRACTIONAL KNAPSACK:
   Sort by value/weight ratio, pick greedily.
   (0/1 Knapsack requires DP because items aren't divisible)
```

#### Greedy vs DP Decision

```
                ┌──────────────────────────────┐
                │  Can you prove that the local │
                │  choice never hurts future    │
                │  choices?                     │
                └──────────────┬───────────────┘
                               │
                  ┌────────────┴────────────┐
                 YES                        NO
                  │                          │
                Greedy                      DP
              (Faster,                 (More general,
              O(n log n)               O(n²) or worse)
              usually)
```

---

### 14. BACKTRACKING

#### Core Idea

Backtracking is **systematic exhaustive search with pruning**. You build candidates incrementally and **abandon** (backtrack) a candidate as soon as you determine it cannot lead to a valid solution.

#### The Backtracking Template

```
UNIVERSAL TEMPLATE:
────────────────────────────────────────────
backtrack(current_state, choices):
    if is_solution(current_state):
        record(current_state)
        return

    for each choice in choices:
        if is_valid(choice, current_state):
            make(choice)                  ← add to state
            backtrack(new_state, new_choices)
            unmake(choice)               ← BACKTRACK (undo)
```

#### Visual: N-Queens Backtracking

```
Place queens on 4×4 board, no two attacking each other.

Try placing queen in row 0:
  Col 0: Q . . .    → proceed to row 1
                         Col 0: ATTACK (same col)
                         Col 1: ATTACK (diagonal)
                         Col 2: Q . Q .  → proceed to row 2
                                              Col 0: ATTACK
                                              Col 1: ATTACK
                                              Col 2: ATTACK
                                              Col 3: ATTACK
                                         BACKTRACK → try col 3
                         Col 3: Q . . Q  → proceed to row 2
                                              Col 1: . Q . .  → row 3
                                              ... and so on

The key: when stuck, go BACK and try the next option.
```

#### Pruning — The Art of Backtracking

```
WITHOUT PRUNING: Brute force (try everything)
WITH PRUNING:    Prune branches that can't possibly lead to solution

Example: Subset sum
arr = [1, 2, 3, 4, 5], target = 10

Without pruning: try all 2^5 = 32 subsets
With pruning: if current_sum > target, stop immediately
              → many branches pruned early
```

---

## TIER 5 — Data Structure Techniques

---

### 15. HASHING

#### Core Idea

A **hash function** maps a key (string, number, object) to an integer index in an array. This gives O(1) average-case lookup, insertion, and deletion.

#### What is a Hash Function?

```
key  →  hash function  →  index (0 to N-1)

"apple" → h("apple") → 3
"cat"   → h("cat")   → 7
"dog"   → h("dog")   → 3  ← COLLISION!

Hash function: key % table_size (simple but weak)
Better: polynomial rolling hash, Murmur, FNV
```

#### Collision Handling

```
CHAINING:
Each bucket holds a linked list.
All keys that hash to same bucket go in its list.

Bucket 3: ["apple", "dog"]  ← both in chain

OPEN ADDRESSING:
On collision, probe next available slot.
Linear probing: try index+1, +2, +3...
Quadratic probing: try index+1², +2², +3²...
Double hashing: use second hash function for step size
```

#### Hashing Techniques in DSA

```
TECHNIQUE 1: Frequency Map
arr = [1, 2, 2, 3, 3, 3]
freq = {1:1, 2:2, 3:3}
Used for: anagram detection, majority element

TECHNIQUE 2: Complement Lookup
"Two Sum": find pair summing to target
For each num, check if (target - num) in hashmap
O(n) instead of O(n²)

TECHNIQUE 3: Prefix Sum + Hashing
"Subarray with given sum"
Store seen prefix sums in hashmap.
If (current_prefix - target) exists → subarray found!

TECHNIQUE 4: Rolling Hash
For pattern matching in strings.
Hash a window, slide it: subtract left char, add right char.
O(n) matching (Rabin-Karp algorithm)
```

---

### 16. MONOTONIC STACK

#### What is Monotonic?
**Monotonic** means "always increasing" or "always decreasing." A monotonic stack maintains this property by popping elements that violate the order before pushing the new element.

#### Visual: Next Greater Element

```
PROBLEM: For each element, find the next greater element to its right.

arr = [2, 1, 2, 4, 3]

Use a DECREASING stack (top is smallest):

Process 2: stack empty, push 2.  Stack: [2]
Process 1: 1 < 2, push 1.        Stack: [2, 1]
Process 2: 2 > 1, POP 1 → NGE(1) = 2
           2 = top(2), push 2.   Stack: [2, 2]
Process 4: 4 > 2, POP 2 → NGE(2) = 4 (rightmost)
           4 > 2, POP 2 → NGE(2) = 4 (leftmost)
           push 4.               Stack: [4]
Process 3: 3 < 4, push 3.        Stack: [4, 3]
End: remaining stack elements have no NGE → -1

Result: [4, 2, 4, -1, -1]

KEY INSIGHT:
When we pop element X because new element Y > X,
Y is the NEXT GREATER ELEMENT for X.
```

#### Algorithm Flow

```
For NEXT GREATER ELEMENT (right side):
────────────────────────────────────────
for i from 0 to n-1:
    while stack not empty AND arr[stack.top] < arr[i]:
        idx = stack.pop()
        result[idx] = arr[i]   ← current element is NGE for popped
    stack.push(i)
remaining in stack → result[idx] = -1

For PREVIOUS SMALLER ELEMENT (left side):
────────────────────────────────────────
Same idea, but process elements left-to-right with
an INCREASING stack (pop when new element is SMALLER).
```

#### Applications of Monotonic Stack

```
┌─────────────────────────────────────────────────────────┐
│ PROBLEM                     │ STACK TYPE                │
├─────────────────────────────────────────────────────────┤
│ Next greater element        │ Decreasing (right→left)   │
│ Previous smaller element    │ Increasing (left→right)   │
│ Largest rectangle in hist.  │ Increasing                │
│ Trapping rainwater          │ Decreasing                │
│ Daily temperatures          │ Decreasing                │
│ Stock span problem          │ Decreasing                │
└─────────────────────────────────────────────────────────┘
```

---

### 17. MONOTONIC QUEUE (DEQUE)

#### Core Idea

Like a monotonic stack, but also supports efficient removal from the **front**. This enables sliding window maximum/minimum in O(n) total time.

```
PROBLEM: Sliding window maximum (window size k)

arr = [1, 3, -1, -3, 5, 3, 6, 7],  k = 3

Use a DECREASING deque (stores indices, front = max):

Window [1,3,-1]:
  Add 1(idx 0): deque=[0]
  Add 3(idx 1): 3>1, pop 0, deque=[1]
  Add -1(idx 2): -1<3, deque=[1,2]
  Max = arr[1] = 3

Window [3,-1,-3]:
  Add -3(idx 3): -3<-1, deque=[1,2,3]
  Front=1, still in window [1..3]. Max=arr[1]=3

Window [-1,-3,5]:
  Add 5(idx 4): 5>-3, pop 3; 5>-1, pop 2; 5>3, pop 1
  deque=[4]. Max=arr[4]=5

And so on...

KEY: deque.front() = index of current window's maximum
     Pop front if it's outside window (expired)
     Pop back if it's smaller than new element (useless)
```

---

### 18. UNION-FIND (Disjoint Set Union)

#### What is a Disjoint Set?
A **disjoint set** is a collection of non-overlapping sets. Union-Find maintains these sets and supports two operations:
- **Find(x):** Which set does x belong to? (Returns the "representative" of x's set)
- **Union(x, y):** Merge the sets containing x and y

#### Visual Representation

```
Initially: each element is its own set
[0] [1] [2] [3] [4]

Union(0, 1): merge sets of 0 and 1
  0         1 → 0    (1's parent becomes 0)
parent = [0, 0, 2, 3, 4]

Union(1, 2): merge sets of 1 and 2
Find(1) = 0, Find(2) = 2
Make 0 parent of 2:
parent = [0, 0, 0, 3, 4]

Union(3, 4):
parent = [0, 0, 0, 3, 3]

Now:
Set {0,1,2} with representative 0
Set {3,4}   with representative 3
```

#### Optimizations — Critical for Performance

```
OPTIMIZATION 1: Union by Rank
Always attach smaller tree under larger tree.
Keeps tree HEIGHT at O(log n) worst case.

OPTIMIZATION 2: Path Compression
When calling Find(x), compress path:
All nodes on path to root directly point to root.

Before Find(4):              After Find(4):
    0                            0
    │                          / │ \
    1                         1  2  4
    │
    2
    │
    4  (find returns 0)

WITH BOTH OPTIMIZATIONS:
find/union = O(α(n)) ≈ O(1) practically
(α = inverse Ackermann function, grows incredibly slowly)
```

#### Applications

```
┌─────────────────────────────────────────────────────────┐
│ PROBLEM                     │ HOW UNION-FIND HELPS      │
├─────────────────────────────────────────────────────────┤
│ Connected components        │ Union edges, count roots  │
│ Cycle detection (undirected)│ Union(u,v): if same set→cycle│
│ Kruskal's MST               │ Add edge if different sets│
│ Number of islands           │ Union adjacent land cells │
│ Accounts merge              │ Union emails of same user │
└─────────────────────────────────────────────────────────┘
```

---

## TIER 6 — Advanced Techniques

---

### 19. BIT MANIPULATION

#### Prerequisite: Bits
Every integer is stored as a sequence of bits (0s and 1s). Bit manipulation operates on these bits directly, often making operations O(1).

```
Decimal 13 = Binary 1101
                      │││└─ bit 0 = 1 (value 1)
                      ││└── bit 1 = 0 (value 2)
                      │└─── bit 2 = 1 (value 4)
                      └──── bit 3 = 1 (value 8)
                      1*8 + 1*4 + 0*2 + 1*1 = 13 ✓
```

#### Core Operations

```
OPERATION      SYNTAX    EXAMPLE (a=12=1100, b=10=1010)
───────────────────────────────────────────────────────
AND            a & b     1100 & 1010 = 1000 = 8
OR             a | b     1100 | 1010 = 1110 = 14
XOR            a ^ b     1100 ^ 1010 = 0110 = 6
NOT            ~a        ~1100 = ...0011 (depends on word size)
Left Shift     a << 1    1100 << 1 = 11000 = 24  (multiply by 2)
Right Shift    a >> 1    1100 >> 1 = 0110  = 6   (divide by 2)
```

#### Powerful Bit Tricks

```
TRICK 1: Check if ith bit is set
(n >> i) & 1 == 1

TRICK 2: Set ith bit
n | (1 << i)

TRICK 3: Clear ith bit
n & ~(1 << i)

TRICK 4: Toggle ith bit
n ^ (1 << i)

TRICK 5: Check if power of 2
n > 0 && (n & (n-1)) == 0
Why? Powers of 2: 1000, 0100, 0010... 
     n-1:         0111, 0011, 0001...
     AND = 0 always for powers of 2!

TRICK 6: Clear lowest set bit
n & (n-1)
Used to count set bits: loop until n=0

TRICK 7: Isolate lowest set bit
n & (-n)

TRICK 8: XOR swap (no temp variable)
a = a ^ b
b = a ^ b
a = a ^ b

TRICK 9: XOR of all elements (find unique)
If all elements appear twice except one,
XOR of all elements = the unique one
(x ^ x = 0, x ^ 0 = x)
```

#### Bitmask as Set Representation

```
For a set of n items (n ≤ 20 typically):
Represent subsets as integers where bit i = 1 means item i is included

{item 0, item 2} = 101 in binary = 5

Iterate all subsets: for mask from 0 to (1<<n)-1
Check if item i in subset: mask & (1<<i)
Add item i to subset:     mask | (1<<i)
Remove item i:            mask & ~(1<<i)
```

---

### 20. SWEEP LINE

#### Core Idea

Imagine a vertical line **sweeping** from left to right across a 2D plane. At each interesting x-coordinate (an "event"), you process what changes. This converts a 2D problem into a series of 1D problems.

```
EVENTS: Points where something starts or ends.

Problem: Count maximum overlapping intervals.

Intervals: [1,5], [2,6], [3,4], [6,8]

Events:
x=1: interval starts (+1)
x=2: interval starts (+1)
x=3: interval starts (+1)
x=4: interval ends   (-1)
x=5: interval ends   (-1)
x=6: interval ends (-1), starts (+1)
x=8: interval ends   (-1)

Sweep:
x=1: count=1
x=2: count=2
x=3: count=3  ← MAXIMUM
x=4: count=2
x=5: count=1
x=6: count=1 (end then start: -1+1=same)
x=8: count=0
```

#### Algorithm Flow

```
┌────────────────────────────────────┐
│  Create events:                    │
│  (x, type) where type=+1 or -1    │
└──────────────────┬─────────────────┘
                   │
                   ▼
┌────────────────────────────────────┐
│  Sort events by x                  │
│  (tie-break: ends before starts    │
│   or starts before ends — depends) │
└──────────────────┬─────────────────┘
                   │
                   ▼
┌────────────────────────────────────┐
│  Process events left to right      │
│  Maintain active set / counter     │
│  Update answer at each event       │
└────────────────────────────────────┘
```

#### Applications

```
┌─────────────────────────────────────────────────────────────┐
│ PROBLEM                       │ EVENT TYPE                  │
├─────────────────────────────────────────────────────────────┤
│ Max overlapping intervals     │ +1 start, -1 end            │
│ Area of union of rectangles   │ +height start, -height end  │
│ Skyline problem               │ Building edges              │
│ Insert interval               │ Sort + merge                │
│ Meeting rooms                 │ Booking start/end           │
└─────────────────────────────────────────────────────────────┘
```

---

### 21. RESERVOIR SAMPLING

#### Problem Statement

You have a stream of **unknown size** (or too large to fit in memory). How do you pick k items **uniformly at random** from the stream, with each item equally likely to be chosen?

```
ALGORITHM (k=1, pick 1 random item):

For i-th item seen (starting at i=1):
    Replace current selection with probability 1/i

PROOF OF CORRECTNESS:
After n items, probability item i is selected:
= P(selected at step i) × P(not replaced at step i+1) × ... × P(not replaced at step n)
= (1/i) × (i/(i+1)) × ((i+1)/(i+2)) × ... × ((n-1)/n)
= 1/n  ✓ (uniform!)

VISUAL:
Stream: [A, B, C, D, E]

Step 1: select A (prob 1/1 = 1)   result=A
Step 2: replace with B? (1/2)     result=A or B
Step 3: replace with C? (1/3)     
Step 4: replace with D? (1/4)
Step 5: replace with E? (1/5)
Each has exactly 1/5 probability of being selected!
```

---

## COGNITIVE FRAMEWORK: How to Master Techniques

```
┌─────────────────────────────────────────────────────────────────┐
│              THE FOUR STAGES OF TECHNIQUE MASTERY               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  STAGE 1: RECOGNITION (Pattern Detection)                       │
│  "I see this problem is about a contiguous subarray with        │
│   some constraint — this smells like Sliding Window."           │
│                                                                 │
│  STAGE 2: REDUCTION (Problem Transformation)                    │
│  "I can reduce this unfamiliar problem to a known pattern       │
│   by reframing the state or data structure."                    │
│                                                                 │
│  STAGE 3: APPLICATION (Technique Execution)                     │
│  "I apply the template, then customize the details."            │
│                                                                 │
│  STAGE 4: OPTIMIZATION (Refining the Solution)                  │
│  "Can I reduce space? Can the constant factor improve?"         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Constraint → Technique Cheat Sheet

```
┌────────────────────────────────────────────────────────────────┐
│ CONSTRAINT / CLUE                  │ LIKELY TECHNIQUE          │
├────────────────────────────────────────────────────────────────┤
│ n ≤ 20                             │ Bitmask DP, Backtracking  │
│ n ≤ 100                            │ O(n³) DP (intervals)      │
│ n ≤ 1000                           │ O(n²) DP                  │
│ n ≤ 10^5                           │ O(n log n) Sort/BinSearch │
│ n ≤ 10^6                           │ O(n) Hashing/Two Pointers │
│ "subarray"                         │ Sliding Window/Prefix Sum │
│ "subsequence"                      │ DP                        │
│ "sorted array"                     │ Binary Search/Two Ptrs    │
│ "all permutations"                 │ Backtracking              │
│ "shortest path, unweighted"        │ BFS                       │
│ "shortest path, weighted"          │ Dijkstra (Greedy)         │
│ "min/max value satisfying X"       │ Binary Search on Answer   │
│ "connected components"             │ BFS/DFS/Union-Find        │
│ "cycle in graph"                   │ DFS/Floyd/Union-Find      │
│ "dependency order"                 │ Topological Sort          │
│ "next greater element"             │ Monotonic Stack           │
│ "window maximum/minimum"           │ Monotonic Deque           │
│ "overlapping intervals"            │ Sweep Line / Sort         │
│ "counting with pairs/XOR"          │ Bit Manipulation          │
│ "stream, random sampling"          │ Reservoir Sampling        │
│ Graph + "minimum spanning tree"    │ Union-Find (Kruskal)      │
└────────────────────────────────────────────────────────────────┘
```

---

## The Psychological Layer: Deliberate Practice Principles

**Chunking:** Each technique is a "chunk" — a single mental unit. The expert doesn't think "shift left pointer, check sum, shift right pointer." They think "Two Pointers." Build your chunk library.

**Desirable Difficulty:** When you study a technique, immediately close your notes and try to reconstruct the template. The struggle of recall strengthens the neural encoding more than re-reading.

**Transfer Learning:** After solving 5 sliding window problems, ask yourself: *"What makes THIS a sliding window problem at its core?"* Abstracting the pattern enables you to recognize it in disguise.

**Interleaving:** Don't solve 20 Two Pointer problems in a row. Mix techniques. Your brain learns to *choose* techniques, not just execute them.

**The Expert's Inner Voice:** When an expert sees a problem, they don't read it and try techniques. They read it and hear a voice say *"this is a monotonic stack problem"* — pattern recognition built from hundreds of hours. Your goal is to build that voice.

---

> **The highest skill in DSA is not knowing the techniques — it is knowing which technique the problem is secretly asking for, even when it's disguised.** Every hard problem is an easy problem wearing a mask. The techniques in this guide are your tools to unmask it.