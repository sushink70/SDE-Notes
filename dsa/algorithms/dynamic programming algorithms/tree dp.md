# Comprehensive Guide to Tree DP

## Introduction

**Tree Dynamic Programming** is a technique for solving optimization problems on tree structures. Unlike linear DP, tree DP leverages the hierarchical nature of trees, where each node can be processed based on its children's states.

### When to Use Tree DP

- Finding maximum/minimum values on tree paths
- Counting specific tree structures or subtrees
- Vertex cover, independent set problems on trees
- Tree coloring and partitioning problems
- Subtree queries and modifications

### Core Pattern

Tree DP typically follows this structure:

```
1. Root the tree (if unrooted)
2. Define dp[node][state] = optimal value for subtree rooted at node with given state
3. Use DFS/post-order traversal to compute from leaves to root
4. Combine children's results to compute parent's result
```

---

## Problem 1: Tree Diameter

**Problem**: Find the longest path between any two nodes in a tree.

### Theory

- For each node, track two values:
  - Maximum depth going down from this node
  - Maximum diameter passing through this node
- Diameter through node = max_depth1 + max_depth2 (two deepest branches)

### Python Implementation

```python
class TreeNode:
    def __init__(self, val=0):
        self.val = val
        self.children = []

def tree_diameter(root):
    """
    Args:
        root: Root of the tree
    Returns:
        Diameter of the tree
    """
    max_diameter = [0]
    
    def dfs(node):
        """Returns maximum depth from this node"""
        if not node:
            return 0
        
        # Get depths from all children
        depths = []
        for child in node.children:
            depths.append(dfs(child))
        
        if not depths:
            return 0
        
        # Sort to get two largest depths
        depths.sort(reverse=True)
        
        # Diameter through this node
        if len(depths) >= 2:
            diameter = depths[0] + depths[1]
        else:
            diameter = depths[0]
        
        max_diameter[0] = max(max_diameter[0], diameter)
        
        # Return max depth going down
        return depths[0] + 1
    
    dfs(root)
    return max_diameter[0]

# Example usage with adjacency list
def tree_diameter_from_edges(n, edges):
    """
    Args:
        n: Number of nodes (0 to n-1)
        edges: List of [u, v] edges
    Returns:
        Diameter of the tree
    """
    from collections import defaultdict
    
    graph = defaultdict(list)
    for u, v in edges:
        graph[u].append(v)
        graph[v].append(u)
    
    max_diameter = [0]
    
    def dfs(node, parent):
        """Returns max depth from this node"""
        depths = []
        
        for neighbor in graph[node]:
            if neighbor != parent:
                depths.append(dfs(neighbor, node))
        
        if not depths:
            return 0
        
        depths.sort(reverse=True)
        
        # Diameter through this node
        if len(depths) >= 2:
            diameter = depths[0] + depths[1]
        else:
            diameter = depths[0]
        
        max_diameter[0] = max(max_diameter[0], diameter)
        
        return depths[0] + 1
    
    dfs(0, -1)
    return max_diameter[0]

# Test
edges = [[0, 1], [0, 2], [1, 3], [1, 4], [2, 5]]
print(f"Tree diameter: {tree_diameter_from_edges(6, edges)}")
# Output: 4 (path: 3-1-0-2-5)
```

### Rust Implementation

```rust
use std::collections::HashMap;

fn tree_diameter(n: usize, edges: Vec<(usize, usize)>) -> i32 {
    let mut graph: HashMap<usize, Vec<usize>> = HashMap::new();
    
    for (u, v) in edges {
        graph.entry(u).or_insert(Vec::new()).push(v);
        graph.entry(v).or_insert(Vec::new()).push(u);
    }
    
    let mut max_diameter = 0;
    
    fn dfs(
        node: usize,
        parent: i32,
        graph: &HashMap<usize, Vec<usize>>,
        max_diameter: &mut i32,
    ) -> i32 {
        let mut depths = Vec::new();
        
        if let Some(neighbors) = graph.get(&node) {
            for &neighbor in neighbors {
                if neighbor != parent as usize {
                    depths.push(dfs(neighbor, node as i32, graph, max_diameter));
                }
            }
        }
        
        if depths.is_empty() {
            return 0;
        }
        
        depths.sort_by(|a, b| b.cmp(a));
        
        let diameter = if depths.len() >= 2 {
            depths[0] + depths[1]
        } else {
            depths[0]
        };
        
        *max_diameter = (*max_diameter).max(diameter);
        
        depths[0] + 1
    }
    
    dfs(0, -1, &graph, &mut max_diameter);
    max_diameter
}

fn main() {
    let edges = vec![(0, 1), (0, 2), (1, 3), (1, 4), (2, 5)];
    println!("Tree diameter: {}", tree_diameter(6, edges));
}
```

### Go Implementation

