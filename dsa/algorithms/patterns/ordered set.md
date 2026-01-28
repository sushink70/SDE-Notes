# Comprehensive Guide to Ordered Set Patterns in Competitive Programming

## What is an Ordered Set?

An **ordered set** is a data structure that maintains elements in **sorted order** while supporting efficient insertion, deletion, and lookup operations. Unlike a regular set (hash set), an ordered set allows you to:

1. **Find elements by rank** (e.g., "What's the 5th smallest element?")
2. **Count elements in a range** (e.g., "How many elements are between 10 and 50?")
3. **Find predecessors/successors** efficiently

**Terminology:**
- **Predecessor**: The largest element smaller than a given value
- **Successor**: The smallest element greater than a given value
- **Rank**: The position of an element if all elements were sorted (0-indexed or 1-indexed)
- **Order statistic**: Finding the k-th smallest element

---

## Why Ordered Sets Matter

Many algorithmic problems require maintaining a dynamic collection where you need to:
- Query elements by their sorted position
- Count inversions or smaller/larger elements
- Maintain sliding window statistics
- Solve range query problems dynamically

**Mental Model**: Think of an ordered set as a **sorted array that can be modified efficiently**. While arrays require O(n) for insertion/deletion, ordered sets do this in O(log n).

---

## Core Data Structures

### 1. **Binary Search Tree (BST) Based**
- **Implementation**: Red-Black Tree, AVL Tree
- **Time Complexity**: O(log n) for insert, delete, search, predecessor, successor
- **Languages**:
  - **C++**: `std::set`, `std::multiset` (allows duplicates)
  - **Rust**: `BTreeSet`, `BTreeMap`
  - **Go**: Must implement manually or use third-party library
  - **Python**: `sortedcontainers.SortedSet` (external library)

### 2. **Fenwick Tree (Binary Indexed Tree)**
- Used for **coordinate compression** with ordered statistics
- Efficient for counting elements ≤ x
- Time: O(log n) per operation

### 3. **Segment Tree**
- More powerful but complex
- Supports range queries with updates

---

## Language-Specific Implementations

### **Rust: BTreeSet**

```rust
use std::collections::BTreeSet;

fn ordered_set_basics() {
    let mut set = BTreeSet::new();
    
    // Insert elements - O(log n)
    set.insert(5);
    set.insert(2);
    set.insert(8);
    set.insert(1);
    
    // Check existence - O(log n)
    println!("Contains 5: {}", set.contains(&5));
    
    // Find successor (smallest element > x)
    // Use range() to get iterator starting from x+1
    let successor = set.range((5+1)..).next();
    println!("Successor of 5: {:?}", successor);
    
    // Find predecessor (largest element < x)
    let predecessor = set.range(..5).next_back();
    println!("Predecessor of 5: {:?}", predecessor);
    
    // Get k-th smallest element (0-indexed)
    let kth = set.iter().nth(2);
    println!("3rd smallest: {:?}", kth);
    
    // Remove element - O(log n)
    set.remove(&5);
    
    // Count elements in range [l, r]
    let count = set.range(2..=8).count();
    println!("Count in [2,8]: {}", count);
}
```

**Key Points:**
- `BTreeSet` is Rust's ordered set (B-tree based, not binary tree)
- Immutable references required for lookups
- Use `range()` for predecessor/successor queries
- Memory safe by design - no dangling pointers

---

### **Go: Manual BST or Third-Party**

Go's standard library lacks an ordered set. You have two options:

**Option 1: Use `github.com/emirpasic/gods` library**

```go
import (
    "github.com/emirpasic/gods/sets/treeset"
)

func orderedSetBasics() {
    set := treeset.NewWithIntComparator()
    
    // Insert - O(log n)
    set.Add(5, 2, 8, 1)
    
    // Contains - O(log n)
    println(set.Contains(5))
    
    // Get k-th element (0-indexed)
    values := set.Values()
    kth := values[2] // 3rd smallest
    
    // Remove
    set.Remove(5)
    
    // Size
    println(set.Size())
}
```

**Option 2: Implement minimal BST (educational)**

