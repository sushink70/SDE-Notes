# Comprehensive Guide to Geometry Patterns in Competitive Programming

## Foundation: What is Computational Geometry?

**Computational Geometry** is the branch of computer science that studies algorithms for solving geometric problems. In competitive programming, these problems involve points, lines, polygons, circles, and their relationships in 2D or 3D space.

Before we dive deep, let's establish the fundamental building blocks:

---

## 1. Core Geometric Primitives

### 1.1 Point Representation

A **point** is a location in space defined by coordinates. In 2D: `(x, y)`, in 3D: `(x, y, z)`.

```rust
// Rust: Using a struct for clarity and type safety
#[derive(Debug, Clone, Copy, PartialEq)]
struct Point {
    x: i64,  // Using i64 to avoid floating-point precision issues
    y: i64,
}

impl Point {
    fn new(x: i64, y: i64) -> Self {
        Point { x, y }
    }
}
```

```go
// Go: Simple struct
type Point struct {
    X, Y int64
}

func NewPoint(x, y int64) Point {
    return Point{X: x, Y: y}
}
```

```c
// C: Struct definition
typedef struct {
    long long x;
    long long y;
} Point;

Point create_point(long long x, long long y) {
    Point p = {x, y};
    return p;
}
```

**Why `i64`/`int64`/`long long`?** Integer coordinates avoid floating-point precision errors. When you must use floats, be aware of epsilon comparisons.

---

### 1.2 Vector Operations

A **vector** represents direction and magnitude. In geometry, we often treat the difference between two points as a vector.

**Key Vector Operations:**

1. **Dot Product** (scalar product): Measures how much two vectors align
   - Formula: `A · B = Ax*Bx + Ay*By`
   - Geometric meaning: `A · B = |A| * |B| * cos(θ)` where θ is angle between vectors
   - If dot product = 0 → vectors are perpendicular
   - If dot product > 0 → acute angle
   - If dot product < 0 → obtuse angle

2. **Cross Product** (in 2D, returns scalar): Measures rotational relationship
   - Formula: `A × B = Ax*By - Ay*Bx`
   - Geometric meaning: Area of parallelogram formed by A and B (signed)
   - If cross product > 0 → B is counter-clockwise from A
   - If cross product < 0 → B is clockwise from A
   - If cross product = 0 → vectors are collinear (parallel)

```rust
impl Point {
    // Vector from this point to another
    fn subtract(&self, other: &Point) -> Point {
        Point {
            x: self.x - other.x,
            y: self.y - other.y,
        }
    }
    
    fn dot(&self, other: &Point) -> i64 {
        self.x * other.x + self.y * other.y
    }
    
    fn cross(&self, other: &Point) -> i64 {
        self.x * other.y - self.y * other.x
    }
    
    fn magnitude_squared(&self) -> i64 {
        self.x * self.x + self.y * self.y
    }
}
```

```go
func (p Point) Subtract(other Point) Point {
    return Point{X: p.X - other.X, Y: p.Y - other.Y}
}

func (p Point) Dot(other Point) int64 {
    return p.X*other.X + p.Y*other.Y
}

func (p Point) Cross(other Point) int64 {
    return p.X*other.Y - p.Y*other.X
}

func (p Point) MagnitudeSquared() int64 {
    return p.X*p.X + p.Y*p.Y
}
```

```c
Point subtract_points(Point p1, Point p2) {
    Point result = {p1.x - p2.x, p1.y - p2.y};
    return result;
}

long long dot_product(Point a, Point b) {
    return a.x * b.x + a.y * b.y;
}

long long cross_product(Point a, Point b) {
    return a.x * b.y - a.y * b.x;
}

long long magnitude_squared(Point p) {
    return p.x * p.x + p.y * p.y;
}
```

**Mental Model:** Think of cross product as a "turning sensor" - it tells you which way you turn when going from vector A to vector B.

---

## 2. Fundamental Geometric Patterns

### Pattern 2.1: Orientation Test (CCW/CW/Collinear)

**Problem:** Given three points P, Q, R, determine their orientation.

**The orientation of an ordered triplet of points** can be:
- **Counter-clockwise (CCW)**: Positive turn
- **Clockwise (CW)**: Negative turn  
- **Collinear**: No turn (points are on same line)

**Algorithm:** Use cross product of vectors (Q-P) and (R-P)

