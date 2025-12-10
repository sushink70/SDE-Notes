"""
50 FUNDAMENTAL DSA PATTERNS - PYTHON REFERENCE
===============================================
Memorize these patterns. Recognition → Implementation → Mastery.
Time to recognize: 30 seconds. Time to implement: 3 minutes.
"""

# ============================================================================
# CATEGORY 1: ARRAY & STRING FUNDAMENTALS (5 patterns)
# ============================================================================

# Pattern 1: Prefix Sum (Range Sum Queries)
# Use: O(1) range sum after O(n) preprocessing
# Time: O(n) build, O(1) query | Space: O(n)
def prefix_sum_pattern(arr):
    n = len(arr)
    prefix = [0] * (n + 1)  # prefix[i] = sum of arr[0..i-1]
    for i in range(n):
        prefix[i + 1] = prefix[i] + arr[i]
    
    # Range sum [left, right] = prefix[right+1] - prefix[left]
    def range_sum(left, right):
        return prefix[right + 1] - prefix[left]
    
    return range_sum

# Pattern 2: Kadane's Algorithm (Maximum Subarray Sum)
# Use: Find max sum of contiguous subarray
# Time: O(n) | Space: O(1)
def kadane_pattern(arr):
    max_sum = float('-inf')
    current_sum = 0
    
    for num in arr:
        current_sum = max(num, current_sum + num)  # Reset or continue
        max_sum = max(max_sum, current_sum)
    
    return max_sum

# Pattern 3: Dutch National Flag (Three-way Partitioning)
# Use: Sort array with 3 distinct values
# Time: O(n) | Space: O(1)
def dutch_flag_pattern(arr):
    low, mid, high = 0, 0, len(arr) - 1
    
    while mid <= high:
        if arr[mid] == 0:
            arr[low], arr[mid] = arr[mid], arr[low]
            low += 1
            mid += 1
        elif arr[mid] == 1:
            mid += 1
        else:  # arr[mid] == 2
            arr[mid], arr[high] = arr[high], arr[mid]
            high -= 1
    
    return arr

# Pattern 4: Monotonic Stack (Next Greater Element)
# Use: Find next greater element for each element
# Time: O(n) | Space: O(n)
def monotonic_stack_pattern(arr):
    n = len(arr)
    result = [-1] * n
    stack = []  # Store indices
    
    for i in range(n):
        # Pop smaller elements - they found their next greater
        while stack and arr[stack[-1]] < arr[i]:
            idx = stack.pop()
            result[idx] = arr[i]
        stack.append(i)
    
    return result

# Pattern 5: Cyclic Sort (Find Missing Number)
# Use: When array contains numbers in range [1, n]
# Time: O(n) | Space: O(1)
def cyclic_sort_pattern(arr):
    i = 0
    while i < len(arr):
        correct_idx = arr[i] - 1
        if arr[i] != arr[correct_idx]:
            arr[i], arr[correct_idx] = arr[correct_idx], arr[i]
        else:
            i += 1
    
    # Find missing: first index where arr[i] != i+1
    for i in range(len(arr)):
        if arr[i] != i + 1:
            return i + 1
    return len(arr) + 1

# ============================================================================
# CATEGORY 2: TWO POINTERS (5 patterns)
# ============================================================================

# Pattern 6: Two Sum (Sorted Array)
# Use: Find pair with target sum in sorted array
# Time: O(n) | Space: O(1)
def two_pointers_sum_pattern(arr, target):
    left, right = 0, len(arr) - 1
    
    while left < right:
        current_sum = arr[left] + arr[right]
        if current_sum == target:
            return [left, right]
        elif current_sum < target:
            left += 1
        else:
            right -= 1
    
    return None

# Pattern 7: Remove Duplicates (In-place)
# Use: Remove duplicates from sorted array
# Time: O(n) | Space: O(1)
def remove_duplicates_pattern(arr):
    if not arr:
        return 0
    
    write_idx = 1
    for read_idx in range(1, len(arr)):
        if arr[read_idx] != arr[read_idx - 1]:
            arr[write_idx] = arr[read_idx]
            write_idx += 1
    
    return write_idx  # New length

# Pattern 8: Partition Around Pivot (Quick Select Core)
# Use: Partition array around pivot
# Time: O(n) | Space: O(1)
def partition_pattern(arr, low, high):
    pivot = arr[high]
    i = low - 1  # Boundary of smaller elements
    
    for j in range(low, high):
        if arr[j] <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    
    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1

# Pattern 9: Merge Two Sorted Arrays
# Use: Merge operation for merge sort
# Time: O(n+m) | Space: O(n+m)
def merge_sorted_pattern(arr1, arr2):
    i, j = 0, 0
    result = []
    
    while i < len(arr1) and j < len(arr2):
        if arr1[i] <= arr2[j]:
            result.append(arr1[i])
            i += 1
        else:
            result.append(arr2[j])
            j += 1
    
    result.extend(arr1[i:])
    result.extend(arr2[j:])
    return result

# Pattern 10: Floyd's Cycle Detection (Tortoise and Hare)
# Use: Detect cycle in linked list or array
# Time: O(n) | Space: O(1)
def floyd_cycle_detection_pattern(get_next, start):
    slow = fast = start
    
    # Phase 1: Detect if cycle exists
    while fast is not None and get_next(fast) is not None:
        slow = get_next(slow)
        fast = get_next(get_next(fast))
        if slow == fast:
            break
    else:
        return None  # No cycle
    
    # Phase 2: Find cycle start
    slow = start
    while slow != fast:
        slow = get_next(slow)
        fast = get_next(fast)
    
    return slow  # Cycle start

# ============================================================================
# CATEGORY 3: SLIDING WINDOW (5 patterns)
# ============================================================================

# Pattern 11: Fixed Size Window Maximum
# Use: Maximum in every window of size k
# Time: O(n) | Space: O(k)
from collections import deque

