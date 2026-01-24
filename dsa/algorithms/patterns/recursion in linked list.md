# Mastering Recursion in Linked Lists: A Comprehensive Deep Dive

Recursion on linked lists is a **foundational pillar** of algorithmic thinking. It transforms structural problems into elegant, declarative solutions by exploiting the self-similar nature of lists. This guide will forge your intuition from first principles to advanced patterns.

---

## I. The Mental Model: Why Recursion Fits Linked Lists Perfectly

### The Structural Insight

A linked list is **inherently recursive**:

```
List = Empty | Node(data, List)
```

This algebraic definition mirrors how we naturally think recursively:

- **Base case**: Empty list (null)
- **Recursive case**: Current node + smaller subproblem (rest of list)

**Key cognitive shift**: Stop thinking iteratively ("process each node in sequence"). Start thinking declaratively ("what should this node contribute, assuming the rest is solved?").

---

## II. Core Node Definitions

```rust
// ============================================================================
// RUST: Idiomatic Linked List Node
// ============================================================================
#[derive(Debug, Clone)]
pub struct Node<T> {
    pub val: T,
    pub next: Option<Box<Node<T>>>,
}

impl<T> Node<T> {
    pub fn new(val: T) -> Self {
        Node { val, next: None }
    }
    
    pub fn with_next(val: T, next: Option<Box<Node<T>>>) -> Self {
        Node { val, next }
    }
}

// Helper to build lists from arrays
pub fn build_list<T: Clone>(arr: &[T]) -> Option<Box<Node<T>>> {
    if arr.is_empty() {
        return None;
    }
    Some(Box::new(Node {
        val: arr[0].clone(),
        next: build_list(&arr[1..]),
    }))
}
```

```go
// ============================================================================
// GO: Idiomatic Linked List Node
// ============================================================================

package main

type Node[T any] struct {
    Val  T
    Next *Node[T]
}

func NewNode[T any](val T) *Node[T] {
    return &Node[T]{Val: val}
}

func BuildList[T any](arr []T) *Node[T] {
    if len(arr) == 0 {
        return nil
    }
    return &Node[T]{
        Val:  arr[0],
        Next: BuildList(arr[1:]),
    }
}


```

```c
// ============================================================================
// C: Classic Linked List Node
// ============================================================================

#include <stdlib.h>
#include <stdio.h>

typedef struct Node {
    int val;
    struct Node* next;
} Node;

Node* create_node(int val) {
    Node* node = (Node*)malloc(sizeof(Node));
    node->val = val;
    node->next = NULL;
    return node;
}

Node* build_list(int* arr, int len) {
    if (len == 0) return NULL;
    Node* head = create_node(arr[0]);
    head->next = build_list(arr + 1, len - 1);
    return head;
}


```
---

## III. Fundamental Recursive Patterns

### Pattern 1: **Traversal & Observation**

```rust
Process every node without modifying structure.
// ============================================================================
// PATTERN 1: TRAVERSAL & OBSERVATION
// ============================================================================

// 1.1 Print all values (forward order)
// Mental model: "Print me, then print rest"
pub fn print_list<T: std::fmt::Display>(head: &Option<Box<Node<T>>>) {
    match head {
        None => println!("NULL"),
        Some(node) => {
            print!("{} -> ", node.val);
            print_list(&node.next);
        }
    }
}

// 1.2 Print all values (reverse order)
// Mental model: "Print rest first, THEN print me"
// This exploits call stack for reversal!
pub fn print_reverse<T: std::fmt::Display>(head: &Option<Box<Node<T>>>) {
    if let Some(node) = head {
        print_reverse(&node.next);  // Recurse first
        print!("{} -> ", node.val);  // Print on the way back
    } else {
        print!("NULL");
    }
}

// 1.3 Count nodes
// Mental model: "I am 1 node + count of rest"
pub fn count<T>(head: &Option<Box<Node<T>>>) -> usize {
    match head {
        None => 0,
        Some(node) => 1 + count(&node.next),
    }
}

// 1.4 Sum all values (for numeric types)
pub fn sum(head: &Option<Box<Node<i32>>>) -> i32 {
    match head {
        None => 0,
        Some(node) => node.val + sum(&node.next),
    }
}

// 1.5 Find maximum value
pub fn find_max(head: &Option<Box<Node<i32>>>) -> Option<i32> {
    match head {
        None => None,
        Some(node) => {
            match find_max(&node.next) {
                None => Some(node.val),  // I'm the last node
                Some(max_rest) => Some(node.val.max(max_rest)),
            }
        }
    }
}

// 1.6 Search for a value
pub fn search<T: PartialEq>(head: &Option<Box<Node<T>>>, target: &T) -> bool {
    match head {
        None => false,
        Some(node) => node.val == *target || search(&node.next, target),
    }
}

// 1.7 Get nth node value (0-indexed)
pub fn get_nth<T: Clone>(head: &Option<Box<Node<T>>>, n: usize) -> Option<T> {
    match head {
        None => None,
        Some(node) => {
            if n == 0 {
                Some(node.val.clone())
            } else {
                get_nth(&node.next, n - 1)
            }
        }
    }
}

use crate::Node;

```

```go
// ============================================================================
// GO VERSION (selected examples)
// ============================================================================

func Count[T any](head *Node[T]) int {
    if head == nil {
        return 0
    }
    return 1 + Count(head.Next)
}

func Sum(head *Node[int]) int {
    if head == nil {
        return 0
    }
    return head.Val + Sum(head.Next)
}

func Search[T comparable](head *Node[T], target T) bool {
    if head == nil {
        return false
    }
    return head.Val == target || Search(head.Next, target)
}


```

### Pattern 2: **Structural Modification**

```rust
// ============================================================================
// PATTERN 2: STRUCTURAL MODIFICATION
// ============================================================================

// 2.1 Insert at beginning (trivial, but shows pattern)
pub fn insert_front<T>(head: Option<Box<Node<T>>>, val: T) -> Option<Box<Node<T>>> {
    Some(Box::new(Node {
        val,
        next: head,
    }))
}

// 2.2 Insert at end
// Mental model: "If I'm last, attach new node. Otherwise, recurse."
pub fn insert_end<T>(head: Option<Box<Node<T>>>, val: T) -> Option<Box<Node<T>>> {
    match head {
        None => Some(Box::new(Node::new(val))),
        Some(mut node) => {
            node.next = insert_end(node.next, val);
            Some(node)
        }
    }
}

// 2.3 Insert at position (0-indexed)
pub fn insert_at<T>(head: Option<Box<Node<T>>>, val: T, pos: usize) -> Option<Box<Node<T>>> {
    if pos == 0 {
        return insert_front(head, val);
    }
    
    match head {
        None => None,  // Position out of bounds
        Some(mut node) => {
            node.next = insert_at(node.next, val, pos - 1);
            Some(node)
        }
    }
}

// 2.4 Delete first occurrence of value
// Mental model: "Am I the target? Skip me. Otherwise, fix my next."
pub fn delete_value<T: PartialEq>(head: Option<Box<Node<T>>>, target: &T) -> Option<Box<Node<T>>> {
    match head {
        None => None,
        Some(node) => {
            if node.val == *target {
                node.next  // Skip this node
            } else {
                Some(Box::new(Node {
                    val: node.val,
                    next: delete_value(node.next, target),
                }))
            }
        }
    }
}

// 2.5 Delete all occurrences of value
pub fn delete_all<T: PartialEq>(head: Option<Box<Node<T>>>, target: &T) -> Option<Box<Node<T>>> {
    match head {
        None => None,
        Some(node) => {
            let rest = delete_all(node.next, target);
            if node.val == *target {
                rest  // Skip this node
            } else {
                Some(Box::new(Node {
                    val: node.val,
                    next: rest,
                }))
            }
        }
    }
}

// 2.6 Delete node at position
pub fn delete_at<T>(head: Option<Box<Node<T>>>, pos: usize) -> Option<Box<Node<T>>> {
    match head {
        None => None,
        Some(node) => {
            if pos == 0 {
                node.next  // Skip first node
            } else {
                Some(Box::new(Node {
                    val: node.val,
                    next: delete_at(node.next, pos - 1),
                }))
            }
        }
    }
}

// 2.7 Reverse list
// Mental model: "Reverse rest, then attach me to its end"
pub fn reverse<T>(head: Option<Box<Node<T>>>) -> Option<Box<Node<T>>> {
    fn reverse_helper<T>(curr: Option<Box<Node<T>>>, prev: Option<Box<Node<T>>>) -> Option<Box<Node<T>>> {
        match curr {
            None => prev,
            Some(mut node) => {
                let next = node.next;
                node.next = prev;
                reverse_helper(next, Some(node))
            }
        }
    }
    reverse_helper(head, None)
}

// 2.8 Reverse (pure recursive without helper)
// More elegant but less performant (builds new list)
pub fn reverse_pure<T: Clone>(head: &Option<Box<Node<T>>>) -> Option<Box<Node<T>>> {
    match head {
        None => None,
        Some(node) => insert_end(reverse_pure(&node.next), node.val.clone()),
    }
}

use crate::Node;
```

