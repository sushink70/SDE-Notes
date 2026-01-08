# Comprehensive Guide to BFS (Breadth-First Search)

## Table of Contents

1. Introduction to BFS
2. How BFS Works
3. BFS Algorithm & Pseudocode
4. Visual Walkthrough with ASCII Diagrams
5. Implementation in Multiple Languages
6. Time & Space Complexity
7. BFS Tree vs BFS Graph
8. Variations of BFS
9. Real-World Use Cases
10. BFS vs DFS Comparison
11. Common Problems & Solutions

---

## 1. Introduction to BFS

**Breadth-First Search (BFS)** is a graph/tree traversal algorithm that explores nodes level by level, visiting all neighbors at the current depth before moving to nodes at the next depth level.

### Key Characteristics:

- Uses a **Queue** data structure (FIFO - First In, First Out)
- Guarantees the **shortest path** in unweighted graphs
- Explores nodes in "waves" or "levels"
- Complete algorithm (finds solution if it exists)
- Optimal for finding shortest distance

---

## 2. How BFS Works

### Core Principle:

BFS explores a graph/tree by visiting all nodes at distance `k` from the source before visiting nodes at distance `k+1`.

### Step-by-Step Process:

1. Start at the root/source node
2. Mark it as visited and enqueue it
3. While queue is not empty:
   - Dequeue a node
   - Process/visit the node
   - Enqueue all unvisited neighbors
   - Mark neighbors as visited

---

## 3. BFS Algorithm & Pseudocode

```
BFS(graph, start_node):
    create a queue Q
    create a set visited
    
    Q.enqueue(start_node)
    visited.add(start_node)
    
    while Q is not empty:
        current = Q.dequeue()
        process(current)
        
        for each neighbor of current:
            if neighbor not in visited:
                visited.add(neighbor)
                Q.enqueue(neighbor)
```

---

## 4. Visual Walkthrough with ASCII Diagrams

### Example 1: BFS on a Tree

```
Initial Tree Structure:
           1
         / | \
        2  3  4
       /|  |  |\
      5 6  7  8 9
```

**BFS Traversal Order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9**

#### Step-by-Step Visualization:

```
Step 0: Start
Queue: [1]
Visited: {1}

          (1)         <- Current
         / | \
        2  3  4
       /|  |  |\
      5 6  7  8 9
```

```
Step 1: Process node 1, enqueue children
Queue: [2, 3, 4]
Visited: {1, 2, 3, 4}

           1
         / | \
       (2) 3  4        <- 2 is next
       /|  |  |\
      5 6  7  8 9
```

```
Step 2: Process node 2, enqueue children
Queue: [3, 4, 5, 6]
Visited: {1, 2, 3, 4, 5, 6}

           1
         / | \
        2 (3) 4        <- 3 is next
       /|  |  |\
      5 6  7  8 9
```

```
Step 3: Process node 3, enqueue children
Queue: [4, 5, 6, 7]
Visited: {1, 2, 3, 4, 5, 6, 7}

           1
         / | \
        2  3 (4)       <- 4 is next
       /|  |  |\
      5 6  7  8 9
```

```
Step 4: Process node 4, enqueue children
Queue: [5, 6, 7, 8, 9]
Visited: {1, 2, 3, 4, 5, 6, 7, 8, 9}

           1
         / | \
        2  3  4
       /|  |  |\
     (5)6  7  8 9      <- 5 is next
```

### Example 2: BFS on a Graph

```
Graph Structure:
    A --- B
    |     |
    C --- D --- E
          |
          F

Adjacency List:
A: [B, C]
B: [A, D]
C: [A, D]
D: [B, C, E, F]
E: [D]
F: [D]
```

**BFS from A: A → B → C → D → E → F**

#### Level-by-Level Breakdown:

