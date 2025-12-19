# Constraint Design Patterns: LeetCode Problem-Solving Focus

## Mental Framework: Constraints in Competitive Programming

In LeetCode problems, **constraints** are the *given limitations* that define valid inputs and guide your solution strategy. Understanding and leveraging constraints is what separates top 1% solutions from average ones.

**Key Insight**: Every constraint is a *hint* about the optimal algorithm. Learn to decode them instantly.

---

## Core Constraint Categories in LeetCode

### 1. **Size Constraints** → Algorithm Complexity
### 2. **Value Range Constraints** → Data Structure Choice  
### 3. **Ordering Constraints** → Preprocessing Opportunities
### 4. **Uniqueness Constraints** → Hash-based Solutions
### 5. **Structural Constraints** → Problem-specific optimizations

---

# Deep Dive: Constraint Pattern Recognition

## **Pattern 1: Size Constraints → Time Complexity**

### The Complexity Decision Tree

```
n ≤ 10        → O(n!), O(n^7)    [Brute force everything]
n ≤ 20        → O(2^n)           [Bitmask DP, backtracking]
n ≤ 100       → O(n^4)           [4D DP]
n ≤ 500       → O(n^3)           [Floyd-Warshall, 3D DP]
n ≤ 3000      → O(n^2)           [2D DP, nested loops]
n ≤ 10^5      → O(n log n)       [Sorting, heap, segment tree]
n ≤ 10^6      → O(n)             [Hash maps, two pointers, prefix sums]
n ≤ 10^8      → O(log n) or O(1) [Binary search, math formulas]
```

### Example Problem: Two Sum Variants

**Constraint Analysis Workflow:**

```python
# Problem: Two Sum
# Constraint: 2 ≤ nums.length ≤ 10^4
# Decode: n ≤ 10^4 → O(n) or O(n log n) required

# ❌ WRONG: O(n²) - Too slow for n=10^4
def two_sum_brute(nums: list[int], target: int) -> list[int]:
    n = len(nums)
    for i in range(n):
        for j in range(i + 1, n):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []

# ✅ CORRECT: O(n) using hash map
def two_sum_optimal(nums: list[int], target: int) -> list[int]:
    seen = {}  # value -> index
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []
```

**Rust Implementation (Zero-Cost Abstractions):**

```rust
use std::collections::HashMap;

pub fn two_sum(nums: Vec<i32>, target: i32) -> Vec<i32> {
    let mut seen: HashMap<i32, usize> = HashMap::with_capacity(nums.len());
    
    for (i, &num) in nums.iter().enumerate() {
        let complement = target - num;
        
        if let Some(&j) = seen.get(&complement) {
            return vec![j as i32, i as i32];
        }
        
        seen.insert(num, i);
    }
    
    vec![] // Guaranteed not to reach here per problem constraints
}

// Performance optimization: pre-allocate HashMap capacity
```

**Go Implementation (Explicit Error Handling):**

```go
func twoSum(nums []int, target int) []int {
    seen := make(map[int]int, len(nums)) // Pre-allocate capacity
    
    for i, num := range nums {
        complement := target - num
        if j, exists := seen[complement]; exists {
            return []int{j, i}
        }
        seen[num] = i
    }
    
    return nil // Per constraints, solution always exists
}
```

**C++ Implementation (Performance-Critical):**

```cpp
#include <vector>
#include <unordered_map>

class Solution {
public:
    std::vector<int> twoSum(std::vector<int>& nums, int target) {
        std::unordered_map<int, int> seen;
        seen.reserve(nums.size()); // Pre-allocate to avoid rehashing
        
        for (int i = 0; i < nums.size(); ++i) {
            int complement = target - nums[i];
            
            auto it = seen.find(complement);
            if (it != seen.end()) {
                return {it->second, i};
            }
            
            seen[nums[i]] = i;
        }
        
        return {}; // Unreachable per constraints
    }
};
```

---

## **Pattern 2: Value Range Constraints → Array Indexing**

### When `-10^6 ≤ nums[i] ≤ 10^6` → Consider counting/frequency arrays

**Problem: Contains Duplicate**

```python
# Constraint: -10^9 ≤ nums[i] ≤ 10^9, 1 ≤ n ≤ 10^5
# Analysis: Range too large for array indexing → Use hash set

def contains_duplicate(nums: list[int]) -> bool:
    seen = set()
    for num in nums:
        if num in seen:
            return True
        seen.add(num)
    return False
    
# Alternative: O(n log n) if memory constrained
def contains_duplicate_sort(nums: list[int]) -> bool:
    nums.sort()  # In-place, O(1) extra space
    for i in range(1, len(nums)):
        if nums[i] == nums[i - 1]:
            return True
    return False
```

**Rust (Ownership Pattern):**

```rust
use std::collections::HashSet;

pub fn contains_duplicate(nums: Vec<i32>) -> bool {
    let mut seen = HashSet::with_capacity(nums.len());
    
    // Using iterator avoids bounds checking
    nums.into_iter().any(|num| !seen.insert(num))
    
    // Explanation of `any`:
    // - `insert` returns false if value already exists
    // - `!seen.insert(num)` is true when duplicate found
    // - `any` short-circuits on first true
}

// Memory-efficient version (sorts in-place)
pub fn contains_duplicate_sort(mut nums: Vec<i32>) -> bool {
    nums.sort_unstable(); // Faster than stable sort
    
    nums.windows(2).any(|pair| pair[0] == pair[1])
    // `windows(2)` creates overlapping pairs: [1,2,3] → [(1,2), (2,3)]
}
```

### When `0 ≤ nums[i] < n` → Array as hash map

**Problem: Find All Duplicates (nums[i] in [1, n])**

```python
# Constraint: 1 ≤ nums[i] ≤ n, where n = len(nums)
# Key insight: Use indices as "hash keys"

def find_duplicates(nums: list[int]) -> list[int]:
    """
    O(n) time, O(1) space using index negation trick.
    
    Technique: Mark visited numbers by negating value at index.
    Since nums[i] ∈ [1, n], we can use nums as our "hash set".
    """
    result = []
    
    for num in nums:
        index = abs(num) - 1  # Map [1,n] to [0,n-1]
        
        if nums[index] < 0:
            # Already negated → this is a duplicate
            result.append(abs(num))
        else:
            # Mark as seen by negating
            nums[index] = -nums[index]
    
    return result

# Example walkthrough:
# nums = [4,3,2,7,8,2,3,1]
# 
# i=0: num=4, index=3, nums[3]=7>0  → negate → nums=[4,3,2,-7,8,2,3,1]
# i=1: num=3, index=2, nums[2]=2>0  → negate → nums=[4,3,-2,-7,8,2,3,1]
# i=2: num=-2, index=1, nums[1]=3>0 → negate → nums=[4,-3,-2,-7,8,2,3,1]
# i=3: num=-7, index=6, nums[6]=3>0 → negate → nums=[4,-3,-2,-7,8,2,-3,1]
# i=4: num=8, index=7, nums[7]=1>0  → negate → nums=[4,-3,-2,-7,8,2,-3,-1]
# i=5: num=2, index=1, nums[1]<0    → DUPLICATE → result=[2]
# i=6: num=-3, index=2, nums[2]<0   → DUPLICATE → result=[2,3]
# i=7: num=-1, index=0, nums[0]=4>0 → negate → nums=[-4,-3,-2,-7,8,2,-3,-1]
```

**Rust (Mutable Reference Pattern):**

```rust
pub fn find_duplicates(mut nums: Vec<i32>) -> Vec<i32> {
    let mut result = Vec::new();
    
    for i in 0..nums.len() {
        let index = (nums[i].abs() - 1) as usize;
        
        if nums[index] < 0 {
            result.push(nums[i].abs());
        } else {
            nums[index] = -nums[index];
        }
    }
    
    result
}

// Key Rust concept: We need `mut nums` to modify in-place
// The signature takes ownership, so caller loses access to original
```

**Go Implementation:**

```go
func findDuplicates(nums []int) []int {
    result := []int{}
    
    for _, num := range nums {
        index := abs(num) - 1
        
        if nums[index] < 0 {
            result = append(result, abs(num))
        } else {
            nums[index] = -nums[index]
        }
    }
    
    return result
}

func abs(x int) int {
    if x < 0 {
        return -x
    }
    return x
}
```

**C++ (Reference Semantics):**

```cpp
class Solution {
public:
    std::vector<int> findDuplicates(std::vector<int>& nums) {
        std::vector<int> result;
        
        for (int num : nums) {
            int index = std::abs(num) - 1;
            
            if (nums[index] < 0) {
                result.push_back(std::abs(num));
            } else {
                nums[index] = -nums[index];
            }
        }
        
        return result;
    }
};
```

---

## **Pattern 3: Sorted Array Constraints → Two Pointers**

**Mental Model:** When input is sorted, think about **exploiting monotonicity**.

### Problem: 3Sum

