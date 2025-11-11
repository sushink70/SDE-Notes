# The Complete Map of Recursion: From Foundations to Mastery

```python
"""
═══════════════════════════════════════════════════════════════════════════════
                    THE ANATOMY OF RECURSION: CORE MECHANICS
═══════════════════════════════════════════════════════════════════════════════

FUNDAMENTAL CONCEPT: A function calling itself with a modified state until 
reaching a base condition. The call stack is your working memory.

Call Stack Visualization for: factorial(4)
───────────────────────────────────────────────────────────────────────────────

Step 1: Initial Call          Step 2: Recursive Descent       Step 3: Base Case
                              
factorial(4) ──────►          factorial(4)                    factorial(4)
                              │                                │
                              └──► factorial(3)                └──► factorial(3)
                                   │                                 │
                                   └──► factorial(2)                 └──► factorial(2)
                                        │                                 │
                                        └──► factorial(1)                 └──► factorial(1)
                                                                               │
                                                                               └──► factorial(0) ──► return 1 ✓


Step 4: Unwinding (The Critical Phase - Where Work Actually Happens)
───────────────────────────────────────────────────────────────────────────────

                              RETURN VALUES ↓
                              
factorial(0) ──────────────► return 1
        ↑
factorial(1) ──────────────► return 1 * 1 = 1
        ↑
factorial(2) ──────────────► return 2 * 1 = 2
        ↑
factorial(3) ──────────────► return 3 * 2 = 6
        ↑
factorial(4) ──────────────► return 4 * 6 = 24 ◄── FINAL RESULT


MEMORY VISUALIZATION: Each frame holds its own context
───────────────────────────────────────────────────────────────────────────────

STACK (grows downward)          HEAP (if needed)
┌─────────────────────┐
│ factorial(4)        │◄── Most recent call (top of stack)
│ n=4, return addr    │
├─────────────────────┤
│ factorial(3)        │
│ n=3, return addr    │
├─────────────────────┤
│ factorial(2)        │
│ n=2, return addr    │
├─────────────────────┤
│ factorial(1)        │
│ n=1, return addr    │
├─────────────────────┤
│ factorial(0)        │◄── Deepest call (about to return)
│ n=0, return addr    │
└─────────────────────┘

Space Complexity: O(n) stack frames
Time Complexity: O(n) operations
"""


def factorial(n):
    """Linear recursion: Single recursive call per invocation"""
    if n <= 1:  # BASE CASE: Termination condition
        return 1
    return n * factorial(n - 1)  # RECURSIVE CASE: Self-invocation with reduction


"""
═══════════════════════════════════════════════════════════════════════════════
                    TYPE 1: LINEAR RECURSION (Single Branch)
═══════════════════════════════════════════════════════════════════════════════

Characteristics:
• One recursive call per function invocation
• Forms a straight line in the call tree
• Stack depth = input size
• Common in: sequential processing, accumulation, traversal

Example: Sum of list elements
───────────────────────────────────────────────────────────────────────────────

sum_list([1, 2, 3, 4])
│
├──► 1 + sum_list([2, 3, 4])
│            │
│            ├──► 2 + sum_list([3, 4])
│            │            │
│            │            ├──► 3 + sum_list([4])
│            │            │            │
│            │            │            ├──► 4 + sum_list([])
│            │            │            │            │
│            │            │            │            └──► 0 (base)
│            │            │            └──► returns 4
│            │            └──► returns 7
│            └──► returns 9
└──► returns 10
"""


def sum_list(arr):
    if not arr:
        return 0
    return arr[0] + sum_list(arr[1:])


"""
═══════════════════════════════════════════════════════════════════════════════
                TYPE 2: BINARY/TREE RECURSION (Multiple Branches)
═══════════════════════════════════════════════════════════════════════════════

Characteristics:
• Multiple recursive calls per invocation (typically 2+)
• Forms a tree structure
• Exponential time without memoization
• Common in: divide-and-conquer, tree traversal, combinatorial problems

Fibonacci Tree: fib(5) - Classic example of explosive branching
───────────────────────────────────────────────────────────────────────────────

                                    fib(5)
                          ┌──────────┴──────────┐
                        fib(4)                 fib(3)
                    ┌─────┴─────┐          ┌─────┴─────┐
                  fib(3)       fib(2)    fib(2)       fib(1)
                ┌───┴───┐    ┌───┴───┐ ┌───┴───┐       │
              fib(2) fib(1) fib(1) fib(0) fib(1) fib(0) │
             ┌───┴───┐  │     │      │     │      │     │
           fib(1) fib(0)│     │      │     │      │     │
             │      │   │     │      │     │      │     │
             1      0   1     1      0     1      0     1

Notice: fib(3) computed 2 times, fib(2) computed 3 times!
Time Complexity: O(2^n) - exponential explosion
Space Complexity: O(n) - maximum depth of recursion tree

REDUNDANT WORK VISUALIZATION:
───────────────────────────────────────────────────────────────────────────────
fib(2): ████████████ (computed 3 times)
fib(3): ████████     (computed 2 times)
fib(4): ████         (computed 1 time)
fib(5): ██           (computed 1 time)

This inefficiency is WHY we need Dynamic Programming!
"""


def fibonacci_naive(n):
    """Binary recursion: Two recursive calls - EXPONENTIAL time!"""
    if n <= 1:
        return n
    return fibonacci_naive(n - 1) + fibonacci_naive(n - 2)


"""
═══════════════════════════════════════════════════════════════════════════════
        TYPE 3: TAIL RECURSION (Last Operation is Recursive Call)
═══════════════════════════════════════════════════════════════════════════════

Characteristics:
• Recursive call is the LAST operation (nothing happens after it returns)
• Can be optimized to iteration by compiler (TCO - Tail Call Optimization)
• Accumulator pattern: carry result forward instead of building it on return
• Python doesn't do TCO, but the pattern is still valuable for understanding

CRITICAL DISTINCTION: Tail vs Non-Tail
───────────────────────────────────────────────────────────────────────────────

NON-TAIL (must remember n):          TAIL (result accumulated in acc):

factorial(3)                         factorial_tail(3, acc=1)
│                                    │
└─► return 3 * factorial(2)         └─► factorial_tail(2, acc=3)
              │                                  │
              └─► return 2 * factorial(1)       └─► factorial_tail(1, acc=6)
                           │                                    │
                           └─► return 1                         └─► factorial_tail(0, acc=6)
                                                                            │
Stack must keep: [3, 2, 1]          Stack can forget previous:             └─► return 6
Each frame waits for result below   Each frame is independent!

VISUALIZATION OF ACCUMULATOR PATTERN:
───────────────────────────────────────────────────────────────────────────────

Call                    Accumulator         Why This Works
─────────────────────────────────────────────────────────────────────────────
factorial_tail(4, 1) ─► acc = 1          │ Start with identity
factorial_tail(3, 4) ─► acc = 4 * 1 = 4  │ Incorporate current n
factorial_tail(2, 12)─► acc = 3 * 4 = 12 │ Result builds forward
factorial_tail(1, 24)─► acc = 2 * 12= 24 │ Not backward on unwind
factorial_tail(0, 24)─► return 24        │ Base case returns accumulated result
"""


def factorial_tail(n, acc=1):
    """Tail recursive: Result accumulated in parameter, not on stack unwind"""
    if n <= 1:
        return acc
    return factorial_tail(n - 1, n * acc)  # acc carries the partial result


"""
═══════════════════════════════════════════════════════════════════════════════
    TYPE 4: DYNAMIC PROGRAMMING with MEMOIZATION (Top-Down Recursion)
═══════════════════════════════════════════════════════════════════════════════

Concept: Cache results to avoid redundant computation. Transform O(2^n) to O(n).

MEMOIZATION VISUALIZATION: fib(6) with cache
───────────────────────────────────────────────────────────────────────────────

                                    fib(6) ◄── NEW COMPUTATION
                          ┌──────────┴──────────┐
                        fib(5) ◄── NEW         fib(4) ◄── HIT CACHE ✓
                    ┌─────┴─────┐                       (return 3 instantly)
                  fib(4) ◄── NEW  fib(3) ◄── HIT ✓
                ┌───┴───┐                   
              fib(3) ◄── NEW  fib(2) ◄── HIT ✓
             ┌───┴───┐  
           fib(2) ◄── NEW  fib(1) ◄── BASE
          ┌───┴───┐  
        fib(1) fib(0)
        BASE   BASE

CACHE STATE EVOLUTION:
───────────────────────────────────────────────────────────────────────────────
After base cases:  cache = {0: 0, 1: 1}
After fib(2):      cache = {0: 0, 1: 1, 2: 1}
After fib(3):      cache = {0: 0, 1: 1, 2: 1, 3: 2}
After fib(4):      cache = {0: 0, 1: 1, 2: 1, 3: 2, 4: 3}
After fib(5):      cache = {0: 0, 1: 1, 2: 1, 3: 2, 4: 3, 5: 5}
After fib(6):      cache = {0: 0, 1: 1, 2: 1, 3: 2, 4: 3, 5: 5, 6: 8}

COMPLEXITY TRANSFORMATION:
───────────────────────────────────────────────────────────────────────────────
                    Without Memo        With Memo
Time Complexity:    O(2^n)             O(n)
Space Complexity:   O(n) stack         O(n) cache + O(n) stack
Calls to fib(3):    2^(n-3)            1 (cached after first)

The magic: Each subproblem solved EXACTLY ONCE, then reused ∞ times.
"""


def fibonacci_memo(n, memo=None):
    """Top-down DP: Recursion + caching"""
    if memo is None:
        memo = {}
    
    if n in memo:  # CHECK CACHE FIRST
        return memo[n]
    
    if n <= 1:  # BASE CASE
        return n
    
    # COMPUTE AND STORE
    memo[n] = fibonacci_memo(n - 1, memo) + fibonacci_memo(n - 2, memo)
    return memo[n]


"""
═══════════════════════════════════════════════════════════════════════════════
        TYPE 5: BACKTRACKING (Recursive Exploration with Abandonment)
═══════════════════════════════════════════════════════════════════════════════

Concept: Systematically explore all possibilities, abandoning paths that 
violate constraints. Build solutions incrementally, undo when stuck.

THE BACKTRACKING TEMPLATE:
───────────────────────────────────────────────────────────────────────────────
1. CHOOSE: Make a decision (add element to current solution)
2. EXPLORE: Recurse to next decision point
3. UNCHOOSE: Undo the decision (backtrack) to try other options

N-Queens Problem: Place N queens on N×N board (no two attack each other)
───────────────────────────────────────────────────────────────────────────────

Board: 4×4, trying to place 4 queens

Initial:        Try Q at (0,0)      Try Q at (0,1)      Try Q at (0,2) ...
┌─┬─┬─┬─┐      ┌─┬─┬─┬─┐          ┌─┬─┬─┬─┐          ┌─┬─┬─┬─┐
│ │ │ │ │      │Q│X│X│X│          │X│Q│X│X│          │X│X│Q│X│
├─┼─┼─┼─┤      ├─┼─┼─┼─┤          ├─┼─┼─┼─┤          ├─┼─┼─┼─┤
│ │ │ │ │      │X│ │ │ │          │X│X│ │ │          │X│X│X│ │
├─┼─┼─┼─┤  ──► ├─┼─┼─┼─┤  ──►    ├─┼─┼─┼─┤  ──►    ├─┼─┼─┼─┤
│ │ │ │ │      │X│ │ │ │          │ │X│ │ │          │ │X│X│ │
├─┼─┼─┼─┤      ├─┼─┼─┼─┤          ├─┼─┼─┼─┤          ├─┼─┼─┼─┤
│ │ │ │ │      │X│ │ │ │          │ │X│ │ │          │ │ │X│ │
└─┴─┴─┴─┘      └─┴─┴─┴─┘          └─┴─┴─┴─┘          └─┴─┴─┴─┘
                    ↓                   ↓                   ↓
              Try row 1...        Try row 1...         Try row 1...
                  ↓                   ↓                   ↓
            CONFLICT! ✗          CONFLICT! ✗         Can continue...
                  ↓                   ↓                   ↓
            BACKTRACK!            BACKTRACK!          (deeper recursion)
            Remove Q              Remove Q
            Try next col          Try next col


RECURSION TREE: N=4, showing pruning
───────────────────────────────────────────────────────────────────────────────

                                place_queens(row=0)
                    ┌──────────┬────────┬────────┬──────────┐
                   col=0      col=1    col=2    col=3
                    │          │        │         │
              place_queens  place_queens place_queens place_queens
                (row=1)      (row=1)    (row=1)    (row=1)
                    │          │          │         │
                  Try all    Try all    Try all   Try all
                   cols       cols       cols      cols
                    │          │          │         │
                    ✗          ✗       SUCCESS!     ✗
                 (dead)     (dead)   (found solution)
                 
The ✗ branches are PRUNED - we don't explore them further!

STATE SPACE TREE PRUNING:
───────────────────────────────────────────────────────────────────────────────
Without pruning: 4^4 = 256 nodes to explore
With pruning:     ~20 nodes explored (early termination on conflicts)

This is the POWER of backtracking: intelligent abandonment of futile paths.
"""


def solve_n_queens(n):
    """Backtracking: systematic exploration with constraint checking"""
    def is_safe(board, row, col):
        # Check column
        for i in range(row):
            if board[i] == col:
                return False
        # Check diagonals
        for i in range(row):
            if abs(board[i] - col) == abs(i - row):
                return False
        return True
    
    def backtrack(row, board):
        if row == n:  # BASE: all queens placed
            solutions.append(board[:])
            return
        
        for col in range(n):
            if is_safe(board, row, col):
                board[row] = col          # CHOOSE
                backtrack(row + 1, board) # EXPLORE
                board[row] = -1           # UNCHOOSE (backtrack)
    
    solutions = []
    backtrack(0, [-1] * n)
    return solutions


"""
═══════════════════════════════════════════════════════════════════════════════
            TYPE 6: DIVIDE AND CONQUER (Split, Solve, Combine)
═══════════════════════════════════════════════════════════════════════════════

Concept: Break problem into independent subproblems, solve recursively, merge.

MERGE SORT VISUALIZATION: arr = [38, 27, 43, 3, 9, 82, 10]
───────────────────────────────────────────────────────────────────────────────

DIVIDE PHASE (Top-down):
────────────────────────

Level 0:                    [38, 27, 43, 3, 9, 82, 10]
                          ┌──────────────┴──────────────┐
Level 1:          [38, 27, 43, 3]                 [9, 82, 10]
                  ┌───────┴───────┐               ┌─────┴─────┐
Level 2:      [38, 27]        [43, 3]         [9, 82]       [10]
              ┌───┴───┐       ┌───┴───┐       ┌───┴───┐       │
Level 3:    [38]    [27]    [43]    [3]     [9]    [82]     [10]
             ↑       ↑       ↑       ↑       ↑       ↑        ↑
          BASE    BASE    BASE    BASE    BASE    BASE     BASE


CONQUER PHASE (Bottom-up - where sorting happens):
──────────────────────────────────────────────────

Level 3:    [38]    [27]    [43]    [3]     [9]    [82]     [10]
              └───┬───┘       └───┬───┘       └───┬───┘       │
Level 2:      [27, 38]        [3, 43]         [9, 82]       [10]
                  └───────┬───────┘               └─────┬─────┘
Level 1:          [3, 27, 38, 43]                 [9, 10, 82]
                          └──────────────┬──────────────┘
Level 0:                    [3, 9, 10, 27, 38, 43, 82]  ← SORTED!


MERGE OPERATION DETAIL: Merging [27, 38] and [3, 43]
───────────────────────────────────────────────────────────────────────────────

Left:  [27, 38]     Right: [3, 43]      Result: []
        ↑                   ↑
        
Step 1: Compare 27 vs 3  → 3 is smaller    Result: [3]
Left:  [27, 38]     Right: [3, 43]
        ↑                      ↑
        
Step 2: Compare 27 vs 43 → 27 is smaller   Result: [3, 27]
Left:  [27, 38]     Right: [3, 43]
           ↑                   ↑
           
Step 3: Compare 38 vs 43 → 38 is smaller   Result: [3, 27, 38]
Left:  [27, 38]     Right: [3, 43]
           ↑ (done)            ↑
           
Step 4: Left exhausted, append rest        Result: [3, 27, 38, 43]


RECURSION TREE WITH WORK DONE AT EACH LEVEL:
───────────────────────────────────────────────────────────────────────────────

Level  Subproblems  Work per Level        Cumulative Work
  0        1         O(n) merge          = O(n)
  1        2         O(n/2) each         = O(n)
  2        4         O(n/4) each         = O(n)
  3        8         O(n/8) each         = O(n)
  ...
  log n    n         O(1) each           = O(n)

Total: O(n) work × O(log n) levels = O(n log n)

This is the OPTIMAL comparison-based sort!
"""


def merge_sort(arr):
    """Divide and conquer: split, recurse, merge"""
    if len(arr) <= 1:  # BASE: single element is sorted
        return arr
    
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])    # DIVIDE & CONQUER left
    right = merge_sort(arr[mid:])   # DIVIDE & CONQUER right
    
    # COMBINE: merge two sorted halves
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result


"""
═══════════════════════════════════════════════════════════════════════════════
        TYPE 7: INDIRECT/MUTUAL RECURSION (Functions Call Each Other)
═══════════════════════════════════════════════════════════════════════════════

Concept: Function A calls B, which calls A, forming a cycle.

CALL CHAIN VISUALIZATION: is_even(4)
───────────────────────────────────────────────────────────────────────────────

is_even(4) ─────────────┐
                        │ if n == 0: False
                        │ else: return is_odd(n-1)
                        ↓
                    is_odd(3) ──────────┐
                                        │ if n == 0: False
                                        │ else: return is_even(n-1)
                                        ↓
                                    is_even(2) ─────────┐
                                                        │
                                                        ↓
                                                    is_odd(1) ──────┐
                                                                    │
                                                                    ↓
                                                                is_even(0)
                                                                    │
                                                                    ↓
                                                                return True ✓

STACK FRAMES:
───────────────────────────────────────────────────────────────────────────────
┌──────────────┐
│ is_even(4)   │ ← Waiting for is_odd(3)
├──────────────┤
│ is_odd(3)    │ ← Waiting for is_even(2)
├──────────────┤
│ is_even(2)   │ ← Waiting for is_odd(1)
├──────────────┤
│ is_odd(1)    │ ← Waiting for is_even(0)
├──────────────┤
│ is_even(0)   │ ← Returns True
└──────────────┘

Then unwinds: True → True → True → True → True (all return True)
"""


def is_even(n):
    """Mutual recursion: calls is_odd"""
    if n == 0:
        return True
    return is_odd(n - 1)


def is_odd(n):
    """Mutual recursion: calls is_even"""
    if n == 0:
        return False
    return is_even(n - 1)


"""
═══════════════════════════════════════════════════════════════════════════════
    TYPE 8: NESTED RECURSION (Recursive Call Contains Recursive Call)
═══════════════════════════════════════════════════════════════════════════════

Concept: The argument to a recursive call is itself a recursive call.
Example: Ackermann function - one of the fastest-growing computable functions.

ackermann(2, 2) EXECUTION TREE:
───────────────────────────────────────────────────────────────────────────────

ackermann(2, 2)
│
└─► ackermann(1, ackermann(2, 1))          ◄─ Note: arg is recursive call!
              │
              └─► ackermann(1, ackermann(2, 0))
                            │
                            └─► ackermann(1, 1)
                                  │
                                  └─► ackermann(0, ackermann(1, 0))
                                                 │
                                                 └─► ackermann(0, 1)
                                                       │
                                                       └─► return 2

Now work backwards through the nesting...

This creates EXTREMELY deep recursion - ackermann(4, 2) can't be computed!

GROWTH COMPARISON:
───────────────────────────────────────────────────────────────────────────────
n           ackermann(4, n)        Approximate Value
0           13                     
1           65533                  (much larger!)
2           2^65536 - 3            (unimaginably large!)
3           2^2^65536 - 3          (beyond universe!)

The nesting causes computational explosion far beyond exponential growth.
"""


def ackermann(m, n):
    """Nested recursion: argument contains recursive call"""
    if m == 0:
        return n + 1
    if n == 0:
        return ackermann(m - 1, 1)
    return ackermann(m - 1, ackermann(m, n - 1))  # NESTED!


"""
═══════════════════════════════════════════════════════════════════════════════
        TYPE 9: TREE RECURSION IN DYNAMIC PROGRAMMING (State Space Tree)
═══════════════════════════════════════════════════════════════════════════════

Example: 0/1 Knapsack Problem
Given items with weights and values, maximize value without exceeding capacity.

DECISION TREE: items = [(w:2, v:3), (w:3, v:4), (w:4, v:5)], capacity = 5
───────────────────────────────────────────────────────────────────────────────

                            knapsack(items=3, cap=5)
                    ┌───────────────┴───────────────┐
            INCLUDE item 0                   EXCLUDE item 0
         (weight=2, value=3)                 (weight=0, value=0)
                    │                                 │
          knapsack(items=2, cap=3)          knapsack(items=2, cap=5)
        ┌──────────┴──────────┐            ┌──────────┴──────────┐
    INCLUDE item 1    EXCLUDE           INCLUDE item 1    EXCLUDE
    (w:3, v:4)        item 1           (w:3, v:4)        item 1
         │              │                     │              │
    knapsack(0,0)  knapsack(1,3)      knapsack(1,2)  knapsack(1,5)
    return 3       ┌────┴────┐        ┌────┴────┐    ┌────┴────┐
                INC    EXC         INC    EXC      INC    EXC
                (w:4)  (w:0)       (w:4)  (w:0)    (w:4)  (w:0)
                 │      │           │      │        │      │
              INVALID  3+0        INVALID  4+0     4+5    4+0
                       =3                  =4      =9     =4

Best path: INCLUDE item 0, EXCLUDE item 1, INCLUDE item 2 → value = 8

STATE REPRESENTATION:
───────────────────────────────────────────────────────────────────────────────
Each node = (index, remaining_capacity)

Without DP: Exponential branches O(2^n)
With DP:    Cache states by (index, capacity) → O(n * W) where W = capacity

MEMOIZATION KEY INSIGHT:
───────────────────────────────────────────────────────────────────────────────
State (index=1, cap=3) might be reached via:
  Path A: Include item 0
  Path B: Exclude item 0

Instead of computing both, we compute ONCE and cache!
"""


def knapsack_recursive(weights, values, capacity, n, memo=None):
    """DP on tree recursion: each node represents a state (n, capacity)"""
    if memo is None:
        memo = {}
    
    # BASE CASES
    if n == 0 or capacity == 0:
        return 0
    
    # CHECK MEMO
    if (n, capacity) in memo:
        return memo[(n, capacity)]
    
    # If weight of nth item > capacity, can't include it
    if weights[n - 1] > capacity:
        result = knapsack_recursive(weights, values, capacity, n - 1, memo)
    else:
        # Max of: include nth item OR exclude it
        include = values[n - 1] + knapsack_recursive(
            weights, values, capacity - weights[n - 1], n - 1, memo
        )
        exclude = knapsack_recursive(weights, values, capacity, n - 1, memo)
        result = max(include, exclude)
    
    memo[(n, capacity)] = result
    return result


"""
═══════════════════════════════════════════════════════════════════════════════
    TYPE 10: PERMUTATIONS & COMBINATIONS (Backtracking with Multiple Choices)
═══════════════════════════════════════════════════════════════════════════════

Generate all permutations of [1, 2, 3]

RECURSION TREE WITH STATE:
───────
```python
"""
═══════════════════════════════════════════════════════════════════════════════
    TYPE 10: PERMUTATIONS & COMBINATIONS (Backtracking with Multiple Choices)
═══════════════════════════════════════════════════════════════════════════════

Generate all permutations of [1, 2, 3]

RECURSION TREE WITH STATE:
───────────────────────────────────────────────────────────────────────────────

Level 0: current=[], remaining=[1,2,3]
         ┌──────────┼──────────┐
      Choose 1   Choose 2   Choose 3
         │          │          │
Level 1: current=[1]  current=[2]  current=[3]
         remaining=[2,3]  [1,3]      [1,2]
         ┌────┴────┐   ┌────┴────┐   ┌────┴────┐
       Take 2  Take 3  Take 1  Take 3  Take 1  Take 2
         │      │       │      │       │      │
Level 2: [1,2] [1,3]  [2,1]  [2,3]  [3,1]  [3,2]
         [3]    [2]    [3]    [1]    [2]    [1]
         │      │       │      │       │      │
Level 3: [1,2,3] [1,3,2] [2,1,3] [2,3,1] [3,1,2] [3,2,1]
         []       []      []      []      []      []
         ↓        ↓       ↓       ↓       ↓       ↓
      SOLUTION SOLUTION SOLUTION SOLUTION SOLUTION SOLUTION

THE BACKTRACKING PATTERN:
───────────────────────────────────────────────────────────────────────────────

At each level:
  1. ITERATE through available choices
  2. CHOOSE one element (add to current, remove from remaining)
  3. RECURSE to next level
  4. UNCHOOSE (backtrack) - restore state to try next option

DETAILED STATE EVOLUTION:
───────────────────────────────────────────────────────────────────────────────

Call Stack                Current Path    Remaining    Action
──────────────────────────────────────────────────────────────────────────────
permute([1,2,3])         []              [1,2,3]      Choose 1
  permute([2,3])         [1]             [2,3]        Choose 2
    permute([3])         [1,2]           [3]          Choose 3
      permute([])        [1,2,3]         []           BASE! Save [1,2,3]
      return                                          ↑ Unwind begins
    permute([3])         [1,2]           [3]          Backtrack from 3
                                                      Try next: none
    return                                           ↑
  permute([2,3])         [1]             [2,3]        Backtrack from 2
                                                      Try next: 3
    permute([2])         [1,3]           [2]          Choose 2
      permute([])        [1,3,2]         []           BASE! Save [1,3,2]
      return                                          ↑
    return                                           ↑
  return                                             ↑
permute([1,2,3])         []              [1,2,3]      Backtrack from 1
                                                      Try next: 2
  permute([1,3])         [2]             [1,3]        ...continues...

Space Complexity: O(n!) solutions × O(n) size = O(n! × n)
Time Complexity: O(n × n!) - generate each permutation costs O(n)
"""


