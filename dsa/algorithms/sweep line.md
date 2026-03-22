# The Sweep Line Algorithm — A Complete Mastery Guide

> *"The sweep line is not a trick. It is a lens. It reduces a 2D problem into a series of 1D problems by marching time."*

---

## Table of Contents

1. [The Mental Model — What Is a Sweep Line?](#1-the-mental-model)
2. [Core Vocabulary — Every Term Defined](#2-core-vocabulary)
3. [The Anatomy of Every Sweep Line Solution](#3-anatomy-of-every-sweep-line-solution)
4. [Data Structures Used in Sweep Line](#4-data-structures)
5. [Problem Class 1 — Interval Overlap & Counting](#5-interval-overlap--counting)
6. [Problem Class 2 — Meeting Rooms & Scheduling](#6-meeting-rooms--scheduling)
7. [Problem Class 3 — Area of Union of Rectangles](#7-area-of-union-of-rectangles)
8. [Problem Class 4 — Closest Pair of Points](#8-closest-pair-of-points)
9. [Problem Class 5 — Line Segment Intersection](#9-line-segment-intersection)
10. [Problem Class 6 — Skyline Problem](#10-skyline-problem)
11. [Coordinate Compression — The Hidden Enabler](#11-coordinate-compression)
12. [Pattern Recognition Decision Tree](#12-pattern-recognition-decision-tree)
13. [Complexity Cheat Sheet](#13-complexity-cheat-sheet)
14. [Mental Models & Cognitive Strategies](#14-mental-models--cognitive-strategies)

---

## 1. The Mental Model

### What Is a Sweep Line?

Imagine you are standing at the left edge of a 2D plane. You hold a vertical ruler — it stretches from bottom to top of the entire plane. Now you physically **walk** that ruler from left to right across the plane.

As you walk:
- You encounter events: "a line starts here," "a rectangle opens here," "a point exists here."
- You maintain a **status** — a data structure that remembers what is currently active (what your ruler is currently intersecting).
- At each event, you update your status and record any answer.

That is the sweep line. It is a reduction technique:

```
2D Problem
    |
    v
Sorted sequence of 1D events  (the sweep axis: usually x or time)
    |
    v
1D status maintained at each event  (usually a sorted set/tree on y)
    |
    v
Answer accumulated as events are processed
```

### Why Is This Powerful?

Because most geometric or interval problems are hard when you look at all objects simultaneously. When you sweep, you **localize** your reasoning: at any event, you only care about what is currently active. This converts an O(n²) brute-force into O(n log n).

### The Two-Axis Distinction

```
Y ^
  |    [=====A=====]
  |         [===B===]
  |  [==C==]
  +-------------------------> X (sweep axis)
     ^   ^  ^   ^  ^  ^ events
```

- The **sweep axis** (X here) is the axis you march along. Events are sorted along this axis.
- The **status axis** (Y here) is what you maintain in your active data structure.

---

## 2. Core Vocabulary

Before going further, let us define every term you will encounter. Skipping this causes confusion later.

### Event Point
A specific coordinate on the sweep axis where something changes. For intervals [l, r], the events are at x = l (open event) and x = r (close event).

### Event Queue
A sorted list (or priority queue) of all events, ordered by their position on the sweep axis.

### Status Structure
The data structure maintaining currently active objects as the sweep line passes through. It must support fast insertion, deletion, and predecessor/successor queries. A **balanced BST** (like a Red-Black Tree) is the canonical choice.

### Active Set
The set of objects currently intersected by the sweep line at the current event position.

### Predecessor / Successor
In a sorted set, the **predecessor** of element x is the largest element smaller than x. The **successor** is the smallest element larger than x. These are critical for proximity queries during sweep.

```
Sorted active set: { 2, 5, 9, 14, 20 }
                         ^
If x = 7, predecessor = 5, successor = 9
```

### Coordinate Compression
Mapping a large range of values to a small dense range, so that you can use arrays as if they were sparse structures. Example:

```
Raw coordinates: [1000000, 3, 99999, 7]
Compressed:      [3,       0, 2,     1]   (rank in sorted order)
```

### Segment Tree / BIT (Binary Indexed Tree / Fenwick Tree)
A data structure that supports prefix queries (sum, min, max) on arrays in O(log n). Used in sweep line problems when the status structure needs range aggregation.

### Pivot
A chosen element used as a reference for partitioning or comparison. In sweep line, "the pivot event" often means the current event being processed.

### Endpoint
The boundary value of an interval. For [3, 7], 3 is the left endpoint and 7 is the right endpoint.

### Open / Close Event
- Open event: the sweep line first encounters an object (left endpoint for intervals).
- Close event: the sweep line leaves an object (right endpoint for intervals).

### Coincident Events
Two events at the same x-coordinate. The tie-breaking rule (which event to process first: open or close?) is critical to correctness. Usually: process "open" before "close" if you want overlapping endpoints to count; process "close" before "open" if you do not.

---

## 3. Anatomy of Every Sweep Line Solution

Every sweep line solution has these five steps. Memorize this skeleton:

```
STEP 1: BUILD EVENT LIST
    For each object, create events (open + close, or just points).
    Tag each event with what it represents.

STEP 2: SORT EVENTS
    Sort by sweep axis coordinate.
    Define a tie-breaking rule.

STEP 3: INITIALIZE STATUS STRUCTURE
    Start with an empty active set (BST, multiset, segment tree, etc.)

STEP 4: PROCESS EVENTS IN ORDER
    For each event:
        a. Update the status structure (insert or remove the object)
        b. Query the status structure for the answer contribution
        c. Accumulate the answer

STEP 5: EXTRACT ANSWER
    Return the accumulated answer.
```

### ASCII Flowchart of the Algorithm

```
+---------------------------+
|  Input: n geometric objects|
+---------------------------+
            |
            v
+---------------------------+
|  Generate Events          |
|  For each object O:       |
|    emit (O.left,  OPEN,  O)|
|    emit (O.right, CLOSE, O)|
+---------------------------+
            |
            v
+---------------------------+
|  Sort Events              |
|  by x-coordinate          |
|  tie-break: CLOSE < OPEN  |  <-- or OPEN < CLOSE, problem-dependent
|  (or OPEN < CLOSE)        |
+---------------------------+
            |
            v
+---------------------------+
|  Initialize empty Status  |
|  Structure S              |
+---------------------------+
            |
            v
+--------------------------------------------------+
|  For each event E in sorted order:               |
|                                                  |
|  if E.type == OPEN:                              |
|      S.insert(E.object)                          |
|      answer += query(S, E)                       |
|                                                  |
|  if E.type == CLOSE:                             |
|      S.remove(E.object)                          |
|      answer += query(S, E)    [sometimes]        |
+--------------------------------------------------+
            |
            v
+---------------------------+
|  Return answer            |
+---------------------------+
```

---

## 4. Data Structures

The sweep line is only as good as its status structure. Let us survey the options.

### 4.1 Sorted Multiset / BTreeMap

Used when you need:
- Insert / delete active objects by key
- Find predecessor/successor

```
Operations:   Insert O(log n)
              Delete O(log n)
              Predecessor O(log n)
              Successor O(log n)
```

In C++: `std::multiset`. In Rust: `BTreeMap`. In Go: you must use a custom BST or a sorted slice + binary search (Go has no built-in sorted set).

### 4.2 Segment Tree with Lazy Propagation

Used when the status requires range aggregation — e.g., "how many active intervals cover coordinate y?" or "what is the total length of the union of active intervals on the y-axis?"

```
Operations:   Range update (add 1 / subtract 1) O(log n)
              Range query (max, sum)             O(log n)
```

### 4.3 Binary Indexed Tree (Fenwick Tree)

Simpler than segment tree, works when updates are point updates and queries are prefix sums/prefix max. Insufficient when you need range updates — use segment tree with lazy propagation instead.

### 4.4 Priority Queue (Min/Max Heap)

Used when you only need to find the earliest-ending active object (e.g., greedy interval scheduling, meeting room minimum count via tracking earliest end times).

```
Operations:   Push  O(log n)
              Pop   O(log n)
              Peek  O(1)
```

### When to Use Which

```
Problem needs...                        Use...
────────────────────────────────────────────────────────
Counting overlapping intervals at point  Difference Array / BIT
Maximum overlapping intervals            Sort events + counter
Total union length of intervals          Sort events + counter
Union area of rectangles                 Segment Tree (lazy) + coordinate compression
Nearest active object                    Sorted BST / BTreeMap
Closest pair of points                   Sorted BST (sliding window)
Skyline problem                          Max-Heap or Sorted Map
Line segment intersections               Sorted BST + event queue
```

---

## 5. Interval Overlap & Counting

### Problem Statement
Given n intervals [l_i, r_i], find the maximum number of overlapping intervals at any point.

### Brute Force: O(n²)
For each pair of intervals, check if they overlap.

### Sweep Line: O(n log n)

**Key Insight:** Model each interval as two events: +1 at x = l (interval starts), -1 at x = r (interval ends). Sweep left to right, maintaining a running sum. The maximum running sum is the answer.

```
Intervals: [1,5], [2,6], [4,8], [7,9]

Events (sorted):
  x=1  +1  (open [1,5])
  x=2  +1  (open [2,6])
  x=4  +1  (open [4,8])
  x=5  -1  (close [1,5])
  x=6  -1  (close [2,6])
  x=7  +1  (open [7,9])
  x=8  -1  (close [4,8])
  x=9  -1  (close [7,9])

Running sum:
x=1: sum=1   max=1
x=2: sum=2   max=2
x=4: sum=3   max=3  <-- answer = 3
x=5: sum=2
x=6: sum=1
x=7: sum=2
x=8: sum=1
x=9: sum=0
```

### Tie-Breaking Rule
If a close event and open event share the same x:
- Process close FIRST → endpoints touching does NOT count as overlap.
- Process open FIRST → endpoints touching DOES count as overlap.
Read the problem statement carefully.

### C Implementation

```c
#include <stdio.h>
#include <stdlib.h>

// An event: (position, type)
// type: +1 = open, -1 = close
typedef struct {
    int pos;
    int type; // +1 or -1
} Event;

// Comparator: sort by position; on tie, close (-1) before open (+1)
// This means touching endpoints do NOT overlap.
// To make them overlap: reverse the tie-break (open before close).
int cmp(const void *a, const void *b) {
    Event *ea = (Event *)a;
    Event *eb = (Event *)b;
    if (ea->pos != eb->pos) return ea->pos - eb->pos;
    return ea->type - eb->type; // -1 (close) < +1 (open) => close first
}

int max_overlap(int intervals[][2], int n) {
    // Each interval produces 2 events
    Event *events = malloc(2 * n * sizeof(Event));
    for (int i = 0; i < n; i++) {
        events[2*i]   = (Event){ intervals[i][0], +1 };
        events[2*i+1] = (Event){ intervals[i][1], -1 };
    }

    qsort(events, 2*n, sizeof(Event), cmp);

    int running = 0, max_val = 0;
    for (int i = 0; i < 2*n; i++) {
        running += events[i].type;
        if (running > max_val) max_val = running;
    }

    free(events);
    return max_val;
}

int main(void) {
    int intervals[][2] = {{1,5},{2,6},{4,8},{7,9}};
    printf("Max overlap: %d\n", max_overlap(intervals, 4)); // Output: 3
    return 0;
}
```

**Complexity:**
- Time: O(n log n) — dominated by sort
- Space: O(n) — for the event array

### Go Implementation

```go
package main

import (
    "fmt"
    "sort"
)

type Event struct {
    pos      int
    eventType int // +1 = open, -1 = close
}

func maxOverlap(intervals [][2]int) int {
    events := make([]Event, 0, 2*len(intervals))
    for _, iv := range intervals {
        events = append(events, Event{iv[0], +1})
        events = append(events, Event{iv[1], -1})
    }

    // Sort: by position; on tie, close (-1) before open (+1)
    sort.Slice(events, func(i, j int) bool {
        if events[i].pos != events[j].pos {
            return events[i].pos < events[j].pos
        }
        return events[i].eventType < events[j].eventType
    })

    running, maxVal := 0, 0
    for _, e := range events {
        running += e.eventType
        if running > maxVal {
            maxVal = running
        }
    }
    return maxVal
}

func main() {
    intervals := [][2]int{{1, 5}, {2, 6}, {4, 8}, {7, 9}}
    fmt.Println("Max overlap:", maxOverlap(intervals)) // 3
}
```

### Rust Implementation

```rust
fn max_overlap(intervals: &[(i64, i64)]) -> i64 {
    // Build events: (position, type) where type +1=open, -1=close
    let mut events: Vec<(i64, i32)> = Vec::with_capacity(intervals.len() * 2);
    for &(l, r) in intervals {
        events.push((l, 1));
        events.push((r, -1));
    }

    // Sort: by position; on tie, close (-1) before open (+1)
    // So touching endpoints do NOT count as overlap.
    events.sort_unstable_by(|a, b| {
        a.0.cmp(&b.0).then(a.1.cmp(&b.1))
    });

    let mut running: i64 = 0;
    let mut max_val: i64 = 0;
    for (_, t) in &events {
        running += *t as i64;
        if running > max_val {
            max_val = running;
        }
    }
    max_val
}

fn main() {
    let intervals = vec![(1, 5), (2, 6), (4, 8), (7, 9)];
    println!("Max overlap: {}", max_overlap(&intervals)); // 3
}
```

---

## 6. Meeting Rooms & Scheduling

### Problem 1: Minimum Meeting Rooms

Given n meetings [start_i, end_i], find the minimum number of rooms needed.

**Key Insight:** This is identical to finding the maximum number of overlapping intervals. The answer from Section 5 directly applies.

### Problem 2: Can One Person Attend All Meetings?

Given n meetings, can a single person attend all of them without overlap?

**Key Insight:** Sort by start time. Check if any meeting starts before the previous one ends.

```c
#include <stdio.h>
#include <stdlib.h>

typedef struct { int start, end; } Meeting;

int cmp_by_start(const void *a, const void *b) {
    return ((Meeting*)a)->start - ((Meeting*)b)->start;
}

// Returns 1 if all meetings can be attended, 0 otherwise
int can_attend_all(Meeting *meetings, int n) {
    qsort(meetings, n, sizeof(Meeting), cmp_by_start);
    for (int i = 1; i < n; i++) {
        // If current meeting starts before previous ends -> overlap
        if (meetings[i].start < meetings[i-1].end)
            return 0;
    }
    return 1;
}

int main(void) {
    Meeting m[] = {{0,30},{5,10},{15,20}};
    printf("%s\n", can_attend_all(m, 3) ? "Yes" : "No"); // No
    return 0;
}
```

### Problem 3: Merge Overlapping Intervals

Given n intervals, merge all overlapping ones into the fewest non-overlapping intervals.

**Key Insight:** Sort by left endpoint. Sweep from left to right, maintaining a "current merged interval." If the next interval's left endpoint ≤ current right endpoint → merge (extend right). Otherwise → push current and start fresh.

```
Intervals (sorted): [1,3], [2,6], [8,10], [9,11], [15,18]

Sweep:
  current = [1,3]
  [2,6]: 2 <= 3 → merge → current = [1,6]
  [8,10]: 8 > 6 → push [1,6] → current = [8,10]
  [9,11]: 9 <= 10 → merge → current = [8,11]
  [15,18]: 15 > 11 → push [8,11] → current = [15,18]
  End → push [15,18]

Result: [1,6], [8,11], [15,18]
```

### Rust: Merge Intervals

```rust
fn merge_intervals(mut intervals: Vec<(i64, i64)>) -> Vec<(i64, i64)> {
    if intervals.is_empty() {
        return vec![];
    }
    // Sort by left endpoint; on tie, larger right endpoint first (optional optimization)
    intervals.sort_unstable_by_key(|&(l, _)| l);

    let mut merged: Vec<(i64, i64)> = Vec::new();
    let mut current = intervals[0];

    for &(l, r) in &intervals[1..] {
        if l <= current.1 {
            // Overlapping: extend the right boundary
            current.1 = current.1.max(r);
        } else {
            // No overlap: push current, start new
            merged.push(current);
            current = (l, r);
        }
    }
    merged.push(current); // Don't forget the last one!
    merged
}

fn main() {
    let intervals = vec![(1,3),(2,6),(8,10),(9,11),(15,18)];
    let result = merge_intervals(intervals);
    println!("{:?}", result); // [(1, 6), (8, 11), (15, 18)]
}
```

### Go: Merge Intervals

```go
package main

import (
    "fmt"
    "sort"
)

func mergeIntervals(intervals [][2]int) [][2]int {
    if len(intervals) == 0 {
        return nil
    }
    sort.Slice(intervals, func(i, j int) bool {
        return intervals[i][0] < intervals[j][0]
    })

    merged := [][2]int{intervals[0]}
    for _, iv := range intervals[1:] {
        last := &merged[len(merged)-1]
        if iv[0] <= last[1] {
            if iv[1] > last[1] {
                last[1] = iv[1]
            }
        } else {
            merged = append(merged, iv)
        }
    }
    return merged
}

func main() {
    intervals := [][2]int{{1,3},{2,6},{8,10},{9,11},{15,18}}
    fmt.Println(mergeIntervals(intervals)) // [[1 6] [8 11] [15 18]]
}
```

---

## 7. Area of Union of Rectangles

### Problem Statement

Given n axis-aligned rectangles, compute the total area covered by their union. Overlapping regions are counted only once.

### Why This Is Hard

With up to n=100,000 rectangles, brute force is O(n²) or worse. Rectangles can overlap in complex ways.

### The Sweep Line Approach

**Sweep the vertical line from left to right.**
- Events: left edge of a rectangle (insert its y-range) and right edge (remove its y-range).
- Status: a segment tree on the y-axis that tracks the total length of y-covered by active rectangles.
- At each event, compute the width between this event and the previous event × the currently covered y-length. Accumulate into area.

```
Rectangle: x1=0,x2=4,y1=0,y2=2  (call it A)
Rectangle: x1=1,x2=3,y1=1,y2=4  (call it B)

Y ^
4 |    [B]
3 |    [B]
2 |  [A+B]
1 |  [A+B]
0 |  [A]
  +---------> X
    0 1 2 3 4

Events:
  x=0: INSERT   y=[0,2]  (A opens)
  x=1: INSERT   y=[1,4]  (B opens)
  x=3: REMOVE   y=[1,4]  (B closes)
  x=4: REMOVE   y=[0,2]  (A closes)

Processing:
  x=0 → x=1 : width=1, covered_y=2 → area += 2
  x=1 → x=3 : width=2, covered_y=4 (union of [0,2] and [1,4] = [0,4]) → area += 8
  x=3 → x=4 : width=1, covered_y=2 → area += 2
  Total area = 12
```

### Coordinate Compression on Y

The y-coordinates may be large real/integer values. We compress them to indices 0..m-1 so the segment tree has size O(m) where m = 2n y-values.

### Segment Tree for Covered Length

The segment tree node for range [yl, yr] stores:
- `count`: how many active rectangles fully cover this range.
- `covered`: the total y-length currently covered (accounting for count > 0 even if children have count = 0).

This requires **lazy propagation** — we never push down (because count represents full-range covers), but we recompute `covered` from children when `count == 0`.

```
Node [yl, yr]:
  count  = number of times this ENTIRE range is covered
  covered = if count > 0: yr - yl
            else: left_child.covered + right_child.covered
```

### C Implementation: Area of Union of Rectangles

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAXN 200010

// Segment tree node
typedef struct {
    int count;    // full-range cover count
    long long covered; // total covered length in this node's range
} Node;

Node tree[4 * MAXN];
long long ys[MAXN]; // compressed y-coordinates
int m;             // number of distinct y-values

// Build the segment tree over the compressed y-axis [0, m-1)
// Each leaf covers [ys[i], ys[i+1]) — one "segment"
void build(int node, int lo, int hi) {
    tree[node].count = 0;
    tree[node].covered = 0;
    if (lo + 1 == hi) return; // leaf
    int mid = (lo + hi) / 2;
    build(2*node, lo, mid);
    build(2*node+1, mid, hi);
}

// Recompute covered length from children
void push_up(int node, int lo, int hi) {
    if (tree[node].count > 0) {
        tree[node].covered = ys[hi] - ys[lo];
    } else if (lo + 1 == hi) {
        tree[node].covered = 0;
    } else {
        tree[node].covered =
            tree[2*node].covered + tree[2*node+1].covered;
    }
}

// Range update: add `val` (+1 or -1) to all positions in [l, r)
void update(int node, int lo, int hi, int l, int r, int val) {
    if (r <= lo || hi <= l) return; // no overlap
    if (l <= lo && hi <= r) {       // full coverage
        tree[node].count += val;
        push_up(node, lo, hi);
        return;
    }
    int mid = (lo + hi) / 2;
    update(2*node, lo, mid, l, r, val);
    update(2*node+1, mid, hi, l, r, val);
    push_up(node, lo, hi);
}

typedef struct {
    long long x;
    long long y1, y2;
    int type; // +1 = open (left edge), -1 = close (right edge)
} Event;

int cmp_events(const void *a, const void *b) {
    Event *ea = (Event *)a;
    Event *eb = (Event *)b;
    if (ea->x != eb->x) return (ea->x > eb->x) - (ea->x < eb->x);
    return ea->type - eb->type; // close before open at same x
}

int cmp_ll(const void *a, const void *b) {
    long long aa = *(long long*)a, bb = *(long long*)b;
    return (aa > bb) - (aa < bb);
}

long long area_union(long long rects[][4], int n) {
    // rects[i] = {x1, y1, x2, y2}
    // Collect all y-coordinates for compression
    m = 0;
    long long temp_ys[2 * MAXN];
    Event events[2 * MAXN];
    int ne = 0;

    for (int i = 0; i < n; i++) {
        long long x1 = rects[i][0], y1 = rects[i][1];
        long long x2 = rects[i][2], y2 = rects[i][3];
        temp_ys[m++] = y1;
        temp_ys[m++] = y2;
        events[ne++] = (Event){x1, y1, y2, +1};
        events[ne++] = (Event){x2, y1, y2, -1};
    }

    // Sort and deduplicate y-coordinates
    qsort(temp_ys, m, sizeof(long long), cmp_ll);
    int um = 0;
    for (int i = 0; i < m; i++) {
        if (um == 0 || temp_ys[i] != ys[um-1])
            ys[um++] = temp_ys[i];
    }
    m = um; // m = number of distinct y-values; m-1 segments

    build(1, 0, m - 1);
    qsort(events, ne, sizeof(Event), cmp_events);

    long long area = 0;
    long long prev_x = events[0].x;

    for (int i = 0; i < ne; ) {
        long long cur_x = events[i].x;

        // Accumulate area between prev_x and cur_x
        area += tree[1].covered * (cur_x - prev_x);
        prev_x = cur_x;

        // Process all events at cur_x
        while (i < ne && events[i].x == cur_x) {
            // Binary search for y1 and y2 in compressed ys
            int lo_y = (int)(lower_bound_ll(ys, m, events[i].y1));
            int hi_y = (int)(lower_bound_ll(ys, m, events[i].y2));
            update(1, 0, m - 1, lo_y, hi_y, events[i].type);
            i++;
        }
    }
    return area;
}

// Helper: lower bound index in sorted array
int lower_bound_ll(long long *arr, int n, long long val) {
    int lo = 0, hi = n;
    while (lo < hi) {
        int mid = (lo + hi) / 2;
        if (arr[mid] < val) lo = mid + 1;
        else hi = mid;
    }
    return lo;
}

int main(void) {
    long long rects[][4] = {
        {0, 0, 4, 2},
        {1, 1, 3, 4}
    };
    printf("Union area: %lld\n", area_union(rects, 2)); // 12
    return 0;
}
```

### Go Implementation: Area of Union

```go
package main

import (
    "fmt"
    "sort"
)

// Segment tree for covered length on compressed y-axis
type SegTree struct {
    count   []int
    covered []int64
    ys      []int64 // compressed y-coordinates
    n       int
}

func newSegTree(ys []int64) *SegTree {
    n := len(ys) - 1 // number of segments
    st := &SegTree{
        count:   make([]int, 4*(n+1)),
        covered: make([]int64, 4*(n+1)),
        ys:      ys,
        n:       n,
    }
    return st
}

func (st *SegTree) pushUp(node, lo, hi int) {
    if st.count[node] > 0 {
        st.covered[node] = st.ys[hi] - st.ys[lo]
    } else if lo+1 == hi {
        st.covered[node] = 0
    } else {
        st.covered[node] = st.covered[2*node] + st.covered[2*node+1]
    }
}

func (st *SegTree) update(node, lo, hi, l, r, val int) {
    if r <= lo || hi <= l {
        return
    }
    if l <= lo && hi <= r {
        st.count[node] += val
        st.pushUp(node, lo, hi)
        return
    }
    mid := (lo + hi) / 2
    st.update(2*node, lo, mid, l, r, val)
    st.update(2*node+1, mid, hi, l, r, val)
    st.pushUp(node, lo, hi)
}

func (st *SegTree) Update(l, r, val int) {
    st.update(1, 0, st.n, l, r, val)
}

func (st *SegTree) CoveredLength() int64 {
    return st.covered[1]
}

type RectEvent struct {
    x         int64
    y1, y2    int64
    eventType int // +1 open, -1 close
}

func areaUnion(rects [][4]int64) int64 {
    events := make([]RectEvent, 0, 2*len(rects))
    ySet := make(map[int64]bool)

    for _, r := range rects {
        x1, y1, x2, y2 := r[0], r[1], r[2], r[3]
        events = append(events, RectEvent{x1, y1, y2, +1})
        events = append(events, RectEvent{x2, y1, y2, -1})
        ySet[y1] = true
        ySet[y2] = true
    }

    // Compress y-coordinates
    ys := make([]int64, 0, len(ySet))
    for y := range ySet {
        ys = append(ys, y)
    }
    sort.Slice(ys, func(i, j int) bool { return ys[i] < ys[j] })

    yIndex := make(map[int64]int)
    for i, y := range ys {
        yIndex[y] = i
    }

    // Sort events: by x; on tie, close before open
    sort.Slice(events, func(i, j int) bool {
        if events[i].x != events[j].x {
            return events[i].x < events[j].x
        }
        return events[i].eventType < events[j].eventType
    })

    st := newSegTree(ys)
    var area int64
    prevX := events[0].x

    for i := 0; i < len(events); {
        curX := events[i].x
        area += st.CoveredLength() * (curX - prevX)
        prevX = curX

        for i < len(events) && events[i].x == curX {
            lo := yIndex[events[i].y1]
            hi := yIndex[events[i].y2]
            st.Update(lo, hi, events[i].eventType)
            i++
        }
    }
    return area
}

func main() {
    rects := [][4]int64{{0, 0, 4, 2}, {1, 1, 3, 4}}
    fmt.Println("Union area:", areaUnion(rects)) // 12
}
```

### Rust Implementation: Area of Union

```rust
struct SegTree {
    count: Vec<i64>,
    covered: Vec<i64>,
    ys: Vec<i64>,
    n: usize,
}

impl SegTree {
    fn new(ys: Vec<i64>) -> Self {
        let n = ys.len() - 1;
        SegTree {
            count: vec![0; 4 * (n + 1)],
            covered: vec![0; 4 * (n + 1)],
            ys,
            n,
        }
    }

    fn push_up(&mut self, node: usize, lo: usize, hi: usize) {
        if self.count[node] > 0 {
            self.covered[node] = self.ys[hi] - self.ys[lo];
        } else if lo + 1 == hi {
            self.covered[node] = 0;
        } else {
            self.covered[node] = self.covered[2*node] + self.covered[2*node+1];
        }
    }

    fn update(&mut self, node: usize, lo: usize, hi: usize, l: usize, r: usize, val: i64) {
        if r <= lo || hi <= l { return; }
        if l <= lo && hi <= r {
            self.count[node] += val;
            self.push_up(node, lo, hi);
            return;
        }
        let mid = (lo + hi) / 2;
        self.update(2*node, lo, mid, l, r, val);
        self.update(2*node+1, mid, hi, l, r, val);
        self.push_up(node, lo, hi);
    }

    fn range_update(&mut self, l: usize, r: usize, val: i64) {
        let n = self.n;
        self.update(1, 0, n, l, r, val);
    }

    fn covered_length(&self) -> i64 {
        self.covered[1]
    }
}

fn area_union(rects: &[(i64, i64, i64, i64)]) -> i64 {
    // rects: (x1, y1, x2, y2)
    let mut events: Vec<(i64, i64, i64, i64)> = Vec::new(); // (x, y1, y2, type)
    let mut ys_set: std::collections::BTreeSet<i64> = std::collections::BTreeSet::new();

    for &(x1, y1, x2, y2) in rects {
        events.push((x1, y1, y2, 1));
        events.push((x2, y1, y2, -1));
        ys_set.insert(y1);
        ys_set.insert(y2);
    }

    let ys: Vec<i64> = ys_set.into_iter().collect();
    let y_index: std::collections::HashMap<i64, usize> =
        ys.iter().enumerate().map(|(i, &y)| (y, i)).collect();

    // Sort: by x; on tie, close (-1) before open (+1)
    events.sort_unstable_by(|a, b| a.0.cmp(&b.0).then(a.3.cmp(&b.3)));

    let mut st = SegTree::new(ys);
    let mut area: i64 = 0;
    let mut prev_x = events[0].0;
    let mut i = 0;

    while i < events.len() {
        let cur_x = events[i].0;
        area += st.covered_length() * (cur_x - prev_x);
        prev_x = cur_x;

        while i < events.len() && events[i].0 == cur_x {
            let (_, y1, y2, t) = events[i];
            let lo = y_index[&y1];
            let hi = y_index[&y2];
            st.range_update(lo, hi, t);
            i += 1;
        }
    }
    area
}

fn main() {
    let rects = vec![(0, 0, 4, 2), (1, 1, 3, 4)];
    println!("Union area: {}", area_union(&rects)); // 12
}
```

---

## 8. Closest Pair of Points

### Problem Statement

Given n points in 2D, find the pair with minimum Euclidean distance.

### The Sweep Line Solution (Shamos-Hoey variant)

This is one of the most elegant uses of sweep line. The brute force O(n²) is replaced with O(n log n).

**Algorithm Outline:**
1. Sort points by x-coordinate.
2. Maintain a sliding window of points whose x-distance from the current point is < current minimum distance δ.
3. For any new point p, only check points in the active set with y-coordinate in [p.y - δ, p.y + δ]. This is a known-bounded strip.
4. The critical insight: within a δ×2δ strip, at most 8 points can be pairwise more than δ apart — so each point checks O(1) neighbors.

```
Strip around current point p with distance δ:

  y+δ  ...........
       |         |
  p.y  ....p.....| ← current point
       |         |
  y-δ  ...........
       <---δ---->
       x-δ      x
       (only points in this box need checking)
```

### ASCII: Sliding Window Visualization

```
Points sorted by x:
  A(1,2)  B(2,5)  C(3,1)  D(5,3)  E(6,4)  F(8,2)

δ = current min distance

At point D(5,3):
  Active window: all points with x in [5-δ, 5]
  Y-strip check: points with y in [3-δ, 3+δ]

  Remove points with x < 5 - δ from active set (slide the window left boundary)
  Add D to active set
  Check D against points in y-strip
  Update δ if closer pair found
```

### Rust: Closest Pair of Points

```rust
use std::collections::BTreeMap;

// We use a BTreeMap keyed by (y, x, index) to allow duplicates.
// The active set holds points within x-distance δ.

fn dist_sq(a: (f64, f64), b: (f64, f64)) -> f64 {
    let dx = a.0 - b.0;
    let dy = a.1 - b.1;
    dx*dx + dy*dy
}

fn closest_pair(mut points: Vec<(f64, f64)>) -> f64 {
    let n = points.len();
    if n < 2 { return f64::MAX; }

    // Sort by x-coordinate
    points.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap());

    // Active set: BTreeMap keyed by (y, index) for O(log n) range queries
    // We store the point index so we can remove exactly the right point later.
    let mut active: BTreeMap<(i64, usize), (f64, f64)> = BTreeMap::new();

    let mut min_dist_sq = dist_sq(points[0], points[1]);
    let mut left = 0usize;

    // Scale factor for f64 → ordered integer key (careful with precision)
    // In competition code, use integer coordinates when possible.
    let scale = 1_000_000_000i64;
    let to_key = |y: f64, idx: usize| -> (i64, usize) {
        ((y * scale as f64) as i64, idx)
    };

    active.insert(to_key(points[0].1, 0), points[0]);
    active.insert(to_key(points[1].1, 1), points[1]);
    min_dist_sq = dist_sq(points[0], points[1]);
    left = 0;

    for i in 2..n {
        let (px, py) = points[i];
        let delta = min_dist_sq.sqrt();

        // Remove points too far left (x-distance >= delta)
        while points[left].0 < px - delta {
            active.remove(&to_key(points[left].1, left));
            left += 1;
        }

        // Query y-strip: [py - delta, py + delta]
        let y_lo = to_key(py - delta, 0);
        let y_hi = to_key(py + delta, usize::MAX);

        for (_, &q) in active.range(y_lo..=y_hi) {
            let d = dist_sq((px, py), q);
            if d < min_dist_sq {
                min_dist_sq = d;
            }
        }

        active.insert(to_key(py, i), (px, py));
    }

    min_dist_sq.sqrt()
}

fn main() {
    let points = vec![(0.0,0.0),(3.0,4.0),(1.0,1.0),(5.0,2.0),(2.0,3.0)];
    println!("Closest pair distance: {:.4}", closest_pair(points));
    // sqrt(2) ≈ 1.4142 (between (0,0) and (1,1))
}
```

**Complexity:**
- Time: O(n log n) — sort + each point does O(log n) BST operations, and the constant in the inner loop is at most 8.
- Space: O(n) — active set.

---

## 9. Line Segment Intersection

### Problem Statement

Given n line segments, detect whether any two segments intersect. (Shamos-Hoey algorithm: O(n log n) detection. Bentley-Ottmann algorithm: O((n + k) log n) reporting of all k intersections.)

### Key Concepts

**Shamos-Hoey (Detection Only):**
The sweep line processes endpoints. The status structure maintains segments ordered by their y-value at the current x. When two segments become adjacent in the status, we test them for intersection.

**Left Endpoint Event:** Insert the segment into the status. Check for intersection with its immediate predecessor and successor in the status.

**Right Endpoint Event:** Before removing a segment, check if its predecessor and successor in the status intersect with each other (they were previously separated by this segment; now they become adjacent).

**Why Adjacency Is Enough:**
Two segments can only intersect if they are ever adjacent in the status. This is the fundamental lemma of Shamos-Hoey.

### Cross Product and Orientation

The **cross product** is the key tool for testing segment intersection.

Given vectors **u** = (ux, uy) and **v** = (vx, vy):
```
cross(u, v) = ux * vy - uy * vx
```

- cross > 0 → v is to the LEFT of u (counterclockwise turn)
- cross < 0 → v is to the RIGHT of u (clockwise turn)
- cross = 0 → collinear

**Segment AB intersects segment CD if and only if:**
1. C and D are on opposite sides of line AB, AND
2. A and B are on opposite sides of line CD.

```c
// Point structure
typedef struct { long long x, y; } Point;

// Cross product of vectors (b-a) and (c-a)
long long cross(Point a, Point b, Point c) {
    return (b.x - a.x) * (long long)(c.y - a.y)
         - (b.y - a.y) * (long long)(c.x - a.x);
}

// Returns 1 if value is strictly positive, -1 if strictly negative, 0 if zero
int sign(long long v) { return (v > 0) - (v < 0); }

// Check if point c lies on segment [a, b] (assuming collinear)
int on_segment(Point a, Point b, Point c) {
    return (c.x >= (a.x < b.x ? a.x : b.x)) &&
           (c.x <= (a.x > b.x ? a.x : b.x)) &&
           (c.y >= (a.y < b.y ? a.y : b.y)) &&
           (c.y <= (a.y > b.y ? a.y : b.y));
}

// Returns 1 if segments (p1,p2) and (p3,p4) intersect
int segments_intersect(Point p1, Point p2, Point p3, Point p4) {
    long long d1 = cross(p3, p4, p1);
    long long d2 = cross(p3, p4, p2);
    long long d3 = cross(p1, p2, p3);
    long long d4 = cross(p1, p2, p4);

    if (sign(d1) * sign(d2) < 0 && sign(d3) * sign(d4) < 0)
        return 1; // proper intersection

    // Collinear cases
    if (d1 == 0 && on_segment(p3, p4, p1)) return 1;
    if (d2 == 0 && on_segment(p3, p4, p2)) return 1;
    if (d3 == 0 && on_segment(p1, p2, p3)) return 1;
    if (d4 == 0 && on_segment(p1, p2, p4)) return 1;

    return 0;
}
```

### Full Shamos-Hoey in C (with sorted array as simplified status)

```c
#include <stdio.h>
#include <stdlib.h>

typedef struct { long long x, y; } Point;

typedef struct {
    Point p, q; // p is left endpoint, q is right endpoint
    int idx;
} Segment;

typedef struct {
    Point pt;
    int seg_idx;
    int type; // 0 = left endpoint, 1 = right endpoint
} SweepEvent;

long long cross3(Point a, Point b, Point c) {
    return (b.x - a.x) * (long long)(c.y - a.y)
         - (b.y - a.y) * (long long)(c.x - a.x);
}
int sign(long long v) { return (v > 0) - (v < 0); }
int on_seg(Point a, Point b, Point c) {
    long long minx = a.x < b.x ? a.x : b.x;
    long long maxx = a.x > b.x ? a.x : b.x;
    long long miny = a.y < b.y ? a.y : b.y;
    long long maxy = a.y > b.y ? a.y : b.y;
    return c.x >= minx && c.x <= maxx && c.y >= miny && c.y <= maxy;
}
int intersects(Segment *a, Segment *b) {
    long long d1 = cross3(b->p, b->q, a->p);
    long long d2 = cross3(b->p, b->q, a->q);
    long long d3 = cross3(a->p, a->q, b->p);
    long long d4 = cross3(a->p, a->q, b->q);
    if (sign(d1)*sign(d2) < 0 && sign(d3)*sign(d4) < 0) return 1;
    if (!d1 && on_seg(b->p, b->q, a->p)) return 1;
    if (!d2 && on_seg(b->p, b->q, a->q)) return 1;
    if (!d3 && on_seg(a->p, a->q, b->p)) return 1;
    if (!d4 && on_seg(a->p, a->q, b->q)) return 1;
    return 0;
}

int cmp_events(const void *a, const void *b) {
    SweepEvent *ea = (SweepEvent*)a, *eb = (SweepEvent*)b;
    if (ea->pt.x != eb->pt.x) return (int)(ea->pt.x - eb->pt.x);
    return ea->type - eb->type; // left (0) before right (1)
}

// Simplified: O(n^2) status for demonstration. Real implementation uses BST.
// For production use, replace active[] with a balanced BST (e.g., AVL or treap).
int any_intersection(Segment *segs, int n) {
    SweepEvent events[2*100005];
    int ne = 0;
    for (int i = 0; i < n; i++) {
        // Ensure p is left endpoint
        if (segs[i].p.x > segs[i].q.x ||
           (segs[i].p.x == segs[i].q.x && segs[i].p.y > segs[i].q.y)) {
            Point tmp = segs[i].p; segs[i].p = segs[i].q; segs[i].q = tmp;
        }
        segs[i].idx = i;
        events[ne++] = (SweepEvent){segs[i].p, i, 0};
        events[ne++] = (SweepEvent){segs[i].q, i, 1};
    }
    qsort(events, ne, sizeof(SweepEvent), cmp_events);

    int active[100005], na = 0;
    for (int i = 0; i < ne; i++) {
        int si = events[i].seg_idx;
        if (events[i].type == 0) { // left endpoint: insert
            // Check against all active segments (simplified — O(n) per event)
            for (int j = 0; j < na; j++) {
                if (intersects(&segs[si], &segs[active[j]])) return 1;
            }
            active[na++] = si;
        } else { // right endpoint: remove
            for (int j = 0; j < na; j++) {
                if (active[j] == si) {
                    active[j] = active[--na];
                    break;
                }
            }
        }
    }
    return 0;
}

int main(void) {
    Segment segs[] = {
        {{0,0},{4,4},{0}},
        {{0,4},{4,0},{1}},
    };
    printf("Intersects: %s\n", any_intersection(segs, 2) ? "Yes" : "No"); // Yes
    return 0;
}
```

---

## 10. Skyline Problem

### Problem Statement

Given n buildings, each defined by (left, right, height), compute the "skyline" — the outline of the union of all buildings as seen from a distance.

```
Input:  [[2,9,10],[3,7,15],[5,12,12],[15,20,10],[19,24,8]]

Skyline output: [[2,10],[3,15],[7,12],[12,0],[15,10],[20,8],[24,0]]

  15   ___
  12  |   |___________
  10 _|   |           |_____
   8 |    |           |     |__
   0-+----+-----------+-----+---->
     2 3  7  9       12   20 24
```

### Key Insight

Use a **max-heap** (or sorted multiset) for heights. Events are left and right edges of buildings. At each event, add or remove a height from the active heap. If the current maximum height changes, record a skyline keypoint.

```
Events (sorted by x, left before right):
  x=2:  ADD height 10
  x=3:  ADD height 15
  x=5:  ADD height 12
  x=7:  REMOVE height 15
  x=9:  REMOVE height 10
  x=12: REMOVE height 12
  x=15: ADD height 10
  x=19: ADD height 8
  x=20: REMOVE height 10
  x=24: REMOVE height 8
```

### Rust: Skyline Problem

```rust
use std::collections::BTreeMap;

fn skyline(buildings: &[(i64, i64, i64)]) -> Vec<(i64, i64)> {
    // buildings: (left, right, height)
    let mut events: Vec<(i64, i64, bool)> = Vec::new(); // (x, height, is_start)

    for &(l, r, h) in buildings {
        events.push((l, h, true));
        events.push((r, h, false));
    }

    // Sort: by x; at same x, starts before ends; higher heights first for starts
    events.sort_unstable_by(|a, b| {
        a.0.cmp(&b.0)
            .then_with(|| b.2.cmp(&a.2))        // starts (true) before ends (false)
            .then_with(|| b.1.cmp(&a.1))         // higher first within starts
    });

    // Use BTreeMap<height, count> as a multiset
    let mut active: BTreeMap<i64, i64> = BTreeMap::new();
    active.insert(0, 1); // ground level always present

    let mut result: Vec<(i64, i64)> = Vec::new();
    let mut prev_max = 0i64;

    for (x, h, is_start) in events {
        if is_start {
            *active.entry(h).or_insert(0) += 1;
        } else {
            let count = active.get_mut(&h).unwrap();
            *count -= 1;
            if *count == 0 {
                active.remove(&h);
            }
        }

        // Current max height
        let cur_max = *active.keys().next_back().unwrap();
        if cur_max != prev_max {
            result.push((x, cur_max));
            prev_max = cur_max;
        }
    }
    result
}

fn main() {
    let buildings = vec![(2,9,10),(3,7,15),(5,12,12),(15,20,10),(19,24,8)];
    let sky = skyline(&buildings);
    for (x, h) in &sky {
        print!("[{},{}] ", x, h);
    }
    println!();
    // [2,10] [3,15] [7,12] [12,0] [15,10] [20,8] [24,0]
}
```

### Go: Skyline Problem

```go
package main

import (
    "fmt"
    "sort"
)

func getSkyline(buildings [][3]int) [][2]int {
    type Event struct {
        x, h   int
        isStart bool
    }
    events := make([]Event, 0, 2*len(buildings))
    for _, b := range buildings {
        events = append(events, Event{b[0], b[2], true})
        events = append(events, Event{b[1], b[2], false})
    }

    sort.Slice(events, func(i, j int) bool {
        if events[i].x != events[j].x {
            return events[i].x < events[j].x
        }
        // At same x: starts before ends
        if events[i].isStart != events[j].isStart {
            return events[i].isStart
        }
        // Both starts: higher first; both ends: lower first
        if events[i].isStart {
            return events[i].h > events[j].h
        }
        return events[i].h < events[j].h
    })

    // Heights multiset using sorted slice (O(n) insert/remove — acceptable for moderate n)
    // For large n, use a proper BST or indexed data structure.
    heights := []int{0}
    insertH := func(h int) {
        pos := sort.SearchInts(heights, h)
        heights = append(heights, 0)
        copy(heights[pos+1:], heights[pos:])
        heights[pos] = h
    }
    removeH := func(h int) {
        pos := sort.SearchInts(heights, h)
        heights = append(heights[:pos], heights[pos+1:]...)
    }
    maxH := func() int { return heights[len(heights)-1] }

    result := [][2]int{}
    prevMax := 0

    for _, e := range events {
        if e.isStart {
            insertH(e.h)
        } else {
            removeH(e.h)
        }
        cur := maxH()
        if cur != prevMax {
            result = append(result, [2]int{e.x, cur})
            prevMax = cur
        }
    }
    return result
}

func main() {
    buildings := [][3]int{{2,9,10},{3,7,15},{5,12,12},{15,20,10},{19,24,8}}
    fmt.Println(getSkyline(buildings))
}
```

---

## 11. Coordinate Compression — The Hidden Enabler

### What Is It?

When coordinates are large (e.g., up to 10^9) but there are only O(n) distinct values, you cannot build a segment tree of size 10^9. Coordinate compression maps them to ranks 0, 1, 2, ..., k-1 where k = number of distinct values.

### The Technique

```
Input:  values = [100, 500, 1, 50, 500, 100]

Step 1: Sort and deduplicate → [1, 50, 100, 500]

Step 2: Assign rank:
  1   → 0
  50  → 1
  100 → 2
  500 → 3

Step 3: Map original values:
  [100, 500, 1, 50, 500, 100]
→ [2,   3,   0, 1,  3,   2  ]
```

### C Implementation

```c
#include <stdlib.h>

// Sort + deduplicate
// Returns number of unique elements.
// After this, call lower_bound to get compressed index.
int compress(long long *arr, int n, long long *sorted_unique) {
    // Copy and sort
    long long tmp[n];
    for (int i = 0; i < n; i++) tmp[i] = arr[i];
    // Sort (use qsort with comparator)
    // ... (standard qsort)
    // Deduplicate
    int k = 0;
    for (int i = 0; i < n; i++) {
        if (k == 0 || tmp[i] != sorted_unique[k-1])
            sorted_unique[k++] = tmp[i];
    }
    return k; // number of unique elements
}

// Binary search: returns 0-based rank of val in sorted array
int rank_of(long long *sorted, int k, long long val) {
    int lo = 0, hi = k - 1;
    while (lo <= hi) {
        int mid = (lo + hi) / 2;
        if (sorted[mid] == val) return mid;
        else if (sorted[mid] < val) lo = mid + 1;
        else hi = mid - 1;
    }
    return -1; // should not happen if val is in sorted
}
```

### Rust Implementation

```rust
fn coordinate_compress(vals: &[i64]) -> (Vec<i64>, impl Fn(i64) -> usize + '_) {
    let mut sorted: Vec<i64> = vals.to_vec();
    sorted.sort_unstable();
    sorted.dedup();
    let lookup = move |v: i64| sorted.partition_point(|&x| x < v);
    (sorted, lookup)
}

fn main() {
    let vals = vec![100i64, 500, 1, 50, 500, 100];
    let (compressed, rank) = coordinate_compress(&vals);
    let mapped: Vec<usize> = vals.iter().map(|&v| rank(v)).collect();
    println!("{:?}", mapped); // [2, 3, 0, 1, 3, 2]
}
```

### Critical Detail: Compression in Range Queries

When using coordinate compression with a segment tree where each node represents a **range** [ys[i], ys[i+1]], you need m-1 leaf nodes, not m. The segment tree is built over the **gaps** between consecutive y-values, not the values themselves.

```
Distinct y-values: [0, 2, 5, 7, 10]
                    ^  ^  ^  ^  ^
Indices:            0  1  2  3  4

Segment tree leaves (the gaps):
  [0,2] [2,5] [5,7] [7,10]
   idx0   idx1  idx2  idx3

Number of leaves = m - 1 = 4 (where m = 5 distinct values)
```

---

## 12. Pattern Recognition Decision Tree

Use this decision tree to identify if a problem requires sweep line and which variant to apply.

```
Is the problem geometric (2D) or temporal (intervals/time)?
│
├─ YES
│   │
│   └─ Does it involve N objects with spatial extent (intervals, segments, rectangles, points)?
│       │
│       ├─ YES
│       │   │
│       │   └─ What is asked?
│       │       │
│       │       ├─ Max/count of overlapping intervals at any point
│       │       │     → EVENT POINT SWEEP + running counter
│       │       │       Sort events, sweep, track max of running sum
│       │       │
│       │       ├─ Merge overlapping intervals into fewest
│       │       │     → SORT BY LEFT + GREEDY MERGE
│       │       │
│       │       ├─ Total length of union of intervals
│       │       │     → EVENT SWEEP + running coverage counter
│       │       │
│       │       ├─ Total AREA of union of rectangles
│       │       │     → SWEEP LINE + SEGMENT TREE with lazy propagation
│       │       │       + coordinate compression on y
│       │       │
│       │       ├─ Closest pair of points
│       │       │     → SWEEP LINE + BST active set (sorted by y)
│       │       │       sliding window by δ
│       │       │
│       │       ├─ Do any line segments intersect?
│       │       │     → SHAMOS-HOEY: sweep + BST status + adjacency checks
│       │       │
│       │       ├─ All intersection points
│       │       │     → BENTLEY-OTTMANN (advanced)
│       │       │
│       │       └─ Skyline / silhouette
│       │             → SWEEP + MAX-HEAP or sorted multimap for heights
│       │
│       └─ NO → Try other paradigms (DP, greedy, graph)
│
└─ NO → Not a sweep line problem
```

### Additional Heuristics

```
Problem has "at any point" or "at all times"  → sweep line + running state
Problem has "union" or "coverage"             → sweep line + counting structure
Problem has "intersect"                       → sweep line + ordered status
Problem has "closest"/"farthest"              → sweep line + sorted BST
Problem has large coords, small n             → coordinate compression needed
Problem asks for silhouette/outline           → sweep line + heap for max
```

---

## 13. Complexity Cheat Sheet

```
Problem                             Time           Space   Key Data Structure
─────────────────────────────────────────────────────────────────────────────
Max overlapping intervals           O(n log n)     O(n)    sorted events + counter
Merge intervals                     O(n log n)     O(n)    sort + linear scan
Total union length                  O(n log n)     O(n)    events + counter
Area of union of rectangles         O(n log n)     O(n)    events + lazy seg tree
Closest pair of points              O(n log n)     O(n)    BST active set
Line segment intersection (detect)  O(n log n)     O(n)    BST status
Line segment intersection (all)     O((n+k) log n) O(n+k)  BST + event queue
Skyline                             O(n log n)     O(n)    sorted multimap / heap
```

---

## 14. Mental Models & Cognitive Strategies

### Mental Model 1: The Physical Analogy

Before writing any code, close your eyes and **physically simulate** the sweep. Imagine walking the ruler across your problem. Ask:
- What happens when I hit this event?
- What do I need to remember as I walk?
- What is the simplest data structure that captures my memory?

This physical simulation almost always reveals the right data structure before any formal analysis.

### Mental Model 2: Events Are State Changes

The sweep line approach transforms a geometric problem into a **sequence of state transitions**. Your job is to:
1. Identify what constitutes a "state change."
2. Ensure those state changes are processed in the correct order.
3. Keep the state structure minimal and efficient.

### Mental Model 3: Reduce Dimensionality

Sweep line is a dimension-reduction technique:
```
2D problem → sorted sequence of 1D problems
3D problem → sorted sequence of 2D problems → each can be solved by another sweep
```

When you see a problem that seems inherently 2D, ask: "Can I fix one coordinate (sweep) and reduce it to a simpler 1D problem?"

### Mental Model 4: The Invariant Lens

At every event, your status structure maintains an invariant: it accurately represents the state of the world *at the current sweep position*. Define this invariant precisely before coding. Then coding becomes trivial: each event just maintains the invariant.

### Cognitive Strategy: Deliberate Practice Protocol

1. **Read** the problem. Identify the "objects" (intervals, rectangles, segments, points).
2. **Draw** the problem on paper. Draw 3-5 example objects.
3. **Walk** a sweep line by hand across your drawing. What changes at each event?
4. **Identify** the status structure: what do you need to remember?
5. **Identify** the answer contribution: how do you extract the answer at each event?
6. **Code** the five-step skeleton, then fill in specifics.
7. **Test** with edge cases: 1 object, all overlapping, all disjoint, collinear, duplicate coordinates.

### Cognitive Strategy: Chunking

Internalize these patterns as atomic chunks:

```
Chunk 1: "max overlap" = sort (open+1, close-1), sweep, track max running sum
Chunk 2: "union area"  = events + lazy seg tree + coord compression
Chunk 3: "skyline"     = events + multiset/max-heap of heights
Chunk 4: "closest pair"= sort by x + BST active set by y + sliding δ-window
```

Once these are chunked, recognizing them in new problems takes seconds, not minutes.

### Cognitive Strategy: The Tie-Breaking Contract

Tie-breaking (what to do when two events share the same x) is the most common source of bugs. Before coding, write out the tie-breaking contract:

```
At same x:
  OPEN before CLOSE  → touching endpoints count as overlapping
  CLOSE before OPEN  → touching endpoints do NOT overlap
  For skyline: starts before ends, higher heights first among starts
```

Sign this contract in a comment at the top of your sort comparator. Never let it be implicit.

### Psychological Principle: Flow Through Reduction

Sweep line exemplifies the **reductionist problem-solving mode** — the state of deep flow where you reduce complexity rather than fighting it. Every complex 2D problem becomes a sequence of simple 1D updates. This is the monk's way: simplify until the path is clear, then walk it without hesitation.

The discipline to always ask "can I reduce this dimension?" before attempting a direct solution separates average programmers from top 1% engineers.

---

## Summary: The Sweep Line in One Paragraph

The sweep line algorithm marches a virtual line across the plane, processing events in sorted order and maintaining an active set that accurately reflects the current state of the world at the sweep position. By reducing a 2D problem to a sequence of 1D queries and updates, it achieves O(n log n) time where brute force would require O(n²) or worse. The key choices — which axis to sweep, what constitutes an event, what data structure maintains the status, and how to break ties at coincident events — fully determine the solution. Master these choices, and every geometric problem becomes a familiar walk.

---

*End of Guide — Sweep Line: From Zero to Expert*

Now let me create the comprehensive Sweep Line guide:Here is your complete Sweep Line mastery guide. Here is what is covered inside:

**Structure of the guide (14 sections):**

1. **Mental Model** — the physical analogy of walking a vertical ruler across a 2D plane, with the dimensionality reduction diagram
2. **Core Vocabulary** — every term defined from scratch: event point, status structure, active set, predecessor/successor, coordinate compression, open/close events, coincident events
3. **Anatomy of Every Solution** — the universal 5-step skeleton with ASCII flowchart that applies to *any* sweep line problem
4. **Data Structures** — when to use sorted multiset, segment tree with lazy propagation, BIT, or priority queue — with a decision table
5. **Interval Overlap & Counting** — the foundational pattern; C, Go, Rust; tie-breaking contract explained
6. **Meeting Rooms** — attend-all check, minimum rooms, merge intervals in Rust and Go
7. **Area of Union of Rectangles** — the hardest classic; segment tree with lazy propagation + coordinate compression in C, Go, Rust
8. **Closest Pair of Points** — the sliding δ-window BST approach in Rust
9. **Line Segment Intersection** — cross product, orientation test, Shamos-Hoey in C
10. **Skyline Problem** — BTreeMap-as-multiset in Rust, sorted slice in Go
11. **Coordinate Compression** — the gap vs. point distinction that causes most bugs
12. **Pattern Recognition Decision Tree** — ASCII flowchart to classify any problem in seconds
13. **Complexity Cheat Sheet** — all problems, time/space, and key data structure in one table
14. **Mental Models & Cognitive Strategies** — the 5 thinking tools including the *tie-breaking contract*, deliberate practice protocol, and chunking patterns