```python
# Constraint: nums is sorted (or can be sorted)
# Strategy: Fix one element, use two pointers for remaining pair

def three_sum(nums: list[int]) -> list[list[int]]:
    """
    O(n²) solution using two pointers.
    
    Key insights:
    1. Sort array → enables two-pointer technique
    2. Skip duplicates → avoid repeated triplets
    3. Early termination → if nums[i] > 0, no solution possible
    """
    nums.sort()  # O(n log n)
    result = []
    n = len(nums)
    
    for i in range(n - 2):
        # Optimization: if smallest number > 0, no triplet sums to 0
        if nums[i] > 0:
            break
        
        # Skip duplicate values for first element
        if i > 0 and nums[i] == nums[i - 1]:
            continue
        
        # Two pointers for remaining pair
        left, right = i + 1, n - 1
        target = -nums[i]
        
        while left < right:
            current_sum = nums[left] + nums[right]
            
            if current_sum == target:
                result.append([nums[i], nums[left], nums[right]])
                
                # Skip duplicates for second element
                while left < right and nums[left] == nums[left + 1]:
                    left += 1
                # Skip duplicates for third element
                while left < right and nums[right] == nums[right - 1]:
                    right -= 1
                
                left += 1
                right -= 1
            elif current_sum < target:
                left += 1
            else:
                right -= 1
    
    return result
```

**Rust (Iterator Elegance):**

```rust
pub fn three_sum(mut nums: Vec<i32>) -> Vec<Vec<i32>> {
    nums.sort_unstable(); // Faster than stable sort
    let mut result = Vec::new();
    let n = nums.len();
    
    for i in 0..n.saturating_sub(2) {
        if nums[i] > 0 {
            break; // Early termination
        }
        
        // Skip duplicates
        if i > 0 && nums[i] == nums[i - 1] {
            continue;
        }
        
        let (mut left, mut right) = (i + 1, n - 1);
        let target = -nums[i];
        
        while left < right {
            let sum = nums[left] + nums[right];
            
            match sum.cmp(&target) {
                std::cmp::Ordering::Equal => {
                    result.push(vec![nums[i], nums[left], nums[right]]);
                    
                    // Skip duplicates
                    while left < right && nums[left] == nums[left + 1] {
                        left += 1;
                    }
                    while left < right && nums[right] == nums[right - 1] {
                        right -= 1;
                    }
                    
                    left += 1;
                    right -= 1;
                }
                std::cmp::Ordering::Less => left += 1,
                std::cmp::Ordering::Greater => right -= 1,
            }
        }
    }
    
    result
}
```

---

## **Pattern 4: Graph Constraints → Algorithm Selection**

### Decoding Graph Problem Constraints

```
|V| ≤ 100, |E| ≤ 5000    → Adjacency matrix, Floyd-Warshall O(V³)
|V| ≤ 10^5, |E| ≤ 10^5   → Adjacency list, BFS/DFS O(V + E)
Weighted graph           → Dijkstra O((V + E) log V)
Negative weights         → Bellman-Ford O(VE)
DAG (Directed Acyclic)   → Topological sort O(V + E)
```

### Problem: Course Schedule (Cycle Detection)

```python
from collections import defaultdict, deque
from typing import List

def can_finish(num_courses: int, prerequisites: List[List[int]]) -> bool:
    """
    Detect cycle in directed graph using Kahn's algorithm (BFS).
    
    Constraint analysis:
    - 1 ≤ numCourses ≤ 2000
    - 0 ≤ prerequisites.length ≤ 5000
    → O(V + E) required → Topological sort
    
    Key insight: If graph has cycle, topological sort is impossible.
    """
    # Build adjacency list and in-degree count
    graph = defaultdict(list)
    in_degree = [0] * num_courses
    
    for course, prereq in prerequisites:
        graph[prereq].append(course)
        in_degree[course] += 1
    
    # Start with courses that have no prerequisites
    queue = deque([i for i in range(num_courses) if in_degree[i] == 0])
    completed = 0
    
    while queue:
        course = queue.popleft()
        completed += 1
        
        # Remove this course as a prerequisite
        for next_course in graph[course]:
            in_degree[next_course] -= 1
            if in_degree[next_course] == 0:
                queue.append(next_course)
    
    return completed == num_courses
```

**Rust (Strong Type Safety):**

```rust
use std::collections::{HashMap, VecDeque};

pub fn can_finish(num_courses: i32, prerequisites: Vec<Vec<i32>>) -> bool {
    let n = num_courses as usize;
    
    // Build graph and in-degree
    let mut graph: HashMap<usize, Vec<usize>> = HashMap::new();
    let mut in_degree = vec![0; n];
    
    for prereq in &prerequisites {
        let (course, pre) = (prereq[0] as usize, prereq[1] as usize);
        graph.entry(pre).or_default().push(course);
        in_degree[course] += 1;
    }
    
    // Initialize queue with zero in-degree courses
    let mut queue: VecDeque<usize> = (0..n)
        .filter(|&i| in_degree[i] == 0)
        .collect();
    
    let mut completed = 0;
    
    while let Some(course) = queue.pop_front() {
        completed += 1;
        
        if let Some(neighbors) = graph.get(&course) {
            for &next in neighbors {
                in_degree[next] -= 1;
                if in_degree[next] == 0 {
                    queue.push_back(next);
                }
            }
        }
    }
    
    completed == n
}
```

**Go (Explicit Structure):**

```go
func canFinish(numCourses int, prerequisites [][]int) bool {
    // Build adjacency list
    graph := make(map[int][]int)
    inDegree := make([]int, numCourses)
    
    for _, prereq := range prerequisites {
        course, pre := prereq[0], prereq[1]
        graph[pre] = append(graph[pre], course)
        inDegree[course]++
    }
    
    // Find courses with no prerequisites
    queue := []int{}
    for i := 0; i < numCourses; i++ {
        if inDegree[i] == 0 {
            queue = append(queue, i)
        }
    }
    
    completed := 0
    
    for len(queue) > 0 {
        course := queue[0]
        queue = queue[1:]
        completed++
        
        for _, next := range graph[course] {
            inDegree[next]--
            if inDegree[next] == 0 {
                queue = append(queue, next)
            }
        }
    }
    
    return completed == numCourses
}
```

---

## **Pattern 5: Binary Search on Answer Space**

**Constraint Pattern:** When asked for "minimum/maximum value such that..." with large ranges.

### Problem: Koko Eating Bananas

```python
import math

def min_eating_speed(piles: list[int], h: int) -> int:
    """
    Binary search on speed (answer space).
    
    Constraint analysis:
    - 1 ≤ piles.length ≤ 10^4
    - piles.length ≤ h ≤ 10^9
    - 1 ≤ piles[i] ≤ 10^9
    
    Key insight: We can't enumerate all speeds (10^9 options).
    But we can binary search: if speed k works, all k' > k also work.
    """
    def can_finish(speed: int) -> bool:
        """Check if Koko can finish with given speed."""
        hours_needed = sum(math.ceil(pile / speed) for pile in piles)
        return hours_needed <= h
    
    # Search space: [1, max(piles)]
    left, right = 1, max(piles)
    
    while left < right:
        mid = left + (right - left) // 2
        
        if can_finish(mid):
            right = mid  # Try slower speed
        else:
            left = mid + 1  # Need faster speed
    
    return left
```

**Rust (Functional Style):**

```rust
pub fn min_eating_speed(piles: Vec<i32>, h: i32) -> i32 {
    fn can_finish(piles: &[i32], speed: i32, h: i32) -> bool {
        let hours_needed: i32 = piles
            .iter()
            .map(|&pile| (pile + speed - 1) / speed) // Ceiling division
            .sum();
        
        hours_needed <= h
    }
    
    let (mut left, mut right) = (1, *piles.iter().max().unwrap());
    
    while left < right {
        let mid = left + (right - left) / 2;
        
        if can_finish(&piles, mid, h) {
            right = mid;
        } else {
            left = mid + 1;
        }
    }
    
    left
}

// Performance note: Ceiling division without floating point
// (a + b - 1) / b is equivalent to ceil(a / b)
```

**C++ (Template Optimization):**

```cpp
class Solution {
public:
    int minEatingSpeed(vector<int>& piles, int h) {
        auto can_finish = [&](long long speed) -> bool {
            long long hours = 0;
            for (int pile : piles) {
                hours += (pile + speed - 1) / speed; // Ceiling division
                if (hours > h) return false; // Early termination
            }
            return true;
        };
        
        int left = 1;
        int right = *max_element(piles.begin(), piles.end());
        
        while (left < right) {
            int mid = left + (right - left) / 2;
            
            if (can_finish(mid)) {
                right = mid;
            } else {
                left = mid + 1;
            }
        }
        
        return left;
    }
};
```

---

## **Pattern 6: Sliding Window for Subarray Problems**

**Constraint Trigger:** "Find maximum/minimum subarray/substring that satisfies..."

### Problem: Longest Substring Without Repeating Characters

```python
def length_of_longest_substring(s: str) -> int:
    """
    Sliding window with hash map.
    
    Constraint: 0 ≤ s.length ≤ 5 * 10^4
    → O(n) required
    
    Technique:
    - Expand window (right pointer) to include new characters
    - Contract window (left pointer) when constraint violated
    - Track maximum valid window size
    """
    char_index = {}  # char -> most recent index
    max_length = 0
    left = 0
    
    for right, char in enumerate(s):
        # If char seen and within current window
        if char in char_index and char_index[char] >= left:
            # Move left past the previous occurrence
            left = char_index[char] + 1
        
        char_index[char] = right
        max_length = max(max_length, right - left + 1)
    
    return max_length

# Example trace: s = "abcabcbb"
# right=0, char='a': window="a", max=1
# right=1, char='b': window="ab", max=2
# right=2, char='c': window="abc", max=3
# right=3, char='a': 'a' at index 0, left=1, window="bca", max=3
# right=4, char='b': 'b' at index 1, left=2, window="cab", max=3
# ...
```

