Perfect! Now let me provide additional advanced concepts and optimization techniques:

---

## 5. Advanced Concepts & Optimizations

### **Time and Space Complexity**

| Operation | Time Complexity | Space Complexity | Notes |
|-----------|----------------|------------------|-------|
| Permutations(n) | O(n × n!) | O(n × n!) | Factorial growth - use carefully |
| Combinations(n,k) | O(C(n,k) × k) | O(C(n,k) × k) | Better than permutations |
| Subsets(n) | O(n × 2^n) | O(n × 2^n) | Exponential but manageable |

### **Key Optimization Strategies**

1. **Early Pruning**: Stop branches that can't lead to valid solutions
2. **Memoization**: Cache intermediate results to avoid recomputation
3. **Iterative Solutions**: Use loops instead of recursion when possible
4. **Bit Manipulation**: Fastest for subsets, O(1) subset check

### **Python: Advanced Optimizations**

```python
from functools import lru_cache
import itertools

# Optimization 1: Generate permutations lazily (memory efficient)
def permutations_generator(arr):
    """Memory-efficient generator for large datasets"""
    if len(arr) <= 1:
        yield arr
    else:
        for i, item in enumerate(arr):
            for p in permutations_generator(arr[:i] + arr[i+1:]):
                yield [item] + p

# Optimization 2: Next permutation (in-place, O(n) time)
def next_permutation(arr):
    """
    Generate next lexicographic permutation in-place.
    Real-world use: Iterate through all permutations without storing them.
    """
    # Find the largest index i such that arr[i] < arr[i + 1]
    i = len(arr) - 2
    while i >= 0 and arr[i] >= arr[i + 1]:
        i -= 1
    
    if i == -1:
        return False  # Already at last permutation
    
    # Find the largest index j > i such that arr[i] < arr[j]
    j = len(arr) - 1
    while arr[j] <= arr[i]:
        j -= 1
    
    # Swap
    arr[i], arr[j] = arr[j], arr[i]
    
    # Reverse the suffix starting at arr[i + 1]
    arr[i + 1:] = reversed(arr[i + 1:])
    return True

# Optimization 3: Combinations with early termination
def combinations_with_sum(arr, k, target_sum):
    """
    Find k-combinations that sum to target.
    Uses pruning to skip impossible branches.
    """
    arr.sort()  # Sort for pruning
    result = []
    
    def backtrack(start, path, current_sum):
        if len(path) == k:
            if current_sum == target_sum:
                result.append(path[:])
            return
        
        remaining_slots = k - len(path)
        for i in range(start, len(arr)):
            # Prune: if minimum possible sum exceeds target, stop
            min_possible = current_sum + sum(arr[i:i+remaining_slots])
            if min_possible > target_sum:
                break
            
            # Prune: if maximum possible sum is less than target, skip
            max_possible = current_sum + sum(arr[len(arr)-remaining_slots:])
            if max_possible < target_sum:
                continue
            
            path.append(arr[i])
            backtrack(i + 1, path, current_sum + arr[i])
            path.pop()
    
    backtrack(0, [], 0)
    return result

# Optimization 4: Subset sum with dynamic programming
def subset_sum_dp(arr, target):
    """
    Find if any subset sums to target using DP.
    Time: O(n × target), Space: O(target)
    """
    dp = [False] * (target + 1)
    dp[0] = True  # Empty subset sums to 0
    
    for num in arr:
        # Traverse backwards to avoid using same element twice
        for s in range(target, num - 1, -1):
            dp[s] = dp[s] or dp[s - num]
    
    return dp[target]

# Real-world application: Cryptocurrency Portfolio Rebalancing
def rebalance_crypto_portfolio(holdings, target_value, max_trades):
    """
    Find optimal combination of trades to reach target portfolio value.
    Real-world use: Automated trading, portfolio management
    """
    from itertools import combinations
    
    # holdings: {coin: (current_amount, current_price)}
    # Generate all possible trade combinations
    coins = list(holdings.keys())
    best_combo = None
    best_diff = float('inf')
    
    for r in range(1, min(max_trades + 1, len(coins) + 1)):
        for combo in combinations(coins, r):
            # Calculate if selling these coins gets us close to target
            sale_value = sum(holdings[coin][0] * holdings[coin][1] 
                           for coin in combo)
            diff = abs(sale_value - target_value)
            
            if diff < best_diff:
                best_diff = diff
                best_combo = combo
    
    return best_combo, best_diff

# Usage example
holdings = {
    'BTC': (0.5, 45000),   # 0.5 BTC at $45k
    'ETH': (10, 3000),     # 10 ETH at $3k
    'SOL': (100, 150),     # 100 SOL at $150
    'ADA': (5000, 0.50)    # 5000 ADA at $0.50
}

coins_to_sell, difference = rebalance_crypto_portfolio(holdings, 25000, 2)
print(f"Sell: {coins_to_sell}")
print(f"Difference from target: ${difference:.2f}")
```

