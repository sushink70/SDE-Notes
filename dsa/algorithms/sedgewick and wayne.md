# The Complete Sedgewick & Wayne "Algorithms" Mastery Guide
## A Monk's Path to Top 1% Algorithmic Excellence

```
┌─────────────────────────────────────────────────────────────┐
│  "An algorithm must be seen to be believed." — Donald Knuth │
│                                                               │
│  Your Journey: Fundamentals → Mastery → Top 1% Excellence   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📚 **Overview: What Makes This Book Essential**

Sedgewick & Wayne's "Algorithms" is the **definitive modern algorithms text** used at Princeton and worldwide. It covers:

- **Fundamental data structures** (bags, stacks, queues, priority queues, symbol tables)
- **Sorting algorithms** (elementary sorts, mergesort, quicksort, heapsort)
- **Searching** (binary search trees, balanced trees, hash tables)
- **Graphs** (undirected/directed graphs, MSTs, shortest paths)
- **Strings** (sorts, tries, substring search, compression, regex)
- **Advanced topics** (context, reductions, intractability)

**Why this approach matters for top 1%:**
- Emphasis on **scientific method**: hypothesis, experiment, analyze
- **Real-world performance analysis**, not just Big-O theory
- **API-first design** thinking
- Focus on **practical implementations** that work in production

---

## 🧭 **Learning Strategy: The Monk's Approach**

```
┌──────────────────────────────────────────────────────────────┐
│                    LEARNING ARCHITECTURE                      │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  1. UNDERSTAND THE PROBLEM                                   │
│     ↓                                                         │
│  2. ANALYZE THE ABSTRACT DATA TYPE (API)                     │
│     ↓                                                         │
│  3. STUDY NAIVE IMPLEMENTATION                               │
│     ↓                                                         │
│  4. IDENTIFY PERFORMANCE BOTTLENECKS                         │
│     ↓                                                         │
│  5. LEARN OPTIMIZED SOLUTIONS                                │
│     ↓                                                         │
│  6. IMPLEMENT IN MULTIPLE LANGUAGES                          │
│     ↓                                                         │
│  7. ANALYZE PERFORMANCE EMPIRICALLY                          │
│     ↓                                                         │
│  8. SOLVE RELATED PROBLEMS                                   │
│     ↓                                                         │
│  9. TEACH/EXPLAIN TO SOLIDIFY                                │
└──────────────────────────────────────────────────────────────┘
```

**Mental Model: Chunking**
- Break each topic into digestible "chunks" (e.g., "insertion sort" is one chunk)
- Master one chunk completely before moving forward
- Link chunks together (e.g., "merge" operation links to mergesort, external sorting, etc.)

---

## 📖 **PART I: FUNDAMENTALS**

### **Chapter 1.1: Basic Programming Model**

**Core Concepts:**
- **Primitive data types**: integers, floats, booleans, characters
- **Control flow**: conditionals, loops, recursion
- **Arrays**: fixed-size collections
- **Static methods**: encapsulated reusable procedures

**Key Insight for Top 1%:**
Everything in algorithms builds on **three fundamental operations**:
1. **Sequence** (do A, then B)
2. **Selection** (if-else)
3. **Iteration** (loops, recursion)

These are your **atomic building blocks**.

---

### **Chapter 1.2: Data Abstraction**

**What is an Abstract Data Type (ADT)?**
An ADT defines:
1. **What** operations are supported (API)
2. **Not how** they're implemented (implementation details hidden)

**Example: Counter ADT**
```
API:
- Counter(String name)  // constructor
- void increment()       // add 1 to count
- int tally()           // return current count
- String toString()     // string representation
```

**Why ADTs Matter:**
- **Separation of concerns**: client code doesn't depend on implementation
- **Flexibility**: can swap implementations without changing client code
- **Reusability**: same interface, multiple contexts

```
┌─────────────────────────────────────────────────┐
│            ADT THINKING PATTERN                 │
├─────────────────────────────────────────────────┤
│                                                 │
│  Problem → What operations do I need? → API    │
│     ↓                                           │
│  How to implement efficiently? → Data Structure│
│     ↓                                           │
│  How does it perform? → Analysis               │
└─────────────────────────────────────────────────┘
```

**Cognitive Principle: Abstraction**
Your brain can only hold ~7 items in working memory. ADTs let you think at higher levels without drowning in details.

---

### **Chapter 1.3: Bags, Queues, and Stacks**

These are **fundamental collection types** you'll use everywhere.

#### **1.3.1: Bag (Unordered Collection)**

**What is it?**
A collection where:
- Order doesn't matter
- Duplicates allowed
- Can add items
- Can iterate through items (in arbitrary order)
- Cannot remove specific items

**API:**
```
Bag<Item>
- Bag()              // create empty bag
- void add(Item item)// add an item
- boolean isEmpty()  // is bag empty?
- int size()        // number of items
- Iterator<Item> iterator() // iterate over items
```

**Use Case:**
Reading marks from a file to compute statistics (order irrelevant).

---

#### **1.3.2: Queue (FIFO - First In First Out)**

**What is FIFO?**
Imagine a line at a coffee shop:
- First person to join → first person served
- New people join at the **back** (enqueue)
- People leave from the **front** (dequeue)

```
ASCII Visualization:
    enqueue →  [5][4][3][2][1] → dequeue
                back       front
                
    Add 6:     [6][5][4][3][2][1]
    Remove:    [6][5][4][3][2]  (1 removed)
