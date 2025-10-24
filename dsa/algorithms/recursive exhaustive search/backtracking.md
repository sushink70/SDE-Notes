# Backtracking Explained

Backtracking is a systematic way to explore all possible solutions by building candidates incrementally and abandoning them ("backtracking") as soon as we determine they can't lead to a valid solution.

## How It Works - ASCII Diagram

```
Start at root
     [1]
    /   \
   /     \
 [1,2]  [1,3]
  / \    / \
[1,2,3][1,2,4] ...
  |      ✗
  ✓    (invalid - backtrack!)
(valid)
  
Process:
1. Choose → Try a candidate
2. Explore → Move forward if valid
3. Backtrack → If invalid/complete, undo and try next option
4. Repeat → Until all possibilities explored
```

## Core Concept

Think of it like exploring a maze:

- Start at entrance
- Try a path
- Hit a dead end? Go back to last junction
- Try a different path
- Repeat until you find the exit or exhaust all paths


---

## Code Examples

### Python - N-Queens Problem

```python
def solve_n_queens(n):
    """
    Solve N-Queens problem using backtracking.
    Place N queens on NxN board so no two queens attack each other.
    """
    def is_safe(board, row, col):
        # Check column
        for i in range(row):
            if board[i] == col:
                return False
        
        # Check diagonal (top-left to bottom-right)
        for i in range(row):
            if abs(board[i] - col) == abs(i - row):
                return False
        
        return True
    
    def backtrack(row):
        # Base case: all queens placed
        if row == n:
            solutions.append(board[:])
            return
        
        # Try placing queen in each column
        for col in range(n):
            if is_safe(board, row, col):
                # Choose: place queen
                board[row] = col
                
                # Explore: move to next row
                backtrack(row + 1)
                
                # Backtrack: remove queen (implicit, we'll overwrite)
    
    solutions = []
    board = [-1] * n  # board[i] = column position of queen in row i
    backtrack(0)
    return solutions


def print_board(solution, n):
    """Visualize a solution"""
    for row in range(n):
        line = ""
        for col in range(n):
            if solution[row] == col:
                line += "Q "
            else:
                line += ". "
        print(line)
    print()
```

# Example: Solve 4-Queens

```python
solutions = solve_n_queens(4)
print(f"Found {len(solutions)} solutions for 4-Queens:\n")

for i, sol in enumerate(solutions, 1):
    print(f"Solution {i}:")
    print_board(sol, 4)


# Example 2: Subset Sum Problem

def subset_sum(nums, target):
    """Find all subsets that sum to target"""
    def backtrack(start, path, current_sum):
        if current_sum == target:
            result.append(path[:])
            return
        
        if current_sum > target:
            return  # Prune: can't reach target
        
        for i in range(start, len(nums)):
            # Choose
            path.append(nums[i])
            
            # Explore
            backtrack(i + 1, path, current_sum + nums[i])
            
            # Backtrack
            path.pop()
    
    result = []
    backtrack(0, [], 0)
    return result


nums = [2, 3, 5, 7]
target = 10
print("\nSubset Sum Problem:")
print(f"Numbers: {nums}, Target: {target}")
print(f"Solutions: {subset_sum(nums, target)}")
```

### Rust - Permutations Generator

