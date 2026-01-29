# Data Stream Patterns: The Complete Mastery Guide

Data stream problems represent a fundamental paradigm shift in algorithmic thinking. Unlike static arrays where you have complete knowledge upfront, streams force you to make optimal decisions with **partial information, bounded memory, and real-time constraints**. This mirrors production systems: log analysis, network monitoring, financial trading, sensor data processing.

Mastering stream patterns requires understanding **three core tensions**:
1. **Space vs. Accuracy**: Perfect answers often require unbounded memory
2. **Time vs. Completeness**: Real-time processing limits computation per element
3. **Recency vs. History**: Balancing current context with long-term trends

---

## I. Foundational Stream Primitives

### 1.1 Running Statistics (Single-Pass Aggregation)

**Core Insight**: Maintain invariants that allow O(1) query after O(1) update.

**Pattern**: Transform raw stream into queryable state without storing entire history.

```rust
// Moving Average from Data Stream (LC 346)
struct MovingAverage {
    window: std::collections::VecDeque<i32>,
    capacity: usize,
    sum: i64,
}

impl MovingAverage {
    fn new(size: i32) -> Self {
        Self {
            window: std::collections::VecDeque::with_capacity(size as usize),
            capacity: size as usize,
            sum: 0,
        }
    }
    
    // The key insight: maintain sum invariant
    fn next(&mut self, val: i32) -> f64 {
        self.sum += val as i64;
        self.window.push_back(val);
        
        if self.window.len() > self.capacity {
            if let Some(old) = self.window.pop_front() {
                self.sum -= old as i64;
            }
        }
        
        self.sum as f64 / self.window.len() as f64
    }
}
```

**Go Implementation (Idiomatic)**:
```go
type MovingAverage struct {
    window   []int
    capacity int
    sum      int64
    start    int // Ring buffer optimization
}

func Constructor(size int) MovingAverage {
    return MovingAverage{
        window:   make([]int, 0, size),
        capacity: size,
    }
}

func (ma *MovingAverage) Next(val int) float64 {
    ma.sum += int64(val)
    
    if len(ma.window) < ma.capacity {
        ma.window = append(ma.window, val)
    } else {
        // Ring buffer: avoid pop_front overhead
        ma.sum -= int64(ma.window[ma.start])
        ma.window[ma.start] = val
        ma.start = (ma.start + 1) % ma.capacity
    }
    
    return float64(ma.sum) / float64(len(ma.window))
}
```

**Mental Model**: The "sum invariant" is your anchor. Every operation must preserve: `sum = Σ(window elements)`. This transforms O(n) recalculation into O(1) maintenance.

**Advanced Variant - Running Median**:
```rust
use std::collections::BinaryHeap;
use std::cmp::Reverse;

struct MedianFinder {
    // Max heap for smaller half
    left: BinaryHeap<i32>,
    // Min heap for larger half (using Reverse)
    right: BinaryHeap<Reverse<i32>>,
}

impl MedianFinder {
    fn new() -> Self {
        Self {
            left: BinaryHeap::new(),
            right: BinaryHeap::new(),
        }
    }
    
    // Invariant: |left| == |right| or |left| == |right| + 1
    // Invariant: max(left) <= min(right)
    fn add_num(&mut self, num: i32) {
        // Always insert to left first
        self.left.push(num);
        
        // Move largest from left to right to maintain order
        if let Some(max_left) = self.left.pop() {
            self.right.push(Reverse(max_left));
        }
        
        // Balance sizes: left should have equal or one more element
        if self.right.len() > self.left.len() {
            if let Some(Reverse(min_right)) = self.right.pop() {
                self.left.push(min_right);
            }
        }
    }
    
    fn find_median(&self) -> f64 {
        if self.left.len() > self.right.len() {
            *self.left.peek().unwrap() as f64
        } else {
            let left_max = *self.left.peek().unwrap() as f64;
            let right_min = self.right.peek().unwrap().0 as f64;
            (left_max + right_min) / 2.0
        }
    }
}
```

**Why Two Heaps?**: The median is the "boundary element" between small and large values. Two heaps let us maintain this boundary in O(log n) per insertion, O(1) per query. The key insight: **partition the stream, not sort it**.