```

**API:**
```
Queue<Item>
- Queue()              // create empty queue
- void enqueue(Item)   // add to back
- Item dequeue()       // remove from front
- boolean isEmpty()
- int size()
```

**Implementation Strategies:**

**1. Array-based (Resizing Array):**
```
Concept: Use array with two pointers (head, tail)
Problem: Array can "drift" right, wasting space at left

Solution: Circular array (wrap around using modulo)

[_][_][3][2][1][_]
      ↑       ↑
     tail   head
     
After dequeue(1):
[_][_][3][2][_][_]
      ↑     ↑
     tail  head
     
After enqueue(4):
[_][_][3][2][_][4]
      ↑         ↑
     tail      head (wrapped)
```

**2. Linked List:**
```
Each node points to next:
[1|→] → [2|→] → [3|→] → null
 ↑                ↑
head            tail

Enqueue: Add at tail
Dequeue: Remove at head
```

**Performance Analysis:**
```
┌─────────────────┬─────────────┬──────────────┬──────────┐
│ Operation       │ Resizing    │ Linked List  │ Winner   │
│                 │ Array       │              │          │
├─────────────────┼─────────────┼──────────────┼──────────┤
│ enqueue         │ O(1)*       │ O(1)         │ Tie      │
│ dequeue         │ O(1)*       │ O(1)         │ Tie      │
│ Space overhead  │ ~25-50%     │ ~64 bytes/   │ Array    │
│                 │             │  item        │          │
│ Cache locality  │ Excellent   │ Poor         │ Array    │
└─────────────────┴─────────────┴──────────────┴──────────┘

* amortized (occasionally O(n) during resize)
```

**Mental Model: Choose based on constraints**
- Need minimal space overhead? → Resizing array
- Need guaranteed O(1) per operation? → Linked list
- Real-world recommendation: Resizing array (cache-friendly)

---

#### **1.3.3: Stack (LIFO - Last In First Out)**

**What is LIFO?**
Like a stack of plates:
- Last plate placed on top → first plate removed
- Add to **top** (push)
- Remove from **top** (pop)

```
ASCII Visualization:
    push      [5] ← top        pop
     ↓        [4]               ↑
             [3]
             [2]
             [1]

Push 6:      [6] ← top
             [5]
             [4]
             ...
             
Pop:         [5] ← top  (6 removed)
             [4]
             ...
```

**API:**
```
Stack<Item>
- Stack()              // create empty stack
- void push(Item)      // add to top
- Item pop()           // remove from top
- Item peek()          // look at top without removing
- boolean isEmpty()
- int size()
```

**Classic Stack Applications:**

**1. Expression Evaluation (Dijkstra's Two-Stack Algorithm)**

Problem: Evaluate `(1 + ((2 + 3) * (4 * 5)))`

```
Algorithm Flow:
┌────────────────────────────────────────────────┐
│ Use TWO stacks: one for values, one for ops   │
├────────────────────────────────────────────────┤
│                                                │
│ 1. Scan left to right                         │
│ 2. If '(': ignore                             │
│ 3. If number: push to value stack             │
│ 4. If operator: push to operator stack        │
│ 5. If ')': pop operator, pop 2 values,        │
│            apply operator, push result        │
└────────────────────────────────────────────────┘

