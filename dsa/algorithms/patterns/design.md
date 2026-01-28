# The Complete Architecture of LeetCode Design Patterns

I'll build this from absolute foundations to mastery level, explaining every concept as if you're encountering it for the first time.

---

## Part I: Foundation — What Are Design Patterns?

**Design Pattern**: A reusable template for solving a specific type of problem. Think of it as a "mental shortcut" — once you recognize the pattern, you know the approach.

In LeetCode context, design patterns are **recurring problem structures** that can be solved using specific algorithmic techniques.

### Why Patterns Matter for Top 1%

1. **Pattern Recognition Speed**: Elite coders recognize patterns in seconds
2. **Solution Space Reduction**: Instead of exploring infinite possibilities, patterns narrow your search
3. **Cognitive Chunking**: Your brain groups similar problems together, freeing mental bandwidth for optimization

---

## Part II: The Complete Pattern Taxonomy

I'll organize patterns into a hierarchical structure, from fundamental to advanced.

### 🎯 Pattern Category 1: ARRAY PATTERNS

#### 1.1 Two Pointers Pattern

**What it is**: Using two indices that move through an array according to specific rules.

**When to use**:
- Array is sorted
- Need to find pairs/triplets
- Need to process from both ends
- Need to partition/rearrange elements

**Core Concept — Pointer**: An index variable that "points" to a position in an array.

**Mental Model**: Imagine two fingers on a sorted list, moving toward each other or in the same direction.

##### Variants:

**a) Opposite Direction (Converging Pointers)**

```rust
// Problem: Two Sum II (sorted array)
fn two_sum(numbers: Vec<i32>, target: i32) -> Vec<i32> {
    let mut left = 0;           // Start pointer at beginning
    let mut right = numbers.len() - 1;  // End pointer at end
    
    while left < right {
        let sum = numbers[left] + numbers[right];
        
        match sum.cmp(&target) {
            std::cmp::Ordering::Equal => {
                return vec![(left + 1) as i32, (right + 1) as i32];
            }
            std::cmp::Ordering::Less => left += 1,   // Sum too small, move left up
            std::cmp::Ordering::Greater => right -= 1, // Sum too large, move right down
        }
    }
    
    vec![]
}

// Time: O(n) — single pass
// Space: O(1) — only two pointers
```

**Why this works**: 
- Sorted array guarantees: moving left pointer increases sum, moving right decreases sum
- This creates a **monotonic search space** (always moving toward answer)

**Go version** (showing idiomatic differences):

```go
func twoSum(numbers []int, target int) []int {
    left, right := 0, len(numbers)-1
    
    for left < right {
        sum := numbers[left] + numbers[right]
        
        switch {
        case sum == target:
            return []int{left + 1, right + 1}
        case sum < target:
            left++
        default:
            right--
        }
    }
    
    return nil
}
```

**b) Same Direction (Fast & Slow Pointers)**

```rust
// Problem: Remove Duplicates from Sorted Array
fn remove_duplicates(nums: &mut Vec<i32>) -> i32 {
    if nums.is_empty() {
        return 0;
    }
    
    let mut slow = 0;  // Position for next unique element
    
    for fast in 1..nums.len() {
        // Fast explores, slow maintains invariant
        if nums[fast] != nums[slow] {
            slow += 1;
            nums[slow] = nums[fast];
        }
    }
    
    (slow + 1) as i32
}

// Invariant: nums[0..=slow] contains unique elements
```

**Cognitive Model**: 
- **Slow pointer**: Maintains the "clean" state (invariant)
- **Fast pointer**: Explores/scans ahead
- This separation of concerns simplifies reasoning

**C version** (showing pointer arithmetic):

```c
int removeDuplicates(int* nums, int numsSize) {
    if (numsSize == 0) return 0;
    
    int slow = 0;
    
    for (int fast = 1; fast < numsSize; fast++) {
        if (nums[fast] != nums[slow]) {
            slow++;
            nums[slow] = nums[fast];
        }
    }
    
    return slow + 1;
}
```

---

#### 1.2 Sliding Window Pattern

**What it is**: A "window" (subarray) that slides through the array, expanding or contracting based on conditions.

**When to use**:
- Find subarray with property (max/min sum, specific length)
- Substring problems
- Consecutive elements
- Need to maintain running state

