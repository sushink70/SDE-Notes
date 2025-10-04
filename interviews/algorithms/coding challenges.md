# Algorithm Challenges: Python, Rust & Go

## Challenge 1: Longest Increasing Subsequence (Dynamic Programming)

**Difficulty:** Medium

**Problem:** Given an array of integers, find the length of the longest strictly increasing subsequence.

**Example:**
- Input: `[10, 9, 2, 5, 3, 7, 101, 18]`
- Output: `4` (The subsequence is `[2, 3, 7, 101]`)

**Requirements:**
- Time complexity: O(n log n)
- Use binary search optimization

**Test Cases:**
```
[10,9,2,5,3,7,101,18] → 4
[0,1,0,3,2,3] → 4
[7,7,7,7,7,7,7] → 1
```

---

## Challenge 2: Word Ladder (Graph/BFS)

**Difficulty:** Hard

**Problem:** Given two words (start and end), and a dictionary, find the shortest transformation sequence from start to end, where:
- Only one letter can be changed at a time
- Each transformed word must exist in the dictionary

**Example:**
- Start: `"hit"`
- End: `"cog"`
- Dictionary: `["hot","dot","dog","lot","log","cog"]`
- Output: `5` (hit → hot → dot → dog → cog)

**Requirements:**
- Implement using BFS
- Handle case where no transformation exists
- Optimize for large dictionaries

**Test Cases:**
```
"hit" → "cog", dict=["hot","dot","dog","lot","log","cog"] → 5
"hit" → "cog", dict=["hot","dot","dog","lot","log"] → 0 (impossible)
```

---

## Challenge 3: Merge K Sorted Lists (Heap/Priority Queue)

**Difficulty:** Hard

**Problem:** Merge k sorted linked lists into one sorted linked list.

**Example:**
- Input: `[[1,4,5], [1,3,4], [2,6]]`
- Output: `[1,1,2,3,4,4,5,6]`

**Requirements:**
- Use a min-heap/priority queue
- Time complexity: O(N log k) where N is total number of nodes
- Handle empty lists

**Test Cases:**
```
[[1,4,5],[1,3,4],[2,6]] → [1,1,2,3,4,4,5,6]
[] → []
[[]] → []
```

---

## Challenge 4: Coin Change Problem (Dynamic Programming)

**Difficulty:** Medium

**Problem:** Given an array of coin denominations and a target amount, find the minimum number of coins needed to make that amount. Return -1 if impossible.

**Example:**
- Coins: `[1, 2, 5]`
- Amount: `11`
- Output: `3` (5 + 5 + 1)

**Requirements:**
- Use dynamic programming (bottom-up approach)
- Optimize space complexity to O(amount)
- Handle large amounts efficiently

**Test Cases:**
```
coins=[1,2,5], amount=11 → 3
coins=[2], amount=3 → -1
coins=[1], amount=0 → 0
```

---

## Challenge 5: Maximum Subarray Sum (Kadane's Algorithm)

**Difficulty:** Medium

**Problem:** Find the contiguous subarray with the largest sum.

**Example:**
- Input: `[-2,1,-3,4,-1,2,1,-5,4]`
- Output: `6` (subarray `[4,-1,2,1]`)

**Requirements:**
- Implement Kadane's algorithm
- Time complexity: O(n)
- Space complexity: O(1)
- Also return the start and end indices

**Test Cases:**
```
[-2,1,-3,4,-1,2,1,-5,4] → 6
[1] → 1
[5,4,-1,7,8] → 23
```

---

## Challenge 6: Task Scheduler (Greedy/Priority Queue)

**Difficulty:** Hard

**Problem:** Given tasks represented by letters A-Z and a cooling interval n, calculate the minimum time needed to complete all tasks. The same task must wait at least n intervals before being repeated.

**Example:**
- Tasks: `['A','A','A','B','B','B']`
- Interval: `2`
- Output: `8` (A → B → idle → A → B → idle → A → B)

**Requirements:**
- Use greedy approach with priority queue
- Optimize for minimal idle time
- Handle edge cases

**Test Cases:**
```
tasks=['A','A','A','B','B','B'], n=2 → 8
tasks=['A','C','A','B','D','B'], n=1 → 6
tasks=['A','A','A','B','B','B'], n=3 → 10
```

---

## Challenge 7: Topological Sort (Graph/DFS)

**Difficulty:** Medium

