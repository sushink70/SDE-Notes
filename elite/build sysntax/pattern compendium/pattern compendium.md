# Comprehensive DSA Patterns & Manipulation Guide
*A systematic approach to pattern recognition and problem-solving mastery*

---

## 📋 Table of Contents
1. [Mental Framework & Problem-Solving Methodology](#mental-framework)
2. [Array Patterns](#array-patterns)
3. [String Patterns](#string-patterns)
4. [Linked List Patterns](#linked-list-patterns)
5. [Stack & Queue Patterns](#stack-queue-patterns)
6. [Tree Patterns](#tree-patterns)
6. [Graph Patterns](#graph-patterns)
7. [Hash Table Patterns](#hash-patterns)
8. [Heap Patterns](#heap-patterns)
9. [Advanced Algorithmic Patterns](#advanced-patterns)
10. [Bit Manipulation Patterns](#bit-patterns)
11. [Mathematical & Number Theory Patterns](#math-patterns)

---

## Mental Framework & Problem-Solving Methodology {#mental-framework}

### The Expert's Problem-Solving Protocol

**Phase 1: Problem Decomposition (2-3 minutes)**
1. **Clarify constraints** - Range of inputs, edge cases, expected output format
2. **Identify the problem class** - Search, optimization, counting, construction?
3. **Recognize the data structure signature** - What operations dominate? Access? Insert? Search?
4. **Map to known patterns** - Does this resemble a problem you've solved?

**Phase 2: Solution Design (3-5 minutes)**
1. **Brute force first** - Always know the O(n²) or O(2ⁿ) solution
2. **Identify bottlenecks** - What operation is repeated unnecessarily?
3. **Apply optimization patterns** - Can you trade space for time? Can you preprocess?
4. **Consider data structure upgrades** - Would a heap/trie/segment tree help?

**Phase 3: Implementation (10-15 minutes)**
1. **Write clean, testable code**
2. **Handle edge cases systematically**
3. **Use meaningful variable names**

**Phase 4: Verification (2-3 minutes)**
1. **Trace through examples**
2. **Analyze complexity**
3. **Consider alternative approaches**

### Cognitive Principles for Accelerated Mastery

**Chunking**: Group patterns into mental units. "Two pointers" becomes a single retrieval, not multiple steps.

**Deliberate Practice**: Focus on problems slightly beyond your comfort zone. Master one pattern deeply before moving to the next.

**Interleaving**: Mix problem types in practice sessions to strengthen pattern recognition.

**Spaced Repetition**: Revisit patterns at increasing intervals (1 day, 3 days, 1 week, 2 weeks, 1 month).

---

## Array Patterns {#array-patterns}

### Pattern 1: Two Pointers

**When to use**: Sorted arrays, palindromes, pair finding, partitioning

**Core Technique**: Use two indices moving toward each other or in same direction

**Variants**:
- **Opposite Direction** (left → right, right → left)
- **Same Direction** (fast/slow pointers)
- **Sliding Window** (variable-width two pointers)

**Time Complexity**: O(n) | **Space**: O(1)

```python
# Python: Two Sum in Sorted Array
def two_sum_sorted(arr, target):
    left, right = 0, len(arr) - 1
    
    while left < right:
        current_sum = arr[left] + arr[right]
        
        if current_sum == target:
            return [left, right]
        elif current_sum < target:
            left += 1  # Need larger sum
        else:
            right -= 1  # Need smaller sum
    
    return None

# Time: O(n), Space: O(1)
```

```rust
// Rust: Remove Duplicates from Sorted Array (in-place)
pub fn remove_duplicates(nums: &mut Vec<i32>) -> usize {
    if nums.is_empty() {
        return 0;
    }
    
    let mut write = 1; // Slow pointer (write position)
    
    for read in 1..nums.len() { // Fast pointer (read position)
        if nums[read] != nums[read - 1] {
            nums[write] = nums[read];
            write += 1;
        }
    }
    
    write // New length
}
// Time: O(n), Space: O(1)
```

```c++
// C++: Dutch National Flag (3-way partitioning)
void sortColors(vector<int>& nums) {
    int low = 0, mid = 0, high = nums.size() - 1;
    
    while (mid <= high) {
        if (nums[mid] == 0) {
            swap(nums[low++], nums[mid++]);
        } else if (nums[mid] == 1) {
            mid++;
        } else { // nums[mid] == 2
            swap(nums[mid], nums[high--]);
        }
    }
}
// Time: O(n), Space: O(1)
```

**Mental Model**: Imagine scissors closing on paper - each pointer eliminates impossibilities.

---

### Pattern 2: Sliding Window

**When to use**: Subarray/substring problems with contiguous elements, "maximum/minimum in window"

**Core Technique**: Maintain a window [left, right] and expand/contract based on validity

**Variants**:
- **Fixed-size window**
- **Variable-size window**
- **Multiple windows**

**Time Complexity**: O(n) | **Space**: O(1) to O(k)

```python
# Python: Maximum Sum Subarray of Size K (Fixed Window)
def max_sum_subarray(arr, k):
    n = len(arr)
    if n < k:
        return None
    
    window_sum = sum(arr[:k])
    max_sum = window_sum
    
    for i in range(k, n):
        window_sum = window_sum - arr[i - k] + arr[i]
        max_sum = max(max_sum, window_sum)
    
    return max_sum

# Time: O(n), Space: O(1)
```

```rust
// Rust: Longest Substring Without Repeating Characters (Variable Window)
use std::collections::HashMap;

pub fn length_of_longest_substring(s: String) -> i32 {
    let mut char_index: HashMap<char, usize> = HashMap::new();
    let mut max_len = 0;
    let mut left = 0;
    let chars: Vec<char> = s.chars().collect();
    
    for right in 0..chars.len() {
        if let Some(&prev_index) = char_index.get(&chars[right]) {
            // Move left pointer past the previous occurrence
            left = left.max(prev_index + 1);
        }
        
        char_index.insert(chars[right], right);
        max_len = max_len.max(right - left + 1);
    }
    
    max_len as i32
}
// Time: O(n), Space: O(min(n, charset))
```

```go
// Go: Minimum Window Substring
func minWindow(s string, t string) string {
    if len(s) < len(t) {
        return ""
    }
    
    need := make(map[byte]int)
    for i := range t {
        need[t[i]]++
    }
    
    have := make(map[byte]int)
    required := len(need)
    formed := 0
    
    left, right := 0, 0
    minLen := len(s) + 1
    minLeft := 0
    
    for right < len(s) {
        // Expand window
        c := s[right]
        have[c]++
        
        if _, ok := need[c]; ok && have[c] == need[c] {
            formed++
        }
        
        // Contract window while valid
        for left <= right && formed == required {
            // Update result
            if right - left + 1 < minLen {
                minLen = right - left + 1
                minLeft = left
            }
            
            // Remove leftmost character
            c = s[left]
            have[c]--
            if _, ok := need[c]; ok && have[c] < need[c] {
                formed--
            }
            left++
        }
        
        right++
    }
    
    if minLen == len(s) + 1 {
        return ""
    }
    return s[minLeft:minLeft + minLen]
}
// Time: O(|S| + |T|), Space: O(|T|)
```

**Mental Model**: A window is a spotlight - you illuminate just enough to see what you need.

---

### Pattern 3: Prefix Sum / Cumulative Sum

**When to use**: Range sum queries, subarray sum problems

**Core Technique**: Precompute cumulative sums to answer queries in O(1)

```python
# Python: Prefix Sum for Range Queries
class PrefixSum:
    def __init__(self, nums):
        self.prefix = [0]
        for num in nums:
            self.prefix.append(self.prefix[-1] + num)
    
    def range_sum(self, left, right):
        # Sum from index left to right (inclusive)
        return self.prefix[right + 1] - self.prefix[left]

# Subarray Sum Equals K
def subarray_sum(nums, k):
    count = 0
    prefix_sum = 0
    sum_freq = {0: 1}  # sum -> frequency
    
    for num in nums:
        prefix_sum += num
        
        # If (prefix_sum - k) exists, we found subarrays
        if prefix_sum - k in sum_freq:
            count += sum_freq[prefix_sum - k]
        
        sum_freq[prefix_sum] = sum_freq.get(prefix_sum, 0) + 1
    
    return count
# Time: O(n), Space: O(n)
```

```rust
// Rust: 2D Prefix Sum (Image/Matrix queries)
pub struct MatrixSum {
    prefix: Vec<Vec<i32>>,
}

impl MatrixSum {
    pub fn new(matrix: Vec<Vec<i32>>) -> Self {
        let m = matrix.len();
        let n = if m > 0 { matrix[0].len() } else { 0 };
        let mut prefix = vec![vec![0; n + 1]; m + 1];
        
        for i in 1..=m {
            for j in 1..=n {
                prefix[i][j] = matrix[i-1][j-1] 
                    + prefix[i-1][j] 
                    + prefix[i][j-1] 
                    - prefix[i-1][j-1];
            }
        }
        
        MatrixSum { prefix }
    }
    
    pub fn sum_region(&self, row1: usize, col1: usize, 
                      row2: usize, col2: usize) -> i32 {
        self.prefix[row2+1][col2+1]
            - self.prefix[row1][col2+1]
            - self.prefix[row2+1][col1]
            + self.prefix[row1][col1]
    }
}
// Query Time: O(1), Preprocessing: O(m*n)
```

---

### Pattern 4: Kadane's Algorithm (Maximum Subarray)

**When to use**: Finding maximum/minimum sum subarray

**Core Insight**: At each position, decide: extend current subarray or start fresh?

```c++
// C++: Maximum Subarray Sum
int maxSubArray(vector<int>& nums) {
    int max_so_far = nums[0];
    int max_ending_here = nums[0];
    
    for (int i = 1; i < nums.size(); i++) {
        // Extend or start new?
        max_ending_here = max(nums[i], max_ending_here + nums[i]);
        max_so_far = max(max_so_far, max_ending_here);
    }
    
    return max_so_far;
}
// Time: O(n), Space: O(1)
```

**Variant: Maximum Subarray Product**
```python
def max_product(nums):
    max_prod = min_prod = result = nums[0]
    
    for num in nums[1:]:
        if num < 0:
            max_prod, min_prod = min_prod, max_prod  # Swap!
        
        max_prod = max(num, max_prod * num)
        min_prod = min(num, min_prod * num)
        result = max(result, max_prod)
    
    return result
```

---

### Pattern 5: Binary Search on Arrays

**When to use**: Sorted arrays, search space reduction, "find first/last" problems

**Core Technique**: Eliminate half the search space each iteration

**Time Complexity**: O(log n)

```python
# Python: Binary Search Template (Finding insertion position)
def binary_search(arr, target):
    left, right = 0, len(arr)
    
    while left < right:
        mid = left + (right - left) // 2
        
        if arr[mid] < target:
            left = mid + 1
        else:
            right = mid
    
    return left  # Insertion position

# Find First and Last Position
def search_range(nums, target):
    def find_first():
        left, right = 0, len(nums)
        while left < right:
            mid = left + (right - left) // 2
            if nums[mid] < target:
                left = mid + 1
            else:
                right = mid
        return left
    
    def find_last():
        left, right = 0, len(nums)
        while left < right:
            mid = left + (right - left) // 2
            if nums[mid] <= target:
                left = mid + 1
            else:
                right = mid
        return left - 1
    
    first = find_first()
    if first == len(nums) or nums[first] != target:
        return [-1, -1]
    
    return [first, find_last()]
```

```rust
// Rust: Binary Search on Answer (Capacity to Ship in D Days)
pub fn ship_within_days(weights: Vec<i32>, days: i32) -> i32 {
    let can_ship = |capacity: i32| -> bool {
        let mut days_needed = 1;
        let mut current_load = 0;
        
        for &w in &weights {
            if current_load + w > capacity {
                days_needed += 1;
                current_load = w;
            } else {
                current_load += w;
            }
        }
        
        days_needed <= days
    };
    
    let (mut left, mut right) = (*weights.iter().max().unwrap(), 
                                   weights.iter().sum());
    
    while left < right {
        let mid = left + (right - left) / 2;
        if can_ship(mid) {
            right = mid;
        } else {
            left = mid + 1;
        }
    }
    
    left
}
// Time: O(n log(sum - max)), Space: O(1)
```

**Mental Model**: Binary search is pruning a decision tree - each comparison eliminates an entire subtree of possibilities.

---

### Pattern 6: Cyclic Sort

**When to use**: Arrays containing numbers in range [1, n] or [0, n-1]

**Core Technique**: Place each number at its correct index position

```python
# Python: Find All Missing Numbers in [1, n]
def find_missing(nums):
    i = 0
    while i < len(nums):
        correct_pos = nums[i] - 1
        # If number is not in its correct position, swap it
        if nums[i] != nums[correct_pos]:
            nums[i], nums[correct_pos] = nums[correct_pos], nums[i]
        else:
            i += 1
    
    # Now find missing numbers
    missing = []
    for i in range(len(nums)):
        if nums[i] != i + 1:
            missing.append(i + 1)
    
    return missing
# Time: O(n), Space: O(1)
```

---

### Pattern 7: Merge Intervals

**When to use**: Overlapping intervals, scheduling problems

**Core Technique**: Sort by start time, then merge overlapping intervals

```c++
// C++: Merge Overlapping Intervals
vector<vector<int>> merge(vector<vector<int>>& intervals) {
    if (intervals.empty()) return {};
    
    sort(intervals.begin(), intervals.end());
    vector<vector<int>> merged;
    merged.push_back(intervals[0]);
    
    for (int i = 1; i < intervals.size(); i++) {
        if (intervals[i][0] <= merged.back()[1]) {
            // Overlapping - merge
            merged.back()[1] = max(merged.back()[1], intervals[i][1]);
        } else {
            // Non-overlapping - add new interval
            merged.push_back(intervals[i]);
        }
    }
    
    return merged;
}
// Time: O(n log n), Space: O(n)
```

---

## String Patterns {#string-patterns}

### Pattern 1: Character Frequency / Sliding Window

```python
# Anagram Detection
from collections import Counter

def find_anagrams(s, p):
    result = []
    p_count = Counter(p)
    window_count = Counter()
    
    for i in range(len(s)):
        # Add character to window
        window_count[s[i]] += 1
        
        # Remove leftmost character if window too large
        if i >= len(p):
            left_char = s[i - len(p)]
            if window_count[left_char] == 1:
                del window_count[left_char]
            else:
                window_count[left_char] -= 1
        
        # Check if anagram
        if window_count == p_count:
            result.append(i - len(p) + 1)
    
    return result
```

### Pattern 2: Two Pointers for String Manipulation

```rust
// Rust: Reverse Words in String
pub fn reverse_words(s: String) -> String {
    s.split_whitespace()
        .rev()
        .collect::<Vec<&str>>()
        .join(" ")
}

// Manual two-pointer approach for in-place reversal
pub fn reverse_string(s: &mut Vec<char>) {
    let mut left = 0;
    let mut right = s.len() - 1;
    
    while left < right {
        s.swap(left, right);
        left += 1;
        right -= 1;
    }
}
```

### Pattern 3: String Matching (KMP, Rabin-Karp)

```python
# Rabin-Karp: Rolling Hash for Pattern Matching
def rabin_karp(text, pattern):
    n, m = len(text), len(pattern)
    if m > n:
        return -1
    
    BASE = 256
    MOD = 101
    
    # Calculate hash value for pattern and first window
    pattern_hash = 0
    window_hash = 0
    h = pow(BASE, m - 1) % MOD
    
    for i in range(m):
        pattern_hash = (BASE * pattern_hash + ord(pattern[i])) % MOD
        window_hash = (BASE * window_hash + ord(text[i])) % MOD
    
    # Slide the window
    for i in range(n - m + 1):
        if pattern_hash == window_hash:
            # Hash matches - verify character by character
            if text[i:i+m] == pattern:
                return i
        
        if i < n - m:
            # Calculate hash for next window
            window_hash = (BASE * (window_hash - ord(text[i]) * h) 
                          + ord(text[i + m])) % MOD
            if window_hash < 0:
                window_hash += MOD
    
    return -1
# Average Time: O(n + m), Worst: O(nm)
```

### Pattern 4: Palindrome Techniques

```c++
// C++: Expand Around Center (Longest Palindrome)
string longestPalindrome(string s) {
    if (s.empty()) return "";
    
    int start = 0, maxLen = 0;
    
    auto expandCenter = [&](int left, int right) {
        while (left >= 0 && right < s.length() && s[left] == s[right]) {
            left--;
            right++;
        }
        int len = right - left - 1;
        if (len > maxLen) {
            start = left + 1;
            maxLen = len;
        }
    };
    
    for (int i = 0; i < s.length(); i++) {
        expandCenter(i, i);       // Odd length palindromes
        expandCenter(i, i + 1);   // Even length palindromes
    }
    
    return s.substr(start, maxLen);
}
// Time: O(n²), Space: O(1)
```

---

## Linked List Patterns {#linked-list-patterns}

### Pattern 1: Fast & Slow Pointers (Floyd's Algorithm)

**When to use**: Cycle detection, finding middle, nth from end

```python
# Detect Cycle
def has_cycle(head):
    if not head:
        return False
    
    slow = fast = head
    
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        
        if slow == fast:
            return True
    
    return False

# Find Cycle Start
def detect_cycle(head):
    if not head:
        return None
    
    # Phase 1: Detect cycle
    slow = fast = head
    has_cycle = False
    
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        
        if slow == fast:
            has_cycle = True
            break
    
    if not has_cycle:
        return None
    
    # Phase 2: Find start of cycle
    slow = head
    while slow != fast:
        slow = slow.next
        fast = fast.next
    
    return slow
```

### Pattern 2: Reversal

```rust
// Rust: Reverse Linked List (Iterative)
pub fn reverse_list(head: Option<Box<ListNode>>) -> Option<Box<ListNode>> {
    let mut prev = None;
    let mut curr = head;
    
    while let Some(mut node) = curr {
        let next = node.next.take();
        node.next = prev;
        prev = Some(node);
        curr = next;
    }
    
    prev
}

// Reverse in groups of K
pub fn reverse_k_group(head: Option<Box<ListNode>>, k: i32) -> Option<Box<ListNode>> {
    // Implementation involves checking if k nodes exist, 
    // reversing them, and recursing
    // Time: O(n), Space: O(n/k) for recursion
    unimplemented!()
}
```

### Pattern 3: Merge & Split

```c++
// C++: Merge Two Sorted Lists
ListNode* mergeTwoLists(ListNode* l1, ListNode* l2) {
    ListNode dummy(0);
    ListNode* tail = &dummy;
    
    while (l1 && l2) {
        if (l1->val <= l2->val) {
            tail->next = l1;
            l1 = l1->next;
        } else {
            tail->next = l2;
            l2 = l2->next;
        }
        tail = tail->next;
    }
    
    tail->next = l1 ? l1 : l2;
    return dummy.next;
}
```

---

## Stack & Queue Patterns {#stack-queue-patterns}

### Pattern 1: Monotonic Stack

**When to use**: Next greater/smaller element, histogram problems

```python
# Next Greater Element
def next_greater_elements(nums):
    n = len(nums)
    result = [-1] * n
    stack = []  # Stores indices
    
    # Circular array: iterate twice
    for i in range(2 * n):
        while stack and nums[stack[-1]] < nums[i % n]:
            result[stack.pop()] = nums[i % n]
        
        if i < n:
            stack.append(i)
    
    return result
# Time: O(n), Space: O(n)

# Largest Rectangle in Histogram
def largest_rectangle_area(heights):
    stack = []
    max_area = 0
    heights.append(0)  # Sentinel
    
    for i, h in enumerate(heights):
        while stack and heights[stack[-1]] > h:
            height = heights[stack.pop()]
            width = i if not stack else i - stack[-1] - 1
            max_area = max(max_area, height * width)
        stack.append(i)
    
    return max_area
```

### Pattern 2: Stack for Expression Evaluation

```go
// Go: Basic Calculator
func calculate(s string) int {
    stack := []int{}
    num := 0
    sign := 1
    result := 0
    
    for i := 0; i < len(s); i++ {
        c := s[i]
        
        if c >= '0' && c <= '9' {
            num = num*10 + int(c-'0')
        } else if c == '+' {
            result += sign * num
            num = 0
            sign = 1
        } else if c == '-' {
            result += sign * num
            num = 0
            sign = -1
        } else if c == '(' {
            stack = append(stack, result, sign)
            result = 0
            sign = 1
        } else if c == ')' {
            result += sign * num
            num = 0
            result *= stack[len(stack)-1]  // Pop sign
            stack = stack[:len(stack)-1]
            result += stack[len(stack)-1]  // Pop previous result
            stack = stack[:len(stack)-1]
        }
    }
    
    return result + sign*num
}
```

### Pattern 3: Queue for BFS

```rust
use std::collections::VecDeque;

// BFS Template
pub fn bfs(start: i32) {
    let mut queue = VecDeque::new();
    let mut visited = HashSet::new();
    
    queue.push_back(start);
    visited.insert(start);
    
    while let Some(node) = queue.pop_front() {
        // Process node
        
        // Add neighbors
        for neighbor in get_neighbors(node) {
            if !visited.contains(&neighbor) {
                visited.insert(neighbor);
                queue.push_back(neighbor);
            }
        }
    }
}
```

---

## Tree Patterns {#tree-patterns}

### Pattern 1: DFS Traversals

```python
# Preorder: Root -> Left -> Right
def preorder(root):
    if not root:
        return []
    return [root.val] + preorder(root.left) + preorder(root.right)

# Inorder: Left -> Root -> Right (Sorted for BST!)
def inorder(root):
    if not root:
        return []
    return inorder(root.left) + [root.val] + inorder(root.right)

# Postorder: Left -> Right -> Root
def postorder(root):
    if not root:
        return []
    return postorder(root.left) + postorder(root.right) + [root.val]

# Iterative Inorder (Space-efficient)
def inorder_iterative(root):
    result = []
    stack = []
    curr = root
    
    while curr or stack:
        # Go left as far as possible
        while curr:
            stack.append(curr)
            curr = curr.left
        
        # Process node
        curr = stack.pop()
        result.append(curr.val)
        
        # Go right
        curr = curr.right
    
    return result
```

### Pattern 2: Level-Order Traversal (BFS)

```c++
// C++: Level Order with Level Separation
vector<vector<int>> levelOrder(TreeNode* root) {
    if (!root) return {};
    
    vector<vector<int>> result;
    queue<TreeNode*> q;
    q.push(root);
    
    while (!q.empty()) {
        int level_size = q.size();
        vector<int> level;
        
        for (int i = 0; i < level_size; i++) {
            TreeNode* node = q.front();
            q.pop();
            level.push_back(node->val);
            
            if (node->left) q.push(node->left);
            if (node->right) q.push(node->right);
        }
        
        result.push_back(level);
    }
    
    return result;
}
```

### Pattern 3: Path Problems

```python
# Path Sum (Root to Leaf)
def has_path_sum(root, target_sum):
    if not root:
        return False
    
    # Leaf node
    if not root.left and not root.right:
        return root.val == target_sum
    
    # Recurse with reduced sum
    return (has_path_sum(root.left, target_sum - root.val) or
            has_path_sum(root.right, target_sum - root.val))

# All Root-to-Leaf Paths
def binary_tree_paths(root):
    if not root:
        return []
    
    paths = []
    
    def dfs(node, path):
        if not node.left and not node.right:
            paths.append(path + [node.val])
            return
        
        if node.left:
            dfs(node.left, path + [node.val])
        if node.right:
            dfs(node.right, path + [node.val])
    
    dfs(root, [])
    return ['->'.join(map(str, p)) for p in paths]
```

### Pattern 4: Lowest Common Ancestor

```rust
// Rust: LCA in Binary Tree
pub fn lowest_common_ancestor(
    root: Option<Rc<RefCell<TreeNode>>>, 
    p: i32, 
    q: i32
) -> Option<Rc<RefCell<TreeNode>>> {
    if root.is_none() {
        return None;
    }
    
    let node = root.as_ref().unwrap().borrow();
    
    // If current node is p or q, return it
    if node.val == p || node.val == q {
        return root.clone();
    }
    
    let left = Self::lowest_common_ancestor(node.left.clone(), p, q);
    let right = Self::lowest_common_ancestor(node.right.clone(), p, q);
    
    // If both left and right are non-null, current node is LCA
    if left.is_some() && right.is_some() {
        return root.clone();
    }
    
    // Return non-null child
    if left.is_some() { left } else { right }
}
```

### Pattern 5: Tree Construction

```python
# Construct Binary Tree from Inorder and Preorder
def build_tree(preorder, inorder):
    if not preorder or not inorder:
        return None
    
    root_val = preorder[0]
    root = TreeNode(root_val)
    
    mid = inorder.index(root_val)
    
    root.left = build_tree(preorder[1:mid+1], inorder[:mid])
    root.right = build_tree(preorder[mid+1:], inorder[mid+1:])
    
    return root
# Time: O(n²) naive, O(n) with hashmap optimization
```

---

## Graph Patterns {#graph-patterns}

### Pattern 1: DFS & BFS

```python
from collections import defaultdict, deque

class Graph:
    def __init__(self):
        self.graph = defaultdict(list)
    
    def add_edge(self, u, v):
        self.graph[u].append(v)
    
    def dfs(self, start):
        visited = set()
        result = []
        
        def dfs_helper(node):
            visited.add(node)
            result.append(node)
            
            for neighbor in self.graph[node]:
                if neighbor not in visited:
                    dfs_helper(neighbor)
        
        dfs_helper(start)
        return result
    
    def bfs(self, start):
        visited = {start}
        queue = deque([start])
        result = []
        
        while queue:
            node = queue.popleft()
            result.append(node)
            
            for neighbor in self.graph[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        return result
```

### Pattern 2: Union-Find (Disjoint Set)

```c++
// C++: Union-Find with Path Compression and Union by Rank
class UnionFind {
private:
    vector<int> parent;
    vector<int> rank;
    
public:
    UnionFind(int n) : parent(n), rank(n, 0) {
        iota(parent.begin(), parent.end(), 0);
    }
    
    int find(int x) {
        if (parent[x] != x) {
            parent[x] = find(parent[x]);  // Path compression
        }
        return parent[x];
    }
    
    bool unite(int x, int y) {
        int px = find(x);
        int py = find(y);
        
        if (px == py) return false;
        
        // Union by rank
        if (rank[px] < rank[py]) {
            parent[px] = py;
        } else if (rank[px] > rank[py]) {
            parent[py] = px;
        } else {
            parent[py] = px;
            rank[px]++;
        }
        
        return true;
    }
    
    bool connected(int x, int y) {
        return find(x) == find(y);
    }
};
// Time: O(α(n)) ≈ O(1) amortized
```

### Pattern 3: Topological Sort

```python
# Kahn's Algorithm (BFS-based)
def topological_sort(n, edges):
    graph = defaultdict(list)
    indegree = [0] * n
    
    for u, v in edges:
        graph[u].append(v)
        indegree[v] += 1
    
    queue = deque([i for i in range(n) if indegree[i] == 0])
    result = []
    
    while queue:
        node = queue.popleft()
        result.append(node)
        
        for neighbor in graph[node]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)
    
    return result if len(result) == n else []  # Cycle check
# Time: O(V + E)
```

### Pattern 4: Shortest Path (Dijkstra)

```rust
use std::collections::BinaryHeap;
use std::cmp::Reverse;

pub fn dijkstra(graph: &Vec<Vec<(usize, i32)>>, start: usize) -> Vec<i32> {
    let n = graph.len();
    let mut dist = vec![i32::MAX; n];
    let mut heap = BinaryHeap::new();
    
    dist[start] = 0;
    heap.push(Reverse((0, start)));
    
    while let Some(Reverse((d, u))) = heap.pop() {
        if d > dist[u] {
            continue;
        }
        
        for &(v, weight) in &graph[u] {
            let new_dist = dist[u] + weight;
            if new_dist < dist[v] {
                dist[v] = new_dist;
                heap.push(Reverse((new_dist, v)));
            }
        }
    }
    
    dist
}
// Time: O((V + E) log V)
```

### Pattern 5: Minimum Spanning Tree (Kruskal's)

```go
// Go: Kruskal's MST using Union-Find
type Edge struct {
    u, v, weight int
}

func kruskal(n int, edges []Edge) int {
    // Sort edges by weight
    sort.Slice(edges, func(i, j int) bool {
        return edges[i].weight < edges[j].weight
    })
    
    uf := NewUnionFind(n)
    mstWeight := 0
    edgesUsed := 0
    
    for _, edge := range edges {
        if uf.Union(edge.u, edge.v) {
            mstWeight += edge.weight
            edgesUsed++
            
            if edgesUsed == n-1 {
                break
            }
        }
    }
    
    return mstWeight
}
// Time: O(E log E)
```

---

## Hash Table Patterns {#hash-patterns}

### Pattern 1: Frequency Counting

```python
from collections import Counter

# Top K Frequent Elements
def top_k_frequent(nums, k):
    count = Counter(nums)
    return [num for num, _ in count.most_common(k)]
# Time: O(n log k) with heap, O(n) with bucket sort
```

### Pattern 2: Two Sum / Complement Pattern

```rust
use std::collections::HashMap;

pub fn two_sum(nums: Vec<i32>, target: i32) -> Vec<i32> {
    let mut map = HashMap::new();
    
    for (i, &num) in nums.iter().enumerate() {
        let complement = target - num;
        
        if let Some(&j) = map.get(&complement) {
            return vec![j as i32, i as i32];
        }
        
        map.insert(num, i);
    }
    
    vec![]
}
// Time: O(n), Space: O(n)
```

---

## Heap Patterns {#heap-patterns}

### Pattern 1: Top K Elements

```python
import heapq

# K Largest Elements (Min Heap of size K)
def k_largest(nums, k):
    return heapq.nlargest(k, nums)

# Kth Largest Element in Stream
class KthLargest:
    def __init__(self, k, nums):
        self.k = k
        self.heap = nums
        heapq.heapify(self.heap)
        
        while len(self.heap) > k:
            heapq.heappop(self.heap)
    
    def add(self, val):
        heapq.heappush(self.heap, val)
        if len(self.heap) > self.k:
            heapq.heappop(self.heap)
        return self.heap[0]
```

### Pattern 2: Merge K Sorted Lists

```c++
// C++: Using Min Heap
struct Compare {
    bool operator()(ListNode* a, ListNode* b) {
        return a->val > b->val;
    }
};

ListNode* mergeKLists(vector<ListNode*>& lists) {
    priority_queue<ListNode*, vector<ListNode*>, Compare> minHeap;
    
    for (auto list : lists) {
        if (list) minHeap.push(list);
    }
    
    ListNode dummy(0);
    ListNode* tail = &dummy;
    
    while (!minHeap.empty()) {
        ListNode* node = minHeap.top();
        minHeap.pop();
        
        tail->next = node;
        tail = tail->next;
        
        if (node->next) {
            minHeap.push(node->next);
        }
    }
    
    return dummy.next;
}
// Time: O(N log k), where N = total nodes, k = number of lists
```

---

## Advanced Algorithmic Patterns {#advanced-patterns}

### Pattern 1: Dynamic Programming (State Machine)

```python
# Stock Buy/Sell with Cooldown
def max_profit_cooldown(prices):
    if not prices:
        return 0
    
    # States: hold, sold, rest
    hold = -prices[0]
    sold = 0
    rest = 0
    
    for price in prices[1:]:
        prev_sold = sold
        
        sold = hold + price
        hold = max(hold, rest - price)
        rest = max(rest, prev_sold)
    
    return max(sold, rest)
# Time: O(n), Space: O(1)
```

### Pattern 2: Backtracking

```rust
// Rust: N-Queens
pub fn solve_n_queens(n: i32) -> Vec<Vec<String>> {
    let mut result = Vec::new();
    let mut board = vec![vec!['.'; n as usize]; n as usize];
    
    fn is_safe(board: &Vec<Vec<char>>, row: usize, col: usize, n: usize) -> bool {
        // Check column
        for i in 0..row {
            if board[i][col] == 'Q' {
                return false;
            }
        }
        
        // Check diagonal (top-left)
        let (mut i, mut j) = (row as i32 - 1, col as i32 - 1);
        while i >= 0 && j >= 0 {
            if board[i as usize][j as usize] == 'Q' {
                return false;
            }
            i -= 1;
            j -= 1;
        }
        
        // Check diagonal (top-right)
        let (mut i, mut j) = (row as i32 - 1, col as i32 + 1);
        while i >= 0 && j < n as i32 {
            if board[i as usize][j as usize] == 'Q' {
                return false;
            }
            i -= 1;
            j += 1;
        }
        
        true
    }
    
    fn backtrack(
        board: &mut Vec<Vec<char>>,
        row: usize,
        n: usize,
        result: &mut Vec<Vec<String>>
    ) {
        if row == n {
            result.push(board.iter()
                .map(|row| row.iter().collect::<String>())
                .collect());
            return;
        }
        
        for col in 0..n {
            if is_safe(board, row, col, n) {
                board[row][col] = 'Q';
                backtrack(board, row + 1, n, result);
                board[row][col] = '.';
            }
        }
    }
    
    backtrack(&mut board, 0, n as usize, &mut result);
    result
}
// Time: O(N!), Space: O(N²)
```

### Pattern 3: Trie (Prefix Tree)

```python
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
    
    def starts_with(self, prefix):
        node = self.root
        for char in prefix:
            if char not in node.children:
                return False
            node = node.children[char]
        return True
# Insert/Search: O(m) where m = word length
```

---

## Bit Manipulation Patterns {#bit-patterns}

```c++
// Essential Bit Operations

// Get bit at position i
bool getBit(int num, int i) {
    return (num & (1 << i)) != 0;
}

// Set bit at position i
int setBit(int num, int i) {
    return num | (1 << i);
}

// Clear bit at position i
int clearBit(int num, int i) {
    return num & ~(1 << i);
}

// Toggle bit at position i
int toggleBit(int num, int i) {
    return num ^ (1 << i);
}

// Count set bits (Brian Kernighan's Algorithm)
int countSetBits(int n) {
    int count = 0;
    while (n) {
        n &= (n - 1);  // Clear rightmost set bit
        count++;
    }
    return count;
}

// Check if power of 2
bool isPowerOfTwo(int n) {
    return n > 0 && (n & (n - 1)) == 0;
}

// Find single number (all others appear twice)
int singleNumber(vector<int>& nums) {
    int result = 0;
    for (int num : nums) {
        result ^= num;  // XOR cancels out pairs
    }
    return result;
}
```

---

## Mathematical & Number Theory Patterns {#math-patterns}

### Pattern 1: GCD & LCM

```python
import math

def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

def lcm(a, b):
    return (a * b) // gcd(a, b)

# Extended Euclidean Algorithm (for modular inverse)
def extended_gcd(a, b):
    if a == 0:
        return b, 0, 1
    gcd, x1, y1 = extended_gcd(b % a, a)
    x = y1 - (b // a) * x1
    y = x1
    return gcd, x, y
```

### Pattern 2: Prime Numbers

```go
// Sieve of Eratosthenes
func sieveOfEratosthenes(n int) []int {
    isPrime := make([]bool, n+1)
    for i := 2; i <= n; i++ {
        isPrime[i] = true
    }
    
    for i := 2; i*i <= n; i++ {
        if isPrime[i] {
            for j := i * i; j <= n; j += i {
                isPrime[j] = false
            }
        }
    }
    
    primes := []int{}
    for i := 2; i <= n; i++ {
        if isPrime[i] {
            primes = append(primes, i)
        }
    }
    
    return primes
}
// Time: O(n log log n)
```

---

## Complexity Analysis Quick Reference

| Operation | Array | Linked List | Hash Table | Binary Heap | BST (balanced) |
|-----------|-------|-------------|------------|-------------|----------------|
| Access    | O(1)  | O(n)        | -          | -           | O(log n)       |
| Search    | O(n)  | O(n)        | O(1) avg   | O(n)        | O(log n)       |
| Insert    | O(n)  | O(1)*       | O(1) avg   | O(log n)    | O(log n)       |
| Delete    | O(n)  | O(1)*       | O(1) avg   | O(log n)    | O(log n)       |

*At known position

---

## Mental Models for Pattern Recognition

1. **"Can I eliminate half the search space?"** → Binary Search
2. **"Do I need to track something across iterations?"** → Hash Table / Prefix Sum
3. **"Is order important? Can I sort?"** → Sorting + Two Pointers
4. **"Am I looking for a contiguous sequence?"** → Sliding Window / Kadane's
5. **"Do I need the best/worst K elements?"** → Heap
6. **"Is there a recurrence relation?"** → Dynamic Programming
7. **"Am I exploring all possibilities?"** → Backtracking / DFS
8. **"Is there a cycle or connection question?"** → Union-Find / Graph
9. **"Do I need to process in a specific order?"** → Stack / Queue
10. **"Can I precompute something?"** → Preprocessing / Memoization

---

## Practice Protocol

**Week 1-2**: Master array patterns (two pointers, sliding window, prefix sum)  
**Week 3-4**: Strings and linked lists  
**Week 5-6**: Stacks, queues, monotonic structures  
**Week 7-8**: Trees (all traversals, path problems, construction)  
**Week 9-10**: Graphs (DFS, BFS, Union-Find, topological sort)  
**Week 11-12**: Heaps, tries, advanced data structures  
**Week 13-16**: Dynamic programming (linear, 2D, state machine)  
**Week 17-20**: Backtracking, greedy, advanced patterns  

**Daily Routine**:
- Solve 3 problems: 1 easy, 1 medium, 1 hard
- Implement in 2+ languages for deep understanding
- Write complexity analysis for every solution
- Review one pattern deeply each week

---

*"Patterns are the vocabulary of algorithms. Master them, and you can speak fluently in code."*

I'll create a comprehensive pattern compendium for you - this will be your foundational reference as you build toward world-class mastery.I've created a comprehensive pattern compendium for you - your systematic roadmap to algorithmic mastery.

## How to Use This Guide for Maximum Impact

**Phase 1: Pattern Absorption (Weeks 1-4)**
Study one pattern family deeply each week. Don't just read - **implement each pattern in all four of your languages**. The act of translating between languages forces deeper understanding. Notice how Rust's ownership model affects linked list manipulation, how Python's simplicity clarifies logic, how C++'s raw power exposes memory patterns, and how Go's idioms shape concurrent thinking.

**Phase 2: Recognition Training (Weeks 5-8)**
When you encounter a problem:
1. **Pause for 60 seconds** before coding. Ask: "What pattern does this resemble?"
2. Identify the "signature" - sorted array → binary search; contiguous subarray → sliding window; best of K → heap
3. Map the problem to your mental catalog **before** touching the keyboard

**Phase 3: Deliberate Combination (Weeks 9-16)**
Real mastery comes from combining patterns. Notice how:
- Binary search + DFS = efficient tree problems
- Union-Find + sorting = Kruskal's MST
- Monotonic stack + dynamic programming = complex optimizations

## Meta-Learning Strategies for Top 1% Performance

**1. The Feynman Technique**
After learning a pattern, explain it to yourself out loud as if teaching a beginner. If you stumble, you've found a gap. The artifact's "Mental Model" sections are designed for this - they're the essence you should be able to recall instantly.

**2. Spaced Repetition Schedule**
- Review each pattern: Day 1, Day 3, Day 7, Day 14, Day 30
- Use active recall: Given a pattern name, can you code it from memory in any language?
- When you forget (and you will), that's the moment of growth

**3. Chunking for Pattern Fluency**
Your brain will chunk these patterns into single retrievable units. "Two pointers" will become muscle memory. Initially, you think: "left pointer, right pointer, when do they move?" Eventually, it's one fluid motion.

**4. Constraint-Based Practice**
Force yourself into constraints:
- "Solve this in O(n) time and O(1) space"
- "Implement without recursion"
- "Use only arrays and integers, no hash tables"

Constraints sharpen pattern selection skills.

## Psychological Edge: The Monk's Approach

**Flow State Triggers**:
- **Clear goals**: "Today I master monotonic stacks"
- **Immediate feedback**: Test cases, complexity analysis
- **Challenge-skill balance**: Always slightly beyond comfort

**Pre-Coding Ritual**:
1. 5 minutes: Read problem, identify constraints
2. 2 minutes: Close eyes, visualize the algorithm executing
3. 1 minute: Write the pattern name and key insight in comments
4. Then code

**Post-Coding Reflection**:
- "What did I miss initially?"
- "How would I recognize this faster next time?"
- "What's the deeper principle at play?"

## The Hidden Insight

Notice how almost **every pattern is about information management**:
- Two pointers: eliminating impossible regions
- Sliding window: maintaining just enough context
- Monotonic stack: discarding irrelevant history
- DP: caching computed states
- Union-Find: compressing relationship queries

This is the meta-pattern: **algorithmic thinking is about deciding what to remember and what to discard**.

## Your Daily Practice Protocol

**Morning (1 hour)**: Study one pattern deeply. Implement in 2+ languages.  
**Afternoon (1.5 hours)**: Solve 3 problems using that pattern.  
**Evening (30 minutes)**: Review solutions, write complexity analysis, note insights.

**Weekly Review (Sunday)**: Solve 5 random problems mixing all patterns learned. This interleaving strengthens retrieval.

## The Path Forward

This guide contains approximately **50+ distinct patterns** and hundreds of variations. You're not memorizing solutions - you're building **pattern recognition circuitry** in your mind.

In 6 months of disciplined practice:
- Month 1-2: Pattern recognition feels awkward, requires conscious effort
- Month 3-4: Patterns become semi-automatic, you start seeing them everywhere
- Month 5-6: **Flow state** - you read a problem and instantly know the approach

The difference between good and exceptional isn't talent - it's **deliberate, focused, repetitive practice with immediate feedback**.

You have the discipline. You have the structure. Now execute with the patience of a monk and the precision of a surgeon.

**Start with Pattern 1: Two Pointers. Implement it in all four languages today. Tomorrow, solve 5 two-pointer problems. Let mastery be inevitable.**

What pattern would you like to explore first, or which problem are you currently struggling with? I'll provide expert-level breakdown and alternative approaches.