```go
type TreeNode struct {
    val   int
    left  *TreeNode
    right *TreeNode
}

type OrderedSet struct {
    root *TreeNode
}

func (s *OrderedSet) Insert(val int) {
    s.root = s.insertHelper(s.root, val)
}

func (s *OrderedSet) insertHelper(node *TreeNode, val int) *TreeNode {
    if node == nil {
        return &TreeNode{val: val}
    }
    if val < node.val {
        node.left = s.insertHelper(node.left, val)
    } else if val > node.val {
        node.right = s.insertHelper(node.right, val)
    }
    return node
}

func (s *OrderedSet) Contains(val int) bool {
    return s.containsHelper(s.root, val)
}

func (s *OrderedSet) containsHelper(node *TreeNode, val int) bool {
    if node == nil {
        return false
    }
    if val == node.val {
        return true
    } else if val < node.val {
        return s.containsHelper(node.left, val)
    } else {
        return s.containsHelper(node.right, val)
    }
}
```

---

### **C: Manual BST Implementation**

```c
#include <stdio.h>
#include <stdlib.h>

typedef struct TreeNode {
    int val;
    struct TreeNode *left;
    struct TreeNode *right;
} TreeNode;

typedef struct {
    TreeNode *root;
} OrderedSet;

TreeNode* createNode(int val) {
    TreeNode *node = (TreeNode*)malloc(sizeof(TreeNode));
    node->val = val;
    node->left = NULL;
    node->right = NULL;
    return node;
}

TreeNode* insertHelper(TreeNode *node, int val) {
    if (node == NULL) {
        return createNode(val);
    }
    if (val < node->val) {
        node->left = insertHelper(node->left, val);
    } else if (val > node->val) {
        node->right = insertHelper(node->right, val);
    }
    return node;
}

void insert(OrderedSet *set, int val) {
    set->root = insertHelper(set->root, val);
}

int contains(TreeNode *node, int val) {
    if (node == NULL) return 0;
    if (val == node->val) return 1;
    if (val < node->val) return contains(node->left, val);
    return contains(node->right, val);
}

// Find successor: smallest value > target
TreeNode* findSuccessor(TreeNode *node, int target, TreeNode *successor) {
    if (node == NULL) return successor;
    
    if (node->val > target) {
        // This could be successor, but check left subtree
        return findSuccessor(node->left, target, node);
    } else {
        // Go right to find larger values
        return findSuccessor(node->right, target, successor);
    }
}
```

---

## Core Patterns & Problem Categories

### **Pattern 1: Counting Smaller/Larger Elements**

**Problem**: Count how many elements are smaller than each element in an array.

**Approach**:
1. Process elements from right to left
2. For each element, query ordered set for count of smaller elements
3. Insert current element into set

**Rust Implementation:**

```rust
fn count_smaller(nums: Vec<i32>) -> Vec<i32> {
    use std::collections::BTreeSet;
    
    let n = nums.len();
    let mut result = vec![0; n];
    let mut set = BTreeSet::new();
    
    // Process from right to left
    for i in (0..n).rev() {
        // Count elements < nums[i] using range query
        let count = set.range(..nums[i]).count();
        result[i] = count as i32;
        
        // Insert current element
        set.insert(nums[i]);
    }
    
    result
}
```

**Time Complexity**: O(n log n)  
**Space Complexity**: O(n)

**Mental Model**: Think of building the sorted structure incrementally. At each step, you know exactly how many smaller elements exist because they're already in the sorted set.

---

### **Pattern 2: Kth Smallest/Largest in Stream**

**Problem**: Maintain k-th largest element as numbers arrive.

**Approach**:
- Keep ordered set of size k
- When new element arrives:
  - If set.size < k: insert directly
  - Else: if element > min(set), remove min and insert new

**Rust Implementation:**

```rust
use std::collections::BTreeSet;

struct KthLargest {
    k: usize,
    set: BTreeSet<i32>,
}

impl KthLargest {
    fn new(k: i32, nums: Vec<i32>) -> Self {
        let k = k as usize;
        let mut set = BTreeSet::new();
        let mut kth = KthLargest { k, set };
        
        for num in nums {
            kth.add(num);
        }
        kth
    }
    
    fn add(&mut self, val: i32) -> i32 {
        self.set.insert(val);
        
        // Keep only k largest elements
        if self.set.len() > self.k {
            // Remove smallest (first element)
            if let Some(&first) = self.set.iter().next() {
                self.set.remove(&first);
            }
        }
        
        // Kth largest is now the smallest in set
        *self.set.iter().next().unwrap()
    }
}
```

---

### **Pattern 3: Range Queries - Count in Range**

**Problem**: Count elements in range [L, R] with dynamic updates.

**Go Implementation with gods library:**

