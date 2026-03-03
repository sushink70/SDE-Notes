# The Complete Dynamic Programming Compendium
## From Foundations to World-Class Mastery

---

# PART I — THE PHILOSOPHY OF DP

## What Dynamic Programming Actually Is

Dynamic Programming is not an algorithm. It is a **problem decomposition philosophy** built on one insight:

> **Optimal substructure + overlapping subproblems = DP.**

Every DP solution is a proof: "the optimal answer to this problem is composed of optimal answers to strictly smaller versions of the same problem." If you cannot write that proof, DP does not apply.

### The Two Pillars

**1. Optimal Substructure**
An optimal solution to the problem contains optimal solutions to subproblems within it. This is what lets you trust a recursive definition.

**2. Overlapping Subproblems**
The same subproblems recur many times during recursion. This is what makes caching worthwhile — otherwise plain recursion or divide-and-conquer suffices.

### The Three Implementation Styles

| Style | Description | When to Use |
|---|---|---|
| **Top-Down (Memoization)** | Recursive + cache. Compute only what you need | Natural recursion, sparse state space |
| **Bottom-Up (Tabulation)** | Iterative. Fill table in dependency order | Dense state space, stack overflow risk |
| **Space-Optimized Bottom-Up** | Rolling array or single variable | When only last 1-2 layers needed |

### Expert Mental Model: State Design

Before writing a single line of code, an expert defines the **DP state** with surgical precision:

```
dp[i][j][k] = "the answer to the subproblem defined by parameters i, j, k"
```

The art is choosing parameters that:
1. Uniquely identify every subproblem
2. Capture everything needed to compute the answer
3. Are as few dimensions as possible

---

# PART II — FOUNDATIONAL PATTERNS

## Pattern 1: Linear DP (1D State)

### Problem: Fibonacci / Climbing Stairs

**State:** `dp[i]` = number of ways to reach step `i`
**Recurrence:** `dp[i] = dp[i-1] + dp[i-2]`
**Base:** `dp[0] = 1, dp[1] = 1`

```c
// C — O(n) time, O(1) space
int climb_stairs(int n) {
    if (n <= 1) return 1;
    int prev2 = 1, prev1 = 1;
    for (int i = 2; i <= n; i++) {
        int cur = prev1 + prev2;
        prev2 = prev1;
        prev1 = cur;
    }
    return prev1;
}
```

```cpp
// C++ — same, idiomatic
int climbStairs(int n) {
    if (n <= 1) return 1;
    int a = 1, b = 1;
    for (int i = 2; i <= n; ++i) {
        tie(a, b) = make_tuple(b, a + b);
    }
    return b;
}
```

```go
// Go — O(1) space
func climbStairs(n int) int {
    if n <= 1 { return 1 }
    a, b := 1, 1
    for i := 2; i <= n; i++ {
        a, b = b, a+b
    }
    return b
}
```

```rust
// Rust — idiomatic iterator
fn climb_stairs(n: u32) -> u64 {
    (0..n).fold((1u64, 1u64), |(a, b), _| (b, a + b)).0
}
```

---

## Pattern 2: Kadane's Algorithm (Maximum Subarray)

**Key Insight:** At each index, either extend the previous subarray or start fresh. The choice depends on whether the running sum is positive.

**State:** `dp[i]` = max subarray sum ending at index `i`
**Recurrence:** `dp[i] = max(arr[i], dp[i-1] + arr[i])`

```c
// C
int max_subarray(int* arr, int n) {
    int best = arr[0], cur = arr[0];
    for (int i = 1; i < n; i++) {
        cur = arr[i] > cur + arr[i] ? arr[i] : cur + arr[i];
        if (cur > best) best = cur;
    }
    return best;
}
```

```rust
// Rust — functional
fn max_subarray(arr: &[i64]) -> i64 {
    arr.iter().skip(1).fold(
        (arr[0], arr[0]),
        |(best, cur), &x| {
            let new_cur = cur.max(0) + x;
            (best.max(new_cur), new_cur)
        }
    ).0
}
```

```go
// Go
func maxSubarray(arr []int) int {
    best, cur := arr[0], arr[0]
    for _, x := range arr[1:] {
        if cur < 0 { cur = 0 }
        cur += x
        if cur > best { best = cur }
    }
    return best
}
```

---

## Pattern 3: House Robber (Decision DP)

**Problem:** Can't rob adjacent houses. Maximize loot.
**State:** `dp[i]` = max loot from first `i` houses
**Recurrence:** `dp[i] = max(dp[i-1], dp[i-2] + nums[i])`

```cpp
// C++
int rob(vector<int>& nums) {
    int n = nums.size();
    if (n == 1) return nums[0];
    int prev2 = nums[0], prev1 = max(nums[0], nums[1]);
    for (int i = 2; i < n; ++i) {
        int cur = max(prev1, prev2 + nums[i]);
        prev2 = prev1; prev1 = cur;
    }
    return prev1;
}
```

```rust
fn rob(nums: Vec<i32>) -> i32 {
    nums.iter().fold((0, 0), |(prev2, prev1), &x| {
        (prev1, prev1.max(prev2 + x))
    }).1
}
```

---

# PART III — KNAPSACK FAMILY

The knapsack family is the backbone of combinatorial DP. Master these deeply.

## 3.1 — 0/1 Knapsack

**Problem:** N items, each with weight `w[i]` and value `v[i]`. Capacity `W`. Each item used at most once.

**State:** `dp[i][w]` = max value using first `i` items with weight limit `w`
**Recurrence:**
- Skip item i: `dp[i][w] = dp[i-1][w]`
- Take item i (if `w[i] <= w`): `dp[i][w] = dp[i-1][w - w[i]] + v[i]`
- `dp[i][w] = max(above two)`

**Critical insight for space optimization:** Because `dp[i]` depends only on `dp[i-1]`, we can use a 1D array, but **must iterate `w` from right to left** to avoid using an item twice.

```c
// C — O(nW) time, O(W) space
int knapsack01(int* w, int* v, int n, int W) {
    int* dp = calloc(W + 1, sizeof(int));
    for (int i = 0; i < n; i++) {
        for (int cap = W; cap >= w[i]; cap--) {   // RIGHT TO LEFT is crucial
            int take = dp[cap - w[i]] + v[i];
            if (take > dp[cap]) dp[cap] = take;
        }
    }
    int ans = dp[W];
    free(dp);
    return ans;
}
```

```cpp
// C++ — clean version
int knapsack01(vector<int>& w, vector<int>& v, int W) {
    vector<int> dp(W + 1, 0);
    for (int i = 0; i < (int)w.size(); ++i)
        for (int cap = W; cap >= w[i]; --cap)
            dp[cap] = max(dp[cap], dp[cap - w[i]] + v[i]);
    return dp[W];
}
```

```go
// Go
func knapsack01(w, v []int, W int) int {
    dp := make([]int, W+1)
    for i := range w {
        for cap := W; cap >= w[i]; cap-- {
            if val := dp[cap-w[i]] + v[i]; val > dp[cap] {
                dp[cap] = val
            }
        }
    }
    return dp[W]
}
```