**Core Concept — Window**: A contiguous range [left, right] in the array.

##### Fixed Size Window

```rust
// Problem: Maximum Average Subarray I
fn find_max_average(nums: Vec<i32>, k: i32) -> f64 {
    let k = k as usize;
    
    // Initialize first window
    let mut window_sum: i32 = nums[..k].iter().sum();
    let mut max_sum = window_sum;
    
    // Slide window: add new element, remove old element
    for i in k..nums.len() {
        window_sum = window_sum + nums[i] - nums[i - k];
        max_sum = max_sum.max(window_sum);
    }
    
    max_sum as f64 / k as f64
}

// Time: O(n) — each element added and removed exactly once
// Space: O(1)
```

**Mental Model**: Imagine a physical window sliding across the array — as it moves right, one element enters, one exits.

##### Variable Size Window (Shrinking)

```rust
// Problem: Minimum Size Subarray Sum
fn min_sub_array_len(target: i32, nums: Vec<i32>) -> i32 {
    let mut left = 0;
    let mut sum = 0;
    let mut min_len = usize::MAX;
    
    for right in 0..nums.len() {
        // Expand window
        sum += nums[right];
        
        // Shrink window while valid
        while sum >= target {
            min_len = min_len.min(right - left + 1);
            sum -= nums[left];
            left += 1;
        }
    }
    
    if min_len == usize::MAX { 0 } else { min_len as i32 }
}

// Time: O(n) — each element visited at most twice (once by right, once by left)
```

**Key Insight**: Even though there's a nested loop, it's O(n) because `left` only moves forward.

**Flow of Execution**:
```
Initial: [2,3,1,2,4,3], target=7, left=0, right=0, sum=0

Step 1: right=0 → sum=2  [2]
Step 2: right=1 → sum=5  [2,3]
Step 3: right=2 → sum=6  [2,3,1]
Step 4: right=3 → sum=8  [2,3,1,2] ≥7 ✓
        Shrink: left=1 → sum=6  [3,1,2]
Step 5: right=4 → sum=10 [3,1,2,4] ≥7 ✓
        Shrink: left=2 → sum=7  [1,2,4] ≥7 ✓
        Shrink: left=3 → sum=6  [2,4]
```

##### Variable Size Window (String Pattern Matching)

```rust
use std::collections::HashMap;

// Problem: Minimum Window Substring
fn min_window(s: String, t: String) -> String {
    if t.is_empty() { return String::new(); }
    
    let s_bytes: Vec<char> = s.chars().collect();
    
    // Build frequency map of target string
    let mut need: HashMap<char, i32> = HashMap::new();
    for c in t.chars() {
        *need.entry(c).or_insert(0) += 1;
    }
    
    let mut have: HashMap<char, i32> = HashMap::new();
    let mut formed = 0;  // How many unique chars have required frequency
    let required = need.len();
    
    let mut left = 0;
    let mut min_len = usize::MAX;
    let mut min_start = 0;
    
    for right in 0..s_bytes.len() {
        let c = s_bytes[right];
        *have.entry(c).or_insert(0) += 1;
        
        // Check if current character's frequency matches requirement
        if need.contains_key(&c) && have[&c] == need[&c] {
            formed += 1;
        }
        
        // Try to shrink window while it's valid
        while formed == required && left <= right {
            // Update result
            if right - left + 1 < min_len {
                min_len = right - left + 1;
                min_start = left;
            }
            
            // Shrink from left
            let left_char = s_bytes[left];
            *have.get_mut(&left_char).unwrap() -= 1;
            
            if need.contains_key(&left_char) && have[&left_char] < need[&left_char] {
                formed -= 1;
            }
            
            left += 1;
        }
    }
    
    if min_len == usize::MAX {
        String::new()
    } else {
        s_bytes[min_start..min_start + min_len].iter().collect()
    }
}

// Time: O(|S| + |T|)
// Space: O(|S| + |T|) for hash maps
```

**Advanced Insight**: The `formed` counter is the key optimization — instead of checking all characters every time, we track when the window becomes valid/invalid.

---

#### 1.3 Prefix Sum Pattern

**What it is**: Precompute cumulative sums to answer range queries in O(1).