```
Level 0: {A}
    (A)--- B
     |     |
     C --- D --- E
           |
           F

Level 1: {B, C}
     A ---(B)
     |     |
    (C)--- D --- E
           |
           F

Level 2: {D}
     A --- B
     |     |
     C ---(D)--- E
           |
           F

Level 3: {E, F}
     A --- B
     |     |
     C --- D ---(E)
           |
          (F)
```

### Example 3: BFS Finding Shortest Path

```
Problem: Find shortest path from S to G

     S --- A --- B
     |     |     |
     C --- D --- G
     |           |
     E --------- F

BFS Path Discovery:

Step 1: Start at S
Distance: {S: 0}
Queue: [S]

Step 2: Explore S's neighbors
Distance: {S: 0, A: 1, C: 1}
Queue: [A, C]
Parent: {A: S, C: S}

Step 3: Explore A's neighbors
Distance: {S: 0, A: 1, C: 1, B: 2, D: 2}
Queue: [C, B, D]
Parent: {A: S, C: S, B: A, D: A}

Step 4: Explore C's neighbors
Distance: {S: 0, A: 1, C: 1, B: 2, D: 2, E: 2}
Queue: [B, D, E]
Parent: {A: S, C: S, B: A, D: A, E: C}

Step 5: Explore B's neighbors
Distance: {S: 0, A: 1, C: 1, B: 2, D: 2, E: 2, G: 3}
Queue: [D, E, G]
Parent: {A: S, C: S, B: A, D: A, E: C, G: B}

Found G! Shortest distance = 3
Path: S → A → B → G
```

---

## 5. Implementation in Multiple Languages

### Python Implementation

```python
from collections import deque

class Graph:
    def __init__(self):
        self.graph = {}
    
    def add_edge(self, u, v):
        if u not in self.graph:
            self.graph[u] = []
        self.graph[u].append(v)
    
    def bfs(self, start):
        visited = set()
        queue = deque([start])
        visited.add(start)
        result = []
        
        while queue:
            node = queue.popleft()
            result.append(node)
            
            # Get neighbors (handle missing keys)
            for neighbor in self.graph.get(node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        return result
    
    def bfs_shortest_path(self, start, goal):
        visited = set()
        queue = deque([(start, [start])])
        visited.add(start)
        
        while queue:
            node, path = queue.popleft()
            
            if node == goal:
                return path
            
            for neighbor in self.graph.get(node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return None  # No path found

# Binary Tree BFS (Level Order Traversal)
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def bfs_tree(root):
    if not root:
        return []
    
    result = []
    queue = deque([root])
    
    while queue:
        node = queue.popleft()
        result.append(node.val)
        
        if node.left:
            queue.append(node.left)
        if node.right:
            queue.append(node.right)
    
    return result

# BFS with level tracking
def bfs_with_levels(root):
    if not root:
        return []
    
    result = []
    queue = deque([root])
    
    while queue:
        level_size = len(queue)
        current_level = []
        
        for _ in range(level_size):
            node = queue.popleft()
            current_level.append(node.val)
            
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        
        result.append(current_level)
    
    return result
```

### JavaScript Implementation

```javascript
class Graph {
    constructor() {
        this.adjacencyList = new Map();
    }
    
    addEdge(u, v) {
        if (!this.adjacencyList.has(u)) {
            this.adjacencyList.set(u, []);
        }
        this.adjacencyList.get(u).push(v);
    }
    
    bfs(start) {
        const visited = new Set();
        const queue = [start];
        const result = [];
        visited.add(start);
        
        while (queue.length > 0) {
            const node = queue.shift();
            result.push(node);
            
            const neighbors = this.adjacencyList.get(node) || [];
            for (const neighbor of neighbors) {
                if (!visited.has(neighbor)) {
                    visited.add(neighbor);
                    queue.push(neighbor);
                }
            }
        }
        
        return result;
    }
}

// Tree BFS
function bfsTree(root) {
    if (!root) return [];
    
    const result = [];
    const queue = [root];
    
    while (queue.length > 0) {
        const node = queue.shift();
        result.push(node.val);
        
        if (node.left) queue.push(node.left);
        if (node.right) queue.push(node.right);
    }
    
    return result;
}
```

