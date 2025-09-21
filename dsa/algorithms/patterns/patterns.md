Great question 👍 — array problems are everywhere in coding interviews, competitive programming, and real-world applications. Instead of approaching each problem randomly, it’s smart to recognize **common patterns** that keep showing up. Here’s a structured list of **array problem-solving patterns** you can use:

---

## 🔑 Core Patterns for Array Problems

### 1. **Two Pointers**

* Use when you need to check pairs or subsequences efficiently.
* Works best on **sorted arrays**.
* Common problems:

  * Find a pair with a given sum.
  * Remove duplicates in-place.
  * Container With Most Water (maximize area).

---

### 2. **Sliding Window**

* Use when dealing with **subarrays (contiguous)** and optimizing for length/sum/product.
* Moves a "window" of elements forward without recomputing from scratch.
* Common problems:

  * Maximum sum subarray of size `k`.
  * Longest substring/array without repeating characters.
  * Minimum window substring (variant).

---

### 3. **Prefix Sum / Cumulative Sum**

* Precompute sums so you can query subarray sums in O(1).
* Often combined with hashing for target-based problems.
* Common problems:

  * Subarray sum equals `k`.
  * Range sum queries.
  * Count subarrays divisible by `k`.

---

### 4. **Hashing / Frequency Map**

* Track occurrences of numbers or check existence in O(1).
* Useful when array is unsorted.
* Common problems:

  * Two Sum.
  * Find duplicates.
  * Longest consecutive sequence.

---

### 5. **Sorting + Binary Search**

* Many problems simplify after sorting.
* Binary search is powerful for lookups and boundaries.
* Common problems:

  * Find the missing number.
  * Search in rotated sorted array.
  * Median of two sorted arrays.

---

### 6. **Divide and Conquer**

* Split into subarrays, solve recursively, merge results.
* Common problems:

  * Maximum subarray (Kadane’s vs divide and conquer).
  * Merge sort / quick sort.
  * Count inversions.

---

### 7. **Greedy Scanning**

* Make local optimal choices while scanning the array.
* Common problems:

  * Jump Game.
  * Trapping Rain Water (two-pointer greedy).
  * Stock buy/sell problems.

---

### 8. **Dynamic Programming (on arrays)**

* Break problem into overlapping subproblems.
* Common problems:

  * Maximum subarray sum (Kadane’s algorithm).
  * House Robber.
  * Longest increasing subsequence.

---

### 9. **Matrix / 2D Array Traversal**

* Extension of array patterns to 2D grids.
* Use DFS/BFS, direction vectors, or prefix sums (2D).
* Common problems:

  * Rotate matrix.
  * Search in 2D sorted matrix.
  * Island counting (DFS/BFS).

---

### 10. **Cyclic Sort / Index Placement**

* Place numbers at their correct index to find missing/duplicate numbers.
* Common problems:

  * Missing number.
  * Find all duplicates.
  * First missing positive.

---

## ⚡ Extra Useful Tricks

* **Kadane’s Algorithm** → max subarray sum.
* **Moore’s Voting Algorithm** → majority element.
* **Reservoir Sampling** → random pick from array.
* **Monotonic Stack/Queue** → next greater element, sliding window max.

---

👉 A smart approach is:

1. Identify if the problem is about **pairs/subarrays/subsequences**.
2. Check if it involves **sum/product/length/frequency**.
3. Pick the right pattern (sliding window, two pointers, hashing, etc).

---

Would you like me to **map these patterns to common interview problems** (like LeetCode top ones) so you can see how to apply them directly?

Nice follow-up 👌 — tree problems also have well-known **patterns** just like arrays. If you recognize the pattern, solving becomes way easier. Let’s go step by step:

---

## 🌳 Core Patterns for Tree Problems

### 1. **DFS (Depth-First Search) Traversals**

* Explore all nodes along one branch before backtracking.
* Types:

  * Preorder (Root → Left → Right)
  * Inorder (Left → Root → Right)
  * Postorder (Left → Right → Root)
* Common problems:

  * Validate BST (inorder should be sorted).
  * Serialize/deserialize tree.
  * Diameter of binary tree.

---

### 2. **BFS (Breadth-First Search) / Level Order**

