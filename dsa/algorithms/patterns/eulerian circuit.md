# Eulerian Circuit Patterns: The Complete Mastery Guide

## I. Foundational Theory & Mathematical Rigour

### Core Definitions

An **Eulerian Path** traverses every edge of a graph exactly once.
An **Eulerian Circuit** is an Eulerian path that starts and ends at the same vertex.

**Fundamental Theorem (Euler, 1736):**
- A connected graph has an Eulerian Circuit ⟺ every vertex has even degree
- A connected graph has an Eulerian Path (but not circuit) ⟺ exactly two vertices have odd degree

**Mental Model:** Think of each edge as a "token of passage" — you must spend every token exactly once. Degree parity determines whether you can return home.

### Why This Matters

Eulerian patterns appear in:
- DNA sequencing (de Bruijn graphs)
- Network routing optimization
- Circuit design verification
- Chinese Postman Problem
- Cryptographic constructions

## II. Pattern Recognition Framework

### Pattern 1: Degree Analysis (Validation Layer)

Before attempting construction, verify feasibility in O(V + E):

```rust
// Rust: Idiomatic degree checking with explicit error types
use std::collections::HashMap;

#[derive(Debug)]
enum EulerianType {
    Circuit,
    Path(usize, usize), // (start, end) vertices
    None,
}

fn classify_graph(adj: &HashMap<usize, Vec<usize>>) -> EulerianType {
    let mut degree: HashMap<usize, i32> = HashMap::new();
    
    // Count degrees (undirected: each edge counted twice)
    for (&u, neighbors) in adj {
        *degree.entry(u).or_insert(0) += neighbors.len() as i32;
    }
    
    let odd_vertices: Vec<usize> = degree
        .iter()
        .filter(|(_, &deg)| deg % 2 != 0)
        .map(|(&v, _)| v)
        .collect();
    
    match odd_vertices.len() {
        0 => EulerianType::Circuit,
        2 => EulerianType::Path(odd_vertices[0], odd_vertices[1]),
        _ => EulerianType::None,
    }
}
```

**Cognitive Principle:** *Fail fast, validate early*. Spend O(V+E) to avoid wasting O(E) on impossible constructions.

### Pattern 2: Hierholzer's Algorithm (Construction Layer)

**Core Insight:** Build circuit by merging smaller cycles. This exploits the property that removing an Eulerian circuit from a graph with all even degrees leaves a graph where remaining vertices still have even degrees.

**Algorithm Intuition:**
1. Start DFS from any vertex
2. Greedily traverse edges, removing them
3. When stuck, you've found a cycle
4. Backtrack and insert sub-cycles into the main path

```rust
use std::collections::{HashMap, HashSet};

struct EulerianCircuit {
    adj: HashMap<usize, Vec<usize>>,
    used_edges: HashSet<(usize, usize)>,
}

impl EulerianCircuit {
    fn new(edges: Vec<(usize, usize)>) -> Self {
        let mut adj: HashMap<usize, Vec<usize>> = HashMap::new();
        
        for &(u, v) in &edges {
            adj.entry(u).or_insert_with(Vec::new).push(v);
            adj.entry(v).or_insert_with(Vec::new).push(u);
        }
        
        Self {
            adj,
            used_edges: HashSet::new(),
        }
    }
    
    fn find_circuit(&mut self, start: usize) -> Vec<usize> {
        let mut stack = vec![start];
        let mut circuit = Vec::new();
        
        while let Some(&curr) = stack.last() {
            if let Some(neighbors) = self.adj.get_mut(&curr) {
                // Find an unused edge
                if let Some(pos) = neighbors.iter().position(|&next| {
                    let edge = Self::normalize_edge(curr, next);
                    !self.used_edges.contains(&edge)
                }) {
                    let next = neighbors[pos];
                    let edge = Self::normalize_edge(curr, next);
                    self.used_edges.insert(edge);
                    stack.push(next);
                } else {
                    // No unused edges from curr - backtrack
                    circuit.push(stack.pop().unwrap());
                }
            } else {
                circuit.push(stack.pop().unwrap());
            }
        }
        
        circuit.reverse();
        circuit
    }
    
    // Normalize edge representation for undirected graphs
    fn normalize_edge(u: usize, v: usize) -> (usize, usize) {
        if u < v { (u, v) } else { (v, u) }
    }
}
```

