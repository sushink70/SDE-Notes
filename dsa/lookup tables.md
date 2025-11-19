I'll provide a comprehensive guide on performance characteristics lookup tables - essential references for understanding algorithmic complexity, data structure operations, and system performance trade-offs.

## What are Performance Characteristics Lookup Tables?

Performance characteristics lookup tables are systematic references that document the time and space complexity of algorithms and data structures. They enable quick comparison and informed decision-making during software design and optimization.

## Core Components

### **1. Complexity Notation**

**Time Complexity Classes (Best to Worst):**
- **O(1)** - Constant: Hash table lookup, array access by index
- **O(log n)** - Logarithmic: Binary search, balanced tree operations
- **O(n)** - Linear: Linear search, array traversal
- **O(n log n)** - Linearithmic: Efficient sorting (merge sort, heap sort)
- **O(n²)** - Quadratic: Nested loops, bubble sort, selection sort
- **O(n³)** - Cubic: Triple nested loops, naive matrix multiplication
- **O(2ⁿ)** - Exponential: Recursive fibonacci, subsets generation
- **O(n!)** - Factorial: Permutations, traveling salesman (brute force)

**Space Complexity:**
- **In-place** - O(1) extra space
- **Linear** - O(n) extra space
- **Exponential** - O(2ⁿ) space (recursion depth, memoization)

### **2. Data Structure Operations Table**

**Array/List:**
- Access by index: O(1)
- Search (unsorted): O(n)
- Search (sorted): O(log n) with binary search
- Insert at end (dynamic array): O(1) amortized
- Insert at beginning/middle: O(n)
- Delete at end: O(1)
- Delete at beginning/middle: O(n)
- Space: O(n)

**Linked List:**
- Access by index: O(n)
- Search: O(n)
- Insert at head: O(1)
- Insert at tail (with tail pointer): O(1)
- Insert at middle: O(n) to find position, O(1) to insert
- Delete at head: O(1)
- Delete at tail: O(n) for singly-linked, O(1) for doubly-linked with tail
- Delete at middle: O(n)
- Space: O(n)

**Hash Table/Dictionary:**
- Search: O(1) average, O(n) worst case
- Insert: O(1) average, O(n) worst case
- Delete: O(1) average, O(n) worst case
- Space: O(n)
- Notes: Performance depends on hash function quality and load factor

**Binary Search Tree (Balanced):**
- Search: O(log n)
- Insert: O(log n)
- Delete: O(log n)
- Min/Max: O(log n)
- Space: O(n)
- Unbalanced worst case: O(n) for all operations

**Heap (Binary):**
- Find min/max: O(1)
- Insert: O(log n)
- Delete min/max: O(log n)
- Build heap: O(n)
- Space: O(n)

**Stack:**
- Push: O(1)
- Pop: O(1)
- Peek: O(1)
- Search: O(n)
- Space: O(n)

**Queue:**
- Enqueue: O(1)
- Dequeue: O(1)
- Peek: O(1)
- Search: O(n)
- Space: O(n)

**Graph (Adjacency List):**
- Add vertex: O(1)
- Add edge: O(1)
- Remove vertex: O(V + E)
- Remove edge: O(E)
- Query edge exists: O(V)
- Space: O(V + E)

**Graph (Adjacency Matrix):**
- Add vertex: O(V²)
- Add edge: O(1)
- Remove vertex: O(V²)
- Remove edge: O(1)
- Query edge exists: O(1)
- Space: O(V²)

**Trie:**
- Search: O(m) where m is key length
- Insert: O(m)
- Delete: O(m)
- Space: O(ALPHABET_SIZE × m × n) worst case

### **3. Sorting Algorithms Table**

**Comparison-Based Sorts:**

**Bubble Sort:**
- Best: O(n) - already sorted
- Average: O(n²)
- Worst: O(n²)
- Space: O(1)
- Stable: Yes
- Use case: Educational purposes, nearly sorted tiny datasets

