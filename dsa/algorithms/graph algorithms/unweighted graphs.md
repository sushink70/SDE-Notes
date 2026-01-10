# **Unweighted Graphs: A Comprehensive Mastery Guide**

## **"A graph is not just nodes and edges—it's a universe of relationships waiting to be explored with precision and elegance."**

---

## **Table of Contents**

1. Foundation: What Are Graphs?
2. Graph Terminology & Taxonomy
3. Graph Representations
4. Core Traversal Algorithms
5. Shortest Path in Unweighted Graphs
6. Cycle Detection
7. Connected Components
8. Topological Sorting
9. Bipartite Graphs
10. Advanced Patterns & Problem-Solving
11. Implementation in Rust, Python, and Go
12. Mental Models & Mastery Strategies

---

## **1. Foundation: What Are Graphs?**

### **Conceptual Understanding**

A **graph** is a mathematical structure that models pairwise relationships between objects. It consists of:

- **Vertices (V)**: The fundamental units (also called nodes)
- **Edges (E)**: Connections between vertices

**Formal Definition:**

```
G = (V, E)
where V is a set of vertices
and E ⊆ V × V is a set of edges
```

### **Real-World Metaphor**

Think of a graph as a **social network**:

- People are **vertices**
- Friendships are **edges**
- Whether friendships are bidirectional (undirected) or one-way (directed) defines graph type

### **Why Unweighted?**

In an **unweighted graph**, all edges have equal cost/weight. This is the foundation—master this before weighted graphs.

---

## **2. Graph Terminology & Taxonomy**

### **Core Concepts**

**Vertex (Node):** A fundamental unit in the graph

```
Example: In a city map, each city is a vertex
```

**Edge:** A connection between two vertices

```
Example: A road between two cities
```

**Degree:** Number of edges connected to a vertex

- **In-degree**: Incoming edges (directed graphs)
- **Out-degree**: Outgoing edges (directed graphs)

```
If vertex A connects to B, C, D → degree of A = 3
```

**Path:** A sequence of vertices where each adjacent pair is connected by an edge

```
Path from A to D: A → B → C → D
```

**Cycle:** A path that starts and ends at the same vertex

```
Cycle: A → B → C → A
```

**Connected Graph:** Every vertex is reachable from every other vertex (undirected graphs)

**Strongly Connected:** Every vertex is reachable from every other vertex in BOTH directions (directed graphs)

**Weakly Connected:** Connected when treating directed graph as undirected

**Tree:** A connected acyclic graph (no cycles)

**DAG (Directed Acyclic Graph):** A directed graph with no cycles

---

### **Graph Types Taxonomy**

```
                    GRAPHS
                      |
        +-------------+-------------+
        |                           |
   UNDIRECTED                   DIRECTED
        |                           |
   +---------+               +------------+
   |         |               |            |
WEIGHTED  UNWEIGHTED     WEIGHTED    UNWEIGHTED
   |         |               |            |
   |    (Our Focus)          |       (Our Focus)
   |                         |
CYCLIC/ACYCLIC          DAG/CYCLIC
```

**ASCII Visualization:**

```
UNDIRECTED GRAPH        DIRECTED GRAPH
     (1)                     (1)
    / | \                   ↙ ↓ ↘
  (2)-(3)-(4)             (2)→(3)→(4)
    \ | /                   ↘ ↑ ↙
     (5)                     (5)
```

---

## **3. Graph Representations**

### **Mental Model: The Storage-Speed Tradeoff**

There are three primary ways to represent graphs. Each has tradeoffs:

1. **Edge List**: Simple but slow queries
2. **Adjacency Matrix**: Fast queries, memory-heavy
3. **Adjacency List**: Balanced—most commonly used

---

### **3.1 Edge List**

**Concept:** Store edges as pairs of vertices

```python
# Edge list representation
edges = [(0, 1), (0, 2), (1, 3), (2, 3)]
```

**Pros:**

- Simple
- Memory efficient for sparse graphs

**Cons:**

- Slow neighbor lookup: O(E)
- Difficult to perform graph algorithms

**When to use:** Rarely in competitive programming; useful for Kruskal's MST algorithm

---

### **3.2 Adjacency Matrix**

**Concept:** 2D array where `matrix[i][j] = 1` if edge exists from i to j

```
For graph: 0→1, 0→2, 1→3, 2→3

    0  1  2  3
0 [[0, 1, 1, 0],
1  [0, 0, 0, 1],
2  [0, 0, 0, 1],
3  [0, 0, 0, 0]]
```

**Time Complexity:**

- Check if edge exists: **O(1)**
- Find all neighbors: **O(V)**
- Space: **O(V²)**

**Pros:**

- Constant-time edge lookup
- Easy to implement

**Cons:**

- Wastes space for sparse graphs
- O(V²) space even with few edges

**When to use:**

- Dense graphs (E ≈ V²)
- Frequent edge existence queries
- Graph algorithms requiring matrix operations (Floyd-Warshall)

---

### **3.3 Adjacency List** ⭐ **Most Important**

**Concept:** Array of lists—each vertex has a list of neighbors

```
Graph: 0→1, 0→2, 1→3, 2→3

Adjacency List:
0: [1, 2]
1: [3]
2: [3]
3: []
```

**ASCII Visualization:**
```
Index    Neighbors
  0  →  [1, 2]
  1  →  [3]
  2  →  [3]
  3  →  []
```

**Time Complexity:**

- Check if edge exists: **O(degree(v))**
- Find all neighbors: **O(degree(v))**
- Space: **O(V + E)**

**Pros:**

- Space efficient: O(V + E)
- Fast neighbor iteration
- Standard in competitive programming

**Cons:**

- Slower edge existence check than matrix

**When to use:**

- Sparse graphs (most real-world graphs)
- BFS, DFS, and most graph algorithms
- Default choice for 95% of problems

---

### **Implementation Comparison**

```python
"""
Graph Representations in Python
Demonstrating all three representation methods
"""

class EdgeListGraph:
    """Edge List: Simple but limited"""
    def __init__(self, vertices):
        self.V = vertices
        self.edges = []
    
    def add_edge(self, u, v):
        self.edges.append((u, v))
    
    def has_edge(self, u, v):
        """O(E) time - inefficient"""
        return (u, v) in self.edges
    
    def get_neighbors(self, u):
        """O(E) time - inefficient"""
        return [v for (a, v) in self.edges if a == u]


class AdjacencyMatrix:
    """Adjacency Matrix: Fast queries, memory-heavy"""
    def __init__(self, vertices):
        self.V = vertices
        self.matrix = [[0] * vertices for _ in range(vertices)]
    
    def add_edge(self, u, v):
        """O(1) time"""
        self.matrix[u][v] = 1
    
    def has_edge(self, u, v):
        """O(1) time - very fast"""
        return self.matrix[u][v] == 1
    
    def get_neighbors(self, u):
        """O(V) time"""
        return [v for v in range(self.V) if self.matrix[u][v] == 1]


class AdjacencyList:
    """Adjacency List: MOST COMMONLY USED - Balanced performance"""
    def __init__(self, vertices):
        self.V = vertices
        self.adj = [[] for _ in range(vertices)]
    
    def add_edge(self, u, v):
        """O(1) time"""
        self.adj[u].append(v)
    
    def has_edge(self, u, v):
        """O(degree(u)) time"""
        return v in self.adj[u]
    
    def get_neighbors(self, u):
        """O(1) time to access, O(degree(u)) to iterate"""
        return self.adj[u]


# Demonstration
def demonstrate_representations():
    """Compare all three representations"""
    
    # Same graph using all three methods
    # Graph: 0→1, 0→2, 1→3, 2→3
    
    print("=== Edge List ===")
    edge_list = EdgeListGraph(4)
    edge_list.add_edge(0, 1)
    edge_list.add_edge(0, 2)
    edge_list.add_edge(1, 3)
    edge_list.add_edge(2, 3)
    print(f"Edges: {edge_list.edges}")
    print(f"Neighbors of 0: {edge_list.get_neighbors(0)}")
    
    print("\n=== Adjacency Matrix ===")
    matrix = AdjacencyMatrix(4)
    matrix.add_edge(0, 1)
    matrix.add_edge(0, 2)
    matrix.add_edge(1, 3)
    matrix.add_edge(2, 3)
    for i, row in enumerate(matrix.matrix):
        print(f"Row {i}: {row}")
    print(f"Has edge 0→1? {matrix.has_edge(0, 1)}")
    
    print("\n=== Adjacency List ===")
    adj_list = AdjacencyList(4)
    adj_list.add_edge(0, 1)
    adj_list.add_edge(0, 2)
    adj_list.add_edge(1, 3)
    adj_list.add_edge(2, 3)
    for i, neighbors in enumerate(adj_list.adj):
        print(f"Vertex {i}: {neighbors}")


if __name__ == "__main__":
    demonstrate_representations()
```
---

## **4. Core Traversal Algorithms**

### **Mental Model: Exploration Strategies**

Graph traversal is about **systematically visiting every vertex**. Two fundamental strategies:

1. **BFS (Breadth-First Search)**: Explore layer by layer—like ripples in water
2. **DFS (Depth-First Search)**: Explore deep paths first—like a maze explorer

**Cognitive Principle:** These are **search patterns**, not just algorithms. Master them as thinking tools.

---

### **4.1 Breadth-First Search (BFS)**

**Core Idea:** Explore all vertices at distance `k` before exploring vertices at distance `k+1`

**Data Structure:** **Queue** (FIFO - First In, First Out)

**ASCII Visualization:**
```
Starting from vertex 0:

Level 0:     (0)
            ↙   ↘
Level 1:  (1)   (2)
           ↓     ↓
Level 2:  (3)   (4)

Queue evolution:
[0]           → dequeue 0, add children 1,2
[1, 2]        → dequeue 1, add children 3
[2, 3]        → dequeue 2, add children 4
[3, 4]        → dequeue 3
[4]           → dequeue 4
[]            → done
```

**Algorithm Flow:**
```
┌─────────────────┐
│  Start at source│
└────────┬────────┘
         ↓
   ┌─────────────┐
   │ Mark visited│
   │ Add to queue│
   └──────┬──────┘
          ↓
    ┌──────────┐
    │Queue empty?├──Yes──→ DONE
    └─────┬────┘
          No
          ↓
   ┌──────────────┐
   │Dequeue vertex│
   └──────┬───────┘
          ↓
   ┌───────────────────┐
   │For each neighbor: │
   │ if not visited:   │
   │  - mark visited   │
   │  - enqueue        │
   └─────┬─────────────┘
         │
         └─────────┐
                   ↓
           (loop back to queue check)
```

**Properties:**

- **Time:** O(V + E)
- **Space:** O(V) for queue and visited array
- **Finds shortest path** in unweighted graphs
- **Level-order traversal**

**When to use:**

- Shortest path in unweighted graphs
- Level-order problems
- Finding connected components
- Checking bipartiteness

### BREADTH-FIRST SEARCH (BFS) IMPLEMENTATIONS

### Python, Rust, and Go

```python
from collections import deque
from typing import List, Set

def bfs_python(graph: List[List[int]], start: int) -> List[int]:
    """
    BFS traversal starting from 'start' vertex
    
    Args:
        graph: Adjacency list representation
        start: Starting vertex
    
    Returns:
        List of vertices in BFS order
    
    Time: O(V + E)
    Space: O(V)
    """
    visited = set()
    queue = deque([start])
    visited.add(start)
    result = []
    
    while queue:
        vertex = queue.popleft()  # O(1) dequeue
        result.append(vertex)
        
        # Explore all neighbors
        for neighbor in graph[vertex]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    
    return result


def bfs_with_distance(graph: List[List[int]], start: int) -> dict:
    """
    BFS that tracks distance from start to each vertex
    ESSENTIAL PATTERN for shortest path problems
    
    Returns:
        Dictionary mapping vertex → distance from start
    """
    distance = {start: 0}
    queue = deque([start])
    
    while queue:
        vertex = queue.popleft()
        
        for neighbor in graph[vertex]:
            if neighbor not in distance:
                distance[neighbor] = distance[vertex] + 1
                queue.append(neighbor)
    
    return distance


def bfs_shortest_path(graph: List[List[int]], start: int, end: int) -> List[int]:
    """
    Find shortest path from start to end
    CRITICAL PATTERN - memorize this
    
    Returns:
        Shortest path as list of vertices, or [] if no path exists
    """
    if start == end:
        return [start]
    
    visited = {start}
    queue = deque([start])
    parent = {start: None}  # Track parent for path reconstruction
    
    while queue:
        vertex = queue.popleft()
        
        for neighbor in graph[vertex]:
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = vertex
                queue.append(neighbor)
                
                # Found the target!
                if neighbor == end:
                    # Reconstruct path
                    path = []
                    current = end
                    while current is not None:
                        path.append(current)
                        current = parent[current]
                    return path[::-1]  # Reverse to get start→end
    
    return []  # No path exists
```

```rust
// Rust implementation with idiomatic patterns

use std::collections::{VecDeque, HashSet};

fn bfs(graph: &Vec<Vec<usize>>, start: usize) -> Vec<usize> {
    let mut visited = HashSet::new();
    let mut queue = VecDeque::new();
    let mut result = Vec::new();
    
    queue.push_back(start);
    visited.insert(start);
    
    while let Some(vertex) = queue.pop_front() {
        result.push(vertex);
        
        for &neighbor in &graph[vertex] {
            if visited.insert(neighbor) {  // insert returns false if already present
                queue.push_back(neighbor);
            }
        }
    }
    
    result
}

// Shortest path in Rust
fn bfs_shortest_path(
    graph: &Vec<Vec<usize>>, 
    start: usize, 
    end: usize
) -> Option<Vec<usize>> {
    if start == end {
        return Some(vec![start]);
    }
    
    let mut visited = HashSet::new();
    let mut queue = VecDeque::new();
    let mut parent = vec![None; graph.len()];
    
    queue.push_back(start);
    visited.insert(start);
    
    while let Some(vertex) = queue.pop_front() {
        for &neighbor in &graph[vertex] {
            if visited.insert(neighbor) {
                parent[neighbor] = Some(vertex);
                queue.push_back(neighbor);
                
                if neighbor == end {
                    // Reconstruct path
                    let mut path = Vec::new();
                    let mut current = Some(end);
                    
                    while let Some(v) = current {
                        path.push(v);
                        current = parent[v];
                    }
                    
                    path.reverse();
                    return Some(path);
                }
            }
        }
    }
    
    None  // No path found
}
```

