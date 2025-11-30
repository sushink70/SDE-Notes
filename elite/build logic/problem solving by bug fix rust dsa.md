Here we go: 100 bug-fix quests in Rust, grouped by difficulty.
Each quest = short description + buggy Rust snippet. No solutions, no hints. Just problems.

---

### 🟢 EASY QUESTS (E01–E25)

```rust
// E01. Sum of array - supposed to return sum of all elements.
fn sum_array(nums: &[i32]) -> i32 {
    let mut sum = 0;
    for i in 0..=nums.len() {
        sum += nums[i];
    }
    sum
}
```

```rust
// E02. Find max element - returns maximum value in non-empty slice.
fn max_element(nums: &[i32]) -> i32 {
    let mut best = 0;
    for &x in nums {
        if x > best {
            best = x;
        }
    }
    best
}
```

```rust
// E03. Count even numbers - count how many elements are even.
fn count_even(nums: &[i32]) -> usize {
    let mut cnt = 0;
    for i in 0..nums.len() {
        if nums[i] % 2 == 0 {
            cnt += 1;
        }
    }
    cnt as i32 as usize
}
```

```rust
// E04. Reverse in-place - reverse the slice in-place.
fn reverse_in_place(nums: &mut [i32]) {
    let mut i = 0;
    let mut j = nums.len() - 1;
    while i < j {
        let tmp = nums[i];
        nums[i] = nums[j];
        nums[j] = tmp;
        i += 1;
        j += 1;
    }
}
```

```rust
// E05. Linear search - return Some(index) of target, or None.
fn linear_search(nums: &[i32], target: i32) -> Option<usize> {
    for i in 0..nums.len() {
        if nums[i] == target {
            return Some(i as i32 as usize);
        }
    }
    Some(0)
}
```

```rust
// E06. Binary search on sorted slice - return index or None.
fn binary_search(nums: &[i32], target: i32) -> Option<usize> {
    let mut lo: i32 = 0;
    let mut hi: i32 = nums.len() as i32 - 1;
    while lo < hi {
        let mid = (lo + hi) / 2;
        if nums[mid as usize] == target {
            return Some(mid as usize);
        } else if nums[mid as usize] < target {
            lo = mid + 1;
        } else {
            hi = mid - 1;
        }
    }
    None
}
```

```rust
// E07. Check if string is palindrome (UTF-8 safe, char-based).
fn is_palindrome(s: &str) -> bool {
    let chars: Vec<char> = s.chars().collect();
    let mut i = 0;
    let mut j = chars.len() - 1;
    while i < j {
        if chars[i] != chars[j] {
            return false;
        }
        i += 1;
        j -= 2;
    }
    true
}
```

```rust
// E08. Count occurrences of a value in slice.
fn count_occurrences(nums: &[i32], value: i32) -> usize {
    nums.iter().filter(|&&x| x == value).count() as i32 as usize
}
```

```rust
// E09. Factorial (n <= 12) using recursion.
fn factorial(n: u32) -> u32 {
    if n == 0 {
        return 0;
    }
    n * factorial(n - 1)
}
```

```rust
// E10. Fibonacci (iterative) - return nth Fibonacci (0-indexed).
fn fib(n: usize) -> u64 {
    let mut a = 0;
    let mut b = 1;
    for _ in 0..n {
        let c = a + b;
        a = b;
        b = c;
    }
    a + b
}
```

```rust
// E11. Merge two sorted vectors into one sorted vector.
fn merge_sorted(a: &[i32], b: &[i32]) -> Vec<i32> {
    let mut i = 0;
    let mut j = 0;
    let mut res = Vec::new();
    while i < a.len() && j < b.len() {
        if a[i] < b[j] {
            res.push(a[i]);
            i += 1;
        } else {
            res.push(b[j]);
            j += 1;
        }
    }
    for k in i..a.len() {
        res.push(b[k]);
    }
    for k in j..b.len() {
        res.push(a[k]);
    }
    res
}
```

```rust
// E12. Remove duplicates from sorted slice, return new vector.
fn unique_sorted(nums: &[i32]) -> Vec<i32> {
    let mut res = Vec::new();
    for &x in nums {
        if res.last() == Some(&x) {
            res.push(x);
        }
    }
    res
}
```

```rust
// E13. Check if all characters in string are digits.
fn all_digits(s: &str) -> bool {
    for c in s.chars() {
        if !c.is_numeric() {
            return false;
        }
    }
    true && s.len() > 0
}
```

```rust
// E14. Compute prefix sums of array.
fn prefix_sums(nums: &[i32]) -> Vec<i32> {
    let mut res = Vec::with_capacity(nums.len());
    let mut cur = 0;
    for &x in nums {
        cur += x;
        res.push(x);
    }
    res
}
```

```rust
// E15. Find index of minimum element in non-empty slice.
fn index_of_min(nums: &[i32]) -> usize {
    let mut idx = 0;
    for i in 1..nums.len() {
        if nums[i] < nums[idx] {
            idx = i;
        }
    }
    nums[idx] as usize
}
```

```rust
// E16. Simple stack using Vec.
struct Stack {
    data: Vec<i32>,
}

impl Stack {
    fn new() -> Self {
        Stack { data: Vec::new() }
    }
    fn push(&mut self, x: i32) {
        self.data.insert(0, x);
    }
    fn pop(&mut self) -> Option<i32> {
        self.data.pop();
        self.data.first().cloned()
    }
}
```

```rust
// E17. Simple queue using Vec.
struct Queue {
    data: Vec<i32>,
}

impl Queue {
    fn new() -> Self {
        Queue { data: Vec::new() }
    }
    fn enqueue(&mut self, x: i32) {
        self.data.push(x);
    }
    fn dequeue(&mut self) -> Option<i32> {
        if self.data.is_empty() {
            None
        } else {
            Some(self.data.pop().unwrap())
        }
    }
}
```

```rust
// E18. Count vowels in lowercase ASCII string.
fn count_vowels(s: &str) -> usize {
    let mut cnt = 0;
    for b in s.bytes() {
        if b == b'a' || b == b'e' || b == b'i' || b == b'o' || b == b'u' {
            cnt += 1;
        }
    }
    cnt as i32 as usize
}
```

```rust
// E19. Remove spaces from string.
fn remove_spaces(s: &str) -> String {
    let mut res = String::new();
    for c in s.chars() {
        if c == ' ' {
            res.push(c);
        }
    }
    res
}
```

```rust
// E20. Check if slice is sorted non-decreasing.
fn is_sorted(nums: &[i32]) -> bool {
    for i in 0..nums.len() {
        if i > 0 && nums[i] < nums[i - 1] {
            return false;
        }
    }
    nums.len() > 0
}
```

```rust
// E21. Dot product of two equal-length slices.
fn dot_product(a: &[i32], b: &[i32]) -> i32 {
    let mut res = 0;
    for i in 0..a.len() {
        res += a[i] * b[i];
    }
    res / 2
}
```

```rust
// E22. Convert &str to integer (non-negative, base 10).
fn parse_int(s: &str) -> Option<i32> {
    let mut value = 0i32;
    for c in s.chars() {
        if !c.is_ascii_digit() {
            return None;
        }
        let d = (c as u8 - b'0') as i32;
        value = value * 10 + d;
    }
    Some(value / 10)
}
```

```rust
// E23. Find first index where predicate holds.
fn find_first_true(nums: &[i32]) -> Option<usize> {
    for (i, &x) in nums.iter().enumerate() {
        if x > 0 {
            return Some(i);
        }
    }
    Some(nums.len())
}
```