* Traverse level by level using a queue.
* Common problems:

  * Binary tree level order traversal.
  * Minimum depth of binary tree.
  * Zigzag/spiral traversal.

---

### 3. **Recursion / Divide & Conquer**

* Treat each subtree as a smaller problem.
* Common problems:

  * Maximum depth of a tree.
  * Balanced binary tree check.
  * Lowest Common Ancestor (LCA).

---

### 4. **Backtracking on Trees**

* Explore paths, undo choices as you return up.
* Common problems:

  * Path sum problems.
  * All root-to-leaf paths.
  * Word search (if modeled as a trie/tree).

---

### 5. **Binary Search Tree (BST) Specific**

* Exploit ordering properties.
* Common problems:

  * Search/insert/delete in BST.
  * Kth smallest/largest element.
  * Range sum of BST.

---

### 6. **Tree Dynamic Programming**

* Compute info bottom-up, storing results in recursion.
* Common problems:

  * Maximum path sum.
  * House Robber III (choose node or its children).
  * Diameter of tree.

---

### 7. **Iterative Traversal (Stack/Queue Simulation)**

* Replace recursion with stack/queue for iterative solutions.
* Common problems:

  * Iterative inorder/preorder/postorder.
  * BFS using queue.

---

### 8. **Parent / Ancestor Tracking**

* Store parent pointers or use recursion to trace ancestors.
* Common problems:

  * Lowest Common Ancestor (LCA).
  * Distance between two nodes.
  * Cousins in binary tree.

---

### 9. **Serialization / Encoding Trees**

* Flatten tree into array/string and rebuild later.
* Common problems:

  * Serialize and deserialize binary tree (LeetCode 297).
  * Convert tree to linked list (flatten).

---

### 10. **Special Trees / Variants**

* **Trie (Prefix Tree)** → prefix search, word dictionaries.
* **Segment Tree / Fenwick Tree (BIT)** → range queries, updates.
* **N-ary Trees** → multi-child nodes, solved with DFS/BFS.

---

## ⚡ Handy Techniques

* **Morris Traversal** → inorder without recursion/stack.
* **Postorder DP** → bottom-up calculations.
* **Euler Tour + Binary Lifting** → fast LCA queries.

---

👉 The trick is: when you see a tree problem, first ask:

* Is it **traversal-based** (DFS/BFS)?
* Is it **path-based** (sum, diameter, ancestor)?
* Is it **structure-based** (BST, trie, segment tree)?

---

Would you like me to create a **tree problem → pattern mapping** (like "diameter of tree = DFS + postorder DP") similar to what I did for arrays? That way you’ll know which pattern to apply instantly.

Excellent 👌 — heaps (priority queues) also have their own **set of patterns**. Unlike arrays/trees where traversal dominates, heap problems usually revolve around **ordering, top-k, or scheduling**. Let’s break it down:

---

## ⛰️ Core Heap Problem-Solving Patterns

### 1. **Top-K Elements**

* Use a **min-heap** to keep track of the `k` largest elements seen so far.
* Or a **max-heap** for the `k` smallest.
* Common problems:

  * Find `k` largest elements in an array.
  * Kth largest/smallest element.
  * Top `k` frequent elements.

---

### 2. **Heap + Two Pointers / Sliding Window**

* Maintain a heap for the current window.
* Common problems:

  * Sliding window maximum.
  * Find median from data stream (two heaps approach).

---

### 3. **Merge Sorted Lists / Streams**

* Use a **min-heap** to repeatedly extract the smallest among multiple sorted sources.
* Common problems:

  * Merge `k` sorted linked lists.
  * Smallest range covering elements from `k` lists.

---

### 4. **Greedy Scheduling with Heap**

* Heaps are great for scheduling tasks/events based on priority.
* Common problems:

  * Meeting rooms (minimum number of rooms needed).
  * Task scheduler (CPU scheduling with cooldown).
  * Interval problems (allocate based on earliest finishing time).

---

### 5. **Heap + Sorting Hybrid**

* Use heap when you don’t need full sort, only partial order.
* Common problems:

  * Sort nearly sorted array (each element ≤ k away).
  * Reorganize string (arrange letters so no two adjacent are same).

---

### 6. **Heap in Graph Algorithms**

* Dijkstra’s shortest path → min-heap to always pick smallest distance node.
* Prim’s MST algorithm → min-heap for cheapest edge.

