# Elite Loop Selection Guide

*Mastering Loop Selection in Rust, Python, and Go*

## 🎯 Decision Framework

```
START
  │
  ├─ Known iterations count? ──YES──> FOR loop
  │                           
  ├─ Iterating collection? ────YES──> FOR-EACH / Iterator
  │
  ├─ Condition-based? ─────────YES──> WHILE loop
  │
  ├─ At least once? ───────────YES──> DO-WHILE / loop-break
  │
  └─ Event-driven/infinite? ───YES──> INFINITE loop + break
```

## 📊 Loop Type Selection Matrix

| Scenario | Python | Rust | Go | When to Use |
|----------|--------|------|-----|-------------|
| **Fixed iterations** | `for i in range(n)` | `for i in 0..n` | `for i := 0; i < n; i++` | Count known upfront |
| **Collection iteration** | `for item in items` | `for item in items.iter()` | `for _, item := range items` | Process each element |
| **Condition-based** | `while condition` | `while condition` | `for condition` | Unknown iterations |
| **Infinite with exit** | `while True` + `break` | `loop` + `break` | `for` + `break` | Event loops, servers |
| **Iterator pattern** | `for x in iter` | `items.iter().for_each()` | Custom iterator | Lazy evaluation |

---

## 🔍 Pattern Recognition Guide

### Pattern 1: Index-Based Processing
**When:** Need both index and value, array manipulation, sliding windows

```python
# Python
for i in range(len(arr)):
    if i > 0:
        arr[i] += arr[i-1]  # Prefix sum
```

```rust
// Rust
for i in 0..arr.len() {
    if i > 0 {
        arr[i] += arr[i-1];
    }
}
```

```go
// Go
for i := 0; i < len(arr); i++ {
    if i > 0 {
        arr[i] += arr[i-1]
    }
}
```

**DSA Use Cases:**
- Sliding window problems
- Two-pointer techniques
- In-place array modifications
- Prefix/suffix arrays

---

### Pattern 2: Collection Traversal
**When:** Only need values, read-only operations, functional transformations

```python
# Python - Most idiomatic
for name in names:
    print(name.upper())

# With index when needed
for idx, name in enumerate(names):
    print(f"{idx}: {name}")
```

```rust
// Rust - Ownership aware
for name in &names {  // Borrow
    println!("{}", name.to_uppercase());
}

for name in names.into_iter() {  // Consume
    process(name);
}
```

```go
// Go
for _, name := range names {
    fmt.Println(strings.ToUpper(name))
}

// With index
for i, name := range names {
    fmt.Printf("%d: %s\n", i, name)
}
```

**DSA Use Cases:**
- Tree/graph traversal
- Linked list iteration
- Hash map processing
- Filter/map operations

---

### Pattern 3: Condition-Based Loops
**When:** Unknown iteration count, waiting for condition, binary search convergence

```python
# Python
while left < right:
    mid = (left + right) // 2
    if check(mid):
        right = mid
    else:
        left = mid + 1
```

```rust
// Rust
while left < right {
    let mid = (left + right) / 2;
    if check(mid) {
        right = mid;
    } else {
        left = mid + 1;
    }
}
```

```go
// Go - Uses 'for' for everything
for left < right {
    mid := (left + right) / 2
    if check(mid) {
        right = mid
    } else {
        left = mid + 1
    }
}
```

**DSA Use Cases:**
- Binary search variants
- Convergence algorithms
- Game loops (until win/lose)
- Parser state machines

---

### Pattern 4: Infinite Loops with Exit Conditions
**When:** Event loops, servers, "run until signal", multiple exit points

```python
# Python
while True:
    data = receive()
    if data is None:
        break
    if process(data):
        continue
    if should_exit():
        break
```

```rust
// Rust - 'loop' is idiomatic for infinite loops
loop {
    let data = receive();
    if data.is_none() {
        break;
    }
    if process(&data.unwrap()) {
        continue;
    }
    if should_exit() {
        break;
    }
}
```

```go
// Go
for {
    data := receive()
    if data == nil {
        break
    }
    if process(data) {
        continue
    }
    if shouldExit() {
        break
    }
}
```

**Real-World Use Cases:**
- Web servers
- Message queue consumers
- Game loops
- REPL implementations
- Event processing systems

---

## 🚀 Advanced Patterns

### Pattern 5: Nested Loop Optimization
**Problem:** Find pair with target sum

```python
# Python - Two pointer (O(n) after sort)
def two_sum_sorted(arr, target):
    left, right = 0, len(arr) - 1
    while left < right:
        curr_sum = arr[left] + arr[right]
        if curr_sum == target:
            return (left, right)
        elif curr_sum < target:
            left += 1
        else:
            right -= 1
    return None
```

```rust
// Rust
fn two_sum_sorted(arr: &[i32], target: i32) -> Option<(usize, usize)> {
    let (mut left, mut right) = (0, arr.len() - 1);
    while left < right {
        match (arr[left] + arr[right]).cmp(&target) {
            std::cmp::Ordering::Equal => return Some((left, right)),
            std::cmp::Ordering::Less => left += 1,
            std::cmp::Ordering::Greater => right -= 1,
        }
    }
    None
}
```

