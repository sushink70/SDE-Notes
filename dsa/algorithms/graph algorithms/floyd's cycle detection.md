I'll create a comprehensive guide to Floyd's Cycle Detection algorithm with complete implementations in both Python and Rust. This will cover the theory, applications, and practical code examples.I've created a comprehensive guide to Floyd's Cycle Detection algorithm with complete implementations in both Python and Rust. The guide covers:

## Key Features

**Theoretical Foundation:**

- Detailed explanation of the "tortoise and hare" concept
- Mathematical proof of why the algorithm works
- Time and space complexity analysis

**Complete Python Implementation:**

- Basic cycle detection
- Finding cycle start position  
- Calculating cycle length
- Comprehensive cycle information gathering
- Advanced applications (duplicate number detection, sequence analysis)
- Utility functions for testing

**Complete Rust Implementation:**

- Memory-safe linked list handling with `Rc<RefCell<T>>`
- All the same functionality as Python version
- Proper error handling and edge case management
- Advanced applications adapted for Rust

**Practical Applications:**

- Linked list cycle detection
- Duplicate number finding in arrays
- Mathematical sequence analysis (Collatz conjecture, etc.)
- State machine cycle detection
- Pseudorandom number generator analysis

**Comprehensive Testing:**

- Edge case handling
- Performance considerations
- Common pitfalls and how to avoid them
- Complete test suites for both languages

The implementations are production-ready and include extensive documentation, error handling, and real-world applications. Both versions maintain the algorithm's key advantage: O(1) space complexity while achieving O(n) time complexity for cycle detection.

