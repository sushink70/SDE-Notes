# Complete DSA Problem-Solving Guide: Tricks, Tips & Patterns

## 🎯 Core Problem-Solving Framework

### 1. **UMPIRE Method** (Systematic Approach)
- **U**nderstand: What exactly is being asked?
- **M**atch: What pattern/technique fits this problem?
- **P**lan: Outline your approach before coding
- **I**mplement: Write clean, readable code
- **R**eview: Check edge cases and optimize
- **E**valuate: Analyze time/space complexity

### 2. **Pattern Recognition** (Most Important Skill)
Before coding, identify which pattern the problem follows:
- Two Pointers
- Sliding Window
- Fast & Slow Pointers
- Merge Intervals
- Cyclic Sort
- In-place Reversal of LinkedList
- Tree/Graph Traversal
- Dynamic Programming
- Backtracking

---

Here's a comprehensive list of pattern recognition techniques and concepts in Data Structures and Algorithms (DSA):

## Array Patterns
**Two Pointers**: Used for problems involving pairs, triplets, or comparing elements from different positions. Common in array searching, palindrome checking, and removing duplicates.

**Sliding Window**: Maintains a window of elements and slides it across the array. Useful for subarray problems, finding maximum/minimum in subarrays, and string matching.

**Prefix Sum**: Precomputes cumulative sums to answer range queries efficiently. Applied in range sum queries and subarray sum problems.

**Kadane's Algorithm**: Finds maximum sum subarray using dynamic programming principles.

**Dutch National Flag**: Partitions array into three sections, commonly used in sorting problems with three distinct values.

## String Patterns
**KMP (Knuth-Morris-Pratt)**: Pattern matching algorithm that avoids redundant comparisons using failure function.

**Rabin-Karp**: Uses rolling hash for pattern matching, effective for multiple pattern searches.

**Z Algorithm**: Finds all occurrences of pattern in text using Z-array preprocessing.

**Manacher's Algorithm**: Finds all palindromic substrings in linear time.

**Trie Operations**: Prefix tree for efficient string storage and retrieval, autocomplete features.

## Searching Patterns
**Binary Search**: Divide and conquer approach for sorted arrays, includes variations like finding first/last occurrence.

**Ternary Search**: Finds maximum/minimum in unimodal functions by dividing search space into three parts.

**Exponential Search**: Combines binary search with unbounded search for infinite arrays.

## Sorting Patterns
**Merge Sort Pattern**: Divide and conquer with merge operation, stable sorting with O(n log n) complexity.

**Quick Sort Pattern**: Partition-based sorting with pivot selection strategies.

**Heap Sort Pattern**: Uses heap data structure for in-place sorting.

**Counting Sort Pattern**: Non-comparison sorting for integers in limited range.

## Tree Patterns
**Tree Traversals**: Inorder, preorder, postorder, and level-order traversal patterns.

**Binary Search Tree Operations**: Search, insert, delete operations maintaining BST property.

**Tree DP**: Dynamic programming on trees for problems like tree diameter, maximum path sum.

**Lowest Common Ancestor (LCA)**: Various algorithms including binary lifting and sparse table approaches.

**Tree Serialization/Deserialization**: Converting tree to string representation and back.

## Graph Patterns
**Depth-First Search (DFS)**: Explores graph by going as deep as possible, used for connectivity, cycle detection, topological sorting.

**Breadth-First Search (BFS)**: Level-by-level exploration, shortest path in unweighted graphs, level-order processing.

**Dijkstra's Algorithm**: Shortest path in weighted graphs with non-negative weights.

**Bellman-Ford Algorithm**: Shortest path allowing negative weights, detects negative cycles.

**Floyd-Warshall Algorithm**: All-pairs shortest path using dynamic programming.

**Topological Sorting**: Linear ordering of vertices in directed acyclic graph.

**Union-Find (Disjoint Set)**: Efficiently handles dynamic connectivity queries and cycle detection.

**Minimum Spanning Tree**: Kruskal's and Prim's algorithms for finding MST.

## Dynamic Programming Patterns
**Linear DP**: Problems with optimal substructure in linear arrangement (Fibonacci, climbing stairs).

**Grid DP**: 2D problems like unique paths, minimum path sum in grids.

**Knapsack Variants**: 0/1 knapsack, unbounded knapsack, multiple knapsack problems.

**Longest Common Subsequence (LCS)**: Comparing sequences for common patterns.

**Longest Increasing Subsequence (LIS)**: Finding increasing subsequences with various optimizations.

**Edit Distance**: Minimum operations to transform one string to another.

**Palindrome DP**: Problems involving palindromic subsequences and substrings.

**Interval DP**: Problems on intervals like matrix chain multiplication.

## Backtracking Patterns
**N-Queens**: Placing queens on chessboard without conflicts.

**Sudoku Solver**: Constraint satisfaction with backtracking.

**Permutations and Combinations**: Generating all possible arrangements.

**Subset Generation**: Finding all subsets of a given set.

**Graph Coloring**: Assigning colors to vertices with constraints.

## Greedy Patterns
**Activity Selection**: Selecting maximum non-overlapping activities.

**Huffman Coding**: Optimal prefix-free coding using greedy approach.

**Fractional Knapsack**: Maximizing value with fractional items allowed.

**Job Scheduling**: Optimizing job sequences for various criteria.

## Mathematical Patterns
**Prime Number Algorithms**: Sieve of Eratosthenes, primality testing.

**Greatest Common Divisor (GCD)**: Euclidean algorithm and extended Euclidean algorithm.

**Fast Exponentiation**: Computing large powers efficiently using binary exponentiation.

**Modular Arithmetic**: Operations under modulo for large number computations.

**Combinatorics**: Calculating combinations, permutations, and binomial coefficients.

## Advanced Patterns
**Segment Trees**: Range query and update operations in logarithmic time.

**Binary Indexed Trees (Fenwick Trees)**: Efficient prefix sum queries and updates.

**Heavy-Light Decomposition**: Tree decomposition for efficient path queries.

**Mo's Algorithm**: Offline query processing for range queries.

**Sqrt Decomposition**: Dividing array into blocks for efficient range operations.

These patterns form the foundation for solving complex algorithmic problems and are essential for technical interviews and competitive programming. Understanding when and how to apply each pattern is crucial for effective problem-solving in DSA.

I've created a comprehensive guide covering all major Pattern Recognition techniques in Data Structures and Algorithms. This guide includes:

## Key Pattern Categories Covered:

1. **String Pattern Matching** - Naive, KMP, and Rabin-Karp algorithms
2. **Array Patterns** - Two pointers, sliding window, fast-slow pointers
3. **Tree Patterns** - Various traversals and path-finding techniques
4. **Dynamic Programming** - Knapsack, Fibonacci, and LCS patterns
5. **Graph Patterns** - DFS and BFS implementations
6. **Backtracking** - Permutations, combinations, and constraint satisfaction
7. **Greedy Algorithms** - Activity selection and optimization problems
8. **Divide and Conquer** - Sorting and searching algorithms
9. **Heap Patterns** - Priority queue operations and median finding
10. **Trie (Prefix Tree)** - String processing and autocomplete
11. **Union-Find** - Disjoint set operations for connectivity problems
12. **Bit Manipulation** - Efficient operations using bitwise operators
13. **Mathematical Patterns** - Number theory and computational mathematics

Each section includes:
- **Complete implementations** with detailed code
- **Time and space complexity analysis**
- **Practical examples** and use cases
- **Common interview problems** that use each pattern

This guide serves as a comprehensive reference for understanding and implementing the most important algorithmic patterns that appear frequently in coding interviews and competitive programming. The patterns are organized logically and include working code that you can run and modify for practice.

# Pattern Recognition in Data Structures and Algorithms

## 1. String Pattern Matching

### 1.1 Naive Pattern Matching
```python
def naive_pattern_search(text, pattern):
    """
    Time Complexity: O(n*m) where n = len(text), m = len(pattern)
    Space Complexity: O(1)
    """
    n = len(text)
    m = len(pattern)
    results = []
    
    for i in range(n - m + 1):
        j = 0
        while j < m and text[i + j] == pattern[j]:
            j += 1
        if j == m:
            results.append(i)
    
    return results

# Example usage
text = "ABABDABACDABABCABCABCABCABC"
pattern = "ABABCAB"
print(naive_pattern_search(text, pattern))  # Output: [15]
```

### 1.2 KMP (Knuth-Morris-Pratt) Algorithm
```python
def compute_lps(pattern):
    """Compute Longest Proper Prefix which is also Suffix array"""
    m = len(pattern)
    lps = [0] * m
    length = 0
    i = 1
    
    while i < m:
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        else:
            if length != 0:
                length = lps[length - 1]
            else:
                lps[i] = 0
                i += 1
    return lps

def kmp_search(text, pattern):
    """
    Time Complexity: O(n + m)
    Space Complexity: O(m)
    """
    n = len(text)
    m = len(pattern)
    
    lps = compute_lps(pattern)
    results = []
    
    i = j = 0
    while i < n:
        if pattern[j] == text[i]:
            i += 1
            j += 1
        
        if j == m:
            results.append(i - j)
            j = lps[j - 1]
        elif i < n and pattern[j] != text[i]:
            if j != 0:
                j = lps[j - 1]
            else:
                i += 1
    
    return results

# Example usage
text = "ABABDABACDABABCABCABCABCABC"
pattern = "ABABCAB"
print(kmp_search(text, pattern))  # Output: [15]
```

### 1.3 Rabin-Karp Algorithm
```python
def rabin_karp_search(text, pattern, prime=101):
    """
    Time Complexity: O(n + m) average, O(n*m) worst case
    Space Complexity: O(1)
    """
    n = len(text)
    m = len(pattern)
    d = 256  # Number of characters in alphabet
    
    pattern_hash = 0
    text_hash = 0
    h = 1
    results = []
    
    # Calculate h = pow(d, m-1) % prime
    for i in range(m - 1):
        h = (h * d) % prime
    
    # Calculate hash for pattern and first window of text
    for i in range(m):
        pattern_hash = (d * pattern_hash + ord(pattern[i])) % prime
        text_hash = (d * text_hash + ord(text[i])) % prime
    
    # Slide the pattern over text
    for i in range(n - m + 1):
        if pattern_hash == text_hash:
            # Check character by character
            if text[i:i + m] == pattern:
                results.append(i)
        
        # Calculate hash for next window
        if i < n - m:
            text_hash = (d * (text_hash - ord(text[i]) * h) + ord(text[i + m])) % prime
            if text_hash < 0:
                text_hash += prime
    
    return results

# Example usage
text = "GEEKS FOR GEEKS"
pattern = "GEEK"
print(rabin_karp_search(text, pattern))  # Output: [0, 10]
```

## 2. Array Pattern Recognition

### 2.1 Two Pointers Pattern
```python
def two_sum_sorted(arr, target):
    """
    Find two numbers that sum to target in sorted array
    Time Complexity: O(n)
    Space Complexity: O(1)
    """
    left, right = 0, len(arr) - 1
    
    while left < right:
        current_sum = arr[left] + arr[right]
        if current_sum == target:
            return [left, right]
        elif current_sum < target:
            left += 1
        else:
            right -= 1
    
    return [-1, -1]

def remove_duplicates(arr):
    """
    Remove duplicates from sorted array in-place
    Time Complexity: O(n)
    Space Complexity: O(1)
    """
    if not arr:
        return 0
    
    write_index = 1
    for i in range(1, len(arr)):
        if arr[i] != arr[i - 1]:
            arr[write_index] = arr[i]
            write_index += 1
    
    return write_index

# Example usage
arr = [1, 2, 3, 4, 6]
print(two_sum_sorted(arr, 6))  # Output: [1, 3]

arr2 = [1, 1, 2, 2, 3, 4, 4, 5]
length = remove_duplicates(arr2)
print(arr2[:length])  # Output: [1, 2, 3, 4, 5]
```

### 2.2 Sliding Window Pattern
```python
def max_sum_subarray_k(arr, k):
    """
    Maximum sum of subarray of size k
    Time Complexity: O(n)
    Space Complexity: O(1)
    """
    if len(arr) < k:
        return -1
    
    # Calculate sum of first window
    window_sum = sum(arr[:k])
    max_sum = window_sum
    
    # Slide the window
    for i in range(k, len(arr)):
        window_sum = window_sum - arr[i - k] + arr[i]
        max_sum = max(max_sum, window_sum)
    
    return max_sum

def longest_substring_k_distinct(s, k):
    """
    Longest substring with at most k distinct characters
    Time Complexity: O(n)
    Space Complexity: O(k)
    """
    if k == 0:
        return 0
    
    char_count = {}
    left = 0
    max_length = 0
    
    for right in range(len(s)):
        # Add character to window
        char_count[s[right]] = char_count.get(s[right], 0) + 1
        
        # Shrink window if more than k distinct characters
        while len(char_count) > k:
            char_count[s[left]] -= 1
            if char_count[s[left]] == 0:
                del char_count[s[left]]
            left += 1
        
        max_length = max(max_length, right - left + 1)
    
    return max_length

# Example usage
arr = [1, 4, 2, 10, 23, 3, 1, 0, 20]
print(max_sum_subarray_k(arr, 4))  # Output: 39

s = "araaci"
print(longest_substring_k_distinct(s, 2))  # Output: 4
```

### 2.3 Fast and Slow Pointers (Floyd's Algorithm)
```python
class ListNode:
    def __init__(self, val=0):
        self.val = val
        self.next = None

def has_cycle(head):
    """
    Detect cycle in linked list
    Time Complexity: O(n)
    Space Complexity: O(1)
    """
    if not head or not head.next:
        return False
    
    slow = fast = head
    
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        
        if slow == fast:
            return True
    
    return False

def find_cycle_start(head):
    """
    Find the start of cycle in linked list
    Time Complexity: O(n)
    Space Complexity: O(1)
    """
    if not head or not head.next:
        return None
    
    # Phase 1: Detect cycle
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow == fast:
            break
    else:
        return None  # No cycle
    
    # Phase 2: Find cycle start
    slow = head
    while slow != fast:
        slow = slow.next
        fast = fast.next
    
    return slow

def find_middle(head):
    """
    Find middle of linked list
    Time Complexity: O(n)
    Space Complexity: O(1)
    """
    slow = fast = head
    
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
    
    return slow
```

## 3. Tree Pattern Recognition

### 3.1 Tree Traversal Patterns
```python
class TreeNode:
    def __init__(self, val=0):
        self.val = val
        self.left = None
        self.right = None

def inorder_traversal(root):
    """In-order traversal (Left, Root, Right)"""
    result = []
    
    def inorder(node):
        if node:
            inorder(node.left)
            result.append(node.val)
            inorder(node.right)
    
    inorder(root)
    return result

def preorder_traversal(root):
    """Pre-order traversal (Root, Left, Right)"""
    result = []
    
    def preorder(node):
        if node:
            result.append(node.val)
            preorder(node.left)
            preorder(node.right)
    
    preorder(root)
    return result

def level_order_traversal(root):
    """Level-order traversal (BFS)"""
    if not root:
        return []
    
    from collections import deque
    queue = deque([root])
    result = []
    
    while queue:
        level_size = len(queue)
        level = []
        
        for _ in range(level_size):
            node = queue.popleft()
            level.append(node.val)
            
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        
        result.append(level)
    
    return result
```

### 3.2 Tree Path Patterns
```python
def has_path_sum(root, target_sum):
    """
    Check if tree has root-to-leaf path with given sum
    Time Complexity: O(n)
    Space Complexity: O(h) where h is height
    """
    if not root:
        return False
    
    if not root.left and not root.right:  # Leaf node
        return root.val == target_sum
    
    remaining_sum = target_sum - root.val
    return (has_path_sum(root.left, remaining_sum) or 
            has_path_sum(root.right, remaining_sum))

def find_all_paths(root, target_sum):
    """
    Find all root-to-leaf paths with given sum
    Time Complexity: O(n^2) worst case
    Space Complexity: O(n^2) worst case
    """
    all_paths = []
    
    def find_paths_recursive(node, target_sum, current_path):
        if not node:
            return
        
        current_path.append(node.val)
        
        if not node.left and not node.right and node.val == target_sum:
            all_paths.append(current_path[:])  # Make a copy
        else:
            find_paths_recursive(node.left, target_sum - node.val, current_path)
            find_paths_recursive(node.right, target_sum - node.val, current_path)
        
        current_path.pop()  # Backtrack
    
    find_paths_recursive(root, target_sum, [])
    return all_paths

def path_sum_any(root, target_sum):
    """
    Count paths with given sum (not necessarily root-to-leaf)
    Time Complexity: O(n^2) worst case
    Space Complexity: O(n)
    """
    def count_paths_from_node(node, target_sum):
        if not node:
            return 0
        
        count = 0
        if node.val == target_sum:
            count = 1
        
        count += count_paths_from_node(node.left, target_sum - node.val)
        count += count_paths_from_node(node.right, target_sum - node.val)
        
        return count
    
    if not root:
        return 0
    
    # Count paths starting from current node
    paths_from_root = count_paths_from_node(root, target_sum)
    
    # Count paths in left and right subtrees
    paths_from_left = path_sum_any(root.left, target_sum)
    paths_from_right = path_sum_any(root.right, target_sum)
    
    return paths_from_root + paths_from_left + paths_from_right
```

## 4. Dynamic Programming Patterns

### 4.1 0/1 Knapsack Pattern
```python
def knapsack_01(weights, values, capacity):
    """
    0/1 Knapsack Problem
    Time Complexity: O(n * capacity)
    Space Complexity: O(n * capacity)
    """
    n = len(weights)
    dp = [[0 for _ in range(capacity + 1)] for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        for w in range(1, capacity + 1):
            # If current item weight is more than capacity, skip it
            if weights[i-1] > w:
                dp[i][w] = dp[i-1][w]
            else:
                # Take maximum of including or excluding current item
                dp[i][w] = max(
                    values[i-1] + dp[i-1][w - weights[i-1]],  # Include
                    dp[i-1][w]  # Exclude
                )
    
    return dp[n][capacity]

def subset_sum(nums, target):
    """
    Check if subset with given sum exists
    Time Complexity: O(n * target)
    Space Complexity: O(target)
    """
    dp = [False] * (target + 1)
    dp[0] = True  # Empty subset has sum 0
    
    for num in nums:
        for i in range(target, num - 1, -1):
            dp[i] = dp[i] or dp[i - num]
    
    return dp[target]

# Example usage
weights = [1, 3, 4, 5]
values = [1, 4, 5, 7]
capacity = 7
print(knapsack_01(weights, values, capacity))  # Output: 9

nums = [1, 5, 11, 5]
target = 11
print(subset_sum(nums, target))  # Output: True
```

