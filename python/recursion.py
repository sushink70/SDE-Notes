# Recursion: From Simple to Advanced

## What is Recursion?

# Recursion is a programming technique where a function calls itself to solve a problem by breaking it down into smaller, 
# similar subproblems. Every recursive function needs two key components:

# 1. **Base case**: A condition that stops the recursion
# 2. **Recursive case**: The function calling itself with a modified input

## Simple Example: Factorial


def factorial(n):
    # Base case
    if n == 0 or n == 1:
        return 1
    # Recursive case
    return n * factorial(n - 1)


# Here, `factorial(5)` becomes `5 * factorial(4)`, which becomes `5 * 4 * factorial(3)`, and so on.

## Big O Notation for Recursion

### Time Complexity
# - **Linear recursion** (like factorial): O(n)
# - **Binary recursion** (like Fibonacci): O(2^n) - exponential
# - **Divide and conquer** (like merge sort): O(n log n)

# ### Space Complexity
# Recursion uses the call stack, so space complexity is typically O(d) where d is the maximum depth of recursion.

### Example Analysis

# Inefficient Fibonacci - O(2^n) time, O(n) space
def fib(n):
    if n <= 1:
        return n
    return fib(n-1) + fib(n-2)

# Optimized with memoization - O(n) time, O(n) space
def fib_memo(n, memo={}):
    if n in memo:
        return memo[n]
    if n <= 1:
        return n
    memo[n] = fib_memo(n-1, memo) + fib_memo(n-2, memo)
    return memo[n]


## Algorithms Using Recursion

### 1. Tree Traversals

def inorder(root):
    if root:
        inorder(root.left)
        print(root.val)
        inorder(root.right)


### 2. Divide and Conquer

def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    
    return merge(left, right)


### 3. Backtracking

def solve_n_queens(n):
    def backtrack(row, board):
        if row == n:
            solutions.append(board[:])
            return
        
        for col in range(n):
            if is_safe(board, row, col):
                board[row] = col
                backtrack(row + 1, board)
                board[row] = -1
    
    solutions = []
    backtrack(0, [-1] * n)
    return solutions


### 4. Dynamic Programming

def coin_change(coins, amount):
    def dp(remaining):
        if remaining == 0:
            return 0
        if remaining < 0:
            return float('inf')
        
        min_coins = float('inf')
        for coin in coins:
            min_coins = min(min_coins, 1 + dp(remaining - coin))
        
        return min_coins
    
    result = dp(amount)
    return result if result != float('inf') else -1


## Advanced Recursion Concepts

### 1. Tail Recursion
# A recursive call is the last operation in the function. Some languages optimize this to avoid stack overflow.


# Not tail recursive
def factorial_normal(n):
    if n <= 1:
        return 1
    return n * factorial_normal(n - 1)  # multiplication after recursive call

# Tail recursive
def factorial_tail(n, acc=1):
    if n <= 1:
        return acc
    return factorial_tail(n - 1, n * acc)  # recursive call is last operation


### 2. Mutual Recursion
# Two or more functions calling each other.


def is_even(n):
    if n == 0:
        return True
    return is_odd(n - 1)

def is_odd(n):
    if n == 0:
        return False
    return is_even(n - 1)


### 3. Memoization
# Caching results to avoid redundant calculations.


from functools import lru_cache

@lru_cache(maxsize=None)
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)


## Essential SDE Concepts Related to Recursion

### 1. Call Stack
# Understanding how function calls are stored and managed in memory.

# ### 2. Stack Overflow
# When recursion depth exceeds the call stack limit.

# ### 3. Iterative vs Recursive Solutions
# Every recursive solution can be converted to iterative using explicit stacks.


# Recursive
def dfs_recursive(graph, node, visited):
    visited.add(node)
    for neighbor in graph[node]:
        if neighbor not in visited:
            dfs_recursive(graph, neighbor, visited)

# Iterative
def dfs_iterative(graph, start):
    visited = set()
    stack = [start]
    
    while stack:
        node = stack.pop()
        if node not in visited:
            visited.add(node)
            stack.extend(graph[node])