**Selection Sort:**
- Best: O(n²)
- Average: O(n²)
- Worst: O(n²)
- Space: O(1)
- Stable: No (standard implementation)
- Use case: Minimizing writes, small datasets

**Insertion Sort:**
- Best: O(n)
- Average: O(n²)
- Worst: O(n²)
- Space: O(1)
- Stable: Yes
- Use case: Nearly sorted data, small datasets, online sorting

**Merge Sort:**
- Best: O(n log n)
- Average: O(n log n)
- Worst: O(n log n)
- Space: O(n)
- Stable: Yes
- Use case: Guaranteed performance, external sorting, stable sort needed

**Quick Sort:**
- Best: O(n log n)
- Average: O(n log n)
- Worst: O(n²) - poor pivot selection
- Space: O(log n) for recursion stack
- Stable: No (standard implementation)
- Use case: General purpose, in-place sorting, average case performance

**Heap Sort:**
- Best: O(n log n)
- Average: O(n log n)
- Worst: O(n log n)
- Space: O(1)
- Stable: No
- Use case: Guaranteed performance with minimal space

**Tim Sort (Python/Java default):**
- Best: O(n)
- Average: O(n log n)
- Worst: O(n log n)
- Space: O(n)
- Stable: Yes
- Use case: Real-world data with partial ordering

**Non-Comparison Sorts:**

**Counting Sort:**
- Time: O(n + k) where k is range
- Space: O(k)
- Stable: Yes
- Use case: Small integer range, known range

**Radix Sort:**
- Time: O(d × (n + k)) where d is digits
- Space: O(n + k)
- Stable: Yes
- Use case: Fixed-length integer keys

**Bucket Sort:**
- Best: O(n + k)
- Average: O(n + k)
- Worst: O(n²)
- Space: O(n + k)
- Stable: Can be
- Use case: Uniformly distributed data

### **4. Search Algorithms Table**

**Linear Search:**
- Time: O(n)
- Space: O(1)
- Use case: Unsorted data, small datasets

**Binary Search:**
- Time: O(log n)
- Space: O(1) iterative, O(log n) recursive
- Requirement: Sorted data
- Use case: Sorted arrays, finding boundaries

**Depth-First Search (DFS):**
- Time: O(V + E) for graphs, O(n) for trees
- Space: O(V) or O(h) where h is height
- Use case: Path finding, topological sort, cycle detection

**Breadth-First Search (BFS):**
- Time: O(V + E)
- Space: O(V)
- Use case: Shortest path (unweighted), level-order traversal

**Dijkstra's Algorithm:**
- Time: O((V + E) log V) with binary heap
- Space: O(V)
- Use case: Shortest path with non-negative weights

**A* Search:**
- Time: O(E) best case, exponential worst case
- Space: O(V)
- Use case: Pathfinding with heuristic, game AI

**Binary Search Tree Search:**
- Average: O(log n)
- Worst: O(n)
- Space: O(1) iterative, O(h) recursive

### **5. String Algorithm Performance**

**Naive Pattern Matching:**
- Time: O(n × m) where n = text length, m = pattern length
- Space: O(1)

**KMP (Knuth-Morris-Pratt):**
- Time: O(n + m)
- Space: O(m) for prefix table

**Boyer-Moore:**
- Best: O(n/m)
- Worst: O(n × m)
- Average: O(n)
- Space: O(m)

**Rabin-Karp:**
- Average: O(n + m)
- Worst: O(n × m)
- Space: O(1)

**Longest Common Subsequence:**
- Time: O(n × m)
- Space: O(n × m), can optimize to O(min(n,m))

**Edit Distance:**
- Time: O(n × m)
- Space: O(n × m), can optimize to O(min(n,m))

### **6. Graph Algorithm Performance**

**Minimum Spanning Tree:**
- Kruskal's: O(E log E) or O(E log V)
- Prim's: O((V + E) log V) with binary heap
- Prim's: O(E + V log V) with Fibonacci heap