def permutations(nums):
    """Backtracking: systematic exploration of all orderings"""
    def backtrack(current, remaining):
        if not remaining:  # BASE: used all elements
            result.append(current[:])
            return
        
        for i in range(len(remaining)):
            # CHOOSE: take element at index i
            current.append(remaining[i])
            new_remaining = remaining[:i] + remaining[i+1:]
            
            # EXPLORE: recurse with one less element
            backtrack(current, new_remaining)
            
            # UNCHOOSE: backtrack for next iteration
            current.pop()
    
    result = []
    backtrack([], nums)
    return result


"""
COMBINATIONS vs PERMUTATIONS:
───────────────────────────────────────────────────────────────────────────────

Permutations: ORDER MATTERS → [1,2,3] ≠ [3,2,1]
Combinations: ORDER DOESN'T MATTER → [1,2,3] = [3,2,1] (same set)

Generate combinations C(4,2) from [1,2,3,4]:

RECURSION TREE (with index tracking to avoid duplicates):
───────────────────────────────────────────────────────────────────────────────

Level 0: current=[], start=0, need 2 more elements
         ┌────────┬────────┬────────┬────────┐
      Take 1   Take 2   Take 3   Take 4
      (start=1) (start=2) (start=3) (start=4)
         │        │         │         │
Level 1: [1]      [2]       [3]       [4]
         start=1  start=2   start=3   start=4
         need 1   need 1    need 1    need 1
      ┌──┬─┬─┐   ┌─┬─┐     ┌─┐       X (can't pick more)
   Take 2 3 4  Take 3 4   Take 4
      │   │ │     │  │      │
     [1,2][1,3][1,4] [2,3][2,4] [3,4]
     DONE DONE DONE DONE DONE DONE

Results: [1,2], [1,3], [1,4], [2,3], [2,4], [3,4] = C(4,2) = 6 combinations

KEY INSIGHT: Start index prevents picking earlier elements, avoiding duplicates!
───────────────────────────────────────────────────────────────────────────────

Without start index:              With start index:
[1,2], [1,3], [1,4]              [1,2], [1,3], [1,4]
[2,1], [2,3], [2,4]  ← DUPES!    [2,3], [2,4]
[3,1], [3,2], [3,4]  ← DUPES!    [3,4]
[4,1], [4,2], [4,3]  ← DUPES!    
"""