# ### 4. Divide and Conquer Paradigm
# Breaking problems into smaller subproblems, solving them recursively, and combining results.

# ### 5. Tree and Graph Algorithms
# Most tree/graph algorithms naturally use recursion.

# ## Real-World Examples

### 1. File System Navigation

import os

def find_files(directory, extension):
    files = []
    
    for item in os.listdir(directory):
        path = os.path.join(directory, item)
        
        if os.path.isfile(path) and path.endswith(extension):
            files.append(path)
        elif os.path.isdir(path):
            files.extend(find_files(path, extension))  # Recursive call
    
    return files


### 2. JSON Parsing

def parse_json_recursive(obj, key_to_find):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == key_to_find:
                return v
            result = parse_json_recursive(v, key_to_find)
            if result is not None:
                return result
    elif isinstance(obj, list):
        for item in obj:
            result = parse_json_recursive(item, key_to_find)
            if result is not None:
                return result
    return None


# ### 3. Database Query Optimization
# Many database systems use recursive algorithms for query planning and optimization.

# ### 4. Compiler Design
# Recursive descent parsers use recursion to parse programming language syntax.

### 5. Web Crawling

def crawl_website(url, visited=None, max_depth=3):
    if visited is None:
        visited = set()
    
    if url in visited or max_depth <= 0:
        return
    
    visited.add(url)
    
    # Process current page
    links = extract_links(url)
    
    # Recursively crawl found links
    for link in links:
        crawl_website(link, visited, max_depth - 1)


## When to Use Recursion

# **Use recursion when:**
# - Problem has a recursive structure (trees, graphs)
# - Problem can be broken into similar subproblems
# - Code becomes cleaner and more readable

# **Avoid recursion when:**
# - Performance is critical and iterative solution is more efficient
# - Stack overflow is a concern
# - Problem doesn't naturally fit recursive thinking

# Understanding recursion deeply is crucial for solving complex algorithmic problems and is fundamental to many advanced computer science concepts like dynamic programming, tree algorithms, and functional programming paradigms.

# I'll break down the concept of recursion from simple to advanced, covering its definition, how it works, examples, Big O notation, and algorithms that use recursion. I'll keep it concise yet comprehensive, as you haven't specified a preferred length.

# ---

### **Simple Explanation: What is Recursion?**
# Recursion is a programming technique where a function calls itself to solve a problem by breaking it into smaller, similar subproblems. It’s like solving a puzzle by dividing it into smaller pieces that look like the original puzzle.

# **Key Components**:
# 1. **Base Case**: The condition that stops the recursion, preventing infinite calls.
# 2. **Recursive Case**: The part where the function calls itself with a modified input, moving closer to the base case.

# **Simple Analogy**:
# Imagine opening a set of Russian nesting dolls. To find the smallest doll:
# - You open the current doll (recursive case).
# - If it’s empty or contains the smallest doll, you stop (base case).
# - Otherwise, you repeat the process with the next smaller doll.

# **Basic Example (Factorial)**:

def factorial(n):
    if n == 0 or n == 1:  # Base case
        return 1
    return n * factorial(n - 1)  # Recursive case

# - `factorial(4)` computes `4 * factorial(3)` → `4 * (3 * factorial(2))` → `4 * (3 * (2 * factorial(1)))` → `4 * 3 * 2 * 1 = 24`.

# ---

# ### **Intermediate Explanation: How Recursion Works**
# Recursion relies on the call stack, a data structure that tracks function calls. Each recursive call pushes a new "frame" onto the stack, storing the function’s state (parameters, local variables). When the base case is reached, the stack "unwinds," resolving each call.

# **Example: Fibonacci Sequence**

def fibonacci(n):
    if n <= 1:  # Base case
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)  # Recursive case

# - `fibonacci(5)` computes `fibonacci(4) + fibonacci(3)`, which further breaks down until base cases (`fibonacci(1)` or `fibonacci(0)`) are reached.
# - Call tree: `fib(5) → fib(4) + fib(3) → [fib(3) + fib(2)] + [fib(2) + fib(1)] → ...`

# **Pros**:
# - Elegant for problems with natural recursive structure (e.g., tree traversals, divide-and-conquer).
# - Reduces complex problems to simpler ones.