### Java Implementation

```java
import java.util.*;

class Graph {
    private Map<Integer, List<Integer>> adjacencyList;
    
    public Graph() {
        adjacencyList = new HashMap<>();
    }
    
    public void addEdge(int u, int v) {
        adjacencyList.putIfAbsent(u, new ArrayList<>());
        adjacencyList.get(u).add(v);
    }
    
    public List<Integer> bfs(int start) {
        Set<Integer> visited = new HashSet<>();
        Queue<Integer> queue = new LinkedList<>();
        List<Integer> result = new ArrayList<>();
        
        visited.add(start);
        queue.offer(start);
        
        while (!queue.isEmpty()) {
            int node = queue.poll();
            result.add(node);
            
            List<Integer> neighbors = adjacencyList.getOrDefault(node, 
                                      new ArrayList<>());
            for (int neighbor : neighbors) {
                if (!visited.contains(neighbor)) {
                    visited.add(neighbor);
                    queue.offer(neighbor);
                }
            }
        }
        
        return result;
    }
}

// Tree BFS
class TreeNode {
    int val;
    TreeNode left, right;
    TreeNode(int val) { this.val = val; }
}

public List<Integer> bfsTree(TreeNode root) {
    List<Integer> result = new ArrayList<>();
    if (root == null) return result;
    
    Queue<TreeNode> queue = new LinkedList<>();
    queue.offer(root);
    
    while (!queue.isEmpty()) {
        TreeNode node = queue.poll();
        result.add(node.val);
        
        if (node.left != null) queue.offer(node.left);
        if (node.right != null) queue.offer(node.right);
    }
    
    return result;
}
```

---

## 6. Time & Space Complexity

### Time Complexity: **O(V + E)**

- **V** = number of vertices/nodes
- **E** = number of edges
- Each vertex is visited once: O(V)
- Each edge is explored once: O(E)

### Space Complexity: **O(V)**

- Queue can hold up to O(V) nodes in worst case
- Visited set stores O(V) nodes
- For a binary tree: O(w) where w is maximum width

### Complexity Breakdown by Structure:

```
Tree Structure:
            1
          /   \
         2     3
        / \   / \
       4   5 6   7

Time: O(n) - visit each node once
Space: O(w) - max width of tree = 4 nodes at level 3

Graph Structure (Complete Graph):
     1 --- 2
     |  X  |
     3 --- 4

Time: O(V + E) = O(4 + 6) = O(10)
Space: O(V) = O(4)
```

---

## 7. BFS Tree vs BFS Graph

### BFS Tree

A **BFS Tree** is the spanning tree created when running BFS on a graph, showing parent-child relationships based on discovery order.

```
Original Graph:          BFS Tree from node 1:
    1 --- 2 --- 5            1
    |     |     |           / \
    3 --- 4     6          2   3
                           |   |
                           5   4
                           |
                           6

Edge Classification:
- Tree edges: (1,2), (1,3), (2,5), (3,4), (5,6)
- Cross edges: (2,4), (2,3) [not in BFS tree]
```

### Properties of BFS Tree:

1. **No back edges** (unlike DFS)
2. Contains tree edges and cross edges only
3. Tree edges connect parent to child
4. Cross edges connect nodes at same or adjacent levels
5. Represents shortest path from root to all nodes

---

## 8. Variations of BFS

### 8.1 Multi-Source BFS

Start from multiple sources simultaneously (useful for finding nearest source).

```python
def multi_source_bfs(graph, sources):
    visited = set(sources)
    queue = deque(sources)
    distances = {s: 0 for s in sources}
    
    while queue:
        node = queue.popleft()
        
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                distances[neighbor] = distances[node] + 1
                queue.append(neighbor)
    
    return distances
```