---

### 1.2 Frequency Tracking

**Core Problem**: Count element occurrences with minimal space.

```rust
use std::collections::HashMap;

// Top K Frequent Elements (Stream Version)
struct FrequencyTracker {
    freq: HashMap<i32, usize>,
    count_to_elems: HashMap<usize, std::collections::HashSet<i32>>,
    max_freq: usize,
}

impl FrequencyTracker {
    fn new() -> Self {
        Self {
            freq: HashMap::new(),
            count_to_elems: HashMap::new(),
            max_freq: 0,
        }
    }
    
    fn add(&mut self, num: i32) {
        let old_freq = self.freq.get(&num).copied().unwrap_or(0);
        let new_freq = old_freq + 1;
        
        // Update freq map
        self.freq.insert(num, new_freq);
        
        // Remove from old bucket
        if old_freq > 0 {
            self.count_to_elems.get_mut(&old_freq)
                .map(|set| set.remove(&num));
        }
        
        // Add to new bucket
        self.count_to_elems.entry(new_freq)
            .or_insert_with(HashSet::new)
            .insert(num);
        
        self.max_freq = self.max_freq.max(new_freq);
    }
    
    fn get_top_k(&self, k: usize) -> Vec<i32> {
        let mut result = Vec::new();
        let mut freq = self.max_freq;
        
        while result.len() < k && freq > 0 {
            if let Some(elems) = self.count_to_elems.get(&freq) {
                for &elem in elems {
                    result.push(elem);
                    if result.len() == k {
                        break;
                    }
                }
            }
            freq -= 1;
        }
        
        result
    }
}
```

**Cognitive Shift**: Instead of sorting (O(n log n)), maintain a "bucket sort" structure. Each frequency level is a bucket. This achieves O(1) insertion, O(k) top-k retrieval.

---

## II. Windowing Patterns

### 2.1 Fixed-Size Sliding Window

**Mental Framework**: A window is a **view** into the stream. As it slides, maintain invariants efficiently.

```rust
// Maximum in Sliding Window (LC 239)
use std::collections::VecDeque;

fn max_sliding_window(nums: Vec<i32>, k: i32) -> Vec<i32> {
    let k = k as usize;
    let mut result = Vec::with_capacity(nums.len() - k + 1);
    // Deque stores indices, maintains decreasing order of values
    let mut deque: VecDeque<usize> = VecDeque::new();
    
    for (i, &num) in nums.iter().enumerate() {
        // Remove indices outside window
        while !deque.is_empty() && deque[0] <= i.saturating_sub(k) {
            deque.pop_front();
        }
        
        // Maintain decreasing order: remove smaller elements
        // They can never be maximum while current element is in window
        while !deque.is_empty() && nums[deque[deque.len() - 1]] <= num {
            deque.pop_back();
        }
        
        deque.push_back(i);
        
        // Start recording once window is full
        if i >= k - 1 {
            result.push(nums[deque[0]]);
        }
    }
    
    result
}
```

**Key Insight**: The deque stores **candidate maximums**. An element can only be maximum if no larger element exists to its right within the window. This is a **monotonic deque** pattern.

**Go Version with Detailed Comments**:
```go
func maxSlidingWindow(nums []int, k int) []int {
    if len(nums) == 0 || k == 0 {
        return []int{}
    }
    
    result := make([]int, 0, len(nums)-k+1)
    deque := make([]int, 0, k) // Stores indices
    
    for i, num := range nums {
        // Invariant 1: Remove expired indices
        for len(deque) > 0 && deque[0] <= i-k {
            deque = deque[1:]
        }
        
        // Invariant 2: Maintain decreasing values
        // Why? If nums[j] <= nums[i] and j < i, then nums[j]
        // can never be maximum while nums[i] is in window
        for len(deque) > 0 && nums[deque[len(deque)-1]] <= num {
            deque = deque[:len(deque)-1]
        }
        
        deque = append(deque, i)
        
        // Window is full, record maximum
        if i >= k-1 {
            result = append(result, nums[deque[0]])
        }
    }
    
    return result
}
```

---

### 2.2 Variable-Size Windows (Two Pointers)

**Pattern**: Expand window when condition allows, contract when violated.