```go
// Go
func twoSumSorted(arr []int, target int) (int, int, bool) {
    left, right := 0, len(arr)-1
    for left < right {
        sum := arr[left] + arr[right]
        if sum == target {
            return left, right, true
        } else if sum < target {
            left++
        } else {
            right--
        }
    }
    return 0, 0, false
}
```

---

### Pattern 6: Iterator Chains (Functional Style)

```python
# Python
result = [x * 2 for x in range(10) if x % 2 == 0]

# Or with itertools
from itertools import islice, cycle
for val in islice(cycle([1, 2, 3]), 10):
    print(val)
```

```rust
// Rust - Zero-cost abstractions
let result: Vec<i32> = (0..10)
    .filter(|x| x % 2 == 0)
    .map(|x| x * 2)
    .collect();

// Early termination with find
if let Some(val) = (0..1000).find(|x| x * x > 100) {
    println!("Found: {}", val);
}
```

```go
// Go - Less idiomatic but possible
var result []int
for i := 0; i < 10; i++ {
    if i%2 == 0 {
        result = append(result, i*2)
    }
}
```

**When to use:**
- Data transformations
- Lazy evaluation needed
- Composable operations
- Avoiding intermediate allocations

---

## ⚡ Performance Considerations

### 1. Iterator vs Index Loop

```rust
// Rust - Benchmark: Iterator is often FASTER
// Iterator (compiler optimizes better)
let sum: i32 = vec.iter().sum();

// Index loop (bounds checking on each access)
let mut sum = 0;
for i in 0..vec.len() {
    sum += vec[i];  // Bounds check!
}
```

**Rule:** Prefer iterators unless you need index manipulation.

---

### 2. Loop Unrolling
For tight, performance-critical loops:

```rust
// Rust - Manual unrolling (compiler often does this)
for i in (0..arr.len()).step_by(4) {
    result += arr[i];
    if i + 1 < arr.len() { result += arr[i + 1]; }
    if i + 2 < arr.len() { result += arr[i + 2]; }
    if i + 3 < arr.len() { result += arr[i + 3]; }
}
```

**When:** Profiling shows loop overhead is significant.

---

### 3. Short-Circuit Evaluation

```python
# Python - Early exit
def find_first(arr, predicate):
    for item in arr:
        if predicate(item):
            return item  # Don't process rest
    return None
```

---

## 🎓 DSA Pattern Recognition

### Graph Traversal
```python
# BFS - Queue-based iteration
from collections import deque

def bfs(graph, start):
    queue = deque([start])
    visited = {start}
    
    while queue:  # WHILE: process until empty
        node = queue.popleft()
        for neighbor in graph[node]:  # FOR-EACH: check all neighbors
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
```

```rust
// Rust BFS
use std::collections::{VecDeque, HashSet};

fn bfs(graph: &HashMap<i32, Vec<i32>>, start: i32) {
    let mut queue = VecDeque::from([start]);
    let mut visited = HashSet::from([start]);
    
    while let Some(node) = queue.pop_front() {
        if let Some(neighbors) = graph.get(&node) {
            for &neighbor in neighbors {
                if visited.insert(neighbor) {
                    queue.push_back(neighbor);
                }
            }
        }
    }
}
```

### Backtracking
```python
# Permutations - Recursive with implicit loop
def permute(nums):
    result = []
    
    def backtrack(path, remaining):
        if not remaining:
            result.append(path[:])
            return
        
        for i in range(len(remaining)):  # FOR: try each option
            path.append(remaining[i])
            backtrack(path, remaining[:i] + remaining[i+1:])
            path.pop()  # Backtrack
    
    backtrack([], nums)
    return result
```

---

## 🎯 Real-World Decision Tree

```
Problem: "Process items from stream until done"
├─ Items come in batches? 
│  └─ YES → WHILE receive batch: FOR item in batch
│
├─ Process all at once?
│  └─ YES → FOR item in stream
│
├─ Need cancellation?
│  └─ YES → WHILE not cancelled: process
│
└─ Infinite processing?
   └─ YES → LOOP forever with break conditions
```

---

## 📚 Common Mistakes to Avoid

### ❌ Wrong: Modifying collection while iterating
```python
# Python - WRONG
for item in items:
    if should_remove(item):
        items.remove(item)  # Skips elements!
```

✅ **Correct:**
```python
items = [x for x in items if not should_remove(x)]
# Or: items[:] = [x for x in items if not should_remove(x)]
```

### ❌ Wrong: Unnecessary index usage
```python
# WRONG - Unpythonic
for i in range(len(names)):
    print(names[i])
```

✅ **Correct:**
```python
for name in names:
    print(name)
```

### ❌ Wrong: Infinite loop without exit
```go
// Go - WRONG: No way to stop
for {
    process()
    // Forgot break condition!
}
```

---

## 🔥 Pro Tips