---

## 6. Common Pitfalls & Best Practices

### **Pitfalls to Avoid**

```python
# ❌ BAD: Creating all permutations for large n
def bad_approach(arr):
    if len(arr) > 10:  # 10! = 3,628,800 permutations
        all_perms = list(permutations(arr))  # Memory explosion!
        return process(all_perms)

# ✅ GOOD: Use generator or early termination
def good_approach(arr):
    for perm in permutations_generator(arr):
        if is_valid(perm):
            return perm  # Stop at first valid solution
```

### **Best Practices**

1. **Estimate before generating**: Calculate C(n,k) or n! first
2. **Use built-in libraries**: `itertools` in Python is highly optimized
3. **Consider alternatives**: Sometimes greedy algorithms suffice
4. **Set limits**: Cap the maximum number of results
5. **Use generators**: For large datasets, yield instead of storing

---

## 7. Interview-Style Problems

### **Problem 1: Phone Number Mnemonics**
```python
def letter_combinations(digits: str) -> List[str]:
    """
    Given digits, return all possible letter combinations.
    Phone mapping: 2=abc, 3=def, 4=ghi, 5=jkl, 6=mno, 7=pqrs, 8=tuv, 9=wxyz
    
    Example: "23" -> ["ad","ae","af","bd","be","bf","cd","ce","cf"]
    Real-world: T9 predictive text, vanity phone numbers
    """
    if not digits:
        return []
    
    phone = {
        '2': 'abc', '3': 'def', '4': 'ghi', '5': 'jkl',
        '6': 'mno', '7': 'pqrs', '8': 'tuv', '9': 'wxyz'
    }
    
    result = []
    
    def backtrack(index, path):
        if index == len(digits):
            result.append(''.join(path))
            return
        
        for letter in phone[digits[index]]:
            path.append(letter)
            backtrack(index + 1, path)
            path.pop()
    
    backtrack(0, [])
    return result
```

### **Problem 2: N-Queens**
```python
def solve_n_queens(n: int) -> List[List[str]]:
    """
    Place n queens on n×n board so none attack each other.
    Real-world: Resource allocation, scheduling with constraints
    """
    result = []
    board = [['.'] * n for _ in range(n)]
    
    def is_valid(row, col):
        # Check column
        for i in range(row):
            if board[i][col] == 'Q':
                return False
        
        # Check diagonal
        i, j = row - 1, col - 1
        while i >= 0 and j >= 0:
            if board[i][j] == 'Q':
                return False
            i -= 1
            j -= 1
        
        # Check anti-diagonal
        i, j = row - 1, col + 1
        while i >= 0 and j < n:
            if board[i][j] == 'Q':
                return False
            i -= 1
            j += 1
        
        return True
    
    def backtrack(row):
        if row == n:
            result.append([''.join(r) for r in board])
            return
        
        for col in range(n):
            if is_valid(row, col):
                board[row][col] = 'Q'
                backtrack(row + 1)
                board[row][col] = '.'
    
    backtrack(0)
    return result
```

---

## 8. Performance Comparison

Here's a quick performance test you can run:

```python
import time
from itertools import permutations as iter_perms

def benchmark():
    test_sizes = [5, 7, 8, 9]
    
    print("Performance Comparison (Permutations):")
    print("n  | Custom    | itertools | Ratio")
    print("-" * 45)
    
    for n in test_sizes:
        arr = list(range(n))
        
        # Custom implementation
        start = time.time()
        custom = list(generate_permutations(arr))
        custom_time = time.time() - start
        
        # itertools
        start = time.time()
        builtin = list(iter_perms(arr))
        builtin_time = time.time() - start
        
        ratio = custom_time / builtin_time if builtin_time > 0 else 0
        
        print(f"{n:2d} | {custom_time:.4f}s | {builtin_time:.4f}s | {ratio:.2f}x")

# Run benchmark
benchmark()
```

---

## Key Takeaways

1. **Permutations**: Use when order matters (scheduling, arrangements)
2. **Combinations**: Use when order doesn't matter (team selection, portfolios)
3. **Subsets**: Use for all possible selections (feature selection, power sets)
4. **Always consider**: Time/space complexity before generating
5. **Optimize**: Use pruning, memoization, and generators
6. **Real-world**: These patterns appear everywhere in CS and business problems

The code examples in Python, Rust, and Go provide production-ready implementations you can adapt to your specific use cases!

use std::collections::{HashSet, HashMap};

// ============================================
// CORE IMPLEMENTATIONS
// ============================================