**Rust (HashMap Pattern):**

```rust
use std::collections::HashMap;

pub fn length_of_longest_substring(s: String) -> i32 {
    let mut char_index: HashMap<char, usize> = HashMap::new();
    let mut max_length = 0;
    let mut left = 0;
    
    for (right, ch) in s.chars().enumerate() {
        if let Some(&prev_index) = char_index.get(&ch) {
            if prev_index >= left {
                left = prev_index + 1;
            }
        }
        
        char_index.insert(ch, right);
        max_length = max_length.max(right - left + 1);
    }
    
    max_length as i32
}
```

**Go (Map Pattern):**

```go
func lengthOfLongestSubstring(s string) int {
    charIndex := make(map[rune]int)
    maxLength := 0
    left := 0
    
    for right, ch := range s {
        if prevIndex, exists := charIndex[ch]; exists && prevIndex >= left {
            left = prevIndex + 1
        }
        
        charIndex[ch] = right
        if right - left + 1 > maxLength {
            maxLength = right - left + 1
        }
    }
    
    return maxLength
}
```

---

## **Pattern 7: Dynamic Programming with State Compression**

### Problem: Combination Sum IV (Order Matters)

```python
def combination_sum4(nums: list[int], target: int) -> int:
    """
    DP with memoization.
    
    Constraint: 
    - 1 ≤ nums.length ≤ 200
    - 1 ≤ nums[i] ≤ 1000
    - 1 ≤ target ≤ 1000
    
    State: dp[i] = number of ways to sum to i
    Transition: dp[i] = sum(dp[i - num] for num in nums if num <= i)
    """
    dp = [0] * (target + 1)
    dp[0] = 1  # Base case: one way to make 0 (use nothing)
    
    for i in range(1, target + 1):
        for num in nums:
            if i >= num:
                dp[i] += dp[i - num]
    
    return dp[target]

# Explanation:
# target = 4, nums = [1,2,3]
# dp[0] = 1
# dp[1] = dp[0] = 1              (just [1])
# dp[2] = dp[1] + dp[0] = 2      ([1,1], [2])
# dp[3] = dp[2] + dp[1] + dp[0] = 4  ([1,1,1], [1,2], [2,1], [3])
# dp[4] = dp[3] + dp[2] + dp[1] = 7
```

**Rust (Array-Based DP):**

```rust
pub fn combination_sum4(nums: Vec<i32>, target: i32) -> i32 {
    let target = target as usize;
    let mut dp = vec![0; target + 1];
    dp[0] = 1;
    
    for i in 1..=target {
        for &num in &nums {
            let num = num as usize;
            if i >= num {
                dp[i] = dp[i].saturating_add(dp[i - num]); // Prevent overflow
            }
        }
    }
    
    dp[target]
}
```

---

## **Real-World Production Patterns**

### **Google Style: Bounds Checking**

```cpp
// chromium/base/containers/span.h pattern
template<typename T>
class Span {
    T* data_;
    size_t size_;
    
public:
    T& operator[](size_t index) {
        CHECK_LT(index, size_); // Debug builds: assert
        return data_[index];
    }
    
    T& at(size_t index) {
        if (index >= size_) {
            throw std::out_of_range("Span index out of range");
        }
        return data_[index];
    }
};
```

### **Meta Style: Input Validation**

```python
def process_user_ids(user_ids: list[int]) -> list[int]:
    """Meta-style defensive programming."""
    # Constraint validation
    if not user_ids:
        return []
    
    if len(user_ids) > 10000:
        raise ValueError("Too many user IDs (max 10000)")
    
    # Sanitize inputs
    valid_ids = [uid for uid in user_ids if 0 < uid < 2**31]
    
    if len(valid_ids) != len(user_ids):
        logger.warning(f"Filtered {len(user_ids) - len(valid_ids)} invalid IDs")
    
    return valid_ids
```

### **Kernel Style: Explicit Bounds**

```c
// Linux kernel pattern: always pass length
int copy_from_user(void *to, const void __user *from, unsigned long n) {
    // 'n' is explicit bound, never inferred
    if (!access_ok(from, n))
        return -EFAULT;
    
    return __copy_from_user(to, from, n);
}
```

---

## **Optimization Decision Tree**

```
Problem received
    ↓
1. Read constraints carefully
    ↓
2. Identify constraint category:
    - Size → Complexity limit
    - Range → Data structure choice
    - Sorted → Two pointers / Binary search
    - Graph structure → Algorithm selection
    ↓
3. Choose approach:
    - Can we do O(n)? → Hash map / Two pointers
    - Need O(n log n)? → Sort / Binary search
    - Need O(n²)? → 2D DP / Nested loops
    - Need O(2^n)? → Backtracking / Bitmask DP
    ↓
4. Implement with pattern:
    - Array indexing → Bounds elimination
    - Hash operations → Pre-allocation
    - Sorting → Choose stable vs unstable
    - Recursion → Memoization / Tail call
    ↓
5. Verify edge cases:
    - Empty input
    - Single element
    - Maximum constraint values
    - Duplicate elements
```

---

## **Practice Roadmap**

### **Week 1-2: Array Constraints**
- Two Sum variations (hash map mastery)
- Product of Array Except Self (no division constraint)
- Find Duplicates (in-place constraint)

### **Week 3-4: Sliding Window**
- Longest Substring Without Repeating Characters
- Minimum Window Substring
- Sliding Window Maximum

### **Week 5-6: Graph Constraints**
- Course Schedule (cycle detection)
- Number of Islands (connected components)
- Word Ladder (shortest path in unweighted graph)

### **Week 7-8: DP State Compression**
- Coin Change (classic DP)
- Combination Sum IV (order matters)
- Decode Ways (state machine DP)

### **Week 9-10: Binary Search**
- Koko Eating Bananas (search on answer)
- Capacity To Ship Packages (search on answer)
- Find Minimum in Rotated Sorted Array

---

# Comprehensive Guide to Constraint Design Patterns by Language

## Foundation: What Are Constraints?

Before we dive deep, let's establish clarity on what "constraints" mean in this context.

**Constraint**: A restriction or limitation on valid states, inputs, or behaviors in your system. Examples:
- A `NonZeroU32` can never be zero
- An index must be within array bounds
- A file handle must be open before reading
- A sorted array must maintain order after insertion

**Design Pattern**: A reusable solution to a common problem. Constraint design patterns are techniques to *encode invariants* (unchanging truths) into your type system, runtime checks, or API design so that invalid states become **impossible** or **detectable**.

Think of constraints as guardrails that prevent your program from reaching undefined behavior, security vulnerabilities, or logical errors.

---

## Core Methodologies Across All Languages

### 1. **Zero-Cost Abstractions (Compile-Time Elimination)**
Constraints enforced at compile time with **no runtime overhead**. The type checker proves correctness.

### 2. **Runtime Validation with Panic/Error**
Constraints checked at runtime; violations cause immediate failure (panic) or return errors.

### 3. **Builder Patterns**
Gradually construct valid objects through a series of validated steps.

### 4. **Phantom Types**
Zero-sized type markers that exist only at compile time to track state transitions.

### 5. **Typestate Pattern**
Encode object lifecycle states in the type system (e.g., `File<Open>` vs `File<Closed>`).

### 6. **Newtype Pattern**
Wrap primitives in distinct types to prevent mixing incompatible values (e.g., `Meters` vs `Feet`).

### 7. **Refinement Types**
Types with logical predicates (e.g., `{x: i32 | x > 0}`). Mostly theoretical but inspiring practical designs.

---

## Language-Specific Deep Dive

---

## **RUST: The Constraint King**

Rust's ownership system, lifetimes, and zero-cost abstractions make it the gold standard for compile-time constraint enforcement.

### **Key Concepts**

**Ownership**: Each value has one owner; when owner goes out of scope, value is dropped.
**Borrowing**: References (`&T`, `&mut T`) temporarily access data without owning it.
**Lifetime**: Ensures references don't outlive the data they point to.
**Phantom Types**: Zero-sized types that exist only at compile time for type-level state tracking.

---

### **1. Newtype Pattern: Semantic Constraints**

```rust
// Prevent mixing incompatible units
struct Meters(f64);
struct Feet(f64);

impl Meters {
    fn new(value: f64) -> Option<Self> {
        if value >= 0.0 {
            Some(Meters(value))
        } else {
            None // Negative distance is invalid
        }
    }
}

// Compile error: can't add Meters + Feet without explicit conversion
fn calculate_distance(a: Meters, b: Meters) -> Meters {
    Meters(a.0 + b.0)
}
```

**Why this matters**: You can't accidentally pass `Feet` where `Meters` is expected. The type system enforces dimensional analysis.

---

### **2. Typestate Pattern: Compile-Time State Machines**