Example:
Input: (1 + 2)

Values: []
Ops: []

See '(': ignore
Values: []
Ops: []

See '1': push value
Values: [1]
Ops: []

See '+': push op
Values: [1]
Ops: [+]

See '2': push value
Values: [1, 2]
Ops: [+]

See ')': pop op '+', pop values 2,1, compute 1+2=3, push 3
Values: [3]
Ops: []

Result: 3
```

**2. Balanced Parentheses Checking**

```
Input: "{[()]}"  → Valid
Input: "{[(])}"  → Invalid

Algorithm:
- Push opening brackets onto stack
- When closing bracket found:
  - Pop stack
  - Check if it matches
  - If stack empty or mismatch → invalid

┌──────────────────────────────────────────┐
│        DECISION TREE                     │
├──────────────────────────────────────────┤
│                                          │
│     See character                        │
│          │                               │
│    ┌─────┴─────┐                        │
│    │           │                        │
│ Opening?   Closing?                     │
│    │           │                        │
│  Push      ┌───┴───┐                   │
│            │       │                   │
│         Stack    Stack                 │
│         empty?   match?                │
│            │       │                   │
│          FAIL    ┌─┴─┐                │
│                  │   │                │
│                PASS POP                │
│                     continue           │
└──────────────────────────────────────────┘
```

**Implementation Comparison:**

```rust
// Rust: Using Vec (stack is just push/pop on vector)
let mut stack: Vec<i32> = Vec::new();
stack.push(5);
stack.push(10);
let top = stack.pop(); // Some(10)
```

```python
# Python: List as stack
stack = []
stack.append(5)
stack.append(10)
top = stack.pop()  # 10
```

```c
// C: Manual array-based stack
typedef struct {
    int items[100];
    int top;
} Stack;

void push(Stack* s, int val) {
    s->items[++s->top] = val;
}

int pop(Stack* s) {
    return s->items[s->top--];
}
```

```cpp
// C++: std::stack
#include <stack>
std::stack<int> s;
s.push(5);
s.push(10);
int top = s.top(); // 10
s.pop();
```

```go
// Go: Slice as stack
stack := make([]int, 0)
stack = append(stack, 5)
stack = append(stack, 10)
top := stack[len(stack)-1]
stack = stack[:len(stack)-1]
```

---

### **Chapter 1.4: Analysis of Algorithms**

**The Central Question:**
*"Will my program be able to solve a large practical input?"*

Not just "does it work?" but "does it work **fast enough** on **real data**?"

#### **1.4.1: The Scientific Method**

```
┌────────────────────────────────────────────────┐
│      PERFORMANCE ANALYSIS FRAMEWORK            │
├────────────────────────────────────────────────┤
│                                                │
│  1. OBSERVE: Run experiments, measure time    │
│      ↓                                         │
│  2. HYPOTHESIZE: Form a model (e.g., ~N²)     │
│      ↓                                         │
│  3. PREDICT: What happens if N doubles?       │
│      ↓                                         │
│  4. VERIFY: Run larger experiments            │
│      ↓                                         │
│  5. VALIDATE: Does reality match theory?      │
└────────────────────────────────────────────────┘
```

**Example: 3-Sum Problem**

*Problem:* Given N integers, count how many triples sum to 0.

**Brute Force Approach:**
```
for i in 0..N:
    for j in i+1..N:
        for k in j+1..N:
            if arr[i] + arr[j] + arr[k] == 0:
                count++
```

**Analysis:**
- Three nested loops
- Inner loop executes ~N³ times
- Expected: O(N³) complexity

**Empirical Validation:**
```
N      Time (seconds)    Ratio
─────────────────────────────────
1000   0.1               -
2000   0.8               8.0
4000   6.4               8.0
8000   51.2              8.0

