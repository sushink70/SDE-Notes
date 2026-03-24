# Transformation Chains — A Comprehensive DSA Guide
### Full Rust Implementations | Deep Concepts | Mental Models

---

> *"A transformation is not just a function — it is a lens through which data reveals its hidden structure."*

---

## Table of Contents

1. [What Is a Transformation Chain?](#1-what-is-a-transformation-chain)
2. [Mathematical Foundation](#2-mathematical-foundation)
3. [Core Mental Model: The Pipeline Abstraction](#3-core-mental-model-the-pipeline-abstraction)
4. [Function Composition — The Root Concept](#4-function-composition--the-root-concept)
5. [Iterator Transformation Chains in Rust](#5-iterator-transformation-chains-in-rust)
6. [Prefix Sum Transform (Partial Sum)](#6-prefix-sum-transform-partial-sum)
7. [Difference Array Transform](#7-difference-array-transform)
8. [Running Statistics Transform](#8-running-statistics-transform)
9. [Coordinate Compression Transform](#9-coordinate-compression-transform)
10. [Discretization Transform](#10-discretization-transform)
11. [Sparse Table Transform (Static RMQ)](#11-sparse-table-transform-static-rmq)
12. [Binary Lifting Transform](#12-binary-lifting-transform)
13. [Euler Tour Transform (Tree Flattening)](#13-euler-tour-transform-tree-flattening)
14. [Rolling Hash Transform](#14-rolling-hash-transform)
15. [Z-Function Transform](#15-z-function-transform)
16. [KMP Failure Function Transform](#16-kmp-failure-function-transform)
17. [Suffix Array Transform](#17-suffix-array-transform)
18. [Monotonic Stack Transform](#18-monotonic-stack-transform)
19. [Monotonic Deque Transform (Sliding Window)](#19-monotonic-deque-transform-sliding-window)
20. [Bit Manipulation Transform Chains](#20-bit-manipulation-transform-chains)
21. [Segment Tree Lazy Propagation (Deferred Transform)](#21-segment-tree-lazy-propagation-deferred-transform)
22. [Square Root Decomposition Transform](#22-square-root-decomposition-transform)
23. [Dynamic Programming as a Transformation Chain](#23-dynamic-programming-as-a-transformation-chain)
24. [Graph Transformation Chains](#24-graph-transformation-chains)
25. [Two-Pointer Transform Pattern](#25-two-pointer-transform-pattern)
26. [Divide and Conquer Transform](#26-divide-and-conquer-transform)
27. [Composing Multiple Transforms](#27-composing-multiple-transforms)
28. [Mental Models for Mastery](#28-mental-models-for-mastery)

---

## 1. What Is a Transformation Chain?

### Concept from Scratch

Imagine you have raw data — say, an array of numbers: `[3, 1, 4, 1, 5, 9, 2, 6]`.

A **transformation** is an operation that takes this data and produces **new data** with a different shape or meaning. For example:
- Sorting it → `[1, 1, 2, 3, 4, 5, 6, 9]`  
- Computing prefix sums → `[3, 4, 8, 9, 14, 23, 25, 31]`  
- Marking it with boolean (is it > 4?) → `[false, false, false, false, true, true, false, true]`

A **Transformation Chain** is when you apply **multiple transformations in sequence**, where each step takes the output of the previous step as its input.

```
Raw Input
    |
    v
[Transform A]  ──►  Intermediate Result A
                              |
                              v
                    [Transform B]  ──►  Intermediate Result B
                                                |
                                                v
                                      [Transform C]  ──►  Final Output
```

### Why This Matters in DSA

Most hard algorithmic problems are NOT solved by a single clever trick. They are solved by **chaining transforms** in the right order:

- **Problem:** Range sum query with point updates  
  **Chain:** Raw array → Segment Tree (structure transform) → Query/Update (functional transform)

- **Problem:** Find longest repeated substring  
  **Chain:** String → Suffix Array → LCP Array → Answer

- **Problem:** Nearest smaller element for every index  
  **Chain:** Array → Monotonic Stack traversal → Result array

Understanding that these are all "chains" gives you a **unified mental framework** to attack any problem.

### Vocabulary You Must Know

| Term | Meaning |
|---|---|
| **Input Domain** | The set of valid inputs to a function/transform |
| **Output Domain (Codomain)** | The set of possible outputs |
| **Composition** | Chaining: output of f becomes input of g → g∘f |
| **Idempotent** | Applying a transform twice gives the same result as once |
| **Invertible** | There exists a reverse transform (e.g., prefix sum ↔ difference array) |
| **Lazy** | The transform is deferred until needed |
| **Eager** | The transform is computed immediately |
| **Monoid** | A structure with an associative binary operation and identity — critical for segment trees and reduce chains |

---

## 2. Mathematical Foundation

### Functions as Transformations

A function `f: A → B` is a transformation. In Rust terms, a function `fn f(a: A) -> B` is a transformation.

**Composition:** If `f: A → B` and `g: B → C`, then `g ∘ f: A → C` means "apply f first, then g."

```
f(x) = x + 1       (add one transform)
g(x) = x * 2       (double transform)
(g ∘ f)(x) = g(f(x)) = (x + 1) * 2
```

### Properties of Good Transforms in DSA

1. **Associativity:** `(a ○ b) ○ c = a ○ (b ○ c)` — enables divide and conquer
2. **Identity element:** `f(identity, x) = x` — enables range queries
3. **Commutativity:** `a ○ b = b ○ a` — simplifies merging (not always available)
4. **Invertibility:** `f⁻¹(f(x)) = x` — enables "undo" operations

### The Monoid Structure

A **monoid** is a set M with:
- A binary operation `⊕: M × M → M`
- An identity element `e` such that `e ⊕ x = x ⊕ e = x`

**Examples:**
- `(i64, +, 0)` — integers with addition  
- `(i64, max, i64::MIN)` — integers with maximum  
- `(String, concat, "")` — strings with concatenation  
- `(Matrix, multiply, I)` — matrices with multiplication

Almost every segment tree, sparse table, and divide-and-conquer transform is built on a monoid. Recognize the monoid → choose the right data structure.

---

## 3. Core Mental Model: The Pipeline Abstraction

### The Pipe Mental Model

Think of data flowing through pipes. Each pipe section does ONE job:

```
[SOURCE] ──pipe──► [FILTER] ──pipe──► [MAP] ──pipe──► [REDUCE] ──► [RESULT]
```

**ASCII Pipeline Visualization:**

```
                    TRANSFORMATION CHAIN PIPELINE
═══════════════════════════════════════════════════════════════

  ┌─────────┐      ┌─────────┐      ┌─────────┐      ┌────────┐
  │  INPUT  │─────►│TRANSFORM│─────►│TRANSFORM│─────►│ OUTPUT │
  │  DATA   │      │    A    │      │    B    │      │        │
  └─────────┘      └─────────┘      └─────────┘      └────────┘
  [3,1,4,1,5]   Sort & Dedup    Prefix Sum      Range Query
                [1,3,4,5]       [1,4,8,13]      Answer: 7

═══════════════════════════════════════════════════════════════
```

### Decision Tree: Which Transform to Apply?

```
PROBLEM RECEIVED
      │
      ▼
Is it a RANGE QUERY problem?
├── YES ──► Is there UPDATE?
│           ├── YES ──► Segment Tree / BIT Transform
│           └── NO  ──► Prefix Sum / Sparse Table
│
└── NO ──► Is it a STRING problem?
           ├── YES ──► Z-func / KMP / Rolling Hash / Suffix Array
           └── NO  ──► Is it TREE problem?
                        ├── YES ──► Euler Tour / Binary Lifting / HLD
                        └── NO  ──► Is it GRAPH problem?
                                    ├── YES ──► BFS/DFS/SCC transform
                                    └── NO  ──► Two Pointer / Mono Stack
```

---

## 4. Function Composition — The Root Concept

### What is Function Composition?

Before we build complex chains, understand the atom: composing two functions.

`compose(g, f)(x) = g(f(x))`

```rust
// ═══════════════════════════════════════════════════════
// FUNCTION COMPOSITION IN RUST
// Building the foundation of all transformation chains
// ═══════════════════════════════════════════════════════

/// Composes two functions: applies `f` first, then `g`.
/// This is the atomic unit of every transformation chain.
fn compose<A, B, C, F, G>(f: F, g: G) -> impl Fn(A) -> C
where
    F: Fn(A) -> B,
    G: Fn(B) -> C,
{
    move |x| g(f(x))
}

/// Composes a chain of transformations from a Vec of boxed functions.
/// Each function must share the same input/output type (endomorphism).
/// An endomorphism is a function where input type = output type: f: A → A
fn compose_chain<T: Clone>(
    funcs: Vec<Box<dyn Fn(T) -> T>>,
) -> impl Fn(T) -> T {
    move |x| funcs.iter().fold(x, |acc, f| f(acc))
}

fn main() {
    // Chain: add_one → double → square
    let add_one = |x: i64| x + 1;
    let double = |x: i64| x * 2;
    let square = |x: i64| x * x;

    // Compose two functions
    let add_then_double = compose(add_one, double);
    println!("compose(add_one, double)(3) = {}", add_then_double(3));
    // (3 + 1) * 2 = 8

    // Compose a chain of boxed functions
    let chain: Vec<Box<dyn Fn(i64) -> i64>> = vec![
        Box::new(|x| x + 1),  // Step 1: add 1
        Box::new(|x| x * 2),  // Step 2: double
        Box::new(|x| x * x),  // Step 3: square
    ];
    let full_transform = compose_chain(chain);
    println!("chain(3) = {}", full_transform(3)); // ((3+1)*2)^2 = 64

    // ── Identity Transform ──
    // Applying no transform: the baseline
    let identity = compose_chain::<i64>(vec![]);
    println!("identity(42) = {}", identity(42)); // 42
}
```

**Complexity:**
- Time: O(k) per application, where k = number of functions in chain
- Space: O(k) to store closures

### The Key Insight

Every algorithm you will ever write is a specialization of this pattern. The difference between a beginner and an expert is that the expert **sees** the chain structure before writing a single line.

---

## 5. Iterator Transformation Chains in Rust

### What Are Iterators?

An **iterator** is an object that produces values one at a time. In Rust, iterators are **lazy** — they do nothing until you "pull" a value from them. This is the most fundamental transformation chain in Rust.

**Iterator Adapters** are transforms. Each adapter wraps the previous iterator and transforms what comes out.

```
Original Iterator
      │
      ▼
   .map(f)         ← Transform each element
      │
      ▼
  .filter(p)       ← Keep only elements matching predicate p
      │
      ▼
  .flat_map(f)     ← Transform and flatten
      │
      ▼
  .take_while(p)   ← Stop when predicate fails
      │
      ▼
  .collect()       ← Consume: materialize into Vec, HashMap, etc.
```

```rust
// ═══════════════════════════════════════════════════════
// ITERATOR TRANSFORMATION CHAINS
// Rust's native lazy pipeline system
// ═══════════════════════════════════════════════════════

fn demonstrate_iterator_chains() {
    let data = vec![1i64, 2, 3, 4, 5, 6, 7, 8, 9, 10];

    // ── Chain 1: Filter → Map → Sum ──
    // Keep evens, square them, sum all
    let result: i64 = data.iter()
        .filter(|&&x| x % 2 == 0)     // [2, 4, 6, 8, 10]
        .map(|&x| x * x)               // [4, 16, 36, 64, 100]
        .sum();                        // 220
    println!("Sum of squares of evens: {}", result);

    // ── Chain 2: Enumerate → Filter → Map ──
    // Get (index, value) pairs where value > 5
    let indexed: Vec<(usize, i64)> = data.iter()
        .enumerate()
        .filter(|(_, &v)| v > 5)
        .map(|(i, &v)| (i, v))
        .collect();
    println!("Indexed values > 5: {:?}", indexed);

    // ── Chain 3: Windows → Map (Sliding Transform) ──
    // Compute differences between consecutive elements
    let differences: Vec<i64> = data.windows(2)
        .map(|w| w[1] - w[0])
        .collect();
    println!("Consecutive differences: {:?}", differences);

    // ── Chain 4: Scan (Running Prefix Transform) ──
    // scan is like fold but yields intermediate states
    // This builds a prefix sum lazily!
    let prefix_sums: Vec<i64> = data.iter()
        .scan(0i64, |acc, &x| {
            *acc += x;
            Some(*acc)
        })
        .collect();
    println!("Prefix sums via scan: {:?}", prefix_sums);

    // ── Chain 5: Flat Map (Expansion Transform) ──
    // Each element produces multiple elements
    let expanded: Vec<i64> = (1i64..=4)
        .flat_map(|x| vec![x, x * 10, x * 100])
        .collect();
    println!("Flat mapped: {:?}", expanded);

    // ── Chain 6: Zip (Parallel Transform) ──
    // Combine two sequences element-by-element
    let a = vec![1i64, 2, 3, 4, 5];
    let b = vec![10i64, 20, 30, 40, 50];
    let combined: Vec<i64> = a.iter().zip(b.iter()).map(|(&x, &y)| x + y).collect();
    println!("Zipped sum: {:?}", combined);

    // ── Chain 7: Fold (Reduction Transform) ──
    // Collapse entire sequence into one value with custom logic
    let product: i64 = data.iter().fold(1, |acc, &x| acc * x);
    println!("Product: {}", product);

    // ── Chain 8: Complex Multi-Stage Chain ──
    // Problem: Given numbers 1..=20, find sum of cubes of
    // numbers divisible by 3 or 5, but not both
    let complex_result: i64 = (1i64..=20)
        .filter(|&x| (x % 3 == 0) ^ (x % 5 == 0)) // XOR: one but not both
        .map(|x| x * x * x)                         // cube
        .sum();
    println!("Complex chain result: {}", complex_result);
}

// ── Custom Iterator Transform ──
// Build your own iterator adapter (a custom transform step)
struct StepBy<I> {
    iter: I,
    step: usize,
    count: usize,
}

impl<I: Iterator> Iterator for StepBy<I> {
    type Item = I::Item;

    fn next(&mut self) -> Option<Self::Item> {
        loop {
            let item = self.iter.next()?;
            if self.count % self.step == 0 {
                self.count += 1;
                return Some(item);
            }
            self.count += 1;
        }
    }
}

fn main() {
    demonstrate_iterator_chains();
}
```

**Why Lazy Evaluation Matters:**

```
EAGER (compute everything now):
  [1..1_000_000] → filter → new Vec(500_000) → map → new Vec(500_000) → take(10)
  Memory used: O(n) even though we only need 10 results

LAZY (compute on demand):
  [1..1_000_000] → filter → map → take(10) → collect
  Memory used: O(1) — only generates 10 results total!
```

This is why Rust iterators are lazy by default. The iterator chain is a **description of a computation**, not the computation itself.

---

## 6. Prefix Sum Transform (Partial Sum)

### What Is a Prefix Sum?

A **prefix sum** (also called a **partial sum** or **cumulative sum**) transforms an array `A` into a new array `P` where:

```
P[0] = A[0]
P[1] = A[0] + A[1]
P[2] = A[0] + A[1] + A[2]
...
P[i] = A[0] + A[1] + ... + A[i]
```

**Why Is This Useful?**

Once you have `P`, you can answer **any range sum query** `sum(A[l..=r])` in O(1):

```
sum(A[l..=r]) = P[r] - P[l-1]
```

**ASCII Visualization:**

```
Array A:    [3,  1,  4,  1,  5,  9,  2,  6]
Indices:     0   1   2   3   4   5   6   7

Prefix P:   [3,  4,  8,  9, 14, 23, 25, 31]

Query: sum(A[2..=5]) = P[5] - P[1] = 23 - 4 = 19
Verify:  A[2]+A[3]+A[4]+A[5] = 4+1+5+9 = 19 ✓

      P[5]                P[1]
       ↓                   ↓
[3, 4, 8, 9, 14, 23, 25, 31]
        ↑___________↑
        This range subtracted
```

**Transform Flow:**

```
RAW ARRAY  ──[prefix_sum_transform]──►  PREFIX ARRAY
                                              │
                                              ▼
                                    ──[query_transform]──►  ANSWER
```

```rust
// ═══════════════════════════════════════════════════════
// PREFIX SUM TRANSFORM — Complete Implementation
// ═══════════════════════════════════════════════════════

/// Represents the result of a prefix sum transformation.
/// The original array is consumed and encoded into this structure.
struct PrefixSum {
    /// prefix[i] = sum of original[0..=i]
    /// We use 1-indexing internally for cleaner range queries.
    /// prefix[0] = 0 (sentinel/identity element)
    prefix: Vec<i64>,
}

impl PrefixSum {
    /// FORWARD TRANSFORM: O(n)
    /// Converts raw array into prefix sum array.
    ///
    /// Transform equation: prefix[i] = prefix[i-1] + arr[i-1]
    fn build(arr: &[i64]) -> Self {
        let n = arr.len();
        let mut prefix = vec![0i64; n + 1]; // +1 for the sentinel at index 0
        for i in 1..=n {
            prefix[i] = prefix[i - 1] + arr[i - 1];
        }
        PrefixSum { prefix }
    }

    /// QUERY TRANSFORM: O(1)
    /// Returns sum of arr[l..=r] (0-indexed, inclusive).
    ///
    /// Formula: prefix[r+1] - prefix[l]
    fn query(&self, l: usize, r: usize) -> i64 {
        assert!(l <= r, "l must be <= r");
        self.prefix[r + 1] - self.prefix[l]
    }

    /// INVERSE TRANSFORM: O(n)
    /// Recovers the original array from the prefix sum.
    /// This demonstrates invertibility — a key property.
    fn recover_original(&self) -> Vec<i64> {
        let n = self.prefix.len() - 1;
        (1..=n).map(|i| self.prefix[i] - self.prefix[i - 1]).collect()
    }
}

// ── 2D Prefix Sum ──
// For 2D grids: sum of any rectangular sub-region in O(1)
//
// Build: P[i][j] = A[i][j] + P[i-1][j] + P[i][j-1] - P[i-1][j-1]
// Query: sum(r1,c1,r2,c2) = P[r2][c2] - P[r1-1][c2] - P[r2][c1-1] + P[r1-1][c1-1]
//
// Inclusion-Exclusion Visualization:
//
//   ┌───────────────┐
//   │   A           │
//   │    ┌──────┐   │
//   │  B │  ?   │ C │   ? = Total - B - C + A (we subtracted A twice)
//   │    └──────┘   │
//   └───────────────┘

struct PrefixSum2D {
    prefix: Vec<Vec<i64>>,
    rows: usize,
    cols: usize,
}

impl PrefixSum2D {
    /// FORWARD TRANSFORM: O(rows * cols)
    fn build(grid: &[Vec<i64>]) -> Self {
        let rows = grid.len();
        let cols = if rows == 0 { 0 } else { grid[0].len() };
        let mut prefix = vec![vec![0i64; cols + 1]; rows + 1];

        for i in 1..=rows {
            for j in 1..=cols {
                prefix[i][j] = grid[i - 1][j - 1]
                    + prefix[i - 1][j]
                    + prefix[i][j - 1]
                    - prefix[i - 1][j - 1]; // subtract the doubly-added corner
            }
        }
        PrefixSum2D { prefix, rows, cols }
    }

    /// QUERY TRANSFORM: O(1)
    /// Returns sum of rectangle (r1,c1)..(r2,c2) inclusive, 0-indexed.
    fn query(&self, r1: usize, c1: usize, r2: usize, c2: usize) -> i64 {
        self.prefix[r2 + 1][c2 + 1]
            - self.prefix[r1][c2 + 1]
            - self.prefix[r2 + 1][c1]
            + self.prefix[r1][c1]
    }
}

// ── Prefix XOR Transform ──
// Same idea, but with XOR instead of +.
// XOR is its own inverse: a XOR a = 0
// query(l, r) = prefix[r+1] XOR prefix[l]

struct PrefixXor {
    prefix: Vec<u64>,
}

impl PrefixXor {
    fn build(arr: &[u64]) -> Self {
        let n = arr.len();
        let mut prefix = vec![0u64; n + 1];
        for i in 1..=n {
            prefix[i] = prefix[i - 1] ^ arr[i - 1];
        }
        PrefixXor { prefix }
    }

    fn query(&self, l: usize, r: usize) -> u64 {
        self.prefix[r + 1] ^ self.prefix[l]
    }
}

// ── Prefix MAX Transform ──
// Useful for: "what is the maximum in the first k elements?"
// NOTE: This is NOT invertible and does NOT support arbitrary range queries.
// It only supports prefix queries: max(arr[0..=r]).

struct PrefixMax {
    prefix: Vec<i64>,
}

impl PrefixMax {
    fn build(arr: &[i64]) -> Self {
        let mut prefix = vec![i64::MIN; arr.len()];
        if !arr.is_empty() {
            prefix[0] = arr[0];
            for i in 1..arr.len() {
                prefix[i] = prefix[i - 1].max(arr[i]);
            }
        }
        PrefixMax { prefix }
    }

    /// Returns max of arr[0..=r]
    fn query_prefix(&self, r: usize) -> i64 {
        self.prefix[r]
    }
}

fn main() {
    // ── 1D Prefix Sum Demo ──
    let arr = vec![3i64, 1, 4, 1, 5, 9, 2, 6];
    let ps = PrefixSum::build(&arr);

    println!("=== 1D Prefix Sum ===");
    println!("Original:    {:?}", arr);
    println!("Prefix:      {:?}", &ps.prefix[1..]);
    println!("sum(2..=5) = {}", ps.query(2, 5)); // 4+1+5+9 = 19
    println!("sum(0..=7) = {}", ps.query(0, 7)); // 31
    println!("Recovered:   {:?}", ps.recover_original());

    // ── 2D Prefix Sum Demo ──
    let grid = vec![
        vec![1i64, 2, 3],
        vec![4i64, 5, 6],
        vec![7i64, 8, 9],
    ];
    let ps2d = PrefixSum2D::build(&grid);
    println!("\n=== 2D Prefix Sum ===");
    println!("sum((0,0)..(1,1)) = {}", ps2d.query(0, 0, 1, 1)); // 1+2+4+5=12
    println!("sum((1,1)..(2,2)) = {}", ps2d.query(1, 1, 2, 2)); // 5+6+8+9=28

    // ── Prefix XOR Demo ──
    let arr_xor = vec![1u64, 2, 3, 4, 5];
    let pxor = PrefixXor::build(&arr_xor);
    println!("\n=== Prefix XOR ===");
    println!("xor(1..=3) = {}", pxor.query(1, 3)); // 2^3^4 = 5
}
```

**Complexity Summary:**

| Operation | Brute Force | Prefix Sum |
|---|---|---|
| Build | O(1) | O(n) |
| Single query | O(n) | O(1) |
| Q queries | O(n × Q) | O(n + Q) |

**Key Insight:** You pay O(n) once to build, then answer each query in O(1). If Q > 1, you always win.

---

## 7. Difference Array Transform

### What Is a Difference Array?

A **difference array** `D` is the **inverse transform** of the prefix sum. Where prefix sum transforms from deltas to cumulative values, the difference array transforms from cumulative values back to deltas.

```
Original A:    [3,  1,  4,  1,  5,  9,  2,  6]
Difference D:  [3, -2,  3, -3,  4,  4, -7,  4]

D[0] = A[0]
D[i] = A[i] - A[i-1]  for i > 0

Reconstruct A from D: A[i] = D[0] + D[1] + ... + D[i]  (prefix sum of D!)
```

### Why Is This Useful?

The difference array enables **range update in O(1)**:

**Goal:** Add value `v` to all elements `A[l..=r]`.  
**Naive approach:** O(r - l + 1) = O(n) per update.  
**Difference array approach:**
1. `D[l] += v`   ← marks where the addition starts
2. `D[r+1] -= v` ← marks where the addition ends

After all updates, reconstruct A with a prefix sum scan: O(n).

```
ASCII Visualization of Range Update:

Original:  [0, 0, 0, 0, 0, 0, 0, 0]
Add 5 to range [2, 5]:
D:         [0, 0, +5, 0, 0, 0, -5, 0]
Prefix sum of D: [0, 0, 5, 5, 5, 5, 0, 0]
                           ↑__________↑
                      The +5 "flows" from index 2 to 5
```

**Transform Chain:**

```
UPDATES (l, r, v)
      │
      ▼
[Difference Array Encode]  ──►  D array (sparse updates)
                                      │
                                      ▼
                             [Prefix Sum Recover]  ──►  Final array
```

```rust
// ═══════════════════════════════════════════════════════
// DIFFERENCE ARRAY TRANSFORM — Complete Implementation
// ═══════════════════════════════════════════════════════

/// Difference array for efficient range updates.
/// Think of it as a "change log" — recording where values
/// start increasing and where they stop.
struct DifferenceArray {
    diff: Vec<i64>,
    n: usize,
}

impl DifferenceArray {
    /// Initialize from an existing array.
    /// FORWARD TRANSFORM: O(n)
    fn from_array(arr: &[i64]) -> Self {
        let n = arr.len();
        let mut diff = vec![0i64; n + 1]; // +1 to handle right boundary
        if n > 0 {
            diff[0] = arr[0];
            for i in 1..n {
                diff[i] = arr[i] - arr[i - 1];
            }
        }
        DifferenceArray { diff, n }
    }

    /// Initialize with all zeros.
    fn zeros(n: usize) -> Self {
        DifferenceArray {
            diff: vec![0i64; n + 1],
            n,
        }
    }

    /// RANGE UPDATE: O(1)
    /// Adds `v` to all elements in [l, r] (0-indexed, inclusive).
    ///
    /// Mental model: "Turn on" a faucet at l, "Turn off" at r+1.
    fn update(&mut self, l: usize, r: usize, v: i64) {
        assert!(r < self.n, "r out of bounds");
        self.diff[l] += v;
        self.diff[r + 1] -= v; // sentinel handles r = n-1 safely
    }

    /// INVERSE TRANSFORM (Prefix Sum Recovery): O(n)
    /// Materializes the actual array after all updates.
    fn build(&self) -> Vec<i64> {
        let mut result = vec![0i64; self.n];
        let mut running = 0i64;
        for i in 0..self.n {
            running += self.diff[i];
            result[i] = running;
        }
        result
    }

    /// Query a single element: O(n) in worst case.
    /// Better: call build() first if querying multiple elements.
    fn point_query(&self, idx: usize) -> i64 {
        self.diff[0..=idx].iter().sum()
    }
}

// ── 2D Difference Array ──
// Enables range rectangle updates in O(1) per update.
// Update rectangle (r1,c1)..(r2,c2): add v to all cells.
//
// Visual:
//   diff[r1][c1]   += v    (start of addition)
//   diff[r1][c2+1] -= v    (end of column range)
//   diff[r2+1][c1] -= v    (end of row range)
//   diff[r2+1][c2+1] += v  (re-add doubly-subtracted corner)
//
// Then reconstruct with 2D prefix sum.

struct DifferenceArray2D {
    diff: Vec<Vec<i64>>,
    rows: usize,
    cols: usize,
}

impl DifferenceArray2D {
    fn zeros(rows: usize, cols: usize) -> Self {
        DifferenceArray2D {
            diff: vec![vec![0i64; cols + 2]; rows + 2],
            rows,
            cols,
        }
    }

    /// Range rectangle update: O(1)
    fn update(&mut self, r1: usize, c1: usize, r2: usize, c2: usize, v: i64) {
        self.diff[r1][c1] += v;
        self.diff[r1][c2 + 1] -= v;
        self.diff[r2 + 1][c1] -= v;
        self.diff[r2 + 1][c2 + 1] += v;
    }

    /// Build final grid: O(rows * cols)
    fn build(&self) -> Vec<Vec<i64>> {
        let mut result = vec![vec![0i64; self.cols]; self.rows];
        // First, prefix sum along rows
        let mut row_prefix = self.diff.clone();
        for i in 0..=self.rows {
            for j in 1..=self.cols {
                row_prefix[i][j] += row_prefix[i][j - 1];
            }
        }
        // Then, prefix sum along columns
        for i in 0..self.rows {
            for j in 0..self.cols {
                let mut col_sum = 0i64;
                for k in 0..=i {
                    col_sum += row_prefix[k][j];
                }
                result[i][j] = col_sum;
            }
        }
        // More efficient: 2D prefix sum of diff directly
        result
    }

    /// Efficient O(rows * cols) build using 2D prefix scan
    fn build_efficient(&self) -> Vec<Vec<i64>> {
        let mut p = self.diff.clone();
        // Row-wise prefix sum
        for i in 0..=self.rows + 1 {
            for j in 1..=self.cols + 1 {
                p[i][j] += p[i][j - 1];
            }
        }
        // Column-wise prefix sum
        for j in 0..=self.cols + 1 {
            for i in 1..=self.rows + 1 {
                p[i][j] += p[i - 1][j];
            }
        }
        (0..self.rows)
            .map(|i| (0..self.cols).map(|j| p[i][j]).collect())
            .collect()
    }
}

fn main() {
    // ── 1D Demo ──
    println!("=== 1D Difference Array ===");
    let mut da = DifferenceArray::zeros(8);
    da.update(2, 5, 5); // Add 5 to indices 2..=5
    da.update(0, 3, 3); // Add 3 to indices 0..=3
    da.update(4, 7, -2); // Sub 2 from indices 4..=7
    let result = da.build();
    println!("Result: {:?}", result);
    // Index: 0  1  2  3   4   5   6   7
    // +5@2..5:  0  0  5   5   5   5   0   0
    // +3@0..3:  3  3  3   3   0   0   0   0
    // -2@4..7:  0  0  0   0  -2  -2  -2  -2
    // Total:    3  3  8   8   3   3  -2  -2

    // ── From existing array ──
    let arr = vec![1i64, 3, 5, 7, 9];
    let da2 = DifferenceArray::from_array(&arr);
    println!("\nOriginal: {:?}", arr);
    println!("Diff array: {:?}", &da2.diff[..5]);
    println!("Recovered: {:?}", da2.build());
}
```

**The Duality:**

```
ARRAY ────[difference transform]────► DIFF ARRAY
DIFF ARRAY ────[prefix sum transform]────► ARRAY

These are INVERSE transforms of each other!
This duality is used everywhere in competitive programming.
```

---

## 8. Running Statistics Transform

### Concept

A running statistics transform converts a sequence into a sequence of cumulative statistical summaries. This extends the prefix sum idea to other aggregation functions.

```rust
// ═══════════════════════════════════════════════════════
// RUNNING STATISTICS TRANSFORMATION CHAIN
// ═══════════════════════════════════════════════════════

/// A running statistics tracker that processes a stream of values
/// and maintains cumulative statistics at each step.
#[derive(Debug, Clone)]
struct RunningStats {
    count: usize,
    sum: f64,
    sum_sq: f64,   // sum of squares: for variance
    min: f64,
    max: f64,
}

impl RunningStats {
    fn new() -> Self {
        RunningStats {
            count: 0,
            sum: 0.0,
            sum_sq: 0.0,
            min: f64::INFINITY,
            max: f64::NEG_INFINITY,
        }
    }

    /// Update transform: incorporate one new value — O(1)
    fn update(&mut self, x: f64) {
        self.count += 1;
        self.sum += x;
        self.sum_sq += x * x;
        self.min = self.min.min(x);
        self.max = self.max.max(x);
    }

    fn mean(&self) -> f64 {
        if self.count == 0 { return 0.0; }
        self.sum / self.count as f64
    }

    /// Variance = E[X²] - (E[X])²
    fn variance(&self) -> f64 {
        if self.count == 0 { return 0.0; }
        let n = self.count as f64;
        self.sum_sq / n - (self.sum / n).powi(2)
    }

    fn std_dev(&self) -> f64 {
        self.variance().sqrt()
    }
}

/// Transform an array into a sequence of running statistics snapshots.
fn running_stats_transform(data: &[f64]) -> Vec<RunningStats> {
    let mut stats = RunningStats::new();
    data.iter().map(|&x| {
        stats.update(x);
        stats.clone()
    }).collect()
}

// ── Welford's Online Algorithm ──
// Numerically stable running mean and variance.
// Regular variance formula can lose precision for large numbers.
// Welford's algorithm avoids this by computing updates incrementally.

#[derive(Debug, Clone)]
struct WelfordStats {
    count: usize,
    mean: f64,
    m2: f64, // Sum of squared deviations from mean
}

impl WelfordStats {
    fn new() -> Self { WelfordStats { count: 0, mean: 0.0, m2: 0.0 } }

    fn update(&mut self, x: f64) {
        self.count += 1;
        let delta = x - self.mean;
        self.mean += delta / self.count as f64; // New mean
        let delta2 = x - self.mean;             // Note: uses NEW mean
        self.m2 += delta * delta2;              // Update sum of squared deviations
    }

    fn variance(&self) -> f64 {
        if self.count < 2 { return 0.0; }
        self.m2 / (self.count - 1) as f64 // Bessel's correction for sample variance
    }
}

fn main() {
    let data = vec![2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0];
    let snapshots = running_stats_transform(&data);

    println!("=== Running Statistics Transform ===");
    for (i, s) in snapshots.iter().enumerate() {
        println!(
            "After {} elements: mean={:.2}, stddev={:.2}, min={}, max={}",
            i + 1, s.mean(), s.std_dev(), s.min, s.max
        );
    }
}
```

---

## 9. Coordinate Compression Transform

### What Is Coordinate Compression?

When values in your array can be very large (e.g., up to 10^9) but the **number of distinct values is small** (e.g., at most n = 10^5), coordinate compression **maps large values to small indices**.

**Before compression:** Values ∈ {1, 5, 100, 1000000}  
**After compression:** Values ∈ {0, 1, 2, 3}

This is critical for using segment trees or BITs when the value range is enormous.

```
ORIGINAL VALUES:  [100, 5, 1000000, 1, 5, 100]
                         │
                  [Sort & Deduplicate]
                         │
                         ▼
SORTED UNIQUE:    [1, 5, 100, 1000000]
                  [0, 1,  2,        3]   ← compressed indices
                         │
                  [Binary Search Rank]
                         │
                         ▼
COMPRESSED:       [2, 1, 3, 0, 1, 2]   ← ready for BIT/Segment Tree
```

```rust
// ═══════════════════════════════════════════════════════
// COORDINATE COMPRESSION TRANSFORM
// ═══════════════════════════════════════════════════════

use std::collections::HashMap;

/// Coordinate compressor for any Ord + Clone type.
/// Transforms arbitrary large values into compact 0-indexed ranks.
struct Compressor<T: Ord + Clone> {
    /// Sorted list of unique values — the "dictionary"
    sorted_unique: Vec<T>,
}

impl<T: Ord + Clone> Compressor<T> {
    /// FORWARD TRANSFORM: Build the compressor from data.
    /// O(n log n) — sort dominates.
    fn build(data: &[T]) -> Self {
        let mut sorted_unique: Vec<T> = data.to_vec();
        sorted_unique.sort_unstable();
        sorted_unique.dedup(); // Remove duplicates
        Compressor { sorted_unique }
    }

    /// COMPRESS: Map a value to its rank (0-indexed).
    /// O(log n) — binary search.
    fn compress(&self, val: &T) -> usize {
        // binary_search returns Ok(index) if found
        self.sorted_unique
            .binary_search(val)
            .expect("Value not in compressor — build includes all values")
    }

    /// DECOMPRESS: Map a rank back to original value.
    /// O(1) — direct array access.
    fn decompress(&self, rank: usize) -> &T {
        &self.sorted_unique[rank]
    }

    /// Compress an entire array.
    fn compress_all(&self, data: &[T]) -> Vec<usize> {
        data.iter().map(|v| self.compress(v)).collect()
    }

    /// Total number of unique values (compressed range size).
    fn size(&self) -> usize {
        self.sorted_unique.len()
    }
}

// ── Application: Count Inversions using BIT + Coordinate Compression ──
// An inversion is a pair (i, j) where i < j but arr[i] > arr[j].
//
// Chain: Raw Array → Compress → BIT Query → Count Inversions
//
// Algorithm:
// 1. Compress values to [0, n-1]
// 2. Process array right to left
// 3. For each element, count how many elements to its right are smaller
//    (= BIT prefix query on already-processed elements)
// 4. Add current element to BIT

struct BinaryIndexedTree {
    tree: Vec<i64>,
    n: usize,
}

impl BinaryIndexedTree {
    fn new(n: usize) -> Self {
        BinaryIndexedTree { tree: vec![0; n + 1], n }
    }

    /// Update: add delta at position i (1-indexed)
    fn update(&mut self, mut i: usize, delta: i64) {
        i += 1; // Convert to 1-indexed
        while i <= self.n {
            self.tree[i] += delta;
            i += i & i.wrapping_neg(); // i += lowest set bit of i
        }
    }

    /// Query: prefix sum [0..=i] (0-indexed)
    fn query(&self, mut i: usize) -> i64 {
        i += 1; // Convert to 1-indexed
        let mut sum = 0i64;
        while i > 0 {
            sum += self.tree[i];
            i -= i & i.wrapping_neg(); // i -= lowest set bit of i
        }
        sum
    }
}

fn count_inversions(arr: &[i64]) -> i64 {
    let n = arr.len();
    if n == 0 { return 0; }

    // Step 1: Coordinate compression
    let comp = Compressor::build(arr);
    let compressed = comp.compress_all(arr);
    let m = comp.size();

    // Step 2: Count inversions using BIT
    let mut bit = BinaryIndexedTree::new(m);
    let mut inversions = 0i64;

    // Process from right to left
    for &c in compressed.iter().rev() {
        // Count elements already processed (to the right) that are smaller than c
        if c > 0 {
            inversions += bit.query(c - 1);
        }
        bit.update(c, 1);
    }

    inversions
}

fn main() {
    // ── Compressor Demo ──
    let data = vec![100i64, 5, 1_000_000, 1, 5, 100];
    let comp = Compressor::build(&data);
    println!("=== Coordinate Compression ===");
    println!("Original:   {:?}", data);
    println!("Compressed: {:?}", comp.compress_all(&data));
    println!("Unique vals: {:?}", comp.sorted_unique);

    // ── Inversion Count Demo ──
    let arr = vec![3i64, 1, 2, 4, 5];
    println!("\n=== Inversion Count ===");
    println!("Array: {:?}", arr);
    println!("Inversions: {}", count_inversions(&arr)); // (3,1),(3,2) = 2

    let arr2 = vec![5i64, 4, 3, 2, 1];
    println!("Inversions in {:?}: {}", arr2, count_inversions(&arr2)); // n*(n-1)/2 = 10
}
```

---

## 10. Discretization Transform

### Concept

Discretization is coordinate compression applied to floating-point or real-valued data to map continuous values into discrete bins. Closely related to coordinate compression but often involves **ranges** rather than point values.

```rust
// ═══════════════════════════════════════════════════════
// DISCRETIZATION TRANSFORM
// ═══════════════════════════════════════════════════════

/// Discretize continuous values into bins of fixed width.
fn discretize_fixed_bins(values: &[f64], num_bins: usize) -> Vec<usize> {
    if values.is_empty() { return vec![]; }
    let min = values.iter().cloned().fold(f64::INFINITY, f64::min);
    let max = values.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
    let range = max - min;

    if range == 0.0 {
        return vec![0; values.len()];
    }

    values.iter().map(|&v| {
        let bin = ((v - min) / range * num_bins as f64) as usize;
        bin.min(num_bins - 1) // Clamp: max value goes to last bin
    }).collect()
}

/// Event-based discretization: given a set of "interesting" values
/// (from queries or updates), discretize a different array against them.
fn discretize_by_events(values: &[i64], events: &[i64]) -> Vec<usize> {
    // Sort and deduplicate events to form the discrete scale
    let mut scale: Vec<i64> = events.to_vec();
    scale.sort_unstable();
    scale.dedup();

    values.iter().map(|&v| {
        scale.partition_point(|&e| e < v) // = number of events < v
    }).collect()
}
```

---

## 11. Sparse Table Transform (Static RMQ)

### What Is a Sparse Table?

A **sparse table** is a data structure built by a preprocessing transform that enables O(1) range minimum (or maximum) queries, but only for **static arrays** (no updates).

**Key Insight:** Any range `[l, r]` can be covered by two overlapping power-of-2 length intervals. For idempotent operations (like min, max, GCD), overlapping is fine.

```
SPARSE TABLE BUILD VISUALIZATION:

Array:   [2, 4, 3, 1, 6, 7, 8, 9]
Index:    0  1  2  3  4  5  6  7

Layer 0 (length 1):  [2, 4, 3, 1, 6, 7, 8, 9]
Layer 1 (length 2):  [min(2,4), min(4,3), min(3,1), min(1,6), min(6,7), min(7,8), min(8,9)]
                   = [2, 3, 1, 1, 6, 7, 8]
Layer 2 (length 4):  [min(2,3,4,3), min(3,1,1,6), min(1,1,6,7), min(1,6,7,8)]
                   = [2, 1, 1, 1]
Layer 3 (length 8):  [min of all 8] = [1]

QUERY min(2, 6):   length = 5, log2(5) = 2 (floor)
  k = 2, length 2^k = 4
  Interval 1: [2, 2+4-1] = [2, 5]    → table[2][2] = 1
  Interval 2: [6-4+1, 6] = [3, 6]    → table[2][3] = 1
  Answer: min(1, 1) = 1 ✓
```

```rust
// ═══════════════════════════════════════════════════════
// SPARSE TABLE TRANSFORM — Static Range Minimum Query
// ═══════════════════════════════════════════════════════

struct SparseTable {
    /// table[k][i] = min/max of arr[i..i + 2^k]
    table: Vec<Vec<i64>>,
    /// log2_floor[i] = floor(log2(i)) precomputed
    log2_floor: Vec<usize>,
    n: usize,
}

impl SparseTable {
    /// FORWARD TRANSFORM: O(n log n) time, O(n log n) space
    ///
    /// Transform equation:
    ///   table[0][i] = arr[i]                             (base case)
    ///   table[k][i] = min(table[k-1][i], table[k-1][i + 2^(k-1)])
    fn build_min(arr: &[i64]) -> Self {
        let n = arr.len();
        if n == 0 {
            return SparseTable { table: vec![], log2_floor: vec![], n: 0 };
        }

        // Precompute floor(log2(i)) for all i in [1..=n]
        let mut log2_floor = vec![0usize; n + 1];
        for i in 2..=n {
            log2_floor[i] = log2_floor[i / 2] + 1;
        }

        let k_max = log2_floor[n] + 1;
        let mut table = vec![vec![i64::MAX; n]; k_max];

        // Layer 0: identity (no transformation yet)
        for i in 0..n {
            table[0][i] = arr[i];
        }

        // Build each layer from the previous (bottom-up DP)
        for k in 1..k_max {
            let half = 1 << (k - 1); // 2^(k-1)
            for i in 0..n {
                if i + (1 << k) <= n { // ensure window fits
                    table[k][i] = table[k - 1][i].min(table[k - 1][i + half]);
                }
            }
        }

        SparseTable { table, log2_floor, n }
    }

    /// QUERY TRANSFORM: O(1)
    /// Returns minimum in arr[l..=r].
    ///
    /// Key idea: cover [l, r] with two overlapping intervals of length 2^k.
    /// Overlapping is OK because min is idempotent: min(x, x) = x.
    fn query_min(&self, l: usize, r: usize) -> i64 {
        assert!(l <= r && r < self.n);
        let len = r - l + 1;
        let k = self.log2_floor[len]; // largest k such that 2^k <= len
        let half = 1 << k;
        // Two overlapping intervals: [l, l+half-1] and [r-half+1, r]
        self.table[k][l].min(self.table[k][r + 1 - half])
    }
}

// ── Sparse Table for GCD (also idempotent) ──
fn gcd(a: u64, b: u64) -> u64 {
    if b == 0 { a } else { gcd(b, a % b) }
}

struct SparseTableGcd {
    table: Vec<Vec<u64>>,
    log2_floor: Vec<usize>,
    n: usize,
}

impl SparseTableGcd {
    fn build(arr: &[u64]) -> Self {
        let n = arr.len();
        let mut log2_floor = vec![0usize; n + 1];
        for i in 2..=n { log2_floor[i] = log2_floor[i / 2] + 1; }
        let k_max = log2_floor[n.max(1)] + 1;
        let mut table = vec![vec![0u64; n]; k_max];
        for i in 0..n { table[0][i] = arr[i]; }
        for k in 1..k_max {
            let half = 1 << (k - 1);
            for i in 0..n {
                if i + (1 << k) <= n {
                    table[k][i] = gcd(table[k-1][i], table[k-1][i + half]);
                } else {
                    table[k][i] = table[k-1][i];
                }
            }
        }
        SparseTableGcd { table, log2_floor, n }
    }

    fn query_gcd(&self, l: usize, r: usize) -> u64 {
        let len = r - l + 1;
        let k = self.log2_floor[len];
        let half = 1 << k;
        gcd(self.table[k][l], self.table[k][r + 1 - half])
    }
}

fn main() {
    let arr = vec![2i64, 4, 3, 1, 6, 7, 8, 9];
    let st = SparseTable::build_min(&arr);

    println!("=== Sparse Table (Range Min) ===");
    println!("Array: {:?}", arr);
    println!("min(0, 7) = {}", st.query_min(0, 7)); // 1
    println!("min(2, 6) = {}", st.query_min(2, 6)); // 1
    println!("min(4, 7) = {}", st.query_min(4, 7)); // 6

    let arr_gcd = vec![12u64, 8, 6, 4, 2];
    let st_gcd = SparseTableGcd::build(&arr_gcd);
    println!("\n=== Sparse Table (Range GCD) ===");
    println!("gcd(0, 4) = {}", st_gcd.query_gcd(0, 4)); // 2
    println!("gcd(0, 2) = {}", st_gcd.query_gcd(0, 2)); // gcd(12,8,6)=2
}
```

**Why "Sparse"?**  
The table has O(log n) layers, and most entries are unused for any given query. It's "sparse" relative to a full lookup table.

---

## 12. Binary Lifting Transform

### What Is Binary Lifting?

**Binary lifting** (also called **sparse lifting** or **jump pointers**) is a preprocessing transform on trees that enables:
1. Finding the **k-th ancestor** of a node in O(log n)
2. Finding the **Lowest Common Ancestor (LCA)** of two nodes in O(log n)

**Core Transform:**

```
For each node v:
  ancestor[0][v] = parent(v)          ← 2^0 = 1 step up
  ancestor[1][v] = parent(parent(v))  ← 2^1 = 2 steps up
  ancestor[2][v] = 4 steps up
  ...
  ancestor[k][v] = 2^k steps up = ancestor[k-1][ancestor[k-1][v]]
```

**ASCII Visualization:**

```
        Tree:
            1
           / \
          2   3
         / \
        4   5
       /
      6

ancestor[0]: [-, 1, 1, 2, 2, 4]    (direct parents)
ancestor[1]: [-, 0, 0, 1, 1, 2]    (grandparents, 2 steps)
ancestor[2]: [-, 0, 0, 0, 0, 0]    (4 steps — root/above)

To find 3rd ancestor of 6:
  3 = 2 + 1 = 10 in binary
  Step 1: jump 2^1=2 steps: 6 → 4 → 2   (use ancestor[1][6] = 2)
  Step 2: jump 2^0=1 step:  2 → 1        (use ancestor[0][2] = 1)
  Answer: 1 ✓
```

```rust
// ═══════════════════════════════════════════════════════
// BINARY LIFTING TRANSFORM — LCA and K-th Ancestor
// ═══════════════════════════════════════════════════════

const LOG: usize = 18; // supports n up to 2^18 ≈ 262144

struct BinaryLifting {
    /// ancestor[k][v] = 2^k-th ancestor of v
    /// 0 means "root's parent" = invalid/none
    ancestor: Vec<Vec<usize>>,
    /// depth[v] = distance from root (root has depth 0)
    depth: Vec<usize>,
    n: usize,
}

impl BinaryLifting {
    /// FORWARD TRANSFORM: Build binary lifting table.
    /// O(n log n) time and space.
    ///
    /// Input: adjacency list of a tree (0-indexed, root = 0)
    fn build(adj: &[Vec<usize>], root: usize, n: usize) -> Self {
        let mut ancestor = vec![vec![0usize; n]; LOG];
        let mut depth = vec![0usize; n];

        // Step 1: BFS to compute parent (ancestor[0]) and depth
        let mut parent = vec![usize::MAX; n];
        let mut queue = std::collections::VecDeque::new();
        let mut visited = vec![false; n];

        queue.push_back(root);
        visited[root] = true;
        ancestor[0][root] = root; // root's parent is itself (sentinel)

        while let Some(u) = queue.pop_front() {
            for &v in &adj[u] {
                if !visited[v] {
                    visited[v] = true;
                    parent[v] = u;
                    depth[v] = depth[u] + 1;
                    ancestor[0][v] = u;
                    queue.push_back(v);
                }
            }
        }

        // Step 2: Fill binary lifting table (DP)
        // ancestor[k][v] = ancestor[k-1][ancestor[k-1][v]]
        for k in 1..LOG {
            for v in 0..n {
                let mid = ancestor[k - 1][v];
                ancestor[k][v] = ancestor[k - 1][mid];
            }
        }

        BinaryLifting { ancestor, depth, n }
    }

    /// K-TH ANCESTOR QUERY: O(log k)
    /// Returns the k-th ancestor of v (0 = v itself).
    fn kth_ancestor(&self, mut v: usize, mut k: usize) -> Option<usize> {
        if k > self.depth[v] { return None; } // k exceeds tree height
        // Decompose k in binary and jump accordingly
        for bit in 0..LOG {
            if k & (1 << bit) != 0 {
                v = self.ancestor[bit][v];
            }
        }
        Some(v)
    }

    /// LCA QUERY: O(log n)
    /// Returns the Lowest Common Ancestor of u and v.
    ///
    /// Algorithm:
    /// 1. Bring u and v to the same depth
    /// 2. Jump both up simultaneously until they meet
    fn lca(&self, mut u: usize, mut v: usize) -> usize {
        // Step 1: Make depth[u] >= depth[v]
        if self.depth[u] < self.depth[v] {
            std::mem::swap(&mut u, &mut v);
        }

        // Step 2: Lift u up to the same depth as v
        let diff = self.depth[u] - self.depth[v];
        for bit in 0..LOG {
            if diff & (1 << bit) != 0 {
                u = self.ancestor[bit][u];
            }
        }

        // Now depth[u] == depth[v]
        if u == v { return u; } // One is an ancestor of the other

        // Step 3: Binary lift both until just below LCA
        for bit in (0..LOG).rev() {
            if self.ancestor[bit][u] != self.ancestor[bit][v] {
                u = self.ancestor[bit][u];
                v = self.ancestor[bit][v];
            }
        }

        // Now ancestor[0][u] == ancestor[0][v] == LCA
        self.ancestor[0][u]
    }

    /// Distance between two nodes: O(log n)
    fn distance(&self, u: usize, v: usize) -> usize {
        let l = self.lca(u, v);
        self.depth[u] + self.depth[v] - 2 * self.depth[l]
    }
}

fn main() {
    // Build tree:   0─1─3─5
    //                 └─4
    //               └─2
    let n = 6;
    let mut adj = vec![vec![]; n];
    let edges = [(0,1),(0,2),(1,3),(1,4),(3,5)];
    for (u, v) in edges {
        adj[u].push(v);
        adj[v].push(u);
    }

    let bl = BinaryLifting::build(&adj, 0, n);

    println!("=== Binary Lifting Transform ===");
    println!("Depths: {:?}", bl.depth);
    println!("LCA(4, 5) = {}", bl.lca(4, 5));   // 1
    println!("LCA(2, 5) = {}", bl.lca(2, 5));   // 0
    println!("LCA(3, 4) = {}", bl.lca(3, 4));   // 1
    println!("2nd ancestor of 5 = {:?}", bl.kth_ancestor(5, 2)); // Some(0)
    println!("Distance(2, 5) = {}", bl.distance(2, 5)); // 4
}
```

---

## 13. Euler Tour Transform (Tree Flattening)

### What Is an Euler Tour?

The **Euler Tour** (also called **DFS order** or **in/out time**) is a transform that **flattens a tree into an array**. After this transform, subtree queries become range queries!

```
Tree:           0
               /|\
              1  2  3
             / \
            4   5

DFS Order (entry time):
  Visit 0 → entry[0] = 0
  Visit 1 → entry[1] = 1
  Visit 4 → entry[4] = 2
  Exit  4 → exit[4]  = 2
  Visit 5 → entry[5] = 3
  Exit  5 → exit[5]  = 3
  Exit  1 → exit[1]  = 3
  Visit 2 → entry[2] = 4
  Exit  2 → exit[2]  = 4
  Visit 3 → entry[3] = 5
  Exit  3 → exit[3]  = 5
  Exit  0 → exit[0]  = 5

Flattened array (by entry time):
  [0, 1, 4, 5, 2, 3]
   ↑_____________↑   entire tree = range [0, 5]
       ↑_____↑        subtree(1) = range [1, 3]
```

```rust
// ═══════════════════════════════════════════════════════
// EULER TOUR TRANSFORM — Tree to Array
// ═══════════════════════════════════════════════════════

struct EulerTour {
    /// entry[v] = time when DFS first visits v (in-time)
    entry: Vec<usize>,
    /// exit[v] = time when DFS finishes v (out-time)
    exit: Vec<usize>,
    /// order[t] = which node was visited at time t
    order: Vec<usize>,
    n: usize,
}

impl EulerTour {
    /// FORWARD TRANSFORM: O(n)
    /// Maps tree structure to linear array positions.
    fn build(adj: &[Vec<usize>], root: usize, n: usize) -> Self {
        let mut entry = vec![0usize; n];
        let mut exit = vec![0usize; n];
        let mut order = Vec::with_capacity(n);
        let mut timer = 0usize;

        // Iterative DFS to avoid stack overflow on large trees
        // Stack stores (node, parent, visited_children_count)
        let mut stack: Vec<(usize, usize, bool)> = vec![(root, usize::MAX, false)];

        while let Some((v, parent, returning)) = stack.last_mut() {
            let v = *v;
            let parent = *parent;

            if !*returning {
                // First visit: record entry time
                entry[v] = timer;
                order.push(v);
                timer += 1;
                *returning = true;

                // Push children in reverse order (so leftmost child is processed first)
                for &u in adj[v].iter().rev() {
                    if u != parent {
                        stack.push((u, v, false));
                    }
                }
            } else {
                // Check if all children processed
                let all_done = adj[v].iter()
                    .filter(|&&u| u != parent)
                    .all(|&u| entry[u] < timer && exit[u] < timer);
                if all_done {
                    exit[v] = timer - 1;
                    stack.pop();
                } else {
                    break; // Children still being processed
                }
            }
        }

        // Simpler recursive approach for clarity (use with caution on large inputs)
        EulerTour { entry, exit, order, n }
    }

    /// Recursive build (cleaner, but may stack overflow for n > 10^5)
    fn build_recursive(adj: &[Vec<usize>], root: usize, n: usize) -> Self {
        let mut entry = vec![0usize; n];
        let mut exit = vec![0usize; n];
        let mut order = Vec::with_capacity(n);
        let mut timer = 0usize;

        fn dfs(
            v: usize, parent: usize, adj: &[Vec<usize>],
            entry: &mut Vec<usize>, exit: &mut Vec<usize>,
            order: &mut Vec<usize>, timer: &mut usize,
        ) {
            entry[v] = *timer;
            order.push(v);
            *timer += 1;
            for &u in &adj[v] {
                if u != parent {
                    dfs(u, v, adj, entry, exit, order, timer);
                }
            }
            exit[v] = *timer - 1;
        }

        dfs(root, usize::MAX, adj, &mut entry, &mut exit, &mut order, &mut timer);
        EulerTour { entry, exit, order, n }
    }

    /// Is `u` an ancestor of `v`?
    fn is_ancestor(&self, u: usize, v: usize) -> bool {
        self.entry[u] <= self.entry[v] && self.exit[v] <= self.exit[u]
    }

    /// Get the range [l, r] in the flattened array for subtree of v.
    fn subtree_range(&self, v: usize) -> (usize, usize) {
        (self.entry[v], self.exit[v])
    }
}

// ── Application: Subtree Sum Queries ──
// After Euler Tour, subtree[v] = arr[entry[v]..=exit[v]]
// Any range query data structure (BIT, Segment Tree) can answer subtree queries!

fn subtree_sum_demo(adj: &[Vec<usize>], node_values: &[i64], root: usize, n: usize) {
    let tour = EulerTour::build_recursive(adj, root, n);

    // Rearrange node values by DFS order
    let flat: Vec<i64> = tour.order.iter().map(|&v| node_values[v]).collect();
    let ps = PrefixSum::build(&flat);

    println!("DFS order: {:?}", tour.order);
    println!("Flat values: {:?}", flat);

    for v in 0..n {
        let (l, r) = tour.subtree_range(v);
        let sum = ps.query(l, r);
        println!("  subtree_sum({}) = {} (range [{}, {}])", v, sum, l, r);
    }
}

struct PrefixSum { prefix: Vec<i64> }
impl PrefixSum {
    fn build(arr: &[i64]) -> Self {
        let n = arr.len();
        let mut prefix = vec![0i64; n + 1];
        for i in 1..=n { prefix[i] = prefix[i-1] + arr[i-1]; }
        PrefixSum { prefix }
    }
    fn query(&self, l: usize, r: usize) -> i64 {
        self.prefix[r + 1] - self.prefix[l]
    }
}

fn main() {
    //       0(10)
    //      / \
    //    1(5)  2(3)
    //    / \
    //  3(1)  4(2)

    let n = 5;
    let mut adj = vec![vec![]; n];
    let edges = [(0,1),(0,2),(1,3),(1,4)];
    for (u, v) in edges {
        adj[u].push(v);
        adj[v].push(u);
    }
    let node_values = vec![10i64, 5, 3, 1, 2];

    println!("=== Euler Tour Transform ===");
    subtree_sum_demo(&adj, &node_values, 0, n);
}
```

---

## 14. Rolling Hash Transform

### What Is Rolling Hash?

A **rolling hash** transforms a string into a sequence of hash values where the hash of any substring can be computed in O(1) after O(n) preprocessing.

**Core Idea:** Use polynomial hashing:
```
hash(s[0..n]) = s[0]*p^(n-1) + s[1]*p^(n-2) + ... + s[n-1]*p^0  (mod M)
```

Then for substring `s[l..r]`:
```
hash(s[l..=r]) = (prefix_hash[r+1] - prefix_hash[l] * p^(r-l+1)) mod M
```

**Transform Chain:**

```
STRING ──[rolling hash build]──► PREFIX HASHES
                                       │
                                       ▼
                              ──[substring query]──► O(1) hash of any substring
                                                          │
                                                          ▼
                                              ──[compare]──► Pattern matching / LCP
```

```rust
// ═══════════════════════════════════════════════════════
// ROLLING HASH TRANSFORM — O(1) Substring Hashing
// ═══════════════════════════════════════════════════════

/// Double hashing: uses two independent hash functions
/// to reduce collision probability to near zero.
struct RollingHash {
    /// Two sets of prefix hashes for double hashing
    h1: Vec<u64>,
    h2: Vec<u64>,
    /// Precomputed powers of the base
    pw1: Vec<u64>,
    pw2: Vec<u64>,
    n: usize,
}

impl RollingHash {
    // Two different (base, modulus) pairs for double hashing
    const BASE1: u64 = 131;
    const MOD1: u64 = 1_000_000_007;
    const BASE2: u64 = 137;
    const MOD2: u64 = 998_244_353;

    /// FORWARD TRANSFORM: O(n)
    /// Computes prefix hashes for the string.
    fn build(s: &[u8]) -> Self {
        let n = s.len();
        let mut h1 = vec![0u64; n + 1];
        let mut h2 = vec![0u64; n + 1];
        let mut pw1 = vec![1u64; n + 1];
        let mut pw2 = vec![1u64; n + 1];

        for i in 0..n {
            h1[i + 1] = (h1[i] * Self::BASE1 + s[i] as u64) % Self::MOD1;
            h2[i + 1] = (h2[i] * Self::BASE2 + s[i] as u64) % Self::MOD2;
            pw1[i + 1] = pw1[i] * Self::BASE1 % Self::MOD1;
            pw2[i + 1] = pw2[i] * Self::BASE2 % Self::MOD2;
        }

        RollingHash { h1, h2, pw1, pw2, n }
    }

    /// QUERY TRANSFORM: O(1)
    /// Returns (hash1, hash2) of s[l..=r].
    fn hash(&self, l: usize, r: usize) -> (u64, u64) {
        let len = r - l + 1;
        let h1 = (self.h1[r + 1] + Self::MOD1 * Self::MOD1
            - self.h1[l] * self.pw1[len] % Self::MOD1) % Self::MOD1;
        let h2 = (self.h2[r + 1] + Self::MOD2 * Self::MOD2
            - self.h2[l] * self.pw2[len] % Self::MOD2) % Self::MOD2;
        (h1, h2)
    }

    /// Are substrings s[l1..=r1] and s[l2..=r2] equal?
    fn equal(&self, l1: usize, r1: usize, l2: usize, r2: usize) -> bool {
        if r1 - l1 != r2 - l2 { return false; }
        self.hash(l1, r1) == self.hash(l2, r2)
    }

    /// Binary search + rolling hash to find LCP (Longest Common Prefix)
    /// of s[l1..n] and s[l2..n]. O(log n).
    fn lcp(&self, l1: usize, l2: usize) -> usize {
        let max_len = (self.n - l1).min(self.n - l2);
        let mut lo = 0;
        let mut hi = max_len;
        while lo < hi {
            let mid = (lo + hi + 1) / 2;
            if self.equal(l1, l1 + mid - 1, l2, l2 + mid - 1) {
                lo = mid;
            } else {
                hi = mid - 1;
            }
        }
        lo
    }

    /// Find all occurrences of pattern in text: O(n + m) expected.
    fn find_all(&self, pattern: &RollingHash, pat_len: usize) -> Vec<usize> {
        if pat_len > self.n { return vec![]; }
        let pat_hash = pattern.hash(0, pat_len - 1);
        (0..=self.n - pat_len)
            .filter(|&i| self.hash(i, i + pat_len - 1) == pat_hash)
            .collect()
    }
}

fn main() {
    let text = b"abacabadabacaba";
    let pattern = b"abacaba";

    let rh_text = RollingHash::build(text);
    let rh_pat = RollingHash::build(pattern);

    println!("=== Rolling Hash Transform ===");
    println!("Text:    {}", std::str::from_utf8(text).unwrap());
    println!("Pattern: {}", std::str::from_utf8(pattern).unwrap());

    let occurrences = rh_text.find_all(&rh_pat, pattern.len());
    println!("Pattern occurs at indices: {:?}", occurrences); // [0, 8]

    println!("LCP of text[0..] and text[8..] = {}", rh_text.lcp(0, 8)); // 7

    // Test substring equality
    println!("text[0..6] == text[8..14]? {}", rh_text.equal(0, 6, 8, 14)); // true
}
```

---

## 15. Z-Function Transform

### What Is the Z-Function?

The **Z-function** transforms a string `s` into an array `Z` where `Z[i]` is the length of the longest string starting at position `i` that is also a **prefix** of `s`.

```
s =  "aabxaab"
Z =  [7, 1, 0, 0, 3, 1, 0]
      ↑  ↑           ↑
      |  |           └─ "aab" matches prefix of length 3
      |  └─── "a" matches prefix of length 1
      └────── Z[0] = len(s) by definition
```

```rust
// ═══════════════════════════════════════════════════════
// Z-FUNCTION TRANSFORM — Linear String Preprocessing
// ═══════════════════════════════════════════════════════

/// FORWARD TRANSFORM: O(n)
/// Builds the Z-array using the Z-box optimization.
///
/// Z-box [l, r]: the interval of the rightmost Z-box seen so far.
/// A Z-box is a substring that matches a prefix.
/// The optimization avoids redundant comparisons by reusing known Z-values.
fn z_function(s: &[u8]) -> Vec<usize> {
    let n = s.len();
    let mut z = vec![0usize; n];
    z[0] = n; // By definition

    let mut l = 0usize; // Left boundary of current rightmost Z-box
    let mut r = 0usize; // Right boundary (exclusive)

    for i in 1..n {
        if i < r {
            // We're inside the current Z-box.
            // z[i - l] is already known (it's within the prefix we've seen).
            // We can reuse it, but clamp to the Z-box boundary.
            z[i] = (r - i).min(z[i - l]);
        }
        // Now try to extend further (naive extension from known position)
        while i + z[i] < n && s[z[i]] == s[i + z[i]] {
            z[i] += 1;
        }
        // Update the rightmost Z-box if we extended it
        if i + z[i] > r {
            l = i;
            r = i + z[i];
        }
    }
    z
}

/// Application: Pattern matching using Z-function.
/// Create combined string: pattern + "$" + text
/// Any position i in the text part where z[i] = len(pattern) is a match.
fn z_pattern_match(text: &[u8], pattern: &[u8]) -> Vec<usize> {
    let mut combined = pattern.to_vec();
    combined.push(b'$'); // Separator not in alphabet
    combined.extend_from_slice(text);

    let z = z_function(&combined);
    let pat_len = pattern.len();
    let offset = pat_len + 1;

    (0..text.len())
        .filter(|&i| z[i + offset] == pat_len)
        .collect()
}

fn main() {
    let s = b"aabxaabxab";
    let z = z_function(s);
    println!("=== Z-Function Transform ===");
    println!("String: {}", std::str::from_utf8(s).unwrap());
    println!("Z-array: {:?}", z);

    let text = b"ababcabab";
    let pattern = b"abab";
    let matches = z_pattern_match(text, pattern);
    println!("\nPattern '{}' in '{}' at: {:?}",
        std::str::from_utf8(pattern).unwrap(),
        std::str::from_utf8(text).unwrap(),
        matches); // [0, 5]
}
```

---

## 16. KMP Failure Function Transform

### What Is the KMP Failure Function?

The **KMP (Knuth-Morris-Pratt) failure function** transforms a pattern string into an array `fail` where `fail[i]` is the length of the longest proper prefix of `pattern[0..=i]` that is also a suffix.

```
pattern = "AABAAB"
fail    = [0, 1, 0, 1, 2, 3]

fail[4] = 2: "AABAA" has "AA" as longest proper prefix == suffix
             "AA" | BAA  (prefix)
              AAB | AA   (suffix)  — length 2
```

```rust
// ═══════════════════════════════════════════════════════
// KMP FAILURE FUNCTION TRANSFORM + PATTERN MATCHING
// ═══════════════════════════════════════════════════════

/// FORWARD TRANSFORM: Compute failure function. O(m).
/// fail[i] = length of longest proper prefix of pattern[0..=i]
///           that is also a suffix.
fn kmp_build(pattern: &[u8]) -> Vec<usize> {
    let m = pattern.len();
    let mut fail = vec![0usize; m];
    let mut k = 0usize; // Length of current matching prefix-suffix

    for i in 1..m {
        // Walk back until we find a match or reach the start
        while k > 0 && pattern[k] != pattern[i] {
            k = fail[k - 1]; // Use previously computed fail values
        }
        if pattern[k] == pattern[i] {
            k += 1;
        }
        fail[i] = k;
    }
    fail
}

/// SEARCH TRANSFORM: Find all pattern occurrences in text. O(n + m).
fn kmp_search(text: &[u8], pattern: &[u8]) -> Vec<usize> {
    if pattern.is_empty() { return vec![]; }
    let fail = kmp_build(pattern);
    let mut matches = Vec::new();
    let mut k = 0usize; // Number of characters matched so far

    for (i, &c) in text.iter().enumerate() {
        while k > 0 && pattern[k] != c {
            k = fail[k - 1]; // Fall back using failure function
        }
        if pattern[k] == c {
            k += 1;
        }
        if k == pattern.len() {
            matches.push(i + 1 - pattern.len()); // Match ending at i
            k = fail[k - 1]; // Prepare for next match
        }
    }
    matches
}

/// Count occurrences of pattern as a substring of text, including overlaps.
fn count_occurrences(text: &[u8], pattern: &[u8]) -> usize {
    kmp_search(text, pattern).len()
}

fn main() {
    let text = b"AABAACAADAABAABA";
    let pattern = b"AABA";
    let fail = kmp_build(pattern);

    println!("=== KMP Transform ===");
    println!("Pattern: {}", std::str::from_utf8(pattern).unwrap());
    println!("Failure: {:?}", fail);
    println!("Text: {}", std::str::from_utf8(text).unwrap());
    println!("Matches at: {:?}", kmp_search(text, pattern)); // [0, 9, 12]
}
```

---

## 17. Suffix Array Transform

### What Is a Suffix Array?

A **suffix array** is the sorted order of all suffixes of a string. It is perhaps the most powerful string transform in competitive programming.

```
s = "banana"
Suffixes (index, suffix):
  0: "banana"
  1: "anana"
  2: "nana"
  3: "ana"
  4: "na"
  5: "a"

Sorted:
  5: "a"
  3: "ana"
  1: "anana"
  0: "banana"
  4: "na"
  2: "nana"

Suffix Array SA = [5, 3, 1, 0, 4, 2]
```

```rust
// ═══════════════════════════════════════════════════════
// SUFFIX ARRAY TRANSFORM — O(n log n) via Prefix Doubling
// ═══════════════════════════════════════════════════════

/// Builds the suffix array using O(n log n) prefix doubling.
/// Returns SA where SA[i] = starting index of i-th lexicographically smallest suffix.
fn build_suffix_array(s: &[u8]) -> Vec<usize> {
    let n = s.len();
    if n == 0 { return vec![]; }
    if n == 1 { return vec![0]; }

    // Initial rank: based on single character
    let mut sa: Vec<usize> = (0..n).collect();
    let mut rank: Vec<i64> = s.iter().map(|&c| c as i64).collect();
    let mut tmp = vec![0i64; n];

    let mut k = 1;
    while k < n {
        // Sort by (rank[i], rank[i + k])
        let rank_ref = &rank;
        let k_ref = k;
        sa.sort_by(|&a, &b| {
            let ra = (rank_ref[a], if a + k_ref < n { rank_ref[a + k_ref] } else { -1 });
            let rb = (rank_ref[b], if b + k_ref < n { rank_ref[b + k_ref] } else { -1 });
            ra.cmp(&rb)
        });

        // Recompute ranks
        tmp[sa[0]] = 0;
        for i in 1..n {
            let prev = sa[i - 1];
            let curr = sa[i];
            let ra_prev = (rank[prev], if prev + k < n { rank[prev + k] } else { -1 });
            let ra_curr = (rank[curr], if curr + k < n { rank[curr + k] } else { -1 });
            tmp[curr] = tmp[prev] + if ra_curr == ra_prev { 0 } else { 1 };
        }
        rank = tmp.clone();

        if rank[sa[n - 1]] == (n - 1) as i64 { break; } // All ranks distinct
        k *= 2;
    }
    sa
}

/// Build LCP array using Kasai's algorithm.
/// LCP[i] = length of longest common prefix between SA[i] and SA[i-1].
/// O(n) time.
///
/// Why LCP? It enables: longest repeated substring, number of distinct substrings,
/// string searching, and more — all by combining SA + LCP.
fn build_lcp_array(s: &[u8], sa: &[usize]) -> Vec<usize> {
    let n = s.len();
    let mut rank = vec![0usize; n]; // Inverse suffix array
    for (i, &sai) in sa.iter().enumerate() {
        rank[sai] = i;
    }

    let mut lcp = vec![0usize; n];
    let mut h = 0usize; // Current LCP length

    for i in 0..n {
        if rank[i] > 0 {
            let j = sa[rank[i] - 1]; // Previous suffix in sorted order
            // Extend match (Kasai's key insight: h can only decrease by 1 per step)
            while i + h < n && j + h < n && s[i + h] == s[j + h] {
                h += 1;
            }
            lcp[rank[i]] = h;
            if h > 0 { h -= 1; } // Key: h decreases by at most 1
        }
    }
    lcp
}

/// Count distinct substrings using SA + LCP.
/// Total substrings = n*(n+1)/2
/// Subtract LCP values (these are shared prefixes — duplicates).
fn count_distinct_substrings(s: &[u8]) -> u64 {
    let n = s.len();
    let sa = build_suffix_array(s);
    let lcp = build_lcp_array(s, &sa);
    let total = (n * (n + 1) / 2) as u64;
    let duplicates: u64 = lcp.iter().map(|&l| l as u64).sum();
    total - duplicates
}

fn main() {
    let s = b"banana";
    let sa = build_suffix_array(s);
    let lcp = build_lcp_array(s, &sa);

    println!("=== Suffix Array Transform ===");
    println!("String: {}", std::str::from_utf8(s).unwrap());
    println!("SA: {:?}", sa);  // [5, 3, 1, 0, 4, 2]
    println!("LCP: {:?}", lcp); // [0, 1, 3, 0, 0, 2]
    println!("Distinct substrings: {}", count_distinct_substrings(s)); // 15

    // Print all suffixes in sorted order
    println!("\nSorted suffixes:");
    for (i, &idx) in sa.iter().enumerate() {
        println!("  SA[{}]={}: \"{}\"  LCP={}",
            i, idx,
            std::str::from_utf8(&s[idx..]).unwrap(),
            lcp[i]);
    }
}
```

---

## 18. Monotonic Stack Transform

### What Is a Monotonic Stack?

A **monotonic stack** is a stack that maintains elements in either strictly increasing or strictly decreasing order. It transforms an array by computing, for each element, a relationship to the **nearest element that is smaller or larger** than it.

**Classic Problems Solved:**
- Next Greater Element (NGE)
- Previous Smaller Element (PSE)
- Largest Rectangle in Histogram
- Maximum area of subarray where all elements ≥ threshold

```
Array:  [3, 1, 4, 1, 5, 9, 2, 6]

Next Greater Element:
  3 → 4 (index 2)
  1 → 4 (index 2)
  4 → 5 (index 4)
  1 → 5 (index 4)
  5 → 9 (index 5)
  9 → -1 (none)
  2 → 6 (index 7)
  6 → -1 (none)

Stack State Trace (for NGE, left to right):
  Process 3: stack=[3(0)]
  Process 1: stack=[3(0),1(1)]
  Process 4: 4>1→pop 1→NGE[1]=4, 4>3→pop 3→NGE[0]=4. stack=[4(2)]
  Process 1: stack=[4(2),1(3)]
  Process 5: 5>1→pop→NGE[3]=5, 5>4→pop→NGE[2]=5. stack=[5(4)]
  Process 9: 9>5→pop→NGE[4]=9. stack=[9(5)]
  Process 2: stack=[9(5),2(6)]
  Process 6: 6>2→pop→NGE[6]=6. stack=[9(5),6(7)]
  End: NGE[5]=-1, NGE[7]=-1
```

```rust
// ═══════════════════════════════════════════════════════
// MONOTONIC STACK TRANSFORM — Complete Suite
// ═══════════════════════════════════════════════════════

/// TRANSFORM: Next Greater Element for each index.
/// Returns array where result[i] = index of next greater element,
/// or n if none exists.
/// O(n) — each element pushed/popped at most once.
fn next_greater_element(arr: &[i64]) -> Vec<usize> {
    let n = arr.len();
    let mut result = vec![n; n]; // Default: no greater element
    let mut stack: Vec<usize> = Vec::new(); // Stack of indices (decreasing values)

    for i in 0..n {
        // Pop all elements smaller than current — their NGE is i
        while let Some(&top) = stack.last() {
            if arr[top] < arr[i] {
                result[top] = i;
                stack.pop();
            } else {
                break;
            }
        }
        stack.push(i);
    }
    result
}

/// TRANSFORM: Previous Smaller Element for each index.
/// Returns array where result[i] = index of previous smaller element,
/// or n (sentinel for "none") if none exists.
fn previous_smaller_element(arr: &[i64]) -> Vec<usize> {
    let n = arr.len();
    let mut result = vec![n; n];
    let mut stack: Vec<usize> = Vec::new(); // Indices with increasing values

    for i in 0..n {
        while let Some(&top) = stack.last() {
            if arr[top] >= arr[i] {
                stack.pop();
            } else {
                break;
            }
        }
        result[i] = stack.last().copied().unwrap_or(n); // n = sentinel for "none"
        stack.push(i);
    }
    result
}

/// TRANSFORM: For each element, find its "domain" —
/// the range [left, right] where it is the minimum.
/// This is the core of histogram rectangle problems.
fn compute_dominance_ranges(arr: &[i64]) -> Vec<(usize, usize)> {
    let n = arr.len();
    let pse = previous_smaller_element(arr); // Left boundary
    let nse: Vec<usize> = { // Next Smaller or Equal Element
        let mut result = vec![n; n];
        let mut stack: Vec<usize> = Vec::new();
        for i in 0..n {
            while let Some(&top) = stack.last() {
                if arr[top] > arr[i] {
                    result[top] = i;
                    stack.pop();
                } else { break; }
            }
            stack.push(i);
        }
        result
    };

    (0..n).map(|i| {
        let left = if pse[i] == n { 0 } else { pse[i] + 1 };
        let right = nse[i] - 1; // nse[i] = n means extends to end
        (left, right)
    }).collect()
}

/// CLASSIC PROBLEM: Largest Rectangle in Histogram.
/// For each bar i, find max rectangle where bar i is the minimum height.
/// Use PSE and NSE to find the width for each bar.
/// Time: O(n), Space: O(n)
fn largest_rectangle_histogram(heights: &[i64]) -> i64 {
    let n = heights.len();
    let ranges = compute_dominance_ranges(heights);

    ranges.iter().enumerate().map(|(i, &(l, r))| {
        let width = (r - l + 1) as i64;
        heights[i] * width
    }).max().unwrap_or(0)
}

/// TRANSFORM: Stock Span Problem
/// For each day i, find the number of consecutive days before i
/// (including i) where the stock price was ≤ price[i].
fn stock_span(prices: &[i64]) -> Vec<usize> {
    let n = prices.len();
    let mut spans = vec![1usize; n];
    let mut stack: Vec<usize> = Vec::new(); // Indices of "blocking" elements

    for i in 0..n {
        while let Some(&top) = stack.last() {
            if prices[top] <= prices[i] {
                stack.pop();
            } else {
                break;
            }
        }
        spans[i] = if stack.is_empty() { i + 1 } else { i - stack.last().unwrap() };
        stack.push(i);
    }
    spans
}

fn main() {
    let arr = vec![3i64, 1, 4, 1, 5, 9, 2, 6];
    println!("=== Monotonic Stack Transforms ===");
    println!("Array: {:?}", arr);

    let nge = next_greater_element(&arr);
    println!("Next Greater (index): {:?}", nge);

    let pse = previous_smaller_element(&arr);
    println!("Prev Smaller (index): {:?}", pse);

    let heights = vec![2i64, 1, 5, 6, 2, 3];
    println!("\n=== Largest Rectangle in Histogram ===");
    println!("Heights: {:?}", heights);
    println!("Max area: {}", largest_rectangle_histogram(&heights)); // 10

    let prices = vec![100i64, 80, 60, 70, 60, 75, 85];
    println!("\n=== Stock Span ===");
    println!("Prices: {:?}", prices);
    println!("Spans:  {:?}", stock_span(&prices)); // [1, 1, 1, 2, 1, 4, 6]
}
```

---

## 19. Monotonic Deque Transform (Sliding Window)

### What Is a Monotonic Deque?

A **monotonic deque** (double-ended queue) extends the monotonic stack to handle **sliding window** problems: maintain the minimum or maximum over a moving window of fixed size k.

```
Array:   [1, 3, -1, -3, 5, 3, 6, 7]   k = 3
Windows: [1,3,-1]  → min=-1, max=3
         [3,-1,-3] → min=-3, max=3
         [-1,-3,5] → min=-3, max=5
         [-3,5,3]  → min=-3, max=5
         [5,3,6]   → min=3,  max=6
         [3,6,7]   → min=3,  max=7

Deque state trace (max, front=maximum side):
Add 1:  deque=[0]
Add 3:  3>1→pop 0. deque=[1]
Add -1: deque=[1,2]. Window=[0,2]: max=arr[1]=3
Add -3: deque=[1,2,3]. Window=[1,3]: max=arr[1]=3
Add 5:  5>-3→pop, 5>-1→pop, 5>3→pop. deque=[4]. Window=[2,4]: max=5
...
```

```rust
// ═══════════════════════════════════════════════════════
// MONOTONIC DEQUE TRANSFORM — Sliding Window Min/Max
// ═══════════════════════════════════════════════════════

use std::collections::VecDeque;

/// TRANSFORM: Sliding window maximum. O(n).
/// Returns array of max values for each window of size k.
/// result[i] = max(arr[i..i+k]) for i in 0..=n-k
fn sliding_window_max(arr: &[i64], k: usize) -> Vec<i64> {
    let n = arr.len();
    if k == 0 || k > n { return vec![]; }

    let mut result = Vec::with_capacity(n - k + 1);
    let mut deque: VecDeque<usize> = VecDeque::new(); // Stores indices, front = max

    for i in 0..n {
        // Remove elements outside the window (expired)
        while let Some(&front) = deque.front() {
            if front + k <= i { deque.pop_front(); } else { break; }
        }
        // Remove elements from back that are smaller than current
        // (they can never be the maximum of any future window)
        while let Some(&back) = deque.back() {
            if arr[back] <= arr[i] { deque.pop_back(); } else { break; }
        }
        deque.push_back(i);

        // Window is complete
        if i + 1 >= k {
            result.push(arr[*deque.front().unwrap()]);
        }
    }
    result
}

/// TRANSFORM: Sliding window minimum. O(n).
fn sliding_window_min(arr: &[i64], k: usize) -> Vec<i64> {
    let n = arr.len();
    if k == 0 || k > n { return vec![]; }

    let mut result = Vec::with_capacity(n - k + 1);
    let mut deque: VecDeque<usize> = VecDeque::new(); // Front = minimum

    for i in 0..n {
        while let Some(&front) = deque.front() {
            if front + k <= i { deque.pop_front(); } else { break; }
        }
        while let Some(&back) = deque.back() {
            if arr[back] >= arr[i] { deque.pop_back(); } else { break; }
        }
        deque.push_back(i);
        if i + 1 >= k {
            result.push(arr[*deque.front().unwrap()]);
        }
    }
    result
}

/// PROBLEM: Longest subarray where max - min ≤ limit.
/// Uses two monotonic deques simultaneously. O(n).
fn longest_subarray_with_limit(arr: &[i64], limit: i64) -> usize {
    let mut max_dq: VecDeque<usize> = VecDeque::new(); // Front = window max
    let mut min_dq: VecDeque<usize> = VecDeque::new(); // Front = window min
    let mut left = 0usize;
    let mut best = 0usize;

    for right in 0..arr.len() {
        // Maintain max deque
        while let Some(&back) = max_dq.back() {
            if arr[back] <= arr[right] { max_dq.pop_back(); } else { break; }
        }
        max_dq.push_back(right);

        // Maintain min deque
        while let Some(&back) = min_dq.back() {
            if arr[back] >= arr[right] { min_dq.pop_back(); } else { break; }
        }
        min_dq.push_back(right);

        // Shrink window if constraint violated
        while arr[*max_dq.front().unwrap()] - arr[*min_dq.front().unwrap()] > limit {
            left += 1;
            if max_dq.front() == Some(&(left - 1)) { max_dq.pop_front(); }
            if min_dq.front() == Some(&(left - 1)) { min_dq.pop_front(); }
        }
        best = best.max(right - left + 1);
    }
    best
}

fn main() {
    let arr = vec![1i64, 3, -1, -3, 5, 3, 6, 7];
    let k = 3;
    println!("=== Sliding Window Transform ===");
    println!("Array: {:?}", arr);
    println!("Window size: {}", k);
    println!("Sliding max: {:?}", sliding_window_max(&arr, k));
    println!("Sliding min: {:?}", sliding_window_min(&arr, k));

    let arr2 = vec![8i64, 2, 4, 7];
    println!("\nLongest subarray with limit 4: {}", longest_subarray_with_limit(&arr2, 4)); // 2
}
```

---

## 20. Bit Manipulation Transform Chains

### Concept

Bit manipulation transforms operate at the level of binary representation, enabling very fast operations.

**Key Vocabulary:**

| Term | Meaning | Bit Op |
|---|---|---|
| **Set bit k** | Turn bit k on | `x \| (1 << k)` |
| **Clear bit k** | Turn bit k off | `x & !(1 << k)` |
| **Toggle bit k** | Flip bit k | `x ^ (1 << k)` |
| **Check bit k** | Is bit k set? | `(x >> k) & 1` |
| **LSB** | Lowest set bit | `x & x.wrapping_neg()` |
| **Popcount** | Count of 1-bits | `x.count_ones()` |

```rust
// ═══════════════════════════════════════════════════════
// BIT MANIPULATION TRANSFORM CHAINS
// ═══════════════════════════════════════════════════════

/// Transform: Enumerate all subsets of a set (bitmask).
/// Critical for bitmask DP.
/// Time: O(2^n), where n = number of bits.
fn enumerate_subsets(mask: u32) -> Vec<u32> {
    let mut subsets = Vec::new();
    let mut sub = mask;
    loop {
        subsets.push(sub);
        if sub == 0 { break; }
        sub = (sub - 1) & mask; // Next smaller subset
    }
    subsets
}

/// Transform: Sum Over Subsets (SOS DP).
/// Computes for each mask: f[mask] = sum of a[sub] for all sub ⊆ mask.
/// Time: O(n * 2^n) where n = number of bits.
///
/// This is a transform over the boolean lattice — very powerful!
fn sum_over_subsets(a: &[i64]) -> Vec<i64> {
    let n = a.len(); // Must be power of 2: n = 2^bits
    let bits = n.trailing_zeros() as usize; // How many bits
    let mut dp = a.to_vec();

    // For each bit position, "spread" contributions upward
    for bit in 0..bits {
        for mask in 0..n {
            if mask & (1 << bit) != 0 {
                // mask has bit `bit` set.
                // dp[mask] += dp[mask without bit `bit`]
                dp[mask] += dp[mask ^ (1 << bit)];
            }
        }
    }
    dp
}

/// Transform: Zeta Transform (general SOS).
/// For each mask, compute union over all subsets.
fn zeta_transform(a: &[i64]) -> Vec<i64> {
    sum_over_subsets(a) // SOS is the zeta transform on subsets
}

/// Transform: Mobius Inversion (inverse of SOS).
/// Recovers original array from SOS result.
fn mobius_inversion(f: &[i64]) -> Vec<i64> {
    let n = f.len();
    let bits = n.trailing_zeros() as usize;
    let mut a = f.to_vec();
    for bit in 0..bits {
        for mask in 0..n {
            if mask & (1 << bit) != 0 {
                a[mask] -= a[mask ^ (1 << bit)];
            }
        }
    }
    a
}

/// Transform: Gray Code
/// Converts integer i to its Gray code representation.
/// Adjacent Gray codes differ by exactly 1 bit.
/// Used in error correction and circuit design.
fn to_gray_code(n: u32) -> u32 {
    n ^ (n >> 1)
}

fn from_gray_code(mut g: u32) -> u32 {
    let mut n = g;
    while g > 0 {
        g >>= 1;
        n ^= g;
    }
    n
}

fn main() {
    // ── Subset Enumeration ──
    let mask = 0b1011u32; // bits 0, 1, 3
    println!("=== Bit Transform Chains ===");
    println!("Subsets of {:04b}: {:?}",
        mask,
        enumerate_subsets(mask).iter().map(|&s| format!("{:04b}", s)).collect::<Vec<_>>()
    );

    // ── Sum Over Subsets ──
    let a = vec![1i64, 2, 3, 4, 5, 6, 7, 8]; // 8 = 2^3, so 3-bit masks
    let sos = sum_over_subsets(&a);
    println!("\nSOS Transform:");
    for (mask, &val) in sos.iter().enumerate() {
        println!("  f[{:03b}] = {}", mask, val);
    }

    // Verify inverse
    let recovered = mobius_inversion(&sos);
    println!("Recovered (Mobius): {:?}", recovered);
    assert_eq!(recovered, a);

    // ── Gray Code ──
    println!("\nGray Code Transform:");
    for i in 0..8u32 {
        println!("  {} → {:03b}", i, to_gray_code(i));
    }
}
```

---

## 21. Segment Tree Lazy Propagation (Deferred Transform)

### What Is Lazy Propagation?

**Lazy propagation** is a technique where you **defer** (delay) a transform on a segment tree node's children until they are actually needed. This enables range updates in O(log n) instead of O(n).

**The Key Insight:** When you update a range, you don't immediately update all affected leaf nodes. Instead, you store a "pending transform" (the **lazy tag**) at the highest possible node. When you need to query a child, you **push down** the lazy tag.

```
LAZY PROPAGATION MENTAL MODEL:

Node stores:
  - value: the result of the transform for this range
  - lazy: a PENDING transform waiting to be pushed to children

When we query/update and need to go deeper:
  1. Push the lazy tag down to both children
  2. Proceed with query/update

Push Down:
  child.value = apply(child.value, parent.lazy)
  child.lazy  = compose(child.lazy, parent.lazy)
  parent.lazy = identity (clear it)
```

```rust
// ═══════════════════════════════════════════════════════
// SEGMENT TREE WITH LAZY PROPAGATION
// Supports: Range Add, Range Sum Query
// ═══════════════════════════════════════════════════════

struct LazySegTree {
    /// Segment values (sum in this case)
    tree: Vec<i64>,
    /// Lazy tags: pending additions
    lazy: Vec<i64>,
    n: usize,
}

impl LazySegTree {
    /// BUILD TRANSFORM: O(n)
    fn build(arr: &[i64]) -> Self {
        let n = arr.len();
        let size = 4 * n;
        let mut seg = LazySegTree {
            tree: vec![0; size],
            lazy: vec![0; size],
            n,
        };
        if n > 0 {
            seg.build_recursive(arr, 1, 0, n - 1);
        }
        seg
    }

    fn build_recursive(&mut self, arr: &[i64], node: usize, l: usize, r: usize) {
        if l == r {
            self.tree[node] = arr[l];
            return;
        }
        let mid = (l + r) / 2;
        self.build_recursive(arr, 2 * node, l, mid);
        self.build_recursive(arr, 2 * node + 1, mid + 1, r);
        self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1];
    }

    /// PUSH DOWN: Propagate lazy tag to children.
    /// This is the core of deferred transforms.
    fn push_down(&mut self, node: usize, l: usize, r: usize) {
        if self.lazy[node] != 0 {
            let mid = (l + r) / 2;
            let left_len = (mid - l + 1) as i64;
            let right_len = (r - mid) as i64;

            // Apply lazy to left child
            self.tree[2 * node] += self.lazy[node] * left_len;
            self.lazy[2 * node] += self.lazy[node];

            // Apply lazy to right child
            self.tree[2 * node + 1] += self.lazy[node] * right_len;
            self.lazy[2 * node + 1] += self.lazy[node];

            // Clear parent lazy
            self.lazy[node] = 0;
        }
    }

    /// RANGE UPDATE TRANSFORM: O(log n)
    /// Add val to all elements in [ql, qr].
    pub fn update(&mut self, ql: usize, qr: usize, val: i64) {
        self.update_recursive(1, 0, self.n - 1, ql, qr, val);
    }

    fn update_recursive(&mut self, node: usize, l: usize, r: usize,
                        ql: usize, qr: usize, val: i64) {
        if ql > r || qr < l { return; } // No overlap

        if ql <= l && r <= qr {
            // Complete overlap: apply transform here, defer children
            self.tree[node] += val * (r - l + 1) as i64;
            self.lazy[node] += val;
            return;
        }

        // Partial overlap: push down before going deeper
        self.push_down(node, l, r);
        let mid = (l + r) / 2;
        self.update_recursive(2 * node, l, mid, ql, qr, val);
        self.update_recursive(2 * node + 1, mid + 1, r, ql, qr, val);
        self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1];
    }

    /// RANGE QUERY TRANSFORM: O(log n)
    /// Returns sum of arr[ql..=qr].
    pub fn query(&mut self, ql: usize, qr: usize) -> i64 {
        self.query_recursive(1, 0, self.n - 1, ql, qr)
    }

    fn query_recursive(&mut self, node: usize, l: usize, r: usize,
                       ql: usize, qr: usize) -> i64 {
        if ql > r || qr < l { return 0; }
        if ql <= l && r <= qr { return self.tree[node]; }
        self.push_down(node, l, r);
        let mid = (l + r) / 2;
        self.query_recursive(2 * node, l, mid, ql, qr)
            + self.query_recursive(2 * node + 1, mid + 1, r, ql, qr)
    }
}

fn main() {
    let arr = vec![1i64, 2, 3, 4, 5];
    let mut seg = LazySegTree::build(&arr);

    println!("=== Lazy Segment Tree Transform ===");
    println!("Initial sum(0,4) = {}", seg.query(0, 4)); // 15
    seg.update(1, 3, 10); // Add 10 to indices 1, 2, 3
    println!("After update(1,3,+10):");
    println!("  sum(0,4) = {}", seg.query(0, 4)); // 45
    println!("  sum(1,3) = {}", seg.query(1, 3)); // 39
    println!("  sum(0,0) = {}", seg.query(0, 0)); // 1
}
```

---

## 22. Square Root Decomposition Transform

### What Is sqrt Decomposition?

**sqrt decomposition** divides an array of n elements into blocks of size √n. It's a "middle ground" transform: not as fast as segment tree (O(log n)) but simpler to implement, supports more complex operations.

```
Array (n=16, block_size=4):
Block 0: [arr[0], arr[1],  arr[2],  arr[3] ]  ← block_sum[0]
Block 1: [arr[4], arr[5],  arr[6],  arr[7] ]  ← block_sum[1]
Block 2: [arr[8], arr[9],  arr[10], arr[11]]  ← block_sum[2]
Block 3: [arr[12],arr[13], arr[14], arr[15]]  ← block_sum[3]

Range query [2, 13]:
  Partial block 0: arr[2] + arr[3]       → individual elements
  Full block 1:    block_sum[1]           → O(1) per block
  Full block 2:    block_sum[2]           → O(1) per block
  Partial block 3: arr[12] + arr[13]     → individual elements
  Total: O(√n) per query
```

```rust
// ═══════════════════════════════════════════════════════
// SQRT DECOMPOSITION TRANSFORM
// ═══════════════════════════════════════════════════════

struct SqrtDecomposition {
    arr: Vec<i64>,
    block_sum: Vec<i64>,
    block_size: usize,
    n: usize,
}

impl SqrtDecomposition {
    /// BUILD TRANSFORM: O(n)
    fn build(arr: &[i64]) -> Self {
        let n = arr.len();
        let block_size = ((n as f64).sqrt().ceil() as usize).max(1);
        let num_blocks = (n + block_size - 1) / block_size;
        let mut block_sum = vec![0i64; num_blocks];

        for (i, &v) in arr.iter().enumerate() {
            block_sum[i / block_size] += v;
        }

        SqrtDecomposition {
            arr: arr.to_vec(),
            block_sum,
            block_size,
            n,
        }
    }

    /// POINT UPDATE: O(1)
    fn update(&mut self, i: usize, new_val: i64) {
        let block = i / self.block_size;
        self.block_sum[block] += new_val - self.arr[i];
        self.arr[i] = new_val;
    }

    /// RANGE ADD: O(√n)
    fn range_add(&mut self, l: usize, r: usize, val: i64) {
        let bl = l / self.block_size;
        let br = r / self.block_size;

        if bl == br {
            // Same block: update individual elements
            for i in l..=r {
                self.arr[i] += val;
            }
            self.block_sum[bl] += val * (r - l + 1) as i64;
        } else {
            // Left partial block
            let left_end = (bl + 1) * self.block_size - 1;
            for i in l..=left_end {
                self.arr[i] += val;
            }
            self.block_sum[bl] += val * (left_end - l + 1) as i64;

            // Full blocks in between
            for b in (bl + 1)..br {
                self.block_sum[b] += val * self.block_size as i64;
                // Note: we'd need lazy array for full correctness with queries
                // For simplicity here we update arr too
                for i in (b * self.block_size)..((b + 1) * self.block_size).min(self.n) {
                    self.arr[i] += val;
                }
            }

            // Right partial block
            let right_start = br * self.block_size;
            for i in right_start..=r {
                self.arr[i] += val;
            }
            self.block_sum[br] += val * (r - right_start + 1) as i64;
        }
    }

    /// RANGE QUERY: O(√n)
    fn query(&self, l: usize, r: usize) -> i64 {
        let bl = l / self.block_size;
        let br = r / self.block_size;
        let mut sum = 0i64;

        if bl == br {
            // Same block: sum individual elements
            sum = self.arr[l..=r].iter().sum();
        } else {
            // Left partial block
            let left_end = (bl + 1) * self.block_size - 1;
            sum += self.arr[l..=left_end].iter().sum::<i64>();

            // Full blocks
            for b in (bl + 1)..br {
                sum += self.block_sum[b];
            }

            // Right partial block
            let right_start = br * self.block_size;
            sum += self.arr[right_start..=r].iter().sum::<i64>();
        }
        sum
    }
}

fn main() {
    let arr = vec![1i64, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16];
    let mut sq = SqrtDecomposition::build(&arr);

    println!("=== Sqrt Decomposition Transform ===");
    println!("Block size: {}", sq.block_size);
    println!("query(2, 13) = {}", sq.query(2, 13)); // 3+4+...+14 = 102
    sq.update(5, 100);
    println!("After update(5, 100):");
    println!("query(4, 6) = {}", sq.query(4, 6)); // 5+100+7 = 112
}
```

---

## 23. Dynamic Programming as a Transformation Chain

### The DP Lens

Every DP is a **transformation chain** on states:

```
INITIAL STATE → [Transform 1] → [Transform 2] → ... → [Transform n] → FINAL STATE
```

The DP recurrence IS the transform. Each `dp[i]` is computed from previous states using a specific transform function.

```
dp[0] = base case
dp[i] = transform(dp[i-1], dp[i-2], ..., input[i])
```

```rust
// ═══════════════════════════════════════════════════════
// DP AS TRANSFORMATION CHAINS
// ═══════════════════════════════════════════════════════

// ── Transform 1: Longest Increasing Subsequence (LIS) ──
// State: dp[i] = length of LIS ending at index i
// Transform: dp[i] = 1 + max(dp[j]) for all j < i where arr[j] < arr[i]
//
// O(n log n) version using patience sorting (BIT-based binary search transform)

fn lis_length(arr: &[i64]) -> usize {
    // tails[i] = smallest tail element of all increasing subsequences of length i+1
    // This is the key transform: maintain the invariant that tails is sorted.
    let mut tails: Vec<i64> = Vec::new();

    for &x in arr {
        // Binary search: find first tail >= x
        let pos = tails.partition_point(|&t| t < x);
        if pos == tails.len() {
            tails.push(x); // Extend LIS by 1
        } else {
            tails[pos] = x; // Replace: maintain smallest possible tail
        }
    }
    tails.len()
}

// ── Transform 2: Knapsack (Set Transform) ──
// State: dp[w] = max value achievable with weight capacity w
// Transform: dp[w] = max(dp[w], dp[w - weight[i]] + value[i])
//
// This is a "reachability" transform over the weight space.

fn knapsack_01(weights: &[usize], values: &[i64], capacity: usize) -> i64 {
    let mut dp = vec![0i64; capacity + 1];

    for (&w, &v) in weights.iter().zip(values.iter()) {
        // Iterate backward to prevent using same item twice (0/1 knapsack)
        for cap in (w..=capacity).rev() {
            dp[cap] = dp[cap].max(dp[cap - w] + v);
        }
    }
    dp[capacity]
}

// ── Transform 3: Edit Distance (2D State Transform) ──
// dp[i][j] = min edits to transform s[0..i] into t[0..j]
// Transform:
//   if s[i-1] == t[j-1]: dp[i][j] = dp[i-1][j-1]
//   else: dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
//                         (delete, insert, replace)

fn edit_distance(s: &[u8], t: &[u8]) -> usize {
    let (m, n) = (s.len(), t.len());
    // Space-optimized: only keep two rows
    let mut prev: Vec<usize> = (0..=n).collect();
    let mut curr = vec![0usize; n + 1];

    for i in 1..=m {
        curr[0] = i; // Delete i characters from s
        for j in 1..=n {
            curr[j] = if s[i - 1] == t[j - 1] {
                prev[j - 1]
            } else {
                1 + prev[j].min(curr[j - 1]).min(prev[j - 1])
            };
        }
        std::mem::swap(&mut prev, &mut curr);
    }
    prev[n]
}

// ── Transform 4: Matrix Chain Multiplication (Interval DP) ──
// dp[i][j] = min cost to multiply matrices i through j
// Transform: dp[i][j] = min over k of (dp[i][k] + dp[k+1][j] + cost(i,k,j))
// This is an "interval merge" transform.

fn matrix_chain_order(dims: &[usize]) -> usize {
    let n = dims.len() - 1; // Number of matrices
    let mut dp = vec![vec![0usize; n]; n];

    // Length 1: single matrix, cost 0 (base case)
    // Length l: try all split points
    for len in 2..=n {
        for i in 0..=n - len {
            let j = i + len - 1;
            dp[i][j] = usize::MAX;
            for k in i..j {
                // Cost of (A_i * ... * A_k) * (A_{k+1} * ... * A_j)
                let cost = dp[i][k] + dp[k+1][j] + dims[i] * dims[k+1] * dims[j+1];
                dp[i][j] = dp[i][j].min(cost);
            }
        }
    }
    dp[0][n - 1]
}

fn main() {
    println!("=== DP Transformation Chains ===");

    let arr = vec![10i64, 9, 2, 5, 3, 7, 101, 18];
    println!("LIS of {:?} = {}", arr, lis_length(&arr)); // 4: [2,3,7,101]

    let weights = vec![1usize, 3, 4, 5];
    let values = vec![1i64, 4, 5, 7];
    println!("Knapsack(capacity=7) = {}", knapsack_01(&weights, &values, 7)); // 9

    println!("Edit distance('horse','ros') = {}",
        edit_distance(b"horse", b"ros")); // 3

    let dims = vec![10usize, 30, 5, 60]; // 3 matrices: 10x30, 30x5, 5x60
    println!("Matrix chain order cost = {}", matrix_chain_order(&dims)); // 4500
}
```

---

## 24. Graph Transformation Chains

### Concept

Graph transforms preprocess graph structure to enable faster queries.

```rust
// ═══════════════════════════════════════════════════════
// GRAPH TRANSFORMATION CHAINS
// ═══════════════════════════════════════════════════════

// ── Transform 1: BFS Distance Layer Transform ──
// Converts graph into "distance layers" from a source.
// Each node's distance is its transform value.

fn bfs_distances(adj: &[Vec<usize>], src: usize) -> Vec<Option<usize>> {
    let n = adj.len();
    let mut dist = vec![None; n];
    let mut queue = std::collections::VecDeque::new();

    dist[src] = Some(0);
    queue.push_back(src);

    while let Some(u) = queue.pop_front() {
        for &v in &adj[u] {
            if dist[v].is_none() {
                dist[v] = Some(dist[u].unwrap() + 1);
                queue.push_back(v);
            }
        }
    }
    dist
}

// ── Transform 2: Topological Sort Transform ──
// Transforms a DAG into a linear order consistent with edges.
// This is a linearization transform.

fn topological_sort(adj: &[Vec<usize>], n: usize) -> Option<Vec<usize>> {
    let mut in_degree = vec![0usize; n];
    for u in 0..n {
        for &v in &adj[u] {
            in_degree[v] += 1;
        }
    }

    let mut queue: std::collections::VecDeque<usize> =
        (0..n).filter(|&v| in_degree[v] == 0).collect();
    let mut order = Vec::new();

    while let Some(u) = queue.pop_front() {
        order.push(u);
        for &v in &adj[u] {
            in_degree[v] -= 1;
            if in_degree[v] == 0 {
                queue.push_back(v);
            }
        }
    }

    if order.len() == n { Some(order) } else { None } // None = cycle detected
}

// ── Transform 3: SCC (Strongly Connected Components) — Kosaraju's ──
// Collapses cycles into single "super-nodes", transforming a directed
// graph into a DAG.
// Chain: Graph → DFS order → Reverse graph DFS → SCC labels → DAG

fn kosaraju_scc(adj: &[Vec<usize>], n: usize) -> Vec<usize> {
    // Step 1: DFS on original graph, record finish order
    let mut visited = vec![false; n];
    let mut finish_order = Vec::new();

    fn dfs1(u: usize, adj: &[Vec<usize>], visited: &mut Vec<bool>, order: &mut Vec<usize>) {
        visited[u] = true;
        for &v in &adj[u] {
            if !visited[v] { dfs1(v, adj, visited, order); }
        }
        order.push(u);
    }

    for u in 0..n {
        if !visited[u] { dfs1(u, adj, &mut visited, &mut finish_order); }
    }

    // Step 2: Build reverse graph
    let mut radj = vec![vec![]; n];
    for u in 0..n {
        for &v in &adj[u] {
            radj[v].push(u);
        }
    }

    // Step 3: DFS on reverse graph in reverse finish order
    let mut comp = vec![usize::MAX; n];
    let mut num_comp = 0;

    fn dfs2(u: usize, c: usize, radj: &[Vec<usize>], comp: &mut Vec<usize>) {
        comp[u] = c;
        for &v in &radj[u] {
            if comp[v] == usize::MAX { dfs2(v, c, radj, comp); }
        }
    }

    for &u in finish_order.iter().rev() {
        if comp[u] == usize::MAX {
            dfs2(u, num_comp, &radj, &mut comp);
            num_comp += 1;
        }
    }

    comp
}

fn main() {
    // Directed graph: 0→1→2→0 (cycle), 3→1, 3→4
    let n = 5;
    let adj = vec![
        vec![1],    // 0→1
        vec![2],    // 1→2
        vec![0],    // 2→0 (creates SCC {0,1,2})
        vec![1, 4], // 3→1, 3→4
        vec![],     // 4 (isolated)
    ];

    let scc = kosaraju_scc(&adj, n);
    println!("=== Graph Transformation Chains ===");
    println!("SCC labels: {:?}", scc);
    println!("Nodes 0,1,2 same SCC: {}", scc[0] == scc[1] && scc[1] == scc[2]);
    println!("Node 3 different SCC: {}", scc[3] != scc[0]);

    // BFS distances
    let dist = bfs_distances(&vec![vec![1,2], vec![3], vec![3], vec![]], 0);
    println!("\nBFS distances from 0: {:?}", dist);
}
```

---

## 25. Two-Pointer Transform Pattern

### Concept

The **two-pointer** technique is a transform over a sequence that maintains two indices (pointers) and moves them toward or away from each other, reducing O(n²) problems to O(n).

```
CLASSIC PATTERNS:

1. OPPOSITE ENDS:        [←─────────────────→]
   left=0, right=n-1    Move toward center

2. SLIDING WINDOW:       [→→→→]
   left, right both      Window expands/contracts
   move right

3. PARTITION (Quicksort):  [→  ←]
                           swap when invariant broken
```

```rust
// ═══════════════════════════════════════════════════════
// TWO-POINTER TRANSFORMATION CHAINS
// ═══════════════════════════════════════════════════════

/// TRANSFORM: Two Sum (sorted array).
/// Find all pairs summing to target. O(n).
fn two_sum_sorted(arr: &[i64], target: i64) -> Vec<(usize, usize)> {
    let mut pairs = Vec::new();
    let (mut left, mut right) = (0, arr.len() - 1);

    while left < right {
        let sum = arr[left] + arr[right];
        match sum.cmp(&target) {
            std::cmp::Ordering::Equal => {
                pairs.push((left, right));
                left += 1;
                right -= 1;
            }
            std::cmp::Ordering::Less => left += 1,
            std::cmp::Ordering::Greater => right -= 1,
        }
    }
    pairs
}

/// TRANSFORM: Container with Most Water.
/// Height array → max water area. O(n).
/// Two pointers from ends, always move the shorter side.
fn max_water(heights: &[i64]) -> i64 {
    let (mut left, mut right) = (0, heights.len() - 1);
    let mut max_area = 0i64;

    while left < right {
        let area = heights[left].min(heights[right]) * (right - left) as i64;
        max_area = max_area.max(area);
        if heights[left] < heights[right] { left += 1; } else { right -= 1; }
    }
    max_area
}

/// TRANSFORM: Minimum Window Substring.
/// Find shortest window in `text` containing all chars of `pattern`. O(n).
fn min_window_substring(text: &[u8], pattern: &[u8]) -> Option<(usize, usize)> {
    if pattern.is_empty() || text.len() < pattern.len() { return None; }

    let mut need = [0i32; 256];
    for &c in pattern { need[c as usize] += 1; }

    let mut have = [0i32; 256];
    let mut formed = 0usize; // How many unique chars satisfied
    let unique_needed = need.iter().filter(|&&n| n > 0).count();

    let (mut best_l, mut best_r, mut best_len) = (0, 0, usize::MAX);
    let mut left = 0usize;

    for right in 0..text.len() {
        let c = text[right] as usize;
        have[c] += 1;
        if need[c] > 0 && have[c] == need[c] { formed += 1; }

        // Shrink window from left while valid
        while formed == unique_needed {
            if right - left + 1 < best_len {
                best_len = right - left + 1;
                best_l = left;
                best_r = right;
            }
            let lc = text[left] as usize;
            have[lc] -= 1;
            if need[lc] > 0 && have[lc] < need[lc] { formed -= 1; }
            left += 1;
        }
    }

    if best_len == usize::MAX { None } else { Some((best_l, best_r)) }
}

fn main() {
    let arr = vec![-4i64, -1, -1, 0, 1, 2];
    println!("=== Two-Pointer Transforms ===");
    println!("Two sum pairs summing to 0: {:?}", two_sum_sorted(&arr, 0));

    let heights = vec![1i64, 8, 6, 2, 5, 4, 8, 3, 7];
    println!("Max water: {}", max_water(&heights)); // 49

    let text = b"ADOBECODEBANC";
    let pattern = b"ABC";
    match min_window_substring(text, pattern) {
        Some((l, r)) => println!("Min window: {:?}", std::str::from_utf8(&text[l..=r]).unwrap()),
        None => println!("No window found"),
    }
}
```

---

## 26. Divide and Conquer Transform

### Concept

Divide and Conquer is a meta-transform: it recursively splits the problem, transforms each half, and combines the results.

```
DIVIDE AND CONQUER TEMPLATE:

solve(arr, l, r):
  if l == r:
    return base_transform(arr[l])    ← BASE CASE TRANSFORM
  mid = (l + r) / 2
  left_result  = solve(arr, l, mid)  ← LEFT TRANSFORM
  right_result = solve(arr, mid+1, r)← RIGHT TRANSFORM
  return merge_transform(left_result, right_result)  ← MERGE TRANSFORM
```

```rust
// ═══════════════════════════════════════════════════════
// DIVIDE AND CONQUER TRANSFORM
// ═══════════════════════════════════════════════════════

/// Merge Sort: the canonical divide-and-conquer transform.
/// Input array → sorted array. But also counts inversions as a side effect!
fn merge_sort_and_count(arr: &mut Vec<i64>, l: usize, r: usize) -> i64 {
    if l >= r { return 0; }
    let mid = l + (r - l) / 2;
    let mut inversions = 0i64;
    inversions += merge_sort_and_count(arr, l, mid);
    inversions += merge_sort_and_count(arr, mid + 1, r);
    inversions += merge(arr, l, mid, r);
    inversions
}

fn merge(arr: &mut Vec<i64>, l: usize, mid: usize, r: usize) -> i64 {
    let left = arr[l..=mid].to_vec();
    let right = arr[mid + 1..=r].to_vec();
    let (mut i, mut j, mut k) = (0, 0, l);
    let mut inversions = 0i64;

    while i < left.len() && j < right.len() {
        if left[i] <= right[j] {
            arr[k] = left[i]; i += 1;
        } else {
            // All remaining left elements form inversions with right[j]
            inversions += (left.len() - i) as i64;
            arr[k] = right[j]; j += 1;
        }
        k += 1;
    }
    while i < left.len() { arr[k] = left[i]; i += 1; k += 1; }
    while j < right.len() { arr[k] = right[j]; j += 1; k += 1; }
    inversions
}

/// Closest Pair of Points: D&C to find closest pair in O(n log n).
fn closest_pair(points: &mut Vec<(f64, f64)>) -> f64 {
    points.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap());
    closest_pair_recursive(points)
}

fn closest_pair_recursive(points: &[(f64, f64)]) -> f64 {
    let n = points.len();
    if n <= 3 {
        // Brute force for small sets
        let mut min_dist = f64::INFINITY;
        for i in 0..n {
            for j in i+1..n {
                let dx = points[i].0 - points[j].0;
                let dy = points[i].1 - points[j].1;
                min_dist = min_dist.min((dx*dx + dy*dy).sqrt());
            }
        }
        return min_dist;
    }

    let mid = n / 2;
    let mid_x = points[mid].0;

    let d_left = closest_pair_recursive(&points[..mid]);
    let d_right = closest_pair_recursive(&points[mid..]);
    let d = d_left.min(d_right);

    // Check the "strip" — points within d of the dividing line
    let mut strip: Vec<&(f64, f64)> = points.iter()
        .filter(|&&(x, _)| (x - mid_x).abs() < d)
        .collect();
    strip.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap());

    let mut strip_min = d;
    for i in 0..strip.len() {
        for j in i+1..strip.len() {
            if strip[j].1 - strip[i].1 >= strip_min { break; }
            let dx = strip[i].0 - strip[j].0;
            let dy = strip[i].1 - strip[j].1;
            strip_min = strip_min.min((dx*dx + dy*dy).sqrt());
        }
    }
    strip_min
}

fn main() {
    let mut arr = vec![3i64, 1, 4, 1, 5, 9, 2, 6];
    let inversions = merge_sort_and_count(&mut arr, 0, arr.len() - 1);
    println!("=== Divide & Conquer Transforms ===");
    println!("Sorted: {:?}", arr);
    println!("Inversions: {}", inversions);

    let mut points = vec![(0.0f64,0.0),(3.0,4.0),(1.0,1.0),(5.0,2.0)];
    println!("Closest pair distance: {:.4}", closest_pair(&mut points));
}
```

---

## 27. Composing Multiple Transforms

### The Grand Pattern

Real competitive programming problems chain 3-7 transforms. Recognizing which transforms to chain and in what order is the expert skill.

```
EXAMPLE: "Count subarrays where XOR of all elements = target"

NAIVE: O(n²) brute force — try all pairs
CHAIN APPROACH:
  1. Prefix XOR Transform:   arr → prefix_xor    O(n)
  2. Hash Map Frequency:     query matching pairs  O(n)
  Answer: count pairs (i,j) where prefix_xor[i] XOR prefix_xor[j] = target
                           ⟺ prefix_xor[j] = prefix_xor[i] XOR target
  Total: O(n)
```

```rust
// ═══════════════════════════════════════════════════════
// COMPOSING MULTIPLE TRANSFORMS — Advanced Problems
// ═══════════════════════════════════════════════════════

use std::collections::HashMap;

/// PROBLEM: Count subarrays with XOR = target.
/// CHAIN: Prefix XOR → HashMap frequency → count
fn count_subarrays_xor(arr: &[u64], target: u64) -> usize {
    let mut freq: HashMap<u64, usize> = HashMap::new();
    freq.insert(0, 1); // Empty prefix
    let mut xor = 0u64;
    let mut count = 0;

    for &x in arr {
        xor ^= x;                          // Step 1: Prefix XOR transform
        let needed = xor ^ target;         // Step 2: Inverse query
        count += freq.get(&needed).copied().unwrap_or(0); // Step 3: Frequency lookup
        *freq.entry(xor).or_insert(0) += 1;
    }
    count
}

/// PROBLEM: Longest subarray with sum = k.
/// CHAIN: Prefix Sum → HashMap first-occurrence → max length
fn longest_subarray_sum_k(arr: &[i64], k: i64) -> usize {
    let mut first_seen: HashMap<i64, i64> = HashMap::new();
    first_seen.insert(0, -1); // Prefix sum 0 seen at index -1 (before array)
    let mut prefix = 0i64;
    let mut max_len = 0usize;

    for (i, &x) in arr.iter().enumerate() {
        prefix += x;
        let needed = prefix - k;
        if let Some(&j) = first_seen.get(&needed) {
            max_len = max_len.max(i as usize - j as usize);
        }
        first_seen.entry(prefix).or_insert(i as i64); // Only first occurrence!
    }
    max_len
}

/// PROBLEM: Count paths in a tree from u to v passing through a node w.
/// CHAIN: Euler Tour → Binary Lifting (LCA) → Distance Formula
fn count_paths_through_node(
    tree_size: usize,
    queries: &[(usize, usize, usize)], // (u, v, w): does path u→v pass through w?
    bl: &BinaryLifting
) -> Vec<bool> {
    // Path u→v passes through w if and only if:
    // dist(u, w) + dist(w, v) == dist(u, v)
    queries.iter().map(|&(u, v, w)| {
        let d_uv = bl.distance(u, v);
        let d_uw = bl.distance(u, w);
        let d_wv = bl.distance(w, v);
        d_uw + d_wv == d_uv
    }).collect()
}

/// PROBLEM: Number of pairs with absolute difference ≤ k in sorted order.
/// CHAIN: Sort → Two Pointers → Count
fn count_pairs_within_diff(arr: &[i64], k: i64) -> u64 {
    let mut sorted = arr.to_vec();
    sorted.sort_unstable();
    let n = sorted.len();
    let mut count = 0u64;
    let mut left = 0;

    for right in 0..n {
        while sorted[right] - sorted[left] > k {
            left += 1;
        }
        count += (right - left) as u64; // All pairs (left..right, right)
    }
    count
}

/// PROBLEM: K-th smallest in matrix (row+col sorted).
/// CHAIN: Binary search on value → Monotonic count transform → Answer
fn kth_smallest_matrix(matrix: &[Vec<i64>], k: usize) -> i64 {
    let n = matrix.len();
    let (mut lo, mut hi) = (matrix[0][0], matrix[n-1][n-1]);

    // Binary search on the answer value
    while lo < hi {
        let mid = lo + (hi - lo) / 2;
        // Count how many elements ≤ mid
        let count: usize = matrix.iter().map(|row| {
            row.partition_point(|&x| x <= mid)
        }).sum();
        if count < k { lo = mid + 1; } else { hi = mid; }
    }
    lo
}

/// PROBLEM: Minimum cost path in grid with obstacles.
/// CHAIN: BFS (shortest path) → DP (min cost) — composition of two transforms
fn min_cost_path(grid: &[Vec<i64>]) -> i64 {
    let (rows, cols) = (grid.len(), grid[0].len());
    let mut dist = vec![vec![i64::MAX; cols]; rows];
    dist[0][0] = grid[0][0];

    // Dijkstra's (priority queue variant for weighted shortest path)
    let mut heap = std::collections::BinaryHeap::new();
    heap.push(std::cmp::Reverse((grid[0][0], 0usize, 0usize)));

    while let Some(std::cmp::Reverse((cost, r, c))) = heap.pop() {
        if cost > dist[r][c] { continue; }
        for (dr, dc) in [(0i64,1i64),(1,0),(0,-1),(-1,0)] {
            let nr = r as i64 + dr;
            let nc = c as i64 + dc;
            if nr >= 0 && nr < rows as i64 && nc >= 0 && nc < cols as i64 {
                let (nr, nc) = (nr as usize, nc as usize);
                let new_cost = cost + grid[nr][nc];
                if new_cost < dist[nr][nc] {
                    dist[nr][nc] = new_cost;
                    heap.push(std::cmp::Reverse((new_cost, nr, nc)));
                }
            }
        }
    }
    dist[rows-1][cols-1]
}

struct BinaryLifting {
    ancestor: Vec<Vec<usize>>,
    depth: Vec<usize>,
}
impl BinaryLifting {
    fn distance(&self, u: usize, v: usize) -> usize {
        // Simplified: just use depth difference for demo
        (self.depth[u] as i64 - self.depth[v] as i64).unsigned_abs() as usize
    }
}

fn main() {
    println!("=== Composed Transforms ===");

    let arr = vec![4u64, 2, 2, 6, 4];
    println!("Subarrays with XOR=6: {}", count_subarrays_xor(&arr, 6)); // 4

    let arr2 = vec![1i64, -1, 5, -2, 3];
    println!("Longest subarray sum=3: {}", longest_subarray_sum_k(&arr2, 3)); // 4

    let arr3 = vec![1i64, 3, 6, 10, 15];
    println!("Pairs with diff ≤ 4: {}", count_pairs_within_diff(&arr3, 4)); // 5

    let matrix = vec![
        vec![1i64, 5, 9],
        vec![10, 11, 13],
        vec![12, 13, 15],
    ];
    println!("8th smallest in matrix: {}", kth_smallest_matrix(&matrix, 8)); // 13

    let grid = vec![
        vec![1i64, 3, 1],
        vec![1, 5, 1],
        vec![4, 2, 1],
    ];
    println!("Min cost path (0,0) to (2,2): {}", min_cost_path(&grid)); // 7
}
```

---

## 28. Mental Models for Mastery

### Model 1: The Five-Question Framework

Before coding ANY problem, ask:

```
1. WHAT IS THE TRANSFORM?
   What changes? What stays the same?
   Input shape → Output shape?

2. IS IT INVERTIBLE?
   Can I undo the transform?
   (prefix sum ↔ difference array)

3. IS IT COMPOSABLE?
   Can I chain multiple transforms?
   What is the "interface" between stages?

4. WHAT IS THE MONOID?
   What operation combines partial results?
   Is it associative? Is there an identity?

5. WHAT IS THE COMPLEXITY TRADE-OFF?
   Build cost vs. Query cost?
   Space vs. Time?
```

### Model 2: The Lazy Flag Pattern

Many transforms can be "deferred":

```
EAGER: Apply transform immediately to all affected data
LAZY:  Mark that a transform is pending; apply when needed

Decision rule:
  If updates outnumber queries → consider LAZY
  If queries outnumber updates → consider EAGER
  If both are frequent       → Lazy Segment Tree / BIT
```

### Model 3: The Duality Principle

Every forward transform has an inverse:

```
FORWARD TRANSFORM          │  INVERSE TRANSFORM
─────────────────────────────────────────────────
Prefix Sum                 │  Difference Array
Zeta (SOS)                 │  Möbius Inversion
Suffix Array build         │  Pattern Search
Euler Tour (flatten)       │  Subtree Range query
BFS distances              │  Shortest path reconstruction
Compression (value→rank)   │  Decompression (rank→value)
```

### Model 4: Deliberate Practice Protocol

**For each new transform you learn:**

```
Phase 1 - UNDERSTAND (1 session):
  ✓ Can you explain it in 30 seconds without code?
  ✓ Can you trace through a small example by hand?
  ✓ Can you identify the monoid?

Phase 2 - IMPLEMENT (1-2 sessions):
  ✓ Implement from scratch without reference
  ✓ Test on edge cases (n=0, n=1, all same, sorted, reverse sorted)
  ✓ Analyze complexity before running

Phase 3 - APPLY (3-5 sessions):
  ✓ Solve 3-5 problems that use ONLY this transform
  ✓ Solve 2-3 problems that CHAIN this with other transforms
  ✓ Find a problem where you ALMOST used this but shouldn't

Phase 4 - INTERNALIZE:
  ✓ Without thinking, recognize when this transform applies
  ✓ Estimate complexity before coding
  ✓ Know the standard pitfalls and edge cases
```

### Model 5: The Chunking Hierarchy

Your brain learns in chunks. The hierarchy for transformation chains:

```
Level 0 (Atoms):    prefix_sum[i] = prefix_sum[i-1] + arr[i]
Level 1 (Molecules): PrefixSum struct with build() and query()
Level 2 (Patterns):  "Any range query on static array → try prefix sum"
Level 3 (Strategies):"Range sum + point update → BIT or Seg Tree"
Level 4 (Meta):      "All range structures are monoid homomorphisms"
```

You must be fluid at Level 4 to be in the top 1%.

### Model 6: Complexity Trade-offs at a Glance

```
PROBLEM TYPE                  │ BEST TRANSFORM        │ BUILD  │ QUERY  │ UPDATE
──────────────────────────────┼───────────────────────┼────────┼────────┼────────
Range sum, no update          │ Prefix Sum            │ O(n)   │ O(1)   │ N/A
Range min/max, no update      │ Sparse Table          │ O(nlogn)│ O(1)  │ N/A
Range sum, point update       │ BIT (Fenwick Tree)    │ O(nlogn)│O(logn)│ O(logn)
Range sum, range update       │ Lazy Seg Tree         │ O(n)   │ O(logn)│ O(logn)
Range min, range update       │ Lazy Seg Tree         │ O(n)   │ O(logn)│ O(logn)
LCA queries                   │ Binary Lifting        │ O(nlogn)│O(logn)│ N/A
Subtree queries               │ Euler Tour + BIT      │ O(nlogn)│O(logn)│ O(logn)
k-th ancestor                 │ Binary Lifting        │ O(nlogn)│O(logn)│ N/A
Pattern matching              │ KMP / Z-function      │ O(n+m) │ O(n)   │ N/A
Substring hash                │ Rolling Hash          │ O(n)   │ O(1)   │ N/A
Inversion count               │ Merge Sort / BIT      │ O(nlogn)│ N/A   │ N/A
Sliding window min/max        │ Monotonic Deque       │ O(n)   │ O(1)   │ N/A
Next greater element          │ Monotonic Stack       │ O(n)   │ O(1)   │ N/A
Range updates, √n queries     │ Sqrt Decomp           │ O(n)   │ O(√n)  │ O(√n)
```

### The Psychological Edge

**Deliberate Practice (Ericsson):** Don't just solve problems — dissect them. After solving, always ask: "What is the minimal transform chain that solves this?" Then find a different chain.

**Interleaved Practice:** Don't study prefix sums for 5 days straight. Mix: prefix sum → sparse table → monotonic stack → back to prefix sum. This forces your brain to build stronger retrieval cues.

**The Generation Effect:** Before reading a solution, WRITE DOWN your prediction of the transform chain. Even if wrong, the act of generation boosts retention by 40% (cognitive science).

**Flow State:** You achieve flow in DSA when problem structure pattern-matches to transform chains automatically — before conscious thought. This requires 200-400 hours of deliberate pattern exposure.

---

## Summary: The Transformation Chain Hierarchy

```
LEVEL 1 — ARRAY TRANSFORMS (Sequential)
  Prefix Sum │ Difference Array │ Running Stats │ Coordinate Compression

LEVEL 2 — STRUCTURE TRANSFORMS (Spatial)
  Sparse Table │ Binary Lifting │ Euler Tour │ Sqrt Decomposition

LEVEL 3 — STRING TRANSFORMS (Pattern)
  Rolling Hash │ Z-Function │ KMP │ Suffix Array

LEVEL 4 — DYNAMIC TRANSFORMS (Temporal)
  Segment Tree │ BIT │ Lazy Propagation │ Monotonic Stack/Deque

LEVEL 5 — ALGORITHMIC TRANSFORMS (Meta)
  DP Recurrences │ Graph SCC │ Divide & Conquer │ Two Pointers

LEVEL 6 — COMPOSED CHAINS (Mastery)
  Any combination of the above, chosen by pattern recognition
```

---

*"The master has failed more times than the beginner has tried. In algorithms, this means: the master has identified and applied more transformation chains than the beginner has seen problems."*

---

**End of Guide — Total Transforms Covered: 28 Categories, 40+ Implementations**

Here is what your guide covers — 28 transformation categories, fully implemented in Rust:

**Foundation Layer**
The guide opens with the mathematical bedrock: functions as transforms, the monoid structure (associativity + identity), and why recognizing monoids instantly tells you which data structure to use. The composition pattern — `g(f(x))` — is established as the atom of everything that follows.

**Array Transforms** (Chapters 6–10)
Prefix Sum and its inverse the Difference Array are treated as a duality pair. You'll see how they are literally inverses of each other, and how 2D variants extend the same idea to grids. Coordinate Compression and Discretization follow as "value-space" transforms.

**Static Query Transforms** (Chapters 11–12)
Sparse Table (for idempotent O(1) range queries) and Binary Lifting (for tree ancestor queries and LCA) — both powered by the same "doubling" principle.

**Tree Transforms** (Chapter 13)
Euler Tour flattening: the key insight that turns any subtree problem into a range problem, unlocking every array data structure for use on trees.

**String Transforms** (Chapters 14–17)
Rolling Hash (O(1) substring equality), Z-Function, KMP Failure Function, and Suffix Array + LCP Array — the complete string toolkit with all proofs via examples.

**Stack/Queue Transforms** (Chapters 18–19)
Monotonic Stack (next/previous greater/smaller, histogram rectangles) and Monotonic Deque (sliding window min/max) — traced step by step with visual state diagrams.

**Advanced Transforms** (Chapters 20–26)
Bit Manipulation (SOS DP, Möbius Inversion, Gray Code), Lazy Segment Tree (deferred transforms), Sqrt Decomposition, DP-as-chain, Graph transforms (SCC, topological sort), Two Pointers, and Divide & Conquer.

**Composition Chapter** (Chapter 27)
Six real problems that require chaining 2–4 transforms — this is where expert pattern recognition is trained.

**Mental Models** (Chapter 28)
The five-question framework, the lazy flag decision rule, the duality table, deliberate practice protocol, and the chunking hierarchy from atom to meta-level — structured to accelerate mastery through cognitive science principles.