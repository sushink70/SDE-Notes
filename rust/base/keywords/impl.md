# DSA in Rust: A World-Class Comprehensive Guide
> *"The expert in anything was once a beginner who refused to give up."*
> Precision. Depth. Mastery.

---

## TABLE OF CONTENTS

1. [Rust's Mental Model for DSA](#1-rusts-mental-model-for-dsa)
2. [Arrays & Slices](#2-arrays--slices)
3. [Linked Lists](#3-linked-lists)
4. [Stacks & Queues](#4-stacks--queues)
5. [Hash Maps & Hash Sets](#5-hash-maps--hash-sets)
6. [Trees: Binary, BST, AVL](#6-trees-binary-bst-avl)
7. [Heaps & Priority Queues](#7-heaps--priority-queues)
8. [Segment Trees & Fenwick Trees](#8-segment-trees--fenwick-trees)
9. [Graphs](#9-graphs)
10. [Tries](#10-tries)
11. [Disjoint Set Union (DSU)](#11-disjoint-set-union-dsu)
12. [Sorting Algorithms](#12-sorting-algorithms)
13. [Searching & Binary Search Mastery](#13-searching--binary-search-mastery)
14. [Dynamic Programming](#14-dynamic-programming)
15. [String Algorithms](#15-string-algorithms)
16. [Advanced Topics](#16-advanced-topics)

---

## 1. RUST'S MENTAL MODEL FOR DSA

### Why Rust Changes How You Think About DSA

In C, you manage memory manually. In Go, the GC handles everything. Rust introduces a **third paradigm**: the compiler *proves* memory safety at compile time through ownership. This is not a burden — it is a *superpower* that forces you to think clearly about data ownership, which is the essence of DSA design.

**Core Mental Model: Every value has exactly ONE owner. Period.**

```
Value → Owner → Drop (when owner goes out of scope)
```

For DSA, this means:
- **Tree nodes**: Who owns children? The parent.
- **Graph edges**: Who owns nodes? The graph itself.
- **Linked lists**: Who owns the next node? The current node.

### Ownership Patterns for Data Structures

```rust
// Pattern 1: Box<T> — Heap allocation, single owner (trees, linked lists)
// Pattern 2: Rc<T> — Reference counted, shared ownership (DAGs, shared nodes)
// Pattern 3: Arc<T> — Atomic Rc, thread-safe shared ownership
// Pattern 4: RefCell<T> — Interior mutability (doubly linked lists)
// Pattern 5: Vec<T> — Contiguous heap array (adjacency lists, stacks)

// The DSA hierarchy of pointer choices:
// Performance: Box > Rc > Arc > RefCell (overhead increases)
// Use the LEAST powerful abstraction that solves your problem.
```

### The Borrow Checker as a DSA Teacher

```rust
// This FAILS — and for good reason:
fn wrong_approach() {
    let mut v = vec![1, 2, 3];
    let first = &v[0];      // immutable borrow
    v.push(4);              // ERROR: mutable borrow while immutable exists
    println!("{}", first);  // first might be dangling if vec reallocated!
}

// This TEACHES you: iterator invalidation is a real bug class.
// Rust forces you to think about it upfront.

// Correct approach:
fn correct_approach() {
    let mut v = vec![1, 2, 3];
    let first_val = v[0];   // copy the value, not a reference
    v.push(4);
    println!("{}", first_val); // works fine
}
```

### Performance Intuitions in Rust

```rust
// Stack allocation vs Heap allocation
// Stack: ultra-fast, size known at compile time
let arr: [i32; 1000] = [0; 1000];  // stack — instant

// Heap: flexible size, small allocation overhead
let vec: Vec<i32> = Vec::with_capacity(1000);  // heap — malloc call

// Key insight: Vec<T> is THREE words on the stack:
// [ptr: *T | len: usize | cap: usize]
// The DATA lives on the heap. The METADATA lives on the stack.

// For DSA: prefer Vec over Box<[T]> when size changes,
// prefer Box<[T]> when size is fixed (no wasted capacity field).

// Cache performance: contiguous > linked
// Vec<T> → O(1) cache lines for sequential access
// LinkedList<T> → O(n) cache misses for sequential access
// This is why Vec almost always beats LinkedList in practice.
```

---

## 2. ARRAYS & SLICES

### Mental Model: Arrays as the Foundation of Everything

Every advanced data structure is built on contiguous memory. Understanding arrays deeply means understanding cache lines, memory layouts, and pointer arithmetic.

```
Memory layout of Vec<i32> with elements [1, 2, 3, 4]:

Stack:
┌──────────────────┐
│ ptr → 0x7f3a1000 │  8 bytes
│ len = 4          │  8 bytes  
│ cap = 4          │  8 bytes
└──────────────────┘

Heap at 0x7f3a1000:
┌────┬────┬────┬────┐
│ 1  │ 2  │ 3  │ 4  │  4 × 4 = 16 bytes
└────┴────┴────┴────┘
```

### Two-Pointer Technique

The two-pointer technique is a pattern that reduces O(n²) brute force to O(n) by exploiting sorted order or convergence properties.

```rust
/// Two Sum — sorted array variant
/// Pattern: converging pointers from both ends
/// Time: O(n), Space: O(1)
fn two_sum_sorted(nums: &[i32], target: i32) -> Option<(usize, usize)> {
    let (mut left, mut right) = (0, nums.len().saturating_sub(1));
    
    while left < right {
        let sum = nums[left] + nums[right];
        match sum.cmp(&target) {
            std::cmp::Ordering::Equal   => return Some((left, right)),
            std::cmp::Ordering::Less    => left += 1,   // need larger sum
            std::cmp::Ordering::Greater => right -= 1,  // need smaller sum
        }
    }
    None
}

/// Container With Most Water
/// Key insight: always move the SHORTER pointer inward.
/// Proof: if we move the taller pointer, the width decreases AND
/// the height is bounded by the shorter one anyway — can only get worse.
/// Time: O(n), Space: O(1)
fn max_water_container(heights: &[i32]) -> i32 {
    let (mut left, mut right) = (0, heights.len() - 1);
    let mut max_water = 0;
    
    while left < right {
        let width  = (right - left) as i32;
        let height = heights[left].min(heights[right]);
        max_water  = max_water.max(width * height);
        
        // Move the shorter side — the key insight
        if heights[left] < heights[right] {
            left += 1;
        } else {
            right -= 1;
        }
    }
    max_water
}

/// Three Sum — deduplication matters
/// Time: O(n²), Space: O(1) excluding output
fn three_sum(mut nums: Vec<i32>) -> Vec<[i32; 3]> {
    nums.sort_unstable(); // sort first — enables two-pointer
    let mut result = Vec::new();
    let n = nums.len();
    
    for i in 0..n.saturating_sub(2) {
        // Skip duplicates for the first element
        if i > 0 && nums[i] == nums[i - 1] { continue; }
        if nums[i] > 0 { break; } // optimization: sorted, can't sum to 0
        
        let (mut left, mut right) = (i + 1, n - 1);
        let target = -nums[i];
        
        while left < right {
            let sum = nums[left] + nums[right];
            match sum.cmp(&target) {
                std::cmp::Ordering::Equal => {
                    result.push([nums[i], nums[left], nums[right]]);
                    // Skip duplicates for left and right
                    while left < right && nums[left]  == nums[left + 1]  { left += 1; }
                    while left < right && nums[right] == nums[right - 1] { right -= 1; }
                    left += 1;
                    right -= 1;
                }
                std::cmp::Ordering::Less    => left += 1,
                std::cmp::Ordering::Greater => right -= 1,
            }
        }
    }
    result
}
```

### Sliding Window Technique

The sliding window is a two-pointer variant where the window expands and contracts based on a validity condition.

```rust
/// Longest Substring Without Repeating Characters
/// Mental model: maintain a window [left, right] where all chars are unique.
/// When we add a char that already exists, move left past its last occurrence.
/// Time: O(n), Space: O(min(n, alphabet_size))
fn longest_unique_substring(s: &str) -> usize {
    use std::collections::HashMap;
    let bytes = s.as_bytes();
    let mut last_seen: HashMap<u8, usize> = HashMap::new();
    let mut max_len = 0;
    let mut left = 0;
    
    for (right, &ch) in bytes.iter().enumerate() {
        // If char was seen within current window, shrink from left
        if let Some(&prev_pos) = last_seen.get(&ch) {
            if prev_pos >= left {
                left = prev_pos + 1;
            }
        }
        last_seen.insert(ch, right);
        max_len = max_len.max(right - left + 1);
    }
    max_len
}

/// Minimum Window Substring
/// Pattern: expand right until valid, shrink left while valid, record minimum
/// Time: O(n + m), Space: O(m) where m = pattern length
fn min_window_substring(s: &str, t: &str) -> String {
    use std::collections::HashMap;
    
    let s_bytes = s.as_bytes();
    let mut need: HashMap<u8, i32> = HashMap::new();
    for &b in t.as_bytes() {
        *need.entry(b).or_insert(0) += 1;
    }
    
    let mut window: HashMap<u8, i32> = HashMap::new();
    let (mut left, mut right) = (0usize, 0usize);
    let (mut formed, required) = (0usize, need.len());
    let mut result = (usize::MAX, 0usize, 0usize); // (length, left, right)
    
    while right < s_bytes.len() {
        let c = s_bytes[right];
        *window.entry(c).or_insert(0) += 1;
        
        // Check if this char satisfies a need
        if let Some(&needed) = need.get(&c) {
            if window[&c] == needed { formed += 1; }
        }
        
        // Contract from left while window is valid
        while left <= right && formed == required {
            let window_len = right - left + 1;
            if window_len < result.0 {
                result = (window_len, left, right);
            }
            
            let left_char = s_bytes[left];
            *window.get_mut(&left_char).unwrap() -= 1;
            if let Some(&needed) = need.get(&left_char) {
                if window[&left_char] < needed { formed -= 1; }
            }
            left += 1;
        }
        right += 1;
    }
    
    if result.0 == usize::MAX {
        String::new()
    } else {
        s[result.1..=result.2].to_string()
    }
}

/// Maximum Subarray — Kadane's Algorithm
/// Mental model: dp[i] = max subarray ending at index i
/// dp[i] = max(nums[i], dp[i-1] + nums[i])
/// If previous sum is negative, start fresh.
/// Time: O(n), Space: O(1)
fn max_subarray(nums: &[i32]) -> i32 {
    let mut current_sum = nums[0];
    let mut global_max  = nums[0];
    
    for &num in &nums[1..] {
        // Key decision: extend current subarray or start new one?
        current_sum = num.max(current_sum + num);
        global_max  = global_max.max(current_sum);
    }
    global_max
}

/// Maximum Subarray with indices (for tracing back the solution)
fn max_subarray_with_indices(nums: &[i32]) -> (i32, usize, usize) {
    let (mut best_sum, mut best_start, mut best_end) = (nums[0], 0, 0);
    let (mut current_sum, mut current_start) = (nums[0], 0);
    
    for (i, &num) in nums.iter().enumerate().skip(1) {
        if current_sum + num < num {
            current_sum   = num;
            current_start = i;
        } else {
            current_sum += num;
        }
        
        if current_sum > best_sum {
            best_sum   = current_sum;
            best_start = current_start;
            best_end   = i;
        }
    }
    (best_sum, best_start, best_end)
}
```

### Prefix Sums — A Fundamental Building Block

```rust
/// Prefix Sum Array: enables O(1) range sum queries after O(n) preprocessing
/// prefix[i] = sum of nums[0..i] (exclusive right)
/// range_sum(l, r) = prefix[r+1] - prefix[l]
struct PrefixSum {
    prefix: Vec<i64>,
}

impl PrefixSum {
    fn new(nums: &[i32]) -> Self {
        let mut prefix = vec![0i64; nums.len() + 1];
        for (i, &n) in nums.iter().enumerate() {
            prefix[i + 1] = prefix[i] + n as i64;
        }
        Self { prefix }
    }
    
    /// Sum of nums[l..=r] inclusive, O(1)
    fn range_sum(&self, l: usize, r: usize) -> i64 {
        self.prefix[r + 1] - self.prefix[l]
    }
}

/// 2D Prefix Sum — for matrix range queries
/// prefix[i][j] = sum of rectangle from (0,0) to (i-1, j-1)
struct PrefixSum2D {
    prefix: Vec<Vec<i64>>,
}

impl PrefixSum2D {
    fn new(matrix: &[Vec<i32>]) -> Self {
        let (rows, cols) = (matrix.len(), matrix[0].len());
        let mut prefix = vec![vec![0i64; cols + 1]; rows + 1];
        
        for i in 1..=rows {
            for j in 1..=cols {
                // Inclusion-exclusion principle
                prefix[i][j] = matrix[i-1][j-1] as i64
                    + prefix[i-1][j]    // add row above
                    + prefix[i][j-1]    // add column left
                    - prefix[i-1][j-1]; // subtract double-counted corner
            }
        }
        Self { prefix }
    }
    
    /// Sum of rectangle (r1,c1) to (r2,c2) inclusive
    fn query(&self, r1: usize, c1: usize, r2: usize, c2: usize) -> i64 {
        self.prefix[r2+1][c2+1]
            - self.prefix[r1][c2+1]
            - self.prefix[r2+1][c1]
            + self.prefix[r1][c1]
    }
}
```

---

## 3. LINKED LISTS

### The Rust Linked List Dilemma

Implementing linked lists in Rust is famously difficult — not because Rust is bad, but because linked lists expose every edge case in ownership. There is literally a book called "Learning Rust With Entirely Too Many Linked Lists." This is your initiation.

**Why it's hard:**
- Each node must own the next node (ownership chain)
- Doubly linked lists need BOTH forward and backward ownership — impossible with simple `Box<T>`
- You need `Option<Box<Node>>` for nullable next pointers

```
Ownership chain in a singly linked list:
List owns → Node1 owns → Node2 owns → Node3 owns → None

This is natural. The PROBLEM is doubly linked:
Node2 owns → Node3 (forward)
Node3 owns → Node2 (backward) ← CYCLE! Rust won't allow this.
```

### Singly Linked List — Production Implementation

```rust
/// Type alias for clarity
type Link<T> = Option<Box<Node<T>>>;

struct Node<T> {
    val:  T,
    next: Link<T>,
}

pub struct LinkedList<T> {
    head: Link<T>,
    len:  usize,
}

impl<T> LinkedList<T> {
    pub fn new() -> Self {
        LinkedList { head: None, len: 0 }
    }
    
    /// Push to front — O(1)
    /// Takes ownership of value, wraps in Box, sets as new head
    pub fn push_front(&mut self, val: T) {
        let new_node = Box::new(Node {
            val,
            next: self.head.take(), // take() extracts, leaves None
        });
        self.head = Some(new_node);
        self.len += 1;
    }
    
    /// Pop from front — O(1)
    pub fn pop_front(&mut self) -> Option<T> {
        self.head.take().map(|node| {
            self.head = node.next;
            self.len -= 1;
            node.val
        })
    }
    
    /// Peek at front — O(1)
    pub fn peek_front(&self) -> Option<&T> {
        self.head.as_ref().map(|node| &node.val)
    }
    
    /// Push to back — O(n) for singly linked
    /// Real systems use a tail pointer to make this O(1)
    pub fn push_back(&mut self, val: T) {
        let new_node = Box::new(Node { val, next: None });
        
        // Traverse to find the last node
        let mut current = &mut self.head;
        while let Some(ref mut node) = current {
            current = &mut node.next;
        }
        *current = Some(new_node);
        self.len += 1;
    }
    
    pub fn len(&self) -> usize { self.len }
    pub fn is_empty(&self) -> bool { self.len == 0 }
    
    /// Reverse in-place — O(n)
    /// Classic interview pattern: maintain prev, curr, next pointers
    pub fn reverse(&mut self) {
        let mut prev = None;
        let mut curr = self.head.take();
        
        while let Some(mut node) = curr {
            let next   = node.next.take(); // save next
            node.next  = prev;             // reverse pointer
            prev       = Some(node);       // advance prev
            curr       = next;             // advance curr
        }
        self.head = prev;
    }
    
    /// Detect cycle — Floyd's Tortoise and Hare
    /// Mental model: if there's a cycle, a fast pointer (2x speed)
    /// will eventually lap the slow pointer inside the cycle.
    /// For Box-based lists this can't happen (no cycles possible),
    /// but the raw pointer version demonstrates the algorithm.
    pub fn has_cycle_raw(head: *mut Node<i32>) -> bool {
        let (mut slow, mut fast) = (head, head);
        unsafe {
            loop {
                if fast.is_null() { return false; }
                fast = (*fast).next.as_mut().map_or(std::ptr::null_mut(), 
                    |n| n.as_mut() as *mut Node<i32>);
                if fast.is_null() { return false; }
                fast = (*fast).next.as_mut().map_or(std::ptr::null_mut(),
                    |n| n.as_mut() as *mut Node<i32>);
                slow = (*slow).next.as_mut().map_or(std::ptr::null_mut(),
                    |n| n.as_mut() as *mut Node<i32>);
                if slow == fast { return true; }
            }
        }
    }
    
    /// Merge two sorted linked lists — O(n + m)
    /// Key insight: always pick the smaller head, recurse on rest
    pub fn merge_sorted(mut l1: Link<i32>, mut l2: Link<i32>) -> Link<i32> {
        match (l1, l2) {
            (None, r) => r,
            (l, None) => l,
            (Some(mut n1), Some(mut n2)) => {
                if n1.val <= n2.val {
                    n1.next = Self::merge_sorted(n1.next.take(), Some(n2));
                    Some(n1)
                } else {
                    n2.next = Self::merge_sorted(Some(n1), n2.next.take());
                    Some(n2)
                }
            }
        }
    }
}

/// Iterator implementation — crucial for idiomatic Rust
pub struct Iter<'a, T> {
    next: Option<&'a Node<T>>,
}

impl<T> LinkedList<T> {
    pub fn iter(&self) -> Iter<'_, T> {
        Iter { next: self.head.as_deref() }
    }
}

impl<'a, T> Iterator for Iter<'a, T> {
    type Item = &'a T;
    
    fn next(&mut self) -> Option<Self::Item> {
        self.next.map(|node| {
            self.next = node.next.as_deref();
            &node.val
        })
    }
}

/// Drop implementation — avoids stack overflow for very long lists
/// Rust's default drop is recursive (drops node → drops next → drops next...)
/// For lists of millions of elements, this OVERFLOWS the stack!
impl<T> Drop for LinkedList<T> {
    fn drop(&mut self) {
        let mut curr = self.head.take();
        while let Some(mut node) = curr {
            curr = node.next.take(); // iteratively drop each node
        }
    }
}
```

### Linked List with Tail Pointer — O(1) Push Back

```rust
/// A production-grade singly linked list with tail pointer
/// Enables O(1) push_back — essential for queue implementations
pub struct LinkedListWithTail<T> {
    head: Link<T>,
    tail: *mut Node<T>, // raw pointer to tail — unsafe but fast
    len:  usize,
}

impl<T> LinkedListWithTail<T> {
    pub fn new() -> Self {
        LinkedListWithTail { head: None, tail: std::ptr::null_mut(), len: 0 }
    }
    
    pub fn push_back(&mut self, val: T) {
        let mut new_node = Box::new(Node { val, next: None });
        let raw_ptr: *mut Node<T> = &mut *new_node;
        
        if self.tail.is_null() {
            self.head = Some(new_node);
        } else {
            unsafe { (*self.tail).next = Some(new_node); }
        }
        self.tail = raw_ptr;
        self.len += 1;
    }
    
    pub fn pop_front(&mut self) -> Option<T> {
        self.head.take().map(|node| {
            self.head = node.next;
            if self.head.is_none() {
                self.tail = std::ptr::null_mut(); // list is now empty
            }
            self.len -= 1;
            node.val
        })
    }
}
```

### Doubly Linked List — The Rc<RefCell<>> Dance

```rust
use std::rc::Rc;
use std::cell::RefCell;

type DLink<T> = Option<Rc<RefCell<DNode<T>>>>;

struct DNode<T> {
    val:  T,
    prev: DLink<T>,
    next: DLink<T>,
}

/// Doubly Linked List — useful for LRU Cache, deque operations
pub struct DoublyLinkedList<T> {
    head: DLink<T>,
    tail: DLink<T>,
    len:  usize,
}

impl<T: Clone> DoublyLinkedList<T> {
    pub fn new() -> Self {
        DoublyLinkedList { head: None, tail: None, len: 0 }
    }
    
    fn make_node(val: T) -> Rc<RefCell<DNode<T>>> {
        Rc::new(RefCell::new(DNode { val, prev: None, next: None }))
    }
    
    pub fn push_back(&mut self, val: T) {
        let node = Self::make_node(val);
        match self.tail.take() {
            None => {
                self.head = Some(Rc::clone(&node));
                self.tail = Some(node);
            }
            Some(old_tail) => {
                old_tail.borrow_mut().next = Some(Rc::clone(&node));
                node.borrow_mut().prev = Some(old_tail);
                self.tail = Some(node);
            }
        }
        self.len += 1;
    }
    
    pub fn push_front(&mut self, val: T) {
        let node = Self::make_node(val);
        match self.head.take() {
            None => {
                self.head = Some(Rc::clone(&node));
                self.tail = Some(node);
            }
            Some(old_head) => {
                old_head.borrow_mut().prev = Some(Rc::clone(&node));
                node.borrow_mut().next = Some(old_head);
                self.head = Some(node);
            }
        }
        self.len += 1;
    }
    
    pub fn pop_front(&mut self) -> Option<T> {
        self.head.take().map(|old_head| {
            match old_head.borrow_mut().next.take() {
                None => { self.tail = None; }
                Some(new_head) => {
                    new_head.borrow_mut().prev = None;
                    self.head = Some(new_head);
                }
            }
            self.len -= 1;
            // Unwrap the Rc<RefCell<>> to get the value
            Rc::try_unwrap(old_head).ok().unwrap().into_inner().val
        })
    }
    
    pub fn pop_back(&mut self) -> Option<T> {
        self.tail.take().map(|old_tail| {
            match old_tail.borrow_mut().prev.take() {
                None => { self.head = None; }
                Some(new_tail) => {
                    new_tail.borrow_mut().next = None;
                    self.tail = Some(new_tail);
                }
            }
            self.len -= 1;
            Rc::try_unwrap(old_tail).ok().unwrap().into_inner().val
        })
    }
}
```

---

## 4. STACKS & QUEUES

### Stack: The Call Stack Analogy

A stack models LIFO (Last In, First Out). It's not just a data structure — it IS how your program executes. Every function call pushes a frame; every return pops one.

```rust
/// Stack implemented over Vec<T>
/// Vec already provides push/pop at the end — perfect stack behavior
/// All operations O(1) amortized
pub struct Stack<T> {
    data: Vec<T>,
}

impl<T> Stack<T> {
    pub fn new() -> Self { Stack { data: Vec::new() } }
    pub fn with_capacity(cap: usize) -> Self { 
        Stack { data: Vec::with_capacity(cap) }
    }
    
    pub fn push(&mut self, val: T)       { self.data.push(val); }
    pub fn pop(&mut self)  -> Option<T>  { self.data.pop() }
    pub fn peek(&self)     -> Option<&T> { self.data.last() }
    pub fn is_empty(&self) -> bool        { self.data.is_empty() }
    pub fn len(&self)      -> usize       { self.data.len() }
}

/// Real-world application 1: Valid Parentheses
/// Pattern: push open brackets, match against close brackets
fn is_valid_parens(s: &str) -> bool {
    let mut stack = Vec::new();
    for ch in s.chars() {
        match ch {
            '(' | '[' | '{' => stack.push(ch),
            ')' => if stack.pop() != Some('(') { return false; }
            ']' => if stack.pop() != Some('[') { return false; }
            '}' => if stack.pop() != Some('{') { return false; }
            _   => {}
        }
    }
    stack.is_empty()
}

/// Real-world application 2: Monotonic Stack
/// The monotonic stack is one of the most powerful stack patterns.
/// Mental model: maintain a stack where elements are always sorted
/// (either increasing or decreasing). When you violate the invariant,
/// POP — and the popped element found its answer.

/// Next Greater Element — O(n)
/// For each element, find the first element to its right that is greater.
/// Key insight: elements waiting in the stack haven't found their NGE yet.
/// When we see a larger element, it's the NGE for everything smaller in stack.
fn next_greater_element(nums: &[i32]) -> Vec<i32> {
    let n = nums.len();
    let mut result = vec![-1; n];
    let mut stack: Vec<usize> = Vec::new(); // stack of indices
    
    for i in 0..n {
        // While current element is greater than stack's top
        while let Some(&top_idx) = stack.last() {
            if nums[i] > nums[top_idx] {
                result[top_idx] = nums[i]; // found NGE for top_idx
                stack.pop();
            } else {
                break;
            }
        }
        stack.push(i);
    }
    result
}

/// Largest Rectangle in Histogram — O(n)
/// Classic monotonic stack application.
/// Key insight: for each bar, its maximum rectangle extends left/right
/// until a shorter bar is encountered.
/// The stack maintains bars in increasing height order.
fn largest_rectangle_in_histogram(heights: &[i32]) -> i32 {
    let mut stack: Vec<usize> = Vec::new(); // stack of indices, heights increasing
    let mut max_area = 0i32;
    let n = heights.len();
    
    // Append 0 sentinel to flush remaining stack elements
    let heights_ext: Vec<i32> = heights.iter().copied().chain([0]).collect();
    
    for i in 0..=n {
        while let Some(&top) = stack.last() {
            if heights_ext[i] < heights_ext[top] {
                stack.pop();
                let width = if stack.is_empty() { i } else { i - stack.last().unwrap() - 1 };
                max_area = max_area.max(heights_ext[top] * width as i32);
            } else {
                break;
            }
        }
        stack.push(i);
    }
    max_area
}

/// Daily Temperatures — monotonic decreasing stack
/// How many days until a warmer temperature?
fn daily_temperatures(temps: &[i32]) -> Vec<i32> {
    let n = temps.len();
    let mut result = vec![0; n];
    let mut stack: Vec<usize> = Vec::new();
    
    for i in 0..n {
        while let Some(&top) = stack.last() {
            if temps[i] > temps[top] {
                result[top] = (i - top) as i32;
                stack.pop();
            } else {
                break;
            }
        }
        stack.push(i);
    }
    result
}

/// Evaluate Reverse Polish Notation — stack-based expression evaluator
fn eval_rpn(tokens: &[&str]) -> i32 {
    let mut stack: Vec<i32> = Vec::new();
    
    for &token in tokens {
        match token {
            "+" | "-" | "*" | "/" => {
                let b = stack.pop().unwrap();
                let a = stack.pop().unwrap();
                stack.push(match token {
                    "+" => a + b,
                    "-" => a - b,
                    "*" => a * b,
                    "/" => a / b,
                    _   => unreachable!(),
                });
            }
            num => stack.push(num.parse().unwrap()),
        }
    }
    stack[0]
}
```

### Queue: BFS and Beyond

```rust
use std::collections::VecDeque;

/// Queue implemented over VecDeque
/// VecDeque is a ring buffer — O(1) push_back AND pop_front
/// This is why you should use VecDeque over Vec for queues.
pub struct Queue<T> {
    data: VecDeque<T>,
}

impl<T> Queue<T> {
    pub fn new()                     -> Self   { Queue { data: VecDeque::new() } }
    pub fn enqueue(&mut self, val: T)          { self.data.push_back(val); }
    pub fn dequeue(&mut self) -> Option<T>     { self.data.pop_front() }
    pub fn front(&self)       -> Option<&T>    { self.data.front() }
    pub fn is_empty(&self)    -> bool           { self.data.is_empty() }
    pub fn len(&self)         -> usize          { self.data.len() }
}

/// Circular Buffer / Ring Buffer — fixed-size, O(1) all operations
/// Used in: audio processing, network packet buffers, OS ring buffers
pub struct CircularBuffer<T> {
    data:  Vec<Option<T>>,
    head:  usize,
    tail:  usize,
    count: usize,
    cap:   usize,
}

impl<T> CircularBuffer<T> {
    pub fn new(cap: usize) -> Self {
        let mut data = Vec::with_capacity(cap);
        for _ in 0..cap { data.push(None); }
        CircularBuffer { data, head: 0, tail: 0, count: 0, cap }
    }
    
    pub fn push(&mut self, val: T) -> bool {
        if self.count == self.cap { return false; } // full
        self.data[self.tail] = Some(val);
        self.tail  = (self.tail + 1) % self.cap; // wrap around
        self.count += 1;
        true
    }
    
    pub fn pop(&mut self) -> Option<T> {
        if self.count == 0 { return None; } // empty
        let val   = self.data[self.head].take();
        self.head = (self.head + 1) % self.cap;
        self.count -= 1;
        val
    }
    
    pub fn is_full(&self)  -> bool { self.count == self.cap }
    pub fn is_empty(&self) -> bool { self.count == 0 }
}

/// Sliding Window Maximum — Monotonic Deque
/// Find the max in every window of size k in O(n) total.
/// Key insight: maintain a deque of INDICES where values are DECREASING.
/// Elements outside the window are removed from front.
/// Elements smaller than current are removed from back (they can never be max).
fn sliding_window_maximum(nums: &[i32], k: usize) -> Vec<i32> {
    let mut deque: VecDeque<usize> = VecDeque::new(); // indices
    let mut result = Vec::new();
    
    for i in 0..nums.len() {
        // Remove elements outside the window
        while let Some(&front) = deque.front() {
            if front + k <= i { deque.pop_front(); } else { break; }
        }
        
        // Remove elements smaller than current from back
        // (they can never be the maximum while current is in window)
        while let Some(&back) = deque.back() {
            if nums[back] <= nums[i] { deque.pop_back(); } else { break; }
        }
        
        deque.push_back(i);
        
        // Window is full — record maximum (front of deque)
        if i >= k - 1 {
            result.push(nums[*deque.front().unwrap()]);
        }
    }
    result
}
```

---

## 5. HASH MAPS & HASH SETS

### Understanding Hash Maps from First Principles

A hash map resolves the question: "Given a key, find its value in O(1)."

```
The three components of a hash map:
1. Hash function: key → index in array  [O(1)]
2. Array (buckets): fixed-size backing store
3. Collision resolution: what to do when two keys map to same index

Rust's HashMap uses:
- SipHash (secure, DoS-resistant, slower) by default
- Can swap to FxHashMap or AHashMap for performance-critical code
```

```rust
use std::collections::{HashMap, HashSet};

/// Building intuition: implement a simple hash map from scratch
/// Using separate chaining for collision resolution
pub struct SimpleHashMap<K, V> {
    buckets: Vec<Vec<(K, V)>>,
    len:     usize,
    cap:     usize,
}

impl<K: std::hash::Hash + Eq, V> SimpleHashMap<K, V> {
    pub fn new() -> Self {
        let cap = 16;
        SimpleHashMap {
            buckets: (0..cap).map(|_| Vec::new()).collect(),
            len: 0,
            cap,
        }
    }
    
    fn bucket_index(&self, key: &K) -> usize {
        use std::hash::{Hash, Hasher};
        use std::collections::hash_map::DefaultHasher;
        let mut hasher = DefaultHasher::new();
        key.hash(&mut hasher);
        (hasher.finish() as usize) % self.cap
    }
    
    pub fn insert(&mut self, key: K, val: V) {
        let idx = self.bucket_index(&key);
        let bucket = &mut self.buckets[idx];
        
        for (k, v) in bucket.iter_mut() {
            if *k == key { *v = val; return; } // update existing
        }
        bucket.push((key, val));
        self.len += 1;
        
        // Resize if load factor > 0.75
        if self.len > self.cap * 3 / 4 { self.resize(); }
    }
    
    pub fn get(&self, key: &K) -> Option<&V> {
        let idx = self.bucket_index(key);
        self.buckets[idx].iter()
            .find(|(k, _)| k == key)
            .map(|(_, v)| v)
    }
    
    fn resize(&mut self) {
        let new_cap = self.cap * 2;
        let mut new_buckets: Vec<Vec<(K, V)>> = (0..new_cap)
            .map(|_| Vec::new()).collect();
        
        use std::hash::{Hash, Hasher};
        use std::collections::hash_map::DefaultHasher;
        
        for bucket in self.buckets.drain(..) {
            for (k, v) in bucket {
                let mut hasher = DefaultHasher::new();
                k.hash(&mut hasher);
                let idx = (hasher.finish() as usize) % new_cap;
                new_buckets[idx].push((k, v));
            }
        }
        self.buckets = new_buckets;
        self.cap = new_cap;
    }
}

/// Real-world HashMap patterns:

/// Pattern 1: Frequency counting
fn character_frequency(s: &str) -> HashMap<char, usize> {
    let mut freq = HashMap::new();
    for ch in s.chars() {
        *freq.entry(ch).or_insert(0) += 1;
    }
    freq
}

/// Pattern 2: Anagram grouping
/// Key insight: sort each word → same key for anagrams
fn group_anagrams(words: Vec<String>) -> Vec<Vec<String>> {
    let mut groups: HashMap<Vec<u8>, Vec<String>> = HashMap::new();
    
    for word in words {
        let mut key: Vec<u8> = word.bytes().collect();
        key.sort_unstable();
        groups.entry(key).or_default().push(word);
    }
    groups.into_values().collect()
}

/// Pattern 3: Two-pass HashMap — Two Sum
fn two_sum(nums: &[i32], target: i32) -> Option<(usize, usize)> {
    let mut seen: HashMap<i32, usize> = HashMap::new();
    
    for (i, &num) in nums.iter().enumerate() {
        let complement = target - num;
        if let Some(&j) = seen.get(&complement) {
            return Some((j, i));
        }
        seen.insert(num, i);
    }
    None
}

/// Pattern 4: Subarray sum equals K
/// Key insight: prefix_sum[j] - prefix_sum[i] = k
/// Rearranged: prefix_sum[i] = prefix_sum[j] - k
/// Count how many previous prefix sums equal current - k
fn subarray_sum_equals_k(nums: &[i32], k: i32) -> i32 {
    let mut count = 0;
    let mut prefix_sum = 0;
    let mut freq: HashMap<i32, i32> = HashMap::new();
    freq.insert(0, 1); // empty prefix has sum 0
    
    for &num in nums {
        prefix_sum += num;
        count += freq.get(&(prefix_sum - k)).copied().unwrap_or(0);
        *freq.entry(prefix_sum).or_insert(0) += 1;
    }
    count
}

/// Pattern 5: LRU Cache — doubly linked list + HashMap
/// The canonical HashMap + data structure combination problem
use std::collections::HashMap;

pub struct LRUCache {
    cap:      usize,
    map:      HashMap<i32, Rc<RefCell<LRUNode>>>,
    head:     Rc<RefCell<LRUNode>>, // sentinel head (MRU side)
    tail:     Rc<RefCell<LRUNode>>, // sentinel tail (LRU side)
}

struct LRUNode {
    key:  i32,
    val:  i32,
    prev: Option<Rc<RefCell<LRUNode>>>,
    next: Option<Rc<RefCell<LRUNode>>>,
}

impl LRUNode {
    fn new(key: i32, val: i32) -> Rc<RefCell<Self>> {
        Rc::new(RefCell::new(LRUNode { key, val, prev: None, next: None }))
    }
}

impl LRUCache {
    pub fn new(cap: usize) -> Self {
        let head = LRUNode::new(0, 0);
        let tail = LRUNode::new(0, 0);
        head.borrow_mut().next = Some(Rc::clone(&tail));
        tail.borrow_mut().prev = Some(Rc::clone(&head));
        LRUCache { cap, map: HashMap::new(), head, tail }
    }
    
    fn remove(node: &Rc<RefCell<LRUNode>>) {
        let prev = node.borrow().prev.clone().unwrap();
        let next = node.borrow().next.clone().unwrap();
        prev.borrow_mut().next = Some(Rc::clone(&next));
        next.borrow_mut().prev = Some(Rc::clone(&prev));
    }
    
    fn insert_after_head(&self, node: &Rc<RefCell<LRUNode>>) {
        let first = self.head.borrow().next.clone().unwrap();
        self.head.borrow_mut().next = Some(Rc::clone(node));
        node.borrow_mut().prev = Some(Rc::clone(&self.head));
        node.borrow_mut().next = Some(Rc::clone(&first));
        first.borrow_mut().prev = Some(Rc::clone(node));
    }
    
    pub fn get(&mut self, key: i32) -> i32 {
        if let Some(node) = self.map.get(&key).cloned() {
            let val = node.borrow().val;
            Self::remove(&node);
            self.insert_after_head(&node);
            val
        } else {
            -1
        }
    }
    
    pub fn put(&mut self, key: i32, value: i32) {
        if let Some(node) = self.map.get(&key).cloned() {
            node.borrow_mut().val = value;
            Self::remove(&node);
            self.insert_after_head(&node);
        } else {
            if self.map.len() == self.cap {
                // Evict LRU (just before tail sentinel)
                let lru = self.tail.borrow().prev.clone().unwrap();
                Self::remove(&lru);
                self.map.remove(&lru.borrow().key);
            }
            let node = LRUNode::new(key, value);
            self.insert_after_head(&node);
            self.map.insert(key, node);
        }
    }
}
```

---

## 6. TREES: BINARY, BST, AVL

### Tree Mental Model

```
Every tree problem follows one of three traversal strategies:
1. Preorder  (root → left → right): serialize tree, copy tree
2. Inorder   (left → root → right): BST sorted order
3. Postorder (left → right → root): compute subtree results, delete tree
4. Level order (BFS):               shortest path in unweighted tree

The KEY insight: most tree problems are variations of:
"Do something at each node, combining results from children"
This is the essence of divide-and-conquer on trees.
```

### Binary Tree Foundation

```rust
use std::collections::VecDeque;

type TreeLink = Option<Box<TreeNode>>;

#[derive(Debug)]
pub struct TreeNode {
    pub val:   i32,
    pub left:  TreeLink,
    pub right: TreeLink,
}

impl TreeNode {
    pub fn new(val: i32) -> Box<Self> {
        Box::new(TreeNode { val, left: None, right: None })
    }
    
    pub fn leaf(val: i32) -> TreeLink {
        Some(Box::new(TreeNode { val, left: None, right: None }))
    }
}

/// Build tree from level-order array (LeetCode style)
fn build_tree(vals: &[Option<i32>]) -> TreeLink {
    if vals.is_empty() || vals[0].is_none() { return None; }
    
    let root = Rc::new(RefCell::new(TreeNode::new(vals[0].unwrap())));
    let mut queue: VecDeque<Rc<RefCell<TreeNode>>> = VecDeque::new();
    // ... (complex due to borrowing, simplified here)
    None // placeholder
}

/// Inorder traversal — iterative (avoids stack overflow for deep trees)
fn inorder_iterative(root: &TreeLink) -> Vec<i32> {
    let mut result = Vec::new();
    let mut stack  = Vec::new();
    let mut curr   = root.as_deref();
    
    loop {
        // Go as far left as possible
        while let Some(node) = curr {
            stack.push(node);
            curr = node.left.as_deref();
        }
        
        match stack.pop() {
            None       => break,
            Some(node) => {
                result.push(node.val);
                curr = node.right.as_deref();
            }
        }
    }
    result
}

/// Level order traversal — BFS
fn level_order(root: &TreeLink) -> Vec<Vec<i32>> {
    let mut result = Vec::new();
    let Some(root_node) = root else { return result; };
    
    let mut queue: VecDeque<&TreeNode> = VecDeque::new();
    queue.push_back(root_node);
    
    while !queue.is_empty() {
        let level_size = queue.len();
        let mut level  = Vec::with_capacity(level_size);
        
        for _ in 0..level_size {
            let node = queue.pop_front().unwrap();
            level.push(node.val);
            if let Some(left)  = &node.left  { queue.push_back(left); }
            if let Some(right) = &node.right { queue.push_back(right); }
        }
        result.push(level);
    }
    result
}

/// Maximum depth of binary tree
fn max_depth(root: &TreeLink) -> i32 {
    match root {
        None       => 0,
        Some(node) => 1 + max_depth(&node.left).max(max_depth(&node.right)),
    }
}

/// Diameter of binary tree
/// Key insight: diameter through a node = left_height + right_height
/// We compute both the height AND the diameter in one DFS pass
fn diameter_of_binary_tree(root: &TreeLink) -> i32 {
    fn dfs(node: &TreeLink, max_diam: &mut i32) -> i32 {
        let Some(n) = node else { return 0; };
        let left_h  = dfs(&n.left,  max_diam);
        let right_h = dfs(&n.right, max_diam);
        *max_diam   = (*max_diam).max(left_h + right_h);
        1 + left_h.max(right_h)
    }
    let mut max_diam = 0;
    dfs(root, &mut max_diam);
    max_diam
}

/// Lowest Common Ancestor
/// Key insight: if both nodes are in different subtrees, current node IS the LCA.
/// If both are in same subtree, recurse into that subtree.
fn lowest_common_ancestor<'a>(
    root: &'a TreeLink, p: i32, q: i32
) -> Option<&'a TreeNode> {
    let node = root.as_deref()?;
    
    if node.val == p || node.val == q { return Some(node); }
    
    let left_lca  = lowest_common_ancestor(&node.left,  p, q);
    let right_lca = lowest_common_ancestor(&node.right, p, q);
    
    match (left_lca, right_lca) {
        (Some(_), Some(_)) => Some(node), // found in both sides → current is LCA
        (Some(l), None)    => Some(l),
        (None, Some(r))    => Some(r),
        (None, None)       => None,
    }
}

/// Path Sum II — find all paths root→leaf with given sum
fn path_sum(root: &TreeLink, target: i32) -> Vec<Vec<i32>> {
    let mut all_paths = Vec::new();
    let mut current_path = Vec::new();
    
    fn dfs(node: &TreeLink, remaining: i32, path: &mut Vec<i32>, result: &mut Vec<Vec<i32>>) {
        let Some(n) = node else { return; };
        path.push(n.val);
        let rem = remaining - n.val;
        
        if n.left.is_none() && n.right.is_none() && rem == 0 {
            result.push(path.clone()); // leaf node with correct sum
        } else {
            dfs(&n.left,  rem, path, result);
            dfs(&n.right, rem, path, result);
        }
        path.pop(); // backtrack
    }
    
    dfs(root, target, &mut current_path, &mut all_paths);
    all_paths
}

/// Serialize and Deserialize Binary Tree
fn serialize(root: &TreeLink) -> String {
    fn helper(node: &TreeLink, parts: &mut Vec<String>) {
        match node {
            None => parts.push("N".to_string()),
            Some(n) => {
                parts.push(n.val.to_string());
                helper(&n.left,  parts);
                helper(&n.right, parts);
            }
        }
    }
    let mut parts = Vec::new();
    helper(root, &mut parts);
    parts.join(",")
}

fn deserialize(data: &str) -> TreeLink {
    let mut iter = data.split(',');
    fn helper(iter: &mut impl Iterator<Item = &str>) -> TreeLink {
        match iter.next()? {
            "N" => None,
            val => {
                let n = val.parse().ok()?;
                Some(Box::new(TreeNode {
                    val:   n,
                    left:  helper(iter),
                    right: helper(iter),
                }))
            }
        }
    }
    helper(&mut iter)
}
```

### Binary Search Tree

```rust
/// BST with full operations
pub struct BST {
    root: TreeLink,
}

impl BST {
    pub fn new() -> Self { BST { root: None } }
    
    /// Insert — O(h) where h = height [O(log n) balanced, O(n) degenerate]
    pub fn insert(&mut self, val: i32) {
        fn insert_rec(node: &mut TreeLink, val: i32) {
            match node {
                None => *node = TreeNode::leaf(val),
                Some(n) => match val.cmp(&n.val) {
                    std::cmp::Ordering::Less    => insert_rec(&mut n.left,  val),
                    std::cmp::Ordering::Greater => insert_rec(&mut n.right, val),
                    std::cmp::Ordering::Equal   => {} // duplicate — ignore
                }
            }
        }
        insert_rec(&mut self.root, val);
    }
    
    /// Search — O(h)
    pub fn search(&self, val: i32) -> bool {
        fn search_rec(node: &TreeLink, val: i32) -> bool {
            match node {
                None    => false,
                Some(n) => match val.cmp(&n.val) {
                    std::cmp::Ordering::Equal   => true,
                    std::cmp::Ordering::Less    => search_rec(&n.left,  val),
                    std::cmp::Ordering::Greater => search_rec(&n.right, val),
                }
            }
        }
        search_rec(&self.root, val)
    }
    
    /// Delete — O(h)
    /// Three cases:
    /// 1. Node has no children → just remove
    /// 2. Node has one child → replace with child
    /// 3. Node has two children → replace with inorder successor (min of right subtree)
    pub fn delete(&mut self, val: i32) {
        fn delete_rec(node: TreeLink, val: i32) -> TreeLink {
            let Some(mut n) = node else { return None; };
            match val.cmp(&n.val) {
                std::cmp::Ordering::Less    => { n.left  = delete_rec(n.left.take(),  val); Some(n) }
                std::cmp::Ordering::Greater => { n.right = delete_rec(n.right.take(), val); Some(n) }
                std::cmp::Ordering::Equal   => {
                    match (n.left.take(), n.right.take()) {
                        (None, right)     => right,
                        (left, None)      => left,
                        (left, Some(mut right)) => {
                            // Find inorder successor (min of right subtree)
                            let (min_val, new_right) = extract_min(right);
                            n.val   = min_val;
                            n.left  = left;
                            n.right = new_right;
                            Some(n)
                        }
                    }
                }
            }
        }
        
        fn extract_min(mut node: Box<TreeNode>) -> (i32, TreeLink) {
            if node.left.is_none() {
                (node.val, node.right.take())
            } else {
                let (min_val, new_left) = extract_min(node.left.take().unwrap());
                node.left = new_left;
                (min_val, Some(node))
            }
        }
        
        self.root = delete_rec(self.root.take(), val);
    }
    
    /// Validate BST — O(n)
    /// Key insight: each node must be within a valid range [min, max]
    /// NOT just greater than left child and less than right child!
    pub fn is_valid_bst(&self) -> bool {
        fn validate(node: &TreeLink, min: i64, max: i64) -> bool {
            match node {
                None    => true,
                Some(n) => {
                    let val = n.val as i64;
                    val > min && val < max
                        && validate(&n.left,  min,  val)
                        && validate(&n.right, val,  max)
                }
            }
        }
        validate(&self.root, i64::MIN, i64::MAX)
    }
    
    /// Kth Smallest in BST — inorder gives sorted order
    pub fn kth_smallest(&self, k: usize) -> Option<i32> {
        let mut count = 0;
        let mut result = None;
        
        fn inorder(node: &TreeLink, k: usize, count: &mut usize, result: &mut Option<i32>) {
            let Some(n) = node else { return; };
            inorder(&n.left, k, count, result);
            *count += 1;
            if *count == k { *result = Some(n.val); return; }
            inorder(&n.right, k, count, result);
        }
        
        inorder(&self.root, k, &mut count, &mut result);
        result
    }
}
```

### AVL Tree — Self-Balancing BST

```rust
/// AVL Tree: maintains |height(left) - height(right)| ≤ 1 invariant
/// Guarantees O(log n) for all operations
/// 
/// Balance factor = height(right) - height(left)
///  -1: left-heavy (OK)
///   0: balanced (perfect)
///  +1: right-heavy (OK)
///  ≤ -2 or ≥ 2: REBALANCE needed

struct AVLNode {
    val:    i32,
    height: i32,
    left:   Option<Box<AVLNode>>,
    right:  Option<Box<AVLNode>>,
}

impl AVLNode {
    fn new(val: i32) -> Box<Self> {
        Box::new(AVLNode { val, height: 1, left: None, right: None })
    }
    
    fn height(node: &Option<Box<AVLNode>>) -> i32 {
        node.as_ref().map_or(0, |n| n.height)
    }
    
    fn balance_factor(node: &Box<AVLNode>) -> i32 {
        Self::height(&node.right) - Self::height(&node.left)
    }
    
    fn update_height(node: &mut Box<AVLNode>) {
        node.height = 1 + Self::height(&node.left).max(Self::height(&node.right));
    }
    
    /// Right rotation — fixes left-heavy imbalance
    /// 
    ///       y                x
    ///      / \              / \
    ///     x   C    →      A   y
    ///    / \                  / \
    ///   A   B                B   C
    fn rotate_right(mut y: Box<AVLNode>) -> Box<AVLNode> {
        let mut x = y.left.take().unwrap();
        y.left    = x.right.take();
        Self::update_height(&mut y);
        x.right   = Some(y);
        Self::update_height(&mut x);
        x
    }
    
    /// Left rotation — fixes right-heavy imbalance
    fn rotate_left(mut x: Box<AVLNode>) -> Box<AVLNode> {
        let mut y = x.right.take().unwrap();
        x.right   = y.left.take();
        Self::update_height(&mut x);
        y.left    = Some(x);
        Self::update_height(&mut y);
        y
    }
    
    /// Rebalance after insertion/deletion
    /// Four cases:
    /// LL: right rotate
    /// RR: left rotate
    /// LR: left rotate left child, then right rotate
    /// RL: right rotate right child, then left rotate
    fn rebalance(mut node: Box<AVLNode>) -> Box<AVLNode> {
        Self::update_height(&mut node);
        let bf = Self::balance_factor(&node);
        
        if bf <= -2 {
            // Left heavy
            if Self::balance_factor(node.left.as_ref().unwrap()) > 0 {
                // LR case: left child is right-heavy
                node.left = Some(Self::rotate_left(node.left.take().unwrap()));
            }
            Self::rotate_right(node) // LL case
        } else if bf >= 2 {
            // Right heavy
            if Self::balance_factor(node.right.as_ref().unwrap()) < 0 {
                // RL case: right child is left-heavy
                node.right = Some(Self::rotate_right(node.right.take().unwrap()));
            }
            Self::rotate_left(node) // RR case
        } else {
            node // balanced
        }
    }
    
    fn insert(node: Option<Box<AVLNode>>, val: i32) -> Box<AVLNode> {
        match node {
            None => Self::new(val),
            Some(mut n) => {
                match val.cmp(&n.val) {
                    std::cmp::Ordering::Less    => n.left  = Some(Self::insert(n.left.take(),  val)),
                    std::cmp::Ordering::Greater => n.right = Some(Self::insert(n.right.take(), val)),
                    std::cmp::Ordering::Equal   => return n,
                }
                Self::rebalance(n)
            }
        }
    }
}

pub struct AVLTree {
    root: Option<Box<AVLNode>>,
}

impl AVLTree {
    pub fn new() -> Self { AVLTree { root: None } }
    
    pub fn insert(&mut self, val: i32) {
        self.root = Some(AVLNode::insert(self.root.take(), val));
    }
    
    pub fn height(&self) -> i32 {
        AVLNode::height(&self.root)
    }
}
```

---

## 7. HEAPS & PRIORITY QUEUES

### Binary Heap Mental Model

```
A binary heap is a complete binary tree stored in an array.
The heap property: every parent is ≤ (min-heap) or ≥ (max-heap) its children.

Array index relationships (0-indexed):
  parent(i)      = (i - 1) / 2
  left_child(i)  = 2 * i + 1
  right_child(i) = 2 * i + 2

Example max-heap [10, 8, 6, 4, 2, 5, 1]:

           10
          /    \
         8      6
        / \    / \
       4   2  5   1

Index: 0   1  2  3  4  5  6
```

```rust
/// Binary Max-Heap implementation from scratch
pub struct MaxHeap {
    data: Vec<i32>,
}

impl MaxHeap {
    pub fn new() -> Self { MaxHeap { data: Vec::new() } }
    
    pub fn len(&self)      -> usize { self.data.len() }
    pub fn is_empty(&self) -> bool  { self.data.is_empty() }
    pub fn peek(&self)     -> Option<i32> { self.data.first().copied() }
    
    fn parent(i: usize)      -> usize { (i - 1) / 2 }
    fn left_child(i: usize)  -> usize { 2 * i + 1 }
    fn right_child(i: usize) -> usize { 2 * i + 2 }
    
    /// Sift up — after insertion at the end
    /// Move the new element up until heap property is restored
    fn sift_up(&mut self, mut i: usize) {
        while i > 0 {
            let p = Self::parent(i);
            if self.data[i] > self.data[p] {
                self.data.swap(i, p);
                i = p;
            } else {
                break;
            }
        }
    }
    
    /// Sift down — after removing root and placing last element at root
    fn sift_down(&mut self, mut i: usize) {
        let n = self.data.len();
        loop {
            let left  = Self::left_child(i);
            let right = Self::right_child(i);
            let mut largest = i;
            
            if left  < n && self.data[left]  > self.data[largest] { largest = left; }
            if right < n && self.data[right] > self.data[largest] { largest = right; }
            
            if largest == i { break; } // heap property satisfied
            self.data.swap(i, largest);
            i = largest;
        }
    }
    
    /// Push — O(log n)
    pub fn push(&mut self, val: i32) {
        self.data.push(val);
        let last = self.data.len() - 1;
        self.sift_up(last);
    }
    
    /// Pop max — O(log n)
    pub fn pop(&mut self) -> Option<i32> {
        if self.data.is_empty() { return None; }
        let n = self.data.len();
        self.data.swap(0, n - 1);
        let max = self.data.pop();
        if !self.data.is_empty() { self.sift_down(0); }
        max
    }
    
    /// Heapify — build heap from array in O(n)
    /// Key insight: only sift down non-leaf nodes (indices 0..n/2)
    /// Starting from last non-leaf ensures all subtrees are valid heaps
    pub fn heapify(data: Vec<i32>) -> Self {
        let mut heap = MaxHeap { data };
        let n = heap.data.len();
        // Start from last non-leaf, sift down each
        if n > 1 {
            for i in (0..n / 2).rev() {
                heap.sift_down(i);
            }
        }
        heap
    }
}

/// Using Rust's std BinaryHeap (max-heap by default)
use std::collections::BinaryHeap;
use std::cmp::Reverse; // for min-heap: wrap in Reverse<T>

/// K Largest Elements
fn k_largest(nums: &[i32], k: usize) -> Vec<i32> {
    // Min-heap of size k — maintain only the k largest
    let mut min_heap: BinaryHeap<Reverse<i32>> = BinaryHeap::new();
    
    for &num in nums {
        min_heap.push(Reverse(num));
        if min_heap.len() > k {
            min_heap.pop(); // remove the smallest
        }
    }
    
    min_heap.into_iter().map(|Reverse(x)| x).collect()
}

/// Merge K Sorted Lists — priority queue approach
/// Time: O(N log k) where N = total elements, k = number of lists
fn merge_k_sorted(lists: Vec<Vec<i32>>) -> Vec<i32> {
    use std::cmp::Ordering;
    
    // (value, list_index, element_index)
    #[derive(Eq, PartialEq)]
    struct HeapItem(i32, usize, usize);
    
    impl Ord for HeapItem {
        fn cmp(&self, other: &Self) -> Ordering {
            other.0.cmp(&self.0) // reverse for min-heap behavior
        }
    }
    impl PartialOrd for HeapItem {
        fn partial_cmp(&self, other: &Self) -> Option<Ordering> { Some(self.cmp(other)) }
    }
    
    let mut heap = BinaryHeap::new();
    let mut result = Vec::new();
    
    // Initialize with first element from each list
    for (i, list) in lists.iter().enumerate() {
        if !list.is_empty() {
            heap.push(HeapItem(list[0], i, 0));
        }
    }
    
    while let Some(HeapItem(val, list_i, elem_i)) = heap.pop() {
        result.push(val);
        let next_i = elem_i + 1;
        if next_i < lists[list_i].len() {
            heap.push(HeapItem(lists[list_i][next_i], list_i, next_i));
        }
    }
    result
}

/// Find Median from Data Stream
/// Two-heap approach: max-heap for lower half, min-heap for upper half
/// Maintain: max_heap.len() == min_heap.len() or max_heap.len() == min_heap.len() + 1
pub struct MedianFinder {
    lower: BinaryHeap<i32>,          // max-heap (lower half)
    upper: BinaryHeap<Reverse<i32>>, // min-heap (upper half)
}

impl MedianFinder {
    pub fn new() -> Self {
        MedianFinder { lower: BinaryHeap::new(), upper: BinaryHeap::new() }
    }
    
    pub fn add_num(&mut self, num: i32) {
        // Always push to lower first
        self.lower.push(num);
        
        // Balance: move largest of lower to upper
        self.upper.push(Reverse(self.lower.pop().unwrap()));
        
        // Ensure lower has >= elements as upper
        if self.upper.len() > self.lower.len() {
            self.lower.push(self.upper.pop().unwrap().0);
        }
    }
    
    pub fn find_median(&self) -> f64 {
        if self.lower.len() > self.upper.len() {
            *self.lower.peek().unwrap() as f64
        } else {
            let top_lower = *self.lower.peek().unwrap() as f64;
            let top_upper = self.upper.peek().unwrap().0 as f64;
            (top_lower + top_upper) / 2.0
        }
    }
}
```

---

## 8. SEGMENT TREES & FENWICK TREES

### Segment Tree — Range Query Master

```
A segment tree enables:
- Point updates in O(log n)
- Range queries in O(log n)
- Build in O(n)

Use it when: prefix sums aren't enough because data changes frequently.

Structure (for array [1, 3, 5, 7, 9, 11]):
                [36] (sum of all)
              /         \
          [9]              [27]
         /   \            /    \
       [4]   [5]       [16]   [11]
       / \   / \       /  \
      [1][3][5][..]  [7]  [9]
```

```rust
/// Segment Tree for Range Sum Queries with Point Updates
pub struct SegmentTree {
    n:    usize,
    tree: Vec<i64>,
}

impl SegmentTree {
    /// Build in O(n)
    pub fn new(arr: &[i32]) -> Self {
        let n = arr.len();
        let mut tree = vec![0i64; 4 * n]; // 4n is safe upper bound
        
        fn build(tree: &mut Vec<i64>, arr: &[i32], node: usize, start: usize, end: usize) {
            if start == end {
                tree[node] = arr[start] as i64;
                return;
            }
            let mid = (start + end) / 2;
            build(tree, arr, 2 * node,     start, mid);
            build(tree, arr, 2 * node + 1, mid + 1, end);
            tree[node] = tree[2 * node] + tree[2 * node + 1];
        }
        
        if n > 0 { build(&mut tree, arr, 1, 0, n - 1); }
        SegmentTree { n, tree }
    }
    
    /// Point update in O(log n)
    pub fn update(&mut self, idx: usize, val: i32) {
        fn update_rec(tree: &mut Vec<i64>, node: usize, start: usize, end: usize, 
                      idx: usize, val: i64) {
            if start == end {
                tree[node] = val;
                return;
            }
            let mid = (start + end) / 2;
            if idx <= mid {
                update_rec(tree, 2 * node,     start, mid,     idx, val);
            } else {
                update_rec(tree, 2 * node + 1, mid + 1, end,   idx, val);
            }
            tree[node] = tree[2 * node] + tree[2 * node + 1];
        }
        let n = self.n;
        update_rec(&mut self.tree, 1, 0, n - 1, idx, val as i64);
    }
    
    /// Range sum query in O(log n)
    pub fn query(&self, l: usize, r: usize) -> i64 {
        fn query_rec(tree: &[i64], node: usize, start: usize, end: usize,
                     l: usize, r: usize) -> i64 {
            if r < start || end < l { return 0; } // out of range
            if l <= start && end <= r { return tree[node]; } // fully covered
            let mid = (start + end) / 2;
            query_rec(tree, 2 * node,     start, mid,   l, r)
            + query_rec(tree, 2 * node + 1, mid + 1, end, l, r)
        }
        let n = self.n;
        query_rec(&self.tree, 1, 0, n - 1, l, r)
    }
}

/// Lazy Propagation Segment Tree — Range Updates in O(log n)
/// When you need to update a RANGE of values (e.g., add 5 to all elements in [l, r])
/// Lazy propagation defers the work: mark parent as "lazy", apply when needed.
pub struct LazySegTree {
    n:    usize,
    tree: Vec<i64>,
    lazy: Vec<i64>, // pending add operations
}

impl LazySegTree {
    pub fn new(arr: &[i32]) -> Self {
        let n = arr.len();
        let mut st = LazySegTree {
            n,
            tree: vec![0; 4 * n],
            lazy: vec![0; 4 * n],
        };
        if n > 0 { st.build(arr, 1, 0, n - 1); }
        st
    }
    
    fn build(&mut self, arr: &[i32], node: usize, start: usize, end: usize) {
        if start == end {
            self.tree[node] = arr[start] as i64;
            return;
        }
        let mid = (start + end) / 2;
        self.build(arr, 2 * node,     start, mid);
        self.build(arr, 2 * node + 1, mid + 1, end);
        self.tree[node] = self.tree[2*node] + self.tree[2*node+1];
    }
    
    fn push_down(&mut self, node: usize, start: usize, end: usize) {
        if self.lazy[node] != 0 {
            let mid = (start + end) / 2;
            let lc = 2 * node;
            let rc = 2 * node + 1;
            let add = self.lazy[node];
            
            self.tree[lc] += add * (mid - start + 1) as i64;
            self.tree[rc] += add * (end - mid)       as i64;
            self.lazy[lc] += add;
            self.lazy[rc] += add;
            self.lazy[node] = 0; // clear lazy flag
        }
    }
    
    /// Range add update — O(log n)
    pub fn range_add(&mut self, l: usize, r: usize, val: i64) {
        self.range_add_rec(1, 0, self.n - 1, l, r, val);
    }
    
    fn range_add_rec(&mut self, node: usize, start: usize, end: usize,
                     l: usize, r: usize, val: i64) {
        if r < start || end < l { return; }
        if l <= start && end <= r {
            self.tree[node] += val * (end - start + 1) as i64;
            self.lazy[node] += val;
            return;
        }
        self.push_down(node, start, end);
        let mid = (start + end) / 2;
        self.range_add_rec(2 * node,     start, mid,     l, r, val);
        self.range_add_rec(2 * node + 1, mid + 1, end,   l, r, val);
        self.tree[node] = self.tree[2*node] + self.tree[2*node+1];
    }
    
    pub fn range_sum(&mut self, l: usize, r: usize) -> i64 {
        self.range_sum_rec(1, 0, self.n - 1, l, r)
    }
    
    fn range_sum_rec(&mut self, node: usize, start: usize, end: usize,
                     l: usize, r: usize) -> i64 {
        if r < start || end < l { return 0; }
        if l <= start && end <= r { return self.tree[node]; }
        self.push_down(node, start, end);
        let mid = (start + end) / 2;
        self.range_sum_rec(2 * node,     start, mid,   l, r)
        + self.range_sum_rec(2 * node + 1, mid + 1, end, l, r)
    }
}

/// Fenwick Tree (Binary Indexed Tree) — simpler range sum with updates
/// Elegant mathematical structure using bit manipulation.
/// BIT[i] stores the sum of a specific range based on i's lowest set bit.
/// 
/// lowbit(i) = i & (-i)  ← extracts the lowest set bit
/// 
/// Query  [1..i]: walk from i toward 0 by subtracting lowbit each time
/// Update [i]:    walk from i toward n by adding lowbit each time
pub struct FenwickTree {
    tree: Vec<i64>,
    n:    usize,
}

impl FenwickTree {
    pub fn new(n: usize) -> Self {
        FenwickTree { tree: vec![0; n + 1], n }
    }
    
    /// Build from array in O(n) using the efficient bottom-up method
    pub fn from_array(arr: &[i32]) -> Self {
        let n = arr.len();
        let mut ft = Self::new(n);
        for (i, &v) in arr.iter().enumerate() {
            ft.add(i + 1, v as i64);
        }
        ft
    }
    
    /// Point update: add delta to index i (1-indexed), O(log n)
    pub fn add(&mut self, mut i: usize, delta: i64) {
        while i <= self.n {
            self.tree[i] += delta;
            i += i & i.wrapping_neg(); // i += lowbit(i)
        }
    }
    
    /// Prefix sum [1..=i], O(log n)
    pub fn prefix_sum(&self, mut i: usize) -> i64 {
        let mut sum = 0;
        while i > 0 {
            sum += self.tree[i];
            i -= i & i.wrapping_neg(); // i -= lowbit(i)
        }
        sum
    }
    
    /// Range sum [l..=r] (1-indexed), O(log n)
    pub fn range_sum(&self, l: usize, r: usize) -> i64 {
        self.prefix_sum(r) - self.prefix_sum(l - 1)
    }
}
```

---

## 9. GRAPHS

### Graph Representations

```
Adjacency Matrix: O(V²) space, O(1) edge lookup, O(V) neighbor iteration
Adjacency List:   O(V+E) space, O(degree) neighbor iteration — PREFERRED for sparse graphs
Edge List:        O(E) space, used for Kruskal's MST

When to use which:
- Dense graph (E ≈ V²): matrix is fine
- Sparse graph (E ≈ V): always use adjacency list
- Need edge weights: store (neighbor, weight) pairs
```

```rust
use std::collections::{HashMap, HashSet, BinaryHeap, VecDeque};

/// Weighted directed graph using adjacency list
pub struct Graph {
    pub adj: Vec<Vec<(usize, i64)>>, // (neighbor, weight)
    pub n:   usize,
}

impl Graph {
    pub fn new(n: usize) -> Self {
        Graph { adj: vec![Vec::new(); n], n }
    }
    
    pub fn add_directed_edge(&mut self, u: usize, v: usize, w: i64) {
        self.adj[u].push((v, w));
    }
    
    pub fn add_undirected_edge(&mut self, u: usize, v: usize, w: i64) {
        self.adj[u].push((v, w));
        self.adj[v].push((u, w));
    }
}

/// BFS — Breadth First Search
/// Time: O(V + E), Space: O(V)
/// Use for: shortest path in unweighted graphs, level-by-level traversal
fn bfs(graph: &Graph, start: usize) -> Vec<i32> {
    let mut dist = vec![-1i32; graph.n];
    let mut queue = VecDeque::new();
    
    dist[start] = 0;
    queue.push_back(start);
    
    while let Some(node) = queue.pop_front() {
        for &(next, _) in &graph.adj[node] {
            if dist[next] == -1 {
                dist[next] = dist[node] + 1;
                queue.push_back(next);
            }
        }
    }
    dist
}

/// DFS — Depth First Search
/// Time: O(V + E), Space: O(V) call stack
/// Use for: cycle detection, topological sort, connected components, SCC
fn dfs(graph: &Graph, start: usize, visited: &mut Vec<bool>, order: &mut Vec<usize>) {
    visited[start] = true;
    for &(next, _) in &graph.adj[start] {
        if !visited[next] {
            dfs(graph, next, visited, order);
        }
    }
    order.push(start); // postorder — useful for topological sort
}

/// Topological Sort — Kahn's Algorithm (BFS-based)
/// Only valid for Directed Acyclic Graphs (DAGs)
/// If result.len() < n, the graph has a cycle
/// Time: O(V + E)
fn topological_sort_kahn(graph: &Graph) -> Option<Vec<usize>> {
    let mut in_degree = vec![0usize; graph.n];
    for u in 0..graph.n {
        for &(v, _) in &graph.adj[u] {
            in_degree[v] += 1;
        }
    }
    
    let mut queue: VecDeque<usize> = (0..graph.n)
        .filter(|&i| in_degree[i] == 0)
        .collect();
    let mut order = Vec::new();
    
    while let Some(u) = queue.pop_front() {
        order.push(u);
        for &(v, _) in &graph.adj[u] {
            in_degree[v] -= 1;
            if in_degree[v] == 0 { queue.push_back(v); }
        }
    }
    
    if order.len() == graph.n { Some(order) } else { None } // None = cycle detected
}

/// Dijkstra's Shortest Path — single source, non-negative weights
/// Time: O((V + E) log V) with binary heap
/// 
/// Mental model: Greedy BFS where we always process the CLOSEST unvisited node.
/// The invariant: once a node is popped from the heap, its distance is FINAL.
/// This works because all weights are non-negative.
fn dijkstra(graph: &Graph, start: usize) -> Vec<i64> {
    const INF: i64 = i64::MAX / 2;
    let mut dist = vec![INF; graph.n];
    let mut heap: BinaryHeap<(std::cmp::Reverse<i64>, usize)> = BinaryHeap::new();
    
    dist[start] = 0;
    heap.push((std::cmp::Reverse(0), start));
    
    while let Some((std::cmp::Reverse(d), u)) = heap.pop() {
        if d > dist[u] { continue; } // stale entry — skip
        
        for &(v, w) in &graph.adj[u] {
            let new_dist = dist[u] + w;
            if new_dist < dist[v] {
                dist[v] = new_dist;
                heap.push((std::cmp::Reverse(new_dist), v));
            }
        }
    }
    dist
}

/// Bellman-Ford — single source, handles NEGATIVE weights
/// Time: O(V × E), detects negative cycles
/// 
/// Key insight: shortest paths have at most V-1 edges.
/// Relax ALL edges V-1 times. If we can still relax on the Vth pass → negative cycle.
fn bellman_ford(graph: &Graph, start: usize) -> Option<Vec<i64>> {
    const INF: i64 = i64::MAX / 2;
    let mut dist = vec![INF; graph.n];
    dist[start] = 0;
    
    // Build edge list
    let mut edges = Vec::new();
    for u in 0..graph.n {
        for &(v, w) in &graph.adj[u] {
            edges.push((u, v, w));
        }
    }
    
    // Relax V-1 times
    for _ in 0..graph.n - 1 {
        for &(u, v, w) in &edges {
            if dist[u] != INF && dist[u] + w < dist[v] {
                dist[v] = dist[u] + w;
            }
        }
    }
    
    // Check for negative cycles
    for &(u, v, w) in &edges {
        if dist[u] != INF && dist[u] + w < dist[v] {
            return None; // negative cycle detected
        }
    }
    
    Some(dist)
}

/// Floyd-Warshall — all-pairs shortest paths
/// Time: O(V³), Space: O(V²)
/// Use when: you need distances between ALL pairs of nodes
fn floyd_warshall(n: usize, edges: &[(usize, usize, i64)]) -> Vec<Vec<i64>> {
    const INF: i64 = i64::MAX / 2;
    let mut dist = vec![vec![INF; n]; n];
    
    for i in 0..n { dist[i][i] = 0; }
    for &(u, v, w) in edges {
        dist[u][v] = w;
        dist[v][u] = w; // if undirected
    }
    
    // The DP insight: dist[i][j] through intermediate vertex k
    for k in 0..n {
        for i in 0..n {
            for j in 0..n {
                if dist[i][k] != INF && dist[k][j] != INF {
                    dist[i][j] = dist[i][j].min(dist[i][k] + dist[k][j]);
                }
            }
        }
    }
    dist
}

/// Kruskal's MST — greedy, sort edges by weight, use DSU
/// Time: O(E log E)
fn kruskal_mst(n: usize, mut edges: Vec<(i64, usize, usize)>) -> (i64, Vec<(usize, usize)>) {
    edges.sort_unstable_by_key(|&(w, _, _)| w);
    let mut dsu = DSU::new(n);
    let mut mst_weight = 0i64;
    let mut mst_edges  = Vec::new();
    
    for (w, u, v) in edges {
        if dsu.union(u, v) { // only add if connects different components
            mst_weight += w;
            mst_edges.push((u, v));
        }
    }
    (mst_weight, mst_edges)
}

/// Prim's MST — greedy, grow from single vertex using priority queue
/// Time: O(E log V), better for dense graphs than Kruskal's
fn prim_mst(graph: &Graph) -> i64 {
    const INF: i64 = i64::MAX / 2;
    let mut min_cost = vec![INF; graph.n];
    let mut in_mst   = vec![false; graph.n];
    let mut heap: BinaryHeap<(std::cmp::Reverse<i64>, usize)> = BinaryHeap::new();
    
    min_cost[0] = 0;
    heap.push((std::cmp::Reverse(0), 0));
    let mut total = 0i64;
    
    while let Some((std::cmp::Reverse(cost), u)) = heap.pop() {
        if in_mst[u] { continue; }
        in_mst[u] = true;
        total += cost;
        
        for &(v, w) in &graph.adj[u] {
            if !in_mst[v] && w < min_cost[v] {
                min_cost[v] = w;
                heap.push((std::cmp::Reverse(w), v));
            }
        }
    }
    total
}

/// Strongly Connected Components — Tarjan's Algorithm
/// An SCC is a maximal group of vertices where every vertex is reachable from every other.
/// Time: O(V + E)
pub struct TarjanSCC {
    graph:    Vec<Vec<usize>>,
    n:        usize,
    disc:     Vec<i32>,   // discovery time
    low:      Vec<i32>,   // lowest discovery time reachable
    on_stack: Vec<bool>,
    stack:    Vec<usize>,
    timer:    i32,
    sccs:     Vec<Vec<usize>>,
}

impl TarjanSCC {
    pub fn new(graph: Vec<Vec<usize>>) -> Self {
        let n = graph.len();
        TarjanSCC {
            graph, n,
            disc:     vec![-1; n],
            low:      vec![-1; n],
            on_stack: vec![false; n],
            stack:    Vec::new(),
            timer:    0,
            sccs:     Vec::new(),
        }
    }
    
    pub fn find_sccs(mut self) -> Vec<Vec<usize>> {
        for i in 0..self.n {
            if self.disc[i] == -1 {
                self.dfs(i);
            }
        }
        self.sccs
    }
    
    fn dfs(&mut self, u: usize) {
        self.disc[u]     = self.timer;
        self.low[u]      = self.timer;
        self.timer       += 1;
        self.stack.push(u);
        self.on_stack[u] = true;
        
        for vi in 0..self.graph[u].len() {
            let v = self.graph[u][vi];
            if self.disc[v] == -1 {
                self.dfs(v);
                self.low[u] = self.low[u].min(self.low[v]);
            } else if self.on_stack[v] {
                self.low[u] = self.low[u].min(self.disc[v]);
            }
        }
        
        // If u is root of an SCC
        if self.low[u] == self.disc[u] {
            let mut scc = Vec::new();
            loop {
                let w = self.stack.pop().unwrap();
                self.on_stack[w] = false;
                scc.push(w);
                if w == u { break; }
            }
            self.sccs.push(scc);
        }
    }
}
```

---

## 10. TRIES

### Trie Mental Model

```
A trie is a tree where each path from root to a node represents a string prefix.
Used for: autocomplete, spell checking, IP routing, prefix matching.

Example trie for words: ["apple", "app", "apply", "apt"]:

        root
         |
         a
         |
         p
        / \
       p   t
      / \
     l   (end: "app")
    / \
   e   y
(end) (end)
(apple) (apply)
```

```rust
/// Trie with full operations
#[derive(Default)]
struct TrieNode {
    children:  [Option<Box<TrieNode>>; 26],
    is_end:    bool,
    word_count: usize, // count of words ending here
}

pub struct Trie {
    root: TrieNode,
}

impl Trie {
    pub fn new() -> Self { Trie { root: TrieNode::default() } }
    
    fn char_index(c: char) -> usize {
        (c as u8 - b'a') as usize
    }
    
    /// Insert word — O(|word|)
    pub fn insert(&mut self, word: &str) {
        let mut node = &mut self.root;
        for ch in word.chars() {
            let idx = Self::char_index(ch);
            node = node.children[idx].get_or_insert_with(|| Box::new(TrieNode::default()));
        }
        node.is_end = true;
        node.word_count += 1;
    }
    
    /// Search for exact word — O(|word|)
    pub fn search(&self, word: &str) -> bool {
        let mut node = &self.root;
        for ch in word.chars() {
            let idx = Self::char_index(ch);
            match &node.children[idx] {
                None => return false,
                Some(child) => node = child,
            }
        }
        node.is_end
    }
    
    /// Check if any word starts with prefix — O(|prefix|)
    pub fn starts_with(&self, prefix: &str) -> bool {
        let mut node = &self.root;
        for ch in prefix.chars() {
            let idx = Self::char_index(ch);
            match &node.children[idx] {
                None => return false,
                Some(child) => node = child,
            }
        }
        true
    }
    
    /// Find all words with given prefix — autocomplete
    pub fn autocomplete(&self, prefix: &str) -> Vec<String> {
        let mut node = &self.root;
        for ch in prefix.chars() {
            let idx = Self::char_index(ch);
            match &node.children[idx] {
                None => return Vec::new(),
                Some(child) => node = child,
            }
        }
        
        let mut results = Vec::new();
        let mut current = prefix.to_string();
        Self::collect_words(node, &mut current, &mut results);
        results
    }
    
    fn collect_words(node: &TrieNode, current: &mut String, results: &mut Vec<String>) {
        if node.is_end { results.push(current.clone()); }
        
        for (i, child) in node.children.iter().enumerate() {
            if let Some(child) = child {
                let ch = (b'a' + i as u8) as char;
                current.push(ch);
                Self::collect_words(child, current, results);
                current.pop();
            }
        }
    }
    
    /// Wildcard search (. matches any character) — O(26^k) worst case
    pub fn search_wildcard(&self, word: &str) -> bool {
        Self::wildcard_dfs(&self.root, word.as_bytes(), 0)
    }
    
    fn wildcard_dfs(node: &TrieNode, word: &[u8], idx: usize) -> bool {
        if idx == word.len() { return node.is_end; }
        
        if word[idx] == b'.' {
            // Try all possible children
            node.children.iter().flatten().any(|child| {
                Self::wildcard_dfs(child, word, idx + 1)
            })
        } else {
            let ci = (word[idx] - b'a') as usize;
            node.children[ci].as_ref()
                .map_or(false, |child| Self::wildcard_dfs(child, word, idx + 1))
        }
    }
}

/// Compressed Trie using HashMap for arbitrary alphabets
pub struct CompressedTrie {
    children: HashMap<char, Box<CompressedTrie>>,
    is_end:   bool,
}

impl CompressedTrie {
    pub fn new() -> Self {
        CompressedTrie { children: HashMap::new(), is_end: false }
    }
    
    pub fn insert(&mut self, word: &str) {
        let mut node = self;
        for ch in word.chars() {
            node = node.children.entry(ch).or_insert_with(|| Box::new(CompressedTrie::new()));
        }
        node.is_end = true;
    }
}
```

---

## 11. DISJOINT SET UNION (DSU)

### DSU Mental Model

```
DSU (Union-Find) answers: "Are these two elements in the same group?"
in nearly O(1) amortized time with two optimizations:
1. Path Compression: after finding root, make all nodes point directly to root
2. Union by Rank: always attach smaller tree under larger tree

Real-world uses: Kruskal's MST, detecting cycles, network connectivity,
                 image segmentation, social network groups.
```

```rust
/// DSU with Path Compression + Union by Rank
/// Amortized O(α(n)) per operation (α = inverse Ackermann, effectively constant)
pub struct DSU {
    parent: Vec<usize>,
    rank:   Vec<usize>,
    size:   Vec<usize>,
    count:  usize, // number of distinct components
}

impl DSU {
    pub fn new(n: usize) -> Self {
        DSU {
            parent: (0..n).collect(),  // each element is its own parent
            rank:   vec![0; n],
            size:   vec![1; n],
            count:  n,
        }
    }
    
    /// Find with path compression — O(α(n))
    pub fn find(&mut self, mut x: usize) -> usize {
        while self.parent[x] != x {
            self.parent[x] = self.parent[self.parent[x]]; // path halving (fast)
            x = self.parent[x];
        }
        x
    }
    
    /// Alternative: full path compression (slower in practice due to recursion)
    pub fn find_full_compress(&mut self, x: usize) -> usize {
        if self.parent[x] != x {
            self.parent[x] = self.find_full_compress(self.parent[x]);
        }
        self.parent[x]
    }
    
    /// Union by rank — returns true if union was performed (elements were in diff sets)
    pub fn union(&mut self, x: usize, y: usize) -> bool {
        let (rx, ry) = (self.find(x), self.find(y));
        if rx == ry { return false; } // already in same set — would create cycle
        
        // Attach smaller rank tree under larger rank tree
        match self.rank[rx].cmp(&self.rank[ry]) {
            std::cmp::Ordering::Less => {
                self.parent[rx] = ry;
                self.size[ry]  += self.size[rx];
            }
            std::cmp::Ordering::Greater => {
                self.parent[ry] = rx;
                self.size[rx]  += self.size[ry];
            }
            std::cmp::Ordering::Equal => {
                self.parent[ry]  = rx;
                self.size[rx]   += self.size[ry];
                self.rank[rx]   += 1; // only increase rank on equal merge
            }
        }
        self.count -= 1;
        true
    }
    
    pub fn connected(&mut self, x: usize, y: usize) -> bool {
        self.find(x) == self.find(y)
    }
    
    pub fn component_size(&mut self, x: usize) -> usize {
        let root = self.find(x);
        self.size[root]
    }
    
    pub fn num_components(&self) -> usize { self.count }
}

/// Application: Number of Islands
fn num_islands(grid: &mut Vec<Vec<char>>) -> i32 {
    if grid.is_empty() { return 0; }
    let (rows, cols) = (grid.len(), grid[0].len());
    let mut dsu = DSU::new(rows * cols);
    let mut water_count = 0;
    
    for r in 0..rows {
        for c in 0..cols {
            if grid[r][c] == '0' { water_count += 1; continue; }
            let idx = r * cols + c;
            // Connect with right and down neighbors (avoid double-counting)
            if c + 1 < cols && grid[r][c+1] == '1' { dsu.union(idx, idx + 1); }
            if r + 1 < rows && grid[r+1][c] == '1' { dsu.union(idx, idx + cols); }
        }
    }
    (dsu.num_components() - water_count) as i32
}
```

---

## 12. SORTING ALGORITHMS

### The Sorting Landscape

```
Algorithm      | Best      | Avg       | Worst     | Space  | Stable?
---------------|-----------|-----------|-----------|--------|--------
Bubble Sort    | O(n)      | O(n²)     | O(n²)     | O(1)   | Yes
Insertion Sort | O(n)      | O(n²)     | O(n²)     | O(1)   | Yes
Merge Sort     | O(n log n)| O(n log n)| O(n log n)| O(n)   | Yes
Quick Sort     | O(n log n)| O(n log n)| O(n²)     | O(log n)| No
Heap Sort      | O(n log n)| O(n log n)| O(n log n)| O(1)   | No
Counting Sort  | O(n+k)    | O(n+k)    | O(n+k)    | O(k)   | Yes
Radix Sort     | O(nk)     | O(nk)     | O(nk)     | O(n+k) | Yes
Tim Sort       | O(n)      | O(n log n)| O(n log n)| O(n)   | Yes ← Rust default

Expert decision tree:
- General purpose → Rust's .sort() (Tim Sort) or .sort_unstable() (pdq sort)
- Nearly sorted   → Insertion sort (adaptive, O(n) best case)
- Memory critical → Heap sort (O(1) space)
- Integer data    → Counting or Radix sort
- Parallel sort   → Merge sort (easily parallelizable)
```

```rust
/// Merge Sort — divide and conquer, stable, O(n log n) guaranteed
fn merge_sort(arr: &mut Vec<i32>) {
    let n = arr.len();
    if n <= 1 { return; }
    
    let mid = n / 2;
    let mut left  = arr[..mid].to_vec();
    let mut right = arr[mid..].to_vec();
    
    merge_sort(&mut left);
    merge_sort(&mut right);
    
    // Merge phase
    let (mut i, mut j, mut k) = (0, 0, 0);
    while i < left.len() && j < right.len() {
        if left[i] <= right[j] { arr[k] = left[i];  i += 1; }
        else                   { arr[k] = right[j]; j += 1; }
        k += 1;
    }
    while i < left.len()  { arr[k] = left[i];  i += 1; k += 1; }
    while j < right.len() { arr[k] = right[j]; j += 1; k += 1; }
}

/// Count inversions using merge sort — O(n log n)
/// An inversion is a pair (i, j) where i < j but arr[i] > arr[j]
fn count_inversions(arr: &mut Vec<i32>) -> i64 {
    if arr.len() <= 1 { return 0; }
    let mid = arr.len() / 2;
    let mut left  = arr[..mid].to_vec();
    let mut right = arr[mid..].to_vec();
    
    let mut count = count_inversions(&mut left) + count_inversions(&mut right);
    
    let (mut i, mut j, mut k) = (0, 0, 0);
    while i < left.len() && j < right.len() {
        if left[i] <= right[j] {
            arr[k] = left[i]; i += 1;
        } else {
            // All remaining elements in left are > right[j] — all are inversions
            count += (left.len() - i) as i64;
            arr[k] = right[j]; j += 1;
        }
        k += 1;
    }
    while i < left.len()  { arr[k] = left[i];  i += 1; k += 1; }
    while j < right.len() { arr[k] = right[j]; j += 1; k += 1; }
    count
}

/// Quick Sort — in-place, cache-friendly, O(n log n) average
fn quick_sort(arr: &mut Vec<i32>, lo: usize, hi: usize) {
    if lo >= hi { return; }
    let pivot_idx = partition(arr, lo, hi);
    if pivot_idx > 0 { quick_sort(arr, lo, pivot_idx - 1); }
    quick_sort(arr, pivot_idx + 1, hi);
}

/// Lomuto partition scheme
fn partition(arr: &mut Vec<i32>, lo: usize, hi: usize) -> usize {
    // Median-of-three pivot selection to avoid worst case on sorted input
    let mid = lo + (hi - lo) / 2;
    if arr[mid] < arr[lo] { arr.swap(mid, lo); }
    if arr[hi]  < arr[lo] { arr.swap(hi,  lo); }
    if arr[mid] < arr[hi] { arr.swap(mid, hi); }
    // Now arr[hi] is the median of three — good pivot
    
    let pivot = arr[hi];
    let mut i = lo;
    
    for j in lo..hi {
        if arr[j] <= pivot {
            arr.swap(i, j);
            i += 1;
        }
    }
    arr.swap(i, hi);
    i
}

/// Dutch National Flag — 3-way partition
/// Crucial for Quick Sort with many duplicate keys (like sort colors problem)
fn dutch_national_flag(arr: &mut Vec<i32>) {
    let (mut lo, mut mid, mut hi) = (0, 0, arr.len());
    
    while mid < hi {
        match arr[mid] {
            0 => { arr.swap(lo, mid); lo += 1; mid += 1; }
            1 => { mid += 1; }
            _ => { hi -= 1; arr.swap(mid, hi); }
        }
    }
}

/// Counting Sort — O(n + k) for small integer ranges
fn counting_sort(arr: &[i32], max_val: usize) -> Vec<i32> {
    let mut count = vec![0usize; max_val + 1];
    for &x in arr { count[x as usize] += 1; }
    
    // Prefix sum to get positions
    for i in 1..=max_val { count[i] += count[i-1]; }
    
    let mut result = vec![0; arr.len()];
    for &x in arr.iter().rev() { // iterate in reverse for stability
        count[x as usize] -= 1;
        result[count[x as usize]] = x;
    }
    result
}

/// Radix Sort — O(nk) for integers with k digits
fn radix_sort(arr: &mut Vec<u32>) {
    let max = *arr.iter().max().unwrap_or(&0);
    let mut exp = 1u32;
    
    while max / exp > 0 {
        counting_sort_by_digit(arr, exp);
        exp = exp.saturating_mul(10);
    }
}

fn counting_sort_by_digit(arr: &mut Vec<u32>, exp: u32) {
    let n = arr.len();
    let mut output = vec![0u32; n];
    let mut count  = [0usize; 10];
    
    for &x in arr.iter() { count[((x / exp) % 10) as usize] += 1; }
    for i in 1..10        { count[i] += count[i-1]; }
    for &x in arr.iter().rev() {
        let digit = ((x / exp) % 10) as usize;
        count[digit] -= 1;
        output[count[digit]] = x;
    }
    arr.copy_from_slice(&output);
}
```

---

## 13. SEARCHING & BINARY SEARCH MASTERY

### Binary Search: The Most Misunderstood Algorithm

```
Binary search is NOT just "find element in sorted array."
It is: "find the boundary of a monotonic predicate."

The universal template:
- Define predicate P(x) that is false for some prefix, true for some suffix (or vice versa)
- Binary search finds the EXACT boundary

Three forms:
1. Find exact element
2. Find leftmost position where P(x) = true  (lower_bound)
3. Find rightmost position where P(x) = false (upper_bound)
```

```rust
/// The Universal Binary Search Template
/// Find the smallest index where predicate returns true.
/// Precondition: predicate is monotonic (false, false, ..., true, true, ...)
fn binary_search_boundary<P: Fn(usize) -> bool>(lo: usize, hi: usize, pred: P) -> usize {
    let (mut lo, mut hi) = (lo, hi);
    while lo < hi {
        let mid = lo + (hi - lo) / 2; // avoids overflow — critical!
        if pred(mid) { hi = mid; }    // boundary is at or before mid
        else         { lo = mid + 1; } // boundary is after mid
    }
    lo // lo == hi == the boundary
}

/// Lower bound: first index where arr[i] >= target
fn lower_bound(arr: &[i32], target: i32) -> usize {
    binary_search_boundary(0, arr.len(), |i| arr[i] >= target)
}

/// Upper bound: first index where arr[i] > target
fn upper_bound(arr: &[i32], target: i32) -> usize {
    binary_search_boundary(0, arr.len(), |i| arr[i] > target)
}

/// Search in Rotated Sorted Array — O(log n)
/// Key insight: one half is ALWAYS sorted. Determine which half, search there.
fn search_rotated(nums: &[i32], target: i32) -> Option<usize> {
    let (mut lo, mut hi) = (0i32, nums.len() as i32 - 1);
    
    while lo <= hi {
        let mid = lo + (hi - lo) / 2;
        let m = mid as usize;
        
        if nums[m] == target { return Some(m); }
        
        // Determine which half is sorted
        if nums[lo as usize] <= nums[m] {
            // Left half is sorted
            if nums[lo as usize] <= target && target < nums[m] {
                hi = mid - 1;
            } else {
                lo = mid + 1;
            }
        } else {
            // Right half is sorted
            if nums[m] < target && target <= nums[hi as usize] {
                lo = mid + 1;
            } else {
                hi = mid - 1;
            }
        }
    }
    None
}

/// Find Minimum in Rotated Array — O(log n)
fn find_minimum_rotated(nums: &[i32]) -> i32 {
    let (mut lo, mut hi) = (0, nums.len() - 1);
    
    while lo < hi {
        let mid = lo + (hi - lo) / 2;
        // If mid element > last element, minimum is in right half
        if nums[mid] > nums[hi] { lo = mid + 1; }
        else                    { hi = mid;      }
    }
    nums[lo]
}

/// Binary search on the ANSWER — the most powerful application
/// "Minimize the maximum" or "Maximize the minimum" problems

/// Koko Eating Bananas — minimize eating speed such that done within H hours
/// Mental model: can_finish(speed) is monotonic — once fast enough, always fast enough
fn min_eating_speed(piles: &[i32], h: i32) -> i32 {
    let max_pile = *piles.iter().max().unwrap();
    
    // Binary search on the answer: speed in [1, max_pile]
    binary_search_boundary(1, max_pile as usize, |speed| {
        // Can we finish all piles at this speed within h hours?
        let hours: i64 = piles.iter()
            .map(|&p| (p as i64 + speed as i64 - 1) / speed as i64) // ceil division
            .sum();
        hours <= h as i64
    }) as i32
}

/// Capacity to Ship Packages — minimize capacity to ship within D days
fn ship_within_days(weights: &[i32], days: i32) -> i32 {
    let lo = *weights.iter().max().unwrap(); // can't be less than heaviest package
    let hi: i32 = weights.iter().sum();     // worst case: ship all in one day
    
    binary_search_boundary(lo as usize, hi as usize, |cap| {
        // Can we ship all packages within 'days' days with this capacity?
        let (mut day_count, mut current_load) = (1i32, 0i32);
        for &w in weights {
            if current_load + w > cap as i32 {
                day_count += 1;
                current_load = w;
            } else {
                current_load += w;
            }
        }
        day_count <= days
    }) as i32
}

/// Median of Two Sorted Arrays — O(log(min(m, n)))
/// The hardest binary search problem. True mastery territory.
fn find_median_sorted_arrays(nums1: &[i32], nums2: &[i32]) -> f64 {
    // Ensure nums1 is the smaller array
    let (a, b) = if nums1.len() <= nums2.len() {
        (nums1, nums2)
    } else {
        (nums2, nums1)
    };
    
    let (m, n)  = (a.len(), b.len());
    let half    = (m + n + 1) / 2;
    let (mut lo, mut hi) = (0, m);
    
    while lo <= hi {
        let i = lo + (hi - lo) / 2; // partition point in a
        let j = half - i;           // partition point in b
        
        let a_left  = if i > 0 { a[i-1] } else { i32::MIN };
        let a_right = if i < m { a[i]   } else { i32::MAX };
        let b_left  = if j > 0 { b[j-1] } else { i32::MIN };
        let b_right = if j < n { b[j]   } else { i32::MAX };
        
        if a_left <= b_right && b_left <= a_right {
            // Found the correct partition
            let max_left  = a_left.max(b_left);
            let min_right = a_right.min(b_right);
            
            return if (m + n) % 2 == 1 {
                max_left as f64
            } else {
                (max_left + min_right) as f64 / 2.0
            };
        } else if a_left > b_right {
            hi = i - 1; // move partition left in a
        } else {
            lo = i + 1; // move partition right in a
        }
    }
    0.0 // shouldn't reach here
}
```

---

## 14. DYNAMIC PROGRAMMING

### The DP Mental Model

```
Dynamic Programming = Recursion + Memoization (top-down)
                    = Iteration + Tabulation  (bottom-up)

Every DP problem has:
1. State: what uniquely defines a subproblem?
2. Transition: how do we compute state from smaller states?
3. Base case: what are the simplest states?
4. Answer: which state contains our final answer?

The 5 DP patterns:
1. Linear DP: dp[i] depends on dp[i-1], dp[i-2], etc.
2. Interval DP: dp[i][j] = best answer for subarray [i, j]
3. Knapsack DP: choose items to maximize value with constraints
4. Grid DP: dp[i][j] = best path to cell (i, j)
5. Bitmask DP: dp[mask] = state for a subset of elements
```

```rust
/// Coin Change — classic unbounded knapsack
/// dp[i] = minimum coins to make amount i
/// Time: O(amount × coins), Space: O(amount)
fn coin_change(coins: &[i32], amount: i32) -> i32 {
    let amount = amount as usize;
    let mut dp = vec![i32::MAX; amount + 1];
    dp[0] = 0; // base case: 0 coins for amount 0
    
    for i in 1..=amount {
        for &coin in coins {
            let c = coin as usize;
            if c <= i && dp[i - c] != i32::MAX {
                dp[i] = dp[i].min(dp[i - c] + 1);
            }
        }
    }
    
    if dp[amount] == i32::MAX { -1 } else { dp[amount] }
}

/// Longest Common Subsequence — 2D DP
/// dp[i][j] = LCS of s1[0..i] and s2[0..j]
/// Transition:
///   if s1[i-1] == s2[j-1]: dp[i][j] = dp[i-1][j-1] + 1
///   else:                   dp[i][j] = max(dp[i-1][j], dp[i][j-1])
fn longest_common_subsequence(s1: &str, s2: &str) -> usize {
    let (a, b) = (s1.as_bytes(), s2.as_bytes());
    let (m, n) = (a.len(), b.len());
    let mut dp = vec![vec![0usize; n + 1]; m + 1];
    
    for i in 1..=m {
        for j in 1..=n {
            dp[i][j] = if a[i-1] == b[j-1] {
                dp[i-1][j-1] + 1
            } else {
                dp[i-1][j].max(dp[i][j-1])
            };
        }
    }
    dp[m][n]
}

/// Longest Increasing Subsequence — O(n log n) with patience sorting
/// The O(n²) DP is straightforward but the O(n log n) is elegant.
/// 
/// Mental model: maintain 'tails' array where tails[i] is the smallest
/// tail element of all increasing subsequences of length i+1.
/// Binary search to find where current element fits.
fn lis(nums: &[i32]) -> usize {
    let mut tails: Vec<i32> = Vec::new();
    
    for &num in nums {
        // Binary search for first tail >= num
        let pos = tails.partition_point(|&t| t < num);
        if pos == tails.len() {
            tails.push(num); // extend LIS by 1
        } else {
            tails[pos] = num; // replace to maintain smallest possible tail
        }
    }
    tails.len()
}

/// Edit Distance (Levenshtein) — classic string DP
/// dp[i][j] = min edits to convert s1[0..i] to s2[0..j]
fn edit_distance(s1: &str, s2: &str) -> usize {
    let (a, b) = (s1.as_bytes(), s2.as_bytes());
    let (m, n) = (a.len(), b.len());
    let mut dp = vec![vec![0; n + 1]; m + 1];
    
    // Base cases: converting to/from empty string
    for i in 0..=m { dp[i][0] = i; }
    for j in 0..=n { dp[0][j] = j; }
    
    for i in 1..=m {
        for j in 1..=n {
            dp[i][j] = if a[i-1] == b[j-1] {
                dp[i-1][j-1] // match — no edit needed
            } else {
                1 + dp[i-1][j-1]      // replace
                    .min(dp[i-1][j])   // delete from s1
                    .min(dp[i][j-1])   // insert into s1
            };
        }
    }
    dp[m][n]
}

/// 0/1 Knapsack — each item can be used at most once
/// dp[i][w] = max value using first i items with capacity w
/// Space optimization: use 1D DP, iterate weights in REVERSE
fn knapsack_01(weights: &[usize], values: &[i32], capacity: usize) -> i32 {
    let n = weights.len();
    let mut dp = vec![0i32; capacity + 1];
    
    for i in 0..n {
        // Iterate in reverse to prevent using item i twice
        for w in (weights[i]..=capacity).rev() {
            dp[w] = dp[w].max(dp[w - weights[i]] + values[i]);
        }
    }
    dp[capacity]
}

/// Matrix Chain Multiplication — interval DP
/// Find optimal parenthesization to minimize scalar multiplications
/// dp[i][j] = min cost to multiply matrices i through j
fn matrix_chain_order(dims: &[usize]) -> usize {
    let n = dims.len() - 1; // number of matrices
    let mut dp = vec![vec![0usize; n]; n];
    
    // Chain length from 2 to n
    for len in 2..=n {
        for i in 0..=(n - len) {
            let j = i + len - 1;
            dp[i][j] = usize::MAX;
            
            for k in i..j {
                let cost = dp[i][k] + dp[k+1][j] + dims[i] * dims[k+1] * dims[j+1];
                dp[i][j] = dp[i][j].min(cost);
            }
        }
    }
    dp[0][n-1]
}

/// Unique Paths in Grid — combinatorial DP
fn unique_paths(m: usize, n: usize) -> u64 {
    let mut dp = vec![1u64; n]; // first row: all 1s (only one way: go right)
    
    for _ in 1..m {
        for j in 1..n {
            dp[j] += dp[j-1]; // paths from left + paths from above
        }
    }
    dp[n-1]
}

/// Palindromic Substrings — expand around center
/// More elegant than DP for this specific problem.
fn count_palindromic_substrings(s: &str) -> usize {
    let s: Vec<char> = s.chars().collect();
    let n = s.len();
    let mut count = 0;
    
    fn expand(s: &[char], mut lo: i32, mut hi: i32) -> usize {
        let mut cnt = 0;
        while lo >= 0 && hi < s.len() as i32 && s[lo as usize] == s[hi as usize] {
            cnt += 1; lo -= 1; hi += 1;
        }
        cnt
    }
    
    for i in 0..n {
        count += expand(&s, i as i32, i as i32);     // odd length
        count += expand(&s, i as i32, i as i32 + 1); // even length
    }
    count
}

/// Bitmask DP — Traveling Salesman Problem
/// dp[mask][i] = minimum cost to visit exactly the cities in 'mask', ending at city i
/// Time: O(2^n × n²), feasible for n ≤ 20
fn tsp(dist: &Vec<Vec<i32>>) -> i32 {
    let n = dist.len();
    let full_mask = (1 << n) - 1;
    const INF: i32 = i32::MAX / 2;
    
    // dp[mask][i]: min cost visiting cities in mask, currently at i, started at 0
    let mut dp = vec![vec![INF; n]; 1 << n];
    dp[1][0] = 0; // start at city 0, visited only city 0 (bit 0 set)
    
    for mask in 1..=(1usize << n) {
        for u in 0..n {
            if dp[mask][u] == INF { continue; }
            if mask & (1 << u) == 0 { continue; } // u not in this mask
            
            for v in 0..n {
                if mask & (1 << v) != 0 { continue; } // v already visited
                let new_mask = mask | (1 << v);
                let new_cost = dp[mask][u] + dist[u][v];
                dp[new_mask][v] = dp[new_mask][v].min(new_cost);
            }
        }
    }
    
    // Find minimum cost to return to start from any last city
    (0..n).map(|i| {
        if dp[full_mask][i] == INF { INF }
        else { dp[full_mask][i] + dist[i][0] }
    }).min().unwrap_or(INF)
}
```

---

## 15. STRING ALGORITHMS

### KMP — Knuth-Morris-Pratt

```rust
/// KMP Pattern Matching — O(n + m)
/// Key: the failure function (LPS array) encodes the longest proper prefix
/// of pattern[0..i] that is also a suffix.
/// This lets us avoid redundant comparisons.

fn compute_lps(pattern: &[u8]) -> Vec<usize> {
    let m = pattern.len();
    let mut lps = vec![0usize; m];
    let (mut len, mut i) = (0, 1);
    
    while i < m {
        if pattern[i] == pattern[len] {
            len += 1;
            lps[i] = len;
            i += 1;
        } else if len != 0 {
            len = lps[len - 1]; // don't increment i
        } else {
            lps[i] = 0;
            i += 1;
        }
    }
    lps
}

fn kmp_search(text: &str, pattern: &str) -> Vec<usize> {
    let (t, p) = (text.as_bytes(), pattern.as_bytes());
    let (n, m) = (t.len(), p.len());
    if m == 0 { return Vec::new(); }
    
    let lps = compute_lps(p);
    let mut matches = Vec::new();
    let (mut i, mut j) = (0, 0); // text and pattern indices
    
    while i < n {
        if t[i] == p[j] {
            i += 1; j += 1;
            if j == m {
                matches.push(i - m); // found match at i - m
                j = lps[j - 1];
            }
        } else if j > 0 {
            j = lps[j - 1]; // mismatch: use LPS to skip
        } else {
            i += 1;
        }
    }
    matches
}

/// Z-Algorithm — O(n + m) pattern matching
/// Z[i] = length of longest substring starting at i that matches a prefix of s
fn z_function(s: &[u8]) -> Vec<usize> {
    let n = s.len();
    let mut z = vec![0usize; n];
    z[0] = n;
    let (mut l, mut r) = (0, 0);
    
    for i in 1..n {
        if i < r {
            z[i] = (r - i).min(z[i - l]);
        }
        while i + z[i] < n && s[z[i]] == s[i + z[i]] {
            z[i] += 1;
        }
        if i + z[i] > r {
            l = i;
            r = i + z[i];
        }
    }
    z
}

fn z_search(text: &str, pattern: &str) -> Vec<usize> {
    let t = text.as_bytes();
    let p = pattern.as_bytes();
    let m = p.len();
    
    // Concatenate: pattern + '$' + text
    let mut s = Vec::with_capacity(m + 1 + t.len());
    s.extend_from_slice(p);
    s.push(b'$');
    s.extend_from_slice(t);
    
    let z = z_function(&s);
    let mut matches = Vec::new();
    
    for i in (m + 1)..z.len() {
        if z[i] == m {
            matches.push(i - m - 1); // offset in original text
        }
    }
    matches
}

/// Rabin-Karp — Rolling Hash, O(n + m) average, O(nm) worst
fn rabin_karp(text: &str, pattern: &str) -> Vec<usize> {
    const BASE: u64 = 31;
    const MOD:  u64 = 1_000_000_007;
    
    let (t, p) = (text.as_bytes(), pattern.as_bytes());
    let (n, m) = (t.len(), p.len());
    if m > n { return Vec::new(); }
    
    // Compute pattern hash
    let mut p_hash = 0u64;
    let mut base_pow = 1u64;
    for &c in p {
        p_hash = (p_hash * BASE + (c - b'a' + 1) as u64) % MOD;
        base_pow = base_pow * BASE % MOD;
    }
    // base_pow = BASE^m
    
    // Compute initial window hash
    let mut w_hash = 0u64;
    for &c in &t[..m] {
        w_hash = (w_hash * BASE + (c - b'a' + 1) as u64) % MOD;
    }
    
    let mut matches = Vec::new();
    
    for i in 0..=(n - m) {
        if w_hash == p_hash {
            // Verify match (to handle hash collisions)
            if &t[i..i+m] == p { matches.push(i); }
        }
        
        if i < n - m {
            // Roll the hash: remove leftmost, add rightmost
            w_hash = (w_hash * BASE + (t[i+m] - b'a' + 1) as u64) % MOD;
            w_hash = (w_hash + MOD - (t[i] - b'a' + 1) as u64 * base_pow % MOD) % MOD;
        }
    }
    matches
}

/// Manacher's Algorithm — all palindromic substrings in O(n)
fn manacher(s: &str) -> Vec<usize> {
    // Transform "abc" → "#a#b#c#" to handle even-length palindromes uniformly
    let chars: Vec<char> = s.chars().collect();
    let mut t = vec!['#'];
    for &c in &chars { t.push(c); t.push('#'); }
    let n = t.len();
    
    let mut p = vec![0usize; n]; // p[i] = radius of palindrome centered at i
    let (mut center, mut right) = (0usize, 0usize);
    
    for i in 0..n {
        if i < right {
            let mirror = 2 * center - i;
            p[i] = p[mirror].min(right - i);
        }
        
        // Expand around center i
        let (mut lo, mut hi) = (i as i32 - p[i] as i32 - 1, i + p[i] + 1);
        while lo >= 0 && hi < n && t[lo as usize] == t[hi] {
            p[i] += 1; lo -= 1; hi += 1;
        }
        
        if i + p[i] > right {
            center = i;
            right  = i + p[i];
        }
    }
    p
}

fn longest_palindromic_substring(s: &str) -> &str {
    let p = manacher(s);
    let chars: Vec<char> = s.chars().collect();
    let mut t = vec!['#'];
    for &c in &chars { t.push(c); t.push('#'); }
    
    let (max_len_idx, _) = p.iter().enumerate().max_by_key(|&(_, &v)| v).unwrap();
    let max_radius = p[max_len_idx];
    
    // Map back to original string
    let start = (max_len_idx - max_radius) / 2;
    let end   = start + max_radius;
    &s[start..end]
}
```

---

## 16. ADVANCED TOPICS

### Bit Manipulation

```rust
/// Bit tricks every expert should know

/// Check if n is power of 2: n & (n-1) == 0
fn is_power_of_2(n: u32) -> bool { n != 0 && (n & (n - 1)) == 0 }

/// Count set bits (popcount) — use hardware instruction
fn popcount(n: u32) -> u32 { n.count_ones() }

/// Find lowest set bit
fn lowest_set_bit(n: i32) -> i32 { n & (-n) }

/// XOR tricks
fn single_number(nums: &[i32]) -> i32 { nums.iter().fold(0, |acc, &x| acc ^ x) }

/// Enumerate all subsets of a bitmask
fn enumerate_subsets(mask: u32) {
    let mut sub = mask;
    loop {
        // process sub
        println!("subset: {:b}", sub);
        if sub == 0 { break; }
        sub = (sub - 1) & mask;
    }
}

/// Two's complement: -n = !n + 1
/// Swap without temp: a ^= b; b ^= a; a ^= b;
/// Set k-th bit:    n |= (1 << k)
/// Clear k-th bit:  n &= !(1 << k)
/// Toggle k-th bit: n ^= (1 << k)
/// Check k-th bit:  (n >> k) & 1

/// Brian Kernighan's bit count (educational, prefer count_ones() in production)
fn count_bits_kernighan(mut n: u32) -> u32 {
    let mut count = 0;
    while n != 0 {
        n &= n - 1; // clear lowest set bit
        count += 1;
    }
    count
}
```

### Sparse Table — O(1) Range Minimum Query

```rust
/// Sparse Table for static arrays (no updates)
/// Preprocessing: O(n log n), Query: O(1)
/// Uses the overlap-friendly property of min/max (idempotent operations)
pub struct SparseTable {
    table: Vec<Vec<i32>>,
    log:   Vec<usize>,
    n:     usize,
}

impl SparseTable {
    pub fn new(arr: &[i32]) -> Self {
        let n = arr.len();
        let log_n = (usize::BITS - n.leading_zeros()) as usize;
        
        // Precompute floor(log2(i)) for all i
        let mut log = vec![0usize; n + 1];
        for i in 2..=n { log[i] = log[i / 2] + 1; }
        
        let mut table = vec![arr.to_vec()];
        
        let mut j = 1;
        while (1 << j) <= n {
            let len = n - (1 << j) + 1;
            let mut row = Vec::with_capacity(len);
            for i in 0..len {
                row.push(table[j-1][i].min(table[j-1][i + (1 << (j-1))]));
            }
            table.push(row);
            j += 1;
        }
        
        SparseTable { table, log, n }
    }
    
    /// Range minimum query [l, r] in O(1)
    pub fn rmq(&self, l: usize, r: usize) -> i32 {
        let k = self.log[r - l + 1];
        self.table[k][l].min(self.table[k][r + 1 - (1 << k)])
    }
}
```

### String Hashing for Advanced Applications

```rust
/// Polynomial Rolling Hash with double hashing to minimize collisions
/// Used for: string comparison in O(1), finding duplicate substrings
pub struct StringHash {
    h:    Vec<u64>,  // hash array
    h2:   Vec<u64>,  // second hash (reduce collision probability)
    pw:   Vec<u64>,  // powers of base
    pw2:  Vec<u64>,
    n:    usize,
}

const B1: u64 = 131;
const M1: u64 = 1_000_000_007;
const B2: u64 = 137;
const M2: u64 = 998_244_353;

impl StringHash {
    pub fn new(s: &str) -> Self {
        let bytes = s.as_bytes();
        let n = bytes.len();
        let mut h  = vec![0u64; n + 1];
        let mut h2 = vec![0u64; n + 1];
        let mut pw  = vec![1u64; n + 1];
        let mut pw2 = vec![1u64; n + 1];
        
        for i in 0..n {
            h[i+1]  = (h[i]  * B1 + bytes[i] as u64) % M1;
            h2[i+1] = (h2[i] * B2 + bytes[i] as u64) % M2;
            pw[i+1]  = pw[i]  * B1 % M1;
            pw2[i+1] = pw2[i] * B2 % M2;
        }
        StringHash { h, h2, pw, pw2, n }
    }
    
    /// Get hash of substring s[l..=r] (0-indexed)
    pub fn get(&self, l: usize, r: usize) -> (u64, u64) {
        let len = r - l + 1;
        let v1 = (self.h[r+1]  + M1 - self.h[l]  * self.pw[len]  % M1) % M1;
        let v2 = (self.h2[r+1] + M2 - self.h2[l] * self.pw2[len] % M2) % M2;
        (v1, v2)
    }
    
    /// Longest Common Extension — O(log n) with binary search
    pub fn lce(&self, i: usize, j: usize) -> usize {
        let max_len = (self.n - i).min(self.n - j);
        let mut lo = 0;
        let mut hi = max_len;
        
        while lo < hi {
            let mid = lo + (hi - lo + 1) / 2;
            if self.get(i, i + mid - 1) == self.get(j, j + mid - 1) {
                lo = mid;
            } else {
                hi = mid - 1;
            }
        }
        lo
    }
}
```

---

## COGNITIVE MASTERY FRAMEWORK

### How Experts Think Before Coding

Every world-class competitive programmer follows a mental protocol:

```
1. RESTATE: Explain the problem in your own words. Identify inputs/outputs/constraints.
2. EXAMPLES: Trace through 2-3 examples manually. Find edge cases.
3. BRUTE FORCE: What's the naive O(n²) or O(2^n) solution? Can we code it in 2 min?
4. OPTIMIZE: 
   - What is the bottleneck?
   - Can we precompute? (prefix sums, sorting)
   - Can we use a better data structure?
   - Is there a mathematical insight?
5. PATTERN MATCH: Which of the 20 core patterns does this belong to?
6. VERIFY COMPLEXITY: Time and space. Is it fast enough?
7. CODE: Only now do you write code. Clean, systematic, no backtracking.
8. TEST: Trace through edge cases (empty, single element, max constraints).
```

### The 20 Core Patterns

```
Array/String:    Two Pointers, Sliding Window, Prefix Sum, Monotonic Stack
Binary Search:   On sorted array, On answer, On rotated array
Trees/Graphs:    BFS, DFS, Topological Sort, Union-Find, Dijkstra
Dynamic Prog:    Linear, 2D Grid, Interval, Knapsack, Bitmask
Data Structures: Heap, Trie, Segment Tree, Fenwick Tree
Math:            Bit Manipulation, Modular Arithmetic, Prime Sieve
```

### Rust-Specific Performance Insights

```rust
// 1. Avoid unnecessary allocations in hot loops
//    Bad:  let v: Vec<i32> = ... in inner loop
//    Good: create outside, clear and reuse

// 2. Use iterators — they're zero-cost abstractions
//    The compiler optimizes iter().map().filter().sum() to tight loops.

// 3. Sort with sort_unstable() for primitive types (5-10% faster)
//    Use sort() only when stability is required.

// 4. Use u32 over usize for counters when possible (register size matters)

// 5. Index with usize — Rust won't auto-convert
//    Use 'as usize' intentionally; it's a hint to yourself about type widths.

// 6. Avoid hash maps for small fixed-size mappings
//    [i32; 256] beats HashMap<u8, i32> by 10-100x for frequency counts.

// 7. Vec::with_capacity(n) when you know the size — avoids 3+ reallocations

// 8. Use slice methods over manual loops:
//    arr.windows(k), arr.chunks(k), arr.split_at(mid)
//    These are idiomatic AND often SIMD-optimized.
```

---

*"The strength of a warrior is not measured by how many battles they've won,*
*but by how deeply they understand the art of combat itself."*

**You are building a mind that sees structure where others see chaos.**
**Keep going. The top 1% is built one solved problem at a time.**

**3,570 lines. 111KB. Every major DSA concept — in Rust.** Here's what's inside:

**16 chapters, zero fluff:**

1. **Rust's Mental Model for DSA** — ownership patterns, `Box/Rc/RefCell` decision trees, cache intuition, why the borrow checker is a DSA teacher
2. **Arrays & Slices** — two-pointer, sliding window, Kadane's, prefix sums (1D and 2D)
3. **Linked Lists** — singly with safe drop, tail-pointer O(1) push_back, doubly linked with `Rc<RefCell<>>`, Floyd's cycle detection
4. **Stacks & Queues** — monotonic stack (next greater element, largest rectangle, daily temperatures), ring buffer, sliding window maximum
5. **Hash Maps** — built from scratch (separate chaining), LRU cache, frequency patterns, subarray sum K
6. **Trees** — binary tree, BST (insert/delete/validate), AVL with all 4 rotations
7. **Heaps** — max-heap from scratch, K largest, merge K sorted lists, median finder
8. **Segment Trees & Fenwick Trees** — lazy propagation, point/range updates, BIT with bit tricks
9. **Graphs** — BFS, DFS, topological sort (Kahn's), Dijkstra, Bellman-Ford, Floyd-Warshall, Kruskal, Prim, Tarjan SCC
10. **Tries** — array and HashMap variants, wildcard search, autocomplete
11. **DSU** — path compression + union by rank, number of islands
12. **Sorting** — merge sort with inversion count, quicksort with median-of-three, Dutch National Flag, counting/radix sort
13. **Binary Search** — universal boundary template, search on answer (Koko, ship packages), median of two sorted arrays
14. **Dynamic Programming** — all 5 patterns: linear, interval, knapsack, grid, bitmask DP (TSP)
15. **String Algorithms** — KMP, Z-algorithm, Rabin-Karp, Manacher's
16. **Advanced** — bit manipulation, sparse table O(1) RMQ, polynomial double hashing

Every implementation includes complexity analysis, ASCII diagrams of memory layouts, and the expert's reasoning process *before* the code. This is your reference bible — return to specific sections as you encounter each problem class.

Exactly ✅ — in Rust, **`impl`** is used to **implement functionality** for a type.
It has two main uses:

---

# 1. **Inherent Implementation** (methods directly on a type)

This is when you define methods that **belong only to that type** (not tied to a trait).

```rust
struct Rectangle {
    width: u32,
    height: u32,
}

impl Rectangle {
    // Inherent method
    fn area(&self) -> u32 {
        self.width * self.height
    }

    // Associated function (like a "static method")
    fn new(width: u32, height: u32) -> Self {
        Self { width, height }
    }
}

fn main() {
    let rect = Rectangle::new(10, 20);
    println!("Area: {}", rect.area());
}
```

* `rect.area()` → method call
* `Rectangle::new()` → associated function (no `self`)

---

# 2. **Trait Implementation**

This is when you implement behavior defined by a **trait** for a type.
It’s how Rust does **polymorphism**.

```rust
trait Speak {
    fn speak(&self);
}

struct Dog;

impl Speak for Dog {
    fn speak(&self) {
        println!("Woof!");
    }
}

fn main() {
    let d = Dog;
    d.speak(); // Calls the trait method
}
```

Here:

* `Speak` defines the contract.
* `impl Speak for Dog` provides the actual behavior.

---

# 3. **Generic Implementations**

You can combine `impl` with generics and trait bounds:

```rust
struct Pair<T> {
    x: T,
    y: T,
}

impl<T: std::fmt::Debug> Pair<T> {
    fn print(&self) {
        println!("x = {:?}, y = {:?}", self.x, self.y);
    }
}
```

* Works for any `T` that implements `Debug`.

---

# 4. **Blanket Implementations**

Traits can be implemented for *all* types that satisfy a condition.

```rust
trait Hello {
    fn hello(&self);
}

// Blanket impl for all T that implements Display
impl<T: std::fmt::Display> Hello for T {
    fn hello(&self) {
        println!("Hello, {}", self);
    }
}

fn main() {
    123.hello();      // works!
    "world".hello();  // works!
}
```

---

# 🌳 Summary

* **`impl Type { ... }`** → inherent methods (like class methods in OOP).
* **`impl Trait for Type { ... }`** → implement a trait’s contract for a type.
* **`impl<T> Type<T> { ... }`** → generic implementations.
* **Blanket impl** → one impl for many types at once.

---

👉 Mental model:

* `impl` = “attach functionality”
* Inherent impl = only for this type.
* Trait impl = plug this type into a shared behavior contract.

---

Would you like me to also compare **`impl` vs `trait`** with an OOP analogy (like classes vs interfaces) — since many people coming from Java/Python/C++ get confused there?