def sliding_window_max_pattern(arr, k):
    dq = deque()  # Store indices
    result = []
    
    for i in range(len(arr)):
        # Remove elements outside window
        while dq and dq[0] <= i - k:
            dq.popleft()
        
        # Remove smaller elements (not useful)
        while dq and arr[dq[-1]] < arr[i]:
            dq.pop()
        
        dq.append(i)
        
        if i >= k - 1:
            result.append(arr[dq[0]])
    
    return result

# Pattern 12: Variable Size Window (Longest Substring)
# Use: Longest substring with at most k distinct characters
# Time: O(n) | Space: O(k)
def variable_window_pattern(s, k):
    char_count = {}
    left = 0
    max_length = 0
    
    for right in range(len(s)):
        # Expand window
        char_count[s[right]] = char_count.get(s[right], 0) + 1
        
        # Contract window if invalid
        while len(char_count) > k:
            char_count[s[left]] -= 1
            if char_count[s[left]] == 0:
                del char_count[s[left]]
            left += 1
        
        max_length = max(max_length, right - left + 1)
    
    return max_length

# Pattern 13: Two Pointer Window (Subarray Sum Equals K)
# Use: Find subarray with exact sum (positive numbers)
# Time: O(n) | Space: O(1)
def subarray_sum_pattern(arr, k):
    left = 0
    current_sum = 0
    
    for right in range(len(arr)):
        current_sum += arr[right]
        
        while current_sum > k and left <= right:
            current_sum -= arr[left]
            left += 1
        
        if current_sum == k:
            return [left, right]
    
    return None

# Pattern 14: Minimum Window Substring
# Use: Smallest window containing all characters
# Time: O(n) | Space: O(k)
def min_window_substring_pattern(s, t):
    if not t:
        return ""
    
    need = {}
    for c in t:
        need[c] = need.get(c, 0) + 1
    
    have = {}
    required = len(need)
    formed = 0
    
    left = 0
    min_len = float('inf')
    min_left = 0
    
    for right in range(len(s)):
        char = s[right]
        have[char] = have.get(char, 0) + 1
        
        if char in need and have[char] == need[char]:
            formed += 1
        
        while formed == required:
            if right - left + 1 < min_len:
                min_len = right - left + 1
                min_left = left
            
            have[s[left]] -= 1
            if s[left] in need and have[s[left]] < need[s[left]]:
                formed -= 1
            left += 1
    
    return "" if min_len == float('inf') else s[min_left:min_left + min_len]

# Pattern 15: Longest Repeating Character Replacement
# Use: Longest substring with k replacements allowed
# Time: O(n) | Space: O(26) = O(1)
def longest_repeating_replacement_pattern(s, k):
    char_count = {}
    left = 0
    max_count = 0
    max_length = 0
    
    for right in range(len(s)):
        char_count[s[right]] = char_count.get(s[right], 0) + 1
        max_count = max(max_count, char_count[s[right]])
        
        # If replacements needed > k, shrink window
        if (right - left + 1) - max_count > k:
            char_count[s[left]] -= 1
            left += 1
        
        max_length = max(max_length, right - left + 1)
    
    return max_length

# ============================================================================
# CATEGORY 4: BINARY SEARCH VARIANTS (5 patterns)
# ============================================================================

# Pattern 16: Classic Binary Search
# Use: Find exact target in sorted array
# Time: O(log n) | Space: O(1)
def binary_search_pattern(arr, target):
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = left + (right - left) // 2
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1

# Pattern 17: Find First/Last Occurrence
# Use: Find leftmost/rightmost position of target
# Time: O(log n) | Space: O(1)
def find_boundary_pattern(arr, target, find_first=True):
    left, right = 0, len(arr) - 1
    result = -1
    
    while left <= right:
        mid = left + (right - left) // 2
        
        if arr[mid] == target:
            result = mid
            if find_first:
                right = mid - 1  # Continue searching left
            else:
                left = mid + 1   # Continue searching right
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return result

# Pattern 18: Search in Rotated Sorted Array
# Use: Binary search in rotated array
# Time: O(log n) | Space: O(1)
def rotated_search_pattern(arr, target):
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = left + (right - left) // 2
        
        if arr[mid] == target:
            return mid
        
        # Determine which half is sorted
        if arr[left] <= arr[mid]:  # Left half is sorted
            if arr[left] <= target < arr[mid]:
                right = mid - 1
            else:
                left = mid + 1
        else:  # Right half is sorted
            if arr[mid] < target <= arr[right]:
                left = mid + 1
            else:
                right = mid - 1
    
    return -1

# Pattern 19: Find Peak Element
# Use: Find any peak in array (arr[i] > arr[i-1] and arr[i] > arr[i+1])
# Time: O(log n) | Space: O(1)
def find_peak_pattern(arr):
    left, right = 0, len(arr) - 1
    
    while left < right:
        mid = left + (right - left) // 2
        
        if arr[mid] > arr[mid + 1]:
            right = mid  # Peak is on left (or mid itself)
        else:
            left = mid + 1  # Peak is on right
    
    return left

# Pattern 20: Binary Search on Answer Space
# Use: Find minimum/maximum value satisfying condition
# Time: O(n log(max-min)) | Space: O(1)
def binary_search_answer_pattern(arr, condition_func):
    left, right = min(arr), max(arr)
    result = right
    
    while left <= right:
        mid = left + (right - left) // 2
        
        if condition_func(mid):
            result = mid
            right = mid - 1  # Try to find smaller valid answer
        else:
            left = mid + 1
    
    return result

# ============================================================================
# CATEGORY 5: LINKED LIST (5 patterns)
# ============================================================================

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

# Pattern 21: Reverse Linked List (Iterative)
# Use: Reverse entire linked list
# Time: O(n) | Space: O(1)
def reverse_linked_list_pattern(head):
    prev = None
    current = head
    
    while current:
        next_temp = current.next
        current.next = prev
        prev = current
        current = next_temp
    
    return prev