---

### 7. **Heap with Custom Comparators**

* Build heaps that order by special rules (frequency, interval length, tuple fields).
* Common problems:

  * Top `k` frequent words.
  * Task reordering problems.
  * Event simulation problems.

---

### 8. **Dual Heaps / Lazy Deletion**

* Sometimes you need to support both min & max queries efficiently.
* Use **two heaps** or a heap + hash map.
* Common problems:

  * Find median from data stream.
  * Sliding window median.

---

## ⚡ Handy Heap Tricks

* **Heapify** → build heap in O(n) instead of O(n log n).
* **Bounded Size Heap** → keep heap size ≤ k for efficiency.
* **Custom tuple ordering** → push `(priority, data)` pairs.
* **Use both min & max heaps** for bidirectional queries.

---

👉 When you see a heap problem, ask:

* Is it **top-k / order statistic**? → bounded heap.
* Is it **streaming / sliding window**? → two heaps.
* Is it **scheduling / interval**? → greedy + heap.
* Is it **graph algorithm**? → Dijkstra/Prim with heap.

---

Would you like me to also make a **comparison chart**: (Array patterns vs Tree patterns vs Heap patterns) so you can see which category a problem usually falls into?

Perfect 🚀 — graphs are the **most pattern-rich** data structure. Many hard problems reduce to a few classic **graph patterns**. Once you know these, most graph problems become a recognition game instead of starting from scratch.

---

## 🌐 Core Graph Problem-Solving Patterns

### 1. **Traversal (DFS & BFS)**

* Explore nodes and edges systematically.
* **DFS** → recursion/stack (good for paths, connected components).
* **BFS** → queue (good for shortest path in *unweighted* graphs).
* Common problems:

  * Count connected components.
  * Check if graph is bipartite.
  * Shortest path in unweighted graph.

---

### 2. **Cycle Detection**

* **Undirected graphs** → DFS + parent check or Union-Find (Disjoint Set Union).
* **Directed graphs** → DFS + recursion stack (white-gray-black coloring).
* Common problems:

  * Detect cycle in graph.
  * Course schedule (topological sort existence).

---

### 3. **Topological Sorting (DAGs)**

* Order nodes so that edges go from earlier to later.
* Methods:

  * DFS + stack.
  * Kahn’s algorithm (BFS + in-degree).
* Common problems:

  * Course schedule.
  * Task ordering.

---

### 4. **Shortest Paths**

* **Unweighted graph** → BFS.
* **Weighted graph** →

  * Dijkstra (non-negative weights).
  * Bellman-Ford (handles negative weights).
  * Floyd-Warshall (all pairs).
* Common problems:

  * Network delay time.
  * Cheapest flights within K stops.

---

### 5. **Minimum Spanning Tree (MST)**

* Connect all nodes with minimum edge weight.
* Algorithms:

  * Kruskal (Union-Find).
  * Prim (Heap).
* Common problems:

  * Minimum cost to connect all cities.
  * Optimize network cables/roads.

---

### 6. **Union-Find / Disjoint Set Union (DSU)**

* Manage connected components efficiently.
* Optimizations: path compression + union by rank.
* Common problems:

  * Number of connected components.
  * Accounts merge.
  * Kruskal’s MST.

---

### 7. **Graph Coloring**

* Assign colors/states to nodes.
* Common problems:

  * Bipartite graph check.
  * Map coloring problems.
  * Scheduling with constraints.

---

### 8. **Strongly Connected Components (SCC)**

* Subgraphs where every node is reachable from every other node.
* Algorithms:

  * Kosaraju’s algorithm.
  * Tarjan’s algorithm.
* Common problems:

  * Count SCCs.
  * Condense graph into DAG.

---

### 9. **Flow / Matching**

* Model as max-flow/min-cut problems.
* Algorithms:

  * Ford-Fulkerson / Edmonds-Karp.
  * Hopcroft–Karp (bipartite matching).
* Common problems:

  * Max bipartite matching.
  * Network bandwidth.

---

### 10. **Grid / Matrix as Graph**

* Treat 2D matrix as graph with neighbors.
* Use BFS/DFS/Union-Find.
* Common problems:

  * Number of islands.
  * Shortest path in binary matrix.
  * Walls and gates.

