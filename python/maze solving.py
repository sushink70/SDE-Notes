from typing import List, Tuple, Set, Optional, Dict, Callable
from collections import deque
import heapq
import random
import time
from enum import Enum

class CellType(Enum):
    """Enum for different cell types in maze"""
    WALL = 0
    OPEN = 1
    START = 2
    END = 3
    PATH = 4
    VISITED = 5

class Direction(Enum):
    """Movement directions in maze"""
    UP = (-1, 0)
    DOWN = (1, 0)
    LEFT = (0, -1)
    RIGHT = (0, 1)

class MazeCell:
    """Individual cell in the maze with type checking"""
    
    def __init__(self, row: int, col: int, cell_type: CellType = CellType.WALL):
        self.row = row
        self.col = col
        self.cell_type = cell_type
        self.g_cost = float('inf')  # For A* algorithm
        self.h_cost = float('inf')  # For A* algorithm
        self.parent: Optional['MazeCell'] = None
    
    @property
    def f_cost(self) -> float:
        """Total cost for A* algorithm"""
        return self.g_cost + self.h_cost
    
    def __lt__(self, other: 'MazeCell') -> bool:
        """For priority queue comparison"""
        return self.f_cost < other.f_cost
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MazeCell):
            return False
        return self.row == other.row and self.col == other.col
    
    def __hash__(self) -> int:
        return hash((self.row, self.col))

class Maze:
    """Maze representation with pathfinding capabilities"""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid: List[List[MazeCell]] = []
        self.start_pos: Optional[Tuple[int, int]] = None
        self.end_pos: Optional[Tuple[int, int]] = None
        
        # Initialize maze with walls
        for row in range(height):
            maze_row = []
            for col in range(width):
                maze_row.append(MazeCell(row, col, CellType.WALL))
            self.grid.append(maze_row)
    
    def set_cell(self, row: int, col: int, cell_type: CellType) -> None:
        """Set cell type with bounds checking"""
        if self.is_valid_position(row, col):
            self.grid[row][col].cell_type = cell_type
            
            if cell_type == CellType.START:
                self.start_pos = (row, col)
            elif cell_type == CellType.END:
                self.end_pos = (row, col)
    
    def is_valid_position(self, row: int, col: int) -> bool:
        """Check if position is within maze bounds"""
        return 0 <= row < self.height and 0 <= col < self.width
    
    def is_traversable(self, row: int, col: int) -> bool:
        """Check if cell can be traversed"""
        if not self.is_valid_position(row, col):
            return False
        
        cell_type = self.grid[row][col].cell_type
        return cell_type in [CellType.OPEN, CellType.START, CellType.END]
    
    def get_neighbors(self, row: int, col: int) -> List[Tuple[int, int]]:
        """Get valid neighboring positions"""
        neighbors = []
        
        for direction in Direction:
            new_row = row + direction.value[0]
            new_col = col + direction.value[1]
            
            if self.is_traversable(new_row, new_col):
                neighbors.append((new_row, new_col))
        
        return neighbors
    
    def reset_path(self) -> None:
        """Reset maze to remove path and visited markers"""
        for row in range(self.height):
            for col in range(self.width):
                if self.grid[row][col].cell_type in [CellType.PATH, CellType.VISITED]:
                    self.grid[row][col].cell_type = CellType.OPEN
                
                # Reset A* algorithm properties
                self.grid[row][col].g_cost = float('inf')
                self.grid[row][col].h_cost = float('inf')
                self.grid[row][col].parent = None
    
    def display(self) -> None:
        """Display maze in console"""
        symbols = {
            CellType.WALL: '█',
            CellType.OPEN: ' ',
            CellType.START: 'S',
            CellType.END: 'E',
            CellType.PATH: '·',
            CellType.VISITED: '○'
        }
        
        print("+" + "-" * self.width + "+")
        for row in self.grid:
            print("|" + "".join(symbols[cell.cell_type] for cell in row) + "|")
        print("+" + "-" * self.width + "+")