def combinations(nums, k):
    """Backtracking with start index: prevent duplicate sets"""
    def backtrack(start, current):
        if len(current) == k:  # BASE: collected k elements
            result.append(current[:])
            return
        
        # Only consider elements from 'start' onwards (prevents duplicates)
        for i in range(start, len(nums)):
            current.append(nums[i])              # CHOOSE
            backtrack(i + 1, current)            # EXPLORE (i+1: next elements only)
            current.pop()                        # UNCHOOSE
    
    result = []
    backtrack(0, [])
    return result


"""
═══════════════════════════════════════════════════════════════════════════════
        TYPE 11: SUBSET GENERATION (Binary Choice Tree)
═══════════════════════════════════════════════════════════════════════════════

Generate all subsets (power set) of [1, 2, 3]

BINARY DECISION TREE: At each element, INCLUDE or EXCLUDE
───────────────────────────────────────────────────────────────────────────────

                                []
                  ┌──────────────┴──────────────┐
              Include 1                      Exclude 1
                  [1]                            []
          ┌───────┴───────┐            ┌─────────┴─────────┐
      Include 2      Exclude 2     Include 2           Exclude 2
        [1,2]          [1]            [2]                 []
      ┌───┴───┐      ┌───┴───┐      ┌───┴───┐         ┌───┴───┐
    Inc 3  Exc 3   Inc 3  Exc 3   Inc 3  Exc 3      Inc 3  Exc 3
   [1,2,3] [1,2]  [1,3]   [1]     [2,3]   [2]        [3]     []

LEAF NODES = ALL SUBSETS:
───────────────────────────────────────────────────────────────────────────────
[], [3], [2], [2,3], [1], [1,3], [1,2], [1,2,3]

Total: 2^n subsets (each element has 2 choices: in or out)

ALTERNATIVE VIEW - Binary String Representation:
───────────────────────────────────────────────────────────────────────────────

For [1, 2, 3], each subset corresponds to a 3-bit binary number:

Binary   Subset     Interpretation
000      []         Include none
001      [3]        Include only element at index 2
010      [2]        Include only element at index 1
011      [2,3]      Include elements at indices 1,2
100      [1]        Include only element at index 0
101      [1,3]      Include elements at indices 0,2
110      [1,2]      Include elements at indices 0,1
111      [1,2,3]    Include all elements

This explains why there are exactly 2^n subsets!
"""


