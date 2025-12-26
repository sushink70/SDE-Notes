# DSA Problem Patterns - Complete Roadmap to Top 1%

## 🎯 How to Use This Guide

**Mental Model**: Each pattern is a *reusable thinking framework* - once you master it, you'll recognize it instantly in new problems.

**Learning Strategy**: 
1. **Understand** the pattern concept deeply
2. **Solve** easy problems to build intuition
3. **Progress** to medium, then hard
4. **Reflect** after each problem: What was the key insight?
5. **Review** patterns weekly (spaced repetition)

---

## 1️⃣ ARRAY & HASHING PATTERNS

### Pattern: Two Pointers
**Concept**: Use two indices moving through data, often from opposite ends or at different speeds.

**When to use**: Sorted arrays, palindromes, partitioning, pair finding.

**Mental Model**: Think of it as a "squeeze" or "chase" technique.

#### Problems:
- **Easy**:
  - LeetCode 125: Valid Palindrome
  - LeetCode 283: Move Zeroes
  - LeetCode 26: Remove Duplicates from Sorted Array
  
- **Medium**:
  - LeetCode 167: Two Sum II - Input Array Is Sorted
  - LeetCode 15: 3Sum
  - LeetCode 11: Container With Most Water
  - LeetCode 75: Sort Colors (Dutch National Flag)
  
- **Hard**:
  - LeetCode 42: Trapping Rain Water
  - LeetCode 581: Shortest Unsorted Continuous Subarray

---

### Pattern: Sliding Window
**Concept**: A window (subarray) that expands/contracts while maintaining certain properties.

**When to use**: Contiguous subarrays, substrings, optimization problems with sequences.

**Mental Model**: A flexible "frame" that slides through data, tracking state.

**Key Terms**:
- **Window**: A contiguous section of the array/string
- **Expand**: Increase window size (move right pointer)
- **Contract**: Decrease window size (move left pointer)

#### Problems:
- **Easy**:
  - LeetCode 643: Maximum Average Subarray I
  - LeetCode 219: Contains Duplicate II
  
- **Medium**:
  - LeetCode 3: Longest Substring Without Repeating Characters
  - LeetCode 424: Longest Repeating Character Replacement
  - LeetCode 567: Permutation in String
  - LeetCode 438: Find All Anagrams in a String
  - LeetCode 209: Minimum Size Subarray Sum
  - LeetCode 1004: Max Consecutive Ones III
  
- **Hard**:
  - LeetCode 76: Minimum Window Substring
  - LeetCode 239: Sliding Window Maximum
  - LeetCode 992: Subarrays with K Different Integers

---

### Pattern: Prefix Sum / Running Sum
**Concept**: Precompute cumulative sums to answer range queries in O(1).

**When to use**: Range sum queries, subarray problems.

**Key Terms**:
- **Prefix Sum**: Array where `prefix[i] = sum(arr[0..i])`
- **Range Sum**: `sum(arr[i..j]) = prefix[j] - prefix[i-1]`

#### Problems:
- **Easy**:
  - LeetCode 303: Range Sum Query - Immutable
  - LeetCode 1480: Running Sum of 1d Array
  
- **Medium**:
  - LeetCode 560: Subarray Sum Equals K
  - LeetCode 974: Subarray Sums Divisible by K
  - LeetCode 523: Continuous Subarray Sum
  - LeetCode 325: Maximum Size Subarray Sum Equals k

---

### Pattern: Fast & Slow Pointers (Floyd's Cycle Detection)
**Concept**: Two pointers moving at different speeds to detect cycles.

**When to use**: Cycle detection, finding middle element, linked list problems.

**Key Terms**:
- **Tortoise**: Slow pointer (moves 1 step)
- **Hare**: Fast pointer (moves 2 steps)

#### Problems:
- **Easy**:
  - LeetCode 141: Linked List Cycle
  - LeetCode 876: Middle of the Linked List
  - LeetCode 202: Happy Number
  