```golang
// Go implementation with container/list for queue

package main

import "container/list"

func BFS(graph [][]int, start int) []int {
    visited := make(map[int]bool)
    queue := list.New()
    result := []int{}
    
    queue.PushBack(start)
    visited[start] = true
    
    for queue.Len() > 0 {
        element := queue.Front()
        vertex := element.Value.(int)
        queue.Remove(element)
        
        result = append(result, vertex)
        
        for _, neighbor := range graph[vertex] {
            if !visited[neighbor] {
                visited[neighbor] = true
                queue.PushBack(neighbor)
            }
        }
    }
    
    return result
}

// Shortest path in Go
func BFSShortestPath(graph [][]int, start, end int) []int {
    if start == end {
        return []int{start}
    }
    
    visited := make(map[int]bool)
    queue := list.New()
    parent := make(map[int]int)
    
    queue.PushBack(start)
    visited[start] = true
    parent[start] = -1  // No parent for start
    
    for queue.Len() > 0 {
        element := queue.Front()
        vertex := element.Value.(int)
        queue.Remove(element)
        
        for _, neighbor := range graph[vertex] {
            if !visited[neighbor] {
                visited[neighbor] = true
                parent[neighbor] = vertex
                queue.PushBack(neighbor)
                
                if neighbor == end {
                    // Reconstruct path
                    path := []int{}
                    current := end
                    
                    for current != -1 {
                        path = append([]int{current}, path...)
                        current = parent[current]
                    }
                    
                    return path
                }
            }
        }
    }
    
    return []int{}  // No path found
}
```

### DEMONSTRATION & TESTING

```python
def test_bfs():
    """Test all BFS variations"""
    
    # Create a sample graph
    #     0
    #    / \
    #   1   2
    #  / \   \
    # 3   4   5
    
    graph = [
        [1, 2],     # 0's neighbors
        [0, 3, 4],  # 1's neighbors
        [0, 5],     # 2's neighbors
        [1],        # 3's neighbors
        [1],        # 4's neighbors
        [2]         # 5's neighbors
    ]
    
    print("Graph structure:")
    for i, neighbors in enumerate(graph):
        print(f"  {i}: {neighbors}")
    
    print("\n=== Basic BFS Traversal ===")
    traversal = bfs_python(graph, 0)
    print(f"BFS from 0: {traversal}")
    
    print("\n=== BFS with Distance ===")
    distances = bfs_with_distance(graph, 0)
    print("Distances from vertex 0:")
    for vertex, dist in sorted(distances.items()):
        print(f"  Vertex {vertex}: distance {dist}")
    
    print("\n=== Shortest Path ===")
    path = bfs_shortest_path(graph, 0, 5)
    print(f"Shortest path from 0 to 5: {path}")
    print(f"Path length: {len(path) - 1}")


if __name__ == "__main__":
    test_bfs()
```
---

### **4.2 Depth-First Search (DFS)**

**Core Idea:** Explore as deep as possible along each branch before backtracking

**Data Structure:** **Stack** (LIFO - Last In, First Out) or **Recursion** (implicit stack)

**ASCII Visualization:**
```
DFS explores one path completely before trying another:

        (0)
       ↙   ↘
     (1)   (2)
    ↙  ↘    ↘
  (3)  (4)  (5)

DFS order: 0 → 1 → 3 → 4 → 2 → 5
(goes deep left first, then backtracks)

Call stack evolution:
dfs(0)
  dfs(1)
    dfs(3)  → returns
    dfs(4)  → returns
  dfs(2)
    dfs(5)  → returns
```

**Algorithm Flow:**
```
      ┌──────────────┐
      │ Visit vertex │
      │ Mark visited │
      └──────┬───────┘
             ↓
    ┌────────────────────┐
    │ For each neighbor: │
    │  if not visited:   │
    │    recursively DFS │
    └────────┬───────────┘
             ↓
       ┌─────────┐
       │ Backtrack│
       └──────────┘
```

**Properties:**

- **Time:** O(V + E)
- **Space:** O(V) for recursion stack/visited array
- Uses **recursion** or **explicit stack**
- **Does NOT find shortest path** in unweighted graphs
- Natural for tree problems

**When to use:**

- Cycle detection
- Topological sorting
- Connected components
- Path existence
- Tree traversal
- Backtracking problems


### DEPTH-FIRST SEARCH (DFS) IMPLEMENTATIONS

### Python, Rust, and Go

```python
from typing import List, Set


def dfs_recursive(graph: List[List[int]], start: int, 
                 visited: Set[int] = None, result: List[int] = None) -> List[int]:
    """
    Recursive DFS - Most elegant and common
    
    Args:
        graph: Adjacency list
        start: Starting vertex
        visited: Set of visited vertices (internal)
        result: Accumulator for result (internal)
    
    Returns:
        List of vertices in DFS order
    
    Time: O(V + E)
    Space: O(V) for recursion stack
    """
    if visited is None:
        visited = set()
    if result is None:
        result = []
    
    visited.add(start)
    result.append(start)
    
    for neighbor in graph[start]:
        if neighbor not in visited:
            dfs_recursive(graph, neighbor, visited, result)
    
    return result


def dfs_iterative(graph: List[List[int]], start: int) -> List[int]:
    """
    Iterative DFS using explicit stack
    
    Note: Order may differ slightly from recursive version
    due to how neighbors are pushed onto stack
    
    Time: O(V + E)
    Space: O(V) for stack
    """
    visited = set()
    stack = [start]
    result = []
    
    while stack:
        vertex = stack.pop()  # LIFO - Last In First Out
        
        if vertex not in visited:
            visited.add(vertex)
            result.append(vertex)
            
            # Add neighbors to stack
            # Reverse order to match recursive DFS traversal
            for neighbor in reversed(graph[vertex]):
                if neighbor not in visited:
                    stack.append(neighbor)
    
    return result


def dfs_all_paths(graph: List[List[int]], start: int, end: int) -> List[List[int]]:
    """
    Find ALL paths from start to end using DFS backtracking
    CRITICAL PATTERN for backtracking problems
    
    Returns:
        List of all possible paths
    """
    def backtrack(vertex: int, path: List[int], all_paths: List[List[int]]):
        # Base case: reached destination
        if vertex == end:
            all_paths.append(path[:])  # Copy current path
            return
        
        # Explore all neighbors
        for neighbor in graph[vertex]:
            if neighbor not in path:  # Avoid cycles
                path.append(neighbor)
                backtrack(neighbor, path, all_paths)
                path.pop()  # BACKTRACK - remove last vertex
    
    all_paths = []
    backtrack(start, [start], all_paths)
    return all_paths


def has_path_dfs(graph: List[List[int]], start: int, end: int) -> bool:
    """
    Check if path exists from start to end
    Simple DFS application
    """
    if start == end:
        return True
    
    visited = set()
    
    def dfs(vertex: int) -> bool:
        if vertex == end:
            return True
        
        visited.add(vertex)
        
        for neighbor in graph[vertex]:
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
        
        return False
    
    return dfs(start)

```

```rust
// Rust DFS implementations

use std::collections::HashSet;

// Recursive DFS
fn dfs_recursive(
    graph: &Vec<Vec<usize>>,
    vertex: usize,
    visited: &mut HashSet<usize>,
    result: &mut Vec<usize>
) {
    visited.insert(vertex);
    result.push(vertex);
    
    for &neighbor in &graph[vertex] {
        if !visited.contains(&neighbor) {
            dfs_recursive(graph, neighbor, visited, result);
        }
    }
}

// Wrapper function for clean API
fn dfs(graph: &Vec<Vec<usize>>, start: usize) -> Vec<usize> {
    let mut visited = HashSet::new();
    let mut result = Vec::new();
    dfs_recursive(graph, start, &mut visited, &mut result);
    result
}

// Iterative DFS
fn dfs_iterative(graph: &Vec<Vec<usize>>, start: usize) -> Vec<usize> {
    let mut visited = HashSet::new();
    let mut stack = vec![start];
    let mut result = Vec::new();
    
    while let Some(vertex) = stack.pop() {
        if visited.insert(vertex) {  // Returns false if already visited
            result.push(vertex);
            
            // Push neighbors in reverse order
            for &neighbor in graph[vertex].iter().rev() {
                if !visited.contains(&neighbor) {
                    stack.push(neighbor);
                }
            }
        }
    }
    
    result
}

// Check if path exists
fn has_path_dfs(graph: &Vec<Vec<usize>>, start: usize, end: usize) -> bool {
    fn dfs_helper(
        graph: &Vec<Vec<usize>>,
        vertex: usize,
        end: usize,
        visited: &mut HashSet<usize>
    ) -> bool {
        if vertex == end {
            return true;
        }
        
        visited.insert(vertex);
        
        for &neighbor in &graph[vertex] {
            if !visited.contains(&neighbor) {
                if dfs_helper(graph, neighbor, end, visited) {
                    return true;
                }
            }
        }
        
        false
    }
    
    if start == end {
        return true;
    }
    
    let mut visited = HashSet::new();
    dfs_helper(graph, start, end, &mut visited)
}
```

```golang
// Go DFS implementations

package main

// Recursive DFS
func DFSRecursive(graph [][]int, vertex int, visited map[int]bool, result *[]int) {
    visited[vertex] = true
    *result = append(*result, vertex)
    
    for _, neighbor := range graph[vertex] {
        if !visited[neighbor] {
            DFSRecursive(graph, neighbor, visited, result)
        }
    }
}

// Wrapper for clean API
func DFS(graph [][]int, start int) []int {
    visited := make(map[int]bool)
    result := []int{}
    DFSRecursive(graph, start, visited, &result)
    return result
}

// Iterative DFS
func DFSIterative(graph [][]int, start int) []int {
    visited := make(map[int]bool)
    stack := []int{start}
    result := []int{}
    
    for len(stack) > 0 {
        // Pop from stack
        vertex := stack[len(stack)-1]
        stack = stack[:len(stack)-1]
        
        if !visited[vertex] {
            visited[vertex] = true
            result = append(result, vertex)
            
            // Push neighbors (in reverse for consistent order)
            for i := len(graph[vertex]) - 1; i >= 0; i-- {
                neighbor := graph[vertex][i]
                if !visited[neighbor] {
                    stack = append(stack, neighbor)
                }
            }
        }
    }
    
    return result
}

// Check if path exists
func HasPathDFS(graph [][]int, start, end int) bool {
    if start == end {
        return true
    }
    
    visited := make(map[int]bool)
    
    var dfs func(int) bool
    dfs = func(vertex int) bool {
        if vertex == end {
            return true
        }
        
        visited[vertex] = true
        
        for _, neighbor := range graph[vertex] {
            if !visited[neighbor] {
                if dfs(neighbor) {
                    return true
                }
            }
        }
        
        return false
    }
    
    return dfs(start)
}
```

### DEMONSTRATION & TESTING

```python
def test_dfs():
    """Test all DFS variations"""
    
    # Same graph as BFS example
    graph = [
        [1, 2],     # 0
        [0, 3, 4],  # 1
        [0, 5],     # 2
        [1],        # 3
        [1],        # 4
        [2]         # 5
    ]
    
    print("=== DFS Recursive ===")
    dfs_rec = dfs_recursive(graph, 0)
    print(f"DFS from 0: {dfs_rec}")
    
    print("\n=== DFS Iterative ===")
    dfs_iter = dfs_iterative(graph, 0)
    print(f"DFS from 0: {dfs_iter}")
    
    print("\n=== Path Existence ===")
    print(f"Path exists 0→5? {has_path_dfs(graph, 0, 5)}")
    print(f"Path exists 3→2? {has_path_dfs(graph, 3, 2)}")
    
    print("\n=== All Paths (Backtracking) ===")
    all_paths = dfs_all_paths(graph, 0, 5)
    print(f"All paths from 0 to 5:")
    for i, path in enumerate(all_paths, 1):
        print(f"  Path {i}: {' → '.join(map(str, path))}")


```

### BFS vs DFS COMPARISON

```python
def compare_bfs_dfs():
    """
    Visual comparison of BFS vs DFS traversal order
    """
    from collections import deque
    
    graph = [
        [1, 2],
        [0, 3, 4],
        [0, 5],
        [1],
        [1],
        [2]
    ]
    
    # BFS
    bfs_order = []
    visited = set([0])
    q = deque([0])
    while q:
        v = q.popleft()
        bfs_order.append(v)
        for n in graph[v]:
            if n not in visited:
                visited.add(n)
                q.append(n)
    
    # DFS
    dfs_order = dfs_recursive(graph, 0)
    
    print("=== TRAVERSAL ORDER COMPARISON ===")
    print(f"BFS: {bfs_order}")
    print(f"DFS: {dfs_order}")
    print("\nBFS explores level-by-level (breadth)")
    print("DFS explores path-by-path (depth)")


if __name__ == "__main__":
    test_dfs()
    print("\n" + "="*50 + "\n")
    compare_bfs_dfs()

```
---

### **BFS vs DFS: When to Use Which?**

**Decision Tree:**
```
                Need shortest path?
                       │
           ┌───────────┴───────────┐
          YES                      NO
           │                        │
         BFS                   Any will work
                                    │
                          ┌─────────┴─────────┐
                    Need to explore      Backtracking/
                    all solutions?       Path finding?
                          │                    │
                       DFS (easier)          DFS
```

**Use BFS when:**

- Finding shortest path in unweighted graph ⭐
- Level-order traversal needed
- Finding minimum steps/moves
- Checking if graph is bipartite

**Use DFS when:**

- Detecting cycles
- Topological sorting
- Finding connected components (either works)
- Backtracking (finding all paths)
- Tree problems
- Memory is constrained (BFS needs more memory for wide graphs)

---

## **5. Shortest Path in Unweighted Graphs**

### **Fundamental Theorem**

> In an **unweighted graph**, BFS finds the shortest path from source to all reachable vertices.

**Why?** BFS explores vertices in increasing order of distance from source.

**Critical Pattern:** Always use BFS for shortest path in unweighted graphs.

### **Common Variations**

1. **Single-source shortest path**: BFS from one vertex
2. **Multi-source BFS**: Start BFS from multiple vertices simultaneously
3. **Bidirectional BFS**: Search from both start and end (optimization)


### SHORTEST PATH PATTERNS IN UNWEIGHTED GRAPHS

### Master these patterns - they appear in 50%+ of graph problems