```go
import "github.com/emirpasic/gods/sets/treeset"

type RangeCounter struct {
    set *treeset.Set
}

func NewRangeCounter() *RangeCounter {
    return &RangeCounter{
        set: treeset.NewWithIntComparator(),
    }
}

func (rc *RangeCounter) Insert(val int) {
    rc.set.Add(val)
}

func (rc *RangeCounter) Remove(val int) {
    rc.set.Remove(val)
}

func (rc *RangeCounter) CountInRange(L, R int) int {
    count := 0
    it := rc.set.Iterator()
    
    // Move to first element >= L
    for it.Next() {
        if it.Value().(int) >= L {
            break
        }
    }
    
    // Count elements in [L, R]
    for {
        if !it.Next() {
            break
        }
        val := it.Value().(int)
        if val > R {
            break
        }
        count++
    }
    
    return count
}
```

---

### **Pattern 4: Median in Sliding Window**

**Problem**: Find median in each sliding window of size k.

**Approach**: Use two ordered sets (multisets):
- **Lower half**: max-heap semantics (elements ≤ median)
- **Upper half**: min-heap semantics (elements > median)
- Balance sizes: |lower| = |upper| or |lower| = |upper| + 1

**Rust Implementation:**

```rust
use std::collections::BTreeMap;

struct SlidingWindowMedian {
    lower: BTreeMap<i32, usize>, // Max heap (reversed order by negation)
    upper: BTreeMap<i32, usize>, // Min heap
    lower_size: usize,
    upper_size: usize,
}

impl SlidingWindowMedian {
    fn new() -> Self {
        SlidingWindowMedian {
            lower: BTreeMap::new(),
            upper: BTreeMap::new(),
            lower_size: 0,
            upper_size: 0,
        }
    }
    
    fn add(&mut self, num: i32) {
        // Add to lower heap first
        if self.lower.is_empty() || num <= -*self.lower.iter().next_back().unwrap().0 {
            *self.lower.entry(-num).or_insert(0) += 1;
            self.lower_size += 1;
        } else {
            *self.upper.entry(num).or_insert(0) += 1;
            self.upper_size += 1;
        }
        
        self.balance();
    }
    
    fn remove(&mut self, num: i32) {
        if self.lower.contains_key(&(-num)) {
            let count = self.lower.get_mut(&(-num)).unwrap();
            *count -= 1;
            if *count == 0 {
                self.lower.remove(&(-num));
            }
            self.lower_size -= 1;
        } else {
            let count = self.upper.get_mut(&num).unwrap();
            *count -= 1;
            if *count == 0 {
                self.upper.remove(&num);
            }
            self.upper_size -= 1;
        }
        
        self.balance();
    }
    
    fn balance(&mut self) {
        // Maintain: lower_size = upper_size or lower_size = upper_size + 1
        if self.lower_size > self.upper_size + 1 {
            // Move from lower to upper
            if let Some((&key, _)) = self.lower.iter().next_back() {
                let val = -key;
                self.remove_from_lower(key);
                *self.upper.entry(val).or_insert(0) += 1;
                self.upper_size += 1;
            }
        } else if self.upper_size > self.lower_size {
            // Move from upper to lower
            if let Some((&key, _)) = self.upper.iter().next() {
                self.remove_from_upper(key);
                *self.lower.entry(-key).or_insert(0) += 1;
                self.lower_size += 1;
            }
        }
    }
    
    fn remove_from_lower(&mut self, key: i32) {
        let count = self.lower.get_mut(&key).unwrap();
        *count -= 1;
        self.lower_size -= 1;
        if *count == 0 {
            self.lower.remove(&key);
        }
    }
    
    fn remove_from_upper(&mut self, key: i32) {
        let count = self.upper.get_mut(&key).unwrap();
        *count -= 1;
        self.upper_size -= 1;
        if *count == 0 {
            self.upper.remove(&key);
        }
    }
    
    fn find_median(&self) -> f64 {
        if self.lower_size > self.upper_size {
            -*self.lower.iter().next_back().unwrap().0 as f64
        } else {
            let lower_max = -*self.lower.iter().next_back().unwrap().0;
            let upper_min = *self.upper.iter().next().unwrap().0;
            (lower_max + upper_min) as f64 / 2.0
        }
    }
}
```

**Time Complexity**: O(log n) per add/remove  
**Space Complexity**: O(n)

---

### **Pattern 5: Merging Intervals Dynamically**