```go
package main

import (
    "fmt"
    "sort"
)

func treeDiameter(n int, edges [][2]int) int {
    graph := make(map[int][]int)
    
    for _, edge := range edges {
        u, v := edge[0], edge[1]
        graph[u] = append(graph[u], v)
        graph[v] = append(graph[v], u)
    }
    
    maxDiameter := 0
    
    var dfs func(node, parent int) int
    dfs = func(node, parent int) int {
        depths := []int{}
        
        for _, neighbor := range graph[node] {
            if neighbor != parent {
                depths = append(depths, dfs(neighbor, node))
            }
        }
        
        if len(depths) == 0 {
            return 0
        }
        
        sort.Sort(sort.Reverse(sort.IntSlice(depths)))
        
        diameter := depths[0]
        if len(depths) >= 2 {
            diameter = depths[0] + depths[1]
        }
        
        if diameter > maxDiameter {
            maxDiameter = diameter
        }
        
        return depths[0] + 1
    }
    
    dfs(0, -1)
    return maxDiameter
}

func main() {
    edges := [][2]int{{0, 1}, {0, 2}, {1, 3}, {1, 4}, {2, 5}}
    fmt.Printf("Tree diameter: %d\n", treeDiameter(6, edges))
}
```

---

## Problem 2: House Robber III (Binary Tree)

**Problem**: Rob houses arranged in a binary tree. Cannot rob two directly-linked nodes. Maximize money.

### Theory

- `dp[node][0]` = max money if node is NOT robbed
- `dp[node][1]` = max money if node IS robbed
- If node is robbed: can't rob children → `dp[node][1] = node.val + dp[left][0] + dp[right][0]`
- If node not robbed: take max from each child → `dp[node][0] = max(dp[left]) + max(dp[right])`

### Python Implementation

```python
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def rob(root):
    """
    Args:
        root: Root of binary tree where each node has a value
    Returns:
        Maximum amount that can be robbed
    """
    def dfs(node):
        """
        Returns (not_robbed, robbed) tuple
        not_robbed: max money if this node is not robbed
        robbed: max money if this node is robbed
        """
        if not node:
            return (0, 0)
        
        left = dfs(node.left)
        right = dfs(node.right)
        
        # If we rob this node, we can't rob children
        robbed = node.val + left[0] + right[0]
        
        # If we don't rob this node, take max from each child
        not_robbed = max(left) + max(right)
        
        return (not_robbed, robbed)
    
    result = dfs(root)
    return max(result)

# Example usage
def build_tree():
    """
    Tree structure:
          3
         / \
        2   3
         \   \
          3   1
    """
    root = TreeNode(3)
    root.left = TreeNode(2)
    root.right = TreeNode(3)
    root.left.right = TreeNode(3)
    root.right.right = TreeNode(1)
    return root

root = build_tree()
print(f"Maximum money: {rob(root)}")
# Output: 7 (rob 3 + 3 + 1)
```

### Rust Implementation

```rust
use std::rc::Rc;
use std::cell::RefCell;

#[derive(Debug, PartialEq, Eq)]
pub struct TreeNode {
    pub val: i32,
    pub left: Option<Rc<RefCell<TreeNode>>>,
    pub right: Option<Rc<RefCell<TreeNode>>>,
}

impl TreeNode {
    fn new(val: i32) -> Self {
        TreeNode {
            val,
            left: None,
            right: None,
        }
    }
}

fn rob(root: Option<Rc<RefCell<TreeNode>>>) -> i32 {
    fn dfs(node: &Option<Rc<RefCell<TreeNode>>>) -> (i32, i32) {
        match node {
            None => (0, 0),
            Some(n) => {
                let n = n.borrow();
                let left = dfs(&n.left);
                let right = dfs(&n.right);
                
                // Robbed: take this node + not robbing children
                let robbed = n.val + left.0 + right.0;
                
                // Not robbed: take max from each child
                let not_robbed = left.0.max(left.1) + right.0.max(right.1);
                
                (not_robbed, robbed)
            }
        }
    }
    
    let result = dfs(&root);
    result.0.max(result.1)
}

fn main() {
    let root = Rc::new(RefCell::new(TreeNode::new(3)));
    root.borrow_mut().left = Some(Rc::new(RefCell::new(TreeNode::new(2))));
    root.borrow_mut().right = Some(Rc::new(RefCell::new(TreeNode::new(3))));
    
    if let Some(left) = &root.borrow().left {
        left.borrow_mut().right = Some(Rc::new(RefCell::new(TreeNode::new(3))));
    }
    if let Some(right) = &root.borrow().right {
        right.borrow_mut().right = Some(Rc::new(RefCell::new(TreeNode::new(1))));
    }
    
    println!("Maximum money: {}", rob(Some(root)));
}
```

### Go Implementation

