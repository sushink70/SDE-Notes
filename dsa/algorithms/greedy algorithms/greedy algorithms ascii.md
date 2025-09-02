# GREEDY ALGORITHM: COIN CHANGE PROBLEM

I'll create a detailed ASCII diagram that illustrates how greedy algorithms work using a classic example - the coin change problem. This will show the step-by-step decision-making process that defines greedy algorithms.I've created a comprehensive ASCII diagram that illustrates how greedy algorithms work using the coin change problem as an example. The diagram shows:

1. **Step-by-step execution** - How the algorithm makes decisions at each step by always choosing the largest available coin
2. **Greedy choice principle** - The algorithm never looks back or reconsiders previous decisions
3. **Decision tree visualization** - Shows how greedy algorithms explore only one path through the solution space
4. **Algorithm template** - The general structure that most greedy algorithms follow
5. **Pros and cons** - When greedy algorithms work well and their limitations

The key insight is that greedy algorithms make the locally optimal choice at each step, hoping this leads to a globally optimal solution. This works for some problems (like coin change with standard denominations) but not others.

The diagram demonstrates the three essential components of a greedy algorithm:

- **Greedy choice property**: Making the best choice at each step
- **No backtracking**: Never reconsidering previous decisions  
- **Optimal substructure**: The problem can be broken into smaller subproblems

Would you like me to show examples of other classic greedy algorithms like activity selection or minimum spanning tree algorithms?

GREEDY ALGORITHM: COIN CHANGE PROBLEM
==========================================

Problem: Make change for 67 cents using minimum number of coins
Available coins: [25¢, 10¢, 5¢, 1¢]

STEP-BY-STEP EXECUTION:
═══════════════════════

Initial State:
┌─────────────────────────────────────┐
│ Target Amount: 67¢                  │
│ Available Coins: [25¢, 10¢, 5¢, 1¢] │
│ Selected Coins: []                  │
│ Remaining: 67¢                      │
└─────────────────────────────────────┘

STEP 1: Choose Largest Coin (Greedy Choice)
═════════════════════════════════════════════
Current Amount: 67¢
┌──────┬──────┬──────┬──────┐
│ 25¢  │ 10¢  │  5¢  │  1¢  │ ← Available coins
└──────┴──────┴──────┴──────┘
   ↑
  PICK (largest ≤ 67¢)

67¢ - 25¢ = 42¢
Selected: [25¢]
Remaining: 42¢

STEP 2: Choose Next Largest Coin
═══════════════════════════════════
Current Amount: 42¢
┌──────┬──────┬──────┬──────┐
│ 25¢  │ 10¢  │  5¢  │  1¢  │
└──────┴──────┴──────┴──────┘
   ↑
  PICK (largest ≤ 42¢)

42¢ - 25¢ = 17¢
Selected: [25¢, 25¢]
Remaining: 17¢

STEP 3: Continue Greedy Selection
═══════════════════════════════════
Current Amount: 17¢
┌──────┬──────┬──────┬──────┐
│ 25¢  │ 10¢  │  5¢  │  1¢  │
└──────┴──────┴──────┴──────┘
  (>17¢)  ↑
         PICK (largest ≤ 17¢)

17¢ - 10¢ = 7¢
Selected: [25¢, 25¢, 10¢]
Remaining: 7¢

STEP 4: Continue Selection
═══════════════════════════
Current Amount: 7¢
┌──────┬──────┬──────┬──────┐
│ 25¢  │ 10¢  │  5¢  │  1¢  │
└──────┴──────┴──────┴──────┘
  (>7¢)  (>7¢)   ↑
              PICK (largest ≤ 7¢)

7¢ - 5¢ = 2¢
Selected: [25¢, 25¢, 10¢, 5¢]
Remaining: 2¢

STEP 5: Final Selection
═══════════════════════
Current Amount: 2¢
┌──────┬──────┬──────┬──────┐
│ 25¢  │ 10¢  │  5¢  │  1¢  │
└──────┴──────┴──────┴──────┘
  (>2¢)  (>2¢)  (>2¢)   ↑
                     PICK

2¢ - 1¢ = 1¢
Selected: [25¢, 25¢, 10¢, 5¢, 1¢]
Remaining: 1¢

STEP 6: Last Coin
═══════════════════
Current Amount: 1¢
┌──────┬──────┬──────┬──────┐
│ 25¢  │ 10¢  │  5¢  │  1¢  │
└──────┴──────┴──────┴──────┘
  (>1¢)  (>1¢)  (>1¢)   ↑
                     PICK

1¢ - 1¢ = 0¢
Selected: [25¢, 25¢, 10¢, 5¢, 1¢, 1¢]
Remaining: 0¢ ✓

FINAL RESULT:
═════════════
┌─────────────────────────────────────┐
│ Original Amount: 67¢                │
│ Final Solution: 6 coins             │
│ Breakdown: 2×25¢ + 1×10¢ + 1×5¢ + 2×1¢│
│ Verification: 50+10+5+2 = 67¢ ✓     │
└─────────────────────────────────────┘

GREEDY ALGORITHM CHARACTERISTICS:
══════════════════════════════════

1. LOCAL OPTIMUM CHOICE:
   ┌─────────────────────────┐
   │ At each step, choose    │ ──┐
   │ the best option NOW     │   │
   └─────────────────────────┘   │
                                 ▼
   ┌─────────────────────────┐
   │ Never reconsider        │
   │ previous choices        │
   └─────────────────────────┘

2. DECISION TREE VISUALIZATION:

   67¢
   ├─25¢→ 42¢
   │     ├─25¢→ 17¢
   │     │     ├─10¢→ 7¢
   │     │     │     ├─5¢→ 2¢
   │     │     │     │   ├─1¢→ 1¢
   │     │     │     │   │   └─1¢→ 0¢ ✓
   │     │     │     │   └─... (other paths)
   │     │     │     └─... (other paths)
   │     │     └─... (other paths)
   │     └─... (other paths)
   └─... (other paths never explored)

3. ALGORITHM TEMPLATE:
   ┌──────────────────────────────────────┐
   │ function greedy_algorithm(problem):  │
   │   solution = []                      │
   │   while not_solved(problem):         │
   │     choice = best_local_choice()     │ ← KEY: Greedy choice
   │     solution.add(choice)             │
   │     update_problem_state()           │
   │   return solution                    │
   └──────────────────────────────────────┘

PROS & CONS:
════════════

ADVANTAGES:               DISADVANTAGES:
┌─────────────────┐      ┌─────────────────────┐
│ • Simple        │      │ • May not find      │
│ • Fast O(n)     │      │   global optimum    │
│ • Memory eff.   │      │ • Problem-dependent │
│ • Easy to code  │      │ • No backtracking   │
└─────────────────┘      └─────────────────────┘

WHEN TO USE GREEDY:
═══════════════════
✓ Problem has greedy choice property
✓ Problem has optimal substructure  
✓ Local optimum leads to global optimum
✓ Examples: Huffman coding, MST, Activity selection

# Comprehensive Guide to Greedy Algorithms