**Shortest Path:**
- Dijkstra: O((V + E) log V) with binary heap
- Bellman-Ford: O(V × E)
- Floyd-Warshall: O(V³)

**Network Flow:**
- Ford-Fulkerson: O(E × max_flow)
- Edmonds-Karp: O(V × E²)
- Dinic's: O(V² × E)

**Topological Sort:**
- Time: O(V + E)
- Space: O(V)

**Strongly Connected Components:**
- Kosaraju's: O(V + E)
- Tarjan's: O(V + E)

### **7. Dynamic Programming vs Alternatives**

**Fibonacci:**
- Naive recursive: O(2ⁿ) time, O(n) space
- Memoized DP: O(n) time, O(n) space
- Iterative DP: O(n) time, O(1) space
- Matrix exponentiation: O(log n) time, O(1) space

**Knapsack (0/1):**
- Brute force: O(2ⁿ)
- DP: O(n × W) where W is capacity
- Space: O(n × W), can optimize to O(W)

**Longest Increasing Subsequence:**
- DP: O(n²) time, O(n) space
- Binary search + DP: O(n log n) time, O(n) space

## Performance Trade-off Analysis

### **Time vs Space Trade-offs**

**Memoization/Caching:**
- Trades: Space for time
- Example: DP problems, computed values
- Impact: O(1) lookup at cost of O(n) or O(n²) storage

**In-place Operations:**
- Trades: Time for space
- Example: In-place sorting vs merge sort
- Impact: May increase time complexity but uses O(1) extra space

**Precomputation:**
- Trades: Upfront time + space for query speed
- Example: Prefix sums, lookup tables
- Impact: O(1) queries after O(n) preprocessing

### **Average vs Worst Case**

**Hash Tables:**
- Average: O(1) operations - excellent for most workloads
- Worst: O(n) operations - with poor hash function or adversarial input
- Mitigation: Good hash functions, load factor management

**Quick Sort:**
- Average: O(n log n) - fastest practical sorting
- Worst: O(n²) - with poor pivot selection
- Mitigation: Randomized pivot, median-of-three, hybrid with insertion sort

**Binary Search Trees:**
- Balanced: O(log n) guaranteed
- Unbalanced: Can degrade to O(n)
- Solution: Self-balancing trees (AVL, Red-Black)

### **Amortized Analysis**

**Dynamic Array Resizing:**
- Individual insert: Can be O(n) when resizing
- Amortized: O(1) per insertion over many operations
- Explanation: Doubling strategy spreads cost

**Union-Find with Path Compression:**
- Individual operation: Up to O(log n)
- Amortized: Nearly O(1) - inverse Ackermann function
- Explanation: Path compression optimizes future operations

## Practical Benchmarking Considerations

### **Real-World Performance Factors**

**Cache Locality:**
- Arrays: Excellent cache performance (contiguous memory)
- Linked lists: Poor cache performance (pointer chasing)
- Impact: Can make O(n) array faster than O(log n) tree for small n

**Branch Prediction:**
- Sorted data: Better prediction in conditionals
- Random data: More branch mispredictions
- Impact: Can affect actual performance significantly

**Memory Allocation:**
- Preallocated structures: Faster
- Dynamic allocation: Slower with overhead
- Impact: May dominate for small operations

**Constant Factors:**
- Merge sort vs Quick sort: Both O(n log n) but Quick sort has better constants
- Hash table vs Tree: Hash has O(1) but may be slower for small n due to hashing overhead

### **Input Size Thresholds**

**Small Inputs (n < 50):**
- Simple algorithms often win (insertion sort, linear search)
- Overhead of complex algorithms may dominate
- Cache effects matter more than theoretical complexity

**Medium Inputs (50 < n < 10,000):**
- Good balance point for most efficient algorithms
- O(n log n) clearly beats O(n²)
- Space-time trade-offs become relevant

**Large Inputs (n > 10,000):**
- Asymptotic complexity dominates
- O(n²) becomes prohibitive
- External memory and parallel algorithms may be needed