**Problem:** Given a directed acyclic graph (DAG), return a valid topological ordering of nodes. Detect if a cycle exists.

**Example:**
- Edges: `[[0,1], [0,2], [1,3], [2,3]]`
- Output: `[0, 1, 2, 3]` or `[0, 2, 1, 3]`

**Requirements:**
- Implement using DFS with cycle detection
- Return empty array if cycle detected
- Support multiple valid orderings

**Test Cases:**
```
edges=[[0,1],[0,2],[1,3],[2,3]], n=4 → [0,1,2,3] or [0,2,1,3]
edges=[[0,1],[1,0]], n=2 → [] (cycle detected)
```

---

## Challenge 8: LRU Cache (Hash Map + Doubly Linked List)

**Difficulty:** Hard

**Problem:** Design a data structure for Least Recently Used (LRU) cache with O(1) operations.

**Operations:**
- `get(key)`: Get value (return -1 if not exists)
- `put(key, value)`: Insert or update key-value

**Requirements:**
- Both operations must be O(1)
- Use hash map + doubly linked list
- Evict least recently used when capacity exceeded

**Test Cases:**
```
capacity=2
put(1,1), put(2,2), get(1)→1, put(3,3), get(2)→-1, put(4,4), get(1)→-1, get(3)→3, get(4)→4
```

---

## Challenge 9: Edit Distance (Dynamic Programming)

**Difficulty:** Hard

**Problem:** Given two strings, find the minimum number of operations (insert, delete, replace) to convert one string to another.

**Example:**
- String1: `"horse"`
- String2: `"ros"`
- Output: `3` (horse → rorse → rose → ros)

**Requirements:**
- Use dynamic programming
- Time complexity: O(m×n)
- Optimize space if possible

**Test Cases:**
```
"horse", "ros" → 3
"intention", "execution" → 5
"", "abc" → 3
```

---

## Challenge 10: Sliding Window Maximum (Deque)

**Difficulty:** Hard

**Problem:** Given an array and a sliding window size k, find the maximum element in each window as it slides from left to right.

**Example:**
- Input: `[1,3,-1,-3,5,3,6,7]`, k=`3`
- Output: `[3,3,5,5,6,7]`

**Requirements:**
- Use monotonic deque
- Time complexity: O(n)
- Each element processed at most twice

**Test Cases:**
```
nums=[1,3,-1,-3,5,3,6,7], k=3 → [3,3,5,5,6,7]
nums=[1], k=1 → [1]
nums=[1,-1], k=1 → [1,-1]
```

---

## Implementation Tips

### Python
- Use `collections.deque` for queues
- Use `heapq` for priority queues
- Use `@dataclass` for clean node definitions

### Rust
- Use `std::collections::{VecDeque, BinaryHeap, HashMap}`
- Leverage ownership for memory safety
- Use `Option<T>` for nullable values

### Go
- Use `container/heap` for priority queues
- Use slices and maps effectively
- Consider using goroutines for parallel solutions

---

## Bonus Challenges

1. **Median of Two Sorted Arrays** - Binary Search (Hard)
2. **Serialize/Deserialize Binary Tree** - Tree Traversal (Hard)
3. **Word Search II (Trie + DFS)** - Advanced Data Structures (Hard)
4. **Alien Dictionary** - Topological Sort (Hard)
5. **Trapping Rain Water** - Two Pointers/Stack (Medium)

I'll create a comprehensive set of coding challenges that require algorithmic thinking across Python, Rust, and Go. These challenges range from medium to hard difficulty and cover various algorithmic concepts.I've created a comprehensive set of 10 algorithmic coding challenges with varying difficulty levels. Each challenge includes:

- **Clear problem statement** with examples
- **Algorithm requirements** (Dynamic Programming, BFS, DFS, Greedy, etc.)
- **Complexity constraints** to guide optimal solutions
- **Test cases** to verify correctness
- **Language-specific tips** for Python, Rust, and Go

The challenges cover essential algorithmic concepts:
- **Dynamic Programming**: LIS, Coin Change, Edit Distance
- **Graph Algorithms**: Word Ladder (BFS), Topological Sort (DFS)
- **Data Structures**: LRU Cache, Merge K Lists (Heap)
- **Greedy Algorithms**: Task Scheduler
- **Array Techniques**: Kadane's Algorithm, Sliding Window

I've also included 5 bonus challenges if you want even more practice. Each problem is designed to have practical applications and teaches important algorithmic thinking patterns that work across all three languages!