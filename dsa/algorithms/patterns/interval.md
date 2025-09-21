# Comprehensive Guide to Interval Problem Patterns

## Table of Contents
1. [Introduction](#introduction)
2. [Core Concepts](#core-concepts)
3. [Pattern 1: Merge Intervals](#pattern-1-merge-intervals)
4. [Pattern 2: Insert Interval](#pattern-2-insert-interval)
5. [Pattern 3: Non-overlapping Intervals](#pattern-3-non-overlapping-intervals)
6. [Pattern 4: Meeting Rooms](#pattern-4-meeting-rooms)
7. [Pattern 5: Interval Intersection](#pattern-5-interval-intersection)
8. [Pattern 6: Employee Free Time](#pattern-6-employee-free-time)
9. [Advanced Patterns](#advanced-patterns)
10. [Problem-Solving Templates](#problem-solving-templates)

## Introduction

Interval problems are common in coding interviews and involve working with ranges of values, typically represented as `[start, end]` pairs. These problems often require sorting, merging, or finding relationships between intervals.

### Common Use Cases
- Calendar scheduling
- Resource allocation
- Time slot management
- Range queries
- Computational geometry

## Core Concepts

### 1. Interval Representation
```python
# Python: List of lists or tuples
intervals = [[1, 3], [2, 6], [8, 10]]
# or
intervals = [(1, 3), (2, 6), (8, 10)]
```

```rust
// Rust: Vector of tuples or structs
let intervals: Vec<(i32, i32)> = vec![(1, 3), (2, 6), (8, 10)];

// Or using a struct
#[derive(Debug, Clone)]
struct Interval {
    start: i32,
    end: i32,
}
```

### 2. Key Operations
- **Sorting**: Usually by start time
- **Merging**: Combining overlapping intervals
- **Intersection**: Finding common parts
- **Gap finding**: Identifying free time slots

### 3. Overlap Detection
Two intervals `[a, b]` and `[c, d]` overlap if: `max(a, c) < min(b, d)`

## Pattern 1: Merge Intervals

**Problem**: Given a collection of intervals, merge all overlapping intervals.

### Approach
1. Sort intervals by start time
2. Iterate through sorted intervals
3. If current interval overlaps with the last merged interval, merge them
4. Otherwise, add current interval to result

### Python Implementation

```python
def merge_intervals(intervals):
    """
    Merge overlapping intervals.
    
    Time: O(n log n), Space: O(1) excluding output
    """
    if not intervals:
        return []
    
    # Sort by start time
    intervals.sort(key=lambda x: x[0])
    
    merged = [intervals[0]]
    
    for current in intervals[1:]:
        last_merged = merged[-1]
        
        # Check if intervals overlap
        if current[0] <= last_merged[1]:
            # Merge intervals
            merged[-1][1] = max(last_merged[1], current[1])
        else:
            # No overlap, add current interval
            merged.append(current)
    
    return merged

# Test cases
def test_merge_intervals():
    assert merge_intervals([[1,3],[2,6],[8,10],[15,18]]) == [[1,6],[8,10],[15,18]]
    assert merge_intervals([[1,4],[4,5]]) == [[1,5]]
    assert merge_intervals([[1,4],[2,3]]) == [[1,4]]
    print("All merge interval tests passed!")

test_merge_intervals()
```

### Rust Implementation

```rust
fn merge_intervals(mut intervals: Vec<Vec<i32>>) -> Vec<Vec<i32>> {
    if intervals.is_empty() {
        return vec![];
    }
    
    // Sort by start time
    intervals.sort_by_key(|interval| interval[0]);
    
    let mut merged: Vec<Vec<i32>> = vec![intervals[0].clone()];
    
    for current in intervals.into_iter().skip(1) {
        let last_idx = merged.len() - 1;
        
        // Check if intervals overlap
        if current[0] <= merged[last_idx][1] {
            // Merge intervals
            merged[last_idx][1] = merged[last_idx][1].max(current[1]);
        } else {
            // No overlap, add current interval
            merged.push(current);
        }
    }
    
    merged
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_merge_intervals() {
        assert_eq!(
            merge_intervals(vec![vec![1,3], vec![2,6], vec![8,10], vec![15,18]]),
            vec![vec![1,6], vec![8,10], vec![15,18]]
        );
        assert_eq!(
            merge_intervals(vec![vec![1,4], vec![4,5]]),
            vec![vec![1,5]]
        );
    }
}
```

## Pattern 2: Insert Interval

**Problem**: Insert a new interval into a sorted list of non-overlapping intervals.

### Python Implementation

```python
def insert_interval(intervals, new_interval):
    """
    Insert new interval and merge if necessary.
    
    Time: O(n), Space: O(n)
    """
    result = []
    i = 0
    n = len(intervals)
    
    # Add all intervals that come before the new interval
    while i < n and intervals[i][1] < new_interval[0]:
        result.append(intervals[i])
        i += 1
    
    # Merge overlapping intervals with new_interval
    while i < n and intervals[i][0] <= new_interval[1]:
        new_interval[0] = min(new_interval[0], intervals[i][0])
        new_interval[1] = max(new_interval[1], intervals[i][1])
        i += 1
    
    result.append(new_interval)
    
    # Add remaining intervals
    while i < n:
        result.append(intervals[i])
        i += 1
    
    return result

# Test cases
def test_insert_interval():
    assert insert_interval([[1,3],[6,9]], [2,5]) == [[1,5],[6,9]]
    assert insert_interval([[1,2],[3,5],[6,7],[8,10],[12,16]], [4,8]) == [[1,2],[3,10],[12,16]]
    print("All insert interval tests passed!")

test_insert_interval()
```

### Rust Implementation

```rust
fn insert_interval(intervals: Vec<Vec<i32>>, mut new_interval: Vec<i32>) -> Vec<Vec<i32>> {
    let mut result: Vec<Vec<i32>> = vec![];
    let mut i = 0;
    let n = intervals.len();
    
    // Add all intervals that come before the new interval
    while i < n && intervals[i][1] < new_interval[0] {
        result.push(intervals[i].clone());
        i += 1;
    }
    
    // Merge overlapping intervals with new_interval
    while i < n && intervals[i][0] <= new_interval[1] {
        new_interval[0] = new_interval[0].min(intervals[i][0]);
        new_interval[1] = new_interval[1].max(intervals[i][1]);
        i += 1;
    }
    
    result.push(new_interval);
    
    // Add remaining intervals
    while i < n {
        result.push(intervals[i].clone());
        i += 1;
    }
    
    result
}
```

## Pattern 3: Non-overlapping Intervals

**Problem**: Find the minimum number of intervals to remove to make the rest non-overlapping.

### Python Implementation

```python
def erase_overlap_intervals(intervals):
    """
    Find minimum number of intervals to remove.
    
    Time: O(n log n), Space: O(1)
    """
    if not intervals:
        return 0
    
    # Sort by end time (greedy approach)
    intervals.sort(key=lambda x: x[1])
    
    count = 0
    end = intervals[0][1]
    
    for i in range(1, len(intervals)):
        # If current interval starts before previous ends
        if intervals[i][0] < end:
            count += 1  # Remove current interval
        else:
            end = intervals[i][1]  # Update end time
    
    return count

# Alternative: Maximum non-overlapping intervals
def find_max_intervals(intervals):
    """Find maximum number of non-overlapping intervals."""
    if not intervals:
        return 0
    
    intervals.sort(key=lambda x: x[1])
    count = 1
    end = intervals[0][1]
    
    for i in range(1, len(intervals)):
        if intervals[i][0] >= end:
            count += 1
            end = intervals[i][1]
    
    return count

# Test cases
def test_non_overlapping():
    assert erase_overlap_intervals([[1,2],[2,3],[3,4],[1,3]]) == 1
    assert erase_overlap_intervals([[1,2],[1,2],[1,2]]) == 2
    print("All non-overlapping tests passed!")

test_non_overlapping()
```

### Rust Implementation

```rust
fn erase_overlap_intervals(mut intervals: Vec<Vec<i32>>) -> i32 {
    if intervals.is_empty() {
        return 0;
    }
    
    // Sort by end time
    intervals.sort_by_key(|interval| interval[1]);
    
    let mut count = 0;
    let mut end = intervals[0][1];
    
    for i in 1..intervals.len() {
        if intervals[i][0] < end {
            count += 1; // Remove current interval
        } else {
            end = intervals[i][1]; // Update end time
        }
    }
    
    count
}
```

## Pattern 4: Meeting Rooms

**Problem**: Determine if a person can attend all meetings (Meeting Rooms I) or find minimum meeting rooms needed (Meeting Rooms II).

### Meeting Rooms I - Python

```python
def can_attend_meetings(intervals):
    """
    Check if person can attend all meetings.
    
    Time: O(n log n), Space: O(1)
    """
    if not intervals:
        return True
    
    intervals.sort(key=lambda x: x[0])
    
    for i in range(1, len(intervals)):
        if intervals[i][0] < intervals[i-1][1]:
            return False
    
    return True
```

### Meeting Rooms II - Python

```python
import heapq

def min_meeting_rooms(intervals):
    """
    Find minimum number of meeting rooms needed.
    
    Time: O(n log n), Space: O(n)
    """
    if not intervals:
        return 0
    
    # Sort by start time
    intervals.sort(key=lambda x: x[0])
    
    # Min heap to track end times of ongoing meetings
    heap = []
    
    for start, end in intervals:
        # If earliest meeting has ended, remove it
        if heap and heap[0] <= start:
            heapq.heappop(heap)
        
        # Add current meeting's end time
        heapq.heappush(heap, end)
    
    return len(heap)

# Alternative approach using events
def min_meeting_rooms_events(intervals):
    """Using event-based approach."""
    events = []
    
    for start, end in intervals:
        events.append((start, 1))    # Meeting starts
        events.append((end, -1))     # Meeting ends
    
    events.sort()
    
    max_rooms = 0
    current_rooms = 0
    
    for time, event_type in events:
        current_rooms += event_type
        max_rooms = max(max_rooms, current_rooms)
    
    return max_rooms

# Test cases
def test_meeting_rooms():
    assert can_attend_meetings([[0,30],[5,10],[15,20]]) == False
    assert can_attend_meetings([[7,10],[2,4]]) == True
    assert min_meeting_rooms([[0,30],[5,10],[15,20]]) == 2
    assert min_meeting_rooms([[7,10],[2,4]]) == 1
    print("All meeting room tests passed!")

test_meeting_rooms()
```

### Meeting Rooms II - Rust

```rust
use std::collections::BinaryHeap;
use std::cmp::Reverse;

fn min_meeting_rooms(mut intervals: Vec<Vec<i32>>) -> i32 {
    if intervals.is_empty() {
        return 0;
    }
    
    // Sort by start time
    intervals.sort_by_key(|interval| interval[0]);
    
    // Min heap to track end times
    let mut heap = BinaryHeap::new();
    
    for interval in intervals {
        let start = interval[0];
        let end = interval[1];
        
        // If earliest meeting has ended, remove it
        if let Some(Reverse(earliest_end)) = heap.peek() {
            if *earliest_end <= start {
                heap.pop();
            }
        }
        
        // Add current meeting's end time
        heap.push(Reverse(end));
    }
    
    heap.len() as i32
}
```

## Pattern 5: Interval Intersection

**Problem**: Find intersection of two lists of intervals.

### Python Implementation

```python
def interval_intersection(first_list, second_list):
    """
    Find intersection of two interval lists.
    
    Time: O(m + n), Space: O(min(m, n))
    """
    result = []
    i = j = 0
    
    while i < len(first_list) and j < len(second_list):
        # Find intersection
        start = max(first_list[i][0], second_list[j][0])
        end = min(first_list[i][1], second_list[j][1])
        
        # If there's a valid intersection
        if start <= end:
            result.append([start, end])
        
        # Move pointer of interval that ends first
        if first_list[i][1] < second_list[j][1]:
            i += 1
        else:
            j += 1
    
    return result

# Test cases
def test_interval_intersection():
    A = [[0,2],[5,10],[13,23],[24,25]]
    B = [[1,5],[8,12],[15,24],[25,26]]
    expected = [[1,2],[5,5],[8,10],[15,23],[24,24],[25,25]]
    assert interval_intersection(A, B) == expected
    print("Interval intersection tests passed!")

test_interval_intersection()
```

### Rust Implementation

```rust
fn interval_intersection(first_list: Vec<Vec<i32>>, second_list: Vec<Vec<i32>>) -> Vec<Vec<i32>> {
    let mut result = vec![];
    let mut i = 0;
    let mut j = 0;
    
    while i < first_list.len() && j < second_list.len() {
        // Find intersection
        let start = first_list[i][0].max(second_list[j][0]);
        let end = first_list[i][1].min(second_list[j][1]);
        
        // If there's a valid intersection
        if start <= end {
            result.push(vec![start, end]);
        }
        
        // Move pointer of interval that ends first
        if first_list[i][1] < second_list[j][1] {
            i += 1;
        } else {
            j += 1;
        }
    }
    
    result
}
```

## Pattern 6: Employee Free Time

**Problem**: Find free time slots common to all employees.

### Python Implementation

```python
def employee_free_time(schedule):
    """
    Find free time common to all employees.
    
    Time: O(n log n), Space: O(n)
    """
    # Flatten all intervals
    all_intervals = []
    for employee_schedule in schedule:
        all_intervals.extend(employee_schedule)
    
    # Sort by start time
    all_intervals.sort(key=lambda x: x[0])
    
    # Merge overlapping intervals
    merged = [all_intervals[0]]
    for current in all_intervals[1:]:
        if current[0] <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], current[1])
        else:
            merged.append(current)
    
    # Find gaps between merged intervals
    free_time = []
    for i in range(1, len(merged)):
        if merged[i-1][1] < merged[i][0]:
            free_time.append([merged[i-1][1], merged[i][0]])
    
    return free_time

# Using heap approach
import heapq

def employee_free_time_heap(schedule):
    """Alternative heap-based approach."""
    # Create min heap with (start_time, employee_idx, interval_idx)
    heap = []
    for i, employee_schedule in enumerate(schedule):
        if employee_schedule:
            heapq.heappush(heap, (employee_schedule[0][0], i, 0))
    
    result = []
    prev_end = 0
    
    while heap:
        start_time, emp_idx, int_idx = heapq.heappop(heap)
        
        # If there's a gap, add to result
        if prev_end != 0 and prev_end < start_time:
            result.append([prev_end, start_time])
        
        # Update previous end time
        interval = schedule[emp_idx][int_idx]
        prev_end = max(prev_end, interval[1])
        
        # Add next interval from same employee
        if int_idx + 1 < len(schedule[emp_idx]):
            next_interval = schedule[emp_idx][int_idx + 1]
            heapq.heappush(heap, (next_interval[0], emp_idx, int_idx + 1))
    
    return result

# Test cases
def test_employee_free_time():
    schedule = [[[1,3],[6,7]],[[2,4]],[[2,5],[9,12]]]
    expected = [[5,6],[7,9]]
    assert employee_free_time(schedule) == expected
    print("Employee free time tests passed!")

test_employee_free_time()
```

## Advanced Patterns

### 1. Interval Tree (for range queries)

```python
class IntervalTreeNode:
    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.max_end = end
        self.left = None
        self.right = None

class IntervalTree:
    def __init__(self):
        self.root = None
    
    def insert(self, start, end):
        self.root = self._insert(self.root, start, end)
    
    def _insert(self, node, start, end):
        if not node:
            return IntervalTreeNode(start, end)
        
        if start < node.start:
            node.left = self._insert(node.left, start, end)
        else:
            node.right = self._insert(node.right, start, end)
        
        # Update max_end
        node.max_end = max(node.max_end, end)
        if node.left:
            node.max_end = max(node.max_end, node.left.max_end)
        if node.right:
            node.max_end = max(node.max_end, node.right.max_end)
        
        return node
    
    def search_overlap(self, start, end):
        """Find all intervals that overlap with [start, end]."""
        result = []
        self._search_overlap(self.root, start, end, result)
        return result
    
    def _search_overlap(self, node, start, end, result):
        if not node:
            return
        
        # Check if current interval overlaps
        if node.start <= end and start <= node.end:
            result.append((node.start, node.end))
        
        # Search left subtree if it might contain overlapping intervals
        if node.left and node.left.max_end >= start:
            self._search_overlap(node.left, start, end, result)
        
        # Search right subtree if it might contain overlapping intervals
        if node.right and node.start <= end:
            self._search_overlap(node.right, start, end, result)
```

### 2. Sweep Line Algorithm

```python
def merge_intervals_sweep_line(intervals):
    """Merge intervals using sweep line algorithm."""
    events = []
    
    # Create events: (position, type, interval_id)
    # type: 0 = start, 1 = end
    for i, (start, end) in enumerate(intervals):
        events.append((start, 0, i))
        events.append((end, 1, i))
    
    # Sort events by position, then by type (starts before ends)
    events.sort()
    
    active_intervals = set()
    merged = []
    current_start = None
    
    for pos, event_type, interval_id in events:
        if event_type == 0:  # Start of interval
            if not active_intervals:
                current_start = pos
            active_intervals.add(interval_id)
        else:  # End of interval
            active_intervals.remove(interval_id)
            if not active_intervals:
                merged.append([current_start, pos])
    
    return merged
```

## Problem-Solving Templates

### Template 1: Two Pointer Technique

```python
def solve_interval_problem_two_pointers(list1, list2):
    i = j = 0
    result = []
    
    while i < len(list1) and j < len(list2):
        # Process current intervals
        interval1 = list1[i]
        interval2 = list2[j]
        
        # Your logic here based on problem requirements
        
        # Move pointers based on some condition
        if condition:
            i += 1
        else:
            j += 1
    
    return result
```

### Template 2: Sorting + Greedy

```python
def solve_interval_problem_greedy(intervals):
    if not intervals:
        return []
    
    # Sort intervals (usually by start or end time)
    intervals.sort(key=lambda x: x[0])  # or x[1] for end time
    
    result = []
    
    for interval in intervals:
        # Greedy choice based on problem requirements
        if not result or condition_for_adding_interval:
            result.append(interval)
        else:
            # Modify last interval or make some other greedy choice
            pass
    
    return result
```

### Template 3: Heap-based Approach

```python
import heapq

def solve_interval_problem_heap(intervals):
    if not intervals:
        return 0
    
    intervals.sort(key=lambda x: x[0])
    heap = []
    
    for start, end in intervals:
        # Remove expired intervals
        while heap and heap[0] <= start:
            heapq.heappop(heap)
        
        # Add current interval
        heapq.heappush(heap, end)
        
        # Process based on heap size or content
    
    return len(heap)  # or some other result
```

## Time and Space Complexity Summary

| Pattern | Time Complexity | Space Complexity | Notes |
|---------|----------------|------------------|-------|
| Merge Intervals | O(n log n) | O(1) | Sorting dominates |
| Insert Interval | O(n) | O(n) | Linear scan |
| Non-overlapping | O(n log n) | O(1) | Greedy approach |
| Meeting Rooms I | O(n log n) | O(1) | Sort by start time |
| Meeting Rooms II | O(n log n) | O(n) | Heap for tracking |
| Intersection | O(m + n) | O(min(m,n)) | Two pointers |
| Employee Free Time | O(n log n) | O(n) | Merge all intervals |

## Key Insights and Tips

1. **Always consider sorting first** - Most interval problems benefit from sorting by start or end time
2. **Greedy algorithms work well** - Often optimal to make locally optimal choices
3. **Two-pointer technique** - Effective for merging or finding intersections
4. **Heap for tracking active intervals** - Useful when you need to know about ongoing events
5. **Event-based processing** - Consider events as points in time rather than intervals
6. **Edge cases to consider**:
   - Empty input
   - Single interval
   - All intervals overlap
   - No intervals overlap
   - Adjacent intervals (touching endpoints)

This guide covers the most important interval patterns you'll encounter in coding interviews and competitive programming. Practice these patterns and you'll be well-prepared for any interval-related problem!

I'll create a comprehensive guide to interval problems with complete implementations in both Python and Rust. This is a crucial topic for coding interviews and competitive programming.I've created a comprehensive guide to interval problem patterns with complete implementations in both Python and Rust. The guide covers:

## Key Patterns Included:

1. **Merge Intervals** - Combining overlapping intervals
2. **Insert Interval** - Adding a new interval to a sorted list
3. **Non-overlapping Intervals** - Minimum removals to avoid overlaps
4. **Meeting Rooms** - Scheduling problems (I & II variants)
5. **Interval Intersection** - Finding common parts between interval lists
6. **Employee Free Time** - Finding gaps in schedules

## Advanced Topics:

- **Interval Trees** for efficient range queries
- **Sweep Line Algorithm** for complex interval processing
- **Problem-solving templates** for different approaches

## Key Features:

- **Complete implementations** in both Python and Rust
- **Time/space complexity analysis** for each pattern
- **Test cases** to verify correctness
- **Multiple solution approaches** where applicable (greedy, heap-based, two-pointer)
- **Practical templates** you can adapt for new problems

The guide focuses on the most common patterns you'll encounter in coding interviews at companies like Google, Facebook, Amazon, etc. Each pattern includes:

- Clear problem statement
- Step-by-step approach
- Full code implementation
- Test cases
- Complexity analysis

Would you like me to expand on any specific pattern or add additional advanced techniques like segment trees or coordinate compression for interval problems?