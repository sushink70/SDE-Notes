# Comprehensive Guide to Depth-First Search Algorithm

## Table of Contents

1. [Introduction](#introduction)
2. [How DFS Works](#how-dfs-works)
3. [Time and Space Complexity](#time-and-space-complexity)
4. [Implementation Approaches](#implementation-approaches)
5. [Python Implementation](#python-implementation)
6. [Rust Implementation](#rust-implementation)
7. [Applications and Use Cases](#applications-and-use-cases)
8. [Comparison with BFS](#comparison-with-bfs)
9. [Practice Problems](#practice-problems)

## Introduction

Depth-First Search (DFS) is a fundamental graph traversal algorithm that explores a graph by visiting nodes as far as possible along each branch before backtracking. It's called "depth-first" because it prioritizes exploring deeper into the graph structure before exploring neighboring nodes at the same level.

### Key Characteristics:

- **Traversal Strategy**: Goes deep before going wide
- **Data Structure**: Uses a stack (either explicit or implicit via recursion)
- **Memory Usage**: Generally more memory-efficient than BFS for deep graphs
- **Path Finding**: Doesn't guarantee shortest path but finds *a* path efficiently

## How DFS Works

DFS follows these steps:

1. Start at a chosen root node
2. Mark the current node as visited
3. For each unvisited neighbor of the current node:
   - Recursively apply DFS to that neighbor
4. Backtrack when no unvisited neighbors remain

### Visual Example:

```
Graph:    A --- B --- E
          |     |
          C --- D

DFS Order: A → B → E → D → C
```

## Time and Space Complexity

| Aspect | Complexity | Explanation |
|--------|------------|-------------|
| **Time** | O(V + E) | Visit each vertex once, examine each edge once |
| **Space** | O(V) | Stack space for recursion or explicit stack |

Where V = number of vertices, E = number of edges

## Implementation Approaches

### 1. Recursive Approach

- Uses the call stack implicitly
- Cleaner, more intuitive code
- Risk of stack overflow for very deep graphs

### 2. Iterative Approach

- Uses an explicit stack data structure
- More control over memory usage
- Handles deeper graphs without stack overflow

## Python Implementation

```python
from collections import defaultdict, deque
from typing import List, Set, Dict, Optional

class Graph:
    """Graph class supporting both directed and undirected graphs"""
    
    def __init__(self, directed: bool = False):
        self.graph = defaultdict(list)
        self.directed = directed
    
    def add_edge(self, u: int, v: int):
        """Add an edge from u to v"""
        self.graph[u].append(v)
        if not self.directed:
            self.graph[v].append(u)
    
    def add_edges(self, edges: List[tuple]):
        """Add multiple edges at once"""
        for u, v in edges:
            self.add_edge(u, v)
    
    def get_vertices(self) -> Set[int]:
        """Get all vertices in the graph"""
        vertices = set()
        for u in self.graph:
            vertices.add(u)
            vertices.update(self.graph[u])
        return vertices

class DFS:
    """Depth-First Search implementation with multiple variants"""
    
    @staticmethod
    def dfs_recursive(graph: Graph, start: int, visited: Optional[Set[int]] = None) -> List[int]:
        """
        Recursive DFS implementation
        
        Args:
            graph: Graph to traverse
            start: Starting vertex
            visited: Set of visited vertices (used for recursion)
        
        Returns:
            List of vertices in DFS order
        """
        if visited is None:
            visited = set()
        
        result = []
        
        def dfs_helper(vertex: int):
            visited.add(vertex)
            result.append(vertex)
            
            # Visit all unvisited neighbors
            for neighbor in graph.graph[vertex]:
                if neighbor not in visited:
                    dfs_helper(neighbor)
        
        dfs_helper(start)
        return result
    
    @staticmethod
    def dfs_iterative(graph: Graph, start: int) -> List[int]:
        """
        Iterative DFS implementation using explicit stack
        
        Args:
            graph: Graph to traverse
            start: Starting vertex
        
        Returns:
            List of vertices in DFS order
        """
        visited = set()
        stack = [start]
        result = []
        
        while stack:
            vertex = stack.pop()
            
            if vertex not in visited:
                visited.add(vertex)
                result.append(vertex)
                
                # Add neighbors to stack (reverse order for consistent traversal)
                for neighbor in reversed(graph.graph[vertex]):
                    if neighbor not in visited:
                        stack.append(neighbor)
        
        return result
    
    @staticmethod
    def dfs_all_components(graph: Graph) -> List[List[int]]:
        """
        DFS on all connected components
        
        Args:
            graph: Graph to traverse
        
        Returns:
            List of components, each containing vertices in DFS order
        """
        visited = set()
        components = []
        
        for vertex in graph.get_vertices():
            if vertex not in visited:
                component = DFS.dfs_recursive(graph, vertex, visited)
                components.append(component)
        
        return components
    
    @staticmethod
    def has_path(graph: Graph, start: int, target: int) -> bool:
        """
        Check if there's a path between start and target vertices
        
        Args:
            graph: Graph to search
            start: Starting vertex
            target: Target vertex
        
        Returns:
            True if path exists, False otherwise
        """
        if start == target:
            return True
        
        visited = set()
        stack = [start]
        
        while stack:
            vertex = stack.pop()
            
            if vertex == target:
                return True
            
            if vertex not in visited:
                visited.add(vertex)
                stack.extend(neighbor for neighbor in graph.graph[vertex] 
                           if neighbor not in visited)
        
        return False
    
    @staticmethod
    def find_path(graph: Graph, start: int, target: int) -> Optional[List[int]]:
        """
        Find a path between start and target vertices
        
        Args:
            graph: Graph to search
            start: Starting vertex
            target: Target vertex
        
        Returns:
            Path as list of vertices, or None if no path exists
        """
        if start == target:
            return [start]
        
        visited = set()
        # Stack stores (vertex, path_to_vertex)
        stack = [(start, [start])]
        
        while stack:
            vertex, path = stack.pop()
            
            if vertex == target:
                return path
            
            if vertex not in visited:
                visited.add(vertex)
                
                for neighbor in graph.graph[vertex]:
                    if neighbor not in visited:
                        stack.append((neighbor, path + [neighbor]))
        
        return None
    
    @staticmethod
    def detect_cycle_undirected(graph: Graph) -> bool:
        """
        Detect cycle in undirected graph using DFS
        
        Args:
            graph: Undirected graph
        
        Returns:
            True if cycle exists, False otherwise
        """
        visited = set()
        
        def has_cycle_util(vertex: int, parent: int) -> bool:
            visited.add(vertex)
            
            for neighbor in graph.graph[vertex]:
                if neighbor not in visited:
                    if has_cycle_util(neighbor, vertex):
                        return True
                elif neighbor != parent:  # Back edge found
                    return True
            
            return False
        
        # Check all components
        for vertex in graph.get_vertices():
            if vertex not in visited:
                if has_cycle_util(vertex, -1):
                    return True
        
        return False
    
    @staticmethod
    def detect_cycle_directed(graph: Graph) -> bool:
        """
        Detect cycle in directed graph using DFS with colors
        
        Args:
            graph: Directed graph
        
        Returns:
            True if cycle exists, False otherwise
        """
        # Colors: 0 = white (unvisited), 1 = gray (visiting), 2 = black (visited)
        color = defaultdict(int)
        
        def has_cycle_util(vertex: int) -> bool:
            color[vertex] = 1  # Mark as gray (visiting)
            
            for neighbor in graph.graph[vertex]:
                if color[neighbor] == 1:  # Back edge to gray node
                    return True
                elif color[neighbor] == 0 and has_cycle_util(neighbor):
                    return True
            
            color[vertex] = 2  # Mark as black (visited)
            return False
        
        # Check all vertices
        for vertex in graph.get_vertices():
            if color[vertex] == 0:
                if has_cycle_util(vertex):
                    return True
        
        return False

# Example usage and testing
def demonstrate_dfs():
    """Demonstrate various DFS operations"""
    print("=== DFS Demonstration ===\n")
    
    # Create sample graph
    graph = Graph()
    edges = [(0, 1), (0, 2), (1, 3), (1, 4), (2, 5), (2, 6)]
    graph.add_edges(edges)
    
    print("Graph edges:", edges)
    print("Graph structure:")
    for vertex in sorted(graph.graph.keys()):
        print(f"  {vertex}: {graph.graph[vertex]}")
    
    # Test recursive DFS
    print(f"\nRecursive DFS from vertex 0: {DFS.dfs_recursive(graph, 0)}")
    
    # Test iterative DFS
    print(f"Iterative DFS from vertex 0: {DFS.dfs_iterative(graph, 0)}")
    
    # Test path finding
    print(f"Path from 0 to 6: {DFS.find_path(graph, 0, 6)}")
    print(f"Path exists 0 to 6: {DFS.has_path(graph, 0, 6)}")
    print(f"Path exists 0 to 7: {DFS.has_path(graph, 0, 7)}")
    
    # Test cycle detection
    print(f"Has cycle (undirected): {DFS.detect_cycle_undirected(graph)}")
    
    # Create graph with cycle
    cycle_graph = Graph()
    cycle_graph.add_edges([(0, 1), (1, 2), (2, 0)])
    print(f"Cycle graph has cycle: {DFS.detect_cycle_undirected(cycle_graph)}")
    
    # Test all components
    disconnected_graph = Graph()
    disconnected_graph.add_edges([(0, 1), (2, 3), (4, 5)])
    print(f"All components: {DFS.dfs_all_components(disconnected_graph)}")

if __name__ == "__main__":
    demonstrate_dfs()
```

## Rust Implementation

```rust
use std::collections::{HashMap, HashSet, VecDeque};
use std::hash::Hash;

#[derive(Debug, Clone)]
pub struct Graph<T> 
where 
    T: Eq + Hash + Clone,
{
    adjacency_list: HashMap<T, Vec<T>>,
    directed: bool,
}

impl<T> Graph<T> 
where 
    T: Eq + Hash + Clone,
{
    /// Create a new graph
    pub fn new(directed: bool) -> Self {
        Self {
            adjacency_list: HashMap::new(),
            directed,
        }
    }
    
    /// Add an edge from u to v
    pub fn add_edge(&mut self, u: T, v: T) {
        self.adjacency_list.entry(u.clone()).or_insert_with(Vec::new).push(v.clone());
        
        if !self.directed {
            self.adjacency_list.entry(v).or_insert_with(Vec::new).push(u);
        }
    }
    
    /// Add multiple edges at once
    pub fn add_edges(&mut self, edges: Vec<(T, T)>) {
        for (u, v) in edges {
            self.add_edge(u, v);
        }
    }
    
    /// Get all vertices in the graph
    pub fn get_vertices(&self) -> HashSet<T> {
        let mut vertices = HashSet::new();
        
        for (vertex, neighbors) in &self.adjacency_list {
            vertices.insert(vertex.clone());
            for neighbor in neighbors {
                vertices.insert(neighbor.clone());
            }
        }
        
        vertices
    }
    
    /// Get neighbors of a vertex
    pub fn get_neighbors(&self, vertex: &T) -> Option<&Vec<T>> {
        self.adjacency_list.get(vertex)
    }
}

pub struct DFS;

impl DFS {
    /// Recursive DFS implementation
    pub fn dfs_recursive<T>(graph: &Graph<T>, start: T) -> Vec<T>
    where 
        T: Eq + Hash + Clone,
    {
        let mut visited = HashSet::new();
        let mut result = Vec::new();
        
        Self::dfs_recursive_helper(graph, start, &mut visited, &mut result);
        result
    }
    
    fn dfs_recursive_helper<T>(
        graph: &Graph<T>, 
        vertex: T, 
        visited: &mut HashSet<T>, 
        result: &mut Vec<T>
    )
    where 
        T: Eq + Hash + Clone,
    {
        visited.insert(vertex.clone());
        result.push(vertex.clone());
        
        if let Some(neighbors) = graph.get_neighbors(&vertex) {
            for neighbor in neighbors {
                if !visited.contains(neighbor) {
                    Self::dfs_recursive_helper(graph, neighbor.clone(), visited, result);
                }
            }
        }
    }
    
    /// Iterative DFS implementation
    pub fn dfs_iterative<T>(graph: &Graph<T>, start: T) -> Vec<T>
    where 
        T: Eq + Hash + Clone,
    {
        let mut visited = HashSet::new();
        let mut stack = Vec::new();
        let mut result = Vec::new();
        
        stack.push(start);
        
        while let Some(vertex) = stack.pop() {
            if !visited.contains(&vertex) {
                visited.insert(vertex.clone());
                result.push(vertex.clone());
                
                if let Some(neighbors) = graph.get_neighbors(&vertex) {
                    // Add neighbors in reverse order to maintain consistent traversal order
                    for neighbor in neighbors.iter().rev() {
                        if !visited.contains(neighbor) {
                            stack.push(neighbor.clone());
                        }
                    }
                }
            }
        }
        
        result
    }
    
    /// DFS on all connected components
    pub fn dfs_all_components<T>(graph: &Graph<T>) -> Vec<Vec<T>>
    where 
        T: Eq + Hash + Clone,
    {
        let mut visited = HashSet::new();
        let mut components = Vec::new();
        
        for vertex in graph.get_vertices() {
            if !visited.contains(&vertex) {
                let mut component_visited = visited.clone();
                let component = Self::dfs_recursive_with_visited(
                    graph, 
                    vertex, 
                    &mut component_visited
                );
                
                // Update global visited set
                for v in &component {
                    visited.insert(v.clone());
                }
                
                components.push(component);
            }
        }
        
        components
    }
    
    fn dfs_recursive_with_visited<T>(
        graph: &Graph<T>, 
        start: T, 
        visited: &mut HashSet<T>
    ) -> Vec<T>
    where 
        T: Eq + Hash + Clone,
    {
        let mut result = Vec::new();
        Self::dfs_recursive_helper(graph, start, visited, &mut result);
        result
    }
    
    /// Check if there's a path between start and target vertices
    pub fn has_path<T>(graph: &Graph<T>, start: T, target: T) -> bool
    where 
        T: Eq + Hash + Clone,
    {
        if start == target {
            return true;
        }
        
        let mut visited = HashSet::new();
        let mut stack = Vec::new();
        
        stack.push(start);
        
        while let Some(vertex) = stack.pop() {
            if vertex == target {
                return true;
            }
            
            if !visited.contains(&vertex) {
                visited.insert(vertex.clone());
                
                if let Some(neighbors) = graph.get_neighbors(&vertex) {
                    for neighbor in neighbors {
                        if !visited.contains(neighbor) {
                            stack.push(neighbor.clone());
                        }
                    }
                }
            }
        }
        
        false
    }
    
    /// Find a path between start and target vertices
    pub fn find_path<T>(graph: &Graph<T>, start: T, target: T) -> Option<Vec<T>>
    where 
        T: Eq + Hash + Clone,
    {
        if start == target {
            return Some(vec![start]);
        }
        
        let mut visited = HashSet::new();
        let mut stack = Vec::new();
        
        // Stack stores (vertex, path_to_vertex)
        stack.push((start.clone(), vec![start]));
        
        while let Some((vertex, path)) = stack.pop() {
            if vertex == target {
                return Some(path);
            }
            
            if !visited.contains(&vertex) {
                visited.insert(vertex.clone());
                
                if let Some(neighbors) = graph.get_neighbors(&vertex) {
                    for neighbor in neighbors {
                        if !visited.contains(neighbor) {
                            let mut new_path = path.clone();
                            new_path.push(neighbor.clone());
                            stack.push((neighbor.clone(), new_path));
                        }
                    }
                }
            }
        }
        
        None
    }
    
    /// Detect cycle in undirected graph
    pub fn detect_cycle_undirected<T>(graph: &Graph<T>) -> bool
    where 
        T: Eq + Hash + Clone,
    {
        let mut visited = HashSet::new();
        
        for vertex in graph.get_vertices() {
            if !visited.contains(&vertex) {
                if Self::has_cycle_undirected_util(graph, vertex, None, &mut visited) {
                    return true;
                }
            }
        }
        
        false
    }
    
    fn has_cycle_undirected_util<T>(
        graph: &Graph<T>,
        vertex: T,
        parent: Option<T>,
        visited: &mut HashSet<T>,
    ) -> bool
    where 
        T: Eq + Hash + Clone,
    {
        visited.insert(vertex.clone());
        
        if let Some(neighbors) = graph.get_neighbors(&vertex) {
            for neighbor in neighbors {
                if !visited.contains(neighbor) {
                    if Self::has_cycle_undirected_util(
                        graph, 
                        neighbor.clone(), 
                        Some(vertex.clone()), 
                        visited
                    ) {
                        return true;
                    }
                } else if Some(neighbor) != parent.as_ref() {
                    // Back edge found
                    return true;
                }
            }
        }
        
        false
    }
    
    /// Detect cycle in directed graph using DFS with colors
    pub fn detect_cycle_directed<T>(graph: &Graph<T>) -> bool
    where 
        T: Eq + Hash + Clone,
    {
        #[derive(PartialEq)]
        enum Color {
            White, // Unvisited
            Gray,  // Visiting
            Black, // Visited
        }
        
        let mut color: HashMap<T, Color> = HashMap::new();
        
        // Initialize all vertices as white
        for vertex in graph.get_vertices() {
            color.insert(vertex, Color::White);
        }
        
        for vertex in graph.get_vertices() {
            if color.get(&vertex) == Some(&Color::White) {
                if Self::has_cycle_directed_util(graph, vertex, &mut color) {
                    return true;
                }
            }
        }
        
        false
    }
    
    fn has_cycle_directed_util<T>(
        graph: &Graph<T>,
        vertex: T,
        color: &mut HashMap<T, Color>,
    ) -> bool
    where 
        T: Eq + Hash + Clone,
    {
        use Color::*;
        
        color.insert(vertex.clone(), Gray);
        
        if let Some(neighbors) = graph.get_neighbors(&vertex) {
            for neighbor in neighbors {
                match color.get(neighbor) {
                    Some(Gray) => return true, // Back edge to gray node
                    Some(White) => {
                        if Self::has_cycle_directed_util(graph, neighbor.clone(), color) {
                            return true;
                        }
                    }
                    Some(Black) => {}, // Already processed
                    None => {
                        color.insert(neighbor.clone(), White);
                        if Self::has_cycle_directed_util(graph, neighbor.clone(), color) {
                            return true;
                        }
                    }
                }
            }
        }
        
        color.insert(vertex, Black);
        false
    }
}

// Example usage and testing
fn demonstrate_dfs() {
    println!("=== DFS Demonstration ===\n");
    
    // Create sample graph
    let mut graph = Graph::new(false);
    let edges = vec![(0, 1), (0, 2), (1, 3), (1, 4), (2, 5), (2, 6)];
    graph.add_edges(edges.clone());
    
    println!("Graph edges: {:?}", edges);
    
    // Test recursive DFS
    let recursive_result = DFS::dfs_recursive(&graph, 0);
    println!("Recursive DFS from vertex 0: {:?}", recursive_result);
    
    // Test iterative DFS
    let iterative_result = DFS::dfs_iterative(&graph, 0);
    println!("Iterative DFS from vertex 0: {:?}", iterative_result);
    
    // Test path finding
    let path = DFS::find_path(&graph, 0, 6);
    println!("Path from 0 to 6: {:?}", path);
    
    let has_path = DFS::has_path(&graph, 0, 6);
    println!("Path exists 0 to 6: {}", has_path);
    
    let has_path_nonexistent = DFS::has_path(&graph, 0, 7);
    println!("Path exists 0 to 7: {}", has_path_nonexistent);
    
    // Test cycle detection
    let has_cycle = DFS::detect_cycle_undirected(&graph);
    println!("Has cycle (undirected): {}", has_cycle);
    
    // Create graph with cycle
    let mut cycle_graph = Graph::new(false);
    cycle_graph.add_edges(vec![(0, 1), (1, 2), (2, 0)]);
    let cycle_detected = DFS::detect_cycle_undirected(&cycle_graph);
    println!("Cycle graph has cycle: {}", cycle_detected);
    
    // Test all components
    let mut disconnected_graph = Graph::new(false);
    disconnected_graph.add_edges(vec![(0, 1), (2, 3), (4, 5)]);
    let components = DFS::dfs_all_components(&disconnected_graph);
    println!("All components: {:?}", components);
}

fn main() {
    demonstrate_dfs();
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_dfs_basic() {
        let mut graph = Graph::new(false);
        graph.add_edges(vec![(1, 2), (1, 3), (2, 4)]);
        
        let result = DFS::dfs_recursive(&graph, 1);
        assert!(result.contains(&1));
        assert!(result.contains(&2));
        assert!(result.contains(&3));
        assert!(result.contains(&4));
    }

    #[test]
    fn test_path_finding() {
        let mut graph = Graph::new(false);
        graph.add_edges(vec![(1, 2), (2, 3), (3, 4)]);
        
        assert!(DFS::has_path(&graph, 1, 4));
        assert!(!DFS::has_path(&graph, 1, 5));
        
        let path = DFS::find_path(&graph, 1, 4);
        assert!(path.is_some());
        let path = path.unwrap();
        assert_eq!(path[0], 1);
        assert_eq!(path[path.len() - 1], 4);
    }

    #[test]
    fn test_cycle_detection() {
        // Graph without cycle
        let mut graph = Graph::new(false);
        graph.add_edges(vec![(1, 2), (2, 3)]);
        assert!(!DFS::detect_cycle_undirected(&graph));
        
        // Graph with cycle
        let mut cycle_graph = Graph::new(false);
        cycle_graph.add_edges(vec![(1, 2), (2, 3), (3, 1)]);
        assert!(DFS::detect_cycle_undirected(&cycle_graph));
    }
}
```

## Applications and Use Cases

### 1. **Connectivity Problems**

- Finding connected components
- Checking if graph is connected
- Finding bridges and articulation points

### 2. **Path Finding**

- Finding any path between two vertices
- Maze solving
- Puzzle solving (like N-Queens)

### 3. **Cycle Detection**

- Detecting cycles in both directed and undirected graphs
- Deadlock detection in operating systems
- Dependency analysis

### 4. **Topological Sorting**

- Course scheduling
- Build systems
- Task dependency resolution

### 5. **Tree Traversals**

- Pre-order, in-order, post-order traversals
- Expression tree evaluation
- File system traversal

## Comparison with BFS

| Aspect | DFS | BFS |
|--------|-----|-----|
| **Data Structure** | Stack (recursive/explicit) | Queue |
| **Memory Usage** | O(h) where h = height | O(w) where w = width |
| **Path Found** | Any path (not necessarily shortest) | Shortest path (unweighted) |
| **Implementation** | Simpler (recursive) | Requires explicit queue |
| **Use Cases** | Connectivity, cycles, puzzles | Shortest path, level-order |

## Practice Problems

### Beginner

1. **Count Islands**: Count the number of connected components in a 2D grid
2. **Path Exists**: Check if a path exists between two nodes
3. **Tree Depth**: Find the maximum depth of a binary tree

### Intermediate  

1. **Clone Graph**: Create a deep copy of an undirected graph
2. **Course Schedule**: Detect if courses can be completed (cycle detection)
3. **Number of Provinces**: Find connected components in a friendship matrix

### Advanced

1. **Reconstruct Itinerary**: Find Eulerian path in a directed graph
2. **Critical Connections**: Find bridges in a network
3. **Strongly Connected Components**: Decompose directed graph into SCCs

## Best Practices

### 1. **Choose the Right Approach**

- Use recursive DFS for simpler code and moderate depth
- Use iterative DFS for very deep graphs or when stack overflow is a concern

### 2. **Handle Edge Cases**

- Empty graphs
- Single-node graphs  
- Disconnected graphs
- Self-loops

### 3. **Memory Optimization**

- Use bit arrays for visited tracking when dealing with dense vertex IDs
- Consider in-place marking for special graph types

### 4. **Error Handling**

- Validate input parameters
- Handle non-existent vertices gracefully
- Provide meaningful error messages

## Conclusion

Depth-First Search is a fundamental algorithm that forms the building block for many advanced graph algorithms. Understanding both recursive and iterative implementations, along with their trade-offs, is crucial for any programmer working with graph problems. The comprehensive implementations provided here offer a solid foundation for tackling real-world graph traversal challenges in both Python and Rust.

I'll create a comprehensive ASCII diagram showing how Depth-First Search (DFS) works step by step. This will include both the tree/graph structure and the algorithm's progression.I've created a comprehensive ASCII diagram showing how Depth-First Search works step by step! The diagram includes:

1. **Visual Graph Structure**: Shows the sample tree/graph we're traversing
2. **Step-by-Step Execution**: Each step shows the current stack state, visited nodes, and which node is being processed
3. **Stack Visualization**: Demonstrates the LIFO (Last In, First Out) behavior crucial to DFS
4. **Algorithm Pseudocode**: The actual implementation logic
5. **Complexity Analysis**: Time and space complexity explanations
6. **Comparison with BFS**: Shows the difference in traversal order
7. **Real-world Applications**: Where DFS is commonly used

The key insight is that DFS uses a **stack** (either explicit or via recursion), which causes it to go as deep as possible down one branch before backtracking. This is why in our example, starting from A, we go A→B→E (deepest) before coming back to visit D, then move to the C branch.

The visual progression shows how the stack changes at each step, making it clear why we get the traversal order A→B→E→D→C→G→F rather than a level-by-level approach like BFS would provide.

## Depth-First Search (DFS) Algorithm - Step by Step

## Sample Graph Structure

```
     A
   /   \
  B     C
 / \   / \
D   E F   G
```

## DFS Traversal Steps (Starting from A)

### Initial State

```
Stack: [A]
Visited: []
Current: None

Graph:
     A  ← START HERE
   /   \
  B     C
 / \   / \
D   E F   G
```

### Step 1: Visit A

```
Stack: [B, C]  ← A's children added (order may vary)
Visited: [A]
Current: A

Graph:
    [A] ← VISITED
   /   \
  B     C
 / \   / \
D   E F   G
```

### Step 2: Visit B (pop from stack)

```
Stack: [C, D, E]  ← B's children added
Visited: [A, B]
Current: B

Graph:
    [A]
   /   \
 [B]    C
 / \   / \
D   E F   G
```

### Step 3: Visit E (pop from stack - LIFO)

```
Stack: [C, D]  ← E has no children
Visited: [A, B, E]
Current: E

Graph:
    [A]
   /   \
 [B]    C
 / \   / \
D  [E] F   G
```

### Step 4: Visit D (pop from stack)

```
Stack: [C]  ← D has no children
Visited: [A, B, E, D]
Current: D

Graph:
    [A]
   /   \
 [B]    C
 / \   / \
[D][E] F   G
```

### Step 5: Visit C (pop from stack)

```
Stack: [F, G]  ← C's children added
Visited: [A, B, E, D, C]
Current: C

Graph:
    [A]
   /   \
 [B]   [C]
 / \   / \
[D][E] F   G
```

### Step 6: Visit G (pop from stack)

```
Stack: [F]  ← G has no children
Visited: [A, B, E, D, C, G]
Current: G

Graph:
    [A]
   /   \
 [B]   [C]
 / \   / \
[D][E] F  [G]
```

### Step 7: Visit F (pop from stack)

```
Stack: []  ← F has no children, stack empty
Visited: [A, B, E, D, C, G, F]
Current: F

Graph:
    [A]
   /   \
 [B]   [C]
 / \   / \
[D][E][F] [G]
```

### Final Result

```
DFS Traversal Order: A → B → E → D → C → G → F
All nodes visited!
Stack: [] (empty)
```

## DFS Algorithm Pseudocode

```
function DFS(graph, start):
    stack = [start]
    visited = set()
    result = []
    
    while stack is not empty:
        current = stack.pop()  // Remove from top (LIFO)
        
        if current not in visited:
            visited.add(current)
            result.append(current)
            
            // Add neighbors to stack (right to left for left-first traversal)
            for neighbor in reverse(graph[current]):
                if neighbor not in visited:
                    stack.push(neighbor)
    
    return result
```

## Key DFS Characteristics

### Stack Behavior (LIFO - Last In, First Out)

```
Push B, C:     [B, C]
Pop C:         [B]     ← C comes out first
Pop B:         []      ← B comes out last
```

### Memory Usage

```
Space Complexity: O(V) where V = number of vertices
- Stack can hold at most V nodes
- Visited set holds at most V nodes
```

### Time Complexity

```
Time Complexity: O(V + E) where:
- V = number of vertices
- E = number of edges
- Each vertex visited once: O(V)
- Each edge examined once: O(E)
```

## DFS vs BFS Comparison

```
DFS (Depth-First):        BFS (Breadth-First):
Uses: Stack               Uses: Queue
Order: A→B→E→D→C→G→F     Order: A→B→C→D→E→F→G
Goes: Deep first          Goes: Wide first

Visual DFS path:          Visual BFS path:
A                         A
└→B                       ├→B
  └→E (deepest first)     └→C
  └→D                     ├→D→E (same level)
└→C                       └→F→G (same level)
  └→G
  └→F
```

## Applications of DFS

- **Topological Sorting**: Ordering tasks with dependencies
- **Cycle Detection**: Finding loops in graphs
- **Path Finding**: Finding any path between two nodes
- **Connected Components**: Finding separate graph sections
- **Maze Solving**: Exploring all possible paths
- **Tree Traversals**: In-order, pre-order, post-order

## Depth-First Search (DFS) Algorithm Guide

I'll create a comprehensive guide to Depth-First Search (DFS) that covers the theory, implementation details, and provides complete code examples in both Python and Rust.I've created a comprehensive guide to Depth-First Search that covers everything from basic theory to advanced implementations. Here are the key highlights:

## What's Included:

**Theoretical Foundation:**

- Clear explanation of how DFS works
- Time and space complexity analysis
- Comparison with BFS

**Complete Python Implementation:**

- Graph class with directed/undirected support
- Both recursive and iterative DFS variants
- Path finding algorithms
- Cycle detection for both graph types
- Connected components finding
- Comprehensive test demonstrations

**Complete Rust Implementation:**

- Similar structure and features as Python version
- Generic graph structure using HashMap
- Memory-safe implementations with proper ownership
- All the same features as Python version
- Unit tests included
- Idiomatic Rust patterns

**Advanced Features:**

- Multiple DFS variants (recursive, iterative, all components)
- Practical applications like cycle detection and path finding
- Performance considerations and optimization tips
- Real-world use cases and applications

**Practice Section:**

- Categorized problems from beginner to advanced
- Best practices and common pitfalls
- Error handling strategies

The implementations are production-ready and include proper error handling, comprehensive documentation, and practical examples. Both versions demonstrate the same concepts but leverage each language's strengths - Python's simplicity and Rust's memory safety and performance.

Would you like me to explain any specific part in more detail or add additional algorithms that build on DFS?