# Pattern 22: Merge Two Sorted Lists
# Use: Merge two sorted linked lists
# Time: O(n+m) | Space: O(1)
def merge_lists_pattern(l1, l2):
    dummy = ListNode(0)
    current = dummy
    
    while l1 and l2:
        if l1.val <= l2.val:
            current.next = l1
            l1 = l1.next
        else:
            current.next = l2
            l2 = l2.next
        current = current.next
    
    current.next = l1 if l1 else l2
    return dummy.next

# Pattern 23: Find Middle of Linked List
# Use: Fast/slow pointers to find middle
# Time: O(n) | Space: O(1)
def find_middle_pattern(head):
    slow = fast = head
    
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
    
    return slow

# Pattern 24: Remove Nth Node from End
# Use: Two pointers with n gap
# Time: O(n) | Space: O(1)
def remove_nth_from_end_pattern(head, n):
    dummy = ListNode(0)
    dummy.next = head
    fast = slow = dummy
    
    # Move fast n+1 steps ahead
    for _ in range(n + 1):
        fast = fast.next
    
    # Move both until fast reaches end
    while fast:
        fast = fast.next
        slow = slow.next
    
    # Remove node
    slow.next = slow.next.next
    return dummy.next

# Pattern 25: Reorder List (L0→L1→...→Ln-1→Ln to L0→Ln→L1→Ln-1→...)
# Use: Find middle, reverse second half, merge
# Time: O(n) | Space: O(1)
def reorder_list_pattern(head):
    if not head or not head.next:
        return
    
    # Find middle
    slow = fast = head
    while fast.next and fast.next.next:
        slow = slow.next
        fast = fast.next.next
    
    # Reverse second half
    second = slow.next
    slow.next = None
    second = reverse_linked_list_pattern(second)
    
    # Merge two halves
    first = head
    while second:
        temp1, temp2 = first.next, second.next
        first.next = second
        second.next = temp1
        first, second = temp1, temp2

# ============================================================================
# CATEGORY 6: TREE TRAVERSALS (5 patterns)
# ============================================================================

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

# Pattern 26: DFS Preorder (Root-Left-Right)
# Use: Process root before children
# Time: O(n) | Space: O(h)
def preorder_pattern(root):
    result = []
    
    def dfs(node):
        if not node:
            return
        result.append(node.val)  # Process root
        dfs(node.left)           # Process left
        dfs(node.right)          # Process right
    
    dfs(root)
    return result

# Pattern 27: DFS Inorder (Left-Root-Right)
# Use: Process BST in sorted order
# Time: O(n) | Space: O(h)
def inorder_pattern(root):
    result = []
    
    def dfs(node):
        if not node:
            return
        dfs(node.left)           # Process left
        result.append(node.val)  # Process root
        dfs(node.right)          # Process right
    
    dfs(root)
    return result

# Pattern 28: DFS Postorder (Left-Right-Root)
# Use: Process children before root (deletion, bottom-up)
# Time: O(n) | Space: O(h)
def postorder_pattern(root):
    result = []
    
    def dfs(node):
        if not node:
            return
        dfs(node.left)           # Process left
        dfs(node.right)          # Process right
        result.append(node.val)  # Process root
    
    dfs(root)
    return result

# Pattern 29: BFS Level Order
# Use: Process level by level
# Time: O(n) | Space: O(w) where w is max width
def level_order_pattern(root):
    if not root:
        return []
    
    result = []
    queue = deque([root])
    
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

# Pattern 30: Path Sum with Backtracking
# Use: Find all root-to-leaf paths with target sum
# Time: O(n) | Space: O(h)
def path_sum_pattern(root, target):
    result = []
    
    def backtrack(node, remaining, path):
        if not node:
            return
        
        path.append(node.val)
        
        if not node.left and not node.right and remaining == node.val:
            result.append(path[:])  # Found valid path
        
        backtrack(node.left, remaining - node.val, path)
        backtrack(node.right, remaining - node.val, path)
        
        path.pop()  # Backtrack
    
    backtrack(root, target, [])
    return result

# ============================================================================
# CATEGORY 7: GRAPH ALGORITHMS (5 patterns)
# ============================================================================

# Pattern 31: DFS on Graph (Adjacency List)
# Use: Explore all connected components
# Time: O(V+E) | Space: O(V)
def graph_dfs_pattern(graph, start):
    visited = set()
    result = []
    
    def dfs(node):
        if node in visited:
            return
        
        visited.add(node)
        result.append(node)
        
        for neighbor in graph[node]:
            dfs(neighbor)
    
    dfs(start)
    return result

# Pattern 32: BFS on Graph (Shortest Path)
# Use: Find shortest path in unweighted graph
# Time: O(V+E) | Space: O(V)
def graph_bfs_pattern(graph, start, end):
    queue = deque([(start, [start])])
    visited = {start}
    
    while queue:
        node, path = queue.popleft()
        
        if node == end:
            return path
        
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    
    return None

# Pattern 33: Topological Sort (Kahn's Algorithm)
# Use: Order tasks with dependencies
# Time: O(V+E) | Space: O(V)
def topological_sort_pattern(graph, n):
    in_degree = [0] * n
    
    for node in graph:
        for neighbor in graph[node]:
            in_degree[neighbor] += 1
    
    queue = deque([i for i in range(n) if in_degree[i] == 0])
    result = []
    
    while queue:
        node = queue.popleft()
        result.append(node)
        
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    return result if len(result) == n else []  # Cycle detected if not all nodes

# Pattern 34: Union-Find (Disjoint Set)
# Use: Detect cycles, connected components
# Time: O(α(n)) per operation (nearly O(1))
class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n
    
    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # Path compression
        return self.parent[x]
    
    def union(self, x, y):
        root_x, root_y = self.find(x), self.find(y)
        
        if root_x == root_y:
            return False  # Already connected
        
        # Union by rank
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1
        
        return True