```rust
/// Generate all permutations using backtracking
fn permute(nums: Vec<i32>) -> Vec<Vec<i32>> {
    let mut result = Vec::new();
    let mut current = Vec::new();
    let mut used = vec![false; nums.len()];
    
    backtrack(&nums, &mut current, &mut used, &mut result);
    result
}

fn backtrack(
    nums: &[i32],
    current: &mut Vec<i32>,
    used: &mut [bool],
    result: &mut Vec<Vec<i32>>,
) {
    // Base case: permutation is complete
    if current.len() == nums.len() {
        result.push(current.clone());
        return;
    }
    
    // Try each unused number
    for i in 0..nums.len() {
        if used[i] {
            continue; // Skip if already used
        }
        
        // Choose: add number to permutation
        current.push(nums[i]);
        used[i] = true;
        
        // Explore: recurse
        backtrack(nums, current, used, result);
        
        // Backtrack: undo choice
        current.pop();
        used[i] = false;
    }
}


/// Solve Sudoku using backtracking
fn solve_sudoku(board: &mut Vec<Vec<char>>) -> bool {
    fn is_valid(board: &[Vec<char>], row: usize, col: usize, num: char) -> bool {
        // Check row
        if board[row].contains(&num) {
            return false;
        }
        
        // Check column
        for r in 0..9 {
            if board[r][col] == num {
                return false;
            }
        }
        
        // Check 3x3 box
        let box_row = (row / 3) * 3;
        let box_col = (col / 3) * 3;
        for r in box_row..box_row + 3 {
            for c in box_col..box_col + 3 {
                if board[r][c] == num {
                    return false;
                }
            }
        }
        
        true
    }
    
    fn backtrack(board: &mut Vec<Vec<char>>) -> bool {
        // Find empty cell
        for row in 0..9 {
            for col in 0..9 {
                if board[row][col] == '.' {
                    // Try digits 1-9
                    for num in '1'..='9' {
                        if is_valid(board, row, col, num) {
                            // Choose
                            board[row][col] = num;
                            
                            // Explore
                            if backtrack(board) {
                                return true;
                            }
                            
                            // Backtrack
                            board[row][col] = '.';
                        }
                    }
                    return false; // No valid number found
                }
            }
        }
        true // All cells filled
    }
    
    backtrack(board)
}


fn main() {
    // Example 1: Permutations
    let nums = vec![1, 2, 3];
    let perms = permute(nums);
    
    println!("Permutations of [1, 2, 3]:");
    for perm in &perms {
        println!("{:?}", perm);
    }
    println!("Total: {} permutations\n", perms.len());
    
    // Example 2: Combination Sum
    fn combination_sum(candidates: Vec<i32>, target: i32) -> Vec<Vec<i32>> {
        fn backtrack(
            candidates: &[i32],
            target: i32,
            start: usize,
            current: &mut Vec<i32>,
            result: &mut Vec<Vec<i32>>,
        ) {
            if target == 0 {
                result.push(current.clone());
                return;
            }
            if target < 0 {
                return;
            }
            
            for i in start..candidates.len() {
                current.push(candidates[i]);
                backtrack(candidates, target - candidates[i], i, current, result);
                current.pop();
            }
        }
        
        let mut result = Vec::new();
        let mut current = Vec::new();
        backtrack(&candidates, target, 0, &mut current, &mut result);
        result
    }
    
    let candidates = vec![2, 3, 6, 7];
    let target = 7;
    let combos = combination_sum(candidates, target);
    
    println!("Combination Sum (target=7, nums=[2,3,6,7]):");
    for combo in combos {
        println!("{:?}", combo);
    }
}
```

### Go - Word Search