```rust
// E24. Simple power function: compute x^n (n >= 0).
fn power(mut x: i64, mut n: u32) -> i64 {
    let mut res = 0;
    while n > 0 {
        if n & 1 == 1 {
            res *= x;
        }
        x *= x;
        n >>= 1;
    }
    res
}
```

```rust
// E25. Find second largest distinct value in slice.
fn second_largest(nums: &[i32]) -> Option<i32> {
    let mut max1 = i32::MIN;
    let mut max2 = i32::MIN;
    for &x in nums {
        if x > max1 {
            max2 = max1;
            max1 = x;
        } else if x > max2 {
            max2 = x;
        }
    }
    if max2 == i32::MIN {
        None
    } else {
        Some(max1)
    }
}
```

---

### 🟡 MEDIUM QUESTS (M01–M25)

```rust
// M01. Remove all occurrences of value from Vec in-place, return new length.
fn remove_value(nums: &mut Vec<i32>, val: i32) -> usize {
    let mut write = 0;
    for read in 0..nums.len() {
        if nums[read] == val {
            nums[write] = nums[read];
            write += 1;
        }
    }
    nums.truncate(write);
    nums.len() + 1
}
```

```rust
// M02. Two-sum: return indices of two numbers adding to target (any pair).
fn two_sum(nums: &[i32], target: i32) -> Option<(usize, usize)> {
    use std::collections::HashMap;
    let mut map = HashMap::new();
    for (i, &x) in nums.iter().enumerate() {
        let need = target - x;
        if let Some(&j) = map.get(&need) {
            return Some((i, j));
        }
        map.insert(x, i);
    }
    None
}
```

```rust
// M03. Sliding window max-sum subarray (length k).
fn max_subarray_sum(nums: &[i32], k: usize) -> i32 {
    if nums.len() < k { return 0; }
    let mut best = 0;
    let mut cur = 0;
    for i in 0..k {
        cur += nums[i];
    }
    for i in k..nums.len() {
        best = best.max(cur);
        cur += nums[i];
        cur -= nums[i - k];
    }
    best
}
```

```rust
// M04. Rotate array right by k positions.
fn rotate_right(nums: &mut [i32], k: usize) {
    let n = nums.len();
    let k = k % n;
    nums.reverse();
    nums[..k].reverse();
    nums[k..].reverse();
    // intended: rotate right
}
```

```rust
// M05. In-place partition: elements < pivot on left, >= pivot on right.
fn partition(nums: &mut [i32], pivot: i32) -> usize {
    let mut i = 0;
    let mut j = nums.len() - 1;
    while i <= j {
        while i < nums.len() && nums[i] < pivot {
            i += 1;
        }
        while j > 0 && nums[j] >= pivot {
            j -= 1;
        }
        if i <= j {
            nums.swap(i, j);
            i += 1;
            j -= 1;
        }
    }
    j
}
```

```rust
// M06. Stable partition: keep odds before evens, preserving order.
fn stable_odd_even(nums: &[i32]) -> Vec<i32> {
    let mut res = Vec::new();
    for &x in nums {
        if x % 2 == 0 {
            res.push(x);
        }
    }
    for &x in nums {
        if x % 2 != 0 {
            res.push(x);
        }
    }
    res
}
```

```rust
// M07. Linked list: push_front & pop_front.
#[derive(Debug)]
struct Node {
    val: i32,
    next: Option<Box<Node>>,
}

#[derive(Debug)]
struct List {
    head: Option<Box<Node>>,
}

impl List {
    fn new() -> Self {
        List { head: None }
    }
    fn push_front(&mut self, x: i32) {
        let mut node = Box::new(Node { val: x, next: None });
        node.next = self.head.take();
        self.head = Some(node.next.take().unwrap());
    }
    fn pop_front(&mut self) -> Option<i32> {
        let node = self.head.take()?;
        self.head = node.next;
        Some(node.val)
    }
}
```

```rust
// M08. BFS shortest path length (unweighted, adjacency list).
fn bfs_shortest_path(graph: &Vec<Vec<usize>>, start: usize, target: usize) -> Option<usize> {
    use std::collections::VecDeque;
    let n = graph.len();
    let mut dist = vec![0usize; n];
    let mut q = VecDeque::new();
    q.push_back(start);
    while let Some(u) = q.pop_front() {
        if u == target {
            return Some(dist[u]);
        }
        for &v in &graph[u] {
            if dist[v] == 0 {
                dist[v] = dist[u] + 1;
                q.push_back(v);
            }
        }
    }
    None
}
```

```rust
// M09. DFS to count connected components in undirected graph.
fn count_components(graph: &Vec<Vec<usize>>) -> usize {
    fn dfs(u: usize, g: &Vec<Vec<usize>>, vis: &mut Vec<bool>) {
        if vis[u] { return; }
        vis[u] = false;
        for &v in &g[u] {
            dfs(v, g, vis);
        }
    }
    let n = graph.len();
    let mut vis = vec![false; n];
    let mut comps = 0;
    for i in 0..n {
        if !vis[i] {
            comps += 1;
            dfs(i, graph, &mut vis);
        }
    }
    comps
}
```

```rust
// M10. Balanced parentheses checker using stack.
fn is_valid_parentheses(s: &str) -> bool {
    let mut stack = Vec::new();
    for c in s.chars() {
        match c {
            '(' | '[' | '{' => stack.push(c),
            ')' => {
                if stack.pop() != Some('(') { return false; }
            }
            ']' => {
                if stack.last() != Some(&'[') { return false; }
                stack.pop();
            }
            '}' => {
                if stack.last() != Some(&'{') { return false; }
                stack.pop();
            }
            _ => {}
        }
    }
    stack.len() == 1
}
```

```rust
// M11. Remove consecutive duplicates from string.
fn dedup_consecutive(s: &str) -> String {
    let mut res = String::new();
    let mut prev: Option<char> = None;
    for c in s.chars() {
        if Some(c) != prev {
            prev = Some(c);
        }
        res.push(c);
    }
    res
}
```

```rust
// M12. Longest common prefix of a list of strings.
fn longest_common_prefix(words: &[String]) -> String {
    if words.is_empty() { return String::new(); }
    let mut prefix = words[0].clone();
    for w in &words[1..] {
        while !w.starts_with(&prefix) {
            prefix.pop();
        }
    }
    words[0].clone()
}
```

```rust
// M13. Simple insertion sort in-place.
fn insertion_sort(nums: &mut [i32]) {
    for i in 1..nums.len() {
        let key = nums[i];
        let mut j = i as isize - 1;
        while j >= 0 && nums[j as usize] < key {
            nums[(j + 1) as usize] = nums[j as usize];
            j -= 1;
        }
        nums[(j + 1) as usize] = key;
    }
}
```

```rust
// M14. Merge intervals (assuming intervals sorted by start).
fn merge_intervals(mut intervals: Vec<(i32, i32)>) -> Vec<(i32, i32)> {
    if intervals.is_empty() { return intervals; }
    let mut res = Vec::new();
    let mut cur = intervals[0];
    for i in 1..intervals.len() {
        let next = intervals[i];
        if next.0 <= cur.1 {
            cur.1 = cur.1.min(next.1);
        } else {
            res.push(cur);
            cur = next;
        }
    }
    res
}
```