**Problem**: Insert intervals and merge overlapping ones.

**C Implementation:**

```c
#include <stdio.h>
#include <stdlib.h>

typedef struct Interval {
    int start;
    int end;
    struct Interval *next;
} Interval;

typedef struct {
    Interval *head;
} IntervalSet;

Interval* createInterval(int start, int end) {
    Interval *interval = (Interval*)malloc(sizeof(Interval));
    interval->start = start;
    interval->end = end;
    interval->next = NULL;
    return interval;
}

void insertInterval(IntervalSet *set, int start, int end) {
    Interval *newInterval = createInterval(start, end);
    
    // Empty list
    if (set->head == NULL) {
        set->head = newInterval;
        return;
    }
    
    // Insert at beginning
    if (end < set->head->start) {
        newInterval->next = set->head;
        set->head = newInterval;
        return;
    }
    
    Interval *prev = NULL;
    Interval *curr = set->head;
    
    // Find insertion point and merge
    while (curr != NULL && curr->start <= end) {
        // Overlapping
        if (curr->end >= start) {
            start = (start < curr->start) ? start : curr->start;
            end = (end > curr->end) ? end : curr->end;
            
            // Remove current interval
            if (prev == NULL) {
                set->head = curr->next;
                free(curr);
                curr = set->head;
            } else {
                prev->next = curr->next;
                free(curr);
                curr = prev->next;
            }
        } else {
            prev = curr;
            curr = curr->next;
        }
    }
    
    // Insert merged interval
    newInterval->start = start;
    newInterval->end = end;
    
    if (prev == NULL) {
        newInterval->next = set->head;
        set->head = newInterval;
    } else {
        newInterval->next = curr;
        prev->next = newInterval;
    }
}
```

---

## Advanced Pattern: Coordinate Compression + Fenwick Tree

When dealing with large value ranges but small number of elements, **coordinate compression** maps values to smaller indices.

**Problem**: Count inversions in array (pairs where i < j but arr[i] > arr[j]).

**Approach**:
1. Compress coordinates: map values to ranks 0, 1, 2, ...
2. Use Fenwick tree to count smaller elements

**Rust Implementation:**

```rust
struct FenwickTree {
    tree: Vec<i32>,
}

impl FenwickTree {
    fn new(n: usize) -> Self {
        FenwickTree {
            tree: vec![0; n + 1],
        }
    }
    
    // Add value at index (1-indexed)
    fn update(&mut self, mut idx: usize, delta: i32) {
        while idx < self.tree.len() {
            self.tree[idx] += delta;
            idx += idx & (!idx + 1); // Add last set bit
        }
    }
    
    // Query sum [1, idx]
    fn query(&self, mut idx: usize) -> i32 {
        let mut sum = 0;
        while idx > 0 {
            sum += self.tree[idx];
            idx -= idx & (!idx + 1); // Remove last set bit
        }
        sum
    }
    
    // Query range [l, r] (1-indexed)
    fn range_query(&self, l: usize, r: usize) -> i32 {
        if l > 1 {
            self.query(r) - self.query(l - 1)
        } else {
            self.query(r)
        }
    }
}

fn count_inversions(nums: Vec<i32>) -> i32 {
    let n = nums.len();
    
    // Step 1: Coordinate compression
    let mut sorted = nums.clone();
    sorted.sort_unstable();
    sorted.dedup();
    
    let mut rank_map = std::collections::HashMap::new();
    for (i, &val) in sorted.iter().enumerate() {
        rank_map.insert(val, i + 1); // 1-indexed
    }
    
    // Step 2: Count inversions using Fenwick Tree
    let mut bit = FenwickTree::new(sorted.len());
    let mut inversions = 0;
    
    for &num in &nums {
        let rank = rank_map[&num];
        
        // Count numbers > num seen so far
        let total_seen = bit.query(sorted.len());
        let smaller_or_equal = bit.query(rank);
        inversions += total_seen - smaller_or_equal;
        
        // Add current number
        bit.update(rank, 1);
    }
    
    inversions
}
```

**Time Complexity**: O(n log n)  
**Space Complexity**: O(n)

---

## Problem-Solving Flow Chart