class MazeSolver:
    """Collection of maze solving algorithms"""
    
    def __init__(self, maze: Maze):
        self.maze = maze
        self.solution_path: List[Tuple[int, int]] = []
        self.visited_cells: Set[Tuple[int, int]] = set()
        self.algorithm_stats = {
            'nodes_explored': 0,
            'path_length': 0,
            'execution_time': 0.0
        }
    
    def _reconstruct_path(self, end_pos: Tuple[int, int], 
                         parent_map: Dict[Tuple[int, int], Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Reconstruct path from parent mapping"""
        path = []
        current = end_pos
        
        while current is not None:
            path.append(current)
            current = parent_map.get(current)
        
        return path[::-1]  # Reverse to get start->end path
    
    def _mark_solution(self, path: List[Tuple[int, int]]) -> None:
        """Mark solution path on maze"""
        for i, (row, col) in enumerate(path):
            if i == 0:  # Start position
                self.maze.set_cell(row, col, CellType.START)
            elif i == len(path) - 1:  # End position
                self.maze.set_cell(row, col, CellType.END)
            else:  # Path
                self.maze.set_cell(row, col, CellType.PATH)
    
    def solve_dfs(self, visualize: bool = False) -> bool:
        """
        Solve maze using Depth-First Search
        Good for: Finding any path, memory efficient
        Bad for: Not optimal path, can be slow
        """
        start_time = time.time()
        
        if not self.maze.start_pos or not self.maze.end_pos:
            return False
        
        self.maze.reset_path()
        self.visited_cells.clear()
        self.algorithm_stats['nodes_explored'] = 0
        
        stack = [self.maze.start_pos]
        parent_map: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {
            self.maze.start_pos: None
        }
        
        while stack:
            current = stack.pop()
            
            if current in self.visited_cells:
                continue
            
            self.visited_cells.add(current)
            self.algorithm_stats['nodes_explored'] += 1
            
            # Mark as visited for visualization
            if visualize and current != self.maze.start_pos and current != self.maze.end_pos:
                self.maze.set_cell(current[0], current[1], CellType.VISITED)
            
            # Check if reached end
            if current == self.maze.end_pos:
                self.solution_path = self._reconstruct_path(current, parent_map)
                self._mark_solution(self.solution_path)
                self.algorithm_stats['path_length'] = len(self.solution_path)
                self.algorithm_stats['execution_time'] = time.time() - start_time
                return True
            
            # Add neighbors to stack
            for neighbor in self.maze.get_neighbors(current[0], current[1]):
                if neighbor not in self.visited_cells:
                    stack.append(neighbor)
                    parent_map[neighbor] = current
        
        self.algorithm_stats['execution_time'] = time.time() - start_time
        return False
    
    def solve_bfs(self, visualize: bool = False) -> bool:
        """
        Solve maze using Breadth-First Search
        Good for: Shortest path in unweighted maze
        Bad for: Memory intensive
        """
        start_time = time.time()
        
        if not self.maze.start_pos or not self.maze.end_pos:
            return False
        
        self.maze.reset_path()
        self.visited_cells.clear()
        self.algorithm_stats['nodes_explored'] = 0
        
        queue = deque([self.maze.start_pos])
        parent_map: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {
            self.maze.start_pos: None
        }
        
        while queue:
            current = queue.popleft()
            
            if current in self.visited_cells:
                continue
            
            self.visited_cells.add(current)
            self.algorithm_stats['nodes_explored'] += 1
            
            # Mark as visited for visualization
            if visualize and current != self.maze.start_pos and current != self.maze.end_pos:
                self.maze.set_cell(current[0], current[1], CellType.VISITED)
            
            # Check if reached end
            if current == self.maze.end_pos:
                self.solution_path = self._reconstruct_path(current, parent_map)
                self._mark_solution(self.solution_path)
                self.algorithm_stats['path_length'] = len(self.solution_path)
                self.algorithm_stats['execution_time'] = time.time() - start_time
                return True
            
            # Add neighbors to queue
            for neighbor in self.maze.get_neighbors(current[0], current[1]):
                if neighbor not in self.visited_cells and neighbor not in parent_map:
                    queue.append(neighbor)
                    parent_map[neighbor] = current
        
        self.algorithm_stats['execution_time'] = time.time() - start_time
        return False
    
    def solve_astar(self, visualize: bool = False) -> bool:
        """
        Solve maze using A* algorithm
        Good for: Optimal path, efficient
        Bad for: More complex implementation
        """
        start_time = time.time()
        
        if not self.maze.start_pos or not self.maze.end_pos:
            return False
        
        self.maze.reset_path()
        self.visited_cells.clear()
        self.algorithm_stats['nodes_explored'] = 0
        
        def heuristic(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
            """Manhattan distance heuristic"""
            return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
        
        # Priority queue: (f_cost, position)
        open_set = []
        heapq.heappush(open_set, (0, self.maze.start_pos))
        
        # Initialize start cell
        start_cell = self.maze.grid[self.maze.start_pos[0]][self.maze.start_pos[1]]
        start_cell.g_cost = 0
        start_cell.h_cost = heuristic(self.maze.start_pos, self.maze.end_pos)
        
        while open_set:
            _, current = heapq.heappop(open_set)
            
            if current in self.visited_cells:
                continue
            
            self.visited_cells.add(current)
            self.algorithm_stats['nodes_explored'] += 1
            
            # Mark as visited for visualization
            if visualize and current != self.maze.start_pos and current != self.maze.end_pos:
                self.maze.set_cell(current[0], current[1], CellType.VISITED)
            
            # Check if reached end
            if current == self.maze.end_pos:
                # Reconstruct path using parent pointers
                path = []
                current_cell = self.maze.grid[current[0]][current[1]]
                
                while current_cell is not None:
                    path.append((current_cell.row, current_cell.col))
                    current_cell = current_cell.parent
                
                self.solution_path = path[::-1]
                self._mark_solution(self.solution_path)
                self.algorithm_stats['path_length'] = len(self.solution_path)
                self.algorithm_stats['execution_time'] = time.time() - start_time
                return True
            
            current_cell = self.maze.grid[current[0]][current[1]]
            
            # Check all neighbors
            for neighbor in self.maze.get_neighbors(current[0], current[1]):
                if neighbor in self.visited_cells:
                    continue
                
                neighbor_cell = self.maze.grid[neighbor[0]][neighbor[1]]
                tentative_g_cost = current_cell.g_cost + 1
                
                if tentative_g_cost < neighbor_cell.g_cost:
                    neighbor_cell.parent = current_cell
                    neighbor_cell.g_cost = tentative_g_cost
                    neighbor_cell.h_cost = heuristic(neighbor, self.maze.end_pos)
                    
                    heapq.heappush(open_set, (neighbor_cell.f_cost, neighbor))
        
        self.algorithm_stats['execution_time'] = time.time() - start_time
        return False
    
    def solve_recursive_backtracking(self, visualize: bool = False) -> bool:
        """
        Solve maze using recursive backtracking
        Good for: Simple implementation, guarantees solution if exists
        Bad for: Stack overflow on large mazes, not optimal
        """
        start_time = time.time()
        
        if not self.maze.start_pos or not self.maze.end_pos:
            return False
        
        self.maze.reset_path()
        self.visited_cells.clear()
        self.algorithm_stats['nodes_explored'] = 0
        
        def backtrack(row: int, col: int, path: List[Tuple[int, int]]) -> bool:
            # Check bounds and if cell is traversable
            if not self.maze.is_traversable(row, col):
                return False
            
            # Check if already visited
            if (row, col) in self.visited_cells:
                return False
            
            # Mark as visited
            self.visited_cells.add((row, col))
            path.append((row, col))
            self.algorithm_stats['nodes_explored'] += 1
            
            # Mark as visited for visualization
            if visualize and (row, col) != self.maze.start_pos and (row, col) != self.maze.end_pos:
                self.maze.set_cell(row, col, CellType.VISITED)
            
            # Check if reached end
            if (row, col) == self.maze.end_pos:
                return True
            
            # Try all four directions
            for direction in Direction:
                new_row = row + direction.value[0]
                new_col = col + direction.value[1]
                
                if backtrack(new_row, new_col, path):
                    return True
            
            # Backtrack
            path.pop()
            if visualize and (row, col) != self.maze.start_pos and (row, col) != self.maze.end_pos:
                self.maze.set_cell(row, col, CellType.OPEN)
            
            return False
        
        path = []
        if backtrack(self.maze.start_pos[0], self.maze.start_pos[1], path):
            self.solution_path = path
            self._mark_solution(self.solution_path)
            self.algorithm_stats['path_length'] = len(self.solution_path)
            self.algorithm_stats['execution_time'] = time.time() - start_time
            return True
        
        self.algorithm_stats['execution_time'] = time.time() - start_time
        return False

class MazeGenerator:
    """Generate different types of mazes"""
    
    @staticmethod
    def generate_simple_maze() -> Maze:
        """Generate a simple test maze"""
        maze = Maze(15, 10)
        
        # Create simple maze pattern
        maze_pattern = [
            "███████████████",
            "█S    █     █E█",
            "█ ███ █ ███ █ █",
            "█   █   █   █ █",
            "███ █████ ███ █",
            "█   █     █   █",
            "█ █ █ █████ █ █",
            "█ █   █     █ █",
            "█ █████ █████ █",
            "█             █",
            "███████████████"
        ]
        
        for row, line in enumerate(maze_pattern):
            for col, char in enumerate(line):
                if char == ' ':
                    maze.set_cell(row, col, CellType.OPEN)
                elif char == 'S':
                    maze.set_cell(row, col, CellType.START)
                elif char == 'E':
                    maze.set_cell(row, col, CellType.END)
                else:
                    maze.set_cell(row, col, CellType.WALL)
        
        return maze
    
    @staticmethod
    def generate_random_maze(width: int, height: int, 
                           wall_probability: float = 0.3) -> Maze:
        """Generate random maze with specified wall probability"""
        maze = Maze(width, height)
        
        # Fill with open spaces
        for row in range(height):
            for col in range(width):
                if random.random() > wall_probability:
                    maze.set_cell(row, col, CellType.OPEN)
        
        # Set start and end positions
        maze.set_cell(1, 1, CellType.START)
        maze.set_cell(height - 2, width - 2, CellType.END)
        
        return maze

# Real-world applications and examples
class GameAI:
    """Example: Game AI using maze solving for pathfinding"""
    
    def __init__(self, maze: Maze):
        self.maze = maze
        self.solver = MazeSolver(maze)
        self.player_pos = maze.start_pos
        self.target_pos = maze.end_pos
    
    def find_path_to_target(self) -> List[Tuple[int, int]]:
        """AI finds path from current position to target"""
        # Update start position to current player position
        if self.player_pos:
            self.maze.start_pos = self.player_pos
        
        # Use A* for optimal pathfinding
        if self.solver.solve_astar():
            return self.solver.solution_path
        return []
    
    def get_next_move(self) -> Optional[Tuple[int, int]]:
        """Get next move for AI"""
        path = self.find_path_to_target()
        if len(path) > 1:
            return path[1]  # Next position after current
        return None

# Demonstration and testing
def demonstrate_maze_solving():
    """Demonstrate different maze solving algorithms"""
    
    print("=== Maze Solving Demonstration ===\n")
    
    # Generate test maze
    maze = MazeGenerator.generate_simple_maze()
    solver = MazeSolver(maze)
    
    print("Original Maze:")
    maze.display()
    
    algorithms = [
        ("DFS", solver.solve_dfs),
        ("BFS", solver.solve_bfs),
        ("A*", solver.solve_astar),
        ("Recursive Backtracking", solver.solve_recursive_backtracking)
    ]
    
    print("\n=== Algorithm Comparison ===")
    
    for name, algorithm in algorithms:
        print(f"\n{name} Algorithm:")
        
        if algorithm():
            print(f"✓ Solution found!")
            print(f"Path length: {solver.algorithm_stats['path_length']}")
            print(f"Nodes explored: {solver.algorithm_stats['nodes_explored']}")
            print(f"Execution time: {solver.algorithm_stats['execution_time']:.4f}s")
            
            # Show maze with solution
            maze.display()
        else:
            print("✗ No solution found")
    
    print("\n=== Game AI Example ===")
    
    # Reset maze and demonstrate game AI
    maze = MazeGenerator.generate_simple_maze()
    game_ai = GameAI(maze)
    
    print("AI pathfinding from start to end:")
    path = game_ai.find_path_to_target()
    if path:
        print(f"AI found path with {len(path)} steps")
        print(f"Path: {path[:5]}..." if len(path) > 5 else f"Path: {path}")
        
        # Show next move
        next_move = game_ai.get_next_move()
        if next_move:
            print(f"Next move: {next_move}")

if __name__ == "__main__":
    demonstrate_maze_solving()

Maze solving is a pathfinding problem where you need to find a route from a starting point to a destination through a maze structure. It's a classic application of graph traversal algorithms like DFS, BFS, and more advanced pathfinding algorithms.

## How Maze Solving Works

A maze can be represented as a graph where:
- **Nodes**: Open spaces (cells you can move to)
- **Edges**: Connections between adjacent open spaces
- **Walls**: Blocked cells that prevent movement
- **Goal**: Find path from start to end position

## Python Implementation

Here's a comprehensive maze solving implementation using multiple algorithms:## Real-World Applications

### 1. **Video Game AI**
- **Usage**: NPC pathfinding, enemy AI, player guidance
- **Example**: NPCs in RPGs finding paths around obstacles
- **Security**: Validate movement boundaries to prevent cheating

### 2. **Robotics Navigation**
- **Usage**: Autonomous vehicles, warehouse robots, drones
- **Example**: Robot vacuum navigating around furniture
- **Security**: Implement safety bounds to prevent dangerous movements

### 3. **Route Planning**
- **Usage**: GPS navigation, delivery optimization, logistics
- **Example**: Google Maps finding alternative routes
- **Security**: Validate coordinates to prevent malicious routing

### 4. **Circuit Board Design**
- **Usage**: PCB routing, wire placement, component layout
- **Example**: Electronic design automation (EDA) tools
- **Security**: Prevent routing conflicts and electrical hazards

### 5. **Network Routing**
- **Usage**: Data packet routing, network topology, load balancing
- **Example**: Internet routers finding optimal data paths
- **Security**: Prevent routing loops and DDoS attacks

## Algorithm Comparison

### **Depth-First Search (DFS)**
- **Pros**: Memory efficient, simple implementation
- **Cons**: Not optimal, can get stuck in long paths
- **Use Case**: When any solution is acceptable

### **Breadth-First Search (BFS)**
- **Pros**: Finds shortest path, explores systematically
- **Cons**: Memory intensive, slower for long paths
- **Use Case**: When shortest path is required

### **A* Algorithm**
- **Pros**: Optimal and efficient, uses heuristics
- **Cons**: More complex, requires good heuristic
- **Use Case**: When you need optimal path quickly

### **Recursive Backtracking**
- **Pros**: Guarantees solution if exists, simple logic
- **Cons**: Stack overflow risk, not optimal
- **Use Case**: Small mazes, educational purposes

## Performance Characteristics

| Algorithm | Time Complexity | Space Complexity | Optimal | Complete |
|-----------|-----------------|------------------|---------|----------|
| DFS | O(b^m) | O(bm) | No | Yes* |
| BFS | O(b^d) | O(b^d) | Yes | Yes |
| A* | O(b^d) | O(b^d) | Yes** | Yes |
| Backtracking | O(4^n) | O(n) | No | Yes |

*Complete if graph is finite  
**Optimal if heuristic is admissible

## Security Considerations

1. **Input Validation**: Always validate maze dimensions and cell values
2. **Boundary Checking**: Prevent out-of-bounds access
3. **Stack Overflow Protection**: Use iterative versions for large mazes
4. **Resource Limits**: Set timeouts for pathfinding operations
5. **Memory Management**: Monitor memory usage in BFS and A*

## Integration with Your Tech Stack

### **Frontend (Next.js)**
```typescript
// React component for maze visualization
const MazeVisualizer: React.FC = () => {
  const [maze, setMaze] = useState<number[][]>([]);
  const [solution, setSolution] = useState<[number, number][]>([]);
  
  // WebSocket connection for real-time pathfinding
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/maze/');
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setSolution(data.path);
    };
  }, []);
};
```

### **Backend (Django)**
```python
# Django REST API endpoint
class MazeSolverView(APIView):
    def post(self, request):
        maze_data = request.data.get('maze')
        algorithm = request.data.get('algorithm', 'astar')
        
        # Validate input
        if not self.validate_maze(maze_data):
            return Response({'error': 'Invalid maze data'}, 
                          status=400)
        
        # Solve maze
        solver = MazeSolver(maze_data)
        solution = solver.solve(algorithm)
        
        return Response({
            'solution': solution,
            'stats': solver.get_stats()
        })
```

The implementation above provides a production-ready maze solving system with comprehensive algorithms, proper type hints, security considerations, and real-world applications that align with your development preferences and security requirements.