### 4.2 Fibonacci Pattern
```python
def fibonacci(n):
    """
    Calculate nth Fibonacci number
    Time Complexity: O(n)
    Space Complexity: O(1)
    """
    if n <= 1:
        return n
    
    prev2, prev1 = 0, 1
    for i in range(2, n + 1):
        current = prev1 + prev2
        prev2, prev1 = prev1, current
    
    return prev1

def climb_stairs(n):
    """
    Number of ways to climb n stairs (1 or 2 steps at a time)
    Time Complexity: O(n)
    Space Complexity: O(1)
    """
    if n <= 2:
        return n
    
    prev2, prev1 = 1, 2
    for i in range(3, n + 1):
        current = prev1 + prev2
        prev2, prev1 = prev1, current
    
    return prev1

def house_robber(nums):
    """
    Maximum amount that can be robbed (no adjacent houses)
    Time Complexity: O(n)
    Space Complexity: O(1)
    """
    if not nums:
        return 0
    if len(nums) == 1:
        return nums[0]
    
    prev2, prev1 = 0, nums[0]
    for i in range(1, len(nums)):
        current = max(prev1, prev2 + nums[i])
        prev2, prev1 = prev1, current
    
    return prev1

# Example usage
print(fibonacci(10))  # Output: 55
print(climb_stairs(5))  # Output: 8
print(house_robber([2, 7, 9, 3, 1]))  # Output: 12
```

### 4.3 Longest Common Subsequence Pattern
```python
def longest_common_subsequence(text1, text2):
    """
    Length of Longest Common Subsequence
    Time Complexity: O(m * n)
    Space Complexity: O(m * n)
    """
    m, n = len(text1), len(text2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i-1] == text2[j-1]:
                dp[i][j] = 1 + dp[i-1][j-1]
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    return dp[m][n]

def edit_distance(word1, word2):
    """
    Minimum operations to convert word1 to word2
    Time Complexity: O(m * n)
    Space Complexity: O(m * n)
    """
    m, n = len(word1), len(word2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # Initialize base cases
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if word1[i-1] == word2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(
                    dp[i-1][j],    # Delete
                    dp[i][j-1],    # Insert
                    dp[i-1][j-1]   # Replace
                )
    
    return dp[m][n]

# Example usage
print(longest_common_subsequence("abcde", "ace"))  # Output: 3
print(edit_distance("horse", "ros"))  # Output: 3
```

## 5. Graph Pattern Recognition

### 5.1 DFS Pattern
```python
def dfs_iterative(graph, start):
    """
    Depth-First Search (Iterative)
    Time Complexity: O(V + E)
    Space Complexity: O(V)
    """
    visited = set()
    stack = [start]
    result = []
    
    while stack:
        vertex = stack.pop()
        if vertex not in visited:
            visited.add(vertex)
            result.append(vertex)
            
            # Add neighbors to stack (in reverse order for correct traversal)
            for neighbor in reversed(graph[vertex]):
                if neighbor not in visited:
                    stack.append(neighbor)
    
    return result

def dfs_recursive(graph, start, visited=None, result=None):
    """
    Depth-First Search (Recursive)
    Time Complexity: O(V + E)
    Space Complexity: O(V)
    """
    if visited is None:
        visited = set()
    if result is None:
        result = []
    
    visited.add(start)
    result.append(start)
    
    for neighbor in graph[start]:
        if neighbor not in visited:
            dfs_recursive(graph, neighbor, visited, result)
    
    return result

def has_path_dfs(graph, start, end):
    """
    Check if path exists between start and end
    Time Complexity: O(V + E)
    Space Complexity: O(V)
    """
    if start == end:
        return True
    
    visited = set()
    stack = [start]
    
    while stack:
        vertex = stack.pop()
        if vertex == end:
            return True
        
        if vertex not in visited:
            visited.add(vertex)
            for neighbor in graph[vertex]:
                if neighbor not in visited:
                    stack.append(neighbor)
    
    return False

# Example usage
graph = {
    'A': ['B', 'C'],
    'B': ['D', 'E'],
    'C': ['F'],
    'D': [],
    'E': ['F'],
    'F': []
}
print(dfs_iterative(graph, 'A'))  # Output: ['A', 'B', 'D', 'E', 'F', 'C']
print(has_path_dfs(graph, 'A', 'F'))  # Output: True
```

### 5.2 BFS Pattern
```python
from collections import deque

def bfs(graph, start):
    """
    Breadth-First Search
    Time Complexity: O(V + E)
    Space Complexity: O(V)
    """
    visited = set()
    queue = deque([start])
    result = []
    
    while queue:
        vertex = queue.popleft()
        if vertex not in visited:
            visited.add(vertex)
            result.append(vertex)
            
            for neighbor in graph[vertex]:
                if neighbor not in visited:
                    queue.append(neighbor)
    
    return result

def shortest_path_bfs(graph, start, end):
    """
    Find shortest path between start and end
    Time Complexity: O(V + E)
    Space Complexity: O(V)
    """
    if start == end:
        return [start]
    
    visited = set()
    queue = deque([(start, [start])])
    
    while queue:
        vertex, path = queue.popleft()
        
        if vertex not in visited:
            visited.add(vertex)
            
            for neighbor in graph[vertex]:
                new_path = path + [neighbor]
                if neighbor == end:
                    return new_path
                if neighbor not in visited:
                    queue.append((neighbor, new_path))
    
    return []  # No path found

def level_order_traversal_graph(graph, start):
    """
    Level-wise traversal of graph
    Time Complexity: O(V + E)
    Space Complexity: O(V)
    """
    visited = set()
    queue = deque([(start, 0)])
    levels = {}
    
    while queue:
        vertex, level = queue.popleft()
        
        if vertex not in visited:
            visited.add(vertex)
            
            if level not in levels:
                levels[level] = []
            levels[level].append(vertex)
            
            for neighbor in graph[vertex]:
                if neighbor not in visited:
                    queue.append((neighbor, level + 1))
    
    return levels

# Example usage
print(bfs(graph, 'A'))  # Output: ['A', 'B', 'C', 'D', 'E', 'F']
print(shortest_path_bfs(graph, 'A', 'F'))  # Output: ['A', 'C', 'F']
print(level_order_traversal_graph(graph, 'A'))  # Output: {0: ['A'], 1: ['B', 'C'], 2: ['D', 'E', 'F']}
```

## 6. Backtracking Patterns

### 6.1 Permutations and Combinations
```python
def permutations(nums):
    """
    Generate all permutations of given array
    Time Complexity: O(n! * n)
    Space Complexity: O(n! * n)
    """
    result = []
    
    def backtrack(current_perm):
        if len(current_perm) == len(nums):
            result.append(current_perm[:])  # Make a copy
            return
        
        for num in nums:
            if num not in current_perm:
                current_perm.append(num)
                backtrack(current_perm)
                current_perm.pop()  # Backtrack
    
    backtrack([])
    return result

def combinations(n, k):
    """
    Generate all combinations of k numbers from 1 to n
    Time Complexity: O(C(n,k) * k)
    Space Complexity: O(C(n,k) * k)
    """
    result = []
    
    def backtrack(start, current_comb):
        if len(current_comb) == k:
            result.append(current_comb[:])  # Make a copy
            return
        
        for i in range(start, n + 1):
            current_comb.append(i)
            backtrack(i + 1, current_comb)
            current_comb.pop()  # Backtrack
    
    backtrack(1, [])
    return result

def subsets(nums):
    """
    Generate all subsets of given array
    Time Complexity: O(2^n * n)
    Space Complexity: O(2^n * n)
    """
    result = []
    
    def backtrack(start, current_subset):
        result.append(current_subset[:])  # Make a copy
        
        for i in range(start, len(nums)):
            current_subset.append(nums[i])
            backtrack(i + 1, current_subset)
            current_subset.pop()  # Backtrack
    
    backtrack(0, [])
    return result

# Example usage
print(permutations([1, 2, 3]))  # Output: [[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]
print(combinations(4, 2))  # Output: [[1,2],[1,3],[1,4],[2,3],[2,4],[3,4]]
print(subsets([1, 2, 3]))  # Output: [[],[1],[2],[1,2],[3],[1,3],[2,3],[1,2,3]]
```

### 6.2 N-Queens Problem
```python
def solve_n_queens(n):
    """
    Solve N-Queens problem
    Time Complexity: O(n!)
    Space Complexity: O(n^2)
    """
    def is_safe(board, row, col):
        # Check column
        for i in range(row):
            if board[i][col] == 'Q':
                return False
        
        # Check diagonal (top-left to bottom-right)
        i, j = row - 1, col - 1
        while i >= 0 and j >= 0:
            if board[i][j] == 'Q':
                return False
            i -= 1
            j -= 1
        
        # Check diagonal (top-right to bottom-left)
        i, j = row - 1, col + 1
        while i >= 0 and j < n:
            if board[i][j] == 'Q':
                return False
            i -= 1
            j += 1
        
        return True
    
    def solve(board, row):
        if row == n:
            result.append([''.join(row) for row in board])
            return
        
        for col in range(n):
            if is_safe(board, row, col):
                board[row][col] = 'Q'
                solve(board, row + 1)
                board[row][col] = '.'  # Backtrack
    
    result = []
    board = [['.' for _ in range(n)] for _ in range(n)]
    solve(board, 0)
    return result

# Example usage
solutions = solve_n_queens(4)
for i, solution in enumerate(solutions):
    print(f"Solution {i + 1}:")
    for row in solution:
        print(row)
    print()
```

## 7. Greedy Algorithm Patterns

### 7.1 Activity Selection
```python
def activity_selection(start_times, end_times):
    """
    Select maximum number of non-overlapping activities
    Time Complexity: O(n log n)
    Space Complexity: O(n)
    """
    n = len(start_times)
    activities = list(zip(start_times, end_times, range(n)))
    
    # Sort by end time
    activities.sort(key=lambda x: x[1])
    
    selected = [activities[0][2]]  # Select first activity
    last_end_time = activities[0][1]
    
    for i in range(1, n):
        start_time, end_time, index = activities[i]
        if start_time >= last_end_time:
            selected.append(index)
            last_end_time = end_time
    
    return selected

def fractional_knapsack(weights, values, capacity):
    """
    Fractional Knapsack Problem
    Time Complexity: O(n log n)
    Space Complexity: O(n)
    """
    n = len(weights)
    items = [(values[i] / weights[i], weights[i], values[i]) for i in range(n)]
    
    # Sort by value-to-weight ratio in descending order
    items.sort(reverse=True)
    
    total_value = 0
    for ratio, weight, value in items:
        if capacity >= weight:
            # Take the whole item
            total_value += value
            capacity -= weight
        else:
            # Take fraction of the item
            total_value += ratio * capacity
            break
    
    return total_value

# Example usage
start_times = [1, 3, 0, 5, 8, 5]
end_times = [2, 4, 6, 7, 9, 9]
print(activity_selection(start_times, end_times))  # Output: [0, 1, 3, 4]

weights = [10, 20, 30]
values = [60, 100, 120]
capacity = 50
print(fractional_knapsack(weights, values, capacity))  # Output: 240.0
```

## 8. Divide and Conquer Patterns

### 8.1 Merge Sort Pattern
```python
def merge_sort(arr):
    """
    Merge Sort Algorithm
    Time Complexity: O(n log n)
    Space Complexity: O(n)
    """
    if len(arr) <= 1:
        return arr
    
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    
    return merge(left, right)

def merge(left, right):
    """Helper function to merge two sorted arrays"""
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

def quick_sort(arr):
    """
    Quick Sort Algorithm
    Time Complexity: O(n log n) average, O(n^2) worst case
    Space Complexity: O(log n) average
    """
    if len(arr) <= 1:
        return arr
    
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    return quick_sort(left) + middle + quick_sort(right)

def binary_search(arr, target):
    """
    Binary Search (Divide and Conquer)
    Time Complexity: O(log n)
    Space Complexity: O(log n)
    """
    def binary_search_helper(left, right):
        if left > right:
            return -1
        
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            return binary_search_helper(mid + 1, right)
        else:
            return binary_search_helper(left, mid - 1)
    
    return binary_search_helper(0, len(arr) - 1)

# Example usage
arr = [64, 34, 25, 12, 22, 11, 90]
print(merge_sort(arr))  # Output: [11, 12, 22, 25, 34, 64, 90]
print(quick_sort(arr))  # Output: [11, 12, 22, 25, 34, 64, 90]

```

### 8.2 Maximum Subarray (Kadane's Algorithm)
```python
def max_subarray_sum(arr):
    """
    Maximum Subarray Sum using Kadane's Algorithm
    Time Complexity: O(n)
    Space Complexity: O(1)
    """
    max_sum = current_sum = arr[0]
    
    for i in range(1, len(arr)):
        current_sum = max(arr[i], current_sum + arr[i])
        max_sum = max(max_sum, current_sum)
    
    return max_sum

def max_subarray_divide_conquer(arr):
    """
    Maximum Subarray Sum using Divide and Conquer
    Time Complexity: O(n log n)
    Space Complexity: O(log n)
    """
    def max_crossing_sum(arr, low, mid, high):
        left_sum = float('-inf')
        current_sum = 0
        for i in range(mid, low - 1, -1):
            current_sum += arr[i]
            if current_sum > left_sum:
                left_sum = current_sum
        
        right_sum = float('-inf')
        current_sum = 0
        for i in range(mid + 1, high + 1):
            current_sum += arr[i]
            if current_sum > right_sum:
                right_sum = current_sum
        
        return left_sum + right_sum
    
    def max_subarray_rec(arr, low, high):
        if low == high:
            return arr[low]
        
        mid = (low + high) // 2
        
        left_sum = max_subarray_rec(arr, low, mid)
        right_sum = max_subarray_rec(arr, mid + 1, high)
        cross_sum = max_crossing_sum(arr, low, mid, high)
        
        return max(left_sum, right_sum, cross_sum)
    
    return max_subarray_rec(arr, 0, len(arr) - 1)

# Example usage
arr = [-2, -3, 4, -1, -2, 1, 5, -3]
print(max_subarray_sum(arr))  # Output: 7
print(max_subarray_divide_conquer(arr))  # Output: 7
```

## 9. Heap Patterns

### 9.1 Min/Max Heap Operations
```python
import heapq

def k_largest_elements(arr, k):
    """
    Find K largest elements using Min Heap
    Time Complexity: O(n log k)
    Space Complexity: O(k)
    """
    if k >= len(arr):
        return sorted(arr, reverse=True)
    
    min_heap = []
    
    for num in arr:
        if len(min_heap) < k:
            heapq.heappush(min_heap, num)
        elif num > min_heap[0]:
            heapq.heapreplace(min_heap, num)
    
    return sorted(min_heap, reverse=True)

def k_smallest_elements(arr, k):
    """
    Find K smallest elements using Max Heap
    Time Complexity: O(n log k)
    Space Complexity: O(k)
    """
    if k >= len(arr):
        return sorted(arr)
    
    max_heap = []
    
    for num in arr:
        if len(max_heap) < k:
            heapq.heappush(max_heap, -num)  # Use negative for max heap
        elif num < -max_heap[0]:
            heapq.heapreplace(max_heap, -num)
    
    return sorted([-x for x in max_heap])

def kth_largest_element(arr, k):
    """
    Find Kth largest element
    Time Complexity: O(n log k)
    Space Complexity: O(k)
    """
    min_heap = []
    
    for num in arr:
        heapq.heappush(min_heap, num)
        if len(min_heap) > k:
            heapq.heappop(min_heap)
    
    return min_heap[0]

class MedianFinder:
    """
    Find median from data stream
    Time Complexity: O(log n) for add, O(1) for find median
    Space Complexity: O(n)
    """
    def __init__(self):
        self.small = []  # Max heap (use negative values)
        self.large = []  # Min heap
    
    def add_num(self, num):
        heapq.heappush(self.small, -num)
        
        # Balance heaps
        if (self.small and self.large and 
            (-self.small[0] > self.large[0])):
            val = -heapq.heappop(self.small)
            heapq.heappush(self.large, val)
        
        # Maintain size property
        if len(self.small) > len(self.large) + 1:
            val = -heapq.heappop(self.small)
            heapq.heappush(self.large, val)
        
        if len(self.large) > len(self.small) + 1:
            val = heapq.heappop(self.large)
            heapq.heappush(self.small, -val)
    
    def find_median(self):
        if len(self.small) > len(self.large):
            return -self.small[0]
        elif len(self.large) > len(self.small):
            return self.large[0]
        else:
            return (-self.small[0] + self.large[0]) / 2

# Example usage
arr = [3, 2, 1, 5, 6, 4]
print(k_largest_elements(arr, 3))  # Output: [6, 5, 4]
print(k_smallest_elements(arr, 3))  # Output: [1, 2, 3]
print(kth_largest_element(arr, 2))  # Output: 5

median_finder = MedianFinder()
for num in [1, 2, 3, 4, 5]:
    median_finder.add_num(num)
    print(f"Added {num}, median: {median_finder.find_median()}")
```

## 10. Trie Pattern

### 10.1 Trie Implementation
```python
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False

class Trie:
    """
    Trie (Prefix Tree) Implementation
    Time Complexity: O(m) for insert, search, startsWith where m is key length
    Space Complexity: O(ALPHABET_SIZE * N * M) where N is number of keys, M is average length
    """
    def __init__(self):
        self.root = TrieNode()
    
    def insert(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True
    
    def search(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end_of_word
    
    def starts_with(self, prefix):
        node = self.root
        for char in prefix:
            if char not in node.children:
                return False
            node = node.children[char]
        return True
    
    def get_all_words_with_prefix(self, prefix):
        def dfs(node, current_word, words):
            if node.is_end_of_word:
                words.append(current_word)
            
            for char, child_node in node.children.items():
                dfs(child_node, current_word + char, words)
        
        node = self.root
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]
        
        words = []
        dfs(node, prefix, words)
        return words
    
    def delete(self, word):
        def delete_helper(node, word, index):
            if index == len(word):
                if not node.is_end_of_word:
                    return False
                node.is_end_of_word = False
                return len(node.children) == 0
            
            char = word[index]
            if char not in node.children:
                return False
            
            should_delete_child = delete_helper(node.children[char], word, index + 1)
            
            if should_delete_child:
                del node.children[char]
                return not node.is_end_of_word and len(node.children) == 0
            
            return False
        
        delete_helper(self.root, word, 0)

# Example usage
trie = Trie()
words = ["apple", "app", "appl", "apply", "application"]
for word in words:
    trie.insert(word)

print(trie.search("app"))  # Output: True
print(trie.search("appl"))  # Output: True
print(trie.search("appli"))  # Output: False
print(trie.starts_with("app"))  # Output: True
print(trie.get_all_words_with_prefix("app"))  # Output: ['app', 'appl', 'apple', 'apply', 'application']
```

