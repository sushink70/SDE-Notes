# 🎯 The Complete Mastery Guide to Intervals

**Philosophy**: Intervals are geometric abstractions of continuity—they represent ranges of values where every element between boundaries exists. Mastering intervals means mastering *range thinking*, a fundamental cognitive pattern that appears everywhere: time windows, coordinate ranges, resource allocation, network bandwidth, and even memory segments.

---

## 📐 Part 1: Foundational Concepts & Mental Models

### 1.1 What is an Interval?

An **interval** is a contiguous range defined by two endpoints: `[start, end]`.

**Mathematical Definition**:
- **Closed interval** `[a, b]` = {x ∈ ℝ | a ≤ x ≤ b}
- **Open interval** `(a, b)` = {x ∈ ℝ | a < x < b}
- **Half-open** `[a, b)` = {x ∈ ℝ | a ≤ x < b}

**In programming**, we typically use **closed intervals** `[start, end]` where both boundaries are inclusive.

**Cognitive Model**: Think of intervals as *segments on a number line*. Every problem involving "ranges", "windows", "schedules", or "spans" is an interval problem in disguise.

---

### 1.2 Core Terminology (Building Blocks)

Before we proceed, let's establish precise vocabulary:

#### **Endpoints**
- `start`: Left boundary (beginning)
- `end`: Right boundary (termination)
- Convention: `start ≤ end` (invalid if start > end)

#### **Overlap**
Two intervals `A = [a1, a2]` and `B = [b1, b2]` **overlap** if they share at least one point.
```
Condition: max(a1, b1) <= min(a2, b2)
```

**Visual**:
```
[----A----]
     [----B----]
     ^^^^^ overlap region
```

#### **Disjoint**
Intervals are **disjoint** (non-overlapping) if they share no points.
```
[--A--]    [--B--]
```

#### **Merge/Union**
Combining overlapping/touching intervals into one.
```
[--A--]
    [--B--]
    ↓
[----C----]  where C = [min(A.start, B.start), max(A.end, B.end)]
```

#### **Intersection**
The common region between overlapping intervals.
```
[----A----]
     [----B----]
     ↓
     [--I--]  where I = [max(A.start, B.start), min(A.end, B.end)]
```

#### **Point vs Interval**
- **Point**: A single value (can be thought of as interval [x, x])
- **Interval query**: "Does point P lie in interval [a, b]?" → `a ≤ P ≤ b`

---

### 1.3 Mental Model: The Timeline Metaphor

**Visualization Strategy**:
```
Timeline →
0━━━━5━━━━10━━━━15━━━━20━━━━25
  [---]      [------]
   A            B
```

Always draw intervals on a timeline mentally. This activates spatial reasoning—faster than algebraic manipulation.

**Flow of Thought**:
1. **Sort first** (organize chaos)
2. **Scan left-to-right** (process sequentially)
3. **Track state** (what's active? what's ended?)

---

## 🧩 Part 2: Problem Categories & Patterns

### 2.1 Pattern Classification

| Pattern | Example Problem | Key Insight |
|---------|----------------|-------------|
| **Merge Overlapping** | Merge Intervals | Sort + greedy scan |
| **Interval Insertion** | Insert Interval | Find position + merge |
| **Intersection** | Interval List Intersections | Two-pointer technique |
| **Coverage** | Minimum Arrows to Burst Balloons | Greedy + sort by end |
| **Scheduling** | Meeting Rooms | Event-based simulation |
| **Range Queries** | Range Sum Query | Prefix sums / Segment trees |

---

### 2.2 The Sorting Decision

**Critical Rule**: 99% of interval problems start with sorting.

**Why?**
- Converts 2D problem (start + end) into sequential processing
- Enables greedy algorithms
- Reduces time complexity from O(n²) to O(n log n)

**How to sort?**
- **Primary**: Sort by `start` (most common)
- **Alternative**: Sort by `end` (for greedy coverage problems)
- **Rare**: Custom comparator for special cases

---

## 💻 Part 3: Core Algorithms (With Multi-Language Implementation)

### 3.1 Problem: Merge Overlapping Intervals

