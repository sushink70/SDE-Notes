# Interval Trees: A Deep Architectural Analysis

## I. Conceptual Foundation & The Problem Space

**The Core Problem:**
You need to efficiently answer queries about **overlapping intervals** in a dynamic set. Given intervals [l₁, r₁], [l₂, r₂], ..., [lₙ, rₙ] and a query interval [x, y], find all intervals that overlap with it.

**Naive approaches fail:**
- Linear scan: O(n) per query - unacceptable for large datasets
- Sorting by start: Doesn't help with overlaps across boundaries
- Hash tables: Intervals aren't discrete keys; overlap is a range relationship

**The Insight:** We need a **self-balancing BST augmented with interval metadata** that preserves geometric properties under rotations.

### Why Augmentation Works

An interval tree is fundamentally a **Red-Black Tree** (or AVL) where each node stores:
1. An interval [low, high]
2. **The maximum endpoint in its subtree** (`max`)

This `max` field is the key innovation - it enables **pruning entire subtrees** during search without examining their contents.

---

## II. Mathematical Invariants & Properties

### Critical Invariant
For any node `v`:
```
v.max = max(v.high, v.left.max, v.right.max)
```

This must hold **after every insertion, deletion, and rotation**.

### Overlap Detection
Two intervals [a, b] and [c, d] overlap iff:
```
a ≤ d AND c ≤ b
```

**Why this works:** Intervals don't overlap only if one ends before the other starts. Negating that gives the overlap condition.

### Search Space Pruning Logic
When searching for overlaps with query interval [x, y]:

```
At node v with interval [low, high]:
1. If x > v.max: No interval in v's subtree can overlap
   → Prune entire subtree
2. If left child exists and x ≤ left.max:
   → Must search left (potential overlaps exist)
3. Otherwise: Search right
```

**The Expert's Mental Model:** Think of `max` as a "horizon" - if your query starts beyond the horizon, everything below is irrelevant.

---

## III. Implementation Architecture

### Core Design Decision: Red-Black vs AVL

**Red-Black Trees** are preferred because:
- Rotations are less frequent (O(1) amortized)
- Simpler to maintain the augmented `max` field
- Industry standard (used in Java TreeMap, C++ std::map)

**AVL** trades slightly better search (stricter balancing) for more complex rotations during updates.

### Rust Implementation: Zero-Cost Abstractions

