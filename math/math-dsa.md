For coding and data structures & algorithms (DSA), here are the essential mathematical concepts you should master:

https://claude.ai/public/artifacts/c867e2ab-c629-4779-842c-19970350e465

**Foundational Mathematics:**
- **Discrete Mathematics** - Logic, sets, relations, functions, and proof techniques form the backbone of computer science reasoning
- **Boolean Algebra** - Essential for understanding logic gates, conditional statements, and bitwise operations
- **Number Theory** - Prime numbers, modular arithmetic, and GCD/LCM are crucial for cryptography and optimization problems

**Algorithm Analysis:**
- **Big O Notation** - Understanding time and space complexity is fundamental for evaluating algorithm efficiency
- **Logarithms** - Critical for analyzing divide-and-conquer algorithms, binary search, and tree operations
- **Summations and Series** - Needed to calculate the total work done by loops and recursive algorithms

**Data Structure Mathematics:**
- **Graph Theory** - Vertices, edges, paths, cycles, and graph traversals are essential for network problems
- **Tree Mathematics** - Binary trees, heap properties, and tree traversal algorithms
- **Combinatorics** - Counting principles, permutations, and combinations for solving arrangement problems

**Problem-Solving Techniques:**
- **Linear Algebra** - Matrix operations, especially for graphics programming and machine learning algorithms
- **Probability and Statistics** - Random algorithms, expected value calculations, and data analysis
- **Recursive Relations** - Understanding how to set up and solve recurrence relations for analyzing recursive algorithms

**Advanced Topics:**
- **Geometry** - Coordinate geometry for computational geometry problems
- **Dynamic Programming Mathematics** - Optimal substructure and overlapping subproblems
- **Game Theory** - Minimax algorithms and strategic decision-making in competitive programming

The depth you need depends on your goals. For general software development, focus heavily on Big O analysis, basic discrete math, and logarithms. For competitive programming or specialized fields, you'll want stronger foundations in all these areas.

I'll provide detailed examples for each mathematical concept used in coding and DSA:I've created a comprehensive guide with detailed examples for all the mathematical concepts essential for coding and DSA. Each section includes:

**Practical Code Examples** - Real implementations showing how the math is used
**Mathematical Analysis** - Why the math works and how it applies
**Complexity Analysis** - How the math helps us understand performance
**Problem-Solving Applications** - Where you'd use these concepts in actual coding problems

The examples progress from foundational concepts like discrete math and Boolean algebra, through algorithm analysis with Big O and logarithms, to advanced topics like dynamic programming and game theory.

Key takeaways:
- **Start with the fundamentals** - Discrete math, Boolean algebra, and basic number theory
- **Master Big O analysis** - This is crucial for any coding interview or optimization work  
- **Understand logarithms** - They appear everywhere in efficient algorithms
- **Learn graph theory** - Essential for network problems and many real-world applications
- **Practice combinatorics** - Helps with counting and arrangement problems

Would you like me to elaborate on any specific section or provide more examples for particular concepts that interest you most?

# Mathematics for Coding & DSA - Detailed Examples

## 1. Foundational Mathematics

### Discrete Mathematics

**Logic & Proof Techniques:**
```python
# Example: Proving algorithm correctness using mathematical induction
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n-1)

# Proof by induction that factorial(n) = n!
# Base case: factorial(1) = 1 = 1!
# Inductive step: If factorial(k) = k!, then factorial(k+1) = (k+1) * factorial(k) = (k+1) * k! = (k+1)!
```

**Sets and Relations:**
```python
# Finding intersection of two arrays (set theory)
def intersection(arr1, arr2):
    set1 = set(arr1)
    set2 = set(arr2)
    return list(set1 & set2)  # Set intersection operation

# Example: arr1 = [1,2,3,4], arr2 = [3,4,5,6]
# Result: [3,4]
```

### Boolean Algebra

**Logic Gates in Code:**
```python
# XOR operation for finding unique element
def find_unique(arr):
    result = 0
    for num in arr:
        result ^= num  # XOR operation
    return result

# Example: [4,1,2,1,2] → 4 (all others appear twice, XOR cancels them out)
# 4 ^ 1 ^ 2 ^ 1 ^ 2 = 4 ^ (1^1) ^ (2^2) = 4 ^ 0 ^ 0 = 4
```

**De Morgan's Laws:**
```python
# !(A && B) = !A || !B
# !(A || B) = !A && !B

def validate_input(x, y):
    # Instead of: not (x > 0 and y > 0)
    # Use: x <= 0 or y <= 0
    return x <= 0 or y <= 0
```

### Number Theory

**GCD/LCM Applications:**
```python
def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

def lcm(a, b):
    return (a * b) // gcd(a, b)

# Application: Simplifying fractions
def simplify_fraction(numerator, denominator):
    g = gcd(numerator, denominator)
    return numerator // g, denominator // g

# Example: 12/18 → gcd(12,18) = 6 → 2/3
```

**Modular Arithmetic:**
```python
# Fast exponentiation using modular arithmetic
def power_mod(base, exp, mod):
    result = 1
    base = base % mod
    while exp > 0:
        if exp % 2 == 1:
            result = (result * base) % mod
        exp = exp >> 1
        base = (base * base) % mod
    return result

# Example: 2^10 mod 1000 = 1024 mod 1000 = 24
```

## 2. Algorithm Analysis

### Big O Notation