```go
package main

import "fmt"

type TreeNode struct {
    Val   int
    Left  *TreeNode
    Right *TreeNode
}

func rob(root *TreeNode) int {
    notRobbed, robbed := dfs(root)
    return max(notRobbed, robbed)
}

func dfs(node *TreeNode) (int, int) {
    if node == nil {
        return 0, 0
    }
    
    leftNotRobbed, leftRobbed := dfs(node.Left)
    rightNotRobbed, rightRobbed := dfs(node.Right)
    
    // If we rob this node
    robbed := node.Val + leftNotRobbed + rightNotRobbed
    
    // If we don't rob this node
    notRobbed := max(leftNotRobbed, leftRobbed) + 
                 max(rightNotRobbed, rightRobbed)
    
    return notRobbed, robbed
}

func max(a, b int) int {
    if a > b {
        return a
    }
    return b
}

func main() {
    root := &TreeNode{Val: 3}
    root.Left = &TreeNode{Val: 2}
    root.Right = &TreeNode{Val: 3}
    root.Left.Right = &TreeNode{Val: 3}
    root.Right.Right = &TreeNode{Val: 1}
    
    fmt.Printf("Maximum money: %d\n", rob(root))
}
```

---

## Problem 3: Binary Tree Maximum Path Sum

**Problem**: Find the maximum path sum where a path can start and end at any node.

### Theory

- For each node, compute:
  - `max_single`: max path sum going through node to ONE child (for parent to use)
  - `max_through`: max path sum going through node to BOTH children (candidate for answer)
- Answer is the maximum `max_through` across all nodes

### Python Implementation

```python
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def max_path_sum(root):
    """
    Args:
        root: Root of binary tree
    Returns:
        Maximum path sum in the tree
    """
    max_sum = [float('-inf')]
    
    def dfs(node):
        """
        Returns: max path sum from this node going down to descendants
        Updates: max_sum with path that might go through this node
        """
        if not node:
            return 0
        
        # Get max sums from children (ignore negative paths)
        left_max = max(0, dfs(node.left))
        right_max = max(0, dfs(node.right))
        
        # Max path sum through this node (to both children)
        path_through_node = node.val + left_max + right_max
        max_sum[0] = max(max_sum[0], path_through_node)
        
        # Return max path going through node to ONE child
        # (for parent to potentially use)
        return node.val + max(left_max, right_max)
    
    dfs(root)
    return max_sum[0]

# Example usage
def build_tree():
    """
    Tree:
        -10
        /  \
       9   20
          /  \
         15   7
    """
    root = TreeNode(-10)
    root.left = TreeNode(9)
    root.right = TreeNode(20)
    root.right.left = TreeNode(15)
    root.right.right = TreeNode(7)
    return root

root = build_tree()
print(f"Maximum path sum: {max_path_sum(root)}")
# Output: 42 (path: 15 -> 20 -> 7)
```

### Rust Implementation

```rust
use std::rc::Rc;
use std::cell::RefCell;

#[derive(Debug)]
pub struct TreeNode {
    pub val: i32,
    pub left: Option<Rc<RefCell<TreeNode>>>,
    pub right: Option<Rc<RefCell<TreeNode>>>,
}

impl TreeNode {
    fn new(val: i32) -> Self {
        TreeNode { val, left: None, right: None }
    }
}

fn max_path_sum(root: Option<Rc<RefCell<TreeNode>>>) -> i32 {
    let mut max_sum = i32::MIN;
    
    fn dfs(
        node: &Option<Rc<RefCell<TreeNode>>>,
        max_sum: &mut i32,
    ) -> i32 {
        match node {
            None => 0,
            Some(n) => {
                let n = n.borrow();
                
                let left_max = dfs(&n.left, max_sum).max(0);
                let right_max = dfs(&n.right, max_sum).max(0);
                
                // Path through this node
                let path_through = n.val + left_max + right_max;
                *max_sum = (*max_sum).max(path_through);
                
                // Return path to one child
                n.val + left_max.max(right_max)
            }
        }
    }
    
    dfs(&root, &mut max_sum);
    max_sum
}

fn main() {
    let root = Rc::new(RefCell::new(TreeNode::new(-10)));
    root.borrow_mut().left = Some(Rc::new(RefCell::new(TreeNode::new(9))));
    
    let right = Rc::new(RefCell::new(TreeNode::new(20)));
    right.borrow_mut().left = Some(Rc::new(RefCell::new(TreeNode::new(15))));
    right.borrow_mut().right = Some(Rc::new(RefCell::new(TreeNode::new(7))));
    root.borrow_mut().right = Some(right);
    
    println!("Maximum path sum: {}", max_path_sum(Some(root)));
}
```

### Go Implementation

```go
package main

import (
    "fmt"
    "math"
)

type TreeNode struct {
    Val   int
    Left  *TreeNode
    Right *TreeNode
}

func maxPathSum(root *TreeNode) int {
    maxSum := math.MinInt32
    
    var dfs func(node *TreeNode) int
    dfs = func(node *TreeNode) int {
        if node == nil {
            return 0
        }
        
        leftMax := max(0, dfs(node.Left))
        rightMax := max(0, dfs(node.Right))
        
        // Path through this node
        pathThrough := node.Val + leftMax + rightMax
        if pathThrough > maxSum {
            maxSum = pathThrough
        }
        
        // Return path to one child
        return node.Val + max(leftMax, rightMax)
    }
    
    dfs(root)
    return maxSum
}

func max(a, b int) int {
    if a > b {
        return a
    }
    return b
}

func main() {
    root := &TreeNode{Val: -10}
    root.Left = &TreeNode{Val: 9}
    root.Right = &TreeNode{Val: 20}
    root.Right.Left = &TreeNode{Val: 15}
    root.Right.Right = &TreeNode{Val: 7}
    
    fmt.Printf("Maximum path sum: %d\n", maxPathSum(root))
}
```