**Example:**
```
Grid with multiple fire sources (F):
    . . F .
    . . . .
    F . . .
    . . . F

Multi-source BFS finds distance to nearest fire from each cell.
```

### 8.2 Bidirectional BFS

Search from both start and goal simultaneously to meet in the middle.

```python
def bidirectional_bfs(graph, start, goal):
    if start == goal:
        return [start]
    
    # Forward BFS from start
    visited_start = {start: None}
    queue_start = deque([start])
    
    # Backward BFS from goal
    visited_goal = {goal: None}
    queue_goal = deque([goal])
    
    while queue_start and queue_goal:
        # Expand from start
        current = queue_start.popleft()
        for neighbor in graph[current]:
            if neighbor in visited_goal:
                # Found intersection!
                return construct_path(visited_start, visited_goal, 
                                     current, neighbor)
            if neighbor not in visited_start:
                visited_start[neighbor] = current
                queue_start.append(neighbor)
        
        # Expand from goal
        current = queue_goal.popleft()
        for neighbor in graph[current]:
            if neighbor in visited_start:
                return construct_path(visited_start, visited_goal, 
                                     neighbor, current)
            if neighbor not in visited_goal:
                visited_goal[neighbor] = current
                queue_goal.append(neighbor)
    
    return None
```

### 8.3 0-1 BFS

For graphs where edges have weights 0 or 1 (uses deque instead of priority queue).

```python
def bfs_01(graph, start, end):
    distance = {start: 0}
    deque_bfs = deque([start])
    
    while deque_bfs:
        node = deque_bfs.popleft()
        
        for neighbor, weight in graph[node]:
            new_dist = distance[node] + weight
            
            if neighbor not in distance or new_dist < distance[neighbor]:
                distance[neighbor] = new_dist
                
                if weight == 0:
                    deque_bfs.appendleft(neighbor)  # Add to front
                else:
                    deque_bfs.append(neighbor)      # Add to back
    
    return distance.get(end, float('inf'))
```

### 8.4 Level-Order BFS with Level Tracking

```python
def bfs_by_level(root):
    if not root:
        return []
    
    result = []
    queue = deque([root])
    level = 0
    
    while queue:
        level_size = len(queue)
        current_level = []
        
        for _ in range(level_size):
            node = queue.popleft()
            current_level.append(node.val)
            
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        
        result.append(current_level)
        level += 1
    
    return result
```

---

## 9. Real-World Use Cases

### 9.1 Social Networks

**Problem:** Find degrees of separation between two people

```
Social Network Graph:
    Alice --- Bob --- Charlie
      |        |        |
    David -- Emma --- Frank

Question: How many connections between Alice and Frank?

BFS Solution:
Level 0: Alice
Level 1: Bob, David
Level 2: Charlie, Emma
Level 3: Frank ✓

Answer: 3 degrees of separation
Path: Alice → Bob → Emma → Frank
```

**Applications:**

- LinkedIn "People you may know"
- Facebook friend suggestions
- Six degrees of Kevin Bacon

### 9.2 GPS Navigation & Shortest Path

**Problem:** Find shortest route between two locations

```
Road Network:
    A --5-- B --3-- C
    |       |       |
    7       2       4
    |       |       |
    D --1-- E --6-- F

Using BFS (unweighted edges):
Find shortest path from A to F

BFS gives: A → B → E → F (3 hops)

For weighted graphs, use Dijkstra's (BFS variant)
```

**Applications:**

- Google Maps routing
- Waze traffic navigation
- Uber driver matching

### 9.3 Web Crawling

**Problem:** Crawl websites level by level

```
Web Structure:
    homepage.com
        |
    +---+---+
    |   |   |
   p1  p2  p3
    |       |
   +--+    +--+
   |  |    |  |
  p11 p12 p31 p32

BFS Crawl Order:
1. homepage.com
2. p1, p2, p3
3. p11, p12, p31, p32

Advantages:
- Finds all pages at depth d before depth d+1
- Respects crawl budget efficiently
- Discovers important pages first
```