/// Generate all permutations of a vector
pub fn permutations<T: Clone>(arr: &[T]) -> Vec<Vec<T>> {
    let mut result = Vec::new();
    let mut used = vec![false; arr.len()];
    let mut path = Vec::new();
    
    fn backtrack<T: Clone>(
        arr: &[T],
        used: &mut Vec<bool>,
        path: &mut Vec<T>,
        result: &mut Vec<Vec<T>>
    ) {
        if path.len() == arr.len() {
            result.push(path.clone());
            return;
        }
        
        for i in 0..arr.len() {
            if !used[i] {
                used[i] = true;
                path.push(arr[i].clone());
                backtrack(arr, used, path, result);
                path.pop();
                used[i] = false;
            }
        }
    }
    
    backtrack(arr, &mut used, &mut path, &mut result);
    result
}

/// Generate all k-length combinations
pub fn combinations<T: Clone>(arr: &[T], k: usize) -> Vec<Vec<T>> {
    let mut result = Vec::new();
    let mut path = Vec::new();
    
    fn backtrack<T: Clone>(
        arr: &[T],
        k: usize,
        start: usize,
        path: &mut Vec<T>,
        result: &mut Vec<Vec<T>>
    ) {
        if path.len() == k {
            result.push(path.clone());
            return;
        }
        
        for i in start..arr.len() {
            path.push(arr[i].clone());
            backtrack(arr, k, i + 1, path, result);
            path.pop();
        }
    }
    
    backtrack(arr, k, 0, &mut path, &mut result);
    result
}

/// Generate all subsets using bit manipulation
pub fn subsets<T: Clone>(arr: &[T]) -> Vec<Vec<T>> {
    let n = arr.len();
    let total = 1 << n; // 2^n
    let mut result = Vec::with_capacity(total);
    
    for mask in 0..total {
        let mut subset = Vec::new();
        for i in 0..n {
            if mask & (1 << i) != 0 {
                subset.push(arr[i].clone());
            }
        }
        result.push(subset);
    }
    
    result
}

/// Generate subsets using backtracking (alternative)
pub fn subsets_backtrack<T: Clone>(arr: &[T]) -> Vec<Vec<T>> {
    let mut result = Vec::new();
    let mut path = Vec::new();
    
    fn backtrack<T: Clone>(
        arr: &[T],
        start: usize,
        path: &mut Vec<T>,
        result: &mut Vec<Vec<T>>
    ) {
        result.push(path.clone());
        
        for i in start..arr.len() {
            path.push(arr[i].clone());
            backtrack(arr, i + 1, path, result);
            path.pop();
        }
    }
    
    backtrack(arr, 0, &mut path, &mut result);
    result
}

// ============================================
// REAL-WORLD CHALLENGE 1: SCHEDULING OPTIMIZER
// ============================================

#[derive(Debug, Clone)]
pub struct Task {
    pub id: String,
    pub duration: u32, // minutes
    pub priority: u32,
    pub dependencies: Vec<String>,
}

#[derive(Debug, Clone)]
pub struct Schedule {
    pub tasks: Vec<String>,
    pub total_time: u32,
    pub priority_score: u32,
}

/// Find optimal task schedules respecting dependencies
/// Real-world use: Project management, CPU scheduling, workflow optimization
pub fn optimize_schedule(tasks: &[Task], max_time: u32) -> Vec<Schedule> {
    let mut valid_schedules = Vec::new();
    
    // Create dependency map
    let dep_map: HashMap<String, Vec<String>> = tasks
        .iter()
        .map(|t| (t.id.clone(), t.dependencies.clone()))
        .collect();
    
    fn can_schedule(task_id: &str, scheduled: &[String], dep_map: &HashMap<String, Vec<String>>) -> bool {
        if let Some(deps) = dep_map.get(task_id) {
            deps.iter().all(|dep| scheduled.contains(dep))
        } else {
            true
        }
    }
    
    fn backtrack(
        tasks: &[Task],
        used: &mut Vec<bool>,
        current_schedule: &mut Vec<String>,
        current_time: u32,
        current_priority: u32,
        max_time: u32,
        dep_map: &HashMap<String, Vec<String>>,
        valid_schedules: &mut Vec<Schedule>
    ) {
        // Save current valid schedule
        if !current_schedule.is_empty() {
            valid_schedules.push(Schedule {
                tasks: current_schedule.clone(),
                total_time: current_time,
                priority_score: current_priority,
            });
        }
        
        for i in 0..tasks.len() {
            if !used[i] && current_time + tasks[i].duration <= max_time {
                // Check if dependencies are met
                if can_schedule(&tasks[i].id, current_schedule, dep_map) {
                    used[i] = true;
                    current_schedule.push(tasks[i].id.clone());
                    
                    backtrack(
                        tasks,
                        used,
                        current_schedule,
                        current_time + tasks[i].duration,
                        current_priority + tasks[i].priority,
                        max_time,
                        dep_map,
                        valid_schedules
                    );
                    
                    current_schedule.pop();
                    used[i] = false;
                }
            }
        }
    }
    
    let mut used = vec![false; tasks.len()];
    let mut current_schedule = Vec::new();
    
    backtrack(
        tasks,
        &mut used,
        &mut current_schedule,
        0,
        0,
        max_time,
        &dep_map,
        &mut valid_schedules
    );
    
    // Sort by priority score (descending)
    valid_schedules.sort_by(|a, b| b.priority_score.cmp(&a.priority_score));
    valid_schedules
}