---

## Problem 4: Tree Distance Sum

**Problem**: For each node, calculate sum of distances to all other nodes.

### Theory

- Two-pass algorithm:
  1. **First DFS**: Calculate subtree sizes and sum of distances within subtrees
  2. **Second DFS (Re-rooting)**: Calculate answer for each node by re-rooting
- When moving root from parent to child:
  - Nodes in child's subtree get 1 closer
  - Nodes outside get 1 farther

### Python Implementation

```python
def sum_of_distances_in_tree(n, edges):
    """
    Args:
        n: Number of nodes (0 to n-1)
        edges: List of edges [u, v]
    Returns:
        List where answer[i] = sum of distances from node i to all other nodes
    """
    from collections import defaultdict
    
    graph = defaultdict(list)
    for u, v in edges:
        graph[u].append(v)
        graph[v].append(u)
    
    # First pass: calculate subtree sizes and initial distances
    count = [1] * n  # count[i] = size of subtree rooted at i
    answer = [0] * n  # answer[i] = sum of distances in subtree
    
    def dfs1(node, parent):
        for child in graph[node]:
            if child != parent:
                dfs1(child, node)
                count[node] += count[child]
                answer[node] += answer[child] + count[child]
    
    # Second pass: re-root to calculate answer for all nodes
    def dfs2(node, parent):
        for child in graph[node]:
            if child != parent:
                # When moving from node to child:
                # - count[child] nodes get 1 closer
                # - (n - count[child]) nodes get 1 farther
                answer[child] = answer[node] - count[child] + (n - count[child])
                dfs2(child, node)
    
    dfs1(0, -1)
    dfs2(0, -1)
    
    return answer

# Example usage
n = 6
edges = [[0, 1], [0, 2], [2, 3], [2, 4], [2, 5]]
result = sum_of_distances_in_tree(n, edges)
print(f"Distance sums: {result}")
# Output: [8, 12, 6, 10, 10, 10]
```

### Rust Implementation

```rust
use std::collections::HashMap;

fn sum_of_distances_in_tree(n: usize, edges: Vec<(usize, usize)>) -> Vec<i32> {
    let mut graph: HashMap<usize, Vec<usize>> = HashMap::new();
    
    for (u, v) in edges {
        graph.entry(u).or_insert(Vec::new()).push(v);
        graph.entry(v).or_insert(Vec::new()).push(u);
    }
    
    let mut count = vec![1; n];
    let mut answer = vec![0; n];
    
    fn dfs1(
        node: usize,
        parent: i32,
        graph: &HashMap<usize, Vec<usize>>,
        count: &mut Vec<i32>,
        answer: &mut Vec<i32>,
    ) {
        if let Some(neighbors) = graph.get(&node) {
            for &child in neighbors {
                if child != parent as usize {
                    dfs1(child, node as i32, graph, count, answer);
                    count[node] += count[child];
                    answer[node] += answer[child] + count[child];
                }
            }
        }
    }
    
    fn dfs2(
        node: usize,
        parent: i32,
        n: i32,
        graph: &HashMap<usize, Vec<usize>>,
        count: &Vec<i32>,
        answer: &mut Vec<i32>,
    ) {
        if let Some(neighbors) = graph.get(&node) {
            for &child in neighbors {
                if child != parent as usize {
                    answer[child] = answer[node] - count[child] + (n - count[child]);
                    dfs2(child, node as i32, n, graph, count, answer);
                }
            }
        }
    }
    
    dfs1(0, -1, &graph, &mut count, &mut answer);
    dfs2(0, -1, n as i32, &graph, &count, &mut answer);
    
    answer
}

fn main() {
    let edges = vec![(0, 1), (0, 2), (2, 3), (2, 4), (2, 5)];
    let result = sum_of_distances_in_tree(6, edges);
    println!("Distance sums: {:?}", result);
}
```

### Go Implementation

