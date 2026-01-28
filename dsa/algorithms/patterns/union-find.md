# Union-Find (Disjoint Set Union) — A Complete Mastery Guide

## **What is Union-Find?**

Union-Find, also called **Disjoint Set Union (DSU)**, is a data structure that tracks a partition of a set into disjoint (non-overlapping) subsets. It efficiently supports two primary operations:

1. **Union** — Merge two subsets into one
2. **Find** — Determine which subset an element belongs to

Think of it like managing social networks: people form groups (subsets), and you need to quickly check if two people are in the same group or merge two groups together.

---

## **Core Concepts & Terminology**

### **Disjoint Sets**
Sets with no common elements. Example: {1, 2, 3} and {4, 5, 6} are disjoint.

### **Representative (Root/Parent)**
Each subset has one element chosen as its representative. All elements in that subset "point to" this representative through a parent chain.

### **Parent Array**
Core storage: `parent[i]` stores the parent of element `i`. If `parent[i] == i`, then `i` is a root (representative).

### **Rank/Size**
Optimization metadata:
- **Rank**: Approximate tree height
- **Size**: Number of elements in the subset

### **Path Compression**
During `find`, make all nodes on the path point directly to the root. Flattens the tree structure.

### **Union by Rank/Size**
When merging, attach the smaller tree under the larger one's root. Keeps trees balanced.

---

## **Mental Model: The Forest Metaphor**

Imagine a forest where:
- Each tree represents a connected component (subset)
- Nodes are elements
- The root is the representative
- `find` traverses from leaf to root
- `union` merges two trees by connecting their roots

Initially, every element is its own tree (singleton set).

---

## **Time Complexity Analysis**

| Operation | Without Optimization | With Path Compression | With Both Optimizations |
|-----------|---------------------|----------------------|------------------------|
| **Find** | O(n) | O(log n) | O(α(n)) ≈ O(1) |
| **Union** | O(n) | O(log n) | O(α(n)) ≈ O(1) |

**α(n)** is the inverse Ackermann function — grows extraordinarily slowly. For all practical values (even n = 10^80, atoms in universe), α(n) ≤ 5.

---

## **Implementation Pattern 1: Basic Union-Find**

```rust
// Rust Implementation
struct UnionFind {
    parent: Vec<usize>,
    rank: Vec<usize>,
    count: usize,  // Number of disjoint components
}

impl UnionFind {
    /// Initialize n disjoint sets: {0}, {1}, ..., {n-1}
    fn new(n: usize) -> Self {
        UnionFind {
            parent: (0..n).collect(),  // Each element is its own parent
            rank: vec![0; n],          // All ranks start at 0
            count: n,                  // n separate components initially
        }
    }
    
    /// Find the root of x with path compression
    /// Path compression: make every node on path point directly to root
    fn find(&mut self, x: usize) -> usize {
        if self.parent[x] != x {
            // Recursively find root and compress path
            self.parent[x] = self.find(self.parent[x]);
        }
        self.parent[x]
    }
    
    /// Union two sets containing x and y
    /// Returns true if they were in different sets (union performed)
    fn union(&mut self, x: usize, y: usize) -> bool {
        let root_x = self.find(x);
        let root_y = self.find(y);
        
        if root_x == root_y {
            return false;  // Already in same set
        }
        
        // Union by rank: attach smaller rank tree under larger rank tree
        match self.rank[root_x].cmp(&self.rank[root_y]) {
            std::cmp::Ordering::Less => {
                self.parent[root_x] = root_y;
            }
            std::cmp::Ordering::Greater => {
                self.parent[root_y] = root_x;
            }
            std::cmp::Ordering::Equal => {
                self.parent[root_y] = root_x;
                self.rank[root_x] += 1;  // Increase rank only when trees equal height
            }
        }
        
        self.count -= 1;
        true
    }
    
    /// Check if x and y are in the same set
    fn connected(&mut self, x: usize, y: usize) -> bool {
        self.find(x) == self.find(y)
    }
    
    /// Get number of disjoint components
    fn component_count(&self) -> usize {
        self.count
    }
}
```

