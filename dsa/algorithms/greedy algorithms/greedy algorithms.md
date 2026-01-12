# The Complete Mastery Guide to Greedy Algorithms

*"The greedy choice is not always optimal, but when it is, it reveals profound mathematical elegance."*

---

## Table of Contents
1. Foundation & Mental Models
2. The Greedy Choice Property (Deep Dive)
3. Proof Techniques & Mathematical Rigor
4. Pattern Recognition Framework
5. Classic Problems (Categorized by Pattern)
6. Implementation Strategies in Rust, Python & Go
7. Advanced Topics & Optimizations
8. Practice Roadmap for Top 1% Mastery

---

## 1. Foundation & Mental Models

### What is a Greedy Algorithm?

A **greedy algorithm** builds a solution by making a sequence of choices, where each choice is:
1. **Locally optimal** - the best choice at the current moment
2. **Irrevocable** - once made, never reconsidered
3. **Myopic** - doesn't look ahead at future consequences

**Key Insight**: Greedy works when local optimality implies global optimality.

### The Psychological Model: "The Impatient Optimizer"

Think of greedy algorithms like a chess player who only considers immediate gains:
- **Strength**: Fast decisions, no backtracking
- **Weakness**: Can miss better long-term strategies
- **When it works**: When the problem has special structure (greedy-choice property)

### Cognitive Framework: Recognition Before Proof

```
Problem → Pattern Recognition → Greedy Hypothesis → Proof → Implementation
          ↓                      ↓                   ↓
          (intuition)            (conjecture)        (verification)
```

**Meta-learning principle**: Your goal is to build *pattern libraries* in your mind. With practice, you'll recognize greedy opportunities in seconds.

---

## 2. The Greedy Choice Property (Deep Understanding)

### Two Fundamental Properties

For a greedy algorithm to work, the problem MUST have:

#### A. **Greedy Choice Property**
Making locally optimal choices leads to a globally optimal solution.

**Formal Definition**: 
If there exists an optimal solution S, and our greedy choice is G, then there exists an optimal solution S' that includes G.

#### B. **Optimal Substructure**
An optimal solution contains optimal solutions to subproblems.

**Formal Definition**:
If S is optimal for problem P, and we remove the greedy choice G from S, the remaining solution is optimal for the reduced problem P'.

### Visualization of Greedy Choice Property

```
Decision Tree (Greedy vs Optimal):

                    [Start]
                   /   |   \
              [G] /    |    \ [Other choices]
                 /     |     \
            [Optimal] [Sub]  [Sub-optimal]
                Path   Path   Paths

Greedy Choice Property guarantees:
The greedy path ALWAYS leads to optimal or reaches it eventually.
```

### Mental Model: "The One-Way Street"

Think of greedy as committing to streets you can never reverse on:
- **Good greedy**: Each street gets you closer to destination
- **Bad greedy**: You might reach a dead-end (local maximum)

---

## 3. Proof Techniques & Mathematical Rigor

### Three Standard Proof Methods

#### Method 1: **Exchange Argument** (Most Common)

**Template**:
1. Assume optimal solution O exists that differs from greedy solution G
2. Show you can "exchange" a choice in O with greedy choice
3. Prove the exchange doesn't worsen the solution
4. Conclude greedy is optimal