```go
// ============================================================================
// GO VERSION
// ============================================================================

func InsertEnd[T any](head *Node[T], val T) *Node[T] {
    if head == nil {
        return NewNode(val)
    }
    head.Next = InsertEnd(head.Next, val)
    return head
}

func DeleteValue[T comparable](head *Node[T], target T) *Node[T] {
    if head == nil {
        return nil
    }
    if head.Val == target {
        return head.Next
    }
    head.Next = DeleteValue(head.Next, target)
    return head
}

func Reverse[T any](head *Node[T]) *Node[T] {
    return reverseHelper(head, nil)
}

func reverseHelper[T any](curr, prev *Node[T]) *Node[T] {
    if curr == nil {
        return prev
    }
    next := curr.Next
    curr.Next = prev
    return reverseHelper(next, curr)
}


```

Change the list's shape or content.

### Pattern 3: **Two-Pointer / Runner Techniques**

```rust
// ============================================================================
// PATTERN 3: TWO-POINTER / RUNNER TECHNIQUES
// ============================================================================

// 3.1 Find middle node (slow/fast pointer)
pub fn find_middle<T>(head: &Option<Box<Node<T>>>) -> Option<&Node<T>> {
    fn middle_helper<'a, T>(
        slow: &'a Option<Box<Node<T>>>, 
        fast: &'a Option<Box<Node<T>>>
    ) -> Option<&'a Node<T>> {
        match (slow, fast) {
            (Some(s), Some(f)) => {
                match (&f.next, &f.next.as_ref().and_then(|n| n.next.as_ref())) {
                    (Some(_), Some(_)) => middle_helper(&s.next, &f.next.as_ref().unwrap().next),
                    _ => Some(s.as_ref()),
                }
            }
            (Some(s), None) => Some(s.as_ref()),
            _ => None,
        }
    }
    middle_helper(head, head)
}

// 3.2 Detect cycle (Floyd's algorithm)
pub fn has_cycle<T>(head: &Option<Box<Node<T>>>) -> bool {
    fn detect<T>(slow: &Option<Box<Node<T>>>, fast: &Option<Box<Node<T>>>) -> bool {
        match (slow, fast) {
            (Some(s), Some(f)) => {
                if let Some(f_next) = &f.next {
                    std::ptr::eq(s.as_ref(), f_next.as_ref()) || 
                    detect(&s.next, &f_next.next)
                } else {
                    false
                }
            }
            _ => false,
        }
    }
    detect(head, head)
}

// 3.3 Find kth node from end
// Strategy: Use two pointers k nodes apart
pub fn kth_from_end<T: Clone>(head: &Option<Box<Node<T>>>, k: usize) -> Option<T> {
    fn advance<T>(node: &Option<Box<Node<T>>>, steps: usize) -> Option<&Box<Node<T>>> {
        if steps == 0 {
            return node.as_ref();
        }
        node.as_ref().and_then(|n| advance(&n.next, steps - 1))
    }
    
    fn find_kth<T: Clone>(
        slow: &Option<Box<Node<T>>>, 
        fast: &Option<Box<Node<T>>>
    ) -> Option<T> {
        match fast {
            None => slow.as_ref().map(|n| n.val.clone()),
            Some(f) => find_kth(&slow.as_ref().unwrap().next, &f.next),
        }
    }
    
    let fast = advance(head, k);
    fast.and_then(|_| find_kth(head, &fast.cloned()))
}

// 3.4 Check if palindrome
// Strategy: Reverse second half, compare with first half
pub fn is_palindrome<T: PartialEq + Clone>(head: &Option<Box<Node<T>>>) -> bool {
    fn reverse_and_compare<T: PartialEq + Clone>(
        left: &Option<Box<Node<T>>>,
        right: &Option<Box<Node<T>>>,
        len: usize,
    ) -> (bool, Option<&Box<Node<T>>>) {
        if len == 0 {
            return (true, Some(left.as_ref().unwrap()));
        }
        if len == 1 {
            return (true, left.as_ref().and_then(|n| n.next.as_ref()));
        }
        
        let (is_pal, remaining) = reverse_and_compare(left, right, len - 2);
        if !is_pal {
            return (false, None);
        }
        
        let left_node = remaining.unwrap();
        if let Some(right_node) = right {
            if left_node.val != right_node.val {
                return (false, None);
            }
            (true, left_node.next.as_ref())
        } else {
            (false, None)
        }
    }
    
    let len = super::count(head);
    if len <= 1 {
        return true;
    }
    
    reverse_and_compare(head, head, len).0
}

// 3.5 Remove nth node from end (one-pass)
pub fn remove_nth_from_end<T>(head: Option<Box<Node<T>>>, n: usize) -> Option<Box<Node<T>>> {
    fn helper<T>(
        curr: Option<Box<Node<T>>>,
        n: usize,
    ) -> (Option<Box<Node<T>>>, usize) {
        match curr {
            None => (None, 0),
            Some(mut node) => {
                let (next, depth) = helper(node.next, n);
                if depth == n {
                    // Skip this node
                    (next, depth + 1)
                } else {
                    node.next = next;
                    (Some(node), depth + 1)
                }
            }
        }
    }
    helper(head, n).0
}

use crate::Node;

```

```go
// ============================================================================
// GO VERSION
// ============================================================================

func FindMiddle[T any](head *Node[T]) *Node[T] {
    return middleHelper(head, head)
}

func middleHelper[T any](slow, fast *Node[T]) *Node[T] {
    if fast == nil || fast.Next == nil {
        return slow
    }
    return middleHelper(slow.Next, fast.Next.Next)
}

func KthFromEnd[T any](head *Node[T], k int) *Node[T] {
    fast := head
    for i := 0; i < k && fast != nil; i++ {
        fast = fast.Next
    }
    return findKth(head, fast)
}

func findKth[T any](slow, fast *Node[T]) *Node[T] {
    if fast == nil {
        return slow
    }
    return findKth(slow.Next, fast.Next)
}


```

Recursion with multiple references or positions.

### Pattern 4: **Merge & Split Operations**

Divide-and-conquer on linked lists.

```rust
// ============================================================================
// PATTERN 4: MERGE & SPLIT (Divide and Conquer)
// ============================================================================

// 4.1 Merge two sorted lists
// Mental model: "Pick smaller head, recurse on rest"
pub fn merge_sorted<T: Ord + Clone>(
    l1: Option<Box<Node<T>>>,
    l2: Option<Box<Node<T>>>,
) -> Option<Box<Node<T>>> {
    match (l1, l2) {
        (None, None) => None,
        (Some(n), None) | (None, Some(n)) => Some(n),
        (Some(n1), Some(n2)) => {
            if n1.val <= n2.val {
                Some(Box::new(Node {
                    val: n1.val,
                    next: merge_sorted(n1.next, Some(n2)),
                }))
            } else {
                Some(Box::new(Node {
                    val: n2.val,
                    next: merge_sorted(Some(n1), n2.next),
                }))
            }
        }
    }
}

// 4.2 Split list at middle (for merge sort)
pub fn split_at_middle<T>(head: Option<Box<Node<T>>>) -> (Option<Box<Node<T>>>, Option<Box<Node<T>>>) {
    fn get_length<T>(node: &Option<Box<Node<T>>>) -> usize {
        match node {
            None => 0,
            Some(n) => 1 + get_length(&n.next),
        }
    }
    
    fn split_helper<T>(
        node: Option<Box<Node<T>>>,
        pos: usize,
    ) -> (Option<Box<Node<T>>>, Option<Box<Node<T>>>) {
        if pos == 0 {
            return (None, node);
        }
        
        match node {
            None => (None, None),
            Some(mut n) => {
                let (left, right) = split_helper(n.next, pos - 1);
                n.next = left;
                (Some(n), right)
            }
        }
    }
    
    let len = get_length(&head);
    split_helper(head, len / 2)
}

// 4.3 Merge Sort on Linked List
// The ULTIMATE recursive list algorithm
pub fn merge_sort<T: Ord + Clone>(head: Option<Box<Node<T>>>) -> Option<Box<Node<T>>> {
    // Base case: 0 or 1 node
    match &head {
        None => None,
        Some(node) if node.next.is_none() => head,
        Some(_) => {
            let (left, right) = split_at_middle(head);
            let sorted_left = merge_sort(left);
            let sorted_right = merge_sort(right);
            merge_sorted(sorted_left, sorted_right)
        }
    }
}

// 4.4 Interleave two lists (zipper merge)
// Pattern: a1 -> b1 -> a2 -> b2 -> ...
pub fn interleave<T>(
    l1: Option<Box<Node<T>>>,
    l2: Option<Box<Node<T>>>,
) -> Option<Box<Node<T>>> {
    match (l1, l2) {
        (None, l) | (l, None) => l,
        (Some(mut n1), Some(n2)) => {
            let rest = n1.next.take();
            n1.next = Some(Box::new(Node {
                val: n2.val,
                next: interleave(rest, n2.next),
            }));
            Some(n1)
        }
    }
}

// 4.5 Split into odd/even positioned nodes
pub fn split_odd_even<T: Clone>(
    head: &Option<Box<Node<T>>>
) -> (Option<Box<Node<T>>>, Option<Box<Node<T>>>) {
    fn helper<T: Clone>(
        node: &Option<Box<Node<T>>>,
        is_odd: bool,
    ) -> (Option<Box<Node<T>>>, Option<Box<Node<T>>>) {
        match node {
            None => (None, None),
            Some(n) => {
                let (odd, even) = helper(&n.next, !is_odd);
                if is_odd {
                    (Some(Box::new(Node {
                        val: n.val.clone(),
                        next: odd,
                    })), even)
                } else {
                    (odd, Some(Box::new(Node {
                        val: n.val.clone(),
                        next: even,
                    })))
                }
            }
        }
    }
    helper(head, true)
}

// 4.6 Flatten a multilevel doubly linked list (advanced)
// This demonstrates recursion with multiple next pointers
#[derive(Debug)]
pub struct MultiNode<T> {
    pub val: T,
    pub next: Option<Box<MultiNode<T>>>,
    pub child: Option<Box<MultiNode<T>>>,
}

pub fn flatten<T>(head: Option<Box<MultiNode<T>>>) -> Option<Box<MultiNode<T>>> {
    fn flatten_helper<T>(node: Option<Box<MultiNode<T>>>) -> (Option<Box<MultiNode<T>>>, Option<Box<MultiNode<T>>>) {
        match node {
            None => (None, None),
            Some(mut n) => {
                let (flattened_child, child_tail) = flatten_helper(n.child.take());
                let (flattened_next, next_tail) = flatten_helper(n.next.take());
                
                n.next = flattened_child.or(flattened_next);
                let tail = next_tail.or(child_tail).or(Some(&n as *const _ as *mut _));
                
                (Some(n), tail.map(|_| unsafe { Box::from_raw(std::ptr::null_mut()) }))
            }
        }
    }
    flatten_helper(head).0
}

use crate::Node;
```