// ============================================
// REAL-WORLD CHALLENGE 2: NETWORK TOPOLOGY
// ============================================

#[derive(Debug, Clone)]
pub struct Node {
    pub id: usize,
    pub capacity: u32,
}

/// Generate all possible network topologies (connections) for n nodes
/// Real-world use: Network design, distributed systems, mesh networks
pub fn generate_network_topologies(nodes: &[Node], max_connections: usize) -> Vec<Vec<(usize, usize)>> {
    let n = nodes.len();
    let mut all_edges = Vec::new();
    
    // Generate all possible edges
    for i in 0..n {
        for j in (i + 1)..n {
            all_edges.push((nodes[i].id, nodes[j].id));
        }
    }
    
    let mut valid_topologies = Vec::new();
    
    // Generate all combinations of edges up to max_connections
    for k in 1..=max_connections.min(all_edges.len()) {
        let combos = combinations(&all_edges, k);
        
        for topology in combos {
            // Verify connectivity (all nodes reachable)
            if is_connected(&topology, n) {
                valid_topologies.push(topology);
            }
        }
    }
    
    valid_topologies
}

fn is_connected(edges: &[(usize, usize)], num_nodes: usize) -> bool {
    if edges.is_empty() {
        return false;
    }
    
    // Build adjacency list
    let mut adj: HashMap<usize, Vec<usize>> = HashMap::new();
    for &(u, v) in edges {
        adj.entry(u).or_insert_with(Vec::new).push(v);
        adj.entry(v).or_insert_with(Vec::new).push(u);
    }
    
    // DFS to check connectivity
    let mut visited = HashSet::new();
    let start = edges[0].0;
    let mut stack = vec![start];
    
    while let Some(node) = stack.pop() {
        if visited.insert(node) {
            if let Some(neighbors) = adj.get(&node) {
                for &neighbor in neighbors {
                    if !visited.contains(&neighbor) {
                        stack.push(neighbor);
                    }
                }
            }
        }
    }
    
    visited.len() == num_nodes
}

// ============================================
// REAL-WORLD CHALLENGE 3: SUBSET SUM OPTIMIZATION
// ============================================

#[derive(Debug, Clone)]
pub struct Item {
    pub name: String,
    pub value: u32,
    pub weight: u32,
}

/// Find all subsets of items that fit within weight limit
/// Real-world use: Knapsack problem, cargo loading, resource allocation
pub fn knapsack_all_solutions(items: &[Item], max_weight: u32) -> Vec<(Vec<Item>, u32, u32)> {
    let mut solutions = Vec::new();
    let mut current_items = Vec::new();
    
    fn backtrack(
        items: &[Item],
        start: usize,
        current_items: &mut Vec<Item>,
        current_weight: u32,
        current_value: u32,
        max_weight: u32,
        solutions: &mut Vec<(Vec<Item>, u32, u32)>
    ) {
        // Save current solution if not empty
        if !current_items.is_empty() && current_weight <= max_weight {
            solutions.push((current_items.clone(), current_weight, current_value));
        }
        
        for i in start..items.len() {
            let new_weight = current_weight + items[i].weight;
            if new_weight <= max_weight {
                current_items.push(items[i].clone());
                backtrack(
                    items,
                    i + 1,
                    current_items,
                    new_weight,
                    current_value + items[i].value,
                    max_weight,
                    solutions
                );
                current_items.pop();
            }
        }
    }
    
    backtrack(items, 0, &mut current_items, 0, 0, max_weight, &mut solutions);
    
    // Sort by value (descending)
    solutions.sort_by(|a, b| b.2.cmp(&a.2));
    solutions
}

// ============================================
// MAIN DEMO
// ============================================