# Pattern 35: Dijkstra's Algorithm (Shortest Path)
# Use: Shortest path in weighted graph (non-negative weights)
# Time: O((V+E)log V) | Space: O(V)
import heapq

def dijkstra_pattern(graph, start):
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    pq = [(0, start)]  # (distance, node)
    
    while pq:
        current_dist, node = heapq.heappop(pq)
        
        if current_dist > distances[node]:
            continue
        
        for neighbor, weight in graph[node]:
            distance = current_dist + weight
            
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                heapq.heappush(pq, (distance, neighbor))
    
    return distances

# ============================================================================
# CATEGORY 8: DYNAMIC PROGRAMMING (5 patterns)
# ============================================================================

# Pattern 36: 1D DP (Fibonacci-like)
# Use: Current state depends on previous states
# Time: O(n) | Space: O(n) or O(1) with optimization
def dp_1d_pattern(n):
    if n <= 1:
        return n
    
    # dp[i] = answer for subproblem i
    dp = [0] * (n + 1)
    dp[0], dp[1] = 0, 1
    
    for i in range(2, n + 1):
        dp[i] = dp[i-1] + dp[i-2]
    
    return dp[n]

# Pattern 37: 2D DP (Grid/Matrix)
# Use: States depend on 2D coordinates
# Time: O(m*n) | Space: O(m*n)
def dp_2d_pattern(grid):
    m, n = len(grid), len(grid[0])
    dp = [[0] * n for _ in range(m)]
    
    # Base case
    dp[0][0] = grid[0][0]
    
    # Fill first row and column
    for i in range(1, m):
        dp[i][0] = dp[i-1][0] + grid[i][0]
    for j in range(1, n):
        dp[0][j] = dp[0][j-1] + grid[0][j]
    
    # Fill rest of table
    for i in range(1, m):
        for j in range(1, n):
            dp[i][j] = min(dp[i-1][j], dp[i][j-1]) + grid[i][j]
    
    return dp[m-1][n-1]

# Pattern 38: Knapsack DP
# Use: 0/1 knapsack or subset problems
# Time: O(n*W) | Space: O(n*W)
def knapsack_pattern(weights, values, capacity):
    n = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        for w in range(capacity + 1):
            if weights[i-1] <= w:
                # Max of (include item, exclude item)
                dp[i][w] = max(
                    values[i-1] + dp[i-1][w - weights[i-1]],
                    dp[i-1][w]
                )
            else:
                dp[i][w] = dp[i-1][w]
    
    return dp[n][capacity]

# Pattern 39: LCS (Longest Common Subsequence)
# Use: String matching, diff algorithms
# Time: O(m*n) | Space: O(m*n)
def lcs_pattern(s1, s2):
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    return dp[m][n]

# Pattern 40: DP with Memoization (Top-Down)
# Use: When recursion tree has overlapping subproblems
# Time: O(n*target) | Space: O(n*target)
def dp_memo_pattern(coins, amount):
    memo = {}
    
    def dp(remaining):
        if remaining == 0:
            return 0
        if remaining < 0:
            return float('inf')
        if remaining in memo:
            return memo[remaining]
        
        min_coins = float('inf')
        for coin in coins:
            min_coins = min(min_coins, 1 + dp(remaining - coin))
        
        memo[remaining] = min_coins
        return min_coins
    
    result = dp(amount)
    return result if result != float('inf') else -1

# ============================================================================
# CATEGORY 9: BACKTRACKING (5 patterns)
# ============================================================================

# Pattern 41: Permutations
# Use: Generate all permutations of array
# Time: O(n! * n) | Space: O(n)
def permutations_pattern(nums):
    result = []
    
    def backtrack(path, remaining):
        if not remaining:
            result.append(path[:])
            return
        
        for i in range(len(remaining)):
            backtrack(
                path + [remaining[i]],
                remaining[:i] + remaining[i+1:]
            )
    
    backtrack([], nums)
    return result

# Pattern 42: Combinations/Subsets
# Use: Generate all subsets/combinations
# Time: O(2^n) | Space: O(n)
def subsets_pattern(nums):
    result = []
    
    def backtrack(start, path):
        result.append(path[:])
        
        for i in range(start, len(nums)):
            path.append(nums[i])
            backtrack(i + 1, path)
            path.pop()
    
    backtrack(0, [])
    return result

# Pattern 43: Combination Sum
# Use: Find combinations that sum to target
# Time: O(2^n) | Space: O(target/min)
def combination_sum_pattern(candidates, target):
    result = []
    
    def backtrack(start, remaining, path):
        if remaining == 0:
            result.append(path[:])
            return
        if remaining < 0:
            return
        
        for i in range(start, len(candidates)):
            path.append(candidates[i])
            backtrack(i, remaining - candidates[i], path)  # Can reuse same element
            path.pop()
    
    backtrack(0, target, [])
    return result

# Pattern 44: N-Queens
# Use: Place N queens on N×N board
# Time: O(N!) | Space: O(N)
def n_queens_pattern(n):
    result = []
    board = [['.'] * n for _ in range(n)]
    cols = set()
    diag1 = set()  # row - col
    diag2 = set()  # row + col
    
    def backtrack(row):
        if row == n:
            result.append([''.join(row) for row in board])
            return
        
        for col in range(n):
            if col in cols or (row - col) in diag1 or (row + col) in diag2:
                continue
            
            # Place queen
            board[row][col] = 'Q'
            cols.add(col)
            diag1.add(row - col)
            diag2.add(row + col)
            
            backtrack(row + 1)
            
            # Remove queen
            board[row][col] = '.'
            cols.remove(col)
            diag1.remove(row - col)
            diag2.remove(row + col)
    
    backtrack(0)
    return result