**Very Large (n > 1,000,000):**
- Even O(n log n) may be slow
- Consider O(n) algorithms when possible
- Distributed/parallel processing often necessary

## Selection Guidelines by Constraint

### **By Memory Constraint**

**Severely Limited (Embedded Systems):**
- Favor: In-place algorithms, iterative over recursive
- Avoid: Hash tables, merge sort, memoization
- Examples: Heap sort, in-place quick sort, selection algorithms

**Moderate Limitation:**
- Balance: Some extra space acceptable for better performance
- Use: Space-optimized DP (rolling arrays)
- Examples: Bottom-up DP, hybrid sorts

**Abundant Memory:**
- Optimize: Purely for speed
- Use: Full memoization, large hash tables, auxiliary structures
- Examples: Top-down DP, counting sort for larger ranges

### **By Latency Requirement**

**Real-time/Interactive (<100ms):**
- Need: O(1) or O(log n) operations
- Use: Hash tables, balanced trees, precomputation
- Avoid: O(n²), unbounded algorithms

**Near Real-time (<1s):**
- Allow: O(n) or O(n log n)
- Use: Efficient sorting, linear scans
- Avoid: Exponential algorithms

**Batch Processing (seconds to minutes):**
- Accept: O(n²) for moderate n, O(n log n) for large n
- Use: Comprehensive algorithms, optimization not critical
- Consider: Thorough but slower approaches

### **By Data Characteristics**

**Nearly Sorted Data:**
- Best: Insertion sort O(n), Tim sort
- Good: Adaptive algorithms
- Avoid: Selection sort, heap sort (no adaptation benefit)

**Random Data:**
- Best: Quick sort, hash tables
- Good: Merge sort, heap sort
- Avoid: Algorithms that assume order

**Duplicate-Heavy Data:**
- Best: Three-way quick sort, counting-based algorithms
- Good: Stable sorts when order matters
- Consider: Specialized duplicate handling

**Small Range Integers:**
- Best: Counting sort, radix sort
- Good: Hash-based approaches
- Avoid: Comparison-based when non-comparison works

## Profiling and Measurement

### **When to Optimize**

1. **Measure first** - Don't assume bottlenecks
2. **Profile** - Use tools to find actual slow points
3. **Focus on hot paths** - 80/20 rule applies
4. **Benchmark** - Compare before and after
5. **Consider maintainability** - Is complexity worth it?

### **Common Profiling Insights**

**Unexpected Results:**
- O(n²) algorithm faster than O(n log n) for n < 100
- Linear search beating binary search for small arrays
- Simple code outperforming "optimized" complex code

**Real Bottlenecks Often:**
- I/O operations (disk, network)
- Memory allocation/deallocation
- Lock contention in concurrent code
- Cache misses
- System calls

## Anti-Patterns in Performance

**Premature Optimization:**
- Optimizing before identifying bottlenecks
- Choosing complex algorithm for tiny datasets
- Solution: Start simple, measure, then optimize

**Ignoring Constants:**
- Assuming O(n log n) always beats O(n²)
- Ignoring real-world overhead
- Solution: Benchmark with realistic data

**Asymptotic Obsession:**
- Optimizing cold paths
- Micro-optimizing when I/O dominates
- Solution: Profile to find actual bottlenecks

**One-Size-Fits-All:**
- Using same algorithm regardless of input
- Not adapting to data characteristics
- Solution: Consider adaptive or hybrid approaches

## Key Takeaways

1. **Complexity is a guide, not absolute truth** - Constants and real-world factors matter
2. **Context determines best choice** - No universally best algorithm
3. **Measure what matters** - Theoretical vs actual performance can differ
4. **Balance trade-offs** - Time, space, code simplicity, maintainability
5. **Start simple** - Optimize only when necessary and after measuring

Performance lookup tables provide the foundation, but effective optimization requires understanding your specific context, constraints, and actual performance characteristics through profiling and measurement.

Would you like me to create a detailed comparison for a specific algorithm family, or help analyze performance characteristics for a particular problem you're working on?