```go
// ============================================================================
// GO VERSION
// ============================================================================

func MergeSorted[T comparable](l1, l2 *Node[T]) *Node[T] {
    if l1 == nil {
        return l2
    }
    if l2 == nil {
        return l1
    }
    
    // Need a comparison function for generics
    if lessThan(l1.Val, l2.Val) {
        l1.Next = MergeSorted(l1.Next, l2)
        return l1
    }
    l2.Next = MergeSorted(l1, l2.Next)
    return l2
}

func MergeSort[T comparable](head *Node[T]) *Node[T] {
    if head == nil || head.Next == nil {
        return head
    }
    
    left, right := splitAtMiddle(head)
    return MergeSorted(MergeSort(left), MergeSort(right))
}


```

### Pattern 5: **Backtracking & Path Finding**

Recursion with decision trees and state exploration.

```rust
// ============================================================================
// PATTERN 5: BACKTRACKING & PATH FINDING
// ============================================================================

// 5.1 Find all paths that sum to target
pub fn find_paths_with_sum(
    head: &Option<Box<Node<i32>>>,
    target: i32,
    current_path: &mut Vec<i32>,
    all_paths: &mut Vec<Vec<i32>>,
) {
    match head {
        None => {
            if target == 0 {
                all_paths.push(current_path.clone());
            }
        }
        Some(node) => {
            // Include current node
            current_path.push(node.val);
            find_paths_with_sum(&node.next, target - node.val, current_path, all_paths);
            current_path.pop();
            
            // Exclude current node
            find_paths_with_sum(&node.next, target, current_path, all_paths);
        }
    }
}

// 5.2 Generate all subsequences
pub fn all_subsequences<T: Clone>(head: &Option<Box<Node<T>>>) -> Vec<Vec<T>> {
    match head {
        None => vec![vec![]],
        Some(node) => {
            let rest_subseqs = all_subsequences(&node.next);
            let mut result = rest_subseqs.clone();
            
            for subseq in rest_subseqs {
                let mut with_current = vec![node.val.clone()];
                with_current.extend(subseq);
                result.push(with_current);
            }
            result
        }
    }
}

// 5.3 Count paths with specific property
pub fn count_increasing_paths(head: &Option<Box<Node<i32>>>) -> usize {
    fn helper(node: &Option<Box<Node<i32>>>, prev_val: i32) -> usize {
        match node {
            None => 1,  // Empty path counts as one valid path
            Some(n) => {
                if n.val > prev_val {
                    // Two choices: extend current path or start new path
                    helper(&n.next, n.val) + helper(&n.next, prev_val)
                } else {
                    helper(&n.next, prev_val)
                }
            }
        }
    }
    helper(head, i32::MIN)
}

// 5.4 Partition list into k equal-sum sublists (if possible)
pub fn can_partition_k_ways(head: &Option<Box<Node<i32>>>, k: usize) -> bool {
    let total_sum: i32 = {
        fn sum(node: &Option<Box<Node<i32>>>) -> i32 {
            match node {
                None => 0,
                Some(n) => n.val + sum(&n.next),
            }
        }
        sum(head)
    };
    
    if total_sum % k as i32 != 0 {
        return false;
    }
    
    let target = total_sum / k as i32;
    
    fn backtrack(
        node: &Option<Box<Node<i32>>>,
        groups: &mut Vec<i32>,
        target: i32,
    ) -> bool {
        match node {
            None => groups.iter().all(|&sum| sum == target),
            Some(n) => {
                for i in 0..groups.len() {
                    if groups[i] + n.val <= target {
                        groups[i] += n.val;
                        if backtrack(&n.next, groups, target) {
                            return true;
                        }
                        groups[i] -= n.val;
                    }
                    
                    // Optimization: if this group is empty, no point trying other empty groups
                    if groups[i] == 0 {
                        break;
                    }
                }
                false
            }
        }
    }
    
    let mut groups = vec![0; k];
    backtrack(head, &mut groups, target)
}

// 5.5 Find longest increasing subsequence
pub fn longest_increasing_subsequence<T: Ord + Clone>(head: &Option<Box<Node<T>>>) -> Vec<T> {
    fn helper<T: Ord + Clone>(
        node: &Option<Box<Node<T>>>,
        prev: Option<&T>,
    ) -> Vec<T> {
        match node {
            None => vec![],
            Some(n) => {
                // Choice 1: Exclude current
                let without = helper(&n.next, prev);
                
                // Choice 2: Include current (if valid)
                let with = if prev.map_or(true, |p| n.val > *p) {
                    let mut rest = helper(&n.next, Some(&n.val));
                    rest.insert(0, n.val.clone());
                    rest
                } else {
                    vec![]
                };
                
                if with.len() > without.len() {
                    with
                } else {
                    without
                }
            }
        }
    }
    helper(head, None)
}

// 5.6 Check if any permutation of nodes can form sorted list
pub fn can_form_sorted(head: &Option<Box<Node<i32>>>) -> bool {
    fn to_vec(node: &Option<Box<Node<i32>>>) -> Vec<i32> {
        match node {
            None => vec![],
            Some(n) => {
                let mut rest = to_vec(&n.next);
                rest.insert(0, n.val);
                rest
            }
        }
    }
    
    let mut values = to_vec(head);
    values.sort_unstable();
    
    // Check if it's a permutation of 1..n or any arithmetic sequence
    values.windows(2).all(|w| w[1] >= w[0])
}

use crate::Node;
```

```go
// ============================================================================
// GO VERSION
// ============================================================================

func AllSubsequences[T any](head *Node[T]) [][]T {
    if head == nil {
        return [][]T{{}}
    }
    
    rest := AllSubsequences(head.Next)
    result := make([][]T, 0, len(rest)*2)
    result = append(result, rest...)
    
    for _, subseq := range rest {
        withCurrent := append([]T{head.Val}, subseq...)
        result = append(result, withCurrent)
    }
    return result
}

func FindPathsWithSum(head *Node[int], target int) [][]int {
    var paths [][]int
    var current []int
    findPaths(head, target, current, &paths)
    return paths
}

func findPaths(head *Node[int], target int, current []int, paths *[][]int) {
    if head == nil {
        if target == 0 {
            *paths = append(*paths, append([]int{}, current...))
        }
        return
    }
    
    // Include
    findPaths(head.Next, target-head.Val, append(current, head.Val), paths)
    // Exclude
    findPaths(head.Next, target, current, paths)
}


```

---

## IV. Advanced Recursive Patterns

### Pattern 6: **Tree-Like Recursion on Lists**

