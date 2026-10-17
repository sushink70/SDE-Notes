# Topological Sort via DFS — The Complete Guide

> Goal: build a *mental model* so solid that you can re-derive the algorithm, its proof,
> its edge cases and its production-grade implementation from first principles.
> Implementations: **C**, **Go**, **Rust**. All diagrams are plain ASCII.

**Source context.** The lecture slides you linked (Kleinberg & Tardos, *Algorithm Design*,
Ch. 3, slides by Kevin Wayne) define DAGs and topological order, and prove the
**source-removal** algorithm (repeatedly delete a node with no incoming edges, tracked with
`count(w)` and a set `S`) runs in `O(m + n)`. This guide covers the **DFS-based** algorithm
(the one in CLRS §22.4 and Sedgewick), and compares it with source-removal (Kahn's algorithm).

---

## Table of Contents

1. [The problem in one picture](#1-the-problem-in-one-picture)
2. [Prerequisites: graphs, digraphs, DAGs](#2-prerequisites)
3. [Topological order: precise definition and properties](#3-topological-order)
4. [DFS fundamentals (the machinery you must own)](#4-dfs-fundamentals)
5. [The key insight: finish times](#5-the-key-insight-finish-times)
6. [The algorithm](#6-the-algorithm)
7. [Full worked trace](#7-full-worked-trace)
8. [Proofs of correctness](#8-proofs-of-correctness)
9. [Complexity analysis](#9-complexity-analysis)
10. [Cycle detection and cycle extraction](#10-cycle-detection-and-extraction)
11. [Recursive vs iterative DFS (and stack overflow)](#11-recursive-vs-iterative)
12. [Edge direction conventions and the "reverse" question](#12-edge-direction-conventions)
13. [DFS vs Kahn (source removal)](#13-dfs-vs-kahn)
14. [Real-world architecture (ASCII)](#14-real-world-architecture)
15. [Implementation in C](#15-c)
16. [Implementation in Go](#16-go)
17. [Implementation in Rust](#17-rust)
18. [Applications built on top of topological order](#18-applications-built-on-top-of-topological-order)
19. [Variants and extensions](#19-variants-and-extensions)
20. [Edge cases and pitfalls checklist](#20-edge-cases-and-pitfalls-checklist)
21. [Testing strategy](#21-testing-strategy)
22. [Practice problems](#22-practice-problems)
23. [Mental-model cheat sheet](#23-mental-model-cheat-sheet)

---

## 1. The problem in one picture

You have tasks with **"must come before"** constraints. You want a linear order that respects
all of them.

```
 Getting dressed.  Edge A ──► B means "A must happen before B".

   underwear ───► trousers ───► belt ───┐
                     │                   ▼
                     └────► shoes      jacket
                              ▲           ▲
   socks ─────────────────────┘           │
   shirt ───────► tie ────────────────────┘

 One valid line-up:  underwear, socks, shirt, trousers, tie, belt, shoes, jacket
```

A **topological order** is any line-up of all nodes in which every arrow points *left to right*.

```
 A small DAG (used for the worked trace in section 7):

     5 ───► 2 ───► 3 ───► 1
     │                    ▲
     │                    │
     └───► 0 ◄─── 4 ──────┘

 One topological order, with every edge checked:

   position:   0   1   2   3   4   5
   node:       5   4   2   3   1   0

   5->2 (0<2) ✔   2->3 (2<3) ✔   3->1 (3<4) ✔
   5->0 (0<5) ✔   4->0 (1<5) ✔   4->1 (1<4) ✔
```

Key facts to hold in your head from the start:

* It exists **if and only if the graph has no directed cycle** (it is a DAG).
* It is generally **not unique**.
* DFS finds it in **`O(V + E)`** by emitting each node at the moment it is *finished*, then reversing.

---

## 2. Prerequisites

### 2.1 Directed graph

`G = (V, E)`, where an edge `(u, v)` **leaves** `u` and **enters** `v`. Orientation matters
(slides: "orientation of edges is crucial"). `n = |V|`, `m = |E|`.

### 2.2 Terminology you will use constantly

| Term | Meaning |
|---|---|
| out-neighbors of `u` | nodes `v` with edge `u -> v` |
| in-degree / out-degree | number of entering / leaving edges |
| source | node with in-degree 0 |
| sink | node with out-degree 0 |
| path | sequence `v1, v2, ..., vk`, each consecutive pair is an edge |
| directed cycle | a path with `v1 = vk` (and `k >= 2` in the slides' notation) |
| self-loop | edge `u -> u` (a cycle of length 1) |
| DAG | directed graph with no directed cycle |
| reachable | `v` is reachable from `u` if a path `u ~> v` exists |

### 2.3 Representations (and why DFS wants adjacency lists)

```
 Edges: 0->1, 0->2, 1->3, 2->3

 Adjacency MATRIX (n x n)               Adjacency LIST (array of lists)
      0 1 2 3                            idx   list
   0 [0 1 1 0]                            0  -> [1, 2]
   1 [0 0 0 1]                            1  -> [3]
   2 [0 0 0 1]                            2  -> [3]
   3 [0 0 0 0]                            3  -> []

 space   Theta(n^2)                      space   Theta(n + m)
 edge?   Theta(1)                        edge?   O(out-degree)
 scan all out-edges of u: Theta(n)       scan all out-edges of u: Theta(out-degree)
 DFS total: Theta(n^2)                   DFS total: Theta(n + m)
```

DFS touches *every out-edge of every node exactly once*. With adjacency lists that is
`sum(out-degree) = m` work, giving the `O(n + m)` bound. With a matrix, finding the out-edges of
a node costs `Theta(n)` regardless, so the total is `Theta(n^2)`.

### 2.4 Memory layouts you will see in the code

```
 C  (forward-star / "linked arrays")        Go  ([][]int)                 Rust (Vec<Vec<usize>>)

 head[]   tail[]    to[]   next[]            adj ──► [ ptr,len,cap ]       adj ──► [ ptr,len,cap ]
 ┌───┐   ┌───┐     edge: 0  1  2  3          [0] ─► [1,2]                  [0] ─► [1,2]
 │ 0 │   │ 1 │      to   1  2  3  3          [1] ─► [3]                    [1] ─► [3]
 │ 2 │   │ 3 │     next  1 -1  -1 -1         [2] ─► [3]                    [2] ─► [3]
 │...│   │...│                               [3] ─► nil                    [3] ─► []
 └───┘   └───┘     node 0: head=0 -> e0 -> e1 -> end
 (index = node)     node 1: head=2 -> e2 -> end
```

---

## 3. Topological order

### 3.1 Definition (from the slides)

A **topological order** of a directed graph `G = (V, E)` is an ordering of its nodes
`v1, v2, ..., vn` such that for **every edge `(vi, vj)` we have `i < j`**.

### 3.2 Three foundational facts

1. **Topological order exists ⇒ graph is a DAG.**
   Suppose a cycle exists. Let `vi` be its lowest-indexed node and `vj` the node just before it
   on the cycle, so `(vj, vi)` is an edge. Lowest index gives `i < j`, but the edge demands
   `j < i`. Contradiction. (This is the slides' proof.)

2. **Graph is a DAG ⇒ some node has in-degree 0.**
   If every node had an entering edge, walk *backwards* edge by edge; after at most `n+1` steps
   you must repeat a node, which closes a cycle. (Slides' proof.) Symmetrically, a DAG always
   has a node with out-degree 0 (a sink). **The DFS algorithm leans on sinks**; Kahn's leans on sources.

3. **Graph is a DAG ⇒ topological order exists.**
   Induction: remove a source, the rest is still a DAG, order it, put the source first.
   (Slides' proof, which *is* Kahn's algorithm.) The DFS algorithm is a different constructive
   proof of the same statement (see section 8).

Together: **DAG ⇔ has a topological order.**

### 3.3 Non-uniqueness and counting

```
   a ──► c
   b ──► c        valid orders:  a b c   and   b a c
```

* A DAG has a **unique** topological order **iff** consecutive nodes in some order are all
  joined by edges (i.e. there is a Hamiltonian path).
* The *number* of topological orders can be as large as `n!` (no edges at all), and counting them
  is `#P`-complete in general. You almost never need it; you need *one* valid order.

### 3.4 Topological order vs "levels"

A topological order is a **line**, not a schedule. If tasks can run in parallel you often want
**layers** (all nodes whose dependencies are done run together). Layers are computed as
`level(v) = 1 + max(level(u) for u -> v)`, which is a DP *over* a topological order
(section 18).

---

## 4. DFS fundamentals

Everything in the proof and every bug you will ever hit with this algorithm comes from DFS
mechanics, so we spell them out.

### 4.1 The three-color state machine

```
                discover u                 finish u
   ┌───────┐  ─────────────►  ┌───────┐  ─────────────►  ┌───────┐
   │ WHITE │                  │ GRAY  │                  │ BLACK │
   │ unseen│                  │ on the│                  │ done: │
   └───────┘                  │ stack │                  │ all   │
                              └───────┘                  │ below │
                                                         │ done  │
                                                         └───────┘
```

* **WHITE** — never visited.
* **GRAY** — visited, currently *in progress*: it is on the recursion stack (an ancestor of the node being processed).
* **BLACK** — finished: it and everything reachable from it that was available are completely explored.

**Crucial invariant:** *the GRAY nodes form exactly one directed path*, the recursion stack, from
the current DFS root down to the current node. This is why cycle extraction is just "slice the stack".

### 4.2 Discovery and finish times

A global clock increments on every discover and every finish:

```
 dfs(u):
     disc[u] = ++clock          # u turns GRAY
     for v in out(u):
         if v is WHITE: dfs(v)
     fin[u]  = ++clock          # u turns BLACK
```

### 4.3 DFS forest

A full DFS (restart from every still-WHITE node) produces a **forest** of DFS trees. The outer
loop is mandatory; a single DFS from one node only reaches what is reachable from it.

### 4.4 Parenthesis theorem

For any two nodes `u`, `v`, exactly one of these holds:

```
  (a) intervals disjoint:        [disc u, fin u]   [disc v, fin v]      neither is a descendant of the other
  (b) v nested inside u:         disc u < disc v < fin v < fin u        v is a descendant of u
  (c) u nested inside v:         disc v < disc u < fin u < fin v        u is a descendant of v
```

Intervals never *partially* overlap, exactly like balanced parentheses `( ( ) ) ( )`.

### 4.5 White-path theorem

`v` becomes a descendant of `u` in the DFS forest **iff**, at the moment `u` is discovered,
there is a path `u ~> v` consisting solely of WHITE nodes.

### 4.6 The four edge types

When DFS examines edge `(u, v)`, the **color of `v`** tells you the type:

| Color of `v` when examined | Edge type | Meaning |
|---|---|---|
| WHITE | **tree edge** | `v` is discovered through `u` |
| GRAY | **back edge** | `v` is an ancestor of `u` (or `u` itself): **closes a cycle** |
| BLACK, `disc[u] < disc[v]` | **forward edge** | `v` is a (finished) descendant of `u`, reached by a shortcut |
| BLACK, `disc[u] > disc[v]` | **cross edge** | `v` is in an earlier finished subtree / another tree |

Illustration (graph: `A->B, B->C, A->C, C->A, D->C`):

```
 Edges:  A->B tree     B->C tree     A->C forward     C->A back     D->C cross

   DFS tree:   A            (back edge C->A points UP to an ancestor)
               │
               B            (forward edge A->C skips B, points DOWN to a descendant)
               │
               C            (cross edge D->C goes to a different, already finished tree)

   D (separate root)

 Timeline (each unit = one clock tick):
 node 1  2  3  4  5  6  7  8
 A    [──────────────]
 B       [────────]
 C          [──]
 D                      [──]

 C->A : when examined (t=3..4) A is GRAY (A's interval still open)   -> BACK edge
 A->C : when examined (t=5..6) C is BLACK, disc[A] < disc[C]          -> FORWARD edge
 D->C : when examined (t=7..8) C is BLACK, disc[D] > disc[C]          -> CROSS edge
```

**For topological sort you only care about one thing:** *is there any GRAY neighbor?* If yes,
there is a cycle. BLACK neighbors (forward or cross) are always safe and need no action.

---

## 5. The key insight: finish times

> **In a DAG, for every edge `u -> v`, `fin[v] < fin[u]`.**
> So sorting nodes by *decreasing finish time* puts `u` before `v` on every edge: that is a topological order.

Intuition ("sign-off" model): a node can only **sign off (finish)** after every node it points to
has signed off. So the sign-off sequence lists each node *after* all its out-neighbors. That is
exactly the **reverse** of what we want. Reverse it, and every arrow points rightwards.

```
 Sign-off (post-order):   0  1  3  2  4  5          <- each node after everything it points to
 Reverse:                 5  4  2  3  1  0          <- each node before everything it points to  ✔
```

Mnemonic: **"Finish last = go first."**

---

## 6. The algorithm

### 6.1 Pseudocode

```
TOPO_SORT_DFS(G):
    color[v] = WHITE for all v
    out = empty list                       # post-order
    for each node s in V:                  # outer loop: covers disconnected parts
        if color[s] == WHITE:
            if not VISIT(s): return CYCLE
    return reverse(out)

VISIT(u):
    color[u] = GRAY
    for each v in adj[u]:
        if color[v] == WHITE:
            if not VISIT(v): return false
        elif color[v] == GRAY:             # back edge => directed cycle
            return false
        # BLACK: forward/cross edge -> nothing to do
    color[u] = BLACK
    append u to out                        # <- post-order position
    return true
```

### 6.2 Why each line exists

| Line | Purpose |
|---|---|
| outer `for` loop | graph may be disconnected / not all nodes reachable from one start |
| `GRAY` mark *before* recursing | lets descendants detect an edge back to an ancestor |
| `if GRAY -> cycle` | the only way a directed cycle can show up in DFS (section 8) |
| `BLACK` ignored | already fully placed; revisiting would be wasted work and could break `O(V+E)` |
| `append` *after* the loop | post-order = "after all my out-neighbors" |
| `reverse` at the end | convert sign-off order into dependency order |

### 6.3 Variants that avoid the reversal step

* Fill an array from the **back** (`pos = n-1; out[pos--] = u`).
* **Prepend** to a linked list (`O(1)`).
* **Flip edge meaning** (`u -> v` = "u *needs* v"): post-order is then directly the execution order (section 12).

---

## 7. Full worked trace

Graph: `n = 6`, edges `5->2, 5->0, 4->0, 4->1, 2->3, 3->1`.
Adjacency (insertion order): `0:[] 1:[] 2:[3] 3:[1] 4:[0,1] 5:[2,0]`.
Outer loop visits roots `0,1,2,3,4,5` in that order. (Numbers below come from the actual C program in section 15.1.)

```
 step  event                              stack (bottom -> top)   post-order so far
 ────  ─────────────────────────────────  ──────────────────────  ─────────────────
  1    root 0: discover 0   (disc=1)      [0]
  2    0 has no out-edges: finish 0 (2)   []                      [0]
  3    root 1: discover 1   (disc=3)      [1]
  4    finish 1 (fin=4)                   []                      [0 1]
  5    root 2: discover 2   (disc=5)      [2]
  6    edge 2->3, 3 WHITE: tree edge;
       discover 3 (disc=6)                [2 3]
  7    edge 3->1, 1 BLACK: cross edge,
       ignore                             [2 3]
  8    finish 3 (fin=7)                   [2]                     [0 1 3]
  9    finish 2 (fin=8)                   []                      [0 1 3 2]
 10    root 3: already BLACK, skip
 11    root 4: discover 4   (disc=9)      [4]
       4->0 BLACK (cross), 4->1 BLACK (cross)
       finish 4 (fin=10)                  []                      [0 1 3 2 4]
 12    root 5: discover 5   (disc=11)     [5]
       5->2 BLACK (cross), 5->0 BLACK (cross)
       finish 5 (fin=12)                  []                      [0 1 3 2 4 5]

 Reverse post-order  ==>  5 4 2 3 1 0      <- the topological order
```

Final table (matches program output):

```
 node  disc  fin
   0     1     2
   1     3     4
   2     5     8
   3     6     7
   4     9    10
   5    11    12
```

Parenthesis picture (each column is one clock tick):

```
 node 1  2  3  4  5  6  7  8  9  10 11 12
 0    [──]
 1          [──]
 2                [────────]
 3                   [──]
 4                            [──]
 5                                  [──]
```

Verify every edge goes left to right in `5 4 2 3 1 0`:

```
 5->2 ✔ (pos 0 < 2)   5->0 ✔ (0 < 5)   4->0 ✔ (1 < 5)
 4->1 ✔ (1 < 4)       2->3 ✔ (2 < 3)   3->1 ✔ (3 < 4)
```

Also check the key theorem `fin[u] > fin[v]` on each edge: `fin[5]=12 > fin[2]=8`, `fin[2]=8 > fin[3]=7`,
`fin[3]=7 > fin[1]=4`, `fin[4]=10 > fin[0]=2`, etc. ✔

### 7.1 The call stack as a "thread in a labyrinth"

Think of Ariadne's thread: the GRAY path is the thread you unspool as you go deeper. Backtracking
winds it back in. A GRAY neighbor means "this corridor leads back onto my own thread", which is a loop.

```
 time ──►
 stack depth
    3 |             ┌─ 3 ─┐
    2 |             │     │
    1 |       ┌─ 2 ─┴─────┴─┐
    0 |  0  1 │             │   4      5
      +────────────────────────────────────►
        (each box = lifetime of one frame; nesting = ancestors)
```

---

## 8. Proofs of correctness

### 8.1 Lemma A — a back edge exists ⇔ a directed cycle exists

**(⇒)** A back edge `(u, v)` has `v` GRAY, i.e. an ancestor of `u` in the DFS tree (or `v = u`).
So there is a tree path `v ~> u`, and the edge `u -> v` closes it: a cycle.

**(⇐)** Suppose a directed cycle `C` exists. Let `w` be the node of `C` discovered **first**.
At that moment every other node of `C` is WHITE and the rest of the cycle is a path of WHITE nodes
starting at `w`. By the **white-path theorem** all of them become descendants of `w`. In particular
the node `x` just before `w` on the cycle is a descendant, and the edge `x -> w` goes to an
ancestor: a back edge. So **DFS on a cyclic graph always sees at least one back edge**. ∎

Conclusion: `no GRAY neighbor ever seen` ⇔ **DAG**. This is both the correctness of cycle detection and the reason the algorithm may legitimately refuse to output an order.

### 8.2 Lemma B — in a DAG, every edge `(u, v)` has `fin[v] < fin[u]`

Consider the moment DFS examines edge `(u, v)` (`u` is GRAY). Cases by the color of `v`:

* **`v` WHITE** → becomes a descendant of `u`; by the parenthesis theorem `v` finishes before `u`. ✔
* **`v` BLACK** → `v` has already finished while `u` is still open. So `fin[v] < fin[u]`. ✔
* **`v` GRAY** → back edge → cycle (Lemma A). **Impossible in a DAG.**

In every possible case `fin[v] < fin[u]`. ∎

### 8.3 Theorem — decreasing finish time is a topological order

Order nodes by decreasing `fin`. For any edge `(u, v)` Lemma B gives `fin[u] > fin[v]`, so `u`
is placed before `v`. Every edge points rightward. ∎

### 8.4 Why the proof didn't need "start from a source"

Kahn's argument needs a node with in-degree 0 (slides: "if G is a DAG, G has a node with no
entering edges"). The DFS argument never looks for one. The start order of the outer loop is
**arbitrary** and the result is still valid; different start orders give *different valid* orders.

---

## 9. Complexity analysis

| Quantity | Value | Why |
|---|---|---|
| Time (adjacency list) | `Θ(V + E)` | each node colored/finished once; each edge examined once |
| Time (adjacency matrix) | `Θ(V²)` | scanning a row costs `V` per node |
| Extra space | `Θ(V)` | color array, output array, stack |
| Recursion depth (worst) | `V` | a simple path graph `1 -> 2 -> ... -> V` |
| Graph storage | `Θ(V + E)` | adjacency lists |

Same bound as the slides' source-removal algorithm, but with a *different constant profile*:
DFS has no in-degree counting pass and no queue; it only needs the colors.

**Deriving `V + E`:** `Σ_{u∈V} (1 + outdeg(u)) = V + E`. The `+1` is the discover/finish work, `outdeg(u)` is the edge-scan work. Unlike the undirected case in the slides (each edge counted twice via `degree(u)` and `degree(v)`), a *directed* edge is scanned exactly **once**, from its tail.

---

## 10. Cycle detection and extraction

### 10.1 Detection

Any GRAY neighbor ⇒ cycle ⇒ **no topological order exists**. The same single traversal
therefore gives you both "is it a DAG?" and the order.

### 10.2 Extracting the actual cycle (what real tools print)

Error messages like `a -> b -> c -> a` are valuable to users. Because the GRAY nodes are the
stack, when you hit a GRAY neighbor `v` from `u`:

```
 stack (bottom -> top):   [ r , x , v , p , q , u ]
                                    ▲                 \
                                    └───── back edge ──┘  u -> v

 cycle = stack from v to top, then v again:   v -> p -> q -> u -> v
```

Recursive implementations keep a separate `path`/`parent` array to do this. Iterative ones
already hold it (the explicit stack).

### 10.3 Self-loops and duplicate edges

* Self-loop `u -> u`: when `u` is examined it is GRAY, and the neighbor is itself. ✔ detected as a cycle of length 1.
* Duplicate (parallel) edges `u -> v` twice: second one sees `v` BLACK (or already scanned). ✔ harmless.

### 10.4 Finding *all* cyclic nodes

Plain DFS reports *one* cycle. To list every node that participates in a cycle you need strongly
connected components (Tarjan 1972, which is cited in your slides, or Kosaraju). A node is on a cycle
iff its SCC has size > 1 or it has a self-loop.

---

## 11. Recursive vs iterative

### 11.1 Recursion is elegant but fragile

Depth can reach `V`. For a path-shaped graph with a million nodes:

| Environment | Typical outcome |
|---|---|
| C | default ~8 MB stack on Linux main thread; a few 10⁴–10⁵ frames can overflow depending on frame size |
| Rust | main thread usually 8 MB; deep recursion ⇒ stack overflow abort (not a panic you can catch) |
| Go | goroutine stacks grow dynamically (default max 1 GB on 64-bit), so deep recursion usually works but costs memory |
| Python/JS | hard recursion limits, much smaller |

For untrusted or very large inputs (package registries, generated build graphs), **use an
explicit stack**.

### 11.2 Converting recursion to an explicit stack

A call frame must remember **(node, which out-edge to resume at)**. That's all.

```
 Recursive world                      Iterative world
 ─────────────────                    ──────────────────────────────
 call dfs(v)                    ==>   push (v, cursor = 0), color[v]=GRAY
 for loop index i inside frame  ==>   cursor field of the top frame
 return from dfs(u)             ==>   cursor == len(adj[u]): color BLACK, emit, pop
```

Pitfall: **advance the cursor *before* pushing the child**, otherwise when you pop back to the
parent you re-examine the same edge forever.

### 11.3 Frame layout at a real cycle detection

Using the real-world example of section 14/15 (`--cycle` flag adds `util.c -> app`):

```
 Node ids:  app=0  main.o=1  net.o=2  libutil.a=3  main.c=4  config.h=5  net.c=6  util.h=7  util.o=8  util.c=9

 explicit stack at the moment of detection (bottom -> top):

   depth   node        cursor / out-degree     meaning
   ─────   ──────────  ──────────────────────  ─────────────────────────────────
     0     app (0)      3 / 3                  finished scanning main.o,net.o,libutil.a
     1     libutil.a    1 / 1                  went into util.o
     2     util.o (8)   1 / 2                  went into util.c, util.h not yet scanned
     3     util.c (9)   1 / 1                  just examined edge util.c -> app
                                               color[app] == GRAY  => BACK EDGE

   cycle = slice from `app` upward + `app`:  app -> libutil.a -> util.o -> util.c -> app
```

---

## 12. Edge direction conventions

This is the single most common source of "my order is backwards" bugs. There are two
equally valid conventions; **pick one deliberately** and document it.

```
 Convention 1: "A -> B  means  A must come BEFORE B"        (precedence / slides' convention)
     result = REVERSE of post-order

 Convention 2: "A -> B  means  A DEPENDS ON / NEEDS B"       (Makefile / package.json style)
     result = post-order itself (deps are emitted first)
```

Illustration with the same real facts:

```
 Fact: to link `app` we must first compile `main.o`.

 Convention 1 graph:   main.o ──► app      topological order: main.o, app  = reverse(postorder)
 Convention 2 graph:   app ──► main.o      postorder:         main.o, app  = no reversal needed
```

Rule of thumb: **Convention 2 + post-order** is the natural fit when you store "what does X
need?" per node (which is how humans write build files). The real-world programs in sections
15–17 use Convention 2.

You can also convert: topological order of `G` with Convention 1 = post-order of the **transpose**
graph (all edges flipped) run with the same DFS.

---

## 13. DFS vs Kahn

| Aspect | DFS (this guide) | Kahn / source removal (your slides) |
|---|---|---|
| Idea | emit a node when it *finishes*; reverse | repeatedly remove a node with in-degree 0 |
| State | 3 colors, stack | `count(w)` (in-degree) array + queue/set `S` |
| Time | `Θ(V + E)` | `Θ(V + E)` |
| Cycle detection | GRAY neighbor (back edge) | queue empties before all `V` nodes emitted |
| Cycle *location* | easy: slice the stack | need extra work (remaining nodes contain a cycle, but not directly the path) |
| Lexicographically smallest order | not natural | trivial: replace queue by a min-heap |
| Layer/parallel levels | needs a DP afterwards | natural: BFS-style rounds |
| Subgraph only (only what `target` needs) | natural: DFS from `target` | needs a reachability pre-pass |
| Recursion depth issue | yes (unless iterative) | no recursion |
| Streaming/online friendliness | needs whole graph | works as in-degrees reach 0 |

When to pick which:

* **DFS**: build systems, dependency resolution, "do exactly what's needed for this target", good cycle error messages, SCC/DAG DP pipelines.
* **Kahn**: schedulers with parallel workers, lexicographic ordering requirements, level-by-level execution.

Kahn pseudocode for comparison (this is what the slides' running-time proof analyses):

```
 indeg[v] = number of incoming edges for each v
 S = { v : indeg[v] == 0 }
 while S not empty:
     v = remove from S;  output v
     for w in adj[v]:
         indeg[w] -= 1
         if indeg[w] == 0: add w to S
 if output size < V: CYCLE
```

---

## 14. Real-world architecture

### 14.1 Where topological sort sits inside a build tool / dependency resolver

This is the actual shape of the program implemented in sections 15–17 (and, with more machinery,
of tools like Make, Cargo, Bazel, Gradle, Terraform, Airflow, `apt`, etc.).

```
                        ┌──────────────────────────────────────────────┐
                        │                CLI / daemon                  │
                        │      `build app`      `build --check`        │
                        └───────────────────────┬──────────────────────┘
                                                │ requested target(s)
                                                ▼
 ┌────────────────┐  text   ┌─────────────────────────────────────────────┐
 │  Rule files    │───────► │ 1. PARSER                                   │
 │  Makefile      │         │    lines -> records (target, [deps...])     │
 │  BUILD / TOML  │         └──────────────────────┬──────────────────────┘
 │  DAG definition│                                │ records
 └────────────────┘                                ▼
                         ┌─────────────────────────────────────────────────┐
                         │ 2. GRAPH BUILDER                                │
                         │    intern: name -> integer id   (hash map)      │
                         │    adj[id] = [dependency ids]   (Convention 2)  │
                         └──────────────────────┬──────────────────────────┘
                                                │ Graph (V nodes, E edges)
                                                ▼
                         ┌─────────────────────────────────────────────────┐
                         │ 3. TOPOLOGICAL SORT  (iterative DFS)            │
                         │                                                 │
                         │   color[]  : WHITE / GRAY / BLACK               │
                         │   stack[]  : (node, edge cursor) = GRAY path    │
                         │   order[]  : post-order == build order          │
                         └───────────┬───────────────────────┬─────────────┘
                              order  │                       │ GRAY neighbor found
                                     ▼                       ▼
        ┌─────────────────────────────────────┐   ┌──────────────────────────────┐
        │ 4. EXECUTOR / SCHEDULER             │   │ 4b. DIAGNOSTICS              │
        │    for task in order: run(task)     │   │  "a -> b -> c -> a"          │
        │    parallel variant: run a task as  │   │  exit status != 0            │
        │    soon as all its deps are done    │   └──────────────────────────────┘
        └─────────────────────────────────────┘
                                     │
                                     ▼
                        ┌──────────────────────────────┐
                        │ 5. ARTIFACT CACHE / OUTPUTS  │
                        │    skip tasks that are fresh │
                        └──────────────────────────────┘
```

### 14.2 Concrete example graph used by all three implementations

Convention 2: an arrow means "needs".

```
                     ┌────────────────────────── app ──────────────────────────┐
                     │                            │                             │
                     ▼                            ▼                             ▼
                  main.o                        net.o                       libutil.a
                  │     │                    │   │   │                         │
                  ▼     ▼                    ▼   ▼   ▼                         ▼
              main.c  config.h            net.c config.h util.h              util.o
                                                                              │    │
                                                                              ▼    ▼
                                                                          util.c  util.h
```

`config.h` and `util.h` are *shared* by several nodes: this makes it a DAG, not a tree. DFS
visits each exactly once thanks to the BLACK check (a "cross" edge is ignored the second time).

Real output of the C program (section 15.2):

```
 build order:
    1. main.c
    2. config.h
    3. main.o
    4. net.c
    5. util.h
    6. net.o
    7. util.c
    8. util.o
    9. libutil.a
   10. app
```

How that order was produced (post-order of the DFS from `app`):

```
 visit app
   visit main.o
     visit main.c      -> emit main.c     (1)
     visit config.h    -> emit config.h   (2)
   emit main.o                            (3)
   visit net.o
     visit net.c       -> emit net.c      (4)
     config.h is BLACK -> skip (cross edge)
     visit util.h      -> emit util.h     (5)
   emit net.o                             (6)
   visit libutil.a
     visit util.o
       visit util.c    -> emit util.c     (7)
       util.h is BLACK -> skip
     emit util.o                          (8)
   emit libutil.a                         (9)
 emit app                                 (10)
```

### 14.3 What real systems do with the same idea

| System | Graph | Cycle behavior |
|---|---|---|
| GNU Make | targets -> prerequisites, DFS from the requested goal | reports a circular dependency and drops it |
| Cargo / package managers | package or build-unit dependency graph | cyclic package dependencies are rejected |
| Terraform | resources and their references | fails with a "Cycle" error listing the participants |
| Airflow / dbt / Dagster style orchestrators | task/model DAG | cycles are rejected when the DAG is loaded |
| ES module loaders | import graph; evaluation is a DFS post-order so dependencies run first | cycles are allowed, with partially-initialized modules |
| Go compiler/linker | package import graph; packages initialize dependencies-first | import cycles are compile errors |
| Spreadsheet recalculation | cell -> cells it references | circular reference warning |

(This table describes the *shape* of each system conceptually; internals differ and evolve.)

---

## 15. C

### 15.1 Minimal recursive version (teaching core)

Convention 1 here: edge `u -> v` means "u before v", so we **reverse** the post-order.
Compressed adjacency (CSR) is used: `start[u] .. start[u+1]` is the slice of `adj` holding the out-neighbors of `u`.

```
 CSR layout for edges 5->2, 5->0, 4->0, 4->1, 2->3, 3->1  (n = 6)

 index :  0  1  2  3  4  5  6
 start :  0  0  0  1  2  4  6          start[u]..start[u+1]-1 = out-edges of u
 adj   :  [3] [1] [0 1] [2 0]
           ▲   ▲    ▲      ▲
           2   3    4      5            (owner node of each block)
```

```c
/* rec.c  -- compile: gcc -std=c11 -Wall -Wextra -O2 -o rec rec.c */
#include <stdio.h>
#include <stdbool.h>
#include <stdlib.h>

enum { WHITE, GRAY, BLACK };

typedef struct { int n; int *start; int *adj; } CSR;   /* compressed adjacency */

static int  *color, *order, order_len, timer_, *disc, *fin;
static bool  has_cycle;

static void dfs(const CSR *g, int u) {
    color[u] = GRAY;  disc[u] = ++timer_;
    for (int i = g->start[u]; i < g->start[u + 1]; i++) {
        int v = g->adj[i];
        if (color[v] == WHITE)     dfs(g, v);          /* tree edge   */
        else if (color[v] == GRAY) has_cycle = true;   /* back edge   */
        /* BLACK -> forward/cross edge: ignore                        */
    }
    color[u] = BLACK; fin[u] = ++timer_;
    order[order_len++] = u;                            /* post-order  */
}

int main(void) {
    int n = 6;
    int edges[][2] = {{5,2},{5,0},{4,0},{4,1},{2,3},{3,1}};
    int m = sizeof edges / sizeof edges[0];

    /* build CSR with a counting pass + prefix sums */
    int *start = calloc(n + 2, sizeof(int)), *adj = malloc(m * sizeof(int));
    for (int i = 0; i < m; i++) start[edges[i][0] + 1]++;
    for (int i = 0; i < n; i++) start[i + 1] += start[i];
    int *pos = malloc(n * sizeof(int));
    for (int i = 0; i < n; i++) pos[i] = start[i];
    for (int i = 0; i < m; i++) adj[pos[edges[i][0]]++] = edges[i][1];
    CSR g = { n, start, adj };

    color = calloc(n, sizeof(int));  order = malloc(n * sizeof(int));
    disc  = calloc(n, sizeof(int));  fin   = calloc(n, sizeof(int));

    for (int u = 0; u < n; u++) if (color[u] == WHITE) dfs(&g, u);   /* outer loop */

    if (has_cycle) { puts("cycle"); return 1; }
    for (int u = 0; u < n; u++) printf("node %d: disc=%d fin=%d\n", u, disc[u], fin[u]);
    printf("postorder:");   for (int i = 0; i < order_len; i++)     printf(" %d", order[i]);
    printf("\ntopo:");      for (int i = order_len - 1; i >= 0; i--) printf(" %d", order[i]);
    puts("");
    return 0;
}
```

Real output (compiled with `gcc 13.3`, `-Wall -Wextra`, no warnings):

```
node 0: disc=1 fin=2
node 1: disc=3 fin=4
node 2: disc=5 fin=8
node 3: disc=6 fin=7
node 4: disc=9 fin=10
node 5: disc=11 fin=12
postorder: 0 1 3 2 4 5
topo: 5 4 2 3 1 0
```

This matches the trace in section 7 exactly.

**Notes on the C code**

* Globals are used only to keep the teaching version short. In library code pass a context struct.
* `calloc` zero-initializes, and `WHITE == 0`, so "all WHITE" is free.
* `has_cycle` is recorded but traversal continues; once a cycle is found the `order` is meaningless. Production code returns immediately (next section).
* Recursion depth can reach `n`. Next section removes recursion.

### 15.2 Real-world version: iterative DFS, named tasks, cycle path

```c
/* depsort.c - build-order resolver using iterative DFS topological sort.
 * Edge direction: target -> dependency ("target needs dependency").
 * Therefore DFS post-order IS the build order (dependencies first).
 *
 * compile:  gcc -std=c11 -Wall -Wextra -O2 -o depsort depsort.c
 * run:      ./depsort            # prints build order
 *           ./depsort --cycle    # injects util.c -> app, reports the cycle
 */
#include <stdio.h>
#include <string.h>

#define MAX_NODES 128
#define MAX_EDGES 1024
#define NAME_LEN  32

typedef struct {
    int  n, m;
    char names[MAX_NODES][NAME_LEN];
    int  head[MAX_NODES];   /* first edge of node, -1 if none        */
    int  tail[MAX_NODES];   /* last edge of node (O(1) append)       */
    int  to[MAX_EDGES];     /* edge -> destination node              */
    int  next[MAX_EDGES];   /* edge -> next edge of same source node */
} Graph;

typedef enum { WHITE = 0, GRAY = 1, BLACK = 2 } Color;

typedef struct {
    int order[MAX_NODES];      int order_len;   /* valid when cycle_len == 0 */
    int cycle[MAX_NODES + 1];  int cycle_len;   /* > 0 => cycle found        */
} TopoResult;

static int graph_id(Graph *g, const char *name) {
    for (int i = 0; i < g->n; i++)
        if (strcmp(g->names[i], name) == 0) return i;
    if (g->n == MAX_NODES) return -1;
    int id = g->n++;
    snprintf(g->names[id], NAME_LEN, "%s", name);
    g->head[id] = g->tail[id] = -1;
    return id;
}

static int graph_add_edge(Graph *g, int from, int to) {
    if (g->m == MAX_EDGES) return -1;
    int e = g->m++;
    g->to[e] = to;
    g->next[e] = -1;
    if (g->head[from] == -1) g->head[from] = e;
    else                     g->next[g->tail[from]] = e;
    g->tail[from] = e;
    return e;
}

/* returns 0 on success, -1 if a cycle exists (r->cycle filled in) */
static int toposort_dfs(const Graph *g, TopoResult *r) {
    Color color[MAX_NODES] = {0};
    int stack_node[MAX_NODES];   /* the explicit call stack = the GRAY path */
    int stack_edge[MAX_NODES];   /* resume point: next edge to look at      */

    r->order_len = 0;
    r->cycle_len = 0;

    for (int root = 0; root < g->n; root++) {
        if (color[root] != WHITE) continue;

        int sp = 0;
        color[root] = GRAY;
        stack_node[sp] = root;
        stack_edge[sp] = g->head[root];
        sp++;

        while (sp > 0) {
            int u = stack_node[sp - 1];
            int e = stack_edge[sp - 1];

            if (e == -1) {                    /* all neighbours done: FINISH u */
                color[u] = BLACK;
                r->order[r->order_len++] = u; /* post-order append             */
                sp--;
                continue;
            }
            stack_edge[sp - 1] = g->next[e];  /* advance BEFORE descending     */
            int v = g->to[e];

            if (color[v] == WHITE) {          /* tree edge: "recurse"          */
                color[v] = GRAY;
                stack_node[sp] = v;
                stack_edge[sp] = g->head[v];
                sp++;
            } else if (color[v] == GRAY) {    /* back edge: cycle!             */
                int i = sp - 1;
                while (stack_node[i] != v) i--;
                int len = 0;
                for (int k = i; k < sp; k++) r->cycle[len++] = stack_node[k];
                r->cycle[len++] = v;          /* close the loop                */
                r->cycle_len = len;
                return -1;
            }
            /* BLACK: forward/cross edge, already fully handled -> ignore      */
        }
    }
    return 0;
}

typedef struct { const char *target; const char *deps[6]; } Rule;

static const Rule RULES[] = {
    {"app",       {"main.o", "net.o", "libutil.a", NULL}},
    {"main.o",    {"main.c", "config.h", NULL}},
    {"net.o",     {"net.c", "config.h", "util.h", NULL}},
    {"libutil.a", {"util.o", NULL}},
    {"util.o",    {"util.c", "util.h", NULL}},
};

int main(int argc, char **argv) {
    Graph g = { .n = 0, .m = 0 };

    for (size_t i = 0; i < sizeof RULES / sizeof RULES[0]; i++) {
        int t = graph_id(&g, RULES[i].target);
        for (int j = 0; RULES[i].deps[j]; j++) {
            int d = graph_id(&g, RULES[i].deps[j]);
            if (t < 0 || d < 0 || graph_add_edge(&g, t, d) < 0) {
                fprintf(stderr, "capacity exceeded\n");
                return 2;
            }
        }
    }
    if (argc > 1 && strcmp(argv[1], "--cycle") == 0) {
        /* sabotage: util.c now "needs" app -> app>libutil.a>util.o>util.c>app */
        graph_add_edge(&g, graph_id(&g, "util.c"), graph_id(&g, "app"));
    }

    TopoResult r;
    if (toposort_dfs(&g, &r) != 0) {
        fprintf(stderr, "error: dependency cycle: ");
        for (int i = 0; i < r.cycle_len; i++)
            fprintf(stderr, "%s%s", g.names[r.cycle[i]],
                    i + 1 < r.cycle_len ? " -> " : "\n");
        return 1;
    }
    printf("build order:\n");
    for (int i = 0; i < r.order_len; i++)
        printf("  %2d. %s\n", i + 1, g.names[r.order[i]]);
    return 0;
}
```

Real runs:

```
$ ./depsort
build order:
   1. main.c
   2. config.h
   3. main.o
   4. net.c
   5. util.h
   6. net.o
   7. util.c
   8. util.o
   9. libutil.a
  10. app

$ ./depsort --cycle ; echo "exit=$?"
error: dependency cycle: app -> libutil.a -> util.o -> util.c -> app
exit=1
```

**Design explanations**

| Decision | Reason |
|---|---|
| forward-star arrays (`head/tail/to/next`) | no per-edge `malloc`; `O(1)` append; cache-friendly; trivially freed |
| `tail[]` array | keeps edges in *insertion order* so output is deterministic and predictable |
| parallel arrays `stack_node` / `stack_edge` | the explicit stack frame is just `(node, cursor)` |
| stack capacity `MAX_NODES` | each node is pushed at most once (it is GRAY only once), so depth ≤ `n` |
| advance cursor before push | otherwise returning to the parent would re-read the same edge forever |
| cycle extraction by scanning the stack | the stack *is* the set of GRAY nodes in path order |
| linear scan in `graph_id` | fine for demos; replace by a hash table when `n` is large (the interning step must be `O(1)` to keep the total near `O(V+E)`) |
| `Color color[...] = {0}` | `WHITE == 0` |

**Scaling it up:** replace fixed arrays by `realloc`-grown vectors, add a hash map for interning,
and return an error code rather than `-1` magic values. The DFS core stays unchanged.

---

## 16. Go

> **Verification note:** the C programs above were compiled and executed. The Go and Rust programs below
> were written to mirror the C program step for step (same node numbering, same edge order, same
> DFS), so they are expected to print the same output, but I did not have the Go/Rust toolchains
> available to run them. If anything fails to compile on your toolchain, treat it as a bug report.

### 16.1 Minimal recursive version

```go
// topo_rec.go
package main

import "fmt"

// TopoSortRecursive: edge u->v means "u must come before v" (Convention 1).
// Returns (order, true), or (nil, false) if the graph has a directed cycle.
func TopoSortRecursive(adj [][]int) ([]int, bool) {
	const (
		white, gray, black = 0, 1, 2
	)
	n := len(adj)
	color := make([]uint8, n)
	post := make([]int, 0, n)

	var dfs func(u int) bool
	dfs = func(u int) bool {
		color[u] = gray
		for _, v := range adj[u] {
			switch color[v] {
			case white:
				if !dfs(v) {
					return false
				}
			case gray: // back edge -> cycle
				return false
			}
			// black: forward/cross edge -> ignore
		}
		color[u] = black
		post = append(post, u) // post-order
		return true
	}

	for u := 0; u < n; u++ { // outer loop: all components
		if color[u] == white && !dfs(u) {
			return nil, false
		}
	}
	// reverse the post-order in place
	for i, j := 0, len(post)-1; i < j; i, j = i+1, j-1 {
		post[i], post[j] = post[j], post[i]
	}
	return post, true
}

func main() {
	adj := [][]int{
		0: {},
		1: {},
		2: {3},
		3: {1},
		4: {0, 1},
		5: {2, 0},
	}
	order, ok := TopoSortRecursive(adj)
	fmt.Println(order, ok) // [5 4 2 3 1 0] true
}
```

Go specifics worth knowing:

* A closure that refers to itself needs `var dfs func(int) bool` declared first.
* Go stacks grow on demand, so deep recursion rarely crashes, but memory use is real (every frame is on a heap-backed stack segment). For adversarial inputs still prefer the explicit stack.
* `switch` cases do not fall through, and an unmatched `black` simply does nothing.

### 16.2 Real-world version: iterative DFS, named tasks, typed cycle error

```go
// depsort.go
//
//	go mod init depsort
//	go run . ; go run . --cycle
package main

import (
	"errors"
	"fmt"
	"os"
	"strings"
)

type Color uint8

const (
	White Color = iota
	Gray
	Black
)

// Graph stores "x needs y" edges (Convention 2): post-order == build order.
type Graph struct {
	names []string
	index map[string]int
	adj   [][]int
}

func NewGraph() *Graph { return &Graph{index: make(map[string]int)} }

// ID interns a name and returns its dense integer id.
func (g *Graph) ID(name string) int {
	if id, ok := g.index[name]; ok {
		return id
	}
	id := len(g.names)
	g.names = append(g.names, name)
	g.index[name] = id
	g.adj = append(g.adj, nil)
	return id
}

// AddEdge records that `from` needs `to`.
func (g *Graph) AddEdge(from, to string) {
	f, t := g.ID(from), g.ID(to) // resolve both ids first: ID may grow g.adj
	g.adj[f] = append(g.adj[f], t)
}

// CycleError carries the offending cycle so callers can print or inspect it.
type CycleError struct{ Path []string }

func (e *CycleError) Error() string {
	return "dependency cycle: " + strings.Join(e.Path, " -> ")
}

// frame is one "call frame" of the simulated recursion.
type frame struct {
	node int // which node
	next int // index of the next out-edge to examine
}

// TopoSort returns names so that every node appears after everything it needs.
func (g *Graph) TopoSort() ([]string, error) {
	n := len(g.names)
	color := make([]Color, n)
	order := make([]string, 0, n)
	stack := make([]frame, 0, n) // depth never exceeds n (a node is GRAY once)

	for root := 0; root < n; root++ {
		if color[root] != White {
			continue
		}
		color[root] = Gray
		stack = append(stack, frame{node: root})

		for len(stack) > 0 {
			top := &stack[len(stack)-1]
			u := top.node

			if top.next == len(g.adj[u]) { // all edges scanned: FINISH u
				color[u] = Black
				order = append(order, g.names[u]) // post-order append
				stack = stack[:len(stack)-1]
				continue
			}

			v := g.adj[u][top.next]
			top.next++ // advance BEFORE pushing a child

			switch color[v] {
			case White: // tree edge
				color[v] = Gray
				stack = append(stack, frame{node: v})
			case Gray: // back edge: the stack IS the gray path
				i := len(stack) - 1
				for stack[i].node != v {
					i--
				}
				path := make([]string, 0, len(stack)-i+1)
				for _, f := range stack[i:] {
					path = append(path, g.names[f.node])
				}
				path = append(path, g.names[v]) // close the loop
				return nil, &CycleError{Path: path}
			case Black:
				// forward/cross edge: nothing to do
			}
		}
	}
	return order, nil
}

type Rule struct {
	Target string
	Deps   []string
}

var rules = []Rule{
	{"app", []string{"main.o", "net.o", "libutil.a"}},
	{"main.o", []string{"main.c", "config.h"}},
	{"net.o", []string{"net.c", "config.h", "util.h"}},
	{"libutil.a", []string{"util.o"}},
	{"util.o", []string{"util.c", "util.h"}},
}

func main() {
	g := NewGraph()
	for _, r := range rules {
		g.ID(r.Target) // same id assignment order as the C version
		for _, d := range r.Deps {
			g.AddEdge(r.Target, d)
		}
	}
	if len(os.Args) > 1 && os.Args[1] == "--cycle" {
		g.AddEdge("util.c", "app") // sabotage: introduces a cycle
	}

	order, err := g.TopoSort()
	if err != nil {
		var ce *CycleError
		if errors.As(err, &ce) {
			fmt.Fprintf(os.Stderr, "error: %v (cycle length %d)\n", ce, len(ce.Path)-1)
		} else {
			fmt.Fprintf(os.Stderr, "error: %v\n", err)
		}
		os.Exit(1)
	}
	fmt.Println("build order:")
	for i, name := range order {
		fmt.Printf("  %2d. %s\n", i+1, name)
	}
}
```

Expected behavior (same graph, same traversal order as the C program):

```
$ go run .
build order:
   1. main.c
   2. config.h
   3. main.o
   4. net.c
   5. util.h
   6. net.o
   7. util.c
   8. util.o
   9. libutil.a
  10. app

$ go run . --cycle
error: dependency cycle: app -> libutil.a -> util.o -> util.c -> app (cycle length 4)
```

**Go design notes**

| Decision | Reason |
|---|---|
| `map[string]int` interning + `[]string` reverse table | `O(1)` average name lookups; dense ids make arrays fast |
| `frame{node,next}` slice as stack | exact translation of "(node, resume point)" |
| `top := &stack[len(stack)-1]` | mutate the cursor in place. Safe here because capacity is `n`, so `append` never reallocates and invalidates `top`; also we do not touch `top` after pushing |
| `*CycleError` implementing `error` | callers can use `errors.As` to inspect the path programmatically |
| `order` stores names directly | the caller does not need the id table |

**Table-driven test (`depsort_test.go`)**

```go
package main

import "testing"

func validOrder(adj [][]int, order []int) bool {
	if len(order) != len(adj) {
		return false
	}
	pos := make([]int, len(adj))
	for i, u := range order {
		pos[u] = i
	}
	for u, vs := range adj {
		for _, v := range vs {
			if pos[u] >= pos[v] { // every edge must point rightwards
				return false
			}
		}
	}
	return true
}

func TestRecursive(t *testing.T) {
	cases := []struct {
		name string
		adj  [][]int
		ok   bool
	}{
		{"empty", [][]int{}, true},
		{"single", [][]int{{}}, true},
		{"chain", [][]int{{1}, {2}, {}}, true},
		{"diamond", [][]int{{1, 2}, {3}, {3}, {}}, true},
		{"self loop", [][]int{{0}}, false},
		{"two cycle", [][]int{{1}, {0}}, false},
		{"cycle behind DAG", [][]int{{1}, {2}, {1}}, false},
	}
	for _, c := range cases {
		order, ok := TopoSortRecursive(c.adj)
		if ok != c.ok {
			t.Fatalf("%s: ok=%v want %v", c.name, ok, c.ok)
		}
		if ok && !validOrder(c.adj, order) {
			t.Fatalf("%s: invalid order %v", c.name, order)
		}
	}
}
```

Run with `go test ./...` and, since cycle bugs hide in concurrency-free code too, `go vet ./...`.

---

## 17. Rust

### 17.1 Minimal recursive version

```rust
// src/bin/topo_rec.rs   (or paste into main.rs)
#[derive(Clone, Copy, PartialEq, Eq)]
enum Color { White, Gray, Black }

/// Convention 1: edge u -> v means "u before v".
/// Returns Some(order) or None if the graph has a cycle.
fn topo_sort_recursive(adj: &[Vec<usize>]) -> Option<Vec<usize>> {
    fn dfs(u: usize, adj: &[Vec<usize>], color: &mut [Color], post: &mut Vec<usize>) -> bool {
        color[u] = Color::Gray;
        for &v in &adj[u] {
            match color[v] {
                Color::White => {
                    if !dfs(v, adj, color, post) {
                        return false;
                    }
                }
                Color::Gray => return false, // back edge -> cycle
                Color::Black => {}           // forward/cross edge
            }
        }
        color[u] = Color::Black;
        post.push(u); // post-order
        true
    }

    let n = adj.len();
    let mut color = vec![Color::White; n];
    let mut post = Vec::with_capacity(n);
    for u in 0..n {
        if color[u] == Color::White && !dfs(u, adj, &mut color, &mut post) {
            return None;
        }
    }
    post.reverse(); // reverse post-order = topological order
    Some(post)
}

fn main() {
    let adj: Vec<Vec<usize>> = vec![
        vec![],      // 0
        vec![],      // 1
        vec![3],     // 2
        vec![1],     // 3
        vec![0, 1],  // 4
        vec![2, 0],  // 5
    ];
    println!("{:?}", topo_sort_recursive(&adj)); // Some([5, 4, 2, 3, 1, 0])
}
```

Rust specifics:

* The borrow checker forces us to thread `color` and `post` as `&mut` parameters instead of capturing them in a closure (a recursive closure needs boxed `dyn Fn` gymnastics; a nested `fn` is cleaner).
* Items (the `enum` and nested `fn`) declared inside a function are visible to each other within that block.
* The program cannot "forget" the outer loop because `Option` makes you handle the cycle result.

### 17.2 Real-world version: iterative DFS, interned names, error type

`Cargo.toml`:

```toml
[package]
name = "depsort"
version = "0.1.0"
edition = "2021"
```

`src/main.rs`:

```rust
use std::collections::HashMap;
use std::env;
use std::fmt;
use std::process::ExitCode;

#[derive(Clone, Copy, PartialEq, Eq)]
enum Color {
    White,
    Gray,
    Black,
}

/// Convention 2: `add_edge(a, b)` means "a needs b" -> post-order is the build order.
#[derive(Default)]
struct Graph {
    names: Vec<String>,
    index: HashMap<String, usize>,
    adj: Vec<Vec<usize>>,
}

#[derive(Debug)]
struct CycleError {
    path: Vec<String>,
}

impl fmt::Display for CycleError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "dependency cycle: {}", self.path.join(" -> "))
    }
}

impl std::error::Error for CycleError {}

impl Graph {
    /// Intern a name and return its dense id.
    fn id(&mut self, name: &str) -> usize {
        if let Some(&id) = self.index.get(name) {
            return id;
        }
        let id = self.names.len();
        self.names.push(name.to_owned());
        self.index.insert(name.to_owned(), id);
        self.adj.push(Vec::new());
        id
    }

    fn add_edge(&mut self, from: &str, to: &str) {
        let f = self.id(from);
        let t = self.id(to);
        self.adj[f].push(t);
    }

    /// Iterative DFS. Returns names borrowed from the graph, dependencies first.
    fn topo_sort(&self) -> Result<Vec<&str>, CycleError> {
        let n = self.names.len();
        let mut color = vec![Color::White; n];
        let mut order: Vec<&str> = Vec::with_capacity(n);
        // (node, index of next out-edge to examine)  == one simulated call frame
        let mut stack: Vec<(usize, usize)> = Vec::with_capacity(n);

        for root in 0..n {
            if color[root] != Color::White {
                continue;
            }
            color[root] = Color::Gray;
            stack.push((root, 0));

            while let Some(top) = stack.last_mut() {
                let u = top.0;

                if top.1 == self.adj[u].len() {
                    // every out-edge scanned: FINISH u
                    color[u] = Color::Black;
                    order.push(&self.names[u]); // post-order append
                    stack.pop();
                    continue;
                }

                let v = self.adj[u][top.1];
                top.1 += 1; // advance BEFORE pushing a child

                match color[v] {
                    Color::White => {
                        // tree edge
                        color[v] = Color::Gray;
                        stack.push((v, 0));
                    }
                    Color::Gray => {
                        // back edge: the stack is the gray path
                        let start = stack.iter().position(|&(node, _)| node == v).unwrap();
                        let mut path: Vec<String> = stack[start..]
                            .iter()
                            .map(|&(node, _)| self.names[node].clone())
                            .collect();
                        path.push(self.names[v].clone()); // close the loop
                        return Err(CycleError { path });
                    }
                    Color::Black => {} // forward/cross edge
                }
            }
        }
        Ok(order)
    }
}

struct Rule {
    target: &'static str,
    deps: &'static [&'static str],
}

const RULES: &[Rule] = &[
    Rule { target: "app",       deps: &["main.o", "net.o", "libutil.a"] },
    Rule { target: "main.o",    deps: &["main.c", "config.h"] },
    Rule { target: "net.o",     deps: &["net.c", "config.h", "util.h"] },
    Rule { target: "libutil.a", deps: &["util.o"] },
    Rule { target: "util.o",    deps: &["util.c", "util.h"] },
];

fn main() -> ExitCode {
    let mut g = Graph::default();
    for r in RULES {
        g.id(r.target); // same id assignment order as the C and Go versions
        for d in r.deps {
            g.add_edge(r.target, d);
        }
    }
    if env::args().nth(1).as_deref() == Some("--cycle") {
        g.add_edge("util.c", "app"); // sabotage: introduces a cycle
    }

    match g.topo_sort() {
        Ok(order) => {
            println!("build order:");
            for (i, name) in order.iter().enumerate() {
                println!("  {:>2}. {}", i + 1, name);
            }
            ExitCode::SUCCESS
        }
        Err(e) => {
            eprintln!("error: {e}");
            ExitCode::from(1)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn order_respects_dependencies() {
        let mut g = Graph::default();
        for (a, b) in [("app", "lib"), ("lib", "util"), ("app", "util")] {
            g.add_edge(a, b);
        }
        let order = g.topo_sort().unwrap();
        let pos = |n: &str| order.iter().position(|&x| x == n).unwrap();
        assert!(pos("util") < pos("lib") && pos("lib") < pos("app"));
    }

    #[test]
    fn detects_cycle_and_reports_path() {
        let mut g = Graph::default();
        g.add_edge("a", "b");
        g.add_edge("b", "c");
        g.add_edge("c", "a");
        let e = g.topo_sort().unwrap_err();
        assert_eq!(e.path, vec!["a", "b", "c", "a"]);
    }

    #[test]
    fn self_loop_is_a_cycle() {
        let mut g = Graph::default();
        g.add_edge("x", "x");
        assert!(g.topo_sort().is_err());
    }
}
```

Run: `cargo run`, `cargo run -- --cycle`, `cargo test`. Expected behavior (same graph, same traversal order as C):

```
$ cargo run
build order:
   1. main.c
   2. config.h
   3. main.o
   4. net.c
   5. util.h
   6. net.o
   7. util.c
   8. util.o
   9. libutil.a
  10. app

$ cargo run -- --cycle
error: dependency cycle: app -> libutil.a -> util.o -> util.c -> app
```

**Rust design notes**

| Decision | Reason |
|---|---|
| `Result<Vec<&str>, CycleError>` | the cycle case is *in the type*: callers cannot ignore it |
| `order: Vec<&str>` borrowed from `self.names` | zero string copies on the success path |
| `(usize, usize)` stack of tuples | simplest frame; `last_mut()` gives in-place cursor update |
| mutate `top.1` *before* `stack.push` | non-lexical lifetimes end the `top` borrow after its last use, so the push compiles |
| `ExitCode` from `main` | proper process exit status without `process::exit` skipping destructors |
| `impl std::error::Error` | composes with `?`, `Box<dyn Error>`, and `anyhow`/`thiserror` ecosystems |
| no `unsafe`, no recursion | cannot overflow the stack, memory-safe by construction |

---

## 18. Applications built on top of topological order

A topological order is rarely the end product. It is the **evaluation order** that makes dynamic
programming on a DAG possible: when you process `v`, all of `v`'s predecessors are already final.

### 18.1 The DAG-DP template

```
 order = topological_order(G)            # Convention 1: u -> v means u before v
 init best[v] for all v
 for u in order:                         # predecessors are already settled
     for v in adj[u]:
         relax/update best[v] using best[u]
```

### 18.2 Longest path in a DAG (critical path method, project scheduling)

NP-hard on general graphs, `O(V + E)` on a DAG.

```
 dist[v] = 0 for all v
 for u in order:
     for (v, w) in adj[u]:
         dist[v] = max(dist[v], dist[u] + w)
 answer = max(dist)
```

```
 Tasks (duration) and precedence:      A(3) ──► C(2) ──► E(4)
                                       B(1) ──► C(2)
                                       B(1) ──► D(5) ──► E(4)

 earliest finish:  A=3  B=1  C=max(3,1)+2=5  D=1+5=6  E=max(5,6)+4=10
 critical path:    B -> D -> E   (length 10)
```

The same loop with `min` computes **shortest paths in a DAG**, which is correct **even with negative edge weights** (Dijkstra cannot do that) because the topological order guarantees each node's distance is final before it is used.

### 18.3 Counting paths

```
 ways[source] = 1
 for u in order:
     for v in adj[u]: ways[v] += ways[u]
```

### 18.4 Parallel scheduling levels

```
 level[v] = 0 if v has no predecessors
 level[v] = 1 + max(level[u] for u -> v)       # computed in topological order

 level 0:  a  b      run together
 level 1:  c         needs a,b
 level 2:  d  e      run together
```

All nodes of one level can run concurrently; `max level + 1` is the minimum number of sequential rounds with unlimited workers.

### 18.5 Demand-driven (lazy) evaluation: DFS from the target only

Running DFS from a single `target` visits **only what that target transitively needs**. This is
how a build tool avoids compiling unrelated modules, and a major practical reason to prefer DFS over a
whole-graph Kahn pass in build systems.

```
 whole graph:   A  B  C  D  E  F         DFS(target = C) touches only: C and what C needs
                      ▲
 build C  ───────────┘
```

### 18.6 Other uses

| Domain | Use |
|---|---|
| Compilers | instruction scheduling, evaluation order of expression DAGs, dead-code and data-flow passes |
| Spreadsheets | recalculation order, circular reference detection |
| Databases | query plan operator ordering, foreign-key-aware table load/delete order |
| Package managers | install order (dependencies first) |
| Course planning | prerequisite chains |
| Neural network frameworks | order of forward ops; reverse order for backpropagation through a computation DAG |
| Version control | commit DAG ordering (parents before children) |
| ML/data pipelines | stage execution order |

---

## 19. Variants and extensions

### 19.1 Cyclic graphs: condense strongly connected components

If cycles are legitimate (module imports, mutual recursion), contract each **strongly connected
component** into one node. The result (the *condensation*) is always a DAG, and you can
topologically sort that.

```
   original (has cycle)                condensation (DAG)

   a ──► b ──► c                        [a] ──► [b c] ──► [d]
         ▲     │                              (SCC)
         └─────┘ ──► d
```

* **Tarjan (1972)**, cited in your slides, finds SCCs in one DFS in `O(V + E)` and emits components in *reverse topological order of the condensation*.
* **Kosaraju**: DFS on `G` recording finish order; then DFS on the **transpose** graph in decreasing finish time. Each DFS tree in the second pass is one SCC. This reuses *exactly* the finish-time idea of this guide.

### 19.2 Lexicographically smallest topological order

Use **Kahn's algorithm with a min-heap** instead of a plain queue/set. Plain DFS does not give this
easily.

### 19.3 Enumerating *all* topological orders

Backtracking over Kahn's choices: at each step pick any currently available source, recurse, undo.
Exponential output size; use only on small graphs.

### 19.4 Detecting "is the order unique?"

Run Kahn: the order is unique iff the ready set never holds more than one node at once.

### 19.5 Incremental / dynamic topological order

When edges arrive one by one (build graphs under edit), recomputing from scratch is wasteful.
Specialized algorithms maintain a valid order incrementally and detect new cycles locally
(for example Pearce–Kelly style approaches). Worth knowing they exist; rarely needed.

### 19.6 Parallelizing

DFS is inherently sequential. For a parallel executor, compute the order (or levels) first, then
schedule with dependency counters: a task is dispatched when its pending-dependency counter hits 0 (that
counter is Kahn's `count(w)` from your slides, which is why runtime schedulers look like Kahn even
if validation used DFS).

### 19.7 Weighted / typed edges

Edge weights do not affect the topological sort itself (only DAG-DP on top). Edge *types* (hard vs
soft dependency, order-only prerequisites like Make's) mean you build **two graphs** or tag edges
and decide which tags participate in the sort.

---

## 20. Edge cases and pitfalls checklist

| # | Pitfall | Symptom | Fix |
|---|---|---|---|
| 1 | Forgetting the outer loop | missing nodes in output | loop over all nodes, start DFS at every WHITE |
| 2 | Using only two states (visited / not) | false positives on diamond DAGs, or missed cycles | use three colors: GRAY ≠ BLACK |
| 3 | Treating BLACK as a cycle | every DAG with shared dependencies "has a cycle" | only **GRAY** means cycle |
| 4 | Forgetting to unmark/mark BLACK at finish | endless cycle reports | set BLACK before emitting |
| 5 | Order reversed | dependencies appear after dependents | reverse post-order (Convention 1) or flip edges (Convention 2) |
| 6 | Cursor not advanced before push (iterative) | infinite loop | `cursor++` first, then push child |
| 7 | Recursion on huge/untrusted graphs | stack overflow | explicit stack |
| 8 | Self-loop not handled | missed cycle | GRAY check covers `u -> u` automatically |
| 9 | Adjacency matrix for sparse graphs | `Θ(V²)` slowness | adjacency lists |
| 10 | Mutating the graph while iterating | skipped or repeated edges | build first, sort second |
| 11 | Using the order after a detected cycle | garbage order | return error / empty result |
| 12 | Duplicate names (`"a "` vs `"a"`) | phantom nodes | normalize names while interning |
| 13 | Missing nodes only mentioned as dependencies | KeyError / dropped nodes | intern on both ends of an edge (as in `AddEdge`) |
| 14 | Non-determinism from hash-map iteration | flaky outputs between runs | iterate nodes by dense id, keep adjacency in insertion order |
| 15 | Disconnected cycle | cycle in a far corner is never examined | outer loop again |
| 16 | Dependency direction misunderstood | "wrong" order accepted as right | write the convention in a comment and in tests |

---

## 21. Testing strategy

**1. Always verify the output with an independent checker**

```
 valid(order, G):  pos[v] = index of v in order
                   every node appears exactly once, and for every edge (u,v): pos[u] < pos[v]
```

(Convention 2 graphs: check `pos[v] < pos[u]`, i.e. dependencies first.)

**2. Hand-picked cases:** empty graph; single node; self-loop; two-node cycle; chain; diamond
(shared dependency); disconnected components; a cycle reachable only from a non-first root;
a DAG with a cycle hanging *off* of it.

**3. Random DAGs by construction:** choose a random permutation `p`, add only edges from an earlier
to a later position of `p`, shuffle the node labels. The result is guaranteed acyclic, so your
sort must succeed and pass the checker.

**4. Random cyclic graphs:** take such a DAG and add one edge from a node to one of its
ancestors (or any edge `v -> u` where `u ~> v` exists). The sort must report a cycle, and the
reported cycle must be a real closed walk (check each consecutive pair is an edge).

**5. Differential testing:** run Kahn and DFS on the same graph. They may return different orders
but must agree on **cycle vs no cycle**, and both orders must pass the checker.

**6. Stress depth:** chain of `10^6` nodes. Recursive version should be expected to blow up in
some languages; the iterative one must pass.

**7. Determinism:** run twice; identical input must give identical output.

---

## 22. Practice problems

| Problem | Core idea |
|---|---|
| LeetCode 207 Course Schedule | cycle detection only (GRAY check) |
| LeetCode 210 Course Schedule II | return the order, `[]` if cyclic |
| LeetCode 269 Alien Dictionary | derive precedence edges from adjacent words, then topo-sort letters; careful with prefix-invalid cases |
| LeetCode 802 Find Eventual Safe States | nodes that cannot reach a cycle; GRAY/BLACK reasoning |
| LeetCode 329 Longest Increasing Path in a Matrix | implicit DAG, DFS + memoization = DP in topological order |
| LeetCode 444 Sequence Reconstruction | unique topological order check (ready set size 1) |
| LeetCode 1203 Sort Items by Groups Respecting Dependencies | two-level topological sort (groups, then items) |
| LeetCode 2115 Find All Possible Recipes | dependency resolution from available supplies |
| Critical path of a project | DAG-DP over topological order |
| Detect a circular import | cycle extraction as in the real-world programs |

Exercises to cement understanding:

1. Modify the C program so that it takes a **target** and prints only what is needed for it (hint: start DFS only from that node).
2. Add a **"level" output**: compute `level[v]` and print tasks grouped by level.
3. Implement Kahn's algorithm in the same three languages and differential-test against DFS.
4. Convert the program to Convention 1 and make it print the *reverse* of post-order.
5. Extend it to report **all** nodes that lie on some cycle using Tarjan's SCC.

---

## 23. Mental-model cheat sheet

```
 ┌──────────────────────────────────────────────────────────────────────────┐
 │ 1. Topological order exists  <=>  no directed cycle (DAG).               │
 │ 2. DFS keeps ONE live path: the GRAY nodes = the recursion stack.        │
 │ 3. See a GRAY neighbor?  You closed a loop -> CYCLE.                     │
 │    See a BLACK neighbor? Already done -> skip. See WHITE? -> recurse.    │
 │ 4. Emit a node when it FINISHES (post-order): it comes after everything  │
 │    it points to.                                                         │
 │ 5. Reverse that list  ->  every arrow points left-to-right.              │
 │    ("Finish last = go first.")                                           │
 │ 6. "X needs Y" edges: post-order is directly the execution order.        │
 │ 7. Time Theta(V+E), extra space Theta(V). Use an explicit stack for      │
 │    deep graphs.                                                          │
 │ 8. Outer loop over all nodes is mandatory (disconnected graphs).         │
 │ 9. Proof in one line: for any edge u->v in a DAG, v finishes before u    │
 │    (v WHITE: nested; v BLACK: already done; v GRAY: impossible).         │
 └──────────────────────────────────────────────────────────────────────────┘
```

**Decision flow**

```
                    need an ordering of tasks with prerequisites?
                                    │
                    ┌───────────────┴────────────────┐
                    │                                │
        need parallel levels,               need "only what target needs",
        lexicographically smallest,         good cycle path error,
        or streaming?                       or SCC / DAG-DP pipeline?
                    │                                │
                    ▼                                ▼
          Kahn (source removal)               DFS post-order (this guide)
          queue / min-heap                    3 colors + (iterative) stack
```

**Re-derivation drill (do this without looking):**

1. Draw a 5-node DAG with a diamond. Run DFS by hand writing `disc/fin`.
2. Write post-order, reverse it, check each edge.
3. Add one edge that makes a cycle and mark where the first GRAY neighbor appears.
4. State why a BLACK neighbor is harmless, and why a GRAY neighbor is not.
5. Explain, in one sentence each, why the order is valid and why the runtime is `O(V+E)`.

If you can do these five from memory, you own the algorithm.

---

## References

* J. Kleinberg & É. Tardos, *Algorithm Design*, Chapter 3 (lecture slides by Kevin Wayne, Princeton): DAGs, topological ordering, source-removal algorithm and its `O(m + n)` analysis.
* T. Cormen, C. Leiserson, R. Rivest, C. Stein, *Introduction to Algorithms* (CLRS), §22.3 (DFS: colors, timestamps, parenthesis and white-path theorems, edge classification) and §22.4 (topological sort).
* R. Sedgewick & K. Wayne, *Algorithms* (4th ed.), §4.2 (directed graphs, DFS, topological order).
* R. Tarjan, "Depth-First Search and Linear Graph Algorithms," *SIAM J. Comput.* 1(2), 1972 (strong components via DFS).
* A. B. Kahn, "Topological sorting of large networks," *Communications of the ACM*, 1962 (source-removal algorithm).