## Table of Contents
1. [Introduction to Greedy Algorithms](#introduction)
2. [Key Characteristics](#characteristics)
3. [When to Use Greedy Algorithms](#when-to-use)
4. [Classic Problems and Implementations](#classic-problems)
5. [Advanced Applications](#advanced-applications)
6. [Optimization Techniques](#optimization)
7. [Testing and Validation](#testing)

## Introduction to Greedy Algorithms {#introduction}

Greedy algorithms make locally optimal choices at each step, hoping to find a global optimum. They follow the principle of making the best choice available at the current moment without considering the overall problem.

### Core Principles
- **Local Optimization**: Make the best choice at each step
- **Irrevocability**: Choices cannot be undone
- **Efficiency**: Often provide O(n log n) or O(n) solutions
- **Approximation**: May not always yield optimal solutions

## Key Characteristics {#characteristics}

### Greedy Choice Property
The optimal solution contains optimal solutions to subproblems, and local optimal choices lead to global optimum.

### Optimal Substructure
A problem exhibits optimal substructure if an optimal solution can be constructed from optimal solutions of its subproblems.

## When to Use Greedy Algorithms {#when-to-use}

✅ **Good for:**
- Optimization problems with greedy choice property
- Problems where local optimum leads to global optimum
- Scheduling and resource allocation
- Graph problems (MST, shortest paths)

❌ **Avoid when:**
- Multiple optimal solutions exist
- Future choices depend heavily on current decisions
- Backtracking might be needed

## Classic Problems and Implementations {#classic-problems}

### 1. Activity Selection Problem

**Problem**: Select maximum number of non-overlapping activities.

#### Python Implementation

```python
from typing import List, Tuple
import heapq

def activity_selection_greedy(activities: List[Tuple[int, int]]) -> List[int]:
    """
    Select maximum number of non-overlapping activities using greedy approach.
    
    Args:
        activities: List of tuples (start_time, end_time)
    
    Returns:
        List of selected activity indices
    """
    if not activities:
        return []
    
    # Create list with indices for tracking
    indexed_activities = [(end, start, i) for i, (start, end) in enumerate(activities)]
    indexed_activities.sort()  # Sort by end time
    
    selected = []
    last_end_time = -1
    
    for end_time, start_time, index in indexed_activities:
        if start_time >= last_end_time:
            selected.append(index)
            last_end_time = end_time
    
    return selected

def activity_selection_weighted(activities: List[Tuple[int, int, float]]) -> Tuple[List[int], float]:
    """
    Select activities to maximize total weight (not necessarily optimal with greedy).
    
    Args:
        activities: List of tuples (start_time, end_time, weight)
    
    Returns:
        Tuple of (selected indices, total weight)
    """
    if not activities:
        return [], 0.0
    
    # Sort by weight/duration ratio (heuristic)
    indexed_activities = []
    for i, (start, end, weight) in enumerate(activities):
        duration = end - start
        ratio = weight / duration if duration > 0 else float('inf')
        indexed_activities.append((ratio, end, start, weight, i))
    
    indexed_activities.sort(reverse=True)  # Sort by ratio descending
    
    selected = []
    total_weight = 0.0
    occupied_times = []
    
    for ratio, end_time, start_time, weight, index in indexed_activities:
        # Check if this activity conflicts with already selected ones
        conflicts = any(not (end_time <= s or start_time >= e) 
                       for s, e in occupied_times)
        
        if not conflicts:
            selected.append(index)
            total_weight += weight
            occupied_times.append((start_time, end_time))
    
    return selected, total_weight

# Example usage and testing
if __name__ == "__main__":
    # Basic activity selection
    activities = [(1, 4), (3, 5), (0, 6), (5, 7), (3, 9), (5, 9), (6, 10), (8, 11)]
    selected = activity_selection_greedy(activities)
    print(f"Selected activities: {selected}")
    print(f"Activities: {[activities[i] for i in selected]}")
    
    # Weighted activity selection
    weighted_activities = [(1, 4, 3), (3, 5, 4), (0, 6, 2), (5, 7, 6)]
    selected_weighted, total = activity_selection_weighted(weighted_activities)
    print(f"Weighted selection: {selected_weighted}, Total weight: {total}")
```

#### Rust Implementation

```rust
use std::cmp::Ordering;

#[derive(Debug, Clone)]
pub struct Activity {
    pub start: i32,
    pub end: i32,
    pub weight: Option<f64>,
}

impl Activity {
    pub fn new(start: i32, end: i32) -> Self {
        Self { start, end, weight: None }
    }
    
    pub fn with_weight(start: i32, end: i32, weight: f64) -> Self {
        Self { start, end, weight: Some(weight) }
    }
    
    pub fn duration(&self) -> i32 {
        self.end - self.start
    }
}

pub fn activity_selection_greedy(activities: &[Activity]) -> Vec<usize> {
    if activities.is_empty() {
        return Vec::new();
    }
    
    // Create indexed activities and sort by end time
    let mut indexed_activities: Vec<(usize, &Activity)> = 
        activities.iter().enumerate().collect();
    
    indexed_activities.sort_by(|a, b| a.1.end.cmp(&b.1.end));
    
    let mut selected = Vec::new();
    let mut last_end_time = i32::MIN;
    
    for (index, activity) in indexed_activities {
        if activity.start >= last_end_time {
            selected.push(index);
            last_end_time = activity.end;
        }
    }
    
    selected
}

pub fn activity_selection_weighted(activities: &[Activity]) -> (Vec<usize>, f64) {
    if activities.is_empty() {
        return (Vec::new(), 0.0);
    }
    
    // Create indexed activities with weight/duration ratio
    let mut indexed_activities: Vec<(f64, i32, usize, &Activity)> = activities
        .iter()
        .enumerate()
        .filter_map(|(i, activity)| {
            activity.weight.map(|w| {
                let ratio = if activity.duration() > 0 {
                    w / activity.duration() as f64
                } else {
                    f64::INFINITY
                };
                (ratio, activity.end, i, activity)
            })
        })
        .collect();
    
    // Sort by ratio descending, then by end time
    indexed_activities.sort_by(|a, b| {
        b.0.partial_cmp(&a.0)
            .unwrap_or(Ordering::Equal)
            .then_with(|| a.1.cmp(&b.1))
    });
    
    let mut selected = Vec::new();
    let mut total_weight = 0.0;
    let mut occupied_times = Vec::new();
    
    for (_, _, index, activity) in indexed_activities {
        // Check for conflicts
        let conflicts = occupied_times.iter().any(|(s, e)| {
            !(activity.end <= *s || activity.start >= *e)
        });
        
        if !conflicts {
            selected.push(index);
            if let Some(weight) = activity.weight {
                total_weight += weight;
            }
            occupied_times.push((activity.start, activity.end));
        }
    }
    
    (selected, total_weight)
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_activity_selection() {
        let activities = vec![
            Activity::new(1, 4),
            Activity::new(3, 5),
            Activity::new(0, 6),
            Activity::new(5, 7),
            Activity::new(3, 9),
            Activity::new(5, 9),
            Activity::new(6, 10),
            Activity::new(8, 11),
        ];
        
        let selected = activity_selection_greedy(&activities);
        println!("Selected activities: {:?}", selected);
        
        // Verify non-overlapping
        let mut prev_end = i32::MIN;
        for &i in &selected {
            assert!(activities[i].start >= prev_end);
            prev_end = activities[i].end;
        }
    }
}
```

### 2. Fractional Knapsack Problem

#### Python Implementation

```python
from typing import List, Tuple, NamedTuple

class Item(NamedTuple):
    value: float
    weight: float
    index: int
    
    @property
    def ratio(self) -> float:
        return self.value / self.weight if self.weight > 0 else float('inf')

def fractional_knapsack(capacity: float, items: List[Tuple[float, float]]) -> Tuple[float, List[Tuple[int, float]]]:
    """
    Solve fractional knapsack problem using greedy approach.
    
    Args:
        capacity: Maximum weight capacity
        items: List of (value, weight) tuples
    
    Returns:
        Tuple of (total_value, list of (item_index, fraction_taken))
    """
    if capacity <= 0 or not items:
        return 0.0, []
    
    # Create items with indices and sort by value/weight ratio
    indexed_items = [Item(value, weight, i) for i, (value, weight) in enumerate(items)]
    indexed_items.sort(key=lambda x: x.ratio, reverse=True)
    
    total_value = 0.0
    solution = []
    remaining_capacity = capacity
    
    for item in indexed_items:
        if remaining_capacity <= 0:
            break
            
        if item.weight <= remaining_capacity:
            # Take the whole item
            total_value += item.value
            solution.append((item.index, 1.0))
            remaining_capacity -= item.weight
        else:
            # Take fraction of the item
            fraction = remaining_capacity / item.weight
            total_value += item.value * fraction
            solution.append((item.index, fraction))
            remaining_capacity = 0
    
    return total_value, solution

def bounded_fractional_knapsack(capacity: float, items: List[Tuple[float, float, int]]) -> Tuple[float, List[Tuple[int, float]]]:
    """
    Fractional knapsack with bounded quantities.
    
    Args:
        capacity: Maximum weight capacity
        items: List of (value, weight, max_quantity) tuples
    
    Returns:
        Tuple of (total_value, list of (item_index, total_fraction))
    """
    if capacity <= 0 or not items:
        return 0.0, []
    
    # Expand items based on quantities and sort by ratio
    expanded_items = []
    for i, (value, weight, quantity) in enumerate(items):
        if weight > 0:
            ratio = value / weight
            expanded_items.append((ratio, value, weight, quantity, i))
    
    expanded_items.sort(reverse=True)
    
    total_value = 0.0
    solution = []
    remaining_capacity = capacity
    
    for ratio, value, weight, max_quantity, original_index in expanded_items:
        if remaining_capacity <= 0:
            break
            
        # Calculate how many units we can take
        max_units_by_weight = remaining_capacity / weight
        units_to_take = min(max_quantity, max_units_by_weight)
        
        if units_to_take > 0:
            total_value += value * units_to_take
            solution.append((original_index, units_to_take / max_quantity))
            remaining_capacity -= weight * units_to_take
    
    return total_value, solution
```

#### Rust Implementation

```rust
use std::cmp::Ordering;

#[derive(Debug, Clone)]
pub struct KnapsackItem {
    pub value: f64,
    pub weight: f64,
    pub max_quantity: Option<i32>,
}

impl KnapsackItem {
    pub fn new(value: f64, weight: f64) -> Self {
        Self { value, weight, max_quantity: None }
    }
    
    pub fn with_quantity(value: f64, weight: f64, quantity: i32) -> Self {
        Self { value, weight, max_quantity: Some(quantity) }
    }
    
    pub fn ratio(&self) -> f64 {
        if self.weight > 0.0 {
            self.value / self.weight
        } else {
            f64::INFINITY
        }
    }
}

#[derive(Debug)]
pub struct KnapsackSolution {
    pub total_value: f64,
    pub items: Vec<(usize, f64)>, // (index, fraction_taken)
}

pub fn fractional_knapsack(capacity: f64, items: &[KnapsackItem]) -> KnapsackSolution {
    if capacity <= 0.0 || items.is_empty() {
        return KnapsackSolution {
            total_value: 0.0,
            items: Vec::new(),
        };
    }
    
    // Create indexed items and sort by value/weight ratio
    let mut indexed_items: Vec<(f64, usize, &KnapsackItem)> = items
        .iter()
        .enumerate()
        .map(|(i, item)| (item.ratio(), i, item))
        .collect();
    
    indexed_items.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap_or(Ordering::Equal));
    
    let mut total_value = 0.0;
    let mut solution_items = Vec::new();
    let mut remaining_capacity = capacity;
    
    for (_, index, item) in indexed_items {
        if remaining_capacity <= 0.0 {
            break;
        }
        
        if item.weight <= remaining_capacity {
            // Take the whole item
            total_value += item.value;
            solution_items.push((index, 1.0));
            remaining_capacity -= item.weight;
        } else {
            // Take fraction of the item
            let fraction = remaining_capacity / item.weight;
            total_value += item.value * fraction;
            solution_items.push((index, fraction));
            remaining_capacity = 0.0;
        }
    }
    
    KnapsackSolution {
        total_value,
        items: solution_items,
    }
}

pub fn bounded_fractional_knapsack(capacity: f64, items: &[KnapsackItem]) -> KnapsackSolution {
    if capacity <= 0.0 || items.is_empty() {
        return KnapsackSolution {
            total_value: 0.0,
            items: Vec::new(),
        };
    }
    
    let mut indexed_items: Vec<(f64, usize, &KnapsackItem)> = items
        .iter()
        .enumerate()
        .filter(|(_, item)| item.weight > 0.0)
        .map(|(i, item)| (item.ratio(), i, item))
        .collect();
    
    indexed_items.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap_or(Ordering::Equal));
    
    let mut total_value = 0.0;
    let mut solution_items = Vec::new();
    let mut remaining_capacity = capacity;
    
    for (_, index, item) in indexed_items {
        if remaining_capacity <= 0.0 {
            break;
        }
        
        let max_quantity = item.max_quantity.unwrap_or(1) as f64;
        let max_units_by_weight = remaining_capacity / item.weight;
        let units_to_take = max_quantity.min(max_units_by_weight);
        
        if units_to_take > 0.0 {
            total_value += item.value * units_to_take;
            solution_items.push((index, units_to_take / max_quantity));
            remaining_capacity -= item.weight * units_to_take;
        }
    }
    
    KnapsackSolution {
        total_value,
        items: solution_items,
    }
}
```

### 3. Huffman Coding

#### Python Implementation

```python
import heapq
from typing import Dict, Optional, Tuple, Counter
from dataclasses import dataclass

@dataclass
class HuffmanNode:
    char: Optional[str]
    freq: int
    left: Optional['HuffmanNode'] = None
    right: Optional['HuffmanNode'] = None
    
    def __lt__(self, other):
        if self.freq != other.freq:
            return self.freq < other.freq
        # For consistent ordering when frequencies are equal
        if self.char is None and other.char is None:
            return False
        if self.char is None:
            return False
        if other.char is None:
            return True
        return self.char < other.char
    
    def is_leaf(self) -> bool:
        return self.left is None and self.right is None

class HuffmanCoding:
    def __init__(self):
        self.root: Optional[HuffmanNode] = None
        self.codes: Dict[str, str] = {}
        self.reverse_codes: Dict[str, str] = {}
    
    def build_tree(self, text: str) -> None:
        """Build Huffman tree from input text."""
        if not text:
            return
        
        # Count frequencies
        frequency = Counter(text)
        
        # Handle single character case
        if len(frequency) == 1:
            char = list(frequency.keys())[0]
            self.root = HuffmanNode(char, frequency[char])
            self.codes[char] = '0'
            self.reverse_codes['0'] = char
            return
        
        # Create priority queue
        heap = [HuffmanNode(char, freq) for char, freq in frequency.items()]
        heapq.heapify(heap)
        
        # Build tree
        while len(heap) > 1:
            left = heapq.heappop(heap)
            right = heapq.heappop(heap)
            
            merged = HuffmanNode(None, left.freq + right.freq, left, right)
            heapq.heappush(heap, merged)
        
        self.root = heap[0]
        self._generate_codes(self.root, "")
    
    def _generate_codes(self, node: HuffmanNode, code: str) -> None:
        """Generate Huffman codes for each character."""
        if node is None:
            return
        
        if node.is_leaf():
            # Handle root-only case
            if code == "":
                code = "0"
            self.codes[node.char] = code
            self.reverse_codes[code] = node.char
            return
        
        self._generate_codes(node.left, code + "0")
        self._generate_codes(node.right, code + "1")
    
    def encode(self, text: str) -> str:
        """Encode text using Huffman coding."""
        if not text or not self.codes:
            return ""
        
        return ''.join(self.codes[char] for char in text)
    
    def decode(self, encoded: str) -> str:
        """Decode Huffman encoded text."""
        if not encoded or not self.root:
            return ""
        
        decoded = []
        current = self.root
        
        # Handle single character tree
        if current.is_leaf():
            return current.char * len(encoded)
        
        for bit in encoded:
            if bit == '0':
                current = current.left
            else:
                current = current.right
            
            if current.is_leaf():
                decoded.append(current.char)
                current = self.root
        
        return ''.join(decoded)
    
    def get_compression_ratio(self, original_text: str) -> float:
        """Calculate compression ratio."""
        if not original_text:
            return 0.0
        
        original_bits = len(original_text) * 8  # ASCII
        encoded = self.encode(original_text)
        compressed_bits = len(encoded)
        
        return compressed_bits / original_bits if original_bits > 0 else 0.0
    
    def print_codes(self) -> None:
        """Print Huffman codes for each character."""
        print("Character | Huffman Code")
        print("-" * 25)
        for char, code in sorted(self.codes.items()):
            display_char = repr(char) if char in [' ', '\n', '\t'] else char
            print(f"{display_char:^9} | {code}")

# Example usage
if __name__ == "__main__":
    huffman = HuffmanCoding()
    text = "this is an example of a huffman tree"
    
    huffman.build_tree(text)
    huffman.print_codes()
    
    encoded = huffman.encode(text)
    decoded = huffman.decode(encoded)
    
    print(f"\nOriginal: {text}")
    print(f"Encoded: {encoded}")
    print(f"Decoded: {decoded}")
    print(f"Compression ratio: {huffman.get_compression_ratio(text):.2f}")
```

#### Rust Implementation

```rust
use std::collections::{BinaryHeap, HashMap};
use std::cmp::Reverse;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HuffmanNode {
    pub char: Option<char>,
    pub freq: usize,
    pub left: Option<Box<HuffmanNode>>,
    pub right: Option<Box<HuffmanNode>>,
}

impl HuffmanNode {
    pub fn new_leaf(char: char, freq: usize) -> Self {
        Self {
            char: Some(char),
            freq,
            left: None,
            right: None,
        }
    }
    
    pub fn new_internal(freq: usize, left: HuffmanNode, right: HuffmanNode) -> Self {
        Self {
            char: None,
            freq,
            left: Some(Box::new(left)),
            right: Some(Box::new(right)),
        }
    }
    
    pub fn is_leaf(&self) -> bool {
        self.left.is_none() && self.right.is_none()
    }
}

impl Ord for HuffmanNode {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        // Reverse for min-heap behavior
        other.freq.cmp(&self.freq)
            .then_with(|| {
                // Consistent ordering for nodes with same frequency
                match (&self.char, &other.char) {
                    (Some(a), Some(b)) => a.cmp(b),
                    (Some(_), None) => std::cmp::Ordering::Less,
                    (None, Some(_)) => std::cmp::Ordering::Greater,
                    (None, None) => std::cmp::Ordering::Equal,
                }
            })
    }
}

impl PartialOrd for HuffmanNode {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}

#[derive(Debug)]
pub struct HuffmanCoding {
    root: Option<HuffmanNode>,
    codes: HashMap<char, String>,
    reverse_codes: HashMap<String, char>,
}

impl HuffmanCoding {
    pub fn new() -> Self {
        Self {
            root: None,
            codes: HashMap::new(),
            reverse_codes: HashMap::new(),
        }
    }
    
    pub fn build_tree(&mut self, text: &str) {
        if text.is_empty() {
            return;
        }
        
        // Count frequencies
        let mut frequency = HashMap::new();
        for ch in text.chars() {
            *frequency.entry(ch).or_insert(0) += 1;
        }
        
        // Handle single character case
        if frequency.len() == 1 {
            let (ch, freq) = frequency.into_iter().next().unwrap();
            self.root = Some(HuffmanNode::new_leaf(ch, freq));
            self.codes.insert(ch, "0".to_string());
            self.reverse_codes.insert("0".to_string(), ch);
            return;
        }
        
        // Create priority queue (min-heap)
        let mut heap = BinaryHeap::new();
        for (ch, freq) in frequency {
            heap.push(HuffmanNode::new_leaf(ch, freq));
        }
        
        // Build tree
        while heap.len() > 1 {
            let left = heap.pop().unwrap();
            let right = heap.pop().unwrap();
            let merged = HuffmanNode::new_internal(left.freq + right.freq, left, right);
            heap.push(merged);
        }
        
        if let Some(root) = heap.pop() {
            self.root = Some(root);
            self.generate_codes();
        }
    }
    
    fn generate_codes(&mut self) {
        self.codes.clear();
        self.reverse_codes.clear();
        
        if let Some(ref root) = self.root {
            if root.is_leaf() {
                // Single character case
                if let Some(ch) = root.char {
                    self.codes.insert(ch, "0".to_string());
                    self.reverse_codes.insert("0".to_string(), ch);
                }
            } else {
                self.generate_codes_recursive(root, String::new());
            }
        }
    }
    
    fn generate_codes_recursive(&mut self, node: &HuffmanNode, code: String) {
        if node.is_leaf() {
            if let Some(ch) = node.char {
                self.codes.insert(ch, code.clone());
                self.reverse_codes.insert(code, ch);
            }
            return;
        }
        
        if let Some(ref left) = node.left {
            self.generate_codes_recursive(left, code.clone() + "0");
        }
        
        if let Some(ref right) = node.right {
            self.generate_codes_recursive(right, code + "1");
        }
    }
    
    pub fn encode(&self, text: &str) -> String {
        text.chars()
            .filter_map(|ch| self.codes.get(&ch))
            .cloned()
            .collect::<Vec<String>>()
            .join("")
    }
    
    pub fn decode(&self, encoded: &str) -> String {
        if encoded.is_empty() || self.root.is_none() {
            return String::new();
        }
        
        let root = self.root.as_ref().unwrap();
        
        // Handle single character tree
        if root.is_leaf() {
            if let Some(ch) = root.char {
                return ch.to_string().repeat(encoded.len());
            }
            return String::new();
        }
        
        let mut decoded = String::new();
        let mut current = root;
        
        for bit in encoded.chars() {
            current = match bit {
                '0' => current.left.as_ref(),
                '1' => current.right.as_ref(),
                _ => continue,
            }.unwrap_or(root);
            
            if current.is_leaf() {
                if let Some(ch) = current.char {
                    decoded.push(ch);
                }
                current = root;
            }
        }
        
        decoded
    }
    
    pub fn get_compression_ratio(&self, original_text: &str) -> f64 {
        if original_text.is_empty() {
            return 0.0;
        }
        
        let original_bits = original_text.len() * 8; // ASCII
        let encoded = self.encode(original_text);
        let compressed_bits = encoded.len();
        
        if original_bits > 0 {
            compressed_bits as f64 / original_bits as f64
        } else {
            0.0
        }
    }
    
    pub fn print_codes(&self) {
        println!("Character | Huffman Code");
        println!("{}", "-".repeat(25));
        
        let mut sorted_codes: Vec<_> = self.codes.iter().collect();
        sorted_codes.sort_by_key(|(ch, _)| *ch);
        
        for (ch, code) in sorted_codes {
            let display_char = match *ch {
                ' ' => "' '",
                '\n' => "'\\n'",
                '\t' => "'\\t'",
                c => &format!("'{}'", c),
            };
            println!("{:^9} | {}", display_char, code);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_huffman_coding() {
        let mut huffman = HuffmanCoding::new();
        let text = "this is an example of a huffman tree";
        
        huffman.build_tree(text);
        
        let encoded = huffman.encode(text);
        let decoded = huffman.decode(&encoded);
        
        assert_eq!(text, decoded);
        assert!(huffman.get_compression_ratio(text) < 1.0);
    }
    
    #[test]
    fn test_single_character() {
        let mut huffman = HuffmanCoding::new();
        let text = "aaaa";
        
        huffman.build_tree(text);
        
        let encoded = huffman.encode(text);
        let decoded = huffman.decode(&encoded);
        
        assert_eq!(text, decoded);
    }
}
```

### 4. Minimum Spanning Tree (Kruskal's Algorithm)

#### Python Implementation

```python
from typing import List, Tuple, Set
from dataclasses import dataclass

@dataclass
class Edge:
    u: int
    v: int
    weight: float
    
    def __lt__(self, other):
        return self.weight < other.weight

class UnionFind:
    """Union-Find (Disjoint Set) data structure with path compression and union by rank."""
    
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.components = n
    
    def find(self, x: int) -> int:
        """Find root with path compression."""
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]
    
    def union(self, x: int, y: int) -> bool:
        """Union two sets by rank. Returns True if union was performed."""
        root_x = self.find(x)
        root_y = self.find(y)
        
        if root_x == root_y:
            return False
        
        # Union by rank
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1
        
        self.components -= 1
        return True
    
    def connected(self, x: int, y: int) -> bool:
        """Check if two elements are in the same set."""
        return self.find(x) == self.find(y)

def kruskals_mst(n: int, edges: List[Edge]) -> Tuple[List[Edge], float]:
    """
    Find Minimum Spanning Tree using Kruskal's algorithm.
    
    Args:
        n: Number of vertices
        edges: List of edges
    
    Returns:
        Tuple of (MST edges, total weight)
    """
    if n <= 0 or not edges:
        return [], 0.0
    
    # Sort edges by weight
    sorted_edges = sorted(edges)
    
    # Initialize Union-Find
    uf = UnionFind(n)
    mst_edges = []
    total_weight = 0.0
    
    for edge in sorted_edges:
        if uf.union(edge.u, edge.v):
            mst_edges.append(edge)
            total_weight += edge.weight
            
            # Early termination: MST has n-1 edges
            if len(mst_edges) == n - 1:
                break
    
    return mst_edges, total_weight

def prims_mst(n: int, edges: List[Edge]) -> Tuple[List[Edge], float]:
    """
    Find Minimum Spanning Tree using Prim's algorithm.
    
    Args:
        n: Number of vertices
        edges: List of edges
    
    Returns:
        Tuple of (MST edges, total weight)
    """
    if n <= 0 or not edges:
        return [], 0.0
    
    # Build adjacency list
    graph = [[] for _ in range(n)]
    for edge in edges:
        graph[edge.u].append((edge.v, edge.weight, edge))
        graph[edge.v].append((edge.u, edge.weight, edge))
    
    visited = [False] * n
    mst_edges = []
    total_weight = 0.0
    
    # Use heap to get minimum weight edge
    import heapq
    min_heap = [(0, 0, None)]  # (weight, vertex, edge)
    
    while min_heap and len(mst_edges) < n - 1:
        weight, u, edge = heapq.heappop(min_heap)
        
        if visited[u]:
            continue
            
        visited[u] = True
        if edge is not None:
            mst_edges.append(edge)
            total_weight += weight
        
        # Add all adjacent edges to heap
        for v, w, e in graph[u]:
            if not visited[v]:
                heapq.heappush(min_heap, (w, v, e))
    
    return mst_edges, total_weight

# Example usage
if __name__ == "__main__":
    # Example graph
    edges = [
        Edge(0, 1, 4), Edge(0, 7, 8), Edge(1, 2, 8), Edge(1, 7, 11),
        Edge(2, 3, 7), Edge(2, 8, 2), Edge(2, 5, 4), Edge(3, 4, 9),
        Edge(3, 5, 14), Edge(4, 5, 10), Edge(5, 6, 2), Edge(6, 7, 1),
        Edge(6, 8, 6), Edge(7, 8, 7)
    ]
    
    n_vertices = 9
    
    # Kruskal's MST
    mst_kruskal, weight_kruskal = kruskals_mst(n_vertices, edges)
    print("Kruskal's MST:")
    for edge in mst_kruskal:
        print(f"  {edge.u} -- {edge.v} (weight: {edge.weight})")
    print(f"Total weight: {weight_kruskal}")
    
    # Prim's MST
    mst_prim, weight_prim = prims_mst(n_vertices, edges)
    print("\nPrim's MST:")
    for edge in mst_prim:
        print(f"  {edge.u} -- {edge.v} (weight: {edge.weight})")
    print(f"Total weight: {weight_prim}")
```

#### Rust Implementation

```rust
use std::collections::BinaryHeap;
use std::cmp::Reverse;

#[derive(Debug, Clone, PartialEq)]
pub struct Edge {
    pub u: usize,
    pub v: usize,
    pub weight: f64,
}

impl Edge {
    pub fn new(u: usize, v: usize, weight: f64) -> Self {
        Self { u, v, weight }
    }
}

impl Eq for Edge {}

impl PartialOrd for Edge {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for Edge {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        self.weight.partial_cmp(&other.weight).unwrap_or(std::cmp::Ordering::Equal)
    }
}

pub struct UnionFind {
    parent: Vec<usize>,
    rank: Vec<usize>,
    components: usize,
}

impl UnionFind {
    pub fn new(n: usize) -> Self {
        Self {
            parent: (0..n).collect(),
            rank: vec![0; n],
            components: n,
        }
    }
    
    pub fn find(&mut self, x: usize) -> usize {
        if self.parent[x] != x {
            self.parent[x] = self.find(self.parent[x]);
        }
        self.parent[x]
    }
    
    pub fn union(&mut self, x: usize, y: usize) -> bool {
        let root_x = self.find(x);
        let root_y = self.find(y);
        
        if root_x == root_y {
            return false;
        }
        
        match self.rank[root_x].cmp(&self.rank[root_y]) {
            std::cmp::Ordering::Less => self.parent[root_x] = root_y,
            std::cmp::Ordering::Greater => self.parent[root_y] = root_x,
            std::cmp::Ordering::Equal => {
                self.parent[root_y] = root_x;
                self.rank[root_x] += 1;
            }
        }
        
        self.components -= 1;
        true
    }
    
    pub fn connected(&mut self, x: usize, y: usize) -> bool {
        self.find(x) == self.find(y)
    }
}

pub fn kruskals_mst(n: usize, edges: &[Edge]) -> (Vec<Edge>, f64) {
    if n == 0 || edges.is_empty() {
        return (Vec::new(), 0.0);
    }
    
    let mut sorted_edges = edges.to_vec();
    sorted_edges.sort();
    
    let mut uf = UnionFind::new(n);
    let mut mst_edges = Vec::new();
    let mut total_weight = 0.0;
    
    for edge in sorted_edges {
        if uf.union(edge.u, edge.v) {
            total_weight += edge.weight;
            mst_edges.push(edge);
            
            if mst_edges.len() == n - 1 {
                break;
            }
        }
    }
    
    (mst_edges, total_weight)
}

pub fn prims_mst(n: usize, edges: &[Edge]) -> (Vec<Edge>, f64) {
    if n == 0 || edges.is_empty() {
        return (Vec::new(), 0.0);
    }
    
    // Build adjacency list
    let mut graph = vec![Vec::new(); n];
    for edge in edges {
        graph[edge.u].push((edge.v, edge.weight, edge));
        graph[edge.v].push((edge.u, edge.weight, edge));
    }
    
    let mut visited = vec![false; n];
    let mut mst_edges = Vec::new();
    let mut total_weight = 0.0;
    
    // Min heap: (weight, vertex, edge)
    let mut heap = BinaryHeap::new();
    heap.push(Reverse((0.0, 0, None)));
    
    while let Some(Reverse((weight, u, edge))) = heap.pop() {
        if visited[u] {
            continue;
        }
        
        visited[u] = true;
        if let Some(e) = edge {
            mst_edges.push(e.clone());
            total_weight += weight;
        }
        
        if mst_edges.len() == n - 1 {
            break;
        }
        
        for &(v, w, ref e) in &graph[u] {
            if !visited[v] {
                heap.push(Reverse((w, v, Some(e))));
            }
        }
    }
    
    (mst_edges, total_weight)
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_mst_algorithms() {
        let edges = vec![
            Edge::new(0, 1, 4.0), Edge::new(0, 7, 8.0), Edge::new(1, 2, 8.0),
            Edge::new(1, 7, 11.0), Edge::new(2, 3, 7.0), Edge::new(2, 8, 2.0),
            Edge::new(2, 5, 4.0), Edge::new(3, 4, 9.0), Edge::new(3, 5, 14.0),
            Edge::new(4, 5, 10.0), Edge::new(5, 6, 2.0), Edge::new(6, 7, 1.0),
            Edge::new(6, 8, 6.0), Edge::new(7, 8, 7.0)
        ];
        
        let n = 9;
        
        let (mst_kruskal, weight_kruskal) = kruskals_mst(n, &edges);
        let (mst_prim, weight_prim) = prims_mst(n, &edges);
        
        assert_eq!(mst_kruskal.len(), n - 1);
        assert_eq!(mst_prim.len(), n - 1);
        assert!((weight_kruskal - weight_prim).abs() < 1e-10);
    }
}

### 5. Dijkstra's Shortest Path Algorithm

#### Python Implementation

```python
import heapq
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import math

@dataclass
class WeightedEdge:
    to: int
    weight: float

class Graph:
    def __init__(self, n: int):
        self.n = n
        self.adj: List[List[WeightedEdge]] = [[] for _ in range(n)]
    
    def add_edge(self, from_vertex: int, to_vertex: int, weight: float, bidirectional: bool = True):
        """Add edge to the graph."""
        self.adj[from_vertex].append(WeightedEdge(to_vertex, weight))
        if bidirectional:
            self.adj[to_vertex].append(WeightedEdge(from_vertex, weight))
    
    def dijkstra(self, start: int) -> Tuple[List[float], List[Optional[int]]]:
        """
        Find shortest paths from start vertex to all other vertices.
        
        Returns:
            Tuple of (distances, predecessors)
        """
        if start < 0 or start >= self.n:
            raise ValueError(f"Start vertex {start} out of range")
        
        distances = [math.inf] * self.n
        predecessors = [None] * self.n
        distances[start] = 0.0
        
        # Priority queue: (distance, vertex)
        pq = [(0.0, start)]
        visited = [False] * self.n
        
        while pq:
            current_dist, u = heapq.heappop(pq)
            
            if visited[u]:
                continue
            
            visited[u] = True
            
            # Early termination if we've visited all vertices
            if all(visited):
                break
            
            for edge in self.adj[u]:
                v = edge.to
                weight = edge.weight
                
                if not visited[v]:
                    new_dist = current_dist + weight
                    if new_dist < distances[v]:
                        distances[v] = new_dist
                        predecessors[v] = u
                        heapq.heappush(pq, (new_dist, v))
        
        return distances, predecessors
    
    def shortest_path(self, start: int, end: int) -> Tuple[float, List[int]]:
        """
        Find shortest path between two vertices.
        
        Returns:
            Tuple of (distance, path)
        """
        distances, predecessors = self.dijkstra(start)
        
        if distances[end] == math.inf:
            return math.inf, []
        
        # Reconstruct path
        path = []
        current = end
        while current is not None:
            path.append(current)
            current = predecessors[current]
        
        path.reverse()
        return distances[end], path
    
    def all_pairs_shortest_paths(self) -> Dict[Tuple[int, int], Tuple[float, List[int]]]:
        """
        Find shortest paths between all pairs of vertices.
        
        Returns:
            Dictionary mapping (start, end) to (distance, path)
        """
        all_paths = {}
        
        for start in range(self.n):
            distances, predecessors = self.dijkstra(start)
            
            for end in range(self.n):
                if distances[end] != math.inf:
                    # Reconstruct path
                    path = []
                    current = end
                    while current is not None:
                        path.append(current)
                        current = predecessors[current]
                    path.reverse()
                    
                    all_paths[(start, end)] = (distances[end], path)
        
        return all_paths

class DijkstraWithPriorityUpdates:
    """Dijkstra implementation with priority queue updates (using indexed heap)."""
    
    def __init__(self, graph: Graph):
        self.graph = graph
    
    def dijkstra_with_decrease_key(self, start: int) -> Tuple[List[float], List[Optional[int]]]:
        """
        Dijkstra with decrease-key operation simulation.
        """
        n = self.graph.n
        distances = [math.inf] * n
        predecessors = [None] * n
        distances[start] = 0.0
        
        # Use dictionary to track vertices in priority queue
        in_queue = {i: True for i in range(n)}
        
        while in_queue:
            # Find vertex with minimum distance
            u = min(in_queue.keys(), key=lambda x: distances[x])
            del in_queue[u]
            
            for edge in self.graph.adj[u]:
                v = edge.to
                weight = edge.weight
                
                if v in in_queue:
                    new_dist = distances[u] + weight
                    if new_dist < distances[v]:
                        distances[v] = new_dist
                        predecessors[v] = u
        
        return distances, predecessors

# Example usage and testing
if __name__ == "__main__":
    # Create example graph
    graph = Graph(6)
    graph.add_edge(0, 1, 4, False)
    graph.add_edge(0, 2, 2, False)
    graph.add_edge(1, 2, 1, False)
    graph.add_edge(1, 3, 5, False)
    graph.add_edge(2, 3, 8, False)
    graph.add_edge(2, 4, 10, False)
    graph.add_edge(3, 4, 2, False)
    graph.add_edge(3, 5, 6, False)
    graph.add_edge(4, 5, 3, False)
    
    # Single source shortest paths
    distances, predecessors = graph.dijkstra(0)
    print("Distances from vertex 0:")
    for i, dist in enumerate(distances):
        if dist != math.inf:
            print(f"  To vertex {i}: {dist}")
        else:
            print(f"  To vertex {i}: unreachable")
    
    # Shortest path between specific vertices
    dist, path = graph.shortest_path(0, 5)
    print(f"\nShortest path from 0 to 5: {path} (distance: {dist})")
    
    # All pairs shortest paths
    all_paths = graph.all_pairs_shortest_paths()
    print(f"\nTotal reachable pairs: {len(all_paths)}")
```

#### Rust Implementation

```rust
use std::collections::{BinaryHeap, HashMap};
use std::cmp::Reverse;

#[derive(Debug, Clone)]
pub struct WeightedEdge {
    pub to: usize,
    pub weight: f64,
}

impl WeightedEdge {
    pub fn new(to: usize, weight: f64) -> Self {
        Self { to, weight }
    }
}

#[derive(Debug)]
pub struct Graph {
    n: usize,
    adj: Vec<Vec<WeightedEdge>>,
}

impl Graph {
    pub fn new(n: usize) -> Self {
        Self {
            n,
            adj: vec![Vec::new(); n],
        }
    }
    
    pub fn add_edge(&mut self, from: usize, to: usize, weight: f64, bidirectional: bool) {
        if from < self.n {
            self.adj[from].push(WeightedEdge::new(to, weight));
        }
        if bidirectional && to < self.n {
            self.adj[to].push(WeightedEdge::new(from, weight));
        }
    }
    
    pub fn dijkstra(&self, start: usize) -> (Vec<f64>, Vec<Option<usize>>) {
        if start >= self.n {
            return (Vec::new(), Vec::new());
        }
        
        let mut distances = vec![f64::INFINITY; self.n];
        let mut predecessors = vec![None; self.n];
        distances[start] = 0.0;
        
        let mut heap = BinaryHeap::new();
        heap.push(Reverse((0.0, start)));
        let mut visited = vec![false; self.n];
        
        while let Some(Reverse((current_dist, u))) = heap.pop() {
            if visited[u] {
                continue;
            }
            
            visited[u] = true;
            
            for edge in &self.adj[u] {
                let v = edge.to;
                let weight = edge.weight;
                
                if v < self.n && !visited[v] {
                    let new_dist = current_dist + weight;
                    if new_dist < distances[v] {
                        distances[v] = new_dist;
                        predecessors[v] = Some(u);
                        heap.push(Reverse((new_dist, v)));
                    }
                }
            }
        }
        
        (distances, predecessors)
    }
    
    pub fn shortest_path(&self, start: usize, end: usize) -> (f64, Vec<usize>) {
        let (distances, predecessors) = self.dijkstra(start);
        
        if end >= distances.len() || distances[end] == f64::INFINITY {
            return (f64::INFINITY, Vec::new());
        }
        
        let mut path = Vec::new();
        let mut current = Some(end);
        
        while let Some(vertex) = current {
            path.push(vertex);
            current = predecessors[vertex];
        }
        
        path.reverse();
        (distances[end], path)
    }
    
    pub fn all_pairs_shortest_paths(&self) -> HashMap<(usize, usize), (f64, Vec<usize>)> {
        let mut all_paths = HashMap::new();
        
        for start in 0..self.n {
            let (distances, predecessors) = self.dijkstra(start);
            
            for end in 0..self.n {
                if distances[end] != f64::INFINITY {
                    let mut path = Vec::new();
                    let mut current = Some(end);
                    
                    while let Some(vertex) = current {
                        path.push(vertex);
                        current = predecessors[vertex];
                    }
                    
                    path.reverse();
                    all_paths.insert((start, end), (distances[end], path));
                }
            }
        }
        
        all_paths
    }
}

pub struct AStar {
    graph: Graph,
}

impl AStar {
    pub fn new(graph: Graph) -> Self {
        Self { graph }
    }
    
    pub fn a_star<F>(&self, start: usize, goal: usize, heuristic: F) -> (f64, Vec<usize>)
    where
        F: Fn(usize) -> f64,
    {
        if start >= self.graph.n || goal >= self.graph.n {
            return (f64::INFINITY, Vec::new());
        }
        
        let mut open_set = BinaryHeap::new();
        open_set.push(Reverse((heuristic(start), 0.0, start)));
        
        let mut came_from = vec![None; self.graph.n];
        let mut g_score = vec![f64::INFINITY; self.graph.n];
        g_score[start] = 0.0;
        
        let mut closed_set = vec![false; self.graph.n];
        
        while let Some(Reverse((_, current_g, current))) = open_set.pop() {
            if current == goal {
                // Reconstruct path
                let mut path = Vec::new();
                let mut node = Some(current);
                
                while let Some(n) = node {
                    path.push(n);
                    node = came_from[n];
                }
                
                path.reverse();
                return (g_score[goal], path);
            }
            
            if closed_set[current] {
                continue;
            }
            
            closed_set[current] = true;
            
            for edge in &self.graph.adj[current] {
                let neighbor = edge.to;
                
                if neighbor >= self.graph.n || closed_set[neighbor] {
                    continue;
                }
                
                let tentative_g = g_score[current] + edge.weight;
                
                if tentative_g < g_score[neighbor] {
                    came_from[neighbor] = Some(current);
                    g_score[neighbor] = tentative_g;
                    let f_score = tentative_g + heuristic(neighbor);
                    open_set.push(Reverse((f_score, tentative_g, neighbor)));
                }
            }
        }
        
        (f64::INFINITY, Vec::new())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_dijkstra() {
        let mut graph = Graph::new(6);
        graph.add_edge(0, 1, 4.0, false);
        graph.add_edge(0, 2, 2.0, false);
        graph.add_edge(1, 2, 1.0, false);
        graph.add_edge(1, 3, 5.0, false);
        graph.add_edge(2, 3, 8.0, false);
        graph.add_edge(2, 4, 10.0, false);
        graph.add_edge(3, 4, 2.0, false);
        graph.add_edge(3, 5, 6.0, false);
        graph.add_edge(4, 5, 3.0, false);
        
        let (distances, _) = graph.dijkstra(0);
        
        assert_eq!(distances[0], 0.0);
        assert_eq!(distances[1], 3.0); // 0->2->1
        assert_eq!(distances[2], 2.0); // 0->2
        assert_eq!(distances[5], 16.0); // 0->2->1->3->4->5
        
        let (dist, path) = graph.shortest_path(0, 5);
        assert_eq!(dist, 16.0);
        assert_eq!(path, vec![0, 2, 1, 3, 4, 5]);
    }
}

## Advanced Applications {#advanced-applications}

### 6. Job Scheduling Problems

#### Python Implementation

```python
from typing import List, Tuple, NamedTuple
import heapq
from dataclasses import dataclass

@dataclass
class Job:
    id: int
    processing_time: int
    deadline: int
    profit: int = 0
    arrival_time: int = 0
    priority: int = 0

class JobScheduler:
    """Collection of job scheduling algorithms using greedy approaches."""
    
    def shortest_job_first(self, jobs: List[Job]) -> Tuple[List[Job], float]:
        """
        Schedule jobs using Shortest Job First (SJF) algorithm.
        
        Returns:
            Tuple of (scheduled_jobs, average_waiting_time)
        """
        if not jobs:
            return [], 0.0
        
        # Sort by processing time
        sorted_jobs = sorted(jobs, key=lambda x: x.processing_time)
        
        current_time = 0
        total_waiting_time = 0
        
        for job in sorted_jobs:
            total_waiting_time += current_time
            current_time += job.processing_time
        
        average_waiting_time = total_waiting_time / len(jobs)
        return sorted_jobs, average_waiting_time
    
    def shortest_remaining_time_first(self, jobs: List[Job]) -> Tuple[List[Tuple[Job, int, int]], float]:
        """
        Preemptive shortest job first scheduling.
        
        Returns:
            Tuple of (execution_order, average_waiting_time)
        """
        if not jobs:
            return [], 0.0
        
        # Create job instances with remaining time
        job_queue = [(job.processing_time, job.arrival_time, job) for job in jobs]
        job_queue.sort(key=lambda x: x[1])  # Sort by arrival time
        
        current_time = 0
        execution_order = []
        completed_jobs = []
        ready_queue = []
        
        i = 0
        while completed_jobs != len(jobs) or ready_queue:
            # Add arrived jobs to ready queue
            while i < len(job_queue) and job_queue[i][1] <= current_time:
                remaining_time, arrival_time, job = job_queue[i]
                heapq.heappush(ready_queue, (remaining_time, job))
                i += 1
            
            if not ready_queue:
                # CPU idle, jump to next job arrival
                if i < len(job_queue):
                    current_time = job_queue[i][1]
                    continue
                else:
                    break
            
            # Execute job with shortest remaining time
            remaining_time, current_job = heapq.heappop(ready_queue)
            execution_time = min(remaining_time, 1)  # Execute for 1 time unit
            
            execution_order.append((current_job, current_time, current_time + execution_time))
            current_time += execution_time
            remaining_time -= execution_time
            
            if remaining_time > 0:
                heapq.heappush(ready_queue, (remaining_time, current_job))
            else:
                completed_jobs.append(current_job)
        
        # Calculate average waiting time
        job_completion_times = {}
        for job, start, end in execution_order:
            if job not in job_completion_times:
                job_completion_times[job] = end
            else:
                job_completion_times[job] = max(job_completion_times[job], end)
        
        total_waiting_time = sum(
            job_completion_times[job] - job.arrival_time - job.processing_time
            for job in jobs
        )
        
        average_waiting_time = total_waiting_time / len(jobs)
        return execution_order, average_waiting_time
    
    def deadline_scheduling(self, jobs: List[Job]) -> Tuple[List[Job], int]:
        """
        Schedule jobs to maximize profit within deadlines.
        
        Returns:
            Tuple of (scheduled_jobs, total_profit)
        """
        if not jobs:
            return [], 0
        
        # Sort jobs by profit in descending order
        sorted_jobs = sorted(jobs, key=lambda x: x.profit, reverse=True)
        
        # Find maximum deadline
        max_deadline = max(job.deadline for job in jobs)
        
        # Initialize result array
        result = [None] * max_deadline
        total_profit = 0
        
        for job in sorted_jobs:
            # Find the latest available slot before deadline
            for slot in range(min(job.deadline, max_deadline) - 1, -1, -1):
                if result[slot] is None:
                    result[slot] = job
                    total_profit += job.profit
                    break
        
        scheduled_jobs = [job for job in result if job is not None]
        return scheduled_jobs, total_profit
    
    def earliest_deadline_first(self, jobs: List[Job]) -> List[Job]:
        """
        Schedule jobs using Earliest Deadline First (EDF) algorithm.
        
        Returns:
            List of scheduled jobs in execution order
        """
        if not jobs:
            return []
        
        # Sort by deadline
        return sorted(jobs, key=lambda x: x.deadline)
    
    def priority_scheduling(self, jobs: List[Job]) -> List[Job]:
        """
        Schedule jobs by priority (higher priority value = higher priority).
        
        Returns:
            List of jobs in execution order
        """
        if not jobs:
            return []
        
        return sorted(jobs, key=lambda x: x.priority, reverse=True)

# Example usage
if __name__ == "__main__":
    scheduler = JobScheduler()
    
    # Example jobs for SJF
    jobs_sjf = [
        Job(1, 6, 0), Job(2, 8, 0), Job(3, 7, 0), Job(4, 3, 0)
    ]
    
    scheduled, avg_wait = scheduler.shortest_job_first(jobs_sjf)
    print("Shortest Job First:")
    for job in scheduled:
        print(f"  Job {job.id} (time: {job.processing_time})")
    print(f"Average waiting time: {avg_wait}")
    
    # Example jobs for deadline scheduling
    jobs_deadline = [
        Job(1, 3, 4, 50), Job(2, 2, 1, 10), Job(3, 1, 2, 40), 
        Job(4, 2, 3, 30)
    ]
    
    scheduled_deadline, profit = scheduler.deadline_scheduling(jobs_deadline)
    print(f"\nDeadline Scheduling (Total profit: {profit}):")
    for job in scheduled_deadline:
        print(f"  Job {job.id} (profit: {job.profit}, deadline: {job.deadline})")
```

#### Rust Implementation

```rust
use std::collections::BinaryHeap;
use std::cmp::Reverse;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Job {
    pub id: usize,
    pub processing_time: u32,
    pub deadline: u32,
    pub profit: u32,
    pub arrival_time: u32,
    pub priority: u32,
}

impl Job {
    pub fn new(id: usize, processing_time: u32) -> Self {
        Self {
            id,
            processing_time,
            deadline: 0,
            profit: 0,
            arrival_time: 0,
            priority: 0,
        }
    }
    
    pub fn with_deadline(mut self, deadline: u32) -> Self {
        self.deadline = deadline;
        self
    }
    
    pub fn with_profit(mut self, profit: u32) -> Self {
        self.profit = profit;
        self
    }
    
    pub fn with_arrival_time(mut self, arrival_time: u32) -> Self {
        self.arrival_time = arrival_time;
        self
    }
    
    pub fn with_priority(mut self, priority: u32) -> Self {
        self.priority = priority;
        self
    }
}

pub struct JobScheduler;

impl JobScheduler {
    pub fn new() -> Self {
        Self
    }
    
    pub fn shortest_job_first(&self, jobs: &[Job]) -> (Vec<Job>, f64) {
        if jobs.is_empty() {
            return (Vec::new(), 0.0);
        }
        
        let mut sorted_jobs = jobs.to_vec();
        sorted_jobs.sort_by_key(|job| job.processing_time);
        
        let mut current_time = 0u32;
        let mut total_waiting_time = 0u32;
        
        for job in &sorted_jobs {
            total_waiting_time += current_time;
            current_time += job.processing_time;
        }
        
        let average_waiting_time = total_waiting_time as f64 / jobs.len() as f64;
        (sorted_jobs, average_waiting_time)
    }
    
    pub fn deadline_scheduling(&self, jobs: &[Job]) -> (Vec<Job>, u32) {
        if jobs.is_empty() {
            return (Vec::new(), 0);
        }
        
        let mut sorted_jobs = jobs.to_vec();
        sorted_jobs.sort_by(|a, b| b.profit.cmp(&a.profit));
        
        let max_deadline = jobs.iter().map(|job| job.deadline).max().unwrap_or(0) as usize;
        let mut result = vec![None; max_deadline];
        let mut total_profit = 0;
        
        for job in sorted_jobs {
            let deadline_limit = std::cmp::min(job.deadline as usize, max_deadline);
            
            // Find latest available slot before deadline
            for slot in (0..deadline_limit).rev() {
                if result[slot].is_none() {
                    result[slot] = Some(job.clone());
                    total_profit += job.profit;
                    break;
                }
            }
        }
        
        let scheduled_jobs: Vec<Job> = result.into_iter().flatten().collect();
        (scheduled_jobs, total_profit)
    }
    
    pub fn earliest_deadline_first(&self, jobs: &[Job]) -> Vec<Job> {
        if jobs.is_empty() {
            return Vec::new();
        }
        
        let mut sorted_jobs = jobs.to_vec();
        sorted_jobs.sort_by_key(|job| job.deadline);
        sorted_jobs
    }
    
    pub fn priority_scheduling(&self, jobs: &[Job]) -> Vec<Job> {
        if jobs.is_empty() {
            return Vec::new();
        }
        
        let mut sorted_jobs = jobs.to_vec();
        sorted_jobs.sort_by(|a, b| b.priority.cmp(&a.priority));
        sorted_jobs
    }
    
    pub fn round_robin(&self, jobs: &[Job], time_quantum: u32) -> Vec<(usize, u32, u32)> {
        if jobs.is_empty() || time_quantum == 0 {
            return Vec::new();
        }
        
        let mut job_queue: Vec<(usize, u32)> = jobs.iter()
            .enumerate()
            .map(|(i, job)| (i, job.processing_time))
            .collect();
        
        let mut execution_order = Vec::new();
        let mut current_time = 0;
        let mut queue_index = 0;
        
        while !job_queue.is_empty() {
            let (job_index, remaining_time) = job_queue[queue_index];
            let execution_time = std::cmp::min(remaining_time, time_quantum);
            
            execution_order.push((job_index, current_time, current_time + execution_time));
            current_time += execution_time;
            
            if remaining_time > time_quantum {
                job_queue[queue_index] = (job_index, remaining_time - time_quantum);
                queue_index = (queue_index + 1) % job_queue.len();
            } else {
                job_queue.remove(queue_index);
                if !job_queue.is_empty() {
                    queue_index %= job_queue.len();
                }
            }
        }        
        execution_order
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_shortest_job_first() {
        let scheduler = JobScheduler::new();
        let jobs = vec![
            Job::new(1, 6),
            Job::new(2, 8),
            Job::new(3, 7),
            Job::new(4, 3),
        ];
        
        let (scheduled, avg_wait) = scheduler.shortest_job_first(&jobs);
        
        assert_eq!(scheduled[0].id, 4); // Shortest job first
        assert_eq!(scheduled[0].processing_time, 3);
        assert!(avg_wait > 0.0);
    }
    
    #[test]
    fn test_deadline_scheduling() {
        let scheduler = JobScheduler::new();
        let jobs = vec![
            Job::new(1, 3).with_deadline(4).with_profit(50),
            Job::new(2, 2).with_deadline(1).with_profit(10),
            Job::new(3, 1).with_deadline(2).with_profit(40),
            Job::new(4, 2).with_deadline(3).with_profit(30),
        ];
        
        let (scheduled, total_profit) = scheduler.deadline_scheduling(&jobs);
        
        assert!(total_profit > 0);
        assert!(!scheduled.is_empty());
    }
}

### 7. Coin Change (Greedy Approach)

#### Python Implementation

```python
from typing import List, Optional, Tuple

class CoinChange:
    """Greedy approach for coin change problems."""
    
    def __init__(self, denominations: List[int]):
        """
        Initialize with coin denominations.
        
        Args:
            denominations: List of coin denominations (should be sorted in descending order for greedy)
        """
        self.denominations = sorted(denominations, reverse=True)
    
    def make_change_greedy(self, amount: int) -> Optional[List[Tuple[int, int]]]:
        """
        Make change using greedy algorithm.
        
        Note: This only works optimally for canonical coin systems (like US coins).
        
        Args:
            amount: Target amount
            
        Returns:
            List of (denomination, count) tuples or None if impossible
        """
        if amount < 0:
            return None
        
        if amount == 0:
            return []
        
        result = []
        remaining = amount
        
        for denomination in self.denominations:
            if remaining >= denomination:
                count = remaining // denomination
                result.append((denomination, count))
                remaining -= denomination * count
                
                if remaining == 0:
                    break
        
        return result if remaining == 0 else None
    
    def make_change_with_limit(self, amount: int, coin_limits: dict) -> Optional[List[Tuple[int, int]]]:
        """
        Make change with limited coins of each denomination.
        
        Args:
            amount: Target amount
            coin_limits: Dictionary mapping denomination to maximum available count
            
        Returns:
            List of (denomination, count) tuples or None if impossible
        """
        if amount < 0:
            return None
        
        if amount == 0:
            return []
        
        result = []
        remaining = amount
        available_coins = coin_limits.copy()
        
        for denomination in self.denominations:
            if remaining >= denomination and available_coins.get(denomination, 0) > 0:
                max_usable = min(remaining // denomination, available_coins[denomination])
                if max_usable > 0:
                    result.append((denomination, max_usable))
                    remaining -= denomination * max_usable
                    available_coins[denomination] -= max_usable
                    
                    if remaining == 0:
                        break
        
        return result if remaining == 0 else None
    
    def minimum_coins_greedy(self, amount: int) -> int:
        """
        Find minimum number of coins needed (greedy approach).
        
        Returns:
            Minimum number of coins or -1 if impossible
        """
        change = self.make_change_greedy(amount)
        if change is None:
            return -1
        
        return sum(count for _, count in change)
    
    def is_canonical_system(self, max_amount: int = 100) -> bool:
        """
        Check if the coin system is canonical (greedy gives optimal solution).
        
        This is a heuristic check that compares greedy with dynamic programming
        for amounts up to max_amount.
        """
        def min_coins_dp(amount: int) -> int:
            dp = [float('inf')] * (amount + 1)
            dp[0] = 0
            
            for i in range(1, amount + 1):
                for coin in self.denominations:
                    if coin <= i and dp[i - coin] != float('inf'):
                        dp[i] = min(dp[i], dp[i - coin] + 1)
            
            return dp[amount] if dp[amount] != float('inf') else -1
        
        for amount in range(1, max_amount + 1):
            greedy_result = self.minimum_coins_greedy(amount)
            dp_result = min_coins_dp(amount)
            
            if greedy_result != dp_result:
                return False
        
        return True

class FractionalCoinChange:
    """Fractional coin change where coins can be broken."""
    
    def __init__(self, denominations: List[float]):
        self.denominations = sorted(denominations, reverse=True)
    
    def make_change_fractional(self, amount: float) -> List[Tuple[float, float]]:
        """
        Make change allowing fractional coins.
        
        Args:
            amount: Target amount
            
        Returns:
            List of (denomination, fraction_used) tuples
        """
        if amount <= 0:
            return []
        
        result = []
        remaining = amount
        
        for denomination in self.denominations:
            if remaining >= denomination:
                # Use whole coins
                whole_coins = int(remaining // denomination)
                if whole_coins > 0:
                    result.append((denomination, float(whole_coins)))
                    remaining -= denomination * whole_coins
            
            # Use fractional part if needed
            if remaining > 0 and denomination <= remaining + 1e-10:  # Account for floating point errors
                fraction = remaining / denomination
                result.append((denomination, fraction))
                remaining = 0
                break
        
        return result

# Example usage and testing
if __name__ == "__main__":
    # US coin system (canonical)
    us_coins = CoinChange([25, 10, 5, 1])  # quarters, dimes, nickels, pennies
    
    amount = 67
    change = us_coins.make_change_greedy(amount)
    print(f"Change for {amount} cents:")
    if change:
        for denomination, count in change:
            print(f"  {count} × {denomination}¢")
        print(f"Total coins: {sum(count for _, count in change)}")
    else:
        print("  Cannot make exact change")
    
    # Check if canonical
    print(f"US coin system is canonical: {us_coins.is_canonical_system()}")
    
    # Non-canonical system example
    non_canonical = CoinChange([4, 3, 1])
    amount = 6
    greedy_result = non_canonical.make_change_greedy(amount)
    print(f"\nGreedy change for {amount} with [4,3,1] coins:")
    if greedy_result:
        for denomination, count in greedy_result:
            print(f"  {count} × {denomination}")
        print(f"Total coins: {sum(count for _, count in greedy_result)}")
    
    print(f"Non-canonical system [4,3,1] is canonical: {non_canonical.is_canonical_system(20)}")
    
    # Fractional coin change
    fractional = FractionalCoinChange([1.0, 0.5, 0.25, 0.1, 0.05, 0.01])
    amount = 1.67
    fractional_change = fractional.make_change_fractional(amount)
    print(f"\nFractional change for ${amount}:")
    for denomination, fraction in fractional_change:
        if fraction == int(fraction):
            print(f"  {int(fraction)} × ${denomination}")
        else:
            print(f"  {fraction:.3f} × ${denomination}")
```

#### Rust Implementation

```rust
use std::collections::HashMap;

#[derive(Debug)]
pub struct CoinChange {
    denominations: Vec<u32>,
}

impl CoinChange {
    pub fn new(mut denominations: Vec<u32>) -> Self {
        denominations.sort_by(|a, b| b.cmp(a)); // Sort in descending order
        Self { denominations }
    }
    
    pub fn make_change_greedy(&self, amount: u32) -> Option<Vec<(u32, u32)>> {
        if amount == 0 {
            return Some(Vec::new());
        }
        
        let mut result = Vec::new();
        let mut remaining = amount;
        
        for &denomination in &self.denominations {
            if remaining >= denomination {
                let count = remaining / denomination;
                result.push((denomination, count));
                remaining -= denomination * count;
                
                if remaining == 0 {
                    break;
                }
            }
        }
        
        if remaining == 0 {
            Some(result)
        } else {
            None
        }
    }
    
    pub fn make_change_with_limit(&self, amount: u32, coin_limits: &HashMap<u32, u32>) -> Option<Vec<(u32, u32)>> {
        if amount == 0 {
            return Some(Vec::new());
        }
        
        let mut result = Vec::new();
        let mut remaining = amount;
        let mut available_coins = coin_limits.clone();
        
        for &denomination in &self.denominations {
            if remaining >= denomination {
                let available = available_coins.get(&denomination).copied().unwrap_or(0);
                if available > 0 {
                    let max_usable = std::cmp::min(remaining / denomination, available);
                    if max_usable > 0 {
                        result.push((denomination, max_usable));
                        remaining -= denomination * max_usable;
                        available_coins.insert(denomination, available - max_usable);
                        
                        if remaining == 0 {
                            break;
                        }
                    }
                }
            }
        }
        
        if remaining == 0 {
            Some(result)
        } else {
            None
        }
    }
    
    pub fn minimum_coins_greedy(&self, amount: u32) -> Option<u32> {
        self.make_change_greedy(amount)
            .map(|change| change.iter().map(|(_, count)| count).sum())
    }
    
    pub fn is_canonical_system(&self, max_amount: u32) -> bool {
        for amount in 1..=max_amount {
            let greedy_result = self.minimum_coins_greedy(amount);
            let dp_result = self.min_coins_dp(amount);
            
            match (greedy_result, dp_result) {
                (Some(greedy), Some(dp)) if greedy != dp => return false,
                (None, Some(_)) => return false,
                _ => continue,
            }
        }
        
        true
    }
    
    fn min_coins_dp(&self, amount: u32) -> Option<u32> {
        let mut dp = vec![u32::MAX; (amount + 1) as usize];
        dp[0] = 0;
        
        for i in 1..=amount as usize {
            for &coin in &self.denominations {
                if coin as usize <= i && dp[i - coin as usize] != u32::MAX {
                    dp[i] = std::cmp::min(dp[i], dp[i - coin as usize] + 1);
                }
            }
        }
        
        if dp[amount as usize] == u32::MAX {
            None
        } else {
            Some(dp[amount as usize])
        }
    }
}

#[derive(Debug)]
pub struct FractionalCoinChange {
    denominations: Vec<f64>,
}

impl FractionalCoinChange {
    pub fn new(mut denominations: Vec<f64>) -> Self {
        denominations.sort_by(|a, b| b.partial_cmp(a).unwrap());
        Self { denominations }
    }
    
    pub fn make_change_fractional(&self, amount: f64) -> Vec<(f64, f64)> {
        if amount <= 0.0 {
            return Vec::new();
        }
        
        let mut result = Vec::new();
        let mut remaining = amount;
        const EPSILON: f64 = 1e-10;
        
        for &denomination in &self.denominations {
            if remaining >= denomination - EPSILON {
                // Use whole coins
                let whole_coins = (remaining / denomination).floor();
                if whole_coins >= 1.0 {
                    result.push((denomination, whole_coins));
                    remaining -= denomination * whole_coins;
                }
                
                // Use fractional part if needed
                if remaining > EPSILON && denomination <= remaining + EPSILON {
                    let fraction = remaining / denomination;
                    result.push((denomination, fraction));
                    remaining = 0.0;
                    break;
                }
            }
        }
        
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_us_coins() {
        let us_coins = CoinChange::new(vec![25, 10, 5, 1]);
        
        let change = us_coins.make_change_greedy(67).unwrap();
        let total_coins: u32 = change.iter().map(|(_, count)| count).sum();
        
        assert_eq!(total_coins, 6); // 2×25 + 1×10 + 1×5 + 2×1
        assert!(us_coins.is_canonical_system(100));
    }
    
    #[test]
    fn test_non_canonical_system() {
        let non_canonical = CoinChange::new(vec![4, 3, 1]);
        
        // For amount 6: greedy gives [1×4, 2×1] = 3 coins
        // Optimal is [2×3] = 2 coins
        assert!(!non_canonical.is_canonical_system(10));
    }
    
    #[test]
    fn test_fractional_coins() {
        let fractional = FractionalCoinChange::new(vec![1.0, 0.5, 0.25, 0.1, 0.01]);
        let change = fractional.make_change_fractional(1.67);
        
        assert!(!change.is_empty());
        let total: f64 = change.iter().map(|(denom, count)| denom * count).sum();
        assert!((total - 1.67).abs() < 1e-10);
    }
}

## Optimization Techniques {#optimization}

### Performance Optimization Strategies

#### Python Optimizations

```python
import bisect
import functools
from typing import List, Tuple, Optional, Set
import heapq
from collections import deque, defaultdict

class OptimizedGreedyAlgorithms:
    """Optimized implementations of greedy algorithms."""
    
    @staticmethod
    @functools.lru_cache(maxsize=1024)
    def fibonacci_greedy_cached(n: int) -> int:
        """Cached fibonacci using greedy approach (for demonstration)."""
        if n <= 1:
            return n
        return OptimizedGreedyAlgorithms.fibonacci_greedy_cached(n-1) + \
               OptimizedGreedyAlgorithms.fibonacci_greedy_cached(n-2)
    
    @staticmethod
    def activity_selection_optimized(activities: List[Tuple[int, int]]) -> List[int]:
        """
        Optimized activity selection with early termination and binary search.
        """
        if not activities:
            return []
        
        # Pre-sort with indices
        indexed_activities = [(end, start, i) for i, (start, end) in enumerate(activities)]
        indexed_activities.sort()
        
        selected = [indexed_activities[0][2]]  # Always select first activity
        last_end_time = indexed_activities[0][0]
        
        # Use binary search for next compatible activity
        for i in range(1, len(indexed_activities)):
            end_time, start_time, index = indexed_activities[i]
            
            if start_time >= last_end_time:
                selected.append(index)
                last_end_time = end_time
                
                # Early termination if remaining activities can't improve
                if len(selected) + (len(indexed_activities) - i - 1) <= len(selected):
                    break
        
        return selected
    
    @staticmethod
    def interval_scheduling_with_priorities(
        intervals: List[Tuple[int, int, float]]
    ) -> Tuple[List[int], float]:
        """
        Interval scheduling with priorities using advanced data structures.
        """
        if not intervals:
            return [], 0.0
        
        # Sort by end time, then by priority
        indexed_intervals = [
            (end, start, priority, i) 
            for i, (start, end, priority) in enumerate(intervals)
        ]
        indexed_intervals.sort(key=lambda x: (x[0], -x[2]))
        
        # Use sweep line algorithm
        selected = []
        total_priority = 0.0
        last_end = float('-inf')
        
        for end, start, priority, index in indexed_intervals:
            if start >= last_end:
                selected.append(index)
                total_priority += priority
                last_end = end
        
        return selected, total_priority
    
    @staticmethod
    def knapsack_with_preprocessing(
        items: List[Tuple[float, float]], capacity: float
    ) -> Tuple[float, List[Tuple[int, float]]]:
        """
        Fractional knapsack with preprocessing and optimizations.
        """
        if capacity <= 0 or not items:
            return 0.0, []
        
        # Preprocess: remove items with zero or negative value
        valid_items = [
            (value, weight, i) for i, (value, weight) in enumerate(items)
            if value > 0 and weight > 0
        ]
        
        if not valid_items:
            return 0.0, []
        
        # Sort by value/weight ratio (descending)
        valid_items.sort(key=lambda x: x[0] / x[1], reverse=True)
        
        total_value = 0.0
        solution = []
        remaining_capacity = capacity
        
        for value, weight, original_index in valid_items:
            if remaining_capacity <= 0:
                break
                
            if weight <= remaining_capacity:
                # Take whole item
                total_value += value
                solution.append((original_index, 1.0))
                remaining_capacity -= weight
            else:
                # Take fraction
                fraction = remaining_capacity / weight
                total_value += value * fraction
                solution.append((original_index, fraction))
                break
        
        return total_value, solution
```

```python
class AdvancedDataStructures:
    """Advanced data structures for greedy algorithms."""
    
    class LazyPropagationSegmentTree:
        """Segment tree with lazy propagation for range updates."""
        
        def __init__(self, n: int):
            self.n = n
            self.tree = [0] * (4 * n)
            self.lazy = [0] * (4 * n)
        
        def push(self, node: int, start: int, end: int):
            """Push lazy value down."""
            if self.lazy[node] != 0:
                self.tree[node] += self.lazy[node]
                if start != end:
                    self.lazy[2 * node] += self.lazy[node]
                    self.lazy[2 * node + 1] += self.lazy[node]
                self.lazy[node] = 0
        
        def update_range(self, node: int, start: int, end: int, 
                        left: int, right: int, value: int):
            """Update range [left, right] with value."""
            self.push(node, start, end)
            
            if start > right or end < left:
                return
            
            if start >= left and end <= right:
                self.lazy[node] += value
                self.push(node, start, end)
                return
            
            mid = (start + end) // 2
            self.update_range(2 * node, start, mid, left, right, value)
            self.update_range(2 * node + 1, mid + 1, end, left, right, value)
        
        def query_range(self, node: int, start: int, end: int, 
                       left: int, right: int) -> int:
            """Query range [left, right]."""
            if start > right or end < left:
                return 0
            
            self.push(node, start, end)
            
            if start >= left and end <= right:
                return self.tree[node]
            
            mid = (start + end) // 2
            left_sum = self.query_range(2 * node, start, mid, left, right)
            right_sum = self.query_range(2 * node + 1, mid + 1, end, left, right)
            return left_sum + right_sum
```

```python
class MemoryEfficientGreedy:
    """Memory-efficient implementations for large datasets."""
    
    @staticmethod
    def streaming_activity_selection(activity_stream) -> List[int]:
        """
        Process activities in streaming fashion with minimal memory.
        """
        selected = []
        last_end_time = float('-inf')
        
        for i, (start, end) in enumerate(activity_stream):
            if start >= last_end_time:
                selected.append(i)
                last_end_time = end
        
        return selected
    
    @staticmethod
    def external_sort_merge_greedy(file_paths: List[str], output_path: str, key_func):
        """
        External sorting for greedy algorithms on large datasets.
        """
        import tempfile
        import os
        import heapq
        
        # Phase 1: Sort individual files
        sorted_files = []
        
        for file_path in file_paths:
            with open(file_path, 'r') as f:
                data = sorted((line.strip() for line in f), key=key_func)
            
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
            for item in data:
                temp_file.write(f"{item}\n")
            temp_file.close()
            sorted_files.append(temp_file.name)
        
        # Phase 2: Merge sorted files
        with open(output_path, 'w') as output:
            file_handles = [open(f, 'r') for f in sorted_files]
            heap = []
            
            # Initialize heap
            for i, fh in enumerate(file_handles):
                line = fh.readline().strip()
                if line:
                    heapq.heappush(heap, (key_func(line), i, line))
            
            # Merge
            while heap:
                _, i, line = heapq.heappop(heap)
                output.write(f"{line}\n")
                next_line = file_handles[i].readline().strip()
                if next_line:
                    heapq.heappush(heap, (key_func(next_line), i, next_line))
            
            # Close file handles
            for fh in file_handles:
                fh.close()
        
        # Clean up temporary files
        for temp_path in sorted_files:
            os.unlink(temp_path)
```