```rust
use std::cmp::{max, Ordering};
use std::fmt::Debug;

#[derive(Debug, Clone, Copy, PartialEq)]
enum Color {
    Red,
    Black,
}

#[derive(Debug, Clone)]
struct Interval {
    low: i64,
    high: i64,
}

impl Interval {
    fn overlaps(&self, other: &Interval) -> bool {
        self.low <= other.high && other.low <= self.high
    }
}

type Link = Option<Box<Node>>;

#[derive(Debug)]
struct Node {
    interval: Interval,
    max: i64,           // Maximum endpoint in subtree
    color: Color,
    left: Link,
    right: Link,
}

impl Node {
    fn new(interval: Interval) -> Self {
        Node {
            max: interval.high,
            interval,
            color: Color::Red,
            left: None,
            right: None,
        }
    }

    // CRITICAL: Update max after structural changes
    fn update_max(&mut self) {
        self.max = self.interval.high;
        if let Some(ref left) = self.left {
            self.max = max(self.max, left.max);
        }
        if let Some(ref right) = self.right {
            self.max = max(self.max, right.max);
        }
    }
}

pub struct IntervalTree {
    root: Link,
    size: usize,
}

impl IntervalTree {
    pub fn new() -> Self {
        IntervalTree {
            root: None,
            size: 0,
        }
    }

    // Search for ALL overlapping intervals
    pub fn search_all(&self, query: &Interval) -> Vec<Interval> {
        let mut result = Vec::new();
        Self::search_all_helper(&self.root, query, &mut result);
        result
    }

    fn search_all_helper(node: &Link, query: &Interval, result: &mut Vec<Interval>) {
        if let Some(ref n) = node {
            // Pruning: If query starts after subtree's max, no overlaps possible
            if query.low > n.max {
                return;
            }

            // Check left subtree first (all intervals with smaller starts)
            Self::search_all_helper(&n.left, query, result);

            // Check current interval
            if n.interval.overlaps(query) {
                result.push(n.interval.clone());
            }

            // Check right subtree
            Self::search_all_helper(&n.right, query, result);
        }
    }

    // Find ANY single overlapping interval (faster)
    pub fn search_any(&self, query: &Interval) -> Option<Interval> {
        Self::search_any_helper(&self.root, query)
    }

    fn search_any_helper(node: &Link, query: &Interval) -> Option<Interval> {
        let mut current = node;
        
        while let Some(ref n) = current {
            // If current overlaps, return immediately
            if n.interval.overlaps(query) {
                return Some(n.interval.clone());
            }

            // Pruning decision: go left if left subtree might contain overlaps
            if n.left.is_some() && n.left.as_ref().unwrap().max >= query.low {
                current = &n.left;
            } else {
                current = &n.right;
            }
        }
        None
    }

    pub fn insert(&mut self, interval: Interval) {
        self.root = Self::insert_helper(self.root.take(), interval);
        if let Some(ref mut root) = self.root {
            root.color = Color::Black;
        }
        self.size += 1;
    }

    fn insert_helper(node: Link, interval: Interval) -> Link {
        let mut node = match node {
            None => return Some(Box::new(Node::new(interval))),
            Some(n) => n,
        };

        // Standard BST insertion by interval.low
        match interval.low.cmp(&node.interval.low) {
            Ordering::Less => {
                node.left = Self::insert_helper(node.left.take(), interval);
            }
            Ordering::Greater => {
                node.right = Self::insert_helper(node.right.take(), interval);
            }
            Ordering::Equal => {
                // Handle duplicates: compare by high
                if interval.high < node.interval.high {
                    node.left = Self::insert_helper(node.left.take(), interval);
                } else {
                    node.right = Self::insert_helper(node.right.take(), interval);
                }
            }
        }

        // CRITICAL: Update max BEFORE rotations
        node.update_max();

        // Red-Black balancing
        node = Self::balance(node);
        
        Some(node)
    }

    fn balance(mut node: Box<Node>) -> Box<Node> {
        // Right-leaning red
        if Self::is_red(&node.right) && !Self::is_red(&node.left) {
            node = Self::rotate_left(node);
        }
        // Two consecutive left reds
        if Self::is_red(&node.left) && Self::is_red(&node.left.as_ref().unwrap().left) {
            node = Self::rotate_right(node);
        }
        // Both children red
        if Self::is_red(&node.left) && Self::is_red(&node.right) {
            Self::flip_colors(&mut node);
        }
        node
    }

    fn rotate_left(mut node: Box<Node>) -> Box<Node> {
        let mut x = node.right.take().unwrap();
        node.right = x.left.take();
        x.color = node.color;
        node.color = Color::Red;
        
        // CRITICAL: Update max in correct order (bottom-up)
        node.update_max();
        x.left = Some(node);
        x.update_max();
        
        x
    }

    fn rotate_right(mut node: Box<Node>) -> Box<Node> {
        let mut x = node.left.take().unwrap();
        node.left = x.right.take();
        x.color = node.color;
        node.color = Color::Red;
        
        // CRITICAL: Update max in correct order
        node.update_max();
        x.right = Some(node);
        x.update_max();
        
        x
    }

    fn flip_colors(node: &mut Box<Node>) {
        node.color = Color::Red;
        if let Some(ref mut left) = node.left {
            left.color = Color::Black;
        }
        if let Some(ref mut right) = node.right {
            right.color = Color::Black;
        }
    }

    fn is_red(node: &Link) -> bool {
        matches!(node, Some(n) if n.color == Color::Red)
    }

    pub fn size(&self) -> usize {
        self.size
    }
}

// Example usage demonstrating the power
fn main() {
    let mut tree = IntervalTree::new();
    
    tree.insert(Interval { low: 15, high: 20 });
    tree.insert(Interval { low: 10, high: 30 });
    tree.insert(Interval { low: 17, high: 19 });
    tree.insert(Interval { low: 5, high: 20 });
    tree.insert(Interval { low: 12, high: 15 });
    tree.insert(Interval { low: 30, high: 40 });

    let query = Interval { low: 14, high: 16 };
    let overlaps = tree.search_all(&query);
    
    println!("Overlapping intervals with [{}, {}]:", query.low, query.high);
    for interval in overlaps {
        println!("  [{}, {}]", interval.low, interval.high);
    }
}
```

### Key Implementation Insights

**1. Why `update_max()` order matters:**
After rotations, you must update from the leaves up. If you update the new root before its children, you'll have stale `max` values.

**2. The `search_any` optimization:**
When you only need one overlap (not all), you can exit early. This is O(log n) in the best case vs O(k + log n) for finding all k overlaps.