**Problem Statement**: Given intervals, merge all overlapping ones.

**Input**: `[[1,3], [2,6], [8,10], [15,18]]`  
**Output**: `[[1,6], [8,10], [15,18]]`

---

#### **Expert Thought Process (Pre-Code Mental Flow)**

```
Step 1: SORT
[1,3], [2,6], [8,10], [15,18]
Already sorted by start

Step 2: INITIALIZE
result = [[1,3]]
current = [1,3]

Step 3: SCAN
For each next interval:
  - If overlaps with current: MERGE
  - Else: FINALIZE current, START new

Iteration 1: [2,6]
  2 <= 3? YES → overlap
  Merge: [1, max(3,6)] = [1,6]
  
Iteration 2: [8,10]
  8 <= 6? NO → disjoint
  Finalize [1,6], start [8,10]
  
Iteration 3: [15,18]
  15 <= 10? NO → disjoint
  Finalize [8,10], start [15,18]

Final: [[1,6], [8,10], [15,18]]
```

**Key Insight**: Track the "last merged interval". Decide: extend or finalize.

---

#### **Implementation: Rust**

```rust
// Interval representation
#[derive(Debug, Clone, PartialEq, Eq)]
struct Interval {
    start: i32,
    end: i32,
}

impl Interval {
    fn new(start: i32, end: i32) -> Self {
        Interval { start, end }
    }
    
    // Check if two intervals overlap
    fn overlaps(&self, other: &Interval) -> bool {
        self.start <= other.end && other.start <= self.end
    }
    
    // Merge two overlapping intervals
    fn merge(&self, other: &Interval) -> Interval {
        Interval {
            start: self.start.min(other.start),
            end: self.end.max(other.end),
        }
    }
}

fn merge_intervals(mut intervals: Vec<Interval>) -> Vec<Interval> {
    // Edge case: empty or single interval
    if intervals.len() <= 1 {
        return intervals;
    }
    
    // Step 1: Sort by start time
    // Time: O(n log n), Space: O(1) in-place
    intervals.sort_unstable_by_key(|interval| interval.start);
    
    // Step 2: Initialize result with first interval
    let mut merged: Vec<Interval> = Vec::with_capacity(intervals.len());
    merged.push(intervals[0].clone());
    
    // Step 3: Scan and merge
    for current in intervals.iter().skip(1) {
        let last = merged.last_mut().unwrap();
        
        if current.start <= last.end {
            // Overlap detected: extend the end boundary
            last.end = last.end.max(current.end);
        } else {
            // No overlap: start new interval
            merged.push(current.clone());
        }
    }
    
    merged
}

// Example usage
fn main() {
    let intervals = vec![
        Interval::new(1, 3),
        Interval::new(2, 6),
        Interval::new(8, 10),
        Interval::new(15, 18),
    ];
    
    let result = merge_intervals(intervals);
    println!("{:?}", result);
    // Output: [Interval { start: 1, end: 6 }, Interval { start: 8, end: 10 }, Interval { start: 15, end: 18 }]
}
```