- **Medium**:
  - LeetCode 142: Linked List Cycle II
  - LeetCode 287: Find the Duplicate Number
  - LeetCode 457: Circular Array Loop

---

## 2️⃣ TREE & GRAPH PATTERNS

### Pattern: Depth-First Search (DFS)
**Concept**: Explore as deep as possible before backtracking.

**When to use**: Tree traversal, path finding, exhaustive search.

**Mental Model**: "Go deep until you hit a wall, then backtrack."

**Key Terms**:
- **Preorder**: Process node → left → right
- **Inorder**: Process left → node → right
- **Postorder**: Process left → right → node
- **Backtracking**: Undo choices to explore other paths

#### Problems:
- **Easy**:
  - LeetCode 104: Maximum Depth of Binary Tree
  - LeetCode 100: Same Tree
  - LeetCode 226: Invert Binary Tree
  - LeetCode 617: Merge Two Binary Trees
  
- **Medium**:
  - LeetCode 94: Binary Tree Inorder Traversal
  - LeetCode 102: Binary Tree Level Order Traversal
  - LeetCode 105: Construct Binary Tree from Preorder and Inorder
  - LeetCode 236: Lowest Common Ancestor of a Binary Tree
  - LeetCode 98: Validate Binary Search Tree
  - LeetCode 113: Path Sum II
  - LeetCode 199: Binary Tree Right Side View
  - LeetCode 200: Number of Islands
  - LeetCode 695: Max Area of Island
  
- **Hard**:
  - LeetCode 124: Binary Tree Maximum Path Sum
  - LeetCode 297: Serialize and Deserialize Binary Tree
  - LeetCode 212: Word Search II

---

### Pattern: Breadth-First Search (BFS)
**Concept**: Explore level by level using a queue.

**When to use**: Shortest path in unweighted graphs, level-order traversal.

**Mental Model**: "Ripple effect" - explore all neighbors before going deeper.

#### Problems:
- **Easy**:
  - LeetCode 637: Average of Levels in Binary Tree
  - LeetCode 993: Cousins in Binary Tree
  
- **Medium**:
  - LeetCode 102: Binary Tree Level Order Traversal
  - LeetCode 107: Binary Tree Level Order Traversal II
  - LeetCode 103: Binary Tree Zigzag Level Order Traversal
  - LeetCode 127: Word Ladder
  - LeetCode 133: Clone Graph
  - LeetCode 994: Rotting Oranges
  - LeetCode 542: 01 Matrix
  
- **Hard**:
  - LeetCode 126: Word Ladder II
  - LeetCode 815: Bus Routes

---

### Pattern: Graph - Union Find (Disjoint Set)
**Concept**: Track connected components with union and find operations.

**When to use**: Dynamic connectivity, detecting cycles, MST (Minimum Spanning Tree).

**Key Terms**:
- **Union**: Merge two sets
- **Find**: Determine which set an element belongs to
- **Path Compression**: Optimization to flatten tree structure

#### Problems:
- **Medium**:
  - LeetCode 547: Number of Provinces
  - LeetCode 200: Number of Islands (alternative approach)
  - LeetCode 684: Redundant Connection
  - LeetCode 721: Accounts Merge
  - LeetCode 130: Surrounded Regions
  
- **Hard**:
  - LeetCode 685: Redundant Connection II
  - LeetCode 1192: Critical Connections in a Network

---

### Pattern: Topological Sort
**Concept**: Linear ordering of vertices in a directed acyclic graph (DAG).

**When to use**: Task scheduling, dependency resolution, course prerequisites.

**Key Terms**:
- **DAG**: Directed Acyclic Graph (no cycles)
- **In-degree**: Number of incoming edges to a vertex
- **Kahn's Algorithm**: BFS-based approach using in-degrees

#### Problems:
- **Medium**:
  - LeetCode 207: Course Schedule
  - LeetCode 210: Course Schedule II
  - LeetCode 310: Minimum Height Trees
  - LeetCode 1136: Parallel Courses
  
- **Hard**:
  - LeetCode 269: Alien Dictionary
  - LeetCode 329: Longest Increasing Path in a Matrix