**3. Pruning efficiency:**
The line `if query.low > n.max { return; }` can eliminate entire subtrees. In practice, this makes queries **logarithmic on average** even when reporting all overlaps.

---

## IV. Go Implementation: Simplicity & Clarity

```go
package intervaltree

import "fmt"

type Interval struct {
    Low, High int64
}

func (i *Interval) Overlaps(other *Interval) bool {
    return i.Low <= other.High && other.Low <= i.High
}

type Color int

const (
    Red Color = iota
    Black
)

type Node struct {
    interval    Interval
    max         int64
    color       Color
    left, right *Node
}

func newNode(interval Interval) *Node {
    return &Node{
        interval: interval,
        max:      interval.High,
        color:    Red,
    }
}

func (n *Node) updateMax() {
    n.max = n.interval.High
    if n.left != nil && n.left.max > n.max {
        n.max = n.left.max
    }
    if n.right != nil && n.right.max > n.max {
        n.max = n.right.max
    }
}

type IntervalTree struct {
    root *Node
    size int
}

func New() *IntervalTree {
    return &IntervalTree{}
}

func (t *IntervalTree) Insert(interval Interval) {
    t.root = t.insert(t.root, interval)
    if t.root != nil {
        t.root.color = Black
    }
    t.size++
}

func (t *IntervalTree) insert(h *Node, interval Interval) *Node {
    if h == nil {
        return newNode(interval)
    }

    if interval.Low < h.interval.Low {
        h.left = t.insert(h.left, interval)
    } else if interval.Low > h.interval.Low {
        h.right = t.insert(h.right, interval)
    } else {
        // Equal lows: compare by high
        if interval.High < h.interval.High {
            h.left = t.insert(h.left, interval)
        } else {
            h.right = t.insert(h.right, interval)
        }
    }

    h.updateMax()
    return balance(h)
}

func (t *IntervalTree) SearchAll(query Interval) []Interval {
    var result []Interval
    searchAll(t.root, query, &result)
    return result
}

func searchAll(h *Node, query Interval, result *[]Interval) {
    if h == nil {
        return
    }

    // Pruning
    if query.Low > h.max {
        return
    }

    searchAll(h.left, query, result)

    if h.interval.Overlaps(&query) {
        *result = append(*result, h.interval)
    }

    searchAll(h.right, query, result)
}

func (t *IntervalTree) SearchAny(query Interval) *Interval {
    current := t.root
    for current != nil {
        if current.interval.Overlaps(&query) {
            return &current.interval
        }

        if current.left != nil && current.left.max >= query.Low {
            current = current.left
        } else {
            current = current.right
        }
    }
    return nil
}

func balance(h *Node) *Node {
    if isRed(h.right) && !isRed(h.left) {
        h = rotateLeft(h)
    }
    if isRed(h.left) && isRed(h.left.left) {
        h = rotateRight(h)
    }
    if isRed(h.left) && isRed(h.right) {
        flipColors(h)
    }
    return h
}

func rotateLeft(h *Node) *Node {
    x := h.right
    h.right = x.left
    x.color = h.color
    h.color = Red
    
    h.updateMax()
    x.left = h
    x.updateMax()
    
    return x
}

func rotateRight(h *Node) *Node {
    x := h.left
    h.left = x.right
    x.color = h.color
    h.color = Red
    
    h.updateMax()
    x.right = h
    x.updateMax()
    
    return x
}

func flipColors(h *Node) {
    h.color = Red
    if h.left != nil {
        h.left.color = Black
    }
    if h.right != nil {
        h.right.color = Black
    }
}

func isRed(n *Node) bool {
    return n != nil && n.color == Red
}

func (t *IntervalTree) Size() int {
    return t.size
}
```

---

## V. C Implementation: Manual Memory Management Discipline