```rust
// Rust
fn knapsack01(w: &[usize], v: &[i64], cap: usize) -> i64 {
    let mut dp = vec![0i64; cap + 1];
    for (wi, vi) in w.iter().zip(v.iter()) {
        for c in ((*wi)..=cap).rev() {
            dp[c] = dp[c].max(dp[c - wi] + vi);
        }
    }
    dp[cap]
}
```

---

## 3.2 — Unbounded Knapsack

**Change:** Each item can be used **unlimited** times.
**Key difference:** Iterate `w` from **left to right** (allows reuse).

```c
// C — only direction changes!
int unbounded_knapsack(int* w, int* v, int n, int W) {
    int* dp = calloc(W + 1, sizeof(int));
    for (int i = 0; i < n; i++) {
        for (int cap = w[i]; cap <= W; cap++) {    // LEFT TO RIGHT
            int take = dp[cap - w[i]] + v[i];
            if (take > dp[cap]) dp[cap] = take;
        }
    }
    int ans = dp[W]; free(dp); return ans;
}
```

```rust
fn unbounded_knapsack(w: &[usize], v: &[i64], cap: usize) -> i64 {
    let mut dp = vec![0i64; cap + 1];
    for c in 0..=cap {
        for (wi, vi) in w.iter().zip(v.iter()) {
            if *wi <= c {
                dp[c] = dp[c].max(dp[c - wi] + vi);
            }
        }
    }
    dp[cap]
}
```

---

## 3.3 — Bounded Knapsack

**Change:** Item `i` can be used at most `k[i]` times.

**Naive:** O(n * W * max_k). 
**Optimized via Binary Grouping:** Split each item into groups of 1, 2, 4, ..., remainder. Reduces to O(n * log(max_k) * W) 0/1 knapsack.

```cpp
// C++ — Binary Grouping
int bounded_knapsack(vector<int>& w, vector<int>& v, vector<int>& k, int W) {
    vector<int> dp(W + 1, 0);
    // Expand each item into binary groups
    for (int i = 0; i < (int)w.size(); ++i) {
        int rem = k[i];
        for (int mul = 1; rem > 0; mul <<= 1) {
            int cnt = min(mul, rem);
            rem -= cnt;
            int gw = cnt * w[i], gv = cnt * v[i];
            for (int cap = W; cap >= gw; --cap)
                dp[cap] = max(dp[cap], dp[cap - gw] + gv);
        }
    }
    return dp[W];
}
```

---

## 3.4 — Partition Equal Subset Sum (Subset Sum / Boolean Knapsack)

**Problem:** Can we partition array into two equal-sum subsets?

This is 0/1 knapsack where values equal weights and target = total_sum / 2. Boolean variant.

```go
func canPartition(nums []int) bool {
    total := 0
    for _, x := range nums { total += x }
    if total%2 != 0 { return false }
    target := total / 2
    dp := make([]bool, target+1)
    dp[0] = true
    for _, x := range nums {
        for j := target; j >= x; j-- {
            dp[j] = dp[j] || dp[j-x]
        }
    }
    return dp[target]
}
```

```rust
fn can_partition(nums: &[i32]) -> bool {
    let total: i32 = nums.iter().sum();
    if total % 2 != 0 { return false; }
    let target = (total / 2) as usize;
    let mut dp = vec![false; target + 1];
    dp[0] = true;
    for &x in nums {
        let x = x as usize;
        for j in (x..=target).rev() {
            dp[j] |= dp[j - x];
        }
    }
    dp[target]
}
```

---

## 3.5 — Coin Change (Count Ways vs Minimum Coins)

### Minimum Coins (Unbounded knapsack on counts)

```c
// C
int coin_change(int* coins, int n, int amount) {
    int* dp = malloc((amount + 1) * sizeof(int));
    for (int i = 0; i <= amount; i++) dp[i] = amount + 1;
    dp[0] = 0;
    for (int i = 1; i <= amount; i++) {
        for (int j = 0; j < n; j++) {
            if (coins[j] <= i) {
                int v = dp[i - coins[j]] + 1;
                if (v < dp[i]) dp[i] = v;
            }
        }
    }
    int ans = dp[amount] > amount ? -1 : dp[amount];
    free(dp); return ans;
}
```

### Count Ways (Combination — order doesn't matter)

Outer loop: **coins**, inner loop: **amounts** (unbounded, left-to-right)

```cpp
// C++
long long count_ways(vector<int>& coins, int amount) {
    vector<long long> dp(amount + 1, 0);
    dp[0] = 1;
    for (int c : coins)                      // outer = items
        for (int a = c; a <= amount; ++a)    // inner = amounts (L->R)
            dp[a] += dp[a - c];
    return dp[amount];
}
```

### Count Permutations (Order matters — Permutation Sum)

Outer loop: **amounts**, inner loop: **coins**

```cpp
long long count_permutations(vector<int>& coins, int amount) {
    vector<long long> dp(amount + 1, 0);
    dp[0] = 1;
    for (int a = 1; a <= amount; ++a)        // outer = amounts
        for (int c : coins)                  // inner = items
            if (c <= a) dp[a] += dp[a - c];
    return dp[amount];
}
```

> **Critical mental model:** Combinations (outer=items) vs Permutations (outer=amounts). This distinction appears everywhere.

---

# PART IV — STRING DP

## 4.1 — Longest Common Subsequence (LCS)

**State:** `dp[i][j]` = LCS length of `s1[0..i]` and `s2[0..j]`
**Recurrence:**
- If `s1[i-1] == s2[j-1]`: `dp[i][j] = dp[i-1][j-1] + 1`
- Else: `dp[i][j] = max(dp[i-1][j], dp[i][j-1])`

```c
// C — O(mn) time, O(mn) space
int lcs(char* s1, char* s2) {
    int m = strlen(s1), n = strlen(s2);
    int dp[m+1][n+1];
    memset(dp, 0, sizeof(dp));
    for (int i = 1; i <= m; i++)
        for (int j = 1; j <= n; j++)
            dp[i][j] = s1[i-1] == s2[j-1]
                ? dp[i-1][j-1] + 1
                : (dp[i-1][j] > dp[i][j-1] ? dp[i-1][j] : dp[i][j-1]);
    return dp[m][n];
}
```

```rust
fn lcs(s1: &[u8], s2: &[u8]) -> usize {
    let (m, n) = (s1.len(), s2.len());
    let mut dp = vec![vec![0usize; n + 1]; m + 1];
    for i in 1..=m {
        for j in 1..=n {
            dp[i][j] = if s1[i-1] == s2[j-1] {
                dp[i-1][j-1] + 1
            } else {
                dp[i-1][j].max(dp[i][j-1])
            };
        }
    }
    dp[m][n]
}
```

**Space-optimized to O(n) using two rows:**

```go
func lcs(s1, s2 string) int {
    m, n := len(s1), len(s2)
    prev := make([]int, n+1)
    for i := 1; i <= m; i++ {
        cur := make([]int, n+1)
        for j := 1; j <= n; j++ {
            if s1[i-1] == s2[j-1] {
                cur[j] = prev[j-1] + 1
            } else if prev[j] > cur[j-1] {
                cur[j] = prev[j]
            } else {
                cur[j] = cur[j-1]
            }
        }
        prev = cur
    }
    return prev[n]
}
```