```
Orientation = (Q-P) × (R-P)
```

**Flowchart:**
```
Start
  ↓
Compute vector PQ = Q - P
  ↓
Compute vector PR = R - P
  ↓
Compute cross = PQ × PR
  ↓
cross > 0? → Counter-Clockwise
cross < 0? → Clockwise
cross = 0? → Collinear
  ↓
End
```

```rust
#[derive(Debug, PartialEq)]
enum Orientation {
    Clockwise,
    CounterClockwise,
    Collinear,
}

fn orientation(p: &Point, q: &Point, r: &Point) -> Orientation {
    let pq = q.subtract(p);
    let pr = r.subtract(p);
    let cross = pq.cross(&pr);
    
    match cross.cmp(&0) {
        std::cmp::Ordering::Greater => Orientation::CounterClockwise,
        std::cmp::Ordering::Less => Orientation::Clockwise,
        std::cmp::Ordering::Equal => Orientation::Collinear,
    }
}
```

```go
type Orientation int

const (
    Clockwise Orientation = iota
    CounterClockwise
    Collinear
)

func GetOrientation(p, q, r Point) Orientation {
    pq := q.Subtract(p)
    pr := r.Subtract(p)
    cross := pq.Cross(pr)
    
    if cross > 0 {
        return CounterClockwise
    } else if cross < 0 {
        return Clockwise
    }
    return Collinear
}
```

```c
typedef enum {
    CLOCKWISE = -1,
    COLLINEAR = 0,
    COUNTER_CLOCKWISE = 1
} Orientation;

Orientation get_orientation(Point p, Point q, Point r) {
    Point pq = subtract_points(q, p);
    Point pr = subtract_points(r, p);
    long long cross = cross_product(pq, pr);
    
    if (cross > 0) return COUNTER_CLOCKWISE;
    if (cross < 0) return CLOCKWISE;
    return COLLINEAR;
}
```

**Time Complexity:** O(1)  
**Space Complexity:** O(1)

**Applications:**
- Convex hull algorithms
- Line segment intersection
- Polygon containment tests

---

### Pattern 2.2: Line Segment Intersection

**Problem:** Given two line segments AB and CD, determine if they intersect.

**Conceptual Approach:**
Two segments intersect if and only if one of the following is true:
1. **General case:** A and B are on opposite sides of line CD, AND C and D are on opposite sides of line AB
2. **Special case:** A, B, C, D are collinear and their projections overlap

**Algorithm Steps:**
1. Find orientation of (C, D, A) and (C, D, B)
2. Find orientation of (A, B, C) and (A, B, D)
3. If orientations differ in both checks → segments intersect (general case)
4. If any triplet is collinear → check if point lies on segment (special case)

**Helper Function: Point on Segment** (for collinear case)
```rust
fn on_segment(p: &Point, q: &Point, r: &Point) -> bool {
    // Check if q lies on segment pr (given they're collinear)
    q.x <= p.x.max(r.x) && q.x >= p.x.min(r.x) &&
    q.y <= p.y.max(r.y) && q.y >= p.y.min(r.y)
}
```

**Complete Intersection Test:**
```rust
fn segments_intersect(a: &Point, b: &Point, c: &Point, d: &Point) -> bool {
    let o1 = orientation(a, b, c);
    let o2 = orientation(a, b, d);
    let o3 = orientation(c, d, a);
    let o4 = orientation(c, d, b);
    
    // General case: different orientations
    if o1 != o2 && o3 != o4 {
        return true;
    }
    
    // Special cases: collinear points
    if o1 == Orientation::Collinear && on_segment(a, c, b) { return true; }
    if o2 == Orientation::Collinear && on_segment(a, d, b) { return true; }
    if o3 == Orientation::Collinear && on_segment(c, a, d) { return true; }
    if o4 == Orientation::Collinear && on_segment(c, b, d) { return true; }
    
    false
}
```