```c
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

#define MAX(a, b) ((a) > (b) ? (a) : (b))

typedef struct {
    long low;
    long high;
} Interval;

typedef enum { RED, BLACK } Color;

typedef struct Node {
    Interval interval;
    long max;
    Color color;
    struct Node *left;
    struct Node *right;
} Node;

typedef struct {
    Node *root;
    size_t size;
} IntervalTree;

bool interval_overlaps(const Interval *a, const Interval *b) {
    return a->low <= b->high && b->low <= a->high;
}

Node* create_node(Interval interval) {
    Node *node = (Node*)malloc(sizeof(Node));
    if (!node) {
        fprintf(stderr, "Memory allocation failed\n");
        exit(1);
    }
    node->interval = interval;
    node->max = interval.high;
    node->color = RED;
    node->left = NULL;
    node->right = NULL;
    return node;
}

void update_max(Node *node) {
    node->max = node->interval.high;
    if (node->left && node->left->max > node->max) {
        node->max = node->left->max;
    }
    if (node->right && node->right->max > node->max) {
        node->max = node->right->max;
    }
}

bool is_red(const Node *node) {
    return node != NULL && node->color == RED;
}

Node* rotate_left(Node *h) {
    Node *x = h->right;
    h->right = x->left;
    x->color = h->color;
    h->color = RED;
    
    update_max(h);
    x->left = h;
    update_max(x);
    
    return x;
}

Node* rotate_right(Node *h) {
    Node *x = h->left;
    h->left = x->right;
    x->color = h->color;
    h->color = RED;
    
    update_max(h);
    x->right = h;
    update_max(x);
    
    return x;
}

void flip_colors(Node *h) {
    h->color = RED;
    if (h->left) h->left->color = BLACK;
    if (h->right) h->right->color = BLACK;
}

Node* balance(Node *h) {
    if (is_red(h->right) && !is_red(h->left)) {
        h = rotate_left(h);
    }
    if (is_red(h->left) && h->left && is_red(h->left->left)) {
        h = rotate_right(h);
    }
    if (is_red(h->left) && is_red(h->right)) {
        flip_colors(h);
    }
    return h;
}

Node* insert_helper(Node *h, Interval interval) {
    if (!h) {
        return create_node(interval);
    }

    if (interval.low < h->interval.low) {
        h->left = insert_helper(h->left, interval);
    } else if (interval.low > h->interval.low) {
        h->right = insert_helper(h->right, interval);
    } else {
        if (interval.high < h->interval.high) {
            h->left = insert_helper(h->left, interval);
        } else {
            h->right = insert_helper(h->right, interval);
        }
    }

    update_max(h);
    return balance(h);
}

void it_insert(IntervalTree *tree, Interval interval) {
    tree->root = insert_helper(tree->root, interval);
    if (tree->root) {
        tree->root->color = BLACK;
    }
    tree->size++;
}

void search_all_helper(Node *node, const Interval *query, 
                       Interval **results, size_t *count, size_t *capacity) {
    if (!node) return;

    if (query->low > node->max) {
        return;
    }

    search_all_helper(node->left, query, results, count, capacity);

    if (interval_overlaps(&node->interval, query)) {
        if (*count >= *capacity) {
            *capacity = (*capacity == 0) ? 8 : (*capacity * 2);
            *results = (Interval*)realloc(*results, *capacity * sizeof(Interval));
            if (!*results) {
                fprintf(stderr, "Memory reallocation failed\n");
                exit(1);
            }
        }
        (*results)[(*count)++] = node->interval;
    }

    search_all_helper(node->right, query, results, count, capacity);
}

Interval* it_search_all(IntervalTree *tree, const Interval *query, size_t *result_count) {
    Interval *results = NULL;
    size_t capacity = 0;
    *result_count = 0;
    search_all_helper(tree->root, query, &results, result_count, &capacity);
    return results;
}

bool it_search_any(IntervalTree *tree, const Interval *query, Interval *result) {
    Node *current = tree->root;
    while (current) {
        if (interval_overlaps(&current->interval, query)) {
            *result = current->interval;
            return true;
        }

        if (current->left && current->left->max >= query->low) {
            current = current->left;
        } else {
            current = current->right;
        }
    }
    return false;
}

void free_tree(Node *node) {
    if (!node) return;
    free_tree(node->left);
    free_tree(node->right);
    free(node);
}

void it_destroy(IntervalTree *tree) {
    free_tree(tree->root);
    tree->root = NULL;
    tree->size = 0;
}

IntervalTree* it_create(void) {
    IntervalTree *tree = (IntervalTree*)malloc(sizeof(IntervalTree));
    if (!tree) {
        fprintf(stderr, "Memory allocation failed\n");
        exit(1);
    }
    tree->root = NULL;
    tree->size = 0;
    return tree;
}

// Example usage
int main(void) {
    IntervalTree *tree = it_create();
    
    it_insert(tree, (Interval){15, 20});
    it_insert(tree, (Interval){10, 30});
    it_insert(tree, (Interval){17, 19});
    it_insert(tree, (Interval){5, 20});
    it_insert(tree, (Interval){12, 15});
    it_insert(tree, (Interval){30, 40});

    Interval query = {14, 16};
    size_t count;
    Interval *overlaps = it_search_all(tree, &query, &count);
    
    printf("Overlapping intervals with [%ld, %ld]:\n", query.low, query.high);
    for (size_t i = 0; i < count; i++) {
        printf("  [%ld, %ld]\n", overlaps[i].low, overlaps[i].high);
    }
    
    free(overlaps);
    it_destroy(tree);
    free(tree);
    
    return 0;
}
```