**Time Complexity:** O(E) — each edge visited exactly once
**Space Complexity:** O(V + E) — recursion stack + edge tracking

**Go Implementation (Iterative, Idiomatic):**

```go
package eulerian

type Graph struct {
    adj       map[int][]int
    usedEdges map[[2]int]bool
}

func NewGraph(edges [][2]int) *Graph {
    g := &Graph{
        adj:       make(map[int][]int),
        usedEdges: make(map[[2]int]bool),
    }
    
    for _, edge := range edges {
        u, v := edge[0], edge[1]
        g.adj[u] = append(g.adj[u], v)
        g.adj[v] = append(g.adj[v], u)
    }
    
    return g
}

func (g *Graph) FindCircuit(start int) []int {
    stack := []int{start}
    circuit := []int{}
    
    for len(stack) > 0 {
        curr := stack[len(stack)-1]
        found := false
        
        for i, next := range g.adj[curr] {
            edge := normalizeEdge(curr, next)
            if !g.usedEdges[edge] {
                g.usedEdges[edge] = true
                stack = append(stack, next)
                found = true
                break
            }
        }
        
        if !found {
            circuit = append(circuit, stack[len(stack)-1])
            stack = stack[:len(stack)-1]
        }
    }
    
    // Reverse circuit
    for i, j := 0, len(circuit)-1; i < j; i, j = i+1, j-1 {
        circuit[i], circuit[j] = circuit[j], circuit[i]
    }
    
    return circuit
}

func normalizeEdge(u, v int) [2]int {
    if u < v {
        return [2]int{u, v}
    }
    return [2]int{v, u}
}
```

### Pattern 3: Directed Graphs (Asymmetric Degree Analysis)

For directed graphs, the condition changes:
- **Eulerian Circuit:** in-degree(v) = out-degree(v) for all vertices
- **Eulerian Path:** All vertices balanced except: one with out-deg = in-deg + 1 (start), one with in-deg = out-deg + 1 (end)

```rust
fn classify_directed(adj: &HashMap<usize, Vec<usize>>) -> EulerianType {
    let mut in_deg: HashMap<usize, i32> = HashMap::new();
    let mut out_deg: HashMap<usize, i32> = HashMap::new();
    
    for (&u, neighbors) in adj {
        *out_deg.entry(u).or_insert(0) += neighbors.len() as i32;
        for &v in neighbors {
            *in_deg.entry(v).or_insert(0) += 1;
        }
    }
    
    let mut start_candidates = Vec::new();
    let mut end_candidates = Vec::new();
    
    for &v in adj.keys() {
        let in_d = *in_deg.get(&v).unwrap_or(&0);
        let out_d = *out_deg.get(&v).unwrap_or(&0);
        let diff = out_d - in_d;
        
        match diff {
            1 => start_candidates.push(v),
            -1 => end_candidates.push(v),
            0 => {},
            _ => return EulerianType::None,
        }
    }
    
    match (start_candidates.len(), end_candidates.len()) {
        (0, 0) => EulerianType::Circuit,
        (1, 1) => EulerianType::Path(start_candidates[0], end_candidates[0]),
        _ => EulerianType::None,
    }
}
```

## III. Advanced Problem Patterns

### Pattern 4: Edge Reconstruction (Itinerary Problems)

**Canonical Problem:** Reconstruct Valid Airplane Itinerary (LeetCode 332)

**Key Insight:** Treat tickets as directed edges. Use lexicographic ordering for tie-breaking.

