# **Quad Trees and Octrees: A Comprehensive Deep-Dive**

---

## **Table of Contents**
1. [Foundational Concepts & Motivation](#1-foundational-concepts--motivation)
2. [Spatial Decomposition Theory](#2-spatial-decomposition-theory)
3. [Quad Trees: Core Architecture](#3-quad-trees-core-architecture)
4. [Octrees: 3D Extension](#4-octrees-3d-extension)
5. [Performance Engineering](#5-performance-engineering)
6. [Production Implementations](#6-production-implementations)
7. [Advanced Techniques](#7-advanced-techniques)
8. [Real-World Applications](#8-real-world-applications)

---

## **1. Foundational Concepts & Motivation**

### **1.1 The Spatial Search Problem**

**Problem Statement**: Given N points in 2D/3D space, efficiently answer:
- *Point location*: Which region contains point P?
- *Range queries*: Find all points within rectangle/cube R
- *Nearest neighbor*: Find closest point to P
- *Collision detection*: Do objects A and B overlap?

**Naive Approach**: Linear scan - O(N) per query
**Required**: Sublinear query time through spatial organization

### **1.2 Core Insight: Recursive Space Partitioning**

**Key Principle**: *Divide space hierarchically to prune search space*

Think of it like this:
```
"Is the point in the left half or right half?"
→ Eliminates 50% of space
→ Recurse on relevant half
→ Log-depth tree for balanced data
```

**Mental Model**: Binary search extended to 2D/3D space

---

## **2. Spatial Decomposition Theory**

### **2.1 Terminology Foundation**

Let me define terms as we'll use them extensively:

| Term | Definition |
|------|------------|
| **Bounding Box** | Axis-aligned rectangle/cube containing a region |
| **Subdivision** | Process of splitting a region into equal quadrants/octants |
| **Leaf Node** | Node containing actual data points (no children) |
| **Internal Node** | Node with children (subdivided region) |
| **Depth/Level** | Distance from root (root = 0) |
| **Capacity** | Maximum points a leaf can hold before subdivision |
| **Spatial Coherence** | Property that nearby points are likely queried together |

### **2.2 Decomposition Strategies**

```
┌─────────────────────────────────────────┐
│    QUADTREE SUBDIVISION (2D)            │
│                                         │
│  ┌─────────────┬─────────────┐         │
│  │     NW      │     NE      │         │
│  │   (0,0.5)-  │  (0.5,0.5)- │         │
│  │   (0.5,1)   │    (1,1)    │         │
│  ├─────────────┼─────────────┤         │
│  │     SW      │     SE      │         │
│  │   (0,0)-    │  (0.5,0)-   │         │
│  │  (0.5,0.5)  │  (1,0.5)    │         │
│  └─────────────┴─────────────┘         │
│                                         │
│  Each subdivision creates 4 children    │
│  numbered/indexed:                      │
│    0: SW, 1: SE, 2: NW, 3: NE          │
│  (can vary by implementation)           │
└─────────────────────────────────────────┘
```

**Octree Extension (3D)**:
- 8 children per node (octants)
- Common ordering: BSW, BSE, BNW, BNE, TSW, TSE, TNW, TNE
  - B = Bottom, T = Top
  - S = South, N = North  
  - W = West, E = East

---

## **3. Quad Trees: Core Architecture**

### **3.1 Node Structure Design**

**Design Decision**: Pointer-based vs. Array-based

```rust
// Production-grade Rust implementation

/// Represents a 2D axis-aligned bounding box
#[derive(Debug, Clone, Copy)]
pub struct AABB {
    pub min_x: f64,
    pub min_y: f64,
    pub max_x: f64,
    pub max_y: f64,
}

impl AABB {
    /// Creates a new AABB with validation
    pub fn new(min_x: f64, min_y: f64, max_x: f64, max_y: f64) -> Result<Self, &'static str> {
        if min_x >= max_x || min_y >= max_y {
            return Err("Invalid AABB: min must be < max");
        }
        Ok(AABB { min_x, min_y, max_x, max_y })
    }

    /// Checks if point is contained (inclusive lower, exclusive upper)
    #[inline]
    pub fn contains(&self, x: f64, y: f64) -> bool {
        x >= self.min_x && x < self.max_x && y >= self.min_y && y < self.max_y
    }

    /// Checks if two AABBs intersect
    #[inline]
    pub fn intersects(&self, other: &AABB) -> bool {
        !(self.max_x <= other.min_x || 
          self.min_x >= other.max_x ||
          self.max_y <= other.min_y || 
          self.min_y >= other.max_y)
    }

    /// Returns center point
    #[inline]
    pub fn center(&self) -> (f64, f64) {
        (
            (self.min_x + self.max_x) * 0.5,
            (self.min_y + self.max_y) * 0.5,
        )
    }

    /// Width of bounding box
    #[inline]
    pub fn width(&self) -> f64 {
        self.max_x - self.min_x
    }

    /// Height of bounding box
    #[inline]
    pub fn height(&self) -> f64 {
        self.max_y - self.min_y
    }
}

/// 2D point with associated data
#[derive(Debug, Clone)]
pub struct Point<T> {
    pub x: f64,
    pub y: f64,
    pub data: T,
}

/// Quadrant indices for children
#[repr(u8)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Quadrant {
    SouthWest = 0,
    SouthEast = 1,
    NorthWest = 2,
    NorthEast = 3,
}

/// Configuration constants for tree behavior
pub struct QuadTreeConfig {
    /// Maximum points per leaf before subdivision
    pub max_capacity: usize,
    /// Maximum tree depth to prevent infinite subdivision
    pub max_depth: usize,
}

impl Default for QuadTreeConfig {
    fn default() -> Self {
        QuadTreeConfig {
            max_capacity: 4,  // Tunable: smaller = deeper tree, better locality
            max_depth: 16,     // Prevents pathological cases
        }
    }
}

/// Internal node representation
/// Design choice: Box for heap allocation, reduces stack pressure
struct QuadTreeNode<T> {
    boundary: AABB,
    points: Vec<Point<T>>,
    // None if leaf, Some([SW, SE, NW, NE]) if subdivided
    children: Option<Box<[QuadTreeNode<T>; 4]>>,
    depth: usize,
}

impl<T: Clone> QuadTreeNode<T> {
    /// Creates a new leaf node
    fn new_leaf(boundary: AABB, depth: usize) -> Self {
        QuadTreeNode {
            boundary,
            points: Vec::with_capacity(4), // Pre-allocate for typical capacity
            children: None,
            depth,
        }
    }

    /// Determines which quadrant contains the point
    #[inline]
    fn get_quadrant(&self, x: f64, y: f64) -> Quadrant {
        let (cx, cy) = self.boundary.center();
        match (x < cx, y < cy) {
            (true, true)   => Quadrant::SouthWest,
            (false, true)  => Quadrant::SouthEast,
            (true, false)  => Quadrant::NorthWest,
            (false, false) => Quadrant::NorthEast,
        }
    }

    /// Creates child bounding boxes for subdivision
    fn create_child_boundaries(&self) -> [AABB; 4] {
        let (cx, cy) = self.boundary.center();
        [
            // SW
            AABB::new(self.boundary.min_x, self.boundary.min_y, cx, cy)
                .expect("SW boundary invalid"),
            // SE
            AABB::new(cx, self.boundary.min_y, self.boundary.max_x, cy)
                .expect("SE boundary invalid"),
            // NW
            AABB::new(self.boundary.min_x, cy, cx, self.boundary.max_y)
                .expect("NW boundary invalid"),
            // NE
            AABB::new(cx, cy, self.boundary.max_x, self.boundary.max_y)
                .expect("NE boundary invalid"),
        ]
    }

    /// Subdivides the node into 4 children
    fn subdivide(&mut self) {
        if self.children.is_some() {
            return; // Already subdivided
        }

        let child_boundaries = self.create_child_boundaries();
        let child_depth = self.depth + 1;

        // Create 4 children
        let children = Box::new([
            QuadTreeNode::new_leaf(child_boundaries[0], child_depth),
            QuadTreeNode::new_leaf(child_boundaries[1], child_depth),
            QuadTreeNode::new_leaf(child_boundaries[2], child_depth),
            QuadTreeNode::new_leaf(child_boundaries[3], child_depth),
        ]);

        self.children = Some(children);

        // Redistribute existing points to children
        // Use drain to avoid cloning and clear in one operation
        let points = std::mem::take(&mut self.points);
        for point in points {
            let quad = self.get_quadrant(point.x, point.y);
            // Safe unwrap: we just created children
            self.children.as_mut().unwrap()[quad as usize]
                .points.push(point);
        }
    }

    /// Inserts a point, subdividing if necessary
    fn insert(&mut self, point: Point<T>, config: &QuadTreeConfig) -> bool {
        // Point must be within boundary
        if !self.boundary.contains(point.x, point.y) {
            return false;
        }

        // If we have children, delegate to appropriate child
        if let Some(ref mut children) = self.children {
            let quad = self.get_quadrant(point.x, point.y);
            return children[quad as usize].insert(point, config);
        }

        // We're a leaf - add point
        self.points.push(point);

        // Check if we need to subdivide
        if self.points.len() > config.max_capacity && self.depth < config.max_depth {
            self.subdivide();
        }

        true
    }

    /// Range query: collect all points within query_range
    fn query_range(&self, query_range: &AABB, result: &mut Vec<Point<T>>) {
        // Early exit if no intersection
        if !self.boundary.intersects(query_range) {
            return;
        }

        // If leaf, check each point
        if self.children.is_none() {
            for point in &self.points {
                if query_range.contains(point.x, point.y) {
                    result.push(point.clone());
                }
            }
            return;
        }

        // Recurse on children
        if let Some(ref children) = self.children {
            for child in children.iter() {
                child.query_range(query_range, result);
            }
        }
    }
}

/// Public QuadTree interface
pub struct QuadTree<T> {
    root: QuadTreeNode<T>,
    config: QuadTreeConfig,
    count: usize,
}

impl<T: Clone> QuadTree<T> {
    /// Creates a new QuadTree with given boundary
    pub fn new(boundary: AABB) -> Self {
        QuadTree {
            root: QuadTreeNode::new_leaf(boundary, 0),
            config: QuadTreeConfig::default(),
            count: 0,
        }
    }

    /// Creates QuadTree with custom configuration
    pub fn with_config(boundary: AABB, config: QuadTreeConfig) -> Self {
        QuadTree {
            root: QuadTreeNode::new_leaf(boundary, 0),
            config,
            count: 0,
        }
    }

    /// Inserts a point into the tree
    pub fn insert(&mut self, point: Point<T>) -> bool {
        if self.root.insert(point, &self.config) {
            self.count += 1;
            true
        } else {
            false
        }
    }

    /// Queries all points within the given range
    pub fn query_range(&self, query_range: &AABB) -> Vec<Point<T>> {
        let mut result = Vec::new();
        self.root.query_range(query_range, &mut result);
        result
    }

    /// Returns total number of points
    pub fn len(&self) -> usize {
        self.count
    }

    /// Checks if tree is empty
    pub fn is_empty(&self) -> bool {
        self.count == 0
    }
}
```

### **3.2 Memory Layout Analysis**

**Rust Structure Size** (64-bit system):
```
QuadTreeNode<T>:
  - boundary: AABB           = 32 bytes (4 × f64)
  - points: Vec<Point<T>>    = 24 bytes (ptr, len, cap)
  - children: Option<Box>    = 8 bytes (pointer or null)
  - depth: usize             = 8 bytes
  TOTAL per node            = 72 bytes + Vec heap allocation

Point<T>:
  - x: f64                   = 8 bytes
  - y: f64                   = 8 bytes
  - data: T                  = sizeof(T)
  TOTAL                      = 16 + sizeof(T)
```

**Cache Implications**:
- Typical L1 cache line: 64 bytes
- Node fits in ~1.125 cache lines
- Sequential point access benefits from prefetching
- Children require pointer chase (potential cache miss)

**Why Box<[Node; 4]>?**
1. **Stack safety**: Prevents deep recursion stack overflow
2. **Allocation control**: Single allocation for 4 children
3. **Null optimization**: `Option<Box>` has no overhead (pointer stores tag)

---

### **3.3 Algorithmic Operations**

#### **3.3.1 Insertion Algorithm**

**Flowchart**:
```
┌─────────────────────┐
│  insert(point)      │
└──────────┬──────────┘
           │
           ▼
    ┌──────────────┐
    │ In boundary? │──No──► Return false
    └──────┬───────┘
           │Yes
           ▼
    ┌──────────────┐
    │ Has children?│──Yes──► Determine quadrant
    └──────┬───────┘         │
           │No               ▼
           │         ┌───────────────────┐
           │         │ Recurse on child  │
           │         └───────────────────┘
           ▼
    ┌──────────────┐
    │ Add to points│
    └──────┬───────┘
           │
           ▼
    ┌──────────────────┐
    │ Over capacity &  │──Yes──► Subdivide
    │ depth < max?     │         │
    └──────┬───────────┘         │
           │No                   ▼
           │              ┌──────────────┐
           │              │ Create 4     │
           │              │ children     │
           │              └──────┬───────┘
           │                     │
           │                     ▼
           │              ┌──────────────┐
           │              │ Redistribute │
           │              │ points       │
           │              └──────────────┘
           ▼
    ┌──────────────┐
    │ Return true  │
    └──────────────┘
```

**Time Complexity Analysis**:
- **Best Case**: O(1) - root is leaf with space
- **Average Case**: O(log N) for balanced distribution
- **Worst Case**: O(depth) = O(log N) or O(max_depth)
  - Pathological: All points at same location → O(max_depth)

**Space Complexity**:
- Tree: O(N) total across all nodes
- Each point stored once
- Internal nodes: ~N/capacity additional overhead

#### **3.3.2 Range Query Algorithm**

**Pruning Strategy**:
```rust
// Pseudocode for mental model
fn query(node, range) {
    if !node.boundary.intersects(range) {
        return;  // PRUNE: entire subtree eliminated
    }
    
    if node.is_leaf() {
        // Check each point individually
        for point in node.points {
            if range.contains(point) {
                collect(point);
            }
        }
    } else {
        // Recurse on all children (some may be pruned)
        for child in node.children {
            query(child, range);
        }
    }
}
```

**Performance Characteristics**:
- **Best Case**: O(k) where k = result size
  - Query range fully contained in single leaf
- **Average Case**: O(log N + k)
  - Visit log N nodes, collect k results
- **Worst Case**: O(N)
  - Query range covers entire space

**Optimization**: Early termination if range fully contains node:
```rust
fn query_optimized(&self, query_range: &AABB, result: &mut Vec<Point<T>>) {
    if !self.boundary.intersects(query_range) {
        return; // Prune
    }
    
    // NEW: If query fully contains this node's boundary
    if query_range.min_x <= self.boundary.min_x &&
       query_range.max_x >= self.boundary.max_x &&
       query_range.min_y <= self.boundary.min_y &&
       query_range.max_y >= self.boundary.max_y {
        // Collect all points in subtree without further checks
        self.collect_all(result);
        return;
    }
    
    // Standard logic...
}
```

---

### **3.4 C Implementation: Memory-Conscious Design**

```c
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <assert.h>

// Configuration constants
#define DEFAULT_CAPACITY 4
#define MAX_DEPTH 16
#define EPSILON 1e-9

// Axis-aligned bounding box
typedef struct {
    double min_x, min_y;
    double max_x, max_y;
} AABB;

// Point with generic data (void pointer)
typedef struct {
    double x, y;
    void* data;
} Point;

// Forward declaration
typedef struct QuadTreeNode QuadTreeNode;

// Node structure
struct QuadTreeNode {
    AABB boundary;
    Point* points;           // Dynamic array
    size_t point_count;
    size_t point_capacity;
    QuadTreeNode* children[4]; // NULL if leaf
    unsigned int depth;
};

// Tree configuration
typedef struct {
    size_t max_capacity;
    size_t max_depth;
} QuadTreeConfig;

// Public tree structure
typedef struct {
    QuadTreeNode* root;
    QuadTreeConfig config;
    size_t total_points;
} QuadTree;

//===== AABB Functions =====

static inline bool aabb_contains(const AABB* box, double x, double y) {
    return x >= box->min_x && x < box->max_x &&
           y >= box->min_y && y < box->max_y;
}

static inline bool aabb_intersects(const AABB* a, const AABB* b) {
    return !(a->max_x <= b->min_x || a->min_x >= b->max_x ||
             a->max_y <= b->min_y || a->min_y >= b->max_y);
}

static inline void aabb_center(const AABB* box, double* cx, double* cy) {
    *cx = (box->min_x + box->max_x) * 0.5;
    *cy = (box->min_y + box->max_y) * 0.5;
}

//===== Node Functions =====

// Determines quadrant index for point
static inline unsigned int get_quadrant(const QuadTreeNode* node, double x, double y) {
    double cx, cy;
    aabb_center(&node->boundary, &cx, &cy);
    
    unsigned int index = 0;
    if (x >= cx) index |= 1;  // East
    if (y >= cy) index |= 2;  // North
    return index;
}

// Creates a new leaf node
static QuadTreeNode* node_create(AABB boundary, unsigned int depth) {
    QuadTreeNode* node = (QuadTreeNode*)malloc(sizeof(QuadTreeNode));
    if (!node) return NULL;
    
    node->boundary = boundary;
    node->points = (Point*)malloc(DEFAULT_CAPACITY * sizeof(Point));
    if (!node->points) {
        free(node);
        return NULL;
    }
    
    node->point_count = 0;
    node->point_capacity = DEFAULT_CAPACITY;
    node->depth = depth;
    
    // Initialize children to NULL (leaf node)
    memset(node->children, 0, sizeof(node->children));
    
    return node;
}

// Subdivides a node into 4 children
static bool node_subdivide(QuadTreeNode* node) {
    if (node->children[0] != NULL) {
        return true; // Already subdivided
    }
    
    double cx, cy;
    aabb_center(&node->boundary, &cx, &cy);
    
    // Create child boundaries
    AABB children_bounds[4] = {
        {node->boundary.min_x, node->boundary.min_y, cx, cy},  // SW
        {cx, node->boundary.min_y, node->boundary.max_x, cy},  // SE
        {node->boundary.min_x, cy, cx, node->boundary.max_y},  // NW
        {cx, cy, node->boundary.max_x, node->boundary.max_y}   // NE
    };
    
    // Create children nodes
    for (int i = 0; i < 4; i++) {
        node->children[i] = node_create(children_bounds[i], node->depth + 1);
        if (!node->children[i]) {
            // Cleanup on failure
            for (int j = 0; j < i; j++) {
                free(node->children[j]->points);
                free(node->children[j]);
            }
            return false;
        }
    }
    
    // Redistribute points to children
    for (size_t i = 0; i < node->point_count; i++) {
        Point* p = &node->points[i];
        unsigned int quad = get_quadrant(node, p->x, p->y);
        
        QuadTreeNode* child = node->children[quad];
        
        // Ensure capacity
        if (child->point_count >= child->point_capacity) {
            size_t new_cap = child->point_capacity * 2;
            Point* new_points = (Point*)realloc(child->points, 
                                                new_cap * sizeof(Point));
            if (!new_points) {
                return false;
            }
            child->points = new_points;
            child->point_capacity = new_cap;
        }
        
        child->points[child->point_count++] = *p;
    }
    
    // Clear parent's points
    node->point_count = 0;
    
    return true;
}

// Inserts a point into a node
static bool node_insert(QuadTreeNode* node, Point point, 
                       const QuadTreeConfig* config) {
    if (!aabb_contains(&node->boundary, point.x, point.y)) {
        return false;
    }
    
    // If we have children, delegate
    if (node->children[0] != NULL) {
        unsigned int quad = get_quadrant(node, point.x, point.y);
        return node_insert(node->children[quad], point, config);
    }
    
    // Add point to this leaf
    if (node->point_count >= node->point_capacity) {
        size_t new_cap = node->point_capacity * 2;
        Point* new_points = (Point*)realloc(node->points, 
                                            new_cap * sizeof(Point));
        if (!new_points) {
            return false;
        }
        node->points = new_points;
        node->point_capacity = new_cap;
    }
    
    node->points[node->point_count++] = point;
    
    // Check if subdivision needed
    if (node->point_count > config->max_capacity && 
        node->depth < config->max_depth) {
        if (!node_subdivide(node)) {
            return false;
        }
    }
    
    return true;
}

// Range query helper
static void node_query_range(const QuadTreeNode* node, const AABB* range,
                            Point** results, size_t* count, size_t* capacity) {
    if (!aabb_intersects(&node->boundary, range)) {
        return; // Prune
    }
    
    // If leaf, check points
    if (node->children[0] == NULL) {
        for (size_t i = 0; i < node->point_count; i++) {
            Point* p = &node->points[i];
            if (aabb_contains(range, p->x, p->y)) {
                // Grow result array if needed
                if (*count >= *capacity) {
                    size_t new_cap = (*capacity) * 2;
                    Point* new_results = (Point*)realloc(*results, 
                                                        new_cap * sizeof(Point));
                    if (!new_results) {
                        return; // Allocation failed
                    }
                    *results = new_results;
                    *capacity = new_cap;
                }
                (*results)[(*count)++] = *p;
            }
        }
        return;
    }
    
    // Recurse on children
    for (int i = 0; i < 4; i++) {
        node_query_range(node->children[i], range, results, count, capacity);
    }
}

// Destroys node and all children
static void node_destroy(QuadTreeNode* node) {
    if (!node) return;
    
    // Recursively destroy children
    for (int i = 0; i < 4; i++) {
        if (node->children[i]) {
            node_destroy(node->children[i]);
        }
    }
    
    free(node->points);
    free(node);
}

//===== Public API =====

QuadTree* quadtree_create(AABB boundary) {
    QuadTree* tree = (QuadTree*)malloc(sizeof(QuadTree));
    if (!tree) return NULL;
    
    tree->config.max_capacity = DEFAULT_CAPACITY;
    tree->config.max_depth = MAX_DEPTH;
    tree->total_points = 0;
    
    tree->root = node_create(boundary, 0);
    if (!tree->root) {
        free(tree);
        return NULL;
    }
    
    return tree;
}

bool quadtree_insert(QuadTree* tree, Point point) {
    if (node_insert(tree->root, point, &tree->config)) {
        tree->total_points++;
        return true;
    }
    return false;
}

Point* quadtree_query_range(const QuadTree* tree, const AABB* range, 
                            size_t* result_count) {
    size_t capacity = 16;
    Point* results = (Point*)malloc(capacity * sizeof(Point));
    if (!results) {
        *result_count = 0;
        return NULL;
    }
    
    *result_count = 0;
    node_query_range(tree->root, range, &results, result_count, &capacity);
    
    return results;
}

void quadtree_destroy(QuadTree* tree) {
    if (!tree) return;
    node_destroy(tree->root);
    free(tree);
}

size_t quadtree_size(const QuadTree* tree) {
    return tree->total_points;
}
```

**C-Specific Optimizations**:
1. **Manual memory management**: Explicit control over allocations
2. **Cache-friendly**: Contiguous point array in each node
3. **Pointer arithmetic**: Fast child access via array indexing
4. **In-place operations**: Minimize copying

**Safety Considerations**:
- Always check `malloc`/`realloc` return values
- Initialize pointers to NULL
- Cleanup on partial failures
- Use `memset` for bulk initialization

---

### **3.5 Go Implementation: Concurrent-Safe Design**

```go
package quadtree

import (
    "errors"
    "math"
    "sync"
)

// AABB represents an axis-aligned bounding box
type AABB struct {
    MinX, MinY float64
    MaxX, MaxY float64
}

// NewAABB creates a validated AABB
func NewAABB(minX, minY, maxX, maxY float64) (*AABB, error) {
    if minX >= maxX || minY >= maxY {
        return nil, errors.New("invalid AABB: min must be < max")
    }
    return &AABB{
        MinX: minX,
        MinY: minY,
        MaxX: maxX,
        MaxY: maxY,
    }, nil
}

// Contains checks if point is within boundary
func (a *AABB) Contains(x, y float64) bool {
    return x >= a.MinX && x < a.MaxX && y >= a.MinY && y < a.MaxY
}

// Intersects checks if two AABBs overlap
func (a *AABB) Intersects(other *AABB) bool {
    return !(a.MaxX <= other.MinX || a.MinX >= other.MaxX ||
        a.MaxY <= other.MinY || a.MinY >= other.MaxY)
}

// Center returns the center point
func (a *AABB) Center() (float64, float64) {
    return (a.MinX + a.MaxX) * 0.5, (a.MinY + a.MaxY) * 0.5
}

// Point represents a 2D point with generic data
type Point struct {
    X, Y float64
    Data interface{}
}

// Quadrant enumeration
type Quadrant uint8

const (
    SouthWest Quadrant = iota
    SouthEast
    NorthWest
    NorthEast
)

// Config holds tree configuration
type Config struct {
    MaxCapacity int
    MaxDepth    int
}

// DefaultConfig returns sensible defaults
func DefaultConfig() Config {
    return Config{
        MaxCapacity: 4,
        MaxDepth:    16,
    }
}

// node represents internal tree structure
type node struct {
    boundary AABB
    points   []Point
    children [4]*node // nil if leaf
    depth    int
}

// newLeaf creates a leaf node
func newLeaf(boundary AABB, depth int) *node {
    return &node{
        boundary: boundary,
        points:   make([]Point, 0, 4), // Pre-allocate
        children: [4]*node{},
        depth:    depth,
    }
}

// getQuadrant determines which child contains point
func (n *node) getQuadrant(x, y float64) Quadrant {
    cx, cy := n.boundary.Center()
    
    switch {
    case x < cx && y < cy:
        return SouthWest
    case x >= cx && y < cy:
        return SouthEast
    case x < cx && y >= cy:
        return NorthWest
    default: // x >= cx && y >= cy
        return NorthEast
    }
}

// subdivide splits node into 4 children
func (n *node) subdivide() {
    if n.children[0] != nil {
        return // Already subdivided
    }
    
    cx, cy := n.boundary.Center()
    childDepth := n.depth + 1
    
    // Create children with proper boundaries
    n.children[SouthWest] = newLeaf(
        AABB{n.boundary.MinX, n.boundary.MinY, cx, cy}, childDepth)
    n.children[SouthEast] = newLeaf(
        AABB{cx, n.boundary.MinY, n.boundary.MaxX, cy}, childDepth)
    n.children[NorthWest] = newLeaf(
        AABB{n.boundary.MinX, cy, cx, n.boundary.MaxY}, childDepth)
    n.children[NorthEast] = newLeaf(
        AABB{cx, cy, n.boundary.MaxX, n.boundary.MaxY}, childDepth)
    
    // Redistribute points
    for _, point := range n.points {
        quad := n.getQuadrant(point.X, point.Y)
        n.children[quad].points = append(n.children[quad].points, point)
    }
    
    // Clear parent's points (help GC)
    n.points = nil
}

// insert adds point to node
func (n *node) insert(point Point, config *Config) bool {
    if !n.boundary.Contains(point.X, point.Y) {
        return false
    }
    
    // Delegate to child if subdivided
    if n.children[0] != nil {
        quad := n.getQuadrant(point.X, point.Y)
        return n.children[quad].insert(point, config)
    }
    
    // Add to leaf
    n.points = append(n.points, point)
    
    // Check subdivision
    if len(n.points) > config.MaxCapacity && n.depth < config.MaxDepth {
        n.subdivide()
    }
    
    return true
}

// queryRange collects points in range
func (n *node) queryRange(queryRange *AABB, results *[]Point) {
    if !n.boundary.Intersects(queryRange) {
        return // Prune
    }
    
    // Leaf: check points
    if n.children[0] == nil {
        for _, point := range n.points {
            if queryRange.Contains(point.X, point.Y) {
                *results = append(*results, point)
            }
        }
        return
    }
    
    // Internal: recurse
    for i := range n.children {
        if n.children[i] != nil {
            n.children[i].queryRange(queryRange, results)
        }
    }
}

// QuadTree is the public interface
type QuadTree struct {
    root   *node
    config Config
    count  int
    mu     sync.RWMutex // Optional: for concurrent access
}

// New creates a new QuadTree
func New(boundary AABB) *QuadTree {
    return &QuadTree{
        root:   newLeaf(boundary, 0),
        config: DefaultConfig(),
        count:  0,
    }
}

// NewWithConfig creates tree with custom config
func NewWithConfig(boundary AABB, config Config) *QuadTree {
    return &QuadTree{
        root:   newLeaf(boundary, 0),
        config: config,
        count:  0,
    }
}

// Insert adds a point to the tree
func (qt *QuadTree) Insert(point Point) bool {
    qt.mu.Lock()
    defer qt.mu.Unlock()
    
    if qt.root.insert(point, &qt.config) {
        qt.count++
        return true
    }
    return false
}

// QueryRange finds all points in range
func (qt *QuadTree) QueryRange(queryRange *AABB) []Point {
    qt.mu.RLock()
    defer qt.mu.RUnlock()
    
    results := make([]Point, 0, 16) // Pre-allocate
    qt.root.queryRange(queryRange, &results)
    return results
}

// Size returns total number of points
func (qt *QuadTree) Size() int {
    qt.mu.RLock()
    defer qt.mu.RUnlock()
    return qt.count
}
```

**Go-Specific Features**:
1. **Concurrency**: `sync.RWMutex` for thread-safe operations
2. **Interfaces**: `interface{}` for generic data (or use type parameters in Go 1.18+)
3. **Garbage Collection**: Automatic memory management
4. **Slice growth**: Dynamic array handling via `append`

---

## **4. Octrees: 3D Extension**

### **4.1 Conceptual Framework**

**Octree = QuadTree + Z-axis**

```
         Top Half (z >= center_z)
         ┌─────────┬─────────┐
        /│   TNW   │   TNE   │/
       / │         │         │/
      /  ├─────────┼─────────┤
     /   │   TSW   │   TSE   │/
    /    └─────────┴─────────┘
   /
  /     Bottom Half (z < center_z)
 /      ┌─────────┬─────────┐
/      /│   BNW   │   BNE   │/
      / │         │         │/
     /  ├─────────┼─────────┤
    /   │   BSW   │   BSE   │/
   /    └─────────┴─────────┘
  /
 
 Octant Indexing:
 0: BSW (x<cx, y<cy, z<cz)
 1: BSE (x≥cx, y<cy, z<cz)
 2: BNW (x<cx, y≥cy, z<cz)
 3: BNE (x≥cx, y≥cy, z<cz)
 4: TSW (x<cx, y<cy, z≥cz)
 5: TSE (x≥cx, y<cy, z≥cz)
 6: TNW (x<cx, y≥cy, z≥cz)
 7: TNE (x≥cx, y≥cy, z≥cz)
```

### **4.2 Rust Octree Implementation**

```rust
/// 3D Axis-Aligned Bounding Box
#[derive(Debug, Clone, Copy)]
pub struct AABB3D {
    pub min_x: f64,
    pub min_y: f64,
    pub min_z: f64,
    pub max_x: f64,
    pub max_y: f64,
    pub max_z: f64,
}

impl AABB3D {
    pub fn new(min_x: f64, min_y: f64, min_z: f64,
               max_x: f64, max_y: f64, max_z: f64) -> Result<Self, &'static str> {
        if min_x >= max_x || min_y >= max_y || min_z >= max_z {
            return Err("Invalid AABB3D: min must be < max");
        }
        Ok(AABB3D { min_x, min_y, min_z, max_x, max_y, max_z })
    }

    #[inline]
    pub fn contains(&self, x: f64, y: f64, z: f64) -> bool {
        x >= self.min_x && x < self.max_x &&
        y >= self.min_y && y < self.max_y &&
        z >= self.min_z && z < self.max_z
    }

    #[inline]
    pub fn intersects(&self, other: &AABB3D) -> bool {
        !(self.max_x <= other.min_x || self.min_x >= other.max_x ||
          self.max_y <= other.min_y || self.min_y >= other.max_y ||
          self.max_z <= other.min_z || self.min_z >= other.max_z)
    }

    #[inline]
    pub fn center(&self) -> (f64, f64, f64) {
        (
            (self.min_x + self.max_x) * 0.5,
            (self.min_y + self.max_y) * 0.5,
            (self.min_z + self.max_z) * 0.5,
        )
    }
}

/// 3D point with data
#[derive(Debug, Clone)]
pub struct Point3D<T> {
    pub x: f64,
    pub y: f64,
    pub z: f64,
    pub data: T,
}

/// Octant indices
#[repr(u8)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Octant {
    BottomSouthWest = 0,
    BottomSouthEast = 1,
    BottomNorthWest = 2,
    BottomNorthEast = 3,
    TopSouthWest = 4,
    TopSouthEast = 5,
    TopNorthWest = 6,
    TopNorthEast = 7,
}

pub struct OctreeConfig {
    pub max_capacity: usize,
    pub max_depth: usize,
}

impl Default for OctreeConfig {
    fn default() -> Self {
        OctreeConfig {
            max_capacity: 8,
            max_depth: 16,
        }
    }
}

struct OctreeNode<T> {
    boundary: AABB3D,
    points: Vec<Point3D<T>>,
    children: Option<Box<[OctreeNode<T>; 8]>>,
    depth: usize,
}

impl<T: Clone> OctreeNode<T> {
    fn new_leaf(boundary: AABB3D, depth: usize) -> Self {
        OctreeNode {
            boundary,
            points: Vec::with_capacity(8),
            children: None,
            depth,
        }
    }

    #[inline]
    fn get_octant(&self, x: f64, y: f64, z: f64) -> Octant {
        let (cx, cy, cz) = self.boundary.center();
        
        let mut index: u8 = 0;
        if x >= cx { index |= 1; } // East
        if y >= cy { index |= 2; } // North
        if z >= cz { index |= 4; } // Top
        
        // Safe: index is 0-7
        unsafe { std::mem::transmute(index) }
    }

    fn subdivide(&mut self) {
        if self.children.is_some() {
            return;
        }

        let (cx, cy, cz) = self.boundary.center();
        let child_depth = self.depth + 1;

        // Create 8 octant boundaries
        let octant_bounds = [
            AABB3D::new(self.boundary.min_x, self.boundary.min_y, self.boundary.min_z, cx, cy, cz).unwrap(),
            AABB3D::new(cx, self.boundary.min_y, self.boundary.min_z, self.boundary.max_x, cy, cz).unwrap(),
            AABB3D::new(self.boundary.min_x, cy, self.boundary.min_z, cx, self.boundary.max_y, cz).unwrap(),
            AABB3D::new(cx, cy, self.boundary.min_z, self.boundary.max_x, self.boundary.max_y, cz).unwrap(),
            AABB3D::new(self.boundary.min_x, self.boundary.min_y, cz, cx, cy, self.boundary.max_z).unwrap(),
            AABB3D::new(cx, self.boundary.min_y, cz, self.boundary.max_x, cy, self.boundary.max_z).unwrap(),
            AABB3D::new(self.boundary.min_x, cy, cz, cx, self.boundary.max_y, self.boundary.max_z).unwrap(),
            AABB3D::new(cx, cy, cz, self.boundary.max_x, self.boundary.max_y, self.boundary.max_z).unwrap(),
        ];

        let children = Box::new([
            OctreeNode::new_leaf(octant_bounds[0], child_depth),
            OctreeNode::new_leaf(octant_bounds[1], child_depth),
            OctreeNode::new_leaf(octant_bounds[2], child_depth),
            OctreeNode::new_leaf(octant_bounds[3], child_depth),
            OctreeNode::new_leaf(octant_bounds[4], child_depth),
            OctreeNode::new_leaf(octant_bounds[5], child_depth),
            OctreeNode::new_leaf(octant_bounds[6], child_depth),
            OctreeNode::new_leaf(octant_bounds[7], child_depth),
        ]);

        self.children = Some(children);

        // Redistribute points
        let points = std::mem::take(&mut self.points);
        for point in points {
            let octant = self.get_octant(point.x, point.y, point.z);
            self.children.as_mut().unwrap()[octant as usize].points.push(point);
        }
    }

    fn insert(&mut self, point: Point3D<T>, config: &OctreeConfig) -> bool {
        if !self.boundary.contains(point.x, point.y, point.z) {
            return false;
        }

        if let Some(ref mut children) = self.children {
            let octant = self.get_octant(point.x, point.y, point.z);
            return children[octant as usize].insert(point, config);
        }

        self.points.push(point);

        if self.points.len() > config.max_capacity && self.depth < config.max_depth {
            self.subdivide();
        }

        true
    }

    fn query_range(&self, query_range: &AABB3D, result: &mut Vec<Point3D<T>>) {
        if !self.boundary.intersects(query_range) {
            return;
        }

        if self.children.is_none() {
            for point in &self.points {
                if query_range.contains(point.x, point.y, point.z) {
                    result.push(point.clone());
                }
            }
            return;
        }

        if let Some(ref children) = self.children {
            for child in children.iter() {
                child.query_range(query_range, result);
            }
        }
    }
}

pub struct Octree<T> {
    root: OctreeNode<T>,
    config: OctreeConfig,
    count: usize,
}

impl<T: Clone> Octree<T> {
    pub fn new(boundary: AABB3D) -> Self {
        Octree {
            root: OctreeNode::new_leaf(boundary, 0),
            config: OctreeConfig::default(),
            count: 0,
        }
    }

    pub fn insert(&mut self, point: Point3D<T>) -> bool {
        if self.root.insert(point, &self.config) {
            self.count += 1;
            true
        } else {
            false
        }
    }

    pub fn query_range(&self, query_range: &AABB3D) -> Vec<Point3D<T>> {
        let mut result = Vec::new();
        self.root.query_range(query_range, &mut result);
        result
    }

    pub fn len(&self) -> usize {
        self.count
    }
}
```

**Key Differences from QuadTree**:
1. **8 children** instead of 4
2. **3D bounding box** (6 planes vs 4)
3. **Octant calculation**: 3-bit index (x|y|z flags)
4. **Memory footprint**: ~2× per node vs QuadTree

---

## **5. Performance Engineering**

### **5.1 Time Complexity Summary**

| Operation | Best | Average | Worst | Notes |
|-----------|------|---------|-------|-------|
| Insert | O(1) | O(log N) | O(max_depth) | Depends on depth |
| Range Query | O(k) | O(log N + k) | O(N) | k = result size |
| Point Query | O(1) | O(log N) | O(max_depth) | Single point lookup |
| Nearest Neighbor | O(log N) | O(log N) | O(N) | With pruning |
| Build (batch) | O(N log N) | O(N log N) | O(N²) | Incremental worse |

**Critical Insight**: Performance degrades with:
- **Clustered data**: Many points in same region → deep subdivision
- **Skewed distribution**: Unbalanced tree structure
- **Large query ranges**: Less pruning benefit

### **5.2 Space Complexity**

**QuadTree**:
- Nodes: O(N / capacity) internal + O(1) leaf storage
- Worst case: O(N × depth) if all points in same location
- Typical: O(N) with constant overhead

**Octree**:
- 2× memory per node vs QuadTree
- Same asymptotic bounds

### **5.3 Cache Performance Analysis**

**Memory Access Pattern**:
```
Query execution on balanced tree:
1. Root access         → Cold cache (miss)
2. Child access        → Potential miss (pointer chase)
3. Leaf points access  → Sequential scan (hits if array small)

Cache lines utilized:
- Node structure: ~1-2 cache lines
- Point array: Depends on capacity × sizeof(Point)
```

**Optimization Strategies**:

1. **Structure-of-Arrays (SoA)** layout:
```rust
// Instead of:
struct Node {
    points: Vec<Point>,  // Each point has x, y, data
}

// Use:
struct Node {
    x_coords: Vec<f64>,
    y_coords: Vec<f64>,
    data: Vec<T>,
}
```
**Benefit**: SIMD-friendly, better spatial locality

2. **Pointer-free** (Morton encoding):
```rust
// Encode 2D coordinates into 1D index
fn morton_encode(x: u32, y: u32) -> u64 {
    let mut result: u64 = 0;
    for i in 0..32 {
        result |= ((x & (1 << i)) as u64) << i;
        result |= ((y & (1 << i)) as u64) << (i + 1);
    }
    result
}
```
**Benefit**: Implicit tree structure, cache-friendly iteration

### **5.4 Allocation Patterns**

**Rust**:
```rust
// Pre-allocate for known size
let mut tree = QuadTree::new(boundary);
tree.root.points.reserve(1000);  // Avoid reallocs

// Bulk operations
let points: Vec<Point<_>> = generate_points();
for point in points {
    tree.insert(point);  // Still O(log N) each
}
```

**C** - Custom allocator:
```c
// Arena allocator for nodes
typedef struct {
    char* buffer;
    size_t used;
    size_t capacity;
} Arena;

QuadTreeNode* arena_alloc_node(Arena* arena) {
    if (arena->used + sizeof(QuadTreeNode) > arena->capacity) {
        return NULL;  // Or grow arena
    }
    QuadTreeNode* node = (QuadTreeNode*)(arena->buffer + arena->used);
    arena->used += sizeof(QuadTreeNode);
    return node;
}
```

**Go** - Sync.Pool for temporary objects:
```go
var pointPool = sync.Pool{
    New: func() interface{} {
        return make([]Point, 0, 16)
    },
}

func (qt *QuadTree) QueryRange(queryRange *AABB) []Point {
    results := pointPool.Get().([]Point)
    results = results[:0]  // Reset length
    defer func() {
        pointPool.Put(results)
    }()
    
    qt.root.queryRange(queryRange, &results)
    
    // Copy to return (caller owns)
    ret := make([]Point, len(results))
    copy(ret, results)
    return ret
}
```

---

## **6. Production Implementations**

### **6.1 Loose QuadTree (Game Development)**

**Problem**: Objects have size, not just points
**Solution**: Expand node boundaries by object radius

```rust
pub struct LooseQuadTree<T> {
    root: LooseNode<T>,
    expansion_factor: f64,  // Typically 2.0
}

struct LooseNode<T> {
    // Logical boundary (for subdivision)
    tight_boundary: AABB,
    // Storage boundary (expanded)
    loose_boundary: AABB,
    objects: Vec<GameObject<T>>,
    children: Option<Box<[LooseNode<T>; 4]>>,
}

struct GameObject<T> {
    position: (f64, f64),
    radius: f64,
    data: T,
}

impl<T> LooseNode<T> {
    fn compute_loose_boundary(tight: &AABB, factor: f64) -> AABB {
        let half_width = (tight.max_x - tight.min_x) * 0.5;
        let half_height = (tight.max_y - tight.min_y) * 0.5;
        let cx = (tight.min_x + tight.max_x) * 0.5;
        let cy = (tight.min_y + tight.max_y) * 0.5;
        
        let expansion = factor - 1.0;
        let expand_x = half_width * expansion;
        let expand_y = half_height * expansion;
        
        AABB {
            min_x: tight.min_x - expand_x,
            min_y: tight.min_y - expand_y,
            max_x: tight.max_x + expand_x,
            max_y: tight.max_y + expand_y,
        }
    }
    
    fn fits_in_loose_boundary(&self, obj: &GameObject<T>) -> bool {
        obj.position.0 - obj.radius >= self.loose_boundary.min_x &&
        obj.position.0 + obj.radius < self.loose_boundary.max_x &&
        obj.position.1 - obj.radius >= self.loose_boundary.min_y &&
        obj.position.1 + obj.radius < self.loose_boundary.max_y
    }
}
```

**Use Case**: Collision detection, spatial hashing in game engines

### **6.2 Region QuadTree (Image Compression)**

**Concept**: Subdivide until uniform color region

```rust
pub struct RegionQuadTree {
    root: RegionNode,
}

struct RegionNode {
    boundary: AABB,
    color: Option<RGB>,  // None if subdivided
    children: Option<Box<[RegionNode; 4]>>,
}

impl RegionNode {
    fn build_from_image(image: &Image, boundary: AABB, threshold: f64) -> Self {
        let pixels = image.get_region(&boundary);
        
        // Check uniformity
        if is_uniform(&pixels, threshold) {
            return RegionNode {
                boundary,
                color: Some(average_color(&pixels)),
                children: None,
            };
        }
        
        // Subdivide
        let children = create_child_nodes(image, &boundary, threshold);
        RegionNode {
            boundary,
            color: None,
            children: Some(Box::new(children)),
        }
    }
}
```

**Applications**: JPEG2000, quadtree textures, LOD systems

---

## **7. Advanced Techniques**

### **7.1 Nearest Neighbor Search**

**Algorithm**: Branch-and-bound with priority queue

```rust
use std::collections::BinaryHeap;
use std::cmp::Ordering;

#[derive(Copy, Clone)]
struct SearchCandidate<'a, T> {
    node: &'a QuadTreeNode<T>,
    min_dist: f64,
}

impl<'a, T> PartialEq for SearchCandidate<'a, T> {
    fn eq(&self, other: &Self) -> bool {
        self.min_dist == other.min_dist
    }
}

impl<'a, T> Eq for SearchCandidate<'a, T> {}

impl<'a, T> PartialOrd for SearchCandidate<'a, T> {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        // Reverse for min-heap
        other.min_dist.partial_cmp(&self.min_dist)
    }
}

impl<'a, T> Ord for SearchCandidate<'a, T> {
    fn cmp(&self, other: &Self) -> Ordering {
        self.partial_cmp(other).unwrap_or(Ordering::Equal)
    }
}

impl<T: Clone> QuadTree<T> {
    pub fn nearest_neighbor(&self, query_x: f64, query_y: f64) -> Option<Point<T>> {
        let mut best_point: Option<Point<T>> = None;
        let mut best_dist_sq = f64::INFINITY;
        
        let mut heap = BinaryHeap::new();
        heap.push(SearchCandidate {
            node: &self.root,
            min_dist: 0.0,
        });
        
        while let Some(candidate) = heap.pop() {
            // Prune if this node can't improve best
            if candidate.min_dist >= best_dist_sq {
                continue;
            }
            
            let node = candidate.node;
            
            // Leaf: check points
            if node.children.is_none() {
                for point in &node.points {
                    let dx = point.x - query_x;
                    let dy = point.y - query_y;
                    let dist_sq = dx * dx + dy * dy;
                    
                    if dist_sq < best_dist_sq {
                        best_dist_sq = dist_sq;
                        best_point = Some(point.clone());
                    }
                }
            } else {
                // Add children to heap with priority
                if let Some(ref children) = node.children {
                    for child in children.iter() {
                        let min_dist = min_distance_to_aabb(
                            query_x, query_y, &child.boundary
                        );
                        
                        if min_dist < best_dist_sq {
                            heap.push(SearchCandidate {
                                node: child,
                                min_dist,
                            });
                        }
                    }
                }
            }
        }
        
        best_point
    }
}

fn min_distance_to_aabb(px: f64, py: f64, box_: &AABB) -> f64 {
    let dx = if px < box_.min_x {
        box_.min_x - px
    } else if px > box_.max_x {
        px - box_.max_x
    } else {
        0.0
    };
    
    let dy = if py < box_.min_y {
        box_.min_y - py
    } else if py > box_.max_y {
        py - box_.max_y
    } else {
        0.0
    };
    
    dx * dx + dy * dy
}
```

**Complexity**: O(log N) average, O(N) worst case

---

### **7.2 Dynamic Updates & Balancing**

**Challenge**: Objects move → tree becomes unbalanced

**Strategy 1**: Lazy deletion + periodic rebuild
```rust
impl<T: Clone> QuadTree<T> {
    pub fn remove(&mut self, x: f64, y: f64) -> Option<Point<T>> {
        // Mark for deletion
        self.deleted_points.push((x, y));
        
        if self.deleted_points.len() > self.count / 4 {
            self.rebuild();
        }
        
        // Actual removal logic...
        None
    }
    
    fn rebuild(&mut self) {
        let all_points = self.collect_all_points();
        *self = QuadTree::new(self.root.boundary);
        for point in all_points {
            self.insert(point);
        }
    }
}
```

**Strategy 2**: Adaptive capacity
```rust
fn adaptive_subdivide(&mut self) {
    // Calculate local density
    let density = self.points.len() as f64 / self.boundary.area();
    let adaptive_capacity = (8.0 / density).max(4.0).min(32.0) as usize;
    
    if self.points.len() > adaptive_capacity {
        self.subdivide();
    }
}
```

---

## **8. Real-World Applications**

### **8.1 Spatial Databases (PostGIS)**

QuadTrees power spatial indices:
- **R-Tree variant**: Hierarchical bounding boxes
- **Query types**: ST_Intersects, ST_Within, ST_Distance
- **Optimization**: Bulk loading, Hilbert curve ordering

### **8.2 Game Engines (Unity, Unreal)**

**Use cases**:
- Collision detection broad phase
- Frustum culling (what's visible?)
- AI pathfinding spatial queries

**Example**: Unity's Physics2D.OverlapAreaAll()

### **8.3 Ray Tracing (Octrees)**

**Acceleration structure** for 3D rendering:
```rust
fn ray_trace(ray: &Ray, octree: &Octree<Triangle>) -> Option<Hit> {
    let mut stack = vec![(octree.root, ray.t_min, ray.t_max)];
    let mut closest_hit = None;
    
    while let Some((node, t_min, t_max)) = stack.pop() {
        if !ray.intersects_aabb(&node.boundary, t_min, t_max) {
            continue;
        }
        
        if node.children.is_none() {
            // Leaf: test triangles
            for triangle in &node.triangles {
                if let Some(hit) = ray.intersect_triangle(triangle) {
                    if hit.t < closest_hit.as_ref().map_or(f64::INFINITY, |h| h.t) {
                        closest_hit = Some(hit);
                    }
                }
            }
        } else {
            // Push children sorted by ray direction
            for child in sorted_children(&node, &ray) {
                stack.push((child, t_min, t_max));
            }
        }
    }
    
    closest_hit
}
```

### **8.4 Scientific Computing**

**N-body simulation**:
```rust
// Barnes-Hut algorithm for gravitational simulation
fn compute_force(body: &Body, octree: &Octree<Body>, theta: f64) -> Vector3 {
    let mut force = Vector3::zero();
    let mut stack = vec![&octree.root];
    
    while let Some(node) = stack.pop() {
        let (cx, cy, cz) = node.boundary.center();
        let dx = cx - body.x;
        let dy = cy - body.y;
        let dz = cz - body.z;
        let dist = (dx*dx + dy*dy + dz*dz).sqrt();
        
        let width = node.boundary.max_x - node.boundary.min_x;
        
        // Far enough? Treat as single mass
        if width / dist < theta {
            force += compute_force_from_center_of_mass(body, node);
        } else if node.is_leaf() {
            // Close: compute exactly
            for other in &node.bodies {
                force += compute_force_between(body, other);
            }
        } else {
            // Descend
            for child in &node.children {
                stack.push(child);
            }
        }
    }
    
    force
}
```

---

## **Key Takeaways for Mastery**

1. **Spatial decomposition is problem-dependent**: Choose capacity, depth based on data distribution

2. **Cache is king**: Structure layout matters more than algorithm in practice

3. **Balance vs. simplicity**: Point-based quadtrees are simple; variants handle complexity

4. **Query patterns drive design**: Optimize for your common case (many small queries vs. few large)

5. **Hardware awareness**: SIMD, cache lines, memory bandwidth - know your bottlenecks

6. **Production requires**:
   - Error handling (allocation failures)
   - Configuration tunability
   - Instrumentation (profiling hooks)
   - Testing (edge cases, pathological inputs)

---

**Mental Model**: Think of QuadTrees/Octrees as "spatial binary search" - you're trading O(log N) query time for O(N) build time and space. Master when this trade-off makes sense.

**Next Steps**: Implement these from scratch, benchmark against naive approaches, profile with real data distributions. Understanding comes from building, breaking, and optimizing.