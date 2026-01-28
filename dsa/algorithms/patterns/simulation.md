# Complete Guide to Simulation Problems in Competitive Programming

## I. Understanding Simulation: The Foundation

**What is Simulation?**

Simulation problems ask you to model a real-world or abstract process *exactly as described*. You implement the rules step-by-step, tracking state changes over time. No fancy algorithms—just precise rule-following with careful state management.

**Core Philosophy:**
- Read requirements with extreme precision
- Model state accurately
- Transform rules into code mechanically
- Handle edge cases explicitly

---

## II. Fundamental Concepts You Must Know

### 2.1 State
**Definition:** The complete snapshot of your system at any moment in time.

**Example:** In a chess game, state includes:
- Position of all pieces
- Whose turn it is
- Castling rights
- En passant possibility

**In Code (Rust):**
```rust
struct GameState {
    board: [[Option<Piece>; 8]; 8],
    current_player: Player,
    move_count: u32,
    castling_rights: CastlingRights,
}
```

### 2.2 Transition
**Definition:** A function that takes current state and produces next state based on rules.

```
State(t) + Action → State(t+1)
```

### 2.3 Invariant
**Definition:** A property that must remain true throughout simulation.

**Example:** In a robot walking on a grid, the invariant might be: "robot position must always be within grid bounds."

### 2.4 Iteration vs Recursion
**Iteration:** Simulate step-by-step in a loop (most common)
**Recursion:** Simulate by recursive state transitions (useful for tree-like simulations)

---

## III. Classification of Simulation Problems

### 3.1 Grid-Based Simulations

**Core Idea:** Simulate movement or changes on a 2D grid.

**Key Patterns:**
- Direction vectors for movement
- Boundary checking
- State tracking per cell

**Example Problem:** Robot Walking on Grid

```rust
// Direction vectors: Right, Down, Left, Up (clockwise)
const DIRECTIONS: [(i32, i32); 4] = [(0, 1), (1, 0), (0, -1), (-1, 0)];

fn simulate_robot(commands: Vec<char>, obstacles: Vec<Vec<i32>>) -> i32 {
    // State: position (x, y), direction index (0-3)
    let mut x = 0;
    let mut y = 0;
    let mut dir = 0; // Initially facing North (up)
    
    // Convert obstacles to HashSet for O(1) lookup
    let obstacle_set: std::collections::HashSet<(i32, i32)> = 
        obstacles.iter().map(|v| (v[0], v[1])).collect();
    
    let mut max_distance = 0;
    
    for command in commands {
        match command {
            'G' => {
                // Try to move forward
                let (dx, dy) = DIRECTIONS[dir];
                let new_x = x + dx;
                let new_y = y + dy;
                
                // Check if obstacle exists
                if !obstacle_set.contains(&(new_x, new_y)) {
                    x = new_x;
                    y = new_y;
                    // Update maximum distance from origin
                    max_distance = max_distance.max(x * x + y * y);
                }
            }
            'L' => {
                // Turn left: decrease direction index (mod 4)
                dir = (dir + 3) % 4; // +3 is same as -1 in mod 4
            }
            'R' => {
                // Turn right: increase direction index
                dir = (dir + 1) % 4;
            }
            _ => {} // Invalid command, ignore
        }
    }
    
    max_distance
}
```

**Go Implementation:**
```go
func simulateRobot(commands []byte, obstacles [][]int) int {
    // Direction vectors
    directions := [][2]int{{0, 1}, {1, 0}, {0, -1}, {-1, 0}}
    
    x, y, dir := 0, 0, 0
    
    // Build obstacle map
    obstacleMap := make(map[[2]int]bool)
    for _, obs := range obstacles {
        obstacleMap[[2]int{obs[0], obs[1]}] = true
    }
    
    maxDist := 0
    
    for _, cmd := range commands {
        switch cmd {
        case 'G':
            newX := x + directions[dir][0]
            newY := y + directions[dir][1]
            
            if !obstacleMap[[2]int{newX, newY}] {
                x, y = newX, newY
                dist := x*x + y*y
                if dist > maxDist {
                    maxDist = dist
                }
            }
        case 'L':
            dir = (dir + 3) % 4
        case 'R':
            dir = (dir + 1) % 4
        }
    }
    
    return maxDist
}
```

**Mental Model:**
1. **State = (position, direction)**
2. **Transition = apply one command**
3. **Invariant = position stays valid (no obstacles)**

---

### 3.2 Time-Based Simulations

**Core Idea:** Simulate events that occur at specific time points.

**Key Techniques:**
- Event queue (priority queue/heap)
- Time pointer advancement
- Event processing

**Example Problem:** Meeting Rooms Simulation

```rust
use std::collections::BinaryHeap;
use std::cmp::Reverse;

fn min_meeting_rooms(intervals: Vec<Vec<i32>>) -> i32 {
    if intervals.is_empty() {
        return 0;
    }
    
    // Sort by start time
    let mut intervals = intervals;
    intervals.sort_by_key(|interval| interval[0]);
    
    // Min-heap tracking end times of ongoing meetings
    let mut heap: BinaryHeap<Reverse<i32>> = BinaryHeap::new();
    
    let mut max_rooms = 0;
    
    for interval in intervals {
        let start = interval[0];
        let end = interval[1];
        
        // Remove all meetings that ended before current start
        while let Some(&Reverse(earliest_end)) = heap.peek() {
            if earliest_end <= start {
                heap.pop();
            } else {
                break;
            }
        }
        
        // Add current meeting's end time
        heap.push(Reverse(end));
        
        // Update maximum concurrent meetings
        max_rooms = max_rooms.max(heap.len());
    }
    
    max_rooms as i32
}
```

**C Implementation:**
```c
#include <stdlib.h>

// Comparison function for qsort
int compare_starts(const void *a, const void *b) {
    int *intervalA = *(int **)a;
    int *intervalB = *(int **)b;
    return intervalA[0] - intervalB[0];
}

int compare_ints(const void *a, const void *b) {
    return (*(int *)a - *(int *)b);
}

int minMeetingRooms(int** intervals, int intervalsSize, int* intervalsColSize) {
    if (intervalsSize == 0) return 0;
    
    // Sort intervals by start time
    qsort(intervals, intervalsSize, sizeof(int*), compare_starts);
    
    // Array to simulate heap (end times)
    int *endTimes = (int *)malloc(intervalsSize * sizeof(int));
    int heapSize = 0;
    int maxRooms = 0;
    
    for (int i = 0; i < intervalsSize; i++) {
        int start = intervals[i][0];
        int end = intervals[i][1];
        
        // Remove meetings that ended
        int writeIdx = 0;
        for (int readIdx = 0; readIdx < heapSize; readIdx++) {
            if (endTimes[readIdx] > start) {
                endTimes[writeIdx++] = endTimes[readIdx];
            }
        }
        heapSize = writeIdx;
        
        // Add current meeting
        endTimes[heapSize++] = end;
        
        // Keep heap sorted (in real implementation, use proper heap)
        qsort(endTimes, heapSize, sizeof(int), compare_ints);
        
        if (heapSize > maxRooms) {
            maxRooms = heapSize;
        }
    }
    
    free(endTimes);
    return maxRooms;
}
```

