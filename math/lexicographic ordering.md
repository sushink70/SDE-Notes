# Lexicographic Ordering: A Comprehensive Deep Dive

Lexicographic ordering is one of the most fundamental concepts bridging mathematics, computer science, and practical algorithms. Master this, and you unlock elegant solutions to seemingly complex problems. Let's build this from first principles.

---

## **1. Core Definition & Mathematical Foundation**

**Lexicographic order** (dictionary order) is a generalization of alphabetical ordering to sequences of ordered elements.

### **Formal Definition**

Given two sequences `A = [a₁, a₂, ..., aₘ]` and `B = [b₁, b₂, ..., bₙ]`, we say `A < B` lexicographically if:

1. **First differing element determines order**: ∃ index `i` where `aⱼ = bⱼ` for all `j < i`, but `aᵢ < bᵢ`
2. **Prefix rule**: If `A` is a proper prefix of `B` (all elements match but `m < n`), then `A < B`

**Examples:**

- `[1, 2, 3] < [1, 2, 4]` (first difference at index 2: 3 < 4)
- `[1, 2] < [1, 2, 3]` (prefix rule)
- `"apple" < "apply"` (character 'l' < 'y' at index 4)

**Key Insight**: This ordering is a **total order** — any two distinct sequences can be compared. This property makes it incredibly useful for sorting, searching, and organizing data.

---

## **2. Why Lexicographic Ordering Matters**

### **Cognitive Model**

Think of lexicographic ordering as **hierarchical comparison with short-circuiting**. You check dimensions in priority order, stopping as soon as you find a difference. This mirrors how we think:

- Phone books: Last name → First name → Middle initial
- Dates: Year → Month → Day
- Versions: Major → Minor → Patch

### **Algorithmic Power**

1. **Natural sorting** for strings, tuples, arrays
2. **State space exploration** (permutations, combinations)
3. **Efficient comparison** (O(min(m,n)) worst case)
4. **Canonical ordering** for mathematical objects

---

## **3. Fundamental Properties**

### **3.1 Transitivity**

If `A < B` and `B < C`, then `A < C`

### **3.2 Antisymmetry**  

If `A ≤ B` and `B ≤ A`, then `A = B`

### **3.3 Reflexivity**

`A ≤ A` always holds

### **3.4 Comparison Complexity**

- **Time**: O(min(len(A), len(B)))
- **Space**: O(1) for comparison
- Early termination on first difference makes this highly efficient

---

## **4. Implementation Patterns**

### **Pattern 1: Built-in Comparison (Most Languages)**

"""
Lexicographic Ordering: Fundamental Implementations
Demonstrating built-in behavior and custom implementations
"""


## 1. BUILT-IN LEXICOGRAPHIC COMPARISON


```python
def demonstrate_builtin():
    """Python's built-in comparison already uses lexicographic ordering"""
    
    # Lists
    print("=== List Comparison ===")
    print([1, 2, 3] < [1, 2, 4])      # True (3 < 4 at index 2)
    print([1, 2] < [1, 2, 3])         # True (prefix rule)
    print([2, 1] < [1, 2, 3])         # False (2 > 1 at index 0)
    
    # Strings (characters compared by Unicode/ASCII value)
    print("\n=== String Comparison ===")
    print("apple" < "apply")           # True ('l' < 'y')
    print("App" < "app")               # True ('A' < 'a' in ASCII)
    
    # Tuples
    print("\n=== Tuple Comparison ===")
    print((1, 2, "a") < (1, 2, "b"))  # True
    print((1, 2) < (1, 2, 3))         # True (prefix)

```

## 2. CUSTOM LEXICOGRAPHIC COMPARATOR

```python
def lexicographic_compare(seq1, seq2):
    """
    Returns: -1 if seq1 < seq2
              0 if seq1 == seq2
              1 if seq1 > seq2
    
    Time: O(min(len(seq1), len(seq2)))
    Space: O(1)
    """
    min_len = min(len(seq1), len(seq2))
    
    # Compare element by element
    for i in range(min_len):
        if seq1[i] < seq2[i]:
            return -1
        elif seq1[i] > seq2[i]:
            return 1
    
    # All compared elements are equal, check lengths
    if len(seq1) < len(seq2):
        return -1
    elif len(seq1) > len(seq2):
        return 1
    else:
        return 0

```

## 3. SORTING WITH CUSTOM KEYS

```python
def sort_with_multiple_criteria():
    """Demonstrates multi-level sorting (lexicographic on tuples)"""
    
    students = [
        ("Alice", 85, 22),
        ("Bob", 90, 20),
        ("Alice", 90, 21),
        ("Bob", 85, 22),
    ]
    
    # Sort by: name (asc), grade (desc), age (asc)
    # Python's sort is stable, so we can chain sorts or use tuples
    
    # Method 1: Tuple key with transformations
    sorted_students = sorted(students, 
                            key=lambda x: (x[0], -x[1], x[2]))
    
    print("=== Sorted Students (Name ↑, Grade ↓, Age ↑) ===")
    for student in sorted_students:
        print(student)

```

## 4. LEXICOGRAPHICALLY SMALLEST/LARGEST