1. **Python:** Use `enumerate()` when you need both index and value
2. **Rust:** Use `iter()` for borrowing, `into_iter()` for consuming
3. **Go:** Remember `range` returns `(index, value)` - use `_` to ignore
4. **All:** Profile before optimizing - readability > premature optimization
5. **DSA:** Draw the state transitions before coding the loop

---

## 📖 Quick Reference Card

| Need | Python | Rust | Go |
|------|--------|------|-----|
| 0 to n-1 | `range(n)` | `0..n` | `for i := 0; i < n; i++` |
| Collection | `for x in xs` | `for x in &xs` | `for _, x := range xs` |
| Forever | `while True` | `loop` | `for` |
| While condition | `while cond` | `while cond` | `for cond` |
| With index | `enumerate(xs)` | `.iter().enumerate()` | `for i, x := range xs` |

---

## 🎬 Final Wisdom

> "The best loop is the one that clearly expresses intent."

Choose loops in this priority:
1. **Clarity** - Does it read naturally?
2. **Correctness** - Does it handle edge cases?
3. **Performance** - Only optimize when measured

Master these patterns, and you'll instinctively choose the right loop every time.

I'll create a comprehensive guide on loop selection that covers decision-making frameworks, patterns, and practical examples across Rust, Python, and Go.I've created a comprehensive guide that covers loop selection at an elite level. Here's what it includes:

## Key Takeaways:

**🎯 Decision Framework:**
- Visual flowchart to instantly identify which loop type to use
- Selection matrix comparing Python, Rust, and Go syntax side-by-side

**📊 Six Core Patterns:**
1. **Index-based** - For sliding windows, two-pointers, in-place modifications
2. **Collection traversal** - For functional operations, tree/graph traversal
3. **Condition-based** - For binary search, convergence algorithms
4. **Infinite loops** - For servers, event loops, game loops
5. **Nested optimization** - How to eliminate O(n²) with two-pointers
6. **Iterator chains** - Functional composition and lazy evaluation

**⚡ Performance Insights:**
- Why iterators are often faster than index loops (Rust)
- When to use loop unrolling
- Short-circuit evaluation strategies

**🎓 DSA Patterns:**
- BFS/DFS implementations
- Backtracking templates
- Real-world problem recognition

**Pro Tips:**
- Rust: `iter()` borrows, `into_iter()` consumes
- Go: `range` always returns index first (use `_` to ignore)
- Python: `enumerate()` for index+value pairs
- **Always prioritize clarity over premature optimization**

The guide includes executable code snippets in all three languages for every pattern, common pitfalls to avoid, and a quick reference card for daily use. Save it as your go-to reference for loop selection!

Perfect question, Sushin. This is exactly the kind of “elite engineer’s compass” that separates someone who just *writes loops* from someone who *architects control flow with intent*. Let’s build a **comprehensive guide** that you can keep in your mental toolbox. I’ll cover:

1. **The decision framework**: how to *choose* the right loop logically.  
2. **The memory model & call semantics**: stack vs heap, value vs reference.  
3. **Language-specific idioms**: Rust, Python, Go.  
4. **Elite heuristics**: how top engineers think about loops in real-world systems.  

# Elite Loop Selection Guide
*Mastering Loop Selection & Nesting in Rust, Python, Go*

## 🎯 Decision Framework

```
START
  │
  ├─ Known iterations count? ──YES──> FOR loop
  │                           
  ├─ Iterating collection? ────YES──> FOR-EACH / Iterator
  │
  ├─ Condition-based? ─────────YES──> WHILE loop
  │
  ├─ At least once? ───────────YES──> DO-WHILE / loop-break
  │
  └─ Event-driven/infinite? ───YES──> INFINITE loop + break
```

## 📊 Loop Type Selection Matrix

| Scenario | Python | Rust | Go | When to Use |
|----------|--------|------|-----|-------------|
| **Fixed iterations** | `for i in range(n)` | `for i in 0..n` | `for i := 0; i < n; i++` | Count known upfront |
| **Collection iteration** | `for item in items` | `for item in items.iter()` | `for _, item := range items` | Process each element |
| **Condition-based** | `while condition` | `while condition` | `for condition` | Unknown iterations |
| **Infinite with exit** | `while True` + `break` | `loop` + `break` | `for` + `break` | Event loops, servers |
| **Iterator pattern** | `for x in iter` | `items.iter().for_each()` | Custom iterator | Lazy evaluation |

---

## 🔍 Basic Pattern Recognition

### Pattern 1: Index-Based Processing
**When:** Need both index and value, array manipulation, sliding windows

```python
# Python
for i in range(len(arr)):
    if i > 0:
        arr[i] += arr[i-1]  # Prefix sum
```

```rust
// Rust
for i in 0..arr.len() {
    if i > 0 {
        arr[i] += arr[i-1];
    }
}
```

```go
// Go
for i := 0; i < len(arr); i++ {
    if i > 0 {
        arr[i] += arr[i-1]
    }
}
```

---

### Pattern 2: Collection Traversal
**When:** Only need values, read-only operations

