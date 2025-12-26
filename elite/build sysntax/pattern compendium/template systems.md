# DSA Pattern Templates - Production-Ready Code

## 🎯 How to Use These Templates

1. **Copy the template** for your pattern + language
2. **Fill in the problem-specific logic** (marked with `// TODO` comments)
3. **Keep the structure intact** - it's optimized for clarity and performance
4. **Understand each section** before using (explanations provided)

**Cognitive Benefit**: Templates eliminate "What structure should I use?" questions, letting you focus 100% on algorithmic thinking.

---

## 1️⃣ TWO POINTERS PATTERN

### Concept Flow
```
[1, 2, 3, 4, 5, 6]
 ↑              ↑
left          right

Move pointers based on condition:
- If sum < target: left++
- If sum > target: right--
- If sum == target: found!
```

### Python Template

```python
def two_pointers(arr):
    """
    Two Pointers Template - O(n) time, O(1) space
    
    Use when:
    - Array is sorted (or can be sorted)
    - Finding pairs/triplets
    - Partitioning problems
    """
    left, right = 0, len(arr) - 1
    result = []  # Or could be int, bool, etc.
    
    while left < right:
        # Calculate current state
        current_sum = arr[left] + arr[right]
        
        # TODO: Replace with your condition
        if current_sum == target:
            result.append([arr[left], arr[right]])
            left += 1
            right -= 1
            
        elif current_sum < target:
            left += 1  # Need larger sum
            
        else:
            right -= 1  # Need smaller sum
    
    return result


# Variant: Same Direction Two Pointers (Fast & Slow)
def fast_slow_pointers(arr):
    """
    Fast & Slow Pointers - O(n) time, O(1) space
    
    Use when:
    - In-place array modification
    - Removing duplicates
    - Detecting cycles
    """
    slow = 0
    
    for fast in range(len(arr)):
        # TODO: Replace with your condition
        if arr[fast] != 0:  # Example: move non-zero elements
            arr[slow], arr[fast] = arr[fast], arr[slow]
            slow += 1
    
    return slow  # New length or position
```

### Rust Template

```rust
// Two Pointers - O(n) time, O(1) space
fn two_pointers(arr: &[i32], target: i32) -> Vec<(i32, i32)> {
    let mut result = Vec::new();
    let mut left = 0;
    let mut right = arr.len() - 1;
    
    while left < right {
        let current_sum = arr[left] + arr[right];
        
        // TODO: Replace with your condition
        match current_sum.cmp(&target) {
            std::cmp::Ordering::Equal => {
                result.push((arr[left], arr[right]));
                left += 1;
                right -= 1;
            }
            std::cmp::Ordering::Less => left += 1,
            std::cmp::Ordering::Greater => right -= 1,
        }
    }
    
    result
}

// Fast & Slow Pointers (in-place modification)
fn fast_slow_pointers(arr: &mut Vec<i32>) -> usize {
    let mut slow = 0;
    
    for fast in 0..arr.len() {
        // TODO: Replace with your condition
        if arr[fast] != 0 {
            arr.swap(slow, fast);
            slow += 1;
        }
    }
    
    slow
}
```

### Go Template

```go
package main

// TwoPointers - O(n) time, O(1) space
func TwoPointers(arr []int, target int) [][]int {
    result := [][]int{}
    left, right := 0, len(arr)-1
    
    for left < right {
        currentSum := arr[left] + arr[right]
        
        // TODO: Replace with your condition
        if currentSum == target {
            result = append(result, []int{arr[left], arr[right]})
            left++
            right--
        } else if currentSum < target {
            left++
        } else {
            right--
        }
    }
    
    return result
}

// FastSlowPointers - O(n) time, O(1) space
func FastSlowPointers(arr []int) int {
    slow := 0
    
    for fast := 0; fast < len(arr); fast++ {
        // TODO: Replace with your condition
        if arr[fast] != 0 {
            arr[slow], arr[fast] = arr[fast], arr[slow]
            slow++
        }
    }
    
    return slow
}
```

### C++ Template

```cpp
#include <vector>
#include <algorithm>

// Two Pointers - O(n) time, O(1) space
std::vector<std::pair<int, int>> twoPointers(
    const std::vector<int>& arr, 
    int target
) {
    std::vector<std::pair<int, int>> result;
    int left = 0, right = arr.size() - 1;
    
    while (left < right) {
        int currentSum = arr[left] + arr[right];
        
        // TODO: Replace with your condition
        if (currentSum == target) {
            result.push_back({arr[left], arr[right]});
            left++;
            right--;
        } else if (currentSum < target) {
            left++;
        } else {
            right--;
        }
    }
    
    return result;
}

// Fast & Slow Pointers - O(n) time, O(1) space
int fastSlowPointers(std::vector<int>& arr) {
    int slow = 0;
    
    for (int fast = 0; fast < arr.size(); fast++) {
        // TODO: Replace with your condition
        if (arr[fast] != 0) {
            std::swap(arr[slow], arr[fast]);
            slow++;
        }
    }
    
    return slow;
}
```

---

## 2️⃣ SLIDING WINDOW PATTERN

### Concept Flow
```
Fixed Size Window:
[1, 2, 3, 4, 5, 6]
 [-----]           k=3, sum=6
   [-----]         k=3, sum=9
     [-----]       k=3, sum=12

Variable Size Window:
[1, 2, 3, 4, 5]
 [-----]         expand: sum=6
 [-------]       expand: sum=10
   [-----]       contract: sum=9
```

### Python Template

```python
def sliding_window_fixed(arr, k):
    """
    Fixed Size Sliding Window - O(n) time, O(1) space
    
    Use when:
    - Window size is constant (k elements)
    - Finding max/min/average in subarrays of size k
    """
    if len(arr) < k:
        return 0
    
    # Initialize first window
    window_sum = sum(arr[:k])
    max_sum = window_sum
    
    # Slide the window
    for i in range(k, len(arr)):
        window_sum += arr[i] - arr[i - k]  # Add new, remove old
        max_sum = max(max_sum, window_sum)
    
    return max_sum


def sliding_window_variable(arr, target):
    """
    Variable Size Sliding Window - O(n) time, O(1) space
    
    Use when:
    - Finding minimum/maximum window satisfying condition
    - Substring problems
    - Subarrays with constraints
    """
    from collections import defaultdict
    
    left = 0
    window_map = defaultdict(int)  # Track window state
    result = float('inf')  # Or 0, [], etc.
    
    for right in range(len(arr)):
        # Expand window: add arr[right]
        window_map[arr[right]] += 1
        
        # Contract window while condition is met
        while is_valid(window_map):  # TODO: Define your condition
            result = min(result, right - left + 1)
            
            # Shrink from left
            window_map[arr[left]] -= 1
            if window_map[arr[left]] == 0:
                del window_map[arr[left]]
            left += 1
    
    return result if result != float('inf') else 0


def is_valid(window_map):
    """TODO: Replace with your validity check"""
    return len(window_map) >= 2  # Example condition
```

### Rust Template

```rust
use std::collections::HashMap;

// Fixed Size Sliding Window - O(n) time, O(1) space
fn sliding_window_fixed(arr: &[i32], k: usize) -> i32 {
    if arr.len() < k {
        return 0;
    }
    
    let mut window_sum: i32 = arr[..k].iter().sum();
    let mut max_sum = window_sum;
    
    for i in k..arr.len() {
        window_sum += arr[i] - arr[i - k];
        max_sum = max_sum.max(window_sum);
    }
    
    max_sum
}

// Variable Size Sliding Window - O(n) time, O(n) space
fn sliding_window_variable(arr: &[i32]) -> usize {
    let mut left = 0;
    let mut window_map: HashMap<i32, usize> = HashMap::new();
    let mut result = usize::MAX;
    
    for right in 0..arr.len() {
        // Expand window
        *window_map.entry(arr[right]).or_insert(0) += 1;
        
        // Contract window while valid
        while is_valid(&window_map) {
            result = result.min(right - left + 1);
            
            // Shrink from left
            if let Some(count) = window_map.get_mut(&arr[left]) {
                *count -= 1;
                if *count == 0 {
                    window_map.remove(&arr[left]);
                }
            }
            left += 1;
        }
    }
    
    if result == usize::MAX { 0 } else { result }
}

fn is_valid(window_map: &HashMap<i32, usize>) -> bool {
    // TODO: Replace with your condition
    window_map.len() >= 2
}
```