**Time Complexity Examples:**
```python
# O(1) - Constant time
def get_first_element(arr):
    return arr[0] if arr else None

# O(log n) - Logarithmic time
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1

# O(n) - Linear time
def linear_search(arr, target):
    for i, val in enumerate(arr):
        if val == target:
            return i
    return -1

# O(n²) - Quadratic time
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]

# O(2^n) - Exponential time (naive Fibonacci)
def fibonacci_naive(n):
    if n <= 1:
        return n
    return fibonacci_naive(n-1) + fibonacci_naive(n-2)
```

### Logarithms

**Why Binary Search is O(log n):**
```python
# Each iteration cuts search space in half
# n elements → n/2 → n/4 → n/8 → ... → 1
# Number of steps = log₂(n)

def analyze_binary_search_steps(n):
    steps = 0
    while n > 1:
        n = n // 2
        steps += 1
    return steps

# For n=1000: log₂(1000) ≈ 10 steps
# For n=1,000,000: log₂(1,000,000) ≈ 20 steps
```

**Tree Height Calculations:**
```python
import math

def tree_height(num_nodes):
    # Complete binary tree height = floor(log₂(n))
    return math.floor(math.log2(num_nodes))

def max_nodes_at_height(h):
    # Maximum nodes at height h = 2^h
    return 2 ** h

# Example: Binary tree with 15 nodes has height 3
# Level 0: 1 node, Level 1: 2 nodes, Level 2: 4 nodes, Level 3: 8 nodes
```

### Summations and Series

**Loop Analysis:**
```python
# Analyzing nested loops
def sum_analysis_example(n):
    total_operations = 0
    
    # Outer loop: i from 1 to n
    for i in range(1, n+1):
        # Inner loop: j from 1 to i
        for j in range(1, i+1):
            total_operations += 1
    
    return total_operations

# Mathematical analysis:
# Sum from i=1 to n of (sum from j=1 to i of 1)
# = Sum from i=1 to n of i
# = 1 + 2 + 3 + ... + n
# = n(n+1)/2
# Therefore: O(n²)
```

**Geometric Series in Algorithms:**
```python
# Merge sort analysis
def merge_sort_operations(n):
    if n <= 1:
        return 1
    
    # Each level does O(n) work
    # Number of levels = log₂(n)
    # Total work = n * log₂(n)
    
    levels = math.log2(n)
    work_per_level = n
    return levels * work_per_level

# Example: For n=8
# Level 0: 8 elements → 4 + 4
# Level 1: 4 elements → 2+2 + 2+2  
# Level 2: 2 elements → 1+1 + 1+1 + 1+1 + 1+1
# Total: 3 levels × 8 operations = 24 operations
```

## 3. Data Structure Mathematics

### Graph Theory

**Graph Representation:**
```python
class Graph:
    def __init__(self, vertices):
        self.V = vertices
        self.adj = [[] for _ in range(vertices)]
    
    def add_edge(self, u, v):
        self.adj[u].append(v)
        self.adj[v].append(u)  # For undirected graph

# Adjacency matrix space: O(V²)
# Adjacency list space: O(V + E)
```