fn main() {
    println!("=== Rust Combinatorics Library ===\n");
    
    // Demo 1: Basic operations
    println!("1. Basic Permutations:");
    let arr = vec![1, 2, 3];
    let perms = permutations(&arr);
    println!("   Permutations of {:?}: {} total", arr, perms.len());
    for p in perms.iter().take(3) {
        println!("   {:?}", p);
    }
    
    println!("\n2. Basic Combinations:");
    let combos = combinations(&arr, 2);
    println!("   C(3,2) = {}", combos.len());
    for c in &combos {
        println!("   {:?}", c);
    }
    
    println!("\n3. Basic Subsets:");
    let subs = subsets(&arr);
    println!("   Subsets of {:?}: {} total", arr, subs.len());
    for s in &subs {
        println!("   {:?}", s);
    }
    
    // Demo 2: Task Scheduling
    println!("\n=== Challenge 1: Task Scheduling ===");
    let tasks = vec![
        Task {
            id: "Setup".to_string(),
            duration: 30,
            priority: 5,
            dependencies: vec![],
        },
        Task {
            id: "Development".to_string(),
            duration: 120,
            priority: 10,
            dependencies: vec!["Setup".to_string()],
        },
        Task {
            id: "Testing".to_string(),
            duration: 60,
            priority: 8,
            dependencies: vec!["Development".to_string()],
        },
        Task {
            id: "Documentation".to_string(),
            duration: 45,
            priority: 6,
            dependencies: vec!["Setup".to_string()],
        },
    ];
    
    let schedules = optimize_schedule(&tasks, 180);
    println!("Found {} valid schedules within 180 minutes", schedules.len());
    for (i, schedule) in schedules.iter().take(3).enumerate() {
        println!("\nSchedule {}: Priority={}, Time={}min", 
                 i + 1, schedule.priority_score, schedule.total_time);
        println!("  Tasks: {:?}", schedule.tasks);
    }
    
    // Demo 3: Knapsack
    println!("\n=== Challenge 3: Knapsack Problem ===");
    let items = vec![
        Item { name: "Laptop".to_string(), value: 1000, weight: 3 },
        Item { name: "Camera".to_string(), value: 500, weight: 2 },
        Item { name: "Book".to_string(), value: 50, weight: 1 },
        Item { name: "Tablet".to_string(), value: 400, weight: 2 },
    ];
    
    let solutions = knapsack_all_solutions(&items, 5);
    println!("Found {} valid packing solutions (max weight: 5kg)", solutions.len());
    for (i, (items, weight, value)) in solutions.iter().take(3).enumerate() {
        println!("\nSolution {}: Value=${}, Weight={}kg", i + 1, value, weight);
        for item in items {
            println!("  - {}", item.name);
        }
    }
}

package main

import (
	"fmt"
	"sort"
)

// ============================================
// CORE IMPLEMENTATIONS
// ============================================

// Permutations generates all permutations of a slice
func Permutations(arr []int) [][]int {
	result := [][]int{}
	used := make([]bool, len(arr))
	path := []int{}

	var backtrack func()
	backtrack = func() {
		if len(path) == len(arr) {
			temp := make([]int, len(path))
			copy(temp, path)
			result = append(result, temp)
			return
		}

		for i := 0; i < len(arr); i++ {
			if !used[i] {
				used[i] = true
				path = append(path, arr[i])
				backtrack()
				path = path[:len(path)-1]
				used[i] = false
			}
		}
	}

	backtrack()
	return result
}

// Combinations generates all k-length combinations
func Combinations(arr []int, k int) [][]int {
	result := [][]int{}
	path := []int{}

	var backtrack func(start int)
	backtrack = func(start int) {
		if len(path) == k {
			temp := make([]int, len(path))
			copy(temp, path)
			result = append(result, temp)
			return
		}

		for i := start; i < len(arr); i++ {
			path = append(path, arr[i])
			backtrack(i + 1)
			path = path[:len(path)-1]
		}
	}

	backtrack(0)
	return result
}

// Subsets generates all subsets using bit manipulation
func Subsets(arr []int) [][]int {
	n := len(arr)
	total := 1 << n // 2^n
	result := make([][]int, total)

	for mask := 0; mask < total; mask++ {
		subset := []int{}
		for i := 0; i < n; i++ {
			if mask&(1<<i) != 0 {
				subset = append(subset, arr[i])
			}
		}
		result[mask] = subset
	}

	return result
}

// SubsetsBacktrack generates subsets using backtracking
func SubsetsBacktrack(arr []int) [][]int {
	result := [][]int{}
	path := []int{}

	var backtrack func(start int)
	backtrack = func(start int) {
		temp := make([]int, len(path))
		copy(temp, path)
		result = append(result, temp)

		for i := start; i < len(arr); i++ {
			path = append(path, arr[i])
			backtrack(i + 1)
			path = path[:len(path)-1]
		}
	}

	backtrack(0)
	return result
}

// ============================================
// REAL-WORLD CHALLENGE 1: TOURNAMENT BRACKET
// ============================================

type Player struct {
	Name   string
	Rating int
}

type Match struct {
	Player1 string
	Player2 string
}

