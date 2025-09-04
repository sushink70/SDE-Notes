# DSA

Data structures and algorithms are two fundamental concepts in computer science that work together but serve different purposes:

**Data Structures** are ways of organizing and storing data in a computer so that it can be accessed and used efficiently. They define how data is arranged in memory and what operations can be performed on that data. Think of them as containers or organizational systems for your data.

Common examples include:

- Arrays (store elements in sequential memory locations)
- Linked Lists (elements connected through pointers)
- Stacks (last-in, first-out structure)
- Queues (first-in, first-out structure)
- Trees (hierarchical structure with parent-child relationships)
- Hash Tables (key-value pairs for fast lookups)

**Algorithms** are step-by-step procedures or sets of rules for solving specific problems or performing computations. They define the logic and methodology for manipulating data, regardless of how that data is stored.

Common examples include:

- Sorting algorithms (bubble sort, merge sort, quicksort)
- Search algorithms (linear search, binary search)
- Graph traversal algorithms (breadth-first search, depth-first search)
- Dynamic programming algorithms
- Machine learning algorithms

**Key Differences:**

**Purpose**: Data structures focus on *how* to organize data, while algorithms focus on *what* to do with that data.

**Nature**: Data structures are static organizational frameworks, while algorithms are dynamic processes or procedures.

**Relationship**: They're interdependent - the choice of data structure affects which algorithms you can use efficiently, and the algorithms you need to implement influence which data structures are most appropriate.

For example, if you need to frequently search for items, you might choose a hash table (data structure) and implement a hash-based lookup algorithm. If you need to maintain sorted data, you might use a binary search tree (data structure) with insertion and search algorithms designed for trees.

Understanding both concepts and how they interact is crucial for writing efficient, well-designed software.

Here's a comprehensive list of data structures, organized by category:

## Linear Data Structures

**Arrays and Array-like Structures:**

- Static Array (fixed size)
- Dynamic Array (resizable, like ArrayList, Vector)
- Sparse Array (for arrays with many empty elements)
- Circular Array
- Multi-dimensional Arrays (2D, 3D, etc.)

**Lists:**

- Singly Linked List
- Doubly Linked List
- Circular Linked List
- Skip List
- Unrolled Linked List

**Stack and Queue Variants:**

- Stack (LIFO)
- Queue (FIFO)
- Circular Queue
- Priority Queue
- Double-ended Queue (Deque)

## Non-Linear Data Structures

**Trees:**

- Binary Tree
- Binary Search Tree (BST)
- AVL Tree (self-balancing BST)
- Red-Black Tree
- B-Tree
- B+ Tree
- Splay Tree
- Treap
- Trie (Prefix Tree)
- Suffix Tree
- Segment Tree
- Fenwick Tree (Binary Indexed Tree)
- Heap (Binary Heap, Min/Max Heap)
- Fibonacci Heap
- Binomial Heap
- Decision Tree
- Parse Tree
- Expression Tree
- N-ary Tree
- Quad Tree
- Octree
- R-Tree
- LSM Tree

**Graphs:**

- Directed Graph (Digraph)
- Undirected Graph
- Weighted Graph
- Unweighted Graph
- Directed Acyclic Graph (DAG)
- Complete Graph
- Bipartite Graph
- Planar Graph
- Sparse Graph
- Dense Graph

## Hash-based Structures

- Hash Table/Hash Map
- Hash Set
- Bloom Filter
- Count-Min Sketch
- HyperLogLog
- Cuckoo Hash Table
- Robin Hood Hash Table
- Consistent Hashing

## String Data Structures

- String (basic)
- Rope (for large strings)
- Trie (Prefix Tree)
- Suffix Array
- Suffix Tree
- Aho-Corasick Automaton
- Z-Algorithm structure
- KMP failure function

## Advanced/Specialized Structures

**Set and Map Variants:**

- Disjoint Set (Union-Find)
- Ordered Set/Map
- Multiset/Multimap
- Interval Tree
- Range Tree

**Geometric Data Structures:**

- Point
- Line Segment
- Polygon
- Convex Hull
- Voronoi Diagram
- Delaunay Triangulation
- KD-Tree
- Range Tree

**Database Structures:**