## 11. Union-Find (Disjoint Set) Pattern

### 11.1 Union-Find Implementation
```python
class UnionFind:
    """
    Union-Find (Disjoint Set Union) with Path Compression and Union by Rank
    Time Complexity: O(α(n)) per operation where α is inverse Ackermann function
    Space Complexity: O(n)
    """
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.components = n
    
    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # Path compression
        return self.parent[x]
    
    def union(self, x, y):
        root_x = self.find(x)
        root_y = self.find(y)
        
        if root_x != root_y:
            # Union by rank
            if self.rank[root_x] < self.rank[root_y]:
                self.parent[root_x] = root_y
            elif self.rank[root_x] > self.rank[root_y]:
                self.parent[root_y] = root_x
            else:
                self.parent[root_y] = root_x
                self.rank[root_x] += 1
            
            self.components -= 1
            return True
        return False
    
    def connected(self, x, y):
        return self.find(x) == self.find(y)
    
    def get_components_count(self):
        return self.components

def number_of_islands(grid):
    """
    Count number of islands using Union-Find
    Time Complexity: O(m * n * α(m * n))
    Space Complexity: O(m * n)
    """
    if not grid:
        return 0
    
    m, n = len(grid), len(grid[0])
    uf = UnionFind(m * n)
    
    def get_index(i, j):
        return i * n + j
    
    water_count = 0
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    
    for i in range(m):
        for j in range(n):
            if grid[i][j] == '1':
                for di, dj in directions:
                    ni, nj = i + di, j + dj
                    if 0 <= ni < m and 0 <= nj < n and grid[ni][nj] == '1':
                        uf.union(get_index(i, j), get_index(ni, nj))
            else:
                water_count += 1
    
    # Count unique roots for land cells
    roots = set()
    for i in range(m):
        for j in range(n):
            if grid[i][j] == '1':
                roots.add(uf.find(get_index(i, j)))
    
    return len(roots)

def accounts_merge(accounts):
    """
    Merge accounts that belong to same person using Union-Find
    Time Complexity: O(N * M * α(N * M)) where N is accounts, M is emails per account
    Space Complexity: O(N * M)
    """
    email_to_id = {}
    email_to_name = {}
    
    # Assign unique ID to each email
    email_id = 0
    for account in accounts:
        name = account[0]
        for email in account[1:]:
            if email not in email_to_id:
                email_to_id[email] = email_id
                email_to_name[email] = name
                email_id += 1
    
    uf = UnionFind(email_id)
    
    # Union emails from same account
    for account in accounts:
        first_email = account[1]
        first_id = email_to_id[first_email]
        
        for email in account[2:]:
            email_id = email_to_id[email]
            uf.union(first_id, email_id)
    
    # Group emails by root
    id_to_email = {v: k for k, v in email_to_id.items()}
    groups = {}
    
    for email_id in range(len(email_to_id)):
        root = uf.find(email_id)
        if root not in groups:
            groups[root] = []
        groups[root].append(id_to_email[email_id])
    
    # Format result
    result = []
    for emails in groups.values():
        name = email_to_name[emails[0]]
        result.append([name] + sorted(emails))
    
    return result

# Example usage
uf = UnionFind(5)
uf.union(0, 1)
uf.union(1, 2)
print(uf.connected(0, 2))  # Output: True
print(uf.get_components_count())  # Output: 3

grid = [
    ["1","1","1","1","0"],
    ["1","1","0","1","0"],
    ["1","1","0","0","0"],
    ["0","0","0","0","0"]
]
print(number_of_islands(grid))  # Output: 1

accounts = [["John","johnsmith@mail.com","john_newyork@mail.com"],
           ["John","johnsmith@mail.com","john00@mail.com"],
           ["Mary","mary@mail.com"],
           ["John","johnnybravo@mail.com"]]
print(accounts_merge(accounts))
```

## 12. Bit Manipulation Patterns

### 12.1 Basic Bit Operations
```python
def count_set_bits(n):
    """
    Count number of 1s in binary representation
    Time Complexity: O(log n)
    Space Complexity: O(1)
    """
    count = 0
    while n:
        count += 1
        n &= (n - 1)  # Remove rightmost set bit
    return count

def is_power_of_two(n):
    """
    Check if number is power of 2
    Time Complexity: O(1)
    Space Complexity: O(1)
    """
    return n > 0 and (n & (n - 1)) == 0

def find_single_number(nums):
    """
    Find single number when all others appear twice
    Time Complexity: O(n)
    Space Complexity: O(1)
    """
    result = 0
    for num in nums:
        result ^= num
    return result

def find_two_single_numbers(nums):
    """
    Find two single numbers when all others appear twice
    Time Complexity: O(n)
    Space Complexity: O(1)
    """
    xor_all = 0
    for num in nums:
        xor_all ^= num
    
    # Find rightmost set bit
    rightmost_set_bit = xor_all & (-xor_all)
    
    num1 = num2 = 0
    for num in nums:
        if num & rightmost_set_bit:
            num1 ^= num
        else:
            num2 ^= num
    
    return [num1, num2]

def subset_xor(nums):
    """
    Find XOR of all subsets
    Time Complexity: O(n)
    Space Complexity: O(1)
    """
    n = len(nums)
    if n % 4 == 1 or n % 4 == 2:
        return 0
    
    xor_all = 0
    for num in nums:
        xor_all ^= num
    
    return xor_all if n % 4 == 3 else 0

def generate_subsets_bits(nums):
    """
    Generate all subsets using bit manipulation
    Time Complexity: O(2^n * n)
    Space Complexity: O(2^n * n)
    """
    n = len(nums)
    subsets = []
    
    for mask in range(1 << n):  # 2^n subsets
        subset = []
        for i in range(n):
            if mask & (1 << i):  # Check if ith bit is set
                subset.append(nums[i])
        subsets.append(subset)
    
    return subsets

# Example usage
print(count_set_bits(12))  # Output: 2 (binary: 1100)
print(is_power_of_two(16))  # Output: True
print(find_single_number([4, 1, 2, 1, 2]))  # Output: 4
print(find_two_single_numbers([1, 2, 3, 2, 1, 4]))  # Output: [3, 4]
print(generate_subsets_bits([1, 2, 3]))  # Output: All subsets
```

## 13. Mathematical Patterns

### 13.1 Number Theory Patterns
```python
def gcd(a, b):
    """
    Greatest Common Divisor using Euclidean Algorithm
    Time Complexity: O(log min(a, b))
    Space Complexity: O(1)
    """
    while b:
        a, b = b, a % b
    return a

def lcm(a, b):
    """
    Least Common Multiple
    Time Complexity: O(log min(a, b))
    Space Complexity: O(1)
    """
    return abs(a * b) // gcd(a, b)

def sieve_of_eratosthenes(n):
    """
    Find all prime numbers up to n
    Time Complexity: O(n log log n)
    Space Complexity: O(n)
    """
    is_prime = [True] * (n + 1)
    is_prime[0] = is_prime[1] = False
    
    for i in range(2, int(n**0.5) + 1):
        if is_prime[i]:
            for j in range(i * i, n + 1, i):
                is_prime[j] = False
    
    return [i for i in range(n + 1) if is_prime[i]]

def is_prime(n):
    """
    Check if number is prime
    Time Complexity: O(sqrt(n))
    Space Complexity: O(1)
    """
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    
    for i in range(3, int(n**0.5) + 1, 2):
        if n % i == 0:
            return False
    return True

def prime_factorization(n):
    """
    Find prime factorization of n
    Time Complexity: O(sqrt(n))
    Space Complexity: O(log n)
    """
    factors = []
    
    # Handle factor 2
    while n % 2 == 0:
        factors.append(2)
        n //= 2
    
    # Handle odd factors
    for i in range(3, int(n**0.5) + 1, 2):
        while n % i == 0:
            factors.append(i)
            n //= i
    
    # If n is still greater than 2, it's a prime
    if n > 2:
        factors.append(n)
    
    return factors

def modular_exponentiation(base, exp, mod):
    """
    Calculate (base^exp) % mod efficiently
    Time Complexity: O(log exp)
    Space Complexity: O(1)
    """
    result = 1
    base = base % mod
    
    while exp > 0:
        if exp % 2 == 1:
            result = (result * base) % mod
        exp = exp >> 1
        base = (base * base) % mod
    
    return result

# Example usage
print(gcd(48, 18))  # Output: 6
print(lcm(12, 15))  # Output: 60
print(sieve_of_eratosthenes(30))  # Output: [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
print(is_prime(17))  # Output: True
print(prime_factorization(60))  # Output: [2, 2, 3, 5]
print(modular_exponentiation(2, 10, 1000))  # Output: 24
```

## Summary

This comprehensive guide covers the major pattern recognition techniques in Data Structures and Algorithms:

1. **String Patterns**: Naive search, KMP, Rabin-Karp for pattern matching
2. **Array Patterns**: Two pointers, sliding window, fast-slow pointers
3. **Tree Patterns**: Traversals, path finding, level-order processing
4. **Dynamic Programming**: Knapsack, Fibonacci, LCS patterns
5. **Graph Patterns**: DFS, BFS for traversal and pathfinding
6. **Backtracking**: Permutations, combinations, N-Queens
7. **Greedy Algorithms**: Activity selection, fractional knapsack
8. **Divide and Conquer**: Merge sort, quick sort, binary search
9. **Heap Patterns**: K largest/smallest, median finding
10. **Trie**: Prefix tree for string operations
11. **Union-Find**: Disjoint set operations
12. **Bit Manipulation**: Efficient operations using bits
13. **Mathematical**: Number theory and computational mathematics

Each pattern includes:
- Time and space complexity analysis
- Complete working code examples
- Practical use cases and variations
- Common interview problems that use the pattern

Master these patterns and you'll be well-equipped to tackle most DSA problems efficiently!

# Advanced Pattern Recognition in Data Structures and Algorithms

## 1. Advanced String Algorithms

### 1.1 Z-Algorithm for Pattern Matching
```python
def z_algorithm(s):
    """
    Z-Algorithm for string matching
    Time Complexity: O(n)
    Space Complexity: O(n)
    """
    n = len(s)
    z = [0] * n
    l, r = 0, 0
    
    for i in range(1, n):
        if i <= r:
            z[i] = min(r - i + 1, z[i - l])
        
        while i + z[i] < n and s[z[i]] == s[i + z[i]]:
            z[i] += 1
        
        if i + z[i] - 1 > r:
            l, r = i, i + z[i] - 1
    
    return z

def pattern_search_z_algorithm(text, pattern):
    """
    Pattern searching using Z-Algorithm
    Time Complexity: O(n + m)
    Space Complexity: O(n + m)
    """
    s = pattern + "$" + text
    z = z_algorithm(s)
    pattern_len = len(pattern)
    
    matches = []
    for i in range(pattern_len + 1, len(s)):
        if z[i] == pattern_len:
            matches.append(i - pattern_len - 1)
    
    return matches

# Example usage
text = "ABABDABACDABABCABCABCABCABC"
pattern = "ABABC"
print(pattern_search_z_algorithm(text, pattern))  # Output: [10, 15]
```

### 1.2 Suffix Array and LCP Array
```python
def build_suffix_array(s):
    """
    Build suffix array using counting sort approach
    Time Complexity: O(n log^2 n)
    Space Complexity: O(n)
    """
    n = len(s)
    suffixes = [(s[i:], i) for i in range(n)]
    suffixes.sort()
    return [suffix[1] for suffix in suffixes]

def build_lcp_array(s, suffix_array):
    """
    Build LCP (Longest Common Prefix) array
    Time Complexity: O(n)
    Space Complexity: O(n)
    """
    n = len(s)
    rank = [0] * n
    lcp = [0] * (n - 1)
    
    # Build rank array
    for i in range(n):
        rank[suffix_array[i]] = i
    
    h = 0
    for i in range(n):
        if rank[i] > 0:
            j = suffix_array[rank[i] - 1]
            while i + h < n and j + h < n and s[i + h] == s[j + h]:
                h += 1
            lcp[rank[i] - 1] = h
            if h > 0:
                h -= 1
    
    return lcp

def longest_repeated_substring(s):
    """
    Find longest repeated substring using suffix array
    Time Complexity: O(n log n)
    Space Complexity: O(n)
    """
    if not s:
        return ""
    
    suffix_array = build_suffix_array(s)
    lcp = build_lcp_array(s, suffix_array)
    
    max_lcp = max(lcp)
    if max_lcp == 0:
        return ""
    
    idx = lcp.index(max_lcp)
    return s[suffix_array[idx]:suffix_array[idx] + max_lcp]

# Example usage
s = "banana"
suffix_array = build_suffix_array(s)
lcp = build_lcp_array(s, suffix_array)
print(f"Suffix Array: {suffix_array}")  # Output: [5, 3, 1, 0, 4, 2]
print(f"LCP Array: {lcp}")  # Output: [1, 3, 0, 0, 2]
print(f"Longest repeated substring: {longest_repeated_substring(s)}")  # Output: "ana"
```

### 1.3 Aho-Corasick Algorithm for Multiple Pattern Matching
```python
from collections import deque, defaultdict

class AhoCorasick:
    """
    Aho-Corasick Algorithm for multiple pattern matching
    Time Complexity: O(n + m + z) where n=text length, m=total pattern length, z=matches
    Space Complexity: O(m)
    """
    def __init__(self):
        self.trie = {}
        self.failure = {}
        self.output = defaultdict(list)
        self.patterns = []
    
    def add_pattern(self, pattern, pattern_id):
        node = self.trie
        for char in pattern:
            if char not in node:
                node[char] = {}
            node = node[char]
        
        if 'end' not in node:
            node['end'] = []
        node['end'].append(pattern_id)
        self.patterns.append(pattern)
    
    def build_failure_function(self):
        queue = deque()
        
        # Initialize failure function for depth 1
        for char in self.trie:
            self.failure[(char,)] = ()
            queue.append((char,))
        
        while queue:
            current_state = queue.popleft()
            current_node = self.trie
            
            # Navigate to current state
            for char in current_state:
                current_node = current_node[char]
            
            # Process each child
            for char in current_node:
                if char == 'end':
                    continue
                
                child_state = current_state + (char,)
                queue.append(child_state)
                
                # Find failure state
                temp_state = current_state
                while temp_state:
                    temp_state = self.failure[temp_state]
                    temp_node = self.trie
                    
                    # Check if suffix + char exists
                    valid = True
                    for c in temp_state:
                        if c not in temp_node:
                            valid = False
                            break
                        temp_node = temp_node[c]
                    
                    if valid and char in temp_node:
                        self.failure[child_state] = temp_state + (char,)
                        break
                else:
                    self.failure[child_state] = ()
                
                # Build output function
                failure_state = self.failure[child_state]
                if failure_state in self.output:
                    self.output[child_state].extend(self.output[failure_state])
    
    def search(self, text):
        self.build_failure_function()
        current_state = ()
        matches = []
        
        for i, char in enumerate(text):
            # Follow failure links until we find a valid transition
            while current_state:
                current_node = self.trie
                valid = True
                
                for c in current_state:
                    if c not in current_node:
                        valid = False
                        break
                    current_node = current_node[c]
                
                if valid and char in current_node:
                    current_state = current_state + (char,)
                    break
                else:
                    current_state = self.failure[current_state]
            else:
                # Check if we can start a new match from root
                if char in self.trie:
                    current_state = (char,)
                else:
                    current_state = ()
            
            # Check for matches
            current_node = self.trie
            for c in current_state:
                current_node = current_node[c]
            
            if 'end' in current_node:
                for pattern_id in current_node['end']:
                    pattern_len = len(self.patterns[pattern_id])
                    matches.append((i - pattern_len + 1, pattern_id))
            
            # Check output function for failure states
            if current_state in self.output:
                for pattern_id in self.output[current_state]:
                    pattern_len = len(self.patterns[pattern_id])
                    matches.append((i - pattern_len + 1, pattern_id))
        
        return matches

# Example usage
ac = AhoCorasick()
ac.add_pattern("he", 0)
ac.add_pattern("she", 1)
ac.add_pattern("his", 2)
ac.add_pattern("hers", 3)

text = "ushers"
matches = ac.search(text)
print("Matches found:")
for pos, pattern_id in matches:
    print(f"Pattern '{ac.patterns[pattern_id]}' found at position {pos}")
```

## 2. Advanced Tree Algorithms

### 2.1 Heavy-Light Decomposition
```python
class HeavyLightDecomposition:
    """
    Heavy-Light Decomposition for tree path queries
    Time Complexity: O(log^2 n) per query
    Space Complexity: O(n)
    """
    def __init__(self, n):
        self.n = n
        self.adj = [[] for _ in range(n)]
        self.parent = [-1] * n
        self.depth = [0] * n
        self.size = [0] * n
        self.heavy = [-1] * n
        self.head = list(range(n))
        self.pos = [0] * n
        self.timer = 0
    
    def add_edge(self, u, v):
        self.adj[u].append(v)
        self.adj[v].append(u)
    
    def dfs1(self, node, par):
        self.size[node] = 1
        self.parent[node] = par
        
        max_child_size = 0
        for child in self.adj[node]:
            if child != par:
                self.depth[child] = self.depth[node] + 1
                self.dfs1(child, node)
                self.size[node] += self.size[child]
                
                if self.size[child] > max_child_size:
                    max_child_size = self.size[child]
                    self.heavy[node] = child
    
    def dfs2(self, node, h):
        self.head[node] = h
        self.pos[node] = self.timer
        self.timer += 1
        
        if self.heavy[node] != -1:
            self.dfs2(self.heavy[node], h)
        
        for child in self.adj[node]:
            if child != self.parent[node] and child != self.heavy[node]:
                self.dfs2(child, child)
    
    def build(self, root=0):
        self.dfs1(root, -1)
        self.dfs2(root, root)
    
    def lca(self, u, v):
        while self.head[u] != self.head[v]:
            if self.depth[self.head[u]] > self.depth[self.head[v]]:
                u = self.parent[self.head[u]]
            else:
                v = self.parent[self.head[v]]
        
        return u if self.depth[u] < self.depth[v] else v
    
    def path_query(self, u, v):
        """Returns list of ranges representing path from u to v"""
        ranges = []
        
        while self.head[u] != self.head[v]:
            if self.depth[self.head[u]] > self.depth[self.head[v]]:
                ranges.append((self.pos[self.head[u]], self.pos[u]))
                u = self.parent[self.head[u]]
            else:
                ranges.append((self.pos[self.head[v]], self.pos[v]))
                v = self.parent[self.head[v]]
        
        if self.pos[u] > self.pos[v]:
            ranges.append((self.pos[v], self.pos[u]))
        else:
            ranges.append((self.pos[u], self.pos[v]))
        
        return ranges

# Example usage
n = 7
hld = HeavyLightDecomposition(n)
edges = [(0, 1), (0, 2), (1, 3), (1, 4), (2, 5), (2, 6)]
for u, v in edges:
    hld.add_edge(u, v)

hld.build()
print(f"LCA of 3 and 5: {hld.lca(3, 5)}")  # Output: 0
print(f"Path ranges from 3 to 5: {hld.path_query(3, 5)}")
```

