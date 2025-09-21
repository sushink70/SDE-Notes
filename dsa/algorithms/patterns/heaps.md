# Comprehensive Guide to Heap Problem Patterns

## Table of Contents
1. [Heap Fundamentals](#heap-fundamentals)
2. [Top-K Elements Pattern](#top-k-elements-pattern)
3. [K-Way Merge Pattern](#k-way-merge-pattern)
4. [Two Heaps Pattern](#two-heaps-pattern)
5. [Sliding Window Maximum/Minimum](#sliding-window-maximumminimum)
6. [Running Median Pattern](#running-median-pattern)
7. [Priority Queue Scheduling](#priority-queue-scheduling)
8. [Heap-based Graph Algorithms](#heap-based-graph-algorithms)

## Heap Fundamentals

### Basic Heap Operations

**Python Implementation:**
```python
import heapq
from typing import List, Optional, Tuple

class MaxHeap:
    def __init__(self):
        self.heap = []
    
    def push(self, val):
        heapq.heappush(self.heap, -val)
    
    def pop(self):
        return -heapq.heappop(self.heap)
    
    def peek(self):
        return -self.heap[0] if self.heap else None
    
    def size(self):
        return len(self.heap)

class MinHeap:
    def __init__(self):
        self.heap = []
    
    def push(self, val):
        heapq.heappush(self.heap, val)
    
    def pop(self):
        return heapq.heappop(self.heap)
    
    def peek(self):
        return self.heap[0] if self.heap else None
    
    def size(self):
        return len(self.heap)
```

**Rust Implementation:**
```rust
use std::collections::BinaryHeap;
use std::cmp::Reverse;

struct MaxHeap<T> {
    heap: BinaryHeap<T>,
}

impl<T: Ord> MaxHeap<T> {
    fn new() -> Self {
        MaxHeap {
            heap: BinaryHeap::new(),
        }
    }
    
    fn push(&mut self, val: T) {
        self.heap.push(val);
    }
    
    fn pop(&mut self) -> Option<T> {
        self.heap.pop()
    }
    
    fn peek(&self) -> Option<&T> {
        self.heap.peek()
    }
    
    fn len(&self) -> usize {
        self.heap.len()
    }
}

struct MinHeap<T> {
    heap: BinaryHeap<Reverse<T>>,
}

impl<T: Ord> MinHeap<T> {
    fn new() -> Self {
        MinHeap {
            heap: BinaryHeap::new(),
        }
    }
    
    fn push(&mut self, val: T) {
        self.heap.push(Reverse(val));
    }
    
    fn pop(&mut self) -> Option<T> {
        self.heap.pop().map(|Reverse(val)| val)
    }
    
    fn peek(&self) -> Option<&T> {
        self.heap.peek().map(|Reverse(val)| val)
    }
    
    fn len(&self) -> usize {
        self.heap.len()
    }
}
```

## Top-K Elements Pattern

This pattern is used when you need to find the top K largest/smallest elements in a dataset.

### Problem: Find K Largest Elements

**Python Implementation:**
```python
def find_k_largest_elements(nums: List[int], k: int) -> List[int]:
    """
    Find k largest elements using min heap of size k
    Time: O(n log k), Space: O(k)
    """
    min_heap = []
    
    for num in nums:
        heapq.heappush(min_heap, num)
        if len(min_heap) > k:
            heapq.heappop(min_heap)
    
    return sorted(min_heap, reverse=True)

def top_k_frequent(nums: List[int], k: int) -> List[int]:
    """
    Find k most frequent elements
    Time: O(n log k), Space: O(n)
    """
    from collections import Counter
    
    count = Counter(nums)
    # Use min heap with frequency as key
    min_heap = []
    
    for num, freq in count.items():
        heapq.heappush(min_heap, (freq, num))
        if len(min_heap) > k:
            heapq.heappop(min_heap)
    
    return [num for freq, num in min_heap]

def kth_largest_element(nums: List[int], k: int) -> int:
    """
    Find kth largest element using min heap
    Time: O(n log k), Space: O(k)
    """
    min_heap = []
    
    for num in nums:
        heapq.heappush(min_heap, num)
        if len(min_heap) > k:
            heapq.heappop(min_heap)
    
    return min_heap[0]
```

**Rust Implementation:**
```rust
use std::collections::HashMap;

fn find_k_largest_elements(nums: Vec<i32>, k: usize) -> Vec<i32> {
    let mut min_heap = MinHeap::new();
    
    for num in nums {
        min_heap.push(num);
        if min_heap.len() > k {
            min_heap.pop();
        }
    }
    
    let mut result = Vec::new();
    while let Some(val) = min_heap.pop() {
        result.push(val);
    }
    result.reverse();
    result
}

fn top_k_frequent(nums: Vec<i32>, k: usize) -> Vec<i32> {
    let mut count = HashMap::new();
    for num in nums {
        *count.entry(num).or_insert(0) += 1;
    }
    
    let mut min_heap = MinHeap::new();
    
    for (num, freq) in count {
        min_heap.push((freq, num));
        if min_heap.len() > k {
            min_heap.pop();
        }
    }
    
    let mut result = Vec::new();
    while let Some((_, num)) = min_heap.pop() {
        result.push(num);
    }
    result
}

fn kth_largest_element(nums: Vec<i32>, k: usize) -> i32 {
    let mut min_heap = MinHeap::new();
    
    for num in nums {
        min_heap.push(num);
        if min_heap.len() > k {
            min_heap.pop();
        }
    }
    
    min_heap.peek().copied().unwrap_or(0)
}
```

## K-Way Merge Pattern

Used when you need to merge K sorted arrays or lists.

### Problem: Merge K Sorted Lists

**Python Implementation:**
```python
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
    
    def __lt__(self, other):
        return self.val < other.val

def merge_k_sorted_lists(lists: List[Optional[ListNode]]) -> Optional[ListNode]:
    """
    Merge k sorted linked lists using min heap
    Time: O(n log k), Space: O(k)
    """
    min_heap = []
    
    # Add first node of each list to heap
    for i, head in enumerate(lists):
        if head:
            heapq.heappush(min_heap, (head.val, i, head))
    
    dummy = ListNode()
    current = dummy
    
    while min_heap:
        val, i, node = heapq.heappop(min_heap)
        current.next = node
        current = current.next
        
        if node.next:
            heapq.heappush(min_heap, (node.next.val, i, node.next))
    
    return dummy.next

def merge_k_sorted_arrays(arrays: List[List[int]]) -> List[int]:
    """
    Merge k sorted arrays
    Time: O(n log k), Space: O(k)
    """
    min_heap = []
    
    # Add first element of each array with array index and element index
    for i, arr in enumerate(arrays):
        if arr:
            heapq.heappush(min_heap, (arr[0], i, 0))
    
    result = []
    
    while min_heap:
        val, arr_idx, elem_idx = heapq.heappop(min_heap)
        result.append(val)
        
        # Add next element from the same array
        if elem_idx + 1 < len(arrays[arr_idx]):
            next_val = arrays[arr_idx][elem_idx + 1]
            heapq.heappush(min_heap, (next_val, arr_idx, elem_idx + 1))
    
    return result

def smallest_range_covering_elements(nums: List[List[int]]) -> List[int]:
    """
    Find smallest range that includes at least one number from each list
    Time: O(n log k), Space: O(k)
    """
    min_heap = []
    max_val = float('-inf')
    
    # Initialize heap with first element from each list
    for i, arr in enumerate(nums):
        if arr:
            heapq.heappush(min_heap, (arr[0], i, 0))
            max_val = max(max_val, arr[0])
    
    range_start, range_end = 0, float('inf')
    
    while len(min_heap) == len(nums):
        min_val, arr_idx, elem_idx = heapq.heappop(min_heap)
        
        # Update range if current is smaller
        if max_val - min_val < range_end - range_start:
            range_start, range_end = min_val, max_val
        
        # Add next element from the same array
        if elem_idx + 1 < len(nums[arr_idx]):
            next_val = nums[arr_idx][elem_idx + 1]
            heapq.heappush(min_heap, (next_val, arr_idx, elem_idx + 1))
            max_val = max(max_val, next_val)
    
    return [range_start, range_end]
```

**Rust Implementation:**
```rust
use std::cmp::Ordering;

#[derive(Debug, PartialEq, Eq)]
struct ListNode {
    val: i32,
    next: Option<Box<ListNode>>,
}

impl PartialOrd for ListNode {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for ListNode {
    fn cmp(&self, other: &Self) -> Ordering {
        other.val.cmp(&self.val) // Reverse for min heap
    }
}

fn merge_k_sorted_lists(lists: Vec<Option<Box<ListNode>>>) -> Option<Box<ListNode>> {
    let mut min_heap = BinaryHeap::new();
    
    // Add first node of each list to heap
    for head in lists {
        if let Some(node) = head {
            min_heap.push(node);
        }
    }
    
    let mut dummy = Box::new(ListNode { val: 0, next: None });
    let mut current = &mut dummy;
    
    while let Some(mut node) = min_heap.pop() {
        if let Some(next) = node.next.take() {
            min_heap.push(next);
        }
        current.next = Some(node);
        current = current.next.as_mut().unwrap();
    }
    
    dummy.next
}

fn merge_k_sorted_arrays(arrays: Vec<Vec<i32>>) -> Vec<i32> {
    let mut min_heap = BinaryHeap::new();
    
    // Add first element of each array
    for (i, arr) in arrays.iter().enumerate() {
        if !arr.is_empty() {
            min_heap.push(Reverse((arr[0], i, 0)));
        }
    }
    
    let mut result = Vec::new();
    
    while let Some(Reverse((val, arr_idx, elem_idx))) = min_heap.pop() {
        result.push(val);
        
        // Add next element from the same array
        if elem_idx + 1 < arrays[arr_idx].len() {
            let next_val = arrays[arr_idx][elem_idx + 1];
            min_heap.push(Reverse((next_val, arr_idx, elem_idx + 1)));
        }
    }
    
    result
}

fn smallest_range_covering_elements(nums: Vec<Vec<i32>>) -> Vec<i32> {
    let mut min_heap = BinaryHeap::new();
    let mut max_val = i32::MIN;
    
    // Initialize heap with first element from each list
    for (i, arr) in nums.iter().enumerate() {
        if !arr.is_empty() {
            min_heap.push(Reverse((arr[0], i, 0)));
            max_val = max_val.max(arr[0]);
        }
    }
    
    let mut range_start = 0;
    let mut range_end = i32::MAX;
    
    while min_heap.len() == nums.len() {
        let Reverse((min_val, arr_idx, elem_idx)) = min_heap.pop().unwrap();
        
        // Update range if current is smaller
        if max_val - min_val < range_end - range_start {
            range_start = min_val;
            range_end = max_val;
        }
        
        // Add next element from the same array
        if elem_idx + 1 < nums[arr_idx].len() {
            let next_val = nums[arr_idx][elem_idx + 1];
            min_heap.push(Reverse((next_val, arr_idx, elem_idx + 1)));
            max_val = max_val.max(next_val);
        }
    }
    
    vec![range_start, range_end]
}
```

## Two Heaps Pattern

This pattern uses two heaps to solve problems involving medians or balanced partitioning.

### Problem: Find Median from Data Stream

**Python Implementation:**
```python
class MedianFinder:
    """
    Find median from data stream using two heaps
    """
    def __init__(self):
        self.small = []  # max heap for smaller half
        self.large = []  # min heap for larger half
    
    def addNum(self, num: int) -> None:
        """Add number to data stream - O(log n)"""
        # Add to appropriate heap
        if not self.large or num > self.large[0]:
            heapq.heappush(self.large, num)
        else:
            heapq.heappush(self.small, -num)
        
        # Balance heaps
        if len(self.small) > len(self.large) + 1:
            val = -heapq.heappop(self.small)
            heapq.heappush(self.large, val)
        elif len(self.large) > len(self.small) + 1:
            val = heapq.heappop(self.large)
            heapq.heappush(self.small, -val)
    
    def findMedian(self) -> float:
        """Find median - O(1)"""
        if len(self.small) == len(self.large):
            return (-self.small[0] + self.large[0]) / 2.0
        elif len(self.small) > len(self.large):
            return float(-self.small[0])
        else:
            return float(self.large[0])

class SlidingWindowMedian:
    """Find median in sliding window"""
    def __init__(self):
        self.small = []  # max heap
        self.large = []  # min heap
    
    def medianSlidingWindow(self, nums: List[int], k: int) -> List[float]:
        result = []
        
        for i in range(len(nums)):
            # Add current number
            self.add_num(nums[i])
            
            # Remove number that's out of window
            if i >= k:
                self.remove_num(nums[i - k])
            
            # Calculate median if window is full
            if i >= k - 1:
                result.append(self.find_median())
        
        return result
    
    def add_num(self, num):
        if not self.large or num > self.large[0]:
            heapq.heappush(self.large, num)
        else:
            heapq.heappush(self.small, -num)
        self.balance_heaps()
    
    def remove_num(self, num):
        if self.small and num <= -self.small[0]:
            self.small.remove(-num)
            heapq.heapify(self.small)
        else:
            self.large.remove(num)
            heapq.heapify(self.large)
        self.balance_heaps()
    
    def balance_heaps(self):
        if len(self.small) > len(self.large) + 1:
            val = -heapq.heappop(self.small)
            heapq.heappush(self.large, val)
        elif len(self.large) > len(self.small) + 1:
            val = heapq.heappop(self.large)
            heapq.heappush(self.small, -val)
    
    def find_median(self):
        if len(self.small) == len(self.large):
            return (-self.small[0] + self.large[0]) / 2.0
        elif len(self.small) > len(self.large):
            return float(-self.small[0])
        else:
            return float(self.large[0])

def ipo_maximize_capital(k: int, w: int, profits: List[int], capital: List[int]) -> int:
    """
    Maximize capital after at most k projects
    Time: O(n log n), Space: O(n)
    """
    # Min heap for projects by capital requirement
    min_capital_heap = [(c, p) for c, p in zip(capital, profits)]
    heapq.heapify(min_capital_heap)
    
    # Max heap for available projects by profit
    max_profit_heap = []
    
    current_capital = w
    
    for _ in range(k):
        # Move all affordable projects to profit heap
        while min_capital_heap and min_capital_heap[0][0] <= current_capital:
            cap, profit = heapq.heappop(min_capital_heap)
            heapq.heappush(max_profit_heap, -profit)
        
        # Pick most profitable project
        if not max_profit_heap:
            break
        
        current_capital += -heapq.heappop(max_profit_heap)
    
    return current_capital
```

**Rust Implementation:**
```rust
use std::collections::BinaryHeap;

struct MedianFinder {
    small: BinaryHeap<i32>,           // max heap for smaller half
    large: BinaryHeap<Reverse<i32>>,  // min heap for larger half
}

impl MedianFinder {
    fn new() -> Self {
        MedianFinder {
            small: BinaryHeap::new(),
            large: BinaryHeap::new(),
        }
    }
    
    fn add_num(&mut self, num: i32) {
        // Add to appropriate heap
        if self.large.is_empty() || num > self.large.peek().unwrap().0 {
            self.large.push(Reverse(num));
        } else {
            self.small.push(num);
        }
        
        // Balance heaps
        if self.small.len() > self.large.len() + 1 {
            let val = self.small.pop().unwrap();
            self.large.push(Reverse(val));
        } else if self.large.len() > self.small.len() + 1 {
            let Reverse(val) = self.large.pop().unwrap();
            self.small.push(val);
        }
    }
    
    fn find_median(&self) -> f64 {
        if self.small.len() == self.large.len() {
            let small_top = *self.small.peek().unwrap() as f64;
            let large_top = self.large.peek().unwrap().0 as f64;
            (small_top + large_top) / 2.0
        } else if self.small.len() > self.large.len() {
            *self.small.peek().unwrap() as f64
        } else {
            self.large.peek().unwrap().0 as f64
        }
    }
}

fn ipo_maximize_capital(k: i32, w: i32, profits: Vec<i32>, capital: Vec<i32>) -> i32 {
    let mut min_capital_heap = BinaryHeap::new();
    
    for (i, &cap) in capital.iter().enumerate() {
        min_capital_heap.push(Reverse((cap, profits[i])));
    }
    
    let mut max_profit_heap = BinaryHeap::new();
    let mut current_capital = w;
    
    for _ in 0..k {
        // Move all affordable projects to profit heap
        while let Some(&Reverse((cap, profit))) = min_capital_heap.peek() {
            if cap <= current_capital {
                min_capital_heap.pop();
                max_profit_heap.push(profit);
            } else {
                break;
            }
        }
        
        // Pick most profitable project
        if let Some(profit) = max_profit_heap.pop() {
            current_capital += profit;
        } else {
            break;
        }
    }
    
    current_capital
}
```

## Sliding Window Maximum/Minimum

Finding maximum or minimum elements in sliding windows.

### Problem: Sliding Window Maximum

**Python Implementation:**
```python
from collections import deque

def sliding_window_maximum(nums: List[int], k: int) -> List[int]:
    """
    Find maximum in each sliding window using deque
    Time: O(n), Space: O(k)
    """
    result = []
    dq = deque()  # stores indices
    
    for i in range(len(nums)):
        # Remove elements outside window
        while dq and dq[0] <= i - k:
            dq.popleft()
        
        # Remove smaller elements from back
        while dq and nums[dq[-1]] <= nums[i]:
            dq.pop()
        
        dq.append(i)
        
        # Add maximum to result if window is complete
        if i >= k - 1:
            result.append(nums[dq[0]])
    
    return result

def sliding_window_maximum_heap(nums: List[int], k: int) -> List[int]:
    """
    Alternative implementation using heap
    Time: O(n log k), Space: O(k)
    """
    max_heap = []
    result = []
    
    for i in range(len(nums)):
        # Add current element
        heapq.heappush(max_heap, (-nums[i], i))
        
        # Remove elements outside window
        while max_heap and max_heap[0][1] <= i - k:
            heapq.heappop(max_heap)
        
        # Add maximum to result if window is complete
        if i >= k - 1:
            result.append(-max_heap[0][0])
    
    return result

def sliding_window_minimum(nums: List[int], k: int) -> List[int]:
    """Find minimum in each sliding window"""
    result = []
    dq = deque()
    
    for i in range(len(nums)):
        # Remove elements outside window
        while dq and dq[0] <= i - k:
            dq.popleft()
        
        # Remove larger elements from back
        while dq and nums[dq[-1]] >= nums[i]:
            dq.pop()
        
        dq.append(i)
        
        if i >= k - 1:
            result.append(nums[dq[0]])
    
    return result
```

**Rust Implementation:**
```rust
use std::collections::{BinaryHeap, VecDeque};

fn sliding_window_maximum(nums: Vec<i32>, k: i32) -> Vec<i32> {
    let k = k as usize;
    let mut result = Vec::new();
    let mut dq = VecDeque::new(); // stores indices
    
    for i in 0..nums.len() {
        // Remove elements outside window
        while let Some(&front) = dq.front() {
            if front <= i.saturating_sub(k) {
                dq.pop_front();
            } else {
                break;
            }
        }
        
        // Remove smaller elements from back
        while let Some(&back) = dq.back() {
            if nums[back] <= nums[i] {
                dq.pop_back();
            } else {
                break;
            }
        }
        
        dq.push_back(i);
        
        // Add maximum to result if window is complete
        if i >= k - 1 {
            result.push(nums[*dq.front().unwrap()]);
        }
    }
    
    result
}

fn sliding_window_maximum_heap(nums: Vec<i32>, k: i32) -> Vec<i32> {
    let k = k as usize;
    let mut max_heap = BinaryHeap::new();
    let mut result = Vec::new();
    
    for i in 0..nums.len() {
        // Add current element (negative for max heap)
        max_heap.push((nums[i], i));
        
        // Remove elements outside window
        while let Some(&(_, idx)) = max_heap.peek() {
            if idx <= i.saturating_sub(k) {
                max_heap.pop();
            } else {
                break;
            }
        }
        
        // Add maximum to result if window is complete
        if i >= k - 1 {
            result.push(max_heap.peek().unwrap().0);
        }
    }
    
    result
}
```

## Priority Queue Scheduling

Using heaps for task scheduling and priority management.

### Problem: Task Scheduler

**Python Implementation:**
```python
import heapq
from collections import Counter, deque

def task_scheduler(tasks: List[str], n: int) -> int:
    """
    Schedule tasks with cooldown period
    Time: O(m log a), Space: O(a) where m = total time, a = unique tasks
    """
    if n == 0:
        return len(tasks)
    
    task_counts = Counter(tasks)
    max_heap = [-count for count in task_counts.values()]
    heapq.heapify(max_heap)
    
    time = 0
    queue = deque()  # (count, available_time)
    
    while max_heap or queue:
        time += 1
        
        # Add available tasks back to heap
        if queue and queue[0][1] == time:
            count, _ = queue.popleft()
            heapq.heappush(max_heap, count)
        
        # Execute most frequent task
        if max_heap:
            count = heapq.heappop(max_heap)
            count += 1  # decrease count (it's negative)
            if count < 0:  # still has remaining tasks
                queue.append((count, time + n + 1))
    
    return time

def reorganize_string(s: str) -> str:
    """
    Reorganize string so no two adjacent characters are same
    Time: O(n log a), Space: O(a)
    """
    count = Counter(s)
    max_heap = [(-freq, char) for char, freq in count.items()]
    heapq.heapify(max_heap)
    
    result = []
    prev_freq, prev_char = 0, ''
    
    while max_heap:
        freq, char = heapq.heappop(max_heap)
        result.append(char)
        
        # Add previous character back if it still has frequency
        if prev_freq < 0:
            heapq.heappush(max_heap, (prev_freq, prev_char))
        
        freq += 1  # decrease frequency (it's negative)
        prev_freq, prev_char = freq, char
    
    return ''.join(result) if len(result) == len(s) else ""

def rearrange_string_k_distance(s: str, k: int) -> str:
    """
    Rearrange string so same characters are at least k distance apart
    Time: O(n log a), Space: O(a)
    """
    if k <= 1:
        return s
    
    count = Counter(s)
    max_heap = [(-freq, char) for char, freq in count.items()]
    heapq.heapify(max_heap)
    
    result = []
    queue = deque()
    
    while max_heap:
        freq, char = heapq.heappop(max_heap)
        result.append(char)
        queue.append((freq + 1, char))  # decrease frequency
        
        # Keep k-1 elements in queue before adding back to heap
        if len(queue) == k:
            front_freq, front_char = queue.popleft()
            if front_freq < 0:
                heapq.heappush(max_heap, (front_freq, front_char))
    
    return ''.join(result) if len(result) == len(s) else ""
```

**Rust Implementation:**
```rust
use std::collections::{HashMap, BinaryHeap, VecDeque};

fn task_scheduler(tasks: Vec<char>, n: i32) -> i32 {
    if n == 0 {
        return tasks.len() as i32;
    }
    
    let mut task_counts = HashMap::new();
    for task in tasks {
        *task_counts.entry(task).or_insert(0) += 1;
    }
    
    let mut max_heap = BinaryHeap::new();
    for count in task_counts.values() {
        max_heap.push(*count);
    }
    
    let mut time = 0;
    let mut queue = VecDeque::new(); // (count, available_time)
    
    while !max_heap.is_empty() || !queue.is_empty() {
        time += 1;
        
        // Add available tasks back to heap
        if let Some(&(count, available_time)) = queue.front() {
            if available_time == time {
                queue.pop_front();
                max_heap.push(count);
            }
        }
        
        // Execute most frequent task
        if let Some(count) = max_heap.pop() {
            let remaining = count - 1;
            if remaining > 0 {
                queue.push_back((remaining, time + n + 1));
            }
        }
    }
    
    time
}

fn reorganize_string(s: String) -> String {
    let mut count = HashMap::new();
    for ch in s.chars() {
        *count.entry(ch).or_insert(0) += 1;
    }
    
    let mut max_heap = BinaryHeap::new();
    for (ch, freq) in count {
        max_heap.push((freq, ch));
    }
    
    let mut result = Vec::new();
    let mut prev = (0, '\0');
    
    while let Some((freq, ch)) = max_heap.pop() {
        result.push(ch);
        
        // Add previous character back if it still has frequency
        if prev.0 > 0 {
            max_heap.push(prev);
        }
        
        prev = (freq - 1, ch);
    }
    
    if result.len() == s.len() {
        result.into_iter().collect()
    } else {
        String::new()
    }
}

fn rearrange_string_k_distance(s: String, k: i32) -> String {
    if k <= 1 {
        return s;
    }
    
    let mut count = HashMap::new();
    for ch in s.chars() {
        *count.entry(ch).or_insert(0) += 1;
    }
    
    let mut max_heap = BinaryHeap::new();
    for (ch, freq) in count {
        max_heap.push((freq, ch));
    }
    
    let mut result = Vec::new();
    let mut queue = VecDeque::new();
    
    while let Some((freq, ch)) = max_heap.pop() {
        result.push(ch);
        queue.push_back((freq - 1, ch));
        
        // Keep k-1 elements in queue before adding back to heap
        if queue.len() == k as usize {
            if let Some((front_freq, front_char)) = queue.pop_front() {
                if front_freq > 0 {
                    max_heap.push((front_freq, front_char));
                }
            }
        }
    }
    
    if result.len() == s.len() {
        result.into_iter().collect()
    } else {
        String::new()
    }
}
```

## Running Median Pattern

Efficiently maintaining median as data is added or removed.

### Problem: Median Maintenance

**Python Implementation:**
```python
class RunningMedian:
    """Maintain median as numbers are added"""
    def __init__(self):
        self.small = []  # max heap for smaller half
        self.large = []  # min heap for larger half
    
    def add_number(self, num: int) -> None:
        """Add number and maintain median property"""
        if not self.large or num > self.large[0]:
            heapq.heappush(self.large, num)
        else:
            heapq.heappush(self.small, -num)
        
        # Balance heaps
        self._balance_heaps()
    
    def remove_number(self, num: int) -> None:
        """Remove number and maintain median property"""
        if self.small and num <= -self.small[0]:
            self.small.remove(-num)
            heapq.heapify(self.small)
        else:
            self.large.remove(num)
            heapq.heapify(self.large)
        
        self._balance_heaps()
    
    def _balance_heaps(self):
        """Ensure heaps are balanced"""
        if len(self.small) > len(self.large) + 1:
            val = -heapq.heappop(self.small)
            heapq.heappush(self.large, val)
        elif len(self.large) > len(self.small) + 1:
            val = heapq.heappop(self.large)
            heapq.heappush(self.small, -val)
    
    def get_median(self) -> float:
        """Get current median"""
        if not self.small and not self.large:
            return 0.0
        
        if len(self.small) == len(self.large):
            return (-self.small[0] + self.large[0]) / 2.0
        elif len(self.small) > len(self.large):
            return float(-self.small[0])
        else:
            return float(self.large[0])

def median_of_running_integers(nums: List[int]) -> List[float]:
    """Return median after each number is added"""
    medians = []
    running_median = RunningMedian()
    
    for num in nums:
        running_median.add_number(num)
        medians.append(running_median.get_median())
    
    return medians

def median_in_sliding_window_optimized(nums: List[int], k: int) -> List[float]:
    """
    Find median in sliding window with optimized approach
    Time: O(n * k) worst case, but often better in practice
    """
    from sortedcontainers import SortedList
    
    if k == 1:
        return [float(x) for x in nums]
    
    result = []
    window = SortedList()
    
    for i in range(len(nums)):
        window.add(nums[i])
        
        if i >= k:
            window.remove(nums[i - k])
        
        if i >= k - 1:
            n = len(window)
            if n % 2 == 1:
                result.append(float(window[n // 2]))
            else:
                result.append((window[n // 2 - 1] + window[n // 2]) / 2.0)
    
    return result
```

**Rust Implementation:**
```rust
struct RunningMedian {
    small: BinaryHeap<i32>,           // max heap for smaller half
    large: BinaryHeap<Reverse<i32>>,  // min heap for larger half
}

impl RunningMedian {
    fn new() -> Self {
        RunningMedian {
            small: BinaryHeap::new(),
            large: BinaryHeap::new(),
        }
    }
    
    fn add_number(&mut self, num: i32) {
        if self.large.is_empty() || num > self.large.peek().unwrap().0 {
            self.large.push(Reverse(num));
        } else {
            self.small.push(num);
        }
        
        self.balance_heaps();
    }
    
    fn balance_heaps(&mut self) {
        if self.small.len() > self.large.len() + 1 {
            let val = self.small.pop().unwrap();
            self.large.push(Reverse(val));
        } else if self.large.len() > self.small.len() + 1 {
            let Reverse(val) = self.large.pop().unwrap();
            self.small.push(val);
        }
    }
    
    fn get_median(&self) -> f64 {
        if self.small.is_empty() && self.large.is_empty() {
            return 0.0;
        }
        
        if self.small.len() == self.large.len() {
            let small_top = *self.small.peek().unwrap() as f64;
            let large_top = self.large.peek().unwrap().0 as f64;
            (small_top + large_top) / 2.0
        } else if self.small.len() > self.large.len() {
            *self.small.peek().unwrap() as f64
        } else {
            self.large.peek().unwrap().0 as f64
        }
    }
}

fn median_of_running_integers(nums: Vec<i32>) -> Vec<f64> {
    let mut medians = Vec::new();
    let mut running_median = RunningMedian::new();
    
    for num in nums {
        running_median.add_number(num);
        medians.push(running_median.get_median());
    }
    
    medians
}
```

## Heap-based Graph Algorithms

Using heaps for graph problems like shortest path algorithms.

### Problem: Dijkstra's Algorithm and Variations

**Python Implementation:**
```python
import heapq
from typing import Dict, List, Tuple
from collections import defaultdict

def dijkstra_shortest_path(graph: Dict[int, List[Tuple[int, int]]], 
                          start: int, end: int) -> Tuple[int, List[int]]:
    """
    Find shortest path using Dijkstra's algorithm
    Time: O((V + E) log V), Space: O(V)
    """
    distances = defaultdict(lambda: float('inf'))
    distances[start] = 0
    previous = {}
    visited = set()
    
    min_heap = [(0, start)]
    
    while min_heap:
        current_dist, current = heapq.heappop(min_heap)
        
        if current in visited:
            continue
        
        visited.add(current)
        
        if current == end:
            # Reconstruct path
            path = []
            while current is not None:
                path.append(current)
                current = previous.get(current)
            return current_dist, path[::-1]
        
        for neighbor, weight in graph.get(current, []):
            if neighbor in visited:
                continue
            
            new_dist = current_dist + weight
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                previous[neighbor] = current
                heapq.heappush(min_heap, (new_dist, neighbor))
    
    return float('inf'), []

def network_delay_time(times: List[List[int]], n: int, k: int) -> int:
    """
    Find minimum time for signal to reach all nodes
    Time: O((V + E) log V), Space: O(V + E)
    """
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    
    distances = {}
    min_heap = [(0, k)]
    
    while min_heap:
        current_time, node = heapq.heappop(min_heap)
        
        if node in distances:
            continue
        
        distances[node] = current_time
        
        for neighbor, time in graph[node]:
            if neighbor not in distances:
                heapq.heappush(min_heap, (current_time + time, neighbor))
    
    return max(distances.values()) if len(distances) == n else -1

def cheapest_flights_with_k_stops(n: int, flights: List[List[int]], 
                                 src: int, dst: int, k: int) -> int:
    """
    Find cheapest flight with at most k stops
    Time: O(E + V * k * log(V * k)), Space: O(V * k)
    """
    graph = defaultdict(list)
    for u, v, price in flights:
        graph[u].append((v, price))
    
    # (cost, city, stops_used)
    min_heap = [(0, src, 0)]
    visited = {}  # (city, stops) -> min_cost
    
    while min_heap:
        cost, city, stops = heapq.heappop(min_heap)
        
        if city == dst:
            return cost
        
        if stops > k:
            continue
        
        if (city, stops) in visited and visited[(city, stops)] <= cost:
            continue
        
        visited[(city, stops)] = cost
        
        for next_city, price in graph[city]:
            heapq.heappush(min_heap, (cost + price, next_city, stops + 1))
    
    return -1

def path_with_minimum_effort(heights: List[List[int]]) -> int:
    """
    Find path with minimum effort (maximum height difference)
    Time: O(mn log(mn)), Space: O(mn)
    """
    if not heights or not heights[0]:
        return 0
    
    rows, cols = len(heights), len(heights[0])
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    
    # (effort, row, col)
    min_heap = [(0, 0, 0)]
    efforts = {}
    
    while min_heap:
        effort, row, col = heapq.heappop(min_heap)
        
        if (row, col) in efforts:
            continue
        
        efforts[(row, col)] = effort
        
        if row == rows - 1 and col == cols - 1:
            return effort
        
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            
            if (0 <= new_row < rows and 0 <= new_col < cols and 
                (new_row, new_col) not in efforts):
                
                height_diff = abs(heights[new_row][new_col] - heights[row][col])
                new_effort = max(effort, height_diff)
                heapq.heappush(min_heap, (new_effort, new_row, new_col))
    
    return -1

class KthLargest:
    """Find kth largest element in stream"""
    def __init__(self, k: int, nums: List[int]):
        self.k = k
        self.heap = nums
        heapq.heapify(self.heap)
        
        # Keep only k largest elements
        while len(self.heap) > k:
            heapq.heappop(self.heap)
    
    def add(self, val: int) -> int:
        heapq.heappush(self.heap, val)
        if len(self.heap) > self.k:
            heapq.heappop(self.heap)
        return self.heap[0]

def meeting_rooms_ii(intervals: List[List[int]]) -> int:
    """
    Find minimum number of meeting rooms needed
    Time: O(n log n), Space: O(n)
    """
    if not intervals:
        return 0
    
    # Sort by start time
    intervals.sort(key=lambda x: x[0])
    
    # Min heap to track end times
    min_heap = []
    
    for start, end in intervals:
        # Remove meetings that have ended
        while min_heap and min_heap[0] <= start:
            heapq.heappop(min_heap)
        
        # Add current meeting's end time
        heapq.heappush(min_heap, end)
    
    return len(min_heap)
```

**Rust Implementation:**
```rust
use std::collections::{HashMap, BinaryHeap};
use std::cmp::Reverse;

fn dijkstra_shortest_path(
    graph: &HashMap<i32, Vec<(i32, i32)>>, 
    start: i32, 
    end: i32
) -> (i32, Vec<i32>) {
    let mut distances = HashMap::new();
    distances.insert(start, 0);
    
    let mut previous = HashMap::new();
    let mut visited = std::collections::HashSet::new();
    let mut min_heap = BinaryHeap::new();
    
    min_heap.push(Reverse((0, start)));
    
    while let Some(Reverse((current_dist, current))) = min_heap.pop() {
        if visited.contains(&current) {
            continue;
        }
        
        visited.insert(current);
        
        if current == end {
            // Reconstruct path
            let mut path = Vec::new();
            let mut curr = Some(current);
            
            while let Some(node) = curr {
                path.push(node);
                curr = previous.get(&node).copied();
            }
            
            path.reverse();
            return (current_dist, path);
        }
        
        if let Some(neighbors) = graph.get(&current) {
            for &(neighbor, weight) in neighbors {
                if visited.contains(&neighbor) {
                    continue;
                }
                
                let new_dist = current_dist + weight;
                let neighbor_dist = distances.get(&neighbor).copied().unwrap_or(i32::MAX);
                
                if new_dist < neighbor_dist {
                    distances.insert(neighbor, new_dist);
                    previous.insert(neighbor, current);
                    min_heap.push(Reverse((new_dist, neighbor)));
                }
            }
        }
    }
    
    (i32::MAX, Vec::new())
}

fn network_delay_time(times: Vec<Vec<i32>>, n: i32, k: i32) -> i32 {
    let mut graph = HashMap::new();
    
    for time in times {
        let (u, v, w) = (time[0], time[1], time[2]);
        graph.entry(u).or_insert_with(Vec::new).push((v, w));
    }
    
    let mut distances = HashMap::new();
    let mut min_heap = BinaryHeap::new();
    min_heap.push(Reverse((0, k)));
    
    while let Some(Reverse((current_time, node))) = min_heap.pop() {
        if distances.contains_key(&node) {
            continue;
        }
        
        distances.insert(node, current_time);
        
        if let Some(neighbors) = graph.get(&node) {
            for &(neighbor, time) in neighbors {
                if !distances.contains_key(&neighbor) {
                    min_heap.push(Reverse((current_time + time, neighbor)));
                }
            }
        }
    }
    
    if distances.len() == n as usize {
        *distances.values().max().unwrap()
    } else {
        -1
    }
}

fn cheapest_flights_with_k_stops(
    n: i32, 
    flights: Vec<Vec<i32>>, 
    src: i32, 
    dst: i32, 
    k: i32
) -> i32 {
    let mut graph = HashMap::new();
    
    for flight in flights {
        let (u, v, price) = (flight[0], flight[1], flight[2]);
        graph.entry(u).or_insert_with(Vec::new).push((v, price));
    }
    
    let mut min_heap = BinaryHeap::new();
    min_heap.push(Reverse((0, src, 0))); // (cost, city, stops)
    
    let mut visited = HashMap::new();
    
    while let Some(Reverse((cost, city, stops))) = min_heap.pop() {
        if city == dst {
            return cost;
        }
        
        if stops > k {
            continue;
        }
        
        if let Some(&prev_cost) = visited.get(&(city, stops)) {
            if prev_cost <= cost {
                continue;
            }
        }
        
        visited.insert((city, stops), cost);
        
        if let Some(neighbors) = graph.get(&city) {
            for &(next_city, price) in neighbors {
                min_heap.push(Reverse((cost + price, next_city, stops + 1)));
            }
        }
    }
    
    -1
}

struct KthLargest {
    k: usize,
    heap: BinaryHeap<Reverse<i32>>, // min heap
}

impl KthLargest {
    fn new(k: i32, nums: Vec<i32>) -> Self {
        let k = k as usize;
        let mut heap = BinaryHeap::new();
        
        for num in nums {
            heap.push(Reverse(num));
        }
        
        // Keep only k largest elements
        while heap.len() > k {
            heap.pop();
        }
        
        KthLargest { k, heap }
    }
    
    fn add(&mut self, val: i32) -> i32 {
        self.heap.push(Reverse(val));
        if self.heap.len() > self.k {
            self.heap.pop();
        }
        self.heap.peek().unwrap().0
    }
}

fn meeting_rooms_ii(intervals: Vec<Vec<i32>>) -> i32 {
    if intervals.is_empty() {
        return 0;
    }
    
    let mut intervals = intervals;
    intervals.sort_by_key(|interval| interval[0]);
    
    let mut min_heap = BinaryHeap::new(); // min heap for end times
    
    for interval in intervals {
        let (start, end) = (interval[0], interval[1]);
        
        // Remove meetings that have ended
        while let Some(&Reverse(earliest_end)) = min_heap.peek() {
            if earliest_end <= start {
                min_heap.pop();
            } else {
                break;
            }
        }
        
        // Add current meeting's end time
        min_heap.push(Reverse(end));
    }
    
    min_heap.len() as i32
}
```

## Advanced Heap Techniques

### Custom Comparators and Complex Data Structures

**Python Implementation:**
```python
from typing import Any
import functools

@functools.total_ordering
class Task:
    """Custom task class with priority"""
    def __init__(self, priority: int, task_id: str, description: str):
        self.priority = priority
        self.task_id = task_id
        self.description = description
    
    def __lt__(self, other):
        # Higher priority tasks come first (lower number = higher priority)
        return self.priority < other.priority
    
    def __eq__(self, other):
        return self.priority == other.priority

def advanced_task_scheduler(tasks: List[Tuple[int, str, str]]) -> List[str]:
    """
    Schedule tasks by priority with custom objects
    """
    task_heap = []
    
    for priority, task_id, description in tasks:
        task = Task(priority, task_id, description)
        heapq.heappush(task_heap, task)
    
    execution_order = []
    while task_heap:
        task = heapq.heappop(task_heap)
        execution_order.append(task.task_id)
    
    return execution_order

class LazyDeletionHeap:
    """
    Heap with lazy deletion for efficient remove operations
    """
    def __init__(self):
        self.heap = []
        self.deleted = set()
    
    def push(self, item):
        heapq.heappush(self.heap, item)
    
    def pop(self):
        while self.heap and self.heap[0] in self.deleted:
            heapq.heappop(self.heap)
        
        if self.heap:
            item = heapq.heappop(self.heap)
            self.deleted.discard(item)
            return item
        return None
    
    def remove(self, item):
        self.deleted.add(item)
    
    def peek(self):
        while self.heap and self.heap[0] in self.deleted:
            heapq.heappop(self.heap)
        return self.heap[0] if self.heap else None
    
    def size(self):
        return len(self.heap) - len(self.deleted)

def merge_intervals_with_priorities(intervals: List[Tuple[int, int, int]]) -> List[Tuple[int, int, int]]:
    """
    Merge intervals where each interval has a priority
    Return merged intervals with highest priority in each range
    """
    if not intervals:
        return []
    
    # Sort by start time
    intervals.sort()
    
    result = []
    current_start, current_end, current_priority = intervals[0]
    
    for start, end, priority in intervals[1:]:
        if start <= current_end:
            # Overlapping intervals - merge and take higher priority
            current_end = max(current_end, end)
            current_priority = max(current_priority, priority)
        else:
            # Non-overlapping - add current to result
            result.append((current_start, current_end, current_priority))
            current_start, current_end, current_priority = start, end, priority
    
    result.append((current_start, current_end, current_priority))
    return result
```

**Rust Implementation:**
```rust
use std::collections::HashSet;

#[derive(Debug, Clone, PartialEq, Eq)]
struct Task {
    priority: i32,
    task_id: String,
    description: String,
}

impl PartialOrd for Task {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for Task {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        // Higher priority tasks come first (lower number = higher priority)
        other.priority.cmp(&self.priority)
    }
}

fn advanced_task_scheduler(tasks: Vec<(i32, String, String)>) -> Vec<String> {
    let mut task_heap = BinaryHeap::new();
    
    for (priority, task_id, description) in tasks {
        let task = Task { priority, task_id, description };
        task_heap.push(task);
    }
    
    let mut execution_order = Vec::new();
    while let Some(task) = task_heap.pop() {
        execution_order.push(task.task_id);
    }
    
    execution_order
}

struct LazyDeletionHeap<T> 
where 
    T: Ord + Clone + std::hash::Hash
{
    heap: BinaryHeap<Reverse<T>>,
    deleted: HashSet<T>,
}

impl<T> LazyDeletionHeap<T>
where 
    T: Ord + Clone + std::hash::Hash
{
    fn new() -> Self {
        LazyDeletionHeap {
            heap: BinaryHeap::new(),
            deleted: HashSet::new(),
        }
    }
    
    fn push(&mut self, item: T) {
        self.heap.push(Reverse(item));
    }
    
    fn pop(&mut self) -> Option<T> {
        while let Some(Reverse(ref item)) = self.heap.peek() {
            if self.deleted.contains(item) {
                self.heap.pop();
            } else {
                break;
            }
        }
        
        if let Some(Reverse(item)) = self.heap.pop() {
            self.deleted.remove(&item);
            Some(item)
        } else {
            None
        }
    }
    
    fn remove(&mut self, item: T) {
        self.deleted.insert(item);
    }
    
    fn peek(&mut self) -> Option<&T> {
        while let Some(Reverse(ref item)) = self.heap.peek() {
            if self.deleted.contains(item) {
                self.heap.pop();
            } else {
                break;
            }
        }
        
        self.heap.peek().map(|Reverse(item)| item)
    }
    
    fn len(&self) -> usize {
        self.heap.len() - self.deleted.len()
    }
}

fn merge_intervals_with_priorities(
    intervals: Vec<(i32, i32, i32)>
) -> Vec<(i32, i32, i32)> {
    if intervals.is_empty() {
        return Vec::new();
    }
    
    let mut intervals = intervals;
    intervals.sort_by_key(|&(start, _, _)| start);
    
    let mut result = Vec::new();
    let (mut current_start, mut current_end, mut current_priority) = intervals[0];
    
    for (start, end, priority) in intervals.into_iter().skip(1) {
        if start <= current_end {
            // Overlapping intervals - merge and take higher priority
            current_end = current_end.max(end);
            current_priority = current_priority.max(priority);
        } else {
            // Non-overlapping - add current to result
            result.push((current_start, current_end, current_priority));
            current_start = start;
            current_end = end;
            current_priority = priority;
        }
    }
    
    result.push((current_start, current_end, current_priority));
    result
}
```

## Time and Space Complexity Summary

| Pattern | Typical Time Complexity | Space Complexity | Use Cases |
|---------|------------------------|------------------|-----------|
| Top-K Elements | O(n log k) | O(k) | Finding largest/smallest K elements |
| K-Way Merge | O(n log k) | O(k) | Merging K sorted arrays/lists |
| Two Heaps | O(log n) per operation | O(n) | Finding medians, balanced partitioning |
| Sliding Window | O(n log k) | O(k) | Window maximum/minimum problems |
| Priority Scheduling | O(n log n) | O(n) | Task scheduling, resource allocation |
| Graph Algorithms | O((V+E) log V) | O(V) | Shortest path, network problems |

## Key Insights and Best Practices

1. **Choose the Right Heap Type**: Use min-heap for smallest elements, max-heap for largest elements
2. **Balance Two Heaps**: Keep heap sizes balanced (differ by at most 1) for median problems
3. **Lazy Deletion**: Use lazy deletion for efficient remove operations in heaps
4. **Custom Comparators**: Implement custom comparison logic for complex objects
5. **Memory Efficiency**: Maintain only necessary elements in heap (size K for top-K problems)
6. **Graph Problems**: Heaps are essential for Dijkstra's algorithm and variants

## Common Pitfalls to Avoid

1. **Heap Size Management**: Not maintaining proper heap size in top-K problems
2. **Comparison Logic**: Incorrect comparison operators leading to wrong heap behavior
3. **Index Tracking**: Losing track of original indices when sorting is involved
4. **Edge Cases**: Not handling empty heaps or single-element cases
5. **Time Complexity**: Using O(n log n) solutions when O(n log k) is sufficient

I've created a comprehensive guide to heap problem patterns with complete implementations in both Python and Rust. The guide covers:

## Key Patterns Covered:

1. **Heap Fundamentals** - Basic heap operations and data structures
2. **Top-K Elements** - Finding K largest/smallest elements efficiently
3. **K-Way Merge** - Merging multiple sorted arrays or lists
4. **Two Heaps** - Using complementary heaps for median and partitioning problems
5. **Sliding Window Maximum/Minimum** - Finding extrema in moving windows
6. **Running Median** - Maintaining median as data streams in
7. **Priority Queue Scheduling** - Task scheduling and resource allocation
8. **Heap-based Graph Algorithms** - Dijkstra's algorithm and variations
9. **Advanced Techniques** - Custom comparators and complex data structures

## Features:

- **Complete implementations** in both Python and Rust
- **Time and space complexity analysis** for each pattern
- **Real-world problem examples** with detailed solutions
- **Best practices and common pitfalls** to avoid
- **Performance comparisons** between different approaches

Each pattern includes multiple problem variations with optimized solutions, making this a practical reference for coding interviews and competitive programming. The implementations demonstrate proper heap usage, efficient algorithms, and language-specific optimizations.