Ratio ≈ 8 = 2³
Conclusion: Confirmed cubic (N³) growth
```

**Key Insight:**
Doubling N multiplies time by 2^b where b is exponent in complexity.
- If O(N): ratio = 2
- If O(N log N): ratio ≈ 2 (slightly more)
- If O(N²): ratio = 4
- If O(N³): ratio = 8

---

#### **1.4.2: Order-of-Growth Classifications**

**What is "Order of Growth"?**
How running time **scales** as input size N increases.

```
Common Complexity Classes (Best to Worst):
┌──────────────┬─────────────┬──────────────────────┐
│ Complexity   │ Name        │ N=1000 → N=2000     │
├──────────────┼─────────────┼──────────────────────┤
│ O(1)         │ Constant    │ Same time            │
│ O(log N)     │ Logarithmic │ +1 operation         │
│ O(N)         │ Linear      │ 2x time              │
│ O(N log N)   │ Linearith.  │ ~2x time             │
│ O(N²)        │ Quadratic   │ 4x time              │
│ O(N³)        │ Cubic       │ 8x time              │
│ O(2^N)       │ Exponential │ Infeasible!          │
└──────────────┴─────────────┴──────────────────────┘
```

**Visualization:**
```
Time
 │
 │                                          ╱ O(2^N)
 │                                      ╱╱╱
 │                               ╱╱╱╱╱╱
 │                        ╱╱╱╱╱╱╱  O(N³)
 │                 ╱╱╱╱╱╱╱
 │          ╱╱╱╱╱╱╱  O(N²)
 │     ╱─────────  O(N log N)
 │  ╱────────── O(N)
 │ ────────── O(log N)
 │──────────── O(1)
 └─────────────────────────────────────────→ N
```

**Practical Guidelines:**

```
┌────────────────────────────────────────────────┐
│  MAXIMUM PROBLEM SIZE FOR 1 SECOND EXECUTION  │
├──────────────┬─────────────────────────────────┤
│ O(log N)     │ Any practical N                 │
│ O(N)         │ ~10^9                           │
│ O(N log N)   │ ~10^7-10^8                      │
│ O(N²)        │ ~10^4                           │
│ O(N³)        │ ~500                            │
│ O(2^N)       │ ~20-25                          │
└──────────────┴─────────────────────────────────┘
```

**Mental Model: Scalability Threshold**
Ask yourself: "If N doubles, can I still solve it in reasonable time?"
- O(N²): Maybe for N=10,000, but not N=1,000,000
- O(N log N): Yes, even for N=10^8

---

#### **1.4.3: Memory Usage**

**Typical Object Overhead (Java/C++/Python):**

```
┌─────────────────────┬──────────┬────────────┐
│ Type                │ Bytes    │ Notes      │
├─────────────────────┼──────────┼────────────┤
│ boolean             │ 1        │            │
│ byte                │ 1        │            │
│ char                │ 2        │            │
│ int                 │ 4        │            │
│ float               │ 4        │            │
│ long                │ 8        │            │
│ double              │ 8        │            │
│ Reference           │ 8        │ 64-bit sys │
│ Array overhead      │ 24       │ + padding  │
│ Object overhead     │ 16       │            │
│ Padding             │ 0-7      │ Multiple 8 │
└─────────────────────┴──────────┴────────────┘
```

**Example: Linked List Node**
```java
class Node {
    int val;      // 4 bytes
    Node next;    // 8 bytes (reference)
    // Object overhead: 16 bytes
    // Total: 16 + 4 + 8 = 28 → padded to 32 bytes
}
```

**Memory vs Speed Tradeoff:**
- Array: Dense (cache-friendly), but fixed size
- Linked List: Flexible size, but pointer overhead

---

### **Chapter 1.5: Union-Find (Disjoint Set Union)**

**The Problem:**
*"Given a set of objects, support two operations:"*
1. **Union**: Connect two objects
2. **Find**: Are two objects connected?

**Real-World Applications:**
- Network connectivity (computers, social networks)
- Image processing (connected components)
- Kruskal's MST algorithm (coming later!)

**Example:**
```
Initial: {0} {1} {2} {3} {4} {5}  (all separate)

union(0, 1): {0,1} {2} {3} {4} {5}
union(2, 3): {0,1} {2,3} {4} {5}
union(1, 3): {0,1,2,3} {4} {5}

