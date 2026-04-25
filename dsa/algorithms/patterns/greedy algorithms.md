# 🧠 Comprehensive Guide to Greedy Algorithms
> *"At every step, pick the best option you can see right now — and never look back."*

---

## Table of Contents

1. [What is a Greedy Algorithm?](#1-what-is-a-greedy-algorithm)
2. [The Mental Model — How to Think Greedy](#2-the-mental-model--how-to-think-greedy)
3. [Core Properties — When Does Greedy Work?](#3-core-properties--when-does-greedy-work)
4. [The Greedy Choice Proof Technique](#4-the-greedy-choice-proof-technique)
5. [Classic Greedy Patterns](#5-classic-greedy-patterns)
   - 5.1 [Activity Selection / Interval Scheduling](#51-activity-selection--interval-scheduling)
   - 5.2 [Fractional Knapsack](#52-fractional-knapsack)
   - 5.3 [Huffman Encoding](#53-huffman-encoding)
   - 5.4 [Minimum Spanning Tree (Kruskal & Prim)](#54-minimum-spanning-tree-kruskal--prim)
   - 5.5 [Dijkstra's Shortest Path](#55-dijkstras-shortest-path)
   - 5.6 [Job Scheduling with Deadlines](#56-job-scheduling-with-deadlines)
   - 5.7 [Coin Change (Greedy vs DP)](#57-coin-change-greedy-vs-dp)
6. [Implementation in Go, C, and Rust](#6-implementations)
7. [Greedy vs Dynamic Programming — The Key Difference](#7-greedy-vs-dynamic-programming)
8. [Common Mistakes & Pitfalls](#8-common-mistakes--pitfalls)
9. [Pattern Recognition Cheat Sheet](#9-pattern-recognition-cheat-sheet)
10. [Mental Models & Cognitive Strategies](#10-mental-models--cognitive-strategies)

---

## 1. What is a Greedy Algorithm?

### Simple Explanation

Imagine you are hiking and you always step on the **highest stone available** at each step, hoping it leads to the mountain top. That is greedy thinking — make the **locally optimal choice** at each step, hoping it produces a **globally optimal result**.

```
Global Optimum
     /\
    /  \
   / ?? \       <--- Greedy hopes local best = global best
  /______\
 STEP1 STEP2   <--- At each step, pick the best visible option
```

### Formal Definition

A **Greedy Algorithm** builds a solution step-by-step by always selecting the option that looks **best at that moment**, without reconsidering past choices.

**Key characteristics:**
- Makes **one decision at a time** — no backtracking
- Decision is **irrevocable** — once made, never undone
- Relies on a **greedy criterion** (what "best" means at each step)

---

## 2. The Mental Model — How to Think Greedy

### The "Regret-Free" Mental Model

Ask yourself: *"If I make this choice now, will I ever regret it?"*

If the answer is **never** — greedy works. If the answer is **maybe** — you need DP or backtracking.

```
PROBLEM
  |
  v
Can I sort or rank the choices?
  |
  +--YES--> Is there a local choice that is ALWAYS safe?
  |              |
  |         +----+----+
  |         |         |
  |        YES        NO
  |         |         |
  |       GREEDY     DP / Backtracking
  |
  +--NO --> Think harder about structure
```

### The Greedy Mindset — 4 Questions

Before writing any code, ask these 4 questions:

```
Q1: What is my "greedy criterion"?
    (What does "best right now" mean in this problem?)

Q2: What order should I process the items?
    (Sort by finish time? By ratio? By weight?)

Q3: Can I prove that my greedy choice never hurts me?
    (Exchange argument or induction)

Q4: What is the feasibility check?
    (Can I actually take this item/interval/job?)
```

---

## 3. Core Properties — When Does Greedy Work?

For Greedy to produce a correct solution, the problem must have TWO properties:

### Property 1: Greedy Choice Property

> A **globally optimal solution** can be reached by making a **locally optimal (greedy) choice** at each step.

**Plain English:** The best local decision leads to the best global outcome.

### Property 2: Optimal Substructure

> The **optimal solution** to the whole problem contains **optimal solutions** to its sub-problems.

**Plain English:** If you remove a greedy choice, the remaining problem is still solvable optimally with the same strategy.

```
OPTIMAL SUBSTRUCTURE CHECK:

Problem P has optimal solution S
  |
  v
Remove the first greedy choice C from S
  |
  v
Is the remaining solution S' still optimal for sub-problem P'?
  |
  +--YES --> Optimal Substructure holds --> Greedy MAY work
  +--NO  --> Greedy will NOT work
```

### When Greedy FAILS

```
GREEDY FAILURE EXAMPLES:

0/1 Knapsack:
  Items: (weight=5, value=10), (weight=3, value=7), (weight=3, value=6)
  Capacity: 6
  Greedy (by ratio): picks item1 (ratio=2), then can't fit anything else → value=10
  Optimal: picks item2 + item3 → value=13
  Greedy is WRONG here.

Coin Change (non-standard coins):
  Coins: [1, 3, 4], Target: 6
  Greedy: 4+1+1 = 3 coins
  Optimal: 3+3   = 2 coins
  Greedy is WRONG here.
```

---

## 4. The Greedy Choice Proof Technique

The standard way to prove greedy correctness is the **Exchange Argument**.

### Exchange Argument (Step-by-Step)

```
EXCHANGE ARGUMENT TEMPLATE:

1. Assume there exists an optimal solution OPT that differs from GREEDY.

2. Find the FIRST point where OPT differs from GREEDY.
   (OPT made a different choice at step k)

3. Show that you can SWAP OPT's choice at step k with GREEDY's choice
   WITHOUT making the solution worse.

4. Repeat until OPT looks exactly like GREEDY.

5. Conclusion: GREEDY is at least as good as OPT → GREEDY is optimal.
```

**Example: Activity Selection**

OPT keeps an activity with finish time 5. GREEDY keeps one with finish time 3.
If we swap: finish time 3 ≤ finish time 5, so we free up MORE time → never worse.
Therefore, greedy (pick earliest finish time) is optimal.

---

## 5. Classic Greedy Patterns

---

### 5.1 Activity Selection / Interval Scheduling

**Problem:** Given N activities with start and finish times, find the **maximum number of non-overlapping activities**.

**Vocabulary:**
- **Interval:** A range [start, end]
- **Overlap:** Two intervals [a,b] and [c,d] overlap if a < d AND c < b
- **Non-overlapping:** Intervals that don't share any time

**Greedy Insight:** Always pick the activity that **finishes earliest** — it leaves the most room for future activities.

**Why not pick the one that starts earliest?**
A job starting early but ending late blocks many future jobs.

**Why not pick the shortest job?**
A short job in the middle might block two non-overlapping long jobs.

```
ACTIVITY SELECTION DECISION FLOW:

Sort activities by FINISH TIME (ascending)
         |
         v
Initialize: last_finish = -INF, count = 0
         |
         v
For each activity [start, finish] in sorted order:
         |
         v
    start >= last_finish?
     /          \
   YES            NO
    |              |
  SELECT         SKIP
  this activity  this activity
  last_finish    (it overlaps)
  = finish
  count++
         |
         v
Return count (and selected activities)


EXAMPLE TRACE:
Activities: [1,4], [3,5], [0,6], [5,7], [3,8], [5,9], [6,10], [8,11], [8,12], [2,13], [12,14]
After sorting by finish: [1,4],[3,5],[0,6],[5,7],[3,8],[5,9],[6,10],[8,11],[8,12],[2,13],[12,14]

Step 1: [1,4]  → 1 >= -INF? YES → SELECT, last=4,  count=1
Step 2: [3,5]  → 3 >= 4?   NO  → SKIP
Step 3: [0,6]  → 0 >= 4?   NO  → SKIP
Step 4: [5,7]  → 5 >= 4?   YES → SELECT, last=7,  count=2
Step 5: [3,8]  → 3 >= 7?   NO  → SKIP
Step 6: [5,9]  → 5 >= 7?   NO  → SKIP
Step 7: [6,10] → 6 >= 7?   NO  → SKIP
Step 8: [8,11] → 8 >= 7?   YES → SELECT, last=11, count=3
Step 9: [8,12] → 8 >= 11?  NO  → SKIP
Step 10:[2,13] → 2 >= 11?  NO  → SKIP
Step 11:[12,14]→ 12>= 11?  YES → SELECT, last=14, count=4

Result: 4 activities selected: [1,4],[5,7],[8,11],[12,14]
```

**Time Complexity:** O(N log N) for sorting + O(N) scan = **O(N log N)**
**Space Complexity:** O(1) extra (or O(N) if storing result)

---

### 5.2 Fractional Knapsack

**Problem:** Given items with weights and values, and a knapsack of capacity W — maximize total value. You **can take fractions** of items.

**Vocabulary:**
- **Value-to-weight ratio (efficiency):** value / weight — how "worth it" each unit of weight is
- **Fraction:** You can take 0.5 of an item (unlike 0/1 Knapsack)

**Greedy Insight:** Always take the item with the **highest value/weight ratio** first. If it doesn't fit completely, take as much as you can.

```
FRACTIONAL KNAPSACK FLOW:

Compute ratio = value/weight for each item
         |
         v
Sort items by ratio (DESCENDING)
         |
         v
Initialize: remaining_capacity = W, total_value = 0
         |
         v
For each item (in sorted order):
         |
         v
    item.weight <= remaining_capacity?
         /                    \
       YES                     NO
        |                       |
   Take FULL item           Take FRACTION:
   total_value +=            fraction = remaining/item.weight
   item.value               total_value += fraction * item.value
   remaining -=             remaining = 0
   item.weight              STOP (knapsack full)


EXAMPLE:
Capacity W = 50
Items: (value=60, weight=10) → ratio=6.0
       (value=100,weight=20) → ratio=5.0
       (value=120,weight=30) → ratio=4.0

Sorted by ratio: ratio=6, ratio=5, ratio=4

Step 1: Take item(10,60) fully  → value=60,  remaining=40
Step 2: Take item(20,100) fully → value=160, remaining=20
Step 3: Take 20/30 of item(30,120) → value=160 + (2/3)*120 = 160+80 = 240, remaining=0

Total Value = 240 (OPTIMAL)
```

**Time Complexity:** O(N log N)
**Space Complexity:** O(1)

---

### 5.3 Huffman Encoding

**Problem:** Given characters and their frequencies, build a **prefix-free binary code** that minimizes total encoded length.

**Vocabulary:**
- **Prefix-free code:** No code is a prefix of another (so decoding is unambiguous)
- **Huffman Tree:** A binary tree where frequent characters get shorter codes
- **Min-Heap / Priority Queue:** A data structure where the smallest element is always accessible at the top

**Greedy Insight:** Always merge the **two least frequent** nodes. Rare characters get longer codes; frequent ones get shorter codes.

```
HUFFMAN ALGORITHM FLOW:

Input: characters with frequencies
e.g., a=5, b=9, c=12, d=13, e=16, f=45

Step 1: Create a leaf node for each character
        Insert all into a MIN-HEAP (priority = frequency)

        Heap: [a:5, b:9, c:12, d:13, e:16, f:45]

Step 2: WHILE heap has more than 1 node:
   a) Extract TWO minimum nodes (left, right)
   b) Create new internal node with:
      - frequency = left.freq + right.freq
      - left child = left
      - right child = right
   c) Insert new node back into heap

TRACE:
Round 1: Extract a:5, b:9 → merge → ab:14
         Heap: [c:12, d:13, ab:14, e:16, f:45]

Round 2: Extract c:12, d:13 → merge → cd:25
         Heap: [ab:14, e:16, cd:25, f:45]

Round 3: Extract ab:14, e:16 → merge → abe:30
         Heap: [cd:25, abe:30, f:45]

Round 4: Extract cd:25, abe:30 → merge → cdabe:55
         Heap: [f:45, cdabe:55]

Round 5: Extract f:45, cdabe:55 → merge → root:100

FINAL TREE:
         root:100
        /         \
      f:45       cdabe:55
                /         \
             cd:25        abe:30
            /    \        /    \
          c:12  d:13   ab:14   e:16
                       /  \
                     a:5  b:9

CODES (0=left, 1=right):
f    → 0          (1 bit,  freq=45) ← most frequent, shortest
c    → 100        (3 bits, freq=12)
d    → 101        (3 bits, freq=13)
a    → 1100       (4 bits, freq=5)
b    → 1101       (4 bits, freq=9)
e    → 111        (3 bits, freq=16)
```

**Time Complexity:** O(N log N) — N extractions, each O(log N)
**Space Complexity:** O(N)

---

### 5.4 Minimum Spanning Tree (Kruskal & Prim)

**Vocabulary:**
- **Graph:** A set of nodes (vertices) connected by edges
- **Spanning Tree:** A tree that connects ALL vertices of a graph using exactly (V-1) edges
- **MST (Minimum Spanning Tree):** A spanning tree with the smallest total edge weight
- **Cycle:** A path that starts and ends at the same vertex
- **Union-Find (Disjoint Set):** A data structure to track which component a node belongs to

#### Kruskal's Algorithm

**Greedy Insight:** Always add the **cheapest edge** that doesn't create a cycle.

```
KRUSKAL'S FLOW:

Sort ALL edges by weight (ascending)
         |
         v
Initialize: Union-Find structure (each node is its own component)
result = []
         |
         v
For each edge (u, v, weight) in sorted order:
         |
         v
    find(u) != find(v)?   (are u and v in DIFFERENT components?)
         /          \
       YES            NO
        |              |
   ADD edge to MST   SKIP (would create a cycle)
   union(u, v)
         |
         v
Continue until we have V-1 edges in MST


EXAMPLE:
Graph:
  A--4--B
  |  \  |
  2   8  5
  |     \|
  C--7--D

Edges sorted: (A,C,2), (A,B,4), (C,D,7), (A,D,8), (B,D,5)
              [wait: let me re-sort: (A,C,2),(A,B,4),(B,D,5),(C,D,7),(A,D,8)]

Step 1: (A,C,2) → A and C different? YES → ADD, union(A,C)
        MST: [A-C]
Step 2: (A,B,4) → A and B different? YES → ADD, union(A,B) (now A,B,C same set)
        MST: [A-C, A-B]
Step 3: (B,D,5) → B and D different? YES → ADD, union(B,D) (now all same set)
        MST: [A-C, A-B, B-D] → 3 edges = V-1 = DONE

MST total weight: 2+4+5 = 11
```

#### Prim's Algorithm

**Greedy Insight:** Always add the **cheapest edge that connects a new vertex** to the current spanning tree.

```
PRIM'S FLOW:

Start from any vertex (say vertex 0)
Mark it as visited
Insert all its edges into a MIN-HEAP
         |
         v
WHILE not all vertices visited:
         |
         v
   Extract min-weight edge (u, v, w) from heap
         |
         v
   Is v already visited?
        /        \
       YES        NO
        |          |
      SKIP       ADD to MST
                 Mark v as visited
                 Add all edges from v to heap
                 (that go to unvisited vertices)
         |
         v
Done when all V vertices are visited
```

**Kruskal vs Prim:**
```
Kruskal:
  - Better for SPARSE graphs (few edges)
  - Sorts edges globally
  - Uses Union-Find
  - Time: O(E log E)

Prim:
  - Better for DENSE graphs (many edges)
  - Grows from one vertex
  - Uses Min-Heap
  - Time: O(E log V) with binary heap
             O(E + V log V) with Fibonacci heap
```

---

### 5.5 Dijkstra's Shortest Path

**Problem:** Find the shortest path from a **source vertex** to all other vertices in a graph with **non-negative weights**.

**Vocabulary:**
- **Relaxation:** Updating the distance to a vertex if a shorter path is found
- **dist[v]:** Current known shortest distance from source to vertex v
- **Priority Queue:** A min-heap ordered by current distance

**Greedy Insight:** Always process the **unvisited vertex with the smallest current distance** first.

```
DIJKSTRA'S FLOW:

Initialize:
  dist[source] = 0
  dist[all others] = INFINITY
  Insert source into MIN-HEAP with priority 0
         |
         v
WHILE heap is not empty:
         |
         v
   Extract vertex u with minimum dist[u]
         |
         v
   For each neighbor v of u:
         |
         v
   new_dist = dist[u] + weight(u, v)
         |
         v
   new_dist < dist[v]?
        /         \
      YES           NO
       |             |
   UPDATE           SKIP
   dist[v] =
   new_dist
   Add v to heap
   with new priority


EXAMPLE:
Graph:
    A --1-- B --2-- C
    |       |
    4       3
    |       |
    D ------E
         1

Source = A
Initial: dist={A:0, B:INF, C:INF, D:INF, E:INF}
Heap: [(0,A)]

Step 1: Extract (0,A)
  Neighbor B: 0+1=1 < INF → dist[B]=1, heap: [(1,B)]
  Neighbor D: 0+4=4 < INF → dist[D]=4, heap: [(1,B),(4,D)]

Step 2: Extract (1,B)
  Neighbor A: 1+1=2 > 0  → skip
  Neighbor C: 1+2=3 < INF → dist[C]=3, heap: [(3,C),(4,D)]
  Neighbor E: 1+3=4 < INF → dist[E]=4, heap: [(3,C),(4,D),(4,E)]

Step 3: Extract (3,C) → no unvisited neighbors

Step 4: Extract (4,D) → no unvisited neighbors leading to improvement

Step 5: Extract (4,E)
  Check D: 4+1=5 > 4 → skip

Final distances: A=0, B=1, C=3, D=4, E=4
```

**Time Complexity:** O((V + E) log V) with binary heap
**Why Greedy works:** Once a vertex is extracted with distance d, no shorter path can be found later (because all weights are non-negative).

> ⚠️ **Dijkstra FAILS with negative weights.** Use Bellman-Ford instead.

---

### 5.6 Job Scheduling with Deadlines

**Problem:** Given N jobs, each with a profit and a deadline (must finish by this time unit), schedule to maximize profit. Each job takes 1 time unit.

**Greedy Insight:** Sort jobs by **profit (descending)**. For each job, assign it to the **latest available time slot** before its deadline.

```
JOB SCHEDULING FLOW:

Sort jobs by profit DESCENDING
         |
         v
Create time_slots array of size max_deadline (all empty)
         |
         v
For each job (in profit order):
         |
         v
Find the latest empty slot <= job.deadline
         |
         v
    Empty slot found?
        /       \
      YES         NO
       |           |
   ASSIGN job    SKIP job
   to that slot  (can't meet deadline)
         |
         v
Sum profits of all assigned jobs


EXAMPLE:
Jobs: (profit=100, deadline=2), (profit=19, deadline=1),
      (profit=27, deadline=2), (profit=25, deadline=1), (profit=15, deadline=3)

Sorted by profit: [100,d2], [27,d2], [25,d1], [19,d1], [15,d3]

Slots: [_, _, _]  (index 1, 2, 3)

Step 1: [100,d2] → check slot 2 (empty) → ASSIGN
        Slots: [_, 100, _]
Step 2: [27,d2]  → check slot 2 (taken), check slot 1 (empty) → ASSIGN
        Slots: [27, 100, _]
Step 3: [25,d1]  → check slot 1 (taken) → SKIP
Step 4: [19,d1]  → check slot 1 (taken) → SKIP
Step 5: [15,d3]  → check slot 3 (empty) → ASSIGN
        Slots: [27, 100, 15]

Total Profit = 27 + 100 + 15 = 142
```

---

### 5.7 Coin Change (Greedy vs DP)

This is the **most important example** showing when greedy fails.

```
COIN CHANGE — GREEDY:
Strategy: Always use the largest coin that fits.

Standard coins [25, 10, 5, 1] → Target 41:
  41 → use 25 → remaining 16
  16 → use 10 → remaining 6
   6 → use  5 → remaining 1
   1 → use  1 → remaining 0
  Result: 4 coins [25,10,5,1] ← CORRECT for this coin system

Non-standard coins [1, 3, 4] → Target 6:
  6 → use 4 → remaining 2
  2 → use 1 → remaining 1
  1 → use 1 → remaining 0
  Result: 3 coins [4,1,1] ← WRONG (2 coins [3,3] is optimal)

CONCLUSION:
Greedy works for standard denominations (where each coin is a multiple of smaller ones).
Greedy FAILS for arbitrary coin systems → use DP.
```

---

## 6. Implementations

---

### 6.1 Activity Selection

#### C Implementation

```c
#include <stdio.h>
#include <stdlib.h>

typedef struct {
    int start;
    int finish;
    int id;
} Activity;

/* Comparator for qsort: sort by finish time ascending */
int compare_by_finish(const void *a, const void *b) {
    Activity *act_a = (Activity *)a;
    Activity *act_b = (Activity *)b;
    return act_a->finish - act_b->finish;
}

/*
 * activity_selection: greedy interval scheduling
 * Returns number of selected activities.
 * selected[] is filled with indices of chosen activities.
 *
 * Time:  O(N log N)  — dominated by sort
 * Space: O(N)        — for selected array
 */
int activity_selection(Activity *acts, int n, int *selected) {
    /* Sort by finish time */
    qsort(acts, n, sizeof(Activity), compare_by_finish);

    int count = 0;
    int last_finish = -1;  /* last_finish = finish time of last selected activity */

    for (int i = 0; i < n; i++) {
        /*
         * Greedy choice: select activity if it starts
         * at or after the last selected activity finishes.
         * This is the "non-overlapping" condition.
         */
        if (acts[i].start >= last_finish) {
            selected[count++] = i;
            last_finish = acts[i].finish;
        }
    }
    return count;
}

int main(void) {
    Activity acts[] = {
        {1, 4, 1}, {3, 5, 2}, {0, 6, 3}, {5, 7, 4},
        {3, 8, 5}, {5, 9, 6}, {6, 10, 7}, {8, 11, 8},
        {8, 12, 9}, {2, 13, 10}, {12, 14, 11}
    };
    int n = sizeof(acts) / sizeof(acts[0]);
    int selected[20];

    int count = activity_selection(acts, n, selected);

    printf("Maximum activities: %d\n", count);
    printf("Selected (start, finish): ");
    for (int i = 0; i < count; i++) {
        printf("[%d,%d] ", acts[selected[i]].start, acts[selected[i]].finish);
    }
    printf("\n");

    return 0;
}
```

#### Go Implementation

```go
package main

import (
    "fmt"
    "sort"
)

// Activity represents a task with a start and finish time
type Activity struct {
    start, finish, id int
}

// activitySelection selects the maximum number of non-overlapping activities.
// Greedy criterion: always pick the activity with the earliest finish time.
//
// Time:  O(N log N) — sorting dominates
// Space: O(N)       — storing result
func activitySelection(acts []Activity) []Activity {
    // Sort by finish time (ascending)
    sort.Slice(acts, func(i, j int) bool {
        return acts[i].finish < acts[j].finish
    })

    selected := []Activity{}
    lastFinish := -1 // Tracks when the last selected activity ends

    for _, act := range acts {
        // Greedy check: does this activity start AFTER the last one ends?
        if act.start >= lastFinish {
            selected = append(selected, act)
            lastFinish = act.finish
        }
    }
    return selected
}

func main() {
    acts := []Activity{
        {1, 4, 1}, {3, 5, 2}, {0, 6, 3}, {5, 7, 4},
        {3, 8, 5}, {5, 9, 6}, {6, 10, 7}, {8, 11, 8},
        {8, 12, 9}, {2, 13, 10}, {12, 14, 11},
    }

    result := activitySelection(acts)

    fmt.Printf("Maximum activities: %d\n", len(result))
    fmt.Print("Selected [start, finish]: ")
    for _, act := range result {
        fmt.Printf("[%d,%d] ", act.start, act.finish)
    }
    fmt.Println()
}
```

#### Rust Implementation

```rust
/// Represents a single activity/interval
#[derive(Debug, Clone)]
struct Activity {
    start:  i32,
    finish: i32,
    id:     usize,
}

/// Greedy activity selection — picks maximum non-overlapping activities.
///
/// Strategy: Sort by finish time, greedily pick the earliest-finishing
/// activity that doesn't overlap with the last selected one.
///
/// # Time Complexity:  O(N log N)
/// # Space Complexity: O(N)
fn activity_selection(mut acts: Vec<Activity>) -> Vec<Activity> {
    // Sort activities by their finish time (ascending)
    acts.sort_unstable_by_key(|a| a.finish);

    let mut selected: Vec<Activity> = Vec::new();
    let mut last_finish = i32::MIN; // Finish time of last selected activity

    for act in acts {
        // Greedy condition: start time must be >= last selected finish time
        if act.start >= last_finish {
            last_finish = act.finish;
            selected.push(act);
        }
    }
    selected
}

fn main() {
    let activities = vec![
        Activity { start: 1,  finish: 4,  id: 1  },
        Activity { start: 3,  finish: 5,  id: 2  },
        Activity { start: 0,  finish: 6,  id: 3  },
        Activity { start: 5,  finish: 7,  id: 4  },
        Activity { start: 3,  finish: 8,  id: 5  },
        Activity { start: 5,  finish: 9,  id: 6  },
        Activity { start: 6,  finish: 10, id: 7  },
        Activity { start: 8,  finish: 11, id: 8  },
        Activity { start: 8,  finish: 12, id: 9  },
        Activity { start: 2,  finish: 13, id: 10 },
        Activity { start: 12, finish: 14, id: 11 },
    ];

    let result = activity_selection(activities);

    println!("Maximum activities: {}", result.len());
    print!("Selected [start, finish]: ");
    for act in &result {
        print!("[{},{}] ", act.start, act.finish);
    }
    println!();
}
```

---

### 6.2 Fractional Knapsack

#### C Implementation

```c
#include <stdio.h>
#include <stdlib.h>

typedef struct {
    double value;
    double weight;
    double ratio; /* value / weight */
} Item;

int compare_by_ratio(const void *a, const void *b) {
    Item *ia = (Item *)a;
    Item *ib = (Item *)b;
    /* Descending order: higher ratio first */
    if (ib->ratio > ia->ratio) return 1;
    if (ib->ratio < ia->ratio) return -1;
    return 0;
}

/*
 * fractional_knapsack:
 * Returns the maximum value achievable.
 *
 * Greedy: take items in order of value/weight ratio (highest first).
 * Take as much as fits; take a fraction if item doesn't fully fit.
 *
 * Time:  O(N log N)
 * Space: O(1)
 */
double fractional_knapsack(Item *items, int n, double capacity) {
    /* Pre-compute ratios */
    for (int i = 0; i < n; i++) {
        items[i].ratio = items[i].value / items[i].weight;
    }

    /* Sort by ratio descending */
    qsort(items, n, sizeof(Item), compare_by_ratio);

    double total_value = 0.0;
    double remaining   = capacity;

    for (int i = 0; i < n && remaining > 0; i++) {
        if (items[i].weight <= remaining) {
            /* Take the FULL item */
            total_value += items[i].value;
            remaining   -= items[i].weight;
        } else {
            /* Take a FRACTION of the item */
            double fraction = remaining / items[i].weight;
            total_value += fraction * items[i].value;
            remaining    = 0; /* knapsack is now full */
        }
    }
    return total_value;
}

int main(void) {
    Item items[] = {
        {60, 10, 0}, /* ratio = 6.0 */
        {100, 20, 0}, /* ratio = 5.0 */
        {120, 30, 0}  /* ratio = 4.0 */
    };
    int n = 3;
    double capacity = 50.0;

    double max_val = fractional_knapsack(items, n, capacity);
    printf("Maximum value: %.2f\n", max_val); /* Expected: 240.00 */

    return 0;
}
```

#### Go Implementation

```go
package main

import (
    "fmt"
    "sort"
)

// Item represents a knapsack item
type Item struct {
    value, weight float64
}

// fractionalKnapsack returns the maximum value for a given capacity.
//
// Greedy: process items by value/weight ratio (descending).
// Take fully if possible; take a fraction otherwise.
//
// Time:  O(N log N)
// Space: O(1)
func fractionalKnapsack(items []Item, capacity float64) float64 {
    // Sort by value/weight ratio descending
    sort.Slice(items, func(i, j int) bool {
        ratioI := items[i].value / items[i].weight
        ratioJ := items[j].value / items[j].weight
        return ratioI > ratioJ
    })

    totalValue := 0.0
    remaining := capacity

    for _, item := range items {
        if remaining <= 0 {
            break
        }
        if item.weight <= remaining {
            // Take the full item
            totalValue += item.value
            remaining -= item.weight
        } else {
            // Take only the fraction that fits
            fraction := remaining / item.weight
            totalValue += fraction * item.value
            remaining = 0
        }
    }
    return totalValue
}

func main() {
    items := []Item{
        {60, 10},   // ratio = 6.0
        {100, 20},  // ratio = 5.0
        {120, 30},  // ratio = 4.0
    }
    capacity := 50.0

    maxVal := fractionalKnapsack(items, capacity)
    fmt.Printf("Maximum value: %.2f\n", maxVal) // Expected: 240.00
}
```

#### Rust Implementation

```rust
/// Represents an item with value and weight
#[derive(Debug, Clone)]
struct Item {
    value:  f64,
    weight: f64,
}

/// Returns maximum value achievable with fractional knapsack.
///
/// Greedy strategy: sort by value/weight ratio (descending),
/// take items fully or fractionally until capacity is filled.
///
/// # Time Complexity:  O(N log N)
/// # Space Complexity: O(1)
fn fractional_knapsack(mut items: Vec<Item>, capacity: f64) -> f64 {
    // Sort by ratio descending — f64::partial_cmp handles float comparison
    items.sort_unstable_by(|a, b| {
        let ratio_a = a.value / a.weight;
        let ratio_b = b.value / b.weight;
        // unwrap_or(Equal) handles NaN edge case gracefully
        ratio_b.partial_cmp(&ratio_a).unwrap_or(std::cmp::Ordering::Equal)
    });

    let mut total_value = 0.0_f64;
    let mut remaining   = capacity;

    for item in items {
        if remaining <= 0.0 {
            break;
        }
        if item.weight <= remaining {
            // Take the full item
            total_value += item.value;
            remaining   -= item.weight;
        } else {
            // Take only what fits
            let fraction = remaining / item.weight;
            total_value += fraction * item.value;
            remaining    = 0.0;
        }
    }
    total_value
}

fn main() {
    let items = vec![
        Item { value: 60.0,  weight: 10.0 }, // ratio = 6.0
        Item { value: 100.0, weight: 20.0 }, // ratio = 5.0
        Item { value: 120.0, weight: 30.0 }, // ratio = 4.0
    ];
    let capacity = 50.0;

    let max_val = fractional_knapsack(items, capacity);
    println!("Maximum value: {:.2}", max_val); // Expected: 240.00
}
```

---

### 6.3 Dijkstra's Shortest Path

#### C Implementation (Adjacency Matrix, simple version)

```c
#include <stdio.h>
#include <limits.h>
#include <stdbool.h>

#define V 9 /* Number of vertices */

/*
 * min_distance: find the vertex with minimum dist[] value
 * among vertices not yet included in shortest path tree.
 *
 * This is the GREEDY CHOICE: always pick the closest unvisited vertex.
 */
int min_distance(int dist[], bool visited[]) {
    int min = INT_MAX, min_index = -1;
    for (int v = 0; v < V; v++) {
        if (!visited[v] && dist[v] <= min) {
            min       = dist[v];
            min_index = v;
        }
    }
    return min_index;
}

/*
 * dijkstra: finds shortest paths from src to all vertices.
 * Uses adjacency matrix graph[V][V].
 * 0 means no edge; > 0 means edge weight.
 *
 * Time:  O(V^2) — simple array version; O((V+E) log V) with heap
 * Space: O(V)
 */
void dijkstra(int graph[V][V], int src) {
    int  dist[V];      /* dist[i] = shortest distance from src to i */
    bool visited[V];   /* visited[i] = true if shortest path to i is finalized */

    /* Initialize: all distances infinite, none visited */
    for (int i = 0; i < V; i++) {
        dist[i]    = INT_MAX;
        visited[i] = false;
    }
    dist[src] = 0; /* Distance to source itself is 0 */

    for (int count = 0; count < V - 1; count++) {
        /* GREEDY CHOICE: pick closest unvisited vertex */
        int u = min_distance(dist, visited);
        if (u == -1) break; /* All remaining vertices are unreachable */

        visited[u] = true;

        /* RELAXATION: update distances of neighbors of u */
        for (int v = 0; v < V; v++) {
            /*
             * Relax edge (u,v) if:
             * 1. v is not yet visited
             * 2. there is an edge from u to v
             * 3. dist[u] is not infinite
             * 4. new path through u is shorter than current dist[v]
             */
            if (!visited[v] &&
                graph[u][v] != 0 &&
                dist[u] != INT_MAX &&
                dist[u] + graph[u][v] < dist[v])
            {
                dist[v] = dist[u] + graph[u][v];
            }
        }
    }

    /* Print results */
    printf("Vertex\tDistance from Source %d\n", src);
    for (int i = 0; i < V; i++) {
        printf("%d\t%d\n", i, dist[i]);
    }
}

int main(void) {
    /*
     * Example graph (adjacency matrix):
     * 0 means no edge.
     */
    int graph[V][V] = {
        {0, 4, 0, 0, 0, 0, 0, 8, 0},
        {4, 0, 8, 0, 0, 0, 0, 11, 0},
        {0, 8, 0, 7, 0, 4, 0, 0, 2},
        {0, 0, 7, 0, 9, 14, 0, 0, 0},
        {0, 0, 0, 9, 0, 10, 0, 0, 0},
        {0, 0, 4, 14, 10, 0, 2, 0, 0},
        {0, 0, 0, 0, 0, 2, 0, 1, 6},
        {8, 11, 0, 0, 0, 0, 1, 0, 7},
        {0, 0, 2, 0, 0, 0, 6, 7, 0}
    };

    dijkstra(graph, 0);
    return 0;
}
```

#### Go Implementation (with Min-Heap)

```go
package main

import (
    "container/heap"
    "fmt"
    "math"
)

// ---- Min-Heap for (distance, vertex) pairs ----

// Edge represents a weighted graph edge
type Edge struct {
    to, weight int
}

// HeapItem holds a vertex and its current known distance
type HeapItem struct {
    vertex, dist int
}

// PriorityQueue implements heap.Interface for HeapItem
type PriorityQueue []HeapItem

func (pq PriorityQueue) Len() int            { return len(pq) }
func (pq PriorityQueue) Less(i, j int) bool  { return pq[i].dist < pq[j].dist }
func (pq PriorityQueue) Swap(i, j int)       { pq[i], pq[j] = pq[j], pq[i] }
func (pq *PriorityQueue) Push(x interface{}) { *pq = append(*pq, x.(HeapItem)) }
func (pq *PriorityQueue) Pop() interface{} {
    old := *pq
    n := len(old)
    item := old[n-1]
    *pq = old[:n-1]
    return item
}

// ---- Dijkstra ----

// dijkstra returns shortest distances from src to all vertices.
//
// graph is an adjacency list: graph[u] = list of {to, weight} edges.
//
// Greedy choice: always process the unvisited vertex with smallest dist.
//
// Time:  O((V + E) log V)
// Space: O(V + E)
func dijkstra(graph [][]Edge, src int) []int {
    n := len(graph)
    dist := make([]int, n)
    for i := range dist {
        dist[i] = math.MaxInt64 // Initialize all distances to "infinity"
    }
    dist[src] = 0

    pq := &PriorityQueue{{vertex: src, dist: 0}}
    heap.Init(pq)

    for pq.Len() > 0 {
        // GREEDY CHOICE: extract the vertex with minimum current distance
        item := heap.Pop(pq).(HeapItem)
        u := item.vertex

        // If this entry is stale (we've already found a better path), skip it
        // This is the "lazy deletion" optimization for Dijkstra with a heap
        if item.dist > dist[u] {
            continue
        }

        // RELAXATION: update distances of all neighbors of u
        for _, edge := range graph[u] {
            newDist := dist[u] + edge.weight
            if newDist < dist[edge.to] {
                dist[edge.to] = newDist
                heap.Push(pq, HeapItem{vertex: edge.to, dist: newDist})
            }
        }
    }
    return dist
}

func main() {
    // Build adjacency list for the example graph
    // 9 vertices, 0-indexed
    graph := make([][]Edge, 9)
    addEdge := func(u, v, w int) {
        graph[u] = append(graph[u], Edge{v, w})
        graph[v] = append(graph[v], Edge{u, w}) // undirected
    }

    addEdge(0, 1, 4)
    addEdge(0, 7, 8)
    addEdge(1, 2, 8)
    addEdge(1, 7, 11)
    addEdge(2, 3, 7)
    addEdge(2, 5, 4)
    addEdge(2, 8, 2)
    addEdge(3, 4, 9)
    addEdge(3, 5, 14)
    addEdge(4, 5, 10)
    addEdge(5, 6, 2)
    addEdge(6, 7, 1)
    addEdge(6, 8, 6)
    addEdge(7, 8, 7)

    dist := dijkstra(graph, 0)

    fmt.Println("Vertex\tDistance from Source 0")
    for i, d := range dist {
        fmt.Printf("%d\t%d\n", i, d)
    }
}
```

#### Rust Implementation (with BinaryHeap)

```rust
use std::collections::BinaryHeap;
use std::cmp::Reverse;

/// Weighted edge in adjacency list
#[derive(Debug, Clone)]
struct Edge {
    to:     usize,
    weight: u64,
}

/// Dijkstra's algorithm — returns shortest distances from src to all vertices.
///
/// Uses a min-heap (BinaryHeap<Reverse<...>>) for greedy selection.
/// Rust's BinaryHeap is a MAX-heap by default, so we wrap with Reverse
/// to turn it into a min-heap.
///
/// # Time Complexity:  O((V + E) log V)
/// # Space Complexity: O(V + E)
fn dijkstra(graph: &[Vec<Edge>], src: usize) -> Vec<u64> {
    let n = graph.len();
    let mut dist = vec![u64::MAX; n]; // u64::MAX acts as "infinity"
    dist[src] = 0;

    // Min-heap: (distance, vertex)
    // Reverse wraps the tuple so the SMALLEST distance has highest priority
    let mut heap: BinaryHeap<Reverse<(u64, usize)>> = BinaryHeap::new();
    heap.push(Reverse((0, src)));

    while let Some(Reverse((d, u))) = heap.pop() {
        // Greedy choice: process the vertex with minimum current distance

        // Stale entry check: if we've already found a better path, skip
        if d > dist[u] {
            continue;
        }

        // Relaxation: update neighbors
        for edge in &graph[u] {
            let new_dist = dist[u].saturating_add(edge.weight);
            // saturating_add prevents overflow when dist[u] = u64::MAX
            if new_dist < dist[edge.to] {
                dist[edge.to] = new_dist;
                heap.push(Reverse((new_dist, edge.to)));
            }
        }
    }
    dist
}

fn main() {
    let n = 9;
    let mut graph: Vec<Vec<Edge>> = vec![vec![]; n];

    // Helper closure to add undirected edge
    let add_edge = |g: &mut Vec<Vec<Edge>>, u: usize, v: usize, w: u64| {
        g[u].push(Edge { to: v, weight: w });
        g[v].push(Edge { to: u, weight: w });
    };

    add_edge(&mut graph, 0, 1, 4);
    add_edge(&mut graph, 0, 7, 8);
    add_edge(&mut graph, 1, 2, 8);
    add_edge(&mut graph, 1, 7, 11);
    add_edge(&mut graph, 2, 3, 7);
    add_edge(&mut graph, 2, 5, 4);
    add_edge(&mut graph, 2, 8, 2);
    add_edge(&mut graph, 3, 4, 9);
    add_edge(&mut graph, 3, 5, 14);
    add_edge(&mut graph, 4, 5, 10);
    add_edge(&mut graph, 5, 6, 2);
    add_edge(&mut graph, 6, 7, 1);
    add_edge(&mut graph, 6, 8, 6);
    add_edge(&mut graph, 7, 8, 7);

    let dist = dijkstra(&graph, 0);

    println!("Vertex\tDistance from Source 0");
    for (i, &d) in dist.iter().enumerate() {
        println!("{}\t{}", i, d);
    }
}
```

---

### 6.4 Kruskal's MST

#### Go Implementation (with Union-Find)

```go
package main

import "fmt"

// Edge in the graph
type Edge struct {
    u, v, weight int
}

// UnionFind (Disjoint Set Union) — tracks connected components.
// Two key operations:
//   Find(x): returns the "root" representative of x's component
//   Union(x, y): merges the components of x and y
type UnionFind struct {
    parent []int
    rank   []int // rank = approximate tree height, for union by rank
}

func NewUnionFind(n int) *UnionFind {
    parent := make([]int, n)
    rank   := make([]int, n)
    for i := range parent {
        parent[i] = i // Each node is initially its own parent
    }
    return &UnionFind{parent, rank}
}

// Find with path compression:
// Flattens the tree so future finds are faster (amortized O(α(N)) ≈ O(1))
func (uf *UnionFind) Find(x int) int {
    if uf.parent[x] != x {
        uf.parent[x] = uf.Find(uf.parent[x]) // Path compression
    }
    return uf.parent[x]
}

// Union by rank: attach smaller tree under larger tree to keep tree shallow
func (uf *UnionFind) Union(x, y int) bool {
    rx, ry := uf.Find(x), uf.Find(y)
    if rx == ry {
        return false // Already in same component — edge would create cycle
    }
    if uf.rank[rx] < uf.rank[ry] {
        uf.parent[rx] = ry
    } else if uf.rank[rx] > uf.rank[ry] {
        uf.parent[ry] = rx
    } else {
        uf.parent[ry] = rx
        uf.rank[rx]++
    }
    return true
}

// kruskal builds the MST using Kruskal's greedy algorithm.
//
// Greedy: always add the cheapest edge that doesn't form a cycle.
//
// Time:  O(E log E) — sorting edges dominates
// Space: O(V) — union-find structure
func kruskal(n int, edges []Edge) ([]Edge, int) {
    // Sort edges by weight ascending
    // Using simple insertion sort for clarity; use sort.Slice in production
    for i := 1; i < len(edges); i++ {
        for j := i; j > 0 && edges[j].weight < edges[j-1].weight; j-- {
            edges[j], edges[j-1] = edges[j-1], edges[j]
        }
    }

    uf  := NewUnionFind(n)
    mst := []Edge{}
    totalWeight := 0

    for _, e := range edges {
        // Greedy choice: add edge if it doesn't form a cycle
        if uf.Union(e.u, e.v) {
            mst = append(mst, e)
            totalWeight += e.weight
            if len(mst) == n-1 {
                break // MST complete: exactly V-1 edges
            }
        }
    }
    return mst, totalWeight
}

func main() {
    // Graph with 4 vertices (0-3)
    edges := []Edge{
        {0, 1, 10}, {0, 2, 6}, {0, 3, 5},
        {1, 3, 15}, {2, 3, 4},
    }
    n := 4

    mst, total := kruskal(n, edges)

    fmt.Printf("MST Total Weight: %d\n", total)
    fmt.Println("MST Edges:")
    for _, e := range mst {
        fmt.Printf("  %d -- %d  (weight %d)\n", e.u, e.v, e.weight)
    }
}
```

---

## 7. Greedy vs Dynamic Programming

This is one of the **most important distinctions** in DSA.

```
COMPARISON TABLE:
+------------------+-------------------------+---------------------------+
| Property         | Greedy                  | Dynamic Programming       |
+------------------+-------------------------+---------------------------+
| Choices          | One irrevocable choice  | Considers all choices     |
|                  | per step                | and memoizes them         |
+------------------+-------------------------+---------------------------+
| Backtracking     | Never                   | Implicitly (via table)    |
+------------------+-------------------------+---------------------------+
| When correct     | Greedy choice property  | Optimal substructure only |
|                  | + Optimal substructure  | (no greedy choice needed) |
+------------------+-------------------------+---------------------------+
| Speed            | Usually faster          | Usually slower            |
|                  | O(N log N) typical      | O(N^2) or O(N*W) typical  |
+------------------+-------------------------+---------------------------+
| Memory           | Usually O(1) or O(N)    | Usually O(N^2) or O(N*W)  |
+------------------+-------------------------+---------------------------+
| Examples         | Activity Selection,     | 0/1 Knapsack,             |
|                  | Huffman, Dijkstra,      | Coin Change (general),    |
|                  | Kruskal, Prim,          | LCS, Edit Distance,       |
|                  | Fractional Knapsack     | Matrix Chain              |
+------------------+-------------------------+---------------------------+

THE KEY QUESTION TO DISTINGUISH THEM:
"Does my current choice depend on future choices I haven't made yet?"

YES → DP (you need to explore multiple paths)
NO  → Greedy might work (local choice is globally safe)
```

### Decision Tree: Greedy or DP?

```
Can the problem be decomposed into sub-problems?
  |
  YES
  |
  v
Do sub-problems have overlapping solutions?
  |
  +--YES --> DP
  |
  +--NO  --> Is there a greedy choice that is always safe?
                   |
             +-----+-----+
             |           |
            YES          NO
             |           |
           GREEDY    Divide & Conquer
                     or Backtracking
```

---

## 8. Common Mistakes & Pitfalls

### Mistake 1: Applying Greedy Without Proof

```
WRONG THINKING: "This problem involves optimization, so greedy works."

CORRECT THINKING:
  1. Identify the greedy criterion.
  2. Try to find a counter-example.
  3. If no counter-example found, try to sketch an exchange argument proof.
  4. Only then code.
```

### Mistake 2: Wrong Greedy Criterion

```
Interval Scheduling:
  WRONG: Sort by start time
         Counter-example: [0,100] starts first but blocks everything
  WRONG: Sort by duration
         Counter-example: A short [5,6] might block two long non-overlapping jobs
  CORRECT: Sort by FINISH TIME
```

### Mistake 3: Forgetting to Sort

```
Greedy almost always requires SORTING first.
Ask yourself: "In what order should I process items for my greedy criterion to work?"
```

### Mistake 4: Applying Greedy to 0/1 Problems

```
If you CANNOT take fractions (0/1 Knapsack, Coin Change with arbitrary coins),
greedy is usually WRONG. The "all-or-nothing" constraint destroys the greedy choice property.
```

---

## 9. Pattern Recognition Cheat Sheet

```
PROBLEM TYPE                    GREEDY CRITERION            SORT BY
---------------------------------------------------------------------------
Interval Scheduling             Earliest finish time        Finish time ASC
Interval Point Cover            Earliest finish time        Finish time ASC
Weighted Job Scheduling         Latest deadline first       Deadline ASC
Task Sequencing (minimize wait) Shortest job first          Duration ASC
Fractional Knapsack             Highest value/weight        Ratio DESC
Huffman Coding                  Merge two smallest          Priority Queue (min)
Minimum Spanning Tree           Cheapest safe edge          Weight ASC (Kruskal)
Shortest Path (non-neg weights) Closest unvisited vertex    Distance (min-heap)
Gas Station Problem             Greedily extend range       Left to right
Jump Game                       Max reachable position      Left to right
Candy Distribution              Local rules, two passes     Position
```

### Quick Identification Keywords

```
Problem says...                         Think...
---------------------------------------------------
"maximum number of non-overlapping"  → Interval greedy (sort by finish)
"minimum spanning"                   → Kruskal or Prim
"shortest path"                      → Dijkstra (non-neg) / Bellman-Ford (neg)
"optimal prefix-free encoding"       → Huffman
"maximize value, can take fractions" → Fractional Knapsack
"minimize total cost of merging"     → Huffman-like (min-heap merging)
"can you always reach the end"       → Jump Game greedy
```

---

## 10. Mental Models & Cognitive Strategies

### The "No-Regret" Mental Model

> At each step, can I make a choice that I will **never need to undo**?

If yes → greedy. If the choice might need to be revised → DP or backtracking.

### The "Sorting Unlocks Structure" Insight

Most greedy problems become obvious **after sorting**. The sort imposes an order that makes the locally optimal choice clearly visible. Train yourself to ask: *"What property should I sort by?"* as a first reflex.

### The "Exchange Argument" Proof Habit

Develop the mental habit of testing your greedy criterion like this:
> "Suppose someone else made a different choice at step k. Can I always swap their choice for mine and do at least as well?"

If yes → your greedy criterion is correct.

### Deliberate Practice Strategy for Greedy

```
WEEK 1: Master the core 5
  - Activity Selection
  - Fractional Knapsack
  - Huffman Coding
  - Kruskal's MST
  - Dijkstra's SSSP

WEEK 2: Practice identification
  - For 10 problems, ONLY decide: Greedy? DP? Neither?
  - Do NOT code yet. Just prove or disprove greedily.

WEEK 3: Exchange arguments
  - For 5 greedy problems, write out the full correctness proof.
  - This builds deep intuition that survives interview pressure.

WEEK 4: Hybrid problems
  - Problems that look greedy but need DP (or vice versa).
  - Build the ability to switch strategies mid-solve.
```

### Cognitive Principle: Chunking

When you see an interval scheduling problem, your brain should fire a **single chunk**: "sort by finish time, scan left to right." Build these chunks through deliberate repetition. After 20 interval problems, you won't think — you'll just *see* the solution structure.

### The "Simplest Possible Counter-Example" Test

Before committing to greedy, spend 2 minutes trying to break it:
- 2-item examples
- Equal values
- One extreme item
- Items that "look" greedy-optimal but lead to sub-optimal outcomes

If you can't break it in 2 minutes AND the exchange argument sketch works → code with confidence.

---

## Summary: The Greedy Algorithm Blueprint

```
GREEDY BLUEPRINT (memorize this):

STEP 1 — IDENTIFY the optimization goal
         (maximize? minimize? count?)

STEP 2 — DEFINE the greedy criterion
         (what does "locally best" mean for THIS problem?)

STEP 3 — PROVE (even informally) the greedy choice property
         (exchange argument sketch)

STEP 4 — SORT if needed
         (most greedy problems require an initial sort)

STEP 5 — SCAN + SELECT
         (iterate, apply feasibility check, make greedy choice)

STEP 6 — VERIFY on small examples by hand
         (trace through 3-5 item inputs manually)

STEP 7 — ANALYZE complexity
         (usually O(N log N) from sort + O(N) scan)
```

---

*"Greedy algorithms are not about being reckless — they are about being so deeply insightful that you know, at every step, which local action leads inevitably to the global optimum."*

---

Now let me create the comprehensive Greedy guide as a `.md` file:Your comprehensive Greedy Algorithms guide is ready. Here's what's packed inside:

**Structure of the guide:**

- **What Greedy Is** — explained with a hiking analogy, zero jargon
- **The Mental Model** — 4 questions to ask before writing any greedy code, with a full decision flowchart
- **Core Properties** — Greedy Choice Property + Optimal Substructure, with clear failure examples (0/1 Knapsack, Coin Change)
- **Proof Technique** — The Exchange Argument as a reusable template
- **7 Classic Problems** with full ASCII trace walkthroughs:
  - Activity Selection, Fractional Knapsack, Huffman Encoding, Kruskal's MST, Prim's MST, Dijkstra, Job Scheduling, Coin Change (with the DP failure case explained)
- **Implementations in C, Go, and Rust** — idiomatic, commented, complexity-annotated
- **Greedy vs DP** — full comparison table + decision tree
- **Pitfalls** — the 4 most common mistakes
- **Pattern Recognition Cheat Sheet** — instant lookup for greedy criterion by problem type
- **Cognitive Blueprint** — the 7-step greedy template + 4-week deliberate practice plan

**Key insight to internalize first:** Almost every greedy problem reduces to → *sort by the right criterion → scan → pick the locally safe choice*. The hard part is proving which criterion is "right." The Exchange Argument is your weapon for that.