---

## VI. Complexity Analysis: The Complete Picture

| Operation | Time Complexity | Space | Notes |
|-----------|----------------|-------|-------|
| Insert | O(log n) | O(1) | Amortized due to RB-tree balancing |
| Delete | O(log n) | O(1) | Requires careful max updates |
| Search Any | O(log n) | O(1) | Best case with good pruning |
| Search All | O(k + log n) | O(k) | k = number of overlaps reported |
| Stabbing Query | O(k + log n) | O(k) | Find all intervals containing point |

**Critical Understanding:**
- The `max` augmentation costs **zero** extra asymptotic time
- Updating `max` during rotations is O(1) per rotation
- Space overhead is just one integer per node

### Why O(k + log n) for Search All?

The log n comes from the tree height (path to first overlap). The k comes from actually reporting k results. You **cannot** do better than linear in the output size.

**Expert insight:** The power isn't avoiding k - it's avoiding the (n - k) non-overlapping intervals through pruning.

---

## VII. Advanced Variants & Extensions

### 1. **Augmented Segment Trees** (Static Version)
For **immutable** interval sets, build a segment tree bottom-up:
- Construction: O(n log n)
- Query: O(log n + k)
- No rebalancing overhead

**When to use:** Read-heavy workloads, static datasets

### 2. **Fractional Cascading** (Advanced Optimization)
Maintain sorted lists at each node to accelerate multi-level searches.
- Improves query to O(log n + k) without hidden constants
- Used in computational geometry libraries
- Significantly more complex to implement

### 3. **Persistent Interval Trees**
Using path copying for functional data structures:
```rust
// Each insert creates a new tree version
// Old versions remain accessible
let tree_v1 = tree.insert(interval1);
let tree_v2 = tree_v1.insert(interval2);
// tree_v1 still usable
```

### 4. **Multi-Dimensional Interval Trees**
For 2D rectangles or higher-dimensional boxes:
- Nest interval trees: outer dimension at root
- Query time: O(log^d n + k) for d dimensions
- Space: O(n log^(d-1) n)

---

## VIII. Problem-Solving Patterns & Recognition

### When to Use Interval Trees

**Signal phrases in problems:**
- "Find all overlapping intervals"
- "Schedule meetings without conflicts"
- "Range collision detection"
- "Time slot availability"
- "Genomic interval analysis"

### Classical Problems

**1. Meeting Rooms II (LeetCode 253)**
```
Given intervals, find minimum rooms needed.
```
**Solution approach:**
- Don't use interval tree naively
- Better: Sort + sweep line (O(n log n))
- Interval tree overkill for this specific problem

**Expert judgment:** Know when NOT to use your tool.

**2. Range Module (LeetCode 715)**
```
Track disjoint ranges, add/remove/query ranges.
```
**Solution approach:**
- Interval tree with merge operations
- O(log n) per operation
- Requires interval splitting logic

**3. Calendar Scheduling**
```
Book intervals, reject if overlap exists.
```
**Perfect fit:** Use `search_any()` for O(log n) conflict detection.

### The Mental Model for Interval Problems

**Think geometrically:**
1. Draw intervals on a number line
2. Identify what relationships you need (containment, overlap, adjacency)
3. Ask: "Can I prune search space using max endpoints?"
4. If yes → Interval tree
5. If no → Consider alternatives (sweep line, sorting, segment tree)

---

## IX. Edge Cases & Pitfalls

### Common Mistakes

**1. Forgetting to update max after rotations**
```rust
// WRONG:
fn rotate_left(mut h: Box<Node>) -> Box<Node> {
    let mut x = h.right.take().unwrap();
    h.right = x.left.take();
    x.left = Some(h);
    x  // BUG: max values are stale!
}

// CORRECT:
fn rotate_left(mut h: Box<Node>) -> Box<Node> {
    let mut x = h.right.take().unwrap();
    h.right = x.left.take();
    h.update_max();  // Update child first
    x.left = Some(h);
    x.update_max();  // Then parent
    x
}
```