def subsets(nums):
    """Backtracking: binary choice (include/exclude) for each element"""
    def backtrack(index, current):
        if index == len(nums):  # BASE: processed all elements
            result.append(current[:])
            return
        
        # EXCLUDE current element (don't add to current)
        backtrack(index + 1, current)
        
        # INCLUDE current element
        current.append(nums[index])
        backtrack(index + 1, current)
        current.pop()  # Backtrack
    
    result = []
    backtrack(0, [])
    return result


"""
═══════════════════════════════════════════════════════════════════════════════
    TYPE 12: GRAPH TRAVERSAL - DFS (Depth-First Search via Recursion)
═══════════════════════════════════════════════════════════════════════════════

Graph:    1 ─── 2
          │     │
          │     │
          3 ─── 4 ─── 5

Adjacency List: {1:[2,3], 2:[1,4], 3:[1,4], 4:[2,3,5], 5:[4]}

DFS TRAVERSAL STARTING FROM NODE 1:
───────────────────────────────────────────────────────────────────────────────

Step-by-step exploration:

Visit 1 (mark visited)
│
├─► Neighbor 2 (unvisited) → Visit 2
│   │
│   ├─► Neighbor 1 (visited, skip)
│   │
│   └─► Neighbor 4 (unvisited) → Visit 4
│       │
│       ├─► Neighbor 2 (visited, skip)
│       │
│       ├─► Neighbor 3 (unvisited) → Visit 3
│       │   │
│       │   ├─► Neighbor 1 (visited, skip)
│       │   │
│       │   └─► Neighbor 4 (visited, skip)
│       │   
│       │   (backtrack to 4)
│       │
│       └─► Neighbor 5 (unvisited) → Visit 5
│           │
│           └─► Neighbor 4 (visited, skip)
│           
│           (backtrack to 4, then 2, then 1)
│
└─► Neighbor 3 (already visited, skip)

(DFS complete)

TRAVERSAL ORDER: 1 → 2 → 4 → 3 → 5

RECURSION STACK EVOLUTION:
───────────────────────────────────────────────────────────────────────────────

Stack State                    Visited Set         Action
──────────────────────────────────────────────────────────────────────────────
[dfs(1)]                      {}                  Visit 1
[dfs(1), dfs(2)]              {1}                 Visit 2
[dfs(1), dfs(2), dfs(4)]      {1,2}               Visit 4
[dfs(1), dfs(2), dfs(4), dfs(3)] {1,2,4}          Visit 3
[dfs(1), dfs(2), dfs(4)]      {1,2,4,3}           Backtrack from 3
[dfs(1), dfs(2), dfs(4), dfs(5)] {1,2,4,3}        Visit 5
[dfs(1), dfs(2), dfs(4)]      {1,2,4,3,5}         Backtrack from 5
[dfs(1), dfs(2)]              {1,2,4,3,5}         Backtrack from 4
[dfs(1)]                      {1,2,4,3,5}         Backtrack from 2
[]                            {1,2,4,3,5}         Backtrack from 1

COMPARISON: DFS vs BFS
───────────────────────────────────────────────────────────────────────────────

DFS (Recursive):              BFS (Iterative with Queue):
- Uses call stack             - Uses explicit queue
- Explores depth first        - Explores level by level
- Space: O(height)            - Space: O(width)
- Natural for recursion       - Natural for shortest path

For graph above:
DFS: 1 → 2 → 4 → 3 → 5        BFS: 1 → 2 → 3 → 4 → 5
     (goes deep first)             (explores by level)
"""


def dfs_graph(graph, start, visited=None):
    """DFS: Recursive graph traversal"""
    if visited is None:
        visited = set()
    
    if start in visited:
        return
    
    visited.add(start)
    print(f"Visiting: {start}")
    
    for neighbor in graph[start]:
        dfs_graph(graph, neighbor, visited)


"""
═══════════════════════════════════════════════════════════════════════════════
        TYPE 13: TREE TRAVERSALS (In-order, Pre-order, Post-order)
═══════════════════════════════════════════════════════════════════════════════

Binary Tree:
                    1
                  /   \
                 2     3
                / \   / \
               4   5 6   7

THREE FUNDAMENTAL TRAVERSAL PATTERNS:
───────────────────────────────────────────────────────────────────────────────

1. PRE-ORDER (Root → Left → Right):
   Visit root BEFORE subtrees
   
                    1 ← Visit first (root)
                  /   \
                 2     3
                / \   / \
               4   5 6   7
   
   Recursion order:
   visit(1) → visit(2) → visit(4) → visit(5) → visit(3) → visit(6) → visit(7)
   
   Result: [1, 2, 4, 5, 3, 6, 7]
   Use case: Create copy of tree, serialize tree


2. IN-ORDER (Left → Root → Right):
   Visit root BETWEEN subtrees
   
                    1 ← Visit fourth (root)
                  /   \
                 2     3
                / \   / \
               4   5 6   7
   
   Recursion order:
   visit(4) → visit(2) → visit(5) → visit(1) → visit(6) → visit(3) → visit(7)
   
   Result: [4, 2, 5, 1, 6, 3, 7]
   Use case: BST traversal gives sorted order!


3. POST-ORDER (Left → Right → Root):
   Visit root AFTER subtrees
   
                    1 ← Visit last (root)
                  /   \
                 2     3
                / \   / \
               4   5 6   7
   
   Recursion order:
   visit(4) → visit(5) → visit(2) → visit(6) → visit(7) → visit(3) → visit(1)
   
   Result: [4, 5, 2, 6, 7, 3, 1]
   Use case: Delete tree, calculate tree properties

RECURSION STACK VISUALIZATION - IN-ORDER for subtree rooted at 2:
───────────────────────────────────────────────────────────────────────────────

inorder(2)
│
├─► inorder(2.left) = inorder(4)
│   │
│   ├─► inorder(4.left) = inorder(None) → return
│   │
│   ├─► visit(4) → print "4"
│   │
│   └─► inorder(4.right) = inorder(None) → return
│   
│   (returned to inorder(2))
│
├─► visit(2) → print "2"
│
└─► inorder(2.right) = inorder(5)
    │
    ├─► inorder(5.left) = inorder(None) → return
    │
    ├─► visit(5) → print "5"
    │
    └─► inorder(5.right) = inorder(None) → return

Output for this subtree: 4, 2, 5
"""


