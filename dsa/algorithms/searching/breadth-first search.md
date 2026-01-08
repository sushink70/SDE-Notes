# Comprehensive Guide to Breadth-First Search Algorithm

## Table of Contents

1. [Introduction](#introduction)
2. [How BFS Works](#how-bfs-works)
3. [Time and Space Complexity](#time-and-space-complexity)
4. [Python Implementation](#python-implementation)
5. [Rust Implementation](#rust-implementation)
6. [Use Cases and Applications](#use-cases-and-applications)
7. [Variations and Extensions](#variations-and-extensions)
8. [Performance Considerations](#performance-considerations)

## Introduction

Breadth-First Search (BFS) is a fundamental graph traversal algorithm that explores vertices in a graph level by level. Starting from a source vertex, BFS visits all vertices at distance 1, then all vertices at distance 2, and so on. This systematic exploration makes BFS particularly useful for finding the shortest path in unweighted graphs.

### Key Characteristics:

- **Complete**: Finds a solution if one exists
- **Optimal**: Finds the shortest path in unweighted graphs
- **Memory Intensive**: Stores all nodes at the current level
- **Queue-Based**: Uses FIFO (First In, First Out) data structure

## How BFS Works

The algorithm follows these steps:

1. **Initialize**: Create a queue and add the starting vertex
2. **Mark as Visited**: Keep track of visited vertices to avoid cycles
3. **Process Current Level**: 
   - Dequeue a vertex from the front
   - Process/visit the vertex
   - Add all unvisited neighbors to the queue
4. **Repeat**: Continue until the queue is empty or target is found

### Visual Example

```
Graph:     A
          / \
         B   C
        /   / \
       D   E   F

BFS Traversal: A → B → C → D → E → F
Queue states:
Initial: [A]
Step 1:  [B, C]     (visited A, added its neighbors)
Step 2:  [C, D]     (visited B, added its neighbors)
Step 3:  [D, E, F]  (visited C, added its neighbors)
Step 4:  [E, F]     (visited D)
Step 5:  [F]        (visited E)
Step 6:  []         (visited F, queue empty)
```

## Time and Space Complexity

- **Time Complexity**: O(V + E)
  - V = number of vertices
  - E = number of edges
  - Each vertex and edge is processed once

- **Space Complexity**: O(V)
  - Queue can contain at most all vertices
  - Visited set stores all vertices

## Python Implementation

```python
from collections import deque
from typing import List, Dict, Set, Optional, Tuple

class Graph:
    """Graph class supporting both directed and undirected graphs"""
    
    def __init__(self, directed: bool = False):
        self.graph: Dict[int, List[int]] = {}
        self.directed = directed
    
    def add_edge(self, u: int, v: int):
        """Add an edge between vertices u and v"""
        if u not in self.graph:
            self.graph[u] = []
        if v not in self.graph:
            self.graph[v] = []
        
        self.graph[u].append(v)
        if not self.directed:
            self.graph[v].append(u)
    
    def get_neighbors(self, vertex: int) -> List[int]:
        """Get all neighbors of a vertex"""
        return self.graph.get(vertex, [])
    
    def get_vertices(self) -> Set[int]:
        """Get all vertices in the graph"""
        return set(self.graph.keys())

def bfs_traversal(graph: Graph, start: int) -> List[int]:
    """
    Perform BFS traversal starting from the given vertex
    
    Args:
        graph: Graph object
        start: Starting vertex
    
    Returns:
        List of vertices in BFS order
    """
    if start not in graph.get_vertices():
        return []
    
    visited: Set[int] = set()
    queue: deque = deque([start])
    result: List[int] = []
    
    visited.add(start)
    
    while queue:
        vertex = queue.popleft()
        result.append(vertex)
        
        # Add all unvisited neighbors to queue
        for neighbor in graph.get_neighbors(vertex):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    
    return result

def bfs_shortest_path(graph: Graph, start: int, target: int) -> Optional[List[int]]:
    """
    Find shortest path between start and target using BFS
    
    Args:
        graph: Graph object
        start: Starting vertex
        target: Target vertex
    
    Returns:
        Shortest path as list of vertices, or None if no path exists
    """
    if start == target:
        return [start]
    
    if start not in graph.get_vertices() or target not in graph.get_vertices():
        return None
    
    visited: Set[int] = set()
    queue: deque = deque([(start, [start])])  # (vertex, path)
    visited.add(start)
    
    while queue:
        vertex, path = queue.popleft()
        
        for neighbor in graph.get_neighbors(vertex):
            if neighbor == target:
                return path + [neighbor]
            
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    
    return None

def bfs_distance(graph: Graph, start: int, target: int) -> int:
    """
    Find shortest distance between start and target
    
    Returns:
        Distance as number of edges, or -1 if no path exists
    """
    if start == target:
        return 0
    
    if start not in graph.get_vertices() or target not in graph.get_vertices():
        return -1
    
    visited: Set[int] = set()
    queue: deque = deque([(start, 0)])  # (vertex, distance)
    visited.add(start)
    
    while queue:
        vertex, distance = queue.popleft()
        
        for neighbor in graph.get_neighbors(vertex):
            if neighbor == target:
                return distance + 1
            
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, distance + 1))
    
    return -1

def bfs_level_order(graph: Graph, start: int) -> List[List[int]]:
    """
    Return vertices grouped by their distance from start
    
    Returns:
        List of levels, where each level contains vertices at that distance
    """
    if start not in graph.get_vertices():
        return []
    
    visited: Set[int] = set()
    queue: deque = deque([start])
    visited.add(start)
    levels: List[List[int]] = []
    
    while queue:
        level_size = len(queue)
        current_level = []
        
        for _ in range(level_size):
            vertex = queue.popleft()
            current_level.append(vertex)
            
            for neighbor in graph.get_neighbors(vertex):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        levels.append(current_level)
    
    return levels

# Example usage and testing
if __name__ == "__main__":
    # Create a sample graph
    g = Graph()
    edges = [(0, 1), (0, 2), (1, 3), (1, 4), (2, 5), (2, 6)]
    
    for u, v in edges:
        g.add_edge(u, v)
    
    print("BFS Traversal from vertex 0:")
    print(bfs_traversal(g, 0))
    
    print("\nShortest path from 0 to 6:")
    print(bfs_shortest_path(g, 0, 6))
    
    print("\nDistance from 0 to 6:")
    print(bfs_distance(g, 0, 6))
    
    print("\nLevel order traversal from 0:")
    print(bfs_level_order(g, 0))
```

## Rust Implementation

```rust
use std::collections::{HashMap, HashSet, VecDeque};
use std::hash::Hash;

#[derive(Debug, Clone)]
pub struct Graph<T> {
    adjacency_list: HashMap<T, Vec<T>>,
    directed: bool,
}

impl<T> Graph<T>
where
    T: Clone + Hash + Eq,
{
    /// Create a new graph
    pub fn new(directed: bool) -> Self {
        Graph {
            adjacency_list: HashMap::new(),
            directed,
        }
    }
    
    /// Add an edge between two vertices
    pub fn add_edge(&mut self, u: T, v: T) {
        self.adjacency_list.entry(u.clone()).or_insert_with(Vec::new).push(v.clone());
        
        if !self.directed {
            self.adjacency_list.entry(v).or_insert_with(Vec::new).push(u);
        }
    }
    
    /// Get neighbors of a vertex
    pub fn get_neighbors(&self, vertex: &T) -> Option<&Vec<T>> {
        self.adjacency_list.get(vertex)
    }
    
    /// Get all vertices
    pub fn vertices(&self) -> Vec<&T> {
        self.adjacency_list.keys().collect()
    }
}

/// Perform BFS traversal
pub fn bfs_traversal<T>(graph: &Graph<T>, start: &T) -> Vec<T>
where
    T: Clone + Hash + Eq,
{
    let mut visited = HashSet::new();
    let mut queue = VecDeque::new();
    let mut result = Vec::new();
    
    if graph.get_neighbors(start).is_none() {
        return result;
    }
    
    queue.push_back(start.clone());
    visited.insert(start.clone());
    
    while let Some(vertex) = queue.pop_front() {
        result.push(vertex.clone());
        
        if let Some(neighbors) = graph.get_neighbors(&vertex) {
            for neighbor in neighbors {
                if !visited.contains(neighbor) {
                    visited.insert(neighbor.clone());
                    queue.push_back(neighbor.clone());
                }
            }
        }
    }
    
    result
}

/// Find shortest path using BFS
pub fn bfs_shortest_path<T>(graph: &Graph<T>, start: &T, target: &T) -> Option<Vec<T>>
where
    T: Clone + Hash + Eq,
{
    if start == target {
        return Some(vec![start.clone()]);
    }
    
    if graph.get_neighbors(start).is_none() || graph.get_neighbors(target).is_none() {
        return None;
    }
    
    let mut visited = HashSet::new();
    let mut queue = VecDeque::new();
    
    queue.push_back((start.clone(), vec![start.clone()]));
    visited.insert(start.clone());
    
    while let Some((vertex, path)) = queue.pop_front() {
        if let Some(neighbors) = graph.get_neighbors(&vertex) {
            for neighbor in neighbors {
                if neighbor == target {
                    let mut result_path = path.clone();
                    result_path.push(neighbor.clone());
                    return Some(result_path);
                }
                
                if !visited.contains(neighbor) {
                    visited.insert(neighbor.clone());
                    let mut new_path = path.clone();
                    new_path.push(neighbor.clone());
                    queue.push_back((neighbor.clone(), new_path));
                }
            }
        }
    }
    
    None
}

/// Find shortest distance using BFS
pub fn bfs_distance<T>(graph: &Graph<T>, start: &T, target: &T) -> Option<usize>
where
    T: Clone + Hash + Eq,
{
    if start == target {
        return Some(0);
    }
    
    if graph.get_neighbors(start).is_none() || graph.get_neighbors(target).is_none() {
        return None;
    }
    
    let mut visited = HashSet::new();
    let mut queue = VecDeque::new();
    
    queue.push_back((start.clone(), 0));
    visited.insert(start.clone());
    
    while let Some((vertex, distance)) = queue.pop_front() {
        if let Some(neighbors) = graph.get_neighbors(&vertex) {
            for neighbor in neighbors {
                if neighbor == target {
                    return Some(distance + 1);
                }
                
                if !visited.contains(neighbor) {
                    visited.insert(neighbor.clone());
                    queue.push_back((neighbor.clone(), distance + 1));
                }
            }
        }
    }
    
    None
}

/// BFS level order traversal
pub fn bfs_level_order<T>(graph: &Graph<T>, start: &T) -> Vec<Vec<T>>
where
    T: Clone + Hash + Eq,
{
    let mut visited = HashSet::new();
    let mut queue = VecDeque::new();
    let mut levels = Vec::new();
    
    if graph.get_neighbors(start).is_none() {
        return levels;
    }
    
    queue.push_back(start.clone());
    visited.insert(start.clone());
    
    while !queue.is_empty() {
        let level_size = queue.len();
        let mut current_level = Vec::new();
        
        for _ in 0..level_size {
            if let Some(vertex) = queue.pop_front() {
                current_level.push(vertex.clone());
                
                if let Some(neighbors) = graph.get_neighbors(&vertex) {
                    for neighbor in neighbors {
                        if !visited.contains(neighbor) {
                            visited.insert(neighbor.clone());
                            queue.push_back(neighbor.clone());
                        }
                    }
                }
            }
        }
        
        levels.push(current_level);
    }
    
    levels
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_bfs_traversal() {
        let mut graph = Graph::new(false);
        let edges = vec![(0, 1), (0, 2), (1, 3), (1, 4), (2, 5), (2, 6)];
        
        for (u, v) in edges {
            graph.add_edge(u, v);
        }
        
        let result = bfs_traversal(&graph, &0);
        assert_eq!(result.len(), 7);
        assert_eq!(result[0], 0); // Start vertex should be first
    }
    
    #[test]
    fn test_shortest_path() {
        let mut graph = Graph::new(false);
        graph.add_edge(0, 1);
        graph.add_edge(0, 2);
        graph.add_edge(1, 3);
        graph.add_edge(2, 3);
        
        let path = bfs_shortest_path(&graph, &0, &3);
        assert!(path.is_some());
        assert_eq!(path.unwrap().len(), 3); // 0 -> 1 -> 3 or 0 -> 2 -> 3
    }
    
    #[test]
    fn test_distance() {
        let mut graph = Graph::new(false);
        graph.add_edge(0, 1);
        graph.add_edge(1, 2);
        graph.add_edge(2, 3);
        
        assert_eq!(bfs_distance(&graph, &0, &3), Some(3));
        assert_eq!(bfs_distance(&graph, &0, &0), Some(0));
    }
}

// Example usage
fn main() {
    let mut graph = Graph::new(false);
    let edges = vec![(0, 1), (0, 2), (1, 3), (1, 4), (2, 5), (2, 6)];
    
    for (u, v) in edges {
        graph.add_edge(u, v);
    }
    
    println!("BFS Traversal from vertex 0:");
    println!("{:?}", bfs_traversal(&graph, &0));
    
    println!("\nShortest path from 0 to 6:");
    println!("{:?}", bfs_shortest_path(&graph, &0, &6));
    
    println!("\nDistance from 0 to 6:");
    println!("{:?}", bfs_distance(&graph, &0, &6));
    
    println!("\nLevel order traversal from 0:");
    println!("{:?}", bfs_level_order(&graph, &0));
}
```

## Use Cases and Applications

### 1. Shortest Path in Unweighted Graphs

BFS guarantees finding the shortest path (minimum number of edges) between two vertices.

### 2. Level Order Tree Traversal

Process tree nodes level by level, useful for printing tree structure or serialization.

### 3. Social Network Analysis

- Finding degrees of separation between users
- Friend suggestions (friends of friends)
- Community detection

### 4. Web Crawling

Systematically explore web pages, processing all pages at depth d before moving to depth d+1.

### 5. Puzzle Solving

- Finding minimum steps to solve puzzles (like sliding puzzles)
- Game state exploration

### 6. Network Broadcasting

Efficiently propagate information through a network, ensuring all nodes are reached in minimum time.

## Variations and Extensions

### 1. Bidirectional BFS

Search from both start and target simultaneously, meeting in the middle. Reduces time complexity for path finding.

### 2. Multi-source BFS

Start BFS from multiple sources simultaneously. Useful for finding nearest facilities or infection spread modeling.

### 3. 0-1 BFS

Modified BFS for graphs where edges have weights of 0 or 1, using a deque instead of queue.

### 4. BFS on Implicit Graphs

Apply BFS to problems where the graph is generated on-the-fly (like maze solving or state space search).

## Performance Considerations

### Memory Usage

- BFS can use significant memory for wide graphs
- Queue size can grow exponentially with branching factor
- Consider iterative deepening for memory-constrained environments

### Optimization Techniques

1. **Early Termination**: Stop when target is found
2. **Visited Set**: Use efficient data structures (HashSet in Rust, set in Python)
3. **Queue Implementation**: Use deque for O(1) append/popleft operations
4. **Memory Pool**: Reuse objects to reduce allocation overhead

### When to Use BFS vs DFS

- **Use BFS when**:
  - Finding shortest path is important
  - Graph is wide but not deep
  - Need level-order processing
  
- **Use DFS when**:
  - Graph is deep but not wide
  - Memory is limited
  - Path existence is more important than shortest path

## Conclusion

BFS is a fundamental algorithm with wide-ranging applications. Its guarantee of finding shortest paths in unweighted graphs makes it invaluable for many real-world problems. The implementations provided offer both basic functionality and advanced features like level-order traversal and distance calculation.

Key takeaways:

- BFS explores graphs level by level using a queue
- Optimal for shortest path problems in unweighted graphs
- Memory intensive but guarantees completeness
- Essential building block for more complex graph algorithms

I'll create a detailed ASCII diagram showing how Breadth-First Search (BFS) works step by step using a simple graph example.This ASCII diagram shows how BFS systematically explores a graph level by level, using a queue to maintain the order of exploration. The key insight is that BFS visits all nodes at distance `k` before visiting any nodes at distance `k+1`, which is why it finds the shortest path in unweighted graphs.

The diagram illustrates how the queue grows and shrinks as we add neighbors and process nodes, and how the "visited" set prevents us from revisiting nodes. Each step shows the current state of the queue, visited nodes, and which node is being processed.

## Breadth-First Search (BFS) Algorithm - Step by Step

## Graph Structure

```

       A
      / \
     B   C
    /|   |\
   D E   F G
```

**Adjacency representation:**

- A: [B, C]
- B: [A, D, E]  
- C: [A, F, G]
- D: [B]
- E: [B]
- F: [C]
- G: [C]

---

## BFS Traversal Starting from Node A

### Step 0: Initialize

```
Queue: [A]
Visited: []
Current: -

       A ← START
      / \
     B   C
    /|   |\
   D E   F G

Status: A is added to queue
```

### Step 1: Process A

```
Queue: [B, C]
Visited: [A]
Current: A

       A ✓
      / \
     B   C ← Added to queue
    /|   |\
   D E   F G

Status: Dequeue A, mark as visited, add neighbors B,C to queue
```

### Step 2: Process B

```
Queue: [C, D, E]
Visited: [A, B]
Current: B

       A ✓
      / \
     B ✓ C
    /|   |\
   D E   F G
   ↑ ↑
   Added to queue

Status: Dequeue B, mark as visited, add unvisited neighbors D,E to queue
```

### Step 3: Process C

```
Queue: [D, E, F, G]
Visited: [A, B, C]
Current: C

       A ✓
      / \
     B ✓ C ✓
    /|   |\
   D E   F G
         ↑ ↑
         Added to queue

Status: Dequeue C, mark as visited, add unvisited neighbors F,G to queue
```

### Step 4: Process D

```
Queue: [E, F, G]
Visited: [A, B, C, D]
Current: D

       A ✓
      / \
     B ✓ C ✓
    /|   |\
   D✓E   F G

Status: Dequeue D, mark as visited, no unvisited neighbors to add
```

### Step 5: Process E

```
Queue: [F, G]
Visited: [A, B, C, D, E]
Current: E

       A ✓
      / \
     B ✓ C ✓
    /|   |\
   D✓E✓  F G

Status: Dequeue E, mark as visited, no unvisited neighbors to add
```

### Step 6: Process F

```
Queue: [G]
Visited: [A, B, C, D, E, F]
Current: F

       A ✓
      / \
     B ✓ C ✓
    /|   |\
   D✓E✓  F✓G

Status: Dequeue F, mark as visited, no unvisited neighbors to add
```

### Step 7: Process G

```
Queue: []
Visited: [A, B, C, D, E, F, G]
Current: G

       A ✓
      / \
     B ✓ C ✓
    /|   |\
   D✓E✓  F✓G✓

Status: Dequeue G, mark as visited, queue is empty - BFS complete!
```

---

## BFS Algorithm Pseudocode

```
BFS(graph, start):
    queue = [start]
    visited = set()
    
    while queue is not empty:
        current = queue.dequeue()
        
        if current not in visited:
            visited.add(current)
            process(current)
            
            for neighbor in graph[current]:
                if neighbor not in visited:
                    queue.enqueue(neighbor)
```

---

## Key Properties of BFS

**Queue Visualization by Level:**
```
Level 0: [A]           ← Distance 0 from start
Level 1: [B, C]        ← Distance 1 from start  
Level 2: [D, E, F, G]  ← Distance 2 from start
```

**Traversal Order:** A → B → C → D → E → F → G

**Time Complexity:** O(V + E) where V = vertices, E = edges
**Space Complexity:** O(V) for the queue and visited set

**Applications:**

- Shortest path in unweighted graphs
- Level-order tree traversal
- Finding connected components
- Web crawling
- Social network analysis

I'll create a comprehensive ASCII diagram showing how Breadth-First Search (BFS) works step by step using a simple graph example.I've created a comprehensive ASCII diagram showing how Breadth-First Search works step by step. The diagram includes:

1. **Sample Graph**: A simple tree-like structure with 7 nodes to demonstrate the algorithm clearly
2. **Step-by-Step Visualization**: Each step shows the current state of the queue, visited nodes, and graph with visual markers
3. **Algorithm Pseudocode**: The core logic of BFS implementation
4. **Key Characteristics**: Time/space complexity and important properties
5. **Queue State Tracking**: A table showing how the queue contents change at each step

The key insight is that BFS uses a queue (FIFO) to ensure nodes are processed level by level, starting from the source node and expanding outward. This guarantees that in an unweighted graph, BFS finds the shortest path to any reachable node.

The visual markers help track the algorithm's progress:

- `*` indicates nodes currently in the queue
- `V` indicates nodes that have been visited
- `C` indicates the node currently being processed

This step-by-step approach makes it easy to understand how BFS systematically explores all nodes at distance 1, then distance 2, and so on.

## Breadth-First Search Algorithm - Step by Step

## Sample Graph Structure

```
    A
   / \
  B   C
 /   / \
D   E   F
    |
    G
```

**Adjacency List Representation:**

- A: [B, C]
- B: [A, D]
- C: [A, E, F]
- D: [B]
- E: [C, G]
- F: [C]
- G: [E]

---

## BFS Traversal Starting from Node A

### Step 0: Initialize

```
Queue: [A]
Visited: []
Current: None

Graph State:
    A*  <- Starting node (marked with *)
   / \
  B   C
 /   / \
D   E   F
    |
    G

Legend: * = in queue, V = visited, C = currently processing
```

### Step 1: Process A

```
Queue: [B, C]  <- A's neighbors added
Visited: [A]   <- A marked as visited
Current: A

Graph State:
    AV  <- A is now visited
   / \
  B*  C*  <- B and C added to queue
 /   / \
D   E   F
    |
    G
```

### Step 2: Process B

```
Queue: [C, D]  <- B processed, D added (A already visited)
Visited: [A, B]
Current: B

Graph State:
    AV
   / \
  BV  C*  <- B is now visited
 /   / \
D*  E   F  <- D added to queue
    |
    G
```

### Step 3: Process C

```
Queue: [D, E, F]  <- C processed, E and F added
Visited: [A, B, C]
Current: C

Graph State:
    AV
   / \
  BV  CV  <- C is now visited
 /   / \
D*  E*  F*  <- E and F added to queue
    |
    G
```

### Step 4: Process D

```
Queue: [E, F]  <- D processed, no new neighbors
Visited: [A, B, C, D]
Current: D

Graph State:
    AV
   / \
  BV  CV
 /   / \
DV  E*  F*  <- D is now visited
    |
    G
```

### Step 5: Process E

```
Queue: [F, G]  <- E processed, G added
Visited: [A, B, C, D, E]
Current: E

Graph State:
    AV
   / \
  BV  CV
 /   / \
DV  EV  F*  <- E is now visited
    |
    G*  <- G added to queue
```

### Step 6: Process F

```
Queue: [G]  <- F processed, no new neighbors
Visited: [A, B, C, D, E, F]
Current: F

Graph State:
    AV
   / \
  BV  CV
 /   / \
DV  EV  FV  <- F is now visited
    |
    G*
```

### Step 7: Process G

```
Queue: []  <- G processed, no new neighbors
Visited: [A, B, C, D, E, F, G]
Current: G

Graph State:
    AV
   / \
  BV  CV
 /   / \
DV  EV  FV  <- All nodes visited
    |
    GV
```

### Final Result: BFS Complete!

```
Final Traversal Order: A → B → C → D → E → F → G
Queue: [] (empty)
All nodes visited: [A, B, C, D, E, F, G]
```

---

## Algorithm Pseudocode

```
BFS(graph, start_node):
    1. Create empty queue
    2. Create empty visited set
    3. Add start_node to queue
    
    4. While queue is not empty:
        a. current = dequeue from front
        b. If current not in visited:
           - Mark current as visited
           - Process current node
           - For each neighbor of current:
             * If neighbor not visited:
               - Add neighbor to queue
    
    5. Return visited nodes in order
```

---

## Key Characteristics of BFS

**Data Structure:** Queue (FIFO - First In, First Out)

**Time Complexity:** O(V + E) where V = vertices, E = edges

**Space Complexity:** O(V) for the queue and visited set

**Properties:**

- Explores nodes level by level (breadth-wise)
- Guarantees shortest path in unweighted graphs
- Uses more memory than DFS due to queue storage
- Finds the shortest path between start node and any reachable node

---

## Queue State Visualization Throughout Process

```
Step | Queue Contents    | Just Visited
-----|-------------------|-------------
 0   | [A]              | -
 1   | [B, C]           | A
 2   | [C, D]           | B  
 3   | [D, E, F]        | C
 4   | [E, F]           | D
 5   | [F, G]           | E
 6   | [G]              | F
 7   | []               | G
```

**Note:** The queue follows FIFO principle - first node added is first node processed, ensuring level-by-level traversal.

## Breadth-First Search (BFS) Algorithm Guide

I'll create a comprehensive guide to the Breadth-First Search (BFS) algorithm with complete implementations in both Python and Rust.I've created a comprehensive guide to the Breadth-First Search algorithm that includes:

## Key Features of the Guide:

**Theoretical Foundation:**

- Clear explanation of how BFS works with visual examples
- Time and space complexity analysis
- Comparison with other traversal methods

**Complete Implementations:**

- **Python**: Object-oriented graph class with multiple BFS variants including traversal, shortest path finding, distance calculation, and level-order processing
- **Rust**: Generic, type-safe implementation with comprehensive error handling and built-in tests

**Practical Applications:**

- Social networks, web crawling, puzzle solving
- Network broadcasting and pathfinding
- Real-world use cases with examples

**Advanced Topics:**

- Algorithm variations (bidirectional BFS, multi-source BFS)
- Performance optimizations and memory considerations
- When to choose BFS over other algorithms

**Code Quality:**

- Both implementations include proper error handling
- Comprehensive type annotations (Python) and generic types (Rust)
- Test cases and example usage
- Production-ready code with documentation

The implementations cover the core BFS functionality as well as common variations like shortest path finding and level-order traversal, making this guide suitable for both learning and practical application.