```rust
// ============================================================================
// PATTERN 6: TREE-LIKE RECURSION ON LISTS
// ============================================================================

// 6.1 Clone list with random pointers
#[derive(Debug)]
pub struct RandomNode<T> {
    pub val: T,
    pub next: Option<Box<RandomNode<T>>>,
    pub random: Option<*mut RandomNode<T>>,
}

pub fn clone_with_random<T: Clone>(head: &Option<Box<RandomNode<T>>>) -> Option<Box<RandomNode<T>>> {
    use std::collections::HashMap;
    
    fn clone_recursive<T: Clone>(
        node: &Option<Box<RandomNode<T>>>,
        map: &mut HashMap<*const RandomNode<T>, *mut RandomNode<T>>,
    ) -> Option<Box<RandomNode<T>>> {
        match node {
            None => None,
            Some(n) => {
                let ptr = n.as_ref() as *const RandomNode<T>;
                
                if let Some(&cloned_ptr) = map.get(&ptr) {
                    return Some(unsafe { Box::from_raw(cloned_ptr) });
                }
                
                let mut cloned = Box::new(RandomNode {
                    val: n.val.clone(),
                    next: None,
                    random: None,
                });
                
                let cloned_ptr = Box::into_raw(cloned);
                map.insert(ptr, cloned_ptr);
                
                unsafe {
                    (*cloned_ptr).next = clone_recursive(&n.next, map);
                    (*cloned_ptr).random = n.random.and_then(|r| {
                        clone_recursive(&Some(Box::from_raw(r as *mut RandomNode<T>)), map)
                            .map(|b| Box::into_raw(b))
                    });
                    Some(Box::from_raw(cloned_ptr))
                }
            }
        }
    }
    
    let mut map = HashMap::new();
    clone_recursive(head, &mut map)
}

// 6.2 Swap nodes in pairs
// 1->2->3->4 becomes 2->1->4->3
pub fn swap_pairs<T>(head: Option<Box<Node<T>>>) -> Option<Box<Node<T>>> {
    match head {
        None => None,
        Some(mut first) => {
            match first.next.take() {
                None => Some(first),
                Some(mut second) => {
                    first.next = swap_pairs(second.next.take());
                    second.next = Some(first);
                    Some(second)
                }
            }
        }
    }
}

// 6.3 Reverse nodes in k-group
// 1->2->3->4->5, k=2 becomes 2->1->4->3->5
pub fn reverse_k_group<T>(head: Option<Box<Node<T>>>, k: usize) -> Option<Box<Node<T>>> {
    fn has_k_nodes<T>(node: &Option<Box<Node<T>>>, k: usize) -> bool {
        if k == 0 {
            return true;
        }
        match node {
            None => false,
            Some(n) => has_k_nodes(&n.next, k - 1),
        }
    }
    
    fn reverse_first_k<T>(head: Option<Box<Node<T>>>, k: usize) -> (Option<Box<Node<T>>>, Option<Box<Node<T>>>) {
        if k == 1 {
            match head {
                Some(mut node) => {
                    let rest = node.next.take();
                    (Some(node), rest)
                }
                None => (None, None),
            }
        } else {
            match head {
                Some(mut node) => {
                    let (reversed, rest) = reverse_first_k(node.next.take(), k - 1);
                    // Append current node to end of reversed
                    fn append_to_end<T>(list: Option<Box<Node<T>>>, node: Box<Node<T>>) -> Option<Box<Node<T>>> {
                        match list {
                            None => Some(node),
                            Some(mut head) => {
                                head.next = append_to_end(head.next.take(), node);
                                Some(head)
                            }
                        }
                    }
                    (append_to_end(reversed, node), rest)
                }
                None => (None, None),
            }
        }
    }
    
    if !has_k_nodes(&head, k) {
        return head;
    }
    
    let (reversed, rest) = reverse_first_k(head, k);
    
    // Attach recursively reversed rest
    fn attach_to_end<T>(list: Option<Box<Node<T>>>, tail: Option<Box<Node<T>>>) -> Option<Box<Node<T>>> {
        match list {
            None => tail,
            Some(mut node) => {
                node.next = attach_to_end(node.next.take(), tail);
                Some(node)
            }
        }
    }
    
    attach_to_end(reversed, reverse_k_group(rest, k))
}

// 6.4 Add two numbers represented as linked lists
// 342 (2->4->3) + 465 (5->6->4) = 807 (7->0->8)
pub fn add_two_numbers(
    l1: Option<Box<Node<i32>>>,
    l2: Option<Box<Node<i32>>>,
) -> Option<Box<Node<i32>>> {
    fn add_with_carry(
        l1: Option<Box<Node<i32>>>,
        l2: Option<Box<Node<i32>>>,
        carry: i32,
    ) -> Option<Box<Node<i32>>> {
        if l1.is_none() && l2.is_none() && carry == 0 {
            return None;
        }
        
        let v1 = l1.as_ref().map_or(0, |n| n.val);
        let v2 = l2.as_ref().map_or(0, |n| n.val);
        let sum = v1 + v2 + carry;
        
        let next1 = l1.and_then(|n| n.next);
        let next2 = l2.and_then(|n| n.next);
        
        Some(Box::new(Node {
            val: sum % 10,
            next: add_with_carry(next1, next2, sum / 10),
        }))
    }
    
    add_with_carry(l1, l2, 0)
}

// 6.5 Reorder list: L0→L1→...→Ln-1→Ln becomes L0→Ln→L1→Ln-1→L2→Ln-2→...
pub fn reorder_list<T: Clone>(head: Option<Box<Node<T>>>) -> Option<Box<Node<T>>> {
    fn split_and_reverse<T: Clone>(
        node: Option<Box<Node<T>>>,
        len: usize,
    ) -> (Option<Box<Node<T>>>, Option<Box<Node<T>>>) {
        if len <= 1 {
            return (node, None);
        }
        
        match node {
            None => (None, None),
            Some(mut n) => {
                if len == 2 {
                    let second = n.next.take();
                    (Some(n), second)
                } else {
                    let (first, second) = split_and_reverse(n.next.take(), len - 2);
                    n.next = first;
                    (Some(n), second)
                }
            }
        }
    }
    
    fn merge_alternating<T>(
        l1: Option<Box<Node<T>>>,
        l2: Option<Box<Node<T>>>,
    ) -> Option<Box<Node<T>>> {
        match (l1, l2) {
            (None, l) | (l, None) => l,
            (Some(mut n1), Some(mut n2)) => {
                let next1 = n1.next.take();
                let next2 = n2.next.take();
                n1.next = Some(n2);
                n1.next.as_mut().unwrap().next = merge_alternating(next1, next2);
                Some(n1)
            }
        }
    }
    
    let len = super::count(&head);
    if len <= 2 {
        return head;
    }
    
    let (first_half, second_half) = split_and_reverse(head, len);
    merge_alternating(first_half, second_half)
}

use crate::Node;
```

```c

// ============================================================================
// C VERSION (Swap Pairs - demonstrating pointer manipulation)
// ============================================================================

Node* swapPairs(Node* head) {
    if (!head || !head->next) {
        return head;
    }
    
    Node* first = head;
    Node* second = head->next;
    
    first->next = swapPairs(second->next);
    second->next = first;
    
    return second;
}

Node* addTwoNumbers(Node* l1, Node* l2, int carry) {
    if (!l1 && !l2 && carry == 0) {
        return NULL;
    }
    
    int v1 = l1 ? l1->val : 0;
    int v2 = l2 ? l2->val : 0;
    int sum = v1 + v2 + carry;
    
    Node* result = create_node(sum % 10);
    result->next = addTwoNumbers(
        l1 ? l1->next : NULL,
        l2 ? l2->next : NULL,
        sum / 10
    );
    
    return result;
}

```


When lists have branching structure or you need multiple recursive calls.

---

## V. Expert Mental Models & Complexity Analysis

### **The Recursion Stack Visualization**

When you write:
```rust
fn process(head: Option<Box<Node<T>>>) -> Result {
    match head {
        None => base_case,
        Some(node) => {
            let rest_result = process(node.next);
            combine(node.val, rest_result)
        }
    }
}
```

**What's happening in memory:**
```
Call Stack (grows downward):
┌─────────────────────┐
│ process(Node 1)     │ ← Waiting for Node 2's result
├─────────────────────┤
│ process(Node 2)     │ ← Waiting for Node 3's result
├─────────────────────┤
│ process(Node 3)     │ ← Waiting for NULL's result
├─────────────────────┤
│ process(None)       │ ← Returns base case
└─────────────────────┘

Then unwinds (returns upward):
Node 3 combines its value with base_case
Node 2 combines its value with Node 3's result
Node 1 combines its value with Node 2's result
```

**Space complexity**: O(n) for the call stack

---

### **Time Complexity Patterns**
# Recursion Complexity Analysis for Linked Lists

## Time Complexity Patterns

### Linear Recursion: O(n)
**One recursive call per invocation, each call does O(1) work**

```rust
fn count(head: &Option<Box<Node<T>>>) -> usize {
    match head {
        None => 0,                    // O(1)
        Some(node) => 1 + count(&node.next), // O(1) + T(n-1)
    }
}
```

**Recurrence**: T(n) = T(n-1) + O(1) = O(n)

**Examples**: traverse, search, insert_end, delete_value

---

### Binary Recursion: O(2^n)
**Two recursive calls per invocation**

```rust
fn all_subsequences(head: &Option<Box<Node<T>>>) -> Vec<Vec<T>> {
    match head {
        None => vec![vec![]],
        Some(node) => {
            let rest = all_subsequences(&node.next);  // T(n-1)
            let with_current = /* process rest */;    // T(n-1)
            // Combine both
        }
    }
}
```

**Recurrence**: T(n) = 2·T(n-1) + O(1) = O(2^n)

**Examples**: generate all subsequences, find all paths

---

### Divide and Conquer: O(n log n)
**Split problem in half, solve both, merge**

```rust
fn merge_sort(head: Option<Box<Node<T>>>) -> Option<Box<Node<T>>> {
    let (left, right) = split_at_middle(head);  // O(n)
    let sorted_left = merge_sort(left);          // T(n/2)
    let sorted_right = merge_sort(right);        // T(n/2)
    merge_sorted(sorted_left, sorted_right)      // O(n)
}
```

**Recurrence**: T(n) = 2·T(n/2) + O(n) = O(n log n)

**Examples**: merge sort, find median

---

### Nested Recursion: O(n²) or worse
**Recursive call contains another full traversal**