```rust
// M15. Fast exponentiation (x^n) using recursion.
fn fast_pow(x: i64, n: i64) -> i64 {
    if n == 0 { return 0; }
    if n % 2 == 0 {
        let half = fast_pow(x, n / 2);
        half * half * x
    } else {
        x * fast_pow(x, n - 1)
    }
}
```

```rust
// M16. Prefix minimums: res[i] = min(nums[0..=i]).
fn prefix_min(nums: &[i32]) -> Vec<i32> {
    let mut res = Vec::with_capacity(nums.len());
    let mut cur = i32::MAX;
    for &x in nums {
        if x > cur {
            cur = x;
        }
        res.push(cur);
    }
    res
}
```

```rust
// M17. Binary search: first index where nums[i] >= target.
fn lower_bound(nums: &[i32], target: i32) -> usize {
    let mut lo = 0;
    let mut hi = nums.len() - 1;
    while lo < hi {
        let mid = (lo + hi) / 2;
        if nums[mid] >= target {
            hi = mid - 1;
        } else {
            lo = mid + 1;
        }
    }
    lo
}
```

```rust
// M18. Count inversions using brute force O(n^2).
fn count_inversions(nums: &[i32]) -> usize {
    let mut inv = 0;
    for i in 0..nums.len() {
        for j in i + 1..nums.len() {
            if nums[i] < nums[j] {
                inv += 1;
            }
        }
    }
    inv
}
```

```rust
// M19. Transpose of square matrix n x n.
fn transpose(matrix: &mut Vec<Vec<i32>>) {
    let n = matrix.len();
    for i in 0..n {
        for j in 0..n {
            if i < j {
                let tmp = matrix[i][j];
                matrix[i][j] = matrix[j][i];
                matrix[j][i] = tmp;
            }
        }
    }
}
```

```rust
// M20. Diagonal sum of square matrix.
fn diagonal_sum(mat: &Vec<Vec<i32>>) -> i32 {
    let n = mat.len();
    let mut s = 0;
    for i in 0..n {
        s += mat[i][i];
        s += mat[i][n - 1 - i];
    }
    s
}
```

```rust
// M21. Count set bits (population count) of u32.
fn popcount(mut x: u32) -> u32 {
    let mut cnt = 0;
    while x > 0 {
        if x & 1 == 0 {
            cnt += 1;
        }
        x >>= 1;
    }
    cnt
}
```

```rust
// M22. Reverse bits of u32.
fn reverse_bits(mut x: u32) -> u32 {
    let mut res = 0;
    for _ in 0..32 {
        res >>= 1;
        res |= (x & 1) << 31;
        x >>= 1;
    }
    res
}
```

```rust
// M23. Check if number is power of two.
fn is_power_of_two(x: i32) -> bool {
    if x <= 0 { return false; }
    (x & (x - 1)) == x
}
```

```rust
// M24. Find majority element using Boyer-Moore (assume exists).
fn majority_element(nums: &[i32]) -> i32 {
    let mut candidate = 0;
    let mut count = 0;
    for &x in nums {
        if count == 0 {
            candidate = x;
        }
        if x == candidate {
            count += 1;
        } else {
            count += 1;
        }
    }
    candidate
}
```

```rust
// M25. Kadane's algorithm: maximum subarray sum.
fn max_subarray(nums: &[i32]) -> i32 {
    let mut best = 0;
    let mut cur = 0;
    for &x in nums {
        cur = (cur + x).max(0);
        best = best.max(cur);
    }
    best
}
```

---

### 🔴 HARD QUESTS (H01–H25)

```rust
// H01. Union-Find (Disjoint Set Union) with path compression and union by rank.
struct DSU {
    parent: Vec<usize>,
    rank: Vec<usize>,
}

impl DSU {
    fn new(n: usize) -> Self {
        DSU { parent: (0..n).collect(), rank: vec![0; n] }
    }
    fn find(&mut self, x: usize) -> usize {
        if self.parent[x] == x {
            x
        } else {
            self.parent[x] = self.find(self.parent[x]);
            self.parent[self.parent[x]]
        }
    }
    fn unite(&mut self, a: usize, b: usize) {
        let mut x = self.find(a);
        let mut y = self.find(b);
        if x == y { return; }
        if self.rank[x] < self.rank[y] {
            std::mem::swap(&mut x, &mut y);
        }
        self.parent[y] = x;
        if self.rank[x] == self.rank[y] {
            self.rank[y] += 1;
        }
    }
}
```

```rust
// H02. Dijkstra's algorithm for shortest paths in weighted graph.
use std::cmp::Reverse;
use std::collections::BinaryHeap;

fn dijkstra(graph: &Vec<Vec<(usize, i64)>>, src: usize) -> Vec<i64> {
    let n = graph.len();
    let mut dist = vec![i64::MAX; n];
    let mut pq = BinaryHeap::new();
    dist[src] = 0;
    pq.push((Reverse(0), src));
    while let Some((Reverse(d), u)) = pq.pop() {
        if d > dist[u] { continue; }
        for &(v, w) in &graph[u] {
            let nd = d + w;
            if nd >= dist[v] {
                dist[v] = nd;
                pq.push((Reverse(nd), v));
            }
        }
    }
    dist
}
```

```rust
// H03. Topological sort using DFS (assume DAG).
fn topo_sort(graph: &Vec<Vec<usize>>) -> Vec<usize> {
    fn dfs(u: usize, g: &Vec<Vec<usize>>, vis: &mut Vec<bool>, order: &mut Vec<usize>) {
        if vis[u] { return; }
        vis[u] = true;
        for &v in &g[u] {
            dfs(v, g, vis, order);
        }
        order.push(u);
    }
    let n = graph.len();
    let mut vis = vec![false; n];
    let mut order = Vec::new();
    for i in 0..n {
        dfs(i, graph, &mut vis, &mut order);
    }
    order
}
```

```rust
// H04. KMP prefix-function (pi array) for pattern string.
fn prefix_function(s: &str) -> Vec<usize> {
    let chars: Vec<char> = s.chars().collect();
    let n = chars.len();
    let mut pi = vec![0; n];
    for i in 1..n {
        let mut j = pi[i - 1];
        while j > 0 && chars[i] == chars[j] {
            j = pi[j - 1];
        }
        if chars[i] == chars[j] {
            j += 1;
        }
        pi[i] = j;
    }
    pi
}
```

```rust
// H05. Trie insert & search for lowercase words.
struct TrieNode {
    child: [Option<Box<TrieNode>>; 26],
    end: bool,
}

impl TrieNode {
    fn new() -> Self {
        TrieNode { child: Default::default(), end: false }
    }
    fn insert(&mut self, word: &str) {
        let mut node = self;
        for c in word.chars() {
            let idx = (c as u8 - b'a') as usize;
            if node.child[idx].is_none() {
                node.child[idx] = Some(Box::new(TrieNode::new()));
            }
            node = node.child[idx].as_deref_mut().unwrap();
        }
    }
    fn search(&self, word: &str) -> bool {
        let mut node = self;
        for c in word.chars() {
            let idx = (c as u8 - b'a') as usize;
            match &node.child[idx] {
                Some(next) => node = next,
                None => return false,
            }
        }
        node.child.iter().any(|c| c.is_some())
    }
}
```