// GenerateTournamentBrackets creates all possible match pairings
// Real-world use: Sports tournaments, esports, chess competitions
func GenerateTournamentBrackets(players []Player, roundSize int) [][]Match {
	brackets := [][]Match{}
	
	// Generate all combinations of players for matches
	combos := CombinationsGeneric(players, roundSize)
	
	for _, combo := range combos {
		// Generate all possible pairings within this combination
		matches := generatePairings(combo)
		if len(matches) == roundSize/2 {
			brackets = append(brackets, matches)
		}
	}
	
	return brackets
}

func generatePairings(players []Player) []Match {
	if len(players) < 2 || len(players)%2 != 0 {
		return []Match{}
	}
	
	matches := []Match{}
	used := make(map[string]bool)
	
	for i := 0; i < len(players); i++ {
		if used[players[i].Name] {
			continue
		}
		for j := i + 1; j < len(players); j++ {
			if !used[players[j].Name] {
				matches = append(matches, Match{
					Player1: players[i].Name,
					Player2: players[j].Name,
				})
				used[players[i].Name] = true
				used[players[j].Name] = true
				break
			}
		}
	}
	
	return matches
}

// CombinationsGeneric for generic types
func CombinationsGeneric(players []Player, k int) [][]Player {
	result := [][]Player{}
	path := []Player{}

	var backtrack func(start int)
	backtrack = func(start int) {
		if len(path) == k {
			temp := make([]Player, len(path))
			copy(temp, path)
			result = append(result, temp)
			return
		}

		for i := start; i < len(players); i++ {
			path = append(path, players[i])
			backtrack(i + 1)
			path = path[:len(path)-1]
		}
	}

	backtrack(0)
	return result
}

// ============================================
// REAL-WORLD CHALLENGE 2: RESTAURANT MENU OPTIMIZER
// ============================================

type MenuItem struct {
	Name     string
	Price    float64
	Calories int
	Category string
}

type MenuCombo struct {
	Items        []MenuItem
	TotalPrice   float64
	TotalCals    int
	Categories   map[string]int
}

// OptimizeMenuCombos finds meal combinations within budget and calorie limits
// Real-world use: Restaurant ordering, meal planning, dietary management
func OptimizeMenuCombos(menu []MenuItem, maxPrice float64, maxCalories int, 
                        minItems, maxItems int) []MenuCombo {
	validCombos := []MenuCombo{}

	var backtrack func(start int, current []MenuItem, price float64, cals int)
	backtrack = func(start int, current []MenuItem, price float64, cals int) {
		// Check if current combo is valid
		if len(current) >= minItems && len(current) <= maxItems {
			if price <= maxPrice && cals <= maxCalories {
				// Count categories for variety
				categories := make(map[string]int)
				for _, item := range current {
					categories[item.Category]++
				}
				
				combo := MenuCombo{
					Items:      make([]MenuItem, len(current)),
					TotalPrice: price,
					TotalCals:  cals,
					Categories: categories,
				}
				copy(combo.Items, current)
				validCombos = append(validCombos, combo)
			}
		}

		// Try adding more items
		if len(current) >= maxItems {
			return
		}

		for i := start; i < len(menu); i++ {
			newPrice := price + menu[i].Price
			newCals := cals + menu[i].Calories
			
			// Prune branches that exceed limits
			if newPrice <= maxPrice && newCals <= maxCalories {
				current = append(current, menu[i])
				backtrack(i+1, current, newPrice, newCals)
				current = current[:len(current)-1]
			}
		}
	}

	backtrack(0, []MenuItem{}, 0, 0)
	
	// Sort by category variety (descending), then by price (ascending)
	sort.Slice(validCombos, func(i, j int) bool {
		if len(validCombos[i].Categories) != len(validCombos[j].Categories) {
			return len(validCombos[i].Categories) > len(validCombos[j].Categories)
		}
		return validCombos[i].TotalPrice < validCombos[j].TotalPrice
	})
	
	return validCombos
}

// ============================================
// REAL-WORLD CHALLENGE 3: SEATING ARRANGEMENT
// ============================================

type Guest struct {
	Name        string
	Preferences []string // Names of people they prefer to sit with
	Conflicts   []string // Names of people they don't want to sit with
}

type SeatingArrangement struct {
	Arrangement    []string
	SatisfiedPrefs int
	Conflicts      int
}