```rust
use std::marker::PhantomData;

// State markers (zero-sized)
struct Open;
struct Closed;

struct File<State> {
    path: String,
    _state: PhantomData<State>, // PhantomData tells compiler we "use" State
}

impl File<Closed> {
    fn new(path: String) -> Self {
        File {
            path,
            _state: PhantomData,
        }
    }

    // Consumes File<Closed>, returns File<Open>
    fn open(self) -> File<Open> {
        println!("Opening {}", self.path);
        File {
            path: self.path,
            _state: PhantomData,
        }
    }
}

impl File<Open> {
    fn read(&self) -> String {
        format!("Contents of {}", self.path)
    }

    // Consumes File<Open>, returns File<Closed>
    fn close(self) -> File<Closed> {
        println!("Closing {}", self.path);
        File {
            path: self.path,
            _state: PhantomData,
        }
    }
}

// Usage
fn main() {
    let file = File::new("data.txt".to_string());
    // file.read(); // COMPILE ERROR: no method `read` on `File<Closed>`
    
    let file = file.open();
    println!("{}", file.read()); // OK
    
    let file = file.close();
    // println!("{}", file.read()); // COMPILE ERROR: file is closed
}
```

**Mental Model**: Each state transition **consumes** the old state and produces a new one. Invalid transitions simply don't compile.

---

### **3. Non-Zero Types: Kernel-Level Safety**

```rust
use std::num::NonZeroU32;

// Represents a process ID that can never be zero
struct ProcessId(NonZeroU32);

impl ProcessId {
    fn new(id: u32) -> Option<Self> {
        NonZeroU32::new(id).map(ProcessId)
    }
    
    fn as_raw(&self) -> u32 {
        self.0.get()
    }
}

// Compiler can optimize Option<NonZeroU32> to same size as u32
// because 0 is unused and can represent None
fn find_process(id: ProcessId) -> Option<ProcessId> {
    // ...
    Some(id)
}
```

**Performance Insight**: `Option<NonZeroU32>` is the same size as `u32` due to **niche optimization**. The compiler uses the invalid `0` value to represent `None`.

---

### **4. Builder Pattern with Compile-Time Validation**

```rust
struct Unset;
struct Set<T>(T);

struct HttpRequestBuilder<U, M, B> {
    url: U,
    method: M,
    body: B,
}

impl HttpRequestBuilder<Unset, Unset, Unset> {
    fn new() -> Self {
        HttpRequestBuilder {
            url: Unset,
            method: Unset,
            body: Unset,
        }
    }
}

impl<M, B> HttpRequestBuilder<Unset, M, B> {
    fn url(self, url: String) -> HttpRequestBuilder<Set<String>, M, B> {
        HttpRequestBuilder {
            url: Set(url),
            method: self.method,
            body: self.body,
        }
    }
}

impl<U, B> HttpRequestBuilder<U, Unset, B> {
    fn method(self, method: String) -> HttpRequestBuilder<U, Set<String>, B> {
        HttpRequestBuilder {
            url: self.url,
            method: Set(method),
            body: self.body,
        }
    }
}

// Only callable when both url and method are Set
impl<B> HttpRequestBuilder<Set<String>, Set<String>, B> {
    fn build(self) -> HttpRequest {
        HttpRequest {
            url: self.url.0,
            method: self.method.0,
        }
    }
}

struct HttpRequest {
    url: String,
    method: String,
}

fn main() {
    let req = HttpRequestBuilder::new()
        .url("https://api.example.com".to_string())
        .method("GET".to_string())
        .build(); // OK
    
    // let req = HttpRequestBuilder::new().build(); // COMPILE ERROR
}
```

**Expert Insight**: This is how libraries like `hyper` and `reqwest` ensure you can't forget required fields.

---

### **5. Lifetime Constraints: Borrow Checker as Constraint Enforcer**

```rust
// Constraint: iterator cannot outlive the data it references
struct MyIter<'a> {
    data: &'a [i32],
    index: usize,
}

impl<'a> Iterator for MyIter<'a> {
    type Item = &'a i32;
    
    fn next(&mut self) -> Option<Self::Item> {
        if self.index < self.data.len() {
            let item = &self.data[self.index];
            self.index += 1;
            Some(item)
        } else {
            None
        }
    }
}

fn create_iter(data: &[i32]) -> MyIter {
    MyIter { data, index: 0 }
}

// This won't compile: iterator would outlive data
// fn dangling_iter() -> MyIter<'static> {
//     let vec = vec![1, 2, 3];
//     MyIter { data: &vec, index: 0 } // ERROR: vec dropped but reference escapes
// }
```

---

### **6. Security-Focused: Prevent Timing Attacks**

```rust
use subtle::ConstantTimeEq;

// Password comparison must be constant-time to prevent timing attacks
struct Password([u8; 32]);

impl Password {
    fn verify(&self, input: &[u8; 32]) -> bool {
        // Constant-time comparison - takes same time regardless of differences
        self.0.ct_eq(input).into()
    }
}

// WRONG (variable time):
// fn insecure_verify(a: &[u8], b: &[u8]) -> bool {
//     a == b // Short-circuits on first difference
// }
```

**Security Principle**: Timing attacks measure how long comparisons take. If comparison stops at first mismatch, attackers can guess password byte-by-byte.

---

### **7. Performance-Critical: Index Bounds Elimination**

```rust
fn sum_slice(data: &[i32]) -> i32 {
    let mut sum = 0;
    // Compiler eliminates bounds checks in iterators
    for &value in data.iter() {
        sum += value;
    }
    sum
}

// Manual indexing keeps bounds checks
fn sum_slice_manual(data: &[i32]) -> i32 {
    let mut sum = 0;
    for i in 0..data.len() {
        sum += data[i]; // Bounds check on every access
    }
    sum
}

// Unsafe: explicitly remove checks (use with extreme care)
fn sum_slice_unsafe(data: &[i32]) -> i32 {
    let mut sum = 0;
    for i in 0..data.len() {
        unsafe {
            sum += *data.get_unchecked(i); // No bounds check
        }
    }
    sum
}
```

**Benchmarking Insight**: `iter()` version is as fast as unsafe version because LLVM proves bounds are correct.

---

## **C++: Manual Control with Modern Safety**

C++ offers powerful constraint mechanisms but requires discipline.

### **Key Concepts**

**RAII (Resource Acquisition Is Initialization)**: Resources tied to object lifetime.
**`constexpr`**: Compile-time evaluation and checking.
**Templates**: Compile-time polymorphism and constraint enforcement.
**Concepts (C++20)**: Explicit template constraints.

---

### **1. Newtype via Strong Typedef**

```cpp
#include <type_traits>

// Strong typedef: prevents accidental mixing
template<typename T, typename Tag>
struct StrongType {
    T value;
    
    explicit StrongType(T v) : value(v) {}
    
    T get() const { return value; }
};

struct MetersTag {};
struct FeetTag {};

using Meters = StrongType<double, MetersTag>;
using Feet = StrongType<double, FeetTag>;

double calculate_distance(Meters a, Meters b) {
    return a.get() + b.get();
}

// Compile error: can't pass Feet where Meters expected
// calculate_distance(Feet{3.0}, Feet{4.0});
```

---

### **2. RAII for Resource Constraints**

```cpp
#include <memory>
#include <mutex>

// Lock is automatically released when guard goes out of scope
class ThreadSafeCounter {
    mutable std::mutex mutex_;
    int count_ = 0;
    
public:
    void increment() {
        std::lock_guard<std::mutex> lock(mutex_); // Lock acquired
        ++count_;
    } // Lock automatically released here
    
    int get() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return count_;
    }
};
```

**Mental Model**: The guard object "owns" the lock. When guard is destroyed (scope exit), lock is released automatically.

---

### **3. `constexpr` for Compile-Time Validation**

```cpp
constexpr int factorial(int n) {
    if (n < 0) {
        throw "Negative factorial!"; // Compile error if triggered
    }
    return n <= 1 ? 1 : n * factorial(n - 1);
}

// Computed at compile time
constexpr int fact5 = factorial(5); // OK: 120

// This would be a compile error:
// constexpr int bad = factorial(-1);

// Runtime check if not constexpr
int runtime_fact(int n) {
    if (n < 0) throw std::invalid_argument("Negative factorial");
    return factorial(n);
}
```

---

### **4. C++20 Concepts: Explicit Constraints**

```cpp
#include <concepts>
#include <vector>

// Define what "sortable" means
template<typename T>
concept Sortable = requires(T a, T b) {
    { a < b } -> std::convertible_to<bool>;
};

// Only works with types that satisfy Sortable
template<Sortable T>
void my_sort(std::vector<T>& vec) {
    // ... sorting logic
}

struct NotComparable {};

// Compile error with clear message:
// std::vector<NotComparable> v;
// my_sort(v); // ERROR: NotComparable doesn't satisfy Sortable
```

---

### **5. Bounds-Checked Access with `std::span`**

```cpp
#include <span>
#include <array>

void process_data(std::span<int> data) {
    // data.size() known at runtime
    for (size_t i = 0; i < data.size(); ++i) {
        data[i] *= 2; // Bounds check in debug builds
    }
}

// Range-based for: no manual indexing
void process_data_safe(std::span<int> data) {
    for (int& value : data) {
        value *= 2; // No bounds checks needed
    }
}
```