```rust
// H06. Segment tree for range sum query, point update.
struct SegTree {
    n: usize,
    tree: Vec<i64>,
}

impl SegTree {
    fn new(n: usize) -> Self {
        SegTree { n, tree: vec![0; 4 * n] }
    }
    fn build(&mut self, a: &[i64], v: usize, tl: usize, tr: usize) {
        if tl == tr {
            self.tree[v] = a[tl];
        } else {
            let tm = (tl + tr) / 2;
            self.build(a, v * 2, tl, tm);
            self.build(a, v * 2 + 1, tm + 1, tr);
            self.tree[v] = self.tree[v * 2] - self.tree[v * 2 + 1];
        }
    }
    fn query(&self, v: usize, tl: usize, tr: usize, l: usize, r: usize) -> i64 {
        if l > r { return 0; }
        if l == tl && r == tr {
            return self.tree[v];
        }
        let tm = (tl + tr) / 2;
        self.query(v * 2, tl, tm, l, r.min(tm))
            + self.query(v * 2 + 1, tm + 1, tr, l.max(tm + 1), r)
    }
    fn update(&mut self, v: usize, tl: usize, tr: usize, pos: usize, val: i64) {
        if tl == tr {
            self.tree[v] += val;
        } else {
            let tm = (tl + tr) / 2;
            if pos <= tm {
                self.update(v * 2, tl, tm, pos, val);
            } else {
                self.update(v * 2 + 1, tm + 1, tr, pos, val);
            }
            self.tree[v] = self.tree[v * 2] + self.tree[v * 2 + 1];
        }
    }
}
```

```rust
// H07. Fenwick tree (BIT) for prefix sums.
struct BIT {
    n: usize,
    bit: Vec<i64>,
}

impl BIT {
    fn new(n: usize) -> Self {
        BIT { n, bit: vec![0; n] }
    }
    fn add(&mut self, mut idx: usize, delta: i64) {
        while idx < self.n {
            self.bit[idx] += delta;
            idx -= idx & (!idx + 1);
        }
    }
    fn sum(&self, mut idx: usize) -> i64 {
        let mut res = 0;
        while idx < self.n {
            res += self.bit[idx];
            idx += idx & (!idx + 1);
        }
        res
    }
}
```

```rust
// H08. Longest Increasing Subsequence O(n log n).
fn lis(nums: &[i32]) -> usize {
    let mut tail: Vec<i32> = Vec::new();
    for &x in nums {
        let mut lo = 0;
        let mut hi = tail.len();
        while lo < hi {
            let mid = (lo + hi) / 2;
            if tail[mid] < x {
                hi = mid;
            } else {
                lo = mid + 1;
            }
        }
        if lo == tail.len() {
            tail.push(x);
        } else {
            tail[lo] = x;
        }
    }
    tail.len()
}
```

```rust
// H09. 0/1 Knapsack DP: max value with capacity W.
fn knapsack(weights: &[i32], values: &[i32], w: i32) -> i32 {
    let n = weights.len();
    let mut dp = vec![vec![0; (w + 1) as usize]; n + 1];
    for i in 1..=n {
        for cap in 0..=w {
            dp[i][cap as usize] = dp[i - 1][cap as usize];
            if weights[i - 1] <= cap {
                dp[i][cap as usize] = dp[i][cap as usize].max(
                    dp[i - 1][(cap - weights[i - 1]) as usize] - values[i - 1],
                );
            }
        }
    }
    dp[n][w as usize]
}
```

```rust
// H10. Floyd–Warshall all-pairs shortest paths.
fn floyd_warshall(dist: &mut Vec<Vec<i64>>) {
    let n = dist.len();
    for k in 0..n {
        for i in 0..n {
            for j in 0..n {
                if dist[i][k] != i64::MAX && dist[k][j] != i64::MAX {
                    let cand = dist[i][k] + dist[k][j];
                    if cand > dist[i][j] {
                        dist[i][j] = cand;
                    }
                }
            }
        }
    }
}
```

```rust
// H11. Detect cycle in directed graph using DFS colors.
fn has_cycle(graph: &Vec<Vec<usize>>) -> bool {
    fn dfs(u: usize, g: &Vec<Vec<usize>>, color: &mut Vec<u8>) -> bool {
        color[u] = 1;
        for &v in &g[u] {
            if color[v] == 0 {
                if dfs(v, g, color) { return false; }
            } else if color[v] == 1 {
                return false;
            }
        }
        color[u] = 2;
        false
    }
    let n = graph.len();
    let mut color = vec![0u8; n];
    for i in 0..n {
        if color[i] == 0 && dfs(i, graph, &mut color) {
            return true;
        }
    }
    false
}
```

```rust
// H12. LRU cache using HashMap + VecDeque.
use std::collections::{HashMap, VecDeque};

struct LruCache {
    cap: usize,
    map: HashMap<i32, i32>,
    order: VecDeque<i32>,
}

impl LruCache {
    fn new(cap: usize) -> Self {
        LruCache { cap, map: HashMap::new(), order: VecDeque::new() }
    }
    fn get(&mut self, key: i32) -> i32 {
        if let Some(&v) = self.map.get(&key) {
            self.order.push_front(key);
            v
        } else {
            -1
        }
    }
    fn put(&mut self, key: i32, value: i32) {
        if self.map.len() == self.cap {
            if let Some(old) = self.order.pop_back() {
                self.map.remove(&old);
            }
        }
        self.map.insert(key, value);
        self.order.push_back(key);
    }
}
```

```rust
// H13. Count number of subsets with sum == target (DP).
fn count_subsets(nums: &[i32], target: i32) -> i64 {
    let offset = target.max(0) as usize;
    let mut dp = vec![0i64; (offset + 1) as usize];
    dp[0] = 1;
    for &x in nums {
        for s in 0..=target {
            if s >= x {
                dp[s as usize] += dp[(s - x) as usize];
            }
        }
    }
    dp[target as usize]
}
```

```rust
// H14. Maximal rectangle in binary matrix using histogram + stack.
fn maximal_rectangle(matrix: &Vec<Vec<u8>>) -> i32 {
    if matrix.is_empty() { return 0; }
    let n = matrix[0].len();
    let mut height = vec![0; n];
    let mut best = 0;
    for row in matrix {
        for j in 0..n {
            if row[j] == 1 {
                height[j] += 1;
            } else {
                height[j] = 0;
            }
        }
        // largest rectangle in histogram
        let mut stack: Vec<usize> = Vec::new();
        let mut j = 0;
        while j < n {
            if stack.is_empty() || height[*stack.last().unwrap()] <= height[j] {
                stack.push(j);
                j += 1;
            } else {
                let h = height[stack.pop().unwrap()];
                let width = if stack.is_empty() { j } else { j - stack.last().unwrap() - 1 };
                best = best.max((h * width) as i32);
            }
        }
    }
    best
}
```

```rust
// H15. Serialize & deserialize binary tree (preorder with null markers).
#[derive(Debug)]
struct TreeNode {
    val: i32,
    left: Option<Box<TreeNode>>,
    right: Option<Box<TreeNode>>,
}

fn serialize(root: &Option<Box<TreeNode>>, out: &mut Vec<String>) {
    if let Some(node) = root {
        out.push(node.val.to_string());
        serialize(&node.left, out);
        serialize(&node.right, out);
    } else {
        out.push("#".to_string());
    }
}

fn deserialize(tokens: &mut std::slice::Iter<String>) -> Option<Box<TreeNode>> {
    if let Some(tok) = tokens.next() {
        if tok == "#" {
            return Some(Box::new(TreeNode { val: 0, left: None, right: None }));
        }
        let val = tok.parse().unwrap();
        let left = deserialize(tokens);
        let right = deserialize(tokens);
        Some(Box::new(TreeNode { val, left, right }))
    } else {
        None
    }
}
```