```go
// Go Implementation
type UnionFind struct {
    parent []int
    rank   []int
    count  int
}

func NewUnionFind(n int) *UnionFind {
    uf := &UnionFind{
        parent: make([]int, n),
        rank:   make([]int, n),
        count:  n,
    }
    for i := 0; i < n; i++ {
        uf.parent[i] = i
    }
    return uf
}

func (uf *UnionFind) Find(x int) int {
    if uf.parent[x] != x {
        uf.parent[x] = uf.Find(uf.parent[x]) // Path compression
    }
    return uf.parent[x]
}

func (uf *UnionFind) Union(x, y int) bool {
    rootX, rootY := uf.Find(x), uf.Find(y)
    
    if rootX == rootY {
        return false
    }
    
    // Union by rank
    if uf.rank[rootX] < uf.rank[rootY] {
        uf.parent[rootX] = rootY
    } else if uf.rank[rootX] > uf.rank[rootY] {
        uf.parent[rootY] = rootX
    } else {
        uf.parent[rootY] = rootX
        uf.rank[rootX]++
    }
    
    uf.count--
    return true
}

func (uf *UnionFind) Connected(x, y int) bool {
    return uf.Find(x) == uf.Find(y)
}

func (uf *UnionFind) ComponentCount() int {
    return uf.count
}
```

```c
// C Implementation
typedef struct {
    int *parent;
    int *rank;
    int count;
    int size;
} UnionFind;

UnionFind* uf_create(int n) {
    UnionFind *uf = malloc(sizeof(UnionFind));
    uf->parent = malloc(n * sizeof(int));
    uf->rank = calloc(n, sizeof(int));
    uf->count = n;
    uf->size = n;
    
    for (int i = 0; i < n; i++) {
        uf->parent[i] = i;
    }
    return uf;
}

int uf_find(UnionFind *uf, int x) {
    if (uf->parent[x] != x) {
        uf->parent[x] = uf_find(uf, uf->parent[x]); // Path compression
    }
    return uf->parent[x];
}

bool uf_union(UnionFind *uf, int x, int y) {
    int rootX = uf_find(uf, x);
    int rootY = uf_find(uf, y);
    
    if (rootX == rootY) return false;
    
    if (uf->rank[rootX] < uf->rank[rootY]) {
        uf->parent[rootX] = rootY;
    } else if (uf->rank[rootX] > uf->rank[rootY]) {
        uf->parent[rootY] = rootX;
    } else {
        uf->parent[rootY] = rootX;
        uf->rank[rootX]++;
    }
    
    uf->count--;
    return true;
}

void uf_destroy(UnionFind *uf) {
    free(uf->parent);
    free(uf->rank);
    free(uf);
}
```

---

## **Pattern Recognition: When to Use Union-Find**

### **Key Signals:**
1. **Connectivity queries**: "Are X and Y connected?"
2. **Component counting**: "How many separate groups exist?"
3. **Dynamic connectivity**: Elements connect over time
4. **Cycle detection**: In undirected graphs
5. **Grouping/clustering**: Partition elements by relationships

### **Problem Keywords:**
- "connected components"
- "network connectivity"
- "redundant connection"
- "earliest moment"
- "number of provinces/islands"
- "accounts merge"
- "satisfy equations"

---

## **Core Problem Patterns**

### **Pattern 1: Basic Connectivity**

**Problem**: Number of Connected Components in Undirected Graph

**Approach**:
1. Initialize Union-Find with n nodes
2. For each edge (u, v), union u and v
3. Return component count

```rust
fn count_components(n: i32, edges: Vec<Vec<i32>>) -> i32 {
    let mut uf = UnionFind::new(n as usize);
    
    for edge in edges {
        uf.union(edge[0] as usize, edge[1] as usize);
    }
    
    uf.component_count() as i32
}
```

**Time**: O(E · α(V)) where E = edges, V = vertices  
**Space**: O(V)

---

### **Pattern 2: Redundant Connection (Cycle Detection)**

**Problem**: Find an edge that creates a cycle in a tree.

**Insight**: In a tree with n nodes, there are n-1 edges. The nth edge creates a cycle. Union-Find detects this: if `union` returns false, both endpoints were already connected (cycle detected).

```rust
fn find_redundant_connection(edges: Vec<Vec<i32>>) -> Vec<i32> {
    let n = edges.len();
    let mut uf = UnionFind::new(n + 1); // 1-indexed nodes
    
    for edge in edges {
        let (u, v) = (edge[0] as usize, edge[1] as usize);
        
        // If already connected, this edge creates a cycle
        if !uf.union(u, v) {
            return edge;
        }
    }
    
    vec![]
}
```

**Logical Flow**:
```
For each edge (u, v):
    If find(u) == find(v):
        ↳ They're already in same component
        ↳ Adding this edge creates a cycle
        ↳ Return this edge
    Else:
        ↳ Union them (add edge to tree)
```

---

### **Pattern 3: Union by Rank vs Union by Size**