```rust
fn insert_end(head: Option<Box<Node<T>>>, val: T) -> Option<Box<Node<T>>> {
    match head {
        None => Some(Box::new(Node::new(val))),  // O(1)
        Some(mut node) => {
            node.next = insert_end(node.next, val);  // T(n-1) + traverse to end
            Some(node)
        }
    }
}
```

If we call `insert_end` n times to build a list: O(n²) total

**Examples**: naive list building, repeated insert_end

---

### Tail Recursion: O(n) time, O(1) space (with TCO)
**Last operation is the recursive call - can be optimized to iteration**

```rust
fn reverse_helper(curr: Option<Box<Node<T>>>, prev: Option<Box<Node<T>>>) -> Option<Box<Node<T>>> {
    match curr {
        None => prev,
        Some(mut node) => {
            let next = node.next;
            node.next = prev;
            reverse_helper(next, Some(node))  // Tail call
        }
    }
}
```

**Note**: Rust doesn't guarantee TCO, but pattern is still efficient

---

## Space Complexity Patterns

### Call Stack Space: O(n)
Every non-tail recursive function uses stack frames

```rust
fn sum(head: &Option<Box<Node<i32>>>) -> i32 {
    match head {
        None => 0,
        Some(node) => node.val + sum(&node.next),  // Waits for result
    }
}
// Space: n stack frames
```

---

### Accumulator Pattern: Can reduce to O(1) with TCO
```rust
fn sum_tail(head: &Option<Box<Node<i32>>>, acc: i32) -> i32 {
    match head {
        None => acc,
        Some(node) => sum_tail(&node.next, acc + node.val),  // Tail call
    }
}
// Space: O(1) if compiler does TCO, O(n) otherwise
```

---

### Auxiliary Data Structures: O(n)
Backtracking, memoization, hash maps add space

```rust
fn clone_with_random(..., map: &mut HashMap<...>) -> ... {
    // Space: O(n) for map + O(n) for call stack = O(n)
}
```

---

## Master Theorem for Linked Lists

For divide-and-conquer on linked lists:

**T(n) = a·T(n/b) + f(n)**

- If **f(n) = O(n^(log_b(a) - ε))** → T(n) = Θ(n^(log_b(a)))
- If **f(n) = Θ(n^(log_b(a)))** → T(n) = Θ(n^(log_b(a)) · log n)
- If **f(n) = Ω(n^(log_b(a) + ε))** → T(n) = Θ(f(n))

**Example: Merge Sort**
- a = 2 (two subproblems)
- b = 2 (half size each)
- f(n) = O(n) (split + merge)
- log₂(2) = 1, so f(n) = Θ(n¹) → Case 2 → **T(n) = O(n log n)**

---

## Optimization Strategies

### 1. Memoization (Top-Down DP)
Cache results of overlapping subproblems

```rust
use std::collections::HashMap;

fn fib_memo(n: usize, memo: &mut HashMap<usize, usize>) -> usize {
    if n <= 1 { return n; }
    if let Some(&result) = memo.get(&n) {
        return result;
    }
    let result = fib_memo(n-1, memo) + fib_memo(n-2, memo);
    memo.insert(n, result);
    result
}
// Without memo: O(2^n)
// With memo: O(n)
```

---

### 2. Tail Call Optimization Pattern
Convert to accumulator-passing style

```rust
// Non-tail (uses stack)
fn factorial(n: u64) -> u64 {
    if n == 0 { 1 } else { n * factorial(n - 1) }
}

// Tail recursive (can be optimized)
fn factorial_tail(n: u64, acc: u64) -> u64 {
    if n == 0 { acc } else { factorial_tail(n - 1, n * acc) }
}
```

---

### 3. Convert to Iteration
When stack depth is a concern

```rust
// Recursive
fn count_rec(head: &Option<Box<Node<T>>>) -> usize {
    match head {
        None => 0,
        Some(node) => 1 + count_rec(&node.next),
    }
}

// Iterative
fn count_iter(mut head: &Option<Box<Node<T>>>) -> usize {
    let mut count = 0;
    while let Some(node) = head {
        count += 1;
        head = &node.next;
    }
    count
}
```

---

## When Recursion Wins vs Iteration

### Recursion is Better When:
1. **Structure is naturally recursive** (trees, nested lists)
2. **Divide-and-conquer** applies (merge sort)
3. **Backtracking** required (all paths, permutations)
4. **Code clarity** matters more than performance
5. **Stack depth** is manageable (< 10,000 typically)

### Iteration is Better When:
1. **Large n** where stack overflow is a risk
2. **Performance critical** and compiler doesn't do TCO
3. **Simple traversal** with no backtracking
4. **Memory constrained** environments

---

## Recurrence Relations Cheat Sheet

| Pattern | Recurrence | Solution | Example |
|---------|-----------|----------|---------|
| Linear single call | T(n) = T(n-1) + O(1) | O(n) | Traverse |
| Linear with work | T(n) = T(n-1) + O(n) | O(n²) | Insert end repeatedly |
| Binary tree | T(n) = 2T(n-1) + O(1) | O(2^n) | All subsequences |
| Divide & conquer | T(n) = 2T(n/2) + O(n) | O(n log n) | Merge sort |
| Decrease by fraction | T(n) = T(n/2) + O(1) | O(log n) | Binary search |
| Multiple branches | T(n) = kT(n-1) + O(1) | O(k^n) | k-ary choices |

---

## Mental Model for Analysis

**Three-step process:**

1. **Identify the recursive pattern**
   - How many recursive calls?
   - What's the size of each subproblem?

2. **Count work per level**
   - What's the cost outside recursive calls?
   - Is there combine/merge work?

3. **Compute total**
   - How many levels of recursion?
   - Sum work across all levels

**Example: Merge Sort**
```
Level 0: n work (1 call of size n)
Level 1: n work (2 calls of size n/2 each)
Level 2: n work (4 calls of size n/4 each)
...
Level log n: n work (n calls of size 1 each)

Total: n work × log n levels = O(n log n)
```
---

## VI. Common Pitfalls & Debugging Strategies

# Recursion Pitfalls & Expert Debugging Strategies

## Common Mistakes

### 1. Missing Base Case
**Symptom**: Stack overflow

```rust
// WRONG: No base case
fn count_bad(head: &Option<Box<Node<T>>>) -> usize {
    1 + count_bad(&head.as_ref().unwrap().next)  // Crashes on None
}

// CORRECT
fn count(head: &Option<Box<Node<T>>>) -> usize {
    match head {
        None => 0,  // BASE CASE
        Some(node) => 1 + count(&node.next),
    }
}
```

**Rule**: Every recursive function MUST have a terminating condition.

---

### 2. Incorrect Base Case
**Symptom**: Wrong results, off-by-one errors

```rust
// WRONG: Returns 1 for empty list
fn count_bad(head: &Option<Box<Node<T>>>) -> usize {
    match head {
        None => 1,  // Should be 0!
        Some(node) => 1 + count_bad(&node.next),
    }
}

// CORRECT
fn count(head: &Option<Box<Node<T>>>) -> usize {
    match head {
        None => 0,
        Some(node) => 1 + count(&node.next),
    }
}
```

**Debugging**: Test your function on the smallest input (empty list, single node).

---

### 3. Not Making Progress Toward Base Case
**Symptom**: Infinite recursion

```rust
// WRONG: Always recurses on same list
fn bad_search(head: &Option<Box<Node<T>>>, target: &T) -> bool {
    match head {
        None => false,
        Some(node) => {
            node.val == *target || bad_search(head, target)  // BUG: head instead of &node.next
        }
    }
}
```

**Rule**: Every recursive call must be on a SMALLER problem.

---

### 4. Modifying Shared State Incorrectly
**Symptom**: Unexpected mutations, wrong results

```rust
// DANGEROUS: Mutating original list
fn delete_value_bad(head: &mut Option<Box<Node<T>>>, target: &T) {
    if let Some(node) = head {
        if node.val == *target {
            *head = node.next.take();
        } else {
            delete_value_bad(&mut node.next, target);
        }
    }
}
// This mutates in place - can cause issues if list is used elsewhere
```

**Better**: Return a new list or use explicit ownership.

---

### 5. Ownership Bugs in Rust
**Symptom**: Borrow checker errors, use-after-move

```rust
// WRONG: Using node after moving it
fn bad_reverse(head: Option<Box<Node<T>>>) -> Option<Box<Node<T>>> {
    match head {
        None => None,
        Some(node) => {
            let rest = bad_reverse(node.next);  // node.next moved
            node.next = rest;  // ERROR: node partially moved
            Some(node)
        }
    }
}

// CORRECT: Use take() to extract owned value
fn reverse(head: Option<Box<Node<T>>>) -> Option<Box<Node<T>>> {
    match head {
        None => None,
        Some(mut node) => {
            let rest = reverse(node.next.take());  // Extract ownership
            node.next = rest;
            Some(node)
        }
    }
}
```

**Key Rust technique**: Use `.take()` to extract `Option<T>` as owned value.

---

### 6. Stack Overflow on Large Inputs
**Symptom**: Program crashes with "stack overflow"