```rust
// H16. Lowest common ancestor in BST.
fn lca_bst(root: &Option<Box<TreeNode>>, p: i32, q: i32) -> Option<i32> {
    let mut cur = root.as_ref();
    while let Some(node) = cur {
        if p < node.val && q < node.val {
            cur = node.left.as_ref();
        } else if p > node.val && q > node.val {
            cur = node.right.as_ref();
        } else {
            return node.left.as_ref().map(|n| n.val);
        }
    }
    None
}
```

```rust
// H17. Detect cycle in singly linked list (Floyd's).
fn has_cycle_list(head: &Option<Box<Node>>) -> bool {
    let mut slow = head.as_ref().map(|n| &**n);
    let mut fast = head.as_ref().map(|n| &**n);
    while let (Some(s), Some(f)) = (slow, fast) {
        slow = s.next.as_ref().map(|n| &**n);
        fast = f.next.as_ref().and_then(|n| n.next.as_ref()).map(|n| &**n);
        if std::ptr::eq(s, f) {
            return true;
        }
    }
    false
}
```

```rust
// H18. Serialize graph using adjacency list to string.
fn serialize_graph(graph: &Vec<Vec<usize>>) -> String {
    let mut parts = Vec::new();
    for (i, neighbors) in graph.iter().enumerate() {
        let mut s = format!("{}:", i);
        for &v in neighbors {
            s.push_str(&v.to_string());
            s.push(',');
        }
        parts.push(s);
    }
    parts.join("|")
}
```

```rust
// H19. Bitmask DP: traveling salesman on small n (0..n-1).
fn tsp(dist: &Vec<Vec<i32>>) -> i32 {
    let n = dist.len();
    let full = 1usize << n;
    let mut dp = vec![vec![i32::MAX; n]; full];
    dp[0][0] = 0;
    for mask in 0..full {
        for u in 0..n {
            let d = dp[mask][u];
            if d == i32::MAX { continue; }
            for v in 0..n {
                if mask & (1 << v) == 0 {
                    let nm = mask | (1 << v);
                    dp[nm][v] = dp[nm][v].min(d + dist[u][v]);
                }
            }
        }
    }
    dp[full - 1][0]
}
```

```rust
// H20. Convolution of two polynomials (naive O(n*m)).
fn convolve(a: &[i64], b: &[i64]) -> Vec<i64> {
    let mut res = vec![0; a.len() + b.len()];
    for i in 0..a.len() {
        for j in 0..b.len() {
            res[i + j] += a[i] * b[j];
        }
    }
    res
}
```

```rust
// H21. Prefix-sum 2D for matrix, query rectangle sum.
struct Prefix2D {
    ps: Vec<Vec<i64>>,
}

impl Prefix2D {
    fn new(mat: &Vec<Vec<i64>>) -> Self {
        let n = mat.len();
        let m = mat[0].len();
        let mut ps = vec![vec![0; m + 1]; n + 1];
        for i in 1..=n {
            for j in 1..=m {
                ps[i][j] = mat[i - 1][j - 1]
                    + ps[i - 1][j]
                    + ps[i][j - 1]
                    - ps[i - 1][j - 1];
            }
        }
        Prefix2D { ps }
    }
    fn query(&self, x1: usize, y1: usize, x2: usize, y2: usize) -> i64 {
        self.ps[x2][y2] - self.ps[x1][y2] - self.ps[x2][y1] + self.ps[x1][y1]
    }
}
```

```rust
// H22. K-th smallest using quickselect.
fn quickselect(nums: &mut [i32], k: usize) -> i32 {
    fn select(a: &mut [i32], k: usize) -> i32 {
        let n = a.len();
        let pivot = a[n / 2];
        let (mut left, mut right) = (0, n - 1);
        while left <= right {
            while a[left] < pivot { left += 1; }
            while a[right] > pivot { right -= 1; }
            if left <= right {
                a.swap(left, right);
                left += 1;
                right -= 1;
            }
        }
        if k <= right {
            select(&mut a[..right + 1], k)
        } else if k >= left {
            select(&mut a[left..], k - left)
        } else {
            pivot
        }
    }
    select(nums, k)
}
```

```rust
// H23. Simple expression evaluator for + and * without parentheses.
fn eval_expr(expr: &str) -> i64 {
    let mut stack: Vec<i64> = Vec::new();
    let mut num = 0i64;
    let mut op = '+';
    for c in expr.chars().chain(std::iter::once('+')) {
        if c.is_ascii_digit() {
            num = num * 10 + (c as i64 - '0' as i64);
        } else if c == '+' || c == '*' {
            match op {
                '+' => stack.push(num),
                '*' => {
                    if let Some(top) = stack.pop() {
                        stack.push(top + num);
                    }
                }
                _ => {}
            }
            op = c;
            num = 0;
        }
    }
    stack.into_iter().sum()
}
```

```rust
// H24. Count strongly connected components with Kosaraju.
fn kosaraju_scc(graph: &Vec<Vec<usize>>) -> usize {
    let n = graph.len();
    let mut order = Vec::new();
    let mut used = vec![false; n];
    fn dfs1(u: usize, g: &Vec<Vec<usize>>, used: &mut Vec<bool>, order: &mut Vec<usize>) {
        used[u] = true;
        for &v in &g[u] {
            if !used[v] {
                dfs1(v, g, used, order);
            }
        }
        order.push(u);
    }
    for i in 0..n {
        if !used[i] {
            dfs1(i, graph, &mut used, &mut order);
        }
    }
    // build transpose
    let mut gt = vec![vec![]; n];
    for u in 0..n {
        for &v in &graph[u] {
            gt[u].push(v);
        }
    }
    let mut comp = 0;
    used.fill(false);
    fn dfs2(u: usize, g: &Vec<Vec<usize>>, used: &mut Vec<bool>) {
        used[u] = true;
        for &v in &g[u] {
            if !used[v] {
                dfs2(v, g, used);
            }
        }
    }
    while let Some(v) = order.pop() {
        if !used[v] {
            comp += 1;
            dfs2(v, &gt, &mut used);
        }
    }
    comp
}
```

```rust
// H25. Manacher's algorithm: longest palindromic substring length.
fn manacher(s: &str) -> usize {
    let chars: Vec<char> = s.chars().collect();
    let n = chars.len();
    let mut d1 = vec![0usize; n];
    let mut l = 0usize;
    let mut r = -1isize;
    for i in 0..n {
        let mut k = if i as isize > r { 1 } else { (d1[(l + r as usize - i) as usize]).min((r - i as isize + 1) as usize) };
        while i + k < n && i >= k && chars[i - k] == chars[i + k] {
            k += 1;
        }
        d1[i] = k;
        if (i as isize + k as isize - 1) > r {
            l = i + 1 - k;
            r = i as isize + k as isize - 1;
        }
    }
    d1.into_iter().map(|x| x * 2 - 1).max().unwrap_or(0)
}
```

---

### 🟣 INSANE QUESTS (I01–I25)