```rust
// Longest Substring Without Repeating Characters (LC 3)
use std::collections::HashMap;

fn length_of_longest_substring(s: String) -> i32 {
    let chars: Vec<char> = s.chars().collect();
    let mut last_pos: HashMap<char, usize> = HashMap::new();
    let mut max_len = 0;
    let mut start = 0;
    
    for (end, &ch) in chars.iter().enumerate() {
        // If character seen and within current window, shrink window
        if let Some(&pos) = last_pos.get(&ch) {
            if pos >= start {
                start = pos + 1;
            }
        }
        
        last_pos.insert(ch, end);
        max_len = max_len.max(end - start + 1);
    }
    
    max_len as i32
}
```

**Advanced Pattern - K Distinct Characters**:
```rust
fn longest_k_distinct(s: String, k: i32) -> i32 {
    if k == 0 {
        return 0;
    }
    
    let chars: Vec<char> = s.chars().collect();
    let mut freq: HashMap<char, usize> = HashMap::new();
    let mut max_len = 0;
    let mut left = 0;
    
    for right in 0..chars.len() {
        // Expand: add right character
        *freq.entry(chars[right]).or_insert(0) += 1;
        
        // Contract: remove left characters until valid
        while freq.len() > k as usize {
            let left_char = chars[left];
            let count = freq.get_mut(&left_char).unwrap();
            *count -= 1;
            if *count == 0 {
                freq.remove(&left_char);
            }
            left += 1;
        }
        
        max_len = max_len.max(right - left + 1);
    }
    
    max_len as i32
}
```

**Cognitive Model**: The window is **elastic**. It stretches right (optimistically), then contracts left (to restore validity). Think of it as **exploring then correcting**.

---

## III. Order Statistics in Streams

### 3.1 Kth Largest Element Stream (LC 703)

```rust
use std::collections::BinaryHeap;
use std::cmp::Reverse;

struct KthLargest {
    k: usize,
    // Min heap of size k: smallest element is kth largest
    heap: BinaryHeap<Reverse<i32>>,
}

impl KthLargest {
    fn new(k: i32, nums: Vec<i32>) -> Self {
        let k = k as usize;
        let mut heap = BinaryHeap::new();
        
        for num in nums {
            heap.push(Reverse(num));
            if heap.len() > k {
                heap.pop();
            }
        }
        
        Self { k, heap }
    }
    
    fn add(&mut self, val: i32) -> i32 {
        self.heap.push(Reverse(val));
        
        if self.heap.len() > self.k {
            self.heap.pop();
        }
        
        // Heap top is kth largest
        self.heap.peek().unwrap().0
    }
}
```

**Why Min Heap?**: We want the kth largest, which is the **smallest among the k largest elements**. A min heap naturally exposes this at the root. Elements smaller than the kth largest are irrelevant—discarded immediately.

**Go Implementation with Generics-like Interface**:
```go
import "container/heap"

type IntHeap []int

func (h IntHeap) Len() int           { return len(h) }
func (h IntHeap) Less(i, j int) bool { return h[i] < h[j] }
func (h IntHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }
func (h *IntHeap) Push(x interface{}) { *h = append(*h, x.(int)) }
func (h *IntHeap) Pop() interface{} {
    old := *h
    n := len(old)
    x := old[n-1]
    *h = old[0 : n-1]
    return x
}

type KthLargest struct {
    k    int
    heap *IntHeap
}

func Constructor(k int, nums []int) KthLargest {
    h := &IntHeap{}
    heap.Init(h)
    
    kth := KthLargest{k: k, heap: h}
    for _, num := range nums {
        kth.Add(num)
    }
    
    return kth
}

func (kth *KthLargest) Add(val int) int {
    heap.Push(kth.heap, val)
    
    if kth.heap.Len() > kth.k {
        heap.Pop(kth.heap)
    }
    
    return (*kth.heap)[0]
}
```

---

## IV. Advanced Stream Patterns

### 4.1 Range Queries with Updates

**Pattern**: Segment Tree or Fenwick Tree for streams with updates.

