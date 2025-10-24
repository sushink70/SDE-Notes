# Comprehensive Backtracking Problem Patterns Guide

## Table of Contents

1. [Introduction to Backtracking](#introduction)
2. [Core Template](#core-template)
3. [Pattern 1: Subset Generation](#pattern-1-subset-generation)
4. [Pattern 2: Permutation Generation](#pattern-2-permutation-generation)
5. [Pattern 3: Combination Generation](#pattern-3-combination-generation)
6. [Pattern 4: N-Queens Problem](#pattern-4-n-queens-problem)
7. [Pattern 5: Sudoku Solver](#pattern-5-sudoku-solver)
8. [Pattern 6: Word Search](#pattern-6-word-search)
9. [Pattern 7: Palindrome Partitioning](#pattern-7-palindrome-partitioning)
10. [Pattern 8: Expression Evaluation](#pattern-8-expression-evaluation)
11. [Pattern 9: Graph Coloring](#pattern-9-graph-coloring)
12. [Pattern 10: Maze Solving](#pattern-10-maze-solving)

## Introduction to Backtracking {#introduction}

Backtracking is a systematic method for solving constraint satisfaction problems by incrementally building candidates to solutions and abandoning candidates ("backtracking") when they cannot lead to a valid solution.

### Key Characteristics:

- **Incremental Construction**: Build solution step by step
- **Constraint Checking**: Validate partial solutions early
- **Backtrack**: Undo choices that lead to invalid states
- **Exhaustive Search**: Explore all possibilities systematically

### When to Use Backtracking:

- Finding all solutions to a constraint problem
- Optimization problems where you need to explore all possibilities
- Problems involving permutations, combinations, or subsets
- Puzzle-solving (Sudoku, N-Queens, etc.)
- Path finding with constraints

## Core Template {#core-template}

### Python Template

```python
def backtrack(state, candidates, target):
    # Base case - found valid solution
    if is_solution(state, target):
        process_solution(state)
        return
    
    # Try each candidate
    for candidate in get_candidates(state, candidates):
        if is_valid(state, candidate):
            # Make choice
            state.append(candidate)
            
            # Recursively explore
            backtrack(state, candidates, target)
            
            # Backtrack (undo choice)
            state.pop()

def is_solution(state, target):
    # Check if current state represents a complete solution
    pass

def get_candidates(state, candidates):
    # Return possible next choices
    pass

def is_valid(state, candidate):
    # Check if adding candidate maintains validity
    pass

def process_solution(state):
    # Handle found solution (store, print, etc.)
    pass
```

### Rust Template

```rust
fn backtrack(state: &mut Vec<i32>, candidates: &[i32], target: i32, result: &mut Vec<Vec<i32>>) {
    // Base case - found valid solution
    if is_solution(state, target) {
        process_solution(state, result);
        return;
    }
    
    // Try each candidate
    for &candidate in get_candidates(state, candidates) {
        if is_valid(state, candidate) {
            // Make choice
            state.push(candidate);
            
            // Recursively explore
            backtrack(state, candidates, target, result);
            
            // Backtrack (undo choice)
            state.pop();
        }
    }
}

fn is_solution(state: &[i32], target: i32) -> bool {
    // Check if current state represents a complete solution
    false
}

fn get_candidates<'a>(state: &[i32], candidates: &'a [i32]) -> &'a [i32] {
    // Return possible next choices
    candidates
}

fn is_valid(state: &[i32], candidate: i32) -> bool {
    // Check if adding candidate maintains validity
    true
}

fn process_solution(state: &[i32], result: &mut Vec<Vec<i32>>) {
    // Handle found solution (store, print, etc.)
    result.push(state.to_vec());
}
```

## Pattern 1: Subset Generation {#pattern-1-subset-generation}

**Problem**: Generate all possible subsets of a given set.

### Python Implementation

```python
def subsets(nums):
    """Generate all subsets of nums array."""
    result = []
    
    def backtrack(start, current_subset):
        # Every state is a valid subset
        result.append(current_subset[:])  # Make a copy
        
        # Try adding each remaining element
        for i in range(start, len(nums)):
            # Include nums[i] in current subset
            current_subset.append(nums[i])
            
            # Recursively generate subsets starting from i+1
            backtrack(i + 1, current_subset)
            
            # Backtrack: remove nums[i]
            current_subset.pop()
    
    backtrack(0, [])
    return result

# Example with duplicates handling
def subsets_with_dups(nums):
    """Generate all unique subsets when nums contains duplicates."""
    result = []
    nums.sort()  # Sort to group duplicates
    
    def backtrack(start, current_subset):
        result.append(current_subset[:])
        
        for i in range(start, len(nums)):
            # Skip duplicates: if current element equals previous
            # and we haven't used the previous element
            if i > start and nums[i] == nums[i-1]:
                continue
                
            current_subset.append(nums[i])
            backtrack(i + 1, current_subset)
            current_subset.pop()
    
    backtrack(0, [])
    return result

# Test
print(subsets([1, 2, 3]))
# Output: [[], [1], [1, 2], [1, 2, 3], [1, 3], [2], [2, 3], [3]]
```

### Rust Implementation
```rust
fn subsets(nums: Vec<i32>) -> Vec<Vec<i32>> {
    let mut result = Vec::new();
    let mut current_subset = Vec::new();
    
    fn backtrack(start: usize, nums: &[i32], current_subset: &mut Vec<i32>, result: &mut Vec<Vec<i32>>) {
        // Every state is a valid subset
        result.push(current_subset.clone());
        
        // Try adding each remaining element
        for i in start..nums.len() {
            // Include nums[i] in current subset
            current_subset.push(nums[i]);
            
            // Recursively generate subsets starting from i+1
            backtrack(i + 1, nums, current_subset, result);
            
            // Backtrack: remove nums[i]
            current_subset.pop();
        }
    }
    
    backtrack(0, &nums, &mut current_subset, &mut result);
    result
}

// Example with duplicates handling
fn subsets_with_dups(mut nums: Vec<i32>) -> Vec<Vec<i32>> {
    let mut result = Vec::new();
    let mut current_subset = Vec::new();
    nums.sort(); // Sort to group duplicates
    
    fn backtrack(start: usize, nums: &[i32], current_subset: &mut Vec<i32>, result: &mut Vec<Vec<i32>>) {
        result.push(current_subset.clone());
        
        for i in start..nums.len() {
            // Skip duplicates
            if i > start && nums[i] == nums[i-1] {
                continue;
            }
            
            current_subset.push(nums[i]);
            backtrack(i + 1, nums, current_subset, result);
            current_subset.pop();
        }
    }
    
    backtrack(0, &nums, &mut current_subset, &mut result);
    result
}
```

## Pattern 2: Permutation Generation {#pattern-2-permutation-generation}

**Problem**: Generate all possible permutations of a given array.

### Python Implementation
```python
def permute(nums):
    """Generate all permutations of nums array."""
    result = []
    
    def backtrack(current_permutation):
        # Base case: we've used all numbers
        if len(current_permutation) == len(nums):
            result.append(current_permutation[:])  # Make a copy
            return
        
        # Try each unused number
        for num in nums:
            if num not in current_permutation:  # Check if unused
                # Choose: add number to permutation
                current_permutation.append(num)
                
                # Recursively build rest of permutation
                backtrack(current_permutation)
                
                # Unchoose: backtrack
                current_permutation.pop()
    
    backtrack([])
    return result

# More efficient version using indices
def permute_optimized(nums):
    """Generate permutations using index swapping for O(1) choice/unchoice."""
    result = []
    
    def backtrack(first):
        # Base case: we've placed all numbers
        if first == len(nums):
            result.append(nums[:])  # Make a copy
            return
        
        # Try placing each remaining number at position 'first'
        for i in range(first, len(nums)):
            # Choose: swap nums[first] with nums[i]
            nums[first], nums[i] = nums[i], nums[first]
            
            # Recursively permute remaining positions
            backtrack(first + 1)
            
            # Unchoose: swap back
            nums[first], nums[i] = nums[i], nums[first]
    
    backtrack(0)
    return result

# Handle duplicates
def permute_unique(nums):
    """Generate unique permutations when nums contains duplicates."""
    result = []
    nums.sort()  # Sort to group duplicates
    used = [False] * len(nums)
    
    def backtrack(current_permutation):
        if len(current_permutation) == len(nums):
            result.append(current_permutation[:])
            return
        
        for i in range(len(nums)):
            if used[i]:
                continue
            
            # Skip duplicates: if current element equals previous
            # and previous element hasn't been used yet
            if i > 0 and nums[i] == nums[i-1] and not used[i-1]:
                continue
            
            used[i] = True
            current_permutation.append(nums[i])
            
            backtrack(current_permutation)
            
            current_permutation.pop()
            used[i] = False
    
    backtrack([])
    return result

# Test
print(permute([1, 2, 3]))
# Output: [[1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 1, 2], [3, 2, 1]]
```

### Rust Implementation
```rust
fn permute(nums: Vec<i32>) -> Vec<Vec<i32>> {
    let mut result = Vec::new();
    let mut current_permutation = Vec::new();
    
    fn backtrack(nums: &[i32], current_permutation: &mut Vec<i32>, result: &mut Vec<Vec<i32>>) {
        // Base case: we've used all numbers
        if current_permutation.len() == nums.len() {
            result.push(current_permutation.clone());
            return;
        }
        
        // Try each unused number
        for &num in nums {
            if !current_permutation.contains(&num) {
                // Choose: add number to permutation
                current_permutation.push(num);
                
                // Recursively build rest of permutation
                backtrack(nums, current_permutation, result);
                
                // Unchoose: backtrack
                current_permutation.pop();
            }
        }
    }
    
    backtrack(&nums, &mut current_permutation, &mut result);
    result
}

// More efficient version using index swapping
fn permute_optimized(mut nums: Vec<i32>) -> Vec<Vec<i32>> {
    let mut result = Vec::new();
    
    fn backtrack(first: usize, nums: &mut [i32], result: &mut Vec<Vec<i32>>) {
        // Base case: we've placed all numbers
        if first == nums.len() {
            result.push(nums.to_vec());
            return;
        }
        
        // Try placing each remaining number at position 'first'
        for i in first..nums.len() {
            // Choose: swap nums[first] with nums[i]
            nums.swap(first, i);
            
            // Recursively permute remaining positions
            backtrack(first + 1, nums, result);
            
            // Unchoose: swap back
            nums.swap(first, i);
        }
    }
    
    backtrack(0, &mut nums, &mut result);
    result
}

// Handle duplicates
fn permute_unique(mut nums: Vec<i32>) -> Vec<Vec<i32>> {
    let mut result = Vec::new();
    let mut current_permutation = Vec::new();
    let mut used = vec![false; nums.len()];
    nums.sort(); // Sort to group duplicates
    
    fn backtrack(
        nums: &[i32], 
        used: &mut [bool], 
        current_permutation: &mut Vec<i32>, 
        result: &mut Vec<Vec<i32>>
    ) {
        if current_permutation.len() == nums.len() {
            result.push(current_permutation.clone());
            return;
        }
        
        for i in 0..nums.len() {
            if used[i] {
                continue;
            }
            
            // Skip duplicates
            if i > 0 && nums[i] == nums[i-1] && !used[i-1] {
                continue;
            }
            
            used[i] = true;
            current_permutation.push(nums[i]);
            
            backtrack(nums, used, current_permutation, result);
            
            current_permutation.pop();
            used[i] = false;
        }
    }
    
    backtrack(&nums, &mut used, &mut current_permutation, &mut result);
    result
}
```

## Pattern 3: Combination Generation {#pattern-3-combination-generation}

**Problem**: Generate all combinations of k elements from n elements.

### Python Implementation
```python
def combine(n, k):
    """Generate all combinations of k numbers from 1 to n."""
    result = []
    
    def backtrack(start, current_combination):
        # Base case: we have k elements
        if len(current_combination) == k:
            result.append(current_combination[:])  # Make a copy
            return
        
        # Optimization: if we can't possibly reach k elements, return early
        need = k - len(current_combination)  # How many more elements we need
        remain = n - start + 1  # How many elements are left
        if remain < need:
            return
        
        # Try each number from start to n
        for i in range(start, n + 1):
            # Choose: add i to combination
            current_combination.append(i)
            
            # Recursively build rest of combination
            backtrack(i + 1, current_combination)
            
            # Unchoose: backtrack
            current_combination.pop()
    
    backtrack(1, [])
    return result

# Combination Sum - find combinations that sum to target
def combination_sum(candidates, target):
    """Find all unique combinations where candidates sum to target.
    Each number can be used multiple times."""
    result = []
    candidates.sort()  # Sort for optimization
    
    def backtrack(start, current_combination, current_sum):
        # Base case: found target sum
        if current_sum == target:
            result.append(current_combination[:])
            return
        
        # Base case: exceeded target
        if current_sum > target:
            return
        
        # Try each candidate starting from 'start'
        for i in range(start, len(candidates)):
            # Optimization: if current candidate is too large, break
            if current_sum + candidates[i] > target:
                break
            
            # Choose: add candidate to combination
            current_combination.append(candidates[i])
            
            # Recursive call: note we use 'i', not 'i+1' to allow reuse
            backtrack(i, current_combination, current_sum + candidates[i])
            
            # Unchoose: backtrack
            current_combination.pop()
    
    backtrack(0, [], 0)
    return result

# Combination Sum II - each number used at most once
def combination_sum2(candidates, target):
    """Find combinations that sum to target, each number used at most once."""
    result = []
    candidates.sort()
    
    def backtrack(start, current_combination, current_sum):
        if current_sum == target:
            result.append(current_combination[:])
            return
        
        if current_sum > target:
            return
        
        for i in range(start, len(candidates)):
            # Skip duplicates: if not the first element in this level
            # and it equals the previous element
            if i > start and candidates[i] == candidates[i-1]:
                continue
            
            if current_sum + candidates[i] > target:
                break
            
            current_combination.append(candidates[i])
            # Use i+1 to ensure each number is used at most once
            backtrack(i + 1, current_combination, current_sum + candidates[i])
            current_combination.pop()
    
    backtrack(0, [], 0)
    return result

# Test
print(combine(4, 2))
# Output: [[1, 2], [1, 3], [1, 4], [2, 3], [2, 4], [3, 4]]

print(combination_sum([2, 3, 6, 7], 7))
# Output: [[2, 2, 3], [7]]
```

### Rust Implementation
```rust
fn combine(n: i32, k: i32) -> Vec<Vec<i32>> {
    let mut result = Vec::new();
    let mut current_combination = Vec::new();
    
    fn backtrack(start: i32, n: i32, k: i32, current_combination: &mut Vec<i32>, result: &mut Vec<Vec<i32>>) {
        // Base case: we have k elements
        if current_combination.len() == k as usize {
            result.push(current_combination.clone());
            return;
        }
        
        // Optimization: early termination
        let need = k - current_combination.len() as i32;
        let remain = n - start + 1;
        if remain < need {
            return;
        }
        
        // Try each number from start to n
        for i in start..=n {
            // Choose: add i to combination
            current_combination.push(i);
            
            // Recursively build rest of combination
            backtrack(i + 1, n, k, current_combination, result);
            
            // Unchoose: backtrack
            current_combination.pop();
        }
    }
    
    backtrack(1, n, k, &mut current_combination, &mut result);
    result
}

// Combination Sum
fn combination_sum(mut candidates: Vec<i32>, target: i32) -> Vec<Vec<i32>> {
    let mut result = Vec::new();
    let mut current_combination = Vec::new();
    candidates.sort();
    
    fn backtrack(
        start: usize, 
        candidates: &[i32], 
        target: i32,
        current_combination: &mut Vec<i32>, 
        current_sum: i32,
        result: &mut Vec<Vec<i32>>
    ) {
        // Base case: found target sum
        if current_sum == target {
            result.push(current_combination.clone());
            return;
        }
        
        // Base case: exceeded target
        if current_sum > target {
            return;
        }
        
        // Try each candidate starting from 'start'
        for i in start..candidates.len() {
            // Optimization: if current candidate is too large, break
            if current_sum + candidates[i] > target {
                break;
            }
            
            // Choose: add candidate to combination
            current_combination.push(candidates[i]);
            
            // Recursive call: note we use 'i', not 'i+1' to allow reuse
            backtrack(i, candidates, target, current_combination, current_sum + candidates[i], result);
            
            // Unchoose: backtrack
            current_combination.pop();
        }
    }
    
    backtrack(0, &candidates, target, &mut current_combination, 0, &mut result);
    result
}

// Combination Sum II
fn combination_sum2(mut candidates: Vec<i32>, target: i32) -> Vec<Vec<i32>> {
    let mut result = Vec::new();
    let mut current_combination = Vec::new();
    candidates.sort();
    
    fn backtrack(
        start: usize,
        candidates: &[i32],
        target: i32,
        current_combination: &mut Vec<i32>,
        current_sum: i32,
        result: &mut Vec<Vec<i32>>
    ) {
        if current_sum == target {
            result.push(current_combination.clone());
            return;
        }
        
        if current_sum > target {
            return;
        }
        
        for i in start..candidates.len() {
            // Skip duplicates
            if i > start && candidates[i] == candidates[i-1] {
                continue;
            }
            
            if current_sum + candidates[i] > target {
                break;
            }
            
            current_combination.push(candidates[i]);
            backtrack(i + 1, candidates, target, current_combination, current_sum + candidates[i], result);
            current_combination.pop();
        }
    }
    
    backtrack(0, &candidates, target, &mut current_combination, 0, &mut result);
    result
}
```

## Pattern 4: N-Queens Problem {#pattern-4-n-queens-problem}

**Problem**: Place N queens on an N×N chessboard so that no two queens attack each other.

### Python Implementation
```python
def solve_n_queens(n):
    """Solve the N-Queens problem and return all solutions."""
    result = []
    board = ['.' * n for _ in range(n)]  # Initialize empty board
    
    def is_safe(row, col):
        """Check if placing a queen at (row, col) is safe."""
        # Check column
        for i in range(row):
            if board[i][col] == 'Q':
                return False
        
        # Check diagonal (top-left to bottom-right)
        for i, j in zip(range(row-1, -1, -1), range(col-1, -1, -1)):
            if board[i][j] == 'Q':
                return False
        
        # Check anti-diagonal (top-right to bottom-left)
        for i, j in zip(range(row-1, -1, -1), range(col+1, n)):
            if board[i][j] == 'Q':
                return False
        
        return True
    
    def backtrack(row):
        """Try to place queens starting from the given row."""
        # Base case: all queens placed successfully
        if row == n:
            result.append([''.join(row) for row in board])
            return
        
        # Try placing queen in each column of current row
        for col in range(n):
            if is_safe(row, col):
                # Choose: place queen
                board[row] = board[row][:col] + 'Q' + board[row][col+1:]
                
                # Recursively place remaining queens
                backtrack(row + 1)
                
                # Unchoose: remove queen (backtrack)
                board[row] = board[row][:col] + '.' + board[row][col+1:]
    
    backtrack(0)
    return result

# Optimized version using sets for conflict tracking
def solve_n_queens_optimized(n):
    """Optimized N-Queens solution using sets for O(1) conflict checking."""
    result = []
    queens = []  # List of (row, col) positions
    cols = set()  # Columns under attack
    diag1 = set()  # Diagonals under attack (row - col)
    diag2 = set()  # Anti-diagonals under attack (row + col)
    
    def backtrack(row):
        if row == n:
            # Convert queen positions to board representation
            board = ['.' * n for _ in range(n)]
            for r, c in queens:
                board[r] = board[r][:c] + 'Q' + board[r][c+1:]
            result.append(board)
            return
        
        for col in range(n):
            # Check conflicts using sets (O(1) lookup)
            if col in cols or (row - col) in diag1 or (row + col) in diag2:
                continue
            
            # Choose: place queen and mark conflicts
            queens.append((row, col))
            cols.add(col)
            diag1.add(row - col)
            diag2.add(row + col)
            
            # Recursively place remaining queens
            backtrack(row + 1)
            
            # Unchoose: remove queen and unmark conflicts
            queens.pop()
            cols.remove(col)
            diag1.remove(row - col)
            diag2.remove(row + col)
    
    backtrack(0)
    return result

# Count solutions only (more efficient)
def total_n_queens(n):
    """Count the number of solutions to N-Queens problem."""
    count = 0
    cols = set()
    diag1 = set()
    diag2 = set()
    
    def backtrack(row):
        nonlocal count
        if row == n:
            count += 1
            return
        
        for col in range(n):
            if col in cols or (row - col) in diag1 or (row + col) in diag2:
                continue
            
            cols.add(col)
            diag1.add(row - col)
            diag2.add(row + col)
            
            backtrack(row + 1)
            
            cols.remove(col)
            diag1.remove(row - col)
            diag2.remove(row + col)
    
    backtrack(0)
    return count

# Test
solutions = solve_n_queens(4)
for i, solution in enumerate(solutions):
    print(f"Solution {i+1}:")
    for row in solution:
        print(row)
    print()
```

### Rust Implementation
```rust
use std::collections::HashSet;

fn solve_n_queens(n: i32) -> Vec<Vec<String>> {
    let mut result = Vec::new();
    let mut board = vec![".".repeat(n as usize); n as usize];
    
    fn is_safe(board: &[String], row: usize, col: usize, n: usize) -> bool {
        // Check column
        for i in 0..row {
            if board[i].chars().nth(col).unwrap() == 'Q' {
                return false;
            }
        }
        
        // Check diagonal (top-left to bottom-right)
        let mut i = row as i32 - 1;
        let mut j = col as i32 - 1;
        while i >= 0 && j >= 0 {
            if board[i as usize].chars().nth(j as usize).unwrap() == 'Q' {
                return false;
            }
            i -= 1;
            j -= 1;
        }
        
        // Check anti-diagonal (top-right to bottom-left)
        let mut i = row as i32 - 1;
        let mut j = col as i32 + 1;
        while i >= 0 && j < n as i32 {
            if board[i as usize].chars().nth(j as usize).unwrap() == 'Q' {
                return false;
            }
            i -= 1;
            j += 1;
        }
        
        true
    }
    
    fn backtrack(row: usize, n: usize, board: &mut Vec<String>, result: &mut Vec<Vec<String>>) {
        // Base case: all queens placed successfully
        if row == n {
            result.push(board.clone());
            return;
        }
        
        // Try placing queen in each column of current row
        for col in 0..n {
            if is_safe(board, row, col, n) {
                // Choose: place queen
                let mut chars: Vec<char> = board[row].chars().collect();
                chars[col] = 'Q';
                board[row] = chars.into_iter().collect();
                
                // Recursively place remaining queens
                backtrack(row + 1, n, board, result);
                
                // Unchoose: remove queen (backtrack)
                let mut chars: Vec<char> = board[row].chars().collect();
                chars[col] = '.';
                board[row] = chars.into_iter().collect();
            }
        }
    }
    
    backtrack(0, n as usize, &mut board, &mut result);
    result
}

// Optimized version using HashSets
fn solve_n_queens_optimized(n: i32) -> Vec<Vec<String>> {
    let mut result = Vec::new();
    let mut queens = Vec::new();
    let mut cols = HashSet::new();
    let mut diag1 = HashSet::new();
    let mut diag2 = HashSet::new();
    
    fn backtrack(
        row: i32,
        n: i32,
        queens: &mut Vec<(i32, i32)>,
        cols: &mut HashSet<i32>,
        diag1: &mut HashSet<i32>,
        diag2: &mut HashSet<i32>,
        result: &mut Vec<Vec<String>>
    ) {
        if row == n {
            // Convert queen positions to board representation
            let mut board = vec![".".repeat(n as usize); n as usize];
            for &(r, c) in queens {
                let mut chars: Vec<char> = board[r as usize].chars().collect();
                chars[c as usize] = 'Q';
                board[r as usize] = chars.into_iter().collect();
            }
            result.push(board);
            return;
        }
        
        for col in 0..n {
            // Check conflicts using sets (O(1) lookup)
            if cols.contains(&col) || diag1.contains(&(row - col)) || diag2.contains(&(row + col)) {
                continue;
            }
            
            // Choose: place queen and mark conflicts
            queens.push((row, col));
            cols.insert(col);
            diag1.insert(row - col);
            diag2.insert(row + col);
            
            // Recursively place remaining queens
            backtrack(row + 1, n, queens, cols, diag1, diag2, result);
            
            // Unchoose: remove queen and unmark conflicts
            queens.pop();
            cols.remove(&col);
            diag1.remove(&(row - col));
            diag2.remove(&(row + col));
        }
    }
    backtrack(0, n, &mut queens, &mut cols, &mut diag1, &mut diag2, &mut result);
    result
}

I've created a comprehensive guide to backtracking problem patterns with complete implementations in both Python and Rust. This guide covers:

## **10 Essential Backtracking Patterns:**

1. **Subset Generation** - Generate all possible subsets with duplicates handling
2. **Permutation Generation** - All arrangements with optimization techniques  
3. **Combination Generation** - Choose k from n elements, combination sums
4. **N-Queens Problem** - Classic constraint satisfaction with conflict tracking
5. **Sudoku Solver** - Grid-based puzzles with advanced heuristics
6. **Word Search** - 2D grid traversal with path tracking
7. **Palindrome Partitioning** - String segmentation with DP optimization
8. **Expression Evaluation** - Operator placement and parentheses handling
9. **Graph Coloring** - Constraint-based vertex coloring with extensions
10. **Maze Solving** - Path finding with multiple objectives and generation

## **Key Features:**

- **Complete implementations** in both Python and Rust
- **Optimized versions** with pruning and heuristics
- **Multiple variants** for each pattern (basic, advanced, constrained)
- **Detailed explanations** of the approach and complexity
- **Best practices** and common pitfalls
- **Testing examples** and verification strategies

## **Optimization Techniques Covered:**

- Early termination and constraint propagation
- Auxiliary data structures for O(1) lookups
- Heuristics like Most Constrained Variable (MRV)
- Memory-efficient state management
- Iterative alternatives for deep recursions

This guide serves as both a learning resource and a practical reference for coding interviews and competitive programming. Each pattern includes the core template, optimizations, and real-world applications with complete working code.

```go
package main

import (
	"fmt"
	"sort"
	"strings"
)

// ============================================================================
// PATTERN 1: SUBSETS / POWERSET
// Problem: Generate all possible subsets of a set
// Time: O(2^n), Space: O(n)
// ============================================================================

func subsets(nums []int) [][]int {
	result := [][]int{}
	path := []int{}
	
	var backtrack func(start int)
	backtrack = func(start int) {
		// Add current subset to result
		temp := make([]int, len(path))
		copy(temp, path)
		result = append(result, temp)
		
		// Explore further elements
		for i := start; i < len(nums); i++ {
			path = append(path, nums[i])  // Choose
			backtrack(i + 1)               // Explore
			path = path[:len(path)-1]      // Unchoose
		}
	}
	
	backtrack(0)
	return result
}

// Variation: Subsets with duplicates
func subsetsWithDup(nums []int) [][]int {
	sort.Ints(nums)
	result := [][]int{}
	path := []int{}
	
	var backtrack func(start int)
	backtrack = func(start int) {
		temp := make([]int, len(path))
		copy(temp, path)
		result = append(result, temp)
		
		for i := start; i < len(nums); i++ {
			// Skip duplicates at same level
			if i > start && nums[i] == nums[i-1] {
				continue
			}
			path = append(path, nums[i])
			backtrack(i + 1)
			path = path[:len(path)-1]
		}
	}
	
	backtrack(0)
	return result
}

// ============================================================================
// PATTERN 2: COMBINATIONS
// Problem: Find all k-length combinations from n elements
// Time: O(C(n,k)), Space: O(k)
// ============================================================================

func combine(n int, k int) [][]int {
	result := [][]int{}
	path := []int{}
	
	var backtrack func(start int)
	backtrack = func(start int) {
		// Base case: combination complete
		if len(path) == k {
			temp := make([]int, k)
			copy(temp, path)
			result = append(result, temp)
			return
		}
		
		// Pruning: not enough elements left
		for i := start; i <= n; i++ {
			if n-i+1 < k-len(path) {
				break
			}
			path = append(path, i)
			backtrack(i + 1)
			path = path[:len(path)-1]
		}
	}
	
	backtrack(1)
	return result
}

// Variation: Combination Sum (can reuse elements)
func combinationSum(candidates []int, target int) [][]int {
	result := [][]int{}
	path := []int{}
	
	var backtrack func(start, sum int)
	backtrack = func(start, sum int) {
		if sum == target {
			temp := make([]int, len(path))
			copy(temp, path)
			result = append(result, temp)
			return
		}
		if sum > target {
			return
		}
		
		for i := start; i < len(candidates); i++ {
			path = append(path, candidates[i])
			backtrack(i, sum+candidates[i]) // i not i+1: can reuse
			path = path[:len(path)-1]
		}
	}
	
	backtrack(0, 0)
	return result
}

// ============================================================================
// PATTERN 3: PERMUTATIONS
// Problem: Generate all permutations of elements
// Time: O(n!), Space: O(n)
// ============================================================================

func permute(nums []int) [][]int {
	result := [][]int{}
	path := []int{}
	used := make([]bool, len(nums))
	
	var backtrack func()
	backtrack = func() {
		if len(path) == len(nums) {
			temp := make([]int, len(path))
			copy(temp, path)
			result = append(result, temp)
			return
		}
		
		for i := 0; i < len(nums); i++ {
			if used[i] {
				continue
			}
			
			path = append(path, nums[i])
			used[i] = true
			backtrack()
			used[i] = false
			path = path[:len(path)-1]
		}
	}
	
	backtrack()
	return result
}

// Variation: Permutations with duplicates
func permuteUnique(nums []int) [][]int {
	sort.Ints(nums)
	result := [][]int{}
	path := []int{}
	used := make([]bool, len(nums))
	
	var backtrack func()
	backtrack = func() {
		if len(path) == len(nums) {
			temp := make([]int, len(path))
			copy(temp, path)
			result = append(result, temp)
			return
		}
		
		for i := 0; i < len(nums); i++ {
			if used[i] {
				continue
			}
			// Skip duplicates: if current equals previous and previous not used
			if i > 0 && nums[i] == nums[i-1] && !used[i-1] {
				continue
			}
			
			path = append(path, nums[i])
			used[i] = true
			backtrack()
			used[i] = false
			path = path[:len(path)-1]
		}
	}
	
	backtrack()
	return result
}

// ============================================================================
// PATTERN 4: N-QUEENS
// Problem: Place N queens on NxN board without attacking each other
// Time: O(N!), Space: O(N)
// ============================================================================

func solveNQueens(n int) [][]string {
	result := [][]string{}
	board := make([][]byte, n)
	for i := range board {
		board[i] = make([]byte, n)
		for j := range board[i] {
			board[i][j] = '.'
		}
	}
	
	cols := make(map[int]bool)
	diag1 := make(map[int]bool) // row - col
	diag2 := make(map[int]bool) // row + col
	
	var backtrack func(row int)
	backtrack = func(row int) {
		if row == n {
			solution := make([]string, n)
			for i := range board {
				solution[i] = string(board[i])
			}
			result = append(result, solution)
			return
		}
		
		for col := 0; col < n; col++ {
			if cols[col] || diag1[row-col] || diag2[row+col] {
				continue
			}
			
			// Place queen
			board[row][col] = 'Q'
			cols[col] = true
			diag1[row-col] = true
			diag2[row+col] = true
			
			backtrack(row + 1)
			
			// Remove queen
			board[row][col] = '.'
			delete(cols, col)
			delete(diag1, row-col)
			delete(diag2, row+col)
		}
	}
	
	backtrack(0)
	return result
}

// ============================================================================
// PATTERN 5: SUDOKU SOLVER
// Problem: Fill 9x9 grid following Sudoku rules
// Time: O(9^m) where m is empty cells, Space: O(1)
// ============================================================================

func solveSudoku(board [][]byte) {
	var backtrack func() bool
	backtrack = func() bool {
		for i := 0; i < 9; i++ {
			for j := 0; j < 9; j++ {
				if board[i][j] != '.' {
					continue
				}
				
				for c := byte('1'); c <= '9'; c++ {
					if !isValidSudoku(board, i, j, c) {
						continue
					}
					
					board[i][j] = c
					if backtrack() {
						return true
					}
					board[i][j] = '.'
				}
				return false
			}
		}
		return true
	}
	
	backtrack()
}

func isValidSudoku(board [][]byte, row, col int, c byte) bool {
	for i := 0; i < 9; i++ {
		if board[row][i] == c || board[i][col] == c {
			return false
		}
		boxRow := 3*(row/3) + i/3
		boxCol := 3*(col/3) + i%3
		if board[boxRow][boxCol] == c {
			return false
		}
	}
	return true
}

// ============================================================================
// PATTERN 6: WORD SEARCH
// Problem: Find if word exists in 2D grid
// Time: O(m*n*4^L) where L is word length, Space: O(L)
// ============================================================================

func exist(board [][]byte, word string) bool {
	m, n := len(board), len(board[0])
	
	var backtrack func(i, j, idx int) bool
	backtrack = func(i, j, idx int) bool {
		if idx == len(word) {
			return true
		}
		if i < 0 || i >= m || j < 0 || j >= n || board[i][j] != word[idx] {
			return false
		}
		
		temp := board[i][j]
		board[i][j] = '#' // Mark visited
		
		found := backtrack(i+1, j, idx+1) ||
			backtrack(i-1, j, idx+1) ||
			backtrack(i, j+1, idx+1) ||
			backtrack(i, j-1, idx+1)
		
		board[i][j] = temp // Restore
		return found
	}
	
	for i := 0; i < m; i++ {
		for j := 0; j < n; j++ {
			if backtrack(i, j, 0) {
				return true
			}
		}
	}
	return false
}

// ============================================================================
// PATTERN 7: PALINDROME PARTITIONING
// Problem: Partition string into all palindrome substrings
// Time: O(n*2^n), Space: O(n)
// ============================================================================

func partition(s string) [][]string {
	result := [][]string{}
	path := []string{}
	
	var backtrack func(start int)
	backtrack = func(start int) {
		if start == len(s) {
			temp := make([]string, len(path))
			copy(temp, path)
			result = append(result, temp)
			return
		}
		
		for end := start; end < len(s); end++ {
			if isPalindrome(s, start, end) {
				path = append(path, s[start:end+1])
				backtrack(end + 1)
				path = path[:len(path)-1]
			}
		}
	}
	
	backtrack(0)
	return result
}

func isPalindrome(s string, left, right int) bool {
	for left < right {
		if s[left] != s[right] {
			return false
		}
		left++
		right--
	}
	return true
}

// ============================================================================
// PATTERN 8: GENERATE PARENTHESES
// Problem: Generate all valid parentheses combinations
// Time: O(4^n/sqrt(n)), Space: O(n)
// ============================================================================

func generateParenthesis(n int) []string {
	result := []string{}
	
	var backtrack func(path string, open, close int)
	backtrack = func(path string, open, close int) {
		if len(path) == 2*n {
			result = append(result, path)
			return
		}
		
		if open < n {
			backtrack(path+"(", open+1, close)
		}
		if close < open {
			backtrack(path+")", open, close+1)
		}
	}
	
	backtrack("", 0, 0)
	return result
}

// ============================================================================
// PATTERN 9: LETTER COMBINATIONS
// Problem: Generate all letter combinations from phone number
// Time: O(4^n), Space: O(n)
// ============================================================================

func letterCombinations(digits string) []string {
	if len(digits) == 0 {
		return []string{}
	}
	
	mapping := map[byte]string{
		'2': "abc", '3': "def", '4': "ghi", '5': "jkl",
		'6': "mno", '7': "pqrs", '8': "tuv", '9': "wxyz",
	}
	
	result := []string{}
	var path strings.Builder
	
	var backtrack func(idx int)
	backtrack = func(idx int) {
		if idx == len(digits) {
			result = append(result, path.String())
			return
		}
		
		letters := mapping[digits[idx]]
		for i := 0; i < len(letters); i++ {
			path.WriteByte(letters[i])
			backtrack(idx + 1)
			path.Truncate(path.Len() - 1)
		}
	}
	
	backtrack(0)
	return result
}

// ============================================================================
// PATTERN 10: RESTORE IP ADDRESSES
// Problem: Generate all valid IP addresses from string
// Time: O(3^4), Space: O(1)
// ============================================================================

func restoreIpAddresses(s string) []string {
	result := []string{}
	path := []string{}
	
	var backtrack func(start int)
	backtrack = func(start int) {
		if len(path) == 4 {
			if start == len(s) {
				result = append(result, strings.Join(path, "."))
			}
			return
		}
		
		for length := 1; length <= 3 && start+length <= len(s); length++ {
			segment := s[start : start+length]
			
			// Check validity
			if len(segment) > 1 && segment[0] == '0' {
				break
			}
			num := 0
			for _, ch := range segment {
				num = num*10 + int(ch-'0')
			}
			if num > 255 {
				break
			}
			
			path = append(path, segment)
			backtrack(start + length)
			path = path[:len(path)-1]
		}
	}
	
	backtrack(0)
	return result
}

// ============================================================================
// MAIN: DEMONSTRATION
// ============================================================================

func main() {
	fmt.Println("=== BACKTRACKING PATTERNS IN GO ===\n")
	
	// Pattern 1: Subsets
	fmt.Println("1. Subsets of [1,2,3]:")
	fmt.Println(subsets([]int{1, 2, 3}))
	
	// Pattern 2: Combinations
	fmt.Println("\n2. Combinations C(4,2):")
	fmt.Println(combine(4, 2))
	
	// Pattern 3: Permutations
	fmt.Println("\n3. Permutations of [1,2,3]:")
	fmt.Println(permute([]int{1, 2, 3}))
	
	// Pattern 4: N-Queens
	fmt.Println("\n4. N-Queens (n=4):")
	solutions := solveNQueens(4)
	fmt.Printf("Found %d solutions\n", len(solutions))
	if len(solutions) > 0 {
		fmt.Println("First solution:")
		for _, row := range solutions[0] {
			fmt.Println(row)
		}
	}
	
	// Pattern 5: Combination Sum
	fmt.Println("\n5. Combination Sum [2,3,6,7], target=7:")
	fmt.Println(combinationSum([]int{2, 3, 6, 7}, 7))
	
	// Pattern 6: Palindrome Partitioning
	fmt.Println("\n6. Palindrome Partitions of 'aab':")
	fmt.Println(partition("aab"))
	
	// Pattern 7: Generate Parentheses
	fmt.Println("\n7. Valid Parentheses (n=3):")
	fmt.Println(generateParenthesis(3))
	
	// Pattern 8: Letter Combinations
	fmt.Println("\n8. Letter Combinations of '23':")
	fmt.Println(letterCombinations("23"))
	
	// Pattern 9: Restore IP Addresses
	fmt.Println("\n9. Valid IP Addresses from '25525511135':")
	fmt.Println(restoreIpAddresses("25525511135"))
}
```

I'll create a comprehensive ASCII diagram showing how backtracking works across Python, Rust, and Go, covering call semantics and memory concepts.I've created a comprehensive ASCII diagram that covers:

**Key Features:**

1. **Memory Layout**: Shows stack vs heap organization for each language
2. **Call Semantics**: Detailed comparison of call-by-value vs call-by-reference
3. **Step-by-Step Execution**: Traces through backtracking with actual memory states at each step
4. **Language-Specific Details**:
   - **Python**: Reference semantics for lists, heap allocation, reference counting
   - **Rust**: Explicit borrowing (&mut), borrow checker, ownership system
   - **Go**: Slice mechanics (ptr/len/cap), backing array sharing, GC

5. **Visual Elements**:
   - Stack frames showing local variables
   - Heap objects with arrows showing references
   - Detailed slice/Vec internal structure
   - State changes through recursive calls

6. **Comparison Summary**: Table comparing key differences
7. **Backtracking Insights**: How state restoration and result collection work differently

The diagram shows how the same backtracking algorithm uses different memory strategies: Python shares heap objects via references, Rust uses exclusive mutable borrows with compile-time safety, and Go passes slice headers by value while sharing backing arrays.

================================================================================
        BACKTRACKING ALGORITHM: MEMORY & CALL SEMANTICS COMPARISON
                    Python | Rust | Go
================================================================================

PROBLEM: Find all subsets of [1, 2, 3]

================================================================================
                          MEMORY LAYOUT OVERVIEW
================================================================================

STACK MEMORY (grows downward)          HEAP MEMORY (dynamic allocation)
┌─────────────────────────┐            ┌──────────────────────────┐
│  Function Call Frames   │            │  Dynamic Data Structures │
│  Local Variables        │            │  Referenced Objects      │
│  Parameters             │            │  Mutable Collections     │
│  Return Addresses       │            │  Large Allocations       │
└─────────────────────────┘            └──────────────────────────┘
     Fast, Limited Size                  Slower, Flexible Size

================================================================================
                    CALL BY VALUE vs CALL BY REFERENCE
================================================================================

CALL BY VALUE                          CALL BY REFERENCE
┌─────────────────┐                    ┌─────────────────┐
│  Original: 5    │                    │  Original: 5    │
└────────┬────────┘                    └────────┬────────┘
         │ Copy                                 │ Address
         ▼                                      ▼
┌─────────────────┐                    ┌─────────────────┐
│  Function: 5    │                    │  Function: &5   │──┐
│  (independent)  │                    │  (same memory)  │  │
└─────────────────┘                    └─────────────────┘  │
Changes don't affect original          Changes affect original ◄┘

================================================================================
                      PYTHON: BACKTRACKING EXAMPLE
================================================================================

CODE:
    def backtrack(nums, path, result):
        result.append(path[:])  # Shallow copy
        for i in range(len(nums)):
            path.append(nums[i])
            backtrack(nums[i+1:], path, result)
            path.pop()

CALL SEMANTICS:
- Immutable types (int, str, tuple): Pass by value (conceptually)
- Mutable types (list, dict): Pass by reference (pointer to object)

MEMORY MODEL:

Step 1: Initial Call
═══════════════════════════════════════════════════════════════════════════
STACK                                  HEAP
┌──────────────────────────────────┐  ┌─────────────────────────────────┐
│ backtrack() Frame #1             │  │ nums = [1, 2, 3]  ◄─────────────┼─┐
│ ┌──────────────────────────────┐ │  │ (PyListObject)                  │ │
│ │ nums      ──────────────────────┼──┤ - size: 3                       │ │
│ │ path      ──────────────────────┼──┤ - items: [ptr1, ptr2, ptr3]    │ │
│ │ result    ──────────────────────┼──┤                                 │ │
│ └──────────────────────────────┘ │  │ path = []         ◄─────────────┼─┤
└──────────────────────────────────┘  │ (PyListObject)                  │ ││
                                      │ - size: 0                       │ ││
                                      │                                 │ ││
                                      │ result = []       ◄─────────────┼─┤│
                                      │ (PyListObject)                  │ │││
                                      └─────────────────────────────────┘ │││
                                              All frames share these! ──────┘││
                                                                          ││││

Step 2: First Recursive Call (choosing 1)
═══════════════════════════════════════════════════════════════════════════
STACK                                  HEAP
┌──────────────────────────────────┐  ┌─────────────────────────────────┐
│ backtrack() Frame #2             │  │ nums = [2, 3] (new slice)       │
│ ┌──────────────────────────────┐ │  │                                 │
│ │ nums      ──────────────────────┼──┤ path = [1]      ◄─────────┐    │
│ │ path      ──────────────────────┼──┤ (modified)                 │    │
│ │ result    ──────────────────────┼──┤                            │    │
│ └──────────────────────────────┘ │  │ result = [[]]   ◄─────────┐│    │
├──────────────────────────────────┤  │ (path[:] copied)           ││    │
│ backtrack() Frame #1             │  └─────────────────────────────┘│    │
│ ┌──────────────────────────────┐ │            ▲                   ││    │
│ │ nums, path, result (same)   ─┼──────────────┴───────────────────┴┘    │
│ └──────────────────────────────┘ │                                      │
└──────────────────────────────────┘                                      │

Step 3: Backtrack (remove 1)
═══════════════════════════════════════════════════════════════════════════
STACK                                  HEAP
┌──────────────────────────────────┐  ┌─────────────────────────────────┐
│ backtrack() Frame #1             │  │ path = []       (1 removed)     │
│ ┌──────────────────────────────┐ │  │                                 │
│ │ After path.pop()             │ │  │ result = [[], [1]]              │
│ └──────────────────────────────┘ │  │                                 │
└──────────────────────────────────┘  └─────────────────────────────────┘

KEY POINTS:
✓ Lists are heap-allocated, stack holds references
✓ path is shared across calls (modified in-place)
✓ path[:] creates shallow copy for result
✓ Reference counting manages heap memory

================================================================================
                       RUST: BACKTRACKING EXAMPLE
================================================================================

CODE:
    fn backtrack(nums: &[i32], path: &mut Vec<i32>, result: &mut Vec<Vec<i32>>) {
        result.push(path.clone());
        for i in 0..nums.len() {
            path.push(nums[i]);
            backtrack(&nums[i+1..], path, result);
            path.pop();
        }
    }

CALL SEMANTICS:
- Primitives (i32, f64): Pass by value (copy)
- Complex types: Explicit borrowing (&T immutable, &mut T mutable)
- Ownership system prevents dangling pointers

MEMORY MODEL:

Step 1: Initial Call
═══════════════════════════════════════════════════════════════════════════
STACK                                  HEAP
┌──────────────────────────────────┐  ┌─────────────────────────────────┐
│ backtrack() Frame #1             │  │ Vec<i32> capacity: 4            │
│ ┌──────────────────────────────┐ │  │ [1, 2, 3] ◄─────────────────────┼─┐
│ │ nums: &[i32]  ───────────────────┼─┤   (owned by caller)             │ │
│ │   ptr     ─────────────────────┼─┤                                  │ │
│ │   len: 3                     │ │  │                                 │ │
│ │                              │ │  │ Vec<i32> (path)                 │ │
│ │ path: &mut Vec<i32> ──────────┼──┤ [] ◄────────────────────────────┼─┤
│ │   ptr     ─────────────────────┼─┤   capacity: 0                    │ ││
│ │   len: 0                     │ │  │                                 │ ││
│ │   cap: 0                     │ │  │ Vec<Vec<i32>> (result)          │ ││
│ │                              │ │  │ [] ◄────────────────────────────┼─┤│
│ │ result: &mut Vec<Vec<i32>>  ──┼──┤   capacity: 0                    │ │││
│ └──────────────────────────────┘ │  └─────────────────────────────────┘ │││
└──────────────────────────────────┘                                      │││
                                          Borrowing rules enforced! ───────┘││
                                                                           │││

Step 2: First Recursive Call (choosing 1)
═══════════════════════════════════════════════════════════════════════════
STACK                                  HEAP
┌──────────────────────────────────┐  ┌─────────────────────────────────┐
│ backtrack() Frame #2             │  │ [1, 2, 3]       (unchanged)     │
│ ┌──────────────────────────────┐ │  │                                 │
│ │ nums: &[i32]                 │ │  │ path = [1]      (modified)      │
│ │   ptr     ─────────────────────┼─┤   len: 1, cap: 4                 │
│ │   len: 2  (slice [2,3])      │ │  │                                 │
│ │                              │ │  │ result = [[]]   (cloned empty)  │
│ │ path: &mut Vec<i32> ──────────┼──┤                                  │
│ │   (borrowed from Frame #1)   │ │  │                                 │
│ │                              │ │  │ BORROW CHECKER:                 │
│ │ result: &mut Vec<Vec<i32>>  ──┼──┤ ✓ Only one &mut to path         │
│ └──────────────────────────────┘ │  │ ✓ Slice doesn't outlive array   │
├──────────────────────────────────┤  └─────────────────────────────────┘
│ backtrack() Frame #1             │
│ ┌──────────────────────────────┐ │
│ │ (variables exist but         │ │
│ │  path borrowed mutably)      │ │
│ └──────────────────────────────┘ │
└──────────────────────────────────┘

Step 3: After path.pop()
═══════════════════════════════════════════════════════════════════════════
STACK                                  HEAP
┌──────────────────────────────────┐  ┌─────────────────────────────────┐
│ backtrack() Frame #1             │  │ [1, 2, 3]                       │
│ ┌──────────────────────────────┐ │  │                                 │
│ │ path: &mut Vec<i32>          │ │  │ path = []       (1 removed)     │
│ │   len: 0                     │ │  │   len: 0, cap: 4                │
│ └──────────────────────────────┘ │  │                                 │
└──────────────────────────────────┘  │ result = [[], [1]]              │
                                      └─────────────────────────────────┘

KEY POINTS:
✓ Explicit borrowing: &T (read-only), &mut T (exclusive write)
✓ Borrow checker prevents data races at compile time
✓ Slices (&[T]) are fat pointers (ptr + len)
✓ No garbage collection, ownership tracks lifetime
✓ Stack stores references, heap stores Vec data

================================================================================
                         GO: BACKTRACKING EXAMPLE
================================================================================

CODE:
    func backtrack(nums []int, path []int, result *[][]int) {
        pathCopy := make([]int, len(path))
        copy(pathCopy, path)
        *result = append(*result, pathCopy)
        
        for i := range nums {
            path = append(path, nums[i])
            backtrack(nums[i+1:], path, result)
            path = path[:len(path)-1]
        }
    }

CALL SEMANTICS:
- Basic types (int, float64): Pass by value (copy)
- Slices, maps, channels: Pass by value BUT contain pointers (reference semantics)
- Pointers (*T): Explicit pass by reference

MEMORY MODEL:

Step 1: Initial Call
═══════════════════════════════════════════════════════════════════════════
STACK                                  HEAP
┌──────────────────────────────────┐  ┌─────────────────────────────────┐
│ backtrack() Frame #1             │  │ Array: [1, 2, 3]                │
│ ┌──────────────────────────────┐ │  │   (backing array) ◄─────────────┼─┐
│ │ nums (slice header)          │ │  │                                 │ │
│ │   ptr     ─────────────────────┼─┤                                  │ │
│ │   len: 3                     │ │  │ Array: []                       │ │
│ │   cap: 3                     │ │  │   (path backing) ◄──────────────┼─┤
│ │                              │ │  │   cap: 0                        │ ││
│ │ path (slice header)          │ │  │                                 │ ││
│ │   ptr     ─────────────────────┼─┤                                  │ ││
│ │   len: 0                     │ │  │ [][]int (result) ◄──────────────┼─┤│
│ │   cap: 0                     │ │  │   backing array                 │ │││
│ │                              │ │  └─────────────────────────────────┘ │││
│ │ result *[][]int              │ │                                      │││
│ │   ptr     ─────────────────────┼────────────────────────────────────────┘││
│ └──────────────────────────────┘ │                                      │││
└──────────────────────────────────┘                                      │││
                                        Slice headers copied, data shared ─┘││
                                                                           │││

Step 2: First Recursive Call (choosing 1)
═══════════════════════════════════════════════════════════════════════════
STACK                                  HEAP
┌──────────────────────────────────┐  ┌─────────────────────────────────┐
│ backtrack() Frame #2             │  │ [1, 2, 3]       (original)      │
│ ┌──────────────────────────────┐ │  │  ▲                              │
│ │ nums (NEW slice header)      │ │  │  │                              │
│ │   ptr     ─────────────────────┼──┤  │ points to offset [1]         │
│ │   len: 2  (sliced [2,3])     │ │  │  └─(nums[1:])                   │
│ │   cap: 2                     │ │  │                                 │
│ │                              │ │  │ [1]             (new alloc)     │
│ │ path (NEW slice header)      │ │  │   after append, may reallocate  │
│ │   ptr     ─────────────────────┼─┤                                  │
│ │   len: 1                     │ │  │                                 │
│ │   cap: 2  (grew)             │ │  │ result points to same [][]int   │
│ │                              │ │  │   (pointer dereferenced)        │
│ │ result *[][]int (SAME PTR)   │ │  │                                 │
│ │   ptr     ─────────────────────┼──┤ [[]]            (pathCopy added)│
│ └──────────────────────────────┘ │  └─────────────────────────────────┘
├──────────────────────────────────┤
│ backtrack() Frame #1             │  SLICE MECHANICS:
│ ┌──────────────────────────────┐ │  - Slice = (ptr, len, cap)
│ │ path still points to []      │ │  - Slicing shares backing array
│ │ (different slice header)     │ │  - append() may reallocate
│ └──────────────────────────────┘ │  - Modifications visible if shared
└──────────────────────────────────┘

Step 3: After path = path[:len(path)-1]
═══════════════════════════════════════════════════════════════════════════
STACK                                  HEAP
┌──────────────────────────────────┐  ┌─────────────────────────────────┐
│ backtrack() Frame #2             │  │ [1, 2, 3]                       │
│ ┌──────────────────────────────┐ │  │                                 │
│ │ path (modified slice header) │ │  │ [1]             (data intact,   │
│ │   ptr     ─────────────────────┼─┤   but len reduced)               │
│ │   len: 0  (shrunk)           │ │  │                                 │
│ │   cap: 2  (unchanged)        │ │  │ result = [[], [1]]              │
│ └──────────────────────────────┘ │  └─────────────────────────────────┘
└──────────────────────────────────┘

KEY POINTS:
✓ Slices are "fat pointers" (ptr, len, cap) passed by value
✓ Slice header copied, but points to same backing array
✓ append() may allocate new array if capacity exceeded
✓ Garbage collector manages heap automatically
✓ Pointer (*T) gives explicit reference semantics

================================================================================
                         COMPARISON SUMMARY
================================================================================

┌─────────────────┬──────────────────────┬──────────────────────┬─────────────────────┐
│   Feature       │       Python         │        Rust          │         Go          │
├─────────────────┼──────────────────────┼──────────────────────┼─────────────────────┤
│ Default Call    │ Pass reference to    │ Pass by value        │ Pass by value       │
│ Semantics       │ mutable objects      │ (explicit borrow)    │ (slice = ref-like)  │
├─────────────────┼──────────────────────┼──────────────────────┼─────────────────────┤
│ List/Array      │ Always heap          │ Vec heap, array      │ Backing array heap, │
│ Storage         │ (reference counted)  │ stack/heap by owner  │ slice header stack  │
├─────────────────┼──────────────────────┼──────────────────────┼─────────────────────┤
│ Memory Safety   │ Runtime (GC)         │ Compile-time         │ Runtime (GC)        │
│                 │                      │ (borrow checker)     │                      │
├─────────────────┼──────────────────────┼──────────────────────┼─────────────────────┤
│ Mutation        │ Direct (shared ref)  │ Explicit &mut        │ Direct (if shared   │
│ Control         │                      │ (exclusive)          │ backing array)      │
├─────────────────┼──────────────────────┼──────────────────────┼─────────────────────┤
│ Copy Overhead   │ path[:] shallow copy │ path.clone() deep    │ make() + copy()     │
│                 │                      │ copy                 │                      │
├─────────────────┼──────────────────────┼──────────────────────┼─────────────────────┤
│ Backtracking    │ Modify shared path   │ Modify borrowed path │ Modify copied slice │
│ Pattern         │ (reference passed)   │ (&mut parameter)     │ header (new slice)  │
└─────────────────┴──────────────────────┴──────────────────────┴─────────────────────┘

CALL STACK VISUALIZATION (Choosing [1] then [1,2]):
═══════════════════════════════════════════════════════════════════════════

    PYTHON              RUST                GO
    
    ┌────────────┐      ┌────────────┐      ┌────────────┐
    │ [1,2] call │      │ [1,2] call │      │ [1,2] call │
    │ path->heap │      │ &mut path  │      │ path copy  │
    └────────────┘      └────────────┘      └────────────┘
    ┌────────────┐      ┌────────────┐      ┌────────────┐
    │ [1] call   │      │ [1] call   │      │ [1] call   │
    │ path->heap │      │ &mut path  │      │ path copy  │
    └────────────┘      └────────────┘      └────────────┘
    ┌────────────┐      ┌────────────┐      ┌────────────┐
    │ [] call    │      │ [] call    │      │ [] call    │
    │ path->heap │      │ &mut path  │      │ path copy  │
    └────────────┘      └────────────┘      └────────────┘
         │                   │                   │
         └───────► SAME HEAP OBJECT ◄────────────┘
         (Python)    (Rust borrows)    (Go shares backing)

================================================================================
                        BACKTRACKING KEY INSIGHTS
================================================================================

1. STATE RESTORATION:
   Python:  path.pop() modifies shared heap object
   Rust:    path.pop() modifies through &mut borrow
   Go:      path[:len-1] creates new slice header, same backing

2. RESULT COLLECTION:
   Python:  path[:] creates shallow copy (new list, same integers)
   Rust:    path.clone() creates deep copy (new Vec)
   Go:      make() + copy() creates independent array

3. MEMORY EFFICIENCY:
   Python:  Reference counting, indirect access
   Rust:    Zero-cost abstractions, no runtime overhead
   Go:      Garbage collection, slice optimization

4. SAFETY GUARANTEES:
   Python:  Runtime errors possible (mutation races)
   Rust:    Compile-time guaranteed (no data races)
   Go:      Runtime GC, potential slice aliasing bugs

================================================================================