```go
package main

import "fmt"

// Word Search: Find if word exists in grid (can move up/down/left/right)
func exist(board [][]byte, word string) bool {
	rows, cols := len(board), len(board[0])
	
	var backtrack func(row, col, index int) bool
	backtrack = func(row, col, index int) bool {
		// Base case: found all characters
		if index == len(word) {
			return true
		}
		
		// Boundary checks
		if row < 0 || row >= rows || col < 0 || col >= cols {
			return false
		}
		
		// Check if current cell matches and not visited
		if board[row][col] != word[index] {
			return false
		}
		
		// Choose: mark as visited
		temp := board[row][col]
		board[row][col] = '#'
		
		// Explore: try all 4 directions
		found := backtrack(row+1, col, index+1) ||
			backtrack(row-1, col, index+1) ||
			backtrack(row, col+1, index+1) ||
			backtrack(row, col-1, index+1)
		
		// Backtrack: restore cell
		board[row][col] = temp
		
		return found
	}
	
	// Try starting from each cell
	for i := 0; i < rows; i++ {
		for j := 0; j < cols; j++ {
			if backtrack(i, j, 0) {
				return true
			}
		}
	}
	
	return false
}

// Generate Parentheses: Generate all valid combinations of n pairs
func generateParenthesis(n int) []string {
	result := []string{}
	
	var backtrack func(current string, open, close int)
	backtrack = func(current string, open, close int) {
		// Base case: used all parentheses
		if len(current) == 2*n {
			result = append(result, current)
			return
		}
		
		// Choose: add opening parenthesis
		if open < n {
			backtrack(current+"(", open+1, close)
		}
		
		// Choose: add closing parenthesis (only if valid)
		if close < open {
			backtrack(current+")", open, close+1)
		}
	}
	
	backtrack("", 0, 0)
	return result
}

// Letter Combinations of Phone Number
func letterCombinations(digits string) []string {
	if len(digits) == 0 {
		return []string{}
	}
	
	phoneMap := map[byte]string{
		'2': "abc", '3': "def", '4': "ghi", '5': "jkl",
		'6': "mno", '7': "pqrs", '8': "tuv", '9': "wxyz",
	}
	
	result := []string{}
	
	var backtrack func(index int, path string)
	backtrack = func(index int, path string) {
		// Base case: processed all digits
		if index == len(digits) {
			result = append(result, path)
			return
		}
		
		// Get letters for current digit
		letters := phoneMap[digits[index]]
		
		// Try each letter
		for i := 0; i < len(letters); i++ {
			// Choose and explore
			backtrack(index+1, path+string(letters[i]))
			// No explicit backtrack needed (string is immutable)
		}
	}
	
	backtrack(0, "")
	return result
}

func main() {
	// Example 1: Word Search
	board := [][]byte{
		{'A', 'B', 'C', 'E'},
		{'S', 'F', 'C', 'S'},
		{'A', 'D', 'E', 'E'},
	}
	
	words := []string{"ABCCED", "SEE", "ABCB"}
	fmt.Println("Word Search Example:")
	for _, word := range words {
		fmt.Printf("Word '%s': %v\n", word, exist(board, word))
	}
	
	// Example 2: Generate Parentheses
	fmt.Println("\nGenerate Parentheses (n=3):")
	parens := generateParenthesis(3)
	for _, p := range parens {
		fmt.Println(p)
	}
	
	// Example 3: Letter Combinations
	fmt.Println("\nLetter Combinations ('23'):")
	combos := letterCombinations("23")
	fmt.Println(combos)
}
```

## Detailed Flow Diagram

```
Example: Generate all subsets of [1,2,3]

                        []
                      / | \
                     /  |  \
                   [1] [2] [3]
                  / |   |
                [1,2][1,3][2,3]
                 |
              [1,2,3]

Step-by-step execution:
1. Start: []
2. Choose 1 → [1]
3. Choose 2 → [1,2]
4. Choose 3 → [1,2,3] ✓ (add to result)
5. Backtrack → [1,2] (remove 3)
6. No more options → Backtrack to [1]
7. Choose 3 → [1,3] ✓
8. Backtrack → []
9. Choose 2 → [2]
10. Choose 3 → [2,3] ✓
11. Backtrack → []
12. Choose 3 → [3] ✓
13. Done!

Call Stack Visualization:
backtrack([])
  ↓
backtrack([1])
  ↓
backtrack([1,2])
  ↓
backtrack([1,2,3]) → valid! return
  ↑ (pop 3)
backtrack([1,2])
  ↑ (pop 2)
backtrack([1])
  ↓
backtrack([1,3]) → valid! return
...
```

---

## Real-World Advantages

**1. Memory Efficient**
- Only stores current path, not all possibilities
- Space: O(depth) instead of O(all solutions)

**2. Early Pruning**
- Stops exploring invalid branches immediately
- Saves exponential computation

**3. Guarantees Exploration**
- Systematically checks all possibilities
- Won't miss valid solutions

**4. Natural Recursion**
- Clean, readable code
- Matches problem structure

**5. Constraint Handling**
- Easy to add validation checks
- Flexible constraint incorporation

---

## Real-World Use Cases

**1. Puzzle Solvers**
- Sudoku, crosswords, Rubik's cube
- Chess move analysis

**2. Scheduling**
- Task allocation
- Course timetabling
- Resource assignment

**3. Pathfinding**
- Route optimization with constraints
- Maze solving

**4. Configuration Problems**
- Network routing
- Circuit design
- Register allocation in compilers

**5. Game AI**
- Game tree search
- Strategy exploration

**6. Combinatorial Optimization**
- Subset selection
- Graph coloring
- Knapsack variations

---

## How to Identify Backtracking Problems

### Key Patterns:

**1. Multiple Choices at Each Step**
```
"Find ALL permutations"
"Generate ALL combinations"
"Find ALL valid arrangements"
```

**2. Constraint Satisfaction**
```
"Place N queens such that..."
"Arrange items without conflicts..."
"Valid configuration where..."
```