```go
package main

import "fmt"

func sumOfDistancesInTree(n int, edges [][2]int) []int {
    graph := make(map[int][]int)
    
    for _, edge := range edges {
        u, v := edge[0], edge[1]
        graph[u] = append(graph[u], v)
        graph[v] = append(graph[v], u)
    }
    
    count := make([]int, n)
    answer := make([]int, n)
    
    for i := range count {
        count[i] = 1
    }
    
    var dfs1 func(node, parent int)
    dfs1 = func(node, parent int) {
        for _, child := range graph[node] {
            if child != parent {
                dfs1(child, node)
                count[node] += count[child]
                answer[node] += answer[child] + count[child]
            }
        }
    }
    
    var dfs2 func(node, parent int)
    dfs2 = func(node, parent int) {
        for _, child := range graph[node] {
            if child != parent {
                answer[child] = answer[node] - count[child] + (n - count[child])
                dfs2(child, node)
            }
        }
    }
    
    dfs1(0, -1)
    dfs2(0, -1)
    
    return answer
}

func main() {
    edges := [][2]int{{0, 1}, {0, 2}, {2, 3}, {2, 4}, {2, 5}}
    result := sumOfDistancesInTree(6, edges)
    fmt.Printf("Distance sums: %v\n", result)
}
```

---

## Problem 5: Minimum Cameras to Monitor Binary Tree

**Problem**: Place minimum cameras on nodes to monitor all nodes. A camera can monitor itself, parent, and children.

### Theory

- Three states for each node:
  - `0`: Not monitored (needs coverage from parent)
  - `1`: Monitored but no camera
  - `2`: Has a camera
- Post-order DFS: process children first
- Logic:
  - If any child is 0 (not monitored): place camera here
  - If any child has camera (2): this node is monitored (1)
  - Otherwise: not monitored (0), parent must handle

### Python Implementation

```python
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def min_camera_cover(root):
    """
    Args:
        root: Root of binary tree
    Returns:
        Minimum number of cameras needed
    """
    cameras = [0]
    
    # States: 0 = not monitored, 1 = monitored no camera, 2 = has camera
    def dfs(node):
        if not node:
            return 1  # Null nodes are considered monitored
        
        left = dfs(node.left)
        right = dfs(node.right)
        
        # If either child is not monitored, place camera here
        if left == 0 or right == 0:
            cameras[0] += 1
            return 2
        
        # If either child has camera, this node is monitored
        if left == 2 or right == 2:
            return 1
        
        # Both children are monitored but have no camera
        # This node is not monitored
        return 0
    
    # If root is not monitored, add camera at root
    if dfs(root) == 0:
        cameras[0] += 1
    
    return cameras[0]

# Example usage
def build_tree():
    """
    Tree:
          0
         / \
        0   0
         \
          0
           \
            0
    """
    root = TreeNode(0)
    root.left = TreeNode(0)
    root.right = TreeNode(0)
    root.left.right = TreeNode(0)
    root.left.right.right = TreeNode(0)
    return root

root = build_tree()
print(f"Minimum cameras: {min_camera_cover(root)}")
# Output: 2
```

### Rust Implementation

```rust
use std::rc::Rc;
use std::cell::RefCell;

#[derive(Debug)]
pub struct TreeNode {
    pub val: i32,
    pub left: Option<Rc<RefCell<TreeNode>>>,
    pub right: Option<Rc<RefCell<TreeNode>>>,
}

impl TreeNode {
    fn new(val: i32) -> Self {
        TreeNode { val, left: None, right: None }
    }
}

fn min_camera_cover(root: Option<Rc<RefCell<TreeNode>>>) -> i32 {
    let mut cameras = 0;
    
    fn dfs(
        node: &Option<Rc<RefCell<TreeNode>>>,
        cameras: &mut i32,
    ) -> i32 {
        match node {
            None => 1, // Null is monitored
            Some(n) => {
                let n = n.borrow();
                let left = dfs(&n.left, cameras);
                let right = dfs(&n.right, cameras);
                
                // If any child not monitored, place camera
                if left == 0 || right == 0 {
                    *cameras += 1;
                    return 2;
                }
                
                // If any child has camera, monitored
                if left == 2 || right == 2 {
                    return 1;
                }
                
                // Not monitored
                0
            }
        }
    }
    
    if dfs(&root, &mut cameras) == 0 {
        cameras += 1;
    }
    
    cameras
}

fn main() {
    let root = Rc::new(RefCell::new(TreeNode::new(0)));
    root.borrow_mut().left = Some(Rc::new(RefCell::new(TreeNode::new(0))));
    root.borrow_mut().right = Some(Rc::new(RefCell::new(TreeNode::new(0))));
    
    let left = root.borrow().left.clone().unwrap();
    left.borrow_mut().right = Some(Rc::new(RefCell::new(TreeNode::new(0))));
    
    let left_right = left.borrow().right.clone().unwrap();
    left_right.borrow_mut().right = Some(Rc::new(RefCell::new(TreeNode::new(0))));
    
    println!("Minimum cameras: {}", min_camera_cover(Some(root)));
}
```

### Go Implementation