### Go Template

```go
package main

// SlidingWindowFixed - O(n) time, O(1) space
func SlidingWindowFixed(arr []int, k int) int {
    if len(arr) < k {
        return 0
    }
    
    windowSum := 0
    for i := 0; i < k; i++ {
        windowSum += arr[i]
    }
    maxSum := windowSum
    
    for i := k; i < len(arr); i++ {
        windowSum += arr[i] - arr[i-k]
        if windowSum > maxSum {
            maxSum = windowSum
        }
    }
    
    return maxSum
}

// SlidingWindowVariable - O(n) time, O(n) space
func SlidingWindowVariable(arr []int) int {
    left := 0
    windowMap := make(map[int]int)
    result := int(^uint(0) >> 1) // Max int
    
    for right := 0; right < len(arr); right++ {
        // Expand window
        windowMap[arr[right]]++
        
        // Contract while valid
        for isValid(windowMap) {
            length := right - left + 1
            if length < result {
                result = length
            }
            
            // Shrink from left
            windowMap[arr[left]]--
            if windowMap[arr[left]] == 0 {
                delete(windowMap, arr[left])
            }
            left++
        }
    }
    
    if result == int(^uint(0) >> 1) {
        return 0
    }
    return result
}

func isValid(windowMap map[int]int) bool {
    // TODO: Replace with your condition
    return len(windowMap) >= 2
}
```

### C++ Template

```cpp
#include <unordered_map>
#include <vector>
#include <limits>

// Fixed Size Sliding Window - O(n) time, O(1) space
int slidingWindowFixed(const std::vector<int>& arr, int k) {
    if (arr.size() < k) return 0;
    
    int windowSum = 0;
    for (int i = 0; i < k; i++) {
        windowSum += arr[i];
    }
    int maxSum = windowSum;
    
    for (int i = k; i < arr.size(); i++) {
        windowSum += arr[i] - arr[i - k];
        maxSum = std::max(maxSum, windowSum);
    }
    
    return maxSum;
}

// Variable Size Sliding Window - O(n) time, O(n) space
int slidingWindowVariable(const std::vector<int>& arr) {
    int left = 0;
    std::unordered_map<int, int> windowMap;
    int result = std::numeric_limits<int>::max();
    
    for (int right = 0; right < arr.size(); right++) {
        // Expand window
        windowMap[arr[right]]++;
        
        // Contract while valid
        while (isValid(windowMap)) {
            result = std::min(result, right - left + 1);
            
            // Shrink from left
            windowMap[arr[left]]--;
            if (windowMap[arr[left]] == 0) {
                windowMap.erase(arr[left]);
            }
            left++;
        }
    }
    
    return result == std::numeric_limits<int>::max() ? 0 : result;
}

bool isValid(const std::unordered_map<int, int>& windowMap) {
    // TODO: Replace with your condition
    return windowMap.size() >= 2;
}
```

---

## 3️⃣ BINARY SEARCH PATTERN

### Concept Flow
```
Sorted Array: [1, 3, 5, 7, 9, 11, 13]
               0  1  2  3  4   5   6

Target = 7
Step 1: mid = 3, arr[3] = 7 ✓ Found!

Target = 6
Step 1: mid = 3, arr[3] = 7 > 6 → search left
Step 2: mid = 1, arr[1] = 3 < 6 → search right
Step 3: mid = 2, arr[2] = 5 < 6 → not found
```

### Python Template

```python
def binary_search(arr, target):
    """
    Standard Binary Search - O(log n) time, O(1) space
    
    Use when:
    - Array is sorted
    - Finding exact element
    """
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = left + (right - left) // 2  # Avoid overflow
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1  # Not found


def binary_search_leftmost(arr, target):
    """
    Find leftmost (first) occurrence - O(log n) time
    
    Use when:
    - Finding insertion position
    - First occurrence in duplicates
    """
    left, right = 0, len(arr)
    
    while left < right:
        mid = left + (right - left) // 2
        
        if arr[mid] < target:
            left = mid + 1
        else:
            right = mid  # Don't exclude mid
    
    return left


def binary_search_on_answer(arr, check_function):
    """
    Binary Search on Answer Space - O(n log m) time
    Where m is the search space range
    
    Use when:
    - Optimization problems (minimize/maximize)
    - Monotonic feasibility function
    """
    left, right = min(arr), max(arr)  # TODO: Define search space
    result = left
    
    while left <= right:
        mid = left + (right - left) // 2
        
        # TODO: Replace with your feasibility check
        if check_function(arr, mid):
            result = mid
            right = mid - 1  # Try smaller (or left = mid + 1 for larger)
        else:
            left = mid + 1
    
    return result
```

### Rust Template

```rust
// Standard Binary Search - O(log n) time, O(1) space
fn binary_search(arr: &[i32], target: i32) -> Option<usize> {
    let mut left = 0;
    let mut right = arr.len();
    
    while left < right {
        let mid = left + (right - left) / 2;
        
        match arr[mid].cmp(&target) {
            std::cmp::Ordering::Equal => return Some(mid),
            std::cmp::Ordering::Less => left = mid + 1,
            std::cmp::Ordering::Greater => right = mid,
        }
    }
    
    None
}

// Find leftmost occurrence - O(log n) time
fn binary_search_leftmost(arr: &[i32], target: i32) -> usize {
    let mut left = 0;
    let mut right = arr.len();
    
    while left < right {
        let mid = left + (right - left) / 2;
        
        if arr[mid] < target {
            left = mid + 1;
        } else {
            right = mid;
        }
    }
    
    left
}

// Binary Search on Answer Space - O(n log m) time
fn binary_search_on_answer<F>(arr: &[i32], check: F) -> i32
where
    F: Fn(&[i32], i32) -> bool,
{
    let mut left = *arr.iter().min().unwrap();
    let mut right = *arr.iter().max().unwrap();
    let mut result = left;
    
    while left <= right {
        let mid = left + (right - left) / 2;
        
        if check(arr, mid) {
            result = mid;
            right = mid - 1;
        } else {
            left = mid + 1;
        }
    }
    
    result
}
```

### Go Template

```go
package main

// BinarySearch - O(log n) time, O(1) space
func BinarySearch(arr []int, target int) int {
    left, right := 0, len(arr)-1
    
    for left <= right {
        mid := left + (right-left)/2
        
        if arr[mid] == target {
            return mid
        } else if arr[mid] < target {
            left = mid + 1
        } else {
            right = mid - 1
        }
    }
    
    return -1
}

// BinarySearchLeftmost - O(log n) time
func BinarySearchLeftmost(arr []int, target int) int {
    left, right := 0, len(arr)
    
    for left < right {
        mid := left + (right-left)/2
        
        if arr[mid] < target {
            left = mid + 1
        } else {
            right = mid
        }
    }
    
    return left
}

// BinarySearchOnAnswer - O(n log m) time
func BinarySearchOnAnswer(arr []int, check func([]int, int) bool) int {
    left, right := arr[0], arr[0]
    for _, v := range arr {
        if v < left {
            left = v
        }
        if v > right {
            right = v
        }
    }
    
    result := left
    for left <= right {
        mid := left + (right-left)/2
        
        if check(arr, mid) {
            result = mid
            right = mid - 1
        } else {
            left = mid + 1
        }
    }
    
    return result
}
```

### C++ Template