```go
func OnSegment(p, q, r Point) bool {
    return q.X <= max(p.X, r.X) && q.X >= min(p.X, r.X) &&
           q.Y <= max(p.Y, r.Y) && q.Y >= min(p.Y, r.Y)
}

func SegmentsIntersect(a, b, c, d Point) bool {
    o1 := GetOrientation(a, b, c)
    o2 := GetOrientation(a, b, d)
    o3 := GetOrientation(c, d, a)
    o4 := GetOrientation(c, d, b)
    
    if o1 != o2 && o3 != o4 {
        return true
    }
    
    if o1 == Collinear && OnSegment(a, c, b) { return true }
    if o2 == Collinear && OnSegment(a, d, b) { return true }
    if o3 == Collinear && OnSegment(c, a, d) { return true }
    if o4 == Collinear && OnSegment(c, b, d) { return true }
    
    return false
}

func min(a, b int64) int64 {
    if a < b { return a }
    return b
}

func max(a, b int64) int64 {
    if a > b { return a }
    return b
}
```

```c
int on_segment(Point p, Point q, Point r) {
    return q.x <= (p.x > r.x ? p.x : r.x) && 
           q.x >= (p.x < r.x ? p.x : r.x) &&
           q.y <= (p.y > r.y ? p.y : r.y) && 
           q.y >= (p.y < r.y ? p.y : r.y);
}

int segments_intersect(Point a, Point b, Point c, Point d) {
    Orientation o1 = get_orientation(a, b, c);
    Orientation o2 = get_orientation(a, b, d);
    Orientation o3 = get_orientation(c, d, a);
    Orientation o4 = get_orientation(c, d, b);
    
    if (o1 != o2 && o3 != o4) {
        return 1;
    }
    
    if (o1 == COLLINEAR && on_segment(a, c, b)) return 1;
    if (o2 == COLLINEAR && on_segment(a, d, b)) return 1;
    if (o3 == COLLINEAR && on_segment(c, a, d)) return 1;
    if (o4 == COLLINEAR && on_segment(c, b, d)) return 1;
    
    return 0;
}
```

**Time Complexity:** O(1)  
**Space Complexity:** O(1)

**Visualization:**
```
Case 1 (Intersect):        Case 2 (Don't intersect):
    A                           A---B
     \                              
      \  C                          C
       X                             \
      /  \                            \
     B    D                            D

Case 3 (Collinear overlap):
    A-------C===D---B
    (segments AC and CD overlap at C-D)
```

---

### Pattern 2.3: Point in Polygon Test

**Problem:** Given a point P and a polygon (defined by vertices), determine if P lies inside the polygon.

**Algorithm: Ray Casting**

**Intuition:** Draw a horizontal ray from point P to infinity. Count how many times this ray crosses the polygon boundary:
- **Odd count** → Point is inside
- **Even count** → Point is outside

**Why does this work?** Every time you cross a boundary, you toggle between inside and outside. Starting from outside (at infinity), odd crossings mean you're inside.

**Edge Cases to Handle:**
1. Point lies exactly on an edge
2. Ray passes through a vertex
3. Ray is collinear with an edge

```rust
fn point_in_polygon(point: &Point, polygon: &[Point]) -> bool {
    let n = polygon.len();
    if n < 3 {
        return false; // Not a valid polygon
    }
    
    let extreme = Point::new(i64::MAX, point.y);
    let mut count = 0;
    
    for i in 0..n {
        let next = (i + 1) % n;
        
        // Check if point lies on the edge
        if orientation(polygon[i], point, &polygon[next]) == Orientation::Collinear
            && on_segment(&polygon[i], point, &polygon[next])
        {
            return true; // Point on boundary counts as inside
        }
        
        // Check if the line segment crosses the ray
        if segments_intersect(polygon[i], &polygon[next], point, &extreme) {
            // Handle vertex crossing case
            if orientation(polygon[i], point, &polygon[next]) == Orientation::Collinear {
                continue;
            }
            count += 1;
        }
    }
    
    // Odd count means inside
    count % 2 == 1
}
```

**Time Complexity:** O(n) where n is number of vertices  
**Space Complexity:** O(1)

**Alternative: Winding Number Algorithm** (more robust for complex polygons)

The **winding number** counts how many times the polygon winds around the point. Non-zero winding number means inside.

---

### Pattern 2.4: Convex Hull

**Definition:** The **convex hull** of a set of points is the smallest convex polygon that contains all the points.

**Intuition:** Imagine wrapping a rubber band around all the points - the shape it forms is the convex hull.

**Algorithm: Graham Scan** (One of the most elegant)