**3. Incremental Building**
```
Problem builds solution piece by piece
Each step depends on previous choices
```

**4. Keywords to Look For:**
- "All possible"
- "Generate all"
- "Find all valid"
- "Combinations/Permutations"
- "Subsets"
- "With constraints"
- "Valid arrangements"

### Decision Framework:

```
Can you build solution incrementally? → YES
  ↓
At each step, multiple choices? → YES
  ↓
Need to explore all possibilities? → YES
  ↓
Can detect invalid choices early? → YES
  ↓
→ USE BACKTRACKING!
```

---

## The Backtracking Pattern (Template)

```python
def backtrack(path, options):
    # 1. Base case: valid solution found
    if is_valid_solution(path):
        result.append(path.copy())
        return
    
    # 2. Pruning: stop if can't succeed
    if cannot_succeed(path):
        return
    
    # 3. Try all choices
    for choice in get_available_choices(options):
        # CHOOSE: add to path
        path.append(choice)
        mark_used(choice)
        
        # EXPLORE: recurse
        backtrack(path, options)
        
        # BACKTRACK: undo choice
        path.pop()
        unmark_used(choice)
```

### Three Core Steps:
1. **Choose**: Make a decision, add to path
2. **Explore**: Recurse with new state
3. **Unchoose**: Undo decision, restore state

---

## Complexity Analysis

**Time**: O(b^d) where:
- b = branching factor (choices per step)
- d = maximum depth

**Space**: O(d) for recursion stack
- Much better than storing all solutions upfront!

**With Pruning**: Often much faster than brute force
- Early termination saves exponential work

The key insight: backtracking trades computation for memory by exploring paths lazily instead of generating everything upfront.

# Combinations Problem - Backtracking Solution

## Problem Analysis

This is a classic **backtracking** problem where we need to:
- Choose `k` numbers from range `[1, n]`
- Order doesn't matter (combinations, not permutations)
- Avoid duplicates (e.g., [1,2] and [2,1] are same)

---

## ASCII Diagram - How It Works

```
Example: n=4, k=2 (choose 2 numbers from [1,2,3,4])

                        []
                    /   |   \   \
                  /     |     \   \
               [1]     [2]    [3] [4]
              / | \     | \     |
            /   |   \   |   \   |
         [1,2][1,3][1,4][2,3][2,4][3,4]
           ✓    ✓    ✓    ✓    ✓    ✓
        (all valid - length k=2)

Key Insight: Start index prevents duplicates
- After choosing 1, only try 2,3,4 (not 1 again)
- After choosing 2, only try 3,4 (not 1,2)
- This ensures [1,2] is generated but [2,1] is not


Detailed Execution Trace for n=4, k=2:

Step 1: Start=1, path=[]
  Try 1: path=[1]
    Step 2: Start=2, path=[1]
      Try 2: path=[1,2] → LENGTH=k, ADD TO RESULT ✓
      Try 3: path=[1,3] → LENGTH=k, ADD TO RESULT ✓
      Try 4: path=[1,4] → LENGTH=k, ADD TO RESULT ✓
    Backtrack to path=[1]
  Backtrack to path=[]
  
  Try 2: path=[2]
    Step 3: Start=3, path=[2]
      Try 3: path=[2,3] → LENGTH=k, ADD TO RESULT ✓
      Try 4: path=[2,4] → LENGTH=k, ADD TO RESULT ✓
    Backtrack to path=[2]
  Backtrack to path=[]
  
  Try 3: path=[3]
    Step 4: Start=4, path=[3]
      Try 4: path=[3,4] → LENGTH=k, ADD TO RESULT ✓
    Backtrack to path=[3]
  Backtrack to path=[]
  
  Try 4: path=[4]
    No more numbers available
  Backtrack

Result: [[1,2],[1,3],[1,4],[2,3],[2,4],[3,4]]


Call Stack Visualization:
combine(1, [])
├─ combine(2, [1])
│  ├─ combine(3, [1,2]) → add [1,2] ✓
│  ├─ combine(4, [1,3]) → add [1,3] ✓
│  └─ combine(5, [1,4]) → add [1,4] ✓
├─ combine(3, [2])
│  ├─ combine(4, [2,3]) → add [2,3] ✓
│  └─ combine(5, [2,4]) → add [2,4] ✓
├─ combine(4, [3])
│  └─ combine(5, [3,4]) → add [3,4] ✓
└─ combine(5, [4]) → stop (start > n)
```