**Core Concept — Prefix Sum**: `prefix[i]` = sum of elements from index 0 to i.

**Mathematical Insight**: 
```
sum(i, j) = prefix[j] - prefix[i-1]
```

**Why this works**: 
```
prefix[j] = arr[0] + arr[1] + ... + arr[i-1] + arr[i] + ... + arr[j]
prefix[i-1] = arr[0] + arr[1] + ... + arr[i-1]

prefix[j] - prefix[i-1] = arr[i] + ... + arr[j]  ← range sum!
```

```rust
// Problem: Range Sum Query - Immutable
struct NumArray {
    prefix: Vec<i32>,
}

impl NumArray {
    fn new(nums: Vec<i32>) -> Self {
        let mut prefix = vec![0; nums.len() + 1];
        
        for i in 0..nums.len() {
            prefix[i + 1] = prefix[i] + nums[i];
        }
        
        NumArray { prefix }
    }
    
    fn sum_range(&self, left: i32, right: i32) -> i32 {
        let (left, right) = (left as usize, right as usize);
        self.prefix[right + 1] - self.prefix[left]
    }
}

// Construction: O(n)
// Query: O(1)
```

**Visualization**:
```
nums:   [1, 2, 3, 4, 5]
prefix: [0, 1, 3, 6, 10, 15]
         ↑
         dummy 0 to simplify logic

sum_range(1, 3) = prefix[4] - prefix[1] = 10 - 1 = 9
                = 2 + 3 + 4 ✓
```

##### 2D Prefix Sum

```rust
// Problem: Range Sum Query 2D
struct NumMatrix {
    prefix: Vec<Vec<i32>>,
}

impl NumMatrix {
    fn new(matrix: Vec<Vec<i32>>) -> Self {
        if matrix.is_empty() || matrix[0].is_empty() {
            return NumMatrix { prefix: vec![] };
        }
        
        let (rows, cols) = (matrix.len(), matrix[0].len());
        let mut prefix = vec![vec![0; cols + 1]; rows + 1];
        
        for r in 0..rows {
            for c in 0..cols {
                prefix[r + 1][c + 1] = matrix[r][c]
                    + prefix[r + 1][c]      // left
                    + prefix[r][c + 1]      // top
                    - prefix[r][c];         // subtract overlap
            }
        }
        
        NumMatrix { prefix }
    }
    
    fn sum_region(&self, row1: i32, col1: i32, row2: i32, col2: i32) -> i32 {
        let (r1, c1, r2, c2) = (row1 as usize, col1 as usize, row2 as usize, col2 as usize);
        
        self.prefix[r2 + 1][c2 + 1]
            - self.prefix[r1][c2 + 1]       // remove top
            - self.prefix[r2 + 1][c1]       // remove left
            + self.prefix[r1][c1]           // add back overlap
    }
}
```

**Inclusion-Exclusion Principle**: 
```
Total = BigRectangle - TopPart - LeftPart + Overlap
```

**Diagram**:
```
        c1      c2
r1  +----+------+
    |    |######|  Top (to remove)
    +----O======+
    |    ║######║  Target region
r2  +----+------+
    Left       
  (to remove)

O = overlap (added twice in removals, so add back once)
```

---

### 🎯 Pattern Category 2: LINKED LIST PATTERNS

**Core Concept — Linked List**: A data structure where each element (node) contains data and a pointer to the next node.

```rust
// Definition
#[derive(PartialEq, Eq, Clone, Debug)]
pub struct ListNode {
    pub val: i32,
    pub next: Option<Box<ListNode>>,
}
```