---

## 4.2 — Edit Distance (Levenshtein)

**State:** `dp[i][j]` = min operations to convert `s1[0..i]` to `s2[0..j]`
**Operations:** Insert, Delete, Replace (each costs 1)

```cpp
// C++
int edit_distance(const string& s1, const string& s2) {
    int m = s1.size(), n = s2.size();
    vector<vector<int>> dp(m+1, vector<int>(n+1));
    for (int i = 0; i <= m; ++i) dp[i][0] = i;
    for (int j = 0; j <= n; ++j) dp[0][j] = j;
    for (int i = 1; i <= m; ++i)
        for (int j = 1; j <= n; ++j)
            dp[i][j] = s1[i-1] == s2[j-1]
                ? dp[i-1][j-1]
                : 1 + min({dp[i-1][j], dp[i][j-1], dp[i-1][j-1]});
    return dp[m][n];
}
```

```rust
fn edit_distance(s1: &str, s2: &str) -> usize {
    let s1: Vec<char> = s1.chars().collect();
    let s2: Vec<char> = s2.chars().collect();
    let (m, n) = (s1.len(), s2.len());
    let mut dp: Vec<Vec<usize>> = (0..=m).map(|i| {
        let mut row = vec![0; n + 1];
        row[0] = i;
        row
    }).collect();
    for j in 0..=n { dp[0][j] = j; }
    for i in 1..=m {
        for j in 1..=n {
            dp[i][j] = if s1[i-1] == s2[j-1] {
                dp[i-1][j-1]
            } else {
                1 + dp[i-1][j].min(dp[i][j-1]).min(dp[i-1][j-1])
            };
        }
    }
    dp[m][n]
}
```

---

## 4.3 — Longest Palindromic Subsequence

**Key Insight:** `LPS(s) = LCS(s, reverse(s))`

Or direct DP:
**State:** `dp[i][j]` = LPS length of `s[i..j]`

```go
func longestPalindromicSubseq(s string) int {
    n := len(s)
    dp := make([][]int, n)
    for i := range dp {
        dp[i] = make([]int, n)
        dp[i][i] = 1
    }
    for length := 2; length <= n; length++ {
        for i := 0; i <= n-length; i++ {
            j := i + length - 1
            if s[i] == s[j] {
                dp[i][j] = 2
                if length > 2 { dp[i][j] += dp[i+1][j-1] }
            } else {
                if dp[i+1][j] > dp[i][j-1] {
                    dp[i][j] = dp[i+1][j]
                } else {
                    dp[i][j] = dp[i][j-1]
                }
            }
        }
    }
    return dp[0][n-1]
}
```

---

## 4.4 — Longest Increasing Subsequence (LIS)

### O(n²) DP Version

```c
int lis_n2(int* arr, int n) {
    int* dp = malloc(n * sizeof(int));
    for (int i = 0; i < n; i++) dp[i] = 1;
    int ans = 1;
    for (int i = 1; i < n; i++) {
        for (int j = 0; j < i; j++) {
            if (arr[j] < arr[i] && dp[j] + 1 > dp[i])
                dp[i] = dp[j] + 1;
        }
        if (dp[i] > ans) ans = dp[i];
    }
    free(dp); return ans;
}
```

### O(n log n) via Patience Sorting + Binary Search

**Key insight:** Maintain a `tails` array where `tails[i]` = smallest tail element of any IS of length `i+1`. Use binary search to place each element.

```cpp
// C++ — O(n log n)
int lis_nlogn(vector<int>& nums) {
    vector<int> tails;
    for (int x : nums) {
        auto it = lower_bound(tails.begin(), tails.end(), x);
        if (it == tails.end()) tails.push_back(x);
        else *it = x;
    }
    return tails.size();
}
```

```rust
fn lis_nlogn(nums: &[i32]) -> usize {
    let mut tails: Vec<i32> = Vec::new();
    for &x in nums {
        match tails.binary_search(&x) {
            Ok(i) | Err(i) => {
                if i == tails.len() { tails.push(x); }
                else { tails[i] = x; }
            }
        }
    }
    tails.len()
}
```

```go
func lis(nums []int) int {
    tails := []int{}
    for _, x := range nums {
        lo, hi := 0, len(tails)
        for lo < hi {
            mid := (lo + hi) / 2
            if tails[mid] < x { lo = mid + 1 } else { hi = mid }
        }
        if lo == len(tails) { tails = append(tails, x) } else { tails[lo] = x }
    }
    return len(tails)
}
```

---

## 4.5 — Palindrome Partitioning (Minimum Cuts)

**State:** `dp[i]` = min cuts for `s[0..i]`
**Key:** Precompute palindrome table `isPalin[i][j]`

```cpp
int min_cuts(const string& s) {
    int n = s.size();
    vector<vector<bool>> p(n, vector<bool>(n, false));
    // Build palindrome table
    for (int i = n-1; i >= 0; --i)
        for (int j = i; j < n; ++j)
            p[i][j] = s[i] == s[j] && (j - i < 2 || p[i+1][j-1]);
    
    vector<int> dp(n, INT_MAX);
    for (int i = 0; i < n; ++i) {
        if (p[0][i]) { dp[i] = 0; continue; }
        for (int j = 1; j <= i; ++j)
            if (p[j][i] && dp[j-1] + 1 < dp[i])
                dp[i] = dp[j-1] + 1;
    }
    return dp[n-1];
}
```

---

# PART V — INTERVAL DP

## Pattern: Think in intervals [i, j], build from smaller to larger

**Key:** Outer loop is **length**, inner loops are **start** and **split point**.

## 5.1 — Matrix Chain Multiplication

**State:** `dp[i][j]` = min multiplications for matrices i through j
**Recurrence:** `dp[i][j] = min over all k in [i,j-1] of { dp[i][k] + dp[k+1][j] + dims[i]*dims[k+1]*dims[j+1] }`

```c
// C — dims has n+1 elements for n matrices
// Matrix i has dimensions dims[i] x dims[i+1]
int matrix_chain(int* dims, int n) {
    // dp[i][j] = min cost to multiply matrices i..j (0-indexed)
    int dp[n][n];
    memset(dp, 0, sizeof(dp));
    for (int len = 2; len <= n; len++) {
        for (int i = 0; i <= n - len; i++) {
            int j = i + len - 1;
            dp[i][j] = INT_MAX;
            for (int k = i; k < j; k++) {
                int cost = dp[i][k] + dp[k+1][j] + dims[i]*dims[k+1]*dims[j+1];
                if (cost < dp[i][j]) dp[i][j] = cost;
            }
        }
    }
    return dp[0][n-1];
}
```

