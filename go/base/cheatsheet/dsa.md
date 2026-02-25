# The Complete DSA & LeetCode Cheat Sheet — Go Edition
> For the top 1% — precision, performance, pattern mastery

---

## TABLE OF CONTENTS
1. [The Expert Problem-Solving Framework](#1-the-expert-problem-solving-framework)
2. [Complexity Analysis — The Scorecard](#2-complexity-analysis--the-scorecard)
3. [Go DSA Primitives & Boilerplate](#3-go-dsa-primitives--boilerplate)
4. [Arrays & Slices](#4-arrays--slices)
5. [Strings](#5-strings)
6. [Hash Maps & Sets](#6-hash-maps--sets)
7. [Two Pointers](#7-two-pointers)
8. [Sliding Window](#8-sliding-window)
9. [Binary Search](#9-binary-search)
10. [Linked Lists](#10-linked-lists)
11. [Stacks & Queues](#11-stacks--queues)
12. [Monotonic Stack & Queue](#12-monotonic-stack--queue)
13. [Trees — Binary Trees](#13-trees--binary-trees)
14. [Trees — Binary Search Trees](#14-trees--binary-search-trees)
15. [Heaps & Priority Queues](#15-heaps--priority-queues)
16. [Graphs — Representation](#16-graphs--representation)
17. [Graphs — BFS & DFS](#17-graphs--bfs--dfs)
18. [Graphs — Advanced Algorithms](#18-graphs--advanced-algorithms)
19. [Tries (Prefix Trees)](#19-tries-prefix-trees)
20. [Union-Find (Disjoint Set)](#20-union-find-disjoint-set)
21. [Sorting Algorithms](#21-sorting-algorithms)
22. [Recursion & Backtracking](#22-recursion--backtracking)
23. [Dynamic Programming](#23-dynamic-programming)
24. [Greedy Algorithms](#24-greedy-algorithms)
25. [Bit Manipulation](#25-bit-manipulation)
26. [Math & Number Theory](#26-math--number-theory)
27. [Interval Problems](#27-interval-problems)
28. [Matrix / 2D Grid](#28-matrix--2d-grid)
29. [Pattern Recognition Map](#29-pattern-recognition-map)
30. [LeetCode Problem Templates](#30-leetcode-problem-templates)

---

## 1. THE EXPERT PROBLEM-SOLVING FRAMEWORK

Before touching code, an expert runs through this mental pipeline:

```
READ → CATEGORIZE → CONSTRAINTS → BRUTE FORCE → OPTIMIZE → CODE → VERIFY
```

### Step 1: READ (5 minutes)
- What is the exact input? Type, size, constraints.
- What is the exact output?
- Edge cases: empty input, single element, all same, negatives, overflow?
- Is the input sorted? Does order matter?

### Step 2: CATEGORIZE
Map the problem to a pattern (see Section 29). Most LeetCode problems are
instances of ~15 fundamental patterns. Recognize the pattern → know the template.

### Step 3: CONSTRAINTS ANALYSIS
```
n ≤ 10          → O(n!) backtracking fine
n ≤ 20          → O(2^n) bitmask DP fine
n ≤ 100         → O(n³) fine
n ≤ 1000        → O(n²) fine
n ≤ 10^4        → O(n² log n) borderline
n ≤ 10^5        → O(n log n) required
n ≤ 10^6        → O(n) required
n ≤ 10^9        → O(log n) or O(1) required
```

### Step 4: BRUTE FORCE FIRST (mentally)
State it in plain English. This anchors your thinking and is the baseline
to improve upon. Never skip this — even experts do it mentally.

### Step 5: OPTIMIZE
Ask these questions in order:
1. Is there repeated computation? → Memoization / DP
2. Is there a sorted structure? → Binary search
3. Can I use extra memory to gain speed? → Hash map
4. Is there a monotonic property? → Two pointers / sliding window / monotonic stack
5. Can I solve a subproblem and build up? → DP / divide and conquer
6. Can I eliminate choices greedily? → Greedy

### Step 6: CODE
Write clean, correct code. Use meaningful variable names.
Handle edge cases explicitly at the top.

### Step 7: VERIFY
- Trace through with the given examples.
- Trace through with your edge cases.
- Mentally verify time and space complexity.

---

## 2. COMPLEXITY ANALYSIS — THE SCORECARD

### Time Complexity Quick Reference
| Notation | Name | Example |
|---|---|---|
| O(1) | Constant | Array index, hash lookup |
| O(log n) | Logarithmic | Binary search, heap ops |
| O(n) | Linear | Single loop, linear scan |
| O(n log n) | Linearithmic | Merge sort, heap sort |
| O(n²) | Quadratic | Nested loops, bubble sort |
| O(n³) | Cubic | 3D DP, matrix multiply naive |
| O(2^n) | Exponential | Subsets, bitmask DP |
| O(n!) | Factorial | Permutations |

### Space Complexity Notes
- Recursion depth = O(depth) stack space
- BFS queue = O(width of graph) = O(V) worst case
- DFS stack = O(depth) = O(V) worst case
- DP table = O(states)
- Call stack in Go: goroutines start at 2KB, grow dynamically

### Amortized Analysis
`append` in Go: single append O(1) amortized (doubles capacity when full)
`strings.Builder.WriteString`: O(1) amortized

---

## 3. GO DSA PRIMITIVES & BOILERPLATE

### Math Utilities
```go
import "math"

math.MaxInt    // max int (platform-dependent, 64-bit on 64-bit OS)
math.MinInt    // min int
math.MaxInt32  // 2147483647
math.MinInt32  // -2147483648
math.MaxFloat64
math.Inf(1)    // +Infinity
math.Inf(-1)   // -Infinity
math.IsInf(f, 1)
math.Abs(x)    // float64 only
math.Sqrt(x)
math.Pow(base, exp)
math.Log(x)    // natural log
math.Log2(x)
math.Log10(x)
math.Floor(x)
math.Ceil(x)
math.Round(x)
math.Max(a, b) // float64 only
math.Min(a, b) // float64 only

// Integer min/max (no stdlib function — write these)
func min(a, b int) int { if a < b { return a }; return b }
func max(a, b int) int { if a > b { return a }; return b }
func abs(x int) int    { if x < 0 { return -x }; return x }

// NOTE: Go 1.21+ has built-in min/max for ordered types:
// min(1, 2) — works natively
```

### Sorting
```go
import "sort"

// Slices
sort.Ints([]int{3,1,2})          // in-place ascending
sort.Strings([]string{"b","a"})
sort.Float64s([]float64{3.1,1.2})

// Reverse
sort.Sort(sort.Reverse(sort.IntSlice(arr)))

// Custom comparator
sort.Slice(arr, func(i, j int) bool {
    return arr[i] < arr[j] // ascending
})
sort.SliceStable(arr, func(i, j int) bool { // stable
    return arr[i].key < arr[j].key
})

// Search (binary search on sorted slice)
// Returns smallest index where f(i) is true
idx := sort.SearchInts(arr, target) // first index >= target
idx  = sort.Search(len(arr), func(i int) bool { return arr[i] >= target })

// Check if sorted
sort.IntsAreSorted(arr)
```

### make, new, init patterns
```go
// Slices
s := make([]int, n)        // len=n, cap=n, all zeros
s  = make([]int, 0, n)     // len=0, cap=n (pre-allocate, append later)

// Maps
m := make(map[string]int)
m  = make(map[string]int, expectedSize) // hint for pre-allocation

// 2D slice
grid := make([][]int, rows)
for i := range grid {
    grid[i] = make([]int, cols)
}

// Copy
dst := make([]int, len(src))
copy(dst, src)

// Append
s = append(s, 1, 2, 3)
s = append(s, other...)  // spread another slice
```

---

## 4. ARRAYS & SLICES

### Core Operations
```go
// Declaration
var arr [5]int              // fixed array, zero-initialized
arr := [5]int{1,2,3,4,5}
arr := [...]int{1,2,3}      // compiler counts

// Slices (use these for DSA)
s := []int{1,2,3,4,5}
s[2]                        // index: O(1)
s[1:4]                      // slice [1,4): O(1), no copy
s[:3]                       // first 3
s[2:]                       // from index 2
len(s), cap(s)

// Append: O(1) amortized
s = append(s, 6)

// Delete element at index i (order preserved): O(n)
s = append(s[:i], s[i+1:]...)

// Delete element at index i (order not preserved): O(1)
s[i] = s[len(s)-1]
s = s[:len(s)-1]

// Insert at index i: O(n)
s = append(s[:i+1], s[i:]...)
s[i] = val

// Reverse in-place: O(n)
for i, j := 0, len(s)-1; i < j; i, j = i+1, j-1 {
    s[i], s[j] = s[j], s[i]
}
```

### Prefix Sum (Critical Pattern)
```go
// Build prefix sum array
// prefix[i] = sum of s[0..i-1]
// Range sum [l, r] = prefix[r+1] - prefix[l]
func buildPrefix(nums []int) []int {
    prefix := make([]int, len(nums)+1)
    for i, v := range nums {
        prefix[i+1] = prefix[i] + v
    }
    return prefix
}
// rangeSum(l, r) = prefix[r+1] - prefix[l]
```

### Difference Array (Range Update Pattern)
```go
// Apply +val to range [l, r] efficiently
// Build diff array, apply all updates O(1) each, then restore O(n)
diff := make([]int, n+1)
diff[l] += val
diff[r+1] -= val
// Restore: prefix sum of diff
```

### Kadane's Algorithm (Max Subarray)
```go
func maxSubArray(nums []int) int {
    best, cur := nums[0], nums[0]
    for _, v := range nums[1:] {
        if cur < 0 { cur = 0 }
        cur += v
        if cur > best { best = cur }
    }
    return best
}
```

---

## 5. STRINGS

### Essential One-liners
```go
import ("strings"; "strconv"; "unicode")

len(s)                          // byte count
utf8.RuneCountInString(s)       // character count

// Conversion
[]byte(s), string(b)
[]rune(s), string(r)
strconv.Itoa(42)                // int → string
strconv.Atoi("42")             // string → int (returns int, error)

// Test & search
strings.Contains(s, sub)
strings.HasPrefix(s, pre)
strings.HasSuffix(s, suf)
strings.Index(s, sub)          // -1 if not found
strings.Count(s, sub)

// Transform
strings.ToUpper(s)
strings.ToLower(s)
strings.TrimSpace(s)
strings.Trim(s, cutset)
strings.Replace(s, old, new, n) // n=-1 for all
strings.ReplaceAll(s, old, new)

// Split / Join
strings.Split(s, sep)
strings.Fields(s)              // split on whitespace
strings.Join(parts, sep)

// Builder (for construction in loops)
var sb strings.Builder
sb.WriteString("hello")
sb.WriteByte(' ')
sb.WriteRune('世')
result := sb.String()
```

### Anagram Check Pattern
```go
func isAnagram(s, t string) bool {
    if len(s) != len(t) { return false }
    var freq [26]int
    for i := 0; i < len(s); i++ {
        freq[s[i]-'a']++
        freq[t[i]-'a']--
    }
    for _, v := range freq {
        if v != 0 { return false }
    }
    return true
}
```

### Palindrome Check
```go
func isPalindrome(s string) bool {
    r := []rune(s)
    for i, j := 0, len(r)-1; i < j; i, j = i+1, j-1 {
        if r[i] != r[j] { return false }
    }
    return true
}
```

---

## 6. HASH MAPS & SETS

### Map Operations
```go
m := make(map[string]int)

// Insert / Update: O(1) average
m["key"] = 42

// Lookup: O(1) average
val := m["key"]           // returns zero value if missing
val, ok := m["key"]       // ok=false if missing — ALWAYS use this form

// Delete: O(1)
delete(m, "key")

// Iterate (random order)
for k, v := range m { }
for k := range m { }       // keys only

// Length
len(m)

// Check existence
if _, ok := m["key"]; ok { }
```

### Set (using map[T]struct{})
```go
// struct{} takes 0 bytes — idiomatic Go set
set := make(map[int]struct{})

// Add
set[42] = struct{}{}

// Contains
_, ok := set[42]

// Remove
delete(set, 42)

// Alternatively use map[int]bool for readability
seen := make(map[int]bool)
seen[42] = true
if seen[42] { }
```

### Frequency Counter Pattern
```go
freq := make(map[byte]int)
for i := 0; i < len(s); i++ {
    freq[s[i]]++
}
// Most common: O(26) for lowercase letters → use [26]int array instead
var freq [26]int
for _, c := range s {
    freq[c-'a']++
}
```

### Two Sum Pattern
```go
func twoSum(nums []int, target int) []int {
    seen := make(map[int]int) // val → index
    for i, v := range nums {
        if j, ok := seen[target-v]; ok {
            return []int{j, i}
        }
        seen[v] = i
    }
    return nil
}
```

---

## 7. TWO POINTERS

**When to use:** Sorted array, find pair/triplet with sum condition,
partition problems, palindrome, remove duplicates.

### Pattern Template
```go
left, right := 0, len(arr)-1
for left < right {
    // evaluate arr[left] and arr[right]
    if condition {
        // found answer or move pointers strategically
        left++
    } else {
        right--
    }
}
```

### Two Sum (Sorted Array)
```go
func twoSumSorted(nums []int, target int) []int {
    l, r := 0, len(nums)-1
    for l < r {
        sum := nums[l] + nums[r]
        if sum == target { return []int{l, r} }
        if sum < target  { l++ } else { r-- }
    }
    return nil
}
```

### Three Sum
```go
func threeSum(nums []int) [][]int {
    sort.Ints(nums)
    var res [][]int
    for i := 0; i < len(nums)-2; i++ {
        if i > 0 && nums[i] == nums[i-1] { continue } // skip dup
        l, r := i+1, len(nums)-1
        for l < r {
            sum := nums[i] + nums[l] + nums[r]
            if sum == 0 {
                res = append(res, []int{nums[i], nums[l], nums[r]})
                for l < r && nums[l] == nums[l+1] { l++ }
                for l < r && nums[r] == nums[r-1] { r-- }
                l++; r--
            } else if sum < 0 { l++ } else { r-- }
        }
    }
    return res
}
```

### Remove Duplicates (Fast/Slow Pointer)
```go
func removeDuplicates(nums []int) int {
    slow := 0
    for fast := 1; fast < len(nums); fast++ {
        if nums[fast] != nums[slow] {
            slow++
            nums[slow] = nums[fast]
        }
    }
    return slow + 1
}
```

---

## 8. SLIDING WINDOW

**When to use:** Subarray/substring with condition on length or value sum.
Fixed window or variable window.

### Fixed Window
```go
// Max sum subarray of size k
func maxSumFixed(nums []int, k int) int {
    windowSum := 0
    for i := 0; i < k; i++ { windowSum += nums[i] }
    best := windowSum
    for i := k; i < len(nums); i++ {
        windowSum += nums[i] - nums[i-k]
        if windowSum > best { best = windowSum }
    }
    return best
}
```

### Variable Window (Expand/Contract)
```go
// Longest substring without repeating characters
func lengthOfLongestSubstring(s string) int {
    seen := make(map[byte]int) // char → last index
    best, left := 0, 0
    for right := 0; right < len(s); right++ {
        if idx, ok := seen[s[right]]; ok && idx >= left {
            left = idx + 1
        }
        seen[s[right]] = right
        if right-left+1 > best {
            best = right - left + 1
        }
    }
    return best
}
```

### Variable Window with Frequency (At Most K Distinct)
```go
func atMostKDistinct(s string, k int) int {
    freq := make(map[byte]int)
    best, left := 0, 0
    for right := 0; right < len(s); right++ {
        freq[s[right]]++
        for len(freq) > k {  // shrink until valid
            freq[s[left]]--
            if freq[s[left]] == 0 { delete(freq, s[left]) }
            left++
        }
        if right-left+1 > best { best = right - left + 1 }
    }
    return best
}
```

---

## 9. BINARY SEARCH

**When to use:** Sorted array, search space can be monotonically evaluated,
"find minimum/maximum that satisfies condition" problems.

### Classic Binary Search
```go
func binarySearch(nums []int, target int) int {
    lo, hi := 0, len(nums)-1
    for lo <= hi {
        mid := lo + (hi-lo)/2  // avoids overflow vs (lo+hi)/2
        if nums[mid] == target { return mid }
        if nums[mid] < target  { lo = mid+1 } else { hi = mid-1 }
    }
    return -1
}
```

### Left Bound (First occurrence / Lower bound)
```go
// Returns index of first element >= target
func lowerBound(nums []int, target int) int {
    lo, hi := 0, len(nums)
    for lo < hi {
        mid := lo + (hi-lo)/2
        if nums[mid] < target { lo = mid+1 } else { hi = mid }
    }
    return lo // lo == hi, first index >= target
}
```

### Right Bound (Upper bound)
```go
// Returns index of first element > target
func upperBound(nums []int, target int) int {
    lo, hi := 0, len(nums)
    for lo < hi {
        mid := lo + (hi-lo)/2
        if nums[mid] <= target { lo = mid+1 } else { hi = mid }
    }
    return lo
}
// Count of target = upperBound(target) - lowerBound(target)
```

### Binary Search on Answer (Parametric Search)
```go
// "Find minimum X such that f(X) is true"
// f must be monotonic: false...false...true...true
lo, hi := minPossible, maxPossible
for lo < hi {
    mid := lo + (hi-lo)/2
    if f(mid) { hi = mid } else { lo = mid+1 }
}
// lo == hi == answer

// "Find maximum X such that f(X) is true"
for lo < hi {
    mid := lo + (hi-lo+1)/2  // +1 avoids infinite loop when hi=lo+1
    if f(mid) { lo = mid } else { hi = mid-1 }
}
```

---

## 10. LINKED LISTS

### Node Definition
```go
type ListNode struct {
    Val  int
    Next *ListNode
}
```

### Core Patterns

**Dummy Head** — eliminates edge cases at head:
```go
dummy := &ListNode{Next: head}
// operate on dummy.Next...
return dummy.Next
```

**Fast & Slow Pointers:**
```go
// Find middle
slow, fast := head, head
for fast != nil && fast.Next != nil {
    slow = slow.Next
    fast = fast.Next.Next
}
// slow is at middle

// Detect cycle (Floyd's)
slow, fast := head, head
for fast != nil && fast.Next != nil {
    slow = slow.Next
    fast = fast.Next.Next
    if slow == fast { return true }
}
return false

// Find cycle start
// After detection: reset slow to head, keep fast at meeting point
// Move both one step at a time → they meet at cycle start
```

**Reverse Linked List:**
```go
func reverseList(head *ListNode) *ListNode {
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
```

**Reverse sublist [left, right]:**
```go
func reverseBetween(head *ListNode, left, right int) *ListNode {
    dummy := &ListNode{Next: head}
    pre := dummy
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
```

**Find Nth from end:**
```go
func removeNthFromEnd(head *ListNode, n int) *ListNode {
    dummy := &ListNode{Next: head}
    fast, slow := dummy, dummy
    for i := 0; i <= n; i++ { fast = fast.Next }
    for fast != nil { slow = slow.Next; fast = fast.Next }
    slow.Next = slow.Next.Next
    return dummy.Next
}
```

---

## 11. STACKS & QUEUES

### Stack (use slice)
```go
var stack []int

// Push: O(1) amortized
stack = append(stack, val)

// Pop: O(1)
top := stack[len(stack)-1]
stack = stack[:len(stack)-1]

// Peek: O(1)
top := stack[len(stack)-1]

// IsEmpty
len(stack) == 0
```

### Queue (use slice — for LeetCode acceptable)
```go
var queue []int
queue = append(queue, val)   // enqueue
front := queue[0]            // peek
queue = queue[1:]            // dequeue (creates new slice header, old memory not freed)
// For production: use two stacks or container/list
```

### Queue with `container/list` (O(1) dequeue)
```go
import "container/list"

q := list.New()
q.PushBack(val)              // enqueue
front := q.Front()           // peek
q.Remove(q.Front())          // dequeue
q.Len()
```

### Valid Parentheses Pattern
```go
func isValid(s string) bool {
    var stack []rune
    pair := map[rune]rune{')': '(', ']': '[', '}': '{'}
    for _, c := range s {
        if c == '(' || c == '[' || c == '{' {
            stack = append(stack, c)
        } else {
            if len(stack) == 0 || stack[len(stack)-1] != pair[c] {
                return false
            }
            stack = stack[:len(stack)-1]
        }
    }
    return len(stack) == 0
}
```

---

## 12. MONOTONIC STACK & QUEUE

**Monotonic Stack:** Stack that maintains increasing or decreasing order.
Useful for: Next greater element, Previous smaller element, Largest rectangle, Trapping rain water.

### Next Greater Element
```go
func nextGreater(nums []int) []int {
    n := len(nums)
    res := make([]int, n)
    for i := range res { res[i] = -1 }
    var stack []int // stores indices

    for i := 0; i < n; i++ {
        // Pop all elements smaller than current
        for len(stack) > 0 && nums[stack[len(stack)-1]] < nums[i] {
            idx := stack[len(stack)-1]
            stack = stack[:len(stack)-1]
            res[idx] = nums[i]
        }
        stack = append(stack, i)
    }
    return res
}
```

### Largest Rectangle in Histogram
```go
func largestRectangleArea(heights []int) int {
    heights = append(heights, 0) // sentinel
    var stack []int
    best := 0
    for i, h := range heights {
        for len(stack) > 0 && heights[stack[len(stack)-1]] > h {
            height := heights[stack[len(stack)-1]]
            stack = stack[:len(stack)-1]
            width := i
            if len(stack) > 0 { width = i - stack[len(stack)-1] - 1 }
            if height*width > best { best = height * width }
        }
        stack = append(stack, i)
    }
    return best
}
```

### Monotonic Deque (Sliding Window Maximum)
```go
func maxSlidingWindow(nums []int, k int) []int {
    var deque []int // stores indices, front = max
    var res []int
    for i, v := range nums {
        // Remove out-of-window elements from front
        for len(deque) > 0 && deque[0] <= i-k {
            deque = deque[1:]
        }
        // Maintain decreasing order: remove smaller from back
        for len(deque) > 0 && nums[deque[len(deque)-1]] < v {
            deque = deque[:len(deque)-1]
        }
        deque = append(deque, i)
        if i >= k-1 {
            res = append(res, nums[deque[0]])
        }
    }
    return res
}
```

---

## 13. TREES — BINARY TREES

### Node Definition
```go
type TreeNode struct {
    Val   int
    Left  *TreeNode
    Right *TreeNode
}
```

### Traversals
```go
// Inorder: Left → Root → Right (gives sorted for BST)
func inorder(root *TreeNode) {
    if root == nil { return }
    inorder(root.Left)
    fmt.Println(root.Val)
    inorder(root.Right)
}

// Preorder: Root → Left → Right (serialize tree)
func preorder(root *TreeNode) {
    if root == nil { return }
    fmt.Println(root.Val)
    preorder(root.Left)
    preorder(root.Right)
}

// Postorder: Left → Right → Root (delete tree, evaluate expression)
func postorder(root *TreeNode) {
    if root == nil { return }
    postorder(root.Left)
    postorder(root.Right)
    fmt.Println(root.Val)
}
```

### Iterative Inorder (Two-Pointer Interview Favorite)
```go
func inorderIterative(root *TreeNode) []int {
    var res []int
    var stack []*TreeNode
    curr := root
    for curr != nil || len(stack) > 0 {
        for curr != nil {
            stack = append(stack, curr)
            curr = curr.Left
        }
        curr = stack[len(stack)-1]
        stack = stack[:len(stack)-1]
        res = append(res, curr.Val)
        curr = curr.Right
    }
    return res
}
```

### BFS — Level Order Traversal
```go
func levelOrder(root *TreeNode) [][]int {
    if root == nil { return nil }
    var res [][]int
    queue := []*TreeNode{root}
    for len(queue) > 0 {
        size := len(queue)
        var level []int
        for i := 0; i < size; i++ {
            node := queue[i]
            level = append(level, node.Val)
            if node.Left  != nil { queue = append(queue, node.Left) }
            if node.Right != nil { queue = append(queue, node.Right) }
        }
        res = append(res, level)
        queue = queue[size:]
    }
    return res
}
```

### Common Tree Functions
```go
// Height / Depth
func height(root *TreeNode) int {
    if root == nil { return 0 }
    return 1 + max(height(root.Left), height(root.Right))
}

// Diameter (longest path between any two nodes)
func diameterOfBinaryTree(root *TreeNode) int {
    best := 0
    var dfs func(*TreeNode) int
    dfs = func(node *TreeNode) int {
        if node == nil { return 0 }
        l, r := dfs(node.Left), dfs(node.Right)
        if l+r > best { best = l + r }
        return 1 + max(l, r)
    }
    dfs(root)
    return best
}

// Is Balanced?
func isBalanced(root *TreeNode) bool {
    var check func(*TreeNode) int
    check = func(node *TreeNode) int {
        if node == nil { return 0 }
        l := check(node.Left)
        if l == -1 { return -1 }
        r := check(node.Right)
        if r == -1 { return -1 }
        if abs(l-r) > 1 { return -1 }
        return 1 + max(l, r)
    }
    return check(root) != -1
}

// LCA (Lowest Common Ancestor)
func lowestCommonAncestor(root, p, q *TreeNode) *TreeNode {
    if root == nil || root == p || root == q { return root }
    left  := lowestCommonAncestor(root.Left, p, q)
    right := lowestCommonAncestor(root.Right, p, q)
    if left != nil && right != nil { return root }
    if left != nil { return left }
    return right
}

// Maximum Path Sum
func maxPathSum(root *TreeNode) int {
    best := math.MinInt32
    var dfs func(*TreeNode) int
    dfs = func(node *TreeNode) int {
        if node == nil { return 0 }
        l := max(0, dfs(node.Left))
        r := max(0, dfs(node.Right))
        if node.Val+l+r > best { best = node.Val + l + r }
        return node.Val + max(l, r)
    }
    dfs(root)
    return best
}
```

---

## 14. TREES — BINARY SEARCH TREES

**BST Property:** left.Val < node.Val < right.Val (for all nodes)
Inorder traversal of BST = sorted sequence.

```go
// Search: O(log n) average, O(n) worst
func searchBST(root *TreeNode, val int) *TreeNode {
    for root != nil {
        if val == root.Val   { return root }
        if val < root.Val    { root = root.Left } else { root = root.Right }
    }
    return nil
}

// Insert: O(log n) average
func insertIntoBST(root *TreeNode, val int) *TreeNode {
    if root == nil { return &TreeNode{Val: val} }
    if val < root.Val { root.Left  = insertIntoBST(root.Left, val) }
    else              { root.Right = insertIntoBST(root.Right, val) }
    return root
}

// Delete: O(log n) average
func deleteNode(root *TreeNode, key int) *TreeNode {
    if root == nil { return nil }
    if key < root.Val      { root.Left  = deleteNode(root.Left, key) }
    else if key > root.Val { root.Right = deleteNode(root.Right, key) }
    else {
        if root.Left  == nil { return root.Right }
        if root.Right == nil { return root.Left }
        // Find inorder successor (min of right subtree)
        succ := root.Right
        for succ.Left != nil { succ = succ.Left }
        root.Val   = succ.Val
        root.Right = deleteNode(root.Right, succ.Val)
    }
    return root
}

// Validate BST
func isValidBST(root *TreeNode) bool {
    var validate func(*TreeNode, int, int) bool
    validate = func(node *TreeNode, lo, hi int) bool {
        if node == nil { return true }
        if node.Val <= lo || node.Val >= hi { return false }
        return validate(node.Left, lo, node.Val) && validate(node.Right, node.Val, hi)
    }
    return validate(root, math.MinInt64, math.MaxInt64)
}
```

---

## 15. HEAPS & PRIORITY QUEUES

Go's `container/heap` requires implementing an interface.

### Min-Heap Template
```go
import "container/heap"

type MinHeap []int

func (h MinHeap) Len() int            { return len(h) }
func (h MinHeap) Less(i, j int) bool  { return h[i] < h[j] } // min at top
func (h MinHeap) Swap(i, j int)       { h[i], h[j] = h[j], h[i] }
func (h *MinHeap) Push(x interface{}) { *h = append(*h, x.(int)) }
func (h *MinHeap) Pop() interface{} {
    old := *h; n := len(old)
    x := old[n-1]; *h = old[:n-1]
    return x
}

// Usage
h := &MinHeap{3, 1, 4, 1, 5}
heap.Init(h)
heap.Push(h, 2)
top := (*h)[0]          // peek min: O(1)
min := heap.Pop(h).(int) // pop min: O(log n)
```

### Max-Heap: change Less
```go
func (h MaxHeap) Less(i, j int) bool { return h[i] > h[j] }
```

### Top K Elements Pattern
```go
// Top K largest: use a min-heap of size K
// If element > heap top, pop and push
func topKFrequent(nums []int, k int) []int {
    freq := make(map[int]int)
    for _, v := range nums { freq[v]++ }

    h := &MinHeap{}
    heap.Init(h)
    for val := range freq {
        heap.Push(h, val)
        if h.Len() > k { heap.Pop(h) }
    }
    return []int(*h)
}
```

### K-Way Merge Pattern
```go
// Push first element of each list with (val, listIdx, elemIdx)
// Pop min, push next from same list
type Item struct{ val, li, ei int }
type ItemHeap []Item
// ... implement heap.Interface
```

### Median from Data Stream (Two Heaps)
```go
// maxHeap (lower half) | minHeap (upper half)
// Invariant: |maxHeap| - |minHeap| <= 1
// Median: if equal sizes → average tops; else → top of larger heap
```

---

## 16. GRAPHS — REPRESENTATION

### Adjacency List (most common)
```go
// Undirected
graph := make([][]int, n)
graph[u] = append(graph[u], v)
graph[v] = append(graph[v], u)

// Directed
graph[u] = append(graph[u], v)

// Weighted
type Edge struct{ to, weight int }
graph := make([][]Edge, n)
graph[u] = append(graph[u], Edge{v, w})

// From edge list
edges := [][]int{{0,1},{1,2},{2,0}}
for _, e := range edges {
    graph[e[0]] = append(graph[e[0]], e[1])
}
```

### Adjacency Matrix
```go
// For dense graphs or when O(1) edge lookup needed
mat := make([][]int, n)
for i := range mat { mat[i] = make([]int, n) }
mat[u][v] = 1 // or weight
```

---

## 17. GRAPHS — BFS & DFS

### BFS (Shortest Path in Unweighted Graph)
```go
func bfs(graph [][]int, start int) []int {
    n := len(graph)
    dist := make([]int, n)
    for i := range dist { dist[i] = -1 }
    dist[start] = 0
    queue := []int{start}
    for len(queue) > 0 {
        node := queue[0]; queue = queue[1:]
        for _, nei := range graph[node] {
            if dist[nei] == -1 {
                dist[nei] = dist[node] + 1
                queue = append(queue, nei)
            }
        }
    }
    return dist
}
```

### DFS (Recursive)
```go
func dfs(graph [][]int, node int, visited []bool) {
    visited[node] = true
    for _, nei := range graph[node] {
        if !visited[nei] {
            dfs(graph, nei, visited)
        }
    }
}
```

### DFS (Iterative — avoids stack overflow)
```go
func dfsIterative(graph [][]int, start int) {
    visited := make([]bool, len(graph))
    stack := []int{start}
    for len(stack) > 0 {
        node := stack[len(stack)-1]
        stack = stack[:len(stack)-1]
        if visited[node] { continue }
        visited[node] = true
        for _, nei := range graph[node] {
            if !visited[nei] { stack = append(stack, nei) }
        }
    }
}
```

### Grid BFS/DFS (2D Matrix)
```go
dirs := [][2]int{{0,1},{0,-1},{1,0},{-1,0}}

func bfsGrid(grid [][]int, sr, sc int) {
    rows, cols := len(grid), len(grid[0])
    visited := make([][]bool, rows)
    for i := range visited { visited[i] = make([]bool, cols) }
    queue := [][2]int{{sr, sc}}
    visited[sr][sc] = true
    for len(queue) > 0 {
        cur := queue[0]; queue = queue[1:]
        r, c := cur[0], cur[1]
        for _, d := range dirs {
            nr, nc := r+d[0], c+d[1]
            if nr >= 0 && nr < rows && nc >= 0 && nc < cols && !visited[nr][nc] {
                visited[nr][nc] = true
                queue = append(queue, [2]int{nr, nc})
            }
        }
    }
}
```

### Topological Sort (Kahn's BFS)
```go
func topoSort(n int, edges [][]int) []int {
    graph := make([][]int, n)
    indegree := make([]int, n)
    for _, e := range edges {
        graph[e[0]] = append(graph[e[0]], e[1])
        indegree[e[1]]++
    }
    var queue []int
    for i, d := range indegree {
        if d == 0 { queue = append(queue, i) }
    }
    var order []int
    for len(queue) > 0 {
        node := queue[0]; queue = queue[1:]
        order = append(order, node)
        for _, nei := range graph[node] {
            indegree[nei]--
            if indegree[nei] == 0 { queue = append(queue, nei) }
        }
    }
    if len(order) != n { return nil } // cycle exists
    return order
}
```

### Cycle Detection (DFS, Directed Graph)
```go
// State: 0=unvisited, 1=in-stack, 2=done
func hasCycle(graph [][]int) bool {
    n := len(graph)
    state := make([]int, n)
    var dfs func(int) bool
    dfs = func(node int) bool {
        state[node] = 1
        for _, nei := range graph[node] {
            if state[nei] == 1 { return true } // back edge
            if state[nei] == 0 && dfs(nei) { return true }
        }
        state[node] = 2
        return false
    }
    for i := 0; i < n; i++ {
        if state[i] == 0 && dfs(i) { return true }
    }
    return false
}
```

---

## 18. GRAPHS — ADVANCED ALGORITHMS

### Dijkstra's (Shortest Path, Non-negative Weights)
```go
// O((V + E) log V)
func dijkstra(graph [][]Edge, start int) []int {
    n := len(graph)
    dist := make([]int, n)
    for i := range dist { dist[i] = math.MaxInt }
    dist[start] = 0

    h := &MinHeapEdge{{0, start}}
    heap.Init(h)

    for h.Len() > 0 {
        cur := heap.Pop(h).(EdgeItem)
        if cur.dist > dist[cur.node] { continue } // stale entry
        for _, e := range graph[cur.node] {
            if nd := dist[cur.node] + e.weight; nd < dist[e.to] {
                dist[e.to] = nd
                heap.Push(h, EdgeItem{nd, e.to})
            }
        }
    }
    return dist
}
```

### Bellman-Ford (Negative Weights, Detect Negative Cycles)
```go
// O(VE)
func bellmanFord(n int, edges [][]int, start int) ([]int, bool) {
    dist := make([]int, n)
    for i := range dist { dist[i] = math.MaxInt / 2 }
    dist[start] = 0
    for i := 0; i < n-1; i++ {
        for _, e := range edges { // [u, v, w]
            if dist[e[0]] + e[2] < dist[e[1]] {
                dist[e[1]] = dist[e[0]] + e[2]
            }
        }
    }
    // Check for negative cycle
    for _, e := range edges {
        if dist[e[0]] + e[2] < dist[e[1]] { return nil, true }
    }
    return dist, false
}
```

### Prim's MST (Min Spanning Tree)
```go
// O((V + E) log V) with heap
func primMST(graph [][]Edge, n int) int {
    visited := make([]bool, n)
    h := &MinHeapEdge{{0, 0}} // {cost, node}
    heap.Init(h)
    total := 0
    for h.Len() > 0 {
        cur := heap.Pop(h).(EdgeItem)
        if visited[cur.node] { continue }
        visited[cur.node] = true
        total += cur.dist
        for _, e := range graph[cur.node] {
            if !visited[e.to] {
                heap.Push(h, EdgeItem{e.weight, e.to})
            }
        }
    }
    return total
}
```

---

## 19. TRIES (PREFIX TREES)

```go
type TrieNode struct {
    children [26]*TrieNode
    isEnd    bool
}

type Trie struct {
    root *TrieNode
}

func NewTrie() *Trie { return &Trie{root: &TrieNode{}} }

func (t *Trie) Insert(word string) {
    node := t.root
    for _, c := range word {
        idx := c - 'a'
        if node.children[idx] == nil {
            node.children[idx] = &TrieNode{}
        }
        node = node.children[idx]
    }
    node.isEnd = true
}

func (t *Trie) Search(word string) bool {
    node := t.root
    for _, c := range word {
        idx := c - 'a'
        if node.children[idx] == nil { return false }
        node = node.children[idx]
    }
    return node.isEnd
}

func (t *Trie) StartsWith(prefix string) bool {
    node := t.root
    for _, c := range prefix {
        idx := c - 'a'
        if node.children[idx] == nil { return false }
        node = node.children[idx]
    }
    return true
}
```

**When to use Trie:**
- Autocomplete, spell check
- Word search in 2D grid
- Longest common prefix
- XOR problems (binary trie)

---

## 20. UNION-FIND (DISJOINT SET)

The most elegant data structure for connectivity problems.

```go
type UnionFind struct {
    parent []int
    rank   []int
    count  int // number of components
}

func NewUnionFind(n int) *UnionFind {
    parent := make([]int, n)
    rank   := make([]int, n)
    for i := range parent { parent[i] = i }
    return &UnionFind{parent, rank, n}
}

// Find with path compression: O(α(n)) ≈ O(1)
func (uf *UnionFind) Find(x int) int {
    if uf.parent[x] != x {
        uf.parent[x] = uf.Find(uf.parent[x]) // path compression
    }
    return uf.parent[x]
}

// Union by rank: O(α(n)) ≈ O(1)
func (uf *UnionFind) Union(x, y int) bool {
    px, py := uf.Find(x), uf.Find(y)
    if px == py { return false } // already connected
    if uf.rank[px] < uf.rank[py] { px, py = py, px }
    uf.parent[py] = px
    if uf.rank[px] == uf.rank[py] { uf.rank[px]++ }
    uf.count--
    return true
}

func (uf *UnionFind) Connected(x, y int) bool {
    return uf.Find(x) == uf.Find(y)
}
```

**When to use:**
- Number of connected components
- Cycle detection in undirected graph
- Kruskal's MST
- Accounts merge, friend circles

---

## 21. SORTING ALGORITHMS

### Built-in (Use this in practice)
```go
sort.Ints(arr)
sort.Slice(arr, func(i, j int) bool { return arr[i] < arr[j] })
```

### Merge Sort (for inversion count, external sort)
```go
func mergeSort(arr []int) []int {
    if len(arr) <= 1 { return arr }
    mid := len(arr) / 2
    left  := mergeSort(arr[:mid])
    right := mergeSort(arr[mid:])
    return merge(left, right)
}

func merge(l, r []int) []int {
    res := make([]int, 0, len(l)+len(r))
    i, j := 0, 0
    for i < len(l) && j < len(r) {
        if l[i] <= r[j] { res = append(res, l[i]); i++ } else { res = append(res, r[j]); j++ }
    }
    res = append(res, l[i:]...)
    res = append(res, r[j:]...)
    return res
}
```

### Quick Select (Kth Largest/Smallest) — O(n) average
```go
func findKthLargest(nums []int, k int) int {
    return quickSelect(nums, 0, len(nums)-1, len(nums)-k)
}

func quickSelect(nums []int, lo, hi, k int) int {
    if lo == hi { return nums[lo] }
    pivot := partition(nums, lo, hi)
    if pivot == k      { return nums[pivot] }
    if pivot < k       { return quickSelect(nums, pivot+1, hi, k) }
    return quickSelect(nums, lo, pivot-1, k)
}

func partition(nums []int, lo, hi int) int {
    pivot := nums[hi]
    i := lo
    for j := lo; j < hi; j++ {
        if nums[j] <= pivot {
            nums[i], nums[j] = nums[j], nums[i]
            i++
        }
    }
    nums[i], nums[hi] = nums[hi], nums[i]
    return i
}
```

---

## 22. RECURSION & BACKTRACKING

### Backtracking Template
```go
var result [][]int

func backtrack(path []int, choices []int, state State) {
    if isGoal(state) {
        tmp := make([]int, len(path))
        copy(tmp, path)
        result = append(result, tmp)
        return
    }
    for _, choice := range choices {
        if !isValid(choice, state) { continue }
        path = append(path, choice)     // choose
        backtrack(path, choices, nextState(state, choice))
        path = path[:len(path)-1]       // unchoose
    }
}
```

### Subsets (Power Set)
```go
func subsets(nums []int) [][]int {
    var res [][]int
    var bt func(start int, path []int)
    bt = func(start int, path []int) {
        tmp := make([]int, len(path))
        copy(tmp, path)
        res = append(res, tmp)
        for i := start; i < len(nums); i++ {
            path = append(path, nums[i])
            bt(i+1, path)
            path = path[:len(path)-1]
        }
    }
    bt(0, nil)
    return res
}
```

### Permutations
```go
func permute(nums []int) [][]int {
    var res [][]int
    used := make([]bool, len(nums))
    var bt func(path []int)
    bt = func(path []int) {
        if len(path) == len(nums) {
            tmp := make([]int, len(path))
            copy(tmp, path)
            res = append(res, tmp)
            return
        }
        for i, v := range nums {
            if used[i] { continue }
            used[i] = true
            bt(append(path, v))
            used[i] = false
        }
    }
    bt(nil)
    return res
}
```

### N-Queens
```go
func solveNQueens(n int) [][]string {
    var res [][]string
    board := make([]int, n) // board[row] = col of queen
    for i := range board { board[i] = -1 }
    cols := make([]bool, n)
    diag1 := make([]bool, 2*n) // row-col+n
    diag2 := make([]bool, 2*n) // row+col
    var bt func(row int)
    bt = func(row int) {
        if row == n {
            // build string board and append to res
            return
        }
        for col := 0; col < n; col++ {
            if cols[col] || diag1[row-col+n] || diag2[row+col] { continue }
            cols[col] = true; diag1[row-col+n] = true; diag2[row+col] = true
            board[row] = col
            bt(row + 1)
            cols[col] = false; diag1[row-col+n] = false; diag2[row+col] = false
        }
    }
    bt(0)
    return res
}
```

---

## 23. DYNAMIC PROGRAMMING

### The DP Mindset
```
1. Define STATE clearly: dp[i], dp[i][j], dp[mask], etc.
2. Define RECURRENCE: how dp[i] relates to smaller subproblems
3. Define BASE CASES: smallest valid inputs
4. Define ITERATION ORDER: ensure subproblems solved before needed
5. Identify the ANSWER: dp[n], dp[n][m], max(dp[i]), etc.
```

### 1D DP Patterns

**Fibonacci / Climbing Stairs:**
```go
// dp[i] = dp[i-1] + dp[i-2]
// Space optimize: only keep last 2 values
```

**House Robber:**
```go
func rob(nums []int) int {
    prev2, prev1 := 0, 0
    for _, v := range nums {
        prev2, prev1 = prev1, max(prev1, prev2+v)
    }
    return prev1
}
```

**Longest Increasing Subsequence (LIS):**
```go
// O(n²) DP
func lisN2(nums []int) int {
    n := len(nums)
    dp := make([]int, n)
    for i := range dp { dp[i] = 1 }
    best := 1
    for i := 1; i < n; i++ {
        for j := 0; j < i; j++ {
            if nums[j] < nums[i] && dp[j]+1 > dp[i] {
                dp[i] = dp[j] + 1
            }
        }
        if dp[i] > best { best = dp[i] }
    }
    return best
}

// O(n log n) Patience Sorting
func lisNlogN(nums []int) int {
    var tails []int
    for _, v := range nums {
        pos := sort.SearchInts(tails, v)
        if pos == len(tails) { tails = append(tails, v) } else { tails[pos] = v }
    }
    return len(tails)
}
```

### 2D DP Patterns

**Longest Common Subsequence:**
```go
func lcs(s, t string) int {
    m, n := len(s), len(t)
    dp := make([][]int, m+1)
    for i := range dp { dp[i] = make([]int, n+1) }
    for i := 1; i <= m; i++ {
        for j := 1; j <= n; j++ {
            if s[i-1] == t[j-1] { dp[i][j] = dp[i-1][j-1] + 1 }
            if dp[i-1][j] > dp[i][j] { dp[i][j] = dp[i-1][j] }
            if dp[i][j-1] > dp[i][j] { dp[i][j] = dp[i][j-1] }
        }
    }
    return dp[m][n]
}
```

**Edit Distance:**
```go
func minDistance(word1, word2 string) int {
    m, n := len(word1), len(word2)
    dp := make([][]int, m+1)
    for i := range dp { dp[i] = make([]int, n+1); dp[i][0] = i }
    for j := 0; j <= n; j++ { dp[0][j] = j }
    for i := 1; i <= m; i++ {
        for j := 1; j <= n; j++ {
            if word1[i-1] == word2[j-1] { dp[i][j] = dp[i-1][j-1] }
            else { dp[i][j] = 1 + min(dp[i-1][j-1], min(dp[i-1][j], dp[i][j-1])) }
        }
    }
    return dp[m][n]
}
```

**0/1 Knapsack:**
```go
func knapsack(weights, values []int, capacity int) int {
    n := len(weights)
    dp := make([]int, capacity+1)
    for i := 0; i < n; i++ {
        for w := capacity; w >= weights[i]; w-- { // reverse order!
            if v := dp[w-weights[i]] + values[i]; v > dp[w] { dp[w] = v }
        }
    }
    return dp[capacity]
}
```

**Unbounded Knapsack / Coin Change:**
```go
func coinChange(coins []int, amount int) int {
    dp := make([]int, amount+1)
    for i := range dp { dp[i] = amount + 1 }
    dp[0] = 0
    for i := 1; i <= amount; i++ {
        for _, c := range coins {
            if c <= i && dp[i-c]+1 < dp[i] { dp[i] = dp[i-c] + 1 }
        }
    }
    if dp[amount] > amount { return -1 }
    return dp[amount]
}
```

### Bitmask DP
```go
// dp[mask] where mask represents a subset of elements
// Classic: Traveling Salesman Problem (small n)
n := 5
dp := make([][]int, 1<<n)
for i := range dp { dp[i] = make([]int, n) }
// dp[mask][i] = cost to visit all nodes in mask, ending at i
```

### Interval DP
```go
// dp[i][j] = optimal solution for subarray [i..j]
// Iterate by length, not by i
for length := 2; length <= n; length++ {
    for i := 0; i+length-1 < n; i++ {
        j := i + length - 1
        for k := i; k < j; k++ {
            // dp[i][j] = f(dp[i][k], dp[k+1][j], cost(i,j,k))
        }
    }
}
```

---

## 24. GREEDY ALGORITHMS

**Greedy works when:** Local optimal choice leads to global optimal.
**Prove it:** Exchange argument — show swapping any two adjacent choices can't improve solution.

### Classic Greedy Problems
```go
// Activity Selection / Non-overlapping Intervals
// Sort by end time, greedily pick intervals that don't overlap
sort.Slice(intervals, func(i, j int) bool {
    return intervals[i][1] < intervals[j][1]
})
end, count := math.MinInt, 0
for _, iv := range intervals {
    if iv[0] >= end { count++; end = iv[1] }
}

// Jump Game
func canJump(nums []int) bool {
    reach := 0
    for i, v := range nums {
        if i > reach { return false }
        if i+v > reach { reach = i + v }
    }
    return true
}

// Gas Station
func canCompleteCircuit(gas, cost []int) int {
    total, cur, start := 0, 0, 0
    for i := range gas {
        diff := gas[i] - cost[i]
        total += diff
        cur   += diff
        if cur < 0 { start = i + 1; cur = 0 }
    }
    if total < 0 { return -1 }
    return start
}
```

---

## 25. BIT MANIPULATION

```go
// Basic operations
x & y    // AND
x | y    // OR
x ^ y    // XOR
x << n   // left shift (multiply by 2^n)
x >> n   // right shift (divide by 2^n)
^x       // bitwise NOT (in Go, ^ is NOT when unary)

// Common tricks
x & 1              // check if odd (last bit)
x & (x-1)         // clear lowest set bit
x & (-x)          // isolate lowest set bit
x | (x+1)         // set lowest unset bit
x ^ x == 0        // true for same values
a ^ b ^ b == a    // XOR cancels out

// Count set bits (Brian Kernighan)
func popcount(x int) int {
    count := 0
    for x != 0 { x &= x - 1; count++ }
    return count
}

// Check power of 2
func isPowerOf2(n int) bool { return n > 0 && n&(n-1) == 0 }

// Get bit at position i
func getBit(n, i int) int { return (n >> i) & 1 }

// Set bit at position i
func setBit(n, i int) int { return n | (1 << i) }

// Clear bit at position i
func clearBit(n, i int) int { return n &^ (1 << i) } // &^ is AND NOT in Go

// Toggle bit at position i
func toggleBit(n, i int) int { return n ^ (1 << i) }

// Single Number (XOR all — duplicates cancel)
func singleNumber(nums []int) int {
    res := 0
    for _, v := range nums { res ^= v }
    return res
}

// Enumerate all subsets of a set represented as bitmask
n := 4
for mask := 0; mask < (1 << n); mask++ {
    // mask represents a subset
    for i := 0; i < n; i++ {
        if mask & (1 << i) != 0 { /* element i is in this subset */ }
    }
}
```

---

## 26. MATH & NUMBER THEORY

```go
// GCD (Euclidean algorithm): O(log min(a,b))
func gcd(a, b int) int {
    for b != 0 { a, b = b, a%b }
    return a
}

// LCM
func lcm(a, b int) int { return a / gcd(a, b) * b }

// Power with modulo: O(log exp)
func powMod(base, exp, mod int) int {
    result := 1
    base %= mod
    for exp > 0 {
        if exp&1 == 1 { result = result * base % mod }
        base = base * base % mod
        exp >>= 1
    }
    return result
}

// Sieve of Eratosthenes: all primes up to n, O(n log log n)
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

// Is Prime: O(√n)
func isPrime(n int) bool {
    if n < 2 { return false }
    for i := 2; i*i <= n; i++ {
        if n%i == 0 { return false }
    }
    return true
}

// Integer square root
func isqrt(n int) int { return int(math.Sqrt(float64(n))) }

// Modular arithmetic constants
const MOD = 1_000_000_007
// Always do: (a + b) % MOD, (a * b) % MOD
// For division: use modular inverse (Fermat's little theorem when MOD is prime)
```

---

## 27. INTERVAL PROBLEMS

```go
// Sort by start time
sort.Slice(intervals, func(i, j int) bool {
    return intervals[i][0] < intervals[j][0]
})

// Merge overlapping intervals
func merge(intervals [][]int) [][]int {
    sort.Slice(intervals, func(i, j int) bool { return intervals[i][0] < intervals[j][0] })
    res := [][]int{intervals[0]}
    for _, iv := range intervals[1:] {
        last := res[len(res)-1]
        if iv[0] <= last[1] {
            if iv[1] > last[1] { last[1] = iv[1] }
        } else {
            res = append(res, iv)
        }
    }
    return res
}

// Min meeting rooms (max overlapping intervals at any point)
// Use events: +1 at start, -1 at end, sort events, running max
func minMeetingRooms(intervals [][]int) int {
    events := make([][2]int, 0, len(intervals)*2)
    for _, iv := range intervals {
        events = append(events, [2]int{iv[0], 1}, [2]int{iv[1], -1})
    }
    sort.Slice(events, func(i, j int) bool {
        if events[i][0] == events[j][0] { return events[i][1] < events[j][1] }
        return events[i][0] < events[j][0]
    })
    rooms, cur := 0, 0
    for _, e := range events {
        cur += e[1]
        if cur > rooms { rooms = cur }
    }
    return rooms
}
```

---

## 28. MATRIX / 2D GRID

```go
// Directions
dirs4  := [][2]int{{0,1},{0,-1},{1,0},{-1,0}}
dirs8  := [][2]int{{0,1},{0,-1},{1,0},{-1,0},{1,1},{1,-1},{-1,1},{-1,-1}}

// Bounds check
func inBounds(r, c, rows, cols int) bool {
    return r >= 0 && r < rows && c >= 0 && c < cols
}

// Spiral order traversal
func spiralOrder(matrix [][]int) []int {
    top, bot := 0, len(matrix)-1
    left, right := 0, len(matrix[0])-1
    var res []int
    for top <= bot && left <= right {
        for c := left; c <= right; c++   { res = append(res, matrix[top][c]) }; top++
        for r := top;  r <= bot;  r++    { res = append(res, matrix[r][right]) }; right--
        if top <= bot {
            for c := right; c >= left; c-- { res = append(res, matrix[bot][c]) }; bot--
        }
        if left <= right {
            for r := bot; r >= top; r--    { res = append(res, matrix[r][left]) }; left++
        }
    }
    return res
}

// Rotate matrix 90° clockwise in-place
func rotate(matrix [][]int) {
    n := len(matrix)
    // Transpose
    for i := 0; i < n; i++ {
        for j := i+1; j < n; j++ {
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
        }
    }
    // Reverse each row
    for i := 0; i < n; i++ {
        for l, r := 0, n-1; l < r; l, r = l+1, r-1 {
            matrix[i][l], matrix[i][r] = matrix[i][r], matrix[i][l]
        }
    }
}
```

---

## 29. PATTERN RECOGNITION MAP

This is your primary diagnostic tool. Read the problem, then match:

| Clue in Problem | Likely Pattern |
|---|---|
| Sorted array, find target | Binary Search |
| "Subarray / substring with condition" | Sliding Window |
| "Pair/triplet with sum" | Two Pointers (if sorted) / Hash Map |
| Array with positive/negative, max subarray | Kadane's |
| "Number of islands / connected components" | BFS/DFS / Union-Find |
| Shortest path, unweighted graph | BFS |
| Shortest path, weighted graph | Dijkstra / Bellman-Ford |
| "Min cost to reach" | DP or Dijkstra |
| Parentheses, monotonic range queries | Stack |
| "Next greater/smaller element" | Monotonic Stack |
| "K largest/smallest" | Heap |
| Tree traversal, path sum | DFS (recursive) |
| Level order, zigzag traversal | BFS |
| Prefix/autocomplete operations | Trie |
| "Optimal substructure" + overlapping subproblems | DP |
| Choices / combinations / permutations | Backtracking |
| Interval scheduling, meeting rooms | Greedy + Sort |
| "Divide into X groups optimally" | Binary Search on Answer |
| XOR, single number, missing number | Bit Manipulation |
| n ≤ 20, all subsets | Bitmask DP |
| Graph edges in increasing order, connectivity | Kruskal's + Union-Find |
| "Rearrange / reorder to satisfy" | Greedy / Sort |
| "Can we do X with K changes" | Binary Search on K |

---

## 30. LEETCODE PROBLEM TEMPLATES

### DFS on Graph (with visited)
```go
visited := make([]bool, n)
var dfs func(node int)
dfs = func(node int) {
    visited[node] = true
    for _, nei := range graph[node] {
        if !visited[nei] { dfs(nei) }
    }
}
```

### BFS Shortest Path
```go
dist := make([]int, n)
for i := range dist { dist[i] = -1 }
dist[start] = 0
queue := []int{start}
for len(queue) > 0 {
    node := queue[0]; queue = queue[1:]
    for _, nei := range graph[node] {
        if dist[nei] == -1 { dist[nei] = dist[node]+1; queue = append(queue, nei) }
    }
}
```

### Memoized DFS (Top-Down DP)
```go
memo := make(map[int]int)
var dfs func(state int) int
dfs = func(state int) int {
    if v, ok := memo[state]; ok { return v }
    // compute result
    memo[state] = result
    return result
}
```

### Binary Search on Answer
```go
lo, hi := 1, maxPossibleAnswer
for lo < hi {
    mid := lo + (hi-lo)/2
    if feasible(mid) { hi = mid } else { lo = mid+1 }
}
// lo is the answer
```

### Backtracking with Deduplication
```go
sort.Ints(nums) // sort first for dedup
var bt func(start int, path []int)
bt = func(start int, path []int) {
    // process path
    for i := start; i < len(nums); i++ {
        if i > start && nums[i] == nums[i-1] { continue } // skip dup
        path = append(path, nums[i])
        bt(i+1, path)
        path = path[:len(path)-1]
    }
}
```

### Quick Union-Find Setup
```go
parent := make([]int, n)
for i := range parent { parent[i] = i }
var find func(int) int
find = func(x int) int {
    if parent[x] != x { parent[x] = find(parent[x]) }
    return parent[x]
}
union := func(x, y int) {
    parent[find(x)] = find(y)
}
```

### Dijkstra Minimal
```go
type Item [2]int // [dist, node]
type PQ []Item
func (h PQ) Len() int            { return len(h) }
func (h PQ) Less(i, j int) bool  { return h[i][0] < h[j][0] }
func (h PQ) Swap(i, j int)       { h[i], h[j] = h[j], h[i] }
func (h *PQ) Push(x interface{}) { *h = append(*h, x.(Item)) }
func (h *PQ) Pop() interface{}   { old := *h; x := old[len(old)-1]; *h = old[:len(old)-1]; return x }

dist := make([]int, n)
for i := range dist { dist[i] = 1<<31 - 1 }
dist[src] = 0
h := &PQ{{0, src}}
heap.Init(h)
for h.Len() > 0 {
    cur := heap.Pop(h).(Item)
    d, u := cur[0], cur[1]
    if d > dist[u] { continue }
    for _, e := range graph[u] {
        v, w := e[0], e[1]
        if nd := dist[u] + w; nd < dist[v] { dist[v] = nd; heap.Push(h, Item{nd, v}) }
    }
}
```

---

## FINAL MENTAL FRAMEWORK

```
PROBLEM
  │
  ├── What structure? → Array / String / Tree / Graph / Other
  │
  ├── What operation? → Search / Count / Optimize / Construct
  │
  ├── What constraint drives the algorithm?
  │     sorted → binary search or two pointer
  │     subarray/substring → sliding window
  │     optimal substructure → DP
  │     choices → backtracking
  │     connectivity → union-find / BFS / DFS
  │
  └── What complexity is required? → n determines algorithm class

CODE with:
  - Edge cases at top (nil, empty, single element)
  - Clear variable names
  - Meaningful comments for non-obvious steps
  - Verified time AND space complexity
```

> *"The expert has not memorized solutions. They have memorized the structure of problems."*
> Pattern recognition is the meta-skill. Every problem you solve should sharpen it.

---

Yes, exactly right. Your instinct is sharp.

Every `[]rune(s)` conversion is an O(n) allocation — it decodes the entire UTF-8 string and creates a brand new slice in heap memory. If you do this carelessly in a loop or a hot path, you're paying that cost repeatedly for no reason.

Here's the mental model broken down precisely:

## What Actually Happens During Conversion

```go
s := "café"
r := []rune(s)  // ← allocates new []int32 on heap, decodes every byte
```

The runtime walks every byte of `s`, decodes UTF-8 sequences, and writes a 4-byte `int32` per character into a new heap array. For a string of `n` bytes, this is O(n) time and O(n) space — always, no exceptions, no compiler magic here.

## The Three Tiers of String Walking

```go
s := "café résumé"

// ❌ TIER 3 — Worst for Unicode correctness, misleading for perf
for i := 0; i < len(s); i++ {
    b := s[i]  // raw byte — breaks on multi-byte runes
}

// ✅ TIER 2 — Idiomatic, zero allocation, correct Unicode
for i, r := range s {
    // Go's range decodes UTF-8 on the fly, one rune at a time
    // NO heap allocation — decodes as it walks
    _ = i  // byte index
    _ = r  // rune value
}

// ❌ TIER 1 — Unnecessary when you just need to walk
r := []rune(s)
for i, r := range r {
    _ = i  // rune index now, not byte index
    _ = r
}
```

The critical insight: **`range` on a string already does UTF-8 decoding on the fly — zero allocation.** It is functionally equivalent to converting to `[]rune` and ranging over that, but without the heap allocation. Most developers don't know this and reflexively convert.

## When Each Approach Is Justified

```go
// ✅ Use range directly — walking characters, no random access needed
for _, r := range s {
    process(r)
}

// ✅ Use utf8 package — zero alloc, need byte position too
import "unicode/utf8"
for i := 0; i < len(s); {
    r, size := utf8.DecodeRuneInString(s[i:])
    process(r)
    i += size
}

// ✅ Convert to []rune ONLY when you need random access by character index
// or you need to mutate individual characters
runes := []rune(s)
runes[3] = 'X'         // ← this is the legitimate use case
result := string(runes)

// ✅ Convert to []byte ONLY when you need byte-level mutation (ASCII only)
b := []byte(s)
b[0] = 'H'
result := string(b)
```

## The Real Cost in Numbers

```go
// Benchmark mindset — what you're paying:

s := strings.Repeat("résumé ", 1000) // ~8000 bytes, ~6000 runes

// Option A: []rune conversion
r := []rune(s)           // 1 malloc, ~24KB heap, O(n) decode
for _, ch := range r { _ = ch }

// Option B: range directly
for _, ch := range s { _ = ch }  // 0 malloc, same O(n) decode, stack only

// Option B wins on:
// - 0 heap allocations (no GC pressure)
// - Better cache behavior (reading original UTF-8 bytes, not a copied array)
// - Same or faster throughput
```

## The Gotcha: When You PAY Twice

The most common mistake beginners make:

```go
// ❌ Paying the conversion cost AND then ranging — double work
func countVowels(s string) int {
    runes := []rune(s)      // O(n) alloc + decode
    count := 0
    for _, r := range runes { // O(n) again
        if isVowel(r) { count++ }
    }
    return count
}

// ✅ Single pass, zero allocation
func countVowels(s string) int {
    count := 0
    for _, r := range s {   // O(n) decode on the fly, no alloc
        if isVowel(r) { count++ }
    }
    return count
}
```

## The Decision Tree

```
Need to walk every character?
    → range s directly. Never convert.

Need character at position i (random access)?
    → Convert to []rune once, index into it.
    → Or walk with utf8.DecodeRuneInString to reach position i (if rare).

Need to modify characters?
    → ASCII only: []byte conversion + mutation.
    → Unicode: []rune conversion + mutation + convert back.

Need byte position alongside character?
    → range s gives you both: for byteIdx, r := range s

Doing this in a hot loop?
    → Cache the []rune conversion OUTSIDE the loop if you must convert.
    → Better: restructure so you don't need conversion inside the loop.
```

## The Expert Rule

> **Never convert to `[]rune` unless you have a concrete reason that `range` cannot satisfy.**

The concrete reasons are exactly two: you need **index-based character access** (`runes[i]`) or you need to **mutate** individual characters. Every other use case — iteration, searching, counting, comparing — can be done with `range` or `unicode/utf8` functions at zero allocation cost.

Your instinct to question this was correct. The ability to notice hidden costs before benchmarking is precisely the kind of analytical sharpness that separates good engineers from great ones.

Honest answer: **No. Not in Go.** This is a deliberate language design decision, not an oversight.

But here's the thing — understanding *why* reveals the correct mental model, and from that you get the closest thing to "no constraints" that actually exists.

## Why There's No "Free" String

Go's strings are immutable by contract. The runtime, compiler, and memory model all rely on this guarantee. A mutable string would break safe sharing, require copy-on-write semantics, and destroy the performance characteristics Go is built around. This is not something you work around — you accept it and choose the right backing type.

The real question is: **what type should I actually be working in?**

## The Actual Answer for DSA / LeetCode

For 95% of LeetCode problems, input is **ASCII only**. In that world, `[]byte` gives you everything you want — mutable, random access, no Unicode concerns, no rune complexity.

```go
// Instead of thinking "string with no constraints"
// Think: "I work in []byte, convert only at the boundary"

func solve(s string) string {
    b := []byte(s)      // O(n) — pay once at entry

    // Now do EVERYTHING here — full freedom
    b[0] = 'H'                          // random write: O(1)
    b[i], b[j] = b[j], b[i]            // swap: O(1)
    b = append(b, '!')                  // extend: O(1) amortized
    b = b[:len(b)-1]                    // shrink: O(1)
    _ = b[i]                            // random read: O(1)

    return string(b)    // O(n) — pay once at exit
}
```

You pay O(n) **twice** — entry and exit. Everything in between is free. This is the idiomatic Go pattern for string manipulation in DSA.

## For Unicode Problems — Work in `[]rune`

Same idea, but for true character-level access:

```go
func solve(s string) string {
    r := []rune(s)      // O(n) — pay once

    // Full freedom over characters
    r[i], r[j] = r[j], r[i]
    r[3] = '界'
    _ = len(r)          // actual character count, not bytes

    return string(r)    // O(n) — pay once
}
```

## The `unsafe` Path — Exists, Never Use It

There is technically a way to get a mutable view of a string's bytes without copying, using `unsafe`:

```go
import "unsafe"

// Convert string to []byte without allocation (READ CAREFULLY)
func stringToBytes(s string) []byte {
    return unsafe.Slice(unsafe.StringData(s), len(s))
}
```

**Do not use this.** Modifying a string's underlying bytes via `unsafe` is undefined behavior. Go's runtime may intern identical strings sharing the same memory. Mutating it corrupts other strings silently. It's a landmine, not a feature.

## The Mental Shift That Actually Helps

Stop thinking "string with no constraints." Start thinking:

```
Input boundary  →  []byte or []rune  →  manipulate freely  →  string output
```

Your working type is never `string`. String is only the serialization format for input/output. This is the same way C treats `char*` — you don't work in the abstract, you work in memory directly.

```go
// The expert Go DSA pattern — clean boundary model
func reverseWords(s string) string {
    b := []byte(s)              // enter the "free zone"

    // Step 1: reverse entire array
    reverse(b, 0, len(b)-1)

    // Step 2: reverse each word
    start := 0
    for i := 0; i <= len(b); i++ {
        if i == len(b) || b[i] == ' ' {
            reverse(b, start, i-1)
            start = i + 1
        }
    }

    return string(b)            // exit the "free zone"
}

func reverse(b []byte, i, j int) {
    for i < j {
        b[i], b[j] = b[j], b[i]
        i++; j--
    }
}
```

No conversions mid-algorithm. No rune concerns. Full mutability. O(n) entry + O(n) exit — unavoidable in any language that enforces string immutability (Java, Python, Rust all have the same cost, just hidden from you).

## The Comparison That Makes It Click

| Language | What you think you have | What actually happens |
|---|---|---|
| Python | Mutable strings | Strings immutable, every `s[i] = x` creates new string |
| Java | Mutable strings | `StringBuilder` under the hood — same as Go's `[]byte` |
| JavaScript | Free string ops | Immutable, every concat allocates |
| **Go** | **Explicit `[]byte` / `[]rune`** | **Honest — you see the cost, you control it** |

Go doesn't give you less power. It gives you the same power with the cost made visible. That visibility is the feature. In a systems language, hidden costs are bugs waiting to happen.

The constraint you're chafing against in Go is the same constraint that exists in every language — Go just refuses to lie to you about it.

## ASCII — The Foundation

**ASCII** stands for *American Standard Code for Information Interchange*, defined in 1963.

The core idea: assign a number to every character a typewriter could produce. That's it.

```
7 bits → 2^7 = 128 possible values (0–127)
```

### The Complete Mental Map

```
0–31    → Control characters (non-printable)
           0  = NULL
           9  = Tab
           10 = Newline (\n)
           13 = Carriage Return (\r)
           27 = Escape

32      → Space (first printable)

33–47   → ! " # $ % & ' ( ) * + , - . /

48–57   → 0 1 2 3 4 5 6 7 8 9
           '0' = 48, so digit → number: c - '0'

58–64   → : ; < = > ? @

65–90   → A B C D ... Z  (uppercase)
           'A' = 65

91–96   → [ \ ] ^ _ `

97–122  → a b c d ... z  (lowercase)
           'a' = 97

123–126 → { | } ~
127     → DEL (control)
```

### The Relationships You'll Use in DSA Every Day

```go
// Uppercase ↔ Lowercase: differ by exactly 32 (bit 5)
'a' - 'A' == 32         // true
'a' ^ ' ' == 'A'        // toggle case with XOR (space = 32 = bit 5)

// Digit to integer
'7' - '0' == 7          // true — works for all '0'–'9'

// Letter to index (0-based)
'g' - 'a' == 6          // for lowercase
'G' - 'A' == 6          // for uppercase

// Check ranges (byte-level, no imports needed)
c >= 'a' && c <= 'z'    // lowercase letter
c >= 'A' && c <= 'Z'    // uppercase letter
c >= '0' && c <= '9'    // digit
c == ' ' || c == '\t' || c == '\n'  // whitespace
```

### What "ASCII Text" Means Practically

When a LeetCode problem says *"input contains only lowercase English letters"* — that's ASCII. Specifically bytes 97–122. This is why in those problems:

```go
// This is safe and correct — no rune needed
var freq [26]int
for i := 0; i < len(s); i++ {
    freq[s[i]-'a']++    // s[i] is a byte, works perfectly
}
```

Every ASCII character is **exactly 1 byte**. So for ASCII-only input:

```
len(s) == number of characters   ← true
s[i]   == the character at i     ← true, no rune needed
```

This is the special case where Go's byte/rune distinction **disappears** — because every character fits in a single byte, the two views are identical.

### ASCII vs Non-ASCII — The Line

```
ASCII   →  bytes 0–127    →  English letters, digits, punctuation
Non-ASCII → bytes 128–255+ →  é, ñ, ك, 世, 😀, ക

In UTF-8:
  ASCII character   = 1 byte   (bit pattern: 0xxxxxxx)
  Non-ASCII starts  = 2+ bytes (bit pattern: 11xxxxxx...)
```

The moment a character has a value > 127, it spills into multiple bytes in UTF-8, and that's when `s[i]` gives you a fragment, not a character — which is exactly when you need `range` or `[]rune`.

### The DSA Decision Rule

```
Problem says "lowercase English letters" / "alphanumeric"?
→ Pure ASCII → work with []byte or direct s[i] → use [26]int freq array

Problem says "Unicode" / "any characters" / shows 中文 or emoji?
→ Non-ASCII possible → use range s or []rune
```

95% of LeetCode string problems are ASCII-only. Knowing this means you almost never actually need runes in competitive programming.

*Generated for Go DSA mastery — Anthropic Claude, Feb 2026*

30 sections. Everything an expert needs — in one document.

Here's the architecture of what's inside:

**The Problem-Solving Engine (Sections 1–2)** — The `READ → CATEGORIZE → CONSTRAINTS → BRUTE FORCE → OPTIMIZE → CODE → VERIFY` pipeline that separates amateurs from experts. Plus the constraint-to-complexity table (`n ≤ 10^5 → O(n log n)`) that immediately tells you what class of algorithm is required.

**Core Data Structures with Go idioms (Sections 3–21)** — Every structure with idiomatic Go: slices-as-stacks, `container/heap` interface, `map[T]struct{}` sets, Union-Find with path compression, Trie with `[26]*TrieNode`. Not just definitions — the exact code patterns you'll reach for in contests.

**Algorithmic Patterns (Sections 7–28)** — Every major pattern with template code: Two Pointers, Sliding Window, Binary Search on Answer (parametric search — one of the most underrated techniques), Backtracking, all DP variants (1D, 2D, Bitmask, Interval), Graphs (BFS/DFS/Dijkstra/Bellman-Ford/Prim/Kruskal/Topological sort).

**The Pattern Recognition Map (Section 29)** — This is the meta-skill table. Scan a problem, find the clue phrase, know the pattern. Build this into muscle memory.

**Ready-to-paste Templates (Section 30)** — Dijkstra, Backtracking with dedup, Binary Search on Answer, Union-Find inline — all in minimal, correct Go.

The cognitive principle embedded throughout: **chunking**. Each pattern is a chunk — a single retrievable unit. The goal of practice is to recognize which chunk applies within seconds, not to derive solutions from scratch. That's what the top 1% actually does differently.