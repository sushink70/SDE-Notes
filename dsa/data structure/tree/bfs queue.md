# BFS (Breadth-First Search) — Comprehensive Guide
> *Train like a monk. Think like an expert. Code like a craftsman.*

---

## Table of Contents

1. [Foundational Concepts — Building the Mental Model](#1-foundational-concepts)
2. [What is a Queue? (FIFO Deep Dive)](#2-what-is-a-queue)
3. [Graph Theory Primer (Vocabulary You Must Know)](#3-graph-theory-primer)
4. [BFS — The Core Algorithm](#4-bfs-the-core-algorithm)
5. [ASCII Visualizations & Step-by-Step Walkthroughs](#5-ascii-visualizations)
6. [Algorithm Flowcharts & Decision Trees](#6-algorithm-flowcharts)
7. [Time & Space Complexity Analysis](#7-complexity-analysis)
8. [Implementation in C](#8-implementation-in-c)
9. [Implementation in Go](#9-implementation-in-go)
10. [Implementation in Rust](#10-implementation-in-rust)
11. [BFS on Trees (Level-Order Traversal)](#11-bfs-on-trees)
12. [BFS on Grids / 2D Matrices](#12-bfs-on-grids)
13. [Multi-Source BFS](#13-multi-source-bfs)
14. [0-1 BFS (Deque-Based)](#14-0-1-bfs)
15. [Bidirectional BFS](#15-bidirectional-bfs)
16. [BFS for Shortest Path (Weighted vs Unweighted)](#16-shortest-path)
17. [BFS vs DFS — Deep Comparison](#17-bfs-vs-dfs)
18. [Common Problem Patterns & Templates](#18-problem-patterns)
19. [Classic Problems with Expert Reasoning](#19-classic-problems)
20. [Mental Models, Cognitive Strategies & Elite Thinking](#20-mental-models)

---

## 1. Foundational Concepts

Before writing a single line of code, an expert builds a *mental model* — a precise, abstract picture of what the algorithm *is* before thinking about how to implement it.

### What Problem Does BFS Solve?

Imagine you are standing in a city. You want to find the **nearest hospital**. You would not randomly teleport to distant locations first — you would explore nearby streets first, then expand outward in rings.

BFS is exactly this: **explore layer by layer, closest first.**

It answers questions like:
- What is the **shortest path** (in terms of number of edges) from A to B?
- Is node B **reachable** from node A at all?
- What are **all nodes at distance k** from a source?
- What is the **minimum number of steps** to solve a puzzle?

### The Wave Metaphor

Drop a stone into still water. Ripples expand outward in concentric circles — the first ring is distance 1, the second ring is distance 2, and so on. BFS is that ripple. It guarantees that when you first reach a node, you reached it via the **shortest path**.

```
         [Source]
            |
     -------+-------          ← Distance 1
     |               |
   [A]             [B]
   / \             / \         ← Distance 2
 [C] [D]        [E] [F]
                              ← Distance 3 ...
```

---

## 2. What is a Queue?

### The FIFO Principle

A **Queue** is a linear data structure that follows **FIFO**: **F**irst **I**n, **F**irst **O**ut.

Think of a line at a ticket counter:
- The first person to arrive is the first to be served.
- New arrivals join the **back (tail/rear)**.
- Service happens from the **front (head)**.

```
ENQUEUE (push to back)                    DEQUEUE (pop from front)
        ↓                                          ↑
  ┌─────────────────────────────────────────────────┐
  │  [E]  [D]  [C]  [B]  [A]  ← ← ← ← ← ← ← ←  │
  └─────────────────────────────────────────────────┘
   BACK                                        FRONT
```

### Queue Operations & Complexity

| Operation | Description                        | Time Complexity |
|-----------|------------------------------------|-----------------|
| `enqueue` | Add element to the back            | O(1)            |
| `dequeue` | Remove element from the front      | O(1)            |
| `peek`    | View front element without removing| O(1)            |
| `is_empty`| Check if queue has no elements     | O(1)            |
| `size`    | Number of elements                 | O(1)            |

### Why Does BFS Need a Queue?

BFS needs to process nodes **in the order they were discovered**. If you discover A's neighbors before B's neighbors, you must finish processing A's neighbors before going deeper. This is exactly what a queue enforces.

If you used a **stack** instead of a queue, you would get **DFS** (Depth-First Search) — you would dive deep before exploring siblings.

```
Queue → BFS (breadth first, level by level)
Stack → DFS (depth first, one path at a time)
```

### Types of Queues Used in BFS Variants

| Queue Type      | Used In                  | Reason                                  |
|-----------------|--------------------------|-----------------------------------------|
| Simple Queue    | Standard BFS             | FIFO ordering                           |
| Deque (double-ended) | 0-1 BFS           | Push 0-weight to front, 1-weight to back|
| Priority Queue  | Dijkstra's / A*          | Process cheapest node first             |
| Two Queues      | Bidirectional BFS        | Expand from both ends                   |

---

## 3. Graph Theory Primer

BFS works on **graphs** and **trees**. You must understand this vocabulary before going further.

### What is a Graph?

A **graph** G = (V, E) consists of:
- **V** — a set of **vertices** (also called *nodes*)
- **E** — a set of **edges** (connections between nodes)

```
Vertices: {A, B, C, D, E}
Edges:    {A-B, A-C, B-D, C-D, D-E}

Graph:
    A
   / \
  B   C
   \ /
    D
    |
    E
```

### Key Vocabulary

| Term | Definition | Example |
|------|-----------|---------|
| **Vertex/Node** | A point in the graph | City in a map |
| **Edge** | A connection between two vertices | Road between cities |
| **Neighbor/Adjacent** | Nodes directly connected by an edge | B is a neighbor of A if A-B is an edge |
| **Degree** | Number of edges connected to a node | If A connects to B,C,D → degree = 3 |
| **Path** | A sequence of vertices connected by edges | A → B → D → E |
| **Shortest Path** | Path with fewest edges (unweighted) | The minimum-hop route |
| **Distance** | Number of edges in the shortest path | dist(A,E) = 3 |
| **Connected** | Every pair of nodes has a path | All nodes reachable |
| **Component** | A maximal connected subgraph | Island of connected nodes |
| **Cycle** | A path that starts and ends at the same node | A → B → C → A |
| **DAG** | Directed Acyclic Graph — no cycles, edges are one-way | Task dependencies |
| **Tree** | Connected graph with no cycles | N nodes, N-1 edges |
| **Root** | Starting node of a tree | Top of the hierarchy |
| **Level** | Distance from root in a tree | Root = level 0 |
| **Leaf** | Node with no children | Node at the bottom |

### Graph Representations

**Adjacency List** (preferred for sparse graphs):
```
A → [B, C]
B → [A, D]
C → [A, D]
D → [B, C, E]
E → [D]
```

**Adjacency Matrix** (preferred for dense graphs):
```
    A  B  C  D  E
A [ 0, 1, 1, 0, 0 ]
B [ 1, 0, 0, 1, 0 ]
C [ 1, 0, 0, 1, 0 ]
D [ 0, 1, 1, 0, 1 ]
E [ 0, 0, 0, 1, 0 ]
```

### Directed vs Undirected

```
Undirected: A -- B  (can go both ways)
Directed:   A --> B (can only go A to B)
```

---

## 4. BFS — The Core Algorithm

### The Big Idea

BFS explores a graph **level by level**, like an expanding ripple:
1. Start at the source node (level 0).
2. Visit all nodes at distance 1 (direct neighbors) → level 1.
3. Visit all nodes at distance 2 → level 2.
4. Continue until target found or all nodes visited.

### The Visited Array — Preventing Infinite Loops

Graphs can have **cycles** (A→B→C→A). Without tracking visited nodes, BFS would loop forever. The `visited` array (or set) marks nodes that have already been enqueued, so they are never processed twice.

**Critical insight**: Mark a node as visited **when you enqueue it**, not when you dequeue it. This prevents duplicates in the queue.

```
Wrong: Mark visited when dequeuing → Same node can be enqueued multiple times
Right: Mark visited when enqueuing → Node enqueued exactly once
```

### Pseudocode

```
BFS(graph, source):
    visited = empty set
    queue   = empty queue
    
    visited.add(source)
    queue.enqueue(source)
    
    while queue is not empty:
        node = queue.dequeue()
        process(node)                    ← do your work here
        
        for each neighbor of node:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.enqueue(neighbor)
```

### BFS with Distance Tracking

```
BFS_with_distance(graph, source):
    dist    = map: all nodes → infinity
    queue   = empty queue
    
    dist[source] = 0
    queue.enqueue(source)
    
    while queue is not empty:
        node = queue.dequeue()
        
        for each neighbor of node:
            if dist[neighbor] == infinity:     ← unvisited
                dist[neighbor] = dist[node] + 1
                queue.enqueue(neighbor)
    
    return dist
```

### BFS with Path Reconstruction

```
BFS_shortest_path(graph, source, target):
    parent  = map: all nodes → null
    visited = empty set
    queue   = empty queue
    
    visited.add(source)
    queue.enqueue(source)
    
    while queue is not empty:
        node = queue.dequeue()
        
        if node == target:
            return reconstruct_path(parent, source, target)
        
        for each neighbor of node:
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = node     ← track who discovered this node
                queue.enqueue(neighbor)
    
    return null  ← no path exists

reconstruct_path(parent, source, target):
    path = []
    curr = target
    while curr != null:
        path.prepend(curr)
        curr = parent[curr]
    return path
```

---

## 5. ASCII Visualizations

### Example Graph

```
    1
   / \
  2   3
 / \   \
4   5   6
    |
    7
```

Adjacency List:
```
1 → [2, 3]
2 → [1, 4, 5]
3 → [1, 6]
4 → [2]
5 → [2, 7]
6 → [3]
7 → [5]
```

### BFS Step-by-Step from Node 1

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 0: Initialize
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Queue:    [ 1 ]
Visited:  { 1 }
Distance: { 1:0 }
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 1: Dequeue 1, process neighbors [2, 3]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Enqueue 2 (not visited), dist[2] = 1
  Enqueue 3 (not visited), dist[3] = 1
Queue:    [ 2, 3 ]
Visited:  { 1, 2, 3 }
Distance: { 1:0, 2:1, 3:1 }
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 2: Dequeue 2, process neighbors [1, 4, 5]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Skip 1 (already visited)
  Enqueue 4 (not visited), dist[4] = 2
  Enqueue 5 (not visited), dist[5] = 2
Queue:    [ 3, 4, 5 ]
Visited:  { 1, 2, 3, 4, 5 }
Distance: { 1:0, 2:1, 3:1, 4:2, 5:2 }
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 3: Dequeue 3, process neighbors [1, 6]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Skip 1 (already visited)
  Enqueue 6 (not visited), dist[6] = 2
Queue:    [ 4, 5, 6 ]
Visited:  { 1, 2, 3, 4, 5, 6 }
Distance: { 1:0, 2:1, 3:1, 4:2, 5:2, 6:2 }
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 4: Dequeue 4, process neighbors [2]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Skip 2 (already visited)
Queue:    [ 5, 6 ]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 5: Dequeue 5, process neighbors [2, 7]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Skip 2 (already visited)
  Enqueue 7 (not visited), dist[7] = 3
Queue:    [ 6, 7 ]
Visited:  { 1, 2, 3, 4, 5, 6, 7 }
Distance: { 1:0, 2:1, 3:1, 4:2, 5:2, 6:2, 7:3 }
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 6: Dequeue 6, process neighbors [3]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Skip 3 (already visited)
Queue:    [ 7 ]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 7: Dequeue 7, process neighbors [5]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Skip 5 (already visited)
Queue:    []  ← EMPTY, BFS complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BFS ORDER: 1 → 2 → 3 → 4 → 5 → 6 → 7

LEVEL MAP:
  Level 0:  [1]
  Level 1:  [2, 3]
  Level 2:  [4, 5, 6]
  Level 3:  [7]
```

### Visual Queue State During BFS

```
Time →

Queue State:
t=0  [ 1                   ]  ← start
t=1  [ 2 3                 ]  ← after processing 1
t=2  [ 3 4 5               ]  ← after processing 2
t=3  [ 4 5 6               ]  ← after processing 3
t=4  [ 5 6                 ]  ← after processing 4
t=5  [ 6 7                 ]  ← after processing 5
t=6  [ 7                   ]  ← after processing 6
t=7  [                     ]  ← after processing 7 → DONE
      ^
      front of queue
```

---

## 6. Algorithm Flowcharts

### Main BFS Flowchart

```
                    ┌─────────────────────┐
                    │       START         │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Initialize Queue   │
                    │  Enqueue source     │
                    │  Mark source visited│
                    └──────────┬──────────┘
                               │
              ┌────────────────▼─────────────────┐
              │         Is Queue Empty?           │
              └──────┬─────────────────┬──────────┘
                     │ YES             │ NO
                     ▼                 ▼
              ┌──────────┐   ┌─────────────────────┐
              │   END    │   │  Dequeue front node │
              └──────────┘   └──────────┬──────────┘
                                        │
                             ┌──────────▼──────────┐
                             │   Process node      │
                             │  (record dist, etc) │
                             └──────────┬──────────┘
                                        │
                             ┌──────────▼──────────┐
                             │  Get all neighbors  │
                             └──────────┬──────────┘
                                        │
                        ┌───────────────▼──────────────────┐
                        │  For each neighbor N:            │
                        │  ┌────────────────────────────┐  │
                        │  │  Is N already visited?     │  │
                        │  └──────┬──────────────┬──────┘  │
                        │        │YES           │NO        │
                        │        ▼              ▼          │
                        │    [Skip N]   [Mark N visited]   │
                        │               [Enqueue N]        │
                        └──────────────────────────────────┘
                                        │
                             (loop back to queue check)
```

### Decision Tree: Which BFS Variant?

```
Is the graph unweighted?
├── YES → Standard BFS
│         ├── One source?     → Single-source BFS
│         ├── Many sources?   → Multi-source BFS
│         └── Find shortest path both ways? → Bidirectional BFS
└── NO  → Is edge weight 0 or 1 only?
          ├── YES → 0-1 BFS (Deque)
          └── NO  → Is edge weight small integer?
                    ├── YES → Modified BFS (repeated edges)
                    └── NO  → Dijkstra / Bellman-Ford
```

---

## 7. Complexity Analysis

### Time Complexity: O(V + E)

- **V** = number of vertices
- **E** = number of edges

Each vertex is enqueued and dequeued **exactly once** → O(V)  
Each edge is examined **at most twice** (once from each endpoint in undirected graphs) → O(E)  
Total: **O(V + E)**

### Space Complexity: O(V)

| Data Structure | Space |
|---------------|-------|
| Queue (worst case, all nodes enqueued) | O(V) |
| Visited array/set | O(V) |
| Distance array | O(V) |
| Parent array (for path reconstruction) | O(V) |
| **Total** | **O(V)** |

### BFS Tree Width

The **maximum queue size** at any point equals the **maximum number of nodes at any single level** in the BFS tree. This is the **width** of the graph at that level.

For a balanced binary tree with N nodes:
- Maximum level width ≈ N/2 (the leaf level)
- So maximum queue size ≈ N/2 → O(N)

For a linear chain graph:
- Maximum level width = 1
- Queue never exceeds size 1

This contrast matters for **memory-bounded** problems.

---

## 8. Implementation in C

### Basic Queue Implementation

```c
/* ================================================================
 * BFS Comprehensive Implementation in C
 * Covers: Basic BFS, Distance Tracking, Path Reconstruction
 * ================================================================ */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

/* ───────────────────────────────────────────
 *  SECTION 1: Queue Data Structure
 * ─────────────────────────────────────────── */

#define MAX_NODES 1000

typedef struct {
    int  data[MAX_NODES];
    int  front;
    int  rear;
    int  size;
} Queue;

void queue_init(Queue *q) {
    q->front = 0;
    q->rear  = 0;
    q->size  = 0;
}

bool queue_is_empty(Queue *q) {
    return q->size == 0;
}

void queue_enqueue(Queue *q, int val) {
    if (q->size >= MAX_NODES) {
        fprintf(stderr, "Queue overflow!\n");
        exit(1);
    }
    q->data[q->rear] = val;
    q->rear  = (q->rear + 1) % MAX_NODES;   /* circular buffer */
    q->size++;
}

int queue_dequeue(Queue *q) {
    if (queue_is_empty(q)) {
        fprintf(stderr, "Queue underflow!\n");
        exit(1);
    }
    int val  = q->data[q->front];
    q->front = (q->front + 1) % MAX_NODES;
    q->size--;
    return val;
}

int queue_peek(Queue *q) {
    if (queue_is_empty(q)) {
        fprintf(stderr, "Queue is empty!\n");
        exit(1);
    }
    return q->data[q->front];
}

/* ───────────────────────────────────────────
 *  SECTION 2: Graph (Adjacency List)
 * ─────────────────────────────────────────── */

/*
 * What is an Adjacency List?
 * For each vertex, we store a linked list of its neighbors.
 * More memory-efficient than a matrix for sparse graphs.
 *
 *  Vertex 0 → [1] → [2] → NULL
 *  Vertex 1 → [0] → [3] → NULL
 *  etc.
 */

typedef struct AdjNode {
    int           dest;
    struct AdjNode *next;
} AdjNode;

typedef struct {
    AdjNode *head[MAX_NODES];
    int      num_vertices;
} Graph;

Graph* graph_create(int num_vertices) {
    Graph *g = (Graph *)malloc(sizeof(Graph));
    g->num_vertices = num_vertices;
    for (int i = 0; i < num_vertices; i++) {
        g->head[i] = NULL;
    }
    return g;
}

/* Add an undirected edge between u and v */
void graph_add_edge(Graph *g, int u, int v) {
    /* Add v to u's list */
    AdjNode *node_v = (AdjNode *)malloc(sizeof(AdjNode));
    node_v->dest = v;
    node_v->next = g->head[u];
    g->head[u]   = node_v;

    /* Add u to v's list (undirected) */
    AdjNode *node_u = (AdjNode *)malloc(sizeof(AdjNode));
    node_u->dest = u;
    node_u->next = g->head[v];
    g->head[v]   = node_u;
}

void graph_print(Graph *g) {
    printf("Graph Adjacency List:\n");
    for (int i = 0; i < g->num_vertices; i++) {
        printf("  %d → ", i);
        AdjNode *curr = g->head[i];
        while (curr) {
            printf("[%d] → ", curr->dest);
            curr = curr->next;
        }
        printf("NULL\n");
    }
}

void graph_free(Graph *g) {
    for (int i = 0; i < g->num_vertices; i++) {
        AdjNode *curr = g->head[i];
        while (curr) {
            AdjNode *tmp = curr;
            curr = curr->next;
            free(tmp);
        }
    }
    free(g);
}

/* ───────────────────────────────────────────
 *  SECTION 3: Basic BFS — Visit Order
 * ─────────────────────────────────────────── */

/*
 * BFS traversal from `source`.
 * Prints nodes in BFS discovery order.
 * Time:  O(V + E)
 * Space: O(V)
 */
void bfs_basic(Graph *g, int source) {
    bool  visited[MAX_NODES] = {false};
    Queue queue;
    queue_init(&queue);

    /* Step 1: Initialize with source */
    visited[source] = true;
    queue_enqueue(&queue, source);

    printf("BFS traversal from node %d:\n  ", source);

    /* Step 2: Process until queue is empty */
    while (!queue_is_empty(&queue)) {
        int node = queue_dequeue(&queue);
        printf("%d ", node);

        /* Step 3: Explore all neighbors */
        AdjNode *neighbor = g->head[node];
        while (neighbor) {
            if (!visited[neighbor->dest]) {
                visited[neighbor->dest] = true;
                queue_enqueue(&queue, neighbor->dest);
            }
            neighbor = neighbor->next;
        }
    }
    printf("\n");
}

/* ───────────────────────────────────────────
 *  SECTION 4: BFS with Distance Tracking
 * ─────────────────────────────────────────── */

/*
 * BFS with distance computation from `source`.
 * dist[v] = minimum number of edges from source to v.
 * dist[v] = -1 means unreachable.
 */
void bfs_distances(Graph *g, int source, int dist[]) {
    bool  visited[MAX_NODES] = {false};
    Queue queue;
    queue_init(&queue);

    /* Initialize all distances as "unreachable" */
    for (int i = 0; i < g->num_vertices; i++) {
        dist[i] = -1;
    }

    dist[source]    = 0;
    visited[source] = true;
    queue_enqueue(&queue, source);

    while (!queue_is_empty(&queue)) {
        int node = queue_dequeue(&queue);

        AdjNode *neighbor = g->head[node];
        while (neighbor) {
            int nb = neighbor->dest;
            if (!visited[nb]) {
                visited[nb]  = true;
                dist[nb]     = dist[node] + 1;
                queue_enqueue(&queue, nb);
            }
            neighbor = neighbor->next;
        }
    }
}

/* ───────────────────────────────────────────
 *  SECTION 5: BFS Shortest Path (with parent tracking)
 * ─────────────────────────────────────────── */

/*
 * What is "parent tracking"?
 * For each node, we record WHICH node first discovered it.
 * Then we can walk backwards from target → source to reconstruct the path.
 *
 * parent[v] = the node that discovered v during BFS
 * parent[source] = -1 (no parent)
 */
bool bfs_shortest_path(Graph *g, int source, int target,
                        int parent[], int dist[]) {
    bool  visited[MAX_NODES] = {false};
    Queue queue;
    queue_init(&queue);

    for (int i = 0; i < g->num_vertices; i++) {
        parent[i] = -1;
        dist[i]   = -1;
    }

    dist[source]    = 0;
    visited[source] = true;
    queue_enqueue(&queue, source);

    while (!queue_is_empty(&queue)) {
        int node = queue_dequeue(&queue);

        if (node == target) {
            return true;   /* Found target! */
        }

        AdjNode *neighbor = g->head[node];
        while (neighbor) {
            int nb = neighbor->dest;
            if (!visited[nb]) {
                visited[nb]    = true;
                dist[nb]       = dist[node] + 1;
                parent[nb]     = node;
                queue_enqueue(&queue, nb);
            }
            neighbor = neighbor->next;
        }
    }
    return false;   /* Target not reachable */
}

/* Reconstruct and print the path from source to target */
void print_path(int parent[], int source, int target) {
    if (target == source) {
        printf("%d", source);
        return;
    }
    if (parent[target] == -1) {
        printf("No path exists from %d to %d\n", source, target);
        return;
    }
    print_path(parent, source, parent[target]);
    printf(" → %d", target);
}

/* ───────────────────────────────────────────
 *  SECTION 6: BFS Level-by-Level
 * ─────────────────────────────────────────── */

/*
 * Technique: Use queue size to determine level boundaries.
 * At the start of processing a level, the queue contains
 * EXACTLY all nodes of the current level.
 * Process `level_size` nodes, then increment level.
 */
void bfs_levels(Graph *g, int source) {
    bool  visited[MAX_NODES] = {false};
    Queue queue;
    queue_init(&queue);

    visited[source] = true;
    queue_enqueue(&queue, source);

    int level = 0;

    while (!queue_is_empty(&queue)) {
        int level_size = queue.size;   /* All nodes of current level */
        printf("Level %d: ", level);

        for (int i = 0; i < level_size; i++) {
            int node = queue_dequeue(&queue);
            printf("%d ", node);

            AdjNode *neighbor = g->head[node];
            while (neighbor) {
                int nb = neighbor->dest;
                if (!visited[nb]) {
                    visited[nb] = true;
                    queue_enqueue(&queue, nb);
                }
                neighbor = neighbor->next;
            }
        }
        printf("\n");
        level++;
    }
}

/* ───────────────────────────────────────────
 *  SECTION 7: BFS Connectivity Check
 * ─────────────────────────────────────────── */

/*
 * Count connected components using BFS.
 * A "connected component" is a maximal group of nodes
 * where every pair is connected by some path.
 *
 * Strategy: Run BFS from each unvisited node.
 * Each BFS run discovers one complete component.
 */
int bfs_count_components(Graph *g) {
    bool  visited[MAX_NODES] = {false};
    Queue queue;
    int   components = 0;

    for (int start = 0; start < g->num_vertices; start++) {
        if (!visited[start]) {
            components++;
            queue_init(&queue);
            visited[start] = true;
            queue_enqueue(&queue, start);

            while (!queue_is_empty(&queue)) {
                int node = queue_dequeue(&queue);
                AdjNode *nb = g->head[node];
                while (nb) {
                    if (!visited[nb->dest]) {
                        visited[nb->dest] = true;
                        queue_enqueue(&queue, nb->dest);
                    }
                    nb = nb->next;
                }
            }
        }
    }
    return components;
}

/* ───────────────────────────────────────────
 *  SECTION 8: Demo / Main
 * ─────────────────────────────────────────── */

int main(void) {
    /*
     * Build this graph:
     *     0
     *    / \
     *   1   2
     *  / \   \
     * 3   4   5
     *     |
     *     6
     */
    Graph *g = graph_create(7);
    graph_add_edge(g, 0, 1);
    graph_add_edge(g, 0, 2);
    graph_add_edge(g, 1, 3);
    graph_add_edge(g, 1, 4);
    graph_add_edge(g, 2, 5);
    graph_add_edge(g, 4, 6);

    graph_print(g);
    printf("\n");

    /* Basic BFS */
    bfs_basic(g, 0);
    printf("\n");

    /* Level-by-level BFS */
    printf("Level-by-level BFS from node 0:\n");
    bfs_levels(g, 0);
    printf("\n");

    /* Distances */
    int dist[MAX_NODES];
    bfs_distances(g, 0, dist);
    printf("Distances from node 0:\n");
    for (int i = 0; i < 7; i++) {
        printf("  dist[%d] = %d\n", i, dist[i]);
    }
    printf("\n");

    /* Shortest path */
    int parent[MAX_NODES];
    printf("Shortest path from 0 to 6:\n  ");
    if (bfs_shortest_path(g, 0, 6, parent, dist)) {
        print_path(parent, 0, 6);
        printf("  (distance: %d)\n", dist[6]);
    }
    printf("\n");

    /* Connected components */
    printf("Number of connected components: %d\n",
           bfs_count_components(g));

    graph_free(g);
    return 0;
}
```

### Expected Output

```
Graph Adjacency List:
  0 → [2] → [1] → NULL
  1 → [4] → [3] → [0] → NULL
  2 → [5] → [0] → NULL
  3 → [1] → NULL
  4 → [6] → [1] → NULL
  5 → [2] → NULL
  6 → [4] → NULL

BFS traversal from node 0:
  0 2 1 5 4 3 6

Level-by-level BFS from node 0:
Level 0: 0
Level 1: 2 1
Level 2: 5 4 3
Level 3: 6

Distances from node 0:
  dist[0] = 0
  dist[1] = 1
  dist[2] = 1
  dist[3] = 2
  dist[4] = 2
  dist[5] = 2
  dist[6] = 3

Shortest path from 0 to 6:
  0 → 1 → 4 → 6  (distance: 3)

Number of connected components: 1
```

---

## 9. Implementation in Go

```go
// ================================================================
// BFS Comprehensive Implementation in Go
// Covers: Basic BFS, Distance, Path Reconstruction, Grid BFS
// ================================================================

package main

import "fmt"

// ───────────────────────────────────────────
//  SECTION 1: Queue using a slice
// ───────────────────────────────────────────

// Go's built-in slice acts as a dynamic queue.
// Enqueue: append to tail
// Dequeue: slice off the head
// NOTE: For production code, use a ring buffer or container/list
//       for O(1) amortized operations.

type Queue struct {
	data []int
}

func (q *Queue) IsEmpty() bool {
	return len(q.data) == 0
}

func (q *Queue) Enqueue(val int) {
	q.data = append(q.data, val)
}

func (q *Queue) Dequeue() int {
	if q.IsEmpty() {
		panic("dequeue from empty queue")
	}
	val    := q.data[0]
	q.data  = q.data[1:] // advance the slice head
	return val
}

func (q *Queue) Size() int {
	return len(q.data)
}

// ───────────────────────────────────────────
//  SECTION 2: Graph (Adjacency List with map)
// ───────────────────────────────────────────

// In Go, we represent the graph as a map:
//   map[int][]int
// key   = vertex ID
// value = slice of neighbor IDs

type Graph struct {
	adj map[int][]int
}

func NewGraph() *Graph {
	return &Graph{adj: make(map[int][]int)}
}

// AddEdge adds an undirected edge between u and v.
func (g *Graph) AddEdge(u, v int) {
	g.adj[u] = append(g.adj[u], v)
	g.adj[v] = append(g.adj[v], u)
}

// AddDirectedEdge adds a one-way edge from u to v.
func (g *Graph) AddDirectedEdge(u, v int) {
	g.adj[u] = append(g.adj[u], v)
}

// ───────────────────────────────────────────
//  SECTION 3: Basic BFS
// ───────────────────────────────────────────

func (g *Graph) BFS(source int) []int {
	visited := make(map[int]bool)
	order   := []int{}
	queue   := &Queue{}

	visited[source] = true
	queue.Enqueue(source)

	for !queue.IsEmpty() {
		node := queue.Dequeue()
		order = append(order, node)

		for _, neighbor := range g.adj[node] {
			if !visited[neighbor] {
				visited[neighbor] = true
				queue.Enqueue(neighbor)
			}
		}
	}
	return order
}

// ───────────────────────────────────────────
//  SECTION 4: BFS with Distances
// ───────────────────────────────────────────

// BFSDistances returns a map of node → shortest distance from source.
// Unreachable nodes will not appear in the map.
func (g *Graph) BFSDistances(source int) map[int]int {
	dist  := make(map[int]int)
	queue := &Queue{}

	dist[source] = 0
	queue.Enqueue(source)

	for !queue.IsEmpty() {
		node := queue.Dequeue()

		for _, neighbor := range g.adj[node] {
			if _, seen := dist[neighbor]; !seen {
				dist[neighbor] = dist[node] + 1
				queue.Enqueue(neighbor)
			}
		}
	}
	return dist
}

// ───────────────────────────────────────────
//  SECTION 5: BFS Shortest Path
// ───────────────────────────────────────────

// BFSShortestPath returns the shortest path from source to target.
// Returns nil if no path exists.
func (g *Graph) BFSShortestPath(source, target int) []int {
	parent := make(map[int]int)   // parent[v] = who discovered v
	dist   := make(map[int]int)
	queue  := &Queue{}

	dist[source]   = 0
	parent[source] = -1
	queue.Enqueue(source)

	found := false
	for !queue.IsEmpty() {
		node := queue.Dequeue()

		if node == target {
			found = true
			break
		}

		for _, neighbor := range g.adj[node] {
			if _, seen := dist[neighbor]; !seen {
				dist[neighbor]   = dist[node] + 1
				parent[neighbor] = node
				queue.Enqueue(neighbor)
			}
		}
	}

	if !found {
		return nil
	}

	// Reconstruct path by walking parent pointers backwards.
	path := []int{}
	curr := target
	for curr != -1 {
		path = append([]int{curr}, path...) // prepend
		curr = parent[curr]
	}
	return path
}

// ───────────────────────────────────────────
//  SECTION 6: BFS Level-by-Level
// ───────────────────────────────────────────

// BFSLevels returns a 2D slice where levels[i] = all nodes at distance i.
func (g *Graph) BFSLevels(source int) [][]int {
	dist   := make(map[int]int)
	queue  := &Queue{}
	levels := [][]int{}

	dist[source] = 0
	queue.Enqueue(source)

	for !queue.IsEmpty() {
		levelSize := queue.Size()
		level     := []int{}

		// Process exactly `levelSize` nodes = one complete level.
		for i := 0; i < levelSize; i++ {
			node := queue.Dequeue()
			level = append(level, node)

			for _, neighbor := range g.adj[node] {
				if _, seen := dist[neighbor]; !seen {
					dist[neighbor] = dist[node] + 1
					queue.Enqueue(neighbor)
				}
			}
		}
		levels = append(levels, level)
	}
	return levels
}

// ───────────────────────────────────────────
//  SECTION 7: BFS on a 2D Grid
// ───────────────────────────────────────────

/*
 * Grid BFS is extremely common in competitive programming.
 * Cells are nodes. Adjacent cells (up/down/left/right) are edges.
 *
 * Problem: Find shortest path from (sr,sc) to (er,ec)
 * '#' = wall (blocked), '.' = open cell
 *
 * Key insight: Instead of a graph adjacency list, we compute
 * neighbors "on the fly" using directional offsets.
 */

type Point struct {
	row, col int
}

// 4-directional movement: up, down, left, right
var directions = []Point{{-1, 0}, {1, 0}, {0, -1}, {0, 1}}

type GridQueue struct {
	data []Point
}

func (q *GridQueue) IsEmpty() bool       { return len(q.data) == 0 }
func (q *GridQueue) Enqueue(p Point)     { q.data = append(q.data, p) }
func (q *GridQueue) Dequeue() Point {
	p      := q.data[0]
	q.data  = q.data[1:]
	return p
}
func (q *GridQueue) Size() int { return len(q.data) }

func GridBFS(grid [][]byte, sr, sc, er, ec int) int {
	rows := len(grid)
	cols := len(grid[0])

	if grid[sr][sc] == '#' || grid[er][ec] == '#' {
		return -1
	}

	dist  := make([][]int, rows)
	for i := range dist {
		dist[i] = make([]int, cols)
		for j := range dist[i] {
			dist[i][j] = -1
		}
	}

	queue := &GridQueue{}
	start := Point{sr, sc}
	dist[sr][sc] = 0
	queue.Enqueue(start)

	for !queue.IsEmpty() {
		curr := queue.Dequeue()

		if curr.row == er && curr.col == ec {
			return dist[er][ec]
		}

		for _, dir := range directions {
			nr := curr.row + dir.row
			nc := curr.col + dir.col

			// Bounds check + wall check + unvisited check
			if nr >= 0 && nr < rows &&
				nc >= 0 && nc < cols &&
				grid[nr][nc] != '#' &&
				dist[nr][nc] == -1 {

				dist[nr][nc] = dist[curr.row][curr.col] + 1
				queue.Enqueue(Point{nr, nc})
			}
		}
	}
	return -1 // target unreachable
}

// ───────────────────────────────────────────
//  SECTION 8: Multi-Source BFS
// ───────────────────────────────────────────

/*
 * Multi-Source BFS: Start BFS from MULTIPLE sources simultaneously.
 * Use case: "Find the minimum distance from ANY source to each cell."
 * Example: Rotting oranges — multiple rotten oranges spread simultaneously.
 *
 * Trick: Enqueue ALL sources at the start with distance 0.
 * BFS then naturally spreads from all of them at the same time.
 */

func MultiSourceBFS(grid [][]byte, sources []Point) [][]int {
	rows := len(grid)
	cols := len(grid[0])

	dist := make([][]int, rows)
	for i := range dist {
		dist[i] = make([]int, cols)
		for j := range dist[i] {
			dist[i][j] = -1
		}
	}

	queue := &GridQueue{}

	// Enqueue ALL sources at distance 0
	for _, src := range sources {
		dist[src.row][src.col] = 0
		queue.Enqueue(src)
	}

	for !queue.IsEmpty() {
		curr := queue.Dequeue()
		for _, dir := range directions {
			nr := curr.row + dir.row
			nc := curr.col + dir.col
			if nr >= 0 && nr < rows &&
				nc >= 0 && nc < cols &&
				grid[nr][nc] != '#' &&
				dist[nr][nc] == -1 {
				dist[nr][nc] = dist[curr.row][curr.col] + 1
				queue.Enqueue(Point{nr, nc})
			}
		}
	}
	return dist
}

// ───────────────────────────────────────────
//  SECTION 9: Demo
// ───────────────────────────────────────────

func main() {
	g := NewGraph()
	g.AddEdge(0, 1)
	g.AddEdge(0, 2)
	g.AddEdge(1, 3)
	g.AddEdge(1, 4)
	g.AddEdge(2, 5)
	g.AddEdge(4, 6)

	fmt.Printf("BFS order from 0: %v\n", g.BFS(0))

	levels := g.BFSLevels(0)
	fmt.Println("BFS levels from 0:")
	for i, level := range levels {
		fmt.Printf("  Level %d: %v\n", i, level)
	}

	dist := g.BFSDistances(0)
	fmt.Println("Distances from 0:")
	for v, d := range dist {
		fmt.Printf("  dist[%d] = %d\n", v, d)
	}

	path := g.BFSShortestPath(0, 6)
	fmt.Printf("Shortest path 0→6: %v\n", path)

	// Grid BFS demo
	grid := [][]byte{
		{'.',  '.', '#', '.', '.'},
		{'.',  '.', '.', '.', '#'},
		{'#',  '.', '#', '.', '.'},
		{'.',  '.', '.', '#', '.'},
		{'.',  '#', '.', '.', '.'},
	}
	result := GridBFS(grid, 0, 0, 4, 4)
	fmt.Printf("Grid BFS shortest path (0,0)→(4,4): %d steps\n", result)
}
```

---

## 10. Implementation in Rust

```rust
// ================================================================
// BFS Comprehensive Implementation in Rust
// Covers: Basic BFS, Distances, Path, Grid, Components
// ================================================================

use std::collections::{HashMap, HashSet, VecDeque};

// ───────────────────────────────────────────
//  SECTION 1: Graph Structure
// ───────────────────────────────────────────

/*
 * In Rust, we use:
 *   VecDeque<T>  → efficient double-ended queue (O(1) push_back, pop_front)
 *   HashMap      → adjacency list (node → list of neighbors)
 *   HashSet      → visited tracking
 *
 * VecDeque is the canonical queue in Rust.
 *   push_back  = enqueue
 *   pop_front  = dequeue
 */

#[derive(Debug)]
struct Graph {
    /// adjacency list: node_id → [neighbor_ids]
    adj: HashMap<usize, Vec<usize>>,
    /// total number of vertices
    num_vertices: usize,
}

impl Graph {
    fn new(n: usize) -> Self {
        let mut adj = HashMap::new();
        for i in 0..n {
            adj.insert(i, vec![]);
        }
        Graph { adj, num_vertices: n }
    }

    /// Add undirected edge
    fn add_edge(&mut self, u: usize, v: usize) {
        self.adj.entry(u).or_default().push(v);
        self.adj.entry(v).or_default().push(u);
    }

    /// Add directed edge (one-way)
    fn add_directed_edge(&mut self, u: usize, v: usize) {
        self.adj.entry(u).or_default().push(v);
    }

    fn neighbors(&self, node: usize) -> &[usize] {
        self.adj.get(&node).map_or(&[], Vec::as_slice)
    }
}

// ───────────────────────────────────────────
//  SECTION 2: Basic BFS
// ───────────────────────────────────────────

/// Returns nodes in BFS discovery order from `source`.
fn bfs_basic(graph: &Graph, source: usize) -> Vec<usize> {
    let mut visited: HashSet<usize> = HashSet::new();
    let mut queue:   VecDeque<usize> = VecDeque::new();
    let mut order:   Vec<usize>      = Vec::new();

    visited.insert(source);
    queue.push_back(source);

    while let Some(node) = queue.pop_front() {
        order.push(node);

        for &neighbor in graph.neighbors(node) {
            if !visited.contains(&neighbor) {
                visited.insert(neighbor);
                queue.push_back(neighbor);
            }
        }
    }
    order
}

// ───────────────────────────────────────────
//  SECTION 3: BFS with Distances
// ───────────────────────────────────────────

/// Returns distances from `source` to all reachable nodes.
/// Unreachable nodes are absent from the returned map.
fn bfs_distances(graph: &Graph, source: usize) -> HashMap<usize, usize> {
    let mut dist:  HashMap<usize, usize> = HashMap::new();
    let mut queue: VecDeque<usize>       = VecDeque::new();

    dist.insert(source, 0);
    queue.push_back(source);

    while let Some(node) = queue.pop_front() {
        let current_dist = dist[&node];

        for &neighbor in graph.neighbors(node) {
            if !dist.contains_key(&neighbor) {
                dist.insert(neighbor, current_dist + 1);
                queue.push_back(neighbor);
            }
        }
    }
    dist
}

// ───────────────────────────────────────────
//  SECTION 4: BFS Shortest Path
// ───────────────────────────────────────────

/*
 * Returns the shortest path as a Vec<usize>, or None if unreachable.
 *
 * Rust Note: We use Option<usize> for parent tracking.
 *   - None  = no parent (this is the source)
 *   - Some(p) = discovered by node p
 */
fn bfs_shortest_path(
    graph:  &Graph,
    source: usize,
    target: usize,
) -> Option<Vec<usize>> {
    let mut parent: HashMap<usize, Option<usize>> = HashMap::new();
    let mut queue:  VecDeque<usize>               = VecDeque::new();

    parent.insert(source, None);
    queue.push_back(source);

    while let Some(node) = queue.pop_front() {
        if node == target {
            // Reconstruct path
            let mut path = Vec::new();
            let mut curr = target;
            loop {
                path.push(curr);
                match parent[&curr] {
                    None    => break,
                    Some(p) => curr = p,
                }
            }
            path.reverse();
            return Some(path);
        }

        for &neighbor in graph.neighbors(node) {
            if !parent.contains_key(&neighbor) {
                parent.insert(neighbor, Some(node));
                queue.push_back(neighbor);
            }
        }
    }
    None  // target not reachable
}

// ───────────────────────────────────────────
//  SECTION 5: BFS Level-by-Level
// ───────────────────────────────────────────

/// Returns a Vec of levels: levels[i] = all nodes at distance i from source.
fn bfs_levels(graph: &Graph, source: usize) -> Vec<Vec<usize>> {
    let mut dist:   HashMap<usize, usize> = HashMap::new();
    let mut queue:  VecDeque<usize>       = VecDeque::new();
    let mut levels: Vec<Vec<usize>>       = Vec::new();

    dist.insert(source, 0);
    queue.push_back(source);

    while !queue.is_empty() {
        let level_size = queue.len();
        let mut level  = Vec::with_capacity(level_size);

        for _ in 0..level_size {
            let node = queue.pop_front().unwrap();
            level.push(node);

            let curr_dist = dist[&node];
            for &neighbor in graph.neighbors(node) {
                if !dist.contains_key(&neighbor) {
                    dist.insert(neighbor, curr_dist + 1);
                    queue.push_back(neighbor);
                }
            }
        }
        levels.push(level);
    }
    levels
}

// ───────────────────────────────────────────
//  SECTION 6: Connected Components
// ───────────────────────────────────────────

/// Returns the number of connected components.
fn bfs_count_components(graph: &Graph) -> usize {
    let mut visited:    HashSet<usize> = HashSet::new();
    let mut components: usize         = 0;

    for start in 0..graph.num_vertices {
        if !visited.contains(&start) {
            components += 1;
            let mut queue: VecDeque<usize> = VecDeque::new();
            visited.insert(start);
            queue.push_back(start);

            while let Some(node) = queue.pop_front() {
                for &neighbor in graph.neighbors(node) {
                    if !visited.contains(&neighbor) {
                        visited.insert(neighbor);
                        queue.push_back(neighbor);
                    }
                }
            }
        }
    }
    components
}

// ───────────────────────────────────────────
//  SECTION 7: BFS on a 2D Grid
// ───────────────────────────────────────────

/*
 * Grid BFS in Rust:
 * - Represent grid as Vec<Vec<char>>
 * - Use (usize, usize) or (i32, i32) for coordinates
 * - Use i32 for coordinates to easily check bounds without underflow
 */

const DIRECTIONS: [(i32, i32); 4] = [(-1,0),(1,0),(0,-1),(0,1)];

fn grid_bfs(
    grid: &[Vec<char>],
    start: (usize, usize),
    end:   (usize, usize),
) -> Option<usize> {
    let rows = grid.len() as i32;
    let cols = grid[0].len() as i32;

    let (sr, sc) = start;
    let (er, ec) = end;

    if grid[sr][sc] == '#' || grid[er][ec] == '#' {
        return None;
    }

    // dist[r][c] = shortest distance, u32::MAX = unvisited
    let mut dist = vec![vec![u32::MAX; cols as usize]; rows as usize];
    let mut queue: VecDeque<(usize, usize)> = VecDeque::new();

    dist[sr][sc] = 0;
    queue.push_back((sr, sc));

    while let Some((r, c)) = queue.pop_front() {
        if r == er && c == ec {
            return Some(dist[er][ec] as usize);
        }

        for &(dr, dc) in &DIRECTIONS {
            let nr = r as i32 + dr;
            let nc = c as i32 + dc;

            if nr >= 0 && nr < rows && nc >= 0 && nc < cols {
                let (nr, nc) = (nr as usize, nc as usize);
                if grid[nr][nc] != '#' && dist[nr][nc] == u32::MAX {
                    dist[nr][nc] = dist[r][c] + 1;
                    queue.push_back((nr, nc));
                }
            }
        }
    }
    None
}

// ───────────────────────────────────────────
//  SECTION 8: 0-1 BFS using VecDeque
// ───────────────────────────────────────────

/*
 * 0-1 BFS: Edge weights are either 0 or 1 only.
 * More efficient than Dijkstra for this special case.
 *
 * Key insight:
 * - Weight-0 edge: neighbor is "as close as" current node → push_front
 * - Weight-1 edge: neighbor is one step farther → push_back
 *
 * This maintains the invariant: queue is always sorted by distance.
 */

#[derive(Debug, Clone)]
struct WeightedEdge {
    to:     usize,
    weight: u32,  // 0 or 1 only
}

fn bfs_01(
    adj:    &[Vec<WeightedEdge>],
    source: usize,
    n:      usize,
) -> Vec<u32> {
    let mut dist:  Vec<u32>             = vec![u32::MAX; n];
    let mut deque: VecDeque<usize>      = VecDeque::new();

    dist[source] = 0;
    deque.push_back(source);

    while let Some(node) = deque.pop_front() {
        for edge in &adj[node] {
            let new_dist = dist[node] + edge.weight;
            if new_dist < dist[edge.to] {
                dist[edge.to] = new_dist;
                if edge.weight == 0 {
                    deque.push_front(edge.to);   // "free" edge — high priority
                } else {
                    deque.push_back(edge.to);    // cost-1 edge — normal priority
                }
            }
        }
    }
    dist
}

// ───────────────────────────────────────────
//  SECTION 9: Demo
// ───────────────────────────────────────────

fn main() {
    let mut g = Graph::new(7);
    g.add_edge(0, 1);
    g.add_edge(0, 2);
    g.add_edge(1, 3);
    g.add_edge(1, 4);
    g.add_edge(2, 5);
    g.add_edge(4, 6);

    println!("BFS order from 0:   {:?}", bfs_basic(&g, 0));

    let levels = bfs_levels(&g, 0);
    println!("BFS levels from 0:");
    for (i, level) in levels.iter().enumerate() {
        println!("  Level {}: {:?}", i, level);
    }

    let dist = bfs_distances(&g, 0);
    let mut dist_sorted: Vec<(usize, usize)> = dist.into_iter().collect();
    dist_sorted.sort();
    println!("Distances from 0: {:?}", dist_sorted);

    match bfs_shortest_path(&g, 0, 6) {
        Some(path) => println!("Shortest path 0→6: {:?}", path),
        None       => println!("No path from 0 to 6"),
    }

    println!("Connected components: {}", bfs_count_components(&g));

    // Grid BFS
    let grid = vec![
        vec!['.', '.', '#', '.', '.'],
        vec!['.', '.', '.', '.', '#'],
        vec!['#', '.', '#', '.', '.'],
        vec!['.', '.', '.', '#', '.'],
        vec!['.', '#', '.', '.', '.'],
    ];
    match grid_bfs(&grid, (0, 0), (4, 4)) {
        Some(d) => println!("Grid BFS (0,0)→(4,4): {} steps", d),
        None    => println!("No path in grid"),
    }
}
```

---

## 11. BFS on Trees (Level-Order Traversal)

A **tree** is a special graph: connected, undirected, with no cycles. BFS on a tree is called **level-order traversal**.

### Binary Tree Node

```
       1          ← Level 0
      / \
     2   3        ← Level 1
    / \ / \
   4  5 6  7     ← Level 2
```

### Level-Order Traversal in C

```c
/* Binary tree node */
typedef struct TreeNode {
    int val;
    struct TreeNode *left;
    struct TreeNode *right;
} TreeNode;

/*
 * Queue for TreeNode pointers.
 * Note: Here we store pointers, not integers.
 */
typedef struct {
    TreeNode *data[1000];
    int front, rear, size;
} TreeQueue;

/* ... (same queue operations as before, but storing TreeNode*) ... */

/*
 * Level-order traversal: Print nodes level by level.
 * Returns a 2D array of levels.
 */
void level_order(TreeNode *root) {
    if (!root) return;

    TreeQueue q = {.front=0, .rear=0, .size=0};
    /* enqueue/dequeue as before */

    q.data[q.rear++] = root;
    q.size++;

    while (q.size > 0) {
        int level_size = q.size;
        printf("[ ");
        for (int i = 0; i < level_size; i++) {
            TreeNode *node = q.data[q.front++];
            q.size--;
            printf("%d ", node->val);
            if (node->left) {
                q.data[q.rear++] = node->left;
                q.size++;
            }
            if (node->right) {
                q.data[q.rear++] = node->right;
                q.size++;
            }
        }
        printf("]\n");
    }
}
```

### Level-Order in Rust (Binary Tree)

```rust
use std::collections::VecDeque;

#[derive(Debug)]
struct TreeNode {
    val:   i32,
    left:  Option<Box<TreeNode>>,
    right: Option<Box<TreeNode>>,
}

impl TreeNode {
    fn new(val: i32) -> Box<Self> {
        Box::new(TreeNode { val, left: None, right: None })
    }
}

fn level_order(root: Option<&Box<TreeNode>>) -> Vec<Vec<i32>> {
    let mut result = Vec::new();
    let mut queue  = VecDeque::new();

    if let Some(node) = root {
        queue.push_back(node);
    }

    while !queue.is_empty() {
        let level_size = queue.len();
        let mut level  = Vec::new();

        for _ in 0..level_size {
            let node = queue.pop_front().unwrap();
            level.push(node.val);

            if let Some(left) = node.left.as_ref() {
                queue.push_back(left);
            }
            if let Some(right) = node.right.as_ref() {
                queue.push_back(right);
            }
        }
        result.push(level);
    }
    result
}
```

### Important Tree BFS Patterns

| Pattern | Technique |
|---------|-----------|
| Level order traversal | Process `queue.size()` nodes per level |
| Maximum width of tree | Track max level size |
| Right side view | Take last node of each level |
| Left side view | Take first node of each level |
| Average of each level | Sum nodes in level / level size |
| Zigzag level order | Alternate left-right, right-left |
| Minimum depth | Return level when first leaf found |

---

## 12. BFS on Grids / 2D Matrices

Grid problems are among the most common BFS applications in competitive programming.

### The Grid-as-Graph Mental Model

```
Grid Cell (r, c) = Node
Adjacent cells   = Edges

4-directional:          8-directional (includes diagonals):
    (r-1,c)                  (r-1,c-1)  (r-1,c)  (r-1,c+1)
       ↑                          ↖        ↑        ↗
(r,c-1)←(r,c)→(r,c+1)     (r,c-1) ←  (r,c)  → (r,c+1)
       ↓                          ↙        ↓        ↘
    (r+1,c)                  (r+1,c-1)  (r+1,c)  (r+1,c+1)
```

### Boundary Checking Pattern

```c
// C version — 4-directional
int dr[] = {-1, 1,  0, 0};
int dc[] = { 0, 0, -1, 1};

for (int d = 0; d < 4; d++) {
    int nr = r + dr[d];
    int nc = c + dc[d];
    if (nr >= 0 && nr < rows &&   /* within row bounds  */
        nc >= 0 && nc < cols &&   /* within col bounds  */
        grid[nr][nc] != '#'  &&   /* not a wall         */
        !visited[nr][nc]) {       /* not yet visited    */
        // valid neighbor!
    }
}
```

### Grid BFS Template (Go)

```go
func shortestPath(grid [][]byte, sr, sc, er, ec int) int {
    rows, cols := len(grid), len(grid[0])
    dirs := [][2]int{{-1,0},{1,0},{0,-1},{0,1}}

    type State struct{ r, c int }
    dist := make([][]int, rows)
    for i := range dist {
        dist[i] = make([]int, cols)
        for j := range dist[i] { dist[i][j] = -1 }
    }

    q := []State{{sr, sc}}
    dist[sr][sc] = 0

    for len(q) > 0 {
        cur := q[0]; q = q[1:]
        if cur.r == er && cur.c == ec { return dist[er][ec] }
        for _, d := range dirs {
            nr, nc := cur.r+d[0], cur.c+d[1]
            if nr >= 0 && nr < rows && nc >= 0 && nc < cols &&
                grid[nr][nc] != '#' && dist[nr][nc] == -1 {
                dist[nr][nc] = dist[cur.r][cur.c] + 1
                q = append(q, State{nr, nc})
            }
        }
    }
    return -1
}
```

---

## 13. Multi-Source BFS

### Concept

Instead of one starting point, you simultaneously start BFS from **multiple sources**.

All sources are enqueued at distance 0. BFS then expands outward from all of them simultaneously, computing the minimum distance from **any** source.

### ASCII Visualization

```
Grid (S = source, . = empty):

  . . . . .          . . . . .          0 1 2 3 4
  . . S . .    →     . . 0 . .    →     1 1 0 1 2
  . . . . .   BFS    . . . . .          2 1 1 1 2
  S . . . .          0 . . . .          0 1 2 2 3
  . . . . .          . . . . .          1 1 2 3 4

Two sources at (1,2) and (3,0).
Each cell shows the minimum distance to the nearest source.
```

### Use Cases

- Rotting Oranges (LeetCode 994)
- 01 Matrix — distance to nearest 0 (LeetCode 542)
- Distance to nearest gate in a maze
- Spreading fire/infection from multiple start points

---

## 14. 0-1 BFS

### When to Use It

When edge weights are **only 0 or 1**, standard BFS gives wrong distances, but Dijkstra is overkill. 0-1 BFS uses a **deque** (double-ended queue) and runs in O(V + E).

### The Insight

In normal BFS, every step costs 1 → queue is always ordered by distance.  
With 0-1 weights: a 0-weight edge means the neighbor is at the **same distance** as current. Push it to the **front** to process it at the same level. A 1-weight edge: push to the **back** as usual.

```
Deque state at distance d:
  front                              back
  [ nodes at dist d | nodes at dist d+1 ]

Process 0-weight neighbor → push_front (same distance)
Process 1-weight neighbor → push_back  (distance + 1)
```

### C Implementation of 0-1 BFS

```c
#include <stdio.h>
#include <limits.h>
#include <string.h>

#define MAXN 1000
#define INF  INT_MAX

/* Circular deque */
typedef struct {
    int data[MAXN * 2];
    int front, rear, size;
} Deque;

void deque_init(Deque *d) {
    d->front = MAXN;  /* start in the middle to allow push_front */
    d->rear  = MAXN;
    d->size  = 0;
}

void push_back(Deque *d, int val) {
    d->data[d->rear++] = val;
    d->size++;
}

void push_front(Deque *d, int val) {
    d->data[--d->front] = val;
    d->size++;
}

int pop_front(Deque *d) {
    d->size--;
    return d->data[d->front++];
}

bool deque_empty(Deque *d) { return d->size == 0; }

/* 0-1 BFS */
void bfs_01(int adj[][MAXN], int weight[][MAXN],
            int n, int source, int dist[]) {
    for (int i = 0; i < n; i++) dist[i] = INF;
    dist[source] = 0;

    Deque dq;
    deque_init(&dq);
    push_back(&dq, source);

    while (!deque_empty(&dq)) {
        int node = pop_front(&dq);
        for (int nb = 0; nb < n; nb++) {
            if (adj[node][nb] && dist[node] + weight[node][nb] < dist[nb]) {
                dist[nb] = dist[node] + weight[node][nb];
                if (weight[node][nb] == 0)
                    push_front(&dq, nb);   /* 0-weight: same level */
                else
                    push_back(&dq, nb);    /* 1-weight: next level */
            }
        }
    }
}
```

---

## 15. Bidirectional BFS

### Concept

Standard BFS from source S explores a ball of radius d.  
Bidirectional BFS runs two simultaneous BFS searches:
- **Forward BFS** from the source
- **Backward BFS** from the target

They meet somewhere in the middle.

### Why It's Faster

If the shortest path has length d:
- Standard BFS explores ≈ b^d nodes (b = branching factor)
- Bidirectional BFS explores ≈ 2 × b^(d/2) nodes

For b=10, d=6: 10^6 = 1,000,000 vs 2×10^3 = 2,000 → **500x speedup**.

### ASCII Visualization

```
Source S         Target T

   S . . . . . T

Standard BFS:
  S →→→→→→→→→ T   (explores all nodes up to distance d)

Bidirectional:
  S →→→  ←← T     (two frontiers meet in the middle)
       ↑↑
       meet here
```

### Bidirectional BFS in Go

```go
// BidirectionalBFS returns shortest distance from src to dst,
// or -1 if unreachable.
func BidirectionalBFS(adj map[int][]int, src, dst int) int {
    if src == dst {
        return 0
    }

    // Two visited sets with distances
    visitedFwd := map[int]int{src: 0}
    visitedBwd := map[int]int{dst: 0}
    queueFwd   := []int{src}
    queueBwd   := []int{dst}

    for len(queueFwd) > 0 && len(queueBwd) > 0 {
        // Always expand the smaller frontier
        if len(queueFwd) <= len(queueBwd) {
            if dist := expandLevel(adj, &queueFwd, visitedFwd, visitedBwd); dist != -1 {
                return dist
            }
        } else {
            if dist := expandLevel(adj, &queueBwd, visitedBwd, visitedFwd); dist != -1 {
                return dist
            }
        }
    }
    return -1
}

func expandLevel(adj map[int][]int, queue *[]int,
                 mine, other map[int]int) int {
    nextQueue := []int{}
    for _, node := range *queue {
        for _, nb := range adj[node] {
            if _, seen := mine[nb]; seen {
                continue
            }
            mine[nb] = mine[node] + 1
            if otherDist, found := other[nb]; found {
                return mine[nb] + otherDist  // paths met!
            }
            nextQueue = append(nextQueue, nb)
        }
    }
    *queue = nextQueue
    return -1
}
```

---

## 16. Shortest Path: Weighted vs Unweighted

### Key Rule

| Graph Type | Use |
|------------|-----|
| Unweighted (all edges cost 1) | BFS → O(V+E) |
| 0-1 weights | 0-1 BFS → O(V+E) |
| Non-negative weights | Dijkstra → O((V+E) log V) |
| Negative weights (no negative cycles) | Bellman-Ford → O(VE) |
| Any weights with negative cycles | Doesn't exist (infinite loop) |

BFS gives **correct shortest paths only on unweighted graphs**. If you use BFS on a weighted graph, you get the path with the fewest edges, not the cheapest path.

---

## 17. BFS vs DFS — Deep Comparison

```
               BFS                        DFS
             ──────                      ──────
Data Struct  Queue (FIFO)                Stack (LIFO) or Recursion
Order        Level by level              Branch by branch
Memory       O(max_width)                O(max_depth)
Shortest Path Yes (unweighted)           No
Complete     Yes (finds all reachable)   Yes
Cycle Detection Yes                      Yes

When to use BFS:                  When to use DFS:
  - Shortest path (unweighted)      - Topological sort
  - Level-order traversal           - Detecting cycles
  - Closest node queries            - Connected components (less memory on deep graphs)
  - Spreading / propagation         - All paths enumeration
  - Word ladder                     - Backtracking problems
  - Maze solving (shortest)         - Maze solving (any path)
  - Social network distance         - Tree structure problems (in/pre/post order)
```

### Memory Comparison

```
Binary tree, depth 20:
  DFS stack depth: 20 nodes
  BFS queue width: 2^19 ≈ 500,000 nodes at the leaf level

For wide, shallow graphs: DFS uses less memory.
For narrow, deep graphs:  BFS uses less memory.
```

---

## 18. Problem Patterns & Templates

### Pattern 1: Shortest Path in Unweighted Graph

```
BFS from source
Return dist[target]
```

### Pattern 2: Shortest Path with State

When the "node" in your BFS is not just a position but a **(position, state)** pair:

```
State = (position, extra_info)
Example: (row, col, keys_collected) for a maze with keys and locks

Mark visited as: visited[row][col][keys_bitmask] = true
```

### Pattern 3: BFS with Level Counting

```
Initialize queue with source(s)
level = 0
while queue not empty:
    process all nodes of current level
    increment level
return level when condition met
```

### Pattern 4: "Minimum Steps to Transform"

```
Word Ladder, Sliding Puzzle, Rubik's Cube, etc.

BFS where:
  Node = current state (string, board configuration, etc.)
  Neighbors = all states reachable in one "move"
  Goal = reach target state

Visited = set of seen states (use hashset)
```

### Template: Generic BFS State Machine (Go)

```go
type State struct {
    // whatever describes your state
    pos int
    // add extra fields here
}

func solve(start, end State) int {
    visited := map[State]bool{start: true}
    queue   := []State{start}
    steps   := 0

    for len(queue) > 0 {
        size := len(queue)
        for i := 0; i < size; i++ {
            curr := queue[i]
            if curr == end { return steps }

            for _, next := range getNeighbors(curr) {
                if !visited[next] {
                    visited[next] = true
                    queue = append(queue, next)
                }
            }
        }
        queue = queue[size:]
        steps++
    }
    return -1
}
```

---

## 19. Classic Problems with Expert Reasoning

### Problem 1: Word Ladder (LeetCode 127)

**Problem**: Transform "hit" → "cog" changing one letter at a time, each intermediate word must be in a dictionary.

**Expert Reasoning**:
1. Each word is a *node*.
2. Two words are *neighbors* if they differ by exactly one character.
3. We want the *shortest path* → BFS.
4. Key insight: Don't build the full graph upfront. Generate neighbors on the fly by trying all 26 × word_length substitutions.

```
hit → hot → dot → dog → cog (answer: 5 words = 4 steps)
```

### Problem 2: Rotting Oranges (LeetCode 994)

**Problem**: Grid with fresh (1) and rotten (2) oranges. Each minute, fresh oranges adjacent to rotten ones become rotten. Find minimum minutes to rot all oranges.

**Expert Reasoning**:
1. All rotten oranges spread simultaneously → **Multi-source BFS**.
2. Enqueue all initially rotten oranges at time 0.
3. BFS level = minutes elapsed.
4. After BFS, if any fresh orange remains → return -1.

### Problem 3: 01 Matrix (LeetCode 542)

**Problem**: Given a matrix of 0s and 1s, find the distance of each cell to the nearest 0.

**Expert Reasoning**:
1. Rephrase: BFS from ALL 0 cells simultaneously (multi-source).
2. Distance of each cell = BFS distance from nearest 0.
3. Enqueue all 0 cells at distance 0, propagate outward.
4. This is exactly multi-source BFS.

### Problem 4: Minimum Knight Moves (LeetCode 1197)

**Problem**: On a chessboard, find minimum knight moves from (0,0) to (x,y).

**Expert Reasoning**:
1. State = (row, col).
2. Neighbors = 8 knight moves.
3. BFS gives minimum moves.
4. Optimization: use symmetry to limit search space.

```
Knight moves: (±1,±2), (±2,±1) — 8 total directions
```

### Problem 5: Snakes and Ladders (LeetCode 909)

**Problem**: On an n×n board with snakes and ladders, find minimum dice rolls to reach square n².

**Expert Reasoning**:
1. State = current square number.
2. From any square, you can reach next 1–6 squares.
3. If a square has a snake/ladder, you are teleported.
4. BFS gives minimum rolls (each "level" = one dice roll).

---

## 20. Mental Models, Cognitive Strategies & Elite Thinking

### Mental Model 1: The Expanding Frontier

Picture BFS as a **wavefront** expanding outward from the source. The queue holds the current frontier — all nodes at the boundary of explored territory. Each BFS iteration advances the frontier by one ring.

### Mental Model 2: The Labeling Machine

BFS is a **labeling machine**. Every node gets exactly one label: its distance from the source. The machine never relabels a node (once labeled, always labeled with the minimum distance). This is the correctness guarantee.

### Mental Model 3: The Breadth-First Invariant

At any point during BFS:
1. All nodes in the queue have distance either d or d+1 (for current processing distance d).
2. All nodes already processed have distance ≤ d.
3. All unvisited nodes have distance > d.

This invariant explains why BFS gives correct shortest paths.

### Mental Model 4: BFS as Parallel Exploration

DFS goes deep on one path before exploring alternatives.  
BFS explores all paths **simultaneously**, one step at a time. When a path reaches the target, it must be the shortest because all shorter paths were already fully explored.

### Cognitive Strategy: Chunking BFS Knowledge

Cognitive chunking means grouping related ideas into a single mental unit. Here are the key BFS chunks:

```
Chunk 1: Infrastructure
  Queue + Visited + Source initialization

Chunk 2: Main Loop
  Dequeue → Process → Enqueue unvisited neighbors

Chunk 3: Level Tracking
  Record queue size at level start → process exactly that many nodes

Chunk 4: Distance Recording
  dist[neighbor] = dist[current] + 1

Chunk 5: Path Reconstruction
  parent[neighbor] = current → walk back from target to source
```

Once each chunk is automatic, you compose them instantly for any BFS problem.

### Deliberate Practice Protocol

1. **Implement BFS from scratch** in all 3 languages without looking at notes.
2. **Solve each variant** from scratch: grid BFS, tree BFS, multi-source BFS.
3. **Analyze each mistake**: wrong visited marking? Wrong level tracking? Off-by-one in bounds?
4. **Time yourself** and track improvement.
5. **Teach it**: Explain BFS to someone (or a rubber duck). Gaps in explanation = gaps in understanding.

### Red Flags (Common Mistakes)

```
MISTAKE 1: Marking visited when dequeuing (not enqueuing)
  → Same node enqueued multiple times → Possible TLE or WA

MISTAKE 2: Not checking bounds in grid BFS
  → Array out of bounds crash

MISTAKE 3: Using BFS on weighted graphs expecting shortest path
  → BFS gives fewest-edges path, not cheapest path

MISTAKE 4: Forgetting to initialize source distance to 0
  → Wrong distances for all nodes

MISTAKE 5: Using global visited array for multiple BFS runs
  → Second BFS sees stale visited data from first BFS

MISTAKE 6: Queue overflow in C with fixed-size arrays
  → Always use a circular buffer or dynamic allocation
```

### The Expert's Problem-Solving Checklist

When facing a new BFS problem, an expert mentally runs through:

```
☐ 1. What is the STATE? (node, position, configuration?)
☐ 2. What are the TRANSITIONS? (edges, moves, transformations?)
☐ 3. What is the SOURCE? (single or multi-source?)
☐ 4. What is the GOAL? (target, condition, all nodes?)
☐ 5. What to TRACK? (distance, path, level count?)
☐ 6. Is the graph UNWEIGHTED? (use BFS; else consider Dijkstra)
☐ 7. Are there CYCLES? (yes → need visited; tree → no visited needed)
☐ 8. Is the graph IMPLICIT? (e.g., grid, puzzle state → compute neighbors on-the-fly)
☐ 9. Can I use MULTI-SOURCE BFS? (multiple equal starting points)
☐ 10. Is BIDIRECTIONAL BFS worth it? (known source AND target, large graph?)
```

### The Flow State Protocol

Peak performance in competitive programming requires flow state:
- **Eliminate ambiguity first**: Read the problem twice, identify inputs/outputs clearly.
- **Sketch the state space** before writing any code.
- **Write the BFS skeleton** from memory, fill in the specifics.
- **Test with the smallest example** manually (trace the queue state).
- **Scale up**: Test with larger inputs, edge cases (disconnected graph, source = target, empty grid).

---

## Summary: BFS Quick Reference Card

```
╔══════════════════════════════════════════════════════════════════╗
║                   BFS QUICK REFERENCE                          ║
╠══════════════════════════════════════════════════════════════════╣
║ Data Structure : Queue (FIFO) — VecDeque in Rust               ║
║ Time Complexity: O(V + E)                                      ║
║ Space Complexity: O(V)                                         ║
╠══════════════════════════════════════════════════════════════════╣
║ Core Steps:                                                    ║
║   1. Mark source visited, enqueue source                       ║
║   2. While queue not empty:                                    ║
║      a. Dequeue front node                                     ║
║      b. Process node                                           ║
║      c. For each unvisited neighbor:                           ║
║         - Mark visited                                         ║
║         - Set dist[neighbor] = dist[node] + 1                  ║
║         - Enqueue                                              ║
╠══════════════════════════════════════════════════════════════════╣
║ Variants:                                                      ║
║   Multi-source → enqueue all sources at distance 0             ║
║   Level-order  → process queue.size() nodes per level          ║
║   Path recon   → track parent[], walk back from target         ║
║   0-1 BFS      → deque: push_front(0-weight), push_back(1-w)  ║
║   Bidir BFS    → two frontiers meet in middle                  ║
╠══════════════════════════════════════════════════════════════════╣
║ Use BFS when:                                                  ║
║   - Shortest path, unweighted graph                            ║
║   - Minimum steps/moves/operations                             ║
║   - Level-by-level processing                                  ║
║   - Spreading/propagation from sources                         ║
╚══════════════════════════════════════════════════════════════════╝
```

---

*"Mastery is not about knowing more — it is about seeing more clearly. Every BFS problem is a wave. Learn to feel the wave, and the code writes itself."*

Here's your complete BFS comprehensive guide. Here's what's inside — 20 chapters covering everything from zero to mastery:

**Foundation** — Queue FIFO internals, graph vocabulary (vertex, edge, neighbor, cycle, component, adjacency list), and the wave/ripple mental model that makes BFS intuitive forever.

**Core Algorithm** — Pseudocode with every decision justified: why you mark visited on *enqueue* (not dequeue), how parent-tracking enables path reconstruction, and the level-boundary trick using `queue.size()`.

**Three Complete Implementations**:
- **C** — Custom circular queue, adjacency list with linked nodes, five fully working BFS functions (basic, distances, path, levels, components)
- **Go** — Idiomatic slice-based queue, map adjacency list, grid BFS with `Point` structs, multi-source BFS
- **Rust** — `VecDeque<T>`, `HashMap`/`HashSet`, full 0-1 BFS using `push_front`/`push_back`, Option-based parent tracking

**Advanced Variants** — Multi-source BFS, 0-1 BFS with deque, Bidirectional BFS with the branching-factor math showing the ~500x speedup, Grid BFS templates.

**Problem Patterns** — 5 classic problems (Word Ladder, Rotting Oranges, 01 Matrix, Knight Moves, Snakes & Ladders) with the expert pre-code reasoning walkthrough.

**Elite Mental Models** — The 10-step expert checklist, chunking protocol, deliberate practice framework, common red flags, and the flow state protocol for competition.

The guide ends with a printable quick-reference card. Study each section until it feels like muscle memory, then implement each variant cold from scratch. That is the path to the top 1%.