```rust
fn matrix_chain(dims: &[usize]) -> usize {
    let n = dims.len() - 1;
    let mut dp = vec![vec![0usize; n]; n];
    for len in 2..=n {
        for i in 0..=(n - len) {
            let j = i + len - 1;
            dp[i][j] = usize::MAX;
            for k in i..j {
                let cost = dp[i][k] + dp[k+1][j] + dims[i] * dims[k+1] * dims[j+1];
                if cost < dp[i][j] { dp[i][j] = cost; }
            }
        }
    }
    dp[0][n-1]
}
```

---

## 5.2 — Burst Balloons

**Problem:** Burst all balloons. Bursting balloon `k` between `i` and `j` (both boundaries) gives `nums[i]*nums[k]*nums[j]` coins.

**Insight:** Think of `k` as the **last** balloon to burst in range `(i,j)`, not the first. This avoids dependency issues.

```go
func max_coins(nums []int) int {
    // Pad with 1s on both sides
    n := len(nums)
    arr := make([]int, n+2)
    arr[0], arr[n+1] = 1, 1
    copy(arr[1:], nums)
    n += 2
    
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
```

---

## 5.3 — Optimal BST

**State:** `dp[i][j]` = min search cost for keys `i..j`
**Recurrence:** For each root `r`, cost = `dp[i][r-1] + dp[r+1][j] + sum(freq[i..j])`

```cpp
// C++ — with prefix sums for O(n^3) total
int optimal_bst(vector<int>& freq) {
    int n = freq.size();
    vector<int> prefix(n+1, 0);
    for (int i = 0; i < n; ++i) prefix[i+1] = prefix[i] + freq[i];
    auto sum = [&](int l, int r) { return prefix[r+1] - prefix[l]; };
    
    vector<vector<int>> dp(n+1, vector<int>(n, 0));
    for (int len = 1; len <= n; ++len) {
        for (int i = 0; i + len - 1 < n; ++i) {
            int j = i + len - 1;
            dp[i][j] = INT_MAX;
            for (int r = i; r <= j; ++r) {
                int left_cost  = (r > i) ? dp[i][r-1] : 0;
                int right_cost = (r < j) ? dp[r+1][j] : 0;
                int cost = left_cost + right_cost + sum(i, j);
                dp[i][j] = min(dp[i][j], cost);
            }
        }
    }
    return dp[0][n-1];
}
```

---

# PART VI — 2D DP (GRID DP)

## 6.1 — Unique Paths

```go
func uniquePaths(m, n int) int {
    dp := make([]int, n)
    for j := range dp { dp[j] = 1 }
    for i := 1; i < m; i++ {
        for j := 1; j < n; j++ {
            dp[j] += dp[j-1]
        }
    }
    return dp[n-1]
}
```

---

## 6.2 — Minimum Path Sum

```rust
fn min_path_sum(grid: &mut Vec<Vec<i32>>) -> i32 {
    let (m, n) = (grid.len(), grid[0].len());
    for i in 0..m {
        for j in 0..n {
            grid[i][j] += match (i, j) {
                (0, 0) => 0,
                (0, _) => grid[0][j-1] - grid[0][j],  // subtract since we already added
                (_, 0) => grid[i-1][0] - grid[i][0],
                _ => (grid[i-1][j]).min(grid[i][j-1]) - grid[i][j],
            };
        }
    }
    // Cleaner version:
    let (m, n) = (grid.len(), grid[0].len());
    let mut dp = grid.clone();
    for i in 1..m { dp[i][0] += dp[i-1][0]; }
    for j in 1..n { dp[0][j] += dp[0][j-1]; }
    for i in 1..m {
        for j in 1..n {
            dp[i][j] += dp[i-1][j].min(dp[i][j-1]);
        }
    }
    dp[m-1][n-1]
}
```

---

## 6.3 — Maximal Square

**State:** `dp[i][j]` = side length of largest square with bottom-right at (i,j)
**Recurrence:** `dp[i][j] = min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]) + 1` (if matrix[i][j] == 1)

```cpp
int maximal_square(vector<vector<char>>& matrix) {
    int m = matrix.size(), n = matrix[0].size(), ans = 0;
    vector<int> dp(n + 1, 0), prev(n + 1, 0);
    for (int i = 1; i <= m; ++i) {
        for (int j = 1; j <= n; ++j) {
            if (matrix[i-1][j-1] == '1') {
                dp[j] = min({prev[j], dp[j-1], prev[j-1]}) + 1;
                ans = max(ans, dp[j]);
            } else dp[j] = 0;
        }
        swap(dp, prev);
        fill(dp.begin(), dp.end(), 0);
    }
    return ans * ans;
}
```

---

# PART VII — BITMASK DP

## Core Concept

When `n` is small (≤ 20-25), we can represent subsets as integers. Each bit represents whether element `i` is in the subset.

**Classic use cases:** TSP, assignment problems, counting Hamiltonian paths, minimum XOR spanning set.

## 7.1 — Traveling Salesman Problem (TSP)

**State:** `dp[mask][i]` = min cost to visit all cities in `mask`, ending at city `i`
**Recurrence:** `dp[mask | (1<<j)][j] = min(dp[mask][i] + cost[i][j])` for all `j` not in mask

```c
// C — O(2^n * n^2) time, O(2^n * n) space
#define MAXN 20
int tsp(int n, int cost[MAXN][MAXN]) {
    int full = (1 << n) - 1;
    int dp[1 << MAXN][MAXN];
    for (int mask = 0; mask <= full; mask++)
        for (int i = 0; i < n; i++) dp[mask][i] = INT_MAX / 2;
    dp[1][0] = 0;  // Start at city 0
    
    for (int mask = 1; mask <= full; mask++) {
        for (int i = 0; i < n; i++) {
            if (!(mask & (1 << i))) continue;
            if (dp[mask][i] == INT_MAX / 2) continue;
            for (int j = 0; j < n; j++) {
                if (mask & (1 << j)) continue;
                int nmask = mask | (1 << j);
                int val = dp[mask][i] + cost[i][j];
                if (val < dp[nmask][j]) dp[nmask][j] = val;
            }
        }
    }
    int ans = INT_MAX;
    for (int i = 1; i < n; i++) {
        int v = dp[full][i] + cost[i][0];
        if (v < ans) ans = v;
    }
    return ans;
}
```

```rust
fn tsp(cost: &Vec<Vec<i32>>) -> i32 {
    let n = cost.len();
    let full = (1 << n) - 1;
    let inf = i32::MAX / 2;
    let mut dp = vec![vec![inf; n]; 1 << n];
    dp[1][0] = 0;
    
    for mask in 1usize..=(full as usize) {
        for i in 0..n {
            if mask & (1 << i) == 0 || dp[mask][i] == inf { continue; }
            for j in 0..n {
                if mask & (1 << j) != 0 { continue; }
                let nmask = mask | (1 << j);
                let val = dp[mask][i] + cost[i][j];
                if val < dp[nmask][j] { dp[nmask][j] = val; }
            }
        }
    }
    (1..n).map(|i| dp[full as usize][i] + cost[i][0]).min().unwrap_or(inf)
}
```

---

## 7.2 — Assignment Problem (Minimum Cost)

**State:** `dp[mask]` = min cost assigning first `popcount(mask)` people to tasks in `mask`