# Pattern 45: Word Search (Grid Backtracking)
# Use: Find word in 2D grid
# Time: O(m*n*4^L) where L is word length | Space: O(L)
def word_search_pattern(board, word):
    m, n = len(board), len(board[0])
    
    def backtrack(row, col, index):
        if index == len(word):
            return True
        
        if (row < 0 or row >= m or col < 0 or col >= n or
            board[row][col] != word[index]):
            return False
        
        # Mark as visited
        temp = board[row][col]
        board[row][col] = '#'
        
        # Explore all 4 directions
        found = (backtrack(row+1, col, index+1) or
                 backtrack(row-1, col, index+1) or
                 backtrack(row, col+1, index+1) or
                 backtrack(row, col-1, index+1))
        
        # Restore cell
        board[row][col] = temp
        
        return found
    
    for i in range(m):
        for j in range(n):
            if backtrack(i, j, 0):
                return True
    return False

# ============================================================================
# CATEGORY 10: ADVANCED PATTERNS (5 patterns)
# ============================================================================

# Pattern 46: Trie (Prefix Tree)
# Use: Efficient string prefix operations
# Time: O(m) per operation | Space: O(ALPHABET_SIZE * m * n)
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False

class Trie:
    def __init__(self):
        self.root = TrieNode()
    
    def insert(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end = True
    
    def search(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end

# Pattern 47: Bit Manipulation (XOR Tricks)
# Use: Find single number, missing number
# Time: O(n) | Space: O(1)
def bit_manipulation_pattern(nums):
    # XOR of all elements cancels duplicates
    result = 0
    for num in nums:
        result ^= num
    return result

# Pattern 48: Quick Select (Kth Largest)
# Use: Find kth largest element without full sort
# Time: O(n) average, O(n²) worst | Space: O(1)
def quick_select_pattern(arr, k):
    def partition(left, right):
        pivot = arr[right]
        i = left
        for j in range(left, right):
            if arr[j] <= pivot:
                arr[i], arr[j] = arr[j], arr[i]
                i += 1
        arr[i], arr[right] = arr[right], arr[i]
        return i
    
    left, right = 0, len(arr) - 1
    k_index = len(arr) - k
    
    while left <= right:
        pivot_index = partition(left, right)
        
        if pivot_index == k_index:
            return arr[pivot_index]
        elif pivot_index < k_index:
            left = pivot_index + 1
        else:
            right = pivot_index - 1
    
    return -1

# Pattern 49: Interval Merging
# Use: Merge overlapping intervals
# Time: O(n log n) | Space: O(n)
def merge_intervals_pattern(intervals):
    if not intervals:
        return []
    
    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]
    
    for current in intervals[1:]:
        last = merged[-1]
        
        if current[0] <= last[1]:  # Overlapping
            merged[-1] = [last[0], max(last[1], current[1])]
        else:
            merged.append(current)
    
    return merged

# Pattern 50: Top K Elements (Heap)
# Use: Find K largest/smallest elements
# Time: O(n log k) | Space: O(k)
def top_k_pattern(nums, k):
    # Min heap of size k for k largest elements
    heap = []
    
    for num in nums:
        heapq.heappush(heap, num)
        if len(heap) > k:
            heapq.heappop(heap)
    
    return heap

"""
MASTERY CHECKLIST:
==================
For each pattern:
1. Recognize in < 30 seconds from problem description
2. Write from memory in < 3 minutes
3. Explain time/space complexity instantly
4. Know when NOT to use it (anti-patterns)

DELIBERATE PRACTICE PROTOCOL:
==============================
Week 1-2: Implement each pattern 3 times
Week 3-4: Mixed recognition drills (random problems)
Week 5-6: Speed contests (time yourself)
Week 7-8: Teach each pattern (Feynman technique)

PATH TO TOP 1%:
===============
These 50 patterns cover 90% of competitive programming problems.
Master these → Combine them → Create new variants.

The difference between good and world-class:
- Good: Knows the patterns
- World-class: Recognizes which pattern in 10 seconds

Your goal: Make these patterns subconscious.
When you see a problem, your hands should start coding before
your conscious mind finishes reading.

That's true mastery.
"""

# Complete Pattern Library Created ✓

I've built you a **combat-ready reference** with all 50 fundamental patterns organized into 10 categories:

## Categories Overview

1. **Array & String Fundamentals** (5) - Prefix sum, Kadane's, Dutch flag, monotonic stack, cyclic sort
2. **Two Pointers** (5) - Sum variants, partitioning, merging, cycle detection
3. **Sliding Window** (5) - Fixed/variable size, substring problems, optimization
4. **Binary Search Variants** (5) - Classic, boundaries, rotated arrays, peak finding, answer space
5. **Linked List** (5) - Reversal, merging, middle finding, reordering
6. **Tree Traversals** (5) - DFS (pre/in/post), BFS, path finding
7. **Graph Algorithms** (5) - DFS/BFS, topological sort, Union-Find, Dijkstra
8. **Dynamic Programming** (5) - 1D/2D, knapsack, LCS, memoization
9. **Backtracking** (5) - Permutations, combinations, N-Queens, grid search
10. **Advanced Patterns** (5) - Trie, bit manipulation, quick select, intervals, heaps

---

## How to Use This Library for Mastery

### **Phase 1: Pattern Recognition (Week 1-2)**

**Daily Protocol:**
- Pick 5 patterns each day
- Read code → Close eyes → Recite structure from memory
- Write out 3 times without looking
- Explain to rubber duck: "This pattern solves X by doing Y"

**Memory Anchor:** Associate each pattern with a **visual image**
- Two Pointers → Two hands closing a book
- Sliding Window → Window sliding across a wall
- Backtracking → Walking maze, leaving breadcrumbs

### **Phase 2: Speed Drills (Week 3-4)**

**Blind Implementation Challenge:**
- Set timer for 3 minutes
- Pick random pattern number (1-50)
- Implement from scratch without reference
- If you fail → Study pattern → Retry immediately

**Target Speed:**
- Week 3: 5 minutes per pattern
- Week 4: 3 minutes per pattern
- Week 5+: < 2 minutes per pattern

### **Phase 3: Problem Mapping (Week 5-6)**

For each LeetCode problem:
1. **Before reading solution:** Which pattern? (30 sec max)
2. **After solving:** Was I right? What was the tell?
3. **Pattern signals journal:** Track recognition cues

**Example signals:**
- "Find in sorted array" → Binary Search
- "All possible combinations" → Backtracking
- "Maximum/minimum subarray" → DP or Kadane's
- "Detect cycle" → Floyd's algorithm

### **Phase 4: Pattern Fusion (Week 7-8)**

Hard problems combine 2-3 patterns:
- Sliding Window + HashMap → Minimum window substring
- Binary Search + DP → Optimal answer in sorted space
- Union-Find + DFS → Connected components with constraints

**Exercise:** Take any 2 patterns → Invent a problem requiring both

---

## Critical Complexity Patterns to Memorize

```python
# INSTANT RECOGNITION TABLE
O(1)         → Hash table lookup, array index
O(log n)     → Binary search, balanced tree operations
O(n)         → Single pass, linear scan
O(n log n)   → Sorting, heap operations × n times
O(n²)        → Nested loops, all pairs
O(2^n)       → Subsets, power set
O(n!)        → Permutations, traveling salesman

# SPACE COMPLEXITY TELLS
O(1)         → Only variables, in-place modification
O(n)         → Hash table, recursion depth, DP table 1D
O(n²)        → 2D DP table, adjacency matrix
```

---

## The Recognition Training System

### **Technique 1: The 10-Second Rule**

Read problem statement → Start timer → Force yourself to guess pattern in 10 seconds.

**Mental checklist (in order):**
1. Is it sorted? → Binary search family
2. Find all/count? → Backtracking/DP
3. Optimize/maximize? → DP/Greedy
4. Graph mentioned? → DFS/BFS/Union-Find
5. Window/substring? → Sliding window
6. Two arrays/pointers? → Two pointers

### **Technique 2: The Wrong Answer Journal**

Every time you:
- Pick wrong pattern → Write down why you were fooled
- Miss optimization → Write down the clue you missed
- Implement incorrectly → Write down the control flow error

**Review this weekly.** Your mistakes become your pattern-recognition database.

### **Technique 3: The Reverse Problem**

Given a pattern, invent 3 problems it solves:
- **Easy variant:** Simple application
- **Medium variant:** With one twist
- **Hard variant:** Combined with another pattern

This trains **pattern → problem** recognition (the inverse skill).

---

## Your Next Steps

1. **Today:** Read through all 50 patterns (30 minutes)
2. **This week:** Implement categories 1-5 from memory (5 patterns/day)
3. **Next week:** Implement categories 6-10 + speed drills
4. **Week 3+:** Solve 3 problems daily, mapping each to patterns

---

## The Psychological Edge

**Pattern mastery creates cognitive chunks.** Right now, your brain sees:
```
"for i in range(n): if arr[i] > threshold: count += 1"
```

After mastery, your brain sees:
```
"linear_filter_pattern"  ← Single chunk
```

This frees up working memory for **higher-level strategy**. You're not thinking about *how* to implement—you're thinking about *which patterns to combine*.

**That's the 1% difference.**

When top competitive programmers read a problem, they instantly see: *"Oh, this is sliding window with hash table tracking, then binary search on answer space."*

Your journey:
- **Month 1:** Recognize patterns consciously (slow)
- **Month 3:** Recognize patterns subconsciously (fast)  
- **Month 6:** Invent new patterns by combining (mastery)

---

Want me to create:
1. **A 30-day training schedule** with specific problems mapped to each pattern?
2. **Pattern combination examples** (hard problems requiring 2-3 patterns)?
3. **Anti-pattern guide** (when NOT to use each pattern)?
4. **Language-specific optimizations** for Rust/Go/C++ implementations?

Tell me what would accelerate your path to mastery most. 🔥

# Mastering the Sorting + Two-Pointer Pattern: A Strategic Learning Path

This is **the** question that separates mediocre from elite problem-solvers. Let me give you the complete roadmap.

---

## **Part 1: Understanding WHY This Pattern Exists**

### **The Core Insight: Sorting Creates Monotonicity**

**Unsorted array:**
```
[3, -2, 5, 1, -4, 7]
```
- Chaotic: no relationship between position and value
- Must check **all combinations** → O(n²) or O(n³)

**Sorted array:**
```
[-4, -2, 1, 3, 5, 7]
```
- **Monotonic property**: values increase left-to-right
- This enables **binary decisions**: "move left" or "move right"
- Transforms brute force into **guided search**

---

### **Two-Pointer Intuition: Converging from Extremes**

**The mental model:**
```
sorted: [-4, -2, 1, 3, 5, 7]
          ↑              ↑
        left          right

If sum too small  → left++  (need bigger numbers)
If sum too large  → right-- (need smaller numbers)
If sum equals target → found it!
```

**Why this works:**
1. Start at **extremes** (smallest + largest)
2. Each decision **eliminates possibilities** without checking them
3. **Proof of correctness**: if `sum < target`, moving `right--` would make sum even smaller (useless)

---

## **Part 2: Where to Learn This Pattern**

### **Canonical Resources (In Order of Learning)**

#### **1. NeetCode's Two Pointers Playlist** ⭐ START HERE
- **Link:** Search "NeetCode Two Pointers" on YouTube
- **Why:** Visual explanations with code walkthroughs
- **Key videos:**
  - "Two Sum II" (easiest introduction)
  - "3Sum" (your current problem)
  - "Container With Most Water"
  - "Trapping Rain Water"

**Action:** Watch each video, code alongside him, then solve **without looking**.

---

#### **2. LeetCode's Study Plan: "Top Interview 150"**
- **Link:** LeetCode.com → Study Plan → Top Interview 150
- **Relevant section:** "Two Pointers"
- **Curated progression** from easy → hard

**Key problems in order:**
1. **Valid Palindrome** (LC 125) - warmup
2. **Two Sum II** (LC 167) - **THE foundation**
3. **3Sum** (LC 15) - your problem
4. **Container With Most Water** (LC 11) - different flavor
5. **Trapping Rain Water** (LC 42) - advanced

---

#### **3. "Elements of Programming Interviews" (EPI)**
- **Chapter:** Arrays (Chapter 5)
- **Why:** Rigorous explanations with variants
- **Best for:** Understanding **why** patterns work, not just **how**

**Available in Python, Java, C++** (get the one matching your language).

---

#### **4. Competitive Programming Resources**

**For building intuition:**
- **"Competitive Programmer's Handbook"** (Free PDF)
  - Chapter 3: "Sorting and Searching"
  - Chapter 8: "Data Structures"
  - **Link:** Google "cses competitive programming handbook"

**For systematic practice:**
- **Codeforces Edu Section:** "Two Pointers Method"
  - **Link:** codeforces.com/edu/course/2
  - Interactive problems with hints

---

## **Part 3: The Complete Pattern Recognition Framework**

### **When to Use Sorting + Two Pointers**

Ask yourself these questions:

| Question | If YES → Consider Two Pointers |
|----------|-------------------------------|
| **Does the problem involve pairs/triplets/combinations?** | ✅ 2Sum, 3Sum, 4Sum |
| **Is there a "too much/too little" decision?** | ✅ Container With Most Water |
| **Can elements be reordered without losing information?** | ✅ Most array problems (not subsequences) |
| **Is there a target/threshold to meet?** | ✅ 3Sum Closest, Sum Target |
| **Do I need to minimize/maximize something?** | ✅ Container With Most Water |

---

### **Two-Pointer Pattern Taxonomy**

There are **three main variants** you must master:

#### **Type 1: Opposite Direction (Converging)**
```python
left, right = 0, len(arr) - 1
while left < right:
    # Make decision based on arr[left] + arr[right]
    if condition:
        left += 1
    else:
        right -= 1
```

**Use cases:**
- 2Sum II (sorted array)
- 3Sum
- Container With Most Water
- Valid Palindrome

---

#### **Type 2: Same Direction (Sliding Window)**
```python
left = 0
for right in range(len(arr)):
    # Expand window
    while condition_violated:
        # Shrink window
        left += 1
    # Process valid window
```

**Use cases:**
- Longest Substring Without Repeating Characters
- Minimum Window Substring
- Maximum Sum Subarray of Size K

---

#### **Type 3: Fast-Slow (Cycle Detection)**
```python
slow = fast = head
while fast and fast.next:
    slow = slow.next
    fast = fast.next.next
    if slow == fast:
        # Cycle detected
```

**Use cases:**
- Linked List Cycle
- Find Duplicate Number
- Middle of Linked List

---

## **Part 4: Deliberate Practice Roadmap**

### **Week 1: Foundation (Type 1 - Converging Pointers)**

**Day 1-2:** Two Sum II (LC 167)
```python
# Master this FIRST - it's the building block
def twoSum(nums, target):
    left, right = 0, len(nums) - 1
    while left < right:
        s = nums[left] + nums[right]
        if s == target:
            return [left + 1, right + 1]
        elif s < target:
            left += 1
        else:
            right -= 1
```

**Practice:**
- Code in Python, Rust, Go
- Explain out loud why each decision is correct
- Prove why this doesn't miss any solutions

---

**Day 3-4:** Valid Palindrome (LC 125)
```python
def isPalindrome(s: str) -> bool:
    left, right = 0, len(s) - 1
    while left < right:
        # Skip non-alphanumeric
        while left < right and not s[left].isalnum():
            left += 1
        while left < right and not s[right].isalnum():
            right -= 1
        
        if s[left].lower() != s[right].lower():
            return False
        
        left += 1
        right -= 1
    
    return True
```

**Insight:** Two pointers work on **any sequence** (not just numbers).

---

**Day 5-7:** 3Sum (LC 15)
- **Day 5:** Code brute force O(n³)
- **Day 6:** Optimize to O(n²) with two pointers
- **Day 7:** Implement in all three languages

---

### **Week 2: Variations**

1. **3Sum Closest** (LC 16) - slight variation on 3Sum
2. **4Sum** (LC 18) - generalize the pattern
3. **Remove Duplicates from Sorted Array** (LC 26) - different application
4. **Container With Most Water** (LC 11) - **critical problem**

---

### **Week 3: Sliding Window (Type 2)**

1. **Longest Substring Without Repeating** (LC 3)
2. **Minimum Size Subarray Sum** (LC 209)
3. **Longest Repeating Character Replacement** (LC 424)

---

### **Week 4: Integration & Advanced**

1. **Trapping Rain Water** (LC 42) - combines two pointers + prefix thinking
2. **Sort Colors** (LC 75) - Dutch National Flag (three pointers!)
3. **Find K Closest Elements** (LC 658) - binary search + two pointers

---

## **Part 5: Building Pattern Recognition**

### **The Monk's Method: Spaced Repetition**

**After solving each problem:**

1. **Immediate review** (same day): Explain solution out loud
2. **1-day review:** Rewrite from memory
3. **3-day review:** Solve a similar problem
4. **7-day review:** Implement in different language
5. **30-day review:** Teach it to someone (or write an explanation)

**Tool:** Use Anki flashcards with:
- Front: Problem name + key constraint
- Back: Pattern name + code skeleton

---

### **Meta-Learning: Building Intuition**

**After each problem, ask:**

1. **Pattern:** "What category does this belong to?"
2. **Trigger:** "What in the problem statement hinted at this pattern?"
3. **Variations:** "How would I modify this for [X]?"
4. **Edge cases:** "What inputs would break my initial thinking?"

**Example for 3Sum:**
- **Pattern:** Sorting + Two Pointers (Converging)
- **Trigger:** "Find triplets" + "sum to target" + "no duplicates"
- **Variations:** 3Sum Closest (change condition), 4Sum (add another loop)
- **Edge cases:** All zeros, all negatives, duplicates

---

## **Part 6: Language-Specific Mastery**

### **Python: Leverage Built-ins**

```python
# Idiomatic duplicate skipping
nums.sort()
result = []
for i in range(len(nums) - 2):
    if i > 0 and nums[i] == nums[i-1]:
        continue  # Skip duplicates
    
    # Two-pointer logic...
```

**Key techniques:**
- `enumerate()` for index tracking
- List comprehensions for filtering
- `itertools.groupby()` for grouping duplicates

---

### **Rust: Zero-Cost Abstractions**

```rust
nums.sort_unstable();  // Faster when stability not needed

// Pattern matching for cleaner logic
match (left_val + right_val).cmp(&target) {
    Ordering::Less => left += 1,
    Ordering::Greater => right -= 1,
    Ordering::Equal => {
        // Found solution
    }
}
```

**Key techniques:**
- `.windows(2)` for pairwise comparisons
- `.dedup()` for removing consecutive duplicates
- Iterator chains for functional style

---

### **Go: Simplicity & Performance**

```go
sort.Ints(nums)  // Efficient in-place sort

// Clean loop structure
for left < right {
    sum := nums[left] + nums[right]
    switch {
    case sum < target:
        left++
    case sum > target:
        right--
    default:
        // Found solution
    }
}
```

**Key techniques:**
- `slices.Clone()` for safe copies
- `slices.Equal()` for comparison
- Defer for cleanup logic

---

## **Part 7: Beyond LeetCode**

### **Real-World Applications**

**This pattern appears in:**
1. **Databases:** Merge join algorithms
2. **Genomics:** DNA sequence alignment
3. **Computer Vision:** Finding matching features
4. **Financial Systems:** Matching buy/sell orders
5. **Recommendation Systems:** Finding similar user pairs

**Understanding the theory makes you better at ALL of these.**

---

### **Competitive Programming**

**Practice sites (easier → harder):**
1. **HackerRank:** "Arrays" domain
2. **Codeforces:** Filter by "two pointers" tag
3. **AtCoder:** Beginner contests often have these
4. **CSES Problem Set:** "Sorting and Searching" section

**Goal:** Solve 50+ two-pointer problems across sites.

---

## **Part 8: The Psychology of Mastery**

### **Avoid Tutorial Hell**

**Wrong approach:**
- Watch 10 videos on two pointers
- Read 5 articles
- Never actually code

**Right approach:**
1. Watch ONE quality explanation (NeetCode)
2. Code it yourself
3. Struggle (this is where learning happens)
4. If stuck >30 min, look at solution structure (not full code)
5. Reimplement from memory

---

### **Flow State Optimization**

**For maximum learning:**
- **Pomodoro:** 25 min focused coding + 5 min review
- **Progressive difficulty:** Start easy, gradually increase
- **Reflection:** After each session, write down what you learned
- **Sleep on it:** Your brain consolidates patterns during sleep

---

### **Measuring Progress**

**Track these metrics:**
1. **Recognition time:** How fast do you identify the pattern?
2. **Implementation time:** How long to code the solution?
3. **Bug rate:** How many bugs before AC (Accepted)?
4. **Explanation clarity:** Can you teach it to someone?

**Target (after 3 months):**
- Recognition: <2 minutes
- Implementation: <15 minutes
- Bug rate: <2 bugs per problem
- Explanation: Clear, confident, correct

---

## **Your 30-Day Action Plan**

**Week 1:**
- Day 1-2: Two Sum II (3 implementations)
- Day 3-4: Valid Palindrome + Container With Most Water
- Day 5-7: 3Sum (deep dive)

**Week 2:**
- Day 8-9: 3Sum Closest + 4Sum
- Day 10-12: Remove Duplicates + Trapping Rain Water
- Day 13-14: Review & re-implement all from memory

**Week 3:**
- Day 15-17: Sliding window problems (Type 2)
- Day 18-20: Fast-slow pointers (Type 3)
- Day 21: Mixed problem set (random from all types)

**Week 4:**
- Day 22-25: Codeforces "two pointers" problems
- Day 26-28: Implement classic algorithms using pattern
- Day 29-30: Teach the pattern (write blog/explain to friend)

---

## **Final Wisdom**

**Pattern recognition is NOT magic—it's exposure + reflection.**

The difference between you now and you in 3 months:
- **Now:** "I need to check all combinations" (brute force thinking)
- **3 months:** "Sorted array + converging pointers" (instant recognition)

**This only happens through:**
1. ✅ Deliberate practice (not random LeetCode grinding)
2. ✅ Spaced repetition (not one-and-done)
3. ✅ Active reflection (not passive watching)

**You're building neural pathways. Each problem strengthens them.**

---

## **Resources Summary**

**Must-watch:**
- NeetCode Two Pointers playlist

**Must-read:**
- CSES Competitive Programming Handbook (free)
- Elements of Programming Interviews (deep understanding)

**Must-solve:**
- LeetCode: 167, 125, 15, 11, 42, 26, 16, 18
- Codeforces: Two pointers tag (first 20 problems)

**Must-track:**
- Notion/Obsidian page with: problem → pattern → key insight

---

**Now stop reading and START CODING. The pattern is earned through repetition, not revelation.**

**Go solve Two Sum II right now. In all three languages. Without looking at solutions. Then come back stronger.** 🔥