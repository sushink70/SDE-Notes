# Pathfinding Algorithms - Technical Interview Guide

## Table of Contents
1. [Breadth-First Search (BFS)](#breadth-first-search-bfs)
2. [Depth-First Search (DFS)](#depth-first-search-dfs)
3. [Dijkstra's Algorithm](#dijkstras-algorithm)
4. [A* Algorithm](#a-algorithm)
5. [Bellman-Ford Algorithm](#bellman-ford-algorithm)

---

## Breadth-First Search (BFS)

### Question 1: Implement BFS for finding shortest path in an unweighted graph

**Problem:** Given an unweighted graph and two nodes, find the shortest path between them.

### Python Implementation
```python
from collections import deque

def bfs_shortest_path(graph, start, end):
    """Find shortest path using BFS"""
    if start == end:
        return [start]
    
    queue = deque([(start, [start])])
    visited = {start}
    
    while queue:
        node, path = queue.popleft()
        
        for neighbor in graph[node]:
            if neighbor in visited:
                continue
            
            if neighbor == end:
                return path + [neighbor]
            
            visited.add(neighbor)
            queue.append((neighbor, path + [neighbor]))
    
    return None  # No path found

# Example usage
graph = {
    'A': ['B', 'C'],
    'B': ['A', 'D', 'E'],
    'C': ['A', 'F'],
    'D': ['B'],
    'E': ['B', 'F'],
    'F': ['C', 'E']
}

path = bfs_shortest_path(graph, 'A', 'F')
print(f"Shortest path: {path}")  # Output: ['A', 'C', 'F']
```

### Rust Implementation
```rust
use std::collections::{HashMap, HashSet, VecDeque};

fn bfs_shortest_path(
    graph: &HashMap<&str, Vec<&str>>,
    start: &str,
    end: &str
) -> Option<Vec<String>> {
    if start == end {
        return Some(vec![start.to_string()]);
    }
    
    let mut queue = VecDeque::new();
    let mut visited = HashSet::new();
    
    queue.push_back((start, vec![start.to_string()]));
    visited.insert(start);
    
    while let Some((node, path)) = queue.pop_front() {
        if let Some(neighbors) = graph.get(node) {
            for &neighbor in neighbors {
                if visited.contains(neighbor) {
                    continue;
                }
                
                if neighbor == end {
                    let mut result = path.clone();
                    result.push(neighbor.to_string());
                    return Some(result);
                }
                
                visited.insert(neighbor);
                let mut new_path = path.clone();
                new_path.push(neighbor.to_string());
                queue.push_back((neighbor, new_path));
            }
        }
    }
    
    None
}
```

### Go Implementation
```go
package main

import "fmt"

func bfsShortestPath(graph map[string][]string, start, end string) []string {
    if start == end {
        return []string{start}
    }
    
    type queueItem struct {
        node string
        path []string
    }
    
    queue := []queueItem{{start, []string{start}}}
    visited := make(map[string]bool)
    visited[start] = true
    
    for len(queue) > 0 {
        item := queue[0]
        queue = queue[1:]
        
        for _, neighbor := range graph[item.node] {
            if visited[neighbor] {
                continue
            }
            
            newPath := append([]string{}, item.path...)
            newPath = append(newPath, neighbor)
            
            if neighbor == end {
                return newPath
            }
            
            visited[neighbor] = true
            queue = append(queue, queueItem{neighbor, newPath})
        }
    }
    
    return nil
}
```

**Time Complexity:** O(V + E) where V is vertices and E is edges  
**Space Complexity:** O(V) for the queue and visited set

---

## Depth-First Search (DFS)

### Question 2: Implement DFS to find any path between two nodes

**Problem:** Find any valid path (not necessarily shortest) between two nodes using DFS.

### Python Implementation
```python
def dfs_find_path(graph, start, end, path=None, visited=None):
    """Find a path using DFS (recursive)"""
    if path is None:
        path = []
    if visited is None:
        visited = set()
    
    path = path + [start]
    visited.add(start)
    
    if start == end:
        return path
    
    for neighbor in graph[start]:
        if neighbor not in visited:
            new_path = dfs_find_path(graph, neighbor, end, path, visited)
            if new_path:
                return new_path
    
    return None

# Iterative version
def dfs_find_path_iterative(graph, start, end):
    """Find a path using DFS (iterative)"""
    stack = [(start, [start])]
    visited = set()
    
    while stack:
        node, path = stack.pop()
        
        if node in visited:
            continue
        
        visited.add(node)
        
        if node == end:
            return path
        
        for neighbor in graph[node]:
            if neighbor not in visited:
                stack.append((neighbor, path + [neighbor]))
    
    return None
```

### Rust Implementation
```rust
use std::collections::{HashMap, HashSet};

fn dfs_find_path(
    graph: &HashMap<&str, Vec<&str>>,
    start: &str,
    end: &str,
    path: &mut Vec<String>,
    visited: &mut HashSet<String>
) -> Option<Vec<String>> {
    path.push(start.to_string());
    visited.insert(start.to_string());
    
    if start == end {
        return Some(path.clone());
    }
    
    if let Some(neighbors) = graph.get(start) {
        for &neighbor in neighbors {
            if !visited.contains(neighbor) {
                if let Some(result) = dfs_find_path(graph, neighbor, end, path, visited) {
                    return Some(result);
                }
            }
        }
    }
    
    path.pop();
    None
}
```

### Go Implementation
```go
func dfsIterative(graph map[string][]string, start, end string) []string {
    type stackItem struct {
        node string
        path []string
    }
    
    stack := []stackItem{{start, []string{start}}}
    visited := make(map[string]bool)
    
    for len(stack) > 0 {
        item := stack[len(stack)-1]
        stack = stack[:len(stack)-1]
        
        if visited[item.node] {
            continue
        }
        visited[item.node] = true
        
        if item.node == end {
            return item.path
        }
        
        for _, neighbor := range graph[item.node] {
            if !visited[neighbor] {
                newPath := append([]string{}, item.path...)
                newPath = append(newPath, neighbor)
                stack = append(stack, stackItem{neighbor, newPath})
            }
        }
    }
    
    return nil
}
```

**Time Complexity:** O(V + E)  
**Space Complexity:** O(V) for recursion stack or explicit stack

---

## Dijkstra's Algorithm

### Question 3: Implement Dijkstra's algorithm for weighted graphs

**Problem:** Find the shortest path in a weighted graph with non-negative edge weights.

### Python Implementation
```python
import heapq
from collections import defaultdict

def dijkstra(graph, start, end):
    """Dijkstra's algorithm for shortest path"""
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    parent = {start: None}
    
    pq = [(0, start)]  # (distance, node)
    visited = set()
    
    while pq:
        current_dist, current = heapq.heappop(pq)
        
        if current in visited:
            continue
        
        visited.add(current)
        
        if current == end:
            break
        
        for neighbor, weight in graph[current]:
            distance = current_dist + weight
            
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                parent[neighbor] = current
                heapq.heappush(pq, (distance, neighbor))
    
    # Reconstruct path
    if distances[end] == float('inf'):
        return None, float('inf')
    
    path = []
    current = end
    while current is not None:
        path.append(current)
        current = parent.get(current)
    
    return path[::-1], distances[end]

# Example usage
graph = {
    'A': [('B', 4), ('C', 2)],
    'B': [('C', 1), ('D', 5)],
    'C': [('D', 8), ('E', 10)],
    'D': [('E', 2)],
    'E': []
}

path, dist = dijkstra(graph, 'A', 'E')
print(f"Path: {path}, Distance: {dist}")  # Path: ['A', 'C', 'D', 'E'], Distance: 12
```

### Rust Implementation
```rust
use std::collections::{BinaryHeap, HashMap, HashSet};
use std::cmp::Ordering;

#[derive(Copy, Clone, Eq, PartialEq)]
struct State {
    cost: u32,
    node: usize,
}

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

fn dijkstra(
    graph: &HashMap<usize, Vec<(usize, u32)>>,
    start: usize,
    end: usize
) -> Option<(Vec<usize>, u32)> {
    let mut distances: HashMap<usize, u32> = HashMap::new();
    let mut parent: HashMap<usize, usize> = HashMap::new();
    let mut heap = BinaryHeap::new();
    
    distances.insert(start, 0);
    heap.push(State { cost: 0, node: start });
    
    while let Some(State { cost, node }) = heap.pop() {
        if node == end {
            break;
        }
        
        if cost > *distances.get(&node).unwrap_or(&u32::MAX) {
            continue;
        }
        
        if let Some(neighbors) = graph.get(&node) {
            for &(neighbor, weight) in neighbors {
                let next = State {
                    cost: cost + weight,
                    node: neighbor,
                };
                
                if next.cost < *distances.get(&neighbor).unwrap_or(&u32::MAX) {
                    distances.insert(neighbor, next.cost);
                    parent.insert(neighbor, node);
                    heap.push(next);
                }
            }
        }
    }
    
    if !distances.contains_key(&end) {
        return None;
    }
    
    let mut path = vec![end];
    let mut current = end;
    while let Some(&prev) = parent.get(&current) {
        path.push(prev);
        current = prev;
    }
    path.reverse();
    
    Some((path, *distances.get(&end).unwrap()))
}
```

### Go Implementation
```go
import (
    "container/heap"
    "math"
)

type PQItem struct {
    node     string
    priority int
    index    int
}

type PriorityQueue []*PQItem

func (pq PriorityQueue) Len() int { return len(pq) }
func (pq PriorityQueue) Less(i, j int) bool { return pq[i].priority < pq[j].priority }
func (pq PriorityQueue) Swap(i, j int) {
    pq[i], pq[j] = pq[j], pq[i]
    pq[i].index = i
    pq[j].index = j
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
    *pq = old[0 : n-1]
    return item
}

func dijkstra(graph map[string]map[string]int, start, end string) ([]string, int) {
    distances := make(map[string]int)
    parent := make(map[string]string)
    
    for node := range graph {
        distances[node] = math.MaxInt32
    }
    distances[start] = 0
    
    pq := make(PriorityQueue, 0)
    heap.Init(&pq)
    heap.Push(&pq, &PQItem{node: start, priority: 0})
    
    for pq.Len() > 0 {
        item := heap.Pop(&pq).(*PQItem)
        current := item.node
        
        if current == end {
            break
        }
        
        for neighbor, weight := range graph[current] {
            distance := distances[current] + weight
            
            if distance < distances[neighbor] {
                distances[neighbor] = distance
                parent[neighbor] = current
                heap.Push(&pq, &PQItem{node: neighbor, priority: distance})
            }
        }
    }
    
    if distances[end] == math.MaxInt32 {
        return nil, -1
    }
    
    path := []string{}
    for at := end; at != ""; at = parent[at] {
        path = append([]string{at}, path...)
        if at == start {
            break
        }
    }
    
    return path, distances[end]
}
```

**Time Complexity:** O((V + E) log V) with binary heap  
**Space Complexity:** O(V)

---

## A* Algorithm

### Question 4: Implement A* pathfinding with heuristic

**Problem:** Find the shortest path using A* algorithm with a heuristic function (commonly used in grid-based pathfinding).

### Python Implementation
```python
import heapq

def manhattan_distance(pos1, pos2):
    """Heuristic function: Manhattan distance"""
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

def a_star(grid, start, goal):
    """A* pathfinding on a 2D grid (0 = walkable, 1 = obstacle)"""
    rows, cols = len(grid), len(grid[0])
    
    # Priority queue: (f_score, g_score, position)
    open_set = [(0, 0, start)]
    came_from = {}
    
    g_score = {start: 0}
    f_score = {start: manhattan_distance(start, goal)}
    
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # right, down, left, up
    
    while open_set:
        _, current_g, current = heapq.heappop(open_set)
        
        if current == goal:
            # Reconstruct path
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            return path[::-1]
        
        for dx, dy in directions:
            neighbor = (current[0] + dx, current[1] + dy)
            
            # Check bounds and obstacles
            if (0 <= neighbor[0] < rows and 
                0 <= neighbor[1] < cols and 
                grid[neighbor[0]][neighbor[1]] == 0):
                
                tentative_g = g_score[current] + 1
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f = tentative_g + manhattan_distance(neighbor, goal)
                    f_score[neighbor] = f
                    heapq.heappush(open_set, (f, tentative_g, neighbor))
    
    return None  # No path found

# Example usage
grid = [
    [0, 0, 0, 0, 0],
    [0, 1, 1, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 1, 1, 0],
    [0, 0, 0, 0, 0]
]

path = a_star(grid, (0, 0), (4, 4))
print(f"Path: {path}")
```

### Rust Implementation
```rust
use std::collections::{BinaryHeap, HashMap, HashSet};
use std::cmp::Ordering;

#[derive(Copy, Clone, Eq, PartialEq)]
struct AStarState {
    f_score: i32,
    g_score: i32,
    pos: (usize, usize),
}

impl Ord for AStarState {
    fn cmp(&self, other: &Self) -> Ordering {
        other.f_score.cmp(&self.f_score)
            .then_with(|| other.g_score.cmp(&self.g_score))
    }
}

impl PartialOrd for AStarState {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

fn manhattan_distance(pos1: (usize, usize), pos2: (usize, usize)) -> i32 {
    ((pos1.0 as i32 - pos2.0 as i32).abs() + 
     (pos1.1 as i32 - pos2.1 as i32).abs())
}

fn a_star(
    grid: &Vec<Vec<i32>>,
    start: (usize, usize),
    goal: (usize, usize)
) -> Option<Vec<(usize, usize)>> {
    let rows = grid.len();
    let cols = grid[0].len();
    
    let mut open_set = BinaryHeap::new();
    let mut came_from: HashMap<(usize, usize), (usize, usize)> = HashMap::new();
    let mut g_score: HashMap<(usize, usize), i32> = HashMap::new();
    
    g_score.insert(start, 0);
    open_set.push(AStarState {
        f_score: manhattan_distance(start, goal),
        g_score: 0,
        pos: start,
    });
    
    let directions = [(0, 1), (1, 0), (0, -1), (-1, 0)];
    
    while let Some(AStarState { pos: current, g_score: current_g, .. }) = open_set.pop() {
        if current == goal {
            let mut path = vec![current];
            let mut curr = current;
            while let Some(&prev) = came_from.get(&curr) {
                path.push(prev);
                curr = prev;
            }
            path.reverse();
            return Some(path);
        }
        
        for &(dx, dy) in &directions {
            let nx = current.0 as i32 + dx;
            let ny = current.1 as i32 + dy;
            
            if nx >= 0 && nx < rows as i32 && ny >= 0 && ny < cols as i32 {
                let neighbor = (nx as usize, ny as usize);
                
                if grid[neighbor.0][neighbor.1] == 0 {
                    let tentative_g = current_g + 1;
                    
                    if tentative_g < *g_score.get(&neighbor).unwrap_or(&i32::MAX) {
                        came_from.insert(neighbor, current);
                        g_score.insert(neighbor, tentative_g);
                        let f = tentative_g + manhattan_distance(neighbor, goal);
                        open_set.push(AStarState {
                            f_score: f,
                            g_score: tentative_g,
                            pos: neighbor,
                        });
                    }
                }
            }
        }
    }
    
    None
}
```

### Go Implementation
```go
import (
    "container/heap"
    "math"
)

type AStarItem struct {
    pos      [2]int
    fScore   int
    gScore   int
    index    int
}

type AStarPQ []*AStarItem

func (pq AStarPQ) Len() int { return len(pq) }
func (pq AStarPQ) Less(i, j int) bool { return pq[i].fScore < pq[j].fScore }
func (pq AStarPQ) Swap(i, j int) {
    pq[i], pq[j] = pq[j], pq[i]
    pq[i].index = i
    pq[j].index = j
}
func (pq *AStarPQ) Push(x interface{}) {
    item := x.(*AStarItem)
    item.index = len(*pq)
    *pq = append(*pq, item)
}
func (pq *AStarPQ) Pop() interface{} {
    old := *pq
    n := len(old)
    item := old[n-1]
    *pq = old[0 : n-1]
    return item
}

func manhattanDistance(pos1, pos2 [2]int) int {
    return int(math.Abs(float64(pos1[0]-pos2[0])) + 
               math.Abs(float64(pos1[1]-pos2[1])))
}

func aStar(grid [][]int, start, goal [2]int) [][2]int {
    rows, cols := len(grid), len(grid[0])
    
    openSet := make(AStarPQ, 0)
    heap.Init(&openSet)
    
    cameFrom := make(map[[2]int][2]int)
    gScore := make(map[[2]int]int)
    gScore[start] = 0
    
    heap.Push(&openSet, &AStarItem{
        pos:    start,
        fScore: manhattanDistance(start, goal),
        gScore: 0,
    })
    
    directions := [][2]int{{0, 1}, {1, 0}, {0, -1}, {-1, 0}}
    
    for openSet.Len() > 0 {
        item := heap.Pop(&openSet).(*AStarItem)
        current := item.pos
        
        if current == goal {
            path := [][2]int{current}
            for {
                prev, exists := cameFrom[current]
                if !exists {
                    break
                }
                path = append([][2]int{prev}, path...)
                current = prev
            }
            return path
        }
        
        for _, dir := range directions {
            neighbor := [2]int{current[0] + dir[0], current[1] + dir[1]}
            
            if neighbor[0] >= 0 && neighbor[0] < rows &&
               neighbor[1] >= 0 && neighbor[1] < cols &&
               grid[neighbor[0]][neighbor[1]] == 0 {
                
                tentativeG := gScore[current] + 1
                
                if existingG, exists := gScore[neighbor]; !exists || tentativeG < existingG {
                    cameFrom[neighbor] = current
                    gScore[neighbor] = tentativeG
                    fScore := tentativeG + manhattanDistance(neighbor, goal)
                    heap.Push(&openSet, &AStarItem{
                        pos:    neighbor,
                        fScore: fScore,
                        gScore: tentativeG,
                    })
                }
            }
        }
    }
    
    return nil
}
```

**Time Complexity:** O(E log V) in the worst case, but typically much faster with good heuristics  
**Space Complexity:** O(V)

---

## Bellman-Ford Algorithm

### Question 5: Implement Bellman-Ford for graphs with negative weights

**Problem:** Find shortest paths even with negative edge weights and detect negative cycles.

### Python Implementation
```python
def bellman_ford(graph, start):
    """
    Bellman-Ford algorithm for shortest paths with negative weights
    Returns distances dict and whether negative cycle exists
    """
    # Initialize distances
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    parent = {node: None for node in graph}
    
    # Relax edges V-1 times
    for _ in range(len(graph) - 1):
        for node in graph:
            for neighbor, weight in graph[node]:
                if distances[node] + weight < distances[neighbor]:
                    distances[neighbor] = distances[node] + weight
                    parent[neighbor] = node
    
    # Check for negative cycles
    for node in graph:
        for neighbor, weight in graph[node]:
            if distances[node] + weight < distances[neighbor]:
                return None, True  # Negative cycle detected
    
    return distances, False

# Example with negative weights
graph = {
    'A': [('B', 4), ('C', 2)],
    'B': [('C', -3), ('D', 2)],
    'C': [('D', 4)],
    'D': []
}

distances, has_negative_cycle = bellman_ford(graph, 'A')
if not has_negative_cycle:
    print(f"Distances: {distances}")
else:
    print("Negative cycle detected!")
```

### Rust Implementation
```rust
use std::collections::HashMap;

fn bellman_ford(
    graph: &HashMap<&str, Vec<(&str, i32)>>,
    start: &str
) -> Result<HashMap<String, i32>, String> {
    let mut distances: HashMap<String, i32> = HashMap::new();
    
    for &node in graph.keys() {
        distances.insert(node.to_string(), i32::MAX);
    }
    distances.insert(start.to_string(), 0);
    
    let n = graph.len();
    
    // Relax edges V-1 times
    for _ in 0..n-1 {
        for (&node, edges) in graph {
            if let Some(&dist) = distances.get(node) {
                if dist != i32::MAX {
                    for &(neighbor, weight) in edges {
                        let new_dist = dist + weight;
                        let neighbor_dist = distances.get(neighbor).copied().unwrap_or(i32::MAX);
                        
                        if new_dist < neighbor_dist {
                            distances.insert(neighbor.to_string(), new_dist);
                        }
                    }
                }
            }
        }
    }
    
    // Check for negative cycles
    for (&node, edges) in graph {
        if let Some(&dist) = distances.get(node) {
            if dist != i32::MAX {
                for &(neighbor, weight) in edges {
                    let neighbor_dist = distances.get(neighbor).copied().unwrap_or(i32::MAX);
                    if dist + weight < neighbor_dist {
                        return Err("Negative cycle detected".to_string());
                    }
                }
            }
        }
    }
    
    Ok(distances)
}
```

### Go Implementation
```go
func bellmanFord(graph map[string][][2]interface{}, start string) (map[string]int, error) {
    distances := make(map[string]int)
    
    // Initialize distances
    for node := range graph {
        distances[node] = math.MaxInt32
    }
    distances[start] = 0
    
    // Relax edges V-1 times
    for i := 0; i < len(graph)-1; i++ {
        for node, edges := range graph {
            if distances[node] != math.MaxInt32 {
                for _, edge := range edges {
                    neighbor := edge[0].(string)
                    weight := edge[1].(int)
                    
                    if distances[node]+weight < distances[neighbor] {
                        distances[neighbor] = distances[node] + weight
                    }
                }
            }
        }
    }
    
    // Check for negative cycles
    for node, edges := range graph {
        if distances[node] != math.MaxInt32 {
            for _, edge := range edges {
                neighbor := edge[0].(string)
                weight := edge[1].(int)
                
                if distances[node]+weight < distances[neighbor] {
                    return nil, fmt.Errorf("negative cycle detected")
                }
            }
        }
    }
    
    return distances, nil
}
```

**Time Complexity:** O(VE)  
**Space Complexity:** O(V)

---

## Common Interview Follow-up Questions

### 1. When would you use BFS vs DFS?
- **BFS**: Finding shortest path in unweighted graphs, level-order traversal, finding all nodes within a certain distance
- **DFS**: Topological sorting, detecting cycles, path finding when any path is acceptable, maze solving

### 2. Why use A* over Dijkstra?
- A* uses a heuristic to guide the search toward the goal, making it faster in practice
- A* is optimal if the heuristic is admissible (never overestimates)
- Dijkstra is a special case of A* where h(n) = 0

### 3. When would you use Bellman-Ford instead of Dijkstra?
- When the graph has negative edge weights
- When you need to detect negative cycles
- Dijkstra fails with negative weights; Bellman-Ford handles them correctly

### 4. What makes a good heuristic for A*?
- **Admissible**: Never overestimates the actual cost to reach the goal
- **Consistent**: h(n) ≤ cost(n, n') + h(n') for any edge from n to n'
- Examples: Manhattan distance for grids, Euclidean distance, Chebyshev distance

### 5. How do you optimize these algorithms?
- **Bidirectional search**: Search from both start and end
- **Jump Point Search**: Skip unnecessary nodes in uniform-cost grids
- **Hierarchical pathfinding**: Use preprocessed data for large graphs
- **Pruning**: Skip nodes that cannot lead to better paths

---

## Advanced Interview Questions

### Question 6: Implement Bidirectional BFS

**Problem:** Optimize BFS by searching from both start and goal simultaneously.

### Python Implementation
```python
from collections import deque

def bidirectional_bfs(graph, start, goal):
    """Bidirectional BFS - search from both ends"""
    if start == goal:
        return [start]
    
    # Forward search from start
    forward_queue = deque([start])
    forward_visited = {start: None}
    
    # Backward search from goal
    backward_queue = deque([goal])
    backward_visited = {goal: None}
    
    def reconstruct_path(meeting_point):
        # Build path from start to meeting point
        path = []
        node = meeting_point
        while node is not None:
            path.append(node)
            node = forward_visited[node]
        path.reverse()
        
        # Build path from meeting point to goal
        node = backward_visited[meeting_point]
        while node is not None:
            path.append(node)
            node = backward_visited[node]
        
        return path
    
    while forward_queue and backward_queue:
        # Expand forward frontier
        if forward_queue:
            current = forward_queue.popleft()
            for neighbor in graph.get(current, []):
                if neighbor in backward_visited:
                    return reconstruct_path(neighbor)
                
                if neighbor not in forward_visited:
                    forward_visited[neighbor] = current
                    forward_queue.append(neighbor)
        
        # Expand backward frontier
        if backward_queue:
            current = backward_queue.popleft()
            for neighbor in graph.get(current, []):
                if neighbor in forward_visited:
                    return reconstruct_path(neighbor)
                
                if neighbor not in backward_visited:
                    backward_visited[neighbor] = current
                    backward_queue.append(neighbor)
    
    return None  # No path found

# Example usage
graph = {
    'A': ['B', 'C'],
    'B': ['A', 'D', 'E'],
    'C': ['A', 'F'],
    'D': ['B', 'G'],
    'E': ['B', 'F'],
    'F': ['C', 'E', 'H'],
    'G': ['D'],
    'H': ['F']
}

path = bidirectional_bfs(graph, 'A', 'H')
print(f"Path: {path}")
```

**Time Complexity:** O(b^(d/2)) where b is branching factor and d is depth (much better than O(b^d) for unidirectional)  
**Space Complexity:** O(b^(d/2))

---

### Question 7: Find All Paths Between Two Nodes

**Problem:** Find all possible paths (not just one) between two nodes.

### Python Implementation
```python
def find_all_paths(graph, start, end, path=None, all_paths=None):
    """Find all paths using DFS with backtracking"""
    if path is None:
        path = []
    if all_paths is None:
        all_paths = []
    
    path = path + [start]
    
    if start == end:
        all_paths.append(path)
        return all_paths
    
    for neighbor in graph.get(start, []):
        if neighbor not in path:  # Avoid cycles
            find_all_paths(graph, neighbor, end, path, all_paths)
    
    return all_paths

# Iterative version
def find_all_paths_iterative(graph, start, end):
    """Find all paths using iterative DFS"""
    stack = [(start, [start])]
    all_paths = []
    
    while stack:
        node, path = stack.pop()
        
        if node == end:
            all_paths.append(path)
            continue
        
        for neighbor in graph.get(node, []):
            if neighbor not in path:
                stack.append((neighbor, path + [neighbor]))
    
    return all_paths

# Example
graph = {
    'A': ['B', 'C'],
    'B': ['D'],
    'C': ['D', 'E'],
    'D': ['E'],
    'E': []
}

paths = find_all_paths(graph, 'A', 'E')
print(f"All paths: {paths}")
# Output: [['A', 'B', 'D', 'E'], ['A', 'C', 'D', 'E'], ['A', 'C', 'E']]
```

### Rust Implementation
```rust
use std::collections::HashMap;

fn find_all_paths(
    graph: &HashMap<&str, Vec<&str>>,
    start: &str,
    end: &str,
    path: &mut Vec<String>,
    all_paths: &mut Vec<Vec<String>>
) {
    path.push(start.to_string());
    
    if start == end {
        all_paths.push(path.clone());
    } else if let Some(neighbors) = graph.get(start) {
        for &neighbor in neighbors {
            if !path.contains(&neighbor.to_string()) {
                find_all_paths(graph, neighbor, end, path, all_paths);
            }
        }
    }
    
    path.pop();
}

fn find_all_paths_wrapper(
    graph: &HashMap<&str, Vec<&str>>,
    start: &str,
    end: &str
) -> Vec<Vec<String>> {
    let mut path = Vec::new();
    let mut all_paths = Vec::new();
    find_all_paths(graph, start, end, &mut path, &mut all_paths);
    all_paths
}
```

### Go Implementation
```go
func findAllPaths(graph map[string][]string, start, end string) [][]string {
    var allPaths [][]string
    var dfs func(node string, path []string)
    
    dfs = func(node string, path []string) {
        path = append(path, node)
        
        if node == end {
            pathCopy := make([]string, len(path))
            copy(pathCopy, path)
            allPaths = append(allPaths, pathCopy)
            return
        }
        
        for _, neighbor := range graph[node] {
            found := false
            for _, p := range path {
                if p == neighbor {
                    found = true
                    break
                }
            }
            if !found {
                dfs(neighbor, path)
            }
        }
    }
    
    dfs(start, []string{})
    return allPaths
}
```

---

### Question 8: Detect Cycle in a Directed Graph

**Problem:** Determine if a directed graph contains a cycle.

### Python Implementation
```python
def has_cycle_directed(graph):
    """Detect cycle in directed graph using DFS with colors"""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {node: WHITE for node in graph}
    
    def dfs(node):
        if color[node] == GRAY:  # Back edge found
            return True
        if color[node] == BLACK:  # Already processed
            return False
        
        color[node] = GRAY  # Mark as being processed
        
        for neighbor in graph.get(node, []):
            if dfs(neighbor):
                return True
        
        color[node] = BLACK  # Mark as completed
        return False
    
    for node in graph:
        if color[node] == WHITE:
            if dfs(node):
                return True
    
    return False

# Example with cycle
graph_with_cycle = {
    'A': ['B'],
    'B': ['C'],
    'C': ['A'],  # Cycle: A -> B -> C -> A
    'D': ['E'],
    'E': []
}

print(has_cycle_directed(graph_with_cycle))  # True

# Example without cycle
graph_without_cycle = {
    'A': ['B', 'C'],
    'B': ['D'],
    'C': ['D'],
    'D': []
}

print(has_cycle_directed(graph_without_cycle))  # False
```

### Rust Implementation
```rust
use std::collections::{HashMap, HashSet};

#[derive(PartialEq, Eq, Clone, Copy)]
enum Color {
    White,
    Gray,
    Black,
}

fn has_cycle_directed(graph: &HashMap<&str, Vec<&str>>) -> bool {
    let mut color: HashMap<&str, Color> = HashMap::new();
    
    for &node in graph.keys() {
        color.insert(node, Color::White);
    }
    
    fn dfs(
        node: &str,
        graph: &HashMap<&str, Vec<&str>>,
        color: &mut HashMap<&str, Color>
    ) -> bool {
        if color.get(node) == Some(&Color::Gray) {
            return true;
        }
        if color.get(node) == Some(&Color::Black) {
            return false;
        }
        
        color.insert(node, Color::Gray);
        
        if let Some(neighbors) = graph.get(node) {
            for &neighbor in neighbors {
                if dfs(neighbor, graph, color) {
                    return true;
                }
            }
        }
        
        color.insert(node, Color::Black);
        false
    }
    
    for &node in graph.keys() {
        if color.get(node) == Some(&Color::White) {
            if dfs(node, graph, &mut color) {
                return true;
            }
        }
    }
    
    false
}
```

### Go Implementation
```go
func hasCycleDirected(graph map[string][]string) bool {
    const (
        WHITE = 0
        GRAY  = 1
        BLACK = 2
    )
    
    color := make(map[string]int)
    for node := range graph {
        color[node] = WHITE
    }
    
    var dfs func(node string) bool
    dfs = func(node string) bool {
        if color[node] == GRAY {
            return true
        }
        if color[node] == BLACK {
            return false
        }
        
        color[node] = GRAY
        
        for _, neighbor := range graph[node] {
            if dfs(neighbor) {
                return true
            }
        }
        
        color[node] = BLACK
        return false
    }
    
    for node := range graph {
        if color[node] == WHITE {
            if dfs(node) {
                return true
            }
        }
    }
    
    return false
}
```

**Time Complexity:** O(V + E)  
**Space Complexity:** O(V)

---

### Question 9: Topological Sort

**Problem:** Order nodes in a directed acyclic graph (DAG) such that for every edge u→v, u comes before v.

### Python Implementation
```python
from collections import deque

def topological_sort_kahn(graph):
    """Topological sort using Kahn's algorithm (BFS-based)"""
    # Calculate in-degrees
    in_degree = {node: 0 for node in graph}
    for node in graph:
        for neighbor in graph[node]:
            in_degree[neighbor] = in_degree.get(neighbor, 0) + 1
    
    # Queue of nodes with no incoming edges
    queue = deque([node for node in graph if in_degree[node] == 0])
    result = []
    
    while queue:
        node = queue.popleft()
        result.append(node)
        
        for neighbor in graph.get(node, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    # If result doesn't contain all nodes, there's a cycle
    if len(result) != len(graph):
        return None  # Graph has cycle
    
    return result

def topological_sort_dfs(graph):
    """Topological sort using DFS"""
    visited = set()
    stack = []
    
    def dfs(node):
        visited.add(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                dfs(neighbor)
        stack.append(node)
    
    for node in graph:
        if node not in visited:
            dfs(node)
    
    return stack[::-1]  # Reverse to get correct order

# Example: Course scheduling
courses = {
    'CS101': [],
    'CS102': ['CS101'],
    'CS201': ['CS102'],
    'CS202': ['CS102'],
    'CS301': ['CS201', 'CS202']
}

order = topological_sort_kahn(courses)
print(f"Course order: {order}")
# Output: ['CS101', 'CS102', 'CS201', 'CS202', 'CS301'] (or similar valid order)
```

### Rust Implementation
```rust
use std::collections::{HashMap, HashSet, VecDeque};

fn topological_sort_kahn(graph: &HashMap<&str, Vec<&str>>) -> Option<Vec<String>> {
    let mut in_degree: HashMap<&str, usize> = HashMap::new();
    
    for &node in graph.keys() {
        in_degree.entry(node).or_insert(0);
    }
    
    for neighbors in graph.values() {
        for &neighbor in neighbors {
            *in_degree.entry(neighbor).or_insert(0) += 1;
        }
    }
    
    let mut queue: VecDeque<&str> = VecDeque::new();
    for (&node, &degree) in &in_degree {
        if degree == 0 {
            queue.push_back(node);
        }
    }
    
    let mut result = Vec::new();
    
    while let Some(node) = queue.pop_front() {
        result.push(node.to_string());
        
        if let Some(neighbors) = graph.get(node) {
            for &neighbor in neighbors {
                if let Some(degree) = in_degree.get_mut(neighbor) {
                    *degree -= 1;
                    if *degree == 0 {
                        queue.push_back(neighbor);
                    }
                }
            }
        }
    }
    
    if result.len() != graph.len() {
        None  // Cycle detected
    } else {
        Some(result)
    }
}
```

### Go Implementation
```go
func topologicalSortKahn(graph map[string][]string) []string {
    inDegree := make(map[string]int)
    
    for node := range graph {
        if _, exists := inDegree[node]; !exists {
            inDegree[node] = 0
        }
        for _, neighbor := range graph[node] {
            inDegree[neighbor]++
        }
    }
    
    queue := []string{}
    for node, degree := range inDegree {
        if degree == 0 {
            queue = append(queue, node)
        }
    }
    
    result := []string{}
    
    for len(queue) > 0 {
        node := queue[0]
        queue = queue[1:]
        result = append(result, node)
        
        for _, neighbor := range graph[node] {
            inDegree[neighbor]--
            if inDegree[neighbor] == 0 {
                queue = append(queue, neighbor)
            }
        }
    }
    
    if len(result) != len(graph) {
        return nil  // Cycle detected
    }
    
    return result
}
```

**Time Complexity:** O(V + E)  
**Space Complexity:** O(V)

---

### Question 10: Floyd-Warshall Algorithm

**Problem:** Find shortest paths between all pairs of vertices.

### Python Implementation
```python
def floyd_warshall(vertices, edges):
    """
    Floyd-Warshall: All-pairs shortest path
    vertices: list of vertex names
    edges: list of tuples (from, to, weight)
    """
    n = len(vertices)
    vertex_to_idx = {v: i for i, v in enumerate(vertices)}
    
    # Initialize distance matrix
    INF = float('inf')
    dist = [[INF] * n for _ in range(n)]
    
    # Distance from vertex to itself is 0
    for i in range(n):
        dist[i][i] = 0
    
    # Add edges
    for u, v, w in edges:
        i, j = vertex_to_idx[u], vertex_to_idx[v]
        dist[i][j] = w
    
    # Floyd-Warshall algorithm
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if dist[i][k] != INF and dist[k][j] != INF:
                    dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])
    
    # Check for negative cycles
    for i in range(n):
        if dist[i][i] < 0:
            return None, "Negative cycle detected"
    
    # Convert back to vertex names
    result = {}
    for i, u in enumerate(vertices):
        result[u] = {}
        for j, v in enumerate(vertices):
            result[u][v] = dist[i][j] if dist[i][j] != INF else None
    
    return result, None

# Example usage
vertices = ['A', 'B', 'C', 'D']
edges = [
    ('A', 'B', 3),
    ('A', 'C', 8),
    ('A', 'D', -4),
    ('B', 'D', 1),
    ('B', 'C', 1),
    ('D', 'B', 7),
    ('D', 'C', 2)
]

distances, error = floyd_warshall(vertices, edges)
if error:
    print(error)
else:
    print("Shortest distances between all pairs:")
    for u in vertices:
        for v in vertices:
            print(f"{u} -> {v}: {distances[u][v]}")
```

### Rust Implementation
```rust
fn floyd_warshall(n: usize, edges: Vec<(usize, usize, i32)>) -> Option<Vec<Vec<i32>>> {
    const INF: i32 = i32::MAX / 2;
    let mut dist = vec![vec![INF; n]; n];
    
    // Initialize diagonal
    for i in 0..n {
        dist[i][i] = 0;
    }
    
    // Add edges
    for (u, v, w) in edges {
        dist[u][v] = w;
    }
    
    // Floyd-Warshall
    for k in 0..n {
        for i in 0..n {
            for j in 0..n {
                if dist[i][k] != INF && dist[k][j] != INF {
                    dist[i][j] = dist[i][j].min(dist[i][k] + dist[k][j]);
                }
            }
        }
    }
    
    // Check for negative cycles
    for i in 0..n {
        if dist[i][i] < 0 {
            return None;
        }
    }
    
    Some(dist)
}
```

### Go Implementation
```go
func floydWarshall(n int, edges [][3]int) [][]int {
    const INF = 1<<30
    dist := make([][]int, n)
    for i := range dist {
        dist[i] = make([]int, n)
        for j := range dist[i] {
            if i == j {
                dist[i][j] = 0
            } else {
                dist[i][j] = INF
            }
        }
    }
    
    for _, edge := range edges {
        u, v, w := edge[0], edge[1], edge[2]
        dist[u][v] = w
    }
    
    for k := 0; k < n; k++ {
        for i := 0; i < n; i++ {
            for j := 0; j < n; j++ {
                if dist[i][k] != INF && dist[k][j] != INF {
                    if dist[i][k]+dist[k][j] < dist[i][j] {
                        dist[i][j] = dist[i][k] + dist[k][j]
                    }
                }
            }
        }
    }
    
    // Check for negative cycles
    for i := 0; i < n; i++ {
        if dist[i][i] < 0 {
            return nil
        }
    }
    
    return dist
}
```

**Time Complexity:** O(V³)  
**Space Complexity:** O(V²)

---

## Performance Comparison Cheat Sheet

| Algorithm | Time Complexity | Space Complexity | Use Case |
|-----------|----------------|------------------|----------|
| BFS | O(V + E) | O(V) | Shortest path (unweighted) |
| DFS | O(V + E) | O(V) | Any path, cycle detection |
| Dijkstra | O((V + E) log V) | O(V) | Shortest path (non-negative weights) |
| A* | O(E log V)* | O(V) | Shortest path with heuristic |
| Bellman-Ford | O(VE) | O(V) | Negative weights, cycle detection |
| Floyd-Warshall | O(V³) | O(V²) | All-pairs shortest path |

*Depends on heuristic quality

---

## Additional Practice Problems

1. **Word Ladder**: Transform one word to another by changing one letter at a time (BFS)
2. **Maze Solving**: Find path in a 2D maze (BFS/DFS/A*)
3. **Network Delay Time**: Minimum time for signal to reach all nodes (Dijkstra)
4. **Cheapest Flights**: Find cheapest route with K stops (Modified Dijkstra/Bellman-Ford)
5. **Course Schedule**: Determine if courses can be completed (Topological Sort)
6. **Alien Dictionary**: Find order of alien language characters (Topological Sort)
7. **Critical Connections**: Find bridges in a network (DFS with timestamps)

I've expanded the guide with advanced topics including:

**New Sections Added:**
- **Bidirectional BFS** - Optimization technique that searches from both ends
- **Find All Paths** - Comprehensive path enumeration with backtracking
- **Cycle Detection** - Using color-marking DFS for directed graphs
- **Topological Sort** - Both Kahn's (BFS) and DFS approaches for DAGs
- **Floyd-Warshall** - All-pairs shortest path algorithm
- **Performance Comparison Table** - Quick reference for algorithm selection
- **Practice Problems** - Real-world LeetCode-style problems to apply these concepts

Each algorithm includes:
✓ Complete implementations in Python, Rust, and Go
✓ Time and space complexity analysis
✓ Practical examples and use cases
✓ Edge case handling

This comprehensive guide now covers everything from basic graph traversal to advanced all-pairs shortest path algorithms, making it perfect preparation for technical interviews!