```python
from collections import deque
from typing import List, Set, Tuple, Optional

## PATTERN 1: Single-Source Shortest Path

def shortest_path_distances(graph: List[List[int]], source: int) -> dict:
    """
    Find shortest distance from source to ALL vertices
    
    Returns:
        dict mapping vertex → distance from source
        Vertices not in dict are unreachable
    
    Time: O(V + E)
    Space: O(V)
    
    MEMORIZE THIS - appears in countless problems
    """
    distance = {source: 0}
    queue = deque([source])
    
    while queue:
        vertex = queue.popleft()
        
        for neighbor in graph[vertex]:
            if neighbor not in distance:
                distance[neighbor] = distance[vertex] + 1
                queue.append(neighbor)
    
    return distance


def shortest_path_with_reconstruction(
    graph: List[List[int]], 
    start: int, 
    end: int
) -> Tuple[int, List[int]]:
    """
    Find shortest path AND the actual path
    
    Returns:
        (distance, path) or (-1, []) if no path exists
    
    KEY INSIGHT: Track parent pointers during BFS
    """
    if start == end:
        return (0, [start])
    
    visited = {start}
    queue = deque([start])
    parent = {start: None}
    
    while queue:
        vertex = queue.popleft()
        
        for neighbor in graph[vertex]:
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = vertex
                queue.append(neighbor)
                
                if neighbor == end:
                    # Reconstruct path
                    path = []
                    current = end
                    while current is not None:
                        path.append(current)
                        current = parent[current]
                    
                    path.reverse()
                    return (len(path) - 1, path)
    
    return (-1, [])  # No path found

### PATTERN 2: Multi-Source BFS


def multi_source_shortest_distance(
    graph: List[List[int]], 
    sources: List[int]
) -> dict:
    """
    Find shortest distance from ANY source to all vertices
    
    CRITICAL PATTERN: Common in matrix problems (rotting oranges, etc.)
    
    Key idea: Add ALL sources to queue initially
    
    Example use cases:
    - Multiple starting points
    - "Spread" or "infection" problems
    - Finding nearest facility/resource
    
    Time: O(V + E)
    """
    distance = {}
    queue = deque()
    
    # Initialize: add ALL sources with distance 0
    for source in sources:
        distance[source] = 0
        queue.append(source)
    
    while queue:
        vertex = queue.popleft()
        
        for neighbor in graph[vertex]:
            if neighbor not in distance:
                distance[neighbor] = distance[vertex] + 1
                queue.append(neighbor)
    
    return distance


# PATTERN 3: Bidirectional BFS


def bidirectional_bfs(
    graph: List[List[int]], 
    start: int, 
    end: int
) -> int:
    """
    Optimization: Search from BOTH start and end simultaneously
    
    When to use:
    - Large graphs where you know start and end
    - Can reduce search space significantly
    
    Time: O(V + E) but often much faster in practice
    Speedup: Instead of exploring b^d nodes, explores 2*b^(d/2)
    where b = branching factor, d = distance
    
    Returns:
        Shortest distance, or -1 if no path
    """
    if start == end:
        return 0
    
    # Two BFS searches
    visited_from_start = {start: 0}
    visited_from_end = {end: 0}
    
    queue_start = deque([start])
    queue_end = deque([end])
    
    distance = 0
    
    while queue_start or queue_end:
        distance += 1
        
        # Expand from start
        if queue_start:
            for _ in range(len(queue_start)):
                vertex = queue_start.popleft()
                
                for neighbor in graph[vertex]:
                    # Found connection!
                    if neighbor in visited_from_end:
                        return distance + visited_from_end[neighbor]
                    
                    if neighbor not in visited_from_start:
                        visited_from_start[neighbor] = distance
                        queue_start.append(neighbor)
        
        # Expand from end
        if queue_end:
            for _ in range(len(queue_end)):
                vertex = queue_end.popleft()
                
                for neighbor in graph[vertex]:
                    # Found connection!
                    if neighbor in visited_from_start:
                        return distance + visited_from_start[neighbor]
                    
                    if neighbor not in visited_from_end:
                        visited_from_end[neighbor] = distance
                        queue_end.append(neighbor)
    
    return -1  # No path exists



# PATTERN 4: 0-1 BFS (Bonus)


def zero_one_bfs(graph: List[List[Tuple[int, int]]], start: int) -> dict:
    """
    Special case: Graph with edge weights of only 0 or 1
    
    KEY INSIGHT: Use deque, add 0-weight edges to FRONT, 1-weight to BACK
    This maintains sorted order by distance
    
    graph[u] = [(v, weight), ...] where weight ∈ {0, 1}
    
    Faster than Dijkstra for this special case
    Time: O(V + E)
    """
    distance = {start: 0}
    dq = deque([start])
    
    while dq:
        vertex = dq.popleft()
        
        for neighbor, weight in graph[vertex]:
            new_dist = distance[vertex] + weight
            
            if neighbor not in distance or new_dist < distance[neighbor]:
                distance[neighbor] = new_dist
                
                if weight == 0:
                    dq.appendleft(neighbor)  # Add to FRONT
                else:
                    dq.append(neighbor)  # Add to BACK
    
    return distance



# TESTING & DEMONSTRATIONS

def test_shortest_path_patterns():
    """Test all patterns"""
    
    # Graph for testing
    #     0 --- 1 --- 3
    #     |     |     |
    #     2 --- 4 --- 5
    
    graph = [
        [1, 2],      # 0
        [0, 3, 4],   # 1
        [0, 4],      # 2
        [1, 5],      # 3
        [1, 2, 5],   # 4
        [3, 4]       # 5
    ]
    
    print("=== Single-Source Shortest Distances ===")
    distances = shortest_path_distances(graph, 0)
    print("Distances from vertex 0:")
    for v in sorted(distances.keys()):
        print(f"  To {v}: {distances[v]}")
    
    print("\n=== Shortest Path with Reconstruction ===")
    dist, path = shortest_path_with_reconstruction(graph, 0, 5)
    print(f"Shortest path 0→5: {' → '.join(map(str, path))}")
    print(f"Distance: {dist}")
    
    print("\n=== Multi-Source BFS ===")
    multi_dist = multi_source_shortest_distance(graph, [0, 5])
    print("Distances from sources {0, 5}:")
    for v in sorted(multi_dist.keys()):
        print(f"  To {v}: {multi_dist[v]}")
    
    print("\n=== Bidirectional BFS ===")
    bi_dist = bidirectional_bfs(graph, 0, 5)
    print(f"Distance 0→5 (bidirectional): {bi_dist}")
    
    print("\n=== 0-1 BFS Example ===")
    # Graph with 0/1 weights
    weighted_graph = [
        [(1, 0), (2, 1)],      # 0 → 1 (weight 0), 0 → 2 (weight 1)
        [(3, 1)],              # 1 → 3 (weight 1)
        [(3, 0)],              # 2 → 3 (weight 0)
        []                     # 3
    ]
    zero_one_dist = zero_one_bfs(weighted_graph, 0)
    print("0-1 BFS distances from 0:")
    for v in sorted(zero_one_dist.keys()):
        print(f"  To {v}: {zero_one_dist[v]}")


# PROBLEM-SOLVING TEMPLATE


def shortest_path_template(graph: List[List[int]], start: int, target: int) -> int:
    """
    UNIVERSAL TEMPLATE for shortest path in unweighted graph
    
    Modify the 'process neighbor' section for specific problems
    
    Steps:
    1. Initialize queue with start, mark visited
    2. Track distance/level
    3. BFS expansion
    4. Check target condition
    5. Return result
    """
    if start == target:
        return 0
    
    visited = {start}
    queue = deque([start])
    distance = 0
    
    while queue:
        distance += 1  # Increment distance for this level
        
        # Process entire level
        for _ in range(len(queue)):
            vertex = queue.popleft()
            
            for neighbor in graph[vertex]:
                if neighbor == target:
                    return distance
                
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
    
    return -1  # No path found


if __name__ == "__main__":
    test_shortest_path_patterns()

```
---

## **6. Cycle Detection**

### **What is a Cycle?**

A **cycle** is a path where you can start at a vertex and return to it by following edges.

```
Cycle Example:
    1 → 2
    ↑   ↓
    4 ← 3

Path: 1 → 2 → 3 → 4 → 1 (returns to start)
```

### **Why Detect Cycles?**

- Validate if graph is a tree (trees have no cycles)
- Check for deadlocks
- Find dependencies (cyclic dependencies are problematic)
- Topological sort prerequisite (only works on acyclic graphs)

---

### **Detection Methods by Graph Type**

**Decision Flow:**
```
        What type of graph?
               │
    ┌──────────┴──────────┐
    │                     │
Undirected            Directed
    │                     │
Use DFS with          Use DFS with
parent tracking       3-color method
```


### CYCLE DETECTION IN GRAPHS

### Different strategies for undirected vs directed graphs

```python
from typing import List, Set
from enum import Enum

# UNDIRECTED GRAPH CYCLE DETECTION


def has_cycle_undirected_dfs(graph: List[List[int]]) -> bool:
    """
    Detect cycle in UNDIRECTED graph using DFS
    
    KEY INSIGHT: In undirected graph, a cycle exists if we visit
    a vertex that's already visited AND it's not our parent
    
    Why parent check? In undirected graph, edge A-B means both A→B and B→A
    We need to distinguish between:
    - Visiting parent (not a cycle)
    - Visiting already-visited non-parent (cycle!)
    
    Time: O(V + E)
    Space: O(V)
    """
    visited = set()
    
    def dfs(vertex: int, parent: int) -> bool:
        visited.add(vertex)
        
        for neighbor in graph[vertex]:
            if neighbor not in visited:
                if dfs(neighbor, vertex):
                    return True
            elif neighbor != parent:
                # Found a visited vertex that's not our parent - CYCLE!
                return True
        
        return False
    
    # Check all components (graph might be disconnected)
    for v in range(len(graph)):
        if v not in visited:
            if dfs(v, -1):  # -1 means no parent
                return True
    
    return False



# DIRECTED GRAPH CYCLE DETECTION


class Color(Enum):
    """
    Three-color method for directed graphs
    
    WHITE (0): Unvisited
    GRAY (1):  Visiting (in current DFS path)
    BLACK (2): Visited (completely processed)
    """
    WHITE = 0
    GRAY = 1
    BLACK = 2


def has_cycle_directed_dfs(graph: List[List[int]]) -> bool:
    """
    Detect cycle in DIRECTED graph using 3-color DFS
    
    KEY INSIGHT: A cycle exists if we encounter a GRAY vertex
    during DFS (vertex in current recursion path)
    
    Why 3 colors?
    - WHITE: Not yet explored
    - GRAY: Currently exploring (in recursion stack)
    - BLACK: Fully explored
    
    Cycle exists ⟺ We find a back edge to a GRAY vertex
    
    Time: O(V + E)
    Space: O(V)
    
    CRITICAL PATTERN - Appears in topological sort, deadlock detection
    """
    color = [Color.WHITE] * len(graph)
    
    def dfs(vertex: int) -> bool:
        color[vertex] = Color.GRAY  # Mark as "currently visiting"
        
        for neighbor in graph[vertex]:
            if color[neighbor] == Color.GRAY:
                # Found back edge to vertex in current path - CYCLE!
                return True
            
            if color[neighbor] == Color.WHITE:
                if dfs(neighbor):
                    return True
        
        color[vertex] = Color.BLACK  # Mark as "completely visited"
        return False
    
    # Check all vertices (graph might be disconnected)
    for v in range(len(graph)):
        if color[v] == Color.WHITE:
            if dfs(v):
                return True
    
    return False


def find_cycle_directed(graph: List[List[int]]) -> List[int]:
    """
    Not only detect, but FIND the actual cycle
    
    Returns:
        List of vertices forming a cycle, or [] if no cycle
    """
    color = [Color.WHITE] * len(graph)
    parent = [-1] * len(graph)
    cycle_start = -1
    cycle_end = -1
    
    def dfs(vertex: int) -> bool:
        nonlocal cycle_start, cycle_end
        
        color[vertex] = Color.GRAY
        
        for neighbor in graph[vertex]:
            if color[neighbor] == Color.GRAY:
                # Found cycle!
                cycle_start = neighbor
                cycle_end = vertex
                return True
            
            if color[neighbor] == Color.WHITE:
                parent[neighbor] = vertex
                if dfs(neighbor):
                    return True
        
        color[vertex] = Color.BLACK
        return False
    
    # Find cycle
    for v in range(len(graph)):
        if color[v] == Color.WHITE:
            if dfs(v):
                break
    
    if cycle_start == -1:
        return []  # No cycle found
    
    # Reconstruct cycle
    cycle = []
    current = cycle_end
    
    while current != cycle_start:
        cycle.append(current)
        current = parent[current]
    
    cycle.append(cycle_start)
    cycle.reverse()
    
    return cycle



# UNION-FIND METHOD (Undirected)


class UnionFind:
    """
    Alternative method for cycle detection in undirected graphs
    
    Useful when building graph edge by edge
    """
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n
    
    def find(self, x: int) -> int:
        """Find root with path compression"""
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]
    
    def union(self, x: int, y: int) -> bool:
        """
        Union two sets
        
        Returns:
            True if union successful, False if already in same set (cycle!)
        """
        root_x = self.find(x)
        root_y = self.find(y)
        
        if root_x == root_y:
            return False  # Already connected - adding edge creates cycle!
        
        # Union by rank
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1
        
        return True


def has_cycle_undirected_unionfind(n: int, edges: List[List[int]]) -> bool:
    """
    Detect cycle using Union-Find
    
    Process edges one by one:
    - If endpoints already in same set → cycle
    - Otherwise, union the sets
    
    Time: O(E × α(V)) where α is inverse Ackermann (nearly constant)
    Space: O(V)
    """
    uf = UnionFind(n)
    
    for u, v in edges:
        if not uf.union(u, v):
            return True  # Cycle detected!
    
    return False



# TESTING & VISUALIZATION


def test_cycle_detection():
    """Test all cycle detection methods"""
    
    print("=== UNDIRECTED GRAPHS ===\n")
    
    # Graph WITH cycle
    #   0 - 1
    #   |   |
    #   2 - 3
    graph_with_cycle = [
        [1, 2],  # 0
        [0, 3],  # 1
        [0, 3],  # 2
        [1, 2]   # 3
    ]
    
    # Graph WITHOUT cycle (tree)
    #   0
    #  / \
    # 1   2
    #     |
    #     3
    graph_without_cycle = [
        [1, 2],  # 0
        [0],     # 1
        [0, 3],  # 2
        [2]      # 3
    ]
    
    print("Graph with cycle:")
    print(f"  Has cycle (DFS)? {has_cycle_undirected_dfs(graph_with_cycle)}")
    
    edges_with_cycle = [(0, 1), (0, 2), (1, 3), (2, 3)]
    print(f"  Has cycle (Union-Find)? {has_cycle_undirected_unionfind(4, edges_with_cycle)}")
    
    print("\nGraph without cycle (tree):")
    print(f"  Has cycle (DFS)? {has_cycle_undirected_dfs(graph_without_cycle)}")
    
    edges_without_cycle = [(0, 1), (0, 2), (2, 3)]
    print(f"  Has cycle (Union-Find)? {has_cycle_undirected_unionfind(4, edges_without_cycle)}")
    
    print("\n=== DIRECTED GRAPHS ===\n")
    
    # Directed graph WITH cycle
    #   0 → 1
    #   ↓   ↓
    #   2 → 3
    #   ↑___↓
    directed_with_cycle = [
        [1, 2],  # 0 → 1, 0 → 2
        [3],     # 1 → 3
        [3],     # 2 → 3
        [2]      # 3 → 2 (creates cycle!)
    ]
    
    # Directed graph WITHOUT cycle (DAG)
    #   0 → 1
    #   ↓   ↓
    #   2 → 3
    directed_without_cycle = [
        [1, 2],  # 0 → 1, 0 → 2
        [3],     # 1 → 3
        [3],     # 2 → 3
        []       # 3
    ]
    
    print("Directed graph with cycle:")
    has_cycle = has_cycle_directed_dfs(directed_with_cycle)
    print(f"  Has cycle? {has_cycle}")
    
    if has_cycle:
        cycle = find_cycle_directed(directed_with_cycle)
        print(f"  Cycle found: {' → '.join(map(str, cycle))}")
    
    print("\nDirected graph without cycle (DAG):")
    print(f"  Has cycle? {has_cycle_directed_dfs(directed_without_cycle)}")



# ALGORITHM COMPARISON


def print_algorithm_comparison():
    """
    Summary of when to use which algorithm
    """
    print("\n" + "="*60)
    print("CYCLE DETECTION - ALGORITHM SELECTION GUIDE")
    print("="*60)
    
    print("\nUNDIRECTED GRAPHS:")
    print("  DFS with parent tracking:")
    print("    ✓ When: Graph already built as adjacency list")
    print("    ✓ Time: O(V + E)")
    print("    ✓ Simple to implement")
    
    print("\n  Union-Find:")
    print("    ✓ When: Building graph edge-by-edge")
    print("    ✓ When: Need to detect cycle while adding edges")
    print("    ✓ Time: O(E × α(V)) ≈ O(E)")
    print("    ✓ Useful for Kruskal's MST algorithm")
    
    print("\nDIRECTED GRAPHS:")
    print("  3-Color DFS:")
    print("    ✓ Only reliable method for directed graphs")
    print("    ✓ Time: O(V + E)")
    print("    ✓ Essential for topological sort")
    print("    ✓ Can find actual cycle, not just detect")


if __name__ == "__main__":
    test_cycle_detection()
    print_algorithm_comparison()

```
---