# **Cons**:
# - Can lead to stack overflow for deep recursion (many calls).
# - May be less efficient than iterative solutions due to stack overhead.

# ---

# ### **Advanced Explanation: Recursion in Depth**
# Recursion is powerful for problems where the solution depends on solutions to smaller instances of the same problem. It’s often used in **divide-and-conquer** and **dynamic programming** approaches.

# #### **Types of Recursion**
# 1. **Direct Recursion**: A function calls itself directly (e.g., `factorial` above).
# 2. **Indirect Recursion**: Function A calls Function B, which calls A (or a chain of calls).
   
   def is_even(n):
       if n == 0: return True
       return is_odd(n - 1)

   def is_odd(n):
       if n == 0: return False
       return is_even(n - 1)
   
# 3. **Tail Recursion**: The recursive call is the last operation in the function. Some languages optimize tail recursion to avoid stack growth.
#    
#    def factorial_tail(n, acc=1):
#        if n <= 1: return acc
#        return factorial_tail(n - 1, n * acc)  # Tail call
#    
# 4. **Head Recursion**: The recursive call occurs before other operations (less common, harder to optimize).
# 5. **Mutual Recursion**: Multiple functions call each other recursively (like `is_even` and `is_odd` above).

# #### **Optimizing Recursion**
# - **Memoization**: Store results of expensive recursive calls to avoid recomputation (used in dynamic programming).
  
  memo = {}
  def fibonacci_memo(n):
      if n in memo: return memo[n]
      if n <= 1: return n
      memo[n] = fibonacci_memo(n - 1) + fibonacci_memo(n - 2)
      return memo[n]
  
# - **Tail Call Optimization (TCO)**: Some languages (not Python) optimize tail-recursive calls to reuse stack frames, preventing overflow.
# - **Iterative Conversion**: Deep recursion can often be rewritten iteratively to save memory.

# #### **Big O Notation for Recursive Algorithms**
# Big O describes the worst-case time or space complexity of an algorithm. For recursive algorithms, it depends on:
# - Number of recursive calls per invocation.
# - Work done per call.
# - Depth of recursion.

# **Examples**:
# 1. **Factorial**:
#    - Time: `O(n)` (n recursive calls, constant work per call).
#    - Space: `O(n)` (n stack frames due to recursion depth).
# 2. **Fibonacci (Naive)**:
#    - Time: `O(2^n)` (exponential due to two recursive calls per level, forming a binary tree).
#    - Space: `O(n)` (stack depth equals n).
# 3. **Fibonacci (Memoized)**:
#    - Time: `O(n)` (each `n` computed once, stored in memo).
#    - Space: `O(n)` (stack depth + memo storage).
# 4. **Binary Search**:
   
   def binary_search(arr, target, low, high):
       if low > high: return -1  # Base case
       mid = (low + high) // 2
       if arr[mid] == target: return mid
       elif arr[mid] > target: return binary_search(arr, target, low, mid - 1)
       else: return binary_search(arr, target, mid + 1, high)
   
#    - Time: `O(log n)` (problem size halved each call).
#    - Space: `O(log n)` (stack depth from recursive calls).

# **Analyzing Big O**:
# - **Recurrence Relations**: Model recursive algorithms mathematically.
#   - Example: Naive Fibonacci: `T(n) = T(n-1) + T(n-2) + O(1) ≈ O(2^n)`.
#   - Binary Search: `T(n) = T(n/2) + O(1) = O(log n)` (via Master Theorem).
# - **Master Theorem**: For divide-and-conquer recurrences of form `T(n) = aT(n/b) + f(n)`:
#   - `a`: number of recursive calls.
#   - `b`: factor by which input size is reduced.
#   - `f(n)`: work done outside recursive calls.
#   - Compare `f(n)` with `n^(log_b(a))` to determine complexity.

# ---

# ### **Algorithms That Use Recursion**
# Recursion is natural for problems with hierarchical or self-similar structures. Common algorithms include:

# 1. **Divide-and-Conquer**:
#    - **Merge Sort**: Divides array into halves, recursively sorts, then merges.
#      - Time: `O(n log n)`.
#      - Space: `O(n)` (for merging).
#    - **Quick Sort**: Partitions array, recursively sorts subarrays.
#      - Time: `O(n log n)` average, `O(n^2)` worst case.
#      - Space: `O(log n)` average (stack depth).
#    - **Binary Search**: As shown above, halves search space each step.

# 2. **Tree and Graph Algorithms**:
#    - **Depth-First Search (DFS)**:
     
     def dfs(graph, node, visited):
         if node in visited: return
         visited.add(node)
         for neighbor in graph[node]:
             dfs(graph, neighbor, visited)
     
#      - Time: `O(V + E)` (vertices + edges).
#      - Space: `O(h)` (height of recursion tree).
#    - **Tree Traversals**: Pre-order, in-order, post-order (used in binary trees).
#      - Time: `O(n)` (visit each node once).
#      - Space: `O(h)` (height of tree).

# 3. **Dynamic Programming (Recursive Form)**:
#    - **Knapsack Problem**: Recursive solution with memoization.
#    - **Longest Common Subsequence**: Breaks into smaller subproblems.
#    - Time/Space: Varies (e.g., `O(n*m)` for LCS with memoization).

# 4. **Backtracking**:
#    - **N-Queens**: Places queens recursively, backtracks on invalid moves.
#    - **Sudoku Solver**: Tries values, backtracks on conflicts.
#    - Time: Often exponential (e.g., `O(n!)` for N-Queens), but pruning reduces complexity.

# 5. **Combinatorial Problems**:
#    - **Permutations/Combinations**: Generate all possible arrangements.
#    - **Tower of Hanoi**: Moves disks recursively following rules.
#      - Time: `O(2^n)`.
#      - Space: `O(n)`.

# ---

### **Practical Considerations**
# - **When to Use Recursion**:
#   - Problems with natural recursive structure (trees, graphs, divide-and-conquer).
#   - When code clarity outweighs minor performance costs.
# - **When to Avoid**:
#   - Deep recursion risks stack overflow (e.g., Python’s default limit is ~1000 calls).
#   - Iterative solutions may be faster for simple problems (e.g., factorial).
# - **Debugging Recursion**:
#   - Ensure base cases are correct and reachable.
#   - Trace call stack for small inputs.
#   - Use memoization for overlapping subproblems.

# ---

### **Summary Table of Big O for Common Recursive Algorithms**

# | Algorithm           | Time Complexity       | Space Complexity       |
# |--------------------|-----------------------|------------------------|
# | Factorial          | O(n)                 | O(n)                  |
# | Fibonacci (Naive)  | O(2^n)               | O(n)                  |
# | Fibonacci (Memoized)| O(n)                | O(n)                  |
# | Binary Search      | O(log n)             | O(log n)              |
# | Merge Sort         | O(n log n)           | O(n)                  |
# | Quick Sort         | O(n log n) avg, O(n²) worst | O(log n) avg   |
# | DFS (Graph)        | O(V + E)             | O(h) (height)         |
# | Tower of Hanoi     | O(2^n)               | O(n)                  |

# ---

# If you’d like a specific algorithm explained further, a chart of recursive call trees, or code for any example, let me know! For now, I’ve avoided generating charts since you didn’t explicitly request one and no numerical data was provided for plotting.

# How Recursion Works Internally: Deep Dive into Memory Management

## The Call Stack: Foundation of Recursion

# When a function calls itself, the computer uses a data structure called the **call stack** to manage execution. Let me break down exactly what happens.

# ### Stack Frame Structure

# Each function call creates a **stack frame** containing:
# - **Local variables**
# - **Function parameters**
# - **Return address** (where to continue after function returns)
# - **Previous frame pointer**
# - **CPU registers state**## Step-by-Step Memory Management Analysis

# ### 1. Function Call Process

# When `factorial(4)` is called, here's what happens internally:


# // Pseudocode for what happens internally
# void call_function(factorial, 4) {
#     // 1. Push current instruction pointer to stack
#     push(instruction_pointer);
    
#     // 2. Allocate new stack frame
#     stack_pointer -= sizeof(stack_frame);
    