class TreeNode:
    def __init__(self, val, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def preorder(node):
    """Pre-order: Root → Left → Right"""
    if not node:
        return []
    return [node.val] + preorder(node.left) + preorder(node.right)


def inorder(node):
    """In-order: Left → Root → Right"""
    if not node:
        return []
    return inorder(node.left) + [node.val] + inorder(node.right)


def postorder(node):
    """Post-order: Left → Right → Root"""
    if not node:
        return []
    return postorder(node.left) + postorder(node.right) + [node.val]


"""
═══════════════════════════════════════════════════════════════════════════════
    TYPE 14: MEMOIZATION vs TABULATION (Top-Down vs Bottom-Up DP)
═══════════════════════════════════════════════════════════════════════════════

Same problem, two approaches: Longest Common Subsequence (LCS)

Strings: X = "ABCD", Y = "ACDF"

TOP-DOWN (Memoization - Recursive with Cache):
───────────────────────────────────────────────────────────────────────────────

Decision Tree (with memoization):

lcs("ABCD", "ACDF", 4, 4)
│
├─► D==F? NO
│   ├─► max(lcs("ABCD", "ACD", 4, 3), lcs("ABC", "ACDF", 3, 4))
│       │
│       ├─► lcs("ABCD", "ACD", 4, 3)
│       │   D==D? YES → 1 + lcs("ABC", "AC", 3, 2)
│       │                     │
│       │                     ├─► lcs("ABC", "AC", 3, 2)
│       │                         C==C? YES → 1 + lcs("AB", "A", 2, 1)
│       │                                           │
│       │                                           └─► ... returns 1
│       │                                     
│       │                                     Total: 1 + 1 + 1 = 3
│       │
│       └─► lcs("ABC", "ACDF", 3, 4)
│           C==F? NO → max(...) [memoized results used here] → 2
│
└─► returns 3

CACHE STATE (memo dictionary):
───────────────────────────────────────────────────────────────────────────────
Key (i,j)     Value    Meaning
(0, any)      0        Empty string X
(any, 0)      0        Empty string Y
(2, 1)        1        LCS("AB", "A") = 1
(3, 2)        2        LCS("ABC", "AC") = 2
(4, 3)        3        LCS("ABCD", "ACD") = 3
...


BOTTOM-UP (Tabulation - Iterative, build table):
───────────────────────────────────────────────────────────────────────────────

DP Table Construction:

      ""  A  C  D  F
 ""   0   0  0  0  0
 A    0   1  1  1  1
 B    0   1  1  1  1
 C    0   1  2  2  2
 D    0   1  2  3  3

Building process (row by row, left to right):

Step 1: Initialize base cases (row 0, col 0 = 0)
Step 2: For each cell (i,j):
        If X[i-1] == Y[j-1]: dp[i][j] = dp[i-1][j-1] + 1
        Else: dp[i][j] = max(dp[i-1][j], dp[i][j-1])

Cell (4,3) calculation:
X[3]='D', Y[2]='D' → MATCH!
dp[4][3] = dp[3][2] + 1 = 2 + 1 = 3

Final answer at dp[4][4] = 3

COMPARISON:
───────────────────────────────────────────────────────────────────────────────

Memoization (Top-Down):           Tabulation (Bottom-Up):
+ Natural recursive thinking      + Systematic, guaranteed complete
+ Computes only needed states     + No recursion overhead
+ Easy to write from recursion    + Better space optimization possible
- Stack overhead                  - Must compute all states
- Function call overhead          - Less intuitive initially

Space: O(m×n) for both           Time: O(m×n) for both
"""


def lcs_memo(X, Y, m, n, memo=None):
    """Top-down DP: Recursion with memoization"""
    if memo is None:
        memo = {}
    
    if m == 0 or n == 0:
        return 0
    
    if (m, n) in memo:
        return memo[(m, n)]
    
    if X[m-1] == Y[n-1]:
        result = 1 + lcs_memo(X, Y, m-1, n-1, memo)
    else:
        result = max(lcs_memo(X, Y, m-1, n, memo),
                     lcs_memo(X, Y, m, n-1, memo))
    
    memo[(m, n)] = result
    return result


def lcs_tab(X, Y):
    """Bottom-up DP: Iterative table construction"""
    m, n = len(X), len(Y)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if X[i-1] == Y[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    return dp[m][n]


"""
═══════════════════════════════════════════════════════════════════════════════
            TYPE 15: RECURSION WITH STATE MACHINES
═══════════════════════════════════════════════════════════════════════════════

Example: Regular Expression Matching with * (wildcard)
Pattern: "a*b" matches: "b", "ab", "aab", "aaab", ...

STATE SPACE EXPLORATION:
───────────────────────────────────────────────────────────────────────────────

match("aaab", "a*b")
│
├─► Current: 'a' vs 'a*'
│   Two choices: TAKE 'a' or SKIP 'a*' entirely
│   
│   Choice 1: TAKE 'a' (use one 'a' from pattern)
│   │
│   └─► match("aab", "a*b")
│       ├─► TAKE 'a'
│       │   │
│       │   └─► match("ab", "a*b")
│       │       ├─► TAKE 'a'
│       │       │   │
│       │       │   └─► match("b", "a*b")
│       │       │       ├─► TAKE 'a' → FAIL (no 'a' in text)
│       │       │       │
│       │       │       └─► SKIP 'a*'
│       │       │           │
│       │       │           └─► match("b", "b") → SUCCESS! ✓
│       │       │
│       │       └─► SKIP 'a*' → also leads to success
│       │
│       └─► SKIP 'a*' → also leads to success
│   
│   Choice 2: SKIP 'a*' entirely (use zero 'a's)
│   │
│   └─► match("aaab", "b") → FAIL (doesn't match 'a')
│
└─► Result: TRUE (found at least one successful path)

KEY INSIGHT: * creates branching - try using it 0, 1, 2, ... times
───────────────────────────────────────────────────────────────────────────────

State = (text_index, pattern_index)
Each state has multiple possible transitions
Find if ANY path leads to complete match

MEMOIZATION CRITICAL: Same (text_pos, pattern_pos) reached multiple ways
"""


def regex_match(text, pattern):
    """Recursion with state machine: multiple paths through state space"""
    memo = {}
    
    def dp(i, j):
        if (i, j) in memo:
            return memo[(i, j)]
        
        # BASE: reached end of pattern
        if j == len(pattern):
            return i == len(text)
        
        # Check if current characters match
        first_match = i < len(text) and pattern[j] in {text[i], '.'}
        
        # Handle * (zero or more of preceding element)
        if j + 1 < len(pattern) and pattern[j + 1] == '*':
            # Two choices:
            # 1. Skip pattern[j]* entirely (use zero occurrences)
            # 2. If first matches, consume text[i] and stay on pattern[j]*
            result = (dp(i, j + 2) or 
                     (first_match and dp(i + 1, j)))
        else:
            # No *, simple: must match and advance both
            result = first_match and dp(i + 1, j + 1)
        
        memo[(i, j)] = result
        return result
    
    return dp(0, 0)


"""
═══════════════════════════════════════════════════════════════════════════════
                    RECURSION COMPLEXITY ANALYSIS SUMMARY
═══════════════════════════════════════════════════════════════════════════════

Pattern              Time (Naive)    Time (Optimized)  Space        Example
──────────────────────────────────────────────────────────────────────────────
Linear              O(n)            O(n)              O(n) stack    factorial
Binary Tree         O(2^n)          O(n) with memo    O(n) depth    fibonacci
Backtracking        O(b^d)          O(b^d) pruned     O(d) depth    n-queens
Divide & Conquer    O(n log n)      O(n log n)        O(log n)      merge sort
Permutations        O(n!)           O(n!)             O(n)          permute
Combinations        O(2^n)          O(2^n)            O(n)          subset
Graph DFS           O(V+E)          O(V+E)            O(V) visited  traverse
Tree Traversal      O(n)            O(n)              O(height)     inorder
2D DP              O(2^(m+n))      O(m×n) with memo  O(m×n)        LCS

b = branching factor, d = depth, V = vertices, E = edges


KEY OPTIMIZATION TECHNIQUES:
───────────────────────────────────────────────────────────────────────────────

1. MEMOIZATION: Cache (state) → result mapping
   When to use: Overlapping subproblems
   
2. PRUNING: Early termination of dead-end branches
   When to use: Constraint violations detected early
   
3. TAIL RECURSION: Accumulator to avoid stack buildup
   When to use: Linear recursion, language supports TCO
   
4. ITERATIVE CONVERSION: Replace recursion with stack/queue
   When to use: Deep recursion, stack overflow risk


MENTAL MODEL FOR MASTERY:
───────────────────────────────────────────────────────────────────────────────

Think of recursion as:
1. STATE SPACE: What are the states? How do they relate?
2. TRANSITIONS: How do I move from one state to another?
3. BASE CASES: When do I stop descending?
4. COMBINATION: How do I combine subproblem results?

Every recursive problem is a GRAPH TRAVERSAL through state space!
- Nodes = states (function arguments)
- Edges = recursive calls
- Goal = reach base case(s)
- Path = sequence of recursive calls
- Solution = combining results along path


THE RECURSIVE LEAP OF FAITH:
───────────────────────────────────────────────────────────────────────────────

Master this mindset:
"Assume f(n-1) works correctly. How do I use it to compute f(n)?"

Don't trace every level mentally - trust the recursion!
Focus on:
1. What's the smallest problem I can solve? (base case)
2. How do I break big problem into smaller ones? (recursive case)
3. How do I combine smaller solutions? (return value)


═══════════════════════════════════════════════════════════════════════════════
                            YOU NOW UNDERSTAND:
═══════════════════════════════════════════════════════════════════════════════

✓ How the call stack manages recursion state
✓ Why memoization transforms exponential → polynomial
✓ When to use recursion vs iteration
✓ How backtracking systematically explores solution spaces
✓ The relationship between recursion and dynamic programming
✓ How to recognize and optimize recursive patterns

Practice these patterns until they become INSTINCTUAL. The top 1% don't just
know recursion - they THINK recursively. They see problems as state spaces,
recognize overlapping subproblems instantly, and architect elegant solutions
that compose small, correct pieces into powerful wholes.

Next level: Implement these in Rust (ownership challenges!), Go (no TCO but
goroutines for parallelism), and analyze YOUR OWN problems recursively before
reaching for loops.

Your mind is now a recursion engine. Deploy it wisely.
═══════════════════════════════════════

```python
"""
═══════════════════════════════════════════════════════════════════════════════
            TYPE 16: RECURSION WITH MULTIPLE DECISION POINTS
                    (Multi-way Branching in DP)
═══════════════════════════════════════════════════════════════════════════════

Example: Coin Change - Find minimum coins to make amount
Coins = [1, 2, 5], Amount = 11

DECISION TREE: At each state, try ALL coin denominations
───────────────────────────────────────────────────────────────────────────────

                            coinChange(11)
                    ┌───────────┼───────────┐
                Use coin 1   Use coin 2   Use coin 5
                    │            │            │
              coinChange(10) coinChange(9) coinChange(6)
              ┌────┼────┐   ┌────┼────┐   ┌────┼────┐
            Use1 Use2 Use5 ...          ...          ...
              │    │    │
         coin(9) coin(8) coin(5)
                           │
                        Eventually reaches 0 (base case)

WITHOUT MEMOIZATION - Overlapping Subproblems:
───────────────────────────────────────────────────────────────────────────────

coinChange(6) computed multiple times:
- Path 1: 11 → (use 5) → 6
- Path 2: 11 → (use 2) → 9 → (use 2) → 7 → (use 1) → 6
- Path 3: 11 → (use 1) → 10 → (use 2) → 8 → (use 2) → 6
... many more!

VISUALIZATION OF REDUNDANCY:
───────────────────────────────────────────────────────────────────────────────

Amount    Times Computed (naive)    Times Computed (memo)
  0            1                          1
  1            3                          1  
  2            9                          1
  3           27                          1
  4           81                          1
  5          243                          1
  6          729                          1  ← 729x reduction!
  ...

Time Complexity:
- Naive: O(amount ^ num_coins) - exponential explosion
- Memoized: O(amount × num_coins) - polynomial!

MEMOIZATION TABLE BUILD (Bottom-Up Perspective):
───────────────────────────────────────────────────────────────────────────────

Amount   0   1   2   3   4   5   6   7   8   9   10  11
────────────────────────────────────────────────────────────
Init     0   ∞   ∞   ∞   ∞   ∞   ∞   ∞   ∞   ∞   ∞   ∞

Try coin 1:
         0   1   2   3   4   5   6   7   8   9   10  11
                 ↑ (min(∞, dp[1]+1) = 2)

Try coin 2:
         0   1   1   2   2   3   3   4   4   5   5   6
                     ↑ (min(2, dp[1]+1) = 2, min(∞, dp[0]+1) = 1)

Try coin 5:
         0   1   1   2   2   1   2   2   3   3   2   3
                             ↑ (min(3, dp[0]+1) = 1)

Final: dp[11] = 3 coins (two 5's and one 1)

RECURRENCE RELATION VISUALIZATION:
───────────────────────────────────────────────────────────────────────────────

For amount = 11:
dp[11] = min(
    dp[11 - 1] + 1,  // Use coin 1 → dp[10] + 1 = 2 + 1 = 3
    dp[11 - 2] + 1,  // Use coin 2 → dp[9]  + 1 = 3 + 1 = 4
    dp[11 - 5] + 1   // Use coin 5 → dp[6]  + 1 = 2 + 1 = 3
) = 3

Visual representation:
                    dp[11] = ?
                    ┌───┴───┐
                    │ try all coins
                    ↓
    ┌───────────────┼───────────────┐
  dp[10]+1        dp[9]+1         dp[6]+1
    = 3             = 4             = 3
    
    Take minimum → dp[11] = 3
"""


def coin_change_memo(coins, amount, memo=None):
    """Multi-way recursion: Try each coin, take minimum"""
    if memo is None:
        memo = {}
    
    if amount == 0:
        return 0
    if amount < 0:
        return float('inf')
    if amount in memo:
        return memo[amount]
    
    # Try each coin and take minimum
    min_coins = float('inf')
    for coin in coins:
        result = coin_change_memo(coins, amount - coin, memo)
        if result != float('inf'):
            min_coins = min(min_coins, result + 1)
    
    memo[amount] = min_coins
    return min_coins


"""
═══════════════════════════════════════════════════════════════════════════════
        TYPE 17: RECURSION WITH CONSTRAINT PROPAGATION
                    (Backtracking with Forward Checking)
═══════════════════════════════════════════════════════════════════════════════

Example: Sudoku Solver - Fill 9×9 grid respecting row/col/box constraints

INTELLIGENT BACKTRACKING: Check constraints BEFORE recursing (prune early)
───────────────────────────────────────────────────────────────────────────────

Grid state (partial):
┌─────┬─────┬─────┐
│5 3 _│_ 7 _│_ _ _│  Current cell: (0,2) marked with _
│6 _ _│1 9 5│_ _ _│  
│_ 9 8│_ _ _│_ 6 _│
├─────┼─────┼─────┤
│8 _ _│_ 6 _│_ _ 3│
│4 _ _│8 _ 3│_ _ 1│
│7 _ _│_ 2 _│_ _ 6│
├─────┼─────┼─────┤
│_ 6 _│_ _ _│2 8 _│
│_ _ _│4 1 9│_ _ 5│
│_ _ _│_ 8 _│_ 7 9│
└─────┴─────┴─────┘

CONSTRAINT CHECKING for cell (0,2):
───────────────────────────────────────────────────────────────────────────────

Try digit = 1:
  Row 0 check:    [5,3,_,_,7,_,_,_,_] → No 1 present ✓
  Col 2 check:    [_,_,8,_,_,_,_,_,_] → No 1 present ✓
  Box (0,0) check: 5 3 _
                   6 _ _  → No 1 present ✓
                   _ 9 8
  ALL CONSTRAINTS SATISFIED → Place 1, recurse

Try digit = 2:
  Row 0 check:    [5,3,_,_,7,_,_,_,_] → No 2 present ✓
  Col 2 check:    [_,_,8,_,_,_,_,_,_] → No 2 present ✓
  Box (0,0) check: 5 3 _
                   6 _ _  → No 2 present ✓
                   _ 9 8
  ALL CONSTRAINTS SATISFIED → Place 2, recurse

Try digit = 3:
  Row 0 check:    [5,3,_,_,7,_,_,_,_] → 3 already present ✗
  CONSTRAINT VIOLATED → Skip this digit (PRUNE!)

RECURSION TREE WITH PRUNING:
───────────────────────────────────────────────────────────────────────────────

                        solve(0,2)
        ┌───────┬───────┬───────┬── ... ──┬───────┐
       try 1   try 2   try 3   try 4     try 9
        │       │       ✗       │          │
        │       │    (pruned)   │          │
        │       │               │          │
    solve(0,3) solve(0,3)   solve(0,3)  solve(0,3)
        │        │              │          │
       ...      ...            ...        ...
        │        │              │          │
        ✗     SUCCESS!          ✗          ✗
    (dead end) (found!)    (dead end) (dead end)

CRITICAL OPTIMIZATION: Check constraints BEFORE recursing!
───────────────────────────────────────────────────────────────────────────────

Without early checking:         With early checking:
- Place digit                   - Check constraints first
- Recurse on all 81 cells       - Skip invalid digits (PRUNE)
- Discover conflict later       - Only recurse on valid placements
- Backtrack up                  - Discover conflicts immediately

Complexity reduction:
Without: O(9^81) ~ 10^77 states to explore
With:    O(9^k) where k = empty cells, heavily pruned
         Typical: ~10^6 states (70 orders of magnitude better!)

STATE SPACE VISUALIZATION:
───────────────────────────────────────────────────────────────────────────────

Each level = one empty cell
Branch factor = digits that satisfy constraints (typically 2-5, not 9!)

Level 0 (cell 1):    [1][2][4][6]  (only 4 valid options due to constraints)
                      │  │  │  │
Level 1 (cell 2):    [3] [5] [7]  (3 options for each parent)
                      │   │   │
                     ...  ... ...
                      │   │   │
Level k (all filled): ✓   ✗   ✗   (only one leads to solution)

The power of constraint propagation: reducing 9^81 to manageable exploration!
"""


def solve_sudoku(board):
    """Backtracking with constraint checking (early pruning)"""
    def is_valid(board, row, col, num):
        # Check row
        if num in board[row]:
            return False
        
        # Check column
        if num in [board[i][col] for i in range(9)]:
            return False
        
        # Check 3×3 box
        box_row, box_col = 3 * (row // 3), 3 * (col // 3)
        for i in range(box_row, box_row + 3):
            for j in range(box_col, box_col + 3):
                if board[i][j] == num:
                    return False
        
        return True
    
    def backtrack():
        # Find next empty cell
        for i in range(9):
            for j in range(9):
                if board[i][j] == 0:
                    # Try each digit 1-9
                    for num in range(1, 10):
                        if is_valid(board, i, j, num):  # CONSTRAINT CHECK
                            board[i][j] = num           # CHOOSE
                            
                            if backtrack():             # EXPLORE
                                return True
                            
                            board[i][j] = 0             # UNCHOOSE (backtrack)
                    
                    return False  # No valid digit found
        
        return True  # All cells filled successfully
    
    backtrack()
    return board


"""
═══════════════════════════════════════════════════════════════════════════════
        TYPE 18: RECURSION WITH PATH RECONSTRUCTION
                    (Tracking Solution Path During Exploration)
═══════════════════════════════════════════════════════════════════════════════

Example: Word Break II - Find all ways to segment string into dictionary words
String: "catsanddog"
Dict: ["cat", "cats", "and", "sand", "dog"]

RECURSION TREE WITH PATH TRACKING:
───────────────────────────────────────────────────────────────────────────────

                        wordBreak("catsanddog", [])
                    ┌──────────────┴──────────────┐
            Try "cat" (match!)           Try "cats" (match!)
                    │                              │
        wordBreak("sanddog", ["cat"])   wordBreak("anddog", ["cats"])
                    │                              │
        ┌───────────┴───────────┐      ┌──────────┴──────────┐
    Try "sand"          Try ...     Try "and"        Try ...
    (match!)                        (match!)
        │                              │
wordBreak("dog",           wordBreak("dog",
    ["cat","sand"])           ["cats","and"])
        │                              │
    Try "dog"                      Try "dog"
    (match!)                       (match!)
        │                              │
    BASE CASE:                     BASE CASE:
    s = ""                         s = ""
    path = ["cat","sand","dog"]    path = ["cats","and","dog"]
        │                              │
    SAVE SOLUTION ✓                SAVE SOLUTION ✓

RESULTS: 
  1. "cat sand dog"
  2. "cats and dog"

PATH EVOLUTION VISUALIZATION:
───────────────────────────────────────────────────────────────────────────────

Remaining String    Current Path           Action
────────────────────────────────────────────────────────────────────────────
"catsanddog"       []                     Try "cat" (valid)
"sanddog"          ["cat"]                Try "sand" (valid)
"dog"              ["cat", "sand"]        Try "dog" (valid)
""                 ["cat", "sand", "dog"] BASE CASE → Save solution!
                                          ↑
                                      BACKTRACK
"dog"              ["cat", "sand"]        No more words to try
                                          ↑
                                      BACKTRACK
"sanddog"          ["cat"]                Try "s" (invalid)
                                      Try "sa" (invalid)
                                      ...
                                          ↑
                                      BACKTRACK
"catsanddog"       []                     Try "cats" (valid)
"anddog"           ["cats"]               Try "and" (valid)
...                                       (continues)

MEMOIZATION FOR PATH PROBLEMS:
───────────────────────────────────────────────────────────────────────────────

Key insight: Cache SOLUTIONS, not just boolean results!

memo["dog"] = [["dog"]]
memo["anddog"] = [["and", "dog"]]
memo["sanddog"] = [["sand", "dog"]]
memo["catsanddog"] = [["cat", "sand", "dog"], ["cats", "and", "dog"]]

When we encounter "dog" again via different path:
  Don't recompute! Just append cached solutions to current path.

RECURSIVE RELATION:
───────────────────────────────────────────────────────────────────────────────

wordBreak(s) = for each word in dict that is prefix of s:
                   [word] + wordBreak(s[len(word):])

Example:
wordBreak("catsanddog") = 
    [["cat"] + wordBreak("sanddog"),    → ["cat"] + [["sand","dog"]]
     ["cats"] + wordBreak("anddog")]    → ["cats"] + [["and","dog"]]
  = [["cat","sand","dog"], ["cats","and","dog"]]
"""


def word_break_ii(s, word_dict, memo=None):
    """Path reconstruction: build all valid segmentations"""
    if memo is None:
        memo = {}
    
    if s in memo:
        return memo[s]
    
    if not s:  # BASE: empty string
        return [[]]  # Return list containing one empty solution
    
    result = []
    for word in word_dict:
        if s.startswith(word):
            # Recursively break remaining string
            sub_results = word_break_ii(s[len(word):], word_dict, memo)
            
            # Prepend current word to each sub-result
            for sub in sub_results:
                result.append([word] + sub)
    
    memo[s] = result
    return result


"""
═══════════════════════════════════════════════════════════════════════════════
        TYPE 19: RECURSION WITH OPTIMIZATION OBJECTIVES
                    (Min/Max Path Problems on Graphs/Grids)
═══════════════════════════════════════════════════════════════════════════════

Example: Minimum Path Sum in Grid
Find path from top-left to bottom-right with minimum sum

Grid:
    1  3  1
    1  5  1
    4  2  1

RECURSIVE EXPLORATION (Brute Force):
───────────────────────────────────────────────────────────────────────────────

                            (0,0) val=1, sum=1
                        ┌─────────┴─────────┐
                    Go RIGHT            Go DOWN
                        │                    │
                    (0,1) val=3          (1,0) val=1
                    sum=4                sum=2
                ┌───────┴───────┐    ┌───────┴───────┐
            RIGHT           DOWN    RIGHT           DOWN
                │                │    │                │
            (0,2) val=1      (1,1)  (1,1)         (2,0) val=4
            sum=5            val=5  val=5         sum=6
                │            sum=9  sum=7             │
            DOWN                │    │             DOWN
                │         ┌─────┴─┐  └─┐              │
            (1,2) val=1  R       D    D          (3,0)  
            sum=6       (1,2)  (2,1) (2,1)       INVALID
                │       sum=10 sum=11 sum=9          
            DOWN           │      │     │          
                │        ...    ...   ...
            (2,2) val=1
            sum=7 ✓

All paths to (2,2):
  1. RIGHT→RIGHT→DOWN→DOWN: 1+3+1+1+1 = 7 ✓ (minimum!)
  2. RIGHT→DOWN→RIGHT→DOWN: 1+3+5+1+1 = 11
  3. RIGHT→DOWN→DOWN→RIGHT: 1+3+5+2+1 = 12
  4. DOWN→RIGHT→RIGHT→DOWN: 1+1+5+1+1 = 9
  5. DOWN→RIGHT→DOWN→RIGHT: 1+1+5+2+1 = 10
  6. DOWN→DOWN→RIGHT→RIGHT: 1+1+4+2+1 = 9

WITHOUT DP: O(2^(m+n)) paths to explore
WITH DP: O(m×n) states to compute

OVERLAPPING SUBPROBLEMS VISUALIZATION:
───────────────────────────────────────────────────────────────────────────────

Cell (1,1) reachable from:
  - (0,1) → DOWN
  - (1,0) → RIGHT

Both paths ask: "What's minimum path from (1,1) to (2,2)?"
WITHOUT memo: Compute twice!
WITH memo: Compute once, reuse!

Cells reached multiple times:
┌─────┬─────┬─────┐
│  1  │  1  │  1  │  ← Number of ways to reach each cell
├─────┼─────┼─────┤
│  1  │  2  │  1  │
├─────┼─────┼─────┤
│  1  │  1  │  1  │
└─────┴─────┴─────┘

Cell (1,1) reached 2 ways → compute subproblem twice in naive version!

DP TABLE CONSTRUCTION (Bottom-Up View):
───────────────────────────────────────────────────────────────────────────────

Step 1: Initialize first row and column
    1   4   5   ← Cumulative sums (can only go right)
    2   _   _
    6   _   _
    ↑ Cumulative sums (can only go down)

Step 2: Fill remaining cells (min of top or left, plus current)
    1   4   5
    2   7   6   ← min(7 from left, 5 from top) + 1 = 6
    6   8   7   ← min(8 from left, 6 from top) + 1 = 7

Final: dp[2][2] = 7

RECURRENCE RELATION:
───────────────────────────────────────────────────────────────────────────────

dp[i][j] = grid[i][j] + min(dp[i-1][j], dp[i][j-1])
                         └──────┬──────┘
                          Come from top or left,
                          whichever has smaller path sum

Visual:
            dp[i-1][j] (from above)
                  │
                  ↓
    dp[i][j-1] → [i,j] ← current cell
                  
    Choose minimum of two incoming paths!
"""


def min_path_sum(grid):
    """DP with optimization objective: minimize path sum"""
    if not grid:
        return 0
    
    m, n = len(grid), len(grid[0])
    memo = {}
    
    def dp(i, j):
        if i == m - 1 and j == n - 1:  # BASE: reached destination
            return grid[i][j]
        
        if i >= m or j >= n:  # OUT OF BOUNDS
            return float('inf')
        
        if (i, j) in memo:
            return memo[(i, j)]
        
        # Try going right or down, take minimum
        result = grid[i][j] + min(
            dp(i + 1, j),  # DOWN
            dp(i, j + 1)   # RIGHT
        )
        
        memo[(i, j)] = result
        return result
    
    return dp(0, 0)


"""
═══════════════════════════════════════════════════════════════════════════════
        TYPE 20: RECURSION WITH GAME THEORY (Minimax Algorithm)
═══════════════════════════════════════════════════════════════════════════════

Example: Optimal Strategy for Coin Game
Array: [3, 7, 2, 3]
Two players alternate picking from either end. Both play optimally.

MINIMAX GAME TREE:
───────────────────────────────────────────────────────────────────────────────

MAX = Player 1 (us), MIN = Player 2 (opponent)

Level 0 (MAX):            [3, 7, 2, 3]
                      ┌────────┴────────┐
                  Take 3              Take 3
                  (left)              (right)
                      │                    │
Level 1 (MIN):    [7, 2, 3]            [3, 7, 2]
                ┌─────┴─────┐        ┌─────┴─────┐
            Take 7      Take 3    Take 3      Take 2
            (left)      (right)   (left)      (right)
                │            │        │            │
Level 2 (MAX): [2, 3]      [7, 2]  [7, 2]      [3, 7]
            ┌───┴───┐   ┌───┴───┐ ┌───┴───┐  ┌───┴───┐
         Take 2 Take 3 Take 7 Take 2 ...      ...
            │     │     │     │
Level 3:   [3]   [2]   [2]   [7]  ... (Continue pattern)

EVALUATION (Bottom-Up):
───────────────────────────────────────────────────────────────────────────────

At leaves (base cases):
  [3] → Player 1 gets 3, return 3
  [2] → Player 1 gets 2, return 2
  [7] → Player 1 gets 7, return 7
  ...

At MIN nodes (opponent picks):
  [2, 3] → Opponent chooses min(2+MAX([3]), 3+MAX([2]))
           = min(2+3, 3+2) = min(5, 5) = 5
           Opponent takes 2, leaving us 3
  
At MAX nodes (we pick):
  [7, 2, 3] → We choose max(7+MIN([2,3]), 3+MIN([7,2]))
              = max(7+5, 3+7) = max(12, 10) = 12
              We take 7 (left)

ALPHA-BETA PRUNING (Advanced Optimization):
───────────────────────────────────────────────────────────────────────────────

Prune branches that can't affect final decision

                        MAX (α=-∞, β=+∞)
                    ┌─────────┴─────────┐
                MAX chooses left      MAX chooses right
                value = 12            value = ?
                    │                     │
                α = 12 now           Still exploring...
                    
                           MIN (α=12, β=+∞)
                        ┌──────┴──────┐
                    MIN left        MIN right
                    value = 10      value = ?
                        │               │
                    α = 12          β = 10 now
                    β = 10
                        │
                        └──► β ≤ α (10 ≤ 12) → PRUNE! ✂
                             No need to explore right subtree

The intuition: If MIN can already force score ≤ 10, but MAX already found
a path giving 12, MAX will never choose this MIN branch. Skip it!

RECURSION WITH TWO PERSPECTIVES:
───────────────────────────────────────────────────────────────────────────────

Key insight: SAME state, DIFFERENT player perspective!

State (arr, left, right):
  - When it's our turn: MAXIMIZE score
  - When it's opponent's turn: MINIMIZE our score (maximize theirs)

This alternating perspective is captured by:
  - Negating values as we recurse
  - Or explicitly tracking whose turn it is

Recurrence:
maxScore(left, right) = max(
    arr[left] + min(
        maxScore(left+2, right),    // Opponent took left
        maxScore(left+1, right-1)   // Opponent took right
    ),
    arr[right] + min(
        maxScore(left+1, right-1),  // Opponent took left
        maxScore(left, right-2)     // Opponent took right
    )
)

The min() represents opponent's optimal move (minimizes our remaining score)!
"""


def predict_winner(nums):
    """Game theory: minimax with memoization"""
    memo = {}
    
    def maxDiff(left, right):
        """Maximum score difference (our score - opponent's score)"""
        if left == right:  # BASE: one element left
            return nums[left]
        
        if (left, right) in memo:
            return memo[(left, right)]
        
        # Take left: our score + (-)opponent's best on remaining
        take_left = nums[left] - maxDiff(left + 1, right)
        
        # Take right: our score + (-)opponent's best on remaining
        take_right = nums[right] - maxDiff(left, right - 1)
        
        # We choose maximum
        result = max(take_left, take_right)
        memo[(left, right)] = result
        return result
    
    return maxDiff(0, len(nums) - 1) >= 0


"""
═══════════════════════════════════════════════════════════════════════════════
            TYPE 21: RECURSION WITH STRING PROCESSING
                    (Edit Distance / Transformation Problems)
═══════════════════════════════════════════════════════════════════════════════

Example: Edit Distance (Levenshtein Distance)
Transform "horse" → "ros" using insert, delete, replace operations

DECISION TREE:
───────────────────────────────────────────────────────────────────────────────

State: (i, j) = positions in word1 and word2

                    editDist("horse", "ros", 5, 3)
                              i=5, j=3
                    ┌──────────┼──────────┐
            word1[4]='e'     Delete e   Insert s   Replace e→s
            word2[2]='s'        │          │           │
            NOT EQUAL       ed(4,3)+1  ed(5,2)+1  ed(4,2)+1
                                │          │           │
                           ed(4,3)    ed(5,2)     ed(4,2)
                                │          │           │
                            "hors"     "horse"     "hors"
                            "ros"      "ro"        "ro"

COMPLETE RECURSION TREE (abbreviated):
───────────────────────────────────────────────────────────────────────────────

                        ("horse", "ros")
                              i=5, j=3
                    ┌──────────┼──────────┐
                Delete     Insert      Replace
               ed(4,3)+1  ed(5,2)+1   ed(4,2)+1
                    │          │           │
        ┌───────────┼──────────┤           ├────────┐
       Del    Ins   Repl      ...         ...      ...
        │      │     │                              
       ...    ...   ed(3,2)+1
                     │
                  ('r'=='r')
                     │
                  ed(2,1)+0  (MATCH! No operation)
                     │
                    ...

BASE CASES:
───────────────────────────────────────────────────────────────────────────────
1. i == 0: Must insert all remaining chars from word2 → return j
2. j == 0: Must delete all remaining chars from word1 → return i

Example:
  editDist("abc", "", 3, 0) → Must delete 3 chars → return 3
  editDist("", "xyz", 0, 3) → Must insert 3 chars → return 3

OVERLAPPING SUBPROBLEMS - DP Table:
───────────────────────────────────────────────────────────────────────────────

        ""  r  o  s
    ""   0  1  2  3   ← Base: insert 0,1,2,3 chars
    h    1  ?  ?  ?
    o    2  ?  ?  ?
    r    3  ?  ?  ?
    s    4  ?  ?  ?
    e    5  ?  ?  ?
    ↑
    Base: delete 0-5 chars

Filling the table:
        ""  r  o  s
    ""   0  1  2  3
    h    1  1  2  3   ← h≠r: min(del,ins,repl) = min(0+1, 1+1, 0+1) = 1
    o    2  2  1  2   ← o=o: take diagonal without adding = 1
    r    3  2  2  2   ← r=r: take diagonal = 2
    s    4  3  3  2   ← s=s: take diagonal = 2
    e    5  4  4  3   ← e≠s: min operations = 3

Final answer: dp[5][3] = 3

OPERATIONS VISUALIZATION:
──────────────────────────────────────────────────────────────────────────────────────────────