- B+ Tree (for databases)
- LSM Tree (Log-Structured Merge Tree)
- Merkle Tree
- Patricia Trie

**Concurrent/Parallel Structures:**

- Lock-free Stack
- Lock-free Queue
- Concurrent Hash Map
- Read-Copy-Update (RCU) structures

**Probabilistic Structures:**

- Bloom Filter
- Count-Min Sketch
- HyperLogLog
- Skip List

**Cache-related Structures:**

- LRU Cache
- LFU Cache
- Cache-Oblivious structures

**Functional Programming Structures:**

- Persistent List
- Persistent Tree
- Immutable structures
- Copy-on-Write structures

**Specialized Application Structures:**

- Matrix (sparse, dense)
- Tensor
- Time Series structures
- Spatial data structures
- Network/Social Graph structures

Each data structure has specific use cases, performance characteristics, and trade-offs in terms of time and space complexity for different operations. The choice depends on your specific requirements for insertion, deletion, search, memory usage, and access patterns.

Here's a comprehensive list of algorithms organized by category:

## Sorting Algorithms

**Comparison-based Sorting:**

- Bubble Sort ✅
- Selection Sort ✅
- Insertion Sort
- Merge Sort ✅
- Quick Sort ✅
- Heap Sort
- Shell Sort ✅
- Cocktail Shaker Sort
- Gnome Sort
- Comb Sort
- Tim Sort
- Intro Sort

**Non-comparison Sorting:**

- Counting Sort
- Radix Sort ✅
- Bucket Sort
- Pigeonhole Sort
- Flash Sort

**Specialized Sorting:**

- Topological Sort
- External Sorting
- Parallel Sorting algorithms
- In-place Sorting variants

## Search Algorithms

**Linear Search Variants:**

- Linear Search
- Sentinel Linear Search
- Binary Search
- Interpolation Search
- Exponential Search
- Jump Search
- Fibonacci Search
- Ternary Search

**Tree Search:**

- Depth-First Search (DFS)
- Breadth-First Search (BFS)
- Best-First Search
- A* Search
- Dijkstra's Algorithm
- Bellman-Ford Algorithm
- Floyd-Warshall Algorithm

**String Search:**

- Naive String Search
- KMP (Knuth-Morris-Pratt)
- Boyer-Moore Algorithm
- Rabin-Karp Algorithm
- Z Algorithm
- Aho-Corasick Algorithm

## Graph Algorithms

**Traversal:**

- Depth-First Search (DFS)
- Breadth-First Search (BFS)
- Iterative Deepening

**Shortest Path:**

- Dijkstra's Algorithm
- Bellman-Ford Algorithm
- Floyd-Warshall Algorithm
- Johnson's Algorithm
- A* Algorithm

**Minimum Spanning Tree:**

- Kruskal's Algorithm
- Prim's Algorithm
- Borůvka's Algorithm

**Network Flow:**

- Ford-Fulkerson Algorithm
- Edmonds-Karp Algorithm
- Dinic's Algorithm
- Push-Relabel Algorithm

**Graph Coloring:**

- Greedy Coloring
- Welsh-Powell Algorithm
- Brook's Algorithm

**Cycle Detection:**

- Floyd's Cycle Detection
- Topological Sort (for DAG)
- Tarjan's Algorithm

**Connectivity:**

- Tarjan's Strongly Connected Components
- Kosaraju's Algorithm
- Union-Find Algorithm

## Dynamic Programming Algorithms

**Classic Problems:**

- Fibonacci Sequence
- Longest Common Subsequence (LCS)
- Longest Increasing Subsequence (LIS)
- Edit Distance (Levenshtein Distance)
- Knapsack Problem (0/1 and Unbounded)
- Coin Change Problem
- Matrix Chain Multiplication
- Optimal Binary Search Tree
- Rod Cutting Problem
- Subset Sum Problem

**Advanced DP:**

- Bitmasking DP
- Tree DP
- Digit DP
- Probability DP
- Game Theory DP

## Greedy Algorithms

- Activity Selection Problem
- Fractional Knapsack
- Huffman Coding
- Job Scheduling
- Minimum Spanning Tree algorithms
- Dijkstra's Algorithm
- Prim's Algorithm
- Kruskal's Algorithm