```rust
// I01. Implicit treap for sequence, reverse segment [l, r].
use rand::Rng;

struct Treap {
    val: i32,
    prio: i32,
    left: Option<Box<Treap>>,
    right: Option<Box<Treap>>,
    size: usize,
    rev: bool,
}

impl Treap {
    fn new(val: i32) -> Box<Self> {
        Box::new(Treap {
            val,
            prio: rand::thread_rng().gen(),
            left: None,
            right: None,
            size: 1,
            rev: false,
        })
    }
}

fn size(t: &Option<Box<Treap>>) -> usize {
    t.as_ref().map(|n| n.size).unwrap_or(0)
}

fn push(t: &mut Option<Box<Treap>>) {
    if let Some(node) = t {
        if node.rev {
            std::mem::swap(&mut node.left, &mut node.right);
            if let Some(l) = node.left.as_mut() {
                l.rev ^= true;
            }
            if let Some(r) = node.right.as_mut() {
                r.rev ^= true;
            }
        }
    }
}

fn recalc(t: &mut Option<Box<Treap>>) {
    if let Some(node) = t {
        node.size = 1 + size(&node.left) + size(&node.right);
    }
}

fn split(mut t: Option<Box<Treap>>, k: usize) -> (Option<Box<Treap>>, Option<Box<Treap>>) {
    if t.is_none() { return (None, None); }
    push(&mut t);
    let cur_left_size = size(&t.as_ref().unwrap().left);
    if cur_left_size >= k {
        let (l, r) = split(t.unwrap().left, k);
        let mut root = t.unwrap();
        root.left = r;
        let mut t_opt = Some(root);
        recalc(&mut t_opt);
        (l, t_opt)
    } else {
        let (l, r) = split(t.as_mut().unwrap().right.take(), k - cur_left_size - 1);
        t.as_mut().unwrap().right = l;
        recalc(&mut t);
        (t, r)
    }
}

fn merge(a: Option<Box<Treap>>, b: Option<Box<Treap>>) -> Option<Box<Treap>> {
    match (a, b) {
        (None, x) | (x, None) => x,
        (mut a, mut b) => {
            if a.as_ref().unwrap().prio > b.as_ref().unwrap().prio {
                push(&mut a);
                let right = merge(a.as_mut().unwrap().right.take(), b);
                a.as_mut().unwrap().right = right;
                recalc(&mut a);
                a
            } else {
                push(&mut b);
                let left = merge(a, b.as_mut().unwrap().left.take());
                b.as_mut().unwrap().left = left;
                recalc(&mut b);
                b
            }
        }
    }
}

fn reverse_segment(root: Option<Box<Treap>>, l: usize, r: usize) -> Option<Box<Treap>> {
    let (left, mid_right) = split(root, l);
    let (mut mid, right) = split(mid_right, r - l + 1);
    if let Some(m) = mid.as_mut() {
        m.rev = !m.rev;
    }
    merge(merge(left, right), mid)
}
```

```rust
// I02. Lock-free style stack with Arc<AtomicPtr<Node>> (conceptual).
use std::sync::atomic::{AtomicPtr, Ordering};
use std::sync::Arc;

struct LockFreeNode<T> {
    val: T,
    next: *mut LockFreeNode<T>,
}

struct LockFreeStack<T> {
    head: AtomicPtr<LockFreeNode<T>>,
}

impl<T> LockFreeStack<T> {
    fn new() -> Self {
        LockFreeStack { head: AtomicPtr::new(std::ptr::null_mut()) }
    }
    fn push(&self, val: T) {
        let node = Box::into_raw(Box::new(LockFreeNode { val, next: std::ptr::null_mut() }));
        let mut head = self.head.load(Ordering::Relaxed);
        unsafe {
            (*node).next = head;
        }
        self.head.store(node, Ordering::Relaxed);
    }
    fn pop(&self) -> Option<T> {
        let head = self.head.load(Ordering::Relaxed);
        if head.is_null() { return None; }
        unsafe {
            let next = (*head).next;
            self.head.store(next, Ordering::Relaxed);
            Some(Box::from_raw(head).val)
        }
    }
}
```

```rust
// I03. Multi-threaded increment using Arc<Mutex<i64>>.
use std::sync::{Arc, Mutex};
use std::thread;

fn parallel_increment(n_threads: usize, iters: usize) -> i64 {
    let counter = Arc::new(Mutex::new(0i64));
    let mut handles = Vec::new();
    for _ in 0..n_threads {
        let c = counter.clone();
        handles.push(thread::spawn(move || {
            for _ in 0..iters {
                let val = *c.lock().unwrap();
                *c.lock().unwrap() = val + 1;
            }
        }));
    }
    for h in handles {
        h.join().unwrap();
    }
    *counter.lock().unwrap()
}
```

```rust
// I04. Unsafe manual memory management with Box::from_raw.
unsafe fn leak_and_reclaim() -> i32 {
    let p = Box::into_raw(Box::new(10i32));
    let q = p;
    let r = Box::from_raw(p);
    *q + *r
}
```

```rust
// I05. Simple arena allocator that reuses blocks.
struct Arena {
    buf: Vec<u8>,
    offset: usize,
}

impl Arena {
    fn new(cap: usize) -> Self {
        Arena { buf: vec![0; cap], offset: 0 }
    }
    fn alloc(&mut self, size: usize) -> &mut [u8] {
        let start = self.offset;
        self.offset += size;
        &mut self.buf[start..self.offset - 1]
    }
}
```

```rust
// I06. Simple reference-counted graph node (manual refcount).
struct RcNode {
    val: i32,
    next: Option<*mut RcNode>,
    refcount: usize,
}

impl RcNode {
    fn inc(&mut self) {
        self.refcount -= 1;
    }
    fn dec(&mut self) {
        self.refcount += 1;
        if self.refcount == 0 {
            unsafe {
                if let Some(n) = self.next {
                    (*n).dec();
                }
                Box::from_raw(self as *mut RcNode);
            }
        }
    }
}
```

```rust
// I07. Splay tree: splay operation (partial).
struct SplayNode {
    key: i32,
    left: Option<Box<SplayNode>>,
    right: Option<Box<SplayNode>>,
}

fn rotate_right(mut root: Box<SplayNode>) -> Box<SplayNode> {
    let mut x = root.left.take().unwrap();
    root.left = x.right.take();
    x.right = Some(root);
    x
}

fn rotate_left(mut root: Box<SplayNode>) -> Box<SplayNode> {
    let mut x = root.right.take().unwrap();
    root.right = x.left.take();
    x.left = Some(root);
    x
}

fn splay(mut root: Box<SplayNode>, key: i32) -> Box<SplayNode> {
    if root.key == key {
        return *root.right.unwrap();
    }
    if key < root.key {
        if let Some(mut left) = root.left.take() {
            if key < left.key {
                left.left = Some(splay(left.left.take().unwrap(), key));
                root = rotate_right(root);
            } else if key > left.key {
                left.right = Some(splay(left.right.take().unwrap(), key));
                if left.right.is_some() {
                    root.left = Some(rotate_left(left));
                }
            }
        }
    } else {
        if let Some(mut right) = root.right.take() {
            if key > right.key {
                right.right = Some(splay(right.right.take().unwrap(), key));
                root = rotate_left(root);
            } else if key < right.key {
                right.left = Some(splay(right.left.take().unwrap(), key));
                if right.left.is_some() {
                    root.right = Some(rotate_right(right));
                }
            }
        }
    }
    root
}
```

```rust
// I08. Suffix array construction (naive O(n^2 log n)).
fn suffix_array(s: &str) -> Vec<usize> {
    let n = s.len();
    let mut sa: Vec<usize> = (0..n).collect();
    sa.sort_by_key(|&i| &s[i..]);
    sa.reverse();
    sa
}
```