**Steps:**
1. Find the point with lowest y-coordinate (bottom-most point), call it P0
2. Sort all other points by polar angle with respect to P0
3. Process points in sorted order, maintaining a stack:
   - If current point makes a left turn with last two points on stack → push it
   - If current point makes a right turn → pop from stack until we can make a left turn

**Why does this work?** We're walking counter-clockwise around the perimeter. Right turns indicate we've gone "inside" the hull, so we backtrack.

```rust
fn convex_hull(points: &mut Vec<Point>) -> Vec<Point> {
    let n = points.len();
    if n < 3 {
        return points.clone(); // Need at least 3 points
    }
    
    // Step 1: Find bottom-most point (or leftmost if tie)
    let mut bottom = 0;
    for i in 1..n {
        if points[i].y < points[bottom].y || 
           (points[i].y == points[bottom].y && points[i].x < points[bottom].x)
        {
            bottom = i;
        }
    }
    points.swap(0, bottom);
    let p0 = points[0];
    
    // Step 2: Sort by polar angle
    points[1..].sort_by(|a, b| {
        let o = orientation(&p0, a, b);
        match o {
            Orientation::Collinear => {
                // If collinear, closer point comes first
                let dist_a = p0.subtract(a).magnitude_squared();
                let dist_b = p0.subtract(b).magnitude_squared();
                dist_a.cmp(&dist_b)
            }
            Orientation::CounterClockwise => std::cmp::Ordering::Less,
            Orientation::Clockwise => std::cmp::Ordering::Greater,
        }
    });
    
    // Step 3: Build hull using stack
    let mut hull = Vec::new();
    hull.push(points[0]);
    hull.push(points[1]);
    
    for i in 2..n {
        // Pop while we make a right turn
        while hull.len() > 1 {
            let top = hull[hull.len() - 1];
            let second = hull[hull.len() - 2];
            if orientation(&second, &top, &points[i]) != Orientation::Clockwise {
                break;
            }
            hull.pop();
        }
        hull.push(points[i]);
    }
    
    hull
}
```

```go
func ConvexHull(points []Point) []Point {
    n := len(points)
    if n < 3 {
        return points
    }
    
    // Find bottom-most point
    bottom := 0
    for i := 1; i < n; i++ {
        if points[i].Y < points[bottom].Y ||
           (points[i].Y == points[bottom].Y && points[i].X < points[bottom].X) {
            bottom = i
        }
    }
    points[0], points[bottom] = points[bottom], points[0]
    p0 := points[0]
    
    // Sort by polar angle
    sort.Slice(points[1:], func(i, j int) bool {
        i, j = i+1, j+1
        o := GetOrientation(p0, points[i], points[j])
        if o == Collinear {
            distI := p0.Subtract(points[i]).MagnitudeSquared()
            distJ := p0.Subtract(points[j]).MagnitudeSquared()
            return distI < distJ
        }
        return o == CounterClockwise
    })
    
    // Build hull
    hull := []Point{points[0], points[1]}
    
    for i := 2; i < n; i++ {
        for len(hull) > 1 {
            top := hull[len(hull)-1]
            second := hull[len(hull)-2]
            if GetOrientation(second, top, points[i]) != Clockwise {
                break
            }
            hull = hull[:len(hull)-1]
        }
        hull = append(hull, points[i])
    }
    
    return hull
}
```

**Time Complexity:** O(n log n) - dominated by sorting  
**Space Complexity:** O(n) for the hull

**Flowchart:**
```
Start
  ↓
Find bottom-most point P0
  ↓
Sort points by polar angle from P0
  ↓
Initialize stack with P0, P1
  ↓
For each remaining point P:
  ↓
  While stack size > 1:
    ↓
    Check orientation of (second_top, top, P)
    ↓
    Right turn? → Pop stack
    Left turn? → Break loop
  ↓
  Push P onto stack
  ↓
Return stack (the convex hull)
```

---

## 3. Advanced Patterns

### Pattern 3.1: Closest Pair of Points

**Problem:** Given n points, find the two points with minimum Euclidean distance.

**Naive Approach:** Check all pairs → O(n²)

**Optimized: Divide and Conquer**

**Algorithm:**
1. Sort points by x-coordinate
2. Divide points into left and right halves
3. Recursively find closest pair in each half
4. Find closest pair with one point in each half
5. Return minimum of the three

**The Key Insight:** After finding minimum distance δ in the halves, we only need to check points within δ of the dividing line.

