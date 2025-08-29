# Time and Space Complexity in DSA

Got it 👍 Let’s go step by step in a **clear, addictive, and fun way** so you’ll actually enjoy learning time and space complexities in DSA.

---

## 🚀 What Are Time and Space Complexities?

When we write an algorithm, two big questions always matter:

1. **Time Complexity** → How fast is my algorithm? (How many steps does it take as input size grows?)
2. **Space Complexity** → How much extra memory does it need? (Apart from the input itself.)

Think of it like this:

* ⏱ Time = How long it takes your brain to solve a puzzle.
* 💾 Space = How much paper you need to scribble while solving.

---

## 📊 Big-O Notation

We usually describe both **time** and **space** using **Big-O notation**.
Big-O gives us an **upper bound** (worst-case growth rate) of the algorithm.

Examples of common complexities (from fastest to slowest):

| Complexity     | Time grows like... | Example                          |
| -------------- | ------------------ | -------------------------------- |
| **O(1)**       | constant           | Accessing an array element       |
| **O(log n)**   | logarithmic        | Binary search                    |
| **O(n)**       | linear             | Loop through an array            |
| **O(n log n)** | log-linear         | Merge sort, Quick sort (average) |
| **O(n²)**      | quadratic          | Bubble sort, nested loops        |
| **O(2ⁿ)**      | exponential        | Recursive Fibonacci              |
| **O(n!)**      | factorial          | Traveling Salesman brute-force   |

---

## 🔍 Time Complexity Examples

### 1. O(1) – Constant Time

```rust
fn get_first(arr: &[i32]) -> i32 {
    arr[0]   // Always one step
}
```

👉 No matter if array has 10 or 10 million elements, it takes 1 step.

---

### 2. O(n) – Linear Time

```rust
fn print_all(arr: &[i32]) {
    for x in arr {
        println!("{}", x);
    }
}
```

👉 Looping through all elements → work grows directly with size of input.

---

### 3. O(n²) – Quadratic Time

```rust
fn print_pairs(arr: &[i32]) {
    for i in 0..arr.len() {
        for j in 0..arr.len() {
            println!("({}, {})", arr[i], arr[j]);
        }
    }
}
```

👉 For each element, you loop through all elements → n × n steps.

---

### 4. O(log n) – Logarithmic Time

```rust
fn binary_search(arr: &[i32], target: i32) -> bool {
    let mut low = 0;
    let mut high = arr.len() - 1;

    while low <= high {
        let mid = (low + high) / 2;
        if arr[mid] == target { return true; }
        else if arr[mid] < target { low = mid + 1; }
        else { high = mid - 1; }
    }
    false
}
```

👉 Each step cuts problem size in half → super efficient!

---

## 🧠 Space Complexity Examples

1. **O(1)** → No extra memory (just variables).

   ```rust
   fn sum(arr: &[i32]) -> i32 {
       let mut total = 0;
       for x in arr {
           total += x;
       }
       total
   }
   ```

2. **O(n)** → Extra memory proportional to input size.

   ```rust
   fn clone_vec(arr: &[i32]) -> Vec<i32> {
       arr.to_vec() // needs n extra space
   }
   ```

3. **O(n²)** → Example: Storing all pairs in a 2D matrix.

---

## ⚡ Memory: Stack vs Heap Connection

When talking about space:

* **Stack** → Local variables, function calls, fixed size.
* **Heap** → Dynamic memory, vectors, recursion-heavy calls.

Example:

* `let x = 5;` → stored in stack.
* `let v = vec![1,2,3];` → vector pointer is on stack, but actual data lives in heap.

---

## 🎯 Quick Trick to Analyze Complexity

1. **Loops:**

   * Single loop → O(n)
   * Nested loops → O(n²)
   * Loop halving each time → O(log n)

2. **Recursion:**

   * Recursive branching (like Fibonacci) → O(2ⁿ)
   * Divide-and-conquer (like Merge Sort) → O(n log n)

3. **Extra Memory:**

   * Just variables → O(1)
   * New array/vector → O(n)

---

⚡ Boom. That’s the **core of time and space complexities in DSA**.

Do you want me to make a **visual memory map/diagram (like ASCII or blocks)** so you can recall complexities instantly while solving problems?

Perfect 😃 Let’s build a **visual memory map** of time & space complexities so it sticks in your brain like a cheat-sheet.

---

## 🧩 Complexity Cheat Map (ASCII Diagram)

```
                   Time & Space Complexities
 ┌──────────────────────────────────────────────────────┐
 |                   FAST → SLOW                        |
 └──────────────────────────────────────────────────────┘

O(1)    Constant
   ──► Direct access, hashmap lookup
   (Fastest – 1 step always)

O(log n)  Logarithmic
   ──► Binary Search, Tree height
   (Divide problem in half each step)

O(n)    Linear
   ──► Scanning array, sum of elements
   (Work grows in proportion to input size)

O(n log n) Log-Linear
   ──► Merge Sort, Quick Sort (avg)
   (Efficient sorting, balanced divide-and-conquer)

O(n²)   Quadratic
   ──► Nested loops, Bubble Sort
   (Bad for large inputs – grows fast!)

O(2ⁿ)   Exponential
   ──► Recursive Fibonacci
   (Explodes quickly, only feasible for tiny n)

O(n!)   Factorial
   ──► Traveling Salesman brute-force
   (Insanely slow – worst category)
```

---

## 💾 Space Complexity Map

```
STACK (fixed size, fast, local)
 ──► Function calls, local vars

HEAP (dynamic, slower, global lifetime)
 ──► Vectors, HashMaps, recursion-heavy memory use

Common Patterns:
 O(1)  - No extra storage (just counters, variables)
 O(n)  - Extra array, cloning vector
 O(n²) - Storing 2D grids, all pairs
```

---

## 🔑 Quick Recognition Tricks

* **One loop → O(n)**
* **Two nested loops → O(n²)**
* **Loop cutting input in half → O(log n)**
* **Sorting (good) → O(n log n)**
* **Brute-force recursion → O(2ⁿ)**
* **Permutations/combinations → O(n!)**

---

⚡ Mnemonic:
**“Constant → Log → Linear → LogLinear → Quadratic → Exponential → Factorial”**
👉 From 🚀 Fastest to 🐌 Slowest.

---

Would you like me to make this into a **picture-style diagram (like blocks/flow chart)** so you can print or keep as wallpaper?

I'll provide a comprehensive guide to DSA time and space complexity analysis strategies and techniques.I've created a comprehensive guide covering DSA time and space complexity analysis. The guide includes:

**Core Techniques:**
* Loop analysis patterns (single, nested, logarithmic)
* Recursive complexity using Master Theorem
* Amortized analysis methods
* Space complexity considerations (auxiliary vs total space)

**Practical Knowledge:**
* Complete complexity tables for sorting, searching, and graph algorithms
* Algorithm design pattern complexities
* Time-space tradeoff strategies
* Data structure selection guidelines

**Advanced Topics:**
* Probabilistic and competitive analysis
* Lower bound proof techniques
* Parameterized complexity
* Cache-aware algorithm design

**Real-World Application:**
* Common pitfalls to avoid
* Best practices for analysis and optimization
* Complexity constraints by problem size
* Memory usage guidelines

The guide emphasizes both theoretical understanding and practical application, helping you analyze complexity accurately and choose optimal algorithms for different constraints. Each technique includes concrete examples and implementation patterns you can apply directly to your DSA problems.

Would you like me to elaborate on any specific technique or provide more detailed examples for particular algorithm categories?

## Comprehensive DSA Time & Space Complexity Guide

## Table of Contents