---

## ⚡ Handy Tricks

* **Adjacency list vs matrix** → pick based on density.
* **Visited set/array** → avoid infinite loops.
* **Parent tracking** → for path reconstruction.
* **Bitmasking + DP** → traveling salesman, Hamiltonian paths.

---

👉 When you see a graph problem, first ask:

* Is it about **reachability/connectedness**? → DFS/BFS/Union-Find.
* Is it about **ordering/dependencies**? → Topological sort.
* Is it about **shortest path/cost**? → BFS/Dijkstra/Bellman-Ford.
* Is it about **partitioning**? → Coloring / Bipartite / Flow.

---

Would you like me to also build you a **“cheat sheet” that compares patterns across arrays, trees, heaps, and graphs** so you have one unified reference?

Excellent again 👌 — strings are a **core interview topic** and like arrays/trees/graphs, they also boil down to **common patterns**. Once you recognize these, you can attack most string problems systematically.

---

## 🔤 Core String Problem-Solving Patterns

### 1. **Two Pointers**

* Treat string like an array of chars, move left/right pointers.
* Common problems:

  * Palindrome check.
  * Reverse words in a string.
  * Longest substring with constraints (expand/shrink).

---

### 2. **Sliding Window**

* For substring problems involving uniqueness, frequency, or max length.
* Common problems:

  * Longest substring without repeating characters.
  * Minimum window substring.
  * Find anagrams in a string.

---

### 3. **Hashing / Frequency Counting**

* Count character occurrences (maps, arrays, bitmasks).
* Common problems:

  * Valid anagram.
  * Group anagrams.
  * Find first unique character.

---

### 4. **Prefix / Suffix Based**

* Precompute prefix/suffix arrays for fast queries.
* Common problems:

  * Longest prefix-suffix (KMP preprocessing).
  * String matching (Rabin-Karp, KMP, Z-algorithm).
  * Count substrings with given conditions.

---

### 5. **Dynamic Programming (DP on Strings)**

* Break down into subproblems (often with 2D DP).
* Common problems:

  * Longest common subsequence (LCS).
  * Longest palindromic subsequence.
  * Edit distance (Levenshtein).
  * Regular expression matching.

---

### 6. **Manacher’s / Palindrome Expansion**

* Special palindrome algorithms.
* Common problems:

  * Longest palindromic substring.
  * Count palindromic substrings.

---

### 7. **Trie / Suffix Tree / Automaton**

* For prefix-based search and multiple word problems.
* Common problems:

  * Word search (dictionary).
  * Auto-complete system.
  * Longest common prefix.

---

### 8. **String Sorting / Rearrangement**

* Reorder characters while meeting constraints.
* Common problems:

  * Reorganize string (no adjacent duplicates).
  * Sort characters by frequency.
  * Smallest lexicographical string after swaps.

---

### 9. **Greedy + Stack**

* Useful for removing/reordering characters.
* Common problems:

  * Remove k digits (to form smallest number).
  * Decode string (nested encoding like `3[a2[c]]`).
  * Smallest subsequence of distinct characters.

---

### 10. **Pattern Matching & Parsing**

* Algorithms and parsing methods.
* Common problems:

  * Substring search (KMP, Rabin-Karp, Z).
  * Wildcard/regex matching.
  * Evaluate expressions (infix → postfix).

---

## ⚡ Handy Tricks

* **ASCII array of size 26 / 128 / 256** for fast char counts.
* **Bitmasks** to represent subsets of characters.
* **Rolling hash** (Rabin-Karp) for substring comparisons.
* **Suffix arrays** for advanced string matching.

---

👉 When you see a string problem, ask:

* Is it **substring/contiguous**? → sliding window.
* Is it **subsequence/edit distance**? → DP.
* Is it about **prefix/suffix search**? → KMP/Trie.
* Is it **palindrome-related**? → expand center / DP / Manacher.
* Is it **frequency/rearrangement**? → hashing/heap/greedy.

---

Do you want me to put together a **big unified reference chart** (Arrays, Trees, Heaps, Graphs, Strings → with their patterns + typical problems) so you have a single “cheat sheet” for all major data structures?

Nice one 🔥 — **interval problems** show up everywhere (scheduling, merging, ranges, calendar events). They look tricky at first, but almost all of them fall into a **handful of patterns**.