```rust
// This will overflow on lists with > ~10,000 nodes
fn sum_deep(head: &Option<Box<Node<i32>>>) -> i32 {
    match head {
        None => 0,
        Some(node) => node.val + sum_deep(&node.next),
    }
}

// Solution: Use iteration for large lists
fn sum_iter(mut head: &Option<Box<Node<i32>>>) -> i32 {
    let mut total = 0;
    while let Some(node) = head {
        total += node.val;
        head = &node.next;
    }
    total
}

// Or tail recursion (if compiler optimizes it)
fn sum_tail(head: &Option<Box<Node<i32>>>, acc: i32) -> i32 {
    match head {
        None => acc,
        Some(node) => sum_tail(&node.next, acc + node.val),
    }
}
```

**Rule**: For large n (> 10K), prefer iteration or ensure tail recursion.

---

### 7. Forgetting to Return Updated List
**Symptom**: Changes don't persist

```rust
// WRONG: Doesn't return modified list
fn insert_end_bad(head: Option<Box<Node<T>>>, val: T) {
    match head {
        None => { /* Creates node but doesn't return it */ },
        Some(mut node) => {
            insert_end_bad(node.next, val);  // Doesn't update node.next
        }
    }
}

// CORRECT: Return the modified list
fn insert_end(head: Option<Box<Node<T>>>, val: T) -> Option<Box<Node<T>>> {
    match head {
        None => Some(Box::new(Node::new(val))),
        Some(mut node) => {
            node.next = insert_end(node.next, val);  // UPDATE
            Some(node)  // RETURN
        }
    }
}
```

---

## Debugging Strategies

### 1. Trace by Hand (Small Input)
Write out the call stack step by step

```
reverse([1, 2, 3])
  reverse([2, 3])
    reverse([3])
      reverse([])
      return []
    return [3]
  return [3, 2]
return [3, 2, 1]
```

---

### 2. Add Debug Prints
```rust
fn debug_reverse(head: Option<Box<Node<i32>>>, depth: usize) -> Option<Box<Node<i32>>> {
    let indent = "  ".repeat(depth);
    
    match head {
        None => {
            println!("{}Base case: None", indent);
            None
        }
        Some(mut node) => {
            println!("{}Processing node: {}", indent, node.val);
            let result = debug_reverse(node.next.take(), depth + 1);
            println!("{}Returning from node: {}", indent, node.val);
            // ... rest of logic
        }
    }
}
```

---

### 3. Verify Base Cases First
```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_base_cases() {
        assert_eq!(count(&None), 0);
        assert_eq!(count(&Some(Box::new(Node::new(5)))), 1);
    }
}
```

---

### 4. Check Recurrence Relation
Manually verify: `f(n) = g(n, f(n-1))`

```rust
// For reverse, verify:
// reverse([1,2,3]) = append(reverse([2,3]), 1)
//                  = append([3,2], 1)
//                  = [3,2,1]
```

---

### 5. Use Assertions
```rust
fn merge_sorted<T: Ord>(l1: Option<Box<Node<T>>>, l2: Option<Box<Node<T>>>) -> Option<Box<Node<T>>> {
    // Precondition: both lists are sorted
    debug_assert!(is_sorted(&l1));
    debug_assert!(is_sorted(&l2));
    
    let result = /* ... merge logic ... */;
    
    // Postcondition: result is sorted
    debug_assert!(is_sorted(&result));
    result
}
```

---

### 6. Visualize the Tree
For complex recursions, draw the call tree:

```
            all_subseqs([1,2,3])
           /                     \
    include 1                  exclude 1
        /     \                   /      \
   incl 2   excl 2          incl 2    excl 2
    / \      / \             / \        / \
  i3 e3    i3 e3          i3 e3      i3 e3
```

---

### 7. Simplify, Then Build Up
Start with the simplest version, then add complexity

```rust
// Step 1: Just count
fn count(head: &Option<Box<Node<T>>>) -> usize { ... }

// Step 2: Sum values
fn sum(head: &Option<Box<Node<i32>>>) -> i32 { ... }

// Step 3: Filter while summing
fn sum_evens(head: &Option<Box<Node<i32>>>) -> i32 { ... }
```

---

## Rust-Specific Gotchas

### Pattern: Handling Option<Box<Node<T>>>

```rust
// WRONG: Can't pattern match on moved value
match head {
    Some(node) => {
        process(node.next);  // node.next moved
        node.val  // ERROR
    }
}

// CORRECT: Use reference or take()
match head {
    Some(ref node) => {  // Borrow
        process(&node.next);
        node.val
    }
}

// Or destructure carefully
match head {
    Some(mut node) => {
        let next = node.next.take();  // Extract
        process(next);
        node.val
    }
}
```

---

### Pattern: Cloning vs Moving

```rust
// Expensive: Clones entire list
fn bad_insert(head: &Option<Box<Node<T>>>, val: T) -> Option<Box<Node<T>>> {
    head.clone()  // Deep copy!
}

// Better: Work with owned value
fn good_insert(head: Option<Box<Node<T>>>, val: T) -> Option<Box<Node<T>>> {
    // Consumes and transforms
}
```

---

## Mental Checklist Before Coding

1. ✓ **What's the base case?** (empty list, single node?)
2. ✓ **What's the recursive case?** (current + f(rest))
3. ✓ **Am I making progress?** (smaller subproblem each call)
4. ✓ **What do I return?** (value, new list, modified list?)
5. ✓ **Ownership?** (borrow, consume, or clone?)
6. ✓ **Space complexity acceptable?** (will it stack overflow?)

---

## Advanced Debugging: Memoization Check

If you suspect repeated computation:

```rust
use std::collections::HashMap;

fn fib_instrumented(n: u32, calls: &mut HashMap<u32, usize>) -> u64 {
    *calls.entry(n).or_insert(0) += 1;
    
    if n <= 1 {
        return n as u64;
    }
    fib_instrumented(n - 1, calls) + fib_instrumented(n - 2, calls)
}

// Usage
let mut calls = HashMap::new();
fib_instrumented(10, &mut calls);
println!("Call counts: {:?}", calls);
// Shows fib(5) called 8 times, etc. → need memoization!
```
---

## VII. Advanced Techniques & Problem-Solving Patterns