```go
func assign_min_cost(cost [][]int) int {
    n := len(cost)
    INF := 1<<30
    dp := make([]int, 1<<n)
    for i := range dp { dp[i] = INF }
    dp[0] = 0
    
    for mask := 1; mask < (1 << n); mask++ {
        person := bits.OnesCount(uint(mask)) - 1  // which person we're assigning
        for task := 0; task < n; task++ {
            if mask & (1 << task) == 0 { continue }
            prev := mask ^ (1 << task)
            if val := dp[prev] + cost[person][task]; val < dp[mask] {
                dp[mask] = val
            }
        }
    }
    return dp[(1<<n)-1]
}
```

---

## 7.3 — Counting Hamiltonian Paths

```cpp
int count_hamiltonian(int n, vector<vector<int>>& adj) {
    vector<vector<int>> dp(1<<n, vector<int>(n, 0));
    for (int i = 0; i < n; ++i) dp[1<<i][i] = 1;
    
    for (int mask = 1; mask < (1<<n); ++mask)
        for (int v = 0; v < n; ++v) {
            if (!dp[mask][v]) continue;
            for (int u = 0; u < n; ++u) {
                if ((mask>>u&1) || !adj[v][u]) continue;
                dp[mask|(1<<u)][u] += dp[mask][v];
            }
        }
    
    int full = (1<<n) - 1, ans = 0;
    for (int v = 0; v < n; ++v) ans += dp[full][v];
    return ans;
}
```

---

# PART VIII — TREE DP

## 8.1 — Maximum Independent Set on Tree

**State:** `dp[v][0]` = max IS size in subtree rooted at `v`, not including `v`
         `dp[v][1]` = max IS size in subtree rooted at `v`, including `v`

```cpp
// C++ — DFS-based
struct Tree {
    int n;
    vector<vector<int>> adj;
    vector<array<int,2>> dp;
    
    Tree(int n) : n(n), adj(n), dp(n) {}
    
    void dfs(int v, int parent) {
        dp[v] = {0, 1};  // {exclude v, include v}
        for (int u : adj[v]) {
            if (u == parent) continue;
            dfs(u, v);
            dp[v][0] += max(dp[u][0], dp[u][1]);  // exclude v: child can be included or not
            dp[v][1] += dp[u][0];                  // include v: child must be excluded
        }
    }
    
    int solve() {
        dfs(0, -1);
        return max(dp[0][0], dp[0][1]);
    }
};
```

```rust
fn tree_mis(adj: &Vec<Vec<usize>>, root: usize) -> usize {
    fn dfs(v: usize, parent: usize, adj: &Vec<Vec<usize>>, dp: &mut Vec<[usize; 2]>) {
        dp[v] = [0, 1];
        for &u in &adj[v] {
            if u == parent { continue; }
            dfs(u, v, adj, dp);
            dp[v][0] += dp[u][0].max(dp[u][1]);
            dp[v][1] += dp[u][0];
        }
    }
    let mut dp = vec![[0usize; 2]; adj.len()];
    dfs(root, usize::MAX, adj, &mut dp);
    dp[root][0].max(dp[root][1])
}
```

---

## 8.2 — Tree Diameter

```go
var diameter int
func tree_diam(adj [][]int) int {
    diameter = 0
    var dfs func(v, parent int) int
    dfs = func(v, parent int) int {
        best1, best2 := 0, 0
        for _, u := range adj[v] {
            if u == parent { continue }
            d := dfs(u, v) + 1
            if d > best1 { best1, best2 = d, best1 } else if d > best2 { best2 = d }
        }
        if best1+best2 > diameter { diameter = best1 + best2 }
        return best1
    }
    dfs(0, -1)
    return diameter
}
```

---

## 8.3 — Tree Knapsack (DP on subtree sizes)

**Problem:** Select exactly `k` nodes from a tree with values; maximize total value.

```cpp
// C++ — O(n^2)
vector<int> val, sz;
vector<vector<int>> adj2;
vector<vector<int>> dp2;  // dp2[v][k] = max value selecting k nodes from subtree of v

void dfs_knapsack(int v, int p) {
    sz[v] = 1;
    dp2[v].assign(2, 0);
    dp2[v][1] = val[v];  // include v itself
    for (int u : adj2[v]) {
        if (u == p) continue;
        dfs_knapsack(u, v);
        // Merge subtrees
        int new_sz = sz[v] + sz[u];
        vector<int> new_dp(new_sz + 1, 0);
        for (int j = 0; j <= sz[v]; ++j)
            for (int k = 0; k <= sz[u]; ++k)
                new_dp[j+k] = max(new_dp[j+k], dp2[v][j] + dp2[u][k]);
        dp2[v] = new_dp;
        sz[v] = new_sz;
    }
}
```

---

# PART IX — DP ON GRAPHS / DAGs

## 9.1 — Longest Path in a DAG

**Key:** DP works directly on DAGs because there are no cycles. Process in topological order.

```go
func longest_path_dag(n int, edges [][2]int) int {
    adj := make([][]int, n)
    indegree := make([]int, n)
    for _, e := range edges {
        adj[e[0]] = append(adj[e[0]], e[1])
        indegree[e[1]]++
    }
    // Topological sort (Kahn's)
    queue := []int{}
    for i := 0; i < n; i++ {
        if indegree[i] == 0 { queue = append(queue, i) }
    }
    dp := make([]int, n)
    ans := 0
    for len(queue) > 0 {
        v := queue[0]; queue = queue[1:]
        for _, u := range adj[v] {
            if dp[v]+1 > dp[u] { dp[u] = dp[v]+1 }
            if dp[u] > ans { ans = dp[u] }
            indegree[u]--
            if indegree[u] == 0 { queue = append(queue, u) }
        }
    }
    return ans
}
```

---

## 9.2 — Number of Paths in a DAG

```rust
fn count_paths_dag(n: usize, adj: &Vec<Vec<usize>>, src: usize, dst: usize) -> u64 {
    let mut topo = vec![];
    let mut visited = vec![false; n];
    fn dfs(v: usize, adj: &Vec<Vec<usize>>, visited: &mut Vec<bool>, topo: &mut Vec<usize>) {
        visited[v] = true;
        for &u in &adj[v] { if !visited[u] { dfs(u, adj, visited, topo); } }
        topo.push(v);
    }
    for i in 0..n { if !visited[i] { dfs(i, adj, &mut visited, &mut topo); } }
    topo.reverse();
    
    let mut dp = vec![0u64; n];
    dp[src] = 1;
    for &v in &topo {
        for &u in &adj[v] {
            dp[u] += dp[v];
        }
    }
    dp[dst]
}
```

---

# PART X — DIGIT DP

## Core Pattern

**Problem Type:** Count numbers in `[L, R]` satisfying some property on their digits.

**State:** `dp[pos][tight][...extra_state]`
- `pos` = current digit position
- `tight` = are we still bounded by the limit?
- Extra state = whatever property we're tracking (sum, mod, digit seen, etc.)