**Cognitive Model:**
- **Timeline:** Sequence of events ordered by time
- **Active Set:** What's currently "happening"
- **Event:** Transition that changes active set

---

### 3.3 Rule-Based Simulations (Game of Life Pattern)

**Core Idea:** Each entity's next state depends on current state of neighbors.

**Critical Pattern:**
- Compute ALL next states before updating ANY current state
- Use double buffering or separate arrays

**Example Problem:** Conway's Game of Life

```rust
fn game_of_life(board: &mut Vec<Vec<i32>>) {
    let rows = board.len();
    let cols = board[0].len();
    
    // Direction vectors for 8 neighbors
    let directions = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1),
    ];
    
    // Helper: count live neighbors
    let count_neighbors = |r: usize, c: usize| -> i32 {
        let mut count = 0;
        for &(dr, dc) in &directions {
            let nr = r as i32 + dr;
            let nc = c as i32 + dc;
            
            // Boundary check
            if nr >= 0 && nr < rows as i32 && nc >= 0 && nc < cols as i32 {
                // Extract original state (ignore encoding)
                count += board[nr as usize][nc as usize] & 1;
            }
        }
        count
    };
    
    // Phase 1: Encode next state in second bit
    for r in 0..rows {
        for c in 0..cols {
            let neighbors = count_neighbors(r, c);
            let current = board[r][c] & 1; // Current state
            
            // Apply rules
            let next = if current == 1 {
                // Live cell
                if neighbors == 2 || neighbors == 3 { 1 } else { 0 }
            } else {
                // Dead cell
                if neighbors == 3 { 1 } else { 0 }
            };
            
            // Encode: bit 0 = current, bit 1 = next
            board[r][c] |= next << 1;
        }
    }
    
    // Phase 2: Extract next state
    for r in 0..rows {
        for c in 0..cols {
            board[r][c] >>= 1; // Shift next state to current
        }
    }
}
```

**Go Implementation with Clean Separation:**
```go
func gameOfLife(board [][]int) {
    rows, cols := len(board), len(board[0])
    
    // Create next state board
    next := make([][]int, rows)
    for i := range next {
        next[i] = make([]int, cols)
    }
    
    directions := [8][2]int{
        {-1, -1}, {-1, 0}, {-1, 1},
        {0, -1},           {0, 1},
        {1, -1},  {1, 0},  {1, 1},
    }
    
    countNeighbors := func(r, c int) int {
        count := 0
        for _, d := range directions {
            nr, nc := r+d[0], c+d[1]
            if nr >= 0 && nr < rows && nc >= 0 && nc < cols {
                count += board[nr][nc]
            }
        }
        return count
    }
    
    // Compute next state
    for r := 0; r < rows; r++ {
        for c := 0; c < cols; c++ {
            neighbors := countNeighbors(r, c)
            
            if board[r][c] == 1 {
                // Live cell: survives with 2-3 neighbors
                if neighbors == 2 || neighbors == 3 {
                    next[r][c] = 1
                }
            } else {
                // Dead cell: becomes alive with exactly 3 neighbors
                if neighbors == 3 {
                    next[r][c] = 1
                }
            }
        }
    }
    
    // Copy back
    for r := 0; r < rows; r++ {
        copy(board[r], next[r])
    }
}
```

**Deep Insight:**
The challenge isn't the rules—it's **synchronization**. All cells must update simultaneously based on the *previous* state, not the *partially updated* state.

**Solutions:**
1. **Double buffering** (two arrays)
2. **Bit manipulation** (encode old and new in same cell)
3. **Temporary state** (mark changes, apply later)

---

### 3.4 Queue-Based Simulations (BFS-like)

**Core Idea:** Process entities in order, where processing one entity may add more entities.

**Example Problem:** Rotting Oranges

```rust
use std::collections::VecDeque;

fn oranges_rotting(mut grid: Vec<Vec<i32>>) -> i32 {
    let rows = grid.len();
    let cols = grid[0].len();
    
    let mut queue: VecDeque<(usize, usize, i32)> = VecDeque::new();
    let mut fresh_count = 0;
    
    // Phase 1: Find all initially rotten oranges and count fresh
    for r in 0..rows {
        for c in 0..cols {
            if grid[r][c] == 2 {
                queue.push_back((r, c, 0)); // (row, col, time)
            } else if grid[r][c] == 1 {
                fresh_count += 1;
            }
        }
    }
    
    // Edge case: no fresh oranges
    if fresh_count == 0 {
        return 0;
    }
    
    let directions = [(0, 1), (1, 0), (0, -1), (-1, 0)];
    let mut max_time = 0;
    
    // Phase 2: BFS simulation
    while let Some((r, c, time)) = queue.pop_front() {
        for &(dr, dc) in &directions {
            let nr = r as i32 + dr;
            let nc = c as i32 + dc;
            
            if nr >= 0 && nr < rows as i32 && nc >= 0 && nc < cols as i32 {
                let nr = nr as usize;
                let nc = nc as usize;
                
                if grid[nr][nc] == 1 {
                    grid[nr][nc] = 2; // Mark as rotten
                    fresh_count -= 1;
                    let new_time = time + 1;
                    max_time = max_time.max(new_time);
                    queue.push_back((nr, nc, new_time));
                }
            }
        }
    }
    
    if fresh_count == 0 {
        max_time
    } else {
        -1 // Some oranges can't rot
    }
}
```

**Mental Model:**
- **Wave Propagation:** Rotting spreads in waves (BFS levels)
- **State Transition:** Fresh → Rotten (irreversible)
- **Time Tracking:** Each wave = +1 minute

---

## IV. Advanced Simulation Patterns

### 4.1 Circular Buffer Simulation

**Use Case:** Limited size queue where oldest elements get overwritten.

**Example Problem:** Design Circular Queue