**Why Linked Lists are Tricky**: 
- No random access (can't jump to index i directly)
- Pointer manipulation requires careful handling
- Off-by-one errors are common

#### 2.1 Fast & Slow Pointers (Tortoise and Hare)

**What it is**: Two pointers moving at different speeds.

**When to use**:
- Detect cycles
- Find middle element
- Find kth element from end

**Mathematical Insight**: If there's a cycle, fast pointer will eventually "lap" slow pointer.

```rust
// Problem: Linked List Cycle
fn has_cycle(head: Option<Box<ListNode>>) -> bool {
    let mut slow = &head;
    let mut fast = &head;
    
    while fast.is_some() && fast.as_ref().unwrap().next.is_some() {
        // Move slow by 1
        slow = &slow.as_ref().unwrap().next;
        
        // Move fast by 2
        fast = &fast.as_ref().unwrap().next.as_ref().unwrap().next;
        
        // Check if they meet
        if slow.as_ref().map(|n| n as *const _) == fast.as_ref().map(|n| n as *const _) {
            return true;
        }
    }
    
    false
}
```

**Why This Works** (Proof Sketch):
1. If no cycle: fast reaches end first → return false
2. If cycle exists:
   - Let's say slow enters cycle after `k` steps
   - Fast is already `k` steps ahead in cycle
   - Distance between them decreases by 1 each step
   - They must meet within cycle length steps

##### Finding Cycle Start (Floyd's Algorithm)

```rust
fn detect_cycle(head: Option<Box<ListNode>>) -> Option<Box<ListNode>> {
    let mut slow = &head;
    let mut fast = &head;
    
    // Phase 1: Detect cycle
    while fast.is_some() && fast.as_ref().unwrap().next.is_some() {
        slow = &slow.as_ref().unwrap().next;
        fast = &fast.as_ref().unwrap().next.as_ref().unwrap().next;
        
        if let (Some(s), Some(f)) = (slow, fast) {
            if std::ptr::eq(s.as_ref(), f.as_ref()) {
                // Phase 2: Find start
                let mut ptr1 = &head;
                let mut ptr2 = slow;
                
                while !std::ptr::eq(
                    ptr1.as_ref().unwrap().as_ref(),
                    ptr2.as_ref().unwrap().as_ref()
                ) {
                    ptr1 = &ptr1.as_ref().unwrap().next;
                    ptr2 = &ptr2.as_ref().unwrap().next;
                }
                
                return ptr1.clone();
            }
        }
    }
    
    None
}
```

**Mathematical Magic**:
- Let distance from head to cycle start = `a`
- Let distance from cycle start to meeting point = `b`
- Let remaining cycle length = `c`

When they meet:
- Slow traveled: `a + b`
- Fast traveled: `a + b + c + b` (one extra loop)

Since fast is 2x speed:
```
2(a + b) = a + 2b + c
2a + 2b = a + 2b + c
a = c
```

So distance from head to start = distance from meeting point to start!

---

#### 2.2 Reverse Linked List Pattern

**Core Technique**: Iteratively reverse pointers.

```rust
fn reverse_list(head: Option<Box<ListNode>>) -> Option<Box<ListNode>> {
    let mut prev = None;
    let mut curr = head;
    
    while let Some(mut node) = curr {
        // Save next
        let next = node.next.take();
        
        // Reverse pointer
        node.next = prev;
        
        // Move forward
        prev = Some(node);
        curr = next;
    }
    
    prev
}
```

**Step-by-Step Execution**:
```
Initial: 1 → 2 → 3 → None
         ↑
        curr
prev=None

Step 1: Save next=2→3
        1.next = None
        prev = 1→None
        curr = 2→3

Step 2: Save next=3→None
        2.next = 1→None
        prev = 2→1→None
        curr = 3→None

Step 3: Save next=None
        3.next = 2→1→None
        prev = 3→2→1→None
        curr = None

Result: 3 → 2 → 1 → None
```

**Mental Model**: Three-way handshake — always keep track of prev, curr, next.

---

### 🎯 Pattern Category 3: TREE PATTERNS

**Core Concept — Tree**: Hierarchical structure with nodes connected by edges, starting from a root.

**Tree Terminology**:
- **Root**: Top node with no parent
- **Leaf**: Node with no children
- **Height**: Longest path from node to leaf
- **Depth**: Distance from root to node
- **Subtree**: Node and all its descendants

```rust
#[derive(Debug, PartialEq, Eq)]
pub struct TreeNode {
    pub val: i32,
    pub left: Option<Rc<RefCell<TreeNode>>>,
    pub right: Option<Rc<RefCell<TreeNode>>>,
}
```

#### 3.1 Tree Traversal Patterns

**Why Multiple Traversals?**: Different traversals expose different properties.

##### a) Depth-First Search (DFS)

**Preorder** (Root → Left → Right):
```rust
fn preorder(root: Option<Rc<RefCell<TreeNode>>>) -> Vec<i32> {
    let mut result = vec![];
    
    fn dfs(node: Option<Rc<RefCell<TreeNode>>>, result: &mut Vec<i32>) {
        if let Some(n) = node {
            result.push(n.borrow().val);           // Process root
            dfs(n.borrow().left.clone(), result);  // Left subtree
            dfs(n.borrow().right.clone(), result); // Right subtree
        }
    }
    
    dfs(root, &mut result);
    result
}
```

**Use Case**: Copy tree structure, serialize tree.

**Inorder** (Left → Root → Right):
```rust
fn inorder(root: Option<Rc<RefCell<TreeNode>>>) -> Vec<i32> {
    let mut result = vec![];
    
    fn dfs(node: Option<Rc<RefCell<TreeNode>>>, result: &mut Vec<i32>) {
        if let Some(n) = node {
            dfs(n.borrow().left.clone(), result);
            result.push(n.borrow().val);
            dfs(n.borrow().right.clone(), result);
        }
    }
    
    dfs(root, &mut result);
    result
}
```

**Critical Property**: For Binary Search Tree, inorder gives **sorted sequence**!

**Postorder** (Left → Right → Root):
```rust
fn postorder(root: Option<Rc<RefCell<TreeNode>>>) -> Vec<i32> {
    let mut result = vec![];
    
    fn dfs(node: Option<Rc<RefCell<TreeNode>>>, result: &mut Vec<i32>) {
        if let Some(n) = node {
            dfs(n.borrow().left.clone(), result);
            dfs(n.borrow().right.clone(), result);
            result.push(n.borrow().val);
        }
    }
    
    dfs(root, &mut result);
    result
}
```

**Use Case**: Delete tree (process children before parent), evaluate expression tree.

##### Iterative DFS with Stack

```rust
fn preorder_iterative(root: Option<Rc<RefCell<TreeNode>>>) -> Vec<i32> {
    let mut result = vec![];
    let mut stack = vec![];
    
    if let Some(node) = root {
        stack.push(node);
    }
    
    while let Some(node) = stack.pop() {
        result.push(node.borrow().val);
        
        // Push right first so left is processed first
        if let Some(right) = node.borrow().right.clone() {
            stack.push(right);
        }
        if let Some(left) = node.borrow().left.clone() {
            stack.push(left);
        }
    }
    
    result
}
```

**Why Right Before Left?**: Stack is LIFO (Last In First Out), so we push right first to process left first.

##### b) Breadth-First Search (BFS) / Level Order

```rust
use std::collections::VecDeque;

fn level_order(root: Option<Rc<RefCell<TreeNode>>>) -> Vec<Vec<i32>> {
    let mut result = vec![];
    
    if root.is_none() {
        return result;
    }
    
    let mut queue = VecDeque::new();
    queue.push_back(root.unwrap());
    
    while !queue.is_empty() {
        let level_size = queue.len();
        let mut level = vec![];
        
        // Process all nodes at current level
        for _ in 0..level_size {
            let node = queue.pop_front().unwrap();
            level.push(node.borrow().val);
            
            if let Some(left) = node.borrow().left.clone() {
                queue.push_back(left);
            }
            if let Some(right) = node.borrow().right.clone() {
                queue.push_back(right);
            }
        }
        
        result.push(level);
    }
    
    result
}
```

**Key Technique**: Process nodes level by level using queue's size at each iteration.

**Visualization**:
```
Tree:       1
           / \
          2   3
         / \
        4   5

Execution:
Level 0: queue=[1]         → output=[[1]]
Level 1: queue=[2,3]       → output=[[1],[2,3]]
Level 2: queue=[4,5]       → output=[[1],[2,3],[4,5]]
```

---

This is Part 1. The guide continues with:

**Part 2 will cover**:
- Binary Search patterns
- Backtracking patterns
- Dynamic Programming patterns
- Graph patterns
- Stack/Queue patterns
- Heap patterns
- Union-Find pattern
- Bit Manipulation patterns

Would you like me to continue with Part 2, or would you prefer to:
1. Work through practice problems for Part 1 patterns
2. See more complex variants of current patterns
3. Get language-specific optimization techniques for these patterns

Let me know what serves your mastery path best.