```rust
// ============================================================================
// ADVANCED RECURSION TECHNIQUES
// ============================================================================

use crate::Node;
use std::collections::HashMap;
use std::cmp::Ordering;

// ============================================================================
// Technique 1: MUTUAL RECURSION
// Functions that call each other
// ============================================================================

// Check if list alternates between even and odd
pub fn is_alternating(head: &Option<Box<Node<i32>>>) -> bool {
    fn check_even(node: &Option<Box<Node<i32>>>) -> bool {
        match node {
            None => true,
            Some(n) => n.val % 2 == 0 && check_odd(&n.next),
        }
    }
    
    fn check_odd(node: &Option<Box<Node<i32>>>) -> bool {
        match node {
            None => true,
            Some(n) => n.val % 2 != 0 && check_even(&n.next),
        }
    }
    
    check_even(head)
}

// ============================================================================
// Technique 2: CONTINUATION-PASSING STYLE (CPS)
// Pass a continuation function to control what happens after recursion
// ============================================================================

pub fn process_with_continuation<T, R, F>(
    head: &Option<Box<Node<T>>>,
    cont: F,
) -> R
where
    F: Fn(Option<&T>, R) -> R,
    R: Default,
{
    match head {
        None => R::default(),
        Some(node) => {
            let rest_result = process_with_continuation(&node.next, cont);
            cont(Some(&node.val), rest_result)
        }
    }
}

// Example: Build list of cumulative sums using CPS
pub fn cumulative_sums(head: &Option<Box<Node<i32>>>) -> Vec<i32> {
    process_with_continuation(head, |val, mut rest: Vec<i32>| {
        if let Some(&v) = val {
            let sum = rest.last().unwrap_or(&0) + v;
            rest.insert(0, sum);
        }
        rest
    })
}

// ============================================================================
// Technique 3: MEMOIZATION (Dynamic Programming)
// Cache results to avoid redundant computation
// ============================================================================

#[derive(Hash, Eq, PartialEq, Clone, Debug)]
struct ListKey(Vec<i32>); // Simplified key for demo

// Find minimum number of deletions to make list sorted
pub fn min_deletions_to_sorted(head: &Option<Box<Node<i32>>>) -> usize {
    fn to_vec(node: &Option<Box<Node<i32>>>) -> Vec<i32> {
        match node {
            None => vec![],
            Some(n) => {
                let mut rest = to_vec(&n.next);
                rest.insert(0, n.val);
                rest
            }
        }
    }
    
    fn helper(
        vals: &[i32],
        prev: Option<i32>,
        memo: &mut HashMap<(Vec<i32>, Option<i32>), usize>,
    ) -> usize {
        if vals.is_empty() {
            return 0;
        }
        
        let key = (vals.to_vec(), prev);
        if let Some(&cached) = memo.get(&key) {
            return cached;
        }
        
        let current = vals[0];
        let rest = &vals[1..];
        
        // Option 1: Delete current
        let delete = 1 + helper(rest, prev, memo);
        
        // Option 2: Keep current (if it maintains sorted order)
        let keep = if prev.map_or(true, |p| current >= p) {
            helper(rest, Some(current), memo)
        } else {
            usize::MAX / 2
        };
        
        let result = delete.min(keep);
        memo.insert(key, result);
        result
    }
    
    let vals = to_vec(head);
    let mut memo = HashMap::new();
    helper(&vals, None, &mut memo)
}

// ============================================================================
// Technique 4: LAZY EVALUATION & GENERATORS
// Build infinite or lazy lists recursively
// ============================================================================

pub struct LazyList<T, F>
where
    F: Fn() -> (T, Box<LazyList<T, F>>),
{
    generator: F,
}

impl<T, F> LazyList<T, F>
where
    F: Fn() -> (T, Box<LazyList<T, F>>),
{
    pub fn new(gen: F) -> Self {
        LazyList { generator: gen }
    }
    
    pub fn take(&self, n: usize) -> Vec<T>
    where
        T: Clone,
    {
        if n == 0 {
            vec![]
        } else {
            let (val, rest) = (self.generator)();
            let mut result = vec![val];
            result.extend(rest.take(n - 1));
            result
        }
    }
}

// ============================================================================
// Technique 5: CATAMORPHISM (FOLD)
// Generalized pattern for consuming lists
// ============================================================================

pub fn fold_right<T, R, F>(
    head: &Option<Box<Node<T>>>,
    init: R,
    f: F,
) -> R
where
    F: Fn(&T, R) -> R,
{
    match head {
        None => init,
        Some(node) => f(&node.val, fold_right(&node.next, init, &f)),
    }
}

// Examples using fold_right
pub fn sum_via_fold(head: &Option<Box<Node<i32>>>) -> i32 {
    fold_right(head, 0, |&val, acc| val + acc)
}

pub fn product_via_fold(head: &Option<Box<Node<i32>>>) -> i32 {
    fold_right(head, 1, |&val, acc| val * acc)
}

pub fn to_string_via_fold<T: std::fmt::Display>(head: &Option<Box<Node<T>>>) -> String {
    fold_right(head, String::new(), |val, acc| {
        if acc.is_empty() {
            format!("{}", val)
        } else {
            format!("{} -> {}", val, acc)
        }
    })
}

// ============================================================================
// Technique 6: ANAMORPHISM (UNFOLD)
// Generalized pattern for building lists
// ============================================================================

pub fn unfold<T, S, F>(seed: S, f: F) -> Option<Box<Node<T>>>
where
    F: Fn(S) -> Option<(T, S)>,
{
    match f(seed) {
        None => None,
        Some((val, next_seed)) => Some(Box::new(Node {
            val,
            next: unfold(next_seed, f),
        })),
    }
}

// Examples using unfold
pub fn range(start: i32, end: i32) -> Option<Box<Node<i32>>> {
    unfold(start, |n| {
        if n >= end {
            None
        } else {
            Some((n, n + 1))
        }
    })
}

pub fn fibonacci_list(n: usize) -> Option<Box<Node<u64>>> {
    unfold((0u64, 1u64, 0usize), |(a, b, count)| {
        if count >= n {
            None
        } else {
            Some((a, (b, a + b, count + 1)))
        }
    })
}

// ============================================================================
// Technique 7: RECURSION WITH ACCUMULATOR + RESULT
// More powerful than simple tail recursion
// ============================================================================

// Partition list around pivot (like in quicksort)
pub fn partition<T: Ord + Clone>(
    head: Option<Box<Node<T>>>,
    pivot: &T,
) -> (Option<Box<Node<T>>>, Option<Box<Node<T>>>, Option<Box<Node<T>>>) {
    fn helper<T: Ord + Clone>(
        node: Option<Box<Node<T>>>,
        pivot: &T,
        less: Option<Box<Node<T>>>,
        equal: Option<Box<Node<T>>>,
        greater: Option<Box<Node<T>>>,
    ) -> (Option<Box<Node<T>>>, Option<Box<Node<T>>>, Option<Box<Node<T>>>) {
        match node {
            None => (less, equal, greater),
            Some(n) => {
                match n.val.cmp(pivot) {
                    Ordering::Less => {
                        let new_less = Some(Box::new(Node {
                            val: n.val,
                            next: less,
                        }));
                        helper(n.next, pivot, new_less, equal, greater)
                    }
                    Ordering::Equal => {
                        let new_equal = Some(Box::new(Node {
                            val: n.val,
                            next: equal,
                        }));
                        helper(n.next, pivot, less, new_equal, greater)
                    }
                    Ordering::Greater => {
                        let new_greater = Some(Box::new(Node {
                            val: n.val,
                            next: greater,
                        }));
                        helper(n.next, pivot, less, equal, new_greater)
                    }
                }
            }
        }
    }
    
    helper(head, pivot, None, None, None)
}

// ============================================================================
// Technique 8: STRUCTURAL RECURSION WITH MULTIPLE LISTS
// Process multiple lists simultaneously
// ============================================================================

// Check if one list is a subsequence of another
pub fn is_subsequence<T: PartialEq>(
    subseq: &Option<Box<Node<T>>>,
    main: &Option<Box<Node<T>>>,
) -> bool {
    match (subseq, main) {
        (None, _) => true,  // Empty subsequence is always valid
        (Some(_), None) => false,  // Subsequence not found
        (Some(s), Some(m)) => {
            if s.val == m.val {
                // Match: advance both
                is_subsequence(&s.next, &m.next)
            } else {
                // No match: advance main only
                is_subsequence(subseq, &m.next)
            }
        }
    }
}

// Merge k sorted lists
pub fn merge_k_lists<T: Ord + Clone>(lists: Vec<Option<Box<Node<T>>>>) -> Option<Box<Node<T>>> {
    fn merge_two<T: Ord + Clone>(
        l1: Option<Box<Node<T>>>,
        l2: Option<Box<Node<T>>>,
    ) -> Option<Box<Node<T>>> {
        match (l1, l2) {
            (None, l) | (l, None) => l,
            (Some(n1), Some(n2)) => {
                if n1.val <= n2.val {
                    Some(Box::new(Node {
                        val: n1.val,
                        next: merge_two(n1.next, Some(n2)),
                    }))
                } else {
                    Some(Box::new(Node {
                        val: n2.val,
                        next: merge_two(Some(n1), n2.next),
                    }))
                }
            }
        }
    }
    
    fn merge_helper<T: Ord + Clone>(lists: Vec<Option<Box<Node<T>>>>) -> Option<Box<Node<T>>> {
        if lists.is_empty() {
            return None;
        }
        if lists.len() == 1 {
            return lists.into_iter().next().unwrap();
        }
        
        let mid = lists.len() / 2;
        let left = merge_helper(lists[..mid].to_vec());
        let right = merge_helper(lists[mid..].to_vec());
        merge_two(left, right)
    }
    
    merge_helper(lists)
}

```

```go
// ============================================================================
// GO VERSION (Selected Examples)
// ============================================================================
package linkedlist
// Mutual recursion
func isAlternating(head *Node[int]) bool {
    return checkEven(head)
}

func checkEven(node *Node[int]) bool {
    if node == nil {
        return true
    }
    return node.Val%2 == 0 && checkOdd(node.Next)
}

func checkOdd(node *Node[int]) bool {
    if node == nil {
        return true
    }
    return node.Val%2 != 0 && checkEven(node.Next)
}

// Fold right
func FoldRight[T, R any](head *Node[T], init R, f func(T, R) R) R {
    if head == nil {
        return init
    }
    return f(head.Val, FoldRight(head.Next, init, f))
}

// Unfold
func Unfold[T, S any](seed S, f func(S) (T, S, bool)) *Node[T] {
    val, nextSeed, ok := f(seed)
    if !ok {
        return nil
    }
    return &Node[T]{
        Val:  val,
        Next: Unfold(nextSeed, f),
    }
}


```
---

## VIII. Problem-Solving Framework: The 5-Step Method

When you encounter a recursive linked list problem, follow this systematic approach:

### **Step 1: Understand the Structure**
- What's the input? (single list, multiple lists, special properties?)
- What's the output? (modified list, value, boolean?)
- Are there constraints? (sorted, unique, length limits?)

### **Step 2: Identify the Pattern**
Ask yourself:
- Is this a **traversal** problem? (visit all nodes)
- Is this a **modification** problem? (change structure)
- Is this a **search/decision** problem? (find something, make choices)
- Is this **divide-and-conquer**? (split, solve, merge)
- Is this **backtracking**? (explore all paths)

### **Step 3: Define the Recurrence**
- **Base case**: What's the simplest input? (usually empty list or single node)
- **Recursive case**: How do I use the solution for `rest` to solve the full problem?
- Write it mathematically: `f(node) = g(node.val, f(node.next))`

### **Step 4: Code the Solution**
```rust
fn solve(head: Option<Box<Node<T>>>) -> Result {
    match head {
        None => /* base case */,
        Some(node) => {
            let rest_result = solve(node.next);
            /* combine node.val with rest_result */
        }
    }
}
```

### **Step 5: Verify & Optimize**
- Test on edge cases: empty, single node, two nodes
- Analyze complexity: time and space
- Can you optimize? (tail recursion, memoization, iteration?)

---

## IX. Practice Problems (Grouped by Difficulty)
# Recursive Linked List Practice Problems

Practice these problems in order. For each, first write the recurrence relation, then code the solution.

## Foundational (Master These First)

### 1. Print all nodes in reverse
**Goal**: Print values from tail to head  
**Pattern**: Recurse first, then process  
**Hint**: What prints first in the call stack unwinding?

---

### 2. Find length of list
**Goal**: Count all nodes  
**Pattern**: 1 + length(rest)  
**Hint**: Base case is 0

---