### 2.2 Link-Cut Tree (Dynamic Tree)
```python
class LinkCutTree:
    """
    Link-Cut Tree for dynamic tree operations
    Time Complexity: O(log n) per operation
    Space Complexity: O(n)
    """
    def __init__(self, n):
        self.n = n
        self.parent = [None] * n
        self.left = [None] * n
        self.right = [None] * n
        self.rev = [False] * n
        self.value = [0] * n
    
    def is_root(self, x):
        p = self.parent[x]
        return p is None or (self.left[p] != x and self.right[p] != x)
    
    def push(self, x):
        if self.rev[x]:
            self.left[x], self.right[x] = self.right[x], self.left[x]
            if self.left[x] is not None:
                self.rev[self.left[x]] ^= True
            if self.right[x] is not None:
                self.rev[self.right[x]] ^= True
            self.rev[x] = False
    
    def rotate(self, x):
        p = self.parent[x]
        g = self.parent[p]
        
        if self.left[p] == x:
            self.left[p] = self.right[x]
            if self.right[x] is not None:
                self.parent[self.right[x]] = p
            self.right[x] = p
        else:
            self.right[p] = self.left[x]
            if self.left[x] is not None:
                self.parent[self.left[x]] = p
            self.left[x] = p
        
        self.parent[p] = x
        self.parent[x] = g
        
        if g is not None:
            if self.left[g] == p:
                self.left[g] = x
            elif self.right[g] == p:
                self.right[g] = x
    
    def splay(self, x):
        stack = []
        y = x
        while not self.is_root(y):
            stack.append(y)
            y = self.parent[y]
        stack.append(y)
        
        for node in reversed(stack):
            self.push(node)
        
        while not self.is_root(x):
            p = self.parent[x]
            g = self.parent[p]
            
            if not self.is_root(p):
                if (self.left[g] == p) == (self.left[p] == x):
                    self.rotate(p)
                else:
                    self.rotate(x)
            self.rotate(x)
    
    def access(self, x):
        self.splay(x)
        self.right[x] = None
        
        while self.parent[x] is not None:
            y = self.parent[x]
            self.splay(y)
            self.right[y] = x
            self.splay(x)
    
    def make_root(self, x):
        self.access(x)
        self.splay(x)
        self.rev[x] ^= True
    
    def link(self, x, y):
        self.make_root(x)
        self.parent[x] = y
    
    def cut(self, x, y):
        self.make_root(x)
        self.access(y)
        self.splay(y)
        
        if self.left[y] == x and self.right[x] is None:
            self.parent[x] = None
            self.left[y] = None
    
    def find_root(self, x):
        self.access(x)
        self.splay(x)
        
        while self.left[x] is not None:
            x = self.left[x]
        
        self.splay(x)
        return x
    
    def connected(self, x, y):
        return self.find_root(x) == self.find_root(y)

# Example usage
n = 5
lct = LinkCutTree(n)
lct.link(0, 1)
lct.link(1, 2)
print(f"0 and 2 connected: {lct.connected(0, 2)}")  # Output: True
lct.cut(0, 1)
print(f"0 and 2 connected after cut: {lct.connected(0, 2)}")  # Output: False
```

## 3. Advanced Graph Algorithms

### 3.1 Tarjan's Algorithm for Strongly Connected Components
```python
class TarjanSCC:
    """
    Tarjan's Algorithm for finding Strongly Connected Components
    Time Complexity: O(V + E)
    Space Complexity: O(V)
    """
    def __init__(self, n):
        self.n = n
        self.graph = [[] for _ in range(n)]
        self.ids = [-1] * n
        self.low = [-1] * n
        self.on_stack = [False] * n
        self.stack = []
        self.id_counter = 0
        self.scc_count = 0
        self.sccs = []
    
    def add_edge(self, u, v):
        self.graph[u].append(v)
    
    def dfs(self, at):
        self.stack.append(at)
        self.on_stack[at] = True
        self.ids[at] = self.low[at] = self.id_counter
        self.id_counter += 1
        
        for to in self.graph[at]:
            if self.ids[to] == -1:
                self.dfs(to)
            if self.on_stack[to]:
                self.low[at] = min(self.low[at], self.low[to])
        
        if self.ids[at] == self.low[at]:
            scc = []
            while True:
                node = self.stack.pop()
                self.on_stack[node] = False
                scc.append(node)
                if node == at:
                    break
            self.sccs.append(scc)
            self.scc_count += 1
    
    def find_sccs(self):
        for i in range(self.n):
            if self.ids[i] == -1:
                self.dfs(i)
        return self.sccs

# Example usage
tarjan = TarjanSCC(8)
edges = [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3), (1, 3), (2, 4), (6, 7)]
for u, v in edges:
    tarjan.add_edge(u, v)

sccs = tarjan.find_sccs()
print("Strongly Connected Components:")
for i, scc in enumerate(sccs):
    print(f"SCC {i}: {scc}")
```

### 3.2 Edmonds-Karp Algorithm for Maximum Flow
```python
from collections import deque

class EdmondsKarp:
    """
    Edmonds-Karp Algorithm for Maximum Flow
    Time Complexity: O(V * E^2)
    Space Complexity: O(V^2)
    """
    def __init__(self, n):
        self.n = n
        self.capacity = [[0] * n for _ in range(n)]
        self.adj = [[] for _ in range(n)]
    
    def add_edge(self, u, v, cap):
        self.capacity[u][v] += cap
        self.adj[u].append(v)
        self.adj[v].append(u)
    
    def bfs(self, source, sink, parent):
        visited = [False] * self.n
        queue = deque([source])
        visited[source] = True
        
        while queue:
            u = queue.popleft()
            
            for v in self.adj[u]:
                if not visited[v] and self.capacity[u][v] > 0:
                    visited[v] = True
                    parent[v] = u
                    if v == sink:
                        return True
                    queue.append(v)
        
        return False
    
    def max_flow(self, source, sink):
        parent = [-1] * self.n
        max_flow_value = 0
        
        while self.bfs(source, sink, parent):
            path_flow = float('inf')
            s = sink
            
            while s != source:
                path_flow = min(path_flow, self.capacity[parent[s]][s])
                s = parent[s]
            
            max_flow_value += path_flow
            v = sink
            
            while v != source:
                u = parent[v]
                self.capacity[u][v] -= path_flow
                self.capacity[v][u] += path_flow
                v = parent[v]
        
        return max_flow_value

# Example usage
graph = EdmondsKarp(6)
graph.add_edge(0, 1, 16)
graph.add_edge(0, 2, 13)
graph.add_edge(1, 2, 10)
graph.add_edge(1, 3, 12)
graph.add_edge(2, 1, 4)
graph.add_edge(2, 4, 14)
graph.add_edge(3, 2, 9)
graph.add_edge(3, 5, 20)
graph.add_edge(4, 3, 7)
graph.add_edge(4, 5, 4)

print(f"Maximum flow: {graph.max_flow(0, 5)}")  # Output: 23
```

### 3.3 Hungarian Algorithm for Assignment Problem
```python
class HungarianAlgorithm:
    """
    Hungarian Algorithm for minimum weight perfect matching
    Time Complexity: O(n^3)
    Space Complexity: O(n^2)
    """
    def __init__(self, cost_matrix):
        self.n = len(cost_matrix)
        self.cost = [row[:] for row in cost_matrix]
        self.u = [0] * (self.n + 1)  # potential for workers
        self.v = [0] * (self.n + 1)  # potential for jobs
        self.p = [0] * (self.n + 1)  # assignment
        self.way = [0] * (self.n + 1)  # for reconstructing path
    
    def solve(self):
        for i in range(1, self.n + 1):
            self.p[0] = i
            j0 = 0
            minv = [float('inf')] * (self.n + 1)
            used = [False] * (self.n + 1)
            
            while True:
                used[j0] = True
                i0 = self.p[j0]
                delta = float('inf')
                j1 = None
                
                for j in range(1, self.n + 1):
                    if not used[j]:
                        cur = self.cost[i0 - 1][j - 1] - self.u[i0] - self.v[j]
                        if cur < minv[j]:
                            minv[j] = cur
                            self.way[j] = j0
                        if minv[j] < delta:
                            delta = minv[j]
                            j1 = j
                
                for j in range(self.n + 1):
                    if used[j]:
                        self.u[self.p[j]] += delta
                        self.v[j] -= delta
                    else:
                        minv[j] -= delta
                
                j0 = j1
                if self.p[j0] == 0:
                    break
            
            while True:
                j1 = self.way[j0]
                self.p[j0] = self.p[j1]
                j0 = j1
                if j0 == 0:
                    break
        
        result = []
        total_cost = 0
        for j in range(1, self.n + 1):
            worker = self.p[j] - 1
            job = j - 1
            result.append((worker, job))
            total_cost += self.cost[worker][job]
        
        return result, total_cost

# Example usage
cost_matrix = [
    [4, 1, 3],
    [2, 0, 5],
    [3, 2, 2]
]

hungarian = HungarianAlgorithm(cost_matrix)
assignment, min_cost = hungarian.solve()
print(f"Optimal assignment: {assignment}")
print(f"Minimum cost: {min_cost}")
```

## 4. Advanced Data Structures

### 4.1 Splay Tree
```python
class SplayNode:
    def __init__(self, key):
        self.key = key
        self.left = None
        self.right = None
        self.parent = None

class SplayTree:
    """
    Splay Tree - Self-adjusting binary search tree
    Amortized Time Complexity: O(log n) per operation
    Space Complexity: O(n)
    """
    def __init__(self):
        self.root = None
    
    def rotate_right(self, x):
        y = x.left
        x.left = y.right
        if y.right:
            y.right.parent = x
        y.parent = x.parent
        
        if not x.parent:
            self.root = y
        elif x == x.parent.right:
            x.parent.right = y
        else:
            x.parent.left = y
        
        y.right = x
        x.parent = y
    
    def rotate_left(self, x):
        y = x.right
        x.right = y.left
        if y.left:
            y.left.parent = x
        y.parent = x.parent
        
        if not x.parent:
            self.root = y
        elif x == x.parent.left:
            x.parent.left = y
        else:
            x.parent.right = y
        
        y.left = x
        x.parent = y
    
    def splay(self, node):
        while node.parent:
            if not node.parent.parent:
                # Zig case
                if node == node.parent.left:
                    self.rotate_right(node.parent)
                else:
                    self.rotate_left(node.parent)
            elif ((node == node.parent.left) == 
                  (node.parent == node.parent.parent.left)):
                # Zig-Zig case
                if node == node.parent.left:
                    self.rotate_right(node.parent.parent)
                    self.rotate_right(node.parent)
                else:
                    self.rotate_left(node.parent.parent)
                    self.rotate_left(node.parent)
            else:
                # Zig-Zag case
                if node == node.parent.left:
                    self.rotate_right(node.parent)
                    self.rotate_left(node.parent)
                else:
                    self.rotate_left(node.parent)
                    self.rotate_right(node.parent)
    
    def search(self, key):
        current = self.root
        while current:
            if key == current.key:
                self.splay(current)
                return current
            elif key < current.key:
                current = current.left
            else:
                current = current.right
        return None
    
    def insert(self, key):
        if not self.root:
            self.root = SplayNode(key)
            return
        
        current = self.root
        while True:
            if key < current.key:
                if not current.left:
                    current.left = SplayNode(key)
                    current.left.parent = current
                    self.splay(current.left)
                    return
                current = current.left
            elif key > current.key:
                if not current.right:
                    current.right = SplayNode(key)
                    current.right.parent = current
                    self.splay(current.right)
                    return
                current = current.right
            else:
                self.splay(current)
                return
    
    def delete(self, key):
        node = self.search(key)
        if not node:
            return
        
        if not node.left:
            self.root = node.right
            if self.root:
                self.root.parent = None
        elif not node.right:
            self.root = node.left
            if self.root:
                self.root.parent = None
        else:
            # Find maximum in left subtree
            max_left = node.left
            while max_left.right:
                max_left = max_left.right
            
            self.splay(max_left)
            max_left.right = node.right
            if node.right:
                node.right.parent = max_left
            self.root = max_left

# Example usage
splay_tree = SplayTree()
keys = [10, 20, 30, 40, 50, 25]
for key in keys:
    splay_tree.insert(key)

print(f"Search for 30: {splay_tree.search(30) is not None}")
print(f"Root after search: {splay_tree.root.key}")
```

### 4.2 Persistent Segment Tree
```python
class PersistentSegmentTree:
    """
    Persistent Segment Tree for range queries with version history
    Time Complexity: O(log n) per update/query
    Space Complexity: O(n log n) for all versions
    """
    class Node:
        def __init__(self, val=0, left=None, right=None):
            self.val = val
            self.left = left
            self.right = right
    
    def __init__(self, arr):
        self.n = len(arr)
        self.versions = []
        root = self.build(arr, 0, self.n - 1)
        self.versions.append(root)
    
    def build(self, arr, tl, tr):
        if tl == tr:
            return self.Node(arr[tl])
        
        tm = (tl + tr) // 2
        left_child = self.build(arr, tl, tm)
        right_child = self.build(arr, tm + 1, tr)
        
        return self.Node(left_child.val + right_child.val, left_child, right_child)
    
    def update(self, version, pos, val, tl=0, tr=None):
        if tr is None:
            tr = self.n - 1
        
        if tl == tr:
            return self.Node(val)
        
        tm = (tl + tr) // 2
        if pos <= tm:
            left_child = self.update(version.left, pos, val, tl, tm)
            right_child = version.right
        else:
            left_child = version.left
            right_child = self.update(version.right, pos, val, tm + 1, tr)
        
        return self.Node(left_child.val + right_child.val, left_child, right_child)
    
    def query(self, version, l, r, tl=0, tr=None):
        if tr is None:
            tr = self.n - 1
        
        if l > r:
            return 0
        if l == tl and r == tr:
            return version.val
        
        tm = (tl + tr) // 2
        left_sum = self.query(version.left, l, min(r, tm), tl, tm)
        right_sum = self.query(version.right, max(l, tm + 1), r, tm + 1, tr)
        
        return left_sum + right_sum
    
    def create_version(self, version_id, pos, val):
        new_root = self.update(self.versions[version_id], pos, val)
        self.versions.append(new_root)
        return len(self.versions) - 1
    
    def range_sum(self, version_id, l, r):
        return self.query(self.versions[version_id], l, r)

# Example usage
arr = [1, 2, 3, 4, 5]
pst = PersistentSegmentTree(arr)

# Version 0: original array [1, 2, 3, 4, 5]
print(f"Sum [0, 2] in version 0: {pst.range_sum(0, 0, 2)}")  # Output: 6

# Version 1: update position 1 to 10 -> [1, 10, 3, 4, 5]
v1 = pst.create_version(0, 1, 10)
print(f"Sum [0, 2] in version 1: {pst.range_sum(v1, 0, 2)}")  # Output: 14

# Version 2: update position 3 to 20 -> [1, 10, 3, 20, 5]
v2 = pst.create_version(v1, 3, 20)
print(f"Sum [0, 4] in version 2: {pst.range_sum(v2, 0, 4)}")  # Output: 39
```

### 4.3 Skip List
```python
import random

class SkipListNode:
    def __init__(self, val, level):
        self.val = val
        self.forward = [None] * (level + 1)

class SkipList:
    """
    Skip List - Probabilistic data structure
    Expected Time Complexity: O(log n) for search, insert, delete
    Space Complexity: O(n)
    """
    def __init__(self, max_level=16, p=0.5):
        self.max_level = max_level
        self.p = p
        self.header = SkipListNode(float('-inf'), max_level)
        self.level = 0
    
    def random_level(self):
        level = 0
        while random.random() < self.p and level < self.max_level:
            level += 1
        return level
    
    def search(self, target):
        current = self.header
        
        for i in range(self.level, -1, -1):
            while current.forward[i] and current.forward[i].val < target:
                current = current.forward[i]
        
        current = current.forward[0]
        return current and current.val == target
    
    def insert(self, val):
        update = [None] * (self.max_level + 1)
        current = self.header
        
        # Find position to insert
        for i in range(self.level, -1, -1):
            while current.forward[i] and current.forward[i].val < val:
                current = current.forward[i]
            update[i] = current
        
        current = current.forward[0]
        
        if current and current.val == val:
            return  # Value already exists
        
        # Generate random level for new node
        new_level = self.random_level()
        
        if new_level > self.level:
            for i in range(self.level + 1, new_level + 1):
                update[i] = self.header
            self.level = new_level
        
        # Create new node
        new_node = SkipListNode(val, new_level)
        
        # Insert node
        for i in range(new_level + 1):
            new_node.forward[i] = update[i].forward[i]
            update[i].forward[i] = new_node
    
    def delete(self, val):
        update = [None] * (self.max_level + 1)
        current = self.header
        
        # Find position to delete
        for i in range(self.level, -1, -1):
            while current.forward[i] and current.forward[i].val < val:
                current = current.forward[i]
            update[i] = current
        
        current = current.forward[0]
        
        if not current or current.val != val:
            return False  # Value not found
        
        # Remove node
        for i in range(self.level + 1):
            if update[i].forward[i] != current:
                break
            update[i].forward[i] = current.forward[i]
        
        # Update level
        while self.level > 0 and not self.header.forward[self.level]:
            self.level -= 1
        
        return True
    
    def display(self):
        for i in range(self.level + 1):
            print(f"Level {i}: ", end="")
            current = self.header.forward[i]
            while current:
                print(f"{current.val} ", end="")
                current = current.forward[i]
            print()

# Example usage
skip_list = SkipList()
elements = [3, 6, 7, 9, 12, 19, 17, 26, 21, 25]
for elem in elements:
    skip_list.insert(elem)

print("Skip List structure:")
skip_list.display()
print(f"Search 19: {skip_list.search(19)}")  # Output: True
print(f"Search 15: {skip_list.search(15)}")  # Output: False
```

