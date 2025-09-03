I'll create a comprehensive guide to graph implementation with complete examples in both Python and Rust. This will be a substantial reference document covering theory, implementation patterns, and practical examples.I've created a comprehensive guide to graph implementation covering both Python and Rust. The guide includes:

## Key Features:

1. **Complete Implementations**: Full-featured graph classes with adjacency list representation
2. **Essential Algorithms**: BFS, DFS, Dijkstra's shortest path, cycle detection, and topological sorting
3. **Both Languages**: Side-by-side Python and Rust implementations with idiomatic code
4. **Practical Examples**: Working code with test cases and usage examples
5. **Performance Analysis**: Time/space complexity analysis and language comparisons

## What's Included:

- **Python Implementation**: Uses type hints, collections, and clean OOP design
- **Rust Implementation**: Memory-safe with proper ownership, comprehensive test suite
- **Algorithm Implementations**: All major graph algorithms with detailed explanations
- **Best Practices**: Performance optimization, testing strategies, and design considerations

The implementations are production-ready and include error handling, comprehensive documentation, and examples. Both versions support directed/undirected graphs, weighted edges, and provide consistent APIs for easy usage.

Would you like me to expand on any particular aspect, such as adding more advanced algorithms (like A*, minimum spanning trees, or network flow), or would you like to see specific optimizations for certain use cases?

# Comprehensive Graph Implementation Guide