```cpp
// C++ — Template for digit DP
// Count numbers in [0, N] with digit sum divisible by k
string num;
int k;
map<tuple<int,int,int>, long long> memo;

long long solve(int pos, int tight, int sum) {
    if (pos == (int)num.size()) return sum % k == 0 ? 1 : 0;
    auto key = make_tuple(pos, tight, sum);
    if (memo.count(key)) return memo[key];
    
    int limit = tight ? (num[pos] - '0') : 9;
    long long ans = 0;
    for (int d = 0; d <= limit; ++d) {
        ans += solve(pos+1, tight && d == limit, (sum + d) % k);
    }
    return memo[key] = ans;
}

long long count_in_range(long long L, long long R, int _k) {
    k = _k; memo.clear();
    num = to_string(R);
    long long res = solve(0, 1, 0);
    if (L > 0) {
        memo.clear();
        num = to_string(L - 1);
        res -= solve(0, 1, 0);
    }
    return res;
}
```

```go
// Go — Digit DP with memoization
func count_no_consecutive_ones(n int) int64 {
    digits := []int{}
    for x := n; x > 0; x /= 10 { digits = append([]int{x % 10}, digits...) }
    
    type State struct{ pos, tight, lastDigit int }
    memo := map[State]int64{}
    
    var dp func(pos, tight, lastDigit int) int64
    dp = func(pos, tight, lastDigit int) int64 {
        if pos == len(digits) { return 1 }
        s := State{pos, tight, lastDigit}
        if v, ok := memo[s]; ok { return v }
        limit := 9
        if tight == 1 { limit = digits[pos] }
        var ans int64
        for d := 0; d <= limit; d++ {
            if d == 1 && lastDigit == 1 { continue }  // no consecutive 1s
            nt := 0
            if tight == 1 && d == limit { nt = 1 }
            ans += dp(pos+1, nt, d)
        }
        memo[s] = ans
        return ans
    }
    return dp(0, 1, 0)
}
```

---

# PART XI — DP WITH DATA STRUCTURES

## 11.1 — Segment Tree / BIT-Optimized DP

**Problem:** LIS in O(n log n) using BIT (Fenwick Tree) — values as indices.

```cpp
// C++ — BIT for range max query
struct BIT {
    vector<int> tree;
    int n;
    BIT(int n) : n(n), tree(n+1, 0) {}
    void update(int i, int v) { for (++i; i <= n; i += i&-i) tree[i] = max(tree[i], v); }
    int query(int i) { int r=0; for (++i; i>0; i -= i&-i) r = max(r, tree[i]); return r; }
};

int lis_bit(vector<int>& nums) {
    // Coordinate compress
    vector<int> sorted = nums;
    sort(sorted.begin(), sorted.end());
    sorted.erase(unique(sorted.begin(), sorted.end()), sorted.end());
    auto rank = [&](int x) { return lower_bound(sorted.begin(), sorted.end(), x) - sorted.begin(); };
    
    int n = sorted.size();
    BIT bit(n);
    int ans = 0;
    for (int x : nums) {
        int r = rank(x);
        int best = r > 0 ? bit.query(r-1) + 1 : 1;
        ans = max(ans, best);
        bit.update(r, best);
    }
    return ans;
}
```

---

## 11.2 — Divide and Conquer Optimization

**When to apply:** `dp[i][j] = min over k < j of { dp[i-1][k] + cost(k+1, j) }` and `cost` is **concave** (opt[i][j] ≤ opt[i][j+1]).

Reduces O(n³) → O(n² log n) or O(n²).

```cpp
// C++ — Divide and Conquer DP optimization
// dp[j] = min cost with j groups using first j elements
// cost(l, r) = cost of making elements [l..r] one group
vector<long long> prev_dp, cur_dp;
auto cost = [](int l, int r) -> long long { /* define here */ return 0; };

void dc(int lo, int hi, int opt_lo, int opt_hi) {
    if (lo > hi) return;
    int mid = (lo + hi) / 2;
    int best_k = opt_lo;
    long long best = LLONG_MAX;
    for (int k = opt_lo; k <= min(mid-1, opt_hi); ++k) {
        long long v = prev_dp[k] + cost(k+1, mid);
        if (v < best) { best = v; best_k = k; }
    }
    cur_dp[mid] = best;
    dc(lo, mid-1, opt_lo, best_k);
    dc(mid+1, hi, best_k, opt_hi);
}
```

---

## 11.3 — Convex Hull Trick (CHT)

**When to apply:** `dp[i] = min over j < i of { dp[j] + b[j]*a[i] + c[i] }` — linear functions in `a[i]`.

This is the "Li Chao Tree" or "line container" approach. Reduces O(n²) → O(n log n).

```cpp
// C++ — Li Chao Tree for minimum of linear functions
struct Line { long long m, b; long long eval(long long x) { return m*x + b; } };
struct LiChao {
    static const int MAXX = 1e9;
    struct Node { Line line; int l, r; } nodes[400005];
    int cnt = 0, root = -1;
    
    void add(int& v, int lo, int hi, Line line) {
        if (v == -1) { v = cnt++; nodes[v] = {line, -1, -1}; return; }
        int mid = (lo + hi) / 2;
        bool left_better = line.eval(lo) < nodes[v].line.eval(lo);
        bool mid_better  = line.eval(mid) < nodes[v].line.eval(mid);
        if (mid_better) swap(nodes[v].line, line);
        if (lo == hi) return;
        if (left_better != mid_better) add(nodes[v].l, lo, mid, line);
        else add(nodes[v].r, mid+1, hi, line);
    }
    
    long long query(int v, int lo, int hi, long long x) {
        if (v == -1) return LLONG_MAX;
        int mid = (lo + hi) / 2;
        long long res = nodes[v].line.eval(x);
        if (x <= mid) return min(res, query(nodes[v].l, lo, mid, x));
        return min(res, query(nodes[v].r, mid+1, hi, x));
    }
    
    void add(Line l) { add(root, 0, MAXX, l); }
    long long query(long long x) { return query(root, 0, MAXX, x); }
};
```

---

# PART XII — PROBABILITY / EXPECTED VALUE DP

## 12.1 — Expected Steps to Reach Goal

```go
// Expected number of dice rolls to reach N (each roll 1-6)
func expected_rolls(N int) float64 {
    dp := make([]float64, N+1)
    // dp[i] = expected rolls from position i to N
    // dp[N] = 0 (already there)
    // dp[i] = 1 + (1/6) * sum(dp[min(i+d, N)] for d in 1..6)
    for i := N - 1; i >= 0; i-- {
        sum := 0.0
        for d := 1; d <= 6; d++ {
            next := i + d
            if next > N { next = N }
            sum += dp[next]
        }
        dp[i] = 1.0 + sum/6.0
    }
    return dp[0]
}
```

## 12.2 — Probability DP

```rust
// Probability of exactly k heads in n flips of biased coin (p)
fn prob_k_heads(n: usize, k: usize, p: f64) -> f64 {
    let mut dp = vec![0.0f64; k + 1];
    dp[0] = 1.0;
    for _ in 0..n {
        let mut new_dp = vec![0.0; k + 1];
        for j in 0..=k {
            new_dp[j] += dp[j] * (1.0 - p);  // tails
            if j > 0 { new_dp[j] += dp[j-1] * p; }  // heads
        }
        dp = new_dp;
    }
    dp[k]
}
```