## 5. Advanced Dynamic Programming Patterns

### 5.1 Digit DP (Dynamic Programming on Digits)
```python
def digit_dp(num_str):
    """
    Count numbers with sum of digits divisible by 3
    Time Complexity: O(n * sum_limit * 2)
    Space Complexity: O(n * sum_limit * 2)
    """
    n = len(num_str)
    memo = {}
    
    def dp(pos, sum_mod, tight, started):
        if pos == n:
            return 1 if sum_mod == 0 and started else 0
        
        if (pos, sum_mod, tight, started) in memo:
            return memo[(pos, sum_mod, tight, started)]
        
        limit = int(num_str[pos]) if tight else 9
        result = 0
        
        for digit in range(0, limit + 1):
            new_sum_mod = (sum_mod + digit) % 3
            new_tight = tight and (digit == limit)
            new_started = started or (digit > 0)
            
            result += dp(pos + 1, new_sum_mod, new_tight, new_started)
        
        memo[(pos, sum_mod, tight, started)] = result
        return result
    
    return dp(0, 0, True, False)

def count_palindromic_subsequences(s):
    """
    Count palindromic subsequences using DP
    Time Complexity: O(n^2)
    Space Complexity: O(n^2)
    """
    n = len(s)
    dp = [[0] * n for _ in range(n)]
    
    # Single characters are palindromes
    for i in range(n):
        dp[i][i] = 1
    
    # Check for palindromes of length 2
    for i in range(n - 1):
        if s[i] == s[i + 1]:
            dp[i][i + 1] = 3  # "", s[i], s[i]s[i+1]
        else:
            dp[i][i + 1] = 2  # "", s[i], s[i+1]
    
    # Check for palindromes of length 3 and more
    for length in range(3, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            
            if s[i] == s[j]:
                dp[i][j] = dp[i + 1][j] + dp[i][j - 1] + 1
            else:
                dp[i][j] = dp[i + 1][j] + dp[i][j - 1] - dp[i + 1][j - 1]
    
    return dp[0][n - 1]

# Example usage
print(f"Numbers ≤ 100 with digit sum divisible by 3: {digit_dp('100')}")
print(f"Palindromic subsequences in 'bccb': {count_palindromic_subsequences('bccb')}")
```

### 5.2 Matrix Chain Multiplication with Optimal Parenthesization
```python
def matrix_chain_order(dimensions):
    """
    Find optimal order to multiply chain of matrices
    Time Complexity: O(n^3)
    Space Complexity: O(n^2)
    """
    n = len(dimensions) - 1
    dp = [[0] * n for _ in range(n)]
    split = [[0] * n for _ in range(n)]
    
    # Length of chain
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            dp[i][j] = float('inf')
            
            for k in range(i, j):
                cost = (dp[i][k] + dp[k + 1][j] + 
                       dimensions[i] * dimensions[k + 1] * dimensions[j + 1])
                
                if cost < dp[i][j]:
                    dp[i][j] = cost
                    split[i][j] = k
    
    def construct_order(i, j):
        if i == j:
            return f"M{i}"
        else:
            return f"({construct_order(i, split[i][j])} x {construct_order(split[i][j] + 1, j)})"
    
    return dp[0][n - 1], construct_order(0, n - 1)

def optimal_binary_search_tree(keys, probabilities):
    """
    Construct optimal binary search tree
    Time Complexity: O(n^3)
    Space Complexity: O(n^2)
    """
    n = len(keys)
    cost = [[0] * n for _ in range(n)]
    root = [[0] * n for _ in range(n)]
    
    # Single key trees
    for i in range(n):
        cost[i][i] = probabilities[i]
        root[i][i] = i
    
    # Trees with multiple keys
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            cost[i][j] = float('inf')
            
            # Sum of probabilities in range [i, j]
            prob_sum = sum(probabilities[i:j + 1])
            
            for r in range(i, j + 1):
                left_cost = cost[i][r - 1] if r > i else 0
                right_cost = cost[r + 1][j] if r < j else 0
                
                total_cost = left_cost + right_cost + prob_sum
                
                if total_cost < cost[i][j]:
                    cost[i][j] = total_cost
                    root[i][j] = r
    
    return cost[0][n - 1], root

# Example usage
dimensions = [1, 2, 3, 4]  # Matrices: 1x2, 2x3, 3x4
min_cost, order = matrix_chain_order(dimensions)
print(f"Minimum scalar multiplications: {min_cost}")
print(f"Optimal order: {order}")

keys = [0, 1, 2, 3]
probabilities = [0.1, 0.2, 0.4, 0.3]
min_cost, root_matrix = optimal_binary_search_tree(keys, probabilities)
print(f"Minimum search cost: {min_cost}")
```

## 6. Advanced Geometric Algorithms

### 6.1 Convex Hull using Graham Scan
```python
import math

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def __repr__(self):
        return f"({self.x}, {self.y})"

def orientation(p, q, r):
    """Find orientation of ordered triplet (p, q, r)
    Returns: 0 -> Collinear, 1 -> Clockwise, 2 -> Counterclockwise
    """
    val = (q.y - p.y) * (r.x - q.x) - (q.x - p.x) * (r.y - q.y)
    if val == 0:
        return 0
    return 1 if val > 0 else 2

def distance_squared(p1, p2):
    return (p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2

def convex_hull_graham(points):
    """
    Graham Scan algorithm for Convex Hull
    Time Complexity: O(n log n)
    Space Complexity: O(n)
    """
    n = len(points)
    if n < 3:
        return points
    
    # Find bottom-most point (or left most in case of tie)
    bottom_point = min(points, key=lambda p: (p.y, p.x))
    
    # Sort points by polar angle with respect to bottom_point
    def polar_angle_key(point):
        if point == bottom_point:
            return -math.pi, 0
        
        dx = point.x - bottom_point.x
        dy = point.y - bottom_point.y
        angle = math.atan2(dy, dx)
        dist = distance_squared(bottom_point, point)
        return angle, dist
    
    sorted_points = sorted(points, key=polar_angle_key)
    
    # Create convex hull
    hull = []
    
    for point in sorted_points:
        while (len(hull) > 1 and 
               orientation(hull[-2], hull[-1], point) == 1):  # Clockwise
            hull.pop()
        hull.append(point)
    
    return hull

def point_in_convex_polygon(point, polygon):
    """
    Check if point is inside convex polygon
    Time Complexity: O(n)
    Space Complexity: O(1)
    """
    n = len(polygon)
    if n < 3:
        return False
    
    # Check if point is on the same side of all edges
    sign = None
    
    for i in range(n):
        j = (i + 1) % n
        cross_product = ((polygon[j].x - polygon[i].x) * (point.y - polygon[i].y) - 
                        (polygon[j].y - polygon[i].y) * (point.x - polygon[i].x))
        
        if cross_product != 0:
            if sign is None:
                sign = cross_product > 0
            elif (cross_product > 0) != sign:
                return False
    
    return True

# Example usage
points = [Point(0, 3), Point(1, 1), Point(2, 2), Point(4, 4),
          Point(0, 0), Point(1, 2), Point(3, 1), Point(3, 3)]

hull = convex_hull_graham(points)
print("Convex Hull:")
for point in hull:
    print(point)

test_point = Point(2, 2)
print(f"Point {test_point} is inside polygon: {point_in_convex_polygon(test_point, hull)}")
```

### 6.2 Closest Pair of Points using Divide and Conquer
```python
def closest_pair_divide_conquer(points):
    """
    Find closest pair of points using divide and conquer
    Time Complexity: O(n log^2 n)
    Space Complexity: O(n)
    """
    def distance(p1, p2):
        return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)
    
    def brute_force(points):
        min_dist = float('inf')
        pair = None
        n = len(points)
        
        for i in range(n):
            for j in range(i + 1, n):
                dist = distance(points[i], points[j])
                if dist < min_dist:
                    min_dist = dist
                    pair = (points[i], points[j])
        
        return min_dist, pair
    
    def closest_pair_rec(px, py):
        n = len(px)
        
        if n <= 3:
            return brute_force(px)
        
        mid = n // 2
        midpoint = px[mid]
        
        pyl = [point for point in py if point.x <= midpoint.x]
        pyr = [point for point in py if point.x > midpoint.x]
        
        dl, pair_l = closest_pair_rec(px[:mid], pyl)
        dr, pair_r = closest_pair_rec(px[mid:], pyr)
        
        # Find minimum of the two halves
        if dl <= dr:
            d = dl
            min_pair = pair_l
        else:
            d = dr
            min_pair = pair_r
        
        # Create strip of points close to line dividing two halves
        strip = [point for point in py if abs(point.x - midpoint.x) < d]
        
        # Find closest points in strip
        for i in range(len(strip)):
            j = i + 1
            while j < len(strip) and (strip[j].y - strip[i].y) < d:
                dist = distance(strip[i], strip[j])
                if dist < d:
                    d = dist
                    min_pair = (strip[i], strip[j])
                j += 1
        
        return d, min_pair
    
    px = sorted(points, key=lambda p: p.x)
    py = sorted(points, key=lambda p: p.y)
    
    return closest_pair_rec(px, py)

# Example usage
points = [Point(2, 3), Point(12, 30), Point(40, 50), Point(5, 1),
          Point(12, 10), Point(3, 4)]

min_distance, closest_points = closest_pair_divide_conquer(points)
print(f"Closest pair: {closest_points[0]} and {closest_points[1]}")
print(f"Distance: {min_distance}")
```

## 7. Advanced Number Theory Algorithms

### 7.1 Miller-Rabin Primality Test
```python
import random

def miller_rabin_test(n, k=5):
    """
    Miller-Rabin probabilistic primality test
    Time Complexity: O(k log^3 n)
    Space Complexity: O(1)
    """
    if n < 2:
        return False
    if n == 2 or n == 3:
        return True
    if n % 2 == 0:
        return False
    
    # Write n-1 as d * 2^r
    d = n - 1
    r = 0
    while d % 2 == 0:
        d //= 2
        r += 1
    
    # Perform k rounds of testing
    for _ in range(k):
        a = random.randrange(2, n - 1)
        x = pow(a, d, n)  # a^d mod n
        
        if x == 1 or x == n - 1:
            continue
        
        composite = True
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                composite = False
                break
        
        if composite:
            return False
    
    return True

def pollard_rho_factorization(n):
    """
    Pollard's Rho algorithm for integer factorization
    Expected Time Complexity: O(n^(1/4))
    Space Complexity: O(1)
    """
    if n <= 1:
        return []
    if n <= 3:
        return [n]
    if n % 2 == 0:
        return [2] + pollard_rho_factorization(n // 2)
    
    def f(x):
        return (x * x + 1) % n
    
    x = random.randint(2, n - 1)
    y = x
    d = 1
    
    while d == 1:
        x = f(x)
        y = f(f(y))
        d = math.gcd(abs(x - y), n)
    
    if d == n:
        return [n]  # Failed, number might be prime
    
    return pollard_rho_factorization(d) + pollard_rho_factorization(n // d)

def extended_euclidean(a, b):
    """
    Extended Euclidean Algorithm
    Returns gcd(a, b) and coefficients x, y such that ax + by = gcd(a, b)
    Time Complexity: O(log min(a, b))
    Space Complexity: O(1)
    """
    if a == 0:
        return b, 0, 1
    
    gcd, x1, y1 = extended_euclidean(b % a, a)
    x = y1 - (b // a) * x1
    y = x1
    
    return gcd, x, y

def chinese_remainder_theorem(remainders, moduli):
    """
    Chinese Remainder Theorem
    Time Complexity: O(n log M) where M is product of moduli
    Space Complexity: O(1)
    """
    if len(remainders) != len(moduli):
        return None
    
    # Check if moduli are pairwise coprime
    for i in range(len(moduli)):
        for j in range(i + 1, len(moduli)):
            if math.gcd(moduli[i], moduli[j]) != 1:
                return None
    
    total_mod = 1
    for mod in moduli:
        total_mod *= mod
    
    result = 0
    for i in range(len(remainders)):
        Mi = total_mod // moduli[i]
        gcd, yi, _ = extended_euclidean(Mi, moduli[i])
        result = (result + remainders[i] * Mi * yi) % total_mod
    
    return result

# Example usage
print(f"Is 97 prime? {miller_rabin_test(97)}")  # Output: True
print(f"Is 100 prime? {miller_rabin_test(100)}")  # Output: False

factors = pollard_rho_factorization(8051)
print(f"Factors of 8051: {factors}")

# Chinese Remainder Theorem example
remainders = [2, 3, 1]
moduli = [3, 4, 5]
result = chinese_remainder_theorem(remainders, moduli)
print(f"x ≡ {result} (mod {math.prod(moduli)})")
```

## 8. Pattern Matching in 2D

### 8.1 2D Pattern Matching using KMP
```python
def compute_lps_2d(pattern):
    """Compute LPS array for 2D pattern matching"""
    rows, cols = len(pattern), len(pattern[0])
    lps = [[0] * cols for _ in range(rows)]
    
    # Compute LPS for each row
    for i in range(rows):
        row = pattern[i]
        length = 0
        j = 1
        
        while j < cols:
            if row[j] == row[length]:
                length += 1
                lps[i][j] = length
                j += 1
            else:
                if length != 0:
                    length = lps[i][length - 1]
                else:
                    lps[i][j] = 0
                    j += 1
    
    return lps

def kmp_2d_search(text, pattern):
    """
    2D Pattern Matching using KMP algorithm
    Time Complexity: O(nm) where n,m are text dimensions
    Space Complexity: O(pq) where p,q are pattern dimensions
    """
    if not text or not pattern or not text[0] or not pattern[0]:
        return []
    
    text_rows, text_cols = len(text), len(text[0])
    pattern_rows, pattern_cols = len(pattern), len(pattern[0])
    
    if pattern_rows > text_rows or pattern_cols > text_cols:
        return []
    
    matches = []
    lps = compute_lps_2d(pattern)
    
    for start_row in range(text_rows - pattern_rows + 1):
        # Use KMP for each possible starting row
        i = 0  # text column index
        j = 0  # pattern column index
        row_matches = []
        
        while i < text_cols:
            # Check if current column matches across all pattern rows
            match = True
            for r in range(pattern_rows):
                if text[start_row + r][i] != pattern[r][j]:
                    match = False
                    break
            
            if match:
                i += 1
                j += 1
                
                if j == pattern_cols:
                    # Found complete match
                    row_matches.append(i - j)
                    j = lps[0][j - 1] if j > 0 else 0
            else:
                if j != 0:
                    j = lps[0][j - 1]
                else:
                    i += 1
        
        for col_start in row_matches:
            matches.append((start_row, col_start))
    
    return matches

def rolling_hash_2d_search(text, pattern):
    """
    2D Pattern Matching using Rolling Hash
    Time Complexity: O(nm) average case
    Space Complexity: O(1)
    """
    if not text or not pattern:
        return []
    
    text_rows, text_cols = len(text), len(text[0])
    pattern_rows, pattern_cols = len(pattern), len(pattern[0])
    
    if pattern_rows > text_rows or pattern_cols > text_cols:
        return []
    
    prime = 101
    base = 256
    
    # Compute pattern hash
    pattern_hash = 0
    power = 1
    
    for i in range(pattern_rows):
        for j in range(pattern_cols):
            pattern_hash = (pattern_hash + ord(pattern[i][j]) * power) % prime
            if i < pattern_rows - 1 or j < pattern_cols - 1:
                power = (power * base) % prime
    
    matches = []
    
    # Check each possible position
    for start_row in range(text_rows - pattern_rows + 1):
        for start_col in range(text_cols - pattern_cols + 1):
            # Compute hash for current window
            window_hash = 0
            current_power = 1
            
            for i in range(pattern_rows):
                for j in range(pattern_cols):
                    window_hash = (window_hash + 
                                 ord(text[start_row + i][start_col + j]) * current_power) % prime
                    if i < pattern_rows - 1 or j < pattern_cols - 1:
                        current_power = (current_power * base) % prime
            
            # If hashes match, verify character by character
            if window_hash == pattern_hash:
                match = True
                for i in range(pattern_rows):
                    for j in range(pattern_cols):
                        if text[start_row + i][start_col + j] != pattern[i][j]:
                            match = False
                            break
                    if not match:
                        break
                
                if match:
                    matches.append((start_row, start_col))
    
    return matches

# Example usage
text = [
    ['A', 'B', 'C', 'A', 'B'],
    ['D', 'E', 'F', 'D', 'E'],
    ['A', 'B', 'C', 'A', 'B'],
    ['G', 'H', 'I', 'G', 'H']
]

pattern = [
    ['A', 'B'],
    ['D', 'E']
]

matches_kmp = kmp_2d_search(text, pattern)
matches_hash = rolling_hash_2d_search(text, pattern)

print(f"2D KMP matches: {matches_kmp}")
print(f"2D Rolling Hash matches: {matches_hash}")
```

## Summary of Advanced Patterns

This advanced guide covers sophisticated algorithmic patterns including:

1. **Advanced String Algorithms**: Z-algorithm, Suffix arrays, Aho-Corasick for multiple pattern matching
2. **Advanced Tree Structures**: Heavy-Light Decomposition, Link-Cut Trees for dynamic trees
3. **Advanced Graph Algorithms**: Tarjan's SCC, Edmonds-Karp max flow, Hungarian algorithm
4. **Advanced Data Structures**: Splay trees, Persistent segment trees, Skip lists
5. **Advanced DP**: Digit DP, Matrix chain multiplication, Optimal BST
6. **Computational Geometry**: Graham scan convex hull, Closest pair algorithms
7. **Advanced Number Theory**: Miller-Rabin primality, Pollard's Rho factorization, Chinese Remainder Theorem
8. **2D Pattern Matching**: KMP and Rolling Hash extensions to 2D

These patterns represent some of the most sophisticated techniques in competitive programming and advanced algorithm design, suitable for complex optimization problems and research applications.