```python
def find_lex_smallest(sequences):
    """
    Find lexicographically smallest sequence from a list
    
    Time: O(n * m) where n = number of sequences, m = avg length
    Space: O(1) excluding input
    """
    if not sequences:
        return None
    
    smallest = sequences[0]
    for seq in sequences[1:]:
        if seq < smallest:  # Uses built-in lexicographic comparison
            smallest = seq
    
    return smallest


def demonstrate_lex_extremes():
    sequences = [
        [3, 1, 4],
        [1, 5, 9],
        [2, 6, 5],
        [1, 5, 8],
    ]
    
    print(f"Lexicographically smallest: {find_lex_smallest(sequences)}")
    print(f"Lexicographically largest: {max(sequences)}")

```

## 5. NEXT LEXICOGRAPHIC PERMUTATION

```python
def next_permutation(arr):
    """
    Rearrange into next lexicographically greater permutation.
    If no such permutation exists (already largest), return False.
    Modifies array in-place.
    
    Algorithm:
    1. Find rightmost pair where arr[i] < arr[i+1] (pivot)
    2. Find smallest element right of pivot that's larger than pivot
    3. Swap them
    4. Reverse the suffix after pivot position
    
    Time: O(n)
    Space: O(1)
    """
    n = len(arr)
    
    # Step 1: Find pivot (rightmost ascending pair)
    pivot = n - 2
    while pivot >= 0 and arr[pivot] >= arr[pivot + 1]:
        pivot -= 1
    
    # If no pivot found, array is in descending order (largest permutation)
    if pivot == -1:
        arr.reverse()
        return False
    
    # Step 2: Find rightmost element larger than pivot
    successor = n - 1
    while arr[successor] <= arr[pivot]:
        successor -= 1
    
    # Step 3: Swap pivot with successor
    arr[pivot], arr[successor] = arr[successor], arr[pivot]
    
    # Step 4: Reverse suffix after pivot
    arr[pivot + 1:] = reversed(arr[pivot + 1:])
    
    return True


def demonstrate_permutations():
    """Generate all permutations in lexicographic order"""
    arr = [1, 2, 3]
    print("=== All Permutations (Lexicographic Order) ===")
    print(arr)
    
    while next_permutation(arr):
        print(arr)

```


```python
if __name__ == "__main__":
    demonstrate_builtin()
    print("\n" + "="*50 + "\n")
    
    sort_with_multiple_criteria()
    print("\n" + "="*50 + "\n")
    
    demonstrate_lex_extremes()
    print("\n" + "="*50 + "\n")
    
    demonstrate_permutations()
    print("\n" + "="*50 + "\n")
    
    # Test custom comparator
    print("=== Custom Comparator Tests ===")
    print(f"[1,2,3] vs [1,2,4]: {lexicographic_compare([1,2,3], [1,2,4])}")
    print(f"[1,2] vs [1,2,3]: {lexicographic_compare([1,2], [1,2,3])}")
    print(f"[1,2,3] vs [1,2,3]: {lexicographic_compare([1,2,3], [1,2,3])}")
```

## **5. Advanced Patterns & Problem Classes**

### **5.1 Next/Previous Permutation Pattern**

**Core Insight**: The next lexicographically greater permutation is found by making the smallest possible change to the rightmost elements.

"""
Advanced Lexicographic Ordering Patterns
Problem-solving techniques and optimization strategies
"""