```go
package main

import "fmt"

type TreeNode struct {
    Val   int
    Left  *TreeNode
    Right *TreeNode
}

func minCameraCover(root *TreeNode) int {
    cameras := 0
    
    var dfs func(node *TreeNode) int
    dfs = func(node *TreeNode) int {
        if node == nil {
            return 1 // Null is monitored
        }
        
        left := dfs(node.Left)
        right := dfs(node.Right)
        
        // If any child not monitored, place camera
        if left == 0 || right == 0 {
            cameras++
            return 2
        }
        
        // If any child has camera, this is monitored
        if left == 2 || right == 2 {
            return 1
        }
        
        // Not monitored
        return 0
    }
    
    if dfs(root) == 0 {
        cameras++
    }
    
    return cameras
}

func main() {
    root := &TreeNode{Val: 0}
    root.Left = &TreeNode{Val: 0}
    root.Right = &TreeNode{Val: 0}
    root.Left.Right = &TreeNode{Val: 0}
    root.Left.Right.Right = &TreeNode{Val: 0}
    fmt.Printf("Minimum cameras: %d\n", minCameraCover(root))
}
# Output: 2
```

```go
func sameTree(p *TreeNode, q *TreeNode) bool {
    if p == nil && q == nil {
        return true
    }
    if p == nil || q == nil {
        return false
    }
    if p.Val != q.Val {
        return false
    }
    return sameTree(p.Left, q.Left) &&
           sameTree(p.Right, q.Right)
}
```

# Execution Order in `&&` — Left Side Always Executes First

## The Golden Rule: Left-to-Right with Short-Circuit Evaluation

In Go (and virtually every C-family language: C, C++, Rust, Python), the `&&` operator:

1. **Always evaluates the LEFT side first**
2. **Only evaluates the RIGHT side IF the left side returned `true`**
3. If left side is `false` → **right side is SKIPPED entirely** (short-circuit)

---

## ASCII Execution Flow

```
return sameTree(p.Left, q.Left) && sameTree(p.Right, q.Right)
         │                              │
         │                              │
         ▼                              │
   ┌─────────────┐                      │
   │ Execute     │                      │
   │ LEFT call   │                      │
   │ first       │                      │
   └──────┬──────┘                      │
          │                             │
          ▼                             │
   ┌──────────────┐                     │
   │ Result =     │                     │
   │ true or      │                     │
   │ false?       │                     │
   └──────┬───────┘                     │
          │                             │
    ┌─────┴──────┐                      │
    │            │                      │
    ▼            ▼                      │
  false        true ──────────────────►─┘
    │            │                      │
    │            │               ┌──────▼──────┐
    │            │               │ Execute     │
    │            │               │ RIGHT call  │
    │            │               └──────┬──────┘
    │            │                      │
    ▼            │               ┌──────▼──────┐
  return         │               │ Return its  │
  false          │               │ result      │
  IMMEDIATELY    │               └─────────────┘
  (right side    │
  NEVER runs)   (continues)
```

---

## Concrete Example — Watch the Call Order

```
        Tree p:          Tree q:
            1                1
           / \              / \
          2   3            2   4   ← different!
```

```
Call: sameTree(p=1, q=1)
│
├── p.Val == q.Val (1==1) ✓
│
├── STEP 1: sameTree(p.Left=2, q.Left=2)   ← LEFT executes FIRST
│       │
│       ├── p.Val == q.Val (2==2) ✓
│       ├── sameTree(nil, nil) → true
│       ├── sameTree(nil, nil) → true
│       └── returns TRUE
│
│   LEFT returned TRUE → proceed to RIGHT
│
└── STEP 2: sameTree(p.Right=3, q.Right=4) ← RIGHT executes NOW
        │
        ├── p.Val != q.Val (3 != 4) ✗
        └── returns FALSE

Final result: true && false = FALSE ✓
```

---

## Now The Short-Circuit Case — Right Side Never Runs

```
        Tree p:          Tree q:
            1                1
           / \              / \
          2   3            5   3   ← left subtrees differ
```

```
Call: sameTree(p=1, q=1)
│
├── p.Val == q.Val (1==1) ✓
│
├── STEP 1: sameTree(p.Left=2, q.Left=5)   ← LEFT executes FIRST
│       │
│       ├── p.Val != q.Val (2 != 5) ✗
│       └── returns FALSE  ◄── SHORT CIRCUIT TRIGGERED!
│
│   LEFT returned FALSE → && stops here
│   sameTree(p.Right, q.Right) is NEVER called
│
└── STEP 2: ██████ SKIPPED ██████  ← RIGHT never executes!

Final result: false  (immediately)
```

---

## Why This Matters for Recursive Trees

```
Short-circuit saves unnecessary work:

Without short-circuit:            With short-circuit (actual):
─────────────────────             ──────────────────────────
Check left subtree  ✓             Check left subtree  ✗
Check right subtree ✓  ← wasted  RIGHT SIDE SKIPPED  ← saved!
```

The deeper the tree, the more calls get pruned when a mismatch is found early in the left subtree.

---

## The Same Rule in All Your Languages

```
Go:     left && right   // left first, short-circuits
C:      left && right   // identical
C++:    left && right   // identical
Rust:   left && right   // identical
Python: left and right  // identical behavior
```

> **Mental Model:** Think of `&&` as a **security checkpoint**.
> Guard 1 (left) checks first. If Guard 1 says NO → the person never reaches Guard 2 (right). Guard 2 only does work when Guard 1 approves.