```rust
// Range Sum Query - Mutable (LC 307)
struct NumArray {
    tree: Vec<i32>,
    n: usize,
}

impl NumArray {
    fn new(nums: Vec<i32>) -> Self {
        let n = nums.len();
        let mut tree = vec![0; 2 * n];
        
        // Build tree: leaves at indices [n, 2n), internal nodes at [1, n)
        for i in 0..n {
            tree[n + i] = nums[i];
        }
        
        for i in (1..n).rev() {
            tree[i] = tree[2 * i] + tree[2 * i + 1];
        }
        
        Self { tree, n }
    }
    
    fn update(&mut self, index: i32, val: i32) {
        let mut pos = self.n + index as usize;
        self.tree[pos] = val;
        
        // Propagate changes upward
        while pos > 1 {
            pos /= 2;
            self.tree[pos] = self.tree[2 * pos] + self.tree[2 * pos + 1];
        }
    }
    
    fn sum_range(&self, left: i32, right: i32) -> i32 {
        let mut l = self.n + left as usize;
        let mut r = self.n + right as usize + 1;
        let mut sum = 0;
        
        while l < r {
            if l % 2 == 1 {
                sum += self.tree[l];
                l += 1;
            }
            if r % 2 == 1 {
                r -= 1;
                sum += self.tree[r];
            }
            l /= 2;
            r /= 2;
        }
        
        sum
    }
}
```

**Mental Model**: The segment tree is a **binary tree of intervals**. Each node represents a range and stores its aggregate (sum, min, max, etc.). Updates propagate O(log n) levels, queries combine O(log n) non-overlapping segments.

---

### 4.2 Timestamp-Based Streams

```rust
use std::collections::BTreeMap;

// Time Based Key-Value Store (LC 981)
struct TimeMap {
    store: std::collections::HashMap<String, BTreeMap<i32, String>>,
}

impl TimeMap {
    fn new() -> Self {
        Self {
            store: std::collections::HashMap::new(),
        }
    }
    
    fn set(&mut self, key: String, value: String, timestamp: i32) {
        self.store
            .entry(key)
            .or_insert_with(BTreeMap::new)
            .insert(timestamp, value);
    }
    
    fn get(&self, key: String, timestamp: i32) -> String {
        if let Some(timeline) = self.store.get(&key) {
            // Find largest timestamp <= given timestamp
            timeline.range(..=timestamp)
                .next_back()
                .map(|(_, v)| v.clone())
                .unwrap_or_default()
        } else {
            String::new()
        }
    }
}
```

**Key Insight**: `BTreeMap::range()` gives us efficient range queries. The `.next_back()` on a reverse range gets the largest timestamp ≤ target in O(log n).

**Go Version with Manual Binary Search**:
```go
type TimeMap struct {
    store map[string][]TimestampValue
}

type TimestampValue struct {
    timestamp int
    value     string
}

func Constructor() TimeMap {
    return TimeMap{
        store: make(map[string][]TimestampValue),
    }
}

func (tm *TimeMap) Set(key string, value string, timestamp int) {
    tm.store[key] = append(tm.store[key], TimestampValue{timestamp, value})
}

func (tm *TimeMap) Get(key string, timestamp int) string {
    values, exists := tm.store[key]
    if !exists {
        return ""
    }
    
    // Binary search for largest timestamp <= target
    left, right := 0, len(values)-1
    result := ""
    
    for left <= right {
        mid := left + (right-left)/2
        if values[mid].timestamp <= timestamp {
            result = values[mid].value
            left = mid + 1
        } else {
            right = mid - 1
        }
    }
    
    return result
}
```

---

### 4.3 LRU Cache Pattern (Dual Data Structure)