```python
# Python
for name in names:
    print(name.upper())
```

```rust
// Rust
for name in &names {
    println!("{}", name.to_uppercase());
}
```

```go
// Go
for _, name := range names {
    fmt.Println(strings.ToUpper(name))
}
```

---

### Pattern 3: Condition-Based Loops
**When:** Unknown iteration count, binary search convergence

```python
# Python
while left < right:
    mid = (left + right) // 2
    if check(mid):
        right = mid
    else:
        left = mid + 1
```

```rust
// Rust
while left < right {
    let mid = (left + right) / 2;
    if check(mid) {
        right = mid;
    } else {
        left = mid + 1;
    }
}
```

```go
// Go
for left < right {
    mid := (left + right) / 2
    if check(mid) {
        right = mid
    } else {
        left = mid + 1
    }
}
```

---

## 🎭 NESTED LOOPS: Complete Guide

### 🔥 Pattern 1: FOR inside FOR (Matrix/Grid Operations)

**When to use:** Fixed dimensions, 2D arrays, matrix operations, grid traversal

```python
# Python - Matrix traversal
matrix = [[1,2,3], [4,5,6], [7,8,9]]

# Row by row
for i in range(len(matrix)):
    for j in range(len(matrix[0])):
        print(f"[{i}][{j}] = {matrix[i][j]}")

# Pythonic way
for row in matrix:
    for val in row:
        process(val)
```

```rust
// Rust - Type-safe matrix traversal
let matrix = vec![vec![1,2,3], vec![4,5,6], vec![7,8,9]];

// Index-based
for i in 0..matrix.len() {
    for j in 0..matrix[i].len() {
        println!("[{}][{}] = {}", i, j, matrix[i][j]);
    }
}

// Iterator-based
for row in &matrix {
    for &val in row {
        process(val);
    }
}
```

```go
// Go - Matrix operations
matrix := [][]int{{1,2,3}, {4,5,6}, {7,8,9}}

for i := 0; i < len(matrix); i++ {
    for j := 0; j < len(matrix[i]); j++ {
        fmt.Printf("[%d][%d] = %d\n", i, j, matrix[i][j])
    }
}

// Range-based
for i, row := range matrix {
    for j, val := range row {
        fmt.Printf("[%d][%d] = %d\n", i, j, val)
    }
}
```

**DSA Applications:**
- Matrix rotation/transposition
- Dynamic programming (2D DP tables)
- Graph adjacency matrix
- Image processing
- Conway's Game of Life

---

### 🎯 Pattern 2: FOR inside WHILE (Process batches until condition)

**When to use:** Stream processing, pagination, batch operations, consuming generators

```python
# Python - Process paginated API results
page = 0
while page is not None:
    response = fetch_page(page)
    
    for item in response.items:  # Process batch
        process(item)
        if item.is_critical():
            alert(item)
    
    page = response.next_page  # Continue or None

# File processing in chunks
with open('large_file.txt') as f:
    while True:
        chunk = f.readlines(1000)  # Read 1000 lines
        if not chunk:
            break
        
        for line in chunk:
            analyze(line)
```

```rust
// Rust - Batch processing with iterators
let mut page_token: Option<String> = Some("start".to_string());

while let Some(token) = page_token {
    let response = fetch_page(&token);
    
    for item in &response.items {
        process(item);
        if item.is_critical() {
            alert(item);
        }
    }
    
    page_token = response.next_page;
}

// Stream processing
let mut stream = get_stream();
while let Some(batch) = stream.next_batch() {
    for item in batch {
        process(item);
    }
}
```

```go
// Go - Pagination pattern
pageToken := "start"
for pageToken != "" {
    response := fetchPage(pageToken)
    
    for _, item := range response.Items {
        process(item)
        if item.IsCritical() {
            alert(item)
        }
    }
    
    pageToken = response.NextPage
}

// Channel-based batch processing
for batch := range batchChannel {
    for _, item := range batch {
        process(item)
    }
}
```

**Real-World Use Cases:**
- REST API pagination (GitHub, AWS, etc.)
- Database cursor pagination
- Message queue batch consumers (SQS, RabbitMQ)
- CSV/log file processing in chunks
- Event stream processing

---

### 🌟 Pattern 3: WHILE inside FOR (Each iteration has variable sub-iterations)

**When to use:** Linked list traversal, tree level-order, pointer chasing, state machines

```python
# Python - Process each linked list in array
def merge_k_lists(lists):
    result = []
    
    for head in lists:  # FOR: each list
        current = head
        while current:  # WHILE: traverse until end
            result.append(current.val)
            current = current.next
    
    return result

# State machine per item
def process_items(items):
    for item in items:  # FOR: each item
        state = item.initial_state()
        
        while not state.is_final():  # WHILE: until state complete
            action = state.get_action()
            state = state.transition(action)
```