---

# PART XIII — ADVANCED TECHNIQUES

## 13.1 — Knuth's Optimization

**Condition:** Applies when `opt[i][j-1] ≤ opt[i][j] ≤ opt[i+1][j]` (monotone opt).
**Result:** O(n³) → O(n²)

```cpp
// C++ — Knuth's optimization
// For dp[i][j] = min over k in [opt[i][j-1], opt[i+1][j]] { dp[i][k] + dp[k+1][j] + cost(i,j) }
int knuth_opt(int n, auto cost) {
    vector<vector<int>> dp(n+2, vector<int>(n+2, 0));
    vector<vector<int>> opt(n+2, vector<int>(n+2, 0));
    
    for (int i = 0; i < n; ++i) opt[i+1][i] = i;
    
    for (int len = 2; len <= n; ++len) {
        for (int i = 1; i + len - 1 <= n; ++i) {
            int j = i + len - 1;
            dp[i][j] = INT_MAX;
            for (int k = opt[i][j-1]; k <= opt[i+1][j]; ++k) {
                int v = dp[i][k] + dp[k+1][j] + cost(i, j);
                if (v < dp[i][j]) { dp[i][j] = v; opt[i][j] = k; }
            }
        }
    }
    return dp[1][n];
}
```

---

## 13.2 — Profile DP (Broken Profile)

**Use:** Tiling problems, counting perfect matchings on grids. Process cell by cell, maintaining the "profile" (boundary between filled and unfilled).

```cpp
// C++ — Count ways to tile m x n grid with dominoes
long long count_tilings(int m, int n) {
    if (m > n) swap(m, n);  // ensure m is smaller dimension
    vector<long long> dp(1 << m, 0);
    dp[0] = 1;
    // Process column by column
    for (int col = 0; col < n; ++col) {
        for (int row = 0; row < m; ++row) {
            vector<long long> ndp(1 << m, 0);
            for (int mask = 0; mask < (1 << m); ++mask) {
                if (!dp[mask]) continue;
                // Try placing vertical domino (requires row+1 < m and row+1 not in mask)
                if (row + 1 < m && !(mask >> (row+1) & 1) && !(mask >> row & 1)) {
                    ndp[mask | (1<<row) | (1<<(row+1))] += dp[mask];
                }
                // Or skip (cell was covered by previous column)
                if (mask >> row & 1) ndp[mask ^ (1<<row)] += dp[mask];
                // Or place horizontal (requires current cell not covered)
                if (!(mask >> row & 1)) ndp[mask | (1<<row)] += dp[mask];
            }
            dp = ndp;
        }
    }
    return dp[(1<<m)-1];
}
```

---

## 13.3 — SOS DP (Sum Over Subsets)

**Problem:** For each mask, compute the sum of `f[submask]` for all submasks.
**Naive:** O(3^n). **SOS DP:** O(n * 2^n)

```cpp
// C++ — Sum over subsets DP
void sos_dp(vector<long long>& f, int n) {
    // After this, f[mask] = sum of original f[s] for all s that are subsets of mask
    for (int i = 0; i < n; ++i)
        for (int mask = 0; mask < (1 << n); ++mask)
            if (mask >> i & 1)
                f[mask] += f[mask ^ (1 << i)];
}
```

```go
func sos(f []int64, n int) {
    for i := 0; i < n; i++ {
        for mask := 0; mask < (1 << n); mask++ {
            if mask>>i&1 == 1 {
                f[mask] += f[mask^(1<<i)]
            }
        }
    }
}
```

```rust
fn sos(f: &mut Vec<i64>, n: usize) {
    for i in 0..n {
        for mask in 0..(1usize << n) {
            if (mask >> i) & 1 == 1 {
                f[mask] += f[mask ^ (1 << i)];
            }
        }
    }
}
```

---

## 13.4 — Matrix Exponentiation for DP

**When:** Linear recurrence with fixed coefficients, but you need the answer for huge `n` (n up to 10^18).

**Key:** Express `dp[n]` as a matrix product and use fast matrix exponentiation.

```go
// Go — Matrix exponentiation for Fibonacci-like recurrences
type Matrix [2][2]int64

func mat_mul(A, B Matrix) Matrix {
    var C Matrix
    for i := 0; i < 2; i++ {
        for k := 0; k < 2; k++ {
            if A[i][k] == 0 { continue }
            for j := 0; j < 2; j++ {
                C[i][j] = (C[i][j] + A[i][k]*B[k][j]) % 1e9+7
            }
        }
    }
    return C
}

func mat_pow(M Matrix, p int64) Matrix {
    result := Matrix{{1, 0}, {0, 1}} // identity
    for p > 0 {
        if p&1 == 1 { result = mat_mul(result, M) }
        M = mat_mul(M, M)
        p >>= 1
    }
    return result
}

func fib_fast(n int64) int64 {
    if n == 0 { return 0 }
    M := Matrix{{1, 1}, {1, 0}}
    res := mat_pow(M, n-1)
    return res[0][0]
}
```

---

# PART XIV — CLASSIC HARD PROBLEMS

## 14.1 — Egg Drop

**State:** `dp[k][n]` = max floors testable with `k` eggs and `n` trials
**Reverse DP:** Instead of "min trials", ask "max floors with k eggs and t trials"
**Recurrence:** `dp[k][t] = dp[k-1][t-1] + dp[k][t-1] + 1`
(egg breaks: check dp[k-1][t-1] floors below; egg survives: check dp[k][t-1] floors above; +1 for current floor)

```cpp
int egg_drop(int k, int n) {
    // dp[i][j] = max floors we can check with i eggs and j trials
    vector<vector<int>> dp(k+1, vector<int>(n+1, 0));
    int t = 0;
    while (dp[k][t] < n) {
        ++t;
        for (int i = 1; i <= k; ++i)
            dp[i][t] = dp[i-1][t-1] + dp[i][t-1] + 1;
    }
    return t;
}
```

---

## 14.2 — Regular Expression Matching

```go
func is_match(s, p string) bool {
    m, n := len(s), len(p)
    dp := make([][]bool, m+1)
    for i := range dp { dp[i] = make([]bool, n+1) }
    dp[0][0] = true
    // Handle patterns like a*, a*b*, a*b*c* that can match empty string
    for j := 1; j <= n; j++ {
        if p[j-1] == '*' && j >= 2 { dp[0][j] = dp[0][j-2] }
    }
    for i := 1; i <= m; i++ {
        for j := 1; j <= n; j++ {
            if p[j-1] == '*' {
                dp[i][j] = dp[i][j-2] // use 0 of the preceding element
                if p[j-2] == '.' || p[j-2] == s[i-1] {
                    dp[i][j] = dp[i][j] || dp[i-1][j] // use 1+ of the preceding element
                }
            } else if p[j-1] == '.' || p[j-1] == s[i-1] {
                dp[i][j] = dp[i-1][j-1]
            }
        }
    }
    return dp[m][n]
}
```

---

## 14.3 — Stone Game / Game Theory DP

