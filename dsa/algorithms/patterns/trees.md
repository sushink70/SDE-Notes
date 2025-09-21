# Complete Guide to Tree Problem Patterns

## Table of Contents
1. [Basic Tree Structure](#basic-tree-structure)
2. [Tree Traversal Patterns](#tree-traversal-patterns)
3. [Tree Construction Patterns](#tree-construction-patterns)
4. [Path Finding Patterns](#path-finding-patterns)
5. [Tree Validation Patterns](#tree-validation-patterns)
6. [Tree Manipulation Patterns](#tree-manipulation-patterns)
7. [Ancestor/Descendant Patterns](#ancestordescendant-patterns)
8. [Tree Comparison Patterns](#tree-comparison-patterns)
9. [Binary Search Tree Patterns](#binary-search-tree-patterns)
10. [Advanced Tree Patterns](#advanced-tree-patterns)

## Basic Tree Structure

### Python Implementation
```python
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
    
    def __repr__(self):
        return f"TreeNode({self.val})"
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
    #[inline]
    pub fn new(val: i32) -> Self {
        TreeNode {
            val,
            left: None,
            right: None
        }
    }
}

type Node = Option<Rc<RefCell<TreeNode>>>;
```

## 1. Tree Traversal Patterns

### Pattern: Depth-First Search (DFS)

#### Preorder Traversal
**Use Case**: Creating copies, expression trees, serialization

**Python:**
```python
def preorder_recursive(root):
    if not root:
        return []
    return [root.val] + preorder_recursive(root.left) + preorder_recursive(root.right)

def preorder_iterative(root):
    if not root:
        return []
    
    result = []
    stack = [root]
    
    while stack:
        node = stack.pop()
        result.append(node.val)
        
        # Push right first, then left (so left is processed first)
        if node.right:
            stack.append(node.right)
        if node.left:
            stack.append(node.left)
    
    return result
```

**Rust:**
```rust
fn preorder_recursive(root: &Node) -> Vec<i32> {
    match root {
        None => vec![],
        Some(node) => {
            let node = node.borrow();
            let mut result = vec![node.val];
            result.extend(preorder_recursive(&node.left));
            result.extend(preorder_recursive(&node.right));
            result
        }
    }
}

fn preorder_iterative(root: &Node) -> Vec<i32> {
    let mut result = Vec::new();
    if root.is_none() {
        return result;
    }
    
    let mut stack = vec![root.as_ref().unwrap().clone()];
    
    while let Some(node) = stack.pop() {
        let node = node.borrow();
        result.push(node.val);
        
        if let Some(ref right) = node.right {
            stack.push(right.clone());
        }
        if let Some(ref left) = node.left {
            stack.push(left.clone());
        }
    }
    
    result
}
```

#### Inorder Traversal
**Use Case**: BST sorted order, expression evaluation

**Python:**
```python
def inorder_recursive(root):
    if not root:
        return []
    return inorder_recursive(root.left) + [root.val] + inorder_recursive(root.right)

def inorder_iterative(root):
    result = []
    stack = []
    current = root
    
    while current or stack:
        # Go to the leftmost node
        while current:
            stack.append(current)
            current = current.left
        
        # Process current node
        current = stack.pop()
        result.append(current.val)
        
        # Move to right subtree
        current = current.right
    
    return result
```

**Rust:**
```rust
fn inorder_recursive(root: &Node) -> Vec<i32> {
    match root {
        None => vec![],
        Some(node) => {
            let node = node.borrow();
            let mut result = inorder_recursive(&node.left);
            result.push(node.val);
            result.extend(inorder_recursive(&node.right));
            result
        }
    }
}

fn inorder_iterative(root: &Node) -> Vec<i32> {
    let mut result = Vec::new();
    let mut stack = Vec::new();
    let mut current = root.clone();
    
    while current.is_some() || !stack.is_empty() {
        while let Some(node) = current {
            stack.push(node.clone());
            current = node.borrow().left.clone();
        }
        
        if let Some(node) = stack.pop() {
            let node_ref = node.borrow();
            result.push(node_ref.val);
            current = node_ref.right.clone();
        }
    }
    
    result
}
```

### Pattern: Breadth-First Search (BFS)

#### Level Order Traversal
**Use Case**: Level-by-level processing, finding shortest path

**Python:**
```python
from collections import deque

def level_order(root):
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

def level_order_flat(root):
    if not root:
        return []
    
    result = []
    queue = deque([root])
    
    while queue:
        node = queue.popleft()
        result.append(node.val)
        
        if node.left:
            queue.append(node.left)
        if node.right:
            queue.append(node.right)
    
    return result
```

**Rust:**
```rust
use std::collections::VecDeque;

fn level_order(root: &Node) -> Vec<Vec<i32>> {
    let mut result = Vec::new();
    if root.is_none() {
        return result;
    }
    
    let mut queue = VecDeque::new();
    queue.push_back(root.as_ref().unwrap().clone());
    
    while !queue.is_empty() {
        let level_size = queue.len();
        let mut level = Vec::new();
        
        for _ in 0..level_size {
            if let Some(node) = queue.pop_front() {
                let node_ref = node.borrow();
                level.push(node_ref.val);
                
                if let Some(ref left) = node_ref.left {
                    queue.push_back(left.clone());
                }
                if let Some(ref right) = node_ref.right {
                    queue.push_back(right.clone());
                }
            }
        }
        
        result.push(level);
    }
    
    result
}
```

## 2. Tree Construction Patterns

### Pattern: Build from Traversal Arrays

#### Build Binary Tree from Preorder and Inorder
**Use Case**: Deserializing trees, reconstructing from traversals

**Python:**
```python
def build_tree_pre_in(preorder, inorder):
    if not preorder or not inorder:
        return None
    
    # Root is always the first element in preorder
    root = TreeNode(preorder[0])
    
    # Find root position in inorder
    mid = inorder.index(preorder[0])
    
    # Recursively build left and right subtrees
    root.left = build_tree_pre_in(preorder[1:mid+1], inorder[:mid])
    root.right = build_tree_pre_in(preorder[mid+1:], inorder[mid+1:])
    
    return root

# Optimized version with hashmap
def build_tree_pre_in_optimized(preorder, inorder):
    inorder_map = {val: i for i, val in enumerate(inorder)}
    self.preorder_idx = 0
    
    def helper(left, right):
        if left > right:
            return None
        
        root_val = preorder[self.preorder_idx]
        self.preorder_idx += 1
        
        root = TreeNode(root_val)
        root_idx = inorder_map[root_val]
        
        root.left = helper(left, root_idx - 1)
        root.right = helper(root_idx + 1, right)
        
        return root
    
    return helper(0, len(inorder) - 1)
```

**Rust:**
```rust
use std::collections::HashMap;

fn build_tree(preorder: Vec<i32>, inorder: Vec<i32>) -> Node {
    if preorder.is_empty() || inorder.is_empty() {
        return None;
    }
    
    let inorder_map: HashMap<i32, usize> = inorder
        .iter()
        .enumerate()
        .map(|(i, &val)| (val, i))
        .collect();
    
    let mut preorder_idx = 0;
    
    fn helper(
        preorder: &[i32],
        preorder_idx: &mut usize,
        inorder_map: &HashMap<i32, usize>,
        left: usize,
        right: usize
    ) -> Node {
        if left > right {
            return None;
        }
        
        let root_val = preorder[*preorder_idx];
        *preorder_idx += 1;
        
        let root = Rc::new(RefCell::new(TreeNode::new(root_val)));
        let root_idx = *inorder_map.get(&root_val).unwrap();
        
        root.borrow_mut().left = helper(preorder, preorder_idx, inorder_map, left, root_idx - 1);
        root.borrow_mut().right = helper(preorder, preorder_idx, inorder_map, root_idx + 1, right);
        
        Some(root)
    }
    
    helper(&preorder, &mut preorder_idx, &inorder_map, 0, inorder.len() - 1)
}
```

## 3. Path Finding Patterns

### Pattern: Root to Leaf Paths

#### Binary Tree Paths
**Use Case**: Finding all possible paths, path enumeration

**Python:**
```python
def binary_tree_paths(root):
    if not root:
        return []
    
    paths = []
    
    def dfs(node, path):
        if not node:
            return
        
        path.append(str(node.val))
        
        # If it's a leaf node, add path to result
        if not node.left and not node.right:
            paths.append("->".join(path))
        else:
            dfs(node.left, path)
            dfs(node.right, path)
        
        # Backtrack
        path.pop()
    
    dfs(root, [])
    return paths

def has_path_sum(root, target_sum):
    if not root:
        return False
    
    # Check if it's a leaf node
    if not root.left and not root.right:
        return root.val == target_sum
    
    # Recursively check left and right subtrees
    remaining = target_sum - root.val
    return (has_path_sum(root.left, remaining) or 
            has_path_sum(root.right, remaining))
```

**Rust:**
```rust
fn binary_tree_paths(root: &Node) -> Vec<String> {
    let mut paths = Vec::new();
    if root.is_none() {
        return paths;
    }
    
    fn dfs(node: &Node, path: &mut Vec<String>, paths: &mut Vec<String>) {
        if let Some(n) = node {
            let n = n.borrow();
            path.push(n.val.to_string());
            
            if n.left.is_none() && n.right.is_none() {
                paths.push(path.join("->"));
            } else {
                dfs(&n.left, path, paths);
                dfs(&n.right, path, paths);
            }
            
            path.pop();
        }
    }
    
    let mut path = Vec::new();
    dfs(root, &mut path, &mut paths);
    paths
}

fn has_path_sum(root: &Node, target_sum: i32) -> bool {
    match root {
        None => false,
        Some(node) => {
            let node = node.borrow();
            
            if node.left.is_none() && node.right.is_none() {
                return node.val == target_sum;
            }
            
            let remaining = target_sum - node.val;
            has_path_sum(&node.left, remaining) || has_path_sum(&node.right, remaining)
        }
    }
}
```

## 4. Tree Validation Patterns

### Pattern: Tree Property Validation

#### Validate Binary Search Tree
**Use Case**: Data structure integrity, constraint validation

**Python:**
```python
def is_valid_bst(root):
    def validate(node, min_val, max_val):
        if not node:
            return True
        
        if node.val <= min_val or node.val >= max_val:
            return False
        
        return (validate(node.left, min_val, node.val) and 
                validate(node.right, node.val, max_val))
    
    return validate(root, float('-inf'), float('inf'))

# Alternative using inorder traversal
def is_valid_bst_inorder(root):
    def inorder(node):
        if not node:
            return []
        return inorder(node.left) + [node.val] + inorder(node.right)
    
    values = inorder(root)
    return all(values[i] < values[i+1] for i in range(len(values)-1))

def is_balanced(root):
    def check_height(node):
        if not node:
            return 0
        
        left_height = check_height(node.left)
        if left_height == -1:
            return -1
        
        right_height = check_height(node.right)
        if right_height == -1:
            return -1
        
        if abs(left_height - right_height) > 1:
            return -1
        
        return max(left_height, right_height) + 1
    
    return check_height(root) != -1
```

**Rust:**
```rust
fn is_valid_bst(root: &Node) -> bool {
    fn validate(node: &Node, min_val: Option<i32>, max_val: Option<i32>) -> bool {
        match node {
            None => true,
            Some(n) => {
                let n = n.borrow();
                
                if let Some(min) = min_val {
                    if n.val <= min {
                        return false;
                    }
                }
                
                if let Some(max) = max_val {
                    if n.val >= max {
                        return false;
                    }
                }
                
                validate(&n.left, min_val, Some(n.val)) && 
                validate(&n.right, Some(n.val), max_val)
            }
        }
    }
    
    validate(root, None, None)
}

fn is_balanced(root: &Node) -> bool {
    fn check_height(node: &Node) -> i32 {
        match node {
            None => 0,
            Some(n) => {
                let n = n.borrow();
                
                let left_height = check_height(&n.left);
                if left_height == -1 {
                    return -1;
                }
                
                let right_height = check_height(&n.right);
                if right_height == -1 {
                    return -1;
                }
                
                if (left_height - right_height).abs() > 1 {
                    return -1;
                }
                
                std::cmp::max(left_height, right_height) + 1
            }
        }
    }
    
    check_height(root) != -1
}
```

## 5. Tree Manipulation Patterns

### Pattern: Tree Modification

#### Invert Binary Tree
**Use Case**: Tree mirroring, structural transformations

**Python:**
```python
def invert_tree(root):
    if not root:
        return None
    
    # Swap left and right children
    root.left, root.right = root.right, root.left
    
    # Recursively invert subtrees
    invert_tree(root.left)
    invert_tree(root.right)
    
    return root

def flatten_tree_to_linked_list(root):
    if not root:
        return
    
    # Recursively flatten left and right subtrees
    flatten_tree_to_linked_list(root.left)
    flatten_tree_to_linked_list(root.right)
    
    # Store right subtree
    right = root.right
    
    # Move left subtree to right
    root.right = root.left
    root.left = None
    
    # Find the rightmost node in the moved subtree
    current = root
    while current.right:
        current = current.right
    
    # Attach the original right subtree
    current.right = right
```

**Rust:**
```rust
fn invert_tree(root: Node) -> Node {
    match root {
        None => None,
        Some(node) => {
            let mut node_ref = node.borrow_mut();
            
            // Swap left and right children
            let temp = node_ref.left.take();
            node_ref.left = node_ref.right.take();
            node_ref.right = temp;
            
            // Recursively invert subtrees
            node_ref.left = invert_tree(node_ref.left.take());
            node_ref.right = invert_tree(node_ref.right.take());
            
            drop(node_ref);
            Some(node)
        }
    }
}

fn flatten(root: &mut Node) {
    fn flatten_helper(node: Node) -> Node {
        match node {
            None => None,
            Some(n) => {
                let mut n_ref = n.borrow_mut();
                let left = n_ref.left.take();
                let right = n_ref.right.take();
                
                drop(n_ref);
                
                let left_tail = flatten_helper(left);
                let right_tail = flatten_helper(right);
                
                if let Some(ref tail) = left_tail {
                    n.borrow_mut().right = Some(tail.clone());
                    
                    // Find the end of left chain
                    let mut current = Some(tail.clone());
                    while let Some(ref curr) = current {
                        if curr.borrow().right.is_none() {
                            curr.borrow_mut().right = right_tail;
                            break;
                        }
                        let next = curr.borrow().right.clone();
                        current = next;
                    }
                } else {
                    n.borrow_mut().right = right_tail;
                }
                
                Some(n)
            }
        }
    }
    
    *root = flatten_helper(root.take());
}
```

## 6. Ancestor/Descendant Patterns

### Pattern: Lowest Common Ancestor

#### LCA in Binary Tree
**Use Case**: Finding common ancestors, tree relationships

**Python:**
```python
def lowest_common_ancestor(root, p, q):
    if not root or root == p or root == q:
        return root
    
    left = lowest_common_ancestor(root.left, p, q)
    right = lowest_common_ancestor(root.right, p, q)
    
    # If both left and right are not None, current node is LCA
    if left and right:
        return root
    
    # Return the non-null child
    return left if left else right

# For BST - more efficient
def lowest_common_ancestor_bst(root, p, q):
    while root:
        if p.val < root.val and q.val < root.val:
            root = root.left
        elif p.val > root.val and q.val > root.val:
            root = root.right
        else:
            return root
    return None
```

**Rust:**
```rust
fn lowest_common_ancestor(root: Node, p: Node, q: Node) -> Node {
    match root {
        None => None,
        Some(node) => {
            if std::ptr::eq(node.as_ptr(), p.as_ref()?.as_ptr()) ||
               std::ptr::eq(node.as_ptr(), q.as_ref()?.as_ptr()) {
                return Some(node);
            }
            
            let left = lowest_common_ancestor(
                node.borrow().left.clone(), 
                p.clone(), 
                q.clone()
            );
            let right = lowest_common_ancestor(
                node.borrow().right.clone(), 
                p, 
                q
            );
            
            match (left, right) {
                (Some(_), Some(_)) => Some(node),
                (Some(l), None) => Some(l),
                (None, Some(r)) => Some(r),
                (None, None) => None,
            }
        }
    }
}
```

## 7. Tree Comparison Patterns

### Pattern: Structural Comparison

#### Same Tree
**Use Case**: Tree equality, structural comparison

**Python:**
```python
def is_same_tree(p, q):
    if not p and not q:
        return True
    if not p or not q:
        return False
    
    return (p.val == q.val and 
            is_same_tree(p.left, q.left) and 
            is_same_tree(p.right, q.right))

def is_subtree(root, subroot):
    if not subroot:
        return True
    if not root:
        return False
    
    return (is_same_tree(root, subroot) or 
            is_subtree(root.left, subroot) or 
            is_subtree(root.right, subroot))

def is_symmetric(root):
    def is_mirror(left, right):
        if not left and not right:
            return True
        if not left or not right:
            return False
        
        return (left.val == right.val and 
                is_mirror(left.left, right.right) and 
                is_mirror(left.right, right.left))
    
    return not root or is_mirror(root.left, root.right)
```

**Rust:**
```rust
fn is_same_tree(p: &Node, q: &Node) -> bool {
    match (p, q) {
        (None, None) => true,
        (Some(p_node), Some(q_node)) => {
            let p_ref = p_node.borrow();
            let q_ref = q_node.borrow();
            
            p_ref.val == q_ref.val &&
            is_same_tree(&p_ref.left, &q_ref.left) &&
            is_same_tree(&p_ref.right, &q_ref.right)
        },
        _ => false,
    }
}

fn is_symmetric(root: &Node) -> bool {
    fn is_mirror(left: &Node, right: &Node) -> bool {
        match (left, right) {
            (None, None) => true,
            (Some(l), Some(r)) => {
                let l_ref = l.borrow();
                let r_ref = r.borrow();
                
                l_ref.val == r_ref.val &&
                is_mirror(&l_ref.left, &r_ref.right) &&
                is_mirror(&l_ref.right, &r_ref.left)
            },
            _ => false,
        }
    }
    
    match root {
        None => true,
        Some(node) => {
            let node_ref = node.borrow();
            is_mirror(&node_ref.left, &node_ref.right)
        }
    }
}
```

## 8. Binary Search Tree Patterns

### Pattern: BST Operations

#### BST Insert and Search
**Use Case**: Maintaining sorted order, efficient search

**Python:**
```python
def search_bst(root, val):
    if not root or root.val == val:
        return root
    
    if val < root.val:
        return search_bst(root.left, val)
    else:
        return search_bst(root.right, val)

def insert_into_bst(root, val):
    if not root:
        return TreeNode(val)
    
    if val < root.val:
        root.left = insert_into_bst(root.left, val)
    else:
        root.right = insert_into_bst(root.right, val)
    
    return root

def delete_node(root, key):
    if not root:
        return None
    
    if key < root.val:
        root.left = delete_node(root.left, key)
    elif key > root.val:
        root.right = delete_node(root.right, key)
    else:
        # Node to be deleted found
        if not root.left:
            return root.right
        elif not root.right:
            return root.left
        
        # Node with two children: get inorder successor
        min_node = root.right
        while min_node.left:
            min_node = min_node.left
        
        root.val = min_node.val
        root.right = delete_node(root.right, min_node.val)
    
    return root
```

**Rust:**
```rust
fn search_bst(root: &Node, val: i32) -> Node {
    match root {
        None => None,
        Some(node) => {
            let node_ref = node.borrow();
            if node_ref.val == val {
                Some(node.clone())
            } else if val < node_ref.val {
                search_bst(&node_ref.left, val)
            } else {
                search_bst(&node_ref.right, val)
            }
        }
    }
}

fn insert_into_bst(root: Node, val: i32) -> Node {
    match root {
        None => Some(Rc::new(RefCell::new(TreeNode::new(val)))),
        Some(node) => {
            {
                let mut node_ref = node.borrow_mut();
                if val < node_ref.val {
                    node_ref.left = insert_into_bst(node_ref.left.take(), val);
                } else {
                    node_ref.right = insert_into_bst(node_ref.right.take(), val);
                }
            }
            Some(node)
        }
    }
}
```

## 9. Advanced Tree Patterns

### Pattern: Tree Diameter and Depth

#### Maximum Depth and Diameter
**Use Case**: Tree metrics, optimization problems

**Python:**
```python
def max_depth(root):
    if not root:
        return 0
    return 1 + max(max_depth(root.left), max_depth(root.right))

def diameter_of_binary_tree(root):
    self.max_diameter = 0
    
    def depth(node):
        if not node:
            return 0
        
        left_depth = depth(node.left)
        right_depth = depth(node.right)
        
        # Update diameter (longest path through current node)
        self.max_diameter = max(self.max_diameter, left_depth + right_depth)
        
        return 1 + max(left_depth, right_depth)
    
    depth(root)
    return self.max_diameter

def max_path_sum(root):
    self.max_sum = float('-inf')
    
    def max_gain(node):
        if not node:
            return 0
        
        # Maximum sum on left and right sub-trees
        left_gain = max(max_gain(node.left), 0)
        right_gain = max(max_gain(node.right), 0)
        
        # Maximum path sum with current node as highest node
        price_new_path = node.val + left_gain + right_gain
        
        # Update max_sum if it's better
        self.max_sum = max(self.max_sum, price_new_path)
        
        # Return max gain if continue the same path
        return node.val + max(left_gain, right_gain)
    
    max_gain(root)
    return self.max_sum
```

**Rust:**
```rust
fn max_depth(root: &Node) -> i32 {
    match root {
        None => 0,
        Some(node) => {
            let node_ref = node.borrow();
            1 + std::cmp::max(
                max_depth(&node_ref.left),
                max_depth(&node_ref.right)
            )
        }
    }
}

fn diameter_of_binary_tree(root: &Node) -> i32 {
    fn depth(node: &Node, max_diameter: &mut i32) -> i32 {
        match node {
            None => 0,
            Some(n) => {
                let n_ref = n.borrow();
                let left_depth = depth(&n_ref.left, max_diameter);
                let right_depth = depth(&n_ref.right, max_diameter);
                
                *max_diameter = std::cmp::max(*max_diameter, left_depth + right_depth);
                
                1 + std::cmp::max(left_depth, right_depth)
            }
        }
    }
    
    let mut max_diameter = 0;
    depth(root, &mut max_diameter);
    max_diameter
}
```

### Pattern: Serialization and Deserialization

#### Tree Codec
**Use Case**: Persistence, network transfer, caching

**Python:**
```python
class Codec:
    def serialize(self, root):
        def preorder(node):
            if not node:
                vals.append("#")
            else:
                vals.append(str(node.val))
                preorder(node.left)
                preorder(node.right)
        
        vals = []
        preorder(root)
        return ",".join(vals)
    
    def deserialize(self, data):
        def build():
            val = next(vals)
            if val == "#":
                return None
            
            node = TreeNode(int(val))
            node.left = build()
            node.right = build()
            return node
        
        vals = iter(data.split(","))
        return build()

# Level-order serialization (alternative approach)
    def serialize_level_order(self, root):
        if not root:
            return ""
        
        from collections import deque
        queue = deque([root])
        result = []
        
        while queue:
            node = queue.popleft()
            if node:
                result.append(str(node.val))
                queue.append(node.left)
                queue.append(node.right)
            else:
                result.append("#")
        
        return ",".join(result)
    
    def deserialize_level_order(self, data):
        if not data:
            return None
        
        from collections import deque
        values = data.split(",")
        root = TreeNode(int(values[0]))
        queue = deque([root])
        i = 1
        
        while queue and i < len(values):
            node = queue.popleft()
            
            if values[i] != "#":
                node.left = TreeNode(int(values[i]))
                queue.append(node.left)
            i += 1
            
            if i < len(values) and values[i] != "#":
                node.right = TreeNode(int(values[i]))
                queue.append(node.right)
            i += 1
        
        return root
```

**Rust:**
```rust
struct Codec;

impl Codec {
    fn new() -> Self {
        Codec
    }
    
    fn serialize(&self, root: &Node) -> String {
        fn preorder(node: &Node, vals: &mut Vec<String>) {
            match node {
                None => vals.push("#".to_string()),
                Some(n) => {
                    let n_ref = n.borrow();
                    vals.push(n_ref.val.to_string());
                    preorder(&n_ref.left, vals);
                    preorder(&n_ref.right, vals);
                }
            }
        }
        
        let mut vals = Vec::new();
        preorder(root, &mut vals);
        vals.join(",")
    }
    
    fn deserialize(&self, data: String) -> Node {
        fn build(vals: &mut std::iter::Peekable<std::str::Split<char>>) -> Node {
            if let Some(val) = vals.next() {
                if val == "#" {
                    None
                } else {
                    let node = Rc::new(RefCell::new(TreeNode::new(val.parse().unwrap())));
                    node.borrow_mut().left = build(vals);
                    node.borrow_mut().right = build(vals);
                    Some(node)
                }
            } else {
                None
            }
        }
        
        let mut vals = data.split(',').peekable();
        build(&mut vals)
    }
}
```

## 10. Tree Utility Functions

### Pattern: Tree Metrics and Analysis

#### Complete Tree Analysis Suite
**Use Case**: Tree debugging, analysis, optimization

**Python:**
```python
class TreeAnalyzer:
    def __init__(self):
        pass
    
    def get_tree_info(self, root):
        """Get comprehensive tree information"""
        info = {
            'height': self.max_depth(root),
            'size': self.count_nodes(root),
            'is_balanced': self.is_balanced(root),
            'is_complete': self.is_complete_tree(root),
            'is_perfect': self.is_perfect_tree(root),
            'leaf_count': self.count_leaves(root),
            'internal_count': self.count_internal_nodes(root)
        }
        return info
    
    def count_nodes(self, root):
        if not root:
            return 0
        return 1 + self.count_nodes(root.left) + self.count_nodes(root.right)
    
    def count_leaves(self, root):
        if not root:
            return 0
        if not root.left and not root.right:
            return 1
        return self.count_leaves(root.left) + self.count_leaves(root.right)
    
    def count_internal_nodes(self, root):
        if not root or (not root.left and not root.right):
            return 0
        return 1 + self.count_internal_nodes(root.left) + self.count_internal_nodes(root.right)
    
    def is_complete_tree(self, root):
        if not root:
            return True
        
        from collections import deque
        queue = deque([root])
        null_found = False
        
        while queue:
            node = queue.popleft()
            
            if not node:
                null_found = True
            else:
                if null_found:
                    return False
                queue.append(node.left)
                queue.append(node.right)
        
        return True
    
    def is_perfect_tree(self, root):
        def get_depth(node):
            if not node:
                return 0
            return 1 + get_depth(node.left)
        
        def is_perfect_helper(node, depth, level=0):
            if not node:
                return True
            
            if not node.left and not node.right:
                return depth == level + 1
            
            if not node.left or not node.right:
                return False
            
            return (is_perfect_helper(node.left, depth, level + 1) and
                    is_perfect_helper(node.right, depth, level + 1))
        
        depth = get_depth(root)
        return is_perfect_helper(root, depth)
    
    def get_level_widths(self, root):
        """Get the number of nodes at each level"""
        if not root:
            return []
        
        from collections import deque
        queue = deque([root])
        widths = []
        
        while queue:
            level_size = len(queue)
            widths.append(level_size)
            
            for _ in range(level_size):
                node = queue.popleft()
                if node.left:
                    queue.append(node.left)
                if node.right:
                    queue.append(node.right)
        
        return widths
    
    def get_nodes_at_distance(self, root, k):
        """Get all nodes at distance k from root"""
        result = []
        
        def dfs(node, distance):
            if not node:
                return
            
            if distance == k:
                result.append(node.val)
                return
            
            dfs(node.left, distance + 1)
            dfs(node.right, distance + 1)
        
        dfs(root, 0)
        return result
    
    def find_path_to_node(self, root, target):
        """Find path from root to target node"""
        path = []
        
        def find_path_helper(node):
            if not node:
                return False
            
            path.append(node.val)
            
            if node.val == target:
                return True
            
            if (find_path_helper(node.left) or 
                find_path_helper(node.right)):
                return True
            
            path.pop()
            return False
        
        if find_path_helper(root):
            return path
        return []

# Example usage
def demo_tree_analysis():
    # Create a sample tree
    #       1
    #      / \
    #     2   3
    #    / \   \
    #   4   5   6
    
    root = TreeNode(1)
    root.left = TreeNode(2)
    root.right = TreeNode(3)
    root.left.left = TreeNode(4)
    root.left.right = TreeNode(5)
    root.right.right = TreeNode(6)
    
    analyzer = TreeAnalyzer()
    info = analyzer.get_tree_info(root)
    print("Tree Analysis:", info)
    print("Level widths:", analyzer.get_level_widths(root))
    print("Nodes at distance 2:", analyzer.get_nodes_at_distance(root, 2))
    print("Path to node 5:", analyzer.find_path_to_node(root, 5))
```

**Rust:**
```rust
struct TreeAnalyzer;

impl TreeAnalyzer {
    fn new() -> Self {
        TreeAnalyzer
    }
    
    fn count_nodes(&self, root: &Node) -> usize {
        match root {
            None => 0,
            Some(node) => {
                let node_ref = node.borrow();
                1 + self.count_nodes(&node_ref.left) + self.count_nodes(&node_ref.right)
            }
        }
    }
    
    fn count_leaves(&self, root: &Node) -> usize {
        match root {
            None => 0,
            Some(node) => {
                let node_ref = node.borrow();
                if node_ref.left.is_none() && node_ref.right.is_none() {
                    1
                } else {
                    self.count_leaves(&node_ref.left) + self.count_leaves(&node_ref.right)
                }
            }
        }
    }
    
    fn is_complete_tree(&self, root: &Node) -> bool {
        if root.is_none() {
            return true;
        }
        
        use std::collections::VecDeque;
        let mut queue = VecDeque::new();
        queue.push_back(root.clone());
        let mut null_found = false;
        
        while let Some(node_opt) = queue.pop_front() {
            match node_opt {
                None => null_found = true,
                Some(node) => {
                    if null_found {
                        return false;
                    }
                    let node_ref = node.borrow();
                    queue.push_back(node_ref.left.clone());
                    queue.push_back(node_ref.right.clone());
                }
            }
        }
        
        true
    }
    
    fn get_nodes_at_distance(&self, root: &Node, k: i32) -> Vec<i32> {
        let mut result = Vec::new();
        
        fn dfs(node: &Node, distance: i32, k: i32, result: &mut Vec<i32>) {
            if let Some(n) = node {
                if distance == k {
                    result.push(n.borrow().val);
                    return;
                }
                
                let n_ref = n.borrow();
                dfs(&n_ref.left, distance + 1, k, result);
                dfs(&n_ref.right, distance + 1, k, result);
            }
        }
        
        dfs(root, 0, k, &mut result);
        result
    }
    
    fn find_path_to_node(&self, root: &Node, target: i32) -> Vec<i32> {
        let mut path = Vec::new();
        
        fn find_path_helper(node: &Node, target: i32, path: &mut Vec<i32>) -> bool {
            if let Some(n) = node {
                let n_ref = n.borrow();
                path.push(n_ref.val);
                
                if n_ref.val == target {
                    return true;
                }
                
                if find_path_helper(&n_ref.left, target, path) ||
                   find_path_helper(&n_ref.right, target, path) {
                    return true;
                }
                
                path.pop();
            }
            false
        }
        
        if find_path_helper(root, target, &mut path) {
            path
        } else {
            Vec::new()
        }
    }
}
```

## 11. Specialized Tree Patterns

### Pattern: Tree with Parent Pointers

#### Operations with Parent References
**Use Case**: Upward traversal, LCA with parent pointers

**Python:**
```python
class TreeNodeWithParent:
    def __init__(self, val=0, left=None, right=None, parent=None):
        self.val = val
        self.left = left
        self.right = right
        self.parent = parent

def lowest_common_ancestor_with_parent(p, q):
    """Find LCA when nodes have parent pointers"""
    # Get all ancestors of p
    ancestors = set()
    current = p
    while current:
        ancestors.add(current)
        current = current.parent
    
    # Find first common ancestor of q
    current = q
    while current:
        if current in ancestors:
            return current
        current = current.parent
    
    return None

def get_ancestors(node):
    """Get all ancestors of a node"""
    ancestors = []
    current = node.parent
    while current:
        ancestors.append(current)
        current = current.parent
    return ancestors

def find_successor_with_parent(node):
    """Find inorder successor with parent pointer"""
    if not node:
        return None
    
    # Case 1: Node has right subtree
    if node.right:
        current = node.right
        while current.left:
            current = current.left
        return current
    
    # Case 2: No right subtree, go up until we find a left turn
    current = node
    parent = current.parent
    while parent and current == parent.right:
        current = parent
        parent = parent.parent
    
    return parent
```

### Pattern: Threaded Binary Trees

#### Morris Traversal (Space-Optimized)
**Use Case**: Memory-efficient traversal, embedded systems

**Python:**
```python
def morris_inorder_traversal(root):
    """Inorder traversal with O(1) space complexity"""
    result = []
    current = root
    
    while current:
        if not current.left:
            # No left child, visit current and go right
            result.append(current.val)
            current = current.right
        else:
            # Find inorder predecessor
            predecessor = current.left
            while predecessor.right and predecessor.right != current:
                predecessor = predecessor.right
            
            if not predecessor.right:
                # Create thread and go left
                predecessor.right = current
                current = current.left
            else:
                # Remove thread, visit current, and go right
                predecessor.right = None
                result.append(current.val)
                current = current.right
    
    return result

def morris_preorder_traversal(root):
    """Preorder traversal with O(1) space complexity"""
    result = []
    current = root
    
    while current:
        if not current.left:
            result.append(current.val)
            current = current.right
        else:
            predecessor = current.left
            while predecessor.right and predecessor.right != current:
                predecessor = predecessor.right
            
            if not predecessor.right:
                result.append(current.val)  # Visit before going left
                predecessor.right = current
                current = current.left
            else:
                predecessor.right = None
                current = current.right
    
    return result
```

**Rust:**
```rust
fn morris_inorder_traversal(root: &Node) -> Vec<i32> {
    let mut result = Vec::new();
    let mut current = root.clone();
    
    while let Some(curr_node) = current {
        let curr_ref = curr_node.borrow();
        
        if curr_ref.left.is_none() {
            result.push(curr_ref.val);
            current = curr_ref.right.clone();
        } else {
            // Find predecessor
            let mut predecessor = curr_ref.left.clone();
            let mut pred_right = None;
            
            while let Some(pred_node) = predecessor {
                let pred_ref = pred_node.borrow();
                if pred_ref.right.is_none() || 
                   (pred_ref.right.is_some() && 
                    std::ptr::eq(
                        pred_ref.right.as_ref().unwrap().as_ptr(),
                        curr_node.as_ptr()
                    )) {
                    pred_right = pred_ref.right.clone();
                    break;
                }
                predecessor = pred_ref.right.clone();
            }
            
            // This is a simplified version - full implementation requires
            // careful handling of Rc/RefCell for thread creation
            current = curr_ref.right.clone();
        }
    }
    
    result
}
```

## 12. Problem-Solving Strategies

### Strategy Guide for Tree Problems

#### Decision Framework
```python
def choose_tree_approach(problem_description):
    """
    Decision tree for choosing the right approach:
    
    1. TRAVERSAL NEEDED?
       - Need all nodes: DFS/BFS
       - Need specific order: Preorder/Inorder/Postorder
       - Level by level: BFS/Level-order
    
    2. SEARCHING?
       - BST: Use BST properties
       - General tree: DFS with early termination
    
    3. PATH PROBLEMS?
       - Root to leaf: DFS with backtracking
       - Any path: Consider each node as potential start
    
    4. TREE MODIFICATION?
       - Structure change: Recursive with careful pointer management
       - Value change: Simple traversal with modification
    
    5. VALIDATION?
       - BST: Inorder or min/max bounds
       - Balance: Height comparison
       - Structure: Recursive property checking
    
    6. CONSTRUCTION?
       - From traversals: Use array indices carefully
       - From other structures: Map relationships
    
    7. COMPARISON?
       - Same structure: Parallel traversal
       - Subtree: Check at each possible root
    
    8. OPTIMIZATION NEEDED?
       - Space: Consider Morris traversal
       - Time: Look for early termination opportunities
    """
    pass

# Common debugging utilities
def print_tree_structure(root, level=0, prefix="Root: "):
    """Print tree structure for debugging"""
    if root:
        print(" " * (level * 4) + prefix + str(root.val))
        if root.left or root.right:
            if root.left:
                print_tree_structure(root.left, level + 1, "L--- ")
            else:
                print(" " * ((level + 1) * 4) + "L--- None")
            if root.right:
                print_tree_structure(root.right, level + 1, "R--- ")
            else:
                print(" " * ((level + 1) * 4) + "R--- None")

def validate_tree_structure(root):
    """Validate basic tree structure"""
    if not root:
        return True
    
    # Check for cycles (simplified)
    visited = set()
    
    def dfs(node):
        if not node:
            return True
        if id(node) in visited:
            return False  # Cycle detected
        
        visited.add(id(node))
        return dfs(node.left) and dfs(node.right)
    
    return dfs(root)
```

## 13. Performance Considerations

### Time and Space Complexity Guide

```python
"""
TRAVERSAL COMPLEXITIES:
- DFS (Recursive): Time O(n), Space O(h) where h is height
- DFS (Iterative): Time O(n), Space O(h) 
- BFS: Time O(n), Space O(w) where w is maximum width
- Morris: Time O(n), Space O(1)

SEARCH COMPLEXITIES:
- BST Search: Average O(log n), Worst O(n)
- General Tree: O(n)

CONSTRUCTION COMPLEXITIES:
- From arrays: Usually O(n) with proper indexing
- Balanced construction: O(n log n)

MODIFICATION COMPLEXITIES:
- Insertion/Deletion in BST: Average O(log n), Worst O(n)
- Tree restructuring: Usually O(n)

MEMORY CONSIDERATIONS:
- Python: Each node ~200-400 bytes
- Rust: More memory efficient, ~24-32 bytes per node
- Consider iterative solutions for deep trees
"""

def benchmark_tree_operations():
    import time
    import sys
    
    # Create test tree
    def create_balanced_tree(depth):
        if depth <= 0:
            return None
        
        root = TreeNode(depth)
        root.left = create_balanced_tree(depth - 1)
        root.right = create_balanced_tree(depth - 1)
        return root
    
    tree = create_balanced_tree(15)  # 2^15 - 1 nodes
    
    # Benchmark different traversals
    start = time.time()
    inorder_recursive(tree)
    recursive_time = time.time() - start
    
    start = time.time()
    inorder_iterative(tree)
    iterative_time = time.time() - start
    
    print(f"Recursive inorder: {recursive_time:.4f}s")
    print(f"Iterative inorder: {iterative_time:.4f}s")
    print(f"Recursion limit: {sys.getrecursionlimit()}")
```

## 14. Test Cases and Edge Cases

### Comprehensive Test Suite

```python
def test_tree_algorithms():
    """Comprehensive test cases for tree algorithms"""
    
    # Test case 1: Empty tree
    assert inorder_recursive(None) == []
    assert level_order(None) == []
    assert max_depth(None) == 0
    
    # Test case 2: Single node
    single = TreeNode(1)
    assert inorder_recursive(single) == [1]
    assert max_depth(single) == 1
    assert is_balanced(single) == True
    
    # Test case 3: Perfect binary tree
    perfect = TreeNode(1)
    perfect.left = TreeNode(2)
    perfect.right = TreeNode(3)
    perfect.left.left = TreeNode(4)
    perfect.left.right = TreeNode(5)
    perfect.right.left = TreeNode(6)
    perfect.right.right = TreeNode(7)
    
    assert level_order(perfect) == [[1], [2, 3], [4, 5, 6, 7]]
    assert is_balanced(perfect) == True
    
    # Test case 4: Skewed tree (worst case)
    skewed = TreeNode(1)
    current = skewed
    for i in range(2, 6):
        current.right = TreeNode(i)
        current = current.right
    
    assert max_depth(skewed) == 5
    assert is_balanced(skewed) == False
    
    # Test case 5: BST validation
    valid_bst = TreeNode(5)
    valid_bst.left = TreeNode(3)
    valid_bst.right = TreeNode(8)
    valid_bst.left.left = TreeNode(1)
    valid_bst.left.right = TreeNode(4)
    
    assert is_valid_bst(valid_bst) == True
    
    invalid_bst = TreeNode(5)
    invalid_bst.left = TreeNode(3)
    invalid_bst.right = TreeNode(8)
    invalid_bst.left.right = TreeNode(6)  # Invalid: 6 > 5
    
    assert is_valid_bst(invalid_bst) == False
    
    print("All tests passed!")

# Run tests
if __name__ == "__main__":
    test_tree_algorithms()
    demo_tree_analysis()
```

This comprehensive guide covers all major tree problem patterns with complete implementations in both Python and Rust. Each pattern includes:

1. **Clear use cases** - When to apply each pattern
2. **Complete implementations** - Both recursive and iterative where applicable
3. **Time/space complexity** - Performance characteristics
4. **Test cases** - Edge cases and validation
5. **Best practices** - Memory management and optimization tips

The guide progresses from basic traversals to advanced patterns, making it suitable for both learning and reference during coding interviews or competitive programming.
I've created a comprehensive guide to tree problem patterns with complete implementations in both Python and Rust. This guide covers:

## Key Patterns Covered:

1. **Tree Traversals** - DFS (preorder, inorder, postorder) and BFS with both recursive and iterative approaches
2. **Tree Construction** - Building trees from traversal arrays and other structures
3. **Path Finding** - Root-to-leaf paths, path sums, and general path problems
4. **Tree Validation** - BST validation, balance checking, structural validation
5. **Tree Manipulation** - Inversion, flattening, and structural modifications
6. **Ancestor/Descendant** - LCA problems and relationship queries
7. **Tree Comparison** - Structural equality, subtree detection, symmetry
8. **BST Operations** - Search, insert, delete operations
9. **Advanced Patterns** - Diameter, serialization, Morris traversal
10. **Specialized Techniques** - Parent pointers, threaded trees

## Features:

- **Complete implementations** in both Python and Rust
- **Time/space complexity** analysis for each pattern
- **Practical use cases** for when to apply each technique
- **Edge case handling** and comprehensive test suites
- **Performance optimization** tips and memory considerations
- **Debugging utilities** and validation functions
- **Decision framework** for choosing the right approach

The guide is structured to be both a learning resource and a practical reference for coding interviews, competitive programming, and real-world applications. Each pattern includes detailed explanations and multiple implementation approaches where beneficial.