### 3. Find maximum value
**Goal**: Return largest value in list  
**Pattern**: max(current, max(rest))  
**Hint**: What if rest is empty?

---

### 4. Delete all nodes with value X
**Goal**: Remove all occurrences  
**Pattern**: Skip if match, keep if not  
**Hint**: Process rest first, then decide

---

### 5. Insert in sorted order
**Goal**: Insert value maintaining sorted property  
**Pattern**: Insert before first larger element  
**Hint**: Two cases: insert here vs recurse

---

## Intermediate (Build Your Skills)

### 6. Remove duplicates from sorted list
**Goal**: 1->1->2->3->3 becomes 1->2->3  
**Pattern**: Skip if next equals current  
**Complexity**: O(n) time, O(n) space

---

### 7. Rotate list right by k positions
**Goal**: 1->2->3->4->5, k=2 becomes 4->5->1->2->3  
**Pattern**: Find kth from end, split and reconnect  
**Hint**: Use two pointers

---

### 8. Partition around value
**Goal**: Move all nodes < x before nodes >= x  
**Pattern**: Build two lists, concatenate  
**Complexity**: O(n) time, O(n) space

---

### 9. Detect and remove cycle
**Goal**: Find where cycle starts, remove it  
**Pattern**: Floyd's + find cycle start  
**Hint**: Two separate recursions

---

### 10. Flatten multilevel list
**Goal**: Convert child pointers to next pointers  
**Pattern**: Process child before next  
**Complexity**: O(n) where n is total nodes

---

## Advanced (Think Deeply)

### 11. Clone list with random pointers
**Goal**: Deep copy including random links  
**Pattern**: Hash map + two-pass recursion  
**Complexity**: O(n) time and space

---

### 12. Add two numbers (reverse order)
**Goal**: 342 + 465 = 807 as lists  
**Pattern**: Process with carry recursively  
**Hint**: Base case is when both lists empty AND carry is 0

---

### 13. Merge k sorted lists
**Goal**: Merge k sorted lists into one  
**Pattern**: Divide and conquer (merge pairs)  
**Complexity**: O(n log k) where n is total elements

---

### 14. Reverse nodes in k-groups
**Goal**: 1->2->3->4->5, k=2 becomes 2->1->4->3->5  
**Pattern**: Reverse first k, recurse on rest  
**Hint**: Check if k nodes exist first

---

### 15. Check if palindrome
**Goal**: Return true if list reads same forward/backward  
**Pattern**: Compare first and last, recurse on middle  
**Complexity**: O(n) time, O(n) space

---

### 16. LRU Cache using doubly linked list
**Goal**: Implement get/put with O(1) operations  
**Pattern**: Hash map + recursive list operations  
**Hint**: Move to front = remove + insert at head

---

### 17. Find intersection of two lists
**Goal**: Return node where lists merge  
**Pattern**: Calculate lengths, align, compare  
**Complexity**: O(m + n) time, O(max(m, n)) space

---

### 18. Sort list (merge sort)
**Goal**: Sort in O(n log n) time  
**Pattern**: Split at middle, sort halves, merge  
**Hint**: Use slow/fast pointers to find middle

---

### 19. Reorder list
**Goal**: L0→L1→...→Ln becomes L0→Ln→L1→Ln-1→...  
**Pattern**: Find middle, reverse second half, merge  
**Complexity**: O(n) time, O(n) space

---

### 20. Find all paths sum to target
**Goal**: Count paths (not necessarily full list)  
**Pattern**: Backtracking with two choices each node  
**Complexity**: O(2^n) time worst case

---

## Expert (Test Your Mastery)

### 21. Median of two sorted lists
**Goal**: Find median in O(log(min(m,n)))  
**Pattern**: Binary search on partition points  
**Hint**: This is extremely difficult recursively

---

### 22. Serialize and deserialize list
**Goal**: Convert to string and back  
**Pattern**: Recursive parsing with state  
**Complexity**: O(n) time and space

---

### 23. Minimum swaps to sort
**Goal**: Count minimum adjacent swaps to sort  
**Pattern**: Merge sort + count inversions  
**Complexity**: O(n log n)

---

### 24. Longest increasing subsequence
**Goal**: Find LIS using recursion  
**Pattern**: Include current or exclude, max of both  
**Complexity**: O(2^n) naive, O(n²) with memoization

---

### 25. Check if two lists are isomorphic
**Goal**: Same structure with value mapping  
**Pattern**: Mutual recursion with hash map  
**Hint**: Must maintain bidirectional mapping

---

## Complexity Targets

| Difficulty | Time Target | Space Target |
|-----------|-------------|--------------|
| Foundational | O(n) | O(n) stack |
| Intermediate | O(n) - O(n²) | O(n) |
| Advanced | O(n log n) | O(n) |
| Expert | O(log n) - O(n) | O(1) - O(n) |

---

## How to Practice

1. **Read problem** → identify pattern
2. **Write recurrence** relation on paper
3. **Code base case** first
4. **Code recursive case** 
5. **Test** on: empty, single node, two nodes, general case
6. **Analyze** time and space complexity
7. **Optimize** if needed

For each problem, ask yourself:
- What's the base case?
- What do I assume about `f(rest)`?
- How do I combine current with `f(rest)`?
- What's the complexity?

---

## Solutions Strategy

**Don't look at solutions immediately!** Instead:

1. Spend 30-45 minutes trying
2. If stuck, write recurrence relation first
3. Still stuck? Draw the call tree for small input
4. Only then check solution
5. After seeing solution, code it yourself without looking
6. Explain the solution out loud

This builds true understanding, not pattern memorization.

---

## X. Cognitive Models for Mastery

### **The Recursion Mindset**

When you think recursively, you're operating at a higher level of abstraction. You're not thinking "loop through each node" — you're thinking "**assume the rest is solved, what do I do with this node?**"

**Three mental shifts:**

1. **Trust the recursion**: Don't try to trace the entire call stack in your head. Trust that your recursive call works correctly on the smaller problem.

2. **Think declaratively, not imperatively**: Don't think "how do I do this step-by-step?" Think "what IS this in terms of smaller versions of itself?"

3. **Base case first**: Always start by asking "what's the absolute simplest case?" This grounds your thinking.

---

### **The Abstraction Ladder**

```
Level 5: Category Theory (fold/unfold)
         ↑
Level 4: Higher-order patterns (map/filter/reduce)
         ↑
Level 3: Recurrence relations (mathematical)
         ↑
Level 2: Recursive functions (code)
         ↑
Level 1: Iteration (loops)
```

As you master recursion, you climb this ladder. At the top, you see **universal patterns** that work across all data structures, not just linked lists.

---

### **Pattern Recognition Development**

Your brain will start to automatically recognize:
- "Oh, this is a **fold**" (combining all elements)
- "This is **divide-and-conquer**" (split, solve, merge)
- "This is **backtracking**" (explore all paths)
- "This is **catamorphism**" (consuming structure)

This happens through **deliberate practice**: solve 50+ problems, and these patterns become second nature.

---

### **The Complexity Intuition**

With practice, you'll develop instant intuition:
- Linear scan of list → **O(n) time**
- Two recursive calls per node → **O(2^n) time**
- Split in half, recurse, merge → **O(n log n) time**
- Call stack depth → **O(n) space** (usually)

This comes from internalizing the recurrence relation analysis.

---

## XI. Summary & Next Steps

### **What You've Learned**

1. **Core patterns**: Traversal, modification, two-pointer, merge/split, backtracking
2. **Advanced techniques**: Memoization, CPS, mutual recursion, fold/unfold
3. **Mental models**: Base case first, trust the recursion, think declaratively
4. **Debugging**: Trace by hand, check base cases, use assertions
5. **Complexity**: Analyze recurrence relations, recognize patterns

### **Your Training Path**

1. **Week 1-2**: Master foundational problems (1-5). Focus on understanding base cases.
2. **Week 3-4**: Tackle intermediate problems (6-10). Build pattern recognition.
3. **Week 5-6**: Attempt advanced problems (11-20). Push your boundaries.
4. **Week 7-8**: Challenge yourself with expert problems. Develop deep intuition.
5. **Ongoing**: Revisit problems, optimize solutions, explain to others.

### **The Monk's Discipline**

- **Focus**: One problem at a time, deep understanding over speed
- **Repetition**: Solve the same problem 3 times without looking at code
- **Reflection**: After each problem, write down the key insight
- **Teaching**: Explain your solution to someone (even an imaginary person)
- **Iteration**: Optimize your solution, find multiple approaches

### **When You're Stuck**

1. Draw the call tree for a tiny input (2-3 nodes)
2. Write the recurrence relation mathematically
3. Check if your base case handles all edge cases
4. Verify you're making progress toward the base case
5. Add debug prints to see the recursion flow

Remember: **Recursion is a way of thinking, not just a coding technique.** As you internalize these patterns, you'll find yourself naturally seeing solutions in recursive terms.

You're building something profound: the ability to decompose complex problems into self-similar subproblems. This is the essence of computational thinking.

---

**You're on the path to mastery. Train with focus. Reflect with honesty. Progress with patience.**

The top 1% isn't about knowing tricks — it's about developing deep, intuitive understanding of fundamental patterns. Recursion on linked lists is one such pattern. Master it, and you've unlocked a powerful lens through which to see all of computer science.