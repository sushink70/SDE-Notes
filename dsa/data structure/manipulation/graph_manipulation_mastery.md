# Graph Manipulation Mastery: Complete Reference Guide

> "A graph is not just a data structure — it is the language in which the universe writes its
> relationships. Master its grammar and you master the structure of problems themselves."

---

## Table of Contents

1. [What Is a Graph — The Mental Model](#1-what-is-a-graph--the-mental-model)
2. [Taxonomy of Graphs](#2-taxonomy-of-graphs)
3. [Internal Representations](#3-internal-representations)
   - 3.1 Adjacency Matrix
   - 3.2 Adjacency List
   - 3.3 Edge List
   - 3.4 Incidence Matrix
   - 3.5 CSR (Compressed Sparse Row)
   - 3.6 Hybrid Representations
4. [Core CRUD Operations](#4-core-crud-operations)
5. [Graph Traversals](#5-graph-traversals)
   - 5.1 Depth-First Search (DFS)
   - 5.2 Breadth-First Search (BFS)
   - 5.3 Iterative DFS vs Recursive DFS
6. [Topological Sort](#6-topological-sort)
7. [Cycle Detection](#7-cycle-detection)
8. [Connectivity and Components](#8-connectivity-and-components)
9. [Shortest Path Algorithms](#9-shortest-path-algorithms)
   - 9.1 BFS Shortest Path (Unweighted)
   - 9.2 Dijkstra's Algorithm
   - 9.3 Bellman-Ford
   - 9.4 Floyd-Warshall
   - 9.5 A* Search
10. [Minimum Spanning Tree](#10-minimum-spanning-tree)
    - 10.1 Kruskal's Algorithm
    - 10.2 Prim's Algorithm
11. [Strongly Connected Components (SCC)](#11-strongly-connected-components-scc)
    - 11.1 Kosaraju's Algorithm
    - 11.2 Tarjan's Algorithm
12. [Bridges and Articulation Points](#12-bridges-and-articulation-points)
13. [Bipartite Graph Detection](#13-bipartite-graph-detection)
14. [Union-Find (Disjoint Set Union)](#14-union-find-disjoint-set-union)
15. [Graph Coloring](#15-graph-coloring)
16. [Eulerian and Hamiltonian Paths](#16-eulerian-and-hamiltonian-paths)
17. [Network Flow](#17-network-flow)
18. [What You CANNOT Do — Common Mistakes and Pitfalls](#18-what-you-cannot-do--common-mistakes-and-pitfalls)
19. [Complexity Reference Table](#19-complexity-reference-table)
20. [Mental Models for Expert Graph Thinking](#20-mental-models-for-expert-graph-thinking)

---

## 1. What Is a Graph — The Mental Model

A graph G = (V, E) is a pair of:
- **V**: a finite set of **vertices** (also called nodes)
- **E**: a set of **edges** — pairs (u, v) where u, v ∈ V

This abstract definition hides enormous depth. Every time you see:
- A map → nodes are cities, edges are roads
- A network → nodes are machines, edges are connections
- Dependencies → nodes are tasks, edges are "must-run-before"
- Social graph → nodes are people, edges are friendships

Graphs are the **universal relationship abstraction**. The algorithms that operate on them encode humanity's deepest understanding of structure, flow, and connectivity.

### Formal Vocabulary

```
G = (V, E)
|V| = n   (number of vertices, also called "order")
|E| = m   (number of edges, also called "size")

Degree of a vertex v:
  deg(v) = number of edges incident on v

For directed graphs:
  in-degree(v)  = edges pointing INTO v
  out-degree(v) = edges pointing OUT of v

Handshaking Lemma (undirected):
  sum of all degrees = 2 * |E|

Maximum edges:
  Undirected: n*(n-1)/2
  Directed:   n*(n-1)

Density:
  sparse graph: |E| << |V|^2  (most real-world graphs)
  dense graph:  |E| ~ |V|^2
```

---

## 2. Taxonomy of Graphs

Understanding graph TYPE before choosing an algorithm is the first expert instinct.

```
                        GRAPH TYPES
                        ===========

  DIRECTED (Digraph)              UNDIRECTED
  +---------+                     +---------+
  | A --> B |                     | A --- B |
  | B --> C |                     | A --- C |
  | A --> C |                     | B --- C |
  +---------+                     +---------+
  Edge (u,v) != (v,u)             Edge {u,v} = {v,u}

  WEIGHTED                        UNWEIGHTED
  +---------+                     +---------+
  | A -5-> B|                     | A --> B |
  | B -3-> C|                     | B --> C |
  +---------+                     +---------+
  Each edge has a real value      All edges are equal

  CYCLIC                          ACYCLIC (DAG)
  A --> B --> C                   A --> B --> D
       ^      |                   A --> C --> D
       |______|                   No cycles, used for dependency
                                  resolution, scheduling

  CONNECTED                       DISCONNECTED
  Every vertex reachable          Multiple components exist
  from every other                {A,B,C} and {D,E} separate

  SIMPLE                          MULTIGRAPH
  No self-loops,                  Multiple edges between
  no multiple edges               same pair of nodes

  BIPARTITE                       COMPLETE (K_n)
  V splits into L,R               Every vertex connected
  Edges only L<->R                to every other vertex
  L: {A,B,C}  R: {X,Y,Z}        K_n has n*(n-1)/2 edges

  PLANAR                          NON-PLANAR
  Can draw without                Cannot draw without
  edge crossings                  crossings (K_5, K_{3,3})

  TREE                            FOREST
  Connected, acyclic              Multiple trees (acyclic,
  |E| = |V| - 1                  possibly disconnected)
```

### Graph Properties Cheat Sheet

| Property         | Condition                                       |
|------------------|-------------------------------------------------|
| Tree             | Connected + Acyclic, `E = V - 1`                |
| DAG              | Directed + Acyclic (topological sort exists)    |
| Bipartite        | No odd-length cycles                            |
| Eulerian Circuit | Every vertex has even degree                    |
| Eulerian Path    | Exactly 0 or 2 vertices with odd degree         |
| Complete Graph   | Every pair connected; `E = V*(V-1)/2`           |

---

## 3. Internal Representations

This is where most engineers stop thinking carefully. **Representation choice determines the constant factor of every algorithm you run.** Expert graph engineers choose representation based on density, operation frequency, and cache locality.

### 3.1 Adjacency Matrix

```
Graph:  A--B, A--C, B--C, B--D

Vertices: A=0, B=1, C=2, D=3

         A  B  C  D
       +--+--+--+--+
    A  | 0| 1| 1| 0|
       +--+--+--+--+
    B  | 1| 0| 1| 1|
       +--+--+--+--+
    C  | 1| 1| 0| 0|
       +--+--+--+--+
    D  | 0| 1| 0| 0|
       +--+--+--+--+

Memory layout (row-major, flat array):
  index = row * n + col
  [0,1,1,0, 1,0,1,1, 1,1,0,0, 0,1,0,0]
   A-row    B-row    C-row    D-row

For weighted graph, store weight instead of 1:
  0 means no edge, INF/0 convention varies — be explicit!
```

**Properties:**
- Space: O(V²) — catastrophic for sparse graphs
- Edge query `(u,v)`: O(1) — fastest possible
- Enumerate neighbors of v: O(V) — always scans entire row
- Adding edge: O(1)
- Removing edge: O(1)
- **Best when:** Dense graphs, frequent edge existence queries, V < 1000

**The hidden danger:** For weighted graphs, `0` weight vs "no edge" must be explicitly distinguished. Use `Option<i64>` in Rust, sentinel `INT_MAX` in C, or `-1` in Go depending on domain.

### 3.2 Adjacency List

```
Graph:  A--B, A--C, B--C, B--D, C--E

  Vertex  |  Neighbors (Linked List or Vec/Slice)
  --------+--------------------------------------------------
    A(0)  |  [B(1)] -> [C(2)] -> NULL
    B(1)  |  [A(0)] -> [C(2)] -> [D(3)] -> NULL
    C(2)  |  [A(0)] -> [B(1)] -> [E(4)] -> NULL
    D(3)  |  [B(1)] -> NULL
    E(4)  |  [C(2)] -> NULL

Memory structure (Vec of Vecs / array of dynamic arrays):

  adj[0]: [1, 2]
  adj[1]: [0, 2, 3]
  adj[2]: [0, 1, 4]
  adj[3]: [1]
  adj[4]: [2]

  For weighted graph, store (neighbor, weight) pairs:
  adj[0]: [(1, 5.0), (2, 3.0)]
  adj[1]: [(0, 5.0), (2, 2.0), (3, 7.0)]
```

**Properties:**
- Space: O(V + E) — ideal for sparse graphs
- Edge query `(u,v)`: O(degree(u)) — linear scan of neighbor list
- Enumerate neighbors: O(degree(v)) — very fast
- Adding edge: O(1) amortized (append to list)
- Removing edge: O(degree(v)) — must find and remove
- **Best when:** Sparse graphs (most real-world), traversal-heavy workloads

**Critical implementation detail:** Using a `HashSet` instead of `Vec` for neighbor lists gives O(1) edge query at the cost of O(degree) memory overhead and poor cache locality. Choose explicitly.

### 3.3 Edge List

```
Graph:  A--B (w=5), A--C (w=3), B--D (w=7)

  Edge List (sorted by source, then by destination):
  +-------+-------+--------+
  | src   | dst   | weight |
  +-------+-------+--------+
  |  A(0) |  B(1) |   5    |
  |  A(0) |  C(2) |   3    |
  |  B(1) |  D(3) |   7    |
  +-------+-------+--------+

  As flat array of structs:
  edges = [(0,1,5), (0,2,3), (1,3,7)]
```

**Properties:**
- Space: O(E)
- Edge query: O(E) — must scan all edges
- Enumerate all edges: O(E) — trivial
- Sorting edges: O(E log E) — prerequisite for Kruskal
- **Best when:** Kruskal's MST, algorithms that process ALL edges uniformly

### 3.4 Incidence Matrix

```
Graph: Vertices {A,B,C}, Edges {e1=A-B, e2=B-C, e3=A-C}

        e1  e2  e3
     A [ 1   0   1 ]
     B [ 1   1   0 ]
     C [ 0   1   1 ]

Directed variant:
  +1 for outgoing, -1 for incoming
        e1  e2  e3
     A [+1   0  +1 ]
     B [-1  +1   0 ]
     C [ 0  -1  -1 ]
```

**Properties:**
- Space: O(V * E) — very expensive
- **Use case:** Graph theory proofs, spectral graph analysis — rarely used in competitive programming

### 3.5 CSR (Compressed Sparse Row)

The professional choice for high-performance graph processing (used in PageRank, graph neural networks, HPC).

```
Graph (directed):
  0 -> [1, 3]
  1 -> [2]
  2 -> []
  3 -> [0, 2]

CSR Structure:
  col_idx: [1, 3, 2, 0, 2]
             edges listed vertex by vertex
  row_ptr: [0, 2, 3, 3, 5]
             row_ptr[v] = start index in col_idx for vertex v
             row_ptr[v+1] = end index (exclusive)

  Neighbors of vertex v = col_idx[row_ptr[v] .. row_ptr[v+1]]

  Vertex 0: col_idx[0..2] = [1, 3]    ✓
  Vertex 1: col_idx[2..3] = [2]        ✓
  Vertex 2: col_idx[3..3] = []         ✓
  Vertex 3: col_idx[3..5] = [0, 2]    ✓

Memory layout:
  row_ptr: [0] [2] [3] [3] [5]
             ^   ^   ^   ^   ^
             |   |   |   |   |
  vertex:    0   1   2   3   (end sentinel)

  col_idx: [1] [3] [2] [0] [2]
              ^^^     ^   ^^^
              v0's    v1  v3's
              nbrs    nbr  nbrs
```

**Properties:**
- Space: O(V + E) — same as adjacency list but in contiguous memory
- Cache efficiency: Excellent — sequential access pattern
- Construction: O(V + E) — requires knowing E in advance or two-pass build
- **Best when:** Read-heavy graph algorithms on large graphs (millions of edges), SIMD processing, parallelism

### 3.6 Hybrid Representations

**HashMap-based (for string-keyed graphs):**
```
adj: HashMap<String, HashSet<String>>
"alice" -> {"bob", "carol"}
"bob"   -> {"alice", "dave"}
```

**Choosing the Right Representation:**

```
                Query Frequency Analysis
                ========================

  Operation         Matrix   Adj List   Edge List   CSR
  ----------------  -------  ---------  ----------  --------
  Edge (u,v)?       O(1)     O(deg)     O(E)        O(log deg)
  Neighbors of v    O(V)     O(deg)     O(E)        O(deg)
  All edges         O(V^2)   O(V+E)     O(E)        O(V+E)
  Add vertex        O(V^2)   O(1)       O(1)        rebuild
  Add edge          O(1)     O(1)       O(1)        rebuild
  Remove edge       O(1)     O(deg)     O(E)        rebuild
  Space             O(V^2)   O(V+E)     O(E)        O(V+E)
  Cache locality    High     Medium     Medium      Very High
```

---

## 4. Core CRUD Operations

### C Implementation — Adjacency List

```c
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>

#define MAX_VERTICES 1000

/* ---------- Data Structures ---------- */

typedef struct AdjNode {
    int dest;
    int weight;
    struct AdjNode *next;
} AdjNode;

typedef struct Graph {
    int V;             /* number of vertices */
    int E;             /* number of edges    */
    AdjNode **adj;     /* array of adjacency lists */
    bool directed;
} Graph;

/* ---------- Construction ---------- */

AdjNode *new_adj_node(int dest, int weight) {
    AdjNode *node = malloc(sizeof(AdjNode));
    if (!node) { perror("malloc"); exit(1); }
    node->dest   = dest;
    node->weight = weight;
    node->next   = NULL;
    return node;
}

Graph *graph_create(int V, bool directed) {
    Graph *g = malloc(sizeof(Graph));
    if (!g) { perror("malloc"); exit(1); }
    g->V        = V;
    g->E        = 0;
    g->directed = directed;
    g->adj      = calloc(V, sizeof(AdjNode *));
    if (!g->adj) { perror("calloc"); exit(1); }
    return g;
}

/* ---------- Add Edge ---------- */

void graph_add_edge(Graph *g, int u, int v, int weight) {
    /* Prepend to adjacency list — O(1) */
    if (u < 0 || u >= g->V || v < 0 || v >= g->V) {
        fprintf(stderr, "add_edge: vertex out of range\n");
        return;
    }
    AdjNode *node = new_adj_node(v, weight);
    node->next    = g->adj[u];
    g->adj[u]     = node;

    if (!g->directed) {
        AdjNode *rev  = new_adj_node(u, weight);
        rev->next     = g->adj[v];
        g->adj[v]     = rev;
    }
    g->E++;
}

/* ---------- Remove Edge ---------- */

void graph_remove_edge(Graph *g, int u, int v) {
    /* O(degree(u)) */
    AdjNode **cur = &g->adj[u];
    while (*cur) {
        if ((*cur)->dest == v) {
            AdjNode *tmp = *cur;
            *cur = (*cur)->next;
            free(tmp);
            g->E--;
            break;
        }
        cur = &(*cur)->next;
    }
    if (!g->directed) {
        cur = &g->adj[v];
        while (*cur) {
            if ((*cur)->dest == u) {
                AdjNode *tmp = *cur;
                *cur = (*cur)->next;
                free(tmp);
                break;
            }
            cur = &(*cur)->next;
        }
    }
}

/* ---------- Query Edge ---------- */

bool graph_has_edge(const Graph *g, int u, int v) {
    AdjNode *cur = g->adj[u];
    while (cur) {
        if (cur->dest == v) return true;
        cur = cur->next;
    }
    return false;
}

int graph_edge_weight(const Graph *g, int u, int v) {
    AdjNode *cur = g->adj[u];
    while (cur) {
        if (cur->dest == v) return cur->weight;
        cur = cur->next;
    }
    return -1; /* no edge */
}

/* ---------- Degree ---------- */

int graph_out_degree(const Graph *g, int u) {
    int count = 0;
    AdjNode *cur = g->adj[u];
    while (cur) { count++; cur = cur->next; }
    return count;
}

/* ---------- Print ---------- */

void graph_print(const Graph *g) {
    for (int i = 0; i < g->V; i++) {
        printf("%d: ", i);
        AdjNode *cur = g->adj[i];
        while (cur) {
            printf("->(%d,w=%d) ", cur->dest, cur->weight);
            cur = cur->next;
        }
        printf("\n");
    }
}

/* ---------- Destroy ---------- */

void graph_destroy(Graph *g) {
    for (int i = 0; i < g->V; i++) {
        AdjNode *cur = g->adj[i];
        while (cur) {
            AdjNode *tmp = cur;
            cur = cur->next;
            free(tmp);
        }
    }
    free(g->adj);
    free(g);
}
```

### Go Implementation — Adjacency List

```go
package graph

import "fmt"

// Edge represents a weighted directed edge.
type Edge struct {
    To     int
    Weight int
}

// Graph is an adjacency-list graph.
type Graph struct {
    V        int
    Directed bool
    Adj      [][]Edge
}

// NewGraph constructs a graph with V vertices.
func NewGraph(v int, directed bool) *Graph {
    return &Graph{
        V:        v,
        Directed: directed,
        Adj:      make([][]Edge, v),
    }
}

// AddEdge adds an edge u->v (and v->u if undirected).
func (g *Graph) AddEdge(u, v, weight int) {
    if u < 0 || u >= g.V || v < 0 || v >= g.V {
        panic(fmt.Sprintf("AddEdge: vertex out of range u=%d v=%d", u, v))
    }
    g.Adj[u] = append(g.Adj[u], Edge{To: v, Weight: weight})
    if !g.Directed {
        g.Adj[v] = append(g.Adj[v], Edge{To: u, Weight: weight})
    }
}

// RemoveEdge removes the first occurrence of edge u->v.
// O(degree(u)) — does NOT preserve order of adjacency list.
func (g *Graph) RemoveEdge(u, v int) {
    g.Adj[u] = removeFromSlice(g.Adj[u], v)
    if !g.Directed {
        g.Adj[v] = removeFromSlice(g.Adj[v], u)
    }
}

func removeFromSlice(edges []Edge, target int) []Edge {
    for i, e := range edges {
        if e.To == target {
            // Swap with last element and truncate — O(1), does NOT preserve order
            edges[i] = edges[len(edges)-1]
            return edges[:len(edges)-1]
        }
    }
    return edges
}

// HasEdge checks if edge u->v exists. O(degree(u)).
func (g *Graph) HasEdge(u, v int) bool {
    for _, e := range g.Adj[u] {
        if e.To == v {
            return true
        }
    }
    return false
}

// Degree returns the out-degree of vertex u.
func (g *Graph) Degree(u int) int {
    return len(g.Adj[u])
}

// Neighbors returns a slice of neighbor vertex IDs.
func (g *Graph) Neighbors(u int) []int {
    result := make([]int, len(g.Adj[u]))
    for i, e := range g.Adj[u] {
        result[i] = e.To
    }
    return result
}

// Transpose returns the graph with all edges reversed (for Kosaraju).
func (g *Graph) Transpose() *Graph {
    t := NewGraph(g.V, g.Directed)
    for u := 0; u < g.V; u++ {
        for _, e := range g.Adj[u] {
            t.Adj[e.To] = append(t.Adj[e.To], Edge{To: u, Weight: e.Weight})
        }
    }
    return t
}

// Print displays the adjacency list.
func (g *Graph) Print() {
    for u := 0; u < g.V; u++ {
        fmt.Printf("%d: %v\n", u, g.Adj[u])
    }
}
```

### Rust Implementation — Adjacency List

```rust
use std::collections::HashMap;

/// A weighted directed/undirected graph using adjacency lists.
#[derive(Debug, Clone)]
pub struct Graph {
    pub v: usize,
    pub directed: bool,
    pub adj: Vec<Vec<(usize, i64)>>,  // adj[u] = [(v, weight), ...]
}

impl Graph {
    /// Create a new graph with `v` vertices.
    pub fn new(v: usize, directed: bool) -> Self {
        Graph {
            v,
            directed,
            adj: vec![Vec::new(); v],
        }
    }

    /// Add edge u -> v with given weight.
    /// Panics if vertices are out of range.
    pub fn add_edge(&mut self, u: usize, v: usize, weight: i64) {
        assert!(u < self.v && v < self.v, "add_edge: vertex out of range");
        self.adj[u].push((v, weight));
        if !self.directed {
            self.adj[v].push((u, weight));
        }
    }

    /// Remove edge u -> v. O(degree(u)).
    /// Returns true if the edge existed.
    pub fn remove_edge(&mut self, u: usize, v: usize) -> bool {
        let original_len = self.adj[u].len();
        self.adj[u].retain(|&(dest, _)| dest != v);
        let removed = self.adj[u].len() < original_len;
        if !self.directed && removed {
            self.adj[v].retain(|&(dest, _)| dest != u);
        }
        removed
    }

    /// Check if edge u -> v exists.
    pub fn has_edge(&self, u: usize, v: usize) -> bool {
        self.adj[u].iter().any(|&(dest, _)| dest == v)
    }

    /// Get the weight of edge u -> v. Returns None if no such edge.
    pub fn edge_weight(&self, u: usize, v: usize) -> Option<i64> {
        self.adj[u]
            .iter()
            .find(|&&(dest, _)| dest == v)
            .map(|&(_, w)| w)
    }

    /// Out-degree of vertex u.
    pub fn degree(&self, u: usize) -> usize {
        self.adj[u].len()
    }

    /// Neighbors of vertex u (only vertex indices).
    pub fn neighbors(&self, u: usize) -> impl Iterator<Item = usize> + '_ {
        self.adj[u].iter().map(|&(v, _)| v)
    }

    /// Transpose: reverse all edge directions.
    pub fn transpose(&self) -> Self {
        let mut t = Graph::new(self.v, self.directed);
        for u in 0..self.v {
            for &(v, w) in &self.adj[u] {
                t.adj[v].push((u, w));
            }
        }
        t
    }

    /// Number of edges (counts directed edges).
    pub fn edge_count(&self) -> usize {
        let total: usize = self.adj.iter().map(|list| list.len()).sum();
        if self.directed { total } else { total / 2 }
    }

    /// Build adjacency matrix representation.
    /// Uses i64::MAX as "no edge" sentinel.
    pub fn to_matrix(&self) -> Vec<Vec<i64>> {
        let mut mat = vec![vec![i64::MAX; self.v]; self.v];
        for i in 0..self.v {
            mat[i][i] = 0;
        }
        for u in 0..self.v {
            for &(v, w) in &self.adj[u] {
                mat[u][v] = w;
            }
        }
        mat
    }
}

impl std::fmt::Display for Graph {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        for u in 0..self.v {
            write!(f, "{}: ", u)?;
            for &(v, w) in &self.adj[u] {
                write!(f, "->({}, w={}) ", v, w)?;
            }
            writeln!(f)?;
        }
        Ok(())
    }
}
```

---

## 5. Graph Traversals

Traversal is the foundation. Every graph algorithm is either a traversal variant or uses traversal as a subroutine. Understand these at a mechanical level.

### 5.1 Depth-First Search (DFS)

**Mental model:** DFS commits fully to one path until it cannot go further, then backtracks. Like exploring a maze by always choosing the leftmost path and marking visited rooms.

```
DFS on: 0-1, 0-2, 1-3, 1-4, 2-5

adj[0]=[1,2], adj[1]=[0,3,4], adj[2]=[0,5]
adj[3]=[1], adj[4]=[1], adj[5]=[2]

Call stack trace (recursive):
  DFS(0): visit 0, push to stack
    DFS(1): visit 1
      DFS(3): visit 3
        No unvisited neighbors -> return
      DFS(4): visit 4
        No unvisited neighbors -> return
      (0 already visited) -> skip
    DFS(2): visit 2
      DFS(5): visit 5
        No unvisited neighbors -> return
      (0 already visited) -> skip

Visit order: 0, 1, 3, 4, 2, 5

DFS Tree (dotted = back/cross edges):
      0
     / \
    1   2
   / \   \
  3   4   5
```

**DFS timestamps — the key insight:**

```
pre[v]  = time when we ENTER v (discovery time)
post[v] = time when we EXIT v (finish time)

Graph: 0->1->2->0 (cycle), 0->3

pre:   [1, 2, 3, 7]
post:  [8, 5, 4, 6]  (for example)

Edge classification by pre/post:
  Tree edge:    pre[u] < pre[v], post[u] > post[v]  (v is descendant)
  Back edge:    pre[v] < pre[u], post[v] > post[u]  (v is ancestor) -> CYCLE
  Forward edge: pre[u] < pre[v], post[u] > post[v]  (but v not direct child)
  Cross edge:   post[v] < pre[u]                    (no ancestor relationship)

Back edges exist <=> graph has a cycle.
Forward/cross edges only exist in directed graphs.
```

**C Implementation — DFS:**

```c
/* Global state for DFS — fine for competitive programming */
bool visited[MAX_VERTICES];
int  pre[MAX_VERTICES];
int  post[MAX_VERTICES];
int  timer_g = 0;

void dfs(const Graph *g, int v) {
    visited[v]  = true;
    pre[v]      = timer_g++;
    printf("enter %d (pre=%d)\n", v, pre[v]);

    AdjNode *cur = g->adj[v];
    while (cur) {
        if (!visited[cur->dest]) {
            dfs(g, cur->dest);
        }
        cur = cur->next;
    }

    post[v] = timer_g++;
    printf("exit  %d (post=%d)\n", v, post[v]);
}

void dfs_full(const Graph *g) {
    memset(visited, false, sizeof(bool) * g->V);
    timer_g = 0;
    for (int i = 0; i < g->V; i++) {
        if (!visited[i]) {
            dfs(g, i);
        }
    }
}
```

**Go Implementation — DFS:**

```go
// DFSResult holds timestamps and component info.
type DFSResult struct {
    Pre     []int
    Post    []int
    Comp    []int // component ID per vertex
    NumComp int
}

// DFS performs full DFS on graph g.
func DFS(g *Graph) DFSResult {
    res := DFSResult{
        Pre:  make([]int, g.V),
        Post: make([]int, g.V),
        Comp: make([]int, g.V),
    }
    visited := make([]bool, g.V)
    timer   := 0

    var dfs func(v, comp int)
    dfs = func(v, comp int) {
        visited[v] = true
        res.Pre[v] = timer
        res.Comp[v] = comp
        timer++
        for _, e := range g.Adj[v] {
            if !visited[e.To] {
                dfs(e.To, comp)
            }
        }
        res.Post[v] = timer
        timer++
    }

    for v := 0; v < g.V; v++ {
        if !visited[v] {
            dfs(v, res.NumComp)
            res.NumComp++
        }
    }
    return res
}
```

**Rust Implementation — DFS:**

```rust
#[derive(Debug, Default)]
pub struct DfsResult {
    pub pre:      Vec<usize>,
    pub post:     Vec<usize>,
    pub comp:     Vec<usize>,
    pub num_comp: usize,
    pub order:    Vec<usize>,  // topological order (reversed post-order)
}

impl Graph {
    pub fn dfs(&self) -> DfsResult {
        let mut res = DfsResult {
            pre:  vec![0; self.v],
            post: vec![0; self.v],
            comp: vec![0; self.v],
            ..Default::default()
        };
        let mut visited = vec![false; self.v];
        let mut timer   = 0usize;

        fn dfs_impl(
            g:       &Graph,
            v:       usize,
            comp:    usize,
            visited: &mut Vec<bool>,
            timer:   &mut usize,
            res:     &mut DfsResult,
        ) {
            visited[v]  = true;
            res.pre[v]  = *timer;
            res.comp[v] = comp;
            *timer += 1;

            for &(u, _) in &g.adj[v] {
                if !visited[u] {
                    dfs_impl(g, u, comp, visited, timer, res);
                }
            }

            res.post[v] = *timer;
            *timer += 1;
            res.order.push(v);  // post-order: useful for topo sort
        }

        for v in 0..self.v {
            if !visited[v] {
                dfs_impl(self, v, res.num_comp, &mut visited, &mut timer, &mut res);
                res.num_comp += 1;
            }
        }
        res
    }
}
```

### 5.2 Breadth-First Search (BFS)

**Mental model:** BFS explores level by level — like ripples in water. It guarantees shortest path in unweighted graphs because it exhausts all distance-d vertices before exploring distance-(d+1) vertices.

```
BFS on: 0-1, 0-2, 1-3, 1-4, 2-4, 3-5

Start: 0

Queue state:
  Init:    [0]          visited={0}
  Step 1:  dequeue 0 -> enqueue 1,2   queue=[1,2]   visited={0,1,2}
  Step 2:  dequeue 1 -> enqueue 3,4   queue=[2,3,4] visited={0,1,2,3,4}
  Step 3:  dequeue 2 -> 4 visited      queue=[3,4]
  Step 4:  dequeue 3 -> enqueue 5     queue=[4,5]   visited={0..5}
  Step 5:  dequeue 4 -> nothing new   queue=[5]
  Step 6:  dequeue 5 -> nothing new   queue=[]

BFS tree (levels = shortest distance from 0):
  Level 0: {0}
  Level 1: {1, 2}
  Level 2: {3, 4}
  Level 3: {5}

dist[0]=0, dist[1]=1, dist[2]=1, dist[3]=2, dist[4]=2, dist[5]=3
```

**C Implementation — BFS:**

```c
#include <limits.h>

typedef struct Queue {
    int data[MAX_VERTICES];
    int front, rear;
} Queue;

void queue_init(Queue *q) { q->front = q->rear = 0; }
bool queue_empty(const Queue *q) { return q->front == q->rear; }
void queue_push(Queue *q, int v) { q->data[q->rear++] = v; }
int  queue_pop(Queue *q)         { return q->data[q->front++]; }

/* BFS: returns dist[] array, -1 if unreachable */
void bfs(const Graph *g, int src, int *dist) {
    for (int i = 0; i < g->V; i++) dist[i] = -1;
    dist[src] = 0;

    Queue q;
    queue_init(&q);
    queue_push(&q, src);

    while (!queue_empty(&q)) {
        int u = queue_pop(&q);
        AdjNode *cur = g->adj[u];
        while (cur) {
            int v = cur->dest;
            if (dist[v] == -1) {
                dist[v] = dist[u] + 1;
                queue_push(&q, v);
            }
            cur = cur->next;
        }
    }
}
```

**Go Implementation — BFS:**

```go
// BFS returns distance from src to every reachable vertex.
// dist[v] == -1 means unreachable.
func BFS(g *Graph, src int) []int {
    dist := make([]int, g.V)
    for i := range dist {
        dist[i] = -1
    }
    dist[src] = 0

    queue := []int{src}
    for len(queue) > 0 {
        u := queue[0]
        queue = queue[1:]  // dequeue — use container/list for large graphs
        for _, e := range g.Adj[u] {
            if dist[e.To] == -1 {
                dist[e.To] = dist[u] + 1
                queue = append(queue, e.To)
            }
        }
    }
    return dist
}

// BFSPath returns shortest path from src to dst, nil if unreachable.
func BFSPath(g *Graph, src, dst int) []int {
    dist := make([]int, g.V)
    prev := make([]int, g.V)
    for i := range dist {
        dist[i] = -1
        prev[i] = -1
    }
    dist[src] = 0
    queue := []int{src}

    for len(queue) > 0 && dist[dst] == -1 {
        u := queue[0]
        queue = queue[1:]
        for _, e := range g.Adj[u] {
            if dist[e.To] == -1 {
                dist[e.To] = dist[u] + 1
                prev[e.To] = u
                queue = append(queue, e.To)
            }
        }
    }
    if dist[dst] == -1 {
        return nil
    }
    // Reconstruct path
    path := []int{}
    for v := dst; v != -1; v = prev[v] {
        path = append([]int{v}, path...)
    }
    return path
}
```

**Rust Implementation — BFS:**

```rust
use std::collections::VecDeque;

impl Graph {
    /// BFS from src. Returns distance vector; usize::MAX means unreachable.
    pub fn bfs(&self, src: usize) -> Vec<usize> {
        let mut dist = vec![usize::MAX; self.v];
        dist[src] = 0;

        let mut queue = VecDeque::new();
        queue.push_back(src);

        while let Some(u) = queue.pop_front() {
            for &(v, _) in &self.adj[u] {
                if dist[v] == usize::MAX {
                    dist[v] = dist[u] + 1;
                    queue.push_back(v);
                }
            }
        }
        dist
    }

    /// BFS shortest path from src to dst.
    pub fn bfs_path(&self, src: usize, dst: usize) -> Option<Vec<usize>> {
        let mut dist = vec![usize::MAX; self.v];
        let mut prev = vec![usize::MAX; self.v];
        dist[src] = 0;

        let mut queue = VecDeque::new();
        queue.push_back(src);

        while let Some(u) = queue.pop_front() {
            if u == dst { break; }
            for &(v, _) in &self.adj[u] {
                if dist[v] == usize::MAX {
                    dist[v] = dist[u] + 1;
                    prev[v] = u;
                    queue.push_back(v);
                }
            }
        }

        if dist[dst] == usize::MAX {
            return None;
        }

        let mut path = Vec::new();
        let mut cur = dst;
        while cur != usize::MAX {
            path.push(cur);
            cur = prev[cur];
        }
        path.reverse();
        Some(path)
    }
}
```

### 5.3 Iterative DFS vs Recursive DFS

**CRITICAL DIFFERENCE:** Iterative DFS using a stack does NOT produce the same traversal order as recursive DFS. This surprises most engineers.

```
Recursive DFS (processes neighbors in order, LEFT to RIGHT):
  Stack at each step is the call stack
  Visit order: 0, 1, 3, 4, 2, 5  (assuming adj order [1,2], [3,4], ...)

Iterative DFS with explicit stack (pushes neighbors, RIGHT to LEFT for
  same order; but edge processing differs):
  Pushes ALL neighbors before processing any
  The FIRST neighbor pushed is processed LAST (LIFO)

The difference:
  Recursive: processes one neighbor, goes deep, then processes next
  Iterative: pushes all neighbors at once, then pops LIFO

To get same order in iterative, push neighbors in REVERSE order.
But for cycle detection / topological sort, this matters.
```

**Rust — Iterative DFS (for large graphs, avoiding stack overflow):**

```rust
impl Graph {
    /// Iterative DFS — safe for deep graphs (no stack overflow risk).
    /// NOTE: visit order differs from recursive DFS for multi-neighbor nodes.
    pub fn dfs_iterative(&self, src: usize) -> Vec<usize> {
        let mut visited = vec![false; self.v];
        let mut order   = Vec::new();
        let mut stack   = vec![src];

        while let Some(u) = stack.pop() {
            if visited[u] { continue; }
            visited[u] = true;
            order.push(u);
            // Push in reverse to maintain left-to-right visit order
            for &(v, _) in self.adj[u].iter().rev() {
                if !visited[v] {
                    stack.push(v);
                }
            }
        }
        order
    }
}
```

**When to use iterative DFS:**
- Graph depth could exceed system stack size (default ~8MB on Linux ≈ ~100K-500K frames)
- In production code where stack overflow is unacceptable
- In Rust, where default stack is even smaller for threads

---

## 6. Topological Sort

Topological sort produces a linear ordering of vertices in a DAG such that for every edge u->v, u appears before v.

**Mental model:** Scheduling — if task A must precede task B, A appears before B in the result.

```
DAG:
  5 -> 0
  5 -> 2
  4 -> 0
  4 -> 1
  2 -> 3
  3 -> 1

  5    4
  |\ / \
  | 2   0  1
  |  \     ^
  |   3----+

Valid topological orders:
  [5, 4, 2, 3, 1, 0]
  [4, 5, 2, 3, 0, 1]
  [5, 4, 0, 2, 3, 1]
  ... (multiple valid orderings possible)
```

### Algorithm 1: Kahn's Algorithm (BFS-based)

```
Key invariant: A vertex with in-degree 0 has no prerequisites.

1. Compute in-degree for all vertices.
2. Initialize queue with all in-degree-0 vertices.
3. Repeatedly:
   a. Dequeue vertex u
   b. Append u to result
   c. For each neighbor v of u: decrement in-degree[v]
      If in-degree[v] becomes 0: enqueue v
4. If result has fewer than V vertices: graph has a CYCLE (not a DAG)

In-degree tracking:
  5:0  4:0  2:1  3:1  0:2  1:2
  Queue: [5, 4]

  Pop 5: result=[5], decrement 0(->1), 2(->0). Queue=[4,2]
  Pop 4: result=[5,4], decrement 0(->0), 1(->1). Queue=[2,0]
  Pop 2: result=[5,4,2], decrement 3(->0). Queue=[0,3]
  Pop 0: result=[5,4,2,0] no neighbors
  Pop 3: result=[5,4,2,0,3], decrement 1(->0). Queue=[1]
  Pop 1: result=[5,4,2,0,3,1]
  |result|=6=V -> no cycle -> valid topological order
```

**Go — Kahn's Algorithm:**

```go
// TopoSortKahn returns a topological order or nil if graph has a cycle.
func TopoSortKahn(g *Graph) []int {
    indegree := make([]int, g.V)
    for u := 0; u < g.V; u++ {
        for _, e := range g.Adj[u] {
            indegree[e.To]++
        }
    }

    queue := []int{}
    for v := 0; v < g.V; v++ {
        if indegree[v] == 0 {
            queue = append(queue, v)
        }
    }

    var result []int
    for len(queue) > 0 {
        u := queue[0]
        queue = queue[1:]
        result = append(result, u)
        for _, e := range g.Adj[u] {
            indegree[e.To]--
            if indegree[e.To] == 0 {
                queue = append(queue, e.To)
            }
        }
    }

    if len(result) != g.V {
        return nil // cycle detected
    }
    return result
}
```

### Algorithm 2: DFS Post-Order (Reverse Post-Order)

```
Key insight: DFS post-order gives REVERSE topological order.
Reversing it gives topological order.

Why? When DFS exits v (assigns post[v]):
  All vertices reachable from v have already been exited.
  So v appears AFTER all its dependencies in post-order.
  Reversing makes v appear BEFORE all its dependencies.
```

**Rust — DFS Topological Sort:**

```rust
impl Graph {
    /// Returns topological order of DAG.
    /// Returns None if a cycle is detected.
    pub fn topo_sort_dfs(&self) -> Option<Vec<usize>> {
        // 0=unvisited, 1=in-progress (gray), 2=done (black)
        let mut color = vec![0u8; self.v];
        let mut order = Vec::new();
        let mut has_cycle = false;

        fn dfs(
            g:         &Graph,
            v:         usize,
            color:     &mut Vec<u8>,
            order:     &mut Vec<usize>,
            has_cycle: &mut bool,
        ) {
            if *has_cycle { return; }
            color[v] = 1; // gray: currently being explored
            for &(u, _) in &g.adj[v] {
                match color[u] {
                    0 => dfs(g, u, color, order, has_cycle),
                    1 => { *has_cycle = true; return; } // back edge = cycle
                    _ => {}
                }
            }
            color[v] = 2; // black: fully explored
            order.push(v);
        }

        for v in 0..self.v {
            if color[v] == 0 {
                dfs(self, v, &mut color, &mut order, &mut has_cycle);
            }
        }

        if has_cycle {
            None
        } else {
            order.reverse();
            Some(order)
        }
    }
}
```

**C — Topological Sort:**

```c
/* color: 0=white, 1=gray, 2=black */
int  topo_color[MAX_VERTICES];
int  topo_result[MAX_VERTICES];
int  topo_idx;
bool topo_has_cycle;

void topo_dfs(const Graph *g, int v) {
    if (topo_has_cycle) return;
    topo_color[v] = 1;
    AdjNode *cur = g->adj[v];
    while (cur) {
        int u = cur->dest;
        if (topo_color[u] == 0) {
            topo_dfs(g, u);
        } else if (topo_color[u] == 1) {
            topo_has_cycle = true;
            return;
        }
        cur = cur->next;
    }
    topo_color[v] = 2;
    topo_result[--topo_idx] = v;  /* prepend */
}

/* Returns true if successful, false if cycle detected.
   Result stored in topo_result[0..V-1] */
bool topo_sort(const Graph *g) {
    memset(topo_color, 0, sizeof(int) * g->V);
    topo_idx       = g->V;
    topo_has_cycle = false;
    for (int v = 0; v < g->V; v++) {
        if (topo_color[v] == 0) {
            topo_dfs(g, v);
        }
    }
    return !topo_has_cycle;
}
```

---

## 7. Cycle Detection

### Undirected Graph — DFS with Parent Tracking

```
Key insight: In undirected DFS, the only "back edge" to worry about
is an edge to a vertex other than the direct parent (since every edge
appears twice in the adjacency list — once for each direction).

WRONG: if visited[neighbor] -> cycle   (NO! Parent is always visited)
RIGHT: if visited[neighbor] AND neighbor != parent -> cycle
```

```c
bool has_cycle_undirected_dfs(const Graph *g, int v, int parent, bool *visited) {
    visited[v] = true;
    AdjNode *cur = g->adj[v];
    while (cur) {
        int u = cur->dest;
        if (!visited[u]) {
            if (has_cycle_undirected_dfs(g, u, v, visited)) return true;
        } else if (u != parent) {
            return true; /* back edge to non-parent: cycle */
        }
        cur = cur->next;
    }
    return false;
}

bool graph_has_cycle_undirected(const Graph *g) {
    bool visited[MAX_VERTICES] = {false};
    for (int v = 0; v < g->V; v++) {
        if (!visited[v]) {
            if (has_cycle_undirected_dfs(g, v, -1, visited)) return true;
        }
    }
    return false;
}
```

### Directed Graph — Color DFS (3-Color Algorithm)

```
White (0) = unvisited
Gray  (1) = currently on DFS stack (in progress)
Black (2) = fully processed

Back edge = edge to a GRAY vertex = CYCLE
Forward/cross edges go to BLACK vertices = not cycles
```

### Undirected Graph — Union-Find (Faster in Practice)

```
For each edge (u, v):
  If find(u) == find(v): CYCLE (they're already in same component)
  Else: union(u, v)

No cycle found after all edges processed.

This is O(E * alpha(V)) ≈ O(E) with union-by-rank + path compression.
```

**Go — Cycle Detection with Union-Find:**

```go
type UnionFind struct {
    parent []int
    rank   []int
}

func NewUnionFind(n int) *UnionFind {
    uf := &UnionFind{parent: make([]int, n), rank: make([]int, n)}
    for i := range uf.parent {
        uf.parent[i] = i
    }
    return uf
}

func (uf *UnionFind) Find(x int) int {
    if uf.parent[x] != x {
        uf.parent[x] = uf.Find(uf.parent[x]) // path compression
    }
    return uf.parent[x]
}

func (uf *UnionFind) Union(x, y int) bool {
    px, py := uf.Find(x), uf.Find(y)
    if px == py { return false } // already in same set
    if uf.rank[px] < uf.rank[py] {
        px, py = py, px
    }
    uf.parent[py] = px
    if uf.rank[px] == uf.rank[py] {
        uf.rank[px]++
    }
    return true
}

// HasCycleUndirected detects cycle using Union-Find. O(E * alpha(V)).
func HasCycleUndirected(g *Graph) bool {
    uf := NewUnionFind(g.V)
    for u := 0; u < g.V; u++ {
        for _, e := range g.Adj[u] {
            if e.To <= u { continue } // process each undirected edge once
            if !uf.Union(u, e.To) {
                return true // same component: cycle
            }
        }
    }
    return false
}
```

---

## 8. Connectivity and Components

### Connected Components (Undirected)

```
Find all maximal connected subgraphs.

Graph: {0-1, 0-2, 3-4, 5}

Components:
  {0, 1, 2}  <- one component
  {3, 4}     <- another
  {5}        <- isolated vertex
```

**Rust — Connected Components:**

```rust
impl Graph {
    /// Returns component ID for each vertex and total component count.
    pub fn connected_components(&self) -> (Vec<usize>, usize) {
        let mut comp = vec![usize::MAX; self.v];
        let mut count = 0;

        for start in 0..self.v {
            if comp[start] != usize::MAX { continue; }
            // BFS from start
            let mut queue = VecDeque::from([start]);
            comp[start] = count;
            while let Some(u) = queue.pop_front() {
                for &(v, _) in &self.adj[u] {
                    if comp[v] == usize::MAX {
                        comp[v] = count;
                        queue.push_back(v);
                    }
                }
            }
            count += 1;
        }
        (comp, count)
    }

    /// Returns true if the graph is connected (all vertices in one component).
    pub fn is_connected(&self) -> bool {
        if self.v == 0 { return true; }
        let dist = self.bfs(0);
        dist.iter().all(|&d| d != usize::MAX)
    }
}
```

---

## 9. Shortest Path Algorithms

### 9.1 BFS Shortest Path (Unweighted)

Already covered in Section 5.2. Key point: **Only valid for unweighted or unit-weight graphs.**

### 9.2 Dijkstra's Algorithm

**Invariant:** At any point, dist[v] = shortest distance from src to v using only vertices that have been "finalized."

**Mental model:** Greedily expand the nearest unvisited vertex. Like water spreading on a flat plane — the wavefront is always at the frontier of minimum distance.

```
Graph (directed, weighted):
  0 --(4)--> 1
  0 --(1)--> 2
  2 --(2)--> 1
  1 --(5)--> 3
  2 --(8)--> 3
  1 --(1)--> 4
  3 --(2)--> 4

Start: 0. Goal: shortest distances to all.

Initial:  dist=[0, INF, INF, INF, INF]  heap={(0,0)}

Step 1: Pop (0,0). Process edges 0->1(4), 0->2(1).
        dist=[0, 4, 1, INF, INF]  heap={(1,2),(4,1)}

Step 2: Pop (1,2). Process edges 2->1(2): 1+2=3 < 4, update!
        2->3(8): 1+8=9.
        dist=[0, 3, 1, 9, INF]   heap={(3,1),(4,1_stale),(9,3)}

Step 3: Pop (3,1). Process edges 1->3(5): 3+5=8 < 9, update!
        1->4(1): 3+1=4.
        dist=[0, 3, 1, 8, 4]    heap={(4,4),(8,3),(4,1_stale),(9,3_stale)}

Step 4: Pop (4,4). Process edges 4 has no outgoing.
        dist=[0, 3, 1, 8, 4]   heap={(8,3),(stales...)}

Step 5: Pop (8,3). Process edges 3->4(2): 8+2=10 > 4, no update.

Final: dist=[0, 3, 1, 8, 4]

Shortest paths:
  0->0: 0
  0->1: 3  (via 0->2->1)
  0->2: 1  (via 0->2)
  0->3: 8  (via 0->2->1->3)
  0->4: 4  (via 0->2->1->4)
```

**The stale entry problem:** When we update a distance in the heap, we don't remove the old entry. We detect stale entries by checking `if dist[v] < extracted_dist: continue`.

**C — Dijkstra (with Min-Heap via sorted array for small V):**

```c
#define INF INT_MAX

/* Priority queue node */
typedef struct {
    int dist;
    int vertex;
} PQNode;

/* Simple min-heap — replace with proper heap for large graphs */
PQNode pq[MAX_VERTICES * MAX_VERTICES];
int pq_size = 0;

void pq_push(int dist, int vertex) {
    pq[pq_size].dist   = dist;
    pq[pq_size].vertex = vertex;
    pq_size++;
    /* bubble up */
    int i = pq_size - 1;
    while (i > 0) {
        int parent = (i - 1) / 2;
        if (pq[parent].dist <= pq[i].dist) break;
        PQNode tmp  = pq[parent];
        pq[parent]  = pq[i];
        pq[i]       = tmp;
        i = parent;
    }
}

PQNode pq_pop() {
    PQNode ret = pq[0];
    pq[0] = pq[--pq_size];
    /* bubble down */
    int i = 0;
    while (true) {
        int left = 2*i+1, right = 2*i+2, smallest = i;
        if (left  < pq_size && pq[left].dist  < pq[smallest].dist) smallest = left;
        if (right < pq_size && pq[right].dist < pq[smallest].dist) smallest = right;
        if (smallest == i) break;
        PQNode tmp    = pq[smallest];
        pq[smallest]  = pq[i];
        pq[i]         = tmp;
        i = smallest;
    }
    return ret;
}

void dijkstra(const Graph *g, int src, int *dist) {
    for (int i = 0; i < g->V; i++) dist[i] = INF;
    dist[src] = 0;
    pq_size   = 0;
    pq_push(0, src);

    while (pq_size > 0) {
        PQNode top = pq_pop();
        int u      = top.vertex;
        int d      = top.dist;
        if (d > dist[u]) continue; /* stale entry */

        AdjNode *cur = g->adj[u];
        while (cur) {
            int v       = cur->dest;
            int nd      = dist[u] + cur->weight;
            if (nd < dist[v]) {
                dist[v] = nd;
                pq_push(nd, v);
            }
            cur = cur->next;
        }
    }
}
```

**Go — Dijkstra:**

```go
import "container/heap"

type PQItem struct {
    vertex int
    dist   int
    index  int
}

type PriorityQueue []*PQItem

func (pq PriorityQueue) Len() int            { return len(pq) }
func (pq PriorityQueue) Less(i, j int) bool  { return pq[i].dist < pq[j].dist }
func (pq PriorityQueue) Swap(i, j int) {
    pq[i], pq[j] = pq[j], pq[i]
    pq[i].index, pq[j].index = i, j
}
func (pq *PriorityQueue) Push(x interface{}) {
    item := x.(*PQItem)
    item.index = len(*pq)
    *pq = append(*pq, item)
}
func (pq *PriorityQueue) Pop() interface{} {
    old := *pq
    n := len(old)
    item := old[n-1]
    old[n-1] = nil
    *pq = old[:n-1]
    return item
}

const INF = int(^uint(0) >> 1)

// Dijkstra returns shortest distances from src.
func Dijkstra(g *Graph, src int) []int {
    dist := make([]int, g.V)
    for i := range dist {
        dist[i] = INF
    }
    dist[src] = 0

    pq := &PriorityQueue{{vertex: src, dist: 0}}
    heap.Init(pq)

    for pq.Len() > 0 {
        item := heap.Pop(pq).(*PQItem)
        u, d := item.vertex, item.dist
        if d > dist[u] {
            continue // stale
        }
        for _, e := range g.Adj[u] {
            nd := dist[u] + e.Weight
            if nd < dist[e.To] {
                dist[e.To] = nd
                heap.Push(pq, &PQItem{vertex: e.To, dist: nd})
            }
        }
    }
    return dist
}
```

**Rust — Dijkstra:**

```rust
use std::collections::BinaryHeap;
use std::cmp::Reverse;

impl Graph {
    /// Dijkstra's shortest path from src.
    /// Returns dist vector; i64::MAX means unreachable.
    /// REQUIRES: all edge weights >= 0.
    pub fn dijkstra(&self, src: usize) -> Vec<i64> {
        let mut dist = vec![i64::MAX; self.v];
        dist[src] = 0;

        // BinaryHeap is a max-heap; wrap in Reverse for min-heap behavior
        let mut heap = BinaryHeap::new();
        heap.push(Reverse((0i64, src)));

        while let Some(Reverse((d, u))) = heap.pop() {
            if d > dist[u] { continue; } // stale entry

            for &(v, w) in &self.adj[u] {
                let nd = dist[u].saturating_add(w);
                if nd < dist[v] {
                    dist[v] = nd;
                    heap.push(Reverse((nd, v)));
                }
            }
        }
        dist
    }

    /// Dijkstra with path reconstruction.
    pub fn dijkstra_path(&self, src: usize, dst: usize) -> Option<(i64, Vec<usize>)> {
        let mut dist = vec![i64::MAX; self.v];
        let mut prev = vec![usize::MAX; self.v];
        dist[src] = 0;

        let mut heap = BinaryHeap::new();
        heap.push(Reverse((0i64, src)));

        while let Some(Reverse((d, u))) = heap.pop() {
            if u == dst { break; }
            if d > dist[u] { continue; }
            for &(v, w) in &self.adj[u] {
                let nd = dist[u].saturating_add(w);
                if nd < dist[v] {
                    dist[v] = nd;
                    prev[v] = u;
                    heap.push(Reverse((nd, v)));
                }
            }
        }

        if dist[dst] == i64::MAX { return None; }

        let mut path = Vec::new();
        let mut cur = dst;
        while cur != usize::MAX {
            path.push(cur);
            cur = prev[cur];
        }
        path.reverse();
        Some((dist[dst], path))
    }
}
```

### 9.3 Bellman-Ford

**When to use:** Negative edge weights, detecting negative cycles.
**Mental model:** Relax ALL edges V-1 times. After V-1 relaxations, if we can still relax an edge, we're in a negative cycle.

```
Why V-1 iterations?
  Shortest path without negative cycles can visit at most V-1 edges.
  Each iteration guarantees one more "hop" of the path is correct.

Negative cycle detection:
  Run one more (V-th) iteration.
  If any dist[v] decreases: negative cycle exists.
```

**C — Bellman-Ford:**

```c
/* Edge list representation (best for Bellman-Ford) */
typedef struct {
    int u, v, weight;
} EdgeBF;

bool bellman_ford(int V, EdgeBF *edges, int E, int src, int *dist) {
    for (int i = 0; i < V; i++) dist[i] = INF;
    dist[src] = 0;

    for (int i = 0; i < V - 1; i++) {
        bool relaxed = false;
        for (int j = 0; j < E; j++) {
            int u = edges[j].u, v = edges[j].v, w = edges[j].weight;
            if (dist[u] != INF && dist[u] + w < dist[v]) {
                dist[v] = dist[u] + w;
                relaxed = true;
            }
        }
        if (!relaxed) break; /* early termination */
    }

    /* Detect negative cycles */
    for (int j = 0; j < E; j++) {
        int u = edges[j].u, v = edges[j].v, w = edges[j].weight;
        if (dist[u] != INF && dist[u] + w < dist[v]) {
            return false; /* negative cycle detected */
        }
    }
    return true;
}
```

### 9.4 Floyd-Warshall

**When to use:** All-pairs shortest paths. Dense graphs, small V (≤ 500).
**Mental model:** Dynamic programming. `dp[k][i][j]` = shortest path from i to j using intermediate vertices from {0..k}.

```
Recurrence:
  dp[k][i][j] = min(dp[k-1][i][j],  dp[k-1][i][k] + dp[k-1][k][j])
              = "go i->j directly" OR "go i->k then k->j"

Space optimization: compute in-place (dp[i][j] = same as dp[k][i][j])
because dp[k][i][k] = dp[k-1][i][k] (k is not an intermediate to itself).
```

**Rust — Floyd-Warshall:**

```rust
impl Graph {
    /// Floyd-Warshall all-pairs shortest paths.
    /// Returns (dist_matrix, has_negative_cycle).
    /// dist[i][j] = i64::MAX means unreachable.
    pub fn floyd_warshall(&self) -> (Vec<Vec<i64>>, bool) {
        let mut dist = self.to_matrix(); // builds matrix with 0 on diagonal, i64::MAX elsewhere

        // Main DP loop
        for k in 0..self.v {
            for i in 0..self.v {
                for j in 0..self.v {
                    if dist[i][k] != i64::MAX && dist[k][j] != i64::MAX {
                        let through_k = dist[i][k] + dist[k][j];
                        if through_k < dist[i][j] {
                            dist[i][j] = through_k;
                        }
                    }
                }
            }
        }

        // Negative cycle: if dist[i][i] < 0 for any i
        let has_neg_cycle = (0..self.v).any(|i| dist[i][i] < 0);
        (dist, has_neg_cycle)
    }
}
```

### 9.5 A* Search

**When to use:** Single-target shortest path with a good heuristic (e.g., grid/map routing).

```
f(v) = g(v) + h(v)
  g(v) = actual cost from src to v (like Dijkstra's dist)
  h(v) = heuristic estimate from v to dst (must be admissible: h(v) <= actual)

Admissible heuristic examples:
  Grid (no diagonal): Manhattan distance |dx| + |dy|
  Grid (with diagonal): Chebyshev distance max(|dx|, |dy|)
  Euclidean graph: Euclidean distance sqrt(dx^2 + dy^2)

A* is Dijkstra when h(v) = 0 for all v.
```

---

## 10. Minimum Spanning Tree

MST: A spanning tree of a connected undirected graph with minimum total edge weight.

**Key properties:**
- Has exactly V-1 edges
- Is unique if all edge weights are distinct
- Cut property: For any cut (S, V-S), the minimum weight edge crossing the cut is in MST
- Cycle property: The maximum weight edge in any cycle is NOT in MST

### 10.1 Kruskal's Algorithm

**Mental model:** Sort all edges by weight. Add each edge if it doesn't create a cycle (using Union-Find to check).

```
Edges sorted: (1,2,1), (0,3,2), (2,3,3), (1,3,5), (0,1,4)

Step 1: Add (1,2,w=1). Union(1,2). MST={(1,2)}
Step 2: Add (0,3,w=2). Union(0,3). MST={(1,2),(0,3)}
Step 3: Add (2,3,w=3). Union(2,3) -> connects {0,3} and {1,2}. MST={(1,2),(0,3),(2,3)}
Step 4: V-1=3 edges added. STOP.
        (1,3,w=5) and (0,1,w=4) would create cycles.

MST weight = 1+2+3 = 6.
```

**Rust — Kruskal:**

```rust
impl Graph {
    /// Kruskal's MST. Returns (total_weight, list_of_edges).
    /// Requires: undirected, connected graph.
    pub fn kruskal_mst(&self) -> (i64, Vec<(usize, usize, i64)>) {
        // Collect all edges (for undirected, only process each once)
        let mut edges: Vec<(i64, usize, usize)> = Vec::new();
        for u in 0..self.v {
            for &(v, w) in &self.adj[u] {
                if u < v { edges.push((w, u, v)); }
            }
        }
        edges.sort_unstable(); // sort by weight

        let mut parent: Vec<usize> = (0..self.v).collect();
        let mut rank   = vec![0usize; self.v];

        fn find(parent: &mut Vec<usize>, x: usize) -> usize {
            if parent[x] != x {
                parent[x] = find(parent, parent[x]);
            }
            parent[x]
        }

        fn union(parent: &mut Vec<usize>, rank: &mut Vec<usize>, x: usize, y: usize) -> bool {
            let px = find(parent, x);
            let py = find(parent, y);
            if px == py { return false; }
            if rank[px] < rank[py] {
                parent[px] = py;
            } else if rank[px] > rank[py] {
                parent[py] = px;
            } else {
                parent[py] = px;
                rank[px] += 1;
            }
            true
        }

        let mut mst_weight = 0i64;
        let mut mst_edges  = Vec::new();

        for (w, u, v) in edges {
            if union(&mut parent, &mut rank, u, v) {
                mst_weight += w;
                mst_edges.push((u, v, w));
                if mst_edges.len() == self.v - 1 { break; }
            }
        }
        (mst_weight, mst_edges)
    }
}
```

### 10.2 Prim's Algorithm

**Mental model:** Start from any vertex. Greedily add the minimum weight edge that extends the current MST to a new vertex.

```
Like Dijkstra, but key[v] = minimum edge weight to connect v to current MST
(not total path length from source).
```

**Go — Prim:**

```go
// PrimMST returns (total_weight, parent_array).
// parent[v] = u means MST edge is u-v.
func PrimMST(g *Graph) (int, []int) {
    inMST := make([]bool, g.V)
    key    := make([]int, g.V)  // minimum edge weight to reach v
    parent := make([]int, g.V)

    for i := range key {
        key[i]    = INF
        parent[i] = -1
    }
    key[0] = 0 // start from vertex 0

    pq := &PriorityQueue{{vertex: 0, dist: 0}}
    heap.Init(pq)

    totalWeight := 0
    for pq.Len() > 0 {
        item := heap.Pop(pq).(*PQItem)
        u := item.vertex
        if inMST[u] { continue }
        inMST[u] = true
        totalWeight += item.dist

        for _, e := range g.Adj[u] {
            v := e.To
            if !inMST[v] && e.Weight < key[v] {
                key[v]    = e.Weight
                parent[v] = u
                heap.Push(pq, &PQItem{vertex: v, dist: e.Weight})
            }
        }
    }
    return totalWeight, parent
}
```

---

## 11. Strongly Connected Components (SCC)

An SCC is a maximal set of vertices such that there is a path from every vertex to every other vertex.

```
Directed graph:
  0 -> 1 -> 2 -> 0  (cycle: SCC = {0,1,2})
  2 -> 3
  3 -> 4 -> 3       (cycle: SCC = {3,4})

SCCs: {0,1,2}, {3,4}

Note: every vertex is in exactly one SCC.
Condensation DAG: contract each SCC into one node.
  {0,1,2} -> {3,4}
```

### 11.1 Kosaraju's Algorithm

```
Two-pass DFS:
  Pass 1: Run DFS on original graph G. Record finish times.
  Pass 2: Run DFS on G^T (transposed) in REVERSE finish order.
          Each DFS tree in pass 2 is one SCC.

Why it works:
  If SCC A can reach SCC B in G, then in G^T, SCC B can reach SCC A.
  The vertex with HIGHEST finish time in pass 1 is in a "source" SCC.
  Starting from it in G^T, we can only reach that SCC's own vertices.
```

**Go — Kosaraju:**

```go
// KosarajuSCC returns component ID for each vertex and total SCC count.
func KosarajuSCC(g *Graph) ([]int, int) {
    // Pass 1: DFS on G, record finish order
    visited  := make([]bool, g.V)
    finishOrder := make([]int, 0, g.V)

    var dfs1 func(v int)
    dfs1 = func(v int) {
        visited[v] = true
        for _, e := range g.Adj[v] {
            if !visited[e.To] {
                dfs1(e.To)
            }
        }
        finishOrder = append(finishOrder, v)
    }

    for v := 0; v < g.V; v++ {
        if !visited[v] {
            dfs1(v)
        }
    }

    // Pass 2: DFS on transposed graph in reverse finish order
    gt   := g.Transpose()
    comp := make([]int, g.V)
    for i := range comp { comp[i] = -1 }
    numComp := 0

    var dfs2 func(v, c int)
    dfs2 = func(v, c int) {
        comp[v] = c
        for _, e := range gt.Adj[v] {
            if comp[e.To] == -1 {
                dfs2(e.To, c)
            }
        }
    }

    for i := len(finishOrder) - 1; i >= 0; i-- {
        v := finishOrder[i]
        if comp[v] == -1 {
            dfs2(v, numComp)
            numComp++
        }
    }
    return comp, numComp
}
```

### 11.2 Tarjan's Algorithm

**One-pass DFS** using a stack and low-link values. More cache-friendly than Kosaraju.

```
low[v] = min(disc[v], min over DFS back-edges to ancestors)
       = lowest disc value reachable from subtree of v

SCC root condition: disc[v] == low[v]
  When we exit v and disc[v] == low[v], all vertices on the stack
  above v (including v) form one SCC.

Stack invariant:
  Stack contains vertices on the current DFS path whose SCC
  has not been fully determined.
```

**Rust — Tarjan's SCC:**

```rust
pub struct TarjanSCC {
    pub comp:    Vec<usize>,  // component ID per vertex
    pub num_scc: usize,
}

impl Graph {
    pub fn tarjan_scc(&self) -> TarjanSCC {
        let mut disc    = vec![usize::MAX; self.v]; // discovery time
        let mut low     = vec![0usize; self.v];
        let mut on_stack = vec![false; self.v];
        let mut stack   = Vec::new();
        let mut comp    = vec![0usize; self.v];
        let mut timer   = 0usize;
        let mut num_scc = 0usize;

        fn dfs(
            g:        &Graph,
            v:        usize,
            disc:     &mut Vec<usize>,
            low:      &mut Vec<usize>,
            on_stack: &mut Vec<bool>,
            stack:    &mut Vec<usize>,
            comp:     &mut Vec<usize>,
            timer:    &mut usize,
            num_scc:  &mut usize,
        ) {
            disc[v]     = *timer;
            low[v]      = *timer;
            *timer      += 1;
            stack.push(v);
            on_stack[v] = true;

            for &(u, _) in &g.adj[v] {
                if disc[u] == usize::MAX {
                    dfs(g, u, disc, low, on_stack, stack, comp, timer, num_scc);
                    low[v] = low[v].min(low[u]);
                } else if on_stack[u] {
                    low[v] = low[v].min(disc[u]);
                }
            }

            // v is root of an SCC if low[v] == disc[v]
            if low[v] == disc[v] {
                while let Some(w) = stack.pop() {
                    on_stack[w] = false;
                    comp[w]     = *num_scc;
                    if w == v { break; }
                }
                *num_scc += 1;
            }
        }

        for v in 0..self.v {
            if disc[v] == usize::MAX {
                dfs(self, v, &mut disc, &mut low, &mut on_stack,
                    &mut stack, &mut comp, &mut timer, &mut num_scc);
            }
        }

        TarjanSCC { comp, num_scc }
    }
}
```

---

## 12. Bridges and Articulation Points

**Bridge:** An edge whose removal disconnects the graph.
**Articulation point:** A vertex whose removal (along with its edges) disconnects the graph.

```
Graph:
  0 -- 1 -- 2 -- 5
  |    |
  3 -- 4

Bridges: edge (2,5) — removing it disconnects vertex 5.
         edge (1,2) — removing it disconnects {2,5} from rest.
Articulation points: vertex 1 (removal disconnects {2,5} from {0,3,4}),
                     vertex 2 (removal disconnects {5}).

Detection (same algorithm as Tarjan's SCC):
  disc[v] = discovery time
  low[v]  = min disc reachable via DFS subtree or single back edge

Bridge condition for edge (u,v) where v is child of u:
  low[v] > disc[u]
  (v cannot reach any ancestor of u without going through u-v edge)

Articulation point condition for u:
  Case 1: u is root of DFS tree and has >= 2 children
  Case 2: u is not root and has a child v with low[v] >= disc[u]
```

**C — Bridges and Articulation Points:**

```c
int  ap_disc[MAX_VERTICES];
int  ap_low[MAX_VERTICES];
int  ap_parent[MAX_VERTICES];
bool ap_is_ap[MAX_VERTICES];
int  ap_timer;
bool ap_bridges[MAX_VERTICES][MAX_VERTICES]; /* for small graphs */

void ap_dfs(const Graph *g, int u) {
    int children = 0;
    ap_disc[u] = ap_low[u] = ap_timer++;

    AdjNode *cur = g->adj[u];
    while (cur) {
        int v = cur->dest;
        if (ap_disc[v] == -1) {
            children++;
            ap_parent[v] = u;
            ap_dfs(g, v);
            ap_low[u] = ap_low[u] < ap_low[v] ? ap_low[u] : ap_low[v];

            /* Articulation point check */
            if (ap_parent[u] == -1 && children > 1) ap_is_ap[u] = true;
            if (ap_parent[u] != -1 && ap_low[v] >= ap_disc[u]) ap_is_ap[u] = true;

            /* Bridge check */
            if (ap_low[v] > ap_disc[u]) {
                printf("Bridge: %d -- %d\n", u, v);
            }
        } else if (v != ap_parent[u]) {
            ap_low[u] = ap_low[u] < ap_disc[v] ? ap_low[u] : ap_disc[v];
        }
        cur = cur->next;
    }
}

void find_bridges_and_ap(const Graph *g) {
    memset(ap_disc,  -1, sizeof(int)*g->V);
    memset(ap_parent,-1, sizeof(int)*g->V);
    memset(ap_is_ap, false, sizeof(bool)*g->V);
    ap_timer = 0;
    for (int i = 0; i < g->V; i++) {
        if (ap_disc[i] == -1) ap_dfs(g, i);
    }
    printf("Articulation points: ");
    for (int i = 0; i < g->V; i++) {
        if (ap_is_ap[i]) printf("%d ", i);
    }
    printf("\n");
}
```

---

## 13. Bipartite Graph Detection

A graph is bipartite iff it has NO odd-length cycles, iff it is 2-colorable.

```
Bipartite check using BFS 2-coloring:

Graph: 0-1, 1-2, 2-3, 3-0  (even cycle, bipartite)
  Color 0 = RED
  BFS: 0(RED) -> 1(BLUE) -> 2(RED) -> 3(BLUE)
  Check edge 3-0: 3 is BLUE, 0 is RED -> different colors -> OK!
  BIPARTITE. Sets: {0,2}=RED, {1,3}=BLUE.

Non-bipartite: 0-1, 1-2, 2-0  (triangle, odd cycle)
  Color 0 = RED
  BFS: 0(RED) -> 1(BLUE) -> 2(RED)
  Check edge 2-0: 2 is RED, 0 is RED -> CONFLICT! NOT BIPARTITE.
```

**Rust — Bipartite Check:**

```rust
impl Graph {
    /// Returns Some(coloring) if bipartite, None otherwise.
    /// coloring[v] = 0 or 1 indicates which partition v belongs to.
    pub fn bipartite_check(&self) -> Option<Vec<usize>> {
        let mut color = vec![usize::MAX; self.v];

        for start in 0..self.v {
            if color[start] != usize::MAX { continue; }
            color[start] = 0;
            let mut queue = VecDeque::from([start]);

            while let Some(u) = queue.pop_front() {
                for &(v, _) in &self.adj[u] {
                    if color[v] == usize::MAX {
                        color[v] = 1 - color[u];
                        queue.push_back(v);
                    } else if color[v] == color[u] {
                        return None; // conflict: odd cycle
                    }
                }
            }
        }
        Some(color)
    }
}
```

---

## 14. Union-Find (Disjoint Set Union)

The most powerful auxiliary structure for graph connectivity problems.

```
Operations:
  find(x)    : returns representative (root) of x's set
  union(x,y) : merges x's set and y's set

Optimizations:
  Path compression: make every node point directly to root
  Union by rank:    always attach smaller tree under larger tree

Combined complexity: O(alpha(n)) per operation (effectively O(1))
alpha = inverse Ackermann function, grows extremely slowly

Internal structure:

Before union(1,3):
  parent: [0] [1] [2] [3] [4]
           0   1   2   3   4    (each is its own root)

After union(0,1), union(2,3), union(4,2):
  parent: [0] [0] [2] [2] [2]
  Trees:      0       2
             /       / \
            1       3   4

After find(1) with path compression:
  parent[1] -> parent[0] -> 0 (root)
  No change needed (1->0 already direct)

After find(4) with path compression:
  parent[4] -> parent[2] -> 2 (root)
  Set parent[4] = 2 (already direct)
```

**Rust — Full Union-Find:**

```rust
#[derive(Debug, Clone)]
pub struct UnionFind {
    parent: Vec<usize>,
    rank:   Vec<usize>,
    size:   Vec<usize>,  // size of each component
    count:  usize,       // number of components
}

impl UnionFind {
    pub fn new(n: usize) -> Self {
        UnionFind {
            parent: (0..n).collect(),
            rank:   vec![0; n],
            size:   vec![1; n],
            count:  n,
        }
    }

    pub fn find(&mut self, x: usize) -> usize {
        if self.parent[x] != x {
            self.parent[x] = self.find(self.parent[x]); // path compression
        }
        self.parent[x]
    }

    /// Returns true if x and y were in different sets (merged successfully).
    pub fn union(&mut self, x: usize, y: usize) -> bool {
        let px = self.find(x);
        let py = self.find(y);
        if px == py { return false; }

        let (big, small) = if self.rank[px] >= self.rank[py] {
            (px, py)
        } else {
            (py, px)
        };
        self.parent[small] = big;
        self.size[big]    += self.size[small];
        if self.rank[big] == self.rank[small] {
            self.rank[big] += 1;
        }
        self.count -= 1;
        true
    }

    pub fn connected(&mut self, x: usize, y: usize) -> bool {
        self.find(x) == self.find(y)
    }

    pub fn component_size(&mut self, x: usize) -> usize {
        let root = self.find(x);
        self.size[root]
    }

    pub fn num_components(&self) -> usize {
        self.count
    }
}
```

---

## 15. Graph Coloring

Assign colors to vertices so no two adjacent vertices share a color.

```
Chromatic number X(G):
  X(G) = 1: graph has no edges (trivial)
  X(G) = 2: bipartite graph
  X(G) = 3: planar graph requires at most 4 (Four Color Theorem)
  X(G) = k: problem is NP-hard for k >= 3

Greedy coloring (not optimal, but useful):
  For each vertex v in some order:
    Assign smallest color not used by any neighbor.

Greedy may use more colors than optimal.
Better ordering (Welsh-Powell): sort by degree descending.
```

**Go — Greedy Graph Coloring:**

```go
// GreedyColor assigns colors (0-indexed) to all vertices.
// Returns color assignment. Number of colors = max(colors)+1.
func GreedyColor(g *Graph) []int {
    color := make([]int, g.V)
    for i := range color {
        color[i] = -1
    }

    for v := 0; v < g.V; v++ {
        // Find colors used by neighbors
        used := make(map[int]bool)
        for _, e := range g.Adj[v] {
            if color[e.To] != -1 {
                used[color[e.To]] = true
            }
        }
        // Find first unused color
        c := 0
        for used[c] {
            c++
        }
        color[v] = c
    }
    return color
}
```

---

## 16. Eulerian and Hamiltonian Paths

### Eulerian Path/Circuit

```
Eulerian Path: visits every EDGE exactly once.
Eulerian Circuit: Eulerian Path that returns to start.

Conditions (undirected):
  Circuit: every vertex has even degree
  Path:    exactly 2 vertices have odd degree (start and end)

Conditions (directed):
  Circuit: in-degree == out-degree for all vertices
  Path:    one vertex has out-degree - in-degree = 1 (start)
           one vertex has in-degree - out-degree = 1 (end)
           all others: in-degree == out-degree
```

**C — Hierholzer's Algorithm for Eulerian Circuit:**

```c
/* Modifiable adjacency for edge deletion */
int adj_ptr[MAX_VERTICES];  /* current position in adjacency list */
int stack_e[MAX_VERTICES * MAX_VERTICES];
int circuit[MAX_VERTICES * MAX_VERTICES];
int circuit_sz = 0;

void hierholzer(int start, int **adj, int *adj_sz) {
    int stack_top = 0;
    stack_e[stack_top++] = start;

    while (stack_top > 0) {
        int v = stack_e[stack_top - 1];
        /* Find next unvisited edge from v */
        if (adj_ptr[v] < adj_sz[v]) {
            int u = adj[v][adj_ptr[v]++];
            stack_e[stack_top++] = u;
        } else {
            /* No more edges from v: add to circuit */
            circuit[circuit_sz++] = stack_e[--stack_top];
        }
    }
    /* circuit[] is now the Eulerian circuit in reverse */
}
```

### Hamiltonian Path/Circuit

**Hamiltonian Path:** visits every VERTEX exactly once.
**This is NP-complete.** No known polynomial algorithm.

```
Exact: backtracking with pruning — O(n! * n) worst case
Approximation for TSP: Christofides algorithm (1.5x optimal)
DP solution: Held-Karp O(2^n * n^2) — practical up to n=20
```

**Rust — Hamiltonian Bitmask DP (Held-Karp):**

```rust
/// Held-Karp TSP/Hamiltonian path using bitmask DP.
/// Returns minimum cost Hamiltonian path, or i64::MAX if impossible.
/// O(2^n * n^2) — practical for n <= 20.
pub fn held_karp(dist: &Vec<Vec<i64>>) -> i64 {
    let n = dist.len();
    let full = (1 << n) - 1;
    // dp[mask][v] = min cost to visit exactly vertices in mask, ending at v
    let mut dp = vec![vec![i64::MAX; n]; 1 << n];
    dp[1][0] = 0; // start at vertex 0

    for mask in 1usize..=full {
        for last in 0..n {
            if dp[mask][last] == i64::MAX { continue; }
            if mask & (1 << last) == 0 { continue; }
            for next in 0..n {
                if mask & (1 << next) != 0 { continue; }
                let new_mask = mask | (1 << next);
                let cost = dp[mask][last].saturating_add(dist[last][next]);
                if cost < dp[new_mask][next] {
                    dp[new_mask][next] = cost;
                }
            }
        }
    }

    // Minimum over all possible last vertices
    (0..n).map(|v| dp[full][v]).min().unwrap_or(i64::MAX)
}
```

---

## 17. Network Flow

### Ford-Fulkerson / Edmonds-Karp

```
Max-Flow Problem:
  Source s, sink t, each edge has capacity.
  Find maximum flow from s to t.

Key Concepts:
  Residual graph: for each edge (u,v,cap,flow),
    add forward edge capacity (cap-flow) and backward edge (flow).
  Augmenting path: path from s to t in residual graph with capacity > 0.
  Max-flow = sum of flows on all augmenting paths.

Max-Flow Min-Cut Theorem:
  Maximum flow == Minimum cut capacity.
  (A cut separates s from t; its capacity = sum of forward edge capacities.)

Edmonds-Karp: BFS to find shortest augmenting path.
  O(V * E^2)
```

**C — Edmonds-Karp Max-Flow:**

```c
#define MAX_FLOW_V 500

int capacity[MAX_FLOW_V][MAX_FLOW_V]; /* residual capacities */
int flow_parent[MAX_FLOW_V];

int bfs_flow(int s, int t, int V) {
    bool visited[MAX_FLOW_V] = {false};
    int queue[MAX_FLOW_V];
    int front = 0, rear = 0;
    visited[s]      = true;
    flow_parent[s]  = -1;
    queue[rear++]   = s;

    while (front < rear) {
        int u = queue[front++];
        for (int v = 0; v < V; v++) {
            if (!visited[v] && capacity[u][v] > 0) {
                visited[v]     = true;
                flow_parent[v] = u;
                if (v == t) return 1;
                queue[rear++] = v;
            }
        }
    }
    return 0;
}

int max_flow_ek(int s, int t, int V) {
    int total_flow = 0;
    while (bfs_flow(s, t, V)) {
        /* Find bottleneck */
        int path_flow = INT_MAX;
        for (int v = t; v != s; v = flow_parent[v]) {
            int u = flow_parent[v];
            path_flow = path_flow < capacity[u][v] ? path_flow : capacity[u][v];
        }
        /* Update residual capacities */
        for (int v = t; v != s; v = flow_parent[v]) {
            int u = flow_parent[v];
            capacity[u][v] -= path_flow;
            capacity[v][u] += path_flow;
        }
        total_flow += path_flow;
    }
    return total_flow;
}
```

---

## 18. What You CANNOT Do — Common Mistakes and Pitfalls

This section is the most valuable for reaching expert level. These are the errors that separate junior engineers from senior engineers.

---

### MISTAKE 1: Modifying the Graph While Traversing It

```
WRONG (Go):
  for v := 0; v < g.V; v++ {
      for _, e := range g.Adj[v] {
          g.AddEdge(e.To, v, e.Weight)  // DISASTER: modifies g.Adj while ranging
      }
  }

WHY IT FAILS:
  append() may allocate a new backing array.
  The range loop captured the slice header at loop start.
  New edges may or may not be seen, depending on whether reallocation occurred.
  Result: undefined, non-deterministic behavior.

CORRECT: Collect changes first, then apply.
  var toAdd []struct{u, v, w int}
  for u := 0; u < g.V; u++ {
      for _, e := range g.Adj[u] {
          toAdd = append(toAdd, struct{u,v,w int}{e.To, u, e.Weight})
      }
  }
  for _, e := range toAdd {
      g.AddEdge(e.u, e.v, e.w)
  }
```

---

### MISTAKE 2: Forgetting to Mark Visited Before Enqueuing (BFS)

```
WRONG:
  queue.push(src)
  while queue not empty:
      u = queue.pop()
      visited[u] = true       // WRONG: mark on dequeue
      for v in neighbors(u):
          if not visited[v]:
              queue.push(v)   // v may be pushed MULTIPLE TIMES

WHY IT FAILS:
  Between pushing v and dequeuing it, another path may also push v.
  V is processed multiple times -> incorrect distances, infinite loops.

CORRECT:
  visited[src] = true
  queue.push(src)
  while queue not empty:
      u = queue.pop()         // mark on ENQUEUE, not dequeue
      for v in neighbors(u):
          if not visited[v]:
              visited[v] = true
              queue.push(v)
```

---

### MISTAKE 3: Using Recursive DFS on Deep Graphs (Stack Overflow)

```
Default system stack: ~8MB on Linux
Typical frame size: ~100-400 bytes
Max recursion depth: ~20,000 - 80,000 levels

A path graph with 1,000,000 nodes -> STACK OVERFLOW.

WRONG:
  fn dfs(g: &Graph, v: usize, visited: &mut Vec<bool>) {
      visited[v] = true;
      for &(u, _) in &g.adj[v] {
          if !visited[u] { dfs(g, u, visited); }  // OVERFLOW on deep graphs
      }
  }

CORRECT options:
  1. Use iterative DFS with explicit stack (see Section 5.3)
  2. Increase stack size:
     In Rust: std::thread::Builder::new().stack_size(64 * 1024 * 1024).spawn(...)
     In Go:   goroutines auto-grow stack (safe, but not unlimited)
     In C:    ulimit -s unlimited or explicit stack allocation

RULE: Use iterative DFS whenever graph depth could exceed 10,000.
```

---

### MISTAKE 4: Running Dijkstra on Negative-Weight Graphs

```
WHY DIJKSTRA FAILS with negative weights:

Graph: 0 --(5)--> 1
       0 --(3)--> 2
       2 --(-4)-> 1

Dijkstra from 0:
  dist=[0, INF, INF]
  Pop (0,0): update 1 to 5, 2 to 3. dist=[0,5,3]
  Pop (3,2): update 1 via 2: 3+(-4)=-1. dist=[0,-1,3] -- WAIT
             But vertex 1 was ALREADY "finalized" in many implementations!

The greedy invariant: "the extracted vertex has optimal distance"
BREAKS when negative edges exist, because a future path via negative
edge might yield a shorter distance.

RULE:
  Negative weights? -> Use Bellman-Ford (or SPFA for sparse graphs).
  Negative cycle?   -> Bellman-Ford detects it; Dijkstra loops forever or gives wrong answer.

EXCEPTION: Johnson's algorithm converts negative weights to non-negative
           using Bellman-Ford as preprocessing, then runs Dijkstra for each vertex.
           O(V^2 log V + VE) -- best for sparse all-pairs shortest paths.
```

---

### MISTAKE 5: Forgetting Multi-Edge or Self-Loop Handling

```
For simple graph algorithms, self-loops and multi-edges can break invariants.

Self-loop (v, v):
  Cycle detection: A self-loop is trivially a cycle.
                   But naive DFS with "parent tracking" won't catch (v,v)
                   if you only check parent[v] != v.
  Degree: Self-loops contribute 2 to degree in some definitions, 1 in others.
           Pick a convention and document it.

Multi-edges (u,v appearing multiple times):
  Minimum spanning tree: if two edges connect u and v, only the lighter matters.
  Flow problems: sum capacities or treat as separate paths?
  Depends on problem domain.

RULE: Always clarify upfront whether the graph is SIMPLE.
      If not, add explicit handling for self-loops and parallel edges.
```

---

### MISTAKE 6: Integer Overflow in Distance Computations

```
WRONG (C):
  int dist[V];
  // Initialize to INT_MAX = 2,147,483,647
  // Then:
  if (dist[u] + weight < dist[v])  // OVERFLOW if dist[u] is INT_MAX!
      dist[v] = dist[u] + weight;

INT_MAX + any_positive = negative (overflow) -> WRONG comparison.

CORRECT:
  if (dist[u] != INT_MAX && dist[u] + weight < dist[v])
      dist[v] = dist[u] + weight;

In Rust: use saturating_add() to avoid overflow:
  let nd = dist[u].saturating_add(w);
  // i64::MAX.saturating_add(1) = i64::MAX, not negative

In Go: use explicit INF sentinel that won't overflow:
  const INF = 1 << 60  // safe for i64 arithmetic
```

---

### MISTAKE 7: Wrong Edge Direction in Directed Graphs

```
PROBLEM: Accidentally adding reverse edges in directed graphs.

WRONG (C, undirected logic applied to directed):
  void add_edge(Graph *g, int u, int v, int w) {
      // adds both directions -- WRONG for directed!
      prepend(g->adj[u], v, w);
      prepend(g->adj[v], u, w);  // should NOT exist for directed graph
  }

SYMPTOM: Topological sort fails (finds cycle in what should be a DAG).
         Shortest path is wrong (can traverse edge backwards).
         SCC algorithm finds wrong components.

RULE: Always have a `directed` flag. Use it consistently.
      Run a sanity check: for directed graphs, |edges in adj lists| == |E|.
      For undirected: |edges in adj lists| == 2 * |E|.
```

---

### MISTAKE 8: Using Visited Array Without Reset Between Multiple Queries

```
WRONG:
  bool visited[MAX_V] = {false};
  // First query:
  bfs(g, 0, visited);  // visited now has state from query 1
  // Second query:
  bfs(g, 3, visited);  // BFS from 3 skips already-visited nodes -> WRONG

CORRECT:
  // Reset before each query:
  memset(visited, false, sizeof(bool) * V);
  bfs(g, 3, visited);

In Rust: pass fresh visited vector each time.
In Go:   allocate new slice or use fill:
  for i := range visited { visited[i] = false }
```

---

### MISTAKE 9: Off-by-One in Adjacency Matrix

```
WRONG:
  int adj[N][N];
  adj[N][0] = 1;   // INDEX OUT OF BOUNDS — N is valid size, N-1 is max index!

  for (int i = 0; i <= N; i++)  // should be i < N
      for (int j = 0; j <= N; j++)
          adj[i][j] = 0;

COMMON SOURCE: Mixing 0-indexed and 1-indexed vertex numbering.

If vertices are labeled 1..N in the problem but arrays are 0..N-1:
  EITHER: shift all vertex labels (v - 1) consistently at input time.
  OR:     allocate adj[N+1][N+1] and use 1-based indexing throughout.
  NEVER:  mix both conventions in the same code.
```

---

### MISTAKE 10: Confusing BFS Level with DFS Depth in Path Length

```
BFS dist[v] = shortest path length (edges) from source to v.
DFS does NOT give shortest path. It gives ONE path, not necessarily shortest.

WRONG:
  // I want shortest path from 0 to 5.
  dfs(g, 0);
  return depth[5];  // WRONG: DFS depth != shortest path

CORRECT:
  dist = bfs(g, 0);
  return dist[5];

Exception: On a TREE, DFS depth == BFS dist (since there's only one path).
```

---

### MISTAKE 11: Not Handling Disconnected Graphs

```
WRONG:
  // "Find if vertex 5 is reachable from vertex 0"
  bfs(g, 0);
  return true; // assumes all vertices are reachable -- WRONG

  // "Topological sort"
  dfs_topo(g, 0);  // only processes component containing 0 -- MISSES others

CORRECT:
  Always iterate over all vertices as starting points:
  for v in 0..V:
      if not visited[v]:
          dfs/bfs(g, v)

  For topological sort: Kahn's algorithm naturally handles disconnected DAGs.
  For DFS topo sort: the outer loop covers all components.
```

---

### MISTAKE 12: Assuming Unique Shortest Paths

```
Multiple shortest paths may exist. If you need ALL shortest paths,
or if tie-breaking matters (e.g., lexicographically smallest),
standard Dijkstra doesn't suffice.

WRONG assumption:
  // "Find the lexicographically smallest shortest path"
  bfs(g, src);  // finds A shortest path, but not necessarily smallest lex

CORRECT:
  Modify BFS to track all predecessors (prev[v] = list of all u where dist[u]+1==dist[v]).
  Then reconstruct all paths and pick smallest lexicographically.

  Or: BFS with pair (dist, vertex) and use a comparator that breaks ties by vertex ID.
```

---

### MISTAKE 13: Wrong Complexity Assumptions (Dense vs Sparse)

```
WRONG:
  // Graph has 10^6 vertices, 10^6 edges (sparse).
  // Using adjacency matrix:
  bool adj[1000000][1000000]; // 10^12 bytes = IMPOSSIBLE

  // Iterating over all V vertices in each BFS step:
  for (int v = 0; v < V; v++) {  // O(V) per step
      if (adj[u][v]) ...          // for sparse graph: O(V*V) = O(E * V) total
  }

CORRECT: Use adjacency list for sparse graphs.
  Total BFS time: O(V + E) -- iterates over each edge exactly once.

MENTAL MODEL:
  Always compute m/n ratio (E/V ratio).
  E/V < 10: sparse, use adjacency list.
  E/V > n/2: dense, adjacency matrix may be fine.
```

---

### MISTAKE 14: Stale Entries in Dijkstra's Heap

```
WRONG:
  // Updating distance without detecting stale entries:
  while heap not empty:
      (d, u) = heap.pop()
      // Missing check: if d > dist[u]: continue
      for each neighbor v of u:
          relax...

WHY IT'S WRONG:
  When we update dist[v], we push a new (smaller_dist, v) to heap.
  The OLD (larger_dist, v) remains in heap.
  When we later pop the stale (larger_dist, v), we re-process u
  with a WRONG distance d, potentially relaxing edges incorrectly.

CORRECT:
  while heap not empty:
      (d, u) = heap.pop()
      if d > dist[u]: continue  // THIS LINE IS CRITICAL
      for each neighbor v of u:
          relax...
```

---

### MISTAKE 15: Undirected Graph — Processing Each Edge Twice

```
For undirected graph stored as adjacency list, edge (u,v) appears in
both adj[u] and adj[v]. Operations that should run once per edge
accidentally run twice.

WRONG (collecting all edges):
  for u in 0..V:
      for (v, w) in adj[u]:
          edges.push((u, v, w))  // DUPLICATE: (u,v,w) AND (v,u,w) both added

CORRECT:
  for u in 0..V:
      for (v, w) in adj[u]:
          if u < v:              // only process each pair once
              edges.push((u, v, w))

This is critical for:
  - Kruskal's MST (sorting edges)
  - Counting edges
  - Any algorithm that processes edge set E
```

---

### MISTAKE 16: Assuming Graph Is a Tree When It May Not Be

```
Trees have special properties not shared by general graphs:
  - Unique path between any two vertices
  - No cycles
  - |E| = |V| - 1

WRONG:
  // Finding LCA (Lowest Common Ancestor) using binary lifting
  // Algorithm assumes TREE structure.
  // If input has cycles (not a tree), binary lifting gives wrong answers.

WRONG:
  // "The graph has n vertices and n-1 edges, so it must be a tree."
  // WRONG: a disconnected graph can have n-1 edges without being a tree.
  //        Example: {0-1, 2-3, 4} = 5 vertices, 2 edges (n-1 = 4 = WRONG example)
  //        More precise: {0-1, 1-2, 3-4-5} = 6 vertices, 4 edges = not a tree.
  //        You need CONNECTED + |E| = |V| - 1 for a tree guarantee.

CORRECT:
  Check: connected AND |E| == |V| - 1 AND no cycle.
  (Any two of these three imply the third.)
```

---

### MISTAKE 17: Infinite Loop in DFS Due to Undirected Self-Loops

```
Self-loop edge (v, v) in undirected adjacency list:
  adj[v] contains v (both directions of same self-loop)

DFS: We're at vertex v, parent = p.
     We see neighbor v.
     Check: v != parent? YES (v != p, assuming p is some other vertex)
     -> dfs(v) again! Infinite recursion.

CORRECT:
  // Skip self-loops explicitly:
  for neighbor in adj[v]:
      if neighbor == v: continue  // self-loop
      if neighbor == parent: continue
      if not visited: dfs(neighbor, v)
```

---

### MISTAKE 18: Forgetting to Handle the `0-weight edge` vs `no edge` Distinction in Matrices

```
WRONG:
  int adj[N][N] = {0};  // 0 means "no edge"
  adj[0][1] = 0;        // wait, is this an edge with weight 0 or no edge?
  
  if (adj[u][v] != 0) { // WRONG: misses valid 0-weight edges
      relax...
  }

CORRECT options:
  1. Use sentinel: -1 or INT_MAX for "no edge", 0 is valid weight.
  2. Use boolean edge matrix + separate weight matrix.
  3. Use Option<i64> in Rust:
     adj[u][v] = Some(0)  vs  adj[u][v] = None

  In Rust:
  let mat: Vec<Vec<Option<i64>>> = vec![vec![None; V]; V];
  mat[u][v] = Some(weight);  // 0-weight edge is Some(0), not None
```

---

### MISTAKE 19: Negative Cycle with Floyd-Warshall

```
After Floyd-Warshall, if dist[i][i] < 0 for any i:
  There is a negative cycle reachable from i.
  Shortest paths through this cycle are -infinity.

WRONG:
  // Just reading dist[i][j] after Floyd-Warshall:
  return dist[src][dst]  // may be meaningless if negative cycle exists

CORRECT:
  Check all dist[i][i] after running Floyd-Warshall.
  If negative cycle exists on any path from src to dst:
    shortest distance = -infinity (problem is ill-defined for shortest path)

Also: if using dist for DP on top of Floyd-Warshall,
      and a vertex on your DP path has dist[v][v] < 0:
      the DP value is invalid.
```

---

### MISTAKE 20: Union-Find Without Path Compression on Large Inputs

```
Union-Find without path compression:
  find(x) traverses parent chain to root -> O(log n) per operation (with rank).
  Without rank either: O(n) worst case (degenerates to linked list).

O(n log n) or O(n^2) for n operations = TLE on large inputs.

CORRECT: Always use BOTH path compression AND union by rank.
  Path compression alone: O(log n) amortized
  Union by rank alone:    O(log n) per operation
  Both:                   O(alpha(n)) ≈ O(1) per operation

In Rust:
  fn find(&mut self, x: usize) -> usize {
      if self.parent[x] != x {
          self.parent[x] = self.find(self.parent[x]); // <- PATH COMPRESSION
      }
      self.parent[x]
  }
```

---

## 19. Complexity Reference Table

| Algorithm                    | Time                     | Space      | Notes                                    |
|------------------------------|--------------------------|------------|------------------------------------------|
| DFS                          | O(V + E)                 | O(V)       | Recursion depth up to O(V)              |
| BFS                          | O(V + E)                 | O(V)       | Queue size up to O(V)                   |
| Topo Sort (DFS)              | O(V + E)                 | O(V)       | DAG only                                |
| Topo Sort (Kahn's)           | O(V + E)                 | O(V)       | DAG only; detects cycles                |
| Dijkstra (binary heap)       | O((V + E) log V)         | O(V)       | Non-negative weights only               |
| Dijkstra (Fibonacci heap)    | O(E + V log V)           | O(V)       | Theoretically optimal, rarely used      |
| Bellman-Ford                 | O(V * E)                 | O(V)       | Handles negatives; detects neg cycles   |
| Floyd-Warshall               | O(V³)                    | O(V²)      | All-pairs; dense graphs                 |
| Johnson's                    | O(VE + V² log V)         | O(V²)      | All-pairs sparse; uses B-F + Dijkstra   |
| Kruskal's MST                | O(E log E)               | O(V)       | Dominated by sort; sparse graphs        |
| Prim's MST (binary heap)     | O((V + E) log V)         | O(V)       | Dense graphs: use O(V²) variant         |
| Kosaraju's SCC               | O(V + E)                 | O(V)       | Two DFS passes + graph transpose        |
| Tarjan's SCC                 | O(V + E)                 | O(V)       | Single DFS pass                         |
| Bridges/Articulation Pts     | O(V + E)                 | O(V)       | Single DFS with low-link values         |
| Bipartite Check              | O(V + E)                 | O(V)       | BFS/DFS 2-coloring                      |
| Union-Find (with both opts)  | O(alpha(n)) per op       | O(V)       | Effectively O(1) per operation          |
| Edmonds-Karp (Max Flow)      | O(V * E²)                | O(V²)      | BFS augmenting paths                    |
| Dinic's Max Flow             | O(V² * E)                | O(V + E)   | Level graph; faster in practice         |
| Held-Karp (TSP)              | O(2^n * n²)              | O(2^n * n) | Exact TSP; n ≤ 20 practical             |
| Hamiltonian path (backtrack) | O(n!)                    | O(n)       | NP-complete; brute force                |
| Graph Coloring (exact)       | NP-hard                  | —          | Greedy is polynomial but not optimal    |

---

## 20. Mental Models for Expert Graph Thinking

### 1. The Representation-First Principle

Before writing any algorithm, answer: **"What operations will dominate?"**
- Mostly traversal? -> Adjacency list
- Mostly edge queries? -> Adjacency matrix or HashSet neighbors
- Sorting edges? -> Edge list
- Production, large scale, cache-sensitive? -> CSR

### 2. The "What Changes DFS Visits" Mental Model

Every major DFS-based algorithm differs in what happens at:
- **Entry** (pre-order): node coloring, discovery time
- **Exit** (post-order): finish time, topological order, SCC detection
- **Edge processing**: cycle detection (back edges), bridge detection (low-link)

If you see a new DFS-based algorithm, immediately classify each of these.

### 3. The Cut-Cycle Duality

Every graph optimization problem has a dual:
- MST uses the **cut property** (min edge crossing a cut is in MST)
- MST uses the **cycle property** (max edge in a cycle is NOT in MST)
- Max-Flow / Min-Cut are **exactly dual** (max flow = min cut capacity)
- Understanding duality instantly doubles your algorithmic toolkit.

### 4. The Reduction Lens

Most problems ARE graph problems in disguise:
- "Can we schedule all tasks?" -> Topological sort on dependency DAG
- "Are these constraints satisfiable?" -> 2-SAT on implication graph
- "Minimum number of swaps?" -> Cycle decomposition on permutation graph
- "Maximum matching?" -> Network flow
- "Interval overlap?" -> Interval graph coloring

Train yourself to see graphs underneath every combinatorial problem.

### 5. The Level-Set Intuition for BFS

BFS doesn't just find shortest paths — it partitions the graph into **levels** (distance layers). Any problem involving "minimum steps," "minimum operations," or "minimum transformations" from a state is BFS on a **state graph** where:
- Nodes = states
- Edges = valid transitions
- Distance = minimum operations needed

Word ladder, puzzle solving, minimum coin changes — all are BFS on implicit graphs.

### 6. The Greedy Safety Condition

Dijkstra and Prim are greedy. Greedy works here because of a **matroid structure** (or a similar exchange argument):
- The set of edges in a partial MST can always be extended to a full MST (matroid independence)
- The set of relaxed vertices in Dijkstra has the property that no future relaxation can improve them (non-negative weights enforce this)

When you see a new greedy graph algorithm, ask: "What is the exchange argument that proves this greedy choice is safe?"

### 7. Chunking: Vertices as States, Edges as Transitions

The deepest insight in graph algorithms: **a graph is a state machine.** Vertices are states, edges are valid transitions. Every algorithm is a policy for exploring or optimizing over state transitions.

When you see a new problem: "What is the state? What transitions are valid? What am I optimizing?" -> You have reduced it to a graph problem, and you know how to solve graph problems.

---

*This guide is a living reference. The depth you build here — in representations, traversals, algorithms, and anti-patterns — forms the irreducible foundation of competitive programming, system design interviews, and production graph systems alike. Internalize these patterns until they are reflexes, not recollections.*
