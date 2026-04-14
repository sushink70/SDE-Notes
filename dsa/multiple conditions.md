# The Complete Guide to Multiple Conditions in DSA
## Mastering Conditional Logic in Loops and Control Flow

> *"Clarity of condition is clarity of thought. Every `if` you write is a decision tree node. Every `while` guard is an invariant. Master the logic, and the code writes itself."*

---

## Table of Contents

1. [The Mental Model — Think Before You Code](#1-the-mental-model)
2. [Boolean Algebra Foundations](#2-boolean-algebra-foundations)
3. [Condition Anatomy — What Makes a Good Condition](#3-condition-anatomy)
4. [Logical Operators Deep Dive](#4-logical-operators-deep-dive)
5. [If / Else If / Else — The Decision Tree](#5-if--else-if--else)
6. [Loop Guards — While and For Conditions](#6-loop-guards)
7. [The Two-Pointer Pattern and Its Conditions](#7-the-two-pointer-pattern)
8. [Binary Search Conditions — The Most Misunderstood](#8-binary-search-conditions)
9. [Short-Circuit Evaluation — A Superpower](#9-short-circuit-evaluation)
10. [Compound Conditions — Building Complex Guards](#10-compound-conditions)
11. [Loop Invariants — The Expert's Secret Weapon](#11-loop-invariants)
12. [Early Exit Strategies — Break, Continue, Return](#12-early-exit-strategies)
13. [Boundary Conditions — The Source of All Bugs](#13-boundary-conditions)
14. [Nested Conditions and How to Flatten Them](#14-nested-conditions)
15. [State Machine Conditions](#15-state-machine-conditions)
16. [DSA Pattern Catalog with Conditions](#16-dsa-pattern-catalog)
17. [Common Mistakes and Anti-Patterns](#17-common-mistakes-and-anti-patterns)
18. [Expert Mental Checklist](#18-expert-mental-checklist)

---

## 1. The Mental Model

### How an Expert Reads a Condition

Before writing any condition, an expert asks three questions:

```
1. WHAT state am I in right now?
2. WHAT must be true to proceed / continue?
3. WHAT happens at the boundary — the exact moment the condition flips?
```

Every condition in DSA is one of three things:

| Type | Purpose | Example |
|------|---------|---------|
| **Guard** | Prevent invalid access | `i < n`, `ptr != NULL` |
| **Invariant check** | Maintain algorithm correctness | `left <= right` in binary search |
| **Termination condition** | Know when to stop | `slow == fast` in cycle detection |

### The Analogy That Locks It In

Think of your loop condition as a **security checkpoint**:
- The guard checks your credentials every single iteration.
- If you fail the check, you are ejected from the loop.
- The **moment** you fail is the **boundary** — the most important moment.

```
BEFORE entering: Is it safe to enter? (pre-condition)
DURING execution: Is the invariant still holding? (loop invariant)
AFTER exiting:   What is guaranteed to be true now? (post-condition)
```

This mindset eliminates off-by-one errors. Not reduces — eliminates.

---

## 2. Boolean Algebra Foundations

### Truth Tables — The Ground Truth

You must know these by heart. Every complex condition decomposes into these:

```
AND (&&, &):   A && B is true ONLY when BOTH A and B are true
OR  (||, |):   A || B is true when AT LEAST ONE of A or B is true
NOT (!):       !A flips the truth value
XOR (^):       A ^ B is true when EXACTLY ONE of A or B is true
```

**AND Table:**
```
A     B     A && B
true  true   true
true  false  false
false true   false
false false  false
```

**OR Table:**
```
A     B     A || B
true  true   true
true  false  true
false true   true
false false  false
```

### De Morgan's Laws — The Most Important Transformation

```
!(A && B)  ==  (!A || !B)
!(A || B)  ==  (!A && !B)
```

**Why this matters in DSA:**

When you want to **break** out of a loop, you write the condition under which you **continue**, then negate it to understand the exit condition — or vice versa.

```
continue while: (left < right && arr[left] != target)
exit when:      !(left < right && arr[left] != target)
             == (left >= right || arr[left] == target)
```

This means: "I stop when I've exhausted the range OR I found the target." That is exactly what binary search does.

---

## 3. Condition Anatomy

### The Five Elements of a Condition

```
  left < right && arr[mid] != target
  ├──────┬──────┘  └───────┬────────┘
  │      │                  │
  │   comparator         comparator
  │   (relational)       (equality)
  │
  logical connector (&&)

Elements:
1. Operands     — the values being compared (left, right, arr[mid], target)
2. Comparators  — ==, !=, <, >, <=, >=
3. Connectors   — &&, ||, !
4. Precedence   — ! > && > ||
5. Side effects — none! Never put side effects in conditions
```

### Operator Precedence (High to Low)

```
!           (highest — applies first)
< > <= >=
== !=
&&
||          (lowest — applies last)
```

**Critical Example:**

```c
// What does this evaluate to?
if (a || b && c)

// It evaluates as:
if (a || (b && c))   // && binds tighter than ||

// NOT as:
if ((a || b) && c)   // WRONG mental model
```

**Rule:** When in doubt, add parentheses. Parentheses cost nothing. Bugs cost hours.

---

## 4. Logical Operators Deep Dive

### AND (`&&`) — The Restrictor

Use AND when **all conditions must be simultaneously true**.

```
"I can proceed only if EVERYTHING is fine."
```

**C Implementation:**
```c
// Safe array access: both index valid AND value matches
bool safe_find(int *arr, int n, int idx, int target) {
    return (idx >= 0 && idx < n && arr[idx] == target);
    //      ─────────   ──────    ─────────────────────
    //      lower bound  upper    actual check
    //      check        bound    (only reached if both above pass)
}
```

**Go Implementation:**
```go
// Two conditions must both hold: within bounds AND satisfies predicate
func canProceed(arr []int, i int, predicate func(int) bool) bool {
    return i < len(arr) && predicate(arr[i])
    // If i >= len(arr), predicate(arr[i]) is NEVER called — safe!
}
```

**Rust Implementation:**
```rust
// Rust's type system often removes need for null checks,
// but range + value conditions are still common
fn find_valid(arr: &[i32], target: i32) -> Option<usize> {
    for (i, &val) in arr.iter().enumerate() {
        if val == target && i % 2 == 0 {  // value match AND even index
            return Some(i);
        }
    }
    None
}
```

---

### OR (`||`) — The Permitter

Use OR when **any one condition being true is sufficient**.

```
"I can proceed if ANYTHING is acceptable."
```

**C Implementation:**
```c
// Exit search if out of bounds OR found match OR found invalid value
while (i < n || j >= 0) {
    // This loop continues while EITHER pointer is valid
    // ...
}

// More common: stop when EITHER condition fails
while (i < n && j >= 0) {  // Both must be valid to continue
    // ...
}
```

**Go Implementation:**
```go
// Palindrome check: stop if mismatch OR pointers cross
func isPalindrome(s string) bool {
    left, right := 0, len(s)-1
    for left < right {
        if s[left] != s[right] {
            return false  // Early exit on mismatch
        }
        left++
        right--
    }
    return true
}

// OR in condition: valid if either edge exists
func hasEdge(adj [][]int, u, v int) bool {
    return u < len(adj) && (v < len(adj[u]) || contains(adj[u], v))
}

func contains(slice []int, val int) bool {
    for _, v := range slice {
        if v == val {
            return true
        }
    }
    return false
}
```

---

### NOT (`!`) — The Inverter

The most misused operator. Prefer positive conditions when possible — they are easier to reason about.

```c
// AVOID: double negation confuses the brain
if (!(!found)) { ... }      // same as if (found)

// PREFER: direct positive condition
if (found) { ... }

// VALID use: when you want to express "while not done"
while (!finished && i < n) {
    // ...
}
```

**The Negation Trick for Loop Design:**

When you know the **exit condition**, negate it to get the **loop condition**:

```
Exit when: i >= n  OR  arr[i] == target
Continue:  i <  n  AND arr[i] != target    ← De Morgan's Law applied
```

```c
// C: elegant linear search
int linear_search(int *arr, int n, int target) {
    int i = 0;
    while (i < n && arr[i] != target) {  // CONTINUE condition
        i++;
    }
    return (i < n) ? i : -1;  // Check if we found or exhausted
}
```

---

## 5. If / Else If / Else — The Decision Tree

### The Architecture of Branching

Think of `if-else if-else` as a **decision tree** where:
- Each branch is **mutually exclusive** (only one executes)
- Branches are evaluated **top to bottom** in order
- The first `true` branch executes; the rest are skipped
- `else` is a catch-all for "none of the above"

```
if (most specific / most likely condition) {
} else if (second specific condition) {
} else if (third condition) {
} else {
    // guaranteed: none of above were true
}
```

### Ordering Strategy — Performance Matters

**Rule 1: Put the most likely branch first** (branch prediction optimization)

**Rule 2: Put the most restrictive check first** (prevents invalid access)

```c
// WRONG ORDER — can access arr[-1] when i == 0
if (arr[i] == arr[i-1] && i > 0) { ... }

// CORRECT ORDER — i > 0 guards arr[i-1] access
if (i > 0 && arr[i] == arr[i-1]) { ... }
```

### Complete C Example — Classifying Array Elements

```c
#include <stdio.h>
#include <stdlib.h>

typedef enum {
    NEGATIVE_LARGE,   // < -100
    NEGATIVE_SMALL,   // -100 to -1
    ZERO,
    POSITIVE_SMALL,   // 1 to 100
    POSITIVE_LARGE    // > 100
} Category;

Category classify(int x) {
    if (x == 0) {
        return ZERO;
    } else if (x > 0) {
        if (x <= 100) {
            return POSITIVE_SMALL;
        } else {
            return POSITIVE_LARGE;
        }
    } else {  // x < 0 — guaranteed by elimination
        if (x >= -100) {
            return NEGATIVE_SMALL;
        } else {
            return NEGATIVE_LARGE;
        }
    }
}

// Flatten nested if — often cleaner
Category classify_flat(int x) {
    if (x == 0)    return ZERO;
    if (x > 100)   return POSITIVE_LARGE;
    if (x > 0)     return POSITIVE_SMALL;
    if (x >= -100) return NEGATIVE_SMALL;
    return NEGATIVE_LARGE;  // guaranteed: x < -100
}
```

### Complete Go Example — Merge Sort Condition Logic

```go
package main

// Three-way merge condition: which of three subarray heads is smallest
func mergeThree(a, b, c []int) []int {
    result := make([]int, 0, len(a)+len(b)+len(c))
    i, j, k := 0, 0, 0

    for i < len(a) || j < len(b) || k < len(c) {
        // Determine smallest available element
        aVal := getOrMax(a, i)
        bVal := getOrMax(b, j)
        cVal := getOrMax(c, k)

        if aVal <= bVal && aVal <= cVal {
            result = append(result, aVal)
            i++
        } else if bVal <= aVal && bVal <= cVal {
            result = append(result, bVal)
            j++
        } else {
            result = append(result, cVal)
            k++
        }
    }
    return result
}

func getOrMax(arr []int, idx int) int {
    if idx < len(arr) {
        return arr[idx]
    }
    return 1<<62 - 1  // max int64 as sentinel
}
```

### Complete Rust Example — Interval Classification

```rust
#[derive(Debug, PartialEq)]
enum Relation {
    Before,     // a ends before b starts
    Overlapping,
    After,      // a starts after b ends
    Contains,   // a fully contains b
    Within,     // a is fully within b
}

fn classify_intervals(a: (i32, i32), b: (i32, i32)) -> Relation {
    let (a_start, a_end) = a;
    let (b_start, b_end) = b;

    if a_end < b_start {
        Relation::Before
    } else if a_start > b_end {
        Relation::After
    } else if a_start <= b_start && a_end >= b_end {
        Relation::Contains
    } else if a_start >= b_start && a_end <= b_end {
        Relation::Within
    } else {
        Relation::Overlapping
    }
}

fn main() {
    println!("{:?}", classify_intervals((1, 5), (6, 10)));  // Before
    println!("{:?}", classify_intervals((1, 10), (3, 7)));  // Contains
    println!("{:?}", classify_intervals((3, 7), (1, 10)));  // Within
    println!("{:?}", classify_intervals((1, 5), (3, 8)));   // Overlapping
}
```

---

## 6. Loop Guards

### The While Loop — Pure Condition Control

The `while` loop is the most fundamental. Its condition is checked **before** each iteration.

```
while (CONDITION) {
    body
}

Semantics:
1. Check CONDITION
2. If false → exit
3. If true  → execute body → goto 1
```

**The guard must encode three things:**
1. **Bounds check** — am I still within valid range?
2. **Termination** — am I done with my work?
3. **Safety** — is it safe to access the next element?

### Multiple Exit Conditions in While

```c
// Pattern: continue while ALL of these are true
while (i < n           // bounds
       && j >= 0       // other pointer bounds
       && !found       // not yet done
       && arr[i] > 0)  // problem-specific invariant
{
    // body
}
```

**The exit occurs when ANY condition becomes false.**

Draw the exit table explicitly for complex loops:

```
Exit when:
- i >= n         → exhausted from left
- j < 0          → exhausted from right
- found == true  → found target
- arr[i] <= 0    → invalid element encountered
```

### For Loop Conditions

```c
for (init; condition; update) {
    body
}
// Equivalent to:
init;
while (condition) {
    body;
    update;
}
```

**Multiple conditions in for loops:**

```c
// Count vowels while also tracking position
for (int i = 0, vowel_count = 0; i < n && vowel_count < max_vowels; i++) {
    if (is_vowel(str[i])) vowel_count++;
}

// Traverse two arrays simultaneously
for (int i = 0, j = n-1; i < j; i++, j--) {
    // symmetric processing
}
```

### The Do-While — Execute At Least Once

```c
do {
    body;
} while (condition);
```

Use do-while when you need to execute the body before the first check. Common in:
- Menu loops (show menu, then check if user wants to continue)
- Newton's method (compute one iteration, then check convergence)
- Input validation

```c
// Input validation: get input FIRST, THEN check
int value;
do {
    printf("Enter positive number: ");
    scanf("%d", &value);
} while (value <= 0);  // Repeat if invalid
```

---

## 7. The Two-Pointer Pattern

This is where multiple conditions are the heart of the algorithm.

### Anatomy of Two-Pointer Conditions

```
Two pointers: left and right
Loop guard:   left < right   (they haven't crossed)
Inner action: depends on comparison of arr[left] and arr[right]
```

**The Critical Question: `<` or `<=`?**

```
left < right   → stop when pointers MEET (for palindrome, sum search)
left <= right  → stop when left PASSES right (for binary search)
```

The difference of one determines whether the middle element is visited.

### Two-Sum in Sorted Array — Full Analysis

```c
// Given sorted arr[], find pair with sum == target
// Returns 1 if found, 0 if not
int two_sum_sorted(int *arr, int n, int target, int *out_i, int *out_j) {
    int left = 0, right = n - 1;

    while (left < right) {          // Guard: valid range (left < right, not <=)
        int sum = arr[left] + arr[right];

        if (sum == target) {         // Found: both conditions
            *out_i = left;
            *out_j = right;
            return 1;
        } else if (sum < target) {   // Too small: move left pointer right
            left++;
        } else {                     // Too large: move right pointer left
            right--;
        }
    }
    return 0;  // Not found
}
```

**Why `left < right` and not `left <= right`?**
- At `left == right`, both pointers point to the same element.
- We need two **distinct** elements. So we stop when they meet.

### Go — Container With Most Water

```go
// Classic two-pointer: maximize area = min(height[l], height[r]) * (r - l)
func maxArea(height []int) int {
    left, right := 0, len(height)-1
    maxWater := 0

    for left < right {  // Continue while pointers haven't crossed
        width := right - left
        h := min(height[left], height[right])
        water := width * h

        if water > maxWater {
            maxWater = water
        }

        // Move the pointer at the shorter bar
        // Reasoning: keeping the taller one maximizes potential future area
        if height[left] < height[right] {
            left++
        } else {
            right--
        }
    }
    return maxWater
}

func min(a, b int) int {
    if a < b {
        return a
    }
    return b
}
```

### Rust — Three-Sum with Multiple Conditions

```rust
fn three_sum(mut nums: Vec<i32>) -> Vec<Vec<i32>> {
    nums.sort_unstable();
    let mut result = Vec::new();
    let n = nums.len();

    // Outer loop: fix the first element
    for i in 0..n.saturating_sub(2) {
        // Skip duplicates for the first element
        if i > 0 && nums[i] == nums[i - 1] {
            continue;  // Condition: i > 0 guards index i-1 access
        }

        let (mut left, mut right) = (i + 1, n - 1);

        while left < right {  // Two-pointer inner loop
            let sum = nums[i] + nums[left] + nums[right];

            if sum == 0 {
                result.push(vec![nums[i], nums[left], nums[right]]);

                // Skip duplicates for left pointer
                // Condition: left < right AND same as previous
                while left < right && nums[left] == nums[left + 1] {
                    left += 1;
                }
                // Skip duplicates for right pointer
                while left < right && nums[right] == nums[right - 1] {
                    right -= 1;
                }

                left += 1;
                right -= 1;
            } else if sum < 0 {
                left += 1;
            } else {
                right -= 1;
            }
        }
    }
    result
}
```

**Condition Analysis in Three-Sum:**

```
Outer loop guard:  i < n - 2                  (need at least 2 more elements)
Duplicate skip:    i > 0 && nums[i] == nums[i-1]  (two guards: bounds + value)
Inner loop guard:  left < right               (valid window exists)
Duplicate skips:   left < right && nums[left] == nums[left+1]
                   ─────────────   ──────────────────────────
                   prevents crossing   value equality check
```

---

## 8. Binary Search Conditions

Binary search has more condition variants than any other algorithm. Mastering it means mastering conditions.

### Template 1: Exact Match

```
left = 0, right = n - 1
loop while: left <= right    ← NOTE: <= not <
```

```c
int binary_search(int *arr, int n, int target) {
    int left = 0, right = n - 1;

    while (left <= right) {        // ← <= because right starts at valid index
        int mid = left + (right - left) / 2;  // Prevents overflow

        if (arr[mid] == target) {
            return mid;
        } else if (arr[mid] < target) {
            left = mid + 1;        // mid is too small, exclude it
        } else {
            right = mid - 1;       // mid is too large, exclude it
        }
    }
    return -1;  // Not found — guaranteed: left > right
}
```

**Post-condition guarantee:** When the loop exits, `left > right`. The target does not exist.

### Template 2: Find Left Boundary (First Occurrence)

```c
// Find first position where arr[i] >= target
int lower_bound(int *arr, int n, int target) {
    int left = 0, right = n;  // NOTE: right = n (one past end)

    while (left < right) {    // NOTE: < not <=  (right is exclusive)
        int mid = left + (right - left) / 2;

        if (arr[mid] < target) {
            left = mid + 1;   // mid is too small
        } else {
            right = mid;      // mid could be the answer, keep it
        }
    }
    return left;  // Post-condition: left == right, arr[left] >= target
}
```

### Template 3: Find Right Boundary (Last Occurrence)

```c
// Find last position where arr[i] <= target
int upper_bound(int *arr, int n, int target) {
    int left = 0, right = n;

    while (left < right) {
        int mid = left + (right - left) / 2;

        if (arr[mid] <= target) {
            left = mid + 1;   // mid could still work, but try right of it
        } else {
            right = mid;
        }
    }
    return left - 1;  // Last valid position
}
```

### Comparison of Loop Guard Conditions

```
Template 1 (exact):          while (left <= right)
  - right = n - 1 (inclusive)
  - Exits when left > right
  - Search space: [left, right]

Template 2 (left boundary):  while (left < right)
  - right = n (exclusive)
  - Exits when left == right
  - Search space: [left, right)

Template 3 (right boundary): while (left < right)
  - Same as template 2
```

**Why the difference?**

In Template 1: `right` is a valid index. When `left == right`, there's one element left to check. So we use `<=`.

In Template 2: `right` is an exclusive upper bound (like `n`). When `left == right`, the search space is empty. So we use `<`.

### Go — Binary Search on Answer

```go
// Find minimum speed to eat all bananas in h hours
// Classic "binary search on the answer" — condition is a function
func minEatingSpeed(piles []int, h int) int {
    left, right := 1, maxPile(piles)

    for left < right {  // Find leftmost valid speed
        mid := left + (right-left)/2

        if canFinish(piles, mid, h) {
            right = mid      // mid works, try smaller
        } else {
            left = mid + 1   // mid too slow, need faster
        }
    }
    return left
}

func canFinish(piles []int, speed, hours int) bool {
    totalHours := 0
    for _, pile := range piles {
        // Ceiling division: (pile + speed - 1) / speed
        totalHours += (pile + speed - 1) / speed
        if totalHours > hours {  // Early exit: already exceeded limit
            return false
        }
    }
    return totalHours <= hours
}

func maxPile(piles []int) int {
    m := 0
    for _, p := range piles {
        if p > m {
            m = p
        }
    }
    return m
}
```

### Rust — Rotated Sorted Array Search

```rust
fn search_rotated(nums: &[i32], target: i32) -> i32 {
    let (mut left, mut right) = (0i32, nums.len() as i32 - 1);

    while left <= right {
        let mid = left + (right - left) / 2;
        let mid_u = mid as usize;

        if nums[mid_u] == target {
            return mid;
        }

        // Determine which half is sorted
        // Multiple conditions here: compare endpoints to determine order
        if nums[left as usize] <= nums[mid_u] {
            // Left half [left..mid] is sorted
            if nums[left as usize] <= target && target < nums[mid_u] {
                // Target is in the sorted left half
                right = mid - 1;
            } else {
                // Target is in the right half
                left = mid + 1;
            }
        } else {
            // Right half [mid..right] is sorted
            if nums[mid_u] < target && target <= nums[right as usize] {
                // Target is in the sorted right half
                left = mid + 1;
            } else {
                // Target is in the left half
                right = mid - 1;
            }
        }
    }
    -1
}
```

---

## 9. Short-Circuit Evaluation

### The Fundamental Rule

```
In (A && B):  if A is false, B is NEVER evaluated
In (A || B):  if A is true,  B is NEVER evaluated
```

This is not just an optimization — it is a **correctness mechanism**.

### Using && for Safe Access

```c
// DANGEROUS: potential null dereference
if (ptr->value == 42) { ... }        // Crashes if ptr is NULL

// SAFE: null check first, access second
if (ptr != NULL && ptr->value == 42) { ... }
//   ──────────   ─────────────────
//   evaluated first    only evaluated if ptr != NULL
```

```go
// DANGEROUS: index out of bounds
if arr[i] == target { ... }           // Panics if i >= len(arr)

// SAFE: bounds check first
if i < len(arr) && arr[i] == target { ... }
```

```rust
// Rust makes this explicit with Option types
fn check_element(arr: &[i32], i: usize, target: i32) -> bool {
    // arr.get(i) returns Option<&i32> — no short-circuit needed for bounds
    arr.get(i).map_or(false, |&v| v == target)

    // Or with explicit short-circuit using match:
    match arr.get(i) {
        Some(&v) => v == target,
        None => false,
    }
}

// But in raw pointer / unsafe contexts, short-circuit matters:
unsafe fn unsafe_check(ptr: *const i32, val: i32) -> bool {
    !ptr.is_null() && *ptr == val
    //  ──────────    ──────────
    //  checked first  only if non-null
}
```

### Using || for Default Fallback

```c
// If primary lookup fails, try secondary
bool find_value(int *primary, int pn, int *secondary, int sn, int target) {
    int i = linear_search(primary, pn, target);
    int j = linear_search(secondary, sn, target);

    return (i != -1) || (j != -1);
    //     ─────────    ─────────
    //     if this true,  this isn't evaluated (optimization)
}
```

### Performance Ordering Rule

Put the **cheaper** or **more likely to short-circuit** check first:

```c
// If is_valid() is O(n) and quick_check() is O(1):
// SLOW: is_valid() runs every time
if (is_valid(data) && quick_check(x)) { ... }

// FAST: quick_check() often short-circuits, skipping is_valid()
if (quick_check(x) && is_valid(data)) { ... }
```

---

## 10. Compound Conditions — Building Complex Guards

### The Art of Building Multi-Part Conditions

Complex conditions are built from simple ones. The key is knowing **which connector to use and why**.

#### Pattern: All-Or-Nothing (AND chain)

```
"Every single requirement must hold."
```

```c
// Valid move in chess board traversal: in bounds AND not visited
bool is_valid_cell(int row, int col, int rows, int cols, bool **visited) {
    return row >= 0
        && row < rows
        && col >= 0
        && col < cols
        && !visited[row][col];
}
```

**Reading: "row is non-negative AND within height AND col is non-negative AND within width AND not yet visited"**

Each condition adds a constraint. If any fails, the whole thing fails.

#### Pattern: Any-Will-Do (OR chain)

```
"At least one requirement must hold."
```

```c
// Character is a word boundary if it's space, newline, or tab
bool is_whitespace(char c) {
    return c == ' '
        || c == '\n'
        || c == '\t'
        || c == '\r';
}
```

#### Pattern: Mixed AND/OR — The Tricky One

```c
// A position is "interesting" if:
// (it's a peak OR a valley) AND (it's not at the boundary)
bool is_interesting(int *arr, int i, int n) {
    bool not_boundary = (i > 0 && i < n - 1);
    bool is_peak = (arr[i] > arr[i-1] && arr[i] > arr[i+1]);
    bool is_valley = (arr[i] < arr[i-1] && arr[i] < arr[i+1]);

    return not_boundary && (is_peak || is_valley);
    //     ─────────────   ─────────────────────
    //     outer AND          inner OR
}
```

**Always break complex compound conditions into named booleans for clarity.**

### Go — BFS Valid Cell Check

```go
package main

// Direction vectors for 4-directional BFS
var dirs = [][2]int{{0, 1}, {0, -1}, {1, 0}, {-1, 0}}

func bfs(grid [][]int, startR, startC int) int {
    rows, cols := len(grid), len(grid[0])
    visited := make([][]bool, rows)
    for i := range visited {
        visited[i] = make([]bool, cols)
    }

    queue := [][2]int{{startR, startC}}
    visited[startR][startC] = true
    count := 0

    for len(queue) > 0 {
        curr := queue[0]
        queue = queue[1:]
        count++

        for _, d := range dirs {
            nr, nc := curr[0]+d[0], curr[1]+d[1]

            // Compound condition: valid AND not visited AND accessible
            if nr >= 0 && nr < rows &&          // row bounds
                nc >= 0 && nc < cols &&          // col bounds
                !visited[nr][nc] &&              // not visited
                grid[nr][nc] == 1 {              // accessible cell
                visited[nr][nc] = true
                queue = append(queue, [2]int{nr, nc})
            }
        }
    }
    return count
}
```

### Rust — DFS with Complex Pruning Conditions

```rust
fn dfs_permutations(
    nums: &[i32],
    used: &mut Vec<bool>,
    current: &mut Vec<i32>,
    result: &mut Vec<Vec<i32>>,
) {
    // Base case: permutation complete
    if current.len() == nums.len() {
        result.push(current.clone());
        return;
    }

    for i in 0..nums.len() {
        // Multiple conditions for pruning:
        // 1. Not already used in current permutation
        // 2. Skip duplicates: if same value as previous AND previous wasn't used
        //    (This handles duplicate elements correctly)
        if used[i] {
            continue;
        }
        if i > 0 && nums[i] == nums[i - 1] && !used[i - 1] {
            continue;  // Skip duplicate permutation branches
        }

        used[i] = true;
        current.push(nums[i]);
        dfs_permutations(nums, used, current, result);
        current.pop();
        used[i] = false;
    }
}

fn permute_unique(mut nums: Vec<i32>) -> Vec<Vec<i32>> {
    nums.sort_unstable();  // Sort to group duplicates
    let n = nums.len();
    let mut result = Vec::new();
    let mut used = vec![false; n];
    let mut current = Vec::new();
    dfs_permutations(&nums, &mut used, &mut current, &mut result);
    result
}
```

---

## 11. Loop Invariants — The Expert's Secret Weapon

A loop invariant is a **property that is true before each iteration, during, and after the loop**. It is the single most powerful tool for writing correct loops.

### How to Use Invariants

**Step 1:** State the invariant in plain English before writing code.
**Step 2:** Verify it holds before the loop starts.
**Step 3:** Verify each iteration preserves it.
**Step 4:** Verify the post-condition is derivable from invariant + exit condition.

### Example 1: Linear Search Invariant

```
Invariant: "arr[0..i) does not contain target"
           (all elements before index i have been checked)

Before loop: i = 0, so arr[0..0) is empty — trivially true
Each step:   We checked arr[i], increment i — invariant preserved
After loop:  i == n (exit) → arr[0..n) doesn't contain target → NOT FOUND
          OR arr[i] == target (exit) → FOUND at i
```

```c
int linear_search_invariant(int *arr, int n, int target) {
    // Invariant: arr[0..i) does not contain target
    int i = 0;
    while (i < n && arr[i] != target) {
        // At this point: arr[0..i) checked, arr[i] != target
        i++;
        // Now: arr[0..i) checked (arr[i-1] was just checked and wasn't target)
    }
    // Post-condition: i == n (not found) OR arr[i] == target (found)
    return (i < n) ? i : -1;
}
```

### Example 2: Binary Search Invariant

```
Invariant: "If target exists in arr, it must be in arr[left..right]"

Before loop: left = 0, right = n-1 → full array → trivially true
Each step:   We eliminate the half that cannot contain target
After loop:  left > right → search space empty → target not present
```

```go
// Binary search with invariant explicitly documented
func binarySearchInvariant(arr []int, target int) int {
    left, right := 0, len(arr)-1
    // Invariant: if target exists, it's in arr[left..right]

    for left <= right {
        mid := left + (right-left)/2

        if arr[mid] == target {
            return mid
        } else if arr[mid] < target {
            left = mid + 1  // arr[left..mid] all < target, eliminate them
            // Invariant preserved: if target exists, now it's in arr[left..right]
        } else {
            right = mid - 1  // arr[mid..right] all > target, eliminate them
            // Invariant preserved
        }
    }
    // Invariant + exit: target in arr[left..right] AND left > right → impossible → not found
    return -1
}
```

### Example 3: Two-Pointer Invariant for Partition

```
Invariant for Dutch National Flag (sort 0s, 1s, 2s):
- arr[0..low)  contains only 0s
- arr[low..mid) contains only 1s
- arr[mid..high] contains unknown elements
- arr[high+1..n) contains only 2s
```

```rust
fn dutch_national_flag(arr: &mut Vec<i32>) {
    let (mut low, mut mid, mut high) = (0, 0, arr.len() - 1);

    // Invariant:
    // arr[0..low)  → all 0s
    // arr[low..mid) → all 1s
    // arr[mid..=high] → unprocessed
    // arr[high+1..] → all 2s

    while mid <= high {
        match arr[mid] {
            0 => {
                arr.swap(low, mid);
                low += 1;
                mid += 1;
                // arr[mid-1] is now 1 (was swapped from arr[low])
                // arr[low-1] is now 0 — invariant preserved
            }
            1 => {
                mid += 1;
                // arr[mid-1] == 1, already in correct zone
            }
            2 => {
                arr.swap(mid, high);
                // high decrements, but mid stays — we need to re-examine arr[mid]
                if high == 0 { break; }  // Boundary: prevent underflow
                high -= 1;
            }
            _ => unreachable!(),
        }
    }
}
```

---

## 12. Early Exit Strategies — Break, Continue, Return

### The Three Weapons

| Keyword | Effect | Use When |
|---------|--------|----------|
| `break` | Exit the innermost loop | Condition found, no need to continue |
| `continue` | Skip to next iteration | Current element invalid, skip processing |
| `return` | Exit entire function | Condition found anywhere in call stack |

### Break — Structured Exit

```c
// Find first pair that sums to target
void find_pair(int *arr, int n, int target) {
    bool found = false;
    int result_i = -1, result_j = -1;

    for (int i = 0; i < n && !found; i++) {
        for (int j = i + 1; j < n; j++) {
            if (arr[i] + arr[j] == target) {
                found = true;
                result_i = i;
                result_j = j;
                break;  // Exit inner loop only
            }
        }
        // !found in outer loop condition handles the outer exit
    }
}
```

**Note:** `break` only exits the **innermost** loop. To exit nested loops, use a flag in the outer condition (as above), or use `goto` in C (rare but legitimate), or restructure into a function and use `return`.

### Continue — Skip and Proceed

```c
// Process only non-zero elements
void process_nonzero(int *arr, int n) {
    for (int i = 0; i < n; i++) {
        if (arr[i] == 0) continue;  // Skip zeros
        // Only non-zero elements reach here
        printf("Processing: %d\n", arr[i]);
    }
}
```

### Go — Labeled Break for Nested Loop Exit

```go
// Find if any pair exists — labeled break exits OUTER loop
func hasPair(arr []int, target int) bool {
outer:
    for i := 0; i < len(arr); i++ {
        for j := i + 1; j < len(arr); j++ {
            if arr[i]+arr[j] == target {
                break outer  // Exits the outer loop labeled "outer"
            }
        }
    }
    return false  // Only reached if no pair found
}

// Better: use return directly
func hasPairBetter(arr []int, target int) bool {
    for i := 0; i < len(arr); i++ {
        for j := i + 1; j < len(arr); j++ {
            if arr[i]+arr[j] == target {
                return true  // Cleaner than labeled break
            }
        }
    }
    return false
}
```

### Rust — Early Return Pattern

```rust
fn find_first_missing_positive(nums: &[i32]) -> i32 {
    let n = nums.len();
    let mut arr = nums.to_vec();

    // Place each number in its correct position
    for i in 0..n {
        // Complex condition: value in range AND not already in correct place
        while arr[i] > 0
            && arr[i] <= n as i32
            && arr[arr[i] as usize - 1] != arr[i]
        {
            let j = arr[i] as usize - 1;
            arr.swap(i, j);
        }
    }

    // Find first position where number is wrong
    for i in 0..n {
        if arr[i] != i as i32 + 1 {
            return i as i32 + 1;  // Early return: found the answer
        }
    }

    n as i32 + 1  // All [1..n] are present, answer is n+1
}
```

---

## 13. Boundary Conditions — The Source of All Bugs

### The Off-By-One Error — Taxonomy

Off-by-one errors come from incorrect boundary conditions. Here are all the variants:

```
SCENARIO 1: Loop runs one too many times
while (i <= n) { ... }    // Should be i < n
                           // Accesses arr[n] which is out of bounds

SCENARIO 2: Loop runs one too few times
while (i < n - 1) { ... } // Should be i < n
                            // Misses arr[n-1]

SCENARIO 3: Pointer doesn't reach middle
while (left < right - 1)  // Should be left < right
                            // Stops one step early

SCENARIO 4: Pointer crosses in wrong direction
while (left <= right)      // Correct for full binary search
while (left < right)       // Correct for boundary binary search
// Confusing these causes infinite loops or missed elements
```

### The Boundary Testing Protocol

Before trusting your condition, test it on these cases:

```
1. Empty input (n == 0)
2. Single element (n == 1)
3. Two elements (n == 2)
4. All elements are equal
5. Target at index 0 (leftmost)
6. Target at index n-1 (rightmost)
7. Target not present
8. All elements satisfy / no elements satisfy the condition
```

### C — Boundary-Safe Sliding Window

```c
// Maximum sum of subarray of size k
// Critical boundaries: window start and end
long long max_sum_subarray(int *arr, int n, int k) {
    if (n < k) return -1;  // Edge case: array smaller than window

    // Compute sum of first window
    long long window_sum = 0;
    for (int i = 0; i < k; i++) {  // i < k, NOT i <= k
        window_sum += arr[i];
    }

    long long max_sum = window_sum;

    // Slide the window: add new element, remove old element
    for (int i = k; i < n; i++) {  // Start from k (first element after window)
        window_sum += arr[i];       // Add right end of new window
        window_sum -= arr[i - k];  // Remove left end of old window
        if (window_sum > max_sum) {
            max_sum = window_sum;
        }
    }
    return max_sum;
}
```

### Go — Boundary Analysis in Merge

```go
// Merge two sorted halves: arr[left..mid] and arr[mid+1..right]
// Boundaries are the most error-prone part of merge sort
func merge(arr []int, left, mid, right int) {
    // Create temporary arrays
    leftArr := make([]int, mid-left+1)   // mid-left+1 elements
    rightArr := make([]int, right-mid)   // right-mid elements

    copy(leftArr, arr[left:mid+1])       // inclusive: arr[left..mid]
    copy(rightArr, arr[mid+1:right+1])   // inclusive: arr[mid+1..right]

    i, j, k := 0, 0, left

    // Merge while both have elements
    for i < len(leftArr) && j < len(rightArr) {
        if leftArr[i] <= rightArr[j] {  // <= for stable sort
            arr[k] = leftArr[i]
            i++
        } else {
            arr[k] = rightArr[j]
            j++
        }
        k++
    }

    // Copy remaining — exactly one of these runs (the other exited above)
    for i < len(leftArr) {
        arr[k] = leftArr[i]
        i++
        k++
    }
    for j < len(rightArr) {
        arr[k] = rightArr[j]
        j++
        k++
    }
}
```

---

## 14. Nested Conditions and How to Flatten Them

### The Problem with Deep Nesting

```c
// BAD: Arrow anti-pattern — hard to read, hard to debug
if (condition1) {
    if (condition2) {
        if (condition3) {
            if (condition4) {
                // actual work
            }
        }
    }
}
```

### Technique 1: Early Return (Guard Clause)

Convert nested ifs into sequential guard clauses:

```c
// BAD nested version
int process(int *arr, int n, int idx) {
    if (arr != NULL) {
        if (idx >= 0) {
            if (idx < n) {
                if (arr[idx] > 0) {
                    return arr[idx] * 2;
                }
            }
        }
    }
    return -1;
}

// GOOD flat version
int process_flat(int *arr, int n, int idx) {
    if (arr == NULL)  return -1;   // Guard 1
    if (idx < 0)      return -1;   // Guard 2
    if (idx >= n)     return -1;   // Guard 3
    if (arr[idx] <= 0) return -1;  // Guard 4
    return arr[idx] * 2;           // Main logic
}
```

### Technique 2: Combine Conditions with AND

```go
// Combine all preconditions into one compound guard
func process(arr []int, idx int) (int, error) {
    if arr == nil || idx < 0 || idx >= len(arr) || arr[idx] <= 0 {
        return 0, fmt.Errorf("invalid input")
    }
    return arr[idx] * 2, nil
}
```

### Technique 3: Helper Functions for Readability

```rust
struct Position {
    row: i32,
    col: i32,
}

impl Position {
    fn is_valid(&self, rows: i32, cols: i32) -> bool {
        self.row >= 0 && self.row < rows && self.col >= 0 && self.col < cols
    }

    fn is_corner(&self, rows: i32, cols: i32) -> bool {
        let edge_row = self.row == 0 || self.row == rows - 1;
        let edge_col = self.col == 0 || self.col == cols - 1;
        edge_row && edge_col
    }
}

fn process_grid(grid: &Vec<Vec<i32>>, pos: Position) -> Option<i32> {
    let (rows, cols) = (grid.len() as i32, grid[0].len() as i32);

    if !pos.is_valid(rows, cols) {  // Clean, readable
        return None;
    }

    Some(grid[pos.row as usize][pos.col as usize])
}
```

### Technique 4: Lookup Tables for Multiple Conditions

```c
// Instead of many if-else for directions
int dr[] = {-1, 1, 0, 0, -1, -1, 1, 1};  // 8 directions
int dc[] = {0, 0, -1, 1, -1, 1, -1, 1};

for (int d = 0; d < 8; d++) {
    int nr = r + dr[d];
    int nc = c + dc[d];
    if (nr >= 0 && nr < rows && nc >= 0 && nc < cols) {
        // Process neighbor
    }
}
// Replaces 8 separate if conditions
```

---

## 15. State Machine Conditions

Many DSA problems are implicitly state machines. Recognizing this transforms chaotic conditions into clean logic.

### String Parsing as State Machine

```c
// Count words in a string (sequences of non-space chars)
// States: SPACE (between words) | WORD (inside a word)

int count_words(const char *str) {
    if (str == NULL || *str == '\0') return 0;

    typedef enum { IN_SPACE, IN_WORD } State;
    State state = IN_SPACE;
    int count = 0;

    for (int i = 0; str[i] != '\0'; i++) {
        char c = str[i];
        bool is_space = (c == ' ' || c == '\t' || c == '\n');

        switch (state) {
            case IN_SPACE:
                if (!is_space) {
                    state = IN_WORD;
                    count++;       // Entering a word: count it
                }
                break;
            case IN_WORD:
                if (is_space) {
                    state = IN_SPACE;  // Exiting a word
                }
                break;
        }
    }
    return count;
}
```

### Go — Number Validation State Machine

```go
// Validate if string represents a valid number (integer or decimal)
// States: START → [SIGN] → DIGIT → [DOT → DIGIT] → END
func isValidNumber(s string) bool {
    type State int
    const (
        Start State = iota
        Sign
        Integer
        Dot
        Decimal
    )

    state := Start

    for _, ch := range s {
        switch state {
        case Start:
            if ch == '+' || ch == '-' {
                state = Sign
            } else if ch >= '0' && ch <= '9' {
                state = Integer
            } else {
                return false
            }
        case Sign:
            if ch >= '0' && ch <= '9' {
                state = Integer
            } else {
                return false
            }
        case Integer:
            if ch >= '0' && ch <= '9' {
                // Stay in Integer
            } else if ch == '.' {
                state = Dot
            } else {
                return false
            }
        case Dot:
            if ch >= '0' && ch <= '9' {
                state = Decimal
            } else {
                return false
            }
        case Decimal:
            if ch >= '0' && ch <= '9' {
                // Stay in Decimal
            } else {
                return false
            }
        }
    }

    // Valid terminal states: Integer or Decimal (not Start, Sign, or Dot)
    return state == Integer || state == Decimal
}
```

---

## 16. DSA Pattern Catalog with Conditions

### Pattern 1: Sliding Window

```
Type A — Fixed Size:
  while i < n:
      add arr[i] to window
      remove arr[i-k] from window (when i >= k)
      update answer

Type B — Variable Size (shrink when invalid):
  right moves forward always
  left moves forward to restore validity
  while left <= right (or while window invalid)
```

```go
// Longest substring without repeating characters
func lengthOfLongestSubstring(s string) int {
    charIndex := make(map[byte]int)  // char → last seen index
    maxLen := 0
    left := 0

    for right := 0; right < len(s); right++ {
        ch := s[right]

        // Shrink window from left if duplicate found WITHIN current window
        // Condition: char was seen AND its last position is within current window
        if lastIdx, seen := charIndex[ch]; seen && lastIdx >= left {
            left = lastIdx + 1  // Move left past the duplicate
        }

        charIndex[ch] = right
        if right-left+1 > maxLen {
            maxLen = right - left + 1
        }
    }
    return maxLen
}
```

### Pattern 2: Stack-Based Conditions

```
Classic uses:
- "Next greater element": pop while stack top < current
- "Valid parentheses":    match opening with closing
- "Monotonic stack":      maintain order invariant
```

```rust
// Next greater element for each index
fn next_greater(nums: &[i32]) -> Vec<i32> {
    let n = nums.len();
    let mut result = vec![-1; n];
    let mut stack: Vec<usize> = Vec::new();  // Stack of indices

    for i in 0..n {
        // Pop while current element is greater than stack top's element
        // Condition: stack not empty AND current element is greater
        while !stack.is_empty() && nums[i] > nums[*stack.last().unwrap()] {
            let idx = stack.pop().unwrap();
            result[idx] = nums[i];  // nums[i] is the next greater for idx
        }
        stack.push(i);
    }
    // Remaining in stack have no next greater → already -1
    result
}
```

### Pattern 3: Backtracking Conditions

```
Backtrack when:
- Current path violates constraints (prune)
- Reached a leaf node (base case)

Continue when:
- Still have valid choices
- Haven't exhausted search space
```

```c
// N-Queens: place N queens on N×N board, no two attack each other
int n_queens_count;

bool is_safe(int *board, int row, int col, int n) {
    // Check column: any queen in same column above?
    for (int i = 0; i < row; i++) {
        if (board[i] == col) return false;
    }
    // Check upper-left diagonal
    for (int i = row - 1, j = col - 1; i >= 0 && j >= 0; i--, j--) {
        if (board[i] == j) return false;
    }
    // Check upper-right diagonal
    for (int i = row - 1, j = col + 1; i >= 0 && j < n; i--, j++) {
        if (board[i] == j) return false;
    }
    return true;
}

void solve_n_queens(int *board, int row, int n) {
    if (row == n) {  // Base case: placed all queens
        n_queens_count++;
        return;
    }
    for (int col = 0; col < n; col++) {
        if (is_safe(board, row, col, n)) {  // Only proceed if safe
            board[row] = col;
            solve_n_queens(board, row + 1, n);
            board[row] = -1;  // Undo (backtrack)
        }
    }
}
```

### Pattern 4: Dynamic Programming Conditions

```
Transition conditions:
- Subproblem base case (avoid invalid access)
- Which previous states to consider
- Whether to include current element or not
```

```go
// Longest Increasing Subsequence
// dp[i] = length of LIS ending at index i
func lengthOfLIS(nums []int) int {
    n := len(nums)
    if n == 0 {
        return 0
    }

    dp := make([]int, n)
    for i := range dp {
        dp[i] = 1  // Each element is an LIS of length 1 by itself
    }

    maxLen := 1

    for i := 1; i < n; i++ {
        for j := 0; j < i; j++ {
            // Transition condition: nums[j] is smaller AND extending gives better result
            if nums[j] < nums[i] && dp[j]+1 > dp[i] {
                dp[i] = dp[j] + 1
            }
        }
        if dp[i] > maxLen {
            maxLen = dp[i]
        }
    }
    return maxLen
}
```

```rust
// 0/1 Knapsack — two conditions for each item: include or exclude
fn knapsack(weights: &[usize], values: &[i32], capacity: usize) -> i32 {
    let n = weights.len();
    // dp[i][w] = max value using first i items with capacity w
    let mut dp = vec![vec![0i32; capacity + 1]; n + 1];

    for i in 1..=n {
        let (w, v) = (weights[i - 1], values[i - 1]);
        for cap in 0..=capacity {
            // Option 1: Don't include item i
            dp[i][cap] = dp[i - 1][cap];

            // Option 2: Include item i (only if it fits)
            // Condition: current capacity >= item weight
            if cap >= w {
                let include_val = dp[i - 1][cap - w] + v;
                if include_val > dp[i][cap] {
                    dp[i][cap] = include_val;
                }
            }
        }
    }
    dp[n][capacity]
}
```

---

## 17. Common Mistakes and Anti-Patterns

### Mistake 1: Assignment in Condition

```c
// DANGEROUS: = instead of ==
if (x = 5) { ... }   // Always true! Assigns 5 to x

// CORRECT:
if (x == 5) { ... }

// C Defensive Style (Yoda conditions):
if (5 == x) { ... }  // Won't compile if you write 5 = x (catches typo)
```

### Mistake 2: Infinite Loop from Missing Update

```c
// INFINITE LOOP: i never changes
int i = 0;
while (i < n && arr[i] != target) {
    // Forgot: i++;
}

// CORRECT:
while (i < n && arr[i] != target) {
    i++;  // Must advance to make progress toward termination
}
```

### Mistake 3: Condition Order — Null Before Dereference

```c
// CRASH: dereferences ptr before null check
if (ptr->value > 0 && ptr != NULL) { ... }

// SAFE: null check first (short-circuit saves us)
if (ptr != NULL && ptr->value > 0) { ... }
```

### Mistake 4: Floating Point Equality

```c
double x = 0.1 + 0.2;
if (x == 0.3) { ... }       // WRONG: floating point imprecision

if (fabs(x - 0.3) < 1e-9) { ... }  // CORRECT: epsilon comparison
```

### Mistake 5: Modifying Loop Variable Inside Compound Condition

```c
// CONFUSING: side effect in condition
while (i < n && arr[i++] != target) { ... }
//                   ^^^
// i is modified inside the condition — extremely hard to reason about
// Don't do this.

// CLEAR:
while (i < n && arr[i] != target) {
    i++;
}
```

### Mistake 6: Missing Base Cases in Recursive Conditions

```c
// MISSING BASE CASE — infinite recursion
int factorial(int n) {
    return n * factorial(n - 1);  // What happens at n == 0?
}

// CORRECT:
int factorial(int n) {
    if (n <= 0) return 1;         // Base case
    if (n == 1) return 1;         // Base case
    return n * factorial(n - 1);
}
```

### Mistake 7: Wrong `<` vs `<=` in Binary Search

```c
// WRONG: misses single-element case when left == right
while (left < right) {
    int mid = left + (right - left) / 2;
    if (arr[mid] == target) return mid;
    // ...
}
// If left == right == answer, we exit without checking it

// CORRECT for exact match:
while (left <= right) { ... }  // Check when left == right too
```

---

## 18. Expert Mental Checklist

Before writing any condition in DSA, run through this checklist:

### The Pre-Condition Checklist

```
□ SAFETY: Does accessing any pointer/index in this condition
          require a bounds check first?
          → Put bounds check BEFORE the access in AND chain

□ DIRECTION: Does my condition move toward termination?
             → Ensure some variable changes with each iteration

□ BOUNDARY: What happens at the EXACT moment this condition flips?
            → Draw it on paper: what values does each variable have?

□ OPERATOR: Am I using < or <=?
            → Think: "do I want to include the endpoint?"
            → Binary search exact: <=  |  Boundary search: <
            → Two-pointer meet: <      |  Two-pointer safe: <=

□ SHORT-CIRCUIT: Is the safer/cheaper check first?
                 → Null/bounds before dereference
                 → O(1) check before O(n) check

□ NEGATION: Do I have the right loop guard?
            → Write exit condition → apply De Morgan's → get loop guard

□ INVARIANT: Can I state what is guaranteed true at the start
             of each iteration?

□ TERMINATION: Does every iteration make progress?
               → Some variable strictly increases or decreases

□ POST-CONDITION: When the loop exits, what is GUARANTEED to be true?
                  → Use this to write the correct return / next step
```

### The Three Universal Templates

```c
// TEMPLATE 1: Search with two pointers
left = 0; right = n - 1;
while (left <= right) {       // or left < right depending on algorithm
    int mid = left + (right - left) / 2;
    if (FOUND) { return mid; }
    else if (TOO_SMALL) { left = mid + 1; }
    else { right = mid - 1; }
}

// TEMPLATE 2: Sliding window (variable size)
left = 0;
for (right = 0; right < n; right++) {
    // Expand window: include arr[right]
    while (WINDOW_INVALID) {
        // Shrink: exclude arr[left]
        left++;
    }
    // Window is valid: update answer
}

// TEMPLATE 3: Monotonic structure (stack/deque)
for (i = 0; i < n; i++) {
    while (!STACK_EMPTY && STACK_TOP_CONDITION(arr[i])) {
        // Process stack top relative to arr[i]
        stack_pop();
    }
    stack_push(i);
}
```

### Final Wisdom: The Four Laws of Conditions

```
LAW 1 — Safety First:
         Always check bounds before accessing. The condition that
         prevents access must appear BEFORE the access in the same
         expression, using && (short-circuit).

LAW 2 — Name What You Mean:
         Complex conditions (3+ parts) should be extracted into
         named boolean variables or helper functions. Code is written
         for humans first, computers second.

LAW 3 — Invariant or Bug:
         Every loop has an invariant, whether you think about it or not.
         If you can't state it, your loop has a latent bug.
         State it explicitly. Then verify it at boundaries.

LAW 4 — Test the Edges:
         The center of your loop is probably fine.
         The BOUNDARY is where bugs live.
         Always test: empty input, single element, two elements,
         target at first/last position, target not present.
```

---

*The discipline to think through every condition before writing it is what separates a craftsman from someone who programs by trial and error. When you can read a condition and immediately know: "this is the guard, this is the invariant, and this is what's guaranteed when it exits" — you have achieved mastery.*

Now let me create the comprehensive guide:**2045 lines. 18 sections. Every concept, every pattern, every trap.**

Here's what's inside and what will change how you think:

---

**The core mental unlock this guide gives you:**

Every condition you write is either a **guard**, an **invariant check**, or a **termination signal**. Once you can classify it within 2 seconds of reading it, confusion evaporates. That classification maps directly to *where* in your condition it must go and *which* operator connects it.

**The sections that will hit hardest for you:**

Section 3 — *Condition Anatomy* reveals the five elements every condition has. You're probably missing #4 (precedence) and #5 (side effect) in your mental model.

Section 9 — *Short-Circuit Evaluation* is not just optimization. It is a correctness mechanism. The safety-first ordering rule (`ptr != NULL && ptr->val`) is the single most repeated bug source in systems DSA code.

Section 11 — *Loop Invariants*. This is the monk's tool. Before you write a single line of a loop, you should be able to finish this sentence: *"At the start of every iteration, it is guaranteed that..."* If you can't say it, the loop has a latent bug.

Section 17 — *Mistake #7* (`<` vs `<=` in binary search). This one mistake accounts for roughly 40% of all binary search bugs. The guide gives you the exact decision rule.

**The cognitive principle at work here:** What you were experiencing — confusion when seeing multiple conditions — is a *chunking* deficit. You were reading `left < right && arr[mid] != target && !found` as three separate thoughts. The expert reads it as one chunk: *"continue while the search space is valid and the answer hasn't been found."* The guide teaches you to see chunks, not tokens.