---

### **6. Linux Kernel Style: Explicit Bounds**

```cpp
// Kernel-style: always pass size with pointer
void process_buffer(const char* buf, size_t len) {
    for (size_t i = 0; i < len; ++i) {
        // Explicit bound: never access beyond len
        char c = buf[i];
        // ...
    }
}

// Modern C++: use span
void process_buffer_modern(std::span<const char> buf) {
    for (char c : buf) {
        // ...
    }
}
```

---

### **7. Security: Prevent Buffer Overflows**

```cpp
#include <cstring>
#include <stdexcept>

class SafeBuffer {
    char* data_;
    size_t capacity_;
    size_t size_;
    
public:
    SafeBuffer(size_t capacity) 
        : data_(new char[capacity]), capacity_(capacity), size_(0) {}
    
    ~SafeBuffer() { delete[] data_; }
    
    void append(const char* str, size_t len) {
        if (size_ + len > capacity_) {
            throw std::runtime_error("Buffer overflow prevented");
        }
        std::memcpy(data_ + size_, str, len);
        size_ += len;
    }
    
    std::span<char> view() { return {data_, size_}; }
};
```

---

## **GO: Simplicity with Runtime Safety**

Go emphasizes simplicity and explicit error handling. Constraints are mostly runtime.

### **Key Concepts**

**Interfaces**: Define behavior contracts.
**Defer**: Ensure cleanup happens (like RAII).
**Panic/Recover**: Runtime safety valve for unrecoverable errors.

---

### **1. Newtype Pattern**

```go
package main

type Meters float64
type Feet float64

func calculateDistance(a, b Meters) Meters {
    return a + b
}

func main() {
    m := Meters(10.0)
    // f := Feet(5.0)
    // result := calculateDistance(m, f) // Compile error: mismatched types
    result := calculateDistance(m, Meters(3.0))
}
```

---

### **2. Builder Pattern with Validation**

```go
type HTTPRequest struct {
    url    string
    method string
}

type HTTPRequestBuilder struct {
    url    string
    method string
}

func NewHTTPRequestBuilder() *HTTPRequestBuilder {
    return &HTTPRequestBuilder{}
}

func (b *HTTPRequestBuilder) URL(url string) *HTTPRequestBuilder {
    b.url = url
    return b
}

func (b *HTTPRequestBuilder) Method(method string) *HTTPRequestBuilder {
    b.method = method
    return b
}

func (b *HTTPRequestBuilder) Build() (*HTTPRequest, error) {
    if b.url == "" {
        return nil, fmt.Errorf("url is required")
    }
    if b.method == "" {
        return nil, fmt.Errorf("method is required")
    }
    return &HTTPRequest{url: b.url, method: b.method}, nil
}

func main() {
    req, err := NewHTTPRequestBuilder().
        URL("https://api.example.com").
        Method("GET").
        Build()
    
    if err != nil {
        log.Fatal(err)
    }
}
```

---

### **3. Defer for Resource Management**

```go
import "sync"

type Counter struct {
    mu    sync.Mutex
    count int
}

func (c *Counter) Increment() {
    c.mu.Lock()
    defer c.mu.Unlock() // Guaranteed to run when function exits
    c.count++
}
```

---

### **4. Interface Constraints**

```go
type Sortable interface {
    Len() int
    Less(i, j int) bool
    Swap(i, j int)
}

func Sort(data Sortable) {
    // ... sorting logic
}

type IntSlice []int

func (s IntSlice) Len() int           { return len(s) }
func (s IntSlice) Less(i, j int) bool { return s[i] < s[j] }
func (s IntSlice) Swap(i, j int)      { s[i], s[j] = s[j], s[i] }

// Now IntSlice can be sorted
```

---

### **5. Bounds Checking (Always On)**

```go
func sumSlice(data []int) int {
    sum := 0
    for i := 0; i < len(data); i++ {
        sum += data[i] // Automatic bounds check, panics if out of range
    }
    return sum
}

// Better: range avoids manual indexing
func sumSliceRange(data []int) int {
    sum := 0
    for _, value := range data {
        sum += value // No index, no bounds check needed
    }
    return sum
}
```

---

### **6. Google Go Style: Explicit Error Returns**

```go
type ProcessID uint32

func NewProcessID(id uint32) (ProcessID, error) {
    if id == 0 {
        return 0, fmt.Errorf("process ID cannot be zero")
    }
    return ProcessID(id), nil
}

func FindProcess(id ProcessID) (*Process, error) {
    // ... lookup logic
    if process == nil {
        return nil, fmt.Errorf("process %d not found", id)
    }
    return process, nil
}
```

---

## **PYTHON: Dynamic but Disciplined**

Python's dynamic nature makes compile-time constraints impossible, but modern typing brings structure.

### **Key Concepts**

**Type Hints**: Optional static type annotations (checked by tools like `mypy`).
**Dataclasses**: Structured data with automatic methods.
**Descriptors**: Custom attribute access control.
**`__slots__`**: Restrict instance attributes for performance.

---

### **1. Newtype with Type Hints**

```python
from typing import NewType

Meters = NewType('Meters', float)
Feet = NewType('Feet', float)

def calculate_distance(a: Meters, b: Meters) -> Meters:
    return Meters(a + b)

m1 = Meters(10.0)
m2 = Meters(5.0)
result = calculate_distance(m1, m2)

# Mypy will warn:
# f = Feet(3.0)
# result = calculate_distance(m1, f)  # Type error
```

---

### **2. Dataclass with Validation**

```python
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)  # Immutable
class ProcessID:
    value: int
    
    def __post_init__(self):
        if self.value <= 0:
            raise ValueError("ProcessID must be positive")

# Usage
pid = ProcessID(1234)  # OK
# pid = ProcessID(0)   # Raises ValueError
```

---

### **3. Property Descriptors for Constraints**

```python
class PositiveNumber:
    def __init__(self, name):
        self.name = name
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return obj.__dict__.get(self.name, 0)
    
    def __set__(self, obj, value):
        if value < 0:
            raise ValueError(f"{self.name} must be positive")
        obj.__dict__[self.name] = value

class BankAccount:
    balance = PositiveNumber('balance')
    
    def __init__(self, initial_balance):
        self.balance = initial_balance

# Usage
account = BankAccount(100)
# account.balance = -50  # Raises ValueError
```

---

### **4. Context Managers (Resource Safety)**

```python
from contextlib import contextmanager
import threading

class ThreadSafeCounter:
    def __init__(self):
        self._lock = threading.Lock()
        self._count = 0
    
    @contextmanager
    def locked(self):
        self._lock.acquire()
        try:
            yield self
        finally:
            self._lock.release()
    
    def increment(self):
        self._count += 1
    
    def get(self):
        return self._count

# Usage
counter = ThreadSafeCounter()
with counter.locked():
    counter.increment()  # Lock held
# Lock released here
```

---

### **5. Type Guards for Runtime Validation**

```python
from typing import TypeGuard

def is_positive_int(value: int) -> TypeGuard[int]:
    """Type guard that narrows int to positive int."""
    return value > 0

def process_positive(value: int) -> None:
    if not is_positive_int(value):
        raise ValueError("Value must be positive")
    # Type checker knows value > 0 here
    print(f"Processing {value}")
```

---

### **6. Meta Style: Explicit Validation Functions**

```python
from typing import Optional

class UserId:
    def __init__(self, value: int):
        self._value = self._validate(value)
    
    @staticmethod
    def _validate(value: int) -> int:
        if value <= 0:
            raise ValueError("User ID must be positive")
        if value > 2**31 - 1:
            raise ValueError("User ID too large")
        return value
    
    @property
    def value(self) -> int:
        return self._value
    
    def __repr__(self) -> str:
        return f"UserId({self._value})"

# Usage
uid = UserId(12345)
# bad = UserId(-1)  # Raises ValueError
```

---

### **7. Bounds Checking (Always On)**

```python
def sum_list(data: list[int]) -> int:
    total = 0
    for i in range(len(data)):
        total += data[i]  # Raises IndexError if out of bounds
    return total

# Better: avoid manual indexing
def sum_list_pythonic(data: list[int]) -> int:
    return sum(data)  # No indexing needed
```

---

## **Performance-Critical Patterns**

### **Hot Path Optimization**

1. **Rust**: Use iterators instead of indexing (bounds checks eliminated by compiler)
2. **C++**: Use `std::span` + range-for to help compiler optimize
3. **Go**: Use `range` instead of manual indexing
4. **Python**: Use built-in functions (`sum`, `map`, etc.) implemented in C

### **Branch Prediction**

```rust
// Likely path should be the true branch
if likely(data.len() > 0) {
    process_data(data);
}

// C++ equivalent
if (__builtin_expect(data.size() > 0, 1)) {
    process_data(data);
}
```

---

## **Security-Focused Patterns**

### **Input Validation**