**Shortest Path (Dijkstra's Algorithm):**
```python
import heapq

def dijkstra(graph, start):
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    pq = [(0, start)]
    
    while pq:
        current_distance, current = heapq.heappop(pq)
        
        if current_distance > distances[current]:
            continue
            
        for neighbor, weight in graph[current]:
            distance = current_distance + weight
            
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                heapq.heappush(pq, (distance, neighbor))
    
    return distances

# Time complexity: O((V + E) log V)
# Uses properties of logarithms in heap operations
```

**Graph Connectivity:**
```python
def is_connected(graph):
    if not graph:
        return True
    
    visited = set()
    start = next(iter(graph))
    
    def dfs(node):
        visited.add(node)
        for neighbor in graph[node]:
            if neighbor not in visited:
                dfs(neighbor)
    
    dfs(start)
    return len(visited) == len(graph)

# Uses graph theory concepts: connected components, DFS traversal
```

### Tree Mathematics

**Binary Search Tree Properties:**
```python
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def is_valid_bst(root, min_val=float('-inf'), max_val=float('inf')):
    if not root:
        return True
    
    if root.val <= min_val or root.val >= max_val:
        return False
    
    return (is_valid_bst(root.left, min_val, root.val) and 
            is_valid_bst(root.right, root.val, max_val))

# Mathematical property: For any node n,
# all nodes in left subtree < n.val < all nodes in right subtree
```

**Heap Properties:**
```python
def heapify(arr, n, i):
    largest = i
    left = 2 * i + 1      # Left child index
    right = 2 * i + 2     # Right child index
    
    # Mathematical relationship: parent at i, children at 2i+1 and 2i+2
    
    if left < n and arr[left] > arr[largest]:
        largest = left
    
    if right < n and arr[right] > arr[largest]:
        largest = right
    
    if largest != i:
        arr[i], arr[largest] = arr[largest], arr[i]
        heapify(arr, n, largest)

# Height of complete binary tree with n nodes = floor(log₂(n))
```

**Tree Traversal Mathematics:**
```python
def count_nodes(root):
    if not root:
        return 0
    return 1 + count_nodes(root.left) + count_nodes(root.right)

def tree_height(root):
    if not root:
        return -1
    return 1 + max(tree_height(root.left), tree_height(root.right))

# Relationship: For a balanced binary tree with n nodes,
# height = O(log n)
# For a skewed tree: height = O(n)
```

### Combinatorics

**Permutations and Combinations in Code:**
```python
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n-1)

def permutations(n, r):
    # P(n,r) = n! / (n-r)!
    return factorial(n) // factorial(n - r)

def combinations(n, r):
    # C(n,r) = n! / (r! * (n-r)!)
    return factorial(n) // (factorial(r) * factorial(n - r))

# Example: How many ways to arrange 3 people from 5?
# P(5,3) = 5!/(5-3)! = 120/2 = 60

# Example: How many ways to choose 3 people from 5?
# C(5,3) = 5!/(3!*2!) = 120/(6*2) = 10
```

**Generate All Permutations:**
```python
def generate_permutations(nums):
    if len(nums) <= 1:
        return [nums]
    
    result = []
    for i in range(len(nums)):
        rest = nums[:i] + nums[i+1:]
        for perm in generate_permutations(rest):
            result.append([nums[i]] + perm)
    
    return result

# Time complexity: O(n! * n) - factorial number of permutations
# Space complexity: O(n! * n) - storing all permutations
```

## 4. Problem-Solving Techniques

### Linear Algebra

**Matrix Operations in Algorithms:**
```python
def matrix_multiply(A, B):
    rows_A, cols_A = len(A), len(A[0])
    rows_B, cols_B = len(B), len(B[0])
    
    if cols_A != rows_B:
        return None
    
    result = [[0 for _ in range(cols_B)] for _ in range(rows_A)]
    
    for i in range(rows_A):
        for j in range(cols_B):
            for k in range(cols_A):
                result[i][j] += A[i][k] * B[k][j]
    
    return result

# Time complexity: O(n³) for n×n matrices
# Used in: shortest paths (Floyd-Warshall), graphics transformations
```

**Matrix Chain Multiplication:**
```python
def matrix_chain_order(dimensions):
    n = len(dimensions) - 1
    dp = [[0 for _ in range(n)] for _ in range(n)]
    
    # l is chain length
    for l in range(2, n + 1):
        for i in range(n - l + 1):
            j = i + l - 1
            dp[i][j] = float('inf')
            for k in range(i, j):
                cost = (dp[i][k] + dp[k+1][j] + 
                       dimensions[i] * dimensions[k+1] * dimensions[j+1])
                dp[i][j] = min(dp[i][j], cost)
    
    return dp[0][n-1]

# Example: Matrices A₁(40×20), A₂(20×30), A₃(30×10)
# dimensions = [40, 20, 30, 10]
# Finds optimal way to parenthesize: (A₁A₂)A₃ vs A₁(A₂A₃)
```

### Probability and Statistics

**Random Algorithms:**
```python
import random

def quicksort_randomized(arr, low, high):
    if low < high:
        # Randomized partition reduces worst-case probability
        random_index = random.randint(low, high)
        arr[random_index], arr[high] = arr[high], arr[random_index]
        
        pi = partition(arr, low, high)
        quicksort_randomized(arr, low, pi - 1)
        quicksort_randomized(arr, pi + 1, high)

# Expected time complexity: O(n log n)
# Worst case probability: 1/n! (very low)
```

**Monte Carlo Methods:**
```python
def estimate_pi(n):
    inside_circle = 0
    
    for _ in range(n):
        x = random.uniform(-1, 1)
        y = random.uniform(-1, 1)
        
        if x*x + y*y <= 1:
            inside_circle += 1
    
    pi_estimate = 4 * inside_circle / n
    return pi_estimate

# Uses probability: Area of circle / Area of square = π/4
# As n increases, estimate approaches π
```

### Recursive Relations

**Solving Recurrence Relations:**
```python
def fibonacci_dp(n):
    if n <= 1:
        return n
    
    dp = [0] * (n + 1)
    dp[1] = 1
    
    for i in range(2, n + 1):
        dp[i] = dp[i-1] + dp[i-2]
    
    return dp[n]

# Recurrence relation: F(n) = F(n-1) + F(n-2)
# Solution: F(n) = (φⁿ - ψⁿ)/√5 where φ = (1+√5)/2, ψ = (1-√5)/2
# Time complexity reduced from O(2ⁿ) to O(n)
```

**Master Theorem Applications:**
```python
# T(n) = aT(n/b) + f(n)

# Merge Sort: T(n) = 2T(n/2) + O(n)
# a=2, b=2, f(n)=n, n^(log_b(a)) = n^1 = n
# Case 2: f(n) = Θ(n^(log_b(a))) → T(n) = Θ(n log n)

# Binary Search: T(n) = T(n/2) + O(1)
# a=1, b=2, f(n)=1, n^(log_b(a)) = n^0 = 1
# Case 2: f(n) = Θ(n^(log_b(a))) → T(n) = Θ(log n)
```

## 5. Advanced Topics

### Geometry

**Computational Geometry:**
```python
def distance(p1, p2):
    return ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)**0.5

def point_in_polygon(point, polygon):
    x, y = point
    n = len(polygon)
    inside = False
    
    p1x, p1y = polygon[0]
    for i in range(n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside

# Uses ray casting algorithm and coordinate geometry
```

**Convex Hull (Graham Scan):**
```python
def orientation(p, q, r):
    val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
    if val == 0:
        return 0  # Collinear
    return 1 if val > 0 else 2  # Clockwise or Counterclockwise

def convex_hull(points):
    n = len(points)
    if n < 3:
        return []
    
    # Find bottom-most point
    l = 0
    for i in range(1, n):
        if points[i][1] < points[l][1]:
            l = i
        elif points[i][1] == points[l][1] and points[i][0] < points[l][0]:
            l = i
    
    hull = []
    p = l
    while True:
        hull.append(points[p])
        q = (p + 1) % n
        
        for i in range(n):
            if orientation(points[p], points[i], points[q]) == 2:
                q = i
        
        p = q
        if p == l:
            break
    
    return hull

# Time complexity: O(n²), can be optimized to O(n log n)
```

### Dynamic Programming Mathematics

**Optimal Substructure:**
```python
def coin_change(coins, amount):
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0
    
    for coin in coins:
        for i in range(coin, amount + 1):
            dp[i] = min(dp[i], dp[i - coin] + 1)
    
    return dp[amount] if dp[amount] != float('inf') else -1

# Recurrence relation: dp[i] = min(dp[i], dp[i-coin] + 1) for all coins
# Optimal substructure: optimal solution contains optimal solutions to subproblems
```

**Edit Distance (Levenshtein Distance):**
```python
def edit_distance(s1, s2):
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j],      # Deletion
                                   dp[i][j-1],      # Insertion
                                   dp[i-1][j-1])    # Substitution
    
    return dp[m][n]

# Mathematical recurrence captures three operations with minimum cost
```

### Game Theory

**Minimax Algorithm:**
```python
def minimax(board, depth, is_maximizing, alpha=float('-inf'), beta=float('inf')):
    score = evaluate_board(board)
    
    # Base cases
    if score == 10:  # Maximizer wins
        return score - depth
    if score == -10:  # Minimizer wins
        return score + depth
    if not moves_left(board):  # Tie
        return 0
    
    if is_maximizing:
        best = float('-inf')
        for move in get_possible_moves(board):
            make_move(board, move)
            val = minimax(board, depth + 1, False, alpha, beta)
            undo_move(board, move)
            best = max(best, val)
            alpha = max(alpha, best)
            if beta <= alpha:
                break  # Alpha-beta pruning
        return best
    else:
        best = float('inf')
        for move in get_possible_moves(board):
            make_move(board, move)
            val = minimax(board, depth + 1, True, alpha, beta)
            undo_move(board, move)
            best = min(best, val)
            beta = min(beta, best)
            if beta <= alpha:
                break  # Alpha-beta pruning
        return best

# Game tree exploration with mathematical optimization (alpha-beta pruning)
# Reduces search space from O(b^d) to O(b^(d/2)) in best case
```

**Nash Equilibrium in Code:**
```python
def find_nash_equilibrium(payoff_matrix_p1, payoff_matrix_p2):
    # Simplified 2x2 game
    strategies_p1 = len(payoff_matrix_p1)
    strategies_p2 = len(payoff_matrix_p1[0])
    
    equilibria = []
    
    # Check pure strategy Nash equilibria
    for i in range(strategies_p1):
        for j in range(strategies_p2):
            is_equilibrium = True
            
            # Check if player 1 wants to deviate
            for k in range(strategies_p1):
                if payoff_matrix_p1[k][j] > payoff_matrix_p1[i][j]:
                    is_equilibrium = False
                    break
            
            # Check if player 2 wants to deviate
            if is_equilibrium:
                for k in range(strategies_p2):
                    if payoff_matrix_p2[i][k] > payoff_matrix_p2[i][j]:
                        is_equilibrium = False
                        break
            
            if is_equilibrium:
                equilibria.append((i, j))
    
    return equilibria

# Mathematical concept: No player can improve by unilaterally changing strategy
```

## Summary

These mathematical concepts form the foundation of efficient algorithms and data structures. Understanding them helps you:

1. **Analyze complexity** - Know why one algorithm is better than another
2. **Design better solutions** - Use mathematical properties to optimize
3. **Solve complex problems** - Break down problems using mathematical techniques
4. **Debug effectively** - Understand the mathematical invariants your code should maintain
5. **Scale solutions** - Predict how algorithms behave with larger inputs

The key is to see these not as abstract math, but as practical tools that directly improve your coding and problem-solving abilities.

I'll provide a comprehensive collection of mathematical operations and tricks commonly used in coding and DSA:I've created a comprehensive collection of mathematical operations and tricks that are essential for coding and DSA! This covers:

**Key Operations You Asked About:**
- `x //= 10` (remove last digit)
- `x % 10` (get last digit) 
- `x & 1` (check odd/even)
- `x ^ y` (XOR operations)
- `x << 1` (multiply by 2)
- `x >> 1` (divide by 2)

**And Many More Including:**
- **Digit manipulation** - reversing numbers, palindrome checking, digit sums
- **Bitwise tricks** - power of 2 checks, bit isolation, XOR magic
- **Modular arithmetic** - fast exponentiation, modular inverse
- **Number theory** - GCD, LCM, prime operations, factorization
- **Geometric operations** - distance calculations, coordinate transformations
- **Combinatorics** - permutations, combinations, probability
- **Advanced patterns** - sliding window, two pointers, binary search applications

**Most Critical Patterns to Master:**
1. `x % 10` and `x //= 10` for digit extraction
2. XOR operations for finding unique elements
3. Bitwise operations for efficient calculations
4. Modular arithmetic for large number handling
5. GCD/LCM for fraction and ratio problems

These operations appear constantly in competitive programming, technical interviews, and real-world problem solving. Would you like me to elaborate on any specific category or provide more examples for particular operations?

# Essential Mathematical Operations & Tricks for Coding

## 1. Number Manipulation Operations

### Basic Digit Operations
```python
# Extract digits from a number
def extract_digits(x):
    digits = []
    while x > 0:
        digit = x % 10    # Get last digit
        digits.append(digit)
        x //= 10          # Remove last digit
    return digits[::-1]   # Reverse to get correct order

# Example: 12345 → [1, 2, 3, 4, 5]

# Count digits in a number
def count_digits(x):
    count = 0
    while x > 0:
        count += 1
        x //= 10
    return count

# Alternative: count = len(str(x)) or count = math.floor(math.log10(x)) + 1

# Reverse a number
def reverse_number(x):
    result = 0
    while x > 0:
        result = result * 10 + x % 10  # Build reversed number
        x //= 10
    return result

# Example: 12345 → 54321
```

### Advanced Digit Manipulations
```python
# Check if number is palindrome
def is_palindrome(x):
    if x < 0:
        return False
    
    original = x
    reversed_num = 0
    while x > 0:
        reversed_num = reversed_num * 10 + x % 10
        x //= 10
    
    return original == reversed_num

# Sum of digits
def sum_of_digits(x):
    total = 0
    while x > 0:
        total += x % 10
        x //= 10
    return total

# Product of digits
def product_of_digits(x):
    product = 1
    while x > 0:
        product *= x % 10
        x //= 10
    return product

# Digital root (keep summing digits until single digit)
def digital_root(x):
    while x >= 10:
        x = sum_of_digits(x)
    return x

# Mathematical formula: digital_root(x) = 1 + (x-1) % 9 if x > 0 else 0
```

### Number Base Conversions
```python
# Convert to different bases
def to_base(num, base):
    if num == 0:
        return "0"
    
    digits = []
    while num > 0:
        digits.append(str(num % base))
        num //= base
    return ''.join(digits[::-1])

# Binary operations
def to_binary(x):
    result = ""
    while x > 0:
        result = str(x % 2) + result
        x //= 2
    return result or "0"

# Count set bits (1s) in binary
def count_set_bits(x):
    count = 0
    while x:
        count += x & 1  # Check if last bit is 1
        x >>= 1         # Right shift by 1
    return count

# Alternative: bin(x).count('1')
```

## 2. Bitwise Operations & Tricks

### Basic Bitwise Operations
```python
# Power of 2 operations
def is_power_of_2(x):
    return x > 0 and (x & (x - 1)) == 0

def next_power_of_2(x):
    x -= 1
    x |= x >> 1
    x |= x >> 2
    x |= x >> 4
    x |= x >> 8
    x |= x >> 16
    return x + 1

# Find position of rightmost set bit
def rightmost_set_bit_position(x):
    return (x & -x).bit_length() - 1

# Turn off rightmost set bit
def turn_off_rightmost_set_bit(x):
    return x & (x - 1)

# Isolate rightmost set bit
def isolate_rightmost_set_bit(x):
    return x & -x
```

### XOR Magic
```python
# Swap two numbers without temporary variable
def swap(a, b):
    a ^= b
    b ^= a
    a ^= b
    return a, b

# Find unique element in array where all others appear twice
def find_unique(arr):
    result = 0
    for num in arr:
        result ^= num
    return result

# Find two unique elements where all others appear twice
def find_two_unique(arr):
    xor_all = 0
    for num in arr:
        xor_all ^= num
    
    # Find rightmost set bit in xor_all
    rightmost_bit = xor_all & -xor_all
    
    num1 = num2 = 0
    for num in arr:
        if num & rightmost_bit:
            num1 ^= num
        else:
            num2 ^= num
    
    return num1, num2

# Check if two numbers have opposite signs
def opposite_signs(x, y):
    return (x ^ y) < 0
```

### Bit Manipulation Patterns
```python
# Set, clear, toggle, check specific bits
def set_bit(x, pos):
    return x | (1 << pos)

def clear_bit(x, pos):
    return x & ~(1 << pos)

def toggle_bit(x, pos):
    return x ^ (1 << pos)

def check_bit(x, pos):
    return bool(x & (1 << pos))

# Count trailing zeros
def count_trailing_zeros(x):
    if x == 0:
        return 32  # or 64 for 64-bit
    count = 0
    while (x & 1) == 0:
        x >>= 1
        count += 1
    return count

# Reverse bits in a number
def reverse_bits(x):
    result = 0
    for i in range(32):  # Assuming 32-bit integer
        if x & (1 << i):
            result |= (1 << (31 - i))
    return result
```

## 3. Modular Arithmetic

### Basic Modular Operations
```python
# Fast exponentiation with modulo
def power_mod(base, exp, mod):
    result = 1
    base %= mod
    while exp > 0:
        if exp & 1:  # If exp is odd
            result = (result * base) % mod
        exp >>= 1    # exp //= 2
        base = (base * base) % mod
    return result

# Modular inverse using Extended Euclidean Algorithm
def extended_gcd(a, b):
    if a == 0:
        return b, 0, 1
    gcd, x1, y1 = extended_gcd(b % a, a)
    x = y1 - (b // a) * x1
    y = x1
    return gcd, x, y

def mod_inverse(a, m):
    gcd, x, y = extended_gcd(a, m)
    if gcd != 1:
        return None  # Modular inverse doesn't exist
    return (x % m + m) % m

# Modular arithmetic properties
def mod_add(a, b, mod):
    return ((a % mod) + (b % mod)) % mod

def mod_subtract(a, b, mod):
    return ((a % mod) - (b % mod) + mod) % mod

def mod_multiply(a, b, mod):
    return ((a % mod) * (b % mod)) % mod
```

### Advanced Modular Techniques
```python
# Chinese Remainder Theorem
def chinese_remainder_theorem(remainders, moduli):
    total = 0
    prod = 1
    for m in moduli:
        prod *= m
    
    for r, m in zip(remainders, moduli):
        p = prod // m
        total += r * mod_inverse(p, m) * p
    
    return total % prod

# Check if number is prime using modular arithmetic
def is_prime(n):
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    
    # Check odd divisors up to √n
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True

# Fermat's Little Theorem: a^(p-1) ≡ 1 (mod p) if p is prime
def fermat_primality_test(n, k=5):
    if n < 2:
        return False
    
    import random
    for _ in range(k):
        a = random.randint(2, n - 1)
        if power_mod(a, n - 1, n) != 1:
            return False
    return True
```

## 4. Mathematical Sequences & Patterns

### Fibonacci and Related Sequences
```python
# Fibonacci with different approaches
def fibonacci_iterative(n):
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

# Matrix exponentiation for Fibonacci
def matrix_multiply(A, B):
    return [[A[0][0]*B[0][0] + A[0][1]*B[1][0], A[0][0]*B[0][1] + A[0][1]*B[1][1]],
            [A[1][0]*B[0][0] + A[1][1]*B[1][0], A[1][0]*B[0][1] + A[1][1]*B[1][1]]]

def matrix_power(matrix, n):
    if n == 1:
        return matrix
    if n % 2 == 0:
        half = matrix_power(matrix, n // 2)
        return matrix_multiply(half, half)
    else:
        return matrix_multiply(matrix, matrix_power(matrix, n - 1))

def fibonacci_matrix(n):
    if n == 0:
        return 0
    base = [[1, 1], [1, 0]]
    result = matrix_power(base, n)
    return result[0][1]

# Tribonacci sequence
def tribonacci(n):
    if n == 0:
        return 0
    elif n <= 2:
        return 1
    
    a, b, c = 0, 1, 1
    for _ in range(3, n + 1):
        a, b, c = b, c, a + b + c
    return c
```

### Mathematical Series
```python
# Sum of arithmetic progression: a + (a+d) + (a+2d) + ... + (a+(n-1)d)
def arithmetic_sum(a, d, n):
    return n * (2 * a + (n - 1) * d) // 2

# Sum of geometric progression: a + ar + ar² + ... + ar^(n-1)
def geometric_sum(a, r, n):
    if r == 1:
        return a * n
    return a * (1 - r**n) // (1 - r)

# Sum of squares: 1² + 2² + 3² + ... + n²
def sum_of_squares(n):
    return n * (n + 1) * (2 * n + 1) // 6

# Sum of cubes: 1³ + 2³ + 3³ + ... + n³
def sum_of_cubes(n):
    return (n * (n + 1) // 2) ** 2

# Catalan numbers: C(n) = (2n)! / ((n+1)! * n!)
def catalan_number(n):
    if n <= 1:
        return 1
    
    catalan = [0] * (n + 1)
    catalan[0], catalan[1] = 1, 1
    
    for i in range(2, n + 1):
        for j in range(i):
            catalan[i] += catalan[j] * catalan[i - 1 - j]
    
    return catalan[n]
```

## 5. GCD, LCM, and Number Theory

### Greatest Common Divisor (GCD)
```python
# Euclidean algorithm
def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

# GCD of multiple numbers
def gcd_multiple(numbers):
    result = numbers[0]
    for i in range(1, len(numbers)):
        result = gcd(result, numbers[i])
    return result

# Extended Euclidean algorithm
def extended_gcd(a, b):
    if a == 0:
        return b, 0, 1
    gcd, x1, y1 = extended_gcd(b % a, a)
    x = y1 - (b // a) * x1
    y = x1
    return gcd, x, y

# Least Common Multiple (LCM)
def lcm(a, b):
    return abs(a * b) // gcd(a, b)

def lcm_multiple(numbers):
    result = numbers[0]
    for i in range(1, len(numbers)):
        result = lcm(result, numbers[i])
    return result
```

### Prime Number Operations
```python
# Sieve of Eratosthenes
def sieve_of_eratosthenes(n):
    is_prime = [True] * (n + 1)
    is_prime[0] = is_prime[1] = False
    
    for i in range(2, int(n**0.5) + 1):
        if is_prime[i]:
            for j in range(i * i, n + 1, i):
                is_prime[j] = False
    
    return [i for i in range(2, n + 1) if is_prime[i]]

# Prime factorization
def prime_factors(n):
    factors = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return factors

# Count divisors
def count_divisors(n):
    count = 0
    i = 1
    while i * i <= n:
        if n % i == 0:
            count += 1 if i * i == n else 2
        i += 1
    return count

# Sum of divisors
def sum_of_divisors(n):
    total = 0
    i = 1
    while i * i <= n:
        if n % i == 0:
            total += i
            if i * i != n:
                total += n // i
        i += 1
    return total
```

## 6. Coordinate Geometry & 2D Operations

### Point and Line Operations
```python
# Distance between two points
def distance(p1, p2):
    return ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)**0.5

# Manhattan distance
def manhattan_distance(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

# Check if three points are collinear
def are_collinear(p1, p2, p3):
    # Using cross product: (p2-p1) × (p3-p1) = 0
    return (p2[1] - p1[1]) * (p3[0] - p1[0]) == (p3[1] - p1[1]) * (p2[0] - p1[0])

# Area of triangle using coordinates
def triangle_area(p1, p2, p3):
    return abs((p1[0]*(p2[1] - p3[1]) + p2[0]*(p3[1] - p1[1]) + p3[0]*(p1[1] - p2[1])) / 2)

# Check if point is inside triangle
def point_in_triangle(p, a, b, c):
    area_abc = triangle_area(a, b, c)
    area_pab = triangle_area(p, a, b)
    area_pbc = triangle_area(p, b, c)
    area_pca = triangle_area(p, c, a)
    
    return abs(area_abc - (area_pab + area_pbc + area_pca)) < 1e-10

# Rotate point around origin
def rotate_point(point, angle):
    import math
    cos_angle = math.cos(angle)
    sin_angle = math.sin(angle)
    x, y = point
    return (x * cos_angle - y * sin_angle, x * sin_angle + y * cos_angle)
```

### Grid and Matrix Operations
```python
# 8-directional movement in grid
directions_8 = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]

# 4-directional movement in grid
directions_4 = [(-1,0), (1,0), (0,-1), (0,1)]

def is_valid_cell(row, col, rows, cols):
    return 0 <= row < rows and 0 <= col < cols

# Convert 2D coordinates to 1D index
def coord_to_index(row, col, cols):
    return row * cols + col

# Convert 1D index to 2D coordinates
def index_to_coord(index, cols):
    return index // cols, index % cols

# Spiral matrix traversal
def spiral_order(matrix):
    if not matrix:
        return []
    
    rows, cols = len(matrix), len(matrix[0])
    result = []
    top, bottom, left, right = 0, rows - 1, 0, cols - 1
    
    while top <= bottom and left <= right:
        # Right
        for col in range(left, right + 1):
            result.append(matrix[top][col])
        top += 1
        
        # Down
        for row in range(top, bottom + 1):
            result.append(matrix[row][right])
        right -= 1
        
        # Left
        if top <= bottom:
            for col in range(right, left - 1, -1):
                result.append(matrix[bottom][col])
            bottom -= 1
        
        # Up
        if left <= right:
            for row in range(bottom, top - 1, -1):
                result.append(matrix[row][left])
            left += 1
    
    return result
```

## 7. Combinatorics & Probability

### Factorials and Combinations
```python
# Factorial with memoization
factorial_cache = {0: 1, 1: 1}

def factorial(n):
    if n in factorial_cache:
        return factorial_cache[n]
    factorial_cache[n] = n * factorial(n - 1)
    return factorial_cache[n]

# Combinations using Pascal's triangle property
def combination(n, r):
    if r > n - r:
        r = n - r  # Take advantage of symmetry
    
    result = 1
    for i in range(r):
        result = result * (n - i) // (i + 1)
    return result

# Permutations
def permutation(n, r):
    result = 1
    for i in range(n, n - r, -1):
        result *= i
    return result

# Derangements (permutations with no fixed points)
def derangements(n):
    if n == 0:
        return 1
    if n == 1:
        return 0
    
    dp = [0] * (n + 1)
    dp[0], dp[1] = 1, 0
    
    for i in range(2, n + 1):
        dp[i] = (i - 1) * (dp[i - 1] + dp[i - 2])
    
    return dp[n]
```

### Probability Calculations
```python
# Binomial coefficient
def binomial_coefficient(n, k):
    if k > n or k < 0:
        return 0
    if k == 0 or k == n:
        return 1
    
    # Use multiplicative formula
    result = 1
    for i in range(min(k, n - k)):
        result = result * (n - i) // (i + 1)
    return result

# Probability of getting exactly k successes in n trials
def binomial_probability(n, k, p):
    return binomial_coefficient(n, k) * (p ** k) * ((1 - p) ** (n - k))

# Expected value and variance
def expected_value(values, probabilities):
    return sum(v * p for v, p in zip(values, probabilities))

def variance(values, probabilities):
    mean = expected_value(values, probabilities)
    return sum(p * (v - mean) ** 2 for v, p in zip(values, probabilities))
```

## 8. Advanced Mathematical Tricks

### Fast Multiplication and Division
```python
# Multiply by powers of 2 using bit shifts
def multiply_by_power_of_2(x, power):
    return x << power  # x * 2^power

def divide_by_power_of_2(x, power):
    return x >> power  # x // 2^power

# Check if number is divisible by 3
def divisible_by_3(x):
    # A number is divisible by 3 if sum of its digits is divisible by 3
    digit_sum = sum_of_digits(abs(x))
    return digit_sum % 3 == 0

# Check if number is divisible by 9
def divisible_by_9(x):
    # A number is divisible by 9 if sum of its digits is divisible by 9
    digit_sum = sum_of_digits(abs(x))
    return digit_sum % 9 == 0

# Fast integer square root
def integer_sqrt(x):
    if x < 2:
        return x
    
    left, right = 1, x // 2 + 1
    while left <= right:
        mid = (left + right) // 2
        square = mid * mid
        if square == x:
            return mid
        elif square < x:
            left = mid + 1
            result = mid
        else:
            right = mid - 1
    return result
```

### Number Pattern Recognition
```python
# Check if number is perfect square
def is_perfect_square(x):
    if x < 0:
        return False
    root = int(x ** 0.5)
    return root * root == x

# Check if number is perfect cube
def is_perfect_cube(x):
    if x < 0:
        cube_root = -int((-x) ** (1/3))
    else:
        cube_root = int(x ** (1/3))
    return cube_root ** 3 == x

# Find next palindrome
def next_palindrome(x):
    s = str(x + 1)
    n = len(s)
    
    # Try to make current number palindrome
    left = s[:n//2]
    middle = s[n//2] if n % 2 == 1 else ""
    right = left[::-1]
    
    candidate = int(left + middle + right)
    
    if candidate > x:
        return candidate
    
    # Increment middle part
    if middle:
        if middle == '9':
            return next_palindrome(int('1' + '0' * (n-1)))
        middle = str(int(middle) + 1)
        return int(left + middle + right)
    else:
        # Increment left part
        left_num = int(left) + 1
        if len(str(left_num)) > len(left):
            return int('1' + '0' * (n-1) + '1')
        left = str(left_num).zfill(len(left))
        right = left[::-1]
        return int(left + right)

# Armstrong number (narcissistic number)
def is_armstrong_number(x):
    digits = [int(d) for d in str(x)]
    n = len(digits)
    return x == sum(d ** n for d in digits)
```

### Mathematical Constants and Approximations
```python
import math

# Calculate π using various methods
def calculate_pi_leibniz(iterations):
    pi_approx = 0
    for i in range(iterations):
        pi_approx += ((-1) ** i) / (2 * i + 1)
    return 4 * pi_approx

def calculate_pi_monte_carlo(samples):
    import random
    inside_circle = 0
    for _ in range(samples):
        x, y = random.random(), random.random()
        if x*x + y*y <= 1:
            inside_circle += 1
    return 4 * inside_circle / samples

# Golden ratio calculations
def golden_ratio_fibonacci(n):
    # φ ≈ F(n+1) / F(n) for large n
    fib_n = fibonacci_iterative(n)
    fib_n_plus_1 = fibonacci_iterative(n + 1)
    return fib_n_plus_1 / fib_n if fib_n != 0 else 0

def golden_ratio_exact():
    return (1 + math.sqrt(5)) / 2

# Euler's number approximation
def calculate_e(iterations):
    e_approx = 0
    for i in range(iterations):
        e_approx += 1 / factorial(i)
    return e_approx
```

## 9. Common Coding Patterns with Math

### Sliding Window with Math
```python
# Maximum sum subarray of size k
def max_sum_subarray(arr, k):
    if len(arr) < k:
        return 0
    
    # Calculate sum of first window
    window_sum = sum(arr[:k])
    max_sum = window_sum
    
    # Slide the window
    for i in range(len(arr) - k):
        window_sum = window_sum - arr[i] + arr[i + k]
        max_sum = max(max_sum, window_sum)
    
    return max_sum

# Count subarrays with sum equal to k
def subarray_sum_equals_k(arr, k):
    count = 0
    prefix_sum = 0
    sum_count = {0: 1}  # Handle empty prefix
    
    for num in arr:
        prefix_sum += num
        if prefix_sum - k in sum_count:
            count += sum_count[prefix_sum - k]
        sum_count[prefix_sum] = sum_count.get(prefix_sum, 0) + 1
    
    return count
```

### Two Pointers with Math
```python
# Two sum in sorted array
def two_sum_sorted(arr, target):
    left, right = 0, len(arr) - 1
    
    while left < right:
        current_sum = arr[left] + arr[right]
        if current_sum == target:
            return [left, right]
        elif current_sum < target:
            left += 1
        else:
            right -= 1
    
    return []

# Three sum closest to target
def three_sum_closest(arr, target):
    arr.sort()
    n = len(arr)
    closest_sum = float('inf')
    
    for i in range(n - 2):
        left, right = i + 1, n - 1
        
        while left < right:
            current_sum = arr[i] + arr[left] + arr[right]
            
            if abs(current_sum - target) < abs(closest_sum - target):
                closest_sum = current_sum
            
            if current_sum < target:
                left += 1
            else:
                right -= 1
    
    return closest_sum
```

### Binary Search with Math
```python
# Square root using binary search
def sqrt_binary_search(x):
    if x < 2:
        return x
    
    left, right = 1, x // 2
    while left <= right:
        mid = (left + right) // 2
        square = mid * mid
        
        if square == x:
            return mid
        elif square < x:
            left = mid + 1
            result = mid
        else:
            right = mid - 1
    
    return result

# Find peak element
def find_peak_element(arr):
    left, right = 0, len(arr) - 1
    
    while left < right:
        mid = (left + right) // 2
        
        if arr[mid] > arr[mid + 1]:
            right = mid
        else:
            left = mid + 1
    
    return left
```

## Summary of Key Patterns

### Most Important Operations:
1. **`x % 10`** - Get last digit
2. **`x // 10`** - Remove last digit  
3. **`x & 1`** - Check if odd/even
4. **`x ^ y`** - XOR for finding unique elements
5. **`x & (x-1)`** - Turn off rightmost set bit
6. **`x << 1`** - Multiply by 2
7. **`x >> 1`** - Divide by 2
8. **`x & -x`** - Isolate rightmost set bit

### Essential Formulas:
- **Sum 1 to n**: `n * (n + 1) // 2`
- **Sum of squares**: `n * (n + 1) * (2*n + 1) // 6`  
- **GCD**: Use Euclidean algorithm
- **Power with mod**: Fast exponentiation
- **Combinations**: `n! / (r! * (n-r)!)`

These operations and patterns form the mathematical foundation for solving most coding problems efficiently!