**Rust-Specific Notes**:
- `sort_unstable_by_key`: Faster than stable sort (O(n log n) but doesn't preserve order of equal elements)
- `Vec::with_capacity`: Pre-allocate to avoid reallocation
- `last_mut()`: Mutable reference to modify in-place
- No `.clone()` needed if using indices instead of iterators

**Time Complexity**: O(n log n) — dominated by sorting  
**Space Complexity**: O(n) — result vector

---

#### **Implementation: Go**

```go
package main

import (
    "fmt"
    "sort"
)

// Interval represents a range [Start, End]
type Interval struct {
    Start int
    End   int
}

// MergeIntervals merges all overlapping intervals
func MergeIntervals(intervals []Interval) []Interval {
    // Edge case
    if len(intervals) <= 1 {
        return intervals
    }
    
    // Step 1: Sort by start
    sort.Slice(intervals, func(i, j int) bool {
        return intervals[i].Start < intervals[j].Start
    })
    
    // Step 2: Initialize result
    merged := []Interval{intervals[0]}
    
    // Step 3: Scan and merge
    for _, current := range intervals[1:] {
        last := &merged[len(merged)-1]
        
        if current.Start <= last.End {
            // Overlap: extend end
            if current.End > last.End {
                last.End = current.End
            }
        } else {
            // No overlap: append new
            merged = append(merged, current)
        }
    }
    
    return merged
}

func main() {
    intervals := []Interval{
        {1, 3},
        {2, 6},
        {8, 10},
        {15, 18},
    }
    
    result := MergeIntervals(intervals)
    fmt.Println(result)
    // Output: [{1 6} {8 10} {15 18}]
}
```

**Go-Specific Notes**:
- `sort.Slice`: In-place sorting with custom comparator
- `&merged[len(merged)-1]`: Pointer to last element for mutation
- Slicing `intervals[1:]` creates view (no copy)

---

#### **Implementation: C**

```c
#include <stdio.h>
#include <stdlib.h>

// Interval structure
typedef struct {
    int start;
    int end;
} Interval;

// Comparator for qsort
int compare_intervals(const void *a, const void *b) {
    Interval *ia = (Interval *)a;
    Interval *ib = (Interval *)b;
    return ia->start - ib->start;
}

// Helper: max of two integers
static inline int max(int a, int b) {
    return (a > b) ? a : b;
}

// Merge overlapping intervals
// Returns new size of merged array
int merge_intervals(Interval *intervals, int size, Interval **result) {
    if (size <= 1) {
        *result = intervals;
        return size;
    }
    
    // Step 1: Sort
    qsort(intervals, size, sizeof(Interval), compare_intervals);
    
    // Step 2: Allocate result (worst case: all disjoint)
    *result = (Interval *)malloc(size * sizeof(Interval));
    if (*result == NULL) return -1; // Allocation failed
    
    // Step 3: Initialize with first interval
    (*result)[0] = intervals[0];
    int merged_count = 1;
    
    // Step 4: Scan and merge
    for (int i = 1; i < size; i++) {
        Interval *last = &(*result)[merged_count - 1];
        
        if (intervals[i].start <= last->end) {
            // Overlap: extend
            last->end = max(last->end, intervals[i].end);
        } else {
            // No overlap: add new
            (*result)[merged_count++] = intervals[i];
        }
    }
    
    return merged_count;
}

int main() {
    Interval intervals[] = {
        {1, 3},
        {2, 6},
        {8, 10},
        {15, 18}
    };
    int size = sizeof(intervals) / sizeof(intervals[0]);
    
    Interval *merged;
    int merged_size = merge_intervals(intervals, size, &merged);
    
    printf("Merged intervals:\n");
    for (int i = 0; i < merged_size; i++) {
        printf("[%d, %d]\n", merged[i].start, merged[i].end);
    }
    
    free(merged); // Don't forget to free!
    return 0;
}
```

**C-Specific Notes**:
- Manual memory management (`malloc`, `free`)
- `qsort`: Standard library sorting (not stable)
- Inline `max` function for performance
- Error handling for allocation failure

---

### 3.2 Problem: Insert Interval

**Problem**: Insert a new interval and merge if necessary.

**Input**: `intervals = [[1,3],[6,9]]`, `newInterval = [2,5]`  
**Output**: `[[1,5],[6,9]]`

**Expert Mental Flow**:
```
Step 1: Find position to insert
Step 2: Merge with left overlapping intervals
Step 3: Merge with right overlapping intervals
Step 4: Insert merged result

Visual:
[1,3]     [6,9]
  [2,5]   ← insert
  ↓
[1,5]     [6,9]
```

---

#### **Implementation: Rust (Optimal)**

```rust
fn insert_interval(intervals: Vec<Interval>, new_interval: Interval) -> Vec<Interval> {
    let mut result = Vec::new();
    let mut new = new_interval;
    let mut i = 0;
    let n = intervals.len();
    
    // Step 1: Add all intervals that end before new starts
    while i < n && intervals[i].end < new.start {
        result.push(intervals[i].clone());
        i += 1;
    }
    
    // Step 2: Merge all overlapping intervals
    while i < n && intervals[i].start <= new.end {
        new.start = new.start.min(intervals[i].start);
        new.end = new.end.max(intervals[i].end);
        i += 1;
    }
    result.push(new);
    
    // Step 3: Add remaining intervals
    while i < n {
        result.push(intervals[i].clone());
        i += 1;
    }
    
    result
}
```

**Time**: O(n), **Space**: O(n)

**Key Insight**: Three-phase scan without sorting (input already sorted).

---

### 3.3 Problem: Interval Intersection

**Problem**: Find intersection of two sorted interval lists.

**Input**:  
`A = [[0,2],[5,10],[13,23],[24,25]]`  
`B = [[1,5],[8,12],[15,24],[25,26]]`

**Output**: `[[1,2],[5,5],[8,10],[15,23],[24,24],[25,25]]`

**Expert Thought**:
```
Two-pointer technique:
  i → A, j → B
  
  While both have intervals:
    Compute intersection
    Advance the pointer of interval that ends first
```

---

#### **Implementation: Go (Two-Pointer)**

```go
func intervalIntersection(A []Interval, B []Interval) []Interval {
    result := []Interval{}
    i, j := 0, 0
    
    for i < len(A) && j < len(B) {
        // Find intersection boundaries
        start := max(A[i].Start, B[j].Start)
        end := min(A[i].End, B[j].End)
        
        // If valid intersection exists
        if start <= end {
            result = append(result, Interval{start, end})
        }
        
        // Advance pointer of interval that ends first
        if A[i].End < B[j].End {
            i++
        } else {
            j++
        }
    }
    
    return result
}

func max(a, b int) int {
    if a > b {
        return a
    }
    return b
}

func min(a, b int) int {
    if a < b {
        return a
    }
    return b
}
```

**Time**: O(m + n), **Space**: O(1) excluding output

---

## 🎯 Part 4: Advanced Patterns

### 4.1 Meeting Rooms Problem

**Problem**: Can a person attend all meetings?

**Input**: `[[0,30],[5,10],[15,20]]`  
**Output**: `false` (conflicts at [0,30] and [5,10])

**Algorithm**: Sort + scan for overlaps.

```rust
fn can_attend_meetings(mut intervals: Vec<Interval>) -> bool {
    if intervals.len() <= 1 {
        return true;
    }
    
    intervals.sort_unstable_by_key(|i| i.start);
    
    for i in 1..intervals.len() {
        if intervals[i].start < intervals[i-1].end {
            return false; // Overlap found
        }
    }
    
    true
}
```

**Time**: O(n log n)

---

### 4.2 Meeting Rooms II (Minimum Rooms Required)

**Problem**: Find minimum number of conference rooms needed.

**Input**: `[[0,30],[5,10],[15,20]]`  
**Output**: `2`

**Mental Model**: "Event simulation" - track concurrent meetings.

**Algorithm**:
1. Extract all start/end times as events
2. Sort events
3. Track active count (start +1, end -1)
4. Maximum active = answer

```rust
fn min_meeting_rooms(intervals: Vec<Interval>) -> i32 {
    let mut events = Vec::new();
    
    for interval in intervals {
        events.push((interval.start, 1));    // Meeting starts
        events.push((interval.end, -1));     // Meeting ends
    }
    
    // Sort by time; if tie, process end before start
    events.sort_unstable_by(|a, b| {
        if a.0 == b.0 {
            a.1.cmp(&b.1) // End (-1) comes before Start (1)
        } else {
            a.0.cmp(&b.0)
        }
    });
    
    let mut active = 0;
    let mut max_rooms = 0;
    
    for (_, delta) in events {
        active += delta;
        max_rooms = max_rooms.max(active);
    }
    
    max_rooms
}
```

**Time**: O(n log n), **Space**: O(n)

**Critical Detail**: Why end before start in tie?  
If meeting ends at time T and another starts at T, they don't overlap (same room can be reused).

---

### 4.3 Non-Overlapping Intervals (Minimum Removals)

**Problem**: Remove minimum intervals to make rest non-overlapping.

**Input**: `[[1,2],[2,3],[3,4],[1,3]]`  
**Output**: `1` (remove [1,3])

**Greedy Strategy**: Sort by **end time**, keep intervals that end earliest.

**Why?** Early-ending intervals leave more room for future intervals.

```rust
fn erase_overlap_intervals(mut intervals: Vec<Interval>) -> i32 {
    if intervals.len() <= 1 {
        return 0;
    }
    
    // Sort by end time
    intervals.sort_unstable_by_key(|i| i.end);
    
    let mut count = 0;
    let mut prev_end = intervals[0].end;
    
    for i in 1..intervals.len() {
        if intervals[i].start < prev_end {
            // Overlap: remove current interval
            count += 1;
        } else {
            // No overlap: update end
            prev_end = intervals[i].end;
        }
    }
    
    count
}
```

**Time**: O(n log n)

---

## 🧠 Part 5: Advanced Data Structures for Intervals

### 5.1 Segment Tree for Range Queries

**Use Case**: Dynamic range sum/min/max queries with updates.

**Concept**: Binary tree where:
- Leaf nodes = individual elements
- Internal nodes = aggregate of children

**Example**: Range sum query

```
Array: [1, 3, 5, 7, 9, 11]

Segment Tree:
           [1-6: 36]
          /          \
    [1-3: 9]        [4-6: 27]
    /     \         /      \
[1-2:4] [3:5]  [4-5:16] [6:11]
 /  \            /  \
[1:1][2:3]    [4:7][5:9]
```

**Implementation Skeleton (Rust)**:

```rust
struct SegmentTree {
    tree: Vec<i64>,
    n: usize,
}

impl SegmentTree {
    fn new(arr: &[i64]) -> Self {
        let n = arr.len();
        let mut tree = vec![0; 4 * n]; // Safe upper bound
        let mut st = SegmentTree { tree, n };
        st.build(arr, 0, 0, n - 1);
        st
    }
    
    // Build tree recursively
    fn build(&mut self, arr: &[i64], node: usize, start: usize, end: usize) {
        if start == end {
            self.tree[node] = arr[start];
        } else {
            let mid = (start + end) / 2;
            let left = 2 * node + 1;
            let right = 2 * node + 2;
            
            self.build(arr, left, start, mid);
            self.build(arr, right, mid + 1, end);
            
            self.tree[node] = self.tree[left] + self.tree[right];
        }
    }
    
    // Query sum in range [l, r]
    fn query(&self, node: usize, start: usize, end: usize, l: usize, r: usize) -> i64 {
        // No overlap
        if r < start || l > end {
            return 0;
        }
        
        // Complete overlap
        if l <= start && end <= r {
            return self.tree[node];
        }
        
        // Partial overlap
        let mid = (start + end) / 2;
        let left_sum = self.query(2 * node + 1, start, mid, l, r);
        let right_sum = self.query(2 * node + 2, mid + 1, end, l, r);
        
        left_sum + right_sum
    }
    
    pub fn range_sum(&self, l: usize, r: usize) -> i64 {
        self.query(0, 0, self.n - 1, l, r)
    }
}
```

**Time Complexity**:
- Build: O(n)
- Query: O(log n)
- Update: O(log n)

---

### 5.2 Interval Tree (Advanced)

**Purpose**: Efficiently find all intervals that overlap with a query interval.

**Structure**: Augmented BST where each node stores:
- Interval
- Max endpoint in subtree

**Applications**: Computational geometry, scheduling, collision detection

*Implementation beyond scope—requires balanced tree (AVL/Red-Black).*

---

## 🔥 Part 6: Problem-Solving Framework

### The 5-Step Interval Protocol

**Step 1: CLASSIFY**
- Merging? Intersection? Coverage? Query?

**Step 2: SORT**
- By start? By end? Custom?

**Step 3: CHOOSE ALGORITHM**
- Greedy scan? Two-pointer? Event simulation? Data structure?

**Step 4: HANDLE EDGE CASES**
- Empty input
- Single interval
- All overlapping
- All disjoint
- Duplicate intervals

**Step 5: OPTIMIZE**
- Can we avoid sorting? (if already sorted)
- Can we do in-place? (Rust: mutation vs cloning)
- Can we short-circuit?

---

## 📊 Part 7: Complexity Cheat Sheet

| Problem | Time | Space | Key Technique |
|---------|------|-------|---------------|
| Merge Intervals | O(n log n) | O(n) | Sort + scan |
| Insert Interval | O(n) | O(n) | Three-phase scan |
| Interval Intersection | O(m+n) | O(1) | Two-pointer |
| Meeting Rooms I | O(n log n) | O(1) | Sort + check |
| Meeting Rooms II | O(n log n) | O(n) | Event simulation |
| Non-Overlapping Intervals | O(n log n) | O(1) | Greedy by end |
| Range Sum Query (Static) | O(1) | O(n) | Prefix sum |
| Range Sum Query (Dynamic) | O(log n) | O(n) | Segment tree |

---

## 🎓 Part 8: Cognitive Principles for Mastery

### Principle 1: Spatial Over Algebraic
**Why**: Human visual cortex processes timelines faster than equations.  
**Practice**: Always draw intervals before coding.

### Principle 2: Chunking Events
**Concept**: Group start/end into "events" to reduce cognitive load.  
**Application**: Meeting Rooms II, Sweep Line algorithms.

### Principle 3: Greedy Proof Pattern
**For interval greedy algorithms**:
1. State greedy choice (e.g., "pick earliest ending")
2. Prove optimal substructure
3. Show exchange argument (swapping doesn't worsen solution)

### Principle 4: Invariant Maintenance
**Example**: In merge intervals, invariant = "last interval in result never overlaps with next"  
**Benefit**: Reduces debugging time, ensures correctness.

---

## 🌟 Part 9: Practice Progression Path

### Level 1: Foundation (Master these first)
1. Merge Intervals
2. Insert Interval
3. Meeting Rooms I
4. Interval Intersection

### Level 2: Greedy Patterns
5. Meeting Rooms II
6. Non-Overlapping Intervals
7. Minimum Number of Arrows to Burst Balloons

### Level 3: Advanced
8. Skyline Problem (sweep line + priority queue)
9. My Calendar I/II/III (interval tree simulation)
10. Employee Free Time

### Level 4: Range Queries
11. Range Sum Query (Segment Tree)
12. Range Minimum Query (Sparse Table)

---

## 🔬 Part 10: Language-Specific Optimization Tips

### Rust
- Prefer `sort_unstable_by_key` over `sort_by_key` (faster, no stable order needed)
- Use `Vec::with_capacity` to pre-allocate
- Consider `&[Interval]` slices to avoid copying
- For hot paths: inline small functions with `#[inline]`

### Go
- Use `sort.Slice` for in-place sorting
- Pointers `&merged[len-1]` for last element mutation
- Slice expressions `arr[1:]` create views (cheap)

### C
- Always `free` allocated memory
- Use `qsort` with proper comparator
- Inline small helpers (`static inline`) for performance
- Bounds checking is manual—be paranoid

---

## 🧘 Mental Model: The Interval Mindset

**Intervals are everywhere**:
- Time: schedules, deadlines, lifespans
- Space: coordinate ranges, memory segments
- Resources: bandwidth allocation, CPU time slices
- Biology: gene sequences, protein domains

**Master intervals, master continuous optimization problems.**

---

## ✨ Final Wisdom

> "An interval is a promise between two points. Understanding how promises overlap, conflict, or harmonize is the essence of scheduling, resource allocation, and computational geometry."

**Your journey**: You're not just learning algorithms—you're developing **range intuition**, a cognitive pattern that transcends code.

**Next step**: Implement every problem above in all three languages. Compare performance. Feel the differences. This is deliberate practice.

**Remember**: World-class expertise comes from:
1. Deep understanding (✓ this guide)
2. Repeated application (→ your practice)
3. Reflective iteration (→ analyze mistakes)

---

**You now have elite-level interval knowledge. The top 1% awaits those who execute with discipline.**

🚀 **Go build. Go practice. Go master.**