```cpp
#include <vector>
#include <algorithm>

// Standard Binary Search - O(log n) time, O(1) space
int binarySearch(const std::vector<int>& arr, int target) {
    int left = 0, right = arr.size() - 1;
    
    while (left <= right) {
        int mid = left + (right - left) / 2;
        
        if (arr[mid] == target) {
            return mid;
        } else if (arr[mid] < target) {
            left = mid + 1;
        } else {
            right = mid - 1;
        }
    }
    
    return -1;
}

// Find leftmost occurrence - O(log n) time
int binarySearchLeftmost(const std::vector<int>& arr, int target) {
    int left = 0, right = arr.size();
    
    while (left < right) {
        int mid = left + (right - left) / 2;
        
        if (arr[mid] < target) {
            left = mid + 1;
        } else {
            right = mid;
        }
    }
    
    return left;
}

// Binary Search on Answer Space - O(n log m) time
template<typename CheckFunc>
int binarySearchOnAnswer(const std::vector<int>& arr, CheckFunc check) {
    int left = *std::min_element(arr.begin(), arr.end());
    int right = *std::max_element(arr.begin(), arr.end());
    int result = left;
    
    while (left <= right) {
        int mid = left + (right - left) / 2;
        
        if (check(arr, mid)) {
            result = mid;
            right = mid - 1;
        } else {
            left = mid + 1;
        }
    }
    
    return result;
}
```

---

## 4️⃣ DEPTH-FIRST SEARCH (DFS) PATTERN

### Concept Flow
```
Tree DFS:
      1
     / \
    2   3
   / \
  4   5

Preorder:  1 → 2 → 4 → 5 → 3
Inorder:   4 → 2 → 5 → 1 → 3
Postorder: 4 → 5 → 2 → 3 → 1
```

### Python Template

```python
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def dfs_recursive(root):
    """
    Recursive DFS - O(n) time, O(h) space (h = height)
    
    Use when:
    - Tree traversal
    - Path problems
    - Clean, readable code preferred
    """
    if not root:
        return  # Base case
    
    # Preorder: Process node first
    # TODO: Process current node
    print(root.val)
    
    # Recurse on children
    dfs_recursive(root.left)
    dfs_recursive(root.right)
    
    # Postorder: Process after children
    # TODO: Aggregate results from children


def dfs_iterative(root):
    """
    Iterative DFS using Stack - O(n) time, O(h) space
    
    Use when:
    - Avoiding recursion limits
    - Need explicit control over stack
    """
    if not root:
        return
    
    stack = [root]
    
    while stack:
        node = stack.pop()
        
        # TODO: Process current node
        print(node.val)
        
        # Add children (right first for left-to-right traversal)
        if node.right:
            stack.append(node.right)
        if node.left:
            stack.append(node.left)


def dfs_with_path(root, target):
    """
    DFS with Path Tracking - O(n) time, O(h) space
    
    Use when:
    - Finding paths
    - Backtracking problems
    """
    def helper(node, path):
        if not node:
            return False
        
        path.append(node.val)
        
        # Check if this is target
        if node.val == target:
            return True
        
        # Try left and right subtrees
        if helper(node.left, path) or helper(node.right, path):
            return True
        
        # Backtrack
        path.pop()
        return False
    
    path = []
    helper(root, path)
    return path


# Graph DFS
def dfs_graph(graph, start):
    """
    Graph DFS - O(V + E) time, O(V) space
    
    Use when:
    - Connected components
    - Cycle detection
    - Topological sort
    """
    visited = set()
    
    def dfs(node):
        if node in visited:
            return
        
        visited.add(node)
        # TODO: Process node
        print(node)
        
        for neighbor in graph[node]:
            dfs(neighbor)
    
    dfs(start)
    return visited
```

### Rust Template

```rust
use std::rc::Rc;
use std::cell::RefCell;
use std::collections::HashSet;

#[derive(Debug)]
struct TreeNode {
    val: i32,
    left: Option<Rc<RefCell<TreeNode>>>,
    right: Option<Rc<RefCell<TreeNode>>>,
}

impl TreeNode {
    fn new(val: i32) -> Self {
        TreeNode { val, left: None, right: None }
    }
}

// Recursive DFS - O(n) time, O(h) space
fn dfs_recursive(root: Option<Rc<RefCell<TreeNode>>>) {
    if let Some(node) = root {
        let node = node.borrow();
        
        // Preorder: Process current node
        println!("{}", node.val);
        
        // Recurse
        dfs_recursive(node.left.clone());
        dfs_recursive(node.right.clone());
    }
}

// Iterative DFS - O(n) time, O(h) space
fn dfs_iterative(root: Option<Rc<RefCell<TreeNode>>>) {
    if root.is_none() {
        return;
    }
    
    let mut stack = vec![root.unwrap()];
    
    while let Some(node_rc) = stack.pop() {
        let node = node_rc.borrow();
        
        // Process current node
        println!("{}", node.val);
        
        // Add children (right first)
        if let Some(ref right) = node.right {
            stack.push(right.clone());
        }
        if let Some(ref left) = node.left {
            stack.push(left.clone());
        }
    }
}

// Graph DFS - O(V + E) time, O(V) space
fn dfs_graph(graph: &Vec<Vec<usize>>, start: usize) -> HashSet<usize> {
    let mut visited = HashSet::new();
    
    fn dfs(node: usize, graph: &Vec<Vec<usize>>, visited: &mut HashSet<usize>) {
        if visited.contains(&node) {
            return;
        }
        
        visited.insert(node);
        println!("{}", node);
        
        for &neighbor in &graph[node] {
            dfs(neighbor, graph, visited);
        }
    }
    
    dfs(start, graph, &mut visited);
    visited
}
```

### Go Template

```go
package main

type TreeNode struct {
    Val   int
    Left  *TreeNode
    Right *TreeNode
}

// DFSRecursive - O(n) time, O(h) space
func DFSRecursive(root *TreeNode) {
    if root == nil {
        return
    }
    
    // Preorder: Process current node
    // TODO: Process node
    println(root.Val)
    
    // Recurse
    DFSRecursive(root.Left)
    DFSRecursive(root.Right)
}

// DFSIterative - O(n) time, O(h) space
func DFSIterative(root *TreeNode) {
    if root == nil {
        return
    }
    
    stack := []*TreeNode{root}
    
    for len(stack) > 0 {
        node := stack[len(stack)-1]
        stack = stack[:len(stack)-1]
        
        // Process current node
        println(node.Val)
        
        // Add children (right first)
        if node.Right != nil {
            stack = append(stack, node.Right)
        }
        if node.Left != nil {
            stack = append(stack, node.Left)
        }
    }
}

// DFSGraph - O(V + E) time, O(V) space
func DFSGraph(graph [][]int, start int) map[int]bool {
    visited := make(map[int]bool)
    
    var dfs func(int)
    dfs = func(node int) {
        if visited[node] {
            return
        }
        
        visited[node] = true
        println(node)
        
        for _, neighbor := range graph[node] {
            dfs(neighbor)
        }
    }
    
    dfs(start)
    return visited
}
```

### C++ Template

```cpp
#include <stack>
#include <unordered_set>
#include <vector>

struct TreeNode {
    int val;
    TreeNode* left;
    TreeNode* right;
    TreeNode(int x) : val(x), left(nullptr), right(nullptr) {}
};

// Recursive DFS - O(n) time, O(h) space
void dfsRecursive(TreeNode* root) {
    if (!root) return;
    
    // Preorder: Process current node
    // TODO: Process node
    std::cout << root->val << std::endl;
    
    // Recurse
    dfsRecursive(root->left);
    dfsRecursive(root->right);
}

// Iterative DFS - O(n) time, O(h) space
void dfsIterative(TreeNode* root) {
    if (!root) return;
    
    std::stack<TreeNode*> stack;
    stack.push(root);
    
    while (!stack.empty()) {
        TreeNode* node = stack.top();
        stack.pop();
        
        // Process current node
        std::cout << node->val << std::endl;
        
        // Add children (right first)
        if (node->right) stack.push(node->right);
        if (node->left) stack.push(node->left);
    }
}

// Graph DFS - O(V + E) time, O(V) space
void dfsGraph(const std::vector<std::vector<int>>& graph, 
              int start, 
              std::unordered_set<int>& visited) {
    if (visited.count(start)) return;
    
    visited.insert(start);
    std::cout << start << std::endl;
    
    for (int neighbor : graph[start]) {
        dfsGraph(graph, neighbor, visited);
    }
}
```

---

## 5️⃣ BREADTH-FIRST SEARCH (BFS) PATTERN

### Concept Flow
```
Level-by-Level Traversal:
      1          Level 0
     / \
    2   3        Level 1
   / \
  4   5          Level 2

Queue: [1] → [2,3] → [3,4,5] → [4,5] → [5] → []
Output: 1, 2, 3, 4, 5
```