connected(0, 3)? → YES (same component)
connected(0, 4)? → NO (different components)
```

**API:**
```
UnionFind
- UF(int N)              // initialize N sites
- void union(int p, int q) // connect p and q
- boolean connected(int p, int q) // are p,q connected?
- int find(int p)         // component identifier for p
- int count()             // number of components
```

---

#### **Evolution of Solutions:**

**Approach 1: Quick-Find (Eager)**

**Idea:** 
Each element stores its component ID directly.

```
Array representation:
Index:  0  1  2  3  4  5
Value: [1][1][3][3][4][5]
        ↑       ↑
     Component 1  Component 3
```

**Operations:**
- **find(p)**: Just return `id[p]` → O(1)
- **union(p, q)**: Change all elements with `id[p]` to `id[q]` → O(N)

**Problem:** Union is too slow! For N unions: O(N²) total

---

**Approach 2: Quick-Union (Lazy)**

**Idea:** 
Each element points to a parent. Root is component ID.

```
Tree representation:
    1           3
   / \         / \
  0   2       4   5

Array (parent pointers):
Index:  0  1  2  3  4  5
Parent:[1][1][1][3][3][3]
```

**Operations:**
- **find(p)**: Follow parent pointers to root
  ```
  while (p != parent[p]):
      p = parent[p]
  return p
  ```
- **union(p, q)**: Set root of p to point to root of q

**Performance:** 
- Best case: O(1) per operation
- Worst case: O(N) if tree becomes tall (linear chain)

---

**Approach 3: Weighted Quick-Union**

**Key Insight:** 
Avoid tall trees by always attaching smaller tree under larger tree.

```
Before union(small_tree, large_tree):
  
  Small:     Large:
    3          1
    |         /|\
    4        0 2 5
    |            |
    6            7

After union (attach small under large):
        1
       /|\
      0 2 5   3
          |   |
          7   4
              |
              6
```

**Track tree sizes:**
```
Index:  0  1  2  3  4  5  6  7
Parent:[1][1][1][1][3][1][4][5]
Size:  [1][5][1][3][1][1][1][1]  (only meaningful at roots)
```

**Performance:** 
- find: O(log N) worst case (tree depth ≤ log N)
- union: O(log N) worst case

**Why log N depth?**
When you union two trees, the depth increases only when equal-sized trees merge. Each merge doubles size, so depth = log₂(size).

---

**Approach 4: Path Compression (Ultimate Optimization)**

**Key Insight:** 
After finding root, make every node point directly to root.

```
Before find(6):
    1
   / \
  2   3
     /
    4
   /
  5
 /
6

After find(6) with path compression:
      1
    / | \  \
   2  3  4  5  6  (all point directly to root!)
```

**Implementation:**
```rust
fn find(&mut self, mut p: usize) -> usize {
    let root = {
        let mut current = p;
        while current != self.parent[current] {
            current = self.parent[current];
        }
        current
    };
    
    // Path compression: make p point directly to root
    while p != root {
        let next = self.parent[p];
        self.parent[p] = root;
        p = next;
    }
    
    root
}
```

**Performance with Path Compression + Weighting:**
- Amortized: O(α(N)) per operation
  - α(N) = inverse Ackermann function
  - For all practical N: α(N) ≤ 5
  - **Essentially constant time!**

---

**Performance Summary:**
```
┌──────────────────────┬──────────┬──────────┐
│ Algorithm            │ union    │ find     │
├──────────────────────┼──────────┼──────────┤
│ Quick-Find           │ O(N)     │ O(1)     │
│ Quick-Union          │ O(N)*    │ O(N)*    │
│ Weighted QU          │ O(log N) │ O(log N) │
│ Weighted + Path Comp │ O(α(N))  │ O(α(N))  │
└──────────────────────┴──────────┴──────────┘
* worst case
```

**Mental Model: Optimization Pattern**
1. Start with simple solution
2. Identify bottleneck
3. Add invariant to prevent worst case (weighting)
4. Add online optimization (path compression)

This pattern repeats throughout algorithms!

---

## **Cognitive Break: Deliberate Practice Framework**

Before continuing, let's discuss **how to practice** these concepts:

```
┌──────────────────────────────────────────────────┐
│           DELIBERATE PRACTICE CYCLE              │
├──────────────────────────────────────────────────┤
│                                                  │
│  1. FOCUS: Pick ONE concept (e.g., Quick-Union) │
│      ↓                                           │
│  2. IMPLEMENT: Code it without looking          │
│      ↓                                           │
│  3. TEST: Run on examples, edge cases           │
│      ↓                                           │
│  4. ANALYZE: What was hard? What did I miss?    │
│      ↓                                           │
│  5. REFINE: Fix mistakes, optimize              │
│      ↓                                           │
│  6. TEACH: Explain it to rubber duck            │
│      ↓                                           │
│  7. APPLY: Solve related LeetCode problem       │
│      ↓                                           │
│  8. REFLECT: What patterns emerged?             │
└──────────────────────────────────────────────────┘
```

**Spaced Repetition:**
- Day 1: Learn Union-Find
- Day 3: Implement from memory
- Day 7: Solve 3 problems using it
- Day 14: Teach it to someone
- Day 30: Review and solve harder variant

---

## 📖 **PART II: SORTING**

Sorting is **fundamental** because:
1. Many problems become easier with sorted data
2. Teaches algorithm design principles
3. Performance analysis matters (N² vs N log N is huge!)

### **Chapter 2.1: Elementary Sorts**

#### **2.1.1: Selection Sort**

**The Idea:**
Find the minimum element, swap it to the front. Repeat for remaining elements.

```
Visualization:
Initial: [5, 2, 8, 1, 9]
         
