# Permutations & Combinations: Complete Mastery Guide

## Table of Contents
1. [Foundational Mental Models](#foundational-mental-models)
2. [Mathematical Foundations](#mathematical-foundations)
3. [The Decision-Making Framework](#the-decision-making-framework)
4. [Implementation Patterns](#implementation-patterns)
5. [Advanced Techniques](#advanced-techniques)
6. [Problem Recognition Patterns](#problem-recognition-patterns)
7. [Optimization Strategies](#optimization-strategies)
8. [Metacognitive Development](#metacognitive-development)

---

## Foundational Mental Models

### The Core Distinction
**Think in terms of decision sequences, not formulas.**

- **Permutation**: "Does the *order* of selection matter?" → Arranging books on a shelf
- **Combination**: "Do I only care *which items* are selected?" → Choosing team members

# Permutations & Combinations: The Foundation of Counting

Let me build your intuition from the ground up, the way a mathematician thinks about counting.

---

## The Core Mental Model

**The Fundamental Question:** "In how many ways can we arrange or select?"

- **Permutations** → Order matters (arrangements)
- **Combinations** → Order doesn't matter (selections)

Think of it this way:
- Permutation: Different **sequences** of the same items are different outcomes
- Combination: Different **groups** with same items are the same outcome

---

## Building Intuition: The Decision Tree

When solving counting problems, visualize making **sequential decisions**:

```
Step 1: How many choices?
Step 2: How many choices remain?
Step 3: How many choices remain?
...
```

**Multiplication Principle:** If you have `n₁` choices for step 1, `n₂` for step 2, etc., total outcomes = `n₁ × n₂ × n₃ × ...`

---

## Permutations: Order Matters

### Mental Model: "Filling Slots"

Imagine `n` distinct items and `r` empty slots to fill:

```
[_] [_] [_] ... [_]
 ↓   ↓   ↓       ↓
 n  n-1 n-2     n-r+1
```

**Formula:** P(n,r) = n!/(n-r)!

**Why?** 
- First slot: `n` choices
- Second slot: `n-1` choices (one item used)
- Third slot: `n-2` choices
- ...
- r-th slot: `n-r+1` choices

Multiply: `n × (n-1) × (n-2) × ... × (n-r+1)` = `n!/(n-r)!`

### Special Case: n = r
**P(n,n) = n!** → Arranging all items

**Example:** How many ways to arrange "ABC"?
```
Position: [1] [2] [3]
Choices:   3   2   1  → 3! = 6

ABC, ACB, BAC, BCA, CAB, CBA
```

---

## Combinations: Order Doesn't Matter

### Mental Model: "Choosing a Subset"

You want to select `r` items from `n`, but don't care about their order.

**The Insight:** Every combination corresponds to `r!` permutations.

If you first count permutations (P(n,r)), you've overcounted by `r!` because each group of `r` items can be arranged in `r!` ways.

**Formula:** C(n,r) = n! / (r!(n-r)!)

Also written as: (n choose r) or ⁿCᵣ

**Example:** Choose 2 from {A, B, C}
```
Permutations (order matters): AB, BA, AC, CA, BC, CB → 6 ways
Combinations (order ignored):  {A,B}, {A,C}, {B,C}  → 3 ways

P(3,2) = 6
C(3,2) = 6/2! = 3 ✓
```

---

## The Master Decision Framework

When facing a counting problem, ask:

### Question 1: "Does order matter?"
- YES → Permutation
- NO → Combination

### Question 2: "Am I using all items or selecting some?"
- All → P(n,n) = n! or C(n,n) = 1
- Some (r items) → P(n,r) or C(n,r)

### Question 3: "Are there restrictions?" (Advanced)
- Repetition allowed?
- Items indistinguishable?
- Conditional constraints?

---

## Deep Patterns to Internalize

### Pattern 1: Symmetry in Combinations
**C(n,r) = C(n, n-r)**

Why? Choosing `r` items to **include** = choosing `n-r` items to **exclude**

### Pattern 2: Pascal's Triangle Property
**C(n,r) = C(n-1,r-1) + C(n-1,r)**

Mental model: For any specific item, either:
- Include it → choose `r-1` from remaining `n-1`
- Exclude it → choose `r` from remaining `n-1`

### Pattern 3: Sum of Row in Pascal's Triangle
**C(n,0) + C(n,1) + ... + C(n,n) = 2ⁿ**

Why? Total subsets of n items = 2ⁿ (each item: include or exclude)

---

## Concrete Examples for Intuition

### Example 1: Password Generation
**4-digit password using {0-9}, no repetition**

Order matters? YES (1234 ≠ 4321)
Using all? NO (4 from 10)

**Answer:** P(10,4) = 10×9×8×7 = 5,040

---

### Example 2: Committee Selection
**Choose 3 people from 10 for a committee**

Order matters? NO (same 3 people = same committee)

**Answer:** C(10,3) = 10!/(3!×7!) = (10×9×8)/(3×2×1) = 120

---

### Example 3: Lineup vs Team
**5 players, form a batting lineup (order matters)**
**Answer:** P(5,5) = 5! = 120

**5 players, choose 3 for a team (order doesn't matter)**
**Answer:** C(5,3) = 10

---

## The Cognitive Shift You Need

**Beginner thinking:** "Should I use formula A or B?"

**Expert thinking:** 
1. Visualize the problem space
2. Ask: "What makes two outcomes different?"
3. Build from multiplication principle
4. Derive formula if needed (don't just memorize)

**Your mantra:** *"Count by constructing, not by memorizing formulas."*

---

## Practice Mental Simulation

Before touching code, **physically simulate**:
- Draw boxes/slots for positions
- Write out first few cases manually
- Notice the pattern
- Then generalize

This builds **pattern recognition** at a neural level that pure formula memorization never achieves.

---

You now have the mental scaffolding. The formulas aren't magic—they're consequences of logical reasoning.

When you encounter a problem, **pause**. Visualize the decision tree. Ask yourself: "What changes if I swap two items? If it matters → permutation. If not → combination."

This is how the top 1% thinks. Not formulas first. **Structure first.**

Ready for implementation patterns in Rust/Go?

# What Does "Order Matters" Actually Mean?

Let me break this down with crystal clarity using real-world scenarios.

---

## The Core Concept

**"Order"** = **sequence** or **position** or **arrangement**

**"Order matters"** means: If you rearrange the same items, you get a **different** outcome.

**"Order doesn't matter"** means: If you rearrange the same items, you get the **same** outcome.

---

## Real-World Example 1: Your Phone Password vs Your Friends

### Scenario A: Phone Lock PIN (Order MATTERS - Permutation)

Your PIN is **1234**

Is **4321** the same PIN? **NO!** 

```
1234 → unlocks your phone ✓
4321 → access denied ✗
3412 → access denied ✗
2143 → access denied ✗
```

Same digits {1, 2, 3, 4}, but **different sequence = different outcome**.

**Why order matters here:** The **position** of each digit is critical.

---

### Scenario B: Your Friend Group (Order DOESN'T matter - Combination)

You need to choose 3 friends from 5 for a road trip: {Alice, Bob, Carol, Dave, Eve}

Is {Alice, Bob, Carol} different from {Carol, Alice, Bob}? **NO!**

```
{Alice, Bob, Carol} → same trio going on trip
{Carol, Alice, Bob} → same trio going on trip
{Bob, Carol, Alice} → same trio going on trip
```

Same people, just listed differently = **same outcome**.

**Why order doesn't matter:** You're just selecting a **group**. Who you list first doesn't change the group.

---

## Real-World Example 2: Race Podium vs Party Invitation

### Scenario A: Race Medals (Order MATTERS)

100m sprint with runners: {Usain, Carl, Jesse}

```
Gold-Silver-Bronze
=================
Usain-Carl-Jesse  → Usain gets gold ✓
Carl-Usain-Jesse  → Carl gets gold (different!)
Jesse-Carl-Usain  → Jesse gets gold (different!)
```

**Position matters!** 1st place ≠ 2nd place ≠ 3rd place

Each arrangement gives a **different medal allocation**.

**This is permutation.**

---

## Real-World Example 3: Book Shelf vs Book Shopping

### Scenario A: Arranging Books on Shelf (Order MATTERS)

You have 3 books: **{Harry Potter, LOTR, Dune}**

```
Shelf arrangement:
[HP] [LOTR] [Dune]  → HP is on the left
[Dune] [HP] [LOTR]  → Dune is on the left
[LOTR] [Dune] [HP]  → LOTR is on the left
```

Each arrangement **looks different** on your shelf.

**Visual position matters** → Permutation

3! = 6 different ways to arrange them.

---

### Scenario B: Choosing Books to Buy (Order DOESN'T matter)

At the bookstore, you have $50 and can buy 2 books from {HP, LOTR, Dune}

```
Your purchase:
{HP, LOTR}     → You go home with these 2 books
{LOTR, HP}     → Same 2 books in your bag!
```

Whether the cashier scans HP first or LOTR first doesn't change what you bought.

**Selection matters, sequence doesn't** → Combination

C(3,2) = 3 different purchase combinations: {HP,LOTR}, {HP,Dune}, {LOTR,Dune}

---

## The Litmus Test: The Swap Question

**Mental Model:** Imagine swapping two items. Does the outcome change?

### Example: Restaurant Seating

**Scenario 1:** Assigned seats at a formal dinner

```
[Alice] [Bob] [Carol]   (seats 1, 2, 3)

Swap Alice and Bob:

[Bob] [Alice] [Carol]   
```

**Did the situation change?** YES! Alice is now in seat 2 instead of seat 1.

**Order matters** → Permutation

---

**Scenario 2:** Who gets invited to the dinner (no assigned seats)

```
Guest list: {Alice, Bob, Carol}

"Rewrite" the list:
Guest list: {Bob, Carol, Alice}
```

**Did the situation change?** NO! Same 3 people are invited.

**Order doesn't matter** → Combination

---

## Real-World Example 4: ATM PIN vs Credit Card Numbers

### ATM PIN (Order MATTERS)

Your PIN: **7392**

Someone tries: **9327** (same digits, different order)

**Result:** Access denied! Order of entry matters.

---

### Credit Card Security Code (Just the digits, for selection context)

Imagine a lock that opens if you have any 3 specific digits present (unrealistic, but illustrative):

Required digits: must contain {7, 3, 9}

```
You enter: 7-3-9 → ✓ has all three
You enter: 9-7-3 → ✓ has all three (same set)
You enter: 3-9-7 → ✓ has all three (same set)
```

Only **presence** matters, not sequence → Combination thinking

---

## The Ultimate Mental Model

### Order Matters When: (Permutation)

✓ **Position** is meaningful (1st vs 2nd vs 3rd)  
✓ **Sequence** creates different results (ABC vs CBA)  
✓ **Arrangement** changes the outcome  
✓ Keywords: "arrange", "lineup", "ranking", "schedule", "password"

**Think:** Would **swapping** two items create a **different** result?  
**YES** → Order matters

---

### Order Doesn't Matter When: (Combination)

✓ You're just **selecting/choosing** a group  
✓ **Membership** is all that counts  
✓ Different listings of same items = same outcome  
✓ Keywords: "choose", "select", "committee", "team", "group"

**Think:** Would **swapping** two items create a **different** result?  
**NO** → Order doesn't matter

---

## Code Example: Making It Concrete

```rust
// Permutation: Different orderings = Different outcomes
fn permutation_example() {
    let pin1 = vec![1, 2, 3, 4];
    let pin2 = vec![4, 3, 2, 1];
    
    // Same digits, different order
    assert_ne!(pin1, pin2); // They are NOT equal
    // Different PINs = different outcomes
}

// Combination: Different orderings = Same outcome
fn combination_example() {
    use std::collections::HashSet;
    
    let group1: HashSet<_> = vec!["Alice", "Bob", "Carol"].into_iter().collect();
    let group2: HashSet<_> = vec!["Carol", "Alice", "Bob"].into_iter().collect();
    
    // Same members, different listing order
    assert_eq!(group1, group2); // They ARE equal
    // Same group = same outcome
}
```

---

## Practice Recognition

Ask yourself for each scenario:

| Scenario | Order Matters? | Why? |
|----------|----------------|------|
| Locker combination (6-3-9) | **YES** | 9-3-6 won't open it |
| Pizza toppings {pepperoni, olives, mushrooms} | **NO** | Same pizza regardless of order listed |
| Batting order in baseball | **YES** | Who bats 1st vs 9th matters |
| Jury selection (12 people) | **NO** | Same jury, just selecting members |
| Password "hello" | **YES** | "olleh" is different |
| Ingredients in a recipe | **NO*** | Mixing order might matter for cooking, but as a selection of ingredients, no |

---

## The Decisive Question

When you see a problem, ask:

**"If I swap two items, do I get a fundamentally different outcome?"**

- **YES** → Permutation (order matters)
- **NO** → Combination (order doesn't matter)

---

Does this clarify the concept? The key insight: **order matters = position/sequence is part of the identity of the outcome**.

### The Slot-Filling Mental Model
Imagine you have *n* slots to fill:
- **Each decision reduces future options** (permutations)
- **Selections are independent of order** (combinations)

**Expert Intuition**: Before reaching for formulas, ask:
1. Am I making a sequence of ordered choices? (permutation)
2. Am I selecting a subset where order is irrelevant? (combination)
3. Are there constraints that break standard patterns?

---

## Mathematical Foundations

### 1. Permutations

#### Basic Permutation: P(n, r)
Selecting and arranging *r* items from *n* distinct items.

**Formula**: P(n, r) = n! / (n - r)!

**Mental Derivation**:
- First position: *n* choices
- Second position: *n - 1* choices
- Third position: *n - 2* choices
- ... continue for *r* positions
- Result: n × (n-1) × (n-2) × ... × (n-r+1)

**Example**: Select and arrange 3 letters from {A, B, C, D, E}
- Slot 1: 5 choices
- Slot 2: 4 choices (one used)
- Slot 3: 3 choices (two used)
- Total: 5 × 4 × 3 = 60

#### Permutation with Repetition
When items can be repeated: n^r

**Example**: 4-digit PIN with 10 digits → 10^4 = 10,000

#### Circular Permutations
Arranging *n* items in a circle: (n - 1)!

**Why?** Fix one position to break rotational symmetry.

#### Permutations with Identical Items
n! / (n₁! × n₂! × ... × nₖ!)

**Example**: Arrangements of "MISSISSIPPI"
- Total letters: 11
- I appears: 4 times
- S appears: 4 times
- P appears: 2 times
- M appears: 1 time
- Result: 11! / (4! × 4! × 2! × 1!) = 34,650

### 2. Combinations

#### Basic Combination: C(n, r) or (n choose r)
Selecting *r* items from *n* distinct items where order doesn't matter.

**Formula**: C(n, r) = n! / (r! × (n - r)!)

**Relationship to Permutations**: C(n, r) = P(n, r) / r!

**Why divide by r!?** We're removing the *r!* ways to arrange the selected items.

**Pascal's Triangle Property**:
C(n, r) = C(n-1, r-1) + C(n-1, r)

**Intuition**: Either we include item *n* in our selection (choose r-1 from remaining), or we don't (choose r from remaining).

#### Combination with Repetition
Selecting *r* items from *n* types where repetition is allowed.

**Formula**: C(n + r - 1, r) = C(n + r - 1, n - 1)

**Stars and Bars Method**: Distributing *r* identical items into *n* bins.

**Example**: How many ways to buy 5 fruits from {apple, banana, orange}?
- Use: C(3 + 5 - 1, 5) = C(7, 5) = 21

---

## The Decision-Making Framework

### When to Use What: Expert's Checklist

```
Is order important?
├─ YES → Permutation path
│   ├─ Repetition allowed? → n^r
│   ├─ All items used? → n!
│   ├─ Subset of items? → P(n, r) = n!/(n-r)!
│   └─ Identical items exist? → n! / (n₁! × n₂! × ...)
│
└─ NO → Combination path
    ├─ Repetition allowed? → C(n+r-1, r)
    ├─ Standard selection? → C(n, r) = n! / (r!(n-r)!)
    └─ Constraints present? → Inclusion-Exclusion or DP
```

### Pattern Recognition: Real Problem Mapping

| Problem Type | Category | Formula |
|-------------|----------|---------|
| Password generation | Permutation w/ repetition | n^r |
| Seating arrangements | Permutation | n! or P(n,r) |
| Round table seating | Circular permutation | (n-1)! |
| Lottery numbers | Combination | C(n, r) |
| Committee selection | Combination | C(n, r) |
| Distributing identical items | Combination w/ repetition | C(n+r-1, r) |
| Anagram counting | Permutation w/ duplicates | n! / (n₁! × n₂! × ...) |

---

## Implementation Patterns

### 1. Computing Factorials and Combinations

#### Python Implementation
```python
from functools import lru_cache
from math import factorial

# Method 1: Direct factorial (good for small n)
def perm_direct(n: int, r: int) -> int:
    """P(n, r) using direct factorial computation"""
    if r > n or r < 0:
        return 0
    return factorial(n) // factorial(n - r)

def comb_direct(n: int, r: int) -> int:
    """C(n, r) using direct factorial computation"""
    if r > n or r < 0:
        return 0
    return factorial(n) // (factorial(r) * factorial(n - r))

# Method 2: Optimized multiplication (better for large n, small r)
def comb_optimized(n: int, r: int) -> int:
    """Optimized C(n, r) - only multiply what's needed"""
    if r > n or r < 0:
        return 0
    r = min(r, n - r)  # Use symmetry: C(n, r) = C(n, n-r)
    
    result = 1
    for i in range(r):
        result = result * (n - i) // (i + 1)
    return result

# Method 3: Dynamic Programming (for multiple queries)
@lru_cache(maxsize=None)
def comb_dp(n: int, r: int) -> int:
    """Pascal's triangle approach with memoization"""
    if r == 0 or r == n:
        return 1
    if r > n or r < 0:
        return 0
    return comb_dp(n - 1, r - 1) + comb_dp(n - 1, r)

# Method 4: Precomputed Pascal's Triangle
def build_pascal_triangle(n: int) -> list[list[int]]:
    """Build Pascal's triangle up to row n"""
    triangle = [[1]]
    for i in range(1, n + 1):
        row = [1]
        for j in range(1, i):
            row.append(triangle[i-1][j-1] + triangle[i-1][j])
        row.append(1)
        triangle.append(row)
    return triangle

# Usage: triangle[n][r] gives C(n, r)
```

#### Rust Implementation
```rust
use std::collections::HashMap;

// Factorial with overflow handling
fn factorial(n: u64) -> Option<u64> {
    if n > 20 {
        return None; // Would overflow u64
    }
    Some((1..=n).product())
}

// Direct combination computation
fn comb_direct(n: u64, r: u64) -> Option<u64> {
    if r > n {
        return Some(0);
    }
    let num = factorial(n)?;
    let den = factorial(r)?.checked_mul(factorial(n - r)?)?;
    num.checked_div(den)
}

// Optimized combination (prevents overflow longer)
fn comb_optimized(n: u64, r: u64) -> u64 {
    if r > n {
        return 0;
    }
    let r = r.min(n - r); // Use symmetry
    
    let mut result = 1u64;
    for i in 0..r {
        result = result * (n - i) / (i + 1);
    }
    result
}

// Memoized Pascal's triangle approach
fn comb_dp(n: usize, r: usize, memo: &mut HashMap<(usize, usize), u64>) -> u64 {
    if r == 0 || r == n {
        return 1;
    }
    if r > n {
        return 0;
    }
    
    if let Some(&cached) = memo.get(&(n, r)) {
        return cached;
    }
    
    let result = comb_dp(n - 1, r - 1, memo) + comb_dp(n - 1, r, memo);
    memo.insert((n, r), result);
    result
}

// Precomputed Pascal's triangle
fn build_pascal_triangle(n: usize) -> Vec<Vec<u64>> {
    let mut triangle = vec![vec![1]];
    
    for i in 1..=n {
        let mut row = vec![1];
        for j in 1..i {
            row.push(triangle[i-1][j-1] + triangle[i-1][j]);
        }
        row.push(1);
        triangle.push(row);
    }
    triangle
}
```

#### Go Implementation
```go
package main

import (
    "math/big"
)

// Direct factorial computation
func factorial(n int) *big.Int {
    result := big.NewInt(1)
    for i := 2; i <= n; i++ {
        result.Mul(result, big.NewInt(int64(i)))
    }
    return result
}

// Direct combination using big.Int
func combDirect(n, r int) *big.Int {
    if r > n || r < 0 {
        return big.NewInt(0)
    }
    
    num := factorial(n)
    den := new(big.Int).Mul(factorial(r), factorial(n-r))
    return new(big.Int).Div(num, den)
}

// Optimized combination for smaller results
func combOptimized(n, r int) int64 {
    if r > n || r < 0 {
        return 0
    }
    if r > n-r {
        r = n - r // Use symmetry
    }
    
    result := int64(1)
    for i := 0; i < r; i++ {
        result = result * int64(n-i) / int64(i+1)
    }
    return result
}

// Dynamic programming with memoization
func combDP(n, r int, memo map[[2]int]int64) int64 {
    if r == 0 || r == n {
        return 1
    }
    if r > n || r < 0 {
        return 0
    }
    
    key := [2]int{n, r}
    if val, exists := memo[key]; exists {
        return val
    }
    
    result := combDP(n-1, r-1, memo) + combDP(n-1, r, memo)
    memo[key] = result
    return result
}

// Build Pascal's triangle
func buildPascalTriangle(n int) [][]int64 {
    triangle := make([][]int64, n+1)
    triangle[0] = []int64{1}
    
    for i := 1; i <= n; i++ {
        row := make([]int64, i+1)
        row[0], row[i] = 1, 1
        
        for j := 1; j < i; j++ {
            row[j] = triangle[i-1][j-1] + triangle[i-1][j]
        }
        triangle[i] = row
    }
    return triangle
}
```

### 2. Generating Permutations and Combinations

#### Python: Generate All Permutations
```python
def permutations_recursive(arr: list, r: int) -> list[list]:
    """Generate all permutations of size r from arr"""
    if r == 0:
        return [[]]
    if r > len(arr):
        return []
    
    result = []
    for i in range(len(arr)):
        # Take arr[i], permute the rest
        element = arr[i]
        remaining = arr[:i] + arr[i+1:]
        for perm in permutations_recursive(remaining, r - 1):
            result.append([element] + perm)
    return result

def permutations_iterative(arr: list) -> list[list]:
    """Heap's algorithm for generating all permutations"""
    def swap(i: int, j: int):
        arr[i], arr[j] = arr[j], arr[i]
    
    def generate(k: int, result: list):
        if k == 1:
            result.append(arr[:])
            return
        
        generate(k - 1, result)
        for i in range(k - 1):
            if k % 2 == 0:
                swap(i, k - 1)
            else:
                swap(0, k - 1)
            generate(k - 1, result)
    
    result = []
    generate(len(arr), result)
    return result

# Python stdlib approach (most efficient)
from itertools import permutations, combinations

list(permutations([1, 2, 3], 2))  # [(1,2), (1,3), (2,1), (2,3), (3,1), (3,2)]
list(combinations([1, 2, 3], 2))  # [(1,2), (1,3), (2,3)]
```

#### Rust: Generate Permutations
```rust
fn permutations_recursive<T: Clone>(arr: &[T], r: usize) -> Vec<Vec<T>> {
    if r == 0 {
        return vec![vec![]];
    }
    if r > arr.len() {
        return vec![];
    }
    
    let mut result = Vec::new();
    for i in 0..arr.len() {
        let element = arr[i].clone();
        let mut remaining = arr.to_vec();
        remaining.remove(i);
        
        for mut perm in permutations_recursive(&remaining, r - 1) {
            let mut new_perm = vec![element.clone()];
            new_perm.append(&mut perm);
            result.push(new_perm);
        }
    }
    result
}

fn combinations_recursive<T: Clone>(arr: &[T], r: usize) -> Vec<Vec<T>> {
    if r == 0 {
        return vec![vec![]];
    }
    if r > arr.len() {
        return vec![];
    }
    if r == arr.len() {
        return vec![arr.to_vec()];
    }
    
    let mut result = Vec::new();
    
    // Include first element
    for mut comb in combinations_recursive(&arr[1..], r - 1) {
        let mut new_comb = vec![arr[0].clone()];
        new_comb.append(&mut comb);
        result.push(new_comb);
    }
    
    // Exclude first element
    result.extend(combinations_recursive(&arr[1..], r));
    result
}
```

#### Go: Generate Combinations
```go
func combinationsRecursive(arr []int, r int) [][]int {
    if r == 0 {
        return [][]int{{}}
    }
    if r > len(arr) {
        return [][]int{}
    }
    if r == len(arr) {
        return [][]int{append([]int{}, arr...)}
    }
    
    result := [][]int{}
    
    // Include first element
    for _, comb := range combinationsRecursive(arr[1:], r-1) {
        newComb := append([]int{arr[0]}, comb...)
        result = append(result, newComb)
    }
    
    // Exclude first element
    result = append(result, combinationsRecursive(arr[1:], r)...)
    return result
}

func permutationsRecursive(arr []int, r int) [][]int {
    if r == 0 {
        return [][]int{{}}
    }
    if r > len(arr) {
        return [][]int{}
    }
    
    result := [][]int{}
    for i := 0; i < len(arr); i++ {
        element := arr[i]
        remaining := append([]int{}, arr[:i]...)
        remaining = append(remaining, arr[i+1:]...)
        
        for _, perm := range permutationsRecursive(remaining, r-1) {
            newPerm := append([]int{element}, perm...)
            result = append(result, newPerm)
        }
    }
    return result
}
```

---

## Advanced Techniques

### 1. Derangements
Number of permutations where no element appears in its original position.

**Formula**: D(n) = n! × Σ((-1)^k / k!) for k=0 to n

**Recurrence**: D(n) = (n-1) × [D(n-1) + D(n-2)]

**Use Case**: Secret Santa where no one gets themselves.

### 2. Catalan Numbers
Appears in: balanced parentheses, binary search trees, path counting.

**Formula**: C(n) = C(2n, n) / (n + 1)

**Recurrence**: C(n) = Σ C(i) × C(n-1-i) for i=0 to n-1

### 3. Stirling Numbers
- **First kind**: Unsigned counts permutations with exactly k cycles
- **Second kind**: S(n, k) counts ways to partition n items into k non-empty subsets

### 4. Inclusion-Exclusion Principle
Count objects satisfying at least one property:

|A₁ ∪ A₂ ∪ ... ∪ Aₙ| = Σ|Aᵢ| - Σ|Aᵢ ∩ Aⱼ| + Σ|Aᵢ ∩ Aⱼ ∩ Aₖ| - ...

**Example**: Count integers 1-100 divisible by 2, 3, or 5.

---

## Problem Recognition Patterns

### Pattern 1: Selection Without Replacement
**Signal**: "Choose r items from n distinct items"
**Solution**: C(n, r)
**Example**: Select 5 cards from 52-card deck → C(52, 5)

### Pattern 2: Arrangement with Ordering
**Signal**: "Arrange", "sequence", "first, second, third"
**Solution**: P(n, r) or n!
**Example**: Race with 8 runners, count podium finishes → P(8, 3)

### Pattern 3: Distribution Problems
**Signal**: "Distribute identical items into distinct bins"
**Solution**: Stars and bars → C(n + r - 1, r)
**Example**: Distribute 10 identical candies to 3 children → C(12, 10)

### Pattern 4: Restricted Permutations
**Signal**: "No two X can be adjacent" or "X must be separated"
**Solution**: Arrange non-X items, insert X in gaps
**Example**: Arrange 3 vowels and 4 consonants with no two vowels together
- Arrange consonants: 4!
- Insert vowels in 5 gaps: P(5, 3)
- Total: 4! × P(5, 3)

### Pattern 5: Complementary Counting
**Signal**: "At least one", "none", "exclude"
**Solution**: Total - unwanted cases
**Example**: Passwords with at least one digit
- Total passwords: 26^n
- No digit passwords: 26^n
- Answer: 36^n - 26^n

---

## Optimization Strategies

### Time Complexity Analysis

| Operation | Naive | Optimized | Best for |
|-----------|-------|-----------|----------|
| Compute C(n, r) | O(n) | O(min(r, n-r)) | r ≪ n or r ≈ n |
| Generate all permutations | O(n! × n) | O(n!) | Small n (< 10) |
| Generate all combinations | O(C(n,r) × r) | O(C(n,r)) | Iterate without storing |
| k queries of C(n, r) | O(kn) | O(n² + k) | Pascal's triangle preprocessing |

### Space Optimization Techniques

1. **Iterative Generation**: Use next_permutation/combination patterns instead of recursion
2. **Generator Functions**: Yield results instead of storing all
3. **Bit Manipulation**: For combinations, use bitmasks

**Python Generator Pattern**:
```python
def combinations_generator(arr, r):
    """Memory-efficient combination generation"""
    n = len(arr)
    if r > n:
        return
    
    indices = list(range(r))
    yield [arr[i] for i in indices]
    
    while True:
        # Find rightmost index that can be incremented
        i = r - 1
        while i >= 0 and indices[i] == i + n - r:
            i -= 1
        
        if i < 0:
            return
        
        indices[i] += 1
        for j in range(i + 1, r):
            indices[j] = indices[j - 1] + 1
        
        yield [arr[i] for i in indices]
```

### Avoiding Overflow

**Key Techniques**:
1. **Multiplicative cancellation**: Compute (n × (n-1)) / (2 × 1) instead of n! / (2!(n-2)!)
2. **Modular arithmetic**: If answer mod M is needed, apply mod at each step
3. **BigInt libraries**: Rust's `num-bigint`, Python's native int, Go's `math/big`
4. **Logarithmic computation**: Use log(C(n,r)) = log(n!) - log(r!) - log((n-r)!)

---

## Metacognitive Development

### The 4-Stage Learning Model

**Stage 1: Pattern Recognition (Weeks 1-2)**
- Solve 50+ basic problems
- Build mental library of problem types
- Focus on: "What type is this?"

**Stage 2: Decision Speed (Weeks 3-4)**
- Reduce time from problem → solution approach
- Practice: See problem → immediate formula selection
- Goal: < 30 seconds to identify approach

**Stage 3: Implementation Mastery (Weeks 5-8)**
- Bug-free code on first attempt
- Optimize for readability and performance simultaneously
- Internalize idioms in all three languages

**Stage 4: Creative Problem Solving (Weeks 9+)**
- Solve problems with multiple constraints
- Combine techniques (DP + combinatorics)
- Create original problems

### Deliberate Practice Protocol

**Daily Routine**:
1. **Morning (30 min)**: Theory review + 1 derivation proof
2. **Afternoon (60 min)**: 3-5 problems, increasing difficulty
3. **Evening (15 min)**: Analyze mistakes, update mental models

**Weekly Deep Dive**:
- Pick one advanced topic (derangements, Catalan, etc.)
- Solve 10+ related problems
- Write explanation in your own words

### Chunking Strategy
Build hierarchical knowledge:
- **Chunk 1**: Basic formulas (P, C)
- **Chunk 2**: Problem type → formula mapping
- **Chunk 3**: Multi-step reasoning (constraints, restrictions)
- **Chunk 4**: Optimization patterns

### The Monk's Mental Discipline

**Before each problem**:
1. **Pause and breathe** (10 seconds)
2. **State the problem in simplest terms**
3. **Identify the core pattern**
4. **Choose the approach confidently**
5. **Code with focus, no distractions**

**After each problem**:
1. **Analyze complexity** (time & space)
2. **Consider alternatives** (was there a better way?)
3. **Extract the lesson** (what did I learn?)

---

## Practice Problems (Ordered by Difficulty)

### Foundational
1. Compute C(100, 50) without overflow
2. Generate all 3-letter permutations from "ABCDE"
3. Count anagrams of "MATHEMATICS"
4. Distribute 15 identical balls into 4 boxes

### Intermediate
5. Arrange 5 men and 5 women alternately in a row
6. Count binary strings of length n with no two consecutive 1s
7. Select a committee of 5 from 6 men and 4 women with at least 2 women
8. Seat n people at a round table with 2 specific people not adjacent

### Advanced
9. Count paths in n×m grid from (0,0) to (n,m) with obstacles
10. Compute nth Catalan number modulo 10^9+7
11. Derangement count for secret Santa with n people
12. Number of ways to partition n into k parts (Stirling second kind)

---

## Conclusion: The Path to Top 1%

**Key Differentiators**:
1. **Speed**: Recognize pattern → apply solution in < 1 minute
2. **Depth**: Understand *why* formulas work, not just *how* to use them
3. **Flexibility**: Seamlessly combine techniques for complex problems
4. **Precision**: Write bug-free, optimized code in one pass

**Your Next 30 Days**:
- Master all basic formulas and their derivations
- Solve 150+ problems across all pattern types
- Implement every technique in Rust, Python, and Go
- Build intuition through visualization and proof

**Remember**: The monk's path is one of patient mastery. Each problem is a meditation. Each insight is enlightenment. The top 1% isn't reached by speed alone—it's reached by *deep, unshakeable understanding*.

Now, begin your practice. 🧘‍♂️

# Permutations & Combinations: The Master's Guide

I'll craft this as a complete training manual—blending mathematical rigor, implementation mastery, and strategic problem-solving intuition. This isn't just about formulas; it's about developing the mental models that separate top-tier problem solvers from the rest.## Your Training Manual Is Ready

I've crafted a complete master's guide that goes far beyond formulas—this is about building the **intuition and mental models** that make combinatorics second nature.

### How to Use This Guide (Recommended Path)

**Week 1-2: Foundation Building**
- Study the "Foundational Mental Models" and "Decision-Making Framework" sections until you can explain them to someone else
- Manually derive each formula from first principles at least once
- Implement all basic computation functions in your preferred language first, then the others

**Week 3-4: Pattern Mastery**
- Memorize the "Problem Recognition Patterns" through active recall
- For each pattern, solve 10 variations
- Practice the decision tree: problem → pattern → approach in under 30 seconds

**Week 5+: Integration & Speed**
- Tackle the practice problems in order
- Time yourself: aim for < 5 minutes per problem (recognition + implementation)
- Start combining techniques for multi-constraint problems

### Key Insights to Internalize

**The Expert's Secret**: Before coding, ask these three questions:
1. "Am I counting sequences (order matters) or sets (order doesn't)?"
2. "What are the constraints that modify the standard formula?"
3. "Can I solve this by complementary counting or breaking into cases?"

**Performance Note for Your Languages**:
- **Python**: Use `math.comb()` for production (C-optimized), recursion with `@lru_cache` for DP patterns
- **Rust**: Leverage type system for compile-time safety; use `u128` or `BigInt` for large values
- **Go**: `math/big` for arbitrary precision; channels for parallel generation if needed

**The Metacognitive Edge**: The difference between good and exceptional isn't just solving more problems—it's **extracting deeper patterns** from each one. After every problem, spend 2 minutes asking: "What made this hard? What could I have seen faster?"

### Your First Challenge

Before moving on, complete this right now:

**Problem**: How many ways can you arrange the letters in "SUCCESS" such that no two S's are adjacent?

**Don't code yet**—first:
1. Identify the pattern type
2. State your approach in words
3. Predict the formula structure
4. Then implement in your language of choice

This is the monk's way: **think before you type**. Clarity of thought → clarity of code.

Would you like me to work through this challenge problem with you, or would you prefer to tackle it independently and then discuss your solution? I can provide the detailed breakdown of expert-level thinking for any problem.