## 🔧 Universal Problem-Solving Techniques

### **Multiple Solution Approaches** (Your Example Expanded)

```python
# Problem: Remove all occurrences of 'val' from array

# Approach 1: Naive (Your approach) - O(n²) time
def removeElement_naive(nums, val):
    i = 0
    while i < len(nums):
        if nums[i] == val:
            nums.pop(i)  # Expensive O(n) operation
        else:
            i += 1
    return len(nums)

# Approach 2: Two Pointers (Optimal) - O(n) time
def removeElement_two_pointers(nums, val):
    left = 0
    for right in range(len(nums)):
        if nums[right] != val:
            nums[left] = nums[right]
            left += 1
    return left

# Approach 3: Two Pointers (Optimized for few elements to remove)
def removeElement_optimized(nums, val):
    i = 0
    n = len(nums)
    while i < n:
        if nums[i] == val:
            nums[i] = nums[n - 1]  # Replace with last element
            n -= 1  # Reduce size
        else:
            i += 1
    return n

# Approach 4: Using built-in functions
def removeElement_filter(nums, val):
    nums[:] = [x for x in nums if x != val]
    return len(nums)

# Approach 5: Reverse iteration (avoids index shifting issues)
def removeElement_reverse(nums, val):
    for i in range(len(nums) - 1, -1, -1):
        if nums[i] == val:
            nums.pop(i)
    return len(nums)
```

---

## 🎪 Advanced Problem-Solving Tricks

### **1. Transform the Problem**
```python
# Instead of "find the element", think "eliminate what we don't want"
# Instead of "check if valid", think "count invalids and compare"
# Instead of "find maximum", think "binary search on answer"
```

### **2. Work Backwards**
```python
# Dynamic Programming: Start from the end
# Tree problems: Think bottom-up
# String problems: Sometimes easier to reverse and process
```

### **3. Use Extra Space for Clarity, Then Optimize**
```python
# Step 1: Solve with HashMap/extra array
# Step 2: Optimize to constant space using math/bit manipulation
```

### **4. Convert Complex to Simple**
```python
# 2D problems → 1D (flatten coordinates)
# Multiple variables → single hash
# Complex conditions → truth tables
```

---

## 🏃‍♂️ Essential Algorithmic Patterns

### **Pattern 1: Two Pointers**
```python
# Use when: Array is sorted, or you need to compare elements

# Template:
def two_pointer_template(arr):
    left, right = 0, len(arr) - 1
    while left < right:
        # Process arr[left] and arr[right]
        if condition:
            left += 1
        else:
            right -= 1

# Variations:
# - Same direction: fast/slow pointers
# - Opposite direction: left/right pointers
# - Three pointers: for 3Sum problems
```

### **Pattern 2: Sliding Window**
```python
# Use when: Subarray/substring problems with constraints

def sliding_window_template(s, k):
    window_start = 0
    max_length = 0
    char_frequency = {}
    
    for window_end in range(len(s)):
        # Expand window
        right_char = s[window_end]
        char_frequency[right_char] = char_frequency.get(right_char, 0) + 1
        
        # Contract window if needed
        while len(char_frequency) > k:
            left_char = s[window_start]
            char_frequency[left_char] -= 1
            if char_frequency[left_char] == 0:
                del char_frequency[left_char]
            window_start += 1
        
        max_length = max(max_length, window_end - window_start + 1)
    
    return max_length
```

### **Pattern 3: Fast & Slow Pointers**
```python
# Use when: Detecting cycles, finding middle element

def has_cycle(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow == fast:
            return True
    return False
```

### **Pattern 4: Dynamic Programming**
```python
# Template for most DP problems:
def dp_template(arr):
    n = len(arr)
    # Step 1: Define dp array
    dp = [0] * n
    
    # Step 2: Base case
    dp[0] = arr[0]
    
    # Step 3: Fill the array
    for i in range(1, n):
        dp[i] = max(dp[i-1], arr[i])  # Decision logic
    
    return dp[n-1]

# Key insight: Always ask "What's the decision at each step?"
```

---

## 🧠 Mental Models & Thinking Tricks

### **1. Time Complexity Hints**
- O(1): Direct access, math formula
- O(log n): Binary search, divide & conquer
- O(n): Single pass through data
- O(n log n): Sorting, merge operations
- O(n²): Nested loops, comparing all pairs
- O(2ⁿ): Generating all subsets, brute force recursion

### **2. Space Optimization Tricks**
```python
# Instead of 2D DP array:
dp = [[0] * n for _ in range(m)]

# Use 1D array if you only need previous row:
prev = [0] * n
curr = [0] * n

# Or even better, use two variables if you only need prev element:
prev, curr = 0, 0
```

### **3. Edge Case Checklist**
```python
# Always consider:
- Empty input ([], "", None)
- Single element
- All elements are the same
- Sorted vs unsorted
- Negative numbers
- Integer overflow
- Duplicate elements
```

---

## 🎯 Problem-Specific Strategies

### **Array Problems**
```python
# Technique 1: Prefix/Suffix arrays
prefix_sum = [0] * (n + 1)
for i in range(n):
    prefix_sum[i + 1] = prefix_sum[i] + arr[i]

# Technique 2: Hash map for O(1) lookups
seen = {}
for i, num in enumerate(arr):
    if target - num in seen:
        return [seen[target - num], i]
    seen[num] = i

# Technique 3: Sort first (if order doesn't matter)
arr.sort()  # Often simplifies the problem
```

### **String Problems**
```python
# Technique 1: Character frequency
from collections import Counter
freq = Counter(s)

# Technique 2: Sliding window for substrings
# Technique 3: Two pointers for palindromes
def is_palindrome(s):
    left, right = 0, len(s) - 1
    while left < right:
        if s[left] != s[right]:
            return False
        left += 1
        right -= 1
    return True
```

### **Tree Problems**
```python
# Template for most tree problems:
def tree_problem(root):
    if not root:
        return base_case
    
    left_result = tree_problem(root.left)
    right_result = tree_problem(root.right)
    
    # Combine results
    return combine(left_result, right_result, root.val)

# Common patterns:
# - Path sum: Keep track of current sum
# - Tree depth: Return max(left, right) + 1
# - Tree diameter: Use global variable for max path
```

### **Graph Problems**
```python
# DFS Template:
def dfs(graph, node, visited):
    if node in visited:
        return
    visited.add(node)
    
    for neighbor in graph[node]:
        dfs(graph, neighbor, visited)

# BFS Template:
from collections import deque
def bfs(graph, start):
    queue = deque([start])
    visited = {start}
    
    while queue:
        node = queue.popleft()
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
```

---

## 🚀 Advanced Optimization Techniques

### **1. Bit Manipulation Tricks**
```python
# Check if power of 2:
def is_power_of_2(n):
    return n > 0 and (n & (n - 1)) == 0

# Get rightmost set bit:
rightmost_bit = n & (-n)

# XOR tricks for finding unique elements:
# a ^ a = 0, a ^ 0 = a
```

### **2. Mathematical Insights**
```python
# Pigeonhole principle: n+1 items, n boxes → duplicate exists
# Sum formula: sum(1 to n) = n * (n + 1) / 2
# Missing number: expected_sum - actual_sum
```

### **3. Preprocessing Tricks**
```python
# Sort the input first
# Build frequency map
# Create prefix sums
# Use auxiliary data structures (heap, stack, queue)
```

---

## 📋 Problem-Solving Checklist

### **Before Coding:**
1. ✅ Understand the problem completely
2. ✅ Identify the pattern/technique needed
3. ✅ Think of multiple approaches
4. ✅ Choose the best approach considering constraints
5. ✅ Write pseudocode first

### **While Coding:**
1. ✅ Use meaningful variable names
2. ✅ Handle edge cases
3. ✅ Add comments for complex logic
4. ✅ Test with example inputs mentally

### **After Coding:**
1. ✅ Trace through your code
2. ✅ Check time and space complexity
3. ✅ Think of optimizations
4. ✅ Consider alternative approaches

---

## 🎨 Code Style & Best Practices

### **Clean Code Principles**
```python
# Bad:
def func(a, b):
    c = []
    for i in range(len(a)):
        if a[i] != b:
            c.append(a[i])
    return len(c)

# Good:
def remove_element(nums, target_val):
    """Remove all occurrences of target_val from nums in-place."""
    write_index = 0
    
    for read_index in range(len(nums)):
        if nums[read_index] != target_val:
            nums[write_index] = nums[read_index]
            write_index += 1
    
    return write_index
```

### **Performance Considerations**
- Use `collections.deque` for O(1) front operations
- Use `bisect` module for sorted list operations
- Use `collections.Counter` for frequency counting
- Use `collections.defaultdict` to avoid key checks

---

## 🎯 Final Tips

1. **Practice Pattern Recognition**: Most problems follow 15-20 common patterns
2. **Start Simple**: Get a working solution first, then optimize
3. **Think in Multiple Ways**: Brute force → Optimize → Alternative approach
4. **Use Built-ins Wisely**: Know when to use vs when to implement from scratch
5. **Time vs Space Trade-offs**: Understand when to sacrifice one for the other
6. **Mock Interview Practice**: Explain your thinking process out loud

Remember: The goal isn't just to solve the problem, but to solve it **efficiently** and **elegantly** while being able to **explain your reasoning** clearly.

# Advanced DSA Mastery: Expert-Level Strategies & Hidden Techniques

## 🧬 Advanced Pattern Recognition Beyond the Basics

### **Meta-Patterns: Patterns Within Patterns**

#### **1. Monotonic Stack/Queue Pattern**
```python
# When: Need to find next/previous greater/smaller element
def next_greater_element(nums):
    stack = []  # Store indices
    result = [-1] * len(nums)
    
    for i in range(len(nums)):
        while stack and nums[i] > nums[stack[-1]]:
            idx = stack.pop()
            result[idx] = nums[i]
        stack.append(i)
    
    return result

# Applications:
# - Largest rectangle in histogram
# - Trapping rain water
# - Daily temperatures
# - Stock span problem
```

#### **2. Union-Find (Disjoint Set) Pattern**
```python
class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.components = n
    
    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # Path compression
        return self.parent[x]
    
    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px == py:
            return False
        
        # Union by rank
        if self.rank[px] < self.rank[py]:
            px, py = py, px
        self.parent[py] = px
        if self.rank[px] == self.rank[py]:
            self.rank[px] += 1
        
        self.components -= 1
        return True

# When to use: Connected components, cycle detection, MST
```

#### **3. Topological Sort Pattern**
```python
from collections import defaultdict, deque

def topological_sort(graph):
    # Kahn's Algorithm
    in_degree = defaultdict(int)
    
    # Calculate in-degrees
    for node in graph:
        for neighbor in graph[node]:
            in_degree[neighbor] += 1
    
    # Start with nodes having 0 in-degree
    queue = deque([node for node in graph if in_degree[node] == 0])
    result = []
    
    while queue:
        node = queue.popleft()
        result.append(node)
        
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    return result if len(result) == len(graph) else []  # Cycle detection

# Applications: Course scheduling, build systems, dependency resolution
```

---

## 🎭 Problem Transformation Techniques

### **1. Coordinate Compression**
```python
# When: Large coordinate space, but few actual points
def compress_coordinates(points):
    xs = sorted(set(x for x, y in points))
    ys = sorted(set(y for x, y in points))
    
    x_map = {x: i for i, x in enumerate(xs)}
    y_map = {y: i for i, y in enumerate(ys)}
    
    return [(x_map[x], y_map[y]) for x, y in points]

# Reduces O(max_coordinate) to O(num_points)
```

### **2. State Space Reduction**
```python
# Instead of tracking all possible states, use mathematical properties

# Example: Instead of simulating entire game
def winner_prediction(n):
    # Mathematical insight: Winner determined by n % 3
    return "Alice" if n % 3 != 0 else "Bob"

# Look for:
# - Cycles in state transitions
# - Mathematical patterns
# - Invariants that don't change
```

### **3. Dimension Reduction**
```python
# 2D → 1D mapping
def matrix_to_1d(i, j, cols):
    return i * cols + j

def one_d_to_matrix(idx, cols):
    return idx // cols, idx % cols

# Useful for:
# - Matrix problems with BFS/DFS
# - Dynamic programming on grids
# - Union-Find on 2D grids
```

---

## 🔬 Advanced Data Structure Techniques

### **1. Segment Tree with Lazy Propagation**
```python
class LazySegmentTree:
    def __init__(self, arr):
        self.n = len(arr)
        self.tree = [0] * (4 * self.n)
        self.lazy = [0] * (4 * self.n)
        self.build(arr, 0, 0, self.n - 1)
    
    def build(self, arr, node, start, end):
        if start == end:
            self.tree[node] = arr[start]
        else:
            mid = (start + end) // 2
            self.build(arr, 2*node+1, start, mid)
            self.build(arr, 2*node+2, mid+1, end)
            self.tree[node] = self.tree[2*node+1] + self.tree[2*node+2]
    
    def push_lazy(self, node, start, end):
        if self.lazy[node] != 0:
            self.tree[node] += (end - start + 1) * self.lazy[node]
            if start != end:
                self.lazy[2*node+1] += self.lazy[node]
                self.lazy[2*node+2] += self.lazy[node]
            self.lazy[node] = 0
    
    def range_update(self, node, start, end, l, r, val):
        self.push_lazy(node, start, end)
        if start > r or end < l:
            return
        
        if start >= l and end <= r:
            self.tree[node] += (end - start + 1) * val
            if start != end:
                self.lazy[2*node+1] += val
                self.lazy[2*node+2] += val
            return
        
        mid = (start + end) // 2
        self.range_update(2*node+1, start, mid, l, r, val)
        self.range_update(2*node+2, mid+1, end, l, r, val)
        
        self.push_lazy(2*node+1, start, mid)
        self.push_lazy(2*node+2, mid+1, end)
        self.tree[node] = self.tree[2*node+1] + self.tree[2*node+2]

# When: Range updates + range queries in O(log n)
```

### **2. Fenwick Tree (Binary Indexed Tree) Variations**
```python
class FenwickTree:
    def __init__(self, n):
        self.n = n
        self.tree = [0] * (n + 1)
    
    def update(self, i, delta):
        while i <= self.n:
            self.tree[i] += delta
            i += i & (-i)  # Add least significant bit
    
    def query(self, i):
        result = 0
        while i > 0:
            result += self.tree[i]
            i -= i & (-i)  # Remove least significant bit
        return result
    
    def range_query(self, l, r):
        return self.query(r) - self.query(l - 1)

# 2D Fenwick Tree for matrix range sums
class FenwickTree2D:
    def __init__(self, matrix):
        self.rows, self.cols = len(matrix), len(matrix[0])
        self.tree = [[0] * (self.cols + 1) for _ in range(self.rows + 1)]
        
        for i in range(self.rows):
            for j in range(self.cols):
                self.update(i + 1, j + 1, matrix[i][j])
    
    def update(self, r, c, delta):
        while r <= self.rows:
            j = c
            while j <= self.cols:
                self.tree[r][j] += delta
                j += j & (-j)
            r += r & (-r)
```

### **3. Trie with Advanced Operations**
```python
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_word = False
        self.count = 0  # Number of words passing through this node
        self.word_count = 0  # Number of times this word appears

class AdvancedTrie:
    def __init__(self):
        self.root = TrieNode()
    
    def insert(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
            node.count += 1
        node.is_word = True
        node.word_count += 1
    
    def count_with_prefix(self, prefix):
        node = self.root
        for char in prefix:
            if char not in node.children:
                return 0
            node = node.children[char]
        return node.count
    
    def auto_complete(self, prefix, limit=5):
        def dfs(node, current_word, results):
            if len(results) >= limit:
                return
            if node.is_word:
                results.append(current_word)
            
            for char in sorted(node.children.keys()):
                dfs(node.children[char], current_word + char, results)
        
        node = self.root
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]
        
        results = []
        dfs(node, prefix, results)
        return results
```

---

## 🎯 Advanced Algorithmic Strategies

### **1. Meet-in-the-Middle Technique**
```python
# When: Brute force is O(2^n) but n ≤ 40
def subset_sum_meet_middle(arr, target):
    n = len(arr)
    mid = n // 2
    
    # Generate all subset sums for first half
    def generate_sums(start, end):
        sums = []
        for mask in range(1 << (end - start)):
            total = 0
            for i in range(end - start):
                if mask & (1 << i):
                    total += arr[start + i]
            sums.append(total)
        return sorted(sums)
    
    left_sums = generate_sums(0, mid)
    right_sums = generate_sums(mid, n)
    
    # Two pointers to find target
    i, j = 0, len(right_sums) - 1
    while i < len(left_sums) and j >= 0:
        current_sum = left_sums[i] + right_sums[j]
        if current_sum == target:
            return True
        elif current_sum < target:
            i += 1
        else:
            j -= 1
    
    return False
# Reduces O(2^n) to O(2^(n/2))
```

### **2. Sqrt Decomposition**
```python
import math

class SqrtDecomposition:
    def __init__(self, arr):
        self.arr = arr[:]
        self.n = len(arr)
        self.block_size = int(math.sqrt(self.n))
        self.blocks = []
        
        # Precompute block sums
        for i in range(0, self.n, self.block_size):
            self.blocks.append(sum(arr[i:i + self.block_size]))
    
    def update(self, idx, val):
        block_idx = idx // self.block_size
        self.blocks[block_idx] += val - self.arr[idx]
        self.arr[idx] = val
    
    def range_sum(self, l, r):
        result = 0
        
        # Left partial block
        while l <= r and l % self.block_size != 0:
            result += self.arr[l]
            l += 1
        
        # Complete blocks
        while l + self.block_size <= r + 1:
            result += self.blocks[l // self.block_size]
            l += self.block_size
        
        # Right partial block
        while l <= r:
            result += self.arr[l]
            l += 1
        
        return result

# O(√n) updates and queries - good middle ground
```