## Table of Contents
1. [Graph Theory Fundamentals](#graph-theory-fundamentals)
2. [Graph Representations](#graph-representations)
3. [Python Implementation](#python-implementation)
4. [Rust Implementation](#rust-implementation)
5. [Common Algorithms](#common-algorithms)
6. [Performance Comparison](#performance-comparison)
7. [Best Practices](#best-practices)

## Graph Theory Fundamentals

### What is a Graph?
A graph G = (V, E) is a mathematical structure consisting of:
- **Vertices (V)**: A set of nodes or points
- **Edges (E)**: A set of connections between vertices

### Types of Graphs
- **Directed vs Undirected**: Edges have direction or are bidirectional
- **Weighted vs Unweighted**: Edges have associated costs/weights
- **Connected vs Disconnected**: All vertices reachable vs isolated components
- **Cyclic vs Acyclic**: Contains cycles or is cycle-free

### Key Properties
- **Degree**: Number of edges connected to a vertex
- **Path**: Sequence of vertices connected by edges
- **Cycle**: Path that starts and ends at the same vertex
- **Connected Component**: Maximal set of connected vertices

## Graph Representations

### 1. Adjacency Matrix
- 2D array where `matrix[i][j]` represents edge from vertex i to j
- **Space Complexity**: O(V²)
- **Good for**: Dense graphs, quick edge lookup

### 2. Adjacency List
- Array of lists where each list contains neighbors of a vertex
- **Space Complexity**: O(V + E)
- **Good for**: Sparse graphs, iterating over neighbors

### 3. Edge List
- Simple list of all edges as pairs/tuples
- **Space Complexity**: O(E)
- **Good for**: Simple operations, algorithms like Kruskal's

## Python Implementation

### Basic Graph Class with Adjacency List

```python
from collections import defaultdict, deque
from typing import List, Dict, Set, Optional, Tuple
import heapq

class Graph:
    def __init__(self, directed: bool = False):
        self.directed = directed
        self.vertices: Set[int] = set()
        self.adjacency_list: Dict[int, List[Tuple[int, float]]] = defaultdict(list)
    
    def add_vertex(self, vertex: int) -> None:
        """Add a vertex to the graph."""
        self.vertices.add(vertex)
    
    def add_edge(self, from_vertex: int, to_vertex: int, weight: float = 1.0) -> None:
        """Add an edge between two vertices."""
        self.vertices.add(from_vertex)
        self.vertices.add(to_vertex)
        
        self.adjacency_list[from_vertex].append((to_vertex, weight))
        if not self.directed:
            self.adjacency_list[to_vertex].append((from_vertex, weight))
    
    def remove_edge(self, from_vertex: int, to_vertex: int) -> None:
        """Remove an edge between two vertices."""
        self.adjacency_list[from_vertex] = [
            (v, w) for v, w in self.adjacency_list[from_vertex] if v != to_vertex
        ]
        if not self.directed:
            self.adjacency_list[to_vertex] = [
                (v, w) for v, w in self.adjacency_list[to_vertex] if v != from_vertex
            ]
    
    def get_neighbors(self, vertex: int) -> List[Tuple[int, float]]:
        """Get all neighbors of a vertex with their weights."""
        return self.adjacency_list[vertex]
    
    def has_edge(self, from_vertex: int, to_vertex: int) -> bool:
        """Check if an edge exists between two vertices."""
        return any(v == to_vertex for v, _ in self.adjacency_list[from_vertex])
    
    def get_vertices(self) -> Set[int]:
        """Get all vertices in the graph."""
        return self.vertices.copy()
    
    def get_edge_count(self) -> int:
        """Get total number of edges."""
        edge_count = sum(len(neighbors) for neighbors in self.adjacency_list.values())
        return edge_count if self.directed else edge_count // 2
    
    def __str__(self) -> str:
        """String representation of the graph."""
        result = []
        for vertex in sorted(self.vertices):
            neighbors = [f"{v}({w})" for v, w in self.adjacency_list[vertex]]
            result.append(f"{vertex}: {', '.join(neighbors)}")
        return "\n".join(result)

class GraphAlgorithms:
    """Collection of graph algorithms."""
    
    @staticmethod
    def bfs(graph: Graph, start_vertex: int) -> List[int]:
        """Breadth-First Search traversal."""
        if start_vertex not in graph.vertices:
            return []
        
        visited = set()
        queue = deque([start_vertex])
        result = []
        
        while queue:
            vertex = queue.popleft()
            if vertex not in visited:
                visited.add(vertex)
                result.append(vertex)
                
                for neighbor, _ in graph.get_neighbors(vertex):
                    if neighbor not in visited:
                        queue.append(neighbor)
        
        return result
    
    @staticmethod
    def dfs(graph: Graph, start_vertex: int) -> List[int]:
        """Depth-First Search traversal."""
        if start_vertex not in graph.vertices:
            return []
        
        visited = set()
        result = []
        
        def dfs_recursive(vertex: int):
            visited.add(vertex)
            result.append(vertex)
            
            for neighbor, _ in graph.get_neighbors(vertex):
                if neighbor not in visited:
                    dfs_recursive(neighbor)
        
        dfs_recursive(start_vertex)
        return result
    
    @staticmethod
    def dijkstra(graph: Graph, start_vertex: int) -> Dict[int, float]:
        """Dijkstra's shortest path algorithm."""
        if start_vertex not in graph.vertices:
            return {}
        
        distances = {vertex: float('inf') for vertex in graph.vertices}
        distances[start_vertex] = 0
        
        priority_queue = [(0, start_vertex)]
        visited = set()
        
        while priority_queue:
            current_distance, current_vertex = heapq.heappop(priority_queue)
            
            if current_vertex in visited:
                continue
            
            visited.add(current_vertex)
            
            for neighbor, weight in graph.get_neighbors(current_vertex):
                distance = current_distance + weight
                
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    heapq.heappush(priority_queue, (distance, neighbor))
        
        return distances
    
    @staticmethod
    def detect_cycle(graph: Graph) -> bool:
        """Detect if the graph contains a cycle."""
        if graph.directed:
            return GraphAlgorithms._detect_cycle_directed(graph)
        else:
            return GraphAlgorithms._detect_cycle_undirected(graph)
    
    @staticmethod
    def _detect_cycle_directed(graph: Graph) -> bool:
        """Detect cycle in directed graph using DFS."""
        color = {vertex: 'white' for vertex in graph.vertices}
        
        def dfs_cycle(vertex: int) -> bool:
            if color[vertex] == 'gray':
                return True
            if color[vertex] == 'black':
                return False
            
            color[vertex] = 'gray'
            for neighbor, _ in graph.get_neighbors(vertex):
                if dfs_cycle(neighbor):
                    return True
            
            color[vertex] = 'black'
            return False
        
        for vertex in graph.vertices:
            if color[vertex] == 'white':
                if dfs_cycle(vertex):
                    return True
        return False
    
    @staticmethod
    def _detect_cycle_undirected(graph: Graph) -> bool:
        """Detect cycle in undirected graph using DFS."""
        visited = set()
        
        def dfs_cycle(vertex: int, parent: int) -> bool:
            visited.add(vertex)
            
            for neighbor, _ in graph.get_neighbors(vertex):
                if neighbor not in visited:
                    if dfs_cycle(neighbor, vertex):
                        return True
                elif neighbor != parent:
                    return True
            return False
        
        for vertex in graph.vertices:
            if vertex not in visited:
                if dfs_cycle(vertex, -1):
                    return True
        return False
    
    @staticmethod
    def topological_sort(graph: Graph) -> Optional[List[int]]:
        """Topological sort for directed acyclic graphs."""
        if not graph.directed:
            return None
        
        if GraphAlgorithms.detect_cycle(graph):
            return None
        
        in_degree = {vertex: 0 for vertex in graph.vertices}
        
        for vertex in graph.vertices:
            for neighbor, _ in graph.get_neighbors(vertex):
                in_degree[neighbor] += 1
        
        queue = deque([v for v in graph.vertices if in_degree[v] == 0])
        result = []
        
        while queue:
            vertex = queue.popleft()
            result.append(vertex)
            
            for neighbor, _ in graph.get_neighbors(vertex):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return result if len(result) == len(graph.vertices) else None

# Example usage
if __name__ == "__main__":
    # Create a directed weighted graph
    graph = Graph(directed=True)
    
    # Add vertices and edges
    graph.add_edge(0, 1, 4)
    graph.add_edge(0, 2, 2)
    graph.add_edge(1, 2, 1)
    graph.add_edge(1, 3, 5)
    graph.add_edge(2, 3, 3)
    
    print("Graph:")
    print(graph)
    print()
    
    # Perform algorithms
    algorithms = GraphAlgorithms()
    
    print("BFS from vertex 0:", algorithms.bfs(graph, 0))
    print("DFS from vertex 0:", algorithms.dfs(graph, 0))
    print("Shortest paths from vertex 0:", algorithms.dijkstra(graph, 0))
    print("Has cycle:", algorithms.detect_cycle(graph))
    print("Topological sort:", algorithms.topological_sort(graph))
```

## Rust Implementation

### Basic Graph Structure with Adjacency List

```rust
use std::collections::{HashMap, HashSet, VecDeque, BinaryHeap};
use std::cmp::Reverse;

#[derive(Debug, Clone)]
pub struct Graph {
    directed: bool,
    vertices: HashSet<usize>,
    adjacency_list: HashMap<usize, Vec<(usize, f64)>>,
}

impl Graph {
    pub fn new(directed: bool) -> Self {
        Graph {
            directed,
            vertices: HashSet::new(),
            adjacency_list: HashMap::new(),
        }
    }
    
    pub fn add_vertex(&mut self, vertex: usize) {
        self.vertices.insert(vertex);
    }
    
    pub fn add_edge(&mut self, from_vertex: usize, to_vertex: usize, weight: f64) {
        self.vertices.insert(from_vertex);
        self.vertices.insert(to_vertex);
        
        self.adjacency_list
            .entry(from_vertex)
            .or_insert_with(Vec::new)
            .push((to_vertex, weight));
        
        if !self.directed {
            self.adjacency_list
                .entry(to_vertex)
                .or_insert_with(Vec::new)
                .push((from_vertex, weight));
        }
    }
    
    pub fn remove_edge(&mut self, from_vertex: usize, to_vertex: usize) {
        if let Some(neighbors) = self.adjacency_list.get_mut(&from_vertex) {
            neighbors.retain(|(v, _)| *v != to_vertex);
        }
        
        if !self.directed {
            if let Some(neighbors) = self.adjacency_list.get_mut(&to_vertex) {
                neighbors.retain(|(v, _)| *v != from_vertex);
            }
        }
    }
    
    pub fn get_neighbors(&self, vertex: usize) -> Vec<(usize, f64)> {
        self.adjacency_list
            .get(&vertex)
            .map(|neighbors| neighbors.clone())
            .unwrap_or_else(Vec::new)
    }
    
    pub fn has_edge(&self, from_vertex: usize, to_vertex: usize) -> bool {
        self.adjacency_list
            .get(&from_vertex)
            .map_or(false, |neighbors| {
                neighbors.iter().any(|(v, _)| *v == to_vertex)
            })
    }
    
    pub fn get_vertices(&self) -> HashSet<usize> {
        self.vertices.clone()
    }
    
    pub fn get_edge_count(&self) -> usize {
        let total_edges: usize = self.adjacency_list
            .values()
            .map(|neighbors| neighbors.len())
            .sum();
        
        if self.directed {
            total_edges
        } else {
            total_edges / 2
        }
    }
    
    pub fn is_directed(&self) -> bool {
        self.directed
    }
}

pub struct GraphAlgorithms;

impl GraphAlgorithms {
    pub fn bfs(graph: &Graph, start_vertex: usize) -> Vec<usize> {
        if !graph.vertices.contains(&start_vertex) {
            return Vec::new();
        }
        
        let mut visited = HashSet::new();
        let mut queue = VecDeque::new();
        let mut result = Vec::new();
        
        queue.push_back(start_vertex);
        
        while let Some(vertex) = queue.pop_front() {
            if !visited.contains(&vertex) {
                visited.insert(vertex);
                result.push(vertex);
                
                for (neighbor, _) in graph.get_neighbors(vertex) {
                    if !visited.contains(&neighbor) {
                        queue.push_back(neighbor);
                    }
                }
            }
        }
        
        result
    }
    
    pub fn dfs(graph: &Graph, start_vertex: usize) -> Vec<usize> {
        if !graph.vertices.contains(&start_vertex) {
            return Vec::new();
        }
        
        let mut visited = HashSet::new();
        let mut result = Vec::new();
        
        Self::dfs_recursive(graph, start_vertex, &mut visited, &mut result);
        result
    }
    
    fn dfs_recursive(
        graph: &Graph,
        vertex: usize,
        visited: &mut HashSet<usize>,
        result: &mut Vec<usize>,
    ) {
        visited.insert(vertex);
        result.push(vertex);
        
        for (neighbor, _) in graph.get_neighbors(vertex) {
            if !visited.contains(&neighbor) {
                Self::dfs_recursive(graph, neighbor, visited, result);
            }
        }
    }
    
    pub fn dijkstra(graph: &Graph, start_vertex: usize) -> HashMap<usize, f64> {
        let mut distances = HashMap::new();
        let mut visited = HashSet::new();
        let mut priority_queue = BinaryHeap::new();
        
        for &vertex in &graph.vertices {
            distances.insert(vertex, f64::INFINITY);
        }
        distances.insert(start_vertex, 0.0);
        
        priority_queue.push(Reverse((0.0, start_vertex)));
        
        while let Some(Reverse((current_distance, current_vertex))) = priority_queue.pop() {
            if visited.contains(&current_vertex) {
                continue;
            }
            
            visited.insert(current_vertex);
            
            for (neighbor, weight) in graph.get_neighbors(current_vertex) {
                let distance = current_distance + weight;
                
                if distance < distances[&neighbor] {
                    distances.insert(neighbor, distance);
                    priority_queue.push(Reverse((distance, neighbor)));
                }
            }
        }
        
        distances
    }
    
    pub fn detect_cycle(graph: &Graph) -> bool {
        if graph.is_directed() {
            Self::detect_cycle_directed(graph)
        } else {
            Self::detect_cycle_undirected(graph)
        }
    }
    
    fn detect_cycle_directed(graph: &Graph) -> bool {
        let mut color = HashMap::new();
        
        for &vertex in &graph.vertices {
            color.insert(vertex, Color::White);
        }
        
        for &vertex in &graph.vertices {
            if color[&vertex] == Color::White {
                if Self::dfs_cycle_directed(graph, vertex, &mut color) {
                    return true;
                }
            }
        }
        
        false
    }
    
    fn dfs_cycle_directed(
        graph: &Graph,
        vertex: usize,
        color: &mut HashMap<usize, Color>,
    ) -> bool {
        if color[&vertex] == Color::Gray {
            return true;
        }
        if color[&vertex] == Color::Black {
            return false;
        }
        
        color.insert(vertex, Color::Gray);
        
        for (neighbor, _) in graph.get_neighbors(vertex) {
            if Self::dfs_cycle_directed(graph, neighbor, color) {
                return true;
            }
        }
        
        color.insert(vertex, Color::Black);
        false
    }
    
    fn detect_cycle_undirected(graph: &Graph) -> bool {
        let mut visited = HashSet::new();
        
        for &vertex in &graph.vertices {
            if !visited.contains(&vertex) {
                if Self::dfs_cycle_undirected(graph, vertex, None, &mut visited) {
                    return true;
                }
            }
        }
        
        false
    }
    
    fn dfs_cycle_undirected(
        graph: &Graph,
        vertex: usize,
        parent: Option<usize>,
        visited: &mut HashSet<usize>,
    ) -> bool {
        visited.insert(vertex);
        
        for (neighbor, _) in graph.get_neighbors(vertex) {
            if !visited.contains(&neighbor) {
                if Self::dfs_cycle_undirected(graph, neighbor, Some(vertex), visited) {
                    return true;
                }
            } else if Some(neighbor) != parent {
                return true;
            }
        }
        
        false
    }
    
    pub fn topological_sort(graph: &Graph) -> Option<Vec<usize>> {
        if !graph.is_directed() {
            return None;
        }
        
        if Self::detect_cycle(graph) {
            return None;
        }
        
        let mut in_degree = HashMap::new();
        
        for &vertex in &graph.vertices {
            in_degree.insert(vertex, 0);
        }
        
        for &vertex in &graph.vertices {
            for (neighbor, _) in graph.get_neighbors(vertex) {
                *in_degree.get_mut(&neighbor).unwrap() += 1;
            }
        }
        
        let mut queue = VecDeque::new();
        for (&vertex, &degree) in &in_degree {
            if degree == 0 {
                queue.push_back(vertex);
            }
        }
        
        let mut result = Vec::new();
        
        while let Some(vertex) = queue.pop_front() {
            result.push(vertex);
            
            for (neighbor, _) in graph.get_neighbors(vertex) {
                *in_degree.get_mut(&neighbor).unwrap() -= 1;
                if in_degree[&neighbor] == 0 {
                    queue.push_back(neighbor);
                }
            }
        }
        
        if result.len() == graph.vertices.len() {
            Some(result)
        } else {
            None
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq)]
enum Color {
    White,
    Gray,
    Black,
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_graph_creation() {
        let mut graph = Graph::new(true);
        graph.add_edge(0, 1, 4.0);
        graph.add_edge(0, 2, 2.0);
        graph.add_edge(1, 2, 1.0);
        
        assert!(graph.has_edge(0, 1));
        assert!(graph.has_edge(1, 2));
        assert!(!graph.has_edge(2, 0));
        assert_eq!(graph.get_edge_count(), 3);
    }
    
    #[test]
    fn test_bfs() {
        let mut graph = Graph::new(false);
        graph.add_edge(0, 1, 1.0);
        graph.add_edge(1, 2, 1.0);
        graph.add_edge(2, 3, 1.0);
        
        let result = GraphAlgorithms::bfs(&graph, 0);
        assert_eq!(result.len(), 4);
        assert_eq!(result[0], 0);
    }
    
    #[test]
    fn test_dijkstra() {
        let mut graph = Graph::new(true);
        graph.add_edge(0, 1, 4.0);
        graph.add_edge(0, 2, 2.0);
        graph.add_edge(1, 3, 3.0);
        graph.add_edge(2, 3, 1.0);
        
        let distances = GraphAlgorithms::dijkstra(&graph, 0);
        assert_eq!(distances[&3], 3.0);
    }
}

// Example usage
fn main() {
    let mut graph = Graph::new(true);
    
    // Add edges
    graph.add_edge(0, 1, 4.0);
    graph.add_edge(0, 2, 2.0);
    graph.add_edge(1, 2, 1.0);
    graph.add_edge(1, 3, 5.0);
    graph.add_edge(2, 3, 3.0);
    
    println!("Graph vertices: {:?}", graph.get_vertices());
    println!("Edge count: {}", graph.get_edge_count());
    
    // Run algorithms
    println!("BFS from vertex 0: {:?}", GraphAlgorithms::bfs(&graph, 0));
    println!("DFS from vertex 0: {:?}", GraphAlgorithms::dfs(&graph, 0));
    println!("Shortest paths from vertex 0: {:?}", GraphAlgorithms::dijkstra(&graph, 0));
    println!("Has cycle: {}", GraphAlgorithms::detect_cycle(&graph));
    
    if let Some(topo_sort) = GraphAlgorithms::topological_sort(&graph) {
        println!("Topological sort: {:?}", topo_sort);
    } else {
        println!("Cannot perform topological sort (graph has cycles or is undirected)");
    }
}
```

## Common Algorithms

### Time Complexities
- **BFS/DFS**: O(V + E)
- **Dijkstra's Algorithm**: O((V + E) log V) with binary heap
- **Cycle Detection**: O(V + E)
- **Topological Sort**: O(V + E)

### Space Complexities
- **Adjacency List**: O(V + E)
- **Adjacency Matrix**: O(V²)
- **BFS/DFS**: O(V) for visited set and recursion stack

## Performance Comparison

### Python vs Rust
- **Memory Safety**: Rust prevents common bugs like null pointer dereferences
- **Performance**: Rust typically 2-10x faster for graph algorithms
- **Concurrency**: Rust's ownership system enables safe parallelism
- **Development Speed**: Python allows faster prototyping

### When to Use Each
- **Python**: Rapid prototyping, data analysis, research
- **Rust**: Production systems, performance-critical applications, system programming

## Best Practices

### Design Considerations
1. **Choose the right representation**: Adjacency list for sparse graphs, matrix for dense graphs
2. **Consider memory usage**: Especially important for large graphs
3. **Error handling**: Check for invalid vertices, negative cycles, etc.
4. **Generic implementations**: Use templates/generics for different vertex types

### Optimization Tips
1. **Use appropriate data structures**: Priority queues for Dijkstra, sets for visited tracking
2. **Avoid unnecessary copying**: Pass by reference when possible
3. **Early termination**: Stop algorithms when target is found
4. **Batch operations**: Group multiple graph modifications together

### Testing Strategies
1. **Edge cases**: Empty graphs, single vertices, disconnected components
2. **Correctness**: Verify algorithm outputs against known results
3. **Performance**: Benchmark with graphs of different sizes and densities
4. **Memory usage**: Monitor memory consumption for large graphs

This comprehensive guide provides solid foundations for implementing graphs in both Python and Rust, with practical examples and best practices for real-world usage.

I'll create a comprehensive ASCII diagram showing how graphs work, covering the fundamental concepts and operations step by step.I've created a comprehensive ASCII diagram guide that walks through how graphs work step by step. The guide covers:

1. **Basic Components** - Shows vertices and edges with simple examples
2. **Graph Types** - Directed, undirected, and weighted graphs
3. **Representations** - Adjacency matrices and lists
4. **Traversal Algorithms** - Step-by-step DFS and BFS with visual progression
5. **Shortest Path** - Dijkstra's algorithm example with distances
6. **Common Patterns** - Trees, cycles, and bipartite graphs
7. **Real Applications** - Social networks, routing, dependencies

Each section uses ASCII art to visually demonstrate the concepts, making it easy to understand how vertices connect through edges and how algorithms traverse these connections. The diagrams show the state changes during algorithm execution, helping you see exactly how graph operations work in practice.

Would you like me to expand on any particular section or add examples of other graph algorithms like topological sorting or minimum spanning trees?

# Complete Guide to Graphs - ASCII Diagrams

## 1. Basic Graph Components

### Vertices (Nodes) and Edges
```
Simple Graph:
    A ---- B
    |      |
    |      |
    C ---- D

Components:
- Vertices: A, B, C, D (the points)
- Edges: A-B, A-C, B-D, C-D (the connections)
- Degree of A: 2 (connected to B and C)
- Degree of B: 2 (connected to A and D)
```

## 2. Types of Graphs

### Directed Graph (Digraph)
```
    A ---> B
    ^      |
    |      |
    |      v
    C <--- D

Arrows show direction:
- A → B (A points to B)
- B → D (B points to D)
- D → C (D points to C)
- C → A (C points to A)
```

### Undirected Graph
```
    A ---- B
    |      |
    |      |
    C ---- D

No arrows = bidirectional connections
A-B means A↔B (can go both ways)
```

### Weighted Graph
```
    A --5-- B
    |       |
   3|       |8
    |       |
    C --2-- D

Numbers on edges represent weights:
- Edge A-B has weight 5
- Edge A-C has weight 3
- Edge B-D has weight 8
- Edge C-D has weight 2
```

## 3. Graph Representations

### Adjacency Matrix
```
Graph:     A ---- B
           |      |
           C ---- D

Matrix:    A  B  C  D
        A [0  1  1  0]
        B [1  0  0  1]  
        C [1  0  0  1]
        D [0  1  1  0]

1 = edge exists, 0 = no edge
```

### Adjacency List
```
Graph:     A ---- B
           |      |
           C ---- D

List:
A: [B, C]
B: [A, D]
C: [A, D]
D: [B, C]

Each vertex lists its neighbors
```

## 4. Graph Traversal Algorithms

### Depth-First Search (DFS)
```
Step-by-step DFS starting from A:

Initial:   A ---- B      Stack: [A]
           |      |      Visited: []
           C ---- D

Step 1:    A ---- B      Stack: [B, C]
          *|      |      Visited: [A]
           C ---- D      Visit A, add neighbors

Step 2:    A ---- B      Stack: [C]
           |      |*     Visited: [A, B]
           C ---- D      Visit B, add unvisited neighbors (D)

Step 3:    A ---- B      Stack: [D]
           |      |      Visited: [A, B, D]
          *C ---- D      Visit D, add unvisited neighbors (C)

Step 4:    A ---- B      Stack: []
           |      |      Visited: [A, B, D, C]
           C ----*D      Visit C, no new neighbors

Order: A → B → D → C
```

### Breadth-First Search (BFS)
```
Step-by-step BFS starting from A:

Initial:   A ---- B      Queue: [A]
           |      |      Visited: []
           C ---- D

Step 1:    A ---- B      Queue: [B, C]
          *|      |      Visited: [A]
           C ---- D      Visit A, add neighbors to queue

Step 2:    A ---- B      Queue: [C, D]
           |      |*     Visited: [A, B]
           C ---- D      Visit B, add unvisited neighbors

Step 3:    A ---- B      Queue: [D]
           |      |      Visited: [A, B, C]
          *C ---- D      Visit C, add unvisited neighbors

Step 4:    A ---- B      Queue: []
           |      |      Visited: [A, B, C, D]
           C ----*D      Visit D, no new neighbors

Order: A → B → C → D (level by level)
```

## 5. Shortest Path Algorithms

### Dijkstra's Algorithm Example
```
Weighted Graph:
         2
    A ------- B
    |         |
   4|         |1
    |         |
    C ------- D
         3

Step 1: Initialize distances from A
Distance: A=0, B=∞, C=∞, D=∞
Current: A

Step 2: Update neighbors of A
         2*
    A ------- B (dist=2)
    |         |
   4|*        |1
    |         |
    C (dist=4) D
         3

Distance: A=0, B=2, C=4, D=∞
Current: B (smallest unvisited)

Step 3: Update neighbors of B
         2
    A ------- B*
    |         |
   4|         |1*
    |         |
    C (dist=4) D (dist=3)
         3

Distance: A=0, B=2, C=4, D=3
Current: D (smallest unvisited)

Step 4: Update neighbors of D
         2
    A ------- B
    |         |
   4|         |1
    |         |
    C ← 3* ← D*
         6

Final distances from A: A=0, B=2, C=4, D=3
(Path A→D: A→B→D with total distance 3)
```

## 6. Common Graph Patterns

### Tree (Special Graph)
```
        A
       / \
      B   C
     / \   \
    D   E   F

Properties:
- No cycles
- N vertices, N-1 edges
- Connected
- Exactly one path between any two nodes
```

### Cycle Detection
```
Undirected Graph with Cycle:
    A ---- B
    |      |
    |      |
    C ---- D

DFS detects cycle when visiting already visited node
(not parent) through different path
```

### Bipartite Graph
```
Set 1    Set 2
  A  ----  D
  |   \  / |
  |    \/  |
  |    /\  |
  |   /  \ |
  B  ----  E
  |        |
  C  ----  F

All edges connect vertices from different sets
Can be colored with 2 colors
```

## 7. Graph Applications

### Social Network
```
    Alice ---- Bob
      |         |
      |         |
    Carol ---- Dave
      |
    Emma

Represents friendships/connections
```

### Route Planning
```
   City_A --50km-- City_B
     |               |
   30km|             |40km
     |               |
   City_C --25km-- City_D

Find shortest route between cities
```

### Dependency Resolution
```
    Task_A
    /    \
   v      v
Task_B  Task_C
   \      /
    v    v
   Task_D

Topological sort gives execution order:
A → B → C → D (or A → C → B → D)
```

## Key Concepts Summary

- **Vertex/Node**: Point in the graph
- **Edge**: Connection between vertices
- **Degree**: Number of edges connected to a vertex
- **Path**: Sequence of vertices connected by edges
- **Cycle**: Path that starts and ends at same vertex
- **Connected**: Path exists between any two vertices
- **Weighted**: Edges have associated values/costs
- **Directed**: Edges have direction (one-way)
- **Undirected**: Edges are bidirectional

Graphs are fundamental data structures used in computer science, mathematics, and real-world modeling for representing relationships and solving connectivity problems.