```rust
struct MyCircularQueue {
    buffer: Vec<i32>,
    head: usize,  // Points to front element
    tail: usize,  // Points to next insert position
    size: usize,  // Current number of elements
    capacity: usize,
}

impl MyCircularQueue {
    fn new(k: i32) -> Self {
        MyCircularQueue {
            buffer: vec![0; k as usize],
            head: 0,
            tail: 0,
            size: 0,
            capacity: k as usize,
        }
    }
    
    fn en_queue(&mut self, value: i32) -> bool {
        if self.is_full() {
            return false;
        }
        
        self.buffer[self.tail] = value;
        self.tail = (self.tail + 1) % self.capacity;
        self.size += 1;
        true
    }
    
    fn de_queue(&mut self) -> bool {
        if self.is_empty() {
            return false;
        }
        
        self.head = (self.head + 1) % self.capacity;
        self.size -= 1;
        true
    }
    
    fn front(&self) -> i32 {
        if self.is_empty() {
            -1
        } else {
            self.buffer[self.head]
        }
    }
    
    fn rear(&self) -> i32 {
        if self.is_empty() {
            -1
        } else {
            // Rear is one position before tail
            let rear_idx = (self.tail + self.capacity - 1) % self.capacity;
            self.buffer[rear_idx]
        }
    }
    
    fn is_empty(&self) -> bool {
        self.size == 0
    }
    
    fn is_full(&self) -> bool {
        self.size == self.capacity
    }
}
```

**Key Insight:** Modulo arithmetic enables wrap-around without shifting elements.

---

### 4.2 Multi-Agent Simulation

**Use Case:** Multiple entities with independent states but shared environment.

**Example Problem:** Car Fleet

```rust
fn car_fleet(target: i32, position: Vec<i32>, speed: Vec<i32>) -> i32 {
    let n = position.len();
    
    // Pair up positions with speeds and sort by position (closest to target first)
    let mut cars: Vec<(i32, f64)> = position
        .iter()
        .zip(speed.iter())
        .map(|(&pos, &spd)| {
            // Calculate time to reach target
            let time = (target - pos) as f64 / spd as f64;
            (pos, time)
        })
        .collect();
    
    // Sort by position (descending - closest to target first)
    cars.sort_by(|a, b| b.0.cmp(&a.0));
    
    let mut fleets = 0;
    let mut prev_time = 0.0;
    
    // Simulate: cars ahead slow down following cars
    for (_, time) in cars {
        if time > prev_time {
            // This car forms a new fleet (can't catch up)
            fleets += 1;
            prev_time = time;
        }
        // Else: this car catches up and joins previous fleet
    }
    
    fleets
}
```

**Cognitive Principle:** When agents interact, process them in **logical order** (here: by position).

---

### 4.3 State Machine Simulation

**Use Case:** System with discrete states and well-defined transitions.

**Example Problem:** String Parser/Validator

```rust
fn is_number(s: String) -> bool {
    let s = s.trim();
    if s.is_empty() {
        return false;
    }
    
    #[derive(Debug, PartialEq)]
    enum State {
        Start,
        Sign,
        Integer,
        Point,
        Fraction,
        Exponent,
        ExpSign,
        ExpNumber,
    }
    
    let mut state = State::Start;
    
    for ch in s.chars() {
        state = match (state, ch) {
            // From Start
            (State::Start, '+' | '-') => State::Sign,
            (State::Start, '0'..='9') => State::Integer,
            (State::Start, '.') => State::Point,
            
            // From Sign
            (State::Sign, '0'..='9') => State::Integer,
            (State::Sign, '.') => State::Point,
            
            // From Integer
            (State::Integer, '0'..='9') => State::Integer,
            (State::Integer, '.') => State::Fraction,
            (State::Integer, 'e' | 'E') => State::Exponent,
            
            // From Point
            (State::Point, '0'..='9') => State::Fraction,
            
            // From Fraction
            (State::Fraction, '0'..='9') => State::Fraction,
            (State::Fraction, 'e' | 'E') => State::Exponent,
            
            // From Exponent
            (State::Exponent, '+' | '-') => State::ExpSign,
            (State::Exponent, '0'..='9') => State::ExpNumber,
            
            // From ExpSign
            (State::ExpSign, '0'..='9') => State::ExpNumber,
            
            // From ExpNumber
            (State::ExpNumber, '0'..='9') => State::ExpNumber,
            
            // Invalid transition
            _ => return false,
        };
    }
    
    // Valid ending states
    matches!(state, State::Integer | State::Fraction | State::ExpNumber)
}
```

**Go State Machine:**
```go
func isNumber(s string) bool {
    s = strings.TrimSpace(s)
    if len(s) == 0 {
        return false
    }
    
    const (
        START = iota
        SIGN
        INTEGER
        POINT
        FRACTION
        EXPONENT
        EXPSIGN
        EXPNUMBER
    )
    
    state := START
    
    for _, ch := range s {
        switch state {
        case START:
            if ch == '+' || ch == '-' {
                state = SIGN
            } else if ch >= '0' && ch <= '9' {
                state = INTEGER
            } else if ch == '.' {
                state = POINT
            } else {
                return false
            }
        case SIGN:
            if ch >= '0' && ch <= '9' {
                state = INTEGER
            } else if ch == '.' {
                state = POINT
            } else {
                return false
            }
        case INTEGER:
            if ch >= '0' && ch <= '9' {
                state = INTEGER
            } else if ch == '.' {
                state = FRACTION
            } else if ch == 'e' || ch == 'E' {
                state = EXPONENT
            } else {
                return false
            }
        case POINT:
            if ch >= '0' && ch <= '9' {
                state = FRACTION
            } else {
                return false
            }
        case FRACTION:
            if ch >= '0' && ch <= '9' {
                state = FRACTION
            } else if ch == 'e' || ch == 'E' {
                state = EXPONENT
            } else {
                return false
            }
        case EXPONENT:
            if ch == '+' || ch == '-' {
                state = EXPSIGN
            } else if ch >= '0' && ch <= '9' {
                state = EXPNUMBER
            } else {
                return false
            }
        case EXPSIGN:
            if ch >= '0' && ch <= '9' {
                state = EXPNUMBER
            } else {
                return false
            }
        case EXPNUMBER:
            if ch >= '0' && ch <= '9' {
                state = EXPNUMBER
            } else {
                return false
            }
        }
    }
    
    return state == INTEGER || state == FRACTION || state == EXPNUMBER
}
```

**Mental Framework:**
```
State Machine = (States, Alphabet, Transition Function, Start State, Accept States)

- States: All possible conditions
- Alphabet: All possible inputs
- Transition: (State, Input) → State
- Start: Initial state
- Accept: Valid ending states
```

---

## V. Common Pitfalls & Debugging Strategies

### 5.1 Off-by-One Errors

**Problem:** Incorrect loop bounds or array indexing.