#     // 3. Initialize frame
#     current_frame = {
#         parameters: {n: 4},
#         local_variables: {},
#         return_address: previous_instruction_pointer,
#         frame_pointer: stack_pointer
#     };
    
#     // 4. Jump to function code
#     instruction_pointer = factorial_address;
# }


# ### 2. Variable Storage and Access

# #### Stack Frame Layout (typical x86-64):

# High Memory Address
# ├─ Previous Frame
# ├─ Return Address     (8 bytes)
# ├─ Frame Pointer      (8 bytes)
# ├─ Parameter: n       (4 bytes)
# ├─ Local Variables    (variable)
# ├─ Saved Registers    (variable)
# └─ Next Frame
# Low Memory Address


# #### Memory Access Pattern:
# assembly
# ; Accessing parameter 'n' in factorial(n)
# mov eax, [rbp + 8]    ; Load n from stack frame
# cmp eax, 1            ; Compare with 1
# jle base_case         ; Jump if n <= 1


# ### 3. Deep Dive: Variable Lifecycle

# Let me show you exactly how variables are managed:


# // What happens during factorial(4) execution
# void factorial_internal_view() {
#     // Call 1: factorial(4)
#     // Stack grows DOWN in memory
#     // 0x1000: return_address_main
#     // 0x0FF8: frame_pointer_main  
#     // 0x0FF4: n = 4
#     // 0x0FF0: (space for local vars)
    
#     // Call 2: factorial(3) 
#     // 0x0FE8: return_address_factorial4
#     // 0x0FE0: frame_pointer_factorial4
#     // 0x0FDC: n = 3
#     // 0x0FD8: (space for local vars)
    
#     // And so on...
# }


# ### 4. Register Usage During Recursion

# The CPU registers play a crucial role:

# assembly
# ; Before recursive call
# push rbp          ; Save current frame pointer
# mov rbp, rsp      ; Set new frame pointer
# sub rsp, 16       ; Allocate space for locals

# ; During function execution
# mov eax, [rbp+8]  ; Load parameter n
# push eax          ; Push argument for recursive call
# call factorial    ; Make recursive call

# ; After recursive call
# mov ebx, eax      ; Store returned value
# mov eax, [rbp+8]  ; Load our n again
# imul eax, ebx     ; Multiply n * factorial(n-1)

# ; Function cleanup
# mov rsp, rbp      ; Restore stack pointer
# pop rbp           ; Restore frame pointer
# ret               ; Return to caller


# ### 5. Memory Layout Visualization


# STACK MEMORY (grows downward)
# ┌─────────────────────────────────┐ ← Higher Address (0x2000)
# │         main() frame            │
# ├─────────────────────────────────┤
# │      factorial(4) frame         │
# │  • n = 4                        │
# │  • return_addr = main+offset    │
# │  • frame_ptr = previous_frame   │
# ├─────────────────────────────────┤
# │      factorial(3) frame         │
# │  • n = 3                        │
# │  • return_addr = factorial4+off │
# │  • frame_ptr = factorial4_frame │
# ├─────────────────────────────────┤
# │      factorial(2) frame         │
# │  • n = 2                        │
# │  • return_addr = factorial3+off │
# │  • frame_ptr = factorial3_frame │
# ├─────────────────────────────────┤
# │      factorial(1) frame         │
# │  • n = 1                        │
# │  • return_addr = factorial2+off │
# │  • frame_ptr = factorial2_frame │
# └─────────────────────────────────┘ ← Lower Address (0x1000)
#                                     ← Stack Pointer (ESP/RSP)


# ### 6. Critical Memory Concepts

# #### Stack Overflow Detection

# // How stack overflow occurs
# void infinite_recursion(int n) {
#     char buffer[1024];  // Each call allocates 1KB
#     infinite_recursion(n + 1);  // No base case!
# }
# // After ~8000 calls (8MB stack), STACK OVERFLOW!


# #### Memory Fragmentation

# // Each recursive call fragments the stack
# void recursive_with_large_locals(int n) {
#     char large_array[10000];  // 10KB per call
#     int small_var;            // 4 bytes
#     // Memory between small_var and large_array is "wasted"
#     if (n > 0) recursive_with_large_locals(n - 1);
# }