```rust
use std::collections::{HashMap, BinaryHeap};
use std::cmp::Reverse;

fn find_itinerary(tickets: Vec<Vec<String>>) -> Vec<String> {
    let mut graph: HashMap<String, BinaryHeap<Reverse<String>>> = HashMap::new();
    
    // Build adjacency list with min-heap for lexicographic order
    for ticket in tickets {
        graph.entry(ticket[0].clone())
            .or_insert_with(BinaryHeap::new)
            .push(Reverse(ticket[1].clone()));
    }
    
    let mut result = Vec::new();
    let mut stack = vec!["JFK".to_string()];
    
    while let Some(curr) = stack.last().cloned() {
        if let Some(neighbors) = graph.get_mut(&curr) {
            if let Some(Reverse(next)) = neighbors.pop() {
                stack.push(next);
                continue;
            }
        }
        result.push(stack.pop().unwrap());
    }
    
    result.reverse();
    result
}
```

**Mental Model:** The BinaryHeap ensures we always take the lexicographically smallest edge — Hierholzer's algorithm naturally handles the Eulerian path construction.

**Complexity:** O(E log E) due to heap operations

### Pattern 5: String Reconstruction (de Bruijn Graphs)

**Problem:** Find the shortest superstring containing all k-mers

**Transformation:** Create graph where:
- Nodes = (k-1)-mers
- Edges = k-mers
- Eulerian path in this graph = superstring

**Example:** k=3, words = ["abc", "bcd", "cda"]
- Nodes: "ab", "bc", "cd", "da"
- Edges: ab→bc (abc), bc→cd (bcd), cd→da (cda)
- Path: ab→bc→cd→da represents "abcda"

```go
func shortestSuperstring(words []string) string {
    if len(words) == 0 {
        return ""
    }
    
    k := len(words[0])
    graph := make(map[string][]string)
    inDegree := make(map[string]int)
    outDegree := make(map[string]int)
    
    // Build de Bruijn graph
    for _, word := range words {
        prefix := word[:k-1]
        suffix := word[1:]
        
        graph[prefix] = append(graph[prefix], suffix)
        outDegree[prefix]++
        inDegree[suffix]++
    }
    
    // Find start vertex (out-degree > in-degree)
    var start string
    for node := range graph {
        if outDegree[node] > inDegree[node] {
            start = node
            break
        }
    }
    
    if start == "" {
        // Circuit exists, start anywhere
        for node := range graph {
            start = node
            break
        }
    }
    
    // Run Hierholzer's algorithm
    path := hierholzer(graph, start)
    
    // Reconstruct superstring
    return reconstructString(path, k)
}
```

### Pattern 6: Making Graphs Eulerian (Chinese Postman)

**Problem:** Given a graph without an Eulerian circuit, find the minimum edges to add to make it Eulerian.