```rust
use std::collections::HashMap;
use std::cell::RefCell;
use std::rc::Rc;

struct Node {
    key: i32,
    value: i32,
    prev: Option<Rc<RefCell<Node>>>,
    next: Option<Rc<RefCell<Node>>>,
}

struct LRUCache {
    capacity: usize,
    cache: HashMap<i32, Rc<RefCell<Node>>>,
    head: Rc<RefCell<Node>>, // Dummy nodes for cleaner logic
    tail: Rc<RefCell<Node>>,
}

impl LRUCache {
    fn new(capacity: i32) -> Self {
        let head = Rc::new(RefCell::new(Node {
            key: 0,
            value: 0,
            prev: None,
            next: None,
        }));
        
        let tail = Rc::new(RefCell::new(Node {
            key: 0,
            value: 0,
            prev: Some(Rc::clone(&head)),
            next: None,
        }));
        
        head.borrow_mut().next = Some(Rc::clone(&tail));
        
        Self {
            capacity: capacity as usize,
            cache: HashMap::new(),
            head,
            tail,
        }
    }
    
    fn remove(&mut self, node: &Rc<RefCell<Node>>) {
        let prev = node.borrow().prev.as_ref().map(Rc::clone);
        let next = node.borrow().next.as_ref().map(Rc::clone);
        
        if let (Some(p), Some(n)) = (prev, next) {
            p.borrow_mut().next = Some(Rc::clone(&n));
            n.borrow_mut().prev = Some(Rc::clone(&p));
        }
    }
    
    fn add_to_front(&mut self, node: &Rc<RefCell<Node>>) {
        let first = self.head.borrow().next.as_ref().map(Rc::clone).unwrap();
        
        node.borrow_mut().prev = Some(Rc::clone(&self.head));
        node.borrow_mut().next = Some(Rc::clone(&first));
        
        self.head.borrow_mut().next = Some(Rc::clone(node));
        first.borrow_mut().prev = Some(Rc::clone(node));
    }
    
    fn get(&mut self, key: i32) -> i32 {
        if let Some(node) = self.cache.get(&key).map(Rc::clone) {
            let value = node.borrow().value;
            self.remove(&node);
            self.add_to_front(&node);
            value
        } else {
            -1
        }
    }
    
    fn put(&mut self, key: i32, value: i32) {
        if let Some(node) = self.cache.get(&key).map(Rc::clone) {
            node.borrow_mut().value = value;
            self.remove(&node);
            self.add_to_front(&node);
        } else {
            let new_node = Rc::new(RefCell::new(Node {
                key,
                value,
                prev: None,
                next: None,
            }));
            
            self.cache.insert(key, Rc::clone(&new_node));
            self.add_to_front(&new_node);
            
            if self.cache.len() > self.capacity {
                // Remove least recently used (before tail)
                let lru = self.tail.borrow().prev.as_ref().map(Rc::clone).unwrap();
                let lru_key = lru.borrow().key;
                self.remove(&lru);
                self.cache.remove(&lru_key);
            }
        }
    }
}
```

**Cleaner Go Implementation**:
```go
type Node struct {
    key, value int
    prev, next *Node
}

type LRUCache struct {
    capacity int
    cache    map[int]*Node
    head, tail *Node
}

func Constructor(capacity int) LRUCache {
    head, tail := &Node{}, &Node{}
    head.next, tail.prev = tail, head
    
    return LRUCache{
        capacity: capacity,
        cache:    make(map[int]*Node),
        head:     head,
        tail:     tail,
    }
}

func (lru *LRUCache) remove(node *Node) {
    node.prev.next = node.next
    node.next.prev = node.prev
}

func (lru *LRUCache) addToFront(node *Node) {
    node.prev = lru.head
    node.next = lru.head.next
    lru.head.next.prev = node
    lru.head.next = node
}

func (lru *LRUCache) Get(key int) int {
    if node, exists := lru.cache[key]; exists {
        lru.remove(node)
        lru.addToFront(node)
        return node.value
    }
    return -1
}

func (lru *LRUCache) Put(key, value int) {
    if node, exists := lru.cache[key]; exists {
        node.value = value
        lru.remove(node)
        lru.addToFront(node)
        return
    }
    
    newNode := &Node{key: key, value: value}
    lru.cache[key] = newNode
    lru.addToFront(newNode)
    
    if len(lru.cache) > lru.capacity {
        lru := lru.tail.prev
        lru.remove(lru)
        delete(lru.cache, lru.key)
    }
}
```

**Pattern Recognition**: LRU requires **O(1) access AND O(1) reordering**. HashMap gives O(1) access, doubly-linked list gives O(1) reordering. The combination is powerful: two data structures maintaining dual invariants.

---

## V. Probabilistic Stream Algorithms

### 5.1 Reservoir Sampling (Uniform Random from Stream)