---

## Python Solution---

## Visual Execution Flow

```
For n=4, k=2:

Decision Tree with Pruning:
                        START
                          |
                    start=1, path=[]
                          |
        ┌─────────┬───────┴───────┬─────────┐
        |         |               |         |
      i=1       i=2             i=3       i=4
        |         |               |         |
   path=[1]   path=[2]       path=[3]   path=[4]
        |         |               |         |
    start=2   start=3         start=4   start=5
        |         |               |         (stop)
   ┌────┼────┐  ┌─┴─┐            |
  i=2  i=3  i=4 i=3 i=4          i=4
   |    |    |   |   |            |
 [1,2][1,3][1,4][2,3][2,4]     [3,4]
   ✓    ✓    ✓   ✓   ✓            ✓


Pruning Example (n=5, k=3):
When at path=[1,2], need 1 more number
- Can try 3,4,5 (3 choices available) ✓
- If we were at path=[1,2] with start=5
  - Need 1, have 1 (5 only) → proceed
- If we were at path=[1] with start=5
  - Need 2, have 1 → PRUNE! Not enough numbers
```

---

## Key Points

### 1. **Why `start` parameter?**
Prevents duplicates by ensuring we only pick numbers greater than previous picks:
- `[1,2]` is generated (start at 1, then 2)
- `[2,1]` is NOT generated (after picking 2, we start at 3)

### 2. **Pruning Optimization**
```python
if n - i + 1 < remaining_needed:
    break
```
- Remaining numbers: `n - i + 1`
- Still need: `k - len(path)`
- If not enough, stop early (saves unnecessary recursion)

### 3. **Backtracking Pattern**
```python
path.append(i)        # CHOOSE
backtrack(i+1, path)  # EXPLORE
path.pop()            # UNCHOOSE (backtrack)
```

### 4. **Time Complexity Breakdown**
- Total combinations: C(n,k) = n!/(k!(n-k)!)
- Each combination takes O(k) to build
- **Total**: O(C(n,k) × k)

---

## When to Use This Pattern?

✓ Need to select subset of fixed size  
✓ Order doesn't matter (combinations)  
✓ No repetition allowed  
✓ Exhaustive search required  

Similar problems: Combination Sum, Letter Combinations, Subsets

"""
COMBINATIONS PROBLEM - BACKTRACKING SOLUTION
Choose k numbers from range [1, n]
"""
```python
# ========== PYTHON SOLUTION ==========
def combine(n, k):
    """
    Generate all combinations of k numbers from [1, n]
    
    Time: O(C(n,k) * k) = O(n!/(k!(n-k)!) * k)
    Space: O(k) for recursion depth
    """
    result = []
    
    def backtrack(start, path):
        # Base case: found a valid combination
        if len(path) == k:
            result.append(path[:])  # Make a copy
            return
        
        # Pruning: if remaining numbers not enough to reach k
        # need: k - len(path) numbers
        # available: n - start + 1 numbers
        remaining_needed = k - len(path)
        
        # Try each number from start to n
        for i in range(start, n + 1):
            # Optimization: stop if not enough numbers left
            if n - i + 1 < remaining_needed:
                break
            
            # Choose: add number to path
            path.append(i)
            
            # Explore: recurse with next starting position
            backtrack(i + 1, path)
            
            # Backtrack: remove number
            path.pop()
    
    backtrack(1, [])
    return result


# Test cases
print("=" * 50)
print("PYTHON - Combinations Problem")
print("=" * 50)

test_cases = [
    (4, 2),
    (1, 1),
    (5, 3),
    (4, 4)
]

for n, k in test_cases:
    result = combine(n, k)
    print(f"\nInput: n={n}, k={k}")
    print(f"Output: {result}")
    print(f"Count: {len(result)} (Expected: C({n},{k}) = {factorial(n)//(factorial(k)*factorial(n-k))})")

def factorial(x):
    if x <= 1:
        return 1
    return x * factorial(x - 1)
```
```rust
# ========== RUST SOLUTION ==========
rust_code = """
// RUST SOLUTION
pub fn combine(n: i32, k: i32) -> Vec<Vec<i32>> {
    let mut result = Vec::new();
    let mut path = Vec::new();
    backtrack(1, n, k, &mut path, &mut result);
    result
}

fn backtrack(
    start: i32,
    n: i32,
    k: i32,
    path: &mut Vec<i32>,
    result: &mut Vec<Vec<i32>>
) {
    // Base case: found valid combination
    if path.len() == k as usize {
        result.push(path.clone());
        return;
    }
    
    let remaining_needed = k as usize - path.len();
    
    for i in start..=n {
        // Pruning: not enough numbers left
        if (n - i + 1) < remaining_needed as i32 {
            break;
        }
        
        // Choose
        path.push(i);
        
        // Explore
        backtrack(i + 1, n, k, path, result);
        
        // Backtrack
        path.pop();
    }
}

fn main() {
    println!("RUST - Combinations Problem");
    println!("{}", "=".repeat(50));
    
    let test_cases = vec![(4, 2), (1, 1), (5, 3)];
    
    for (n, k) in test_cases {
        let result = combine(n, k);
        println!("\\nInput: n={}, k={}", n, k);
        println!("Output: {:?}", result);
        println!("Count: {}", result.len());
    }
}
"""
```