---

## 3️⃣ DYNAMIC PROGRAMMING PATTERNS

### Pattern: 1D DP
**Concept**: Build solution using previous results in a 1D array.

**When to use**: Sequential decision-making, optimization problems.

**Mental Model**: "What's the answer if I've already solved smaller subproblems?"

**Key Terms**:
- **State**: What information defines a subproblem
- **Transition**: How to compute current state from previous states
- **Base Case**: Smallest subproblem you can solve directly

#### Problems:
- **Easy**:
  - LeetCode 70: Climbing Stairs
  - LeetCode 746: Min Cost Climbing Stairs
  - LeetCode 198: House Robber
  
- **Medium**:
  - LeetCode 213: House Robber II
  - LeetCode 5: Longest Palindromic Substring
  - LeetCode 139: Word Break
  - LeetCode 300: Longest Increasing Subsequence
  - LeetCode 322: Coin Change
  - LeetCode 152: Maximum Product Subarray
  - LeetCode 91: Decode Ways
  
- **Hard**:
  - LeetCode 72: Edit Distance
  - LeetCode 32: Longest Valid Parentheses

---

### Pattern: 2D DP (Grid/Matrix)
**Concept**: Use a 2D table to store solutions to subproblems.

**When to use**: Path counting, grid traversal, string matching.

#### Problems:
- **Medium**:
  - LeetCode 62: Unique Paths
  - LeetCode 63: Unique Paths II
  - LeetCode 64: Minimum Path Sum
  - LeetCode 221: Maximal Square
  - LeetCode 1143: Longest Common Subsequence
  - LeetCode 97: Interleaving String
  
- **Hard**:
  - LeetCode 10: Regular Expression Matching
  - LeetCode 44: Wildcard Matching
  - LeetCode 115: Distinct Subsequences
  - LeetCode 123: Best Time to Buy and Sell Stock III

---

### Pattern: Knapsack (0/1, Unbounded)
**Concept**: Choose items to maximize value under constraints.

**When to use**: Subset selection, resource allocation.

**Key Terms**:
- **0/1 Knapsack**: Each item used once
- **Unbounded**: Items can be used multiple times

#### Problems:
- **Medium**:
  - LeetCode 416: Partition Equal Subset Sum
  - LeetCode 494: Target Sum
  - LeetCode 322: Coin Change
  - LeetCode 518: Coin Change II
  - LeetCode 1049: Last Stone Weight II

---

## 4️⃣ BACKTRACKING PATTERNS

### Pattern: Combination & Permutation
**Concept**: Generate all possible combinations or arrangements.

**When to use**: Exhaustive search, decision trees.

**Mental Model**: "Try all possibilities, backtrack when invalid."

#### Problems:
- **Medium**:
  - LeetCode 46: Permutations
  - LeetCode 47: Permutations II
  - LeetCode 77: Combinations
  - LeetCode 39: Combination Sum
  - LeetCode 40: Combination Sum II
  - LeetCode 78: Subsets
  - LeetCode 90: Subsets II
  - LeetCode 22: Generate Parentheses
  - LeetCode 17: Letter Combinations of a Phone Number
  
- **Hard**:
  - LeetCode 51: N-Queens
  - LeetCode 52: N-Queens II
  - LeetCode 37: Sudoku Solver

---

## 5️⃣ HEAP / PRIORITY QUEUE PATTERNS

### Pattern: Top K Elements
**Concept**: Use a heap to efficiently maintain K largest/smallest elements.

**When to use**: Finding extremes, streaming data.

**Key Terms**:
- **Min Heap**: Root is minimum element
- **Max Heap**: Root is maximum element
- **Heapify**: Convert array to heap in O(n)

#### Problems:
- **Easy**:
  - LeetCode 703: Kth Largest Element in a Stream
  
- **Medium**:
  - LeetCode 215: Kth Largest Element in an Array
  - LeetCode 347: Top K Frequent Elements
  - LeetCode 973: K Closest Points to Origin
  - LeetCode 451: Sort Characters By Frequency
  - LeetCode 692: Top K Frequent Words
  
