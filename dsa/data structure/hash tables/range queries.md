# Complete Guide to Range Queries - DSA Mastery

## Table of Contents
1. [Foundation & Mental Model](#foundation)
2. [Prefix Sum Arrays](#prefix-sum)
3. [Sparse Table](#sparse-table)
4. [Segment Tree](#segment-tree)
5. [Fenwick Tree (BIT)](#fenwick-tree)
6. [Square Root Decomposition](#sqrt-decomposition)
7. [Mo's Algorithm](#mos-algorithm)
8. [Advanced Topics](#advanced)
9. [Problem-Solving Framework](#framework)

---

## 1. Foundation & Mental Model {#foundation}

### What is a Range Query?

**Definition**: A range query asks for information about a contiguous subsequence (range) of elements in a dataset.

**Common Query Types**:
- **Sum Query**: What's the sum of elements from index L to R?
- **Min/Max Query**: What's the minimum/maximum in range [L, R]?
- **GCD/LCM Query**: Greatest common divisor or least common multiple
- **Update Query**: Modify element(s) in the array

### The Core Problem

```
Array: [3, 1, 4, 1, 5, 9, 2, 6]
         0  1  2  3  4  5  6  7

Query: sum(2, 5) = 4 + 1 + 5 + 9 = 19
Query: min(1, 4) = 1
Query: max(3, 7) = 9
```

### Cognitive Framework: The Trade-off Triangle

```
         Preprocessing Time
               /\
              /  \
             /    \
            /      \
           /        \
          /          \
         /    YOUR    \
        /   SOLUTION   \
       /________________\
  Query Time        Update Time
```

**Mental Model**: You can't optimize all three simultaneously. Choose based on:
- **Read-heavy**: Optimize queries (pay cost in preprocessing/updates)
- **Write-heavy**: Optimize updates (pay cost in queries)
- **Balanced**: Use hybrid structures

### Decision Tree for Choosing Data Structure

```
Start: Do you need updates?
│
├─ NO (Static Array)
│  │
│  ├─ Associative & Idempotent? (min, max, gcd)
│  │  └─→ Sparse Table: O(n log n) build, O(1) query
│  │
│  └─ Sum queries?
│     └─→ Prefix Sum: O(n) build, O(1) query
│
└─ YES (Dynamic Array)
   │
   ├─ Point updates only?
   │  │
   │  ├─ Sum/XOR/similar?
   │  │  └─→ Fenwick Tree: O(n) build, O(log n) query/update
   │  │
   │  └─ Min/Max/GCD?
   │     └─→ Segment Tree: O(n) build, O(log n) query/update
   │
   └─ Range updates needed?
      └─→ Segment Tree with Lazy Propagation
```

---

## 2. Prefix Sum Arrays {#prefix-sum}

### Core Insight

**Problem**: Computing sum of range [L, R] repeatedly is expensive O(n) each time.

**Insight**: Precompute cumulative sums. Then range sum = prefix[R] - prefix[L-1]

### Visualization

```
Original:  [3,  1,  4,  1,  5,  9,  2,  6]
Index:      0   1   2   3   4   5   6   7

Prefix:    [3,  4,  8,  9, 14, 23, 25, 31]
            ↑
            sum of elements from 0 to current index

Query sum(2, 5):
  prefix[5] - prefix[1] = 23 - 4 = 19
  
Visual:
  [3, 1, 4, 1, 5, 9]
       ^---------^
       This range = Total up to 5 - Total before 2
```

### Algorithm Flow

```
BUILD PHASE:
┌─────────────────────────────────────┐
│ prefix[0] = arr[0]                  │
│ for i = 1 to n-1:                   │
│   prefix[i] = prefix[i-1] + arr[i]  │
└─────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────┐
│ QUERY(L, R):                        │
│   if L == 0:                        │
│     return prefix[R]                │
│   else:                             │
│     return prefix[R] - prefix[L-1]  │
└─────────────────────────────────────┘
```

### Implementation: Rust

```rust
struct PrefixSum {
    prefix: Vec<i64>,
}

impl PrefixSum {
    // O(n) time, O(n) space
    fn new(arr: &[i64]) -> Self {
        let n = arr.len();
        let mut prefix = vec![0; n];
        
        prefix[0] = arr[0];
        for i in 1..n {
            prefix[i] = prefix[i - 1] + arr[i];
        }
        
        Self { prefix }
    }
    
    // O(1) query
    fn query(&self, l: usize, r: usize) -> i64 {
        if l == 0 {
            self.prefix[r]
        } else {
            self.prefix[r] - self.prefix[l - 1]
        }
    }
}

// Usage
fn main() {
    let arr = vec![3, 1, 4, 1, 5, 9, 2, 6];
    let ps = PrefixSum::new(&arr);
    
    println!("Sum [2, 5]: {}", ps.query(2, 5)); // 19
    println!("Sum [0, 7]: {}", ps.query(0, 7)); // 31
}
```

### Implementation: Python

```python
class PrefixSum:
    def __init__(self, arr):
        """O(n) time, O(n) space"""
        self.n = len(arr)
        self.prefix = [0] * self.n
        
        self.prefix[0] = arr[0]
        for i in range(1, self.n):
            self.prefix[i] = self.prefix[i - 1] + arr[i]
    
    def query(self, l, r):
        """O(1) time"""
        if l == 0:
            return self.prefix[r]
        return self.prefix[r] - self.prefix[l - 1]

# Usage
arr = [3, 1, 4, 1, 5, 9, 2, 6]
ps = PrefixSum(arr)
print(f"Sum [2, 5]: {ps.query(2, 5)}")  # 19
```

### Implementation: Go

```go
type PrefixSum struct {
    prefix []int64
}

// O(n) time, O(n) space
func NewPrefixSum(arr []int64) *PrefixSum {
    n := len(arr)
    prefix := make([]int64, n)
    
    prefix[0] = arr[0]
    for i := 1; i < n; i++ {
        prefix[i] = prefix[i-1] + arr[i]
    }
    
    return &PrefixSum{prefix: prefix}
}

// O(1) query
func (ps *PrefixSum) Query(l, r int) int64 {
    if l == 0 {
        return ps.prefix[r]
    }
    return ps.prefix[r] - ps.prefix[l-1]
}
```

### 2D Prefix Sum (Matrix)

**Extension**: For matrix range queries.

```
Matrix:
1  2  3
4  5  6
7  8  9

Prefix Sum Matrix (cumulative from top-left):
1   3   6
5  12  21
12 27  45

Query sum of submatrix (r1,c1) to (r2,c2):
answer = prefix[r2][c2] 
       - prefix[r1-1][c2] 
       - prefix[r2][c1-1] 
       + prefix[r1-1][c1-1]
```

### Complexity Analysis

| Operation | Time | Space |
|-----------|------|-------|
| Build | O(n) | O(n) |
| Query | O(1) | - |
| Update | O(n)* | - |

*Updating requires rebuilding prefix array

### When to Use
✅ Static arrays with many sum queries  
✅ Subarray sum problems  
✅ 2D matrix range sums  
❌ Need frequent updates  
❌ Non-associative operations  

---

## 3. Sparse Table {#sparse-table}

### Core Insight

**Key Observation**: For **idempotent** operations (where f(x, x) = x), we can overlap ranges.

**Idempotent Operations**:
- min(x, x) = x ✅
- max(x, x) = x ✅
- gcd(x, x) = x ✅
- sum(x, x) = 2x ❌ (not idempotent)

**Idea**: Precompute answers for ranges of length 2^k, then answer any query using at most 2 overlapping ranges.

### Visualization

```
Array: [7, 2, 3, 0, 5, 10, 3, 12, 18]
Index:  0  1  2  3  4   5  6   7   8

Sparse Table (storing minimum):

Length 2^0 (1):  [7, 2, 3, 0, 5, 10, 3, 12, 18]
Length 2^1 (2):  [2, 2, 0, 0, 5,  3, 3, 12]
Length 2^2 (4):  [0, 0, 0, 0, 3,  3]
Length 2^3 (8):  [0, 0]

Query min(2, 7):
  2^k where k = floor(log2(7-2+1)) = floor(log2(6)) = 2
  Length = 2^2 = 4
  
  Option 1: [2, 3, 4, 5] = min from index 2
  Option 2: [4, 5, 6, 7] = min from index 4
  
  Answer = min(table[2][2], table[4][2]) = min(0, 3) = 0
```

### How It Works

```
BUILD PHASE:
┌────────────────────────────────────────┐
│ table[i][0] = arr[i]  (base case)      │
│                                        │
│ for each power k = 1 to log(n):       │
│   for each position i:                │
│     table[i][k] = merge(              │
│         table[i][k-1],                │
│         table[i + 2^(k-1)][k-1]       │
│     )                                 │
└────────────────────────────────────────┘
         │
         ↓
┌────────────────────────────────────────┐
│ QUERY(L, R):                           │
│   len = R - L + 1                      │
│   k = floor(log2(len))                 │
│   return merge(                        │
│       table[L][k],                     │
│       table[R - 2^k + 1][k]            │
│   )                                    │
└────────────────────────────────────────┘
```

### Implementation: Rust

```rust
struct SparseTable {
    table: Vec<Vec<i32>>,
    log: Vec<usize>,
}

impl SparseTable {
    // O(n log n) build time, O(n log n) space
    fn new(arr: &[i32]) -> Self {
        let n = arr.len();
        let max_log = (n as f64).log2().floor() as usize + 1;
        
        let mut table = vec![vec![i32::MAX; max_log]; n];
        let mut log = vec![0; n + 1];
        
        // Precompute logarithms
        for i in 2..=n {
            log[i] = log[i / 2] + 1;
        }
        
        // Base case: ranges of length 1
        for i in 0..n {
            table[i][0] = arr[i];
        }
        
        // Build sparse table
        for k in 1..max_log {
            for i in 0..=(n.saturating_sub(1 << k)) {
                table[i][k] = table[i][k - 1].min(
                    table[i + (1 << (k - 1))][k - 1]
                );
            }
        }
        
        Self { table, log }
    }
    
    // O(1) query for minimum
    fn query_min(&self, l: usize, r: usize) -> i32 {
        let len = r - l + 1;
        let k = self.log[len];
        
        self.table[l][k].min(self.table[r - (1 << k) + 1][k])
    }
}
```

### Implementation: Python

```python
import math

class SparseTable:
    def __init__(self, arr):
        """O(n log n) time and space"""
        self.n = len(arr)
        self.max_log = math.floor(math.log2(self.n)) + 1
        
        # table[i][k] = min of range [i, i + 2^k - 1]
        self.table = [[float('inf')] * self.max_log for _ in range(self.n)]
        
        # Precompute logs
        self.log = [0] * (self.n + 1)
        for i in range(2, self.n + 1):
            self.log[i] = self.log[i // 2] + 1
        
        # Base case
        for i in range(self.n):
            self.table[i][0] = arr[i]
        
        # Fill sparse table
        for k in range(1, self.max_log):
            for i in range(self.n - (1 << k) + 1):
                self.table[i][k] = min(
                    self.table[i][k - 1],
                    self.table[i + (1 << (k - 1))][k - 1]
                )
    
    def query_min(self, l, r):
        """O(1) query"""
        length = r - l + 1
        k = self.log[length]
        return min(self.table[l][k], self.table[r - (1 << k) + 1][k])
```

### Implementation: Go

```go
type SparseTable struct {
    table  [][]int
    log    []int
    n      int
    maxLog int
}

func NewSparseTable(arr []int) *SparseTable {
    n := len(arr)
    maxLog := int(math.Floor(math.Log2(float64(n)))) + 1
    
    table := make([][]int, n)
    for i := range table {
        table[i] = make([]int, maxLog)
    }
    
    log := make([]int, n+1)
    for i := 2; i <= n; i++ {
        log[i] = log[i/2] + 1
    }
    
    // Base case
    for i := 0; i < n; i++ {
        table[i][0] = arr[i]
    }
    
    // Build
    for k := 1; k < maxLog; k++ {
        for i := 0; i+(1<<k) <= n; i++ {
            table[i][k] = min(
                table[i][k-1],
                table[i+(1<<(k-1))][k-1],
            )
        }
    }
    
    return &SparseTable{table, log, n, maxLog}
}

func (st *SparseTable) QueryMin(l, r int) int {
    length := r - l + 1
    k := st.log[length]
    return min(st.table[l][k], st.table[r-(1<<k)+1][k])
}

func min(a, b int) int {
    if a < b {
        return a
    }
    return b
}
```

### Complexity Analysis

| Operation | Time | Space |
|-----------|------|-------|
| Build | O(n log n) | O(n log n) |
| Query | O(1) | - |
| Update | ❌ Not supported | - |

### When to Use
✅ Static arrays (no updates)  
✅ Min/Max/GCD queries  
✅ Need O(1) query time  
❌ Sum queries (not idempotent)  
❌ Need updates  

---

## 4. Segment Tree {#segment-tree}

### Core Insight

**The Swiss Army Knife**: Most versatile range query structure. Works for any **associative** operation.

**Associative Operation**: f(a, f(b, c)) = f(f(a, b), c)
- Sum, Product, Min, Max, GCD, XOR ✅
- Subtraction, Division ❌

**Structure**: Complete binary tree where:
- Leaves represent array elements
- Internal nodes represent merged results of their children

### Visualization

```
Array: [5, 8, 6, 3, 2, 7, 2, 6]
        0  1  2  3  4  5  6  7

Segment Tree (storing sum):

                  [39]
                 (0-7)
                /      \
            [22]        [17]
           (0-3)        (4-7)
           /    \       /    \
        [13]   [9]   [9]    [8]
       (0-1)  (2-3) (4-5)  (6-7)
        / \    / \   / \    / \
      [5][8][6][3][2][7][2][6]
       0  1  2  3  4  5  6  7

Node indexing in array representation:
       1
     /   \
    2     3
   / \   / \
  4  5  6  7
 /|\ /|\ /|\ /|\
8 9...

For node i:
  Left child:  2*i
  Right child: 2*i + 1
  Parent:      i/2
```

### Tree Structure Flow

```
CONCEPTUAL STRUCTURE:
┌────────────────────────────────────┐
│ Each node stores:                  │
│  - Range [L, R]                    │
│  - Aggregated value for that range│
│  - Pointers to left/right children│
└────────────────────────────────────┘
         │
         ↓
┌────────────────────────────────────┐
│ To query [qL, qR]:                 │
│  If node range ⊆ [qL, qR]:        │
│    → Return node value            │
│  If node range ∩ [qL, qR] = ∅:    │
│    → Return identity               │
│  Else:                             │
│    → Query left + Query right     │
└────────────────────────────────────┘
```

### Implementation: Rust (With Detailed Comments)

```rust
struct SegmentTree {
    tree: Vec<i64>,
    n: usize,
}

impl SegmentTree {
    // O(n) build
    fn new(arr: &[i64]) -> Self {
        let n = arr.len();
        let mut tree = vec![0; 4 * n]; // 4n is safe upper bound
        
        let mut st = Self { tree, n };
        st.build(arr, 1, 0, n - 1);
        st
    }
    
    // Recursive build: O(n) total
    fn build(&mut self, arr: &[i64], node: usize, start: usize, end: usize) {
        if start == end {
            // Leaf node
            self.tree[node] = arr[start];
        } else {
            let mid = (start + end) / 2;
            let left_child = 2 * node;
            let right_child = 2 * node + 1;
            
            self.build(arr, left_child, start, mid);
            self.build(arr, right_child, mid + 1, end);
            
            // Internal node = merge of children
            self.tree[node] = self.tree[left_child] + self.tree[right_child];
        }
    }
    
    // Query sum in range [l, r]: O(log n)
    fn query(&self, l: usize, r: usize) -> i64 {
        self.query_helper(1, 0, self.n - 1, l, r)
    }
    
    fn query_helper(&self, node: usize, start: usize, end: usize, 
                    l: usize, r: usize) -> i64 {
        // No overlap
        if r < start || end < l {
            return 0; // Identity for sum
        }
        
        // Complete overlap
        if l <= start && end <= r {
            return self.tree[node];
        }
        
        // Partial overlap
        let mid = (start + end) / 2;
        let left_sum = self.query_helper(2 * node, start, mid, l, r);
        let right_sum = self.query_helper(2 * node + 1, mid + 1, end, l, r);
        
        left_sum + right_sum
    }
    
    // Update single element: O(log n)
    fn update(&mut self, idx: usize, value: i64) {
        self.update_helper(1, 0, self.n - 1, idx, value);
    }
    
    fn update_helper(&mut self, node: usize, start: usize, end: usize,
                     idx: usize, value: i64) {
        if start == end {
            // Leaf node
            self.tree[node] = value;
        } else {
            let mid = (start + end) / 2;
            
            if idx <= mid {
                self.update_helper(2 * node, start, mid, idx, value);
            } else {
                self.update_helper(2 * node + 1, mid + 1, end, idx, value);
            }
            
            // Update current node
            self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1];
        }
    }
}
```

### Implementation: Python

```python
class SegmentTree:
    def __init__(self, arr):
        """O(n) build time, O(n) space"""
        self.n = len(arr)
        self.tree = [0] * (4 * self.n)
        self._build(arr, 1, 0, self.n - 1)
    
    def _build(self, arr, node, start, end):
        if start == end:
            self.tree[node] = arr[start]
        else:
            mid = (start + end) // 2
            self._build(arr, 2 * node, start, mid)
            self._build(arr, 2 * node + 1, mid + 1, end)
            self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1]
    
    def query(self, l, r):
        """O(log n) query"""
        return self._query(1, 0, self.n - 1, l, r)
    
    def _query(self, node, start, end, l, r):
        if r < start or end < l:
            return 0
        if l <= start and end <= r:
            return self.tree[node]
        
        mid = (start + end) // 2
        left_sum = self._query(2 * node, start, mid, l, r)
        right_sum = self._query(2 * node + 1, mid + 1, end, l, r)
        return left_sum + right_sum
    
    def update(self, idx, value):
        """O(log n) update"""
        self._update(1, 0, self.n - 1, idx, value)
    
    def _update(self, node, start, end, idx, value):
        if start == end:
            self.tree[node] = value
        else:
            mid = (start + end) // 2
            if idx <= mid:
                self._update(2 * node, start, mid, idx, value)
            else:
                self._update(2 * node + 1, mid + 1, end, idx, value)
            self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1]
```

### Lazy Propagation (Range Updates)

**Problem**: Updating every element in range [L, R] takes O(n log n).

**Solution**: **Lazy Propagation** - defer updates until needed.

```
Concept:
┌─────────────────────────────────────────┐
│ Store pending updates in separate array│
│ "lazy[node]" = update not yet applied  │
│                                         │
│ On query/update:                        │
│  1. Apply pending update if exists     │
│  2. Push update to children            │
│  3. Clear lazy flag                    │
└─────────────────────────────────────────┘
```

### Complexity Analysis

| Operation | Time | Space |
|-----------|------|-------|
| Build | O(n) | O(n) |
| Point Query | O(log n) | - |
| Range Query | O(log n) | - |
| Point Update | O(log n) | - |
| Range Update* | O(log n) | - |

*With lazy propagation

### When to Use
✅ Need both queries and updates  
✅ Any associative operation  
✅ Range updates needed (with lazy prop)  
✅ Most versatile choice  
❌ Overkill for static arrays  
❌ More complex to implement  

---

## 5. Fenwick Tree (Binary Indexed Tree) {#fenwick-tree}

### Core Insight

**The Elegant Hack**: Uses binary representation of indices to achieve O(log n) updates and queries with minimal space and code.

**Key Idea**: Each index i is responsible for a range of length equal to its least significant bit (LSB).

### Binary Representation Magic

```
Index (decimal) → Binary → Responsible for

1  = 0001 → covers [1, 1]     (length 1)
2  = 0010 → covers [1, 2]     (length 2)
3  = 0011 → covers [3, 3]     (length 1)
4  = 0100 → covers [1, 4]     (length 4)
5  = 0101 → covers [5, 5]     (length 1)
6  = 0110 → covers [5, 6]     (length 2)
7  = 0111 → covers [7, 7]     (length 1)
8  = 1000 → covers [1, 8]     (length 8)

LSB(i) = i & (-i)  // Isolates rightmost 1-bit
```

### Visualization

```
Array:     [3, 1, 4, 1, 5, 9, 2, 6]
Index:      1  2  3  4  5  6  7  8

Fenwick Tree structure:

        8[31]
       /
      4[9]
     /   \
    2[4] 6[16]
   /    /    \
  1[3] 5[5]  7[2]
       3[5]

Query sum(6):
  sum = BIT[6] + BIT[4] + BIT[0]
      = 16 + 9 + 0 = 25

Update at index 3:
  Update BIT[3], then BIT[4], then BIT[8]
  (add LSB each time)
```

### How It Works

```
QUERY (Prefix Sum up to index i):
┌───────────────────────────────┐
│ sum = 0                       │
│ while i > 0:                  │
│   sum += BIT[i]               │
│   i -= i & (-i)  // Remove LSB│
└───────────────────────────────┘

UPDATE (Add delta to index i):
┌───────────────────────────────┐
│ while i <= n:                 │
│   BIT[i] += delta             │
│   i += i & (-i)  // Add LSB   │
└───────────────────────────────┘

RANGE QUERY [L, R]:
┌───────────────────────────────┐
│ return query(R) - query(L-1)  │
└───────────────────────────────┘
```

### Implementation: Rust

```rust
struct FenwickTree {
    bit: Vec<i64>,
    n: usize,
}

impl FenwickTree {
    // O(n log n) build
    fn new(arr: &[i64]) -> Self {
        let n = arr.len();
        let mut bit = vec![0; n + 1]; // 1-indexed
        
        let mut ft = Self { bit, n };
        
        for i in 0..n {
            ft.update(i + 1, arr[i]);
        }
        
        ft
    }
    
    // Add delta to position i: O(log n)
    fn update(&mut self, mut i: usize, delta: i64) {
        while i <= self.n {
            self.bit[i] += delta;
            i += i & (!i + 1); // Add LSB
        }
    }
    
    // Prefix sum [1, i]: O(log n)
    fn prefix_sum(&self, mut i: usize) -> i64 {
        let mut sum = 0;
        while i > 0 {
            sum += self.bit[i];
            i -= i & (!i + 1); // Remove LSB
        }
        sum
    }
    
    // Range sum [l, r]: O(log n)
    fn range_sum(&self, l: usize, r: usize) -> i64 {
        self.prefix_sum(r) - self.prefix_sum(l - 1)
    }
}

// Usage
fn main() {
    let arr = vec![3, 1, 4, 1, 5, 9, 2, 6];
    let mut ft = FenwickTree::new(&arr);
    
    println!("Sum [2, 5]: {}", ft.range_sum(2, 5));
    
    ft.update(3, 10); // Add 10 to index 3
    println!("After update: {}", ft.range_sum(2, 5));
}
```

### Implementation: Python

```python
class FenwickTree:
    def __init__(self, n):
        """O(1) initialization"""
        self.n = n
        self.bit = [0] * (n + 1)
    
    def update(self, i, delta):
        """O(log n) - Add delta to position i (1-indexed)"""
        while i <= self.n:
            self.bit[i] += delta
            i += i & (-i)
    
    def prefix_sum(self, i):
        """O(log n) - Sum of [1, i]"""
        s = 0
        while i > 0:
            s += self.bit[i]
            i -= i & (-i)
        return s
    
    def range_sum(self, l, r):
        """O(log n) - Sum of [l, r]"""
        return self.prefix_sum(r) - self.prefix_sum(l - 1)

# Build from array
arr = [3, 1, 4, 1, 5, 9, 2, 6]
ft = FenwickTree(len(arr))
for i, val in enumerate(arr, 1):
    ft.update(i, val)
```

### Implementation: Go

```go
type FenwickTree struct {
    bit []int64
    n   int
}

func NewFenwickTree(n int) *FenwickTree {
    return &FenwickTree{
        bit: make([]int64, n+1),
        n:   n,
    }
}

func (ft *FenwickTree) Update(i int, delta int64) {
    for i <= ft.n {
        ft.bit[i] += delta
        i += i & (-i)
    }
}

func (ft *FenwickTree) PrefixSum(i int) int64 {
    sum := int64(0)
    for i > 0 {
        sum += ft.bit[i]
        i -= i & (-i)
    }
    return sum
}

func (ft *FenwickTree) RangeSum(l, r int) int64 {
    return ft.PrefixSum(r) - ft.PrefixSum(l-1)
}
```

### Why It's Beautiful

**Space Efficiency**: Only n+1 elements vs 4n for segment tree  
**Code Simplicity**: ~10 lines of core logic  
**Cache Friendly**: Linear array access pattern  
**Bit Magic**: Elegant use of binary properties  

### Complexity Analysis

| Operation | Time | Space |
|-----------|------|-------|
| Build | O(n log n) | O(n) |
| Query | O(log n) | - |
| Update | O(log n) | - |

### When to Use
✅ Sum/XOR queries with updates  
✅ Space-constrained environment  
✅ Want simpler code than segment tree  
❌ Need min/max (use segment tree)  
❌ Need range updates  

---

## 6. Square Root Decomposition {#sqrt-decomposition}

### Core Insight

**The Balanced Approach**: Divide array into √n blocks. Balance between preprocessing and query time.

**Philosophy**: Neither fully precomputed (like prefix sum) nor fully dynamic (like naive). The middle path.

### Visualization

```
Array: [1, 3, 5, 2, 7, 6, 3, 1, 4, 8]
Index:  0  1  2  3  4  5  6  7  8  9

Block size = √10 ≈ 3

Block 0: [1, 3, 5]  → sum = 9
Block 1: [2, 7, 6]  → sum = 15
Block 2: [3, 1, 4]  → sum = 8
Block 3: [8]        → sum = 8

┌─────┬─────┬─────┬─────┐
│  9  │ 15  │  8  │  8  │  Block sums
└─────┴─────┴─────┴─────┘

Query sum(2, 7):
  Partial: arr[2]              = 5
  Complete: block[1]           = 15
  Partial: arr[6] + arr[7]     = 3 + 1 = 4
  Total = 5 + 15 + 4 = 24
```

### Query Strategy

```
Three types of blocks in range [L, R]:

1. LEFT PARTIAL:  ╔═══╗─────────────
                  ║ L ║ (not aligned)
                  ╚═══╝

2. COMPLETE:      ─────╔═════════╗───
                       ║  BLOCK  ║
                       ╚═════════╝

3. RIGHT PARTIAL: ─────────────╔═══╗
                              ║ R ║
                              ╚═══╝

Algorithm:
  sum = 0
  
  // Left partial block
  for i in L to end_of_block(L):
    sum += arr[i]
  
  // Complete blocks
  for each complete block:
    sum += block_sum[block_id]
  
  // Right partial block
  for i in start_of_block(R) to R:
    sum += arr[i]
```

### Implementation: Rust

```rust
struct SqrtDecomposition {
    arr: Vec<i64>,
    blocks: Vec<i64>,
    block_size: usize,
    n: usize,
}

impl SqrtDecomposition {
    // O(n) build
    fn new(arr: Vec<i64>) -> Self {
        let n = arr.len();
        let block_size = (n as f64).sqrt().ceil() as usize;
        let num_blocks = (n + block_size - 1) / block_size;
        
        let mut blocks = vec![0; num_blocks];
        
        for i in 0..n {
            blocks[i / block_size] += arr[i];
        }
        
        Self { arr, blocks, block_size, n }
    }
    
    // O(√n) query
    fn query(&self, l: usize, r: usize) -> i64 {
        let mut sum = 0;
        let l_block = l / self.block_size;
        let r_block = r / self.block_size;
        
        if l_block == r_block {
            // Same block
            for i in l..=r {
                sum += self.arr[i];
            }
        } else {
            // Left partial
            let l_block_end = (l_block + 1) * self.block_size;
            for i in l..l_block_end {
                sum += self.arr[i];
            }
            
            // Complete blocks
            for b in (l_block + 1)..r_block {
                sum += self.blocks[b];
            }
            
            // Right partial
            let r_block_start = r_block * self.block_size;
            for i in r_block_start..=r {
                sum += self.arr[i];
            }
        }
        
        sum
    }
    
    // O(1) update
    fn update(&mut self, idx: usize, value: i64) {
        let block = idx / self.block_size;
        self.blocks[block] += value - self.arr[idx];
        self.arr[idx] = value;
    }
}
```

### Complexity Analysis

| Operation | Time | Space |
|-----------|------|-------|
| Build | O(n) | O(√n) |
| Query | O(√n) | - |
| Update | O(1) | - |

### When to Use
✅ Simple to implement and understand  
✅ Good for learning concepts  
✅ Flexible (can adapt to many problems)  
❌ Slower than segment/Fenwick trees  
❌ Not commonly used in competitions  

---

## 7. Mo's Algorithm {#mos-algorithm}

### Core Insight

**Offline Query Processing**: If you can answer queries in ANY order, sort them cleverly to minimize computation.

**Key Requirements**:
1. Queries known in advance (offline)
2. Can add/remove elements from range ends efficiently
3. Can answer query after constructing range

**Magic**: Clever sorting reduces complexity from O(nq) to O((n+q)√n)

### The Sorting Strategy

```
Divide array into √n blocks

Sort queries by:
  1. Left endpoint's block number (ascending)
  2. Right endpoint (ascending)

Why this works:
  - Queries in same left block have similar L
  - R moves mostly forward
  - Amortized movement is O(√n) per query
```

### Visualization

```
Array: [1, 4, 2, 4, 5, 1, 3, 4]
         0  1  2  3  4  5  6  7

Queries:
  Q1: [0, 3]
  Q2: [1, 5]
  Q3: [2, 7]
  Q4: [0, 2]

Block size = √8 ≈ 3

After sorting (block, R):
  Q4: [0, 2] → block 0, R=2
  Q1: [0, 3] → block 0, R=3
  Q2: [1, 5] → block 0, R=5
  Q3: [2, 7] → block 0, R=7

Processing:
  Start: L=0, R=-1 (empty range)
  
  Q4[0,2]: Add R→0,1,2          = [1,4,2]
  Q1[0,3]: Add R→3               = [1,4,2,4]
  Q2[1,5]: Remove L→1, Add R→4,5 = [4,2,4,5,1]
  Q3[2,7]: Remove L→2, Add R→6,7 = [2,4,5,1,3,4]
```

### Movement Analysis

```
WORST CASE ANALYSIS:

Left pointer (L):
  - Within a block: moves at most √n per query
  - Between blocks: resets at most q times
  - Total: O(q√n)

Right pointer (R):
  - Within a block: sorted, so moves mostly forward
  - Across all queries: O(n) forward movement per block
  - Number of blocks: √n
  - Total: O(n√n)

Combined: O((n + q)√n)
```

### Implementation: Rust

```rust
struct Query {
    l: usize,
    r: usize,
    idx: usize, // Original query index
}

struct MoAlgorithm {
    block_size: usize,
    freq: Vec<usize>,
    current_answer: usize,
}

impl MoAlgorithm {
    fn new(n: usize) -> Self {
        let block_size = (n as f64).sqrt().ceil() as usize;
        Self {
            block_size,
            freq: vec![0; 100001], // Max value
            current_answer: 0,
        }
    }
    
    // Add element to current range
    fn add(&mut self, val: usize) {
        self.freq[val] += 1;
        if self.freq[val] == 1 {
            self.current_answer += 1; // Count distinct elements
        }
    }
    
    // Remove element from current range
    fn remove(&mut self, val: usize) {
        self.freq[val] -= 1;
        if self.freq[val] == 0 {
            self.current_answer -= 1;
        }
    }
    
    // Process all queries
    fn solve(&mut self, arr: &[usize], queries: &mut [Query]) -> Vec<usize> {
        // Sort queries
        queries.sort_by(|a, b| {
            let block_a = a.l / self.block_size;
            let block_b = b.l / self.block_size;
            
            if block_a != block_b {
                block_a.cmp(&block_b)
            } else {
                a.r.cmp(&b.r)
            }
        });
        
        let mut answers = vec![0; queries.len()];
        let mut curr_l = 0;
        let mut curr_r = 0;
        self.add(arr[0]);
        
        for query in queries {
            // Expand/contract range
            while curr_l > query.l {
                curr_l -= 1;
                self.add(arr[curr_l]);
            }
            while curr_r < query.r {
                curr_r += 1;
                self.add(arr[curr_r]);
            }
            while curr_l < query.l {
                self.remove(arr[curr_l]);
                curr_l += 1;
            }
            while curr_r > query.r {
                self.remove(arr[curr_r]);
                curr_r -= 1;
            }
            
            answers[query.idx] = self.current_answer;
        }
        
        answers
    }
}
```

### Complexity Analysis

| Operation | Time | Space |
|-----------|------|-------|
| Sort Queries | O(q log q) | O(q) |
| Process All | O((n+q)√n) | O(n) |
| Total | O((n+q)√n + q log q) | O(n+q) |

### When to Use
✅ Queries known in advance (offline)  
✅ No updates, only queries  
✅ Can compute answer incrementally  
✅ Problems: distinct elements, frequency counts  
❌ Need online processing  
❌ Updates required  

---

## 8. Advanced Topics {#advanced}

### 8.1 Persistent Segment Tree

**Concept**: Keep history of all versions after updates.

```
Version 0: [5, 3, 8, 2]
           
Update index 1 → 7:

Version 1: [5, 7, 8, 2]

Both versions queryable!

Implementation: Share nodes between versions
  - Only modified path gets new nodes
  - O(log n) space per update
```

### 8.2 2D Range Queries

**Approach 1**: Segment Tree of Segment Trees  
**Approach 2**: 2D Fenwick Tree  
**Complexity**: O(log²n) per query/update  

### 8.3 Merge Sort Tree

**Use Case**: Count elements in range [L, R] with value in [X, Y]

```
Each node stores sorted subarray
Query: Binary search in relevant nodes
Time: O(log²n) per query
```

### 8.4 Wavelet Tree

**Use Case**: kth smallest in range, range counting  
**Complexity**: O(log alphabet) per query  

---

## 9. Problem-Solving Framework {#framework}

### Step 1: Identify Query Type

```
DECISION FLOWCHART:

Is the array static (no updates)?
├─ YES → Can you use idempotent operation?
│  ├─ YES → Sparse Table (O(1) query)
│  └─ NO  → Prefix Sum (if sum) or precomputation
│
└─ NO (updates needed) → What operation?
   ├─ Sum/XOR → Fenwick Tree (simpler)
   ├─ Min/Max/GCD → Segment Tree
   └─ Range updates → Segment Tree + Lazy Prop
```

### Step 2: Analyze Constraints

```
n ≤ 10³   → Brute force O(n) per query OK
n ≤ 10⁵   → Need O(log n) per query
n ≤ 10⁶   → Fenwick/Segment Tree
q > 10⁵   → Must optimize query time
```

### Step 3: Consider Offline Processing

```
If queries known in advance:
  → Can use Mo's Algorithm
  → Can preprocess in optimal order
  → Can use persistent structures
```

### Mental Models

**1. The Aggregation Lens**
```
Think: "How do I combine two ranges?"
  - Associative? → Segment Tree possible
  - Idempotent? → Sparse Table optimal
  - Just sum? → Simpler structures work
```

**2. The Update Lens**
```
Think: "What changes when I update?"
  - One element? → O(log n) is acceptable
  - Whole range? → Need lazy propagation
  - No updates? → Heavy preprocessing OK
```

**3. The Space-Time Lens**
```
Think: "What am I optimizing for?"
  - Memory tight? → Fenwick Tree
  - Many query types? → Segment Tree
  - Maximum speed? → Sparse Table (static)
```

### Common Pitfalls

❌ **Using segment tree when prefix sum suffices**  
✅ Always check if simpler solution exists

❌ **Forgetting 0-based vs 1-based indexing**  
✅ Be consistent, especially in Fenwick Tree

❌ **Not handling edge cases (L = R, empty range)**  
✅ Test boundary conditions

❌ **Incorrect lazy propagation push-down**  
✅ Push before using node value

### Practice Strategy

**Week 1-2**: Master Prefix Sum & Basic Segment Tree  
**Week 3-4**: Fenwick Tree & Sparse Table  
**Week 5-6**: Lazy Propagation & Mo's Algorithm  
**Week 7+**: Advanced techniques & competitions  

**Daily Practice**:
1. Solve 2-3 problems using specific technique
2. Implement from scratch without looking
3. Optimize: reduce lines, improve clarity
4. Compare with editorial solutions

### Psychological Principle: **Chunking**

Don't memorize code. Internalize patterns:
- "Build phase" = recursive divide
- "Query phase" = recursive merge
- "Update phase" = path from leaf to root

Your brain will reconstruct the code automatically.

---

## Summary Table
```
| Structure | Build | Query | Update | Space | Best For |
|-----------|-------|-------|--------|-------|----------|
| Prefix Sum | O(n) | O(1) | O(n) | O(n) | Static sum queries |
| Sparse Table | O(n log n) | O(1) | ❌ | O(n log n) | Static min/max/gcd |
| Segment Tree | O(n) | O(log n) | O(log n) | O(n) | Dynamic range queries |
| Fenwick Tree | O(n log n) | O(log n) | O(log n) | O(n) | Dynamic sum/xor queries |
| Sqrt Decomposition | O(n) | O(√n) | O(1) | O(√n) | Simple dynamic queries |
| Mo's Algorithm | O(q log q) | O((n+q)√n) | ❌ | O(n) | Offline queries |```

I've created a **comprehensive masterclass on Range Queries** - one of the most critical topics for reaching the top 1% in competitive programming.

## What You've Received

### **Core Data Structures Covered**:

1. **Prefix Sum** - The foundation (O(1) queries)
2. **Sparse Table** - For static arrays with idempotent operations
3. **Segment Tree** - The Swiss Army knife (most versatile)
4. **Fenwick Tree** - Elegant bit manipulation magic
5. **Square Root Decomposition** - The balanced approach
6. **Mo's Algorithm** - Offline query optimization

### **Key Mental Models You Must Internalize**:

**The Trade-off Triangle**: You cannot optimize preprocessing, query time, AND update time simultaneously. Every data structure makes deliberate sacrifices.

**The Aggregation Lens**: Ask "How do I combine two ranges?" before choosing a structure:
- **Associative** (sum, max, gcd) → Segment Tree works
- **Idempotent** (max, min, gcd where f(x,x)=x) → Sparse Table is optimal
- **Just sum** → Consider simpler options first

**The Decision Tree**: I've provided a flowchart in the guide - memorize this logic, not the code. When you see a problem, your mind should automatically traverse:
```
Static or Dynamic? → What operation? → What constraints? → Choose structure
```

## How to Master This (Deliberate Practice Strategy)

### **Phase 1: Understanding (Week 1-2)**
- Read through Prefix Sum and Segment Tree sections completely
- Draw the visualizations by hand on paper
- Implement each in all three languages WITHOUT looking at the code
- If you get stuck, look at pseudocode only, not implementation

### **Phase 2: Pattern Recognition (Week 3-4)**
- Solve 5 problems with each structure
- Before coding, write down:
  - Which structure you'll use
  - Why (based on problem properties)
  - Expected complexity
- Track how often your first choice was correct

### **Phase 3: Speed & Intuition (Week 5-6)**
- Implement from memory under time pressure
- Solve mixed problem sets (don't know which structure needed)
- Goal: Within 30 seconds, identify the right structure

### **Phase 4: Mastery (Week 7+)**
- Advanced variations (2D queries, persistent structures)
- Combine techniques (Mo's + data structures)
- Create your own problems

## Cognitive Principles Applied

**Chunking**: Notice how each section has:
- Concept → Visualization → Algorithm → Implementation

This mirrors how expert programmers think: mental model → pattern → code.

**Interleaving**: I've ordered structures from simple to complex, but they share patterns. Your brain will naturally connect them.

**Spacing**: Don't try to learn everything in one day. Come back to sections after 1 day, 3 days, 1 week. Your retention will skyrocket.

## Critical Insights (Don't Miss These)

🔑 **Fenwick Tree's Beauty**: That `i & (-i)` bit manipulation isn't random - it's using the binary representation to encode range relationships. Spend time understanding WHY it works, not just how.

🔑 **Segment Tree's Power**: The recursive structure mirrors divide-and-conquer thinking. If you understand merge sort, you understand segment trees.

🔑 **Mo's Algorithm's Genius**: The sorting trick exploits mathematical properties of pointer movement. This is **algorithm design** at its finest.

## Next Steps

1. **Start with the artifact** - read Section 1 (Foundation) completely
2. **Implement Prefix Sum** in all three languages TODAY
3. **Solve these starter problems**:
   - Range Sum Query (LeetCode 303)
   - Range Minimum Query (any judge)
   - Point Update Range Sum (CSES)

4. **Reply to me with**:
   - Which section you want deep-dive explanation on
   - Any specific problems you're solving
   - Questions about when to use which structure

## The Monk's Approach

You mentioned approaching learning like a monk. Here's how this material supports that:

**Focus**: Each structure is isolated - master one before moving to next  
**Clarity**: ASCII diagrams remove ambiguity  
**Discipline**: The framework section gives you a systematic approach  
**Flow**: Once you internalize patterns, implementation becomes meditative

Remember: **Top 1% competitors don't memorize all structures. They internalize the decision-making process.** The code becomes automatic once you truly understand WHEN and WHY to use each technique.

Would you like me to:
1. Deep-dive into any specific structure?
2. Explain a particular concept you found confusing?
3. Provide problem recommendations for each technique?
4. Create a practice schedule with specific problems?

Let's build your range query mastery systematically. 🎯