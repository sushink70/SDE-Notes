use std::collections::{HashMap, HashSet, VecDeque, BinaryHeap};
use std::cmp::Ordering;

// ============================================================================
// PROBLEM 1: Basic BFS - Shortest Path in Unweighted Grid
// ============================================================================

fn bfs_grid_shortest_path(
    grid: &Vec<Vec<i32>>,
    start: (usize, usize),
    end: (usize, usize),
) -> i32 {
    if grid.is_empty() || grid[start.0][start.1] == 1 {
        return -1;
    }

    let rows = grid.len();
    let cols = grid[0].len();
    let mut queue = VecDeque::new();
    let mut visited = HashSet::new();
    let directions = [(0, 1), (1, 0), (0, -1), (-1, 0)];

    queue.push_back((start.0, start.1, 0));
    visited.insert(start);

    while let Some((r, c, dist)) = queue.pop_front() {
        if (r, c) == end {
            return dist;
        }

        for (dr, dc) in &directions {
            let nr = r as i32 + dr;
            let nc = c as i32 + dc;

            if nr >= 0 && nr < rows as i32 && nc >= 0 && nc < cols as i32 {
                let nr = nr as usize;
                let nc = nc as usize;

                if !visited.contains(&(nr, nc)) && grid[nr][nc] == 0 {
                    visited.insert((nr, nc));
                    queue.push_back((nr, nc, dist + 1));
                }
            }
        }
    }

    -1
}

// ============================================================================
// PROBLEM 2: DFS - Find All Paths
// ============================================================================

fn dfs_all_paths(
    graph: &HashMap<i32, Vec<i32>>,
    start: i32,
    end: i32,
) -> Vec<Vec<i32>> {
    let mut all_paths = Vec::new();
    let mut path = vec![start];
    let mut visited = HashSet::new();
    visited.insert(start);

    fn dfs(
        node: i32,
        end: i32,
        graph: &HashMap<i32, Vec<i32>>,
        path: &mut Vec<i32>,
        visited: &mut HashSet<i32>,
        all_paths: &mut Vec<Vec<i32>>,
    ) {
        if node == end {
            all_paths.push(path.clone());
            return;
        }

        if let Some(neighbors) = graph.get(&node) {
            for &neighbor in neighbors {
                if !visited.contains(&neighbor) {
                    visited.insert(neighbor);
                    path.push(neighbor);
                    dfs(neighbor, end, graph, path, visited, all_paths);
                    path.pop();
                    visited.remove(&neighbor);
                }
            }
        }
    }

    dfs(start, end, graph, &mut path, &mut visited, &mut all_paths);
    all_paths
}

// ============================================================================
// PROBLEM 3: Dijkstra's Algorithm - Weighted Graph Shortest Path
// ============================================================================

#[derive(Copy, Clone, Eq, PartialEq)]
struct State {
    cost: i32,
    node: i32,
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
    graph: &HashMap<i32, Vec<(i32, i32)>>,
    start: i32,
    end: i32,
) -> (i32, Vec<i32>) {
    let mut heap = BinaryHeap::new();
    let mut visited = HashSet::new();
    let mut distances: HashMap<i32, i32> = HashMap::new();
    let mut predecessors: HashMap<i32, i32> = HashMap::new();

    heap.push(State { cost: 0, node: start });
    distances.insert(start, 0);

    while let Some(State { cost, node }) = heap.pop() {
        if node == end {
            let mut path = Vec::new();
            let mut current = end;
            while current != start {
                path.push(current);
                current = predecessors[&current];
            }
            path.push(start);
            path.reverse();
            return (cost, path);
        }

        if visited.contains(&node) {
            continue;
        }
        visited.insert(node);

        if let Some(neighbors) = graph.get(&node) {
            for &(neighbor, weight) in neighbors {
                if !visited.contains(&neighbor) {
                    let new_cost = cost + weight;
                    let is_better = distances
                        .get(&neighbor)
                        .map_or(true, |&current| new_cost < current);

                    if is_better {
                        distances.insert(neighbor, new_cost);
                        predecessors.insert(neighbor, node);
                        heap.push(State { cost: new_cost, node: neighbor });
                    }
                }
            }
        }
    }

    (i32::MAX, Vec::new())
}