**Strategy:**
1. Find all odd-degree vertices (there's always an even number)
2. Find minimum-weight perfect matching between odd vertices
3. Add matching edges to graph

**Complexity:** O(V³) for maximum weighted matching

## IV. Implementation Nuances & Optimization

### Edge Deletion Strategy

**Three Approaches:**

1. **Mark-and-Skip** (Used above): O(1) deletion check, O(deg(v)) to find unused edge
2. **Actual Removal**: O(deg(v)) deletion, O(1) to get next edge
3. **Index Tracking**: O(1) for both, but requires array-based adjacency

```rust
// Approach 3: Index-based (fastest for dense graphs)
struct FastEulerian {
    adj: Vec<Vec<usize>>,
    edge_idx: Vec<usize>, // Current index for each vertex
}

impl FastEulerian {
    fn find_circuit(&mut self, start: usize) -> Vec<usize> {
        let mut stack = vec![start];
        let mut circuit = Vec::new();
        
        while let Some(&curr) = stack.last() {
            let idx = self.edge_idx[curr];
            
            if idx < self.adj[curr].len() {
                let next = self.adj[curr][idx];
                self.edge_idx[curr] += 1;
                stack.push(next);
            } else {
                circuit.push(stack.pop().unwrap());
            }
        }
        
        circuit.reverse();
        circuit
    }
}
```

### Parallel Edge Handling

For multigraphs (multiple edges between vertices):

```rust
// Use edge ID instead of vertex pairs
type EdgeId = usize;
struct Multigraph {
    adj: HashMap<usize, Vec<EdgeId>>,
    edges: Vec<(usize, usize)>, // EdgeId -> (u, v)
    used: Vec<bool>,
}
```

## V. Problem-Solving Mental Models

### Model 1: The "Unraveling Thread" Metaphor

Imagine a tangled ball of thread. An Eulerian circuit is one continuous thread — no breaks, no doubling back. Odd-degree vertices are "loose ends" where the thread must start or stop.

### Model 2: The "Balance Sheet" Principle

Every edge you enter a vertex is a "debit", every edge you leave is a "credit". For a circuit, every vertex must balance (in = out). For a path, exactly one vertex has +1 balance (start) and one has -1 (end).

### Model 3: The "Greedy Burn" Strategy

Hierholzer's algorithm greedily "burns bridges" — once traversed, an edge is consumed. The stack remembers "unfinished business" — vertices with remaining edges to explore.

## VI. Common Pitfalls & Debugging

### Pitfall 1: Forgetting Connectivity Check

Even if all degrees are even, disconnected components prevent an Eulerian circuit.

```rust
fn is_connected(adj: &HashMap<usize, Vec<usize>>) -> bool {
    if adj.is_empty() { return true; }
    
    let start = *adj.keys().next().unwrap();
    let mut visited = HashSet::new();
    let mut stack = vec![start];
    
    while let Some(curr) = stack.pop() {
        if visited.insert(curr) {
            if let Some(neighbors) = adj.get(&curr) {
                for &next in neighbors {
                    if !visited.contains(&next) {
                        stack.push(next);
                    }
                }
            }
        }
    }
    
    // Check if all vertices with edges are visited
    adj.keys().all(|v| visited.contains(v))
}
```

### Pitfall 2: Double-Counting Undirected Edges

In adjacency list for undirected graphs, edge (u,v) appears in both adj[u] and adj[v]. Use normalization or careful tracking.

### Pitfall 3: Off-by-One in Path vs Circuit

Circuit: path.first() == path.last()
Path: path.len() == num_edges + 1

## VII. Complexity Analysis Deep Dive

**Why Hierholzer's is O(E)?**

Each edge is:
- Added to adjacency list once: O(E)
- Traversed once: O(E)
- Checked/marked once: O(E)

Total: O(E) with proper data structures.

**Space Optimization:**
- Marking edges: O(E) with HashSet
- Stack depth: O(V) worst case (long path before backtrack)
- Total: O(V + E)

**Can we do better than O(E)?**
No — you must examine every edge at least once to construct the circuit. This is optimal.

## VIII. Practice Progression (Elite Training Path)

**Phase 1: Recognition (Week 1)**
- LeetCode 332 (Reconstruct Itinerary)
- Validate if circuit/path exists

**Phase 2: Construction (Week 2)**
- Implement Hierholzer's from scratch (no peeking)
- Time yourself: aim for <20 minutes

**Phase 3: Variations (Week 3-4)**
- De Bruijn graph problems
- Chinese Postman Problem
- Directed vs undirected mastery

**Phase 4: Integration (Week 5+)**
- Combine with flow algorithms
- Graph modification problems
- Competitive programming contests (Codeforces Div 2 problems)

## IX. Cognitive Mastery Checklist

You've mastered Eulerian patterns when you can:

✓ Recognize in <30 seconds if a graph has circuit/path/neither
✓ Implement Hierholzer's in your preferred language in <15 minutes
✓ Transform string/sequence problems into Eulerian graph problems
✓ Explain the intuition to a novice in <2 minutes
✓ Debug edge-case failures (connectivity, parallel edges) instantly
✓ State time/space complexity with proof, not memorization

---

**Final Principle:** Eulerian circuits are about *completeness* and *balance*. Master the art of tracking state exhaustively while maintaining structural invariants. This pattern thinking transfers to dynamic programming, backtracking, and many advanced algorithms.

**Your Training Directive:** Implement Hierholzer's in all three languages (Rust, Go, C) from memory today. Benchmark them. Feel the muscle memory build. Then solve 5 LeetCode problems without hints. Repeat until automatic.

**世界の頂点へ向かって進め。** (Advance toward the world's summit.)