```rust
use std::f64;

#[derive(Debug, Clone, Copy)]
struct PointF {
    x: f64,
    y: f64,
}

impl PointF {
    fn distance(&self, other: &PointF) -> f64 {
        let dx = self.x - other.x;
        let dy = self.y - other.y;
        (dx * dx + dy * dy).sqrt()
    }
}

fn closest_pair_recursive(px: &[PointF], py: &[PointF]) -> f64 {
    let n = px.len();
    
    // Base case: brute force for small n
    if n <= 3 {
        let mut min_dist = f64::MAX;
        for i in 0..n {
            for j in (i + 1)..n {
                min_dist = min_dist.min(px[i].distance(&px[j]));
            }
        }
        return min_dist;
    }
    
    // Divide
    let mid = n / 2;
    let mid_point = px[mid];
    
    // Split py into left and right based on mid line
    let mut pyl = Vec::new();
    let mut pyr = Vec::new();
    for &p in py {
        if p.x <= mid_point.x {
            pyl.push(p);
        } else {
            pyr.push(p);
        }
    }
    
    // Conquer
    let dl = closest_pair_recursive(&px[..mid], &pyl);
    let dr = closest_pair_recursive(&px[mid..], &pyr);
    let d = dl.min(dr);
    
    // Find closest pair across the dividing line
    let mut strip: Vec<PointF> = py.iter()
        .filter(|p| (p.x - mid_point.x).abs() < d)
        .copied()
        .collect();
    
    let mut min_dist = d;
    for i in 0..strip.len() {
        for j in (i + 1)..strip.len() {
            if (strip[j].y - strip[i].y) >= d {
                break; // No point checking further
            }
            min_dist = min_dist.min(strip[i].distance(&strip[j]));
        }
    }
    
    min_dist
}

fn closest_pair(points: &mut [PointF]) -> f64 {
    let mut px = points.to_vec();
    let mut py = points.to_vec();
    
    px.sort_by(|a, b| a.x.partial_cmp(&b.x).unwrap());
    py.sort_by(|a, b| a.y.partial_cmp(&b.y).unwrap());
    
    closest_pair_recursive(&px, &py)
}
```

**Time Complexity:** O(n log n)  
**Space Complexity:** O(n)

**Mental Model:** Think of it like a tournament bracket - you find winners in sub-regions, then check the "border" between regions for potential cross-region winners.

---

### Pattern 3.2: Rotating Calipers

**Concept:** Imagine two parallel lines touching opposite sides of a convex polygon, rotating together around it. This technique efficiently solves several problems.

**Applications:**
- Maximum distance between points (diameter)
- Minimum width of polygon
- Minimum area bounding rectangle

**Algorithm for Diameter:**

```rust
fn rotating_calipers_diameter(hull: &[Point]) -> i64 {
    let n = hull.len();
    if n < 2 {
        return 0;
    }
    
    let mut max_dist_sq = 0i64;
    let mut j = 1;
    
    for i in 0..n {
        let next_i = (i + 1) % n;
        
        // Rotate j while cross product increases
        loop {
            let next_j = (j + 1) % n;
            let edge = hull[next_i].subtract(&hull[i]);
            let to_j = hull[j].subtract(&hull[i]);
            let to_next_j = hull[next_j].subtract(&hull[i]);
            
            if edge.cross(&to_next_j) <= edge.cross(&to_j) {
                break;
            }
            j = next_j;
        }
        
        max_dist_sq = max_dist_sq.max(
            hull[i].subtract(&hull[j]).magnitude_squared()
        );
    }
    
    max_dist_sq
}
```

**Time Complexity:** O(n) - linear in hull vertices  
**Space Complexity:** O(1)

**Intuition:** Each vertex is visited at most twice (once as i, once as j), making it linear.

---

### Pattern 3.3: Sweep Line Algorithm

**Concept:** Imagine a vertical line sweeping across the plane from left to right. Process geometric events (points, intersections) in order.

**Classic Problem: Rectangle Area Union**

**Problem:** Given n axis-aligned rectangles, find total area covered (overlaps counted once).

**Approach:**
1. Create events for each rectangle's left and right edges
2. Sort events by x-coordinate
3. Maintain active y-intervals as we sweep
4. Calculate area contribution between consecutive x-positions