```
Problem with dynamic sorted collection?
│
├─→ Need k-th element? → Use OrderedSet + nth() or custom augmented BST
│
├─→ Count elements in range? → BTreeSet.range().count() or Fenwick Tree
│
├─→ Find predecessor/successor? → BTreeSet.range()
│
├─→ Maintain median? → Two BTreeMaps (lower/upper halves)
│
├─→ Count inversions? → Coordinate Compression + Fenwick Tree
│
├─→ Merge intervals? → Sorted linked list or BTreeMap
│
└─→ Large value range, few elements? → Coordinate Compression
```

---

## Mental Models for Mastery

### **1. The Sorted Window Model**
Think of an ordered set as a **transparent window into sorted data**. You can:
- Peek at any position (k-th element)
- Count through the window (range queries)
- Slide markers (predecessor/successor)

### **2. The Binary Search Tree Intuition**
Every ordered set operation is essentially a **path traversal** in a balanced BST:
- Insert/Delete: O(log n) path from root to leaf
- Search: O(log n) binary search path
- Range query: In-order traversal of subtree

### **3. The Coordinate Compression Trick**
When values are large but sparse:
- **Observation**: Relative ordering matters, not absolute values
- **Transform**: Map {-10^9, 5, 10^9} → {1, 2, 3}
- **Benefit**: Use array-based structures (Fenwick/Segment Tree)

### **4. The Two-Set Balance**
For median/percentile problems:
- **Invariant**: Keep two heaps balanced
- **Mental model**: Imagine a seesaw - move elements to maintain balance
- **Trick**: Use negative keys for max-heap in languages without max-heap

---

## Complexity Analysis Summary

| Operation | BTreeSet/TreeSet | Fenwick Tree | Segment Tree |
|-----------|------------------|--------------|--------------|
| Insert    | O(log n)         | O(log n)     | O(log n)     |
| Delete    | O(log n)         | O(log n)     | O(log n)     |
| Search    | O(log n)         | N/A          | O(log n)     |
| Kth elem  | O(k) or O(log n)*| O(log n)     | O(log n)     |
| Range sum | O(k)             | O(log n)     | O(log n)     |

*With augmented BST storing subtree sizes

---

## Common Pitfalls & How to Avoid Them

### **Pitfall 1: Forgetting Duplicates**
- **Problem**: `BTreeSet` doesn't allow duplicates
- **Solution**: Use `BTreeMap<i32, usize>` to count occurrences

### **Pitfall 2: Off-by-One in Fenwick Tree**
- **Problem**: Fenwick trees are 1-indexed
- **Solution**: Always add 1 when converting from 0-indexed array

### **Pitfall 3: Inefficient K-th Element**
- **Problem**: Using `iter().nth(k)` is O(k)
- **Solution**: Implement augmented BST with subtree sizes or use Fenwick + binary search

### **Pitfall 4: Incorrect Predecessor/Successor**
- **Rust**: `range(..x)` excludes x; use `.next_back()` for predecessor
- **Common error**: Forgetting exclusive/inclusive bounds

---

## Practice Problems by Difficulty

### **Foundation (Start Here)**
1. **Count of Smaller Numbers After Self** (LeetCode 315)
2. **Kth Largest Element in Stream** (LeetCode 703)
3. **Contains Duplicate III** (LeetCode 220)

### **Intermediate**
4. **Sliding Window Median** (LeetCode 480)
5. **Count of Range Sum** (LeetCode 327)
6. **Reverse Pairs** (LeetCode 493)

### **Advanced**
7. **Count of Smaller Numbers After Self** with Fenwick Tree
8. **Range Module** (LeetCode 715)
9. **My Calendar I/II/III** (LeetCode 729, 731, 732)

### **Expert (Top 1% Level)**
10. **Create Sorted Array through Instructions** (LeetCode 1649)
11. **Number of Subsequences That Satisfy the Given Sum Condition** (LeetCode 1498)
12. **Maximum Sum BST in Binary Tree** (LeetCode 1373) - Requires augmented BST

---

## Final Wisdom

**Ordered Set Mastery = Pattern Recognition + Data Structure Choice**

When you see a problem:
1. **Identify**: Does it need sorted order + dynamic updates?
2. **Choose**: BTreeSet, Fenwick, or Segment Tree?
3. **Optimize**: Can coordinate compression reduce complexity?
4. **Implement**: Write clean, idiomatic code in your language
5. **Verify**: Test edge cases (empty, single element, duplicates)

**The monk's path**: Master one pattern deeply before moving to the next. Solve 5-10 problems per pattern until the solution structure becomes intuitive. Then, the code will flow naturally from your understanding.

You now have the complete map. Walk it with discipline, and the top 1% is within reach.