```rust
use rand::Rng;

// Linked List Random Node (LC 382)
struct Solution {
    head: Option<Box<ListNode>>,
}

impl Solution {
    fn new(head: Option<Box<ListNode>>) -> Self {
        Self { head }
    }
    
    // Picks random node with uniform probability
    fn get_random(&self) -> i32 {
        let mut rng = rand::thread_rng();
        let mut current = &self.head;
        let mut result = 0;
        let mut count = 0;
        
        while let Some(node) = current {
            count += 1;
            // With probability 1/count, replace result
            if rng.gen_range(0..count) == 0 {
                result = node.val;
            }
            current = &node.next;
        }
        
        result
    }
}
```

**Mathematical Insight**: For the ith element, probability it's chosen = (1/i) × (i/(i+1)) × ((i+1)/(i+2)) × ... × ((n-1)/n) = 1/n. Each element has exactly 1/n probability of being selected, achieving **perfect uniformity without knowing stream length**.

**Advanced: Weighted Reservoir Sampling**:
```rust
// Random Pick with Weight (LC 528)
struct Solution {
    prefix_sums: Vec<i32>,
    total: i32,
}

impl Solution {
    fn new(w: Vec<i32>) -> Self {
        let mut prefix_sums = Vec::with_capacity(w.len());
        let mut sum = 0;
        
        for weight in w {
            sum += weight;
            prefix_sums.push(sum);
        }
        
        Self {
            prefix_sums,
            total: sum,
        }
    }
    
    fn pick_index(&self) -> i32 {
        let target = rand::thread_rng().gen_range(1..=self.total);
        
        // Binary search for first element >= target
        let mut left = 0;
        let mut right = self.prefix_sums.len();
        
        while left < right {
            let mid = left + (right - left) / 2;
            if self.prefix_sums[mid] < target {
                left = mid + 1;
            } else {
                right = mid;
            }
        }
        
        left as i32
    }
}
```

---

## VI. Monotonic Structures in Streams

### 6.1 Monotonic Stack Pattern

```rust
// Online Stock Span (LC 901)
struct StockSpanner {
    // Stack stores (price, span) pairs
    stack: Vec<(i32, i32)>,
}

impl StockSpanner {
    fn new() -> Self {
        Self { stack: Vec::new() }
    }
    
    fn next(&mut self, price: i32) -> i32 {
        let mut span = 1;
        
        // Pop all elements with price <= current price
        while let Some(&(prev_price, prev_span)) = self.stack.last() {
            if prev_price <= price {
                span += prev_span;
                self.stack.pop();
            } else {
                break;
            }
        }
        
        self.stack.push((price, span));
        span
    }
}
```

**Key Insight**: For each price, we want to know how many consecutive previous prices are ≤ current. By maintaining a monotonic stack, we can **accumulate spans efficiently**. If we pop an element, its span becomes part of our span.

**Visualization**:
```
Prices:  100, 80, 60, 70, 60, 75, 85
Spans:     1,  1,  1,  2,  1,  4,  6
```

When 85 arrives:
- Pop 75 (span 4): our span += 4
- Pop 60, 70, 60: already accounted in 75's span
- Pop 80 (span 1): our span += 1
- Can't pop 100: stop
- Final span: 1 (self) + 4 (from 75) + 1 (from 80) = 6

---

## VII. Pattern Synthesis: Complex Stream Problems

### 7.1 Count of Range Sum (LC 327) - Merge Sort + Stream Processing