**Example:**
```rust
// WRONG: Processes n-1 elements
for i in 0..n-1 {
    process(arr[i]);
}

// CORRECT: Processes n elements
for i in 0..n {
    process(arr[i]);
}
```

**Prevention:**
- Use `.len()` or `.iter()` when possible
- Test with arrays of size 1, 2, 3
- Verify first and last iterations manually

### 5.2 Simultaneous Update Issues

**Problem:** Updating state while reading it (Game of Life mistake).

**Solution:**
```rust
// WRONG: Updates affect subsequent reads
for r in 0..rows {
    for c in 0..cols {
        let neighbors = count_neighbors(board, r, c);
        board[r][c] = apply_rule(board[r][c], neighbors); // Corrupts future counts!
    }
}

// CORRECT: Separate read and write phases
let next = compute_next_state(&board);
board = next;
```

### 5.3 Boundary Conditions

**Checklist:**
- Empty input (n=0)
- Single element (n=1)
- All same values
- Grid edges (first/last row/column)
- Negative indices after arithmetic

**Rust Safety Pattern:**
```rust
// Check bounds explicitly
if nr >= 0 && nr < rows as i32 && nc >= 0 && nc < cols as i32 {
    let nr = nr as usize;
    let nc = nc as usize;
    // Safe to access grid[nr][nc]
}

// Or use checked arithmetic
if let Some(nr) = r.checked_add(dr) {
    if nr < rows {
        // Safe
    }
}
```

---

## VI. Optimization Techniques

### 6.1 Precomputation

**Principle:** Calculate invariant data once before simulation.

**Example:**
```rust
// Instead of recomputing in every iteration
for step in 0..n {
    let sqrt_step = (step as f64).sqrt(); // SLOW
    process(sqrt_step);
}

// Precompute
let sqrt_values: Vec<f64> = (0..n).map(|s| (s as f64).sqrt()).collect();
for step in 0..n {
    process(sqrt_values[step]); // FAST
}
```

### 6.2 Early Termination

**Principle:** Stop simulation when outcome is determined.

**Example:**
```rust
// Check if simulation can end early
while !queue.is_empty() {
    if fresh_count == 0 {
        return current_time; // Early exit
    }
    // ... rest of simulation
}
```

### 6.3 Data Structure Selection

| Use Case | Data Structure | Why |
|----------|---------------|-----|
| Fast lookup | `HashSet`, `HashMap` | O(1) contains/get |
| Maintain order | `Vec`, `VecDeque` | Indexed access |
| Priority | `BinaryHeap` | O(log n) extract-min |
| Both ends | `VecDeque` | O(1) push/pop both ends |

---

## VII. Practice Progression Path

### Level 1: Basic Simulation (Foundation)
1. Spiral Matrix (Grid traversal)
2. Robot Return to Origin (State tracking)
3. Valid Parentheses (Stack simulation)

### Level 2: Time/Event Simulation
1. Meeting Rooms II (Event processing)
2. Task Scheduler (Greedy simulation)
3. Design Hit Counter (Time window)

### Level 3: Multi-State Simulation
1. Game of Life (Synchronous update)
2. Rotting Oranges (BFS simulation)
3. Snakes and Ladders (Graph + simulation)

### Level 4: Complex State Machines
1. Design In-Memory File System (Trie + simulation)
2. LRU Cache (Doubly linked list + hashmap)
3. Robot Room Cleaner (Backtracking + simulation)

---

## VIII. Final Mental Models

### The Simulation Checklist

```
□ Define state representation clearly
□ Identify all state transitions
□ Determine update order (sequential vs parallel)
□ Handle boundary conditions
□ Check for early termination opportunities
□ Verify invariants after each step
□ Test with minimal cases (n=0, n=1, n=2)
```

### Complexity Analysis Framework

**Time:** Usually O(steps × work_per_step)
- Steps: Total iterations/rounds
- Work per step: Operations in one iteration

**Space:** O(state_size)
- State size: Memory needed to represent current configuration

**Example (Rotting Oranges):**
- Time: O(rows × cols) — Each cell processed once
- Space: O(rows × cols) — Queue can hold all cells

---

## IX. Rust-Specific Idioms

### Pattern Matching for State

```rust
enum Direction { North, East, South, West }

let new_dir = match (current_dir, turn) {
    (Direction::North, 'L') => Direction::West,
    (Direction::North, 'R') => Direction::East,
    (Direction::East, 'L') => Direction::North,
    (Direction::East, 'R') => Direction::South,
    (Direction::South, 'L') => Direction::East,
    (Direction::South, 'R') => Direction::West,
    (Direction::West, 'L') => Direction::South,
    (Direction::West, 'R') => Direction::North,
    _ => current_dir,
};
```

### Iterators for Simulation

```rust
// Elegant range-based simulation
let result = (0..steps)
    .scan(initial_state, |state, _| {
        *state = transition(*state);
        Some(*state)
    })
    .last()
    .unwrap();
```

---

This guide covers the essential patterns for 95% of simulation problems. The key is **precise rule-following** combined with **careful state management**. Master these patterns, and simulation problems become mechanical exercises rather than puzzles.

Your monk-like discipline will serve you well here—simulation rewards systematic thinking and attention to detail over cleverness.

# The Complete Simulation Mastery Guide
## From First Principles to Top 1% Mastery

---

## **Part I: Understanding Simulation from Ground Zero**

### **What is Simulation?**

**Simulation** means *following instructions step-by-step exactly as described*, mimicking a real-world process or system behavior in code.

Think of it like this:
- You're given a set of **rules** (like a board game manual)
- You must **execute** those rules precisely
- You track **state changes** at each step
- You produce an **output** based on the final state

**Real-world analogy**: Imagine you're a robot executing a recipe. You don't optimize or shortcut — you follow each instruction literally, maintaining the kitchen's state (ingredients, temperature, time) until complete.

---

### **Why Simulation Problems Exist**

Simulation problems test your ability to:

1. **Translate natural language** → precise logic
2. **Manage state** across multiple steps
3. **Handle edge cases** without over-complicating
4. **Write bug-free code** under detailed specifications
5. **Model systems** accurately

These skills are critical in:
- Game development (physics engines)
- Financial modeling (market simulations)
- Systems programming (process schedulers)
- Scientific computing (molecular dynamics)

---

### **Core Mental Model**

```
┌─────────────────────────────────────────┐
│         SIMULATION FRAMEWORK            │
├─────────────────────────────────────────┤
│                                         │
│  1. READ RULES (understand mechanics)   │
│           ↓                             │
│  2. MODEL STATE (what changes?)         │
│           ↓                             │
│  3. SIMULATE STEPS (execute rules)      │
│           ↓                             │
│  4. TRACK CHANGES (update state)        │
│           ↓                             │
│  5. TERMINATE (stopping condition)      │
│           ↓                             │
│  6. EXTRACT RESULT (final state)        │
│                                         │
└─────────────────────────────────────────┘
```