---

## Key Takeaway

| Question | Answer |
|---|---|
| Which executes first? | **Left side always** |
| Does right always run? | **No — only if left returns `true`** |
| What is this called? | **Short-circuit evaluation** |
| Is order guaranteed in Go? | **Yes, by the language spec** |

This is not just a Go thing — it's a **fundamental property of boolean logic evaluation** in all serious languages, and a critical detail when your conditions have **side effects** (like recursive calls, I/O, or mutations).

# Recursion + Short-Circuit in a Deep Tree — Unwrapped Completely

## First, Understand One Core Truth

```
Every single recursive call follows the SAME rule:
"Execute LEFT child first, RIGHT child only if LEFT returns true"

This rule repeats at EVERY level of the tree.
```

The complexity is not actually complicated — it's the **same simple rule applied repeatedly**. Let's build this understanding layer by layer.

---

## The Tree We'll Use

```
        Tree p:                    Tree q:
              1                          1
            /   \                      /   \
           2     3                    2     3
          / \   / \                  / \   / \
         4   5 6   7                4   5 6   9  ← different here!
```

---

## Mental Model — The "Chain of Promises"

```
Before any code runs, think of it as a CHAIN:

sameTree(1,1)
    PROMISES: "I will check left subtree first,
               then right subtree ONLY IF left passed"
        │
        ├── sameTree(2,2)
        │       PROMISES: "I will check left subtree first,
        │                   then right subtree ONLY IF left passed"
        │           │
        │           ├── sameTree(4,4)  → checks its children
        │           └── sameTree(5,5)  → checks its children
        │
        └── sameTree(3,3)  ← WAITS. Will only run after sameTree(2,2) finishes
                PROMISES: same rule
                    │
                    ├── sameTree(6,6)  → checks its children
                    └── sameTree(7,9)  ← MISMATCH! returns false
```

---

## Full Execution Order — Step by Step

```
LEVEL 0:  sameTree(1, 1)
          1==1 ✓ ... now go LEFT first

  LEVEL 1L:  sameTree(2, 2)        ← LEFT of root executes
             2==2 ✓ ... now go LEFT first

    LEVEL 2LL:  sameTree(4, 4)     ← LEFT of node-2 executes
                4==4 ✓
                sameTree(nil,nil) → true   (left child)
                sameTree(nil,nil) → true   (right child)
                RETURNS TRUE ✓
                ─────────────────────────────────────────────
                [LEFT passed → RIGHT is allowed to run]

    LEVEL 2LR:  sameTree(5, 5)     ← RIGHT of node-2 executes
                5==5 ✓
                sameTree(nil,nil) → true
                sameTree(nil,nil) → true
                RETURNS TRUE ✓
             ─────────────────────────────────────────────────
             sameTree(2,2) RETURNS TRUE
             [LEFT of root passed → RIGHT of root allowed to run]

  LEVEL 1R:  sameTree(3, 3)        ← RIGHT of root executes NOW
             3==3 ✓ ... now go LEFT first

    LEVEL 2RL:  sameTree(6, 6)     ← LEFT of node-3 executes
                6==6 ✓
                RETURNS TRUE ✓
                ─────────────────────────────────────────────
                [LEFT passed → RIGHT is allowed to run]

    LEVEL 2RR:  sameTree(7, 9)     ← RIGHT of node-3 executes
                7 != 9 ✗
                RETURNS FALSE ✗
             ─────────────────────────────────────────────────
             sameTree(3,3) RETURNS FALSE

LEVEL 0: true && false = FALSE ← Final answer
```

---

## The Call Stack Visualization

```
This is what lives in memory simultaneously:

  ┌────────────────────────────────┐  ← currently executing
  │  sameTree(7, 9)  → FALSE       │
  └────────────────────────────────┘
  ┌────────────────────────────────┐
  │  sameTree(3, 3)  → waiting...  │  ← waiting for right child result
  └────────────────────────────────┘
  ┌────────────────────────────────┐
  │  sameTree(1, 1)  → waiting...  │  ← waiting for right child result
  └────────────────────────────────┘

Stack unwinds UPWARD:
sameTree(7,9) returns FALSE
    → sameTree(3,3) receives FALSE from right child
    → sameTree(3,3) returns FALSE
        → sameTree(1,1) receives FALSE from right child
        → sameTree(1,1) returns FALSE
            → DONE
```

---

## Short-Circuit Scenario — Mismatch Found EARLY (Left Side)

```
Now imagine node-4 and node-4 are different (4 vs 99):

        p:           q:
          1            1
         / \          / \
        2   3        2   3
       / \          / \
      4   5       99   5   ← mismatch here
```

