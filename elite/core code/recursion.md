# Complete Guide: Recursion, Backtracking & Dynamic Programming

## Table of Contents

1. [Foundation: Understanding Recursion](#foundation-recursion)
2. [Memory Architecture & Call Stack](#memory-architecture)
3. [State Tracking & Variable Lifecycle](#state-tracking)
4. [Backtracking: Exploration with Undo](#backtracking)
5. [Dynamic Programming: Optimization via Memory](#dynamic-programming)
6. [Mental Models & Problem-Solving Strategies](#mental-models)

---

## 1. Foundation: Understanding Recursion {#foundation-recursion}

### What is Recursion?

**Recursion** is when a function calls itself to solve a smaller instance of the same problem. It's a problem-solving paradigm based on **self-similarity** and **reduction**.

**Core Principle:** Break a problem into smaller subproblems of the same type, solve them recursively, and combine their results.

### Anatomy of a Recursive Function

```
┌─────────────────────────────────────┐
│   RECURSIVE FUNCTION STRUCTURE      │
├─────────────────────────────────────┤
│ 1. BASE CASE(S)                     │
│    ├─ Termination condition         │
│    └─ Direct return (no recursion)  │
│                                     │
│ 2. RECURSIVE CASE(S)                │
│    ├─ Problem reduction/division    │
│    ├─ Recursive call(s)             │
│    └─ Combination of results        │
│                                     │
│ 3. PROGRESS TOWARDS BASE            │
│    └─ Each call moves closer        │
└─────────────────────────────────────┘
```

### Simple Example: Factorial

**Mathematical Definition:**

- n! = n × (n-1)!  (recursive case)
- 0! = 1           (base case)

#### Python Implementation

```python
def factorial(n):
    # BASE CASE: Termination condition
    if n == 0:
        return 1
    
    # RECURSIVE CASE: Reduction + combination
    return n * factorial(n - 1)
```

#### Rust Implementation

```rust
fn factorial(n: u64) -> u64 {
    // BASE CASE
    if n == 0 {
        return 1;
    }
    
    // RECURSIVE CASE
    n * factorial(n - 1)
}
```

#### Go Implementation

```go
func factorial(n int) int {
    // BASE CASE
    if n == 0 {
        return 1
    }
    
    // RECURSIVE CASE
    return n * factorial(n-1)
}
```

#### C++ Implementation

```cpp
int factorial(int n) {
    // BASE CASE
    if (n == 0) {
        return 1;
    }
    
    // RECURSIVE CASE
    return n * factorial(n - 1);
}
```

#### C Implementation

```c
int factorial(int n) {
    // BASE CASE
    if (n == 0) {
        return 1;
    }
    
    // RECURSIVE CASE
    return n * factorial(n - 1);
}
```

---

## 2. Memory Architecture & Call Stack {#memory-architecture}

### Understanding the Call Stack

The **call stack** (or execution stack) is a region of memory that stores information about active function calls. It operates on a **LIFO** (Last In, First Out) principle.

**Stack Frame:** Each function call creates a stack frame containing:

- **Return address** (where to continue after function returns)
- **Parameters** (arguments passed to the function)
- **Local variables** (variables declared within the function)
- **Saved registers** (CPU state)

### Memory Layout During Recursion

```
MEMORY LAYOUT (Simplified):
┌────────────────────┐  ← High Address
│   STACK (grows ↓)  │
│  ┌──────────────┐  │
│  │ Frame N      │  │  ← Stack Pointer (SP)
│  ├──────────────┤  │
│  │ Frame N-1    │  │
│  ├──────────────┤  │
│  │ Frame N-2    │  │
│  └──────────────┘  │
│                    │
│   (unused space)   │
│                    │
│  ┌──────────────┐  │
│  │ HEAP (grows↑)│  │
│  └──────────────┘  │
├────────────────────┤
│   DATA SEGMENT     │  ← Global/static variables
├────────────────────┤
│   CODE SEGMENT     │  ← Program instructions
└────────────────────┘  ← Low Address
```

### Detailed Stack Frame Structure

```
STACK FRAME for factorial(3):
┌─────────────────────────────┐
│ Return Address: 0x1234      │ ← Where to jump after return
├─────────────────────────────┤
│ Parameter: n = 3            │ ← Function argument
├─────────────────────────────┤
│ Local Variables: (none)     │ ← Space for local vars
├─────────────────────────────┤
│ Saved Registers: [...]      │ ← Preserved CPU state
└─────────────────────────────┘
```

### Execution Trace: factorial(3)

Let's trace `factorial(3)` step-by-step:

```
STEP-BY-STEP EXECUTION:

Call: factorial(3)
═══════════════════════════════════════════════════════════════
PHASE 1: DESCENDING (Building Stack)
───────────────────────────────────────────────────────────────

1. factorial(3) called
   Stack: [factorial(3)]
   ├─ n = 3, n != 0
   └─ Calls: factorial(2)

2. factorial(2) called
   Stack: [factorial(3), factorial(2)]
   ├─ n = 2, n != 0
   └─ Calls: factorial(1)

3. factorial(1) called
   Stack: [factorial(3), factorial(2), factorial(1)]
   ├─ n = 1, n != 0
   └─ Calls: factorial(0)

4. factorial(0) called
   Stack: [factorial(3), factorial(2), factorial(1), factorial(0)]
   ├─ n = 0, BASE CASE!
   └─ Returns: 1

───────────────────────────────────────────────────────────────
PHASE 2: ASCENDING (Unwinding Stack)
───────────────────────────────────────────────────────────────

5. factorial(0) returns 1
   Stack: [factorial(3), factorial(2), factorial(1)]
   ├─ Computation: 1 * 1 = 1
   └─ factorial(1) returns: 1

6. factorial(1) returns 1
   Stack: [factorial(3), factorial(2)]
   ├─ Computation: 2 * 1 = 2
   └─ factorial(2) returns: 2

7. factorial(2) returns 2
   Stack: [factorial(3)]
   ├─ Computation: 3 * 2 = 6
   └─ factorial(3) returns: 6

8. factorial(3) returns 6
   Stack: []
   Final result: 6
```

### Visual Call Stack Evolution

```
TIME ──────────────────────────────────────────────────>

T0: Initial Call
┌───────────────┐
│ factorial(3)  │ ← Stack grows downward
└───────────────┘

T1: After recursive call
┌───────────────┐
│ factorial(3)  │
├───────────────┤
│ factorial(2)  │
└───────────────┘

T2: Deeper recursion
┌───────────────┐
│ factorial(3)  │
├───────────────┤
│ factorial(2)  │
├───────────────┤
│ factorial(1)  │
└───────────────┘

T3: Maximum depth (base case)
┌───────────────┐
│ factorial(3)  │
├───────────────┤
│ factorial(2)  │
├───────────────┤
│ factorial(1)  │
├───────────────┤
│ factorial(0)  │ ← BASE CASE REACHED
└───────────────┘

T4: Starting to unwind
┌───────────────┐
│ factorial(3)  │
├───────────────┤
│ factorial(2)  │
├───────────────┤
│ factorial(1)  │ ← Receives 1, computes 1*1=1
└───────────────┘

T5: Further unwinding
┌───────────────┐
│ factorial(3)  │
├───────────────┤
│ factorial(2)  │ ← Receives 1, computes 2*1=2
└───────────────┘

T6: Almost complete
┌───────────────┐
│ factorial(3)  │ ← Receives 2, computes 3*2=6
└───────────────┘

T7: Complete
(empty stack)
Result: 6
```

### Memory Usage Analysis

**Space Complexity: O(n)** where n is the recursion depth.

Each recursive call adds a stack frame:

- **Depth:** n (for factorial(n), depth = n)
- **Size per frame:** Typically 16-64 bytes (depends on architecture and parameters)
- **Total memory:** depth × frame_size
- **Example:** factorial(1000) needs ~1000 frames ≈ 16-64 KB

**Stack Overflow:** Occurs when recursion depth exceeds stack size limit (usually 1-8 MB).

---

## 3. State Tracking & Variable Lifecycle {#state-tracking}

### Understanding State in Recursion

**State** = All information needed to solve a subproblem at a given recursion level.

### Types of State:

1. **Explicit Parameters:** Passed through function arguments
2. **Implicit State:** Maintained in the call stack (return addresses, local variables)
3. **Global State:** Shared across all recursive calls (avoid when possible)
4. **Accumulator State:** Built up through recursive calls

### Example: Sum of Array

Let's track state comprehensively:

#### Python with Detailed State Tracking

```python
def array_sum(arr, index=0):
    """
    STATE VARIABLES:
    - arr: The array (shared, read-only)
    - index: Current position (changes with each recursion)
    
    INVARIANT: Returns sum of arr[index:]
    """
    
    # BASE CASE: No more elements
    if index >= len(arr):
        return 0
    
    # RECURSIVE CASE:
    # Current element + sum of rest
    current_value = arr[index]
    rest_sum = array_sum(arr, index + 1)
    
    return current_value + rest_sum

# Execution trace for [1, 2, 3]:
# array_sum([1,2,3], 0) = 1 + array_sum([1,2,3], 1)
#   array_sum([1,2,3], 1) = 2 + array_sum([1,2,3], 2)
#     array_sum([1,2,3], 2) = 3 + array_sum([1,2,3], 3)
#       array_sum([1,2,3], 3) = 0  (base case)
#     returns 3 + 0 = 3
#   returns 2 + 3 = 5
# returns 1 + 5 = 6
```

#### Rust with Ownership Tracking

```rust
fn array_sum(arr: &[i32], index: usize) -> i32 {
    // STATE: arr borrowed (read-only), index owned
    
    // BASE CASE
    if index >= arr.len() {
        return 0;
    }
    
    // RECURSIVE CASE
    let current = arr[index];
    let rest = array_sum(arr, index + 1);
    
    current + rest
}

// Memory note: arr is borrowed, so no copying occurs
// Each frame only stores: index (8 bytes) + locals
```

#### Go with Pointer State

```go
func arraySum(arr []int, index int) int {
    // STATE: arr is slice header (pointer + len + cap)
    //        index is value copy
    
    // BASE CASE
    if index >= len(arr) {
        return 0
    }
    
    // RECURSIVE CASE
    current := arr[index]
    rest := arraySum(arr, index+1)
    
    return current + rest
}
```

### Return Mechanism Deep Dive

**What Happens During Return:**

```
RETURN SEQUENCE:
┌────────────────────────────────────────┐
│ 1. Compute return value                │
│ 2. Store in return register (RAX/R0)   │
│ 3. Pop local variables from stack      │
│ 4. Restore caller's registers          │
│ 5. Jump to return address              │
│ 6. Caller retrieves value from register│
└────────────────────────────────────────┘
```

#### Example with Registers (x86-64 architecture)

```
factorial(3) execution at assembly level:

factorial(3):
    push rbp              ; Save base pointer
    mov rbp, rsp          ; Set new base pointer
    sub rsp, 16           ; Allocate local space
    
    cmp edi, 0            ; Compare n with 0
    je .base_case         ; Jump if equal
    
    ; Recursive case
    sub edi, 1            ; n - 1
    call factorial        ; Recursive call
    imul eax, DWORD PTR [rbp+8]  ; n * result
    jmp .epilogue
    
.base_case:
    mov eax, 1            ; Return 1
    
.epilogue:
    add rsp, 16           ; Deallocate locals
    pop rbp               ; Restore base pointer
    ret                   ; Return to caller
```

### Accumulator Pattern

**Concept:** Build result while descending instead of while returning.

#### Python Accumulator

```python
def factorial_acc(n, accumulator=1):
    """
    STATE:
    - n: remaining multiplications
    - accumulator: result so far
    
    TAIL RECURSIVE: Last operation is the recursive call
    """
    
    # BASE CASE
    if n == 0:
        return accumulator
    
    # RECURSIVE CASE: Update accumulator
    return factorial_acc(n - 1, accumulator * n)

# Trace: factorial_acc(4, 1)
# factorial_acc(4, 1)   → factorial_acc(3, 4)
# factorial_acc(3, 4)   → factorial_acc(2, 12)
# factorial_acc(2, 12)  → factorial_acc(1, 24)
# factorial_acc(1, 24)  → factorial_acc(0, 24)
# factorial_acc(0, 24)  → 24
```

**Tail Call Optimization (TCO):**

- Some compilers can optimize tail recursion to iteration
- Rust and C++ can do this with optimizations enabled
- Python and Go do NOT optimize tail calls

#### Rust Tail Recursive (will be optimized)

```rust
fn factorial_acc(n: u64, acc: u64) -> u64 {
    match n {
        0 => acc,
        _ => factorial_acc(n - 1, acc * n),
    }
}

// With optimizations, this compiles to a loop!
// No stack frames are built up
```

---

## 4. Backtracking: Exploration with Undo {#backtracking}

### What is Backtracking?

**Backtracking** is a systematic way to explore all possible solutions by:

1. Making a choice
2. Exploring consequences
3. Undoing the choice if it doesn't lead to a solution
4. Trying the next choice

**Mental Model:** Think of it as exploring a maze:

- Move forward when path is valid
- Mark dead ends
- Backtrack when stuck
- Try alternate paths

### Backtracking Template

```
BACKTRACKING ALGORITHM STRUCTURE:
┌────────────────────────────────────┐
│ function backtrack(state):         │
│                                    │
│   1. BASE CASE                     │
│      if goal reached:              │
│          save/return solution      │
│                                    │
│   2. PRUNING (optimization)        │
│      if current path invalid:      │
│          return (early exit)       │
│                                    │
│   3. ITERATION over choices        │
│      for each possible choice:     │
│          ├─ MAKE choice            │
│          ├─ RECURSE                │
│          └─ UNDO choice            │
└────────────────────────────────────┘
```

### Classic Problem: N-Queens

**Problem:** Place N queens on an N×N chessboard so no two queens attack each other.

**State Representation:**

- `board`: 2D array
- `row`: current row being processed
- `cols`, `diag1`, `diag2`: sets tracking attacked positions

#### Python N-Queens with Complete State Tracking

```python
def solve_n_queens(n):
    """
    STATE TRACKING:
    - board: current board configuration
    - cols: set of occupied columns
    - diag1: set of occupied \ diagonals (row - col)
    - diag2: set of occupied / diagonals (row + col)
    - solutions: accumulator for valid boards
    """
    
    def backtrack(row, cols, diag1, diag2, board):
        # BASE CASE: All queens placed
        if row == n:
            solutions.append([''.join(row) for row in board])
            return
        
        # TRY each column in current row
        for col in range(n):
            # PRUNING: Check if position is attacked
            if col in cols or (row - col) in diag1 or (row + col) in diag2:
                continue  # Skip invalid position
            
            # MAKE CHOICE: Place queen
            board[row][col] = 'Q'
            cols.add(col)
            diag1.add(row - col)
            diag2.add(row + col)
            
            # RECURSE: Move to next row
            backtrack(row + 1, cols, diag1, diag2, board)
            
            # UNDO CHOICE: Remove queen (backtrack)
            board[row][col] = '.'
            cols.remove(col)
            diag1.remove(row - col)
            diag2.remove(row + col)
    
    solutions = []
    board = [['.' for _ in range(n)] for _ in range(n)]
    backtrack(0, set(), set(), set(), board)
    return solutions

```

#### Rust N-Queens (Idiomatic with Borrowing)

```rust
fn solve_n_queens(n: usize) -> Vec<Vec<String>> {
    fn backtrack(
        row: usize,
        n: usize,
        cols: &mut std::collections::HashSet<usize>,
        diag1: &mut std::collections::HashSet<i32>,
        diag2: &mut std::collections::HashSet<i32>,
        board: &mut Vec<Vec<char>>,
        solutions: &mut Vec<Vec<String>>,
    ) {
        // BASE CASE
        if row == n {
            solutions.push(
                board.iter()
                    .map(|r| r.iter().collect::<String>())
                    .collect()
            );
            return;
        }
        
        // TRY each column
        for col in 0..n {
            let d1 = row as i32 - col as i32;
            let d2 = row as i32 + col as i32;
            
            // PRUNING
            if cols.contains(&col) || diag1.contains(&d1) || diag2.contains(&d2) {
                continue;
            }
            
            // MAKE CHOICE
            board[row][col] = 'Q';
            cols.insert(col);
            diag1.insert(d1);
            diag2.insert(d2);
            
            // RECURSE
            backtrack(row + 1, n, cols, diag1, diag2, board, solutions);
            
            // UNDO CHOICE
            board[row][col] = '.';
            cols.remove(&col);
            diag1.remove(&d1);
            diag2.remove(&d2);
        }
    }
    
    let mut solutions = Vec::new();
    let mut board = vec![vec!['.'; n]; n];
    let mut cols = std::collections::HashSet::new();
    let mut diag1 = std::collections::HashSet::new();
    let mut diag2 = std::collections::HashSet::new();
    
    backtrack(0, n, &mut cols, &mut diag1, &mut diag2, &mut board, &mut solutions);
    solutions
}
```

#### Go N-Queens

```go
func solveNQueens(n int) [][]string {
    solutions := [][]string{}
    board := make([][]byte, n)
    for i := range board {
        board[i] = make([]byte, n)
        for j := range board[i] {
            board[i][j] = '.'
        }
    }
    
    cols := make(map[int]bool)
    diag1 := make(map[int]bool)
    diag2 := make(map[int]bool)
    
    var backtrack func(int)
    backtrack = func(row int) {
        // BASE CASE
        if row == n {
            solution := make([]string, n)
            for i := range board {
                solution[i] = string(board[i])
            }
            solutions = append(solutions, solution)
            return
        }
        
        // TRY each column
        for col := 0; col < n; col++ {
            d1, d2 := row - col, row + col
            
            // PRUNING
            if cols[col] || diag1[d1] || diag2[d2] {
                continue
            }
            
            // MAKE CHOICE
            board[row][col] = 'Q'
            cols[col] = true
            diag1[d1] = true
            diag2[d2] = true
            
            // RECURSE
            backtrack(row + 1)
            
            // UNDO CHOICE
            board[row][col] = '.'
            delete(cols, col)
            delete(diag1, d1)
            delete(diag2, d2)
        }
    }
    
    backtrack(0)
    return solutions
}
```

### Backtracking Execution Tree

```
N-Queens (n=4) Decision Tree:

Level 0 (row 0):
    Try col 0, 1, 2, 3
        │
        ├─ Q at (0,0) ───┐
        ├─ Q at (0,1) ───┼──> (continues)
        ├─ Q at (0,2) ───┤
        └─ Q at (0,3) ───┘

Level 1 (row 1, assuming Q at (0,0)):
    Can't place at col 0 (same column)
    Can't place at col 1 (diagonal)
    Try col 2 ───┐
    Try col 3 ───┼──> (continues)
                 │
Level 2 (row 2, Q at (0,0), (1,2)):
    Can't place at col 0 (diagonal)
    Try col 1 ───> Eventually finds solution
    ...

PRUNING eliminates invalid branches early!

Complete tree for n=4:
     [ROOT]
       / | \ \
      /  |  \ \
   (0,0)(0,1)(0,2)(0,3)
    /|\   /|\   /|\   /|\
  ... ... ... ... ... ...
  
Total nodes: O(N^N) without pruning
With pruning: Much fewer nodes explored
```

---

## 5. Dynamic Programming: Optimization via Memory {#dynamic-programming}

### What is Dynamic Programming?

**Dynamic Programming (DP)** optimizes recursive solutions by storing and reusing results of subproblems.

**Key Insight:** Many recursive problems recompute the same subproblems multiple times. DP trades space for time.

### When to Use DP?

DP applies when problems have:

1. **Optimal Substructure:** Optimal solution contains optimal solutions to subproblems
2. **Overlapping Subproblems:** Same subproblems are solved multiple times

### Two Approaches:

```
┌──────────────────────────────────────┐
│ MEMOIZATION (Top-Down)               │
├──────────────────────────────────────┤
│ • Recursive approach                 │
│ • Cache results in dictionary/map    │
│ • Compute on demand                  │
│ • Easier to write from recursion     │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ TABULATION (Bottom-Up)               │
├──────────────────────────────────────┤
│ • Iterative approach                 │
│ • Fill table in order                │
│ • No recursion overhead              │
│ • Usually faster, more space-efficient│
└──────────────────────────────────────┘
```

### Classic Example: Fibonacci

**Naive Recursion:** Exponential time O(2^n)

```
fib(5) call tree:
                fib(5)
               /      \
          fib(4)      fib(3)
          /    \       /    \
     fib(3)  fib(2) fib(2) fib(1)
     /   \    /  \   /  \
fib(2) fib(1) ...  ... ...

Many repeated computations! fib(2) calculated 3 times, fib(3) twice
```

#### Memoization (Top-Down DP)

**Python Memoization**

```python
def fib_memo(n, memo=None):
    """
    STATE: memo dictionary stores computed results
    TIME: O(n) - each subproblem solved once
    SPACE: O(n) - recursion stack + memo dictionary
    """
    
    if memo is None:
        memo = {}
    
    # BASE CASES
    if n <= 1:
        return n
    
    # CHECK CACHE
    if n in memo:
        return memo[n]  # Already computed!
    
    # COMPUTE and STORE
    memo[n] = fib_memo(n - 1, memo) + fib_memo(n - 2, memo)
    return memo[n]

# Using Python's built-in decorator
from functools import lru_cache

@lru_cache(maxsize=None)
def fib_cached(n):
    if n <= 1:
        return n
    return fib_cached(n - 1) + fib_cached(n - 2)
```

**Rust Memoization**

```rust
use std::collections::HashMap;

fn fib_memo(n: u64, memo: &mut HashMap<u64, u64>) -> u64 {
    // BASE CASES
    if n <= 1 {
        return n;
    }
    
    // CHECK CACHE
    if let Some(&result) = memo.get(&n) {
        return result;
    }
    
    // COMPUTE
    let result = fib_memo(n - 1, memo) + fib_memo(n - 2, memo);
    
    // STORE
    memo.insert(n, result);
    result
}

// Usage:
// let mut memo = HashMap::new();
// let result = fib_memo(50, &mut memo);
```

**Go Memoization**

```go
func fibMemo(n int, memo map[int]int) int {
    // BASE CASES
    if n <= 1 {
        return n
    }
    
    // CHECK CACHE
    if val, exists := memo[n]; exists {
        return val
    }
    
    // COMPUTE and STORE
    memo[n] = fibMemo(n-1, memo) + fibMemo(n-2, memo)
    return memo[n]
}

// Usage:
// memo := make(map[int]int)
// result := fibMemo(50, memo)
```

#### Tabulation (Bottom-Up DP)

**Python Tabulation**

```python
def fib_tab(n):
    """
    TIME: O(n)
    SPACE: O(n) - can be optimized to O(1)
    
    APPROACH: Build table from smallest to largest
    """
    
    if n <= 1:
        return n
    
    # CREATE TABLE
    dp = [0] * (n + 1)
    
    # BASE CASES
    dp[0] = 0
    dp[1] = 1
    
    # FILL TABLE: Each entry depends on previous two
    for i in range(2, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]
    
    return dp[n]

# Space-optimized version
def fib_optimized(n):
    """
    SPACE: O(1) - only track last two values
    """
    if n <= 1:
        return n
    
    prev2, prev1 = 0, 1
    
    for _ in range(2, n + 1):
        current = prev1 + prev2
        prev2 = prev1
        prev1 = current
    
    return prev1
```

**Rust Tabulation**

```rust
fn fib_tab(n: usize) -> u64 {
    if n <= 1 {
        return n as u64;
    }
    
    let mut dp = vec![0u64; n + 1];
    dp[0] = 0;
    dp[1] = 1;
    
    for i in 2..=n {
        dp[i] = dp[i - 1] + dp[i - 2];
    }
    
    dp[n]
}

// Space-optimized
fn fib_optimized(n: usize) -> u64 {
    if n <= 1 {
        return n as u64;
    }
    
    let (mut prev2, mut prev1) = (0, 1);
    
    for _ in 2..=n {
        let current = prev1 + prev2;
        prev2 = prev1;
        prev1 = current;
    }
    
    prev1
}
```

### Complex DP: Longest Common Subsequence (LCS)

**Problem:** Find length of longest subsequence common to two strings.

**Example:**

- s1 = "ABCDGH"
- s2 = "AEDFHR"
- LCS = "ADH" (length 3)

#### State Definition

```
STATE: dp[i][j] = LCS length for s1[0..i] and s2[0..j]

RECURRENCE:
┌─────────────────────────────────────────────┐
│ if s1[i] == s2[j]:                          │
│     dp[i][j] = dp[i-1][j-1] + 1             │
│ else:                                       │
│     dp[i][j] = max(dp[i-1][j], dp[i][j-1])  │
└─────────────────────────────────────────────┘

BASE CASES:
dp[0][j] = 0 (empty s1)
dp[i][0] = 0 (empty s2)
```

**Python LCS Implementation**

```python
def lcs(s1, s2):
    """
    TIME: O(m * n) where m, n are string lengths
    SPACE: O(m * n) for dp table
    """
    m, n = len(s1), len(s2)
    
    # CREATE TABLE with extra row/col for base cases
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # FILL TABLE
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                # Characters match: extend previous LCS
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                # Characters differ: take max of excluding either
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    
    return dp[m][n]

# With path reconstruction
def lcs_with_string(s1, s2):
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    
    # BACKTRACK to reconstruct LCS
    lcs_str = []
    i, j = m, n
    while i > 0 and j > 0:
        if s1[i - 1] == s2[j - 1]:
            lcs_str.append(s1[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] > dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    
    return ''.join(reversed(lcs_str))
```

**Rust LCS**

```rust
fn lcs(s1: &str, s2: &str) -> usize {
    let s1_chars: Vec<char> = s1.chars().collect();
    let s2_chars: Vec<char> = s2.chars().collect();
    let m = s1_chars.len();
    let n = s2_chars.len();
    
    let mut dp = vec![vec![0; n + 1]; m + 1];
    
    for i in 1..=m {
        for j in 1..=n {
            if s1_chars[i - 1] == s2_chars[j - 1] {
                dp[i][j] = dp[i - 1][j - 1] + 1;
            } else {
                dp[i][j] = dp[i - 1][j].max(dp[i][j - 1]);
            }
        }
    }
    
    dp[m][n]
}
```

### DP Table Visualization

```
LCS("ABCDGH", "AEDFHR"):

    ""  A  E  D  F  H  R
""   0  0  0  0  0  0  0
A    0  1  1  1  1  1  1
B    0  1  1  1  1  1  1
C    0  1  1  1  1  1  1
D    0  1  1  2  2  2  2
G    0  1  1  2  2  2  2
H    0  1  1  2  2  3  3

How to read:
- dp[4][3] = 2 means LCS("ABCD", "AED") has length 2
- Bottom-right: dp[6][6] = 3 is final answer
- Diagonal moves: characters match
- Horizontal/Vertical moves: characters don't match
```

---

## 6. Mental Models & Problem-Solving Strategies {#mental-models}

### The Recursion Mindset

**"Think Smaller, Not Bigger"**

- Break problem into smaller subproblems
- Solve each subproblem recursively
- Combine subproblem solutions for final answer

1. **Trust the recursion:** Assume smaller problems are solved correctly
2. **Focus on current level:** What do I do at THIS step?
3. **Combine results:** How do I use subproblem solutions?

### Decision Tree for Choosing Approach

```
┌─────────────────────────────────────┐
│ Does problem have optimal           │
│ substructure?                       │
└────────┬──────────────────────┬─────┘
         │ YES                  │ NO
         ▼                      ▼
    ┌─────────┐          Use different
    │ Are     │          approach
    │ subpro- │          (greedy,
    │ blems   │          divide &
    │ overlap?│          conquer)
    └────┬────┘
         │
    ┌────┴────┐
    │ YES     │ NO
    ▼         ▼
   DP      Simple
           Recursion
    │
    ├──> Need all solutions? → Backtracking
    │
    └──> Just optimal? → DP
         │
         ├─> Easy to memoize? → Top-down DP
         └─> Clear iteration order? → Bottom-up DP
```

### Complexity Analysis Framework

**Time Complexity of Recursion:**

```
T(n) = (# of recursive calls) × (work per call) + (combining work)

Examples:
- Factorial: T(n) = T(n-1) + O(1) = O(n)
- Fibonacci: T(n) = T(n-1) + T(n-2) + O(1) = O(2^n)
- Binary Search: T(n) = T(n/2) + O(1) = O(log n)
- Merge Sort: T(n) = 2T(n/2) + O(n) = O(n log n)
```

**Space Complexity:**

```
Space = (Recursion depth) × (Space per frame) + (Auxiliary space)

Examples:
- Factorial: O(n) stack + O(1) = O(n)
- Memoized Fib: O(n) stack + O(n) memo = O(n)
- Tabulated Fib: O(1) stack + O(n) table = O(n)
- Space-optimized Fib: O(1) stack + O(1) = O(1)
```

### Master Theorem (for Divide & Conquer)

```
T(n) = aT(n/b) + f(n)

Where:
- a = # of subproblems
- b = size reduction factor
- f(n) = work outside recursion

CASES:
1. f(n) = O(n^c) where c < log_b(a)
   → T(n) = Θ(n^log_b(a))

2. f(n) = Θ(n^c) where c = log_b(a)
   → T(n) = Θ(n^c log n)

3. f(n) = Ω(n^c) where c > log_b(a)
   → T(n) = Θ(f(n))
```

### Problem-Solving Workflow

```
STEP 1: UNDERSTAND
┌──────────────────────────────────┐
│ • What is the input/output?      │
│ • What are the constraints?      │
│ • Can I solve a smaller version? │
│ • What's the base case?          │
└──────────────────────────────────┘
         │
         ▼
STEP 2: BRUTE FORCE
┌──────────────────────────────────┐
│ • Write naive recursive solution │
│ • Verify correctness on examples│
│ • Analyze time/space complexity  │
└──────────────────────────────────┘
         │
         ▼
STEP 3: OPTIMIZE
┌──────────────────────────────────┐
│ • Overlapping subproblems? → DP  │
│ • Multiple choices? → Backtrack  │
│ • Tail recursive? → Iteration    │
└──────────────────────────────────┘
         │
         ▼
STEP 4: IMPLEMENT
┌──────────────────────────────────┐
│ • Choose language idioms         │
│ • Handle edge cases              │
│ • Add state tracking if needed   │
└──────────────────────────────────┘
         │
         ▼
STEP 5: VALIDATE
┌──────────────────────────────────┐
│ • Test on small inputs           │
│ • Test edge cases                │
│ • Verify complexity              │
└──────────────────────────────────┘
```

### Cognitive Principles for Mastery

**1. Chunking**

- Group related concepts (base case, recursive case, combination)
- Practice recognizing patterns (subset sum, path finding, optimization)

**2. Deliberate Practice**

- Focus on weak areas (backtracking state management, DP transitions)
- Implement same problem in multiple languages
- Optimize after getting correct solution

**3. Spaced Repetition**

- Revisit problems after 1 day, 1 week, 1 month
- Each iteration should be faster and more elegant

**4. Meta-Learning**

- After solving, ask: "What pattern did I use?"
- Document your mistakes and insights
- Build a personal problem taxonomy

**5. Flow State Prerequisites**

- Clear goals (solve specific problem)
- Immediate feedback (test cases)
- Challenge matched to skill (not too easy/hard)

### Advanced Patterns

#### Pattern 1: Multiple Recursion Branches

```python
def count_paths(grid, r, c):
    """Count paths from top-left to (r, c)"""
    # BASE CASES
    if r == 0 and c == 0:
        return 1
    if r < 0 or c < 0:
        return 0
    if grid[r][c] == 1:  # Blocked
        return 0
    
    # RECURSIVE CASE: Sum paths from top and left
    return count_paths(grid, r-1, c) + count_paths(grid, r, c-1)
```

#### Pattern 2: State Restoration (Backtracking)

```python
def permutations(nums):
    result = []
    
    def backtrack(current, remaining):
        if not remaining:
            result.append(current[:])  # Copy!
            return
        
        for i in range(len(remaining)):
            # MAKE CHOICE
            current.append(remaining[i])
            new_remaining = remaining[:i] + remaining[i+1:]
            
            # RECURSE
            backtrack(current, new_remaining)
            
            # UNDO
            current.pop()
    
    backtrack([], nums)
    return result
```

#### Pattern 3: DP with Path Reconstruction

```python
def min_cost_path(grid):
    """Find minimum cost path with the path itself"""
    m, n = len(grid), len(grid[0])
    dp = [[float('inf')] * n for _ in range(m)]
    parent = [[None] * n for _ in range(m)]
    
    dp[0][0] = grid[0][0]
    
    for i in range(m):
        for j in range(n):
            if i > 0 and dp[i-1][j] + grid[i][j] < dp[i][j]:
                dp[i][j] = dp[i-1][j] + grid[i][j]
                parent[i][j] = (i-1, j)
            if j > 0 and dp[i][j-1] + grid[i][j] < dp[i][j]:
                dp[i][j] = dp[i][j-1] + grid[i][j]
                parent[i][j] = (i, j-1)
    
    # RECONSTRUCT PATH
    path = []
    i, j = m-1, n-1
    while i >= 0 and j >= 0:
        path.append((i, j))
        if parent[i][j] is None:
            break
        i, j = parent[i][j]
    
    return dp[m-1][n-1], path[::-1]
```

---

## Summary: Your Learning Path

### Phase 1: Foundation (Weeks 1-2)

- Master basic recursion (factorial, fibonacci, sum)
- Understand call stack deeply
- Implement in all 5 languages

### Phase 2: Patterns (Weeks 3-4)

- Multiple branches (tree traversal)
- Accumulator pattern
- Tail recursion

### Phase 3: Backtracking (Weeks 5-6)

- N-Queens, Sudoku
- Subset sum, permutations
- State management mastery

### Phase 4: Dynamic Programming (Weeks 7-10)

- 1D DP (fibonacci, climbing stairs)
- 2D DP (LCS, edit distance, knapsack)
- Path reconstruction
- Space optimization

### Phase 5: Advanced (Weeks 11-12)

- Tree DP
- Digit DP
- State compression
- Optimization techniques

### Daily Practice Structure

```
15 min: Review previous problem
45 min: New problem (multiple approaches)
30 min: Implement in different language
15 min: Optimize and document patterns
15 min: Reflect on what you learned
```

Remember: **Understanding > Speed > Optimization**

First solve it, then solve it correctly, then solve it elegantly.

---

*"In recursion, as in life, trust that each step brings you closer to the solution, even when you can't see the entire path."*

I'll create a comprehensive guide to recursion, backtracking, and dynamic programming that covers memory-level details, state tracking, and implementations across all your languages. This will be your training manual for mastering these fundamental concepts.I've created a comprehensive guide that takes you from the fundamental concepts of recursion all the way through to advanced dynamic programming. Let me highlight some key insights:

## Critical Concepts Covered:

**Memory-Level Understanding:**

- The call stack grows downward with each recursive call
- Each frame holds parameters, local variables, return addresses, and saved registers
- Stack overflow happens when depth × frame_size exceeds stack limit (typically 1-8MB)
- Return values flow through CPU registers (RAX on x86-64)

**The Three Pillars:**

1. **Recursion** = Self-referential problem reduction
2. **Backtracking** = Recursive exploration with choice undo
3. **Dynamic Programming** = Recursion + memoization to eliminate redundant computation

## Mental Models for Mastery:

**The "Trust Principle":** When writing recursive code, assume smaller subproblems are solved correctly. Focus only on:

- What happens at THIS level?
- How do I combine results?
- When do I stop (base case)?

**The "Phases of Recursion":**

- **Descending Phase:** Building up the call stack, making the problem smaller
- **Base Case:** The turning point where recursion stops
- **Ascending Phase:** Unwinding the stack, combining results

**DP Decision Framework:**

```
Overlapping subproblems? 
  ↓ YES
Need optimal solution?
  ↓ YES
Can you define state clearly?
  ↓ YES
→ Use Dynamic Programming
```

## Cognitive Strategies:

1. **Visualization Practice:** Draw the recursion tree for every problem. This builds intuition about time complexity and overlapping subproblems.

2. **State Invariant Discipline:** Before writing code, write down: "At this recursion level, state X represents Y, and the function returns Z." This clarity prevents bugs.

3. **The 4-Implementation Rule:** Solve each problem in at least 4 ways:
   - Naive recursion (understand structure)
   - Memoization (recognize overlaps)
   - Tabulation (remove recursion overhead)
   - Space-optimized (understand dependencies)

4. **Error Pattern Recognition:** Track your mistakes. Most recursion bugs fall into 5 categories:
   - Missing/wrong base case
   - Wrong state progression (not moving toward base case)
   - Forgetting to restore state (backtracking)
   - Off-by-one in DP indices
   - Incorrect subproblem combination

## Language-Specific Insights:

- **Python:** Recursion limit is 1000 by default (changeable with `sys.setrecursionlimit`). Best for rapid prototyping.
- **Rust:** Ownership forces explicit state management, which actually helps avoid bugs. Compiler may optimize tail recursion.
- **Go:** No tail call optimization. Goroutines have separate stacks, but still limited.
- **C/C++:** Full control but easy to overflow. Use `-O2` or `-O3` for tail call optimization.

## Next Steps:

Start with the **Phase 1 problems** in the guide. Implement factorial and fibonacci in all 5 languages. Focus on understanding the call stack visualization. Then gradually progress through the phases.

**Key question to ask yourself after each problem:** "If I had to solve a similar but slightly different version of this problem, what would change and what would stay the same?" This builds pattern recognition.

Would you like me to:

1. Create practice problems with solutions for each phase?
2. Dive deeper into any specific topic (like DP state transitions or backtracking pruning)?
3. Provide a visual debugger/tracer for watching recursion in action?