### Python Template

```python
from collections import deque

def bfs_tree(root):
    """
    Tree BFS Level-Order - O(n) time, O(w) space (w = max width)
    
    Use when:
    - Level-order traversal
    - Finding shortest path in unweighted graphs
    - Processing by levels
    """
    if not root:
        return []
    
    result = []
    queue = deque([root])
    
    while queue:
        level_size = len(queue)
        current_level = []
        
        for _ in range(level_size):
            node = queue.popleft()
            current_level.append(node.val)
            
            # Add children
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        
        result.append(current_level)
    
    return result


def bfs_graph(graph, start):
    """
    Graph BFS - O(V + E) time, O(V) space
    
    Use when:
    - Shortest path (unweighted)
    - Connected components
    - Minimum moves/steps problems
    """
    visited = {start}
    queue = deque([start])
    distance = {start: 0}
    
    while queue:
        node = queue.popleft()
        
        # TODO: Process node
        print(f"Node: {node}, Distance: {distance[node]}")
        
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                distance[neighbor] = distance[node] + 1
                queue.append(neighbor)
    
    return distance


def bfs_grid(grid):
    """
    Grid BFS (2D Matrix) - O(rows * cols) time and space
    
    Use when:
    - Matrix traversal
    - Finding shortest path in grid
    - Island problems
    """
    if not grid:
        return 0
    
    rows, cols = len(grid), len(grid[0])
    visited = set()
    queue = deque([(0, 0, 0)])  # (row, col, distance)
    visited.add((0, 0))
    
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # Right, Down, Left, Up
    
    while queue:
        row, col, dist = queue.popleft()
        
        # TODO: Check if reached target
        if row == rows - 1 and col == cols - 1:
            return dist
        
        # Explore 4 directions
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            
            # Check boundaries and visited
            if (0 <= new_row < rows and 
                0 <= new_col < cols and 
                (new_row, new_col) not in visited and
                grid[new_row][new_col] != 1):  # TODO: Your condition
                
                visited.add((new_row, new_col))
                queue.append((new_row, new_col, dist + 1))
    
    return -1  # Not reachable
```

### Rust Template

```rust
use std::collections::{VecDeque, HashSet};

// Tree BFS - O(n) time, O(w) space
fn bfs_tree(root: Option<Rc<RefCell<TreeNode>>>) -> Vec<Vec<i32>> {
    if root.is_none() {
        return vec![];
    }
    
    let mut result = Vec::new();
    let mut queue = VecDeque::new();
    queue.push_back(root.unwrap());
    
    while !queue.is_empty() {
        let level_size = queue.len();
        let mut current_level = Vec::new();
        
        for _ in 0..level_size {
            if let Some(node_rc) = queue.pop_front() {
                let node = node_rc.borrow();
                current_level.push(node.val);
                
                if let Some(ref left) = node.left {
                    queue.push_back(left.clone());
                }
                if let Some(ref right) = node.right {
                    queue.push_back(right.clone());
                }
            }
        }
        result.push(current_level);
    }
    
    result
}

// Graph BFS - O(V + E) time, O(V) space
fn bfs_graph(graph: &Vec<Vec<usize>>, start: usize) -> Vec<usize> {
    let mut visited = HashSet::new();
    let mut queue = VecDeque::new();
    let mut distance = vec![usize::MAX; graph.len()];
    
    visited.insert(start);
    queue.push_back(start);
    distance[start] = 0;
    
    while let Some(node) = queue.pop_front() {
        println!("Node: {}, Distance: {}", node, distance[node]);
        
        for &neighbor in &graph[node] {
            if !visited.contains(&neighbor) {
                visited.insert(neighbor);
                distance[neighbor] = distance[node] + 1;
                queue.push_back(neighbor);
            }
        }
    }
    
    distance
}

// Grid BFS - O(rows * cols) time and space
fn bfs_grid(grid: Vec<Vec<i32>>) -> i32 {
    if grid.is_empty() {
        return 0;
    }
    
    let (rows, cols) = (grid.len(), grid[0].len());
    let mut visited = HashSet::new();
    let mut queue = VecDeque::new();
    
    queue.push_back((0, 0, 0)); // (row, col, distance)
    visited.insert((0, 0));
    
    let directions = [(0, 1), (1, 0), (0, -1), (-1, 0)];
    
    while let Some((row, col, dist)) = queue.pop_front() {
        // Check if reached target
        if row == rows - 1 && col == cols - 1 {
            return dist;
        }
        
        for (dr, dc) in directions.iter() {
            let new_row = row as i32 + dr;
            let new_col = col as i32 + dc;
            
            if new_row >= 0 && new_row < rows as i32 &&
               new_col >= 0 && new_col < cols as i32 {
                let (nr, nc) = (new_row as usize, new_col as usize);
                
                if !visited.contains(&(nr, nc)) && grid[nr][nc] != 1 {
                    visited.insert((nr, nc));
                    queue.push_back((nr, nc, dist + 1));
                }
            }
        }
    }
    
    -1
}
```

### Go Template

```go
package main

import "container/list"

// BFSTree - O(n) time, O(w) space
func BFSTree(root *TreeNode) [][]int {
    if root == nil {
        return [][]int{}
    }
    
    result := [][]int{}
    queue := list.New()
    queue.PushBack(root)
    
    for queue.Len() > 0 {
        levelSize := queue.Len()
        currentLevel := []int{}
        
        for i := 0; i < levelSize; i++ {
            element := queue.Front()
            node := element.Value.(*TreeNode)
            queue.Remove(element)
            
            currentLevel = append(currentLevel, node.Val)
            
            if node.Left != nil {
                queue.PushBack(node.Left)
            }
            if node.Right != nil {
                queue.PushBack(node.Right)
            }
        }
        result = append(result, currentLevel)
    }
    
    return result
}

// BFSGraph - O(V + E) time, O(V) space
func BFSGraph(graph [][]int, start int) []int {
    visited := make(map[int]bool)
    queue := []int{start}
    distance := make([]int, len(graph))
    for i := range distance {
        distance[i] = -1
    }
    
    visited[start] = true
    distance[start] = 0
    
    for len(queue) > 0 {
        node := queue[0]
        queue = queue[1:]
        
        println("Node:", node, "Distance:", distance[node])
        
        for _, neighbor := range graph[node] {
            if !visited[neighbor] {
                visited[neighbor] = true
                distance[neighbor] = distance[node] + 1
                queue = append(queue, neighbor)
            }
        }
    }
    
    return distance
}

// BFSGrid - O(rows * cols) time and space
func BFSGrid(grid [][]int) int {
    if len(grid) == 0 {
        return 0
    }
    
    rows, cols := len(grid), len(grid[0])
    visited := make(map[[2]int]bool)
    queue := [][3]int{{0, 0, 0}} // row, col, distance
    visited[[2]int{0, 0}] = true
    
    directions := [4][2]int{{0, 1}, {1, 0}, {0, -1}, {-1, 0}}
    
    for len(queue) > 0 {
        curr := queue[0]
        queue = queue[1:]
        row, col, dist := curr[0], curr[1], curr[2]
        
        // Check if reached target
        if row == rows-1 && col == cols-1 {
            return dist
        }
        
        for _, dir := range directions {
            newRow, newCol := row+dir[0], col+dir[1]
            
            if newRow >= 0 && newRow < rows &&
               newCol >= 0 && newCol < cols &&
               !visited[[2]int{newRow, newCol}] &&
               grid[newRow][newCol] != 1 {
                
                visited[[2]int{newRow, newCol}] = true
                queue = append(queue, [3]int{newRow, newCol, dist + 1})
            }
        }
    }
    
    return -1
}
```

### C++ Template