---

## **Part II: Fundamental Concepts**

### **Concept 1: State Representation**

**State** = all information needed to describe the system at a given moment.

**Example**: Simulating a robot on a grid
- State = `(x_position, y_position, direction_facing)`

**How to choose state representation:**

```
Decision Tree:
├─ What changes over time?
│  └─ Include in state
├─ What determines next step?
│  └─ Include in state
├─ What's needed for final answer?
│  └─ Include in state
└─ Everything else?
   └─ Discard (keep it minimal)
```

---

### **Concept 2: Time Steps (Discrete vs Continuous)**

**Discrete time**: Events happen at specific moments (tick 1, tick 2, ...)
- Example: Snake game moves one cell per turn

**Continuous time**: Events can happen at any moment
- Usually discretized in simulations (sample at intervals)

Most LeetCode simulations use **discrete time steps**.

---

### **Concept 3: Rules & Transitions**

**Transition Function**: `new_state = f(current_state, input)`

This is the heart of simulation. You must:
1. Identify all possible transitions
2. Determine transition conditions
3. Apply transitions in correct order

**Example**: Traffic light
```
current: RED
rule: "after 30 seconds, turn GREEN"
next: GREEN
```

---

### **Concept 4: Boundary Conditions**

**Boundaries** define limits of your simulation space.

Types:
1. **Hard boundaries**: Can't cross (walls)
2. **Wrapping boundaries**: Exit one side, enter other (Pac-Man)
3. **Reflecting boundaries**: Bounce back

---

## **Part III: Classification of Simulation Problems**

### **Type 1: Grid/Matrix Simulation**

Moving entities on a 2D grid following rules.

**Key patterns:**
- Direction vectors
- Boundary checking
- State grids (visited, obstacles)

**Example Problem**: Robot Walking in Grid

```
Problem: Robot starts at (0,0). Given moves "RRULDL":
- R: right (+1, 0)
- L: left (-1, 0)  
- U: up (0, +1)
- D: down (0, -1)
Return final position.
```

**Step-by-step thinking:**

```
1. State: (x, y) coordinates
2. Rules: Each character changes position
3. Steps: Process each character sequentially
4. Termination: After all moves
5. Result: Final (x, y)
```

**Rust Implementation (Idiomatic):**

```rust
/// Returns final position after executing moves
/// 
/// Time: O(n) where n = moves.len()
/// Space: O(1) - only storing coordinates
pub fn robot_position(moves: &str) -> (i32, i32) {
    let mut x = 0;
    let mut y = 0;
    
    for move_char in moves.chars() {
        match move_char {
            'R' => x += 1,
            'L' => x -= 1,
            'U' => y += 1,
            'D' => y -= 1,
            _ => {} // Invalid moves ignored
        }
    }
    
    (x, y)
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_robot_position() {
        assert_eq!(robot_position("RRULDL"), (0, 0));
        assert_eq!(robot_position("RRUUDL"), (1, 2));
    }
}
```

**Go Implementation:**

```go
// RobotPosition returns final coordinates after moves
// Time: O(n), Space: O(1)
func RobotPosition(moves string) (int, int) {
    x, y := 0, 0
    
    for _, move := range moves {
        switch move {
        case 'R':
            x++
        case 'L':
            x--
        case 'U':
            y++
        case 'D':
            y--
        }
    }
    
    return x, y
}
```

**C Implementation:**

```c
#include <stdio.h>

typedef struct {
    int x;
    int y;
} Position;

// Returns final position after moves
// Time: O(n), Space: O(1)
Position robot_position(const char* moves) {
    Position pos = {0, 0};
    
    while (*moves != '\0') {
        switch (*moves) {
            case 'R': pos.x++; break;
            case 'L': pos.x--; break;
            case 'U': pos.y++; break;
            case 'D': pos.y--; break;
        }
        moves++;
    }
    
    return pos;
}
```

---

### **Type 2: Circular/Rotation Simulation**

Simulating rotation, circular arrays, or cyclic processes.

**Key concept**: **Modulo arithmetic** for wrapping

**Modulo explanation**: 
- `a % b` gives remainder when dividing a by b
- Used to "wrap around": index 5 in array of size 3 → index 2 (5 % 3 = 2)

**Example Problem**: Rotate Array

```
Problem: Rotate array [1,2,3,4,5] right by 2 steps
Result: [4,5,1,2,3]
```

**Thinking process:**

```
Brute force approach:
├─ Rotate one step at a time (k times)
├─ Time: O(n*k), Space: O(1)
└─ Too slow for large k

Optimized approach:
├─ Observe: rotating n times = no change
├─ Only need to rotate k % n times
├─ Use reversal trick:
│  1. Reverse entire array
│  2. Reverse first k elements
│  3. Reverse remaining elements
└─ Time: O(n), Space: O(1)
```

**Rust Implementation (Optimized):**

```rust
/// Rotates array right by k steps in-place
/// 
/// Algorithm: Three-reversal method
/// Time: O(n), Space: O(1)
pub fn rotate(nums: &mut Vec<i32>, k: usize) {
    let n = nums.len();
    if n == 0 {
        return;
    }
    
    // Normalize k to avoid unnecessary full rotations
    let k = k % n;
    if k == 0 {
        return;
    }
    
    // Helper to reverse a slice in-place
    fn reverse(arr: &mut [i32]) {
        let mut left = 0;
        let mut right = arr.len() - 1;
        
        while left < right {
            arr.swap(left, right);
            left += 1;
            right -= 1;
        }
    }
    
    // Three reversals
    reverse(nums);           // Reverse all
    reverse(&mut nums[..k]); // Reverse first k
    reverse(&mut nums[k..]); // Reverse rest
}
```

**Why this works (Mathematical insight):**

```
Original: [1, 2, 3, 4, 5], k=2
Goal:     [4, 5, 1, 2, 3]

Step 1: Reverse all
[5, 4, 3, 2, 1]

Step 2: Reverse first k=2
[4, 5, 3, 2, 1]

Step 3: Reverse remaining
[4, 5, 1, 2, 3] ✓

Intuition: We're placing last k elements first,
but they're in wrong order, so we fix their order.
```

---

### **Type 3: String Manipulation Simulation**

Processing strings character-by-character with rules.

**Key patterns:**
- Stack for nested operations
- Two pointers for comparison
- StringBuilder for efficiency

**Example Problem**: Decode String

```
Problem: "3[a2[c]]" → "accaccacc"
Rules:
- k[string] means repeat string k times
- Can be nested
```

