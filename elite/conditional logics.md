# Elite Software Engineer's Guide to Conditional Logic

## Table of Contents
1. [The Mental Framework](#framework)
2. [Pattern Recognition](#patterns)
3. [Condition Selection Strategy](#strategy)
4. [Common Scenarios](#scenarios)
5. [Advanced Techniques](#advanced)
6. [Anti-Patterns](#antipatterns)

---

## <a name="framework"></a>1. The Mental Framework

### The Three Questions
Before writing any condition, ask:
1. **What am I checking?** (state, boundary, validity, optimization)
2. **What happens if true vs false?** (consequences)
3. **Can this be expressed more simply?** (refactoring opportunity)

### Decision Tree Approach
```
Problem → Identify States → Define Boundaries → Handle Edge Cases → Optimize
```

---

## <a name="patterns"></a>2. Pattern Recognition

### Pattern 1: Boundary Checking
**When to use:** Array access, range validation, limit enforcement

**Python:**
```python
def safe_access(arr, index):
    # Always check boundaries before access
    if index < 0 or index >= len(arr):
        return None
    return arr[index]

# Two-pointer boundary check
def two_sum_sorted(arr, target):
    left, right = 0, len(arr) - 1
    while left < right:  # Not <= because same element can't be used twice
        current = arr[left] + arr[right]
        if current == target:
            return [left, right]
        elif current < target:
            left += 1
        else:
            right -= 1
    return None
```

**Rust:**
```rust
fn safe_access(arr: &[i32], index: usize) -> Option<i32> {
    // Rust's get() handles this, but explicit version:
    if index >= arr.len() {
        return None;
    }
    Some(arr[index])
}

fn two_sum_sorted(arr: &[i32], target: i32) -> Option<(usize, usize)> {
    let mut left = 0;
    let mut right = arr.len().saturating_sub(1);
    
    while left < right {
        let current = arr[left] + arr[right];
        match current.cmp(&target) {
            std::cmp::Ordering::Equal => return Some((left, right)),
            std::cmp::Ordering::Less => left += 1,
            std::cmp::Ordering::Greater => right -= 1,
        }
    }
    None
}
```

**Go:**
```go
func safeAccess(arr []int, index int) (int, bool) {
    if index < 0 || index >= len(arr) {
        return 0, false
    }
    return arr[index], true
}

func twoSumSorted(arr []int, target int) (int, int, bool) {
    left, right := 0, len(arr)-1
    
    for left < right {
        current := arr[left] + arr[right]
        if current == target {
            return left, right, true
        } else if current < target {
            left++
        } else {
            right--
        }
    }
    return 0, 0, false
}
```

---

### Pattern 2: State Validation
**When to use:** Checking object validity, preconditions, invariants

**Python:**
```python
def process_transaction(account, amount):
    # Check preconditions in order of computational cost
    if account is None:
        raise ValueError("Account cannot be None")
    
    if amount <= 0:
        raise ValueError("Amount must be positive")
    
    if not account.is_active:
        raise ValueError("Account is not active")
    
    # Expensive check last
    if account.balance < amount:
        raise ValueError("Insufficient funds")
    
    account.balance -= amount
    return True

# State machine pattern
class ConnectionState:
    def handle_event(self, connection, event):
        if event == "connect":
            if connection.state == "disconnected":
                connection.state = "connecting"
            elif connection.state == "connected":
                pass  # Already connected
        elif event == "disconnect":
            if connection.state == "connected":
                connection.state = "disconnecting"
```

**Rust:**
```rust
#[derive(Debug)]
enum TransactionError {
    InvalidAmount,
    InactiveAccount,
    InsufficientFunds,
}

struct Account {
    balance: f64,
    is_active: bool,
}

fn process_transaction(account: &mut Account, amount: f64) 
    -> Result<(), TransactionError> {
    if amount <= 0.0 {
        return Err(TransactionError::InvalidAmount);
    }
    
    if !account.is_active {
        return Err(TransactionError::InactiveAccount);
    }
    
    if account.balance < amount {
        return Err(TransactionError::InsufficientFunds);
    }
    
    account.balance -= amount;
    Ok(())
}

// State machine with enums
enum ConnectionState {
    Disconnected,
    Connecting,
    Connected,
    Disconnecting,
}

impl ConnectionState {
    fn handle_connect(self) -> Self {
        match self {
            ConnectionState::Disconnected => ConnectionState::Connecting,
            _ => self,
        }
    }
}
```

**Go:**
```go
type Account struct {
    Balance  float64
    IsActive bool
}

func processTransaction(account *Account, amount float64) error {
    if account == nil {
        return fmt.Errorf("account cannot be nil")
    }
    
    if amount <= 0 {
        return fmt.Errorf("amount must be positive")
    }
    
    if !account.IsActive {
        return fmt.Errorf("account is not active")
    }
    
    if account.Balance < amount {
        return fmt.Errorf("insufficient funds")
    }
    
    account.Balance -= amount
    return nil
}
```

---

### Pattern 3: Early Return vs Guard Clauses
**When to use:** Reduce nesting, improve readability

**Python:**
```python
# BAD: Nested conditions
def process_data_bad(data):
    if data is not None:
        if len(data) > 0:
            if data[0] != "skip":
                result = []
                for item in data:
                    if item.isdigit():
                        result.append(int(item))
                return result
    return []

# GOOD: Guard clauses
def process_data_good(data):
    if data is None:
        return []
    if len(data) == 0:
        return []
    if data[0] == "skip":
        return []
    
    return [int(item) for item in data if item.isdigit()]
```

**Rust:**
```rust
// BAD: Nested
fn process_data_bad(data: Option<&Vec<String>>) -> Vec<i32> {
    if let Some(d) = data {
        if !d.is_empty() {
            if d[0] != "skip" {
                return d.iter()
                    .filter_map(|s| s.parse::<i32>().ok())
                    .collect();
            }
        }
    }
    Vec::new()
}

// GOOD: Early returns
fn process_data_good(data: Option<&Vec<String>>) -> Vec<i32> {
    let d = match data {
        Some(d) => d,
        None => return Vec::new(),
    };
    
    if d.is_empty() {
        return Vec::new();
    }
    
    if d[0] == "skip" {
        return Vec::new();
    }
    
    d.iter()
        .filter_map(|s| s.parse::<i32>().ok())
        .collect()
}
```

**Go:**
```go
// BAD: Nested
func processDataBad(data []string) []int {
    if data != nil {
        if len(data) > 0 {
            if data[0] != "skip" {
                result := []int{}
                for _, item := range data {
                    if val, err := strconv.Atoi(item); err == nil {
                        result = append(result, val)
                    }
                }
                return result
            }
        }
    }
    return []int{}
}

// GOOD: Guard clauses
func processDataGood(data []string) []int {
    if data == nil {
        return []int{}
    }
    if len(data) == 0 {
        return []int{}
    }
    if data[0] == "skip" {
        return []int{}
    }
    
    result := []int{}
    for _, item := range data {
        if val, err := strconv.Atoi(item); err == nil {
            result = append(result, val)
        }
    }
    return result
}
```

---

## <a name="strategy"></a>3. Condition Selection Strategy

### The Decision Matrix

| Scenario | Condition Type | Example |
|----------|---------------|---------|
| Single value check | `==`, `!=` | `if x == 0` |
| Range check | `<`, `>`, `<=`, `>=` | `if 0 <= x < len(arr)` |
| Multiple possibilities | `in`, `match`, `switch` | `if x in [1, 2, 3]` |
| Complex logic | Combined with `and`/`or` | `if x > 0 and y < 10` |
| Type checking | `isinstance`, type assertions | `if isinstance(x, int)` |
| Existence check | `is None`, `nil`, `Option` | `if x is not None` |

### Choosing Between Patterns

**Python:**
```python
# Use if-elif-else for mutually exclusive conditions
def get_grade(score):
    if score >= 90:
        return 'A'
    elif score >= 80:
        return 'B'
    elif score >= 70:
        return 'C'
    else:
        return 'F'

# Use match (Python 3.10+) for pattern matching
def process_command(cmd):
    match cmd:
        case ["quit"]:
            return "quitting"
        case ["load", filename]:
            return f"loading {filename}"
        case ["save", filename, mode]:
            return f"saving {filename} in {mode} mode"
        case _:
            return "unknown command"

# Use dictionary dispatch for dynamic conditions
def calculate(operation, a, b):
    operations = {
        'add': lambda x, y: x + y,
        'sub': lambda x, y: x - y,
        'mul': lambda x, y: x * y,
        'div': lambda x, y: x / y if y != 0 else None,
    }
    return operations.get(operation, lambda x, y: None)(a, b)
```

**Rust:**
```rust
// Use match for exhaustive pattern matching
fn get_grade(score: i32) -> char {
    match score {
        90..=100 => 'A',
        80..=89 => 'B',
        70..=79 => 'C',
        _ => 'F',
    }
}

// Use if-else for simple conditions
fn is_valid_age(age: i32) -> bool {
    age >= 0 && age <= 150
}

// Use match with enums for type-safe state
enum Command {
    Quit,
    Load(String),
    Save(String, String),
}

fn process_command(cmd: Command) -> String {
    match cmd {
        Command::Quit => "quitting".to_string(),
        Command::Load(filename) => format!("loading {}", filename),
        Command::Save(filename, mode) => {
            format!("saving {} in {} mode", filename, mode)
        }
    }
}
```

**Go:**
```go
// Use if-else for simple conditions
func getGrade(score int) string {
    if score >= 90 {
        return "A"
    } else if score >= 80 {
        return "B"
    } else if score >= 70 {
        return "C"
    }
    return "F"
}

// Use switch for multiple conditions
func getDayType(day string) string {
    switch day {
    case "Saturday", "Sunday":
        return "weekend"
    case "Monday", "Tuesday", "Wednesday", "Thursday", "Friday":
        return "weekday"
    default:
        return "invalid"
    }
}

// Use map for dynamic dispatch
func calculate(operation string, a, b float64) (float64, error) {
    operations := map[string]func(float64, float64) float64{
        "add": func(x, y float64) float64 { return x + y },
        "sub": func(x, y float64) float64 { return x - y },
        "mul": func(x, y float64) float64 { return x * y },
    }
    
    if op, exists := operations[operation]; exists {
        return op(a, b), nil
    }
    return 0, fmt.Errorf("unknown operation: %s", operation)
}
```

---

## <a name="scenarios"></a>4. Common DSA Scenarios

### Scenario 1: Binary Search Conditions

**Python:**
```python
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    
    while left <= right:  # <= because we need to check when left == right
        mid = left + (right - left) // 2  # Prevent overflow
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1  # +1 because mid is not the answer
        else:
            right = mid - 1  # -1 because mid is not the answer
    
    return -1

# Find first occurrence
def binary_search_first(arr, target):
    left, right = 0, len(arr) - 1
    result = -1
    
    while left <= right:
        mid = left + (right - left) // 2
        
        if arr[mid] == target:
            result = mid
            right = mid - 1  # Continue searching left
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return result
```

**Rust:**
```rust
fn binary_search(arr: &[i32], target: i32) -> Option<usize> {
    let mut left = 0;
    let mut right = arr.len();
    
    while left < right {  // < because right is exclusive
        let mid = left + (right - left) / 2;
        
        match arr[mid].cmp(&target) {
            std::cmp::Ordering::Equal => return Some(mid),
            std::cmp::Ordering::Less => left = mid + 1,
            std::cmp::Ordering::Greater => right = mid,
        }
    }
    
    None
}

fn binary_search_first(arr: &[i32], target: i32) -> Option<usize> {
    let mut left = 0;
    let mut right = arr.len();
    let mut result = None;
    
    while left < right {
        let mid = left + (right - left) / 2;
        
        match arr[mid].cmp(&target) {
            std::cmp::Ordering::Equal => {
                result = Some(mid);
                right = mid;  // Continue searching left
            }
            std::cmp::Ordering::Less => left = mid + 1,
            std::cmp::Ordering::Greater => right = mid,
        }
    }
    
    result
}
```

**Go:**
```go
func binarySearch(arr []int, target int) int {
    left, right := 0, len(arr)-1
    
    for left <= right {
        mid := left + (right-left)/2
        
        if arr[mid] == target {
            return mid
        } else if arr[mid] < target {
            left = mid + 1
        } else {
            right = mid - 1
        }
    }
    
    return -1
}

func binarySearchFirst(arr []int, target int) int {
    left, right := 0, len(arr)-1
    result := -1
    
    for left <= right {
        mid := left + (right-left)/2
        
        if arr[mid] == target {
            result = mid
            right = mid - 1  // Continue searching left
        } else if arr[mid] < target {
            left = mid + 1
        } else {
            right = mid - 1
        }
    }
    
    return result
}
```

---

### Scenario 2: Graph Traversal Conditions

**Python:**
```python
def dfs_recursive(graph, node, visited, path):
    # Base case: already visited
    if node in visited:
        return
    
    visited.add(node)
    path.append(node)
    
    # Process neighbors
    for neighbor in graph.get(node, []):
        if neighbor not in visited:  # Only visit unvisited
            dfs_recursive(graph, neighbor, visited, path)

def bfs(graph, start):
    from collections import deque
    
    if start not in graph:  # Validate start node
        return []
    
    visited = {start}
    queue = deque([start])
    result = []
    
    while queue:  # Continue while queue has elements
        node = queue.popleft()
        result.append(node)
        
        for neighbor in graph.get(node, []):
            if neighbor not in visited:  # Avoid cycles
                visited.add(neighbor)
                queue.append(neighbor)
    
    return result

# Detect cycle in directed graph
def has_cycle(graph):
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
        
        color[node] = BLACK  # Mark as fully processed
        return False
    
    return any(dfs(node) for node in graph if color[node] == WHITE)
```

**Rust:**
```rust
use std::collections::{HashMap, HashSet, VecDeque};

fn dfs_recursive(
    graph: &HashMap<i32, Vec<i32>>,
    node: i32,
    visited: &mut HashSet<i32>,
    path: &mut Vec<i32>,
) {
    if visited.contains(&node) {
        return;
    }
    
    visited.insert(node);
    path.push(node);
    
    if let Some(neighbors) = graph.get(&node) {
        for &neighbor in neighbors {
            if !visited.contains(&neighbor) {
                dfs_recursive(graph, neighbor, visited, path);
            }
        }
    }
}

fn bfs(graph: &HashMap<i32, Vec<i32>>, start: i32) -> Vec<i32> {
    if !graph.contains_key(&start) {
        return Vec::new();
    }
    
    let mut visited = HashSet::new();
    let mut queue = VecDeque::new();
    let mut result = Vec::new();
    
    visited.insert(start);
    queue.push_back(start);
    
    while let Some(node) = queue.pop_front() {
        result.push(node);
        
        if let Some(neighbors) = graph.get(&node) {
            for &neighbor in neighbors {
                if !visited.contains(&neighbor) {
                    visited.insert(neighbor);
                    queue.push_back(neighbor);
                }
            }
        }
    }
    
    result
}

#[derive(PartialEq)]
enum Color { White, Gray, Black }

fn has_cycle(graph: &HashMap<i32, Vec<i32>>) -> bool {
    let mut color: HashMap<i32, Color> = 
        graph.keys().map(|&k| (k, Color::White)).collect();
    
    fn dfs(
        node: i32,
        graph: &HashMap<i32, Vec<i32>>,
        color: &mut HashMap<i32, Color>,
    ) -> bool {
        if color[&node] == Color::Gray {
            return true;  // Back edge
        }
        if color[&node] == Color::Black {
            return false;  // Already processed
        }
        
        color.insert(node, Color::Gray);
        
        if let Some(neighbors) = graph.get(&node) {
            for &neighbor in neighbors {
                if dfs(neighbor, graph, color) {
                    return true;
                }
            }
        }
        
        color.insert(node, Color::Black);
        false
    }
    
    graph.keys().any(|&node| {
        color[&node] == Color::White && dfs(node, graph, &mut color)
    })
}
```

**Go:**
```go
func dfsRecursive(graph map[int][]int, node int, visited map[int]bool, path *[]int) {
    if visited[node] {
        return
    }
    
    visited[node] = true
    *path = append(*path, node)
    
    for _, neighbor := range graph[node] {
        if !visited[neighbor] {
            dfsRecursive(graph, neighbor, visited, path)
        }
    }
}

func bfs(graph map[int][]int, start int) []int {
    if _, exists := graph[start]; !exists {
        return []int{}
    }
    
    visited := make(map[int]bool)
    queue := []int{start}
    result := []int{}
    visited[start] = true
    
    for len(queue) > 0 {
        node := queue[0]
        queue = queue[1:]
        result = append(result, node)
        
        for _, neighbor := range graph[node] {
            if !visited[neighbor] {
                visited[neighbor] = true
                queue = append(queue, neighbor)
            }
        }
    }
    
    return result
}

const (
    white = 0
    gray  = 1
    black = 2
)

func hasCycle(graph map[int][]int) bool {
    color := make(map[int]int)
    for node := range graph {
        color[node] = white
    }
    
    var dfs func(int) bool
    dfs = func(node int) bool {
        if color[node] == gray {
            return true  // Back edge found
        }
        if color[node] == black {
            return false  // Already processed
        }
        
        color[node] = gray
        
        for _, neighbor := range graph[node] {
            if dfs(neighbor) {
                return true
            }
        }
        
        color[node] = black
        return false
    }
    
    for node := range graph {
        if color[node] == white && dfs(node) {
            return true
        }
    }
    
    return false
}
```

---

### Scenario 3: Dynamic Programming Conditions

**Python:**
```python
def longest_common_subsequence(text1, text2):
    m, n = len(text1), len(text2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            # Key condition: characters match or not
            if text1[i-1] == text2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    return dp[m][n]

def can_partition(nums):
    total = sum(nums)
    
    # Early termination: odd sum cannot be split equally
    if total % 2 != 0:
        return False
    
    target = total // 2
    dp = [False] * (target + 1)
    dp[0] = True  # Base case: sum of 0 is always achievable
    
    for num in nums:
        # Traverse backwards to avoid using same element twice
        for j in range(target, num - 1, -1):
            # Can we make sum j?
            if dp[j - num]:  # If we can make (j - num)
                dp[j] = True
    
    return dp[target]

def coin_change(coins, amount):
    if amount == 0:
        return 0
    
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0
    
    for coin in coins:
        for i in range(coin, amount + 1):
            # Only update if previous state is reachable
            if dp[i - coin] != float('inf'):
                dp[i] = min(dp[i], dp[i - coin] + 1)
    
    return dp[amount] if dp[amount] != float('inf') else -1
```

**Rust:**
```rust
fn longest_common_subsequence(text1: &str, text2: &str) -> i32 {
    let chars1: Vec<char> = text1.chars().collect();
    let chars2: Vec<char> = text2.chars().collect();
    let (m, n) = (chars1.len(), chars2.len());
    
    let mut dp = vec![vec![0; n + 1]; m + 1];
    
    for i in 1..=m {
        for j in 1..=n {
            if chars1[i-1] == chars2[j-1] {
                dp[i][j] = dp[i-1][j-1] + 1;
            } else {
                dp[i][j] = dp[i-1][j].max(dp[i][j-1]);
            }
        }
    }
    
    dp[m][n]
}

fn can_partition(nums: Vec<i32>) -> bool {
    let total: i32 = nums.iter().sum();
    
    if total % 2 != 0 {
        return false;
    }
    
    let target = (total / 2) as usize;
    let mut dp = vec![false; target + 1];
    dp[0] = true;
    
    for &num in &nums {
        let num = num as usize;
        for j in (num..=target).rev() {
            if dp[j - num] {
                dp[j] = true;
            }
        }
    }
    
    dp[target]
}

fn coin_change(coins: Vec<i32>, amount: i32) -> i32 {
    if amount == 0 {
        return 0;
    }
    
    let amount = amount as usize;
    let mut dp = vec![i32::MAX; amount + 1];
    dp[0] = 0;
    
    for &coin in &coins {
        let coin = coin as usize;
        for i in coin..=amount {
            if dp[i - coin] != i32::MAX {
                dp[i] = dp[i].min(dp[i - coin] + 1);
            }
        }
    }
    
    if dp[amount] == i32::MAX { -1 } else { dp[amount] }
}
```

**Go:**
```go
func longestCommonSubsequence(text1, text2 string) int {
    m, n := len(text1), len(text2)
    dp := make([][]int, m+1)
    for i := range dp {
        dp[i] = make([]int, n+1)
    }
    
    for i := 1; i <= m; i++ {
        for j := 1; j <= n; j++ {
            if text1[i-1] == text2[j-1] {
                dp[i][j] = dp[i-1][j-1] + 1
            } else {
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
            }
        }
    }
    
    return dp[m][n]
}

func canPartition(nums []int) bool {
    total := 0
    for _, num := range nums {
        total += num
    }
    
    if total%2 != 0 {
        return false
    }
    
    target := total / 2
    dp := make([]bool, target+1)
    dp[0] = true
    
    for _, num := range nums {
        for j := target; j >= num; j-- {
            if dp[j-num] {
                dp[j] = true
            }
        }
    }
    
    return dp[target]
}

func coinChange(coins []int, amount int) int {
    if amount == 0 {
        return 0
    }
    
    dp := make([]int, amount+1)
    for i := range dp {
        dp[i] = amount + 1  // Use as infinity
    }
    dp[0] = 0
    
    for _, coin := range coins {
        for i := coin; i <= amount; i++ {
            if dp[i-coin] != amount+1 {
                dp[i] = min(dp[i], dp[i-coin]+1)
            }
        }
    }
    
    if dp[amount] > amount {
        return -1
    }
    return dp[amount]
}

func max(a, b int) int {
    if a > b {
        return a
    }
    return b
}

func min(a, b int) int {
    if a < b {
        return a
    }
    return b
}
```

---

## <a name="advanced"></a>5. Advanced Techniques

### Technique 1: Short-Circuit Evaluation

**Python:**
```python
# Use short-circuit for performance
def validate_and_process(data):
    # If data is None, second condition never evaluates
    if data is not None and len(data) > 0:
        return process(data)
    return None

# Avoid expensive computation when possible
def complex_check(x):
    # cheap_check() runs first; if False, expensive_check() never runs
    return cheap_check(x) and expensive_check(x)

# Use 'or' for default values
def get_value(config):
    return config.get('value') or default_value()
```

**Rust:**
```rust
fn validate_and_process(data: Option<&Vec<i32>>) -> Option<Vec<i32>> {
    // Pattern matching naturally short-circuits
    data.filter(|d| !d.is_empty())
        .map(|d| process(d))
}

fn complex_check(x: i32) -> bool {
    cheap_check(x) && expensive_check(x)
}

// Use unwrap_or_else for lazy evaluation
fn get_value(config: &Config) -> Value {
    config.get('value')
        .unwrap_or_else(|| default_value())  // Only called if None
}
```

**Go:**
```go
func validateAndProcess(data []int) []int {
    // Go evaluates left to right with short-circuit
    if data != nil && len(data) > 0 {
        return process(data)
    }
    return nil
}

func complexCheck(x int) bool {
    return cheapCheck(x) && expensiveCheck(x)
}

// Explicit default value handling
func getValue(config map[string]Value) Value {
    if val, ok := config["value"]; ok {
        return val
    }
    return defaultValue()
}
```

---

### Technique 2: State Machines

**Python:**
```python
from enum import Enum

class State(Enum):
    IDLE = 1
    PROCESSING = 2
    ERROR = 3
    COMPLETE = 4

class StateMachine:
    def __init__(self):
        self.state = State.IDLE
        self.transitions = {
            State.IDLE: {
                'start': State.PROCESSING,
            },
            State.PROCESSING: {
                'success': State.COMPLETE,
                'error': State.ERROR,
            },
            State.ERROR: {
                'retry': State.PROCESSING,
                'abort': State.IDLE,
            },
            State.COMPLETE: {
                'reset': State.IDLE,
            }
        }
    
    def transition(self, event):
        if self.state in self.transitions:
            if event in self.transitions[self.state]:
                self.state = self.transitions[self.state][event]
                return True
        return False
```

**Rust:**
```rust
#[derive(Debug, PartialEq, Clone)]
enum State {
    Idle,
    Processing,
    Error,
    Complete,
}

enum Event {
    Start,
    Success,
    Error,
    Retry,
    Abort,
    Reset,
}

struct StateMachine {
    state: State,
}

impl StateMachine {
    fn new() -> Self {
        Self { state: State::Idle }
    }
    
    fn transition(&mut self, event: Event) -> bool {
        let next_state = match (&self.state, event) {
            (State::Idle, Event::Start) => Some(State::Processing),
            (State::Processing, Event::Success) => Some(State::Complete),
            (State::Processing, Event::Error) => Some(State::Error),
            (State::Error, Event::Retry) => Some(State::Processing),
            (State::Error, Event::Abort) => Some(State::Idle),
            (State::Complete, Event::Reset) => Some(State::Idle),
            _ => None,
        };
        
        match next_state {
            Some(state) => {
                self.state = state;
                true
            }
            None => false,
        }
    }
}
```

**Go:**
```go
type State int

const (
    Idle State = iota
    Processing
    Error
    Complete
)

type Event string

const (
    Start   Event = "start"
    Success Event = "success"
    ErrorEv Event = "error"
    Retry   Event = "retry"
    Abort   Event = "abort"
    Reset   Event = "reset"
)

type StateMachine struct {
    state       State
    transitions map[State]map[Event]State
}

func NewStateMachine() *StateMachine {
    return &StateMachine{
        state: Idle,
        transitions: map[State]map[Event]State{
            Idle: {
                Start: Processing,
            },
            Processing: {
                Success: Complete,
                ErrorEv: Error,
            },
            Error: {
                Retry: Processing,
                Abort: Idle,
            },
            Complete: {
                Reset: Idle,
            },
        },
    }
}

func (sm *StateMachine) Transition(event Event) bool {
    if transitions, ok := sm.transitions[sm.state]; ok {
        if nextState, ok := transitions[event]; ok {
            sm.state = nextState
            return true
        }
    }
    return false
}
```

---

## <a name="antipatterns"></a>6. Anti-Patterns to Avoid

### Anti-Pattern 1: Magic Numbers

**BAD:**
```python
def process_age(age):
    if age < 18:
        return "minor"
    elif age < 65:
        return "adult"
    else:
        return "senior"
```

**GOOD:**
```python
MIN_ADULT_AGE = 18
MIN_SENIOR_AGE = 65

def process_age(age):
    if age < MIN_ADULT_AGE:
        return "minor"
    elif age < MIN_SENIOR_AGE:
        return "adult"
    else:
        return "senior"
```

---

### Anti-Pattern 2: Boolean Blindness

**BAD:**
```python
def validate_user(user):
    return True, None  # What does True mean here?

success, error = validate_user(user)
```

**GOOD:**
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class ValidationResult:
    is_valid: bool
    error: Optional[str] = None

def validate_user(user) -> ValidationResult:
    if not user.email:
        return ValidationResult(False, "Email required")
    return ValidationResult(True)
```

---

### Anti-Pattern 3: Deeply Nested Conditions

**BAD:**
```python
def process(data):
    if data:
        if 'key' in data:
            if data['key'] > 0:
                if data['key'] < 100:
                    return data['key'] * 2
    return 0
```

**GOOD:**
```python
def process(data):
    if not data:
        return 0
    if 'key' not in data:
        return 0
    
    value = data['key']
    if value <= 0 or value >= 100:
        return 0
    
    return value * 2
```

---

## Summary: The Elite Mindset

1. **Think in states, not just values**: What state is the system in? What transitions are valid?

2. **Order conditions by:**
   - Likelihood (most common first)
   - Cost (cheapest checks first)
   - Dependencies (check prerequisites before dependent conditions)

3. **Prefer explicitness over cleverness**: Code is read more than written.

4. **Use the type system**: Let the compiler catch errors (especially in Rust).

5. **Test edge cases systematically:**
   - Empty inputs
   - Single element
   - Boundaries (0, -1, max values)
   - Null/None/nil
   - Duplicates

6. **Refactor complex conditions into functions** with descriptive names.

7. **Document non-obvious conditions** with comments explaining WHY, not WHAT.

I'll create a comprehensive guide on mastering conditional logic for elite software engineers, with examples in Rust, Python, and Go.I've created a comprehensive guide for mastering conditional logic in DSA problems! Here are the key takeaways:

## Core Principles for Elite Engineers:

**1. The Three Questions Framework**
- What am I checking? (boundary, state, optimization)
- What are the consequences of true/false?
- Can this be simplified?

**2. Condition Ordering Strategy**
Order by:
- **Likelihood** - Check common cases first
- **Cost** - Cheap validations before expensive ones
- **Dependencies** - Prerequisites before dependent checks

**3. Pattern Recognition**
The guide covers critical patterns:
- **Boundary checking** (array access, two-pointers)
- **State validation** (preconditions, invariants)
- **Guard clauses** (reduce nesting with early returns)
- **Short-circuit evaluation** (performance optimization)

**4. Key Decision Matrix**

| When | Use |
|------|-----|
| Single value | `==`, `!=` |
| Range | `<`, `>`, `<=`, `>=` |
| Multiple possibilities | `match`/`switch`/`in` |
| Complex logic | Combined with `&&`/`||` |
| Type safety | Pattern matching (Rust), `isinstance` (Python) |

**5. Critical DSA Scenarios Covered**
- Binary search (why `<=` vs `<`, `+1` vs `-1`)
- Graph traversal (cycle detection, visited checks)
- Dynamic programming (state transitions, base cases)

**The Elite Mindset**: Think in **states and transitions**, not just values. Every condition should have a clear purpose that you can articulate. If you can't explain why a condition exists, it probably shouldn't.

The guide includes production-ready examples in all three languages with proper error handling, type safety, and idiomatic patterns for each language!

Excellent, Sushin. You’re asking the *real* engineer’s question: not “how do I write a condition,” but **how do I *choose* the right condition to drive logic in real-world systems?**  
This is the difference between a coder and an architect. Let’s build a **comprehensive elite guide**.

---

# 🧭 1. The Decision Framework: Choosing Conditions

Conditions are the **guardians of control flow**. Choosing the right one depends on:

| Condition Type | When to Use | Mental Model |
|----------------|-------------|--------------|
| **Equality / Inequality (`==`, `!=`)** | Exact matches, sentinel values, state checks. | Door lock: either the key fits or it doesn’t. |
| **Relational (`<`, `>`, `<=`, `>=`)** | Ranges, thresholds, bounds. | Thermostat: trigger when temp crosses a limit. |
| **Membership / Containment** | Check if element belongs to a set, list, map. | Guest list at a gala: is the name invited? |
| **Boolean flags** | Simple on/off states. | Light switch. |
| **Compound (`&&`, `||`, `!`)** | Multiple conditions combined. | Gate with multiple locks: all must open, or at least one. |
| **Pattern matching / guards** | Complex state machines, enums, tagged unions. | Sorting hat: different houses based on traits. |
| **Short-circuit conditions** | Expensive checks only if needed. | Guard dog: only barks if someone enters. |

---

# 🧠 2. Memory Model & Call Semantics

Elite engineers don’t just check conditions—they **map them to data representation**:

- **Stack vs Heap**:  
  - Comparing small scalars (ints, floats, bools) → stack-level, cheap.  
  - Comparing heap objects (strings, vectors, structs) → may involve pointer deref, deep equality.  

- **Value vs Reference**:  
  - Rust: `==` may move or borrow; prefer `&x == &y` for non-copy types.  
  - Python: `==` checks value equality, `is` checks identity (pointer equality).  
  - Go: `==` works on comparable types; slices and maps cannot be compared directly except with `nil`.  

---

# ⚙️ 3. Language-Specific Idioms

### **Rust**
```rust
// Equality
if user_id == 42 {
    println!("Admin user");
}

// Relational
if temperature > 100.0 {
    println!("Overheating!");
}

// Membership (using collections)
if set.contains(&value) {
    println!("Found in set");
}

// Pattern matching
match request {
    Request::Get(url) if url.starts_with("https") => println!("Secure GET"),
    Request::Post(_) => println!("POST request"),
    _ => println!("Other"),
}
```

**Elite tip**: Rust’s `match` with guards is the most expressive, safe way to encode complex conditions.

---

### **Python**
```python
# Equality
if user_id == 42:
    print("Admin user")

# Relational
if temperature > 100.0:
    print("Overheating!")

# Membership
if value in my_set:
    print("Found in set")

# Compound
if is_logged_in and not is_banned:
    print("Access granted")
```

**Elite tip**: Use `in` for readability; avoid chaining `and/or` with side effects.

---

### **Go**
```go
// Equality
if userID == 42 {
    fmt.Println("Admin user")
}

// Relational
if temperature > 100.0 {
    fmt.Println("Overheating!")
}

// Compound
if loggedIn && !banned {
    fmt.Println("Access granted")
}

// Switch (Go’s pattern-like)
switch req := request.(type) {
case GetRequest:
    fmt.Println("GET", req.URL)
case PostRequest:
    fmt.Println("POST")
default:
    fmt.Println("Other")
}
```

**Elite tip**: Go’s `switch` is more powerful than many realize—use it instead of long `if-else` chains.

---

# 🏆 4. Elite Heuristics

- **Clarity first**: Write the condition so the *intent* is obvious.  
- **Guard clauses**: Instead of deep nesting, exit early with conditions.  
- **Short-circuit expensive checks**: Put cheap conditions first in `&&` chains.  
- **Use domain language**: Wrap conditions in functions like `is_admin(user)` instead of `user.id == 42`.  
- **Pattern matching > nested ifs**: In Rust (and Go’s `switch`), prefer declarative matching.  
- **Avoid “boolean blindness”**: Don’t pass raw booleans around; use enums or descriptive flags.  

---

# 🌌 Fantasy Anchor (for you)

Think of conditions as **celestial gates**:

- **Equality** → a star gate that opens only with the exact rune.  
- **Relational** → a moon phase: only visible when threshold is crossed.  
- **Membership** → constellation membership: is this star part of Orion?  
- **Pattern matching** → the cosmic oracle: destiny branches based on traits.  

---

✅ **Summary for elite engineers**:  
- Start with **intent**: exact match, threshold, membership, or state machine.  
- Map to **data semantics**: stack vs heap, value vs reference.  
- Use **language idioms**: Rust `match`, Python `in`, Go `switch`.  
- Optimize for **clarity, performance, and maintainability**.  

---

Would you like me to now create a **side-by-side visual flow diagram** (Rust `match`, Python `if/elif`, Go `switch`) showing how conditions branch in memory and control flow? That would give you a single mental image to anchor all three languages.