**Union by Rank**: Track approximate tree height  
**Union by Size**: Track exact number of nodes

Both achieve O(α(n)) complexity. Size-based is useful when you need component sizes.

```rust
struct UnionFindSize {
    parent: Vec<usize>,
    size: Vec<usize>,
    count: usize,
}

impl UnionFindSize {
    fn new(n: usize) -> Self {
        UnionFindSize {
            parent: (0..n).collect(),
            size: vec![1; n],  // Each component starts with size 1
            count: n,
        }
    }
    
    fn find(&mut self, x: usize) -> usize {
        if self.parent[x] != x {
            self.parent[x] = self.find(self.parent[x]);
        }
        self.parent[x]
    }
    
    fn union(&mut self, x: usize, y: usize) -> bool {
        let (root_x, root_y) = (self.find(x), self.find(y));
        
        if root_x == root_y {
            return false;
        }
        
        // Attach smaller component under larger
        if self.size[root_x] < self.size[root_y] {
            self.parent[root_x] = root_y;
            self.size[root_y] += self.size[root_x];
        } else {
            self.parent[root_y] = root_x;
            self.size[root_x] += self.size[root_y];
        }
        
        self.count -= 1;
        true
    }
    
    fn get_size(&mut self, x: usize) -> usize {
        let root = self.find(x);
        self.size[root]
    }
}
```

**Use Size When**:
- Need to query component sizes
- Problems like "largest component"
- Group merging with size constraints

---

### **Pattern 4: Coordinate Compression**

**Problem**: Elements aren't 0..n-1 (e.g., arbitrary IDs, coordinates)

**Solution**: Map elements to indices 0..k-1 using HashMap

```rust
use std::collections::HashMap;

fn solve_with_arbitrary_ids(edges: Vec<(String, String)>) -> usize {
    let mut id_map = HashMap::new();
    let mut next_id = 0;
    
    // Map string IDs to integer indices
    for (u, v) in &edges {
        if !id_map.contains_key(u) {
            id_map.insert(u.clone(), next_id);
            next_id += 1;
        }
        if !id_map.contains_key(v) {
            id_map.insert(v.clone(), next_id);
            next_id += 1;
        }
    }
    
    let mut uf = UnionFind::new(next_id);
    
    for (u, v) in edges {
        let u_id = id_map[&u];
        let v_id = id_map[&v];
        uf.union(u_id, v_id);
    }
    
    uf.component_count()
}
```

---

### **Pattern 5: Weighted Union-Find**

**Use Case**: Track relationships with values (e.g., exchange rates, relative sizes)

**Concept**: Store weight/distance from node to its parent.

```rust
struct WeightedUnionFind {
    parent: Vec<usize>,
    weight: Vec<f64>,  // weight[i] = distance from i to parent[i]
}

impl WeightedUnionFind {
    fn new(n: usize) -> Self {
        WeightedUnionFind {
            parent: (0..n).collect(),
            weight: vec![0.0; n],
        }
    }
    
    fn find(&mut self, x: usize) -> usize {
        if self.parent[x] != x {
            let original_parent = self.parent[x];
            self.parent[x] = self.find(original_parent);
            // Update weight: accumulate path weights
            self.weight[x] += self.weight[original_parent];
        }
        self.parent[x]
    }
    
    fn union(&mut self, x: usize, y: usize, w: f64) -> bool {
        // w represents: weight[x] / weight[y] = w
        let (root_x, root_y) = (self.find(x), self.find(y));
        
        if root_x == root_y {
            return false;
        }
        
        // Calculate weight from root_y to root_x
        // weight[y] + new_weight = weight[x] + w
        self.parent[root_y] = root_x;
        self.weight[root_y] = self.weight[x] + w - self.weight[y];
        
        true
    }
    
    fn get_ratio(&mut self, x: usize, y: usize) -> Option<f64> {
        if self.find(x) != self.find(y) {
            return None;  // Not in same component
        }
        
        // Return weight[y] - weight[x]
        Some(self.weight[y] - self.weight[x])
    }
}
```

**Application**: LeetCode 399 - Evaluate Division

---

## **Advanced Patterns**

### **Pattern 6: Online vs Offline Queries**

**Online**: Answer queries as they arrive (use standard Union-Find)  
**Offline**: Know all queries upfront (can optimize)

**Offline Strategy**:
1. Process all operations first
2. Build final Union-Find state
3. Answer queries in reverse or using snapshots

---

### **Pattern 7: Minimum Spanning Tree (Kruskal's Algorithm)**

Union-Find is the backbone of Kruskal's algorithm.