### **3. Heavy-Light Decomposition (Trees)**
```python
class HeavyLightDecomposition:
    def __init__(self, n):
        self.n = n
        self.adj = [[] for _ in range(n)]
        self.heavy = [-1] * n
        self.depth = [0] * n
        self.parent = [-1] * n
        self.size = [0] * n
        self.head = [0] * n
        self.pos = [0] * n
        self.cur_pos = 0
    
    def add_edge(self, u, v):
        self.adj[u].append(v)
        self.adj[v].append(u)
    
    def dfs_size(self, v, p):
        self.size[v] = 1
        self.parent[v] = p
        max_child_size = 0
        
        for u in self.adj[v]:
            if u != p:
                self.depth[u] = self.depth[v] + 1
                self.dfs_size(u, v)
                self.size[v] += self.size[u]
                
                if self.size[u] > max_child_size:
                    max_child_size = self.size[u]
                    self.heavy[v] = u
    
    def dfs_decompose(self, v, h):
        self.head[v] = h
        self.pos[v] = self.cur_pos
        self.cur_pos += 1
        
        if self.heavy[v] != -1:
            self.dfs_decompose(self.heavy[v], h)
        
        for u in self.adj[v]:
            if u != self.parent[v] and u != self.heavy[v]:
                self.dfs_decompose(u, u)
    
    def path_query(self, u, v):
        # Query path from u to v in O(log²n)
        result = 0
        while self.head[u] != self.head[v]:
            if self.depth[self.head[u]] > self.depth[self.head[v]]:
                u, v = v, u
            
            # Query segment [pos[head[v]], pos[v]]
            result += self.segment_tree_query(self.pos[self.head[v]], self.pos[v])
            v = self.parent[self.head[v]]
        
        if self.depth[u] > self.depth[v]:
            u, v = v, u
        
        result += self.segment_tree_query(self.pos[u], self.pos[v])
        return result

# Enables O(log²n) path queries on trees
```

---

## 🧮 Mathematical & Number Theory Techniques

### **1. Extended Euclidean Algorithm**
```python
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

# Applications: Modular arithmetic, cryptography, Chinese remainder theorem
```

### **2. Fast Matrix Exponentiation**
```python
def matrix_multiply(A, B, mod=None):
    n, m, p = len(A), len(B), len(B[0])
    C = [[0] * p for _ in range(n)]
    
    for i in range(n):
        for j in range(p):
            for k in range(m):
                C[i][j] += A[i][k] * B[k][j]
                if mod:
                    C[i][j] %= mod
    return C

def matrix_power(matrix, n, mod=None):
    size = len(matrix)
    result = [[1 if i == j else 0 for j in range(size)] for i in range(size)]
    base = [row[:] for row in matrix]
    
    while n > 0:
        if n & 1:
            result = matrix_multiply(result, base, mod)
        base = matrix_multiply(base, base, mod)
        n >>= 1
    
    return result

# Applications: Fibonacci in O(log n), linear recurrence relations
def fibonacci(n):
    if n <= 1:
        return n
    
    fib_matrix = [[1, 1], [1, 0]]
    result = matrix_power(fib_matrix, n - 1)
    return result[0][0]
```

### **3. Polynomial Hashing**
```python
class PolynomialHash:
    def __init__(self, s, base=31, mod=10**9 + 7):
        self.n = len(s)
        self.base = base
        self.mod = mod
        
        # Precompute hash values and powers
        self.hash_values = [0] * (self.n + 1)
        self.powers = [1] * (self.n + 1)
        
        for i in range(self.n):
            self.hash_values[i + 1] = (self.hash_values[i] * base + ord(s[i])) % mod
            self.powers[i + 1] = (self.powers[i] * base) % mod
    
    def get_hash(self, l, r):
        # Hash of substring s[l:r+1]
        result = (self.hash_values[r + 1] - self.hash_values[l] * self.powers[r - l + 1]) % self.mod
        return (result + self.mod) % self.mod
    
    def compare(self, l1, r1, l2, r2):
        return self.get_hash(l1, r1) == self.get_hash(l2, r2)

# Applications: String matching, longest common substring, rolling hash
```

---

## 🎪 Advanced Problem-Solving Heuristics

### **1. Invariant-Based Thinking**
```python
# Look for properties that remain constant throughout algorithm execution

# Example: In array rotation problems
def rotate_invariant(arr, k):
    # Invariant: (i + k) % n gives new position
    n = len(arr)
    k %= n
    
    def gcd(a, b):
        return a if b == 0 else gcd(b, a % b)
    
    cycles = gcd(n, k)
    for start in range(cycles):
        current = start
        prev = arr[start]
        
        while True:
            next_pos = (current + k) % n
            arr[next_pos], prev = prev, arr[next_pos]
            current = next_pos
            
            if current == start:
                break
```

### **2. Greedy Choice Property Identification**
```python
# Template for proving greedy algorithms work:
def greedy_template(items):
    # Step 1: Sort by greedy criterion
    items.sort(key=lambda x: greedy_criterion(x))
    
    # Step 2: Make greedy choices
    result = []
    for item in items:
        if is_safe_choice(item, result):
            result.append(item)
    
    return result

# Common greedy criteria:
# - Earliest deadline first
# - Shortest job first
# - Highest value/weight ratio
# - Furthest reach first
```

### **3. Amortized Analysis Techniques**
```python
# Example: Dynamic Array with table doubling
class DynamicArray:
    def __init__(self):
        self.capacity = 1
        self.size = 0
        self.data = [None] * self.capacity
    
    def append(self, item):
        if self.size == self.capacity:
            # Resize operation: O(n) worst case, but O(1) amortized
            old_data = self.data
            self.capacity *= 2
            self.data = [None] * self.capacity
            for i in range(self.size):
                self.data[i] = old_data[i]
        
        self.data[self.size] = item
        self.size += 1

# Potential function analysis:
# Φ(D) = 2 * size - capacity
# Amortized cost = actual cost + Φ(D_i) - Φ(D_{i-1})
```

---

## 🔍 Advanced Search & Optimization

### **1. Ternary Search**
```python
def ternary_search(f, left, right, eps=1e-9):
    """Find maximum of unimodal function f in range [left, right]"""
    while right - left > eps:
        m1 = left + (right - left) / 3
        m2 = right - (right - left) / 3
        
        if f(m1) < f(m2):
            left = m1
        else:
            right = m2
    
    return (left + right) / 2

# Applications: Finding maximum/minimum of unimodal functions
```

### **2. Parallel Binary Search**
```python
def parallel_binary_search(queries, check_function):
    """Answer multiple binary search queries efficiently"""
    n = len(queries)
    answers = [-1] * n
    
    # Initialize search ranges
    left = [0] * n
    right = [max_possible_answer] * n
    
    while True:
        # Group queries by their middle points
        mid_groups = {}
        active_queries = []
        
        for i in range(n):
            if left[i] <= right[i]:
                mid = (left[i] + right[i]) // 2
                if mid not in mid_groups:
                    mid_groups[mid] = []
                mid_groups[mid].append(i)
                active_queries.append(i)
        
        if not active_queries:
            break
        
        # Process each group
        for mid, query_indices in mid_groups.items():
            can_achieve = check_function(mid, query_indices)
            
            for i, idx in enumerate(query_indices):
                if can_achieve[i]:
                    answers[idx] = mid
                    right[idx] = mid - 1
                else:
                    left[idx] = mid + 1
    
    return answers
```

### **3. Simulated Annealing**
```python
import random
import math

def simulated_annealing(initial_state, cost_function, neighbor_function, 
                       initial_temp=1000, cooling_rate=0.95, min_temp=1):
    current_state = initial_state
    current_cost = cost_function(current_state)
    best_state = current_state
    best_cost = current_cost
    
    temperature = initial_temp
    
    while temperature > min_temp:
        # Generate neighbor
        neighbor = neighbor_function(current_state)
        neighbor_cost = cost_function(neighbor)
        
        # Decide whether to accept neighbor
        if neighbor_cost < current_cost:
            current_state = neighbor
            current_cost = neighbor_cost
            
            if neighbor_cost < best_cost:
                best_state = neighbor
                best_cost = neighbor_cost
        else:
            # Accept with probability based on temperature
            probability = math.exp(-(neighbor_cost - current_cost) / temperature)
            if random.random() < probability:
                current_state = neighbor
                current_cost = neighbor_cost
        
        temperature *= cooling_rate
    
    return best_state, best_cost

# Applications: TSP, job scheduling, optimization problems
```

---

## 🎨 Code Optimization Techniques

### **1. Loop Unrolling & Vectorization**
```python
# Instead of:
def sum_slow(arr):
    total = 0
    for x in arr:
        total += x
    return total

# Use built-in optimized functions:
def sum_fast(arr):
    return sum(arr)  # Implemented in C

# Manual unrolling for specific cases:
def sum_unrolled(arr):
    total = 0
    i = 0
    
    # Process 4 elements at a time
    while i + 3 < len(arr):
        total += arr[i] + arr[i+1] + arr[i+2] + arr[i+3]
        i += 4
    
    # Handle remaining elements
    while i < len(arr):
        total += arr[i]
        i += 1
    
    return total
```

### **2. Memoization Patterns**
```python
from functools import lru_cache
import sys

# Method 1: Decorator-based
@lru_cache(maxsize=None)
def fibonacci_memo(n):
    if n <= 1:
        return n
    return fibonacci_memo(n-1) + fibonacci_memo(n-2)

# Method 2: Manual memoization with custom key
class Memoize:
    def __init__(self, func):
        self.func = func
        self.cache = {}
    
    def __call__(self, *args, **kwargs):
        key = (args, tuple(sorted(kwargs.items())))
        if key not in self.cache:
            self.cache[key] = self.func(*args, **kwargs)
        return self.cache[key]

# Method 3: Bottom-up to avoid recursion limits
def fibonacci_iterative(n):
    if n <= 1:
        return n
    
    dp = [0] * (n + 1)
    dp[1] = 1
    
    for i in range(2, n + 1):
        dp[i] = dp[i-1] + dp[i-2]
    
    return dp[n]
```

### **3. Bit Manipulation Optimizations**
```python
# Fast operations using bit manipulation

def is_power_of_4(n):
    # Must be power of 2 and have odd position bit set
    return n > 0 and (n & (n - 1)) == 0 and (n & 0x55555555) != 0

def count_set_bits(n):
    # Brian Kernighan's algorithm
    count = 0
    while n:
        n &= n - 1  # Remove rightmost set bit
        count += 1
    return count

def reverse_bits(n):
    result = 0
    for _ in range(32):
        result = (result << 1) | (n & 1)
        n >>= 1
    return result

def find_single_number(arr):
    # All numbers appear twice except one
    result = 0
    for num in arr:
        result ^= num
    return result

def find_two_single_numbers(arr):
    # All numbers appear twice except two
    xor_all = 0
    for num in arr:
        xor_all ^= num
    
    # Find rightmost set bit in XOR result
    rightmost_bit = xor_all & (-xor_all)
    
    num1 = num2 = 0
    for num in arr:
        if num & rightmost_bit:
            num1 ^= num
        else:
            num2 ^= num
    
    return num1, num2
```

---

## 🚀 Competition Programming Tricks

### **1. Fast I/O Templates**
```python
import sys
from collections import defaultdict, deque, Counter
from bisect import bisect_left, bisect_right
import heapq

# Fast input
def fast_input():
    return sys.stdin.readline().strip()

def fast_int():
    return int(sys.stdin.readline())

def fast_ints():
    return list(map(int, sys.stdin.readline().split()))

def fast_float():
    return float(sys.stdin.readline())

# Fast output
def fast_print(*args, sep=' ', end='\n'):
    sys.stdout.write(sep.join(map(str, args)) + end)

# Template for multiple test cases
def solve():
    # Your solution here
    pass

def main():
    t = fast_int()  # Number of test cases
    for _ in range(t):
        solve()

if __name__ == "__main__":
    main()
```

### **2. Coordinate Compression with Discretization**
```python
def coordinate_compress(points):
    # Extract and sort unique coordinates
    x_coords = sorted(set(p[0] for p in points))
    y_coords = sorted(set(p[1] for p in points))
    
    # Create mappings
    x_map = {x: i for i, x in enumerate(x_coords)}
    y_map = {y: i for i, y in enumerate(y_coords)}
    
    # Compress points
    compressed = [(x_map[p[0]], y_map[p[1]]) for p in points]
    
    return compressed, x_coords, y_coords

# Applications: Range queries on sparse data, 2D problems with large coordinates
```

### **3. Mo's Algorithm for Range Queries**
```python
import math

class MoAlgorithm:
    def __init__(self, arr, queries):
        self.arr = arr
        self.n = len(arr)
        self.queries = queries
        self.block_size = int(math.sqrt(self.n))
        
        # Sort queries by Mo's order
        self.queries.sort(key=lambda q: (q[0] // self.block_size, q[1]))
        
        self.frequency = [0] * (max(arr) + 1)
        self.current_answer = 0
    
    def add(self, idx):
        val = self.arr[idx]
        self.frequency[val] += 1
        if self.frequency[val] == 1:
            self.current_answer += 1
    
    def remove(self, idx):
        val = self.arr[idx]
        self.frequency[val] -= 1
        if self.frequency[val] == 0:
            self.current_answer -= 1
    
    def solve(self):
        answers = [0] * len(self.queries)
        current_l, current_r = 0, -1
        
        for i, (l, r) in enumerate(self.queries):
            # Extend right
            while current_r < r:
                current_r += 1
                self.add(current_r)
            
            # Shrink right
            while current_r > r:
                self.remove(current_r)
                current_r -= 1
            
            # Extend left
            while current_l > l:
                current_l -= 1
                self.add(current_l)
            
            # Shrink left
            while current_l < l:
                self.remove(current_l)
                current_l += 1
            
            answers[i] = self.current_answer
        
        return answers

# O((N + Q) * √N) for Q queries on array of size N
```

---

## 🎲 Randomized Algorithms & Probabilistic Techniques

### **1. Randomized QuickSelect**
```python
import random

def randomized_quickselect(arr, k):
    """Find kth smallest element in O(n) average time"""
    def partition(arr, low, high, pivot_idx):
        # Move pivot to end
        arr[pivot_idx], arr[high] = arr[high], arr[pivot_idx]
        pivot = arr[high]
        
        i = low - 1
        for j in range(low, high):
            if arr[j] <= pivot:
                i += 1
                arr[i], arr[j] = arr[j], arr[i]
        
        arr[i + 1], arr[high] = arr[high], arr[i + 1]
        return i + 1
    
    def quickselect(arr, low, high, k):
        if low == high:
            return arr[low]
        
        # Randomized pivot selection
        pivot_idx = random.randint(low, high)
        pivot_idx = partition(arr, low, high, pivot_idx)
        
        if k == pivot_idx:
            return arr[k]
        elif k < pivot_idx:
            return quickselect(arr, low, pivot_idx - 1, k)
        else:
            return quickselect(arr, pivot_idx + 1, high, k)
    
    return quickselect(arr, 0, len(arr) - 1, k)
```

### **2. Bloom Filter**
```python
import hashlib
import math

class BloomFilter:
    def __init__(self, capacity, error_rate=0.1):
        self.capacity = capacity
        self.error_rate = error_rate
        
        # Calculate optimal parameters
        self.bit_array_size = int(-capacity * math.log(error_rate) / (math.log(2) ** 2))
        self.hash_count = int(self.bit_array_size * math.log(2) / capacity)
        
        self.bit_array = [False] * self.bit_array_size
    
    def _hash(self, item, seed):
        return int(hashlib.md5((str(item) + str(seed)).encode()).hexdigest(), 16) % self.bit_array_size
    
    def add(self, item):
        for i in range(self.hash_count):
            index = self._hash(item, i)
            self.bit_array[index] = True
    
    def contains(self, item):
        for i in range(self.hash_count):
            index = self._hash(item, i)
            if not self.bit_array[index]:
                return False
        return True  # Probably contains (false positives possible)

# Applications: Checking membership with space efficiency, web crawling
```

### **3. Skip List**
```python
import random

class SkipListNode:
    def __init__(self, value, level):
        self.value = value
        self.forward = [None] * (level + 1)

class SkipList:
    def __init__(self, max_level=16, p=0.5):
        self.max_level = max_level
        self.p = p
        self.header = SkipListNode(float('-inf'), max_level)
        self.level = 0
    
    def random_level(self):
        level = 0
        while random.random() < self.p and level < self.max_level:
            level += 1
        return level
    
    def search(self, target):
        current = self.header
        
        for i in range(self.level, -1, -1):
            while current.forward[i] and current.forward[i].value < target:
                current = current.forward[i]
        
        current = current.forward[0]
        return current and current.value == target
    
    def insert(self, value):
        update = [None] * (self.max_level + 1)
        current = self.header
        
        # Find insertion point at each level
        for i in range(self.level, -1, -1):
            while current.forward[i] and current.forward[i].value < value:
                current = current.forward[i]
            update[i] = current
        
        current = current.forward[0]
        
        if not current or current.value != value:
            new_level = self.random_level()
            
            if new_level > self.level:
                for i in range(self.level + 1, new_level + 1):
                    update[i] = self.header
                self.level = new_level
            
            new_node = SkipListNode(value, new_level)
            for i in range(new_level + 1):
                new_node.forward[i] = update[i].forward[i]
                update[i].forward[i] = new_node

# O(log n) average case for search, insert, delete
```

---

## 🌊 Advanced Dynamic Programming Patterns

### **1. Digit DP (Digit Dynamic Programming)**
```python
def count_numbers_with_property(n):
    """Count numbers <= n with specific digit properties"""
    s = str(n)
    memo = {}
    
    def dp(pos, tight, started, state):
        if pos == len(s):
            return 1 if started else 0
        
        if (pos, tight, started, state) in memo:
            return memo[(pos, tight, started, state)]
        
        limit = int(s[pos]) if tight else 9
        result = 0
        
        for digit in range(0, limit + 1):
            new_tight = tight and (digit == limit)
            new_started = started or (digit > 0)
            new_state = update_state(state, digit) if new_started else state
            
            if not new_started or is_valid_state(new_state):
                result += dp(pos + 1, new_tight, new_started, new_state)
        
        memo[(pos, tight, started, state)] = result
        return result
    
    return dp(0, True, False, initial_state())

# Applications: Count numbers with specific digit patterns, sum of digits
```

### **2. Profile DP (Bitmask DP on rows/columns)**
```python
def tiling_ways(n, m):
    """Count ways to tile n×m board with 1×2 dominoes"""
    # Use bitmask to represent column profile
    dp = [{} for _ in range(n + 1)]
    dp[0][0] = 1  # Base case: empty board
    
    for i in range(n):
        for mask in dp[i]:
            fill_column(i, mask, 0, 0, dp[i][mask], dp[i + 1])
    
    return dp[n].get(0, 0)

def fill_column(col, mask, pos, new_mask, ways, next_dp):
    if pos == m:
        # Completed current column
        next_dp[new_mask] = next_dp.get(new_mask, 0) + ways
        return
    
    if mask & (1 << pos):
        # Cell already filled by previous column
        fill_column(col, mask, pos + 1, new_mask, ways, next_dp)
    else:
        # Place vertical domino (extends to next column)
        fill_column(col, mask, pos + 1, new_mask | (1 << pos), ways, next_dp)
        
        # Place horizontal domino (if next cell is empty)
        if pos + 1 < m and not (mask & (1 << (pos + 1))):
            fill_column(col, mask | (1 << (pos + 1)), pos + 2, new_mask, ways, next_dp)
```