**Applications:**

- Search engine indexing (Google, Bing)
- Web scraping frameworks
- Sitemap generation

### 9.4 Network Broadcasting

**Problem:** Broadcast message to all nodes in minimum time

```
Network Topology:
    Router A (source)
       / | \
      B  C  D
     /|  |  |\
    E F  G  H I

BFS Broadcast:
Time 0: A broadcasts
Time 1: B, C, D receive
Time 2: E, F, G, H, I receive

Total time: 2 units (minimum possible)
```

**Applications:**

- Network packet routing
- Distributed system updates
- Blockchain transaction propagation

### 9.5 Puzzle Solving

**Problem:** Solve sliding puzzle or maze

```
15-Puzzle State Space:
Initial:        Goal:
1 2 3 4        1 2 3 4
5 6 7 8        5 6 7 8
9 10 11 12     9 10 11 12
13 14 _ 15     13 14 15 _

BFS explores states level by level
Each level = one more move

Maze Example:
S . # . . .
. . # . # .
# . . . # .
. . # . . G

BFS finds shortest path: 10 steps
```

**Applications:**

- Rubik's Cube solvers
- Maze navigation
- Game AI (chess, checkers)

### 9.6 Dependency Resolution

**Problem:** Install software packages in correct order

```
Package Dependencies:
    App
    / \
   B   C
  /|   |\
 D E   F G

BFS Order (level-order installation):
Level 0: D, E, F, G (no dependencies)
Level 1: B, C (depend on level 0)
Level 2: App (depends on B, C)

Installation order ensures all dependencies met
```

**Applications:**

- Package managers (npm, pip, apt)
- Build systems (make, gradle)
- Task scheduling

### 9.7 Bipartite Graph Testing

**Problem:** Can you color graph with 2 colors?

```python
def is_bipartite_bfs(graph):
    color = {}
    
    for start in graph:
        if start in color:
            continue
            
        queue = deque([start])
        color[start] = 0
        
        while queue:
            node = queue.popleft()
            
            for neighbor in graph[node]:
                if neighbor not in color:
                    color[neighbor] = 1 - color[node]
                    queue.append(neighbor)
                elif color[neighbor] == color[node]:
                    return False  # Not bipartite
    
    return True
```

**Applications:**


- Job assignment problems
- Network flow algorithms
- Matching problems

### 9.8 Recommendation Systems

**Problem:** Recommend items based on user connections

```
User-Item Graph:
Users:   U1 --- U2 --- U3
          |      |      |
Items:   I1    I2     I3

BFS from U1:
Level 0: U1's items: I1
Level 1: U2's items: I2 (recommend to U1)
Level 2: U3's items: I3 (also recommend)

Collaborative filtering using BFS
```

**Applications:**

- Netflix recommendations
- Amazon "Customers also bought"
- Spotify playlist suggestions

---

## 10. BFS vs DFS Comparison

```
Visual Comparison:

Tree:       1
          /   \
         2     3
        / \   / \
       4   5 6   7

BFS Order: 1 → 2 → 3 → 4 → 5 → 6 → 7
           (level by level)

DFS Order: 1 → 2 → 4 → 5 → 3 → 6 → 7
           (depth first)
```

### Detailed Comparison Table

| Feature | BFS | DFS |
|---------|-----|-----|
| **Data Structure** | Queue (FIFO) | Stack/Recursion (LIFO) |
| **Exploration** | Level by level | Branch by branch |
| **Space Complexity** | O(w) - width | O(h) - height |
| **Time Complexity** | O(V + E) | O(V + E) |
| **Shortest Path** | ✓ Guaranteed | ✗ Not guaranteed |
| **Completeness** | ✓ Always finds | ✓ Always finds |
| **Optimal** | ✓ For unweighted | ✗ Not optimal |
| **Memory Usage** | Higher (wide trees) | Lower (deep trees) |