1. [Fundamental Concepts](#fundamental-concepts)
2. [Time Complexity Analysis Techniques](#time-complexity-analysis-techniques)
3. [Space Complexity Analysis Techniques](#space-complexity-analysis-techniques)
4. [Algorithm Categories & Complexities](#algorithm-categories--complexities)
5. [Advanced Analysis Techniques](#advanced-analysis-techniques)
6. [Optimization Strategies](#optimization-strategies)
7. [Common Pitfalls & Best Practices](#common-pitfalls--best-practices)

## Fundamental Concepts

### Big O Notation Hierarchy

```
O(1) < O(log n) < O(n) < O(n log n) < O(n²) < O(n³) < O(2ⁿ) < O(n!)
```

### Growth Rate Comparison

- **O(1)**: Constant - Hash table lookup
* **O(log n)**: Logarithmic - Binary search
* **O(n)**: Linear - Array traversal
* **O(n log n)**: Linearithmic - Merge sort
* **O(n²)**: Quadratic - Nested loops
* **O(2ⁿ)**: Exponential - Recursive Fibonacci
* **O(n!)**: Factorial - Permutation generation

## Time Complexity Analysis Techniques

### 1. Loop Analysis

#### Single Loop

```python
# O(n)
for i in range(n):
    print(i)
```

#### Nested Loops

```python
# O(n²) - Both loops depend on n
for i in range(n):
    for j in range(n):
        print(i, j)

# O(n*m) - Loops depend on different variables
for i in range(n):
    for j in range(m):
        print(i, j)
```

#### Loop with Decreasing/Increasing Steps

```python
# O(log n) - Dividing by 2 each iteration
i = 1
while i < n:
    print(i)
    i *= 2

# O(n) - Despite appearance, visits n elements
i = n
while i > 0:
    print(i)
    i -= 1
```

### 2. Recursive Analysis

#### Master Theorem

For recurrences of the form: `T(n) = aT(n/b) + f(n)`

**Cases:**

1. If f(n) = O(n^(log_b(a) - ε)), then T(n) = Θ(n^log_b(a))
2. If f(n) = Θ(n^log_b(a)), then T(n) = Θ(n^log_b(a) * log n)
3. If f(n) = Ω(n^(log_b(a) + ε)), then T(n) = Θ(f(n))

#### Common Recursive Patterns

**Binary Search:** T(n) = T(n/2) + O(1) = O(log n)
**Merge Sort:** T(n) = 2T(n/2) + O(n) = O(n log n)
**Binary Tree Traversal:** T(n) = 2T(n/2) + O(1) = O(n)
**Naive Fibonacci:** T(n) = T(n-1) + T(n-2) + O(1) = O(2ⁿ)

### 3. Amortized Analysis

#### Aggregate Method

Calculate total cost of n operations, divide by n.

#### Accounting Method

Assign costs to operations, maintain non-negative credit.

#### Potential Method

Use potential function to represent stored work.

**Example: Dynamic Array**
* Individual insertion: O(n) worst case
* Amortized insertion: O(1) average

## Space Complexity Analysis Techniques

### 1. Auxiliary Space vs Total Space

**Auxiliary Space:** Extra space used by algorithm
**Total Space:** Input space + Auxiliary space

### 2. Recursive Space Analysis

```python
# O(n) space due to call stack
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n-1)

# O(1) space - tail recursion optimized
def factorial_iterative(n):
    result = 1
    for i in range(1, n+1):
        result *= i
    return result
```

### 3. Data Structure Space Requirements

* **Array:** O(n)
* **Linked List:** O(n) + pointer overhead
* **Binary Tree:** O(n) + pointer overhead
* **Hash Table:** O(n) + bucket overhead
* **Graph (Adjacency Matrix):** O(V²)
* **Graph (Adjacency List):** O(V + E)

## Algorithm Categories & Complexities

### Sorting Algorithms

| Algorithm | Best | Average | Worst | Space | Stable |
|-----------|------|---------|-------|-------|--------|
| Bubble Sort | O(n) | O(n²) | O(n²) | O(1) | Yes |
| Selection Sort | O(n²) | O(n²) | O(n²) | O(1) | No |
| Insertion Sort | O(n) | O(n²) | O(n²) | O(1) | Yes |
| Merge Sort | O(n log n) | O(n log n) | O(n log n) | O(n) | Yes |
| Quick Sort | O(n log n) | O(n log n) | O(n²) | O(log n) | No |
| Heap Sort | O(n log n) | O(n log n) | O(n log n) | O(1) | No |
| Radix Sort | O(d(n+b)) | O(d(n+b)) | O(d(n+b)) | O(n+b) | Yes |

### Search Algorithms

| Algorithm | Time | Space | Requirements |
|-----------|------|-------|--------------|
| Linear Search | O(n) | O(1) | None |
| Binary Search | O(log n) | O(1) | Sorted array |
| Hash Table | O(1) avg | O(n) | Hash function |
| BST Search | O(log n) avg | O(1) | Balanced tree |

### Graph Algorithms

| Algorithm | Time | Space | Use Case |
|-----------|------|-------|----------|
| BFS | O(V + E) | O(V) | Shortest path (unweighted) |
| DFS | O(V + E) | O(V) | Connected components |
| Dijkstra | O((V + E) log V) | O(V) | Shortest path (weighted) |
| Floyd-Warshall | O(V³) | O(V²) | All pairs shortest path |
| Kruskal's | O(E log E) | O(V) | Minimum spanning tree |
| Prim's | O((V + E) log V) | O(V) | Minimum spanning tree |

### Dynamic Programming

| Problem | Time | Space | Optimization |
|---------|------|-------|--------------|
| Fibonacci | O(n) | O(1) | Bottom-up |
| LCS | O(mn) | O(min(m,n)) | Space optimized |
| Knapsack | O(nW) | O(W) | 1D array |
| Edit Distance | O(mn) | O(min(m,n)) | Rolling array |

## Advanced Analysis Techniques

### 1. Probabilistic Analysis

- **Expected Time:** Average over all possible inputs
* **Randomized Algorithms:** Algorithm makes random choices
* **Monte Carlo vs Las Vegas:** Correctness vs runtime guarantees

### 2. Competitive Analysis

- **Online Algorithms:** Process input incrementally
* **Competitive Ratio:** Compare to optimal offline algorithm

### 3. Parameterized Complexity

- **Fixed Parameter Tractable (FPT):** O(f(k) * n^c)
* **Parameter:** Small integer that affects complexity

### 4. Lower Bound Techniques

#### Comparison-Based Sorting

- Decision tree model proves Ω(n log n) lower bound
* Information theoretic argument: need log(n!) bits

#### Element Distinctness

- Algebraic decision tree model proves Ω(n log n)

## Optimization Strategies

### 1. Time-Space Tradeoffs

#### Memoization

```python
# Time: O(n), Space: O(n)
def fibonacci_memo(n, memo={}):
    if n in memo:
        return memo[n]
    if n <= 1:
        return n
    memo[n] = fibonacci_memo(n-1, memo) + fibonacci_memo(n-2, memo)
    return memo[n]
```

#### Space Optimization

```python
# Time: O(n), Space: O(1)
def fibonacci_optimized(n):
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b
```

### 2. Algorithm Design Patterns

#### Divide and Conquer

- **Time:** Often O(n log n)
* **Space:** O(log n) due to recursion
* **Examples:** Merge sort, quick sort, binary search

#### Greedy Algorithms

- **Time:** Usually O(n log n) due to sorting
* **Space:** O(1) typically
* **Examples:** Huffman coding, activity selection

#### Dynamic Programming

- **Time:** O(n^k) for k-dimensional problems
* **Space:** Can often be reduced by one dimension
* **Examples:** LCS, knapsack, shortest paths

### 3. Data Structure Optimization

#### Choose Right Data Structure

- **Frequent lookups:** Hash table O(1)
* **Ordered operations:** Balanced BST O(log n)
* **Range queries:** Segment tree O(log n)
* **Union operations:** Disjoint set O(α(n))

#### Hybrid Approaches

- **Timsort:** Merge + insertion sort
* **Introsort:** Quick + heap + insertion sort
* **Cache-oblivious algorithms:** Optimize for memory hierarchy

## Common Pitfalls & Best Practices

### Analysis Pitfalls

1. **Ignoring Hidden Constants**
   * O(1) hash operations can be expensive
   * String operations often O(length)

2. **Worst Case vs Average Case**
   * Quick sort: O(n²) worst, O(n log n) average
   * Hash table: O(n) worst, O(1) average

3. **Input Size Assumptions**
   * What constitutes "n"?
   * Multiple variables (n, m, k)

4. **Space Complexity Oversights**
   * Recursive call stack
   * Input modification vs auxiliary space

### Best Practices

#### 1. Always Consider Both Time and Space

```python
# Time: O(n²), Space: O(1) - in-place
def bubble_sort_inplace(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]

# Time: O(n log n), Space: O(n) - requires extra space
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)
```

#### 2. Profile Before Optimizing

- Identify actual bottlenecks
* Consider input characteristics
* Measure real performance

#### 3. Document Complexity

```python
def two_sum(nums, target):
    """
    Find two numbers that add up to target.
    
    Time Complexity: O(n)
    Space Complexity: O(n)
    
    Args:
        nums: List of integers
        target: Target sum
    
    Returns:
        Indices of two numbers that add up to target
    """
    seen = {}  # O(n) space
    for i, num in enumerate(nums):  # O(n) time
        complement = target - num
        if complement in seen:  # O(1) average
            return [seen[complement], i]
        seen[num] = i
    return []
```

#### 4. Consider Input Constraints

- Small n: Even O(n³) might be acceptable
* Large n: Need sublinear or linear solutions
* Online vs offline algorithms
* Memory constraints

#### 5. Understand Amortized Analysis

- Dynamic arrays: O(1) amortized insertion
* Disjoint sets: O(α(n)) amortized operations
* Splay trees: O(log n) amortized operations

### Complexity Cheat Sheet

#### Common Time Complexities by Problem Size

- **n ≤ 10:** O(n!), O(2ⁿ)
* **n ≤ 20:** O(2ⁿ), O(n³)
* **n ≤ 500:** O(n³)
* **n ≤ 5000:** O(n²)
* **n ≤ 10⁶:** O(n log n)
* **n ≤ 10⁸:** O(n)
* **n > 10⁸:** O(log n), O(1)

#### Memory Usage Guidelines

- **Arrays:** 4-8 bytes per element (int/pointer)
* **Strings:** 1-4 bytes per character
* **Objects:** Additional overhead (24+ bytes in Java)
* **Call stack:** Typically 1MB limit (1000-10000 calls)

This comprehensive guide provides the foundation for analyzing and optimizing algorithm complexity. Remember that complexity analysis is both an art and a science - theoretical bounds matter, but so does practical performance on real inputs.

I'll create a comprehensive guide covering all the important pattern recognition algorithms in Data Structures and Algorithms (DSA) with sample code and complexity analysis.I've created a comprehensive guide covering all the major pattern recognition algorithms in DSA. The document includes:

**String Pattern Matching:**
* Naive/Brute Force approach
* KMP (Knuth-Morris-Pratt) with LPS array
* Rabin-Karp using rolling hash
* Boyer-Moore with bad character heuristic

**Subsequence Patterns:**
* Longest Common Subsequence (LCS)
* Longest Increasing Subsequence (LIS) with both O(n²) and O(n log n) solutions

**Array Patterns:**
* Sliding Window Maximum using deque
* Kadane's Algorithm for maximum subarray sum

**Tree & Graph Patterns:**
* Various tree traversals and path sum
* Cycle detection in both directed and undirected graphs

**Advanced Algorithms:**
* Z Algorithm for linear time pattern matching
* Manacher's Algorithm for palindrome detection

Each algorithm includes:
* Complete working code with examples
* Detailed time and space complexity analysis
* Practical use cases and applications

The algorithms range from basic O(n*m) brute force approaches to sophisticated O(n) linear time solutions, covering the most important pattern recognition techniques you'll encounter in competitive programming and technical interviews.

## Pattern Recognition Algorithms in DSA

## 1. String Pattern Matching Algorithms

### 1.1 Naive Pattern Matching (Brute Force)

```python
def naive_search(text, pattern):
    n, m = len(text), len(pattern)
    result = []
    
    for i in range(n - m + 1):
        j = 0
        while j < m and text[i + j] == pattern[j]:
            j += 1
        if j == m:
            result.append(i)
    
    return result

# Example usage
text = "ABABDABACDABABCABCABCABCABC"
pattern = "ABABCAB"
print(naive_search(text, pattern))
```

**Time Complexity:** O(n*m) where n = length of text, m = length of pattern  
**Space Complexity:** O(1)

### 1.2 KMP (Knuth-Morris-Pratt) Algorithm

```python
def kmp_search(text, pattern):
    def compute_lps(pattern):
        m = len(pattern)
        lps = [0] * m
        length = 0
        i = 1
        
        while i < m:
            if pattern[i] == pattern[length]:
                length += 1
                lps[i] = length
                i += 1
            else:
                if length != 0:
                    length = lps[length - 1]
                else:
                    lps[i] = 0
                    i += 1
        return lps
    
    n, m = len(text), len(pattern)
    lps = compute_lps(pattern)
    result = []
    
    i = j = 0
    while i < n:
        if pattern[j] == text[i]:
            i += 1
            j += 1
        
        if j == m:
            result.append(i - j)
            j = lps[j - 1]
        elif i < n and pattern[j] != text[i]:
            if j != 0:
                j = lps[j - 1]
            else:
                i += 1
    
    return result

# Example usage
text = "ABABDABACDABABCABCABCABCABC"
pattern = "ABABCAB"
print(kmp_search(text, pattern))
```

**Time Complexity:** O(n + m)  
**Space Complexity:** O(m) for LPS array

### 1.3 Rabin-Karp Algorithm (Rolling Hash)

```python
def rabin_karp_search(text, pattern, prime=101):
    n, m = len(text), len(pattern)
    pattern_hash = text_hash = 0
    h = 1
    result = []
    
    # Calculate hash value for pattern and first window
    for i in range(m - 1):
        h = (h * 256) % prime
    
    for i in range(m):
        pattern_hash = (256 * pattern_hash + ord(pattern[i])) % prime
        text_hash = (256 * text_hash + ord(text[i])) % prime
    
    # Slide pattern over text
    for i in range(n - m + 1):
        if pattern_hash == text_hash:
            if text[i:i+m] == pattern:
                result.append(i)
        
        if i < n - m:
            text_hash = (256 * (text_hash - ord(text[i]) * h) + ord(text[i + m])) % prime
            if text_hash < 0:
                text_hash += prime
    
    return result

# Example usage
text = "GEEKS FOR GEEKS"
pattern = "GEEK"
print(rabin_karp_search(text, pattern))
```

**Time Complexity:** O(n + m) average case, O(n*m) worst case  
**Space Complexity:** O(1)

### 1.4 Boyer-Moore Algorithm

```python
def boyer_moore_search(text, pattern):
    def bad_character_heuristic(pattern):
        bad_char = [-1] * 256
        for i in range(len(pattern)):
            bad_char[ord(pattern[i])] = i
        return bad_char
    
    n, m = len(text), len(pattern)
    bad_char = bad_character_heuristic(pattern)
    result = []
    
    shift = 0
    while shift <= n - m:
        j = m - 1
        
        while j >= 0 and pattern[j] == text[shift + j]:
            j -= 1
        
        if j < 0:
            result.append(shift)
            shift += (m - bad_char[ord(text[shift + m])] if shift + m < n else 1)
        else:
            shift += max(1, j - bad_char[ord(text[shift + j])])
    
    return result

# Example usage
text = "ABAAABCDABABCABCABCABC"
pattern = "ABC"
print(boyer_moore_search(text, pattern))
```

**Time Complexity:** O(n*m) worst case, O(n/m) best case  
**Space Complexity:** O(σ) where σ is alphabet size

## 2. Subsequence Pattern Matching

### 2.1 Longest Common Subsequence (LCS)

```python
def lcs_length(text1, text2):
    m, n = len(text1), len(text2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i-1] == text2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    return dp[m][n]

def lcs_string(text1, text2):
    m, n = len(text1), len(text2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # Fill dp table
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i-1] == text2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    # Reconstruct LCS
    lcs = []
    i, j = m, n
    while i > 0 and j > 0:
        if text1[i-1] == text2[j-1]:
            lcs.append(text1[i-1])
            i -= 1
            j -= 1
        elif dp[i-1][j] > dp[i][j-1]:
            i -= 1
        else:
            j -= 1
    
    return ''.join(reversed(lcs))

# Example usage
text1 = "AGGTAB"
text2 = "GXTXAYB"
print(f"LCS Length: {lcs_length(text1, text2)}")
print(f"LCS: {lcs_string(text1, text2)}")
```

**Time Complexity:** O(m*n)  
**Space Complexity:** O(m*n)

### 2.2 Longest Increasing Subsequence (LIS)

```python
def lis_length(arr):
    n = len(arr)
    if n == 0:
        return 0
    
    dp = [1] * n
    
    for i in range(1, n):
        for j in range(i):
            if arr[j] < arr[i]:
                dp[i] = max(dp[i], dp[j] + 1)
    
    return max(dp)

def lis_optimized(arr):
    from bisect import bisect_left
    
    if not arr:
        return 0
    
    tails = []
    
    for num in arr:
        pos = bisect_left(tails, num)
        if pos == len(tails):
            tails.append(num)
        else:
            tails[pos] = num
    
    return len(tails)

# Example usage
arr = [10, 9, 2, 5, 3, 7, 101, 18]
print(f"LIS Length (DP): {lis_length(arr)}")
print(f"LIS Length (Optimized): {lis_optimized(arr)}")
```

**Time Complexity:** O(n²) for DP, O(n log n) for optimized  
**Space Complexity:** O(n)

## 3. Array Pattern Recognition

### 3.1 Sliding Window Maximum/Minimum

```python
from collections import deque

def sliding_window_maximum(arr, k):
    dq = deque()
    result = []
    
    for i in range(len(arr)):
        # Remove elements outside current window
        while dq and dq[0] <= i - k:
            dq.popleft()
        
        # Remove smaller elements from rear
        while dq and arr[dq[-1]] <= arr[i]:
            dq.pop()
        
        dq.append(i)
        
        # Add to result if window is complete
        if i >= k - 1:
            result.append(arr[dq[0]])
    
    return result

# Example usage
arr = [1, 2, 3, 1, 4, 5, 2, 3, 6]
k = 3
print(sliding_window_maximum(arr, k))
```

**Time Complexity:** O(n)  
**Space Complexity:** O(k)

### 3.2 Kadane's Algorithm (Maximum Subarray Sum)

```python
def max_subarray_sum(arr):
    max_ending_here = max_so_far = arr[0]
    start = end = s = 0
    
    for i in range(1, len(arr)):
        if max_ending_here < 0:
            max_ending_here = arr[i]
            s = i
        else:
            max_ending_here += arr[i]
        
        if max_so_far < max_ending_here:
            max_so_far = max_ending_here
            start = s
            end = i
    
    return max_so_far, (start, end)

# Example usage
arr = [-2, -3, 4, -1, -2, 1, 5, -3]
max_sum, indices = max_subarray_sum(arr)
print(f"Maximum sum: {max_sum}, Subarray: {arr[indices[0]:indices[1]+1]}")
```

**Time Complexity:** O(n)  
**Space Complexity:** O(1)

## 4. Tree Pattern Recognition

### 4.1 Tree Traversal Patterns

```python
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def inorder_traversal(root):
    result = []
    
    def inorder(node):
        if node:
            inorder(node.left)
            result.append(node.val)
            inorder(node.right)
    
    inorder(root)
    return result

def level_order_traversal(root):
    if not root:
        return []
    
    from collections import deque
    queue = deque([root])
    result = []
    
    while queue:
        level_size = len(queue)
        level = []
        
        for _ in range(level_size):
            node = queue.popleft()
            level.append(node.val)
            
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        
        result.append(level)
    
    return result

# Path Sum Pattern
def has_path_sum(root, target_sum):
    if not root:
        return False
    
    if not root.left and not root.right:
        return root.val == target_sum
    
    return (has_path_sum(root.left, target_sum - root.val) or 
            has_path_sum(root.right, target_sum - root.val))
```

**Time Complexity:** O(n) for all traversals  
**Space Complexity:** O(h) for recursive, O(w) for level order (h=height, w=max width)

## 5. Graph Pattern Recognition

### 5.1 Cycle Detection

```python
def has_cycle_undirected(graph):
    visited = set()
    
    def dfs(node, parent):
        visited.add(node)
        
        for neighbor in graph[node]:
            if neighbor not in visited:
                if dfs(neighbor, node):
                    return True
            elif neighbor != parent:
                return True
        
        return False
    
    for node in graph:
        if node not in visited:
            if dfs(node, -1):
                return True
    
    return False

def has_cycle_directed(graph):
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {node: WHITE for node in graph}
    
    def dfs(node):
        if color[node] == GRAY:
            return True
        if color[node] == BLACK:
            return False
        
        color[node] = GRAY
        
        for neighbor in graph[node]:
            if dfs(neighbor):
                return True
        
        color[node] = BLACK
        return False
    
    for node in graph:
        if color[node] == WHITE:
            if dfs(node):
                return True
    
    return False

# Example usage
undirected_graph = {0: [1, 2], 1: [0, 2], 2: [0, 1, 3], 3: [2]}
directed_graph = {0: [1], 1: [2], 2: [3], 3: [1]}

print(f"Undirected graph has cycle: {has_cycle_undirected(undirected_graph)}")
print(f"Directed graph has cycle: {has_cycle_directed(directed_graph)}")
```

**Time Complexity:** O(V + E)  
**Space Complexity:** O(V)

## 6. Advanced Pattern Recognition

### 6.1 Z Algorithm (Linear Time Pattern Matching)

```python
def z_algorithm(s):
    n = len(s)
    z = [0] * n
    l, r = 0, 0
    
    for i in range(1, n):
        if i <= r:
            z[i] = min(r - i + 1, z[i - l])
        
        while i + z[i] < n and s[z[i]] == s[i + z[i]]:
            z[i] += 1
        
        if i + z[i] - 1 > r:
            l, r = i, i + z[i] - 1
    
    return z

def z_search(text, pattern):
    combined = pattern + "$" + text
    z_array = z_algorithm(combined)
    pattern_len = len(pattern)
    result = []
    
    for i in range(pattern_len + 1, len(combined)):
        if z_array[i] == pattern_len:
            result.append(i - pattern_len - 1)
    
    return result

# Example usage
text = "AABAACAADAABAABA"
pattern = "AABA"
print(z_search(text, pattern))
```

**Time Complexity:** O(n + m)  
**Space Complexity:** O(n + m)

### 6.2 Manacher's Algorithm (Palindrome Detection)

```python
def manacher_algorithm(s):
    # Transform string: "abc" -> "^#a#b#c#$"
    transformed = "^#" + "#".join(s) + "#$"
    n = len(transformed)
    p = [0] * n
    center = right = 0
    
    for i in range(1, n - 1):
        mirror = 2 * center - i
        
        if i < right:
            p[i] = min(right - i, p[mirror])
        
        # Try to expand palindrome centered at i
        while transformed[i + p[i] + 1] == transformed[i - p[i] - 1]:
            p[i] += 1
        
        # If palindrome centered at i extends past right, adjust center and right
        if i + p[i] > right:
            center, right = i, i + p[i]
    
    return p

def longest_palindrome(s):
    if not s:
        return ""
    
    p = manacher_algorithm(s)
    max_len = 0
    center_index = 0
    
    for i in range(len(p)):
        if p[i] > max_len:
            max_len = p[i]
            center_index = i
    
    start = (center_index - max_len) // 2
    return s[start:start + max_len]

# Example usage
s = "babad"
print(f"Longest palindrome in '{s}': {longest_palindrome(s)}")
```

**Time Complexity:** O(n)  
**Space Complexity:** O(n)

## Summary of Time & Space Complexities

| Algorithm | Time Complexity | Space Complexity | Use Case |
|-----------|----------------|------------------|----------|
| Naive Search | O(n*m) | O(1) | Simple pattern matching |
| KMP | O(n+m) | O(m) | Efficient pattern matching |
| Rabin-Karp | O(n+m) avg, O(n*m) worst | O(1) | Multiple pattern search |
| Boyer-Moore | O(n/m) best, O(n*m) worst | O(σ) | Large alphabet searches |
| LCS | O(m*n) | O(m*n) | Sequence comparison |
| LIS | O(n²) or O(n log n) | O(n) | Increasing subsequences |
| Sliding Window | O(n) | O(k) | Range queries |
| Kadane's | O(n) | O(1) | Maximum subarray |
| Z Algorithm | O(n+m) | O(n+m) | Linear pattern matching |
| Manacher's | O(n) | O(n) | Palindrome detection |

These algorithms form the foundation of pattern recognition in computer science and are essential for solving various string matching, sequence analysis, and optimization problems.

I've completed the comprehensive guide with advanced real-world pattern recognition algorithms. The document now includes 12 major categories covering everything from basic string matching to sophisticated neural networks and streaming pattern detection.

**Key highlights of the advanced sections:**

**Real-World Applications:**
* **Aho-Corasick**: Used in antivirus software and intrusion detection systems
* **Suffix Arrays**: Essential for bioinformatics and genome analysis
* **Rolling Hash**: Powers content deduplication in distributed systems
* **Bloom Filters**: Optimize database queries and web crawling
* **Radix Trees**: Enable efficient IP routing and autocomplete features
* **Geometric Pattern Matching**: Used in computer vision and robotics
* **Time Series DTW**: Powers speech recognition and financial analysis
* **HMMs**: Enable speech recognition and gene finding
* **Neural Networks**: Form the basis of modern AI pattern recognition
* **Graph Pattern Matching**: Analyzes social networks and protein structures
* **Streaming Pattern Detection**: Enables real-time analytics and IoT monitoring

**Advanced Features:**
* Complete implementations with proper error handling
* Real-world examples from different domains
* Performance optimization techniques
* Scalability considerations
* Memory-efficient algorithms for large datasets

**Industry Applications:**
* Cybersecurity (pattern matching in network traffic)
* Bioinformatics (DNA/protein sequence analysis)
* Finance (algorithmic trading, fraud detection)
* Search engines (text indexing and retrieval)
* Computer vision (object recognition, medical imaging)
* Natural language processing (machine translation, sentiment analysis)
* Social media (recommendation systems, community detection)
* IoT and sensor networks (anomaly detection, predictive maintenance)

Each algorithm includes complexity analysis, practical examples, and discusses trade-offs between accuracy, speed, and memory usage that are crucial for production deployments.

# Pattern Recognition Algorithms in DSA

## 1. String Pattern Matching Algorithms

### 1.1 Naive Pattern Matching (Brute Force)

```python
def naive_search(text, pattern):
    n, m = len(text), len(pattern)
    result = []
    
    for i in range(n - m + 1):
        j = 0
        while j < m and text[i + j] == pattern[j]:
            j += 1
        if j == m:
            result.append(i)
    
    return result

# Example usage
text = "ABABDABACDABABCABCABCABCABC"
pattern = "ABABCAB"
print(naive_search(text, pattern))
```

**Time Complexity:** O(n*m) where n = length of text, m = length of pattern  
**Space Complexity:** O(1)

### 1.2 KMP (Knuth-Morris-Pratt) Algorithm

```python
def kmp_search(text, pattern):
    def compute_lps(pattern):
        m = len(pattern)
        lps = [0] * m
        length = 0
        i = 1
        
        while i < m:
            if pattern[i] == pattern[length]:
                length += 1
                lps[i] = length
                i += 1
            else:
                if length != 0:
                    length = lps[length - 1]
                else:
                    lps[i] = 0
                    i += 1
        return lps
    
    n, m = len(text), len(pattern)
    lps = compute_lps(pattern)
    result = []
    
    i = j = 0
    while i < n:
        if pattern[j] == text[i]:
            i += 1
            j += 1
        
        if j == m:
            result.append(i - j)
            j = lps[j - 1]
        elif i < n and pattern[j] != text[i]:
            if j != 0:
                j = lps[j - 1]
            else:
                i += 1
    
    return result

# Example usage
text = "ABABDABACDABABCABCABCABCABC"
pattern = "ABABCAB"
print(kmp_search(text, pattern))
```

**Time Complexity:** O(n + m)  
**Space Complexity:** O(m) for LPS array

### 1.3 Rabin-Karp Algorithm (Rolling Hash)

```python
def rabin_karp_search(text, pattern, prime=101):
    n, m = len(text), len(pattern)
    pattern_hash = text_hash = 0
    h = 1
    result = []
    
    # Calculate hash value for pattern and first window
    for i in range(m - 1):
        h = (h * 256) % prime
    
    for i in range(m):
        pattern_hash = (256 * pattern_hash + ord(pattern[i])) % prime
        text_hash = (256 * text_hash + ord(text[i])) % prime
    
    # Slide pattern over text
    for i in range(n - m + 1):
        if pattern_hash == text_hash:
            if text[i:i+m] == pattern:
                result.append(i)
        
        if i < n - m:
            text_hash = (256 * (text_hash - ord(text[i]) * h) + ord(text[i + m])) % prime
            if text_hash < 0:
                text_hash += prime
    
    return result

# Example usage
text = "GEEKS FOR GEEKS"
pattern = "GEEK"
print(rabin_karp_search(text, pattern))
```

**Time Complexity:** O(n + m) average case, O(n*m) worst case  
**Space Complexity:** O(1)

### 1.4 Boyer-Moore Algorithm

```python
def boyer_moore_search(text, pattern):
    def bad_character_heuristic(pattern):
        bad_char = [-1] * 256
        for i in range(len(pattern)):
            bad_char[ord(pattern[i])] = i
        return bad_char
    
    n, m = len(text), len(pattern)
    bad_char = bad_character_heuristic(pattern)
    result = []
    
    shift = 0
    while shift <= n - m:
        j = m - 1
        
        while j >= 0 and pattern[j] == text[shift + j]:
            j -= 1
        
        if j < 0:
            result.append(shift)
            shift += (m - bad_char[ord(text[shift + m])] if shift + m < n else 1)
        else:
            shift += max(1, j - bad_char[ord(text[shift + j])])
    
    return result

# Example usage
text = "ABAAABCDABABCABCABCABC"
pattern = "ABC"
print(boyer_moore_search(text, pattern))
```

**Time Complexity:** O(n*m) worst case, O(n/m) best case  
**Space Complexity:** O(σ) where σ is alphabet size

## 2. Subsequence Pattern Matching

### 2.1 Longest Common Subsequence (LCS)

```python
def lcs_length(text1, text2):
    m, n = len(text1), len(text2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i-1] == text2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    return dp[m][n]

def lcs_string(text1, text2):
    m, n = len(text1), len(text2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # Fill dp table
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i-1] == text2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    # Reconstruct LCS
    lcs = []
    i, j = m, n
    while i > 0 and j > 0:
        if text1[i-1] == text2[j-1]:
            lcs.append(text1[i-1])
            i -= 1
            j -= 1
        elif dp[i-1][j] > dp[i][j-1]:
            i -= 1
        else:
            j -= 1
    
    return ''.join(reversed(lcs))

# Example usage
text1 = "AGGTAB"
text2 = "GXTXAYB"
print(f"LCS Length: {lcs_length(text1, text2)}")
print(f"LCS: {lcs_string(text1, text2)}")
```

**Time Complexity:** O(m*n)  
**Space Complexity:** O(m*n)

### 2.2 Longest Increasing Subsequence (LIS)

```python
def lis_length(arr):
    n = len(arr)
    if n == 0:
        return 0
    
    dp = [1] * n
    
    for i in range(1, n):
        for j in range(i):
            if arr[j] < arr[i]:
                dp[i] = max(dp[i], dp[j] + 1)
    
    return max(dp)

def lis_optimized(arr):
    from bisect import bisect_left
    
    if not arr:
        return 0
    
    tails = []
    
    for num in arr:
        pos = bisect_left(tails, num)
        if pos == len(tails):
            tails.append(num)
        else:
            tails[pos] = num
    
    return len(tails)

# Example usage
arr = [10, 9, 2, 5, 3, 7, 101, 18]
print(f"LIS Length (DP): {lis_length(arr)}")
print(f"LIS Length (Optimized): {lis_optimized(arr)}")
```

**Time Complexity:** O(n²) for DP, O(n log n) for optimized  
**Space Complexity:** O(n)

## 3. Array Pattern Recognition

### 3.1 Sliding Window Maximum/Minimum

```python
from collections import deque

def sliding_window_maximum(arr, k):
    dq = deque()
    result = []
    
    for i in range(len(arr)):
        # Remove elements outside current window
        while dq and dq[0] <= i - k:
            dq.popleft()
        
        # Remove smaller elements from rear
        while dq and arr[dq[-1]] <= arr[i]:
            dq.pop()
        
        dq.append(i)
        
        # Add to result if window is complete
        if i >= k - 1:
            result.append(arr[dq[0]])
    
    return result

# Example usage
arr = [1, 2, 3, 1, 4, 5, 2, 3, 6]
k = 3
print(sliding_window_maximum(arr, k))
```

**Time Complexity:** O(n)  
**Space Complexity:** O(k)

### 3.2 Kadane's Algorithm (Maximum Subarray Sum)

```python
def max_subarray_sum(arr):
    max_ending_here = max_so_far = arr[0]
    start = end = s = 0
    
    for i in range(1, len(arr)):
        if max_ending_here < 0:
            max_ending_here = arr[i]
            s = i
        else:
            max_ending_here += arr[i]
        
        if max_so_far < max_ending_here:
            max_so_far = max_ending_here
            start = s
            end = i
    
    return max_so_far, (start, end)

# Example usage
arr = [-2, -3, 4, -1, -2, 1, 5, -3]
max_sum, indices = max_subarray_sum(arr)
print(f"Maximum sum: {max_sum}, Subarray: {arr[indices[0]:indices[1]+1]}")
```

**Time Complexity:** O(n)  
**Space Complexity:** O(1)

## 4. Tree Pattern Recognition

### 4.1 Tree Traversal Patterns

```python
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def inorder_traversal(root):
    result = []
    
    def inorder(node):
        if node:
            inorder(node.left)
            result.append(node.val)
            inorder(node.right)
    
    inorder(root)
    return result

def level_order_traversal(root):
    if not root:
        return []
    
    from collections import deque
    queue = deque([root])
    result = []
    
    while queue:
        level_size = len(queue)
        level = []
        
        for _ in range(level_size):
            node = queue.popleft()
            level.append(node.val)
            
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        
        result.append(level)
    
    return result

# Path Sum Pattern
def has_path_sum(root, target_sum):
    if not root:
        return False
    
    if not root.left and not root.right:
        return root.val == target_sum
    
    return (has_path_sum(root.left, target_sum - root.val) or 
            has_path_sum(root.right, target_sum - root.val))
```

**Time Complexity:** O(n) for all traversals  
**Space Complexity:** O(h) for recursive, O(w) for level order (h=height, w=max width)

## 5. Graph Pattern Recognition

### 5.1 Cycle Detection

```python
def has_cycle_undirected(graph):
    visited = set()
    
    def dfs(node, parent):
        visited.add(node)
        
        for neighbor in graph[node]:
            if neighbor not in visited:
                if dfs(neighbor, node):
                    return True
            elif neighbor != parent:
                return True
        
        return False
    
    for node in graph:
        if node not in visited:
            if dfs(node, -1):
                return True
    
    return False

def has_cycle_directed(graph):
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {node: WHITE for node in graph}
    
    def dfs(node):
        if color[node] == GRAY:
            return True
        if color[node] == BLACK:
            return False
        
        color[node] = GRAY
        
        for neighbor in graph[node]:
            if dfs(neighbor):
                return True
        
        color[node] = BLACK
        return False
    
    for node in graph:
        if color[node] == WHITE:
            if dfs(node):
                return True
    
    return False

# Example usage
undirected_graph = {0: [1, 2], 1: [0, 2], 2: [0, 1, 3], 3: [2]}
directed_graph = {0: [1], 1: [2], 2: [3], 3: [1]}

print(f"Undirected graph has cycle: {has_cycle_undirected(undirected_graph)}")
print(f"Directed graph has cycle: {has_cycle_directed(directed_graph)}")
```

**Time Complexity:** O(V + E)  
**Space Complexity:** O(V)

## 6. Advanced Pattern Recognition

### 6.1 Z Algorithm (Linear Time Pattern Matching)

```python
def z_algorithm(s):
    n = len(s)
    z = [0] * n
    l, r = 0, 0
    
    for i in range(1, n):
        if i <= r:
            z[i] = min(r - i + 1, z[i - l])
        
        while i + z[i] < n and s[z[i]] == s[i + z[i]]:
            z[i] += 1
        
        if i + z[i] - 1 > r:
            l, r = i, i + z[i] - 1
    
    return z

def z_search(text, pattern):
    combined = pattern + "$" + text
    z_array = z_algorithm(combined)
    pattern_len = len(pattern)
    result = []
    
    for i in range(pattern_len + 1, len(combined)):
        if z_array[i] == pattern_len:
            result.append(i - pattern_len - 1)
    
    return result

# Example usage
text = "AABAACAADAABAABA"
pattern = "AABA"
print(z_search(text, pattern))
```

**Time Complexity:** O(n + m)  
**Space Complexity:** O(n + m)

### 6.2 Manacher's Algorithm (Palindrome Detection)

```python
def manacher_algorithm(s):
    # Transform string: "abc" -> "^#a#b#c#$"
    transformed = "^#" + "#".join(s) + "#$"
    n = len(transformed)
    p = [0] * n
    center = right = 0
    
    for i in range(1, n - 1):
        mirror = 2 * center - i
        
        if i < right:
            p[i] = min(right - i, p[mirror])
        
        # Try to expand palindrome centered at i
        while transformed[i + p[i] + 1] == transformed[i - p[i] - 1]:
            p[i] += 1
        
        # If palindrome centered at i extends past right, adjust center and right
        if i + p[i] > right:
            center, right = i, i + p[i]
    
    return p

def longest_palindrome(s):
    if not s:
        return ""
    
    p = manacher_algorithm(s)
    max_len = 0
    center_index = 0
    
    for i in range(len(p)):
        if p[i] > max_len:
            max_len = p[i]
            center_index = i
    
    start = (center_index - max_len) // 2
    return s[start:start + max_len]

# Example usage
s = "babad"
print(f"Longest palindrome in '{s}': {longest_palindrome(s)}")
```

**Time Complexity:** O(n)  
**Space Complexity:** O(n)

## 7. Advanced Real-World Pattern Recognition

### 7.1 Aho-Corasick Algorithm (Multiple Pattern Matching)

*Used in: Antivirus software, intrusion detection, text editors*

```python
from collections import defaultdict, deque

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False
        self.failure = None
        self.output = []

class AhoCorasick:
    def __init__(self):
        self.root = TrieNode()
        self.patterns = []
    
    def add_pattern(self, pattern):
        self.patterns.append(pattern)
        node = self.root
        for char in pattern:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end = True
        node.output.append(len(self.patterns) - 1)
    
    def build_failure_function(self):
        queue = deque()
        
        # Initialize failure links for depth 1
        for child in self.root.children.values():
            child.failure = self.root
            queue.append(child)
        
        while queue:
            current = queue.popleft()
            
            for char, child in current.children.items():
                queue.append(child)
                
                # Find failure link
                failure = current.failure
                while failure and char not in failure.children:
                    failure = failure.failure
                
                child.failure = failure.children.get(char, self.root)
                child.output.extend(child.failure.output)
    
    def search(self, text):
        self.build_failure_function()
        matches = []
        node = self.root
        
        for i, char in enumerate(text):
            # Follow failure links until we find a match or reach root
            while node and char not in node.children:
                node = node.failure
            
            if not node:
                node = self.root
                continue
            
            node = node.children[char]
            
            # Check for pattern matches
            for pattern_idx in node.output:
                pattern_len = len(self.patterns[pattern_idx])
                start_pos = i - pattern_len + 1
                matches.append((start_pos, pattern_idx, self.patterns[pattern_idx]))
        
        return matches

# Example usage - Virus signature detection
ac = AhoCorasick()
signatures = ["virus", "malware", "trojan", "spyware"]
for sig in signatures:
    ac.add_pattern(sig)

text = "This file contains virus and malware signatures for trojan detection"
matches = ac.search(text)
for start, idx, pattern in matches:
    print(f"Found '{pattern}' at position {start}")
```

**Time Complexity:** O(n + m + z) where n=text length, m=total pattern length, z=matches  
**Space Complexity:** O(m)  
**Real-world use:** Antivirus scanning, network intrusion detection, plagiarism detection

### 7.2 Suffix Array with LCP (Longest Common Prefix)

*Used in: Bioinformatics, data compression, text indexing*

```python
def build_suffix_array(s):
    """Build suffix array using counting sort approach"""
    n = len(s)
    suffixes = [(s[i:], i) for i in range(n)]
    suffixes.sort()
    return [suffix[1] for suffix in suffixes]

def build_lcp_array(s, suffix_array):
    """Build LCP array using Kasai's algorithm"""
    n = len(s)
    rank = [0] * n
    lcp = [0] * (n - 1)
    
    # Build rank array
    for i in range(n):
        rank[suffix_array[i]] = i
    
    h = 0
    for i in range(n):
        if rank[i] > 0:
            j = suffix_array[rank[i] - 1]
            while (i + h < n and j + h < n and 
                   s[i + h] == s[j + h]):
                h += 1
            lcp[rank[i] - 1] = h
            if h > 0:
                h -= 1
    
    return lcp

class SuffixArrayLCP:
    def __init__(self, text):
        self.text = text + "$"  # Add sentinel
        self.suffix_array = build_suffix_array(self.text)
        self.lcp_array = build_lcp_array(self.text, self.suffix_array)
        self.n = len(self.text)
    
    def search_pattern(self, pattern):
        """Binary search for pattern occurrences"""
        def compare_suffix(idx, pattern):
            suffix = self.text[self.suffix_array[idx]:]
            return suffix[:len(pattern)] == pattern
        
        left, right = 0, self.n - 1
        results = []
        
        # Find leftmost occurrence
        while left <= right:
            mid = (left + right) // 2
            suffix = self.text[self.suffix_array[mid]:]
            if suffix.startswith(pattern):
                results.append(self.suffix_array[mid])
                # Continue searching for more occurrences
                i = mid - 1
                while i >= 0 and self.text[self.suffix_array[i]:].startswith(pattern):
                    results.append(self.suffix_array[i])
                    i -= 1
                i = mid + 1
                while i < self.n and self.text[self.suffix_array[i]:].startswith(pattern):
                    results.append(self.suffix_array[i])
                    i += 1
                break
            elif suffix < pattern:
                left = mid + 1
            else:
                right = mid - 1
        
        return sorted(results)
    
    def longest_repeated_substring(self):
        """Find longest repeated substring using LCP array"""
        max_lcp = max(self.lcp_array) if self.lcp_array else 0
        if max_lcp == 0:
            return ""
        
        idx = self.lcp_array.index(max_lcp)
        return self.text[self.suffix_array[idx]:self.suffix_array[idx] + max_lcp]

# Example usage - DNA sequence analysis
dna_sequence = "ATCGATCGAATCG"
sa_lcp = SuffixArrayLCP(dna_sequence)
print(f"Longest repeated substring: {sa_lcp.longest_repeated_substring()}")
print(f"Pattern 'ATC' found at: {sa_lcp.search_pattern('ATC')}")
```

**Time Complexity:** O(n log n) for construction, O(log n + k) for search  
**Space Complexity:** O(n)  
**Real-world use:** Genome analysis, data compression algorithms, full-text search

### 7.3 Rolling Hash with Polynomial Hashing

*Used in: Distributed systems, database sharding, content deduplication*

```python
class RollingHash:
    def __init__(self, base=257, mod=10**9 + 7):
        self.base = base
        self.mod = mod
        self.hash_values = []
        self.powers = []
    
    def compute_hash(self, s):
        """Compute hash for entire string"""
        h = 0
        power = 1
        self.powers = [1]
        
        for i, char in enumerate(s):
            h = (h + ord(char) * power) % self.mod
            self.hash_values.append(h)
            power = (power * self.base) % self.mod
            self.powers.append(power)
        
        return h
    
    def get_substring_hash(self, left, right):
        """Get hash of substring s[left:right+1]"""
        if left == 0:
            return self.hash_values[right]
        
        hash_val = (self.hash_values[right] - self.hash_values[left - 1]) % self.mod
        hash_val = (hash_val * pow(self.powers[left], self.mod - 2, self.mod)) % self.mod
        return hash_val
    
    def find_duplicates(self, text, window_size):
        """Find all duplicate substrings of given size"""
        if window_size > len(text):
            return []
        
        self.hash_values = []
        self.compute_hash(text)
        
        hash_count = {}
        duplicates = []
        
        for i in range(len(text) - window_size + 1):
            substr_hash = self.get_substring_hash(i, i + window_size - 1)
            substr = text[i:i + window_size]
            
            if substr_hash in hash_count:
                if substr not in hash_count[substr_hash]:
                    duplicates.append((substr, [hash_count[substr_hash][0], i]))
                    hash_count[substr_hash].append(i)
                else:
                    duplicates[-1][1].append(i)
            else:
                hash_count[substr_hash] = [i]
        
        return duplicates

# Example usage - Document deduplication
rh = RollingHash()
document = "This is a sample text. This is a sample for duplicate detection. This is a test."
duplicates = rh.find_duplicates(document, 10)
for substr, positions in duplicates:
    print(f"Duplicate '{substr}' found at positions: {positions}")
```

**Time Complexity:** O(n) for preprocessing, O(1) for substring hash  
**Space Complexity:** O(n)  
**Real-world use:** Content deduplication, distributed hash tables, caching systems

### 7.4 Bloom Filter for Pattern Existence

*Used in: Databases, web crawlers, distributed systems*

```python
import hashlib
import math

class BloomFilter:
    def __init__(self, expected_elements, false_positive_rate=0.01):
        self.expected_elements = expected_elements
        self.false_positive_rate = false_positive_rate
        
        # Calculate optimal size and hash functions
        self.size = int(-expected_elements * math.log(false_positive_rate) / (math.log(2) ** 2))
        self.hash_count = int(self.size * math.log(2) / expected_elements)
        
        self.bit_array = [0] * self.size
        self.elements_added = 0
    
    def _hash(self, item, seed):
        """Generate hash using different seeds"""
        hasher = hashlib.md5()
        hasher.update(f"{item}{seed}".encode('utf-8'))
        return int(hasher.hexdigest(), 16) % self.size
    
    def add(self, item):
        """Add item to bloom filter"""
        for i in range(self.hash_count):
            index = self._hash(item, i)
            self.bit_array[index] = 1
        self.elements_added += 1
    
    def contains(self, item):
        """Check if item might be in the set"""
        for i in range(self.hash_count):
            index = self._hash(item, i)
            if self.bit_array[index] == 0:
                return False
        return True
    
    def false_positive_probability(self):
        """Calculate actual false positive probability"""
        return (1 - math.exp(-self.hash_count * self.elements_added / self.size)) ** self.hash_count

# Example usage - Web crawler URL filtering
bf = BloomFilter(expected_elements=1000000, false_positive_rate=0.01)

# Simulate crawled URLs
crawled_urls = [
    "https://example.com/page1",
    "https://example.com/page2",
    "https://example.com/page3"
]

for url in crawled_urls:
    bf.add(url)

# Check if URL was already crawled
test_urls = [
    "https://example.com/page1",  # Should return True
    "https://example.com/newpage"  # Might return False
]

for url in test_urls:
    if bf.contains(url):
        print(f"URL {url} might have been crawled (could be false positive)")
    else:
        print(f"URL {url} definitely not crawled")

print(f"False positive probability: {bf.false_positive_probability():.4f}")
```

**Time Complexity:** O(k) for add/query where k=number of hash functions  
**Space Complexity:** O(m) where m=bit array size  
**Real-world use:** Database query optimization, web crawling, caching

### 7.5 Trie with Compressed Paths (Radix Tree)

*Used in: IP routing tables, autocomplete systems, file systems*

```python
class RadixNode:
    def __init__(self):
        self.children = {}
        self.is_end = False
        self.compressed_key = ""
        self.value = None

class RadixTree:
    def __init__(self):
        self.root = RadixNode()
    
    def insert(self, key, value=None):
        """Insert key-value pair into radix tree"""
        node = self.root
        i = 0
        
        while i < len(key):
            found_child = None
            
            # Find child with matching prefix
            for child_key, child_node in node.children.items():
                if key[i:i+len(child_key)] == child_key:
                    found_child = (child_key, child_node)
                    break
                
                # Check for partial match
                common_prefix = ""
                for j in range(min(len(key) - i, len(child_key))):
                    if key[i + j] == child_key[j]:
                        common_prefix += key[i + j]
                    else:
                        break
                
                if common_prefix:
                    # Split the child node
                    old_child = node.children[child_key]
                    del node.children[child_key]
                    
                    # Create intermediate node
                    intermediate = RadixNode()
                    intermediate.compressed_key = common_prefix
                    node.children[common_prefix] = intermediate
                    
                    # Update old child
                    old_child.compressed_key = child_key[len(common_prefix):]
                    intermediate.children[old_child.compressed_key] = old_child
                    
                    found_child = (common_prefix, intermediate)
                    break
            
            if found_child:
                child_key, child_node = found_child
                i += len(child_key)
                node = child_node
            else:
                # Create new node for remaining key
                new_key = key[i:]
                new_node = RadixNode()
                new_node.compressed_key = new_key
                new_node.is_end = True
                new_node.value = value
                node.children[new_key] = new_node
                return
        
        node.is_end = True
        node.value = value
    
    def search(self, key):
        """Search for key in radix tree"""
        node = self.root
        i = 0
        
        while i < len(key) and node:
            found = False
            for child_key, child_node in node.children.items():
                if key[i:].startswith(child_key):
                    i += len(child_key)
                    node = child_node
                    found = True
                    break
            
            if not found:
                return None
        
        return node.value if node and node.is_end else None
    
    def autocomplete(self, prefix):
        """Get all keys with given prefix"""
        node = self.root
        i = 0
        
        # Navigate to prefix node
        while i < len(prefix) and node:
            found = False
            for child_key, child_node in node.children.items():
                if prefix[i:].startswith(child_key):
                    i += len(child_key)
                    node = child_node
                    found = True
                    break
                elif child_key.startswith(prefix[i:]):
                    # Partial match - prefix ends within compressed key
                    return [prefix + child_key[len(prefix[i:]):]] if child_node.is_end else []
            
            if not found:
                return []
        
        # Collect all completions from current node
        results = []
        
        def dfs(current_node, current_prefix):
            if current_node.is_end:
                results.append(current_prefix)
            
            for child_key, child_node in current_node.children.items():
                dfs(child_node, current_prefix + child_key)
        
        dfs(node, prefix)
        return results

# Example usage - Autocomplete system
rt = RadixTree()

# Insert programming languages
languages = ["python", "javascript", "java", "julia", "rust", "ruby", "go", "swift"]
for lang in languages:
    rt.insert(lang, f"{lang}_info")

# Search functionality
print(f"Search 'python': {rt.search('python')}")
print(f"Search 'php': {rt.search('php')}")

# Autocomplete functionality
print(f"Autocomplete 'ja': {rt.autocomplete('ja')}")
print(f"Autocomplete 'ru': {rt.autocomplete('ru')}")
```

**Time Complexity:** O(k) where k=key length  
**Space Complexity:** O(ALPHABET_SIZE *N* M) worst case  
**Real-world use:** IP routing, file system directories, autocomplete

### 7.6 Geometric Pattern Matching (2D)

*Used in: Computer vision, image processing, robotics*

```python
import numpy as np
from typing import List, Tuple

class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
    
    def distance(self, other):
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
    
    def __repr__(self):
        return f"Point({self.x}, {self.y})"

class GeometricPatternMatcher:
    def __init__(self, tolerance: float = 1e-6):
        self.tolerance = tolerance
    
    def normalize_pattern(self, points: List[Point]) -> List[Point]:
        """Normalize pattern to unit scale and center at origin"""
        if not points:
            return points
        
        # Find centroid
        cx = sum(p.x for p in points) / len(points)
        cy = sum(p.y for p in points) / len(points)
        
        # Center points
        centered = [Point(p.x - cx, p.y - cy) for p in points]
        
        # Find scale factor
        max_dist = max(Point(0, 0).distance(p) for p in centered)
        if max_dist < self.tolerance:
            return centered
        
        # Normalize to unit scale
        return [Point(p.x / max_dist, p.y / max_dist) for p in centered]
    
    def compute_shape_signature(self, points: List[Point]) -> List[float]:
        """Compute rotation-invariant shape signature"""
        if len(points) < 3:
            return []
        
        normalized = self.normalize_pattern(points)
        n = len(normalized)
        
        # Compute distances from centroid
        distances = [Point(0, 0).distance(p) for p in normalized]
        
        # Compute angles between consecutive points
        angles = []
        for i in range(n):
            p1 = normalized[i]
            p2 = normalized[(i + 1) % n]
            angle = np.arctan2(p2.y - p1.y, p2.x - p1.x)
            angles.append(angle)
        
        # Normalize angles to be rotation-invariant
        angle_diffs = []
        for i in range(n):
            diff = angles[(i + 1) % n] - angles[i]
            if diff > np.pi:
                diff -= 2 * np.pi
            elif diff < -np.pi:
                diff += 2 * np.pi
            angle_diffs.append(diff)
        
        # Combine distances and angle differences
        signature = []
        for i in range(n):
            signature.extend([distances[i], angle_diffs[i]])
        
        return signature
    
    def match_patterns(self, pattern: List[Point], target: List[Point]) -> float:
        """Compute similarity between two patterns (0.0 = identical, higher = more different)"""
        sig1 = self.compute_shape_signature(pattern)
        sig2 = self.compute_shape_signature(target)
        
        if len(sig1) != len(sig2):
            return float('inf')
        
        if not sig1:
            return 0.0
        
        # Compute Euclidean distance between signatures
        distance = sum((a - b) ** 2 for a, b in zip(sig1, sig2)) ** 0.5
        return distance
    
    def find_pattern_in_image(self, pattern: List[Point], image_points: List[Point], 
                            window_size: int = 5) -> List[Tuple[List[Point], float]]:
        """Find occurrences of pattern in image points using sliding window"""
        if len(image_points) < len(pattern):
            return []
        
        matches = []
        
        for i in range(len(image_points) - len(pattern) + 1):
            window = image_points[i:i + len(pattern)]
            similarity = self.match_patterns(pattern, window)
            
            if similarity < self.tolerance * 10:  # Threshold for matching
                matches.append((window, similarity))
        
        # Sort by similarity (best matches first)
        matches.sort(key=lambda x: x[1])
        return matches

# Example usage - Shape recognition in computer vision
gpm = GeometricPatternMatcher(tolerance=0.1)

# Define a triangle pattern
triangle_pattern = [
    Point(0, 0),
    Point(1, 0),
    Point(0.5, 0.866)  # Equilateral triangle
]

# Define some test shapes
test_triangle = [
    Point(2, 2),
    Point(4, 2),
    Point(3, 3.732)  # Scaled triangle
]

test_square = [
    Point(0, 0),
    Point(1, 0),
    Point(1, 1),
    Point(0, 1)
]

# Test pattern matching
triangle_similarity = gpm.match_patterns(triangle_pattern, test_triangle)
square_similarity = gpm.match_patterns(triangle_pattern, test_square)

print(f"Triangle similarity: {triangle_similarity:.4f}")
print(f"Square similarity: {square_similarity:.4f}")

# Simulate finding triangles in a point cloud
image_points = [
    Point(1, 1), Point(2, 1), Point(1.5, 1.866),  # Triangle 1
    Point(5, 5), Point(6, 5), Point(5.5, 5.866),  # Triangle 2
    Point(10, 10), Point(11, 10), Point(11, 11), Point(10, 11)  # Square
]

matches = gpm.find_pattern_in_image(triangle_pattern, image_points)
print(f"Found {len(matches)} potential triangle matches")
```

**Time Complexity:** O(n*m) where n=image points, m=pattern points  
**Space Complexity:** O(m) for pattern storage  
**Real-world use:** Object recognition, medical imaging, quality control

### 7.7 Time Series Pattern Recognition (DTW)

*Used in: Speech recognition, financial analysis, bioinformatics*

```python
import numpy as np
from typing import List, Tuple

class DTWMatcher:
    def __init__(self):
        self.cost_matrix = None
    
    def dtw_distance(self, series1: List[float], series2: List[float]) -> float:
        """Compute Dynamic Time Warping distance between two time series"""
        n, m = len(series1), len(series2)
        
        # Create cost matrix
        self.cost_matrix = np.full((n + 1, m + 1), np.inf)
        self.cost_matrix[0, 0] = 0
        
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                cost = abs(series1[i-1] - series2[j-1])
                self.cost_matrix[i, j] = cost + min(
                    self.cost_matrix[i-1, j],      # insertion
                    self.cost_matrix[i, j-1],      # deletion
                    self.cost_matrix[i-1, j-1]     # match
                )
        
        return self.cost_matrix[n, m]
    
    def get_warping_path(self) -> List[Tuple[int, int]]:
        """Get the optimal warping path from the last DTW computation"""
        if self.cost_matrix is None:
            return []
        
        n, m = self.cost_matrix.shape
        i, j = n - 1, m - 1
        path = []
        
        while i > 0 or j > 0:
            path.append((i-1, j-1))
            
            if i == 0:
                j -= 1
            elif j == 0:
                i -= 1
            else:
                # Choose minimum cost predecessor
                costs = [
                    self.cost_matrix[i-1, j-1],    # diagonal
                    self.cost_matrix[i-1, j],      # up
                    self.cost_matrix[i, j-1]       # left
                ]
                min_idx = costs.index(min(costs))
                if min_idx == 0:
                    i, j = i-1, j-1
                elif min_idx == 1:
                    i -= 1
                else:
                    j -= 1
        
        return path[::-1]
    
    def find_pattern_in_series(self, pattern: List[float], series: List[float], 
                             threshold: float = None) -> List[Tuple[int, int, float]]:
        """Find occurrences of pattern in time series using sliding DTW"""
        pattern_len = len(pattern)
        matches = []
        
        if threshold is None:
            threshold = pattern_len * 0.5  # Default threshold
        
        for i in range(len(series) - pattern_len + 1):
            window = series[i:i + pattern_len]
            distance = self.dtw_distance(pattern, window)
            
            if distance <= threshold:
                matches.append((i, i + pattern_len - 1, distance))
        
        return matches
    
    def normalize_series(self, series: List[float]) -> List[float]:
        """Normalize time series to zero mean and unit variance"""
        if not series:
            return series
        
        mean_val = np.mean(series)
        std_val = np.std(series)
        
        if std_val == 0:
            return [0] * len(series)
        
        return [(x - mean_val) / std_val for x in series]

class PatternLibrary:
    def __init__(self):
        self.patterns = {}
        self.dtw = DTWMatcher()
    
    def add_pattern(self, name: str, pattern: List[float]):
        """Add a named pattern to the library"""
        self.patterns[name] = self.dtw.normalize_series(pattern)
    
    def classify_series(self, series: List[float]) -> Tuple[str, float]:
        """Classify a time series against all known patterns"""
        normalized_series = self.dtw.normalize_series(series)
        best_match = None
        best_distance = float('inf')
        
        for name, pattern in self.patterns.items():
            distance = self.dtw.dtw_distance(pattern, normalized_series)
            if distance < best_distance:
                best_distance = distance
                best_match = name
        
        return best_match, best_distance

# Example usage - Financial pattern recognition
dtw = DTWMatcher()
pattern_lib = PatternLibrary()

# Define common financial patterns
uptrend = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
downtrend = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
sideways = [5, 5.1, 4.9, 5.2, 4.8, 5.0, 5.1, 4.9, 5.0, 5.1]
spike = [5, 5, 5, 10, 5, 5, 5, 5, 5, 5]

# Add patterns to library
pattern_lib.add_pattern("uptrend", uptrend)
pattern_lib.add_pattern("downtrend", downtrend)
pattern_lib.add_pattern("sideways", sideways)
pattern_lib.add_pattern("spike", spike)

# Test with sample data
test_series1 = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]  # Should match uptrend
test_series2 = [100, 90, 80, 70, 60, 50, 40, 30, 20, 10]  # Should match downtrend

result1 = pattern_lib.classify_series(test_series1)
result2 = pattern_lib.classify_series(test_series2)

print(f"Series 1 classified as: {result1[0]} with distance: {result1[1]:.2f}")
print(f"Series 2 classified as: {result2[0]} with distance: {result2[1]:.2f}")

# Find pattern occurrences in longer series
long_series = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 5, 4, 3, 2, 1, 5, 5, 5, 5, 5]
matches = dtw.find_pattern_in_series(uptrend, long_series, threshold=5.0)
print(f"Found uptrend pattern at positions: {matches}")
```

**Time Complexity:** O(n*m) where n,m are series lengths  
**Space Complexity:** O(n*m) for cost matrix  
**Real-world use:** Speech recognition, gesture recognition, financial analysis, medical signal processing

### 7.8 Approximate String Matching (Edit Distance Variants)

*Used in: Spell checkers, DNA sequence alignment, fuzzy search*

```python
class ApproximateStringMatcher:
    def __init__(self):
        self.dp = None
    
    def levenshtein_distance(self, s1: str, s2: str) -> int:
        """Classic edit distance with insertions, deletions, substitutions"""
        m, n = len(s1), len(s2)
        self.dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        # Initialize base cases
        for i in range(m + 1):
            self.dp[i][0] = i
        for j in range(n + 1):
            self.dp[0][j] = j
        
        # Fill DP table
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i-1] == s2[j-1]:
                    self.dp[i][j] = self.dp[i-1][j-1]
                else:
                    self.dp[i][j] = 1 + min(
                        self.dp[i-1][j],    # deletion
                        self.dp[i][j-1],    # insertion
                        self.dp[i-1][j-1]   # substitution
                    )
        
        return self.dp[m][n]
    
    def damerau_levenshtein_distance(self, s1: str, s2: str) -> int:
        """Edit distance with transpositions (swapping adjacent characters)"""
        m, n = len(s1), len(s2)
        
        # Create character frequency map
        char_map = {}
        for c in s1 + s2:
            char_map[c] = 0
        
        # Extended DP table
        max_dist = m + n
        dp = [[max_dist] * (n + 2) for _ in range(m + 2)]
        dp[0][0] = max_dist
        
        for i in range(0, m + 1):
            dp[i+1][0] = max_dist
            dp[i+1][1] = i
        for j in range(0, n + 1):
            dp[0][j+1] = max_dist
            dp[1][j+1] = j
        
        for i in range(1, m + 1):
            db = 0
            for j in range(1, n + 1):
                i1 = char_map[s2[j-1]]
                j1 = db
                cost = 1
                
                if s1[i-1] == s2[j-1]:
                    cost = 0
                    db = j
                
                dp[i+1][j+1] = min(
                    dp[i][j] + cost,                    # substitution
                    dp[i+1][j] + 1,                     # insertion
                    dp[i][j+1] + 1,                     # deletion
                    dp[i1][j1] + (i-i1-1) + 1 + (j-j1-1)  # transposition
                )
            
            char_map[s1[i-1]] = i
        
        return dp[m+1][n+1]
    
    def fuzzy_search(self, pattern: str, text: str, max_distance: int = 2) -> List[Tuple[int, int, int]]:
        """Find all approximate matches of pattern in text"""
        matches = []
        pattern_len = len(pattern)
        
        for i in range(len(text) - pattern_len + max_distance + 1):
            # Try different window sizes around pattern length
            for window_size in range(max(1, pattern_len - max_distance), 
                                   min(len(text) - i + 1, pattern_len + max_distance + 1)):
                if i + window_size > len(text):
                    break
                
                substring = text[i:i + window_size]
                distance = self.levenshtein_distance(pattern, substring)
                
                if distance <= max_distance:
                    matches.append((i, i + window_size - 1, distance))
        
        return matches
    
    def spell_check(self, word: str, dictionary: List[str], max_suggestions: int = 5) -> List[Tuple[str, int]]:
        """Find closest dictionary words for spell checking"""
        suggestions = []
        
        for dict_word in dictionary:
            distance = self.levenshtein_distance(word, dict_word)
            suggestions.append((dict_word, distance))
        
        # Sort by distance and return top suggestions
        suggestions.sort(key=lambda x: x[1])
        return suggestions[:max_suggestions]

class BioinformaticsAligner:
    def __init__(self, match_score: int = 2, mismatch_penalty: int = -1, gap_penalty: int = -1):
        self.match_score = match_score
        self.mismatch_penalty = mismatch_penalty
        self.gap_penalty = gap_penalty
    
    def needleman_wunsch(self, seq1: str, seq2: str) -> Tuple[str, str, int]:
        """Global sequence alignment using Needleman-Wunsch algorithm"""
        m, n = len(seq1), len(seq2)
        
        # Initialize scoring matrix
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        # Initialize first row and column
        for i in range(m + 1):
            dp[i][0] = i * self.gap_penalty
        for j in range(n + 1):
            dp[0][j] = j * self.gap_penalty
        
        # Fill scoring matrix
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                match = dp[i-1][j-1] + (self.match_score if seq1[i-1] == seq2[j-1] else self.mismatch_penalty)
                delete = dp[i-1][j] + self.gap_penalty
                insert = dp[i][j-1] + self.gap_penalty
                
                dp[i][j] = max(match, delete, insert)
        
        # Traceback to find alignment
        aligned1, aligned2 = "", ""
        i, j = m, n
        
        while i > 0 or j > 0:
            if i > 0 and j > 0:
                score_current = dp[i][j]
                score_diag = dp[i-1][j-1]
                score_up = dp[i-1][j]
                score_left = dp[i][j-1]
                
                if score_current == score_diag + (self.match_score if seq1[i-1] == seq2[j-1] else self.mismatch_penalty):
                    aligned1 = seq1[i-1] + aligned1
                    aligned2 = seq2[j-1] + aligned2
                    i -= 1
                    j -= 1
                elif score_current == score_up + self.gap_penalty:
                    aligned1 = seq1[i-1] + aligned1
                    aligned2 = "-" + aligned2
                    i -= 1
                else:
                    aligned1 = "-" + aligned1
                    aligned2 = seq2[j-1] + aligned2
                    j -= 1
            elif i > 0:
                aligned1 = seq1[i-1] + aligned1
                aligned2 = "-" + aligned2
                i -= 1
            else:
                aligned1 = "-" + aligned1
                aligned2 = seq2[j-1] + aligned2
                j -= 1
        
        return aligned1, aligned2, dp[m][n]
    
    def smith_waterman(self, seq1: str, seq2: str) -> Tuple[str, str, int]:
        """Local sequence alignment using Smith-Waterman algorithm"""
        m, n = len(seq1), len(seq2)
        
        # Initialize scoring matrix
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        max_score = 0
        max_i = max_j = 0
        
        # Fill scoring matrix
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                match = dp[i-1][j-1] + (self.match_score if seq1[i-1] == seq2[j-1] else self.mismatch_penalty)
                delete = dp[i-1][j] + self.gap_penalty
                insert = dp[i][j-1] + self.gap_penalty
                
                dp[i][j] = max(0, match, delete, insert)
                
                if dp[i][j] > max_score:
                    max_score = dp[i][j]
                    max_i, max_j = i, j
        
        # Traceback from maximum score
        aligned1, aligned2 = "", ""
        i, j = max_i, max_j
        
        while i > 0 and j > 0 and dp[i][j] > 0:
            score_current = dp[i][j]
            score_diag = dp[i-1][j-1]
            score_up = dp[i-1][j]
            score_left = dp[i][j-1]
            
            if score_current == score_diag + (self.match_score if seq1[i-1] == seq2[j-1] else self.mismatch_penalty):
                aligned1 = seq1[i-1] + aligned1
                aligned2 = seq2[j-1] + aligned2
                i -= 1
                j -= 1
            elif score_current == score_up + self.gap_penalty:
                aligned1 = seq1[i-1] + aligned1
                aligned2 = "-" + aligned2
                i -= 1
            else:
                aligned1 = "-" + aligned1
                aligned2 = seq2[j-1] + aligned2
                j -= 1
        
        return aligned1, aligned2, max_score

# Example usage - Spell checker
spell_checker = ApproximateStringMatcher()
dictionary = ["hello", "world", "python", "programming", "algorithm", "computer", "science"]

# Test spell checking
misspelled = "progaming"
suggestions = spell_checker.spell_check(misspelled, dictionary, max_suggestions=3)
print(f"Suggestions for '{misspelled}': {suggestions}")

# Test fuzzy search
text = "This is a sample text with some programming concepts"
pattern = "program"
matches = spell_checker.fuzzy_search(pattern, text, max_distance=2)
print(f"Fuzzy matches for '{pattern}': {matches}")

# Example usage - DNA sequence alignment
aligner = BioinformaticsAligner()

# DNA sequences
seq1 = "ACGTACGT"
seq2 = "ACGTTCGT"

global_alignment = aligner.needleman_wunsch(seq1, seq2)
print(f"Global alignment:")
print(f"Seq1: {global_alignment[0]}")
print(f"Seq2: {global_alignment[1]}")
print(f"Score: {global_alignment[2]}")

local_alignment = aligner.smith_waterman(seq1, seq2)
print(f"\nLocal alignment:")
print(f"Seq1: {local_alignment[0]}")
print(f"Seq2: {local_alignment[1]}")
print(f"Score: {local_alignment[2]}")
```

**Time Complexity:** O(n*m) for all alignment algorithms  
**Space Complexity:** O(n*m) for DP table  
**Real-world use:** Bioinformatics, spell checking, plagiarism detection, version control

### 7.9 Probabilistic Pattern Matching (HMM)

*Used in: Speech recognition, bioinformatics, natural language processing*

```python
import numpy as np
from typing import Dict, List, Tuple

class HiddenMarkovModel:
    def __init__(self, states: List[str], observations: List[str]):
        self.states = states
        self.observations = observations
        self.n_states = len(states)
        self.n_observations = len(observations)
        
        # State to index mappings
        self.state_to_idx = {state: i for i, state in enumerate(states)}
        self.obs_to_idx = {obs: i for i, obs in enumerate(observations)}
        
        # Initialize matrices
        self.transition_prob = np.zeros((self.n_states, self.n_states))
        self.emission_prob = np.zeros((self.n_states, self.n_observations))
        self.initial_prob = np.zeros(self.n_states)
    
    def set_initial_probabilities(self, initial_probs: Dict[str, float]):
        """Set initial state probabilities"""
        for state, prob in initial_probs.items():
            self.initial_prob[self.state_to_idx[state]] = prob
    
    def set_transition_probabilities(self, transitions: Dict[str, Dict[str, float]]):
        """Set state transition probabilities"""
        for from_state, to_states in transitions.items():
            from_idx = self.state_to_idx[from_state]
            for to_state, prob in to_states.items():
                to_idx = self.state_to_idx[to_state]
                self.transition_prob[from_idx][to_idx] = prob
    
    def set_emission_probabilities(self, emissions: Dict[str, Dict[str, float]]):
        """Set observation emission probabilities"""
        for state, observations in emissions.items():
            state_idx = self.state_to_idx[state]
            for obs, prob in observations.items():
                obs_idx = self.obs_to_idx[obs]
                self.emission_prob[state_idx][obs_idx] = prob
    
    def viterbi(self, observations: List[str]) -> Tuple[List[str], float]:
        """Find most likely state sequence using Viterbi algorithm"""
        T = len(observations)
        
        # Convert observations to indices
        obs_indices = [self.obs_to_idx[obs] for obs in observations]
        
        # Initialize Viterbi tables
        viterbi_prob = np.zeros((self.n_states, T))
        viterbi_path = np.zeros((self.n_states, T), dtype=int)
        
        # Initialize first column
        for s in range(self.n_states):
            viterbi_prob[s][0] = self.initial_prob[s] * self.emission_prob[s][obs_indices[0]]
            viterbi_path[s][0] = 0
        
        # Fill Viterbi table
        for t in range(1, T):
            for s in range(self.n_states):
                # Find best previous state
                trans_probs = viterbi_prob[:, t-1] * self.transition_prob[:, s]
                best_prev_state = np.argmax(trans_probs)
                
                viterbi_prob[s][t] = (trans_probs[best_prev_state] * 
                                    self.emission_prob[s][obs_indices[t]])
                viterbi_path[s][t] = best_prev_state
        
        # Backtrack to find best path
        best_path = []
        best_last_state = np.argmax(viterbi_prob[:, T-1])
        best_prob = viterbi_prob[best_last_state][T-1]
        
        # Reconstruct path
        state_sequence = [0] * T
        state_sequence[T-1] = best_last_state
        
        for t in range(T-2, -1, -1):
            state_sequence[t] = viterbi_path[state_sequence[t+1]][t+1]
        
        # Convert indices back to state names
        best_path = [self.states[idx] for idx in state_sequence]
        
        return best_path, best_prob
    
    def forward_backward(self, observations: List[str]) -> float:
        """Calculate probability of observation sequence using forward algorithm"""
        T = len(observations)
        obs_indices = [self.obs_to_idx[obs] for obs in observations]
        
        # Forward algorithm
        forward_prob = np.zeros((self.n_states, T))
        
        # Initialize
        for s in range(self.n_states):
            forward_prob[s][0] = self.initial_prob[s] * self.emission_prob[s][obs_indices[0]]
        
        # Forward pass
        for t in range(1, T):
            for s in range(self.n_states):
                forward_prob[s][t] = (np.sum(forward_prob[:, t-1] * self.transition_prob[:, s]) *
                                    self.emission_prob[s][obs_indices[t]])
        
        # Total probability
        total_prob = np.sum(forward_prob[:, T-1])
        return total_prob
    
    def train_baum_welch(self, observation_sequences: List[List[str]], max_iterations: int = 100, tolerance: float = 1e-6):
        """Train HMM parameters using Baum-Welch algorithm (EM)"""
        for iteration in range(max_iterations):
            old_log_likelihood = self._compute_log_likelihood(observation_sequences)
            
            # E-step: Compute forward-backward probabilities
            gamma_sum = np.zeros((self.n_states,))
            xi_sum = np.zeros((self.n_states, self.n_states))
            gamma_obs_sum = np.zeros((self.n_states, self.n_observations))
            
            for obs_seq in observation_sequences:
                gamma, xi = self._forward_backward_gamma_xi(obs_seq)
                T = len(obs_seq)
                
                # Accumulate sufficient statistics
                gamma_sum += np.sum(gamma, axis=1)
                xi_sum += np.sum(xi, axis=2)
                
                for t in range(T):
                    obs_idx = self.obs_to_idx[obs_seq[t]]
                    gamma_obs_sum[:, obs_idx] += gamma[:, t]
            
            # M-step: Update parameters
            # Update initial probabilities
            self.initial_prob = gamma_sum / len(observation_sequences)
            
            # Update transition probabilities
            for i in range(self.n_states):
                if gamma_sum[i] > 0:
                    self.transition_prob[i, :] = xi_sum[i, :] / gamma_sum[i]
            
            # Update emission probabilities
            for i in range(self.n_states):
                if gamma_sum[i] > 0:
                    self.emission_prob[i, :] = gamma_obs_sum[i, :] / gamma_sum[i]
            
            # Check convergence
            new_log_likelihood = self._compute_log_likelihood(observation_sequences)
            if abs(new_log_likelihood - old_log_likelihood) < tolerance:
                break
    
    def _forward_backward_gamma_xi(self, observations: List[str]):
        """Compute gamma and xi for Baum-Welch"""
        T = len(observations)
        obs_indices = [self.obs_to_idx[obs] for obs in observations]
        
        # Forward pass
        alpha = np.zeros((self.n_states, T))
        for i in range(self.n_states):
            alpha[i][0] = self.initial_prob[i] * self.emission_prob[i][obs_indices[0]]
        
        for t in range(1, T):
            for j in range(self.n_states):
                alpha[j][t] = (np.sum(alpha[:, t-1] * self.transition_prob[:, j]) *
                             self.emission_prob[j][obs_indices[t]])
        
        # Backward pass
        beta = np.zeros((self.n_states, T))
        beta[:, T-1] = 1.0
        
        for t in range(T-2, -1, -1):
            for i in range(self.n_states):
                beta[i][t] = np.sum(self.transition_prob[i, :] * 
                                  self.emission_prob[:, obs_indices[t+1]] * beta[:, t+1])
        
        # Compute gamma
        gamma = alpha * beta
        gamma = gamma / np.sum(gamma, axis=0)
        
        # Compute xi
        xi = np.zeros((self.n_states, self.n_states, T-1))
        for t in range(T-1):
            denominator = np.sum(alpha[:, t] * beta[:, t])
            for i in range(self.n_states):
                for j in range(self.n_states):
                    xi[i][j][t] = (alpha[i][t] * self.transition_prob[i][j] * 
                                 self.emission_prob[j][obs_indices[t+1]] * beta[j][t+1]) / denominator
        
        return gamma, xi
    
    def _compute_log_likelihood(self, observation_sequences: List[List[str]]) -> float:
        """Compute total log likelihood of observation sequences"""
        total_log_likelihood = 0
        for obs_seq in observation_sequences:
            prob = self.forward_backward(obs_seq)
            if prob > 0:
                total_log_likelihood += np.log(prob)
        return total_log_likelihood

# Example usage - Weather prediction model
states = ["Sunny", "Rainy"]
observations = ["Walk", "Shop", "Clean"]

weather_hmm = HiddenMarkovModel(states, observations)

# Set model parameters
weather_hmm.set_initial_probabilities({"Sunny": 0.6, "Rainy": 0.4})

weather_hmm.set_transition_probabilities({
    "Sunny": {"Sunny": 0.7, "Rainy": 0.3},
    "Rainy": {"Sunny": 0.4, "Rainy": 0.6}
})

weather_hmm.set_emission_probabilities({
    "Sunny": {"Walk": 0.1, "Shop": 0.4, "Clean": 0.5},
    "Rainy": {"Walk": 0.6, "Shop": 0.3, "Clean": 0.1}
})

# Predict weather sequence from activities
activities = ["Walk", "Shop", "Clean", "Walk"]
weather_sequence, probability = weather_hmm.viterbi(activities)

print(f"Activities: {activities}")
print(f"Predicted weather: {weather_sequence}")
print(f"Probability: {probability:.6f}")

# Calculate probability of observation sequence
obs_probability = weather_hmm.forward_backward(activities)
print(f"Observation sequence probability: {obs_probability:.6f}")
```

**Time Complexity:** O(N²T) for Viterbi, O(N²T²M) for Baum-Welch training  
**Space Complexity:** O(N²) for model parameters + O(NT) for computation  
**Real-world use:** Speech recognition, gene finding, financial modeling, weather prediction

### 7.10 Neural Pattern Recognition (Simple Perceptron for Pattern Classification)

*Used in: Image recognition, text classification, anomaly detection*

```python
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple, Callable

class PatternPerceptron:
    def __init__(self, input_size: int, learning_rate: float = 0.01):
        self.weights = np.random.normal(0, 0.1, input_size)
        self.bias = np.random.normal(0, 0.1)
        self.learning_rate = learning_rate
        self.training_history = []
    
    def activation(self, x: float) -> int:
        """Step activation function"""
        return 1 if x >= 0 else 0
    
    def predict(self, inputs: np.ndarray) -> int:
        """Make prediction for single input"""
        linear_output = np.dot(inputs, self.weights) + self.bias
        return self.activation(linear_output)
    
    def train(self, training_data: List[Tuple[np.ndarray, int]], epochs: int = 100) -> List[float]:
        """Train perceptron using training data"""
        errors = []
        
        for epoch in range(epochs):
            total_error = 0
            for inputs, target in training_data:
                prediction = self.predict(inputs)
                error = target - prediction
                
                # Update weights and bias
                self.weights += self.learning_rate * error * inputs
                self.bias += self.learning_rate * error
                
                total_error += abs(error)
            
            errors.append(total_error)
            self.training_history.append((epoch, total_error))
            
            # Early stopping if no errors
            if total_error == 0:
                print(f"Converged at epoch {epoch}")
                break
        
        return errors
    
    def evaluate(self, test_data: List[Tuple[np.ndarray, int]]) -> Tuple[float, List[int], List[int]]:
        """Evaluate model on test data"""
        predictions = []
        actual = []
        correct = 0
        
        for inputs, target in test_data:
            prediction = self.predict(inputs)
            predictions.append(prediction)
            actual.append(target)
            
            if prediction == target:
                correct += 1
        
        accuracy = correct / len(test_data)
        return accuracy, predictions, actual

class SimpleNeuralNetwork:
    def __init__(self, input_size: int, hidden_size: int, output_size: int, learning_rate: float = 0.01):
        # Initialize weights randomly
        self.W1 = np.random.normal(0, 0.1, (input_size, hidden_size))
        self.b1 = np.zeros((1, hidden_size))
        self.W2 = np.random.normal(0, 0.1, (hidden_size, output_size))
        self.b2 = np.zeros((1, output_size))
        
        self.learning_rate = learning_rate
        self.training_history = []
    
    def sigmoid(self, x: np.ndarray) -> np.ndarray:
        """Sigmoid activation function"""
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))
    
    def sigmoid_derivative(self, x: np.ndarray) -> np.ndarray:
        """Derivative of sigmoid function"""
        return x * (1 - x)
    
    def forward(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Forward propagation"""
        z1 = np.dot(X, self.W1) + self.b1
        a1 = self.sigmoid(z1)
        z2 = np.dot(a1, self.W2) + self.b2
        a2 = self.sigmoid(z2)
        return a1, a2, z2
    
    def backward(self, X: np.ndarray, y: np.ndarray, a1: np.ndarray, a2: np.ndarray):
        """Backward propagation"""
        m = X.shape[0]
        
        # Output layer gradients
        dz2 = a2 - y
        dW2 = (1/m) * np.dot(a1.T, dz2)
        db2 = (1/m) * np.sum(dz2, axis=0, keepdims=True)
        
        # Hidden layer gradients
        dz1 = np.dot(dz2, self.W2.T) * self.sigmoid_derivative(a1)
        dW1 = (1/m) * np.dot(X.T, dz1)
        db1 = (1/m) * np.sum(dz1, axis=0, keepdims=True)
        
        # Update parameters
        self.W1 -= self.learning_rate * dW1
        self.b1 -= self.learning_rate * db1
        self.W2 -= self.learning_rate * dW2
        self.b2 -= self.learning_rate * db2
    
    def train(self, X: np.ndarray, y: np.ndarray, epochs: int = 1000) -> List[float]:
        """Train neural network"""
        costs = []
        
        for epoch in range(epochs):
            # Forward propagation
            a1, a2, z2 = self.forward(X)
            
            # Compute cost
            cost = np.mean((a2 - y) ** 2)
            costs.append(cost)
            
            # Backward propagation
            self.backward(X, y, a1, a2)
            
            if epoch % 100 == 0:
                print(f"Epoch {epoch}, Cost: {cost:.4f}")
        
        return costs
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        _, a2, _ = self.forward(X)
        return (a2 > 0.5).astype(int)

# Pattern recognition examples
class PatternRecognitionExamples:
    @staticmethod
    def create_xor_dataset() -> Tuple[np.ndarray, np.ndarray]:
        """Create XOR dataset for testing neural networks"""
        X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
        y = np.array([[0], [1], [1], [0]])
        return X, y
    
    @staticmethod
    def create_pattern_recognition_dataset(n_samples: int = 100) -> Tuple[List[Tuple[np.ndarray, int]], List[Tuple[np.ndarray, int]]]:
        """Create synthetic pattern recognition dataset"""
        # Pattern 1: Points in upper right quadrant
        pattern1_x = np.random.uniform(0.5, 1.0, n_samples // 2)
        pattern1_y = np.random.uniform(0.5, 1.0, n_samples // 2)
        pattern1_data = [(np.array([x, y]), 1) for x, y in zip(pattern1_x, pattern1_y)]
        
        # Pattern 0: Points in lower left quadrant
        pattern0_x = np.random.uniform(0.0, 0.5, n_samples // 2)
        pattern0_y = np.random.uniform(0.0, 0.5, n_samples // 2)
        pattern0_data = [(np.array([x, y]), 0) for x, y in zip(pattern0_x, pattern0_y)]
        
        # Combine and shuffle
        all_data = pattern1_data + pattern0_data
        np.random.shuffle(all_data)
        
        # Split into train and test
        split_idx = int(0.8 * len(all_data))
        return all_data[:split_idx], all_data[split_idx:]
    
    @staticmethod
    def create_image_pattern_dataset() -> Tuple[np.ndarray, np.ndarray]:
        """Create simple 3x3 image patterns (T and L shapes)"""
        # T pattern
        t_patterns = [
            np.array([1, 1, 1, 0, 1, 0, 0, 1, 0]).reshape(-1),  # T shape
            np.array([1, 1, 1, 0, 1, 0, 0, 1, 0]).reshape(-1) + np.random.normal(0, 0.1, 9),  # Noisy T
        ]
        
        # L pattern  
        l_patterns = [
            np.array([1, 0, 0, 1, 0, 0, 1, 1, 1]).reshape(-1),  # L shape
            np.array([1, 0, 0, 1, 0, 0, 1, 1, 1]).reshape(-1) + np.random.normal(0, 0.1, 9),  # Noisy L
        ]
        
        X = np.vstack([t_patterns, l_patterns])
        y = np.array([1, 1, 0, 0]).reshape(-1, 1)  # 1 for T, 0 for L
        
        return X, y

# Example usage - Pattern classification with Perceptron
print("=== Perceptron Pattern Recognition ===")
train_data, test_data = PatternRecognitionExamples.create_pattern_recognition_dataset(200)

# Train perceptron
perceptron = PatternPerceptron(input_size=2, learning_rate=0.1)
training_errors = perceptron.train(train_data, epochs=100)

# Evaluate
accuracy, predictions, actual = perceptron.evaluate(test_data)
print(f"Perceptron Accuracy: {accuracy:.2%}")

# Example usage - XOR problem with Neural Network
print("\n=== Neural Network XOR Pattern ===")
X_xor, y_xor = PatternRecognitionExamples.create_xor_dataset()

nn = SimpleNeuralNetwork(input_size=2, hidden_size=4, output_size=1, learning_rate=1.0)
costs = nn.train(X_xor, y_xor, epochs=1000)

predictions_nn = nn.predict(X_xor)
print("XOR Truth Table vs Predictions:")
for i in range(len(X_xor)):
    print(f"Input: {X_xor[i]} | Expected: {y_xor[i][0]} | Predicted: {predictions_nn[i][0]}")

# Example usage - Image pattern recognition
print("\n=== Image Pattern Recognition ===")
X_img, y_img = PatternRecognitionExamples.create_image_pattern_dataset()

img_nn = SimpleNeuralNetwork(input_size=9, hidden_size=6, output_size=1, learning_rate=0.5)
img_costs = img_nn.train(X_img, y_img, epochs=500)

img_predictions = img_nn.predict(X_img)
print("Image Pattern Classification:")
patterns = ['T', 'T (noisy)', 'L', 'L (noisy)']
for i in range(len(X_img)):
    print(f"Pattern: {patterns[i]} | Expected: {y_img[i][0]} | Predicted: {img_predictions[i][0]}")
```

**Time Complexity:** O(W*E*N) where W=weights, E=epochs, N=samples  
**Space Complexity:** O(W) for model parameters  
**Real-world use:** Image classification, text sentiment analysis, fraud detection

### 7.11 Advanced Graph Pattern Matching

*Used in: Social network analysis, protein structure analysis, circuit design*

```python
import networkx as nx
from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple, Optional

class GraphPatternMatcher:
    def __init__(self):
        self.cache = {}
    
    def subgraph_isomorphism(self, pattern_graph: Dict[int, List[int]], 
                           target_graph: Dict[int, List[int]]) -> List[Dict[int, int]]:
        """Find all isomorphic matches of pattern in target graph using backtracking"""
        pattern_nodes = list(pattern_graph.keys())
        target_nodes = list(target_graph.keys())
        
        if len(pattern_nodes) > len(target_nodes):
            return []
        
        matches = []
        
        def is_valid_mapping(mapping: Dict[int, int], pattern_node: int, target_node: int) -> bool:
            # Check degree constraint
            if len(pattern_graph[pattern_node]) > len(target_graph[target_node]):
                return False
            
            # Check neighbor constraints
            for pattern_neighbor in pattern_graph[pattern_node]:
                if pattern_neighbor in mapping:
                    target_neighbor = mapping[pattern_neighbor]
                    if target_neighbor not in target_graph[target_node]:
                        return False
            
            return True
        
        def backtrack(mapping: Dict[int, int], pattern_idx: int):
            if pattern_idx == len(pattern_nodes):
                matches.append(mapping.copy())
                return
            
            pattern_node = pattern_nodes[pattern_idx]
            
            for target_node in target_nodes:
                if target_node not in mapping.values():
                    if is_valid_mapping(mapping, pattern_node, target_node):
                        mapping[pattern_node] = target_node
                        backtrack(mapping, pattern_idx + 1)
                        del mapping[pattern_node]
        
        backtrack({}, 0)
        return matches
    
    def find_motifs(self, graph: Dict[int, List[int]], motif_size: int = 3) -> Dict[str, int]:
        """Find all network motifs of given size"""
        nodes = list(graph.keys())
        motif_counts = defaultdict(int)
        
        def get_motif_signature(subgraph_nodes: List[int]) -> str:
            """Create canonical signature for motif"""
            edges = []
            node_mapping = {node: i for i, node in enumerate(sorted(subgraph_nodes))}
            
            for node in subgraph_nodes:
                for neighbor in graph[node]:
                    if neighbor in subgraph_nodes and node < neighbor:
                        edges.append((node_mapping[node], node_mapping[neighbor]))
            
            return str(sorted(edges))
        
        # Generate all combinations of nodes
        from itertools import combinations
        for subgraph_nodes in combinations(nodes, motif_size):
            signature = get_motif_signature(list(subgraph_nodes))
            motif_counts[signature] += 1
        
        return dict(motif_counts)
    
    def find_cliques(self, graph: Dict[int, List[int]], min_size: int = 3) -> List[Set[int]]:
        """Find all maximal cliques using Bron-Kerbosch algorithm"""
        cliques = []
        
        def bron_kerbosch(R: Set[int], P: Set[int], X: Set[int]):
            if not P and not X:
                if len(R) >= min_size:
                    cliques.append(R.copy())
                return
            
            # Choose pivot vertex
            pivot = max(P.union(X), key=lambda v: len(set(graph[v]).intersection(P)), default=None)
            
            for v in P.difference(set(graph.get(pivot, []))):
                neighbors_v = set(graph.get(v, []))
                bron_kerbosch(
                    R.union({v}),
                    P.intersection(neighbors_v),
                    X.intersection(neighbors_v)
                )
                P.remove(v)
                X.add(v)
        
        all_nodes = set(graph.keys())
        bron_kerbosch(set(), all_nodes, set())
        return cliques
    
    def community_detection_louvain(self, graph: Dict[int, List[int]]) -> Dict[int, int]:
        """Simple community detection using modularity optimization"""
        # Initialize each node in its own community
        communities = {node: node for node in graph}
        total_edges = sum(len(neighbors) for neighbors in graph.values()) // 2
        
        def modularity(communities: Dict[int, int]) -> float:
            """Calculate modularity of current community assignment"""
            if total_edges == 0:
                return 0
            
            community_edges = defaultdict(int)
            community_degrees = defaultdict(int)
            
            for node, neighbors in graph.items():
                community = communities[node]
                community_degrees[community] += len(neighbors)
                
                for neighbor in neighbors:
                    if communities[neighbor] == community:
                        community_edges[community] += 1
            
            # Each edge counted twice in community_edges
            for community in community_edges:
                community_edges[community] //= 2
            
            Q = 0
            for community in set(communities.values()):
                e_ii = community_edges[community] / total_edges
                a_i = community_degrees[community] / (2 * total_edges)
                Q += e_ii - (a_i ** 2)
            
            return Q
        
        improved = True
        while improved:
            improved = False
            current_modularity = modularity(communities)
            
            for node in graph:
                original_community = communities[node]
                best_community = original_community
                best_modularity = current_modularity
                
                # Try moving node to each neighbor's community
                neighbor_communities = set()
                for neighbor in graph[node]:
                    neighbor_communities.add(communities[neighbor])
                
                for community in neighbor_communities:
                    if community != original_community:
                        communities[node] = community
                        new_modularity = modularity(communities)
                        
                        if new_modularity > best_modularity:
                            best_modularity = new_modularity
                            best_community = community
                
                communities[node] = best_community
                if best_community != original_community:
                    improved = True
        
        return communities

class AdvancedPatternMatching:
    def __init__(self):
        self.pattern_matcher = GraphPatternMatcher()
    
    def analyze_social_network(self, friendships: Dict[int, List[int]]) -> Dict[str, any]:
        """Comprehensive social network analysis"""
        results = {}
        
        # Find triangles (3-cliques)
        triangles = self.pattern_matcher.find_cliques(friendships, min_size=3)
        triangle_count = len([clique for clique in triangles if len(clique) == 3])
        results['triangles'] = triangle_count
        
        # Find network motifs
        motifs = self.pattern_matcher.find_motifs(friendships, motif_size=3)
        results['motifs'] = motifs
        
        # Community detection
        communities = self.pattern_matcher.community_detection_louvain(friendships)
        community_sizes = defaultdict(int)
        for community in communities.values():
            community_sizes[community] += 1
        results['communities'] = dict(community_sizes)
        
        # Central nodes (by degree)
        degrees = {node: len(neighbors) for node, neighbors in friendships.items()}
        results['most_connected'] = max(degrees, key=degrees.get)
        results['avg_degree'] = sum(degrees.values()) / len(degrees)
        
        return results
    
    def protein_structure_analysis(self, amino_acid_contacts: Dict[str, List[str]]) -> Dict[str, any]:
        """Analyze protein structure patterns"""
        results = {}
        
        # Convert to integer graph for pattern matching
        aa_to_int = {aa: i for i, aa in enumerate(amino_acid_contacts.keys())}
        int_graph = {aa_to_int[aa]: [aa_to_int[contact] for contact in contacts] 
                    for aa, contacts in amino_acid_contacts.items()}
        
        # Find structural motifs
        motifs = self.pattern_matcher.find_motifs(int_graph, motif_size=4)
        results['structural_motifs'] = len(motifs)
        
        # Find dense regions (cliques)
        cliques = self.pattern_matcher.find_cliques(int_graph, min_size=4)
        results['dense_regions'] = len(cliques)
        
        # Identify potential binding sites (high connectivity nodes)
        connectivity = {aa: len(contacts) for aa, contacts in amino_acid_contacts.items()}
        binding_sites = [aa for aa, conn in connectivity.items() if conn > np.mean(list(connectivity.values())) + 2 * np.std(list(connectivity.values()))]
        results['potential_binding_sites'] = binding_sites
        
        return results

# Example usage - Social Network Analysis
print("=== Social Network Pattern Analysis ===")

# Create sample social network
social_network = {
    0: [1, 2, 3],      # Alice
    1: [0, 2, 4],      # Bob  
    2: [0, 1, 3, 4],   # Charlie
    3: [0, 2, 5],      # David
    4: [1, 2, 6],      # Eve
    5: [3, 6, 7],      # Frank
    6: [4, 5, 7],      # Grace
    7: [5, 6]          # Henry
}

analyzer = AdvancedPatternMatching()
social_results = analyzer.analyze_social_network(social_network)

print("Social Network Analysis Results:")
for metric, value in social_results.items():
    print(f"  {metric}: {value}")

# Example usage - Graph Pattern Matching
print("\n=== Subgraph Isomorphism ===")

# Pattern: triangle
pattern = {0: [1, 2], 1: [0, 2], 2: [0, 1]}

# Target: larger graph
target = {
    0: [1, 2, 3], 1: [0, 2], 2: [0, 1, 4], 
    3: [0, 4], 4: [2, 3, 5], 5: [4]
}

gpm = GraphPatternMatcher()
matches = gpm.subgraph_isomorphism(pattern, target)
print(f"Found {len(matches)} triangle patterns in target graph:")
for i, match in enumerate(matches):
    print(f"  Match {i+1}: {match}")

# Example usage - Protein Structure Analysis  
print("\n=== Protein Structure Analysis ===")

# Sample protein contact map (simplified)
protein_contacts = {
    'A': ['B', 'C'],           # Amino acid A contacts B and C
    'B': ['A', 'C', 'D'],      # Amino acid B contacts A, C, D
    'C': ['A', 'B', 'E'],      # etc.
    'D': ['B', 'E', 'F'],
    'E': ['C', 'D', 'F'],
    'F': ['D', 'E']
}

protein_results = analyzer.protein_structure_analysis(protein_contacts)
print("Protein Structure Analysis Results:")
for metric, value in protein_results.items():
    print(f"  {metric}: {value}")

### 7.12 Streaming Pattern Recognition
*Used in: Real-time analytics, IoT sensor data, financial trading systems*

```python
import collections
import heapq
import time
from typing import Any, Callable, Generator, Optional

class StreamingPatternDetector:
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self.buffer = collections.deque(maxlen=window_size)
        self.pattern_callbacks = []
        self.statistics = {
            'count': 0,
            'sum': 0,
            'sum_squares': 0,
            'min': float('inf'),
            'max': float('-inf')
        }
    
    def add_pattern_detector(self, detector: Callable[[collections.deque], bool], 
                           callback: Callable[[Any], None], name: str = ""):
        """Add a pattern detection function with callback"""
        self.pattern_callbacks.append((detector, callback, name))
    
    def process_value(self, value: float, timestamp: float = None):
        """Process a single streaming value"""
        if timestamp is None:
            timestamp = time.time()
        
        # Add to buffer
        self.buffer.append((value, timestamp))
        
        # Update statistics
        self.statistics['count'] += 1
        self.statistics['sum'] += value
        self.statistics['sum_squares'] += value ** 2
        self.statistics['min'] = min(self.statistics['min'], value)
        self.statistics['max'] = max(self.statistics['max'], value)
        
        # Check all pattern detectors
        for detector, callback, name in self.pattern_callbacks:
            if len(self.buffer) >= 2:  # Need at least 2 points
                if detector(self.buffer):
                    callback({
                        'pattern': name,
                        'timestamp': timestamp,
                        'value': value,
                        'buffer_snapshot': list(self.buffer)[-10:]  # Last 10 values
                    })
    
    def get_statistics(self) -> dict:
        """Get current streaming statistics"""
        if self.statistics['count'] == 0:
            return self.statistics
        
        mean = self.statistics['sum'] / self.statistics['count']
        variance = (self.statistics['sum_squares'] / self.statistics['count']) - (mean ** 2)
        
        return {
            **self.statistics,
            'mean': mean,
            'variance': max(0, variance),  # Avoid negative due to floating point errors
            'std': max(0, variance) ** 0.5
        }

class AnomalyDetector:
    def __init__(self, threshold: float = 2.0, min_samples: int = 30):
        self.threshold = threshold
        self.min_samples = min_samples
        self.values = collections.deque(maxlen=1000)
        self.mean = 0
        self.variance = 0
    
    def update_statistics(self):
        """Update running mean and variance"""
        if len(self.values) < self.min_samples:
            return
        
        self.mean = sum(self.values) / len(self.values)
        self.variance = sum((x - self.mean) ** 2 for x in self.values) / len(self.values)
    
    def is_anomaly(self, value: float) -> bool:
        """Check if value is anomalous using z-score"""
        if len(self.values) < self.min_samples:
            self.values.append(value)
            return False
        
        z_score = abs(value - self.mean) / (self.variance ** 0.5 + 1e-10)
        is_anomalous = z_score > self.threshold
        
        self.values.append(value)
        self.update_statistics()
        
        return is_anomalous

class TrendDetector:
    def __init__(self, window_size: int = 10, min_trend_strength: float = 0.7):
        self.window_size = window_size
        self.min_trend_strength = min_trend_strength
    
    def detect_trend(self, buffer: collections.deque) -> Optional[str]:
        """Detect trend using linear regression on recent values"""
        if len(buffer) < self.window_size:
            return None
        
        recent_values = [item[0] for item in list(buffer)[-self.window_size:]]
        n = len(recent_values)
        
        # Simple linear regression
        x_values = list(range(n))
        x_mean = sum(x_values) / n
        y_mean = sum(recent_values) / n
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, recent_values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        if denominator == 0:
            return None
        
        slope = numerator / denominator
        
        # Calculate correlation coefficient
        y_variance = sum((y - y_mean) ** 2 for y in recent_values)
        if y_variance == 0:
            return None
        
        correlation = numerator / (denominator * y_variance) ** 0.5
        
        if abs(correlation) > self.min_trend_strength:
            return "uptrend" if slope > 0 else "downtrend"
        
        return "sideways"

class FrequencyPatternDetector:
    def __init__(self, pattern_length: int = 5):
        self.pattern_length = pattern_length
        self.pattern_counts = collections.defaultdict(int)
        self.total_patterns = 0
    
    def discretize_value(self, value: float, buffer: collections.deque) -> str:
        """Convert continuous value to discrete symbol based on recent history"""
        if len(buffer) < 10:
            return 'M'  # Medium
        
        recent_values = [item[0] for item in list(buffer)[-10:]]
        q1 = sorted(recent_values)[len(recent_values)//4]
        q3 = sorted(recent_values)[3*len(recent_values)//4]
        
        if value <= q1:
            return 'L'  # Low
        elif value >= q3:
            return 'H'  # High
        else:
            return 'M'  # Medium
    
    def detect_frequent_patterns(self, buffer: collections.deque) -> Optional[str]:
        """Detect frequently occurring patterns"""
        if len(buffer) < self.pattern_length:
            return None
        
        # Convert recent values to symbols
        symbols = []
        for i, (value, _) in enumerate(list(buffer)[-self.pattern_length:]):
            symbol = self.discretize_value(value, collections.deque(list(buffer)[:len(buffer)-self.pattern_length+i]))
            symbols.append(symbol)
        
        pattern = ''.join(symbols)
        self.pattern_counts[pattern] += 1
        self.total_patterns += 1
        
        # Check if this pattern is frequent (appears in >5% of windows)
        if self.pattern_counts[pattern] > self.total_patterns * 0.05:
            return pattern
        
        return None

# Example usage - Real-time streaming data analysis
print("=== Streaming Pattern Recognition ===")

# Create streaming detector
stream_detector = StreamingPatternDetector(window_size=50)

# Create specialized detectors
anomaly_detector = AnomalyDetector(threshold=2.5)
trend_detector = TrendDetector(window_size=10)
frequency_detector = FrequencyPatternDetector(pattern_length=5)

# Define pattern detection functions
def detect_anomaly(buffer):
    if len(buffer) > 0:
        current_value = buffer[-1][0]
        return anomaly_detector.is_anomaly(current_value)
    return False

def detect_trend_change(buffer):
    trend = trend_detector.detect_trend(buffer)
    return trend in ['uptrend', 'downtrend']

def detect_spike(buffer):
    if len(buffer) < 5:
        return False
    recent_values = [item[0] for item in list(buffer)[-5:]]
    current = recent_values[-1]
    previous_avg = sum(recent_values[:-1]) / len(recent_values[:-1])
    return current > previous_avg * 1.5  # Spike if 50% above recent average

def detect_frequent_pattern(buffer):
    pattern = frequency_detector.detect_frequent_patterns(buffer)
    return pattern is not None

# Add pattern detectors
stream_detector.add_pattern_detector(
    detect_anomaly, 
    lambda data: print(f"ANOMALY detected at {data['timestamp']:.2f}: value={data['value']:.2f}"),
    "Anomaly"
)

stream_detector.add_pattern_detector(
    detect_trend_change,
    lambda data: print(f"TREND CHANGE detected at {data['timestamp']:.2f}: value={data['value']:.2f}"),
    "Trend Change"
)

stream_detector.add_pattern_detector(
    detect_spike,
    lambda data: print(f"SPIKE detected at {data['timestamp']:.2f}: value={data['value']:.2f}"),
    "Spike"
)

stream_detector.add_pattern_detector(
    detect_frequent_pattern,
    lambda data: print(f"FREQUENT PATTERN detected at {data['timestamp']:.2f}"),
    "Frequent Pattern"
)

# Simulate streaming data (sensor readings, stock prices, etc.)
import random
import math

print("Processing simulated streaming data...")
base_value = 100
trend = 0
for i in range(200):
    # Simulate various patterns
    timestamp = time.time() + i * 0.1
    
    # Add trend
    trend += random.uniform(-0.1, 0.1)
    trend = max(-2, min(2, trend))  # Limit trend
    
    # Generate value with noise, trend, and occasional spikes/anomalies
    noise = random.gauss(0, 2)
    value = base_value + trend * i * 0.1 + noise
    
    # Add occasional spikes
    if random.random() < 0.05:  # 5% chance of spike
        value += random.uniform(10, 20)
    
    # Add occasional anomalies
    if random.random() < 0.02:  # 2% chance of anomaly
        value += random.uniform(-30, 30)
    
    # Process the value
    stream_detector.process_value(value, timestamp)
    
    # Print statistics every 50 values
    if i % 50 == 49:
        stats = stream_detector.get_statistics()
        print(f"\nStreaming Statistics (sample {i+1}):")
        print(f"  Mean: {stats.get('mean', 0):.2f}")
        print(f"  Std Dev: {stats.get('std', 0):.2f}")
        print(f"  Min: {stats['min']:.2f}, Max: {stats['max']:.2f}")

print(f"\nFinal statistics: {stream_detector.get_statistics()}")
```

**Time Complexity:** O(1) amortized per streaming element  
**Space Complexity:** O(W) where W is window size  
**Real-world use:** IoT sensor monitoring, financial market analysis, network traffic analysis

## Summary of Advanced Real-World Pattern Recognition Algorithms

| Algorithm | Time Complexity | Space Complexity | Primary Use Cases |
|-----------|----------------|------------------|------------------|
| Aho-Corasick | O(n + m + z) | O(m) | Antivirus, intrusion detection, text search |
| Suffix Array + LCP | O(n log n) build, O(log n + k) search | O(n) | Bioinformatics, full-text search, data compression |
| Rolling Hash | O(n) | O(1) | Content deduplication, distributed systems |
| Bloom Filter | O(k) per operation | O(m) | Database optimization, web crawling, caching |
| Radix Tree | O(k) | O(ALPHABET_SIZE *N* M) | IP routing, autocomplete, file systems |
| 2D Geometric | O(n*m) | O(m) | Computer vision, robotics, medical imaging |
| DTW (Time Series) | O(n*m) | O(n*m) | Speech recognition, financial analysis, bioinformatics |
| Edit Distance Variants | O(n*m) | O(n*m) | Spell checking, DNA alignment, fuzzy search |
| HMM | O(N²T) Viterbi, O(N²T²M) training | O(N²) + O(NT) | Speech recognition, gene finding, NLP |
| Neural Networks | O(W*E*N) | O(W) | Image classification, pattern recognition, AI |
| Graph Isomorphism | O(n!) worst case | O(n²) | Social networks, protein analysis, circuit design |
| Streaming Patterns | O(1) amortized | O(W) | Real-time analytics, IoT, trading systems |

These advanced algorithms represent the state-of-the-art in pattern recognition and are actively used in production systems across various industries. They handle complex real-world scenarios including noise, scale, real-time constraints, and multi-dimensional data patterns.