```
sameTree(1,1)
  └── LEFT: sameTree(2,2)
              └── LEFT: sameTree(4, 99)
                          4 != 99
                          RETURNS FALSE ✗
                          ↑
              sameTree(2,2):
                LEFT returned FALSE
                ██ sameTree(5,5) NEVER CALLED ██  ← short-circuit!
                RETURNS FALSE ✗
                ↑
sameTree(1,1):
  LEFT returned FALSE
  ██ sameTree(3,3) and ALL its subtree NEVER CALLED ██ ← entire subtree skipped!
  RETURNS FALSE ✗
```

```
Work saved by short-circuit:
─────────────────────────────
Called:    sameTree(1,1)
           sameTree(2,2)
           sameTree(4,99)    ← stops here

NEVER called:
           sameTree(5,5)     ← skipped
           sameTree(3,3)     ← skipped (entire right subtree!)
           sameTree(6,6)     ← skipped
           sameTree(7,7)     ← skipped

4 function calls saved!
```

---

## The Pattern At Every Level — Decision Tree

```
At ANY node during recursion:

            sameTree(p, q)
                  │
         ┌────────▼────────┐
         │ p==nil, q==nil? │
         └────────┬────────┘
              YES │  NO
                  │   └──► ┌──────────────────┐
                  │        │ one of them nil? │
            return│        └────────┬─────────┘
             true │            YES  │  NO
                  │                 │   └──► ┌─────────────┐
                  │           return│        │ p.Val==q.Val│
                  │           false │        └──────┬──────┘
                  │                 │          NO   │  YES
                  │                 │               │   └──► Execute LEFT child
                  │                 │  return       │        call first
                  │                 │  false        │            │
                  │                 │               │        LEFT returned?
                  │                 │               │        ┌───┴───┐
                  │                 │               │      false    true
                  │                 │               │        │       │
                  │                 │               │    return   Execute RIGHT
                  │                 │               │    false    child call
                  │                 │               │                │
                  │                 │               │            return its result
                  ▼                 ▼               ▼
```

---

## Why It Doesn't Get "Complicated"

```
Your brain sees the whole tree and gets overwhelmed.
The COMPUTER only ever sees ONE node at a time.

At any given moment, the computer is only answering:
"Are these two nodes equal, and are their subtrees equal?"

It doesn't know about the full tree.
It doesn't care about depth.
It just answers its tiny local question
and trusts the recursion to handle the rest.
```

```
This is called:

  RECURSIVE FAITH
  ───────────────
  "I don't need to understand the whole problem.
   I solve my tiny piece correctly,
   and assume the recursive calls do their piece correctly."

  This is the #1 mental model for recursive thinking.
```

---

## Time Complexity Implication

```
Best case (mismatch at root):    O(1)   — stops immediately
Best case (mismatch at level 2): O(1 + left_subtree_size)
Worst case (trees are identical): O(N)  — every node visited once

N = total number of nodes

Short-circuit makes average case
much better than worst case.
```

---

## The Summary

| What feels complicated | What's actually happening |
|---|---|
| Deep recursion | Same 3-line logic repeating |
| Big tree | Computer only sees 1 node at a time |
| Short-circuit in recursion | Each level independently decides to stop or continue |
| Call stack | Just "paused" parent calls waiting for children to finish |

> **Cognitive Principle — Chunking:**
> Your brain tries to simulate the whole tree at once — that's why it feels complex. Expert programmers **chunk** recursion into: *"trust the base case + trust the recursive call + write only the current step."* Train yourself to think locally, not globally, when reading recursive code.

That version is **not correct as written**, because the order of checks matters.

You wrote:

```go
if treeP == nil || treeQ == nil {
    return false
}

if treeP == nil && treeQ == nil {
    return true
}
```

### ❌ Problem

The first condition:

```go
treeP == nil || treeQ == nil
```

also covers the case where **both are nil**.

So when both are `nil`:

```go
treeP == nil && treeQ == nil
```

👉 the first `if` already triggers and returns `false`
👉 the second `if` is **never reached**

---

### 🔍 Truth Table

```

| treeP | treeQ | `||` condition | `&&` condition | Your result |
|------|------|---------------|---------------|------------|
| nil  | nil  | true          | true          | ❌ false (wrong) |
| nil  | val  | true          | false         | false |
| val  | nil  | true          | false         | false |
```

---

### ✅ Correct Order

You must check the **more specific condition first**:

```go
if treeP == nil && treeQ == nil {
    return true
}

if treeP == nil || treeQ == nil {
    return false
}
```

---

### 🧠 Why this works

* `&&` is **more specific** (both must be nil)
* `||` is **broader** (any one nil)

So:

```text
Specific case → General case
```

---

### ⚡ Rule of thumb

> Always check **strict / exact conditions first**, then broader ones.

---

### Final correct structure

```go
func sameTree(p *TreeNode, q *TreeNode) bool {
    if p == nil && q == nil {
        return true
    }
    if p == nil || q == nil {
        return false
    }
    if p.Val != q.Val {
        return false
    }
    return sameTree(p.Left, q.Left) &&
           sameTree(p.Right, q.Right)
}
```

---

If you want, I can show a **minimal failing test case** that proves your version breaks — it’s a good way to lock this concept in.