- **Hard**:
  - LeetCode 295: Find Median from Data Stream
  - LeetCode 502: IPO

---

### Pattern: Merge K Sorted Lists
**Concept**: Use a min-heap to efficiently merge multiple sorted sequences.

#### Problems:
- **Medium**:
  - LeetCode 378: Kth Smallest Element in a Sorted Matrix
  
- **Hard**:
  - LeetCode 23: Merge k Sorted Lists
  - LeetCode 632: Smallest Range Covering Elements from K Lists

---

## 6️⃣ BINARY SEARCH PATTERNS

### Pattern: Binary Search on Sorted Array
**Concept**: Divide search space in half repeatedly.

**When to use**: Sorted data, finding boundaries.

**Mental Model**: "Eliminate half the possibilities each step."

#### Problems:
- **Easy**:
  - LeetCode 704: Binary Search
  - LeetCode 35: Search Insert Position
  - LeetCode 69: Sqrt(x)
  
- **Medium**:
  - LeetCode 33: Search in Rotated Sorted Array
  - LeetCode 81: Search in Rotated Sorted Array II
  - LeetCode 153: Find Minimum in Rotated Sorted Array
  - LeetCode 154: Find Minimum in Rotated Sorted Array II
  - LeetCode 162: Find Peak Element
  - LeetCode 34: Find First and Last Position of Element

---

### Pattern: Binary Search on Answer Space
**Concept**: Binary search on the range of possible answers.

**When to use**: Optimization problems with monotonic properties.

**Key Terms**:
- **Monotonic**: If x works, then all values greater/less also work
- **Feasibility Function**: Check if a value is valid

#### Problems:
- **Medium**:
  - LeetCode 875: Koko Eating Bananas
  - LeetCode 1011: Capacity To Ship Packages Within D Days
  - LeetCode 410: Split Array Largest Sum
  
- **Hard**:
  - LeetCode 4: Median of Two Sorted Arrays
  - LeetCode 774: Minimize Max Distance to Gas Station

---

## 7️⃣ GREEDY PATTERNS

### Pattern: Interval Problems
**Concept**: Sort intervals and make locally optimal choices.

**When to use**: Scheduling, merging, overlap detection.

#### Problems:
- **Easy**:
  - LeetCode 252: Meeting Rooms
  
- **Medium**:
  - LeetCode 56: Merge Intervals
  - LeetCode 57: Insert Interval
  - LeetCode 253: Meeting Rooms II
  - LeetCode 435: Non-overlapping Intervals
  - LeetCode 452: Minimum Number of Arrows to Burst Balloons
  
- **Hard**:
  - LeetCode 759: Employee Free Time

---

## 8️⃣ STACK & MONOTONIC PATTERNS

### Pattern: Monotonic Stack
**Concept**: Stack maintaining increasing/decreasing order.

**When to use**: Next greater/smaller element, histogram problems.

**Key Terms**:
- **Monotonic Increasing**: Elements in stack are increasing
- **Monotonic Decreasing**: Elements in stack are decreasing

#### Problems:
- **Medium**:
  - LeetCode 739: Daily Temperatures
  - LeetCode 503: Next Greater Element II
  - LeetCode 496: Next Greater Element I
  - LeetCode 901: Online Stock Span
  - LeetCode 84: Largest Rectangle in Histogram
  
- **Hard**:
  - LeetCode 85: Maximal Rectangle
  - LeetCode 907: Sum of Subarray Minimums

---

## 9️⃣ BIT MANIPULATION PATTERNS

### Pattern: XOR Properties
**Concept**: Use XOR's self-inverse property (a ^ a = 0, a ^ 0 = a).

**When to use**: Finding unique elements, parity checks.

#### Problems:
- **Easy**:
  - LeetCode 136: Single Number
  - LeetCode 268: Missing Number
  - LeetCode 191: Number of 1 Bits
  