// ============================================================================
// PROBLEM 4: A* Algorithm - Grid with Heuristic
// ============================================================================

#[derive(Copy, Clone, Eq, PartialEq)]
struct AStarState {
    priority: i32,
    cost: i32,
    pos: (usize, usize),
}

impl Ord for AStarState {
    fn cmp(&self, other: &Self) -> Ordering {
        other.priority.cmp(&self.priority)
    }
}

impl PartialOrd for AStarState {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

fn astar_grid(
    grid: &Vec<Vec<i32>>,
    start: (usize, usize),
    end: (usize, usize),
) -> Vec<(usize, usize)> {
    fn heuristic(pos: (usize, usize), end: (usize, usize)) -> i32 {
        ((pos.0 as i32 - end.0 as i32).abs() + (pos.1 as i32 - end.1 as i32).abs())
    }

    let rows = grid.len();
    let cols = grid[0].len();
    let mut heap = BinaryHeap::new();
    let mut visited = HashSet::new();
    let mut predecessors: HashMap<(usize, usize), (usize, usize)> = HashMap::new();
    let directions = [(0, 1), (1, 0), (0, -1), (-1, 0)];

    heap.push(AStarState {
        priority: heuristic(start, end),
        cost: 0,
        pos: start,
    });

    while let Some(AStarState { cost, pos, .. }) = heap.pop() {
        if pos == end {
            let mut path = Vec::new();
            let mut current = end;
            while current != start {
                path.push(current);
                current = predecessors[&current];
            }
            path.push(start);
            path.reverse();
            return path;
        }

        if visited.contains(&pos) {
            continue;
        }
        visited.insert(pos);

        for (dr, dc) in &directions {
            let nr = pos.0 as i32 + dr;
            let nc = pos.1 as i32 + dc;

            if nr >= 0 && nr < rows as i32 && nc >= 0 && nc < cols as i32 {
                let nr = nr as usize;
                let nc = nc as usize;
                let new_pos = (nr, nc);

                if !visited.contains(&new_pos) && grid[nr][nc] == 0 {
                    let new_cost = cost + 1;
                    let priority = new_cost + heuristic(new_pos, end);
                    predecessors.insert(new_pos, pos);
                    heap.push(AStarState {
                        priority,
                        cost: new_cost,
                        pos: new_pos,
                    });
                }
            }
        }
    }

    Vec::new()
}

// ============================================================================
// PROBLEM 5: Bellman-Ford - Negative Weight Handling
// ============================================================================

fn bellman_ford(
    edges: &Vec<(i32, i32, i32)>,
    n: usize,
    start: i32,
) -> Result<HashMap<i32, i32>, String> {
    let mut dist: HashMap<i32, i32> = HashMap::new();
    
    for i in 0..n as i32 {
        dist.insert(i, i32::MAX);
    }
    dist.insert(start, 0);

    // Relax edges n-1 times
    for _ in 0..n - 1 {
        for &(u, v, w) in edges {
            if dist[&u] != i32::MAX && dist[&u] + w < dist[&v] {
                dist.insert(v, dist[&u] + w);
            }
        }
    }

    // Check for negative cycles
    for &(u, v, w) in edges {
        if dist[&u] != i32::MAX && dist[&u] + w < dist[&v] {
            return Err("Graph contains negative weight cycle".to_string());
        }
    }

    Ok(dist)
}

// ============================================================================
// PRACTICE EXERCISES
// ============================================================================

fn main() {
    println!("{}", "=".repeat(60));
    println!("PROBLEM 1: BFS Grid Shortest Path");
    let grid1 = vec![
        vec![0, 0, 0],
        vec![1, 1, 0],
        vec![0, 0, 0],
    ];
    let result1 = bfs_grid_shortest_path(&grid1, (0, 0), (2, 2));
    println!("Shortest path length: {}", result1);

    println!("\n{}", "=".repeat(60));
    println!("PROBLEM 2: DFS All Paths");
    let mut graph2 = HashMap::new();
    graph2.insert(0, vec![1, 2]);
    graph2.insert(1, vec![2, 3]);
    graph2.insert(2, vec![3]);
    graph2.insert(3, vec![]);
    let result2 = dfs_all_paths(&graph2, 0, 3);
    println!("All paths: {:?}", result2);

    println!("\n{}", "=".repeat(60));
    println!("PROBLEM 3: Dijkstra's Algorithm");
    let mut graph3 = HashMap::new();
    graph3.insert(0, vec![(1, 4), (2, 1)]);
    graph3.insert(1, vec![(3, 1)]);
    graph3.insert(2, vec![(1, 2), (3, 5)]);
    graph3.insert(3, vec![]);
    let (dist3, path3) = dijkstra(&graph3, 0, 3);
    println!("Shortest distance: {}, Path: {:?}", dist3, path3);

    println!("\n{}", "=".repeat(60));
    println!("PROBLEM 4: A* Algorithm");
    let grid4 = vec![
        vec![0, 0, 0],
        vec![0, 1, 0],
        vec![0, 0, 0],
    ];
    let result4 = astar_grid(&grid4, (0, 0), (2, 2));
    println!("A* path: {:?}", result4);

    println!("\n{}", "=".repeat(60));
    println!("PROBLEM 5: Bellman-Ford Algorithm");
    let edges5 = vec![
        (0, 1, 4),
        (0, 2, 1),
        (2, 1, 2),
        (1, 3, 1),
        (2, 3, 5),
    ];
    match bellman_ford(&edges5, 4, 0) {
        Ok(result5) => println!("Shortest distances: {:?}", result5),
        Err(e) => println!("Error: {}", e),
    }
    println!("{}", "=".repeat(60));
}

# Path Finding Algorithms: Practice Problems & Exercises

I'll create a comprehensive set of practice problems with implementations in both Python and Rust to help you master pathfinding algorithms.## Practice Problems Overview

I've created comprehensive pathfinding practice problems with implementations in both Python and Rust. Here's what's included:

### **Problem 1: BFS - Shortest Path in Unweighted Grid**
- **Concept**: Breadth-First Search for finding shortest paths in grids
- **Use Case**: Navigation in games, maze solving
- **Key Learning**: Level-order traversal, queue-based exploration

### **Problem 2: DFS - Find All Paths**
- **Concept**: Depth-First Search with backtracking
- **Use Case**: Finding all possible routes between nodes
- **Key Learning**: Recursive exploration, path tracking, backtracking

### **Problem 3: Dijkstra's Algorithm**
- **Concept**: Shortest path in weighted graphs (non-negative weights)
- **Use Case**: Road networks, routing protocols
- **Key Learning**: Priority queue, greedy approach, path reconstruction

### **Problem 4: A* Algorithm**
- **Concept**: Heuristic-guided pathfinding
- **Use Case**: Game AI, GPS navigation
- **Key Learning**: Combining actual cost with heuristic estimates (Manhattan distance)

### **Problem 5: Bellman-Ford Algorithm**
- **Concept**: Shortest path with negative weights
- **Use Case**: Currency exchange, network routing with costs
- **Key Learning**: Edge relaxation, negative cycle detection

## Suggested Exercises

1. **Modify the grid problems** to support diagonal movement (8 directions)
2. **Implement bidirectional search** for BFS and A*
3. **Add weight variations** to grid cells (mud, water, etc.)
4. **Create a maze generator** and use these algorithms to solve it
5. **Benchmark the algorithms** on different graph sizes
6. **Implement Floyd-Warshall** for all-pairs shortest paths
7. **Add visualization** to see the search progression

Both implementations are ready to run and include test cases. Try modifying the examples or creating your own graphs to deepen your understanding!