**Thinking process:**

```
Need to handle:
1. Numbers (repeat counts)
2. Characters (content to repeat)
3. Brackets (nesting structure)

Data structure choice:
├─ Stack? ✓ Good for nesting
├─ Recursion? ✓ Good for nesting
└─ We'll use stack (more explicit control)

Algorithm:
1. Scan left to right
2. Push numbers and strings onto stack
3. When seeing ']', pop until '[', repeat, push back
```

**Rust Implementation:**

```rust
/// Decodes encoded string with nested repetitions
/// 
/// Time: O(maxK * n) where maxK is max repeat count
/// Space: O(n) for stack
pub fn decode_string(s: String) -> String {
    let mut stack: Vec<String> = Vec::new();
    let mut current_num = 0;
    let mut current_str = String::new();
    
    for ch in s.chars() {
        match ch {
            '0'..='9' => {
                // Build multi-digit number
                current_num = current_num * 10 + ch.to_digit(10).unwrap() as usize;
            }
            '[' => {
                // Push current state to stack
                stack.push(current_num.to_string());
                stack.push(current_str.clone());
                
                // Reset for new level
                current_num = 0;
                current_str.clear();
            }
            ']' => {
                // Pop previous string and repeat count
                let prev_str = stack.pop().unwrap();
                let repeat_count = stack.pop().unwrap().parse::<usize>().unwrap();
                
                // Repeat current string and prepend previous
                current_str = prev_str + &current_str.repeat(repeat_count);
            }
            _ => {
                // Regular character
                current_str.push(ch);
            }
        }
    }
    
    current_str
}
```

**Go Implementation:**

```go
func decodeString(s string) string {
    stack := []string{}
    currentNum := 0
    currentStr := ""
    
    for _, ch := range s {
        switch {
        case ch >= '0' && ch <= '9':
            currentNum = currentNum*10 + int(ch-'0')
            
        case ch == '[':
            // Push state
            stack = append(stack, fmt.Sprintf("%d", currentNum))
            stack = append(stack, currentStr)
            currentNum = 0
            currentStr = ""
            
        case ch == ']':
            // Pop and decode
            prevStr := stack[len(stack)-1]
            stack = stack[:len(stack)-1]
            repeatCount, _ := strconv.Atoi(stack[len(stack)-1])
            stack = stack[:len(stack)-1]
            
            currentStr = prevStr + strings.Repeat(currentStr, repeatCount)
            
        default:
            currentStr += string(ch)
        }
    }
    
    return currentStr
}
```

---

### **Type 4: Game Simulation**

Simulating game rules, turns, player actions.

**Key patterns:**
- Turn-based state updates
- Win condition checking
- Player alternation

**Example Problem**: Tic-Tac-Toe Winner Detection

```
Problem: Given moves, determine winner
moves = [[0,0],[2,0],[1,1],[2,1],[2,2]]
Player A: moves[0,2,4] → X
Player B: moves[1,3] → O
```

**State representation:**

```rust
#[derive(Debug, Clone, Copy, PartialEq)]
enum Cell {
    Empty,
    X,
    O,
}

type Board = [[Cell; 3]; 3];
```

**Complete Implementation:**

```rust
#[derive(Debug, PartialEq)]
enum GameResult {
    A,      // Player A wins
    B,      // Player B wins
    Draw,   // Game is draw
    Pending // Game not finished
}

pub fn tic_tac_toe(moves: Vec<Vec<i32>>) -> String {
    let mut board = [[Cell::Empty; 3]; 3];
    
    // Simulate moves
    for (i, move_pos) in moves.iter().enumerate() {
        let row = move_pos[0] as usize;
        let col = move_pos[1] as usize;
        
        // Alternate players (even index = A, odd = B)
        board[row][col] = if i % 2 == 0 { Cell::X } else { Cell::O };
    }
    
    // Check winner
    match check_winner(&board) {
        Some(Cell::X) => "A".to_string(),
        Some(Cell::O) => "B".to_string(),
        None => {
            if moves.len() == 9 {
                "Draw".to_string()
            } else {
                "Pending".to_string()
            }
        }
    }
}

fn check_winner(board: &Board) -> Option<Cell> {
    // Check rows
    for row in 0..3 {
        if board[row][0] != Cell::Empty &&
           board[row][0] == board[row][1] &&
           board[row][1] == board[row][2] {
            return Some(board[row][0]);
        }
    }
    
    // Check columns
    for col in 0..3 {
        if board[0][col] != Cell::Empty &&
           board[0][col] == board[1][col] &&
           board[1][col] == board[2][col] {
            return Some(board[0][col]);
        }
    }
    
    // Check diagonals
    if board[1][1] != Cell::Empty {
        // Main diagonal
        if board[0][0] == board[1][1] && board[1][1] == board[2][2] {
            return Some(board[1][1]);
        }
        // Anti-diagonal
        if board[0][2] == board[1][1] && board[1][1] == board[2][0] {
            return Some(board[1][1]);
        }
    }
    
    None
}
```

---

## **Part IV: Advanced Simulation Patterns**

### **Pattern 1: Multi-Agent Simulation**

Multiple entities interacting according to rules.

**Example**: Robot Room Cleaner

```
Problem: Robot in room with obstacles
- Can move forward
- Can turn left/right
- Must clean all reachable cells
- Can't see whole room (local view only)
```

**Key insight**: Need to track what robot has visited while exploring unknown space.

**Algorithm**: DFS with backtracking

```rust
use std::collections::HashSet;

pub struct Robot {
    // Mock interface - in real problem, these are provided
}

impl Robot {
    fn move_forward(&mut self) -> bool {
        // Returns true if moved, false if obstacle
        unimplemented!()
    }
    
    fn turn_left(&mut self) {
        unimplemented!()
    }
    
    fn turn_right(&mut self) {
        unimplemented!()
    }
    
    fn clean(&mut self) {
        unimplemented!()
    }
}

pub fn clean_room(robot: &mut Robot) {
    let mut visited = HashSet::new();
    // Directions: up, right, down, left
    let dirs = [(0, 1), (1, 0), (0, -1), (-1, 0)];
    
    fn dfs(
        robot: &mut Robot,
        x: i32,
        y: i32,
        dir: usize,
        visited: &mut HashSet<(i32, i32)>,
        dirs: &[(i32, i32); 4]
    ) {
        visited.insert((x, y));
        robot.clean();
        
        // Try all 4 directions
        for i in 0..4 {
            let new_dir = (dir + i) % 4;
            let (dx, dy) = dirs[new_dir];
            let (nx, ny) = (x + dx, y + dy);
            
            if !visited.contains(&(nx, ny)) && robot.move_forward() {
                dfs(robot, nx, ny, new_dir, visited, dirs);
                // Backtrack: go back and face same direction
                go_back(robot);
            }
            
            robot.turn_right();
        }
    }
    
    fn go_back(robot: &mut Robot) {
        robot.turn_right();
        robot.turn_right();
        robot.move_forward();
        robot.turn_right();
        robot.turn_right();
    }
    
    dfs(robot, 0, 0, 0, &mut visited, &dirs);
}
```