## **7. Connected Components**

### **What is a Connected Component?**

A **connected component** is a maximal set of vertices where every vertex is reachable from every other vertex in that set.

**ASCII Visualization:**
```
Graph with 3 connected components:

Component 1:  Component 2:  Component 3:
   0---1         4---5          7
   |   |                        |
   2---3            6            8

Total vertices: 9
Total components: 3
```

### **Applications:**

- Social network analysis (friend groups)
- Image processing (blob detection)
- Network connectivity
- Finding islands in a grid


### CONNECTED COMPONENTS

### Finding and analyzing connected subgraphs

```python
from typing import List, Set, Dict
from collections import deque


# BASIC CONNECTED COMPONENTS


def count_components_dfs(graph: List[List[int]]) -> int:
    """
    Count number of connected components using DFS
    
    Algorithm:
    1. Start with count = 0
    2. For each unvisited vertex:
       - Increment count
       - DFS to mark entire component as visited
    
    Time: O(V + E)
    Space: O(V)
    """
    visited = set()
    count = 0
    
    def dfs(vertex: int):
        visited.add(vertex)
        for neighbor in graph[vertex]:
            if neighbor not in visited:
                dfs(neighbor)
    
    for v in range(len(graph)):
        if v not in visited:
            count += 1
            dfs(v)
    
    return count


def count_components_bfs(graph: List[List[int]]) -> int:
    """
    Count components using BFS
    
    BFS and DFS are equivalent for this problem
    Choose based on preference or constraints
    """
    visited = set()
    count = 0
    
    def bfs(start: int):
        queue = deque([start])
        visited.add(start)
        
        while queue:
            vertex = queue.popleft()
            for neighbor in graph[vertex]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
    
    for v in range(len(graph)):
        if v not in visited:
            count += 1
            bfs(v)
    
    return count



# FIND COMPONENTS WITH LABELS


def label_components(graph: List[List[int]]) -> Dict[int, int]:
    """
    Assign each vertex a component ID
    
    Returns:
        dict mapping vertex → component_id
    
    Example:
        {0: 0, 1: 0, 2: 1, 3: 1, 4: 2}
        means vertices 0,1 in component 0, vertices 2,3 in component 1, etc.
    
    CRITICAL PATTERN for Union-Find equivalence
    """
    component = {}
    component_id = 0
    
    def dfs(vertex: int, comp_id: int):
        component[vertex] = comp_id
        for neighbor in graph[vertex]:
            if neighbor not in component:
                dfs(neighbor, comp_id)
    
    for v in range(len(graph)):
        if v not in component:
            dfs(v, component_id)
            component_id += 1
    
    return component


def get_component_vertices(graph: List[List[int]]) -> List[List[int]]:
    """
    Get actual list of vertices in each component
    
    Returns:
        List of components, where each component is a list of vertices
    
    Example:
        [[0, 1, 2], [3, 4], [5]]
        means component 0 has vertices {0,1,2}, component 1 has {3,4}, etc.
    """
    visited = set()
    components = []
    
    def dfs(vertex: int, component: List[int]):
        visited.add(vertex)
        component.append(vertex)
        for neighbor in graph[vertex]:
            if neighbor not in visited:
                dfs(neighbor, component)
    
    for v in range(len(graph)):
        if v not in visited:
            component = []
            dfs(v, component)
            components.append(component)
    
    return components



# COMPONENT SIZES


def get_component_sizes(graph: List[List[int]]) -> List[int]:
    """
    Find size of each connected component
    
    Returns:
        List of component sizes, sorted in descending order
    
    Useful for:
    - Finding largest component
    - Distribution analysis
    """
    visited = set()
    sizes = []
    
    def dfs(vertex: int) -> int:
        visited.add(vertex)
        size = 1
        for neighbor in graph[vertex]:
            if neighbor not in visited:
                size += dfs(neighbor)
        return size
    
    for v in range(len(graph)):
        if v not in visited:
            size = dfs(v)
            sizes.append(size)
    
    return sorted(sizes, reverse=True)


def largest_component_size(graph: List[List[int]]) -> int:
    """
    Find size of largest connected component
    
    Common interview question
    """
    sizes = get_component_sizes(graph)
    return sizes[0] if sizes else 0



# UNION-FIND APPROACH


class UnionFind:
    """
    Alternative approach using Union-Find (Disjoint Set Union)
    
    Advantage: Dynamic - can add edges incrementally
    Can answer "are vertices connected?" in near-constant time
    """
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.components = n  # Initially, each vertex is its own component
    
    def find(self, x: int) -> int:
        """Find root with path compression"""
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]
    
    def union(self, x: int, y: int) -> bool:
        """
        Union two components
        
        Returns:
            True if union was performed, False if already in same component
        """
        root_x = self.find(x)
        root_y = self.find(y)
        
        if root_x == root_y:
            return False  # Already in same component
        
        # Union by rank
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1
        
        self.components -= 1  # Merged two components
        return True
    
    def connected(self, x: int, y: int) -> bool:
        """Check if two vertices are in same component"""
        return self.find(x) == self.find(y)
    
    def count_components(self) -> int:
        """Return number of components"""
        return self.components


def count_components_unionfind(n: int, edges: List[List[int]]) -> int:
    """
    Count components using Union-Find
    
    Useful when:
    - Graph given as edge list
    - Need to build graph incrementally
    - Need dynamic connectivity queries
    
    Time: O(E × α(V)) where α is inverse Ackermann
    """
    uf = UnionFind(n)
    
    for u, v in edges:
        uf.union(u, v)
    
    return uf.count_components()


# SPECIAL PATTERNS


def is_fully_connected(graph: List[List[int]]) -> bool:
    """
    Check if graph has exactly 1 connected component
    
    I.e., can reach any vertex from any other vertex
    """
    if not graph:
        return True
    
    visited = set()
    
    def dfs(vertex: int):
        visited.add(vertex)
        for neighbor in graph[vertex]:
            if neighbor not in visited:
                dfs(neighbor)
    
    # Start DFS from vertex 0
    dfs(0)
    
    # If all vertices visited, graph is fully connected
    return len(visited) == len(graph)


def bridges_to_connect_all(graph: List[List[int]]) -> int:
    """
    Minimum number of edges needed to make graph fully connected
    
    Answer: (number of components) - 1
    
    Intuition: Need (k-1) edges to connect k components into one
    """
    return count_components_dfs(graph) - 1



# TESTING & DEMONSTRATION


def test_connected_components():
    """Test all component algorithms"""
    
    # Create graph with 3 components
    #
    # Component 1:  Component 2:  Component 3:
    #    0---1         4---5           7
    #    |   |                         |
    #    2---3            6             8
    
    graph = [
        [1, 2],     # 0
        [0, 3],     # 1
        [0, 3],     # 2
        [1, 2],     # 3
        [5],        # 4
        [4],        # 5
        [],         # 6 (isolated)
        [8],        # 7
        [7]         # 8
    ]
    
    print("=== Graph Structure ===")
    for i, neighbors in enumerate(graph):
        print(f"  Vertex {i}: {neighbors}")
    
    print("\n=== Component Counting ===")
    print(f"Number of components (DFS): {count_components_dfs(graph)}")
    print(f"Number of components (BFS): {count_components_bfs(graph)}")
    
    print("\n=== Component Labels ===")
    labels = label_components(graph)
    print("Vertex → Component ID:")
    for v, comp_id in sorted(labels.items()):
        print(f"  Vertex {v} → Component {comp_id}")
    
    print("\n=== Component Vertices ===")
    components = get_component_vertices(graph)
    for i, comp in enumerate(components):
        print(f"  Component {i}: {sorted(comp)}")
    
    print("\n=== Component Sizes ===")
    sizes = get_component_sizes(graph)
    print(f"Component sizes (descending): {sizes}")
    print(f"Largest component size: {largest_component_size(graph)}")
    
    print("\n=== Union-Find Approach ===")
    edges = [(0,1), (0,2), (1,3), (2,3), (4,5), (7,8)]
    uf_count = count_components_unionfind(9, edges)
    print(f"Components via Union-Find: {uf_count}")
    
    print("\n=== Connectivity Analysis ===")
    print(f"Is graph fully connected? {is_fully_connected(graph)}")
    print(f"Bridges needed to connect all: {bridges_to_connect_all(graph)}")



# ALGORITHM SELECTION GUIDE


def print_selection_guide():
    """When to use which algorithm"""
    print("\n" + "="*60)
    print("CONNECTED COMPONENTS - ALGORITHM SELECTION")
    print("="*60)
    
    print("\nDFS/BFS Approach:")
    print("  ✓ Graph already built as adjacency list")
    print("  ✓ Need to find actual components, not just count")
    print("  ✓ One-time analysis")
    print("  ✓ Time: O(V + E)")
    
    print("\nUnion-Find Approach:")
    print("  ✓ Graph given as edge list")
    print("  ✓ Building graph incrementally")
    print("  ✓ Need dynamic connectivity queries")
    print("  ✓ Kruskal's MST algorithm")
    print("  ✓ Time: O(E × α(V)) ≈ O(E)")
    
    print("\nDFS vs BFS:")
    print("  → Functionally equivalent for components")
    print("  → DFS: Simpler code (recursion)")
    print("  → BFS: Better for some applications (level-based)")


if __name__ == "__main__":
    test_connected_components()
    print_selection_guide()
```
---

## **8. Topological Sorting**

### **What is Topological Sort?**

A **topological sort** is a linear ordering of vertices in a **directed acyclic graph (DAG)** such that for every edge `u → v`, vertex `u` comes before `v` in the ordering.

**Intuition:** Imagine course prerequisites. You must take prerequisite courses before advanced courses. Topological sort gives you a valid course order.

**Critical Property:** Topological sort only exists for **DAGs** (Directed Acyclic Graphs). If graph has a cycle, no valid ordering exists.

**ASCII Visualization:**
```
DAG:
     0 → 1 → 3
     ↓   ↓
     2 → 4

Valid topological orderings:
  [0, 1, 2, 3, 4]
  [0, 1, 2, 4, 3]
  [0, 2, 1, 3, 4]
  [0, 2, 1, 4, 3]
  etc.

Key property: 0 comes before 1,2; 1 comes before 3,4; 2 comes before 4
```

### **Two Algorithms**