**2. Wrong overlap detection**
```rust
// WRONG (misses touching intervals):
fn overlaps_wrong(a: &Interval, b: &Interval) -> bool {
    a.low < b.high && b.low < a.high  // Excludes [1,5] and [5,10]
}

// CORRECT:
fn overlaps(a: &Interval, b: &Interval) -> bool {
    a.low <= b.high && b.low <= a.high  // Includes touching
}
```

Decide if touching intervals count as overlapping based on your problem domain.

**3. Off-by-one in pruning**
```rust
// WRONG:
if query.low >= node.max { return; }  // Misses exact matches

// CORRECT:
if query.low > node.max { return; }
```

### Degenerate Cases

**Single-point intervals [x, x]:**
- Ensure they're handled consistently
- Overlap only with ranges containing x

**Empty tree:**
- Always check for null root
- Return empty results, not errors

**All intervals identical:**
- Tree degenerates to linked list (still O(log n) with balancing)
- Red-Black tree handles this gracefully

---

## X. Performance Optimization Techniques

### 1. **Memory Layout Optimization (C/Rust)**

```rust
// Cache-friendly node layout
#[repr(C)]
struct Node {
    interval: Interval,  // 16 bytes
    max: i64,            // 8 bytes
    left: *mut Node,     // 8 bytes
    right: *mut Node,    // 8 bytes
    color: u8,           // 1 byte
    _padding: [u8; 7],   // Align to 64-byte cache line
}
```

This ensures nodes fit cleanly in cache lines, reducing memory stalls.

### 2. **Bulk Loading**

For static or mostly-static datasets:
```rust
fn bulk_load(intervals: &mut [Interval]) -> IntervalTree {
    intervals.sort_by_key(|i| i.low);
    // Build balanced tree bottom-up
    // O(n) construction instead of O(n log n)
}
```

### 3. **Lazy Propagation** (Advanced)

For range updates on intervals:
- Mark subtrees with pending updates
- Propagate lazily on access
- Reduces update complexity

---

## XI. The Deeper Algorithmic Insight

**Why interval trees work is not obvious:**

The key is that `max` creates a **monotonic relationship** between tree structure and geometric space. When you prune based on max, you're exploiting the fact that:

```
If no interval in a subtree extends past point p,
then no interval in that subtree can overlap with [p, q]
```

This isn't just a "neat trick" - it's a profound connection between:
- **Algebraic structure** (BST invariant on `low`)
- **Geometric structure** (interval containment)
- **Augmented metadata** (`max` aggregation)

**The mental breakthrough:** You're not just searching a BST; you're pruning a geometric search space using algebraic invariants.

This same principle generalizes to:
- Range trees (multi-dimensional)
- Priority search trees (2D dominance)
- Segment trees (range queries)

---

## XII. Alternative Approaches & Trade-offs

| Data Structure | Insert | Query | Space | When to Use |
|----------------|--------|-------|-------|-------------|
| Interval Tree | O(log n) | O(k + log n) | O(n) | Dynamic, general overlap queries |
| Segment Tree | O(log n) | O(log n + k) | O(n) | Static/semi-static, stabbing queries |
| Sorted Array + Binary Search | O(n) | O(log n + k) | O(n) | Read-only, small datasets |
| Sweep Line | O(n log n) | O(n) | O(n) | One-time batch processing |

**Decision framework:**
1. **Dynamic updates?** → Interval tree or segment tree
2. **Point stabbing only?** → Segment tree or simpler structures
3. **Batch processing?** → Sweep line algorithm
4. **Memory constrained?** → Compressed segment tree

---

## Final Mastery Checklist

You've mastered interval trees when you can:

✓ **Explain** why `max` must be updated bottom-up after rotations  
✓ **Derive** the O(k + log n) query complexity from first principles  
✓ **Implement** from scratch in under 30 minutes  
✓ **Recognize** when interval trees are overkill  
✓ **Extend** to multi-dimensional or persistent variants  
✓ **Debug** max-propagation bugs instantly  
✓ **Choose** between interval tree, segment tree, and sweep line  

**The monk's approach:** True mastery isn't memorizing code - it's understanding the invariants so deeply that implementation becomes inevitable.

You now possess the architectural knowledge. The path forward: deliberate practice on increasingly complex variants until interval trees become an instinctive tool in your algorithmic arsenal.

*The tree balances itself; the mind balances understanding.*