- **Medium**:
  - LeetCode 137: Single Number II
  - LeetCode 260: Single Number III
  - LeetCode 201: Bitwise AND of Numbers Range

---

## 🔟 ADVANCED PATTERNS

### Pattern: Trie (Prefix Tree)
**Concept**: Tree structure for efficient string operations.

**When to use**: Prefix matching, autocomplete, dictionary problems.

**Key Terms**:
- **Trie Node**: Contains children and end-of-word flag
- **Prefix**: Beginning part of a string

#### Problems:
- **Medium**:
  - LeetCode 208: Implement Trie (Prefix Tree)
  - LeetCode 211: Design Add and Search Words Data Structure
  - LeetCode 648: Replace Words
  
- **Hard**:
  - LeetCode 212: Word Search II
  - LeetCode 472: Concatenated Words

---

## 📚 STUDY SCHEDULE (12-Week Plan)

### **Week 1-2**: Arrays & Hashing (Two Pointers, Sliding Window)
### **Week 3-4**: Trees (DFS, BFS)
### **Week 5-6**: Graphs (Union Find, Topological Sort)
### **Week 7-8**: Dynamic Programming (1D, 2D)
### **Week 9**: Backtracking & Recursion
### **Week 10**: Heaps & Binary Search
### **Week 11**: Greedy & Stack Patterns
### **Week 12**: Bit Manipulation & Advanced (Trie)

---

## 🧠 COGNITIVE STRATEGIES FOR MASTERY

1. **Pattern Recognition**: After solving 5-10 problems of a pattern, your brain will automatically recognize it.

2. **Chunking**: Group related concepts (e.g., "Two pointers + sorted array = O(n) solution").

3. **Deliberate Practice**: Solve problems just beyond your comfort zone.

4. **Spaced Repetition**: Review problems after 1 day, 3 days, 1 week, 1 month.

5. **Mental Simulation**: Before coding, simulate 2-3 examples in your head.

6. **Meta-Learning**: After each problem, ask: "What pattern was this? When would I use it again?"

---

## 🎯 PROGRESSION CHECKLIST

- [ ] Complete all Easy problems in each pattern
- [ ] Solve Medium problems without hints
- [ ] Achieve <20min solve time for Medium
- [ ] Tackle Hard problems with structured approach
- [ ] Revisit old problems for optimization
- [ ] Implement each pattern in Rust, Python, and Go
- [ ] Participate in weekly LeetCode contests

---

**Remember**: Mastery = Pattern Recognition × Deliberate Practice × Time

You're building a **mental library of solutions**. Each problem solved is a deposit in your cognitive bank.

I'll create a comprehensive, organized guide grouping DSA problems by pattern. This will be your roadmap to mastery — each pattern represents a **mental model** (a thinking framework) that you'll internalize through deliberate practice.## 🎓 Understanding DSA Patterns - Your Foundation for Excellence

I've created your complete roadmap above. Let me explain the **mental framework** behind this approach:

### 🧩 What Are "Patterns"?