1. **DFS-based (Kahn's algorithm variant)**: Post-order DFS with reversal
2. **BFS-based (Kahn's algorithm)**: Remove vertices with in-degree 0


### TOPOLOGICAL SORTING

### Linear ordering of vertices in a DAG (Directed Acyclic Graph)

```python
from typing import List, Optional
from collections import deque
from enum import Enum


# METHOD 1: DFS-BASED


class Color(Enum):
    """3-color method for cycle detection during topological sort"""
    WHITE = 0  # Unvisited
    GRAY = 1   # Visiting (in current path)
    BLACK = 2  # Visited (completely processed)


def topological_sort_dfs(graph: List[List[int]]) -> Optional[List[int]]:
    """
    DFS-based topological sort
    
    Algorithm:
    1. Do DFS from each unvisited vertex
    2. Add vertex to result AFTER processing all descendants (post-order)
    3. Reverse result at end
    
    Key insight: Post-order DFS naturally gives reverse topological order
    
    Returns:
        Topological ordering, or None if graph has cycle
    
    Time: O(V + E)
    Space: O(V)
    """
    color = [Color.WHITE] * len(graph)
    result = []
    has_cycle = False
    
    def dfs(vertex: int) -> bool:
        """
        Returns True if cycle detected
        """
        color[vertex] = Color.GRAY
        
        for neighbor in graph[vertex]:
            if color[neighbor] == Color.GRAY:
                # Back edge to vertex in current path - CYCLE!
                return True
            
            if color[neighbor] == Color.WHITE:
                if dfs(neighbor):
                    return True
        
        color[vertex] = Color.BLACK
        result.append(vertex)  # Add in POST-ORDER
        return False
    
    # Process all vertices
    for v in range(len(graph)):
        if color[v] == Color.WHITE:
            if dfs(v):
                return None  # Cycle detected
    
    return result[::-1]  # Reverse to get topological order



# METHOD 2: BFS-BASED (Kahn's Algorithm)


def topological_sort_bfs(graph: List[List[int]]) -> Optional[List[int]]:
    """
    Kahn's Algorithm - BFS-based topological sort
    
    Algorithm:
    1. Calculate in-degree for all vertices
    2. Add all vertices with in-degree 0 to queue
    3. Process queue:
       - Remove vertex, add to result
       - Decrease in-degree of neighbors
       - If neighbor's in-degree becomes 0, add to queue
    4. If processed all vertices, return result; else cycle exists
    
    INTUITION: Always process vertices with no dependencies first
    
    Advantage: More intuitive for some problems
    Naturally detects cycles (if result.length < V)
    
    Time: O(V + E)
    Space: O(V)
    """
    n = len(graph)
    in_degree = [0] * n
    
    # Calculate in-degree for each vertex
    for vertex in range(n):
        for neighbor in graph[vertex]:
            in_degree[neighbor] += 1
    
    # Start with vertices having no dependencies (in-degree 0)
    queue = deque()
    for v in range(n):
        if in_degree[v] == 0:
            queue.append(v)
    
    result = []
    
    while queue:
        vertex = queue.popleft()
        result.append(vertex)
        
        # "Remove" this vertex by decreasing in-degree of neighbors
        for neighbor in graph[vertex]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    # If we processed all vertices, no cycle
    if len(result) == n:
        return result
    else:
        return None  # Cycle exists



# FIND ALL TOPOLOGICAL ORDERINGS


def all_topological_sorts(graph: List[List[int]]) -> List[List[int]]:
    """
    Find ALL possible topological orderings
    
    Uses backtracking with in-degree tracking
    
    Warning: Can be exponentially many orderings!
    Only use for small graphs
    
    Time: O(V! × E) in worst case
    """
    n = len(graph)
    in_degree = [0] * n
    
    # Calculate in-degrees
    for v in range(n):
        for neighbor in graph[v]:
            in_degree[neighbor] += 1
    
    def backtrack(current_order: List[int], remaining_in_degree: List[int]):
        # If we've ordered all vertices, save this ordering
        if len(current_order) == n:
            all_orderings.append(current_order[:])
            return
        
        # Try all vertices with in-degree 0
        for v in range(n):
            if v not in current_order and remaining_in_degree[v] == 0:
                # Choose this vertex
                current_order.append(v)
                
                # Update in-degrees
                temp_in_degree = remaining_in_degree[:]
                for neighbor in graph[v]:
                    temp_in_degree[neighbor] -= 1
                
                # Recurse
                backtrack(current_order, temp_in_degree)
                
                # Backtrack
                current_order.pop()
    
    all_orderings = []
    backtrack([], in_degree)
    return all_orderings



# APPLICATIONS


def can_finish_courses(num_courses: int, prerequisites: List[List[int]]) -> bool:
    """
    Classic LeetCode problem: Course Schedule
    
    Given prerequisites like [1, 0] meaning "course 1 requires course 0"
    Determine if all courses can be completed
    
    Solution: Check if topological sort exists (no cycle in dependency graph)
    """
    # Build graph
    graph = [[] for _ in range(num_courses)]
    for course, prereq in prerequisites:
        graph[prereq].append(course)  # prereq → course
    
    # If topological sort exists, courses can be completed
    return topological_sort_bfs(graph) is not None


def find_course_order(num_courses: int, prerequisites: List[List[int]]) -> List[int]:
    """
    Find valid order to take all courses
    
    Returns one valid ordering, or [] if impossible
    """
    graph = [[] for _ in range(num_courses)]
    for course, prereq in prerequisites:
        graph[prereq].append(course)
    
    result = topological_sort_bfs(graph)
    return result if result is not None else []


def compile_order(files: List[str], dependencies: List[List[str]]) -> List[str]:
    """
    Real-world application: Determine compilation order for source files
    
    dependencies: [fileA, fileB] means fileA depends on fileB
    """
    # Map file names to indices
    file_to_idx = {f: i for i, f in enumerate(files)}
    
    # Build graph
    graph = [[] for _ in range(len(files))]
    for file_a, file_b in dependencies:
        idx_a = file_to_idx[file_a]
        idx_b = file_to_idx[file_b]
        graph[idx_b].append(idx_a)  # file_b must come before file_a
    
    # Get topological order
    order_indices = topological_sort_bfs(graph)
    
    if order_indices is None:
        return []  # Circular dependency!
    
    return [files[i] for i in order_indices]



# TESTING & DEMONSTRATION


def test_topological_sort():
    """Test both algorithms"""
    
    print("=== Valid DAG ===")
    # DAG:
    #   0 → 1 → 3
    #   ↓   ↓
    #   2 → 4
    
    dag = [
        [1, 2],  # 0 → 1, 0 → 2
        [3, 4],  # 1 → 3, 1 → 4
        [4],     # 2 → 4
        [],      # 3
        []       # 4
    ]
    
    print("Graph adjacency list:")
    for i, neighbors in enumerate(dag):
        if neighbors:
            print(f"  {i} → {neighbors}")
    
    dfs_order = topological_sort_dfs(dag)
    bfs_order = topological_sort_bfs(dag)
    
    print(f"\nDFS-based order: {dfs_order}")
    print(f"BFS-based order: {bfs_order}")
    
    # Verify both are valid
    def is_valid_topo_order(graph, order):
        position = {v: i for i, v in enumerate(order)}
        for u in range(len(graph)):
            for v in graph[u]:
                if position[u] >= position[v]:
                    return False
        return True
    
    print(f"DFS order valid? {is_valid_topo_order(dag, dfs_order)}")
    print(f"BFS order valid? {is_valid_topo_order(dag, bfs_order)}")
    
    print("\n=== Graph with Cycle ===")
    # Graph with cycle: 0 → 1 → 2 → 0
    cyclic = [
        [1],  # 0 → 1
        [2],  # 1 → 2
        [0]   # 2 → 0 (creates cycle!)
    ]
    
    dfs_result = topological_sort_dfs(cyclic)
    bfs_result = topological_sort_bfs(cyclic)
    
    print(f"DFS result (should be None): {dfs_result}")
    print(f"BFS result (should be None): {bfs_result}")
    
    print("\n=== All Topological Orderings ===")
    small_dag = [
        [1, 2],  # 0 → 1, 0 → 2
        [3],     # 1 → 3
        [3],     # 2 → 3
        []       # 3
    ]
    
    all_orders = all_topological_sorts(small_dag)
    print(f"Found {len(all_orders)} valid orderings:")
    for i, order in enumerate(all_orders, 1):
        print(f"  {i}. {order}")
    
    print("\n=== Course Schedule Problem ===")
    prerequisites = [[1, 0], [2, 0], [3, 1], [3, 2]]
    can_finish = can_finish_courses(4, prerequisites)
    print(f"Prerequisites: {prerequisites}")
    print(f"Can finish all courses? {can_finish}")
    
    if can_finish:
        order = find_course_order(4, prerequisites)
        print(f"One valid course order: {order}")



# ALGORITHM COMPARISON

def print_algorithm_comparison():
    """Compare DFS vs BFS approaches"""
    print("\n" + "="*60)
    print("TOPOLOGICAL SORT - ALGORITHM COMPARISON")
    print("="*60)
    
    print("\nDFS-Based (Post-order with reversal):")
    print("  ✓ More elegant recursive code")
    print("  ✓ Natural for some problems")
    print("  ✓ Can find cycle during sorting")
    print("  ✓ Time: O(V + E), Space: O(V)")
    
    print("\nBFS-Based (Kahn's Algorithm):")
    print("  ✓ More intuitive (process nodes with no dependencies)")
    print("  ✓ Easier to understand for beginners")
    print("  ✓ Natural cycle detection (count processed vertices)")
    print("  ✓ Easier to extend (e.g., parallel task scheduling)")
    print("  ✓ Time: O(V + E), Space: O(V)")
    
    print("\nBoth algorithms:")
    print("  → Same time complexity O(V + E)")
    print("  → Detect cycles")
    print("  → May produce different valid orderings")
    print("  → Choose based on problem context and preference")


if __name__ == "__main__":
    test_topological_sort()
    print_algorithm_comparison()

```
---

## **9. Bipartite Graphs**

### **What is a Bipartite Graph?**

A graph is **bipartite** if its vertices can be divided into two disjoint sets such that every edge connects vertices from different sets.

**Intuition:** Think of it as a matching problem - like matching students to projects, where no two students share a project, and no two projects share a student.

**Theorem:** A graph is bipartite **if and only if** it contains **no odd-length cycles**.

**ASCII Visualization:**
```
BIPARTITE:              NOT BIPARTITE:
Set A    Set B          
  1  ----  2              1 --- 2
  |   \/   |              |     |
  |   /\   |              |     |
  3  ----  4              3 --- 4
                           \   /
Valid 2-coloring           \ /
(alternate colors)          5

                        (odd cycle: 1-2-4-5-3-1)
```


## BIPARTITE GRAPHS

### Detecting and working with 2-colorable graphs

```python
from typing import List, Optional, Dict, Tuple
from collections import deque


# BIPARTITE DETECTION


def is_bipartite_bfs(graph: List[List[int]]) -> bool:
    """
    Check if graph is bipartite using BFS with 2-coloring
    
    Algorithm:
    1. Try to color graph with 2 colors (0 and 1)
    2. Start BFS from uncolored vertices
    3. Color each vertex with opposite color of its parent
    4. If we encounter a vertex with same color as current → NOT bipartite
    
    Key insight: Bipartite ⟺ Can 2-color the graph
    
    Time: O(V + E)
    Space: O(V)
    """
    n = len(graph)
    color = [-1] * n  # -1 means uncolored
    
    # Graph might be disconnected, check all components
    for start in range(n):
        if color[start] == -1:
            # BFS to color this component
            queue = deque([start])
            color[start] = 0  # Start with color 0
            
            while queue:
                vertex = queue.popleft()
                
                for neighbor in graph[vertex]:
                    if color[neighbor] == -1:
                        # Color with opposite color
                        color[neighbor] = 1 - color[vertex]
                        queue.append(neighbor)
                    elif color[neighbor] == color[vertex]:
                        # Conflict! Same color for adjacent vertices
                        return False
    
    return True


def is_bipartite_dfs(graph: List[List[int]]) -> bool:
    """
    Check if graph is bipartite using DFS with 2-coloring
    
    Recursive DFS approach - often cleaner than BFS for this problem
    """
    n = len(graph)
    color = [-1] * n
    
    def dfs(vertex: int, c: int) -> bool:
        """
        Color vertex with color c and recursively color neighbors
        Returns False if conflict found
        """
        color[vertex] = c
        
        for neighbor in graph[vertex]:
            if color[neighbor] == -1:
                # Recursively color with opposite color
                if not dfs(neighbor, 1 - c):
                    return False
            elif color[neighbor] == c:
                # Conflict!
                return False
        
        return True
    
    # Check all components
    for v in range(n):
        if color[v] == -1:
            if not dfs(v, 0):
                return False
    
    return True


# ===========================
# GET BIPARTITE SETS
# ===========================

def get_bipartite_sets(graph: List[List[int]]) -> Optional[Tuple[List[int], List[int]]]:
    """
    If graph is bipartite, return the two sets
    
    Returns:
        (set_a, set_b) where all edges go between sets, or None if not bipartite
    """
    n = len(graph)
    color = [-1] * n
    
    def bfs(start: int) -> bool:
        queue = deque([start])
        color[start] = 0
        
        while queue:
            vertex = queue.popleft()
            
            for neighbor in graph[vertex]:
                if color[neighbor] == -1:
                    color[neighbor] = 1 - color[vertex]
                    queue.append(neighbor)
                elif color[neighbor] == color[vertex]:
                    return False
        
        return True
    
    # Color all components
    for v in range(n):
        if color[v] == -1:
            if not bfs(v):
                return None  # Not bipartite
    
    # Separate into two sets
    set_a = [v for v in range(n) if color[v] == 0]
    set_b = [v for v in range(n) if color[v] == 1]
    
    return (set_a, set_b)


# ===========================
# ODD CYCLE DETECTION
# ===========================

def find_odd_cycle(graph: List[List[int]]) -> Optional[List[int]]:
    """
    Find an odd-length cycle in the graph
    
    Theorem: Graph is NOT bipartite ⟺ contains odd-length cycle
    
    Returns:
        List of vertices forming odd cycle, or None if bipartite
    """
    n = len(graph)
    color = [-1] * n
    parent = [-1] * n
    
    def bfs(start: int) -> Optional[List[int]]:
        queue = deque([start])
        color[start] = 0
        
        while queue:
            vertex = queue.popleft()
            
            for neighbor in graph[vertex]:
                if color[neighbor] == -1:
                    color[neighbor] = 1 - color[vertex]
                    parent[neighbor] = vertex
                    queue.append(neighbor)
                elif color[neighbor] == color[vertex]:
                    # Found odd cycle! Reconstruct it
                    cycle = [vertex]
                    
                    # Trace back from neighbor
                    curr = neighbor
                    while curr != vertex:
                        cycle.append(curr)
                        # Find common ancestor
                        # (In simple case, go back to parent)
                        if parent[curr] != -1:
                            curr = parent[curr]
                        else:
                            break
                    
                    return cycle
        
        return None
    
    for v in range(n):
        if color[v] == -1:
            cycle = bfs(v)
            if cycle:
                return cycle
    
    return None  # No odd cycle (bipartite)


# ===========================
# APPLICATIONS
# ===========================

def can_assign_tasks(num_people: int, conflicts: List[List[int]]) -> bool:
    """
    Task assignment problem
    
    Can assign tasks to num_people people such that conflicting tasks
    are assigned to different people?
    
    conflicts: pairs of task indices that can't be assigned to same person
    
    Solution: Build conflict graph, check if bipartite
    If bipartite, can assign tasks to 2 groups
    """
    # Build conflict graph
    graph = [[] for _ in range(len(conflicts))]
    conflict_set = set()
    
    for a, b in conflicts:
        if (a, b) not in conflict_set:
            graph[a].append(b)
            graph[b].append(a)
            conflict_set.add((a, b))
            conflict_set.add((b, a))
    
    return is_bipartite_bfs(graph)


def possible_bipartition(n: int, dislikes: List[List[int]]) -> bool:
    """
    LeetCode 886: Possible Bipartition
    
    Given n people and list of pairs who dislike each other,
    can we split them into 2 groups where no one dislikes anyone in their group?
    
    Solution: Build dislike graph, check if bipartite
    """
    # Build graph (1-indexed in problem, convert to 0-indexed)
    graph = [[] for _ in range(n)]
    
    for a, b in dislikes:
        graph[a - 1].append(b - 1)
        graph[b - 1].append(a - 1)
    
    return is_bipartite_dfs(graph)


# ===========================
# SPECIAL PATTERNS
# ===========================

def is_tree_bipartite(graph: List[List[int]]) -> bool:
    """
    Special case: All trees are bipartite!
    
    Proof: Trees have no cycles, thus no odd cycles
    
    This is just for demonstration - in practice, just return True for trees
    """
    # Trees are always bipartite
    # But let's verify using our algorithm
    return is_bipartite_bfs(graph)


def bipartite_matching_possible(graph: List[List[int]]) -> bool:
    """
    Check if perfect matching is possible in bipartite graph
    
    This is a placeholder - actual maximum bipartite matching
    requires more complex algorithms (Hungarian, Hopcroft-Karp)
    """
    # First check if bipartite
    if not is_bipartite_bfs(graph):
        return False
    
    # For perfect matching, need |set_a| = |set_b|
    sets = get_bipartite_sets(graph)
    if sets is None:
        return False
    
    set_a, set_b = sets
    return len(set_a) == len(set_b)


# ===========================
# TESTING & DEMONSTRATION
# ===========================

def test_bipartite():
    """Test bipartite detection"""
    
    print("=== BIPARTITE GRAPH ===")
    # Bipartite graph:
    #   0 --- 1
    #   |     |
    #   2 --- 3
    
    bipartite = [
        [1, 2],  # 0
        [0, 3],  # 1
        [0, 3],  # 2
        [1, 2]   # 3
    ]
    
    print("Graph edges:")
    for i, neighbors in enumerate(bipartite):
        print(f"  {i}: {neighbors}")
    
    print(f"\nIs bipartite (BFS)? {is_bipartite_bfs(bipartite)}")
    print(f"Is bipartite (DFS)? {is_bipartite_dfs(bipartite)}")
    
    sets = get_bipartite_sets(bipartite)
    if sets:
        set_a, set_b = sets
        print(f"Set A: {set_a}")
        print(f"Set B: {set_b}")
    
    print("\n=== NON-BIPARTITE GRAPH (has odd cycle) ===")
    # Triangle (odd cycle):
    #   0 --- 1
    #    \   /
    #      2
    
    non_bipartite = [
        [1, 2],  # 0
        [0, 2],  # 1
        [0, 1]   # 2
    ]
    
    print("Graph edges:")
    for i, neighbors in enumerate(non_bipartite):
        print(f"  {i}: {neighbors}")
    
    print(f"\nIs bipartite (BFS)? {is_bipartite_bfs(non_bipartite)}")
    print(f"Is bipartite (DFS)? {is_bipartite_dfs(non_bipartite)}")
    
    odd_cycle = find_odd_cycle(non_bipartite)
    if odd_cycle:
        print(f"Odd cycle found: {odd_cycle}")
    
    print("\n=== DISCONNECTED GRAPH ===")
    # Two components, both bipartite:
    #   0 --- 1    2 --- 3
    
    disconnected = [
        [1],     # 0
        [0],     # 1
        [3],     # 2
        [2]      # 3
    ]
    
    print(f"Is bipartite? {is_bipartite_bfs(disconnected)}")
    
    sets = get_bipartite_sets(disconnected)
    if sets:
        set_a, set_b = sets
        print(f"Set A: {set_a}")
        print(f"Set B: {set_b}")


# ===========================
# KEY INSIGHTS
# ===========================

def print_key_insights():
    """Important theorems and insights"""
    print("\n" + "="*60)
    print("BIPARTITE GRAPHS - KEY INSIGHTS")
    print("="*60)
    
    print("\nDefinition:")
    print("  Graph where vertices can be split into 2 disjoint sets")
    print("  such that all edges connect vertices from different sets")
    
    print("\nEquivalent Conditions (all mean the same thing):")
    print("  1. Graph is bipartite")
    print("  2. Graph is 2-colorable")
    print("  3. Graph contains NO odd-length cycles")
    
    print("\nDetection Algorithm:")
    print("  • Use BFS or DFS with 2-coloring")
    print("  • Time: O(V + E)")
    print("  • Space: O(V)")
    
    print("\nSpecial Cases:")
    print("  • ALL TREES are bipartite (no cycles)")
    print("  • Even-length cycles are bipartite")
    print("  • Odd-length cycles are NOT bipartite")
    
    print("\nApplications:")
    print("  • Task assignment with conflicts")
    print("  • Graph coloring problems")
    print("  • Matching problems")
    print("  • Social network analysis")


if __name__ == "__main__":
    test_bipartite()
    print_key_insights()
```
---

## **10. Advanced Patterns & Problem-Solving**

### **10.1 Graph Problem Recognition Patterns**

**Decision Tree for Problem Selection:**

```
                    Graph Problem?
                          │
         ┌────────────────┼────────────────┐
         │                                  │
    Shortest Path?                    Structural Analysis?
         │                                  │
    ┌────┴────┐                    ┌────────┴────────┐
  Weighted  Unweighted         Cycles?  Components?  Order?
    │           │                  │         │         │
  Dijkstra    BFS              DFS/Color   DFS/BFS  Topological
```

### **10.2 Common Problem Patterns**


## ADVANCED GRAPH PATTERNS & PROBLEM-SOLVING TECHNIQUES
### Master these patterns to solve 90%+ of graph problems

```python
from typing import List, Set, Dict, Tuple
from collections import deque, defaultdict


# PATTERN 1: Grid as Graph (Implicit Graph)


def grid_bfs_template(grid: List[List[int]], start_row: int, start_col: int) -> int:
    """
    CRITICAL PATTERN: Treating 2D grid as implicit graph
    
    Each cell is a vertex
    Adjacent cells (up/down/left/right) are connected
    
    Used in: Islands, rotting oranges, walls and gates, etc.
    
    Time: O(rows × cols)
    Space: O(rows × cols)
    """
    rows, cols = len(grid), len(grid[0])
    visited = set([(start_row, start_col)])
    queue = deque([(start_row, start_col, 0)])  # (row, col, distance)
    
    # 4 directions: up, down, left, right
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    max_distance = 0
    
    while queue:
        row, col, dist = queue.popleft()
        max_distance = max(max_distance, dist)
        
        # Explore all 4 neighbors
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            
            # Check bounds and visited
            if (0 <= new_row < rows and 
                0 <= new_col < cols and 
                (new_row, new_col) not in visited and
                grid[new_row][new_col] != -1):  # Example: -1 = obstacle
                
                visited.add((new_row, new_col))
                queue.append((new_row, new_col, dist + 1))
    
    return max_distance


def count_islands_dfs(grid: List[List[str]]) -> int:
    """
    LeetCode 200: Number of Islands
    
    Pattern: Connected components in implicit graph (grid)
    
    '1' = land, '0' = water
    Count number of islands (connected components of land)
    """
    if not grid:
        return 0
    
    rows, cols = len(grid), len(grid[0])
    visited = set()
    count = 0
    
    def dfs(r: int, c: int):
        # Mark this cell as visited
        visited.add((r, c))
        
        # Explore 4 directions
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if (0 <= nr < rows and 
                0 <= nc < cols and 
                (nr, nc) not in visited and 
                grid[nr][nc] == '1'):
                dfs(nr, nc)
    
    # Find all islands
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == '1' and (r, c) not in visited:
                count += 1
                dfs(r, c)
    
    return count



# PATTERN 2: Multi-Source BFS


def walls_and_gates(rooms: List[List[int]]) -> None:
    """
    LeetCode 286: Walls and Gates
    
    Pattern: Multi-source BFS
    
    Given grid:
    - INF (2^31 - 1) = empty room
    - 0 = gate
    - -1 = wall
    
    Fill each room with distance to nearest gate
    """
    if not rooms:
        return
    
    INF = 2147483647
    rows, cols = len(rooms), len(rooms[0])
    queue = deque()
    
    # Start BFS from ALL gates simultaneously
    for r in range(rows):
        for c in range(cols):
            if rooms[r][c] == 0:
                queue.append((r, c))
    
    # BFS from all gates
    while queue:
        r, c = queue.popleft()
        
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            
            if (0 <= nr < rows and 
                0 <= nc < cols and 
                rooms[nr][nc] == INF):
                # Update distance
                rooms[nr][nc] = rooms[r][c] + 1
                queue.append((nr, nc))


def oranges_rotting(grid: List[List[int]]) -> int:
    """
    LeetCode 994: Rotting Oranges
    
    Pattern: Multi-source BFS with timestamp
    
    0 = empty, 1 = fresh orange, 2 = rotten orange
    Each minute, rotten oranges rot adjacent fresh oranges
    Return minutes until all oranges rot, or -1 if impossible
    """
    rows, cols = len(grid), len(grid[0])
    queue = deque()
    fresh_count = 0
    
    # Find all initial rotten oranges and count fresh
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 2:
                queue.append((r, c, 0))  # (row, col, time)
            elif grid[r][c] == 1:
                fresh_count += 1
    
    max_time = 0
    
    while queue:
        r, c, time = queue.popleft()
        max_time = max(max_time, time)
        
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            
            if (0 <= nr < rows and 
                0 <= nc < cols and 
                grid[nr][nc] == 1):
                # Rot this orange
                grid[nr][nc] = 2
                fresh_count -= 1
                queue.append((nr, nc, time + 1))
    
    return max_time if fresh_count == 0 else -1



# PATTERN 3: Clone/Copy Graph


class Node:
    def __init__(self, val: int = 0, neighbors: List['Node'] = None):
        self.val = val
        self.neighbors = neighbors if neighbors else []


def clone_graph(node: Node) -> Node:
    """
    LeetCode 133: Clone Graph
    
    Pattern: Deep copy with mapping
    
    Create deep copy of graph, preserving structure
    Key: Use dict to map old nodes → new nodes
    """
    if not node:
        return None
    
    # Map old node → new node
    old_to_new = {}
    
    def dfs(node: Node) -> Node:
        if node in old_to_new:
            return old_to_new[node]
        
        # Create new node
        copy = Node(node.val)
        old_to_new[node] = copy
        
        # Clone neighbors
        for neighbor in node.neighbors:
            copy.neighbors.append(dfs(neighbor))
        
        return copy
    
    return dfs(node)



# PATTERN 4: Building Graph from Equations


def calc_equation(equations: List[List[str]], values: List[float],
                  queries: List[List[str]]) -> List[float]:
    """
    LeetCode 399: Evaluate Division
    
    Pattern: Build weighted graph from relationships
    
    Given equations like a/b = 2.0, build graph:
    a → b with weight 2.0
    b → a with weight 0.5
    
    Query: a/c = ? → Find path from a to c, multiply edge weights
    """
    # Build graph
    graph = defaultdict(dict)
    
    for (a, b), value in zip(equations, values):
        graph[a][b] = value
        graph[b][a] = 1.0 / value
    
    def dfs(start: str, end: str, visited: Set[str]) -> float:
        # Base cases
        if start not in graph or end not in graph:
            return -1.0
        if start == end:
            return 1.0
        
        visited.add(start)
        
        for neighbor, weight in graph[start].items():
            if neighbor not in visited:
                result = dfs(neighbor, end, visited)
                if result != -1.0:
                    return weight * result
        
        return -1.0
    
    # Answer queries
    results = []
    for a, b in queries:
        results.append(dfs(a, b, set()))
    
    return results



# PATTERN 5: Word Ladder / Transformation


def ladder_length(begin_word: str, end_word: str, word_list: List[str]) -> int:
    """
    LeetCode 127: Word Ladder
    
    Pattern: BFS on implicit graph where edges = 1-letter transformations
    
    Find shortest transformation sequence from begin_word to end_word
    """
    word_set = set(word_list)
    if end_word not in word_set:
        return 0
    
    queue = deque([(begin_word, 1)])  # (word, length)
    visited = {begin_word}
    
    while queue:
        word, length = queue.popleft()
        
        if word == end_word:
            return length
        
        # Try all possible 1-letter transformations
        for i in range(len(word)):
            for c in 'abcdefghijklmnopqrstuvwxyz':
                next_word = word[:i] + c + word[i+1:]
                
                if next_word in word_set and next_word not in visited:
                    visited.add(next_word)
                    queue.append((next_word, length + 1))
    
    return 0



# PATTERN 6: Course Schedule (Cycle Detection + Topological Sort)


def find_order(num_courses: int, prerequisites: List[List[int]]) -> List[int]:
    """
    LeetCode 210: Course Schedule II
    
    Pattern: Topological sort with Kahn's algorithm
    
    Return any valid course order, or [] if impossible (cycle exists)
    """
    # Build graph
    graph = [[] for _ in range(num_courses)]
    in_degree = [0] * num_courses
    
    for course, prereq in prerequisites:
        graph[prereq].append(course)
        in_degree[course] += 1
    
    # Kahn's algorithm
    queue = deque([i for i in range(num_courses) if in_degree[i] == 0])
    order = []
    
    while queue:
        course = queue.popleft()
        order.append(course)
        
        for next_course in graph[course]:
            in_degree[next_course] -= 1
            if in_degree[next_course] == 0:
                queue.append(next_course)
    
    return order if len(order) == num_courses else []



# PATTERN 7: Undirected Graph Cycle (Union-Find)


def valid_tree(n: int, edges: List[List[int]]) -> bool:
    """
    LeetCode 261: Graph Valid Tree
    
    Pattern: Tree validation (connected + acyclic)
    
    A graph is a tree if:
    1. It's connected (1 component)
    2. It's acyclic (no cycles)
    3. Has exactly n-1 edges (tree property)
    """
    # Tree must have exactly n-1 edges
    if len(edges) != n - 1:
        return False
    
    # Build graph
    graph = [[] for _ in range(n)]
    for a, b in edges:
        graph[a].append(b)
        graph[b].append(a)
    
    # Check if connected using BFS
    visited = set([0])
    queue = deque([0])
    
    while queue:
        node = queue.popleft()
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    
    return len(visited) == n



# TESTING PATTERNS


def test_patterns():
    """Test various patterns"""
    
    print("=== GRID AS GRAPH (Islands) ===")
    grid = [
        ['1', '1', '0', '0', '0'],
        ['1', '1', '0', '0', '0'],
        ['0', '0', '1', '0', '0'],
        ['0', '0', '0', '1', '1']
    ]
    print(f"Number of islands: {count_islands_dfs(grid)}")
    
    print("\n=== MULTI-SOURCE BFS (Rotting Oranges) ===")
    oranges = [
        [2, 1, 1],
        [1, 1, 0],
        [0, 1, 1]
    ]
    print(f"Minutes to rot all oranges: {oranges_rotting(oranges)}")
    
    print("\n=== GRAPH FROM EQUATIONS ===")
    equations = [["a", "b"], ["b", "c"]]
    values = [2.0, 3.0]
    queries = [["a", "c"], ["b", "a"], ["a", "e"]]
    results = calc_equation(equations, values, queries)
    print(f"Division results: {results}")
    
    print("\n=== COURSE SCHEDULE (Topological Sort) ===")
    order = find_order(4, [[1,0], [2,0], [3,1], [3,2]])
    print(f"Course order: {order}")


if __name__ == "__main__":
    test_patterns()
```
---

## **11. Implementation Guide: Rust, Python, Go**

Now let's see idiomatic implementations across your preferred languages:

```rust

use std::collections::{VecDeque, HashSet, HashMap};

// ===========================
// GRAPH REPRESENTATION
// ===========================

/// Adjacency list graph - most common representation
/// 
/// Using Vec<Vec<usize>> for maximum performance
/// - Indexing is O(1)
/// - Cache-friendly
/// - No heap allocations for lookups
#[derive(Debug, Clone)]
pub struct Graph {
    adj: Vec<Vec<usize>>,
}

impl Graph {
    /// Create new graph with `n` vertices
    pub fn new(n: usize) -> Self {
        Self {
            adj: vec![Vec::new(); n],
        }
    }

    /// Add directed edge from u to v
    pub fn add_edge(&mut self, u: usize, v: usize) {
        self.adj[u].push(v);
    }

    /// Add undirected edge between u and v
    pub fn add_undirected_edge(&mut self, u: usize, v: usize) {
        self.adj[u].push(v);
        self.adj[v].push(u);
    }

    /// Get neighbors of vertex v
    pub fn neighbors(&self, v: usize) -> &[usize] {
        &self.adj[v]
    }

    /// Number of vertices
    pub fn size(&self) -> usize {
        self.adj.len()
    }
}

// ===========================
// BFS IMPLEMENTATION
// ===========================

/// BFS traversal starting from `start`
/// 
/// Returns vertices in BFS order
/// 
/// Time: O(V + E)
/// Space: O(V)
pub fn bfs(graph: &Graph, start: usize) -> Vec<usize> {
    let mut visited = HashSet::new();
    let mut queue = VecDeque::new();
    let mut result = Vec::new();

    queue.push_back(start);
    visited.insert(start);

    while let Some(vertex) = queue.pop_front() {
        result.push(vertex);

        for &neighbor in graph.neighbors(vertex) {
            if visited.insert(neighbor) {  // Returns false if already present
                queue.push_back(neighbor);
            }
        }
    }

    result
}

/// BFS shortest path from start to end
/// 
/// Returns (distance, path) or None if no path exists
pub fn bfs_shortest_path(
    graph: &Graph,
    start: usize,
    end: usize,
) -> Option<(usize, Vec<usize>)> {
    if start == end {
        return Some((0, vec![start]));
    }

    let mut visited = HashSet::new();
    let mut queue = VecDeque::new();
    let mut parent = vec![None; graph.size()];

    queue.push_back(start);
    visited.insert(start);

    while let Some(vertex) = queue.pop_front() {
        for &neighbor in graph.neighbors(vertex) {
            if visited.insert(neighbor) {
                parent[neighbor] = Some(vertex);
                queue.push_back(neighbor);

                if neighbor == end {
                    // Reconstruct path
                    let mut path = Vec::new();
                    let mut current = Some(end);

                    while let Some(v) = current {
                        path.push(v);
                        current = parent[v];
                    }

                    path.reverse();
                    return Some((path.len() - 1, path));
                }
            }
        }
    }

    None
}

// ===========================
// DFS IMPLEMENTATION
// ===========================

/// DFS traversal (recursive)
/// 
/// Returns vertices in DFS order
pub fn dfs(graph: &Graph, start: usize) -> Vec<usize> {
    let mut visited = HashSet::new();
    let mut result = Vec::new();

    fn dfs_helper(
        graph: &Graph,
        vertex: usize,
        visited: &mut HashSet<usize>,
        result: &mut Vec<usize>,
    ) {
        visited.insert(vertex);
        result.push(vertex);

        for &neighbor in graph.neighbors(vertex) {
            if !visited.contains(&neighbor) {
                dfs_helper(graph, neighbor, visited, result);
            }
        }
    }

    dfs_helper(graph, start, &mut visited, &mut result);
    result
}

/// DFS iterative using explicit stack
pub fn dfs_iterative(graph: &Graph, start: usize) -> Vec<usize> {
    let mut visited = HashSet::new();
    let mut stack = vec![start];
    let mut result = Vec::new();

    while let Some(vertex) = stack.pop() {
        if visited.insert(vertex) {
            result.push(vertex);

            // Push neighbors in reverse for consistent ordering
            for &neighbor in graph.neighbors(vertex).iter().rev() {
                if !visited.contains(&neighbor) {
                    stack.push(neighbor);
                }
            }
        }
    }

    result
}

// ===========================
// CYCLE DETECTION
// ===========================

#[derive(Clone, Copy, PartialEq, Eq)]
enum Color {
    White,  // Unvisited
    Gray,   // Visiting
    Black,  // Visited
}

/// Detect cycle in directed graph
/// 
/// Uses 3-color DFS algorithm
pub fn has_cycle_directed(graph: &Graph) -> bool {
    let n = graph.size();
    let mut color = vec![Color::White; n];

    fn dfs(
        graph: &Graph,
        vertex: usize,
        color: &mut [Color],
    ) -> bool {
        color[vertex] = Color::Gray;

        for &neighbor in graph.neighbors(vertex) {
            match color[neighbor] {
                Color::Gray => return true,  // Back edge - cycle!
                Color::White => {
                    if dfs(graph, neighbor, color) {
                        return true;
                    }
                }
                Color::Black => {}
            }
        }

        color[vertex] = Color::Black;
        false
    }

    for v in 0..n {
        if color[v] == Color::White {
            if dfs(graph, v, &mut color) {
                return true;
            }
        }
    }

    false
}

// ===========================
// TOPOLOGICAL SORT
// ===========================

/// Topological sort using Kahn's algorithm (BFS-based)
/// 
/// Returns topological ordering or None if cycle exists
pub fn topological_sort(graph: &Graph) -> Option<Vec<usize>> {
    let n = graph.size();
    let mut in_degree = vec![0; n];

    // Calculate in-degrees
    for v in 0..n {
        for &neighbor in graph.neighbors(v) {
            in_degree[neighbor] += 1;
        }
    }

    // Start with vertices having in-degree 0
    let mut queue: VecDeque<usize> = (0..n)
        .filter(|&v| in_degree[v] == 0)
        .collect();

    let mut result = Vec::with_capacity(n);

    while let Some(vertex) = queue.pop_front() {
        result.push(vertex);

        for &neighbor in graph.neighbors(vertex) {
            in_degree[neighbor] -= 1;
            if in_degree[neighbor] == 0 {
                queue.push_back(neighbor);
            }
        }
    }

    if result.len() == n {
        Some(result)
    } else {
        None  // Cycle exists
    }
}

// ===========================
// CONNECTED COMPONENTS
// ===========================

/// Count number of connected components
pub fn count_components(graph: &Graph) -> usize {
    let n = graph.size();
    let mut visited = vec![false; n];
    let mut count = 0;

    fn dfs(graph: &Graph, vertex: usize, visited: &mut [bool]) {
        visited[vertex] = true;

        for &neighbor in graph.neighbors(vertex) {
            if !visited[neighbor] {
                dfs(graph, neighbor, visited);
            }
        }
    }

    for v in 0..n {
        if !visited[v] {
            count += 1;
            dfs(graph, v, &mut visited);
        }
    }

    count
}

// ===========================
// UNION-FIND (Disjoint Set Union)
// ===========================

/// Efficient Union-Find with path compression and union by rank
pub struct UnionFind {
    parent: Vec<usize>,
    rank: Vec<usize>,
    components: usize,
}

impl UnionFind {
    /// Create new Union-Find with `n` elements
    pub fn new(n: usize) -> Self {
        Self {
            parent: (0..n).collect(),
            rank: vec![0; n],
            components: n,
        }
    }

    /// Find root with path compression
    pub fn find(&mut self, x: usize) -> usize {
        if self.parent[x] != x {
            self.parent[x] = self.find(self.parent[x]);  // Path compression
        }
        self.parent[x]
    }

    /// Union two sets, return true if they were separate
    pub fn union(&mut self, x: usize, y: usize) -> bool {
        let root_x = self.find(x);
        let root_y = self.find(y);

        if root_x == root_y {
            return false;  // Already in same set
        }

        // Union by rank
        match self.rank[root_x].cmp(&self.rank[root_y]) {
            std::cmp::Ordering::Less => {
                self.parent[root_x] = root_y;
            }
            std::cmp::Ordering::Greater => {
                self.parent[root_y] = root_x;
            }
            std::cmp::Ordering::Equal => {
                self.parent[root_y] = root_x;
                self.rank[root_x] += 1;
            }
        }

        self.components -= 1;
        true
    }

    /// Check if two elements are in same set
    pub fn connected(&mut self, x: usize, y: usize) -> bool {
        self.find(x) == self.find(y)
    }

    /// Get number of components
    pub fn count_components(&self) -> usize {
        self.components
    }
}

// ===========================
// TESTING
// ===========================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_bfs() {
        let mut graph = Graph::new(6);
        graph.add_edge(0, 1);
        graph.add_edge(0, 2);
        graph.add_edge(1, 3);
        graph.add_edge(1, 4);
        graph.add_edge(2, 5);

        let result = bfs(&graph, 0);
        assert_eq!(result.len(), 6);
        assert_eq!(result[0], 0);  // Start node
    }

    #[test]
    fn test_shortest_path() {
        let mut graph = Graph::new(6);
        graph.add_edge(0, 1);
        graph.add_edge(0, 2);
        graph.add_edge(1, 3);
        graph.add_edge(2, 3);
        graph.add_edge(3, 4);
        graph.add_edge(4, 5);

        let result = bfs_shortest_path(&graph, 0, 5);
        assert!(result.is_some());
        
        let (dist, path) = result.unwrap();
        assert_eq!(dist, 4);
        assert_eq!(path[0], 0);
        assert_eq!(path[path.len() - 1], 5);
    }

    #[test]
    fn test_cycle_detection() {
        let mut dag = Graph::new(4);
        dag.add_edge(0, 1);
        dag.add_edge(0, 2);
        dag.add_edge(1, 3);
        dag.add_edge(2, 3);

        assert!(!has_cycle_directed(&dag));

        let mut cyclic = Graph::new(3);
        cyclic.add_edge(0, 1);
        cyclic.add_edge(1, 2);
        cyclic.add_edge(2, 0);

        assert!(has_cycle_directed(&cyclic));
    }

    #[test]
    fn test_topological_sort() {
        let mut graph = Graph::new(4);
        graph.add_edge(0, 1);
        graph.add_edge(0, 2);
        graph.add_edge(1, 3);
        graph.add_edge(2, 3);

        let result = topological_sort(&graph);
        assert!(result.is_some());
        
        let order = result.unwrap();
        assert_eq!(order.len(), 4);
        
        // 0 should come before 1 and 2
        let pos = order.iter().position(|&v| v == 0).unwrap();
        assert!(pos < order.iter().position(|&v| v == 1).unwrap());
        assert!(pos < order.iter().position(|&v| v == 2).unwrap());
    }
}

fn main() {
    println!("Rust Graph Implementation");
    println!("Run with: cargo test");
}
```

```golang

package main

import (
	"container/list"
	"fmt"
)

// ===========================
// GRAPH REPRESENTATION
// ===========================

// Graph represents an adjacency list graph
type Graph struct {
	vertices int
	adj      [][]int
}

// NewGraph creates a new graph with n vertices
func NewGraph(n int) *Graph {
	return &Graph{
		vertices: n,
		adj:      make([][]int, n),
	}
}

// AddEdge adds a directed edge from u to v
func (g *Graph) AddEdge(u, v int) {
	g.adj[u] = append(g.adj[u], v)
}

// AddUndirectedEdge adds an undirected edge between u and v
func (g *Graph) AddUndirectedEdge(u, v int) {
	g.adj[u] = append(g.adj[u], v)
	g.adj[v] = append(g.adj[v], u)
}

// Neighbors returns neighbors of vertex v
func (g *Graph) Neighbors(v int) []int {
	return g.adj[v]
}

// Size returns number of vertices
func (g *Graph) Size() int {
	return g.vertices
}

// ===========================
// BFS IMPLEMENTATION
// ===========================

// BFS performs breadth-first search from start vertex
// Returns vertices in BFS order
//
// Time: O(V + E)
// Space: O(V)
func (g *Graph) BFS(start int) []int {
	visited := make(map[int]bool)
	queue := list.New()
	result := []int{}

	queue.PushBack(start)
	visited[start] = true

	for queue.Len() > 0 {
		element := queue.Front()
		vertex := element.Value.(int)
		queue.Remove(element)

		result = append(result, vertex)

		for _, neighbor := range g.adj[vertex] {
			if !visited[neighbor] {
				visited[neighbor] = true
				queue.PushBack(neighbor)
			}
		}
	}

	return result
}

// BFSShortestPath finds shortest path from start to end
// Returns (distance, path, found)
func (g *Graph) BFSShortestPath(start, end int) (int, []int, bool) {
	if start == end {
		return 0, []int{start}, true
	}

	visited := make(map[int]bool)
	queue := list.New()
	parent := make(map[int]int)

	queue.PushBack(start)
	visited[start] = true
	parent[start] = -1

	for queue.Len() > 0 {
		element := queue.Front()
		vertex := element.Value.(int)
		queue.Remove(element)

		for _, neighbor := range g.adj[vertex] {
			if !visited[neighbor] {
				visited[neighbor] = true
				parent[neighbor] = vertex
				queue.PushBack(neighbor)

				if neighbor == end {
					// Reconstruct path
					path := []int{}
					current := end

					for current != -1 {
						path = append([]int{current}, path...)
						current = parent[current]
					}

					return len(path) - 1, path, true
				}
			}
		}
	}

	return -1, nil, false
}

// ===========================
// DFS IMPLEMENTATION
// ===========================

// DFS performs depth-first search from start vertex (recursive)
// Returns vertices in DFS order
func (g *Graph) DFS(start int) []int {
	visited := make(map[int]bool)
	result := []int{}

	g.dfsHelper(start, visited, &result)

	return result
}

func (g *Graph) dfsHelper(vertex int, visited map[int]bool, result *[]int) {
	visited[vertex] = true
	*result = append(*result, vertex)

	for _, neighbor := range g.adj[vertex] {
		if !visited[neighbor] {
			g.dfsHelper(neighbor, visited, result)
		}
	}
}

// DFSIterative performs DFS using explicit stack
func (g *Graph) DFSIterative(start int) []int {
	visited := make(map[int]bool)
	stack := []int{start}
	result := []int{}

	for len(stack) > 0 {
		// Pop from stack
		vertex := stack[len(stack)-1]
		stack = stack[:len(stack)-1]

		if !visited[vertex] {
			visited[vertex] = true
			result = append(result, vertex)

			// Push neighbors in reverse order
			for i := len(g.adj[vertex]) - 1; i >= 0; i-- {
				neighbor := g.adj[vertex][i]
				if !visited[neighbor] {
					stack = append(stack, neighbor)
				}
			}
		}
	}

	return result
}

// ===========================
// CYCLE DETECTION
// ===========================

// Color represents vertex state in 3-color algorithm
type Color int

const (
	White Color = iota // Unvisited
	Gray               // Visiting
	Black              // Visited
)

// HasCycleDirected detects cycle in directed graph
// Uses 3-color DFS
func (g *Graph) HasCycleDirected() bool {
	color := make([]Color, g.vertices)

	var dfs func(int) bool
	dfs = func(vertex int) bool {
		color[vertex] = Gray

		for _, neighbor := range g.adj[vertex] {
			if color[neighbor] == Gray {
				return true // Back edge - cycle!
			}
			if color[neighbor] == White {
				if dfs(neighbor) {
					return true
				}
			}
		}

		color[vertex] = Black
		return false
	}

	for v := 0; v < g.vertices; v++ {
		if color[v] == White {
			if dfs(v) {
				return true
			}
		}
	}

	return false
}

// HasCycleUndirected detects cycle in undirected graph
// Uses DFS with parent tracking
func (g *Graph) HasCycleUndirected() bool {
	visited := make(map[int]bool)

	var dfs func(int, int) bool
	dfs = func(vertex, parent int) bool {
		visited[vertex] = true

		for _, neighbor := range g.adj[vertex] {
			if !visited[neighbor] {
				if dfs(neighbor, vertex) {
					return true
				}
			} else if neighbor != parent {
				// Visited and not parent - cycle!
				return true
			}
		}

		return false
	}

	for v := 0; v < g.vertices; v++ {
		if !visited[v] {
			if dfs(v, -1) {
				return true
			}
		}
	}

	return false
}

// ===========================
// TOPOLOGICAL SORT
// ===========================

// TopologicalSort returns topological ordering using Kahn's algorithm
// Returns nil if cycle exists
func (g *Graph) TopologicalSort() []int {
	inDegree := make([]int, g.vertices)

	// Calculate in-degrees
	for v := 0; v < g.vertices; v++ {
		for _, neighbor := range g.adj[v] {
			inDegree[neighbor]++
		}
	}

	// Start with vertices having in-degree 0
	queue := list.New()
	for v := 0; v < g.vertices; v++ {
		if inDegree[v] == 0 {
			queue.PushBack(v)
		}
	}

	result := []int{}

	for queue.Len() > 0 {
		element := queue.Front()
		vertex := element.Value.(int)
		queue.Remove(element)

		result = append(result, vertex)

		for _, neighbor := range g.adj[vertex] {
			inDegree[neighbor]--
			if inDegree[neighbor] == 0 {
				queue.PushBack(neighbor)
			}
		}
	}

	if len(result) == g.vertices {
		return result
	}
	return nil // Cycle exists
}

// ===========================
// CONNECTED COMPONENTS
// ===========================

// CountComponents returns number of connected components
func (g *Graph) CountComponents() int {
	visited := make(map[int]bool)
	count := 0

	var dfs func(int)
	dfs = func(vertex int) {
		visited[vertex] = true
		for _, neighbor := range g.adj[vertex] {
			if !visited[neighbor] {
				dfs(neighbor)
			}
		}
	}

	for v := 0; v < g.vertices; v++ {
		if !visited[v] {
			count++
			dfs(v)
		}
	}

	return count
}

// ===========================
// UNION-FIND
// ===========================

// UnionFind implements disjoint set union with path compression
type UnionFind struct {
	parent     []int
	rank       []int
	components int
}

// NewUnionFind creates a new Union-Find with n elements
func NewUnionFind(n int) *UnionFind {
	uf := &UnionFind{
		parent:     make([]int, n),
		rank:       make([]int, n),
		components: n,
	}

	for i := 0; i < n; i++ {
		uf.parent[i] = i
	}

	return uf
}

// Find returns root of element x with path compression
func (uf *UnionFind) Find(x int) int {
	if uf.parent[x] != x {
		uf.parent[x] = uf.Find(uf.parent[x]) // Path compression
	}
	return uf.parent[x]
}

// Union merges sets containing x and y
// Returns true if union performed, false if already in same set
func (uf *UnionFind) Union(x, y int) bool {
	rootX := uf.Find(x)
	rootY := uf.Find(y)

	if rootX == rootY {
		return false
	}

	// Union by rank
	if uf.rank[rootX] < uf.rank[rootY] {
		uf.parent[rootX] = rootY
	} else if uf.rank[rootX] > uf.rank[rootY] {
		uf.parent[rootY] = rootX
	} else {
		uf.parent[rootY] = rootX
		uf.rank[rootX]++
	}

	uf.components--
	return true
}

// Connected checks if x and y are in same set
func (uf *UnionFind) Connected(x, y int) bool {
	return uf.Find(x) == uf.Find(y)
}

// CountComponents returns number of components
func (uf *UnionFind) CountComponents() int {
	return uf.components
}

// ===========================
// TESTING
// ===========================

func main() {
	fmt.Println("=== BFS Test ===")
	g := NewGraph(6)
	g.AddEdge(0, 1)
	g.AddEdge(0, 2)
	g.AddEdge(1, 3)
	g.AddEdge(1, 4)
	g.AddEdge(2, 5)

	bfsResult := g.BFS(0)
	fmt.Printf("BFS from 0: %v\n", bfsResult)

	fmt.Println("\n=== Shortest Path Test ===")
	dist, path, found := g.BFSShortestPath(0, 5)
	if found {
		fmt.Printf("Distance: %d, Path: %v\n", dist, path)
	}

	fmt.Println("\n=== DFS Test ===")
	dfsResult := g.DFS(0)
	fmt.Printf("DFS from 0: %v\n", dfsResult)

	fmt.Println("\n=== Cycle Detection Test ===")
	dag := NewGraph(4)
	dag.AddEdge(0, 1)
	dag.AddEdge(0, 2)
	dag.AddEdge(1, 3)
	dag.AddEdge(2, 3)
	fmt.Printf("DAG has cycle: %v\n", dag.HasCycleDirected())

	cyclic := NewGraph(3)
	cyclic.AddEdge(0, 1)
	cyclic.AddEdge(1, 2)
	cyclic.AddEdge(2, 0)
	fmt.Printf("Cyclic graph has cycle: %v\n", cyclic.HasCycleDirected())

	fmt.Println("\n=== Topological Sort Test ===")
	topoOrder := dag.TopologicalSort()
	fmt.Printf("Topological order: %v\n", topoOrder)

	fmt.Println("\n=== Components Test ===")
	disconnected := NewGraph(6)
	disconnected.AddUndirectedEdge(0, 1)
	disconnected.AddUndirectedEdge(2, 3)
	disconnected.AddUndirectedEdge(4, 5)
	fmt.Printf("Number of components: %d\n", disconnected.CountComponents())

	fmt.Println("\n=== Union-Find Test ===")
	uf := NewUnionFind(5)
	uf.Union(0, 1)
	uf.Union(2, 3)
	fmt.Printf("0 and 1 connected: %v\n", uf.Connected(0, 1))
	fmt.Printf("0 and 2 connected: %v\n", uf.Connected(0, 2))
	fmt.Printf("Components: %d\n", uf.CountComponents())
}
```
---

## **12. Mental Models & Mastery Strategies**

### **12.1 The Graph Intuition Framework**

**Cognitive Principle:** Expert problem-solvers don't memorize algorithms—they build **mental models** that let them see patterns instantly.

**Your Three-Level Understanding System:**

```
Level 1: RECOGNITION
"Is this a graph problem?"
↓
Level 2: CLASSIFICATION  
"What type? Shortest path? Cycle? Components?"
↓
Level 3: SOLUTION PATTERN
"Which algorithm template applies?"
```

### **12.2 Pattern Recognition Checklist**

**When you see a problem, ask:**

1. **Is it implicitly a graph?**
   - Grid/matrix → Graph (cells = vertices, adjacency = edges)
   - Dependencies → DAG
   - Relationships → Graph

2. **What am I optimizing?**
   - Shortest path → BFS (unweighted) or Dijkstra (weighted)
   - All paths → DFS with backtracking
   - Ordering → Topological sort
   - Grouping → Connected components

3. **What are the constraints?**
   - Directed/Undirected
   - Weighted/Unweighted
   - Cyclic/Acyclic
   - Dense/Sparse

### **12.3 Deliberate Practice Strategy**

**The Monk's Approach to Mastery:**

**Week 1-2: Foundations**
- Implement all basic algorithms from scratch (BFS, DFS, cycle detection)
- Do NOT look at solutions first
- Time yourself, aim to implement BFS in < 5 minutes by week 2

**Week 3-4: Pattern Recognition**
- Solve 50 problems, categorize each by pattern
- After solving, write down: "This is a [PATTERN] problem because..."
- Keep a pattern journal

**Week 5-6: Speed & Variations**
- Solve same problem 3 ways
- Optimize for time, then space, then elegance
- Can you solve it without looking at notes?

**Week 7-8: Integration**
- Hard problems combining multiple concepts
- Explain solutions out loud (Feynman technique)
- Teach someone else

### **12.4 Psychological Flow State**

**Meta-Cognitive Principles for Deep Focus:**

1. **Chunking:** Don't think "build graph then BFS then reconstruct path"
   - Think: "Shortest path template with parent tracking"
   - One mental chunk vs three

2. **Progressive Revelation:** Start simple
   ```
   Step 1: Can I detect if path exists? (Boolean)
   Step 2: Can I find distance? (Integer)
   Step 3: Can I reconstruct path? (List)
   ```

3. **Failure = Data:** When stuck, ask:
   - "What am I missing?"
   - "Is there a hidden constraint?"
   - "Have I seen something similar?"

### **12.5 The 5-Minute Template Framework**

**For any graph problem, spend first 5 minutes on:**

1. **Draw it** (30 seconds)
2. **Classify it** (30 seconds) - Directed? Weighted? Cyclic?
3. **Pattern match** (1 minute) - Which template?
4. **Edge cases** (1 minute) - Empty graph? Disconnected? Cycles?
5. **Complexity check** (1 minute) - Will my solution be fast enough?
6. **Code outline** (1 minute) - Pseudocode main steps

**Only then start coding.**

---

## **Summary: The Complete Mental Map**

```
UNWEIGHTED GRAPHS
│
├─ REPRESENTATIONS
│  ├─ Edge List (rare, simple)
│  ├─ Adjacency Matrix (dense graphs, O(1) edge check)
│  └─ Adjacency List ⭐ (default choice, O(V+E))
│
├─ TRAVERSAL (Master These First)
│  ├─ BFS (Queue, layer-by-layer)
│  │  └─ USE FOR: Shortest path, level-order
│  └─ DFS (Stack/Recursion, deep exploration)
│     └─ USE FOR: Cycles, topological sort, backtracking
│
├─ CORE ALGORITHMS
│  ├─ Shortest Path → BFS ⭐
│  ├─ Cycle Detection
│  │  ├─ Undirected → DFS with parent
│  │  └─ Directed → 3-color DFS
│  ├─ Connected Components → DFS/BFS or Union-Find
│  ├─ Topological Sort → DFS or Kahn's (BFS)
│  └─ Bipartite Check → BFS/DFS with 2-coloring
│
└─ ADVANCED PATTERNS
   ├─ Grid as Graph (implicit)
   ├─ Multi-source BFS
   ├─ Bidirectional BFS (optimization)
   └─ Union-Find (dynamic connectivity)
```

---

## **Your Path to Top 1%**

**You now have:**
✅ Complete conceptual understanding
✅ All fundamental algorithms
✅ Implementations in Rust, Python, Go
✅ Problem-solving patterns
✅ Mental models for mastery

**Next steps:**
1. Implement each algorithm once from scratch without looking
2. Solve 10 problems per pattern (BFS, DFS, etc.)
3. Time yourself - speed comes from pattern recognition
4. Revisit this guide when stuck - internalize the decision trees

**Remember:** The difference between good and great isn't knowing more algorithms—it's recognizing patterns instantly and executing flawlessly.

## *"The master has failed more times than the beginner has even tried."*

You're building a foundation that will serve you for life. Trust the process, embrace the struggle, and stay disciplined. 

Would you like me to dive deeper into any specific topic, provide more practice problems for a particular pattern, or move on to weighted graphs next?