```rust
fn count_range_sum(nums: Vec<i32>, lower: i32, upper: i32) -> i32 {
    let n = nums.len();
    let mut prefix_sums = vec![0i64; n + 1];
    
    // Build prefix sums
    for i in 0..n {
        prefix_sums[i + 1] = prefix_sums[i] + nums[i] as i64;
    }
    
    fn merge_count(
        sums: &mut [i64],
        lower: i64,
        upper: i64,
        temp: &mut [i64],
    ) -> i32 {
        let n = sums.len();
        if n <= 1 {
            return 0;
        }
        
        let mid = n / 2;
        let mut count = merge_count(&mut sums[..mid], lower, upper, temp);
        count += merge_count(&mut sums[mid..], lower, upper, temp);
        
        // Count ranges crossing the midpoint
        let mut j = mid;
        let mut k = mid;
        
        for i in 0..mid {
            // Find range [j, k) where sums[j..k] - sums[i] in [lower, upper]
            while j < n && sums[j] - sums[i] < lower {
                j += 1;
            }
            while k < n && sums[k] - sums[i] <= upper {
                k += 1;
            }
            count += (k - j) as i32;
        }
        
        // Merge two sorted halves
        temp[..n].copy_from_slice(sums);
        let mut i = 0;
        let mut j = mid;
        let mut k = 0;
        
        while i < mid && j < n {
            if temp[i] <= temp[j] {
                sums[k] = temp[i];
                i += 1;
            } else {
                sums[k] = temp[j];
                j += 1;
            }
            k += 1;
        }
        
        while i < mid {
            sums[k] = temp[i];
            i += 1;
            k += 1;
        }
        
        count
    }
    
    let mut temp = vec![0i64; n + 1];
    merge_count(&mut prefix_sums, lower as i64, upper as i64, &mut temp)
}
```

**Pattern Recognition**: This combines:
1. **Prefix sums** to convert range queries to point queries
2. **Divide and conquer** to count efficiently
3. **Two pointers** during merge to count valid ranges

---

## VIII. Mental Models for Stream Mastery

### Model 1: The Invariant Preservation Principle
Every stream operation should maintain a **set of invariants** that enable efficient queries. Design your data structure around what invariants make queries O(1) or O(log n).

### Model 2: The Space-Time Tradeoff Spectrum
```
No extra space ←→ O(n) space
O(n) time      ←→ O(1) time

Stream algorithms live on this spectrum.
Choose based on constraints.
```

### Model 3: The Monotonic Elimination Heuristic
If an element X can never affect future answers when element Y arrives (and Y is "better"), **eliminate X immediately**. This underlies monotonic stacks/queues.

### Model 4: The Prefix Transform
Many stream problems become trivial after transforming to prefix sums/products/XORs. Think: "What cumulative function makes this easier?"

---

## IX. Performance Characteristics Summary

| Pattern | Add/Update | Query | Space | Use Case |
|---------|-----------|--------|-------|----------|
| Running Stats | O(1) | O(1) | O(1) | Averages, sums |
| Sliding Window Max | O(1) amortized | O(1) | O(k) | Window extrema |
| Median Finder | O(log n) | O(1) | O(n) | Order statistics |
| Segment Tree | O(log n) | O(log n) | O(n) | Range updates/queries |
| LRU Cache | O(1) | O(1) | O(n) | Cache systems |
| Monotonic Stack | O(1) amortized | N/A | O(n) worst | Next greater/smaller |

---

## X. Problem Classification Framework

**Tier 1: Foundation (Master These First)**
- Moving Average (LC 346)
- Find Median from Data Stream (LC 295)
- Kth Largest Element in Stream (LC 703)
- Sliding Window Maximum (LC 239)

**Tier 2: Core Patterns**
- LRU Cache (LC 146)
- LFU Cache (LC 460)
- Time Based Key-Value Store (LC 981)
- Online Stock Span (LC 901)

**Tier 3: Advanced Combinations**
- Count of Range Sum (LC 327)
- Longest Substring with At Most K Distinct (LC 340)
- Random Pick with Weight (LC 528)

**Tier 4: Expert Level**
- Find Median from Data Stream (with removal)
- Count of Smaller Numbers After Self (LC 315)
- Range Module (LC 715)

---

## Final Thoughts: The Stream Mindset

Stream problems demand a **different cognitive mode**:

1. **Think incrementally**: Each element is processed exactly once
2. **Maintain minimal state**: Only store what's absolutely necessary for future queries
3. **Exploit monotonicity**: Past elements that can't affect future answers should be discarded
4. **Amortized analysis**: Some operations may be O(n) individually but O(1) amortized

The master asks: "What's the minimum I need to remember to answer the next query correctly?"

This is algorithmic **minimalism**—stripping away all non-essential computation and storage. It's the essence of efficiency.

Continue your practice with this principle: **Every data structure is a commitment to certain invariants. Choose them wisely.**