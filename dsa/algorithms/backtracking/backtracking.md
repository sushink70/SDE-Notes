# Backtracking — Complete Mastery Guide

> *"Backtracking is not brute force. It is disciplined exploration — the art of knowing when to advance, and when to retreat."*

---

## Table of Contents

1. [What Is Backtracking?](#1-what-is-backtracking)
2. [The Mental Model — State Space Trees](#2-the-mental-model--state-space-trees)
3. [The Universal Backtracking Template](#3-the-universal-backtracking-template)
4. [Constraint Satisfaction: The Three Core Operations](#4-constraint-satisfaction-the-three-core-operations)
5. [Pruning — The Soul of Backtracking](#5-pruning--the-soul-of-backtracking)
6. [Complexity Analysis Framework](#6-complexity-analysis-framework)
7. [Problem Category Taxonomy](#7-problem-category-taxonomy)
8. [Classic Problems — Deep Dives](#8-classic-problems--deep-dives)
   - 8.1 [N-Queens](#81-n-queens)
   - 8.2 [Subsets / Power Set](#82-subsets--power-set)
   - 8.3 [Permutations](#83-permutations)
   - 8.4 [Combination Sum](#84-combination-sum)
   - 8.5 [Sudoku Solver](#85-sudoku-solver)
   - 8.6 [Word Search](#86-word-search)
   - 8.7 [Palindrome Partitioning](#87-palindrome-partitioning)
   - 8.8 [Graph Coloring](#88-graph-coloring)
   - 8.9 [Hamiltonian Path / Cycle](#89-hamiltonian-path--cycle)
   - 8.10 [Letter Combinations of a Phone Number](#810-letter-combinations-of-a-phone-number)
9. [Advanced Techniques](#9-advanced-techniques)
   - 9.1 [Forward Checking](#91-forward-checking)
   - 9.2 [Arc Consistency (AC-3)](#92-arc-consistency-ac-3)
   - 9.3 [Constraint Propagation](#93-constraint-propagation)
   - 9.4 [Bitmask Backtracking](#94-bitmask-backtracking)
   - 9.5 [Memoized Backtracking vs DP](#95-memoized-backtracking-vs-dp)
10. [Backtracking vs Other Paradigms](#10-backtracking-vs-other-paradigms)
11. [Expert Mental Models & Intuition Building](#11-expert-mental-models--intuition-building)
12. [Common Mistakes & How to Avoid Them](#12-common-mistakes--how-to-avoid-them)
13. [Master Problem-Solving Framework](#13-master-problem-solving-framework)

---

## 1. What Is Backtracking?

Backtracking is a **systematic, depth-first algorithmic technique** for solving problems that require searching through a potentially enormous set of candidate solutions. It incrementally builds candidates to the solution and **abandons a candidate (backtracks) the moment it determines that this candidate cannot lead to a valid solution**.

This is its defining power: it does not enumerate all possibilities blindly — it *prunes* branches of the search space, often reducing exponential work dramatically.

### Etymology of the Idea

The word "backtrack" was coined by **D.H. Lehmer** in the 1950s. The concept formalizes what humans do naturally: when solving a maze, if you hit a dead end, you retrace your steps to the last decision point and try another path.

### Key Characteristics

| Property | Description |
|---|---|
| **Search strategy** | Depth-First Search (DFS) |
| **Problem type** | Constraint satisfaction, enumeration, optimization |
| **State** | A partial candidate solution built incrementally |
| **Pruning** | Abandoning a path when constraints are violated |
| **Completeness** | Guaranteed to find all solutions (if asked) |
| **Optimality** | Not inherently optimal — requires extra logic |

### Backtracking vs Brute Force

Brute force generates **all** candidates and then filters. Backtracking **never generates** candidates it knows are invalid. The difference in practice is the difference between a combinatorial explosion and a tractable algorithm.

```
Brute Force:  Generate → Filter → Answer
Backtracking: Explore → Prune early → Build → Answer
```

---

## 2. The Mental Model — State Space Trees

Every backtracking problem can be mapped to an **implicit tree** called the **State Space Tree**.

```
Root = Empty / Initial State
|
+-- Choice 1 --> [Partial State]
|       |
|       +-- Choice 1.1 --> [Deeper Partial State]
|       |         |
|       |         +-- (pruned: constraint violated)
|       |
|       +-- Choice 1.2 --> [Deeper Partial State]
|                 |
|                 +-- SOLUTION FOUND (leaf node)
|
+-- Choice 2 --> [Partial State]
        |
        +-- (pruned: constraint violated)
```

### Key Insight

- **Each node** in the tree represents a **partial solution state**.
- **Each edge** represents a **choice / decision**.
- **Leaf nodes** are either complete solutions or dead ends.
- **Pruning** cuts entire subtrees before expanding them.

### The Three Types of Nodes

1. **Live node** — Generated but not yet expanded (on the stack).
2. **E-node** (Expanding node) — Currently being explored.
3. **Dead node** — Pruned or fully explored; never revisited.

### State Space Size

For a problem with `n` positions and `k` choices at each position:
- **Without pruning**: O(k^n) nodes
- **With pruning**: Depends on constraint density — can be orders of magnitude smaller

This is why backtracking's *worst case* is exponential but its *practical case* is often dramatically better.

---

## 3. The Universal Backtracking Template

All backtracking problems follow the same fundamental skeleton. Internalizing this template is the single most important step.

### Pseudocode Template

```
function backtrack(state, choices):
    if is_solution(state):
        record(state)
        return  // or return true for decision problems
    
    for each choice in get_valid_choices(state, choices):
        make_choice(state, choice)          // CHOOSE
        backtrack(state, choices)           // EXPLORE
        undo_choice(state, choice)          // UNCHOOSE (backtrack)
```

### The Three Sacred Operations

1. **CHOOSE**: Apply a choice to the current state.
2. **EXPLORE**: Recurse deeper with the updated state.
3. **UNCHOOSE**: Undo the choice, restoring the state exactly.

The UNCHOOSE step is what makes backtracking elegant — it reuses a single mutable state object rather than copying it for every recursive call.

### Go Implementation — Generic Template

```go
package backtracking

// Generic backtracking skeleton in Go.
// Replace types and logic with problem-specific code.

func backtrack(
    state []int,         // current partial solution
    choices []int,       // available choices
    results *[][]int,    // accumulator for complete solutions
) {
    // Base case: is the current state a complete solution?
    if isSolution(state) {
        // Deep copy — NEVER store a reference to mutable state
        snapshot := make([]int, len(state))
        copy(snapshot, state)
        *results = append(*results, snapshot)
        return
    }

    for _, choice := range choices {
        // Pruning: skip choices that violate constraints
        if !isValid(state, choice) {
            continue
        }

        // CHOOSE
        state = append(state, choice)

        // EXPLORE
        backtrack(state, choices, results)

        // UNCHOOSE — restore to previous state
        state = state[:len(state)-1]
    }
}

func isSolution(state []int) bool {
    // Problem-specific
    return false
}

func isValid(state []int, choice int) bool {
    // Problem-specific constraint check
    return true
}
```

### Rust Implementation — Generic Template

```rust
fn backtrack(
    state: &mut Vec<i32>,
    choices: &[i32],
    results: &mut Vec<Vec<i32>>,
) {
    // Base case: complete solution
    if is_solution(state) {
        results.push(state.clone()); // clone = deep copy
        return;
    }

    for &choice in choices {
        // Pruning: skip invalid choices
        if !is_valid(state, choice) {
            continue;
        }

        // CHOOSE
        state.push(choice);

        // EXPLORE
        backtrack(state, choices, results);

        // UNCHOOSE
        state.pop();
    }
}

fn is_solution(state: &[i32]) -> bool {
    // Problem-specific
    false
}

fn is_valid(state: &[i32], choice: i32) -> bool {
    // Problem-specific
    true
}
```

### C Implementation — Generic Template

```c
#include <stdio.h>
#include <string.h>
#include <stdbool.h>

#define MAX_DEPTH 20
#define MAX_RESULTS 10000

int state[MAX_DEPTH];
int state_len = 0;
int results[MAX_RESULTS][MAX_DEPTH];
int result_lens[MAX_RESULTS];
int result_count = 0;

bool is_solution(int depth) {
    // Problem-specific
    return false;
}

bool is_valid(int choice, int depth) {
    // Problem-specific
    return true;
}

void backtrack(int choices[], int num_choices, int depth) {
    if (is_solution(depth)) {
        // Record solution
        memcpy(results[result_count], state, depth * sizeof(int));
        result_lens[result_count] = depth;
        result_count++;
        return;
    }

    for (int i = 0; i < num_choices; i++) {
        int choice = choices[i];

        if (!is_valid(choice, depth)) {
            continue;
        }

        // CHOOSE
        state[depth] = choice;

        // EXPLORE
        backtrack(choices, num_choices, depth + 1);

        // UNCHOOSE — in C with index-based state, nothing to undo
        // (state[depth] will be overwritten next iteration)
    }
}
```

**Note on C**: In C, because we use index-based state arrays, "unchoosing" is implicit — the next iteration overwrites the slot. However, for problems with auxiliary data structures (visited arrays, constraint tables), explicit undo logic is required.

---

## 4. Constraint Satisfaction: The Three Core Operations

Backtracking is the backbone of **Constraint Satisfaction Problems (CSPs)**. A CSP is defined by:

- **Variables**: `X = {X1, X2, ..., Xn}` — what we are assigning values to
- **Domains**: `D = {D1, D2, ..., Dn}` — valid values for each variable
- **Constraints**: `C` — rules that must hold between variable assignments

### How Backtracking Solves CSPs

1. **Select** an unassigned variable.
2. **Try** each value in its domain.
3. **Check** if the assignment satisfies all constraints with already-assigned variables.
4. If consistent: recurse. If not: try next value. If no values remain: backtrack.

### Variable Ordering Heuristics (Expert-Level Optimization)

These heuristics dramatically reduce the search tree:

| Heuristic | Description | Effect |
|---|---|---|
| **MRV** (Minimum Remaining Values) | Choose the variable with the fewest legal values | Detects failures early |
| **Degree Heuristic** | Choose the variable involved in the most constraints with unassigned variables | Breaks MRV ties |
| **LCV** (Least Constraining Value) | Choose the value that rules out the fewest choices for neighbors | Keeps options open |

---

## 5. Pruning — The Soul of Backtracking

Pruning is what separates an expert's backtracking from a novice's. There are two primary forms:

### 5.1 Explicit Pruning (Constraint Checking)

You check constraints at each step and skip invalid choices immediately.

```
if !is_valid(state, choice):
    continue  // prune this branch entirely
```

This is the most common form and appears in virtually every backtracking problem.

### 5.2 Bound-Based Pruning (Branch and Bound)

Used in optimization backtracking (e.g., finding the *minimum* or *maximum*). You compute an optimistic bound for the current partial solution and abandon paths that cannot beat the current best.

```
if optimistic_bound(state) >= best_known_cost:
    return  // this branch can never be better
```

### 5.3 Symmetry Breaking

Many problems have symmetric solutions that are logically identical. Pruning symmetric branches avoids redundant work.

Example: In generating subsets, always choose elements in sorted order to avoid generating `{1,3}` and `{3,1}` as distinct.

### 5.4 Dead-End Detection (Forward Checking)

Before expanding a node, peek ahead to see if any remaining variable has *no* legal values left. If so, prune immediately without expanding.

---

## 6. Complexity Analysis Framework

Analyzing backtracking complexity requires understanding the state space tree structure.

### General Formula

```
Time Complexity = O(nodes in state space tree × work per node)
```

Work per node is typically O(n) for constraint checking.

### Common Complexity Classes

| Problem Type | State Space Size | Typical Complexity |
|---|---|---|
| Permutations of n | n! leaves | O(n · n!) |
| Subsets of n | 2^n leaves | O(n · 2^n) |
| k-combinations of n | C(n,k) leaves | O(n · C(n,k)) |
| N-Queens | << n! (heavy pruning) | ~O(n!) worst, much less in practice |
| Sudoku | << 9^81 (heavy pruning) | Practically O(1) for valid boards |

### The Pruning Factor

The real complexity of backtracking is:

```
T(n) = (branches at each node) ^ (depth) × (pruning factor)
```

Where pruning factor ∈ [0, 1] — closer to 0 means more pruning, closer to 1 means brute force.

### Space Complexity

Backtracking uses the **call stack** as its primary data structure.

```
Space = O(depth of recursion × state size per level)
```

For most problems, depth = n, giving O(n) stack frames.

---

## 7. Problem Category Taxonomy

Categorizing problems before solving them is a critical expert habit.

### Category 1: Existence Problems
*"Does a solution exist?"*
- Return `true/false` on first find
- Prune aggressively
- Examples: Sudoku solvability check, Hamiltonian path existence

### Category 2: Enumeration Problems
*"Find ALL solutions."*
- Collect every complete state
- Never short-circuit on first find
- Examples: All permutations, all subsets, all N-Queens configurations

### Category 3: Optimization Problems
*"Find the BEST solution."*
- Track current best
- Use bound-based pruning
- Examples: Minimum cost path, 0/1 Knapsack via backtracking

### Category 4: Counting Problems
*"How many solutions exist?"*
- Increment counter at base case
- No need to store solutions
- Examples: Count permutations satisfying a constraint

### Decision Table: Recognizing Backtracking Problems

| Signal in Problem | Likely Approach |
|---|---|
| "Generate all..." | Enumeration backtracking |
| "Find if possible..." | Existence backtracking |
| Grid/board with rules | CSP backtracking |
| "Combinations/Permutations..." | Enumeration with pruning |
| Nested choices with undo | Classic backtracking |
| "Partition into..." | Set/grouping backtracking |

---

## 8. Classic Problems — Deep Dives

---

### 8.1 N-Queens

**Problem**: Place N queens on an N×N chessboard such that no two queens attack each other (same row, column, or diagonal).

#### Expert Reasoning Before Coding

- **Key observation**: One queen per row (forced). So we place queens row by row.
- **State**: `queens[i]` = column where queen in row `i` is placed.
- **Constraints**: No two queens share a column or diagonal.
  - Same column: `queens[i] == queens[j]`
  - Same diagonal: `|queens[i] - queens[j]| == |i - j|`
- **Pruning**: Check all three constraints before placing.
- **Optimization**: Use three boolean arrays to track occupied columns and diagonals in O(1).

#### Go Implementation

```go
package nqueens

func SolveNQueens(n int) [][]string {
    queens := make([]int, n) // queens[row] = col
    for i := range queens {
        queens[i] = -1
    }

    // O(1) constraint lookup structures
    cols := make([]bool, n)
    diag1 := make([]bool, 2*n-1) // major diagonal: row - col + n - 1
    diag2 := make([]bool, 2*n-1) // minor diagonal: row + col

    var results [][]string

    var backtrack func(row int)
    backtrack = func(row int) {
        // Base case: all rows filled
        if row == n {
            results = append(results, buildBoard(queens, n))
            return
        }

        for col := 0; col < n; col++ {
            d1 := row - col + n - 1
            d2 := row + col

            // Pruning: check all three constraints at once
            if cols[col] || diag1[d1] || diag2[d2] {
                continue
            }

            // CHOOSE
            queens[row] = col
            cols[col] = true
            diag1[d1] = true
            diag2[d2] = true

            // EXPLORE
            backtrack(row + 1)

            // UNCHOOSE
            queens[row] = -1
            cols[col] = false
            diag1[d1] = false
            diag2[d2] = false
        }
    }

    backtrack(0)
    return results
}

func buildBoard(queens []int, n int) []string {
    board := make([]string, n)
    row := make([]byte, n)
    for i, col := range queens {
        for j := range row {
            row[j] = '.'
        }
        row[col] = 'Q'
        board[i] = string(row)
    }
    return board
}
```

#### Rust Implementation

```rust
pub fn solve_n_queens(n: usize) -> Vec<Vec<String>> {
    let mut queens = vec![usize::MAX; n]; // queens[row] = col, MAX = unset
    let mut cols = vec![false; n];
    let mut diag1 = vec![false; 2 * n - 1]; // row - col + n - 1
    let mut diag2 = vec![false; 2 * n - 1]; // row + col
    let mut results = Vec::new();

    backtrack(0, n, &mut queens, &mut cols, &mut diag1, &mut diag2, &mut results);
    results
}

fn backtrack(
    row: usize,
    n: usize,
    queens: &mut Vec<usize>,
    cols: &mut Vec<bool>,
    diag1: &mut Vec<bool>,
    diag2: &mut Vec<bool>,
    results: &mut Vec<Vec<String>>,
) {
    if row == n {
        results.push(build_board(queens, n));
        return;
    }

    for col in 0..n {
        let d1 = row + n - 1 - col; // row - col + n - 1, avoiding underflow
        let d2 = row + col;

        if cols[col] || diag1[d1] || diag2[d2] {
            continue; // prune
        }

        // CHOOSE
        queens[row] = col;
        cols[col] = true;
        diag1[d1] = true;
        diag2[d2] = true;

        // EXPLORE
        backtrack(row + 1, n, queens, cols, diag1, diag2, results);

        // UNCHOOSE
        queens[row] = usize::MAX;
        cols[col] = false;
        diag1[d1] = false;
        diag2[d2] = false;
    }
}

fn build_board(queens: &[usize], n: usize) -> Vec<String> {
    queens
        .iter()
        .map(|&col| {
            let mut row = vec![b'.'; n];
            row[col] = b'Q';
            String::from_utf8(row).unwrap()
        })
        .collect()
}
```

#### C Implementation

```c
#include <stdio.h>
#include <stdbool.h>
#include <string.h>
#include <stdlib.h>

#define MAXN 16

int queens[MAXN];
bool cols[MAXN];
bool diag1[2 * MAXN]; // row - col + N - 1
bool diag2[2 * MAXN]; // row + col

int solutions = 0;

void solve(int row, int n) {
    if (row == n) {
        solutions++;
        // Print or store solution here
        return;
    }

    for (int col = 0; col < n; col++) {
        int d1 = row - col + n - 1;
        int d2 = row + col;

        if (cols[col] || diag1[d1] || diag2[d2]) {
            continue; // prune
        }

        // CHOOSE
        queens[row] = col;
        cols[col] = true;
        diag1[d1] = true;
        diag2[d2] = true;

        // EXPLORE
        solve(row + 1, n);

        // UNCHOOSE
        cols[col] = false;
        diag1[d1] = false;
        diag2[d2] = false;
    }
}

int count_n_queens(int n) {
    memset(cols, false, sizeof(cols));
    memset(diag1, false, sizeof(diag1));
    memset(diag2, false, sizeof(diag2));
    solutions = 0;
    solve(0, n);
    return solutions;
}
```

**Complexity**: Time O(N!), Space O(N). With diagonal bitmasks the constant factor drops significantly.

**Hidden Insight**: The diagonal check `|r1 - r2| == |c1 - c2|` is equivalent to checking `r1 - c1 == r2 - c2` (major diagonal index) or `r1 + c1 == r2 + c2` (minor diagonal index). This converts a comparison to an array lookup.

---

### 8.2 Subsets / Power Set

**Problem**: Generate all subsets of a given set of distinct integers.

#### Expert Reasoning

- **State**: Current subset being built.
- **Decision at each step**: Include or exclude the next element.
- **Depth**: Exactly `n` levels deep. Every path from root to leaf is a valid subset.
- **No pruning needed** — all 2^n subsets are valid.
- **Key**: Use a `start` index to avoid duplicates and ensure each element is considered only once.

#### Go Implementation

```go
package subsets

func Subsets(nums []int) [][]int {
    results := [][]int{}
    current := []int{}

    var backtrack func(start int)
    backtrack = func(start int) {
        // Every node in the tree is a valid subset (including root = empty set)
        snapshot := make([]int, len(current))
        copy(snapshot, current)
        results = append(results, snapshot)

        for i := start; i < len(nums); i++ {
            // CHOOSE: include nums[i]
            current = append(current, nums[i])

            // EXPLORE: only consider elements after i
            backtrack(i + 1)

            // UNCHOOSE
            current = current[:len(current)-1]
        }
    }

    backtrack(0)
    return results
}
```

#### Rust Implementation

```rust
pub fn subsets(nums: Vec<i32>) -> Vec<Vec<i32>> {
    let mut results = Vec::new();
    let mut current = Vec::new();
    backtrack(0, &nums, &mut current, &mut results);
    results
}

fn backtrack(
    start: usize,
    nums: &[i32],
    current: &mut Vec<i32>,
    results: &mut Vec<Vec<i32>>,
) {
    // Record current state as a valid subset
    results.push(current.clone());

    for i in start..nums.len() {
        current.push(nums[i]);         // CHOOSE
        backtrack(i + 1, nums, current, results); // EXPLORE
        current.pop();                  // UNCHOOSE
    }
}
```

#### C Implementation

```c
#include <stdlib.h>
#include <string.h>

#define MAX_N 20
#define MAX_SUBSETS (1 << MAX_N)

int current[MAX_N];
int current_len = 0;
int results[MAX_SUBSETS][MAX_N];
int result_lens[MAX_SUBSETS];
int result_count = 0;

void subsets(int nums[], int n, int start) {
    // Record current subset
    memcpy(results[result_count], current, current_len * sizeof(int));
    result_lens[result_count] = current_len;
    result_count++;

    for (int i = start; i < n; i++) {
        current[current_len++] = nums[i]; // CHOOSE
        subsets(nums, n, i + 1);          // EXPLORE
        current_len--;                     // UNCHOOSE
    }
}
```

#### Handling Duplicates (Subsets II)

When the input contains duplicates, sort first and skip duplicate elements at the same recursion level:

```go
func SubsetsWithDup(nums []int) [][]int {
    sort.Ints(nums) // sort first
    results := [][]int{}
    current := []int{}

    var backtrack func(start int)
    backtrack = func(start int) {
        snapshot := make([]int, len(current))
        copy(snapshot, current)
        results = append(results, snapshot)

        for i := start; i < len(nums); i++ {
            // Skip duplicates at the same decision level
            if i > start && nums[i] == nums[i-1] {
                continue
            }
            current = append(current, nums[i])
            backtrack(i + 1)
            current = current[:len(current)-1]
        }
    }

    backtrack(0)
    return results
}
```

**Complexity**: Time O(n · 2^n), Space O(n).

---

### 8.3 Permutations

**Problem**: Generate all permutations of a list of distinct integers.

#### Expert Reasoning

- **Key difference from subsets**: Order matters. Every element can appear at every position.
- **State**: Current permutation being built.
- **Constraint**: Each element used exactly once → track with `used` boolean array.
- **Depth**: Exactly `n` levels. A permutation is complete when `len(current) == n`.

#### Go Implementation

```go
package permutations

func Permute(nums []int) [][]int {
    n := len(nums)
    results := [][]int{}
    current := []int{}
    used := make([]bool, n)

    var backtrack func()
    backtrack = func() {
        if len(current) == n {
            snapshot := make([]int, n)
            copy(snapshot, current)
            results = append(results, snapshot)
            return
        }

        for i := 0; i < n; i++ {
            if used[i] {
                continue // element already in current permutation
            }

            // CHOOSE
            current = append(current, nums[i])
            used[i] = true

            // EXPLORE
            backtrack()

            // UNCHOOSE
            current = current[:len(current)-1]
            used[i] = false
        }
    }

    backtrack()
    return results
}
```

#### Rust Implementation

```rust
pub fn permute(nums: Vec<i32>) -> Vec<Vec<i32>> {
    let n = nums.len();
    let mut results = Vec::new();
    let mut current = Vec::with_capacity(n);
    let mut used = vec![false; n];
    backtrack(&nums, &mut used, &mut current, &mut results);
    results
}

fn backtrack(
    nums: &[i32],
    used: &mut Vec<bool>,
    current: &mut Vec<i32>,
    results: &mut Vec<Vec<i32>>,
) {
    if current.len() == nums.len() {
        results.push(current.clone());
        return;
    }

    for i in 0..nums.len() {
        if used[i] {
            continue;
        }

        current.push(nums[i]); // CHOOSE
        used[i] = true;

        backtrack(nums, used, current, results); // EXPLORE

        current.pop();         // UNCHOOSE
        used[i] = false;
    }
}
```

#### C Implementation

```c
#include <string.h>
#include <stdbool.h>

#define MAX_N 12
#define MAX_PERMS 479001600 // 12!

int nums_g[MAX_N];
int current[MAX_N];
bool used[MAX_N];
int n_g;
int results[MAX_PERMS][MAX_N];
int result_count = 0;

void permute(int depth) {
    if (depth == n_g) {
        memcpy(results[result_count++], current, n_g * sizeof(int));
        return;
    }

    for (int i = 0; i < n_g; i++) {
        if (used[i]) continue;

        current[depth] = nums_g[i]; // CHOOSE
        used[i] = true;

        permute(depth + 1);         // EXPLORE

        used[i] = false;            // UNCHOOSE
    }
}
```

#### Permutations with Duplicates

Sort and skip same element at same level with same `used` state:

```go
func PermuteUnique(nums []int) [][]int {
    sort.Ints(nums)
    n := len(nums)
    results := [][]int{}
    current := []int{}
    used := make([]bool, n)

    var backtrack func()
    backtrack = func() {
        if len(current) == n {
            snapshot := make([]int, n)
            copy(snapshot, current)
            results = append(results, snapshot)
            return
        }

        for i := 0; i < n; i++ {
            if used[i] {
                continue
            }
            // Skip if same value as previous AND previous is not used in current path
            // This means we're at the same decision level with the same value
            if i > 0 && nums[i] == nums[i-1] && !used[i-1] {
                continue
            }

            current = append(current, nums[i])
            used[i] = true
            backtrack()
            current = current[:len(current)-1]
            used[i] = false
        }
    }

    backtrack()
    return results
}
```

**Complexity**: Time O(n · n!), Space O(n).

---

### 8.4 Combination Sum

**Problem**: Given an array of distinct candidates and a target, find all combinations that sum to target. Each number may be used unlimited times.

#### Expert Reasoning

- **Key**: Unlike permutations, combinations are order-independent. Use `start` index.
- **Unlimited use**: Recurse with `i` (not `i+1`) to allow reuse.
- **Pruning**: If `remaining < 0`, stop immediately.
- **Optimization**: Sort candidates — when a candidate exceeds `remaining`, all subsequent ones will too (early termination in loop).

#### Go Implementation

```go
package combinationsum

import "sort"

func CombinationSum(candidates []int, target int) [][]int {
    sort.Ints(candidates) // enable early termination
    results := [][]int{}
    current := []int{}

    var backtrack func(start, remaining int)
    backtrack = func(start, remaining int) {
        if remaining == 0 {
            snapshot := make([]int, len(current))
            copy(snapshot, current)
            results = append(results, snapshot)
            return
        }

        for i := start; i < len(candidates); i++ {
            // Early termination: candidates are sorted, no need to continue
            if candidates[i] > remaining {
                break
            }

            // CHOOSE
            current = append(current, candidates[i])

            // EXPLORE: i (not i+1) allows reuse of same element
            backtrack(i, remaining-candidates[i])

            // UNCHOOSE
            current = current[:len(current)-1]
        }
    }

    backtrack(0, target)
    return results
}
```

#### Rust Implementation

```rust
pub fn combination_sum(mut candidates: Vec<i32>, target: i32) -> Vec<Vec<i32>> {
    candidates.sort_unstable();
    let mut results = Vec::new();
    let mut current = Vec::new();
    backtrack(0, target, &candidates, &mut current, &mut results);
    results
}

fn backtrack(
    start: usize,
    remaining: i32,
    candidates: &[i32],
    current: &mut Vec<i32>,
    results: &mut Vec<Vec<i32>>,
) {
    if remaining == 0 {
        results.push(current.clone());
        return;
    }

    for i in start..candidates.len() {
        if candidates[i] > remaining {
            break; // early termination: sorted, rest will also be too large
        }

        current.push(candidates[i]);
        backtrack(i, remaining - candidates[i], candidates, current, results);
        current.pop();
    }
}
```

#### Combination Sum II (Each element used once, duplicates in input)

```go
func CombinationSum2(candidates []int, target int) [][]int {
    sort.Ints(candidates)
    results := [][]int{}
    current := []int{}

    var backtrack func(start, remaining int)
    backtrack = func(start, remaining int) {
        if remaining == 0 {
            snapshot := make([]int, len(current))
            copy(snapshot, current)
            results = append(results, snapshot)
            return
        }

        for i := start; i < len(candidates); i++ {
            if candidates[i] > remaining {
                break
            }
            // Skip duplicates at the same level
            if i > start && candidates[i] == candidates[i-1] {
                continue
            }

            current = append(current, candidates[i])
            backtrack(i+1, remaining-candidates[i]) // i+1: each used once
            current = current[:len(current)-1]
        }
    }

    backtrack(0, target)
    return results
}
```

**Complexity**: O(2^(T/M)) where T = target, M = min candidate value.

---

### 8.5 Sudoku Solver

**Problem**: Fill a 9×9 Sudoku grid where each row, column, and 3×3 box contains digits 1–9 exactly once.

#### Expert Reasoning

- **Variables**: 81 cells, 17–30 are pre-filled.
- **Domains**: {1..9} for each empty cell.
- **Constraints**: Row uniqueness, column uniqueness, 3×3 box uniqueness.
- **Key optimization**: Use three 9×9 boolean arrays (or 9-bit integers) for O(1) constraint checking.
- **Order**: Process empty cells in order (or use MRV heuristic for speed).
- **Box index formula**: `box = (row/3)*3 + col/3`

#### Go Implementation

```go
package sudoku

func SolveSudoku(board [][]byte) {
    // rows[r][d] = true means digit d+1 is used in row r
    var rows, cols, boxes [9][9]bool

    // Initialize constraint tables from given board
    for r := 0; r < 9; r++ {
        for c := 0; c < 9; c++ {
            if board[r][c] != '.' {
                d := board[r][c] - '1'
                box := (r/3)*3 + c/3
                rows[r][d] = true
                cols[c][d] = true
                boxes[box][d] = true
            }
        }
    }

    var backtrack func() bool
    backtrack = func() bool {
        // Find next empty cell
        for r := 0; r < 9; r++ {
            for c := 0; c < 9; c++ {
                if board[r][c] != '.' {
                    continue
                }

                box := (r/3)*3 + c/3

                for d := 0; d < 9; d++ {
                    // Pruning: digit already used in row, col, or box
                    if rows[r][d] || cols[c][d] || boxes[box][d] {
                        continue
                    }

                    // CHOOSE
                    board[r][c] = byte('1' + d)
                    rows[r][d] = true
                    cols[c][d] = true
                    boxes[box][d] = true

                    // EXPLORE
                    if backtrack() {
                        return true // solution found, propagate up
                    }

                    // UNCHOOSE
                    board[r][c] = '.'
                    rows[r][d] = false
                    cols[c][d] = false
                    boxes[box][d] = false
                }

                return false // no digit worked for this cell — backtrack
            }
        }
        return true // all cells filled
    }

    backtrack()
}
```

#### Rust Implementation

```rust
pub fn solve_sudoku(board: &mut Vec<Vec<char>>) {
    let mut rows = [[false; 9]; 9];
    let mut cols = [[false; 9]; 9];
    let mut boxes = [[false; 9]; 9];

    // Initialize from pre-filled cells
    for r in 0..9 {
        for c in 0..9 {
            if board[r][c] != '.' {
                let d = (board[r][c] as usize) - ('1' as usize);
                let b = (r / 3) * 3 + c / 3;
                rows[r][d] = true;
                cols[c][d] = true;
                boxes[b][d] = true;
            }
        }
    }

    backtrack(board, &mut rows, &mut cols, &mut boxes);
}

fn backtrack(
    board: &mut Vec<Vec<char>>,
    rows: &mut [[bool; 9]; 9],
    cols: &mut [[bool; 9]; 9],
    boxes: &mut [[bool; 9]; 9],
) -> bool {
    for r in 0..9 {
        for c in 0..9 {
            if board[r][c] != '.' {
                continue;
            }

            let b = (r / 3) * 3 + c / 3;

            for d in 0..9 {
                if rows[r][d] || cols[c][d] || boxes[b][d] {
                    continue; // pruned
                }

                // CHOOSE
                board[r][c] = char::from_digit(d as u32 + 1, 10).unwrap();
                rows[r][d] = true;
                cols[c][d] = true;
                boxes[b][d] = true;

                // EXPLORE
                if backtrack(board, rows, cols, boxes) {
                    return true;
                }

                // UNCHOOSE
                board[r][c] = '.';
                rows[r][d] = false;
                cols[c][d] = false;
                boxes[b][d] = false;
            }

            return false; // no valid digit for this cell
        }
    }
    true // all cells filled
}
```

#### C Implementation

```c
#include <stdbool.h>
#include <string.h>

char board[9][9];
bool rows[9][9];  // rows[r][d]: digit d used in row r
bool cols[9][9];
bool boxes[9][9]; // boxes[b][d]: digit d used in box b

bool solve() {
    for (int r = 0; r < 9; r++) {
        for (int c = 0; c < 9; c++) {
            if (board[r][c] != '.') continue;

            int b = (r / 3) * 3 + c / 3;

            for (int d = 0; d < 9; d++) {
                if (rows[r][d] || cols[c][d] || boxes[b][d]) continue;

                // CHOOSE
                board[r][c] = '1' + d;
                rows[r][d] = cols[c][d] = boxes[b][d] = true;

                // EXPLORE
                if (solve()) return true;

                // UNCHOOSE
                board[r][c] = '.';
                rows[r][d] = cols[c][d] = boxes[b][d] = false;
            }

            return false; // dead end
        }
    }
    return true;
}
```

**Complexity**: Worst case O(9^81) but with constraint propagation practically near O(1) for typical boards.

---

### 8.6 Word Search

**Problem**: Given a 2D grid of characters, determine if a word exists in the grid by connecting adjacent (4-directional) cells. Each cell may be used at most once.

#### Expert Reasoning

- **State**: Current path of cells forming a prefix of the word.
- **Constraint**: Cells not revisited; adjacent cells only.
- **Visited tracking**: Mark cell as visited by temporarily modifying it (elegant in-place trick), or use a visited 2D array.
- **Pruning**: If current cell doesn't match word[depth], stop immediately.

#### Go Implementation

```go
package wordsearch

func Exist(board [][]byte, word string) bool {
    rows := len(board)
    cols := len(board[0])
    w := []byte(word)

    var backtrack func(r, c, depth int) bool
    backtrack = func(r, c, depth int) bool {
        if depth == len(w) {
            return true // entire word matched
        }

        // Boundary check and character match
        if r < 0 || r >= rows || c < 0 || c >= cols {
            return false
        }
        if board[r][c] != w[depth] {
            return false
        }

        // CHOOSE: mark cell as visited using sentinel character
        temp := board[r][c]
        board[r][c] = '#'

        // EXPLORE: 4 directions
        dirs := [][2]int{{0, 1}, {0, -1}, {1, 0}, {-1, 0}}
        found := false
        for _, d := range dirs {
            if backtrack(r+d[0], c+d[1], depth+1) {
                found = true
                break
            }
        }

        // UNCHOOSE: restore cell
        board[r][c] = temp

        return found
    }

    for r := 0; r < rows; r++ {
        for c := 0; c < cols; c++ {
            if backtrack(r, c, 0) {
                return true
            }
        }
    }
    return false
}
```

#### Rust Implementation

```rust
pub fn exist(board: Vec<Vec<char>>, word: String) -> bool {
    let mut board = board;
    let rows = board.len();
    let cols = board[0].len();
    let word: Vec<char> = word.chars().collect();

    for r in 0..rows {
        for c in 0..cols {
            if backtrack(r, c, 0, &mut board, &word, rows, cols) {
                return true;
            }
        }
    }
    false
}

fn backtrack(
    r: usize,
    c: usize,
    depth: usize,
    board: &mut Vec<Vec<char>>,
    word: &[char],
    rows: usize,
    cols: usize,
) -> bool {
    if depth == word.len() {
        return true;
    }
    if r >= rows || c >= cols || board[r][c] != word[depth] {
        return false;
    }

    let temp = board[r][c];
    board[r][c] = '#'; // mark visited

    let directions: [(i32, i32); 4] = [(0, 1), (0, -1), (1, 0), (-1, 0)];
    let found = directions.iter().any(|&(dr, dc)| {
        let nr = r as i32 + dr;
        let nc = c as i32 + dc;
        if nr >= 0 && nc >= 0 {
            backtrack(nr as usize, nc as usize, depth + 1, board, word, rows, cols)
        } else {
            false
        }
    });

    board[r][c] = temp; // restore
    found
}
```

**Complexity**: Time O(M · N · 4^L) where M×N is grid size and L = word length. Space O(L) for recursion stack.

---

### 8.7 Palindrome Partitioning

**Problem**: Given a string, partition it such that every substring is a palindrome. Return all possible partitions.

#### Expert Reasoning

- **State**: Current partition being built.
- **Choice**: At each position, choose the length of the next palindrome segment.
- **Constraint**: The chosen substring must be a palindrome.
- **Optimization**: Precompute all palindrome substrings using DP to make checks O(1).

#### Go Implementation

```go
package palindromepartition

func Partition(s string) [][]string {
    n := len(s)
    results := [][]string{}
    current := []string{}

    // Precompute: isPalin[i][j] = true if s[i..j] is palindrome
    isPalin := make([][]bool, n)
    for i := range isPalin {
        isPalin[i] = make([]bool, n)
    }
    // DP to fill isPalin
    for length := 1; length <= n; length++ {
        for i := 0; i <= n-length; i++ {
            j := i + length - 1
            if s[i] == s[j] && (length <= 2 || isPalin[i+1][j-1]) {
                isPalin[i][j] = true
            }
        }
    }

    var backtrack func(start int)
    backtrack = func(start int) {
        if start == n {
            snapshot := make([]string, len(current))
            copy(snapshot, current)
            results = append(results, snapshot)
            return
        }

        for end := start; end < n; end++ {
            if isPalin[start][end] {
                // CHOOSE: take s[start..end] as next segment
                current = append(current, s[start:end+1])

                // EXPLORE
                backtrack(end + 1)

                // UNCHOOSE
                current = current[:len(current)-1]
            }
        }
    }

    backtrack(0)
    return results
}
```

#### Rust Implementation

```rust
pub fn partition(s: String) -> Vec<Vec<String>> {
    let s: Vec<char> = s.chars().collect();
    let n = s.len();

    // Precompute palindrome table
    let mut is_palin = vec![vec![false; n]; n];
    for len in 1..=n {
        for i in 0..=n - len {
            let j = i + len - 1;
            is_palin[i][j] = s[i] == s[j] && (len <= 2 || is_palin[i + 1][j - 1]);
        }
    }

    let mut results = Vec::new();
    let mut current: Vec<String> = Vec::new();

    backtrack(0, n, &s, &is_palin, &mut current, &mut results);
    results
}

fn backtrack(
    start: usize,
    n: usize,
    s: &[char],
    is_palin: &Vec<Vec<bool>>,
    current: &mut Vec<String>,
    results: &mut Vec<Vec<String>>,
) {
    if start == n {
        results.push(current.clone());
        return;
    }

    for end in start..n {
        if is_palin[start][end] {
            let segment: String = s[start..=end].iter().collect();
            current.push(segment);
            backtrack(end + 1, n, s, is_palin, current, results);
            current.pop();
        }
    }
}
```

**Complexity**: Time O(n · 2^n) total, with palindrome precomputation O(n^2). Space O(n^2) for the DP table.

**Hidden Insight**: Without the palindrome precomputation, you'd check palindromes in O(n) inside the backtracking — making it O(n^2 · 2^n). The DP table reduces the check to O(1), cutting a factor of n.

---

### 8.8 Graph Coloring

**Problem**: Given a graph with `n` vertices and `m` colors, assign a color to each vertex such that no two adjacent vertices share a color.

#### Expert Reasoning

- **Classic CSP**: Variables = vertices, domains = colors, constraints = edges.
- **State**: `color[v]` for each vertex `v`.
- **Pruning**: Before assigning a color, check all neighbors already colored.
- **Ordering**: Process vertices 0..n-1 in order (or use MRV).

#### Go Implementation

```go
package graphcoloring

func GraphColor(graph [][]int, n, m int) []int {
    colors := make([]int, n) // colors[v] = 0 means uncolored

    var backtrack func(vertex int) bool
    backtrack = func(vertex int) bool {
        if vertex == n {
            return true // all vertices colored
        }

        for color := 1; color <= m; color++ {
            if isSafe(graph, colors, vertex, color) {
                // CHOOSE
                colors[vertex] = color

                // EXPLORE
                if backtrack(vertex + 1) {
                    return true
                }

                // UNCHOOSE
                colors[vertex] = 0
            }
        }

        return false // no valid color found
    }

    if backtrack(0) {
        return colors
    }
    return nil
}

func isSafe(graph [][]int, colors []int, vertex, color int) bool {
    for _, neighbor := range graph[vertex] {
        if colors[neighbor] == color {
            return false
        }
    }
    return true
}
```

#### Rust Implementation

```rust
pub fn graph_color(graph: &Vec<Vec<usize>>, n: usize, m: usize) -> Option<Vec<usize>> {
    let mut colors = vec![0usize; n]; // 0 = uncolored
    if backtrack(0, n, m, graph, &mut colors) {
        Some(colors)
    } else {
        None
    }
}

fn backtrack(
    vertex: usize,
    n: usize,
    m: usize,
    graph: &Vec<Vec<usize>>,
    colors: &mut Vec<usize>,
) -> bool {
    if vertex == n {
        return true;
    }

    for color in 1..=m {
        if is_safe(graph, colors, vertex, color) {
            colors[vertex] = color; // CHOOSE

            if backtrack(vertex + 1, n, m, graph, colors) {
                return true; // EXPLORE
            }

            colors[vertex] = 0; // UNCHOOSE
        }
    }

    false
}

fn is_safe(graph: &Vec<Vec<usize>>, colors: &[usize], vertex: usize, color: usize) -> bool {
    graph[vertex].iter().all(|&neighbor| colors[neighbor] != color)
}
```

**Complexity**: Time O(m^n) worst case (m colors, n vertices). Heavy pruning makes this tractable for sparse graphs.

---

### 8.9 Hamiltonian Path / Cycle

**Problem**: Find a path through a graph that visits every vertex exactly once. If it returns to the starting vertex, it is a Hamiltonian *cycle*.

#### Expert Reasoning

- **State**: Current path of visited vertices.
- **Constraint**: Next vertex must be adjacent to current AND not yet visited.
- **Cycle detection**: After visiting all vertices, check if last vertex connects back to start.
- **Pruning**: Dead-end detection — if any unvisited vertex has 0 remaining reachable unvisited neighbors, prune.

#### Go Implementation

```go
package hamiltonian

func HamiltonianPath(graph [][]bool, n int) []int {
    path := make([]int, 0, n)
    visited := make([]bool, n)

    path = append(path, 0) // start from vertex 0
    visited[0] = true

    var backtrack func() bool
    backtrack = func() bool {
        if len(path) == n {
            return true // all vertices visited — Hamiltonian path found
        }

        last := path[len(path)-1]
        for next := 0; next < n; next++ {
            if graph[last][next] && !visited[next] {
                // CHOOSE
                path = append(path, next)
                visited[next] = true

                // EXPLORE
                if backtrack() {
                    return true
                }

                // UNCHOOSE
                path = path[:len(path)-1]
                visited[next] = false
            }
        }

        return false
    }

    if backtrack() {
        return path
    }
    return nil
}

func HamiltonianCycle(graph [][]bool, n int) []int {
    path := make([]int, 0, n+1)
    visited := make([]bool, n)

    path = append(path, 0)
    visited[0] = true

    var backtrack func() bool
    backtrack = func() bool {
        if len(path) == n {
            // Check if last vertex connects back to start (vertex 0)
            return graph[path[n-1]][0]
        }

        last := path[len(path)-1]
        for next := 0; next < n; next++ {
            if graph[last][next] && !visited[next] {
                path = append(path, next)
                visited[next] = true

                if backtrack() {
                    return true
                }

                path = path[:len(path)-1]
                visited[next] = false
            }
        }

        return false
    }

    if backtrack() {
        path = append(path, path[0]) // complete the cycle
        return path
    }
    return nil
}
```

**Complexity**: O(n!) worst case. The Hamiltonian path problem is NP-complete — no known polynomial algorithm exists.

---

### 8.10 Letter Combinations of a Phone Number

**Problem**: Given a string of digits 2-9, return all possible letter combinations using the phone keyboard mapping.

#### Expert Reasoning

- **State**: Current combination being built.
- **Depth**: One level per digit in input.
- **Choices at each level**: Letters mapped to current digit.
- **No pruning needed**: All combinations are valid.

#### Go Implementation

```go
package phonecombinations

func LetterCombinations(digits string) []string {
    if len(digits) == 0 {
        return nil
    }

    mapping := map[byte]string{
        '2': "abc", '3': "def", '4': "ghi", '5': "jkl",
        '6': "mno", '7': "pqrs", '8': "tuv", '9': "wxyz",
    }

    results := []string{}
    current := make([]byte, 0, len(digits))

    var backtrack func(index int)
    backtrack = func(index int) {
        if index == len(digits) {
            results = append(results, string(current))
            return
        }

        for _, ch := range mapping[digits[index]] {
            current = append(current, byte(ch)) // CHOOSE
            backtrack(index + 1)                // EXPLORE
            current = current[:len(current)-1]  // UNCHOOSE
        }
    }

    backtrack(0)
    return results
}
```

#### Rust Implementation

```rust
pub fn letter_combinations(digits: String) -> Vec<String> {
    if digits.is_empty() {
        return vec![];
    }

    let mapping = vec![
        "", "", "abc", "def", "ghi", "jkl",
        "mno", "pqrs", "tuv", "wxyz",
    ];

    let digits: Vec<usize> = digits
        .bytes()
        .map(|b| (b - b'0') as usize)
        .collect();

    let mut results = Vec::new();
    let mut current = String::new();

    backtrack(0, &digits, &mapping, &mut current, &mut results);
    results
}

fn backtrack(
    index: usize,
    digits: &[usize],
    mapping: &[&str],
    current: &mut String,
    results: &mut Vec<String>,
) {
    if index == digits.len() {
        results.push(current.clone());
        return;
    }

    for ch in mapping[digits[index]].chars() {
        current.push(ch);                                          // CHOOSE
        backtrack(index + 1, digits, mapping, current, results);   // EXPLORE
        current.pop();                                             // UNCHOOSE
    }
}
```

**Complexity**: Time O(4^n · n) where n = number of digits (4 = max letters per key, `n` for string construction). Space O(n).

---

## 9. Advanced Techniques

### 9.1 Forward Checking

**Concept**: After making an assignment, immediately check if any *future* variable has its domain *emptied*. If yes, prune before even trying to assign that variable.

**When to use**: Dense constraint graphs (Sudoku, N-Queens with large N).

```go
// After assigning a value to variable v, propagate to neighbors
func forwardCheck(assignment map[int]int, domains map[int][]int, variable, value int, neighbors []int) bool {
    for _, neighbor := range neighbors {
        if _, assigned := assignment[neighbor]; assigned {
            continue
        }
        // Remove value from neighbor's domain
        newDomain := []int{}
        for _, d := range domains[neighbor] {
            if d != value {
                newDomain = append(newDomain, d)
            }
        }
        if len(newDomain) == 0 {
            return false // domain wipeout — prune this branch
        }
        domains[neighbor] = newDomain
    }
    return true
}
```

### 9.2 Arc Consistency (AC-3)

**Concept**: For every pair of variables (Xi, Xj) connected by a constraint, ensure every value in Xi's domain has at least one consistent value in Xj's domain. Remove values that don't — and propagate the removal.

**Algorithm**:
1. Initialize queue with all arcs (Xi, Xj).
2. For each arc, remove inconsistent values from Xi's domain.
3. If Xi's domain changes, re-add all arcs (Xk, Xi) to the queue.
4. Repeat until queue is empty.

```go
type Arc struct{ xi, xj int }

func AC3(domains map[int][]int, constraints map[[2]int]func(a, b int) bool) bool {
    queue := []Arc{}
    for arc := range constraints {
        queue = append(queue, Arc{arc[0], arc[1]})
        queue = append(queue, Arc{arc[1], arc[0]})
    }

    for len(queue) > 0 {
        arc := queue[0]
        queue = queue[1:]

        if revised := revise(domains, constraints, arc.xi, arc.xj); revised {
            if len(domains[arc.xi]) == 0 {
                return false // domain wipeout
            }
            // Re-add all arcs (xk, xi) where xk != xj
            for constraint := range constraints {
                if constraint[1] == arc.xi && constraint[0] != arc.xj {
                    queue = append(queue, Arc{constraint[0], arc.xi})
                }
            }
        }
    }
    return true
}

func revise(domains map[int][]int, constraints map[[2]int]func(a, b int) bool, xi, xj int) bool {
    revised := false
    newDomain := []int{}
    constraint := constraints[[2]int{xi, xj}]

    for _, vx := range domains[xi] {
        consistent := false
        for _, vy := range domains[xj] {
            if constraint(vx, vy) {
                consistent = true
                break
            }
        }
        if consistent {
            newDomain = append(newDomain, vx)
        } else {
            revised = true
        }
    }

    domains[xi] = newDomain
    return revised
}
```

### 9.3 Constraint Propagation

A general technique: after every assignment, use logic to infer and reduce domains of other variables. AC-3 is one form. Others include:

- **Path Consistency**: Ensure consistency along paths of 3+ variables.
- **Singleton Propagation**: If a domain has only one value, assign it immediately.

These techniques transform backtracking from a search into a *reasoning + search* hybrid — dramatically more powerful.

### 9.4 Bitmask Backtracking

For problems where state can be encoded as a bitmask of used/available items, bitwise operations provide O(1) state transitions and constraint checks.

**Example: N-Queens with bitmask**

```go
// Bitmask N-Queens — represents column/diagonal constraints as integers
func SolveNQueensBitmask(n int) int {
    full := (1 << n) - 1 // all n columns used
    count := 0

    var backtrack func(cols, diag1, diag2 int)
    backtrack = func(cols, diag1, diag2 int) {
        if cols == full {
            count++
            return
        }

        // Available columns: not blocked by any constraint
        available := full & ^(cols | diag1 | diag2)

        for available != 0 {
            // Pick the lowest set bit (rightmost available column)
            bit := available & (-available)
            available &= available - 1 // remove this bit

            // Recurse: shift diagonals appropriately
            backtrack(
                cols|bit,
                (diag1|bit)<<1,
                (diag2|bit)>>1,
            )
        }
    }

    backtrack(0, 0, 0)
    return count
}
```

**Key Insight**: `available & (-available)` isolates the lowest set bit in O(1). Shifting diagonals by 1 represents their movement across rows. This is an order of magnitude faster than the array-based approach.

#### Rust Bitmask N-Queens

```rust
pub fn total_n_queens(n: u32) -> i32 {
    let full = (1u32 << n) - 1;
    let mut count = 0;
    backtrack(0, 0, 0, full, &mut count);
    count
}

fn backtrack(cols: u32, diag1: u32, diag2: u32, full: u32, count: &mut i32) {
    if cols == full {
        *count += 1;
        return;
    }

    let mut available = full & !(cols | diag1 | diag2);
    while available != 0 {
        let bit = available & available.wrapping_neg();
        available &= available - 1;
        backtrack(
            cols | bit,
            (diag1 | bit) << 1,
            (diag2 | bit) >> 1,
            full,
            count,
        );
    }
}
```

#### C Bitmask N-Queens

```c
#include <stdio.h>

int n_g;
int full_mask;
int solution_count = 0;

void solve_bitmask(int cols, int diag1, int diag2) {
    if (cols == full_mask) {
        solution_count++;
        return;
    }

    int available = full_mask & ~(cols | diag1 | diag2);
    while (available) {
        int bit = available & (-available);
        available &= available - 1;
        solve_bitmask(
            cols | bit,
            (diag1 | bit) << 1,
            (diag2 | bit) >> 1
        );
    }
}

int count_queens_bitmask(int n) {
    n_g = n;
    full_mask = (1 << n) - 1;
    solution_count = 0;
    solve_bitmask(0, 0, 0);
    return solution_count;
}
```

### 9.5 Memoized Backtracking vs DP

**When do they overlap?**

If a backtracking problem has **overlapping subproblems** (same `(state, remaining)` pair reached multiple times), memoization transforms it into top-down DP.

| | Backtracking | Memoized Backtracking | Bottom-up DP |
|---|---|---|---|
| Overlapping subproblems | No | Yes | Yes |
| All solutions | Yes | Harder | Harder |
| Optimal solution | With extra logic | Yes | Yes |
| Space | O(depth) | O(states) | O(states) |

**Rule**: If the problem asks for *count* or *optimal value* (not enumeration of all paths), consider whether DP applies. If it asks for *all solutions*, backtracking is the natural choice.

---

## 10. Backtracking vs Other Paradigms

### Backtracking vs Recursion

All backtracking is recursive, but not all recursion is backtracking. Backtracking specifically involves:
- Building a state incrementally.
- **Undoing** changes after recursive calls.
- Pruning invalid paths.

### Backtracking vs BFS

| | Backtracking (DFS) | BFS |
|---|---|---|
| Memory | O(depth) | O(width) — can be huge |
| Finds solution | Arbitrary order | Shortest path (unweighted) |
| All solutions | Natural | Needs modification |
| Use case | CSPs, enumeration | Shortest path problems |

### Backtracking vs Dynamic Programming

| | Backtracking | Dynamic Programming |
|---|---|---|
| Subproblem overlap | Handles poorly | Built for it |
| Enumeration | Natural | Difficult |
| Optimization | Possible | Natural |
| State reuse | No (without memo) | Yes |
| Transition | Top-down with undo | Explicit formula |

**Key Insight**: Many problems have both DP and backtracking solutions. DP is superior when you need a count or optimum. Backtracking is superior when you need all solutions or cannot define subproblem structure.

### Backtracking vs Greedy

Greedy makes irrevocable local decisions. Backtracking explores all options and undoes bad ones. Greedy is faster but not always correct. Backtracking is complete (finds all solutions) but slower.

---

## 11. Expert Mental Models & Intuition Building

### Mental Model 1: "The Decision Tree"

Every backtracking problem is a tree of decisions. Before coding, draw (or mentally trace) the tree for a small input. Identify:
- What is the **branching factor** (choices per node)?
- What is the **depth** (length of a solution)?
- What **constraints** reduce branches?

### Mental Model 2: "The Incremental Builder"

Think of yourself as building a Lego structure. At each step, you add one piece (CHOOSE). If the piece doesn't fit (constraint violated), you put it back (UNCHOOSE) and try another. You never tear down the whole structure — only the last piece.

### Mental Model 3: "Prune Early, Prune Often"

The power of backtracking is not the exploration — it is the *abandonment*. Every pruning condition you add is an entire subtree you never visit. Always ask: "Can I detect invalidity *earlier* than I currently do?"

### Mental Model 4: "State as a Stack"

Backtracking implicitly maintains a stack of decisions. The call stack IS the decision stack. When you `return`, you pop one decision. The UNCHOOSE step mirrors this pop by undoing one decision's side effects.

### Mental Model 5: "The Lazy Evaluator"

Backtracking evaluates solutions lazily — it only explores paths as deep as necessary before pruning. This is why it outperforms brute force: it fails *fast* rather than generating and then filtering.

### Cognitive Principle: Chunking the Template

The CHOOSE → EXPLORE → UNCHOOSE pattern should become automatic — a single cognitive chunk. Once internalized, all backtracking problems reduce to: "What are the choices? What are the constraints? What constitutes a solution?" — the template handles the rest.

### Cognitive Principle: Abstracting the State

The hardest part of any backtracking problem is identifying what the *state* is. Practice this:
- What information is needed to decide if a partial solution can be extended?
- What information is needed to check constraints?
- What information defines a complete solution?

The state must contain exactly this — no more, no less.

---

## 12. Common Mistakes & How to Avoid Them

### Mistake 1: Mutating Shared State Without Undoing

```go
// WRONG: append returns new slice but if cap allows, modifies underlying array
results = append(results, current)  // current will be modified later!

// CORRECT: always deep copy
snapshot := make([]int, len(current))
copy(snapshot, current)
results = append(results, snapshot)
```

In Rust, `.clone()` handles this correctly. In Go, always `make` + `copy`. In C, always `memcpy`.

### Mistake 2: Off-by-One in the Start Index

Using `i` vs `i+1` controls whether elements can be reused:
- `backtrack(i, ...)` — current element can be reused (Combination Sum I)
- `backtrack(i+1, ...)` — each element used at most once (Subsets, Combination Sum II)

### Mistake 3: Not Sorting Before Deduplication

Duplicate skipping (`if i > start && nums[i] == nums[i-1]`) only works if the array is **sorted**. Always sort when input has duplicates.

### Mistake 4: Incorrect Base Case

- Returning too early: missing some valid solutions.
- Not returning: infinite recursion.
- Check: does every recursive path hit the base case?

### Mistake 5: Inefficient Constraint Checking

Recomputing constraints from scratch at each node is O(n) per check. Use auxiliary structures (boolean arrays, bitmasks) for O(1) checks. The constraint data structures must be maintained during CHOOSE and restored during UNCHOOSE.

### Mistake 6: Using Global State Without Reset

In C especially, global arrays must be reset between test cases. In Go and Rust, create fresh state per call.

### Mistake 7: Confusing Index-Based and Value-Based State

- **Index-based**: "Which index am I at?" — for subsets, combinations.
- **Value-based**: "Have I used this value?" — for permutations.

Mixing these leads to subtle bugs.

---

## 13. Master Problem-Solving Framework

When encountering any backtracking problem, apply this systematic framework before writing a single line of code:

### Step 1: Classify

- Is this existence, enumeration, counting, or optimization?
- Is it a CSP? Graph problem? String problem? Grid problem?

### Step 2: Define the State Space

- What is the **partial solution state**?
- What are the **choices** at each step?
- What defines a **complete solution**?
- What **constraints** must be satisfied?

### Step 3: Identify Pruning Opportunities

- What constraint violations can be detected early?
- Can I use auxiliary data structures for O(1) constraint checks?
- Can I sort input to enable early termination?
- Are there symmetries I can break?

### Step 4: Design the Recursion

- What parameters does `backtrack()` need?
- What is the base case (complete solution)?
- What is the stopping condition (invalid state)?

### Step 5: Analyze Complexity

- What is the branching factor?
- What is the depth?
- What is the worst-case tree size?
- How much does pruning realistically reduce it?

### Step 6: Implement with the Template

```
backtrack(state):
    if is_complete(state): record/return
    for each choice:
        if is_valid(state, choice):
            CHOOSE: apply choice
            EXPLORE: backtrack(updated_state)
            UNCHOOSE: revert choice
```

### Step 7: Verify with Small Examples

- Trace through a 2-3 element example by hand.
- Verify the state tree matches your mental model.
- Check that UNCHOOSE exactly reverses CHOOSE.

---

## Summary: The Five Laws of Backtracking

1. **The Law of Incrementality**: Build solutions one piece at a time.
2. **The Law of Reversibility**: Every CHOOSE must have a corresponding UNCHOOSE.
3. **The Law of Constraint First**: Check constraints before exploring, not after.
4. **The Law of Early Termination**: Prune as early as possible, as often as possible.
5. **The Law of Deep Copy**: Never store references to mutable state — always snapshot.

---

*Master these principles, and you will not just solve backtracking problems — you will see through them.*

Here's your complete backtracking mastery guide. Here's what's covered end-to-end:

**Foundations** — the state space tree mental model, the universal CHOOSE → EXPLORE → UNCHOOSE template in Go, Rust, and C, and the three sacred operations that all backtracking reduces to.

**Ten Classic Problems** — each with expert reasoning *before* the code (how a top engineer thinks), then full implementations in all three languages: N-Queens, Subsets/Power Set, Permutations (with and without duplicates), Combination Sum (I and II), Sudoku, Word Search, Palindrome Partitioning, Graph Coloring, Hamiltonian Path/Cycle, and Phone Number Combinations.

**Advanced Techniques** — Forward Checking, AC-3 Arc Consistency, Constraint Propagation, and Bitmask Backtracking (including the bitmask N-Queens which is an order of magnitude faster than the array version, using `available & (-available)` to isolate the lowest set bit in O(1)).

**Expert Mental Models** — the five key mental frameworks, the UNCHOOSE-as-stack-pop model, and the cognitive chunking principle for making the template feel automatic.

One thing to internalize above everything else: the difference between a novice and an expert backtracking solution is almost never the algorithm — it is the *pruning*. The bitmask N-Queens vs the array N-Queens illustrates this perfectly. Same logic, fundamentally different constant factor. Always ask: *can I detect invalidity one level higher?*