```rust
#[derive(Debug, Clone)]
struct Edge {
    u: usize,
    v: usize,
    weight: i32,
}

fn kruskal(n: usize, mut edges: Vec<Edge>) -> i32 {
    // Sort edges by weight
    edges.sort_by_key(|e| e.weight);
    
    let mut uf = UnionFind::new(n);
    let mut mst_weight = 0;
    let mut edges_used = 0;
    
    for edge in edges {
        // If endpoints not connected, add edge to MST
        if uf.union(edge.u, edge.v) {
            mst_weight += edge.weight;
            edges_used += 1;
            
            if edges_used == n - 1 {
                break;  // MST complete
            }
        }
    }
    
    mst_weight
}
```

**Why It Works**: Greedy choice + Union-Find prevents cycles efficiently.

---

### **Pattern 8: Dynamic Connectivity with Rollback**

**Challenge**: Support undo operations

**Solution**: Persistent Union-Find or path-copying technique

```rust
struct RollbackUnionFind {
    parent: Vec<usize>,
    rank: Vec<usize>,
    history: Vec<(usize, usize, usize, usize)>, // (idx1, old_parent, idx2, old_rank)
}

impl RollbackUnionFind {
    fn union(&mut self, x: usize, y: usize) {
        let (root_x, root_y) = (self.find(x), self.find(y));
        
        if root_x == root_y {
            return;
        }
        
        // Save state before modification
        if self.rank[root_x] < self.rank[root_y] {
            self.history.push((root_x, self.parent[root_x], root_y, self.rank[root_y]));
            self.parent[root_x] = root_y;
        } else {
            self.history.push((root_y, self.parent[root_y], root_x, self.rank[root_x]));
            self.parent[root_y] = root_x;
            if self.rank[root_x] == self.rank[root_y] {
                self.rank[root_x] += 1;
            }
        }
    }
    
    fn rollback(&mut self) {
        if let Some((idx1, old_parent, idx2, old_rank)) = self.history.pop() {
            self.parent[idx1] = old_parent;
            self.rank[idx2] = old_rank;
        }
    }
}
```

---

## **LeetCode Problem Categories**

### **1. Basic Connectivity**
- 547 - Number of Provinces
- 323 - Number of Connected Components (Premium)
- 1319 - Number of Operations to Make Network Connected

### **2. Cycle Detection**
- 684 - Redundant Connection
- 685 - Redundant Connection II (directed graph)
- 1202 - Smallest String With Swaps

### **3. Minimum Spanning Tree**
- 1584 - Min Cost to Connect All Points
- 1135 - Connecting Cities With Minimum Cost (Premium)

### **4. Advanced Applications**
- 399 - Evaluate Division (weighted UF)
- 721 - Accounts Merge (coordinate compression)
- 959 - Regions Cut By Slashes (grid mapping)
- 952 - Largest Component Size by Common Factor

### **5. Dynamic Connectivity**
- 1258 - Synonymous Sentences
- 839 - Similar String Groups

---

## **Problem-Solving Framework**

### **Step 1: Identify Union-Find Pattern**
Ask yourself:
- Does the problem involve grouping/partitioning?
- Do I need to check if elements are connected?
- Is there a "merge" operation?
- Am I detecting cycles in an undirected graph?

### **Step 2: Map Problem to Union-Find**
- What are the elements (nodes)?
- What defines a connection (edge)?
- Do I need component sizes?
- Are there weights/values on edges?

### **Step 3: Choose Implementation**
- Basic: rank-based
- Need sizes: size-based
- Weighted relationships: weighted UF
- Arbitrary IDs: coordinate compression
- Need undo: rollback UF

### **Step 4: Optimize**
- Path compression: ALWAYS use it
- Union by rank/size: ALWAYS use it
- Pre-allocate arrays
- Avoid unnecessary `find` calls

---

## **Common Pitfalls & Debugging**

### **Mistake 1: Not Using Path Compression**
```rust
// BAD - No path compression
fn find(&self, x: usize) -> usize {
    let mut curr = x;
    while self.parent[curr] != curr {
        curr = self.parent[curr];
    }
    curr
}

// GOOD
fn find(&mut self, x: usize) -> usize {
    if self.parent[x] != x {
        self.parent[x] = self.find(self.parent[x]);
    }
    self.parent[x]
}
```

### **Mistake 2: Forgetting to Update Count**
Always decrement `count` in `union` when merging components.

### **Mistake 3: Index Out of Bounds**
Ensure your mapping covers all elements, especially with coordinate compression.