**Example**: Activity Selection (we'll prove this later)

#### Method 2: **Greedy Stays Ahead**

**Template**:
1. Define a measure of "progress"
2. Prove greedy is always "ahead" of any other solution at each step
3. Conclude greedy reaches optimal first

**Example**: Fractional Knapsack

#### Method 3: **Structural Induction**

**Template**:
1. Base case: Greedy works for smallest problem
2. Inductive step: If greedy works for problem size n-1, it works for n
3. Conclude greedy works for all sizes

---

## 4. Pattern Recognition Framework

### The Five Canonical Greedy Patterns

```
┌─────────────────────────────────────────────────────────┐
│                GREEDY PATTERN TAXONOMY                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. SELECTION PROBLEMS                                  │
│     └─ Pick optimal subset from candidates              │
│     └─ Example: Activity Selection, Job Scheduling      │
│                                                         │
│  2. ORDERING/ARRANGEMENT PROBLEMS                       │
│     └─ Arrange elements to minimize/maximize metric     │
│     └─ Example: Huffman Coding, Task Scheduling         │
│                                                         │
│  3. OPTIMIZATION WITH CONSTRAINTS                       │
│     └─ Maximize/minimize while respecting limits        │
│     └─ Example: Knapsack, Minimum Coins                 │
│                                                         │
│  4. GRAPH PROBLEMS (Locally Optimal Paths)              │
│     └─ Build optimal tree/path greedily                 │
│     └─ Example: Dijkstra's, Prim's, Kruskal's           │
│                                                         │
│  5. INVARIANT MAINTENANCE                               │
│     └─ Maintain property through greedy moves           │
│     └─ Example: Jump Game, Gas Station                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Decision Flow: "Is This Problem Greedy?"

```
                    [Problem Statement]
                            |
                            v
                    Can you make choices
                    one at a time?
                       /         \
                    NO           YES
                    /              \
            [Not Greedy]            v
            Try DP/Backtrack   Does local choice
                               seem optimal?
                                  /        \
                               NO          YES
                               /             \
                        [Probably DP]         v
                                        Can you prove
                                        exchange/stays-ahead?
                                           /         \
                                        NO           YES
                                        /              \
                                [Try DP]          [GREEDY!]
```

---

## 5. Classic Problems (Categorized by Pattern)

### Pattern 1: Selection Problems

#### **Problem 1: Activity Selection** (The Foundation)

**Statement**: Given n activities with start and finish times, select maximum number of non-overlapping activities.

**Input**: 
```
Activities: [(start_i, finish_i)]
Example: [(1,4), (3,5), (0,6), (5,7), (3,9), (5,9), (6,10), (8,11), (8,12), (2,14), (12,16)]
```

**Greedy Strategy**: Always pick the activity that finishes earliest (and doesn't conflict).

**Why It Works - Exchange Argument Proof**:

```
Let O = optimal solution
Let G = greedy solution (sorted by finish time)

Claim: |G| = |O|

Proof:
1. Let g₁ be the first greedy choice (earliest finish)
2. Let o₁ be the first activity in O

3. If g₁ = o₁, we're done with first choice
   
4. If g₁ ≠ o₁:
   - Since g₁ finishes earliest, finish(g₁) ≤ finish(o₁)
   - Replace o₁ with g₁ in O → creates O'
   - O' is still valid (g₁ finishes earlier, no conflicts)
   - |O'| = |O| (same size)
   
5. By induction, greedy matches optimal at every step
6. Therefore, greedy is optimal ∎
```

**Visualization**:

```
Timeline:
0    2    4    6    8    10   12   14   16
|----●----|----●----|----●----|----●----|
     |====A1====|
          |=====A2=====|
|==========A3===========|
                    |====A4====|
          |===========A5============|
                    |======A6========|
                         |=====A7=====|
                              |====A8====|
                              |======A9=======|
     |===================A10==================|
                                        |===A11===|

Greedy Selection (by earliest finish):
1. A1 (finishes at 4) ✓
2. A4 (finishes at 7, starts at 5 > 4) ✓
3. A7 (finishes at 10, starts at 6 > 7) ✓
4. A11 (finishes at 16, starts at 12 > 10) ✓

Maximum: 4 activities
```

**Implementation - Rust** (Idiomatic, Performance-Focused):

```rust
use std::cmp::Ordering;

#[derive(Debug, Clone, Copy)]
struct Activity {
    start: i32,
    finish: i32,
    index: usize, // Original index for tracking
}

fn activity_selection(mut activities: Vec<Activity>) -> Vec<usize> {
    if activities.is_empty() {
        return vec![];
    }
    
    // Sort by finish time (stable sort preserves original order for ties)
    // Time: O(n log n), Space: O(1) - in-place sort
    activities.sort_by(|a, b| {
        a.finish.cmp(&b.finish)
            .then_with(|| a.start.cmp(&b.start)) // Tie-breaker
    });
    
    let mut selected = Vec::with_capacity(activities.len() / 2); // Heuristic capacity
    selected.push(activities[0].index);
    let mut last_finish = activities[0].finish;
    
    // Greedy selection: O(n)
    for activity in activities.iter().skip(1) {
        if activity.start >= last_finish {
            selected.push(activity.index);
            last_finish = activity.finish;
        }
    }
    
    selected
}

// Alternative: Using iterators (more functional style)
fn activity_selection_iter(mut activities: Vec<Activity>) -> Vec<usize> {
    if activities.is_empty() {
        return vec![];
    }
    
    activities.sort_unstable_by_key(|a| (a.finish, a.start));
    
    activities
        .iter()
        .scan(i32::MIN, |last_finish, activity| {
            if activity.start >= *last_finish {
                *last_finish = activity.finish;
                Some(Some(activity.index))
            } else {
                Some(None)
            }
        })
        .flatten()
        .collect()
}

// Example usage
fn main() {
    let activities = vec![
        Activity { start: 1, finish: 4, index: 0 },
        Activity { start: 3, finish: 5, index: 1 },
        Activity { start: 0, finish: 6, index: 2 },
        Activity { start: 5, finish: 7, index: 3 },
        Activity { start: 3, finish: 9, index: 4 },
        Activity { start: 5, finish: 9, index: 5 },
        Activity { start: 6, finish: 10, index: 6 },
        Activity { start: 8, finish: 11, index: 7 },
        Activity { start: 8, finish: 12, index: 8 },
        Activity { start: 2, finish: 14, index: 9 },
        Activity { start: 12, finish: 16, index: 10 },
    ];
    
    let result = activity_selection(activities.clone());
    println!("Selected activities: {:?}", result);
    println!("Count: {}", result.len());
}
```

**Implementation - Python** (Clean, Readable):

```python
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class Activity:
    start: int
    finish: int
    index: int
    
    def __repr__(self):
        return f"A{self.index}({self.start}->{self.finish})"

def activity_selection(activities: List[Activity]) -> List[int]:
    """
    Select maximum non-overlapping activities.
    
    Time: O(n log n) - dominated by sorting
    Space: O(n) - for result storage
    
    Args:
        activities: List of activities with start/finish times
        
    Returns:
        Indices of selected activities
    """
    if not activities:
        return []
    
    # Sort by finish time (key insight of greedy strategy)
    sorted_acts = sorted(activities, key=lambda a: (a.finish, a.start))
    
    selected = [sorted_acts[0].index]
    last_finish = sorted_acts[0].finish
    
    for activity in sorted_acts[1:]:
        if activity.start >= last_finish:
            selected.append(activity.index)
            last_finish = activity.finish
    
    return selected

# Alternative: Generator version (memory efficient for large inputs)
def activity_selection_gen(activities: List[Activity]):
    """Generator version - yields selected activities lazily"""
    if not activities:
        return
    
    sorted_acts = sorted(activities, key=lambda a: a.finish)
    
    yield sorted_acts[0].index
    last_finish = sorted_acts[0].finish
    
    for activity in sorted_acts[1:]:
        if activity.start >= last_finish:
            yield activity.index
            last_finish = activity.finish

# Example usage
if __name__ == "__main__":
    activities = [
        Activity(1, 4, 0),
        Activity(3, 5, 1),
        Activity(0, 6, 2),
        Activity(5, 7, 3),
        Activity(3, 9, 4),
        Activity(5, 9, 5),
        Activity(6, 10, 6),
        Activity(8, 11, 7),
        Activity(8, 12, 8),
        Activity(2, 14, 9),
        Activity(12, 16, 10),
    ]
    
    result = activity_selection(activities)
    print(f"Selected activities: {result}")
    print(f"Count: {len(result)}")
    
    # Visualize
    for idx in result:
        print(activities[idx])
```

**Implementation - Go** (Efficient, Concurrent-Ready):

```go
package main

import (
    "fmt"
    "sort"
)

// Activity represents a time interval with original index
type Activity struct {
    Start  int
    Finish int
    Index  int
}

// ActivitySelection selects maximum non-overlapping activities
// Time: O(n log n), Space: O(n)
func ActivitySelection(activities []Activity) []int {
    if len(activities) == 0 {
        return []int{}
    }
    
    // Sort by finish time (stable sort)
    sort.SliceStable(activities, func(i, j int) bool {
        if activities[i].Finish == activities[j].Finish {
            return activities[i].Start < activities[j].Start
        }
        return activities[i].Finish < activities[j].Finish
    })
    
    selected := make([]int, 0, len(activities)/2) // Preallocate with heuristic
    selected = append(selected, activities[0].Index)
    lastFinish := activities[0].Finish
    
    for i := 1; i < len(activities); i++ {
        if activities[i].Start >= lastFinish {
            selected = append(selected, activities[i].Index)
            lastFinish = activities[i].Finish
        }
    }
    
    return selected
}

// Alternative: Functional style using filter
func ActivitySelectionFunc(activities []Activity) []int {
    if len(activities) == 0 {
        return []int{}
    }
    
    // Create a copy for sorting
    sorted := make([]Activity, len(activities))
    copy(sorted, activities)
    
    sort.SliceStable(sorted, func(i, j int) bool {
        return sorted[i].Finish < sorted[j].Finish
    })
    
    var selected []int
    lastFinish := -1 << 31 // Min int
    
    for _, act := range sorted {
        if act.Start >= lastFinish {
            selected = append(selected, act.Index)
            lastFinish = act.Finish
        }
    }
    
    return selected
}

func main() {
    activities := []Activity{
        {Start: 1, Finish: 4, Index: 0},
        {Start: 3, Finish: 5, Index: 1},
        {Start: 0, Finish: 6, Index: 2},
        {Start: 5, Finish: 7, Index: 3},
        {Start: 3, Finish: 9, Index: 4},
        {Start: 5, Finish: 9, Index: 5},
        {Start: 6, Finish: 10, Index: 6},
        {Start: 8, Finish: 11, Index: 7},
        {Start: 8, Finish: 12, Index: 8},
        {Start: 2, Finish: 14, Index: 9},
        {Start: 12, Finish: 16, Index: 10},
    }
    
    result := ActivitySelection(activities)
    fmt.Printf("Selected activities: %v\n", result)
    fmt.Printf("Count: %d\n", len(result))
}
```

**Complexity Analysis**:
- **Time**: O(n log n) - dominated by sorting
- **Space**: O(1) - if we can modify input, O(n) otherwise
- **Optimal**: Yes, cannot do better than sorting

**Key Insights**:
1. **Sorting criterion matters**: Finish time, NOT start time or duration
2. **Why not longest duration?** Counterexample: [(0,10)] vs [(0,1), (1,2), ..., (9,10)]
3. **Greedy stays ahead**: Finishing early leaves more room for future activities

---

### Pattern 2: Optimization with Constraints

#### **Problem 2: Fractional Knapsack**

**Statement**: Given items with values and weights, and a knapsack capacity, maximize total value (can take fractions of items).

**Why Greedy Works**: Value-to-weight ratio is the correct greedy criterion.

**Concept Explanation**:
- **Fractional**: Unlike 0/1 knapsack, you can take parts of items
- **Ratio**: Value per unit weight = value/weight (efficiency metric)
- **Greedy**: Always take the highest ratio item (or fraction) first

**Visual Representation**:

```
Items (Value, Weight, Ratio):
┌────────────────────────────────────┐
│ Item 1: V=60,  W=10, R=6.0  ████████████ (Best)
│ Item 2: V=100, W=20, R=5.0  ██████████
│ Item 3: V=120, W=30, R=4.0  ████████
└────────────────────────────────────┘

Capacity = 50

Greedy Process:
1. Take all of Item 1 (W=10): Value = 60, Remaining = 40
2. Take all of Item 2 (W=20): Value = 160, Remaining = 20
3. Take 20/30 of Item 3: Value = 160 + 80 = 240

Total: 240
```

**Implementation - Rust**:

```rust
#[derive(Debug, Clone, Copy)]
struct Item {
    value: f64,
    weight: f64,
}

impl Item {
    fn ratio(&self) -> f64 {
        self.value / self.weight
    }
}

fn fractional_knapsack(mut items: Vec<Item>, capacity: f64) -> f64 {
    // Sort by value-to-weight ratio (descending)
    items.sort_by(|a, b| b.ratio().partial_cmp(&a.ratio()).unwrap());
    
    let mut total_value = 0.0;
    let mut remaining_capacity = capacity;
    
    for item in items {
        if remaining_capacity == 0.0 {
            break;
        }
        
        let take = remaining_capacity.min(item.weight);
        total_value += take * item.ratio();
        remaining_capacity -= take;
    }
    
    total_value
}

// Detailed version with tracking
fn fractional_knapsack_detailed(mut items: Vec<Item>, capacity: f64) 
    -> (f64, Vec<(usize, f64)>) {
    
    // Track original indices
    let indexed: Vec<_> = items.iter().enumerate()
        .map(|(i, item)| (i, *item))
        .collect();
    
    let mut indexed = indexed;
    indexed.sort_by(|a, b| b.1.ratio().partial_cmp(&a.1.ratio()).unwrap());
    
    let mut total_value = 0.0;
    let mut remaining_capacity = capacity;
    let mut selections = Vec::new();
    
    for (idx, item) in indexed {
        if remaining_capacity == 0.0 {
            break;
        }
        
        let take = remaining_capacity.min(item.weight);
        let fraction = take / item.weight;
        
        total_value += take * item.ratio();
        remaining_capacity -= take;
        selections.push((idx, fraction));
    }
    
    (total_value, selections)
}
```

**Implementation - Python**:

```python
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class Item:
    value: float
    weight: float
    index: int = 0
    
    @property
    def ratio(self) -> float:
        return self.value / self.weight if self.weight > 0 else 0
    
    def __repr__(self):
        return f"Item{self.index}(V={self.value}, W={self.weight}, R={self.ratio:.2f})"

def fractional_knapsack(items: List[Item], capacity: float) -> float:
    """
    Maximize value in fractional knapsack.
    
    Time: O(n log n) - sorting
    Space: O(1) - in-place if input can be modified
    
    Strategy: Greedily select highest value/weight ratio items
    """
    # Sort by ratio (descending)
    sorted_items = sorted(items, key=lambda x: x.ratio, reverse=True)
    
    total_value = 0.0
    remaining = capacity
    
    for item in sorted_items:
        if remaining == 0:
            break
        
        # Take as much as possible
        take = min(remaining, item.weight)
        total_value += take * item.ratio
        remaining -= take
    
    return total_value

def fractional_knapsack_detailed(items: List[Item], capacity: float) \
    -> Tuple[float, List[Tuple[int, float]]]:
    """Returns (total_value, [(item_index, fraction_taken), ...])"""
    
    sorted_items = sorted(items, key=lambda x: x.ratio, reverse=True)
    
    total_value = 0.0
    remaining = capacity
    selections = []
    
    for item in sorted_items:
        if remaining == 0:
            break
        
        take = min(remaining, item.weight)
        fraction = take / item.weight
        
        total_value += take * item.ratio
        remaining -= take
        selections.append((item.index, fraction))
    
    return total_value, selections

# Example
if __name__ == "__main__":
    items = [
        Item(value=60, weight=10, index=0),
        Item(value=100, weight=20, index=1),
        Item(value=120, weight=30, index=2),
    ]
    
    capacity = 50
    
    max_value, selections = fractional_knapsack_detailed(items, capacity)
    print(f"Maximum value: {max_value}")
    print("Selections:")
    for idx, fraction in selections:
        print(f"  Item {idx}: {fraction*100:.1f}% taken")
```

**Proof (Greedy Stays Ahead)**:

```
Claim: Taking highest ratio item first is optimal

Proof by Exchange:
1. Let G be greedy solution (sorted by ratio descending)
2. Let O be any optimal solution
3. Suppose O differs from G in the first item

4. Let g₁ have ratio r_g and O takes o₁ with ratio r_o
5. Since greedy chose g₁, we know r_g ≥ r_o

6. Exchange argument:
   - If O takes w_o weight of o₁, replace with w_o of g₁
   - Value change: w_o * (r_g - r_o) ≥ 0
   - O' = O with exchange is at least as good

7. Repeat for all items
8. Greedy = O' ∎
```

---

### Pattern 3: Ordering/Arrangement

#### **Problem 3: Huffman Coding** (Optimal Prefix-Free Codes)

**Context**: You need to understand what Huffman coding solves before we build it.

**Concept - Prefix-Free Codes**:

Imagine you need to transmit characters {'A', 'B', 'C', 'D'} over a binary channel.

**Bad encoding** (Fixed-length):
```
A = 00
B = 01  
C = 10
D = 11
```
Cost: Every character takes 2 bits.

**Better encoding** (Variable-length based on frequency):
If text has frequencies: A=45%, B=13%, C=12%, D=30%

```
A = 0      (1 bit - most frequent)
B = 110    (3 bits)
C = 111    (3 bits)
D = 10     (2 bits)
```

**Prefix-free property**: No code is a prefix of another.
- Why? So we can decode uniquely: "0110" = "A B" (not ambiguous)

**Huffman's Insight**: Build a binary tree where:
- Frequent characters are near root (short codes)
- Rare characters are deep (long codes)

**Visual - Huffman Tree**:

```
        [100%]
        /    \
      0/      \1
      /        \
    [A:45]    [55%]
              /    \
            0/      \1
            /        \
         [30:D]    [25%]
                   /    \
                 0/      \1
                 /        \
              [B:13]    [C:12]

Codes:
A = 0
D = 10  
B = 110
C = 111

Average bits per character:
= 0.45×1 + 0.30×2 + 0.13×3 + 0.12×3
= 0.45 + 0.60 + 0.39 + 0.36
= 1.80 bits (vs 2.0 for fixed-length)
```

**Greedy Algorithm**:

```
Algorithm Huffman(frequencies):
    1. Create leaf node for each character with its frequency
    2. Put all nodes in a min-heap (priority queue by frequency)
    
    3. While heap has more than 1 node:
        a. Extract two nodes with minimum frequency
        b. Create new internal node with these as children
        c. New node's frequency = sum of children frequencies
        d. Insert new node back into heap
    
    4. The remaining node is the root of Huffman tree
    
    5. Assign codes by traversing tree (left=0, right=1)
```

**Why Greedy Works**:

**Theorem**: Combining the two least frequent symbols first is optimal.

**Intuition**: Least frequent symbols should be deepest in tree (longest codes).

**Implementation - Rust** (Using BinaryHeap):

```rust
use std::collections::BinaryHeap;
use std::cmp::Ordering;
use std::rc::Rc;
use std::cell::RefCell;

#[derive(Debug, Clone)]
enum NodeType {
    Leaf(char),
    Internal,
}

#[derive(Debug, Clone)]
struct HuffmanNode {
    freq: u32,
    node_type: NodeType,
    left: Option<Rc<RefCell<HuffmanNode>>>,
    right: Option<Rc<RefCell<HuffmanNode>>>,
}

// Custom Ord for min-heap (reverse ordering)
impl Ord for HuffmanNode {
    fn cmp(&self, other: &Self) -> Ordering {
        other.freq.cmp(&self.freq) // Reverse for min-heap
    }
}

impl PartialOrd for HuffmanNode {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl PartialEq for HuffmanNode {
    fn eq(&self, other: &Self) -> bool {
        self.freq == other.freq
    }
}

impl Eq for HuffmanNode {}

impl HuffmanNode {
    fn leaf(ch: char, freq: u32) -> Self {
        HuffmanNode {
            freq,
            node_type: NodeType::Leaf(ch),
            left: None,
            right: None,
        }
    }
    
    fn internal(left: HuffmanNode, right: HuffmanNode) -> Self {
        HuffmanNode {
            freq: left.freq + right.freq,
            node_type: NodeType::Internal,
            left: Some(Rc::new(RefCell::new(left))),
            right: Some(Rc::new(RefCell::new(right))),
        }
    }
}

use std::collections::HashMap;

fn build_huffman_tree(frequencies: &HashMap<char, u32>) -> Option<HuffmanNode> {
    if frequencies.is_empty() {
        return None;
    }
    
    // Create min-heap with leaf nodes
    let mut heap: BinaryHeap<HuffmanNode> = frequencies
        .iter()
        .map(|(&ch, &freq)| HuffmanNode::leaf(ch, freq))
        .collect();
    
    // Edge case: single character
    if heap.len() == 1 {
        return heap.pop();
    }
    
    // Build tree by combining minimum frequency nodes
    while heap.len() > 1 {
        let left = heap.pop().unwrap();
        let right = heap.pop().unwrap();
        let parent = HuffmanNode::internal(left, right);
        heap.push(parent);
    }
    
    heap.pop()
}

fn generate_codes_helper(
    node: &HuffmanNode,
    prefix: String,
    codes: &mut HashMap<char, String>,
) {
    match &node.node_type {
        NodeType::Leaf(ch) => {
            codes.insert(*ch, if prefix.is_empty() { "0".to_string() } else { prefix });
        }
        NodeType::Internal => {
            if let Some(left) = &node.left {
                generate_codes_helper(&left.borrow(), format!("{}0", prefix), codes);
            }
            if let Some(right) = &node.right {
                generate_codes_helper(&right.borrow(), format!("{}1", prefix), codes);
            }
        }
    }
}

fn generate_huffman_codes(frequencies: &HashMap<char, u32>) -> HashMap<char, String> {
    let tree = build_huffman_tree(frequencies);
    let mut codes = HashMap::new();
    
    if let Some(root) = tree {
        generate_codes_helper(&root, String::new(), &mut codes);
    }
    
    codes
}

// Example usage
fn main() {
    let mut frequencies = HashMap::new();
    frequencies.insert('A', 45);
    frequencies.insert('B', 13);
    frequencies.insert('C', 12);
    frequencies.insert('D', 30);
    
    let codes = generate_huffman_codes(&frequencies);
    
    println!("Huffman Codes:");
    for (ch, code) in &codes {
        println!("  {} -> {}", ch, code);
    }
    
    // Calculate average length
    let total_freq: u32 = frequencies.values().sum();
    let avg_length: f64 = codes.iter()
        .map(|(ch, code)| {
            let freq = frequencies[ch] as f64;
            (freq / total_freq as f64) * code.len() as f64
        })
        .sum();
    
    println!("\nAverage code length: {:.2} bits", avg_length);
}
```

**Implementation - Python** (Cleaner with heapq):

```python
import heapq
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field

@dataclass(order=True)
class HuffmanNode:
    freq: int
    char: Optional[str] = field(compare=False, default=None)
    left: Optional['HuffmanNode'] = field(compare=False, default=None)
    right: Optional['HuffmanNode'] = field(compare=False, default=None)
    
    def is_leaf(self) -> bool:
        return self.char is not None

def build_huffman_tree(frequencies: Dict[str, int]) -> Optional[HuffmanNode]:
    """
    Build Huffman tree using greedy algorithm.
    
    Time: O(n log n) where n = number of unique characters
    Space: O(n) for heap and tree
    """
    if not frequencies:
        return None
    
    # Create min-heap with leaf nodes
    heap = [HuffmanNode(freq=freq, char=char) 
            for char, freq in frequencies.items()]
    heapq.heapify(heap)
    
    # Edge case: single character
    if len(heap) == 1:
        return heap[0]
    
    # Greedy: Combine two minimum frequency nodes
    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        
        parent = HuffmanNode(
            freq=left.freq + right.freq,
            left=left,
            right=right
        )
        heapq.heappush(heap, parent)
    
    return heap[0]

def generate_codes(root: Optional[HuffmanNode]) -> Dict[str, str]:
    """Generate Huffman codes by tree traversal."""
    if not root:
        return {}
    
    codes = {}
    
    def dfs(node: HuffmanNode, code: str):
        if node.is_leaf():
            codes[node.char] = code if code else "0"  # Single char case
            return
        
        if node.left:
            dfs(node.left, code + "0")
        if node.right:
            dfs(node.right, code + "1")
    
    dfs(root, "")
    return codes

def huffman_encoding(text: str) -> Tuple[Dict[str, str], str]:
    """
    Complete Huffman encoding.
    
    Returns: (codes_dict, encoded_text)
    """
    # Calculate frequencies
    frequencies = {}
    for char in text:
        frequencies[char] = frequencies.get(char, 0) + 1
    
    # Build tree and generate codes
    tree = build_huffman_tree(frequencies)
    codes = generate_codes(tree)
    
    # Encode text
    encoded = ''.join(codes[char] for char in text)
    
    return codes, encoded

def huffman_decoding(encoded: str, codes: Dict[str, str]) -> str:
    """Decode using reverse code lookup."""
    # Create reverse mapping
    reverse_codes = {code: char for char, code in codes.items()}
    
    decoded = []
    current_code = ""
    
    for bit in encoded:
        current_code += bit
        if current_code in reverse_codes:
            decoded.append(reverse_codes[current_code])
            current_code = ""
    
    return ''.join(decoded)

# Example
if __name__ == "__main__":
    text = "AAAAAAAAAAAAAAAAAAAAAAAAAAABBBBBBBBBBBBCCCCCCCCCCCCDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"
    
    codes, encoded = huffman_encoding(text)
    
    print("Huffman Codes:")
    for char, code in sorted(codes.items()):
        print(f"  {char} -> {code}")
    
    print(f"\nOriginal length: {len(text) * 8} bits (8 bits/char)")
    print(f"Encoded length: {len(encoded)} bits")
    print(f"Compression ratio: {len(encoded) / (len(text) * 8):.2%}")
    
    # Verify decoding
    decoded = huffman_decoding(encoded, codes)
    assert decoded == text, "Decoding failed!"
    print("\n✓ Decoding verified")
```

**Complexity**:
- **Time**: O(n log n) - each heap operation is O(log n), done n-1 times
- **Space**: O(n) - heap and tree storage

**Key Insights**:
1. **Why min-heap?** Need to efficiently find two minimum frequency nodes
2. **Why combine minimum?** Least frequent should be deepest (proved by exchange)
3. **Prefix-free guarantee**: Tree structure ensures no code is prefix of another

---

## (Continuing with more patterns...)

Due to length constraints, I'll provide a roadmap for remaining topics. Would you like me to continue with:

### Remaining Patterns:
4. **Graph Greedy Algorithms** (Dijkstra, Prim's, Kruskal's)
5. **Invariant Maintenance** (Jump Game, Gas Station, Boats to Save People)
6. **Advanced Greedy** (Meeting Rooms II, Task Scheduler, Candy Distribution)

### Advanced Topics:
7. **Matroids** (Mathematical foundation of greedy)
8. **Approximation Algorithms** (When exact greedy fails)
9. **Greedy vs DP Decision Framework**
10. **Competition Problem Patterns**

**What would you like me to expand next?** I can provide:
- Complete implementations of all classic problems
- Detailed proofs for each
- Flowcharts and ASCII visualizations
- Problem-solving mental models
- Practice problem sets categorized by difficulty

Let me know which direction serves your mastery journey best!