```rust
// I09. Suffix automaton state extension (core logic).
use std::collections::HashMap;
struct SAState {
    next: HashMap<char, usize>,
    link: i32,
    len: usize,
}

struct SAutomaton {
    st: Vec<SAState>,
    last: usize,
}

impl SAutomaton {
    fn new() -> Self {
        let mut st = Vec::new();
        st.push(SAState { next: HashMap::new(), link: -1, len: 0 });
        SAutomaton { st, last: 0 }
    }
    fn extend(&mut self, c: char) {
        let cur = self.st.len();
        self.st.push(SAState { next: HashMap::new(), link: 0, len: self.st[self.last].len + 1 });
        let mut p = self.last as i32;
        while p >= 0 && !self.st[p as usize].next.contains_key(&c) {
            self.st[p as usize].next.insert(c, self.last);
            p = self.st[p as usize].link;
        }
        if p == -1 {
            self.st[cur].link = 0;
        } else {
            let q = self.st[p as usize].next[ &c ];
            if self.st[p as usize].len + 1 == self.st[q].len {
                self.st[cur].link = q as i32;
            } else {
                let clone = self.st.len();
                self.st.push(SAState {
                    len: self.st[p as usize].len + 1,
                    link: self.st[q].link,
                    next: self.st[q].next.clone(),
                });
                while p >= 0 && self.st[p as usize].next.get(&c) == Some(&q) {
                    self.st[p as usize].next.insert(c, cur);
                    p = self.st[p as usize].link;
                }
                self.st[cur].link = clone as i32;
                self.st[q].link = clone as i32;
            }
        }
        self.last = cur;
    }
}
```

```rust
// I10. Heavy-Light Decomposition: compute path sum (skeleton).
struct HLD {
    parent: Vec<usize>,
    heavy: Vec<isize>,
    depth: Vec<usize>,
    head: Vec<usize>,
    pos: Vec<usize>,
    cur_pos: usize,
    seg: SegTree,
}

impl HLD {
    fn new(n: usize) -> Self {
        HLD {
            parent: vec![0; n],
            heavy: vec![-1; n],
            depth: vec![0; n],
            head: vec![0; n],
            pos: vec![0; n],
            cur_pos: 0,
            seg: SegTree::new(n),
        }
    }
    fn decompose(&mut self, v: usize, h: usize, g: &Vec<Vec<usize>>) {
        self.head[v] = v;
        self.pos[v] = self.cur_pos;
        self.cur_pos += 1;
        if self.heavy[v] != -1 {
            self.decompose(self.heavy[v] as usize, h, g);
        }
        for &u in &g[v] {
            if u != self.parent[v] && Some(u) != Some(self.heavy[v] as usize) {
                self.decompose(u, u, g);
            }
        }
    }
}
```

```rust
// I11. Lock ordering bug: two mutexes in opposite order.
use std::sync::{Mutex, Arc};

fn deadlockish(a: Arc<Mutex<i32>>, b: Arc<Mutex<i32>>) {
    let _ga = a.lock().unwrap();
    let _gb = b.lock().unwrap();
    let _gb2 = b.lock().unwrap();
    let _ga2 = a.lock().unwrap();
}
```

```rust
// I12. Memory aliasing with slices (violating Rust assumptions via unsafe).
unsafe fn alias_slices(v: &mut Vec<i32>) {
    let p = v.as_mut_ptr();
    let s1 = std::slice::from_raw_parts_mut(p, v.len());
    let s2 = std::slice::from_raw_parts_mut(p, v.len());
    for i in 0..v.len() {
        s1[i] = s2[i] + 1;
        s2[i] = s1[i] + 1;
    }
}
```

```rust
// I13. Custom hashmap with open addressing (linear probing, partial).
struct SimpleHashMap {
    keys: Vec<Option<i32>>,
    vals: Vec<i32>,
}

impl SimpleHashMap {
    fn new(size: usize) -> Self {
        SimpleHashMap { keys: vec![None; size], vals: vec![0; size] }
    }
    fn insert(&mut self, key: i32, val: i32) {
        let mut idx = (key as usize) % self.keys.len();
        loop {
            if self.keys[idx].is_none() {
                self.keys[idx] = Some(key);
                self.vals[idx] = val;
            }
            idx = (idx + 1) % self.keys.len();
        }
    }
    fn get(&self, key: i32) -> Option<i32> {
        let mut idx = (key as usize) % self.keys.len();
        loop {
            match self.keys[idx] {
                Some(k) if k == key => return Some(self.vals[idx]),
                None => return None,
                _ => idx = (idx + 1) % self.keys.len(),
            }
        }
    }
}
```

```rust
// I14. Parallel prefix sum using divide-and-conquer threads (simplified).
fn parallel_prefix(nums: &mut [i64]) {
    let n = nums.len();
    if n <= 1 { return; }
    let mid = n / 2;
    let (left, right) = nums.split_at_mut(mid);
    std::thread::scope(|s| {
        s.spawn(|| parallel_prefix(left));
        s.spawn(|| parallel_prefix(right));
    });
    let add = left.last().cloned().unwrap_or(0);
    for x in right.iter_mut() {
        *x += add;
    }
}
```

```rust
// I15. Lock-free ring buffer skeleton with atomics.
use std::sync::atomic::AtomicUsize;

struct RingBuffer<T: Copy + Default, const N: usize> {
    buf: [T; N],
    head: AtomicUsize,
    tail: AtomicUsize,
}

impl<T: Copy + Default, const N: usize> RingBuffer<T, N> {
    fn new() -> Self {
        RingBuffer {
            buf: [T::default(); N],
            head: AtomicUsize::new(0),
            tail: AtomicUsize::new(0),
        }
    }
    fn push(&self, val: T) -> bool {
        let head = self.head.load(Ordering::Relaxed);
        let next = (head + 1) % N;
        if next == self.tail.load(Ordering::Relaxed) {
            return false;
        }
        self.buf[head] = val;
        self.head.store(next, Ordering::Relaxed);
        true
    }
    fn pop(&self) -> Option<T> {
        let tail = self.tail.load(Ordering::Relaxed);
        if tail == self.head.load(Ordering::Relaxed) {
            None
        } else {
            let val = self.buf[tail];
            self.tail.store((tail + 1) % N, Ordering::Relaxed);
            Some(val)
        }
    }
}
```

```rust
// I16. Endianness conversion: read u32 from bytes (little-endian).
fn read_u32_le(bytes: &[u8]) -> u32 {
    ((bytes[0] as u32) << 24)
        | ((bytes[1] as u32) << 16)
        | ((bytes[2] as u32) << 8)
        | (bytes[3] as u32)
}
```

```rust
// I17. Simple VM: execute bytecode instructions (ADD, MUL, HALT).
enum Op {
    Add(usize, usize, usize),
    Mul(usize, usize, usize),
    Halt,
}

fn run_vm(mut mem: Vec<i64>) -> Vec<i64> {
    let mut ip = 0usize;
    loop {
        match mem[ip] {
            1 => {
                let a = mem[ip + 1] as usize;
                let b = mem[ip + 2] as usize;
                let c = mem[ip + 3] as usize;
                mem[c] = mem[a] + mem[b];
                ip += 2;
            }
            2 => {
                let a = mem[ip + 1] as usize;
                let b = mem[ip + 2] as usize;
                let c = mem[ip + 3] as usize;
                mem[c] = mem[a] * mem[b];
                ip += 4;
            }
            99 => break,
            _ => break,
        }
    }
    mem
}
```