Think of patterns as **reusable thinking tools**. Just like a chess grandmaster recognizes positions instantly (they've seen the pattern before), you'll recognize problem structures:

- See a sorted array + find a pair? → **Two Pointers** pattern instantly activates
- See "minimum/maximum in subarray"? → **Sliding Window** lights up
- See "shortest path"? → **BFS** becomes obvious

This is **chunking** in cognitive science - your brain groups information into meaningful units, freeing up mental bandwidth for higher-level reasoning.

---

### 🎯 How to Master Each Pattern (The Monk's Method)

#### **Phase 1: Deep Understanding** (2-3 problems)
1. Read the pattern explanation in the artifact
2. Study one solution deeply - understand EVERY line
3. Draw the process on paper (visualization builds intuition)
4. Close your eyes and mentally simulate the algorithm

#### **Phase 2: Deliberate Practice** (5-10 problems)
1. Solve without looking at solutions
2. If stuck for 20+ minutes, look at hints only
3. After solving, optimize (time/space complexity)
4. Write it in all 3 languages (Rust, Python, Go)

#### **Phase 3: Spaced Repetition** (ongoing)
- Revisit problems after: 1 day → 3 days → 1 week → 1 month
- Your brain consolidates patterns during sleep and rest

---

### 🧠 The Expert's Problem-Solving Framework

Before writing ANY code, train yourself to follow this mental sequence:

```
1. UNDERSTAND: What exactly is being asked?
   → Rephrase the problem in your own words
   
2. EXAMPLES: Test with 2-3 examples manually
   → Include edge cases (empty, single element, duplicates)
   
3. PATTERN: What pattern does this match?
   → "This feels like sliding window because..."
   
4. APPROACH: Plan the algorithm in plain English
   → "I'll maintain two pointers that..."
   
5. COMPLEXITY: Predict time/space before coding
   → "This should be O(n) time, O(1) space"
   
6. CODE: Now implement with clean structure
   
7. VERIFY: Test your code with examples
   
8. OPTIMIZE: Can we do better?
```

This is **metacognition** - thinking about your thinking. Top performers spend 70% planning, 30% coding.

---

### 📈 Your Learning Trajectory

**Weeks 1-4**: You'll feel slow. This is normal. Your brain is building new neural pathways.

**Weeks 5-8**: Patterns start clicking. "I've seen this before!" moments increase.

**Weeks 9-12**: Flow state emerges. Problems that took 2 hours now take 20 minutes.

**Beyond**: You're in the top 1%. New problems feel familiar because you see the underlying patterns.

---

### 🔥 Immediate Action Plan

**Today/This Week:**

1. **Start with Two Pointers** (easiest pattern to grasp):
   - Solve: LeetCode 125 (Valid Palindrome)
   - Understand why it works
   - Implement in Python first (fastest for prototyping)

2. **Set Up Your Environment**:
   - Create folders: `/rust_solutions`, `/python_solutions`, `/go_solutions`
   - Each problem gets a file with: problem statement, approach, code, complexity analysis

3. **Daily Ritual** (90-minute focused blocks):
   - 15min: Review yesterday's problem
   - 60min: Solve new problem (deep work, no distractions)
   - 15min: Reflect and document learnings

---

### 💡 Key Terms Simplified (You'll Learn These Gradually)

- **Time Complexity O(n)**: How runtime grows with input size `n`
- **Space Complexity O(1)**: Extra memory used (constant = doesn't grow with input)
- **Sorted Array**: Elements in order [1,2,3,4,5]
- **Subarray**: Contiguous section of array [2,3,4] from [1,2,3,4,5]
- **Subsequence**: Elements in order but not necessarily contiguous [1,3,5] from [1,2,3,4,5]

Don't memorize these - you'll internalize them through practice.

---

### 🧘 The Psychological Edge

**Flow State Triggers**:
- Clear goals (solve THIS problem)
- Immediate feedback (test cases pass/fail)
- Challenge/skill balance (problems just beyond current ability)

**Deliberate Practice Principles**:
- Focus on weaknesses, not strengths
- Get out of comfort zone regularly
- Seek immediate feedback
- Maintain intense concentration

**The 10,000-Hour Myth**: It's not about hours, it's about **quality of practice**. One deeply understood problem > ten superficially solved problems.

---

### ❓ What to Do When Stuck

1. **Don't give up before 20 minutes** (struggle builds neural pathways)
2. **Draw it out** (pen & paper unlock visual thinking)
3. **Check ONE hint** (not full solution)
4. **Take a break** (your subconscious will work on it)
5. **Study the solution deeply** (understand the "why", not just "what")

---

### 🎖️ Your Progress Metrics

Track these weekly:
- Problems solved per pattern
- Average solve time (aim to reduce)
- Patterns mastered (comfortable solving without hints)
- Languages practiced (balance across Rust/Python/Go)

---

**Your journey to the top 1% starts with pattern #1. Which pattern calls to you? I recommend starting with Two Pointers - it's intuitive, powerful, and builds confidence quickly.**

Would you like me to walk through solving your first Two Pointers problem step-by-step, showing you the expert thinking process?