```rust
fn parse_user_input(input: &str) -> Result<u32, ParseError> {
    let trimmed = input.trim();
    
    // Constraint: length limit (prevent DoS)
    if trimmed.len() > 1000 {
        return Err(ParseError::TooLong);
    }
    
    // Constraint: numeric range
    let value: u32 = trimmed.parse()
        .map_err(|_| ParseError::InvalidFormat)?;
    
    if value > 100_000 {
        return Err(ParseError::OutOfRange);
    }
    
    Ok(value)
}
```

### **Constant-Time Operations**

```cpp
// Prevent timing attacks in cryptographic code
bool constant_time_compare(const uint8_t* a, const uint8_t* b, size_t len) {
    uint8_t diff = 0;
    for (size_t i = 0; i < len; ++i) {
        diff |= a[i] ^ b[i];  // Always runs full length
    }
    return diff == 0;
}
```

---

## **Real-World Examples**

### **Linux Kernel: Bounds Safety**

```c
// Always pass length with pointers
ssize_t read(int fd, void *buf, size_t count);

// Never use:
// void unsafe_read(int fd, void *buf);  // How much can we write?
```

### **Google Chromium: Type Safety**

```cpp
// Strong typedefs prevent mixing IDs
using TabId = base::StrongAlias<class TabIdTag, int32_t>;
using WindowId = base::StrongAlias<class WindowIdTag, int32_t>;

// Compile error if you pass WindowId where TabId expected
void FocusTab(TabId id);
```

### **Meta/Facebook: Hack Language**

```php
// Refinement types in Hack
function get_positive_int(): int where result > 0 {
    return 42;
}
```

---

## **Mental Models for Mastery**

### **1. Make Invalid States Unrepresentable**
Design types so invalid combinations can't exist. Example: `Option<NonZeroU32>` vs `u32 + bool`.

### **2. Parse, Don't Validate**
Instead of checking constraints repeatedly, parse once into a validated type.

```rust
// Bad: validate everywhere
fn process(id: u32) {
    assert!(id != 0);
    // ...
}

// Good: validate once, use validated type
fn process(id: NonZeroU32) {
    // id is guaranteed non-zero
}
```

### **3. Fail Fast, Fail Loud**
Detect constraint violations as early as possible. Compile-time > construction-time > usage-time.

### **4. Separate Validation from Business Logic**
Keep constraint checking in constructors/parsers. Keep business logic constraint-free.

---

## **Practice Path**

1. **Week 1-2**: Implement newtype wrappers in all four languages
2. **Week 3-4**: Build typestate machines (file handle, TCP connection)
3. **Week 5-6**: Create builder patterns with compile-time validation
4. **Week 7-8**: Study production codebases (Rust: `tokio`, C++: `abseil`, Go: `kubernetes`, Python: `pydantic`)

---

## **Key Takeaways**

- **Rust**: Maximum compile-time safety, zero-cost abstractions
- **C++**: Powerful but requires discipline; modern features (concepts, span) help
- **Go**: Runtime safety with explicit errors; simplicity over cleverness
- **Python**: Dynamic nature limits compile-time checks; use type hints + runtime validation

**Your Goal**: Think in constraints. Every function, every type should encode its invariants clearly. The compiler/runtime should enforce them automatically.

This is the path to 1% mastery. Now go build something that's **impossible to use incorrectly**.

---

# I. Constraint Design Patterns by Language

## 1. Rust (Compile-Time First, Zero-Cost Abstractions)

Rust is the gold standard for **constraint-by-construction**.

### Core Patterns

#### 1. Newtype Pattern (Most Important)

```rust
struct Size(u16);

impl Size {
    fn new(v: u16) -> Result<Self, &'static str> {
        if v <= 200 { Ok(Self(v)) } else { Err("Out of range") }
    }
}
```

**Why it works**

* Invalid values cannot exist
* Eliminates repeated runtime checks
* Zero runtime overhead after validation

---

#### 2. Typestate Pattern (State Constraints)

```rust
struct Unvalidated;
struct Validated;

struct Input<State> {
    data: Vec<i32>,
    _state: std::marker::PhantomData<State>,
}
```

Used when:

* order matters
* state transitions must be enforced

---

#### 3. NonZero / NonEmpty Types

```rust
use std::num::NonZeroUsize;
```

Used heavily in:

* kernel code
* allocators
* crypto

---

### Rust Philosophy

> “Make illegal states unrepresentable.”

---

## 2. C++ (Assertions + RAII + Defensive Boundaries)

C++ relies on **discipline**, not enforcement.

### Core Patterns

#### 1. Constructor Validation

```cpp
class Size {
    int value;
public:
    explicit Size(int v) {
        if (v < 0 || v > 200) throw std::out_of_range("Invalid size");
        value = v;
    }
};
```

---

#### 2. Assertions for Invariants

```cpp
void process(int m) {
    assert(m <= 200); // programmer error
}
```

---

#### 3. Strong Typedefs

```cpp
using Index = int;
```

Better:

```cpp
struct Index {
    int value;
};
```

---

### C++ Philosophy

> “Trust the programmer, but verify aggressively.”

---

## 3. Go (Explicit Validation, Simplicity Over Safety)

Go does not have a strong type system for constraints.

### Core Patterns

#### 1. Validation at Boundaries

```go
func Validate(m int, n int) error {
    if m < 0 || m > 200 {
        return errors.New("m out of range")
    }
    return nil
}
```

---

#### 2. Error-as-Value Discipline

```go
if err := Validate(m, n); err != nil {
    return err
}
```

---

#### 3. Struct-Level Validation

```go
type Input struct {
    M int
    N int
}

func (i Input) Validate() error {
    if i.M+i.N > 200 {
        return errors.New("size exceeded")
    }
    return nil
}
```

---

### Go Philosophy

> “Clarity over cleverness. Validate once, trust later.”

---

## 4. Python (Runtime Contracts, Fast Failure)

Python is **dynamic**, so discipline matters most.

### Core Patterns

#### 1. Guard Clauses

```python
def process(nums, m):
    if m > 200:
        raise ValueError("m out of range")
```

---

#### 2. Dataclass Validation

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Input:
    m: int

    def __post_init__(self):
        if not 0 <= self.m <= 200:
            raise ValueError("Invalid m")
```

---

#### 3. Assertion for Internal Invariants

```python
assert len(nums) == m + n
```

---

### Python Philosophy

> “Fail fast, fail loud, validate everything.”

---

# II. Security-Focused Constraint Handling

Constraints are **security boundaries**.

### Security-Critical Constraint Types

| Constraint | Exploit If Broken |
| ---------- | ----------------- |
| Size       | Buffer overflow   |
| Index      | Memory corruption |
| Range      | Integer overflow  |
| Structure  | Logic bypass      |
| Ordering   | TOCTOU            |

---

### Secure Coding Rules

1. **Never trust external input**
2. **Validate before allocation**
3. **Check integer overflow**
4. **Reject, never clamp**

#### Example (C)

```c
if (size > MAX_SIZE) return ERROR;
buffer = malloc(size); // safe
```

---

### Kernel Rule

> “Validate before use, assert after.”

---

# III. Performance-Critical Constraint Elimination

### Problem

Repeated checks in hot loops kill performance.

### Solution

**Validate once, encode validity into types.**

---

### Pattern: One-Time Validation

```rust
struct ValidatedInput {
    nums: Vec<i32>,
}

fn process(v: ValidatedInput) {
    // no checks needed
}
```

---

### Pattern: Debug-Only Assertions

```cpp
#ifdef DEBUG
assert(size <= 200);
#endif
```

---

### Pattern: Branch Elimination

```c
// bad
for (...) {
    if (i < n) { ... }
}

// good
assert(n <= MAX);
for (int i = 0; i < n; i++) { ... }
```

---

### Performance Rule

> “Constraints should disappear after validation.”

---

# IV. How Google, Meta, and Kernel Code Handle Constraints

## 1. Linux Kernel

### Practices

* `WARN_ON()` for recoverable issues
* `BUG_ON()` for fatal invariants
* Extensive bounds checking before memory access

```c
BUG_ON(size > MAX_SIZE);
```

Kernel philosophy:

> “Crashing early is safer than corrupting memory.”

---

## 2. Google

### Internal Practices

* Heavy use of **static analysis**
* `CHECK()` macros (fatal)
* `DCHECK()` (debug only)

```cpp
CHECK(m <= 200);
```

They assume:

* inputs validated at API edges
* internal code is trusted

---

## 3. Meta (Facebook)

### Practices

* Schema-driven validation
* Hack / Flow type enforcement
* Runtime guards for user input

Philosophy:

> “Types for correctness, runtime checks for safety.”

---

## 4. Common Industry Pattern

```text
[Edge Validation]
   ↓
[Strongly Typed Domain Objects]
   ↓