**Cognitive principle**: **Exploration-Exploitation Tradeoff**
- Must explore unknown areas (DFS)
- Must remember what's explored (HashSet)
- Must be able to backtrack (return to known state)

---

### **Pattern 2: Event-Driven Simulation**

Processing events in time order.

**Example**: Meeting Rooms II (Minimum Conference Rooms)

```
Problem: intervals = [[0,30],[5,10],[15,20]]
What's minimum rooms needed?
```

**Key insight**: Track room occupancy over time using events.

**Algorithm**:
1. Create START and END events for each meeting
2. Sort events by time
3. Track active meetings

**Rust Implementation:**

```rust
use std::cmp::Ordering;

#[derive(Debug, Clone, Copy)]
enum EventType {
    Start,
    End,
}

#[derive(Debug, Clone, Copy)]
struct Event {
    time: i32,
    event_type: EventType,
}

pub fn min_meeting_rooms(intervals: Vec<Vec<i32>>) -> i32 {
    let mut events = Vec::new();
    
    // Create events
    for interval in intervals {
        events.push(Event {
            time: interval[0],
            event_type: EventType::Start,
        });
        events.push(Event {
            time: interval[1],
            event_type: EventType::End,
        });
    }
    
    // Sort events
    // Critical: if same time, END before START (room becomes free first)
    events.sort_by(|a, b| {
        match a.time.cmp(&b.time) {
            Ordering::Equal => {
                match (a.event_type, b.event_type) {
                    (EventType::End, EventType::Start) => Ordering::Less,
                    (EventType::Start, EventType::End) => Ordering::Greater,
                    _ => Ordering::Equal,
                }
            }
            other => other,
        }
    });
    
    let mut current_rooms = 0;
    let mut max_rooms = 0;
    
    // Process events
    for event in events {
        match event.event_type {
            EventType::Start => current_rooms += 1,
            EventType::End => current_rooms -= 1,
        }
        max_rooms = max_rooms.max(current_rooms);
    }
    
    max_rooms
}
```

**Why END before START matters:**

```
If meeting ends at time 10 and another starts at 10:
├─ Same room can be used
├─ If we process START first: count=2 (wrong!)
└─ If we process END first: count=1 (correct!)
```

---

### **Pattern 3: Lazy Propagation Simulation**

Don't compute until needed (optimization technique).

**Example**: Range Addition

```
Problem: Array of zeros, apply updates:
updates = [[1,3,2], [2,4,3]]
meaning: add 2 to indices [1,3], add 3 to indices [2,4]
```

**Brute force**: Update each index → O(k*n) where k = updates

**Optimized**: Use difference array (lazy propagation)

**Difference Array Explanation**:
```
If we have: [1, 3, 5, 7]
Difference: [1, 2, 2, 2] (each element = arr[i] - arr[i-1])

To add val to range [L, R]:
├─ diff[L] += val (start of range)
└─ diff[R+1] -= val (end of range)

Then reconstruct with prefix sum!
```

**Rust Implementation:**

```rust
pub fn get_modified_array(length: i32, updates: Vec<Vec<i32>>) -> Vec<i32> {
    let n = length as usize;
    let mut diff = vec![0; n + 1]; // Extra space for boundary
    
    // Apply all updates to difference array
    for update in updates {
        let start = update[0] as usize;
        let end = update[1] as usize;
        let val = update[2];
        
        diff[start] += val;
        diff[end + 1] -= val;
    }
    
    // Reconstruct original array via prefix sum
    let mut result = vec![0; n];
    let mut current = 0;
    
    for i in 0..n {
        current += diff[i];
        result[i] = current;
    }
    
    result
}
```

**Time complexity**: O(k + n) instead of O(k*n)

---

## **Part V: Performance Optimization Strategies**

### **Strategy 1: State Compression**

Reduce memory by encoding state efficiently.

**Example**: Instead of 2D boolean array, use bitmask:

```rust
// Instead of: Vec<Vec<bool>> (64 bytes per row)
// Use: u64 (8 bytes for 64 columns)

pub struct CompressedGrid {
    rows: Vec<u64>, // Each u64 represents one row
}

impl CompressedGrid {
    pub fn new(height: usize) -> Self {
        Self {
            rows: vec![0; height],
        }
    }
    
    pub fn set(&mut self, row: usize, col: usize) {
        self.rows[row] |= 1 << col;
    }
    
    pub fn get(&self, row: usize, col: usize) -> bool {
        (self.rows[row] & (1 << col)) != 0
    }
    
    pub fn toggle(&mut self, row: usize, col: usize) {
        self.rows[row] ^= 1 << col;
    }
}
```

**Memory savings**: 8x reduction for sparse grids!

---

### **Strategy 2: Early Termination**

Stop simulation when answer is determined.

```rust
// Example: Checking if pattern exists
pub fn pattern_found(grid: &Vec<Vec<char>>, pattern: &str) -> bool {
    for row in grid {
        for col in 0..row.len() {
            if matches_pattern(grid, row, col, pattern) {
                return true; // Early termination!
            }
        }
    }
    false
}
```

---

### **Strategy 3: Memoization**

Cache repeated computations (when subproblems overlap).

**Example**: Simulation with repeated states

```rust
use std::collections::HashMap;

type State = (i32, i32, i32);

pub fn simulate_with_memo(
    initial: State,
    steps: usize
) -> i32 {
    let mut memo: HashMap<State, i32> = HashMap::new();
    simulate_helper(initial, steps, &mut memo)
}

fn simulate_helper(
    state: State,
    remaining: usize,
    memo: &mut HashMap<State, i32>
) -> i32 {
    if remaining == 0 {
        return compute_result(state);
    }
    
    // Check cache
    if let Some(&result) = memo.get(&state) {
        return result;
    }
    
    // Compute new state
    let next = transition(state);
    let result = simulate_helper(next, remaining - 1, memo);
    
    // Cache result
    memo.insert(state, result);
    result
}

fn transition(state: State) -> State {
    // State transition logic
    state // placeholder
}

fn compute_result(state: State) -> i32 {
    // Result computation
    state.0 // placeholder
}
```

---