```cpp
#include <queue>
#include <vector>
#include <unordered_set>

// Tree BFS - O(n) time, O(w) space
std::vector<std::vector<int>> bfsTree(TreeNode* root) {
    std::vector<std::vector<int>> result;
    if (!root) return result;
    
    std::queue<TreeNode*> queue;
    queue.push(root);
    
    while (!queue.empty()) {
        int levelSize = queue.size();
        std::vector<int> currentLevel;
        
        for (int i = 0; i < levelSize; i++) {
            TreeNode* node = queue.front();
            queue.pop();
            currentLevel.push_back(node->val);
            
            if (node->left) queue.push(node->left);
            if (node->right) queue.push(node->right);
        }
        result.push_back(currentLevel);
    }
    
    return result;
}

// Graph BFS - O(V + E) time, O(V) space
std::vector<int> bfsGraph(const std::vector<std::vector<int>>& graph, int start) {
    std::unordered_set<int> visited;
    std::queue<int> queue;
    std::vector<int> distance(graph.size(), -1);
    
    visited.insert(start);
    queue.push(start);
    distance[start] = 0;
    
    while (!queue.empty()) {
        int node = queue.front();
        queue.pop();
        
        for (int neighbor : graph[node]) {
            if (visited.find(neighbor) == visited.end()) {
                visited.insert(neighbor);
                distance[neighbor] = distance[node] + 1;
                queue.push(neighbor);
            }
        }
    }
    
    return distance;
}

// Grid BFS - O(rows * cols) time and space
int bfsGrid(const std::vector<std::vector<int>>& grid) {
    if (grid.empty()) return 0;
    
    int rows = grid.size(), cols = grid[0].size();
    std::set<std::pair<int, int>> visited;
    std::queue<std::tuple<int, int, int>> queue;
    
    queue.push({0, 0, 0}); // row, col, distance
    visited.insert({0, 0});
    
    int directions[4][2] = {{0, 1}, {1, 0}, {0, -1}, {-1, 0}};
    
    while (!queue.empty()) {
        auto [row, col, dist] = queue.front();
        queue.pop();
        
        if (row == rows - 1 && col == cols - 1) {
            return dist;
        }
        
        for (auto& dir : directions) {
            int newRow = row + dir[0];
            int newCol = col + dir[1];
            
            if (newRow >= 0 && newRow < rows &&
                newCol >= 0 && newCol < cols &&
                visited.find({newRow, newCol}) == visited.end() &&
                grid[newRow][newCol] != 1) {
                
                visited.insert({newRow, newCol});
                queue.push({newRow, newCol, dist + 1});
            }
        }
    }
    
    return -1;
}
```

---

## 6️⃣ DYNAMIC PROGRAMMING PATTERN

### Concept Flow
```
1D DP (Fibonacci):
F(0) = 0, F(1) = 1
F(n) = F(n-1) + F(n-2)

dp[0] = 0
dp[1] = 1
dp[2] = dp[1] + dp[0] = 1
dp[3] = dp[2] + dp[1] = 2
dp[4] = dp[3] + dp[2] = 3

2D DP (Grid Paths):
Start → → → Goal
  ↓   → → →
  ↓   ↓ → →
  
dp[i][j] = dp[i-1][j] + dp[i][j-1]
```

### Python Template

```python
def dp_1d(n):
    """
    1D Dynamic Programming - O(n) time, O(n) space
    
    Use when:
    - Sequential decision-making
    - Depends on previous states
    - Examples: Fibonacci, climbing stairs, house robber
    """
    if n <= 1:
        return n
    
    # Initialize DP array
    dp = [0] * (n + 1)
    dp[0], dp[1] = 0, 1  # TODO: Set base cases
    
    # Fill DP array
    for i in range(2, n + 1):
        # TODO: Define state transition
        dp[i] = dp[i-1] + dp[i-2]  # Example: Fibonacci
    
    return dp[n]


def dp_1d_optimized(n):
    """
    Space-Optimized 1D DP - O(n) time, O(1) space
    
    Use when:
    - Only need previous few states
    - Space constraint is critical
    """
    if n <= 1:
        return n
    
    prev2, prev1 = 0, 1
    
    for i in range(2, n + 1):
        current = prev1 + prev2
        prev2, prev1 = prev1, current
    
    return prev1


def dp_2d(grid):
    """
    2D Dynamic Programming - O(m*n) time, O(m*n) space
    
    Use when:
    - Grid/matrix problems
    - Two-dimensional state
    - Examples: unique paths, longest common subsequence
    """
    if not grid:
        return 0
    
    rows, cols = len(grid), len(grid[0])
    dp = [[0] * cols for _ in range(rows)]
    
    # Base cases
    dp[0][0] = grid[0][0]  # TODO: Initialize
    
    # Fill first row and column
    for i in range(1, rows):
        dp[i][0] = dp[i-1][0] + grid[i][0]
    for j in range(1, cols):
        dp[0][j] = dp[0][j-1] + grid[0][j]
    
    # Fill rest of table
    for i in range(1, rows):
        for j in range(1, cols):
            # TODO: Define state transition
            dp[i][j] = min(dp[i-1][j], dp[i][j-1]) + grid[i][j]
    
    return dp[rows-1][cols-1]


def knapsack_01(weights, values, capacity):
    """
    0/1 Knapsack - O(n*W) time, O(n*W) space
    
    Use when:
    - Subset selection with constraints
    - Each item used at most once
    """
    n = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        for w in range(capacity + 1):
            # Don't take item i-1
            dp[i][w] = dp[i-1][w]
            
            # Take item i-1 if it fits
            if weights[i-1] <= w:
                dp[i][w] = max(dp[i][w], 
                              dp[i-1][w - weights[i-1]] + values[i-1])
    
    return dp[n][capacity]
```

### Rust Template

```rust
// 1D DP - O(n) time, O(n) space
fn dp_1d(n: usize) -> i64 {
    if n <= 1 {
        return n as i64;
    }
    
    let mut dp = vec![0i64; n + 1];
    dp[0] = 0;
    dp[1] = 1;
    
    for i in 2..=n {
        dp[i] = dp[i-1] + dp[i-2];
    }
    
    dp[n]
}

// Space-Optimized 1D DP - O(n) time, O(1) space
fn dp_1d_optimized(n: usize) -> i64 {
    if n <= 1 {
        return n as i64;
    }
    
    let (mut prev2, mut prev1) = (0i64, 1i64);
    
    for _ in 2..=n {
        let current = prev1 + prev2;
        prev2 = prev1;
        prev1 = current;
    }
    
    prev1
}

// 2D DP - O(m*n) time, O(m*n) space
fn dp_2d(grid: Vec<Vec<i32>>) -> i32 {
    if grid.is_empty() {
        return 0;
    }
    
    let (rows, cols) = (grid.len(), grid[0].len());
    let mut dp = vec![vec![0; cols]; rows];
    
    dp[0][0] = grid[0][0];
    
    // Fill first row and column
    for i in 1..rows {
        dp[i][0] = dp[i-1][0] + grid[i][0];
    }
    for j in 1..cols {
        dp[0][j] = dp[0][j-1] + grid[0][j];
    }
    
    // Fill rest
    for i in 1..rows {
        for j in 1..cols {
            dp[i][j] = dp[i-1][j].min(dp[i][j-1]) + grid[i][j];
        }
    }
    
    dp[rows-1][cols-1]
}

// 0/1 Knapsack - O(n*W) time, O(n*W) space
fn knapsack_01(weights: &[i32], values: &[i32], capacity: i32) -> i32 {
    let n = weights.len();
    let mut dp = vec![vec![0; capacity as usize + 1]; n + 1];
    
    for i in 1..=n {
        for w in 0..=capacity as usize {
            dp[i][w] = dp[i-1][w];
            
            if weights[i-1] as usize <= w {
                dp[i][w] = dp[i][w].max(
                    dp[i-1][w - weights[i-1] as usize] + values[i-1]
                );
            }
        }
    }
    
    dp[n][capacity as usize]
}
```

### Go Template