```go
print("\n" + "=" * 50)
print("RUST CODE:")
print("=" * 50)
print(rust_code)


# ========== GO SOLUTION ==========
go_code = """
// GO SOLUTION
package main

import "fmt"

func combine(n int, k int) [][]int {
    result := [][]int{}
    path := []int{}
    backtrack(1, n, k, &path, &result)
    return result
}

func backtrack(start, n, k int, path *[]int, result *[][]int) {
    // Base case: found valid combination
    if len(*path) == k {
        // Make a copy of the path
        combination := make([]int, k)
        copy(combination, *path)
        *result = append(*result, combination)
        return
    }
    
    remainingNeeded := k - len(*path)
    
    for i := start; i <= n; i++ {
        // Pruning: not enough numbers left
        if n - i + 1 < remainingNeeded {
            break
        }
        
        // Choose
        *path = append(*path, i)
        
        // Explore
        backtrack(i+1, n, k, path, result)
        
        // Backtrack
        *path = (*path)[:len(*path)-1]
    }
}

func main() {
    fmt.Println("GO - Combinations Problem")
    fmt.Println(strings.Repeat("=", 50))
    
    testCases := []struct{n, k int}{
        {4, 2},
        {1, 1},
        {5, 3},
    }
    
    for _, tc := range testCases {
        result := combine(tc.n, tc.k)
        fmt.Printf("\\nInput: n=%d, k=%d\\n", tc.n, tc.k)
        fmt.Printf("Output: %v\\n", result)
        fmt.Printf("Count: %d\\n", len(result))
    }
}
"""

print("\n" + "=" * 50)
print("GO CODE:")
print("=" * 50)
print(go_code)


# ========== ALTERNATIVE APPROACH: Iterative ==========
def combine_iterative(n, k):
    """
    Iterative solution using stack simulation
    """
    result = []
    stack = [(1, [])]  # (start_index, current_path)
    
    while stack:
        start, path = stack.pop()
        
        if len(path) == k:
            result.append(path)
            continue
        
        # Add choices in reverse order (so they pop in correct order)
        for i in range(n, start - 1, -1):
            if n - i + 1 >= k - len(path):
                stack.append((i + 1, path + [i]))
    
    return result


print("\n" + "=" * 50)
print("PYTHON - Iterative Approach")
print("=" * 50)

for n, k in [(4, 2), (5, 3)]:
    result = combine_iterative(n, k)
    print(f"\nInput: n={n}, k={k}")
    print(f"Output: {result}")
    print(f"Count: {len(result)}")
"""

print("\n" + "=" * 50)
print("COMPLEXITY ANALYSIS")
print("=" * 50)
print("""
Time Complexity: O(C(n,k) * k)
- C(n,k) = n!/(k!(n-k)!) combinations to generate
- Each combination takes O(k) to copy to result
- Example: n=4, k=2 → C(4,2) = 6 combinations

Space Complexity: O(k)
- Recursion depth: O(k)
- Path array: O(k)
- Result storage: O(C(n,k) * k) but not counted as auxiliary space

Optimizations Applied:
1. Pruning: Stop when remaining numbers < needed numbers
2. Start index: Prevents generating duplicate combinations
3. In-place modification: Minimize memory allocations
""")
```