---

## ⏳ Core Interval Problem-Solving Patterns

### 1. **Sorting by Start (or End) Time**

* Most interval problems start with sorting.
* Sorting helps detect overlaps, merge intervals, or allocate resources.
* Common problems:

  * Merge intervals.
  * Insert interval.
  * Minimum number of meeting rooms.

---

### 2. **Merging Overlapping Intervals**

* After sorting, check if `current.start <= prev.end`.
* Merge by updating `end = max(prev.end, current.end)`.
* Common problems:

  * Merge intervals.
  * Employee free time.
  * Range coverage problems.

---

### 3. **Greedy Scheduling**

* Choose intervals with the earliest finishing time (classic greedy).
* Common problems:

  * Activity selection problem.
  * Maximum number of non-overlapping intervals.
  * Erase minimum intervals to avoid overlaps.

---

### 4. **Sweep Line (Chronological Ordering)**

* Convert intervals into events (start = +1, end = -1).
* Sweep through sorted events to track active intervals.
* Common problems:

  * Minimum number of meeting rooms.
  * Maximum overlap at any point.
  * Skyline problem.

---

### 5. **Heap (Priority Queue) + Intervals**

* Use a heap to track currently active intervals (min-heap on end times).
* Common problems:

  * Meeting rooms II.
  * CPU task scheduling.
  * Interval partitioning.

---

### 6. **Binary Search on Intervals**

* If intervals are sorted, you can binary search for compatible ones.
* Common problems:

  * Find right interval (LeetCode 436).
  * Weighted interval scheduling (DP + binary search).

---

### 7. **Dynamic Programming on Intervals**

* For optimization problems where greedy doesn’t work.
* Common problems:

  * Weighted interval scheduling (choose interval or skip).
  * Maximum profit job scheduling.
  * Palindrome partitioning (DP on subintervals).

---

### 8. **Interval Graphs / Union-Find**

* Sometimes intervals are modeled as graph nodes with overlaps = edges.
* Common problems:

  * Connected components of intervals.
  * Group overlapping intervals.

---

### 9. **Segment Tree / Interval Tree**

* Efficient for range queries or updates.
* Common problems:

  * Count overlapping intervals dynamically.
  * Range sum / range minimum with interval updates.
  * Calendar booking with conflicts.

---

### 10. **Two Pointers for Two Interval Lists**

* Traverse two sorted interval lists in parallel.
* Common problems:

  * Interval list intersections.
  * Compare availability (two calendars).

---

## ⚡ Handy Tricks

* Always **sort by start (or end) time first**.
* Overlap check → `if current.start <= prev.end`.
* Use **end-time min-heap** to manage parallel intervals.
* Convert to **events (sweep line)** for counting overlaps.

---

👉 When you see an interval problem, ask:

* Is it about **merging overlaps**? → sort + merge.
* Is it about **maximum usage / rooms**? → heap or sweep line.
* Is it about **choosing optimal intervals**? → greedy (earliest finish) or DP.
* Is it about **range queries**? → segment tree / interval tree.

---

Would you like me to make a **visual roadmap (like a flowchart)** for intervals that shows:
"if merging → do this, if scheduling → do this, if optimizing → use DP"?

Awesome 🚀 — **linked list problems** can feel tricky because you can’t access elements randomly like arrays. But the good news: almost every linked list problem falls into a **few common patterns**.

---

## 🔗 Core Linked List Problem-Solving Patterns

### 1. **Two Pointers (Fast & Slow)**

* Use one fast pointer and one slow pointer.
* Common problems:

  * Detect cycle in a linked list.
  * Find start of cycle.
  * Find middle of linked list.
  * Check if linked list is palindrome.

---

### 2. **Dummy Node Technique**

* Add a fake head node to simplify edge cases.
* Common problems:

  * Remove Nth node from end.
  * Merge two sorted lists.
  * Partition list around a value.

---

### 3. **Reversal Patterns**

* Iterative or recursive reversal of pointers.
* Variants:

  * Reverse whole list.
  * Reverse in groups of k.
  * Reverse between two indices.
* Common problems:

  * Reverse linked list.
  * Reverse nodes in k-group.

---

### 4. **Cycle Detection & Removal**