# ### 7. Compiler Optimizations

# #### Tail Call Optimization

# // Not tail recursive - needs stack frame
# int factorial_normal(int n) {
#     if (n <= 1) return 1;
#     return n * factorial_normal(n - 1);  // Multiplication after call
# }

# // Tail recursive - can be optimized
# int factorial_tail(int n, int acc) {
#     if (n <= 1) return acc;
#     return factorial_tail(n - 1, n * acc);  // Direct return
# }


# #### What TCO does internally:
# assembly
# ; Without TCO (normal recursion)
# call factorial_normal
# imul eax, ebx        ; Multiply after return

# ; With TCO (tail recursion)
# jmp factorial_tail   ; Jump instead of call - reuses stack frame!


# ### 8. Memory Access Patterns

# #### Cache Behavior

# // Poor cache locality - each frame far apart
# void deep_recursion(int n) {
#     if (n <= 0) return;
#     deep_recursion(n - 1);
# }

# // Better cache locality - iterative
# void iterative_version(int n) {
#     for (int i = 0; i < n; i++) {
#         // Process here
#     }
# }


# ### 9. Advanced Memory Management

# #### Dynamic Memory in Recursion

# int* recursive_malloc(int n) {
#     if (n <= 0) return NULL;
    
#     int* arr = malloc(n * sizeof(int));  // Heap allocation
#     int* sub_result = recursive_malloc(n - 1);
    
#     // Memory leak potential!
#     // Each recursive call allocates but may not free
    
#     free(sub_result);  // Must free recursively allocated memory
#     return arr;
# }


# #### Memory Leak Detection

# // Each recursive call leaks memory
# void memory_leak_recursion(int n) {
#     char* buffer = malloc(1024);  // Allocated but never freed
#     if (n > 0) {
#         memory_leak_recursion(n - 1);
#     }
#     // Missing free(buffer)!
# }


# ### 10. Stack vs Heap in Recursion

# | Aspect | Stack Memory | Heap Memory |
# |--------|-------------|-------------|
# | **Allocation** | Automatic (function calls) | Manual (malloc/new) |
# | **Deallocation** | Automatic (function returns) | Manual (free/delete) |
# | **Speed** | Very fast | Slower |
# | **Size Limit** | Limited (~8MB) | Large (GB) |
# | **Fragmentation** | No fragmentation | Can fragment |
# | **Access Pattern** | LIFO (Last In, First Out) | Random access |

# ### 11. Debugging Recursion Issues

# #### Stack Trace Analysis

# // gdb stack trace for factorial(4)
# #0  factorial (n=1) at recursion.c:4
# #1  factorial (n=2) at recursion.c:6
# #2  factorial (n=3) at recursion.c:6  
# #3  factorial (n=4) at recursion.c:6
# #4  main () at recursion.c:10


# #### Memory Debugging Tools

# # Valgrind for memory leaks
# valgrind --tool=memcheck --leak-check=full ./recursive_program

# # GDB for stack analysis
# gdb ./recursive_program
# (gdb) backtrace  # Show call stack
# (gdb) info registers  # Show register state
# (gdb) x/32x $rsp  # Examine stack memory


# ### 12. Performance Implications

# #### Memory Bandwidth

# // High memory bandwidth usage
# void bandwidth_heavy_recursion(int n) {
#     char buffer[4096];  // 4KB per call
#     memset(buffer, 0, sizeof(buffer));  // Touch every byte
#     if (n > 0) bandwidth_heavy_recursion(n - 1);
# }


# #### CPU Cache Misses

# // Cache-friendly recursion
# void cache_friendly(int* arr, int start, int end) {
#     if (start >= end) return;
    
#     int mid = (start + end) / 2;
#     cache_friendly(arr, start, mid);      // Process left half
#     cache_friendly(arr, mid + 1, end);    // Process right half
# }


# This deep dive shows that recursion isn't just about function calls - it's about understanding how the computer manages memory, registers, and the call stack at the hardware level. Each recursive call creates a complete execution context that must be preserved and restored, making recursion both powerful and memory-intensive.