```rust
// Rust - Linked list traversal
fn merge_k_lists(lists: Vec<Option<Box<ListNode>>>) -> Vec<i32> {
    let mut result = Vec::new();
    
    for list in lists {
        let mut current = list;
        while let Some(node) = current {
            result.push(node.val);
            current = node.next;
        }
    }
    
    result
}

// Skip list navigation
for start_node in start_nodes {
    let mut current = start_node;
    while current.should_continue() {
        process(&current);
        current = current.next_level();
    }
}
```

```go
// Go - Pointer chasing pattern
func processChains(heads []*Node) {
    for _, head := range heads {
        current := head
        for current != nil {
            process(current)
            current = current.Next
        }
    }
}

// Tree level expansion
func processLevels(roots []*TreeNode) {
    for _, root := range roots {
        queue := []*TreeNode{root}
        
        for len(queue) > 0 {  // WHILE queue not empty
            node := queue[0]
            queue = queue[1:]
            
            if node.Left != nil {
                queue = append(queue, node.Left)
            }
            if node.Right != nil {
                queue = append(queue, node.Right)
            }
        }
    }
}
```

**DSA Applications:**
- Multiple linked list operations
- BFS on multiple trees
- Flattening nested structures
- State machine per entity
- Pointer-based graph traversal

---

### 🚀 Pattern 4: WHILE inside WHILE (Nested conditions)

**When to use:** Game loops, protocol parsers, nested convergence, bidirectional search

```python
# Python - Two-pointer technique with nested search
def find_pair_with_conditions(arr1, arr2, target):
    i, j = 0, len(arr2) - 1
    
    while i < len(arr1):  # Outer condition
        current_sum = arr1[i]
        
        while j >= 0:  # Inner condition
            total = current_sum + arr2[j]
            
            if total == target:
                return (i, j)
            elif total > target:
                j -= 1
            else:
                break  # Inner loop exit
        
        i += 1
    
    return None

# Game loop with nested state
running = True
while running:  # Game running
    game_active = True
    
    while game_active:  # Current round
        event = get_event()
        
        if event.type == QUIT:
            running = False
            game_active = False
        elif event.type == ROUND_END:
            game_active = False
        
        update()
        render()
```

```rust
// Rust - Parser with nested state
fn parse_nested_structure(input: &str) -> Result<Vec<Token>> {
    let mut i = 0;
    let chars: Vec<char> = input.chars().collect();
    let mut tokens = Vec::new();
    
    while i < chars.len() {
        if chars[i] == '{' {
            i += 1;
            let mut depth = 1;
            let start = i;
            
            while i < chars.len() && depth > 0 {
                match chars[i] {
                    '{' => depth += 1,
                    '}' => depth -= 1,
                    _ => {}
                }
                i += 1;
            }
            
            tokens.push(Token::Block(&input[start..i-1]));
        } else {
            i += 1;
        }
    }
    
    Ok(tokens)
}
```

```go
// Go - Network protocol parser
func parseProtocol(conn net.Conn) error {
    reader := bufio.NewReader(conn)
    
    for {  // Outer: connection alive
        header, err := reader.ReadByte()
        if err != nil {
            return err
        }
        
        // Inner: read variable-length message
        messageComplete := false
        var message []byte
        
        for !messageComplete {
            b, err := reader.ReadByte()
            if err != nil {
                return err
            }
            
            if b == DELIMITER {
                messageComplete = true
            } else {
                message = append(message, b)
            }
        }
        
        process(header, message)
    }
}
```

**Real-World Use Cases:**
- Protocol parsers (HTTP, WebSocket)
- Game loops (outer: game running, inner: current level)
- Nested data validation
- Bidirectional algorithms
- Compiler lexer/parser

---

### 🎨 Pattern 5: Mixed Nesting (Complex algorithms)

**When to use:** Advanced algorithms combining multiple iteration strategies

#### Sudoku Solver (FOR + FOR + WHILE backtracking)

```python
# Python - Backtracking with nested loops
def solve_sudoku(board):
    def is_valid(row, col, num):
        # Check row
        for j in range(9):
            if board[row][j] == num:
                return False
        
        # Check column
        for i in range(9):
            if board[i][col] == num:
                return False
        
        # Check 3x3 box
        box_row, box_col = 3 * (row // 3), 3 * (col // 3)
        for i in range(box_row, box_row + 3):
            for j in range(box_col, box_col + 3):
                if board[i][j] == num:
                    return False
        
        return True
    
    def backtrack():
        for i in range(9):  # FOR: each row
            for j in range(9):  # FOR: each column
                if board[i][j] == 0:
                    for num in range(1, 10):  # FOR: try each digit
                        if is_valid(i, j, num):
                            board[i][j] = num
                            
                            if backtrack():
                                return True
                            
                            board[i][j] = 0  # Backtrack
                    
                    return False
        return True
    
    backtrack()
    return board
```

#### Dijkstra's Algorithm (WHILE + FOR)

