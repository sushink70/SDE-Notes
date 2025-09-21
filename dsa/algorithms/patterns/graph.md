# Comprehensive Guide to Graph Problem Patterns

## Table of Contents
1. [Graph Representation](#graph-representation)
2. [Graph Traversal Patterns](#graph-traversal-patterns)
3. [Shortest Path Patterns](#shortest-path-patterns)
4. [Cycle Detection Patterns](#cycle-detection-patterns)
5. [Topological Sort Patterns](#topological-sort-patterns)
6. [Connected Components Patterns](#connected-components-patterns)
7. [Minimum Spanning Tree Patterns](#minimum-spanning-tree-patterns)
8. [Bipartite Graph Patterns](#bipartite-graph-patterns)
9. [Advanced Patterns](#advanced-patterns)

---

## Graph Representation

### Adjacency List

**Python Implementation:**
```python
from collections import defaultdict, deque
from typing import List, Dict, Set, Tuple, Optional
import heapq

class Graph:
    def __init__(self, directed=False):
        self.graph = defaultdict(list)
        self.directed = directed
    
    def add_edge(self, u, v, weight=1):
        self.graph[u].append((v, weight))
        if not self.directed:
            self.graph[v].append((u, weight))
    
    def get_vertices(self):
        vertices = set()
        for u in self.graph:
            vertices.add(u)
            for v, _ in self.graph[u]:
                vertices.add(v)
        return vertices
```

**Rust Implementation:**
```rust
use std::collections::{HashMap, VecDeque, HashSet, BinaryHeap};
use std::cmp::Reverse;

#[derive(Debug, Clone)]
pub struct Graph {
    pub graph: HashMap<i32, Vec<(i32, i32)>>, // node -> [(neighbor, weight)]
    pub directed: bool,
}

impl Graph {
    pub fn new(directed: bool) -> Self {
        Graph {
            graph: HashMap::new(),
            directed,
        }
    }
    
    pub fn add_edge(&mut self, u: i32, v: i32, weight: i32) {
        self.graph.entry(u).or_insert(Vec::new()).push((v, weight));
        if !self.directed {
            self.graph.entry(v).or_insert(Vec::new()).push((u, weight));
        }
    }
    
    pub fn get_vertices(&self) -> HashSet<i32> {
        let mut vertices = HashSet::new();
        for (&u, neighbors) in &self.graph {
            vertices.insert(u);
            for &(v, _) in neighbors {
                vertices.insert(v);
            }
        }
        vertices
    }
}
```

---

## Graph Traversal Patterns

### Pattern 1: Depth-First Search (DFS)

**When to use:** Exploring all paths, finding cycles, topological sort, connected components.

**Python Implementation:**
```python
def dfs_recursive(graph, start, visited=None):
    if visited is None:
        visited = set()
    
    visited.add(start)
    result = [start]
    
    for neighbor, _ in graph.graph.get(start, []):
        if neighbor not in visited:
            result.extend(dfs_recursive(graph, neighbor, visited))
    
    return result

def dfs_iterative(graph, start):
    visited = set()
    stack = [start]
    result = []
    
    while stack:
        node = stack.pop()
        if node not in visited:
            visited.add(node)
            result.append(node)
            
            # Add neighbors in reverse order for consistent ordering
            for neighbor, _ in reversed(graph.graph.get(node, [])):
                if neighbor not in visited:
                    stack.append(neighbor)
    
    return result
```

**Rust Implementation:**
```rust
impl Graph {
    pub fn dfs_recursive(&self, start: i32, visited: &mut HashSet<i32>, result: &mut Vec<i32>) {
        visited.insert(start);
        result.push(start);
        
        if let Some(neighbors) = self.graph.get(&start) {
            for &(neighbor, _) in neighbors {
                if !visited.contains(&neighbor) {
                    self.dfs_recursive(neighbor, visited, result);
                }
            }
        }
    }
    
    pub fn dfs_iterative(&self, start: i32) -> Vec<i32> {
        let mut visited = HashSet::new();
        let mut stack = vec![start];
        let mut result = Vec::new();
        
        while let Some(node) = stack.pop() {
            if !visited.contains(&node) {
                visited.insert(node);
                result.push(node);
                
                if let Some(neighbors) = self.graph.get(&node) {
                    for &(neighbor, _) in neighbors.iter().rev() {
                        if !visited.contains(&neighbor) {
                            stack.push(neighbor);
                        }
                    }
                }
            }
        }
        
        result
    }
}
```

### Pattern 2: Breadth-First Search (BFS)

**When to use:** Shortest path in unweighted graphs, level-order traversal, finding minimum steps.

**Python Implementation:**
```python
def bfs(graph, start):
    visited = set()
    queue = deque([start])
    result = []
    
    while queue:
        node = queue.popleft()
        if node not in visited:
            visited.add(node)
            result.append(node)
            
            for neighbor, _ in graph.graph.get(node, []):
                if neighbor not in visited:
                    queue.append(neighbor)
    
    return result

def bfs_shortest_path(graph, start, end):
    if start == end:
        return [start]
    
    visited = set()
    queue = deque([(start, [start])])
    
    while queue:
        node, path = queue.popleft()
        if node in visited:
            continue
        
        visited.add(node)
        
        for neighbor, _ in graph.graph.get(node, []):
            if neighbor == end:
                return path + [neighbor]
            
            if neighbor not in visited:
                queue.append((neighbor, path + [neighbor]))
    
    return []
```

**Rust Implementation:**
```rust
impl Graph {
    pub fn bfs(&self, start: i32) -> Vec<i32> {
        let mut visited = HashSet::new();
        let mut queue = VecDeque::new();
        let mut result = Vec::new();
        
        queue.push_back(start);
        
        while let Some(node) = queue.pop_front() {
            if !visited.contains(&node) {
                visited.insert(node);
                result.push(node);
                
                if let Some(neighbors) = self.graph.get(&node) {
                    for &(neighbor, _) in neighbors {
                        if !visited.contains(&neighbor) {
                            queue.push_back(neighbor);
                        }
                    }
                }
            }
        }
        
        result
    }
    
    pub fn bfs_shortest_path(&self, start: i32, end: i32) -> Vec<i32> {
        if start == end {
            return vec![start];
        }
        
        let mut visited = HashSet::new();
        let mut queue = VecDeque::new();
        queue.push_back((start, vec![start]));
        
        while let Some((node, path)) = queue.pop_front() {
            if visited.contains(&node) {
                continue;
            }
            
            visited.insert(node);
            
            if let Some(neighbors) = self.graph.get(&node) {
                for &(neighbor, _) in neighbors {
                    if neighbor == end {
                        let mut result = path.clone();
                        result.push(neighbor);
                        return result;
                    }
                    
                    if !visited.contains(&neighbor) {
                        let mut new_path = path.clone();
                        new_path.push(neighbor);
                        queue.push_back((neighbor, new_path));
                    }
                }
            }
        }
        
        Vec::new()
    }
}
```

---

## Shortest Path Patterns

### Pattern 3: Dijkstra's Algorithm

**When to use:** Single-source shortest path in weighted graphs with non-negative weights.

**Python Implementation:**
```python
def dijkstra(graph, start):
    distances = {node: float('inf') for node in graph.get_vertices()}
    distances[start] = 0
    previous = {}
    
    # Priority queue: (distance, node)
    pq = [(0, start)]
    visited = set()
    
    while pq:
        current_dist, current = heapq.heappop(pq)
        
        if current in visited:
            continue
        
        visited.add(current)
        
        for neighbor, weight in graph.graph.get(current, []):
            if neighbor not in visited:
                new_dist = current_dist + weight
                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    previous[neighbor] = current
                    heapq.heappush(pq, (new_dist, neighbor))
    
    return distances, previous

def reconstruct_path(previous, start, end):
    if end not in previous and end != start:
        return []
    
    path = []
    current = end
    while current is not None:
        path.append(current)
        current = previous.get(current)
    
    return path[::-1]
```

**Rust Implementation:**
```rust
impl Graph {
    pub fn dijkstra(&self, start: i32) -> (HashMap<i32, i32>, HashMap<i32, i32>) {
        let mut distances = HashMap::new();
        let mut previous = HashMap::new();
        let mut visited = HashSet::new();
        let mut pq = BinaryHeap::new();
        
        // Initialize distances
        for &vertex in &self.get_vertices() {
            distances.insert(vertex, i32::MAX);
        }
        distances.insert(start, 0);
        
        pq.push(Reverse((0, start)));
        
        while let Some(Reverse((current_dist, current))) = pq.pop() {
            if visited.contains(&current) {
                continue;
            }
            
            visited.insert(current);
            
            if let Some(neighbors) = self.graph.get(&current) {
                for &(neighbor, weight) in neighbors {
                    if !visited.contains(&neighbor) {
                        let new_dist = current_dist + weight;
                        if new_dist < *distances.get(&neighbor).unwrap_or(&i32::MAX) {
                            distances.insert(neighbor, new_dist);
                            previous.insert(neighbor, current);
                            pq.push(Reverse((new_dist, neighbor)));
                        }
                    }
                }
            }
        }
        
        (distances, previous)
    }
    
    pub fn reconstruct_path(&self, previous: &HashMap<i32, i32>, start: i32, end: i32) -> Vec<i32> {
        if !previous.contains_key(&end) && end != start {
            return Vec::new();
        }
        
        let mut path = Vec::new();
        let mut current = Some(end);
        
        while let Some(node) = current {
            path.push(node);
            current = previous.get(&node).copied();
        }
        
        path.reverse();
        path
    }
}
```

### Pattern 4: Bellman-Ford Algorithm

**When to use:** Single-source shortest path with negative weights, detecting negative cycles.

**Python Implementation:**
```python
def bellman_ford(graph, start):
    vertices = graph.get_vertices()
    distances = {node: float('inf') for node in vertices}
    distances[start] = 0
    previous = {}
    
    # Relax edges V-1 times
    for _ in range(len(vertices) - 1):
        for u in graph.graph:
            if distances[u] != float('inf'):
                for v, weight in graph.graph[u]:
                    if distances[u] + weight < distances[v]:
                        distances[v] = distances[u] + weight
                        previous[v] = u
    
    # Check for negative cycles
    negative_cycle = False
    for u in graph.graph:
        if distances[u] != float('inf'):
            for v, weight in graph.graph[u]:
                if distances[u] + weight < distances[v]:
                    negative_cycle = True
                    break
        if negative_cycle:
            break
    
    return distances, previous, negative_cycle
```

**Rust Implementation:**
```rust
impl Graph {
    pub fn bellman_ford(&self, start: i32) -> (HashMap<i32, i32>, HashMap<i32, i32>, bool) {
        let vertices = self.get_vertices();
        let mut distances = HashMap::new();
        let mut previous = HashMap::new();
        
        // Initialize distances
        for &vertex in &vertices {
            distances.insert(vertex, i32::MAX);
        }
        distances.insert(start, 0);
        
        // Relax edges V-1 times
        for _ in 0..vertices.len() - 1 {
            for (&u, neighbors) in &self.graph {
                if let Some(&dist_u) = distances.get(&u) {
                    if dist_u != i32::MAX {
                        for &(v, weight) in neighbors {
                            let new_dist = dist_u + weight;
                            if new_dist < *distances.get(&v).unwrap_or(&i32::MAX) {
                                distances.insert(v, new_dist);
                                previous.insert(v, u);
                            }
                        }
                    }
                }
            }
        }
        
        // Check for negative cycles
        let mut negative_cycle = false;
        for (&u, neighbors) in &self.graph {
            if let Some(&dist_u) = distances.get(&u) {
                if dist_u != i32::MAX {
                    for &(v, weight) in neighbors {
                        if dist_u + weight < *distances.get(&v).unwrap_or(&i32::MAX) {
                            negative_cycle = true;
                            break;
                        }
                    }
                }
                if negative_cycle {
                    break;
                }
            }
        }
        
        (distances, previous, negative_cycle)
    }
}
```

---

## Cycle Detection Patterns

### Pattern 5: Cycle Detection in Undirected Graph

**When to use:** Detecting cycles in undirected graphs, validating tree properties.

**Python Implementation:**
```python
def has_cycle_undirected_dfs(graph):
    visited = set()
    
    def dfs(node, parent):
        visited.add(node)
        
        for neighbor, _ in graph.graph.get(node, []):
            if neighbor not in visited:
                if dfs(neighbor, node):
                    return True
            elif neighbor != parent:
                return True
        
        return False
    
    for vertex in graph.get_vertices():
        if vertex not in visited:
            if dfs(vertex, -1):
                return True
    
    return False

def has_cycle_undirected_union_find(edges, n):
    parent = list(range(n))
    
    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]
    
    def union(x, y):
        px, py = find(x), find(y)
        if px == py:
            return True
        parent[px] = py
        return False
    
    for u, v in edges:
        if union(u, v):
            return True
    
    return False
```

**Rust Implementation:**
```rust
impl Graph {
    pub fn has_cycle_undirected(&self) -> bool {
        let mut visited = HashSet::new();
        
        fn dfs(graph: &Graph, node: i32, parent: i32, visited: &mut HashSet<i32>) -> bool {
            visited.insert(node);
            
            if let Some(neighbors) = graph.graph.get(&node) {
                for &(neighbor, _) in neighbors {
                    if !visited.contains(&neighbor) {
                        if dfs(graph, neighbor, node, visited) {
                            return true;
                        }
                    } else if neighbor != parent {
                        return true;
                    }
                }
            }
            
            false
        }
        
        for &vertex in &self.get_vertices() {
            if !visited.contains(&vertex) {
                if dfs(self, vertex, -1, &mut visited) {
                    return true;
                }
            }
        }
        
        false
    }
}

// Union-Find for cycle detection
pub struct UnionFind {
    parent: Vec<usize>,
}

impl UnionFind {
    pub fn new(n: usize) -> Self {
        UnionFind {
            parent: (0..n).collect(),
        }
    }
    
    pub fn find(&mut self, x: usize) -> usize {
        if self.parent[x] != x {
            self.parent[x] = self.find(self.parent[x]);
        }
        self.parent[x]
    }
    
    pub fn union(&mut self, x: usize, y: usize) -> bool {
        let px = self.find(x);
        let py = self.find(y);
        
        if px == py {
            return true; // Cycle detected
        }
        
        self.parent[px] = py;
        false
    }
}
```

### Pattern 6: Cycle Detection in Directed Graph

**When to use:** Detecting cycles in directed graphs, dependency resolution.

**Python Implementation:**
```python
def has_cycle_directed(graph):
    WHITE, GRAY, BLACK = 0, 1, 2
    colors = {node: WHITE for node in graph.get_vertices()}
    
    def dfs(node):
        if colors[node] == GRAY:
            return True
        if colors[node] == BLACK:
            return False
        
        colors[node] = GRAY
        
        for neighbor, _ in graph.graph.get(node, []):
            if dfs(neighbor):
                return True
        
        colors[node] = BLACK
        return False
    
    for vertex in graph.get_vertices():
        if colors[vertex] == WHITE:
            if dfs(vertex):
                return True
    
    return False

def find_cycle_path_directed(graph):
    WHITE, GRAY, BLACK = 0, 1, 2
    colors = {node: WHITE for node in graph.get_vertices()}
    parent = {}
    
    def dfs(node, path):
        if colors[node] == GRAY:
            # Found back edge - extract cycle
            cycle_start = len(path) - 1
            while path[cycle_start] != node:
                cycle_start -= 1
            return path[cycle_start:]
        
        if colors[node] == BLACK:
            return None
        
        colors[node] = GRAY
        path.append(node)
        
        for neighbor, _ in graph.graph.get(node, []):
            cycle = dfs(neighbor, path)
            if cycle:
                return cycle
        
        path.pop()
        colors[node] = BLACK
        return None
    
    for vertex in graph.get_vertices():
        if colors[vertex] == WHITE:
            cycle = dfs(vertex, [])
            if cycle:
                return cycle
    
    return None
```

**Rust Implementation:**
```rust
#[derive(Clone, Copy, PartialEq)]
enum Color {
    White,
    Gray,
    Black,
}

impl Graph {
    pub fn has_cycle_directed(&self) -> bool {
        let mut colors = HashMap::new();
        
        for &vertex in &self.get_vertices() {
            colors.insert(vertex, Color::White);
        }
        
        fn dfs(graph: &Graph, node: i32, colors: &mut HashMap<i32, Color>) -> bool {
            if let Some(&Color::Gray) = colors.get(&node) {
                return true;
            }
            if let Some(&Color::Black) = colors.get(&node) {
                return false;
            }
            
            colors.insert(node, Color::Gray);
            
            if let Some(neighbors) = graph.graph.get(&node) {
                for &(neighbor, _) in neighbors {
                    if dfs(graph, neighbor, colors) {
                        return true;
                    }
                }
            }
            
            colors.insert(node, Color::Black);
            false
        }
        
        for &vertex in &self.get_vertices() {
            if let Some(&Color::White) = colors.get(&vertex) {
                if dfs(self, vertex, &mut colors) {
                    return true;
                }
            }
        }
        
        false
    }
    
    pub fn find_cycle_path_directed(&self) -> Option<Vec<i32>> {
        let mut colors = HashMap::new();
        
        for &vertex in &self.get_vertices() {
            colors.insert(vertex, Color::White);
        }
        
        fn dfs(graph: &Graph, node: i32, colors: &mut HashMap<i32, Color>, path: &mut Vec<i32>) -> Option<Vec<i32>> {
            if let Some(&Color::Gray) = colors.get(&node) {
                // Found back edge - extract cycle
                if let Some(cycle_start) = path.iter().position(|&x| x == node) {
                    return Some(path[cycle_start..].to_vec());
                }
            }
            
            if let Some(&Color::Black) = colors.get(&node) {
                return None;
            }
            
            colors.insert(node, Color::Gray);
            path.push(node);
            
            if let Some(neighbors) = graph.graph.get(&node) {
                for &(neighbor, _) in neighbors {
                    if let Some(cycle) = dfs(graph, neighbor, colors, path) {
                        return Some(cycle);
                    }
                }
            }
            
            path.pop();
            colors.insert(node, Color::Black);
            None
        }
        
        for &vertex in &self.get_vertices() {
            if let Some(&Color::White) = colors.get(&vertex) {
                let mut path = Vec::new();
                if let Some(cycle) = dfs(self, vertex, &mut colors, &mut path) {
                    return Some(cycle);
                }
            }
        }
        
        None
    }
}
```

---

## Topological Sort Patterns

### Pattern 7: Topological Sort (Kahn's Algorithm)

**When to use:** Task scheduling, dependency resolution, course prerequisites.

**Python Implementation:**
```python
def topological_sort_kahn(graph):
    # Calculate in-degrees
    in_degree = {node: 0 for node in graph.get_vertices()}
    
    for u in graph.graph:
        for v, _ in graph.graph[u]:
            in_degree[v] += 1
    
    # Start with nodes having in-degree 0
    queue = deque([node for node in in_degree if in_degree[node] == 0])
    result = []
    
    while queue:
        node = queue.popleft()
        result.append(node)
        
        for neighbor, _ in graph.graph.get(node, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    # Check if all nodes are processed (no cycle)
    if len(result) != len(graph.get_vertices()):
        return None  # Cycle detected
    
    return result

def topological_sort_dfs(graph):
    visited = set()
    rec_stack = set()
    result = []
    
    def dfs(node):
        if node in rec_stack:
            return False  # Cycle detected
        if node in visited:
            return True
        
        visited.add(node)
        rec_stack.add(node)
        
        for neighbor, _ in graph.graph.get(node, []):
            if not dfs(neighbor):
                return False
        
        rec_stack.remove(node)
        result.append(node)
        return True
    
    for vertex in graph.get_vertices():
        if vertex not in visited:
            if not dfs(vertex):
                return None  # Cycle detected
    
    return result[::-1]
```

**Rust Implementation:**
```rust
impl Graph {
    pub fn topological_sort_kahn(&self) -> Option<Vec<i32>> {
        let mut in_degree = HashMap::new();
        let vertices = self.get_vertices();
        
        // Initialize in-degrees
        for &vertex in &vertices {
            in_degree.insert(vertex, 0);
        }
        
        // Calculate in-degrees
        for (_, neighbors) in &self.graph {
            for &(neighbor, _) in neighbors {
                *in_degree.entry(neighbor).or_insert(0) += 1;
            }
        }
        
        // Start with nodes having in-degree 0
        let mut queue = VecDeque::new();
        for (&node, &degree) in &in_degree {
            if degree == 0 {
                queue.push_back(node);
            }
        }
        
        let mut result = Vec::new();
        
        while let Some(node) = queue.pop_front() {
            result.push(node);
            
            if let Some(neighbors) = self.graph.get(&node) {
                for &(neighbor, _) in neighbors {
                    if let Some(degree) = in_degree.get_mut(&neighbor) {
                        *degree -= 1;
                        if *degree == 0 {
                            queue.push_back(neighbor);
                        }
                    }
                }
            }
        }
        
        // Check if all nodes are processed
        if result.len() != vertices.len() {
            None // Cycle detected
        } else {
            Some(result)
        }
    }
    
    pub fn topological_sort_dfs(&self) -> Option<Vec<i32>> {
        let mut visited = HashSet::new();
        let mut rec_stack = HashSet::new();
        let mut result = Vec::new();
        
        fn dfs(graph: &Graph, node: i32, visited: &mut HashSet<i32>, 
               rec_stack: &mut HashSet<i32>, result: &mut Vec<i32>) -> bool {
            if rec_stack.contains(&node) {
                return false; // Cycle detected
            }
            if visited.contains(&node) {
                return true;
            }
            
            visited.insert(node);
            rec_stack.insert(node);
            
            if let Some(neighbors) = graph.graph.get(&node) {
                for &(neighbor, _) in neighbors {
                    if !dfs(graph, neighbor, visited, rec_stack, result) {
                        return false;
                    }
                }
            }
            
            rec_stack.remove(&node);
            result.push(node);
            true
        }
        
        for &vertex in &self.get_vertices() {
            if !visited.contains(&vertex) {
                if !dfs(self, vertex, &mut visited, &mut rec_stack, &mut result) {
                    return None; // Cycle detected
                }
            }
        }
        
        result.reverse();
        Some(result)
    }
}
```

---

## Connected Components Patterns

### Pattern 8: Connected Components in Undirected Graph

**When to use:** Finding isolated groups, network analysis, clustering.

**Python Implementation:**
```python
def find_connected_components(graph):
    visited = set()
    components = []
    
    def dfs(node, component):
        visited.add(node)
        component.append(node)
        
        for neighbor, _ in graph.graph.get(node, []):
            if neighbor not in visited:
                dfs(neighbor, component)
    
    for vertex in graph.get_vertices():
        if vertex not in visited:
            component = []
            dfs(vertex, component)
            components.append(component)
    
    return components

def strongly_connected_components_tarjan(graph):
    """Tarjan's algorithm for finding SCCs in one pass"""
    def tarjan_dfs(node):
        nonlocal time, stack, on_stack, low_link, disc, components
        
        disc[node] = low_link[node] = time
        time += 1
        stack.append(node)
        on_stack.add(node)
        
        for neighbor, _ in graph.graph.get(node, []):
            if neighbor not in disc:
                tarjan_dfs(neighbor)
                low_link[node] = min(low_link[node], low_link[neighbor])
            elif neighbor in on_stack:
                low_link[node] = min(low_link[node], disc[neighbor])
        
        # If node is a root of SCC
        if low_link[node] == disc[node]:
            component = []
            while True:
                w = stack.pop()
                on_stack.remove(w)
                component.append(w)
                if w == node:
                    break
            components.append(component)
    
    disc = {}
    low_link = {}
    stack = []
    on_stack = set()
    time = 0
    components = []
    
    for vertex in graph.get_vertices():
        if vertex not in disc:
            tarjan_dfs(vertex)
    
    return components
```

**Rust Implementation:**
```rust
impl Graph {
    pub fn strongly_connected_components_kosaraju(&self) -> Vec<Vec<i32>> {
        fn dfs1(graph: &Graph, node: i32, visited: &mut HashSet<i32>, stack: &mut Vec<i32>) {
            visited.insert(node);
            
            if let Some(neighbors) = graph.graph.get(&node) {
                for &(neighbor, _) in neighbors {
                    if !visited.contains(&neighbor) {
                        dfs1(graph, neighbor, visited, stack);
                    }
                }
            }
            
            stack.push(node);
        }
        
        fn dfs2(node: i32, visited: &mut HashSet<i32>, component: &mut Vec<i32>, 
                reversed_graph: &HashMap<i32, Vec<i32>>) {
            visited.insert(node);
            component.push(node);
            
            if let Some(neighbors) = reversed_graph.get(&node) {
                for &neighbor in neighbors {
                    if !visited.contains(&neighbor) {
                        dfs2(neighbor, visited, component, reversed_graph);
                    }
                }
            }
        }
        
        // Step 1: Fill vertices in stack according to finishing times
        let mut visited = HashSet::new();
        let mut stack = Vec::new();
        
        for &vertex in &self.get_vertices() {
            if !visited.contains(&vertex) {
                dfs1(self, vertex, &mut visited, &mut stack);
            }
        }
        
        // Step 2: Create reversed graph
        let mut reversed_graph: HashMap<i32, Vec<i32>> = HashMap::new();
        for (&u, neighbors) in &self.graph {
            for &(v, _) in neighbors {
                reversed_graph.entry(v).or_insert(Vec::new()).push(u);
            }
        }
        
        // Step 3: Process vertices in reverse finishing order
        visited.clear();
        let mut components = Vec::new();
        
        while let Some(vertex) = stack.pop() {
            if !visited.contains(&vertex) {
                let mut component = Vec::new();
                dfs2(vertex, &mut visited, &mut component, &reversed_graph);
                components.push(component);
            }
        }
        
        components
    }
    
    pub fn strongly_connected_components_tarjan(&self) -> Vec<Vec<i32>> {
        struct TarjanState {
            disc: HashMap<i32, usize>,
            low_link: HashMap<i32, usize>,
            stack: Vec<i32>,
            on_stack: HashSet<i32>,
            time: usize,
            components: Vec<Vec<i32>>,
        }
        
        fn tarjan_dfs(graph: &Graph, node: i32, state: &mut TarjanState) {
            state.disc.insert(node, state.time);
            state.low_link.insert(node, state.time);
            state.time += 1;
            state.stack.push(node);
            state.on_stack.insert(node);
            
            if let Some(neighbors) = graph.graph.get(&node) {
                for &(neighbor, _) in neighbors {
                    if !state.disc.contains_key(&neighbor) {
                        tarjan_dfs(graph, neighbor, state);
                        let neighbor_low = *state.low_link.get(&neighbor).unwrap();
                        let node_low = state.low_link.get_mut(&node).unwrap();
                        *node_low = (*node_low).min(neighbor_low);
                    } else if state.on_stack.contains(&neighbor) {
                        let neighbor_disc = *state.disc.get(&neighbor).unwrap();
                        let node_low = state.low_link.get_mut(&node).unwrap();
                        *node_low = (*node_low).min(neighbor_disc);
                    }
                }
            }
            
            // If node is a root of SCC
            if state.low_link[&node] == state.disc[&node] {
                let mut component = Vec::new();
                loop {
                    let w = state.stack.pop().unwrap();
                    state.on_stack.remove(&w);
                    component.push(w);
                    if w == node {
                        break;
                    }
                }
                state.components.push(component);
            }
        }
        
        let mut state = TarjanState {
            disc: HashMap::new(),
            low_link: HashMap::new(),
            stack: Vec::new(),
            on_stack: HashSet::new(),
            time: 0,
            components: Vec::new(),
        };
        
        for &vertex in &self.get_vertices() {
            if !state.disc.contains_key(&vertex) {
                tarjan_dfs(self, vertex, &mut state);
            }
        }
        
        state.components
    }
}

---

## Minimum Spanning Tree Patterns

### Pattern 10: Kruskal's Algorithm

**When to use:** Finding minimum spanning tree, connecting components with minimum cost.

**Python Implementation:**
```python
def kruskal_mst(graph):
    """Find MST using Kruskal's algorithm with Union-Find"""
    
    class UnionFind:
        def __init__(self, vertices):
            self.parent = {v: v for v in vertices}
            self.rank = {v: 0 for v in vertices}
        
        def find(self, x):
            if self.parent[x] != x:
                self.parent[x] = self.find(self.parent[x])
            return self.parent[x]
        
        def union(self, x, y):
            px, py = self.find(x), self.find(y)
            if px == py:
                return False
            
            if self.rank[px] < self.rank[py]:
                px, py = py, px
            
            self.parent[py] = px
            if self.rank[px] == self.rank[py]:
                self.rank[px] += 1
            
            return True
    
    # Get all edges
    edges = []
    for u in graph.graph:
        for v, weight in graph.graph[u]:
            if not graph.directed or u < v:  # Avoid duplicate edges for undirected
                edges.append((weight, u, v))
    
    edges.sort()  # Sort by weight
    
    vertices = graph.get_vertices()
    uf = UnionFind(vertices)
    mst_edges = []
    total_weight = 0
    
    for weight, u, v in edges:
        if uf.union(u, v):
            mst_edges.append((u, v, weight))
            total_weight += weight
            
            if len(mst_edges) == len(vertices) - 1:
                break
    
    return mst_edges, total_weight

def prim_mst(graph, start=None):
    """Find MST using Prim's algorithm"""
    vertices = graph.get_vertices()
    if not vertices:
        return [], 0
    
    if start is None:
        start = next(iter(vertices))
    
    visited = {start}
    mst_edges = []
    total_weight = 0
    
    # Priority queue: (weight, u, v)
    pq = []
    for neighbor, weight in graph.graph.get(start, []):
        heapq.heappush(pq, (weight, start, neighbor))
    
    while pq and len(visited) < len(vertices):
        weight, u, v = heapq.heappop(pq)
        
        if v in visited:
            continue
        
        visited.add(v)
        mst_edges.append((u, v, weight))
        total_weight += weight
        
        # Add new edges from v
        for neighbor, w in graph.graph.get(v, []):
            if neighbor not in visited:
                heapq.heappush(pq, (w, v, neighbor))
    
    return mst_edges, total_weight
```

**Rust Implementation:**
```rust
#[derive(Debug, Clone)]
pub struct UnionFind {
    parent: HashMap<i32, i32>,
    rank: HashMap<i32, usize>,
}

impl UnionFind {
    pub fn new(vertices: &HashSet<i32>) -> Self {
        let mut parent = HashMap::new();
        let mut rank = HashMap::new();
        
        for &v in vertices {
            parent.insert(v, v);
            rank.insert(v, 0);
        }
        
        UnionFind { parent, rank }
    }
    
    pub fn find(&mut self, x: i32) -> i32 {
        if self.parent[&x] != x {
            let root = self.find(self.parent[&x]);
            self.parent.insert(x, root);
        }
        self.parent[&x]
    }
    
    pub fn union(&mut self, x: i32, y: i32) -> bool {
        let px = self.find(x);
        let py = self.find(y);
        
        if px == py {
            return false;
        }
        
        let rank_x = self.rank[&px];
        let rank_y = self.rank[&py];
        
        if rank_x < rank_y {
            self.parent.insert(px, py);
        } else if rank_x > rank_y {
            self.parent.insert(py, px);
        } else {
            self.parent.insert(py, px);
            self.rank.insert(px, rank_x + 1);
        }
        
        true
    }
}

impl Graph {
    pub fn kruskal_mst(&self) -> (Vec<(i32, i32, i32)>, i32) {
        // Get all edges
        let mut edges = Vec::new();
        for (&u, neighbors) in &self.graph {
            for &(v, weight) in neighbors {
                if !self.directed || u < v {
                    edges.push((weight, u, v));
                }
            }
        }
        
        edges.sort_by_key(|&(weight, _, _)| weight);
        
        let vertices = self.get_vertices();
        let mut uf = UnionFind::new(&vertices);
        let mut mst_edges = Vec::new();
        let mut total_weight = 0;
        
        for (weight, u, v) in edges {
            if uf.union(u, v) {
                mst_edges.push((u, v, weight));
                total_weight += weight;
                
                if mst_edges.len() == vertices.len() - 1 {
                    break;
                }
            }
        }
        
        (mst_edges, total_weight)
    }
    
    pub fn prim_mst(&self, start: Option<i32>) -> (Vec<(i32, i32, i32)>, i32) {
        let vertices = self.get_vertices();
        if vertices.is_empty() {
            return (Vec::new(), 0);
        }
        
        let start = start.unwrap_or_else(|| *vertices.iter().next().unwrap());
        
        let mut visited = HashSet::new();
        visited.insert(start);
        
        let mut mst_edges = Vec::new();
        let mut total_weight = 0;
        
        let mut pq = BinaryHeap::new();
        
        // Add initial edges
        if let Some(neighbors) = self.graph.get(&start) {
            for &(neighbor, weight) in neighbors {
                pq.push(Reverse((weight, start, neighbor)));
            }
        }
        
        while let Some(Reverse((weight, u, v))) = pq.pop() {
            if visited.contains(&v) {
                continue;
            }
            
            visited.insert(v);
            mst_edges.push((u, v, weight));
            total_weight += weight;
            
            if visited.len() == vertices.len() {
                break;
            }
            
            // Add new edges from v
            if let Some(neighbors) = self.graph.get(&v) {
                for &(neighbor, w) in neighbors {
                    if !visited.contains(&neighbor) {
                        pq.push(Reverse((w, v, neighbor)));
                    }
                }
            }
        }
        
        (mst_edges, total_weight)
    }
}

---

## Bipartite Graph Patterns

### Pattern 11: Bipartite Graph Detection and Matching

**When to use:** Detecting if graph is bipartite, finding maximum matching, assignment problems.

**Python Implementation:**
```python
def is_bipartite(graph):
    """Check if graph is bipartite using BFS coloring"""
    color = {}
    
    for start in graph.get_vertices():
        if start in color:
            continue
        
        queue = deque([start])
        color[start] = 0
        
        while queue:
            node = queue.popleft()
            
            for neighbor, _ in graph.graph.get(node, []):
                if neighbor not in color:
                    color[neighbor] = 1 - color[node]
                    queue.append(neighbor)
                elif color[neighbor] == color[node]:
                    return False
    
    return True

def get_bipartite_sets(graph):
    """Get the two sets of a bipartite graph"""
    if not is_bipartite(graph):
        return None, None
    
    color = {}
    set1, set2 = set(), set()
    
    for start in graph.get_vertices():
        if start in color:
            continue
        
        queue = deque([start])
        color[start] = 0
        
        while queue:
            node = queue.popleft()
            
            if color[node] == 0:
                set1.add(node)
            else:
                set2.add(node)
            
            for neighbor, _ in graph.graph.get(node, []):
                if neighbor not in color:
                    color[neighbor] = 1 - color[node]
                    queue.append(neighbor)
    
    return set1, set2

def maximum_bipartite_matching(graph):
    """Find maximum matching in bipartite graph using DFS"""
    set1, set2 = get_bipartite_sets(graph)
    if set1 is None:
        return []
    
    match = {}
    
    def dfs(u, visited):
        for neighbor, _ in graph.graph.get(u, []):
            if neighbor in visited:
                continue
            
            visited.add(neighbor)
            
            # If neighbor is unmatched or we can find augmenting path
            if neighbor not in match or dfs(match[neighbor], visited):
                match[neighbor] = u
                return True
        
        return False
    
    matching = []
    for u in set1:
        visited = set()
        if dfs(u, visited):
            # Find the matched pair
            for v in set2:
                if match.get(v) == u:
                    matching.append((u, v))
                    break
    
    return matching
```

**Rust Implementation:**
```rust
impl Graph {
    pub fn is_bipartite(&self) -> bool {
        let mut color = HashMap::new();
        
        for &start in &self.get_vertices() {
            if color.contains_key(&start) {
                continue;
            }
            
            let mut queue = VecDeque::new();
            queue.push_back(start);
            color.insert(start, 0);
            
            while let Some(node) = queue.pop_front() {
                if let Some(neighbors) = self.graph.get(&node) {
                    for &(neighbor, _) in neighbors {
                        if !color.contains_key(&neighbor) {
                            color.insert(neighbor, 1 - color[&node]);
                            queue.push_back(neighbor);
                        } else if color[&neighbor] == color[&node] {
                            return false;
                        }
                    }
                }
            }
        }
        
        true
    }
    
    pub fn get_bipartite_sets(&self) -> Option<(HashSet<i32>, HashSet<i32>)> {
        if !self.is_bipartite() {
            return None;
        }
        
        let mut color = HashMap::new();
        let mut set1 = HashSet::new();
        let mut set2 = HashSet::new();
        
        for &start in &self.get_vertices() {
            if color.contains_key(&start) {
                continue;
            }
            
            let mut queue = VecDeque::new();
            queue.push_back(start);
            color.insert(start, 0);
            
            while let Some(node) = queue.pop_front() {
                if color[&node] == 0 {
                    set1.insert(node);
                } else {
                    set2.insert(node);
                }
                
                if let Some(neighbors) = self.graph.get(&node) {
                    for &(neighbor, _) in neighbors {
                        if !color.contains_key(&neighbor) {
                            color.insert(neighbor, 1 - color[&node]);
                            queue.push_back(neighbor);
                        }
                    }
                }
            }
        }
        
        Some((set1, set2))
    }
    
    pub fn maximum_bipartite_matching(&self) -> Vec<(i32, i32)> {
        let (set1, set2) = match self.get_bipartite_sets() {
            Some((s1, s2)) => (s1, s2),
            None => return Vec::new(),
        };
        
        let mut match_map = HashMap::new();
        
        fn dfs(graph: &Graph, u: i32, visited: &mut HashSet<i32>, 
               match_map: &mut HashMap<i32, i32>) -> bool {
            if let Some(neighbors) = graph.graph.get(&u) {
                for &(neighbor, _) in neighbors {
                    if visited.contains(&neighbor) {
                        continue;
                    }
                    
                    visited.insert(neighbor);
                    
                    // If neighbor is unmatched or we can find augmenting path
                    if !match_map.contains_key(&neighbor) || 
                       dfs(graph, match_map[&neighbor], visited, match_map) {
                        match_map.insert(neighbor, u);
                        return true;
                    }
                }
            }
            
            false
        }
        
        for &u in &set1 {
            let mut visited = HashSet::new();
            dfs(self, u, &mut visited, &mut match_map);
        }
        
        // Convert to matching pairs
        let mut matching = Vec::new();
        for (&v, &u) in &match_map {
            matching.push((u, v));
        }
        
        matching
    }
}

---

## Advanced Patterns

### Pattern 12: Articulation Points and Bridges

**When to use:** Finding critical nodes/edges whose removal increases connected components.

**Python Implementation:**
```python
def find_articulation_points(graph):
    """Find articulation points using Tarjan's algorithm"""
    visited = set()
    disc = {}
    low = {}
    parent = {}
    ap = set()
    time = [0]
    
    def ap_dfs(u):
        children = 0
        visited.add(u)
        disc[u] = low[u] = time[0]
        time[0] += 1
        
        for neighbor, _ in graph.graph.get(u, []):
            if neighbor not in visited:
                children += 1
                parent[neighbor] = u
                ap_dfs(neighbor)
                
                low[u] = min(low[u], low[neighbor])
                
                # Root is AP if it has more than one child
                if parent.get(u) is None and children > 1:
                    ap.add(u)
                
                # Non-root is AP if removing it disconnects the graph
                if parent.get(u) is not None and low[neighbor] >= disc[u]:
                    ap.add(u)
                    
            elif neighbor != parent.get(u):
                low[u] = min(low[u], disc[neighbor])
    
    for vertex in graph.get_vertices():
        if vertex not in visited:
            ap_dfs(vertex)
    
    return list(ap)

def find_bridges(graph):
    """Find bridges using Tarjan's algorithm"""
    visited = set()
    disc = {}
    low = {}
    parent = {}
    bridges = []
    time = [0]
    
    def bridge_dfs(u):
        visited.add(u)
        disc[u] = low[u] = time[0]
        time[0] += 1
        
        for neighbor, _ in graph.graph.get(u, []):
            if neighbor not in visited:
                parent[neighbor] = u
                bridge_dfs(neighbor)
                
                low[u] = min(low[u], low[neighbor])
                
                # If low value of neighbor is more than discovery of u
                if low[neighbor] > disc[u]:
                    bridges.append((u, neighbor))
                    
            elif neighbor != parent.get(u):
                low[u] = min(low[u], disc[neighbor])
    
    for vertex in graph.get_vertices():
        if vertex not in visited:
            bridge_dfs(vertex)
    
    return bridges
```

**Rust Implementation:**
```rust
impl Graph {
    pub fn find_articulation_points(&self) -> Vec<i32> {
        let mut visited = HashSet::new();
        let mut disc = HashMap::new();
        let mut low = HashMap::new();
        let mut parent = HashMap::new();
        let mut ap = HashSet::new();
        let mut time = 0;
        
        fn ap_dfs(graph: &Graph, u: i32, visited: &mut HashSet<i32>,
                  disc: &mut HashMap<i32, usize>, low: &mut HashMap<i32, usize>,
                  parent: &mut HashMap<i32, i32>, ap: &mut HashSet<i32>,
                  time: &mut usize) {
            let mut children = 0;
            visited.insert(u);
            disc.insert(u, *time);
            low.insert(u, *time);
            *time += 1;
            
            if let Some(neighbors) = graph.graph.get(&u) {
                for &(neighbor, _) in neighbors {
                    if !visited.contains(&neighbor) {
                        children += 1;
                        parent.insert(neighbor, u);
                        ap_dfs(graph, neighbor, visited, disc, low, parent, ap, time);
                        
                        let neighbor_low = *low.get(&neighbor).unwrap();
                        let u_low = low.get_mut(&u).unwrap();
                        *u_low = (*u_low).min(neighbor_low);
                        
                        // Root is AP if it has more than one child
                        if !parent.contains_key(&u) && children > 1 {
                            ap.insert(u);
                        }
                        
                        // Non-root is AP if removing it disconnects the graph
                        if parent.contains_key(&u) && neighbor_low >= disc[&u] {
                            ap.insert(u);
                        }
                    } else if Some(neighbor) != parent.get(&u).copied() {
                        let neighbor_disc = *disc.get(&neighbor).unwrap();
                        let u_low = low.get_mut(&u).unwrap();
                        *u_low = (*u_low).min(neighbor_disc);
                    }
                }
            }
        }
        
        for &vertex in &self.get_vertices() {
            if !visited.contains(&vertex) {
                ap_dfs(self, vertex, &mut visited, &mut disc, &mut low,
                       &mut parent, &mut ap, &mut time);
            }
        }
        
        ap.into_iter().collect()
    }
    
    pub fn find_bridges(&self) -> Vec<(i32, i32)> {
        let mut visited = HashSet::new();
        let mut disc = HashMap::new();
        let mut low = HashMap::new();
        let mut parent = HashMap::new();
        let mut bridges = Vec::new();
        let mut time = 0;
        
        fn bridge_dfs(graph: &Graph, u: i32, visited: &mut HashSet<i32>,
                      disc: &mut HashMap<i32, usize>, low: &mut HashMap<i32, usize>,
                      parent: &mut HashMap<i32, i32>, bridges: &mut Vec<(i32, i32)>,
                      time: &mut usize) {
            visited.insert(u);
            disc.insert(u, *time);
            low.insert(u, *time);
            *time += 1;
            
            if let Some(neighbors) = graph.graph.get(&u) {
                for &(neighbor, _) in neighbors {
                    if !visited.contains(&neighbor) {
                        parent.insert(neighbor, u);
                        bridge_dfs(graph, neighbor, visited, disc, low, parent, bridges, time);
                        
                        let neighbor_low = *low.get(&neighbor).unwrap();
                        let u_low = low.get_mut(&u).unwrap();
                        *u_low = (*u_low).min(neighbor_low);
                        
                        // If low value of neighbor is more than discovery of u
                        if neighbor_low > disc[&u] {
                            bridges.push((u, neighbor));
                        }
                    } else if Some(neighbor) != parent.get(&u).copied() {
                        let neighbor_disc = *disc.get(&neighbor).unwrap();
                        let u_low = low.get_mut(&u).unwrap();
                        *u_low = (*u_low).min(neighbor_disc);
                    }
                }
            }
        }
        
        for &vertex in &self.get_vertices() {
            if !visited.contains(&vertex) {
                bridge_dfs(self, vertex, &mut visited, &mut disc, &mut low,
                          &mut parent, &mut bridges, &mut time);
            }
        }
        
        bridges
    }
}

---

## Common Problem Examples and Solutions

### Example 1: Word Ladder (Shortest Transformation)

**Python Implementation:**
```python
def word_ladder(begin_word, end_word, word_list):
    """Find shortest transformation sequence"""
    if end_word not in word_list:
        return 0
    
    # Build graph of word transformations
    word_set = set(word_list)
    queue = deque([(begin_word, 1)])
    visited = {begin_word}
    
    while queue:
        word, length = queue.popleft()
        
        if word == end_word:
            return length
        
        # Try all possible one-letter changes
        for i in range(len(word)):
            for c in 'abcdefghijklmnopqrstuvwxyz':
                new_word = word[:i] + c + word[i+1:]
                
                if new_word in word_set and new_word not in visited:
                    visited.add(new_word)
                    queue.append((new_word, length + 1))
    
    return 0
```

**Rust Implementation:**
```rust
use std::collections::{HashSet, VecDeque};

pub fn word_ladder(begin_word: &str, end_word: &str, word_list: &[String]) -> i32 {
    let word_set: HashSet<&str> = word_list.iter().map(|s| s.as_str()).collect();
    
    if !word_set.contains(end_word) {
        return 0;
    }
    
    let mut queue = VecDeque::new();
    let mut visited = HashSet::new();
    
    queue.push_back((begin_word.to_string(), 1));
    visited.insert(begin_word.to_string());
    
    while let Some((word, length)) = queue.pop_front() {
        if word == end_word {
            return length;
        }
        
        // Try all possible one-letter changes
        let word_chars: Vec<char> = word.chars().collect();
        for i in 0..word_chars.len() {
            for c in 'a'..='z' {
                let mut new_word_chars = word_chars.clone();
                new_word_chars[i] = c;
                let new_word: String = new_word_chars.iter().collect();
                
                if word_set.contains(new_word.as_str()) && !visited.contains(&new_word) {
                    visited.insert(new_word.clone());
                    queue.push_back((new_word, length + 1));
                }
            }
        }
    }
    
    0
}

### Example 2: Course Schedule (Topological Sort)

**Python Implementation:**
```python
def can_finish_courses(num_courses, prerequisites):
    """Check if all courses can be finished (no cycle in prerequisites)"""
    # Build adjacency list
    graph = defaultdict(list)
    in_degree = [0] * num_courses
    
    for course, prereq in prerequisites:
        graph[prereq].append(course)
        in_degree[course] += 1
    
    # Kahn's algorithm
    queue = deque([i for i in range(num_courses) if in_degree[i] == 0])
    completed = 0
    
    while queue:
        prereq = queue.popleft()
        completed += 1
        
        for course in graph[prereq]:
            in_degree[course] -= 1
            if in_degree[course] == 0:
                queue.append(course)
    
    return completed == num_courses

def find_course_order(num_courses, prerequisites):
    """Find valid course order"""
    graph = defaultdict(list)
    in_degree = [0] * num_courses
    
    for course, prereq in prerequisites:
        graph[prereq].append(course)
        in_degree[course] += 1
    
    queue = deque([i for i in range(num_courses) if in_degree[i] == 0])
    order = []
    
    while queue:
        prereq = queue.popleft()
        order.append(prereq)
        
        for course in graph[prereq]:
            in_degree[course] -= 1
            if in_degree[course] == 0:
                queue.append(course)
    
    return order if len(order) == num_courses else []
```

**Rust Implementation:**
```rust
use std::collections::{HashMap, VecDeque};

pub fn can_finish_courses(num_courses: i32, prerequisites: Vec<Vec<i32>>) -> bool {
    let n = num_courses as usize;
    let mut graph: HashMap<i32, Vec<i32>> = HashMap::new();
    let mut in_degree = vec![0; n];
    
    for prereq in prerequisites {
        let course = prereq[0];
        let pre = prereq[1];
        graph.entry(pre).or_insert(Vec::new()).push(course);
        in_degree[course as usize] += 1;
    }
    
    let mut queue = VecDeque::new();
    for i in 0..n {
        if in_degree[i] == 0 {
            queue.push_back(i as i32);
        }
    }
    
    let mut completed = 0;
    
    while let Some(prereq) = queue.pop_front() {
        completed += 1;
        
        if let Some(courses) = graph.get(&prereq) {
            for &course in courses {
                in_degree[course as usize] -= 1;
                if in_degree[course as usize] == 0 {
                    queue.push_back(course);
                }
            }
        }
    }
    
    completed == n
}

pub fn find_course_order(num_courses: i32, prerequisites: Vec<Vec<i32>>) -> Vec<i32> {
    let n = num_courses as usize;
    let mut graph: HashMap<i32, Vec<i32>> = HashMap::new();
    let mut in_degree = vec![0; n];
    
    for prereq in prerequisites {
        let course = prereq[0];
        let pre = prereq[1];
        graph.entry(pre).or_insert(Vec::new()).push(course);
        in_degree[course as usize] += 1;
    }
    
    let mut queue = VecDeque::new();
    for i in 0..n {
        if in_degree[i] == 0 {
            queue.push_back(i as i32);
        }
    }
    
    let mut order = Vec::new();
    
    while let Some(prereq) = queue.pop_front() {
        order.push(prereq);
        
        if let Some(courses) = graph.get(&prereq) {
            for &course in courses {
                in_degree[course as usize] -= 1;
                if in_degree[course as usize] == 0 {
                    queue.push_back(course);
                }
            }
        }
    }
    
    if order.len() == n {
        order
    } else {
        Vec::new()
    }
}

### Example 3: Clone Graph

**Python Implementation:**
```python
class GraphNode:
    def __init__(self, val=0, neighbors=None):
        self.val = val
        self.neighbors = neighbors if neighbors is not None else []

def clone_graph_dfs(node):
    """Clone graph using DFS"""
    if not node:
        return None
    
    visited = {}
    
    def dfs(node):
        if node in visited:
            return visited[node]
        
        clone = GraphNode(node.val)
        visited[node] = clone
        
        for neighbor in node.neighbors:
            clone.neighbors.append(dfs(neighbor))
        
        return clone
    
    return dfs(node)

def clone_graph_bfs(node):
    """Clone graph using BFS"""
    if not node:
        return None
    
    visited = {node: GraphNode(node.val)}
    queue = deque([node])
    
    while queue:
        current = queue.popleft()
        
        for neighbor in current.neighbors:
            if neighbor not in visited:
                visited[neighbor] = GraphNode(neighbor.val)
                queue.append(neighbor)
            
            visited[current].neighbors.append(visited[neighbor])
    
    return visited[node]
```

**Rust Implementation:**
```rust
use std::collections::{HashMap, VecDeque};
use std::rc::Rc;
use std::cell::RefCell;

#[derive(Debug, Clone)]
pub struct GraphNode {
    pub val: i32,
    pub neighbors: Vec<Rc<RefCell<GraphNode>>>,
}

impl GraphNode {
    pub fn new(val: i32) -> Self {
        GraphNode {
            val,
            neighbors: Vec::new(),
        }
    }
}

pub fn clone_graph_dfs(node: Option<Rc<RefCell<GraphNode>>>) -> Option<Rc<RefCell<GraphNode>>> {
    if let Some(node) = node {
        let mut visited: HashMap<i32, Rc<RefCell<GraphNode>>> = HashMap::new();
        Some(dfs(node, &mut visited))
    } else {
        None
    }
}

fn dfs(node: Rc<RefCell<GraphNode>>, visited: &mut HashMap<i32, Rc<RefCell<GraphNode>>>) -> Rc<RefCell<GraphNode>> {
    let val = node.borrow().val;
    
    if let Some(clone) = visited.get(&val) {
        return clone.clone();
    }
    
    let clone = Rc::new(RefCell::new(GraphNode::new(val)));
    visited.insert(val, clone.clone());
    
    for neighbor in &node.borrow().neighbors {
        let cloned_neighbor = dfs(neighbor.clone(), visited);
        clone.borrow_mut().neighbors.push(cloned_neighbor);
    }
    
    clone
}

### Example 4: Network Delay Time (Shortest Path)

**Python Implementation:**
```python
def network_delay_time(times, n, k):
    """Find time for signal to reach all nodes"""
    # Build graph
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    
    # Dijkstra's algorithm
    distances = {i: float('inf') for i in range(1, n + 1)}
    distances[k] = 0
    
    pq = [(0, k)]
    
    while pq:
        curr_dist, node = heapq.heappop(pq)
        
        if curr_dist > distances[node]:
            continue
        
        for neighbor, weight in graph[node]:
            new_dist = curr_dist + weight
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                heapq.heappush(pq, (new_dist, neighbor))
    
    max_dist = max(distances.values())
    return max_dist if max_dist != float('inf') else -1
```

**Rust Implementation:**
```rust
use std::collections::{HashMap, BinaryHeap};
use std::cmp::Reverse;

pub fn network_delay_time(times: Vec<Vec<i32>>, n: i32, k: i32) -> i32 {
    let mut graph: HashMap<i32, Vec<(i32, i32)>> = HashMap::new();
    
    for time in times {
        let (u, v, w) = (time[0], time[1], time[2]);
        graph.entry(u).or_insert(Vec::new()).push((v, w));
    }
    
    let mut distances = HashMap::new();
    for i in 1..=n {
        distances.insert(i, i32::MAX);
    }
    distances.insert(k, 0);
    
    let mut pq = BinaryHeap::new();
    pq.push(Reverse((0, k)));
    
    while let Some(Reverse((curr_dist, node))) = pq.pop() {
        if curr_dist > *distances.get(&node).unwrap_or(&i32::MAX) {
            continue;
        }
        
        if let Some(neighbors) = graph.get(&node) {
            for &(neighbor, weight) in neighbors {
                let new_dist = curr_dist + weight;
                if new_dist < *distances.get(&neighbor).unwrap_or(&i32::MAX) {
                    distances.insert(neighbor, new_dist);
                    pq.push(Reverse((new_dist, neighbor)));
                }
            }
        }
    }
    
    let max_dist = distances.values().max().unwrap_or(&i32::MAX);
    if *max_dist == i32::MAX {
        -1
    } else {
        *max_dist
    }
}

---

## Summary of When to Use Each Pattern

### Traversal Patterns
- **DFS**: Tree problems, path finding, cycle detection, topological sort
- **BFS**: Shortest path in unweighted graphs, level-order traversal, minimum steps

### Shortest Path Patterns
- **Dijkstra**: Single-source shortest path with non-negative weights
- **Bellman-Ford**: Single-source shortest path with negative weights, cycle detection
- **Floyd-Warshall**: All-pairs shortest path (not covered but worth mentioning)

### Structural Analysis
- **Cycle Detection**: Validating DAGs, dependency resolution
- **Topological Sort**: Task scheduling, build systems, course planning
- **Connected Components**: Network analysis, clustering, union-find problems
- **Strongly Connected Components**: Web link analysis, social networks

### Optimization Patterns
- **MST (Kruskal/Prim)**: Network design, clustering, minimum cost connections
- **Maximum Flow**: Network capacity, bipartite matching, assignment problems

### Special Graph Types
- **Bipartite**: Matching problems, two-coloring, assignment problems
- **Trees**: Hierarchical data, parsing, decision trees

### Critical Points
- **Articulation Points**: Network reliability, critical infrastructure
- **Bridges**: Network bridges, connectivity analysis

This guide provides a comprehensive foundation for solving graph problems. Practice implementing these patterns and recognizing when to apply each one based on the problem constraints and requirements.

def count_connected_components(graph):
    visited = set()
    count = 0
    
    def dfs(node):
        visited.add(node)
        for neighbor, _ in graph.graph.get(node, []):
            if neighbor not in visited:
                dfs(neighbor)
    
    for vertex in graph.get_vertices():
        if vertex not in visited:
            dfs(vertex)
            count += 1
    
    return count
```

**Rust Implementation:**
```rust
impl Graph {
    pub fn find_connected_components(&self) -> Vec<Vec<i32>> {
        let mut visited = HashSet::new();
        let mut components = Vec::new();
        
        fn dfs(graph: &Graph, node: i32, visited: &mut HashSet<i32>, component: &mut Vec<i32>) {
            visited.insert(node);
            component.push(node);
            
            if let Some(neighbors) = graph.graph.get(&node) {
                for &(neighbor, _) in neighbors {
                    if !visited.contains(&neighbor) {
                        dfs(graph, neighbor, visited, component);
                    }
                }
            }
        }
        
        for &vertex in &self.get_vertices() {
            if !visited.contains(&vertex) {
                let mut component = Vec::new();
                dfs(self, vertex, &mut visited, &mut component);
                components.push(component);
            }
        }
        
        components
    }
    
    pub fn count_connected_components(&self) -> usize {
        let mut visited = HashSet::new();
        let mut count = 0;
        
        fn dfs(graph: &Graph, node: i32, visited: &mut HashSet<i32>) {
            visited.insert(node);
            
            if let Some(neighbors) = graph.graph.get(&node) {
                for &(neighbor, _) in neighbors {
                    if !visited.contains(&neighbor) {
                        dfs(graph, neighbor, visited);
                    }
                }
            }
        }
        
        for &vertex in &self.get_vertices() {
            if !visited.contains(&vertex) {
                dfs(self, vertex, &mut visited);
                count += 1;
            }
        }
        
        count
    }
}
```

### Pattern 9: Strongly Connected Components (Kosaraju's Algorithm)

**When to use:** Finding strongly connected components in directed graphs, detecting cycles in directed graphs.

**Python Implementation:**
```python
def strongly_connected_components_kosaraju(graph):
    def dfs1(node, visited, stack):
        visited.add(node)
        for neighbor, _ in graph.graph.get(node, []):
            if neighbor not in visited:
                dfs1(neighbor, visited, stack)
        stack.append(node)
    
    def dfs2(node, visited, component, reversed_graph):
        visited.add(node)
        component.append(node)
        for neighbor in reversed_graph.get(node, []):
            if neighbor not in visited:
                dfs2(neighbor, visited, component, reversed_graph)
    
    # Step 1: Fill vertices in stack according to finishing times
    visited = set()
    stack = []
    for vertex in graph.get_vertices():
        if vertex not in visited:
            dfs1(vertex, visited, stack)
    
    # Step 2: Create reversed graph
    reversed_graph = defaultdict(list)
    for u in graph.graph:
        for v, _ in graph.graph[u]:
            reversed_graph[v].append(u)
    
    # Step 3: Process vertices in reverse finishing order
    visited = set()
    components = []
    
    while stack:
        vertex = stack.pop()
        if vertex not in visited:
            component = []
            dfs2(vertex, visited, component, reversed_graph)
            components.append(component)
    
    return components

**Rust Implementation:**
```rust
impl Graph {
    pub fn strongly_connected_components_kosaraju(&self) -> Vec<Vec<i32>> {
        fn dfs1(graph: &Graph, node: i32, visited: &mut HashSet<i32>, stack: &mut Vec<i32>) {
            visited.insert(node);
            if let Some(neighbors) = graph.graph.get(&node) {
                for &(neighbor, _) in neighbors {
                    if !visited.contains(&neighbor) {
                        dfs1(graph, neighbor, visited, stack);
                    }
                }
            }
            stack.push(node);
        }

        fn dfs2(graph: &Graph, node: i32, visited: &mut HashSet<i32>, component: &mut Vec<i32>, reversed_graph: &HashMap<i32, Vec<(i32, i32)>>) {
            visited.insert(node);
            component.push(node);
            if let Some(neighbors) = reversed_graph.get(&node) {
                for &(neighbor, _) in neighbors {
                    if !visited.contains(&neighbor) {
                        dfs2(graph, neighbor, visited, component, reversed_graph);
                    }
                }
            }
        }

        // Step 1: Fill vertices in stack according to finishing times
        let mut visited = HashSet::new();
        let mut stack = Vec::new();
        for vertex in self.get_vertices() {
            if !visited.contains(&vertex) {
                dfs1(self, vertex, &mut visited, &mut stack);
            }
        }

        // Step 2: Create reversed graph
        let mut reversed_graph = HashMap::new();
        for u in self.get_vertices() {
            if let Some(neighbors) = self.graph.get(&u) {
                for &(v, _) in neighbors {
                    reversed_graph.entry(v).or_insert_with(Vec::new).push((u, 0));
                }
            }
        }

        // Step 3: Process vertices in reverse finishing order
        visited.clear();
        let mut components = Vec::new();
        while let Some(vertex) = stack.pop() {
            if !visited.contains(&vertex) {
                let mut component = Vec::new();
                dfs2(self, vertex, &mut visited, &mut component, &reversed_graph);
                components.push(component);
            }
        }

        components
    }
}

I've created a comprehensive guide to graph problem patterns with complete implementations in both Python and Rust. This guide covers:

## Key Patterns Included:

1. **Graph Representation** - Adjacency list implementation
2. **Traversal Patterns** - DFS and BFS with multiple variations
3. **Shortest Path Algorithms** - Dijkstra's and Bellman-Ford
4. **Cycle Detection** - For both directed and undirected graphs
5. **Topological Sort** - Kahn's algorithm and DFS-based
6. **Connected Components** - Including strongly connected components (Kosaraju's and Tarjan's)
7. **Minimum Spanning Tree** - Kruskal's and Prim's algorithms
8. **Bipartite Graphs** - Detection and maximum matching
9. **Advanced Patterns** - Articulation points and bridges
10. **Real Problem Examples** - Word ladder, course scheduling, graph cloning, network delay

## Features:

- **Complete implementations** in both Python and Rust
- **When to use** guidelines for each pattern
- **Time and space complexity** considerations
- **Real-world problem examples** with solutions
- **Best practices** for each algorithm type

Each implementation includes:
- Clear, well-commented code
- Error handling where appropriate
- Efficient data structures
- Multiple approaches where applicable (iterative vs recursive)

The guide is structured to help you quickly identify which pattern to use based on problem characteristics and provides ready-to-use implementations for coding interviews and competitive programming.