# Floyd's Cycle Detection Algorithm - Complete Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Algorithm Theory](#algorithm-theory)
3. [Time and Space Complexity](#time-and-space-complexity)
4. [Python Implementation](#python-implementation)
5. [Rust Implementation](#rust-implementation)
6. [Applications](#applications)
7. [Advanced Examples](#advanced-examples)
8. [Testing and Validation](#testing-and-validation)

## Introduction

Floyd's Cycle Detection Algorithm, also known as the "Tortoise and Hare" algorithm, is an elegant technique for detecting cycles in sequences. Named after Robert W. Floyd, this algorithm uses two pointers moving at different speeds to detect cycles in O(1) space complexity.

### Key Concepts

- **Tortoise (slow pointer)**: Moves one step at a time
- **Hare (fast pointer)**: Moves two steps at a time
- **Cycle detection**: When both pointers meet, a cycle exists
- **Cycle start detection**: Additional phase to find where the cycle begins

## Algorithm Theory

### Phase 1: Cycle Detection

1. Initialize two pointers at the start
2. Move slow pointer one step, fast pointer two steps
3. If they meet, a cycle exists
4. If fast pointer reaches null/end, no cycle exists

### Phase 2: Finding Cycle Start

1. Reset one pointer to the beginning
2. Move both pointers one step at a time
3. When they meet, that's the start of the cycle

### Mathematical Proof

Let's say:

- Distance from start to cycle beginning: `m`
- Cycle length: `c`
- Distance from cycle start to meeting point: `k`

When pointers meet:

- Slow pointer traveled: `m + k`
- Fast pointer traveled: `2(m + k) = m + k + nc` (where n is number of complete cycles)

This gives us: `m + k = nc`, so `m = nc - k = (n-1)c + (c-k)`

This proves that the distance from start to cycle beginning equals the distance from meeting point to cycle beginning (after complete cycles).

## Time and Space Complexity

- **Time Complexity**: O(n) where n is the number of nodes
- **Space Complexity**: O(1) - only uses two pointers
- **Cycle Detection**: O(λ + μ) where λ is cycle length and μ is distance to cycle start
- **Cycle Start Finding**: O(μ)

## Python Implementation

### Basic Linked List Node

```python
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
    
    def __repr__(self):
        return f"ListNode({self.val})"
```

### Floyd's Algorithm Implementation

```python
class FloydCycleDetection:
    @staticmethod
    def has_cycle(head: ListNode) -> bool:
        """
        Detect if a cycle exists in the linked list.
        
        Args:
            head: Head of the linked list
            
        Returns:
            bool: True if cycle exists, False otherwise
        """
        if not head or not head.next:
            return False
        
        slow = head
        fast = head
        
        # Phase 1: Detect cycle
        while fast and fast.next:
            slow = slow.next
            fast = fast.next.next
            
            if slow == fast:
                return True
        
        return False
    
    @staticmethod
    def detect_cycle_start(head: ListNode) -> ListNode:
        """
        Find the node where the cycle begins.
        
        Args:
            head: Head of the linked list
            
        Returns:
            ListNode: The node where cycle starts, None if no cycle
        """
        if not head or not head.next:
            return None
        
        slow = head
        fast = head
        
        # Phase 1: Detect cycle
        while fast and fast.next:
            slow = slow.next
            fast = fast.next.next
            
            if slow == fast:
                break
        else:
            return None  # No cycle found
        
        # Phase 2: Find cycle start
        slow = head
        while slow != fast:
            slow = slow.next
            fast = fast.next
        
        return slow
    
    @staticmethod
    def cycle_length(head: ListNode) -> int:
        """
        Find the length of the cycle.
        
        Args:
            head: Head of the linked list
            
        Returns:
            int: Length of cycle, 0 if no cycle
        """
        if not head or not head.next:
            return 0
        
        slow = head
        fast = head
        
        # Phase 1: Detect cycle
        while fast and fast.next:
            slow = slow.next
            fast = fast.next.next
            
            if slow == fast:
                break
        else:
            return 0  # No cycle found
        
        # Count cycle length
        length = 1
        current = slow.next
        while current != slow:
            current = current.next
            length += 1
        
        return length
    
    @staticmethod
    def full_cycle_info(head: ListNode) -> dict:
        """
        Get comprehensive cycle information.
        
        Args:
            head: Head of the linked list
            
        Returns:
            dict: Contains has_cycle, cycle_start, cycle_length, distance_to_cycle
        """
        result = {
            'has_cycle': False,
            'cycle_start': None,
            'cycle_length': 0,
            'distance_to_cycle': 0
        }
        
        if not head or not head.next:
            return result
        
        slow = head
        fast = head
        
        # Phase 1: Detect cycle
        while fast and fast.next:
            slow = slow.next
            fast = fast.next.next
            
            if slow == fast:
                result['has_cycle'] = True
                break
        else:
            return result  # No cycle found
        
        # Phase 2: Find cycle start and distance
        distance = 0
        slow = head
        while slow != fast:
            slow = slow.next
            fast = fast.next
            distance += 1
        
        result['cycle_start'] = slow
        result['distance_to_cycle'] = distance
        
        # Phase 3: Find cycle length
        length = 1
        current = slow.next
        while current != slow:
            current = current.next
            length += 1
        
        result['cycle_length'] = length
        
        return result

# Utility functions for testing
def create_linked_list_with_cycle(values: list, cycle_pos: int = -1) -> ListNode:
    """Create a linked list with optional cycle."""
    if not values:
        return None
    
    nodes = [ListNode(val) for val in values]
    
    # Connect nodes
    for i in range(len(nodes) - 1):
        nodes[i].next = nodes[i + 1]
    
    # Create cycle if specified
    if 0 <= cycle_pos < len(nodes):
        nodes[-1].next = nodes[cycle_pos]
    
    return nodes[0]

def print_list(head: ListNode, max_nodes: int = 20) -> None:
    """Print linked list (with cycle protection)."""
    current = head
    visited = set()
    count = 0
    
    while current and count < max_nodes:
        if id(current) in visited:
            print(f" -> {current.val} (cycle detected)")
            break
        
        visited.add(id(current))
        print(f" -> {current.val}", end="")
        current = current.next
        count += 1
    
    if current and count >= max_nodes:
        print(" -> ... (truncated)")
    elif not current:
        print(" -> None")
```

### Advanced Python Applications

```python
# Application 1: Function Iteration Cycle Detection
def find_duplicate_number(nums: list) -> int:
    """
    Find duplicate number using Floyd's algorithm.
    Based on the fact that array indices create a functional graph.
    """
    slow = nums[0]
    fast = nums[0]
    
    # Phase 1: Find intersection point
    while True:
        slow = nums[slow]
        fast = nums[nums[fast]]
        if slow == fast:
            break
    
    # Phase 2: Find entrance to cycle (duplicate number)
    slow = nums[0]
    while slow != fast:
        slow = nums[slow]
        fast = nums[fast]
    
    return slow

# Application 2: Sequence Pattern Detection
class SequenceCycleDetector:
    def __init__(self):
        self.sequence = []
    
    def detect_cycle_in_sequence(self, generator_func, start_val):
        """Detect cycle in a sequence generated by a function."""
        seen = {}
        current = start_val
        position = 0
        
        while current not in seen:
            seen[current] = position
            self.sequence.append(current)
            current = generator_func(current)
            position += 1
        
        cycle_start = seen[current]
        cycle_length = position - cycle_start
        
        return {
            'cycle_start_pos': cycle_start,
            'cycle_length': cycle_length,
            'cycle_start_value': current,
            'sequence': self.sequence
        }

# Example usage of sequence detector
def collatz_next(n):
    """Collatz conjecture next value."""
    return n // 2 if n % 2 == 0 else 3 * n + 1

def quadratic_map(x, a=4):
    """Quadratic map: x_{n+1} = a * x_n * (1 - x_n)"""
    return a * x * (1 - x)
```

## Rust Implementation

### Basic Linked List Structure

```rust
use std::cell::RefCell;
use std::rc::{Rc, Weak};
use std::collections::HashMap;

#[derive(Debug)]
pub struct ListNode {
    pub val: i32,
    pub next: Option<Rc<RefCell<ListNode>>>,
}

impl ListNode {
    pub fn new(val: i32) -> Self {
        ListNode { val, next: None }
    }
}

type NodeRef = Rc<RefCell<ListNode>>;
type WeakNodeRef = Weak<RefCell<ListNode>>;
```

### Floyd's Algorithm Implementation

```rust
pub struct FloydCycleDetection;

impl FloydCycleDetection {
    /// Detect if a cycle exists in the linked list
    pub fn has_cycle(head: &Option<NodeRef>) -> bool {
        if head.is_none() {
            return false;
        }
        
        let mut slow = head.clone();
        let mut fast = head.clone();
        
        loop {
            // Move slow pointer one step
            if let Some(slow_node) = &slow {
                slow = slow_node.borrow().next.clone();
            } else {
                return false;
            }
            
            // Move fast pointer two steps
            if let Some(fast_node) = &fast {
                if let Some(next) = &fast_node.borrow().next {
                    fast = next.borrow().next.clone();
                } else {
                    return false;
                }
            } else {
                return false;
            }
            
            // Check if pointers meet
            match (&slow, &fast) {
                (Some(s), Some(f)) => {
                    if Rc::ptr_eq(s, f) {
                        return true;
                    }
                }
                _ => return false,
            }
        }
    }
    
    /// Find the node where the cycle begins
    pub fn detect_cycle_start(head: &Option<NodeRef>) -> Option<NodeRef> {
        if head.is_none() {
            return None;
        }
        
        let mut slow = head.clone();
        let mut fast = head.clone();
        
        // Phase 1: Detect cycle
        loop {
            // Move slow pointer one step
            if let Some(slow_node) = &slow {
                slow = slow_node.borrow().next.clone();
            } else {
                return None;
            }
            
            // Move fast pointer two steps
            if let Some(fast_node) = &fast {
                if let Some(next) = &fast_node.borrow().next {
                    fast = next.borrow().next.clone();
                } else {
                    return None;
                }
            } else {
                return None;
            }
            
            // Check if pointers meet
            match (&slow, &fast) {
                (Some(s), Some(f)) => {
                    if Rc::ptr_eq(s, f) {
                        break;
                    }
                }
                _ => return None,
            }
        }
        
        // Phase 2: Find cycle start
        slow = head.clone();
        while let (Some(s), Some(f)) = (&slow, &fast) {
            if Rc::ptr_eq(s, f) {
                return slow;
            }
            slow = s.borrow().next.clone();
            fast = f.as_ref().map(|node| node.borrow().next.clone()).flatten();
        }
        
        None
    }
    
    /// Get the length of the cycle
    pub fn cycle_length(head: &Option<NodeRef>) -> usize {
        if head.is_none() {
            return 0;
        }
        
        let mut slow = head.clone();
        let mut fast = head.clone();
        
        // Phase 1: Detect cycle
        loop {
            // Move slow pointer one step
            if let Some(slow_node) = &slow {
                slow = slow_node.borrow().next.clone();
            } else {
                return 0;
            }
            
            // Move fast pointer two steps
            if let Some(fast_node) = &fast {
                if let Some(next) = &fast_node.borrow().next {
                    fast = next.borrow().next.clone();
                } else {
                    return 0;
                }
            } else {
                return 0;
            }
            
            // Check if pointers meet
            match (&slow, &fast) {
                (Some(s), Some(f)) => {
                    if Rc::ptr_eq(s, f) {
                        break;
                    }
                }
                _ => return 0,
            }
        }
        
        // Count cycle length
        let mut length = 1;
        let start = slow.clone();
        let mut current = slow.as_ref().unwrap().borrow().next.clone();
        
        while let Some(curr_node) = &current {
            if let Some(start_node) = &start {
                if Rc::ptr_eq(curr_node, start_node) {
                    break;
                }
            }
            current = curr_node.borrow().next.clone();
            length += 1;
        }
        
        length
    }
    
    /// Get comprehensive cycle information
    pub fn full_cycle_info(head: &Option<NodeRef>) -> CycleInfo {
        let mut result = CycleInfo::default();
        
        if head.is_none() {
            return result;
        }
        
        let mut slow = head.clone();
        let mut fast = head.clone();
        
        // Phase 1: Detect cycle
        loop {
            // Move slow pointer one step
            if let Some(slow_node) = &slow {
                slow = slow_node.borrow().next.clone();
            } else {
                return result;
            }
            
            // Move fast pointer two steps
            if let Some(fast_node) = &fast {
                if let Some(next) = &fast_node.borrow().next {
                    fast = next.borrow().next.clone();
                } else {
                    return result;
                }
            } else {
                return result;
            }
            
            // Check if pointers meet
            match (&slow, &fast) {
                (Some(s), Some(f)) => {
                    if Rc::ptr_eq(s, f) {
                        result.has_cycle = true;
                        break;
                    }
                }
                _ => return result,
            }
        }
        
        // Phase 2: Find cycle start and distance
        let mut distance = 0;
        slow = head.clone();
        while let (Some(s), Some(f)) = (&slow, &fast) {
            if Rc::ptr_eq(s, f) {
                result.cycle_start = slow.clone();
                result.distance_to_cycle = distance;
                break;
            }
            slow = s.borrow().next.clone();
            fast = f.as_ref().map(|node| node.borrow().next.clone()).flatten();
            distance += 1;
        }
        
        // Phase 3: Find cycle length
        if let Some(start) = &result.cycle_start {
            let mut length = 1;
            let mut current = start.borrow().next.clone();
            
            while let Some(curr_node) = &current {
                if Rc::ptr_eq(curr_node, start) {
                    break;
                }
                current = curr_node.borrow().next.clone();
                length += 1;
            }
            result.cycle_length = length;
        }
        
        result
    }
}

#[derive(Debug, Default)]
pub struct CycleInfo {
    pub has_cycle: bool,
    pub cycle_start: Option<NodeRef>,
    pub cycle_length: usize,
    pub distance_to_cycle: usize,
}

// Utility functions
pub fn create_linked_list_with_cycle(values: Vec<i32>, cycle_pos: Option<usize>) -> Option<NodeRef> {
    if values.is_empty() {
        return None;
    }
    
    let nodes: Vec<NodeRef> = values
        .into_iter()
        .map(|val| Rc::new(RefCell::new(ListNode::new(val))))
        .collect();
    
    // Connect nodes
    for i in 0..nodes.len() - 1 {
        nodes[i].borrow_mut().next = Some(nodes[i + 1].clone());
    }
    
    // Create cycle if specified
    if let Some(pos) = cycle_pos {
        if pos < nodes.len() {
            nodes[nodes.len() - 1].borrow_mut().next = Some(nodes[pos].clone());
        }
    }
    
    Some(nodes[0].clone())
}

// Advanced Applications
pub fn find_duplicate_number(nums: Vec<i32>) -> i32 {
    let mut slow = nums[0] as usize;
    let mut fast = nums[0] as usize;
    
    // Phase 1: Find intersection point
    loop {
        slow = nums[slow] as usize;
        fast = nums[nums[fast] as usize] as usize;
        if slow == fast {
            break;
        }
    }
    
    // Phase 2: Find entrance to cycle
    slow = nums[0] as usize;
    while slow != fast {
        slow = nums[slow] as usize;
        fast = nums[fast] as usize;
    }
    
    slow as i32
}

pub struct SequenceCycleDetector {
    pub sequence: Vec<i32>,
}

impl SequenceCycleDetector {
    pub fn new() -> Self {
        SequenceCycleDetector {
            sequence: Vec::new(),
        }
    }
    
    pub fn detect_cycle_in_sequence<F>(&mut self, generator_func: F, start_val: i32) -> SequenceCycleInfo
    where
        F: Fn(i32) -> i32,
    {
        let mut seen: HashMap<i32, usize> = HashMap::new();
        let mut current = start_val;
        let mut position = 0;
        
        while !seen.contains_key(&current) {
            seen.insert(current, position);
            self.sequence.push(current);
            current = generator_func(current);
            position += 1;
        }
        
        let cycle_start = seen[&current];
        let cycle_length = position - cycle_start;
        
        SequenceCycleInfo {
            cycle_start_pos: cycle_start,
            cycle_length,
            cycle_start_value: current,
            sequence: self.sequence.clone(),
        }
    }
}

#[derive(Debug)]
pub struct SequenceCycleInfo {
    pub cycle_start_pos: usize,
    pub cycle_length: usize,
    pub cycle_start_value: i32,
    pub sequence: Vec<i32>,
}

// Example generator functions
pub fn collatz_next(n: i32) -> i32 {
    if n % 2 == 0 {
        n / 2
    } else {
        3 * n + 1
    }
}

pub fn linear_congruential_generator(x: i32) -> i32 {
    // Simple LCG: x_{n+1} = (a * x_n + c) mod m
    let a = 1664525;
    let c = 1013904223;
    let m = 2_i32.pow(32);
    ((a as i64 * x as i64 + c as i64) % m as i64) as i32
}
```

## Applications

### 1. Linked List Cycle Detection

The most common application - detecting cycles in singly linked lists.

### 2. Duplicate Number Detection

Using array indices as pointers to detect duplicate numbers in O(1) space.

### 3. Function Iteration Analysis

Detecting periodic behavior in iterative functions like:

- Collatz conjecture sequences
- Pseudorandom number generators
- Mathematical recurrence relations

### 4. State Machine Cycle Detection

Detecting repeating states in finite state machines.

### 5. Hash Function Analysis

Finding collisions and cycles in hash function outputs.

## Advanced Examples

### Python: Complete Testing Suite

```python
def run_comprehensive_tests():
    """Run comprehensive tests for Floyd's algorithm."""
    
    # Test 1: No cycle
    head1 = create_linked_list_with_cycle([1, 2, 3, 4, 5])
    info1 = FloydCycleDetection.full_cycle_info(head1)
    print("Test 1 - No cycle:", info1)
    
    # Test 2: Cycle at position 1
    head2 = create_linked_list_with_cycle([1, 2, 3, 4, 5], 1)
    info2 = FloydCycleDetection.full_cycle_info(head2)
    print("Test 2 - Cycle at pos 1:", info2)
    
    # Test 3: Self-loop
    head3 = create_linked_list_with_cycle([1], 0)
    info3 = FloydCycleDetection.full_cycle_info(head3)
    print("Test 3 - Self loop:", info3)
    
    # Test 4: Duplicate number detection
    nums = [1, 3, 4, 2, 2]
    duplicate = find_duplicate_number(nums)
    print(f"Test 4 - Duplicate number in {nums}: {duplicate}")
    
    # Test 5: Sequence cycle detection
    detector = SequenceCycleDetector()
    collatz_info = detector.detect_cycle_in_sequence(collatz_next, 27)
    print("Test 5 - Collatz sequence (27):", collatz_info)

if __name__ == "__main__":
    run_comprehensive_tests()
```

### Rust: Complete Testing Suite

```rust
#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_no_cycle() {
        let head = create_linked_list_with_cycle(vec![1, 2, 3, 4, 5], None);
        let info = FloydCycleDetection::full_cycle_info(&head);
        
        assert!(!info.has_cycle);
        assert_eq!(info.cycle_length, 0);
        assert_eq!(info.distance_to_cycle, 0);
        assert!(info.cycle_start.is_none());
    }
    
    #[test]
    fn test_cycle_at_position_one() {
        let head = create_linked_list_with_cycle(vec![1, 2, 3, 4, 5], Some(1));
        let info = FloydCycleDetection::full_cycle_info(&head);
        
        assert!(info.has_cycle);
        assert_eq!(info.cycle_length, 4);
        assert_eq!(info.distance_to_cycle, 1);
        assert!(info.cycle_start.is_some());
        assert_eq!(info.cycle_start.as_ref().unwrap().borrow().val, 2);
    }
    
    #[test]
    fn test_self_loop() {
        let head = create_linked_list_with_cycle(vec![1], Some(0));
        let info = FloydCycleDetection::full_cycle_info(&head);
        
        assert!(info.has_cycle);
        assert_eq!(info.cycle_length, 1);
        assert_eq!(info.distance_to_cycle, 0);
        assert!(info.cycle_start.is_some());
        assert_eq!(info.cycle_start.as_ref().unwrap().borrow().val, 1);
    }
    
    #[test]
    fn test_duplicate_number_detection() {
        let nums = vec![1, 3, 4, 2, 2];
        let duplicate = find_duplicate_number(nums);
        assert_eq!(duplicate, 2);
        
        let nums2 = vec![3, 1, 3, 4, 2];
        let duplicate2 = find_duplicate_number(nums2);
        assert_eq!(duplicate2, 3);
    }
    
    #[test]
    fn test_sequence_cycle_detection() {
        let mut detector = SequenceCycleDetector::new();
        let info = detector.detect_cycle_in_sequence(collatz_next, 4);
        
        // Collatz sequence for 4: 4 -> 2 -> 1 -> 4 -> 2 -> 1 -> ...
        assert_eq!(info.cycle_length, 3);
        assert_eq!(info.cycle_start_value, 4);
    }
}

fn main() {
    println!("Floyd's Cycle Detection - Rust Implementation");
    
    // Example usage
    let head = create_linked_list_with_cycle(vec![1, 2, 3, 4, 5], Some(1));
    let info = FloydCycleDetection::full_cycle_info(&head);
    
    println!("Cycle Info: {:#?}", info);
    
    // Duplicate detection example
    let nums = vec![1, 3, 4, 2, 2];
    let duplicate = find_duplicate_number(nums.clone());
    println!("Duplicate in {:?}: {}", nums, duplicate);
    
    // Sequence analysis
    let mut detector = SequenceCycleDetector::new();
    let collatz_info = detector.detect_cycle_in_sequence(collatz_next, 27);
    println!("Collatz sequence analysis: {:#?}", collatz_info);
}
```

## Testing and Validation

### Edge Cases to Consider

1. **Empty list**: Handle null/None input
2. **Single node**: Test self-loops and no cycles
3. **Two nodes**: Test simple cycles
4. **Large cycles**: Ensure algorithm handles long cycles efficiently
5. **No cycle**: Verify correct termination
6. **Cycle at beginning**: Test when cycle starts at head

### Performance Benchmarks

- **Small lists** (< 100 nodes): Microsecond performance
- **Medium lists** (1K-10K nodes): Millisecond performance  
- **Large lists** (100K+ nodes): Still linear time complexity
- **Memory usage**: Constant O(1) regardless of input size

### Common Pitfalls

1. **Infinite loops**: Ensure proper termination conditions
2. **Null pointer dereference**: Check for null/None before accessing
3. **Integer overflow**: Consider wrap-around in sequence applications
4. **Pointer comparison**: Use proper equality checks (especially in Rust)

## Conclusion

Floyd's Cycle Detection Algorithm is a powerful and elegant solution for cycle detection problems. Its O(1) space complexity makes it superior to hash-based approaches for memory-constrained environments. The algorithm's applications extend far beyond linked lists, making it a valuable tool for various computational problems involving periodic behavior detection.

Key takeaways:

- **Simplicity**: Easy to understand and implement
- **Efficiency**: O(n) time, O(1) space complexity
- **Versatility**: Applicable to many domains beyond linked lists
- **Robustness**: Handles edge cases gracefully when properly implemented

I'll create a detailed ASCII diagram showing Floyd's Cycle Detection algorithm (also known as the "tortoise and hare" algorithm) step by step.I've created a comprehensive ASCII diagram showing Floyd's Cycle Detection algorithm step by step. The diagram includes:

1. **Visual representation** of how the tortoise (slow pointer) and hare (fast pointer) move through a linked list
2. **Step-by-step execution** showing exactly where each pointer is at each iteration
3. **Examples** of both cycle detection and non-cycle scenarios
4. **Mathematical explanation** of why the algorithm works
5. **Complexity analysis** and pseudocode
6. **Bonus section** on finding the actual start of the cycle

The key insight is that the hare moves twice as fast as the tortoise, so if there's a cycle, the hare will eventually "lap" the tortoise and they'll meet at the same node. If there's no cycle, the hare will reach the end (NULL) first.

The ASCII art shows exactly how the pointers move through the linked list structure, making it easy to visualize why this elegant algorithm works so effectively for cycle detection.

# Floyd's Cycle Detection Algorithm - Step by Step

## Algorithm Overview

- **Tortoise (slow pointer)**: Moves 1 step at a time
- **Hare (fast pointer)**: Moves 2 steps at a time
- **Detection**: If there's a cycle, they will eventually meet

## Example Linked List with Cycle

```ascii
Initial Structure:
[A] -> [B] -> [C] -> [D] -> [E]
                ^           |
                |___________|
```

## Step-by-Step Execution

### Step 0: Initial State

```ascii
Tortoise: T
Hare: H

[A] -> [B] -> [C] -> [D] -> [E]
 TH            ^           |
               |___________|

Both pointers start at head (A)
```

### Step 1: First Movement

```ascii
Tortoise moves 1 step, Hare moves 2 steps

[A] -> [B] -> [C] -> [D] -> [E]
       T      H     ^      |
                    |______|

Tortoise at B, Hare at C
No collision yet
```

### Step 2: Second Movement

```ascii
Tortoise moves 1 step, Hare moves 2 steps

[A] -> [B] -> [C] -> [D] -> [E]
              T             ^H
                           |
                           |_______|

Tortoise at C, Hare at E
No collision yet
```

### Step 3: Third Movement

```ascii
Tortoise moves 1 step, Hare moves 2 steps
(Hare wraps around due to cycle)

[A] -> [B] -> [C] -> [D] -> [E]
                     T      ^
                     H      |
                           |_______|

Tortoise at D, Hare at D
COLLISION DETECTED! Cycle exists!
```

## Algorithm in Action - Detailed View

### Without Cycle (No Detection)

```ascii
Step 0: [1] -> [2] -> [3] -> [4] -> NULL
        TH

Step 1: [1] -> [2] -> [3] -> [4] -> NULL
               T      H

Step 2: [1] -> [2] -> [3] -> [4] -> NULL
                      T             H→NULL

Result: Hare reaches NULL, no cycle detected
```

### With Cycle (Detection Occurs)

```ascii
List: [1] -> [2] -> [3] -> [4] -> [5]
                    ^             |
                    |_____________|

Step 0: [1] -> [2] -> [3] -> [4] -> [5]
        TH            ^             |
                      |_____________|

Step 1: [1] -> [2] -> [3] -> [4] -> [5]
               T      H     ^      |
                            |______|

Step 2: [1] -> [2] -> [3] -> [4] -> [5]
                      T             H
                      ^             |
                      |_____________|

Step 3: [1] -> [2] -> [3] -> [4] -> [5]
                             T      ^
                             H      |
                                   |__|

Step 4: [1] -> [2] -> [3] -> [4] -> [5]
                             ^      T
                             H      |
                                   |__|

COLLISION! Both pointers meet at node [4]
```

## Why It Works - Mathematical Proof

### Key Insight

If there's a cycle of length `C`, and the distance from start to cycle entry is `D`:

```ascii
Visual representation:
[Start] --D steps--> [Cycle Entry] --C steps--> [Back to Cycle Entry]
                           ^                            |
                           |____________________________|
```

### When they meet

- **Tortoise position**: `D + k` (where k < C)
- **Hare position**: `D + 2k` (hare moves twice as fast)

Since hare laps tortoise in the cycle:
`D + 2k = D + k + nC` (where n is number of complete cycles)

This simplifies to: `k = nC`

The meeting point is guaranteed because the relative speed difference is 1 step per iteration.

## Complexity Analysis

```ascii
Time Complexity:  O(n) - where n is number of nodes
Space Complexity: O(1) - only uses two pointers

Worst case: Hare travels at most 2n steps before:
- Meeting tortoise (cycle detected), or  
- Reaching NULL (no cycle)
```

## Pseudocode

```ascii
function detectCycle(head):
    if head == NULL:
        return false
    
    tortoise = head
    hare = head
    
    while hare != NULL and hare.next != NULL:
        tortoise = tortoise.next        // Move 1 step
        hare = hare.next.next          // Move 2 steps
        
        if tortoise == hare:           // Collision!
            return true                // Cycle detected
    
    return false                       // No cycle
```

## Finding Cycle Start (Bonus)

After detecting a cycle, to find where it starts:

```ascii
Step 1: Keep one pointer at collision point
Step 2: Move other pointer to head
Step 3: Move both at same speed (1 step each)
Step 4: Where they meet = cycle start

Example:
[A] -> [B] -> [C] -> [D] -> [E]
              ^             |
              |_____________|

After collision at D:
- Reset one pointer to A
- Keep other at D  
- Move both 1 step at a time
- They meet at C (cycle start)
```
