I'll create a comprehensive guide on algorithm selection flowcharts - visual tools that help you choose the right algorithm for specific problems.

## What are Algorithm Selection Flowcharts?

Algorithm selection flowcharts are decision-making diagrams that guide you through choosing optimal algorithms based on problem characteristics, constraints, and requirements.

## Major Algorithm Categories & Selection Criteria

### **1. Sorting Algorithms**

**Key Questions:**
- What's the input size? (Small < 50, Medium < 10K, Large > 10K)
- Is the data nearly sorted?
- Do you need stable sorting?
- What are space constraints?

**Decision Path:**
- **Small dataset + simplicity needed** → Insertion Sort
- **Nearly sorted data** → Insertion Sort or Bubble Sort
- **General purpose, guaranteed O(n log n)** → Merge Sort
- **Average case speed, in-place needed** → Quick Sort
- **Working with primitives, linear time possible** → Counting/Radix Sort
- **Guaranteed O(n log n) in-place** → Heap Sort

### **2. Searching Algorithms**

**Key Questions:**
- Is data sorted?
- Is data in memory or on disk?
- What's the search frequency?

**Decision Path:**
- **Sorted array** → Binary Search O(log n)
- **Unsorted small dataset** → Linear Search O(n)
- **Frequent searches needed** → Build Hash Table O(1) lookup
- **Range queries on sorted data** → Binary Search variations
- **Pattern matching in text** → KMP, Boyer-Moore, Rabin-Karp

### **3. Graph Algorithms**

**Key Questions:**
- Weighted or unweighted?
- Directed or undirected?
- What's the problem type?

**Decision Path:**
- **Shortest path, unweighted** → BFS
- **Shortest path, weighted, no negative edges** → Dijkstra's
- **Shortest path, negative edges allowed** → Bellman-Ford
- **All pairs shortest path** → Floyd-Warshall
- **Minimum spanning tree** → Kruskal's or Prim's
- **Explore all nodes/paths** → DFS
- **Topological ordering** → DFS or Kahn's algorithm
- **Strongly connected components** → Kosaraju's or Tarjan's

### **4. Dynamic Programming vs. Greedy vs. Divide & Conquer**

**Key Questions:**
- Does the problem have optimal substructure?
- Are there overlapping subproblems?
- Does greedy choice lead to global optimum?

**Decision Path:**
- **Overlapping subproblems + optimal substructure** → Dynamic Programming
- **Greedy choice property + optimal substructure** → Greedy Algorithm
- **Independent subproblems** → Divide & Conquer
- **No clear structure** → Backtracking or Brute Force

### **5. String Algorithms**

**Key Questions:**
- Pattern matching or manipulation?
- Single pattern or multiple?
- Exact or approximate matching?

**Decision Path:**
- **Simple pattern search** → Naive/KMP
- **Multiple pattern search** → Aho-Corasick
- **Longest common subsequence** → DP
- **String matching with preprocessing** → Suffix Array/Tree
- **Approximate matching** → Edit Distance (DP)

## Performance Consideration Matrix

| Constraint | Consider | Avoid |
|------------|----------|-------|
| Limited memory | In-place algorithms, streaming | Algorithms requiring extra space |
| Real-time requirements | O(1) or O(log n) | O(n²) or exponential |
| Large datasets | O(n log n) or better | O(n²) or worse |
| Parallel processing | Divide & Conquer | Sequential algorithms |
| Worst-case guarantees | Merge Sort, Heap Sort | Quick Sort (standard) |

## Quick Selection Guide by Problem Type

**Optimization Problems:**
- Maximize/minimize with constraints → Dynamic Programming or Greedy
- Resource allocation → Greedy or Linear Programming
- Path optimization → Dijkstra's, A*, Bellman-Ford

**Combinatorial Problems:**
- Generate all solutions → Backtracking
- Find feasible solution → Constraint satisfaction
- Count solutions → Dynamic Programming

**Computational Geometry:**
- Closest points → Divide & Conquer
- Convex hull → Graham Scan, Jarvis March
- Line intersection → Sweep Line

**Data Processing:**
- Aggregation → Hash tables, sorting
- Filtering → Linear scan with conditions
- Transformation → Map-Reduce paradigm

## Practical Decision Framework

1. **Identify the problem type** (search, sort, optimization, etc.)
2. **Analyze constraints** (time, space, input size)
3. **Consider data characteristics** (sorted, unique, distribution)
4. **Evaluate trade-offs** (time vs. space, average vs. worst-case)
5. **Prototype and benchmark** if multiple candidates exist

Would you like me to create an interactive visual flowchart for a specific algorithm category, or dive deeper into algorithm selection for a particular problem domain you're working with?