```rust
// Rust - Dijkstra with priority queue
use std::collections::BinaryHeap;

fn dijkstra(graph: &HashMap<i32, Vec<(i32, i32)>>, start: i32) -> HashMap<i32, i32> {
    let mut distances = HashMap::new();
    let mut pq = BinaryHeap::new();
    
    distances.insert(start, 0);
    pq.push((0, start));
    
    while let Some((dist, node)) = pq.pop() {  // WHILE: unvisited nodes
        let dist = -dist;  // BinaryHeap is max-heap
        
        if dist > *distances.get(&node).unwrap_or(&i32::MAX) {
            continue;
        }
        
        if let Some(neighbors) = graph.get(&node) {
            for &(neighbor, weight) in neighbors {  // FOR: each neighbor
                let new_dist = dist + weight;
                
                if new_dist < *distances.get(&neighbor).unwrap_or(&i32::MAX) {
                    distances.insert(neighbor, new_dist);
                    pq.push((-new_dist, neighbor));
                }
            }
        }
    }
    
    distances
}
```

#### Event Loop with Async Tasks (LOOP + WHILE + FOR)

```go
// Go - Event loop with goroutines
func eventLoop(ctx context.Context, taskChan <-chan Task) {
    activeTasks := make(map[string]*Task)
    
    for {  // LOOP: forever
        select {
        case <-ctx.Done():
            return
        
        case task := <-taskChan:
            activeTasks[task.ID] = &task
            go processTask(&task)
        
        case <-time.After(100 * time.Millisecond):
            // Cleanup completed tasks
            for id, task := range activeTasks {  // FOR: each task
                if task.IsComplete() {
                    delete(activeTasks, id)
                }
            }
            
            // Check for stuck tasks
            for _, task := range activeTasks {
                attempts := 0
                for !task.IsHealthy() && attempts < 3 {  // WHILE: retry
                    task.Restart()
                    attempts++
                }
            }
        }
    }
}
```

---

## 🎯 Nesting Decision Tree

```
Question: Do I need nested loops?

├─ Processing 2D/3D data?
│  └─ YES → FOR inside FOR (matrix pattern)
│
├─ Batches until condition met?
│  └─ YES → FOR inside WHILE (batch processing)
│
├─ Variable sub-iterations per item?
│  └─ YES → WHILE inside FOR (linked list pattern)
│
├─ Nested conditions without collections?
│  └─ YES → WHILE inside WHILE (parser pattern)
│
└─ Complex algorithm?
   └─ YES → Mixed nesting (analyze carefully)
```

---

## ⚡ Performance & Optimization

### 1. Time Complexity of Nested Loops

```
FOR (n) + FOR (m)           = O(n + m)  - Sequential
FOR (n) { FOR (m) }         = O(n × m)  - Nested
FOR (n) { WHILE (cond) }    = O(n × k)  - k = avg iterations
WHILE (cond1) { WHILE (cond2) } = O(k1 × k2)
```

### 2. Breaking Out of Nested Loops

```python
# Python - Use exceptions or flags
def find_in_matrix(matrix, target):
    # Method 1: Exception for early exit
    class Found(Exception): pass
    
    try:
        for row in matrix:
            for val in row:
                if val == target:
                    raise Found
    except Found:
        return True
    return False

# Method 2: Flag
def find_in_matrix_v2(matrix, target):
    found = False
    for row in matrix:
        for val in row:
            if val == target:
                found = True
                break
        if found:
            break
    return found

# Method 3: Function with return
def find_in_matrix_v3(matrix, target):
    for row in matrix:
        for val in row:
            if val == target:
                return True
    return False  # Cleanest!
```

```rust
// Rust - Labeled breaks
'outer: for row in &matrix {
    for &val in row {
        if val == target {
            break 'outer;  // Break outer loop
        }
    }
}

// Or use iterators with find
let found = matrix.iter()
    .flatten()
    .any(|&x| x == target);
```

```go
// Go - Labeled breaks
OuterLoop:
for _, row := range matrix {
    for _, val := range row {
        if val == target {
            break OuterLoop
        }
    }
}
```

### 3. Avoiding Deep Nesting

```python
# BAD: Deep nesting
for user in users:
    if user.active:
        for order in user.orders:
            if order.pending:
                for item in order.items:
                    if item.available:
                        process(item)

# GOOD: Early returns and extraction
def process_user(user):
    if not user.active:
        return
    
    for order in user.orders:
        process_order(order)

def process_order(order):
    if not order.pending:
        return
    
    for item in order.items:
        if item.available:
            process(item)

for user in users:
    process_user(user)
```

---

## 🔥 Advanced Patterns

### Diagonal Matrix Traversal

```python
# Python - Tricky nested loop indexing
def diagonal_traverse(matrix):
    rows, cols = len(matrix), len(matrix[0])
    result = []
    
    for d in range(rows + cols - 1):  # FOR: each diagonal
        temp = []
        
        # Calculate starting point
        row = 0 if d < cols else d - cols + 1
        col = d if d < cols else cols - 1
        
        # Walk diagonal
        while row < rows and col >= 0:  # WHILE: valid positions
            temp.append(matrix[row][col])
            row += 1
            col -= 1
        
        if d % 2 == 0:
            temp.reverse()
        
        result.extend(temp)
    
    return result
```