// GenerateSeatingArrangements finds optimal seating orders
// Real-world use: Wedding planning, conference seating, classroom arrangement
func GenerateSeatingArrangements(guests []Guest, maxSeats int) []SeatingArrangement {
	arrangements := []SeatingArrangement{}
	guestNames := make([]string, len(guests))
	guestMap := make(map[string]Guest)
	
	for i, g := range guests {
		guestNames[i] = g.Name
		guestMap[g.Name] = g
	}
	
	// Generate all permutations up to maxSeats
	if len(guestNames) > maxSeats {
		guestNames = guestNames[:maxSeats]
	}
	
	perms := PermutationsString(guestNames)
	
	// Evaluate each arrangement
	for _, perm := range perms {
		satisfied := 0
		conflicts := 0
		
		for i, name := range perm {
			guest := guestMap[name]
			
			// Check adjacent seats
			if i > 0 {
				leftNeighbor := perm[i-1]
				if contains(guest.Preferences, leftNeighbor) {
					satisfied++
				}
				if contains(guest.Conflicts, leftNeighbor) {
					conflicts++
				}
			}
			
			if i < len(perm)-1 {
				rightNeighbor := perm[i+1]
				if contains(guest.Preferences, rightNeighbor) {
					satisfied++
				}
				if contains(guest.Conflicts, rightNeighbor) {
					conflicts++
				}
			}
		}
		
		arrangements = append(arrangements, SeatingArrangement{
			Arrangement:    perm,
			SatisfiedPrefs: satisfied,
			Conflicts:      conflicts,
		})
	}
	
	// Sort by most satisfied preferences and fewest conflicts
	sort.Slice(arrangements, func(i, j int) bool {
		if arrangements[i].Conflicts != arrangements[j].Conflicts {
			return arrangements[i].Conflicts < arrangements[j].Conflicts
		}
		return arrangements[i].SatisfiedPrefs > arrangements[j].SatisfiedPrefs
	})
	
	return arrangements
}

func PermutationsString(arr []string) [][]string {
	result := [][]string{}
	used := make([]bool, len(arr))
	path := []string{}

	var backtrack func()
	backtrack = func() {
		if len(path) == len(arr) {
			temp := make([]string, len(path))
			copy(temp, path)
			result = append(result, temp)
			return
		}

		for i := 0; i < len(arr); i++ {
			if !used[i] {
				used[i] = true
				path = append(path, arr[i])
				backtrack()
				path = path[:len(path)-1]
				used[i] = false
			}
		}
	}

	backtrack()
	return result
}

func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}

// ============================================
// REAL-WORLD CHALLENGE 4: PORTFOLIO DIVERSIFICATION
// ============================================

type Stock struct {
	Symbol string
	Sector string
	Price  float64
	Risk   int // 1-10 scale
}

type Portfolio struct {
	Stocks      []Stock
	TotalValue  float64
	AvgRisk     float64
	Sectors     map[string]int
	Diversified bool
}

// GeneratePortfolios creates diversified stock portfolios
// Real-world use: Investment planning, risk management, asset allocation
func GeneratePortfolios(stocks []Stock, budget float64, minStocks, maxStocks int) []Portfolio {
	portfolios := []Portfolio{}
	
	var backtrack func(start int, current []Stock, value float64)
	backtrack = func(start int, current []Stock, value float64) {
		if len(current) >= minStocks && len(current) <= maxStocks && value <= budget {
			// Calculate metrics
			sectors := make(map[string]int)
			totalRisk := 0
			
			for _, stock := range current {
				sectors[stock.Sector]++
				totalRisk += stock.Risk
			}
			
			avgRisk := float64(totalRisk) / float64(len(current))
			diversified := len(sectors) >= 3 // At least 3 sectors
			
			portfolio := Portfolio{
				Stocks:      make([]Stock, len(current)),
				TotalValue:  value,
				AvgRisk:     avgRisk,
				Sectors:     sectors,
				Diversified: diversified,
			}
			copy(portfolio.Stocks, current)
			portfolios = append(portfolios, portfolio)
		}
		
		if len(current) >= maxStocks || value >= budget {
			return
		}
		
		for i := start; i < len(stocks); i++ {
			newValue := value + stocks[i].Price
			if newValue <= budget {
				current = append(current, stocks[i])
				backtrack(i+1, current, newValue)
				current = current[:len(current)-1]
			}
		}
	}
	
	backtrack(0, []Stock{}, 0)
	
	// Sort by diversification, then by average risk (ascending)
	sort.Slice(portfolios, func(i, j int) bool {
		if portfolios[i].Diversified != portfolios[j].Diversified {
			return portfolios[i].Diversified
		}
		return portfolios[i].AvgRisk < portfolios[j].AvgRisk
	})
	
	return portfolios
}

// ============================================
// MAIN DEMO
// ============================================

