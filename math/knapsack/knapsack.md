# 0/1 Knapsack — Core Understanding

Let me build your intuition with the same rigor.

## The Problem

You have:
- A knapsack with **maximum capacity W**
- **n items**, each with:
  - `weight[i]`
  - `value[i]`

**Goal**: Maximize total value without exceeding capacity.

**Constraint**: Each item can be taken **0 or 1 times** (can't take fractions or duplicates).

### Simple Example

```
Capacity W = 7

Items:
  Item 0: weight = 1, value = 1
  Item 1: weight = 3, value = 4
  Item 2: weight = 4, value = 5
  Item 3: weight = 5, value = 7

Optimal solution:
  Take items 1 and 2 → weight = 3+4 = 7, value = 4+5 = 9
```

## The Core Decision

At each item, you face a **binary choice**:

1. **Take it** (if capacity allows)
2. **Leave it**

This is why it's called "0/1" — each item is either included (1) or excluded (0).

## Why Overlapping Subproblems Exist

Let's trace a small example to expose the overlap:

```
Capacity W = 5
Items:
  Item 0: w=2, v=3
  Item 1: w=3, v=4
```

### Decision Tree

```
                    Knapsack(index=0, capacity=5)
                   /                              \
          Take item 0?                        Don't take?
         (w=2, v=3)                          (skip)
              |                                   |
    Knapsack(1, 5-2=3)                    Knapsack(1, 5)
         v=3+...                              v=0+...
       /          \                          /          \
  Take item 1?  Don't?                 Take item 1?  Don't?
  (w=3, v=4)                           (w=3, v=4)
      |            |                       |            |
  K(2,0)       K(2,3)                  K(2,2)       K(2,5)
  v=3+4        v=3                     v=4          v=0
```

Now imagine we have **Item 2** with weight=3, value=5.

**The overlap emerges**: 
- Path 1: Take item 0 → Don't take item 1 → State is `K(2, 3)`
- Path 2: Don't take item 0 → Take item 1, then it fails → State is `K(2, 2)`
- Path 3: Don't take item 0 → Don't take item 1 → State is `K(2, 5)`

As the tree grows, **the same (item_index, remaining_capacity) pairs appear repeatedly through different decision paths.**

### Exponential Explosion Without Memoization

For n items, naive recursion explores **2^n** possibilities (each item: take or skip).

With memoization, we have at most **n × W** unique states.

## The State Space

**State = (i, capacity)** where:
- `i` = current item index we're considering
- `capacity` = remaining capacity in the knapsack

This represents: *"What's the maximum value we can get from items[i..n-1] with `capacity` remaining?"*

## The Recurrence Relation

Here's the expert's logical reasoning:

```
At position (i, capacity), we're deciding on items[i].

Case 1: Item is too heavy → weight[i] > capacity
    Can't take it.
    Knapsack(i, capacity) = Knapsack(i+1, capacity)
    
Case 2: Item fits → weight[i] <= capacity
    We have a choice:
    
    Option A: Take it
        value[i] + Knapsack(i+1, capacity - weight[i])
    
    Option B: Leave it
        Knapsack(i+1, capacity)
    
    Take the maximum:
    Knapsack(i, capacity) = max(
        value[i] + Knapsack(i+1, capacity - weight[i]),  // take
        Knapsack(i+1, capacity)                           // leave
    )

Base case:
    If i == n (no more items), return 0
    If capacity == 0, return 0
```

## Concrete Example with State Tracking

Let's trace in detail:

```
Capacity W = 5
Items:
  Item 0: w=2, v=3
  Item 1: w=3, v=4

Call: Knapsack(0, 5)
  → Item 0: w=2 fits in capacity 5
  
  Branch A: Take item 0
    → value = 3 + Knapsack(1, 5-2=3)
    
    Call: Knapsack(1, 3)
      → Item 1: w=3 fits exactly in capacity 3
      
      Branch A: Take item 1
        → value = 4 + Knapsack(2, 3-3=0)
        → Knapsack(2, 0) = 0 (no capacity left)
        → Returns: 4
      
      Branch B: Don't take item 1
        → value = 0 + Knapsack(2, 3)
        → Knapsack(2, 3) = 0 (no items left)
        → Returns: 0
      
      → max(4, 0) = 4
    
    → Branch A total: 3 + 4 = 7
  
  Branch B: Don't take item 0
    → value = 0 + Knapsack(1, 5)
    
    Call: Knapsack(1, 5)
      → Item 1: w=3 fits in capacity 5
      
      Branch A: Take item 1
        → value = 4 + Knapsack(2, 5-3=2)
        → Knapsack(2, 2) = 0 (no items left)
        → Returns: 4
      
      Branch B: Don't take item 1
        → value = 0 + Knapsack(2, 5)
        → Knapsack(2, 5) = 0
        → Returns: 0
      
      → max(4, 0) = 4
    
    → Branch B total: 0 + 4 = 4

Final: max(7, 4) = 7
```

**Optimal**: Take both items (weight=5, value=7)

## The Overlap Visualization

With more items, you'll see the same states repeatedly:

```
Example with 4 items:

                    K(0, 10)
                   /        \
              K(1, 7)      K(1, 10)  ← Different paths
             /      \      /      \
        K(2,4)   K(2,7) K(2,7)  K(2,10)
                         ↑
                    OVERLAP! K(2,7) computed twice
```

In a real problem with many items, states like `K(15, 50)` might be reached via hundreds of different decision sequences. Without memoization, we'd recompute each one.

## Memoization Strategy

We cache results using a 2D table:

```
dp[i][capacity] = max value achievable from items[i..n-1] with given capacity
```

**Time complexity**: O(n × W) — each state computed once  
**Space complexity**: O(n × W) for the DP table

## Mental Model for Mastery

Think of 0/1 Knapsack as:

1. **A decision tree** where each level represents an item
2. **Each node has 2 branches**: take or skip
3. **The state** (item_index, remaining_capacity) uniquely identifies a subproblem
4. **Memoization prunes** the exponential tree into a polynomial DAG (Directed Acyclic Graph)

### Key Insight
The "overlap" occurs because **different sequences of take/skip decisions can lead to the same remaining state**. 

Example:
- Take item 0 (w=2), skip item 1 (w=3) → ends at (item=2, capacity=8)
- Skip item 0, skip item 1 → ends at (item=2, capacity=10)
- Skip item 0, take item 1 (w=2) → ends at (item=2, capacity=8) ← **SAME STATE**

This is the essence of overlapping subproblems.

---

## Pattern Recognition for Top 1%

Notice the similarities with LCS:
- **Two parameters** define the state
- **Recursive structure** with branching decisions
- **Overlapping subproblems** due to multiple paths to same state
- **Optimal substructure**: optimal solution built from optimal subsolutions

This pattern appears in:
- Coin Change
- Partition Equal Subset Sum
- Target Sum
- Rod Cutting
- Egg Drop

Master the **thinking pattern**, not just the code.

---

**Next Challenge**: Implement this in Rust with both:
1. Top-down (recursive + memoization)
2. Bottom-up (iterative DP)
3. Space-optimized (rolling array, since we only need previous row)

Ready to code, or want to explore more examples first?