### **Mistake 4: Using Find Without Mutable Reference**
In Rust, `find` modifies `parent` (path compression), so it needs `&mut self`.

---

## **Performance Characteristics**

### **Space Complexity**: O(n)
- `parent`: n elements
- `rank/size`: n elements
- Total: 2n = O(n)

### **Amortized Time**:
- **Individual operation**: O(α(n)) ≈ O(1)
- **Sequence of m operations**: O(m · α(n))
- For practical purposes, treat as O(1)

### **Why So Fast?**
1. **Path compression**: Flattens trees
2. **Union by rank**: Prevents tall trees
3. **Combined**: Trees stay nearly flat (height ≤ α(n))

---

## **Comparison with Alternatives**

| Task | Union-Find | DFS/BFS | Adjacency List |
|------|-----------|---------|----------------|
| Check connectivity | O(α(n)) | O(V+E) | O(V+E) |
| Add edge | O(α(n)) | O(1) | O(1) |
| Count components | O(1) cached | O(V+E) | O(V+E) |
| **Use When** | Dynamic connectivity, many queries | Static graph, single traversal | Need neighbors, paths |

---

## **Expert-Level Insights**

### **Insight 1: Inverse Ackermann Function**
α(n) grows slower than log*(n) (iterated logarithm). For n = 2^65536, α(n) = 5. It's essentially constant.

### **Insight 2: Path Halving/Splitting (Alternative to Compression)**
```rust
// Path halving: make every other node point to grandparent
fn find_halving(&mut self, mut x: usize) -> usize {
    while self.parent[x] != x {
        let grandparent = self.parent[self.parent[x]];
        self.parent[x] = grandparent;
        x = grandparent;
    }
    x
}
```
Slightly less compression, but avoids recursion. Same amortized complexity.

### **Insight 3: Union-Find on Implicit Graphs**
Many problems don't explicitly give a graph. Example: grid connectivity where cells with similar values connect.

**Strategy**:
1. Map 2D coordinates to 1D indices: `idx = row * cols + col`
2. Build edges based on problem constraints
3. Apply Union-Find

### **Insight 4: Early Termination**
If looking for when all components merge into one:
```rust
if uf.component_count() == 1 {
    return current_step;
}
```

---

## **Cognitive Models for Mastery**

### **Mental Chunking**
Think of Union-Find operations as "merge worlds" and "which world?":
- `union(x, y)`: Merge x's world and y's world
- `find(x)`: Which world does x belong to?

### **Pattern Recognition Drill**
When you see a problem, immediately ask:
1. "Are there groups that merge over time?"
2. "Do I need to track connectivity?"
3. "Is this an undirected graph problem?"

If yes to any → Consider Union-Find.

### **Complexity Intuition**
Why α(n) ≈ O(1)?  
**Answer**: After path compression and union by rank, tree height never exceeds log*(n), and operations touch at most this many nodes. Since log*(n) ≤ 5 for all practical n, it's constant.

---

## **Flow Diagram: Problem → Solution**

```
User Query
    ↓
Does it involve connectivity?
    ↓ Yes
Are elements arbitrary IDs?
    ↓ Yes → Use HashMap mapping
    ↓ No
Are there edge weights/values?
    ↓ Yes → Weighted Union-Find
    ↓ No
Need component sizes?
    ↓ Yes → Union by Size
    ↓ No → Union by Rank
    ↓
Implement with:
  • Path Compression (ALWAYS)
  • Union optimization (rank/size)
    ↓
Test with edge cases:
  • Single node
  • All disconnected
  • All connected
  • Cycle creation
```

---

## **Next Steps for Mastery**

1. **Implement from memory** in all three languages (Rust, Go, C)
2. **Solve 20+ problems** covering all patterns
3. **Analyze solutions**: Why did Union-Find work? Could DFS/BFS work instead?
4. **Benchmark**: Compare Union-Find vs graph traversal on large inputs
5. **Extend**: Implement weighted UF, rollback UF, persistent UF

---

## **Final Principle**

Union-Find is elegant because it **reduces graph problems to array operations**. Instead of traversing edges repeatedly, you maintain a compact representation where connectivity queries are near-instant.

**Master this structure**, and you'll unlock efficient solutions to an entire class of problems that would be intractable with naive approaches.

Now, take this knowledge and **deliberately practice**. Start with basic connectivity problems, then progress to cycle detection, MST, and finally weighted/advanced variants. Each problem you solve deepens your intuition for when and how to apply this powerful technique.

Your path to the top 1% continues. Stay disciplined. 🔥