func main() {
	fmt.Println("=== Go Combinatorics Library ===\n")
	
	// Demo 1: Basic operations
	fmt.Println("1. Basic Permutations:")
	arr := []int{1, 2, 3}
	perms := Permutations(arr)
	fmt.Printf("   Permutations of %v: %d total\n", arr, len(perms))
	for i, p := range perms {
		if i >= 3 {
			break
		}
		fmt.Printf("   %v\n", p)
	}
	
	fmt.Println("\n2. Basic Combinations:")
	combos := Combinations(arr, 2)
	fmt.Printf("   C(3,2) = %d\n", len(combos))
	for _, c := range combos {
		fmt.Printf("   %v\n", c)
	}
	
	fmt.Println("\n3. Basic Subsets:")
	subs := Subsets(arr)
	fmt.Printf("   Subsets of %v: %d total\n", arr, len(subs))
	for _, s := range subs {
		fmt.Printf("   %v\n", s)
	}
	
	// Demo 2: Tournament Brackets
	fmt.Println("\n=== Challenge 1: Tournament Brackets ===")
	players := []Player{
		{Name: "Alice", Rating: 1800},
		{Name: "Bob", Rating: 1650},
		{Name: "Carol", Rating: 1900},
		{Name: "Dave", Rating: 1750},
	}
	
	brackets := GenerateTournamentBrackets(players, 4)
	fmt.Printf("Generated %d possible brackets for %d players\n", len(brackets), len(players))
	for i, bracket := range brackets {
		if i >= 2 {
			break
		}
		fmt.Printf("\nBracket %d:\n", i+1)
		for j, match := range bracket {
			fmt.Printf("  Match %d: %s vs %s\n", j+1, match.Player1, match.Player2)
		}
	}
	
	// Demo 3: Restaurant Menu
	fmt.Println("\n=== Challenge 2: Restaurant Menu Optimizer ===")
	menu := []MenuItem{
		{Name: "Burger", Price: 12.99, Calories: 650, Category: "Main"},
		{Name: "Salad", Price: 8.99, Calories: 250, Category: "Main"},
		{Name: "Fries", Price: 4.99, Calories: 400, Category: "Side"},
		{Name: "Soda", Price: 2.99, Calories: 150, Category: "Drink"},
		{Name: "Water", Price: 0.00, Calories: 0, Category: "Drink"},
		{Name: "Ice Cream", Price: 5.99, Calories: 350, Category: "Dessert"},
	}
	
	combos2 := OptimizeMenuCombos(menu, 20.00, 1000, 2, 4)
	fmt.Printf("Found %d valid menu combinations (Budget: $20, Max calories: 1000)\n", len(combos2))
	for i, combo := range combos2 {
		if i >= 3 {
			break
		}
		fmt.Printf("\nCombo %d: $%.2f, %d cal, %d categories\n", 
			i+1, combo.TotalPrice, combo.TotalCals, len(combo.Categories))
		for _, item := range combo.Items {
			fmt.Printf("  - %s\n", item.Name)
		}
	}
	
	// Demo 4: Seating Arrangements
	fmt.Println("\n=== Challenge 3: Seating Arrangements ===")
	guests := []Guest{
		{Name: "Alice", Preferences: []string{"Bob"}, Conflicts: []string{"Dave"}},
		{Name: "Bob", Preferences: []string{"Alice", "Carol"}, Conflicts: []string{}},
		{Name: "Carol", Preferences: []string{"Bob"}, Conflicts: []string{}},
		{Name: "Dave", Preferences: []string{}, Conflicts: []string{"Alice"}},
	}
	
	seating := GenerateSeatingArrangements(guests, 4)
	fmt.Printf("Found %d possible seating arrangements\n", len(seating))
	for i, arr := range seating {
		if i >= 3 {
			break
		}
		fmt.Printf("\nArrangement %d: %d satisfied prefs, %d conflicts\n", 
			i+1, arr.SatisfiedPrefs, arr.Conflicts)
		fmt.Printf("  Order: %v\n", arr.Arrangement)
	}
	
	// Demo 5: Portfolio
	fmt.Println("\n=== Challenge 4: Portfolio Diversification ===")
	stocks := []Stock{
		{Symbol: "AAPL", Sector: "Tech", Price: 150.00, Risk: 5},
		{Symbol: "GOOGL", Sector: "Tech", Price: 140.00, Risk: 5},
		{Symbol: "JPM", Sector: "Finance", Price: 130.00, Risk: 6},
		{Symbol: "JNJ", Sector: "Healthcare", Price: 160.00, Risk: 3},
		{Symbol: "XOM", Sector: "Energy", Price: 110.00, Risk: 7},
	}
	
	portfolios := GeneratePortfolios(stocks, 400.00, 2, 3)
	fmt.Printf("Found %d valid portfolios (Budget: $400)\n", len(portfolios))
	for i, port := range portfolios {
		if i >= 3 {
			break
		}
		fmt.Printf("\nPortfolio %d: $%.2f, Avg Risk: %.2f, Diversified: %v\n", 
			i+1, port.TotalValue, port.AvgRisk, port.Diversified)
		fmt.Printf("  Sectors: %v\n", port.Sectors)
		for _, stock := range port.Stocks {
			fmt.Printf("  - %s (%s): $%.2f\n", stock.Symbol, stock.Sector, stock.Price)
		}
	}
}