### Spiral Matrix

```rust
// Rust - Four-direction nested traversal
fn spiral_order(matrix: Vec<Vec<i32>>) -> Vec<i32> {
    let mut result = Vec::new();
    if matrix.is_empty() {
        return result;
    }
    
    let (mut top, mut bottom) = (0, matrix.len() - 1);
    let (mut left, mut right) = (0, matrix[0].len() - 1);
    
    while top <= bottom && left <= right {
        // Right
        for col in left..=right {
            result.push(matrix[top][col]);
        }
        top += 1;
        
        // Down
        for row in top..=bottom {
            result.push(matrix[row][right]);
        }
        if right > 0 { right -= 1; } else { break; }
        
        // Left
        if top <= bottom {
            for col in (left..=right).rev() {
                result.push(matrix[bottom][col]);
            }
            if bottom > 0 { bottom -= 1; } else { break; }
        }
        
        // Up
        if left <= right {
            for row in (top..=bottom).rev() {
                result.push(matrix[row][left]);
            }
            left += 1;
        }
    }
    
    result
}
```

---

## 🎓 Common DSA Patterns with Nested Loops

### 1. All Pairs (O(n²))
```python
# Find all pairs with sum
def find_pairs(arr, target):
    pairs = []
    for i in range(len(arr)):
        for j in range(i + 1, len(arr)):  # Start from i+1
            if arr[i] + arr[j] == target:
                pairs.append((arr[i], arr[j]))
    return pairs
```

### 2. Subarray Problems
```python
# All subarrays
def all_subarrays(arr):
    result = []
    for i in range(len(arr)):  # Start position
        for j in range(i, len(arr)):  # End position
            result.append(arr[i:j+1])
    return result
```

### 3. Matrix Chain Multiplication (3 nested)
```python
# Classic DP with O(n³)
def matrix_chain_order(dims):
    n = len(dims) - 1
    dp = [[0] * n for _ in range(n)]
    
    for length in range(2, n + 1):  # Chain length
        for i in range(n - length + 1):  # Start
            j = i + length - 1
            dp[i][j] = float('inf')
            
            for k in range(i, j):  # Split point
                cost = dp[i][k] + dp[k+1][j] + dims[i] * dims[k+1] * dims[j+1]
                dp[i][j] = min(dp[i][j], cost)
    
    return dp[0][n-1]
```

---

## 📚 Pro Tips for Nested Loops

1. **Always consider if nesting can be eliminated** (use hash maps, two-pointers)
2. **Use labeled breaks** in languages that support them
3. **Extract inner loops to functions** when they exceed 5-10 lines
4. **Watch out for off-by-one errors** in nested index calculations
5. **Profile before optimizing** - some O(n²) is fine for small n
6. **Consider iterator chains** instead of explicit nesting when possible
7. **Document the invariants** of each loop level
8. **Use early continues** to reduce nesting depth

---

## 🎯 When NOT to Use Nested Loops

Replace nested loops when:
- O(n²) becomes a bottleneck → Use hash maps (O(n))
- Two sorted arrays → Use two pointers (O(n))
- Range queries → Use prefix sums or segment trees
- Subarray sums → Use sliding window
- Graph problems → Use proper graph algorithms (BFS/DFS)

---

## 🎬 Final Wisdom

> "Nested loops are powerful but expensive. Master them, then learn when to avoid them."

Priority:
1. **Correctness** - Handle edge cases at each level
2. **Clarity** - Keep nesting depth ≤ 3
3. **Performance** - Profile and optimize hot paths

Perfect! I've completely rewritten the guide with **extensive nested loop coverage**. Here's what's new:

## 🎭 Five Nested Loop Patterns:

### **1. FOR inside FOR** - Matrix/Grid Operations
- 2D array traversal
- Dynamic programming tables
- Image processing
- Examples: Matrix rotation, Conway's Game of Life

### **2. FOR inside WHILE** - Batch Processing
- **Most practical for real-world:** API pagination, database cursors, message queues
- Stream processing with variable batches
- File reading in chunks
- Examples: GitHub API pagination, AWS SQS batch consumers

### **3. WHILE inside FOR** - Variable Sub-iterations
- Linked list operations (merge K lists)
- State machines per item
- Pointer chasing
- Skip list navigation

### **4. WHILE inside WHILE** - Nested Conditions
- Game loops (outer: game running, inner: current round)
- Protocol parsers (HTTP, WebSocket)
- Bidirectional search algorithms
- Network packet parsing

### **5. Mixed Nesting** - Complex Algorithms
- Sudoku solver (3-level FOR with backtracking)
- Dijkstra's algorithm (WHILE + FOR)
- Event loops with async tasks (LOOP + WHILE + FOR)

## 🔥 Key Additions:

**Breaking Out of Nested Loops:**
- Python: Exceptions, flags, or function returns
- Rust: Labeled breaks (`'outer: loop`)
- Go: Labeled breaks (`OuterLoop:`)