## Divide and Conquer

- Merge Sort
- Quick Sort
- Binary Search
- Strassen's Matrix Multiplication
- Closest Pair of Points
- Maximum Subarray Problem (Kadane's variant)
- Fast Fourier Transform (FFT)

## Backtracking Algorithms

- N-Queens Problem
- Sudoku Solver
- Graph Coloring
- Hamiltonian Path/Cycle
- Subset Generation
- Permutation Generation
- Knight's Tour Problem
- Maze Solving

## Mathematical Algorithms

**Number Theory:**

- Euclidean Algorithm (GCD)
- Extended Euclidean Algorithm
- Sieve of Eratosthenes
- Primality Testing (Miller-Rabin, etc.)
- Modular Exponentiation
- Chinese Remainder Theorem
- Fermat's Little Theorem applications

**Matrix Operations:**

- Matrix Multiplication
- Gaussian Elimination
- LU Decomposition
- Determinant Calculation
- Matrix Inversion
- Eigenvalue algorithms

**Combinatorics:**

- Permutation Generation
- Combination Generation
- Catalan Numbers
- Pascal's Triangle

## Geometric Algorithms

- Convex Hull (Graham Scan, Jarvis March)
- Line Intersection
- Point in Polygon
- Closest Pair of Points
- Voronoi Diagram construction
- Delaunay Triangulation
- Area/Volume calculations
- Collision Detection algorithms

## String Algorithms

**Pattern Matching:**

- KMP Algorithm
- Boyer-Moore Algorithm
- Rabin-Karp Algorithm
- Z Algorithm
- Aho-Corasick Algorithm

**String Processing:**

- Longest Common Substring
- Longest Palindromic Substring
- String Reversal
- Anagram Detection
- Suffix Array construction
- Manacher's Algorithm

## Tree Algorithms

- Tree Traversals (Inorder, Preorder, Postorder)
- Level Order Traversal
- Tree Height Calculation
- Lowest Common Ancestor (LCA)
- Tree Diameter
- Tree Isomorphism
- Heavy-Light Decomposition
- Centroid Decomposition

## Machine Learning Algorithms

**Supervised Learning:**

- Linear Regression
- Logistic Regression
- Decision Trees
- Random Forest
- Support Vector Machines (SVM)
- K-Nearest Neighbors (KNN)
- Naive Bayes
- Neural Networks/Deep Learning

**Unsupervised Learning:**

- K-Means Clustering
- Hierarchical Clustering
- DBSCAN
- Principal Component Analysis (PCA)
- Independent Component Analysis (ICA)

**Reinforcement Learning:**

- Q-Learning
- SARSA
- Policy Gradient Methods
- Actor-Critic Methods

## Optimization Algorithms

- Gradient Descent
- Simulated Annealing
- Genetic Algorithm
- Particle Swarm Optimization
- Ant Colony Optimization
- Linear Programming (Simplex Method)
- Interior Point Methods

## Cryptographic Algorithms

- RSA Algorithm
- Diffie-Hellman Key Exchange
- Advanced Encryption Standard (AES)
- Data Encryption Standard (DES)
- SHA (Secure Hash Algorithm)
- MD5 (Message Digest)
- Digital Signature algorithms

## Parallel/Concurrent Algorithms

- Parallel Sorting algorithms
- MapReduce algorithms
- Lock-free algorithms
- Wait-free algorithms
- Consensus algorithms (Paxos, Raft)

## Approximation Algorithms

- Traveling Salesman Problem approximations
- Vertex Cover approximation
- Set Cover approximation
- Load Balancing algorithms

## Randomized Algorithms

- Monte Carlo methods
- Las Vegas algorithms
- Randomized QuickSort
- Skip List operations
- Bloom Filter operations

## Computational Geometry

- Graham Scan
- Gift Wrapping Algorithm
- Sutherland-Hodgman Clipping
- Cohen-Sutherland Line Clipping
- Bresenham's Line Algorithm

## Summary

Each category contains algorithms with different time and space complexities, use cases, and performance characteristics. The choice of algorithm depends on the specific problem requirements, input size, and performance constraints.