[High-Performance Core]
```

---

# V. Unified Mental Model

### Constraint Hierarchy

```
Security > Correctness > Performance > Convenience
```

### Golden Rules

1. Validate at boundaries
2. Encode constraints in types
3. Assert invariants internally
4. Eliminate checks in hot paths
5. Log violations
6. Never ignore a violation

---

## Final Statement

> **Elite systems do not “handle” constraints — they are built so constraints cannot be violated.**

If you want next:

* a full **constraint-handling framework**
* reverse-engineering constraint failures in real CVEs
* converting LeetCode solutions into production systems
* kernel-style validation macros for your own codebase

Specify your next focus.

Below is a **comprehensive, real-world guide** to writing **constraint-aware, production-ready code**. This is not LeetCode advice; it reflects how constraints are handled in **large codebases, security-sensitive systems, and high-reliability software**.

---

# 1. What “Constraints” Mean in Real-World Software

In production, a constraint is **not**:

* Just a comment
* Just an `if` statement
* Just a unit test

A constraint is a **contract** that must hold across:

* APIs
* Data models
* Business logic
* Storage
* Distributed boundaries

### Categories of Constraints

| Category    | Examples                 |
| ----------- | ------------------------ |
| Structural  | lengths, shapes, schemas |
| Value range | min/max, bounds          |
| Relational  | `len == m + n`           |
| Temporal    | order of operations      |
| Security    | taint, trust levels      |
| Performance | max sizes                |
| Resource    | memory, CPU              |
| Invariants  | “must always be true”    |

---

# 2. Constraint Lifecycle (Critical Concept)

Constraints have a **lifecycle**, not a location.

```
Define → Validate → Enforce → Assume → Monitor
```

Most bugs happen when:

* constraints are validated late
* constraints are re-validated redundantly
* constraints are silently ignored

---

# 3. Where Constraints Must Live (Architecture)

### Golden Rule

> **Validate at system boundaries, assume inside.**

### Boundary Examples

| Boundary   | Validate Here      |
| ---------- | ------------------ |
| REST API   | JSON schema        |
| CLI        | argument parsing   |
| File input | parser             |
| Network    | protocol decoder   |
| User input | frontend + backend |

### Core Logic

```text
[Untrusted Input]
      ↓ validate
[Trusted Domain Objects]
      ↓ no checks
[Algorithms]
```

---

# 4. Constraint Expression Layers (Stacked)

Production systems use **multiple layers simultaneously**.

| Layer           | Purpose             |
| --------------- | ------------------- |
| Documentation   | Human understanding |
| Type System     | Compile-time safety |
| Validation Code | Runtime safety      |
| Assertions      | Programmer errors   |
| Tests           | Regression safety   |
| Monitoring      | Runtime detection   |

---

# 5. Documentation Is a Contract (Not Optional)

Use **precise language**.

Bad:

```
m and n are small
```

Good:

```
0 ≤ m, n ≤ 200
len(nums1) == m + n
```

Documentation drives:

* code review
* test generation
* API usage
* security analysis

---

# 6. Type-Level Constraints (Best ROI)

### Goal

Make **invalid states unrepresentable**.

### Example: Size-Bounded Type

#### Rust

```rust
struct Size(u16);

impl Size {
    fn new(v: u16) -> Result<Self, &'static str> {
        if v <= 200 {
            Ok(Self(v))
        } else {
            Err("Size exceeds limit")
        }
    }
}
```

Now:

* `Size` cannot exceed 200
* no repeated checks

---

### Example: Non-Empty Collection

```rust
struct NonEmptyVec<T>(Vec<T>);

impl<T> NonEmptyVec<T> {
    fn new(v: Vec<T>) -> Result<Self, &'static str> {
        if v.is_empty() {
            Err("Must not be empty")
        } else {
            Ok(Self(v))
        }
    }
}
```

---

# 7. Runtime Validation Patterns

### Pattern 1: Guard Clauses (Preferred)

```python
def process(nums):
    if not nums:
        raise ValueError("nums must not be empty")
```

* shallow
* readable
* early failure

---

### Pattern 2: Validator Objects (Scalable)

```python
class MergeValidator:
    @staticmethod
    def validate(nums1, m, nums2, n):
        if len(nums1) != m + n:
            raise ValueError("Invalid length")
```

Used when:

* many constraints
* reused across modules

---

### Pattern 3: Schema Validation (APIs)

* OpenAPI
* JSON Schema
* Protobuf

```json
{
  "type": "array",
  "maxItems": 200
}
```

---

# 8. Assertions vs Validation (Critical Distinction)

| Aspect         | Validation        | Assertion          |
| -------------- | ----------------- | ------------------ |
| Triggered by   | User/system input | Programmer mistake |
| Exists in prod | Yes               | Optional           |
| Recoverable    | Yes               | No                 |

### Example

```cpp
assert(m <= 200);          // programmer error
if (m > 200) return err;  // user error
```

---

# 9. Error Handling Strategy

Production constraints must be:

* explicit
* actionable
* logged

### Bad

```text
Invalid input
```

### Good

```text
nums1 length 10 does not match m+n = 12
```

---

# 10. Constraint Composition (Advanced)

Constraints often depend on other constraints.

Example:

```
len(nums1) == m + n
m + n ≤ MAX_SIZE
```

Implementation:

```python
total = m + n
if total > MAX_SIZE:
    raise ValueError("Total size exceeds limit")

if len(nums1) != total:
    raise ValueError("nums1 length mismatch")
```

Order matters:

* cheap checks first
* dependent checks later

---

# 11. Avoid Common Anti-Patterns

### ❌ Scatter Checks Everywhere

```python
if m > 200: ...
if m > 200: ...
```

### ❌ Silent Clamping

```python
m = min(m, 200)
```

### ❌ Relying Only on Tests

Tests do not enforce runtime safety.

---

# 12. Performance-Aware Constraints

In hot paths:

* validate once
* store validated state
* reuse

Example:

```python
validated = ValidatedInput(nums1, m, nums2, n)
process(validated)
```

---

# 13. Security Perspective

Constraints are a **security boundary**.

Unchecked constraints lead to:

* buffer overflows
* integer overflow
* DoS attacks

Security rule:

> **Every constraint violation is a potential exploit.**

---

# 14. Monitoring & Runtime Detection

Production systems log constraint violations:

* frequency
* source
* payload size

Used to detect:

* abuse
* malformed clients
* integration bugs

---

# 15. Testing Constraints Properly

Test **failure cases explicitly**.

```python
def test_length_violation():
    with pytest.raises(ValueError):
        validate(nums1=[1], m=2, nums2=[], n=0)
```

Use:

* boundary values
* fuzz testing
* property-based tests

---

# 16. Formal Methods (Elite Tier)

Used in:

* kernels
* avionics
* cryptography

Tools:

* Dafny
* SPARK
* Coq
* TLA+

You mathematically prove constraints cannot be violated.

---

# 17. Minimal Production Template

```text
1. Define constraints explicitly
2. Validate at entry
3. Convert to domain types
4. Assume validity internally
5. Assert invariants
6. Test violations
7. Monitor in production
```

---

# Final Principle

> **Constraints are not defensive programming; they are domain modeling.**

If you want next:

* constraint design patterns by language (Rust / C++ / Go / Python)
* security-focused constraint handling
* performance-critical constraint elimination
* how Google, Meta, or kernel code handles constraints

State your direction.

Below is a **comprehensive, real-world guide** to writing **constraint-safe, production-grade code**. This is not competitive-programming advice; it reflects how constraints are handled in **large systems, security-critical code, APIs, kernels, compilers, and backend services**.

---

# 1. What “Constraints” Mean in Real Systems

In production, constraints are **rules about valid states**, not just numbers.

They fall into five categories:

1. **Structural**

   * Lengths, shapes, formats
   * Example: `len(nums1) == m + n`

2. **Range**

   * Numeric bounds
   * Example: `0 ≤ m, n ≤ 200`

3. **Relational**

   * Relationships between values
   * Example: `nums2.length == n`

4. **Semantic**

   * Meaningful correctness
   * Example: `nums1` has `m` valid elements, rest are placeholders

5. **Temporal / Lifecycle**

   * When something is allowed
   * Example: initialized → validated → processed

**Good constraint code enforces all five.**

---

# 2. Where Constraints Belong (Critical Design Rule)

### ❌ Wrong

* Spread checks everywhere
* Validate deep inside loops
* Mix business logic and validation

### ✅ Correct Architecture

```text
┌──────────────┐
│ Input / API  │  ← validate here
└──────┬───────┘
       ↓
┌──────────────┐
│ Domain Model │  ← encode constraints
└──────┬───────┘
       ↓
┌──────────────┐
│ Core Logic   │  ← assume valid state
└──────────────┘
```

**Constraint checks happen ONCE at boundaries.**

---

# 3. Constraint Levels (Use the Right Tool)

| Level        | Tool            | Purpose                 |
| ------------ | --------------- | ----------------------- |
| Compile-time | Types, generics | Prevent invalid states  |
| Runtime      | Validation      | Reject bad input        |
| Debug        | Assertions      | Catch programmer bugs   |
| Test         | Property tests  | Prove coverage          |
| Formal       | Contracts       | Mathematical guarantees |

---

# 4. Compile-Time Constraints (Best Possible)

### Goal

> **Make invalid states unrepresentable**

### Example: Bounded Type (Rust-style concept)

```rust
struct BoundedUsize<const MAX: usize>(usize);