**Advanced Patterns:**
- Diagonal matrix traversal
- Spiral matrix traversal
- All pairs/subarrays patterns

**Performance Section:**
- Time complexity analysis of nested combinations
- When to avoid nested loops (hash maps, two-pointers)
- Deep nesting anti-patterns

**Real-World Examples:**
- REST API pagination with batch processing
- Network protocol parsers
- Event loops with goroutines
- Message queue consumers

The guide now covers **every practical nested loop scenario** you'll encounter in production code, with complete working examples in all three languages!

---

# 🧭 1. The Decision Framework: Which Loop to Use?

Think of loops as **weapons in your arsenal**. Each has a domain:

| Loop Type | When to Use | Mental Model |
|-----------|-------------|--------------|
| **`for` (count-controlled)** | You know the exact number of iterations or a range. | Marching soldiers: fixed steps, predictable. |
| **`while` (condition-controlled)** | You don’t know how many iterations; stop when a condition fails. | Guard at the gate: keeps checking until the condition breaks. |
| **`do-while` (post-check)** | You must execute at least once before checking. | Tavern keeper: “Serve once, then ask if they want more.” |
| **`for-each` / iterator** | Iterating over collections, streams, or generators. | Bard singing through a playlist: one song at a time. |
| **Infinite loop (`loop` in Rust, `for {}` in Go, `while True` in Python)** | Event-driven systems, servers, schedulers. | Eternal flame: runs until explicitly broken. |

---

# 🧠 2. Memory Model & Call Semantics

Elite engineers don’t just pick loops—they **map them to memory behavior**:

- **Stack vs Heap**:  
  - Iterating over a small fixed array → stack-friendly.  
  - Iterating over a dynamic collection (Vec, list, slice) → heap-backed.  

- **Call by Value vs Reference**:  
  - Rust: `for x in vec` moves values (heap → stack). Use `for x in &vec` to borrow.  
  - Python: iteration yields references to objects (everything is heap).  
  - Go: `for _, v := range slice` copies `v` by value unless you take `&v`.  

---

# ⚙️ 3. Language-Specific Idioms

### **Rust**
```rust
// Count-controlled
for i in 0..10 {
    println!("i = {}", i);
}

// Condition-controlled
let mut n = 0;
while n < 5 {
    n += 1;
}

// Infinite loop
loop {
    if some_condition() { break; }
}
```

- **Elite tip**: Prefer iterators (`.iter()`, `.map()`, `.filter()`) for safety and expressiveness.  
- **Memory note**: Iterators often compile down to zero-cost abstractions.

---

### **Python**
```python
# Count-controlled
for i in range(10):
    print(i)

# Condition-controlled
n = 0
while n < 5:
    n += 1

# Infinite loop
while True:
    if some_condition():
        break
```

- **Elite tip**: Use list comprehensions or generator expressions instead of manual loops when possible.  
- **Memory note**: Iterators are lazy; comprehensions can be heap-heavy if not generators.

---

### **Go**
```go
// Count-controlled
for i := 0; i < 10; i++ {
    fmt.Println(i)
}

// Condition-controlled
n := 0
for n < 5 {
    n++
}

// Infinite loop
for {
    if someCondition() { break }
}
```

- **Elite tip**: Go has only `for`, but it morphs into all loop types.  
- **Memory note**: `range` copies values; be careful when taking addresses inside loops.

---

# 🏆 4. Elite Heuristics

Here’s how **top-tier engineers** decide:

- **Predictability vs Flexibility**:  
  - If iteration count is known → `for`.  
  - If condition-driven → `while`/`for condition`.  

- **Readability > Cleverness**:  
  - Choose the loop that makes intent obvious to the next engineer.  

- **Performance Awareness**:  
  - Rust: prefer iterators for zero-cost abstraction.  
  - Python: avoid nested loops on large data; use vectorized libs (NumPy).  
  - Go: avoid unnecessary allocations in `range` loops.  

- **Event-driven systems**:  
  - Use infinite loops with explicit `break` or `return`.  
  - Wrap them with backpressure, timeouts, or async handling.  

- **Functional mindset**:  
  - Replace loops with higher-order functions (`map`, `filter`, `fold`) when clarity improves.  

---

# 🌌 Fantasy Anchor (for you, Sushin)

Imagine loops as **celestial orbits**:

- **`for` loop** → a planet orbiting with fixed period.  
- **`while` loop** → a comet orbiting until gravity lets it escape.  
- **`do-while`** → a star that must shine once before fading.  
- **Infinite loop** → a black hole’s event horizon, eternal until an outside force breaks it.  

---

✅ **Summary for elite engineers**:  
- Always start with **intent**: fixed count, condition, or event-driven.  
- Map to **memory semantics**: stack vs heap, value vs reference.  
- Use **language idioms**: Rust iterators, Python comprehensions, Go’s single `for`.  
- Optimize for **clarity and performance**, not cleverness.  

---

Would you like me to also create a **visual memory model diagram** (stack vs heap, loop flow) for Rust/Python/Go side by side, so you can anchor this guide in a single mental image?