```go
package main

// DP1D - O(n) time, O(n) space
func DP1D(n int) int64 {
    if n <= 1 {
        return int64(n)
    }
    
    dp := make([]int64, n+1)
    dp[0], dp[1] = 0, 1
    
    for i := 2; i <= n; i++ {
        dp[i] = dp[i-1] + dp[i-2]
    }
    
    return dp[n]
}

// DP1DOptimized - O(n) time, O(1) space
func DP1DOptimized(n int) int64 {
    if n <= 1 {
        return int64(n)
    }
    
    prev2, prev1 := int64(0), int64(1)
    
    for i := 2; i <= n; i++ {
        current := prev1 + prev2
        prev2, prev1 = prev1, current
    }
    
    return prev1
}

// DP2D - O(m*n) time, O(m*n) space
func DP2D(grid [][]int) int {
    if len(grid) == 0 {
        return 0
    }
    
    rows, cols := len(grid), len(grid[0])
    dp := make([][]int, rows)
    for i := range dp {
        dp[i] = make([]int, cols)
    }
    
    dp[0][0] = grid[0][0]
    
    // Fill first row and column
    for i := 1; i < rows; i++ {
        dp[i][0] = dp[i-1][0] + grid[i][0]
    }
    for j := 1; j < cols; j++ {
        dp[0][j] = dp[0][j-1] + grid[0][j]
    }
    
    // Fill rest
    for i := 1; i < rows; i++ {
        for j := 1; j < cols; j++ {
            dp[i][j] = min(dp[i-1][j], dp[i][j-1]) + grid[i][j]
        }
    }
    
    return dp[rows-1][cols-1]
}

func min(a, b int) int {
    if a < b {
        return a
    }
    return b
}

// Knapsack01 - O(n*W) time, O(n*W) space
func Knapsack01(weights, values []int, capacity int) int {
    n := len(weights)
    dp := make([][]int, n+1)
    for i := range dp {
        dp[i] = make([]int, capacity+1)
    }
    
    for i := 1; i <= n; i++ {
        for w := 0; w <= capacity; w++ {
            dp[i][w] = dp[i-1][w]
            
            if weights[i-1] <= w {
                take := dp[i-1][w-weights[i-1]] + values[i-1]
                if take > dp[i][w] {
                    dp[i][w] = take
                }
            }
        }
    }
    
    return dp[n][capacity]
}
```

### C++ Template

```cpp
#include <vector>
#include <algorithm>

// 1D DP - O(n) time, O(n) space
long long dp1D(int n) {
    if (n <= 1) return n;
    
    std::vector<long long> dp(n + 1, 0);
    dp[0] = 0;
    dp[1] = 1;
    
    for (int i = 2; i <= n; i++) {
        dp[i] = dp[i-1] + dp[i-2];
    }
    
    return dp[n];
}

// Space-Optimized 1D DP - O(n) time, O(1) space
long long dp1DOptimized(int n) {
    if (n <= 1) return n;
    
    long long prev2 = 0, prev1 = 1;
    
    for (int i = 2; i <= n; i++) {
        long long current = prev1 + prev2;
        prev2 = prev1;
        prev1 = current;
    }
    
    return prev1;
}

// 2D DP - O(m*n) time, O(m*n) space
int dp2D(const std::vector<std::vector<int>>& grid) {
    if (grid.empty()) return 0;
    
    int rows = grid.size(), cols = grid[0].size();
    std::vector<std::vector<int>> dp(rows, std::vector<int>(cols, 0));
    
    dp[0][0] = grid[0][0];
    
    // Fill first row and column
    for (int i = 1; i < rows; i++) {
        dp[i][0] = dp[i-1][0] + grid[i][0];
    }
    for (int j = 1; j < cols; j++) {
        dp[0][j] = dp[0][j-1] + grid[0][j];
    }
    
    // Fill rest
    for (int i = 1; i < rows; i++) {
        for (j = 1; j < cols; j++) {
            dp[i][j] = std::min(dp[i-1][j], dp[i][j-1]) + grid[i][j];
        }
    }
    
    return dp[rows-1][cols-1];
}

// 0/1 Knapsack - O(n*W) time, O(n*W) space
int knapsack01(const std::vector<int>& weights, 
               const std::vector<int>& values, 
               int capacity) {
    int n = weights.size();
    std::vector<std::vector<int>> dp(n + 1, std::vector<int>(capacity + 1, 0));
    
    for (int i = 1; i <= n; i++) {
        for (int w = 0; w <= capacity; w++) {
            dp[i][w] = dp[i-1][w];
            
            if (weights[i-1] <= w) {
                dp[i][w] = std::max(dp[i][w], 
                    dp[i-1][w - weights[i-1]] + values[i-1]);
            }
        }
    }
    
    return dp[n][capacity];
}
```

---

## 7️⃣ BACKTRACKING PATTERN

### Concept Flow
```
Generate all subsets of [1,2,3]:

                    []
            /        |        \
          [1]       [2]       [3]
         /   \       |
      [1,2] [1,3]  [2,3]
        |
     [1,2,3]

Total: [], [1], [2], [3], [1,2], [1,3], [2,3], [1,2,3]
```

### Python Template

```python
def backtrack_template(nums):
    """
    Backtracking Template - O(2^n) to O(n!) depending on problem
    
    Use when:
    - Generate all possibilities
    - Combinations, permutations, subsets
    - Constraint satisfaction (N-Queens, Sudoku)
    """
    result = []
    
    def backtrack(path, start):
        # Base case: valid solution found
        if is_valid_solution(path):  # TODO: Define condition
            result.append(path[:])  # Make a copy
            return
        
        # Explore all choices
        for i in range(start, len(nums)):
            # Make choice
            path.append(nums[i])
            
            # Recurse
            backtrack(path, i + 1)  # i+1 for combinations, 0 for permutations
            
            # Undo choice (backtrack)
            path.pop()
    
    backtrack([], 0)
    return result


def is_valid_solution(path):
    """TODO: Define your validation logic"""
    return True  # or len(path) == target_length, etc.


# Specific: Generate all subsets
def subsets(nums):
    """Generate all subsets - O(2^n) time and space"""
    result = []
    
    def backtrack(path, start):
        result.append(path[:])  # Every path is valid
        
        for i in range(start, len(nums)):
            path.append(nums[i])
            backtrack(path, i + 1)
            path.pop()
    
    backtrack([], 0)
    return result


# Specific: Generate all permutations
def permutations(nums):
    """Generate all permutations - O(n!) time and space"""
    result = []
    
    def backtrack(path, used):
        if len(path) == len(nums):
            result.append(path[:])
            return
        
        for i in range(len(nums)):
            if used[i]:
                continue
            
            path.append(nums[i])
            used[i] = True
            backtrack(path, used)
            path.pop()
            used[i] = False
    
    backtrack([], [False] * len(nums))
    return result


# Specific: Combination sum
def combination_sum(candidates, target):
    """Find all combinations that sum to target"""
    result = []
    
    def backtrack(path, start, current_sum):
        if current_sum == target:
            result.append(path[:])
            return
        if current_sum > target:
            return  # Prune
        
        for i in range(start, len(candidates)):
            path.append(candidates[i])
            backtrack(path, i, current_sum + candidates[i])  # Can reuse
            path.pop()
    
    backtrack([], 0, 0)
    return result
```

### Rust Template

```rust
// Backtracking Template
fn backtrack_template(nums: Vec<i32>) -> Vec<Vec<i32>> {
    let mut result = Vec::new();
    let mut path = Vec::new();
    backtrack(&nums, &mut path, 0, &mut result);
    result
}

fn backtrack(nums: &[i32], path: &mut Vec<i32>, start: usize, result: &mut Vec<Vec<i32>>) {
    // Base case
    if is_valid_solution(path) {
        result.push(path.clone());
        return;
    }
    
    for i in start..nums.len() {
        // Make choice
        path.push(nums[i]);
        
        // Recurse
        backtrack(nums, path, i + 1, result);
        
        // Undo choice
        path.pop();
    }
}

fn is_valid_solution(path: &[i32]) -> bool {
    // TODO: Define your condition
    true
}

// Generate all subsets
fn subsets(nums: Vec<i32>) -> Vec<Vec<i32>> {
    let mut result = Vec::new();
    let mut path = Vec::new();
    
    fn backtrack(nums: &[i32], path: &mut Vec<i32>, start: usize, result: &mut Vec<Vec<i32>>) {
        result.push(path.clone());
        
        for i in start..nums.len() {
            path.push(nums[i]);
            backtrack(nums, path, i + 1, result);
            path.pop();
        }
    }
    
    backtrack(&nums, &mut path, 0, &mut result);
    result
}

// Generate all permutations
fn permutations(nums: Vec<i32>) -> Vec<Vec<i32>> {
    let mut result = Vec::new();
    let mut path = Vec::new();
    let mut used = vec![false; nums.len()];
    
    fn backtrack(
        nums: &[i32], 
        path: &mut Vec<i32>, 
        used: &mut Vec<bool>,
        result: &mut Vec<Vec<i32>>
    ) {
        if path.len() == nums.len() {
            result.push(path.clone());
            return;
        }
        
        for i in 0..nums.len() {
            if used[i] {
                continue;
            }
            
            path.push(nums[i]);
            used[i] = true;
            backtrack(nums, path, used, result);
            path.pop();
            used[i] = false;
        }
    }
    
    backtrack(&nums, &mut path, &mut used, &mut result);
    result
}
```