## **Part VI: Common Pitfalls & Debugging**

### **Pitfall 1: Off-by-One Errors**

```rust
// ❌ WRONG: Misses last element
for i in 0..arr.len() - 1 {
    process(arr[i]);
}

// ✓ CORRECT
for i in 0..arr.len() {
    process(arr[i]);
}

// ❌ WRONG: Array access out of bounds
if i < arr.len() - 1 {
    next = arr[i + 1]; // Fails when i == len-1
}

// ✓ CORRECT
if i + 1 < arr.len() {
    next = arr[i + 1];
}
```

---

### **Pitfall 2: Mutating While Iterating**

```rust
// ❌ WRONG: Can't modify while iterating
for item in vec.iter() {
    vec.push(new_item); // Compile error!
}

// ✓ CORRECT: Collect changes, apply later
let changes: Vec<_> = vec.iter()
    .map(|item| compute_new(*item))
    .collect();
vec.extend(changes);
```

---

### **Pitfall 3: Integer Overflow**

```rust
// ❌ WRONG: Can overflow
let result = a * b + c;

// ✓ CORRECT: Use checked arithmetic
let result = a.checked_mul(b)
    .and_then(|x| x.checked_add(c))
    .expect("Overflow detected");

// Or use wider type
let result = (a as i64) * (b as i64) + (c as i64);
```

---

## **Part VII: Mental Models for Mastery**

### **Model 1: The State Machine View**

Every simulation is a state machine:

```
Current State + Input → Transition Function → Next State
```

Always ask:
1. What is my state space?
2. What are valid transitions?
3. What's my acceptance condition?

---

### **Model 2: The Invariant Maintenance**

Identify properties that must hold at every step:

```rust
// Example: Sum invariant in rotation
fn rotate_maintaining_sum(arr: &mut [i32]) {
    let original_sum: i32 = arr.iter().sum();
    
    // ... perform rotation ...
    
    let new_sum: i32 = arr.iter().sum();
    debug_assert_eq!(original_sum, new_sum, "Sum invariant violated!");
}
```

**Cognitive benefit**: Invariants catch bugs early!

---

### **Model 3: Chunking Complex Rules**

Break complex rules into simple functions:

```rust
// Instead of one giant function:
pub fn complex_simulation(input: Input) -> Output {
    // 200 lines of nested logic...
}

// Break into logical chunks:
pub fn complex_simulation(input: Input) -> Output {
    let state = initialize_state(input);
    let state = apply_phase_1(state);
    let state = apply_phase_2(state);
    let state = apply_phase_3(state);
    finalize(state)
}

fn apply_phase_1(state: State) -> State {
    // Focused logic
}
```

**Cognitive principle**: Working memory holds ~7 items. Chunking reduces cognitive load.

---

## **Part VIII: Real LeetCode Problems (Categorized)**

### **Grid Simulation**
1. Robot Bounded in Circle (LC 1041)
2. Walking Robot Simulation (LC 874)
3. Spiral Matrix (LC 54)
4. Rotate Image (LC 48)

### **String Simulation**
1. Decode String (LC 394)
2. Basic Calculator (LC 224)
3. Remove All Adjacent Duplicates In String II (LC 1209)

### **Game Simulation**
1. Can I Win (LC 464)
2. Predict the Winner (LC 486)
3. Stone Game (LC 877)

### **Event-Driven**
1. Meeting Rooms II (LC 253)
2. Car Fleet (LC 853)
3. The Skyline Problem (LC 218)

### **Array Manipulation**
1. Range Addition (LC 370)
2. Product of Array Except Self (LC 238)
3. Rotating the Box (LC 1861)

---

## **Part IX: Practice Framework**

### **Level 1: Foundation (Weeks 1-2)**
Focus: Basic grid/array simulation

**Approach**:
1. Solve 3-5 easy problems daily
2. Implement in all 3 languages
3. Compare performance
4. Document patterns observed

### **Level 2: Pattern Recognition (Weeks 3-4)**
Focus: Identifying simulation types quickly

**Approach**:
1. Solve medium problems
2. Before coding, identify: type, state, transitions
3. Estimate complexity before implementing
4. Verify estimation after

### **Level 3: Optimization (Weeks 5-6)**
Focus: Reducing time/space complexity

**Approach**:
1. Solve problem naively first
2. Identify bottlenecks
3. Apply optimization patterns
4. Benchmark improvements

### **Level 4: Mastery (Weeks 7+)**
Focus: Hard problems, edge cases, production quality

**Approach**:
1. Solve without looking at hints
2. Write comprehensive tests
3. Handle all edge cases
4. Write documentation

---

## **Part X: Language-Specific Idioms**

### **Rust Excellence**

```rust
// Use iterators for elegance
let sum: i32 = (0..n)
    .filter(|&x| x % 2 == 0)
    .map(|x| x * x)
    .sum();

// Use enums for state
enum State {
    Idle,
    Processing { progress: usize },
    Done { result: i32 },
}

// Use Option/Result for safety
fn simulate(input: i32) -> Result<i32, SimError> {
    if input < 0 {
        return Err(SimError::InvalidInput);
    }
    Ok(input * 2)
}
```

### **Go Simplicity**

```go
// Use defer for cleanup
func simulate() error {
    f, err := os.Open("state.dat")
    if err != nil {
        return err
    }
    defer f.Close() // Always closes
    
    // ... use f ...
    return nil
}

// Use goroutines for parallel simulation
results := make(chan int, len(inputs))
for _, input := range inputs {
    go func(in int) {
        results <- process(in)
    }(input)
}
```

### **C Performance**

```c
// Use restrict for optimization hints
void simulate(int * restrict a, int * restrict b, int n) {
    // Compiler knows a and b don't overlap
    for (int i = 0; i < n; i++) {
        a[i] = b[i] * 2;
    }
}

// Use inline for hot paths
static inline int transition(int state) {
    return state * 2 + 1;
}

// Use CPU cache efficiently
// ✓ Good: row-major access
for (int i = 0; i < rows; i++) {
    for (int j = 0; j < cols; j++) {
        grid[i][j] = compute();
    }
}
```

---

## **Closing Wisdom**

Simulation mastery is about **disciplined translation** from problem statement to executable logic. You're building a mental compiler: natural language → precise state machine → correct code.

**The path to top 1%:**
1. **Precision**: Every word in problem statement matters
2. **Visualization**: Draw state transitions before coding
3. **Simplicity**: Complex simulations are compositions of simple rules
4. **Verification**: Test edge cases obsessively

You have all tools now. The rest is **deliberate practice**.

*Now, shall we dive deeper into any specific simulation type, or would you like me to walk through solving a complex problem step-by-step?*