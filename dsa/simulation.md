# Comprehensive Guide: Simulation in Data Structures and Algorithms

## Table of Contents
1. [What is Simulation?](#what-is-simulation)
2. [When to Use Simulation](#when-to-use-simulation)
3. [Core Concepts](#core-concepts)
4. [Implementation Patterns](#implementation-patterns)
5. [Complete Implementations](#complete-implementations)
6. [Common Mistakes & Warnings](#common-mistakes--warnings)
7. [Performance Analysis](#performance-analysis)
8. [Security Considerations](#security-considerations)

---

## What is Simulation?

**Simulation** in DSA is a technique where you **directly model** a process by executing each step of the problem statement, rather than finding a mathematical formula or optimized pattern.

### Real-World Example
Think of a **robot warehouse system** (like Amazon's fulfillment centers):
- Instead of calculating the optimal path mathematically, you simulate the robot moving step-by-step
- Track its position, battery level, package pickup/delivery
- Handle collisions, queue management, priority changes

### How It Works Internally
```
Problem Statement → Break into discrete steps → Execute each step → Track state changes → Produce result
```

**Architecture:**
```
State Container (current system state)
    ↓
Step Executor (applies rules/transformations)
    ↓
State Validator (checks constraints)
    ↓
Result Accumulator (collects outputs)
```

---

## When to Use Simulation

### ✅ Use Simulation When:
1. **Problem explicitly describes a process** (robot movement, game simulation, time-based events)
2. **Step-by-step execution is clearer** than mathematical formula
3. **State transitions are complex** with many edge cases
4. **Problem size is manageable** (simulation can be O(n) or O(n²) depending on steps)

### ❌ Avoid Simulation When:
1. Mathematical formula exists (e.g., sum of 1 to n = n*(n+1)/2)
2. Problem requires O(n³) or worse complexity
3. Can use dynamic programming or greedy approach more efficiently

### Real-World Usage:
- **Gaming engines**: Character movement, collision detection
- **Traffic management systems**: Car flow simulation
- **Network packet routing**: Simulating packet travel through nodes
- **Financial systems**: Stock price changes over time
- **Queue management**: Customer service simulation

---

## Core Concepts

### 1. State Management
Track all relevant variables that change during simulation.

### 2. Time Steps
Break continuous time into discrete intervals (tick-based or event-based).

### 3. Rules/Constraints
Define how state transitions happen (movement rules, collision rules, etc.).

### 4. Boundary Conditions
Handle edge cases (out of bounds, empty states, overflow).

---

## Implementation Patterns

### Pattern 1: Grid-Based Simulation
**Used in**: Robot navigation, game boards, image processing

### Pattern 2: Queue-Based Simulation
**Used in**: Task scheduling, server request handling, BFS traversal

### Pattern 3: Event-Driven Simulation
**Used in**: Discrete event systems, time-series data processing

### Pattern 4: Agent-Based Simulation
**Used in**: Multi-entity systems, crowd simulation, particle systems

---

## Complete Implementations

### Problem 1: Robot Walking in Grid (Basic Simulation)

**Problem**: Robot starts at (0,0). Given commands "UDLR" (Up, Down, Left, Right), simulate movement and return final position. Grid is infinite.

**Real-World**: Warehouse robot navigation, drone flight path

#### Python Implementation (With Type Checking)

```python
from typing import Tuple, List
from enum import Enum

class Direction(Enum):
    """Enum for direction commands - provides type safety"""
    UP = 'U'
    DOWN = 'D'
    LEFT = 'L'
    RIGHT = 'R'

def simulate_robot_walk(commands: str) -> Tuple[int, int]:
    """
    Simulates robot walking on infinite grid.
    
    Time Complexity: O(n) where n = len(commands)
    Space Complexity: O(1) - only storing position
    
    Args:
        commands: String of direction commands (UDLR)
    
    Returns:
        Tuple of (x, y) final position
        
    Security: Input validation prevents injection attacks
    """
    # Input validation - CRITICAL for security
    if not isinstance(commands, str):
        raise TypeError(f"Expected str, got {type(commands).__name__}")
    
    # Validate only allowed characters
    valid_chars = set('UDLR')
    if not all(c in valid_chars for c in commands):
        raise ValueError("Invalid command characters. Only U, D, L, R allowed")
    
    # State initialization
    x: int = 0
    y: int = 0
    
    # Direction mapping - using dict for O(1) lookup
    # This is more readable than if-elif chains
    moves = {
        'U': (0, 1),   # Move up: y increases
        'D': (0, -1),  # Move down: y decreases
        'L': (-1, 0),  # Move left: x decreases
        'R': (1, 0)    # Move right: x increases
    }
    
    # Simulation loop - execute each step
    for command in commands:
        dx, dy = moves[command]  # Get direction vector
        x += dx  # Apply transformation
        y += dy
        
        # Optional: Log for debugging
        # print(f"Command: {command}, Position: ({x}, {y})")
    
    return (x, y)

# Test cases
if __name__ == "__main__":
    # Test 1: Basic movement
    assert simulate_robot_walk("UURR") == (2, 2)
    
    # Test 2: Return to origin
    assert simulate_robot_walk("UDLR") == (0, 0)
    
    # Test 3: Complex path
    assert simulate_robot_walk("UUURRRDDDLLL") == (-1, 0)
    
    print("✅ All tests passed!")
```

#### Rust Implementation

```rust
use std::collections::HashMap;

/// Represents a 2D position on the grid
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct Position {
    x: i32,
    y: i32,
}

/// Custom error type for simulation errors
/// This provides type-safe error handling
#[derive(Debug)]
enum SimulationError {
    InvalidCommand(char),
    EmptyInput,
}

impl std::fmt::Display for SimulationError {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        match self {
            SimulationError::InvalidCommand(c) => {
                write!(f, "Invalid command character: '{}'", c)
            }
            SimulationError::EmptyInput => write!(f, "Empty command string"),
        }
    }
}

impl std::error::Error for SimulationError {}

/// Simulates robot walking on infinite grid
/// 
/// # Arguments
/// * `commands` - String slice containing direction commands (U/D/L/R)
/// 
/// # Returns
/// * `Result<Position, SimulationError>` - Final position or error
/// 
/// # Time Complexity: O(n) where n = len(commands)
/// # Space Complexity: O(1)
/// 
/// # Security: Validates input to prevent undefined behavior
fn simulate_robot_walk(commands: &str) -> Result<Position, SimulationError> {
    // Input validation - Rust's type system helps but we still validate
    if commands.is_empty() {
        return Err(SimulationError::EmptyInput);
    }
    
    // State initialization - explicit types for clarity
    let mut position = Position { x: 0, y: 0 };
    
    // Direction mapping using HashMap for O(1) lookup
    // In Rust, we use tuples for direction vectors
    let moves: HashMap<char, (i32, i32)> = [
        ('U', (0, 1)),   // Up
        ('D', (0, -1)),  // Down
        ('L', (-1, 0)),  // Left
        ('R', (1, 0)),   // Right
    ]
    .iter()
    .cloned()
    .collect();
    
    // Simulation loop with error handling
    for command in commands.chars() {
        // Lookup direction vector
        match moves.get(&command) {
            Some(&(dx, dy)) => {
                // Apply transformation with overflow checking
                // In production, use checked_add for security
                position.x = position.x.checked_add(dx)
                    .expect("Position overflow on x-axis");
                position.y = position.y.checked_add(dy)
                    .expect("Position overflow on y-axis");
            }
            None => return Err(SimulationError::InvalidCommand(command)),
        }
    }
    
    Ok(position)
}

fn main() {
    // Test cases with pattern matching for error handling
    let test_cases = vec![
        ("UURR", Position { x: 2, y: 2 }),
        ("UDLR", Position { x: 0, y: 0 }),
        ("UUURRRDDDLLL", Position { x: -1, y: 0 }),
    ];
    
    for (commands, expected) in test_cases {
        match simulate_robot_walk(commands) {
            Ok(pos) => {
                assert_eq!(pos, expected, "Test failed for: {}", commands);
                println!("✅ Test passed: {} -> ({}, {})", commands, pos.x, pos.y);
            }
            Err(e) => panic!("Test failed: {}", e),
        }
    }
    
    // Test error cases
    match simulate_robot_walk("UUXR") {
        Err(SimulationError::InvalidCommand('X')) => {
            println!("✅ Error handling works correctly");
        }
        _ => panic!("Should have returned InvalidCommand error"),
    }
}
```

---

### Problem 2: Snake Game Simulation (Advanced)

**Problem**: Simulate a snake game. Snake moves in grid, eats food, grows, and game ends if it hits itself or wall.

**Real-World**: Game development, autonomous vehicle path planning, resource collection systems

#### Python Implementation

```python
from typing import List, Tuple, Deque, Optional
from collections import deque
from enum import Enum

class Direction(Enum):
    """Direction enum for type safety"""
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

class SnakeGame:
    """
    Snake game simulation with state management.
    
    Architecture:
    - State: snake body (deque), food position, score, game status
    - Rules: movement, collision detection, growth logic
    - Boundary: grid walls, self-collision
    
    Time Complexity per move: O(1) amortized
    Space Complexity: O(snake_length)
    """
    
    def __init__(
        self, 
        width: int, 
        height: int, 
        food: List[List[int]]
    ) -> None:
        """
        Initialize snake game.
        
        Args:
            width: Grid width
            height: Grid height
            food: List of [row, col] food positions
            
        Security: Validates grid dimensions to prevent memory issues
        """
        # Input validation - CRITICAL
        if width <= 0 or height <= 0:
            raise ValueError("Grid dimensions must be positive")
        if not isinstance(food, list):
            raise TypeError("Food must be a list")
            
        self.width: int = width
        self.height: int = height
        self.food: Deque[Tuple[int, int]] = deque(
            (r, c) for r, c in food
        )
        
        # Snake starts at top-left, moving right
        # Using deque for O(1) append/popleft operations
        self.snake: Deque[Tuple[int, int]] = deque([(0, 0)])
        
        # Initial state
        self.score: int = 0
        self.game_over: bool = False
        
    def move(self, direction: str) -> int:
        """
        Simulate one move of the snake.
        
        Args:
            direction: 'U', 'D', 'L', or 'R'
            
        Returns:
            Current score, or -1 if game over
            
        Process:
        1. Calculate new head position
        2. Check wall collision
        3. Check self collision
        4. Check food consumption
        5. Update snake body
        """
        if self.game_over:
            return -1
            
        # Map direction to movement vector
        direction_map = {
            'U': Direction.UP.value,
            'D': Direction.DOWN.value,
            'L': Direction.LEFT.value,
            'R': Direction.RIGHT.value
        }
        
        if direction not in direction_map:
            raise ValueError(f"Invalid direction: {direction}")
        
        # Get current head position
        head_row, head_col = self.snake[0]
        
        # Calculate new head position
        dr, dc = direction_map[direction]
        new_head = (head_row + dr, head_col + dc)
        new_row, new_col = new_head
        
        # Collision detection with walls
        if (new_row < 0 or new_row >= self.height or 
            new_col < 0 or new_col >= self.width):
            self.game_over = True
            return -1
        
        # Check if snake eats food
        ate_food = False
        if self.food and new_head == self.food[0]:
            self.food.popleft()  # Remove eaten food
            self.score += 1
            ate_food = True
        
        # Add new head
        self.snake.appendleft(new_head)
        
        # If didn't eat food, remove tail (movement simulation)
        # If ate food, keep tail (growth simulation)
        if not ate_food:
            self.snake.pop()
        
        # Self-collision detection (check if head hits body)
        # We check len > 1 because head is already in snake
        if len(self.snake) > 1 and new_head in list(self.snake)[1:]:
            self.game_over = True
            return -1
        
        return self.score
    
    def get_snake_body(self) -> List[Tuple[int, int]]:
        """Returns current snake body positions"""
        return list(self.snake)
    
    def get_remaining_food(self) -> List[Tuple[int, int]]:
        """Returns remaining food positions"""
        return list(self.food)

# Test simulation
if __name__ == "__main__":
    # Create game: 3x2 grid, food at positions
    game = SnakeGame(
        width=3, 
        height=2, 
        food=[[1, 2], [0, 1]]
    )
    
    # Simulate moves
    moves = ['R', 'D', 'R', 'U', 'L', 'U']
    expected_scores = [0, 0, 1, 1, 2, -1]  # Last move hits wall
    
    print("🐍 Snake Game Simulation")
    print(f"Grid: {game.width}x{game.height}")
    print(f"Starting position: {game.snake[0]}")
    print(f"Food locations: {list(game.food)}\n")
    
    for i, direction in enumerate(moves):
        score = game.move(direction)
        print(f"Move {i+1}: {direction} -> Score: {score}")
        
        if score == -1:
            print("❌ Game Over!")
            break
        else:
            print(f"   Snake body: {game.get_snake_body()}")
    
    print("\n✅ Simulation complete!")
```

#### Rust Implementation

```rust
use std::collections::{VecDeque, HashSet};

/// Direction enum with associated movement vectors
#[derive(Debug, Clone, Copy)]
enum Direction {
    Up,
    Down,
    Left,
    Right,
}

impl Direction {
    /// Returns movement vector (row_delta, col_delta)
    fn to_vector(&self) -> (i32, i32) {
        match self {
            Direction::Up => (0, -1),
            Direction::Down => (0, 1),
            Direction::Left => (-1, 0),
            Direction::Right => (1, 0),
        }
    }
    
    /// Parse direction from string
    fn from_str(s: &str) -> Option<Direction> {
        match s {
            "U" => Some(Direction::Up),
            "D" => Some(Direction::Down),
            "L" => Some(Direction::Left),
            "R" => Some(Direction::Right),
            _ => None,
        }
    }
}

/// Position type for better type safety
type Position = (i32, i32);

/// Snake game simulator with ownership-based state management
pub struct SnakeGame {
    width: i32,
    height: i32,
    /// Using VecDeque for O(1) push/pop at both ends
    snake: VecDeque<Position>,
    /// Food queue for ordered consumption
    food: VecDeque<Position>,
    score: i32,
    game_over: bool,
}

impl SnakeGame {
    /// Creates new snake game
    /// 
    /// # Arguments
    /// * `width` - Grid width
    /// * `height` - Grid height
    /// * `food` - Vector of food positions as [row, col]
    /// 
    /// # Panics
    /// Panics if width or height <= 0 (security validation)
    pub fn new(width: i32, height: i32, food: Vec<Vec<i32>>) -> Self {
        // Input validation - prevents invalid state
        assert!(width > 0 && height > 0, "Grid dimensions must be positive");
        
        // Convert food positions to tuple format
        let food_queue: VecDeque<Position> = food
            .into_iter()
            .map(|pos| {
                assert_eq!(pos.len(), 2, "Food position must have 2 coordinates");
                (pos[0], pos[1])
            })
            .collect();
        
        // Initialize snake at origin
        let mut snake = VecDeque::new();
        snake.push_back((0, 0));
        
        Self {
            width,
            height,
            snake,
            food: food_queue,
            score: 0,
            game_over: false,
        }
    }
    
    /// Simulates one move
    /// 
    /// # Returns
    /// * `Ok(score)` - Current score after move
    /// * `Err(-1)` - Game over
    /// 
    /// # Process
    /// 1. Validate game state
    /// 2. Calculate new head position
    /// 3. Check collisions (walls, self)
    /// 4. Handle food consumption
    /// 5. Update snake body
    pub fn move_snake(&mut self, direction: &str) -> Result<i32, i32> {
        if self.game_over {
            return Err(-1);
        }
        
        // Parse direction
        let dir = Direction::from_str(direction)
            .ok_or_else(|| {
                eprintln!("Invalid direction: {}", direction);
                -1
            })?;
        
        // Get current head (safe unwrap as snake always has at least 1 segment)
        let (head_row, head_col) = self.snake.front().unwrap();
        
        // Calculate new head position
        let (dr, dc) = dir.to_vector();
        let new_row = head_row + dr;
        let new_col = head_col + dc;
        let new_head = (new_row, new_col);
        
        // Wall collision detection
        if new_row < 0 || new_row >= self.height || 
           new_col < 0 || new_col >= self.width {
            self.game_over = true;
            return Err(-1);
        }
        
        // Check food consumption
        let ate_food = if let Some(&food_pos) = self.food.front() {
            if new_head == food_pos {
                self.food.pop_front();
                self.score += 1;
                true
            } else {
                false
            }
        } else {
            false
        };
        
        // Add new head to snake
        self.snake.push_front(new_head);
        
        // Remove tail if didn't eat food (simulate movement)
        if !ate_food {
            self.snake.pop_back();
        }
        
        // Self-collision detection using HashSet for O(n) check
        // We skip the first element (head) when checking
        let body_set: HashSet<_> = self.snake.iter().skip(1).collect();
        if body_set.contains(&new_head) {
            self.game_over = true;
            return Err(-1);
        }
        
        Ok(self.score)
    }
    
    /// Returns current snake body positions
    pub fn get_snake_body(&self) -> Vec<Position> {
        self.snake.iter().copied().collect()
    }
}

fn main() {
    // Test simulation
    let mut game = SnakeGame::new(
        3,
        2,
        vec![vec![1, 2], vec![0, 1]],
    );
    
    println!("🐍 Snake Game Simulation");
    println!("Grid: 3x2");
    println!("Starting position: {:?}\n", game.snake.front().unwrap());
    
    let moves = vec!["R", "D", "R", "U", "L", "U"];
    
    for (i, &direction) in moves.iter().enumerate() {
        match game.move_snake(direction) {
            Ok(score) => {
                println!("Move {}: {} -> Score: {}", i + 1, direction, score);
                println!("   Snake body: {:?}", game.get_snake_body());
            }
            Err(_) => {
                println!("Move {}: {} -> ❌ Game Over!", i + 1, direction);
                break;
            }
        }
    }
    
    println!("\n✅ Simulation complete!");
}
```

---

## Common Mistakes & Warnings

### ❌ Mistake 1: Not Validating Input

**Incorrect (Python):**
```python
def simulate(commands: str):
    x, y = 0, 0
    for cmd in commands:  # No validation!
        if cmd == 'U': y += 1
        # ... crashes if invalid command
```

**Security Risk**: Could cause KeyError, undefined behavior, or injection attacks.

**Correct:**
```python
def simulate(commands: str):
    valid_commands = set('UDLR')
    if not all(c in valid_commands for c in commands):
        raise ValueError("Invalid commands")
    # ... proceed safely
```

### ❌ Mistake 2: Modifying State While Iterating

**Incorrect (Python):**
```python
# Simulating queue processing
for item in queue:
    if condition:
        queue.remove(item)  # Modifying during iteration!
```

**Warning**: This causes undefined behavior and skipped elements.

**Correct:**
```python
# Use list comprehension or iterate over copy
queue = [item for item in queue if not condition]
# OR
for item in list(queue):  # Iterate over copy
    if condition:
        queue.remove(item)
```

### ❌ Mistake 3: Not Handling Boundaries

**Incorrect (Rust):**
```rust
let new_x = current_x + dx;  // Could overflow!
grid[new_x][new_y] = value;  // Out of bounds panic!
```

**Correct:**
```rust
let new_x = current_x.checked_add(dx)
    .ok_or("Position overflow")?;
    
if new_x < 0 || new_x >= grid_width {
    return Err("Out of bounds");
}
```

### ❌ Mistake 4: Using Wrong Data Structure

**Incorrect (Python):**
```python
# Using list for queue simulation - O(n) removal!
queue = [1, 2, 3, 4, 5]
first = queue.pop(0)  # O(n) operation!
```

**Performance Issue**: O(n) for each dequeue operation.

**Correct:**
```python
from collections import deque
queue = deque([1, 2, 3, 4, 5])
first = queue.popleft()  # O(1) operation!
```

---

## Performance Analysis

### Time Complexity Comparison

| Operation | Without Simulation | With Simulation |
|-----------|-------------------|-----------------|
| Robot Walk | O(1) formula | O(n) simulation |
| Sum 1 to n | O(1) formula | O(n) simulation |
| Game State | N/A | O(steps × operations) |
| Pathfinding | O(V + E) graph | O(grid_size × moves) |

### When Simulation is Optimal

1. **State-dependent problems**: Each step depends on previous state
2. **No closed-form solution**: Can't reduce to formula
3. **Complex rules**: Multiple conditions and edge cases

---

## Security Considerations

### 1. Input Validation
```python
# ALWAYS validate input bounds to prevent:
# - Buffer overflows
# - Memory exhaustion
# - Integer overflows
# - Injection attacks

def secure_simulate(commands: str, max_length: int = 10000):
    if len(commands) > max_length:
        raise ValueError("Command length exceeds limit")
    # ... validate characters, format, etc.
```

### 2. Resource Limits
```rust
// Prevent infinite loops or excessive memory
const MAX_ITERATIONS: usize = 1_000_000;
const MAX_GRID_SIZE: usize = 10_000;

if width > MAX_GRID_SIZE || height > MAX_GRID_SIZE {
    return Err("Grid size exceeds safety limit");
}
```

### 3. State Overflow Protection
```python
# Use bounds checking for position values
MAX_COORD = 10**9

if abs(x) > MAX_COORD or abs(y) > MAX_COORD:
    raise OverflowError("Position exceeded safe bounds")
```

---

## Control & Benefits: Simulation vs Direct Formula

### Python Control Comparison

#### Without Simulation (Formula-Based)
```python
# Problem: Sum of first n numbers
def sum_n(n: int) -> int:
    return n * (n + 1) // 2  # O(1), but limited to this pattern

# Benefits:
# ✅ Fast: O(1)
# ✅ Memory efficient: O(1)
# ❌ Limited: Only works for mathematical patterns
# ❌ No intermediate states
# ❌ Can't handle complex rules
```

#### With Simulation
```python
def sum_n_simulation(n: int) -> int:
    total = 0
    for i in range(1, n + 1):
        total += i  # O(n)
        # Can add logging, conditions, state tracking
    return total

# Benefits:
# ✅ Flexible: Can add conditions at each step
# ✅ Observable: Can track intermediate states
# ✅ Debuggable: Can log each step
# ✅ Extensible: Easy to modify rules
# ❌ Slower: O(n)
# ❌ More memory: O(1) but with overhead
```

### Rust Control Comparison

#### Without Simulation (Optimized)
```rust
fn sum_n(n: u64) -> u64 {
    n * (n + 1) / 2
}
// Rust compiler optimizes this to single instruction
// Benefits: Type safety + performance
```

#### With Simulation (Controlled)
```rust
fn sum_n_simulation(n: u64) -> u64 {
    let mut total = 0u64;
    for i in 1..=n {
        // Full control over each iteration
        total = total.checked_add(i)
            .expect("Overflow detected");
        // Can add: logging, breakpoints, state checks
    }
    total
}
// Benefits: 
// - Overflow detection (checked_add)
// - Step-by-step control
// - Can inject custom logic
```

---

## Summary: Key Takeaways

### Use Simulation When:
1. **Problem describes a process** (movement, time-based, events)
2. **Step-by-step logic is clearer** than formula
3. **Need to track intermediate states**
4. **Complex rules with many conditions**
5. **Debugging requires step visibility**

### Avoid Simulation When:
1. **Mathematical formula exists and is simpler**
2. **Performance is critical** and O(n) is too slow
3. **Problem can be solved with DP/greedy/binary search**

### Python vs Rust for Simulation

**Python Advantages:**
- Faster prototyping
- Dynamic typing for flexibility
- Rich standard library (deque, defaultdict)
- Easier debugging with print statements

**Rust Advantages:**
- Memory safety guarantees (no buffer overflows)
- Type system catches errors at compile time
- Zero-cost abstractions
- Better performance for large simulations
- Fearless concurrency (can parallelize simulations)

### Security Checklist
- ✅ Validate all inputs
- ✅ Set resource limits
- ✅ Check bounds before access
- ✅ Use overflow-safe arithmetic
- ✅ Sanitize external data
- ✅ Limit iteration counts

---

## Real-World Applications

1. **Game Engines**: Unity, Unreal Engine use simulation for physics, AI pathfinding
2. **Trading Systems**: Simulate market conditions, order execution
3. **Network Simulators**: ns-3, OMNeT++ simulate packet routing
4. **Autonomous Vehicles**: Simulate sensor data, obstacle avoidance
5. **Queueing Systems**: Simulate customer service, server load
6. **Scientific Computing**: Climate models, particle physics
7. **Robotics**: ROS (Robot Operating System) uses simulation extensively

---

## Further Learning

### Practice Problems:
1. **LeetCode 874**: Walking Robot Simulation
2. **LeetCode 353**: Design Snake Game
3. **LeetCode 489**: Robot Room Cleaner
4. **LeetCode 1823**: Find Winner of Circular Game
5. **LeetCode 735**: Asteroid Collision

### Architecture Patterns:
- **Event Loop Pattern**: Continuous simulation cycles
- **State Machine Pattern**: Discrete state transitions
- **Observer Pattern**: Track simulation changes
- **Command Pattern**: Queue simulation commands

### System Design:
- **Distributed Simulation**: Multiple agents, synchronization
- **Time Management**: Discrete vs continuous time
- **Scalability**: Parallel simulation, data partitioning
- **Fault Tolerance**: Checkpoint/restart, state recovery

---

## Advanced Simulation Patterns

### Problem 3: Traffic Light System (Event-Driven Simulation)

**Problem**: Simulate a traffic light system with multiple intersections. Each light cycles through states (RED → GREEN → YELLOW → RED) with specific timing.

**Real-World**: Smart city traffic management, IoT sensor networks, time-series event processing

#### Python Implementation

```python
from typing import Dict, List, Tuple, Optional
from enum import Enum
from dataclasses import dataclass
import heapq  # For event priority queue

class LightState(Enum):
    """Traffic light states"""
    RED = "RED"
    GREEN = "GREEN"
    YELLOW = "YELLOW"

@dataclass
class Event:
    """
    Event in simulation - using dataclass for automatic __init__, __repr__
    
    Attributes:
        time: When event occurs (timestamp)
        intersection_id: Which intersection
        new_state: State to transition to
    """
    time: int
    intersection_id: str
    new_state: LightState
    
    def __lt__(self, other: 'Event') -> bool:
        """
        Less-than comparison for heap operations.
        Events with earlier time have higher priority.
        """
        return self.time < other.time

class TrafficLightSimulator:
    """
    Event-driven simulation of traffic light system.
    
    Architecture:
    - Event Queue: Priority queue (min-heap) for events sorted by time
    - State Manager: Tracks current state of each intersection
    - Timing Rules: State transition durations
    
    Time Complexity: O(n log n) where n = number of events
    Space Complexity: O(k + n) where k = intersections, n = events
    
    Security: Validates timing to prevent infinite loops
    """
    
    # State transition timings (seconds)
    TIMINGS = {
        LightState.GREEN: 60,   # Green lasts 60 seconds
        LightState.YELLOW: 5,   # Yellow lasts 5 seconds
        LightState.RED: 60,     # Red lasts 60 seconds
    }
    
    # Next state mapping - defines the cycle
    NEXT_STATE = {
        LightState.RED: LightState.GREEN,
        LightState.GREEN: LightState.YELLOW,
        LightState.YELLOW: LightState.RED,
    }
    
    def __init__(self, intersections: List[str]) -> None:
        """
        Initialize traffic light simulator.
        
        Args:
            intersections: List of intersection IDs
            
        Security: Validates intersection list
        """
        if not intersections:
            raise ValueError("Must have at least one intersection")
        
        # Current state of each intersection
        self.states: Dict[str, LightState] = {
            iid: LightState.RED for iid in intersections
        }
        
        # Event queue - using heap for O(log n) insertion/extraction
        # heapq maintains min-heap property automatically
        self.event_queue: List[Event] = []
        
        # Current simulation time
        self.current_time: int = 0
        
        # Schedule initial events for all intersections
        for iid in intersections:
            self._schedule_next_event(iid, start_time=0)
    
    def _schedule_next_event(
        self, 
        intersection_id: str, 
        start_time: int
    ) -> None:
        """
        Schedule the next state transition event.
        
        Process:
        1. Get current state
        2. Determine next state
        3. Calculate event time
        4. Add to event queue
        
        Args:
            intersection_id: Intersection to schedule for
            start_time: When to schedule from
        """
        current_state = self.states[intersection_id]
        duration = self.TIMINGS[current_state]
        next_state = self.NEXT_STATE[current_state]
        
        event_time = start_time + duration
        
        event = Event(
            time=event_time,
            intersection_id=intersection_id,
            new_state=next_state
        )
        
        # heappush maintains heap invariant - O(log n)
        heapq.heappush(self.event_queue, event)
    
    def simulate(self, duration: int) -> List[Tuple[int, str, LightState]]:
        """
        Run simulation for specified duration.
        
        Args:
            duration: How long to simulate (seconds)
            
        Returns:
            List of (time, intersection_id, state) transitions
            
        Security: Limits duration to prevent resource exhaustion
        """
        MAX_DURATION = 86400  # 24 hours
        if duration > MAX_DURATION:
            raise ValueError(f"Duration exceeds limit of {MAX_DURATION}s")
        
        transitions: List[Tuple[int, str, LightState]] = []
        
        # Process events until end time or queue empty
        while self.event_queue and self.event_queue[0].time <= duration:
            # Extract earliest event - O(log n)
            event = heapq.heappop(self.event_queue)
            
            # Update simulation time
            self.current_time = event.time
            
            # Apply state transition
            old_state = self.states[event.intersection_id]
            self.states[event.intersection_id] = event.new_state
            
            # Record transition
            transitions.append((
                event.time,
                event.intersection_id,
                event.new_state
            ))
            
            # Schedule next transition for this intersection
            self._schedule_next_event(
                event.intersection_id,
                start_time=event.time
            )
        
        return transitions
    
    def get_state_at_time(
        self, 
        intersection_id: str, 
        time: int
    ) -> LightState:
        """
        Get the state of an intersection at a specific time.
        This requires simulating up to that time.
        """
        if time < self.current_time:
            raise ValueError("Cannot query past simulation time")
        
        # Simulate up to requested time
        self.simulate(time)
        return self.states[intersection_id]

# Test simulation
if __name__ == "__main__":
    print("🚦 Traffic Light Simulation\n")
    
    # Create simulator with 2 intersections
    intersections = ["North_Main", "South_Main"]
    simulator = TrafficLightSimulator(intersections)
    
    print(f"Intersections: {intersections}")
    print(f"Initial states: {simulator.states}\n")
    
    # Run simulation for 150 seconds
    transitions = simulator.simulate(duration=150)
    
    print("State Transitions:")
    print("-" * 60)
    for time, intersection, state in transitions:
        print(f"Time {time:3d}s | {intersection:12s} → {state.value}")
    
    print(f"\n✅ Total transitions: {len(transitions)}")
    print(f"Final simulation time: {simulator.current_time}s")
```

#### Rust Implementation

```rust
use std::collections::{BinaryHeap, HashMap};
use std::cmp::Ordering;

/// Traffic light states
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
enum LightState {
    Red,
    Green,
    Yellow,
}

impl LightState {
    /// Get duration in seconds for this state
    fn duration(&self) -> u32 {
        match self {
            LightState::Green => 60,
            LightState::Yellow => 5,
            LightState::Red => 60,
        }
    }
    
    /// Get next state in cycle
    fn next(&self) -> Self {
        match self {
            LightState::Red => LightState::Green,
            LightState::Green => LightState::Yellow,
            LightState::Yellow => LightState::Red,
        }
    }
}

/// Event in the simulation
/// 
/// Note: We implement custom Ord to make BinaryHeap a min-heap
/// (Rust's BinaryHeap is max-heap by default)
#[derive(Debug, Clone, Eq, PartialEq)]
struct Event {
    time: u32,
    intersection_id: String,
    new_state: LightState,
}

impl Ord for Event {
    fn cmp(&self, other: &Self) -> Ordering {
        // Reverse comparison to make min-heap
        other.time.cmp(&self.time)
    }
}

impl PartialOrd for Event {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

/// Traffic light simulator using event-driven architecture
pub struct TrafficLightSimulator {
    /// Current state of each intersection
    states: HashMap<String, LightState>,
    /// Priority queue of events (min-heap by time)
    event_queue: BinaryHeap<Event>,
    /// Current simulation time
    current_time: u32,
}

impl TrafficLightSimulator {
    /// Create new simulator with specified intersections
    /// 
    /// # Arguments
    /// * `intersections` - Vector of intersection IDs
    /// 
    /// # Panics
    /// Panics if intersections is empty
    pub fn new(intersections: Vec<String>) -> Self {
        assert!(!intersections.is_empty(), "Must have at least one intersection");
        
        let mut states = HashMap::new();
        let mut event_queue = BinaryHeap::new();
        
        // Initialize all intersections to RED state
        for id in &intersections {
            states.insert(id.clone(), LightState::Red);
            
            // Schedule first transition
            let event = Event {
                time: LightState::Red.duration(),
                intersection_id: id.clone(),
                new_state: LightState::Red.next(),
            };
            event_queue.push(event);
        }
        
        Self {
            states,
            event_queue,
            current_time: 0,
        }
    }
    
    /// Schedule next state transition for an intersection
    fn schedule_next_event(&mut self, intersection_id: &str, start_time: u32) {
        let current_state = self.states.get(intersection_id)
            .expect("Intersection not found");
        
        let duration = current_state.duration();
        let next_state = current_state.next();
        let event_time = start_time + duration;
        
        let event = Event {
            time: event_time,
            intersection_id: intersection_id.to_string(),
            new_state: next_state,
        };
        
        self.event_queue.push(event);
    }
    
    /// Run simulation for specified duration
    /// 
    /// # Arguments
    /// * `duration` - Simulation duration in seconds
    /// 
    /// # Returns
    /// Vector of (time, intersection_id, state) transitions
    /// 
    /// # Security
    /// Limits duration to prevent resource exhaustion
    pub fn simulate(&mut self, duration: u32) -> Vec<(u32, String, LightState)> {
        const MAX_DURATION: u32 = 86400; // 24 hours
        assert!(duration <= MAX_DURATION, "Duration exceeds safety limit");
        
        let mut transitions = Vec::new();
        
        // Process events until duration reached or queue empty
        while let Some(event) = self.event_queue.peek() {
            if event.time > duration {
                break;
            }
            
            // Extract event (pop removes and returns)
            let event = self.event_queue.pop().unwrap();
            
            // Update current time
            self.current_time = event.time;
            
            // Apply state transition
            self.states.insert(
                event.intersection_id.clone(),
                event.new_state
            );
            
            // Record transition
            transitions.push((
                event.time,
                event.intersection_id.clone(),
                event.new_state
            ));
            
            // Schedule next transition
            self.schedule_next_event(&event.intersection_id, event.time);
        }
        
        transitions
    }
    
    /// Get current state of an intersection
    pub fn get_state(&self, intersection_id: &str) -> Option<LightState> {
        self.states.get(intersection_id).copied()
    }
}

fn main() {
    println!("🚦 Traffic Light Simulation\n");
    
    let intersections = vec![
        "North_Main".to_string(),
        "South_Main".to_string(),
    ];
    
    let mut simulator = TrafficLightSimulator::new(intersections.clone());
    
    println!("Intersections: {:?}", intersections);
    println!("Initial states: {:?}\n", simulator.states);
    
    // Run simulation for 150 seconds
    let transitions = simulator.simulate(150);
    
    println!("State Transitions:");
    println!("{}", "-".repeat(60));
    
    for (time, intersection, state) in &transitions {
        println!("Time {:3}s | {:12} → {:?}", time, intersection, state);
    }
    
    println!("\n✅ Total transitions: {}", transitions.len());
    println!("Final simulation time: {}s", simulator.current_time);
}
```

---

### Problem 4: Particle Collision Simulation (Physics-Based)

**Problem**: Simulate particles moving in 1D space. Each particle has position and velocity. When two particles collide, they pass through each other. Find all collision times.

**Real-World**: Molecular dynamics, game physics engines, collision detection systems

#### Python Implementation

```python
from typing import List, Tuple, Optional
import heapq
from dataclasses import dataclass, field

@dataclass
class Particle:
    """
    Represents a particle in 1D space.
    
    Attributes:
        id: Unique identifier
        position: Current position (can be float)
        velocity: Velocity (positive = right, negative = left)
    """
    id: int
    position: float
    velocity: float
    
    def position_at_time(self, time: float) -> float:
        """Calculate position at given time using kinematics"""
        return self.position + self.velocity * time

@dataclass(order=True)
class Collision:
    """
    Represents a collision event.
    
    Note: Using order=True for automatic comparison based on time.
    field(compare=False) excludes particle_ids from comparison.
    """
    time: float
    particle_ids: Tuple[int, int] = field(compare=False)
    
    def __str__(self) -> str:
        return f"t={self.time:.2f}: Particles {self.particle_ids[0]} & {self.particle_ids[1]}"

class ParticleSimulator:
    """
    Physics-based particle collision simulator.
    
    Algorithm:
    1. Calculate all pairwise collision times
    2. Sort collisions by time
    3. Process collisions chronologically
    
    Time Complexity: O(n²) for n particles (pairwise comparison)
    Space Complexity: O(n²) for collision storage
    
    Physics Formula:
    For particles at positions p1, p2 with velocities v1, v2:
    Collision time t = (p2 - p1) / (v1 - v2) if v1 > v2
    """
    
    def __init__(self, particles: List[Particle]) -> None:
        """
        Initialize simulator.
        
        Args:
            particles: List of particles to simulate
            
        Security: Validates particle data
        """
        if not particles:
            raise ValueError("Must have at least one particle")
        
        # Validate particles
        for p in particles:
            if not isinstance(p.position, (int, float)):
                raise TypeError(f"Invalid position type for particle {p.id}")
            if not isinstance(p.velocity, (int, float)):
                raise TypeError(f"Invalid velocity type for particle {p.id}")
        
        self.particles = particles
        self.collisions: List[Collision] = []
    
    def _calculate_collision_time(
        self, 
        p1: Particle, 
        p2: Particle
    ) -> Optional[float]:
        """
        Calculate when two particles collide.
        
        Physics:
        - Particles collide when positions are equal
        - p1.pos + v1*t = p2.pos + v2*t
        - t = (p2.pos - p1.pos) / (v1 - v2)
        
        Args:
            p1, p2: Particles to check
            
        Returns:
            Collision time if they collide, None otherwise
        """
        # If velocities are equal, particles move parallel (no collision)
        if abs(p1.velocity - p2.velocity) < 1e-9:  # Float comparison tolerance
            return None
        
        # Calculate collision time
        collision_time = (p2.position - p1.position) / (p1.velocity - p2.velocity)
        
        # Collision must be in future (t > 0) and p1 must be catching up to p2
        if collision_time > 0 and p1.velocity > p2.velocity:
            return collision_time
        
        return None
    
    def find_all_collisions(self) -> List[Collision]:
        """
        Find all collision events.
        
        Process:
        1. Check all pairs of particles
        2. Calculate collision time for each pair
        3. Store valid collisions
        4. Sort by time
        
        Returns:
            List of collisions sorted by time
        """
        collisions: List[Collision] = []
        n = len(self.particles)
        
        # Check all pairs - O(n²)
        for i in range(n):
            for j in range(i + 1, n):
                p1 = self.particles[i]
                p2 = self.particles[j]
                
                # Ensure p1 is to the left of p2
                if p1.position > p2.position:
                    p1, p2 = p2, p1
                
                # Calculate collision
                collision_time = self._calculate_collision_time(p1, p2)
                
                if collision_time is not None:
                    collision = Collision(
                        time=collision_time,
                        particle_ids=(p1.id, p2.id)
                    )
                    collisions.append(collision)
        
        # Sort by time - O(n² log n)
        collisions.sort()
        
        self.collisions = collisions
        return collisions
    
    def simulate(self, end_time: float) -> List[Tuple[float, int, int]]:
        """
        Simulate particle motion and collisions.
        
        Args:
            end_time: When to stop simulation
            
        Returns:
            List of (time, particle1_id, particle2_id) collision events
        """
        # Find all collisions
        all_collisions = self.find_all_collisions()
        
        # Filter collisions within time window
        valid_collisions = [
            (c.time, c.particle_ids[0], c.particle_ids[1])
            for c in all_collisions
            if c.time <= end_time
        ]
        
        return valid_collisions
    
    def get_particle_position(
        self, 
        particle_id: int, 
        time: float
    ) -> float:
        """Get position of particle at specific time"""
        particle = next(
            (p for p in self.particles if p.id == particle_id),
            None
        )
        
        if particle is None:
            raise ValueError(f"Particle {particle_id} not found")
        
        return particle.position_at_time(time)

# Test simulation
if __name__ == "__main__":
    print("⚛️  Particle Collision Simulation\n")
    
    # Create particles
    # Particle: (id, position, velocity)
    particles = [
        Particle(id=0, position=0.0, velocity=3.0),   # Fast, left
        Particle(id=1, position=5.0, velocity=1.0),   # Slow, middle
        Particle(id=2, position=10.0, velocity=-2.0), # Moving left, right
    ]
    
    print("Initial Particles:")
    for p in particles:
        print(f"  Particle {p.id}: pos={p.position:.1f}, vel={p.velocity:.1f}")
    
    # Create simulator
    simulator = ParticleSimulator(particles)
    
    # Find collisions
    print("\n🔍 Finding collisions...")
    collisions = simulator.find_all_collisions()
    
    print(f"\nFound {len(collisions)} collision(s):")
    for collision in collisions:
        print(f"  {collision}")
        
        # Calculate positions at collision time
        p1_pos = simulator.get_particle_position(
            collision.particle_ids[0],
            collision.time
        )
        p2_pos = simulator.get_particle_position(
            collision.particle_ids[1],
            collision.time
        )
        print(f"    Collision point: ({p1_pos:.2f}, {p2_pos:.2f})")
    
    print("\n✅ Simulation complete!")
```

#### Rust Implementation

```rust
use std::cmp::Ordering;

/// Represents a particle in 1D space
#[derive(Debug, Clone, Copy)]
struct Particle {
    id: usize,
    position: f64,
    velocity: f64,
}

impl Particle {
    /// Calculate position at given time
    fn position_at_time(&self, time: f64) -> f64 {
        self.position + self.velocity * time
    }
}

/// Represents a collision event
#[derive(Debug, Clone)]
struct Collision {
    time: f64,
    particle_ids: (usize, usize),
}

impl Collision {
    fn new(time: f64, particle_ids: (usize, usize)) -> Self {
        Self { time, particle_ids }
    }
}

// Implement ordering for sorting collisions by time
impl PartialEq for Collision {
    fn eq(&self, other: &Self) -> bool {
        self.time == other.time
    }
}

impl Eq for Collision {}

impl PartialOrd for Collision {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        self.time.partial_cmp(&other.time)
    }
}

impl Ord for Collision {
    fn cmp(&self, other: &Self) -> Ordering {
        // Handle NaN by treating them as equal
        self.partial_cmp(other).unwrap_or(Ordering::Equal)
    }
}

/// Particle collision simulator
pub struct ParticleSimulator {
    particles: Vec<Particle>,
    collisions: Vec<Collision>,
}

impl ParticleSimulator {
    /// Create new simulator
    /// 
    /// # Arguments
    /// * `particles` - Vector of particles to simulate
    /// 
    /// # Panics
    /// Panics if particles vector is empty
    pub fn new(particles: Vec<Particle>) -> Self {
        assert!(!particles.is_empty(), "Must have at least one particle");
        
        Self {
            particles,
            collisions: Vec::new(),
        }
    }
    
    /// Calculate collision time between two particles
    /// 
    /// Physics: p1.pos + v1*t = p2.pos + v2*t
    /// Solving for t: t = (p2.pos - p1.pos) / (v1 - v2)
    /// 
    /// Returns None if no collision or collision in past
    fn calculate_collision_time(&self, p1: &Particle, p2: &Particle) -> Option<f64> {
        const EPSILON: f64 = 1e-9;
        
        let velocity_diff = p1.velocity - p2.velocity;
        
        // Parallel motion - no collision
        if velocity_diff.abs() < EPSILON {
            return None;
        }
        
        let position_diff = p2.position - p1.position;
        let collision_time = position_diff / velocity_diff;
        
        // Collision must be in future and p1 must be catching up
        if collision_time > 0.0 && p1.velocity > p2.velocity {
            Some(collision_time)
        } else {
            None
        }
    }
    
    /// Find all collision events
    /// 
    /// # Returns
    /// Vector of collisions sorted by time
    /// 
    /// # Time Complexity
    /// O(n²) for n particles (pairwise comparison)
    pub fn find_all_collisions(&mut self) -> &[Collision] {
        let mut collisions = Vec::new();
        let n = self.particles.len();
        
        // Check all pairs
        for i in 0..n {
            for j in (i + 1)..n {
                let mut p1 = self.particles[i];
                let mut p2 = self.particles[j];
                
                // Ensure p1 is to the left of p2
                if p1.position > p2.position {
                    std::mem::swap(&mut p1, &mut p2);
                }
                
                // Calculate collision
                if let Some(time) = self.calculate_collision_time(&p1, &p2) {
                    collisions.push(Collision::new(time, (p1.id, p2.id)));
                }
            }
        }
        
        // Sort by time
        collisions.sort();
        
        self.collisions = collisions;
        &self.collisions
    }
    
    /// Get particle position at specific time
    pub fn get_particle_position(&self, particle_id: usize, time: f64) -> Option<f64> {
        self.particles
            .iter()
            .find(|p| p.id == particle_id)
            .map(|p| p.position_at_time(time))
    }
}

fn main() {
    println!("⚛️  Particle Collision Simulation\n");
    
    // Create particles
    let particles = vec![
        Particle { id: 0, position: 0.0, velocity: 3.0 },
        Particle { id: 1, position: 5.0, velocity: 1.0 },
        Particle { id: 2, position: 10.0, velocity: -2.0 },
    ];
    
    println!("Initial Particles:");
    for p in &particles {
        println!("  Particle {}: pos={:.1}, vel={:.1}", p.id, p.position, p.velocity);
    }
    
    // Create simulator
    let mut simulator = ParticleSimulator::new(particles);
    
    // Find collisions
    println!("\n🔍 Finding collisions...");
    let collisions = simulator.find_all_collisions();
    
    println!("\nFound {} collision(s):", collisions.len());
    for collision in collisions {
        println!("  t={:.2}: Particles {} & {}", 
            collision.time, 
            collision.particle_ids.0, 
            collision.particle_ids.1
        );
        
        // Calculate positions at collision time
        if let (Some(p1_pos), Some(p2_pos)) = (
            simulator.get_particle_position(collision.particle_ids.0, collision.time),
            simulator.get_particle_position(collision.particle_ids.1, collision.time),
        ) {
            println!("    Collision point: ({:.2}, {:.2})", p1_pos, p2_pos);
        }
    }
    
    println!("\n✅ Simulation complete!");
}
```

---

## Memory Management & Performance Optimization

### Python Memory Considerations

```python
# INEFFICIENT: Creating new lists in loop
def simulate_inefficient(n: int) -> List[int]:
    result = []
    for i in range(n):
        # Creating temporary list each iteration - wasteful!
        temp = [x for x in range(i)]
        result.append(sum(temp))
    return result

# EFFICIENT: Reusing memory
def simulate_efficient(n: int) -> List[int]:
    result = []
    cumulative = 0
    for i in range(n):
        cumulative += i  # No temporary allocation
        result.append(cumulative)
    return result

# Using generator for memory efficiency
def simulate_generator(n: int):
    """
    Yields results one at a time - O(1) space instead of O(n).
    Perfect for large simulations where you process results incrementally.
    """
    cumulative = 0
    for i in range(n):
        cumulative += i
        yield cumulative  # Lazy evaluation
```

### Rust Memory Optimization

```rust
// INEFFICIENT: Unnecessary cloning
fn simulate_inefficient(data: Vec<i32>) -> Vec<i32> {
    let mut result = Vec::new();
    for item in &data {
        // Clone each time - expensive!
        result.push(item.clone());
    }
    result
}

// EFFICIENT: Using references and move semantics
fn simulate_efficient(data: Vec<i32>) -> Vec<i32> {
    // Take ownership directly - no cloning
    data
}

// EFFICIENT: Pre-allocate capacity
fn simulate_with_capacity(n: usize) -> Vec<i32> {
    // Reserve memory upfront - avoids reallocations
    let mut result = Vec::with_capacity(n);
    for i in 0..n {
        result.push(i as i32);
    }
    result
}

// Using iterators for zero-cost abstraction
fn simulate_iterator(n: usize) -> Vec<i32> {
    // Compiler optimizes this to same as manual loop
    // But more expressive and composable
    (0..n).map(|i| i as i32).collect()
}
```

---

## Parallel Simulation (Multi-threaded)

### Problem 5: Parallel Grid Simulation

**Real-World**: Weather simulation, cellular automata (Conway's Game of Life), distributed systems modeling

#### Python Implementation (Threading)

```python
from typing import List, Tuple, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from dataclasses import dataclass
import copy

@dataclass
class GridCell:
    """Represents a cell in the grid with its state"""
    alive: bool
    row: int
    col: int

class ParallelGridSimulator:
    """
    Conway's Game of Life - Parallel Implementation
    
    Rules:
    1. Any live cell with 2-3 neighbors survives
    2. Any dead cell with exactly 3 neighbors becomes alive
    3. All other cells die or stay dead
    
    Architecture:
    - Grid divided into chunks for parallel processing
    - Thread-safe state updates using locks
    - Barrier synchronization between generations
    
    Time Complexity: O(rows * cols / num_threads) per generation
    Space Complexity: O(rows * cols)
    
    Real-World: Weather models split globe into grid cells,
    each processed by different CPU cores
    """
    
    def __init__(
        self, 
        rows: int, 
        cols: int, 
        initial_alive: List[Tuple[int, int]],
        num_threads: int = 4
    ) -> None:
        """
        Initialize parallel grid simulator.
        
        Args:
            rows: Number of rows
            cols: Number of columns
            initial_alive: List of (row, col) initially alive
            num_threads: Number of parallel threads
            
        Security: Validates grid size and thread count
        """
        if rows <= 0 or cols <= 0:
            raise ValueError("Grid dimensions must be positive")
        if num_threads <= 0:
            raise ValueError("Thread count must be positive")
        
        self.rows = rows
        self.cols = cols
        self.num_threads = min(num_threads, rows)  # Cap threads at row count
        
        # Initialize grid - using list of lists for mutability
        self.grid: List[List[bool]] = [
            [False] * cols for _ in range(rows)
        ]
        
        # Set initial alive cells
        for row, col in initial_alive:
            if 0 <= row < rows and 0 <= col < cols:
                self.grid[row][col] = True
            else:
                raise ValueError(f"Invalid cell position: ({row}, {col})")
        
        # Thread synchronization
        self.lock = threading.Lock()
        self.generation = 0
    
    def _count_neighbors(self, row: int, col: int) -> int:
        """
        Count alive neighbors for a cell.
        
        Checks 8 adjacent cells (Moore neighborhood):
        NW  N  NE
        W  [X]  E
        SW  S  SE
        
        Time Complexity: O(1) - always checks 8 cells
        """
        count = 0
        # Direction vectors for 8 neighbors
        directions = [
            (-1, -1), (-1, 0), (-1, 1),  # Top row
            (0, -1),           (0, 1),    # Same row
            (1, -1),  (1, 0),  (1, 1)     # Bottom row
        ]
        
        for dr, dc in directions:
            nr, nc = row + dr, col + dc
            
            # Check bounds and if neighbor is alive
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                if self.grid[nr][nc]:
                    count += 1
        
        return count
    
    def _process_chunk(
        self, 
        start_row: int, 
        end_row: int
    ) -> List[Tuple[int, int, bool]]:
        """
        Process a chunk of rows for next generation.
        
        Args:
            start_row: Starting row (inclusive)
            end_row: Ending row (exclusive)
            
        Returns:
            List of (row, col, new_state) updates
            
        Note: Returns updates instead of modifying grid directly
        to avoid race conditions
        """
        updates: List[Tuple[int, int, bool]] = []
        
        for row in range(start_row, end_row):
            for col in range(self.cols):
                neighbors = self._count_neighbors(row, col)
                current_state = self.grid[row][col]
                
                # Apply Conway's rules
                new_state = False
                if current_state:
                    # Live cell survives with 2-3 neighbors
                    new_state = neighbors in (2, 3)
                else:
                    # Dead cell becomes alive with exactly 3 neighbors
                    new_state = neighbors == 3
                
                # Only record if state changes (optimization)
                if new_state != current_state:
                    updates.append((row, col, new_state))
        
        return updates
    
    def step(self) -> int:
        """
        Execute one generation step using parallel processing.
        
        Process:
        1. Divide grid into chunks
        2. Process each chunk in parallel thread
        3. Collect all updates
        4. Apply updates atomically
        
        Returns:
            Number of cells changed
            
        Security: Thread-safe updates using lock
        """
        # Calculate chunk size for each thread
        chunk_size = self.rows // self.num_threads
        
        all_updates: List[Tuple[int, int, bool]] = []
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            # Submit tasks for each chunk
            futures = []
            for i in range(self.num_threads):
                start_row = i * chunk_size
                # Last thread handles remaining rows
                end_row = (i + 1) * chunk_size if i < self.num_threads - 1 else self.rows
                
                future = executor.submit(self._process_chunk, start_row, end_row)
                futures.append(future)
            
            # Collect results as they complete
            for future in as_completed(futures):
                updates = future.result()
                all_updates.extend(updates)
        
        # Apply all updates atomically (thread-safe)
        with self.lock:
            for row, col, new_state in all_updates:
                self.grid[row][col] = new_state
            self.generation += 1
        
        return len(all_updates)
    
    def simulate(self, generations: int) -> List[int]:
        """
        Run simulation for multiple generations.
        
        Args:
            generations: Number of generations to simulate
            
        Returns:
            List of change counts per generation
        """
        if generations <= 0:
            raise ValueError("Generations must be positive")
        
        changes_per_generation = []
        
        for _ in range(generations):
            num_changes = self.step()
            changes_per_generation.append(num_changes)
            
            # Early termination if grid stabilizes
            if num_changes == 0:
                break
        
        return changes_per_generation
    
    def get_alive_cells(self) -> List[Tuple[int, int]]:
        """Get list of all alive cells"""
        alive = []
        for row in range(self.rows):
            for col in range(self.cols):
                if self.grid[row][col]:
                    alive.append((row, col))
        return alive
    
    def print_grid(self) -> None:
        """Print current grid state"""
        print(f"Generation {self.generation}:")
        for row in self.grid:
            print(''.join('█' if cell else '·' for cell in row))
        print()

# Test parallel simulation
if __name__ == "__main__":
    print("🧬 Conway's Game of Life - Parallel Simulation\n")
    
    # Create a "glider" pattern (moves diagonally)
    # Pattern:
    #  · █ ·
    #  · · █
    #  █ █ █
    initial_alive = [
        (0, 1),
        (1, 2),
        (2, 0), (2, 1), (2, 2)
    ]
    
    # Create 10x10 grid with 4 threads
    simulator = ParallelGridSimulator(
        rows=10,
        cols=10,
        initial_alive=initial_alive,
        num_threads=4
    )
    
    print("Initial state:")
    simulator.print_grid()
    
    # Run 5 generations
    changes = simulator.simulate(generations=5)
    
    print("Final state:")
    simulator.print_grid()
    
    print(f"Changes per generation: {changes}")
    print(f"✅ Simulation used {simulator.num_threads} threads")
```

#### Rust Implementation (Rayon - Data Parallelism)

```rust
use rayon::prelude::*;
use std::sync::{Arc, Mutex};

/// Grid cell position
type Position = (usize, usize);

/// Parallel grid simulator using Rayon for data parallelism
/// 
/// Rayon provides work-stealing parallelism - much more efficient
/// than manual thread management
pub struct ParallelGridSimulator {
    rows: usize,
    cols: usize,
    grid: Vec<Vec<bool>>,
    generation: usize,
}

impl ParallelGridSimulator {
    /// Create new simulator
    /// 
    /// # Arguments
    /// * `rows` - Number of rows
    /// * `cols` - Number of columns
    /// * `initial_alive` - Vector of initially alive cells
    pub fn new(rows: usize, cols: usize, initial_alive: Vec<Position>) -> Self {
        assert!(rows > 0 && cols > 0, "Grid dimensions must be positive");
        
        // Initialize grid
        let mut grid = vec![vec![false; cols]; rows];
        
        // Set initial alive cells
        for (row, col) in initial_alive {
            assert!(row < rows && col < cols, "Invalid cell position");
            grid[row][col] = true;
        }
        
        Self {
            rows,
            cols,
            grid,
            generation: 0,
        }
    }
    
    /// Count alive neighbors for a cell
    /// 
    /// Checks 8 adjacent cells (Moore neighborhood)
    fn count_neighbors(&self, row: usize, col: usize) -> usize {
        const DIRECTIONS: [(i32, i32); 8] = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1),
        ];
        
        let mut count = 0;
        
        for (dr, dc) in DIRECTIONS {
            // Calculate neighbor position with bounds checking
            let nr = row as i32 + dr;
            let nc = col as i32 + dc;
            
            // Check if in bounds
            if nr >= 0 && nr < self.rows as i32 && nc >= 0 && nc < self.cols as i32 {
                if self.grid[nr as usize][nc as usize] {
                    count += 1;
                }
            }
        }
        
        count
    }
    
    /// Calculate next state for a single cell
    fn next_cell_state(&self, row: usize, col: usize) -> bool {
        let neighbors = self.count_neighbors(row, col);
        let current = self.grid[row][col];
        
        // Conway's rules
        if current {
            // Live cell survives with 2-3 neighbors
            neighbors == 2 || neighbors == 3
        } else {
            // Dead cell becomes alive with exactly 3 neighbors
            neighbors == 3
        }
    }
    
    /// Execute one generation using parallel processing
    /// 
    /// # Returns
    /// Number of cells that changed state
    /// 
    /// # Performance
    /// Uses Rayon's par_iter for automatic parallelization
    /// Work is distributed across CPU cores automatically
    pub fn step(&mut self) -> usize {
        // Calculate next generation in parallel
        // Rayon automatically splits work across threads
        let new_grid: Vec<Vec<bool>> = (0..self.rows)
            .into_par_iter()  // Parallel iterator
            .map(|row| {
                // Process entire row in parallel
                (0..self.cols)
                    .map(|col| self.next_cell_state(row, col))
                    .collect()
            })
            .collect();
        
        // Count changes
        let changes = (0..self.rows)
            .into_par_iter()
            .map(|row| {
                (0..self.cols)
                    .filter(|&col| self.grid[row][col] != new_grid[row][col])
                    .count()
            })
            .sum();
        
        // Update grid
        self.grid = new_grid;
        self.generation += 1;
        
        changes
    }
    
    /// Run simulation for multiple generations
    /// 
    /// # Arguments
    /// * `generations` - Number of generations to simulate
    /// 
    /// # Returns
    /// Vector of change counts per generation
    pub fn simulate(&mut self, generations: usize) -> Vec<usize> {
        let mut changes_per_generation = Vec::with_capacity(generations);
        
        for _ in 0..generations {
            let num_changes = self.step();
            changes_per_generation.push(num_changes);
            
            // Early termination if stabilized
            if num_changes == 0 {
                break;
            }
        }
        
        changes_per_generation
    }
    
    /// Get list of alive cells
    pub fn get_alive_cells(&self) -> Vec<Position> {
        let mut alive = Vec::new();
        
        for row in 0..self.rows {
            for col in 0..self.cols {
                if self.grid[row][col] {
                    alive.push((row, col));
                }
            }
        }
        
        alive
    }
    
    /// Print grid state
    pub fn print_grid(&self) {
        println!("Generation {}:", self.generation);
        for row in &self.grid {
            for &cell in row {
                print!("{}", if cell { '█' } else { '·' });
            }
            println!();
        }
        println!();
    }
}

fn main() {
    println!("🧬 Conway's Game of Life - Parallel Simulation\n");
    
    // Create a "glider" pattern
    let initial_alive = vec![
        (0, 1),
        (1, 2),
        (2, 0), (2, 1), (2, 2),
    ];
    
    let mut simulator = ParallelGridSimulator::new(10, 10, initial_alive);
    
    println!("Initial state:");
    simulator.print_grid();
    
    // Run 5 generations
    let changes = simulator.simulate(5);
    
    println!("Final state:");
    simulator.print_grid();
    
    println!("Changes per generation: {:?}", changes);
    println!("✅ Simulation used Rayon's work-stealing scheduler");
}
```

**Note on Rayon**: Add to `Cargo.toml`:
```toml
[dependencies]
rayon = "1.8"
```

---

## Error Handling Patterns

### Python Error Handling

```python
from typing import Optional, Union
from enum import Enum

class SimulationError(Exception):
    """Base exception for simulation errors"""
    pass

class InvalidStateError(SimulationError):
    """Raised when simulation enters invalid state"""
    pass

class BoundaryViolationError(SimulationError):
    """Raised when entity moves out of bounds"""
    pass

class RobustSimulator:
    """
    Demonstrates comprehensive error handling in simulations.
    
    Security: All input validated, all state transitions checked
    """
    
    def __init__(self, grid_size: int) -> None:
        # Input validation with clear error messages
        if not isinstance(grid_size, int):
            raise TypeError(
                f"grid_size must be int, got {type(grid_size).__name__}"
            )
        
        if grid_size <= 0:
            raise ValueError(
                f"grid_size must be positive, got {grid_size}"
            )
        
        if grid_size > 10000:
            raise ValueError(
                f"grid_size exceeds safety limit of 10000, got {grid_size}"
            )
        
        self.grid_size = grid_size
        self.position = (0, 0)
    
    def move(self, dx: int, dy: int) -> Optional[tuple[int, int]]:
        """
        Move with comprehensive error handling.
        
        Returns:
            New position on success, None on boundary violation
            
        Raises:
            TypeError: If dx or dy not integers
            InvalidStateError: If simulator in invalid state
        """
        # Type validation
        if not isinstance(dx, int) or not isinstance(dy, int):
            raise TypeError("Movement deltas must be integers")
        
        # Calculate new position
        new_x = self.position[0] + dx
        new_y = self.position[1] + dy
        
        # Boundary check - return None instead of raising
        # This allows caller to handle gracefully
        if not (0 <= new_x < self.grid_size and 0 <= new_y < self.grid_size):
            return None
        
        # State validation
        if not hasattr(self, 'position'):
            raise InvalidStateError("Simulator not properly initialized")
        
        # Apply movement
        self.position = (new_x, new_y)
        return self.position
    
    def move_strict(self, dx: int, dy: int) -> tuple[int, int]:
        """
        Move with strict error handling (raises on violation).
        
        Use this when boundary violations are programmer errors
        that should crash the program.
        """
        result = self.move(dx, dy)
        
        if result is None:
            raise BoundaryViolationError(
                f"Movement ({dx}, {dy}) from {self.position} "
                f"exceeds grid bounds {self.grid_size}"
            )
        
        return result

# Example usage with error handling
def safe_simulation_example():
    """Demonstrates safe simulation with error handling"""
    try:
        sim = RobustSimulator(grid_size=10)
        
        # Try to move - handle failure gracefully
        new_pos = sim.move(5, 5)
        if new_pos is None:
            print("⚠️  Movement blocked by boundary")
        else:
            print(f"✅ Moved to {new_pos}")
        
        # Strict movement - will raise on error
        sim.move_strict(100, 100)
        
    except BoundaryViolationError as e:
        print(f"❌ Boundary violation: {e}")
    except SimulationError as e:
        print(f"❌ Simulation error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        # Cleanup code always runs
        print("🧹 Cleanup complete")

if __name__ == "__main__":
    safe_simulation_example()
```

### Rust Error Handling (Result Type)

```rust
use std::fmt;

/// Custom error types for simulation
#[derive(Debug)]
pub enum SimulationError {
    InvalidState(String),
    BoundaryViolation { position: (i32, i32), bounds: usize },
    InvalidInput { field: String, value: String },
}

impl fmt::Display for SimulationError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            SimulationError::InvalidState(msg) => {
                write!(f, "Invalid state: {}", msg)
            }
            SimulationError::BoundaryViolation { position, bounds } => {
                write!(
                    f,
                    "Position ({}, {}) exceeds bounds {}",
                    position.0, position.1, bounds
                )
            }
            SimulationError::InvalidInput { field, value } => {
                write!(f, "Invalid input for {}: {}", field, value)
            }
        }
    }
}

impl std::error::Error for SimulationError {}

/// Result type alias for cleaner code
pub type SimResult<T> = Result<T, SimulationError>;

/// Robust simulator with comprehensive error handling
pub struct RobustSimulator {
    grid_size: usize,
    position: (i32, i32),
}

impl RobustSimulator {
    /// Create new simulator with validation
    /// 
    /// # Arguments
    /// * `grid_size` - Size of simulation grid
    /// 
    /// # Returns
    /// Result containing simulator or error
    /// 
    /// # Errors
    /// Returns InvalidInput if grid_size is invalid
    pub fn new(grid_size: usize) -> SimResult<Self> {
        const MAX_GRID_SIZE: usize = 10000;
        
        if grid_size == 0 {
            return Err(SimulationError::InvalidInput {
                field: "grid_size".to_string(),
                value: "0".to_string(),
            });
        }
        
        if grid_size > MAX_GRID_SIZE {
            return Err(SimulationError::InvalidInput {
                field: "grid_size".to_string(),
                value: format!("{} (exceeds {})", grid_size, MAX_GRID_SIZE),
            });
        }
        
        Ok(Self {
            grid_size,
            position: (0, 0),
        })
    }
    
    /// Move with error handling
    /// 
    /// # Returns
    /// Result containing new position or error
    /// 
    /// # Errors
    /// Returns BoundaryViolation if move exceeds bounds
    pub fn move_entity(&mut self, dx: i32, dy: i32) -> SimResult<(i32, i32)> {
        let new_x = self.position.0 + dx;
        let new_y = self.position.1 + dy;
        
        // Boundary check
        if new_x < 0 || new_x >= self.grid_size as i32 ||
           new_y < 0 || new_y >= self.grid_size as i32 {
            return Err(SimulationError::BoundaryViolation {
                position: (new_x, new_y),
                bounds: self.grid_size,
            });
        }
        
        self.position = (new_x, new_y);
        Ok(self.position)
    }
    
    /// Checked move with overflow detection
    /// 
    /// # Security
    /// Uses checked arithmetic to prevent integer overflow
    pub fn move_checked(&mut self, dx: i32, dy: i32) -> SimResult<(i32, i32)> {
        // Checked addition prevents overflow
        let new_x = self.position.0.checked_add(dx)
            .ok_or_else(|| SimulationError::InvalidState(
                "Position overflow on x-axis".to_string()
            ))?;
        
        let new_y = self.position.1.checked_add(dy)
            .ok_or_else(|| SimulationError::InvalidState(
                "Position overflow on y-axis".to_string()
            ))?;
        
        // Boundary check
        if new_x < 0 || new_x >= self.grid_size as i32 ||
           new_y < 0 || new_y >= self.grid_size as i32 {
            return Err(SimulationError::BoundaryViolation {
                position: (new_x, new_y),
                bounds: self.grid_size,
            });
        }
        
        self.position = (new_x, new_y);
        Ok(self.position)
    }
}

// Example usage with error handling
fn safe_simulation_example() {
    // Using ? operator for error propagation
    let result = (|| -> SimResult<()> {
        let mut sim = RobustSimulator::new(10)?;
        
        // This succeeds
        let pos = sim.move_entity(5, 5)?;
        println!("✅ Moved to ({}, {})", pos.0, pos.1);
        
        // This fails with boundary violation
        sim.move_entity(100, 100)?;
        
        Ok(())
    })();
    
    // Pattern matching on result
    match result {
        Ok(()) => println!("✅ Simulation completed successfully"),
        Err(SimulationError::BoundaryViolation { position, bounds }) => {
            println!(
                "❌ Boundary violation: position ({}, {}) exceeds bounds {}",
                position.0, position.1, bounds
            );
        }
        Err(e) => println!("❌ Simulation error: {}", e),
    }
}

fn main() {
    safe_simulation_example();
}
```

---

## Testing Simulation Code

### Python Unit Tests

```python
import unittest
from typing import List

class TestRobotSimulation(unittest.TestCase):
    """
    Unit tests for robot simulation.
    
    Testing Strategy:
    1. Test normal cases
    2. Test edge cases (empty input, single command)
    3. Test boundary conditions
    4. Test error handling
    """
    
    def test_basic_movement(self):
        """Test basic UDLR movements"""
        result = simulate_robot_walk("UURR")
        self.assertEqual(result, (2, 2))
    
    def test_return_to_origin(self):
        """Test circular path returns to start"""
        result = simulate_robot_walk("UDLR")
        self.assertEqual(result, (0, 0))
    
    def test_empty_commands(self):
        """Test empty command string"""
        result = simulate_robot_walk("")
        self.assertEqual(result, (0, 0))
    
    def test_single_command(self):
        """Test single command"""
        self.assertEqual(simulate_robot_walk("U"), (0, 1))
        self.assertEqual(simulate_robot_walk("D"), (0, -1))
        self.assertEqual(simulate_robot_walk("L"), (-1, 0))
        self.assertEqual(simulate_robot_walk("R"), (1, 0))
    
    def test_invalid_command(self):
        """Test invalid command raises error"""
        with self.assertRaises(ValueError):
            simulate_robot_walk("UURX")
    
    def test_type_error(self):
        """Test invalid type raises error"""
        with self.assertRaises(TypeError):
            simulate_robot_walk(123)  # type: ignore
    
    def test_large_input(self):
        """Test performance with large input"""
        # Create large command string
        commands = "UDLR" * 10000
        result = simulate_robot_walk(commands)
        self.assertEqual(result, (0, 0))  # Should cancel out

if __name__ == "__main__":
    unittest.main()
```

### Rust Tests

```rust
#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_basic_movement() {
        let result = simulate_robot_walk("UURR").unwrap();
        assert_eq!(result, Position { x: 2, y: 2 });
    }
    
    #[test]
    fn test_return_to_origin() {
        let result = simulate_robot_walk("UDLR").unwrap();
        assert_eq!(result, Position { x: 0, y: 0 });
    }
    
    #[test]
    fn test_empty_commands() {
        let result = simulate_robot_walk("");
        assert!(result.is_err());
    }
    
    #[test]
    fn test_invalid_command() {
        let result = simulate_robot_walk("UURX");
        assert!(matches!(result, Err(SimulationError::InvalidCommand('X'))));
    }
    
    #[test]
    fn test_overflow_detection() {
        // Create simulator
        let mut sim = RobustSimulator::new(10).unwrap();
        
        // This should fail with overflow
        let result = sim.move_checked(i32::MAX, 0);
        assert!(result.is_err());
    }
    
    #[test]
    fn test_boundary_violation() {
        let mut sim = RobustSimulator::new(10).unwrap();
        let result = sim.move_entity(100, 100);
        
        assert!(matches!(
            result,
            Err(SimulationError::BoundaryViolation { .. })
        ));
    }
    
    // Property-based testing example
    #[test]
    fn test_property_opposite_movements_cancel() {
        // U then D should cancel
        assert_eq!(
            simulate_robot_walk("UD").unwrap(),
            Position { x: 0, y: 0 }
        );
        
        // L then R should cancel
        assert_eq!(
            simulate_robot_walk("LR").unwrap(),
            Position { x: 0, y: 0 }
        );
    }
}
```

---

## Performance Profiling

### Python Profiling

```python
import cProfile
import pstats
from io import StringIO

def profile_simulation():
    """Profile simulation performance"""
    profiler = cProfile.Profile()
    
    # Start profiling
    profiler.enable()
    
    # Run simulation
    simulator = SnakeGame(100, 100, [])
    for _ in range(1000):
        simulator.move('R')
    
    # Stop profiling
    profiler.disable()
    
    # Print stats
    s = StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats()
    print(s.getvalue())

# Timing comparison
import time

def benchmark_data_structures():
    """Compare different data structure performance"""
    # Test list vs deque for queue operations
    from collections import deque
    
    n = 100000
    
    # List (slow)
    start = time.time()
    queue_list = []
    for i in range(n):
        queue_list.append(i)
    for _ in range(n):
        queue_list.pop(0)  # O(n) operation!
    list_time = time.time() - start
    
    # Deque (fast)
    start = time.time()
    queue_deque = deque()
    for i in range(n):
        queue_deque.append(i)
    for _ in range(n):
        queue_deque.popleft()  # O(1) operation!
    deque_time = time.time() - start
    
    print(f"List time: {list_time:.3f}s")
    print(f"Deque time: {deque_time:.3f}s")
    print(f"Speedup: {list_time/deque_time:.1f}x")

if __name__ == "__main__":
    benchmark_data_structures()
```

### Rust Benchmarking

```rust
// Add to Cargo.toml:
// [dev-dependencies]
// criterion = "0.5"

#[cfg(test)]
mod benchmarks {
    use criterion::{black_box, criterion_group, criterion_main, Criterion};
    use super::*;
    
    fn bench_robot_walk(c: &mut Criterion) {
        c.bench_function("robot_walk_1000", |b| {
            let commands = "UDLR".repeat(250);
            b.iter(|| {
                simulate_robot_walk(black_box(&commands))
            });
        });
    }
    
    fn bench_snake_game(c: &mut Criterion) {
        c.bench_function("snake_game_100_moves", |b| {
            b.iter(|| {
                let mut game = SnakeGame::new(10, 10, vec![]);
                for _ in 0..100 {
                    game.move_snake(black_box("R"));
                }
            });
        });
    }
    
    criterion_group!(benches, bench_robot_walk, bench_snake_game);
    criterion_main!(benches);
}
```

---

## Real-World System Design: Distributed Simulation

### Architecture for Large-Scale Simulation

```
┌─────────────────────────────────────────────────────┐
│              Load Balancer / API Gateway            │
└─────────────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼──────┐  ┌──────▼──────┐  ┌─────▼───────┐
│ Simulation   │  │ Simulation  │  │ Simulation  │
│ Worker 1     │  │ Worker 2    │  │ Worker 3    │
│              │  │             │  │             │
│ Region A     │  │ Region B    │  │ Region C    │
└──────┬───────┘  └──────┬──────┘  └─────┬───────┘
       │                 │                │
       └─────────────────┼────────────────┘
                         │
                ┌────────▼────────┐
                │  State Store    │
                │  (Redis/DB)     │
                └─────────────────┘
```

### Python - Distributed Simulation with Redis

```python
from typing import Dict, List, Tuple, Optional
import redis
import json
import hashlib
from dataclasses import dataclass, asdict
import uuid

@dataclass
class SimulationState:
    """
    Represents a chunk of simulation state.
    
    Design: Each worker handles a region of the simulation space.
    Workers communicate via shared state store (Redis).
    """
    region_id: str
    entities: List[Dict]
    timestamp: int
    worker_id: str

class DistributedSimulator:
    """
    Distributed simulation system using Redis for coordination.
    
    Architecture:
    - Each worker simulates a region of space
    - State stored in Redis for coordination
    - Workers poll for boundary updates from neighbors
    
    Real-World: This pattern used in:
    - Massively multiplayer games (regional servers)
    - Weather simulation (grid partitioning)
    - Traffic simulation (city districts)
    
    Security: All state validated before application
    """
    
    def __init__(
        self,
        worker_id: str,
        region_id: str,
        redis_host: str = 'localhost',
        redis_port: int = 6379
    ):
        """
        Initialize distributed simulator worker.
        
        Args:
            worker_id: Unique worker identifier
            region_id: Region this worker handles
            redis_host: Redis server host
            redis_port: Redis server port
        """
        self.worker_id = worker_id
        self.region_id = region_id
        
        # Connect to Redis (state store)
        # In production, use connection pooling
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True
        )
        
        # Local state cache
        self.local_state: Dict = {}
        self.timestamp = 0
    
    def _get_state_key(self, region_id: str) -> str:
        """Generate Redis key for region state"""
        return f"sim:region:{region_id}:state"
    
    def _get_lock_key(self, region_id: str) -> str:
        """Generate Redis key for region lock"""
        return f"sim:region:{region_id}:lock"
    
    def save_state(self, entities: List[Dict]) -> bool:
        """
        Save region state to Redis.
        
        Args:
            entities: List of entity dictionaries
            
        Returns:
            True if successful
            
        Security: Validates entities before saving
        """
        # Validate entities
        for entity in entities:
            if not isinstance(entity, dict):
                raise TypeError("Entity must be dict")
            if 'id' not in entity or 'position' not in entity:
                raise ValueError("Entity must have id and position")
        
        # Create state object
        state = SimulationState(
            region_id=self.region_id,
            entities=entities,
            timestamp=self.timestamp,
            worker_id=self.worker_id
        )
        
        # Serialize to JSON
        state_json = json.dumps(asdict(state))
        
        # Save to Redis with expiration (1 hour)
        key = self._get_state_key(self.region_id)
        self.redis_client.setex(key, 3600, state_json)
        
        return True
    
    def load_state(self, region_id: str) -> Optional[SimulationState]:
        """
        Load region state from Redis.
        
        Args:
            region_id: Region to load
            
        Returns:
            SimulationState or None if not found
        """
        key = self._get_state_key(region_id)
        state_json = self.redis_client.get(key)
        
        if state_json is None:
            return None
        
        # Deserialize
        state_dict = json.loads(state_json)
        return SimulationState(**state_dict)
    
    def acquire_lock(self, timeout: int = 10) -> bool:
        """
        Acquire distributed lock for region.
        
        Uses Redis SET NX (set if not exists) for atomic locking.
        
        Args:
            timeout: Lock timeout in seconds
            
        Returns:
            True if lock acquired
        """
        lock_key = self._get_lock_key(self.region_id)
        lock_value = f"{self.worker_id}:{uuid.uuid4()}"
        
        # SET NX with expiration - atomic operation
        acquired = self.redis_client.set(
            lock_key,
            lock_value,
            nx=True,  # Only set if key doesn't exist
            ex=timeout  # Expiration time
        )
        
        if acquired:
            # Store lock value to verify ownership
            self.local_state['lock_value'] = lock_value
            return True
        
        return False
    
    def release_lock(self) -> bool:
        """
        Release distributed lock.
        
        Security: Verifies lock ownership before release
        """
        lock_key = self._get_lock_key(self.region_id)
        lock_value = self.local_state.get('lock_value')
        
        if lock_value is None:
            return False
        
        # Lua script for atomic check-and-delete
        # This prevents releasing someone else's lock
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        
        result = self.redis_client.eval(lua_script, 1, lock_key, lock_value)
        return bool(result)
    
    def step(self, entities: List[Dict]) -> List[Dict]:
        """
        Execute one simulation step with distributed coordination.
        
        Process:
        1. Acquire lock for region
        2. Load neighbor states (boundary conditions)
        3. Simulate local region
        4. Save updated state
        5. Release lock
        
        Args:
            entities: Current entities in region
            
        Returns:
            Updated entities
        """
        # Acquire lock
        if not self.acquire_lock():
            raise RuntimeError(f"Failed to acquire lock for {self.region_id}")
        
        try:
            # Simulate (placeholder - implement actual logic)
            updated_entities = []
            for entity in entities:
                # Example: Move entity
                pos = entity['position']
                entity['position'] = (pos[0] + 1, pos[1])
                updated_entities.append(entity)
            
            # Save state
            self.timestamp += 1
            self.save_state(updated_entities)
            
            return updated_entities
            
        finally:
            # Always release lock
            self.release_lock()

# Example usage
if __name__ == "__main__":
    print("🌐 Distributed Simulation System\n")
    
    # Create worker for Region A
    worker = DistributedSimulator(
        worker_id="worker-1",
        region_id="region-a"
    )
    
    # Initial entities
    entities = [
        {'id': 1, 'position': (0, 0), 'type': 'robot'},
        {'id': 2, 'position': (5, 5), 'type': 'robot'},
    ]
    
    print("Running simulation step...")
    try:
        updated = worker.step(entities)
        print(f"✅ Updated {len(updated)} entities")
        
        # Load state to verify
        state = worker.load_state("region-a")
        if state:
            print(f"State timestamp: {state.timestamp}")
            print(f"Worker: {state.worker_id}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
```

---

## Complete Comparison Table: Simulation vs Other Approaches

| Aspect | Simulation | Mathematical Formula | DP/Memoization | Greedy |
|--------|-----------|---------------------|----------------|--------|
| **Time Complexity** | O(n) to O(n²) | O(1) to O(log n) | O(n·m) state space | O(n log n) |
| **Space Complexity** | O(state size) | O(1) | O(n·m) | O(1) to O(n) |
| **Debuggability** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Flexibility** | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Performance** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Code Clarity** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Use Case** | Process modeling | Math problems | Optimization | Local optimal |

---

## Industry Best Practices

### 1. Simulation Design Checklist

```python
"""
Simulation Design Checklist
---------------------------

□ State Management
  ✓ All state variables identified
  ✓ State transitions clearly defined
  ✓ Initial state properly initialized
  ✓ State validation implemented

□ Time Management
  ✓ Time step size chosen appropriately
  ✓ Event ordering strategy defined
  ✓ Synchronization mechanism in place

□ Boundary Conditions
  ✓ Edge cases identified
  ✓ Boundary handling implemented
  ✓ Wraparound vs. hard boundaries decided

□ Performance
  ✓ Complexity analysis completed
  ✓ Data structures optimized
  ✓ Profiling performed
  ✓ Parallelization considered

□ Validation
  ✓ Unit tests written
  ✓ Integration tests added
  ✓ Property-based tests considered
  ✓ Results validated against known cases

□ Security
  ✓ Input validation implemented
  ✓ Resource limits set
  ✓ Overflow protection added
  ✓ Error handling comprehensive
"""
```

### 2. Code Review Guidelines

```rust
/*
Simulation Code Review Checklist
---------------------------------

Memory Safety (Rust-specific):
□ No unsafe blocks without justification
□ All borrows properly scoped
□ No data races in concurrent code
□ Proper lifetime annotations

General:
□ State mutations are controlled
□ No hidden side effects
□ Error handling is comprehensive
□ Documentation explains "why" not just "what"
□ Tests cover edge cases
□ Performance characteristics documented
*/
```

### 3. Common Anti-Patterns to Avoid

```python
# ❌ ANTI-PATTERN 1: Hidden State
class BadSimulator:
    def step(self):
        # Modifying global state - hard to test!
        global_state.update()

# ✅ BETTER: Explicit State
class GoodSimulator:
    def step(self, state: State) -> State:
        # Pure function - easy to test!
        return state.updated()


# ❌ ANTI-PATTERN 2: God Object
class MonolithicSimulator:
    # Does everything - hard to maintain
    def simulate_physics(self): pass
    def simulate_ai(self): pass
    def simulate_network(self): pass
    def simulate_economy(self): pass

# ✅ BETTER: Separated Concerns
class PhysicsSimulator: pass
class AISimulator: pass
class NetworkSimulator: pass
# Each handles one aspect


# ❌ ANTI-PATTERN 3: Magic Numbers
def simulate(steps):
    if steps > 1000000:  # What is this limit?
        raise Error()

# ✅ BETTER: Named Constants
MAX_SIMULATION_STEPS = 1_000_000  # Prevents memory exhaustion

def simulate(steps):
    if steps > MAX_SIMULATION_STEPS:
        raise Error("Exceeds safety limit")
```

---

## Visualization and Debugging Tools

### Python Visualization with Matplotlib

```python
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from typing import List, Tuple
import numpy as np

class SimulationVisualizer:
    """
    Visualize simulation in real-time.
    
    Useful for:
    - Debugging movement patterns
    - Verifying collision detection
    - Understanding system behavior
    """
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.fig, self.ax = plt.subplots()
        self.history: List[List[Tuple[int, int]]] = []
    
    def record_frame(self, positions: List[Tuple[int, int]]):
        """Record positions for this frame"""
        self.history.append(positions.copy())
    
    def animate(self, interval: int = 100):
        """
        Create animation of simulation.
        
        Args:
            interval: Milliseconds between frames
        """
        def update(frame):
            self.ax.clear()
            self.ax.set_xlim(0, self.width)
            self.ax.set_ylim(0, self.height)
            self.ax.set_title(f"Frame {frame}")
            
            if frame < len(self.history):
                positions = self.history[frame]
                if positions:
                    x, y = zip(*positions)
                    self.ax.scatter(x, y, c='blue', s=100)
        
        anim = animation.FuncAnimation(
            self.fig,
            update,
            frames=len(self.history),
            interval=interval,
            repeat=True
        )
        
        plt.show()

# Example usage
def visualize_robot_path():
    """Visualize robot walking pattern"""
    viz = SimulationVisualizer(20, 20)
    
    x, y = 10, 10
    commands = "UUURRRDDDLLL"
    
    moves = {
        'U': (0, 1), 'D': (0, -1),
        'L': (-1, 0), 'R': (1, 0)
    }
    
    # Record initial position
    viz.record_frame([(x, y)])
    
    # Simulate and record
    for cmd in commands:
        dx, dy = moves[cmd]
        x += dx
        y += dy
        viz.record_frame([(x, y)])
    
    # Animate
    viz.animate(interval=200)
```

---

## Final Summary: When to Choose What

### Decision Tree

```
Is the problem explicitly describing a step-by-step process?
│
├─ YES: Can you find a mathematical formula?
│   │
│   ├─ YES: Use formula (e.g., sum = n*(n+1)/2)
│   │
│   └─ NO: Does it involve state transitions?
│       │
│       ├─ YES: Use SIMULATION ✓
│       │
│       └─ NO: Consider DP or Greedy
│
└─ NO: Is it an optimization problem?
    │
    ├─ YES: Try DP or Greedy first
    │
    └─ NO: Graph algorithm or other approach
```

### Language Choice Guide

**Choose Python when:**
- Rapid prototyping needed
- Rich libraries required (NumPy, matplotlib)
- Data science integration important
- Team familiar with Python
- Performance not critical

**Choose Rust when:**
- Performance critical (real-time systems)
- Memory safety required
- Long-running simulations
- Embedded systems
- Concurrent/parallel execution important

### Key Takeaways

1. **Simulation = Direct Modeling**: Execute each step of the process
2. **Use for clarity**: When step-by-step logic is clearer than formula
3. **Validate everything**: Input, state, boundaries
4. **Choose right data structures**: deque for queues, sets for lookups
5. **Handle errors gracefully**: Comprehensive error handling
6. **Test thoroughly**: Unit tests, edge cases, performance tests
7. **Profile before optimizing**: Measure, don't guess
8. **Document the "why"**: Explain design decisions
9. **Security matters**: Validate, limit resources, check overflows
10. **Parallelization helps**: For large-scale simulations

---

## Additional Resources

### Books
- "Introduction to Algorithms" (CLRS) - Chapter on simulation
- "The Algorithm Design Manual" - Simulation patterns
- "Programming Rust" - Systems programming
- "Fluent Python" - Advanced Python patterns

### Online Resources
- LeetCode Simulation Problems: #874, #353, #489, #1823, #735
- Rust Book: https://doc.rust-lang.org/book/
- Python Type Hints: https://docs.python.org/3/library/typing.html

### Tools
- **Python**: pytest, mypy (type checking), cProfile, memory_profiler
- **Rust**: cargo test, cargo bench, criterion, flamegraph
- **Visualization**: matplotlib, plotly, D3.js
- **Profiling**: perf, valgrind, py-spy

---

## Conclusion

Simulation is a fundamental technique in DSA that trades mathematical elegance for **clarity, flexibility, and debuggability**. Use it when the problem naturally describes a process, when state management is complex, or when you need to track intermediate results.

**Remember**: The best solution isn't always the fastest—it's the one that's **correct, maintainable, and appropriate** for your constraints.

**Security First**: Always validate inputs, set resource limits, handle errors, and check boundaries. These aren't optional—they're essential.

**Type Safety**: Both Python (with type hints) and Rust (with its type system) help catch errors early. Use them!

Happy simulating! 🚀

Perfect! I've completed the comprehensive guide on **Simulation in DSA**. Here's what the complete guide now covers:

## 📚 Complete Guide Contents:

### Core Concepts:
1. ✅ **What is Simulation** - Internal workings with real-world examples
2. ✅ **When to Use/Avoid** - Decision framework
3. ✅ **Core Concepts** - State management, time steps, rules, boundaries

### 5 Complete Problem Implementations:
1. ✅ **Robot Walking** (Basic) - Grid navigation
2. ✅ **Snake Game** (Intermediate) - Game simulation with collision
3. ✅ **Traffic Light System** (Event-Driven) - Priority queue based
4. ✅ **Particle Collision** (Physics-Based) - Scientific computing
5. ✅ **Conway's Game of Life** (Parallel) - Multi-threaded processing

### Advanced Topics:
- ✅ **Memory Management** - Efficient vs inefficient patterns
- ✅ **Parallel Simulation** - Threading (Python) and Rayon (Rust)
- ✅ **Error Handling** - Comprehensive patterns for both languages
- ✅ **Distributed Systems** - Redis-based coordination
- ✅ **Testing Strategies** - Unit tests, property-based tests
- ✅ **Performance Profiling** - Benchmarking and optimization
- ✅ **Visualization** - Matplotlib animations for debugging

### Security & Best Practices:
- ✅ Input validation examples
- ✅ Resource limit enforcement
- ✅ Overflow protection (especially Rust)
- ✅ Thread-safe operations
- ✅ Code review checklist
- ✅ Anti-patterns to avoid

### Comparison Analysis:
- ✅ Benefits of simulation vs formulas
- ✅ Control differences Python vs Rust
- ✅ When to use each approach
- ✅ Performance trade-offs table

## 🎯 Key Highlights:

**For Your Preferences:**
- All Python code has **type hints** for readability
- Comments explain **internal functionality** and architectural decisions
- Real-world examples for every concept
- **Security-first** approach throughout
- Focus on DSA fundamentals with system design touches

**Rust Benefits Demonstrated:**
- Memory safety with ownership
- Compile-time error catching
- Zero-cost abstractions
- Fearless concurrency with Rayon
- Result type for error handling

**Python Benefits Demonstrated:**
- Rapid prototyping
- Rich standard library (deque, heapq)
- Type hints for clarity
- Threading and multiprocessing
- Easy visualization with matplotlib

This guide provides everything you need to understand simulation deeply, implement it correctly in both languages, and make informed decisions about when to use it versus other approaches!