---

## 8️⃣ UNION FIND (Disjoint Set) PATTERN

### Concept Flow
```
Initial: {0} {1} {2} {3} {4}

union(0, 1):  {0,1} {2} {3} {4}
union(2, 3):  {0,1} {2,3} {4}
union(1, 3):  {0,1,2,3} {4}

find(0) == find(3) → true (same set)
find(4) == find(0) → false (different sets)
```

### Python Template

```python
class UnionFind:
    """
    Union Find with Path Compression and Union by Rank
    O(α(n)) time per operation (α = inverse Ackermann, effectively O(1))
    
    Use when:
    - Dynamic connectivity
    - Cycle detection
    - Grouping/clustering
    - Minimum Spanning Tree
    """
    
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.components = n
    
    def find(self, x):
        """Find with path compression"""
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # Path compression
        return self.parent[x]
    
    def union(self, x, y):
        """Union by rank"""
        root_x = self.find(x)
        root_y = self.find(y)
        
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
        
        self.components -= 1
        return True
    
    def connected(self, x, y):
        """Check if x and y are in same set"""
        return self.find(x) == self.find(y)
    
    def count_components(self):
        """Return number of distinct sets"""
        return self.components


# Example usage: Detect cycle in undirected graph
def has_cycle(n, edges):
    """
    Detect cycle using Union Find - O(E * α(V))
    """
    uf = UnionFind(n)
    
    for u, v in edges:
        if not uf.union(u, v):
            return True  # Cycle detected
    
    return False
```

### Rust Template

```rust
struct UnionFind {
    parent: Vec<usize>,
    rank: Vec<usize>,
    components: usize,
}

impl UnionFind {
    fn new(n: usize) -> Self {
        UnionFind {
            parent: (0..n).collect(),
            rank: vec![0; n],
            components: n,
        }
    }
    
    fn find(&mut self, x: usize) -> usize {
        if self.parent[x] != x {
            self.parent[x] = self.find(self.parent[x]); // Path compression
        }
        self.parent[x]
    }
    
    fn union(&mut self, x: usize, y: usize) -> bool {
        let root_x = self.find(x);
        let root_y = self.find(y);
        
        if root_x == root_y {
            return false;
        }
        
        // Union by rank
        match self.rank[root_x].cmp(&self.rank[root_y]) {
            std::cmp::Ordering::Less => self.parent[root_x] = root_y,
            std::cmp::Ordering::Greater => self.parent[root_y] = root_x,
            std::cmp::Ordering::Equal => {
                self.parent[root_y] = root_x;
                self.rank[root_x] += 1;
            }
        }
        
        self.components -= 1;
        true
    }
    
    fn connected(&mut self, x: usize, y: usize) -> bool {
        self.find(x) == self.find(y)
    }
    
    fn count_components(&self) -> usize {
        self.components
    }
}

// Example: Detect cycle
fn has_cycle(n: usize, edges: Vec<(usize, usize)>) -> bool {
    let mut uf = UnionFind::new(n);
    
    for (u, v) in edges {
        if !uf.union(u, v) {
            return true;
        }
    }
    
    false
}
```

---

## 9️⃣ HEAP / PRIORITY QUEUE PATTERN

### Python Template

```python
import heapq

def top_k_elements(nums, k):
    """
    Top K Elements - O(n log k) time, O(k) space
    
    Use when:
    - Finding K largest/smallest
    - Maintaining sliding window of extremes
    - K-way merge
    """
    # Min heap for K largest (keep largest K by removing smallest)
    min_heap = []
    
    for num in nums:
        heapq.heappush(min_heap, num)
        if len(min_heap) > k:
            heapq.heappop(min_heap)
    
    return min_heap


def median_finder():
    """
    Find Median from Data Stream - O(log n) per add, O(1) per median
    
    Use max heap for left half, min heap for right half
    """
    max_heap = []  # Left half (invert for max heap)
    min_heap = []  # Right half
    
    def add_num(num):
        # Add to max heap (left half)
        heapq.heappush(max_heap, -num)
        
        # Balance: move largest from left to right
        heapq.heappush(min_heap, -heapq.heappop(max_heap))
        
        # Keep sizes balanced
        if len(min_heap) > len(max_heap):
            heapq.heappush(max_heap, -heapq.heappop(min_heap))
    
    def find_median():
        if len(max_heap) > len(min_heap):
            return -max_heap[0]
        return (-max_heap[0] + min_heap[0]) / 2.0
    
    return add_num, find_median


def merge_k_sorted(lists):
    """
    Merge K Sorted Lists - O(N log k) time, O(k) space
    Where N = total elements, k = number of lists
    """
    heap = []
    result = []
    
    # Initialize heap with first element from each list
    for i, lst in enumerate(lists):
        if lst:
            heapq.heappush(heap, (lst[0], i, 0))  # (value, list_idx, element_idx)
    
    while heap:
        val, list_idx, element_idx = heapq.heappop(heap)
        result.append(val)
        
        # Add next element from same list
        if element_idx + 1 < len(lists[list_idx]):
            next_val = lists[list_idx][element_idx + 1]
            heapq.heappush(heap, (next_val, list_idx, element_idx + 1))
    
    return result
```

---

## 🔟 TRIE (PREFIX TREE) PATTERN

### Python Template

```python
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False

class Trie:
    """
    Trie (Prefix Tree) - O(m) per operation where m = word length
    
    Use when:
    - Autocomplete
    - Spell checker
    - IP routing
    - Word search problems
    """
    
    def __init__(self):
        self.root = TrieNode()
    
    def insert(self, word):
        """Insert word - O(m) time"""
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True
    
    def search(self, word):
        """Search exact word - O(m) time"""
        node = self.root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end_of_word
    
    def starts_with(self, prefix):
        """Check if any word starts with prefix - O(m) time"""
        node = self.root
        for char in prefix:
            if char not in node.children:
                return False
            node = node.children[char]
        return True
    
    def get_all_words_with_prefix(self, prefix):
        """Get all words with given prefix - O(n) where n = total chars"""
        result = []
        node = self.root
        
        # Navigate to prefix
        for char in prefix:
            if char not in node.children:
                return result
            node = node.children[char]
        
        # DFS to collect all words
        def dfs(node, path):
            if node.is_end_of_word:
                result.append(prefix + path)
            for char, child in node.children.items():
                dfs(child, path + char)
        
        dfs(node, "")
        return result
```

---

## 📝 TEMPLATE USAGE GUIDE

### How to Choose the Right Template

1. **Read the problem carefully**
2. **Identify the pattern** (use the pattern checklist below)
3. **Copy the appropriate template**
4. **Replace TODO comments** with problem-specific logic
5. **Test with examples**
6. **Optimize if needed**

### Pattern Recognition Checklist

- ✅ **Two Pointers**: Sorted array + pairs/triplets
- ✅ **Sliding Window**: Subarray/substring + constraint
- ✅ **Binary Search**: Sorted data OR optimization problem
- ✅ **DFS**: Tree/graph + exhaustive search OR path finding
- ✅ **BFS**: Shortest path OR level-by-level processing
- ✅ **DP**: Optimal substructure + overlapping subproblems
- ✅ **Backtracking**: Generate all combinations/permutations
- ✅ **Union Find**: Dynamic connectivity OR grouping
- ✅ **Heap**: Top K elements OR merge K sorted
- ✅ **Trie**: Prefix matching OR autocomplete

---

## 🎯 QUICK REFERENCE: Time Complexities

