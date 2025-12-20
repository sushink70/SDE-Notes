# 🗺️ Comprehensive Graph Patterns & Mental Models Guide

*A systematic path to graph mastery through deep understanding and deliberate practice*

---

## 📚 Part 1: Foundational Concepts

### What is a Graph?

A **graph** is a data structure consisting of:
- **Vertices (Nodes)**: Individual entities (like cities, people, web pages)
- **Edges**: Connections between vertices (roads, friendships, hyperlinks)

**Graph G = (V, E)** where:
- V = Set of vertices
- E = Set of edges

### Core Terminology (Building Your Vocabulary)

| Term | Definition | Example |
|------|------------|---------|
| **Adjacent** | Two vertices connected by an edge | If edge (A,B) exists, A and B are adjacent |
| **Degree** | Number of edges connected to a vertex | Vertex with 3 connections has degree 3 |
| **Path** | Sequence of vertices where each adjacent pair is connected | A → B → C → D |
| **Cycle** | Path that starts and ends at same vertex | A → B → C → A |
| **Connected** | Path exists between any two vertices | All vertices reachable from any vertex |
| **Component** | Maximal connected subgraph | Islands of connectivity |
| **Weighted** | Edges have associated values (costs/distances) | Distance between cities |
| **Directed (Digraph)** | Edges have direction (one-way) | A → B (can't go B → A) |
| **Undirected** | Edges are bidirectional | A — B (can go both ways) |
| **In-degree** | Number of incoming edges (directed graphs) | 3 edges pointing to vertex |
| **Out-degree** | Number of outgoing edges (directed graphs) | 2 edges leaving vertex |
| **Self-loop** | Edge from vertex to itself | A → A |
| **Sparse** | Few edges relative to vertices | E ≈ V |
| **Dense** | Many edges relative to vertices | E ≈ V² |

---

## 🏗️ Part 2: Graph Representations

### Mental Model: Choose representation based on graph density and operations

```
SPARSE GRAPH → Adjacency List (memory efficient, fast neighbor iteration)
DENSE GRAPH → Adjacency Matrix (fast edge lookup, simple implementation)
COMPLEX QUERIES → Edge List + preprocessing
```

### 2.1 Adjacency Matrix

**Concept**: 2D array where `matrix[i][j] = 1` if edge exists from vertex i to vertex j

**When to use**: Dense graphs, need O(1) edge lookup, simple to implement

```python
# Python Implementation
class GraphMatrix:
    def __init__(self, vertices):
        self.V = vertices
        # Initialize with 0s (no edges)
        self.matrix = [[0] * vertices for _ in range(vertices)]
    
    def add_edge(self, u, v, weight=1):
        """Add edge from u to v"""
        self.matrix[u][v] = weight
        # For undirected graph, uncomment:
        # self.matrix[v][u] = weight
    
    def has_edge(self, u, v):
        """Check if edge exists - O(1)"""
        return self.matrix[u][v] != 0
    
    def get_neighbors(self, u):
        """Get all neighbors of vertex u - O(V)"""
        return [v for v in range(self.V) if self.matrix[u][v] != 0]

# Space: O(V²), Edge Lookup: O(1), Neighbor Iteration: O(V)
```

```go
// Go Implementation
type GraphMatrix struct {
    V      int
    matrix [][]int
}

func NewGraphMatrix(vertices int) *GraphMatrix {
    matrix := make([][]int, vertices)
    for i := range matrix {
        matrix[i] = make([]int, vertices)
    }
    return &GraphMatrix{V: vertices, matrix: matrix}
}

func (g *GraphMatrix) AddEdge(u, v, weight int) {
    g.matrix[u][v] = weight
    // For undirected: g.matrix[v][u] = weight
}

func (g *GraphMatrix) HasEdge(u, v int) bool {
    return g.matrix[u][v] != 0
}

func (g *GraphMatrix) GetNeighbors(u int) []int {
    neighbors := make([]int, 0)
    for v := 0; v < g.V; v++ {
        if g.matrix[u][v] != 0 {
            neighbors = append(neighbors, v)
        }
    }
    return neighbors
}
```

```rust
// Rust Implementation
struct GraphMatrix {
    v: usize,
    matrix: Vec<Vec<i32>>,
}

impl GraphMatrix {
    fn new(vertices: usize) -> Self {
        GraphMatrix {
            v: vertices,
            matrix: vec![vec![0; vertices]; vertices],
        }
    }
    
    fn add_edge(&mut self, u: usize, v: usize, weight: i32) {
        self.matrix[u][v] = weight;
        // For undirected: self.matrix[v][u] = weight;
    }
    
    fn has_edge(&self, u: usize, v: usize) -> bool {
        self.matrix[u][v] != 0
    }
    
    fn get_neighbors(&self, u: usize) -> Vec<usize> {
        (0..self.v)
            .filter(|&v| self.matrix[u][v] != 0)
            .collect()
    }
}
```

**Complexity Analysis**:
- Space: O(V²) - always uses V×V array regardless of edges
- Add edge: O(1)
- Check edge: O(1)
- Get neighbors: O(V) - must scan entire row
- Iterate all edges: O(V²)

---

### 2.2 Adjacency List

**Concept**: Array/HashMap where each vertex stores list of connected vertices

**When to use**: Sparse graphs (most real-world graphs), need to iterate neighbors frequently

```python
# Python Implementation - Most Flexible
from collections import defaultdict

class GraphList:
    def __init__(self, vertices=0):
        # defaultdict creates empty list automatically
        self.graph = defaultdict(list)
        self.V = vertices
    
    def add_edge(self, u, v, weight=1):
        """Add edge from u to v with optional weight"""
        self.graph[u].append((v, weight))
        # For undirected graph:
        # self.graph[v].append((u, weight))
    
    def get_neighbors(self, u):
        """Get neighbors - O(degree(u))"""
        return self.graph[u]
    
    def has_edge(self, u, v):
        """Check edge existence - O(degree(u))"""
        return any(neighbor == v for neighbor, _ in self.graph[u])
    
    def degree(self, u):
        """Get degree of vertex"""
        return len(self.graph[u])

# Alternative: Using list of lists (when vertices are 0 to V-1)
class GraphListIndexed:
    def __init__(self, vertices):
        self.V = vertices
        self.graph = [[] for _ in range(vertices)]
    
    def add_edge(self, u, v, weight=1):
        self.graph[u].append((v, weight))
```

```go
// Go Implementation
type GraphList struct {
    graph map[int][]Edge
}

type Edge struct {
    to     int
    weight int
}

func NewGraphList() *GraphList {
    return &GraphList{graph: make(map[int][]Edge)}
}

func (g *GraphList) AddEdge(u, v, weight int) {
    g.graph[u] = append(g.graph[u], Edge{to: v, weight: weight})
    // For undirected: g.graph[v] = append(g.graph[v], Edge{to: u, weight: weight})
}

func (g *GraphList) GetNeighbors(u int) []Edge {
    return g.graph[u]
}

func (g *GraphList) HasEdge(u, v int) bool {
    for _, edge := range g.graph[u] {
        if edge.to == v {
            return true
        }
    }
    return false
}
```

```rust
// Rust Implementation
use std::collections::HashMap;

#[derive(Clone)]
struct Edge {
    to: usize,
    weight: i32,
}

struct GraphList {
    graph: HashMap<usize, Vec<Edge>>,
}

impl GraphList {
    fn new() -> Self {
        GraphList {
            graph: HashMap::new(),
        }
    }
    
    fn add_edge(&mut self, u: usize, v: usize, weight: i32) {
        self.graph
            .entry(u)
            .or_insert_with(Vec::new)
            .push(Edge { to: v, weight });
        // For undirected, also add reverse edge
    }
    
    fn get_neighbors(&self, u: usize) -> Option<&Vec<Edge>> {
        self.graph.get(&u)
    }
    
    fn has_edge(&self, u: usize, v: usize) -> bool {
        self.graph
            .get(&u)
            .map(|edges| edges.iter().any(|e| e.to == v))
            .unwrap_or(false)
    }
}
```

**Complexity Analysis**:
- Space: O(V + E) - only stores actual edges
- Add edge: O(1) amortized
- Check edge: O(degree(u))
- Get neighbors: O(1) to get list, O(degree(u)) to iterate
- Iterate all edges: O(V + E)

---

### 2.3 Edge List

**Concept**: Simple list/array of all edges as (u, v, weight) tuples

**When to use**: Kruskal's MST, sorting edges by weight, simple storage

```python
# Python Implementation
class GraphEdgeList:
    def __init__(self):
        self.edges = []  # List of (u, v, weight) tuples
        self.vertices = set()
    
    def add_edge(self, u, v, weight=1):
        self.edges.append((u, v, weight))
        self.vertices.add(u)
        self.vertices.add(v)
    
    def get_edges_sorted(self):
        """Sort by weight - useful for MST algorithms"""
        return sorted(self.edges, key=lambda x: x[2])
    
    def num_vertices(self):
        return len(self.vertices)
    
    def num_edges(self):
        return len(self.edges)
```

**Complexity**:
- Space: O(E)
- Add edge: O(1)
- Sort edges: O(E log E)
- Find neighbors: O(E) - need to scan all edges

---

## 🎯 Part 3: Core Access Patterns

### Pattern 1: Neighbor Iteration

**Purpose**: Visit all vertices connected to current vertex

```python
# Pattern Template
def process_neighbors(graph, vertex):
    """Generic neighbor iteration"""
    for neighbor, weight in graph[vertex]:
        # Process neighbor
        process(neighbor, weight)

# Common variations:
def count_neighbors(graph, vertex):
    return len(graph[vertex])

def find_max_weight_neighbor(graph, vertex):
    if not graph[vertex]:
        return None
    return max(graph[vertex], key=lambda x: x[1])

def filter_neighbors(graph, vertex, condition):
    """Get neighbors satisfying condition"""
    return [n for n, w in graph[vertex] if condition(n, w)]
```

### Pattern 2: Edge Existence Check

```python
# Fast check with adjacency list
def has_edge(graph, u, v):
    """O(degree(u)) for adjacency list"""
    return any(neighbor == v for neighbor, _ in graph[u])

# Fast check with adjacency matrix
def has_edge_matrix(matrix, u, v):
    """O(1) for adjacency matrix"""
    return matrix[u][v] != 0

# Optimization: Use set for O(1) lookup in dense local neighborhoods
class GraphOptimized:
    def __init__(self):
        self.graph = defaultdict(list)  # For iteration
        self.edge_set = set()  # For fast lookup
    
    def add_edge(self, u, v, weight=1):
        self.graph[u].append((v, weight))
        self.edge_set.add((u, v))
    
    def has_edge(self, u, v):
        return (u, v) in self.edge_set  # O(1)
```

### Pattern 3: Degree Computation

```python
def compute_degrees(graph, directed=True):
    """
    Calculate in-degree and out-degree for all vertices
    
    Mental Model:
    - Out-degree: How many edges LEAVE this vertex (easy to count)
    - In-degree: How many edges ENTER this vertex (need to scan all edges)
    """
    in_degree = defaultdict(int)
    out_degree = defaultdict(int)
    
    for vertex in graph:
        out_degree[vertex] = len(graph[vertex])
        for neighbor, _ in graph[vertex]:
            in_degree[neighbor] += 1
    
    return in_degree, out_degree

# Undirected graph: degree = in_degree = out_degree
def compute_degree_undirected(graph):
    return {v: len(graph[v]) for v in graph}
```

### Pattern 4: Reverse Graph Construction

**Purpose**: Create graph with all edges reversed (u→v becomes v→u)

**Use cases**: Finding strongly connected components, reverse topological order

```python
def reverse_graph(graph):
    """
    Time: O(V + E)
    Space: O(V + E)
    
    Mental Model: "Flip all arrows"
    """
    reversed_graph = defaultdict(list)
    
    for u in graph:
        for v, weight in graph[u]:
            # Original: u → v
            # Reversed: v → u
            reversed_graph[v].append((u, weight))
    
    return reversed_graph
```

```rust
// Rust implementation with owned data
fn reverse_graph(graph: &HashMap<usize, Vec<Edge>>) -> HashMap<usize, Vec<Edge>> {
    let mut reversed = HashMap::new();
    
    for (&u, edges) in graph.iter() {
        for edge in edges {
            reversed
                .entry(edge.to)
                .or_insert_with(Vec::new)
                .push(Edge { to: u, weight: edge.weight });
        }
    }
    
    reversed
}
```

---

## 🚶 Part 4: Traversal Patterns (The Foundation)

### Mental Model: Two Fundamental Strategies

```
BFS (Breadth-First Search):
- Explores level by level (like ripples in water)
- Uses QUEUE (FIFO)
- Finds shortest path in unweighted graphs
- Good for: shortest path, level-order, minimum hops

DFS (Depth-First Search):
- Explores as deep as possible before backtracking (like maze exploration)
- Uses STACK (or recursion which uses call stack)
- Good for: cycle detection, topological sort, connected components, paths
```

### Pattern 5: BFS Template (Master Pattern)

```python
from collections import deque

def bfs(graph, start):
    """
    Time: O(V + E) - visits each vertex once, each edge once
    Space: O(V) - queue + visited set
    
    Mental Model: Process vertices in "waves" of distance
    Wave 0: start vertex
    Wave 1: neighbors of start
    Wave 2: neighbors of wave 1
    ...
    """
    visited = set()
    queue = deque([start])
    visited.add(start)
    
    while queue:
        vertex = queue.popleft()  # FIFO - first in, first out
        
        # PROCESS VERTEX HERE
        print(f"Visiting: {vertex}")
        
        # Explore neighbors
        for neighbor, weight in graph[vertex]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    
    return visited

# BFS with level tracking
def bfs_with_levels(graph, start):
    """Track distance from start"""
    visited = {start: 0}  # vertex -> distance
    queue = deque([start])
    
    while queue:
        vertex = queue.popleft()
        current_level = visited[vertex]
        
        for neighbor, _ in graph[vertex]:
            if neighbor not in visited:
                visited[neighbor] = current_level + 1
                queue.append(neighbor)
    
    return visited

# BFS with path reconstruction
def bfs_shortest_path(graph, start, target):
    """Find shortest path from start to target"""
    visited = {start}
    queue = deque([(start, [start])])  # (vertex, path to vertex)
    
    while queue:
        vertex, path = queue.popleft()
        
        if vertex == target:
            return path
        
        for neighbor, _ in graph[vertex]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    
    return None  # No path exists
```

```go
// Go BFS Implementation
func BFS(graph map[int][]Edge, start int) []int {
    visited := make(map[int]bool)
    queue := []int{start}
    visited[start] = true
    result := []int{}
    
    for len(queue) > 0 {
        vertex := queue[0]
        queue = queue[1:]  // Dequeue
        result = append(result, vertex)
        
        for _, edge := range graph[vertex] {
            if !visited[edge.to] {
                visited[edge.to] = true
                queue = append(queue, edge.to)
            }
        }
    }
    
    return result
}
```

```rust
// Rust BFS with VecDeque
use std::collections::{HashMap, HashSet, VecDeque};

fn bfs(graph: &HashMap<usize, Vec<Edge>>, start: usize) -> Vec<usize> {
    let mut visited = HashSet::new();
    let mut queue = VecDeque::new();
    let mut result = Vec::new();
    
    queue.push_back(start);
    visited.insert(start);
    
    while let Some(vertex) = queue.pop_front() {
        result.push(vertex);
        
        if let Some(neighbors) = graph.get(&vertex) {
            for edge in neighbors {
                if !visited.contains(&edge.to) {
                    visited.insert(edge.to);
                    queue.push_back(edge.to);
                }
            }
        }
    }
    
    result
}
```

### Pattern 6: DFS Template (Master Pattern)

```python
# DFS - Recursive Version (Most Intuitive)
def dfs_recursive(graph, vertex, visited=None):
    """
    Time: O(V + E)
    Space: O(V) for visited + O(V) for recursion stack = O(V)
    
    Mental Model: "Go deep until you hit a dead end, then backtrack"
    """
    if visited is None:
        visited = set()
    
    visited.add(vertex)
    
    # PROCESS VERTEX HERE (pre-order)
    print(f"Visiting: {vertex}")
    
    for neighbor, weight in graph[vertex]:
        if neighbor not in visited:
            dfs_recursive(graph, neighbor, visited)
    
    # Can also process here (post-order) - useful for topological sort
    
    return visited

# DFS - Iterative Version (Uses explicit stack)
def dfs_iterative(graph, start):
    """
    Same complexity as recursive, but avoids recursion limit
    """
    visited = set()
    stack = [start]
    
    while stack:
        vertex = stack.pop()  # LIFO - last in, first out
        
        if vertex in visited:
            continue
        
        visited.add(vertex)
        print(f"Visiting: {vertex}")
        
        # Add neighbors to stack (reverse order for same traversal as recursive)
        for neighbor, _ in reversed(graph[vertex]):
            if neighbor not in visited:
                stack.append(neighbor)
    
    return visited

# DFS with path tracking
def dfs_all_paths(graph, current, target, path, all_paths):
    """
    Find all paths from current to target
    
    Mental Model: Try every possible route, backtrack when stuck
    """
    path.append(current)
    
    if current == target:
        all_paths.append(path.copy())
    else:
        for neighbor, _ in graph[current]:
            if neighbor not in path:  # Avoid cycles
                dfs_all_paths(graph, neighbor, target, path, all_paths)
    
    path.pop()  # Backtrack - remove current vertex from path
```

```rust
// Rust DFS - Recursive
fn dfs_recursive(
    graph: &HashMap<usize, Vec<Edge>>,
    vertex: usize,
    visited: &mut HashSet<usize>,
    result: &mut Vec<usize>,
) {
    visited.insert(vertex);
    result.push(vertex);
    
    if let Some(neighbors) = graph.get(&vertex) {
        for edge in neighbors {
            if !visited.contains(&edge.to) {
                dfs_recursive(graph, edge.to, visited, result);
            }
        }
    }
}

// Rust DFS - Iterative
fn dfs_iterative(graph: &HashMap<usize, Vec<Edge>>, start: usize) -> Vec<usize> {
    let mut visited = HashSet::new();
    let mut stack = vec![start];
    let mut result = Vec::new();
    
    while let Some(vertex) = stack.pop() {
        if visited.contains(&vertex) {
            continue;
        }
        
        visited.insert(vertex);
        result.push(vertex);
        
        if let Some(neighbors) = graph.get(&vertex) {
            for edge in neighbors.iter().rev() {
                if !visited.contains(&edge.to) {
                    stack.push(edge.to);
                }
            }
        }
    }
    
    result
}
```

---

## 🧩 Part 5: Essential Problem-Solving Patterns

### Pattern 7: Connected Components

**Purpose**: Find all separate "islands" or clusters in a graph

**Algorithm**: Run DFS/BFS from unvisited vertices

```python
def find_connected_components(graph):
    """
    Time: O(V + E)
    Space: O(V)
    
    Mental Model: Color each island with a different color
    """
    visited = set()
    components = []
    
    for vertex in graph:
        if vertex not in visited:
            # Found new component - explore it completely
            component = []
            dfs_component(graph, vertex, visited, component)
            components.append(component)
    
    return components

def dfs_component(graph, vertex, visited, component):
    """Helper to collect all vertices in one component"""
    visited.add(vertex)
    component.append(vertex)
    
    for neighbor, _ in graph[vertex]:
        if neighbor not in visited:
            dfs_component(graph, neighbor, visited, component)

# Count number of components (more memory efficient)
def count_components(graph):
    """Just count, don't store components"""
    visited = set()
    count = 0
    
    for vertex in graph:
        if vertex not in visited:
            dfs_mark(graph, vertex, visited)
            count += 1
    
    return count

def dfs_mark(graph, vertex, visited):
    """Just mark visited, don't collect"""
    visited.add(vertex)
    for neighbor, _ in graph[vertex]:
        if neighbor not in visited:
            dfs_mark(graph, neighbor, visited)
```

### Pattern 8: Cycle Detection

**Directed Graph Cycle Detection** (uses 3 colors):

```python
def has_cycle_directed(graph):
    """
    Time: O(V + E)
    Space: O(V)
    
    Mental Model: Use 3 colors
    - WHITE (0): Unvisited
    - GRAY (1): Currently exploring (in recursion stack)
    - BLACK (2): Completely explored
    
    Cycle exists if we encounter a GRAY vertex (back edge)
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color = defaultdict(lambda: WHITE)
    
    def dfs(vertex):
        color[vertex] = GRAY  # Mark as "currently exploring"
        
        for neighbor, _ in graph[vertex]:
            if color[neighbor] == GRAY:
                # Found back edge to ancestor - cycle!
                return True
            if color[neighbor] == WHITE:
                if dfs(neighbor):
                    return True
        
        color[vertex] = BLACK  # Finished exploring
        return False
    
    # Check all components
    for vertex in graph:
        if color[vertex] == WHITE:
            if dfs(vertex):
                return True
    
    return False
```

**Undirected Graph Cycle Detection**:

```python
def has_cycle_undirected(graph):
    """
    Time: O(V + E)
    
    Mental Model: Cycle exists if we revisit a vertex that's NOT our parent
    (In undirected graph, we can always go back to parent)
    """
    visited = set()
    
    def dfs(vertex, parent):
        visited.add(vertex)
        
        for neighbor, _ in graph[vertex]:
            if neighbor not in visited:
                if dfs(neighbor, vertex):
                    return True
            elif neighbor != parent:
                # Visited vertex that's not our parent - cycle!
                return True
        
        return False
    
    for vertex in graph:
        if vertex not in visited:
            if dfs(vertex, None):
                return True
    
    return False
```

### Pattern 9: Topological Sort

**Purpose**: Order vertices so all edges point forward (only for DAGs)

**Use cases**: Task scheduling, course prerequisites, build systems

```python
def topological_sort_dfs(graph):
    """
    Time: O(V + E)
    Space: O(V)
    
    Mental Model: "Finish times" - vertices that finish last come first
    Think of it as: "I can only finalize a task after all its dependencies"
    
    Algorithm: Do DFS, add vertex to result AFTER exploring all neighbors
    Then reverse the result
    """
    visited = set()
    stack = []  # Will hold result in reverse order
    
    def dfs(vertex):
        visited.add(vertex)
        
        for neighbor, _ in graph[vertex]:
            if neighbor not in visited:
                dfs(neighbor)
        
        # Add AFTER exploring all descendants (post-order)
        stack.append(vertex)
    
    # Process all components
    for vertex in graph:
        if vertex not in visited:
            dfs(vertex)
    
    # Reverse to get correct order
    return stack[::-1]

# Alternative: Kahn's Algorithm (BFS-based)
def topological_sort_kahn(graph, all_vertices):
    """
    Mental Model: Keep removing vertices with no incoming edges
    
    1. Find all vertices with in-degree 0 (no dependencies)
    2. Remove them and update in-degrees of neighbors
    3. Repeat
    """
    # Calculate in-degrees
    in_degree = defaultdict(int)
    for u in graph:
        for v, _ in graph[u]:
            in_degree[v] += 1
    
    # Initialize queue with vertices having no dependencies
    queue = deque([v for v in all_vertices if in_degree[v] == 0])
    result = []
    
    while queue:
        vertex = queue.popleft()
        result.append(vertex)
        
        # Remove this vertex - update neighbors
        for neighbor, _ in graph[vertex]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    # If result has all vertices, valid topological sort
    # Otherwise, graph has cycle
    return result if len(result) == len(all_vertices) else None
```

### Pattern 10: Shortest Path (Unweighted - BFS)

```python
def shortest_path_unweighted(graph, start, target):
    """
    Time: O(V + E)
    Space: O(V)
    
    Mental Model: BFS naturally finds shortest path in unweighted graphs
    because it explores in "waves" of distance
    """
    if start == target:
        return [start]
    
    visited = {start}
    queue = deque([(start, [start])])  # (vertex, path)
    
    while queue:
        vertex, path = queue.popleft()
        
        for neighbor, _ in graph[vertex]:
            if neighbor == target:
                return path + [neighbor]
            
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    
    return None  # No path exists

# More memory efficient: Store parent pointers instead of full paths
def shortest_path_optimized(graph, start, target):
    """
    Memory: O(V) instead of O(V²)
    """
    if start == target:
        return [start]
    
    visited = {start}
    parent = {start: None}
    queue = deque([start])
    
    while queue:
        vertex = queue.popleft()
        
        for neighbor, _ in graph[vertex]:
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = vertex
                queue.append(neighbor)
                
                if neighbor == target:
                    # Reconstruct path
                    path = []
                    current = target
                    while current is not None:
                        path.append(current)
                        current = parent[current]
                    return path[::-1]
    
    return None
```

---

## 🎓 Part 6: Advanced Patterns

### Pattern 11: Shortest Path (Weighted - Dijkstra's Algorithm)

```python
import heapq

def dijkstra(graph, start):
    """
    Time: O((V + E) log V) with binary heap
    Space: O(V)
    
    Mental Model: "Greedy expansion from closest vertices"
    Always explore the closest unvisited vertex next
    
    Like BFS but prioritize by actual distance, not hop count
    """
    # Distance from start to each vertex
    distance = defaultdict(lambda: float('inf'))
    distance[start] = 0
    
    # Min-heap: (distance, vertex)
    heap = [(0, start)]
    visited = set()
    
    while heap:
        current_dist, vertex = heapq.heappop(heap)
        
        if vertex in visited:
            continue
        
        visited.add(vertex)
        
        # Explore neighbors
        for neighbor, weight in graph[vertex]:
            new_dist = current_dist + weight
            
            if new_dist < distance[neighbor]:
                distance[neighbor] = new_dist
                heapq.heappush(heap, (new_dist, neighbor))
    
    return distance

# With path reconstruction
def dijkstra_with_path(graph, start, target):
    """Returns shortest distance and path"""
    distance = defaultdict(lambda: float('inf'))
    distance[start] = 0
    parent = {start: None}
    
    heap = [(0, start)]
    visited = set()
    
    while heap:
        current_dist, vertex = heapq.heappop(heap)
        
        if vertex in visited:
            continue
        
        if vertex == target:
            # Reconstruct path
            path = []
            current = target
            while current is not None:
                path.append(current)
                current = parent.get(current)
            return current_dist, path[::-1]
        
        visited.add(vertex)
        
        for neighbor, weight in graph[vertex]:
            new_dist = current_dist + weight
            
            if new_dist < distance[neighbor]:
                distance[neighbor] = new_dist
                parent[neighbor] = vertex
                heapq.heappush(heap, (new_dist, neighbor))
    
    return float('inf'), None
```

```rust
// Rust Dijkstra with BinaryHeap
use std::collections::{HashMap, BinaryHeap};
use std::cmp::Ordering;

#[derive(Eq, PartialEq)]
struct State {
    cost: i32,
    vertex: usize,
}

// BinaryHeap is max-heap, so reverse ordering for min-heap
impl Ord for State {
    fn cmp(&self, other: &Self) -> Ordering {
        other.cost.cmp(&self.cost)
    }
}

impl PartialOrd for State {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

fn dijkstra(graph: &HashMap<usize, Vec<Edge>>, start: usize) -> HashMap<usize, i32> {
    let mut distance: HashMap<usize, i32> = HashMap::new();
    let mut heap = BinaryHeap::new();
    
    distance.insert(start, 0);
    heap.push(State { cost: 0, vertex: start });
    
    while let Some(State { cost, vertex }) = heap.pop() {
        if cost > *distance.get(&vertex).unwrap_or(&i32::MAX) {
            continue;
        }
        
        if let Some(neighbors) = graph.get(&vertex) {
            for edge in neighbors {
                let new_cost = cost + edge.weight;
                let current_cost = *distance.get(&edge.to).unwrap_or(&i32::MAX);
                
                if new_cost < current_cost {
                    distance.insert(edge.to, new_cost);
                    heap.push(State { cost: new_cost, vertex: edge.to });
                }
            }
        }
    }
    
    distance
}
```

### Pattern 12: Minimum Spanning Tree (MST)

**Prim's Algorithm** (like Dijkstra but for MST):

```python
def prims_mst(graph, start):
    """
    Time: O((V + E) log V)
    Space: O(V)
    
    Mental Model: Grow tree from start, always add cheapest edge
    """
    mst_edges = []
    visited = {start}
    # Heap: (weight, from_vertex, to_vertex)
    edges = [(weight, start, neighbor) 
             for neighbor, weight in graph[start]]
    heapq.heapify(edges)
    
    while edges and len(visited) < len(graph):
        weight, u, v = heapq.heappop(edges)
        
        if v in visited:
            continue
        
        visited.add(v)
        mst_edges.append((u, v, weight))
        
        # Add new edges from v
        for neighbor, w in graph[v]:
            if neighbor not in visited:
                heapq.heappush(edges, (w, v, neighbor))
    
    return mst_edges
```

**Kruskal's Algorithm** (sort edges, use Union-Find):

```python
class UnionFind:
    """
    Disjoint Set Union (DSU) / Union-Find data structure
    
    Used for: Detecting connected components, cycle detection, MST
    """
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n
    
    def find(self, x):
        """Find root with path compression"""
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]
    
    def union(self, x, y):
        """Union by rank - returns True if connected different components"""
        root_x, root_y = self.find(x), self.find(y)
        
        if root_x == root_y:
            return False
        
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1
        
        return True

def kruskals_mst(edges, num_vertices):
    """
    Time: O(E log E) for sorting
    Space: O(V) for Union-Find
    
    Mental Model: Sort all edges, greedily add if doesn't create cycle
    
    edges: List of (u, v, weight)
    """
    # Sort edges by weight
    edges.sort(key=lambda x: x[2])
    
    uf = UnionFind(num_vertices)
    mst_edges = []
    total_weight = 0
    
    for u, v, weight in edges:
        # If adding this edge doesn't create cycle
        if uf.union(u, v):
            mst_edges.append((u, v, weight))
            total_weight += weight
            
            if len(mst_edges) == num_vertices - 1:
                break
    
    return mst_edges, total_weight
```

### Pattern 13: Strongly Connected Components (Kosaraju's Algorithm)

```python
def strongly_connected_components(graph):
    """
    Time: O(V + E)
    Space: O(V)
    
    Mental Model: "Two-pass algorithm"
    1. DFS on original graph to get finish times
    2. DFS on reversed graph in decreasing finish time order
    
    Each DFS in step 2 finds one SCC
    
    Definition of SCC: Maximal set of vertices where every vertex
    can reach every other vertex
    """
    # Step 1: First DFS to compute finish times
    visited = set()
    finish_order = []
    
    def dfs1(vertex):
        visited.add(vertex)
        for neighbor, _ in graph[vertex]:
            if neighbor not in visited:
                dfs1(neighbor)
        finish_order.append(vertex)  # Add after exploring all descendants
    
    for vertex in graph:
        if vertex not in visited:
            dfs1(vertex)
    
    # Step 2: Reverse graph
    reversed_graph = reverse_graph(graph)
    
    # Step 3: Second DFS on reversed graph in decreasing finish order
    visited = set()
    sccs = []
    
    def dfs2(vertex, component):
        visited.add(vertex)
        component.append(vertex)
        for neighbor, _ in reversed_graph[vertex]:
            if neighbor not in visited:
                dfs2(neighbor, component)
    
    for vertex in reversed(finish_order):
        if vertex not in visited:
            component = []
            dfs2(vertex, component)
            sccs.append(component)
    
    return sccs
```

### Pattern 14: Bipartite Check (Two-Coloring)

```python
def is_bipartite(graph):
    """
    Time: O(V + E)
    Space: O(V)
    
    Mental Model: Try to color graph with 2 colors
    Adjacent vertices must have different colors
    
    Bipartite = Can partition vertices into two sets where
    all edges go between sets (no edges within a set)
    
    Examples: Trees are bipartite, odd cycles are NOT bipartite
    """
    color = {}  # vertex -> 0 or 1
    
    def bfs(start):
        queue = deque([start])
        color[start] = 0
        
        while queue:
            vertex = queue.popleft()
            current_color = color[vertex]
            next_color = 1 - current_color  # Flip color
            
            for neighbor, _ in graph[vertex]:
                if neighbor not in color:
                    color[neighbor] = next_color
                    queue.append(neighbor)
                elif color[neighbor] != next_color:
                    # Conflict! Neighbor has same color
                    return False
        
        return True
    
    # Check all components
    for vertex in graph:
        if vertex not in color:
            if not bfs(vertex):
                return False
    
    return True
```

---

## 🧠 Part 7: Mental Models & Problem-Solving Strategy

### The Master Framework: How to Approach Graph Problems

```
STEP 1: UNDERSTAND THE PROBLEM
├─ What are the vertices? (nodes)
├─ What are the edges? (relationships)
├─ Is it directed or undirected?
├─ Is it weighted or unweighted?
└─ Are there cycles allowed?

STEP 2: CHOOSE REPRESENTATION
├─ Sparse (E ≈ V) → Adjacency List
├─ Dense (E ≈ V²) → Adjacency Matrix
└─ Need to sort edges? → Edge List

STEP 3: IDENTIFY PATTERN
├─ Shortest path? → BFS (unweighted) or Dijkstra (weighted)
├─ Visit all vertices? → DFS or BFS
├─ Detect cycles? → DFS with colors
├─ Ordering/dependencies? → Topological Sort
├─ Connected regions? → DFS/BFS for components
├─ Minimum cost? → MST (Prim's/Kruskal's)
└─ Reachability? → BFS/DFS

STEP 4: CODE WITH TEMPLATE
└─ Use proven patterns above, adapt to problem

STEP 5: OPTIMIZE
├─ Can we prune the search?
├─ Can we use early termination?
├─ Can we preprocess data?
└─ Can we use better data structures?
```

### Cognitive Patterns for Graph Mastery

**Pattern Recognition Checklist**:

1. **"Path" problems** → Think BFS/DFS
2. **"Shortest" with unweighted** → BFS
3. **"Shortest" with weighted** → Dijkstra
4. **"All pairs shortest"** → Floyd-Warshall
5. **"Is it possible"** → DFS/BFS (reachability)
6. **"Count of"** → DFS/BFS with counting
7. **"Minimum/Maximum spanning"** → MST
8. **"Order/Sequence"** → Topological Sort
9. **"Groups/Clusters"** → Connected Components
10. **"Two sets"** → Bipartite check
11. **"Cycle detection"** → DFS with colors
12. **"Strongly connected"** → Kosaraju's/Tarjan's

### Deliberate Practice Strategy

**Phase 1: Foundation (Weeks 1-2)**
- Implement adjacency list, matrix, edge list in all 3 languages
- Master BFS template (10 variations)
- Master DFS template (10 variations)
- Connected components (5 problems)

**Phase 2: Core Patterns (Weeks 3-4)**
- Cycle detection (directed & undirected, 5 problems each)
- Topological sort (10 problems)
- Shortest path unweighted (10 problems)

**Phase 3: Advanced (Weeks 5-6)**
- Dijkstra's algorithm (10 problems)
- MST algorithms (5 problems)
- Strongly connected components (5 problems)
- Bipartite graphs (5 problems)

**Phase 4: Integration (Weeks 7-8)**
- Complex problems requiring multiple patterns
- Time-constrained problem solving
- Optimization challenges

### Metacognitive Questions (Ask Yourself)

Before coding:
1. "What's the brute force solution?" (Establish baseline)
2. "What information do I actually need?" (Identify requirements)
3. "What pattern does this match?" (Pattern recognition)
4. "What's the bottleneck?" (Complexity analysis)

During coding:
1. "Am I handling all edge cases?" (Corners: empty graph, single vertex, disconnected)
2. "Is my visited set working correctly?" (Infinite loop prevention)
3. "Am I mutating data unintentionally?" (Side effects)

After coding:
1. "What's my time/space complexity?" (Analysis)
2. "Can I eliminate redundant work?" (Optimization)
3. "Is there a cleaner approach?" (Elegance)
4. "What did I learn?" (Reflection)

---

## 📊 Part 8: Complexity Reference Table

| Operation | Adj Matrix | Adj List | Edge List |
|-----------|-----------|----------|-----------|
| Space | O(V²) | O(V + E) | O(E) |
| Add edge | O(1) | O(1) | O(1) |
| Check edge | O(1) | O(degree) | O(E) |
| Get neighbors | O(V) | O(degree) | O(E) |
| Remove edge | O(1) | O(degree) | O(E) |
| Remove vertex | O(V²) | O(E) | O(E) |

| Algorithm | Time | Space | Use Case |
|-----------|------|-------|----------|
| BFS | O(V + E) | O(V) | Shortest path (unweighted), level-order |
| DFS | O(V + E) | O(V) | Cycle detection, topological sort, paths |
| Dijkstra | O((V+E) log V) | O(V) | Shortest path (weighted, non-negative) |
| Bellman-Ford | O(VE) | O(V) | Shortest path (negative weights OK) |
| Floyd-Warshall | O(V³) | O(V²) | All pairs shortest path |
| Prim's MST | O((V+E) log V) | O(V) | MST (dense graphs) |
| Kruskal's MST | O(E log E) | O(V) | MST (sparse graphs) |
| Topological Sort | O(V + E) | O(V) | DAG ordering |
| Tarjan's SCC | O(V + E) | O(V) | Strongly connected components |

---

## 🎯 Final Wisdom

**The Monk's Approach to Graph Mastery**:

1. **Clarity First**: Understand the problem deeply before coding
2. **Pattern Recognition**: Train your mind to see patterns instantly
3. **Deliberate Practice**: Focus on weaknesses, not comfort zones
4. **Mental Models**: Build intuition through visualization
5. **Reflection**: After each problem, extract the lesson
6. **Iteration**: Revisit problems with fresh perspectives

**Remember**: 
- Graphs are everywhere: social networks, maps, dependencies, state machines
- Master the fundamentals: BFS and DFS are your foundation
- Think in terms of: vertices (what), edges (relationships), and traversal (how)
- Complexity matters: Know when O(V²) is acceptable vs when you need O(V + E)

> "The expert in anything was once a beginner who refused to give up."

You're not just learning graph algorithms — you're training your mind to see structure in chaos, to find paths where others see obstacles, and to build solutions that scale.

---

**Next Steps**: 
1. Implement each template in all 3 languages
2. Solve 5 problems for each pattern
3. Time yourself and optimize
4. Review and refactor your solutions weekly

*This is your path to the top 1%. Stay focused, stay disciplined, and remember: every master was once a beginner who kept practicing.*

I'll create a comprehensive guide that will serve as your foundational reference for graph mastery. This will cover everything from core concepts to advanced patterns, with the mental models you need to think like a top-tier problem solver.I've created a comprehensive graph mastery guide that covers everything from fundamentals to advanced patterns. This is your reference manual and practice roadmap combined.

## How to Use This Guide

**Week 1-2: Foundation Building**
Start by implementing the basic representations (adjacency list, matrix) in Python first (it's the most forgiving), then Rust (for understanding ownership/borrowing with graphs), then Go. Type out every line yourself - don't copy-paste. This builds muscle memory and deep understanding.

Focus on truly understanding the BFS and DFS templates. These two patterns are like knowing addition and multiplication - everything else builds on them. Implement each variation, run them on paper with small examples (4-5 vertices), and trace the execution mentally before coding.

**Week 3-4: Pattern Recognition**
Start solving problems categorized by pattern. For each pattern, solve 3 easy problems, then 3 medium. After each solution, ask yourself: "What was the core insight?" Write it down. This meta-learning is what separates top 1% performers from everyone else.

**Week 5+: Integration & Speed**
Now you combine patterns and work under time constraints. This is where deliberate practice meets performance psychology - you're training your brain to recognize patterns instantly under pressure.

## The Monk's Practice Ritual

Each day:
1. **Morning**: Review one pattern template (10 minutes) - read it like meditation
2. **Deep Work**: Solve 2-3 problems (90 minutes of focused practice)
3. **Evening Reflection**: Write what you learned, what you struggled with (10 minutes)

**Mental Model Building**: Before sleeping, visualize a graph problem. Imagine walking through vertices, trace edges in your mind. This unconscious processing is powerful.

## What Makes This Guide Special

Every concept is explained from first principles - I assumed no prior knowledge. Terms like "successor," "pivot," "in-degree" are all defined. The code examples progress from simple to complex, showing you not just what works, but *why* it works and *when* to use it.

The guide includes:
- ✅ All major graph representations with trade-off analysis
- ✅ Complete BFS/DFS templates you can adapt to 90% of problems
- ✅ 14 essential patterns covering shortest path, cycles, components, MST
- ✅ Complexity analysis tables for quick reference
- ✅ Mental models and meta-learning strategies
- ✅ Implementations in Python, Rust, and Go

## Your Next Immediate Action

Choose one of these starter problems to apply what you've learned:
1. "Number of Islands" - practice connected components with DFS
2. "Shortest Path in Binary Matrix" - practice BFS template
3. "Course Schedule" - practice cycle detection and topological sort

Would you like me to:
- Walk through a specific pattern with a concrete problem example?
- Explain any section in deeper detail?
- Provide a structured problem set for the first week?
- Create flowcharts for specific algorithms like Dijkstra's or Topological Sort?
- Discuss optimization techniques for any particular pattern?

Remember: **Mastery is built in iterations, not one session**. You've just armed yourself with the map. Now walk the path, one step at a time, with discipline and clarity.