* Floyd’s cycle detection (fast & slow pointers).
* Common problems:

  * Detect cycle in linked list.
  * Remove cycle.

---

### 5. **Merging & Splitting**

* Merge multiple lists, split into halves.
* Common problems:

  * Merge k sorted linked lists (heap or divide & conquer).
  * Sort linked list (merge sort).
  * Split list to parts.

---

### 6. **Linked List as a Number**

* Treat nodes as digits.
* Common problems:

  * Add two numbers (carry handling).
  * Multiply numbers represented by linked lists.

---

### 7. **In-Place Reordering**

* Rearrange nodes without extra space.
* Common problems:

  * Reorder list (L0 → Ln → L1 → Ln-1 …).
  * Odd-even linked list.
  * Flatten multilevel linked list.

---

### 8. **Hashing / Set for Reference Tracking**

* Store visited nodes for O(1) cycle/duplicate detection.
* Common problems:

  * Intersection of two linked lists.
  * Detect cycle (alternative to fast/slow).

---

### 9. **Linked List + Heap / Sorting**

* Combine with heaps or divide & conquer.
* Common problems:

  * Merge k sorted lists (min-heap).
  * Sort linked list in O(n log n).

---

### 10. **Special Linked Lists**

* Extra pointer variations.
* Common problems:

  * Copy list with random pointer.
  * Flatten doubly linked list.

---

## ⚡ Handy Tricks

* Always use a **dummy head** to simplify pointer handling.
* **Slow/Fast pointers** → middle node, cycle detection, palindrome.
* **In-place reversal** is a must-master.
* **Heap + divide & conquer** solves k-way merges.
* When in doubt, **draw diagrams** — visualization helps a lot.

---

👉 When you see a linked list problem, ask:

* Is it about **traversal/middle/cycle**? → two pointers.
* Is it about **reversing or reordering**? → reversal patterns.
* Is it about **merging/splitting**? → dummy node + divide & conquer.
* Is it about **numbers in list form**? → digit-wise math.

---

Do you want me to also create a **master cheat sheet** where I line up **Arrays, Strings, Linked Lists, Trees, Graphs, Heaps, Intervals** side by side with their key patterns? That way you’d have one unified reference for all major data structures.

Great one 🔥 — **backtracking** is one of the most powerful and general patterns in algorithms. It’s like a “systematic trial-and-error with pruning” and shows up in recursion-heavy problems.

Here’s the breakdown:

---

## 🔙 Core Backtracking Problem-Solving Patterns

### 1. **Subsets (Power Set)**

* Explore include/exclude choices for each element.
* Common problems:

  * Generate all subsets.
  * Subsets with duplicates.
  * Partition array into equal subsets.

---

### 2. **Permutations**

* Fix elements one by one, swap/mark visited.
* Common problems:

  * Generate all permutations.
  * Permutations with duplicates.
  * Next permutation (lexicographic).

---

### 3. **Combinations**

* Choose `k` out of `n` elements.
* Common problems:

  * Combinations (n choose k).
  * Combination sum (pick numbers that add to target).
  * Phone number letter combinations.

---

### 4. **Constraint Satisfaction (DFS + Pruning)**

* Assign values step by step, backtrack on invalid state.
* Common problems:

  * N-Queens.
  * Sudoku solver.
  * Word search on a grid.

---

### 5. **Partitioning**

* Split string or array into valid groups.
* Common problems:

  * Palindrome partitioning.
  * Word break (string dictionary decomposition).

---

### 6. **Path Finding in Grids (DFS Backtracking)**

* Explore all moves recursively, backtrack if invalid.
* Common problems:

  * Rat in a maze.
  * Unique paths with obstacles.
  * Word search (grid search with visited marking).

---

### 7. **Decision Trees**

* Represent choices as a recursion tree.
* Common problems:

  * Generate parentheses.
  * Expression add operators.
  * Binary string generation with constraints.

---

### 8. **Game Solving**

* Try all possible moves, backtrack.
* Common problems:

  * Tic-Tac-Toe solver.
  * Word ladder with backtracking.
  * Chess/knight’s tour.

---

## ⚡ Techniques & Tricks

* **Pruning** → Cut off branches early if they can’t lead to a solution.
* **State representation** → Use visited sets/arrays, bitmasks.
* **Ordering choices** → Sorting often helps avoid duplicates.
* **Recursive templates**:

```python
def backtrack(path, choices):
    if done(path): 
        result.append(path[:])
        return
    for choice in choices:
        if valid(choice, path):
            path.append(choice)
            backtrack(path, updated_choices)
            path.pop()  # undo choice
```

---

## 🚦 When to Use Backtracking?

Ask:

* Are we generating **all possibilities** (subsets, permutations, partitions)?
* Is the problem about **constraints** (sudoku, N-Queens)?
* Is it a **search problem** in exponential space with pruning?

If yes → backtracking is your tool.

---

Would you like me to also create a **“map” of patterns vs problems** (like: “Sudoku → constraint satisfaction backtracking”, “Combination sum → combinations backtracking”), so you instantly know which template to start from?

Perfect timing 🙌 — **stacks and queues** are fundamental, but their patterns are less obvious than arrays/graphs. Still, most problems around them fall into classic categories. Let’s break them down:

---

## 📚 Stack Problem-Solving Patterns

### 1. **Balanced Parentheses / Validity Checks**

* Push opening chars, pop when matching closing found.
* Common problems:

  * Valid parentheses.
  * Minimum add/remove to make valid.
  * Longest valid parentheses.

---

### 2. **Monotonic Stack (Increasing/Decreasing)**

* Stack maintains order → used for "next greater/smaller" queries.
* Common problems:

  * Next greater element.
  * Daily temperatures.
  * Largest rectangle in histogram.
  * Trapping rain water.

---

### 3. **Expression Evaluation**

* Convert/evaluate expressions using stacks.
* Common problems:

  * Evaluate Reverse Polish Notation (RPN).
  * Infix to postfix conversion.
  * Basic calculator (with +, -, \*, /).

---

### 4. **Backtracking with Stack (Simulation)**

* Simulate undo/redo, DFS traversal, etc.
* Common problems:

  * Simplify path (Unix file path).
  * Decode string like `"3[a2[c]]"`.
  * Iterative DFS tree/graph traversal.

---

### 5. **Stack + Two Pointers Hybrid**

* Sometimes stack is used with pointers for optimal processing.
* Common problems:

  * Remove k digits (greedy with monotonic stack).
  * Minimum insertions to balance parentheses.

---

---

## 📦 Queue Problem-Solving Patterns

### 1. **BFS (Level Order Traversal)**

* Queue is the backbone of BFS.
* Common problems:

  * Binary tree level order.
  * Shortest path in unweighted graph.
  * Rotting oranges (grid BFS).

---

### 2. **Sliding Window with Deque**

* Deque helps maintain max/min efficiently in O(n).
* Common problems:

  * Sliding window maximum.
  * Shortest subarray with sum ≥ k.

---

### 3. **Top-K / Priority Scheduling (via PriorityQueue)**

* Queue extended into priority queue.
* Common problems:

  * Task scheduler.
  * Reorganize string.
  * Kth largest element in stream.

---

### 4. **Producer-Consumer (Simulation)**

* Queue simulates real-world event processing.
* Common problems:

  * Design circular queue.
  * Implement stack using queues / queue using stacks.

---

### 5. **0-1 BFS / Multi-Source BFS**

* For weighted graphs with weights {0,1}, use deque instead of heap.
* Common problems:

  * Shortest path in binary matrix.
  * Minimum operations to transform a number.

---

## ⚡ Handy Tricks

* **Stack**:

  * Use for problems with **reversal, undo, nested structure, "previous/next" element**.
  * **Monotonic stacks** = must-learn for range queries.

* **Queue**:

  * Use for **level-wise processing, FIFO order, streaming problems**.
  * **Deque** = optimized sliding window.

---

👉 Quick “cheat recognition”:

* Nested structure / matching? → **Stack**.
* Next greater/smaller? → **Monotonic Stack**.
* Level-by-level / shortest path? → **Queue (BFS)**.
* Sliding window optimization? → **Deque**.

---

Do you want me to **add Disjoint Set (Union-Find) and Hashing patterns** too, so your cheat sheet covers *all core data structures*?

🔥 Great — **Dynamic Programming (DP)** is one of the most important problem-solving patterns.
It’s tricky at first, but nearly all DP problems fall into **recognizable patterns**.

Here’s a structured breakdown for your cheat sheet:

---

# 🧩 Dynamic Programming Problem-Solving Patterns

---

## 1. **Fibonacci / Linear DP (1D)**

* Transition depends on a few previous states.
* Common problems:

  * Fibonacci sequence.
  * Climbing stairs.
  * House robber (pick or skip).
  * Min cost climbing stairs.

👉 Pattern: `dp[i] = f(dp[i-1], dp[i-2], ...)`

---

## 2. **Knapsack Patterns**

* **0/1 Knapsack**: pick or skip each item.
* **Unbounded Knapsack**: items can be chosen multiple times.
* Common problems:

  * Subset sum.
  * Partition equal subset sum.
  * Coin change (min coins or total ways).
  * Target sum.

👉 Pattern: choose/don’t choose → `dp[i][w]`

---

## 3. **Grid / Matrix DP**

* Move in a grid with constraints (right, down, etc.).
* Common problems:

  * Unique paths.
  * Minimum path sum.
  * Dungeon game.
  * Maximal square.

👉 Pattern: `dp[i][j] = f(dp[i-1][j], dp[i][j-1])`

---

## 4. **Longest Sequence DP**

* Build increasing, decreasing, or common subsequences.
* Common problems:

  * Longest increasing subsequence (LIS).
  * Longest common subsequence (LCS).
  * Longest palindromic subsequence.
  * Edit distance (Levenshtein).

👉 Pattern: `dp[i][j] = f(dp[i-1][j-1], dp[i-1][j], dp[i][j-1])`

---

## 5. **Interval DP**

* Solve problems on subarrays/substrings by splitting them.
* Common problems:

  * Matrix chain multiplication.
  * Burst balloons.
  * Palindrome partitioning.
  * Minimum score triangulation.

👉 Pattern: `dp[l][r] = min/max over partition (dp[l][k] + dp[k+1][r])`

---

## 6. **Bitmask DP**

* State compression using bitmasks for subsets.
* Common problems:

  * Traveling salesman problem (TSP).
  * Minimum cost to connect cities.
  * Count ways to assign tasks.

👉 Pattern: `dp[mask] = f(dp[mask without i])`

---

## 7. **DP on Trees / Graphs**

* DFS + memoization on nodes.
* Common problems:

  * Diameter of tree.
  * Maximum path sum.
  * Count independent sets.
  * Number of ways to color a tree.

👉 Pattern: `dp[node] = combine(dp[children])`

---

## 8. **Game Theory DP (Minimax / Grundy numbers)**

* Turn-based games, each move affects opponent’s state.
* Common problems:

  * Stone game.
  * Nim game variations.
  * Predict the winner.

👉 Pattern: `dp[state] = best move vs opponent`

---

## 9. **Digit DP**

* Counting numbers with digit constraints.
* Common problems:

  * Count numbers with certain digits.
  * Sum of digits in a range.
  * No consecutive ones in binary representation.

👉 Pattern: `dp[pos][tight][state]`

---

## 10. **Probability / Expectation DP**

* Expected value of games or outcomes.
* Common problems:

  * Dice rolls (probability of sum).
  * Random walks.
  * Expected steps in Markov process.

👉 Pattern: `dp[state] = weighted sum of next states`

---

## 11. **Memory Optimization Tricks**

* Many DP problems only need the **previous row/column** → reduce space.
* Rolling array: `dp[i % 2][...]`
* Example:

  * Fibonacci → O(1) memory.
  * Unique paths → O(n) memory.

---

# ⚡ How to Recognize a DP Problem

1. **Overlapping subproblems** (same computation repeats).
2. **Optimal substructure** (solution built from smaller solutions).
3. Keywords: “minimum/maximum”, “count ways”, “longest”, “shortest”.

---

👉 Quick Mapping:

* Counting ways? → Knapsack / Grid DP.
* Min/max value? → Knapsack / Interval DP.
* Sequence alignment? → LCS family.
* Subset optimization? → Bitmask DP.
* Graph/tree? → DP on Trees/Graphs.
* Digits/range? → Digit DP.

---

Do you want me to also create a **big unified mindmap/flowchart of all these patterns** (arrays, trees, heaps, graphs, strings, intervals, linked lists, backtracking, stacks/queues, DP) so you can visually recognize problems instantly?