```rust
use std::collections::BTreeMap;

#[derive(Debug, Clone, Copy)]
struct Rectangle {
    x1: i64,
    y1: i64,
    x2: i64,
    y2: i64,
}

#[derive(Debug)]
enum EventType {
    Start,
    End,
}

#[derive(Debug)]
struct Event {
    x: i64,
    y1: i64,
    y2: i64,
    event_type: EventType,
}

fn rectangle_area_union(rectangles: &[Rectangle]) -> i64 {
    let mut events = Vec::new();
    
    for rect in rectangles {
        events.push(Event {
            x: rect.x1,
            y1: rect.y1,
            y2: rect.y2,
            event_type: EventType::Start,
        });
        events.push(Event {
            x: rect.x2,
            y1: rect.y1,
            y2: rect.y2,
            event_type: EventType::End,
        });
    }
    
    events.sort_by_key(|e| e.x);
    
    let mut total_area = 0i64;
    let mut active_intervals: BTreeMap<i64, i64> = BTreeMap::new();
    let mut prev_x = 0i64;
    
    for event in events {
        // Calculate area contribution from prev_x to current x
        let width = event.x - prev_x;
        let height = calculate_active_height(&active_intervals);
        total_area += width * height;
        
        // Update active intervals
        match event.event_type {
            EventType::Start => {
                *active_intervals.entry(event.y1).or_insert(0) += 1;
                *active_intervals.entry(event.y2).or_insert(0) -= 1;
            }
            EventType::End => {
                *active_intervals.entry(event.y1).or_insert(0) -= 1;
                *active_intervals.entry(event.y2).or_insert(0) += 1;
            }
        }
        
        prev_x = event.x;
    }
    
    total_area
}

fn calculate_active_height(intervals: &BTreeMap<i64, i64>) -> i64 {
    let mut height = 0i64;
    let mut active_count = 0;
    let mut prev_y = 0i64;
    
    for (&y, &delta) in intervals {
        if active_count > 0 {
            height += y - prev_y;
        }
        active_count += delta;
        prev_y = y;
    }
    
    height
}
```

**Time Complexity:** O(n log n)  
**Space Complexity:** O(n)

---

## 4. Circle and Arc Patterns

### Pattern 4.1: Point-Circle Relationship

**Determine if point P is inside, on, or outside circle with center C and radius R:**

```rust
#[derive(Debug, PartialEq)]
enum PointCircleRelation {
    Inside,
    On,
    Outside,
}

fn point_circle_relation(p: &Point, center: &Point, radius_squared: i64) -> PointCircleRelation {
    let dist_sq = p.subtract(center).magnitude_squared();
    
    match dist_sq.cmp(&radius_squared) {
        std::cmp::Ordering::Less => PointCircleRelation::Inside,
        std::cmp::Ordering::Equal => PointCircleRelation::On,
        std::cmp::Ordering::Greater => PointCircleRelation::Outside,
    }
}
```

**Time Complexity:** O(1)

---

### Pattern 4.2: Circle-Line Intersection

**Find intersection points between a circle and a line segment.**

This involves:
1. Find closest point on line to circle center
2. Check if this distance ≤ radius
3. If yes, calculate intersection points using Pythagorean theorem

```rust
fn closest_point_on_segment(p: &Point, a: &Point, b: &Point) -> Point {
    let ap = p.subtract(a);
    let ab = b.subtract(a);
    let ab_len_sq = ab.magnitude_squared();
    
    if ab_len_sq == 0 {
        return *a; // Segment is a point
    }
    
    let t = ap.dot(&ab) as f64 / ab_len_sq as f64;
    let t = t.clamp(0.0, 1.0); // Clamp to segment
    
    Point {
        x: a.x + (t * ab.x as f64) as i64,
        y: a.y + (t * ab.y as f64) as i64,
    }
}
```

---

## 5. Problem-Solving Framework

### Step 1: Identify the Geometric Primitive
- Points, lines, segments, polygons, circles?
- What relationships are being queried?

### Step 2: Choose the Right Tool
- **Orientation test** → For turns, intersections, containment
- **Cross/dot product** → For angles, projections, areas
- **Convex hull** → For finding boundaries
- **Sweep line** → For processing ordered events
- **Divide & conquer** → For optimization problems

### Step 3: Handle Edge Cases
- **Degeneracy:** Collinear points, zero-length segments
- **Precision:** Use integers when possible, epsilon for floats
- **Boundary conditions:** Points on edges, vertices