### When to Use BFS:

- Finding shortest path in unweighted graphs
- Level-order traversal needed
- Finding all nodes within k distance
- Web crawling (breadth first)
- Social network analysis

### When to Use DFS:

- Detecting cycles
- Topological sorting
- Finding strongly connected components
- Maze solving (one solution)
- Memory constrained (deep > wide)

### Example Comparison

```
Graph:      1
          / | \
         2  3  4
         |     |
         5     6

Path from 1 to 5:

BFS Exploration:
Step 1: Visit 1
Step 2: Visit 2, 3, 4
Step 3: Visit 5 ✓
Path found: 1 → 2 → 5 (shortest)
Nodes visited: 5

DFS Exploration:
Step 1: Visit 1
Step 2: Visit 2
Step 3: Visit 5 ✓
Path found: 1 → 2 → 5
Nodes visited: 3

BFS guarantees shortest path
DFS found quickly but no guarantee
```

---

## 11. Common Problems & Solutions

### Problem 1: Binary Tree Level Order Traversal

```python
def levelOrder(root):
    """
    Input:      3
              /   \
             9    20
                 /  \
                15   7
    
    Output: [[3], [9, 20], [15, 7]]
    """
    if not root:
        return []
    
    result = []
    queue = deque([root])
    
    while queue:
        level_size = len(queue)
        current_level = []
        
        for _ in range(level_size):
            node = queue.popleft()
            current_level.append(node.val)
            
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        
        result.append(current_level)
    
    return result
```

### Problem 2: Shortest Path in Binary Matrix

```python
def shortestPathBinaryMatrix(grid):
    """
    Input:  [[0,1],
             [1,0]]
    Output: 2
    
    Path: (0,0) → (1,1)
    """
    n = len(grid)
    if grid[0][0] == 1 or grid[n-1][n-1] == 1:
        return -1
    
    directions = [(-1,-1), (-1,0), (-1,1), 
                  (0,-1),          (0,1),
                  (1,-1),  (1,0),  (1,1)]
    
    queue = deque([(0, 0, 1)])  # row, col, distance
    grid[0][0] = 1  # Mark visited
    
    while queue:
        row, col, dist = queue.popleft()
        
        if row == n-1 and col == n-1:
            return dist
        
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            
            if (0 <= new_row < n and 0 <= new_col < n and 
                grid[new_row][new_col] == 0):
                
                grid[new_row][new_col] = 1
                queue.append((new_row, new_col, dist + 1))
    
    return -1
```

### Problem 3: Word Ladder

```python
def ladderLength(beginWord, endWord, wordList):
    """
    Input: beginWord = "hit", endWord = "cog"
           wordList = ["hot","dot","dog","lot","log","cog"]
    Output: 5
    Explanation: "hit" → "hot" → "dot" → "dog" → "cog"
    """
    if endWord not in wordList:
        return 0
    
    wordList = set(wordList)
    queue = deque([(beginWord, 1)])
    
    while queue:
        word, steps = queue.popleft()
        
        if word == endWord:
            return steps
        
        # Try changing each character
        for i in range(len(word)):
            for c in 'abcdefghijklmnopqrstuvwxyz':
                next_word = word[:i] + c + word[i+1:]
                
                if next_word in wordList:
                    wordList.remove(next_word)
                    queue.append((next_word, steps + 1))
    
    return 0
```

### Problem 4: Rotting Oranges