impl<const MAX: usize> BoundedUsize<MAX> {
    fn new(value: usize) -> Result<Self, &'static str> {
        if value <= MAX {
            Ok(Self(value))
        } else {
            Err("Out of bounds")
        }
    }
}
```

Now:

* `m` **cannot exceed 200**
* Checks occur **once**
* No runtime overhead later

---

# 5. Runtime Validation (Production Standard)

### Principle

Validate **all external input**. Assume **nothing**.

### Python (Clean Pattern)

```python
def validate_merge_inputs(nums1, m, nums2, n):
    if not isinstance(nums1, list) or not isinstance(nums2, list):
        raise TypeError("Inputs must be lists")

    if len(nums1) != m + n:
        raise ValueError("nums1 length mismatch")

    if len(nums2) != n:
        raise ValueError("nums2 length mismatch")

    if not (0 <= m <= 200 and 0 <= n <= 200):
        raise ValueError("m, n out of range")

    if not (1 <= m + n <= 200):
        raise ValueError("Invalid total size")

    for x in nums1[:m] + nums2:
        if not -10**9 <= x <= 10**9:
            raise ValueError("Value out of bounds")
```

**Rules**

* Validate structure first
* Validate ranges second
* Validate semantics last

---

# 6. Assertions ≠ Validation (Critical Difference)

### Use assertions when:

* Violation means **programmer error**
* Code should never reach this state

### C Example

```c
assert(m >= 0 && m <= 200);
```

### Never use assertions for:

* User input
* Network data
* File parsing

Assertions can be disabled in production.

---

# 7. Encoding Constraints in Domain Models (Elite Practice)

### Bad

```python
def merge(nums1, m, nums2, n):
    ...
```

### Good

```python
@dataclass(frozen=True)
class MergeInput:
    nums1: list[int]
    nums2: list[int]
    m: int
    n: int

    def __post_init__(self):
        validate_merge_inputs(self.nums1, self.m, self.nums2, self.n)
```

Now:

* Invalid objects **cannot exist**
* Core logic stays clean
* Constraints are centralized

---

# 8. Fail Fast, Fail Loud, Fail Early

### Good Error Design

```text
❌ "Invalid input"
✅ "nums1 length (5) must equal m + n (3)"
```

This:

* Speeds debugging
* Prevents silent corruption
* Improves observability

---

# 9. Performance-Aware Constraint Checks

### Rule

> Validate once, trust afterward

### Bad

```python
for i in range(m):
    if i >= len(nums1): raise Error
```

### Good

```python
validate(...)
for i in range(m):
    ...
```

Constraint checks should be **O(1)** or **O(n) once**.

---

# 10. Constraints in Security-Critical Code

### Additional Rules

* Reject on overflow
* Avoid implicit casting
* Check before allocation
* Validate before memcpy

### C Example

```c
if (m > 200 || n > 200) return ERROR;
if (m + n > 200) return ERROR;
if (nums1_len != m + n) return ERROR;
```

Order matters to prevent overflow.

---

# 11. Testing Constraints (Non-Negotiable)

### Boundary Tests

```python
def test_min_bounds():
    merge([0], 1, [], 0)

def test_max_bounds():
    merge([0]*200, 200, [], 0)
```

### Property-Based Tests

```python
from hypothesis import given, strategies as st
```

This catches cases you didn’t think of.

---

# 12. Constraints in APIs & Microservices

### API Layer

* JSON schema
* OpenAPI validation
* Reject malformed input

### Domain Layer

* Strong types
* Value objects

### Core Layer

* No checks
* Pure logic

---

# 13. Common Anti-Patterns (Avoid These)

❌ Trusting documentation only
❌ Validating deep inside logic
❌ Using comments instead of code
❌ Ignoring relational constraints
❌ Over-validating inside loops

---

# 14. Mental Model (Very Important)

Think in **states**, not values.

```text
Raw Input
   ↓
Validated Input
   ↓
Domain Object
   ↓
Algorithm
```

Each transition **reduces uncertainty**.

---

# 15. Production Constraint Checklist

Before shipping, verify:

* [ ] All external inputs validated
* [ ] Constraints centralized
* [ ] Domain objects enforce invariants
* [ ] Assertions used only for bugs
* [ ] Tests cover boundaries
* [ ] Errors are explicit
* [ ] Invalid states are impossible

---

## Final Principle

> **Constraints are part of your program’s correctness, not an afterthought.**

If you want next:

* A reusable constraint-validation framework
* Rust-first constraint design
* Security-oriented constraint patterns (kernel / exploit-safe code)
* Formal methods and contracts

State which direction you want.

In production-ready code, **constraints are not just comments**. They are enforced through a combination of **type design, validation, defensive checks, contracts, and tests**. Below is a structured, industry-grade approach, using your constraints as the concrete example.

---

## 1. Document Constraints Clearly (Non-Executable, but Required)

Every production system starts with **explicit documentation**. This is usually placed in:

* Function docstrings
* API contracts
* Interface definitions
* Design specs

### Example (language-agnostic)

```text
Constraints:
- nums1.length == m + n
- nums2.length == n
- 0 ≤ m, n ≤ 200
- 1 ≤ m + n ≤ 200
- -1e9 ≤ nums1[i], nums2[j] ≤ 1e9
```

Documentation alone is **never sufficient**, but it is mandatory.

---

## 2. Enforce Constraints at Runtime (Input Validation Layer)

This is the **minimum bar** for production code.

### Python (Defensive Programming)

```python
def merge(nums1: list[int], m: int, nums2: list[int], n: int) -> None:
    # Structural constraints
    if len(nums1) != m + n:
        raise ValueError("nums1 length must be m + n")

    if len(nums2) != n:
        raise ValueError("nums2 length must be n")

    # Range constraints
    if not (0 <= m <= 200 and 0 <= n <= 200):
        raise ValueError("m and n must be in range [0, 200]")

    if not (1 <= m + n <= 200):
        raise ValueError("m + n must be in range [1, 200]")

    # Element constraints
    for x in nums1[:m]:
        if not (-10**9 <= x <= 10**9):
            raise ValueError("nums1 element out of bounds")

    for x in nums2:
        if not (-10**9 <= x <= 10**9):
            raise ValueError("nums2 element out of bounds")

    # Core logic continues...
```

This is **production-acceptable** for internal services.

---

## 3. Prefer Design-Time Guarantees (Types & Contracts)

Production systems aim to **prevent invalid states** rather than detect them late.

### Rust (Strong Guarantees)

```rust
fn merge(
    nums1: &mut Vec<i32>,
    m: usize,
    nums2: &Vec<i32>,
    n: usize,
) -> Result<(), String> {
    if nums1.len() != m + n {
        return Err("nums1 length must be m + n".into());
    }
    if nums2.len() != n {
        return Err("nums2 length must be n".into());
    }
    if m > 200 || n > 200 || m + n == 0 || m + n > 200 {
        return Err("Invalid size constraints".into());
    }
    Ok(())
}
```

Rust’s type system ensures:

* No nulls
* No out-of-bounds access
* Clear ownership rules

---

## 4. Use Assertions for Internal Invariants

Assertions are used when **violations indicate programmer bugs**, not user errors.

### C++ Example

```cpp
#include <cassert>

void merge(vector<int>& nums1, int m, vector<int>& nums2, int n) {
    assert(nums1.size() == m + n);
    assert(nums2.size() == n);
    assert(m >= 0 && m <= 200);
    assert(n >= 0 && n <= 200);
    assert(m + n >= 1 && m + n <= 200);
}
```

Use:

* `assert` → internal invariants
* exceptions / error codes → user input errors

---

## 5. Encode Constraints via Domain Types (Best Practice)

This is **elite-level production design**.

### Example: Bounded Integer Type

#### Rust

```rust
struct BoundedSize(usize);

impl BoundedSize {
    fn new(value: usize) -> Result<Self, String> {
        if value <= 200 {
            Ok(Self(value))
        } else {
            Err("Value exceeds max size".into())
        }
    }
}
```

Now invalid values **cannot exist**.

---

## 6. Contract-Based Programming (Modern Systems)

### Example: Using Preconditions (Pseudo-Code)

```text
requires:
  len(nums1) == m + n
  len(nums2) == n
  0 ≤ m, n ≤ 200
  1 ≤ m + n ≤ 200
```

Languages / tools:

* Eiffel
* Ada
* Dafny
* SPARK
* Formal verification systems

---

## 7. Validate at System Boundaries Only

**Do not scatter checks everywhere.**

Correct architecture:

```text
[API Boundary]
     ↓ (validate constraints)
[Domain Logic]
     ↓ (assumes valid state)
[Algorithm]
```

This avoids:

* Redundant checks
* Performance degradation
* Code noise

---

## 8. Test Constraints Explicitly

Production readiness requires **tests for constraint violations**.

### Example (Python / pytest)

```python
import pytest

def test_invalid_length():
    with pytest.raises(ValueError):
        merge([1,2], 1, [3], 1)
```

---

## Summary: Production-Grade Constraint Strategy

| Layer          | Technique                  |
| -------------- | -------------------------- |
| Documentation  | Explicit constraints       |
| API Boundary   | Runtime validation         |
| Domain Model   | Strong types               |
| Internal Logic | Assertions                 |
| Architecture   | Single validation entry    |
| Testing        | Constraint violation tests |

---

### Key Rule

> **Constraints should be impossible to violate by construction, and detectable when they are.**

If you want, I can:

* Refactor your LeetCode-style solution into production-grade architecture
* Show a zero-overhead Rust solution
* Provide a reusable validation framework template

State your preference.