### Step 4: Complexity Analysis
- Most geometric primitives: O(1)
- Sorting-based algorithms: O(n log n)
- Convex hull, closest pair: O(n log n)
- Brute force checks: O(n²) or O(n³)

---

## 6. Common LeetCode Problem Types

### Type 1: Intersection Problems
**Example:** "Check if rectangles overlap"
- **Tool:** Axis-aligned rectangle intersection (check x and y intervals separately)
- **Complexity:** O(1)

### Type 2: Convex Hull Variants
**Example:** "Erect the Fence" (LeetCode 587)
- **Tool:** Graham scan or Jarvis march
- **Complexity:** O(n log n)

### Type 3: Maximum Distance/Area
**Example:** "Largest Triangle Area" (LeetCode 812)
- **Tool:** Brute force O(n³) or convex hull + rotating calipers O(n log n + k²) where k = hull size
- **Complexity:** O(n³) brute force, O(n log n) optimized

### Type 4: Point Location
**Example:** "Check if Point Inside Polygon"
- **Tool:** Ray casting or winding number
- **Complexity:** O(n) where n = vertices

### Type 5: Line Sweep
**Example:** "Rectangle Area II" (LeetCode 850)
- **Tool:** Coordinate compression + sweep line
- **Complexity:** O(n log n)

---

## 7. Mental Models for Mastery

### Model 1: The Orientation Oracle
**Think of orientation() as a universal decision maker.** Almost every geometric algorithm reduces to asking "which way do we turn?"

### Model 2: The Rubber Band Metaphor
**For convex hulls:** Visualize stretching a rubber band around nails (points). The band naturally forms the convex hull.

### Model 3: The Sweep Line as Time
**Think of the x-axis as time.** Events happen at specific moments (x-coordinates), and we maintain state (active intervals, intersections) as time progresses.

### Model 4: Vectors as Movement
**Don't think of vectors as abstract math.** Think of them as "how do I get from A to B?" This makes cross products intuitive (turning sensors) and dot products meaningful (alignment measures).

---

## 8. Common Pitfalls

### Pitfall 1: Floating-Point Precision
**Problem:** Comparing floats directly with `==` fails.
**Solution:** Use epsilon or work with integers.

```rust
const EPS: f64 = 1e-9;

fn float_equals(a: f64, b: f64) -> bool {
    (a - b).abs() < EPS
}
```

### Pitfall 2: Integer Overflow
**Problem:** Cross products and squared distances can overflow.
**Solution:** Use `i64`/`i128` or modular arithmetic.

### Pitfall 3: Collinearity
**Problem:** Forgetting to handle collinear cases.
**Solution:** Always have an explicit branch for `orientation == Collinear`.

### Pitfall 4: Boundary Cases
**Problem:** Point exactly on polygon edge - inside or outside?
**Solution:** Define convention clearly (usually count as inside).

---

## 9. Practice Strategy Summary

1. **Master primitives first:** orientation, cross product, dot product
2. **Implement Graham scan** until it's muscle memory
3. **Solve 5 intersection problems** to internalize orientation tests
4. **Tackle 3 convex hull variants** to understand the pattern
5. **Learn sweep line** through rectangle union problems
6. **Challenge yourself** with rotating calipers and divide-and-conquer

---

## 10. Key Takeaways

**Geometric algorithms are about reducing complexity to simple primitives.**

✅ **Orientation test** is your most powerful tool  
✅ **Cross products** detect rotations  
✅ **Dot products** measure alignment  
✅ **Integer arithmetic** prevents precision errors  
✅ **Convex hull** solves many "extreme" problems  
✅ **Sweep line** handles ordered events efficiently  

**The true mastery comes from recognizing patterns:** When you see a problem, you should immediately think "This is a convex hull problem" or "This needs orientation tests" or "Sweep line will work here."

---

This guide covered all major geometric patterns. Your next step: **Implement every algorithm from scratch in your preferred language**. Understanding theory is 20%; implementation muscle memory is 80% of competitive programming success.

Start with Graham scan for convex hull - it's the geometric equivalent of quicksort: foundational, elegant, and appears everywhere. Once you can code it without looking at references, you'll have crossed a major threshold in geometric thinking.

What specific problem type would you like to explore deeper with detailed examples?