```rust
// Can first player guarantee a win? (Stone game: pick from either end)
fn stone_game(piles: &[i32]) -> bool {
    let n = piles.len();
    // dp[i][j] = max score difference (current player - other) for piles[i..=j]
    let mut dp = vec![vec![0i32; n]; n];
    for i in 0..n { dp[i][i] = piles[i]; }
    for len in 2..=n {
        for i in 0..=n-len {
            let j = i + len - 1;
            dp[i][j] = (piles[i] - dp[i+1][j]).max(piles[j] - dp[i][j-1]);
        }
    }
    dp[0][n-1] > 0
}
```

---

## 14.4 — Counting Distinct Subsequences

```cpp
// Count distinct subsequences of s that equal t
long long count_subseq(const string& s, const string& t) {
    int m = s.size(), n = t.size();
    const long long MOD = 1e9 + 7;
    vector<vector<long long>> dp(m+1, vector<long long>(n+1, 0));
    for (int i = 0; i <= m; ++i) dp[i][0] = 1;  // empty t always matched
    for (int i = 1; i <= m; ++i)
        for (int j = 1; j <= n; ++j) {
            dp[i][j] = dp[i-1][j];  // don't use s[i-1]
            if (s[i-1] == t[j-1]) dp[i][j] = (dp[i][j] + dp[i-1][j-1]) % MOD;
        }
    return dp[m][n];
}
```

---

# PART XV — MENTAL MODELS & EXPERT INSIGHTS

## The DP Design Framework (Expert's Checklist)

```
1. RECOGNIZE: Does the problem have optimal substructure?
   → Recursive definition possible? Each subproblem independent once chosen?

2. DEFINE STATE: What minimal information uniquely defines a subproblem?
   → Start with obvious parameters (index, remaining capacity, position)
   → Add extra dimensions only when needed

3. WRITE RECURRENCE: What's the last decision made?
   → Think: "What was the LAST choice that produced this state?"
   → Express dp[state] in terms of strictly smaller states

4. IDENTIFY BASE CASES: What states have trivially known answers?

5. DETERMINE ORDER: In what order must states be computed?
   → Top-down: any order (recursion handles it)
   → Bottom-up: must compute dependencies first

6. OPTIMIZE SPACE: Can you discard old states?
   → If dp[i] depends only on dp[i-1]: use two rows
   → If dp[i] depends only on dp[i-k]: use circular buffer

7. IDENTIFY COMPLEXITY: Is it acceptable?
   → If not, look for monotone optimization (D&C, CHT, Knuth)
```

## Pattern Recognition Guide

| Problem Signal | DP Pattern |
|---|---|
| "Count ways / paths" | Classical DP, state machine |
| "Min/Max with constraint" | Knapsack variant |
| "Substring / subsequence" | String DP (LCS, Edit Distance) |
| "Contiguous subarray" | Kadane's, prefix sums |
| "Interval / range" | Interval DP |
| "Permutation / subset" | Bitmask DP |
| "Tree / graph structure" | Tree DP, DAG DP |
| "Digit constraint" | Digit DP |
| "Game theory (two players)" | Minimax DP, Win/Lose states |
| "Expected value / probability" | Probability DP |
| "Very large n (10^18)" | Matrix exponentiation |
| "Tiling a grid" | Profile DP |
| "Sum over subsets" | SOS DP |
| "Linear cost function, ordered" | CHT / Li Chao Tree |

## Cognitive Principle: The "Last Step" Trick

When stuck on a recurrence, ask: **"What was the very last step to reach this optimal state?"**

For LCS: the last step is either "both characters matched" or "one string extended without matching."
For Knapsack: the last step is either "included item n" or "didn't include item n."
For TSP: the last step is "we entered city i from some previous city j in the remaining tour."

This transforms vague intuition into a clean recurrence every time.

## Complexity Classes in DP

| Complexity | Typical Structure |
|---|---|
| O(n) | 1D linear DP, Fibonacci-like |
| O(n log n) | LIS with patience sort, CHT |
| O(n²) | LCS, Edit Distance, Interval DP with Knuth |
| O(n² log n) | Interval DP with D&C opt |
| O(n³) | Matrix Chain, standard Interval DP |
| O(2ⁿ · n) | Bitmask DP |
| O(n · W) | Knapsack (pseudo-polynomial) |
| O(log n) per query | Matrix Exponentiation |

---

# PART XVI — PROBLEM TAXONOMY

## Tier 1 — Foundational (Must be automatic)
- Fibonacci, Climbing Stairs
- House Robber I/II
- Coin Change (count + min)
- 0/1 Knapsack
- LCS, LIS, Edit Distance
- Unique Paths, Min Path Sum

## Tier 2 — Core Competitive
- Burst Balloons
- Palindrome Partitioning II
- Regular Expression Matching
- Wildcard Matching
- Word Break I/II
- Maximal Rectangle

## Tier 3 — Advanced Competitive
- TSP (Bitmask)
- Digit DP problems
- Optimal BST (Knuth)
- Stone Game variants
- DP on Trees (all variants)
- Profile DP (tiling)

## Tier 4 — World-Class
- DP + Segment Tree / BIT
- Convex Hull Trick / Li Chao Tree
- Matrix Exponentiation DP
- SOS DP
- Broken Profile DP
- Alien Trick (Lagrangian relaxation)

---

*"The master has failed more times than the beginner has tried. In DP, each wrong state definition is a step toward the right one."*

1,731 lines. Here's what the guide covers across 16 parts:

**Foundations** — The philosophy of DP: what it actually *is* (not just "a technique"), the two pillars (optimal substructure + overlapping subproblems), and the three implementation styles with when to use each.

**Patterns covered with Go/Rust/C/C++ implementations:**

- **Linear DP** — Fibonacci, Kadane's, House Robber with O(1) space idioms
- **Knapsack Family** — 0/1, Unbounded, Bounded (binary grouping), Subset Sum, Coin Change — crucially, the combination vs permutation distinction explained via loop-order direction
- **String DP** — LCS (with space optimization), Edit Distance, LIS in both O(n²) and O(n log n), Palindromic Subsequence, Min Cuts
- **Interval DP** — Matrix Chain, Burst Balloons (the "last to pop" inversion insight), Optimal BST
- **Grid DP** — Unique Paths, Min Path Sum, Maximal Square
- **Bitmask DP** — TSP, Assignment Problem, Hamiltonian Path counting, SOS DP
- **Tree DP** — MIS on Tree, Diameter, Tree Knapsack (O(n²) merge)
- **DAG DP** — Longest/Count paths via topological order
- **Digit DP** — Full template with tight/free states
- **DP + Data Structures** — BIT-optimized LIS, Divide & Conquer optimization, Li Chao Tree (CHT)
- **Probability DP** — Expected value, probability recurrences
- **Advanced** — Knuth's optimization, Profile DP (tiling), Matrix Exponentiation, Egg Drop, Game Theory DP

The **Pattern Recognition Table** and **Expert Design Framework Checklist** are the two most reusable mental tools — internalize those and your pattern recognition will accelerate dramatically. The "Last Step Trick" alone will unblock most stuck recurrences.