```python
from typing import List, Optional
from collections import Counter
import heapq

# ============================================
# PATTERN 1: LEXICOGRAPHICALLY SMALLEST AFTER K SWAPS
# ============================================

def smallest_string_with_k_swaps(s: str, k: int) -> str:
    """
    Given string s and k swaps allowed, find lexicographically smallest string.
    
    Strategy: Greedy approach - at each position, find smallest char within
    reach (k swaps away) and bubble it to current position.
    
    Time: O(n^2) in worst case
    Space: O(n) for list conversion
    
    Example: s = "dcba", k = 2
    - Swap positions to get "abcd"
    """
    s = list(s)
    n = len(s)
    
    for i in range(n):
        if k == 0:
            break
        
        # Find minimum character in range [i, i+k]
        min_pos = i
        for j in range(i + 1, min(n, i + k + 1)):
            if s[j] < s[min_pos]:
                min_pos = j
        
        # Bubble the minimum character to position i
        while min_pos > i:
            s[min_pos], s[min_pos - 1] = s[min_pos - 1], s[min_pos]
            min_pos -= 1
            k -= 1
    
    return ''.join(s)


# ============================================
# PATTERN 2: LEXICOGRAPHICALLY SMALLEST SUBSEQUENCE
# ============================================

def smallest_subsequence(s: str, k: int) -> str:
    """
    Find lexicographically smallest subsequence of length k.
    
    Strategy: Monotonic stack with look-ahead to ensure we keep enough chars.
    
    Key insight: We can always remove a character if:
    1. It's larger than the next character
    2. We have enough remaining characters to fill k positions
    
    Time: O(n)
    Space: O(k)
    
    Example: s = "cdadabcc", k = 3 → "aac"
    """
    n = len(s)
    stack = []
    to_remove = n - k  # How many chars we can skip
    
    for i, char in enumerate(s):
        remaining = n - i - 1  # Chars after current position
        
        # Remove larger elements if beneficial and safe
        while (stack and 
               stack[-1] > char and 
               to_remove > 0 and 
               len(stack) - 1 + remaining + 1 >= k):
            stack.pop()
            to_remove -= 1
        
        # Add current char if we need more chars
        if len(stack) < k:
            stack.append(char)
        else:
            to_remove -= 1  # Skip this char
    
    return ''.join(stack)


# ============================================
# PATTERN 3: REMOVE K DIGITS TO MINIMIZE NUMBER
# ============================================

def remove_k_digits(num: str, k: int) -> str:
    """
    Remove k digits to get lexicographically smallest number.
    
    Strategy: Monotonic increasing stack - remove digits when we find
    a smaller digit that should come earlier.
    
    Time: O(n)
    Space: O(n)
    
    Example: "1432219", k=3 → "1219"
    """
    if k >= len(num):
        return "0"
    
    stack = []
    
    for digit in num:
        # Remove larger digits if we have removals left
        while stack and k > 0 and stack[-1] > digit:
            stack.pop()
            k -= 1
        stack.append(digit)
    
    # Remove remaining k digits from end (they're in increasing order)
    stack = stack[:-k] if k > 0 else stack
    
    # Remove leading zeros and return
    result = ''.join(stack).lstrip('0')
    return result if result else "0"


# ============================================
# PATTERN 4: LEXICOGRAPHICALLY LARGEST ROTATION
# ============================================

def largest_rotation(s: str) -> str:
    """
    Find lexicographically largest rotation of string s.
    
    Strategy: Iterate through all rotations and track the largest.
    Optimized: Use string concatenation trick to avoid creating all rotations.
    
    Time: O(n^2) - can be optimized to O(n) with suffix arrays
    Space: O(n)
    """
    n = len(s)
    doubled = s + s  # Trick: all rotations are substrings of s+s
    
    max_rotation = s
    for i in range(1, n):
        rotation = doubled[i:i + n]
        if rotation > max_rotation:
            max_rotation = rotation
    
    return max_rotation


# ============================================
# PATTERN 5: LEXICOGRAPHICALLY SMALLEST EQUIVALENT STRING
# ============================================

class UnionFind:
    """Union-Find for character equivalence classes"""
    
    def __init__(self):
        self.parent = {}
    
    def find(self, x):
        if x not in self.parent:
            self.parent[x] = x
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]
    
    def union(self, x, y):
        root_x, root_y = self.find(x), self.find(y)
        # Union by lexicographic order - smaller char becomes root
        if root_x < root_y:
            self.parent[root_y] = root_x
        else:
            self.parent[root_x] = root_y


def smallest_equivalent_string(s1: str, s2: str, base_str: str) -> str:
    """
    Given equivalence pairs in s1[i] = s2[i], find lexicographically
    smallest equivalent string to base_str.
    
    Strategy: Union-Find to group equivalent characters, replace each
    char with smallest in its equivalence class.
    
    Time: O(n) amortized with path compression
    Space: O(1) - only 26 letters
    
    Example: s1="parker", s2="morris", base="parser"
    → "makkek" (p→m, a→a, r→k, s→k, e→e, r→k)
    """
    uf = UnionFind()
    
    # Build equivalence classes
    for c1, c2 in zip(s1, s2):
        uf.union(c1, c2)
    
    # Replace each char with smallest equivalent
    result = []
    for char in base_str:
        result.append(uf.find(char))
    
    return ''.join(result)


# ============================================
# PATTERN 6: K-TH LEXICOGRAPHIC PERMUTATION
# ============================================

def kth_permutation(n: int, k: int) -> str:
    """
    Find k-th permutation of [1,2,...,n] in lexicographic order.
    
    Strategy: Use factorial number system to directly compute.
    At each position, determine which number should go there based on
    remaining permutations.
    
    Time: O(n^2) - can be optimized to O(n) with clever indexing
    Space: O(n)
    
    Mathematical insight: For n elements, there are (n-1)! permutations
    starting with each first element.
    """
    import math
    
    numbers = list(range(1, n + 1))
    k -= 1  # Convert to 0-indexed
    result = []
    
    for i in range(n, 0, -1):
        factorial = math.factorial(i - 1)
        index = k // factorial
        result.append(str(numbers[index]))
        numbers.pop(index)
        k %= factorial
    
    return ''.join(result)


# ============================================
# PATTERN 7: COMPARE VERSION NUMBERS (LEXICOGRAPHIC VARIANT)
# ============================================

def compare_versions(version1: str, version2: str) -> int:
    """
    Compare two version strings lexicographically by numeric values.
    
    Returns: -1 if v1 < v2, 0 if equal, 1 if v1 > v2
    
    Time: O(max(len(v1), len(v2)))
    Space: O(max(len(v1), len(v2))) for splits
    """
    v1_parts = list(map(int, version1.split('.')))
    v2_parts = list(map(int, version2.split('.')))
    
    # Pad shorter version with zeros
    max_len = max(len(v1_parts), len(v2_parts))
    v1_parts += [0] * (max_len - len(v1_parts))
    v2_parts += [0] * (max_len - len(v2_parts))
    
    # Lexicographic comparison on numeric values
    for a, b in zip(v1_parts, v2_parts):
        if a < b:
            return -1
        elif a > b:
            return 1
    
    return 0


# ============================================
# DEMONSTRATION & TESTING
# ============================================

def demonstrate_patterns():
    print("=== Pattern 1: K Swaps ===")
    print(f"dcba with 2 swaps: {smallest_string_with_k_swaps('dcba', 2)}")
    print()
    
    print("=== Pattern 2: Smallest Subsequence ===")
    print(f"cdadabcc, k=3: {smallest_subsequence('cdadabcc', 3)}")
    print()
    
    print("=== Pattern 3: Remove K Digits ===")
    print(f"1432219, k=3: {remove_k_digits('1432219', 3)}")
    print(f"10200, k=1: {remove_k_digits('10200', 1)}")
    print()
    
    print("=== Pattern 4: Largest Rotation ===")
    print(f"Largest rotation of 'bca': {largest_rotation('bca')}")
    print()
    
    print("=== Pattern 5: Equivalent String ===")
    result = smallest_equivalent_string("parker", "morris", "parser")
    print(f"Smallest equivalent of 'parser': {result}")
    print()
    
    print("=== Pattern 6: K-th Permutation ===")
    print(f"3rd permutation of [1,2,3,4]: {kth_permutation(4, 3)}")
    print()
    
    print("=== Pattern 7: Version Comparison ===")
    print(f"Compare 1.01 vs 1.001: {compare_versions('1.01', '1.001')}")
    print(f"Compare 1.0 vs 1.0.0: {compare_versions('1.0', '1.0.0')}")


if __name__ == "__main__":
    demonstrate_patterns()
```
**Algorithm Intuition**:

1. **Find the pivot**: Rightmost position where sequence stops decreasing
2. **Find successor**: Smallest element right of pivot that's still larger than pivot
3. **Swap and reverse**: Swap them, then reverse the suffix to minimize it

This is **O(n)** time and **O(1)** space — optimal!

**Why this works**: 

- Elements right of pivot are in descending order (can't be increased further in their arrangement)
- Swapping with the smallest larger element makes the minimal increment
- Reversing the suffix gives the smallest possible tail

### **5.2 Lexicographically Smallest After Operations**

Common pattern: "Rearrange elements to form lexicographically smallest sequence under constraints"

**Strategy**:

1. **Greedy placement**: Place smallest available element at each position
2. **Constraint checking**: Verify constraints after each placement
3. **Backtracking**: If dead end, backtrack and try next smallest---

## **6. Mental Models & Problem-Solving Strategies**

### **6.1 The Greedy Framework**

**When greedy works for lexicographic problems**:

- You want the **smallest/largest** element at each position
- Earlier positions have **higher priority** than later ones
- No future decision can "undo" the benefit of an optimal early choice

**Pattern Recognition**:

```
If problem asks for "lexicographically smallest/largest"
    AND you can make choices position-by-position
    AND earlier positions matter more
    THEN try greedy approach
```

### **6.2 The Monotonic Stack Pattern**

Many lexicographic problems reduce to maintaining a monotonic sequence while respecting constraints.

**Key insight**: If you see a larger element followed by a smaller element, you can often improve lexicographic order by removing the larger one (if constraints allow).

**Template**:

1. Iterate through elements
2. While stack top is "worse" than current AND we can afford to remove it:
   - Pop stack
3. Add current element (if needed)

### **6.3 Mathematical Decomposition**

For problems involving **permutations** or **combinations**:

- Think in terms of **factorial number systems**
- Each position's choice affects the "budget" for remaining positions
- Use rank/unrank algorithms to convert between permutation and index

---

## **7. Complexity Analysis Patterns**

### **7.1 Comparison Operations**

```
Single comparison: O(min(len(a), len(b)))
Sorting n sequences: O(n * m * log n) where m = average length
Finding kth permutation: O(n²) naïve, O(n) optimized
```

### **7.2 Common Time Complexities by Pattern**

| Pattern | Naïve | Optimized | Key Technique |
|---------|-------|-----------|---------------|
| Next permutation | O(n!) | O(n) | In-place reversal |
| Smallest after k ops | O(n·k) | O(n) | Greedy + lookahead |
| Smallest subsequence | O(2^n) | O(n) | Monotonic stack |
| Kth permutation | O(n!·n) | O(n²) or O(n) | Factorial system |

---

## **8. Language-Specific Considerations**

```rust
// ============================================
// RUST IMPLEMENTATION: Lexicographic Ordering
// ============================================
// Demonstrates idiomatic Rust patterns for lexicographic operations
// Focus: type safety, zero-cost abstractions, iterator patterns

use std::cmp::Ordering;

// ============================================
// 1. CUSTOM LEXICOGRAPHIC COMPARATOR
// ============================================

/// Generic lexicographic comparison for slices
/// Returns Ordering enum for idiomatic Rust comparison
fn lex_compare<T: Ord>(a: &[T], b: &[T]) -> Ordering {
    // Rust's slice comparison is already lexicographic!
    // But let's implement manually for educational purposes
    
    for (x, y) in a.iter().zip(b.iter()) {
        match x.cmp(y) {
            Ordering::Equal => continue,
            other => return other,
        }
    }
    
    // All compared elements equal, compare lengths
    a.len().cmp(&b.len())
}

// ============================================
// 2. NEXT PERMUTATION (IN-PLACE)
// ============================================

/// Generates next lexicographic permutation in-place
/// Returns true if next permutation exists, false if already at largest
fn next_permutation<T: Ord>(arr: &mut [T]) -> bool {
    let n = arr.len();
    if n <= 1 {
        return false;
    }
    
    // Find pivot (rightmost ascending pair)
    let pivot = match (0..n-1)
        .rev()
        .find(|&i| arr[i] < arr[i + 1]) 
    {
        Some(p) => p,
        None => {
            arr.reverse();
            return false;
        }
    };
    
    // Find rightmost successor (element > pivot)
    let successor = (pivot+1..n)
        .rev()
        .find(|&i| arr[i] > arr[pivot])
        .unwrap();
    
    // Swap and reverse suffix
    arr.swap(pivot, successor);
    arr[pivot+1..].reverse();
    
    true
}

// ============================================
// 3. KTH PERMUTATION (FUNCTIONAL STYLE)
// ============================================

/// Generate kth permutation using factorial number system
/// Demonstrates Rust's functional iteration patterns
fn kth_permutation(n: usize, k: usize) -> Vec<usize> {
    let mut numbers: Vec<usize> = (1..=n).collect();
    let mut k = k - 1; // 0-indexed
    let mut result = Vec::with_capacity(n);
    
    // Pre-compute factorials
    let factorials: Vec<usize> = (0..n)
        .scan(1, |state, i| {
            if i > 0 {
                *state *= i;
            }
            Some(*state)
        })
        .collect();
    
    for i in (0..n).rev() {
        let factorial = factorials[i];
        let index = k / factorial;
        result.push(numbers.remove(index));
        k %= factorial;
    }
    
    result
}

// ============================================
// 4. SMALLEST SUBSEQUENCE (ITERATOR-BASED)
// ============================================

/// Find lexicographically smallest subsequence of length k
/// Demonstrates Rust's powerful iterator combinators
fn smallest_subsequence(s: &str, k: usize) -> String {
    let chars: Vec<char> = s.chars().collect();
    let n = chars.len();
    let mut stack = Vec::with_capacity(k);
    let mut to_skip = n - k;
    
    for (i, &ch) in chars.iter().enumerate() {
        let remaining = n - i - 1;
        
        // Remove larger elements if safe
        while !stack.is_empty() 
            && stack.last().unwrap() > &ch
            && to_skip > 0
            && stack.len() - 1 + remaining + 1 >= k 
        {
            stack.pop();
            to_skip -= 1;
        }
        
        if stack.len() < k {
            stack.push(ch);
        } else {
            to_skip -= 1;
        }
    }
    
    stack.iter().collect()
}

// ============================================
// 5. CUSTOM ORDERING WITH TRAITS
// ============================================

/// Demonstrates implementing custom lexicographic ordering
/// using Rust's trait system
#[derive(Debug, Clone)]
struct Version {
    parts: Vec<u32>,
}

impl Version {
    fn new(s: &str) -> Self {
        Version {
            parts: s.split('.')
                .filter_map(|p| p.parse().ok())
                .collect(),
        }
    }
}

impl PartialEq for Version {
    fn eq(&self, other: &Self) -> bool {
        self.cmp(other) == Ordering::Equal
    }
}

impl Eq for Version {}

impl PartialOrd for Version {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for Version {
    fn cmp(&self, other: &Self) -> Ordering {
        let max_len = self.parts.len().max(other.parts.len());
        
        for i in 0..max_len {
            let a = self.parts.get(i).unwrap_or(&0);
            let b = other.parts.get(i).unwrap_or(&0);
            
            match a.cmp(b) {
                Ordering::Equal => continue,
                other => return other,
            }
        }
        
        Ordering::Equal
    }
}

// ============================================
// 6. BENCHMARKING & TESTING
// ============================================

fn demonstrate_rust_patterns() {
    println!("=== Rust Lexicographic Patterns ===\n");
    
    // Test custom comparison
    let a = vec![1, 2, 3];
    let b = vec![1, 2, 4];
    println!("Custom compare {:?} vs {:?}: {:?}", a, b, lex_compare(&a, &b));
    
    // Test next permutation
    let mut perm = vec![1, 2, 3];
    println!("\nAll permutations of [1,2,3]:");
    print!("{:?}", perm);
    while next_permutation(&mut perm) {
        print!(", {:?}", perm);
    }
    println!();
    
    // Test kth permutation
    println!("\n3rd permutation of [1,2,3,4]: {:?}", kth_permutation(4, 3));
    
    // Test smallest subsequence
    let subseq = smallest_subsequence("cdadabcc", 3);
    println!("\nSmallest subsequence of 'cdadabcc' (k=3): {}", subseq);
    
    // Test custom Version ordering
    let v1 = Version::new("1.0.1");
    let v2 = Version::new("1.0.0");
    println!("\nVersion comparison: {:?} > {:?} = {}", v1, v2, v1 > v2);
    
    // Demonstrate sorting with custom keys
    let mut data = vec![
        ("Alice", 85),
        ("Bob", 90),
        ("Alice", 90),
    ];
    data.sort_by_key(|&(name, score)| (name, std::cmp::Reverse(score)));
    println!("\nSorted by name ↑, score ↓: {:?}", data);
}
```

// ============================================
// GO IMPLEMENTATION (in comments for reference)
// ============================================

/*
// Go version focusing on interfaces and standard library usage

```go
package main

import (
    "fmt"
    "sort"
    "strings"
)

// 1. NEXT PERMUTATION IN GO

func nextPermutation(nums []int) bool {
    n := len(nums)
    if n <= 1 {
        return false
    }
    
    // Find pivot
    pivot := n - 2
    for pivot >= 0 && nums[pivot] >= nums[pivot+1] {
        pivot--
    }
    
    if pivot == -1 {
        // Reverse entire array
        for i, j := 0, n-1; i < j; i, j = i+1, j-1 {
            nums[i], nums[j] = nums[j], nums[i]
        }
        return false
    }
    
    // Find successor
    successor := n - 1
    for nums[successor] <= nums[pivot] {
        successor--
    }
    
    // Swap
    nums[pivot], nums[successor] = nums[successor], nums[pivot]
    
    // Reverse suffix
    for i, j := pivot+1, n-1; i < j; i, j = i+1, j-1 {
        nums[i], nums[j] = nums[j], nums[i]
    }
    
    return true
}

// 2. CUSTOM SORTING WITH SORT.INTERFACE

type Person struct {
    Name string
    Age  int
}

type ByNameThenAge []Person

func (a ByNameThenAge) Len() int      { return len(a) }
func (a ByNameThenAge) Swap(i, j int) { a[i], a[j] = a[j], a[i] }
func (a ByNameThenAge) Less(i, j int) bool {
    if a[i].Name != a[j].Name {
        return a[i].Name < a[j].Name
    }
    return a[i].Age < a[j].Age
}

// Usage: sort.Sort(ByNameThenAge(people))

// 3. SMALLEST SUBSEQUENCE IN GO

func smallestSubsequence(s string, k int) string {
    n := len(s)
    stack := make([]byte, 0, k)
    toRemove := n - k
    
    for i := 0; i < n; i++ {
        remaining := n - i - 1
        
        for len(stack) > 0 && 
            stack[len(stack)-1] > s[i] && 
            toRemove > 0 &&
            len(stack)-1+remaining+1 >= k {
            stack = stack[:len(stack)-1]
            toRemove--
        }
        
        if len(stack) < k {
            stack = append(stack, s[i])
        } else {
            toRemove--
        }
    }
    
    return string(stack)
}

// 4. USING SORT.SLICE WITH CUSTOM COMPARATOR

func sortWithMultipleCriteria(items []Item) {
    sort.Slice(items, func(i, j int) bool {
        // Lexicographic comparison on multiple fields
        if items[i].Category != items[j].Category {
            return items[i].Category < items[j].Category
        }
        if items[i].Priority != items[j].Priority {
            return items[i].Priority > items[j].Priority // Descending
        }
        return items[i].Name < items[j].Name
    })
}
*/

fn main() {
    demonstrate_rust_patterns();
}
```

## **9. Problem-Solving Framework**

### **Step 1: Identify the Pattern**

Ask yourself:

1. **What are we comparing?** Strings, arrays, tuples, custom objects?
2. **What's the goal?** Smallest? Largest? Next? Kth?
3. **Are there constraints?** Fixed operations? Transformation rules?

### **Step 2: Choose the Right Strategy**

```
Lexicographic Problem Decision Tree:
│
├─ Need next/previous permutation?
│  └─ Use in-place pivot algorithm (O(n))
│
├─ Need smallest/largest with operations?
│  ├─ Swaps allowed? → Greedy bubble-to-front
│  ├─ Removals allowed? → Monotonic stack
│  └─ Insertions? → Greedy placement
│
├─ Need kth element in sequence?
│  └─ Use factorial number system (O(n²) or O(n))
│
├─ Need to compare custom objects?
│  └─ Implement comparison traits/interfaces
│
└─ Sorting with multiple criteria?
   └─ Use tuple keys or custom comparators
```

### **Step 3: Complexity Analysis**

**Before coding**, estimate:

- How many comparisons? (Each comparison is O(m) for length m sequences)
- Can we use greedy? (Verify optimal substructure)
- Do we need auxiliary space? (Can we work in-place?)

---

## **10. Common Pitfalls & How to Avoid Them**

### **Pitfall 1: Forgetting Prefix Rule**

```python
# Wrong: [1, 2] == [1, 2, 3] ❌
# Right: [1, 2] < [1, 2, 3] ✓
```

### **Pitfall 2: Not Checking Remaining Elements**

When using greedy removal, always ensure you have enough elements left to meet the target length.

### **Pitfall 3: Integer Overflow in Factorial Calculations**

For large n, factorials overflow. Use modular arithmetic or arbitrary precision.

### **Pitfall 4: Case Sensitivity in Strings**

'A' (65) < 'a' (97) in ASCII. Normalize if needed.

### **Pitfall 5: Mutating While Iterating**

```python
# Dangerous:
for i in range(len(arr)):
    arr.pop()  # ❌ Modifying while iterating

# Safe:
while arr:
    arr.pop()  # ✓
```

---

## **11. Practice Problem Roadmap**

### **Foundation (Master These First)**

1. ✅ Implement next permutation from scratch
2. ✅ Find lexicographically smallest string after k swaps
3. ✅ Remove k digits to minimize number
4. ✅ Compare version strings

### **Intermediate (Pattern Recognition)**

5. Smallest subsequence of distinct characters
6. Lexicographically smallest equivalent string (Union-Find)
7. Rearrange string k distance apart
8. Next greater element (circular)

### **Advanced (Combination Patterns)**

9. Count distinct permutations in lexicographic range
10. Shortest palindrome by adding characters (KMP + lex)
11. Lexicographically smallest string after substring swaps
12. Minimum deletions to make palindrome + lex smallest

---

## **12. Cognitive Principles for Mastery**

### **Chunking Strategy**

Group related patterns:

- **Chunk 1**: "Position-by-position greedy" (swaps, removals)
- **Chunk 2**: "Monotonic sequence maintenance" (stack-based)
- **Chunk 3**: "Factorial decomposition" (permutation ranking)

### **Deliberate Practice Protocol**

1. **Solve without looking** (30 min timer)
2. **Compare with optimal** (analyze differences)
3. **Explain to yourself** (Feynman technique)
4. **Implement in all 3 languages** (Rust, Python, Go)
5. **Revisit after 1 day, 1 week, 1 month** (spaced repetition)

### **Mental Simulation**

Before coding:

- **Trace by hand** on 3-4 examples
- **Identify invariants** (what stays true at each step?)
- **Predict edge cases** (empty, single element, all same, reversed)

### **Meta-Learning Insight**

Lexicographic problems train **hierarchical decision-making** — a transferable skill. You're learning to:

- Prioritize dimensions of comparison
- Make locally optimal choices with global awareness
- Reason about state space efficiently

This mental model applies to:

- Database indexing
- Game tree search (alpha-beta pruning)
- Multi-criteria optimization
- Any problem with ordered preferences

---

## **13. Final Mastery Checklist**

Can you:

- [ ] Implement next permutation in O(n) time, O(1) space?
- [ ] Explain why greedy works for "smallest after k swaps"?
- [ ] Derive time complexity of sorting n sequences of length m?
- [ ] Implement monotonic stack for "smallest subsequence"?
- [ ] Convert between permutation and rank using factorials?
- [ ] Design custom comparison logic for domain objects?
- [ ] Identify when lexicographic problems are actually disguised sorting?
- [ ] Optimize from O(n²) to O(n) using lookahead techniques?

---

## **The Path Forward**

You're not just learning an algorithm — you're internalizing a **fundamental way computers order information**. Every database index, every sorted file system, every ranked search result uses lexicographic ordering.

**Next Steps**:

1. Implement all patterns in the artifacts above in Rust and Go
2. Solve 20 problems (5 from each category in the roadmap)
3. Time yourself: can you recognize the pattern in <60 seconds?
4. Write your own variants: what if we want kth smallest instead of smallest?

Remember: **Top 1% mastery comes from seeing the patterns others miss.** When you look at a problem, you should immediately recognize: "Ah, this is monotonic stack with lookahead" or "This needs factorial decomposition."

That instant pattern recognition? That's what we're building.

Let's forge that intuition through fire. What problem shall we tackle first? 🔥

### Next Permutation Illustration for [1, 2, 3, 4, 5, 6]

The array [1, 2, 3, 4, 5, 6] is strictly increasing, so it's the first permutation in lexicographical order. To find the "next" one, we apply the algorithm you described. Here's a step-by-step breakdown with ASCII diagrams (using 0-based indexing for clarity). I'll explain the pivot concept first, then walk through the steps.

#### Quick Explanation of the Pivot

The **pivot** is the *rightmost* position (index `k`) in the array where the sequence "stops decreasing" when scanning from the right. In other words:

- Start from the end and move left, looking for the longest "decreasing suffix" (a tail where each element is ≥ the next one, i.e., non-increasing).
- The pivot is the element *just before* this suffix starts—specifically, the rightmost index where `a[k] < a[k+1]`.
- This works because the decreasing suffix represents the "exhausted" part of the permutation (like the end of a sorted list). To get the next permutation, we need to "bump up" the pivot (by swapping with a slightly larger successor) and then minimize the new suffix to keep things lexicographically smallest.
- In [1, 2, 3, 4, 5, 6], the entire array is increasing, so the decreasing suffix is just the last element (length 1). Thus, the pivot is at index 4 (value 5), since 5 < 6.

If no such pivot exists (e.g., fully decreasing like [6,5,4,3,2,1]), it's the last permutation—wrap around to the sorted one.

#### Step 1: Find the Pivot

Scan from the right for the rightmost `k` where `a[k] < a[k+1]`.

```
Original: [ 1, 2, 3, 4, 5, 6 ]
Indices:   0  1  2  3  4  5
           ↑              ↑
           |              |
           └─ Increasing ─┘
From right: Fully increasing → decreasing suffix = [6] (just index 5)
Pivot (k=4): Rightmost where it "stops decreasing" (5 < 6)
```

#### Step 2: Find the Successor

From the right of the pivot (suffix starting at index 5), find the *smallest* element `l > k` where `a[l] > a[k]` (i.e., >5). Here, only 6 qualifies, so `l=5`.

```
After pivot: [ 1, 2, 3, 4 | 5, 6 ]  ← Suffix after pivot (indices 5+)
Pivot val:     5                  ↑
              ↑                   └─ Smallest >5 in suffix? Yes, 6 (l=5)
```

#### Step 3: Swap Pivot and Successor, Then Reverse Suffix

- Swap `a[4]` (5) and `a[5]` (6) → [1, 2, 3, 4, 6, 5]
- Reverse the suffix after the pivot (indices 5 to end: just [5], which stays the same)

```
Before swap: [ 1, 2, 3, 4, 5, 6 ]
              ↑        ↑  ↑
              |        |  └─ Successor (l=5)
              |        └─ Pivot (k=4)
              └─ Unchanged prefix

After swap:   [ 1, 2, 3, 4, 6, 5 ]
              ↑        ↑  ↑
              |        |  └─ Swapped (now 5)
              |        └─ Swapped (now 6)
              └─ Unchanged prefix

After reverse (suffix 5-end: [5] → no change): [ 1, 2, 3, 4, 6, 5 ]
```

The result [1, 2, 3, 4, 6, 5] is the immediate next permutation—smallest possible change from the original while staying larger in lex order. The reverse step ensures the new suffix is the smallest possible (sorted ascending).

### Key Terms in the Next Permutation Algorithm

These terms come from the standard algorithm for generating the next lexicographically larger permutation of a sequence (e.g., from [1,2,3] to [1,3,2]). The goal is to find the smallest possible "next" arrangement without generating all permutations. I'll explain each term below, using the example sequence **[1, 2, 3, 4, 5, 6]** (which becomes [1, 2, 3, 4, 6, 5] as the next one). I'll include a simple ASCII diagram for context.

#### 1. **Pivot**

- **Meaning**: The *rightmost* index `k` in the sequence where the elements start to "increase" again after scanning from the right. In other words, it's the position where `a[k] < a[k+1]` holds, marking the end of the longest "decreasing suffix" (a tail where elements are non-increasing, like a sorted descending list that's been exhausted).
- **Why it matters**: This identifies the point to "increment" the sequence—like carrying over in addition. Everything left of the pivot stays the same (it's already the smallest possible prefix), and we only tweak the suffix.
- **In the example**: The whole sequence is increasing, so the decreasing suffix is just [6]. The pivot is at index 4 (value **5**), because 5 < 6.

```
     [ 1, 2, 3, 4 | 5, 6 ]  ← Pivot at | (index 4: 5 < 6)
            Prefix  |  Suffix (decreasing tail)
```

#### 2. **Successor**

- **Meaning**: The *smallest* element in the suffix (right of the pivot) that is *larger* than the pivot value. It's found by scanning the suffix from the right.
- **Why it matters**: Swapping with this ensures the smallest possible increase at the pivot position, keeping the new permutation as close as possible to the original (lexicographically next).
- **In the example**: Suffix is [6]. The smallest >5 is **6** (at index 5).

```
     [ 1, 2, 3, 4 | 5, 6 ]  ← Successor is 6 (smallest in suffix > pivot 5)
            Prefix  |  ↑ (index 5)
```

#### 3. **Suffix**

- **Meaning**: The subsequence starting *immediately after the pivot* to the end of the array. This is always non-increasing (decreasing or equal) by definition of the pivot.
- **Why it matters**: It's the "exhausted" part of the current permutation. After swapping, we need to rearrange it to be the smallest possible (ascending) for the next permutation.
- **In the example**: After pivot (index 4), suffix = **[6]** (indices 5 to end).

```
     [ 1, 2, 3, 4 | 5 | 6 ]  ← Suffix starts after pivot: [6]
            Prefix  |     |
                 Pivot   Suffix
```

#### 4. **Reverse Suffix**

- **Meaning**: After swapping the pivot with its successor, *reverse* the entire suffix (now including the swapped elements) to sort it in ascending order. This minimizes the tail, ensuring the overall permutation is the smallest possible next one.
- **Why it matters**: The suffix was originally descending; reversing makes it ascending, which is the lexicographically smallest arrangement of those elements.
- **In the example**:

- After swap: [1, 2, 3, 4, **6**, **5**] (suffix now [5])
- Reverse suffix [5] → still [5] (single element, no change)
- Final: **[1, 2, 3, 4, 6, 5]**

```
     Before swap: [ 1, 2, 3, 4 | 5 | 6 ]  ← Suffix: [6]
     After swap:  [ 1, 2, 3, 4 | 6 | 5 ]  ← Suffix now: [5] (descending? No, but reverse anyway)
     After reverse:[ 1, 2, 3, 4 | 6 | 5 ]  ← Suffix reversed to ascending: [5]
```

For a more interesting example with a longer suffix, consider [1, 2, 5, 4, 3]:

- Pivot: Index 1 (2 < 5)
- Suffix: [5,4,3] (decreasing)
- Successor: 3 (smallest in suffix >2)
- Swap: [1, 3, 5, 4, 2]
- Reverse suffix [5,4,2] → [2,4,5]
- Final: [1, 3, 2, 4, 5]

This algorithm is efficient (O(n)) and skips duplicates if the sequence has them. If no pivot exists (fully decreasing), it's the last permutation—reset to sorted order.