Step 1: Find min (1), swap with first
        [1 | 2, 8, 5, 9]
         ↑ sorted

Step 2: Find min in [2,8,5,9] → 2, already in place
        [1, 2 | 8, 5, 9]
            ↑ sorted

Step 3: Find min in [8,5,9] → 5, swap with 8
        [1, 2, 5 | 8, 9]
               ↑ sorted

Step 4: Find min in [8,9] → 8, already in place
        [1, 2, 5, 8 | 9]
                  ↑ sorted

Done!
```

**Algorithm Flow:**
```
┌────────────────────────────────────────┐
│  for i = 0 to N-1:                    │
│      min_idx = i                       │
│      for j = i+1 to N:                 │
│          if arr[j] < arr[min_idx]:     │
│              min_idx = j               │
│      swap(arr[i], arr[min_idx])        │
└────────────────────────────────────────┘
```

**Implementation (Rust):**
```rust
fn selection_sort<T: Ord>(arr: &mut [T]) {
    let n = arr.len();
    for i in 0..n {
        let mut min_idx = i;
        for j in (i + 1)..n {
            if arr[j] < arr[min_idx] {
                min_idx = j;
            }
        }
        arr.swap(i, min_idx);
    }
}
```

**Performance Analysis:**
- **Comparisons:** (N-1) + (N-2) + ... + 1 = N(N-1)/2 ≈ N²/2
- **Swaps:** Exactly N-1 (one per outer loop)
- **Time Complexity:** O(N²) - quadratic
- **Space Complexity:** O(1) - in-place
- **Stable?** No (can swap equal elements out of order)

**Characteristics:**
- ✅ Simple to understand
- ✅ Minimal swaps (good if swaps are expensive)
- ✅ Works well on small arrays
- ❌ Quadratic time (slow for large N)
- ❌ Doesn't adapt to partially sorted data

---

#### **2.1.2: Insertion Sort**

**The Idea:**
Like sorting cards in your hand. Take each element, insert it into correct position among previously sorted elements.

```
Visualization:
Initial: [5, 2, 8, 1, 9]

Step 1: [5] already sorted
        [5 | 2, 8, 1, 9]

Step 2: Insert 2 into sorted part
        [2, 5 | 8, 1, 9]

Step 3: Insert 8 (already in place)
        [2, 5, 8 | 1, 9]

Step 4: Insert 1
        [1, 2, 5, 8 | 9]

Step 5: Insert 9 (already in place)
        [1, 2, 5, 8, 9]
```

**Algorithm Flow:**
```
┌────────────────────────────────────────┐
│  for i = 1 to N-1:                    │
│      key = arr[i]                      │
│      j = i - 1                         │
│      while j >= 0 and arr[j] > key:    │
│          arr[j+1] = arr[j]             │
│          j--                           │
│      arr[j+1] = key                    │
└────────────────────────────────────────┘
```