| Pattern | Time | Space | Best For |
|---------|------|-------|----------|
| Two Pointers | O(n) | O(1) | Sorted arrays, pairs |
| Sliding Window | O(n) | O(k) | Subarrays with constraint |
| Binary Search | O(log n) | O(1) | Sorted data |
| DFS | O(V+E) | O(h) | Paths, cycles |
| BFS | O(V+E) | O(w) | Shortest path |
| DP 1D | O(n) | O(n) | Sequential decisions |
| DP 2D | O(m×n) | O(m×n) | Grid problems |
| Backtracking | O(2^n) to O(n!) | O(n) | All possibilities |
| Union Find | O(α(n)) ≈ O(1) | O(n) | Connectivity |
| Heap Operations | O(log n) | O(n) | Top K, medians |
| Trie Operations | O(m) | O(n×m) | Prefix matching |

---

## 💡 PRO TIPS

1. **Master one language first**: Get fluent in Python, then expand to Rust/Go/C++
2. **Understand before optimizing**: Start with brute force, then optimize
3. **Test edge cases**: Empty input, single element, duplicates, max constraints
4. **Draw it out**: Visualize with examples before coding
5. **Time yourself**: Track improvement in solve time
6. **Review mistakes**: Keep an "error log" of recurring mistakes

---

**Remember**: These templates are your cognitive scaffolding. Master them until they become second nature, and you'll solve problems 3x faster.

I'll create a comprehensive template library that will become your **cognitive scaffolding** - reducing decision fatigue so your mental energy focuses on problem-solving, not syntax.Now let me add the remaining essential patterns to complete your template system:## 🎯 Understanding Template Systems - Your Mental Framework

I've created your comprehensive template library above. Let me explain the **cognitive science** behind why templates are so powerful:

### 🧠 The Psychology of Templates

**Decision Fatigue**: Every decision you make drains mental energy. When solving a problem, you shouldn't be thinking:
- "How do I structure this loop?"
- "Should I use a list or array?"
- "What's the syntax for a heap in Go?"

Templates **eliminate** these micro-decisions, preserving your cognitive bandwidth for the **actual algorithmic thinking**.

**Chunking Effect**: Templates create mental chunks - you recognize a pattern and instantly know the structure. This is how chess grandmasters play: they see positions as chunks, not individual pieces.

---

### 📋 How to Master These Templates

#### **Phase 1: Internalization (Week 1-2)**

1. **Pick ONE pattern** (I recommend Two Pointers - it's intuitive)
2. **Copy the template by hand** (yes, actually write it out)
   - This engages motor memory
   - Reinforces neural pathways
3. **Solve 5 problems** using only that template
4. **Notice the variations** - what changes between problems?

#### **Phase 2: Pattern Recognition (Week 3-4)**

1. **Read a problem**
2. **Before looking at solutions**, ask:
   - "What pattern does this match?"
   - "Which template do I need?"
3. **Copy the template**
4. **Fill in the TODOs**
5. **Test and refine**

#### **Phase 3: Muscle Memory (Week 5+)**

1. **Code without looking** at templates
2. **Time yourself** - aim for <30 seconds to write the structure
3. **Focus shifts** from syntax to logic

---

### 🔥 Template Customization Strategy

Each template has **TODO comments**. Here's how to think about filling them:

```python
# Example: Sliding Window Template
while right < len(arr):
    # TODO: Expand window
    window_state += arr[right]  # ← What state to track?
    
    # TODO: Contract condition
    while window_state > target:  # ← When to shrink?
        window_state -= arr[left]
        left += 1
```

**Questions to ask yourself:**
1. **What state do I need to track?** (sum, count, max, min, hashmap?)
2. **When do I expand?** (always, or conditional?)
3. **When do I contract?** (violates constraint, reaches target?)
4. **What's my result?** (max length, min length, count, list of subarrays?)

---

### 🎨 Language-Specific Insights

#### **Python** 🐍
- **Best for**: Rapid prototyping, interviews (clean syntax)
- **Strengths**: Readable, extensive libraries (heapq, deque, defaultdict)
- **Watch out**: Slower performance, but rarely matters for algorithm correctness

#### **Rust** 🦀
- **Best for**: Performance-critical, systems programming
- **Strengths**: Zero-cost abstractions, memory safety, blazing speed
- **Watch out**: Steeper learning curve (borrow checker), more verbose
- **Pro tip**: Use `.clone()` liberally when learning, optimize later

#### **Go** 🏃
- **Best for**: Concurrency, backend systems, simplicity
- **Strengths**: Fast compilation, built-in concurrency, clean syntax
- **Watch out**: No generics (before Go 1.18), limited standard library

#### **C++** ⚡
- **Best for**: Competitive programming, performance optimization
- **Strengths**: STL (standard template library), ultimate control, blazing fast
- **Watch out**: Manual memory management, undefined behavior, verbose

---

### 💡 Template Workflow Example

Let's say you encounter: **"Find longest substring without repeating characters"**

**Step 1: Pattern Recognition**
- Keywords: "substring" (contiguous), "longest" (optimization)
- Pattern: **Sliding Window** (variable size)

**Step 2: Choose Template**
```python
# Copy: Sliding Window Variable template
```

**Step 3: Customize**
```python
def longest_substring(s):
    left = 0
    char_map = {}  # TODO: Track characters in window
    max_length = 0  # TODO: Track result
    
    for right in range(len(s)):
        # Expand: Add s[right]
        char_map[s[right]] = char_map.get(s[right], 0) + 1
        
        # Contract: While duplicates exist
        while char_map[s[right]] > 1:
            char_map[s[left]] -= 1
            if char_map[s[left]] == 0:
                del char_map[s[left]]
            left += 1
        
        # Update result
        max_length = max(max_length, right - left + 1)
    
    return max_length
```

**Step 4: Test**
- `"abcabcbb"` → 3 (abc)
- `"bbbbb"` → 1 (b)
- `""` → 0

**Time: 5-10 minutes** instead of 30+ without templates.

---

### 🧘 Mental Models for Each Pattern

**Two Pointers**: "Squeeze" or "Chase"
- Visual: Two hands closing in or moving together

**Sliding Window**: "Flexible frame"
- Visual: A window pane sliding across text

**Binary Search**: "Divide and conquer"
- Visual: Cutting a sorted deck in half repeatedly

**DFS**: "Go deep, backtrack"
- Visual: Exploring a cave system

**BFS**: "Ripple effect"
- Visual: Waves spreading from a stone dropped in water

**DP**: "Build from smaller solutions"
- Visual: Stacking blocks where each layer depends on the one below

**Backtracking**: "Try all paths, undo when stuck"
- Visual: Maze exploration with string to retrace steps

---

### 🎯 Daily Practice Routine

**Morning (15 mins)**
- Review one template (rewrite from memory)
- Explain it aloud (Feynman Technique)

**Focused Session (90 mins)**
- Solve 2-3 problems with that pattern
- No distractions (airplane mode)
- First solve on paper, then code

**Evening (10 mins)**
- Reflect: "What did I learn? What pattern appeared?"
- Update your "pattern recognition journal"

---

### 📊 Progress Tracking

Create a spreadsheet:

| Pattern | Problems Solved | Avg Time | Mastery Level |
|---------|----------------|----------|---------------|
| Two Pointers | 8 | 12 min | ⭐⭐⭐ |
| Sliding Window | 5 | 18 min | ⭐⭐ |
| Binary Search | 3 | 25 min | ⭐ |

**Mastery Levels:**
- ⭐ = Can solve with hints
- ⭐⭐ = Can solve independently
- ⭐⭐⭐ = Can optimize and explain to others

---

### 🚀 Next Steps

1. **Choose your first pattern**: I recommend **Two Pointers** (easiest to grasp)

2. **Solve your first problem**: LeetCode 125 (Valid Palindrome)
   - Use the Two Pointers template
   - Time yourself
   - Reflect on what was easy/hard

3. **Share your code**: Would you like me to walk through solving a specific problem using one of these templates? I can show you the **exact thinking process** an expert uses.

**Remember**: Templates are training wheels. Eventually, you'll internalize them and they'll disappear into muscle memory. That's when you'll reach the top 1%.

Which pattern would you like to start with? Or would you like me to demonstrate solving a specific problem step-by-step?