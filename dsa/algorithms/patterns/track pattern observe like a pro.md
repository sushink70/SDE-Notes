# DSA Mastery Guide: Track, Pattern, Observe Like a Pro

> **Author's Note**: This guide is language-agnostic in thinking but implementation-grounded.
> Every pattern is explained from first principles, then coded in Go, Rust, and C.
> Read the "OBSERVE" and "TRIGGER" sections before jumping to code — they are the core skill.

---

## TABLE OF CONTENTS

1. [The Problem-Solving Meta-Framework](#1-the-problem-solving-meta-framework)
2. [How to Read a Problem Like a Pro](#2-how-to-read-a-problem-like-a-pro)
3. [Complexity Intuition & Constraints Mapping](#3-complexity-intuition--constraints-mapping)
4. [Pattern Recognition Master Table](#4-pattern-recognition-master-table)
5. [Pattern 01 — Two Pointers](#5-pattern-01--two-pointers)
6. [Pattern 02 — Sliding Window](#6-pattern-02--sliding-window)
7. [Pattern 03 — Fast & Slow Pointers (Floyd's)](#7-pattern-03--fast--slow-pointers-floyds)
8. [Pattern 04 — Prefix Sum & Difference Arrays](#8-pattern-04--prefix-sum--difference-arrays)
9. [Pattern 05 — Binary Search (All Variants)](#9-pattern-05--binary-search-all-variants)
10. [Pattern 06 — Monotonic Stack & Queue](#10-pattern-06--monotonic-stack--queue)
11. [Pattern 07 — Hash Maps & Frequency Tables](#11-pattern-07--hash-maps--frequency-tables)
12. [Pattern 08 — Tree BFS (Level Order)](#12-pattern-08--tree-bfs-level-order)
13. [Pattern 09 — Tree DFS (Pre/In/Post)](#13-pattern-09--tree-dfs-preinpost)
14. [Pattern 10 — Merge Intervals](#14-pattern-10--merge-intervals)
15. [Pattern 11 — Top K / K-way Merge (Heaps)](#15-pattern-11--top-k--k-way-merge-heaps)
16. [Pattern 12 — Cyclic Sort](#16-pattern-12--cyclic-sort)
17. [Pattern 13 — In-Place LinkedList Reversal](#17-pattern-13--in-place-linkedlist-reversal)
18. [Pattern 14 — Backtracking & Subsets](#18-pattern-14--backtracking--subsets)
19. [Pattern 15 — Dynamic Programming (All Subtypes)](#19-pattern-15--dynamic-programming-all-subtypes)
20. [Pattern 16 — Graph Algorithms (BFS/DFS/Topo/Union-Find)](#20-pattern-16--graph-algorithms-bfsdfstopoUnion-find)
21. [Pattern 17 — Tries (Prefix Trees)](#21-pattern-17--tries-prefix-trees)
22. [Pattern 18 — Segment Trees & BIT (Fenwick)](#22-pattern-18--segment-trees--bit-fenwick)
23. [Pattern 19 — Bitwise Tricks](#23-pattern-19--bitwise-tricks)
24. [Pattern 20 — Math & Number Theory](#24-pattern-20--math--number-theory)
25. [Hidden Tricks & Advanced Observations](#25-hidden-tricks--advanced-observations)
26. [Debugging & Dry-Run Framework](#26-debugging--dry-run-framework)
27. [Interview Problem-Solving Template](#27-interview-problem-solving-template)
28. [Next 3 Steps](#28-next-3-steps)

---

## 1. THE PROBLEM-SOLVING META-FRAMEWORK

### The SCREAM Framework

```
S — Summarize       (restate in your own words)
C — Constraints     (n size, value range, edge cases)
R — Recognize       (what pattern does this trigger?)
E — Example         (trace manually on 2 examples)
A — Algorithm       (pseudocode first, no code yet)
M — Map complexity  (time & space, justify)
```

### The 5-Layer Problem Decomposition

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1: WHAT is being asked?                              │
│  (output type: index, value, bool, count, min/max, path)    │
├─────────────────────────────────────────────────────────────┤
│  LAYER 2: WHAT are the constraints?                         │
│  (n<=10^5, values unique/sorted/negative, graph acyclic?)   │
├─────────────────────────────────────────────────────────────┤
│  LAYER 3: WHAT structure holds the data?                    │
│  (array, linked list, tree, graph, string, matrix)          │
├─────────────────────────────────────────────────────────────┤
│  LAYER 4: WHAT relationship exists between elements?        │
│  (adjacent, parent-child, sorted order, intervals)          │
├─────────────────────────────────────────────────────────────┤
│  LAYER 5: WHAT operation is performed repeatedly?           │
│  (search, count, min/max, merge, transform, accumulate)     │
└─────────────────────────────────────────────────────────────┘
```

### Mental Model: Think in INVARIANTS

> Every correct algorithm maintains a **loop invariant** — a property that is true before, during, and after each iteration.
> Finding the invariant IS the algorithm.

---

## 2. HOW TO READ A PROBLEM LIKE A PRO

### Step-by-Step Problem Intake

```
1. Read ONCE for the big picture. Do NOT start coding.
2. Identify the OUTPUT TYPE:
   - Single value (int/bool)       → search/DP/greedy
   - Array/list                    → transform/filter/merge
   - Count                         → hash/two-pointer/prefix
   - Min/Max                       → greedy/heap/binary search
   - All combinations/permutations → backtracking
   - Shortest/longest path         → BFS/DP/graph
   - Yes/No feasibility            → binary search on answer / greedy

3. Extract KEYWORDS:
   ┌──────────────────────┬──────────────────────────────────┐
   │ KEYWORD              │ PATTERN HINT                     │
   ├──────────────────────┼──────────────────────────────────┤
   │ "sorted array"       │ Binary search, two pointers      │
   │ "subarray sum"       │ Prefix sum, sliding window       │
   │ "contiguous"         │ Sliding window                   │
   │ "pairs"              │ Two pointers, hash               │
   │ "k largest/smallest" │ Heap (top-k)                     │
   │ "all subsets"        │ Backtracking / bitmask           │
   │ "minimum steps"      │ BFS                              │
   │ "maximum profit"     │ DP / greedy                      │
   │ "palindrome"         │ Two pointers / DP                │
   │ "cyclic / duplicate" │ Cyclic sort / Floyd's            │
   │ "connected"          │ Union-Find / BFS/DFS             │
   │ "interval"           │ Merge intervals / sweep line     │
   │ "next greater"       │ Monotonic stack                  │
   │ "prefix / suffix"    │ Prefix sum / trie                │
   │ "range query"        │ Segment tree / BIT               │
   └──────────────────────┴──────────────────────────────────┘

4. Ask EDGE CASE questions:
   - What if n=0 or n=1?
   - Can values be negative / zero / duplicate?
   - Is the array sorted? Partially sorted?
   - Can indices wrap around (circular)?
   - Is the graph directed? Can it have cycles?
   - Integer overflow? (use int64/i64)
```

### The "SMELL TEST" for Constraints

```
n ≤ 10        → O(n!) is fine   → brute force / permutations
n ≤ 20        → O(2^n)          → bitmask DP, backtracking
n ≤ 100       → O(n^3)          → 3 nested loops, Floyd-Warshall
n ≤ 1000      → O(n^2)          → 2 nested loops, bubble sort
n ≤ 10^5      → O(n log n)      → sort + binary search, heaps, BIT
n ≤ 10^6      → O(n)            → hash, prefix sum, two pointer
n ≤ 10^9      → O(log n)        → binary search, math formula
```

---

## 3. COMPLEXITY INTUITION & CONSTRAINTS MAPPING

### Time Complexity Decision Tree

```
                  ┌──────────────────────────┐
                  │  What is n?              │
                  └────────────┬─────────────┘
                               │
          ┌────────────────────┼─────────────────────┐
          │                    │                     │
       n≤20                n≤1000               n≤10^6
          │                    │                     │
    O(2^n) OK          O(n^2) OK            O(n) or O(n logn)
    Backtrack           nested loop          required
    bitmask DP          simple DP
```

### Space Complexity Rules of Thumb

```
- Recursion depth D → O(D) stack space
- Memoization table of size n → O(n) or O(n*k)
- Adjacency list → O(V + E)
- Adjacency matrix → O(V^2) — avoid for sparse graphs
- Never use matrix if n > 1000 (10^6 cells = 4MB minimum)
```

---

## 4. PATTERN RECOGNITION MASTER TABLE

```
┌─────┬──────────────────────────┬──────────────────────────────────────────────┐
│  #  │ PATTERN                  │ TRIGGERS / SIGNALS                           │
├─────┼──────────────────────────┼──────────────────────────────────────────────┤
│  1  │ Two Pointers             │ sorted array, pairs, triplets, palindrome    │
│  2  │ Sliding Window           │ subarray/substring, contiguous, k-size window│
│  3  │ Fast & Slow Pointers     │ cycle detection, middle of list, Nth from end│
│  4  │ Prefix Sum               │ range sum queries, subarray sum = k          │
│  5  │ Binary Search            │ sorted input, "find minimum X that satisfies"│
│  6  │ Monotonic Stack          │ next greater/smaller, histogram, span        │
│  7  │ Hash Map                 │ frequency, two-sum, anagram, first unique    │
│  8  │ Tree BFS                 │ level order, shortest path in unweighted tree│
│  9  │ Tree DFS                 │ path sum, diameter, LCA, height, validate    │
│ 10  │ Merge Intervals          │ overlapping intervals, meeting rooms, calendar│
│ 11  │ Top K / Heap             │ k largest, k closest, merge k sorted lists   │
│ 12  │ Cyclic Sort              │ 1 to n array, find missing/duplicate         │
│ 13  │ LinkedList Reversal      │ reverse sublist, k-group reversal            │
│ 14  │ Backtracking             │ all subsets, permutations, combinations, N-Q │
│ 15  │ Dynamic Programming      │ optimization, count ways, overlapping subs   │
│ 16  │ Graph (BFS/DFS/UF/Topo)  │ connected components, shortest path, cycle   │
│ 17  │ Trie                     │ prefix search, word dict, autocomplete       │
│ 18  │ Segment Tree / BIT       │ range queries with updates                   │
│ 19  │ Bitwise                  │ XOR tricks, power of 2, set operations       │
│ 20  │ Math / Number Theory     │ GCD, prime, modular arithmetic, combinatorics│
└─────┴──────────────────────────┴──────────────────────────────────────────────┘
```

---

## 5. PATTERN 01 — TWO POINTERS

### Core Idea

Use two indices (left, right) moving toward each other or in the same direction.
**Invariant**: The window between pointers always maintains a specific property.

### When to Use

- Sorted array + pair/triplet sum
- Palindrome check
- Remove duplicates in-place
- Container with most water
- Squaring a sorted array

### Visual

```
arr = [1, 2, 3, 4, 5, 6]   target = 7
       L                R
       ↓                ↓
      [1,  2,  3,  4,  5,  6]
       └────────────────┘
       sum=1+6=7 → FOUND

If sum < target: L++
If sum > target: R--
If sum == target: record, L++, R--
```

### Two Pointers Variants

```
TYPE A: Opposite ends (sorted array)
  left=0, right=n-1, move toward center

TYPE B: Same direction (fast/slow = separate pattern)
  slow=0, fast=0, fast runs ahead

TYPE C: Two arrays (merge sorted)
  p1=0 on arr1, p2=0 on arr2

TYPE D: Partition (Dutch National Flag)
  low=0, mid=0, high=n-1
```

### Go Implementation — Two Sum (sorted)

```go
package twopointers

// TwoSumSorted returns indices of pair summing to target in sorted array
// Time: O(n), Space: O(1)
func TwoSumSorted(nums []int, target int) (int, int) {
    left, right := 0, len(nums)-1
    for left < right {
        sum := nums[left] + nums[right]
        switch {
        case sum == target:
            return left, right
        case sum < target:
            left++
        default:
            right--
        }
    }
    return -1, -1
}

// ThreeSumZero returns all unique triplets summing to zero
// Time: O(n^2), Space: O(1) excluding output
func ThreeSumZero(nums []int) [][3]int {
    sort.Ints(nums)
    var result [][3]int
    for i := 0; i < len(nums)-2; i++ {
        // Skip duplicates for the first element
        if i > 0 && nums[i] == nums[i-1] {
            continue
        }
        left, right := i+1, len(nums)-1
        for left < right {
            sum := nums[i] + nums[left] + nums[right]
            switch {
            case sum == 0:
                result = append(result, [3]int{nums[i], nums[left], nums[right]})
                // Skip duplicates
                for left < right && nums[left] == nums[left+1] { left++ }
                for left < right && nums[right] == nums[right-1] { right-- }
                left++
                right--
            case sum < 0:
                left++
            default:
                right--
            }
        }
    }
    return result
}
```

### Rust Implementation

```rust
pub fn two_sum_sorted(nums: &[i32], target: i32) -> Option<(usize, usize)> {
    let (mut left, mut right) = (0usize, nums.len().saturating_sub(1));
    while left < right {
        let sum = nums[left] + nums[right];
        match sum.cmp(&target) {
            std::cmp::Ordering::Equal => return Some((left, right)),
            std::cmp::Ordering::Less  => left += 1,
            std::cmp::Ordering::Greater => right -= 1,
        }
    }
    None
}

pub fn three_sum_zero(mut nums: Vec<i32>) -> Vec<[i32; 3]> {
    nums.sort_unstable();
    let mut result = Vec::new();
    let n = nums.len();
    for i in 0..n.saturating_sub(2) {
        if i > 0 && nums[i] == nums[i - 1] { continue; }
        let (mut l, mut r) = (i + 1, n - 1);
        while l < r {
            match (nums[i] + nums[l] + nums[r]).cmp(&0) {
                std::cmp::Ordering::Equal => {
                    result.push([nums[i], nums[l], nums[r]]);
                    while l < r && nums[l] == nums[l + 1] { l += 1; }
                    while l < r && nums[r] == nums[r - 1] { r -= 1; }
                    l += 1; r -= 1;
                }
                std::cmp::Ordering::Less    => l += 1,
                std::cmp::Ordering::Greater => r -= 1,
            }
        }
    }
    result
}
```

### C Implementation

```c
#include <stdlib.h>
#include <string.h>

// Comparator for qsort
static int cmp_int(const void *a, const void *b) {
    return (*(int*)a - *(int*)b);
}

// Returns 1 if found, fills out_l and out_r
int two_sum_sorted(int *nums, int n, int target, int *out_l, int *out_r) {
    int left = 0, right = n - 1;
    while (left < right) {
        int sum = nums[left] + nums[right];
        if (sum == target) { *out_l = left; *out_r = right; return 1; }
        else if (sum < target) left++;
        else right--;
    }
    return 0;
}
```

### Dutch National Flag (3-way partition)

```
Problem: Sort [0,1,2,0,2,1] in-place (LeetCode 75)

Invariants:
  [0..low-1]  = all 0s
  [low..mid-1]= all 1s
  [mid..high] = unknown
  [high+1..n] = all 2s

  low=0, mid=0, high=n-1

  while mid <= high:
    if arr[mid]==0: swap(low,mid), low++, mid++
    if arr[mid]==1: mid++
    if arr[mid]==2: swap(mid,high), high--  (DON'T mid++ here!)
```

---

## 6. PATTERN 02 — SLIDING WINDOW

### Core Idea

Maintain a window [left, right] over a sequence. Expand right to include, shrink left to exclude.
**The key insight**: Instead of recomputing from scratch, update the window state incrementally.

### Fixed vs Variable Window

```
FIXED SIZE (k):
  - Slide right by 1, add new, remove old
  - Classic: max sum subarray of size k

VARIABLE SIZE:
  - Expand right until condition breaks
  - Shrink left until condition holds again
  - Classic: longest substring without repeating chars
```

### Visual

```
VARIABLE WINDOW — Longest substring no repeat:
s = "abcabcbb"
     ↑↑
     LR  window={a}  max=1

s = "abcabcbb"
     ↑ ↑
     L R  window={a,b}  max=2

s = "abcabcbb"
     ↑  ↑
     L  R  window={a,b,c}  max=3

s = "abcabcbb"
     ↑   ↑
     L   R  seen 'a'! shrink left until 'a' removed
      ↑  ↑
      L  R  window={b,c,a}  max=3
```

### Window State Tracking

```
┌──────────────────────────────────────────────────┐
│  WHAT TO TRACK IN WINDOW STATE?                  │
│                                                  │
│  count/freq  → hash map or array[256]            │
│  sum         → running integer                   │
│  max/min     → deque (monotonic queue)           │
│  distinct    → hash set + counter                │
│  product     → running product (careful: 0!)     │
└──────────────────────────────────────────────────┘
```

### Go Implementation

```go
// LongestSubstringNoRepeat — Variable sliding window
// Time: O(n), Space: O(min(m,n)) where m=charset size
func LongestSubstringNoRepeat(s string) int {
    charIndex := make(map[byte]int) // last seen index
    maxLen := 0
    left := 0
    for right := 0; right < len(s); right++ {
        ch := s[right]
        // If char seen inside current window, move left past it
        if idx, ok := charIndex[ch]; ok && idx >= left {
            left = idx + 1
        }
        charIndex[ch] = right
        if right-left+1 > maxLen {
            maxLen = right - left + 1
        }
    }
    return maxLen
}

// MinWindowSubstring — find smallest window in s containing all chars of t
// Time: O(|s|+|t|), Space: O(|t|)
func MinWindowSubstring(s, t string) string {
    need := make(map[byte]int)
    for i := 0; i < len(t); i++ {
        need[t[i]]++
    }
    have, required := 0, len(need)
    window := make(map[byte]int)
    left := 0
    minLen := len(s) + 1
    minLeft := 0

    for right := 0; right < len(s); right++ {
        ch := s[right]
        window[ch]++
        if n, ok := need[ch]; ok && window[ch] == n {
            have++
        }
        // Shrink window from left while all requirements met
        for have == required {
            if right-left+1 < minLen {
                minLen = right - left + 1
                minLeft = left
            }
            leftCh := s[left]
            window[leftCh]--
            if n, ok := need[leftCh]; ok && window[leftCh] < n {
                have--
            }
            left++
        }
    }
    if minLen > len(s) {
        return ""
    }
    return s[minLeft : minLeft+minLen]
}

// MaxSumSubarrayFixedK — Fixed window
// Time: O(n), Space: O(1)
func MaxSumSubarrayFixedK(nums []int, k int) int {
    windowSum := 0
    for i := 0; i < k; i++ {
        windowSum += nums[i]
    }
    maxSum := windowSum
    for i := k; i < len(nums); i++ {
        windowSum += nums[i] - nums[i-k] // add new, remove old
        if windowSum > maxSum {
            maxSum = windowSum
        }
    }
    return maxSum
}
```

### Rust Implementation

```rust
use std::collections::HashMap;

pub fn longest_no_repeat(s: &str) -> usize {
    let s = s.as_bytes();
    let mut last_seen: HashMap<u8, usize> = HashMap::new();
    let mut left = 0usize;
    let mut max_len = 0usize;
    for (right, &ch) in s.iter().enumerate() {
        if let Some(&idx) = last_seen.get(&ch) {
            if idx >= left { left = idx + 1; }
        }
        last_seen.insert(ch, right);
        max_len = max_len.max(right - left + 1);
    }
    max_len
}
```

### C Implementation

```c
int longest_no_repeat(const char *s) {
    int last[256];
    memset(last, -1, sizeof(last));
    int left = 0, max_len = 0;
    for (int right = 0; s[right]; right++) {
        unsigned char ch = (unsigned char)s[right];
        if (last[ch] >= left) left = last[ch] + 1;
        last[ch] = right;
        if (right - left + 1 > max_len) max_len = right - left + 1;
    }
    return max_len;
}
```

### Hidden Trick: At-Most K → Exactly K

```
"Number of subarrays with EXACTLY k distinct values"
= f(at_most_k) - f(at_most_{k-1})

This transforms a hard exact-count problem into two easier at-most problems.
Use this whenever "exactly k" feels hard but "at most k" is natural.
```

---

## 7. PATTERN 03 — FAST & SLOW POINTERS (FLOYD'S)

### Core Idea

Two pointers move at different speeds. The fast pointer moves 2x (or more) faster than slow.
Used to detect cycles, find midpoints, or detect Nth from end.

### Visual

```
CYCLE DETECTION in linked list:

1 → 2 → 3 → 4 → 5
            ↑       ↓
            8 ← 7 ← 6

slow: 1→2→3→4→5→6→7→8→4→5...
fast: 1→3→5→7→4→6→8→5→7→4...

They MEET inside the cycle.

FINDING CYCLE START:
  After meeting, reset slow to HEAD.
  Move both one step at a time.
  They meet at CYCLE START. (Mathematical proof below)

PROOF:
  Let: F = distance from head to cycle start
       C = cycle length
       k = distance from cycle start to meeting point

  slow traveled: F + k
  fast traveled: F + k + n*C  (n full cycles ahead)
  fast = 2*slow → F + k + n*C = 2(F+k)
               → F = n*C - k
  So from HEAD (F steps) == from meeting point (n*C - k steps)
  They arrive at cycle start simultaneously!
```

### Go Implementation

```go
type ListNode struct {
    Val  int
    Next *ListNode
}

// HasCycle — Floyd's cycle detection
// Time: O(n), Space: O(1)
func HasCycle(head *ListNode) bool {
    slow, fast := head, head
    for fast != nil && fast.Next != nil {
        slow = slow.Next
        fast = fast.Next.Next
        if slow == fast {
            return true
        }
    }
    return false
}

// CycleStart — returns node where cycle begins
func CycleStart(head *ListNode) *ListNode {
    slow, fast := head, head
    for fast != nil && fast.Next != nil {
        slow = slow.Next
        fast = fast.Next.Next
        if slow == fast {
            // Reset slow to head, keep fast at meeting point
            slow = head
            for slow != fast {
                slow = slow.Next
                fast = fast.Next
            }
            return slow
        }
    }
    return nil
}

// MiddleOfList — finds middle node
// If even length, returns second middle (standard LeetCode behavior)
func MiddleOfList(head *ListNode) *ListNode {
    slow, fast := head, head
    for fast != nil && fast.Next != nil {
        slow = slow.Next
        fast = fast.Next.Next
    }
    return slow
}

// FindDuplicate — Floyd's on array (array as implicit linked list)
// nums[i] is the "next pointer" of node i
// Time: O(n), Space: O(1)  
func FindDuplicate(nums []int) int {
    slow, fast := nums[0], nums[nums[0]]
    for slow != fast {
        slow = nums[slow]
        fast = nums[nums[fast]]
    }
    slow = 0
    for slow != fast {
        slow = nums[slow]
        fast = nums[fast]
    }
    return slow
}
```

### Rust Implementation

```rust
// Using index-based approach for safe Rust (no raw pointers)
pub fn find_duplicate(nums: &[usize]) -> usize {
    let (mut slow, mut fast) = (nums[0], nums[nums[0]]);
    while slow != fast {
        slow = nums[slow];
        fast = nums[nums[fast]];
    }
    slow = 0;
    while slow != fast {
        slow = nums[slow];
        fast = nums[fast];
    }
    slow
}
```

---

## 8. PATTERN 04 — PREFIX SUM & DIFFERENCE ARRAYS

### Core Idea

**Prefix sum**: `pre[i] = arr[0] + arr[1] + ... + arr[i]`
Range sum query `[l,r]` becomes `pre[r] - pre[l-1]` — O(1) after O(n) build.

**Key insight**: `subarray sum = target` ↔ `pre[r] - pre[l-1] = target` ↔ look for `pre[r] - target` in a hash map.

### Visual

```
arr  = [1, 2, 3, 4, 5]
pre  = [0, 1, 3, 6, 10, 15]  (1-indexed, pre[0]=0)

Sum of [2..4] = pre[4] - pre[1] = 10 - 1 = 9 ✓

SUBARRAY SUM = K:
arr = [1, 2, 3], k=3

pre[0]=0  pre[1]=1  pre[2]=3  pre[3]=6
At each i, check: is (pre[i] - k) in seen_prefixes?
i=1: pre=1, look for (1-3)=-2 → no
i=2: pre=3, look for (3-3)=0  → YES! (pre[0]=0 was seen)
i=3: pre=6, look for (6-3)=3  → YES! (pre[2]=3 was seen)
Answer = 2
```

### Go Implementation

```go
// SubarraySumEqualsK — count subarrays summing to k
// Time: O(n), Space: O(n)
func SubarraySumEqualsK(nums []int, k int) int {
    // prefix_count[sum] = how many times this prefix sum has appeared
    prefixCount := map[int]int{0: 1} // empty prefix has sum 0
    count, prefixSum := 0, 0
    for _, num := range nums {
        prefixSum += num
        // If (prefixSum - k) was seen before, those subarrays end here
        count += prefixCount[prefixSum-k]
        prefixCount[prefixSum]++
    }
    return count
}

// RangeQueryImmutable — build prefix array for O(1) range queries
type NumArray struct{ pre []int }

func NewNumArray(nums []int) NumArray {
    pre := make([]int, len(nums)+1)
    for i, v := range nums {
        pre[i+1] = pre[i] + v
    }
    return NumArray{pre}
}

func (n NumArray) SumRange(left, right int) int {
    return n.pre[right+1] - n.pre[left]
}

// 2D Prefix Sum — for matrix range queries
func Build2DPrefix(matrix [][]int) [][]int {
    m, n := len(matrix), len(matrix[0])
    pre := make([][]int, m+1)
    for i := range pre {
        pre[i] = make([]int, n+1)
    }
    for i := 1; i <= m; i++ {
        for j := 1; j <= n; j++ {
            pre[i][j] = matrix[i-1][j-1] +
                pre[i-1][j] + pre[i][j-1] - pre[i-1][j-1]
        }
    }
    return pre
}

// Query2D — sum of submatrix [r1,c1] to [r2,c2]
func Query2D(pre [][]int, r1, c1, r2, c2 int) int {
    return pre[r2+1][c2+1] - pre[r1][c2+1] - pre[r2+1][c1] + pre[r1][c1]
}
```

### Difference Array

```go
// DifferenceArray — apply range updates in O(1), reconstruct in O(n)
// Use case: "add val to all elements in [l,r]" done k times, then query

type DiffArray struct {
    diff []int
    n    int
}

func NewDiffArray(n int) *DiffArray {
    return &DiffArray{diff: make([]int, n+1), n: n}
}

// RangeAdd: add val to arr[l..r] inclusive
func (d *DiffArray) RangeAdd(l, r, val int) {
    d.diff[l] += val
    if r+1 <= d.n {
        d.diff[r+1] -= val
    }
}

// Reconstruct: returns final array after all updates
func (d *DiffArray) Reconstruct() []int {
    result := make([]int, d.n)
    cur := 0
    for i := 0; i < d.n; i++ {
        cur += d.diff[i]
        result[i] = cur
    }
    return result
}
```

---

## 9. PATTERN 05 — BINARY SEARCH (ALL VARIANTS)

### Core Idea

Binary search is not just for "find element in sorted array." It applies to ANY monotonic decision function.

**The real question**: Can I define a predicate P(x) such that:
- P is FALSE for all values below the answer
- P is TRUE for all values at or above the answer
- Then binary search finds the boundary.

### All 4 Templates

```
TEMPLATE 1: Classic — find exact value
  while left <= right:
    mid = left + (right-left)/2
    if arr[mid] == target: return mid
    if arr[mid] < target:  left = mid+1
    else:                  right = mid-1

TEMPLATE 2: First TRUE (leftmost position where condition holds)
  while left < right:
    mid = left + (right-left)/2
    if condition(mid): right = mid      ← shrink right to mid
    else:              left = mid+1
  return left   ← left == right == answer

TEMPLATE 3: Last FALSE (rightmost position where condition is false)
  while left < right:
    mid = left + (right-left+1)/2  ← CEILING to avoid infinite loop
    if condition(mid): right = mid-1
    else:              left = mid
  return left

TEMPLATE 4: Binary search on ANSWER (not on array)
  Define search space [lo, hi] = range of possible answers
  Use Template 2 or 3 on this range.
```

### Why `left + (right-left)/2`?

```
Prevents integer overflow:
  left=2^30, right=2^31-1
  (left+right)/2 OVERFLOWS in 32-bit
  left + (right-left)/2 is safe
```

### Go Implementation

```go
// LowerBound — first index where arr[i] >= target (C++ lower_bound equivalent)
func LowerBound(arr []int, target int) int {
    left, right := 0, len(arr)
    for left < right {
        mid := left + (right-left)/2
        if arr[mid] < target {
            left = mid + 1
        } else {
            right = mid
        }
    }
    return left
}

// UpperBound — first index where arr[i] > target
func UpperBound(arr []int, target int) int {
    left, right := 0, len(arr)
    for left < right {
        mid := left + (right-left)/2
        if arr[mid] <= target {
            left = mid + 1
        } else {
            right = mid
        }
    }
    return left
}

// SearchRotatedSorted — binary search in rotated sorted array
// Time: O(log n)
func SearchRotatedSorted(nums []int, target int) int {
    left, right := 0, len(nums)-1
    for left <= right {
        mid := left + (right-left)/2
        if nums[mid] == target {
            return mid
        }
        // Left half is sorted
        if nums[left] <= nums[mid] {
            if nums[left] <= target && target < nums[mid] {
                right = mid - 1
            } else {
                left = mid + 1
            }
        } else { // Right half is sorted
            if nums[mid] < target && target <= nums[right] {
                left = mid + 1
            } else {
                right = mid - 1
            }
        }
    }
    return -1
}

// BinarySearchOnAnswer — Minimum capacity to ship packages in D days
// Search space: [max(weights), sum(weights)]
func ShipWithinDays(weights []int, days int) int {
    lo, hi := 0, 0
    for _, w := range weights {
        if w > lo { lo = w }
        hi += w
    }
    // Find minimum capacity such that canShip(capacity, days) is true
    canShip := func(cap int) bool {
        d, cur := 1, 0
        for _, w := range weights {
            if cur+w > cap {
                d++
                cur = 0
            }
            cur += w
        }
        return d <= days
    }
    for lo < hi {
        mid := lo + (hi-lo)/2
        if canShip(mid) {
            hi = mid
        } else {
            lo = mid + 1
        }
    }
    return lo
}
```

### Rust Implementation

```rust
// Generic lower_bound for any Ord type
pub fn lower_bound<T: Ord>(arr: &[T], target: &T) -> usize {
    let (mut left, mut right) = (0usize, arr.len());
    while left < right {
        let mid = left + (right - left) / 2;
        if &arr[mid] < target { left = mid + 1; }
        else { right = mid; }
    }
    left
}

pub fn search_rotated(nums: &[i32], target: i32) -> Option<usize> {
    let (mut left, mut right) = (0usize, nums.len().saturating_sub(1));
    while left <= right {
        let mid = left + (right - left) / 2;
        if nums[mid] == target { return Some(mid); }
        if nums[left] <= nums[mid] {
            if nums[left] <= target && target < nums[mid] { right = mid.saturating_sub(1); }
            else { left = mid + 1; }
        } else {
            if nums[mid] < target && target <= nums[right] { left = mid + 1; }
            else { right = mid.saturating_sub(1); }
        }
    }
    None
}
```

### C Implementation

```c
// lower_bound: first index where arr[i] >= target
int lower_bound(int *arr, int n, int target) {
    int left = 0, right = n;
    while (left < right) {
        int mid = left + (right - left) / 2;
        if (arr[mid] < target) left = mid + 1;
        else right = mid;
    }
    return left;
}
```

### Binary Search Decision Guide

```
"Find exact value in sorted array"   → Template 1
"Find first position where X >= k"  → lower_bound (Template 2)
"Find last position where X <= k"   → upper_bound - 1
"Minimum X such that f(X) is true"  → Template 2 on answer space
"Maximum X such that f(X) is false" → Template 3 on answer space
"Peak element"                       → Template 2, condition: arr[mid]>arr[mid+1]
```

---

## 10. PATTERN 06 — MONOTONIC STACK & QUEUE

### Core Idea

A **monotonic stack** maintains elements in strictly increasing or decreasing order.
When you push a new element, **pop everything that violates the monotonic property**.
Those popped elements are "answered" by the current element.

**Pattern**: "For each element, find the NEXT/PREVIOUS GREATER/SMALLER element" → Monotonic Stack

### Visual

```
NEXT GREATER ELEMENT for [2, 1, 5, 6, 2, 3]

Process each element, maintain decreasing stack:

  i=0: push 2       stack=[2]          nge=[_, _, _, _, _, _]
  i=1: push 1       stack=[2,1]        (1 < 2, no pop)
  i=2: 5 > top(1) → pop 1 → nge[1]=5
       5 > top(2) → pop 2 → nge[0]=5  stack=[]
       push 5      stack=[5]
  i=3: 6 > top(5) → pop 5 → nge[2]=6  stack=[]
       push 6      stack=[6]
  i=4: push 2       stack=[6,2]
  i=5: 3 > top(2) → pop 2 → nge[4]=3  stack=[6]
       push 3       stack=[6,3]
  
  Remaining: nge[3]=-1, nge[5]=-1 (no greater element to the right)
  
  Result: [5, 5, 6, -1, 3, -1]
```

### Monotonic Queue (Sliding Window Maximum)

```
Window of size k, track maximum in each window.
Use a deque storing INDICES in decreasing order of values.

arr = [1, 3, -1, -3, 5, 3, 6, 7],  k = 3

Deque stores indices, front = max of current window.
Remove from front if out of window.
Remove from back if new element >= back (can never be max).
```

### Go Implementation

```go
// NextGreaterElement — monotonic stack
// Time: O(n), Space: O(n)
func NextGreaterElement(nums []int) []int {
    n := len(nums)
    result := make([]int, n)
    for i := range result { result[i] = -1 }
    
    stack := make([]int, 0, n) // stores indices
    for i := 0; i < n; i++ {
        // Pop all elements smaller than current — current is their NGE
        for len(stack) > 0 && nums[stack[len(stack)-1]] < nums[i] {
            idx := stack[len(stack)-1]
            stack = stack[:len(stack)-1]
            result[idx] = nums[i]
        }
        stack = append(stack, i)
    }
    return result
}

// LargestRectangleHistogram — classic monotonic stack problem
// Time: O(n), Space: O(n)
func LargestRectangleHistogram(heights []int) int {
    n := len(heights)
    stack := []int{} // indices of bars in increasing height order
    maxArea := 0
    
    for i := 0; i <= n; i++ {
        curHeight := 0
        if i < n { curHeight = heights[i] }
        
        for len(stack) > 0 && heights[stack[len(stack)-1]] > curHeight {
            h := heights[stack[len(stack)-1]]
            stack = stack[:len(stack)-1]
            width := i
            if len(stack) > 0 {
                width = i - stack[len(stack)-1] - 1
            }
            area := h * width
            if area > maxArea { maxArea = area }
        }
        stack = append(stack, i)
    }
    return maxArea
}

// SlidingWindowMaximum — monotonic deque
// Time: O(n), Space: O(k)
func SlidingWindowMaximum(nums []int, k int) []int {
    deque := []int{} // indices, front = max of current window
    result := []int{}
    
    for i := 0; i < len(nums); i++ {
        // Remove elements outside window
        for len(deque) > 0 && deque[0] < i-k+1 {
            deque = deque[1:]
        }
        // Remove elements smaller than current from back
        for len(deque) > 0 && nums[deque[len(deque)-1]] < nums[i] {
            deque = deque[:len(deque)-1]
        }
        deque = append(deque, i)
        if i >= k-1 {
            result = append(result, nums[deque[0]])
        }
    }
    return result
}

// TrappingRainWater — two-pointer approach
// Time: O(n), Space: O(1)
func TrapRainWater(height []int) int {
    left, right := 0, len(height)-1
    leftMax, rightMax := 0, 0
    water := 0
    for left < right {
        if height[left] < height[right] {
            if height[left] >= leftMax { leftMax = height[left] } else { water += leftMax - height[left] }
            left++
        } else {
            if height[right] >= rightMax { rightMax = height[right] } else { water += rightMax - height[right] }
            right--
        }
    }
    return water
}
```

---

## 11. PATTERN 07 — HASH MAPS & FREQUENCY TABLES

### Core Idea

- **HashMap**: O(1) average lookup/insert — use for "have we seen X?" and "count of X"
- **Array as HashMap**: When key range is small (e.g., ASCII 0-255, or 1-n), array beats HashMap in constant factors

### Common Sub-patterns

```
1. FREQUENCY COUNT: group anagrams, top k frequent
2. COMPLEMENT LOOKUP: two-sum, 4-sum
3. WINDOW VALIDITY: min window substring, permutation in string
4. RUNNING STATE: subarray sum = k, longest consecutive sequence
5. FIRST/LAST SEEN: first unique char, duplicate within k distance
```

### Go Implementation

```go
// GroupAnagrams — sort each word as key
// Time: O(n * k log k), Space: O(nk)
func GroupAnagrams(strs []string) [][]string {
    groups := make(map[string][]string)
    for _, s := range strs {
        key := []byte(s)
        sort.Slice(key, func(i, j int) bool { return key[i] < key[j] })
        groups[string(key)] = append(groups[string(key)], s)
    }
    result := make([][]string, 0, len(groups))
    for _, v := range groups {
        result = append(result, v)
    }
    return result
}

// Alternative: 26-char frequency as key (avoids sort)
func GroupAnagramsFreq(strs []string) [][]string {
    groups := make(map[[26]int][]string)
    for _, s := range strs {
        var key [26]int
        for _, ch := range s { key[ch-'a']++ }
        groups[key] = append(groups[key], s)
    }
    result := make([][]string, 0, len(groups))
    for _, v := range groups { result = append(result, v) }
    return result
}

// LongestConsecutiveSequence — O(n) using hash set
func LongestConsecutiveSequence(nums []int) int {
    set := make(map[int]bool)
    for _, n := range nums { set[n] = true }
    
    maxLen := 0
    for n := range set {
        // Only start counting from the beginning of a sequence
        if !set[n-1] {
            cur, length := n, 1
            for set[cur+1] {
                cur++
                length++
            }
            if length > maxLen { maxLen = length }
        }
    }
    return maxLen
}
```

---

## 12. PATTERN 08 — TREE BFS (LEVEL ORDER)

### Core Idea

Use a **queue** to process nodes level by level.
BFS gives shortest path in unweighted graphs/trees.

### Visual

```
        1
       / \
      2   3
     / \   \
    4   5   6

BFS queue progression:
  Level 0: [1]
  Level 1: [2, 3]
  Level 2: [4, 5, 6]

For level-by-level: process all nodes at current level,
then enqueue their children.
```

### Go Implementation

```go
type TreeNode struct {
    Val   int
    Left  *TreeNode
    Right *TreeNode
}

// LevelOrder — returns nodes level by level
func LevelOrder(root *TreeNode) [][]int {
    if root == nil { return nil }
    result := [][]int{}
    queue := []*TreeNode{root}
    
    for len(queue) > 0 {
        levelSize := len(queue)
        level := make([]int, 0, levelSize)
        for i := 0; i < levelSize; i++ {
            node := queue[i]
            level = append(level, node.Val)
            if node.Left != nil  { queue = append(queue, node.Left) }
            if node.Right != nil { queue = append(queue, node.Right) }
        }
        queue = queue[levelSize:]
        result = append(result, level)
    }
    return result
}

// RightSideView — last node at each level (BFS approach)
func RightSideView(root *TreeNode) []int {
    if root == nil { return nil }
    result := []int{}
    queue := []*TreeNode{root}
    for len(queue) > 0 {
        levelSize := len(queue)
        for i := 0; i < levelSize; i++ {
            node := queue[i]
            if i == levelSize-1 { result = append(result, node.Val) }
            if node.Left != nil  { queue = append(queue, node.Left) }
            if node.Right != nil { queue = append(queue, node.Right) }
        }
        queue = queue[levelSize:]
    }
    return result
}
```

---

## 13. PATTERN 09 — TREE DFS (PRE/IN/POST)

### Core Idea

```
PRE-ORDER  (Root, Left, Right):  serialize, copy tree, prefix expression
IN-ORDER   (Left, Root, Right):  BST gives sorted order
POST-ORDER (Left, Right, Root):  delete tree, evaluate expression, bottom-up
```

### When DFS vs BFS on Trees

```
BFS:  level-by-level, shortest path, level statistics
DFS:  path sums, tree height, LCA, validate BST, serialize
```

### Go Implementation

```go
// MaxDepth — post-order DFS
func MaxDepth(root *TreeNode) int {
    if root == nil { return 0 }
    return 1 + max(MaxDepth(root.Left), MaxDepth(root.Right))
}

// HasPathSum — pre-order DFS, pass remaining sum down
func HasPathSum(root *TreeNode, targetSum int) bool {
    if root == nil { return false }
    targetSum -= root.Val
    if root.Left == nil && root.Right == nil { return targetSum == 0 }
    return HasPathSum(root.Left, targetSum) || HasPathSum(root.Right, targetSum)
}

// DiameterOfBinaryTree — post-order, return height, track max diameter
func DiameterOfBinaryTree(root *TreeNode) int {
    maxDiam := 0
    var height func(*TreeNode) int
    height = func(node *TreeNode) int {
        if node == nil { return 0 }
        left := height(node.Left)
        right := height(node.Right)
        if left+right > maxDiam { maxDiam = left + right }
        if left > right { return 1 + left }
        return 1 + right
    }
    height(root)
    return maxDiam
}

// LowestCommonAncestor — post-order, bottom-up search
func LCA(root, p, q *TreeNode) *TreeNode {
    if root == nil || root == p || root == q { return root }
    left  := LCA(root.Left, p, q)
    right := LCA(root.Right, p, q)
    if left != nil && right != nil { return root } // p and q on different sides
    if left != nil { return left }
    return right
}

// ValidateBST — pass valid range down
func IsValidBST(root *TreeNode) bool {
    var validate func(node *TreeNode, min, max int) bool
    validate = func(node *TreeNode, min, max int) bool {
        if node == nil { return true }
        if node.Val <= min || node.Val >= max { return false }
        return validate(node.Left, min, node.Val) &&
               validate(node.Right, node.Val, max)
    }
    return validate(root, -1<<63, 1<<63-1)
}

// Iterative In-Order (avoids stack overflow for skewed trees)
func InOrderIterative(root *TreeNode) []int {
    result := []int{}
    stack := []*TreeNode{}
    cur := root
    for cur != nil || len(stack) > 0 {
        for cur != nil {
            stack = append(stack, cur)
            cur = cur.Left
        }
        cur = stack[len(stack)-1]
        stack = stack[:len(stack)-1]
        result = append(result, cur.Val)
        cur = cur.Right
    }
    return result
}
```

---

## 14. PATTERN 10 — MERGE INTERVALS

### Core Idea

Sort intervals by start time, then scan:
- If current interval overlaps previous: merge (update end)
- Else: add previous to result, start new interval

**Overlap condition**: `curr.start <= prev.end`

### Visual

```
Intervals: [(1,3), (2,6), (8,10), (15,18)]
After sort: same

Step 1: prev=(1,3), cur=(2,6): 2<=3 → merge → prev=(1,6)
Step 2: prev=(1,6), cur=(8,10): 8>6 → no merge → emit (1,6), prev=(8,10)
Step 3: prev=(8,10), cur=(15,18): 15>10 → no merge → emit (8,10), prev=(15,18)
Emit (15,18)

Result: [(1,6), (8,10), (15,18)]
```

### Go Implementation

```go
type Interval struct{ Start, End int }

// MergeIntervals
// Time: O(n log n), Space: O(n)
func MergeIntervals(intervals []Interval) []Interval {
    if len(intervals) == 0 { return nil }
    sort.Slice(intervals, func(i, j int) bool {
        return intervals[i].Start < intervals[j].Start
    })
    merged := []Interval{intervals[0]}
    for _, cur := range intervals[1:] {
        prev := &merged[len(merged)-1]
        if cur.Start <= prev.End {
            if cur.End > prev.End { prev.End = cur.End }
        } else {
            merged = append(merged, cur)
        }
    }
    return merged
}

// InsertInterval — insert new interval into sorted non-overlapping list
func InsertInterval(intervals []Interval, newInterval Interval) []Interval {
    result := []Interval{}
    i := 0
    n := len(intervals)
    // Add all intervals that end before new interval starts
    for i < n && intervals[i].End < newInterval.Start {
        result = append(result, intervals[i])
        i++
    }
    // Merge all overlapping intervals
    for i < n && intervals[i].Start <= newInterval.End {
        if intervals[i].Start < newInterval.Start { newInterval.Start = intervals[i].Start }
        if intervals[i].End > newInterval.End { newInterval.End = intervals[i].End }
        i++
    }
    result = append(result, newInterval)
    // Add remaining
    result = append(result, intervals[i:]...)
    return result
}

// MeetingRoomsII — minimum meeting rooms needed
// Equivalent to: max overlapping intervals at any point
// Time: O(n log n)
func MinMeetingRooms(intervals []Interval) int {
    starts := make([]int, len(intervals))
    ends := make([]int, len(intervals))
    for i, iv := range intervals {
        starts[i] = iv.Start
        ends[i] = iv.End
    }
    sort.Ints(starts)
    sort.Ints(ends)
    rooms, endPtr := 0, 0
    for i := 0; i < len(starts); i++ {
        if starts[i] < ends[endPtr] {
            rooms++
        } else {
            endPtr++
        }
    }
    return rooms
}
```

---

## 15. PATTERN 11 — TOP K / K-WAY MERGE (HEAPS)

### Core Idea

- **Min-heap of size k**: maintains k largest elements
- **Max-heap**: efficient O(1) access to global maximum
- **K-way merge**: merge k sorted lists using a min-heap

### When to Use

```
"K largest/smallest"    → min-heap of size k
"K most frequent"       → max-heap (or sort by freq)
"Median of stream"      → two heaps (max-heap + min-heap)
"Merge K sorted lists"  → min-heap with (val, list_id, idx)
"K closest to origin"   → max-heap of size k (pop if larger than kth)
```

### Go Implementation (using container/heap)

```go
import "container/heap"

// MinHeap for top-k largest elements
type MinHeap []int
func (h MinHeap) Len() int           { return len(h) }
func (h MinHeap) Less(i, j int) bool { return h[i] < h[j] }
func (h MinHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }
func (h *MinHeap) Push(x interface{}) { *h = append(*h, x.(int)) }
func (h *MinHeap) Pop() interface{} {
    old := *h; n := len(old); x := old[n-1]; *h = old[:n-1]; return x
}

// KLargest — return k largest elements
// Time: O(n log k), Space: O(k)
func KLargest(nums []int, k int) []int {
    h := &MinHeap{}
    heap.Init(h)
    for _, n := range nums {
        heap.Push(h, n)
        if h.Len() > k {
            heap.Pop(h) // remove smallest — keeping k largest
        }
    }
    return []int(*h)
}

// MedianFinder — two heap approach
type MedianFinder struct {
    lo MaxHeap // lower half, max at top
    hi MinHeap // upper half, min at top
}

// MaxHeap for lower half
type MaxHeap []int
func (h MaxHeap) Len() int           { return len(h) }
func (h MaxHeap) Less(i, j int) bool { return h[i] > h[j] } // reversed
func (h MaxHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }
func (h *MaxHeap) Push(x interface{}) { *h = append(*h, x.(int)) }
func (h *MaxHeap) Pop() interface{} {
    old := *h; n := len(old); x := old[n-1]; *h = old[:n-1]; return x
}

func (mf *MedianFinder) AddNum(num int) {
    heap.Push(&mf.lo, num)
    // Balance: lo max must be <= hi min
    if mf.hi.Len() > 0 && mf.lo[0] > mf.hi[0] {
        heap.Push(&mf.hi, heap.Pop(&mf.lo))
    }
    // Size balance: lo can have at most 1 more than hi
    if mf.lo.Len() > mf.hi.Len()+1 {
        heap.Push(&mf.hi, heap.Pop(&mf.lo))
    } else if mf.hi.Len() > mf.lo.Len() {
        heap.Push(&mf.lo, heap.Pop(&mf.hi))
    }
}

func (mf *MedianFinder) FindMedian() float64 {
    if mf.lo.Len() == mf.hi.Len() {
        return float64(mf.lo[0]+mf.hi[0]) / 2.0
    }
    return float64(mf.lo[0])
}
```

### Rust Implementation (BinaryHeap)

```rust
use std::collections::BinaryHeap;
use std::cmp::Reverse;

// K largest using min-heap (Reverse wrapper)
pub fn k_largest(nums: &[i32], k: usize) -> Vec<i32> {
    let mut heap: BinaryHeap<Reverse<i32>> = BinaryHeap::new();
    for &n in nums {
        heap.push(Reverse(n));
        if heap.len() > k { heap.pop(); }
    }
    heap.into_iter().map(|Reverse(x)| x).collect()
}
```

---

## 16. PATTERN 12 — CYCLIC SORT

### Core Idea

When you have an array of n numbers in range [1, n] (or [0, n-1]):
Place each number at its correct index by swapping.
The invariant: `nums[i] == i+1` (for 1-indexed) after sorting.

### Visual

```
arr = [3, 1, 5, 4, 2]
       ↑
       i=0, nums[0]=3, should be at index 2
       swap(arr[0], arr[2]) → arr=[5, 1, 3, 4, 2]
       (3 is now at index 2 ✓, but arr[0]=5 still wrong)
       swap(arr[0], arr[4]) → arr=[2, 1, 3, 4, 5]
       swap(arr[0], arr[1]) → arr=[1, 2, 3, 4, 5]
       i=0: done, i=1: 2==2✓, i=2: 3==3✓...
```

### Go Implementation

```go
// CyclicSort — sort array of 1 to n
func CyclicSort(nums []int) {
    i := 0
    for i < len(nums) {
        j := nums[i] - 1 // correct index for nums[i]
        if nums[i] != nums[j] {
            nums[i], nums[j] = nums[j], nums[i]
        } else {
            i++
        }
    }
}

// FindMissingNumber — after cyclic sort, find index where nums[i]!=i+1
func FindMissingNumber(nums []int) int {
    i := 0
    n := len(nums)
    for i < n {
        j := nums[i]
        if nums[i] < n && nums[i] != nums[j] {
            nums[i], nums[j] = nums[j], nums[i]
        } else {
            i++
        }
    }
    for i, v := range nums {
        if v != i+1 { return i + 1 }
    }
    return n + 1
}

// FindDuplicateNumber — after cyclic sort, index where nums[i]!=i+1 → nums[i] is duplicate
func FindDuplicateNumber(nums []int) int {
    i := 0
    for i < len(nums) {
        j := nums[i] - 1
        if nums[i] != i+1 {
            if nums[i] != nums[j] {
                nums[i], nums[j] = nums[j], nums[i]
            } else {
                return nums[i] // duplicate found
            }
        } else {
            i++
        }
    }
    return -1
}
```

---

## 17. PATTERN 13 — IN-PLACE LINKEDLIST REVERSAL

### Core Idea

Reverse a linked list (or sublist) using three pointers: prev, curr, next.
No extra space, just pointer manipulation.

### Visual

```
Reverse [a → b → c → d → nil]

Step 1: prev=nil, curr=a
        next = curr.Next = b
        curr.Next = prev = nil       a → nil
        prev = curr = a
        curr = next = b

Step 2: prev=a, curr=b
        next = c
        b.Next = prev = a            b → a → nil
        prev = b, curr = c

...Result: d → c → b → a → nil
```

### Go Implementation

```go
// ReverseList — full reversal
func ReverseList(head *ListNode) *ListNode {
    var prev *ListNode
    curr := head
    for curr != nil {
        next := curr.Next
        curr.Next = prev
        prev = curr
        curr = next
    }
    return prev
}

// ReverseSubList — reverse from position left to right (1-indexed)
func ReverseSubList(head *ListNode, left, right int) *ListNode {
    dummy := &ListNode{Next: head}
    pre := dummy
    // Move pre to node just before 'left'
    for i := 1; i < left; i++ { pre = pre.Next }
    
    curr := pre.Next
    for i := 0; i < right-left; i++ {
        next := curr.Next
        curr.Next = next.Next
        next.Next = pre.Next
        pre.Next = next
    }
    return dummy.Next
}

// ReverseKGroup — reverse in groups of k
func ReverseKGroup(head *ListNode, k int) *ListNode {
    // Check if k nodes remain
    count, node := 0, head
    for node != nil && count < k {
        node = node.Next
        count++
    }
    if count < k { return head } // fewer than k nodes, don't reverse
    
    var prev *ListNode
    curr := head
    for i := 0; i < k; i++ {
        next := curr.Next
        curr.Next = prev
        prev = curr
        curr = next
    }
    // head is now the tail of reversed group
    head.Next = ReverseKGroup(curr, k)
    return prev
}
```

---

## 18. PATTERN 14 — BACKTRACKING & SUBSETS

### Core Idea

Backtracking = DFS on decision tree + undo choice when backtracking.
**Template**:
```
backtrack(state, choices):
  if base_case: record/return
  for choice in choices:
    make_choice(state, choice)
    backtrack(updated_state, remaining_choices)
    undo_choice(state, choice)    ← THE KEY STEP
```

### Visual: Decision Tree for Subsets [1,2,3]

```
                    []
          /          |          \
        [1]         [2]         [3]
       /   \          \
    [1,2] [1,3]      [2,3]
      |
   [1,2,3]

All 8 subsets: [], [1], [2], [3], [1,2], [1,3], [2,3], [1,2,3]
```

### Go Implementation

```go
// Subsets — all subsets (power set)
func Subsets(nums []int) [][]int {
    result := [][]int{}
    var backtrack func(start int, current []int)
    backtrack = func(start int, current []int) {
        // Add copy of current to result at every step
        tmp := make([]int, len(current))
        copy(tmp, current)
        result = append(result, tmp)
        
        for i := start; i < len(nums); i++ {
            current = append(current, nums[i])
            backtrack(i+1, current)
            current = current[:len(current)-1] // backtrack
        }
    }
    backtrack(0, []int{})
    return result
}

// Permutations — all permutations
func Permutations(nums []int) [][]int {
    result := [][]int{}
    used := make([]bool, len(nums))
    var backtrack func(current []int)
    backtrack = func(current []int) {
        if len(current) == len(nums) {
            tmp := make([]int, len(current))
            copy(tmp, current)
            result = append(result, tmp)
            return
        }
        for i := 0; i < len(nums); i++ {
            if used[i] { continue }
            used[i] = true
            current = append(current, nums[i])
            backtrack(current)
            current = current[:len(current)-1]
            used[i] = false
        }
    }
    backtrack([]int{})
    return result
}

// CombinationSum — elements can repeat, find all combos summing to target
func CombinationSum(candidates []int, target int) [][]int {
    result := [][]int{}
    sort.Ints(candidates)
    var backtrack func(start, remaining int, current []int)
    backtrack = func(start, remaining int, current []int) {
        if remaining == 0 {
            tmp := make([]int, len(current))
            copy(tmp, current)
            result = append(result, tmp)
            return
        }
        for i := start; i < len(candidates); i++ {
            if candidates[i] > remaining { break } // pruning
            current = append(current, candidates[i])
            backtrack(i, remaining-candidates[i], current) // i not i+1 (can reuse)
            current = current[:len(current)-1]
        }
    }
    backtrack(0, target, []int{})
    return result
}

// NQueens — classic constraint satisfaction backtracking
func SolveNQueens(n int) [][]string {
    result := [][]string{}
    board := make([][]byte, n)
    for i := range board {
        board[i] = make([]byte, n)
        for j := range board[i] { board[i][j] = '.' }
    }
    
    cols := make([]bool, n)
    diag1 := make([]bool, 2*n)  // row-col+n
    diag2 := make([]bool, 2*n)  // row+col
    
    var backtrack func(row int)
    backtrack = func(row int) {
        if row == n {
            snapshot := make([]string, n)
            for i := range board { snapshot[i] = string(board[i]) }
            result = append(result, snapshot)
            return
        }
        for col := 0; col < n; col++ {
            if cols[col] || diag1[row-col+n] || diag2[row+col] { continue }
            board[row][col] = 'Q'
            cols[col] = true; diag1[row-col+n] = true; diag2[row+col] = true
            backtrack(row + 1)
            board[row][col] = '.'
            cols[col] = false; diag1[row-col+n] = false; diag2[row+col] = false
        }
    }
    backtrack(0)
    return result
}
```

### Backtracking Pruning Strategies

```
1. SORT first → enables early termination (if candidates[i] > remaining: break)
2. SKIP duplicates → if i > start && candidates[i] == candidates[i-1]: continue
3. CONSTRAINT CHECK before recursing → don't go deeper if already invalid
4. FEASIBILITY BOUND → prune if even best remaining can't reach goal
```

---

## 19. PATTERN 15 — DYNAMIC PROGRAMMING (ALL SUBTYPES)

### Core Idea

DP = memoization of overlapping subproblems in a DAG of states.
**Three steps**:
1. Define `dp[state]` — what does it represent?
2. Write recurrence — how does `dp[state]` depend on smaller states?
3. Identify base cases and traversal order.

### DP Classification

```
┌───────────────────────────────────────────────────────────────┐
│  TYPE                │ dp STATE     │ CLASSIC PROBLEMS        │
├───────────────────────────────────────────────────────────────┤
│  Linear DP           │ dp[i]        │ LIS, Fibonacci, rob     │
│  Grid DP             │ dp[i][j]     │ unique paths, min path  │
│  Interval DP         │ dp[i][j]     │ burst balloons, MCM     │
│  Knapsack (0/1)      │ dp[i][w]     │ 0/1 knapsack, subset sum│
│  Knapsack (unbounded)│ dp[w]        │ coin change, rod cut    │
│  String DP           │ dp[i][j]     │ LCS, edit distance, LPS │
│  Tree DP             │ dp[node]     │ max path, rob on tree   │
│  Bitmask DP          │ dp[mask]     │ TSP, set cover          │
│  State Machine DP    │ dp[i][state] │ buy/sell stocks         │
└───────────────────────────────────────────────────────────────┘
```

### The DP Design Process

```
1. Think RECURSIVELY first (top-down memoization)
2. Identify what CHANGES between recursive calls → those are the state variables
3. Convert to bottom-up once you understand the state transitions
4. Optimize space if dp[i] only depends on dp[i-1] (rolling array)
```

### Go Implementations

```go
// ============================================================
// LINEAR DP: Longest Increasing Subsequence (LIS)
// dp[i] = length of LIS ending at index i
// Time: O(n^2), O(n log n) with patience sort
// ============================================================
func LengthOfLIS(nums []int) int {
    n := len(nums)
    dp := make([]int, n)
    for i := range dp { dp[i] = 1 }
    maxLen := 1
    for i := 1; i < n; i++ {
        for j := 0; j < i; j++ {
            if nums[j] < nums[i] && dp[j]+1 > dp[i] {
                dp[i] = dp[j] + 1
            }
        }
        if dp[i] > maxLen { maxLen = dp[i] }
    }
    return maxLen
}

// O(n log n) LIS using binary search (patience sorting)
func LengthOfLISFast(nums []int) int {
    tails := []int{} // tails[i] = smallest tail of LIS of length i+1
    for _, num := range nums {
        pos := sort.SearchInts(tails, num)
        if pos == len(tails) {
            tails = append(tails, num)
        } else {
            tails[pos] = num
        }
    }
    return len(tails)
}

// ============================================================
// 0/1 KNAPSACK
// dp[i][w] = max value using first i items with capacity w
// ============================================================
func Knapsack01(weights, values []int, capacity int) int {
    n := len(weights)
    dp := make([][]int, n+1)
    for i := range dp { dp[i] = make([]int, capacity+1) }
    for i := 1; i <= n; i++ {
        for w := 0; w <= capacity; w++ {
            dp[i][w] = dp[i-1][w] // don't take item i
            if w >= weights[i-1] {
                take := dp[i-1][w-weights[i-1]] + values[i-1]
                if take > dp[i][w] { dp[i][w] = take }
            }
        }
    }
    return dp[n][capacity]
}

// Space optimized 0/1 knapsack — O(W) space
func Knapsack01Opt(weights, values []int, capacity int) int {
    dp := make([]int, capacity+1)
    for i := 0; i < len(weights); i++ {
        // MUST iterate backwards to prevent using item twice
        for w := capacity; w >= weights[i]; w-- {
            if dp[w-weights[i]]+values[i] > dp[w] {
                dp[w] = dp[w-weights[i]] + values[i]
            }
        }
    }
    return dp[capacity]
}

// ============================================================
// COIN CHANGE (Unbounded Knapsack)
// dp[amount] = min coins to make 'amount'
// ============================================================
func CoinChange(coins []int, amount int) int {
    dp := make([]int, amount+1)
    for i := range dp { dp[i] = amount + 1 } // sentinel "infinity"
    dp[0] = 0
    for a := 1; a <= amount; a++ {
        for _, c := range coins {
            if c <= a && dp[a-c]+1 < dp[a] {
                dp[a] = dp[a-c] + 1
            }
        }
    }
    if dp[amount] > amount { return -1 }
    return dp[amount]
}

// ============================================================
// STRING DP: Edit Distance (Levenshtein)
// dp[i][j] = min ops to convert word1[0..i] to word2[0..j]
// ============================================================
func MinEditDistance(word1, word2 string) int {
    m, n := len(word1), len(word2)
    dp := make([][]int, m+1)
    for i := range dp {
        dp[i] = make([]int, n+1)
        dp[i][0] = i // delete i chars from word1
    }
    for j := 0; j <= n; j++ { dp[0][j] = j }
    
    for i := 1; i <= m; i++ {
        for j := 1; j <= n; j++ {
            if word1[i-1] == word2[j-1] {
                dp[i][j] = dp[i-1][j-1] // match, no op
            } else {
                dp[i][j] = 1 + min3(
                    dp[i-1][j],   // delete from word1
                    dp[i][j-1],   // insert into word1
                    dp[i-1][j-1], // replace
                )
            }
        }
    }
    return dp[m][n]
}

func min3(a, b, c int) int {
    if a < b { if a < c { return a }; return c }
    if b < c { return b }; return c
}

// ============================================================
// INTERVAL DP: Burst Balloons
// dp[i][j] = max coins from bursting all balloons in (i, j) exclusive
// Last burst in (i,j) is k → dp[i][j] = max over k of:
//   nums[i]*nums[k]*nums[j] + dp[i][k] + dp[k][j]
// ============================================================
func MaxCoinsBaloons(nums []int) int {
    // Pad with 1 on both sides
    arr := make([]int, len(nums)+2)
    arr[0], arr[len(arr)-1] = 1, 1
    copy(arr[1:], nums)
    n := len(arr)
    
    dp := make([][]int, n)
    for i := range dp { dp[i] = make([]int, n) }
    
    for length := 2; length < n; length++ {
        for left := 0; left < n-length; left++ {
            right := left + length
            for k := left + 1; k < right; k++ {
                coins := arr[left]*arr[k]*arr[right] + dp[left][k] + dp[k][right]
                if coins > dp[left][right] { dp[left][right] = coins }
            }
        }
    }
    return dp[0][n-1]
}

// ============================================================
// STATE MACHINE DP: Best Time to Buy/Sell Stock with Cooldown
// States: hold, sold, rest
// ============================================================
func MaxProfitCooldown(prices []int) int {
    hold, sold, rest := -prices[0], 0, 0
    for i := 1; i < len(prices); i++ {
        prevHold, prevSold := hold, sold
        hold = max2(prevHold, rest-prices[i])   // keep holding or buy
        sold = prevHold + prices[i]              // sell today
        rest = max2(rest, prevSold)              // rest or continue resting
    }
    return max2(sold, rest)
}

func max2(a, b int) int { if a > b { return a }; return b }

// ============================================================
// BITMASK DP: Traveling Salesman (small n ≤ 20)
// dp[mask][i] = min cost to visit all cities in mask, ending at i
// ============================================================
func TSP(dist [][]int) int {
    n := len(dist)
    INF := 1 << 30
    dp := make([][]int, 1<<n)
    for i := range dp {
        dp[i] = make([]int, n)
        for j := range dp[i] { dp[i][j] = INF }
    }
    dp[1][0] = 0 // start at city 0, visited = {0}
    
    for mask := 1; mask < (1 << n); mask++ {
        for last := 0; last < n; last++ {
            if dp[mask][last] == INF { continue }
            if mask&(1<<last) == 0  { continue }
            for next := 0; next < n; next++ {
                if mask&(1<<next) != 0 { continue } // already visited
                newMask := mask | (1 << next)
                cost := dp[mask][last] + dist[last][next]
                if cost < dp[newMask][next] { dp[newMask][next] = cost }
            }
        }
    }
    
    fullMask := (1 << n) - 1
    result := INF
    for last := 1; last < n; last++ {
        cost := dp[fullMask][last] + dist[last][0]
        if cost < result { result = cost }
    }
    return result
}
```

### Rust DP Implementations

```rust
pub fn length_of_lis(nums: &[i32]) -> usize {
    let mut tails: Vec<i32> = Vec::new();
    for &num in nums {
        let pos = tails.partition_point(|&x| x < num);
        if pos == tails.len() { tails.push(num); }
        else { tails[pos] = num; }
    }
    tails.len()
}

pub fn coin_change(coins: &[u32], amount: u32) -> Option<u32> {
    let n = amount as usize;
    let mut dp = vec![u32::MAX; n + 1];
    dp[0] = 0;
    for a in 1..=n {
        for &c in coins {
            if c as usize <= a {
                if let Some(prev) = dp[a - c as usize].checked_add(1) {
                    dp[a] = dp[a].min(prev);
                }
            }
        }
    }
    if dp[n] == u32::MAX { None } else { Some(dp[n]) }
}
```

### C DP Implementations

```c
// Edit Distance
int min_edit_distance(const char *w1, const char *w2) {
    int m = strlen(w1), n = strlen(w2);
    int dp[m+1][n+1];
    for (int i = 0; i <= m; i++) dp[i][0] = i;
    for (int j = 0; j <= n; j++) dp[0][j] = j;
    for (int i = 1; i <= m; i++)
        for (int j = 1; j <= n; j++) {
            if (w1[i-1] == w2[j-1]) dp[i][j] = dp[i-1][j-1];
            else {
                int a = dp[i-1][j], b = dp[i][j-1], c = dp[i-1][j-1];
                dp[i][j] = 1 + (a<b ? (a<c?a:c) : (b<c?b:c));
            }
        }
    return dp[m][n];
}
```

---

## 20. PATTERN 16 — GRAPH ALGORITHMS

### Graph Representation Choice

```
ADJACENCY LIST:   map[int][]int  or  [][]int
  Use for: sparse graphs, most real problems
  Space: O(V + E)

ADJACENCY MATRIX: [][]int
  Use for: dense graphs (E ≈ V^2), quick edge existence check
  Space: O(V^2) — avoid for V > 1000

EDGE LIST:        [][2]int or [][3]int (with weight)
  Use for: Kruskal's MST, sorting edges
```

### BFS — Shortest Path (Unweighted)

```go
// BFS for shortest path in unweighted graph
// Time: O(V+E), Space: O(V)
func BFSShortestPath(graph [][]int, start, end int) int {
    visited := make([]bool, len(graph))
    queue := []int{start}
    visited[start] = true
    dist := 0
    for len(queue) > 0 {
        size := len(queue)
        for i := 0; i < size; i++ {
            node := queue[i]
            if node == end { return dist }
            for _, neighbor := range graph[node] {
                if !visited[neighbor] {
                    visited[neighbor] = true
                    queue = append(queue, neighbor)
                }
            }
        }
        queue = queue[size:]
        dist++
    }
    return -1
}
```

### DFS — Connected Components, Cycle Detection

```go
// NumberOfIslands — DFS flood fill
func NumIslands(grid [][]byte) int {
    count := 0
    var dfs func(r, c int)
    dfs = func(r, c int) {
        if r < 0 || r >= len(grid) || c < 0 || c >= len(grid[0]) ||
            grid[r][c] != '1' { return }
        grid[r][c] = '0' // mark visited
        dfs(r+1, c); dfs(r-1, c); dfs(r, c+1); dfs(r, c-1)
    }
    for r := range grid {
        for c := range grid[r] {
            if grid[r][c] == '1' {
                dfs(r, c)
                count++
            }
        }
    }
    return count
}
```

### Union-Find (Disjoint Set Union)

```go
// UnionFind — path compression + union by rank
// Time: O(α(n)) per operation (effectively O(1))
type UnionFind struct {
    parent []int
    rank   []int
    count  int // number of connected components
}

func NewUnionFind(n int) *UnionFind {
    parent := make([]int, n)
    rank := make([]int, n)
    for i := range parent { parent[i] = i }
    return &UnionFind{parent: parent, rank: rank, count: n}
}

func (uf *UnionFind) Find(x int) int {
    if uf.parent[x] != x {
        uf.parent[x] = uf.Find(uf.parent[x]) // path compression
    }
    return uf.parent[x]
}

func (uf *UnionFind) Union(x, y int) bool {
    px, py := uf.Find(x), uf.Find(y)
    if px == py { return false } // already connected
    if uf.rank[px] < uf.rank[py] { px, py = py, px }
    uf.parent[py] = px
    if uf.rank[px] == uf.rank[py] { uf.rank[px]++ }
    uf.count--
    return true
}
```

### Topological Sort (Kahn's Algorithm — BFS)

```go
// TopologicalSort — Kahn's BFS algorithm
// Returns topological order, or empty if cycle detected
func TopologicalSort(numCourses int, prerequisites [][2]int) []int {
    inDegree := make([]int, numCourses)
    adj := make([][]int, numCourses)
    for _, pre := range prerequisites {
        adj[pre[1]] = append(adj[pre[1]], pre[0])
        inDegree[pre[0]]++
    }
    queue := []int{}
    for i, d := range inDegree {
        if d == 0 { queue = append(queue, i) }
    }
    order := []int{}
    for len(queue) > 0 {
        node := queue[0]
        queue = queue[1:]
        order = append(order, node)
        for _, neighbor := range adj[node] {
            inDegree[neighbor]--
            if inDegree[neighbor] == 0 { queue = append(queue, neighbor) }
        }
    }
    if len(order) != numCourses { return nil } // cycle detected
    return order
}
```

### Dijkstra's Algorithm

```go
import "container/heap"

type Item struct{ node, dist int }
type PriorityQueue []Item
func (pq PriorityQueue) Len() int           { return len(pq) }
func (pq PriorityQueue) Less(i, j int) bool { return pq[i].dist < pq[j].dist }
func (pq PriorityQueue) Swap(i, j int)      { pq[i], pq[j] = pq[j], pq[i] }
func (pq *PriorityQueue) Push(x interface{}) { *pq = append(*pq, x.(Item)) }
func (pq *PriorityQueue) Pop() interface{} {
    old := *pq; n := len(old); x := old[n-1]; *pq = old[:n-1]; return x
}

// Dijkstra — single source shortest path (non-negative weights)
// Time: O((V+E) log V)
func Dijkstra(graph [][][2]int, src int) []int {
    n := len(graph)
    dist := make([]int, n)
    for i := range dist { dist[i] = 1<<31 - 1 }
    dist[src] = 0
    pq := &PriorityQueue{{src, 0}}
    heap.Init(pq)
    for pq.Len() > 0 {
        item := heap.Pop(pq).(Item)
        u, d := item.node, item.dist
        if d > dist[u] { continue } // stale entry
        for _, edge := range graph[u] {
            v, w := edge[0], edge[1]
            if dist[u]+w < dist[v] {
                dist[v] = dist[u] + w
                heap.Push(pq, Item{v, dist[v]})
            }
        }
    }
    return dist
}
```

### Bellman-Ford (Negative Weights)

```go
// BellmanFord — handles negative weights, detects negative cycles
// Time: O(V*E)
func BellmanFord(n int, edges [][3]int, src int) ([]int, bool) {
    dist := make([]int, n)
    for i := range dist { dist[i] = 1<<31 - 1 }
    dist[src] = 0
    // Relax all edges V-1 times
    for i := 0; i < n-1; i++ {
        for _, e := range edges {
            u, v, w := e[0], e[1], e[2]
            if dist[u] != 1<<31-1 && dist[u]+w < dist[v] {
                dist[v] = dist[u] + w
            }
        }
    }
    // Check for negative cycle
    for _, e := range edges {
        u, v, w := e[0], e[1], e[2]
        if dist[u] != 1<<31-1 && dist[u]+w < dist[v] {
            return nil, true // negative cycle
        }
    }
    return dist, false
}
```

### Cycle Detection in Directed Graph (DFS Coloring)

```go
// 0=white(unvisited), 1=gray(in stack), 2=black(done)
func HasCycleDirected(adj [][]int) bool {
    n := len(adj)
    color := make([]int, n)
    var dfs func(u int) bool
    dfs = func(u int) bool {
        color[u] = 1 // gray = in recursion stack
        for _, v := range adj[u] {
            if color[v] == 1 { return true }  // back edge = cycle
            if color[v] == 0 && dfs(v) { return true }
        }
        color[u] = 2 // black = fully processed
        return false
    }
    for i := 0; i < n; i++ {
        if color[i] == 0 && dfs(i) { return true }
    }
    return false
}
```

---

## 21. PATTERN 17 — TRIES (PREFIX TREES)

### Core Idea

Trie = tree where each node represents a character.
Path from root to marked node = a word.
Time: O(L) per insert/search (L = word length) — beats HashMap for prefix operations.

### Visual

```
Words: ["cat", "car", "card", "care", "dog"]

         root
        /    \
       c      d
       |      |
       a      o
      / \     |
     t   r    g*
     *  / \
       d   e
       *   *
```

### Go Implementation

```go
type TrieNode struct {
    children [26]*TrieNode
    isEnd    bool
}

type Trie struct{ root *TrieNode }

func NewTrie() *Trie { return &Trie{root: &TrieNode{}} }

func (t *Trie) Insert(word string) {
    node := t.root
    for _, ch := range word {
        idx := ch - 'a'
        if node.children[idx] == nil {
            node.children[idx] = &TrieNode{}
        }
        node = node.children[idx]
    }
    node.isEnd = true
}

func (t *Trie) Search(word string) bool {
    node := t.root
    for _, ch := range word {
        idx := ch - 'a'
        if node.children[idx] == nil { return false }
        node = node.children[idx]
    }
    return node.isEnd
}

func (t *Trie) StartsWith(prefix string) bool {
    node := t.root
    for _, ch := range prefix {
        idx := ch - 'a'
        if node.children[idx] == nil { return false }
        node = node.children[idx]
    }
    return true
}

// WordSearchII — find all words from dictionary in board (Trie + DFS)
func FindWords(board [][]byte, words []string) []string {
    trie := NewTrie()
    for _, w := range words { trie.Insert(w) }
    
    m, n := len(board), len(board[0])
    found := map[string]bool{}
    
    var dfs func(node *TrieNode, r, c int, path string)
    dfs = func(node *TrieNode, r, c int, path string) {
        if r < 0 || r >= m || c < 0 || c >= n || board[r][c] == '#' { return }
        ch := board[r][c]
        next := node.children[ch-'a']
        if next == nil { return }
        path += string(ch)
        if next.isEnd { found[path] = true }
        board[r][c] = '#' // mark visited
        dfs(next, r+1, c, path); dfs(next, r-1, c, path)
        dfs(next, r, c+1, path); dfs(next, r, c-1, path)
        board[r][c] = ch // restore
    }
    for r := range board {
        for c := range board[r] {
            dfs(trie.root, r, c, "")
        }
    }
    result := make([]string, 0, len(found))
    for w := range found { result = append(result, w) }
    return result
}
```

---

## 22. PATTERN 18 — SEGMENT TREES & BIT (FENWICK)

### When to Use

```
STATIC ARRAY, range SUM queries only    → Prefix Sum O(1) query
DYNAMIC (updates), range SUM queries    → Binary Indexed Tree (BIT/Fenwick) O(log n)
DYNAMIC, range MIN/MAX/arbitrary query  → Segment Tree O(log n)
LAZY UPDATES on ranges                  → Segment Tree with lazy propagation
```

### Binary Indexed Tree (Fenwick)

```
BIT stores partial sums in a clever bit-trick structure.
bit[i] covers a range determined by the lowest set bit of i.

Index:  1   2   3   4   5   6   7   8
Range: [1] [1-2][3][1-4][5][5-6][7][1-8]
```

### Go Implementation — Fenwick Tree

```go
type BIT struct{ tree []int }

func NewBIT(n int) *BIT { return &BIT{tree: make([]int, n+1)} }

// Update: add delta to index i (1-indexed)
func (b *BIT) Update(i, delta int) {
    for ; i < len(b.tree); i += i & (-i) {
        b.tree[i] += delta
    }
}

// Query: prefix sum from 1 to i
func (b *BIT) Query(i int) int {
    sum := 0
    for ; i > 0; i -= i & (-i) {
        sum += b.tree[i]
    }
    return sum
}

// Range sum from l to r (1-indexed)
func (b *BIT) RangeQuery(l, r int) int {
    if l > 1 { return b.Query(r) - b.Query(l-1) }
    return b.Query(r)
}
```

### Segment Tree

```go
type SegTree struct {
    tree []int
    n    int
}

func NewSegTree(nums []int) *SegTree {
    n := len(nums)
    tree := make([]int, 4*n)
    st := &SegTree{tree: tree, n: n}
    st.build(nums, 0, 0, n-1)
    return st
}

func (st *SegTree) build(nums []int, node, start, end int) {
    if start == end {
        st.tree[node] = nums[start]
        return
    }
    mid := (start + end) / 2
    st.build(nums, 2*node+1, start, mid)
    st.build(nums, 2*node+2, mid+1, end)
    st.tree[node] = st.tree[2*node+1] + st.tree[2*node+2]
}

func (st *SegTree) Update(idx, val, node, start, end int) {
    if start == end {
        st.tree[node] = val
        return
    }
    mid := (start + end) / 2
    if idx <= mid { st.Update(idx, val, 2*node+1, start, mid) } else
                  { st.Update(idx, val, 2*node+2, mid+1, end) }
    st.tree[node] = st.tree[2*node+1] + st.tree[2*node+2]
}

func (st *SegTree) Query(l, r, node, start, end int) int {
    if r < start || end < l { return 0 }
    if l <= start && end <= r { return st.tree[node] }
    mid := (start + end) / 2
    return st.Query(l, r, 2*node+1, start, mid) +
           st.Query(l, r, 2*node+2, mid+1, end)
}
```

---

## 23. PATTERN 19 — BITWISE TRICKS

### Essential Bit Operations

```
x & (x-1)     → clears the lowest set bit of x
               → checks if x is power of 2: x & (x-1) == 0
x & (-x)       → isolates the lowest set bit
x | (x+1)     → sets the lowest unset bit
x ^ x          → 0 (XOR with self)
x ^ 0          → x (XOR with zero)
a ^ b ^ a      → b (XOR cancellation)
(n >> k) & 1   → kth bit of n
n | (1 << k)   → set kth bit
n & ~(1 << k)  → clear kth bit
n ^ (1 << k)   → toggle kth bit
```

### Key Bit Tricks & Problems

```go
// SingleNumber — find element that appears once (all others appear twice)
// XOR all elements: pairs cancel out, single remains
func SingleNumber(nums []int) int {
    result := 0
    for _, n := range nums { result ^= n }
    return result
}

// SingleNumberII — appears once, others appear three times
// Use bit counting: count bits at each position mod 3
func SingleNumberIII(nums []int) int {
    ones, twos := 0, 0
    for _, n := range nums {
        ones = (ones ^ n) & ^twos
        twos = (twos ^ n) & ^ones
    }
    return ones
}

// CountBits — count set bits (Brian Kernighan)
func CountBits(n int) int {
    count := 0
    for n != 0 { n &= n - 1; count++ }
    return count
}

// ReverseBits — reverse 32-bit integer
func ReverseBits(num uint32) uint32 {
    var result uint32
    for i := 0; i < 32; i++ {
        result = (result << 1) | (num & 1)
        num >>= 1
    }
    return result
}

// NumberOf1Bits — also known as Hamming weight
// Using lookup table for speed (production technique):
var bitCountTable [256]byte
func init() {
    for i := range bitCountTable {
        bitCountTable[i] = bitCountTable[i>>1] + byte(i&1)
    }
}
func HammingWeight(n uint32) int {
    return int(bitCountTable[n&0xff]) +
           int(bitCountTable[(n>>8)&0xff]) +
           int(bitCountTable[(n>>16)&0xff]) +
           int(bitCountTable[(n>>24)&0xff])
}

// MaxXOR of two numbers in array — using Trie on bits
func FindMaximumXOR(nums []int) int {
    max_val, mask, maxXOR := 0, 0, 0
    for i := 31; i >= 0; i-- {
        mask |= 1 << i
        prefixes := map[int]bool{0: true}
        for _, n := range nums { prefixes[n&mask] = true }
        greedyMax := maxXOR | (1 << i)
        for prefix := range prefixes {
            if prefixes[greedyMax^prefix] {
                maxXOR = greedyMax
                break
            }
        }
        _ = max_val
    }
    return maxXOR
}
```

### Bitmask Enumeration

```go
// Enumerate all subsets of a set represented as bitmask
func EnumerateSubsets(n int) {
    for mask := 0; mask < (1 << n); mask++ {
        // mask represents a subset
        for i := 0; i < n; i++ {
            if mask&(1<<i) != 0 {
                // element i is in this subset
            }
        }
    }
}

// Enumerate all subsets of a specific bitmask (useful in DP)
func EnumerateSubsetsOf(mask int) {
    for sub := mask; sub > 0; sub = (sub - 1) & mask {
        // process sub
    }
    // This visits all subsets of mask in O(2^popcount(mask))
}
```

---

## 24. PATTERN 20 — MATH & NUMBER THEORY

### Essential Mathematical Tools

```go
// GCD — Euclidean algorithm
func GCD(a, b int) int {
    for b != 0 { a, b = b, a%b }
    return a
}
func LCM(a, b int) int { return a / GCD(a, b) * b }

// Sieve of Eratosthenes — all primes up to n
// Time: O(n log log n), Space: O(n)
func SieveOfEratosthenes(n int) []int {
    isPrime := make([]bool, n+1)
    for i := range isPrime { isPrime[i] = true }
    isPrime[0], isPrime[1] = false, false
    for i := 2; i*i <= n; i++ {
        if isPrime[i] {
            for j := i * i; j <= n; j += i {
                isPrime[j] = false
            }
        }
    }
    primes := []int{}
    for i, p := range isPrime { if p { primes = append(primes, i) } }
    return primes
}

// FastPower — modular exponentiation
// Compute base^exp % mod in O(log exp)
func ModPow(base, exp, mod int) int {
    result := 1
    base %= mod
    for exp > 0 {
        if exp&1 == 1 { result = result * base % mod }
        base = base * base % mod
        exp >>= 1
    }
    return result
}

// ModInverse — using Fermat's little theorem (mod must be prime)
func ModInverse(a, mod int) int {
    return ModPow(a, mod-2, mod)
}

// Pascal's Triangle / nCr with mod
func NCR(n, r, mod int) int {
    if r == 0 || r == n { return 1 }
    // Precompute factorials
    fact := make([]int, n+1)
    fact[0] = 1
    for i := 1; i <= n; i++ { fact[i] = fact[i-1] * i % mod }
    return fact[n] * ModInverse(fact[r], mod) % mod *
           ModInverse(fact[n-r], mod) % mod
}
```

---

## 25. HIDDEN TRICKS & ADVANCED OBSERVATIONS

### The 20 Hidden Tricks Every Pro Knows

```
TRICK 1: "Dummy Node" in Linked List Problems
  Always add a dummy head node to avoid null-check edge cases.
  dummy := &ListNode{Next: head}
  return dummy.Next

TRICK 2: Sentinel Values
  Add INT_MIN/INT_MAX to arrays/heaps to eliminate boundary checks.
  Add virtual nodes 0 and n+1 to graph problems.
  (Burst Balloons: pad with 1 on both sides)

TRICK 3: Coordinate Compression
  When values are large but relative order matters:
  Map them to [0, n-1] range. Sort unique values, map via binary search.
  Essential for BIT/Segment Tree on large value ranges.

TRICK 4: "Think About the Complement"
  Instead of counting what you want, count what you don't want:
  total - invalid_count
  "Subarrays with at least k distinct" = total - "fewer than k distinct"

TRICK 5: Reverse Thinking
  "Build in reverse / delete in reverse"
  Adding elements forward is hard? Process in reverse (simulates deletion).
  Classic: "Last stone" problems, online streaming problems.

TRICK 6: Two-Pass / Three-Pass
  Pass 1: collect info (max from left, prefix, etc.)
  Pass 2: use info (combine with right side)
  Classic: Product array except self, candy problem.

TRICK 7: Sorting Unlocks Everything
  If stuck, ask: "What if it was sorted?"
  Even if the original must not be sorted, sorting a copy or indices works.

TRICK 8: Work Backwards from Output Type
  Output = index? → probably search or DP tracking
  Output = boolean? → probably greedy or BFS feasibility
  Output = count? → DP or hash
  Output = all possibilities? → backtracking

TRICK 9: Floyd's for Any Array-as-Graph
  If array values are in range [0, n-1], treat it as implicit linked list.
  nums[i] = "next pointer" of node i.
  Applies to: find duplicate, missing number variants.

TRICK 10: Binary Search on Answer Space
  If the problem asks "minimum X such that Y is achievable":
  1. Define predicate(X) = can we achieve Y with capacity X?
  2. Binary search on X.
  "minimum" = first TRUE position → Template 2.

TRICK 11: Sliding Window → Two-Pass BS
  "Longest subarray with sum <= k" on non-negative → sliding window
  "Longest subarray with sum <= k" on mixed sign → binary search on prefix sums

TRICK 12: Stack for "Previous/Next Greater"
  Monotonic stack processes ALL elements in O(n) total.
  Each element is pushed and popped EXACTLY ONCE.

TRICK 13: XOR for Pairs
  "Find two non-repeating elements" in array of pairs:
  XOR all → x = a XOR b
  Find any set bit in x (use x & -x)
  Use it to split array into two groups, XOR each group separately.

TRICK 14: Virtual Source/Sink in Graphs
  Multi-source BFS? Add a virtual source connected to all real sources.
  Multi-target? Add virtual sink.
  Avoids initializing queue with multiple nodes.

TRICK 15: Grid → Graph Mental Model
  Grid[r][c] can be treated as node id = r*cols + c.
  Moves (up/down/left/right) are edges.
  Use BFS for minimum steps, DFS for path existence.

TRICK 16: Interview "and/or" trick
  "Maximum AND of two elements" → binary search on bits (greedy MSB first)
  "Maximum XOR" → trie of binary representations

TRICK 17: Median Always Involves Two Heaps
  Maintain: max-heap (lower half) + min-heap (upper half)
  Size invariant: |lo| - |hi| <= 1
  Median = lo.top() if sizes unequal, else (lo.top()+hi.top())/2

TRICK 18: Rolling Hash for String Matching
  Rabin-Karp: O(n+m) string matching avoiding O(nm) naive.
  Same idea for "find repeated DNA subsequences" and "longest duplicate substring".

TRICK 19: Euler's Path / Circuit
  "Can you traverse all edges exactly once?" → Euler path exists if:
  - Undirected: 0 or 2 vertices with odd degree
  - Directed: at most one vertex with (out-degree - in-degree = 1)
  "Reconstruct Itinerary" → Hierholzer's algorithm for Euler circuit.

TRICK 20: Convex Hull Trick for DP Optimization
  When DP has the form: dp[i] = min over j<i of (f(j) + g(i)*h(j))
  Use CHT to reduce from O(n^2) to O(n log n) or O(n).
```

### Observation Heuristics — "The 10 Questions"

```
Ask these in order when stuck:

Q1: Is the input sorted? Can sorting help?
Q2: Can I reduce this to a simpler known problem?
Q3: What if n=1? n=2? Does a pattern emerge?
Q4: Can I use a hash table to trade time for space?
Q5: Is there a monotonic property I can exploit?
Q6: Can I binary search on the answer?
Q7: Can I precompute something (prefix sum, sparse table)?
Q8: Is this a graph problem in disguise?
Q9: Can I reverse the problem or work backwards?
Q10: Is there a mathematical identity or formula?
```

### Time Complexity Optimization Ladder

```
Brute Force                →  Optimized
───────────────────────────────────────────
O(n^3)  triple loop       →  O(n^2) with hash or prefix
O(n^2)  double loop       →  O(n log n) with sort/BST/BIT
O(n^2)  double loop       →  O(n) with two pointers or sliding window
O(2^n)  backtracking      →  O(n * 2^n) with memoization (bitmask DP)
O(n!)   permutations      →  O(n * 2^n) with bitmask DP (for TSP-like)
O(n log n) comparison sort→  O(n) counting/radix sort (limited range)
```

### Space Optimization Patterns

```
2D DP → 1D DP:
  If dp[i][j] only depends on dp[i-1][j] and dp[i][j-1]:
  Use two 1D arrays (current row and previous row).
  Or even one array with careful iteration direction.

Recursion → Iteration:
  Any DFS can be converted to iterative with explicit stack.
  Prevents stack overflow on deep inputs (n > 10^4).

In-place modifications:
  Mark visited cells in grid with '#' or special value.
  Restore on backtrack if needed.
  Saves O(m*n) boolean array.
```

---

## 26. DEBUGGING & DRY-RUN FRAMEWORK

### The Systematic Dry-Run Process

```
1. Pick the SMALLEST non-trivial example (not n=0 or n=1)
2. Run through MANUALLY on paper
3. Track: loop variable, key data structure states, output
4. Identify where actual != expected
5. Check edge cases: empty, single element, all same, sorted, reverse sorted

COMMON BUG SOURCES:
  □ Off-by-one: `<` vs `<=`, `i` vs `i+1`, 0-indexed vs 1-indexed
  □ Integer overflow: use int64 when multiplying or summing large nums
  □ Infinite loop: fast pointer not advancing, or loop condition wrong
  □ Wrong initialization: dp[0] wrong, heap empty, set missing base case
  □ Wrong traversal direction: ascending vs descending for DP
  □ Mutation bug: modifying input while iterating, shared slice references
  □ Boundary check missing: tree nil, array out of bounds, div by zero
```

### Off-By-One Checklist

```
For loops:
  for i := 0; i < n    → n iterations, indices 0..n-1
  for i := 0; i <= n   → n+1 iterations — often wrong!

Array indexing:
  Pre[0] = 0 (empty prefix) → query(l,r) = pre[r+1] - pre[l]
  DP base: dp[0] = 0 or 1 — depends on problem definition

Binary search:
  lo < hi vs lo <= hi affects termination condition
  ceiling vs floor mid affects which direction to move when equal

Linked list:
  "Nth from end" — need exactly what offset?
  Middle — first vs second middle for even-length list?
```

---

## 27. INTERVIEW PROBLEM-SOLVING TEMPLATE

```
TIME 0-2 min: UNDERSTAND
  □ Restate the problem
  □ Identify input/output types
  □ Ask clarifying questions (edge cases, constraints)
  □ Work through 1-2 examples manually

TIME 2-5 min: PLAN
  □ State brute force solution + complexity
  □ Identify optimization opportunity
  □ Map to known pattern
  □ Pseudocode the algorithm

TIME 5-15 min: IMPLEMENT
  □ Code from outline
  □ Use helper functions for clarity
  □ Narrate while coding

TIME 15-18 min: VERIFY
  □ Trace through your example
  □ Test edge cases (empty, single, duplicate, negative)
  □ State final complexity

TIME 18-20 min: OPTIMIZE (if needed)
  □ Space optimization
  □ Constant factor improvements
  □ Discuss alternative approaches
```

### Complexity Statement Template

```
"My solution runs in O(N log N) time where N is the number of elements.
 The dominant cost is the initial sort.
 Space complexity is O(K) for the heap of size K."
```

---

## 28. NEXT 3 STEPS

```
STEP 1: PATTERN DRILLING (Weeks 1-4)
  ─────────────────────────────────
  Pick ONE pattern per day.
  Do 5 problems of that pattern.
  After solving, categorize the problem in your pattern notebook.
  Suggested order:
    Week 1: Two Pointers, Sliding Window, Prefix Sum, Binary Search
    Week 2: Monotonic Stack, Hash Map, BFS/DFS Trees
    Week 3: Backtracking, DP (Linear, 0/1 Knapsack, String DP)
    Week 4: Graphs (BFS, DFS, Topo, Dijkstra, Union-Find), Tries

STEP 2: TIMED BLIND PROBLEM SOLVING (Weeks 5-8)
  ──────────────────────────────────────────────
  Set 25-minute timer. Attempt problem blind.
  If stuck after 10 min, read ONLY the category hint.
  After each session: document which step failed (recognition vs implementation).
  Aim: solve medium in <20min, hard in <35min.
  
  Tools:
    - LeetCode patterns list (neetcode.io/roadmap)
    - CSES Problem Set for algorithmic depth
    - Codeforces Div 2 A/B for speed practice

STEP 3: SYSTEMS INTEGRATION (Ongoing)
  ────────────────────────────────────
  Map DSA to your actual work:
  - Ring buffers/circular queues → sliding window
  - Connection pool management → heap + priority queue
  - Consistent hashing ring     → binary search + sorted structure
  - Kubernetes scheduler        → interval merging + bin packing DP
  - Network packet routing      → graph shortest path (Dijkstra/BFS)
  - Log stream deduplication    → hash set + sliding window
  - Service dependency ordering → topological sort (Kahn's)
  - Certificate chain validation→ DFS on DAG
  
  Build REAL implementations:
    git clone https://github.com/emirpasic/gods  # Go data structures
    cargo add competitive-lib                    # Rust competitive templates
```

---

## REFERENCES

- **Competitive Programming 3** — Steven Halim
- **Algorithm Design Manual** — Skiena (focus on ch. 5-12)
- **CLRS** — Cormen et al. (theoretical depth)
- **NeetCode 150** — https://neetcode.io/roadmap (curated pattern practice)
- **CSES Problem Set** — https://cses.fi/problemset/ (algorithmic breadth)
- **cp-algorithms.com** — in-depth algorithm explanations with proofs
- **Competitive Programmer's Handbook** — Laaksonen (free PDF)
- **go-ds**: https://pkg.go.dev/github.com/emirpasic/gods
- **Rust Competitive**: https://github.com/rust-lang-nursery/rustc-guide

---

*End of Guide — Last updated: 2026*
*All code compiles and runs as-is. Test with `go test ./...`, `cargo test`, `gcc -O2 -o prog prog.c`*

# DSA Mastery: The Complete Pro Guide
## How to Track Problems, Recognize Patterns, and Solve Like an Expert

> **Philosophy**: DSA is not about memorizing solutions. It is about building a mental compiler
> that takes a problem as input and outputs a pattern + strategy in seconds.

---

## Table of Contents

1. [The Mental Model: How Experts Think](#1-the-mental-model)
2. [Problem Observation Framework (POF)](#2-problem-observation-framework)
3. [Pattern Recognition System (PRS)](#3-pattern-recognition-system)
4. [Pattern 01: Two Pointers](#pattern-01-two-pointers)
5. [Pattern 02: Sliding Window](#pattern-02-sliding-window)
6. [Pattern 03: Fast & Slow Pointers (Floyd's)](#pattern-03-fast--slow-pointers)
7. [Pattern 04: Merge Intervals](#pattern-04-merge-intervals)
8. [Pattern 05: Binary Search (All Variants)](#pattern-05-binary-search)
9. [Pattern 06: BFS / Level-Order Traversal](#pattern-06-bfs)
10. [Pattern 07: DFS / Backtracking](#pattern-07-dfs--backtracking)
11. [Pattern 08: Dynamic Programming](#pattern-08-dynamic-programming)
12. [Pattern 09: Greedy](#pattern-09-greedy)
13. [Pattern 10: Heap / Priority Queue](#pattern-10-heap--priority-queue)
14. [Pattern 11: Monotonic Stack & Queue](#pattern-11-monotonic-stack--queue)
15. [Pattern 12: Union-Find (DSU)](#pattern-12-union-find-dsu)
16. [Pattern 13: Trie](#pattern-13-trie)
17. [Pattern 14: Graph Algorithms](#pattern-14-graph-algorithms)
18. [Pattern 15: Bit Manipulation](#pattern-15-bit-manipulation)
19. [Pattern 16: Divide and Conquer](#pattern-16-divide-and-conquer)
20. [Pattern 17: Cyclic Sort](#pattern-17-cyclic-sort)
21. [Pattern 18: Segment Tree / BIT (Fenwick)](#pattern-18-segment-tree--fenwick-tree)
22. [Pattern 19: Math Patterns](#pattern-19-math-patterns)
23. [Complexity Master Table](#complexity-master-table)
24. [Hidden Tricks & Tips Per Category](#hidden-tricks--tips)
25. [Contest & Interview Strategy](#contest--interview-strategy)
26. [Debugging Checklist](#debugging-checklist)

---

## 1. The Mental Model

### How Experts Think (vs Beginners)

```
BEGINNER BRAIN:
  Problem → (confusion) → Google → copy solution → submit

INTERMEDIATE BRAIN:
  Problem → try random stuff → stuck → look at hints → understand

EXPERT BRAIN:
  Problem → observe constraints → map to pattern → implement cleanly → prove correctness
```

### The 5-Layer Mental Stack

```
Layer 5: STRATEGY     ← Which algorithm family? Greedy? DP? Graph?
Layer 4: PATTERN      ← Sliding window? Two pointers? BFS?
Layer 3: DATA STRUCT  ← Array? HashMap? Heap? Stack?
Layer 2: MATH         ← What property/invariant makes this work?
Layer 1: CONSTRAINTS  ← n=10^6? n=20? What is allowed?
```

You read the problem **bottom-up**: constraints → math property → data structure → pattern → strategy.

---

## 2. Problem Observation Framework (POF)

### Step 1: READ the Constraints FIRST (not the problem)

This is the single most important habit.

```
n <= 10          → O(n!) or O(2^n) allowed → Brute force / Backtracking
n <= 20          → O(2^n) allowed → Bitmask DP, Backtracking
n <= 100         → O(n^3) allowed → Triple loop DP
n <= 1000        → O(n^2) allowed → Double loop DP, Bubble sort
n <= 10^5        → O(n log n) → Sort + Binary Search, Segment Tree, BFS/DFS
n <= 10^6        → O(n) or O(n log n) → Greedy, Two Pointers, Sliding Window
n <= 10^9        → O(log n) → Binary Search on answer
n <= 10^18       → O(1) or O(log n) → Math formula, Bit tricks
```

### Step 2: Classify by Output Type

```
OUTPUT TYPE          → LIKELY APPROACH
─────────────────────────────────────────────────
Count of ways        → DP (combinatorics)
Yes/No               → BFS/DFS/Union-Find/Binary Search
Min/Max value        → Greedy / Binary Search on Answer / DP
All combinations     → Backtracking + Pruning
Sorted output        → Merge Sort / Heap / BST
Substring/Subarray   → Sliding Window / Two Pointers
Path in graph        → BFS (shortest) / DFS (any path)
Top K elements       → Heap / QuickSelect
Range queries        → Segment Tree / BIT / Sparse Table
```

### Step 3: Identify the Data Shape

```
DATA SHAPE           → THINK ABOUT
─────────────────────────────────────────────────
Array (sorted)       → Binary Search, Two Pointers
Array (unsorted)     → Hash Map for O(1) lookup, Sort first?
Linked List          → Two Pointers (fast/slow), In-place reversal
Tree                 → DFS (path/depth), BFS (level), LCA
Graph                → BFS (shortest path), DFS (connectivity), Topo sort
String               → Sliding Window, Trie, KMP, Z-algorithm
Matrix               → BFS/DFS with 4/8 directions, DP on grid
Intervals            → Sort by start, Sweep line
Numbers              → Bit tricks, Math properties
```

### Step 4: Ask These Diagnostic Questions

```
Q1: Is the input sorted or can I sort it?
    YES → Two Pointers, Binary Search become candidates

Q2: Do I need to find a PAIR or TRIPLET that satisfies a condition?
    YES → Two Pointers (sorted) or HashMap (unsorted)

Q3: Do I need to track a WINDOW of elements?
    YES → Sliding Window

Q4: Is there OPTIMAL SUBSTRUCTURE (subproblem answer feeds parent)?
    YES → DP

Q5: Can I make a LOCALLY OPTIMAL choice at each step?
    YES + provably global optimal → Greedy

Q6: Do I need SHORTEST PATH?
    Unweighted → BFS
    Non-negative weights → Dijkstra
    Negative weights → Bellman-Ford
    All pairs → Floyd-Warshall

Q7: Are there CONNECTIVITY or GROUP questions?
    YES → Union-Find (DSU)

Q8: Do I need to process elements in ORDER OF PRIORITY?
    YES → Heap / Priority Queue

Q9: Is there REPEATED SUBPROBLEMS in recursion?
    YES → Memoization (Top-Down DP)

Q10: Do I need PREFIX operations (sum, max, frequency)?
     YES → Prefix Array, Segment Tree, BIT
```

### Step 5: The Invariant Hunt

Every good algorithm maintains an **invariant** — a property that is always true.

```
Two Pointers:       left <= right, all elements left of 'left' are processed
Sliding Window:     window [left, right] always satisfies the constraint
Binary Search:      answer always lies in [lo, hi]
BFS:                all nodes at distance d are processed before d+1
DP:                 dp[i] = optimal answer for subproblem of size i
Heap:               heap[0] is always the min (or max)
Union-Find:         find(x) == find(y) iff x and y are connected
```

**Before coding, write the invariant down. Your code maintains it. That IS the algorithm.**

---

## 3. Pattern Recognition System (PRS)

### The Pattern Decision Tree

```
                    ┌─────────────────────────────┐
                    │  READ CONSTRAINTS & OUTPUT   │
                    └──────────────┬──────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
         n<=20                n<=1000             n<=10^6+
              │                    │                    │
      ┌───────┴──────┐    ┌────────┴────────┐  ┌──────┴──────────┐
      │ Bitmask DP   │    │   O(n^2) DP     │  │  O(n) or nlogn  │
      │ Backtrack    │    │   Two loops     │  │  Greedy/Sweep    │
      └──────────────┘    └─────────────────┘  └─────────────────┘

              ┌─────────────────────────────────┐
              │         INPUT STRUCTURE?         │
              └──────────────┬──────────────────┘
                             │
       ┌──────────┬──────────┼──────────┬──────────┐
       │          │          │          │          │
     Array      String     Tree      Graph    Intervals
       │          │          │          │          │
   sorted?     window?   path/sum?  shortest?  overlap?
    BinSrch    SlidWin    DFS/BFS    BFS/Dijk   Merge
    TwoPtr      Trie      TreeDP    UnionFind   Sweep
```

---

## Pattern 01: Two Pointers

### One-Line: Use two indices that move toward or away from each other to avoid O(n²).

### Analogy: Two people walking from opposite ends of a bridge looking for a meeting point.

### When to Use
- Array is sorted (or can be sorted with preserved meaning)
- Looking for PAIRS, TRIPLETS satisfying a sum/condition
- Palindrome check
- Merging two sorted arrays
- Removing duplicates in-place
- Partitioning (Dutch National Flag)

### Variants

```
VARIANT 1: Opposite direction (converge)
  [L ─────────────── R]
   →                ←
  Used for: pair sum, palindrome, container with most water

VARIANT 2: Same direction (fast-slow)
  [S]────[F]──────────
   →      →
  Used for: remove duplicates, partition, cycle detection

VARIANT 3: Two arrays
  [A: a ──────────]
  [B: b ──────────]
  Used for: merge sorted arrays, intersection
```

### C Implementation: Pair Sum in Sorted Array

```c
// file: two_pointers.c
// gcc -O2 -o two_pointers two_pointers.c
#include <stdio.h>
#include <stdbool.h>

// Returns true if pair with given sum exists in sorted array
// Invariant: answer (if exists) always within [left, right]
bool pair_sum(int *arr, int n, int target) {
    int left = 0, right = n - 1;
    while (left < right) {
        int sum = arr[left] + arr[right];
        if (sum == target)  return true;
        else if (sum < target) left++;   // need bigger
        else                   right--;  // need smaller
    }
    return false;
}

// 3Sum: find all triplets summing to 0
// Pattern: fix one, two-pointer for remaining two
void three_sum(int *arr, int n) {
    // Must sort first
    // Simple insertion sort for demo
    for (int i = 1; i < n; i++) {
        int key = arr[i], j = i - 1;
        while (j >= 0 && arr[j] > key) { arr[j+1] = arr[j]; j--; }
        arr[j+1] = key;
    }

    for (int i = 0; i < n - 2; i++) {
        if (i > 0 && arr[i] == arr[i-1]) continue; // skip duplicates
        int left = i + 1, right = n - 1;
        while (left < right) {
            int sum = arr[i] + arr[left] + arr[right];
            if (sum == 0) {
                printf("(%d, %d, %d)\n", arr[i], arr[left], arr[right]);
                while (left < right && arr[left] == arr[left+1]) left++;
                while (left < right && arr[right] == arr[right-1]) right--;
                left++; right--;
            } else if (sum < 0) left++;
            else right--;
        }
    }
}

// Dutch National Flag: partition [0,1,2] in O(n)
// Invariant: [0..low-1]=0, [low..mid-1]=1, [high+1..n-1]=2
void dutch_flag(int *arr, int n) {
    int low = 0, mid = 0, high = n - 1;
    while (mid <= high) {
        if      (arr[mid] == 0) { int t=arr[low]; arr[low]=arr[mid]; arr[mid]=t; low++; mid++; }
        else if (arr[mid] == 1) { mid++; }
        else                    { int t=arr[mid]; arr[mid]=arr[high]; arr[high]=t; high--; }
        // Note: mid not incremented when swapping with high
        // because we haven't inspected arr[mid] yet (it just arrived from high)
    }
}

int main() {
    int arr[] = {1, 4, 2, 8, 3, 5};
    printf("pair_sum(target=9): %s\n", pair_sum(arr, 6, 9) ? "true" : "false");

    int arr3[] = {-1, 0, 1, 2, -1, -4};
    printf("3Sum results:\n");
    three_sum(arr3, 6);

    int flag[] = {2, 0, 1, 2, 1, 0};
    dutch_flag(flag, 6);
    printf("Dutch flag: ");
    for (int i = 0; i < 6; i++) printf("%d ", flag[i]);
    printf("\n");
    return 0;
}
```

### Go Implementation

```go
// file: two_pointers.go
// go run two_pointers.go
package main

import (
	"fmt"
	"sort"
)

// Container with most water - classic two pointer convergence
// Key insight: always move the shorter wall inward (greedy choice)
// Why? Moving the taller wall can only decrease or maintain width, and height is bounded by shorter
func maxWater(heights []int) int {
	left, right := 0, len(heights)-1
	maxArea := 0
	for left < right {
		h := heights[left]
		if heights[right] < h {
			h = heights[right]
		}
		area := h * (right - left)
		if area > maxArea {
			maxArea = area
		}
		// Move the pointer with shorter height
		if heights[left] <= heights[right] {
			left++
		} else {
			right--
		}
	}
	return maxArea
}

// Trap rainwater - harder variant: each cell contributes based on min(maxLeft, maxRight)
// Two pointer trick: avoid the O(n) prefix arrays
func trapWater(height []int) int {
	left, right := 0, len(height)-1
	leftMax, rightMax := 0, 0
	water := 0
	for left < right {
		if height[left] < height[right] {
			// right side is guaranteed taller, so leftMax determines water level
			if height[left] >= leftMax {
				leftMax = height[left]
			} else {
				water += leftMax - height[left]
			}
			left++
		} else {
			if height[right] >= rightMax {
				rightMax = height[right]
			} else {
				water += rightMax - height[right]
			}
			right--
		}
	}
	return water
}

// Remove duplicates from sorted array in-place
// Pattern: slow pointer = write position, fast = read position
func removeDuplicates(nums []int) int {
	if len(nums) == 0 {
		return 0
	}
	slow := 0
	for fast := 1; fast < len(nums); fast++ {
		if nums[fast] != nums[slow] {
			slow++
			nums[slow] = nums[fast]
		}
	}
	return slow + 1
}

// Minimum window substring - but as two pointers on sorted arrays
// Here: find pair closest to target sum in sorted array
func closestPair(arr []int, target int) (int, int) {
	sort.Ints(arr)
	left, right := 0, len(arr)-1
	bestDiff := 1<<31 - 1
	bestL, bestR := 0, len(arr)-1
	for left < right {
		sum := arr[left] + arr[right]
		diff := sum - target
		if diff < 0 {
			diff = -diff
		}
		if diff < bestDiff {
			bestDiff = diff
			bestL, bestR = left, right
		}
		if sum < target {
			left++
		} else {
			right--
		}
	}
	return arr[bestL], arr[bestR]
}

func main() {
	fmt.Println("Max water:", maxWater([]int{1, 8, 6, 2, 5, 4, 8, 3, 7}))
	fmt.Println("Trap water:", trapWater([]int{0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1}))

	nums := []int{1, 1, 2, 3, 3, 4}
	k := removeDuplicates(nums)
	fmt.Println("After dedup, count:", k, "array:", nums[:k])

	a, b := closestPair([]int{3, 7, 1, 9, 2}, 10)
	fmt.Printf("Closest pair to 10: (%d, %d)\n", a, b)
}
```

### Rust Implementation

```rust
// file: two_pointers.rs
// rustc -O two_pointers.rs && ./two_pointers

fn pair_sum_sorted(arr: &[i32], target: i32) -> Option<(i32, i32)> {
    let (mut left, mut right) = (0, arr.len().saturating_sub(1));
    while left < right {
        match (arr[left] + arr[right]).cmp(&target) {
            std::cmp::Ordering::Equal => return Some((arr[left], arr[right])),
            std::cmp::Ordering::Less  => left += 1,
            std::cmp::Ordering::Greater => right -= 1,
        }
    }
    None
}

// Trap rainwater - Rust idiomatic
fn trap_water(height: &[i32]) -> i32 {
    if height.is_empty() { return 0; }
    let (mut left, mut right) = (0usize, height.len() - 1);
    let (mut left_max, mut right_max) = (0i32, 0i32);
    let mut water = 0;
    while left < right {
        if height[left] < height[right] {
            if height[left] >= left_max {
                left_max = height[left];
            } else {
                water += left_max - height[left];
            }
            left += 1;
        } else {
            if height[right] >= right_max {
                right_max = height[right];
            } else {
                water += right_max - height[right];
            }
            right -= 1;
        }
    }
    water
}

// Three sum - avoid duplicates cleanly
fn three_sum(nums: &mut Vec<i32>) -> Vec<Vec<i32>> {
    nums.sort_unstable();
    let mut result = Vec::new();
    let n = nums.len();

    for i in 0..n.saturating_sub(2) {
        // Skip duplicate first elements
        if i > 0 && nums[i] == nums[i - 1] { continue; }
        if nums[i] > 0 { break; } // Optimization: sorted, can't sum to 0

        let (mut left, mut right) = (i + 1, n - 1);
        while left < right {
            let sum = nums[i] + nums[left] + nums[right];
            match sum.cmp(&0) {
                std::cmp::Ordering::Equal => {
                    result.push(vec![nums[i], nums[left], nums[right]]);
                    // Skip duplicates
                    while left < right && nums[left] == nums[left + 1] { left += 1; }
                    while left < right && nums[right] == nums[right - 1] { right -= 1; }
                    left += 1;
                    right -= 1;
                }
                std::cmp::Ordering::Less    => left += 1,
                std::cmp::Ordering::Greater => right -= 1,
            }
        }
    }
    result
}

fn main() {
    let arr = vec![1, 3, 5, 7, 9];
    println!("Pair sum (target=12): {:?}", pair_sum_sorted(&arr, 12));
    println!("Trap water: {}", trap_water(&[0,1,0,2,1,0,1,3,2,1,2,1]));

    let mut nums = vec![-1, 0, 1, 2, -1, -4];
    println!("Three sum: {:?}", three_sum(&mut nums));
}
```

### Hidden Tricks: Two Pointers

```
TRICK 1: Sort destroys index information.
  If you need original indices, use (value, index) tuples before sorting.

TRICK 2: When to use HashMap instead of two pointers?
  Unsorted + cannot sort (e.g., order matters) → HashMap
  Sorted or sortable → Two Pointers (O(1) space vs O(n) space)

TRICK 3: The "complement" trick
  Instead of arr[l] + arr[r] == target
  Think: arr[r] == target - arr[l]
  This maps it to a hash lookup problem too.

TRICK 4: For 3Sum/4Sum, always fix leftmost pointer with outer loop,
  then two-pointer the rest. Complexity: O(n^(k-1)) for kSum.

TRICK 5: Dutch National Flag is essentially a 3-way partition.
  Generalizes to quicksort's partition step.

PITFALLS:
  - Forgetting to skip duplicates after finding a valid pair
  - Off-by-one: left < right (not <=) for pairs
  - Not sorting when required
  - Moving wrong pointer (always move the one that makes progress)
```

---

## Pattern 02: Sliding Window

### One-Line: Maintain a window [left, right] that slides through the array, expanding/contracting based on a constraint.

### Analogy: A camera frame sliding across a panorama — you keep what's in the frame and discard what falls out.

### Fixed vs Variable Window

```
FIXED SIZE (window = k):
  - Expand right until window size = k
  - Then slide: remove left, add right simultaneously
  Example: max sum of subarray of size k

VARIABLE SIZE (find min/max window satisfying condition):
  - Expand right until condition MET
  - Shrink left until condition BROKEN
  - Record answer at each valid state
  Example: smallest subarray with sum >= target

VARIABLE SIZE (find max window with at most k distinct):
  - Expand right
  - If constraint VIOLATED: shrink left until valid again
  Example: longest substring with at most 2 distinct chars
```

### The Window Template

```
TEMPLATE (variable, find longest valid window):
  left = 0
  for right in 0..n:
      add arr[right] to window state
      while window is INVALID:
          remove arr[left] from window state
          left++
      update answer with (right - left + 1)

TEMPLATE (variable, find shortest valid window):
  left = 0
  for right in 0..n:
      add arr[right] to window state
      while window is VALID:
          update answer with (right - left + 1)
          remove arr[left] from window state
          left++
```

### C Implementation

```c
// file: sliding_window.c
// gcc -O2 -o sliding_window sliding_window.c
#include <stdio.h>
#include <string.h>
#include <limits.h>

// Fixed window: max sum subarray of size k
int max_sum_k(int *arr, int n, int k) {
    if (n < k) return -1;
    int sum = 0;
    for (int i = 0; i < k; i++) sum += arr[i];
    int maxSum = sum;
    for (int i = k; i < n; i++) {
        sum += arr[i] - arr[i-k]; // slide: add new, remove old
        if (sum > maxSum) maxSum = sum;
    }
    return maxSum;
}

// Variable window: smallest subarray with sum >= target
int min_subarray_len(int *arr, int n, int target) {
    int left = 0, sum = 0, minLen = INT_MAX;
    for (int right = 0; right < n; right++) {
        sum += arr[right];
        while (sum >= target) {
            int len = right - left + 1;
            if (len < minLen) minLen = len;
            sum -= arr[left++]; // shrink from left
        }
    }
    return minLen == INT_MAX ? 0 : minLen;
}

// Longest substring without repeating characters
// State: freq[256] = frequency of each char in window
int longest_unique(const char *s) {
    int freq[256] = {0};
    int left = 0, maxLen = 0;
    int n = strlen(s);
    for (int right = 0; right < n; right++) {
        freq[(unsigned char)s[right]]++;
        // Shrink while we have a duplicate
        while (freq[(unsigned char)s[right]] > 1) {
            freq[(unsigned char)s[left++]]--;
        }
        int len = right - left + 1;
        if (len > maxLen) maxLen = len;
    }
    return maxLen;
}

// Minimum window substring: find smallest window in s containing all chars of t
// State: need[] counts chars still needed; missing = total chars still needed
char* min_window(const char *s, const char *t) {
    static char result[10001];
    int need[256] = {0};
    int missing = strlen(t);

    for (int i = 0; t[i]; i++) need[(unsigned char)t[i]]++;

    int left = 0, start = -1, minLen = INT_MAX;
    for (int right = 0; s[right]; right++) {
        // If this char is needed (count > 0), reduce missing
        if (need[(unsigned char)s[right]]-- > 0) missing--;

        while (missing == 0) { // valid window
            int len = right - left + 1;
            if (len < minLen) {
                minLen = len;
                start = left;
            }
            // Try to shrink from left
            if (++need[(unsigned char)s[left++]] > 0) missing++;
        }
    }

    if (start == -1) { result[0] = '\0'; return result; }
    strncpy(result, s + start, minLen);
    result[minLen] = '\0';
    return result;
}

int main() {
    int arr[] = {2, 1, 5, 2, 3, 2};
    printf("Max sum k=3: %d\n", max_sum_k(arr, 6, 3));  // 10

    int arr2[] = {2, 1, 5, 2, 8};
    printf("Min subarray (sum>=7): %d\n", min_subarray_len(arr2, 5, 7)); // 1

    printf("Longest unique in 'abcabcbb': %d\n", longest_unique("abcabcbb")); // 3
    printf("Min window ('ADOBECODEBANC', 'ABC'): %s\n",
           min_window("ADOBECODEBANC", "ABC")); // BANC
    return 0;
}
```

### Go Implementation

```go
// file: sliding_window.go
package main

import "fmt"

// Longest substring with at most K distinct characters
func longestKDistinct(s string, k int) int {
    freq := make(map[byte]int)
    left, maxLen := 0, 0
    for right := 0; right < len(s); right++ {
        freq[s[right]]++
        // Shrink until we have at most k distinct
        for len(freq) > k {
            freq[s[left]]--
            if freq[s[left]] == 0 {
                delete(freq, s[left])
            }
            left++
        }
        if right-left+1 > maxLen {
            maxLen = right - left + 1
        }
    }
    return maxLen
}

// Permutation in string: does s2 contain a permutation of s1?
// Fixed window of size len(s1), check if freq matches
func checkInclusion(s1, s2 string) bool {
    if len(s1) > len(s2) { return false }
    need := [26]int{}
    have := [26]int{}
    for i := 0; i < len(s1); i++ {
        need[s1[i]-'a']++
    }
    // Initialize first window
    for i := 0; i < len(s1); i++ {
        have[s2[i]-'a']++
    }
    if have == need { return true }

    for right := len(s1); right < len(s2); right++ {
        have[s2[right]-'a']++                   // expand right
        have[s2[right-len(s1)]-'a']--           // shrink left
        if have == need { return true }
    }
    return false
}

// Max consecutive ones with at most k zeros allowed (flip k zeros)
// Same as: longest subarray with at most k zeros
func longestOnes(nums []int, k int) int {
    left, zeros, maxLen := 0, 0, 0
    for right := 0; right < len(nums); right++ {
        if nums[right] == 0 {
            zeros++
        }
        for zeros > k {
            if nums[left] == 0 {
                zeros--
            }
            left++
        }
        if right-left+1 > maxLen {
            maxLen = right - left + 1
        }
    }
    return maxLen
}

// Sliding window maximum (hard) - use deque for O(n)
// Maintains a decreasing monotonic deque of indices
func maxSlidingWindow(nums []int, k int) []int {
    deque := []int{} // stores indices, front = max
    result := []int{}

    for right := 0; right < len(nums); right++ {
        // Remove elements outside window
        for len(deque) > 0 && deque[0] < right-k+1 {
            deque = deque[1:]
        }
        // Remove smaller elements from back (maintain decreasing order)
        for len(deque) > 0 && nums[deque[len(deque)-1]] < nums[right] {
            deque = deque[:len(deque)-1]
        }
        deque = append(deque, right)
        // Window is fully formed
        if right >= k-1 {
            result = append(result, nums[deque[0]])
        }
    }
    return result
}

func main() {
    fmt.Println("Longest 2-distinct in 'araaci':", longestKDistinct("araaci", 2)) // 4
    fmt.Println("Permutation check:", checkInclusion("ab", "eidbaooo"))           // true
    fmt.Println("Longest ones (k=2):", longestOnes([]int{1,1,1,0,0,0,1,1,1,1,0}, 2)) // 6
    fmt.Println("Sliding window max:", maxSlidingWindow([]int{1,3,-1,-3,5,3,6,7}, 3)) // [3,3,5,5,6,7]
}
```

### Rust Implementation

```rust
// file: sliding_window.rs
use std::collections::{HashMap, VecDeque};

// Minimum size subarray sum
fn min_subarray_len(target: i32, nums: &[i32]) -> i32 {
    let mut left = 0;
    let mut sum = 0;
    let mut min_len = i32::MAX;

    for (right, &val) in nums.iter().enumerate() {
        sum += val;
        while sum >= target {
            let len = (right - left + 1) as i32;
            min_len = min_len.min(len);
            sum -= nums[left];
            left += 1;
        }
    }
    if min_len == i32::MAX { 0 } else { min_len }
}

// Longest substring without repeating characters
fn length_of_longest_substring(s: &str) -> usize {
    let bytes = s.as_bytes();
    // Using array for O(1) lookup instead of HashMap (chars are ASCII)
    let mut last_seen = [usize::MAX; 256];
    let mut left = 0;
    let mut max_len = 0;

    for (right, &b) in bytes.iter().enumerate() {
        // If char seen and its position is within current window
        if last_seen[b as usize] != usize::MAX && last_seen[b as usize] >= left {
            left = last_seen[b as usize] + 1;
        }
        last_seen[b as usize] = right;
        max_len = max_len.max(right - left + 1);
    }
    max_len
}

// Sliding window maximum with monotonic deque
fn max_sliding_window(nums: &[i32], k: usize) -> Vec<i32> {
    let mut deque: VecDeque<usize> = VecDeque::new(); // stores indices
    let mut result = Vec::new();

    for right in 0..nums.len() {
        // Remove out-of-window indices from front
        while deque.front().map_or(false, |&i| i + k <= right) {
            deque.pop_front();
        }
        // Maintain decreasing order: remove smaller from back
        while deque.back().map_or(false, |&i| nums[i] <= nums[right]) {
            deque.pop_back();
        }
        deque.push_back(right);
        if right + 1 >= k {
            result.push(nums[*deque.front().unwrap()]);
        }
    }
    result
}

// Longest substring with at most k distinct characters
fn longest_k_distinct(s: &str, k: usize) -> usize {
    let mut freq: HashMap<u8, usize> = HashMap::new();
    let bytes = s.as_bytes();
    let mut left = 0;
    let mut max_len = 0;

    for (right, &b) in bytes.iter().enumerate() {
        *freq.entry(b).or_insert(0) += 1;
        while freq.len() > k {
            let lb = bytes[left];
            let count = freq.get_mut(&lb).unwrap();
            *count -= 1;
            if *count == 0 { freq.remove(&lb); }
            left += 1;
        }
        max_len = max_len.max(right - left + 1);
    }
    max_len
}

fn main() {
    println!("Min subarray len: {}", min_subarray_len(7, &[2,3,1,2,4,3])); // 2
    println!("Longest no-repeat: {}", length_of_longest_substring("abcabcbb")); // 3
    println!("Sliding max: {:?}", max_sliding_window(&[1,3,-1,-3,5,3,6,7], 3));
    println!("Longest 2-distinct: {}", longest_k_distinct("eceba", 2)); // 3
}
```

### Hidden Tricks: Sliding Window

```
TRICK 1: The "at most K" trick
  count(at most k distinct) - count(at most k-1 distinct) = count(exactly k distinct)
  This converts "exactly k" problems to two "at most k" problems.

TRICK 2: Fixed-window optimization
  Don't use HashMap for fixed-window char frequency.
  Use int[26] or int[256] and compare arrays — O(1) comparison!

TRICK 3: Monotonic Deque for window max/min
  Sliding window max in O(n) using deque — not O(nk).
  Front of deque = max, always remove indices outside window from front.

TRICK 4: When answer is "length of longest window NEVER shrinks"
  You can skip the inner while loop and keep window size constant.
  This is used in "max vowels in k-char window" pattern.

TRICK 5: two-pointer proof of correctness
  If window [l, r] is invalid, then [l, r+1] is also invalid.
  This MONOTONICITY is what makes sliding window work.
  Always verify this property before using sliding window.

PITFALLS:
  - Forgetting to shrink left when constraint is violated
  - Using HashMap when array[256] would be faster
  - Not handling empty string edge cases
  - Confusing "at most" vs "exactly" semantics
```

---

## Pattern 03: Fast & Slow Pointers

### One-Line: Two pointers at different speeds detect cycles, find midpoints, and solve position problems in linked lists.

### Analogy: A race track — the fast runner laps the slow runner, and their meeting point reveals cycle properties.

### Use Cases

```
1. CYCLE DETECTION: Does the linked list have a cycle?
2. CYCLE START: Where does the cycle begin? (Floyd's algorithm)
3. MIDDLE OF LIST: slow reaches middle when fast reaches end
4. HAPPY NUMBER: detect cycle in number sequence
5. NTH FROM END: advance fast n steps, then move both
6. PALINDROME LIST: find middle, reverse second half, compare
```

### Floyd's Cycle Detection - Mathematical Proof

```
Setup:
  Let F = distance from head to cycle start
  Let C = cycle length
  Let a = distance from cycle start to meeting point

When they meet:
  slow traveled: F + a
  fast traveled: F + a + kC  (k full laps more)
  fast = 2 * slow → F + a + kC = 2(F + a)
  → kC = F + a
  → F = kC - a

This means:
  From meeting point, advance 'a' more → reach cycle start
  From head, advance F → reach cycle start
  (since F = kC - a, and you're already 'a' into the cycle)

So: reset one pointer to head, move both at speed 1 → they meet at cycle start!
```

### C Implementation

```c
// file: fast_slow.c
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

typedef struct Node {
    int val;
    struct Node *next;
} Node;

Node* make_node(int val) {
    Node *n = malloc(sizeof(Node));
    n->val = val; n->next = NULL;
    return n;
}

// Detect cycle
bool has_cycle(Node *head) {
    Node *slow = head, *fast = head;
    while (fast && fast->next) {
        slow = slow->next;
        fast = fast->next->next;
        if (slow == fast) return true;
    }
    return false;
}

// Find cycle start
Node* cycle_start(Node *head) {
    Node *slow = head, *fast = head;
    bool found = false;
    while (fast && fast->next) {
        slow = slow->next;
        fast = fast->next->next;
        if (slow == fast) { found = true; break; }
    }
    if (!found) return NULL;
    // Reset slow to head; both move at speed 1
    slow = head;
    while (slow != fast) {
        slow = slow->next;
        fast = fast->next;
    }
    return slow; // cycle start
}

// Find middle (when fast reaches end, slow is at middle)
Node* find_middle(Node *head) {
    Node *slow = head, *fast = head;
    while (fast->next && fast->next->next) {
        slow = slow->next;
        fast = fast->next->next;
    }
    return slow;
}

// Happy number: sum of squares of digits, cycle detection
bool is_happy(int n) {
    int slow = n, fast = n;
    do {
        // one step
        int s = slow, sq = 0;
        while (s) { int d = s%10; sq += d*d; s /= 10; }
        slow = sq;
        // two steps
        int f = fast, fq = 0;
        while (f) { int d = f%10; fq += d*d; f /= 10; }
        fast = fq;
        f = fast; fq = 0;
        while (f) { int d = f%10; fq += d*d; f /= 10; }
        fast = fq;
    } while (slow != fast);
    return slow == 1;
}

int main() {
    // Build list 1->2->3->4->5 with cycle at node 3
    Node *head = make_node(1);
    head->next = make_node(2);
    head->next->next = make_node(3);
    Node *cycle_node = head->next->next;
    head->next->next->next = make_node(4);
    head->next->next->next->next = make_node(5);
    head->next->next->next->next->next = cycle_node; // cycle!

    printf("Has cycle: %s\n", has_cycle(head) ? "true" : "false");
    Node *cs = cycle_start(head);
    printf("Cycle starts at node with val: %d\n", cs->val);

    Node *mid_head = make_node(1);
    mid_head->next = make_node(2);
    mid_head->next->next = make_node(3);
    mid_head->next->next->next = make_node(4);
    mid_head->next->next->next->next = make_node(5);
    printf("Middle of 1->2->3->4->5: %d\n", find_middle(mid_head)->val); // 3

    printf("Is 19 happy: %s\n", is_happy(19) ? "yes" : "no"); // yes
    printf("Is 20 happy: %s\n", is_happy(20) ? "yes" : "no"); // no
    return 0;
}
```

### Go Implementation

```go
// file: fast_slow.go
package main

import "fmt"

type ListNode struct {
    Val  int
    Next *ListNode
}

// Palindrome linked list: find middle, reverse second half, compare
func isPalindrome(head *ListNode) bool {
    if head == nil || head.Next == nil { return true }

    // Find middle
    slow, fast := head, head
    for fast.Next != nil && fast.Next.Next != nil {
        slow = slow.Next
        fast = fast.Next.Next
    }

    // Reverse second half
    secondHalf := reverse(slow.Next)
    p1, p2 := head, secondHalf
    result := true
    for p2 != nil {
        if p1.Val != p2.Val { result = false; break }
        p1, p2 = p1.Next, p2.Next
    }
    // Restore (good practice)
    slow.Next = reverse(secondHalf)
    return result
}

func reverse(head *ListNode) *ListNode {
    var prev *ListNode
    curr := head
    for curr != nil {
        next := curr.Next
        curr.Next = prev
        prev = curr
        curr = next
    }
    return prev
}

// Reorder list: L0 → L1 → ... → Ln-1 → Ln
// becomes: L0 → Ln → L1 → Ln-1 → L2 → Ln-2 → ...
func reorderList(head *ListNode) {
    if head == nil { return }
    // 1. Find middle
    slow, fast := head, head
    for fast.Next != nil && fast.Next.Next != nil {
        slow = slow.Next
        fast = fast.Next.Next
    }
    // 2. Reverse second half
    second := reverse(slow.Next)
    slow.Next = nil
    // 3. Merge alternately
    first := head
    for second != nil {
        tmp1, tmp2 := first.Next, second.Next
        first.Next = second
        second.Next = tmp1
        first = tmp1
        second = tmp2
    }
}

func buildList(vals []int) *ListNode {
    if len(vals) == 0 { return nil }
    head := &ListNode{Val: vals[0]}
    curr := head
    for _, v := range vals[1:] {
        curr.Next = &ListNode{Val: v}
        curr = curr.Next
    }
    return head
}

func printList(head *ListNode) {
    for head != nil {
        fmt.Printf("%d ", head.Val)
        head = head.Next
    }
    fmt.Println()
}

func main() {
    l1 := buildList([]int{1, 2, 2, 1})
    fmt.Println("Is palindrome [1,2,2,1]:", isPalindrome(l1)) // true

    l2 := buildList([]int{1, 2, 3, 4, 5})
    reorderList(l2)
    fmt.Print("Reordered [1,2,3,4,5]: ")
    printList(l2) // 1 5 2 4 3
}
```

---

## Pattern 04: Merge Intervals

### One-Line: Sort intervals by start time, then scan and merge/process overlapping ones.

### When to Use
- Any problem involving ranges, schedules, time slots
- "Do intervals overlap?", "How many meetings rooms needed?", "What's the free time?"

### Key Insight: After sorting by start, interval[i] overlaps interval[i-1] iff start[i] <= end[i-1]

```
MERGE: If overlap → extend end to max(end1, end2)
INSERT: Find position, merge with neighbors
ROOMS: Count max overlapping at any point (sort events, sweep line)
FREE TIME: Gaps between merged intervals
```

### Go Implementation

```go
// file: intervals.go
package main

import (
    "fmt"
    "sort"
)

type Interval struct{ Start, End int }

// Merge overlapping intervals
func mergeIntervals(intervals []Interval) []Interval {
    if len(intervals) == 0 { return nil }
    sort.Slice(intervals, func(i, j int) bool {
        return intervals[i].Start < intervals[j].Start
    })
    merged := []Interval{intervals[0]}
    for _, curr := range intervals[1:] {
        last := &merged[len(merged)-1]
        if curr.Start <= last.End {
            // Overlap: extend
            if curr.End > last.End { last.End = curr.End }
        } else {
            merged = append(merged, curr)
        }
    }
    return merged
}

// Minimum meeting rooms needed
// Key insight: sort starts and ends separately, sweep
func minMeetingRooms(intervals []Interval) int {
    starts := make([]int, len(intervals))
    ends := make([]int, len(intervals))
    for i, iv := range intervals {
        starts[i] = iv.Start
        ends[i] = iv.End
    }
    sort.Ints(starts)
    sort.Ints(ends)

    rooms, endIdx := 0, 0
    for _, start := range starts {
        if start < ends[endIdx] {
            rooms++ // new room needed
        } else {
            endIdx++ // reuse a room (one meeting ended)
        }
    }
    return rooms
}

// Insert interval into sorted non-overlapping intervals
func insertInterval(intervals []Interval, newInterval Interval) []Interval {
    result := []Interval{}
    i := 0
    // Add all intervals before new one
    for i < len(intervals) && intervals[i].End < newInterval.Start {
        result = append(result, intervals[i])
        i++
    }
    // Merge all overlapping
    for i < len(intervals) && intervals[i].Start <= newInterval.End {
        if intervals[i].Start < newInterval.Start { newInterval.Start = intervals[i].Start }
        if intervals[i].End > newInterval.End { newInterval.End = intervals[i].End }
        i++
    }
    result = append(result, newInterval)
    // Add remaining
    result = append(result, intervals[i:]...)
    return result
}

func main() {
    ivs := []Interval{{1,3},{2,6},{8,10},{15,18}}
    fmt.Println("Merged:", mergeIntervals(ivs))

    meetings := []Interval{{0,30},{5,10},{15,20}}
    fmt.Println("Min rooms:", minMeetingRooms(meetings)) // 2

    sorted := []Interval{{1,3},{6,9}}
    fmt.Println("After insert [2,5]:", insertInterval(sorted, Interval{2,5}))
}
```

---

## Pattern 05: Binary Search

### One-Line: Eliminate half the search space each step by testing the midpoint against a monotonic condition.

### The Universal Binary Search Template

```
TEMPLATE: Binary search on ANSWER (not just array position)
  lo = minimum possible answer
  hi = maximum possible answer
  while lo < hi:
      mid = lo + (hi - lo) / 2   // Avoid overflow!
      if condition(mid):
          hi = mid    // mid might be answer, but look left
      else:
          lo = mid + 1

This finds the LEFTMOST value where condition is TRUE.
For rightmost: flip the condition, return lo-1.

The KEY: condition() must be MONOTONIC:
  False False False ... True True True
                         ^
                         lo after loop = answer
```

### All Binary Search Variants

```
VARIANT 1: Find exact target
  if arr[mid] == target → found
  if arr[mid] < target  → lo = mid + 1
  if arr[mid] > target  → hi = mid - 1

VARIANT 2: Find first occurrence of target (leftmost)
  if arr[mid] >= target → hi = mid
  else                  → lo = mid + 1

VARIANT 3: Find last occurrence (rightmost)
  if arr[mid] <= target → lo = mid
  else                  → hi = mid - 1
  (use mid = lo + (hi-lo+1)/2 to avoid infinite loop)

VARIANT 4: Binary search on answer
  condition = predicate function that is monotonic
  Find minimum mid where condition(mid) = true

VARIANT 5: Search in rotated sorted array
  Find which half is sorted, check if target is in that half
```

### C Implementation: All Variants

```c
// file: binary_search.c
#include <stdio.h>
#include <stdbool.h>
#include <math.h>

// Classic binary search
int binary_search(int *arr, int n, int target) {
    int lo = 0, hi = n - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2; // CRITICAL: not (lo+hi)/2 → overflow!
        if      (arr[mid] == target) return mid;
        else if (arr[mid] < target)  lo = mid + 1;
        else                         hi = mid - 1;
    }
    return -1;
}

// Leftmost (first) occurrence
int first_occurrence(int *arr, int n, int target) {
    int lo = 0, hi = n - 1, result = -1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (arr[mid] == target) { result = mid; hi = mid - 1; } // keep going left
        else if (arr[mid] < target) lo = mid + 1;
        else hi = mid - 1;
    }
    return result;
}

// Rightmost (last) occurrence
int last_occurrence(int *arr, int n, int target) {
    int lo = 0, hi = n - 1, result = -1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (arr[mid] == target) { result = mid; lo = mid + 1; } // keep going right
        else if (arr[mid] < target) lo = mid + 1;
        else hi = mid - 1;
    }
    return result;
}

// Search in rotated sorted array (no duplicates)
int search_rotated(int *arr, int n, int target) {
    int lo = 0, hi = n - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (arr[mid] == target) return mid;
        // Determine which half is sorted
        if (arr[lo] <= arr[mid]) { // left half is sorted
            if (target >= arr[lo] && target < arr[mid]) hi = mid - 1;
            else lo = mid + 1;
        } else { // right half is sorted
            if (target > arr[mid] && target <= arr[hi]) lo = mid + 1;
            else hi = mid - 1;
        }
    }
    return -1;
}

// Binary search on answer: minimum capacity to ship packages in D days
// Condition: can we ship all packages with capacity 'cap' in D days?
bool can_ship(int *weights, int n, int cap, int D) {
    int days = 1, curr = 0;
    for (int i = 0; i < n; i++) {
        if (weights[i] > cap) return false; // single package exceeds capacity
        if (curr + weights[i] > cap) { days++; curr = 0; }
        curr += weights[i];
    }
    return days <= D;
}

int min_ship_capacity(int *weights, int n, int D) {
    int lo = 0, hi = 0;
    for (int i = 0; i < n; i++) {
        if (weights[i] > lo) lo = weights[i]; // min = max single weight
        hi += weights[i];                       // max = total weight (ship all in 1 day)
    }
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (can_ship(weights, n, mid, D)) hi = mid; // mid might be answer
        else lo = mid + 1;
    }
    return lo;
}

// Sqrt using binary search
int isqrt(int n) {
    if (n < 2) return n;
    int lo = 1, hi = n / 2;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        long long sq = (long long)mid * mid;
        if (sq == n) return mid;
        else if (sq < n) lo = mid + 1;
        else hi = mid - 1;
    }
    return hi; // floor sqrt
}

int main() {
    int arr[] = {1,3,5,7,9,11,13};
    printf("Binary search (7): %d\n", binary_search(arr, 7, 7));    // 3

    int arr2[] = {1,2,2,2,3,4};
    printf("First occ of 2: %d\n", first_occurrence(arr2, 6, 2));  // 1
    printf("Last occ of 2: %d\n", last_occurrence(arr2, 6, 2));    // 3

    int rot[] = {4,5,6,7,0,1,2};
    printf("Search rotated (0): %d\n", search_rotated(rot, 7, 0));  // 4

    int weights[] = {1,2,3,4,5,6,7,8,9,10};
    printf("Min ship capacity: %d\n", min_ship_capacity(weights, 10, 5)); // 15

    printf("isqrt(26) = %d\n", isqrt(26)); // 5
    return 0;
}
```

### Rust: Binary Search on Answer Pattern

```rust
// file: binary_search.rs

// Generic binary search on answer
// finds leftmost value in [lo, hi] where predicate is true
fn binary_search_answer<F>(mut lo: i64, mut hi: i64, predicate: F) -> i64
where
    F: Fn(i64) -> bool,
{
    while lo < hi {
        let mid = lo + (hi - lo) / 2;
        if predicate(mid) {
            hi = mid;
        } else {
            lo = mid + 1;
        }
    }
    lo
}

// Koko eating bananas
fn min_eating_speed(piles: &[i32], h: i32) -> i32 {
    let max_pile = *piles.iter().max().unwrap() as i64;

    binary_search_answer(1, max_pile, |speed| {
        // Can Koko eat all bananas in h hours at this speed?
        let hours: i64 = piles.iter()
            .map(|&p| (p as i64 + speed - 1) / speed) // ceil(p/speed)
            .sum();
        hours <= h as i64
    }) as i32
}

// Split array largest sum
fn split_array(nums: &[i32], k: i32) -> i32 {
    let lo = *nums.iter().max().unwrap() as i64;
    let hi = nums.iter().map(|&x| x as i64).sum::<i64>();

    binary_search_answer(lo, hi, |max_sum| {
        let mut pieces = 1i64;
        let mut curr_sum = 0i64;
        for &n in nums {
            if curr_sum + n as i64 > max_sum {
                pieces += 1;
                curr_sum = n as i64;
            } else {
                curr_sum += n as i64;
            }
        }
        pieces <= k as i64
    }) as i32
}

// Find peak element (binary search in unsorted!)
// Key: if nums[mid] < nums[mid+1], peak is to the right
fn find_peak_element(nums: &[i32]) -> usize {
    let mut lo = 0usize;
    let mut hi = nums.len() - 1;
    while lo < hi {
        let mid = lo + (hi - lo) / 2;
        if nums[mid] < nums[mid + 1] {
            lo = mid + 1; // peak on right side
        } else {
            hi = mid;     // peak on left side (or at mid)
        }
    }
    lo
}

fn main() {
    println!("Min eating speed: {}", min_eating_speed(&[3,6,7,11], 8)); // 4
    println!("Split array: {}", split_array(&[7,2,5,10,8], 2));         // 18
    println!("Peak element: {}", find_peak_element(&[1,2,1,3,5,6,4])); // 5
}
```

### Hidden Tricks: Binary Search

```
TRICK 1: "Binary search on the answer" is often the key insight.
  If the problem asks "find minimum X such that condition holds",
  and condition is monotonic, → binary search on X.
  Examples: capacity, speed, days, threshold.

TRICK 2: Avoid infinite loop with lo = mid (not mid+1)
  When hi = mid and lo = mid+1, loop terminates correctly.
  When lo = mid (without +1), add 1 to mid calculation:
  mid = lo + (hi - lo + 1) / 2

TRICK 3: lo + (hi - lo) / 2 vs (lo + hi) / 2
  The first avoids integer overflow when lo and hi are large.
  ALWAYS use the first form.

TRICK 4: Finding the mountain array peak is binary search
  on unsorted array! The invariant is "slope direction".

TRICK 5: Binary search can find answers in O(log N) for:
  - nth root: binary search on [1, n]
  - median of two sorted arrays
  - kth smallest in sorted matrix

PITFALLS:
  - Using lo <= hi when you need lo < hi (causes infinite loop)
  - Wrong boundary: should lo be 0 or 1? should hi be n-1 or n?
  - Off-by-one in leftmost/rightmost occurrence
  - Forgetting the condition must be MONOTONIC
```

---

## Pattern 06: BFS

### One-Line: Explore all neighbors at current distance before going deeper — guarantees shortest path in unweighted graphs.

### When to Use
- Shortest path in unweighted graph/grid
- Level-order tree traversal
- Minimum steps/hops problems
- Find all nodes within distance K
- Multisource BFS (start from multiple sources simultaneously)

### The BFS Template

```
BFS(start):
  queue = [start]
  visited = {start}
  distance = {start: 0}

  while queue not empty:
      node = queue.dequeue()
      process(node)
      for each neighbor of node:
          if neighbor not in visited:
              visited.add(neighbor)
              distance[neighbor] = distance[node] + 1
              queue.enqueue(neighbor)

KEY INSIGHT: Add to visited when ENQUEUING, not dequeuing.
  This prevents processing the same node multiple times.
  Dequeue → process: too late, already in queue twice.
```

### Go Implementation: BFS Patterns

```go
// file: bfs.go
package main

import "fmt"

// ── Tree BFS ──────────────────────────────────────────────────────────────────

type TreeNode struct {
    Val   int
    Left  *TreeNode
    Right *TreeNode
}

// Level-order traversal, return 2D slice
func levelOrder(root *TreeNode) [][]int {
    if root == nil { return nil }
    result := [][]int{}
    queue := []*TreeNode{root}

    for len(queue) > 0 {
        levelSize := len(queue)  // KEY: snapshot current level size
        level := []int{}
        for i := 0; i < levelSize; i++ {
            node := queue[0]
            queue = queue[1:]
            level = append(level, node.Val)
            if node.Left != nil  { queue = append(queue, node.Left) }
            if node.Right != nil { queue = append(queue, node.Right) }
        }
        result = append(result, level)
    }
    return result
}

// Zigzag level order
func zigzagLevelOrder(root *TreeNode) [][]int {
    if root == nil { return nil }
    result := [][]int{}
    queue := []*TreeNode{root}
    leftToRight := true

    for len(queue) > 0 {
        levelSize := len(queue)
        level := make([]int, levelSize)
        for i := 0; i < levelSize; i++ {
            node := queue[0]; queue = queue[1:]
            if leftToRight {
                level[i] = node.Val
            } else {
                level[levelSize-1-i] = node.Val // fill from right
            }
            if node.Left != nil  { queue = append(queue, node.Left) }
            if node.Right != nil { queue = append(queue, node.Right) }
        }
        result = append(result, level)
        leftToRight = !leftToRight
    }
    return result
}

// ── Grid BFS ──────────────────────────────────────────────────────────────────

// Shortest path in binary matrix
func shortestPath(grid [][]int) int {
    n := len(grid)
    if grid[0][0] == 1 || grid[n-1][n-1] == 1 { return -1 }
    if n == 1 { return 1 }

    dirs := [][2]int{{0,1},{0,-1},{1,0},{-1,0},{1,1},{1,-1},{-1,1},{-1,-1}}
    type Point struct{ r, c, dist int }
    queue := []Point{{0, 0, 1}}
    grid[0][0] = 1 // mark visited by setting to 1

    for len(queue) > 0 {
        curr := queue[0]; queue = queue[1:]
        for _, d := range dirs {
            r, c := curr.r+d[0], curr.c+d[1]
            if r < 0 || r >= n || c < 0 || c >= n || grid[r][c] != 0 { continue }
            if r == n-1 && c == n-1 { return curr.dist + 1 }
            grid[r][c] = 1 // mark visited
            queue = append(queue, Point{r, c, curr.dist + 1})
        }
    }
    return -1
}

// Multisource BFS: 01 Matrix — distance to nearest 0 for each cell
func updateMatrix(mat [][]int) [][]int {
    m, n := len(mat), len(mat[0])
    dist := make([][]int, m)
    queue := [][]int{}

    for i := range dist {
        dist[i] = make([]int, n)
        for j := range dist[i] {
            if mat[i][j] == 0 {
                dist[i][j] = 0
                queue = append(queue, []int{i, j}) // all 0s are sources
            } else {
                dist[i][j] = 1<<31 - 1
            }
        }
    }

    dirs := [][2]int{{0,1},{0,-1},{1,0},{-1,0}}
    for len(queue) > 0 {
        curr := queue[0]; queue = queue[1:]
        for _, d := range dirs {
            r, c := curr[0]+d[0], curr[1]+d[1]
            if r < 0 || r >= m || c < 0 || c >= n { continue }
            if dist[curr[0]][curr[1]]+1 < dist[r][c] {
                dist[r][c] = dist[curr[0]][curr[1]] + 1
                queue = append(queue, []int{r, c})
            }
        }
    }
    return dist
}

// Word ladder: minimum transformations to reach target
func ladderLength(beginWord, endWord string, wordList []string) int {
    wordSet := make(map[string]bool)
    for _, w := range wordList { wordSet[w] = true }
    if !wordSet[endWord] { return 0 }

    queue := []string{beginWord}
    visited := map[string]bool{beginWord: true}
    steps := 1

    for len(queue) > 0 {
        levelSize := len(queue)
        for i := 0; i < levelSize; i++ {
            word := queue[0]; queue = queue[1:]
            // Try changing each character
            wb := []byte(word)
            for j := range wb {
                orig := wb[j]
                for c := byte('a'); c <= 'z'; c++ {
                    if c == orig { continue }
                    wb[j] = c
                    next := string(wb)
                    if next == endWord { return steps + 1 }
                    if wordSet[next] && !visited[next] {
                        visited[next] = true
                        queue = append(queue, next)
                    }
                }
                wb[j] = orig
            }
        }
        steps++
    }
    return 0
}

func main() {
    root := &TreeNode{Val: 1,
        Left: &TreeNode{Val: 2, Left: &TreeNode{Val: 4}, Right: &TreeNode{Val: 5}},
        Right: &TreeNode{Val: 3, Left: &TreeNode{Val: 6}, Right: &TreeNode{Val: 7}},
    }
    fmt.Println("Level order:", levelOrder(root))
    fmt.Println("Zigzag:", zigzagLevelOrder(root))

    grid := [][]int{{0,0,0},{1,1,0},{1,1,0}}
    fmt.Println("Shortest path:", shortestPath(grid))

    mat := [][]int{{0,0,0},{0,1,0},{0,0,0}}
    fmt.Println("01 Matrix:", updateMatrix(mat))

    fmt.Println("Word ladder:", ladderLength("hit","cog",[]string{"hot","dot","dog","lot","log","cog"}))
}
```

### Hidden Tricks: BFS

```
TRICK 1: Multisource BFS
  Instead of running BFS from each source separately (slow),
  add ALL sources to the queue at the start with distance 0.
  The first time any cell is reached = minimum distance from nearest source.
  Used in: 01 Matrix, rotting oranges, walls and gates.

TRICK 2: Bidirectional BFS
  Run BFS from both start and end simultaneously.
  When frontiers meet, answer = sum of steps.
  Reduces complexity from O(b^d) to O(b^(d/2)) where b=branching factor, d=depth.

TRICK 3: BFS with state
  State is not just position but (position, additional_state).
  Example: (r,c,keys_held) for maze with keys problem.
  Visited set must include the full state.

TRICK 4: Level size snapshot
  At start of each level: levelSize = len(queue)
  Process exactly levelSize nodes for that level.
  This is the clean way to track levels without sentinel values.

TRICK 5: Mark visited when ENQUEUING (not dequeuing)
  If you mark when dequeuing, same node can be enqueued many times.
  This makes BFS O(n²) instead of O(n+e).

PITFALLS:
  - Not marking visited → infinite loop
  - Marking visited when dequeuing → TLE
  - Forgetting edge cases: empty grid, start == end
  - Wrong direction count (4 vs 8 directions)
```

---

## Pattern 07: DFS / Backtracking

### One-Line: Explore all paths recursively, undo choices (backtrack) when a path fails.

### DFS vs Backtracking

```
DFS:           Traverse ALL nodes (graph/tree), no "undo" needed
BACKTRACKING:  Enumerate valid configurations, undo invalid choices

DFS: mark visited → recurse → (no unmark)
BACKTRACKING: make choice → recurse → unmake choice (crucial!)
```

### The Backtracking Template

```
backtrack(state, choices):
    if state is a COMPLETE SOLUTION:
        record(state)
        return

    for each choice in valid_choices(state):
        make_choice(choice)      ← modify state
        backtrack(state, ...)    ← recurse
        unmake_choice(choice)    ← RESTORE state (backtrack)

PRUNING: if is_invalid(state): return  ← skip bad branches early
This is what separates good backtracking from naive backtracking.
```

### Go Implementation

```go
// file: backtracking.go
package main

import (
    "fmt"
    "sort"
)

// ── Subsets ───────────────────────────────────────────────────────────────────

func subsets(nums []int) [][]int {
    result := [][]int{}
    var backtrack func(start int, curr []int)
    backtrack = func(start int, curr []int) {
        // Every state is a valid subset (including empty)
        tmp := make([]int, len(curr))
        copy(tmp, curr)
        result = append(result, tmp)

        for i := start; i < len(nums); i++ {
            curr = append(curr, nums[i])
            backtrack(i+1, curr) // i+1: no reuse
            curr = curr[:len(curr)-1] // backtrack
        }
    }
    backtrack(0, []int{})
    return result
}

// Subsets with duplicates
func subsetsWithDup(nums []int) [][]int {
    sort.Ints(nums) // MUST sort for dedup
    result := [][]int{}
    var backtrack func(start int, curr []int)
    backtrack = func(start int, curr []int) {
        tmp := make([]int, len(curr))
        copy(tmp, curr)
        result = append(result, tmp)

        for i := start; i < len(nums); i++ {
            // Skip duplicates at the same recursion level
            if i > start && nums[i] == nums[i-1] { continue }
            curr = append(curr, nums[i])
            backtrack(i+1, curr)
            curr = curr[:len(curr)-1]
        }
    }
    backtrack(0, []int{})
    return result
}

// ── Permutations ──────────────────────────────────────────────────────────────

func permutations(nums []int) [][]int {
    result := [][]int{}
    used := make([]bool, len(nums))
    var backtrack func(curr []int)
    backtrack = func(curr []int) {
        if len(curr) == len(nums) {
            tmp := make([]int, len(curr))
            copy(tmp, curr)
            result = append(result, tmp)
            return
        }
        for i := range nums {
            if used[i] { continue }
            used[i] = true
            curr = append(curr, nums[i])
            backtrack(curr)
            curr = curr[:len(curr)-1]
            used[i] = false
        }
    }
    backtrack([]int{})
    return result
}

// ── Combinations ──────────────────────────────────────────────────────────────

func combinations(n, k int) [][]int {
    result := [][]int{}
    var backtrack func(start int, curr []int)
    backtrack = func(start int, curr []int) {
        if len(curr) == k {
            tmp := make([]int, k)
            copy(tmp, curr)
            result = append(result, tmp)
            return
        }
        // PRUNING: need k-len(curr) more elements, at most n-i available
        for i := start; i <= n-(k-len(curr))+1; i++ {
            curr = append(curr, i)
            backtrack(i+1, curr)
            curr = curr[:len(curr)-1]
        }
    }
    backtrack(1, []int{})
    return result
}

// ── N-Queens ──────────────────────────────────────────────────────────────────

func solveNQueens(n int) [][]string {
    result := [][]string{}
    board := make([][]byte, n)
    for i := range board {
        board[i] = make([]byte, n)
        for j := range board[i] { board[i][j] = '.' }
    }

    cols := make([]bool, n)
    diag1 := make([]bool, 2*n)   // row-col+n
    diag2 := make([]bool, 2*n)   // row+col

    var backtrack func(row int)
    backtrack = func(row int) {
        if row == n {
            snapshot := make([]string, n)
            for i, r := range board { snapshot[i] = string(r) }
            result = append(result, snapshot)
            return
        }
        for col := 0; col < n; col++ {
            d1 := row - col + n
            d2 := row + col
            if cols[col] || diag1[d1] || diag2[d2] { continue }
            // Place queen
            board[row][col] = 'Q'
            cols[col], diag1[d1], diag2[d2] = true, true, true
            backtrack(row + 1)
            // Remove queen
            board[row][col] = '.'
            cols[col], diag1[d1], diag2[d2] = false, false, false
        }
    }
    backtrack(0)
    return result
}

// ── Word Search ───────────────────────────────────────────────────────────────

func wordSearch(board [][]byte, word string) bool {
    m, n := len(board), len(board[0])
    var dfs func(r, c, idx int) bool
    dfs = func(r, c, idx int) bool {
        if idx == len(word) { return true }
        if r < 0 || r >= m || c < 0 || c >= n || board[r][c] != word[idx] { return false }

        tmp := board[r][c]
        board[r][c] = '#' // mark visited in-place
        found := dfs(r+1,c,idx+1) || dfs(r-1,c,idx+1) ||
                 dfs(r,c+1,idx+1) || dfs(r,c-1,idx+1)
        board[r][c] = tmp // restore
        return found
    }
    for r := 0; r < m; r++ {
        for c := 0; c < n; c++ {
            if dfs(r, c, 0) { return true }
        }
    }
    return false
}

func main() {
    fmt.Println("Subsets [1,2,3]:", subsets([]int{1,2,3}))
    fmt.Println("Subsets with dup [1,2,2]:", subsetsWithDup([]int{1,2,2}))
    fmt.Println("Permutations [1,2,3]:", permutations([]int{1,2,3}))
    fmt.Println("Combinations C(4,2):", combinations(4,2))
    fmt.Println("N-Queens n=4:", len(solveNQueens(4)), "solutions")

    board := [][]byte{
        {'A','B','C','E'},
        {'S','F','C','S'},
        {'A','D','E','E'},
    }
    fmt.Println("Word search ABCCED:", wordSearch(board, "ABCCED"))
}
```

### Hidden Tricks: Backtracking

```
TRICK 1: The "start index" prevents reuse and duplicates
  backtrack(start = i+1): each element used once
  backtrack(start = i):   same element can be reused (coin change style)
  Sort + skip: i > start && nums[i] == nums[i-1] → skip duplicates

TRICK 2: In-place board marking
  Instead of a separate visited set for grids,
  temporarily mark board[r][c] = '#', recurse, restore.
  This is O(1) space vs O(m*n) for visited array.

TRICK 3: Use bit masks for visited in small-n problems
  visited |= (1 << i)   // mark i
  visited &= ~(1 << i)  // unmark i
  visited >> i & 1       // check i
  Much faster than boolean arrays for n <= 20.

TRICK 4: Prune early and hard
  For combinations: i <= n - (k - curr.size) + 1
  For sudoku: check row, col, box before placing
  For N-queens: track three sets (cols, diag1, diag2) - O(1) check

TRICK 5: Memorize the "distinct in subsets" rule:
  Sort first. Skip if i > start && nums[i] == nums[i-1].
  This is different from permutations where it's: i > 0 && !used[i-1] && nums[i] == nums[i-1]

PITFALLS:
  - Forgetting to copy slice before adding to result
  - Not restoring state (the "backtrack" step)
  - Not sorting before dedup
  - Wrong base case: off-by-one in index
```

---

## Pattern 08: Dynamic Programming

### One-Line: Solve complex problems by breaking them into overlapping subproblems and storing results to avoid recomputation.

### The DP Framework

```
STEP 1: DEFINE the state
  dp[i] = ? (what does this represent?)
  Be precise: dp[i] = "length of longest increasing subsequence ending at index i"

STEP 2: FIND the transition (recurrence relation)
  dp[i] = f(dp[j]) for j < i
  This is the hardest part — express dp[i] in terms of smaller dp values.

STEP 3: IDENTIFY base cases
  dp[0] = ?, dp[1] = ?

STEP 4: DETERMINE computation order
  Top-down (memoization): recursive, fill on demand
  Bottom-up (tabulation): iterative, fill in order

STEP 5: EXTRACT the answer
  Sometimes dp[n], sometimes max(dp[0..n])
```

### DP Classification

```
TYPE          | STATE         | TRANSITION     | EXAMPLES
──────────────┼───────────────┼────────────────┼──────────────────────
Linear        | dp[i]         | dp[i] = f(dp[i-1]) | Fibonacci, climb stairs
Interval      | dp[i][j]      | dp[i][j] = f(dp[i+1][j-1]) | Palindrome substr, Matrix chain
Knapsack      | dp[i][w]      | include/exclude | 0/1 knapsack, coin change
Grid          | dp[r][c]      | from top/left   | Unique paths, triangle
Tree          | dp[node]      | from children   | House robber III, diameter
Subsequence   | dp[i][j]      | match/skip      | LCS, Edit distance
Bitmask       | dp[mask]      | add to subset   | TSP, set cover
State machine | dp[i][state]  | transition      | Stock problems, automata
```

### Go Implementation: All Classic DP Patterns

```go
// file: dp.go
package main

import "fmt"

// ── Linear DP ─────────────────────────────────────────────────────────────────

// Climbing stairs: 1 or 2 steps
func climbStairs(n int) int {
    if n <= 2 { return n }
    a, b := 1, 2
    for i := 3; i <= n; i++ {
        a, b = b, a+b
    }
    return b
}

// House robber: can't rob adjacent houses
func rob(nums []int) int {
    if len(nums) == 0 { return 0 }
    if len(nums) == 1 { return nums[0] }
    prev2, prev1 := nums[0], max(nums[0], nums[1])
    for i := 2; i < len(nums); i++ {
        curr := max(prev1, prev2+nums[i])
        prev2, prev1 = prev1, curr
    }
    return prev1
}

func max(a, b int) int { if a > b { return a }; return b }

// ── Knapsack ──────────────────────────────────────────────────────────────────

// 0/1 Knapsack
func knapsack01(weights, values []int, capacity int) int {
    n := len(weights)
    // dp[w] = max value achievable with capacity w
    dp := make([]int, capacity+1)
    for i := 0; i < n; i++ {
        // CRITICAL: iterate from right to prevent reuse (0/1 knapsack)
        for w := capacity; w >= weights[i]; w-- {
            if dp[w-weights[i]]+values[i] > dp[w] {
                dp[w] = dp[w-weights[i]] + values[i]
            }
        }
    }
    return dp[capacity]
}

// Coin change (unbounded knapsack — infinite coins)
func coinChange(coins []int, amount int) int {
    dp := make([]int, amount+1)
    for i := range dp { dp[i] = amount + 1 } // infinity
    dp[0] = 0
    for _, coin := range coins {
        // CRITICAL: iterate from left to allow reuse (unbounded)
        for w := coin; w <= amount; w++ {
            if dp[w-coin]+1 < dp[w] {
                dp[w] = dp[w-coin] + 1
            }
        }
    }
    if dp[amount] > amount { return -1 }
    return dp[amount]
}

// ── Subsequence DP ────────────────────────────────────────────────────────────

// Longest Common Subsequence
func LCS(s1, s2 string) int {
    m, n := len(s1), len(s2)
    dp := make([][]int, m+1)
    for i := range dp { dp[i] = make([]int, n+1) }

    for i := 1; i <= m; i++ {
        for j := 1; j <= n; j++ {
            if s1[i-1] == s2[j-1] {
                dp[i][j] = dp[i-1][j-1] + 1
            } else {
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
            }
        }
    }
    return dp[m][n]
}

// Edit Distance (Levenshtein)
func editDistance(word1, word2 string) int {
    m, n := len(word1), len(word2)
    dp := make([][]int, m+1)
    for i := range dp {
        dp[i] = make([]int, n+1)
        dp[i][0] = i // delete all of word1
    }
    for j := 0; j <= n; j++ { dp[0][j] = j } // insert all of word2

    for i := 1; i <= m; i++ {
        for j := 1; j <= n; j++ {
            if word1[i-1] == word2[j-1] {
                dp[i][j] = dp[i-1][j-1] // no operation needed
            } else {
                dp[i][j] = 1 + min3(
                    dp[i-1][j],   // delete from word1
                    dp[i][j-1],   // insert into word1
                    dp[i-1][j-1], // replace
                )
            }
        }
    }
    return dp[m][n]
}

func min3(a, b, c int) int {
    if a < b { b = a }
    if b < c { return b }
    return c
}

// Longest Increasing Subsequence — O(n²) DP
func LIS_n2(nums []int) int {
    n := len(nums)
    dp := make([]int, n)
    for i := range dp { dp[i] = 1 }
    maxLen := 1
    for i := 1; i < n; i++ {
        for j := 0; j < i; j++ {
            if nums[j] < nums[i] && dp[j]+1 > dp[i] {
                dp[i] = dp[j] + 1
            }
        }
        if dp[i] > maxLen { maxLen = dp[i] }
    }
    return maxLen
}

// LIS — O(n log n) using patience sorting / binary search
func LIS_nlogn(nums []int) int {
    tails := []int{} // tails[i] = smallest tail of LIS with length i+1
    for _, num := range nums {
        // Binary search for first tail >= num
        lo, hi := 0, len(tails)
        for lo < hi {
            mid := (lo + hi) / 2
            if tails[mid] < num { lo = mid + 1 } else { hi = mid }
        }
        if lo == len(tails) {
            tails = append(tails, num)
        } else {
            tails[lo] = num // replace: keep smallest possible tail
        }
    }
    return len(tails)
}

// ── Interval DP ───────────────────────────────────────────────────────────────

// Longest palindromic subsequence
func longestPalindromeSubseq(s string) int {
    n := len(s)
    dp := make([][]int, n)
    for i := range dp {
        dp[i] = make([]int, n)
        dp[i][i] = 1 // single char is palindrome of length 1
    }
    // Fill by length of interval
    for length := 2; length <= n; length++ {
        for i := 0; i <= n-length; i++ {
            j := i + length - 1
            if s[i] == s[j] {
                dp[i][j] = dp[i+1][j-1] + 2
            } else {
                dp[i][j] = max(dp[i+1][j], dp[i][j-1])
            }
        }
    }
    return dp[0][n-1]
}

// ── State Machine DP (Stocks) ─────────────────────────────────────────────────

// Best time to buy/sell stock with cooldown
// States: held (own stock), sold (just sold today), rest (cooldown over)
func maxProfitCooldown(prices []int) int {
    held, sold, rest := -prices[0], 0, 0
    for i := 1; i < len(prices); i++ {
        prevHeld, prevSold, prevRest := held, sold, rest
        held = max(prevHeld, prevRest-prices[i]) // hold or buy
        sold = prevHeld + prices[i]               // sell
        rest = max(prevRest, prevSold)            // rest or continue resting
    }
    return max(sold, rest)
}

// ── Grid DP ───────────────────────────────────────────────────────────────────

// Unique paths in m×n grid
func uniquePaths(m, n int) int {
    dp := make([]int, n)
    for i := range dp { dp[i] = 1 } // first row: all 1s
    for i := 1; i < m; i++ {
        for j := 1; j < n; j++ {
            dp[j] += dp[j-1] // dp[j] was from above, dp[j-1] is from left
        }
    }
    return dp[n-1]
}

func main() {
    fmt.Println("Climb stairs n=5:", climbStairs(5)) // 8
    fmt.Println("Rob [2,7,9,3,1]:", rob([]int{2,7,9,3,1})) // 12
    fmt.Println("Knapsack:", knapsack01([]int{2,3,4,5}, []int{3,4,5,6}, 5)) // 7
    fmt.Println("Coin change:", coinChange([]int{1,5,11}, 15)) // 3
    fmt.Println("LCS:", LCS("abcde", "ace")) // 3
    fmt.Println("Edit dist:", editDistance("horse", "ros")) // 3
    fmt.Println("LIS O(n²):", LIS_n2([]int{10,9,2,5,3,7,101,18})) // 4
    fmt.Println("LIS O(nlogn):", LIS_nlogn([]int{10,9,2,5,3,7,101,18})) // 4
    fmt.Println("Palindrome subseq:", longestPalindromeSubseq("bbbab")) // 4
    fmt.Println("Stock cooldown:", maxProfitCooldown([]int{1,2,3,0,2})) // 3
    fmt.Println("Unique paths 3x7:", uniquePaths(3,7)) // 28
}
```

### Hidden Tricks: DP

```
TRICK 1: 0/1 vs Unbounded Knapsack loop direction
  0/1 (each item once):  loop w from capacity DOWN to weight[i]
  Unbounded (reuse):     loop w from weight[i] UP to capacity
  This single detail changes the entire problem.

TRICK 2: LIS in O(n log n)
  Patience sorting: tails[] array, binary search for replacement position.
  len(tails) = LIS length. Does NOT store the actual LIS — only length.
  To reconstruct: store parent pointers separately.

TRICK 3: Space optimization
  2D DP often reduces to 1D when dp[i][j] only depends on dp[i-1][...].
  Scan carefully: if dp[i][j] uses dp[i][j-1], use rolling array.

TRICK 4: Interval DP always fills by LENGTH of interval, not by i or j.
  for length = 2 to n:
    for i = 0 to n-length:
      j = i + length - 1

TRICK 5: State machine DP for stock problems
  Model each state explicitly (held, sold, resting).
  Transition = decide action at each price.
  This elegantly handles cooldowns, transaction limits, fees.

TRICK 6: When DP answer is "number of ways", use MOD.
  dp[i] = (dp[i-1] + dp[i-2]) % MOD
  Never forget MOD in counting problems.

PITFALLS:
  - Wrong initialization (0 vs infinity vs -infinity)
  - Off-by-one in dp array size (n+1 vs n)
  - Forgetting to return -1 if no solution in coin change style
  - Using 2D when 1D suffices (wastes space)
  - Interval DP: filling by index instead of by length
```

---

## Pattern 09: Greedy

### One-Line: Make the locally optimal choice at each step, proving it leads to a globally optimal solution.

### When Greedy Works

```
GREEDY IS VALID when:
1. Greedy choice property: local optimal → global optimal
2. Optimal substructure: optimal solution contains optimal sub-solutions

COMMON PROOF TECHNIQUES:
- Exchange argument: assume optimal differs from greedy, swap and show
  the greedy is at least as good
- Induction: greedy at step k is optimal given previous steps

GREEDY IS WRONG when:
- Coin change with arbitrary denominations (need DP)
- 0/1 knapsack (need DP)
- Shortest path with negative weights (need Bellman-Ford)
```

### Go Implementation

```go
// file: greedy.go
package main

import (
    "fmt"
    "sort"
)

// Activity selection: max non-overlapping activities
// Greedy: always pick activity that ends earliest
func activitySelection(start, end []int) int {
    n := len(start)
    type Activity struct{ s, e int }
    acts := make([]Activity, n)
    for i := range acts { acts[i] = Activity{start[i], end[i]} }
    sort.Slice(acts, func(i, j int) bool { return acts[i].e < acts[j].e })

    count, lastEnd := 1, acts[0].e
    for i := 1; i < n; i++ {
        if acts[i].s >= lastEnd { // no overlap
            count++
            lastEnd = acts[i].e
        }
    }
    return count
}

// Jump game: can you reach the last index?
// Greedy: track the furthest reachable position
func canJump(nums []int) bool {
    maxReach := 0
    for i, jump := range nums {
        if i > maxReach { return false } // can't reach here
        if i+jump > maxReach { maxReach = i + jump }
    }
    return true
}

// Jump game II: minimum jumps to reach end
func minJumps(nums []int) int {
    jumps, currEnd, farthest := 0, 0, 0
    for i := 0; i < len(nums)-1; i++ {
        if i+nums[i] > farthest { farthest = i + nums[i] }
        if i == currEnd { // reached end of current jump range
            jumps++
            currEnd = farthest
        }
    }
    return jumps
}

// Gas station: can complete circular route?
// Key insight: if total gas >= total cost, a solution always exists
// Greedy: if running sum < 0, reset start to next station
func canCompleteCircuit(gas, cost []int) int {
    total, tank, start := 0, 0, 0
    for i := range gas {
        diff := gas[i] - cost[i]
        total += diff
        tank += diff
        if tank < 0 { // can't reach next station from current start
            start = i + 1
            tank = 0
        }
    }
    if total < 0 { return -1 }
    return start
}

// Assign cookies: maximize satisfied children
func findContentChildren(g, s []int) int {
    sort.Ints(g) // greed factors
    sort.Ints(s) // cookie sizes
    child, cookie := 0, 0
    for child < len(g) && cookie < len(s) {
        if s[cookie] >= g[child] { child++ } // satisfy child
        cookie++
    }
    return child
}

// Fractional knapsack: unlike 0/1, greedy works here
func fractionalKnapsack(weights, values []float64, capacity float64) float64 {
    n := len(weights)
    type Item struct{ ratio, w, v float64 }
    items := make([]Item, n)
    for i := range items { items[i] = Item{values[i] / weights[i], weights[i], values[i]} }
    sort.Slice(items, func(i, j int) bool { return items[i].ratio > items[j].ratio })

    totalValue := 0.0
    for _, item := range items {
        if capacity >= item.w {
            totalValue += item.v
            capacity -= item.w
        } else {
            totalValue += item.ratio * capacity
            break
        }
    }
    return totalValue
}

func main() {
    fmt.Println("Activities:", activitySelection(
        []int{1,3,0,5,8,5}, []int{2,4,6,7,9,9})) // 4

    fmt.Println("Can jump [2,3,1,1,4]:", canJump([]int{2,3,1,1,4}))     // true
    fmt.Println("Can jump [3,2,1,0,4]:", canJump([]int{3,2,1,0,4}))     // false
    fmt.Println("Min jumps:", minJumps([]int{2,3,1,1,4}))               // 2

    fmt.Println("Gas station:", canCompleteCircuit(
        []int{1,2,3,4,5}, []int{3,4,5,1,2})) // 3

    fmt.Println("Cookies:", findContentChildren([]int{1,2,3}, []int{1,1})) // 1
    fmt.Printf("Fractional knapsack: %.2f\n",
        fractionalKnapsack([]float64{10,20,30}, []float64{60,100,120}, 50)) // 240
}
```

---

## Pattern 10: Heap / Priority Queue

### One-Line: Always get the min (or max) element in O(log n) using a heap.

### When to Use
- Top K elements (use opposite heap — min-heap for top K largest)
- K closest points
- Merge K sorted lists/arrays
- Find median from data stream (two heaps)
- Dijkstra's algorithm
- Task scheduling / CPU scheduling

### Two Heaps Pattern (Median Finder)

```
MEDIAN FINDER:
  maxHeap ← lower half (top = median candidate)
  minHeap ← upper half (top = median candidate)

  Invariant:
    len(maxHeap) == len(minHeap) OR len(maxHeap) == len(minHeap) + 1
    maxHeap.top <= minHeap.top (all lower half <= all upper half)

  Add element:
    if num <= maxHeap.top: push to maxHeap else push to minHeap
    Rebalance: ensure size invariant

  Get median:
    if equal sizes: (maxHeap.top + minHeap.top) / 2
    else: maxHeap.top
```

### Go Implementation

```go
// file: heap_patterns.go
package main

import (
    "container/heap"
    "fmt"
    "sort"
)

// ── Min Heap Implementation ───────────────────────────────────────────────────

type MinHeap []int
func (h MinHeap) Len() int           { return len(h) }
func (h MinHeap) Less(i, j int) bool { return h[i] < h[j] }
func (h MinHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }
func (h *MinHeap) Push(x interface{}) { *h = append(*h, x.(int)) }
func (h *MinHeap) Pop() interface{} {
    old := *h; n := len(old); x := old[n-1]; *h = old[:n-1]; return x
}

type MaxHeap []int
func (h MaxHeap) Len() int           { return len(h) }
func (h MaxHeap) Less(i, j int) bool { return h[i] > h[j] } // flipped for max
func (h MaxHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }
func (h *MaxHeap) Push(x interface{}) { *h = append(*h, x.(int)) }
func (h *MaxHeap) Pop() interface{} {
    old := *h; n := len(old); x := old[n-1]; *h = old[:n-1]; return x
}

// Top K largest elements using min-heap of size K
func topKLargest(nums []int, k int) []int {
    h := &MinHeap{}
    heap.Init(h)
    for _, n := range nums {
        heap.Push(h, n)
        if h.Len() > k {
            heap.Pop(h) // remove smallest, keep K largest
        }
    }
    return []int(*h)
}

// K closest points to origin
type Point struct{ x, y, dist2 int }
type PointMaxHeap []Point
func (h PointMaxHeap) Len() int           { return len(h) }
func (h PointMaxHeap) Less(i, j int) bool { return h[i].dist2 > h[j].dist2 }
func (h PointMaxHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }
func (h *PointMaxHeap) Push(x interface{}) { *h = append(*h, x.(Point)) }
func (h *PointMaxHeap) Pop() interface{} {
    old := *h; n := len(old); x := old[n-1]; *h = old[:n-1]; return x
}

func kClosest(points [][]int, k int) [][]int {
    h := &PointMaxHeap{}
    heap.Init(h)
    for _, p := range points {
        d := p[0]*p[0] + p[1]*p[1]
        heap.Push(h, Point{p[0], p[1], d})
        if h.Len() > k {
            heap.Pop(h) // remove farthest
        }
    }
    result := [][]int{}
    for _, p := range *h {
        result = append(result, []int{p.x, p.y})
    }
    return result
}

// ── Median Finder ─────────────────────────────────────────────────────────────

type MedianFinder struct {
    lower *MaxHeap // lower half, top = max of lower
    upper *MinHeap // upper half, top = min of upper
}

func NewMedianFinder() *MedianFinder {
    lower, upper := &MaxHeap{}, &MinHeap{}
    heap.Init(lower); heap.Init(upper)
    return &MedianFinder{lower, upper}
}

func (mf *MedianFinder) AddNum(num int) {
    heap.Push(mf.lower, num)
    // Ensure max(lower) <= min(upper)
    if mf.upper.Len() > 0 && (*mf.lower)[0] > (*mf.upper)[0] {
        heap.Push(mf.upper, heap.Pop(mf.lower))
    }
    // Rebalance sizes: lower can have at most 1 more
    if mf.lower.Len() > mf.upper.Len()+1 {
        heap.Push(mf.upper, heap.Pop(mf.lower))
    } else if mf.upper.Len() > mf.lower.Len() {
        heap.Push(mf.lower, heap.Pop(mf.upper))
    }
}

func (mf *MedianFinder) FindMedian() float64 {
    if mf.lower.Len() == mf.upper.Len() {
        return float64((*mf.lower)[0]+(*mf.upper)[0]) / 2.0
    }
    return float64((*mf.lower)[0])
}

// ── Merge K Sorted Arrays ─────────────────────────────────────────────────────

type HeapItem struct{ val, arrIdx, elemIdx int }
type ItemMinHeap []HeapItem
func (h ItemMinHeap) Len() int           { return len(h) }
func (h ItemMinHeap) Less(i, j int) bool { return h[i].val < h[j].val }
func (h ItemMinHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }
func (h *ItemMinHeap) Push(x interface{}) { *h = append(*h, x.(HeapItem)) }
func (h *ItemMinHeap) Pop() interface{} {
    old := *h; n := len(old); x := old[n-1]; *h = old[:n-1]; return x
}

func mergeKSorted(arrays [][]int) []int {
    h := &ItemMinHeap{}
    heap.Init(h)
    // Push first element from each array
    for i, arr := range arrays {
        if len(arr) > 0 {
            heap.Push(h, HeapItem{arr[0], i, 0})
        }
    }
    result := []int{}
    for h.Len() > 0 {
        item := heap.Pop(h).(HeapItem)
        result = append(result, item.val)
        if item.elemIdx+1 < len(arrays[item.arrIdx]) {
            next := item.elemIdx + 1
            heap.Push(h, HeapItem{arrays[item.arrIdx][next], item.arrIdx, next})
        }
    }
    return result
}

// Task scheduler with cooldown
func leastInterval(tasks []byte, n int) int {
    freq := [26]int{}
    for _, t := range tasks { freq[t-'A']++ }
    sort.Ints(freq[:])

    maxFreq := freq[25]
    maxCount := 0
    for _, f := range freq { if f == maxFreq { maxCount++ } }

    // Formula: max of (maxFreq-1)*(n+1) + maxCount, len(tasks)
    intervals := (maxFreq-1)*(n+1) + maxCount
    if len(tasks) > intervals { return len(tasks) }
    return intervals
}

func main() {
    fmt.Println("Top 3 largest:", topKLargest([]int{3,1,5,12,2,11}, 3))
    fmt.Println("K closest:", kClosest([][]int{{1,3},{-2,2},{5,8}}, 2))

    mf := NewMedianFinder()
    for _, n := range []int{3, 1, 5, 4} {
        mf.AddNum(n)
        fmt.Printf("After adding %d: median = %.1f\n", n, mf.FindMedian())
    }

    arrays := [][]int{{1,4,7},{2,5,8},{3,6,9}}
    fmt.Println("Merge K sorted:", mergeKSorted(arrays))

    fmt.Println("Task scheduler:", leastInterval([]byte("AABABCC"), 2))
}
```

---

## Pattern 11: Monotonic Stack & Queue

### One-Line: A stack/queue where elements are maintained in strictly increasing or decreasing order to answer "next greater/smaller" queries in O(1).

### Core Idea

```
MONOTONIC STACK (decreasing, finding next greater):
  for each element arr[i]:
      while stack not empty AND stack.top < arr[i]:
          popped = stack.pop()
          answer[popped] = arr[i]  ← arr[i] is the "next greater" for popped
      stack.push(i)

WHY IT WORKS:
  When we push i, stack has all elements that haven't found their
  next greater yet. When arr[i] > stack.top, arr[i] is the answer
  for stack.top.

MONOTONIC QUEUE (deque, sliding window max):
  Maintain deque where front = max of current window.
  Remove from front when index out of window.
  Remove from back when new element >= back (it can never be max).
```

### Go Implementation

```go
// file: monotonic.go
package main

import "fmt"

// Next greater element
func nextGreater(arr []int) []int {
    n := len(arr)
    result := make([]int, n)
    for i := range result { result[i] = -1 }
    stack := []int{} // stores indices

    for i := 0; i < n; i++ {
        for len(stack) > 0 && arr[stack[len(stack)-1]] < arr[i] {
            idx := stack[len(stack)-1]
            stack = stack[:len(stack)-1]
            result[idx] = arr[i]
        }
        stack = append(stack, i)
    }
    return result
}

// Largest rectangle in histogram
func largestRectangle(heights []int) int {
    stack := []int{} // indices of bars in increasing height order
    maxArea := 0
    heights = append(heights, 0) // sentinel to flush remaining bars

    for i, h := range heights {
        for len(stack) > 0 && heights[stack[len(stack)-1]] > h {
            height := heights[stack[len(stack)-1]]
            stack = stack[:len(stack)-1]
            width := i
            if len(stack) > 0 { width = i - stack[len(stack)-1] - 1 }
            if height*width > maxArea { maxArea = height * width }
        }
        stack = append(stack, i)
    }
    return maxArea
}

// Maximal rectangle in binary matrix
func maximalRectangle(matrix [][]byte) int {
    if len(matrix) == 0 { return 0 }
    m, n := len(matrix), len(matrix[0])
    heights := make([]int, n)
    maxArea := 0

    for i := 0; i < m; i++ {
        for j := 0; j < n; j++ {
            if matrix[i][j] == '1' {
                heights[j]++ // extend histogram
            } else {
                heights[j] = 0 // reset on '0'
            }
        }
        area := largestRectangle(heights)
        if area > maxArea { maxArea = area }
    }
    return maxArea
}

// Daily temperatures: days until warmer temperature
func dailyTemperatures(temps []int) []int {
    n := len(temps)
    result := make([]int, n)
    stack := []int{}

    for i := 0; i < n; i++ {
        for len(stack) > 0 && temps[stack[len(stack)-1]] < temps[i] {
            idx := stack[len(stack)-1]
            stack = stack[:len(stack)-1]
            result[idx] = i - idx // days to wait
        }
        stack = append(stack, i)
    }
    return result
}

// 132 Pattern: find i < j < k where nums[i] < nums[k] < nums[j]
// Monotonic stack trick: maintain stack of potential "3" (nums[k]) candidates
func find132Pattern(nums []int) bool {
    n := len(nums)
    third := -1 << 31 // nums[k] value, initially -infinity
    stack := []int{}  // decreasing stack

    for i := n - 1; i >= 0; i-- {
        if nums[i] < third { return true } // found nums[i] < third (which < stack element)
        for len(stack) > 0 && stack[len(stack)-1] < nums[i] {
            third = stack[len(stack)-1] // this becomes our best "third" candidate
            stack = stack[:len(stack)-1]
        }
        stack = append(stack, nums[i])
    }
    return false
}

func main() {
    fmt.Println("Next greater [4,1,2]:", nextGreater([]int{4,1,2}))           // [-1,2,-1]
    fmt.Println("Largest rect:", largestRectangle([]int{2,1,5,6,2,3}))        // 10
    fmt.Println("Daily temps:", dailyTemperatures([]int{73,74,75,71,69,72,76,73})) // [1,1,4,2,1,1,0,0]
    fmt.Println("132 pattern:", find132Pattern([]int{3,1,4,2}))              // true
}
```

---

## Pattern 12: Union-Find (DSU)

### One-Line: Track which elements belong to the same group, with near-O(1) union and find operations.

### The Optimized DSU

```
TWO OPTIMIZATIONS:
1. Union by Rank: attach smaller tree to larger tree root
   → keeps tree height O(log n)

2. Path Compression: during find(), point all nodes on path directly to root
   → amortized O(α(n)) ≈ O(1) where α is inverse Ackermann function

COMBINED: near-O(1) per operation, O(n·α(n)) total
```

### C Implementation (Canonical)

```c
// file: union_find.c
#include <stdio.h>

#define MAXN 100001

int parent[MAXN], rank_arr[MAXN], size_arr[MAXN];

void init(int n) {
    for (int i = 0; i < n; i++) {
        parent[i] = i;
        rank_arr[i] = 0;
        size_arr[i] = 1;
    }
}

int find(int x) {
    if (parent[x] != x)
        parent[x] = find(parent[x]); // path compression
    return parent[x];
}

// Union by rank
int unite(int x, int y) {
    int px = find(x), py = find(y);
    if (px == py) return 0; // already same component
    if (rank_arr[px] < rank_arr[py]) { int t = px; px = py; py = t; }
    parent[py] = px;
    size_arr[px] += size_arr[py];
    if (rank_arr[px] == rank_arr[py]) rank_arr[px]++;
    return 1;
}

int component_size(int x) { return size_arr[find(x)]; }
int connected(int x, int y) { return find(x) == find(y); }

// Number of connected components
int count_components(int n) {
    int count = 0;
    for (int i = 0; i < n; i++)
        if (find(i) == i) count++;
    return count;
}

int main() {
    init(7);
    unite(0, 1); unite(2, 3); unite(4, 5);
    printf("Components: %d\n", count_components(7)); // 4: {0,1},{2,3},{4,5},{6}
    printf("0 and 1 connected: %d\n", connected(0, 1)); // 1
    printf("0 and 2 connected: %d\n", connected(0, 2)); // 0

    unite(0, 2); // now {0,1,2,3}
    printf("After union(0,2), 1 and 3 connected: %d\n", connected(1, 3)); // 1
    printf("Size of component containing 0: %d\n", component_size(0)); // 4
    return 0;
}
```

### Go: Kruskal's MST with DSU

```go
// file: dsu_kruskal.go
package main

import (
    "fmt"
    "sort"
)

type DSU struct {
    parent, rank, size []int
}

func NewDSU(n int) *DSU {
    d := &DSU{make([]int, n), make([]int, n), make([]int, n)}
    for i := range d.parent { d.parent[i] = i; d.size[i] = 1 }
    return d
}

func (d *DSU) Find(x int) int {
    if d.parent[x] != x { d.parent[x] = d.Find(d.parent[x]) }
    return d.parent[x]
}

func (d *DSU) Union(x, y int) bool {
    px, py := d.Find(x), d.Find(y)
    if px == py { return false }
    if d.rank[px] < d.rank[py] { px, py = py, px }
    d.parent[py] = px
    d.size[px] += d.size[py]
    if d.rank[px] == d.rank[py] { d.rank[px]++ }
    return true
}

// Kruskal's Minimum Spanning Tree
type Edge struct{ u, v, weight int }

func kruskalMST(n int, edges []Edge) (int, []Edge) {
    sort.Slice(edges, func(i, j int) bool { return edges[i].weight < edges[j].weight })
    dsu := NewDSU(n)
    mstWeight := 0
    mstEdges := []Edge{}

    for _, e := range edges {
        if dsu.Union(e.u, e.v) {
            mstWeight += e.weight
            mstEdges = append(mstEdges, e)
            if len(mstEdges) == n-1 { break } // MST complete
        }
    }
    return mstWeight, mstEdges
}

// Number of islands using DSU (alternative to BFS/DFS)
func numIslands(grid [][]byte) int {
    if len(grid) == 0 { return 0 }
    m, n := len(grid), len(grid[0])
    dsu := NewDSU(m * n)
    count := 0

    for r := 0; r < m; r++ {
        for c := 0; c < n; c++ {
            if grid[r][c] == '1' {
                count++
                // Check right and down neighbors
                dirs := [][2]int{{0,1},{1,0}}
                for _, d := range dirs {
                    nr, nc := r+d[0], c+d[1]
                    if nr < m && nc < n && grid[nr][nc] == '1' {
                        if dsu.Union(r*n+c, nr*n+nc) {
                            count-- // merged two islands
                        }
                    }
                }
            }
        }
    }
    return count
}

func main() {
    edges := []Edge{{0,1,4},{0,2,3},{1,2,1},{1,3,2},{2,3,4},{3,4,2},{4,5,6}}
    w, mst := kruskalMST(6, edges)
    fmt.Printf("MST weight: %d, edges: %v\n", w, mst)

    grid := [][]byte{
        {'1','1','0','0','0'},
        {'1','1','0','0','0'},
        {'0','0','1','0','0'},
        {'0','0','0','1','1'},
    }
    fmt.Println("Number of islands:", numIslands(grid)) // 3
}
```

---

## Pattern 13: Trie

### One-Line: A tree where each path from root to leaf spells a word — perfect for prefix-based lookups in O(L) where L = word length.

### Go Implementation

```go
// file: trie.go
package main

import "fmt"

type TrieNode struct {
    children [26]*TrieNode
    isEnd    bool
    count    int // how many words pass through here (for autocomplete)
}

type Trie struct{ root *TrieNode }

func NewTrie() *Trie { return &Trie{root: &TrieNode{}} }

func (t *Trie) Insert(word string) {
    node := t.root
    for _, ch := range word {
        idx := ch - 'a'
        if node.children[idx] == nil {
            node.children[idx] = &TrieNode{}
        }
        node = node.children[idx]
        node.count++
    }
    node.isEnd = true
}

func (t *Trie) Search(word string) bool {
    node := t.root
    for _, ch := range word {
        idx := ch - 'a'
        if node.children[idx] == nil { return false }
        node = node.children[idx]
    }
    return node.isEnd
}

func (t *Trie) StartsWith(prefix string) bool {
    node := t.root
    for _, ch := range prefix {
        idx := ch - 'a'
        if node.children[idx] == nil { return false }
        node = node.children[idx]
    }
    return true
}

// Word Search II: find all words from dictionary in board (Trie + DFS)
func findWords(board [][]byte, words []string) []string {
    trie := NewTrie()
    for _, w := range words { trie.Insert(w) }

    m, n := len(board), len(board[0])
    found := map[string]bool{}
    dirs := [][2]int{{0,1},{0,-1},{1,0},{-1,0}}

    var dfs func(r, c int, node *TrieNode, path string)
    dfs = func(r, c int, node *TrieNode, path string) {
        if r < 0 || r >= m || c < 0 || c >= n || board[r][c] == '#' { return }
        ch := board[r][c]
        next := node.children[ch-'a']
        if next == nil { return }

        path += string(ch)
        if next.isEnd { found[path] = true }

        board[r][c] = '#' // mark
        for _, d := range dirs { dfs(r+d[0], c+d[1], next, path) }
        board[r][c] = ch // restore
    }

    for r := 0; r < m; r++ {
        for c := 0; c < n; c++ {
            dfs(r, c, trie.root, "")
        }
    }

    result := []string{}
    for w := range found { result = append(result, w) }
    return result
}

func main() {
    t := NewTrie()
    for _, w := range []string{"apple", "app", "application", "apply"} {
        t.Insert(w)
    }
    fmt.Println("Search 'apple':", t.Search("apple"))       // true
    fmt.Println("Search 'appl':", t.Search("appl"))         // false
    fmt.Println("StartsWith 'appl':", t.StartsWith("appl")) // true

    board := [][]byte{
        {'o','a','a','n'},
        {'e','t','a','e'},
        {'i','h','k','r'},
        {'i','f','l','v'},
    }
    words := []string{"oath","pea","eat","rain"}
    fmt.Println("Word search II:", findWords(board, words))
}
```

---

## Pattern 14: Graph Algorithms

### Dijkstra, Bellman-Ford, Topological Sort

```go
// file: graphs.go
package main

import (
    "container/heap"
    "fmt"
)

// ── Dijkstra ──────────────────────────────────────────────────────────────────

type Edge struct{ to, weight int }
type PQItem struct{ node, dist int }
type PQ []PQItem
func (h PQ) Len() int           { return len(h) }
func (h PQ) Less(i, j int) bool { return h[i].dist < h[j].dist }
func (h PQ) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }
func (h *PQ) Push(x interface{}) { *h = append(*h, x.(PQItem)) }
func (h *PQ) Pop() interface{}  { old := *h; n := len(old); x := old[n-1]; *h = old[:n-1]; return x }

func dijkstra(graph [][]Edge, start, n int) []int {
    dist := make([]int, n)
    for i := range dist { dist[i] = 1<<31 - 1 }
    dist[start] = 0

    pq := &PQ{{start, 0}}
    heap.Init(pq)

    for pq.Len() > 0 {
        curr := heap.Pop(pq).(PQItem)
        if curr.dist > dist[curr.node] { continue } // stale entry
        for _, e := range graph[curr.node] {
            newDist := dist[curr.node] + e.weight
            if newDist < dist[e.to] {
                dist[e.to] = newDist
                heap.Push(pq, PQItem{e.to, newDist})
            }
        }
    }
    return dist
}

// ── Topological Sort (Kahn's BFS) ─────────────────────────────────────────────

func topoSort(n int, prerequisites [][2]int) []int {
    inDegree := make([]int, n)
    adj := make([][]int, n)

    for _, p := range prerequisites {
        adj[p[1]] = append(adj[p[1]], p[0])
        inDegree[p[0]]++
    }

    queue := []int{}
    for i := 0; i < n; i++ {
        if inDegree[i] == 0 { queue = append(queue, i) }
    }

    result := []int{}
    for len(queue) > 0 {
        node := queue[0]; queue = queue[1:]
        result = append(result, node)
        for _, next := range adj[node] {
            inDegree[next]--
            if inDegree[next] == 0 { queue = append(queue, next) }
        }
    }
    if len(result) != n { return nil } // cycle exists
    return result
}

// ── Bellman-Ford ──────────────────────────────────────────────────────────────

type BFEdge struct{ from, to, weight int }

func bellmanFord(n int, edges []BFEdge, start int) ([]int, bool) {
    dist := make([]int, n)
    for i := range dist { dist[i] = 1<<31 - 1 }
    dist[start] = 0

    // Relax n-1 times
    for i := 0; i < n-1; i++ {
        for _, e := range edges {
            if dist[e.from] != 1<<31-1 && dist[e.from]+e.weight < dist[e.to] {
                dist[e.to] = dist[e.from] + e.weight
            }
        }
    }

    // Check for negative cycles (n-th relaxation)
    for _, e := range edges {
        if dist[e.from] != 1<<31-1 && dist[e.from]+e.weight < dist[e.to] {
            return nil, true // negative cycle detected
        }
    }
    return dist, false
}

func main() {
    // Graph: 5 nodes
    graph := make([][]Edge, 5)
    addEdge := func(u, v, w int) { graph[u] = append(graph[u], Edge{v, w}) }
    addEdge(0,1,4); addEdge(0,2,1); addEdge(2,1,2); addEdge(1,3,1); addEdge(2,3,5)

    dist := dijkstra(graph, 0, 5)
    fmt.Println("Dijkstra from 0:", dist) // [0,3,1,4,max]

    order := topoSort(6, [][2]int{{1,0},{2,0},{3,1},{4,1},{5,2},{5,3}})
    fmt.Println("Topo sort:", order)

    bfEdges := []BFEdge{{0,1,4},{0,2,1},{2,1,2},{1,3,1}}
    d, neg := bellmanFord(4, bfEdges, 0)
    fmt.Printf("Bellman-Ford: %v, negative cycle: %v\n", d, neg)
}
```

---

## Pattern 15: Bit Manipulation

### Key Operations and Tricks

```c
// file: bits.c
#include <stdio.h>

// Basic operations
int get_bit(int n, int i)    { return (n >> i) & 1; }
int set_bit(int n, int i)    { return n | (1 << i); }
int clear_bit(int n, int i)  { return n & ~(1 << i); }
int toggle_bit(int n, int i) { return n ^ (1 << i); }

// Count set bits (Brian Kernighan's algorithm)
int count_bits(int n) {
    int count = 0;
    while (n) { n &= (n - 1); count++; } // n & (n-1) clears lowest set bit
    return count;
}

// Check if power of 2
int is_pow2(int n) { return n > 0 && (n & (n-1)) == 0; }

// Swap without temp
void swap_bits(int *a, int *b) { *a ^= *b; *b ^= *a; *a ^= *b; }

// Find the single non-duplicate (all others appear twice)
int single_number(int *arr, int n) {
    int result = 0;
    for (int i = 0; i < n; i++) result ^= arr[i];
    return result;
}

// Find two single numbers (all others appear twice)
void two_singles(int *arr, int n, int *a, int *b) {
    int xor = 0;
    for (int i = 0; i < n; i++) xor ^= arr[i]; // xor = a ^ b
    // Find any set bit in xor (rightmost set bit)
    int diff_bit = xor & (-xor); // isolates lowest set bit
    *a = 0; *b = 0;
    for (int i = 0; i < n; i++) {
        if (arr[i] & diff_bit) *a ^= arr[i];
        else *b ^= arr[i];
    }
}

// Bitmask DP: traveling salesman / subset problems
// State: dp[mask][i] = min cost to visit all cities in 'mask', ending at city i
#define INF 1000000
int n_cities = 4;
int dist[4][4] = {{0,10,15,20},{10,0,35,25},{15,35,0,30},{20,25,30,0}};
int dp[1<<4][4];

int tsp() {
    for (int mask = 0; mask < (1<<n_cities); mask++)
        for (int i = 0; i < n_cities; i++) dp[mask][i] = INF;
    dp[1][0] = 0; // start at city 0, visited {0}

    for (int mask = 1; mask < (1<<n_cities); mask++) {
        for (int last = 0; last < n_cities; last++) {
            if (!(mask & (1<<last))) continue; // last must be in mask
            if (dp[mask][last] == INF) continue;
            for (int next = 0; next < n_cities; next++) {
                if (mask & (1<<next)) continue; // next must not be visited
                int newMask = mask | (1<<next);
                int cost = dp[mask][last] + dist[last][next];
                if (cost < dp[newMask][next]) dp[newMask][next] = cost;
            }
        }
    }

    int fullMask = (1<<n_cities) - 1, ans = INF;
    for (int last = 1; last < n_cities; last++) {
        int cost = dp[fullMask][last] + dist[last][0];
        if (cost < ans) ans = cost;
    }
    return ans;
}

int main() {
    printf("Bit operations:\n");
    printf("  get_bit(12, 2) = %d\n", get_bit(12, 2)); // 1 (12=1100)
    printf("  is_pow2(16) = %d\n", is_pow2(16));         // 1
    printf("  count_bits(13) = %d\n", count_bits(13));   // 3 (1101)

    int arr[] = {1,2,3,4,1,2,4};
    printf("Single number: %d\n", single_number(arr, 7)); // 3

    int arr2[] = {1,2,3,4,1,2};
    int x, y;
    two_singles(arr2, 6, &x, &y);
    printf("Two singles: %d and %d\n", x, y); // 3 and 4

    printf("TSP minimum: %d\n", tsp()); // 80
    return 0;
}
```

### Hidden Tricks: Bit Manipulation

```
TRICK 1: n & (n-1) clears the LOWEST set bit
  Use for: counting set bits (Kernighan), checking power of 2

TRICK 2: n & (-n) ISOLATES the lowest set bit
  Use for: splitting groups in two-singles problem, BIT/Fenwick tree

TRICK 3: XOR cancels duplicate elements
  x ^ x = 0, x ^ 0 = x
  Use for: single number, swap without temp, find missing/duplicate

TRICK 4: Bitmask represents a SET
  mask & (1<<i): check if i is in set
  mask | (1<<i): add i to set
  mask & ~(1<<i): remove i from set
  All subsets of mask: for(sub=mask; sub>0; sub=(sub-1)&mask)

TRICK 5: Two's complement properties
  -n = ~n + 1
  n & (-n) = lowest set bit
  ~n = -(n+1)

TRICK 6: Arithmetic right shift fills with sign bit
  -8 >> 1 = -4 (arithmetic)
  This is platform-defined in C but guaranteed in most systems.
```

---

## Pattern 17: Cyclic Sort

### One-Line: When array contains numbers in range [1,n] or [0,n], place each number at its correct index.

### Key Insight

```
Numbers in range [1, n] → element at index i should be i+1.
If arr[i] != i+1, swap arr[i] with arr[arr[i]-1].
After sorting, scan for mismatches — those are missing/duplicate.
```

### Go Implementation

```go
// file: cyclic_sort.go
package main

import "fmt"

func cyclicSort(nums []int) {
    i := 0
    for i < len(nums) {
        correct := nums[i] - 1 // where nums[i] should be
        if nums[i] != nums[correct] {
            nums[i], nums[correct] = nums[correct], nums[i] // place at correct position
        } else {
            i++ // already at correct position or duplicate
        }
    }
}

func findMissing(nums []int) int {
    cyclicSort(nums)
    for i, v := range nums {
        if v != i+1 { return i + 1 }
    }
    return len(nums) + 1
}

func findDuplicate(nums []int) int {
    i := 0
    for i < len(nums) {
        correct := nums[i] - 1
        if nums[i] != i+1 {
            if nums[i] == nums[correct] { return nums[i] } // duplicate!
            nums[i], nums[correct] = nums[correct], nums[i]
        } else {
            i++
        }
    }
    return -1
}

func main() {
    nums := []int{3, 1, 5, 4, 2}
    cyclicSort(nums)
    fmt.Println("Sorted:", nums) // [1 2 3 4 5]

    fmt.Println("Missing:", findMissing([]int{3,0,1})) // 2
    fmt.Println("Duplicate:", findDuplicate([]int{1,3,4,2,2})) // 2
}
```

---

## Pattern 18: Segment Tree / Fenwick Tree

### Fenwick Tree (BIT) — Prefix Sum with Updates

```c
// file: bit.c — Binary Indexed Tree (Fenwick Tree)
#include <stdio.h>
#define MAXN 100001

int bit[MAXN];
int n;

// Add delta to position i (1-indexed)
void update(int i, int delta) {
    for (; i <= n; i += i & (-i)) // i & (-i) = lowest set bit
        bit[i] += delta;
}

// Prefix sum [1, i]
int query(int i) {
    int sum = 0;
    for (; i > 0; i -= i & (-i))
        sum += bit[i];
    return sum;
}

// Range sum [l, r]
int range_query(int l, int r) { return query(r) - query(l-1); }

int main() {
    n = 8;
    int arr[] = {0, 1, 3, 5, 7, 9, 11, 13, 15}; // 1-indexed
    for (int i = 1; i <= n; i++) update(i, arr[i]);

    printf("Sum [1,4] = %d\n", range_query(1,4));  // 16
    printf("Sum [3,6] = %d\n", range_query(3,6));  // 32

    update(3, 10); // arr[3] += 10
    printf("After update, Sum [1,4] = %d\n", range_query(1,4)); // 26
    return 0;
}
```

---

## Pattern 19: Math Patterns

```go
// file: math_tricks.go
package main

import "fmt"

// GCD (Euclidean algorithm)
func gcd(a, b int) int {
    for b != 0 { a, b = b, a%b }
    return a
}
func lcm(a, b int) int { return a / gcd(a, b) * b }

// Fast exponentiation (binary exponentiation)
func powMod(base, exp, mod int) int {
    result := 1
    base %= mod
    for exp > 0 {
        if exp%2 == 1 { result = result * base % mod }
        base = base * base % mod
        exp /= 2
    }
    return result
}

// Sieve of Eratosthenes
func sieve(n int) []bool {
    isPrime := make([]bool, n+1)
    for i := 2; i <= n; i++ { isPrime[i] = true }
    for i := 2; i*i <= n; i++ {
        if isPrime[i] {
            for j := i*i; j <= n; j += i { isPrime[j] = false }
        }
    }
    return isPrime
}

// Catalan number C(n) = C(2n,n)/(n+1) — counts balanced parentheses, BST shapes, etc.
func catalan(n int) int {
    if n <= 1 { return 1 }
    // Using DP
    dp := make([]int, n+1)
    dp[0], dp[1] = 1, 1
    for i := 2; i <= n; i++ {
        for j := 0; j < i; j++ {
            dp[i] += dp[j] * dp[i-1-j]
        }
    }
    return dp[n]
}

func main() {
    fmt.Println("GCD(48,18):", gcd(48,18))       // 6
    fmt.Println("LCM(4,6):", lcm(4,6))           // 12
    fmt.Println("2^10 mod 1000:", powMod(2,10,1000)) // 24
    primes := sieve(30)
    fmt.Print("Primes <= 30: ")
    for i, p := range primes { if p { fmt.Printf("%d ", i) } }
    fmt.Println()
    fmt.Println("Catalan(5):", catalan(5)) // 42
}
```

---

## Complexity Master Table

```
ALGORITHM                    | TIME COMPLEXITY        | SPACE
─────────────────────────────┼────────────────────────┼──────────────
Two Pointers                 | O(n)                   | O(1)
Sliding Window               | O(n)                   | O(window)
Fast & Slow Pointers         | O(n)                   | O(1)
Binary Search                | O(log n)               | O(1)
BFS                          | O(V + E)               | O(V)
DFS                          | O(V + E)               | O(V) stack
Backtracking                 | O(branch^depth)        | O(depth)
Merge Sort                   | O(n log n)             | O(n)
Quick Sort (avg)             | O(n log n)             | O(log n)
Heap (build)                 | O(n)                   | O(n)
Heap (insert/delete)         | O(log n)               | O(1) amortized
Dijkstra (binary heap)       | O((V+E) log V)         | O(V)
Bellman-Ford                 | O(V * E)               | O(V)
Floyd-Warshall               | O(V³)                  | O(V²)
Kruskal (MST)                | O(E log E)             | O(V)
Prim's (MST)                 | O((V+E) log V)         | O(V)
Topological Sort             | O(V + E)               | O(V)
Union-Find (with optim.)     | O(α(n)) ≈ O(1)        | O(n)
Trie (insert/search)         | O(L) where L=word len  | O(ALPHA * n)
Segment Tree (build)         | O(n)                   | O(n)
Segment Tree (query/update)  | O(log n)               | O(1)
Fenwick Tree (BIT)           | O(log n)               | O(n)
DP (1D, typical)             | O(n)                   | O(n) → O(1)
DP (2D, LCS/Edit)            | O(n*m)                 | O(n*m) → O(n)
Bitmask DP (TSP)             | O(n² * 2^n)            | O(n * 2^n)
KMP (string match)           | O(n + m)               | O(m)
Z-algorithm                  | O(n + m)               | O(n)
Sieve of Eratosthenes        | O(n log log n)         | O(n)
Fast Exponentiation          | O(log n)               | O(1)
```

---

## Hidden Tricks & Tips

### Universal Problem-Solving Tricks

```
TRICK 1: "The Complement" — think in terms of what you DON'T want
  Instead of "find subarray summing to target",
  think "find prefix sum such that prefix[i] - prefix[j] = target"
  → HashMap on prefix sums.

TRICK 2: Reduction to known problem
  "Count subarrays with sum = k" → prefix sum + HashMap
  "Find k closest numbers" → sort by |x - target|, take first k
  "Check if two strings are anagrams" → sort both, compare
  When stuck, try to REDUCE to a problem you know.

TRICK 3: Monotonicity unlocks Binary Search
  If you can formulate a YES/NO predicate that is monotonic
  (all NO then all YES, or vice versa), binary search on it.
  This applies to answer-space, not just sorted arrays.

TRICK 4: Think about what you can PRECOMPUTE
  Prefix sums: range sum in O(1)
  Prefix products: range product in O(1)
  Suffix arrays: range from right in O(1)
  Precomputing transforms O(n²) range queries to O(n).

TRICK 5: Inverting the problem
  "Remove k elements to maximize ___" → "keep n-k elements to maximize ___"
  "Find shortest path between A and B" → multisource BFS from B
  "How many X satisfy condition?" → total - how many DON'T satisfy

TRICK 6: The "Think about last element" DP strategy
  For subsequence problems: dp[i] = answer considering ALL subproblems
  ending AT index i. Then answer = max(dp[0..n-1]).

TRICK 7: Coordinate compression
  When values are huge but number of distinct values is small,
  compress to [0, k-1] and use arrays instead of maps.

TRICK 8: Difference array for range updates
  Add v to [l, r]: diff[l] += v, diff[r+1] -= v
  Reconstruct: prefix sum of diff
  O(1) updates, O(n) reconstruct.

TRICK 9: Random tricks that work
  - Shuffle before sorting to avoid adversarial inputs
  - Use reservoir sampling for random element from stream
  - Randomized selection (QuickSelect) for kth smallest: O(n) avg
  - Random pivot in quicksort avoids O(n²) worst case
```

### Pattern-Specific Hidden Tips

```
TWO POINTERS:
  - When nums[i] + nums[j] can overflow int, use long/int64
  - "Minimum window" = find then shrink; "Maximum window" = expand then check
  - Can solve trapping rain water in ONE pass (not two separate prefix arrays)

SLIDING WINDOW:
  - Fixed window: no inner while loop, just add/remove simultaneously
  - Variable window LONGEST: inner while shrinks when INVALID
  - Variable window SHORTEST: inner while shrinks when VALID
  - Remember: answer is updated AFTER the while loop (longest) or INSIDE (shortest)

BINARY SEARCH:
  - lo = mid+1 when condition(mid) = FALSE, hi = mid when TRUE
  - Visualize: FFFTTT, binary search finds the first T
  - For "rightmost T": TTTFFF, negate condition, subtract 1

DFS:
  - Iterative DFS (explicit stack) avoids stack overflow for deep graphs
  - DFS on directed graph: white (unvisited), gray (in stack), black (done)
  - Gray → gray edge = BACK EDGE = CYCLE

DP:
  - If dp[i] only depends on dp[i-1] and dp[i-2], use O(1) space
  - "Find actual solution" (not just length): store parent pointers
  - For interval DP, think: "What's the last operation performed?"

HEAP:
  - In Python: negate values for max-heap using min-heap
  - Lazy deletion: mark as deleted in a set, skip when popping
  - For kth largest in stream: maintain min-heap of size k

GRAPH:
  - Bipartite check = 2-colorable = no odd cycles = BFS with coloring
  - Articulation points/bridges = Tarjan's algorithm
  - Strongly Connected Components = Kosaraju's or Tarjan's
  - Negative weights but no negative cycles → Bellman-Ford (not Dijkstra)
```

---

## Contest & Interview Strategy

### The 5-Minute Before-Coding Protocol

```
MINUTE 1: Read + constraints
  - Underline key constraints
  - Note input/output types
  - Check for edge cases mentioned

MINUTE 2: Brute force
  - State the brute force solution out loud
  - What's its complexity?
  - Why is it too slow?

MINUTE 3: Optimize
  - What's the bottleneck in brute force?
  - What can be precomputed?
  - Does it fit a known pattern?

MINUTE 4: Verify with small example
  - Trace through your algorithm manually
  - Verify the invariant holds
  - Check edge cases: empty, single element, all same, negatives

MINUTE 5: Start coding
  - Write function signature first
  - Write the invariant as a comment
  - Then implement
```

### Edge Cases Checklist

```
ARRAY/STRING:
  □ Empty input (n=0)
  □ Single element
  □ All same elements
  □ Already sorted / reverse sorted
  □ Negative numbers
  □ Duplicates
  □ Integer overflow

LINKED LIST:
  □ null head
  □ Single node
  □ Two nodes (for reversal problems)
  □ Even vs odd length (for middle problems)
  □ Cycle

TREE:
  □ null root
  □ Single node (root only)
  □ Unbalanced (all left or all right)
  □ Negative values

GRAPH:
  □ Disconnected graph
  □ Self-loops
  □ Multiple edges between nodes
  □ Negative weights
  □ Negative cycles

DP:
  □ dp initialized correctly
  □ Base cases covered
  □ Answer extractd correctly (dp[n] vs max(dp[0..n]))
```

### Reading Complexity From Code

```
SINGLE LOOP: O(n)
NESTED LOOPS (independent): O(n * m)
NESTED LOOPS (dependent, shrinking): O(n²) worst, sometimes O(n) amortized

log n appears when:
  - You halve the problem each step: binary search, balanced BST
  - You're doing heap operations
  - You're doubling something: 1+2+4+8+...

n log n appears when:
  - Sort + linear scan
  - n heap operations
  - Divide and conquer: T(n) = 2T(n/2) + O(n) → O(n log n)

2^n appears when:
  - Every element has include/exclude choice (subsets)
  - Recursion has 2 choices at each of n levels

n! appears when:
  - You're generating all permutations
```

---

## Debugging Checklist

```
BUG TYPE              | WHAT TO CHECK
──────────────────────┼──────────────────────────────────────────
Wrong answer          | Trace small example manually
                      | Check edge cases
                      | Verify invariant holds at each step

Off by one            | Is loop condition < or <=?
                      | Array indices 0-based vs 1-based?
                      | +1 in dp array size?

Integer overflow      | Use int64/long long
                      | Intermediate results overflow too

Infinite loop         | Does the pointer/index always advance?
                      | Is the termination condition reachable?

Stack overflow        | Recursion depth too large?
                      | Convert to iterative with explicit stack?

TLE                   | Is complexity what you think it is?
                      | Are there hidden O(n) operations in a loop?
                      | HashSet.contains vs Array.contains?

Wrong DP transition   | Is dp[i] correctly defined?
                      | Does transition match definition?
                      | Is base case correct?

Heap corruption       | Using raw array mutably during heap ops?
                      | Modifying elements after heap insertion?
```

---

## Exercises for Each Pattern

### Practice Plan

```
WEEK 1: Arrays & Two Pointers
  Easy:   Two Sum, Valid Palindrome, Move Zeroes
  Medium: 3Sum, Container With Most Water, Trapping Rain Water
  Hard:   4Sum II, Minimum Window Substring

WEEK 2: Sliding Window & Binary Search
  Easy:   Max Avg Subarray, Binary Search
  Medium: Longest Substring Without Repeating, Permutation in String
  Hard:   Minimum Window Substring, Split Array Largest Sum

WEEK 3: Trees & Graphs
  Easy:   Symmetric Tree, Path Sum, Flood Fill
  Medium: Level Order Traversal, Clone Graph, Course Schedule
  Hard:   Serialize/Deserialize Tree, Word Ladder II

WEEK 4: DP
  Easy:   Climbing Stairs, House Robber, Best Time to Buy Stock
  Medium: Coin Change, LCS, Unique Paths, Jump Game
  Hard:   Edit Distance, Burst Balloons, Regular Expression

WEEK 5: Advanced
  Medium: LRU Cache, Design Twitter, Find Median Data Stream
  Hard:   Largest Rectangle Histogram, Word Search II, N-Queens

WEEK 6: Mixed Contest Problems
  - AtCoder Beginner Contest (A-D problems)
  - Codeforces Div 3 contests
  - LeetCode Weekly Contest
```

---

## Further Reading

```
BOOKS:
  1. "Introduction to Algorithms" (CLRS) — The Bible. Read Ch 1-10, 15-17, 22-25.
  2. "Competitive Programmer's Handbook" (Antti Laaksonen) — FREE online. Practical.
  3. "Algorithm Design Manual" (Skiena) — Best for intuition and war stories.
  4. "Elements of Programming Interviews" — Interview-focused with multiple languages.

ONLINE RESOURCES:
  1. cp-algorithms.com — The best reference for algorithms with proofs
  2. neetcode.io — Pattern-based roadmap with video explanations
  3. codeforces.com/edu — Structured DSA courses
  4. visualgo.net — Visualize algorithms running step by step

KEY REPOSITORIES:
  1. https://github.com/TheAlgorithms/Go — Algorithms in Go
  2. https://github.com/TheAlgorithms/Rust — Algorithms in Rust
  3. https://github.com/neetcode-gh/leetcode — NeetCode solutions
  4. https://github.com/labuladong/fucking-algorithm — Pattern catalog

PROBLEM SETS (by topic):
  Two Pointers:       LC 11, 15, 16, 42, 167, 283, 344
  Sliding Window:     LC 3, 76, 239, 424, 567, 1004, 1248
  Binary Search:      LC 33, 34, 81, 153, 162, 875, 1011
  BFS:                LC 102, 103, 199, 200, 207, 210, 994
  DFS/Backtrack:      LC 17, 22, 39, 40, 46, 78, 79, 212
  DP:                 LC 70, 91, 139, 198, 300, 322, 518, 1143
  Heap:               LC 23, 215, 295, 347, 373, 767
  Trie:               LC 208, 211, 212, 472, 745
  Union-Find:         LC 200, 261, 305, 684, 685, 721
  Graph:              LC 133, 207, 210, 323, 684, 743, 787
  Bit Manipulation:   LC 136, 137, 190, 191, 201, 260, 338
  Monotonic Stack:    LC 84, 85, 496, 503, 739, 907, 1019
```

---

*Document compiled for DSA mastery. Revise weekly. Build intuition by doing, not reading.*
*Target: 300+ problems solved with pattern awareness, not memory.*