### **3. Tree DP with Rerooting**
```python
def tree_dp_rerooting(graph, n):
    """Compute answer for each node as root efficiently"""
    # Phase 1: Compute subtree answers with arbitrary root
    subtree_ans = [0] * n
    visited = [False] * n
    
    def dfs1(node, parent):
        visited[node] = True
        subtree_ans[node] = base_value(node)
        
        for neighbor in graph[node]:
            if neighbor != parent:
                dfs1(neighbor, node)
                subtree_ans[node] = combine(subtree_ans[node], subtree_ans[neighbor])
    
    # Phase 2: Reroot and compute answers for all nodes
    final_ans = [0] * n
    
    def dfs2(node, parent, parent_contribution):
        # Combine subtree answer with parent contribution
        final_ans[node] = combine(subtree_ans[node], parent_contribution)
        
        for neighbor in graph[node]:
            if neighbor != parent:
                # Calculate contribution from node to neighbor
                remaining = remove_subtree(final_ans[node], subtree_ans[neighbor])
                dfs2(neighbor, node, remaining)
    
    dfs1(0, -1)
    dfs2(0, -1, identity_value())
    
    return final_ans

# Applications: Sum of distances, tree diameter from each node
```

---

## 🔮 Advanced String Algorithms

### **1. Z-Algorithm**
```python
def z_algorithm(s):
    """Compute Z array: Z[i] = length of longest substring starting at i that is also prefix"""
    n = len(s)
    z = [0] * n
    z[0] = n
    
    l, r = 0, 0  # Current Z-box boundaries
    
    for i in range(1, n):
        if i <= r:
            z[i] = min(r - i + 1, z[i - l])
        
        while i + z[i] < n and s[z[i]] == s[i + z[i]]:
            z[i] += 1
        
        if i + z[i] - 1 > r:
            l, r = i, i + z[i] - 1
    
    return z

def pattern_matching_z(text, pattern):
    """Find all occurrences of pattern in text using Z-algorithm"""
    combined = pattern + ' + text
    z = z_algorithm(combined)
    
    pattern_len = len(pattern)
    occurrences = []
    
    for i in range(pattern_len + 1, len(combined)):
        if z[i] == pattern_len:
            occurrences.append(i - pattern_len - 1)
    
    return occurrences
```

### **2. Suffix Array with LCP**
```python
def build_suffix_array(s):
    """Build suffix array using radix sort approach"""
    n = len(s)
    s += chr(0)  # Add sentinel
    
    # Initial ranking based on first character
    rank = [ord(c) for c in s]
    temp_rank = [0] * (n + 1)
    sa = list(range(n + 1))
    
    k = 1
    while k <= n:
        # Sort by second key, then by first key
        sa.sort(key=lambda x: (rank[x], rank[(x + k) % (n + 1)]))
        
        temp_rank[sa[0]] = 0
        for i in range(1, n + 1):
            prev_pair = (rank[sa[i-1]], rank[(sa[i-1] + k) % (n + 1)])
            curr_pair = (rank[sa[i]], rank[(sa[i] + k) % (n + 1)])
            
            temp_rank[sa[i]] = temp_rank[sa[i-1]]
            if prev_pair != curr_pair:
                temp_rank[sa[i]] += 1
        
        rank = temp_rank[:]
        k *= 2
    
    return sa[1:]  # Remove sentinel

def build_lcp_array(s, sa):
    """Build LCP array using Kasai's algorithm"""
    n = len(s)
    rank = [0] * n
    lcp = [0] * (n - 1)
    
    # Build rank array
    for i in range(n):
        rank[sa[i]] = i
    
    h = 0
    for i in range(n):
        if rank[i] > 0:
            j = sa[rank[i] - 1]
            while i + h < n and j + h < n and s[i + h] == s[j + h]:
                h += 1
            lcp[rank[i] - 1] = h
            if h > 0:
                h -= 1
    
    return lcp
```

### **3. Aho-Corasick Algorithm**
```python
from collections import deque, defaultdict

class AhoCorasick:
    def __init__(self, patterns):
        self.trie = defaultdict(dict)
        self.failure = defaultdict(int)
        self.output = defaultdict(list)
        self.patterns = patterns
        self.build_trie()
        self.build_failure_function()
    
    def build_trie(self):
        for i, pattern in enumerate(self.patterns):
            node = 0
            for char in pattern:
                if char not in self.trie[node]:
                    self.trie[node][char] = len(self.trie)
                node = self.trie[node][char]
            self.output[node].append(i)
    
    def build_failure_function(self):
        queue = deque()
        
        # Initialize failure function for depth 1
        for char in self.trie[0]:
            node = self.trie[0][char]
            self.failure[node] = 0
            queue.append(node)
        
        while queue:
            current = queue.popleft()
            
            for char in self.trie[current]:
                child = self.trie[current][char]
                queue.append(child)
                
                # Find failure link
                temp = self.failure[current]
                while temp != 0 and char not in self.trie[temp]:
                    temp = self.failure[temp]
                
                if char in self.trie[temp]:
                    self.failure[child] = self.trie[temp][char]
                else:
                    self.failure[child] = 0
                
                # Inherit output from failure link
                self.output[child].extend(self.output[self.failure[child]])
    
    def search(self, text):
        matches = []
        node = 0
        
        for i, char in enumerate(text):
            while node != 0 and char not in self.trie[node]:
                node = self.failure[node]
            
            if char in self.trie[node]:
                node = self.trie[node][char]
            
            for pattern_idx in self.output[node]:
                pattern = self.patterns[pattern_idx]
                start = i - len(pattern) + 1
                matches.append((start, pattern_idx, pattern))
        
        return matches

# Applications: Multiple pattern matching, virus scanning, DNA sequence analysis
```

---

## 🎪 Advanced Tree Algorithms

### **1. Link-Cut Tree**
```python
class LCTNode:
    def __init__(self, value):
        self.value = value
        self.parent = None
        self.left = None
        self.right = None
        self.flipped = False
        self.subtree_sum = value
        self.path_sum = value

class LinkCutTree:
    def __init__(self):
        pass
    
    def is_root(self, node):
        return (node.parent is None or 
                (node.parent.left != node and node.parent.right != node))
    
    def push(self, node):
        if node.flipped:
            node.left, node.right = node.right, node.left
            if node.left:
                node.left.flipped = not node.left.flipped
            if node.right:
                node.right.flipped = not node.right.flipped
            node.flipped = False
    
    def update(self, node):
        node.path_sum = node.value
        if node.left:
            node.path_sum += node.left.path_sum
        if node.right:
            node.path_sum += node.right.path_sum
    
    def rotate(self, node):
        parent = node.parent
        grand = parent.parent
        
        self.push(parent)
        self.push(node)
        
        if parent.left == node:
            parent.left = node.right
            if node.right:
                node.right.parent = parent
            node.right = parent
        else:
            parent.right = node.left
            if node.left:
                node.left.parent = parent
            node.left = parent
        
        parent.parent = node
        node.parent = grand
        
        if grand:
            if grand.left == parent:
                grand.left = node
            elif grand.right == parent:
                grand.right = node
        
        self.update(parent)
        self.update(node)
    
    def splay(self, node):
        while not self.is_root(node):
            parent = node.parent
            grand = parent.parent
            
            if not self.is_root(parent):
                if ((grand.left == parent) == (parent.left == node)):
                    self.rotate(parent)
                else:
                    self.rotate(node)
            self.rotate(node)
    
    def access(self, node):
        self.splay(node)
        if node.right:
            node.right.parent = None
        node.right = None
        self.update(node)
        
        while node.parent:
            parent = node.parent
            self.splay(parent)
            if parent.right:
                parent.right.parent = None
            parent.right = node
            self.update(parent)
            self.splay(node)
    
    def make_root(self, node):
        self.access(node)
        node.flipped = not node.flipped
    
    def link(self, u, v):
        self.make_root(u)
        u.parent = v
    
    def cut(self, u, v):
        self.make_root(u)
        self.access(v)
        v.left.parent = None
        v.left = None
        self.update(v)
    
    def path_query(self, u, v):
        self.make_root(u)
        self.access(v)
        return v.path_sum

# Applications: Dynamic tree queries, network connectivity, online MST
```

### **2. Centroid Decomposition**
```python
class CentroidDecomposition:
    def __init__(self, graph):
        self.graph = graph
        self.n = len(graph)
        self.removed = [False] * self.n
        self.centroid_parent = [-1] * self.n
        self.decompose(0)
    
    def get_subtree_size(self, node, parent):
        size = 1
        for neighbor in self.graph[node]:
            if neighbor != parent and not self.removed[neighbor]:
                size += self.get_subtree_size(neighbor, node)
        return size
    
    def find_centroid(self, node, parent, tree_size):
        for neighbor in self.graph[node]:
            if (neighbor != parent and not self.removed[neighbor] and
                self.get_subtree_size(neighbor, node) > tree_size // 2):
                return self.find_centroid(neighbor, node, tree_size)
        return node
    
    def decompose(self, node):
        tree_size = self.get_subtree_size(node, -1)
        centroid = self.find_centroid(node, -1, tree_size)
        
        self.removed[centroid] = True
        
        # Process centroid (add your logic here)
        self.process_centroid(centroid)
        
        # Recursively decompose subtrees
        for neighbor in self.graph[centroid]:
            if not self.removed[neighbor]:
                child_centroid = self.decompose(neighbor)
                self.centroid_parent[child_centroid] = centroid
        
        return centroid
    
    def process_centroid(self, centroid):
        # Your specific processing logic
        pass
    
    def query_up_tree(self, node):
        """Query path from node to root of centroid tree"""
        result = 0
        current = node
        
        while current != -1:
            # Process path from original node to current centroid
            result += self.compute_contribution(node, current)
            current = self.centroid_parent[current]
        
        return result

# Applications: Path queries on trees, tree distance problems
```

---

## ⚡ High-Performance Coding Patterns

### **1. Iterator-Based Processing**
```python
def process_large_data_lazy(data_source):
    """Process data without loading everything into memory"""
    def chunk_processor(chunk_size=1000):
        buffer = []
        for item in data_source:
            buffer.append(process_item(item))
            if len(buffer) >= chunk_size:
                yield from buffer
                buffer = []
        if buffer:
            yield from buffer
    
    return chunk_processor()

def sliding_window_iterator(iterable, window_size):
    """Memory-efficient sliding window"""
    from collections import deque
    
    it = iter(iterable)
    window = deque(maxlen=window_size)
    
    # Fill initial window
    for _ in range(window_size):
        try:
            window.append(next(it))
        except StopIteration:
            return
    
    yield list(window)
    
    # Slide window
    for item in it:
        window.append(item)
        yield list(window)
```

### **2. Memory Pool Allocation**
```python
class MemoryPool:
    def __init__(self, block_size, pool_size=1000):
        self.block_size = block_size
        self.pool = [bytearray(block_size) for _ in range(pool_size)]
        self.available = list(range(pool_size))
        self.in_use = set()
    
    def allocate(self):
        if not self.available:
            # Expand pool if needed
            start_idx = len(self.pool)
            self.pool.extend(bytearray(self.block_size) for _ in range(100))
            self.available.extend(range(start_idx, start_idx + 100))
        
        idx = self.available.pop()
        self.in_use.add(idx)
        return idx, self.pool[idx]
    
    def deallocate(self, idx):
        if idx in self.in_use:
            self.in_use.remove(idx)
            self.available.append(idx)
            # Clear the block
            self.pool[idx][:] = bytearray(self.block_size)

# Applications: High-frequency trading, game engines, embedded systems
```

### **3. Branch Prediction Optimization**
```python
def optimized_conditional_processing(data, threshold):
    """Optimize branch prediction by sorting conditions"""
    # Separate data by condition to reduce branch misprediction
    above_threshold = []
    below_threshold = []
    
    for item in data:
        if item >= threshold:
            above_threshold.append(item)
        else:
            below_threshold.append(item)
    
    # Process each group separately
    results = []
    
    # Process above threshold (likely branch)
    for item in above_threshold:
        results.append(expensive_operation(item))
    
    # Process below threshold (unlikely branch)
    for item in below_threshold:
        results.append(cheap_operation(item))
    
    return results

def branchless_max(a, b):
    """Branchless maximum using bit manipulation"""
    diff = a - b
    sign = (diff >> 31) & 1  # Extract sign bit
    return a - diff * sign

def branchless_abs(x):
    """Branchless absolute value"""
    mask = x >> 31  # All 1s if negative, all 0s if positive
    return (x ^ mask) - mask
```

---

## 🎯 Problem Classification & Solution Templates

### **1. Interval/Range Problems Template**
```python
def interval_problems_template(intervals):
    # Step 1: Sort intervals by start time (usually)
    intervals.sort(key=lambda x: x[0])
    
    result = []
    current_start, current_end = intervals[0]
    
    for start, end in intervals[1:]:
        if start <= current_end:  # Overlapping
            current_end = max(current_end, end)  # Merge
        else:  # Non-overlapping
            result.append([current_start, current_end])
            current_start, current_end = start, end
    
    result.append([current_start, current_end])
    return result

# Variations:
# - Meeting rooms: Just check overlaps
# - Insert interval: Find insertion point
# - Remove interval: Handle partial overlaps
```

### **2. Subarray Problems Template**
```python
def subarray_problems_template(arr, target):
    # Sliding window approach
    left = 0
    current_sum = 0
    result = []
    
    for right in range(len(arr)):
        current_sum += arr[right]
        
        # Shrink window if necessary
        while current_sum > target and left <= right:
            current_sum -= arr[left]
            left += 1
        
        if current_sum == target:
            result.append([left, right])
    
    return result

def subarray_with_hashmap(arr, target):
    # Prefix sum + HashMap approach
    prefix_sum = 0
    sum_count = {0: 1}  # Handle subarrays starting from index 0
    result = 0
    
    for num in arr:
        prefix_sum += num
        
        if prefix_sum - target in sum_count:
            result += sum_count[prefix_sum - target]
        
        sum_count[prefix_sum] = sum_count.get(prefix_sum, 0) + 1
    
    return result
```

### **3. Backtracking Template**
```python
def backtracking_template(candidates, target):
    def backtrack(path, remaining, start_idx):
        # Base cases
        if remaining == 0:
            result.append(path[:])  # Found valid solution
            return
        if remaining < 0 or start_idx >= len(candidates):
            return  # Invalid path
        
        for i in range(start_idx, len(candidates)):
            # Skip duplicates (if needed)
            if i > start_idx and candidates[i] == candidates[i-1]:
                continue
            
            # Choose
            path.append(candidates[i])
            
            # Recurse
            backtrack(path, remaining - candidates[i], i + 1)  # or i for reuse
            
            # Unchoose (backtrack)
            path.pop()
    
    result = []
    candidates.sort()  # Often needed for duplicate handling
    backtrack([], target, 0)
    return result

# Applications: Combination sum, permutations, N-Queens, Sudoku solver
```

---

## 🏆 Contest Programming Meta-Strategies

### **1. Time Management Framework**
```python
# Contest time allocation (2.5 hour contest):
# - Read all problems: 15 minutes
# - Easy problems (A, B): 30 minutes
# - Medium problems (C, D): 60 minutes  
# - Hard problems (E, F): 60 minutes
# - Debug & optimize: 15 minutes

def contest_strategy():
    problems = read_all_problems()
    
    # Sort by estimated difficulty and your strength
    problem_order = sort_by_priority(problems)
    
    for problem in problem_order:
        if time_remaining < estimated_time(problem) * 2:
            continue  # Skip if not enough time
        
        solution = solve_problem(problem)
        if solution:
            submit_and_continue(solution)
        else:
            move_to_next_problem()
```

### **2. Code Template for Contests**
```python
#!/usr/bin/env python3
import sys
from collections import defaultdict, deque, Counter
from bisect import bisect_left, bisect_right
from heapq import heappush, heappop, heapify
from itertools import permutations, combinations, product
import math

# Fast I/O
input = lambda: sys.stdin.readline().strip()
print = lambda *args: sys.stdout.write(' '.join(map(str, args)) + '\n')

# Utility functions
def gcd(a, b):
    while b: a, b = b, a % b
    return a

def lcm(a, b):
    return a * b // gcd(a, b)

def is_prime(n):
    if n < 2: return False
    if n == 2: return True
    if n % 2 == 0: return False
    for i in range(3, int(n**0.5) + 1, 2):
        if n % i == 0: return False
    return True

# Constants
MOD = 10**9 + 7
INF = float('inf')
EPS = 1e-9

def main():
    # Your solution here
    pass

if __name__ == "__main__":
    main()
```

### **3. Debugging Strategies**
```python
def debug_template():
    # 1. Print intermediate states
    def debug_print(*args):
        if DEBUG:
            print("DEBUG:", *args, file=sys.stderr)
    
    # 2. Assert invariants
    def check_invariant(condition, message="Invariant violated"):
        assert condition, message
    
    # 3. Test with edge cases
    test_cases = [
        [],  # Empty input
        [1],  # Single element
        [1, 1, 1],  # All same
        [-1, 0, 1],  # Mixed signs
        list(range(10**5))  # Large input
    ]
    
    # 4. Binary search debugging
    def binary_search_debug(arr, target):
        left, right = 0, len(arr) - 1
        iterations = 0
        
        while left <= right:
            iterations += 1
            assert iterations < 100, "Infinite loop detected"
            
            mid = (left + right) // 2
            debug_print(f"left={left}, mid={mid}, right={right}, arr[mid]={arr[mid]}")
            
            if arr[mid] == target:
                return mid
            elif arr[mid] < target:
                left = mid + 1
            else:
                right = mid - 1
        
        return -1

# Common bugs to watch for:
# - Integer overflow
# - Off-by-one errors
# - Wrong base cases in recursion
# - Modulo operations with negative numbers
# - Floating point precision issues
```

This comprehensive guide covers advanced DSA techniques that go well beyond the basics. Each section provides both theoretical understanding and practical implementation, focusing on patterns and strategies that can be applied across different problem domains.