```python
def orangesRotting(grid):
    """
    Input: [[2,1,1],
            [1,1,0],
            [0,1,1]]
    Output: 4
    
    Minute 0: [[2,1,1],    Minute 1: [[2,2,1],
              [1,1,0],                [2,1,0],
              [0,1,1]]                [0,1,1]]
    """
    rows, cols = len(grid), len(grid[0])
    queue = deque()
    fresh = 0
    
    # Count fresh oranges and find rotten ones
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 2:
                queue.append((r, c, 0))
            elif grid[r][c] == 1:
                fresh += 1
    
    if fresh == 0:
        return 0
    
    directions = [(0,1), (1,0), (0,-1), (-1,0)]
    max_time = 0
    
    while queue:
        r, c, time = queue.popleft()
        max_time = max(max_time, time)
        
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            
            if (0 <= nr < rows and 0 <= nc < cols and 
                grid[nr][nc] == 1):
                
                grid[nr][nc] = 2
                fresh -= 1
                queue.append((nr, nc, time + 1))
    
    return max_time if fresh == 0 else -1
```

### Problem 5: Number of Islands

```python
def numIslands(grid):
    """
    Input: [["1","1","0","0","0"],
            ["1","1","0","0","0"],
            ["0","0","1","0","0"],
            ["0","0","0","1","1"]]
    Output: 3
    """
    if not grid:
        return 0
    
    def bfs(r, c):
        queue = deque([(r, c)])
        grid[r][c] = '0'
        
        while queue:
            row, col = queue.popleft()
            
            for dr, dc in [(0,1), (1,0), (0,-1), (-1,0)]:
                nr, nc = row + dr, col + dc
                
                if (0 <= nr < len(grid) and 0 <= nc < len(grid[0]) 
                    and grid[nr][nc] == '1'):
                    
                    grid[nr][nc] = '0'
                    queue.append((nr, nc))
    
    count = 0
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] == '1':
                bfs(r, c)
                count += 1
    
    return count
```

---

## Summary

### Key Takeaways:

1. **BFS explores level by level** using a queue (FIFO)
2. **Guarantees shortest path** in unweighted graphs
3. **Space complexity O(V)** - can be memory intensive for wide trees
4. **Perfect for:** shortest paths, level-order traversal, finding nearest nodes
5. **Real applications:** navigation, social networks, web crawling, broadcasting

### Quick Decision Guide:

```
Choose BFS when you need:
├── Shortest path in unweighted graph ✓
├── Level-order traversal ✓
├── Minimum steps/moves ✓
├── Find all nodes within k distance ✓
└── Guarantee completeness ✓

Choose DFS when you need:
├── Detect cycles
├── Topological sort
├── Memory constrained (deep graphs)
├── Path existence (any path)
└── Backtracking problems
```

### Practice Resources:

- LeetCode: BFS tagged problems
- HackerRank: Graph theory section
- CodeForces: Graph algorithms
- GeeksforGeeks: BFS tutorials

I'll create a comprehensive guide to Breadth-First Search (BFS) for you, covering all essential concepts with ASCII diagrams and real-world applications.I've created a comprehensive guide to BFS (Breadth-First Search) covering everything from fundamentals to advanced applications!

## What's Included:

**Core Concepts:**

- Complete algorithm explanation with pseudocode
- Step-by-step ASCII visualizations of BFS traversal on trees and graphs
- How BFS finds shortest paths with visual examples

**Implementations:**

- Full working code in Python, JavaScript, and Java
- Tree and graph implementations
- Variations like Multi-source BFS, Bidirectional BFS, and 0-1 BFS

**Real-World Applications:**

- 🌐 Social networks (degrees of separation)
- 🗺️ GPS navigation and routing
- 🕷️ Web crawling and search engines
- 📡 Network broadcasting
- 🧩 Puzzle solving (mazes, sliding puzzles)
- 📦 Package dependency resolution
- 🎬 Recommendation systems
- And more!

**Practice Problems:**

- Binary Tree Level Order Traversal
- Shortest Path in Binary Matrix
- Word Ladder
- Rotting Oranges
- Number of Islands

The guide includes detailed ASCII diagrams showing how BFS explores nodes level-by-level, making it easy to visualize the algorithm in action. Each section builds on the previous one, from basic concepts to complex real-world applications.

Feel free to ask if you'd like me to elaborate on any specific section or provide additional examples!