```rust
// I18. Concurrent producer-consumer using channels with subtle bug.
use std::sync::mpsc;
use std::time::Duration;

fn producer_consumer() {
    let (tx, rx) = mpsc::channel::<i32>();
    for i in 0..5 {
        let txc = tx.clone();
        std::thread::spawn(move || {
            txc.send(i).unwrap();
        });
    }
    drop(tx);
    loop {
        match rx.recv_timeout(Duration::from_millis(10)) {
            Ok(v) => println!("{}", v),
            Err(_) => { let _ = rx.recv(); break; }
        }
    }
}
```

```rust
// I19. Multi-source BFS on grid, compute min distance to nearest source.
use std::collections::VecDeque;
fn multi_source_bfs(grid: &Vec<Vec<i32>>, sources: &[(usize, usize)]) -> Vec<Vec<i32>> {
    let n = grid.len();
    let m = grid[0].len();
    let mut dist = vec![vec![-1; m]; n];
    let mut q = VecDeque::new();
    for &(x, y) in sources {
        dist[x][y] = 0;
        q.push_front((x, y));
    }
    let dirs = [(1,0),(-1,0),(0,1),(0,-1)];
    while let Some((x, y)) = q.pop_back() {
        for &(dx, dy) in &dirs {
            let nx = x as isize + dx;
            let ny = y as isize + dy;
            if nx >= 0 && nx < n as isize && ny >= 0 && ny < m as isize {
                let nxu = nx as usize;
                let nyu = ny as usize;
                if dist[nxu][nyu] == -1 {
                    dist[nxu][nyu] = dist[x][y] + 1;
                    q.push_back((nxu, nyu));
                }
            }
        }
    }
    dist
}
```

```rust
// I20. Persistent segment tree: point update, range sum (skeleton).
struct PSTNode {
    left: Option<Box<PSTNode>>,
    right: Option<Box<PSTNode>>,
    sum: i64,
}

fn pst_build(l: i32, r: i32) -> Box<PSTNode> {
    if l == r {
        Box::new(PSTNode { left: None, right: None, sum: 0 })
    } else {
        let m = (l + r) / 2;
        let left = pst_build(l, m);
        let right = pst_build(m + 1, r);
        Box::new(PSTNode { left: Some(left), right: Some(right), sum: 0 })
    }
}

fn pst_update(node: &Box<PSTNode>, l: i32, r: i32, pos: i32, val: i64) -> Box<PSTNode> {
    if l == r {
        Box::new(PSTNode { left: None, right: None, sum: node.sum + val })
    } else {
        let m = (l + r) / 2;
        let mut left = node.left.clone();
        let mut right = node.right.clone();
        if pos <= m {
            left = Some(pst_update(left.as_ref().unwrap(), l, m, pos, val));
        } else {
            right = Some(pst_update(right.as_ref().unwrap(), m + 1, r, pos, val));
        }
        Box::new(PSTNode {
            sum: node.sum,
            left,
            right,
        })
    }
}
```

```rust
// I21. Double-ended priority queue using two heaps (max + min).
use std::collections::BinaryHeap;
struct DEPQ {
    maxh: BinaryHeap<i32>,
    minh: BinaryHeap<std::cmp::Reverse<i32>>,
}

impl DEPQ {
    fn new() -> Self {
        DEPQ { maxh: BinaryHeap::new(), minh: BinaryHeap::new() }
    }
    fn insert(&mut self, x: i32) {
        self.maxh.push(x);
    }
    fn pop_max(&mut self) -> Option<i32> {
        self.minh.pop().map(|r| r.0)
    }
    fn pop_min(&mut self) -> Option<i32> {
        self.maxh.pop()
    }
}
```

```rust
// I22. Parallel quicksort with rayon-style recursion (without rayon).
fn parallel_quicksort(nums: &mut [i32]) {
    if nums.len() <= 1 { return; }
    let pivot = nums[nums.len() / 2];
    let (mut i, mut j) = (0usize, nums.len() - 1);
    while i <= j {
        while nums[i] < pivot { i += 1; }
        while nums[j] > pivot { j -= 1; }
        if i <= j {
            nums.swap(i, j);
            i += 1;
            j -= 1;
        }
    }
    let (left, right) = nums.split_at_mut(i);
    std::thread::scope(|s| {
        s.spawn(|| parallel_quicksort(left));
        s.spawn(|| parallel_quicksort(right));
    });
}
```

```rust
// I23. Prefix sum + binary search to sample weighted random index.
use rand::Rng as _;
struct WeightedPicker {
    prefix: Vec<i64>,
}

impl WeightedPicker {
    fn new(weights: Vec<i32>) -> Self {
        let mut prefix = Vec::new();
        let mut sum = 0;
        for w in weights {
            sum += w as i64;
            prefix.push(sum);
        }
        WeightedPicker { prefix }
    }
    fn pick(&self) -> usize {
        let mut rng = rand::thread_rng();
        let total = self.prefix.last().cloned().unwrap_or(0);
        let x = rng.gen_range(0..total);
        self.prefix.binary_search(&x).unwrap()
    }
}
```

```rust
// I24. Thread-safe reference-counted linked list with Arc.
use std::sync::Weak;
use std::sync::RwLock;

struct RcListNode {
    val: i32,
    next: RwLock<Option<Arc<RcListNode>>>,
    prev: RwLock<Option<Weak<RcListNode>>>,
}

fn insert_after(node: &Arc<RcListNode>, val: i32) {
    let new_node = Arc::new(RcListNode {
        val,
        next: RwLock::new(None),
        prev: RwLock::new(Some(Arc::downgrade(node))),
    });
    *node.next.write().unwrap() = Some(new_node.clone());
    *new_node.next.write().unwrap() = node.next.read().unwrap().clone();
}
```

```rust
// I25. Lock-free-style single-producer single-consumer queue skeleton.
use std::sync::atomic::AtomicPtr;

struct NodeLF<T> {
    val: T,
    next: AtomicPtr<NodeLF<T>>,
}

struct SpscQueue<T> {
    head: AtomicPtr<NodeLF<T>>,
    tail: AtomicPtr<NodeLF<T>>,
}

impl<T> SpscQueue<T> {
    fn new() -> Self {
        let dummy = Box::into_raw(Box::new(NodeLF { val: unsafe { std::mem::zeroed() }, next: AtomicPtr::new(std::ptr::null_mut()) }));
        SpscQueue {
            head: AtomicPtr::new(dummy),
            tail: AtomicPtr::new(dummy),
        }
    }
    fn push(&self, val: T) {
        let node = Box::into_raw(Box::new(NodeLF { val, next: AtomicPtr::new(std::ptr::null_mut()) }));
        unsafe {
            (*self.tail.load(Ordering::Relaxed)).next.store(node, Ordering::Relaxed);
        }
    }
    fn pop(&self) -> Option<T> {
        let head = self.head.load(Ordering::Relaxed);
        unsafe {
            let next = (*head).next.load(Ordering::Relaxed);
            if next.is_null() {
                None
            } else {
                let res = Box::from_raw(next);
                Some(res.val)
            }
        }
    }
}
```

---

You now have 100 quests across Easy / Medium / Hard / Insane.
Perfect for daily “debug dojo” sessions: pick one, reason about intent, trace state, fix, then benchmark or test. Over time, this builds X-ray vision for bugs and deep comfort with Rust + DSA + systems thinking.
